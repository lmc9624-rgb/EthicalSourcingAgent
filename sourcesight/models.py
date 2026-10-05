from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    input_name: str
    share: float


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    brand: str
    summary: str
    root_entity_id: str
    edges: tuple[Edge, ...]


@dataclass(frozen=True)
class Entity:
    id: str
    name: str
    country: str
    region: str
    role: str
    sector: str
    address: str
    directors: tuple[str, ...]
    owners: tuple[tuple[str, float], ...]
    upstream_disclosed: bool | None


@dataclass(frozen=True)
class Signal:
    pillar: str
    title: str
    strength: float
    claim_kind: str
    detail: str
    source_ids: tuple[str, ...]
    next_step: str = ""
    source_group: str | None = None


@dataclass(frozen=True)
class SupplierAssessment:
    entity_id: str
    signals: tuple[Signal, ...]
    pillar_scores: dict[str, float]
    composite_score: float
    convergence: int
    own_tier: str
    tier_reason: str
    confidence_score: float
    confidence: str
    ilo_indicators: tuple[str, ...]
    effective_tier: str
    effective_score: float
    inherited_tier: str | None = None
    risk_path: tuple[str, ...] = field(default_factory=tuple)
    risk_source_id: str | None = None


class DataSource(Protocol):
    """Read-only source contract used by signal detection and scoring."""

    def products(self) -> tuple[Product, ...]: ...
    def entities(self) -> dict[str, Entity]: ...
    def listings(self) -> tuple[dict, ...]: ...
    def enforcement_events(self) -> tuple[dict, ...]: ...
    def sector_baselines(self) -> tuple[dict, ...]: ...
    def trade_profiles(self) -> dict[str, dict]: ...
    def documents(self) -> dict[str, tuple[dict, ...]]: ...


@dataclass(frozen=True)
class ProductAssessment:
    product: Product
    suppliers: dict[str, SupplierAssessment]
    effective_tier: str
    own_tier: str
    inherited_tier: str | None
    risk_path: tuple[str, ...]
    risk_source_id: str | None