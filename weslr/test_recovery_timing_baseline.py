#!/usr/bin/env python3
# test_recovery_timing_baseline.py - WESLR v80: Recovery Timing Baseline Tests
# Tests baseline measurement and hotspot analysis for recovery workflow.

from __future__ import annotations

import json
import os
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from weslr.recovery_timing_baseline import (
    TimingBenchmarkRun,
    HotspotAnalysis,
    RecoveryTimingBaselineRunner,
    compute_summary_statistics_with_confidence,
    compute_percentile,
)


class TestTimingBenchmarkRun(unittest.TestCase):
    """Test TimingBenchmarkRun dataclass."""
    
    def test_run_creation(self):
        """Test creating a timing benchmark run."""
        run = TimingBenchmarkRun(
            run_id="run-001",
            timestamp="2026-04-07T12:00:00Z",
            stage="v75_recommendation",
            substage="generation",
            batch_size=1,
            total_records=10,
            total_latency_ms=500.0,
            avg_ms=50.0,
            p50_ms=40.0,
            p50_available=True,
            max_ms=100.0,
            min_ms=20.0,
        )
        
        self.assertEqual(run.run_id, "run-001")
        self.assertEqual(run.stage, "v75_recommendation")
        self.assertEqual(run.batch_size, 1)
    
    def test_run_serialization(self):
        """Test run serialization to dict."""
        run = TimingBenchmarkRun(
            run_id="run-001",
            timestamp="2026-04-07T12:00:00Z",
            stage="v75_recommendation",
            substage="generation",
            batch_size=1,
            total_records=10,
            total_latency_ms=500.0,
            avg_ms=50.0,
            p50_ms=40.0,
            p50_available=True,
            p95_ms=80.0,
            p95_available=True,
            max_ms=100.0,
            min_ms=20.0,
        )
        
        data = run.to_dict()
        
        self.assertEqual(data["run_id"], "run-001")
        self.assertEqual(data["avg_ms"], 50.0)
        self.assertEqual(data["p95_ms"], 80.0)
    
    def test_run_json_serialization(self):
        """Test run serialization to JSON."""
        run = TimingBenchmarkRun(
            run_id="run-001",
            timestamp="2026-04-07T12:00:00Z",
            stage="v75_recommendation",
            substage="generation",
            batch_size=1,
            total_records=10,
            total_latency_ms=500.0,
            avg_ms=50.0,
            p50_ms=40.0,
            p50_available=True,
            max_ms=100.0,
            min_ms=20.0,
        )
        
        json_str = run.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["run_id"], "run-001")
        self.assertEqual(data["total_latency_ms"], 500.0)


class TestHotspotAnalysis(unittest.TestCase):
    """Test HotspotAnalysis dataclass."""
    
    def test_hotspot_creation(self):
        """Test creating a hotspot analysis."""
        hotspot = HotspotAnalysis(
            hotspot_id="hotspot-001",
            stage="v75_recommendation",
            substage="generation",
            avg_ms=50.0,
            p50_ms=40.0,
            max_ms=100.0,
            min_ms=20.0,
            variance=400.0,
            std_dev=20.0,
            sample_count=10,
            confidence_level="medium",
        )
        
        self.assertEqual(hotspot.hotspot_id, "hotspot-001")
        self.assertEqual(hotspot.stage, "v75_recommendation")
        self.assertEqual(hotspot.confidence_level, "medium")
    
    def test_hotspot_serialization(self):
        """Test hotspot serialization."""
        hotspot = HotspotAnalysis(
            hotspot_id="hotspot-001",
            stage="v75_recommendation",
            substage="generation",
            avg_ms=50.0,
            p50_ms=40.0,
            p95_ms=80.0,
            p99_ms=90.0,
            max_ms=100.0,
            min_ms=20.0,
            variance=400.0,
            std_dev=20.0,
            sample_count=10,
            confidence_level="medium",
        )
        
        data = hotspot.to_dict()
        
        self.assertEqual(data["avg_ms"], 50.0)
        self.assertEqual(data["p95_ms"], 80.0)
        self.assertEqual(data["p99_ms"], 90.0)
        self.assertEqual(data["sample_count"], 10)
    
    def test_hotspot_with_unavailable_p95_p99(self):
        """Test hotspot when p95/p99 not available."""
        hotspot = HotspotAnalysis(
            hotspot_id="hotspot-001",
            stage="v75_recommendation",
            substage="generation",
            avg_ms=50.0,
            p50_ms=40.0,
            max_ms=100.0,
            min_ms=20.0,
            variance=400.0,
            std_dev=20.0,
            sample_count=5,  # Less than 10
            confidence_level="low",
        )
        
        data = hotspot.to_dict()
        
        self.assertNotIn("p95_ms", data)
        self.assertNotIn("p99_ms", data)
        self.assertEqual(data["sample_count"], 5)
        self.assertEqual(data["confidence_level"], "low")


