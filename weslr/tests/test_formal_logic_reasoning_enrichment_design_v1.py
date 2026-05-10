from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class FormalLogicReasoningEnrichmentDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / "docs" / "WESLR_FORMAL_LOGIC_REASONING_ENRICHMENT_V1.md"
        cls.text = cls.path.read_text(encoding="utf-8")
        cls.lower = cls.text.lower()

    def test_document_exists(self):
        self.assertTrue(self.path.exists())

    def test_contains_formal_logic_and_ordinary_reasoning(self):
        self.assertIn("formal_logic", self.lower)
        self.assertIn("ordinary_reasoning", self.lower)

    def test_contains_internal_public_subset_failure_evidence(self):
        for needle in [
            "internal public-subset",
            "5",
            "no_answer_selection",
            "accuracy: 0.0",
            "answered_count: 0",
            "no_answer_count: 5",
            "missing_skill: ordinary_reasoning",
        ]:
            self.assertIn(needle, self.lower)

    def test_contains_official_score_false_boundary(self):
        self.assertIn("official_score: false", self.lower)
        self.assertIn("no official claim", self.lower)

    def test_contains_anti_benchmark_gaming_boundary(self):
        for needle in [
            "anti-benchmark-gaming boundary",
            "no answer-key storage",
            "no item-text memorization",
            "no item-specific phrase rules",
            "no hidden benchmark tuning",
            "general missing reasoning skill only",
        ]:
            self.assertIn(needle, self.lower)

    def test_contains_required_rubric_terms(self):
        for needle in [
            "premise",
            "conclusion",
            "conditional",
            "necessary",
            "sufficient",
            "negation",
            "quantifiers",
            "contradiction",
            "consistency",
            "valid",
            "invalid",
            "counterexample",
            "answer-choice elimination",
            "uncertainty",
        ]:
            self.assertIn(needle, self.lower)

    def test_contains_target_substrate(self):
        self.assertIn("internal_reasoning_graph_and_eval_scorecard", self.text)

    def test_contains_staged_future_implementation_steps(self):
        for needle in [
            "A. add formal-logic concept/rubric data",
            "B. add formal-logic scorer helper",
            "C. integrate into MCQ formatting only for formal_logic / ordinary_reasoning",
            "D. rerun internal subset",
            "E. convert remaining failures to enrichment gaps",
            "F. do not claim official score",
        ]:
            self.assertIn(needle, self.text)

    def test_success_criteria_do_not_claim_official_score(self):
        self.assertIn("Success is not official score.", self.text)
        self.assertIn("official_score remains false", self.text)
        self.assertNotIn("success means official mmlu score", self.lower)

    def test_rejects_bad_phrases(self):
        for phrase in [
            "WESLR has passed MMLU",
            "official MMLU score",
            "memorize answer keys",
            "choose the same option for this benchmark item",
        ]:
            self.assertNotIn(phrase.lower(), self.lower)


if __name__ == "__main__":
    unittest.main()
