# FranQuestions — Observatorio Económico v2.9.2

Repositorio funcional del observatorio macroeconomico de Costa Rica. Incluye 12 indicadores, PostgreSQL, conectores piloto, controles de calidad, API interna y dashboard publico.

Desde la versión 2.7.1, la vigencia de los 12 indicadores se calcula primero contra su próxima fecha oficial de publicación. Las ventanas generales por frecuencia quedan como respaldo cuando no existe un calendario oficial.

La versión 2.8.0 incorpora una presentación adaptable para teléfonos: título protegido de la barra superior, tarjetas apiladas, controles de ancho completo, tablas desplazables y gráficos limitados al ancho de la pantalla.

La versión 2.9.1 mejora el calendario económico y sus descargas: genera eventos `.ics`, un libro `.xlsx` con columnas reales y una tabla `.csv` compatible con la configuración regional en español.

La versión 2.9.2 extiende las descargas de Excel y CSV a cada uno de los 12 indicadores desde el explorador, incluyendo fecha, valor, unidad, nombre del indicador y fuente oficial.

> Estado: MVP local probado. La base incluida contiene 12 series obtenidas de los archivos oficiales conservados en el respaldo. Antes de citar un valor, revise siempre su fecha, unidad y nota metodológica.

La sección **Mis preferencias** conserva hasta seis indicadores favoritos y prepara alertas locales por nuevos datos oficiales, cambios excepcionales y revisiones de fuente. La frecuencia puede ser inmediata, diaria o semanal. Por ahora no se envían correos ni mensajes externos.

El **Centro de alertas** reúne esos avisos, los ordena por prioridad y permite marcarlos como leídos. Todo el estado permanece local en esta etapa.

El **Calendario económico** muestra fechas operativas estimadas para revisar las fuentes, permite filtrar los seis favoritos y descargar los eventos en `.ics` o `.csv`. Estas fechas no se presentan como compromisos oficiales de publicación.

## Que funciona

- Catalogo versionado de 12 indicadores y fuentes oficiales.
- Calendario económico que distingue fechas confirmadas, fechas límite oficiales y revisiones estimadas.
- Recorrido inicial de un minuto, opcional y persistente, para orientar a nuevos usuarios sin saturarlos.
- Tablas para fuentes, series, observaciones, revisiones, ingestas y alertas.
- PostgreSQL en Docker y SQLite para una prueba inmediata.
- Conector BCCR XML con credenciales por entorno.
- Conector INEC parametrizable para CSV oficiales.
- Validacion de faltantes, duplicados, fechas, cambios extremos y frecuencia.
- FastAPI: catalogo, metadatos, observaciones y ultimo valor.
- Streamlit: doce tarjetas, gráfico y ficha explicativa.
- Estado de vigencia para cada serie, con resumen de indicadores al día, fuentes revisadas sin dato nuevo, próximos a revisión y pendientes.
- Primera capa de inteligencia descriptiva: cambio reciente, comparación interanual, tendencia y explicación automática neutral.
- Iniciador de Windows de doble clic con comprobaciones y apertura automática.
- Pruebas de catalogo, conectores, validacion y API.

## Inicio sencillo en Windows

Después de completar una vez la instalación indicada abajo, haga doble clic en:

```text
INICIAR_FRANQUESTIONS.cmd
```

El iniciador comprueba la base de datos, enciende la API y el dashboard, y abre el
Observatorio en el navegador. Mantenga su ventana abierta mientras use la aplicación.
Para detener FranQuestions, cierre esa ventana o presione `Ctrl+C`.

Los registros de diagnóstico se guardan en la carpeta `logs`.

## Actualizar indicadores

Desde el Observatorio pulse `Actualizar datos oficiales`. Como alternativa, abra
`ACTUALIZAR_FRANQUESTIONS.cmd`. La herramienta:

