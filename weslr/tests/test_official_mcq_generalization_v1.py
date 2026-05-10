from __future__ import annotations

import json
import subprocess
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.evals.official_mcq_adapter import load_suite, run_suite  # noqa: E402


GENERALIZATION_SUITE = ROOT / "weslr" / "evals" / "conversation_suites" / "official_mcq_generalization_sample_v1.json"
TINY_SUITE = ROOT / "weslr" / "evals" / "conversation_suites" / "official_mcq_tiny_sample_v0.json"


class OfficialMcqGeneralizationV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generalization_suite = load_suite(GENERALIZATION_SUITE)
        cls.tiny_suite = load_suite(TINY_SUITE)

    def test_load_generalization_suite(self):
        self.assertEqual(self.generalization_suite["suite_id"], "official_mcq_generalization_sample_v1")

    def test_suite_flags_remain_sample_only(self):
        self.assertTrue(self.generalization_suite["sample_only"])
        self.assertFalse(self.generalization_suite["official_score"])

    def test_suite_has_20_items(self):
        self.assertEqual(len(self.generalization_suite["items"]), 20)

    def test_no_exact_duplicate_question_text_from_tiny_sample(self):
        tiny_questions = {item.question for item in self.tiny_suite["items"]}
        generalization_questions = {item.question for item in self.generalization_suite["items"]}
        duplicates = tiny_questions & generalization_questions
        self.assertEqual(duplicates, set())

    def test_labels_are_distributed(self):
        counts = Counter(item.answer_label for item in self.generalization_suite["items"])
        self.assertGreaterEqual(len(counts), 3)
        self.assertGreaterEqual(sum(1 for label in counts if label != "B"), 2)
        self.assertGreaterEqual(sum(count for label, count in counts.items() if label != "B"), 5)

    def test_run_adapter_on_generalization_suite(self):
        summary = run_suite(GENERALIZATION_SUITE)
        self.assertEqual(summary.total, 20)
        self.assertEqual(summary.suite_id, "official_mcq_generalization_sample_v1")

    def test_answered_count_is_at_least_half(self):
        summary = run_suite(GENERALIZATION_SUITE)
        self.assertGreaterEqual(summary.answered_count, 10, msg=f"answered_count={summary.answered_count}, accuracy={summary.accuracy}")

    def test_no_answer_count_is_reported(self):
        summary = run_suite(GENERALIZATION_SUITE)
        self.assertIsInstance(summary.no_answer_count, int)
        self.assertGreaterEqual(summary.no_answer_count, 0)

    def test_official_score_remains_false(self):
        summary = run_suite(GENERALIZATION_SUITE)
        self.assertFalse(summary.official_score)

    def test_accuracy_is_reported_without_high_bar(self):
        summary = run_suite(GENERALIZATION_SUITE)
        self.assertIsInstance(summary.accuracy, float)
        self.assertGreaterEqual(summary.accuracy, 0.0)
        self.assertLessEqual(summary.accuracy, 1.0)

    def test_no_official_or_leaderboard_claim_language(self):
        raw = GENERALIZATION_SUITE.read_text(encoding="utf-8").lower()
        self.assertNotIn("official benchmark score", raw)
        self.assertNotIn("leaderboard", raw)
        payload = json.dumps(run_suite(GENERALIZATION_SUITE).to_dict()).lower()
        self.assertIn('"official_score": false', payload)
        self.assertNotIn("official benchmark score", payload)
        self.assertNotIn("leaderboard", payload)

    def test_cli_json_output_runs(self):
        result = subprocess.run(
            [
                "python3",
                "-m",
                "weslr.evals.official_mcq_adapter",
                "--suite",
                str(GENERALIZATION_SUITE),
                "--json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["suite_id"], "official_mcq_generalization_sample_v1")
        self.assertFalse(payload["official_score"])
        self.assertTrue(payload["sample_only"])


if __name__ == "__main__":
    unittest.main()
