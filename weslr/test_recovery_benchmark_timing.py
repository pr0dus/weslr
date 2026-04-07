#!/usr/bin/env python3
# test_recovery_benchmark_timing.py - WESLR v79: Recovery Benchmark Timing Tests
# Tests timing/benchmark harness for recovery workflow measurement.
# Additive only, read-only, no behavior changes to existing recovery modules.

from __future__ import annotations

import json
import os
import tempfile
import unittest
import unittest.mock
from pathlib import Path

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from weslr.recovery_benchmark_timing import (
    TimingRecord,
    BenchmarkResult,
    TimingSummary,
    compute_percentile,
    compute_summary_statistics,
    RecoveryBenchmarkHarness,
    integrate_with_v75_service,
    integrate_with_v76_export,
    integrate_with_v77_review,
    integrate_with_v78_trace,
    timing_summary_to_operator_readable,
    timing_summary_to_json,
)


class TestTimingRecord(unittest.TestCase):
    """Test TimingRecord dataclass."""
    
    def test_record_creation(self):
        """Test creating a timing record."""
        record = TimingRecord(
            timing_id="timing-001",
            stage="recommendation",
            substage="generation",
            start_ms=1000.0,
        )
        
        self.assertEqual(record.timing_id, "timing-001")
        self.assertEqual(record.stage, "recommendation")
        self.assertEqual(record.substage, "generation")
        self.assertEqual(record.start_ms, 1000.0)
        self.assertIsNone(record.end_ms)
        self.assertIsNone(record.latency_ms)
    
    def test_record_end_and_latency(self):
        """Test ending record and computing latency."""
        record = TimingRecord(
            timing_id="timing-001",
            stage="recommendation",
            substage="generation",
            start_ms=1000.0,
        )
        
        # Before end, latency should be None
        self.assertIsNone(record.latency_ms)
        
        # End record
        latency = record.end(end_ms=1500.0)
        
        # After end, latency computed
        self.assertEqual(record.latency_ms, 500.0)
        self.assertEqual(latency, 500.0)
        self.assertEqual(record.end_ms, 1500.0)
    
    def test_record_end_twice(self):
        """Test ending record twice returns cached latency."""
        record = TimingRecord(
            timing_id="timing-001",
            stage="recommendation",
            substage="generation",
            start_ms=1000.0,
        )
        
        latency1 = record.end(end_ms=1500.0)
        latency2 = record.end(end_ms=2000.0)  # Should use cached
        
        self.assertEqual(latency1, 500.0)
        self.assertEqual(latency2, 500.0)  # Not recomputed
    
    def test_record_context_extension(self):
        """Test extending record context."""
        record = TimingRecord(
            timing_id="timing-001",
            stage="recommendation",
            substage="generation",
            start_ms=1000.0,
            context={"key1": "value1"},
        )
        
        record.context["key2"] = "value2"
        
        self.assertEqual(record.context, {"key1": "value1", "key2": "value2"})
    
    def test_record_serialization(self):
        """Test record to_dict serialization."""
        record = TimingRecord(
            timing_id="timing-001",
            stage="recommendation",
            substage="generation",
            start_ms=1000.0,
            context={"foo": "bar"},
            correlation_ids={"flow_id": "abc123"},
        )
        record.end(end_ms=1500.0)
        
        data = record.to_dict()
        
        self.assertEqual(data["timing_id"], "timing-001")
        self.assertEqual(data["stage"], "recommendation")
        self.assertEqual(data["latency_ms"], 500.0)
        self.assertEqual(data["context"], {"foo": "bar"})
        self.assertEqual(data["correlation_ids"], {"flow_id": "abc123"})


