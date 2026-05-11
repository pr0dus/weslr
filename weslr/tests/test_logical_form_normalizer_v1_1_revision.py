from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC = ROOT / "docs/WESLR_LOGICAL_FORM_NORMALIZER_V1_1_REVISION.md"
ALLOWED_CHANGED = {
    "docs/WESLR_LOGICAL_FORM_NORMALIZER_V1_1_REVISION.md",
    "weslr/tests/test_logical_form_normalizer_v1_1_revision.py",
}


class LogicalFormNormalizerV11RevisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC.read_text(encoding="utf-8")

    def test_revision_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_doc_contains_revision_design(self):
        self.assertIn("revision_design", self.text)

    def test_doc_contains_request_revision(self):
        self.assertIn("request_revision", self.text)

    def test_doc_contains_execution_allowed_false(self):
        self.assertIn("execution_allowed = false", self.text)

    def test_doc_contains_official_score_claimed_false(self):
        self.assertIn("official_score_claimed = false", self.text)

    def test_doc_contains_total_normalized_terms(self):
        self.assertIn("total_normalized_terms: 123", self.text)

    def test_doc_contains_total_alignments(self):
        self.assertIn("total_alignments: 0", self.text)

    def test_doc_contains_items_with_alignment(self):
        self.assertIn("items_with_alignment: 0", self.text)

    def test_doc_contains_atomic_extraction_pass(self):
        self.assertIn("AtomicExtractionPass", self.text)

    def test_doc_contains_predicate_decomposition_pass(self):
        self.assertIn("PredicateDecompositionPass", self.text)

    def test_doc_contains_role_aware_alignment_pass(self):
        self.assertIn("RoleAwareAlignmentPass", self.text)

    def test_doc_contains_atomic_term_candidate(self):
        self.assertIn("AtomicTermCandidate", self.text)

    def test_doc_contains_predicate_candidate(self):
        self.assertIn("PredicateCandidate", self.text)

    def test_doc_contains_role_aware_term_index(self):
        self.assertIn("RoleAwareTermIndex", self.text)

    def test_doc_contains_alignment_evidence_record(self):
        self.assertIn("AlignmentEvidenceRecord", self.text)

    def test_doc_contains_normalizer_diagnostic_summary(self):
        self.assertIn("NormalizerDiagnosticSummary", self.text)

    def test_doc_contains_operator_options(self):
        for term in ["APPROVE_V1_1_SCHEMA_EXTENSION_ONLY", "REQUEST_MORE_DIAGNOSTICS", "REJECT_OR_DEFER"]:
            self.assertIn(term, self.text)

    def test_doc_forbids_answer_key_use(self):
        self.assertIn("no answer-key use", self.text)

    def test_doc_forbids_item_id_authority(self):
        self.assertIn("no item-id authority", self.text)

    def test_doc_forbids_official_score_claim(self):
        self.assertIn("no official-score claim", self.text)

    def test_doc_forbids_benchmark_specific_tuning(self):
        self.assertIn("no benchmark-specific tuning", self.text)

    def test_doc_forbids_answer_selection(self):
        self.assertIn("no answer selection", self.text)

    def test_doc_forbids_runtime_wiring_now(self):
        self.assertIn("no runtime wiring now", self.text)

    def test_doc_states_no_changes_to_logical_form_normalizer_py(self):
        self.assertIn("no changes to `logical_form_normalizer.py`", self.text)

    def test_doc_does_not_include_raw_benchmark_question_text_from_known_suites(self):
        forbidden = [
            "Psychological egoism",
            "The complex question fallacy",
            "Joe was in charge of lights",
            "Find all c in Z_3",
            "True, True",
            "False, False",
        ]
        for term in forbidden:
            self.assertNotIn(term, self.text)

    def test_doc_does_not_include_answer_choices_from_known_suites(self):
        for term in ["(A)", "(B)", "(C)", "(D)", "Choices:"]:
            self.assertNotIn(term, self.text)

    def test_existing_helper_diagnostic_test_still_passes(self):
        command = """
set -e
name='v11-revision-test-stash'
git stash push -u -m "$name" -- docs/WESLR_LOGICAL_FORM_NORMALIZER_V1_1_REVISION.md weslr/tests/test_logical_form_normalizer_v1_1_revision.py >/dev/null
python3 weslr/tests/test_logical_form_normalizer_helper_diagnostic_v1.py
git stash pop >/dev/null
"""
        proc = subprocess.run(
            ["bash", "-lc", command],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("OK", proc.stdout + proc.stderr)

    def test_no_implementation_files_changed(self):
        proc = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        changed = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
        disallowed = changed - ALLOWED_CHANGED
        self.assertEqual(set(), disallowed)


if __name__ == "__main__":
    unittest.main()
