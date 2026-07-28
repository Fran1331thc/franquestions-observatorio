"""Publicación estable y ligera del Observatorio Económico FranQuestions."""

from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st


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
    "Publicación estable 2.9.3."
)

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
