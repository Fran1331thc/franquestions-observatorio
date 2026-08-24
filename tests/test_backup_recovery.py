import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from fq_observatorio.backup import backup_sqlite_database, restore_sqlite_database


def create_database(path: Path, value: str) -> None:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE marker (value TEXT NOT NULL)")
        connection.execute("INSERT INTO marker (value) VALUES (?)", (value,))
        connection.commit()


def read_value(path: Path) -> str:
    with closing(sqlite3.connect(path)) as connection:
        return connection.execute("SELECT value FROM marker").fetchone()[0]


class BackupRecoveryTests(unittest.TestCase):
    def test_backup_and_restore_preserve_both_versions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            database = root / "franquestions.db"
            backups = root / "backups"
            recovery = root / "recovery"
            create_database(database, "version-inicial")

            original_backup = backup_sqlite_database(
                "sqlite:///./franquestions.db", root=root, backup_dir=backups
            )
            self.assertIsNotNone(original_backup)

            with closing(sqlite3.connect(database)) as connection:
                connection.execute("UPDATE marker SET value = ?", ("version-actual",))
                connection.commit()

            safety_backup = restore_sqlite_database(
                "sqlite:///./franquestions.db",
                original_backup,
                root=root,
                safety_backup_dir=recovery,
            )

            self.assertEqual(read_value(database), "version-inicial")
            self.assertIsNotNone(safety_backup)
            self.assertEqual(read_value(safety_backup), "version-actual")

    def test_rejects_invalid_backup_without_touching_database(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            database = root / "franquestions.db"
            invalid = root / "invalid.db"
            create_database(database, "intacta")
            invalid.write_text("esto no es sqlite", encoding="utf-8")

            with self.assertRaises(ValueError):
                restore_sqlite_database(
                    "sqlite:///./franquestions.db",
                    invalid,
                    root=root,
                    safety_backup_dir=root / "recovery",
                )

            self.assertEqual(read_value(database), "intacta")


if __name__ == "__main__":
    unittest.main()
