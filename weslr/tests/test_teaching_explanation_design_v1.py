from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "WESLR_TEACHING_EXPLANATION_DESIGN_V1.md"

FORBIDDEN_CHANGED = {
    "weslr/logic_teaching_spine.py",
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
}
ALLOWED_CHANGED = {
    "docs/WESLR_TEACHING_EXPLANATION_DESIGN_V1.md",
    "weslr/tests/test_teaching_explanation_design_v1.py",
}


class TeachingExplanationDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = DOC.read_text(encoding="utf-8")
        cls.lower = cls.text.lower()

    def test_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_title_present(self):
        self.assertIn("Teaching Explanation Design V1", self.text)

    def test_status_markers_present(self):
        self.assertIn("design_only", self.text)
        self.assertIn("execution_allowed = false", self.text)
        self.assertIn("official_score_claimed = false", self.text)

    def test_distinguishes_proof_step_from_teaching_explanation(self):
        self.assertIn("ProofStep` is a structured reasoning step", self.text)
        self.assertIn("TeachingExplanation` is a human-facing view", self.text)

    def test_no_new_reasoning_authority(self):
        self.assertIn("TeachingExplanation` must not create new reasoning authority", self.text)

    def test_must_not_select_answers_or_claim_truth(self):
        self.assertIn("TeachingExplanation` must not select answers", self.text)
        self.assertIn("TeachingExplanation` must not claim benchmark truth", self.text)

    def test_contains_all_explanation_modes(self):
        for mode in ["beginner", "technical", "academic", "spock", "operator_audit"]:
            self.assertIn(mode, self.lower)

    def test_contains_spock(self):
        self.assertIn("spock", self.lower)

    def test_contains_conditional_patterns(self):
        for pattern in ["modus ponens", "modus tollens", "affirming consequent", "denying antecedent"]:
            self.assertIn(pattern, self.lower)

    def test_unsupported_gaps_remain_visible(self):
        self.assertIn("unsupported gaps remain visible", self.lower)

    def test_forbids_answer_key_and_item_id_authority(self):
        self.assertIn("no answer keys", self.lower)
        self.assertIn("no item-id authority", self.lower)

    def test_forbids_official_score_and_benchmark_tuning(self):
        self.assertIn("no official score claim", self.lower)
        self.assertIn("no benchmark-specific tuning", self.lower)

    def test_forbids_runtime_integration(self):
        self.assertIn("no runtime integration", self.lower)

    def test_operator_decisions_present(self):
        for decision in [
            "APPROVE_TEACHING_EXPLANATION_SCHEMA_ALIGNMENT_ONLY",
            "APPROVE_TEACHING_EXPLANATION_HELPERS_DIAGNOSTICS_ONLY",
            "REQUEST_REVISION",
            "REJECT_OR_DEFER",
        ]:
            self.assertIn(decision, self.text)

    def test_no_forbidden_implementation_files_changed(self):
        proc = subprocess.run(
            ["bash", "-lc", "git diff --name-only && git diff --cached --name-only && git ls-files --others --exclude-standard"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        changed = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
