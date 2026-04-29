"""
WESLR Pressure Aggregation Layer V1 — Tests

Validates:
- aggregation across multiple runs
- correct grouping by pressure type
- persistence score calculation
- empty runs handling
- deterministic output
- no forbidden fields
- no-write proof
- value_inference_applied always false
- behavior_change_allowed always false

Run:
  python3 weslr/tests/test_pressure_aggregation_v1.py
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pressure_aggregation import aggregate_pressure_indicators


class TestPressureAggregationV1(unittest.TestCase):
    """Tests for WESLR Pressure Aggregation Layer V1."""

    # ------------------------------------------------------------------
    # Hard Constraints
    # ------------------------------------------------------------------

    def test_value_inference_applied_always_false(self):
        """value_inference_applied must always be False — hard constraint."""
        runs = [[
            {
                "pattern_id": "p1",
                "signal_type": "S2",
                "topic_normalized": "test",
                "candidate_pressure": "expansion",
                "basis": "S2 strengthening",
                "confidence": 0.8,
                "status": "strengthening",
            }
        ]]
        result = aggregate_pressure_indicators(runs)
        self.assertFalse(result["value_inference_applied"])

    def test_behavior_change_allowed_always_false(self):
        """behavior_change_allowed must always be False — hard constraint."""
        runs = [[
            {
                "pattern_id": "p1",
                "signal_type": "S4",
                "topic_normalized": "test",
                "candidate_pressure": "optimization",
                "basis": "S4 weakening",
                "confidence": 0.7,
                "status": "weakening",
            }
        ]]
        result = aggregate_pressure_indicators(runs)
        self.assertFalse(result["behavior_change_allowed"])

    def test_no_forbidden_fields(self):
        """Output must not contain ranking, recommendation, action, priority, dominant."""
        runs = [
            [
                {
                    "pattern_id": "p1",
                    "signal_type": "S1",
                    "topic_normalized": "test",
                    "candidate_pressure": "expansion",
                    "basis": "S1 strengthening",
                    "confidence": 0.8,
                    "status": "strengthening",
                },
                {
                    "pattern_id": "p2",
                    "signal_type": "S5",
                    "topic_normalized": "test",
                    "candidate_pressure": "optimization",
                    "basis": "S5 strengthening",
                    "confidence": 0.8,
                    "status": "strengthening",
                },
            ]
        ]
        result = aggregate_pressure_indicators(runs)
        for summary in result["pressure_summary"]:
            self.assertNotIn("ranking", summary)
            self.assertNotIn("recommendation", summary)
            self.assertNotIn("action", summary)
            self.assertNotIn("priority", summary)
            self.assertNotIn("dominant", summary)
            self.assertNotIn("preference", summary)
            self.assertNotIn("want", summary)
            self.assertNotIn("goal", summary)
            self.assertNotIn("value", summary)

    # ------------------------------------------------------------------
    # Aggregation Logic
    # ------------------------------------------------------------------

    def test_single_run_single_pressure(self):
        """Single run with one pressure type → correct aggregation."""
        runs = [[
            {
                "pattern_id": "p1",
                "signal_type": "S2",
                "topic_normalized": "test",
                "candidate_pressure": "expansion",
                "basis": "S2 strengthening",
                "confidence": 0.9,
                "status": "strengthening",
            }
        ]]
        result = aggregate_pressure_indicators(runs)
        self.assertEqual(result["total_runs"], 1)
        self.assertEqual(len(result["pressure_summary"]), 1)
        summary = result["pressure_summary"][0]
        self.assertEqual(summary["candidate_pressure"], "expansion")
        self.assertEqual(summary["occurrences"], 1)
        self.assertEqual(summary["run_diversity"], 1)
        self.assertEqual(summary["temporal_span"], 0.0)

    def test_multiple_runs_grouping(self):
        """Multiple runs → grouped by candidate_pressure correctly."""
        runs = [
            [  # Run 0
                {
                    "pattern_id": "p1",
                    "signal_type": "S1",
                    "topic_normalized": "test",
                    "candidate_pressure": "expansion",
                    "basis": "S1",
                    "confidence": 0.8,
                    "status": "strengthening",
                },
                {
                    "pattern_id": "p2",
                    "signal_type": "S5",
                    "topic_normalized": "test",
                    "candidate_pressure": "optimization",
                    "basis": "S5",
                    "confidence": 0.8,
                    "status": "strengthening",
                },
            ],
            [  # Run 1
                {
                    "pattern_id": "p3",
                    "signal_type": "S1",
                    "topic_normalized": "test",
                    "candidate_pressure": "expansion",
                    "basis": "S1",
                    "confidence": 0.85,
                    "status": "strengthening",
                },
                {
                    "pattern_id": "p4",
                    "signal_type": "S5",
                    "topic_normalized": "test",
                    "candidate_pressure": "optimization",
                    "basis": "S5",
                    "confidence": 0.8,
                    "status": "strengthening",
                },
            ],
            [  # Run 2
                {
                    "pattern_id": "p5",
                    "signal_type": "S1",
                    "topic_normalized": "test",
                    "candidate_pressure": "expansion",
                    "basis": "S1",
                    "confidence": 0.9,
                    "status": "strengthening",
                },
            ],
        ]
        result = aggregate_pressure_indicators(runs)
        self.assertEqual(result["total_runs"], 3)

        by_cp = {s["candidate_pressure"]: s for s in result["pressure_summary"]}

        # expansion: 3 occurrences across 3 runs (runs 0,1,2)
        self.assertEqual(by_cp["expansion"]["occurrences"], 3)
        self.assertEqual(by_cp["expansion"]["run_diversity"], 3)
        self.assertEqual(by_cp["expansion"]["temporal_span"], 2.0)  # runs 0→2 = span 2

        # optimization: 2 occurrences across 2 runs (runs 0,1)
        self.assertEqual(by_cp["optimization"]["occurrences"], 2)
        self.assertEqual(by_cp["optimization"]["run_diversity"], 2)
        self.assertEqual(by_cp["optimization"]["temporal_span"], 1.0)  # runs 0→1 = span 1

    def test_run_diversity_single_run(self):
        """Run appearing only in one run has run_diversity=1."""
        runs = [
            [
                {
                    "pattern_id": "p1",
                    "signal_type": "S2",
                    "topic_normalized": "test",
                    "candidate_pressure": "expansion",
                    "basis": "S2",
                    "confidence": 0.9,
                    "status": "strengthening",
                }
            ],
            [  # empty run
            ],
            [
                {
                    "pattern_id": "p2",
                    "signal_type": "S4",
                    "topic_normalized": "test",
                    "candidate_pressure": "unknown",
                    "basis": "S4",
                    "confidence": 0.6,
                    "status": "weakening",
                }
            ],
        ]
        result = aggregate_pressure_indicators(runs)
        self.assertEqual(result["total_runs"], 3)
        by_cp = {s["candidate_pressure"]: s for s in result["pressure_summary"]}
        self.assertEqual(by_cp["expansion"]["run_diversity"], 1)
        self.assertEqual(by_cp["unknown"]["run_diversity"], 1)

    def test_empty_runs(self):
        """Empty runs list → empty pressure_summary."""
        result = aggregate_pressure_indicators([])
        self.assertEqual(result["total_runs"], 0)
        self.assertEqual(result["pressure_summary"], [])

    def test_all_empty_runs(self):
        """All runs empty → empty pressure_summary."""
        runs = [[], [], []]
        result = aggregate_pressure_indicators(runs)
        self.assertEqual(result["total_runs"], 3)
        self.assertEqual(result["pressure_summary"], [])

    # ------------------------------------------------------------------
    # Persistence Score
    # ------------------------------------------------------------------

    def test_persistence_score_formula(self):
        """Persistence score = 0.4*norm_occ + 0.4*norm_div + 0.2*norm_span."""
        # 3 runs, expansion appears in all 3 runs with 2 occurrences each
        runs = [
            [
                {"pattern_id": "p1", "candidate_pressure": "expansion",
                 "signal_type": "S1", "topic_normalized": "t", "basis": "", "confidence": 0.8, "status": "s"},
                {"pattern_id": "p2", "candidate_pressure": "expansion",
                 "signal_type": "S1", "topic_normalized": "t", "basis": "", "confidence": 0.8, "status": "s"},
            ],
            [
                {"pattern_id": "p3", "candidate_pressure": "expansion",
                 "signal_type": "S1", "topic_normalized": "t", "basis": "", "confidence": 0.8, "status": "s"},
                {"pattern_id": "p4", "candidate_pressure": "expansion",
                 "signal_type": "S1", "topic_normalized": "t", "basis": "", "confidence": 0.8, "status": "s"},
            ],
            [],  # empty run
        ]
        result = aggregate_pressure_indicators(runs)
        exp = [s for s in result["pressure_summary"] if s["candidate_pressure"] == "expansion"][0]

        # occurrences=4, run_diversity=2, temporal_span=1 (run 0→1)
        # max_occurrences=4
        # norm_occ = 4/4 = 1.0
        # norm_div = 2/3 = 0.6667
        # norm_span = 1/2 = 0.5
        # score = 0.4*1.0 + 0.4*(2/3) + 0.2*0.5 = 0.4 + 0.2667 + 0.1 = 0.7667
        self.assertAlmostEqual(exp["persistence_score"], 0.7667, places=3)

    def test_persistence_score_clamped_0_to_1(self):
        """Persistence score must be clamped to [0.0, 1.0]."""
        # Very sparse case: single occurrence in single run
        runs = [[
            {
                "pattern_id": "p1",
                "signal_type": "S3",
                "topic_normalized": "test",
                "candidate_pressure": "unknown",
                "basis": "unmapped",
                "confidence": 0.5,
                "status": "stable",
            }
        ]]
        result = aggregate_pressure_indicators(runs)
        score = result["pressure_summary"][0]["persistence_score"]
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_single_run_no_temporal_span(self):
        """Single run → temporal_span = 0, norm_span = 0."""
        runs = [[
            {
                "pattern_id": "p1",
                "signal_type": "S1",
                "topic_normalized": "test",
                "candidate_pressure": "expansion",
                "basis": "S1",
                "confidence": 0.9,
                "status": "strengthening",
            }
        ]]
        result = aggregate_pressure_indicators(runs)
        summary = result["pressure_summary"][0]
        self.assertEqual(summary["temporal_span"], 0.0)
        self.assertGreaterEqual(summary["persistence_score"], 0.0)

    # ------------------------------------------------------------------
    # Determinism
    # ------------------------------------------------------------------

    def test_deterministic_output(self):
        """Same input → same output every time."""
        runs = [
            [
                {"pattern_id": "p1", "candidate_pressure": "expansion",
                 "signal_type": "S1", "topic_normalized": "t1", "basis": "", "confidence": 0.8, "status": "s"},
                {"pattern_id": "p2", "candidate_pressure": "optimization",
                 "signal_type": "S5", "topic_normalized": "t2", "basis": "", "confidence": 0.8, "status": "s"},
            ],
            [
                {"pattern_id": "p3", "candidate_pressure": "expansion",
                 "signal_type": "S2", "topic_normalized": "t1", "basis": "", "confidence": 0.85, "status": "s"},
            ],
        ]
        result1 = aggregate_pressure_indicators(runs)
        result2 = aggregate_pressure_indicators(runs)
        self.assertEqual(result1, result2)

    def test_ordering_stable_alphabetical(self):
        """pressure_summary is sorted alphabetically by candidate_pressure."""
        runs = [
            [
                {"pattern_id": "p1", "candidate_pressure": "unknown",
                 "signal_type": "S3", "topic_normalized": "t", "basis": "", "confidence": 0.5, "status": "stable"},
                {"pattern_id": "p2", "candidate_pressure": "expansion",
                 "signal_type": "S1", "topic_normalized": "t", "basis": "", "confidence": 0.8, "status": "strengthening"},
                {"pattern_id": "p3", "candidate_pressure": "optimization",
                 "signal_type": "S5", "topic_normalized": "t", "basis": "", "confidence": 0.8, "status": "strengthening"},
            ],
        ]
        result = aggregate_pressure_indicators(runs)
        cps = [s["candidate_pressure"] for s in result["pressure_summary"]]
        self.assertEqual(cps, sorted(cps))

    # ------------------------------------------------------------------
    # No-Write Proof
    # ------------------------------------------------------------------

    def test_no_write_to_files(self):
        """Function must not write any files."""
        import tempfile
        import os

        runs = [[
            {
                "pattern_id": "p_write",
                "signal_type": "S2",
                "topic_normalized": "write_test",
                "candidate_pressure": "expansion",
                "basis": "test",
                "confidence": 0.9,
                "status": "strengthening",
            }
        ]]

        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                result = aggregate_pressure_indicators(runs)
            finally:
                os.chdir(old_cwd)

        self.assertIsInstance(result, dict)
        self.assertIn("pressure_summary", result)

    # ------------------------------------------------------------------
    # Total Runs Counted Correctly
    # ------------------------------------------------------------------

    def test_total_runs_includes_empty_runs(self):
        """total_runs must count all runs including empty ones."""
        runs = [[], [{"pattern_id": "p1", "candidate_pressure": "optimization",
                       "signal_type": "S5", "topic_normalized": "t", "basis": "", "confidence": 0.8, "status": "s"}], []]
        result = aggregate_pressure_indicators(runs)
        self.assertEqual(result["total_runs"], 3)

    # ------------------------------------------------------------------
    # Unknown Pressure
    # ------------------------------------------------------------------

    def test_unknown_pressure_grouped(self):
        """Unknown pressure types grouped correctly."""
        runs = [
            [
                {"pattern_id": "u1", "candidate_pressure": "unknown",
                 "signal_type": "S3", "topic_normalized": "t", "basis": "", "confidence": 0.5, "status": "stable"},
                {"pattern_id": "u2", "candidate_pressure": "unknown",
                 "signal_type": "S6", "topic_normalized": "t", "basis": "", "confidence": 0.5, "status": "stable"},
            ],
            [
                {"pattern_id": "u3", "candidate_pressure": "unknown",
                 "signal_type": "S3", "topic_normalized": "t", "basis": "", "confidence": 0.6, "status": "stable"},
            ],
        ]
        result = aggregate_pressure_indicators(runs)
        unknown = [s for s in result["pressure_summary"] if s["candidate_pressure"] == "unknown"][0]
        self.assertEqual(unknown["occurrences"], 3)
        self.assertEqual(unknown["run_diversity"], 2)

    # ------------------------------------------------------------------
    # Occurrences Cumulative Across Runs
    # ------------------------------------------------------------------

    def test_occurrences_cumulative(self):
        """occurrences = sum across all runs."""
        runs = [
            [{"pattern_id": "p1", "candidate_pressure": "expansion",
              "signal_type": "S1", "topic_normalized": "t", "basis": "", "confidence": 0.8, "status": "s"}],
            [
                {"pattern_id": "p2", "candidate_pressure": "expansion",
                 "signal_type": "S1", "topic_normalized": "t", "basis": "", "confidence": 0.8, "status": "s"},
                {"pattern_id": "p3", "candidate_pressure": "expansion",
                 "signal_type": "S2", "topic_normalized": "t", "basis": "", "confidence": 0.8, "status": "s"},
            ],
            [{"pattern_id": "p4", "candidate_pressure": "expansion",
              "signal_type": "S1", "topic_normalized": "t", "basis": "", "confidence": 0.9, "status": "s"}],
        ]
        result = aggregate_pressure_indicators(runs)
        exp = [s for s in result["pressure_summary"] if s["candidate_pressure"] == "expansion"][0]
        self.assertEqual(exp["occurrences"], 4)  # 1 + 2 + 1


if __name__ == "__main__":
    unittest.main()