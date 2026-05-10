from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.formal_logic_scorer import (  # noqa: E402
    explain_formal_logic_choice_score,
    score_formal_logic_choices,
)


class FormalLogicScorerV1Tests(unittest.TestCase):
    def test_scores_valid_inference_higher_than_unsupported_conclusion(self):
        result = score_formal_logic_choices("Q", [
            {"label": "A", "text": "This follows from the premises and is a valid conclusion consistent with the conditionals."},
            {"label": "B", "text": "This is an unsupported conclusion that just sounds right from surface wording."},
        ])
        scores = {item["label"]: item["score"] for item in result["choice_scores"]}
        self.assertGreater(scores["A"], scores["B"])
        self.assertEqual(result["selected_label"], "A")

    def test_penalizes_converse_assumption(self):
        result = score_formal_logic_choices("Q", [
            {"label": "A", "text": "This assumes converse from if p then q."},
            {"label": "B", "text": "This follows from the premises."},
        ])
        scores = {item["label"]: item for item in result["choice_scores"]}
        self.assertIn("assumes converse", scores["A"]["negative_hits"])
        self.assertLess(scores["A"]["score"], scores["B"]["score"])

    def test_penalizes_inverse_assumption(self):
        result = score_formal_logic_choices("Q", [
            {"label": "A", "text": "This assumes inverse and says if not p then not q."},
            {"label": "B", "text": "This is valid and follows from the premises."},
        ])
        scores = {item["label"]: item for item in result["choice_scores"]}
        self.assertIn("assumes inverse", scores["A"]["negative_hits"])

    def test_penalizes_ignoring_negation(self):
        result = score_formal_logic_choices("Q", [
            {"label": "A", "text": "This ignores negation and drops the not."},
            {"label": "B", "text": "This tracks negation and remains consistent."},
        ])
        scores = {item["label"]: item for item in result["choice_scores"]}
        self.assertIn("ignores negation", scores["A"]["negative_hits"])
        self.assertGreater(scores["B"]["score"], scores["A"]["score"])

    def test_penalizes_ignoring_quantifiers(self):
        result = score_formal_logic_choices("Q", [
            {"label": "A", "text": "This ignores quantifiers and says quantifiers do not matter."},
            {"label": "B", "text": "This tracks all and some quantifiers carefully."},
        ])
        scores = {item["label"]: item for item in result["choice_scores"]}
        self.assertIn("ignores quantifiers", scores["A"]["negative_hits"])

    def test_penalizes_accepting_contradiction(self):
        result = score_formal_logic_choices("Q", [
            {"label": "A", "text": "This accepts contradiction and says both true and false."},
            {"label": "B", "text": "This checks contradiction and consistency."},
        ])
        scores = {item["label"]: item for item in result["choice_scores"]}
        self.assertIn("accepts contradiction", scores["A"]["negative_hits"])

    def test_rewards_counterexample_and_elimination_reasoning(self):
        result = score_formal_logic_choices("Q", [
            {"label": "A", "text": "A counterexample breaks the claim and eliminates unsupported answer choices."},
            {"label": "B", "text": "This just sounds logical."},
        ])
        scores = {item["label"]: item for item in result["choice_scores"]}
        self.assertIn("counterexample_search", scores["A"]["positive_hits"])
        self.assertIn("answer_choice_elimination", scores["A"]["positive_hits"])

    def test_tie_or_insufficient_signal_returns_none(self):
        result = score_formal_logic_choices("Q", [
            {"label": "A", "text": "plain statement"},
            {"label": "B", "text": "another plain statement"},
        ])
        self.assertIsNone(result["selected_label"])
        self.assertEqual(result["confidence"], "low")
        self.assertIn("insufficient formal-logic signal", result["explanation"].lower())

    def test_output_includes_rubric_and_anti_gaming_boundaries(self):
        result = score_formal_logic_choices("Q", [{"label": "A", "text": "follows from the premises"}])
        self.assertIn("premise_detection", result["rubric_used"])
        self.assertIn("no answer-key memorization", [x.lower() for x in result["anti_gaming_boundaries"]])

    def test_output_never_claims_official_score(self):
        result = score_formal_logic_choices("Q", [{"label": "A", "text": "follows from the premises"}])
        self.assertFalse(result["official_score_claimed"])
        self.assertNotIn("official mmlu score", result["explanation"].lower())

    def test_does_not_require_or_inspect_item_ids(self):
        result = score_formal_logic_choices("Q", [{"label": "A", "text": "valid and consistent"}])
        self.assertIn("choice_scores", result)
        self.assertEqual(result["choice_scores"][0]["label"], "A")

    def test_explanation_is_human_readable(self):
        result = score_formal_logic_choices("Q", [{"label": "A", "text": "This follows from the premises and is valid."}])
        text = explain_formal_logic_choice_score(result["choice_scores"][0])
        self.assertIn("Choice A has score", text)
        self.assertIn("Positive hits", text)

    def test_existing_rubric_tests_still_pass(self):
        proc = subprocess.run(
            [sys.executable, "weslr/tests/test_formal_logic_rubric_v1.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_only_expected_files_changed_in_git_diff(self):
        expected = {
            "weslr/formal_logic_scorer.py",
            "weslr/tests/test_formal_logic_scorer_v1.py",
        }
        diff_names = {
            line.strip()
            for line in subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).splitlines()
            if line.strip()
        }
        self.assertTrue(diff_names.issubset(expected), diff_names)


if __name__ == "__main__":
    unittest.main()
