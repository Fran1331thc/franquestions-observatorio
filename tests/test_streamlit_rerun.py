import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class StreamlitRerunRegressionTests(unittest.TestCase):
    """Evita que la interfaz desaparezca después de una interacción."""

    app_path = Path(__file__).resolve().parents[1] / "streamlit_app.py"

    def test_public_app_rebuilds_interface_after_rerun(self):
        app = AppTest.from_file(str(self.app_path), default_timeout=30)

        app.run()
        self.assertEqual([], list(app.exception))
        self.assertGreaterEqual(len(app.selectbox), 1)

        indicator_selector = app.selectbox[-1]
        indicator_selector.select(indicator_selector.options[1]).run()

        self.assertEqual([], list(app.exception))
        self.assertGreaterEqual(len(app.selectbox), 1)


if __name__ == "__main__":
    unittest.main()
