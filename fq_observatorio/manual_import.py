import logging
import re
from dataclasses import asdict, dataclass
from calendar import monthrange
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Alert, IngestionRun, Observation, Revision, Series
from .validation import validate_series

logger = logging.getLogger(__name__)


@dataclass
class ImportReport:
    run_id: int
    status: str
    rows_received: int
    inserted: int
    revised: int
    unchanged: int
    issues: list[dict]


def read_official_file(
    path: str | Path,
    date_column: str,
    value_column: str,
    sheet_name: str | int = 0,
    header_row: int = 1,
) -> list[dict]:
    """Lee un CSV o Excel descargado sin modificar el archivo de origen."""
    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {source_path}")
    header_index = header_row - 1
    if source_path.suffix.lower() == ".csv":
        frame = pd.read_csv(source_path, header=header_index)
    elif source_path.suffix.lower() in {".xlsx", ".xls"}:
        normalized_sheet = int(sheet_name) if isinstance(sheet_name, str) and sheet_name.isdigit() else sheet_name
        frame = pd.read_excel(source_path, sheet_name=normalized_sheet, header=header_index)
    else:
        raise ValueError("Formato no admitido; use CSV, XLSX o XLS")
    missing = {date_column, value_column} - set(frame.columns)
    if missing:
        raise ValueError(f"Columnas ausentes: {', '.join(sorted(missing))}")
    rows = []
    for _, raw in frame[[date_column, value_column]].iterrows():
        period = pd.to_datetime(raw[date_column], errors="coerce")
        value = raw[value_column]
        try:
            parsed_value = None if pd.isna(value) else Decimal(str(value).replace(" ", "").replace(",", ""))
        except InvalidOperation:
            parsed_value = None
        rows.append({"period": None if pd.isna(period) else period.date(), "value": parsed_value})
    return rows


def read_inec_moving_quarter_file(
    path: str | Path,
    sheet_name: str,
    period_row: int,
    value_row: int,
) -> list[dict]:
    """Lee cuadros horizontales de la ECE y fecha cada trimestre movil por su mes final."""
    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {source_path}")
    frame = pd.read_excel(source_path, sheet_name=sheet_name, header=None)
    periods = frame.iloc[period_row - 1, 1:]
    values = frame.iloc[value_row - 1, 1:]
    end_month = {
        "EFM": 3, "FMA": 4, "MAM": 5, "AMJ": 6, "MJJ": 7, "JJA": 8,
        "JAS": 9, "ASO": 10, "SON": 11, "OND": 12, "NDE": 1, "DEF": 2,
    }
    rows = []
    for raw_period, raw_value in zip(periods, values):
        if pd.isna(raw_period) and pd.isna(raw_value):
            continue
        parts = str(raw_period).strip().upper().split()
        period = None
        if len(parts) == 2 and parts[0] in end_month and parts[1].isdigit():
            year = int(parts[1]) + (1 if parts[0] in {"NDE", "DEF"} else 0)
            month = end_month[parts[0]]
            period = date(year, month, monthrange(year, month)[1])
        try:
            value = None if pd.isna(raw_value) else Decimal(str(raw_value))
        except InvalidOperation:
            value = None
        rows.append({"period": period, "value": value})
    return rows


def read_inec_annual_label_file(
    path: str | Path,
    sheet_name: str,
    header_row: int,
    label_column: str,
    value_column: str,
    label_prefix: str,
    month: int = 7,
) -> list[dict]:
    """Lee series anuales del INEC cuyo anio forma parte de una etiqueta de fila."""
    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {source_path}")
    frame = pd.read_excel(source_path, sheet_name=sheet_name, header=header_row - 1)
    missing = {label_column, value_column} - set(frame.columns)
    if missing:
        raise ValueError(f"Columnas ausentes: {', '.join(sorted(missing))}")
    rows = []
    for _, raw in frame[[label_column, value_column]].iterrows():
        label = str(raw[label_column]).strip()
        if not label.startswith(label_prefix):
            continue
        year_text = label.removeprefix(label_prefix).strip()
        period = None
        if year_text.isdigit():
            year = int(year_text)
            period = date(year, month, monthrange(year, month)[1])
        try:
            value = None if pd.isna(raw[value_column]) else Decimal(str(raw[value_column]))
        except InvalidOperation:
            value = None
        rows.append({"period": period, "value": value})
    return rows


def read_horizontal_annual_file(
    path: str | Path,
    sheet_name: str,
    year_row: int,
    value_row: int,
    scale: Decimal = Decimal("1"),
) -> list[dict]:
    """Lee una serie anual horizontal y conserva solo encabezados que sean anios."""
    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {source_path}")
    frame = pd.read_excel(source_path, sheet_name=sheet_name, header=None)
    years = frame.iloc[year_row - 1, :]
    values = frame.iloc[value_row - 1, :]
    rows = []
    for raw_year, raw_value in zip(years, values):
        try:
            year = int(raw_year)
        except (TypeError, ValueError):
            continue
        if year < 1900 or year > 2200:
            continue
        try:
            value = None if pd.isna(raw_value) else Decimal(str(raw_value)) * scale
        except InvalidOperation:
            value = None
        rows.append({"period": date(year, 12, 31), "value": value})
    return rows


