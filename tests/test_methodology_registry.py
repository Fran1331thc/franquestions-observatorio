from fq_observatorio.methodology_registry import (
    CANONICAL_PRINCIPLE_IDS,
    CT05,
    CT06,
    CT06_CONCLUSION_V1,
    CT06_PREREGISTRATION,
    CT07_PREREGISTRATION,
    EXECUTION_MODES_LAB_ONLY,
    FORBIDDEN_PUBLIC_CAPABILITIES,
    HYBRID_RETURN_TO_LAB_TRIGGERS,
    HUMAN_INTERACTION_HYPOTHESIS,
    PG01,
    PRINCIPLES,
    RP01_PROSPECTIVE_TEST,
    TOOLKIT_01_CONVERGENCE,
    TOOLKIT_EXTENSIONS,
    validate_methodology_registry,
)
from fq_observatorio.reasoning_toolkit import TOOLS


def test_ct05_preserves_complete_authorized_record() -> None:
    assert CT05.id == "CT-05"
    assert CT05.version == "1.0"
    assert len(CT05.hypotheses) == 7
    assert len(CT05.provisional_conclusions) == 9
    assert CT05.knows and CT05.believes and CT05.unknowns
    assert CT05.confidence and CT05.review_triggers
    assert CT05.tool_autopsy and CT05.workflow_autopsy
    assert CT05.self_critique and CT05.closure_audit and CT05.traceability


def test_rp01_ids_and_amended_ct02_origins_are_canonical() -> None:
    assert tuple(principle.id for principle in PRINCIPLES) == CANONICAL_PRINCIPLE_IDS
    by_id = {principle.id: principle for principle in PRINCIPLES}
    for principle_id in ("P-04", "P-05", "P-06"):
        assert by_id[principle_id].origin == "CT-02 - origen reconstruido"
        assert by_id[principle_id].review_condition
        assert by_id[principle_id].future_test


def test_toolkit_remains_twenty_and_extensions_reuse_existing_tools() -> None:
    tool_keys = {tool.key for tool in TOOLS}
    assert len(TOOLS) == 20
    assert all(set(keys) <= tool_keys for keys in TOOLKIT_EXTENSIONS.values())
    validate_methodology_registry(len(TOOLS))


def test_modes_and_interaction_remain_internal_and_experimental() -> None:
    assert EXECUTION_MODES_LAB_ONLY["assisted"] == "valor operativo observado en CT-05"
    assert EXECUTION_MODES_LAB_ONLY["delegated"] == "validado formalmente solo en CT-04"
    hybrid = EXECUTION_MODES_LAB_ONLY["hybrid"]
    assert hybrid.startswith("experimental")
    assert "1 ejecucion formal" in hybrid
    assert "sin validacion ni superioridad" in hybrid
    assert HYBRID_RETURN_TO_LAB_TRIGGERS
    assert "pendiente" in HUMAN_INTERACTION_HYPOTHESIS
    assert "public_execution_modes" in FORBIDDEN_PUBLIC_CAPABILITIES


def test_forbidden_capabilities_cannot_be_exposed() -> None:
    for forbidden in FORBIDDEN_PUBLIC_CAPABILITIES:
        try:
            validate_methodology_registry(len(TOOLS), {forbidden})
        except ValueError as exc:
            assert forbidden in str(exc)
        else:
            raise AssertionError(f"Se expuso una capacidad prohibida: {forbidden}")


def test_ct06_is_preregistered_without_becoming_evidence() -> None:
    assert CT06_PREREGISTRATION.id == "CT-06"
    assert "no investigado" in CT06_PREREGISTRATION.status
    assert CT06_PREREGISTRATION.question_frozen is False
    assert CT06_PREREGISTRATION.execution_mode == "hybrid"
    assert "experimental" in CT06_PREREGISTRATION.execution_mode_status
    assert CT06_PREREGISTRATION.inherited_principles == (
        "P-01", "P-03", "P-06", "P-08", "P-09", "P-10", "P-22", "P-24"
    )
    assert "replicacion por mera inclusion en el pre-registro" in CT06_PREREGISTRATION.forbidden_inferences
    assert len(CT06_PREREGISTRATION.preregistration_questions) == 5


def test_ct06_preregistration_is_preserved_as_historical_sequence() -> None:
    assert CT06_PREREGISTRATION.question_frozen is False
    assert "no investigado" in CT06_PREREGISTRATION.status
    assert "seleccion, causalidad inversa" in CT06_PREREGISTRATION.provisional_question
    assert "causalidad inversa, seleccion" in CT06.question
    assert CT06.traceability[0].startswith("pre-registro historico")


