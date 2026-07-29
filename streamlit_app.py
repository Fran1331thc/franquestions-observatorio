"""Publicación estable y ligera del Observatorio Económico FranQuestions."""

from pathlib import Path
import sqlite3
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from fq_observatorio.publication_calendar import (
    build_calendar_events,
    calendar_to_ics,
)
from fq_observatorio.panorama_pdf import build_panorama_pdf


APP_DIR = Path(__file__).resolve().parent
DATABASE = APP_DIR / "franquestions.db"

INDICATORS = {
    "exchange-rate": ("Tipo de cambio CRC/USD", "CRC por USD", "BCCR"),
    "policy-rate": ("Tasa de Política Monetaria", "% anual", "BCCR"),
    "inflation": ("Inflación interanual", "% interanual", "INEC/BCCR"),
    "imae": ("IMAE tendencia-ciclo", "% interanual", "BCCR"),
    "unemployment": ("Tasa de desempleo", "% de la fuerza de trabajo", "INEC"),
    "poverty": ("Hogares en pobreza", "% de hogares", "INEC"),
    "fiscal-balance": ("Balance financiero", "% del PIB", "Ministerio de Hacienda"),
    "public-debt": ("Deuda del Gobierno Central", "% del PIB", "Ministerio de Hacienda"),
    "reserves": ("Reservas brutas del Banco Central", "USD millones", "BCCR"),
    "exports": ("Exportaciones FOB", "USD millones", "BCCR/Aduanas"),
    "tourism": ("Llegadas internacionales de turistas", "personas", "ICT/DGME"),
    "fdi": ("Inversión directa en Costa Rica", "USD millones", "BCCR/IED"),
}

GROUPS = {
    "Coyuntura económica": ("exchange-rate", "policy-rate", "inflation", "imae"),
    "Sociedad y finanzas públicas": (
        "unemployment",
        "poverty",
        "fiscal-balance",
        "public-debt",
    ),
    "Sector externo": ("reserves", "exports", "tourism", "fdi"),
}

FREQUENCIES = {
    "exchange-rate": "daily",
    "policy-rate": "daily",
    "inflation": "monthly",
    "imae": "monthly",
    "unemployment": "monthly",
    "poverty": "annual",
    "fiscal-balance": "annual",
    "public-debt": "annual",
    "reserves": "monthly",
    "exports": "monthly",
    "tourism": "monthly",
    "fdi": "quarterly",
}

FRESHNESS_WINDOWS = {
    "daily": (4, 10),
    "monthly": (62, 100),
    "quarterly": (155, 220),
    "annual": (430, 550),
}

DEFAULT_FAVORITES = (
    "exchange-rate",
    "inflation",
    "imae",
    "policy-rate",
    "unemployment",
    "poverty",
)

