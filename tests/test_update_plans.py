import tempfile
import unittest
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fq_observatorio.catalog import CATALOG
from fq_observatorio.db import Base
from fq_observatorio.models import Observation, Series, Source
from fq_observatorio.update_plans import build_all_update_plans


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
            debt = next(plan for plan in plans if plan.slug == "public-debt")
            self.assertIn("2 archivos", debt.requirement)

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
