import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from fq_observatorio.recovery_rehearsal import run_recovery_rehearsal


class RecoveryRehearsalTests(unittest.TestCase):
    def test_rehearsal_restores_only_a_temporary_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "source.db"
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("CREATE TABLE observations (id INTEGER, value TEXT)")
                connection.executemany(
                    "INSERT INTO observations VALUES (?, ?)",
                    [(1, "primera"), (2, "segunda")],
                )
                connection.commit()
            source_bytes = database.read_bytes()

            report = run_recovery_rehearsal(database)

            self.assertTrue(report.passed)
            self.assertTrue(report.source_unchanged)
            self.assertTrue(report.backup_matches_source)
            self.assertTrue(report.restored_matches_source)
            self.assertTrue(report.emergency_copy_created)
            self.assertEqual(report.tables_checked, 1)
            self.assertEqual(report.rows_checked, 2)
            self.assertEqual(report.writes_to_source, 0)
            self.assertEqual(database.read_bytes(), source_bytes)


if __name__ == "__main__":
    unittest.main()
