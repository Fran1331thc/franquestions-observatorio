import tempfile
import unittest
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from fq_observatorio.db import Base
from fq_observatorio.ingestion import ingest_from_official_source
from fq_observatorio.models import IngestionRun, Observation, Series, Source


class IngestionTests(unittest.TestCase):
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
                    slug="exchange-rate",
                    name="Tipo de cambio",
                    source_id=source.id,
                    official_code="318",
                    frequency="daily",
                    unit="CRC por USD",
                    description="Serie de prueba",
                )
            )
            session.commit()

    def tearDown(self):
        self.engine.dispose()
        self.database.unlink(missing_ok=True)

    def test_successful_fetch_is_recorded_and_written(self):
        with self.Session() as session:
            report = ingest_from_official_source(
                session,
                "exchange-rate",
                lambda: [{"period": date(2026, 8, 1), "value": 500}],
            )
            self.assertEqual(report.status, "success")
            self.assertEqual(report.inserted, 1)
            run = session.scalar(select(IngestionRun))
            self.assertEqual(run.status, "success")
            self.assertEqual(session.query(Observation).count(), 1)

    def test_fetch_failure_is_recorded_without_changing_observations(self):
        def fail():
            raise RuntimeError("credenciales ausentes")

        with self.Session() as session:
            with self.assertRaisesRegex(RuntimeError, "credenciales ausentes"):
                ingest_from_official_source(session, "exchange-rate", fail)
            run = session.scalar(select(IngestionRun))
            self.assertEqual(run.status, "failed")
            self.assertIn("credenciales", run.error_message)
            self.assertEqual(session.query(Observation).count(), 0)

    def test_invalid_rows_are_rejected_without_writes(self):
        rows = [
            {"period": date(2026, 8, 1), "value": 500},
            {"period": date(2026, 8, 1), "value": 501},
        ]
        with self.Session() as session:
            report = ingest_from_official_source(
                session, "exchange-rate", lambda: rows
            )
            self.assertEqual(report.status, "rejected")
            self.assertEqual(session.query(Observation).count(), 0)


if __name__ == "__main__":
    unittest.main()
