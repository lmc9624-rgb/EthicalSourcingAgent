import json
from pathlib import Path

from streamlit.testing.v1 import AppTest
from app import _selected_map_node, investigation_map_data
from sourcesight.case_study import recruitment_debt_profiles


EXPECTED_PRODUCTS = {
    "Compal Electronics | Notebook PC Manufacturing",
    "Garmin | GPS Device Manufacturing",
    "Pegavision | Contact Lens Manufacturing",
    "China Motor Corporation | Vehicle Manufacturing",
    "Advanced Optoelectronic Technology (AOT) | Optoelectronic Component Manufacturing",
    "Digital Generation International (DGI) | Electronics Manufacturing",
    "Tsurumi Pump | Water Pump Manufacturing",
}


def test_product_selector_uses_seven_report_products_and_existing_tabs():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()

    product_selector = next(item for item in app.selectbox if item.label == "Product")
    assert set(product_selector.options) == EXPECTED_PRODUCTS
    assert product_selector.value == "Compal Electronics | Notebook PC Manufacturing"
    assert any(item.value == "Compal Electronics | Notebook PC Manufacturing" for item in app.subheader)
    product_summary = next(item.value for item in app.markdown
                           if "Report-attributed recruitment-fee investigation" in item.value)
    assert "USD 2,050-USD 6,400" in product_summary
    assert [tab.label for tab in app.tabs] == [
        "Geographic view", "Supply map", "Supplier evidence", "How scoring works"
    ]
    assert any("REPORT-ATTRIBUTED CASE MATERIAL" in item.value for item in app.warning)
    assert not app.exception
    for option in product_selector.options:
        next(item for item in app.selectbox if item.label == "Product").select(option).run()
        assert not app.exception


def test_branded_header_has_logo_and_investigation_heading():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()
    header = next(item.value for item in app.markdown
                  if "Recruitment Debt in Taiwan's Supply Chains" in item.value)
    assert "SourceSight" in header
    assert "Recruitment Debt in Taiwan's Supply Chains" in header
    assert "viewBox=\"0 0 48 48\"" in header
    assert not app.exception


def test_possible_buyers_are_not_rendered_as_confirmed_supply_edges():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()
    next(tab for tab in app.tabs if tab.label == "Supply map").run()

    assert any("No confirmed supplier-input edges" in item.value for item in app.info)
    assert any("not treated as confirmed customers" in item.value for item in app.info)
    assert not app.exception


def test_report_geography_has_clickable_investigation_entities():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()
    assert app.tabs[0].label == "Geographic view"
    deck = json.loads(app.get("deck_gl_json_chart")[0].proto.json)
    layer_ids = {layer.get("id") for layer in deck["layers"]}
    assert "investigation-entities" in layer_ids
    assert "investigation-relationships" in layer_ids
    entity_layer = next(layer for layer in deck["layers"] if layer.get("id") == "investigation-entities")
    names = {point["name"] for point in entity_layer["data"]}
    assert "Compal Electronics" in names
    assert "Advanced Optoelectronic Technology (AOT)" in names
    assert "Unnamed Vietnamese recruitment agency" in names
    assert "Mitsubishi Motors" in names
    assert "Worker home country: VN" in names
    manufacturer_nodes = [point for point in entity_layer["data"]
                          if point["node_type"] == "Investigated manufacturer"]
    assert manufacturer_nodes
    assert all(point["color"] == [240, 161, 93, 240] for point in manufacturer_nodes)
    buyer_layer = next(layer for layer in deck["layers"] if layer.get("id") == "investigation-contacted-buyers")
    assert buyer_layer["@@type"] == "PolygonLayer"
    assert buyer_layer["data"]
    assert all(point["symbol"] == "◆" for point in buyer_layer["data"])
    assert all(len(point["marker_polygon"]) == 4 for point in buyer_layer["data"])
    assert all(point.get("issue") and point.get("source_note") for point in entity_layer["data"])
    home_node = next(point for point in entity_layer["data"] if point["node_id"] == "WORKER-HOME-VN")
    assert home_node["linked_score"] is None
    assert home_node["tier"] == "Context only"
    aot_node = next(point for point in entity_layer["data"] if point["node_id"] == "TSM-AOT")
    assert 24.85 <= aot_node["latitude"] <= 24.95
    assert 120.99 <= aot_node["longitude"] <= 121.13
    assert any("Selected investigation point" in item.value for item in app.markdown)
    assert any("Investigated manufacturer (orange)" in item.value for item in app.markdown)
    assert any("Contacted buyer; possible connection" in item.value for item in app.markdown)
    assert any("Worker recruitment corridor" in item.value for item in app.markdown)
    assert not app.exception


