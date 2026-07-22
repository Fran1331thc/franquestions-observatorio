from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Indicator:
    slug: str
    name: str
    description: str
    source: str
    source_url: str
    frequency: str
    unit: str
    geography: str = "Costa Rica"
    official_code: str | None = None
    status: str = "catalogued"
    why_it_matters: str = ""
    caveat: str = ""
    observation_frequency: str | None = None


INDICATORS = (
    Indicator("inflation", "Inflación interanual", "Variación interanual del IPC general (diciembre 2020=100), producido por INEC y distribuido por BCCR.", "INEC/BCCR", "https://sdd.bccr.fi.cr/es/IndicadoresEconomicos/Inicio/Contenedor/969?Cuadro=51", "monthly", "% interanual", status="official-data-loaded", why_it_matters="Mide el cambio del costo de una canasta representativa.", caveat="El IPC no representa exactamente el consumo de cada hogar."),
    Indicator("exchange-rate", "Tipo de cambio CRC/USD", "Tipo de cambio de referencia de venta.", "BCCR", "https://sdd.bccr.fi.cr/es/IndicadoresEconomicos/Inicio/Contenedor/6?Cuadro=1", "daily", "CRC por USD", "Costa Rica", "318", status="official-data-loaded", why_it_matters="Afecta importaciones, deuda en dólares y competitividad."),
    Indicator("policy-rate", "Tasa de Política Monetaria", "Tasa de referencia del BCCR.", "BCCR", "https://sdd.bccr.fi.cr/es/IndicadoresEconomicos/Inicio/Contenedor/358?Cuadro=223", "daily", "% anual", status="official-data-loaded", why_it_matters="Orienta las condiciones monetarias y las tasas del sistema financiero."),
    Indicator("imae", "IMAE tendencia-ciclo", "Variación interanual del Índice Mensual de Actividad Económica, tendencia-ciclo (2022=100).", "BCCR", "https://sdd.bccr.fi.cr/es/IndicadoresEconomicos/Inicio/Contenedor/1588?Cuadro=944", "monthly", "% interanual", status="official-data-loaded", why_it_matters="Da una lectura oportuna de la actividad antes del PIB trimestral.", caveat="Puede revisarse y no equivale al PIB."),
    Indicator("unemployment", "Tasa de desempleo", "Personas desempleadas como porcentaje de la fuerza de trabajo; estimación nacional de trimestre móvil de la ECE.", "INEC", "https://sistemas.inec.cr/pad5/index.php/catalog/384/related-materials", "quarterly", "% de la fuerza de trabajo", status="official-data-loaded", why_it_matters="Muestra la capacidad de la economía para generar empleo.", caveat="Contiene observaciones mensuales de trimestres móviles, pero el archivo oficial se publica trimestralmente; las diferencias pequeñas deben interpretarse junto con los errores de muestreo.", observation_frequency="monthly"),
    Indicator("poverty", "Hogares en pobreza", "Porcentaje nacional de hogares en pobreza total por línea de pobreza: pobreza no extrema más pobreza extrema.", "INEC", "https://admin.inec.cr/en/node/56187", "annual", "% de hogares", status="official-data-loaded", why_it_matters="Resume insuficiencia de ingreso para cubrir necesidades alimentarias y no alimentarias.", caveat="Dato anual de julio; no equivale a pobreza de personas ni al índice de pobreza multidimensional."),
    Indicator("fiscal-balance", "Balance financiero del Gobierno Central", "Superávit o déficit financiero acumulado al cierre de cada año como porcentaje del PIB.", "Ministerio de Hacienda", "https://www.hacienda.go.cr/EstadisticasFiscales.html", "annual", "% del PIB", status="official-data-loaded", why_it_matters="Indica la necesidad neta de financiamiento público.", caveat="Serie de cierre enero-diciembre; no debe compararse directamente con resultados parciales acumulados durante el año."),
    Indicator("public-debt", "Deuda del Gobierno Central", "Saldo anual de deuda interna y externa del Gobierno Central relativo al PIB oficial utilizado por Hacienda.", "Ministerio de Hacienda", "https://www.hacienda.go.cr/EstadisticasFiscales.html", "annual", "% del PIB", status="official-data-loaded", why_it_matters="Condiciona intereses, riesgo soberano y espacio fiscal.", caveat="La razón se calcula con saldos en millones de colones y el PIB de Hacienda; revisiones del PIB o del tipo de cambio pueden modificarla."),
    Indicator("reserves", "Reservas brutas del Banco Central", "Activos de reserva brutos administrados por el BCCR.", "BCCR", "https://sdd.bccr.fi.cr/es/IndicadoresEconomicos/Inicio/Contenedor/512?Cuadro=68", "monthly", "USD millones", status="official-data-loaded", why_it_matters="Amortiguan choques externos y respaldan la estabilidad cambiaria.", caveat="Es una medida bruta, no reservas internacionales netas; el mes más reciente puede ser provisional."),
    Indicator("exports", "Exportaciones FOB", "Valor mensual de las exportaciones FOB de bienes, con ajustes metodológicos del BCCR.", "BCCR / Dirección General de Aduanas", "https://gee.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?CodCuadro=28&idioma=1", "monthly", "USD millones", official_code="Cuadro 28", status="official-data-loaded", why_it_matters="Mide demanda externa y generación de divisas.", caveat="Cifras preliminares desde enero de 2025; desde 2000 incluyen ajustes por servicios de transformación y mantenimiento y reparaciones."),
    Indicator("tourism", "Llegadas internacionales de turistas", "Llegadas mensuales de turistas internacionales a Costa Rica por todas las vías.", "ICT / DGME", "https://www.ict.go.cr/es/estadisticas/informes-estadisticos.html", "monthly", "personas", status="official-data-loaded", why_it_matters="El turismo es una fuente relevante de empleo y divisas.", caveat="No incluye costarricenses, residentes, tripulantes, transportistas ni cruceristas; la serie reciente disponible llega a junio de 2026."),
    Indicator("fdi", "Inversión directa en Costa Rica", "Flujo trimestral total de inversión directa en la economía declarante bajo el principio direccional.", "BCCR / Grupo Interinstitucional de IED", "https://gee.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmVerCatCuadro.aspx?CodCuadro=2723&idioma=1", "quarterly", "USD millones", official_code="Cuadro 2723", status="official-data-loaded", why_it_matters="Refleja financiamiento productivo externo y capacidad de atracción.", caveat="Es un flujo trimestral, no la posición acumulada; las cifras de 2023 a 2026 son preliminares y pueden revisarse."),
)

CATALOG = {item.slug: item for item in INDICATORS}


def catalog_as_dicts() -> list[dict]:
    return [asdict(item) for item in INDICATORS]
