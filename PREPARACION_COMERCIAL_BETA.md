# Checkpoint de transición a preparación comercial de la beta

**Fecha:** 23 de septiembre de 2026
**Estado:** interno y provisional
**Registro ejecutable:** `fq_observatorio/commercial_transition.py`

## Estado preservado

El Toolkit 0.1 conserva sus 20 definiciones y madurez técnica (8 núcleo, 9 candidatas a fusión, 3 laboratorio). CT-01–CT-04 mantienen sus referencias históricas; CT-05 y CT-06 conservan sus expedientes y conclusiones. Los pre-registros de CT-06 y CT-07 siguen siendo objetos históricos separados de los resultados posteriores. Este checkpoint no modifica esos expedientes.

CT-07 queda **pausado tras el Bloque 5**, conforme al estado comunicado para esta transición. Su cierre no se ha incorporado al MVP. `GAP-CT07-B` queda como **candidato pendiente**, sujeto a los criterios del pre-registro y a la prueba de alojamiento/pérdida en las 20 herramientas. El detalle de los Bloques 4–5 y la ficha del candidato no constan en el registro local disponible; deben añadirse como fuentes versionadas antes de usar esos resultados para cambiar madurez o arquitectura. No se declara segunda ejecución híbrida completada.

## Tres decisiones distintas

La **madurez técnica** describe cuánto se ha probado una operación. La **autorización de exposición pública** decide si un usuario externo puede acceder a ella. La **asignación comercial** decide en qué plan podría ubicarse. Ninguna de las tres se deduce automáticamente de otra. Los campos están separados en cada fila de la matriz.

## Matriz comercial provisional

Cada fila registra la herramienta canónica, referencias verificables, utilidad observada y límite. `—` significa que aún falta documentar una activación individual en los expedientes locales; no significa que la herramienta carezca de utilidad. Para las 20 filas, exposición pública = **no autorizada**, acceso actual = **propietario** y plan posible = **por evaluar entre Free beta, Pro posterior y propietario**.

| # | Herramienta | Madurez | Evidencia CT local | Utilidad y límite principal |
|---:|---|---|---|---|
| 1 | Prueba de definición | Núcleo | CT-05, CT-06 | Separa unidades y exposiciones; definir no prueba causalidad. |
| 2 | Clasificación de evidencia | Núcleo | CT-06 | Distingue diseños; no mejora por sí sola la fuente. |
| 3 | Fuente y corroboración | Núcleo | CT-05 | Expone incentivos y límites de datos; no elimina sesgo. |
| 4 | Mecanismo, magnitud y suficiencia | Núcleo | CT-05, CT-06 | Evita cuantificar sin estimación; plausibilidad no basta. |
| 5 | Descomposición del resultado | Candidata a fusión | CT-05, CT-06 | Distingue outcomes; necesita datos por resultado. |
| 6 | Mapa de atribución | Laboratorio | CT-05, CT-06 | Mapea causas y mediación; no asigna pesos automáticamente. |
| 7 | Traza de implementación | Candidata a fusión | — | Activación individual pendiente; requiere seguimiento de eslabones. |
| 8 | Tipo de problema | Candidata a fusión | — | Activación individual pendiente; requiere probar utilidad en caso. |
| 9 | Mapa de restricciones | Candidata a fusión | — | Activación individual pendiente; presencia no prueba restricción vinculante. |
| 10 | Capacidad, acceso y utilización | Candidata a fusión | — | Activación individual pendiente; etapas requieren denominadores. |
| 11 | Producto frente a resultado | Núcleo | — | Activación individual pendiente; salida no demuestra impacto. |
| 12 | Mapa de transmisión | Candidata a fusión | — | Activación individual pendiente; canales requieren evidencia. |
| 13 | Prueba de distribución | Candidata a fusión | CT-05, CT-06 | Conserva grupos y roles; no predice el efecto individual. |
| 14 | Horizonte temporal | Candidata a fusión | CT-06 | Separa momentos; necesita mediciones comparables. |
| 15 | Mapa del desacuerdo | Candidata a fusión | CT-05, CT-06 | Descompone controversias; no arbitra valores. |
| 16 | Prueba contrafactual | Laboratorio | CT-05 | Introduce uso alternativo; depende de supuestos explícitos. |
| 17 | Responsabilidad causal | Laboratorio | — | Activación individual pendiente; exige control y evitabilidad. |
| 18 | Capa de confianza | Núcleo | CT-05, CT-06 | Expone incertidumbre; etiquetas no reemplazan justificación. |
| 19 | Traza evidencia-conclusión | Núcleo | CT-06 | Bloquea saltos inferenciales; no certifica fuentes. |
| 20 | Actualización de conclusiones | Núcleo | CT-06 | Registra correcciones; revisión no implica cambio automático. |

Las seis capacidades de flujo siguen accesibles **solo en modo propietario**. Esta matriz prepara la evaluación comercial posterior; no cambia permisos, define precios ni hace promesas de producto.

## Política de lanzamiento

Los CT pendientes **no bloquean automáticamente** la beta. Un bloqueo requiere demostrar un riesgo concreto para el alcance inicial publicado. La decisión de lanzamiento se apoya en aceptación visual y operativa, revisión de datos y fuentes, permisos y comunicación del alcance. Los CT adicionales pueden mejorar el método después de la beta sin convertirse en un requisito general previo.

FranQuestions Free es la etapa inicial propuesta con las capacidades públicas ya autorizadas del observatorio. Pro permanece como etapa comercial posterior: sin precio definitivo, fecha comprometida ni asignación irrevocable de herramientas. Las seis capacidades experimentales del Toolkit continúan en modo propietario.
