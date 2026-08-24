"""Arquitectura provisional del FQ Reasoning Toolkit 0.1.

El registro preserva las veinte operaciones del manual sin convertirlas en
veinte productos independientes. Los flujos y las capas comerciales siguen en
validación y no deben habilitarse como promesas públicas automáticamente.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ReasoningTool:
    number: int
    key: str
    name: str
    question: str
    workflow: str
    maturity: str


@dataclass(frozen=True)
class ReasoningWorkflow:
    key: str
    name: str
    purpose: str
    candidate_feature: str


WORKFLOWS = {
    "claim_integrity": ReasoningWorkflow(
        "claim_integrity",
        "Definir y verificar la afirmación",
        "Aclara el objeto, clasifica la afirmación y comprueba qué respalda la fuente.",
        "reasoning_foundations_lab",
    ),
    "causal_path": ReasoningWorkflow(
        "causal_path",
        "Probar el camino causal",
        "Examina mecanismo, canales, magnitud, suficiencia y contrafactual.",
        "causal_reasoning_lab",
    ),
    "system_delivery": ReasoningWorkflow(
        "system_delivery",
        "Reconstruir implementación y restricciones",
        "Localiza rupturas, tipo de problema, restricciones y pérdidas de utilización.",
        "system_reasoning_lab",
    ),
    "outcomes_attribution": ReasoningWorkflow(
        "outcomes_attribution",
        "Descomponer resultados y atribución",
        "Separa productos, resultados, distribución, tiempo y responsabilidad.",
        "outcome_reasoning_lab",
    ),
    "conclusion_audit": ReasoningWorkflow(
        "conclusion_audit",
        "Auditar la conclusión",
        "Expone desacuerdos, confianza y cada salto entre evidencia y conclusión.",
        "conclusion_audit_lab",
    ),
    "updating": ReasoningWorkflow(
        "updating",
        "Actualizar la conclusión",
        "Registra qué cambió, por qué cambió y qué evidencia exigiría otra revisión.",
        "conclusion_update_lab",
    ),
}


TOOLS = (
    ReasoningTool(1, "definition_test", "Prueba de definición", "¿Qué significa exactamente la afirmación que estamos evaluando?", "claim_integrity", "core"),
    ReasoningTool(2, "evidence_classification", "Clasificación de evidencia", "¿Qué clase de afirmación tengo delante y qué fuerza tiene su respaldo?", "claim_integrity", "core"),
    ReasoningTool(3, "source_corroboration", "Prueba de fuente y corroboración", "¿Quién afirma esto y qué demuestra realmente esa fuente?", "claim_integrity", "core"),
    ReasoningTool(4, "mechanism_magnitude_sufficiency", "Mecanismo, magnitud y suficiencia", "¿Cómo produciría X el resultado Y, cuánto explica y alcanza por sí solo?", "causal_path", "core"),
    ReasoningTool(5, "outcome_decomposition", "Descomposición del resultado", "¿Qué componentes distintos están escondidos dentro de éxito o fracaso?", "outcomes_attribution", "fusion_candidate"),
    ReasoningTool(6, "attribution_map", "Mapa de atribución", "¿Qué factores contribuyeron al resultado y cuánto peso merece cada uno?", "outcomes_attribution", "laboratory"),
    ReasoningTool(7, "implementation_trace", "Traza de implementación", "¿En qué eslabón apareció el problema y en cuál se originó?", "system_delivery", "fusion_candidate"),
    ReasoningTool(8, "problem_type_test", "Prueba del tipo de problema", "¿El cuello de botella es de conocimiento, capacidad, incentivos o valores?", "system_delivery", "fusion_candidate"),
    ReasoningTool(9, "constraint_map", "Mapa de restricciones", "¿Qué impide que una solución aparentemente razonable ocurra?", "system_delivery", "fusion_candidate"),
    ReasoningTool(10, "capability_access_utilization", "Capacidad, acceso y utilización", "¿Existe la capacidad, llega a quien debe usarla y se utiliza efectivamente?", "system_delivery", "fusion_candidate"),
    ReasoningTool(11, "output_outcome", "Distinción producto-resultado", "¿Qué produjo el sistema y qué cambio real generó?", "outcomes_attribution", "core"),
    ReasoningTool(12, "transmission_map", "Mapa de transmisión", "¿Por qué canales una decisión produce efectos posteriores?", "causal_path", "fusion_candidate"),
    ReasoningTool(13, "distribution_test", "Prueba de distribución", "¿Quién gana, quién pierde y cuándo soporta cada grupo los costos y beneficios?", "outcomes_attribution", "fusion_candidate"),
    ReasoningTool(14, "time_horizon_test", "Prueba del horizonte temporal", "¿En qué horizonte ocurre cada costo y beneficio?", "outcomes_attribution", "fusion_candidate"),
    ReasoningTool(15, "disagreement_map", "Mapa del desacuerdo", "¿En qué punto exacto están en desacuerdo las partes?", "conclusion_audit", "fusion_candidate"),
    ReasoningTool(16, "counterfactual_test", "Prueba contrafactual", "¿Qué habría ocurrido razonablemente sin X o con una alternativa?", "causal_path", "laboratory"),
    ReasoningTool(17, "causal_responsibility", "Responsabilidad causal y evitabilidad", "¿Qué causó el resultado, quién lo controlaba y podía razonablemente evitarlo?", "outcomes_attribution", "laboratory"),
    ReasoningTool(18, "confidence_layer", "Capa de confianza", "¿Qué tan seguros estamos, por qué y qué incertidumbre permanece?", "conclusion_audit", "core"),
    ReasoningTool(19, "evidence_conclusion_trace", "Traza evidencia-conclusión", "¿Puede otra persona reconstruir cada salto desde la fuente hasta la conclusión?", "conclusion_audit", "core"),
    ReasoningTool(20, "conclusion_update", "Protocolo de actualización de conclusiones", "¿Sigue siendo la conclusión anterior la mejor explicación disponible?", "updating", "core"),
)


TOOL_BY_KEY = {tool.key: tool for tool in TOOLS}


def tools_for_workflow(workflow: str) -> tuple[ReasoningTool, ...]:
    if workflow not in WORKFLOWS:
        raise ValueError(f"Flujo de razonamiento desconocido: {workflow}")
    return tuple(tool for tool in TOOLS if tool.workflow == workflow)


def toolkit_as_dicts() -> list[dict]:
    return [asdict(tool) for tool in TOOLS]


def candidate_features() -> tuple[str, ...]:
    """Capacidades comerciales experimentales; no equivalen a planes publicados."""
    return tuple(workflow.candidate_feature for workflow in WORKFLOWS.values())
