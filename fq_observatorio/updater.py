"""Interfaz local para actualizar series desde archivos oficiales."""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
import streamlit as st

from fq_observatorio.catalog import CATALOG
from fq_observatorio.backup import backup_sqlite_database, restore_sqlite_database
from fq_observatorio.connection_checks import check_bccr_connection
from fq_observatorio.exchange_rate_job import (
    build_exchange_rate_plan,
    execute_exchange_rate_update,
)
from fq_observatorio.config import get_settings
from fq_observatorio.db import Base, SessionLocal, engine
from fq_observatorio.manual_import import (
    compare_rows,
    import_rows,
    read_bccr_html_monthly_file,
    read_bccr_html_quarterly_file,
    read_debt_to_gdp_files,
    read_horizontal_annual_file,
    read_ict_monthly_pdf,
    read_inec_annual_label_file,
    read_inec_moving_quarter_file,
    read_official_file,
)
from fq_observatorio.ingestion_history import recent_runs, status_counts
from fq_observatorio.seed import seed_catalog
from fq_observatorio.update_plans import build_all_update_plans
from fq_observatorio.validation import validate_series


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ARCHIVE = ROOT / "Fuentes oficiales" / "Actualizaciones"
BACKUP_DIR = ROOT / "backups"
RECOVERY_BACKUP_DIR = BACKUP_DIR / "before_restore"
LEGACY_BACKUP_DIRS = (
    ROOT.parents[1] / "FranQuestions_Observatorio_v1.1.0" / "backups",
)

PRESETS = {
    "exchange-rate": {
        "extensions": ["xlsx"],
        "help": "Archivo del BCCR de tipo de cambio, exportado en formato vertical.",
    },
    "policy-rate": {
        "extensions": ["xlsx"],
        "help": "Archivo del BCCR de Tasa de Política Monetaria.",
    },
    "inflation": {
        "extensions": ["xlsx"],
        "help": "Archivo del IPC interanual distribuido por BCCR/INEC.",
    },
    "imae": {
        "extensions": ["xlsx"],
        "help": "Archivo del IMAE tendencia-ciclo, variación interanual.",
    },
    "reserves": {
        "extensions": ["xlsx"],
        "help": "Archivo de activos de reserva del Banco Central.",
    },
    "unemployment": {
        "extensions": ["xlsx"],
        "help": "Cuadros históricos de la ECE con la hoja «C1 total ».",
    },
    "poverty": {
        "extensions": ["xlsx"],
        "help": "Serie de pobreza ENAHO con la hoja «Cuadro 1».",
    },
    "fiscal-balance": {
        "extensions": ["xlsx"],
        "help": "Cifras fiscales de diciembre, hoja «ACUMULADO».",
    },
    "public-debt": {
        "extensions": ["xlsx"],
        "help": "Requiere el histórico de deuda y el archivo fiscal de diciembre usado para el PIB.",
    },
    "exports": {
        "extensions": ["xls"],
        "help": "Exportación HTML/XLS del cuadro 28 del BCCR.",
    },
    "tourism": {
        "extensions": ["pdf"],
        "help": "Informe mensual del ICT que contiene el Cuadro 11.",
    },
    "fdi": {
        "extensions": ["xls"],
        "help": "Exportación HTML/XLS del cuadro 2723 del BCCR.",
    },
}


