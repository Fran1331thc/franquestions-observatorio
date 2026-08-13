"""Auditoría reproducible de las doce series públicas de FranQuestions."""

from __future__ import annotations

import json
import math
import sqlite3
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from statistics import median

from fq_observatorio.catalog import CATALOG


EXPECTED_SERIES = {
    "exchange-rate": ("daily", "CRC por USD"),
    "policy-rate": ("daily", "% anual"),
    "inflation": ("monthly", "% interanual"),
    "imae": ("monthly", "% interanual"),
    "unemployment": ("monthly", "% de la fuerza de trabajo"),
    "poverty": ("annual", "% de hogares"),
    "fiscal-balance": ("annual", "% del PIB"),
    "public-debt": ("annual", "% del PIB"),
    "reserves": ("monthly", "USD millones"),
    "exports": ("monthly", "USD millones"),
    "tourism": ("monthly", "personas"),
    "fdi": ("quarterly", "USD millones"),
}

EXPECTED_GAP_DAYS = {
    "daily": (1, 10),
    "monthly": (20, 50),
    "quarterly": (70, 115),
    "annual": (300, 430),
}

BROAD_VALUE_RANGES = {
    "exchange-rate": (100, 1_500),
    "policy-rate": (-5, 30),
    "inflation": (-20, 50),
    "imae": (-50, 50),
    "unemployment": (0, 100),
    "poverty": (0, 100),
    "fiscal-balance": (-30, 30),
    "public-debt": (0, 250),
    "reserves": (0, 100_000),
    "exports": (0, 100_000),
    "tourism": (0, 2_000_000),
    "fdi": (-20_000, 20_000),
}


@dataclass(frozen=True)
class AuditFinding:
    slug: str
    severity: str
    check: str
    message: str


def _parse_date(raw: object) -> date | None:
    try:
        return date.fromisoformat(str(raw)[:10])
    except (TypeError, ValueError):
        return None


def _is_number(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _observed_frequency(periods: list[date]) -> tuple[str | None, float | None]:
    if len(periods) < 3:
        return None, None
    gaps = [(current - previous).days for previous, current in zip(periods, periods[1:])]
    typical_gap = float(median(gaps))
    for frequency, (minimum, maximum) in EXPECTED_GAP_DAYS.items():
        if minimum <= typical_gap <= maximum:
            return frequency, typical_gap
    return "irregular", typical_gap


def _comparison_ready(periods: list[date], values: list[float], today: date) -> bool:
    cutoff = date(today.year - 5, today.month, min(today.day, 28))
    recent_values = [value for period, value in zip(periods, values) if period >= cutoff]
    return len(recent_values) >= 3 and max(recent_values) != min(recent_values)


def audit_database(database: str | Path, *, today: date | None = None) -> dict:
    """Audita catálogo, metadatos y observaciones sin modificar la base."""

    today = today or date.today()
    findings: list[AuditFinding] = []
    series_results: list[dict] = []
    connection = sqlite3.connect(Path(database))
    connection.row_factory = sqlite3.Row
    try:
        catalog = connection.execute(
            """
            SELECT s.id, s.slug, s.name, s.frequency, s.unit, s.description,
                   src.name AS source_name, src.url AS source_url, src.is_official
            FROM series s JOIN sources src ON src.id = s.source_id
            ORDER BY s.id
            """
        ).fetchall()
        catalog_by_slug = {row["slug"]: row for row in catalog}

        missing_slugs = sorted(set(EXPECTED_SERIES) - set(catalog_by_slug))
        extra_slugs = sorted(set(catalog_by_slug) - set(EXPECTED_SERIES))
        for slug in missing_slugs:
            findings.append(AuditFinding(slug, "error", "catalog", "Serie ausente del catálogo."))
        for slug in extra_slugs:
            findings.append(AuditFinding(slug, "warning", "catalog", "Serie no incluida en el catálogo oficial de 12 indicadores."))

        for slug, (expected_frequency, expected_unit) in EXPECTED_SERIES.items():
            metadata = catalog_by_slug.get(slug)
            if metadata is None:
                continue
            declared_frequency = CATALOG[slug].frequency
            if metadata["frequency"] != declared_frequency:
                findings.append(
                    AuditFinding(
                        slug,
                        "warning",
                        "metadata_frequency",
                        f"Frecuencia declarada '{metadata['frequency']}', esperada '{declared_frequency}'.",
                    )
                )
            if metadata["unit"] != expected_unit:
                findings.append(
                    AuditFinding(
                        slug,
                        "warning",
                        "metadata_unit",
                        f"Unidad declarada '{metadata['unit']}', esperada '{expected_unit}'.",
                    )
                )
            if not metadata["description"] or not metadata["source_url"] or not metadata["source_name"]:
                findings.append(AuditFinding(slug, "error", "metadata", "Metadatos obligatorios incompletos."))
            if not metadata["is_official"]:
                findings.append(AuditFinding(slug, "error", "source", "La fuente no está marcada como oficial."))

            rows = connection.execute(
                "SELECT period, value FROM observations WHERE series_id = ? ORDER BY period",
                (metadata["id"],),
            ).fetchall()
            raw_periods = [row["period"] for row in rows]
            periods = [_parse_date(raw) for raw in raw_periods]
            invalid_dates = sum(period is None for period in periods)
            if invalid_dates:
                findings.append(AuditFinding(slug, "error", "dates", f"{invalid_dates} fechas inválidas."))
            valid_periods = [period for period in periods if period is not None]
            duplicates = [period for period, count in Counter(valid_periods).items() if count > 1]
            if duplicates:
                findings.append(AuditFinding(slug, "error", "duplicates", f"{len(duplicates)} periodos duplicados."))
            future_dates = [period for period in valid_periods if period > today]
            if future_dates:
                findings.append(AuditFinding(slug, "error", "future_dates", f"{len(future_dates)} observaciones futuras."))

            invalid_values = sum(not _is_number(row["value"]) for row in rows)
            if invalid_values:
                findings.append(AuditFinding(slug, "error", "values", f"{invalid_values} valores faltantes o inválidos."))
            values = [float(row["value"]) for row in rows if _is_number(row["value"])]
            minimum, maximum = BROAD_VALUE_RANGES[slug]
            outside_range = [value for value in values if not minimum <= value <= maximum]
            if outside_range:
                findings.append(AuditFinding(slug, "error", "range", f"{len(outside_range)} valores fuera del rango de plausibilidad."))

            observed_frequency, typical_gap = _observed_frequency(valid_periods)
            if observed_frequency not in (None, expected_frequency):
                findings.append(
                    AuditFinding(
                        slug,
                        "warning",
                        "observed_frequency",
                        f"La separación mediana es {typical_gap:.0f} días ({observed_frequency}); se esperaba {expected_frequency}.",
                    )
                )
            maximum_gap = max(
                ((current - previous).days for previous, current in zip(valid_periods, valid_periods[1:])),
                default=0,
            )
            allowed_maximum = EXPECTED_GAP_DAYS[expected_frequency][1]
            if maximum_gap > allowed_maximum:
                findings.append(
                    AuditFinding(
                        slug,
                        "review",
                        "gaps",
                        f"Brecha máxima de {maximum_gap} días; revisar continuidad y notas metodológicas.",
                    )
                )

            latest_period = max(valid_periods) if valid_periods else None
            latest_value = values[-1] if values else None
            series_results.append(
                {
                    "slug": slug,
                    "name": metadata["name"],
                    "observations": len(rows),
                    "first_period": min(valid_periods).isoformat() if valid_periods else None,
                    "latest_period": latest_period.isoformat() if latest_period else None,
                    "latest_value": latest_value,
                    "declared_frequency": metadata["frequency"],
                    "expected_frequency": expected_frequency,
                    "observed_frequency": observed_frequency,
                    "typical_gap_days": typical_gap,
                    "max_gap_days": maximum_gap,
                    "comparison_ready_5y": _comparison_ready(valid_periods, values, today) if valid_periods and values else False,
                }
            )
    finally:
        connection.close()

    severity_counts = Counter(finding.severity for finding in findings)
    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "audit_date": today.isoformat(),
        "expected_series": len(EXPECTED_SERIES),
        "catalog_series": len(catalog),
        "summary": {
            "errors": severity_counts["error"],
            "warnings": severity_counts["warning"],
            "reviews": severity_counts["review"],
            "comparison_ready_5y": sum(item["comparison_ready_5y"] for item in series_results),
        },
        "series": series_results,
        "findings": [asdict(finding) for finding in findings],
    }