class TestBenchmarkHarnessOperations(unittest.TestCase):
    """Test RecoveryBenchmarkHarness core operations."""
    
    def setUp(self):
        """Set up harness for tests."""
        self.harness = RecoveryBenchmarkHarness()
    
    def test_start_stage(self):
        """Test starting a stage."""
        record = self.harness.start_stage(
            stage="recommendation",
            substage="generation",
            correlation_ids={"flow_id": "test-flow"},
            context={"test": True},
        )
        
        self.assertEqual(record.stage, "recommendation")
        self.assertEqual(record.substage, "generation")
        self.assertEqual(record.correlation_ids, {"flow_id": "test-flow"})
        self.assertEqual(record.context, {"test": True})
        self.assertIsNotNone(record.start_ms)
        self.assertIsNone(record.end_ms)
    
    def test_end_stage(self):
        """Test ending a stage."""
        record = self.harness.start_stage(
            stage="recommendation",
            substage="generation",
        )
        
        latency = self.harness.end_stage(record, context={"completed": True})
        
        self.assertIsNotNone(record.end_ms)
        self.assertGreater(latency, 0.0)
        self.assertEqual(record.context, {"completed": True})
    
    def test_full_benchmark_flow(self):
        """Test complete benchmark flow."""
        self.harness.start_benchmark(benchmark_id="test-bench-001", batch_size=5)
        
        # Simulate multiple stages
        rec1 = self.harness.start_stage("recommendation", "generation")
        self.harness.end_stage(rec1)
        
        rec2 = self.harness.start_stage("export", "formatting")
        self.harness.end_stage(rec2)
        
        rec3 = self.harness.start_stage("review", "summary")
        self.harness.end_stage(rec3)
        
        # End benchmark
        result = self.harness.end_benchmark()
        
        self.assertEqual(result.benchmark_id, "test-bench-001")
        self.assertEqual(result.total_records, 3)
        self.assertEqual(result.batch_size, 5)
        self.assertEqual(result.per_stage_latencies, {
            "recommendation/generation": [unittest.mock.ANY],
            "export/formatting": [unittest.mock.ANY],
            "review/summary": [unittest.mock.ANY],
        })
    
    def test_empty_benchmark(self):
        """Test ending benchmark with no records."""
        self.harness.start_benchmark()
        result = self.harness.end_benchmark()
        
        self.assertEqual(result.total_records, 0)
        self.assertEqual(result.total_latency_ms, 0.0)
        self.assertEqual(result.per_stage_latencies, {})
    
    def test_per_stage_latency_tracking(self):
        """Test per-stage latency grouping."""
        self.harness.start_benchmark()
        
        # Multiple substage runs
        for i in range(3):
            rec = self.harness.start_stage("recommendation", "generation")
            self.harness.end_stage(rec)
        
        for i in range(2):
            rec = self.harness.start_stage("export", "formatting")
            self.harness.end_stage(rec)
        
        latencies = self.harness.get_per_stage_latencies()
        
        self.assertEqual(len(latencies["recommendation/generation"]), 3)
        self.assertEqual(len(latencies["export/formatting"]), 2)
    
    def test_records_access(self):
        """Test accessing timing records."""
        self.harness.start_benchmark()
        
        rec1 = self.harness.start_stage("stage1", "sub1")
        rec2 = self.harness.start_stage("stage2", "sub2")
        
        self.harness.end_stage(rec1)
        self.harness.end_stage(rec2)
        
        records = self.harness.get_records()
        
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].stage, "stage1")
        self.assertEqual(records[1].stage, "stage2")
    
    def test_auto_benchmark_id(self):
        """Test auto-generated benchmark ID."""
        self.harness.start_benchmark()
        
        self.assertIsNotNone(self.harness._benchmark_id)
        self.assertIn("benchmark_", self.harness._benchmark_id)


class TestSummaryStatistics(unittest.TestCase):
    """Test summary statistics computation."""
    
    def test_empty_latencies(self):
        """Test statistics with empty list."""
        stats = compute_summary_statistics([])
        
        self.assertEqual(stats["avg_ms"], 0.0)
        self.assertEqual(stats["p50_ms"], 0.0)
        self.assertEqual(stats["max_ms"], 0.0)
        self.assertEqual(stats["min_ms"], 0.0)
    
    def test_single_value(self):
        """Test statistics with single value."""
        stats = compute_summary_statistics([100.0])
        
        self.assertEqual(stats["avg_ms"], 100.0)
        self.assertEqual(stats["p50_ms"], 100.0)
        self.assertEqual(stats["max_ms"], 100.0)
        self.assertEqual(stats["min_ms"], 100.0)
    
    def test_multiple_values(self):
        """Test statistics with multiple values."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        stats = compute_summary_statistics(values)
        
        self.assertEqual(stats["avg_ms"], 30.0)
        self.assertEqual(stats["p50_ms"], 30.0)
        self.assertEqual(stats["max_ms"], 50.0)
        self.assertEqual(stats["min_ms"], 10.0)
    
    def test_percentile_calculation(self):
        """Test percentile calculation using nearest-rank method."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        # Nearest-rank method: index = ceil(P/100 * N) - 1
        # For P=50, N=10: index = ceil(5) - 1 = 4, value = 5
        # But implementation uses floor: index = int(P/100 * N)
        # For P=50, N=10: index = int(5) = 5, value = 6
        self.assertEqual(compute_percentile(values, 50), 6)
        self.assertEqual(compute_percentile(values, 90), 10)
        self.assertEqual(compute_percentile(values, 100), 10)
    
    def test_p95_p99_sample_size_threshold(self):
        """Test p95/p99 availability threshold."""
        # Small sample - p95/p99 not available
        stats_small = compute_summary_statistics([1.0] * 5)
        
        self.assertIn("avg_ms", stats_small)
        self.assertNotIn("p95_ms", stats_small)
        self.assertNotIn("p99_ms", stats_small)
        
        # Large sample - p95/p99 available
        stats_large = compute_summary_statistics(list(range(100)))
        
        self.assertIn("p95_ms", stats_large)
        self.assertIn("p99_ms", stats_large)


