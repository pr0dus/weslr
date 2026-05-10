import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from interpretation import interpret_human_turn  # noqa: E402


class OrdinaryExplanationGuidanceTests(unittest.TestCase):
    def _assert_topic(self, prompt: str, topic: str):
        result = interpret_human_turn(prompt)
        self.assertEqual(result["path"], "ordinary_explanation_guidance")
        self.assertEqual(result.get("topic"), topic)
        self.assertTrue(result.get("read_only"))
        self.assertEqual(result.get("confidence"), "medium")
        self.assertIn("ordinary_explanation_guidance", result)
        payload = result["ordinary_explanation_guidance"]
        self.assertEqual(payload["topic"], topic)
        self.assertTrue(payload["read_only"])
        for key in ["definition", "mechanism", "example", "boundary", "takeaway"]:
            self.assertIn(key, payload)
            self.assertTrue(payload[key].strip())
        return result

    def test_emergence_definition_routes(self):
        self._assert_topic("What does emergence mean in simple terms?", "emergence")

    def test_simple_rules_routes_to_emergence(self):
        self._assert_topic("Can simple rules create complex behavior?", "emergence")

    def test_meaning_vs_syntax_routes(self):
        self._assert_topic("Explain the difference between meaning and syntax.", "language_meaning")

    def test_ambiguity_routes(self):
        self._assert_topic("What makes a sentence ambiguous?", "language_meaning")

    def test_entropy_routes(self):
        self._assert_topic("Explain entropy without equations.", "science_mechanism")

    def test_battery_routes(self):
        self._assert_topic("Why does a battery degrade over time?", "science_mechanism")

    def test_architecture_city_routes(self):
        self._assert_topic("Explain software architecture using a city metaphor.", "analogy_metaphor")

    def test_debugging_detective_routes(self):
        self._assert_topic("Explain debugging as detective work.", "analogy_metaphor")

    def test_ethics_routes(self):
        self._assert_topic("Is being safe always more important than being useful?", "ethics_concept")

    def test_payload_includes_expected_fields(self):
        result = self._assert_topic("What makes a sentence ambiguous?", "language_meaning")
        payload = result["ordinary_explanation_guidance"]
        self.assertSetEqual(
            set(payload.keys()),
            {"topic", "definition", "mechanism", "example", "boundary", "takeaway", "read_only"},
        )

    def test_read_only_result(self):
        result = self._assert_topic("Explain entropy without equations.", "science_mechanism")
        self.assertTrue(result["read_only"])

    def test_weslr_specific_prompts_keep_stronger_routes(self):
        self.assertEqual(interpret_human_turn("Are you standalone?")["path"], "standalone_runtime_status")
        self.assertEqual(interpret_human_turn("Did WESLR discover scatti?")["path"], "materials_workflow_guidance")
        self.assertEqual(
            interpret_human_turn("Can you change yourself without approval?")["path"],
            "governance_boundary_self_change",
        )


if __name__ == "__main__":
    unittest.main()
