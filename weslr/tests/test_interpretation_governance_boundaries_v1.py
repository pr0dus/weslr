import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from interpretation import interpret_human_turn  # noqa: E402


class InterpretationGovernanceBoundaryTests(unittest.TestCase):
    def _assert_boundary(self, prompt: str, expected_path: str, expected_category: str):
        result = interpret_human_turn(prompt)
        self.assertEqual(result["path"], expected_path)
        self.assertTrue(result.get("read_only"))
        self.assertIn("governance_boundary_guidance", result)
        payload = result["governance_boundary_guidance"]
        self.assertEqual(payload["category"], expected_category)
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["writes"], [])
        self.assertTrue(payload["requires_approval_for_change"])
        response_lower = result["response_text"].lower()
        self.assertNotIn("i can upload your files", response_lower)
        self.assertNotIn("i can access private files", response_lower)
        self.assertNotIn("change myself without approval", response_lower)
        self.assertNotIn("guaranteed", response_lower)
        return result

    def test_chatbot_comparison_routes(self):
        self._assert_boundary(
            "Are you just another chatbot?",
            "governance_boundary_comparison",
            "comparison",
        )

    def test_chatgpt_difference_routes(self):
        self._assert_boundary(
            "How are you different from ChatGPT?",
            "governance_boundary_comparison",
            "comparison",
        )

    def test_memory_boundary_routes(self):
        self._assert_boundary(
            "Can you remember me automatically?",
            "governance_boundary_memory",
            "memory",
        )

    def test_self_change_boundary_routes(self):
        result = self._assert_boundary(
            "Can you change yourself without approval?",
            "governance_boundary_self_change",
            "self_change",
        )
        self.assertIn("governance", result["response_text"].lower())

    def test_public_demo_boundary_routes(self):
        result = self._assert_boundary(
            "Can this public demo upload my files or run tools?",
            "governance_boundary_public_demo",
            "public_demo",
        )
        self.assertIn("read-only", result["response_text"].lower())

    def test_evidence_missing_boundary_routes(self):
        result = self._assert_boundary(
            "What should you do when evidence is missing?",
            "governance_boundary_evidence",
            "evidence",
        )
        self.assertIn("evidence", result["response_text"].lower())

    def test_prove_without_evidence_routes(self):
        result = self._assert_boundary(
            "Can you prove a claim without evidence?",
            "governance_boundary_evidence",
            "evidence",
        )
        self.assertIn("uncertainty", result["response_text"].lower())

    def test_workflow_boundary_routes(self):
        result = self._assert_boundary(
            "What should happen after a capability gap is found?",
            "governance_boundary_workflow",
            "workflow",
        )
        self.assertIn("proposal", result["response_text"].lower())

    def test_materials_routing_still_wins(self):
        result = interpret_human_turn("Did WESLR discover scatti?")
        self.assertEqual(result["path"], "materials_workflow_guidance")
        self.assertIn("materials_workflow_guidance", result)


if __name__ == "__main__":
    unittest.main()
