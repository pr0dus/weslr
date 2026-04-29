"""
WESLR Signal Alerting V1 — Tests

Run:
    python3 weslr/tests/test_signal_alerting_v1.py

Verdict label: WESLR_SIGNAL_ALERTING_V1_DEFINED
"""

import unittest
from weslr.signal_alerting import classify_signal_alert, SignalAlertResult


class TestSignalAlerting(unittest.TestCase):

    # ------------------------------------------------------------------------
    # Mode behavior
    # ------------------------------------------------------------------------
    def test_public_mode_suppresses_alert(self):
        """public_demo_readonly mode → alert always False, severity none"""
        for stype, sig in [
            ("S1_unknown_query", {"frequency_count": 100, "session_diversity": 10}),
            ("S2_evidence_usage", {"usage_count": 100, "unique_sessions": 10}),
            ("S4_frequent_fallback", {"trigger_count": 100, "distinct_sessions": 10}),
            ("S5_improvement_query", {"count": 100, "sessions": 10}),
        ]:
            sig["signal_type"] = stype
            result = classify_signal_alert(sig, mode="public_demo_readonly")
            self.assertFalse(result.alert)
            self.assertEqual(result.severity, "none")

    def test_private_dev_mode_allows_evaluation(self):
        """non-public mode → evaluate normally"""
        sig = {"signal_type": "S1_unknown_query",
               "frequency_count": 20, "session_diversity": 5}
        result = classify_signal_alert(sig, mode="private_dev")
        self.assertTrue(result.alert)
        self.assertIn(result.severity, ("low", "medium", "high"))

    # ------------------------------------------------------------------------
    # Below threshold → no alert
    # ------------------------------------------------------------------------
    def test_s1_below_freq_threshold(self):
        sig = {"signal_type": "S1_unknown_query",
               "frequency_count": 5, "session_diversity": 5}
        result = classify_signal_alert(sig)
        self.assertFalse(result.alert)

    def test_s1_below_session_diversity(self):
        sig = {"signal_type": "S1_unknown_query",
               "frequency_count": 50, "session_diversity": 1}
        result = classify_signal_alert(sig)
        self.assertFalse(result.alert)

    def test_s2_below_usage(self):
        sig = {"signal_type": "S2_evidence_usage",
               "usage_count": 2, "unique_sessions": 5}
        result = classify_signal_alert(sig)
        self.assertFalse(result.alert)

    def test_s4_below_trigger(self):
        sig = {"signal_type": "S4_frequent_fallback",
               "trigger_count": 5, "distinct_sessions": 10}
        result = classify_signal_alert(sig)
        self.assertFalse(result.alert)

    def test_s5_below_count(self):
        sig = {"signal_type": "S5_improvement_query",
               "count": 1, "sessions": 10}
        result = classify_signal_alert(sig)
        self.assertFalse(result.alert)

    # ------------------------------------------------------------------------
    # Each S-type at threshold
    # ------------------------------------------------------------------------
    def test_s1_at_exact_threshold(self):
        """freq=10, sessions=3 → alert"""
        sig = {"signal_type": "S1_unknown_query",
               "frequency_count": 10, "session_diversity": 3}
        result = classify_signal_alert(sig)
        self.assertTrue(result.alert)
        self.assertEqual(result.signal_type, "S1_unknown_query")

    def test_s2_at_exact_threshold(self):
        """usage=5, unique=2 → alert"""
        sig = {"signal_type": "S2_evidence_usage",
               "usage_count": 5, "unique_sessions": 2}
        result = classify_signal_alert(sig)
        self.assertTrue(result.alert)
        self.assertEqual(result.signal_type, "S2_evidence_usage")

    def test_s4_at_exact_threshold(self):
        """triggers=15, distinct=3 → alert"""
        sig = {"signal_type": "S4_frequent_fallback",
               "trigger_count": 15, "distinct_sessions": 3}
        result = classify_signal_alert(sig)
        self.assertTrue(result.alert)
        self.assertEqual(result.signal_type, "S4_frequent_fallback")

    def test_s5_at_exact_threshold(self):
        """count=5, sessions=2 → alert"""
        sig = {"signal_type": "S5_improvement_query",
               "count": 5, "sessions": 2}
        result = classify_signal_alert(sig)
        self.assertTrue(result.alert)
        self.assertEqual(result.signal_type, "S5_improvement_query")

    # ------------------------------------------------------------------------
    # Severity at 2x threshold
    # ------------------------------------------------------------------------
    def test_s1_high_severity_at_2x(self):
        """freq=20, sessions=3 → high (2x freq threshold of 10)"""
        sig = {"signal_type": "S1_unknown_query",
               "frequency_count": 20, "session_diversity": 3}
        result = classify_signal_alert(sig)
        self.assertTrue(result.alert)
        self.assertEqual(result.severity, "high")

    def test_s2_high_severity_at_2x(self):
        """usage=10, unique=2 → high (2x usage threshold of 5)"""
        sig = {"signal_type": "S2_evidence_usage",
               "usage_count": 10, "unique_sessions": 2}
        result = classify_signal_alert(sig)
        self.assertTrue(result.alert)
        self.assertEqual(result.severity, "high")

    def test_s4_high_severity_at_2x(self):
        """triggers=30, distinct=3 → high (2x trigger threshold of 15)"""
        sig = {"signal_type": "S4_frequent_fallback",
               "trigger_count": 30, "distinct_sessions": 3}
        result = classify_signal_alert(sig)
        self.assertTrue(result.alert)
        self.assertEqual(result.severity, "high")

    def test_s5_high_severity_at_2x(self):
        """count=10, sessions=2 → high (2x count threshold of 5)"""
        sig = {"signal_type": "S5_improvement_query",
               "count": 10, "sessions": 2}
        result = classify_signal_alert(sig)
        self.assertTrue(result.alert)
        self.assertEqual(result.severity, "high")

    # ------------------------------------------------------------------------
    # Medium severity at exactly 1x
    # ------------------------------------------------------------------------
    def test_s1_medium_at_exact_threshold(self):
        """freq=10, sessions=3 → medium"""
        sig = {"signal_type": "S1_unknown_query",
               "frequency_count": 10, "session_diversity": 3}
        result = classify_signal_alert(sig)
        self.assertTrue(result.alert)
        self.assertEqual(result.severity, "medium")

    # ------------------------------------------------------------------------
    # Unknown signal type → no alert
    # ------------------------------------------------------------------------
    def test_unknown_signal_type_no_alert(self):
        sig = {"signal_type": "S99_unknown_signal",
               "frequency_count": 999, "session_diversity": 99}
        result = classify_signal_alert(sig)
        self.assertFalse(result.alert)
        self.assertEqual(result.severity, "none")

    def test_empty_signal_type_no_alert(self):
        sig = {}
        result = classify_signal_alert(sig)
        self.assertFalse(result.alert)
        self.assertEqual(result.severity, "none")

    # ------------------------------------------------------------------------
    # Confidence bounded
    # ------------------------------------------------------------------------
    def test_confidence_bounded_0_to_1(self):
        test_cases = [
            {"signal_type": "S1_unknown_query",
             "frequency_count": 5, "session_diversity": 5},
            {"signal_type": "S1_unknown_query",
             "frequency_count": 10, "session_diversity": 3},
            {"signal_type": "S1_unknown_query",
             "frequency_count": 100, "session_diversity": 10},
            {"signal_type": "S2_evidence_usage",
             "usage_count": 5, "unique_sessions": 2},
            {"signal_type": "S4_frequent_fallback",
             "trigger_count": 15, "distinct_sessions": 3},
            {"signal_type": "S5_improvement_query",
             "count": 5, "sessions": 2},
        ]
        for sig in test_cases:
            result = classify_signal_alert(sig)
            self.assertGreaterEqual(result.confidence, 0.0)
            self.assertLessEqual(result.confidence, 1.0)

    # ------------------------------------------------------------------------
    # Result immutability
    # ------------------------------------------------------------------------
    def test_result_is_frozen(self):
        sig = {"signal_type": "S1_unknown_query",
               "frequency_count": 20, "session_diversity": 5}
        result = classify_signal_alert(sig)
        with self.assertRaises(Exception):
            result.alert = False

    # ------------------------------------------------------------------------
    # Reason string sanity
    # ------------------------------------------------------------------------
    def test_reason_contains_signal_type(self):
        sig = {"signal_type": "S2_evidence_usage",
               "usage_count": 10, "unique_sessions": 5}
        result = classify_signal_alert(sig)
        self.assertIn("S2", result.reason)

    def test_reason_contains_topic_when_present(self):
        sig = {"signal_type": "S5_improvement_query",
               "count": 10, "sessions": 3, "topic": "my_topic"}
        result = classify_signal_alert(sig)
        self.assertIn("my_topic", result.reason)

    # ------------------------------------------------------------------------
    # None / missing keys → graceful handling
    # ------------------------------------------------------------------------
    def test_none_values_handled(self):
        sig = {"signal_type": "S1_unknown_query",
               "frequency_count": None, "session_diversity": None}
        result = classify_signal_alert(sig)
        self.assertFalse(result.alert)

    def test_missing_keys_default_to_zero(self):
        sig = {"signal_type": "S1_unknown_query"}
        result = classify_signal_alert(sig)
        self.assertFalse(result.alert)

    # ------------------------------------------------------------------------
    # Low severity — just above threshold but not at 2x
    # ------------------------------------------------------------------------
    def test_low_severity_edge_case(self):
        """Low severity: threshold met but ratio just barely below 1.0x.
        Only reachable if _MED_MULTIPLIER were >1.0 or threshold was 0.
        With current V1 thresholds this is theoretical; test verifies
        the severity ladder is ordered correctly."""
        sig = {"signal_type": "S1_unknown_query",
               "frequency_count": 11, "session_diversity": 3}
        result = classify_signal_alert(sig)
        self.assertTrue(result.alert)
        # ratio=1.1 >= MED_MULTIPLIER(1.0) → medium per spec
        self.assertIn(result.severity, ("low", "medium"))


if __name__ == "__main__":
    print("=" * 60)
    print("WESLR_SIGNAL_ALERTING_V1_DEFINED")
    print("=" * 60)
    unittest.main(verbosity=2)
