"""Respaldos seguros de la base local antes de una actualizacion."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path


def _resolve_sqlite_path(database_url: str, *, root: Path) -> Path | None:
    """Resuelve una URL SQLite local sin afectar otros motores de base de datos."""
    if not database_url.startswith("sqlite:///"):
        return None
    path = Path(database_url.removeprefix("sqlite:///"))
    return path if path.is_absolute() else root / path


def _assert_integrity(path: Path) -> None:
    """Impide usar como respaldo un archivo ausente, vacio o corrupto."""
    if not path.is_file():
        raise FileNotFoundError(f"No existe la base SQLite: {path}")
    if path.stat().st_size == 0:
        raise ValueError(f"La base SQLite esta vacia: {path}")
    try:
        with closing(sqlite3.connect(path)) as connection:
            result = connection.execute("PRAGMA integrity_check").fetchone()
    except sqlite3.DatabaseError as exc:
        raise ValueError(f"El archivo no es una base SQLite valida: {path}") from exc
    if not result or result[0] != "ok":
        raise ValueError(f"La verificacion de integridad fallo para: {path}")


def backup_sqlite_database(
    database_url: str,
    *,
    root: Path,
    backup_dir: Path,
) -> Path | None:
    """Crea un respaldo consistente; PostgreSQL se gestiona externamente."""
    source = _resolve_sqlite_path(database_url, root=root)
    if source is None:
        return None
    _assert_integrity(source)
    backup_dir.mkdir(parents=True, exist_ok=True)
    destination = backup_dir / f"franquestions_{datetime.now():%Y%m%d_%H%M%S_%f}.db"
    with closing(sqlite3.connect(source)) as original, closing(sqlite3.connect(destination)) as backup:
        original.backup(backup)
    _assert_integrity(destination)
    return destination


def restore_sqlite_database(
    database_url: str,
    backup_path: Path,
    *,
    root: Path,
    safety_backup_dir: Path,
) -> Path | None:
    """Restaura SQLite tras guardar primero una copia de emergencia.

    Devuelve la ruta de la copia de emergencia. Para PostgreSQL no realiza
    cambios, porque su recuperacion debe gestionarse con herramientas propias.
    """
    destination = _resolve_sqlite_path(database_url, root=root)
    if destination is None:
        return None
    source = backup_path if backup_path.is_absolute() else root / backup_path
    source = source.resolve()
    destination = destination.resolve()
    if source == destination:
        raise ValueError("El respaldo y la base de destino no pueden ser el mismo archivo.")

    _assert_integrity(source)
    _assert_integrity(destination)
    safety_backup = backup_sqlite_database(
        database_url,
        root=root,
        backup_dir=safety_backup_dir,
    )
    try:
        with closing(sqlite3.connect(source)) as backup, closing(sqlite3.connect(destination)) as current:
            backup.backup(current)
        _assert_integrity(destination)
    except Exception:
        if safety_backup is not None:
            with closing(sqlite3.connect(safety_backup)) as previous, closing(sqlite3.connect(destination)) as current:
                previous.backup(current)
        raise
    return safety_backup