1. identifica el formato esperado para cada indicador;
2. genera una vista previa;
3. valida fechas, faltantes, duplicados, frecuencia y cambios extremos;
4. exige confirmación antes de escribir;
5. crea un respaldo previo de SQLite;
6. conserva el archivo original;
7. registra valores nuevos y revisiones históricas.

La herramienta es local y no descarga datos automáticamente. Los archivos deben provenir
de BCCR, INEC, Hacienda o ICT. Para deuda pública solicita también el archivo fiscal de
diciembre utilizado como denominador del PIB.

## Instalación inicial

Requiere Python 3.11 o posterior.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
```

Para probar sin PostgreSQL, cambie en `.env`:

```dotenv
FQ_DATABASE_URL=sqlite:///./franquestions.db
```

La versión distribuida incluye la base oficial ya preparada. Para crear una base de
demostración separada durante desarrollo puede ejecutar:

```powershell
python scripts/init_db.py --demo
```

Inicie la API y, en otra terminal, el dashboard:

```powershell
uvicorn fq_observatorio.api:app --reload
streamlit run fq_observatorio/dashboard.py
```

- API: http://localhost:8000
- Documentacion: http://localhost:8000/docs
- Dashboard: http://localhost:8501

## PostgreSQL

```powershell
docker compose up -d postgres
Copy-Item .env.example .env
python scripts/init_db.py --demo
```

El esquema independiente esta en `sql/schema.sql`; SQLAlchemy tambien crea las tablas.

## Endpoints

| Metodo | Ruta | Uso |
|---|---|---|
| GET | `/health` | Estado |
| GET | `/api/v1/catalog` | Catalogo de 12 indicadores |
| GET | `/api/v1/series/{slug}` | Metadatos |
| GET | `/api/v1/series/{slug}/observations` | Serie con `start`, `end`, `limit` |
| GET | `/api/v1/series/{slug}/latest` | Ultimo valor |

## Integraciones oficiales

### Ruta temporal sin token

Mientras se resuelve la suscripcion del BCCR, descargue una tabla oficial en CSV o XLSX y carguela sin alterar el archivo original:

```powershell
python scripts/import_official_file.py datos.xlsx `
  --series inflation `
  --date-column Fecha `
  --value-column Valor `
  --sheet 0 `
  --header-row 1
```

La importacion valida primero el archivo, rechaza errores estructurales, crea alertas para advertencias, registra la ejecucion y conserva cualquier valor anterior en `revisions`. Los nombres de columnas dependen del archivo oficial.

Para el archivo oficial de tipo de cambio descargado del nuevo sitio del BCCR:

```powershell
python scripts/import_official_file.py tipo_cambio.xlsx `
  --series exchange-rate `
  --date-column Fecha `
  --value-column "Tipo cambio venta" `
  --sheet 0 `
  --header-row 5
```

Para la Tasa de Politica Monetaria:

```powershell
python scripts/import_official_file.py tpm.xlsx `
  --series policy-rate `
  --date-column Fecha `
  --value-column "Tasa política monetaria" `
  --sheet 0 `
  --header-row 5
```

Para el IMAE tendencia-ciclo, variacion interanual:

```powershell
python scripts/import_official_file.py imae.xlsx `
  --series imae `
  --date-column Fecha `
  --value-column "IMAE, variación interanual (%)" `
  --sheet 0 `
  --header-row 5
```

Para los activos de reserva brutos del Banco Central:

```powershell
python scripts/import_official_file.py reservas.xlsx `
  --series reserves `
  --date-column Fecha `
  --value-column "Reservas brutas del Banco Central" `
  --sheet 0 `
  --header-row 5
```

Para la inflacion interanual medida por el IPC:

```powershell
python scripts/import_official_file.py ipc.xlsx `
  --series inflation `
  --date-column Fecha `
  --value-column "IPC, variación interanual (%)" `
  --sheet 0 `
  --header-row 5
