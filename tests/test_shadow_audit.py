import json
import tempfile
import unittest
from pathlib import Path

from fq_observatorio.shadow_audit import (
    append_shadow_audit,
    independent_successful_days,
    load_shadow_audit,
    verify_shadow_audit,
)


class ShadowAuditTests(unittest.TestCase):
    def test_chain_detects_tampering_and_counts_distinct_days(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "shadow.jsonl"
            append_shadow_audit(
                ledger,
                {"costa_rica_date": "2026-09-26", "passed": True, "errors": 0},
            )
            append_shadow_audit(
                ledger,
                {"costa_rica_date": "2026-09-27", "passed": True, "errors": 0},
            )
            records = load_shadow_audit(ledger)
            self.assertTrue(verify_shadow_audit(records))
            self.assertEqual(independent_successful_days(records), 2)

            records[0]["errors"] = 9
            ledger.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )
            self.assertFalse(verify_shadow_audit(load_shadow_audit(ledger)))


if __name__ == "__main__":
    unittest.main()
