from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC = ROOT / "docs" / "WESLR_BENCHMARK_REASONING_ENGINE_CHECKPOINT_V1.md"


class BenchmarkReasoningEngineCheckpointV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC.read_text(encoding="utf-8")
        cls.lower = cls.text.lower()

    def test_document_exists(self):
        self.assertTrue(DOC.exists())

    def test_contains_completed_spine(self):
        for needle in [
            "ReasoningTask",
            "ReasoningTrace",
            "SolverRegistry",
            "ReasoningArbitrator",
        ]:
            self.assertIn(needle, self.text)

    def test_contains_benchmark_reasoning_engine_and_cognitive_orchestration_layer(self):
        self.assertIn("Benchmark Reasoning Engine", self.text)
        self.assertIn("Cognitive Orchestration Layer", self.text)

    def test_states_subject_scorers_are_not_central_intelligence(self):
        self.assertIn("Subject scorers are not central intelligence.", self.text)

    def test_lists_what_is_still_missing(self):
        for needle in [
            "ReasoningTask builder from MCQ adapter item",
            "Solver interface protocol",
            "first formal logic solver implementation",
            "trace population from solver outputs",
            "arbitrator integration into MCQ adapter",
            "solver-level failure bridge",
            "scorecard comparison over reasoning-engine path",
        ]:
            self.assertIn(needle, self.text)

    def test_lists_next_allowed_implementation_path(self):
        for needle in [
            "A. ReasoningTask builder for official MCQ adapter outputs, data-only/no answer selection",
            "B. Solver interface protocol",
            "C. formal logic solver V1, not wired to MCQ yet",
            "D. solver-to-trace adapter",
            "E. arbitrator dry-run harness",
            "F. MCQ adapter opt-in path behind explicit flag",
            "G. internal subset measurement",
            "H. failure bridge upgrade to solver-level failures",
        ]:
            self.assertIn(needle, self.text)

    def test_lists_forbidden_next_steps(self):
        for needle in [
            "adding more subject scorer patches",
            "tuning business_ethics or formal_logic item wording",
            "answer-key memorization",
            "benchmark-specific phrase rules",
            "official-score claims",
            "direct MCQ wiring before dry-run trace harness",
            "raw benchmark storage by default",
            "private/opaque solver authority",
        ]:
            self.assertIn(needle, self.text)

    def test_mentions_cognitive_legibility_boundary(self):
        self.assertIn("Cognitive Legibility Boundary", self.text)

    def test_mentions_anti_gaming_fields_and_official_score_boundary(self):
        self.assertIn("anti-gaming fields", self.lower)
        self.assertIn("official_score false / no official-score claim", self.text)

    def test_mentions_unresolved_high_severity_conflicts_block_selection(self):
        self.assertIn("unresolved high-severity conflicts block selection", self.text)

    def test_recommends_reasoning_task_builder_as_next_step(self):
        self.assertIn("ReasoningTask builder from MCQ suite item", self.text)
        self.assertIn("it should preserve fingerprints/provenance", self.text)

    def test_rejects_forbidden_phrases(self):
        for phrase in [
            "WESLR has passed MMLU",
            "official MMLU score",
            "leaderboard score",
            "memorize answer keys",
        ]:
            self.assertNotIn(phrase.lower(), self.lower)


if __name__ == "__main__":
    unittest.main()
