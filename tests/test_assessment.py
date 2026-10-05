from copy import deepcopy
import json
from pathlib import Path

import pytest

from sourcesight.data import DATA_PATH, MockSource
from sourcesight.engine import _tier, assess_product
from sourcesight.signals import detect_signals
from sourcesight.validation import DataValidationError, validate_data


def fixture_data():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def test_fictional_product_acceptance_cases():
    source = MockSource()
    hoodie = assess_product(source, "hoodie")
    solar = assess_product(source, "solar")
    tuna = assess_product(source, "tuna")

    assert hoodie.effective_tier == "High"
    assert hoodie.risk_source_id == "E05"
    assert hoodie.risk_path == ("E05", "E04", "E03", "E02", "E01")
    assert hoodie.suppliers["E06"].own_tier == "Low"

    strait_crest = solar.suppliers["S04"]
    trade_titles = {signal.title for signal in strait_crest.signals if signal.pillar == "trade"}
    assert trade_titles == {
        "Exports exceed stated monthly capacity",
        "Export volume increased around enforcement event",
    }
    assert strait_crest.own_tier == "High"
    assert solar.suppliers["S06"].own_tier == "Watch"

    assert tuna.suppliers["T05"].own_tier == "Elevated"
    assert "debt_bondage" in tuna.suppliers["T05"].ilo_indicators
    assert tuna.suppliers["T06"].own_tier == "Low"


def test_valid_mock_data_exposes_provenance_contract():
    source = MockSource()
    assert {product.id for product in source.products()} == {"hoodie", "solar", "tuna"}
    doc = source.documents()["T05"][0]
    assert {"id", "type", "date", "reliability", "summary", "ilo_indicators"} <= doc.keys()
    assert source.listings()[0]["id"]
    assert source.enforcement_events()[0]["id"]
    assert source.sector_baselines()[0]["source_id"]
    assert source.trade_profiles()["S04"]["id"]


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda data: data["products"][0]["edges"][0].update({"to": "MISSING"}), "unknown to entity"),
        (lambda data: data["products"][0]["edges"][0].update({"share": 1.1}), "share must be between 0 and 1"),
        (lambda data: data["products"][0]["edges"].append({"from": "E01", "to": "E05", "input": "cycle", "share": 0.2}), "contains a cycle"),
        (lambda data: data["documents"]["T05"][0].update({"reliability": "unknown"}), "unknown reliability"),
        (lambda data: data["documents"]["T05"][0]["ilo_indicators"].append("unknown_indicator"), "unknown ILO indicator"),
        (lambda data: data["documents"]["T05"][0].update({"date": "yesterday"}), "date must be ISO"),
    ],
)
def test_invalid_fixture_data_fails_with_actionable_error(mutate, message):
    data = deepcopy(fixture_data())
    mutate(data)
    with pytest.raises(DataValidationError, match=message):
        validate_data(data)


def test_low_share_still_inherits_tier_and_retains_path():
    data = fixture_data()
    data["products"][0]["edges"][0]["share"] = 0.1
    assessment = assess_product(MockSource(data), "hoodie")
    assert assessment.effective_tier == "High"
    assert assessment.risk_source_id == "E05"
    assert assessment.risk_path[-1] == "E01"
    assert assessment.suppliers["E04"].effective_score < assessment.suppliers["E05"].effective_score


def test_tier_threshold_semantics_are_inclusive_as_specified():
    assert _tier(False, 3, 0.0)[0] == "High"
    assert _tier(False, 2, 0.85)[0] == "High"
    assert _tier(False, 2, 0.8499)[0] == "Elevated"
    assert _tier(False, 0, 0.6)[0] == "Elevated"
    assert _tier(False, 1, 0.0)[0] == "Watch"
    assert _tier(False, 0, 0.3)[0] == "Watch"
    assert _tier(False, 0, 0.2999)[0] == "Low"


