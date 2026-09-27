"""Consultas BCCR en sombra: comparan resultados sin escribir en la base."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from .connectors import BCCRConnector
from .manual_import import compare_rows
from .models import Series
from .validation import ValidationIssue, validate_series


@dataclass(frozen=True)
class ShadowUpdateReport:
    slug: str
    indicator_code: str
    start: date
    end: date
    rows_received: int
    new_rows: int
    revised_rows: int
    unchanged: int
    errors: int
    warnings: int
    database_latest: date | None
    source_latest: date | None
    writes_performed: bool = False

    @property
    def passed(self) -> bool:
        return self.rows_received > 0 and self.errors == 0

    def as_dict(self) -> dict:
        result = asdict(self)
        for key in ("start", "end", "database_latest", "source_latest"):
            value = result[key]
            result[key] = value.isoformat() if value else None
        result["passed"] = self.passed
        return result


def execute_bccr_shadow_check(
    session: Session,
    *,
    slug: str,
    indicator_code: str,
    start: date,
    end: date,
    connector: BCCRConnector | None = None,
) -> ShadowUpdateReport:
    """Consulta, valida y compara una serie sin commit, flush ni escrituras."""
    if start > end:
        raise ValueError("La fecha inicial no puede ser posterior a la final")
    series = session.scalar(select(Series).where(Series.slug == slug))
    if not series:
        raise ValueError(f"Serie desconocida: {slug}")

    client = connector or BCCRConnector()
    rows = client.fetch(indicator_code, start, end)
    issues = validate_series(rows, series.frequency)
    for row in rows:
        period = row.get("period")
        if isinstance(period, date) and period > end:
            issues.append(
                ValidationIssue(
                    "future_period",
                    "error",
                    "Periodo posterior al limite solicitado",
                    period,
                )
            )
    comparison = compare_rows(session, slug, rows)
    return ShadowUpdateReport(
        slug=slug,
        indicator_code=indicator_code,
        start=start,
        end=end,
        rows_received=len(rows),
        new_rows=len(comparison.new_rows),
        revised_rows=len(comparison.revised_rows),
        unchanged=comparison.unchanged,
        errors=sum(issue.severity == "error" for issue in issues),
        warnings=sum(issue.severity == "warning" for issue in issues),
        database_latest=comparison.database_latest,
        source_latest=comparison.file_latest,
    )