def save_upload(upload, suffix: str | None = None) -> Path:
    extension = suffix or Path(upload.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as handle:
        handle.write(upload.getvalue())
        return Path(handle.name)


def parse_upload(slug: str, main_path: Path, second_path: Path | None = None) -> list[dict]:
    if slug == "exchange-rate":
        return read_official_file(main_path, "Fecha", "Tipo cambio venta", 0, 5)
    if slug == "policy-rate":
        return read_official_file(main_path, "Fecha", "Tasa política monetaria", 0, 5)
    if slug == "inflation":
        return read_official_file(main_path, "Fecha", "IPC, variación interanual (%)", 0, 5)
    if slug == "imae":
        return read_official_file(main_path, "Fecha", "IMAE, variación interanual (%)", 0, 5)
    if slug == "reserves":
        return read_official_file(main_path, "Fecha", "Reservas brutas del Banco Central", 0, 5)
    if slug == "unemployment":
        return read_inec_moving_quarter_file(main_path, "C1 total ", 4, 110)
    if slug == "poverty":
        return read_inec_annual_label_file(
            main_path,
            "Cuadro 1",
            3,
            "Región de planificación y año",
            "Total pobreza no extrema y pobreza extrema",
            "Total país",
            7,
        )
    if slug == "fiscal-balance":
        return read_horizontal_annual_file(main_path, "ACUMULADO", 7, 72, Decimal("100"))
    if slug == "public-debt":
        if second_path is None:
            raise ValueError("Falta el archivo fiscal de diciembre para obtener el PIB")
        return read_debt_to_gdp_files(
            main_path, "Hoja1", 6, 8, 12, second_path, "ACUMULADO", 7, 78
        )
    if slug == "exports":
        return read_bccr_html_monthly_file(main_path)
    if slug == "tourism":
        return read_ict_monthly_pdf(main_path, 12)
    if slug == "fdi":
        return read_bccr_html_quarterly_file(
            main_path, "Total Inversion directa en la economia declarante"
        )
    raise ValueError(f"No existe una plantilla de actualización para {slug}")


def archive_upload(upload, slug: str) -> Path:
    target_dir = SOURCE_ARCHIVE / slug
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(upload.name).name
    target = target_dir / f"{datetime.now():%Y%m%d_%H%M%S}_{safe_name}"
    with target.open("wb") as handle:
        shutil.copyfileobj(upload, handle)
    upload.seek(0)
    return target


def available_backups() -> list[Path]:
    """Devuelve solo respaldos SQLite creados por FranQuestions."""
    backup_dirs = (BACKUP_DIR, *LEGACY_BACKUP_DIRS)
    candidates: dict[Path, Path] = {}
    for backup_dir in backup_dirs:
        if not backup_dir.is_dir():
            continue
        for path in backup_dir.glob("franquestions_*.db"):
            if path.is_file():
                candidates[path.resolve()] = path
    return sorted(
        candidates.values(),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def backup_label(path: Path) -> str:
    modified = datetime.fromtimestamp(path.stat().st_mtime)
    size_mb = path.stat().st_size / (1024 * 1024)
    return f"{modified:%d/%m/%Y %H:%M:%S} · {size_mb:.2f} MB · {path.name}"


@st.dialog("Restaurar un respaldo local")
def recovery_dialog() -> None:
    st.warning(
        "Esta operación reemplaza la base local vigente. Antes de hacerlo, "
        "FranQuestions creará automáticamente una copia de emergencia."
    )
    backups = available_backups()
    if not backups:
        st.info("Todavía no hay respaldos disponibles para restaurar.")
        return

    selected_backup = st.selectbox(
        "Respaldo que desea restaurar",
        options=backups,
        format_func=backup_label,
        key="recovery-backup-selection",
    )
    st.caption(f"Archivo seleccionado: {selected_backup.name}")
    confirmed = st.checkbox(
        "Entiendo que se reemplazará la base local vigente.",
        key="recovery-risk-confirmation",
    )
    confirmation_text = st.text_input(
        "Para confirmar, escriba RESTAURAR",
        key="recovery-confirmation-text",
    )
    ready = confirmed and confirmation_text.strip() == "RESTAURAR"
    if st.button(
        "Restaurar respaldo",
        type="primary",
        disabled=not ready,
        key="restore-selected-backup",
    ):
        try:
            engine.dispose()
            safety_backup = restore_sqlite_database(
                get_settings().database_url,
                selected_backup,
                root=ROOT,
                safety_backup_dir=RECOVERY_BACKUP_DIR,
            )
            engine.dispose()
        except Exception as exc:
            st.error(f"No se pudo restaurar el respaldo: {exc}")
        else:
            st.cache_data.clear()
            safety_name = safety_backup.name if safety_backup else "respaldo externo"
            st.session_state["recovery-success"] = (
                f"Restauración completada. Copia de emergencia conservada: {safety_name}."
            )
            st.rerun()


st.set_page_config(page_title="Actualizar FranQuestions", page_icon="🔄", layout="wide")
st.title("Actualizar indicadores de FranQuestions")
st.markdown("[← Volver al Observatorio](http://127.0.0.1:8501)")
st.caption("Herramienta local con vista previa, validación, respaldo y registro de revisiones.")
st.warning(
    "Use únicamente archivos descargados de las fuentes oficiales. "
    "Ningún dato se incorpora hasta pulsar el botón final de confirmación."
)

if recovery_message := st.session_state.pop("recovery-success", None):
    st.success(recovery_message)

with st.expander("Historial y control de actualizaciones"):
    st.markdown("#### Comprobar acceso al BCCR")
    st.caption(
        "La prueba consulta una muestra corta del tipo de cambio. "
        "No incorpora ni modifica observaciones."
    )
    if st.button("Probar conexion con el BCCR", key="check-bccr"):
        with st.spinner("Comprobando configuracion y respuesta del BCCR..."):
            connection_result = check_bccr_connection()
        if connection_result.ok:
            st.success(connection_result.message)
            st.caption(
                f"Observaciones leidas: {connection_result.observations}. "
                f"Ultimo periodo recibido: {connection_result.latest_period}."
            )
        elif not connection_result.configured:
            st.warning(
                "Las credenciales del BCCR todavia no estan configuradas. "
                "La herramienta seguira disponible para cuando sean entregadas."
            )
        else:
            st.error(connection_result.message)

    st.markdown("#### Actualizacion controlada del tipo de cambio")
    with SessionLocal() as plan_session:
        exchange_plan = build_exchange_rate_plan(plan_session)
    st.caption(
        f"Periodo previsto: {exchange_plan.start:%d/%m/%Y} a "
        f"{exchange_plan.end:%d/%m/%Y}. Incluye "
        f"{exchange_plan.overlap_days} dias para detectar revisiones."
    )
    current_settings = get_settings()
    bccr_ready = all(
        (
            current_settings.bccr_name,
            current_settings.bccr_email,
            current_settings.bccr_token,
        )
    )
    if not bccr_ready:
        st.info(
            "La actualizacion permanecera bloqueada hasta configurar las "
            "credenciales entregadas por el BCCR."
        )
    apply_confirmed = st.checkbox(
        "Confirmo que deseo crear un respaldo y aplicar solo datos validados.",
        key="confirm-auto-exchange",
        disabled=not bccr_ready,
    )
    if st.button(
        "Actualizar tipo de cambio desde el BCCR",
        key="apply-auto-exchange",
        type="primary",
        disabled=not (bccr_ready and apply_confirmed),
    ):
        with st.spinner("Creando respaldo y consultando el BCCR..."):
            try:
                with SessionLocal() as update_session:
                    update_result = execute_exchange_rate_update(update_session)
            except Exception as exc:
                st.error(f"La actualizacion no pudo completarse: {exc}")
            else:
                report = update_result["report"]
                st.success(
                    "Actualizacion terminada: "
                    f"{report['inserted']} nuevos, {report['revised']} revisados "
                    f"y {report['unchanged']} sin cambios."
                )
                if update_result["backup"]:
                    st.caption(f"Respaldo previo: {update_result['backup']}")
                st.cache_data.clear()

    st.markdown("#### Historial de ejecuciones")
    with SessionLocal() as history_session:
        counts = status_counts(history_session)
        history = recent_runs(history_session, limit=50)
    metric_columns = st.columns(4)
    metric_columns[0].metric("Exitosas", counts.get("success", 0))
    metric_columns[1].metric("Rechazadas", counts.get("rejected", 0))
    metric_columns[2].metric("Fallidas", counts.get("failed", 0))
    metric_columns[3].metric("En curso", counts.get("running", 0))
    if history:
        history_frame = pd.DataFrame(history).rename(
            columns={
                "run_id": "Ejecucion",
                "source": "Fuente",
                "status": "Estado",
                "started_at": "Inicio",
                "finished_at": "Fin",
                "rows_received": "Filas recibidas",
                "rows_written": "Filas escritas",
                "error_message": "Detalle",
            }
        )
        st.dataframe(history_frame, width="stretch", hide_index=True)
    else:
        st.info("Todavia no existen ejecuciones registradas.")

with st.expander("Recuperación y respaldos"):
    st.markdown("#### Recuperación protegida de la base local")
    st.caption(
        "Esta función existe únicamente en el actualizador local. "
        "No aparece en la aplicación pública y nunca restaura datos sin "
        "selección explícita y doble confirmación."
    )
    if message := st.session_state.pop("backup-success", None):
        st.success(message)

    backups = available_backups()
    backup_count = len(backups)
    st.write(f"Respaldos disponibles: **{backup_count}**")
    action_row = st.container(horizontal=True)
    with action_row:
        if st.button(
            "Crear respaldo ahora",
            icon=":material/backup:",
            key="create-current-backup",
        ):
            try:
                engine.dispose()
                backup_path = backup_sqlite_database(
                    get_settings().database_url,
                    root=ROOT,
                    backup_dir=BACKUP_DIR,
                )
            except Exception as exc:
                st.error(f"No se pudo crear el respaldo: {exc}")
            else:
                st.session_state["backup-success"] = (
                    f"Respaldo creado correctamente: {backup_path.name}."
                )
                st.rerun()

        if st.button(
            "Abrir recuperación protegida",
            icon=":material/settings_backup_restore:",
            disabled=backup_count == 0,
            key="open-recovery-dialog",
        ):
            recovery_dialog()

    if backups:
        latest_backup = backups[0]
        st.download_button(
            "Descargar respaldo más reciente",
            data=latest_backup.read_bytes(),
            file_name=latest_backup.name,
            mime="application/vnd.sqlite3",
            icon=":material/download:",
            key="download-latest-backup",
            help=(
                "Guarda una copia externa de la base. Descargarla no modifica "
                "ni restaura los datos del Observatorio."
            ),
        )
        st.caption(f"Copia disponible: {backup_label(latest_backup)}")

with st.expander("Plan de actualizacion de los 12 indicadores"):
    current_settings = get_settings()
    credentials_ready = all(
        (
            current_settings.bccr_name,
            current_settings.bccr_email,
            current_settings.bccr_token,
        )
    )
    with SessionLocal() as plans_session:
        update_plans = build_all_update_plans(
            plans_session,
            bccr_credentials_ready=credentials_ready,
        )
    plans_frame = pd.DataFrame([plan.as_dict() for plan in update_plans]).rename(
        columns={
            "indicator": "Indicador",
            "latest_stored": "Ultimo dato",
            "start": "Inicio de revision",
            "end": "Fin",
            "observation_frequency": "Frecuencia",
            "mechanism": "Mecanismo",
            "readiness": "Estado",
            "requirement": "Requisito",
            "writes_require_confirmation": "Confirmacion obligatoria",
        }
    )
    st.dataframe(
        plans_frame.drop(columns=["slug"]),
        hide_index=True,
    )
    st.caption(
        "Los periodos incluyen solapamiento para detectar revisiones. "
        "Ningun plan escribe datos sin validacion y confirmacion."
    )

slug = st.selectbox(
    "Indicador que desea actualizar",
    list(PRESETS),
    format_func=lambda value: CATALOG[value].name,
)
preset = PRESETS[slug]
st.info(preset["help"])
main_upload = st.file_uploader(
    "Archivo oficial",
    type=preset["extensions"],
    key=f"main-{slug}",
)
second_upload = None
if slug == "public-debt":
    second_upload = st.file_uploader(
        "Archivo fiscal de diciembre para el PIB",
        type=["xlsx"],
        key="gdp-file",
    )

if main_upload is not None and (slug != "public-debt" or second_upload is not None):
    temporary_paths: list[Path] = []
    try:
        main_path = save_upload(main_upload)
        temporary_paths.append(main_path)
        second_path = save_upload(second_upload) if second_upload is not None else None
        if second_path:
            temporary_paths.append(second_path)
        rows = parse_upload(slug, main_path, second_path)
        issues = validate_series(rows, CATALOG[slug].frequency)
        errors = [issue for issue in issues if issue.severity == "error"]
        warnings = [issue for issue in issues if issue.severity == "warning"]

        st.success(f"Vista previa generada: {len(rows):,} observaciones encontradas.")
        preview = pd.DataFrame(rows).dropna().sort_values("period", ascending=False).head(12)
        st.dataframe(preview, hide_index=True)

        if warnings:
            st.warning(f"Se detectaron {len(warnings)} advertencias que requieren revisión.")
            with st.expander("Ver advertencias"):
                for issue in warnings[:50]:
                    st.write(f"- {issue.period or 'Sin fecha'}: {issue.message}")
        if errors:
            st.error(f"El archivo contiene {len(errors)} errores y no puede importarse.")
        else:
            Base.metadata.create_all(engine)
            with SessionLocal() as session:
                seed_catalog(session)
                comparison = compare_rows(session, slug, rows)

            st.subheader("Comparación con la base vigente")
            metric_columns = st.columns(3)
            metric_columns[0].metric("Observaciones nuevas", len(comparison.new_rows))
            metric_columns[1].metric("Revisiones detectadas", len(comparison.revised_rows))
            metric_columns[2].metric("Sin cambios", comparison.unchanged)
            database_latest = comparison.database_latest.isoformat() if comparison.database_latest else "Sin datos"
            file_latest = comparison.file_latest.isoformat() if comparison.file_latest else "Sin datos"
            st.caption(
                f"Último periodo en la base: {database_latest} · "
                f"Último periodo en el archivo: {file_latest}"
            )

            changed_rows = [
                {"periodo": row["period"], "tipo": "Nueva", "valor actual": None, "valor del archivo": row["value"]}
                for row in comparison.new_rows
            ] + [
                {
                    "periodo": row["period"],
                    "tipo": "Revisada",
                    "valor actual": row["current_value"],
                    "valor del archivo": row["file_value"],
                }
                for row in comparison.revised_rows
            ]
            if changed_rows:
                st.warning(
                    f"El archivo contiene {comparison.changes} cambios que requieren revisión antes de incorporarse."
                )
                changes_frame = pd.DataFrame(changed_rows).sort_values("periodo", ascending=False)
                st.dataframe(changes_frame, hide_index=True)
            else:
                st.info("El archivo no aporta observaciones nuevas ni revisiones. No es necesario incorporarlo.")

            confirmed = st.checkbox(
                "Confirmo que revisé los cambios y que el archivo proviene de la fuente oficial.",
                disabled=comparison.changes == 0,
            )
            if st.button(
                "Incorporar actualización",
                type="primary",
                disabled=not confirmed or comparison.changes == 0,
            ):
                backup_path = backup_sqlite_database(
                    get_settings().database_url,
                    root=ROOT,
                    backup_dir=BACKUP_DIR,
                )
                archived_path = archive_upload(main_upload, slug)
                if second_upload is not None:
                    archive_upload(second_upload, f"{slug}-pib")
                Base.metadata.create_all(engine)
                with SessionLocal() as session:
                    seed_catalog(session)
                    report = import_rows(session, slug, rows)
                st.success(
                    f"Actualización terminada: {report.inserted} nuevos, "
                    f"{report.revised} revisados y {report.unchanged} sin cambios."
                )
                st.caption(f"Archivo conservado en: {archived_path.relative_to(ROOT)}")
                if backup_path:
                    st.caption(f"Respaldo previo: {backup_path.relative_to(ROOT)}")
                st.cache_data.clear()
    except Exception as exc:
        st.error(f"No se pudo interpretar el archivo: {exc}")
    finally:
        for temporary_path in temporary_paths:
            temporary_path.unlink(missing_ok=True)
else:
    st.caption("Seleccione el indicador y cargue el archivo requerido para generar la vista previa.")