```

Para la tasa de desempleo nacional de trimestre movil de la ECE (formato horizontal):

```powershell
python scripts/import_official_file.py desempleo.xlsx `
  --series unemployment `
  --sheet "C1 total " `
  --horizontal-period-row 4 `
  --horizontal-value-row 110
```

El periodo se registra con el ultimo dia del trimestre movil: por ejemplo, `JAS 2010`
se almacena como `2010-09-30` y `EFM 2026` como `2026-03-31`.

Para hogares en pobreza total por linea de pobreza de la ENAHO:

```powershell
python scripts/import_official_file.py pobreza.xlsx `
  --series poverty `
  --sheet "Cuadro 1" `
  --header-row 3 `
  --label-column "Región de planificación y año" `
  --label-prefix "Total país" `
  --value-column "Total pobreza no extrema y pobreza extrema" `
  --annual-month 7
```

Para el balance financiero anual del Gobierno Central en el cierre de diciembre:

```powershell
python scripts/import_official_file.py 12Diciembre25.xlsx `
  --series fiscal-balance `
  --sheet "ACUMULADO" `
  --horizontal-year-row 7 `
  --horizontal-value-row 72 `
  --value-scale 100
```

El factor 100 convierte las fracciones almacenadas por Excel a puntos porcentuales del PIB.

Para la deuda anual del Gobierno Central como porcentaje del PIB:

```powershell
python scripts/import_official_file.py deuda.xlsx `
  --series public-debt `
  --sheet "Hoja1" `
  --debt-date-row 6 `
  --debt-internal-row 8 `
  --debt-external-row 12 `
  --gdp-file 12Diciembre25.xlsx `
  --gdp-sheet "ACUMULADO" `
  --gdp-year-row 7 `
  --gdp-value-row 78
```

La razon se calcula como `(deuda interna en colones + deuda externa en colones) / PIB * 100`.

Para el archivo `.xls` exportado por el cuadro 28 del BCCR (Exportaciones FOB):

```powershell
python scripts/import_official_file.py BCCR_Exportaciones_FOB.xls `
  --series exports `
  --bccr-html-monthly
```

El importador reconoce el formato HTML interno del archivo, excluye la fila `Total`,
convierte la coma decimal y registra cada observacion en el ultimo dia de su mes.

Para el informe mensual del ICT con llegadas internacionales por todas las vias:

```powershell
python scripts/import_official_file.py ICT_Llegadas_Internacionales.pdf `
  --series tourism `
  --ict-monthly-pdf `
  --pdf-page 12
```

El importador toma exclusivamente el Cuadro 11. Las variaciones extremas de 2020
son advertencias esperadas por el cierre asociado a la pandemia, no errores de carga.

Para inversion directa trimestral recibida por Costa Rica, cuadro 2723 del BCCR:

```powershell
python scripts/import_official_file.py BCCR_Inversion_Directa.xls `
  --series fdi `
  --bccr-html-quarterly `
  --row-label "Total Inversion directa en la economia declarante"
```

La serie usa el principio direccional y no debe confundirse con activos, pasivos
o la posicion acumulada de inversion internacional.

### BCCR

El servicio oficial requiere suscripcion:

```dotenv
FQ_BCCR_NAME=Nombre de la persona usuaria
FQ_BCCR_EMAIL=correo@ejemplo.com
FQ_BCCR_TOKEN=token-entregado-por-bccr
```

