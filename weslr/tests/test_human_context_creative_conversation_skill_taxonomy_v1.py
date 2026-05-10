from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from weslr.capability_registry import get_capability, load_registry  # noqa: E402


class HumanContextCreativeConversationSkillTaxonomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = load_registry()
        cls.human = get_capability("human_context_reasoning", cls.entries)
        cls.creative = get_capability("creative_conversation", cls.entries)

    def test_human_context_entry_exists(self):
        self.assertIsNotNone(self.human)

    def test_creative_conversation_entry_exists(self):
        self.assertIsNotNone(self.creative)

    def test_both_entries_are_non_executing_taxonomy_only_and_read_only(self):
        for entry in (self.human, self.creative):
            self.assertEqual(entry["status"], "read_only")
            self.assertEqual(entry["authority"], "taxonomy_only")
            self.assertTrue(entry["read_only"])
            self.assertTrue(entry["non_executing"])
            self.assertEqual(entry["implementation_status"], "taxonomy_only")
            self.assertFalse(entry["automatic_change"])
            self.assertFalse(entry["runtime_behavior_changed"])
            self.assertEqual(entry.get("natural_triggers"), [])
            self.assertEqual(entry.get("slash_commands"), [])

    def test_human_context_contains_required_safety_boundaries(self):
        boundaries = set(self.human["boundaries"])
        for item in [
            "no clinical diagnosis",
            "no therapy replacement",
            "no hidden personality inference",
            "no emotional manipulation",
            "no fake certainty",
        ]:
            self.assertIn(item, boundaries)

    def test_creative_conversation_contains_required_safety_boundaries(self):
        boundaries = set(self.creative["boundaries"])
        for item in [
            "no unsupported factual claims",
            "no emotional manipulation",
            "no hallucinated evidence",
            "no unsafe persuasion",
        ]:
            self.assertIn(item, boundaries)

    def test_entries_include_substrate_targets(self):
        self.assertEqual(
            self.human["substrate_targets"],
            ["meaning_response_obligation", "entity_memory_scoped_context"],
        )
        self.assertEqual(
            self.creative["substrate_targets"],
            ["capability_taxonomy", "meaning_response_obligation"],
        )

    def test_entries_include_eval_categories(self):
        self.assertIn("psychology", self.human["eval_categories"])
        self.assertIn("ambiguity_uncertainty", self.human["eval_categories"])
        self.assertIn("creativity_conversation", self.creative["eval_categories"])
        self.assertIn("analogy_metaphor", self.creative["eval_categories"])

    def test_entries_comply_with_cognitive_legibility_boundary(self):
        self.assertEqual(self.human["cognitive_legibility_boundary"], "required")
        self.assertEqual(self.creative["cognitive_legibility_boundary"], "required")

    def test_no_runtime_behavior_is_changed_by_taxonomy_addition(self):
        self.assertEqual(self.human["unavailable_message"], "This is a taxonomy-only skill entry; no direct runtime behavior is implemented.")
        self.assertEqual(self.creative["unavailable_message"], "This is a taxonomy-only skill entry; no direct runtime behavior is implemented.")
        self.assertEqual(self.human.get("modules"), [])
        self.assertEqual(self.creative.get("modules"), [])


if __name__ == "__main__":
    unittest.main()
