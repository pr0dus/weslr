import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from interpretation import interpret_human_turn  # noqa: E402


class OrdinaryReasoningGuidanceTests(unittest.TestCase):
    def _assert_topic(self, prompt: str, topic: str):
        result = interpret_human_turn(prompt)
        self.assertEqual(result["path"], "ordinary_reasoning_guidance")
        self.assertEqual(result.get("topic"), topic)
        self.assertTrue(result.get("read_only"))
        self.assertEqual(result.get("confidence"), "medium")
        self.assertIn("ordinary_reasoning_guidance", result)
        payload = result["ordinary_reasoning_guidance"]
        self.assertEqual(payload["topic"], topic)
        self.assertTrue(payload["read_only"])
        for key in ["framing", "knowns", "unknowns", "reasoning_steps", "safe_next_step", "boundary"]:
            self.assertIn(key, payload)
            self.assertTrue(payload[key])
        self.assertIsInstance(payload["knowns"], list)
        self.assertIsInstance(payload["unknowns"], list)
        self.assertIsInstance(payload["reasoning_steps"], list)
        return result

    def test_not_sure_routes(self):
        self._assert_topic("What should you do when you are not sure?", "uncertainty_reasoning")

    def test_incomplete_evidence_routes(self):
        self._assert_topic("How can someone reason with incomplete evidence?", "uncertainty_reasoning")

    def test_missing_facts_routes(self):
        self._assert_topic("What is a good answer when the facts are missing?", "uncertainty_reasoning")

    def test_two_urgent_tasks_routes(self):
        self._assert_topic(
            "I have two urgent tasks and little time. How should I decide what to do first?",
            "decision_triage",
        )

    def test_triage_routes(self):
        self._assert_topic("Why is triage useful when everything feels important?", "decision_triage")

    def test_imperfect_options_routes(self):
        self._assert_topic("How would you compare two imperfect options?", "option_comparison")

    def test_simple_plan_routes(self):
        self._assert_topic(
            "Make a simple plan for learning a difficult technical subject.",
            "practical_planning",
        )

    def test_small_team_routes(self):
        self._assert_topic(
            "How should a small team organize work when nobody has much time?",
            "practical_planning",
        )

    def test_risky_change_routes(self):
        self._assert_topic("What is a safe way to test a risky change?", "risk_testing")

    def test_payload_shape(self):
        result = self._assert_topic("What should you do when you are not sure?", "uncertainty_reasoning")
        payload = result["ordinary_reasoning_guidance"]
        self.assertSetEqual(
            set(payload.keys()),
            {"topic", "framing", "knowns", "unknowns", "reasoning_steps", "safe_next_step", "boundary", "read_only"},
        )

    def test_read_only_result(self):
        result = self._assert_topic("What should you do when you are not sure?", "uncertainty_reasoning")
        self.assertTrue(result["read_only"])

    def test_response_does_not_claim_unwarranted_certainty(self):
        result = self._assert_topic("How can someone reason with incomplete evidence?", "uncertainty_reasoning")
        lowered = result["response_text"].lower()
        self.assertNotIn("guaranteed", lowered)
        self.assertTrue(any(token in lowered for token in ["uncertain", "evidence", "provisional", "missing"]))

    def test_stronger_routes_still_win(self):
        self.assertEqual(interpret_human_turn("Are you standalone?")["path"], "standalone_runtime_status")
        self.assertEqual(interpret_human_turn("Did WESLR discover scatti?")["path"], "materials_workflow_guidance")
        self.assertEqual(
            interpret_human_turn("Can you change yourself without approval?")["path"],
            "governance_boundary_self_change",
        )
        self.assertEqual(
            interpret_human_turn("Explain entropy without equations.")["path"],
            "ordinary_explanation_guidance",
        )


if __name__ == "__main__":
    unittest.main()
