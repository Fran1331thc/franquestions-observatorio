from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_acceptance_launcher_uses_expected_apps_and_ports() -> None:
    script = (ROOT / "scripts" / "start_acceptance_review.ps1").read_text(
        encoding="utf-8"
    )

    assert '"streamlit_app.py"' in script
    assert '"fq_observatorio\\updater.py"' in script
    assert "-Port 8501" in script
    assert "-Port 8503" in script
    assert '"REVISION_VISUAL_PUBLICACION.md"' in script


def test_acceptance_launcher_does_not_run_ingestion_or_restore() -> None:
    script = (ROOT / "scripts" / "start_acceptance_review.ps1").read_text(
        encoding="utf-8"
    ).lower()

    assert "execute_exchange_rate_update" not in script
    assert "restore_sqlite_database" not in script
    assert "import_rows" not in script