FQ_READINGS = {
    "exchange-rate": {
        "meaning": "Muestra cuántos colones se requieren para comprar un dólar estadounidense.",
        "hypotheses": (
            "Flujos de divisas por exportaciones, turismo o inversión.",
            "Condiciones financieras internacionales y tasas de interés.",
            "Expectativas y decisiones del Banco Central.",
        ),
    },
    "policy-rate": {
        "meaning": "Resume la orientación de la política monetaria del Banco Central.",
        "hypotheses": (
            "Trayectoria reciente y esperada de la inflación.",
            "Actividad económica y condiciones del crédito.",
            "Decisiones futuras comunicadas por el Banco Central.",
        ),
    },
    "inflation": {
        "meaning": "Mide el cambio interanual del costo de una canasta representativa de consumo.",
        "hypotheses": (
            "Cambios en alimentos, combustibles y servicios.",
            "Efectos del tipo de cambio y los costos importados.",
            "Presiones de demanda, oferta y expectativas.",
        ),
    },
    "imae": {
        "meaning": "Aproxima la trayectoria mensual de la actividad económica, pero no sustituye al PIB.",
        "hypotheses": (
            "Sectores que explican la aceleración o desaceleración.",
            "Diferencias entre régimen especial y régimen definitivo.",
            "Efectos estacionales y posibles revisiones de la serie.",
        ),
    },
    "unemployment": {
        "meaning": "Indica qué proporción de la fuerza de trabajo está desempleada.",
        "hypotheses": (
            "Cambios en la participación laboral.",
            "Creación o pérdida de empleo por sector.",
            "Diferencias por sexo, edad, región y condición de informalidad.",
        ),
    },
    "poverty": {
        "meaning": "Resume la proporción de hogares cuyo ingreso está por debajo de la línea de pobreza.",
        "hypotheses": (
            "Cambios en empleo, salarios e ingresos de los hogares.",
            "Inflación y costo de la canasta básica.",
            "Transferencias sociales y diferencias territoriales.",
        ),
    },
    "fiscal-balance": {
        "meaning": "Compara los ingresos y gastos del Gobierno Central durante el periodo.",
        "hypotheses": (
            "Comportamiento de la recaudación y del gasto primario.",
            "Carga de intereses y costo del financiamiento.",
            "Efectos extraordinarios o cambios contables.",
        ),
    },
    "public-debt": {
        "meaning": "Relaciona la deuda del Gobierno Central con el tamaño de la economía.",
        "hypotheses": (
            "Balance primario y costo de los intereses.",
            "Crecimiento nominal del PIB y tipo de cambio.",
            "Operaciones de financiamiento y revisiones metodológicas.",
        ),
    },
    "reserves": {
        "meaning": "Muestra los activos externos de reserva administrados por el Banco Central.",
        "hypotheses": (
            "Compras o ventas de divisas del Banco Central.",
            "Desembolsos, pagos externos y movimientos del Gobierno.",
            "Valoración de activos y cambios metodológicos.",
        ),
    },
    "exports": {
        "meaning": "Mide el valor de los bienes exportados bajo valoración FOB.",
        "hypotheses": (
            "Cambios en volumen y precios internacionales.",
            "Desempeño por producto, destino y régimen comercial.",
            "Estacionalidad, revisiones y efectos del tipo de cambio.",
        ),
    },
    "tourism": {
        "meaning": "Cuenta las llegadas internacionales de turistas registradas en el periodo.",
        "hypotheses": (
            "Conectividad aérea y oferta de vuelos.",
            "Temporada turística y condiciones económicas externas.",
            "Cambios por mercado de origen y vía de ingreso.",
        ),
    },
    "fdi": {
        "meaning": "Registra flujos de inversión directa hacia la economía costarricense.",
        "hypotheses": (
            "Nuevas inversiones, reinversión de utilidades y deuda entre empresas.",
            "Diferencias por régimen, sector y país de origen.",
            "Operaciones excepcionales y revisiones de cifras preliminares.",
        ),
    },
}

VERIFICATION_QUESTIONS = (
    "¿El movimiento aparece también en sus componentes relacionados?",
    "¿La fuente publicó una revisión o nota metodológica?",
    "¿La señal se mantiene al comparar más de un periodo?",
)

