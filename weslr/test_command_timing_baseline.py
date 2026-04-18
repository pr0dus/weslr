#!/usr/bin/env python3
# test_command_timing_baseline.py - WESLR v81: Command Timing Baseline Tests
# Tests end-to-end command path timing measurement.

from __future__ import annotations

import json
import os
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from weslr.command_timing_baseline import (
    CommandTimingRecord,
    CommandTimingRun,
    CommandBaselineSummary,
    compute_percentile,
    compute_summary_statistics_with_confidence,
    CommandTimingBaselineRunner,
)


class TestCommandTimingRecord(unittest.TestCase):
    """Test CommandTimingRecord dataclass."""
    
    def test_record_creation(self):
        """Test creating a command timing record."""
        record = CommandTimingRecord(
            record_id="rec-001",
            command="diagnostics-summary",
            timestamp="2026-04-07T12:00:00Z",
            start_ms=1000.0,
            end_ms=1050.0,
            latency_ms=50.0,
            warmup=False,
            batch_index=0,
            output_chars=1000,
        )
        
        self.assertEqual(record.record_id, "rec-001")
        self.assertEqual(record.command, "diagnostics-summary")
        self.assertEqual(record.latency_ms, 50.0)
    
    def test_record_end_method(self):
        """Test record end method."""
        record = CommandTimingRecord(
            record_id="rec-001",
            command="diagnostics-summary",
            timestamp="2026-04-07T12:00:00Z",
            start_ms=1000.0,
            end_ms=None,
            latency_ms=None,
            warmup=False,
            batch_index=0,
            output_chars=1000,
        )
        
        self.assertIsNone(record.end_ms)
        self.assertIsNone(record.latency_ms)
        
        latency = record.end(end_ms=1050.0)
        
        self.assertEqual(record.end_ms, 1050.0)
        self.assertEqual(record.latency_ms, 50.0)
        self.assertEqual(latency, 50.0)
    
    def test_record_serialization(self):
        """Test record serialization to dict."""
        record = CommandTimingRecord(
            record_id="rec-001",
            command="diagnostics-summary",
            timestamp="2026-04-07T12:00:00Z",
            start_ms=1000.0,
            end_ms=1050.0,
            latency_ms=50.0,
            warmup=False,
            batch_index=0,
            output_chars=1000,
            correlation_ids={"flow_id": "abc123"},
        )
        
        data = record.to_dict()
        
        self.assertEqual(data["record_id"], "rec-001")
        self.assertEqual(data["command"], "diagnostics-summary")
        self.assertEqual(data["latency_ms"], 50.0)
        self.assertEqual(data["correlation_ids"], {"flow_id": "abc123"})
    
    def test_record_json_serialization(self):
        """Test record serialization to JSON."""
        record = CommandTimingRecord(
            record_id="rec-001",
            command="diagnostics-summary",
            timestamp="2026-04-07T12:00:00Z",
            start_ms=1000.0,
            end_ms=1050.0,
            latency_ms=50.0,
            warmup=False,
            batch_index=0,
            output_chars=1000,
        )
        
        json_str = record.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["record_id"], "rec-001")
        self.assertEqual(data["latency_ms"], 50.0)
    
    def test_warmup_flag_handling(self):
        """Test warmup flag is preserved."""
        record1 = CommandTimingRecord(
            record_id="rec-001",
            command="diagnostics-summary",
            timestamp="2026-04-07T12:00:00Z",
            start_ms=1000.0,
            warmup=True,
        )
        
        record2 = CommandTimingRecord(
            record_id="rec-002",
            command="diagnostics-summary",
            timestamp="2026-04-07T12:00:00Z",
            start_ms=2000.0,
            warmup=False,
        )
        
        self.assertTrue(record1.warmup)
        self.assertFalse(record2.warmup)