def test_ct06_is_canonical_versioned_and_complete() -> None:
    assert CT06.id == "CT-06"
    assert CT06.version == "1.0"
    assert CT06.status == "Caso canonico - CLOSE PROVISIONAL v1.0 / actualizacion abierta"
    assert "Consolidado" not in CT06.status
    assert len(CT06.hypotheses) == 7
    assert len(CT06.provisional_conclusions) == 7
    assert CT06.knows and CT06.believes and CT06.unknowns
    assert CT06.confidence and CT06.review_triggers
    assert CT06.tool_autopsy and CT06.workflow_autopsy
    assert CT06.self_critique and CT06.closure_audit and CT06.traceability
    assert "exposicion uniforme" in CT06_CONCLUSION_V1
    assert "crisis general" in CT06.self_critique[-1]


def test_rp01_has_one_prospective_run_but_is_not_validated() -> None:
    assert RP01_PROSPECTIVE_TEST.formal_runs == 1
    assert RP01_PROSPECTIVE_TEST.evidence_case == "CT-06"
    assert RP01_PROSPECTIVE_TEST.observed_value == "valor operativo observado"
    assert RP01_PROSPECTIVE_TEST.validation_status.startswith("no validado")


def test_authorized_principle_maturity_and_ct06_activations() -> None:
    by_id = {principle.id: principle for principle in PRINCIPLES}
    assert by_id["P-22"].status == "fortalecido"
    assert by_id["P-24"].status == "fortalecido"
    expected = {
        "P-01": "fortalecido", "P-03": "fortalecido", "P-06": "consolidado",
        "P-08": "fortalecido", "P-09": "consolidado", "P-10": "consolidado",
    }
    for principle_id, status in expected.items():
        assert by_id[principle_id].status == status
        assert "CT-06" in by_id[principle_id].activation


def test_pg01_and_toolkit_convergence_keep_their_boundaries() -> None:
    assert PG01.id == "PG-01"
    assert PG01.id not in CANONICAL_PRINCIPLE_IDS
    assert PG01.canonical_principle is False
    assert "candidato de gobernanza" in PG01.status
    assert TOOLKIT_01_CONVERGENCE.toolkit_version == "0.1"
    assert "no demuestra suficiencia universal" in TOOLKIT_01_CONVERGENCE.limitation


def test_ct04_remains_only_formal_work_codex_validation() -> None:
    assert EXECUTION_MODES_LAB_ONLY["delegated"] == "validado formalmente solo en CT-04"


def test_post_ct06_blocked_capabilities_are_explicit() -> None:
    assert {
        "tool_21", "toolkit_0_2_official", "fq_score", "social_media_score",
        "automatic_causal_weights", "automatic_regulatory_recommendations",
        "public_execution_modes",
    } <= FORBIDDEN_PUBLIC_CAPABILITIES
    validate_methodology_registry(len(TOOLS))


def test_ct07_is_only_an_adversarial_preregistration() -> None:
    assert CT07_PREREGISTRATION.id == "CT-07"
    assert "no investigado" in CT07_PREREGISTRATION.status
    assert "sin evidencia incorporada" in CT07_PREREGISTRATION.status
    assert CT07_PREREGISTRATION.question_frozen is False
    assert len(CT07_PREREGISTRATION.fq_hypotheses) == 5
    assert len(CT07_PREREGISTRATION.initial_alternatives) == 5
    assert len(CT07_PREREGISTRATION.gap_candidate_conditions) == 5


def test_ct07_gap_does_not_pre_authorize_tool_21() -> None:
    assert "GAP-CT07" in CT07_PREREGISTRATION.mandatory_gap_test[-1]
    assert "tool_21" in FORBIDDEN_PUBLIC_CAPABILITIES
    assert any("herramienta 21" in item for item in CT07_PREREGISTRATION.forbidden_inferences)
    assert CT07_PREREGISTRATION.prior_convergence_status.endswith("no confirmada")


def test_ct07_separates_evidence_prediction_and_values() -> None:
    assert tuple(key for key, _ in CT07_PREREGISTRATION.evidence_prediction_values_rule) == (
        "EVIDENCIA", "PREDICCION", "PREFERENCIAS/VALORES"
    )
    assert any("preferencia normativa" in item for item in CT07_PREREGISTRATION.forbidden_inferences)


def test_ct07_does_not_count_as_second_hybrid_run_yet() -> None:
    assert "1 ejecucion formal" in EXECUTION_MODES_LAB_ONLY["hybrid"]
    assert "seria la segunda ejecucion formal solo si" in CT07_PREREGISTRATION.execution_mode_status
    validate_methodology_registry(len(TOOLS))
