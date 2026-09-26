import tempfile
import unittest
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fq_observatorio.catalog import CATALOG
from fq_observatorio.db import Base
from fq_observatorio.models import Observation, Series, Source
from fq_observatorio.update_plans import build_all_update_plans, summarize_update_modes


class UpdatePlansTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temporary.close()
        self.database = Path(temporary.name)
        self.engine = create_engine(f"sqlite:///{self.database}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(self.engine, expire_on_commit=False)
        with self.Session() as session:
            source = Source(name="Oficial", url="https://example.test", is_official=True)
            session.add(source)
            session.flush()
            for item in CATALOG.values():
                session.add(
                    Series(
                        slug=item.slug, name=item.name, source_id=source.id,
                        official_code=item.official_code,
                        frequency=item.observation_frequency or item.frequency,
                        unit=item.unit, description=item.description
                    )
                )
            session.commit()

    def tearDown(self):
        self.engine.dispose()
        self.database.unlink(missing_ok=True)

    def test_catalog_has_twelve_safe_plans(self):
        with self.Session() as session:
            plans = build_all_update_plans(session, today=date(2026, 8, 1))
            self.assertEqual(len(plans), 12)
            self.assertTrue(all(plan.writes_require_confirmation for plan in plans))
            exchange = next(plan for plan in plans if plan.slug == "exchange-rate")
            self.assertEqual(exchange.readiness, "Esperando credenciales")
            self.assertEqual(exchange.update_mode, "Automatica supervisada")
            self.assertIn("Confirmar", exchange.human_role)
            self.assertIn("token", exchange.next_action)
            debt = next(plan for plan in plans if plan.slug == "public-debt")
            self.assertIn("2 archivos", debt.requirement)
            self.assertEqual(debt.update_mode, "Semiautomatica")
            self.assertIn("2 archivos", debt.human_role)

    def test_update_modes_cover_the_complete_catalog(self):
        with self.Session() as session:
            plans = build_all_update_plans(session, today=date(2026, 8, 1))
            modes = {plan.slug: plan.update_mode for plan in plans}
            self.assertEqual(set(modes), set(CATALOG))
            self.assertEqual(
                sum(mode == "Automatica supervisada" for mode in modes.values()),
                1,
            )
            self.assertEqual(
                sum(mode == "Semiautomatica" for mode in modes.values()),
                11,
            )

    def test_mode_summary_keeps_manual_work_visible(self):
        with self.Session() as session:
            plans = build_all_update_plans(session, today=date(2026, 8, 1))
            self.assertEqual(
                summarize_update_modes(plans),
                {
                    "Automatica supervisada": 1,
                    "Semiautomatica": 11,
                    "Manual": 0,
                },
            )

    def test_credentials_only_unlock_exchange_rate(self):
        with self.Session() as session:
            plans = build_all_update_plans(
                session, today=date(2026, 8, 1), bccr_credentials_ready=True
            )
            exchange = next(plan for plan in plans if plan.slug == "exchange-rate")
            self.assertEqual(exchange.readiness, "Listo")
            manual = [plan for plan in plans if plan.slug != "exchange-rate"]
            self.assertTrue(
                all(plan.readiness == "Disponible con revision humana" for plan in manual)
            )


if __name__ == "__main__":
    unittest.main()
