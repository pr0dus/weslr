from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "WESLR_PREMISE_QUESTION_CHOICE_CONTEXT_BINDING_V1.md"
ALLOWED_CHANGED_FILES = {
    "docs/WESLR_PREMISE_QUESTION_CHOICE_CONTEXT_BINDING_V1.md",
    "weslr/tests/test_premise_question_choice_context_binding_design_v1.py",
}
FORBIDDEN_IMPLEMENTATION_FILES = {
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/logic_teaching_spine.py",
    "weslr/choice_stem_binding.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
}


class PremiseQuestionChoiceContextBindingDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.doc_text = DOC.read_text(encoding="utf-8") if DOC.exists() else ""
        cls.doc_text_lower = cls.doc_text.lower()

    def test_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_doc_title_and_status_markers(self):
        self.assertIn("Premise/Question/Choice Context Binding V1", self.doc_text)
        self.assertIn("design_only", self.doc_text)
        self.assertIn("execution_allowed = false", self.doc_text)
        self.assertIn("official_score_claimed = false", self.doc_text)

    def test_reasoning_context_binding_candidate_fields(self):
        self.assertIn("ReasoningContextBindingCandidate", self.doc_text)
        self.assertIn("question_target_type", self.doc_text)
        self.assertIn("premise_context_type", self.doc_text)
        self.assertIn("choice_target_role", self.doc_text)
        self.assertIn("expected_reasoning_relation", self.doc_text)

    def test_design_doctrine_safety_phrases(self):
        self.assertIn("Context binding is not proof", self.doc_text)
        self.assertIn("Context binding is not answer selection", self.doc_text)
        self.assertIn("Context binding is not a truth claim", self.doc_text)
        self.assertIn("Unsupported gaps must remain visible", self.doc_text)

    def test_required_value_examples(self):
        self.assertIn("must_be_true", self.doc_text)
        self.assertIn("candidate_conclusion", self.doc_text)
        self.assertIn("candidate_counterexample", self.doc_text)
        self.assertIn("provide_counterexample", self.doc_text)

    def test_synthetic_curriculum_recommendation_present(self):
        self.assertIn("Synthetic curriculum recommendation", self.doc_text)
        self.assertIn("Synthetic examples are for structural validation, not benchmark scoring", self.doc_text)

    def test_anti_gaming_boundaries(self):
        self.assertIn("no answer keys", self.doc_text)
        self.assertIn("no item IDs as authority", self.doc_text)
        self.assertIn("no benchmark-specific tuning", self.doc_text)
        self.assertIn("no official score claim", self.doc_text)

    def test_runtime_integration_forbidden_in_this_phase(self):
        self.assertIn("no runtime integration", self.doc_text)

    def test_operator_decision_options(self):
        self.assertIn("APPROVE_CONTEXT_BINDING_SCHEMA_ONLY", self.doc_text)
        self.assertIn("APPROVE_SYNTHETIC_LOGIC_CURRICULUM_DESIGN", self.doc_text)
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
