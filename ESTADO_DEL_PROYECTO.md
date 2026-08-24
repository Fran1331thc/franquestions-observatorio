# Estado del proyecto FranQuestions

## Candidato posterior a 2.13.1

- Prueba de comprensión integrada en el comparador estandarizado.
- Plan de beta académica cerrada para 8–12 participantes.
- Invitación y cuestionario neutrales, sin prometer automatización total.
- No se incorporan umbrales universales de importancia basados en Z-Scores.
- Estos cambios permanecen sin publicar hasta una nueva aceptación.

## Actualizador local 2.13.1 — 23 de agosto de 2026

- La comparación con la base vigente aparece antes de la confirmación en los 12 indicadores.
- La validación, la vista previa y la escritura comparten la misma normalización de fechas y decimales.
- Los archivos sin novedades muestran una explicación explícita y no habilitan la incorporación.
- El archivo oficial completo del tipo de cambio se verificó sin falsos positivos.

## Compatibilidad móvil del 13 de agosto de 2026

- Las gráficas de líneas, incluidas las comparaciones de señales, ahora se renderizan como SVG y no requieren WebGL.
- Se añadió una prueba de regresión que impide volver a introducir gráficas Plotly dependientes de WebGL.
- La versión funcional vigente quedó alineada en 2.13.1.
- El Protocolo de actualización de conclusiones FQ-MET-AC-001 quedó aprobado e integrado en las lecturas y fichas de investigación.

## Corrección de estabilidad del 11 de agosto de 2026

- Se corrigió la entrada pública para que Streamlit reconstruya toda la interfaz en cada interacción y recarga, evitando que el módulo principal quede retenido en la caché de importaciones y produzca una pantalla vacía.
- La corrección fue comprobada mediante ejecuciones repetidas de la aplicación y la apertura de los 12 indicadores, sin excepciones.
- Se añadió la prueba de regresión `tests/test_streamlit_rerun.py`, que abre la aplicación, interactúa con el selector y confirma que la interfaz permanece disponible después de la nueva ejecución.
- La suite completa quedó verificada después de la corrección: 28 de 28 pruebas aprobadas.
- La corrección está validada en la carpeta canónica local. Su publicación en Streamlit Community Cloud queda pendiente de incorporarla al repositorio conectado a GitHub.

## Punto de control del 9 de agosto de 2026

**Versión operativa:** 2.13.1
**Carpeta canónica:** `Version actual/Publicacion/FQ_Public_v2.9.2_limpio`  
**Estado:** MVP funcional en operación local y demostración pública de solo lectura.

> La carpeta conserva `v2.9.2` en el nombre para no romper los iniciadores locales ni la publicación existente. La versión funcional vigente es 2.13.1.

## Verificaciones realizadas

- La aceptación automatizada fue verificada nuevamente el 9 de agosto de 2026: 27 de 27 pruebas aprobadas. Las interfaces pública y administrativa cargaron sin excepciones mediante las pruebas de Streamlit.
- Los 12 indicadores tienen metadatos públicos completos, enlace oficial HTTPS, observaciones y capacidad de comparación histórica de cinco años.

- La base SQLite supera `PRAGMA integrity_check` con resultado `ok`.
- La base contiene 12 series, 10 fuentes, 4.487 observaciones, 14 ejecuciones de ingesta y 98 alertas.
- El Observatorio público carga mediante la herramienta de pruebas de Streamlit sin excepciones.
- El actualizador local carga mediante la herramienta de pruebas de Streamlit sin excepciones.
- El código Python del Observatorio, del actualizador y del paquete compila sin errores.
- Existe creación manual de respaldos, descarga de la copia más reciente y recuperación protegida.
- La versión declarada por el paquete, la API, el dashboard y la documentación quedó alineada en 2.13.1.

## Capacidades consolidadas

1. Catálogo de 12 indicadores oficiales de Costa Rica.
2. Fichas metodológicas, gráficos, contexto y fuentes oficiales.
3. Preferencias con hasta seis indicadores favoritos.
4. Estado de actualización y calendario económico.
5. Lecturas descriptivas, señales relacionadas y advertencias contra conclusiones causales indebidas.
6. Descargas de fichas, series, panorama y calendario.
7. Actualización local con vista previa y confirmación humana.
8. Comparación que distingue observaciones nuevas, revisiones y filas sin cambios.
9. Historial de ingestas, respaldos y recuperación protegida.
10. Conector piloto del BCCR preparado para activarse cuando existan credenciales válidas.

## Límites actuales

- La aplicación pública no modifica la base oficial; la administración permanece local.
- El webservice del BCCR sigue bloqueado hasta recibir credenciales oficiales.
- Varias fuentes todavía se actualizan cargando manualmente archivos descargados de sus sitios oficiales.
- La demostración pública no sustituye todavía una arquitectura multiusuario con autenticación y base administrada.
- Las lecturas automáticas son descriptivas: no son pronósticos, recomendaciones ni demostraciones de causalidad.

## Próximo bloque recomendado

Completar la **aceptación visual y operativa manual**: escritorio, teléfono, descargas, navegación local, actualización con archivo oficial nuevo y restauración controlada. La evidencia automatizada está en `audit_reports/aceptacion_mvp_2026-08-01.md`. Las incidencias encontradas deben corregirse antes de ampliar el catálogo o añadir funciones comerciales.
