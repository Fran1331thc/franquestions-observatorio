import unittest
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fq_observatorio.db import Base
from fq_observatorio.manual_import import compare_rows, import_rows
from fq_observatorio.models import IngestionRun, Observation, Revision, Series, Source


class PreviewComparisonTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine)
        with self.Session() as session:
            source = Source(name="INEC", url="https://inec.cr", is_official=True)
            session.add(source)
            session.flush()
            series = Series(
                slug="unemployment",
                name="Tasa de desempleo",
                source_id=source.id,
                official_code=None,
                frequency="monthly",
                unit="%",
                description="Prueba",
            )
            session.add(series)
            session.flush()
            session.add_all(
                [
                    Observation(series_id=series.id, period=date(2026, 2, 28), value=Decimal("6.66")),
                    Observation(series_id=series.id, period=date(2026, 3, 31), value=Decimal("7.00")),
                ]
            )
            session.commit()

    def test_classifies_new_revised_and_unchanged_without_writing(self):
        rows = [
            {"period": date(2026, 2, 28), "value": Decimal("6.66")},
            {"period": date(2026, 3, 31), "value": Decimal("7.0815")},
            {"period": date(2026, 4, 30), "value": Decimal("7.20")},
        ]
        with self.Session() as session:
            result = compare_rows(session, "unemployment", rows)
            count_after = session.query(Observation).count()

        self.assertEqual(result.unchanged, 1)
        self.assertEqual(len(result.revised_rows), 1)
        self.assertEqual(len(result.new_rows), 1)
        self.assertEqual(result.changes, 2)
        self.assertEqual(result.database_latest, date(2026, 3, 31))
        self.assertEqual(result.file_latest, date(2026, 4, 30))
        self.assertEqual(count_after, 2)

    def test_ignores_float_noise_below_database_precision(self):
        rows = [
            {"period": date(2026, 2, 28), "value": Decimal("6.660000000000001")},
            {"period": date(2026, 3, 31), "value": Decimal("7.000000000000001")},
        ]
        with self.Session() as session:
            result = compare_rows(session, "unemployment", rows)

        self.assertEqual(result.unchanged, 2)
        self.assertEqual(result.changes, 0)

    def test_equivalent_date_and_decimal_representations_are_unchanged(self):
        rows = [
            {"period": datetime(2026, 2, 28, 18, 45), "value": 6.66},
            {"period": "2026-03-31", "value": Decimal("7.000000004")},
        ]
        with self.Session() as session:
            preview = compare_rows(session, "unemployment", rows)
            report = import_rows(session, "unemployment", rows)

        self.assertEqual(preview.changes, 0)
        self.assertEqual(preview.unchanged, 2)
        self.assertEqual(preview.file_latest, date(2026, 3, 31))
        self.assertEqual(report.inserted, 0)
        self.assertEqual(report.revised, 0)
        self.assertEqual(report.unchanged, 2)

    def test_difference_at_database_precision_is_rounding_noise(self):
        rows = [
            {"period": date(2026, 2, 28), "value": Decimal("6.660000006")},
            {"period": date(2026, 3, 31), "value": "7.0"},
        ]
        with self.Session() as session:
            result = compare_rows(session, "unemployment", rows)

        self.assertEqual(len(result.revised_rows), 0)
        self.assertEqual(result.unchanged, 2)

    def test_applies_real_new_value_and_revision_with_history(self):
        rows = [
            {"period": date(2026, 2, 28), "value": Decimal("6.66")},
            {"period": date(2026, 3, 31), "value": Decimal("7.0815")},
            {"period": date(2026, 4, 30), "value": Decimal("7.20")},
        ]

        with self.Session() as session:
            preview = compare_rows(session, "unemployment", rows)
            report = import_rows(session, "unemployment", rows)

            series = session.query(Series).filter_by(slug="unemployment").one()
            observations = {
                item.period: item.value
                for item in session.query(Observation).filter_by(series_id=series.id).all()
            }
            revision = session.query(Revision).one()
            run = session.query(IngestionRun).filter_by(id=report.run_id).one()

        self.assertEqual(preview.changes, 2)
        self.assertEqual(report.inserted, 1)
        self.assertEqual(report.revised, 1)
        self.assertEqual(report.unchanged, 1)
        self.assertEqual(observations[date(2026, 3, 31)], Decimal("7.08150000"))
        self.assertEqual(observations[date(2026, 4, 30)], Decimal("7.20000000"))
        self.assertEqual(revision.old_value, Decimal("7.00000000"))
        self.assertEqual(revision.new_value, Decimal("7.08150000"))
        self.assertEqual(run.status, "success")
        self.assertEqual(run.rows_received, 3)
        self.assertEqual(run.rows_written, 2)


if __name__ == "__main__":
    unittest.main()
