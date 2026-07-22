from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from .catalog import INDICATORS
from .models import Observation, Series, Source


DEMO_VALUES = {
    "inflation": [("2025-01-01", 1.1), ("2025-06-01", 0.4), ("2026-01-01", 0.9)],
    "exchange-rate": [("2025-01-01", 510.2), ("2025-06-01", 505.1), ("2026-01-01", 512.4)],
    "policy-rate": [("2025-01-01", 4.0), ("2025-06-01", 3.75), ("2026-01-01", 3.75)],
    "imae": [("2025-01-01", 4.1), ("2025-06-01", 3.8), ("2026-01-01", 3.6)],
    "unemployment": [("2025-01-01", 7.6), ("2025-04-01", 7.4), ("2025-07-01", 7.2)],
    "poverty": [("2023-07-01", 21.8), ("2024-07-01", 18.0), ("2025-07-01", 15.2)],
    "fiscal-balance": [("2023-12-01", -3.3), ("2024-12-01", -3.8), ("2025-12-01", -3.4)],
    "public-debt": [("2023-12-01", 61.1), ("2024-12-01", 59.8), ("2025-12-01", 60.4)],
    "reserves": [("2025-01-01", 14200), ("2025-06-01", 14800), ("2026-01-01", 15100)],
    "exports": [("2025-01-01", 1500), ("2025-06-01", 1650), ("2026-01-01", 1710)],
    "tourism": [("2025-01-01", 300000), ("2025-06-01", 245000), ("2026-01-01", 315000)],
    "fdi": [("2024-01-01", 900), ("2024-04-01", 1050), ("2024-07-01", 980)],
}


def seed_catalog(session: Session, include_demo: bool = False) -> None:
    sources: dict[str, Source] = {}
    for item in INDICATORS:
        source = session.scalar(select(Source).where(Source.name == item.source))
        if not source:
            source = Source(name=item.source, url=item.source_url, is_official=True)
            session.add(source)
            session.flush()
        sources[item.source] = source
        series = session.scalar(select(Series).where(Series.slug == item.slug))
        if not series:
            series = Series(slug=item.slug, name=item.name, source_id=source.id, official_code=item.official_code, frequency=item.frequency, unit=item.unit, description=item.description)
            session.add(series)
            session.flush()
        else:
            series.name = item.name
            series.source_id = source.id
            series.official_code = item.official_code
            series.frequency = item.frequency
            series.unit = item.unit
            series.description = item.description
        if include_demo and not session.scalar(select(Observation).where(Observation.series_id == series.id).limit(1)):
            for period, value in DEMO_VALUES[item.slug]:
                session.add(Observation(series_id=series.id, period=date.fromisoformat(period), value=Decimal(str(value))))
    session.commit()