def read_bccr_html_monthly_file(path: str | Path) -> list[dict]:
    """Lee el .xls HTML que exportan los cuadros historicos del BCCR.

    El cuadro coloca los anios en columnas y los meses en filas. La fecha de
    cada observacion se normaliza al ultimo dia del mes y se omite la fila
    ``Total`` para conservar valores mensuales, no acumulados.
    """
    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {source_path}")
    tables = pd.read_html(source_path, encoding="windows-1252", decimal=",", thousands=".")
    if not tables:
        raise ValueError("El archivo del BCCR no contiene tablas")
    frame = tables[0]
    year_row = None
    for row_index in range(min(len(frame), 12)):
        valid_years = 0
        for raw in frame.iloc[row_index, 1:]:
            try:
                year = int(raw)
            except (TypeError, ValueError):
                continue
            if 1900 <= year <= 2200:
                valid_years += 1
        if valid_years >= 2:
            year_row = row_index
            break
    if year_row is None:
        raise ValueError("No se encontro la fila de anios en el archivo del BCCR")

    months = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    }
    rows = []
    for row_index in range(year_row + 1, len(frame)):
        label = str(frame.iloc[row_index, 0]).strip().lower()
        if label not in months:
            continue
        month = months[label]
        for column in range(1, len(frame.columns)):
            try:
                year = int(frame.iloc[year_row, column])
            except (TypeError, ValueError):
                continue
            raw_value = frame.iloc[row_index, column]
            try:
                value = None if pd.isna(raw_value) else Decimal(str(raw_value))
            except InvalidOperation:
                value = None
            if value is not None:
                rows.append({
                    "period": date(year, month, monthrange(year, month)[1]),
                    "value": value,
                })
    return sorted(rows, key=lambda row: row["period"])


def read_bccr_html_quarterly_file(path: str | Path, row_label: str) -> list[dict]:
    """Lee una fila trimestral de los archivos .xls HTML exportados por el BCCR."""
    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {source_path}")
    tables = pd.read_html(source_path, encoding="windows-1252", decimal=",", thousands=".")
    if not tables:
        raise ValueError("El archivo del BCCR no contiene tablas")
    frame = tables[0]
    header_row = None
    pattern = re.compile(r"trimestre\s+([1-4])/(20\d{2})", re.IGNORECASE)
    for row_index in range(min(len(frame), 12)):
        if sum(bool(pattern.fullmatch(str(raw).strip())) for raw in frame.iloc[row_index, 1:]) >= 2:
            header_row = row_index
            break
    if header_row is None:
        raise ValueError("No se encontro el encabezado trimestral del BCCR")
    target_row = None
    normalized_label = " ".join(row_label.split()).casefold()
    for row_index in range(header_row + 1, len(frame)):
        candidate = " ".join(str(frame.iloc[row_index, 0]).split()).casefold()
        if candidate == normalized_label:
            target_row = row_index
            break
    if target_row is None:
        raise ValueError(f"No se encontro la fila: {row_label}")
    rows = []
    for column in range(1, len(frame.columns)):
        match = pattern.fullmatch(str(frame.iloc[header_row, column]).strip())
        if not match:
            continue
        quarter, year = int(match.group(1)), int(match.group(2))
        month = quarter * 3
        raw_value = frame.iloc[target_row, column]
        try:
            value = None if pd.isna(raw_value) else Decimal(str(raw_value))
        except InvalidOperation:
            value = None
        if value is not None:
            rows.append({
                "period": date(year, month, monthrange(year, month)[1]),
                "value": value,
            })
    return sorted(rows, key=lambda row: row["period"])


def parse_ict_monthly_text(text: str) -> list[dict]:
    """Convierte el Cuadro 11 del ICT en observaciones mensuales."""
    section = text.split("Cuadro 12", 1)[0]
    years_match = re.search(r"Mes\s+((?:20\d{2}\s+)+20\d{2})", section)
    if not years_match:
        raise ValueError("No se encontro el encabezado de anios del Cuadro 11")
    years = [int(value) for value in re.findall(r"20\d{2}", years_match.group(1))]
    months = {
        "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4,
        "Mayo": 5, "Junio": 6, "Julio": 7, "Agosto": 8,
        "Setiembre": 9, "Septiembre": 9, "Octubre": 10,
        "Noviembre": 11, "Diciembre": 12,
    }
    rows = []
    for line in section.splitlines():
        label = next((name for name in months if line.startswith(name + " ")), None)
        if not label:
            continue
        groups = re.findall(r"\d+", line[len(label):])
        if len(groups) % 2:
            raise ValueError(f"Valores ambiguos en la fila {label}")
        values = [Decimal(groups[index] + groups[index + 1]) for index in range(0, len(groups), 2)]
        if len(values) > len(years):
            raise ValueError(f"Demasiados valores en la fila {label}")
        month = months[label]
        for year, value in zip(years, values):
            rows.append({
                "period": date(year, month, monthrange(year, month)[1]),
                "value": value,
            })
    if not rows:
        raise ValueError("No se encontraron observaciones mensuales en el Cuadro 11")
    return sorted(rows, key=lambda row: row["period"])


