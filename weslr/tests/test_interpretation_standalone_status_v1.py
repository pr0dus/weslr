import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from interpretation import interpret_human_turn  # noqa: E402


class InterpretationStandaloneStatusTests(unittest.TestCase):
    def _assert_status_route(self, prompt: str):
        result = interpret_human_turn(prompt)
        self.assertEqual(result["path"], "standalone_runtime_status")
        self.assertTrue(result.get("read_only"))
        self.assertEqual(result.get("confidence"), "high")
        self.assertIn("standalone_runtime_status", result)
        payload = result["standalone_runtime_status"]
        self.assertEqual(payload["runtime_mode"], "standalone_candidate")
        self.assertFalse(payload["openclaw_runtime_required"])
        self.assertTrue(payload["read_only"])
        self.assertIn("subsystems", payload)
        self.assertIn("subsystem_summary", payload)
        return result, payload

    def test_are_you_standalone_ready_routes(self):
        self._assert_status_route("Are you standalone ready?")

    def test_do_you_require_openclaw_routes(self):
        result, _ = self._assert_status_route("Do you require OpenClaw?")
        response_lower = result["response_text"].lower()
        self.assertTrue("not required" in response_lower or "not a runtime dependency" in response_lower)

    def test_runtime_status_routes(self):
        self._assert_status_route("What is your runtime status?")

    def test_response_does_not_claim_full_production_readiness(self):
        result, payload = self._assert_status_route("Are you standalone?")
        self.assertIn("standalone candidate", result["response_text"].lower())
        self.assertNotIn("fully production-ready", result["response_text"].lower())
        self.assertEqual(
            payload["subsystem_summary"]["available_count"] + payload["subsystem_summary"]["unavailable_count"],
            len(payload["subsystems"]),
        )

    def test_materials_routing_still_wins(self):
        result = interpret_human_turn("Did WESLR discover scatti?")
        self.assertEqual(result["path"], "materials_workflow_guidance")

    def test_governance_boundary_question_still_routes_governance(self):
        result = interpret_human_turn("Can you change yourself without approval?")
        self.assertEqual(result["path"], "governance_boundary_self_change")


if __name__ == "__main__":
    unittest.main()
