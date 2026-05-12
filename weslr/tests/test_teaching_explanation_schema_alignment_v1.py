from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logic_teaching_spine import (  # noqa: E402
    TeachingExplanation,
    create_empty_teaching_explanation,
    summarize_teaching_explanation,
    teaching_explanation_from_dict,
    teaching_explanation_to_dict,
    validate_teaching_explanation,
)


TEACHING_MODES = ["beginner", "technical", "academic", "spock", "operator_audit", "unknown"]
SUPPORT_STATUSES = [
    "supported",
    "contradicted",
    "counterexample_supported",
    "rule_application_supported",
    "template_completed",
    "ambiguous",
    "unsupported",
    "unknown",
]
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
    "weslr/tests/test_logic_teaching_spine_schema_v1.py",
    "weslr/tests/test_teaching_explanation_schema_alignment_v1.py",
}


class TeachingExplanationSchemaAlignmentV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        proc = subprocess.run(
            ["bash", "-lc", "git diff --name-only && git diff --cached --name-only && git ls-files --others --exclude-standard"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        return {line.strip() for line in proc.stdout.splitlines() if line.strip()}

    def valid_explanation(self) -> TeachingExplanation:
        explanation = create_empty_teaching_explanation(
            explanation_id="teaching:1",
            source_proof_step_ids=["proof_step:1"],
            source_context_binding_ids=["ctx:1"],
            source_proposition_ids=["prop:1"],
            support_status="supported",
            teaching_mode="technical",
            core_claim="Redacted structural claim only.",
            why_it_follows_or_fails="Redacted structural reason only.",
            pattern_name="modus ponens",
            confidence="medium",
        )
        explanation.human_explanation = "Redacted human-facing explanation only."
        explanation.unsupported_gaps = ["gap:visible"]
        return explanation

    def test_schema_imports(self):
        self.assertIsNotNone(TeachingExplanation)
        self.assertTrue(callable(create_empty_teaching_explanation))

    def test_empty_teaching_explanation_instantiates(self):
        explanation = create_empty_teaching_explanation(explanation_id="teaching:empty")
        self.assertEqual("teaching:empty", explanation.explanation_id)
        self.assertEqual("unknown", explanation.teaching_mode)
        self.assertEqual("low", explanation.confidence)

    def test_safe_anti_gaming_defaults(self):
        explanation = create_empty_teaching_explanation()
        self.assertFalse(explanation.anti_gaming.uses_answer_key)
        self.assertFalse(explanation.anti_gaming.uses_item_id_as_authority)
        self.assertFalse(explanation.anti_gaming.uses_answer_position_bias)
        self.assertFalse(explanation.anti_gaming.claims_official_score)
        self.assertFalse(explanation.anti_gaming.benchmark_specific_tuning)
        self.assertTrue(explanation.anti_gaming.no_answer_selection)

    def test_safe_legibility_defaults(self):
        explanation = create_empty_teaching_explanation()
        self.assertTrue(explanation.legibility.human_translation_available)
        self.assertTrue(explanation.legibility.redacted_summary_only)
        self.assertFalse(explanation.legibility.stores_raw_benchmark_text)
        self.assertFalse(explanation.legibility.private_symbolic_authority)
        self.assertFalse(explanation.legibility.hides_unsupported_assumptions)

    def test_all_teaching_modes_validate(self):
        for mode in TEACHING_MODES:
            explanation = create_empty_teaching_explanation(explanation_id=f"teaching:{mode}", teaching_mode=mode)
            self.assertNotIn("invalid teaching mode", validate_teaching_explanation(explanation))

    def test_all_support_statuses_validate(self):
        for status in SUPPORT_STATUSES:
            explanation = create_empty_teaching_explanation(explanation_id=f"teaching:{status}", support_status=status)
            self.assertNotIn("invalid support status", validate_teaching_explanation(explanation))

    def test_invalid_teaching_mode_fails(self):
        explanation = create_empty_teaching_explanation(explanation_id="teaching:bad", teaching_mode="wizard")
        self.assertIn("invalid teaching mode", validate_teaching_explanation(explanation))

    def test_invalid_support_status_fails(self):
        explanation = create_empty_teaching_explanation(explanation_id="teaching:bad", support_status="proven_true")
        self.assertIn("invalid support status", validate_teaching_explanation(explanation))

    def test_invalid_confidence_fails(self):
        explanation = create_empty_teaching_explanation(explanation_id="teaching:bad", confidence="certain")
        self.assertIn("invalid confidence", validate_teaching_explanation(explanation))

    def test_missing_explanation_id_fails(self):
        self.assertIn("missing explanation id", validate_teaching_explanation(create_empty_teaching_explanation()))

    def test_high_confidence_missing_proof_step_refs_fails(self):
        explanation = create_empty_teaching_explanation(explanation_id="teaching:high", confidence="high")
        explanation.human_explanation = "Redacted explanation."
        self.assertIn("missing proof step refs for high-confidence teaching explanation", validate_teaching_explanation(explanation))

    def test_high_confidence_missing_explanation_fails(self):
        explanation = create_empty_teaching_explanation(
            explanation_id="teaching:high",
            source_proof_step_ids=["proof_step:1"],
            confidence="high",
        )
        self.assertIn("missing human explanation for high-confidence teaching explanation", validate_teaching_explanation(explanation))

    def test_unsupported_gaps_remain_visible(self):
        explanation = self.valid_explanation()
        self.assertIn("gap:visible", explanation.unsupported_gaps)
        explanation.legibility.hides_unsupported_assumptions = True
        errors = validate_teaching_explanation(explanation)
        self.assertIn("unsupported gaps must remain visible", errors)
        self.assertIn("unsupported assumptions must remain visible", errors)

    def test_answer_key_use_fails(self):
        explanation = create_empty_teaching_explanation(explanation_id="teaching:1")
        explanation.anti_gaming.uses_answer_key = True
        self.assertIn("answer-key use is forbidden", validate_teaching_explanation(explanation))

    def test_item_id_authority_fails(self):
        explanation = create_empty_teaching_explanation(explanation_id="teaching:1")
        explanation.anti_gaming.uses_item_id_as_authority = True
        self.assertIn("item-id authority is forbidden", validate_teaching_explanation(explanation))

    def test_answer_position_bias_fails(self):
        explanation = create_empty_teaching_explanation(explanation_id="teaching:1")
        explanation.anti_gaming.uses_answer_position_bias = True
        self.assertIn("answer-position bias is forbidden", validate_teaching_explanation(explanation))

    def test_benchmark_specific_tuning_fails(self):
        explanation = create_empty_teaching_explanation(explanation_id="teaching:1")
        explanation.anti_gaming.benchmark_specific_tuning = True
        self.assertIn("benchmark-specific tuning is forbidden", validate_teaching_explanation(explanation))

    def test_answer_selection_enabled_fails(self):
        explanation = create_empty_teaching_explanation(explanation_id="teaching:1")
        explanation.anti_gaming.no_answer_selection = False
        self.assertIn("answer selection must remain disabled", validate_teaching_explanation(explanation))

    def test_official_score_claim_fails(self):
        explanation = create_empty_teaching_explanation(explanation_id="teaching:1")
        explanation.anti_gaming.claims_official_score = True
        self.assertIn("official-score claim is forbidden", validate_teaching_explanation(explanation))

    def test_raw_benchmark_storage_fails(self):
        explanation = create_empty_teaching_explanation(explanation_id="teaching:1")
        explanation.legibility.stores_raw_benchmark_text = True
        self.assertIn("raw benchmark storage by default is forbidden", validate_teaching_explanation(explanation))

    def test_private_symbolic_authority_fails(self):
        explanation = create_empty_teaching_explanation(explanation_id="teaching:1")
        explanation.legibility.private_symbolic_authority = True
        self.assertIn("private symbolic authority is forbidden", validate_teaching_explanation(explanation))

    def test_to_from_dict_roundtrip_works(self):
        explanation = self.valid_explanation()
        explanation.fallacy_name = ""
        explanation.counterexample_note = "No counterexample note needed."
        explanation.step_by_step_explanation = ["Redacted structural step."]
        data = teaching_explanation_to_dict(explanation)
        restored = teaching_explanation_from_dict(data)
        self.assertEqual(data, teaching_explanation_to_dict(restored))

    def test_summary_is_redacted(self):
        explanation = self.valid_explanation()
        explanation.core_claim = "secret core claim"
        explanation.why_it_follows_or_fails = "secret reason"
        explanation.human_explanation = "secret explanation"
        summary = summarize_teaching_explanation(explanation)
        self.assertNotIn("core_claim", summary)
        self.assertNotIn("why_it_follows_or_fails", summary)
        self.assertNotIn("human_explanation", summary)
        self.assertEqual(1, summary["source_proof_step_count"])
        self.assertEqual(1, summary["source_context_binding_count"])

    def test_summary_does_not_contain_forbidden_raw_fields(self):
        summary_text = str(summarize_teaching_explanation(self.valid_explanation())).lower()
        for forbidden in ["question", "choice", "answer_key", "correct_answer", "raw_text", "official_score"]:
            self.assertNotIn(forbidden, summary_text)

    def test_design_test_still_passes(self):
        proc = subprocess.run(
            ["python3", "weslr/tests/test_teaching_explanation_design_v1.py"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("OK", proc.stdout + proc.stderr)

    def test_release_gate_and_check_pass(self):
        proc = subprocess.run(
            ["bash", "-lc", "python3 weslr/tests/release_gate_v1.py && bash scripts/weslr_release_check.sh"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        output = proc.stdout + proc.stderr
        self.assertIn("WESLR_RELEASE_GATE_V1_OK", output)
        self.assertIn("WESLR_RELEASE_CHECK_OK", output)

    def test_no_forbidden_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
