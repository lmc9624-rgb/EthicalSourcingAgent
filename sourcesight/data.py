from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sourcesight.models import Edge, Entity, Product
from sourcesight.validation import validate_data


DATA_PATH = Path(__file__).parent / "fixtures" / "mock_data.json"


class MockSource:
    """JSON-backed fictional data provider implementing the DataSource contract."""

    def __init__(self, data: dict[str, Any] | None = None):
        if data is None:
            with DATA_PATH.open(encoding="utf-8") as fixture_file:
                data = json.load(fixture_file)
        validate_data(data)
        self._data = data

    def products(self) -> tuple[Product, ...]:
        return tuple(Product(
            id=item["id"], name=item["name"], brand=item["brand"], summary=item["summary"],
            root_entity_id=item["root_entity_id"],
            edges=tuple(Edge(edge["from"], edge["to"], edge["input"], float(edge["share"])) for edge in item["edges"]),
        ) for item in self._data["products"])

    def entities(self) -> dict[str, Entity]:
        return {entity_id: Entity(
            id=entity_id, name=item["name"], country=item["country"], region=item.get("region", ""),
            role=item["role"], sector=item["sector"], address=item["address"],
            directors=tuple(item["directors"]),
            owners=tuple((owner["name"], float(owner["share"])) for owner in item["owners"]),
            upstream_disclosed=bool(item["upstream_disclosed"]),
        ) for entity_id, item in self._data["entities"].items()}

    def listings(self) -> tuple[dict, ...]:
        return tuple(self._data["listings"])

    def enforcement_events(self) -> tuple[dict, ...]:
        return tuple(self._data["enforcement_events"])

    def sector_baselines(self) -> tuple[dict, ...]:
        return tuple(self._data["sector_baselines"])

    def trade_profiles(self) -> dict[str, dict]:
        return self._data["trade_profiles"]

    def documents(self) -> dict[str, tuple[dict, ...]]:
        return {entity_id: tuple(records) for entity_id, records in self._data["documents"].items()}