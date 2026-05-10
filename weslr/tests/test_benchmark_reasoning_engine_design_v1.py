from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class BenchmarkReasoningEngineDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / "docs" / "WESLR_BENCHMARK_REASONING_ENGINE_V1.md"
        cls.text = cls.path.read_text(encoding="utf-8")
        cls.lower = cls.text.lower()

    def test_doc_exists(self):
        self.assertTrue(self.path.exists())

    def test_contains_benchmark_reasoning_engine(self):
        self.assertIn("Benchmark Reasoning Engine", self.text)

    def test_contains_pipeline_stages(self):
        for needle in [
            "task classification",
            "question decomposition",
            "constraint extraction",
            "answer-choice representation",
            "candidate reasoning paths",
            "solver/tool selection",
            "option scoring",
            "contradiction/evidence check",
            "confidence calibration",
            "human-readable explanation",
            "failure-to-enrichment record",
        ]:
            self.assertIn(needle, self.lower)

    def test_contains_solver_families(self):
        for needle in [
            "formal logic solver",
            "ethics/tradeoff solver",
            "science mechanism solver",
            "semantic/language solver",
            "mathematical reasoning solver",
            "factual/evidence retrieval solver",
            "analogy/abstraction solver",
            "uncertainty/calibration solver",
        ]:
            self.assertIn(needle, self.lower)

    def test_contains_intermediate_representation_fields(self):
        for needle in [
            "task_type",
            "parsed_question",
            "constraints",
            "assumptions",
            "choice_representations",
            "reasoning_steps",
            "solver_outputs",
            "selected_answer",
            "confidence",
            "uncertainty",
            "explanation",
            "failure_modes",
            "provenance",
            "anti_gaming_flags",
        ]:
            self.assertIn(needle, self.text)

    def test_contains_cognitive_legibility_boundary(self):
        self.assertIn("Cognitive Legibility Boundary", self.text)
        self.assertIn("translatable", self.lower)
        self.assertIn("human-teachable", self.lower)

    def test_contains_anti_benchmark_gaming_boundary(self):
        for needle in [
            "no item IDs",
            "no answer-label learning",
            "no raw benchmark memorization",
            "no official-score claims",
            "no leaderboard inference",
            "no benchmark-specific shortcuts",
        ]:
            self.assertIn(needle, self.text)

    def test_maps_existing_substrates_correctly(self):
        for needle in [
            "internal_reasoning_graph = reasoning traces, failures, proposals",
            "concept_graph = domain concepts and evidence",
            "capability_registry = task and skill taxonomy",
            "eval/scorecard = measurement only",
            "existing scorers = helper modules, not core intelligence",
            "MCQ adapter = input/output shell, not reasoning engine",
        ]:
            self.assertIn(needle, self.text)

    def test_subject_scorers_are_helpers_not_central_intelligence(self):
        self.assertIn("helper tools, not the central intelligence layer", self.lower)
        self.assertIn("helper modules, not core intelligence", self.lower)

    def test_contains_future_implementation_phases(self):
        for needle in [
            "A. ReasoningTrace schema",
            "B. Task classifier",
            "C. Solver registry",
            "D. Formal logic solver as first real solver",
            "E. Ethics/tradeoff solver migration into solver registry",
            "F. MCQ adapter calls reasoning engine",
            "G. failure bridge records solver-level failures",
            "H. scorecard compares before/after",
            "I. no official claim",
        ]:
            self.assertIn(needle, self.text)

    def test_does_not_contain_forbidden_claims(self):
        for phrase in [
            "WESLR has passed MMLU",
            "official MMLU score",
            "leaderboard score",
            "memorize answer keys",
        ]:
            self.assertNotIn(phrase.lower(), self.lower)


if __name__ == "__main__":
    unittest.main()
