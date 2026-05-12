from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "WESLR_PROOF_STEP_BEHAVIOR_DESIGN_V1.md"
ALLOWED_CHANGED_FILES = {
    "docs/WESLR_PROOF_STEP_BEHAVIOR_DESIGN_V1.md",
    "weslr/tests/test_proof_step_behavior_design_v1.py",
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


class ProofStepBehaviorDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.doc_text = DOC.read_text(encoding="utf-8") if DOC.exists() else ""
        cls.doc_text_lower = cls.doc_text.lower()

    def test_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_doc_title_and_status_markers(self):
        self.assertIn("ProofStep Behavior Design V1", self.doc_text)
        self.assertIn("design_only", self.doc_text)
        self.assertIn("execution_allowed = false", self.doc_text)
        self.assertIn("official_score_claimed = false", self.doc_text)

    def test_distinguishes_candidate_from_proof_step(self):
        self.assertIn("ProofStepCandidate", self.doc_text)
        self.assertIn("ProofStep", self.doc_text)
        self.assertIn("possible proof move", self.doc_text)
        self.assertIn("accepted structured reasoning step", self.doc_text)

    def test_proof_step_answer_and_truth_boundaries(self):
        self.assertIn("ProofStep` still must not select answers", self.doc_text)
        self.assertIn("ProofStep` still must not claim benchmark truth", self.doc_text)
        self.assertIn("Unsupported gaps must remain visible", self.doc_text)

    def test_all_allowed_proof_step_statuses_present(self):
        for status in [
            "supported",
            "contradicted",
            "counterexample_supported",
            "rule_application_supported",
            "template_completed",
            "ambiguous",
            "unsupported",
        ]:
            self.assertIn(status, self.doc_text)

    def test_required_future_fields_present(self):
        for field in [
            "proof_step_id",
            "source_candidate_id",
            "source_context_binding_ids",
            "source_premise_proposition_ids",
            "source_choice_proposition_ids",
            "reasoning_relation",
            "inference_pattern",
            "support_status",
            "confidence",
            "warrant",
            "unsupported_gaps",
            "human_explanation",
            "legibility",
            "anti_gaming",
        ]:
            self.assertIn(field, self.doc_text)

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
        self.assertIn("no raw benchmark storage by default", self.doc_text)
        self.assertIn("no hidden symbolic authority", self.doc_text)
        self.assertIn("low-confidence steps must not be silently promoted", self.doc_text)

    def test_non_goals_preserve_runtime_and_scoring_boundaries(self):
        for non_goal in [
            "no implementation in this phase",
            "no proof generation",
            "no proof-chain generation",
            "no teaching explanation generation",
            "no solver changes",
            "no MCQ adapter changes",
            "no runtime integration",
            "no scoring",
        ]:
            self.assertIn(non_goal, self.doc_text)

    def test_operator_decision_options_present(self):
        self.assertIn("APPROVE_PROOF_STEP_SCHEMA_ALIGNMENT_ONLY", self.doc_text)
        self.assertIn("APPROVE_PROOF_STEP_HELPERS_DIAGNOSTICS_ONLY", self.doc_text)
        self.assertIn("REQUEST_REVISION", self.doc_text)
        self.assertIn("REJECT_OR_DEFER", self.doc_text)

    def test_no_forbidden_implementation_files_changed(self):
        result = subprocess.run(
            ["bash", "-lc", "git diff --name-only && git diff --cached --name-only"],
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
