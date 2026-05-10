from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr import formal_logic_rubric as rubric  # noqa: E402


class FormalLogicRubricV1Tests(unittest.TestCase):
    def test_rubric_contains_all_required_dimensions(self):
        data = rubric.get_formal_logic_rubric()
        for key in [
            "premise_detection",
            "conclusion_detection",
            "conditional_reasoning",
            "necessary_conditions",
            "sufficient_conditions",
            "negation",
            "quantifiers",
            "contradiction_detection",
            "consistency_checking",
            "valid_inference",
            "invalid_inference",
            "counterexample_search",
            "answer_choice_elimination",
            "symbolic_form_uncertainty",
        ]:
            self.assertIn(key, data)

    def test_positive_markers_cover_required_concepts(self):
        text = "\n".join(rubric.get_formal_logic_positive_markers()).lower()
        for needle in [
            "premise",
            "conclusion",
            "necessary",
            "sufficient",
            "conditional",
            "negation",
            "quantifiers",
            "contradiction",
            "consistency",
            "validity",
            "counterexample",
            "eliminates unsupported answer choices",
            "uncertainty",
        ]:
            self.assertIn(needle, text)

    def test_negative_markers_cover_required_failure_patterns(self):
        text = "\n".join(rubric.get_formal_logic_negative_markers()).lower()
        for needle in [
            "necessary and sufficient",
            "assumes converse",
            "assumes inverse",
            "ignores negation",
            "ignores quantifiers",
            "accepts contradiction",
            "unsupported conclusion",
            "surface wording",
            "answer-position bias",
        ]:
            self.assertIn(needle, text)

    def test_anti_gaming_boundaries_cover_required_rules(self):
        text = "\n".join(rubric.get_formal_logic_anti_gaming_boundaries()).lower()
        for needle in [
            "no answer-key memorization",
            "no item-specific phrase rules",
            "no official-score inference",
            "no benchmark tuning",
            "no raw question storage by default",
            "no answer-position bias",
        ]:
            self.assertIn(needle, text)

    def test_human_explanation_mentions_legibility_requirements(self):
        text = rubric.explain_formal_logic_rubric_for_humans().lower()
        for needle in [
            "teachable",
            "human-understandable",
            "symbolic shorthand must be translatable",
        ]:
            self.assertIn(needle, text)

    def test_no_official_score_claim_phrases(self):
        corpus = "\n".join([
            rubric.explain_formal_logic_rubric_for_humans(),
            *rubric.get_formal_logic_positive_markers(),
            *rubric.get_formal_logic_negative_markers(),
            *rubric.get_formal_logic_anti_gaming_boundaries(),
            *rubric.get_formal_logic_rubric().values(),
        ]).lower()
        for phrase in [
            "weslr has passed mmlu",
            "official mmlu score",
            "leaderboard",
        ]:
            self.assertNotIn(phrase, corpus)

    def test_only_expected_files_changed_in_git_diff(self):
        expected = {
            "weslr/formal_logic_rubric.py",
            "weslr/tests/test_formal_logic_rubric_v1.py",
        }
        diff_names = {
            line.strip()
            for line in (ROOT / ".git").exists() and __import__("subprocess").check_output(
                ["git", "diff", "--name-only"], cwd=ROOT, text=True
            ).splitlines()
            if line.strip()
        }
        self.assertTrue(diff_names.issubset(expected), diff_names)


if __name__ == "__main__":
    unittest.main()
