"""Checkpoint interno de transición comercial; no modifica permisos de producto."""

from __future__ import annotations

from dataclasses import dataclass

from .entitlements import PLAN_FEATURES
from .methodology_registry import CT05, CT06, CT07_PREREGISTRATION
from .reasoning_toolkit import TOOLS, WORKFLOWS, candidate_features


@dataclass(frozen=True)
class PendingResearch:
    id: str
    parent_case: str
    status: str
    last_reached_block: int | None
    evidence_status: str
    next_step: str
    source: str


@dataclass(frozen=True)
class CommercialMatrixRow:
    tool_number: int
    tool_key: str
    tool_name: str
    workflow: str
    technical_maturity: str
    evidence_refs: tuple[str, ...]
    observed_utility: str
    limitations: str
    public_exposure_authorized: bool
    current_access: str
    possible_plan: str
    commercial_assignment_status: str


@dataclass(frozen=True)
class TransitionCheckpoint:
    id: str
    date: str
    toolkit_version: str
    toolkit_size: int
    preserved_cases: tuple[str, ...]
    historical_sources: tuple[str, ...]
    pending_research: tuple[str, ...]
    launch_policy: str
    launch_gate: str
    pro_stage: str
    price_status: str
    public_behavior_change: bool


# Referencias a expedientes existentes. Una celda vacía significa que la
# activación individual aún no está documentada en el registro local.
_EVIDENCE = {
    "definition_test": (("CT-05/tool_autopsy", "CT-06/tool_autopsy"), "Separó unidades, exposición y resultados.", "La definición no demuestra causalidad."),
    "evidence_classification": (("CT-06/tool_autopsy",), "Distinguió diseños observacionales, experimentales y síntesis.", "Clasificar no aumenta la calidad de la fuente."),
    "source_corroboration": (("CT-05/tool_autopsy",), "Hizo explícitos incentivos y límites de datos comerciales.", "Corroborar no elimina sesgo residual."),
    "mechanism_magnitude_sufficiency": (("CT-05/tool_autopsy", "CT-06/tool_autopsy"), "Bloqueó inferencias de magnitud y suficiencia sin estimaciones.", "Un mecanismo plausible no cuantifica su contribución."),
    "outcome_decomposition": (("CT-05/tool_autopsy", "CT-06/tool_autopsy"), "Separó resultados habitacionales y de salud distintos.", "Requiere definiciones y datos para cada resultado."),
    "attribution_map": (("CT-05/tool_autopsy", "CT-06/tool_autopsy"), "Representó selección, mediación y causalidad inversa.", "El mapa no asigna pesos causales por sí solo."),
    "implementation_trace": ((), "Aplicación individual pendiente de documentar en los CT incorporados.", "No inferir validación por pertenecer a un flujo."),
    "problem_type_test": ((), "Aplicación individual pendiente de documentar en los CT incorporados.", "No inferir validación por pertenecer a un flujo."),
    "constraint_map": ((), "Aplicación individual pendiente de documentar en los CT incorporados.", "No inferir validación por pertenecer a un flujo."),
    "capability_access_utilization": ((), "Aplicación individual pendiente de documentar en los CT incorporados.", "No inferir validación por pertenecer a un flujo."),
    "output_outcome": ((), "Aplicación individual pendiente de documentar en los CT incorporados.", "No inferir validación por pertenecer a un flujo."),
    "transmission_map": ((), "Aplicación individual pendiente de documentar en los CT incorporados.", "No inferir validación por pertenecer a un flujo."),
    "distribution_test": (("CT-05/tool_autopsy", "CT-06/tool_autopsy"), "Conservó roles superpuestos y heterogeneidad.", "No predice por sí sola efectos individuales."),
    "time_horizon_test": (("CT-06/tool_autopsy",), "Separó efectos por momento y seguimiento.", "Los horizontes requieren mediciones comparables."),
    "disagreement_map": (("CT-05/tool_autopsy", "CT-06/tool_autopsy"), "Separó debates causales, distributivos y normativos.", "Mapear desacuerdo no resuelve diferencias de valores."),
    "counterfactual_test": (("CT-05/tool_autopsy",), "Introdujo el uso alternativo plausible de activos.", "Un contrafactual requiere supuestos explícitos."),
    "causal_responsibility": ((), "Aplicación individual pendiente de documentar en los CT incorporados.", "No atribuir responsabilidad sin evidencia de control y evitabilidad."),
    "confidence_layer": (("CT-05/confidence", "CT-06/confidence"), "Hizo visible la fuerza desigual de las conclusiones.", "La etiqueta de confianza no sustituye la justificación."),
    "evidence_conclusion_trace": (("CT-06/tool_autopsy",), "Bloqueó el salto de asociación a crisis poblacional.", "La traza no prueba que las fuentes sean correctas."),
    "conclusion_update": (("CT-06/tool_autopsy",), "Registró una corrección de fuente sin forzar nueva conclusión.", "Nueva evidencia solo exige revisión material cuando cambia la comprensión."),
}


CT07_PROGRESS = PendingResearch(
    id="CT-07",
    parent_case="CT-07",
    status="pausada / cierre no completado",
    last_reached_block=5,
    evidence_status="progreso de investigación conservado; no incorporado como expediente cerrado ni prueba de madurez",
    next_step="recuperar los bloques 1-5, contrastar fuentes y continuar desde el Bloque 6 cuando se reactive",
    source="checkpoint comercial comunicado por el usuario el 23-09-2026; detalle del Bloque 5 pendiente de adjuntar al registro local",
)

