# Pruebas de aceptación del MVP

Fecha de preparación: 1 de agosto de 2026.

## Resultado automatizado

La ronda automatizada del 1 de agosto de 2026 fue aprobada: **24 de 24 pruebas**, integridad SQLite `ok`, auditoría con **0 errores y 0 advertencias**, catálogo y selectores con **12 de 12 indicadores**. La evidencia completa está en `audit_reports/aceptacion_mvp_2026-08-01.md`.

Las casillas siguientes permanecen sin marcar cuando requieren observación humana. La aprobación automatizada no debe confundirse con la aceptación visual y operativa final.

Use esta lista antes de declarar una nueva versión estable. Marque una prueba únicamente cuando haya observado el resultado esperado. Si falla, anote la incidencia y no publique hasta corregirla o documentar explícitamente el límite.

## A. Inicio y navegación

- [ ] `INICIAR_FRANQUESTIONS.cmd` abre el Observatorio local y mantiene activos sus servicios.
- [ ] `ACTUALIZAR_FRANQUESTIONS.cmd` abre el actualizador en el puerto local previsto.
- [ ] La aplicación pública abre sin pantalla negra ni error visible.
- [ ] Los enlaces entre Observatorio y actualizador funcionan en el entorno local.
- [ ] Cerrar la ventana de inicio detiene los servicios locales de forma comprensible.

## B. Presentación

- [ ] El encabezado, las tarjetas y el explorador se ven completos en una computadora.
- [ ] En un teléfono, las tarjetas se apilan y ningún texto o botón queda fuera de pantalla.
- [ ] Los 12 indicadores muestran valor, fecha, unidad, fuente y estado de actualización.
- [ ] Los gráficos no presentan fechas futuras, saltos imposibles ni unidades incorrectas.
- [ ] Las advertencias metodológicas aparecen en los indicadores que las requieren.

## C. Explorador de los 12 indicadores

Compruebe cada indicador en el selector y marque su fila.

| Indicador | Gráfico | Lectura | Fuente | Descarga |
|---|---:|---:|---:|---:|
| Tipo de cambio CRC/USD | [ ] | [ ] | [ ] | [ ] |
| Tasa de Política Monetaria | [ ] | [ ] | [ ] | [ ] |
| Inflación interanual | [ ] | [ ] | [ ] | [ ] |
| IMAE tendencia-ciclo | [ ] | [ ] | [ ] | [ ] |
| Tasa de desempleo | [ ] | [ ] | [ ] | [ ] |
| Hogares en pobreza | [ ] | [ ] | [ ] | [ ] |
| Balance financiero del Gobierno Central | [ ] | [ ] | [ ] | [ ] |
| Deuda del Gobierno Central | [ ] | [ ] | [ ] | [ ] |
| Reservas brutas del Banco Central | [ ] | [ ] | [ ] | [ ] |
| Exportaciones FOB | [ ] | [ ] | [ ] | [ ] |
| Llegadas internacionales de turistas | [ ] | [ ] | [ ] | [ ] |
| Inversión directa en Costa Rica | [ ] | [ ] | [ ] | [ ] |

## D. Preferencias, calendario y alertas

- [ ] Es posible guardar hasta seis favoritos y recuperarlos al volver a abrir la aplicación.
- [ ] El calendario filtra correctamente solo los favoritos.
- [ ] Las fechas oficiales se distinguen de las fechas operativas estimadas.
- [ ] El archivo `.ics` se abre o importa correctamente en una aplicación de calendario.
- [ ] Los archivos `.xlsx` y `.csv` se abren con columnas separadas correctamente.
- [ ] El Centro de alertas permite marcar avisos como leídos sin alterar observaciones.

## E. Actualización controlada

- [ ] Un archivo oficial válido genera una vista previa coherente.
- [ ] Un archivo idéntico informa `0 nuevas`, `0 revisiones` y no permite una escritura innecesaria.
- [ ] Un archivo con un periodo nuevo lo clasifica como observación nueva.
- [ ] Un cambio real en un periodo existente aparece como revisión con ambos valores visibles.
- [ ] Diferencias menores de representación decimal no se clasifican como revisiones.
- [ ] Un archivo con fechas inválidas, duplicados o columnas equivocadas es rechazado con un mensaje claro.
- [ ] La incorporación exige confirmación humana explícita.
- [ ] Una incorporación válida crea un respaldo antes de modificar la base.
- [ ] El historial registra fuente, estado, filas recibidas, filas escritas y detalle.

## F. Respaldo y recuperación

- [ ] `Crear respaldo ahora` aumenta en uno el contador de respaldos.
- [ ] `Descargar respaldo más reciente` produce un archivo `.db` con tamaño mayor que cero.
- [ ] Se entiende que el archivo `.db` se conserva como respaldo y no necesita abrirse con doble clic.
- [ ] La recuperación exige seleccionar una copia y realizar doble confirmación.
- [ ] Después de una recuperación de prueba, la integridad de la base sigue siendo `ok`.
- [ ] La base conserva 12 series y sus observaciones después de la recuperación.

## G. Resultado final

- [ ] No hay errores visibles ni excepciones en los flujos anteriores.
- [ ] Las incidencias restantes están documentadas con impacto, responsable y decisión.
- [ ] Existe una copia descargada de la base y otra copia fuera de la computadora principal.
- [ ] La versión del paquete, API, interfaz y documentación coincide.
- [ ] La versión candidata fue probada en al menos un navegador de escritorio y un teléfono.

## Registro de incidencias

| ID | Fecha | Prueba | Resultado observado | Gravedad | Estado |
|---|---|---|---|---|---|
| | | | | | |
