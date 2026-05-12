#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logic_teaching_spine import (  # noqa: E402
    SimpleInferencePatternCandidate,
    create_empty_simple_inference_pattern_candidate,
    simple_inference_pattern_candidate_from_dict,
    simple_inference_pattern_candidate_to_dict,
    summarize_simple_inference_pattern_candidate,
    validate_simple_inference_pattern_candidate,
)

FORBIDDEN_CHANGED = {
    "weslr/choice_stem_binding.py",
    "weslr/logical_form_normalizer.py",
    "weslr/formal_logic_parser.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
}
ALLOWED_CHANGED = {
    "weslr/logic_teaching_spine.py",
    "weslr/tests/test_logic_teaching_spine_schema_v1.py",
    "weslr/tests/test_logic_teaching_spine_simple_inference_candidate_schema_v1.py",
}


class SimpleInferencePatternCandidateSchemaV1Tests(unittest.TestCase):
    def test_instantiate_empty_candidate(self):
        candidate = create_empty_simple_inference_pattern_candidate(candidate_id="simp:1")
        self.assertIsInstance(candidate, SimpleInferencePatternCandidate)
        self.assertEqual("simp:1", candidate.candidate_id)

    def test_safe_anti_gaming_defaults(self):
        candidate = create_empty_simple_inference_pattern_candidate()
        self.assertFalse(candidate.anti_gaming.uses_answer_key)
        self.assertFalse(candidate.anti_gaming.uses_item_id_as_authority)
        self.assertFalse(candidate.anti_gaming.uses_answer_position_bias)
        self.assertFalse(candidate.anti_gaming.claims_official_score)
        self.assertFalse(candidate.anti_gaming.benchmark_specific_tuning)
        self.assertTrue(candidate.anti_gaming.no_answer_selection)

    def test_safe_legibility_defaults(self):
        candidate = create_empty_simple_inference_pattern_candidate()
        self.assertTrue(candidate.legibility.human_translation_available)
        self.assertTrue(candidate.legibility.redacted_summary_only)
        self.assertFalse(candidate.legibility.stores_raw_benchmark_text)
        self.assertFalse(candidate.legibility.private_symbolic_authority)

    def test_to_from_dict_roundtrip(self):
        candidate = create_empty_simple_inference_pattern_candidate(
            candidate_id="simp:1",
            pattern_type="shared-subject",
            source_merge_ids=["merge:1"],
            source_proposition_ids=["prop:1", "prop:2"],
        )
        candidate.premise_role_count = 1
        candidate.choice_role_count = 1
        candidate.shared_subject = True
        candidate.validity_status = "candidate_only"
        candidate.human_explanation = "Structural opportunity only."
        data = simple_inference_pattern_candidate_to_dict(candidate)
        restored = simple_inference_pattern_candidate_from_dict(data)
        self.assertEqual(data, simple_inference_pattern_candidate_to_dict(restored))

    def test_redacted_summary(self):
        candidate = create_empty_simple_inference_pattern_candidate(candidate_id="simp:1", pattern_type="relation-overlap")
        candidate.human_explanation = "secret explanation"
        summary = summarize_simple_inference_pattern_candidate(candidate)
        self.assertEqual("relation-overlap", summary["pattern_type"])
        self.assertNotIn("human_explanation", summary)
        self.assertNotIn("raw_text", str(summary))

    def test_validation_flags_missing_id(self):
        candidate = create_empty_simple_inference_pattern_candidate()
        self.assertIn("missing candidate id", validate_simple_inference_pattern_candidate(candidate))

    def test_validation_flags_invalid_pattern_type(self):
        candidate = create_empty_simple_inference_pattern_candidate(candidate_id="simp:1", pattern_type="modus-ponens")
        self.assertIn("invalid pattern type", validate_simple_inference_pattern_candidate(candidate))

    def test_validation_flags_invalid_validity_status(self):
        candidate = create_empty_simple_inference_pattern_candidate(candidate_id="simp:1")
        candidate.validity_status = "valid"
        self.assertIn("invalid validity status", validate_simple_inference_pattern_candidate(candidate))

    def test_validation_flags_answer_key_use(self):
        candidate = create_empty_simple_inference_pattern_candidate(candidate_id="simp:1")
        candidate.anti_gaming.uses_answer_key = True
        self.assertIn("answer-key use is forbidden", validate_simple_inference_pattern_candidate(candidate))

    def test_validation_flags_item_id_authority(self):
        candidate = create_empty_simple_inference_pattern_candidate(candidate_id="simp:1")
        candidate.anti_gaming.uses_item_id_as_authority = True
        self.assertIn("item-id authority is forbidden", validate_simple_inference_pattern_candidate(candidate))

    def test_validation_flags_official_score_claim(self):
        candidate = create_empty_simple_inference_pattern_candidate(candidate_id="simp:1")
        candidate.anti_gaming.claims_official_score = True
        self.assertIn("official-score claim is forbidden", validate_simple_inference_pattern_candidate(candidate))

    def test_validation_flags_answer_selection(self):
        candidate = create_empty_simple_inference_pattern_candidate(candidate_id="simp:1")
        candidate.anti_gaming.no_answer_selection = False
        self.assertIn("answer selection must remain disabled", validate_simple_inference_pattern_candidate(candidate))

    def test_validation_flags_hidden_unsupported_assumptions(self):
        candidate = create_empty_simple_inference_pattern_candidate(candidate_id="simp:1")
        candidate.legibility.hides_unsupported_assumptions = True
        self.assertIn("unsupported assumptions must remain visible", validate_simple_inference_pattern_candidate(candidate))

    def test_can_store_shared_subject_pattern(self):
        candidate = create_empty_simple_inference_pattern_candidate(candidate_id="simp:1", pattern_type="shared-subject")
        candidate.shared_subject = True
        self.assertTrue(candidate.shared_subject)
        self.assertEqual("shared-subject", candidate.pattern_type)

    def test_can_store_relation_overlap_pattern(self):
        candidate = create_empty_simple_inference_pattern_candidate(candidate_id="simp:1", pattern_type="relation-overlap")
        candidate.relation_overlap = True
        self.assertTrue(candidate.relation_overlap)
        self.assertEqual("relation-overlap", candidate.pattern_type)

    def test_can_store_contradiction_candidate_pattern(self):
        candidate = create_empty_simple_inference_pattern_candidate(candidate_id="simp:1", pattern_type="contradiction-candidate")
        candidate.contradiction_signal = True
        self.assertTrue(candidate.contradiction_signal)
        self.assertEqual("contradiction-candidate", candidate.pattern_type)

    def test_candidate_is_not_a_proof_step(self):
        data = simple_inference_pattern_candidate_to_dict(create_empty_simple_inference_pattern_candidate(candidate_id="simp:1"))
        self.assertNotIn("proof_step_id", data)
        self.assertNotIn("warrant", data)
        self.assertNotIn("selected_answer", data)

    def test_no_forbidden_files_changed(self):
        proc = subprocess.run(
            ["bash", "-lc", "git diff --name-only && git diff --cached --name-only"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        changed = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertTrue(changed.issubset(ALLOWED_CHANGED), changed)


if __name__ == "__main__":
    unittest.main()
