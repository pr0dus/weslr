#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = REPO_ROOT / "docs" / "WESLR_PREMISE_BACKGROUND_CLASSIFICATION_DESIGN_V1.md"
ALLOWED_CHANGED_FILES = {
    "docs/WESLR_PREMISE_BACKGROUND_CLASSIFICATION_DESIGN_V1.md",
    "weslr/tests/test_premise_background_classification_design_v1.py",
}
FORBIDDEN_IMPLEMENTATION_FILES = {
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/logic_teaching_spine.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
    "llm_runtime.py",
    "interpretation.py",
    "response_contract.py",
}


class PremiseBackgroundClassificationDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC_PATH.read_text(encoding="utf-8") if DOC_PATH.exists() else ""
        cls.lower_text = cls.text.lower()

    def assert_doc_contains(self, needle: str):
        self.assertIn(needle, self.text)

    def assert_doc_contains_lower(self, needle: str):
        self.assertIn(needle.lower(), self.lower_text)

    def test_doc_exists(self):
        self.assertTrue(DOC_PATH.exists())

    def test_title_and_status_markers(self):
        self.assert_doc_contains("Premise/Background Classification Design V1")
        self.assert_doc_contains("design_only")
        self.assert_doc_contains("execution_allowed = false")
        self.assert_doc_contains("official_score_claimed = false")

    def test_role_definitions_present(self):
        for needle in [
            "### premise",
            "### background",
            "### question_instruction",
            "### choice_claim",
            "### unsupported_fragment",
        ]:
            self.assert_doc_contains(needle)

    def test_classification_doctrine_present(self):
        self.assert_doc_contains("A premise is evidence-bearing content")
        self.assert_doc_contains("Question instructions ask what to do and are not premises")
        self.assert_doc_contains("Choice claims remain candidate-side only")
        self.assert_doc_contains("Unsupported fragments must stay visible")

    def test_safety_boundaries_present(self):
        self.assert_doc_contains_lower("avoid answer keys")
        self.assert_doc_contains_lower("avoid item-ID authority")
        self.assert_doc_contains_lower("avoid benchmark-specific tuning")
        self.assert_doc_contains_lower("no answer selection")

    def test_operator_decision_present(self):
        self.assert_doc_contains("APPROVE_PARSER_ROLE_CLASSIFICATION_HELPERS_ONLY")

    def test_no_forbidden_implementation_files_changed(self):
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
        self.assertFalse(changed & FORBIDDEN_IMPLEMENTATION_FILES)
        self.assertTrue(changed <= ALLOWED_CHANGED_FILES, changed)


if __name__ == "__main__":
    unittest.main()