class TestRecoveryTimingBaselineRunner(unittest.TestCase):
    """Test RecoveryTimingBaselineRunner operations."""
    
    def setUp(self):
        """Set up runner for tests."""
        self.runner = RecoveryTimingBaselineRunner()
    
    def test_v75_recommendation_generation_benchmark(self):
        """Test v75 recommendation generation benchmark."""
        run = self.runner.run_v75_recommendation_generation(samples=5, batch_size=1)
        
        self.assertEqual(run.stage, "v75_recommendation")
        self.assertEqual(run.substage, "generation")
        # The warmup record is counted, so total is 6 (1 warmup + 5 samples)
        self.assertGreaterEqual(run.total_records, 5)
        self.assertGreater(run.avg_ms, 0.0)
        self.assertTrue(run.p50_available)
    
    def test_v76_recommendation_export_benchmark(self):
        """Test v76 recommendation export benchmark."""
        run = self.runner.run_v76_recommendation_export(samples=5, batch_size=1)
        
        self.assertEqual(run.stage, "v76_recommendation")
        self.assertEqual(run.substage, "export")
        self.assertGreaterEqual(run.total_records, 5)
        self.assertGreater(run.avg_ms, 0.0)
    
    def test_v77_recovery_review_benchmark(self):
        """Test v77 recovery review benchmark."""
        run = self.runner.run_v77_recovery_review(samples=5, batch_size=1)
        
        self.assertEqual(run.stage, "v77_recovery")
        self.assertEqual(run.substage, "review")
        self.assertGreaterEqual(run.total_records, 5)
        self.assertGreater(run.avg_ms, 0.0)
    
    def test_v78_decision_trace_export_benchmark(self):
        """Test v78 decision trace export benchmark."""
        run = self.runner.run_v78_decision_trace_export(samples=5, batch_size=1)
        
        self.assertEqual(run.stage, "v78_decision_trace")
        self.assertEqual(run.substage, "export")
        self.assertGreaterEqual(run.total_records, 5)
        self.assertGreater(run.avg_ms, 0.0)
    
    def test_multiple_benchmark_runs(self):
        """Test running multiple benchmarks."""
        run1 = self.runner.run_v75_recommendation_generation(samples=5, batch_size=1)
        run2 = self.runner.run_v76_recommendation_export(samples=5, batch_size=1)
        run3 = self.runner.run_v77_recovery_review(samples=5, batch_size=1)
        run4 = self.runner.run_v78_decision_trace_export(samples=5, batch_size=1)
        
        self.assertEqual(len(self.runner._runs), 4)
        self.assertEqual(self.runner._runs[0].stage, "v75_recommendation")
        self.assertEqual(self.runner._runs[1].stage, "v76_recommendation")
        self.assertEqual(self.runner._runs[2].stage, "v77_recovery")
        self.assertEqual(self.runner._runs[3].stage, "v78_decision_trace")
    
    def test_identify_hotspots(self):
        """Test hotspot identification."""
        # Run all benchmarks with sufficient samples for p95/p99
        self.runner.run_v75_recommendation_generation(samples=20, batch_size=1)
        self.runner.run_v76_recommendation_export(samples=20, batch_size=1)
        self.runner.run_v77_recovery_review(samples=20, batch_size=1)
        self.runner.run_v78_decision_trace_export(samples=20, batch_size=1)
        
        # Identify hotspots
        hotspots = self.runner.identify_hotspots()
        
        self.assertGreater(len(hotspots), 0)
        self.assertEqual(len(hotspots), 4)
        
        # Verify confidence levels based on sample count
        for hotspot in hotspots:
            self.assertEqual(hotspot.sample_count, 21)
            # With 20 samples, confidence should be 'low' or better
            self.assertIn(hotspot.confidence_level, ["medium", "high", "low"])
    
    def test_hotspots_sorted_by_latency(self):
        """Test that hotspots are sorted by latency (descending)."""
        self.runner.run_v75_recommendation_generation(samples=20, batch_size=1)
        
        hotspots = self.runner.identify_hotspots()
        
        # Verify descending order
        for i in range(len(hotspots) - 1):
            self.assertGreaterEqual(hotspots[i].avg_ms, hotspots[i + 1].avg_ms)
    
    def test_baseline_summary(self):
        """Test baseline summary generation."""
        self.runner.run_v75_recommendation_generation(samples=10, batch_size=1)
        self.runner.run_v76_recommendation_export(samples=10, batch_size=1)
        
        summary = self.runner.get_baseline_summary()
        
        self.assertIn("baseline_summary_id", summary)
        self.assertEqual(summary["total_runs"], 2)
        self.assertIn("runs", summary)
        self.assertIn("hotspots", summary)
    
    def test_baseline_json_export(self):
        """Test baseline JSON export."""
        self.runner.run_v75_recommendation_generation(samples=10, batch_size=1)
        
        json_str = self.runner.export_baseline_json()
        data = json.loads(json_str)
        
        self.assertIn("baseline_summary_id", data)
        self.assertEqual(data["total_runs"], 1)
    
    def test_operator_readable_export(self):
        """Test operator-readable export."""
        self.runner.run_v75_recommendation_generation(samples=10, batch_size=1)
        self.runner.run_v76_recommendation_export(samples=10, batch_size=1)
        
        output = self.runner.export_operator_readable()
        
        self.assertIn("RECOVERY TIMING BASELINE SUMMARY", output)
        self.assertIn("BENCHMARK RUNS", output)
    
    def test_batch_size_comparison(self):
        """Test baseline with different batch sizes."""
        run1 = self.runner.run_v75_recommendation_generation(samples=5, batch_size=1)
        run2 = self.runner.run_v75_recommendation_generation(samples=5, batch_size=5)
        
        self.assertEqual(run1.batch_size, 1)
        self.assertEqual(run2.batch_size, 5)


