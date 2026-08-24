import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fq_observatorio.db import Base
from fq_observatorio.ingestion_history import recent_runs, status_counts
from fq_observatorio.models import IngestionRun, Source


class IngestionHistoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temporary.close()
        self.database = Path(temporary.name)
        self.engine = create_engine(f"sqlite:///{self.database}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(self.engine, expire_on_commit=False)

    def tearDown(self):
        self.engine.dispose()
        self.database.unlink(missing_ok=True)

    def test_history_summarizes_status_and_source(self):
        with self.Session() as session:
            source = Source(name="BCCR", url="https://example.test", is_official=True)
            session.add(source)
            session.flush()
            session.add_all(
                [
                    IngestionRun(source_id=source.id, status="success", rows_received=3, rows_written=1),
                    IngestionRun(source_id=source.id, status="failed", error_message="sin token"),
                ]
            )
            session.commit()
            self.assertEqual(status_counts(session), {"failed": 1, "success": 1})
            history = recent_runs(session)
            self.assertEqual(len(history), 2)
            self.assertEqual(history[0]["source"], "BCCR")


if __name__ == "__main__":
    unittest.main()
