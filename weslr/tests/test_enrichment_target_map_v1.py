from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class EnrichmentTargetMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / "docs" / "WESLR_ENRICHMENT_TARGET_MAP_V1.md"
        cls.text = cls.path.read_text(encoding="utf-8")
        cls.lower = cls.text.lower()

    def test_map_document_exists(self):
        self.assertTrue(self.path.exists())

    def test_contains_all_listed_substrates(self):
        for needle in [
            "concept graph",
            "internal reasoning graph",
            "evidence substrate",
            "capability registry/router",
            "meaning / response-obligation substrate",
            "entity / memory graph",
            "eval / scorecard substrate",
            "cognitive legibility doctrine",
        ]:
            self.assertIn(needle, self.lower)

    def test_contains_required_capability_rows(self):
        for needle in [
            "ordinary explanation skills",
            "ordinary reasoning skills",
            "psychology / human context",
            "creativity / conversation",
            "mmlu/gpqa-style multiple choice tasks",
            "helm-style multi-metric evaluation",
            "swe-bench/occ coding task workflow",
            "arc-agi-style abstract task reasoning",
        ]:
            self.assertIn(needle, self.lower)

    def test_contains_new_graph_decision_table(self):
        self.assertIn("new graph decision table", self.lower)
        for needle in [
            "knowledge domain graph",
            "cognitive skill graph",
            "benchmark task graph",
            "evidence calibration graph",
            "failure refinement graph",
            "legibility translation graph",
        ]:
            self.assertIn(needle, self.lower)

    def test_states_extend_existing_substrate_first(self):
        self.assertIn("extend existing substrate first", self.lower)

    def test_states_new_graphs_require_proof_or_justification(self):
        self.assertTrue(
            "new graphs require proof and justification" in self.lower
            or "proof that would justify new graph" in self.lower
        )

    def test_references_cognitive_legibility_boundary(self):
        self.assertIn("cognitive legibility boundary", self.lower)
        self.assertIn("legibility", self.lower)
        self.assertIn("teachable", self.lower)
        self.assertIn("audit", self.lower)

    def test_rejects_fake_benchmark_claims(self):
        for needle in [
            "WESLR has passed MMLU-Pro",
            "WESLR beats AGI",
            "official leaderboard score",
        ]:
            self.assertNotIn(needle, self.text)


if __name__ == "__main__":
    unittest.main()