class TestStatisticsHelpers(unittest.TestCase):
    """Test statistics helper functions."""
    
    def test_empty_latencies(self):
        """Test statistics with empty list."""
        stats = compute_summary_statistics_with_confidence([])
        
        self.assertEqual(stats["avg_ms"], 0.0)
        self.assertEqual(stats["p50_ms"], 0.0)
        self.assertEqual(stats["sample_count"], 0)
        self.assertFalse(stats["p95_available"])
        self.assertFalse(stats["p99_available"])
    
    def test_single_value(self):
        """Test statistics with single value."""
        stats = compute_summary_statistics_with_confidence([100.0])
        
        self.assertEqual(stats["avg_ms"], 100.0)
        self.assertEqual(stats["p50_ms"], 100.0)
        self.assertEqual(stats["sample_count"], 1)
        self.assertFalse(stats["p95_available"])  # < 10
        self.assertFalse(stats["p99_available"])  # < 10
    
    def test_multiple_values(self):
        """Test statistics with multiple values."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        stats = compute_summary_statistics_with_confidence(values)
        
        self.assertEqual(stats["avg_ms"], 30.0)
        self.assertEqual(stats["p50_ms"], 30.0)
        self.assertEqual(stats["max_ms"], 50.0)
        self.assertEqual(stats["min_ms"], 10.0)
        self.assertFalse(stats["p95_available"])  # < 10
    
    def test_p95_p99_with_sufficient_samples(self):
        """Test p95/p99 with sufficient samples."""
        values = list(range(100))  # 100 samples
        stats = compute_summary_statistics_with_confidence(values)
        
        self.assertTrue(stats["p95_available"])
        self.assertTrue(stats["p99_available"])
        self.assertIn("p95_ms", stats)
        self.assertIn("p99_ms", stats)
    
    def test_percentile_calculation(self):
        """Test percentile calculation."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        # Nearest-rank method
        self.assertEqual(compute_percentile(values, 50), 6)
        self.assertEqual(compute_percentile(values, 90), 10)
        self.assertEqual(compute_percentile(values, 100), 10)


class TestEndToEndBaseline(unittest.TestCase):
    """Test end-to-end baseline workflow."""
    
    def test_full_baseline_workflow(self):
        """Test complete baseline workflow end-to-end."""
        runner = RecoveryTimingBaselineRunner()
        
        # Run all benchmarks with sufficient samples
        run1 = runner.run_v75_recommendation_generation(samples=20, batch_size=1)
        run2 = runner.run_v76_recommendation_export(samples=20, batch_size=1)
        run3 = runner.run_v77_recovery_review(samples=20, batch_size=1)
        run4 = runner.run_v78_decision_trace_export(samples=20, batch_size=1)
        
        # Identify hotspots
        hotspots = runner.identify_hotspots()
        
        # Get summary
        summary = runner.get_baseline_summary()
        json_output = runner.export_baseline_json()
        operator_output = runner.export_operator_readable()
        
        # Verify
        self.assertEqual(len(runner._runs), 4)
        self.assertEqual(len(hotspots), 4)
        self.assertEqual(summary["total_runs"], 4)
        
        # Verify JSON is parseable
        parsed = json.loads(json_output)
        self.assertEqual(parsed["total_runs"], 4)
        
        # Verify operator-readable contains expected sections
        self.assertIn("RECOVERY TIMING BASELINE SUMMARY", operator_output)
        self.assertIn("BENCHMARK RUNS", operator_output)
        self.assertIn("MEASURED HOTSPOTS", operator_output)


if __name__ == "__main__":
    unittest.main()