def test_assessment_accepts_an_injected_data_source():
    class WrappedSource:
        def __init__(self):
            self.source = MockSource()

        def __getattr__(self, name):
            return getattr(self.source, name)

    assert assess_product(WrappedSource(), "tuna").suppliers["T05"].own_tier == "Elevated"


def test_exposure_uses_the_most_specific_matching_baseline():
    signals = detect_signals("E05", MockSource(), mapped_inputs=True)
    exposure = next(signal for signal in signals if signal.pillar == "exposure")
    assert exposure.source_ids == ("BASE-MOCK-COTTON-XJ",)
    assert exposure.strength == 0.8


def test_minor_ownership_network_edge_uses_specified_strength():
    data = fixture_data()
    data["entities"]["E06"]["owners"] = [{"name": "Strait Crest Holdings", "share": 0.49}]
    signals = detect_signals("E06", MockSource(data), mapped_inputs=False)
    linkage = next(signal for signal in signals if signal.pillar == "linkage")
    assert linkage.claim_kind == "INFERENCE"
    assert linkage.strength == pytest.approx(0.6)
    assert linkage.source_ids == ("LIST-MOCK-02",)


def test_network_linkage_uses_two_hops_and_stops_at_the_limit():
    data = fixture_data()
    for entity_id, name, directors in (
        ("N01", "Network Source One", ["Chain A"]),
        ("N02", "Network Source Two", ["Chain A", "Chain B"]),
        ("N03", "Network Listed Three", ["Chain B", "Chain C"]),
        ("N04", "Network Listed Four", ["Chain C"]),
    ):
        data["entities"][entity_id] = {
            "name": name, "country": "XX", "region": "", "role": "test entity", "sector": "test",
            "address": entity_id, "directors": directors, "owners": [], "upstream_disclosed": True,
        }
    data["listings"].append({"id": "LIST-N03", "entity_name": "Network Listed Three", "date": "2025-01-01", "source_type": "fictional test", "reliability": "high"})
    source = MockSource(data)
    linkage = next(signal for signal in detect_signals("N01", source, False) if signal.pillar == "linkage")
    assert linkage.source_ids == ("LIST-N03",)
    assert linkage.strength == pytest.approx(0.55**2)

    data["listings"] = [item for item in data["listings"] if item["id"] != "LIST-N03"]
    data["listings"].append({"id": "LIST-N04", "entity_name": "Network Listed Four", "date": "2025-01-01", "source_type": "fictional test", "reliability": "high"})
    signals = detect_signals("N01", MockSource(data), False)
    assert not any(signal.pillar == "linkage" for signal in signals)


def test_missing_and_short_trade_series_do_not_create_unsupported_signals():
    data = fixture_data()
    data["trade_profiles"].pop("S04")
    assert not any(signal.pillar == "trade" for signal in detect_signals("S04", MockSource(data), False))
    data = fixture_data()
    data["trade_profiles"]["S04"]["months"] = []
    assert not any(signal.pillar == "trade" for signal in detect_signals("S04", MockSource(data), False))


def test_worker_reliability_changes_claim_and_strength_not_provenance():
    data = fixture_data()
    data["documents"]["T05"][0]["reliability"] = "medium"
    signal = next(signal for signal in detect_signals("T05", MockSource(data), False) if signal.pillar == "worker")
    assert signal.claim_kind == "LEAD"
    assert signal.strength == pytest.approx(0.75 * 0.75)
    assert signal.source_ids == ("DOC-MOCK-T05",)


def test_transparency_affects_composite_and_confidence_but_not_convergence():
    data = fixture_data()
    exposed = assess_product(MockSource(data), "hoodie").suppliers["E01"]
    data["entities"]["E01"]["upstream_disclosed"] = False
    undisclosed = assess_product(MockSource(data), "hoodie").suppliers["E01"]
    assert exposed.convergence == undisclosed.convergence == 0
    assert exposed.own_tier == undisclosed.own_tier == "Low"
    assert undisclosed.pillar_scores["transparency"] == 0.6
    assert undisclosed.composite_score > exposed.composite_score
    assert undisclosed.confidence_score < exposed.confidence_score