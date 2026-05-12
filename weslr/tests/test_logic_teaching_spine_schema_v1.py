from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logic_teaching_spine import (  # noqa: E402
    counterexample_candidate_from_dict,
    counterexample_candidate_to_dict,
    create_empty_counterexample_candidate,
    create_empty_proof_step,
    create_empty_proposition_candidate,
    create_empty_teaching_explanation,
    proof_step_from_dict,
    proof_step_to_dict,
    proposition_candidate_from_dict,
    proposition_candidate_to_dict,
    summarize_counterexample_candidate,
    summarize_proof_step,
    summarize_proposition_candidate,
    summarize_teaching_explanation,
    teaching_explanation_from_dict,
    teaching_explanation_to_dict,
    validate_counterexample_candidate,
    validate_proof_step,
    validate_proposition_candidate,
    validate_teaching_explanation,
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
    "weslr/tests/test_logic_teaching_spine_counterexample_schema_v1.py",
    "weslr/tests/test_logic_teaching_spine_teaching_explanation_schema_v1.py",
    "weslr/tests/test_logic_teaching_spine_proposition_helpers_v1.py",
    "weslr/tests/test_logic_teaching_spine_proposition_merge_schema_v1.py",
    "weslr/tests/test_logic_teaching_spine_simple_inference_candidate_schema_v1.py",
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
        candidate = create_empty_proposition_candidate(
            proposition_id="prop:1",
            source_predicate_ids=["pred:1"],
            source_statement_ids=["stmt:1"],
            source_statement_roles=["parsed_premise"],
            proposition_role="parsed_premise",
            proposition_type="binary_relation",
        )
        candidate.subject = "subject"
        candidate.relation = "relates_to"
        candidate.object = "object"
        candidate.human_translation = "Subject relates to object."
        data = proposition_candidate_to_dict(candidate)
        restored = proposition_candidate_from_dict(data)
        self.assertEqual(data, proposition_candidate_to_dict(restored))

    def test_summary_is_redacted(self):
        candidate = create_empty_proposition_candidate(proposition_id="prop:1", proposition_role="premise")
        candidate.subject = "secret_subject"
        candidate.relation = "secret_relation"
        candidate.object = "secret_object"
        candidate.human_translation = "Hidden text"
        summary = summarize_proposition_candidate(candidate)
        self.assertNotIn("subject", summary)
        self.assertNotIn("relation", summary)
        self.assertNotIn("object", summary)
        self.assertNotIn("human_translation", summary)
        self.assertEqual("premise", summary["proposition_role"])

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

    def test_instantiate_empty_counterexample_candidate(self):
        counterexample = create_empty_counterexample_candidate(counterexample_id="counter:1")
        self.assertEqual("counter:1", counterexample.counterexample_id)

    def test_counterexample_safe_anti_gaming_defaults(self):
        counterexample = create_empty_counterexample_candidate()
        self.assertFalse(counterexample.anti_gaming.uses_answer_key)
        self.assertFalse(counterexample.anti_gaming.uses_item_id_as_authority)
        self.assertFalse(counterexample.anti_gaming.uses_answer_position_bias)
        self.assertFalse(counterexample.anti_gaming.claims_official_score)
        self.assertTrue(counterexample.anti_gaming.no_answer_selection)

    def test_counterexample_safe_legibility_defaults(self):
        counterexample = create_empty_counterexample_candidate()
        self.assertFalse(counterexample.legibility.stores_raw_benchmark_text)
        self.assertTrue(counterexample.legibility.redacted_summary_only)
        self.assertFalse(counterexample.legibility.private_symbolic_authority)

    def test_counterexample_roundtrip_to_from_dict(self):
        counterexample = create_empty_counterexample_candidate(
            counterexample_id="counter:1",
            challenged_proposition_id="prop:1",
            challenged_proof_step_id="step:1",
            counterexample_type="possible_world",
        )
        counterexample.possible_world_sketch = "A world where premises hold and the conclusion fails."
        counterexample.violated_assumption = "The conclusion was treated as necessary."
        counterexample.fallacy_pattern_id = "pattern:affirming_consequent"
        counterexample.human_explanation = "This is only a structural counterexample record."
        data = counterexample_candidate_to_dict(counterexample)
        restored = counterexample_candidate_from_dict(data)
        self.assertEqual(data, counterexample_candidate_to_dict(restored))

    def test_counterexample_summary_is_redacted(self):
        counterexample = create_empty_counterexample_candidate(counterexample_id="counter:1")
        counterexample.possible_world_sketch = "secret world"
        counterexample.violated_assumption = "secret assumption"
        counterexample.human_explanation = "secret explanation"
        summary = summarize_counterexample_candidate(counterexample)
        self.assertNotIn("possible_world_sketch", summary)
        self.assertNotIn("violated_assumption", summary)
        self.assertNotIn("human_explanation", summary)

    def test_counterexample_validation_flags_missing_id(self):
        self.assertIn("missing counterexample id", validate_counterexample_candidate(create_empty_counterexample_candidate()))

    def test_counterexample_validation_flags_missing_challenged_target_when_high_confidence(self):
        counterexample = create_empty_counterexample_candidate(counterexample_id="counter:1")
        counterexample.confidence = "high"
        counterexample.human_explanation = "present"
        self.assertIn("missing challenged target for high-confidence counterexample", validate_counterexample_candidate(counterexample))

    def test_counterexample_validation_flags_missing_explanation_when_high_confidence(self):
        counterexample = create_empty_counterexample_candidate(counterexample_id="counter:1")
        counterexample.confidence = "high"
        counterexample.challenged_proposition_id = "prop:1"
        self.assertIn("missing human explanation for high-confidence counterexample", validate_counterexample_candidate(counterexample))

    def test_counterexample_validation_flags_official_score_claim(self):
        counterexample = create_empty_counterexample_candidate(counterexample_id="counter:1")
        counterexample.anti_gaming.claims_official_score = True
        self.assertIn("official-score claim is forbidden", validate_counterexample_candidate(counterexample))

    def test_counterexample_validation_flags_answer_key_use(self):
        counterexample = create_empty_counterexample_candidate(counterexample_id="counter:1")
        counterexample.anti_gaming.uses_answer_key = True
        self.assertIn("answer-key use is forbidden", validate_counterexample_candidate(counterexample))

    def test_counterexample_validation_flags_item_id_authority(self):
        counterexample = create_empty_counterexample_candidate(counterexample_id="counter:1")
        counterexample.anti_gaming.uses_item_id_as_authority = True
        self.assertIn("item-id authority is forbidden", validate_counterexample_candidate(counterexample))

    def test_counterexample_validation_flags_raw_benchmark_storage(self):
        counterexample = create_empty_counterexample_candidate(counterexample_id="counter:1")
        counterexample.legibility.stores_raw_benchmark_text = True
        self.assertIn("raw benchmark storage by default is forbidden", validate_counterexample_candidate(counterexample))

    def test_counterexample_validation_flags_answer_selection(self):
        counterexample = create_empty_counterexample_candidate(counterexample_id="counter:1")
        counterexample.anti_gaming.no_answer_selection = False
        self.assertIn("answer selection must remain disabled", validate_counterexample_candidate(counterexample))

    def test_counterexample_can_reference_challenged_proposition_and_proof_step_structurally(self):
        counterexample = create_empty_counterexample_candidate(
            counterexample_id="counter:1",
            challenged_proposition_id="prop:challenged:1",
            challenged_proof_step_id="step:challenged:1",
            counterexample_type="possible_world",
        )
        self.assertEqual("prop:challenged:1", counterexample.challenged_proposition_id)
        self.assertEqual("step:challenged:1", counterexample.challenged_proof_step_id)

    def test_instantiate_empty_teaching_explanation(self):
        explanation = create_empty_teaching_explanation(explanation_id="explain:1")
        self.assertEqual("explain:1", explanation.explanation_id)

    def test_teaching_explanation_safe_anti_gaming_defaults(self):
        explanation = create_empty_teaching_explanation()
        self.assertFalse(explanation.anti_gaming.uses_answer_key)
        self.assertFalse(explanation.anti_gaming.uses_item_id_as_authority)
        self.assertFalse(explanation.anti_gaming.uses_answer_position_bias)
        self.assertFalse(explanation.anti_gaming.claims_official_score)
        self.assertTrue(explanation.anti_gaming.no_answer_selection)

    def test_teaching_explanation_safe_legibility_defaults(self):
        explanation = create_empty_teaching_explanation()
        self.assertFalse(explanation.legibility.stores_raw_benchmark_text)
        self.assertTrue(explanation.legibility.redacted_summary_only)
        self.assertFalse(explanation.legibility.private_symbolic_authority)

    def test_teaching_explanation_roundtrip_to_from_dict(self):
        explanation = create_empty_teaching_explanation(
            explanation_id="explain:1",
            support_status="supported",
            teaching_mode="standard",
            learner_level="general",
        )
        explanation.source_proposition_ids = ["prop:1"]
        explanation.source_proof_step_ids = ["step:1"]
        explanation.source_counterexample_ids = ["counter:1"]
        explanation.conclusion = "A conclusion"
        explanation.step_by_step_explanation = ["Step 1", "Step 2"]
        explanation.uncertainty_note = "Some uncertainty"
        explanation.human_explanation = "Human teaching explanation"
        data = teaching_explanation_to_dict(explanation)
        restored = teaching_explanation_from_dict(data)
        self.assertEqual(data, teaching_explanation_to_dict(restored))

    def test_teaching_explanation_summary_is_redacted(self):
        explanation = create_empty_teaching_explanation(explanation_id="explain:1")
        explanation.conclusion = "secret conclusion"
        explanation.step_by_step_explanation = ["secret step"]
        explanation.uncertainty_note = "secret uncertainty"
        explanation.human_explanation = "secret explanation"
        summary = summarize_teaching_explanation(explanation)
        self.assertNotIn("conclusion", summary)
        self.assertNotIn("step_by_step_explanation", summary)
        self.assertNotIn("uncertainty_note", summary)
        self.assertNotIn("human_explanation", summary)

    def test_teaching_explanation_validation_flags_missing_id(self):
        self.assertIn("missing explanation id", validate_teaching_explanation(create_empty_teaching_explanation()))

    def test_teaching_explanation_validation_flags_invalid_support_status(self):
        explanation = create_empty_teaching_explanation(explanation_id="explain:1")
        explanation.support_status = "certainly_supported"
        self.assertIn("invalid support status", validate_teaching_explanation(explanation))

    def test_teaching_explanation_validation_flags_invalid_teaching_mode(self):
        explanation = create_empty_teaching_explanation(explanation_id="explain:1")
        explanation.teaching_mode = "wizard_mode"
        self.assertIn("invalid teaching mode", validate_teaching_explanation(explanation))

    def test_teaching_explanation_validation_flags_official_score_claim(self):
        explanation = create_empty_teaching_explanation(explanation_id="explain:1")
        explanation.anti_gaming.claims_official_score = True
        self.assertIn("official-score claim is forbidden", validate_teaching_explanation(explanation))

    def test_teaching_explanation_validation_flags_answer_key_use(self):
        explanation = create_empty_teaching_explanation(explanation_id="explain:1")
        explanation.anti_gaming.uses_answer_key = True
        self.assertIn("answer-key use is forbidden", validate_teaching_explanation(explanation))

    def test_teaching_explanation_validation_flags_item_id_authority(self):
        explanation = create_empty_teaching_explanation(explanation_id="explain:1")
        explanation.anti_gaming.uses_item_id_as_authority = True
        self.assertIn("item-id authority is forbidden", validate_teaching_explanation(explanation))

    def test_teaching_explanation_validation_flags_raw_benchmark_storage(self):
        explanation = create_empty_teaching_explanation(explanation_id="explain:1")
        explanation.legibility.stores_raw_benchmark_text = True
        self.assertIn("raw benchmark storage by default is forbidden", validate_teaching_explanation(explanation))

    def test_teaching_explanation_validation_flags_answer_selection(self):
        explanation = create_empty_teaching_explanation(explanation_id="explain:1")
        explanation.anti_gaming.no_answer_selection = False
        self.assertIn("answer selection must remain disabled", validate_teaching_explanation(explanation))

    def test_teaching_explanation_supports_spock_mode_structurally(self):
        explanation = create_empty_teaching_explanation(explanation_id="explain:1", teaching_mode="spock")
        self.assertEqual("spock", explanation.teaching_mode)

    def test_teaching_explanation_supports_socratic_hint_mode_structurally(self):
        explanation = create_empty_teaching_explanation(explanation_id="explain:1", teaching_mode="socratic_hint")
        self.assertEqual("socratic_hint", explanation.teaching_mode)

    def test_teaching_explanation_can_reference_propositions_proof_steps_and_counterexamples_structurally(self):
        explanation = create_empty_teaching_explanation(explanation_id="explain:1")
        explanation.source_proposition_ids = ["prop:1", "prop:2"]
        explanation.source_proof_step_ids = ["step:1"]
        explanation.source_counterexample_ids = ["counter:1"]
        self.assertEqual(["prop:1", "prop:2"], explanation.source_proposition_ids)
        self.assertEqual(["step:1"], explanation.source_proof_step_ids)
        self.assertEqual(["counter:1"], explanation.source_counterexample_ids)

    def test_existing_teaching_spine_design_doc_remains_present(self):
        design_doc = ROOT / "docs" / "WESLR_LOGIC_TEACHING_SPINE_V1.md"
        text = design_doc.read_text(encoding="utf-8")
        self.assertIn("WESLR Logic Teaching Spine V1", text)
        self.assertIn("design_only", text)

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