def test_recruitment_debt_lens_compares_fee_ranges_without_extrapolating_population_totals():
    profiles = recruitment_debt_profiles()
    assert len(profiles) == 7
    aot = next(item for item in profiles if item["company_id"] == "TSM-AOT")
    assert (aot["fee_low_usd"], aot["fee_high_usd"]) == (1000, 1200)
    assert (aot["workers_with_reported_fees"], aot["workers_interviewed"]) == (3, 4)
    assert "currency-switch loan" in aot["debt_evidence"]
    assert "total_fee_usd" not in aot

    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()
    assert any("Recruitment-debt lens" in item.value for item in app.markdown)
    debt_table = next(frame.value for frame in app.dataframe
                      if "Reported fee range per worker" in frame.value.columns)
    assert len(debt_table) == 7
    assert not app.exception


def test_pydeck_single_object_selection_picks_clicked_node():
    class MapSelection:
        selection = {"objects": {"investigation-contacted-buyers": [{"node_id": "CONTACTED-BUYERS-US"}]}}

    assert _selected_map_node(MapSelection()) == "CONTACTED-BUYERS-US"


def test_map_scores_recruiter_from_own_evidence_and_affiliates_as_linked_exposure():
    from sourcesight.case_study import CaseStudySource

    nodes, _, details, _ = investigation_map_data(CaseStudySource())
    by_id = {node["node_id"]: node for node in nodes}
    recruiter = by_id["TSM-AGENCY"]
    mitsubishi = by_id["AFFILIATE-TSM-CMC-mitsubishi-motors"]

    assert recruiter["own_score"] is not None
    assert recruiter["linked_score"] == recruiter["own_score"]
    assert recruiter["investigated"]
    assert mitsubishi["own_score"] is None
    assert mitsubishi["linked_score"] > 0
    assert not mitsubishi["investigated"]
    assert "not an independent allegation" in details[mitsubishi["node_id"]]["source_note"]


def test_case_study_exposes_opt_in_public_list_screen_without_running_it():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()
    assert any(button.label == "Run public list screening" for button in app.button)
    assert any("Sayari and Tradeverifyd adapters and credentials are not present" in item.value
               for item in app.warning)
    assert not app.exception


def test_supply_map_shows_cmc_affiliates_and_report_location_context():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()
    product_selector = next(item for item in app.selectbox if item.label == "Product")
    product_selector.select("China Motor Corporation | Vehicle Manufacturing").run()
    next(tab for tab in app.tabs if tab.label == "Supply map").run()

    affiliation_table = next(
        frame.value for frame in app.dataframe
        if {"Company", "Connection", "Report location", "Location precision", "Report status", "Exposure"}
        <= set(frame.value.columns)
    )
    companies = set(affiliation_table["Company"])
    assert "China Motor Corporation" in companies
    assert "Mitsubishi Motors" in companies
    assert "Yulon Group-linked holders" in companies
    mitsubishi = affiliation_table[affiliation_table["Company"] == "Mitsubishi Motors"].iloc[0]
    assert "JP" in mitsubishi["Report location"]
    assert "ownership lead" in mitsubishi["Connection"]
    assert "Linked only" in mitsubishi["Exposure"]
    assert not app.exception


def test_additional_pdf_analysis_is_visible_as_inactive_preview():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()
    assert any("PDF-to-map analysis is not implemented" in item.value for item in app.caption)
    assert any(item.value == "Agentic report analysis" for item in app.subheader)
    assert any(item.label == "Generate map from report" and not item.disabled for item in app.button)
    assert not app.exception


def test_fake_report_map_action_does_not_analyze_or_change_assessment():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()
    next(item for item in app.button if item.label == "Generate map from report").click().run()
    assert any("PDF was not read" in item.value for item in app.info)
    assert any("PDF-to-map analysis is not implemented" in item.value for item in app.caption)
    assert not app.exception
