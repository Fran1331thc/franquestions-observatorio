import unittest

from fq_observatorio.entitlements import PLAN_FEATURES, has_feature
from fq_observatorio.reasoning_toolkit import (
    TOOLS,
    WORKFLOWS,
    candidate_features,
    tools_for_workflow,
)


class ReasoningToolkitTests(unittest.TestCase):
    def test_all_twenty_tools_are_unique_and_assigned_once(self) -> None:
        self.assertEqual([tool.number for tool in TOOLS], list(range(1, 21)))
        self.assertEqual(len({tool.key for tool in TOOLS}), 20)
        self.assertTrue(all(tool.workflow in WORKFLOWS for tool in TOOLS))
        assigned = [tool.key for key in WORKFLOWS for tool in tools_for_workflow(key)]
        self.assertCountEqual(assigned, [tool.key for tool in TOOLS])

    def test_maturity_preserves_core_fusion_and_laboratory_states(self) -> None:
        counts = {
            maturity: sum(tool.maturity == maturity for tool in TOOLS)
            for maturity in {tool.maturity for tool in TOOLS}
        }
        self.assertEqual(counts, {"core": 8, "fusion_candidate": 9, "laboratory": 3})

    def test_candidate_commercial_features_are_owner_only(self) -> None:
        features = candidate_features()
        self.assertEqual(len(features), 6)
        for feature in features:
            self.assertTrue(has_feature("owner", feature))
            for plan in ("public", "pro", "business", "institutional"):
                self.assertFalse(has_feature(plan, feature))
                self.assertNotIn(feature, PLAN_FEATURES[plan])


if __name__ == "__main__":
    unittest.main()
