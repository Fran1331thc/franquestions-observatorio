"""Ejecuta y registra una prueba BCCR sin escribir observaciones económicas."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from fq_observatorio.config import Settings
from fq_observatorio.connectors import BCCRConnector
from fq_observatorio.db import SessionLocal
from fq_observatorio.shadow_audit import append_shadow_audit
from fq_observatorio.shadow_updates import execute_bccr_shadow_check


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "audit_reports" / "bccr_exchange_rate_shadow.jsonl"
CR_TIMEZONE = ZoneInfo("America/Costa_Rica")


def main() -> None:
    now_utc = datetime.now(timezone.utc)
    today_cr = now_utc.astimezone(CR_TIMEZONE).date()
    payload = {
        "schema_version": 1,
        "run_at_utc": now_utc.isoformat(timespec="seconds"),
        "costa_rica_date": today_cr.isoformat(),
        "mode": "shadow_read_only",
        "slug": "exchange-rate",
        "indicator_code": "318",
        "workflow_run_id": os.getenv("GITHUB_RUN_ID", "local"),
        "commit_sha": os.getenv("GITHUB_SHA", "local"),
        "writes_performed": False,
    }
    try:
        with SessionLocal() as session:
            report = execute_bccr_shadow_check(
                session,
                slug="exchange-rate",
                indicator_code="318",
                start=today_cr - timedelta(days=45),
                end=today_cr,
                connector=BCCRConnector(settings=Settings()),
            )
        payload.update(report.as_dict())
    except Exception as exc:
        payload.update(
            {
                "passed": False,
                "errors": 1,
                "error_type": type(exc).__name__,
                "error_message": str(exc)[:300],
            }
        )
    entry = append_shadow_audit(LEDGER, payload)
    print(
        f"shadow_passed={str(entry.get('passed', False)).lower()} "
        f"record_hash={entry['record_hash']}"
    )


if __name__ == "__main__":
    main()
