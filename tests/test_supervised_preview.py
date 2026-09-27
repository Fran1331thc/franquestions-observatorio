import unittest

from fq_observatorio.shadow_audit import record_hash
from fq_observatorio.supervised_preview import (
    build_human_review_checklist,
    evaluate_readiness,
)


def chained_records(days: list[str]) -> list[dict]:
    records = []
    previous_hash = "GENESIS"
    for day in days:
        record = {
            "costa_rica_date": day,
            "passed": True,
            "errors": 0,
            "writes_performed": False,
            "previous_hash": previous_hash,
        }
        record["record_hash"] = record_hash(record)
        records.append(record)
        previous_hash = record["record_hash"]
    return records


class ReadinessGateTests(unittest.TestCase):
    def test_blocks_until_three_distinct_successful_days(self):
        gate = evaluate_readiness(
            chained_records(["2026-09-27"]), current_check_passed=True
        )
        self.assertFalse(gate.ready)
        self.assertEqual(gate.successful_days, 1)
        self.assertIn("Faltan 2 día(s)", gate.reasons[0])

    def test_opens_only_when_all_conditions_are_true(self):
        gate = evaluate_readiness(
            chained_records(["2026-09-27", "2026-09-28", "2026-09-29"]),
            current_check_passed=True,
        )
        self.assertTrue(gate.ready)
        self.assertEqual(gate.reasons, ())

    def test_tampering_or_a_write_keeps_gate_closed(self):
        records = chained_records(["2026-09-27", "2026-09-28", "2026-09-29"])
        records[-1]["writes_performed"] = True
        gate = evaluate_readiness(records, current_check_passed=True)
        self.assertFalse(gate.ready)
        self.assertFalse(gate.chain_valid)
        self.assertFalse(gate.read_only_history)

    def test_human_checklist_never_claims_final_authorization(self):
        gate = evaluate_readiness(
            chained_records(["2026-09-27", "2026-09-28", "2026-09-29"]),
            current_check_passed=True,
        )
        checklist = build_human_review_checklist(
            {
                "gate": gate.as_dict(),
                "candidates": [
                    {
                        "Acción": "Agregar",
                        "Fecha": "2026-09-29",
                        "Valor propuesto": 455.0,
                    }
                ],
                "errors": 0,
                "warnings": 0,
                "writes_performed": False,
            }
        )
        final_authorization = checklist[-1]
        self.assertEqual(final_authorization["Estado"], "No solicitada")
        self.assertNotIn("Aplicar", [item["Estado"] for item in checklist])


if __name__ == "__main__":
    unittest.main()
