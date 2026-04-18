#!/usr/bin/env python3
# test_recovery_pattern_history.py - WESLR v84: Recovery Pattern History / Trend Tests
# Tests pattern history layer for recovery incidents over time.

from __future__ import annotations

import json
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from weslr.recovery_pattern_history import (
    PatternHistoryRecord,
    TrendSummary,
    RecoveryPatternHistory,
)


class TestPatternHistoryRecord(unittest.TestCase):
    """Test PatternHistoryRecord dataclass."""
    
    def test_record_creation(self):
        """Test creating a pattern history record."""
        record = PatternHistoryRecord(
            history_id="history-001",
            timestamp="2026-04-07T12:00:00Z",
            pattern_type="recommendation",
            pattern_id="rec-001",
            correlation_ids={"flow_id": "flow-123"},
            content={"stage": "proposal"},
            sequence=1,
            window_start="2026-04-07T12:00:00Z",
            window_end="2026-04-07T13:00:00Z",
        )
        
        self.assertEqual(record.history_id, "history-001")
        self.assertEqual(record.pattern_type, "recommendation")
        self.assertEqual(record.sequence, 1)
    
    def test_record_serialization(self):
        """Test pattern history record to dict."""
        record = PatternHistoryRecord(
            history_id="history-001",
            timestamp="2026-04-07T12:00:00Z",
            pattern_type="decision_trace",
            pattern_id="trace-001",
            correlation_ids={"flow_id": "flow-123", "request_id": "req-456"},
            content={"rationale": "test rationale"},
            sequence=2,
            window_start="2026-04-07T12:00:00Z",
            window_end="2026-04-07T13:00:00Z",
        )
        
        data = record.to_dict()
        
        self.assertEqual(data["history_id"], "history-001")
        self.assertEqual(data["pattern_type"], "decision_trace")
        self.assertIn("flow_id", data["correlation_ids"])
        self.assertEqual(data["sequence"], 2)
    
    def test_record_json_serialization(self):
        """Test pattern history record to JSON."""
        record = PatternHistoryRecord(
            history_id="history-001",
            timestamp="2026-04-07T12:00:00Z",
            pattern_type="recommendation",
            pattern_id="rec-001",
            correlation_ids={"flow_id": "flow-123"},
            content={"stage": "proposal"},
            sequence=1,
            window_start="2026-04-07T12:00:00Z",
            window_end="2026-04-07T13:00:00Z",
        )
        
        json_str = record.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["pattern_type"], "recommendation")
        self.assertIn("flow_id", data["correlation_ids"])


class TestTrendSummary(unittest.TestCase):
    """Test TrendSummary dataclass."""
    
    def test_summary_creation(self):
        """Test creating a trend summary."""
        summary = TrendSummary(
            summary_id="trend-001",
            timestamp="2026-04-07T12:00:00Z",
            total_patterns=5,
            pattern_type_distribution={"recommendation": 3, "decision_trace": 2},
            repeated_patterns={"pattern_type_recommendation": 3},
            confidence_trend={"high": 3, "medium": 2},
            safe_action_patterns={"review": 4, "escalate": 1},
            operator_readable="Summary text",
            machine_readable='{"test": true}',
        )
        
        self.assertEqual(summary.summary_id, "trend-001")
        self.assertEqual(summary.total_patterns, 5)
    
    def test_summary_serialization(self):
        """Test trend summary to dict."""
        summary = TrendSummary(
            summary_id="trend-001",
            timestamp="2026-04-07T12:00:00Z",
            total_patterns=5,
            pattern_type_distribution={"recommendation": 3},
            repeated_patterns={"pattern_type_recommendation": 3},
            confidence_trend={"high": 3},
            safe_action_patterns={"review": 4},
            operator_readable="Summary",
            machine_readable='{"patterns": 5}',
        )
        
        data = summary.to_dict()
        
        self.assertEqual(data["total_patterns"], 5)
        self.assertIn("recommendation", data["pattern_type_distribution"])
    
    def test_summary_json_serialization(self):
        """Test trend summary to JSON."""
        summary = TrendSummary(
            summary_id="trend-001",
            timestamp="2026-04-07T12:00:00Z",
            total_patterns=3,
            pattern_type_distribution={"decision_trace": 3},
            repeated_patterns={},
            confidence_trend={"medium": 3},
            safe_action_patterns={"review": 3},
            operator_readable="Summary",
            machine_readable='{"patterns": 3}',
        )
        
        json_str = summary.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["total_patterns"], 3)
        self.assertEqual(data["pattern_type_distribution"]["decision_trace"], 3)


