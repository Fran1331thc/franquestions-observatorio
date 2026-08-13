"""Actualizaciones programables para conectores oficiales confirmados."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from .connectors import BCCRConnector, INECConnector
from .ingestion import ingest_from_official_source
from .manual_import import ImportReport
from .models import Series


def update_bccr_series(
    session: Session,
    slug: str,
    start: date,
    end: date,
    connector: BCCRConnector | None = None,
) -> ImportReport:
    """Actualiza una serie cuyo codigo webservice haya sido confirmado."""
    series = session.scalar(select(Series).where(Series.slug == slug))
    if not series:
        raise ValueError(f"Serie desconocida: {slug}")
    if not series.official_code or not series.official_code.isdigit():
        raise ValueError(
            f"{slug} no tiene un codigo numerico del webservice BCCR confirmado"
        )
    client = connector or BCCRConnector()
    return ingest_from_official_source(
        session,
        slug,
        lambda: client.fetch(series.official_code, start, end),
    )


def update_inec_csv_series(
    session: Session,
    slug: str,
    *,
    url: str | None = None,
    date_column: str = "period",
    value_column: str = "value",
    connector: INECConnector | None = None,
) -> ImportReport:
    """Actualiza una serie desde un CSV oficial expresamente configurado."""
    client = connector or INECConnector()
    return ingest_from_official_source(
        session,
        slug,
        lambda: client.fetch(url, date_column, value_column),
    )
