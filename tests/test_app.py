import json
from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_geographic_view_renders_for_every_product():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()
    workspace = next(item for item in app.selectbox if item.label == "Workspace")
    workspace.select("Fictional demo").run()

    product_options = next(item for item in app.selectbox if item.label == "Product").options
    assert len(product_options) == 3
    _assert_geographic_supply_arcs(app)
    assert not app.exception

    for option in product_options:
        next(item for item in app.selectbox if item.label == "Product").select(option).run()
        _assert_geographic_supply_arcs(app)
        assert not app.exception


def test_solar_supplier_evidence_shows_observed_route_shift():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()
    next(item for item in app.selectbox if item.label == "Workspace").select("Fictional demo").run()
    product_selector = next(item for item in app.selectbox if item.label == "Product")
    product_selector.select("Residential Solar Module - Daybreak Energy").run()

    signal_table = next(frame.value for frame in app.dataframe if "Signal" in frame.value.columns)
    route_signal = signal_table[signal_table["Signal"] == "Trade route mix shifted around enforcement event"]
    assert len(route_signal) == 1
    assert route_signal.iloc[0]["Claim"] == "INFERENCE"
    assert "EVENT-MOCK-01" in route_signal.iloc[0]["Source IDs"]
    assert not app.exception


def test_fictional_demo_is_default_and_featured_case_remains_optional():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()
    workspace = next(item for item in app.selectbox if item.label == "Workspace")
    assert workspace.value == "Fictional demo"
    assert any(item.label == "Product" for item in app.selectbox)

    workspace.select("Featured case study").run()
    assert any("not independently verified by SourceSight" in item.value for item in app.warning)
    assert any("unknown. No live list lookup has been run" in item.value for item in app.info)
    assert any(item.label == "Report profile" for item in app.selectbox)
    assert any("not independent corroboration" in item.value for item in app.caption)
    assert not app.exception


def _assert_geographic_supply_arcs(app):
    charts = app.get("deck_gl_json_chart")
    assert len(charts) == 1
    deck = json.loads(charts[0].proto.json)
    arc_layer = next(layer for layer in deck["layers"] if layer["@@type"] == "ArcLayer")
    assert arc_layer["data"]
    assert any(link["on_risk_path"] for link in arc_layer["data"])