class TestRecoveryPatternHistory(unittest.TestCase):
    """Test RecoveryPatternHistory layer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.history = RecoveryPatternHistory()
    
    def test_add_recommendation_pattern(self):
        """Test adding a recommendation pattern to history."""
        recommendation = {
            "recommendation_id": "rec-001",
            "stage": "proposal",
            "confidence": "high",
        }
        correlation_ids = {"flow_id": "flow-123", "request_id": "req-456"}
        
        record = self.history.add_recommendation_pattern(
            recommendation,
            correlation_ids,
        )
        
        self.assertEqual(record.pattern_type, "recommendation")
        self.assertEqual(record.pattern_id, "rec-001")
        self.assertEqual(record.correlation_ids["flow_id"], "flow-123")
        self.assertEqual(self.history._sequence_counter, 1)
    
    def test_add_decision_trace_pattern(self):
        """Test adding a decision trace pattern to history."""
        decision_trace = {
            "trace_id": "trace-001",
            "confidence_level": "medium",
            "safe_next_action": {"type": "review"},
        }
        correlation_ids = {"handshake_id": "hs-789"}
        
        record = self.history.add_decision_trace_pattern(
            decision_trace,
            correlation_ids,
        )
        
        self.assertEqual(record.pattern_type, "decision_trace")
        self.assertEqual(record.pattern_id, "trace-001")
        self.assertEqual(record.correlation_ids["handshake_id"], "hs-789")
        self.assertEqual(self.history._sequence_counter, 1)
    
    def test_get_pattern_history_with_filter(self):
        """Test getting pattern history with filters."""
        # Add different pattern types
        self.history.add_recommendation_pattern(
            {"recommendation_id": "rec-001"},
            {"flow_id": "flow-1"},
        )
        self.history.add_decision_trace_pattern(
            {"trace_id": "trace-001"},
            {"flow_id": "flow-1"},
        )
        self.history.add_recommendation_pattern(
            {"recommendation_id": "rec-002"},
            {"flow_id": "flow-2"},
        )
        
        # Filter by pattern type
        recommendations = self.history.get_pattern_history(pattern_type="recommendation")
        self.assertEqual(len(recommendations), 2)
        
        traces = self.history.get_pattern_history(pattern_type="decision_trace")
        self.assertEqual(len(traces), 1)
    
    def test_get_pattern_history_with_correlation_filter(self):
        """Test getting pattern history with correlation filters."""
        self.history.add_recommendation_pattern(
            {"recommendation_id": "rec-001"},
            {"flow_id": "flow-123", "request_id": "req-456"},
        )
        self.history.add_decision_trace_pattern(
            {"trace_id": "trace-001"},
            {"flow_id": "flow-123", "request_id": "req-789"},
        )
        
        # Filter by flow_id
        flow1_patterns = self.history.get_pattern_history(
            correlation_type="flow_id",
            correlation_id="flow-123",
        )
        self.assertEqual(len(flow1_patterns), 2)
        
        # Filter by different flow_id
        flow2_patterns = self.history.get_pattern_history(
            correlation_type="flow_id",
            correlation_id="flow-999",
        )
        self.assertEqual(len(flow2_patterns), 0)
    
    def test_find_repeated_patterns(self):
        """Test finding repeated patterns in history."""
        self.history.add_recommendation_pattern(
            {"recommendation_id": "rec-001"},
            {"flow_id": "flow-123"},
        )
        self.history.add_recommendation_pattern(
            {"recommendation_id": "rec-002"},
            {"flow_id": "flow-123"},
        )
        self.history.add_decision_trace_pattern(
            {"trace_id": "trace-001"},
            {"flow_id": "flow-456"},
        )
        
        repeated = self.history.find_repeated_patterns()
        
        # Should track pattern types
        self.assertIn("pattern_type_recommendation", repeated)
        self.assertIn("pattern_type_decision_trace", repeated)
        
        # Should track correlation patterns
        self.assertIn("correlation_flow_id=flow-123", repeated)
        self.assertIn("correlation_flow_id=flow-456", repeated)
    
    def test_get_trend_summary_empty(self):
        """Test getting trend summary with no history."""
        summary = self.history.get_trend_summary()
        
        self.assertEqual(summary.total_patterns, 0)
        self.assertIn("No pattern history", summary.operator_readable)
    
    def test_get_trend_summary(self):
        """Test getting trend summary with patterns."""
        # Add some patterns
        self.history.add_recommendation_pattern(
            {"recommendation_id": "rec-001", "confidence": "high"},
        )
        self.history.add_decision_trace_pattern(
            {
                "trace_id": "trace-001",
                "confidence_level": "high",
                "safe_next_action": {"type": "review"},
            },
            {"flow_id": "flow-123"},
        )
        self.history.add_decision_trace_pattern(
            {
                "trace_id": "trace-002",
                "confidence_level": "medium",
                "safe_next_action": {"type": "escalate"},
            },
            {"flow_id": "flow-456"},
        )
        self.history.add_recommendation_pattern(
            {"recommendation_id": "rec-002", "confidence": "medium"},
        )
        
        summary = self.history.get_trend_summary()
        
        self.assertEqual(summary.total_patterns, 4)
        self.assertEqual(summary.pattern_type_distribution["recommendation"], 2)
        self.assertEqual(summary.pattern_type_distribution["decision_trace"], 2)
        self.assertIn("high", summary.confidence_trend)
        self.assertIn("medium", summary.confidence_trend)
        self.assertIn("review", summary.safe_action_patterns)
        self.assertIn("escalate", summary.safe_action_patterns)
        
        # Verify machine-readable export
        machine_data = json.loads(summary.machine_readable)
        self.assertEqual(machine_data["total_patterns"], 4)
    
    def test_export_operator_readable(self):
        """Test exporting operator-readable summary."""
        self.history.add_recommendation_pattern(
            {"recommendation_id": "rec-001"},
        )
        self.history.add_decision_trace_pattern(
            {"trace_id": "trace-001"},
        )
        
        export = self.history.export_operator_readable()
        
        self.assertIn("RECOVERY PATTERN HISTORY TREND SUMMARY", export)
        self.assertIn("PATTERN TYPE DISTRIBUTION", export)
        self.assertIn("REPEATED PATTERNS", export)
        self.assertIn("CONFIDENCE GUIDANCE TRENDS", export)
        self.assertIn("SAFE-NEXT-ACTION PATTERNS", export)
    
    def test_export_machine_readable(self):
        """Test exporting machine-readable summary."""
        self.history.add_recommendation_pattern(
            {"recommendation_id": "rec-001"},
        )
        
        export = self.history.export_machine_readable()
        data = json.loads(export)
        
        self.assertEqual(data["total_patterns"], 1)
        self.assertIn("pattern_type_distribution", data)
        self.assertIn("repeated_patterns", data)
    
    def test_export_patterns_as_json(self):
        """Test exporting all patterns as JSON."""
        self.history.add_recommendation_pattern(
            {"recommendation_id": "rec-001"},
        )
        self.history.add_decision_trace_pattern(
            {"trace_id": "trace-001"},
        )
        
        export = self.history.export_patterns_as_json()
        patterns = json.loads(export)
        
        self.assertEqual(len(patterns), 2)
        self.assertEqual(patterns[0]["pattern_type"], "recommendation")
        self.assertEqual(patterns[1]["pattern_type"], "decision_trace")
    
    def test_export_trend_data_as_json(self):
        """Test exporting trend data as JSON."""
        self.history.add_decision_trace_pattern(
            {
                "trace_id": "trace-001",
                "confidence_level": "high",
                "safe_next_action": {"type": "review"},
            },
        )
        
        export = self.history.export_trend_data_as_json()
        data = json.loads(export)
        
        self.assertEqual(data["total_patterns"], 1)
        self.assertIn("confidence_trend", data)
        self.assertIn("safe_action_patterns", data)
        self.assertIn("high", data["confidence_trend"])
        self.assertIn("review", data["safe_action_patterns"])


class TestIntegration(unittest.TestCase):
    """Test integration with other layers."""
    
    def test_integrate_with_v83_comparison(self):
        """Test integration hook with v83 comparison layer."""
        from weslr.recovery_pattern_history import integrate_with_v83_comparison
        
        history = RecoveryPatternHistory()
        result = integrate_with_v83_comparison(history)
        
        self.assertEqual(result["hooked"], True)
        self.assertEqual(result["measures"], "pattern_history_integration")
    
    def test_correlate_with_v78_decision_traces(self):
        """Test correlation hook with v78 decision traces."""
        from weslr.recovery_pattern_history import correlate_with_v78_decision_traces
        
        history = RecoveryPatternHistory()
        result = correlate_with_v78_decision_traces(history)
        
        self.assertEqual(result["hooked"], True)
        self.assertEqual(result["measures"], "decision_trace_correlation")


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with v76-v83 layers."""
    
    def test_no_breaking_changes(self):
        """Test that v84 does not break existing layers."""
        # This layer should not modify v75-v83 behavior
        history = RecoveryPatternHistory()
        
        # Add pattern - should work independently
        record = history.add_recommendation_pattern(
            {"recommendation_id": "rec-001"},
        )
        self.assertIsNotNone(record.history_id)
        
        # Export - should work independently
        export = history.export_operator_readable()
        self.assertIn("RECOVERY PATTERN HISTORY", export)
    
    def test_correlation_ids_compatibility(self):
        """Test correlation ID compatibility with v78."""
        history = RecoveryPatternHistory()
        
        # v78 uses flow_id, request_id, handshake_id, deadline_id
        correlation_ids = {
            "flow_id": "flow-123",
            "request_id": "req-456",
            "handshake_id": "hs-789",
            "deadline_id": "dl-012",
        }
        
        record = history.add_recommendation_pattern(
            {"recommendation_id": "rec-001"},
            correlation_ids,
        )
        
        for cid in correlation_ids:
            self.assertIn(cid, record.correlation_ids)


if __name__ == "__main__":
    unittest.main()
