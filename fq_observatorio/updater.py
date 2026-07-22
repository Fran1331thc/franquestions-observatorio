"""Interfaz local para actualizar series desde archivos oficiales."""

from __future__ import annotations

import shutil
import sqlite3
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
import streamlit as st

from fq_observatorio.catalog import CATALOG
from fq_observatorio.config import get_settings
from fq_observatorio.db import Base, SessionLocal, engine
from fq_observatorio.manual_import import (
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
from fq_observatorio.seed import seed_catalog
from fq_observatorio.validation import validate_series


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ARCHIVE = ROOT / "Fuentes oficiales" / "Actualizaciones"
BACKUP_DIR = ROOT / "backups"

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


def backup_sqlite_database() -> Path | None:
    database_url = get_settings().database_url
    if not database_url.startswith("sqlite:///"):
        return None
    source = Path(database_url.removeprefix("sqlite:///"))
    if not source.is_absolute():
        source = ROOT / source
    BACKUP_DIR.mkdir(exist_ok=True)
    destination = BACKUP_DIR / f"franquestions_{datetime.now():%Y%m%d_%H%M%S}.db"
    with sqlite3.connect(source) as original, sqlite3.connect(destination) as backup:
        original.backup(backup)
    return destination


def archive_upload(upload, slug: str) -> Path:
    target_dir = SOURCE_ARCHIVE / slug
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(upload.name).name
    target = target_dir / f"{datetime.now():%Y%m%d_%H%M%S}_{safe_name}"
    with target.open("wb") as handle:
        shutil.copyfileobj(upload, handle)
    upload.seek(0)
    return target


st.set_page_config(page_title="Actualizar FranQuestions", page_icon="🔄", layout="wide")
st.title("Actualizar indicadores de FranQuestions")
st.markdown("[← Volver al Observatorio](http://127.0.0.1:8501)")
st.caption("Herramienta local con vista previa, validación, respaldo y registro de revisiones.")
st.warning(
    "Use únicamente archivos descargados de las fuentes oficiales. "
    "Ningún dato se incorpora hasta pulsar el botón final de confirmación."
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
        st.dataframe(preview, use_container_width=True, hide_index=True)

        if warnings:
            st.warning(f"Se detectaron {len(warnings)} advertencias que requieren revisión.")
            with st.expander("Ver advertencias"):
                for issue in warnings[:50]:
                    st.write(f"- {issue.period or 'Sin fecha'}: {issue.message}")
        if errors:
            st.error(f"El archivo contiene {len(errors)} errores y no puede importarse.")
        else:
            confirmed = st.checkbox(
                "Confirmo que revisé la vista previa y que el archivo proviene de la fuente oficial."
            )
            if st.button("Incorporar actualización", type="primary", disabled=not confirmed):
                backup_path = backup_sqlite_database()
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
