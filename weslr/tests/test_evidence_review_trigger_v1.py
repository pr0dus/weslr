"""
WESLR Evidence Review Trigger V1 — Tests

Run:
    python3 weslr/tests/test_evidence_review_trigger_v1.py

Verdict label: WESLR_EVIDENCE_REVIEW_TRIGGER_V1_DEFINED
"""

import unittest
from weslr.evidence_review_trigger import (
    detect_evidence_review_need,
    EvidenceReviewResult,
    EvidenceReviewSignals,
)


class TestEvidenceReviewTrigger(unittest.TestCase):

    def _call(self, topic: str, evidence_events: dict) -> EvidenceReviewResult:
        return detect_evidence_review_need(topic, evidence_events)

    # ------------------------------------------------------------------
    # No trigger below threshold
    # ------------------------------------------------------------------
    def test_no_trigger_below_frequency_threshold(self):
        """freq=2 < 3 → no trigger"""
        result = self._call("test_topic", {"frequency": 2, "diversity": 3, "growth": 1.5})
        self.assertFalse(result.trigger)

    def test_no_trigger_below_diversity_threshold(self):
        """diversity=1 < 2 → no trigger"""
        result = self._call("test_topic", {"frequency": 5, "diversity": 1, "growth": 1.0})
        self.assertFalse(result.trigger)

    def test_no_trigger_when_growth_not_positive(self):
        """growth=0.0 → no trigger"""
        result = self._call("test_topic", {"frequency": 4, "diversity": 3, "growth": 0.0})
        self.assertFalse(result.trigger)

    def test_no_trigger_when_growth_negative(self):
        """growth=-0.5 → no trigger"""
        result = self._call("test_topic", {"frequency": 4, "diversity": 3, "growth": -0.5})
        self.assertFalse(result.trigger)

    def test_no_trigger_all_thresholds_missed(self):
        """All below: freq=1, div=1, growth=-1 → no trigger"""
        result = self._call("test_topic", {"frequency": 1, "diversity": 1, "growth": -1.0})
        self.assertFalse(result.trigger)

    # ------------------------------------------------------------------
    # Trigger at threshold
    # ------------------------------------------------------------------
    def test_trigger_at_exact_frequency_threshold(self):
        """freq=3, div=2, growth=0.1 → trigger (growth > 0)"""
        result = self._call("test_topic", {"frequency": 3, "diversity": 2, "growth": 0.1})
        self.assertTrue(result.trigger)

    def test_trigger_at_exact_diversity_threshold(self):
        """freq=5, div=2, growth=0.5 → trigger"""
        result = self._call("test_topic", {"frequency": 5, "diversity": 2, "growth": 0.5})
        self.assertTrue(result.trigger)

    def test_trigger_exactly_at_all_thresholds(self):
        """freq=3, div=2, growth=0.001 → trigger (strict > 0)"""
        result = self._call("test_topic", {"frequency": 3, "diversity": 2, "growth": 0.001})
        self.assertTrue(result.trigger)

    # ------------------------------------------------------------------
    # Trigger with growth
    # ------------------------------------------------------------------
    def test_trigger_with_positive_growth(self):
        """freq=4, div=3, growth=2.0 → trigger"""
        result = self._call("test_topic", {"frequency": 4, "diversity": 3, "growth": 2.0})
        self.assertTrue(result.trigger)
        self.assertGreater(result.confidence, 0.0)

    def test_trigger_high_confidence_with_strong_signals(self):
        """freq=10, div=5, growth=3.0 → trigger, high confidence"""
        result = self._call("test_topic", {"frequency": 10, "diversity": 5, "growth": 3.0})
        self.assertTrue(result.trigger)
        self.assertGreater(result.confidence, 0.7)

    # ------------------------------------------------------------------
    # No false positives
    # ------------------------------------------------------------------
    def test_no_false_positive_frequency_only(self):
        """freq=10 but div=1, growth=0 → no trigger"""
        result = self._call("test_topic", {"frequency": 10, "diversity": 1, "growth": 0.0})
        self.assertFalse(result.trigger)

    def test_no_false_positive_diversity_only(self):
        """diversity=5 but freq=1, growth=0 → no trigger"""
        result = self._call("test_topic", {"frequency": 1, "diversity": 5, "growth": 0.0})
        self.assertFalse(result.trigger)

    def test_no_false_positive_growth_only(self):
        """growth positive but freq=1, div=1 → no trigger"""
        result = self._call("test_topic", {"frequency": 1, "diversity": 1, "growth": 5.0})
        self.assertFalse(result.trigger)

    def test_no_false_positive_missing_keys(self):
        """Missing keys default to 0 → no trigger"""
        result = self._call("test_topic", {})
        self.assertFalse(result.trigger)

    def test_no_false_positive_none_values(self):
        """None values handled gracefully → no trigger"""
        result = self._call("test_topic", {"frequency": None, "diversity": None, "growth": None})
        self.assertFalse(result.trigger)

    # ------------------------------------------------------------------
    # Signal integrity
    # ------------------------------------------------------------------
    def test_signals_preserved(self):
        """Signals in result match inputs"""
        result = self._call("test_topic", {"frequency": 5, "diversity": 3, "growth": 2.0})
        self.assertEqual(result.signals.frequency, 5)
        self.assertEqual(result.signals.diversity, 3)
        self.assertEqual(result.signals.growth, 2.0)

    def test_result_is_frozen_immutable(self):
        """Result is immutable dataclass"""
        result = self._call("test_topic", {"frequency": 5, "diversity": 3, "growth": 2.0})
        with self.assertRaises(Exception):  # frozen dataclass
            result.trigger = False

    # ------------------------------------------------------------------
    # Reason string
    # ------------------------------------------------------------------
    def test_reason_contains_topic(self):
        """Reason includes topic"""
        result = self._call("my_topic", {"frequency": 5, "diversity": 3, "growth": 1.0})
        self.assertIn("my_topic", result.reason)

    def test_reason_contains_signal_values(self):
        """Reason includes signal counts"""
        result = self._call("test_topic", {"frequency": 5, "diversity": 3, "growth": 1.0})
        self.assertIn("freq=5", result.reason)
        self.assertIn("div=3", result.reason)

    # ------------------------------------------------------------------
    # Confidence range
    # ------------------------------------------------------------------
    def test_confidence_is_bounded(self):
        """Confidence always 0.0–1.0"""
        for freq in [0, 1, 3, 5, 10]:
            for div in [0, 1, 2, 5]:
                for growth in [-2.0, -0.5, 0.0, 0.1, 1.0, 5.0]:
                    result = self._call("test", {"frequency": freq, "diversity": div, "growth": growth})
                    self.assertGreaterEqual(result.confidence, 0.0)
                    self.assertLessEqual(result.confidence, 1.0)


if __name__ == "__main__":
    print("=" * 60)
    print("WESLR_EVIDENCE_REVIEW_TRIGGER_V1_DEFINED")
    print("=" * 60)
    unittest.main(verbosity=2)
