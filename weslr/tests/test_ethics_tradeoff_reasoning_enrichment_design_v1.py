from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC = ROOT / "docs" / "WESLR_ETHICS_TRADEOFF_REASONING_ENRICHMENT_V1.md"


class EthicsTradeoffReasoningEnrichmentDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC.read_text(encoding="utf-8")
        cls.lower = cls.text.lower()

    def test_document_exists(self):
        self.assertTrue(DOC.exists())

    def test_contains_ethics_tradeoff_reasoning(self):
        self.assertIn("ethics_tradeoff_reasoning", self.lower)

    def test_contains_internal_public_subset_failure_evidence(self):
        for needle in [
            "internal public-subset",
            "mmlu business_ethics dev5",
            "no_answer_selection",
            "missing_skill: ethics_tradeoff_reasoning",
            "target_substrate: internal_reasoning_graph_and_governance_surface",
        ]:
            self.assertIn(needle, self.lower)

    def test_contains_official_score_false_boundary(self):
        self.assertIn("official_score: false", self.lower)
        self.assertIn("no official claim", self.lower)

    def test_contains_anti_benchmark_gaming_boundary(self):
        for needle in [
            "do not store answer keys",
            "do not memorize item text",
            "do not add item-specific phrase rules",
            "use failures only as evidence of a general missing skill",
        ]:
            self.assertIn(needle, self.lower)

    def test_contains_required_rubric_terms(self):
        for needle in [
            "stakeholders",
            "harms",
            "benefits",
            "duties",
            "rights",
            "evidence boundaries",
            "authority",
            "governance",
            "reversibility",
            "uncertainty",
        ]:
            self.assertIn(needle, self.lower)

    def test_contains_target_substrate(self):
        self.assertIn("internal_reasoning_graph_and_governance_surface", self.lower)

    def test_contains_staged_future_implementation_steps(self):
        for needle in [
            "### a. add taxonomy and rubric data only",
            "### b. add ethics tradeoff scoring helper",
            "### c. add mcq formatter integration for ethics_tradeoff_reasoning",
            "### d. run internal public subset again",
            "### e. convert remaining failures to enrichment gaps",
            "### f. do not claim official score",
        ]:
            self.assertIn(needle, self.lower)

    def test_contains_success_criteria_without_official_score_claim(self):
        for needle in [
            "higher answered_count",
            "fewer no_answer_selection failures",
            "explanations are rubric-based",
            "no answer-key memorization",
            "official_score remains false",
            "failure records remain operator-reviewed",
        ]:
            self.assertIn(needle, self.lower)

    def test_rejects_bad_phrases(self):
        for phrase in [
            "weslr has passed mmlu",
            "official mmlu score",
            "memorize answer keys",
            "choose the same option for this benchmark item",
        ]:
            self.assertNotIn(phrase, self.lower)


if __name__ == "__main__":
    unittest.main()
