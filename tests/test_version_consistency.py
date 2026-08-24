import tomllib
import unittest
from pathlib import Path

from fq_observatorio import __version__


class VersionConsistencyTests(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]

    def test_package_matches_project_metadata(self):
        with (self.root / "pyproject.toml").open("rb") as project_file:
            metadata = tomllib.load(project_file)

        self.assertEqual(metadata["project"]["version"], __version__)

    def test_documentation_names_current_version(self):
        for filename in ("README.md", "ESTADO_DEL_PROYECTO.md"):
            contents = (self.root / filename).read_text(encoding="utf-8")
            self.assertIn(__version__, contents, filename)

    def test_stable_app_uses_shared_version(self):
        contents = (self.root / "streamlit_app_stable.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("from fq_observatorio import __version__", contents)
        self.assertIn("Publicación estable {__version__}", contents)


    def test_stable_charts_preserve_page_scrolling_by_default(self):
        contents = (self.root / "streamlit_app_stable.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"staticPlot": not interactive', contents)
        self.assertIn('"scrollZoom": False', contents)
        self.assertIn("touch-action: pan-y", contents)
        self.assertNotIn("st.line_chart(", contents)


if __name__ == "__main__":
    unittest.main()
