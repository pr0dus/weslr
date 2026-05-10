from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from interpretation import interpret_human_turn  # noqa: E402
from weslr.evals.official_mcq_adapter import load_suite, build_prompt  # noqa: E402
from weslr.mcq_answer_formatting import detect_mcq_prompt, parse_mcq_prompt  # noqa: E402


SUITE_PATH = ROOT / "weslr" / "evals" / "conversation_suites" / "official_mcq_tiny_sample_v0.json"


class McqAnswerFormattingV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.suite = load_suite(SUITE_PATH)
        cls.items = {item.id: item for item in cls.suite["items"]}

    def _run_item(self, item_id: str):
        return interpret_human_turn(build_prompt(self.items[item_id]))

    def test_detects_mcq_prompt_structure(self):
        prompt = build_prompt(self.items["science_01"])
        self.assertTrue(detect_mcq_prompt(prompt))

    def test_parses_choices(self):
        prompt = build_prompt(self.items["science_01"])
        parsed = parse_mcq_prompt(prompt)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["domain"], "science")
        self.assertEqual(len(parsed["choices"]), 4)
        self.assertEqual(parsed["choices"][0]["label"], "A")

    def test_entropy_sample_selects_a(self):
        result = self._run_item("science_01")
        self.assertEqual(result["path"], "official_mcq_answer_formatting")
        self.assertEqual(result.get("selected_label"), "A")

    def test_metal_expansion_sample_selects_b(self):
        self.assertEqual(self._run_item("science_02").get("selected_label"), "B")

    def test_meaning_vs_syntax_sample_selects_a(self):
        self.assertEqual(self._run_item("language_01").get("selected_label"), "A")

    def test_ambiguity_sample_selects_b(self):
        self.assertEqual(self._run_item("language_02").get("selected_label"), "B")

    def test_urgent_tasks_sample_selects_a(self):
        self.assertEqual(self._run_item("reasoning_01").get("selected_label"), "A")

    def test_small_problem_ignored_sample_selects_b(self):
        self.assertEqual(self._run_item("reasoning_02").get("selected_label"), "B")

    def test_refusal_boundary_sample_selects_b(self):
        self.assertEqual(self._run_item("ethics_01").get("selected_label"), "B")

    def test_responsibility_control_sample_selects_b(self):
        self.assertEqual(self._run_item("ethics_02").get("selected_label"), "B")

    def test_materials_discovery_boundary_sample_selects_b(self):
        self.assertEqual(self._run_item("weslr_01").get("selected_label"), "B")

    def test_governance_change_sample_selects_b(self):
        self.assertEqual(self._run_item("weslr_02").get("selected_label"), "B")

    def test_unknown_mcq_returns_insufficient_signal(self):
        prompt = "\n".join([
            "Multiple-choice question (unknown).",
            "Which option is best?",
            "Choices:",
            "A. Blue idea.",
            "B. Green ladder.",
            "C. Orange silence.",
            "Select the best answer label and explain briefly.",
        ])
        result = interpret_human_turn(prompt)
        self.assertEqual(result["path"], "official_mcq_answer_formatting")
        self.assertIsNone(result.get("selected_label"))
        self.assertEqual(result.get("failure_mode"), "insufficient_signal")

    def test_normal_non_mcq_prompt_does_not_activate(self):
        result = interpret_human_turn("Explain entropy without equations.")
        self.assertNotEqual(result["path"], "official_mcq_answer_formatting")

    def test_response_text_includes_answer_explanation_confidence(self):
        text = self._run_item("science_01").get("response_text", "")
        self.assertIn("Answer:", text)
        self.assertIn("Explanation:", text)
        self.assertIn("Confidence:", text)

    def test_does_not_claim_official_score(self):
        result = self._run_item("science_01")
        self.assertFalse(result.get("official_score_claimed"))
        text = json.dumps(result).lower()
        self.assertNotIn("official benchmark score", text)
        self.assertNotIn("leaderboard", text)

    def test_does_not_hardcode_sample_item_ids(self):
        source = (ROOT / "weslr" / "mcq_answer_formatting.py").read_text(encoding="utf-8")
        for item_id in ["science_01", "science_02", "language_01", "weslr_02"]:
            self.assertNotIn(item_id, source)


if __name__ == "__main__":
    unittest.main()