RELATED_SIGNALS = {
    "exchange-rate": (
        ("reserves", "Capacidad de amortiguar choques externos."),
        ("inflation", "Posible transmisión de costos importados hacia los precios."),
        ("policy-rate", "Condiciones monetarias relativas y expectativas."),
    ),
    "policy-rate": (
        ("inflation", "Principal referencia para evaluar presiones de precios."),
        ("exchange-rate", "Canal financiero y de expectativas monetarias."),
        ("imae", "Contexto de actividad económica para la decisión de tasas."),
    ),
    "inflation": (
        ("policy-rate", "Respuesta de política monetaria frente a los precios."),
        ("exchange-rate", "Posible transmisión de costos importados."),
        ("imae", "Contexto de demanda y actividad económica."),
    ),
    "imae": (
        ("unemployment", "Contraste entre actividad y capacidad de generar empleo."),
        ("exports", "Demanda externa y producción vinculada al comercio."),
        ("policy-rate", "Condiciones financieras que pueden influir en la actividad."),
    ),
    "unemployment": (
        ("imae", "Contraste entre producción y mercado laboral."),
        ("poverty", "Relación contextual entre empleo e ingresos de los hogares."),
        ("inflation", "Efecto del costo de vida sobre el ingreso real."),
    ),
    "poverty": (
        ("unemployment", "Acceso al empleo y generación de ingresos."),
        ("inflation", "Poder adquisitivo y costo de la canasta básica."),
        ("imae", "Contexto general de crecimiento y actividad."),
    ),
    "fiscal-balance": (
        ("public-debt", "Los déficits persistentes aumentan las necesidades de deuda."),
        ("policy-rate", "Condiciones financieras y costo de financiamiento."),
        ("imae", "La actividad influye en recaudación y algunos gastos."),
    ),
    "public-debt": (
        ("fiscal-balance", "Flujo fiscal que modifica las necesidades de financiamiento."),
        ("policy-rate", "Referencia para las condiciones generales de tasas."),
        ("exchange-rate", "Puede afectar la valoración de obligaciones en moneda extranjera."),
    ),
    "reserves": (
        ("exchange-rate", "Mercado cambiario y capacidad de respuesta externa."),
        ("exports", "Una fuente potencial de entrada de divisas."),
        ("tourism", "Ingresos de divisas asociados a visitantes internacionales."),
    ),
    "exports": (
        ("imae", "Producción y actividad de sectores exportadores."),
        ("exchange-rate", "Contexto de competitividad y valoración en colones."),
        ("reserves", "Vínculo con la disponibilidad agregada de divisas."),
    ),
    "tourism": (
        ("exchange-rate", "Contexto de precios relativos para visitantes."),
        ("reserves", "Ingresos externos y disponibilidad de divisas."),
        ("imae", "Actividad de servicios vinculados al turismo."),
    ),
    "fdi": (
        ("exchange-rate", "Condiciones cambiarias para flujos de capital."),
        ("reserves", "Contexto de la posición externa del país."),
        ("imae", "Entorno de actividad y capacidad productiva."),
    ),
}


def read_observations() -> pd.DataFrame:
    """Lee la base publicada sin conservar conexiones entre sesiones."""
    with sqlite3.connect(DATABASE) as connection:
        return pd.read_sql_query(
            """
            SELECT s.slug, s.description, src.url AS source_url,
                   o.period, CAST(o.value AS REAL) AS value
            FROM observations AS o
            JOIN series AS s ON s.id = o.series_id
            JOIN sources AS src ON src.id = s.source_id
            WHERE s.slug IN (
                'exchange-rate','policy-rate','inflation','imae',
                'unemployment','poverty','fiscal-balance','public-debt',
                'reserves','exports','tourism','fdi'
            )
            ORDER BY s.slug, o.period
            """,
            connection,
        )


def format_value(value: float, unit: str) -> str:
    decimals = 0 if unit == "personas" else 2
    return f"{value:,.{decimals}f}"


def freshness_status(slug: str, period: pd.Timestamp) -> dict:
    """Clasifica la vigencia con reglas transparentes según la frecuencia."""
    frequency = FREQUENCIES[slug]
    fresh_days, warning_days = FRESHNESS_WINDOWS[frequency]
    latest_date = period.date()
    age_days = max(0, (date.today() - latest_date).days)
    if age_days <= fresh_days:
        return {
            "status": "Al día",
            "icon": "🟢",
            "review_due": latest_date + timedelta(days=fresh_days),
            "age_days": age_days,
        }
    if age_days <= warning_days:
        return {
            "status": "Revisar pronto",
            "icon": "🟡",
            "review_due": latest_date + timedelta(days=fresh_days),
            "age_days": age_days,
        }
    return {
        "status": "Actualización pendiente",
        "icon": "🔴",
        "review_due": latest_date + timedelta(days=fresh_days),
        "age_days": age_days,
    }


