# Implementación provisional del FQ Reasoning Toolkit 0.1

## Decisión

Las veinte herramientas se conservan como operaciones auditables, pero se presentan internamente mediante seis flujos. Esta arquitectura permite probar fusiones y nombres sin prometer todavía veinte productos ni asignarlos definitivamente a planes de pago.

| Flujo candidato | Herramientas | Estado comercial |
|---|---|---|
| Definir y verificar la afirmación | 1–3 | Laboratorio propietario |
| Probar el camino causal | 4, 12 y 16 | Laboratorio propietario |
| Reconstruir implementación y restricciones | 7–10 | Laboratorio propietario |
| Descomponer resultados y atribución | 5, 6, 11, 13, 14 y 17 | Laboratorio propietario |
| Auditar la conclusión | 15, 18 y 19 | Laboratorio propietario |
| Actualizar la conclusión | 20 | Laboratorio propietario |

## Madurez

- **Núcleo:** 1, 2, 3, 4, 11, 18, 19 y 20. Ya coinciden con principios presentes en FranQuestions y pueden probarse como operaciones estables.
- **Candidatas a fusión:** 5, 7, 8, 9, 10, 12, 13, 14 y 15. Deben evaluarse dentro de los seis flujos, no como módulos aislados.
- **Laboratorio avanzado:** 6, 16 y 17. Atribución, contrafactual y responsabilidad causal requieren evidencia y revisión humana especialmente exigentes.

## Capas de pago

Se añadieron seis capacidades experimentales al sistema de permisos. Por ahora solo el modo propietario puede acceder a ellas. No forman parte de Público, Pro, Empresas ni Institucional hasta que las pruebas determinen:

1. cuáles herramientas sobreviven;
2. cuáles se fusionan;
3. qué tareas resuelven realmente;
4. qué grado de revisión humana necesitan;
5. qué resultados son reproducibles y auditables;
6. qué promesa comercial puede sostenerse sin exageración.

## Regla de producto

El sistema debe comenzar por la pregunta que bloquea el análisis y recorrer únicamente el flujo que la evidencia exija. Completar veinte casillas no es un objetivo.

La salida común de todos los flujos deberá converger en:

1. conclusión provisional;
2. evidencia decisiva;
3. incertidumbre;
4. confianza justificada;
5. condición de revisión;
6. próxima búsqueda.

## Límite metodológico

La arquitectura no automatiza causalidad, responsabilidad ni certeza. Las etiquetas resumen razonamiento documentado; nunca reemplazan la evidencia que las sostiene.
