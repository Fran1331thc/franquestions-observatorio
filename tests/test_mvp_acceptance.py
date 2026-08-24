import sqlite3
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from fq_observatorio.catalog import CATALOG


ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "franquestions.db"


class MvpAcceptanceTests(unittest.TestCase):
    def test_database_contains_the_complete_public_catalog(self):
        self.assertTrue(DATABASE.exists(), "No se encontró la base de datos vigente.")

        with sqlite3.connect(DATABASE) as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            rows = connection.execute(
                """
                SELECT s.slug, COUNT(o.id)
                FROM series AS s
                LEFT JOIN observations AS o ON o.series_id = s.id
                GROUP BY s.slug
                """
            ).fetchall()

        counts = dict(rows)
        self.assertEqual(integrity, "ok")
        self.assertEqual(set(counts), set(CATALOG))
        self.assertTrue(
            all(count > 0 for count in counts.values()),
            "Todos los indicadores deben tener al menos una observación.",
        )

    def test_all_indicators_have_public_metadata_and_official_links(self):
        self.assertEqual(len(CATALOG), 12)
        for slug, item in CATALOG.items():
            with self.subTest(slug=slug):
                self.assertTrue(item.name.strip())
                self.assertTrue(item.description.strip())
                self.assertTrue(item.source.strip())
                self.assertTrue(item.source_url.startswith("https://"))
                self.assertTrue(item.frequency.strip())
                self.assertTrue(item.unit.strip())
                self.assertTrue(item.why_it_matters.strip())

    def test_public_observatory_starts_and_exposes_all_indicators(self):
        app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
        app.run(timeout=30)

        self.assertEqual(list(app.exception), [])
        explorer = next(
            widget for widget in app.selectbox if widget.label == "Explorar indicador"
        )
        self.assertEqual(set(explorer.options), {item.name for item in CATALOG.values()})

    def test_local_updater_starts_and_exposes_all_indicators(self):
        app = AppTest.from_file(
            str(ROOT / "fq_observatorio" / "updater.py"), default_timeout=30
        )
        app.run(timeout=30)

        self.assertEqual(list(app.exception), [])
        selector = next(
            widget
            for widget in app.selectbox
            if widget.label == "Indicador que desea actualizar"
        )
        self.assertEqual(set(selector.options), {item.name for item in CATALOG.values()})


if __name__ == "__main__":
    unittest.main()
