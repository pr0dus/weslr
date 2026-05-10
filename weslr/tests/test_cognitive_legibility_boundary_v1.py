from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class CognitiveLegibilityBoundaryTests(unittest.TestCase):
    def _read(self, rel: str) -> str:
        return (ROOT / rel).read_text(encoding="utf-8")

    def test_canonical_self_model_contains_boundary(self):
        text = self._read("docs/WESLR_CANONICAL_SELF_MODEL_V1.md")
        for needle in [
            "Cognitive Legibility Boundary",
            "translatable",
            "teachable",
            "operator",
            "private authority",
            "cannot govern",
        ]:
            self.assertIn(needle, text)

    def test_core_identity_contains_boundary(self):
        text = self._read("CORE-IDENTITY.md")
        self.assertIn("Cognitive Legibility Boundary", text)
        self.assertIn("emergent", text)
        self.assertIn("human-understandable", text)
        self.assertIn("operator authority", text.lower())

    def test_omnichat_contains_translation_rule(self):
        text = self._read("weslr/docs/OMNICHAT_LAYER_V1.md")
        for needle in [
            "human-meaningful",
            "internal",
            "not expose",
            "authority",
        ]:
            self.assertIn(needle, text)

    def test_runtime_prompt_rules_still_forbid_meta_internal_language(self):
        self.assertIn("No meta/internal language", self._read("llm_runtime.py"))
        self.assertIn("No meta/internal language", self._read("weslr/providers.py"))

    def test_rejects_doctrine_drift_phrases(self):
        corpus = "\n".join([
            self._read("docs/WESLR_CANONICAL_SELF_MODEL_V1.md"),
            self._read("CORE-IDENTITY.md"),
            self._read("weslr/docs/OMNICHAT_LAYER_V1.md"),
        ]).lower()
        for phrase in [
            "private internal language may govern",
            "operator cannot inspect",
            "untranslatable cognition is allowed",
            "opaque authority is acceptable",
        ]:
            self.assertNotIn(phrase, corpus)

    def test_internal_abstractions_remain_allowed_when_legible(self):
        canonical = self._read("docs/WESLR_CANONICAL_SELF_MODEL_V1.md").lower()
        core = self._read("CORE-IDENTITY.md").lower()
        self.assertIn("may develop internal abstractions", canonical)
        self.assertIn("that is allowed", canonical)
        self.assertIn("remain human-understandable", core)
        self.assertIn("translated, inspected, taught, and audited", core)


if __name__ == "__main__":
    unittest.main()
