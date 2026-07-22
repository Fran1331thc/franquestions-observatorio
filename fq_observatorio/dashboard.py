import httpx
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import date, timedelta
from importlib import reload
from io import BytesIO
from sqlalchemy import select

from fq_observatorio.catalog import CATALOG
from fq_observatorio.db import SessionLocal
from fq_observatorio.freshness import evaluate_freshness
import fq_observatorio.config as config_module
import fq_observatorio.intelligence as intelligence_module
import fq_observatorio.preferences as preferences_module
import fq_observatorio.alert_center as alert_center_module
import fq_observatorio.publication_calendar as calendar_module
from fq_observatorio.models import IngestionRun, Observation, Revision, Series

# Streamlit puede conservar módulos antiguos en memoria durante una recarga parcial.
# Recargarlos evita errores cuando una versión añade nuevas funciones o ajustes.
config_module = reload(config_module)
intelligence_module = reload(intelligence_module)
preferences_module = reload(preferences_module)
alert_center_module = reload(alert_center_module)
calendar_module = reload(calendar_module)
get_settings = config_module.get_settings
analyze_series = intelligence_module.analyze_series
build_fq_reading = intelligence_module.build_fq_reading
explain_analysis = intelligence_module.explain_analysis
related_indicator_specs = intelligence_module.related_indicator_specs
build_research_brief = intelligence_module.build_research_brief
build_economic_snapshot = intelligence_module.build_economic_snapshot
build_executive_summary = intelligence_module.build_executive_summary
load_preferences = preferences_module.load_preferences
save_preferences = preferences_module.save_preferences
load_preferences_from_values = preferences_module.load_preferences_from_values
build_local_alerts = alert_center_module.build_local_alerts
build_calendar_events = calendar_module.build_calendar_events
calendar_to_ics = calendar_module.calendar_to_ics

settings = get_settings()
INDICATOR_GROUPS = {
    "Coyuntura económica": ["exchange-rate", "policy-rate", "inflation", "imae"],
    "Sociedad y finanzas públicas": [
        "unemployment",
        "poverty",
        "fiscal-balance",
        "public-debt",
    ],
    "Sector externo": ["reserves", "exports", "tourism", "fdi"],
}
PUBLIC_SLUGS = [slug for slugs in INDICATOR_GROUPS.values() for slug in slugs]
if settings.env == "production":
    preferences = load_preferences_from_values(
        st.session_state.get("fq_preferences", {}), set(PUBLIC_SLUGS)
    )
    st.session_state["fq_preferences"] = preferences
else:
    preferences = load_preferences(settings.preferences_path, set(PUBLIC_SLUGS))
FREQUENCY_LABELS = {
    "daily": "Diaria",
    "monthly": "Mensual",
    "quarterly": "Trimestral",
    "annual": "Anual",
}
CARD_SOURCE_LABELS = {
    "Ministerio de Hacienda": "Hacienda",
    "BCCR / Dirección General de Aduanas": "BCCR/Aduanas",
    "BCCR / Grupo Interinstitucional de IED": "BCCR/IED",
}
CARD_TITLES = {"fiscal-balance": "Balance financiero"}
STATUS_ICONS = {"current": "🟢", "checked": "🔵", "review": "🟡", "overdue": "🔴", "missing": "⚪"}


def acknowledge_source_check(status: dict, checked_on: date | None, frequency: str) -> dict:
    """Presenta una revisión oficial sin dato nuevo aunque Streamlit conserve módulos antiguos."""
    if not checked_on or status.get("status") not in {"review", "overdue"}:
        return status
    review_due = status.get("review_due")
    if review_due and checked_on < review_due:
        return status
    fresh_days = {"daily": 4, "monthly": 62, "quarterly": 155, "annual": 430}.get(frequency, 62)
    return {
        **status,
        "status": "checked",
        "label": "Fuente revisada, sin dato nuevo",
        "severity": "info",
        "last_checked": checked_on,
        "review_due": checked_on + timedelta(days=fresh_days),
        "explanation": "La fuente oficial fue revisada y todavía no publicó una observación posterior.",
    }


