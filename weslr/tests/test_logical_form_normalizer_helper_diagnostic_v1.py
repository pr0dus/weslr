from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC = ROOT / "docs/WESLR_LOGICAL_FORM_NORMALIZER_HELPER_DIAGNOSTIC_V1.md"

from weslr.tests.phase_scope_policy import (  # noqa: E402
    assert_logical_form_normalizer_atomic_helper_phase_allowed,
)


class LogicalFormNormalizerHelperDiagnosticV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC.read_text(encoding="utf-8")

    def test_diagnostic_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_doc_contains_diagnostic_checkpoint(self):
        self.assertIn("diagnostic_checkpoint", self.text)

    def test_doc_contains_evidence_only(self):
        self.assertIn("evidence_only", self.text)

    def test_doc_contains_execution_allowed_false(self):
        self.assertIn("execution_allowed = false", self.text)

    def test_doc_contains_official_score_claimed_false(self):
        self.assertIn("official_score_claimed = false", self.text)

    def test_doc_contains_suite_count(self):
        self.assertIn("suite_count: 5", self.text)

    def test_doc_contains_total_item_count(self):
        self.assertIn("total_item_count: 25", self.text)

    def test_doc_contains_total_normalized_terms(self):
        self.assertIn("total_normalized_terms: 123", self.text)

    def test_doc_contains_total_alignments(self):
        self.assertIn("total_alignments: 0", self.text)

    def test_doc_contains_items_with_alignment(self):
        self.assertIn("items_with_alignment: 0", self.text)

    def test_doc_contains_items_with_no_premises(self):
        self.assertIn("items_with_no_premises: 10", self.text)

    def test_doc_states_negative_evidence(self):
        self.assertIn("Helpers are useful as negative evidence.", self.text)

    def test_doc_states_surface_normalization_is_too_weak(self):
        self.assertIn("Whole-statement surface normalization does not create useful term alignments.", self.text)

    def test_doc_recommends_request_revision(self):
        self.assertIn("REQUEST_REVISION", self.text)

    def test_doc_mentions_logical_form_normalizer_v1_1(self):
        self.assertIn("LogicalFormNormalizer V1.1", self.text)

    def test_doc_includes_no_raw_benchmark_question_text_from_known_suites(self):
        forbidden = ["Question:", "Suppose that", "Which of the following"]
        for term in forbidden:
            self.assertNotIn(term, self.text)

    def test_doc_includes_no_answer_choices_from_known_suites(self):
        for term in ["(A)", "(B)", "(C)", "(D)", "Choices:"]:
            self.assertNotIn(term, self.text)

    def test_doc_forbids_answer_key_use(self):
        self.assertIn("no answer-key use", self.text)

    def test_doc_forbids_item_id_authority(self):
        self.assertIn("no item-id authority", self.text)

    def test_doc_forbids_benchmark_specific_tuning(self):
        self.assertIn("no benchmark-specific tuning", self.text)

    def test_doc_forbids_mcq_adapter_wiring_now(self):
        self.assertIn("no MCQ adapter wiring", self.text)

    def test_doc_forbids_solver_wiring_now(self):
        self.assertIn("This does not justify solver wiring.", self.text)

    def test_doc_forbids_threshold_changes(self):
        self.assertIn("This does not justify threshold changes.", self.text)

    def test_existing_logical_form_normalizer_schema_helper_tests_still_pass(self):
        commands = [
            ["python3", "weslr/tests/test_logical_form_normalizer_schema_v1.py"],
            ["python3", "weslr/tests/test_logical_form_normalizer_helpers_v1.py"],
        ]
        for command in commands:
            proc = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, check=True)
            self.assertIn("OK", proc.stdout + proc.stderr)

    def test_no_runtime_files_changed(self):
        assert_logical_form_normalizer_atomic_helper_phase_allowed(self)


if __name__ == "__main__":
    unittest.main()
