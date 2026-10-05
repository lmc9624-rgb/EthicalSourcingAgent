from __future__ import annotations

from collections import defaultdict
from datetime import date
from difflib import SequenceMatcher
import re

from sourcesight.models import DataSource, Entity, Signal
from sourcesight.validation import ILO_INDICATORS


PILLARS = ("exposure", "linkage", "trade", "worker", "transparency")
PILLAR_WEIGHTS = {"exposure": 0.5, "linkage": 0.9, "trade": 0.7, "worker": 0.9, "transparency": 0.3}
ILO_WEIGHTS = {indicator: 0.3 for indicator in ILO_INDICATORS}
ILO_WEIGHTS.update({
    "restriction_of_movement": 0.5, "debt_bondage": 0.5, "retention_of_identity_documents": 0.5,
    "withholding_of_wages": 0.5, "physical_and_sexual_violence": 0.6, "excessive_overtime": 0.2,
})
RELIABILITY_MULTIPLIER = {"high": 1.0, "medium": 0.75, "low": 0.5}


def noisy_or(values: list[float]) -> float:
    remaining = 1.0
    for value in values:
        remaining *= 1.0 - value
    return 1.0 - remaining


def detect_signals(entity_id: str, source: DataSource, mapped_inputs: bool) -> tuple[Signal, ...]:
    entity = source.entities()[entity_id]
    signals = []
    signals.extend(_exposure(entity, source))
    signals.extend(_linkage(entity, source))
    signals.extend(_trade(entity, source))
    signals.extend(_worker(entity_id, source))
    if entity.upstream_disclosed is False:
        strength = 0.6 if mapped_inputs else 0.4
        signals.append(Signal(
            "transparency", "Upstream sources are not disclosed", strength, "LEAD",
            "Available records do not identify this supplier's upstream sources; this is a data gap, not evidence of misconduct.",
            (f"ENTITY:{entity_id}",), "Request a current upstream supplier and origin disclosure.",
        ))
    return tuple(signals)


def _exposure(entity: Entity, source: DataSource) -> list[Signal]:
    matches = [row for row in source.sector_baselines()
               if row["sector"] == entity.sector
               and (not row.get("country") or row["country"] == entity.country)
               and (not row.get("region") or row["region"] == entity.region)]
    if not matches:
        return []
    row = max(matches, key=lambda item: (bool(item.get("country")) + bool(item.get("region")), bool(item.get("region"))))
    if row["score"] <= 0:
        return []
    detail = f"Illustrative baseline matched {entity.sector} in {entity.country}"
    if entity.region:
        detail += f", {entity.region}"
    return [Signal("exposure", "Sector and geography exposure", float(row["score"]), "INFERENCE",
                   f"{detail} (score {row['score']:.2f}).", (row["source_id"],),
                   "Verify origin and production conditions with current documentation.",
                   row.get("source_group"))]


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _linkage(entity: Entity, source: DataSource) -> list[Signal]:
    listings = source.listings()
    direct = [item for item in listings if SequenceMatcher(None, _normalize(entity.name), _normalize(item["entity_name"])).ratio() >= 0.82]
    if direct:
        return [Signal("linkage", "Direct listed-entity name match", 1.0, "FACT",
                       f"Normalized entity name matches listed name '{item['entity_name']}'. Identity still requires human review.",
                       (item["id"],), "Confirm legal identity, aliases, and the listing's current status.") for item in direct]

    entities = source.entities()
    listing_names = [(item, _normalize(item["entity_name"])) for item in listings]
    queue: list[tuple[str, float, tuple[str, ...], int]] = [(entity.id, 1.0, (entity.id,), 0)]
    seen = {entity.id}
    while queue:
        current_id, strength, chain, hops = queue.pop(0)
        if hops >= 2:
            continue
        current = entities[current_id]
        neighbors: list[tuple[str, float]] = []
        for other_id, other in entities.items():
            if other_id == current_id:
                continue
            ownership = next((share for name, share in current.owners if _normalize(name) == _normalize(other.name)), None)
            if ownership is None:
                ownership = next((share for name, share in other.owners if _normalize(name) == _normalize(current.name)), None)
            if ownership is not None:
                neighbors.append((other_id, 0.8 if ownership >= 0.5 else 0.6))
            elif set(current.directors) & set(other.directors):
                neighbors.append((other_id, 0.55))
            elif current.address and current.address == other.address:
                neighbors.append((other_id, 0.5))
        for other_id, edge_strength in neighbors:
            other = entities[other_id]
            next_strength = strength * edge_strength
            next_chain = chain + (other_id,)
            match = next((listing for listing, name in listing_names
                          if SequenceMatcher(None, _normalize(other.name), name).ratio() >= 0.82), None)
            if match:
                path = " -> ".join(entities[item].name for item in next_chain)
                return [Signal("linkage", "Corporate-network proximity to listed entity", next_strength, "INFERENCE",
                               f"A bounded network path links this entity to '{match['entity_name']}': {path}.",
                               (match["id"],), "Verify each relationship and the listed entity's identity.")]
            if other_id not in seen:
                seen.add(other_id)
                queue.append((other_id, next_strength, next_chain, hops + 1))
    return []