GAP_CT07_B = PendingResearch(
    id="GAP-CT07-B",
    parent_case="CT-07",
    status="candidato pendiente",
    last_reached_block=None,
    evidence_status="sin auditoría final de alojamiento, pérdida y recurrencia; no es herramienta 21",
    next_step="recuperar formulación y evidencia del candidato; aplicar las cinco condiciones del pre-registro y la doble prueba obligatoria",
    source="checkpoint comercial comunicado por el usuario el 23-09-2026; ficha detallada pendiente de preservar",
)

PENDING_RESEARCH = (CT07_PROGRESS, GAP_CT07_B)

FREE_BETA_TOOL_KEYS = frozenset(
    {
        "definition_test",
        "evidence_classification",
        "source_corroboration",
        "mechanism_magnitude_sufficiency",
        "confidence_layer",
        "evidence_conclusion_trace",
        "conclusion_update",
    }
)

COMMERCIAL_MATRIX = tuple(
    CommercialMatrixRow(
        tool_number=tool.number,
        tool_key=tool.key,
        tool_name=tool.name,
        workflow=tool.workflow,
        technical_maturity=tool.maturity,
        evidence_refs=_EVIDENCE[tool.key][0],
        observed_utility=_EVIDENCE[tool.key][1],
        limitations=_EVIDENCE[tool.key][2],
        public_exposure_authorized=tool.key in FREE_BETA_TOOL_KEYS,
        current_access="public" if tool.key in FREE_BETA_TOOL_KEYS else "owner",
        possible_plan=(
            "Free beta"
            if tool.key in FREE_BETA_TOOL_KEYS
            else "por_evaluar: Pro posterior / propietario / fuera del alcance"
        ),
        commercial_assignment_status=(
            "autorización beta revocable / sin asignación comercial definitiva"
            if tool.key in FREE_BETA_TOOL_KEYS
            else "provisional / sin asignación irrevocable"
        ),
    )
    for tool in TOOLS
)

CHECKPOINT = TransitionCheckpoint(
    id="FQ-COMMERCIAL-TRANSITION-2026-09-23",
    date="2026-09-23",
    toolkit_version="0.1",
    toolkit_size=20,
    preserved_cases=("CT-01", "CT-02", "CT-03", "CT-04", CT05.id, CT06.id),
    historical_sources=(
        "reasoning_toolkit.py",
        "methodology_registry.py: CT05, CT06_PREREGISTRATION, CT06, CT07_PREREGISTRATION",
        "POST_CT05_IMPLEMENTACION.md",
        "POST_CT06_IMPLEMENTACION.md",
        "CT07_PREREGISTRO_ADVERSARIAL.md",
    ),
    pending_research=(CT07_PROGRESS.id, GAP_CT07_B.id),
    launch_policy="Los CT pendientes no bloquean automáticamente la beta; cada bloqueo requiere un riesgo concreto del producto inicial.",
    launch_gate="La beta requiere aceptación visual y operativa, fuentes y datos revisables, permisos y comunicación acordes al alcance publicado.",
    pro_stage="Pro es una etapa comercial posterior al lanzamiento inicial; sin fecha ni asignación definitiva.",
    price_status="sin precios definitivos",
    public_behavior_change=False,
)

PUBLIC_BETA_CHECKPOINT = TransitionCheckpoint(
    id="FQ-PUBLIC-BETA-AUTHORIZATION-2026-09-24",
    date="2026-09-24",
    toolkit_version="0.1",
    toolkit_size=20,
    preserved_cases=CHECKPOINT.preserved_cases,
    historical_sources=CHECKPOINT.historical_sources,
    pending_research=CHECKPOINT.pending_research,
    launch_policy=CHECKPOINT.launch_policy,
    launch_gate=(
        "Autorización revocable de las herramientas Free #1, #2, #3, #4, #18, #19 y #20 "
        "como un único recorrido descriptivo; su publicación exige controles y aceptación."
    ),
    pro_stage=CHECKPOINT.pro_stage,
    price_status=CHECKPOINT.price_status,
    public_behavior_change=True,
)


def validate_commercial_transition() -> None:
    if len(TOOLS) != 20 or len(COMMERCIAL_MATRIX) != 20:
        raise ValueError("Toolkit y matriz deben contener exactamente 20 herramientas")
    if {row.tool_key for row in COMMERCIAL_MATRIX} != {tool.key for tool in TOOLS}:
        raise ValueError("La matriz no coincide con el Toolkit canónico")
    if any(row.technical_maturity != tool.maturity for row, tool in zip(COMMERCIAL_MATRIX, TOOLS)):
        raise ValueError("La matriz alteró la madurez técnica")
    public_rows = {row.tool_key for row in COMMERCIAL_MATRIX if row.public_exposure_authorized}
    if public_rows != FREE_BETA_TOOL_KEYS:
        raise ValueError("La matriz debe autorizar exactamente las siete herramientas Free")
    if any(
        row.current_access != ("public" if row.tool_key in FREE_BETA_TOOL_KEYS else "owner")
        for row in COMMERCIAL_MATRIX
    ):
        raise ValueError("El acceso actual no coincide con la autorización comercial")
    if CT07_PREREGISTRATION.question_frozen or CT07_PROGRESS.last_reached_block != 5:
        raise ValueError("El pre-registro y el checkpoint de progreso deben permanecer separados")
    if GAP_CT07_B.status != "candidato pendiente":
        raise ValueError("GAP-CT07-B no está autorizado como herramienta")
    if not PUBLIC_BETA_CHECKPOINT.public_behavior_change:
        raise ValueError("La autorización pública debe conservar su checkpoint propio")
    for feature in candidate_features():
        if feature not in PLAN_FEATURES["owner"]:
            raise ValueError("Capacidad experimental ausente del modo propietario")
        if any(feature in PLAN_FEATURES[plan] for plan in ("public", "pro", "business", "institutional")):
            raise ValueError("Capacidad experimental expuesta fuera del modo propietario")
