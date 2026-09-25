"""Controles del checkpoint comercial sin activar funciones de producto."""

from fq_observatorio.commercial_transition import (
    CHECKPOINT,
    COMMERCIAL_MATRIX,
    CT07_PROGRESS,
    FREE_BETA_TOOL_KEYS,
    GAP_CT07_B,
    PUBLIC_BETA_CHECKPOINT,
    validate_commercial_transition,
)
from fq_observatorio.entitlements import PLAN_FEATURES
from fq_observatorio.methodology_registry import CT07_PREREGISTRATION
from fq_observatorio.reasoning_toolkit import TOOLS, candidate_features


def test_checkpoint_preserves_research_sequence_and_launch_rule() -> None:
    assert CT07_PREREGISTRATION.status == "seleccionado / no investigado / sin evidencia incorporada"
    assert CT07_PROGRESS.status == "pausada / cierre no completado"
    assert CT07_PROGRESS.last_reached_block == 5
    assert GAP_CT07_B.status == "candidato pendiente"
    assert GAP_CT07_B.id in CHECKPOINT.pending_research
    assert "no bloquean automáticamente" in CHECKPOINT.launch_policy
    assert CHECKPOINT.pro_stage.startswith("Pro es una etapa comercial posterior")
    assert CHECKPOINT.public_behavior_change is False
    assert PUBLIC_BETA_CHECKPOINT.public_behavior_change is True
    assert PUBLIC_BETA_CHECKPOINT.date == "2026-09-24"


def test_matrix_covers_canonical_tools_and_only_grants_the_free_beta_scope() -> None:
    assert len(TOOLS) == len(COMMERCIAL_MATRIX) == 20
    assert [(row.tool_number, row.tool_key, row.technical_maturity) for row in COMMERCIAL_MATRIX] == [
        (tool.number, tool.key, tool.maturity) for tool in TOOLS
    ]
    assert all(row.observed_utility and row.limitations and row.possible_plan for row in COMMERCIAL_MATRIX)
    public_rows = {row.tool_key for row in COMMERCIAL_MATRIX if row.public_exposure_authorized}
    assert public_rows == FREE_BETA_TOOL_KEYS
    assert all(
        row.current_access == ("public" if row.tool_key in FREE_BETA_TOOL_KEYS else "owner")
        for row in COMMERCIAL_MATRIX
    )
    assert CHECKPOINT.price_status == "sin precios definitivos"


def test_six_experimental_capabilities_remain_owner_only() -> None:
    for feature in candidate_features():
        assert feature in PLAN_FEATURES["owner"]
        assert all(feature not in PLAN_FEATURES[plan] for plan in ("public", "pro", "business", "institutional"))
    validate_commercial_transition()
