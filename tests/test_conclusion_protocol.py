from datetime import date

from fq_observatorio.intelligence import (
    build_conclusion_protocol,
    build_fq_reading,
    build_research_brief,
)


def sample_analysis() -> dict:
    return {
        "latest_period": date(2026, 6, 30),
        "latest_value": 3.5,
        "previous_period": date(2026, 5, 31),
        "previous_value": 3.4,
        "recent_change": 0.1,
        "recent_percent": None,
        "annual_period": date(2025, 6, 30),
        "annual_value": 3.0,
        "annual_change": 0.5,
        "annual_percent": None,
        "trend": "Al alza",
        "trend_observations": 6,
        "is_rate": True,
    }


def test_protocol_exposes_revisable_knowledge_contract() -> None:
    protocol = build_conclusion_protocol("economic-activity")

    assert protocol["fact_state"] == "Sabemos"
    assert protocol["knowledge_state"] == "Creemos provisionalmente"
    assert protocol["mandatory_question"] == "¿Qué evidencia nos haría cambiar de parecer?"
    assert protocol["revision_condition"]
    assert protocol["remaining_uncertainty"]
    assert protocol["principle"] == "Una conclusión no merece protección. El método sí."


def test_reading_preserves_protocol_fields() -> None:
    reading = build_fq_reading(
        "economic-activity",
        "IMAE tendencia-ciclo",
        sample_analysis(),
    )

    for field in (
        "fact_state",
        "knowledge_state",
        "mandatory_question",
        "change_mind_evidence",
        "remaining_uncertainty",
        "revision_condition",
        "principle",
    ):
        assert reading[field]


def test_research_brief_makes_revision_logic_visible() -> None:
    analysis = sample_analysis()
    reading = build_fq_reading("economic-activity", "IMAE tendencia-ciclo", analysis)
    brief = build_research_brief(
        "economic-activity",
        "IMAE tendencia-ciclo",
        analysis,
        reading,
        [],
        "BCCR",
        "https://www.bccr.fi.cr/",
        "% interanual",
    )

    assert "ESTADO DEL CONOCIMIENTO" in brief
    assert "¿QUÉ EVIDENCIA NOS HARÍA CAMBIAR DE PARECER?" in brief
    assert "INCERTIDUMBRE RESTANTE" in brief
    assert "CONDICIÓN DE REVISIÓN" in brief
    assert "Una conclusión no merece protección. El método sí." in brief
