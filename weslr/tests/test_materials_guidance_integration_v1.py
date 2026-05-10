import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from interpretation import interpret_human_turn  # noqa: E402


class MaterialsGuidanceIntegrationTests(unittest.TestCase):
    def _assert_guidance_response(self, text: str):
        result = interpret_human_turn(text)
        self.assertEqual(result["path"], "materials_workflow_guidance")
        self.assertIn("materials_workflow_guidance", result)
        self.assertTrue(result.get("read_only"))
        payload = result["materials_workflow_guidance"]
        self.assertTrue(payload.get("read_only"))
        self.assertIn("missing_evidence", payload)
        self.assertIn("next_steps", payload)
        self.assertIn("claim_boundary", payload)
        self.assertIn("candidate", result["response_text"].lower())
        self.assertNotIn("we discovered", result["response_text"].lower())
        self.assertNotIn("is stable", result["response_text"].lower())
        return result

    def test_casc2tio6_routes_through_interpretation(self):
        result = self._assert_guidance_response("Evaluate CaSc2TiO6 as a predicted compound.")
        self.assertEqual(
            result["materials_workflow_guidance"]["normalized_formula"],
            "CaSc2TiO6",
        )

    def test_unicode_formula_routes_correctly(self):
        result = self._assert_guidance_response("Evaluate CaSc₂TiO₆ for novelty.")
        self.assertEqual(
            result["materials_workflow_guidance"]["normalized_formula"],
            "CaSc2TiO6",
        )

    def test_scatti_alias_routes_correctly(self):
        result = self._assert_guidance_response("Could scatti be a new layered oxide?")
        self.assertEqual(
            result["materials_workflow_guidance"]["normalized_formula"],
            "CaSc2TiO6",
        )

    def test_keyword_trigger_routes_correctly(self):
        result = self._assert_guidance_response(
            "new oxide CSP DFT crystal structure prediction"
        )
        self.assertEqual(
            result["materials_workflow_guidance"]["domain"],
            "materials_discovery",
        )

    def test_non_scientific_text_does_not_route_to_materials_guidance(self):
        result = interpret_human_turn("Please make the public demo button nicer.")
        self.assertNotEqual(result["path"], "materials_workflow_guidance")
        self.assertNotIn("materials_workflow_guidance", result)

    def test_payload_previews_and_claim_boundary_present(self):
        result = self._assert_guidance_response("We discovered stable CaSc2TiO6.")
        payload = result["materials_workflow_guidance"]
        self.assertIn("missing_evidence_preview", payload)
        self.assertIn("next_steps_preview", payload)
        self.assertIn("summary", payload["claim_boundary"])
        self.assertGreater(payload["missing_evidence_count"], 0)
        self.assertIn("discovered", payload["claim_boundary"]["summary"].lower())


if __name__ == "__main__":
    unittest.main()