def read_ict_monthly_pdf(path: str | Path, page_number: int = 12) -> list[dict]:
    """Lee llegadas internacionales mensuales por todas las vias del ICT."""
    import pdfplumber

    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {source_path}")
    with pdfplumber.open(source_path) as pdf:
        if page_number < 1 or page_number > len(pdf.pages):
            raise ValueError(f"Pagina fuera de rango: {page_number}")
        text = pdf.pages[page_number - 1].extract_text() or ""
    return parse_ict_monthly_text(text)


def read_debt_to_gdp_files(
    debt_path: str | Path,
    debt_sheet: str,
    debt_date_row: int,
    internal_row: int,
    external_row: int,
    gdp_path: str | Path,
    gdp_sheet: str,
    gdp_year_row: int,
    gdp_value_row: int,
) -> list[dict]:
    """Calcula deuda/PIB con saldos y PIB oficiales expresados en millones de colones."""
    debt_frame = pd.read_excel(debt_path, sheet_name=debt_sheet, header=None)
    gdp_frame = pd.read_excel(gdp_path, sheet_name=gdp_sheet, header=None)
    gdp_by_year: dict[int, Decimal] = {}
    for raw_year, raw_gdp in zip(gdp_frame.iloc[gdp_year_row - 1, :], gdp_frame.iloc[gdp_value_row - 1, :]):
        try:
            year = int(raw_year)
            gdp = Decimal(str(raw_gdp))
        except (TypeError, ValueError, InvalidOperation):
            continue
        if 1900 <= year <= 2200 and gdp > 0:
            gdp_by_year[year] = gdp

    rows = []
    for raw_date, raw_internal, raw_external in zip(
        debt_frame.iloc[debt_date_row - 1, :],
        debt_frame.iloc[internal_row - 1, :],
        debt_frame.iloc[external_row - 1, :],
    ):
        if isinstance(raw_date, (int, float)):
            parsed = pd.to_datetime(raw_date, unit="D", origin="1899-12-30", errors="coerce")
        else:
            parsed = pd.to_datetime(raw_date, errors="coerce")
        if pd.isna(parsed):
            continue
        year = int(parsed.year)
        if year not in gdp_by_year:
            continue
        try:
            total_debt = Decimal(str(raw_internal)) + Decimal(str(raw_external))
        except (TypeError, InvalidOperation):
            total_debt = None
        value = None if total_debt is None else total_debt / gdp_by_year[year] * Decimal("100")
        rows.append({"period": date(year, 12, 31), "value": value})
    return rows


def import_rows(session: Session, slug: str, rows: list[dict]) -> ImportReport:
    """Valida y aplica una importacion con historial de revisiones y alertas."""
    series = session.scalar(select(Series).where(Series.slug == slug))
    if not series:
        raise ValueError(f"Serie desconocida: {slug}. Inicialice primero el catalogo.")
    run = IngestionRun(source_id=series.source_id, status="running")
    session.add(run)
    session.flush()
    issues = validate_series(rows, series.frequency)
    errors = [issue for issue in issues if issue.severity == "error"]
    for issue in issues:
        session.add(Alert(series_id=series.id, alert_type=issue.kind, severity=issue.severity, message=issue.message, period=issue.period))
    inserted = revised = unchanged = 0
    try:
        if errors:
            run.status = "rejected"
            run.rows_received = len(rows)
            run.error_message = f"{len(errors)} errores de validacion"
        else:
            for row in rows:
                current = session.scalar(select(Observation).where(Observation.series_id == series.id, Observation.period == row["period"]))
                if current is None:
                    session.add(Observation(series_id=series.id, **row))
                    inserted += 1
                elif current.value != row["value"]:
                    session.add(Revision(observation_id=current.id, old_value=current.value, new_value=row["value"]))
                    current.value = row["value"]
                    revised += 1
                else:
                    unchanged += 1
            run.status = "success"
            run.rows_received = len(rows)
            run.rows_written = inserted + revised
        run.finished_at = datetime.now(timezone.utc)
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.exception("Fallo la importacion manual", extra={"slug": slug})
        raise RuntimeError(f"La importacion no pudo completarse: {exc}") from exc
    return ImportReport(run.id, run.status, len(rows), inserted, revised, unchanged, [asdict(issue) for issue in issues])
