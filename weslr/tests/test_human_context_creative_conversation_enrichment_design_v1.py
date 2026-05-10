from __future__ import annotations

import os
import unittest
from pathlib import Path


DOC_PATH = Path(__file__).resolve().parents[2] / "docs" / "WESLR_HUMAN_CONTEXT_CREATIVE_CONVERSATION_ENRICHMENT_V1.md"


class HumanContextCreativeConversationEnrichmentDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC_PATH.read_text(encoding="utf-8")
        cls.lower = cls.text.lower()

    def test_document_exists(self):
        self.assertTrue(DOC_PATH.exists())

    def test_contains_required_skill_names(self):
        self.assertIn("human_context_reasoning", self.text)
        self.assertIn("creative_conversation", self.text)

    def test_contains_target_substrates(self):
        self.assertIn("meaning/response-obligation", self.lower)
        self.assertIn("entity/memory", self.lower)
        self.assertIn("capability taxonomy", self.lower)

    def test_contains_safety_boundaries(self):
        self.assertIn("no clinical diagnosis", self.lower)
        self.assertIn("no therapy replacement", self.lower)
        self.assertIn("no emotional manipulation", self.lower)
        self.assertIn("no fake certainty", self.lower)

    def test_contains_enrichment_dimensions(self):
        for needle in [
            "domain knowledge added",
            "cognitive skill added",
            "evidence requirement",
            "routing/capability impact",
            "eval impact",
            "human-legibility explanation",
            "rollback/reversibility",
        ]:
            self.assertIn(needle, self.lower)

    def test_references_cognitive_legibility_boundary(self):
        self.assertIn("cognitive legibility boundary", self.lower)

    def test_states_no_runtime_behavior_implemented(self):
        self.assertIn("no runtime behavior is implemented by this design", self.lower)

    def test_rejects_fake_benchmark_and_psychology_claims(self):
        self.assertIn('"weslr can diagnose users"', self.lower)
        self.assertIn('"weslr has passed official psychology benchmarks"', self.lower)
        self.assertIn('"weslr beats agi"', self.lower)


if __name__ == "__main__":
    unittest.main()
