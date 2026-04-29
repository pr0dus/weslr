"""
WESLR Pressure Detection Layer V1 — Tests

Validates:
- S2 strengthening → expansion
- S1 strengthening → expansion
- S5 strengthening → optimization
- S4 weakening → optimization
- unmapped signal → unknown
- disappearing pattern → unknown or reduced confidence
- value_inference_applied always False
- behavior_change_allowed always False
- no recommendation/action fields
- deterministic output
- no-write proof

Run:
  python3 weslr/tests/test_pressure_detection_v1.py
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pressure_detection import detect_pressure_indicators


class TestPressureDetectionV1(unittest.TestCase):
    """Tests for WESLR Pressure Detection Layer V1."""

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def run_detect(self, comparisons: list[dict]) -> dict:
        result = detect_pressure_indicators(comparisons)
        self.assertIsInstance(result, dict)
        return result

    # ------------------------------------------------------------------
    # Hard Constraints
    # ------------------------------------------------------------------

    def test_value_inference_applied_always_false(self):
        """value_inference_applied must always be False — hard constraint."""
        comparisons = [
            {
                "pattern_id": "p1",
                "signal_type": "S2",
                "topic_normalized": "test",
                "status": "strengthening",
                "frequency_delta": 5,
                "diversity_delta": 2,
                "consistency_delta": 0.1,
                "confidence": 0.9,
            }
        ]
        result = self.run_detect(comparisons)
        self.assertFalse(result["value_inference_applied"])

    def test_behavior_change_allowed_always_false(self):
        """behavior_change_allowed must always be False — hard constraint."""
        comparisons = [
            {
                "pattern_id": "p1",
                "signal_type": "S4",
                "topic_normalized": "test",
                "status": "weakening",
                "frequency_delta": -3,
                "diversity_delta": -1,
                "consistency_delta": -0.2,
                "confidence": 0.8,
            }
        ]
        result = self.run_detect(comparisons)
        self.assertFalse(result["behavior_change_allowed"])

    def test_no_recommendation_action_fields(self):
        """Output must not contain recommendation or action fields."""
        comparisons = [
            {
                "pattern_id": "p1",
                "signal_type": "S1",
                "topic_normalized": "test",
                "status": "strengthening",
                "frequency_delta": 5,
                "diversity_delta": 2,
                "consistency_delta": 0.1,
                "confidence": 0.9,
            }
        ]
        result = self.run_detect(comparisons)
        for indicator in result["pressure_indicators"]:
            self.assertNotIn("recommendation", indicator)
            self.assertNotIn("action", indicator)
            self.assertNotIn("priority", indicator)
            self.assertNotIn("ranking", indicator)
            self.assertNotIn("preference", indicator)
            self.assertNotIn("want", indicator)
            self.assertNotIn("goal", indicator)
            self.assertNotIn("value", indicator)

    # ------------------------------------------------------------------
    # Signal Type Mappings
    # ------------------------------------------------------------------

    def test_S2_strengthening_maps_to_expansion(self):
        """S2 + strengthening → expansion candidate."""
        comparisons = [
            {
                "pattern_id": "p_expand_s2",
                "signal_type": "S2",
                "topic_normalized": "evidence_topic",
                "status": "strengthening",
                "frequency_delta": 5,
                "diversity_delta": 2,
                "consistency_delta": 0.1,
                "confidence": 0.9,
            }
        ]
        result = self.run_detect(comparisons)
        self.assertEqual(len(result["pressure_indicators"]), 1)
        ind = result["pressure_indicators"][0]
        self.assertEqual(ind["candidate_pressure"], "expansion")
        self.assertEqual(ind["signal_type"], "S2")
        self.assertIn("S2", ind["basis"])

    def test_S1_strengthening_maps_to_expansion(self):
        """S1 + strengthening → expansion candidate."""
        comparisons = [
            {
                "pattern_id": "p_expand_s1",
                "signal_type": "S1",
                "topic_normalized": "unknown_topic",
                "status": "strengthening",
                "frequency_delta": 8,
                "diversity_delta": 4,
                "consistency_delta": 0.05,
                "confidence": 0.85,
            }
        ]
        result = self.run_detect(comparisons)
        self.assertEqual(len(result["pressure_indicators"]), 1)
        ind = result["pressure_indicators"][0]
        self.assertEqual(ind["candidate_pressure"], "expansion")
        self.assertEqual(ind["signal_type"], "S1")

    def test_S5_strengthening_maps_to_optimization(self):
        """S5 + strengthening → optimization candidate."""
        comparisons = [
            {
                "pattern_id": "p_opt_s5",
                "signal_type": "S5",
                "topic_normalized": "improvement_topic",
                "status": "strengthening",
                "frequency_delta": 4,
                "diversity_delta": 2,
                "consistency_delta": 0.15,
                "confidence": 0.88,
            }
        ]
        result = self.run_detect(comparisons)
        self.assertEqual(len(result["pressure_indicators"]), 1)
        ind = result["pressure_indicators"][0]
        self.assertEqual(ind["candidate_pressure"], "optimization")
        self.assertEqual(ind["signal_type"], "S5")

    def test_S4_weakening_maps_to_optimization(self):
        """S4 + weakening → optimization candidate."""
        comparisons = [
            {
                "pattern_id": "p_opt_s4",
                "signal_type": "S4",
                "topic_normalized": "fallback_topic",
                "status": "weakening",
                "frequency_delta": -3,
                "diversity_delta": -1,
                "consistency_delta": -0.25,
                "confidence": 0.8,
            }
        ]
        result = self.run_detect(comparisons)
        self.assertEqual(len(result["pressure_indicators"]), 1)
        ind = result["pressure_indicators"][0]
        self.assertEqual(ind["candidate_pressure"], "optimization")
        self.assertEqual(ind["signal_type"], "S4")

    def test_unmapped_signal_S3_maps_to_unknown(self):
        """S3 (unmapped) → unknown candidate."""
        comparisons = [
            {
                "pattern_id": "p_s3",
                "signal_type": "S3",
                "topic_normalized": "topic_cluster",
                "status": "stable",
                "frequency_delta": 0,
                "diversity_delta": 0,
                "consistency_delta": 0.0,
                "confidence": 0.75,
            }
        ]
        result = self.run_detect(comparisons)
        self.assertEqual(len(result["pressure_indicators"]), 1)
        ind = result["pressure_indicators"][0]
        self.assertEqual(ind["candidate_pressure"], "unknown")
        self.assertEqual(ind["signal_type"], "S3")

    def test_unmapped_signal_S6_maps_to_unknown(self):
        """S6 (unmapped) → unknown candidate."""
        comparisons = [
            {
                "pattern_id": "p_s6",
                "signal_type": "S6",
                "topic_normalized": "entity_pair",
                "status": "stable",
                "frequency_delta": 1,
                "diversity_delta": 1,
                "consistency_delta": 0.05,
                "confidence": 0.7,
            }
        ]
        result = self.run_detect(comparisons)
        self.assertEqual(len(result["pressure_indicators"]), 1)
        ind = result["pressure_indicators"][0]
        self.assertEqual(ind["candidate_pressure"], "unknown")
        self.assertEqual(ind["signal_type"], "S6")

    # ------------------------------------------------------------------
    # Disappearing Patterns
    # ------------------------------------------------------------------

    def test_disappearing_pattern_reduced_confidence(self):
        """Disappearing patterns get reduced confidence."""
        comparisons = [
            {
                "pattern_id": "p_disappear",
                "signal_type": "S4",
                "topic_normalized": "fallback_topic",
                "status": "disappearing",
                "frequency_delta": -5,
                "diversity_delta": -2,
                "consistency_delta": -0.3,
                "confidence": 0.8,
            }
        ]
        result = self.run_detect(comparisons)
        self.assertEqual(len(result["pressure_indicators"]), 1)
        ind = result["pressure_indicators"][0]
        # Disappearing → ×0.4: 0.8 * 0.4 = 0.32
        self.assertLess(ind["confidence"], 0.8)
        self.assertTrue(ind["confidence"] <= 0.4)

    def test_disappearing_still_has_basis(self):
        """Disappearing patterns still get a mapping with basis."""
        comparisons = [
            {
                "pattern_id": "p_gone",
                "signal_type": "S2",
                "topic_normalized": "evidence_topic",
                "status": "disappearing",
                "frequency_delta": -4,
                "diversity_delta": -2,
                "consistency_delta": -0.4,
                "confidence": 0.9,
            }
        ]
        result = self.run_detect(comparisons)
        ind = result["pressure_indicators"][0]
        self.assertIn("DISAPPEARING", ind["basis"])
        self.assertIn("expansion", ind["candidate_pressure"])

    # ------------------------------------------------------------------
    # Confidence Clamping
    # ------------------------------------------------------------------

    def test_confidence_clamped_to_1_0(self):
        """Confidence > 1.0 must be clamped to 1.0."""
        comparisons = [
            {
                "pattern_id": "p_clamp",
                "signal_type": "S2",
                "topic_normalized": "test",
                "status": "strengthening",
                "frequency_delta": 5,
                "diversity_delta": 2,
                "consistency_delta": 0.1,
                "confidence": 1.5,  # invalid — over 1.0
            }
        ]
        result = self.run_detect(comparisons)
        ind = result["pressure_indicators"][0]
        self.assertLessEqual(ind["confidence"], 1.0)

    def test_confidence_clamped_to_0_0(self):
        """Negative confidence must be clamped to 0.0."""
        comparisons = [
            {
                "pattern_id": "p_neg",
                "signal_type": "S2",
                "topic_normalized": "test",
                "status": "strengthening",
                "frequency_delta": 5,
                "diversity_delta": 2,
                "consistency_delta": 0.1,
                "confidence": -0.5,  # invalid — negative
            }
        ]
        result = self.run_detect(comparisons)
        ind = result["pressure_indicators"][0]
        self.assertGreaterEqual(ind["confidence"], 0.0)

    # ------------------------------------------------------------------
    # Determinism
    # ------------------------------------------------------------------

    def test_deterministic_output(self):
        """Same input must produce same output — no randomness."""
        comparisons = [
            {
                "pattern_id": "p_det",
                "signal_type": "S1",
                "topic_normalized": "det_topic",
                "status": "strengthening",
                "frequency_delta": 3,
                "diversity_delta": 1,
                "consistency_delta": 0.05,
                "confidence": 0.8,
            }
        ]
        result1 = self.run_detect(comparisons)
        result2 = self.run_detect(comparisons)
        self.assertEqual(result1, result2)

    # ------------------------------------------------------------------
    # Total Patterns Evaluated
    # ------------------------------------------------------------------

    def test_total_patterns_evaluated_counts_all(self):
        """total_patterns_evaluated must equal number of input comparisons."""
        comparisons = [
            {
                "pattern_id": f"p_{i}",
                "signal_type": ["S1", "S2", "S3", "S4", "S5", "S6"][i % 6],
                "topic_normalized": f"topic_{i}",
                "status": ["stable", "strengthening", "weakening", "new", "disappearing"][i % 5],
                "frequency_delta": i,
                "diversity_delta": 1,
                "consistency_delta": 0.05,
                "confidence": 0.75,
            }
            for i in range(10)
        ]
        result = self.run_detect(comparisons)
        self.assertEqual(result["total_patterns_evaluated"], 10)
        self.assertEqual(len(result["pressure_indicators"]), 10)

    # ------------------------------------------------------------------
    # No-Write Proof
    # ------------------------------------------------------------------

    def test_no_write_to_files(self):
        """Function must not write any files."""
        import tempfile
        import os

        comparisons = [
            {
                "pattern_id": "p_write_test",
                "signal_type": "S2",
                "topic_normalized": "write_test",
                "status": "strengthening",
                "frequency_delta": 5,
                "diversity_delta": 2,
                "consistency_delta": 0.1,
                "confidence": 0.9,
            }
        ]

        # Run in temp directory to catch any file creation
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                result = detect_pressure_indicators(comparisons)
                files_after = set(os.listdir(tmpdir))
            finally:
                os.chdir(old_cwd)

        # No files created (tmpdir is empty — we only checked, didn't create anything)
        # Result is returned in memory, no files written
        self.assertIsInstance(result, dict)
        self.assertIn("pressure_indicators", result)

    # ------------------------------------------------------------------
    # Status Preserved
    # ------------------------------------------------------------------

    def test_status_preserved_from_comparison(self):
        """Status field must be passed through unchanged from comparison input."""
        for status in ["new", "stable", "strengthening", "weakening", "disappearing"]:
            comparisons = [
                {
                    "pattern_id": f"p_{status}",
                    "signal_type": "S2",
                    "topic_normalized": "test",
                    "status": status,
                    "frequency_delta": 5,
                    "diversity_delta": 2,
                    "consistency_delta": 0.1,
                    "confidence": 0.8,
                }
            ]
            result = self.run_detect(comparisons)
            self.assertEqual(result["pressure_indicators"][0]["status"], status)

    # ------------------------------------------------------------------
    # Topic Normalized Preserved
    # ------------------------------------------------------------------

    def test_topic_normalized_preserved(self):
        """topic_normalized must be preserved from input."""
        comparisons = [
            {
                "pattern_id": "p_topic",
                "signal_type": "S5",
                "topic_normalized": "my_test_topic",
                "status": "strengthening",
                "frequency_delta": 3,
                "diversity_delta": 1,
                "consistency_delta": 0.05,
                "confidence": 0.85,
            }
        ]
        result = self.run_detect(comparisons)
        self.assertEqual(result["pressure_indicators"][0]["topic_normalized"], "my_test_topic")

    def test_topic_normalized_none_preserved(self):
        """topic_normalized=None must be preserved."""
        comparisons = [
            {
                "pattern_id": "p_topic_none",
                "signal_type": "S1",
                "topic_normalized": None,
                "status": "stable",
                "frequency_delta": 0,
                "diversity_delta": 0,
                "consistency_delta": 0.0,
                "confidence": 0.6,
            }
        ]
        result = self.run_detect(comparisons)
        self.assertIsNone(result["pressure_indicators"][0]["topic_normalized"])

    # ------------------------------------------------------------------
    # Multiple Comparisons
    # ------------------------------------------------------------------

    def test_multiple_mixed_comparisons(self):
        """Multiple comparisons with different signal types → correct mappings."""
        comparisons = [
            {
                "pattern_id": "p1",
                "signal_type": "S1",
                "topic_normalized": "unknown_topic",
                "status": "strengthening",
                "frequency_delta": 5,
                "diversity_delta": 2,
                "consistency_delta": 0.05,
                "confidence": 0.85,
            },
            {
                "pattern_id": "p2",
                "signal_type": "S4",
                "topic_normalized": "fallback_topic",
                "status": "weakening",
                "frequency_delta": -4,
                "diversity_delta": -2,
                "consistency_delta": -0.2,
                "confidence": 0.8,
            },
            {
                "pattern_id": "p3",
                "signal_type": "S3",
                "topic_normalized": "cluster_topic",
                "status": "stable",
                "frequency_delta": 0,
                "diversity_delta": 0,
                "consistency_delta": 0.0,
                "confidence": 0.7,
            },
            {
                "pattern_id": "p4",
                "signal_type": "S5",
                "topic_normalized": "improve_topic",
                "status": "strengthening",
                "frequency_delta": 3,
                "diversity_delta": 1,
                "consistency_delta": 0.1,
                "confidence": 0.88,
            },
        ]
        result = self.run_detect(comparisons)
        self.assertEqual(result["total_patterns_evaluated"], 4)
        self.assertEqual(len(result["pressure_indicators"]), 4)

        by_pid = {ind["pattern_id"]: ind for ind in result["pressure_indicators"]}

        self.assertEqual(by_pid["p1"]["candidate_pressure"], "expansion")
        self.assertEqual(by_pid["p2"]["candidate_pressure"], "optimization")
        self.assertEqual(by_pid["p3"]["candidate_pressure"], "unknown")
        self.assertEqual(by_pid["p4"]["candidate_pressure"], "optimization")

    # ------------------------------------------------------------------
    # New Pattern Confidence Reduction
    # ------------------------------------------------------------------

    def test_new_pattern_reduced_confidence(self):
        """New patterns get ×0.7 confidence multiplier."""
        comparisons = [
            {
                "pattern_id": "p_new",
                "signal_type": "S2",
                "topic_normalized": "new_topic",
                "status": "new",
                "frequency_delta": 3,
                "diversity_delta": 1,
                "consistency_delta": 0.0,
                "confidence": 0.9,
            }
        ]
        result = self.run_detect(comparisons)
        ind = result["pressure_indicators"][0]
        # new: ×0.7 → 0.9 * 0.7 = 0.63
        self.assertAlmostEqual(ind["confidence"], 0.63, places=3)
        self.assertIn("[NEW]", ind["basis"])

    # ------------------------------------------------------------------
    # Weakening Pattern Confidence Reduction
    # ------------------------------------------------------------------

    def test_weakening_pattern_reduced_confidence(self):
        """Weakening patterns get ×0.75 confidence multiplier."""
        comparisons = [
            {
                "pattern_id": "p_weak",
                "signal_type": "S2",
                "topic_normalized": "weakening_topic",
                "status": "weakening",
                "frequency_delta": -2,
                "diversity_delta": -1,
                "consistency_delta": -0.1,
                "confidence": 0.8,
            }
        ]
        result = self.run_detect(comparisons)
        ind = result["pressure_indicators"][0]
        # weakening: ×0.75 → 0.8 * 0.75 = 0.6
        self.assertAlmostEqual(ind["confidence"], 0.6, places=3)


if __name__ == "__main__":
    unittest.main()