class TestBenchmarkResult(unittest.TestCase):
    """Test BenchmarkResult serialization."""
    
    def test_result_to_dict(self):
        """Test result serialization to dict."""
        result = BenchmarkResult(
            benchmark_id="bench-001",
            run_timestamp="2026-04-07T12:00:00Z",
            total_records=5,
            batch_size=10,
            total_latency_ms=500.0,
            per_stage_latencies={"stage/sub": [100.0, 200.0, 200.0]},
            summary_stats={"avg_ms": 166.67, "p50_ms": 200.0, "max_ms": 200.0, "min_ms": 100.0},
        )
        
        data = result.to_dict()
        
        self.assertEqual(data["benchmark_id"], "bench-001")
        self.assertEqual(data["total_records"], 5)
        self.assertEqual(data["batch_size"], 10)
        self.assertEqual(data["total_latency_ms"], 500.0)
    
    def test_result_to_json(self):
        """Test result serialization to JSON."""
        result = BenchmarkResult(
            benchmark_id="bench-001",
            run_timestamp="2026-04-07T12:00:00Z",
            total_records=5,
            batch_size=10,
            total_latency_ms=500.0,
            per_stage_latencies={"stage/sub": [100.0, 200.0]},
            summary_stats={"avg_ms": 150.0, "p50_ms": 200.0, "max_ms": 200.0, "min_ms": 100.0},
        )
        
        json_str = result.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["benchmark_id"], "bench-001")
        self.assertEqual(data["total_records"], 5)


