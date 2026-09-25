from datetime import date, datetime, timezone
from pathlib import Path
import sqlite3

from fq_observatorio.catalog import CATALOG
from fq_observatorio.entitlements import features_for_plan, has_feature, normalize_plan
from fq_observatorio.intelligence import analyze_series
from fq_observatorio.public_reading import build_public_reading, validate_public_reading


ROOT = Path(__file__).resolve().parents[1]


def sample_analysis() -> dict:
    return {
        "latest_period": date(2026, 6, 30),
        "latest_value": 3.5,
        "previous_period": date(2026, 5, 31),
        "previous_value": 3.4,
        "recent_change": 0.1,
        "recent_percent": None,
        "annual_reference_period": date(2025, 6, 30),
        "annual_change": 0.5,
        "annual_percent": None,
        "trend": "Al alza",
        "trend_observations": 6,
        "is_rate": True,
    }


def build_valid_reading():
    return build_public_reading(
        slug="imae",
        name="IMAE tendencia-ciclo",
        unit="% interanual",
        source="BCCR",
        source_url="https://www.bccr.fi.cr/",
        analysis=sample_analysis(),
        consulted_on=date(2026, 9, 24),
        generated_at=datetime(2026, 9, 24, 12, tzinfo=timezone.utc),
    )


def test_unknown_or_empty_plans_are_denied_by_default() -> None:
    assert normalize_plan(None) is None
    assert normalize_plan("") is None
    assert normalize_plan("inventado") is None
    assert not has_feature("inventado", "reasoning_foundations_lab")
    assert features_for_plan("inventado") == ()
    assert normalize_plan(" OWNER ") == "owner"
    assert has_feature("public", "public_reasoning_reading")
    assert not has_feature("public", "reasoning_foundations_lab")


def test_public_reading_separates_description_from_causality() -> None:
    reading = build_valid_reading()

    assert reading.status == "complete"
    assert reading.evidence_class == "serie oficial descriptiva/observacional"
    assert reading.causal_magnitude_status == "not_estimated"
    assert reading.sufficiency_status == "not_demonstrated"
    assert reading.confidence[0].level == "sustentada"
    assert reading.confidence[1].level == "no determinada"
    validate_public_reading(reading)


def test_single_source_is_not_mislabeled_as_corroborated() -> None:
    reading = build_valid_reading()
    assert reading.corroboration_status == "single_source"


def test_missing_verifiable_source_blocks_publication() -> None:
    reading = build_public_reading(
        slug="imae",
        name="IMAE tendencia-ciclo",
        unit="% interanual",
        source="BCCR",
        source_url="http://example.invalid/source",
        analysis=sample_analysis(),
    )

    assert reading.status == "blocked"
    assert reading.blocking_reasons
    assert reading.confidence[0].level == "no asignada"
    validate_public_reading(reading)


def test_trace_preserves_source_observation_claim_and_limit() -> None:
    reading = build_valid_reading()
    trace = " ".join(reading.trace)
    assert "Fuente:" in trace
    assert "Observación:" in trace
    assert "Afirmación:" in trace
    assert "Límite:" in trace


def test_catalog_database_builds_complete_public_readings() -> None:
    with sqlite3.connect(ROOT / "franquestions.db") as connection:
        for slug, item in CATALOG.items():
            rows = [
                {"period": period, "value": value}
                for period, value in connection.execute(
                    """
                    SELECT o.period, o.value
                    FROM observations AS o
                    JOIN series AS s ON s.id = o.series_id
                    WHERE s.slug = ?
                    ORDER BY o.period
                    """,
                    (slug,),
                )
            ]
            analysis = analyze_series(
                rows,
                item.observation_frequency or item.frequency,
                item.unit,
            )
            reading = build_public_reading(
                slug=slug,
                name=item.name,
                unit=item.unit,
                source=item.source,
                source_url=item.source_url,
                analysis=analysis,
                caveat=item.caveat,
            )

            validate_public_reading(reading)
            assert reading.status == "complete", (slug, reading.blocking_reasons)
