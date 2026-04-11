"""Tests for ExplanationModeSelector (Human-Adaptive Explanation v1 slice)."""

import unittest
from weslr.explanation_mode_selector import ExplanationModeSelector, ExplanationKnobs


class TestExplanationModeSelector(unittest.TestCase):
    def test_explicit_override_be_shorter(self):
        sel = ExplanationModeSelector()
        sel.apply_overrides({"be shorter": True})
        knobs = sel.select_knobs(None)
        self.assertLess(knobs.depth, 0.5)
        self.assertEqual(knobs.pacing, "fast")

    def test_session_preference_persists(self):
        sel = ExplanationModeSelector()
        sel.apply_overrides({"be more technical": True})
        knobs1 = sel.select_knobs(None)
        knobs2 = sel.select_knobs(None)  # still applied
        self.assertGreaterEqual(knobs2.technicality, 0.7)

    def test_conflict_high_ambiguity_keeps_uncertainty_plain(self):
        sel = ExplanationModeSelector(persona="engineer")
        sel.apply_overrides({"be shorter": True})
        knobs = sel.select_knobs(None, signals={"ambiguity": 0.8})
        self.assertTrue(knobs.uncertainty_plain)
        self.assertGreaterEqual(knobs.directness, 0.5)

    def test_persona_defaults(self):
        sel = ExplanationModeSelector(persona="child")
        knobs = sel.select_knobs(None)
        self.assertEqual(knobs.pacing, "slow")
        self.assertLess(knobs.technicality, 0.3)

    def test_multiple_overrides_combine(self):
        sel = ExplanationModeSelector()
        sel.apply_overrides({"be more direct": True, "less formal": True})
        knobs = sel.select_knobs(None)
        self.assertGreaterEqual(knobs.directness, 0.7)
        self.assertGreater(knobs.structure_looseness, 0.5)


if __name__ == "__main__":
    unittest.main()
