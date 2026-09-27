"""Ledger append-only para pruebas en sombra, separado de los datos publicados."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


def _canonical(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def record_hash(record: dict[str, Any]) -> str:
    payload = {key: value for key, value in record.items() if key != "record_hash"}
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def load_shadow_audit(path: str | Path) -> list[dict[str, Any]]:
    ledger = Path(path)
    if not ledger.exists():
        return []
    records = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def verify_shadow_audit(records: Iterable[dict[str, Any]]) -> bool:
    previous_hash = "GENESIS"
    for record in records:
        if record.get("previous_hash") != previous_hash:
            return False
        if record.get("record_hash") != record_hash(record):
            return False
        previous_hash = record["record_hash"]
    return True


def append_shadow_audit(path: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    ledger = Path(path)
    records = load_shadow_audit(ledger)
    if not verify_shadow_audit(records):
        raise ValueError("El historial de pruebas en sombra no supera la verificacion")
    entry = dict(payload)
    entry["previous_hash"] = records[-1]["record_hash"] if records else "GENESIS"
    entry["record_hash"] = record_hash(entry)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(_canonical(entry) + "\n")
    return entry


def independent_successful_days(records: Iterable[dict[str, Any]]) -> int:
    return len(
        {
            record.get("costa_rica_date")
            for record in records
            if record.get("passed") is True and record.get("errors") == 0
        }
        - {None}
    )
