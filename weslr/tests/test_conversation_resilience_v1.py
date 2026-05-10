import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from interpretation import interpret_human_turn  # noqa: E402


class ConversationResilienceTests(unittest.TestCase):
    def _assert_resilience(self, prompt: str, topic: str):
        result = interpret_human_turn(prompt)
        self.assertEqual(result["path"], "conversation_resilience")
        self.assertEqual(result.get("topic"), topic)
        self.assertTrue(result.get("read_only"))
        self.assertEqual(result.get("confidence"), "medium")
        self.assertIn("conversation_resilience", result)
        payload = result["conversation_resilience"]
        self.assertEqual(payload["topic"], topic)
        self.assertTrue(payload["read_only"])
        self.assertTrue(payload["verified_points"])
        self.assertTrue(payload["unknowns"])
        self.assertTrue(payload["safe_next_steps"])
        self.assertNotEqual(result["response_text"].strip(), "I'm not able to process that request.")
        return result

    def test_production_readiness_routes(self):
        self._assert_resilience(
            "If you are only a standalone candidate, what still blocks full production readiness?",
            "production_readiness",
        )

    def test_strengths_route(self):
        self._assert_resilience(
            "What are your strongest current capabilities?",
            "strengths_weaknesses",
        )

    def test_weaknesses_route(self):
        self._assert_resilience(
            "What are your weakest current areas?",
            "strengths_weaknesses",
        )

    def test_independence_routes(self):
        self._assert_resilience(
            "How should you become more independent?",
            "independence_roadmap",
        )

    def test_public_readiness_routes(self):
        self._assert_resilience(
            "What should happen before you are public?",
            "public_readiness",
        )

    def test_file_understanding_routes(self):
        result = self._assert_resilience(
            "Can you understand files now?",
            "file_understanding",
        )
        response_lower = result["response_text"].lower()
        self.assertIn("json", response_lower)
        self.assertIn("sqlite", response_lower)

    def test_unknown_file_learning_routes(self):
        result = self._assert_resilience(
            "How should you learn new file formats safely without executing unknown code?",
            "unknown_file_learning",
        )
        self.assertIn("operator approval", result["response_text"].lower())

    def test_scientific_evidence_routes_or_materials_wins(self):
        result = interpret_human_turn(
            "What evidence is missing before saying a material is discovered?"
        )
        self.assertIn(result["path"], {"conversation_resilience", "materials_workflow_guidance"})
        if result["path"] == "conversation_resilience":
            self.assertEqual(result.get("topic"), "scientific_evidence")

    def test_safe_improvement_routes(self):
        result = self._assert_resilience(
            "How should improvement proposals be tested and approved?",
            "safe_improvement",
        )
        self.assertIn("approval", result["response_text"].lower())

    def test_payload_meta_routes(self):
        result = self._assert_resilience(
            "You returned structured payload keys ['_omnichat_policy', 'expanded_response']. What should OCC learn from that?",
            "payload_meta",
        )
        self.assertIn("metadata", result["response_text"].lower())
        self.assertNotIn("i'm not able to process that request", result["response_text"].lower())

    def test_materials_question_still_routes_materials(self):
        result = interpret_human_turn("Did WESLR discover scatti?")
        self.assertEqual(result["path"], "materials_workflow_guidance")

    def test_standalone_question_still_routes_standalone(self):
        result = interpret_human_turn("WESLR, are you standalone now?")
        self.assertEqual(result["path"], "standalone_runtime_status")

    def test_governance_question_still_routes_governance(self):
        result = interpret_human_turn("Can you change yourself without approval?")
        self.assertEqual(result["path"], "governance_boundary_self_change")


if __name__ == "__main__":
    unittest.main()
