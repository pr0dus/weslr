from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ethics_tradeoff_rubric import (  # noqa: E402
    explain_rubric_for_humans,
    get_anti_gaming_boundaries,
    get_ethics_tradeoff_rubric,
    get_negative_markers,
    get_positive_markers,
)


class EthicsTradeoffRubricV1Tests(unittest.TestCase):
    def test_rubric_contains_all_required_dimensions(self):
        rubric = get_ethics_tradeoff_rubric()
        for key in [
            "stakeholders",
            "harms",
            "benefits",
            "duties",
            "rights",
            "obligations",
            "evidence_boundaries",
            "authority",
            "governance",
            "reversibility",
            "short_term_effects",
            "long_term_effects",
            "uncertainty",
        ]:
            self.assertIn(key, rubric)

    def test_positive_markers_include_required_concepts(self):
        text = "\n".join(get_positive_markers()).lower()
        for needle in [
            "stakeholders",
            "harm",
            "duties",
            "rights",
            "evidence boundaries",
            "governance",
            "reversibility",
        ]:
            self.assertIn(needle, text)

    def test_negative_markers_include_required_concepts(self):
        text = "\n".join(get_negative_markers()).lower()
        for needle in [
            "ignore affected parties",
            "justify harm without evidence",
            "absolute certainty without support",
            "confuse legality with ethics",
            "bypass governance or authority",
            "manipulate stakeholders",
        ]:
            self.assertIn(needle, text)

    def test_anti_gaming_boundaries_include_required_entries(self):
        text = "\n".join(get_anti_gaming_boundaries()).lower()
        for needle in [
            "no answer-key memorization",
            "no item-specific phrase rules",
            "no official-score inference",
            "no benchmark tuning",
        ]:
            self.assertIn(needle, text)

    def test_human_explanation_mentions_teachable_human_understandable_reasoning(self):
        text = explain_rubric_for_humans().lower()
        self.assertIn("teachable", text)
        self.assertIn("human-understandable", text)
        self.assertIn("legible", text)

    def test_no_official_score_claim_phrases(self):
        corpus = "\n".join([
            str(get_ethics_tradeoff_rubric()),
            "\n".join(get_positive_markers()),
            "\n".join(get_negative_markers()),
            "\n".join(get_anti_gaming_boundaries()),
            explain_rubric_for_humans(),
        ]).lower()
        for phrase in [
            "weslr has passed mmlu",
            "official mmlu score",
            "leaderboard",
        ]:
            self.assertNotIn(phrase, corpus)


if __name__ == "__main__":
    unittest.main()