def report_markdown(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# Auditoría de los 12 indicadores de FranQuestions",
        "",
        f"- Fecha de auditoría: {report['audit_date']}",
        f"- Series esperadas/encontradas: {report['expected_series']}/{report['catalog_series']}",
        f"- Errores críticos: {summary['errors']}",
        f"- Advertencias: {summary['warnings']}",
        f"- Revisiones metodológicas: {summary['reviews']}",
        f"- Series comparables en ventana de cinco años: {summary['comparison_ready_5y']}/{report['expected_series']}",
        "",
        "## Resultado por indicador",
        "",
        "| Indicador | Observaciones | Cobertura | Frecuencia observada | Comparador 5 años |",
        "|---|---:|---|---|---|",
    ]
    for item in report["series"]:
        coverage = f"{item['first_period']} a {item['latest_period']}"
        comparison = "Sí" if item["comparison_ready_5y"] else "No"
        lines.append(
            f"| {item['name']} | {item['observations']} | {coverage} | "
            f"{item['observed_frequency']} | {comparison} |"
        )
    lines.extend(["", "## Hallazgos", ""])
    if not report["findings"]:
        lines.append("No se detectaron hallazgos.")
    else:
        for finding in report["findings"]:
            lines.append(
                f"- **{finding['severity'].upper()} · {finding['slug']} · "
                f"{finding['check']}:** {finding['message']}"
            )
    lines.extend(
        [
            "",
            "## Interpretación",
            "",
            "Una advertencia o revisión no prueba que el dato sea incorrecto. Señala un punto que debe "
            "contrastarse con la metodología y las publicaciones de la fuente oficial.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_report(database: str | Path, destination: str | Path) -> dict:
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    report = audit_database(database)
    (destination / "auditoria_indicadores.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (destination / "auditoria_indicadores.md").write_text(
        report_markdown(report), encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = write_report(root / "franquestions.db", root / "audit_reports")
    print(json.dumps(result["summary"], ensure_ascii=False))
