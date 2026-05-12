#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = REPO_ROOT / "docs" / "WESLR_PARSER_ROLE_CLASSIFICATION_EXPECTATIONS_V1.md"
ALLOWED_CHANGED_FILES = {
    "docs/WESLR_PARSER_ROLE_CLASSIFICATION_EXPECTATIONS_V1.md",
    "weslr/tests/test_parser_role_classification_expectations_v1.py",
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


class ParserRoleClassificationExpectationsV1Tests(unittest.TestCase):
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

    def test_status_markers_present(self):
        self.assert_doc_contains("expectations_only")
        self.assert_doc_contains("execution_allowed = false")
        self.assert_doc_contains("official_score_claimed = false")

    def test_role_expectations_defined(self):
        for needle in [
            "### premise expectation",
            "### background expectation",
            "### question_instruction expectation",
            "### choice_claim expectation",
            "### unsupported_fragment expectation",
        ]:
            self.assert_doc_contains(needle)

    def test_required_safety_expectations_present(self):
        self.assert_doc_contains("question instructions are not premises")
        self.assert_doc_contains("Background frames context and is not evidence by default")
        self.assert_doc_contains("choice claims stay candidate-side")
        self.assert_doc_contains("unsupported fragments stay visible")

    def test_forbidden_anti_gaming_patterns_present(self):
        self.assert_doc_contains_lower("no answer-key use")
        self.assert_doc_contains_lower("no item-ID authority")
        self.assert_doc_contains_lower("no benchmark-specific tuning")
        self.assert_doc_contains_lower("no official score claim")

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
