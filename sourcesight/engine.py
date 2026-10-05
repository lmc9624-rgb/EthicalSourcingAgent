from __future__ import annotations

from collections import defaultdict, deque

from sourcesight.models import DataSource, ProductAssessment, SupplierAssessment
from sourcesight.signals import PILLAR_WEIGHTS, PILLARS, detect_signals, noisy_or


TIER_ORDER = {"Low": 0, "Watch": 1, "Elevated": 2, "High": 3}


def assess_product(source: DataSource, product_id: str) -> ProductAssessment:
    product = next((item for item in source.products() if item.id == product_id), None)
    if product is None:
        raise KeyError(f"Unknown product '{product_id}'")
    entities = source.entities()
    incoming = defaultdict(list)
    for edge in product.edges:
        incoming[edge.target].append(edge)
    involved = {product.root_entity_id}
    for edge in product.edges:
        involved.update((edge.source, edge.target))
    order = _topological_order(involved, product.edges, product.id)
    assessments: dict[str, SupplierAssessment] = {}
    for entity_id in order:
        entity = entities[entity_id]
        signals = detect_signals(entity_id, source, bool(incoming[entity_id]))
        pillar_scores = {pillar: noisy_or([signal.strength for signal in signals if signal.pillar == pillar]) for pillar in PILLARS}
        composite = noisy_or([pillar_scores[pillar] * PILLAR_WEIGHTS[pillar] for pillar in PILLARS])
        convergence = sum(pillar_scores[pillar] >= 0.4 for pillar in PILLARS if pillar != "transparency")
        direct_listing = any(signal.pillar == "linkage" and signal.claim_kind == "FACT" for signal in signals)
        own_tier, reason = _tier(direct_listing, convergence, composite)
        docs = source.documents().get(entity_id, ())
        non_exposure_fact = any(signal.claim_kind == "FACT" and signal.pillar != "exposure" for signal in signals)
        confidence_score = min(1.0, 0.25 + (0.2 if entity_id in source.trade_profiles() else 0)
                               + (0.2 if docs else 0) + (0.15 if entity.upstream_disclosed else 0)
                               + (0.2 if non_exposure_fact else 0))
        confidence = "High" if confidence_score >= 0.75 else "Medium" if confidence_score >= 0.5 else "Low"
        indicators = tuple(dict.fromkeys(indicator for document in docs for indicator in document["ilo_indicators"]))

        inherited_candidates = []
        for edge in incoming[entity_id]:
            upstream = assessments[edge.source]
            if upstream.effective_tier == "Low":
                continue
            scaled_score = upstream.effective_score * (0.6 + 0.4 * edge.share)
            path = (upstream.risk_path or (edge.source,)) + (entity_id,)
            inherited_candidates.append((upstream.effective_tier, scaled_score, path, upstream.risk_source_id or edge.source))
        inherited = max(inherited_candidates, key=lambda item: (TIER_ORDER[item[0]], item[1], item[3]), default=None)
        inherited_tier = inherited[0] if inherited else None
        effective_tier = max((own_tier, inherited_tier or "Low"), key=TIER_ORDER.get)
        effective_score = max(composite, inherited[1] if inherited else 0.0)
        if inherited and TIER_ORDER[inherited[0]] > TIER_ORDER[own_tier]:
            risk_path, risk_source_id = inherited[2], inherited[3]
        elif own_tier != "Low":
            risk_path, risk_source_id = (entity_id,), entity_id
        else:
            risk_path, risk_source_id = (), None
        assessments[entity_id] = SupplierAssessment(
            entity_id=entity_id, signals=signals, pillar_scores=pillar_scores, composite_score=composite,
            convergence=convergence, own_tier=own_tier, tier_reason=reason,
            confidence_score=confidence_score, confidence=confidence, ilo_indicators=indicators,
            effective_tier=effective_tier, effective_score=effective_score,
            inherited_tier=inherited_tier, risk_path=risk_path, risk_source_id=risk_source_id,
        )
    root = assessments[product.root_entity_id]
    return ProductAssessment(product, assessments, root.effective_tier, root.own_tier,
                             root.inherited_tier, root.risk_path, root.risk_source_id)


def _tier(direct_listing: bool, convergence: int, composite: float) -> tuple[str, str]:
    if direct_listing:
        return "High", "Direct listed-entity name match; confirm identity and listing status."
    if convergence >= 3:
        return "High", f"{convergence} independent evidence pillars converge."
    if convergence >= 2 and composite >= 0.85:
        return "High", f"{convergence} pillars converge and composite score is at least 0.85."
    if convergence >= 2:
        return "Elevated", f"{convergence} independent evidence pillars meet the convergence threshold."
    if composite >= 0.6:
        return "Elevated", "Composite score is at least 0.60."
    if convergence >= 1 or composite >= 0.3:
        return "Watch", "At least one evidence pillar meets the watch threshold."
    return "Low", "No available pillar meets the illustrative watch threshold."


def _topological_order(nodes: set[str], edges, product_id: str) -> list[str]:
    indegree = {node: 0 for node in nodes}
    outgoing = defaultdict(list)
    for edge in edges:
        indegree[edge.target] += 1
        outgoing[edge.source].append(edge.target)
    ready = deque(sorted(node for node, count in indegree.items() if count == 0))
    order = []
    while ready:
        node = ready.popleft()
        order.append(node)
        for neighbor in sorted(outgoing[node]):
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                ready.append(neighbor)
    if len(order) != len(nodes):
        raise ValueError(f"Product {product_id}: supply map contains a cycle; assessment stopped.")
    return order