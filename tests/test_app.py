import json
from pathlib import Path

from streamlit.testing.v1 import AppTest


EXPECTED_PRODUCTS = {
    "Notebook computers - Compal Electronics",
    "GPS devices - Garmin",
    "Contact lenses - Pegavision",
    "Vehicles - China Motor Corporation",
    "Optoelectronic components - Advanced Optoelectronic Technology (AOT)",
    "Electronics - Digital Generation International (DGI)",
    "Water pumps - Tsurumi Pump",
}


def test_product_selector_uses_seven_report_products_and_existing_tabs():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()

    product_selector = next(item for item in app.selectbox if item.label == "Product")
    assert set(product_selector.options) == EXPECTED_PRODUCTS
    assert product_selector.value == "Notebook computers - Compal Electronics"
    product_summary = next(item.value for item in app.markdown
                           if "Report-attributed recruitment-fee investigation" in item.value)
    assert "USD 2,050-USD 6,400" in product_summary
    assert [tab.label for tab in app.tabs] == [
        "Supply map", "Geographic view", "Supplier evidence", "How scoring works"
    ]
    assert any("REPORT-ATTRIBUTED CASE MATERIAL" in item.value for item in app.warning)
    assert not app.exception

    for option in product_selector.options:
        next(item for item in app.selectbox if item.label == "Product").select(option).run()
        assert not app.exception


def test_possible_buyers_are_not_rendered_as_confirmed_supply_edges():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()

    assert any("No confirmed supplier-input edges" in item.value for item in app.info)
    assert any("not treated as confirmed customers" in item.value for item in app.info)
    assert not app.exception


def test_report_geography_uses_only_approximate_country_centroid():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()
    deck = json.loads(app.get("deck_gl_json_chart")[0].proto.json)
    marker_layer = next(layer for layer in deck["layers"] if layer["@@type"] == "ScatterplotLayer")
    assert marker_layer["data"][0]["location"] == "Country level, TW"
    assert marker_layer["data"][0]["latitude"] == 23.7
    assert marker_layer["data"][0]["longitude"] == 120.96
    assert not app.exception