`ObtenerIndicadoresEconomicosXML` recibe codigo, rango `dd/mm/yyyy`, nombre, correo y token. Consulte la [guia oficial](https://gee.bccr.fi.cr/indicadoreseconomicos/Documentos/DocumentosMetodologiasNotasTecnicas/Webservices_de_indicadores_economicos.pdf) y el [catalogo publico](https://gee.bccr.fi.cr/Indicadores/Suscripciones/UI/ConsultaIndicadores). El codigo `318` se incluye como piloto para tipo de cambio; los restantes deben confirmarse en el catalogo vigente.

```python
from datetime import date
from fq_observatorio.connectors import BCCRConnector

rows = BCCRConnector().fetch("318", date(2026, 1, 1), date(2026, 1, 31))
```

### INEC

INEC publica paginas tematicas, archivos y microdatos, pero no todos comparten URL o columnas. Configure un CSV oficial:

```dotenv
FQ_INEC_DATA_URL=https://.../archivo-oficial.csv
```

```python
from fq_observatorio.connectors import INECConnector

rows = INECConnector().fetch(date_column="fecha", value_column="tasa")
```

Referencias: [empleo](https://inec.cr/estadisticas-fuentes/encuestas/encuesta-continua-empleo), [pobreza](https://inec.cr/estadisticas-fuentes/encuestas/encuesta-nacional-hogares) e [IPC](https://inec.cr/estadisticas-fuentes/estadisticas-economicas/indice-precios-consumidor).

## Calidad y pruebas

`validate_series(rows, frequency)` informa `missing`, `duplicate`, `invalid_date`, `extreme_change` y `frequency_gap`. Un salto extremo requiere revision; no prueba por si solo que el dato sea erroneo.

```powershell
pytest
ruff check .
```

## Calendario económico

El calendario combina tres clases de fecha claramente identificadas:

- **Confirmada:** fecha definitiva publicada por la institución responsable.
- **Programada oficialmente:** fecha esperada publicada por el BCCR y sujeta a cambio.
- **Fecha límite oficial:** plazo máximo publicado en un calendario oficial; la divulgación puede ocurrir antes.
- **Frecuencia oficial diaria:** publicación regulada para cada día hábil, sin una fecha aislada en el calendario.
- **Semana oficial:** semana de divulgación indicada por la institución, sin atribuirle un día exacto.
- **Estimada:** fecha operativa interna para volver a revisar una fuente cuando no existe un calendario oficial verificable.

Las fechas oficiales de 2026 se apoyan en el calendario definitivo del INEC, el calendario anticipado de divulgación del BCCR, el calendario de reuniones de política monetaria del BCCR, el reglamento cambiario y el calendario semanal del ICT. Cada fila incluye un enlace a su respaldo y el sistema evita convertir semanas o frecuencias oficiales en días exactos inventados.

Referencias: [INEC — Calendario de divulgación estadística 2026](https://admin.inec.cr/sites/default/files/2025-12/evCalendarioDivulgacionEstadistica2026.pdf), [BCCR — Calendario anticipado de divulgación](https://gee.bccr.fi.cr/indicadoreseconomicos/Documentos/NEDD/Calendario-esp.htm), [BCCR — Reuniones de política monetaria 2026](https://www.bccr.fi.cr/comunicacion-y-prensa/Docs_Comunicados_Prensa/CP-BCCR-051-2025-Calendario_reuniones_politica_monetaria_2026.pdf), [BCCR — Reglamento cambiario](https://www.bccr.fi.cr/marco-legal/DocReglamento/Reglamento_Operaciones_Cambiarias_Contado_BCCR.pdf) e [ICT — Calendario de movimientos migratorios](https://www.ict.go.cr/images/Calendario_1_Movimientos_Migratorios.png).

## Estructura

```text
fq_observatorio/       aplicacion, catalogo, conectores y persistencia
scripts/init_db.py     inicializacion y demo
sql/schema.sql         esquema PostgreSQL
tests/                 pruebas basicas
```

## Pendiente para produccion

1. Confirmar y versionar codigos exactos de todas las series BCCR.
2. Crear adaptadores específicos para INEC, Hacienda, PROCOMER e ICT.
3. Orquestar ingestas y escribir revisiones de forma transaccional.
4. Sustituir datos demo por series oficiales y registrar metodologias/licencias.
5. Añadir Alembic, autenticacion, cache, monitoreo y despliegue seguro.
6. Calibrar alertas por serie y probar contra respuestas oficiales controladas.
