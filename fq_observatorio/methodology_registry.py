"""Registro interno y versionado de aprendizaje metodologico de FranQuestions.

Este modulo cruza la frontera laboratorio -> MVP solo como estructura interna.
No crea superficies publicas, scores, veredictos ni herramientas nuevas.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Principle:
    id: str
    statement: str
    origin: str
    status: str
    activation: str
    operational_change: str
    review_condition: str
    future_test: str
    version: str = "0.1"


@dataclass(frozen=True)
class CrashTestRecord:
    id: str
    version: str
    status: str
    question: str
    hypotheses: tuple[tuple[str, str], ...]
    provisional_conclusions: tuple[tuple[str, str], ...]
    knows: tuple[str, ...]
    believes: tuple[str, ...]
    unknowns: tuple[str, ...]
    confidence: tuple[tuple[str, str], ...]
    review_triggers: tuple[str, ...]
    tool_autopsy: tuple[str, ...]
    workflow_autopsy: str
    self_critique: tuple[str, ...]
    closure_audit: tuple[tuple[str, str], ...]
    traceability: tuple[str, ...]


@dataclass(frozen=True)
class CrashTestPreregistration:
    """Diseno congelable de un CT sin resultados ni valor probatorio."""

    id: str
    status: str
    domain: str
    provisional_question: str
    question_frozen: bool
    primary_objective: str
    secondary_objective: str
    inherited_principles: tuple[str, ...]
    anticipated_design_conditions: tuple[str, ...]
    execution_mode: str
    execution_mode_status: str
    workflow: tuple[str, ...]
    preregistration_questions: tuple[str, ...]
    forbidden_inferences: tuple[str, ...]


@dataclass(frozen=True)
class ProspectivePrincipleTest:
    id: str
    status: str
    formal_runs: int
    observed_value: str
    validation_status: str
    evidence_case: str


@dataclass(frozen=True)
class GovernanceCandidate:
    id: str
    statement: str
    status: str
    evidence: str
    canonical_principle: bool = False


@dataclass(frozen=True)
class MethodologyConvergenceEvidence:
    toolkit_version: str
    evidence_case: str
    finding: str
    limitation: str


@dataclass(frozen=True)
class AdversarialPreregistration:
    id: str
    status: str
    domain: str
    provisional_question: str
    question_frozen: bool
    primary_objective: str
    secondary_objective: str
    prior_convergence_status: str
    fq_hypotheses: tuple[tuple[str, str], ...]
    initial_alternatives: tuple[tuple[str, str], ...]
    gap_candidate_conditions: tuple[str, ...]
    mandatory_gap_test: tuple[str, ...]
    convergence_strengthener: str
    convergence_weakener: str
    evidence_prediction_values_rule: tuple[tuple[str, str], ...]
    execution_mode: str
    execution_mode_status: str
    forbidden_inferences: tuple[str, ...]


CT05 = CrashTestRecord(
    id="CT-05",
    version="1.0",
    status="CLOSE-PROVISIONAL / actualizacion abierta",
    question=(
        "En que medida la expansion de los alquileres de corto plazo en zonas "
        "costeras de Guanacaste ha contribuido a cambios en disponibilidad y "
        "precios de vivienda, desarrollo inmobiliario y competencia turistica, "
        "y que parte puede distinguirse de otros factores economicos y territoriales?"
    ),
    hypotheses=(
        ("H1", "Efecto STR material sobre oferta residencial, rentas, precios o suelo."),
        ("H2", "Seleccion geografica o causalidad inversa."),
        ("H3", "Desarrollo inmobiliario, segunda residencia y nueva construccion."),
        ("H4", "Demanda general por turismo, migracion, capital e ingresos."),
        ("H5", "Restricciones de oferta de agua, infraestructura, regulacion y geografia."),
        ("H6", "Interaccion multicausal, mediacion, retroalimentacion o causas comunes."),
        ("H7", "Distribucion de beneficios y costos entre roles distintos y superpuestos."),
    ),
    provisional_conclusions=(
        ("CP-1", "Presencia grande y concentrada; coincidencia espacial no prueba causalidad."),
        ("CP-2", "Inventario STR no equivale a vivienda residencial retirada."),
        ("CP-3", "Precios pueden cambiar por desplazamiento o capitalizacion de ingresos."),
        ("CP-4", "Deben separarse tendencias previas, seleccion y causalidad inversa."),
        ("CP-5", "Venta, renta, suelo, accesibilidad y desplazamiento son outcomes distintos."),
        ("CP-6", "Restricciones pueden amplificar presiones sin coeficientes locales robustos."),
        ("CP-7", "Beneficios y costos se distribuyen entre roles superpuestos."),
        ("CP-8", "Los actores discrepan sobre vivienda, competencia, regulacion y causalidad."),
        ("CP-9", "La explicacion multicausal sobrevive provisionalmente, pero debe poder perder."),
    ),
    knows=(
        "Hay concentracion territorial de STR.",
        "Una unidad listada no prueba desplazamiento residencial.",
        "Mecanismos distintos pueden producir el mismo resultado.",
        "Los efectos distributivos requieren grupos, denominadores y roles explicitos.",
    ),
    believes=(
        "STR, turismo, inversion, desarrollo, seleccion y restricciones interactuan.",
        "Los STR pueden ser causa, consecuencia o amplificador segun el territorio.",
    ),
    unknowns=(
        "Magnitud causal local por mecanismo y causa dominante.",
        "Fraccion del inventario que habria sido residencia.",
        "Balance neto por grupo y efecto de restricciones especificas.",
    ),
    confidence=(
        ("Inferencia causal simple insuficiente", "alta"),
        ("Varios mecanismos plausibles", "alta"),
        ("Interaccion multicausal local", "moderada-alta"),
        ("Efecto material de STR en zonas concretas", "moderada"),
        ("Pesos causales relativos", "baja"),
        ("Causa dominante", "no determinada"),
    ),
    review_triggers=(
        "Series longitudinales o disenos cuasi experimentales locales.",
        "Evidencia de uso alternativo del activo y conversion residencial/turistica.",
        "Comparaciones de zonas similares con distinta exposicion STR.",
        "Datos verificables de propiedad, rentas, precios, agua e infraestructura.",
        "Evaluaciones posteriores a restricciones o reformas.",
    ),
    tool_autopsy=(
        "Definition Test separo listado, vivienda y uso alternativo.",
        "Counterfactual Test incorporo el uso contrafactual del activo.",
        "Attribution Map represento seleccion, mediacion y retroalimentacion.",
        "Outcome Decomposition separo cinco resultados habitacionales.",
        "Distribution Test admitio roles superpuestos.",
        "Disagreement Map separo debates distintos.",
        "Mechanism-Magnitude-Sufficiency impidio afirmar magnitudes no probadas.",
        "Source and Corroboration trato incentivos y datos comerciales explicitamente.",
    ),
    workflow_autopsy=(
        "CT-05 fue asistido e interactivo. Se observo valor operativo de la capa "
        "compacta. La contribucion incremental de la interaccion humana frente a "
        "delegacion completa sigue siendo una hipotesis operativa candidata. CT-04 "
        "permanece como unica validacion formal de investigacion delegada Work/Codex."
    ),
    self_critique=(
        "No equiparar listado STR con vivienda retirada.",
        "No suponer que una propiedad turistica carece de efectos sobre vivienda o suelo.",
        "No usar multicausalidad como refugio ante falta de cuantificacion.",
        "No transferir coeficientes internacionales a Guanacaste.",
        "No tratar grupos economicos como homogeneos o mutuamente exclusivos.",
    ),
    closure_audit=(
        ("Pregunta respondida", "si, provisionalmente"),
        ("Rivales y falsadores", "presentes"),
        ("Categorias epistemicas separadas", "presentes"),
        ("Herramientas nuevas", "ninguna"),
        ("Toolkit 0.1", "20 herramientas congeladas"),
        ("Actualizacion", "abierta ante triggers materiales"),
    ),
    traceability=(
        "pregunta -> H1-H7 -> evidencia -> CP-1-CP-9",
        "CP -> Sabemos/Creemos/No sabemos -> Confidence Layer",
        "limites -> falsadores/condiciones de revision -> triggers",
        "Tool Autopsy -> Workflow Autopsy -> Self-Critique -> Closure Audit",
    ),
)


CT06_PREREGISTRATION = CrashTestPreregistration(
    id="CT-06",
    status="seleccionado / no investigado / no incorporado como evidencia",
    domain="salud poblacional, adolescencia y plataformas digitales",
    provisional_question=(
        "En que medida el uso de redes sociales contribuye causalmente a cambios "
        "en la salud mental de adolescentes, mediante que mecanismos y para que "
        "grupos, y cuanto de la asociacion observada puede explicarse por seleccion, "
        "causalidad inversa y factores compartidos?"
    ),
    question_frozen=False,
    primary_objective=(
        "Primera prueba prospectiva de RP-01: comprobar si principios heredados "
        "modifican de forma util y trazable el comportamiento de un caso nuevo."
    ),
    secondary_objective=(
        "Probar las capacidades de FQ en literatura cientifica y salud poblacional "
        "con heterogeneidad, causalidad inversa y multiples outcomes."
    ),
    inherited_principles=("P-01", "P-03", "P-06", "P-08", "P-09", "P-10", "P-22", "P-24"),
    anticipated_design_conditions=(
        "tiempo de uso no equivale a tipo de uso",
        "asociacion no equivale a causalidad",
        "uso de redes -> salud mental puede coexistir con salud mental -> mayor uso",
        "promedio poblacional no equivale a efecto sobre subgrupos",
        "salud mental no equivale a un unico outcome",
    ),
    execution_mode="hybrid",
    execution_mode_status="primera ejecucion formal prevista; experimental y no validada",
    workflow=(
        "congelar pregunta, rivales, falsadores y principios heredados",
        "ejecutar investigacion pesada por etapas",
        "producir una capa compacta con ruta de descompresion",
        "volver al laboratorio ante contradiccion, novedad o activacion relevante",
        "delegar nuevamente solo cuando corresponda",
        "auditar y cerrar mediante paquete versionado",
    ),
    preregistration_questions=(
        "Que principios hereda CT-06?",
        "Que condiciones deberian activarlos?",
        "Que error intenta evitar cada uno?",
        "Que evidencia mostraria que alguno no anade valor?",
        "Que resultado mostraria una necesidad analitica no cubierta por las 20 herramientas?",
    ),
    forbidden_inferences=(
        "conclusiones sobre redes sociales y salud mental",
        "cambios de madurez de principios",
        "replicacion por mera inclusion en el pre-registro",
        "validacion de RP-01",
        "validacion o publicacion del modo hibrido",
        "modificacion del Toolkit 0.1 o creacion de herramientas",
    ),
)


CT06 = CrashTestRecord(
    id="CT-06",
    version="1.0",
    status="Caso canonico - CLOSE PROVISIONAL v1.0 / actualizacion abierta",
    question=(
        "En que medida el uso de redes sociales contribuye causalmente a cambios "
        "en la salud mental de adolescentes, mediante que mecanismos y para que "
        "grupos, y cuanto de la asociacion observada puede explicarse por causalidad "
        "inversa, seleccion y factores compartidos?"
    ),
    hypotheses=(
        ("H1", "Ciertos patrones de uso producen efectos adversos causales materiales."),
        ("H2", "El malestar previo modifica cuanto o como se usan las redes."),
        ("H3", "Factores familiares, sociales, economicos, escolares o personales afectan uso y salud mental."),
        ("H4", "El promedio oculta heterogeneidad por persona, edad, vulnerabilidad, plataforma, uso y contexto."),
        ("H5", "El tipo y la experiencia de uso informan mas que el tiempo bruto por si solo."),
        ("H6", "Riesgos y beneficios pueden coexistir y su balance depende del contexto."),
        ("H7", "La interaccion multicausal es un modelo organizador provisional y falsable, no causalidad demostrada."),
    ),
    provisional_conclusions=(
        ("CP-1", "Uso de redes y salud mental requieren descomposicion por exposicion, experiencia, poblacion y outcome."),
        ("CP-2", "Asociaciones observadas no resuelven por si mismas direccion causal, seleccion ni factores compartidos."),
        ("CP-3", "Mecanismos plausibles no identifican automaticamente magnitud, suficiencia ni mecanismo dominante."),
        ("CP-4", "Los promedios agregados ocultan heterogeneidad real que aun no permite prediccion individual robusta."),
        ("CP-5", "Tiempo bruto, tipo de uso, contenido, plataforma y uso problematico no son exposiciones equivalentes."),
        ("CP-6", "La evidencia admite efectos adversos, nulos y beneficiosos segun outcome, persona, contexto y horizonte."),
        ("CP-7", "H7 organiza provisionalmente la evidencia, limitada por dependencia, observacion, autorreporte y heterogeneidad; uso problematico no es una causa independiente limpia."),
    ),
    knows=(
        "Uso de redes y salud mental son categorias amplias que necesitan descomposicion.",
        "El cuerpo de evidencia presenta heterogeneidad sustancial.",
        "Uso general y uso problematico no deben mezclarse como una misma exposicion.",
        "Existen asociaciones observadas y relaciones longitudinales en ambas direcciones en algunos estudios.",
        "Contexto, tipo de uso y caracteristicas individuales importan.",
    ),
    believes=(
        "Determinados patrones y experiencias digitales contribuyen causalmente a determinados outcomes en algunos adolescentes.",
        "Varias rutas pueden interactuar y formar retroalimentaciones.",
        "H7 organiza mejor el cuerpo revisado que una explicacion monocausal simple, sin demostrar causalidad general.",
    ),
    unknowns=(
        "Magnitud causal poblacional general y proporcion del deterioro historico atribuible a redes.",
        "Causa o mecanismo dominante y balance causal neto de riesgos y beneficios.",
        "Que adolescente concreto experimentara que efecto.",
        "Que intervencion o regulacion seria optima.",
    ),
    confidence=(
        ("Las categorias amplias requieren descomposicion", "alta"),
        ("Heterogeneidad sustancial", "alta"),
        ("Uso general y problematico no son equivalentes", "alta"),
        ("Patrones concretos pueden contribuir a outcomes concretos", "moderada-alta"),
        ("Bidireccionalidad y mecanismos multiples en algunos contextos", "moderada"),
        ("Prediccion individual anticipada", "baja-moderada"),
        ("Magnitud causal poblacional atribuible", "baja"),
        ("Fraccion de la tendencia historica causada por redes", "muy baja / no determinada"),
    ),
    review_triggers=(
        "RCT o cuasi-experimento grande con exposicion especifica y objetiva y efectos consistentes y duraderos.",
        "Evidencia replicada de un mecanismo dominante o de efectos practicamente nulos.",
        "Cuantificacion convincente de una fraccion causal poblacional.",
        "Evaluacion robusta de cambios de diseno, plataforma o restricciones.",
        "Revision de alta calidad que altere materialmente magnitud o direccion.",
        "Correccion o retractacion importante de evidencia central.",
    ),
    tool_autopsy=(
        "Definition Test separo acceso, tiempo, tipo de uso, experiencia y outcome.",
        "Evidence Classification distinguio evidencia transversal, longitudinal, experimental y sintetica.",
        "Mechanism-Magnitude-Sufficiency bloqueo el salto de mecanismo plausible a suficiencia causal.",
        "Outcome Decomposition evito comprimir depresion, ansiedad, bienestar, sueno y otros resultados.",
        "Attribution Map represento mediacion, moderacion, causalidad inversa y retroalimentacion.",
        "Distribution y Time-Horizon Tests conservaron heterogeneidad entre personas, grupos y momentos.",
        "Disagreement Map separo existencia, causalidad, magnitud, distribucion, tendencia y umbral normativo.",
        "Evidence-to-Conclusion Trace bloqueo el salto desde asociacion hasta crisis poblacional.",
        "Update Protocol registro una correccion de evidencia sin forzar cambio de conclusion.",
    ),
    workflow_autopsy=(
        "Primera ejecucion formal operativa del modo hibrido. Se observo valor al alternar "
        "investigacion por bloques y retorno al laboratorio, pero no existe comparacion "
        "contrafactual que demuestre superioridad ni validacion general. CT-04 permanece "
        "como unica validacion formal de investigacion delegada Work/Codex."
    ),
    self_critique=(
        "No contar publicaciones solapadas como cuerpos independientes.",
        "Preservar edad, exposicion y outcome de cada resultado.",
        "No transformar uso problematico en una causa independiente limpia.",
        "Falta de potencia no demuestra ausencia ni existencia de efecto.",
        "Ausencia de causa dominante puede reflejar limites de identificacion.",
        "No atribuir a redes sociales la crisis general de salud mental adolescente.",
    ),
    closure_audit=(
        ("Pregunta congelada y respondida", "si, provisionalmente"),
        ("H1-H7 y CP-1-CP-7 preservadas", "si"),
        ("Adversarial Test", "completado; H7 sobrevivio mas limitada"),
        ("Self-Critique", "completado con correccion material de H7"),
        ("Categorias epistemicas", "Sabemos / Creemos / No sabemos separadas"),
        ("Herramientas nuevas", "ninguna"),
        ("Toolkit 0.1", "20 herramientas congeladas"),
        ("Actualizacion", "abierta ante cambio material de comprension"),
    ),
    traceability=(
        "pre-registro historico -> pregunta congelada -> H1-H7 -> investigacion por bloques",
        "evidencia -> CP-1-CP-7 -> Adversarial Test -> Self-Critique",
        "Sabemos/Creemos/No sabemos -> Conclusion central v1.0 -> Confidence Layer",
        "Closure Completeness Audit -> CLOSE PROVISIONAL v1.0 -> triggers de reapertura",
    ),
)

CT06_CONCLUSION_V1 = (
    "No existe base para tratar el uso de redes sociales como una exposicion uniforme "
    "ni para atribuirle un unico efecto sobre la salud mental adolescente. Determinados "
    "patrones y experiencias pueden contribuir a determinados outcomes para algunos "
    "adolescentes, junto con causalidad inversa, factores compartidos y heterogeneidad; "
    "la magnitud causal poblacional y la contribucion a la tendencia historica permanecen indeterminadas."
)

RP01_PROSPECTIVE_TEST = ProspectivePrincipleTest(
    id="RP-01",
    status="primera prueba prospectiva completada",
    formal_runs=1,
    observed_value="valor operativo observado",
    validation_status="no validado; generalizacion pendiente",
    evidence_case="CT-06",
)

PG01 = GovernanceCandidate(
    id="PG-01",
    statement="Pre-registrar objetivos y criterios reduce el riesgo de reinterpretacion retrospectiva.",
    status="candidato de gobernanza / evidencia operativa inicial",
    evidence="CT-06 preservo expectativas anteriores a los resultados.",
)

TOOLKIT_01_CONVERGENCE = MethodologyConvergenceEvidence(
    toolkit_version="0.1",
    evidence_case="CT-06",
    finding="Evidencia adicional de estabilidad: un dominio cientifico y de salud fue absorbido sin ampliar las 20 herramientas.",
    limitation="Hipotesis acumulativa de convergencia; no demuestra suficiencia universal ni autoriza Toolkit 0.2.",
)


CT07_PREREGISTRATION = AdversarialPreregistration(
    id="CT-07",
    status="seleccionado / no investigado / sin evidencia incorporada",
    domain="decision organizacional prospectiva sobre IA generativa y trabajo humano",
    provisional_question=(
        "Como deberia estructurarse una decision sobre sustituir, complementar o "
        "mantener trabajo humano frente a IA generativa cuando productividad, calidad, "
        "costos, empleo, privacidad, resiliencia y aprendizaje futuro pueden entrar en "
        "conflicto, y la evidencia disponible no permite conocer con certeza los resultados futuros?"
    ),
    question_frozen=False,
    primary_objective=(
        "Intentar falsar la hipotesis de convergencia del Toolkit 0.1 mediante un "
        "problema prospectivo, multiobjetivo y con valores en conflicto."
    ),
    secondary_objective=(
        "Evaluar si FranQuestions separa evidencia, prediccion y preferencias/valores "
        "sin introducir silenciosamente una preferencia normativa propia."
    ),
    prior_convergence_status="fortalecida despues de CT-06, pero no confirmada",
    fq_hypotheses=(
        ("FQ-H1", "Las 20 herramientas son suficientes sin deformacion material."),
        ("FQ-H2", "Falta una operacion analitica para decisiones multiobjetivo y trade-offs."),
        ("FQ-H3", "Falta una operacion para valor de informacion, aprendizaje y opcionalidad."),
        ("FQ-H4", "Falta una operacion para reversibilidad, irreversibilidad y capacidades dificiles de recuperar."),
        ("FQ-H5", "El posible hueco pertenece al workflow de decision y no requiere ampliar el Toolkit."),
    ),
    initial_alternatives=(
        ("A", "Mantener operacion humana actual."),
        ("B", "IA como asistencia al trabajo humano."),
        ("C", "Automatizacion parcial."),
        ("D", "Automatizacion amplia."),
        ("E", "Piloto reversible antes de una decision mayor."),
    ),
    gap_candidate_conditions=(
        "Es necesaria para sostener responsablemente la conclusion.",
        "Aparece de forma material y no anecdotica.",
        "Ninguna combinacion razonable de las 20 herramientas puede realizarla sin deformar su funcion original.",
        "No es simplemente vocabulario, metrica, vista, workflow o regla de gobernanza.",
        "Omitirla produce un error analitico identificable.",
    ),
    mandatory_gap_test=(
        "Intentar alojar la operacion razonablemente dentro de Toolkit 0.1.",
        "Intentar demostrar que ese alojamiento pierde informacion, confunde operaciones o produce errores.",
        "Solo si sobrevive ambas pruebas puede registrarse como GAP-CT07; nunca como herramienta automatica.",
    ),
    convergence_strengthener=(
        "CT-07 se resuelve sin nueva operacion analitica y sin estirar artificialmente las herramientas existentes."
    ),
    convergence_weakener=(
        "Aparece una tarea necesaria, recurrente y no absorbible por el nucleo."
    ),
    evidence_prediction_values_rule=(
        ("EVIDENCIA", "Que sabemos sobre consecuencias posibles."),
        ("PREDICCION", "Que creemos que podria ocurrir bajo cada alternativa."),
        ("PREFERENCIAS/VALORES", "Que resultados considera mas importantes quien toma la decision."),
    ),
    execution_mode="hybrid",
    execution_mode_status=(
        "previsto y experimental; seria la segunda ejecucion formal solo si CT-07 se completa bajo este modo"
    ),
    forbidden_inferences=(
        "herramienta 21 o Toolkit 0.2 autorizados",
        "cambios de arquitectura, scores o pesos automaticos",
        "recomendaciones sobre sustitucion de trabajadores",
        "IA es mejor o peor que trabajo humano",
        "preferencia normativa convertida en conclusion factual",
        "segunda ejecucion hibrida antes de completar CT-07",
    ),
)


_PRINCIPLE_ROWS = (
    ("P-01", "Lista causal no basta cuando las causas interactuan.", "CT-01 - origen reconstruido", "fortalecido", "causas mediadas o comunes; replicacion prospectiva CT-06", "representar relaciones y mediadores", "una lista simple produce igual calidad"),
    ("P-02", "Aprendizaje institucional exige cambio observable.", "CT-01 - origen reconstruido", "fortalecido", "se afirma aprendizaje institucional", "exigir problema, cambio y evidencia", "no mejora trazabilidad"),
    ("P-03", "No inventar pesos causales sin estimaciones.", "CT-01 - origen reconstruido", "fortalecido", "varias causas sin magnitud robusta; activacion prospectiva CT-06", "bloquear porcentajes no sustentados", "una estimacion validada los sustituye"),
    ("P-04", "Elegibilidad, prioridad, aprobacion, pago y recepcion son estados distintos.", "CT-02 - origen reconstruido", "experimental", "programas con embudo de acceso", "separar etapas y denominadores", "las etapas coinciden materialmente"),
    ("P-05", "Output no equivale a outcome.", "CT-02 - origen reconstruido", "fortalecido", "ejecucion se usa como prueba de suficiencia", "exigir outcome y contrafactual", "output predice por si solo el resultado"),
    ("P-06", "Un agregado puede ocultar resultados distributivos opuestos.", "CT-02 - origen reconstruido", "consolidado", "personas, dinero, grupos u horizontes distintos; replicacion prospectiva CT-06", "exigir grupo, denominador, unidad y horizonte", "desagregar no cambia la comprension"),
    ("P-07", "Una politica debe analizarse por version.", "CT-03 - origen directo", "fortalecido", "normas modificadas en el tiempo", "preservar version, fecha y efecto", "versiones no alteran la inferencia"),
    ("P-08", "Antes de arbitrar hay que identificar el desacuerdo real.", "CT-03 - origen directo", "fortalecido", "actores parecen discrepar en bloque; replicacion prospectiva CT-06", "descomponer afirmaciones y criterios", "no reduce falsos desacuerdos"),
    ("P-09", "Control epistemologico detecta errores; no certifica verdad.", "CT-03 - origen directo", "consolidado", "se aplica control o autocritica; activacion prospectiva explicita CT-06", "prohibir sellos automaticos de verdad", "control validado certifica verdad"),
    ("P-10", "Repeticion fortalece un patron sin cerrar refutacion.", "CT-03 - origen directo", "consolidado", "un patron reaparece; activacion prospectiva explicita CT-06", "subir madurez y conservar falsadores", "replicar vuelve innecesaria la refutacion"),
    ("P-11", "Resumir debe preservar limites y ruta de descompresion.", "CT-03 - origen directo", "fortalecido", "se crea capa ejecutiva", "conservar ruta a evidencia y limites", "omitir limites no cambia decisiones"),
    ("P-12", "MVP absorbe evidencia consolidada, no exploracion cruda.", "CT-03 - origen directo", "consolidado", "un paquete cruza la frontera al MVP", "exigir madurez, autorizacion y limites", "exploracion cruda mejora sin riesgo"),
    ("P-13", "Realidad, registro, reporte, conocimiento y decision tienen relojes distintos.", "CT-04 - origen directo", "fortalecido", "informacion asimetrica o versionada", "activar cronologia multirreloj", "vista lineal evita los mismos errores"),
    ("P-14", "Senal existente no equivale a senal material y accionable.", "CT-04 - origen directo", "fortalecido", "se atribuye omision o responsabilidad", "exigir acceso, especificidad, capacidad, autoridad y deber", "la cadena no cambia atribucion"),
    ("P-15", "Perdida visible no identifica causa o responsable.", "CT-04 - origen directo", "fortalecido", "dano con multiples actores", "reconstruir causalidad, informacion y evitabilidad", "la perdida basta para atribuir"),
    ("P-16", "Perdida total y dano incremental evitable son distintos.", "CT-04 - origen directo", "fortalecido", "existe una intervencion alternativa", "separar dano previo y modificable", "la separacion no altera el juicio"),
    ("P-17", "Porcentaje de personas no equivale a porcentaje de valor.", "CT-04 - origen directo", "fortalecido", "aparecen porcentajes distributivos", "mostrar denominador, unidad y perimetro", "ambos porcentajes coinciden sistematicamente"),
    ("P-18", "Resultado operativo favorable no demuestra optimalidad global.", "CT-04 - origen directo", "fortalecido", "una solucion funciona y se afirma que fue la mejor", "comparar alternativas, costo y valor", "resultado operativo identifica optimalidad"),
    ("P-19", "Ausencia de documentacion publica no equivale a ausencia de accion.", "CT-04 - origen directo", "fortalecido", "el expediente es incompleto", "clasificar como no documentado", "fuentes exhaustivas prueban ausencia"),
    ("P-20", "Escalar investigacion separa ejecucion, auditoria y decision.", "CT-04 - origen directo", "experimental", "carga alta y diseno estable", "delegar ejecucion y conservar autoridad", "pierde profundidad o trazabilidad"),
    ("P-21", "Unidad listada no equivale a vivienda desplazada.", "CT-05 - origen directo", "experimental", "un activo admite varios usos", "exigir uso contrafactual plausible", "listados predicen conversion uno a uno"),
    ("P-22", "Resultado correcto no identifica mecanismo correcto.", "CT-05 - origen directo", "fortalecido", "varios mecanismos predicen el mismo outcome; replicacion prospectiva CT-06", "separar prueba de resultado y mecanismo", "el control no mejora inferencia"),
    ("P-23", "Restriccion existente no equivale a restriccion vinculante.", "CT-05 - origen directo", "experimental", "se invoca limite de oferta o capacidad", "probar cuello de botella y magnitud", "la presencia basta para explicar"),
    ("P-24", "Multicausalidad tambien debe poder perder.", "CT-05 - origen directo", "fortalecido", "modelo multicausal gana por prudencia; prueba adversarial prospectiva CT-06", "definir falsador de causa dominante", "nunca discrimina entre rivales"),
    ("P-25", "Correlacion espacial no equivale a atribucion causal.", "CT-05 - origen directo", "experimental", "variables se concentran territorialmente", "activar seleccion y causalidad inversa", "no reduce errores frente a mapa simple"),
    ("P-26", "Roles economicos pueden superponerse.", "CT-05 - origen directo", "experimental", "un actor ocupa varias posiciones", "permitir pertenencia multiple", "no cambia la distribucion observada"),
)


PRINCIPLES = tuple(
    Principle(*row, future_test="CT-06 o siguiente caso pertinente")
    for row in _PRINCIPLE_ROWS
)

CANONICAL_PRINCIPLE_IDS = tuple(f"P-{number:02d}" for number in range(1, 27))

TOOLKIT_EXTENSIONS = {
    "information_version_trace": ("implementation_trace", "evidence_conclusion_trace"),
    "signal_actionability": ("evidence_classification", "causal_responsibility"),
    "responsibility_layering": ("definition_test", "causal_responsibility"),
    "incremental_avoidable_harm": ("counterfactual_test", "causal_responsibility"),
    "protection_perimeter": ("distribution_test",),
    "counterfactual_use_of_asset": ("counterfactual_test",),
    "selection_reverse_causality": ("attribution_map", "counterfactual_test"),
    "overlapping_roles": ("distribution_test",),
}

EXECUTION_MODES_LAB_ONLY = {
    "manual": "arquitectura experimental",
    "assisted": "valor operativo observado en CT-05",
    "delegated": "validado formalmente solo en CT-04",
    "hybrid": "experimental; 1 ejecucion formal en CT-06; valor operativo observado; sin validacion ni superioridad",
}

HYBRID_RETURN_TO_LAB_TRIGGERS = (
    "contradiccion que altere una conclusion provisional",
    "cambio material de comprension, direccion, magnitud o confianza",
    "activacion, limitacion o contradiccion trazable de un principio",
    "posible necesidad analitica no cubierta por las herramientas existentes",
    "correccion o retractacion de evidencia central",
)

HUMAN_INTERACTION_HYPOTHESIS = (
    "La interaccion humana puede contribuir al descubrimiento metodologico; "
    "su valor incremental frente a delegacion completa sigue pendiente."
)

FORBIDDEN_PUBLIC_CAPABILITIES = frozenset(
    {
        "tool_21",
        "toolkit_0_2_official",
        "fq_score",
        "str_score",
        "automatic_causal_weights",
        "social_media_score",
        "automatic_regulatory_recommendations",
        "automatic_good_bad_verdict",
        "automatic_blame_verdict",
        "automatic_truth_verdict",
        "automatic_optimality_verdict",
        "public_execution_modes",
    }
)


def validate_methodology_registry(tool_count: int, public_features: set[str] | None = None) -> None:
    """Falla si la implementacion rompe la autorizacion post-CT-06."""
    if tool_count != 20:
        raise ValueError("Toolkit 0.1 debe conservar exactamente 20 herramientas")
    if tuple(principle.id for principle in PRINCIPLES) != CANONICAL_PRINCIPLE_IDS:
        raise ValueError("P-01 a P-26 son los IDs canonicos de RP-01 v0.1")
    if CT06_PREREGISTRATION.question_frozen:
        raise ValueError("El pre-registro historico no debe reescribirse retroactivamente")
    if "no investigado" not in CT06_PREREGISTRATION.status:
        raise ValueError("El pre-registro debe conservar su estado anterior a resultados")
    if CT06.status != "Caso canonico - CLOSE PROVISIONAL v1.0 / actualizacion abierta":
        raise ValueError("CT-06 debe conservar estado de caso, no madurez Consolidado")
    if RP01_PROSPECTIVE_TEST.validation_status.startswith("validado"):
        raise ValueError("RP-01 no puede marcarse como validado")
    by_id = {principle.id: principle for principle in PRINCIPLES}
    if any(by_id[principle_id].status != "fortalecido" for principle_id in ("P-22", "P-24")):
        raise ValueError("P-22 y P-24 deben quedar fortalecidos, no consolidados")
    if PG01.id in CANONICAL_PRINCIPLE_IDS or PG01.canonical_principle:
        raise ValueError("PG-01 no puede convertirse en P-27")
    if "solo en CT-04" not in EXECUTION_MODES_LAB_ONLY["delegated"]:
        raise ValueError("CT-04 debe seguir como unica validacion formal Work/Codex")
    if CT07_PREREGISTRATION.question_frozen:
        raise ValueError("La pregunta de CT-07 permanece provisional")
    if "no investigado" not in CT07_PREREGISTRATION.status:
        raise ValueError("CT-07 no puede registrarse como evidencia antes de investigarse")
    if "seria la segunda" not in CT07_PREREGISTRATION.execution_mode_status:
        raise ValueError("CT-07 no debe contarse anticipadamente como segunda ejecucion hibrida")
    if "GAP-CT07" not in CT07_PREREGISTRATION.mandatory_gap_test[-1]:
        raise ValueError("Un posible hueco debe registrarse primero como GAP-CT07")
    leaked = FORBIDDEN_PUBLIC_CAPABILITIES.intersection(public_features or set())
    if leaked:
        raise ValueError(f"Capacidades no autorizadas expuestas: {sorted(leaked)}")
