from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class IntelligenceEnrichmentDoctrineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / "docs" / "WESLR_INTELLIGENCE_ENRICHMENT_DOCTRINE_V1.md"
        cls.text = cls.path.read_text(encoding="utf-8")
        cls.lower = cls.text.lower()

    def test_doctrine_file_exists(self):
        self.assertTrue(self.path.exists())

    def test_required_sections_exist(self):
        for needle in [
            "Enrichment before expansion",
            "Graph extension principle",
            "Cognitive legibility boundary",
            "eval → gap graph",
            "no private authority",
        ]:
            self.assertIn(needle, self.text)

    def test_required_graph_names_exist(self):
        for needle in [
            "knowledge domain graph",
            "cognitive skill graph",
            "benchmark task graph",
            "evidence calibration graph",
            "failure refinement graph",
            "legibility translation graph",
        ]:
            self.assertIn(needle, self.lower)

    def test_required_anti_patterns_exist(self):
        for needle in [
            "one handler per prompt",
            "benchmark gaming",
            "unconnected graphs",
            "hidden self-modification",
        ]:
            self.assertIn(needle, self.lower)

    def test_requires_audit_before_new_graphs(self):
        self.assertIn("existing graph/substrate must be audited before adding new graph systems", self.lower)

    def test_new_graphs_only_when_existing_cannot_represent_relation(self):
        self.assertIn(
            "new graphs are allowed only when existing structures cannot represent the relation",
            self.lower,
        )

    def test_references_cognitive_legibility_boundary(self):
        self.assertIn("cognitive legibility boundary", self.lower)
        self.assertIn("translatable", self.lower)
        self.assertIn("inspectable", self.lower)
        self.assertIn("teachable", self.lower)
        self.assertIn("auditable", self.lower)

    def test_rejects_fake_official_benchmark_claims(self):
        for needle in [
            "WESLR has passed MMLU-Pro",
            "WESLR beats AGI",
            "official leaderboard score",
        ]:
            self.assertNotIn(needle, self.text)


if __name__ == "__main__":
    unittest.main()
