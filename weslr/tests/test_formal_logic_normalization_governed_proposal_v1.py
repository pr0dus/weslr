from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC = ROOT / "docs/WESLR_FORMAL_LOGIC_NORMALIZATION_GOVERNED_PROPOSAL_V1.md"

from weslr.tests.phase_scope_policy import (  # noqa: E402
    assert_logical_form_normalizer_atomic_helper_phase_allowed,
)


class FormalLogicNormalizationGovernedProposalV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC.read_text(encoding="utf-8")

    def test_document_exists(self):
        self.assertTrue(DOC.exists())

    def test_contains_design_first_status(self):
        for term in [
            "DESIGN_FIRST",
            "operator_review_required",
            "execution_allowed = false",
            "official_score_claimed = false",
            "proposal_only",
            "design_first",
        ]:
            self.assertIn(term, self.text)

    def test_contains_logical_form_normalizer_v1(self):
        self.assertIn("LogicalFormNormalizer V1", self.text)

    def test_contains_aggregate_evidence_metrics(self):
        for term in [
            "sample size: 25",
            "distinct subsets: 5",
            "no_term_overlap",
            "20",
            "proposed answers: 0",
            "parsed_no_supported_inference: 24",
            "parsed_ambiguous_candidates: 1",
        ]:
            self.assertIn(term, self.text)

    def test_forbids_answer_key_use(self):
        self.assertIn("no answer-key use", self.text)

    def test_forbids_item_id_authority(self):
        self.assertIn("no item-id authority", self.text)

    def test_forbids_benchmark_specific_tuning(self):
        self.assertIn("no benchmark-specific tuning", self.text)

    def test_forbids_runtime_wiring_now(self):
        self.assertIn("no runtime wiring now", self.text)

    def test_contains_operator_decision_labels(self):
        for term in ["APPROVE_SCHEMA_ONLY", "REQUEST_REVISION", "REJECT_OR_DEFER"]:
            self.assertIn(term, self.text)

    def test_does_not_include_generic_raw_benchmark_markers(self):
        forbidden = [
            "Question:",
            "Choices:",
            "Correct answer:",
            "Answer:",
            "(A)",
            "(B)",
            "(C)",
            "(D)",
        ]
        for term in forbidden:
            self.assertNotIn(term, self.text)

    def test_no_runtime_files_changed(self):
        assert_logical_form_normalizer_atomic_helper_phase_allowed(self)


if __name__ == "__main__":
    unittest.main()
