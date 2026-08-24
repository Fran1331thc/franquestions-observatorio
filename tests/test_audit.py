import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path

from fq_observatorio.audit import BROAD_VALUE_RANGES, EXPECTED_SERIES, audit_database
from fq_observatorio.catalog import CATALOG


class AuditTests(unittest.TestCase):
    def make_database(self) -> Path:
        temporary = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temporary.close()
        database = Path(temporary.name)
        connection = sqlite3.connect(database)
        connection.executescript(
            """
            CREATE TABLE sources (id INTEGER PRIMARY KEY, name TEXT, url TEXT, is_official INTEGER);
            CREATE TABLE series (
                id INTEGER PRIMARY KEY, slug TEXT, name TEXT, source_id INTEGER,
                frequency TEXT, unit TEXT, description TEXT
            );
            CREATE TABLE observations (
                id INTEGER PRIMARY KEY, series_id INTEGER, period TEXT, value REAL
            );
            INSERT INTO sources VALUES (1, 'Fuente', 'https://example.test', 1);
            """
        )
        for index, (slug, (_frequency, unit)) in enumerate(EXPECTED_SERIES.items(), start=1):
            frequency = CATALOG[slug].frequency
            connection.execute(
                "INSERT INTO series VALUES (?, ?, ?, 1, ?, ?, ?)",
                (index, slug, slug, frequency, unit, "Descripción"),
            )
            minimum, maximum = BROAD_VALUE_RANGES[slug]
            baseline = minimum + (maximum - minimum) / 3
            connection.executemany(
                "INSERT INTO observations(series_id, period, value) VALUES (?, ?, ?)",
                [
                    (index, "2024-01-31", baseline),
                    (index, "2025-01-31", baseline + 1),
                    (index, "2026-01-31", baseline + 2),
                ],
            )
        connection.commit()
        connection.close()
        return database

    def test_complete_catalog_has_no_critical_errors(self):
        database = self.make_database()
        try:
            report = audit_database(database, today=date(2026, 8, 1))
            self.assertEqual(report["catalog_series"], 12)
            self.assertEqual(report["summary"]["errors"], 0)
            metadata_warnings = [
                finding
                for finding in report["findings"]
                if finding["check"] in {"metadata_frequency", "metadata_unit"}
            ]
            self.assertEqual(metadata_warnings, [])
        finally:
            database.unlink(missing_ok=True)

    def test_duplicate_and_future_dates_are_errors(self):
        database = self.make_database()
        try:
            connection = sqlite3.connect(database)
            connection.execute(
                "INSERT INTO observations(series_id, period, value) VALUES (1, '2026-01-31', 9)"
            )
            connection.execute(
                "INSERT INTO observations(series_id, period, value) VALUES (1, '2027-01-31', 9)"
            )
            connection.commit()
            connection.close()
            report = audit_database(database, today=date(2026, 8, 1))
            checks = {(finding["slug"], finding["check"]) for finding in report["findings"]}
            self.assertIn(("exchange-rate", "duplicates"), checks)
            self.assertIn(("exchange-rate", "future_dates"), checks)
        finally:
            database.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
