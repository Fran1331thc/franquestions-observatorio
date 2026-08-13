"""Consultas de seguimiento para las actualizaciones de fuentes oficiales."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import IngestionRun, Source


@dataclass(frozen=True)
class RunHistoryItem:
    run_id: int
    source: str
    status: str
    started_at: str
    finished_at: str | None
    rows_received: int
    rows_written: int
    error_message: str | None


def status_counts(session: Session) -> dict[str, int]:
    """Cuenta ejecuciones por estado sin asumir que todos ya existen."""
    rows = session.execute(
        select(IngestionRun.status, func.count(IngestionRun.id)).group_by(
            IngestionRun.status
        )
    ).all()
    return {status: count for status, count in rows}


def recent_runs(session: Session, limit: int = 50) -> list[dict]:
    """Devuelve el historial reciente con el nombre legible de la fuente."""
    rows = session.execute(
        select(IngestionRun, Source.name)
        .join(Source, Source.id == IngestionRun.source_id)
        .order_by(IngestionRun.started_at.desc(), IngestionRun.id.desc())
        .limit(limit)
    ).all()
    return [
        asdict(
            RunHistoryItem(
                run_id=run.id,
                source=source_name,
                status=run.status,
                started_at=run.started_at.isoformat() if run.started_at else "",
                finished_at=run.finished_at.isoformat() if run.finished_at else None,
                rows_received=run.rows_received or 0,
                rows_written=run.rows_written or 0,
                error_message=run.error_message,
            )
        )
        for run, source_name in rows
    ]