def latest_statement(slug: str, latest_rows: pd.DataFrame) -> str:
    """Construye una oración factual con valor, unidad y periodo."""
    name, unit, _source = INDICATORS[slug]
    if slug not in latest_rows.index:
        return f"{name}: sin datos publicados."
    row = latest_rows.loc[slug]
    period = pd.Timestamp(row["period"]).strftime("%d/%m/%Y")
    value = format_value(float(row["value"]), unit)
    return f"{name}: {value} {unit} ({period})."


st.set_page_config(
    page_title="FranQuestions | Observatorio",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    @media (max-width: 768px) {
        .block-container {padding: 2.8rem 0.8rem 2rem;}
        h1 {font-size: 1.8rem !important;}
        [data-testid="stHorizontalBlock"] {flex-wrap: wrap;}
        [data-testid="column"] {min-width: 100% !important;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("FranQuestions — Observatorio Económico")
st.caption(
    "Datos oficiales de Costa Rica con fuente, fecha y contexto. "
    "Publicación estable 2.11.0."
)

if "show_quick_start" not in st.session_state:
    st.session_state.show_quick_start = True

if st.session_state.show_quick_start:
    with st.container(border=True):
        st.subheader("Empieza aquí")
        st.caption(
            "En menos de un minuto puedes conocer la situación, elegir lo que "
            "quieres vigilar y profundizar con evidencia."
        )
        quick_start_columns = st.columns(3)
        with quick_start_columns[0]:
            st.markdown("**1. Revisa el estado**")
            st.write(
                "Los colores indican si cada fuente está al día o necesita revisión."
            )
        with quick_start_columns[1]:
            st.markdown("**2. Elige tus seis indicadores**")
            st.write(
                "Usa Mis preferencias para crear una vista breve con tus prioridades."
            )
        with quick_start_columns[2]:
            st.markdown("**3. Explora y descarga**")
            st.write(
                "Compara periodos, revisa la fuente y descarga datos o el panorama PDF."
            )
        st.info(
            "FranQuestions describe y organiza evidencia. No presenta sus lecturas "
            "como predicciones, recomendaciones ni pruebas de causalidad."
        )
        if st.button("Entendido, ocultar guía", key="dismiss_quick_start"):
            st.session_state.show_quick_start = False
            st.rerun()
else:
    if st.button(
        "¿Cómo usar FranQuestions?",
        key="open_quick_start",
        help="Vuelve a mostrar la guía inicial.",
    ):
        st.session_state.show_quick_start = True
        st.rerun()

try:
    observations = read_observations()
except Exception as error:
    st.error("No fue posible leer la base oficial publicada.")
    st.exception(error)
    st.stop()

if observations.empty:
    st.warning("La base publicada todavía no contiene observaciones.")
    st.stop()

latest_rows = (
    observations.sort_values("period")
    .groupby("slug", as_index=False)
    .tail(1)
    .set_index("slug")
)

status_rows = []
status_records = []
for slug in INDICATORS:
    if slug not in latest_rows.index:
        continue
    latest_period = pd.Timestamp(latest_rows.loc[slug, "period"])
    status = freshness_status(slug, latest_period)
    status_records.append(
        {
            "slug": slug,
            "latest_period": latest_period.date(),
            "review_due": status["review_due"],
            "status": (
                "current"
                if status["status"] == "Al día"
                else "review"
                if status["status"] == "Revisar pronto"
                else "overdue"
            ),
        }
    )
    status_rows.append(
        {
            "Indicador": INDICATORS[slug][0],
            "Estado": f"{status['icon']} {status['status']}",
            "Último dato": latest_period.strftime("%d/%m/%Y"),
            "Revisión recomendada": status["review_due"].strftime("%d/%m/%Y"),
            "Antigüedad": f"{status['age_days']} días",
        }
    )

st.subheader("Estado de actualización")
status_frame = pd.DataFrame(status_rows)
status_counts = status_frame["Estado"].value_counts()
summary_columns = st.columns(3)
summary_columns[0].metric(
    "🟢 Al día",
    int(sum(value.startswith("🟢") for value in status_frame["Estado"])),
)
summary_columns[1].metric(
    "🟡 Revisar pronto",
    int(sum(value.startswith("🟡") for value in status_frame["Estado"])),
)
summary_columns[2].metric(
    "🔴 Pendientes",
    int(sum(value.startswith("🔴") for value in status_frame["Estado"])),
)
with st.expander("Ver estado de los 12 indicadores"):
    st.dataframe(status_frame, hide_index=True, width="stretch")

calendar_events = build_calendar_events(
    status_records,
    {slug: values[0] for slug, values in INDICATORS.items()},
    {slug: values[2] for slug, values in INDICATORS.items()},
)
st.subheader("Calendario económico")
st.caption(
    "Combina fechas oficiales conocidas y revisiones operativas estimadas. "
    "Las instituciones pueden modificar sus calendarios."
)
horizon_days = st.selectbox(
    "Horizonte",
    (30, 60, 90, 180, 365),
    index=2,
    format_func=lambda days: f"Próximos {days} días",
)
calendar_limit = date.today() + timedelta(days=horizon_days)
visible_calendar = [
    event
    for event in calendar_events
    if date.today() <= event["date"] <= calendar_limit
]
if visible_calendar:
    calendar_frame = pd.DataFrame(
        {
            "Fecha o periodo": event.get("date_label")
            or event["date"].strftime("%d/%m/%Y"),
            "Indicador": event["name"],
            "Fuente": event["source"],
            "Tipo": event["confirmation"],
            "Calendario oficial": event.get("source_url") or "",
        }
        for event in visible_calendar
    )
    st.dataframe(
        calendar_frame,
        hide_index=True,
        width="stretch",
        column_config={
            "Calendario oficial": st.column_config.LinkColumn(
                "Calendario oficial",
                display_text="Abrir fuente",
            )
        },
    )
    calendar_downloads = st.columns(2)
    calendar_downloads[0].download_button(
        "Añadir a mi calendario (.ics)",
        calendar_to_ics(visible_calendar, date.today()).encode("utf-8"),
        file_name=f"FQ_calendario_economico_{date.today().isoformat()}.ics",
        mime="text/calendar; charset=utf-8",
        width="stretch",
    )
    calendar_downloads[1].download_button(
        "Descargar tabla compatible (.csv)",
        ("\ufeff" + calendar_frame.to_csv(index=False, sep=";")).encode("utf-8"),
        file_name=f"FQ_calendario_economico_{date.today().isoformat()}.csv",
        mime="text/csv; charset=utf-8",
        width="stretch",
    )
else:
    st.info("No hay fechas dentro del horizonte seleccionado.")

with st.expander("Resumen ejecutivo automático"):
    st.markdown(
        "- **Precios y condiciones monetarias:** "
        + " ".join(
            latest_statement(slug, latest_rows)
            for slug in ("inflation", "policy-rate", "exchange-rate")
        )
    )
    st.markdown(
        "- **Actividad y empleo:** "
        + " ".join(
            latest_statement(slug, latest_rows)
            for slug in ("imae", "unemployment", "poverty")
        )
    )
    st.markdown(
        "- **Finanzas públicas:** "
        + " ".join(
            latest_statement(slug, latest_rows)
            for slug in ("fiscal-balance", "public-debt")
        )
    )
    st.markdown(
        "- **Sector externo:** "
        + " ".join(
            latest_statement(slug, latest_rows)
            for slug in ("reserves", "exports", "tourism", "fdi")
        )
    )

    attention_items = [
        row["Indicador"]
        for row in status_rows
        if not row["Estado"].startswith("🟢")
    ]
    if attention_items:
        st.warning(
            "**Requieren revisión de fuente o actualización:** "
            + ", ".join(attention_items)
            + "."
        )
    else:
        st.success("Los 12 indicadores están dentro de su ventana operativa.")

    st.caption(
        "Resumen factual y descriptivo. Las series tienen frecuencias y periodos "
        "de referencia distintos; no constituye predicción, recomendación ni "
        "prueba de causalidad."
    )

panorama_records = []
slug_to_group = {
    slug: group_name
    for group_name, group_slugs in GROUPS.items()
    for slug in group_slugs
}
for slug in INDICATORS:
    if slug not in latest_rows.index:
        continue
    row = latest_rows.loc[slug]
    status = freshness_status(slug, pd.Timestamp(row["period"]))
    name, unit, source = INDICATORS[slug]
    panorama_records.append(
        {
            "group": slug_to_group[slug],
            "name": name,
            "value": format_value(float(row["value"]), unit),
            "unit": unit,
            "period": pd.Timestamp(row["period"]).strftime("%d/%m/%Y"),
            "source": source,
            "status": status["status"],
        }
    )

panorama_pdf = build_panorama_pdf(
    panorama_records,
    date.today(),
    attention_items,
)
st.download_button(
    "Descargar Panorama Económico (.pdf)",
    panorama_pdf,
    file_name=f"FQ_Panorama_Economico_{date.today().isoformat()}.pdf",
    mime="application/pdf",
    width="stretch",
)
st.caption(
    "Incluye los 12 indicadores, sus fechas, fuentes, estado de actualización "
    "y una advertencia metodológica."
)

with st.expander("Mis preferencias"):
    favorite_slugs = st.multiselect(
        "Indicadores favoritos",
        options=list(INDICATORS),
        default=list(DEFAULT_FAVORITES),
        max_selections=6,
        format_func=lambda slug: INDICATORS[slug][0],
        help="Elige hasta seis indicadores para mantener una vista breve y útil.",
        key="favorite_indicators",
    )
    st.caption(
        "Esta selección se conserva durante la sesión actual. "
        "La persistencia entre dispositivos se añadirá cuando exista autenticación."
    )

st.subheader("Mis indicadores")
if favorite_slugs:
    favorite_rows = [
        (slug, latest_rows.loc[slug])
        for slug in favorite_slugs
        if slug in latest_rows.index
    ]
    for start in range(0, len(favorite_rows), 3):
        favorite_columns = st.columns(3)
        for column, (slug, row) in zip(
            favorite_columns,
            favorite_rows[start : start + 3],
        ):
            name, unit, source = INDICATORS[slug]
            status = freshness_status(slug, pd.Timestamp(row["period"]))
            with column.container(border=True):
                st.markdown(f"**{name}**")
                st.metric("Último dato", format_value(float(row["value"]), unit))
                st.caption(unit)
                st.caption(
                    f"{pd.Timestamp(row['period']).strftime('%d/%m/%Y')} · "
                    f"{status['icon']} {status['status']}"
                )
else:
    st.info("Selecciona al menos un indicador en Mis preferencias.")

for group_name, slugs in GROUPS.items():
    st.subheader(group_name)
    columns = st.columns(4)
    for column, slug in zip(columns, slugs):
        name, unit, source = INDICATORS[slug]
        with column.container(border=True):
            if slug not in latest_rows.index:
                st.markdown(f"**{name}**")
                st.metric("Último dato", "Sin datos")
                continue
            row = latest_rows.loc[slug]
            st.markdown(f"**{name}**")
            st.metric("Último dato", format_value(float(row["value"]), unit))
            st.caption(unit)
            st.caption(
                f"Actualizado: {pd.Timestamp(row['period']).strftime('%d/%m/%Y')} · {source}"
            )

st.divider()

selected_slug = st.selectbox(
    "Explorar indicador",
    list(INDICATORS),
    format_func=lambda slug: INDICATORS[slug][0],
)
name, unit, source = INDICATORS[selected_slug]
selected = observations.loc[observations["slug"] == selected_slug].copy()
selected["period"] = pd.to_datetime(selected["period"])
selected = selected.sort_values("period")
latest = selected.iloc[-1]

metric_columns = st.columns(3)
metric_columns[0].metric("Último dato", format_value(float(latest["value"]), unit))
metric_columns[0].caption(latest["period"].strftime("%d/%m/%Y"))

if len(selected) > 1:
    previous = float(selected.iloc[-2]["value"])
    current = float(latest["value"])
    change = current - previous
    metric_columns[1].metric("Cambio reciente", f"{change:+,.2f}")
    metric_columns[1].caption(
        f"Frente a {selected.iloc[-2]['period'].strftime('%d/%m/%Y')}"
    )
else:
    metric_columns[1].metric("Cambio reciente", "No disponible")

metric_columns[2].metric("Fuente", source)
metric_columns[2].caption("Dato oficial")

reading = FQ_READINGS[selected_slug]
with st.expander("Lectura FranQuestions: qué sabemos y qué falta verificar"):
    st.markdown("**Hecho comprobado**")
    fact = (
        f"El último dato oficial de {name} es "
        f"{format_value(float(latest['value']), unit)} {unit}, "
        f"correspondiente al {latest['period'].strftime('%d/%m/%Y')}."
    )
    if len(selected) > 1:
        fact += (
            f" Frente a la observación anterior cambió "
            f"{change:+,.2f} {unit}."
        )
    st.write(fact)

    st.markdown("**Qué puede significar**")
    st.write(reading["meaning"])

    st.markdown("**Hipótesis que deben investigarse**")
    for hypothesis in reading["hypotheses"]:
        st.markdown(f"- {hypothesis}")

    st.markdown("**Preguntas de verificación**")
    for question in VERIFICATION_QUESTIONS:
        st.markdown(f"- {question}")

    st.warning(
        "Esta lectura es descriptiva: no demuestra causalidad, no es una "
        "predicción y puede cambiar con nuevas observaciones."
    )

with st.expander("Señales relacionadas: contraste entre indicadores"):
    st.caption(
        "Estas relaciones orientan la investigación. Que dos indicadores se "
        "muevan al mismo tiempo no demuestra que uno cause al otro."
    )
    related_columns = st.columns(3)
    for column, (related_slug, relationship) in zip(
        related_columns,
        RELATED_SIGNALS[selected_slug],
    ):
        related_name, related_unit, related_source = INDICATORS[related_slug]
        with column.container(border=True):
            st.markdown(f"**{related_name}**")
            if related_slug not in latest_rows.index:
                st.metric("Último dato", "Sin datos")
                st.caption(relationship)
                continue
            related_row = latest_rows.loc[related_slug]
            st.metric(
                "Último dato",
                format_value(float(related_row["value"]), related_unit),
            )
            st.caption(related_unit)
            st.caption(
                f"{pd.Timestamp(related_row['period']).strftime('%d/%m/%Y')} · "
                f"{related_source}"
            )
            st.write(relationship)

st.line_chart(
    selected.set_index("period")["value"],
    x_label="Fecha",
    y_label=unit,
)

with st.container(border=True):
    st.subheader(name)
    st.write(str(latest["description"]))
    st.write(f"**Frecuencia y unidad:** {unit}")
    st.write(f"**Fuente oficial:** [{source}]({latest['source_url']})")
    st.caption(
        "Revise siempre la fecha, la unidad, la fuente y las notas metodológicas "
        "antes de citar o interpretar el indicador."
    )
