import tempfile
import unittest
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fq_observatorio.db import Base
from fq_observatorio.exchange_rate_job import build_exchange_rate_plan
from fq_observatorio.models import Observation, Series, Source


class ExchangeRatePlanTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temporary.close()
        self.database = Path(temporary.name)
        self.engine = create_engine(f"sqlite:///{self.database}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(self.engine, expire_on_commit=False)
        with self.Session() as session:
            source = Source(name="BCCR", url="https://example.test", is_official=True)
            session.add(source)
            session.flush()
            session.add(
                Series(
                    slug="exchange-rate", name="Tipo de cambio", source_id=source.id,
                    official_code="318", frequency="daily", unit="CRC por USD",
                    description="Serie de prueba"
                )
            )
            session.commit()

    def tearDown(self):
        self.engine.dispose()
        self.database.unlink(missing_ok=True)

    def test_new_series_requests_one_year(self):
        with self.Session() as session:
            plan = build_exchange_rate_plan(session, today=date(2026, 8, 1))
            self.assertEqual(plan.start, date(2025, 8, 1))
            self.assertIsNone(plan.latest_stored)

    def test_existing_series_uses_overlap_for_revisions(self):
        with self.Session() as session:
            series = session.query(Series).filter_by(slug="exchange-rate").one()
            session.add(Observation(series_id=series.id, period=date(2026, 7, 30), value=500))
            session.commit()
            plan = build_exchange_rate_plan(
                session, today=date(2026, 8, 1), overlap_days=7
            )
            self.assertEqual(plan.start, date(2026, 7, 23))
            self.assertEqual(plan.end, date(2026, 8, 1))


if __name__ == "__main__":
    unittest.main()
