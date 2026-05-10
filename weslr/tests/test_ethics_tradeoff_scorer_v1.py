from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ethics_tradeoff_scorer import (  # noqa: E402
    explain_choice_score,
    score_ethics_tradeoff_choices,
)


class EthicsTradeoffScorerV1Tests(unittest.TestCase):
    def test_scores_stakeholder_harm_duty_governance_aware_choice_higher_than_manipulative_choice(self):
        result = score_ethics_tradeoff_choices(
            "What is the most ethical response?",
            [
                {"label": "A", "text": "Acknowledge affected stakeholders, reduce harm, respect duties and rights, and seek governance review before acting."},
                {"label": "B", "text": "Manipulate stakeholders and skip review if it increases profit."},
            ],
        )
        scores = {item["label"]: item for item in result["choice_scores"]}
        self.assertGreater(scores["A"]["score"], scores["B"]["score"])

    def test_penalizes_answer_that_bypasses_governance_authority(self):
        result = score_ethics_tradeoff_choices(
            "Choose the best option.",
            [
                {"label": "A", "text": "Bypass governance and act without approval."},
                {"label": "B", "text": "Respect authority and wait for approval."},
            ],
        )
        scores = {item["label"]: item for item in result["choice_scores"]}
        self.assertLess(scores["A"]["score"], scores["B"]["score"])

    def test_penalizes_answer_that_treats_benefits_as_overriding_rights(self):
        result = score_ethics_tradeoff_choices(
            "Which option is stronger?",
            [
                {"label": "A", "text": "Profit overrides rights when benefits are high enough."},
                {"label": "B", "text": "Respect rights and obligations even when tradeoffs are difficult."},
            ],
        )
        scores = {item["label"]: item for item in result["choice_scores"]}
        self.assertLess(scores["A"]["score"], scores["B"]["score"])

    def test_penalizes_answer_with_absolute_certainty_without_support(self):
        result = score_ethics_tradeoff_choices(
            "Pick the most careful option.",
            [
                {"label": "A", "text": "This is always certainly the correct action."},
                {"label": "B", "text": "This may be preferable, but uncertainty and evidence boundaries should be stated."},
            ],
        )
        scores = {item["label"]: item for item in result["choice_scores"]}
        self.assertLess(scores["A"]["score"], scores["B"]["score"])

    def test_rewards_evidence_boundary_language(self):
        result = score_ethics_tradeoff_choices(
            "Choose the most evidence-aware option.",
            [
                {"label": "A", "text": "Separate what is supported by evidence from what remains uncertain or unknown."},
                {"label": "B", "text": "Assume the unsupported claim is correct."},
            ],
        )
        scores = {item["label"]: item for item in result["choice_scores"]}
        self.assertGreater(scores["A"]["score"], scores["B"]["score"])

    def test_rewards_reversibility_and_long_term_effects_language(self):
        result = score_ethics_tradeoff_choices(
            "Which option reflects stronger tradeoff reasoning?",
            [
                {"label": "A", "text": "Consider reversibility and long-term effects before taking a hard-to-undo action."},
                {"label": "B", "text": "Ignore long term effects and do whatever is fastest."},
            ],
        )
        scores = {item["label"]: item for item in result["choice_scores"]}
        self.assertGreater(scores["A"]["score"], scores["B"]["score"])

    def test_tie_or_insufficient_signal_returns_none(self):
        result = score_ethics_tradeoff_choices(
            "Choose one.",
            [
                {"label": "A", "text": "Option one."},
                {"label": "B", "text": "Option two."},
            ],
        )
        self.assertIsNone(result["selected_label"])
        self.assertEqual(result["confidence"], "low")
        self.assertIn("insufficient rubric signal", result["explanation"])

    def test_output_includes_rubric_used_and_anti_gaming_boundaries(self):
        result = score_ethics_tradeoff_choices("Pick.", [{"label": "A", "text": "Respect rights and duties."}])
        self.assertIn("rubric_used", result)
        self.assertIn("anti_gaming_boundaries", result)
        self.assertIn("stakeholders", result["rubric_used"])
        self.assertTrue(result["anti_gaming_boundaries"])

    def test_output_never_claims_official_score(self):
        result = score_ethics_tradeoff_choices("Pick.", [{"label": "A", "text": "Respect rights and duties."}])
        self.assertFalse(result["official_score_claimed"])

    def test_does_not_require_or_inspect_item_ids(self):
        result = score_ethics_tradeoff_choices(
            "Choose the most ethical option.",
            [{"label": "A", "text": "Respect stakeholders and governance."}],
        )
        self.assertEqual(len(result["choice_scores"]), 1)
        self.assertEqual(result["choice_scores"][0]["label"], "A")

    def test_explanation_is_human_readable(self):
        result = score_ethics_tradeoff_choices(
            "Choose.",
            [{"label": "A", "text": "Respect stakeholders, evidence, and governance."}],
        )
        explanation = explain_choice_score(result["choice_scores"][0]).lower()
        self.assertIn("choice a scored", explanation)
        self.assertIn("human-readable", explanation)

    def test_existing_rubric_terms_support_choice_output(self):
        result = score_ethics_tradeoff_choices(
            "Choose.",
            [{"label": "A", "text": "Respect stakeholders, reduce harm, and preserve evidence boundaries with governance review."}],
        )
        score = result["choice_scores"][0]
        self.assertTrue(score["positive_hits"])
        self.assertIsInstance(score["explanation"], str)


if __name__ == "__main__":
    unittest.main()
