from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logic_teaching_spine import (  # noqa: E402
    create_empty_proof_step,
    create_empty_proposition_candidate,
    proof_step_from_dict,
    proof_step_to_dict,
    proposition_candidate_from_dict,
    proposition_candidate_to_dict,
    summarize_proof_step,
    summarize_proposition_candidate,
    validate_proof_step,
    validate_proposition_candidate,
)

FORBIDDEN_CHANGED = {
    "weslr/logical_form_normalizer.py",
    "weslr/formal_logic_parser.py",
    "weslr/formal_logic_solver.py",
    "weslr/mcq_answer_formatting.py",
    "weslr/evals/official_mcq_adapter.py",
}
ALLOWED_CHANGED = {
    "weslr/logic_teaching_spine.py",
    "weslr/tests/test_logic_teaching_spine_schema_v1.py",
    "weslr/tests/test_logic_teaching_spine_inference_pattern_schema_v1.py",
}


class LogicTeachingSpineSchemaV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        proc = subprocess.run(
            ["bash", "-lc", "git diff --name-only && git diff --cached --name-only"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        return {line.strip() for line in proc.stdout.splitlines() if line.strip()}

    def run_direct(self, script: str) -> str:
        proc = subprocess.run(["bash", "-lc", script], cwd=str(ROOT), capture_output=True, text=True, check=True)
        return proc.stdout + proc.stderr

    def test_schema_can_instantiate(self):
        candidate = create_empty_proposition_candidate(proposition_id="prop:1")
        self.assertEqual("prop:1", candidate.proposition_id)

    def test_safe_defaults(self):
        candidate = create_empty_proposition_candidate()
        self.assertFalse(candidate.anti_gaming.uses_answer_key)
        self.assertFalse(candidate.anti_gaming.uses_item_id_as_authority)
        self.assertFalse(candidate.anti_gaming.uses_answer_position_bias)
        self.assertFalse(candidate.anti_gaming.claims_official_score)
        self.assertFalse(candidate.anti_gaming.benchmark_specific_tuning)
        self.assertFalse(candidate.legibility.stores_raw_benchmark_text)
        self.assertTrue(candidate.anti_gaming.no_answer_selection)
        self.assertTrue(candidate.legibility.redacted_summary_only)

    def test_validation_flags_answer_key_use(self):
        candidate = create_empty_proposition_candidate(proposition_id="prop:1")
        candidate.anti_gaming.uses_answer_key = True
        self.assertIn("answer-key use is forbidden", validate_proposition_candidate(candidate))

    def test_validation_flags_item_id_authority(self):
        candidate = create_empty_proposition_candidate(proposition_id="prop:1")
        candidate.anti_gaming.uses_item_id_as_authority = True
        self.assertIn("item-id authority is forbidden", validate_proposition_candidate(candidate))

    def test_validation_flags_official_score_claim(self):
        candidate = create_empty_proposition_candidate(proposition_id="prop:1")
        candidate.anti_gaming.claims_official_score = True
        self.assertIn("official-score claim is forbidden", validate_proposition_candidate(candidate))

    def test_validation_flags_raw_text_storage_by_default(self):
        candidate = create_empty_proposition_candidate(proposition_id="prop:1")
        candidate.legibility.stores_raw_benchmark_text = True
        self.assertIn("raw benchmark storage by default is forbidden", validate_proposition_candidate(candidate))

    def test_validation_flags_private_symbolic_authority(self):
        candidate = create_empty_proposition_candidate(proposition_id="prop:1")
        candidate.legibility.private_symbolic_authority = True
        self.assertIn("private symbolic authority is forbidden", validate_proposition_candidate(candidate))

    def test_validation_flags_missing_proposition_id(self):
        candidate = create_empty_proposition_candidate()
        self.assertIn("missing proposition id", validate_proposition_candidate(candidate))

    def test_validation_flags_missing_human_translation_when_confidence_is_high(self):
        candidate = create_empty_proposition_candidate(proposition_id="prop:1")
        candidate.confidence = "high"
        self.assertIn("missing human translation for high-confidence proposition", validate_proposition_candidate(candidate))

    def test_roundtrip_to_from_dict(self):
        candidate = create_empty_proposition_candidate(proposition_id="prop:1", source_predicate_ids=["pred:1"], proposition_type="binary_relation")
        candidate.subject = "subject"
        candidate.relation = "relates_to"
        candidate.object = "object"
        candidate.human_translation = "Subject relates to object."
        data = proposition_candidate_to_dict(candidate)
        restored = proposition_candidate_from_dict(data)
        self.assertEqual(data, proposition_candidate_to_dict(restored))

    def test_summary_is_redacted(self):
        candidate = create_empty_proposition_candidate(proposition_id="prop:1")
        candidate.subject = "secret_subject"
        candidate.relation = "secret_relation"
        candidate.object = "secret_object"
        candidate.human_translation = "Hidden text"
        summary = summarize_proposition_candidate(candidate)
        self.assertNotIn("subject", summary)
        self.assertNotIn("relation", summary)
        self.assertNotIn("object", summary)
        self.assertNotIn("human_translation", summary)

    def test_summary_does_not_contain_raw_question_choices_answers(self):
        summary_text = str(summarize_proposition_candidate(create_empty_proposition_candidate(proposition_id="prop:1")))
        for snippet in ["question", "choices", "answer", "correct_answer", "raw_text"]:
            self.assertNotIn(snippet, summary_text)

    def test_no_answer_selection_field_exists(self):
        data = proposition_candidate_to_dict(create_empty_proposition_candidate(proposition_id="prop:1"))
        self.assertNotIn("answer_selection", data)
        self.assertNotIn("selected_answer", data)

    def test_instantiate_empty_proof_step(self):
        proof_step = create_empty_proof_step(proof_step_id="step:1")
        self.assertEqual("step:1", proof_step.proof_step_id)

    def test_proof_step_safe_anti_gaming_defaults(self):
        proof_step = create_empty_proof_step()
        self.assertFalse(proof_step.anti_gaming.uses_answer_key)
        self.assertFalse(proof_step.anti_gaming.uses_item_id_as_authority)
        self.assertFalse(proof_step.anti_gaming.uses_answer_position_bias)
        self.assertFalse(proof_step.anti_gaming.claims_official_score)
        self.assertTrue(proof_step.anti_gaming.no_answer_selection)

    def test_proof_step_safe_legibility_defaults(self):
        proof_step = create_empty_proof_step()
        self.assertFalse(proof_step.legibility.stores_raw_benchmark_text)
        self.assertTrue(proof_step.legibility.redacted_summary_only)
        self.assertFalse(proof_step.legibility.private_symbolic_authority)

    def test_proof_step_roundtrip_to_from_dict(self):
        proof_step = create_empty_proof_step(
            proof_step_id="step:1",
            source_proposition_ids=["prop:1", "prop:2"],
            target_proposition_id="prop:3",
            inference_pattern_id="pattern:modus_ponens",
            validity_status="valid",
        )
        proof_step.warrant = "Structural warrant only."
        proof_step.human_explanation = "This proof step is described structurally."
        data = proof_step_to_dict(proof_step)
        restored = proof_step_from_dict(data)
        self.assertEqual(data, proof_step_to_dict(restored))

    def test_proof_step_summary_is_redacted(self):
        proof_step = create_empty_proof_step(proof_step_id="step:1")
        proof_step.warrant = "secret warrant"
        proof_step.human_explanation = "secret explanation"
        summary = summarize_proof_step(proof_step)
        self.assertNotIn("warrant", summary)
        self.assertNotIn("human_explanation", summary)

    def test_proof_step_validation_flags_missing_id(self):
        self.assertIn("missing proof step id", validate_proof_step(create_empty_proof_step()))

    def test_proof_step_validation_flags_invalid_validity_status(self):
        proof_step = create_empty_proof_step(proof_step_id="step:1")
        proof_step.validity_status = "definitely_right"
        self.assertIn("invalid validity status", validate_proof_step(proof_step))

    def test_proof_step_validation_flags_missing_warrant_when_high_confidence(self):
        proof_step = create_empty_proof_step(proof_step_id="step:1")
        proof_step.confidence = "high"
        proof_step.human_explanation = "present"
        self.assertIn("missing warrant for high-confidence proof step", validate_proof_step(proof_step))

    def test_proof_step_validation_flags_missing_explanation_when_high_confidence(self):
        proof_step = create_empty_proof_step(proof_step_id="step:1")
        proof_step.confidence = "high"
        proof_step.warrant = "present"
        self.assertIn("missing human explanation for high-confidence proof step", validate_proof_step(proof_step))

    def test_proof_step_validation_flags_official_score_claim(self):
        proof_step = create_empty_proof_step(proof_step_id="step:1")
        proof_step.anti_gaming.claims_official_score = True
        self.assertIn("official-score claim is forbidden", validate_proof_step(proof_step))

    def test_proof_step_validation_flags_answer_key_use(self):
        proof_step = create_empty_proof_step(proof_step_id="step:1")
        proof_step.anti_gaming.uses_answer_key = True
        self.assertIn("answer-key use is forbidden", validate_proof_step(proof_step))

    def test_proof_step_validation_flags_item_id_authority(self):
        proof_step = create_empty_proof_step(proof_step_id="step:1")
        proof_step.anti_gaming.uses_item_id_as_authority = True
        self.assertIn("item-id authority is forbidden", validate_proof_step(proof_step))

    def test_proof_step_validation_flags_raw_benchmark_storage(self):
        proof_step = create_empty_proof_step(proof_step_id="step:1")
        proof_step.legibility.stores_raw_benchmark_text = True
        self.assertIn("raw benchmark storage by default is forbidden", validate_proof_step(proof_step))

    def test_proof_step_validation_flags_answer_selection(self):
        proof_step = create_empty_proof_step(proof_step_id="step:1")
        proof_step.anti_gaming.no_answer_selection = False
        self.assertIn("answer selection must remain disabled", validate_proof_step(proof_step))

    def test_proof_step_can_reference_proposition_ids_and_inference_pattern_id_structurally(self):
        proof_step = create_empty_proof_step(
            proof_step_id="step:1",
            source_proposition_ids=["prop:premise:1", "prop:premise:2"],
            target_proposition_id="prop:target:1",
            inference_pattern_id="pattern:modus_ponens",
            validity_status="valid",
        )
        self.assertEqual(["prop:premise:1", "prop:premise:2"], proof_step.source_proposition_ids)
        self.assertEqual("prop:target:1", proof_step.target_proposition_id)
        self.assertEqual("pattern:modus_ponens", proof_step.inference_pattern_id)

    def test_existing_teaching_spine_design_test_passes(self):
        output = self.run_direct("python3 weslr/tests/test_logic_teaching_spine_design_v1.py")
        self.assertIn("OK", output)

    def test_release_gate_and_check_pass(self):
        output = self.run_direct("python3 weslr/tests/release_gate_v1.py && bash scripts/weslr_release_check.sh")
        self.assertIn("WESLR_RELEASE_GATE_V1_OK", output)
        self.assertIn("WESLR_RELEASE_CHECK_OK", output)

    def test_no_forbidden_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertTrue(changed.issubset(ALLOWED_CHANGED))


if __name__ == "__main__":
    unittest.main()
