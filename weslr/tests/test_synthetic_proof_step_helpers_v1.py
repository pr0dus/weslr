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
    create_empty_proof_step_candidate,
    create_proof_step_from_candidate,
    create_proof_steps_from_candidates,
    summarize_proof_step,
    summarize_proof_step_generation_diagnostics,
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
    "weslr/tests/test_teaching_explanation_helpers_v1.py",
    "weslr/tests/test_logic_teaching_spine_schema_v1.py",
    "weslr/tests/test_proof_step_candidate_helpers_v1.py",
    "weslr/tests/test_synthetic_proof_step_helpers_v1.py",
    "weslr/tests/test_teaching_explanation_fallacy_mapping_helpers_v1.py",
}


class SyntheticProofStepHelpersV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        proc = subprocess.run(
            ["bash", "-lc", "git diff --name-only && git diff --cached --name-only && git ls-files --others --exclude-standard"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        return {line.strip() for line in proc.stdout.splitlines() if line.strip()}

    def candidate(self, candidate_type: str = "support_step_candidate", **kwargs):
        data = {
            "candidate_id": f"candidate:{candidate_type}",
            "source_context_binding_ids": ["ctx:1"],
            "source_premise_proposition_ids": ["premise:1", "premise:2"],
            "source_choice_proposition_ids": ["choice:1"],
            "candidate_type": candidate_type,
            "expected_reasoning_relation": "support",
            "inference_pattern_hint": "supports_target",
            "support_status": "candidate_only",
        }
        unsupported_gaps = list(kwargs.pop("unsupported_gaps", []))
        data.update(kwargs)
        candidate = create_empty_proof_step_candidate(**data)
        candidate.confidence = "medium"
        candidate.unsupported_gaps = unsupported_gaps
        candidate.human_explanation = "Redacted structural candidate explanation only."
        return candidate

    def test_creates_proof_step_from_support_candidate(self):
        step = create_proof_step_from_candidate(self.candidate("support_step_candidate"))
        self.assertIsInstance(step, ProofStep)
        self.assertEqual("supported", step.support_status)

    def test_creates_proof_step_from_rule_application_candidate(self):
        step = create_proof_step_from_candidate(
            self.candidate("rule_application_candidate", expected_reasoning_relation="apply_condition", inference_pattern_hint="apply_condition")
        )
        self.assertEqual("rule_application_supported", step.support_status)

    def test_creates_proof_step_from_counterexample_candidate(self):
        step = create_proof_step_from_candidate(
            self.candidate("counterexample_step_candidate", expected_reasoning_relation="provide_counterexample", inference_pattern_hint="tests_target")
        )
        self.assertEqual("counterexample_supported", step.support_status)
        self.assertTrue(step.requires_counterexample)

    def test_creates_proof_step_from_template_completion_candidate(self):
        step = create_proof_step_from_candidate(
            self.candidate("template_completion_candidate", expected_reasoning_relation="complete_template", inference_pattern_hint="complete_template")
        )
        self.assertEqual("template_completed", step.support_status)

    def test_unsupported_candidate_stays_visible_as_unsupported_or_ambiguous(self):
        step = create_proof_step_from_candidate(
            self.candidate(
                "unsupported_step_candidate",
                expected_reasoning_relation="unknown",
                inference_pattern_hint="",
                support_status="unsupported",
                unsupported_gaps=["gap:visible"],
            )
        )
        self.assertIn(step.support_status, {"unsupported", "ambiguous"})
        self.assertIn("gap:visible", step.unsupported_gaps)

    def test_preserves_source_candidate_id(self):
        step = create_proof_step_from_candidate(self.candidate(candidate_id="candidate:preserve"))
        self.assertEqual("candidate:preserve", step.source_candidate_id)

    def test_preserves_context_binding_ids(self):
        step = create_proof_step_from_candidate(self.candidate(source_context_binding_ids=["ctx:a", "ctx:b"]))
        self.assertEqual(["ctx:a", "ctx:b"], step.source_context_binding_ids)

    def test_preserves_premise_proposition_ids(self):
        step = create_proof_step_from_candidate(self.candidate(source_premise_proposition_ids=["premise:a", "premise:b"]))
        self.assertEqual(["premise:a", "premise:b"], step.source_premise_proposition_ids)

    def test_preserves_choice_proposition_ids(self):
        step = create_proof_step_from_candidate(self.candidate(source_choice_proposition_ids=["choice:a", "choice:b"]))
        self.assertEqual(["choice:a", "choice:b"], step.source_choice_proposition_ids)

    def test_preserves_unsupported_gaps(self):
        step = create_proof_step_from_candidate(self.candidate(unsupported_gaps=["gap:visible"]))
        self.assertIn("gap:visible", step.unsupported_gaps)

    def test_preserves_human_explanation(self):
        step = create_proof_step_from_candidate(self.candidate())
        self.assertEqual("Redacted structural candidate explanation only.", step.human_explanation)

    def test_does_not_select_answers(self):
        step = create_proof_step_from_candidate(self.candidate())
        self.assertTrue(step.anti_gaming.no_answer_selection)
        self.assertFalse(summarize_proof_step_generation_diagnostics([step])["answer_selection_enabled"])

    def test_does_not_claim_truth(self):
        step = create_proof_step_from_candidate(self.candidate())
        summary = summarize_proof_step_generation_diagnostics([step])
        self.assertFalse(summary["truth_claim_made"])
        self.assertNotIn("correct", str(summarize_proof_step(step)).lower())

    def test_does_not_use_answer_key(self):
        self.assertFalse(create_proof_step_from_candidate(self.candidate()).anti_gaming.uses_answer_key)

    def test_does_not_use_item_id_as_authority(self):
        self.assertFalse(create_proof_step_from_candidate(self.candidate()).anti_gaming.uses_item_id_as_authority)

    def test_does_not_generate_proof_chain(self):
        steps = create_proof_steps_from_candidates([self.candidate(), self.candidate(candidate_id="candidate:2")])
        summary = summarize_proof_step_generation_diagnostics(steps)
        self.assertFalse(summary["proof_chain_generated"])

    def test_does_not_generate_teaching_explanation(self):
        summary = summarize_proof_step_generation_diagnostics([create_proof_step_from_candidate(self.candidate())])
        self.assertFalse(summary["teaching_explanation_generated"])

    def test_summary_is_redacted(self):
        step = create_proof_step_from_candidate(
            self.candidate(
                source_premise_proposition_ids=["premise:secret"],
                source_choice_proposition_ids=["choice:secret"],
                unsupported_gaps=["hidden raw gap"],
            )
        )
        summary = summarize_proof_step_generation_diagnostics([step])
        text = str(summary).lower()
        self.assertEqual(1, summary["proof_step_count"])
        for forbidden in ["source_premise_proposition_ids", "source_choice_proposition_ids", "answer_key", "correct_answer", "raw_text"]:
            self.assertNotIn(forbidden, text)

    def test_existing_proof_step_schema_tests_still_pass(self):
        proc = subprocess.run(
            ["python3", "weslr/tests/test_logic_teaching_spine_schema_v1.py"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("OK", proc.stdout + proc.stderr)

    def test_proof_step_candidate_helper_tests_still_pass(self):
        proc = subprocess.run(
            ["python3", "weslr/tests/test_proof_step_candidate_helpers_v1.py"],
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
