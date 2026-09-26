import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from fq_observatorio.db import Base
from fq_observatorio.models import Observation, Series, Source
from fq_observatorio.shadow_updates import execute_bccr_shadow_check


class FakeConnector:
    def fetch(self, indicator_code, start, end):
        return [
            {"period": date(2026, 8, 24), "value": Decimal("3.00")},
            {"period": date(2026, 9, 25), "value": Decimal("3.25")},
        ]


class ShadowUpdateTests(unittest.TestCase):
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
            series = Series(
                slug="policy-rate",
                name="Tasa de Politica Monetaria",
                source_id=source.id,
                frequency="daily",
                unit="% anual",
                description="Prueba",
            )
            session.add(series)
            session.flush()
            session.add(
                Observation(
                    series_id=series.id,
                    period=date(2026, 8, 24),
                    value=Decimal("3.00"),
                )
            )
            session.commit()

    def tearDown(self):
        self.engine.dispose()
        self.database.unlink(missing_ok=True)

    def test_shadow_check_compares_without_writing(self):
        with self.Session() as session:
            before = list(session.scalars(select(Observation)).all())
            report = execute_bccr_shadow_check(
                session,
                slug="policy-rate",
                indicator_code="3541",
                start=date(2026, 8, 24),
                end=date(2026, 9, 25),
                connector=FakeConnector(),
            )
            after = list(session.scalars(select(Observation)).all())
            self.assertTrue(report.passed)
            self.assertEqual(report.unchanged, 1)
            self.assertEqual(report.new_rows, 1)
            self.assertFalse(report.writes_performed)
            self.assertEqual(len(before), len(after))
            self.assertFalse(session.new)
            self.assertFalse(session.dirty)


if __name__ == "__main__":
    unittest.main()
