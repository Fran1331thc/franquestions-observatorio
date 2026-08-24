import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BetaReadinessTests(unittest.TestCase):
    def test_comparator_includes_retrieval_practice_and_limits(self) -> None:
        source = (ROOT / "streamlit_app_stable.py").read_text(encoding="utf-8")
        self.assertIn("Comprueba tu lectura del comparador", source)
        self.assertIn("1,2 desviaciones estándar por encima", source)
        self.assertIn("No demuestra importancia", source)
        self.assertIn("económica, causalidad ni un cambio estructural", source)

    def test_beta_plan_uses_a_small_diverse_cohort_and_honest_claims(self) -> None:
        plan = (ROOT / "BETA_ACADEMICA.md").read_text(encoding="utf-8")
        self.assertIn("8 a 12 personas", plan)
        self.assertIn("UCR, UNA y TEC", plan)
        self.assertIn("requieren descarga y revisión humana", plan)
        self.assertNotIn("automatiza la captura de datos oficiales", plan.casefold())
        self.assertNotIn("aísla el ruido mediático", plan.casefold())


if __name__ == "__main__":
    unittest.main()
