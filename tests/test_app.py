import json
from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_geographic_view_renders_for_every_product():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()

    product_options = next(item for item in app.selectbox if item.label == "Product").options
    assert len(product_options) == 3
    _assert_geographic_supply_arcs(app)
    assert not app.exception

    for option in product_options:
        next(item for item in app.selectbox if item.label == "Product").select(option).run()
        _assert_geographic_supply_arcs(app)
        assert not app.exception


def _assert_geographic_supply_arcs(app):
    charts = app.get("deck_gl_json_chart")
    assert len(charts) == 1
    deck = json.loads(charts[0].proto.json)
    arc_layer = next(layer for layer in deck["layers"] if layer["@@type"] == "ArcLayer")
    assert arc_layer["data"]
    assert any(link["on_risk_path"] for link in arc_layer["data"])