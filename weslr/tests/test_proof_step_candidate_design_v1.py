from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "WESLR_PROOF_STEP_CANDIDATE_DESIGN_V1.md"
ALLOWED_CHANGED_FILES = {
    "docs/WESLR_PROOF_STEP_CANDIDATE_DESIGN_V1.md",
    "weslr/tests/test_proof_step_candidate_design_v1.py",
}
FORBIDDEN_IMPLEMENTATION_FILES = {
    "weslr/logic_teaching_spine.py",
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
}


class ProofStepCandidateDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.doc_text = DOC.read_text(encoding="utf-8") if DOC.exists() else ""
        cls.doc_text_lower = cls.doc_text.lower()

    def test_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_doc_title_and_status_markers(self):
        self.assertIn("Proof-Step Candidate Design V1", self.doc_text)
        self.assertIn("design_only", self.doc_text)
        self.assertIn("execution_allowed = false", self.doc_text)
        self.assertIn("official_score_claimed = false", self.doc_text)

    def test_proof_step_candidate_object_and_spine(self):
        self.assertIn("ProofStepCandidate", self.doc_text)
        self.assertIn("ReasoningContextBindingCandidate → ProofStepCandidate", self.doc_text)

    def test_core_rule_candidate_is_not_proof_answer_or_truth(self):
        self.assertIn("candidate is not proof", self.doc_text_lower)
        self.assertIn("candidate is not answer selection", self.doc_text_lower)
        self.assertIn("candidate is not a truth claim", self.doc_text_lower)

    def test_all_candidate_types_present(self):
        for candidate_type in [
            "support_step_candidate",
            "contradiction_step_candidate",
            "counterexample_step_candidate",
            "rule_application_candidate",
            "invalidity_test_candidate",
            "template_completion_candidate",
            "unsupported_step_candidate",
        ]:
            self.assertIn(candidate_type, self.doc_text)

    def test_all_support_statuses_present(self):
        for support_status in [
            "candidate_only",
            "insufficient_support",
            "ambiguous",
            "unsupported",
            "unknown",
        ]:
            self.assertIn(support_status, self.doc_text)

    def test_safety_boundaries_present(self):
        for boundary in [
            "no answer keys",
            "no item-ID authority",
            "no answer selection",
            "no official score claim",
            "no benchmark-specific tuning",
            "no runtime integration",
        ]:
            self.assertIn(boundary, self.doc_text)
        self.assertIn("Unsupported gaps must remain visible", self.doc_text)

    def test_operator_decision_options_present(self):
        self.assertIn("APPROVE_PROOF_STEP_CANDIDATE_SCHEMA_ONLY", self.doc_text)
        self.assertIn("REQUEST_REVISION", self.doc_text)
        self.assertIn("REJECT_OR_DEFER", self.doc_text)

    def test_no_forbidden_implementation_files_changed(self):
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
        self.assertFalse(changed & FORBIDDEN_IMPLEMENTATION_FILES)
        unexpected = changed - ALLOWED_CHANGED_FILES
        self.assertFalse(unexpected, f"unexpected changed files: {sorted(unexpected)}")


if __name__ == "__main__":
    unittest.main()
