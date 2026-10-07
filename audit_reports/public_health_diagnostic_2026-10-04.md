# Diagnóstico operativo de la comprobación pública de Streamlit

Fecha del diagnóstico inicial: 2026-10-04. Actualización confirmatoria: 2026-10-07 (America/Costa_Rica).

Este documento se limita a disponibilidad pública y observabilidad del chequeo. No evalúa los CT metodológicos, las pruebas comerciales ni la propuesta futura Data Intake Gate.

## Conclusión ejecutiva

Se confirmaron dos fallos de acceso observados por el chequeo, con respuestas distintas:

- El 2026-09-27 a las 22:15 CST, `verify-public-beta` agotó el máximo de 50 redirecciones en sus seis intentos.
- El 2026-10-03 a las 20:49 CST, `shadow-check` recibió HTTP 400 en sus seis intentos.

No hay evidencia de una caída continua de la aplicación. El primer fallo fue seguido esa misma noche por dos ejecuciones satisfactorias. El segundo ocurrió después de cinco ejecuciones diarias satisfactorias con el mismo commit. El 2026-10-04 a la 01:44 CST la ruta de salud alojada respondió HTTP 200, cuerpo `ok`, sin redirecciones; a la 01:46 CST la aplicación cargó manualmente en navegador.

La causa externa exacta del episodio de redirecciones del 27 de septiembre no puede confirmarse retrospectivamente. El 7 de octubre sí se confirmó directamente que la aplicación estaba dormida por inactividad: Streamlit mostró `This app has gone to sleep due to inactivity`, mientras el endpoint alojado devolvía HTTP 400. Tras reactivarla, el mismo endpoint respondió HTTP 200 `ok` y la repetición de GitHub Actions terminó satisfactoriamente. Este comportamiento explica el fallo actual y es consistente con el HTTP 400 del 3 de octubre, aunque el estado visual de aquella fecha no quedó registrado.

También se confirmó un defecto del chequeo anterior: sus mensajes ocultaban código HTTP, duración y cadena de redirecciones. Se corrigió esa falta de observabilidad y se mantuvo como ruta canónica de Streamlit Cloud `/~/+/_stcore/health`.

## Confirmación y corrección del 2026-10-07

| Hora Costa Rica | Origen | URL/acción | Evidencia | Duración | Resultado |
|---|---|---|---|---:|---|
| 01:11:59–01:12:50 CST | GitHub Actions, run `37585797891`, intento 1 | `/~/+/_stcore/health` | Seis respuestas HTTP 400, cuerpo vacío, cero redirecciones | 177–294ms por solicitud; paso 51s por las cinco esperas | Fallo |
| 01:14:25 CST | Diagnóstico sin cookies | `/~/+/_stcore/health` | HTTP 400, cuerpo vacío, cero redirecciones | 570ms | Fallo |
| 01:14:29 CST | Diagnóstico sin cookies | `/_stcore/health` | Circuito HTTP 303 hacia autenticación/login | 4.781s hasta cortar; >10 redirecciones | Fallo |
| 01:15 CST | Interfaz de Streamlit | Portada | Mensaje literal: `This app has gone to sleep due to inactivity` | No aplica | Causa actual confirmada |
| 01:15:28 CST | Diagnóstico sin cookies, después de reactivar | `/~/+/_stcore/health` | HTTP 200, cuerpo `ok`, cero redirecciones | 318ms | Éxito |
| 01:16–01:17 CST | GitHub Actions, run `37585797891`, intento 2 | Suite completa + endpoint | Suite, recuperación y chequeo público satisfactorios | 46s total | Éxito |

Commit remoto verificado: `10f1b4d4485435fa996ae0b0466d67b11f18e15f` en `stable-public`.

## Evidencia original

| Ejecución | Hora Costa Rica | Rama y commit | URL consultada | Intentos | Evidencia HTTP/red | Duración | Resultado |
|---|---|---|---|---:|---|---:|---|
| `verify-public-beta` #2, run `36376881964` | 2026-09-27 22:15 CST (inicio del paso) | `stable-public` · `4cb1dcb23cfd6c10787f524f40ea69261f30d639` | `https://franquestions-observatorio-v2.streamlit.app/_stcore/health` | 6 | Cada intento: `curl: (47) Maximum (50) redirects followed`. El registro no conservó los códigos intermedios ni tiempos individuales. | Paso: 2m00s; job: 2m39s | Fallo |
| `shadow-check` #10, run `37172173549` | 2026-10-03 20:49 CST (inicio del paso) | `main` · `e4bcc4db0eaf899d77f5766bf2e4b6a53b0a1a54` | `https://franquestions-observatorio-v2.streamlit.app/~/+/_stcore/health` | 6 | Cada intento: `curl: (22) The requested URL returned error: 400`. Sin redirección ni tiempos individuales registrados. | Paso: 52s; job: 1m27s | Fallo |

En ambos jobs, las comprobaciones anteriores terminaron correctamente. En particular, el `shadow-check` de BCCR y el registro append-only pasaron antes del fallo de acceso público.

## Ejecuciones relacionadas