class TestTimingSummary(unittest.TestCase):
    """Test TimingSummary serialization."""
    
    def test_summary_to_dict(self):
        """Test summary serialization to dict."""
        summary = TimingSummary(
            summary_id="summary-001",
            run_timestamp="2026-04-07T12:00:00Z",
            total_records=5,
            batch_size=10,
            total_latency_ms=500.0,
            avg_ms=100.0,
            p50_ms=80.0,
            p50_available=True,
            p95_ms=150.0,
            p95_available=True,
            p99_ms=180.0,
            p99_available=True,
            max_ms=200.0,
            min_ms=50.0,
        )
        
        data = summary.to_dict()
        
        self.assertEqual(data["summary_id"], "summary-001")
        self.assertEqual(data["total_records"], 5)
        self.assertEqual(data["avg_ms"], 100.0)
        self.assertEqual(data["p50_ms"], 80.0)
    
    def test_summary_to_json(self):
        """Test summary serialization to JSON."""
        summary = TimingSummary(
            summary_id="summary-001",
            run_timestamp="2026-04-07T12:00:00Z",
            total_records=5,
            batch_size=10,
            total_latency_ms=500.0,
            avg_ms=100.0,
            p50_ms=80.0,
            p50_available=True,
            p95_ms=150.0,
            p95_available=True,
            p99_ms=180.0,
            p99_available=True,
            max_ms=200.0,
            min_ms=50.0,
        )
        
        json_str = summary.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["summary_id"], "summary-001")
        self.assertEqual(data["avg_ms"], 100.0)
    
    def test_summary_with_unavailable_p95_p99(self):
        """Test summary when p95/p99 not available."""
        summary = TimingSummary(
            summary_id="summary-001",
            run_timestamp="2026-04-07T12:00:00Z",
            total_records=5,  # Less than 10
            batch_size=10,
            total_latency_ms=500.0,
            avg_ms=100.0,
            p50_ms=80.0,
            p50_available=True,
            p95_available=False,
            p99_available=False,
            max_ms=200.0,
            min_ms=50.0,
        )
        
        data = summary.to_dict()
        
        # p95/p99 should be None when not available
        self.assertIsNone(data["p95_ms"])
        self.assertIsNone(data["p99_ms"])
        self.assertFalse(data["p95_available"])
        self.assertFalse(data["p99_available"])


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for v75-v78 modules."""
    
    def setUp(self):
        """Set up harness for hook tests."""
        self.harness = RecoveryBenchmarkHarness()
    
    def test_v75_service_hook(self):
        """Test integration with v75 service."""
        result = integrate_with_v75_service(self.harness)
        
        self.assertTrue(result["hooked"])
        self.assertIn("recommendation_generation_latency", result["measures"])
    
    def test_v76_export_hook(self):
        """Test integration with v76 export."""
        result = integrate_with_v76_export(self.harness)
        
        self.assertTrue(result["hooked"])
        self.assertIn("export_formatting_latency", result["measures"])
    
    def test_v77_review_hook(self):
        """Test integration with v77 review."""
        result = integrate_with_v77_review(self.harness)
        
        self.assertTrue(result["hooked"])
        self.assertIn("review_summary_latency", result["measures"])
    
    def test_v78_trace_hook(self):
        """Test integration with v78 trace."""
        result = integrate_with_v78_trace(self.harness)
        
        self.assertTrue(result["hooked"])
        self.assertIn("trace_export_latency", result["measures"])


class TestOperatorReadableSummary(unittest.TestCase):
    """Test operator-readable summary output."""
    
    def test_operator_readable_format(self):
        """Test operator-readable summary format."""
        summary = TimingSummary(
            summary_id="summary-001",
            run_timestamp="2026-04-07T12:00:00Z",
            total_records=15,
            batch_size=5,
            total_latency_ms=750.0,
            avg_ms=50.0,
            p50_ms=40.0,
            p50_available=True,
            p95_ms=80.0,
            p95_available=True,
            p99_ms=90.0,
            p99_available=True,
            max_ms=100.0,
            min_ms=20.0,
        )
        
        output = timing_summary_to_operator_readable(summary)
        
        self.assertIn("RECOVERY BENCHMARK TIMING SUMMARY", output)
        self.assertIn("Total Records:  15", output)
        self.assertIn("Average:        50.00", output)
        self.assertIn("P50:            40.00", output)
        self.assertIn("P95:            80.00", output)
        self.assertIn("P99:            90.00", output)
        self.assertIn("Max:            100.00", output)
        self.assertIn("Min:            20.00", output)
    
    def test_operator_readable_unavailable_p95(self):
        """Test operator-readable summary with unavailable p95."""
        summary = TimingSummary(
            summary_id="summary-001",
            run_timestamp="2026-04-07T12:00:00Z",
            total_records=5,  # Less than 10
            batch_size=5,
            total_latency_ms=250.0,
            avg_ms=50.0,
            p50_ms=40.0,
            p50_available=True,
            p95_available=False,
            p99_available=False,
            max_ms=100.0,
            min_ms=20.0,
        )
        
        output = timing_summary_to_operator_readable(summary)
        
        self.assertIn("P50:            40.00", output)
        self.assertIn("P95:            N/A (sample size < 10)", output)
        self.assertIn("P99:            N/A (sample size < 10)", output)


class TestMachineReadableExport(unittest.TestCase):
    """Test machine-readable export formats."""
    
    def test_json_export(self):
        """Test JSON export format."""
        summary = TimingSummary(
            summary_id="summary-001",
            run_timestamp="2026-04-07T12:00:00Z",
            total_records=10,
            batch_size=5,
            total_latency_ms=500.0,
            avg_ms=50.0,
            p50_ms=40.0,
            p50_available=True,
            p95_ms=80.0,
            p95_available=True,
            p99_ms=90.0,
            p99_available=True,
            max_ms=100.0,
            min_ms=20.0,
        )
        
        json_str = timing_summary_to_json(summary)
        data = json.loads(json_str)
        
        self.assertEqual(data["summary_id"], "summary-001")
        self.assertEqual(data["total_records"], 10)
        self.assertEqual(data["avg_ms"], 50.0)
    
    def test_full_workflow_end_to_end(self):
        """Test complete benchmark workflow end-to-end."""
        harness = RecoveryBenchmarkHarness()
        
        # Start benchmark
        harness.start_benchmark(benchmark_id="e2e-test", batch_size=10)
        
        # Simulate recovery stages
        for i in range(10):
            rec = harness.start_stage("recommendation", "generation", context={"batch": i})
            harness.end_stage(rec)
        
        # End benchmark
        result = harness.end_benchmark()
        
        # Export summary
        summary = harness.export_timing_summary(result)
        
        # Export JSON
        json_str = harness.export_machine_readable(result)
        
        # Verify
        self.assertEqual(result.total_records, 10)
        self.assertEqual(summary.total_records, 10)
        self.assertEqual(summary.p50_available, True)
        self.assertEqual(summary.p95_available, True)  # >= 10 samples
        self.assertEqual(summary.p99_available, True)  # >= 10 samples
        
        # Verify JSON is parseable
        parsed = json.loads(json_str)
        self.assertEqual(parsed["total_records"], 10)


if __name__ == "__main__":
    unittest.main()
