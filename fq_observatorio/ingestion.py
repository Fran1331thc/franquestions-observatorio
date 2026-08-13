"""Orquestacion segura de ingestas desde fuentes oficiales."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .manual_import import ImportReport, apply_rows
from .models import IngestionRun, Series

logger = logging.getLogger(__name__)

Fetcher = Callable[[], list[dict]]


def ingest_from_official_source(
    session: Session,
    slug: str,
    fetcher: Fetcher,
) -> ImportReport:
    """Consulta una fuente y aplica sus filas con trazabilidad completa.

    El registro de ejecucion se confirma antes de llamar al conector. Si la
    descarga falla, la base conserva el intento como ``failed`` y ninguna
    observacion existente se modifica.
    """
    series = session.scalar(select(Series).where(Series.slug == slug))
    if not series:
        raise ValueError(f"Serie desconocida: {slug}. Inicialice primero el catalogo.")

    run = IngestionRun(source_id=series.source_id, status="running")
    session.add(run)
    session.commit()

    try:
        rows = fetcher()
        if not rows:
            raise ValueError("La fuente oficial no devolvio observaciones")
    except Exception as exc:
        session.rollback()
        run = session.get(IngestionRun, run.id)
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
        run.error_message = str(exc)[:2000]
        session.commit()
        logger.warning("Fallo la consulta de la fuente oficial", extra={"slug": slug})
        raise

    return apply_rows(session, series, run, rows)
