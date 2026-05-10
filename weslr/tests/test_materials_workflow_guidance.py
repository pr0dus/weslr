import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
 sys.path.insert(0, ROOT)

from weslr.modules.materials_workflow_guidance import ( # noqa: E402
 CANONICAL_SCATTI_FORMULA,
 detect_materials_workflow,
 guide_materials_workflow,
)


class MaterialsWorkflowGuidanceTests(unittest.TestCase):
 def test_detects_casc2tio6_formula(self):
  result = detect_materials_workflow("Evaluate CaSc2TiO6 as a predicted compound.")
  self.assertEqual(result["domain"], "materials_discovery")
  self.assertEqual(result["normalized_formula"], CANONICAL_SCATTI_FORMULA)
  self.assertTrue(result["read_only"])

 def test_normalizes_unicode_subscript_formula(self):
  result = detect_materials_workflow("Evaluate CaSc₂TiO₆ for novelty.")
  self.assertEqual(result["domain"], "materials_discovery")
  self.assertEqual(result["normalized_formula"], CANONICAL_SCATTI_FORMULA)

 def test_detects_scatti_alias(self):
  result = detect_materials_workflow("Could scatti be a new layered oxide?")
  self.assertEqual(result["domain"], "materials_discovery")
  self.assertEqual(result["normalized_formula"], CANONICAL_SCATTI_FORMULA)
  self.assertEqual(result["candidates"][0]["name"], "scatti")

 def test_materials_keywords_trigger_discovery_domain(self):
  text = "Run CSP and DFT thinking for a new oxide crystal structure prediction."
  result = detect_materials_workflow(text)
  self.assertEqual(result["domain"], "materials_discovery")
  self.assertIn("csp", result["trigger_terms"])
  self.assertIn("dft", result["trigger_terms"])

 def test_missing_evidence_generated_automatically(self):
  result = guide_materials_workflow("CaSc2TiO6 predicted compound")
  self.assertEqual(result["domain"], "materials_discovery")
  self.assertIn("literature_search", result["missing_evidence"])
  self.assertIn("database_crosscheck", result["missing_evidence"])
  self.assertIn("stability_screening", result["missing_evidence"])
  self.assertTrue(result["next_steps"])

 def test_discovered_claim_is_downgraded_when_evidence_missing(self):
  result = guide_materials_workflow("We discovered CaSc2TiO6.")
  boundary = result["claim_boundary"]
  self.assertIn("discovered", boundary["blocked_claims"])
  self.assertIn("candidate", boundary["safe_terms"])
  self.assertIn("predicted compound", boundary["safe_terms"])
  self.assertIn("do not claim discovered", boundary["discovery_wording"].lower())

 def test_checked_sources_allow_only_bounded_not_found_wording(self):
  evidence = {
   "candidate_definition": True,
   "formula_normalization": True,
   "literature_search": True,
   "database_crosscheck": True,
   "checked_sources": ["COD", "Materials Project", "OQMD"],
  }
  result = guide_materials_workflow("Novelty check for CaSc2TiO6", evidence=evidence)
  boundary = result["claim_boundary"]
  self.assertIn("not found in checked sources", boundary["novelty_wording"])
  self.assertNotIn("absolute_novelty", boundary["blocked_claims"])

 def test_missing_stability_blocks_stable_and_discovered_claims(self):
  evidence = {
   "candidate_definition": True,
   "formula_normalization": True,
   "literature_search": True,
   "database_crosscheck": True,
   "checked_sources": ["COD", "Materials Project"],
  }
  result = guide_materials_workflow("We discovered stable CaSc2TiO6.", evidence=evidence)
  boundary = result["claim_boundary"]
  self.assertIn("stable", boundary["blocked_claims"])
  self.assertIn("discovered", boundary["blocked_claims"])
  self.assertIn("Do not claim stability", boundary["stability_wording"])

 def test_unknown_non_scientific_text_returns_unknown(self):
  result = guide_materials_workflow("Please make the public demo button nicer.")
  self.assertEqual(result["domain"], "unknown")
  self.assertIsNone(result["normalized_formula"])
  self.assertEqual(result["missing_evidence"], [])
  self.assertEqual(result["confidence"], 0.0)

 def test_read_only_always_true(self):
  detection = detect_materials_workflow("CaSc₂TiO₆")
  guidance = guide_materials_workflow("CaSc₂TiO₆")
  unknown = guide_materials_workflow("hello")
  self.assertTrue(detection["read_only"])
  self.assertTrue(guidance["read_only"])
  self.assertTrue(unknown["read_only"])


if __name__ == "__main__":
 unittest.main()
