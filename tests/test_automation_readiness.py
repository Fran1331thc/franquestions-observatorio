import unittest

from fq_observatorio.automation_readiness import priority_automation_candidates


class AutomationReadinessTests(unittest.TestCase):
    def test_priority_candidates_cannot_be_promoted_prematurely(self):
        candidates = priority_automation_candidates()
        self.assertEqual(
            {candidate.slug for candidate in candidates},
            {"policy-rate", "reserves"},
        )
        self.assertTrue(all(candidate.official_source for candidate in candidates))
        self.assertTrue(all(candidate.parser_available for candidate in candidates))
        self.assertTrue(all(candidate.validation_available for candidate in candidates))
        self.assertTrue(
            all(not candidate.ready_for_supervised_automation for candidate in candidates)
        )

    def test_each_candidate_requires_three_shadow_runs(self):
        candidates = priority_automation_candidates()
        self.assertTrue(
            all(candidate.shadow_runs_required == 3 for candidate in candidates)
        )


if __name__ == "__main__":
    unittest.main()
