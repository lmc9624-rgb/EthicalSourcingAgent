import json

from sourcesight import case_enrichment
from sourcesight.case_study import COMPANIES, possible_buyer_relationships


def test_case_screen_matches_names_and_aliases_exactly_and_preserves_review_status(tmp_path, monkeypatch):
    def fake_download(record, cache_dir, refresh=False):
        path = cache_dir / record["filename"]
        path.parent.mkdir(parents=True, exist_ok=True)
        if "us_dhs_uflpa" in path.name:
            path.write_text('id,name,aliases\n1,"Dell Inc.","Dell Technologies|Dell"\n', encoding="utf-8")
        else:
            path.write_text("id,name,aliases\n", encoding="utf-8")
        path.with_suffix(path.suffix + ".source.json").write_text(json.dumps({
            "retrieved_at": "2026-10-05T12:00:00+00:00",
        }), encoding="utf-8")
        return path, False

    monkeypatch.setattr(case_enrichment.data_requests, "_download", fake_download)
    report = case_enrichment.screen_case_companies(tmp_path)

    dell = report["companies"]["Dell"]
    assert dell["datasets"]["us_dhs_uflpa"] == "Exact name/alias candidate"
    assert dell["matches"][0]["listed_name"] == "Dell Inc."
    assert dell["matches"][0]["match_basis"].endswith("identity unconfirmed")
    assert dell["datasets"]["us_cbp_forced_labor"] == "No exact match in this snapshot"
    assert len(report["snapshots"]) == 3
    assert "do not change SourceSight tiers" in report["disclaimer"]


def test_case_screen_does_not_fuzzy_match_and_includes_named_companies(tmp_path, monkeypatch):
    def fake_download(record, cache_dir, refresh=False):
        path = cache_dir / record["filename"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("id,name,aliases\n1,Amazonia LLC,\n", encoding="utf-8")
        return path, True

    monkeypatch.setattr(case_enrichment.data_requests, "_download", fake_download)
    report = case_enrichment.screen_case_companies(tmp_path)
    assert "Compal Electronics" in report["companies"]
    assert "Amazon" in report["companies"]
    assert report["companies"]["Amazon"]["matches"] == []


def test_report_named_buyers_have_conditional_tier_positions_and_do_not_propagate():
    aot = next(company for company in COMPANIES if company["id"] == "TSM-AOT")
    relationships = possible_buyer_relationships(aot)
    assert {item["company"] for item in relationships} == {"Garmin", "Samsung"}
    assert all("Tier 1 downstream if confirmed" in item["tier_position"] for item in relationships)
    assert all(not item["propagates_risk"] for item in relationships)
    assert all("Former" in item["status"] for item in relationships)