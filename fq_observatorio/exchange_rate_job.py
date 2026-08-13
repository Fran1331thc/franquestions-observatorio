"""Tarea controlada para actualizar el tipo de cambio del BCCR."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .backup import backup_sqlite_database
from .config import get_settings
from .connectors import BCCRConnector
from .db import SessionLocal
from .models import Observation, Series
from .source_updates import update_bccr_series

ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT / "backups"


@dataclass(frozen=True)
class UpdatePlan:
    slug: str
    start: date
    end: date
    latest_stored: date | None
    overlap_days: int

    def as_dict(self) -> dict:
        result = asdict(self)
        return {
            key: value.isoformat() if isinstance(value, date) else value
            for key, value in result.items()
        }


def build_exchange_rate_plan(
    session: Session,
    *,
    today: date | None = None,
    overlap_days: int = 7,
) -> UpdatePlan:
    end = today or date.today()
    series = session.scalar(select(Series).where(Series.slug == "exchange-rate"))
    if not series:
        raise ValueError("La serie exchange-rate no existe en el catalogo local")
    latest = session.scalar(
        select(func.max(Observation.period)).where(Observation.series_id == series.id)
    )
    start = latest - timedelta(days=overlap_days) if latest else end - timedelta(days=365)
    if start > end:
        start = end
    return UpdatePlan("exchange-rate", start, end, latest, overlap_days)


def execute_exchange_rate_update(
    session: Session,
    *,
    connector: BCCRConnector | None = None,
    today: date | None = None,
    overlap_days: int = 7,
) -> dict:
    """Respalda y actualiza. Solo debe llamarse tras confirmacion explicita."""
    plan = build_exchange_rate_plan(
        session, today=today, overlap_days=overlap_days
    )
    settings = get_settings()
    backup = backup_sqlite_database(
        settings.database_url,
        root=ROOT,
        backup_dir=BACKUP_DIR,
    )
    report = update_bccr_series(
        session,
        plan.slug,
        plan.start,
        plan.end,
        connector=connector,
    )
    return {
        "plan": plan.as_dict(),
        "backup": str(backup) if backup else None,
        "report": {
            "run_id": report.run_id,
            "status": report.status,
            "rows_received": report.rows_received,
            "inserted": report.inserted,
            "revised": report.revised,
            "unchanged": report.unchanged,
            "issues": report.issues,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Actualizacion controlada del tipo de cambio FranQuestions"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Crea respaldo, consulta el BCCR y aplica datos validados.",
    )
    parser.add_argument("--overlap-days", type=int, default=7)
    args = parser.parse_args()
    with SessionLocal() as session:
        if not args.apply:
            plan = build_exchange_rate_plan(
                session, overlap_days=max(0, args.overlap_days)
            )
            print(json.dumps({"mode": "plan-only", "plan": plan.as_dict()}, ensure_ascii=False))
            return 0
        result = execute_exchange_rate_update(
            session, overlap_days=max(0, args.overlap_days)
        )
        print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