def _trade(entity: Entity, source: DataSource) -> list[Signal]:
    profile = source.trade_profiles().get(entity.id)
    if not profile:
        return []
    signals = []
    months = sorted(profile.get("months", []), key=lambda row: row["date"])
    peak = max((row.get("exports", 0) for row in months), default=0)
    capacity = profile.get("monthly_capacity", 0)
    ratio = peak / capacity if capacity else 0
    if capacity and ratio > 1.15:
        signals.append(Signal("trade", "Exports exceed stated monthly capacity", min(1.0, ratio - 1.0), "INFERENCE",
                              f"Peak monthly exports were {peak:g} units against estimated capacity of {capacity:g} (ratio {ratio:.2f}).",
                              (profile["id"],), "Request production and shipment records for the period."))
    for event in source.enforcement_events():
        if event.get("entity_id") != entity.id:
            continue
        event_date = date.fromisoformat(event["date"])
        before = [row["exports"] for row in months if date.fromisoformat(row["date"]) < event_date][-3:]
        after = [row["exports"] for row in months if date.fromisoformat(row["date"]) >= event_date][:3]
        if before and after and sum(before) / len(before) > 0:
            surge = (sum(after) / len(after)) / (sum(before) / len(before))
            if surge >= 1.25:
                signals.append(Signal("trade", "Export volume increased around enforcement event", min(1.0, surge - 1.0), "INFERENCE",
                                      f"Average exports were {surge:.2f}x higher in available post-event months around {event['date']}; this pattern is not causal evidence.",
                                      (event["id"], profile["id"]), "Review shipment, capacity, and enforcement records for context."))
        route_before = [row for row in months if date.fromisoformat(row["date"]) < event_date][-3:]
        route_after = [row for row in months if date.fromisoformat(row["date"]) >= event_date][:3]
        before_mix, before_months = _route_mix(route_before)
        after_mix, after_months = _route_mix(route_after)
        if before_months >= 2 and after_months >= 2:
            route_keys = set(before_mix) | set(after_mix)
            shift = 0.5 * sum(abs(before_mix.get(route, 0.0) - after_mix.get(route, 0.0))
                              for route in route_keys)
            if shift >= 0.5:
                previous_route = max(before_mix, key=before_mix.get)
                observed_route = max(after_mix, key=after_mix.get)
                signals.append(Signal(
                    "trade", "Trade route mix shifted around enforcement event", min(1.0, shift), "INFERENCE",
                    f"Observed shipment-route mix changed by {shift:.0%} across available months around "
                    f"{event['date']}: dominant route shifted from {_route_label(previous_route)} to "
                    f"{_route_label(observed_route)}. This is a temporal association, not evidence that "
                    "enforcement caused the change or that shipments were deliberately diverted.",
                    (event["id"], profile["id"]),
                    "Compare bills of lading, customs declarations, and transshipment records to verify the route change.",
                ))
    floor = profile.get("price_floor")
    below_floor = [row for row in months[-3:] if floor is not None and row.get("price", floor) < floor]
    if below_floor:
        prices = ", ".join(f"{row['date']}: {row['price']:g}" for row in below_floor)
        signals.append(Signal("trade", "Recent prices below illustrative labor-cost floor", 0.5, "LEAD",
                              f"Recent prices fell below the illustrative floor of {floor:g}: {prices}.",
                              (profile["id"],), "Check pricing assumptions and obtain cost and wage documentation."))
    return signals


def _route_mix(months: list[dict]) -> tuple[dict[tuple[str, str, str], float], int]:
    volumes: dict[tuple[str, str, str], float] = defaultdict(float)
    observed_months = 0
    for month in months:
        routes = month.get("routes", [])
        month_total = sum(route["volume"] for route in routes)
        if month_total <= 0:
            continue
        observed_months += 1
        for route in routes:
            key = (route["origin"], route.get("transit", ""), route["destination"])
            volumes[key] += route["volume"]
    total = sum(volumes.values())
    return ({route: volume / total for route, volume in volumes.items()} if total else {}, observed_months)


def _route_label(route: tuple[str, str, str]) -> str:
    origin, transit, destination = route
    via = f" via {transit}" if transit else " direct"
    return f"{origin}{via} to {destination}"


def _worker(entity_id: str, source: DataSource) -> list[Signal]:
    signals = []
    for document in source.documents().get(entity_id, ()):
        indicators = tuple(item for item in document["ilo_indicators"] if item in ILO_WEIGHTS)
        if not indicators:
            continue
        strength = noisy_or([ILO_WEIGHTS[item] for item in indicators]) * RELIABILITY_MULTIPLIER[document["reliability"]]
        claim = "FACT" if document["reliability"] == "high" else "LEAD"
        labels = ", ".join(item.replace("_", " ") for item in indicators)
        signals.append(Signal("worker", "Document reports ILO forced-labor indicators", strength, claim,
                              f"{document['summary']} Reported indicators: {labels}. Reliability: {document['reliability']}.",
                              (document["id"],), "Seek corroboration through safe worker engagement and independent records.",
                              document.get("source_group")))
    return signals