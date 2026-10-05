from __future__ import annotations

from datetime import date
from typing import Any


ILO_INDICATORS = {
    "abuse_of_vulnerability", "deception", "restriction_of_movement", "isolation",
    "physical_and_sexual_violence", "intimidation_and_threats", "retention_of_identity_documents",
    "withholding_of_wages", "debt_bondage", "abusive_working_and_living_conditions", "excessive_overtime",
}
RELIABILITY = {"high", "medium", "low"}


class DataValidationError(ValueError):
    """Raised when fixture records cannot safely enter an assessment."""


def validate_data(data: dict[str, Any]) -> None:
    errors: list[str] = []
    collections = ("products", "entities", "listings", "enforcement_events", "sector_baselines", "trade_profiles", "documents")
    for key in collections:
        if key not in data:
            errors.append(f"missing top-level collection '{key}'")

    entities = data.get("entities", {})
    if not isinstance(entities, dict):
        errors.append("entities must be an object keyed by entity ID")
        entities = {}
    for entity_id, entity in entities.items():
        for field in ("name", "country", "role", "sector", "address", "directors", "owners", "upstream_disclosed"):
            if field not in entity:
                errors.append(f"entity {entity_id}: missing required field '{field}'")
        for owner in entity.get("owners", []):
            share = owner.get("share")
            if not isinstance(share, (float, int)) or not 0 <= share <= 1:
                errors.append(f"entity {entity_id}: owner share must be between 0 and 1")

    for product in data.get("products", []):
        product_id = product.get("id", "<unknown>")
        for field in ("name", "brand", "summary", "root_entity_id", "edges"):
            if field not in product:
                errors.append(f"product {product_id}: missing required field '{field}'")
        if product.get("root_entity_id") not in entities:
            errors.append(f"product {product_id}: unknown root_entity_id '{product.get('root_entity_id')}'")
        graph: dict[str, list[str]] = {}
        for edge in product.get("edges", []):
            for field in ("from", "to", "input", "share"):
                if field not in edge:
                    errors.append(f"product {product_id}: edge missing required field '{field}'")
            source, target = edge.get("from"), edge.get("to")
            if source not in entities:
                errors.append(f"product {product_id}: edge has unknown from entity '{source}'")
            if target not in entities:
                errors.append(f"product {product_id}: edge has unknown to entity '{target}'")
            share = edge.get("share")
            if not isinstance(share, (int, float)) or not 0 <= share <= 1:
                errors.append(f"product {product_id}: edge {source} -> {target} share must be between 0 and 1")
            if source in entities and target in entities:
                graph.setdefault(source, []).append(target)

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                errors.append(f"product {product_id}: supply map contains a cycle through '{node}'")
                return
            if node in visited:
                return
            visiting.add(node)
            for neighbor in graph.get(node, []):
                visit(neighbor)
            visiting.remove(node)
            visited.add(node)

        for node in graph:
            visit(node)

    for event in data.get("enforcement_events", []):
        validate_date(event.get("date"), f"enforcement event {event.get('id', '<unknown>')}", errors)
        if event.get("entity_id") not in entities:
            errors.append(f"enforcement event {event.get('id', '<unknown>')}: unknown entity '{event.get('entity_id')}'")
        if event.get("reliability") not in RELIABILITY:
            errors.append(f"enforcement event {event.get('id', '<unknown')}: unknown reliability '{event.get('reliability')}'")
    for entity_id, profile in data.get("trade_profiles", {}).items():
        if entity_id not in entities:
            errors.append(f"trade profile {profile.get('id', '<unknown>')}: unknown entity '{entity_id}'")
        for month in profile.get("months", []):
            validate_date(month.get("date"), f"trade profile {profile.get('id', '<unknown>')}", errors)
    for entity_id, records in data.get("documents", {}).items():
        if entity_id not in entities:
            errors.append(f"documents: unknown entity '{entity_id}'")
        for document in records:
            document_id = document.get("id", "<unknown>")
            for field in ("type", "date", "reliability", "summary", "ilo_indicators"):
                if field not in document:
                    errors.append(f"document {document_id}: missing required field '{field}'")
            validate_date(document.get("date"), f"document {document_id}", errors)
            if document.get("reliability") not in RELIABILITY:
                errors.append(f"document {document_id}: unknown reliability '{document.get('reliability')}'")
            for indicator in document.get("ilo_indicators", []):
                if indicator not in ILO_INDICATORS:
                    errors.append(f"document {document_id}: unknown ILO indicator '{indicator}'")
    for listing in data.get("listings", []):
        if not listing.get("id") or not listing.get("entity_name"):
            errors.append("listing requires an id and entity_name")
        validate_date(listing.get("date"), f"listing {listing.get('id', '<unknown')}", errors)
        if listing.get("reliability") not in RELIABILITY:
            errors.append(f"listing {listing.get('id', '<unknown')}: unknown reliability '{listing.get('reliability')}'")
    for baseline in data.get("sector_baselines", []):
        score = baseline.get("score")
        if not baseline.get("source_id") or not isinstance(score, (float, int)) or not 0 <= score <= 1:
            errors.append(f"sector baseline {baseline.get('source_id', '<unknown')}: score must be between 0 and 1 and source_id is required")
        if "date" in baseline:
            validate_date(baseline["date"], f"sector baseline {baseline.get('source_id', '<unknown')}", errors)
        if "reliability" in baseline and baseline["reliability"] not in RELIABILITY:
            errors.append(f"sector baseline {baseline.get('source_id', '<unknown')}: unknown reliability '{baseline.get('reliability')}'")

    if errors:
        raise DataValidationError("Invalid mock data:\n- " + "\n- ".join(errors))


def validate_date(value: Any, context: str, errors: list[str]) -> None:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError):
        errors.append(f"{context}: date must be ISO format YYYY-MM-DD")