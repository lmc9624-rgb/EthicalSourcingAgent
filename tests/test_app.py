from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_geographic_view_renders_for_every_product():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()

    product_options = next(item for item in app.selectbox if item.label == "Product").options
    assert len(product_options) == 3
    assert len(app.get("deck_gl_json_chart")) == 1
    assert not app.exception

    for option in product_options:
        next(item for item in app.selectbox if item.label == "Product").select(option).run()
        assert len(app.get("deck_gl_json_chart")) == 1
        assert not app.exception