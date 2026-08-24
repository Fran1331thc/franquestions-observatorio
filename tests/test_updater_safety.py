"""Pruebas de seguridad para el flujo local de actualización.

Todas las pruebas usan una base SQLite temporal. Nunca leen ni modifican la
base vigente de FranQuestions.
"""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from fq_observatorio.backup import backup_sqlite_database, restore_sqlite_database
from fq_observatorio.db import Base
from fq_observatorio.manual_import import compare_rows, import_rows
from fq_observatorio.models import Observation, Revision, Series, Source


class UpdaterSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.database_path = self.root / "franquestions-test.db"
        self.database_url = f"sqlite:///{self.database_path.as_posix()}"
        self.engine = create_engine(
            self.database_url,
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(self.engine)

        with Session(self.engine) as session:
            source = Source(
                name="Fuente oficial de prueba",
                url="https://example.test/oficial",
                is_official=True,
            )
            series = Series(
                slug="test-monthly-series",
                name="Serie mensual de prueba",
                source=source,
                frequency="monthly",
                unit="porcentaje",
                description="Serie creada únicamente para pruebas.",
            )
            session.add_all(
                [
                    series,
                    Observation(
                        series=series,
                        period=date(2026, 1, 31),
                        value=Decimal("10.00000000"),
                    ),
                    Observation(
                        series=series,
                        period=date(2026, 2, 28),
                        value=Decimal("11.00000000"),
                    ),
                ]
            )
            session.commit()

    def tearDown(self) -> None:
        self.engine.dispose()
        self.temporary_directory.cleanup()

    @staticmethod
    def _unchanged_rows() -> list[dict]:
        return [
            {"period": date(2026, 1, 31), "value": Decimal("10")},
            {"period": date(2026, 2, 28), "value": Decimal("11")},
        ]

    def _observation_count(self) -> int:
        with Session(self.engine) as session:
            return session.scalar(select(func.count()).select_from(Observation)) or 0

    def test_unchanged_file_produces_no_writes(self) -> None:
        with Session(self.engine) as session:
            comparison = compare_rows(session, "test-monthly-series", self._unchanged_rows())
            report = import_rows(session, "test-monthly-series", self._unchanged_rows())

        self.assertEqual(comparison.changes, 0)
        self.assertEqual(comparison.unchanged, 2)
        self.assertEqual(report.inserted, 0)
        self.assertEqual(report.revised, 0)
        self.assertEqual(report.unchanged, 2)
        self.assertEqual(self._observation_count(), 2)

    def test_equivalent_numeric_and_date_representations_are_unchanged(self) -> None:
        rows = [
            {"period": datetime(2026, 1, 31, 18, 45), "value": 10.0},
            {"period": "2026-02-28", "value": Decimal("11.000000004")},
        ]

        with Session(self.engine) as session:
            comparison = compare_rows(session, "test-monthly-series", rows)
            report = import_rows(session, "test-monthly-series", rows)

        self.assertEqual(comparison.changes, 0)
        self.assertEqual(comparison.unchanged, 2)
        self.assertEqual(comparison.file_latest, date(2026, 2, 28))
        self.assertEqual(report.inserted, 0)
        self.assertEqual(report.revised, 0)
        self.assertEqual(report.unchanged, 2)
        self.assertEqual(self._observation_count(), 2)

    def test_difference_at_database_precision_is_rounding_noise(self) -> None:
        rows = [
            {"period": date(2026, 1, 31), "value": Decimal("10.000000006")},
            {"period": date(2026, 2, 28), "value": "11.0"},
        ]

        with Session(self.engine) as session:
            comparison = compare_rows(session, "test-monthly-series", rows)

        self.assertEqual(len(comparison.revised_rows), 0)
        self.assertEqual(comparison.unchanged, 2)

    def test_new_observation_inserts_only_the_new_period(self) -> None:
        rows = self._unchanged_rows() + [
            {"period": date(2026, 3, 31), "value": Decimal("12")}
        ]

        with Session(self.engine) as session:
            comparison = compare_rows(session, "test-monthly-series", rows)
            report = import_rows(session, "test-monthly-series", rows)

        self.assertEqual(len(comparison.new_rows), 1)
        self.assertEqual(len(comparison.revised_rows), 0)
        self.assertEqual(report.inserted, 1)
        self.assertEqual(report.revised, 0)
        self.assertEqual(report.unchanged, 2)
        self.assertEqual(self._observation_count(), 3)

    def test_historical_revision_is_detected_and_recorded(self) -> None:
        rows = [
            {"period": date(2026, 1, 31), "value": Decimal("10")},
            {"period": date(2026, 2, 28), "value": Decimal("11.25")},
        ]

        with Session(self.engine) as session:
            comparison = compare_rows(session, "test-monthly-series", rows)
            report = import_rows(session, "test-monthly-series", rows)

        self.assertEqual(len(comparison.new_rows), 0)
        self.assertEqual(len(comparison.revised_rows), 1)
        self.assertEqual(report.inserted, 0)
        self.assertEqual(report.revised, 1)
        with Session(self.engine) as session:
            revision = session.scalar(select(Revision))
            revised_observation = session.scalar(
                select(Observation).where(Observation.period == date(2026, 2, 28))
            )
        self.assertIsNotNone(revision)
        self.assertEqual(revision.old_value, Decimal("11.00000000"))
        self.assertEqual(revision.new_value, Decimal("11.25000000"))
        self.assertEqual(revised_observation.value, Decimal("11.25000000"))

    def test_invalid_file_is_rejected_without_changing_observations(self) -> None:
        invalid_rows = [
            {"period": date(2026, 3, 31), "value": Decimal("12")},
            {"period": date(2026, 3, 31), "value": Decimal("13")},
        ]

        before = self._observation_count()
        with Session(self.engine) as session:
            report = import_rows(session, "test-monthly-series", invalid_rows)

        self.assertEqual(report.status, "rejected")
        self.assertTrue(any(issue["kind"] == "duplicate" for issue in report.issues))
        self.assertEqual(report.inserted, 0)
        self.assertEqual(report.revised, 0)
        self.assertEqual(self._observation_count(), before)

    def test_backup_is_created_before_a_valid_write(self) -> None:
        backup_path = backup_sqlite_database(
            self.database_url,
            root=self.root,
            backup_dir=self.root / "backups",
        )
        self.assertIsNotNone(backup_path)
        self.assertTrue(backup_path.exists())

        rows = self._unchanged_rows() + [
            {"period": date(2026, 3, 31), "value": Decimal("12")}
        ]
        with Session(self.engine) as session:
            report = import_rows(session, "test-monthly-series", rows)

        self.assertEqual(report.inserted, 1)
        self.assertEqual(self._observation_count(), 3)
        # El administrador de contexto de sqlite3 confirma la transacción,
        # pero no cierra la conexión. ``closing`` evita bloquear el respaldo
        # temporal en Windows al terminar la prueba.
        with closing(sqlite3.connect(backup_path)) as backup_connection:
            backup_count = backup_connection.execute(
                "SELECT COUNT(*) FROM observations"
            ).fetchone()[0]
            new_period_in_backup = backup_connection.execute(
                "SELECT COUNT(*) FROM observations WHERE period = ?",
                ("2026-03-31",),
            ).fetchone()[0]
        self.assertEqual(backup_count, 2)
        self.assertEqual(new_period_in_backup, 0)

    def test_restore_recovers_previous_state_and_keeps_emergency_copy(self) -> None:
        backup_path = backup_sqlite_database(
            self.database_url,
            root=self.root,
            backup_dir=self.root / "backups",
        )
        rows = self._unchanged_rows() + [
            {"period": date(2026, 3, 31), "value": Decimal("12")}
        ]
        with Session(self.engine) as session:
            report = import_rows(session, "test-monthly-series", rows)
        self.assertEqual(report.inserted, 1)
        self.assertEqual(self._observation_count(), 3)

        # Libera el archivo antes del reemplazo, igual que haría un reinicio
        # controlado de la aplicación local.
        self.engine.dispose()
        emergency_copy = restore_sqlite_database(
            self.database_url,
            backup_path,
            root=self.root,
            safety_backup_dir=self.root / "emergency-backups",
        )
        self.engine = create_engine(
            self.database_url,
            connect_args={"check_same_thread": False},
        )

        self.assertIsNotNone(emergency_copy)
        self.assertTrue(emergency_copy.exists())
        self.assertEqual(self._observation_count(), 2)
        with closing(sqlite3.connect(emergency_copy)) as connection:
            emergency_count = connection.execute(
                "SELECT COUNT(*) FROM observations"
            ).fetchone()[0]
        self.assertEqual(emergency_count, 3)

    def test_corrupt_backup_is_rejected_without_changing_database(self) -> None:
        corrupt_backup = self.root / "corrupt-backup.db"
        corrupt_backup.write_text("esto no es una base SQLite", encoding="utf-8")
        before = self._observation_count()

        with self.assertRaises(ValueError):
            restore_sqlite_database(
                self.database_url,
                corrupt_backup,
                root=self.root,
                safety_backup_dir=self.root / "emergency-backups",
            )

        self.assertEqual(self._observation_count(), before)


if __name__ == "__main__":
    unittest.main()
