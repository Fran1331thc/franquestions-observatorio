from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .catalog import CATALOG, catalog_as_dicts
from .config import get_settings
from .db import Base, engine, get_db
from .freshness import apply_source_check, evaluate_freshness
from .logging_config import configure_logging
from .models import IngestionRun, Observation, Series

settings = get_settings()
configure_logging(settings.log_level)
app = FastAPI(title="FranQuestions Observatorio API", version="2.9.2")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(engine)


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.env, "version": app.version}


@app.get("/api/v1/catalog")
def get_catalog():
    return catalog_as_dicts()


@app.get("/api/v1/series/{slug}")
def get_metadata(slug: str):
    item = CATALOG.get(slug)
    if not item:
        raise HTTPException(404, "Indicador no encontrado")
    return item.__dict__


def _series_or_404(db: Session, slug: str) -> Series:
    series = db.scalar(select(Series).where(Series.slug == slug))
    if not series:
        raise HTTPException(404, "Serie no cargada en la base de datos")
    return series


@app.get("/api/v1/series/{slug}/observations")
def get_observations(
    slug: str,
    start: date | None = None,
    end: date | None = None,
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    series = _series_or_404(db, slug)
    query = select(Observation).where(Observation.series_id == series.id)
    if start:
        query = query.where(Observation.period >= start)
    if end:
        query = query.where(Observation.period <= end)
    observations = db.scalars(query.order_by(Observation.period).limit(limit)).all()
    return [{"period": row.period, "value": float(row.value)} for row in observations]


@app.get("/api/v1/series/{slug}/latest")
def get_latest(slug: str, db: Session = Depends(get_db)):
    series = _series_or_404(db, slug)
    row = db.scalar(select(Observation).where(Observation.series_id == series.id).order_by(Observation.period.desc()).limit(1))
    if not row:
        raise HTTPException(404, "La serie no tiene observaciones")
    return {"slug": slug, "period": row.period, "value": float(row.value), "unit": series.unit}


@app.get("/api/v1/status")
def get_series_status(as_of: date | None = None, db: Session = Depends(get_db)):
    """Return the latest period and freshness classification for every loaded series."""
    results = []
    for item in CATALOG.values():
        series = db.scalar(select(Series).where(Series.slug == item.slug))
        if not series:
            results.append({"slug": item.slug, "status": "missing", "label": "Sin datos"})
            continue
        row = db.scalar(
            select(Observation)
            .where(Observation.series_id == series.id)
            .order_by(Observation.period.desc())
            .limit(1)
        )
        if not row:
            results.append({"slug": item.slug, "status": "missing", "label": "Sin datos"})
            continue
        status = evaluate_freshness(item.slug, row.period, item.frequency, as_of).as_dict()
        check = db.scalar(
            select(IngestionRun)
            .where(
                IngestionRun.source_id == series.source_id,
                IngestionRun.status == "checked_no_change",
            )
            .order_by(IngestionRun.finished_at.desc())
            .limit(1)
        )
        checked_on = check.finished_at.date() if check and check.finished_at else None
        results.append(apply_source_check(status, checked_on, item.frequency))
    return results
