from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC = ROOT / "docs" / "WESLR_LOGIC_TEACHING_SPINE_V1.md"
FORBIDDEN_CHANGED = {
    "weslr/logical_form_normalizer.py",
    "weslr/formal_logic_parser.py",
    "weslr/formal_logic_solver.py",
    "weslr/mcq_answer_formatting.py",
    "weslr/evals/official_mcq_adapter.py",
}
ALLOWED_CHANGED = {
    "docs/WESLR_LOGIC_TEACHING_SPINE_V1.md",
    "weslr/tests/test_logic_teaching_spine_design_v1.py",
}


class LogicTeachingSpineDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC.read_text(encoding="utf-8")

    def git_changed_files(self) -> set[str]:
        proc = subprocess.run(
            ["bash", "-lc", "git diff --name-only && git diff --cached --name-only"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        return {line.strip() for line in proc.stdout.splitlines() if line.strip()}

    def test_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_contains_title(self):
        self.assertIn("WESLR Logic Teaching Spine V1", self.text)

    def test_contains_design_only(self):
        self.assertIn("design_only", self.text)

    def test_contains_execution_allowed_false(self):
        self.assertIn("execution_allowed = false", self.text)

    def test_contains_official_score_claimed_false(self):
        self.assertIn("official_score_claimed = false", self.text)

    def test_contains_predicate_candidate(self):
        self.assertIn("PredicateCandidate", self.text)

    def test_contains_proposition_candidate(self):
        self.assertIn("PropositionCandidate", self.text)

    def test_contains_inference_pattern(self):
        self.assertIn("InferencePattern", self.text)

    def test_contains_proof_step(self):
        self.assertIn("ProofStep", self.text)

    def test_contains_counterexample_candidate(self):
        self.assertIn("CounterexampleCandidate", self.text)

    def test_contains_teaching_explanation(self):
        self.assertIn("TeachingExplanation", self.text)

    def test_contains_modus_ponens(self):
        self.assertIn("modus ponens", self.text)

    def test_contains_modus_tollens(self):
        self.assertIn("modus tollens", self.text)

    def test_contains_universal_syllogism(self):
        self.assertIn("universal syllogism", self.text)

    def test_contains_affirming_the_consequent(self):
        self.assertIn("affirming the consequent", self.text)

    def test_contains_denying_the_antecedent(self):
        self.assertIn("denying the antecedent", self.text)

    def test_contains_necessary_sufficient_confusion(self):
        self.assertIn("necessary/sufficient confusion", self.text)

    def test_contains_spock_mode(self):
        self.assertIn("Spock mode", self.text)

    def test_forbids_answer_key_use(self):
        self.assertIn("no answer-key use", self.text)

    def test_forbids_item_id_authority(self):
        self.assertIn("no item-id authority", self.text)

    def test_forbids_mcq_adapter_wiring(self):
        self.assertIn("no MCQ adapter wiring", self.text)

    def test_forbids_runtime_wiring(self):
        self.assertIn("no runtime wiring", self.text)

    def test_forbids_official_score_claim(self):
        self.assertIn("no official score claim", self.text)

    def test_contains_operator_decision_approve(self):
        self.assertIn("APPROVE_PROPOSITION_SCHEMA_ONLY", self.text)

    def test_contains_operator_decision_request_revision(self):
        self.assertIn("REQUEST_REVISION", self.text)

    def test_contains_operator_decision_reject_or_defer(self):
        self.assertIn("REJECT_OR_DEFER", self.text)

    def test_does_not_contain_raw_benchmark_question_text(self):
        forbidden_snippets = [
            "Which of the following",
            "All of the following",
            "What is the correct answer",
        ]
        for snippet in forbidden_snippets:
            self.assertNotIn(snippet, self.text)

    def test_does_not_contain_answer_choices(self):
        for snippet in ["A)", "B)", "C)", "D)"]:
            self.assertNotIn(snippet, self.text)

    def test_no_forbidden_implementation_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertTrue(changed.issubset(ALLOWED_CHANGED))


if __name__ == "__main__":
    unittest.main()