| Hora Costa Rica | Flujo | Rama y commit | Ruta | Duración del paso | Resultado |
|---|---|---|---|---:|---|
| 2026-09-27 23:17:20 CST | `verify-public-beta` #3 | `stable-public` · `daf938f36aca313ccbffd8babc0385a720ce6ec6` | `/~/+/_stcore/health` | <1s según resolución de GitHub | Éxito |
| 2026-09-27 23:23:47 CST | `verify-public-beta` #4 | `stable-public` · `b3e0dfae39e655ba08bcfa7e5ebf5d14dfd5dcd5` | `/~/+/_stcore/health` | <1s según resolución de GitHub | Éxito |
| 2026-10-02 20:13:28 CST | `shadow-check` #9 | `main` · `e4bcc4db0eaf899d77f5766bf2e4b6a53b0a1a54` | `/~/+/_stcore/health` | <1s según resolución de GitHub | Éxito |

Entre el 28 de septiembre y el 2 de octubre hubo otras cuatro ejecuciones satisfactorias de `shadow-check` con el mismo commit `e4bcc4d`. Al cerrar este diagnóstico todavía no existía una ejecución programada posterior al fallo #10.

## Reproducción manual del 2026-10-04

| Hora Costa Rica | Método | URL | HTTP | Respuesta relevante | Duración | Redirecciones | Resultado |
|---|---|---|---:|---|---:|---:|---|
| 01:44:25 CST | Script diagnóstico, acceso sin cookies | `/_stcore/health` | 303 | Sin cuerpo; circuito entre la aplicación, `share.streamlit.io/-/auth/app` y `/-/login` | 5.474s hasta cortar | >10 | Fallo |
| 01:44:25 CST | Script diagnóstico, acceso sin cookies | `/~/+/_stcore/health` | 200 | `ok` | 486ms | 0 | Éxito |
| 01:45:27 CST | Repetición del chequeo nuevo | `/~/+/_stcore/health` | 200 | `ok` | 331ms | 0 | Éxito |
| 01:46 CST aprox. | Navegador | `/` | 200 visible | Título y contenido del Observatorio cargados | ~5s hasta contenido completo | Navegador las resolvió | Éxito |

Los valores de consultas en redirecciones se redactan deliberadamente. No se guardaron cookies, encabezados de autenticación ni cargas de sesión.

## Hechos, hipótesis y causa confirmada

### Hechos

- El primer fallo fue un bucle de redirecciones; el segundo fue HTTP 400.
- Los seis intentos de cada job fallaron de la misma manera dentro de su ejecución.
- Hubo ejecuciones satisfactorias entre ambos fallos, incluso cinco con el mismo commit del segundo fallo.
- La ruta alojada respondió correctamente durante este diagnóstico y la aplicación abrió manualmente.
- El chequeo anterior descartaba la salida de `curl` y no registraba metadatos suficientes para atribuir el origen de la respuesta.

### Hipótesis aún no confirmadas

- Que el fallo HTTP 400 del 3 de octubre también correspondiera a reposo por inactividad. Es consistente con la reproducción del 7 de octubre, pero no existe captura de la pantalla de reposo de aquella fecha.
- Que el bucle del 27 de septiembre tuviera el mismo origen. El síntoma fue distinto y no debe agruparse sin evidencia adicional.

No existe evidencia suficiente para elegir entre estas hipótesis ni para atribuir el incidente al código de FranQuestions.

### Causa confirmada

- **Del fallo reproducido el 7 de octubre:** reposo automático de Streamlit Community Cloud por inactividad.
- **De la baja calidad diagnóstica:** el script ocultaba los metadatos necesarios. Esto está confirmado por su implementación y por los registros originales.
- **Del HTTP 400 del 3 de octubre:** causa probable, no confirmada retrospectivamente, de reposo por inactividad.
- **Del bucle del 27 de septiembre:** no confirmada.

## Cambio aplicado

- Ambos workflows usan la misma ruta alojada `/~/+/_stcore/health`.
- El chequeo conserva seis intentos, espera de 10 segundos y tiempo máximo de 30 segundos por solicitud.
- Cada intento registra en JSON: UTC y Costa Rica, URL saneada, estado HTTP, fragmento limitado del cuerpo, duración, número y destinos saneados de redirecciones, y resultado.
- Los valores de consulta se sustituyen por `<redacted>` para evitar guardar cargas de autenticación.
- Se añadieron pruebas unitarias para respuesta `ok`, redirección y redacción de consultas.

## Impacto sobre la ronda pequeña

No hay evidencia de pérdida de datos, corrupción del Observatorio ni fallo de las comprobaciones BCCR. El riesgo para participantes fue de acceso intermitente: una persona que coincidiera con una ventana problemática podría no abrir la aplicación. No se debe invalidar la ronda ni interpretar estos eventos como evidencia metodológica. Conviene anotar cualquier imposibilidad de acceso con hora y reintentar una vez, sin cambiar el formulario ni la experiencia durante la ronda.

## Pendientes

1. Confirmar la siguiente ejecución programada de `shadow-check` con el registro enriquecido; el workflow en `main` todavía debe recibir la misma instrumentación que `stable-public`.
2. Si vuelve a fallar, conservar el JSON del intento y comparar código, ruta y cadena de redirecciones antes de atribuir causa.
3. Considerar dos señales separadas en una ronda posterior: salud técnica (`ok`) y acceso anónimo real a la portada. No ampliar ahora el alcance de la beta.
