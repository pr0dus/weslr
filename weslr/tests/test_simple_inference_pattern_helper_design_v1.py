#!/usr/bin/env python3
from pathlib import Path
import subprocess
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = REPO_ROOT / "docs" / "WESLR_SIMPLE_INFERENCE_PATTERN_HELPER_DESIGN_V1.md"
ALLOWED_CHANGED_FILES = {
    "docs/WESLR_SIMPLE_INFERENCE_PATTERN_HELPER_DESIGN_V1.md",
    "weslr/tests/test_simple_inference_pattern_helper_design_v1.py",
}
FORBIDDEN_IMPLEMENTATION_FILES = {
    "weslr/logic_teaching_spine.py",
    "weslr/choice_stem_binding.py",
    "weslr/logical_form_normalizer.py",
    "weslr/formal_logic_parser.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
}


class SimpleInferencePatternHelperDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC_PATH.read_text(encoding="utf-8") if DOC_PATH.exists() else ""

    def assert_doc_contains(self, needle: str):
        self.assertIn(needle, self.text)

    def test_doc_exists(self):
        self.assertTrue(DOC_PATH.exists())

    def test_title_and_status_markers(self):
        self.assert_doc_contains("Simple Inference Pattern Helper Design V1")
        self.assert_doc_contains("design_only")
        self.assert_doc_contains("execution_allowed = false")
        self.assert_doc_contains("official_score_claimed = false")

    def test_contains_combined_proposition_evidence(self):
        for needle in [
            "predicate-derived propositions: 61",
            "binding-derived propositions: 28",
            "combined propositions: 89",
            "items with propositions: 21/25",
            "items with both premise and choice propositions: 4",
            "premise-choice comparisons: 16",
            "simple pattern candidates: 6",
            "items with simple pattern candidate: 3",
            "unsupported gaps: 0",
            "duplicate proposition signatures: 28",
        ]:
            self.assert_doc_contains(needle)

    def test_contains_duplicate_signature_and_dedup_precondition(self):
        self.assert_doc_contains("duplicate proposition signatures")
        self.assert_doc_contains("Proposition deduplication / merge handling must happen before inference candidates are trusted.")
        self.assert_doc_contains("PropositionMergeCandidate")

    def test_contains_simple_pattern_candidate_types(self):
        for needle in [
            "shared-subject",
            "shared-object",
            "relation-overlap",
            "contradiction-candidate",
            "duplicate-support-candidate",
            "transitivity-candidate",
            "unsupported/no-pattern",
        ]:
            self.assert_doc_contains(needle)

    def test_safety_boundaries_are_explicit(self):
        self.assert_doc_contains("pattern candidates are not proof steps")
        self.assert_doc_contains("pattern candidates cannot select answers")
        self.assert_doc_contains("no answer-key use")
        self.assert_doc_contains("no item-ID authority")
        self.assert_doc_contains("no runtime integration")

    def test_operator_decision_options(self):
        self.assert_doc_contains("APPROVE_PROPOSITION_MERGE_SCHEMA_ONLY")
        self.assert_doc_contains("REQUEST_REVISION")
        self.assert_doc_contains("REJECT_OR_DEFER")

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
