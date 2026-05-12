from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "WESLR_SYNTHETIC_LOGIC_CURRICULUM_DESIGN_V1.md"
ALLOWED_CHANGED_FILES = {
    "docs/WESLR_SYNTHETIC_LOGIC_CURRICULUM_DESIGN_V1.md",
    "weslr/tests/test_synthetic_logic_curriculum_design_v1.py",
}
FORBIDDEN_IMPLEMENTATION_FILES = {
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/logic_teaching_spine.py",
    "weslr/choice_stem_binding.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
}


class SyntheticLogicCurriculumDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.doc_text = DOC.read_text(encoding="utf-8") if DOC.exists() else ""
        cls.doc_text_lower = cls.doc_text.lower()

    def test_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_title_and_status(self):
        self.assertIn("Synthetic Logic Curriculum Design V1", self.doc_text)
        self.assertIn("design_only", self.doc_text)
        self.assertIn("execution_allowed = false", self.doc_text)
        self.assertIn("official_score_claimed = false", self.doc_text)

    def test_curriculum_categories(self):
        required = [
            "universal syllogism",
            "modus ponens",
            "modus tollens",
            "affirming the consequent",
            "denying the antecedent",
            "contradiction",
            "counterexample",
            "irrelevant choice",
            "noun-phrase choice binding",
            "invalid argument identification",
            "necessary/sufficient confusion",
        ]
        for phrase in required:
            self.assertIn(phrase, self.doc_text)

    def test_example_schema_fields(self):
        self.assertIn("example_id", self.doc_text)
        self.assertIn("expected_structural_pattern", self.doc_text)
        self.assertIn("expected_context_binding_type", self.doc_text)

    def test_not_benchmark_scoring(self):
        self.assertIn("Synthetic examples are not benchmark scoring", self.doc_text)

    def test_safety_boundaries(self):
        self.assertIn("no external benchmark text", self.doc_text)
        self.assertIn("no answer-key tuning", self.doc_text)
        self.assertIn("no official score", self.doc_text)
        self.assertIn("no runtime integration", self.doc_text)

    def test_operator_decisions(self):
        self.assertIn("APPROVE_SYNTHETIC_CURRICULUM_SCHEMA_ONLY", self.doc_text)
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
