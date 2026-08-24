from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTECTED_BRAND = '<span translate="no" class="notranslate">FranQuestions</span>'


def test_brand_is_protected_in_public_and_local_interfaces():
    files = (
        ROOT / "streamlit_app_stable.py",
        ROOT / "fq_observatorio" / "dashboard.py",
        ROOT / "fq_observatorio" / "updater.py",
    )

    for path in files:
        assert PROTECTED_BRAND in path.read_text(encoding="utf-8")


def test_translation_is_not_disabled_for_the_whole_heading_or_page():
    public_source = (ROOT / "streamlit_app_stable.py").read_text(encoding="utf-8")
    dashboard_source = (ROOT / "fq_observatorio" / "dashboard.py").read_text(
        encoding="utf-8"
    )

    for source in (public_source, dashboard_source):
        assert '<h1 translate="no"' not in source
        assert 'name="google" content="notranslate"' not in source


def test_widget_labels_do_not_expose_the_brand_to_page_translation():
    public_source = (ROOT / "streamlit_app_stable.py").read_text(encoding="utf-8")
    dashboard_source = (ROOT / "fq_observatorio" / "dashboard.py").read_text(
        encoding="utf-8"
    )

    assert "¿Cómo usar FranQuestions?" not in public_source
    assert "Lectura FranQuestions:" not in public_source
    assert "Cómo usar FranQuestions" not in dashboard_source
    assert "Lectura FranQuestions:" not in dashboard_source
