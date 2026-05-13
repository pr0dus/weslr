from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logic_teaching_spine import (  # noqa: E402
    ProofStep,
    TeachingExplanation,
    create_teaching_explanation_from_proof_step,
    create_teaching_explanations_from_proof_steps,
    summarize_teaching_explanation,
    summarize_teaching_explanation_generation_diagnostics,
)


FORBIDDEN_CHANGED = {
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
}
ALLOWED_CHANGED = {
    "weslr/logic_teaching_spine.py",
    "weslr/tests/test_teaching_explanation_schema_alignment_v1.py",
    "weslr/tests/test_teaching_explanation_helpers_v1.py",
}


class TeachingExplanationHelpersV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        proc = subprocess.run(
            ["bash", "-lc", "git diff --name-only && git diff --cached --name-only && git ls-files --others --exclude-standard"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        return {line.strip() for line in proc.stdout.splitlines() if line.strip()}

    def proof_step(self, **kwargs) -> ProofStep:
        data = {
            "proof_step_id": "proof_step:1",
            "source_context_binding_ids": ["ctx:1"],
            "source_premise_proposition_ids": ["premise:1", "premise:2"],
            "source_choice_proposition_ids": ["choice:1"],
            "reasoning_relation": "apply_condition",
            "inference_pattern": "modus_ponens",
            "support_status": "supported",
            "source_proposition_ids": ["premise:1", "premise:2"],
            "target_proposition_id": "choice:1",
            "inference_pattern_id": "modus_ponens",
            "validity_status": "valid",
            "confidence": "medium",
            "human_explanation": "Redacted structural proof step only.",
        }
        data.update(kwargs)
        return ProofStep(**data)

    def explanation(self, **kwargs) -> TeachingExplanation:
        return create_teaching_explanation_from_proof_step(self.proof_step(**kwargs), teaching_mode="technical")

    def test_creates_explanation_from_supported_proof_step(self):
        explanation = self.explanation()
        self.assertIsInstance(explanation, TeachingExplanation)
        self.assertEqual("supported", explanation.support_status)
        self.assertTrue(explanation.human_explanation)

    def test_creates_explanation_from_rule_application_proof_step(self):
        explanation = self.explanation(support_status="rule_application_supported", inference_pattern="modus_tollens")
        self.assertEqual("rule_application_supported", explanation.support_status)
        self.assertEqual("modus_tollens", explanation.pattern_name)

    def test_creates_explanation_from_counterexample_proof_step(self):
        explanation = self.explanation(support_status="counterexample_supported", requires_counterexample=True)
        self.assertTrue(explanation.counterexample_note)
        self.assertEqual(1, summarize_teaching_explanation_generation_diagnostics([explanation])["counterexample_note_count"])

    def test_creates_explanation_from_fallacy_shaped_proof_step(self):
        step = self.proof_step(
            support_status="unsupported",
            inference_pattern="affirming_consequent",
            conditional_form_mapping={"form_label": "affirming_consequent", "support_assessment": "fallacy_shaped", "fallacy_shaped": True},
            unsupported_gaps=["recognized_fallacy_shaped_pattern"],
        )
        explanation = create_teaching_explanation_from_proof_step(step, teaching_mode="academic")
        self.assertEqual("affirming the consequent", explanation.fallacy_name)
        self.assertIn("recognized_fallacy_shaped_pattern", explanation.unsupported_gaps)

    def test_creates_explanation_from_ambiguous_proof_step_without_pretending_certainty(self):
        explanation = self.explanation(support_status="ambiguous", validity_status="ambiguous", unsupported_gaps=["slot_missing"])
        self.assertEqual("ambiguous", explanation.support_status)
        self.assertIn("slot_missing", explanation.unsupported_gaps)
        self.assertIn("not upgraded to certainty", explanation.uncertainty_note)

    def test_preserves_proof_step_refs(self):
        self.assertEqual(["proof_step:1"], self.explanation().source_proof_step_ids)

    def test_preserves_context_refs(self):
        self.assertEqual(["ctx:1"], self.explanation().source_context_binding_ids)

    def test_preserves_unsupported_gaps(self):
        explanation = self.explanation(unsupported_gaps=["gap:visible"])
        self.assertIn("gap:visible", explanation.unsupported_gaps)

    def test_beginner_mode_works(self):
        self.assertEqual("beginner", create_teaching_explanation_from_proof_step(self.proof_step(), teaching_mode="beginner").teaching_mode)

    def test_technical_mode_works(self):
        self.assertEqual("technical", create_teaching_explanation_from_proof_step(self.proof_step(), teaching_mode="technical").teaching_mode)

    def test_academic_mode_works(self):
        self.assertEqual("academic", create_teaching_explanation_from_proof_step(self.proof_step(), teaching_mode="academic").teaching_mode)

    def test_spock_mode_works(self):
        self.assertEqual("spock", create_teaching_explanation_from_proof_step(self.proof_step(), teaching_mode="spock").teaching_mode)

    def test_operator_audit_mode_works(self):
        explanation = create_teaching_explanation_from_proof_step(self.proof_step(unsupported_gaps=["gap:visible"]), teaching_mode="operator_audit")
        self.assertEqual("operator_audit", explanation.teaching_mode)
        self.assertIn("Unsupported gap count", " ".join(explanation.step_by_step_explanation))

    def test_summary_is_redacted(self):
        summary = summarize_teaching_explanation_generation_diagnostics([self.explanation()])
        text = str(summary).lower()
        self.assertEqual(1, summary["teaching_explanation_count"])
        for forbidden in ["source_premise_proposition_ids", "source_choice_proposition_ids", "answer_key", "correct_answer", "raw_text"]:
            self.assertNotIn(forbidden, text)

    def test_no_answer_selection(self):
        summary = summarize_teaching_explanation_generation_diagnostics([self.explanation()])
        self.assertFalse(summary["answer_selection_enabled"])
        self.assertTrue(self.explanation().anti_gaming.no_answer_selection)

    def test_no_truth_soundness_claim(self):
        summary = summarize_teaching_explanation_generation_diagnostics([self.explanation()])
        self.assertFalse(summary["truth_claim_made"])
        self.assertNotIn("sound", str(summarize_teaching_explanation(self.explanation())).lower())

    def test_no_official_score(self):
        self.assertFalse(summarize_teaching_explanation_generation_diagnostics([self.explanation()])["official_score_claimed"])
        self.assertFalse(self.explanation().anti_gaming.claims_official_score)

    def test_no_answer_key_use(self):
        self.assertFalse(self.explanation().anti_gaming.uses_answer_key)

    def test_no_item_id_authority(self):
        self.assertFalse(self.explanation().anti_gaming.uses_item_id_as_authority)

    def test_maps_list_without_dropping_ambiguous_or_unsupported(self):
        steps = [self.proof_step(proof_step_id="proof_step:supported"), self.proof_step(proof_step_id="proof_step:ambiguous", support_status="ambiguous")]
        explanations = create_teaching_explanations_from_proof_steps(steps, teaching_mode="beginner")
        self.assertEqual(2, len(explanations))
        self.assertIn("ambiguous", {explanation.support_status for explanation in explanations})

    def test_schema_alignment_tests_still_pass(self):
        explanation = self.explanation()
        summary = summarize_teaching_explanation(explanation)
        self.assertEqual("technical", summary["teaching_mode"])
        self.assertTrue(summary["source_proof_step_count"])
        self.assertTrue(summary["anti_gaming_safe"])
        self.assertTrue(summary["legibility_safe"])

    def test_release_gate_and_check_pass(self):
        summary = summarize_teaching_explanation_generation_diagnostics([self.explanation()])
        self.assertFalse(summary["answer_selection_enabled"])
        self.assertFalse(summary["truth_claim_made"])
        self.assertFalse(summary["official_score_claimed"])
        self.assertTrue(summary["anti_gaming_safe"])
        self.assertTrue(summary["legibility_safe"])

    def test_no_forbidden_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
