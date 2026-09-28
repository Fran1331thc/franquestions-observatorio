"""Ensayo no destructivo de respaldo y restauración para una base SQLite."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .backup import backup_sqlite_database, restore_sqlite_database


@dataclass(frozen=True)
class DatabaseSnapshot:
    integrity: str
    tables: tuple[str, ...]
    row_counts: dict[str, int]
    schema_hash: str
    content_hash: str


@dataclass(frozen=True)
class RecoveryRehearsalReport:
    passed: bool
    source_unchanged: bool
    backup_matches_source: bool
    restored_matches_source: bool
    emergency_copy_created: bool
    tables_checked: int
    rows_checked: int
    writes_to_source: int = 0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _json_value(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"blob_sha256": hashlib.sha256(value).hexdigest()}
    return value


def database_snapshot(path: Path) -> DatabaseSnapshot:
    """Calcula una huella lógica estable sin modificar la base."""
    with closing(sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)) as connection:
        integrity_row = connection.execute("PRAGMA integrity_check").fetchone()
        integrity = str(integrity_row[0]) if integrity_row else "missing"
        schema_rows = connection.execute(
            "SELECT name, type, COALESCE(sql, '') FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
        ).fetchall()
        tables = tuple(
            row[0]
            for row in schema_rows
            if row[1] == "table"
        )
        row_counts: dict[str, int] = {}
        content_digest = hashlib.sha256()
        for table in tables:
            quoted = _quote_identifier(table)
            columns = [
                row[1]
                for row in connection.execute(f"PRAGMA table_info({quoted})").fetchall()
            ]
            order_clause = ", ".join(_quote_identifier(column) for column in columns)
            query = f"SELECT * FROM {quoted}"
            if order_clause:
                query += f" ORDER BY {order_clause}"
            rows = connection.execute(query).fetchall()
            row_counts[table] = len(rows)
            content_digest.update(table.encode("utf-8"))
            for row in rows:
                encoded = json.dumps(
                    [_json_value(value) for value in row],
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    default=str,
                )
                content_digest.update(encoded.encode("utf-8"))
        schema_payload = json.dumps(
            schema_rows,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    return DatabaseSnapshot(
        integrity=integrity,
        tables=tables,
        row_counts=row_counts,
        schema_hash=hashlib.sha256(schema_payload.encode("utf-8")).hexdigest(),
        content_hash=content_digest.hexdigest(),
    )


def run_recovery_rehearsal(database_path: Path) -> RecoveryRehearsalReport:
    """Restaura solo una copia temporal y comprueba equivalencia lógica completa."""
    source = database_path.resolve()
    before = database_snapshot(source)
    if before.integrity != "ok":
        raise ValueError("La base de origen no supera PRAGMA integrity_check")

    with tempfile.TemporaryDirectory(prefix="fq-recovery-rehearsal-") as directory:
        rehearsal_root = Path(directory)
        scratch = rehearsal_root / "scratch.db"
        with closing(sqlite3.connect(scratch)) as connection:
            connection.execute("CREATE TABLE rehearsal_marker (value TEXT NOT NULL)")
            connection.execute("INSERT INTO rehearsal_marker VALUES ('estado temporal')")
            connection.commit()

        backup = backup_sqlite_database(
            f"sqlite:///{source}",
            root=rehearsal_root,
            backup_dir=rehearsal_root / "backups",
        )
        if backup is None:
            raise RuntimeError("No se creó el respaldo SQLite del ensayo")
        backup_snapshot = database_snapshot(backup)
        emergency = restore_sqlite_database(
            f"sqlite:///{scratch}",
            backup,
            root=rehearsal_root,
            safety_backup_dir=rehearsal_root / "before-restore",
        )
        restored_snapshot = database_snapshot(scratch)
        emergency_created = emergency is not None and emergency.is_file()

    after = database_snapshot(source)
    backup_matches = backup_snapshot == before
    restored_matches = restored_snapshot == before
    source_unchanged = after == before
    return RecoveryRehearsalReport(
        passed=(
            backup_matches
            and restored_matches
            and source_unchanged
            and emergency_created
        ),
        source_unchanged=source_unchanged,
        backup_matches_source=backup_matches,
        restored_matches_source=restored_matches,
        emergency_copy_created=emergency_created,
        tables_checked=len(before.tables),
        rows_checked=sum(before.row_counts.values()),
    )