class TestCommandTimingRun(unittest.TestCase):
    """Test CommandTimingRun dataclass."""
    
    def test_run_creation(self):
        """Test creating a timing run."""
        run = CommandTimingRun(
            run_id="run-001",
            command="diagnostics-summary",
            total_records=10,
            total_latency_ms=500.0,
            avg_ms=50.0,
            p50_ms=40.0,
            max_ms=100.0,
            min_ms=20.0,
            sample_count=10,
            confidence_level="medium",
        )
        
        self.assertEqual(run.run_id, "run-001")
        self.assertEqual(run.command, "diagnostics-summary")
        self.assertEqual(run.avg_ms, 50.0)
    
    def test_run_serialization(self):
        """Test run serialization to dict."""
        run = CommandTimingRun(
            run_id="run-001",
            command="diagnostics-summary",
            total_records=10,
            total_latency_ms=500.0,
            avg_ms=50.0,
            p50_ms=40.0,
            p50_available=True,
            p95_ms=80.0,
            p95_available=True,
            max_ms=100.0,
            min_ms=20.0,
            sample_count=10,
            confidence_level="medium",
        )
        
        data = run.to_dict()
        
        self.assertEqual(data["avg_ms"], 50.0)
        self.assertEqual(data["p95_ms"], 80.0)
    
    def test_run_with_unavailable_p95_p99(self):
        """Test run when p95/p99 not available."""
        run = CommandTimingRun(
            run_id="run-001",
            command="diagnostics-summary",
            total_records=5,
            total_latency_ms=250.0,
            avg_ms=50.0,
            p50_ms=40.0,
            p50_available=True,
            p95_available=False,
            p99_available=False,
            max_ms=100.0,
            min_ms=20.0,
            sample_count=5,
            confidence_level="low",
        )
        
        data = run.to_dict()
        
        # p95_ms and p99_ms should not be in data when not available
        self.assertNotIn("p95_ms", data)
        self.assertNotIn("p99_ms", data)
        
        # But the availability flags should be present
        self.assertIn("p95_available", data)
        self.assertIn("p99_available", data)
        self.assertFalse(data["p95_available"])
        self.assertFalse(data["p99_available"])
    
    def test_run_json_serialization(self):
        """Test run serialization to JSON."""
        run = CommandTimingRun(
            run_id="run-001",
            command="diagnostics-summary",
            total_records=10,
            total_latency_ms=500.0,
            avg_ms=50.0,
            p50_ms=40.0,
            max_ms=100.0,
            min_ms=20.0,
            sample_count=10,
            confidence_level="medium",
        )
        
        json_str = run.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["command"], "diagnostics-summary")
        self.assertEqual(data["total_latency_ms"], 500.0)


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
        self.assertEqual(stats["variance"], 0.0)
        self.assertEqual(stats["std_dev"], 0.0)
    
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
        self.assertGreater(stats["variance"], 0.0)
        self.assertGreater(stats["std_dev"], 0.0)
    
    def test_percentile_calculation(self):
        """Test percentile calculation."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        # Nearest-rank method
        self.assertEqual(compute_percentile(values, 50), 6)
        self.assertEqual(compute_percentile(values, 90), 10)
        self.assertEqual(compute_percentile(values, 100), 10)
    
    def test_confidence_levels(self):
        """Test confidence level assignment based on sample count."""
        # Small sample
        stats1 = compute_summary_statistics_with_confidence([1.0] * 5)
        self.assertEqual(stats1["sample_count"], 5)
        self.assertEqual(stats1["confidence"], "very_low")
        
        # Small but sufficient
        stats2 = compute_summary_statistics_with_confidence([1.0] * 10)
        self.assertEqual(stats2["confidence"], "low")
        
        # Medium
        stats3 = compute_summary_statistics_with_confidence([1.0] * 30)
        self.assertEqual(stats3["confidence"], "medium")
        
        # High
        stats4 = compute_summary_statistics_with_confidence([1.0] * 100)
        self.assertEqual(stats4["confidence"], "high")


class TestCommandTimingBaselineRunner(unittest.TestCase):
    """Test CommandTimingBaselineRunner operations."""
    
    def setUp(self):
        """Set up runner for tests."""
        self.runner = CommandTimingBaselineRunner()
    
    def test_build_command_timing_run(self):
        """Test building timing run from records."""
        records = [
            CommandTimingRecord(
                record_id=f"rec-{i}",
                command="diagnostics-summary",
                timestamp="2026-04-07T12:00:00Z",
                start_ms=1000.0 + i * 10,
                end_ms=1050.0 + i * 10,
                latency_ms=50.0,
                warmup=False,
                batch_index=i,
            )
            for i in range(10)
        ]
        
        run = self.runner.build_command_timing_run(records)
        
        self.assertEqual(run.command, "diagnostics-summary")
        self.assertEqual(run.total_records, 10)
        self.assertEqual(run.avg_ms, 50.0)
        self.assertTrue(run.p50_available)
    
    def test_build_with_warmup_exclusion(self):
        """Test that warmup records are excluded from stats."""
        warmup_records = [
            CommandTimingRecord(
                record_id="warmup-0",
                command="diagnostics-summary",
                timestamp="2026-04-07T12:00:00Z",
                start_ms=1000.0,
                end_ms=2000.0,  # 1000ms - should be excluded
                latency_ms=1000.0,
                warmup=True,
                batch_index=0,
            )
        ]
        
        timed_records = [
            CommandTimingRecord(
                record_id=f"rec-{i}",
                command="diagnostics-summary",
                timestamp="2026-04-07T12:00:00Z",
                start_ms=1000.0 + i * 10,
                end_ms=1050.0 + i * 10,
                latency_ms=50.0,
                warmup=False,
                batch_index=i,
            )
            for i in range(10)
        ]
        
        all_records = warmup_records + timed_records
        run = self.runner.build_command_timing_run(all_records)
        
        # Warmup should be excluded
        self.assertEqual(run.total_records, 10)  # Only timed records
        self.assertEqual(run.avg_ms, 50.0)  # Not 1000ms
        self.assertEqual(run.min_ms, 50.0)  # Not 1000ms
    
    def test_run_all_commands_mocked(self):
        """Test running all commands with mocked command dispatch."""
        # Mock the command dispatch to avoid actual command execution
        with unittest.mock.patch.object(self.runner, '_dispatch_command', return_value=("", 100)):
            runs = self.runner.run_all_commands(samples=5, warmup=1)
        
        self.assertEqual(len(runs), 5)  # diagnostics-summary, fallback-status, etc.
        
        for run in runs:
            self.assertIn(run.command, [
                "diagnostics-summary",
                "fallback-status",
                "diagnostics-recovery-hints",
                "diagnostics-trace-export",
                "fallback-trace-export",
            ])
    
    def test_identify_command_hotspots(self):
        """Test command hotspot identification."""
        # Create some runs with different latencies
        self.runner._commands = [
            CommandTimingRun(
                run_id="run-1",
                command="fallback-status",
                total_records=10,
                total_latency_ms=10.0,
                avg_ms=1.0,
                p50_ms=1.0,
                max_ms=2.0,
                min_ms=0.5,
                sample_count=10,
                confidence_level="medium",
            ),
            CommandTimingRun(
                run_id="run-2",
                command="diagnostics-summary",
                total_records=10,
                total_latency_ms=100.0,
                avg_ms=10.0,
                p50_ms=10.0,
                max_ms=20.0,
                min_ms=5.0,
                sample_count=10,
                confidence_level="medium",
            ),
        ]
        
        hotspots = self.runner.identify_command_hotspots()
        
        # Should be sorted by avg latency descending
        self.assertEqual(len(hotspots), 2)
        self.assertEqual(hotspots[0].avg_ms, 10.0)  # diagnostics-summary first
        self.assertEqual(hotspots[1].avg_ms, 1.0)   # fallback-status second
    
    def test_get_baseline_summary(self):
        """Test baseline summary generation."""
        self.runner._commands = [
            CommandTimingRun(
                run_id="run-1",
                command="diagnostics-summary",
                total_records=10,
                total_latency_ms=100.0,
                avg_ms=10.0,
                p50_ms=10.0,
                max_ms=20.0,
                min_ms=5.0,
                sample_count=10,
                confidence_level="medium",
            ),
        ]
        
        summary = self.runner.get_baseline_summary()
        
        self.assertIn("summary_id", summary.to_dict())
        self.assertEqual(summary.total_commands, 1)
        self.assertIn("COMMAND TIMING BASELINE SUMMARY", summary.operator_readable)
        self.assertIn("diagnostics-summary", summary.operator_readable)
    
    def test_export_baseline_json(self):
        """Test JSON export."""
        self.runner._commands = [
            CommandTimingRun(
                run_id="run-1",
                command="diagnostics-summary",
                total_records=10,
                total_latency_ms=100.0,
                avg_ms=10.0,
                p50_ms=10.0,
                max_ms=20.0,
                min_ms=5.0,
                sample_count=10,
                confidence_level="medium",
            ),
        ]
        
        json_str = self.runner.export_baseline_json()
        data = json.loads(json_str)
        
        self.assertIn("total_commands", data)
        self.assertEqual(data["total_commands"], 1)
    
    def test_export_operator_readable(self):
        """Test operator-readable export."""
        self.runner._commands = [
            CommandTimingRun(
                run_id="run-1",
                command="diagnostics-summary",
                total_records=10,
                total_latency_ms=100.0,
                avg_ms=10.0,
                p50_ms=10.0,
                max_ms=20.0,
                min_ms=5.0,
                sample_count=10,
                confidence_level="medium",
            ),
        ]
        
        output = self.runner.export_operator_readable()
        
        self.assertIn("COMMAND TIMING BASELINE SUMMARY", output)
        self.assertIn("diagnostics-summary", output)
        self.assertIn("MEASURED HOTSPOTS", output)


class TestEndToEndCommandTiming(unittest.TestCase):
    """Test end-to-end command timing workflow."""
    
    def test_full_command_timing_workflow(self):
        """Test complete command timing workflow end-to-end."""
        runner = CommandTimingBaselineRunner()
        
        # Run all commands with sufficient samples
        runs = runner.run_all_commands(samples=10, warmup=1)
        
        # Verify we have records
        self.assertGreater(len(runs), 0)
        
        # Check each run has required fields
        for run in runs:
            self.assertGreater(run.total_records, 0)
            self.assertGreater(run.avg_ms, 0.0)
            self.assertTrue(run.p50_available)
        
        # Identify hotspots
        hotspots = runner.identify_command_hotspots()
        
        # Verify hotspots sorted by latency
        for i in range(len(hotspots) - 1):
            self.assertGreaterEqual(hotspots[i].avg_ms, hotspots[i + 1].avg_ms)
        
        # Get summary
        summary = runner.get_baseline_summary()
        json_output = runner.export_baseline_json()
        operator_output = runner.export_operator_readable()
        
        # Verify JSON is parseable
        parsed = json.loads(json_output)
        self.assertIn("total_commands", parsed)
        
        # Verify operator-readable contains expected sections
        self.assertIn("COMMAND TIMING BASELINE SUMMARY", operator_output)
        self.assertIn("COMMAND BREAKDOWN", operator_output)
        self.assertIn("MEASURED HOTSPOTS", operator_output)


if __name__ == "__main__":
    unittest.main()
