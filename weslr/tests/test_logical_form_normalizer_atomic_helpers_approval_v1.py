from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC = ROOT / "docs/WESLR_LOGICAL_FORM_NORMALIZER_ATOMIC_HELPERS_APPROVAL_V1.md"


class LogicalFormNormalizerAtomicHelpersApprovalV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC.read_text(encoding="utf-8")

    def test_approval_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_contains_approve_atomic_extraction_helpers_only(self):
        self.assertIn("APPROVE_ATOMIC_EXTRACTION_HELPERS_ONLY", self.text)

    def test_contains_operator_approved_helper_phase(self):
        self.assertIn("operator_approved_helper_phase", self.text)

    def test_contains_execution_allowed_false(self):
        self.assertIn("execution_allowed = false", self.text)

    def test_contains_official_score_claimed_false(self):
        self.assertIn("official_score_claimed = false", self.text)

    def test_allows_weslr_logical_form_normalizer_py_only_for_helper_phase(self):
        self.assertIn("Changes to `weslr/logical_form_normalizer.py` are now allowed only for helper functions", self.text)

    def test_forbids_parser_wiring(self):
        self.assertIn("parser wiring", self.text)

    def test_forbids_solver_wiring(self):
        self.assertIn("solver wiring", self.text)

    def test_forbids_mcq_adapter_wiring(self):
        self.assertIn("MCQ adapter wiring", self.text)

    def test_forbids_runtime_wiring(self):
        self.assertIn("runtime wiring", self.text)

    def test_forbids_threshold_changes(self):
        self.assertIn("threshold changes", self.text)

    def test_forbids_benchmark_specific_tuning(self):
        self.assertIn("benchmark-specific tuning", self.text)

    def test_forbids_answer_key_use(self):
        self.assertIn("answer-key use", self.text)

    def test_forbids_item_id_authority(self):
        self.assertIn("item-id authority", self.text)

    def test_forbids_answer_selection(self):
        self.assertIn("answer selection", self.text)


if __name__ == "__main__":
    unittest.main()