def persist_preferences(values: dict) -> dict:
    """Aísla las preferencias por sesión pública y conserva el archivo del propietario local."""
    if settings.env == "production":
        clean = load_preferences_from_values(values, set(PUBLIC_SLUGS))
        st.session_state["fq_preferences"] = clean
        return clean
    return save_preferences(settings.preferences_path, values, set(PUBLIC_SLUGS))

st.set_page_config(page_title="FranQuestions | Observatorio", page_icon="📊", layout="wide")
st.markdown('<h1 translate="no" class="notranslate">FranQuestions — Observatorio Económico</h1>', unsafe_allow_html=True)
st.caption("Datos oficiales de Costa Rica con fuente, fecha y contexto. Versión preliminar 2.9.2")
if settings.env != "production":
    st.markdown("[🔄 **Actualizar datos oficiales**](http://127.0.0.1:8503)")
st.markdown(
    """
    <style>
    @media (max-width: 768px) {
        .block-container {padding: 3.4rem 0.75rem 2rem !important;}
        h1 {font-size: 1.7rem !important; line-height: 1.15 !important; overflow-wrap: anywhere;}
        h2 {font-size: 1.5rem !important; line-height: 1.2 !important;}
        h3 {font-size: 1.2rem !important; line-height: 1.2 !important;}
        p, li, label {line-height: 1.45 !important;}
        [data-testid="stHorizontalBlock"] {flex-wrap: wrap !important; gap: 0.65rem !important;}
        [data-testid="column"] {
            flex: 1 1 100% !important;
            width: 100% !important;
            min-width: 100% !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.85rem !important;
            white-space: normal !important;
            overflow-wrap: anywhere !important;
        }
        [data-testid="stDataFrame"] {max-width: 100%; overflow-x: auto;}
        .stButton > button, .stDownloadButton > button {width: 100%; min-height: 2.75rem;}
        [data-testid="stExpander"] details summary {min-height: 3rem;}
        .js-plotly-plot, .plot-container {max-width: 100% !important;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300)
def api_get(path: str):
    if settings.env == "production":
        return database_get(path)
    try:
        response = httpx.get(f"{settings.api_url}{path}", timeout=3)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError:
        return database_get(path)


def database_get(path: str):
    """Serve las consultas esenciales desde SQLite cuando no existe una API separada."""
    route = path.split("?", 1)[0].strip("/").split("/")
    if len(route) != 5 or route[:3] != ["api", "v1", "series"]:
        raise httpx.ConnectError(f"Ruta local no compatible: {path}")
    slug, action = route[3], route[4]
    with SessionLocal() as session:
        series = session.scalar(select(Series).where(Series.slug == slug))
        if not series:
            raise httpx.ConnectError(f"Serie no disponible: {slug}")
        if action == "latest":
            row = session.scalar(
                select(Observation)
                .where(Observation.series_id == series.id)
                .order_by(Observation.period.desc())
                .limit(1)
            )
            if not row:
                raise httpx.ConnectError(f"Serie sin observaciones: {slug}")
            return {
                "slug": slug,
                "period": row.period.isoformat(),
                "value": float(row.value),
                "unit": series.unit,
            }
        if action == "observations":
            rows = session.scalars(
                select(Observation)
                .where(Observation.series_id == series.id)
                .order_by(Observation.period)
                .limit(5000)
            ).all()
            return [{"period": row.period.isoformat(), "value": float(row.value)} for row in rows]
    raise httpx.ConnectError(f"Acción local no compatible: {action}")


def format_value(value: float, unit: str) -> str:
    decimals = 0 if unit == "personas" else 2
    return f"{value:,.{decimals}f}"


def format_period(period: str) -> str:
    return pd.Timestamp(period).strftime("%d/%m/%Y")


def format_change(analysis: dict, annual: bool = False) -> str:
    change = analysis["annual_change" if annual else "recent_change"]
    percent = analysis["annual_percent" if annual else "recent_percent"]
    if change is None:
        return "No disponible"
    if analysis["is_rate"]:
        return f"{change:+.2f} puntos"
    return f"{percent:+.2f}%" if percent is not None else "No calculable"


def dataframe_to_excel(frame: pd.DataFrame) -> bytes:
    """Genera un libro de Excel sin depender del separador regional del equipo."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame.to_excel(writer, sheet_name="Calendario", index=False)
        worksheet = writer.sheets["Calendario"]
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions
        for index, column in enumerate(frame.columns, start=1):
            longest = max(len(str(column)), *(len(str(value)) for value in frame[column]))
            worksheet.column_dimensions[chr(64 + index)].width = min(longest + 2, 55)
    return output.getvalue()


guide_title = "Empieza aquí · recorrido de 1 minuto" if not preferences["onboarding_complete"] else "Cómo usar FranQuestions"
with st.expander(guide_title, expanded=not preferences["onboarding_complete"]):
    st.write("FranQuestions convierte datos oficiales en una lectura clara, sin ocultar fuentes ni incertidumbres.")
    guide_columns = st.columns(3)
    with guide_columns[0].container(border=True):
        st.markdown("### 1. Elige")
        st.write("Guarda hasta seis indicadores en **Mis preferencias** para crear tu tablero personal.")
    with guide_columns[1].container(border=True):
        st.markdown("### 2. Comprende")
        st.write("Revisa el último dato, su fecha, tendencia y advertencias antes de interpretarlo.")
    with guide_columns[2].container(border=True):
        st.markdown("### 3. Verifica")
        st.write("Abre la fuente oficial y usa las preguntas FranQuestions antes de sacar conclusiones.")
    st.info("Sugerencia: empieza con inflación, empleo y tipo de cambio. Luego añade los indicadores que afecten tus decisiones.")
    if not preferences["onboarding_complete"] and st.button("Entendido · empezar a explorar", type="primary"):
        preferences = persist_preferences(
            {**preferences, "onboarding_complete": True},
        )
        st.rerun()

with st.expander("Mis preferencias", expanded=False):
    favorite_selection = st.multiselect(
        "Indicadores favoritos",
        PUBLIC_SLUGS,
        default=preferences["favorites"],
        format_func=lambda slug: CATALOG[slug].name,
        max_selections=6,
    )
    default_options = favorite_selection or preferences["favorites"]
    current_default = preferences["default_indicator"] if preferences["default_indicator"] in default_options else default_options[0]
    default_selection = st.selectbox(
        "Indicador principal",
        default_options,
        index=default_options.index(current_default),
        format_func=lambda slug: CATALOG[slug].name,
    )
    detail_selection = st.radio(
        "Nivel de detalle",
        ("Esencial", "Completo"),
        index=0 if preferences["detail_level"] == "Esencial" else 1,
        horizontal=True,
    )
    st.markdown("**Alertas para mis indicadores**")
    alert_labels = {
        "official_update": "Nuevo dato oficial",
        "extreme_change": "Cambio excepcional",
        "revision": "Revisión de la fuente",
    }
    alert_selection = st.multiselect(
        "Avisarme cuando ocurra",
        list(alert_labels),
        default=preferences["alert_types"],
        format_func=lambda value: alert_labels[value],
    )
    alert_frequency = st.radio(
        "Frecuencia preferida",
        ("Inmediata", "Diaria", "Semanal"),
        index=("Inmediata", "Diaria", "Semanal").index(preferences["alert_frequency"]),
        horizontal=True,
        help="Esta preferencia queda preparada localmente. El envío externo se habilitará en una etapa posterior.",
    )
    if st.button("Guardar preferencias", type="primary"):
        preferences = persist_preferences(
            {
                **preferences,
                "favorites": favorite_selection,
                "default_indicator": default_selection,
                "detail_level": detail_selection,
                "alert_types": alert_selection,
                "alert_frequency": alert_frequency,
            },
        )
        st.success("Preferencias guardadas en esta computadora.")

if preferences["alert_types"]:
    alert_names = {
        "official_update": "nuevos datos oficiales",
        "extreme_change": "cambios excepcionales",
        "revision": "revisiones de la fuente",
    }
    enabled_alerts = ", ".join(alert_names[value] for value in preferences["alert_types"])
    st.info(
        f"Alertas locales preparadas para {len(preferences['favorites'])} indicadores: "
        f"{enabled_alerts}. Frecuencia: {preferences['alert_frequency'].lower()}. "
        "Aún no se envían correos ni mensajes."
    )


try:
    latest_by_slug = {
        slug: api_get(f"/api/v1/series/{slug}/latest") for slug in PUBLIC_SLUGS
    }
    statuses = [
        evaluate_freshness(
            slug,
            pd.Timestamp(latest_by_slug[slug]["period"]).date(),
            CATALOG[slug].frequency,
            date.today(),
        ).as_dict()
        for slug in PUBLIC_SLUGS
    ]
    with SessionLocal() as session:
        for index, status in enumerate(statuses):
            series = session.scalar(select(Series).where(Series.slug == status["slug"]))
            if not series:
                continue
            check = session.scalar(
                select(IngestionRun)
                .where(
                    IngestionRun.source_id == series.source_id,
                    IngestionRun.status == "checked_no_change",
                )
                .order_by(IngestionRun.finished_at.desc())
                .limit(1)
            )
            checked_on = check.finished_at.date() if check and check.finished_at else None
            statuses[index] = acknowledge_source_check(status, checked_on, CATALOG[status["slug"]].frequency)
    status_by_slug = {item["slug"]: item for item in statuses}
    status_counts = {
        key: sum(item.get("status") == key for item in statuses)
        for key in ("current", "checked", "review", "overdue")
    }

    st.subheader("Estado de actualización")
    summary_columns = st.columns(4)
    summary_columns[0].metric("🟢 Al día", status_counts["current"])
    summary_columns[1].metric("🔵 Fuente revisada", status_counts["checked"])
    summary_columns[2].metric("🟡 Revisar pronto", status_counts["review"])
    summary_columns[3].metric("🔴 Pendientes", status_counts["overdue"])
    with st.expander("Ver estado de los 12 indicadores"):
        status_table = pd.DataFrame(
            {
                "Indicador": CATALOG[item["slug"]].name,
                "Estado": (
                    "🔵 Fuente revisada"
                    if item.get("status") == "checked"
                    else f"{STATUS_ICONS.get(item.get('status'), '⚪')} {item.get('label', 'Sin datos')}"
                ),
                "Último dato": format_period(item["latest_period"]) if item.get("latest_period") else "—",
                "Revisión recomendada": format_period(item["review_due"]) if item.get("review_due") else "—",
                "Antigüedad": f"{item['age_days']} días" if "age_days" in item else "—",
            }
            for item in statuses
        )
        st.dataframe(status_table, width="stretch", hide_index=True)

    calendar_events = build_calendar_events(
        statuses,
        {slug: CATALOG[slug].name for slug in PUBLIC_SLUGS},
        {slug: CATALOG[slug].source for slug in PUBLIC_SLUGS},
    )
    st.subheader("Calendario económico")
    st.caption(
        "Combina fechas confirmadas, fechas límite oficiales y revisiones operativas estimadas. "
        "Cada tipo se identifica por separado."
    )
    calendar_controls = st.columns(2)
    favorites_only = calendar_controls[0].checkbox("Solo mis seis favoritos", value=True)
    horizon_days = calendar_controls[1].selectbox(
        "Horizonte",
        (30, 60, 90, 180, 365),
        index=2,
        format_func=lambda days: f"Próximos {days} días",
    )
    calendar_limit = date.today() + timedelta(days=horizon_days)
    visible_calendar = [
        event
        for event in calendar_events
        if (not favorites_only or event["slug"] in preferences["favorites"])
        and date.today() <= event["date"] <= calendar_limit
    ]
    if visible_calendar:
        calendar_table = pd.DataFrame(
            {
                "Fecha o periodo": event.get("date_label") or event["date"].strftime("%d/%m/%Y"),
                "Indicador": event["name"],
                "Fuente": event["source"],
                "Tipo": event["confirmation"],
                "Respaldo": event.get("source_url") or "",
            }
            for event in visible_calendar
        )
        st.dataframe(
            calendar_table,
            width="stretch",
            hide_index=True,
            column_config={"Respaldo": st.column_config.LinkColumn("Calendario oficial", display_text="Abrir fuente")},
        )
        calendar_downloads = st.columns(3)
        calendar_downloads[0].download_button(
            "Añadir a mi calendario (.ics)",
            calendar_to_ics(visible_calendar, date.today()).encode("utf-8"),
            file_name=f"FQ_calendario_economico_{date.today().isoformat()}.ics",
            mime="text/calendar; charset=utf-8",
            width="stretch",
        )
        calendar_downloads[1].download_button(
            "Descargar para Excel (.xlsx)",
            dataframe_to_excel(calendar_table),
            file_name=f"FQ_calendario_economico_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )
        calendar_downloads[2].download_button(
            "Descargar tabla compatible (.csv)",
            ("\ufeff" + calendar_table.to_csv(index=False, sep=";")).encode("utf-8"),
            file_name=f"FQ_calendario_economico_{date.today().isoformat()}.csv",
            mime="text/csv; charset=utf-8",
            width="stretch",
        )
    else:
        st.info("No hay revisiones estimadas dentro del horizonte seleccionado.")

    attention_items = [item for item in statuses if item.get("status") in {"review", "overdue"}]
    if attention_items:
        with st.container(border=True):
            st.subheader("Atención requerida")
            for alert in attention_items:
                icon = STATUS_ICONS[alert["status"]]
                st.write(
                    f"{icon} **{CATALOG[alert['slug']].name}:** {alert['label']}. "
                    f"Último dato: {format_period(alert['latest_period'])}."
                )
            st.markdown("[Abrir herramienta de actualización](http://127.0.0.1:8503)")

    st.subheader("Mis indicadores")
    favorite_slugs = preferences["favorites"]
    for start in range(0, len(favorite_slugs), 3):
        favorite_columns = st.columns(3)
        for column, slug in zip(favorite_columns, favorite_slugs[start:start + 3]):
            favorite_item = CATALOG[slug]
            favorite_latest = latest_by_slug[slug]
            with column.container(border=True):
                st.markdown(f"**{favorite_item.name}**")
                st.metric("Último dato", format_value(favorite_latest["value"], favorite_item.unit))
                st.caption(f"{format_period(favorite_latest['period'])} · {status_by_slug[slug]['label']}")

    snapshot_groups = []
    for group_name, slugs in INDICATOR_GROUPS.items():
        snapshot_items = []
        for slug in slugs:
            snapshot_item = CATALOG[slug]
            snapshot_data = api_get(f"/api/v1/series/{slug}/observations?limit=5000")
            snapshot_frequency = getattr(snapshot_item, "observation_frequency", None) or snapshot_item.frequency
            snapshot_analysis = analyze_series(snapshot_data, snapshot_frequency, snapshot_item.unit)
            snapshot_items.append(
                {
                    "slug": slug,
                    "name": snapshot_item.name,
                    "value": f"{format_value(snapshot_analysis['latest_value'], snapshot_item.unit)} {snapshot_item.unit}",
                    "period": format_period(snapshot_analysis["latest_period"]),
                    "trend": snapshot_analysis["trend"],
                    "status": status_by_slug[slug]["label"],
                    "status_code": status_by_slug[slug]["status"],
                    "caveat": snapshot_item.caveat,
                    "provisional": snapshot_analysis["latest_period"] > date.today(),
                    "extreme": snapshot_analysis.get("extreme_change", False),
                }
            )
        snapshot_groups.append((group_name, snapshot_items))
    economic_snapshot = build_economic_snapshot(snapshot_groups, date.today())
    snapshot_by_slug = {
        item["slug"]
        : item
        for _, indicators in snapshot_groups
        for item in indicators
    }
    revisions_by_slug = {}
    with SessionLocal() as session:
        revision_rows = session.execute(
            select(Revision, Observation, Series)
            .join(Observation, Revision.observation_id == Observation.id)
            .join(Series, Observation.series_id == Series.id)
            .where(Series.slug.in_(favorite_slugs))
            .order_by(Revision.detected_at.desc())
        ).all()
        for revision, observation, series in revision_rows:
            if series.slug not in revisions_by_slug:
                revisions_by_slug[series.slug] = {
                    "period": observation.period,
                    "old_value": float(revision.old_value),
                    "new_value": float(revision.new_value),
                }

    local_alerts = build_local_alerts(
        favorite_slugs,
        latest_by_slug,
        snapshot_by_slug,
        revisions_by_slug,
        preferences["alert_types"],
        {slug: CATALOG[slug].name for slug in PUBLIC_SLUGS},
    )
    read_alert_ids = set(preferences["read_alert_ids"])
    unread_alerts = [alert for alert in local_alerts if alert["id"] not in read_alert_ids]
    st.subheader("Centro de alertas")
    alert_metrics = st.columns(3)
    alert_metrics[0].metric("Nuevas", len(unread_alerts))
    alert_metrics[1].metric("Prioridad alta", sum(alert["severity"] == "high" for alert in unread_alerts))
    alert_metrics[2].metric("Total local", len(local_alerts))
    alert_controls = st.columns([1, 2])
    show_read_alerts = alert_controls[0].checkbox("Mostrar alertas leídas", value=False)
    if unread_alerts and alert_controls[1].button("Marcar todas como leídas"):
        preferences = persist_preferences(
            {**preferences, "read_alert_ids": sorted(read_alert_ids | {alert["id"] for alert in unread_alerts})},
        )
        st.rerun()
    visible_alerts = local_alerts if show_read_alerts else unread_alerts
    if not visible_alerts:
        st.success("No hay alertas nuevas para tus indicadores favoritos.")
    else:
        alert_icons = {"high": "🔴", "medium": "🟡", "info": "🔵"}
        with st.expander(f"Ver {len(visible_alerts)} alertas", expanded=True):
            for alert in visible_alerts:
                state = " · Leída" if alert["id"] in read_alert_ids else ""
                st.markdown(f"{alert_icons[alert['severity']]} **{alert['title']}**{state}")
                st.caption(alert["message"])
    st.caption(
        f"Preferencia: frecuencia {preferences['alert_frequency'].lower()}. "
        "El centro es local; todavía no envía correos ni notificaciones móviles."
    )

    with st.expander("Resumen ejecutivo automático", expanded=True):
        for summary_line in build_executive_summary(snapshot_by_slug):
            st.markdown(f"- {summary_line}")
        st.caption("Resumen descriptivo: no constituye predicción, recomendación ni prueba de causalidad.")
    st.download_button(
        "Descargar Panorama Económico de los 12 indicadores (.txt)",
        ("\ufeff" + economic_snapshot).encode("utf-8"),
        file_name=f"FQ_panorama_economico_{date.today().isoformat()}.txt",
        mime="text/plain; charset=utf-8",
        width="stretch",
    )

    for group_name, slugs in INDICATOR_GROUPS.items():
        st.subheader(group_name)
        cards = st.columns(4)
        for card, slug in zip(cards, slugs, strict=True):
            item = CATALOG[slug]
            with card.container(border=True):
                try:
                    latest = latest_by_slug[slug]
                    card_title = CARD_TITLES.get(slug, item.name)
                    st.metric(card_title, format_value(latest["value"], item.unit))
                    st.caption(item.unit)
                    short_source = CARD_SOURCE_LABELS.get(item.source, item.source)
                    st.caption(f"Actualizado: {format_period(latest['period'])} · {short_source}")
                    freshness = status_by_slug.get(slug, {})
                    status_icon = STATUS_ICONS.get(freshness.get("status"), "⚪")
                    st.caption(f"{status_icon} {freshness.get('label', 'Estado no disponible')}")
                except Exception:
                    st.metric(CARD_TITLES.get(slug, item.name), "Sin datos")
                    st.caption(f"Fuente prevista: {item.source}")

    st.divider()
    selected = st.selectbox(
        "Explorar indicador",
        PUBLIC_SLUGS,
        index=PUBLIC_SLUGS.index(preferences["default_indicator"]),
        format_func=lambda slug: CATALOG[slug].name,
    )
    item = CATALOG[selected]
    data = api_get(f"/api/v1/series/{selected}/observations?limit=5000")
    if data:
        frame = pd.DataFrame(data)
        frame["period"] = pd.to_datetime(frame["period"])
        indicator_table = pd.DataFrame(
            {
                "Fecha": frame["period"].dt.strftime("%d/%m/%Y"),
                "Valor": frame["value"],
                "Unidad": item.unit,
                "Indicador": item.name,
                "Fuente": item.source,
            }
        )
        observation_frequency = getattr(item, "observation_frequency", None)
        analysis_frequency = observation_frequency or item.frequency
        analysis = analyze_series(data, analysis_frequency, item.unit)
        intelligence_columns = st.columns(4)
        intelligence_columns[0].metric(
            "Último dato",
            format_value(analysis["latest_value"], item.unit),
        )
        intelligence_columns[0].caption(format_period(analysis["latest_period"]))
        if analysis["latest_period"] > date.today():
            intelligence_columns[0].caption("Fecha de cierre del periodo; el valor más reciente puede ser provisional.")
        intelligence_columns[1].metric("Cambio reciente", format_change(analysis))
        if analysis["previous_period"]:
            intelligence_columns[1].caption(f"Frente a {format_period(analysis['previous_period'])}")
        intelligence_columns[2].metric("Cambio interanual", format_change(analysis, annual=True))
        if analysis["annual_reference_period"]:
            intelligence_columns[2].caption(f"Frente a {format_period(analysis['annual_reference_period'])}")
        intelligence_columns[3].metric("Tendencia reciente", analysis["trend"])
        intelligence_columns[3].caption(f"Últimas {analysis['trend_observations']} observaciones")
        st.info(explain_analysis(item.name, analysis))
        extreme_change = analysis.get("extreme_change")
        if extreme_change is None and analysis.get("recent_change") is not None:
            extreme_change = (
                abs(analysis["recent_change"]) >= 5
                if analysis["is_rate"]
                else bool(analysis.get("recent_percent") is not None and abs(analysis["recent_percent"]) >= 100)
            )
        if extreme_change:
            st.warning(
                "La variación frente al periodo anterior es excepcional. Conviene revisar notas metodológicas, "
                "carácter preliminar y posibles revisiones antes de interpretarla."
            )
        st.caption("Lectura descriptiva automática; no constituye una predicción ni una recomendación.")
        fq_reading = build_fq_reading(selected, item.name, analysis, item.caveat)
        with st.expander(
            "Lectura FranQuestions: qué sabemos y qué falta verificar",
            expanded=preferences["detail_level"] == "Completo",
        ):
            st.markdown(f"**Hecho comprobado**  \n{fq_reading['fact']}")
            st.markdown(f"**Qué puede significar**  \n{fq_reading['meaning']}")
            st.markdown("**Hipótesis que deben investigarse**")
            for hypothesis in fq_reading["hypotheses"]:
                st.markdown(f"- {hypothesis.capitalize()}.")
            st.markdown("**Preguntas de verificación**")
            for question in fq_reading["questions"]:
                st.markdown(f"- {question}")
            st.warning(fq_reading["caveat"])
        with st.expander("Señales relacionadas: contraste entre indicadores", expanded=False):
            st.caption("Estas relaciones orientan la investigación. Que dos señales se muevan juntas no demuestra que una cause la otra.")
            related_specs = related_indicator_specs(selected)
            related_columns = st.columns(len(related_specs)) if related_specs else []
            related_brief_rows = []
            for column, (related_slug, reason) in zip(related_columns, related_specs):
                related_item = CATALOG[related_slug]
                related_data = api_get(f"/api/v1/series/{related_slug}/observations?limit=5000")
                with column:
                    st.markdown(f"**{related_item.name}**")
                    if related_data:
                        related_frequency = getattr(related_item, "observation_frequency", None) or related_item.frequency
                        related_analysis = analyze_series(related_data, related_frequency, related_item.unit)
                        related_brief_rows.append(
                            {
                                "name": related_item.name,
                                "value": format_value(related_analysis["latest_value"], related_item.unit),
                                "trend": related_analysis["trend"],
                                "period": format_period(related_analysis["latest_period"]),
                                "reason": reason,
                                "provisional": related_analysis["latest_period"] > date.today(),
                            }
                        )
                        st.metric(
                            "Último dato",
                            format_value(related_analysis["latest_value"], related_item.unit),
                            related_analysis["trend"],
                            delta_color="off",
                        )
                        st.caption(f"{format_period(related_analysis['latest_period'])} · {reason.capitalize()}.")
                        if related_analysis["latest_period"] > date.today():
                            st.caption("Fecha de cierre del período; dato provisional.")
                    else:
                        st.write("Sin datos disponibles")
        research_brief = build_research_brief(
            selected,
            item.name,
            analysis,
            fq_reading,
            related_brief_rows,
            item.source,
            item.source_url,
            item.unit,
        )
        st.download_button(
            "Descargar ficha de investigación (.txt)",
            ("\ufeff" + research_brief).encode("utf-8"),
            file_name=f"FQ_ficha_{selected}_{analysis['latest_period'].isoformat()}.txt",
            mime="text/plain; charset=utf-8",
            width="stretch",
        )
        indicator_downloads = st.columns(2)
        indicator_downloads[0].download_button(
            "Descargar serie para Excel (.xlsx)",
            dataframe_to_excel(indicator_table),
            file_name=f"FQ_serie_{selected}_{analysis['latest_period'].isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )
        indicator_downloads[1].download_button(
            "Descargar serie compatible (.csv)",
            ("\ufeff" + indicator_table.to_csv(index=False, sep=";")).encode("utf-8"),
            file_name=f"FQ_serie_{selected}_{analysis['latest_period'].isoformat()}.csv",
            mime="text/csv; charset=utf-8",
            width="stretch",
        )
        fig = px.line(
            frame,
            x="period",
            y="value",
            markers=len(frame) <= 200,
            labels={"period": "Fecha", "value": item.unit},
        )
        fig.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        fig.update_xaxes(range=[frame["period"].min(), frame["period"].max()])
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Todavía no hay observaciones cargadas para esta serie.")

    with st.container(border=True):
        st.subheader(item.name)
        st.write(item.description)
        st.write(f"**Por qué importa:** {item.why_it_matters}")
        frequency = FREQUENCY_LABELS.get(item.frequency, item.frequency)
        observation_frequency = getattr(item, "observation_frequency", None)
        if observation_frequency and observation_frequency != item.frequency:
            observation_frequency_label = FREQUENCY_LABELS.get(observation_frequency, observation_frequency)
            st.write(
                f"**Publicación:** {frequency} · **Observaciones:** {observation_frequency_label} · **Unidad:** {item.unit}"
            )
        else:
            st.write(f"**Frecuencia:** {frequency} · **Unidad:** {item.unit}")
        st.write(f"**Fuente oficial:** [{item.source}]({item.source_url})")
        if item.caveat:
            st.warning(item.caveat)
        st.caption("Revise siempre la fecha, unidad, fuente y notas metodológicas antes de citar el indicador.")
except httpx.HTTPError:
    st.error("No se pudo conectar con la API. Inicie FastAPI y confirme FQ_API_URL.")
