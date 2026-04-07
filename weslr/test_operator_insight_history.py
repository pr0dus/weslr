#!/usr/bin/env python3
# test_operator_insight_history.py - WESLR v86: Operator Insight History / Comparative Significance Tests
# Tests insight history layer for comparative significance analysis.

from __future__ import annotations

import json
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from weslr.operator_insight_history import (
    InsightHistoryRecord,
    ComparativeSignificance,
    SignificanceTrend,
    ComparativeSummary,
    InsightHistoryStore,
    OperatorInsightHistory,
)
from weslr.operator_recovery_insight import InsightSummary, OperatorRecoveryInsight


class TestInsightHistoryRecord(unittest.TestCase):
    """Test InsightHistoryRecord dataclass."""
    
    def test_record_creation(self):
        """Test creating an insight history record."""
        record = InsightHistoryRecord(
            history_id="history-001",
            timestamp="2026-04-07T12:00:00Z",
            insight_summary_id="summary-001",
            correlation_ids={"flow_id": "flow-123"},
            insight_count=5,
            insight_types={"convergence": 3, "divergence": 2},
            shift_count=2,
            shift_types={"confidence": 2},
            convergence_patterns={"action_a": 3},
            divergence_patterns={"action_b": 2},
            sequence=1,
            window_start="2026-04-07T12:00:00Z",
            window_end="2026-04-07T13:00:00Z",
        )
        
        self.assertEqual(record.history_id, "history-001")
        self.assertEqual(record.insight_count, 5)
    
    def test_record_serialization(self):
        """Test insight history record to dict."""
        record = InsightHistoryRecord(
            history_id="history-001",
            timestamp="2026-04-07T12:00:00Z",
            insight_summary_id="summary-001",
            correlation_ids={"flow_id": "flow-123"},
            insight_count=3,
            insight_types={"convergence": 3},
            shift_count=1,
            shift_types={"confidence": 1},
            convergence_patterns={},
            divergence_patterns={},
            sequence=2,
            window_start="2026-04-07T12:00:00Z",
            window_end="2026-04-07T13:00:00Z",
        )
        
        data = record.to_dict()
        
        self.assertEqual(data["insight_count"], 3)
        self.assertIn("flow_id", data["correlation_ids"])
    
    def test_record_json_serialization(self):
        """Test insight history record to JSON."""
        record = InsightHistoryRecord(
            history_id="history-001",
            timestamp="2026-04-07T12:00:00Z",
            insight_summary_id="summary-001",
            correlation_ids={"flow_id": "flow-123"},
            insight_count=2,
            insight_types={"divergence": 2},
            shift_count=0,
            shift_types={},
            convergence_patterns={},
            divergence_patterns={},
            sequence=1,
            window_start="2026-04-07T12:00:00Z",
            window_end="2026-04-07T13:00:00Z",
        )
        
        json_str = record.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["insight_count"], 2)


class TestComparativeSignificance(unittest.TestCase):
    """Test ComparativeSignificance dataclass."""
    
    def test_comparison_creation(self):
        """Test creating a comparative significance."""
        comparison = ComparativeSignificance(
            comparison_id="comp-001",
            timestamp="2026-04-07T12:00:00Z",
            comparison_type="insight_summary",
            summary1_id="summary-001",
            summary2_id="summary-002",
            shared_fields={"total_insights": 5},
            differences={"insight_count": (3, 5)},
            significance_shift="increasing",
            meaningful_shift=True,
            meaningful_shift_reason="Significant increase detected.",
        )
        
        self.assertEqual(comparison.comparison_id, "comp-001")
        self.assertEqual(comparison.comparison_type, "insight_summary")
    
    def test_comparison_serialization(self):
        """Test comparative significance to dict."""
        comparison = ComparativeSignificance(
            comparison_id="comp-001",
            timestamp="2026-04-07T12:00:00Z",
            comparison_type="significance",
            summary1_id="summary-001",
            summary2_id="summary-002",
            significance_shift="stable",
            meaningful_shift=False,
            meaningful_shift_reason="No significant change.",
        )
        
        data = comparison.to_dict()
        
        self.assertEqual(data["significance_shift"], "stable")
        self.assertFalse(data["meaningful_shift"])
    
    def test_comparison_json_serialization(self):
        """Test comparative significance to JSON."""
        comparison = ComparativeSignificance(
            comparison_id="comp-001",
            timestamp="2026-04-07T12:00:00Z",
            comparison_type="confidence",
            summary1_id="summary-001",
            summary2_id="summary-002",
            significance_shift="decreasing",
            meaningful_shift=True,
            meaningful_shift_reason="Decrease detected.",
        )
        
        json_str = comparison.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["significance_shift"], "decreasing")
        self.assertTrue(data["meaningful_shift"])


class TestSignificanceTrend(unittest.TestCase):
    """Test SignificanceTrend dataclass."""
    
    def test_trend_creation(self):
        """Test creating a significance trend."""
        trend = SignificanceTrend(
            trend_id="trend-001",
            timestamp="2026-04-07T12:00:00Z",
            trend_type="insight_count",
            direction="increasing",
            magnitude="moderate",
            interpretation="More insights being detected.",
            heuristic_significance="medium",
            heuristic_reason="Standard heuristic significance.",
            reference_summary_id="ref-001",
        )
        
        self.assertEqual(trend.trend_id, "trend-001")
        self.assertEqual(trend.direction, "increasing")
    
    def test_trend_serialization(self):
        """Test significance trend to dict."""
        trend = SignificanceTrend(
            trend_id="trend-001",
            timestamp="2026-04-07T12:00:00Z",
            trend_type="safe_action_convergence",
            direction="stable",
            magnitude="minor",
            interpretation="Convergence stable.",
            heuristic_significance="low",
            heuristic_reason="Standard heuristic significance.",
            reference_summary_id="ref-001",
        )
        
        data = trend.to_dict()
        
        self.assertEqual(data["direction"], "stable")
        self.assertEqual(data["magnitude"], "minor")
    
    def test_trend_json_serialization(self):
        """Test significance trend to JSON."""
        trend = SignificanceTrend(
            trend_id="trend-001",
            timestamp="2026-04-07T12:00:00Z",
            trend_type="confidence",
            direction="variable",
            magnitude="significant",
            interpretation="Variable confidence.",
            heuristic_significance="high",
            heuristic_reason="Significant variance detected.",
            reference_summary_id="ref-001",
        )
        
        json_str = trend.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["direction"], "variable")
        self.assertEqual(data["magnitude"], "significant")


class TestComparativeSummary(unittest.TestCase):
    """Test ComparativeSummary dataclass."""
    
    def test_summary_creation(self):
        """Test creating a comparative summary."""
        summary = ComparativeSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_comparisons=5,
            comparison_type_distribution={"insight_summary": 3, "significance": 2},
            meaningful_shifts=[{"comparison": "test"}],
            significance_trends=[{"trend": "test"}],
            operator_readable="Summary text",
            machine_readable='{"test": true}',
        )
        
        self.assertEqual(summary.summary_id, "summary-001")
        self.assertEqual(summary.total_comparisons, 5)
    
    def test_summary_serialization(self):
        """Test comparative summary to dict."""
        summary = ComparativeSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_comparisons=3,
            comparison_type_distribution={"insight_summary": 3},
            meaningful_shifts=[],
            significance_trends=[],
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        data = summary.to_dict()
        
        self.assertEqual(data["total_comparisons"], 3)
    
    def test_summary_json_serialization(self):
        """Test comparative summary to JSON."""
        summary = ComparativeSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_comparisons=2,
            comparison_type_distribution={"confidence": 2},
            meaningful_shifts=[],
            significance_trends=[],
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        json_str = summary.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["total_comparisons"], 2)


class TestInsightHistoryStore(unittest.TestCase):
    """Test InsightHistoryStore class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.store = InsightHistoryStore()
    
    def test_add_insight_summary(self):
        """Test adding an insight summary to history."""
        summary = InsightSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_insights=5,
            insight_type_distribution={"convergence": 3, "divergence": 2},
            trend_shifts=[],
            convergence_patterns={"action_a": 3},
            divergence_patterns={"action_b": 2},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        record = self.store.add_insight_summary(
            summary,
            {"flow_id": "flow-123"},
        )
        
        self.assertEqual(record.insight_count, 5)
        self.assertEqual(record.sequence, 1)
        self.assertEqual(record.correlation_ids["flow_id"], "flow-123")
    
    def test_add_insight_summary_no_correlation(self):
        """Test adding summary without correlation IDs."""
        summary = InsightSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_insights=3,
            insight_type_distribution={"convergence": 3},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        record = self.store.add_insight_summary(summary)
        
        self.assertEqual(record.insight_count, 3)
        self.assertEqual(record.correlation_ids, {})
    
    def test_get_latest_history(self):
        """Test getting latest history records."""
        summary1 = InsightSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_insights=3,
            insight_type_distribution={"convergence": 3},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        summary2 = InsightSummary(
            summary_id="summary-002",
            timestamp="2026-04-07T13:00:00Z",
            total_insights=5,
            insight_type_distribution={"convergence": 3, "divergence": 2},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        summary3 = InsightSummary(
            summary_id="summary-003",
            timestamp="2026-04-07T14:00:00Z",
            total_insights=7,
            insight_type_distribution={"convergence": 5, "divergence": 2},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        self.store.add_insight_summary(summary1)
        self.store.add_insight_summary(summary2)
        self.store.add_insight_summary(summary3)
        
        latest = self.store.get_latest_history(2)
        
        self.assertEqual(len(latest), 2)
        self.assertEqual(latest[0].insight_summary_id, "summary-002")
        self.assertEqual(latest[1].insight_summary_id, "summary-003")
    
    def test_get_history_by_insight_summary_id(self):
        """Test getting history by summary ID."""
        summary = InsightSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_insights=3,
            insight_type_distribution={"convergence": 3},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        record = self.store.add_insight_summary(summary)
        
        found = self.store.get_history_by_insight_summary_id("summary-001")
        
        self.assertEqual(found, record)
        self.assertIsNone(self.store.get_history_by_insight_summary_id("nonexistent"))
    
    def test_get_history_with_correlation_filter(self):
        """Test getting history with correlation filters."""
        summary1 = InsightSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_insights=3,
            insight_type_distribution={"convergence": 3},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        summary2 = InsightSummary(
            summary_id="summary-002",
            timestamp="2026-04-07T13:00:00Z",
            total_insights=5,
            insight_type_distribution={"convergence": 5},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        self.store.add_insight_summary(summary1, {"flow_id": "flow-123"})
        self.store.add_insight_summary(summary2, {"flow_id": "flow-456"})
        
        flow1_records = self.store.get_history(correlation_type="flow_id", correlation_id="flow-123")
        flow2_records = self.store.get_history(correlation_type="flow_id", correlation_id="flow-456")
        no_filter_records = self.store.get_history()
        
        self.assertEqual(len(flow1_records), 1)
        self.assertEqual(len(flow2_records), 1)
        self.assertEqual(len(no_filter_records), 2)


class TestOperatorInsightHistory(unittest.TestCase):
    """Test OperatorInsightHistory class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.history = OperatorInsightHistory()
    
    def test_compare_significance(self):
        """Test comparing significance between summaries."""
        summary1 = InsightSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_insights=3,
            insight_type_distribution={"convergence": 3},
            trend_shifts=[],
            convergence_patterns={"action_a": 3},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        summary2 = InsightSummary(
            summary_id="summary-002",
            timestamp="2026-04-07T13:00:00Z",
            total_insights=5,
            insight_type_distribution={"convergence": 3, "divergence": 2},
            trend_shifts=[],
            convergence_patterns={"action_a": 3, "action_b": 2},
            divergence_patterns={"action_c": 1},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        comparison = self.history.compare_significance(summary1, summary2)
        
        self.assertEqual(comparison.significance_shift, "increasing")
        self.assertTrue(comparison.meaningful_shift)
        self.assertIn("increase", comparison.meaningful_shift_reason.lower())
    
    def test_compare_significance_stable(self):
        """Test comparing stable significance."""
        summary1 = InsightSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_insights=3,
            insight_type_distribution={"convergence": 3},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        summary2 = InsightSummary(
            summary_id="summary-002",
            timestamp="2026-04-07T13:00:00Z",
            total_insights=3,
            insight_type_distribution={"convergence": 3},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        comparison = self.history.compare_significance(summary1, summary2)
        
        self.assertEqual(comparison.significance_shift, "stable")
        self.assertFalse(comparison.meaningful_shift)
    
    def test_analyze_significance_trends_empty(self):
        """Test analyzing trends with no history."""
        trends = self.history.analyze_significance_trends([])
        
        self.assertEqual(len(trends), 0)
    
    def test_analyze_significance_trends(self):
        """Test analyzing trends with history."""
        history = [
            InsightHistoryRecord(
                history_id="history-001",
                timestamp="2026-04-07T12:00:00Z",
                insight_summary_id="summary-001",
                correlation_ids={},
                insight_count=2,
                insight_types={"convergence": 2},
                shift_count=0,
                shift_types={},
                convergence_patterns={"action_a": 2},
                divergence_patterns={},
                sequence=1,
                window_start="2026-04-07T12:00:00Z",
                window_end="2026-04-07T13:00:00Z",
            ),
            InsightHistoryRecord(
                history_id="history-002",
                timestamp="2026-04-07T13:00:00Z",
                insight_summary_id="summary-002",
                correlation_ids={},
                insight_count=4,
                insight_types={"convergence": 2, "divergence": 2},
                shift_count=0,
                shift_types={},
                convergence_patterns={"action_a": 3},
                divergence_patterns={"action_b": 1},
                sequence=2,
                window_start="2026-04-07T13:00:00Z",
                window_end="2026-04-07T14:00:00Z",
            ),
            InsightHistoryRecord(
                history_id="history-003",
                timestamp="2026-04-07T14:00:00Z",
                insight_summary_id="summary-003",
                correlation_ids={},
                insight_count=6,
                insight_types={"convergence": 4, "divergence": 2},
                shift_count=0,
                shift_types={},
                convergence_patterns={"action_a": 4},
                divergence_patterns={"action_b": 2},
                sequence=3,
                window_start="2026-04-07T14:00:00Z",
                window_end="2026-04-07T15:00:00Z",
            ),
        ]
        
        trends = self.history.analyze_significance_trends(history)
        
        # Should detect insight_count trend
        self.assertGreater(len(trends), 0)
        self.assertEqual(trends[0].trend_type, "insight_count")
    
    def test_detect_significant_shifts(self):
        """Test detecting significant shifts."""
        history = [
            InsightHistoryRecord(
                history_id="history-001",
                timestamp="2026-04-07T12:00:00Z",
                insight_summary_id="summary-001",
                correlation_ids={},
                insight_count=2,
                insight_types={"convergence": 2},
                shift_count=0,
                shift_types={},
                convergence_patterns={},
                divergence_patterns={},
                sequence=1,
                window_start="2026-04-07T12:00:00Z",
                window_end="2026-04-07T13:00:00Z",
            ),
            InsightHistoryRecord(
                history_id="history-002",
                timestamp="2026-04-07T13:00:00Z",
                insight_summary_id="summary-002",
                correlation_ids={},
                insight_count=5,
                insight_types={"convergence": 3, "divergence": 2},
                shift_count=0,
                shift_types={},
                convergence_patterns={},
                divergence_patterns={},
                sequence=2,
                window_start="2026-04-07T13:00:00Z",
                window_end="2026-04-07T14:00:00Z",
            ),
        ]
        
        shifts = self.history.detect_significant_shifts(history)
        
        # Should detect significant shift (2 -> 5)
        self.assertGreater(len(shifts), 0)
        self.assertTrue(shifts[0].meaningful_shift)
    
    def test_get_comparative_summary_empty(self):
        """Test getting comparative summary with no data."""
        empty_history = OperatorInsightHistory()
        summary = empty_history.get_comparative_summary()
        
        self.assertEqual(summary.total_comparisons, 0)
        self.assertIn("No comparative", summary.operator_readable)
    
    def test_get_comparative_summary(self):
        """Test getting comparative summary with data."""
        summary1 = InsightSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_insights=3,
            insight_type_distribution={"convergence": 3},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        summary2 = InsightSummary(
            summary_id="summary-002",
            timestamp="2026-04-07T13:00:00Z",
            total_insights=5,
            insight_type_distribution={"convergence": 3, "divergence": 2},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        self.history.compare_significance(summary1, summary2)
        result = self.history.get_comparative_summary()
        
        self.assertEqual(result.total_comparisons, 1)
        self.assertIn("COMPARATIVE SIGNIFICANCE SUMMARY", result.operator_readable)
    
    def test_export_operator_readable(self):
        """Test exporting operator-readable summary."""
        summary1 = InsightSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_insights=3,
            insight_type_distribution={"convergence": 3},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        summary2 = InsightSummary(
            summary_id="summary-002",
            timestamp="2026-04-07T13:00:00Z",
            total_insights=5,
            insight_type_distribution={"convergence": 3, "divergence": 2},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        self.history.compare_significance(summary1, summary2)
        export = self.history.export_operator_readable()
        
        self.assertIn("OPERATOR INSIGHT HISTORY COMPARATIVE SIGNIFICANCE SUMMARY", export)
        self.assertIn("COMPARISON TYPE DISTRIBUTION", export)
        self.assertIn("HEURISTIC NOTE", export)
    
    def test_export_machine_readable(self):
        """Test exporting machine-readable summary."""
        summary1 = InsightSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_insights=3,
            insight_type_distribution={"convergence": 3},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        summary2 = InsightSummary(
            summary_id="summary-002",
            timestamp="2026-04-07T13:00:00Z",
            total_insights=5,
            insight_type_distribution={"convergence": 3, "divergence": 2},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        self.history.compare_significance(summary1, summary2)
        export = self.history.export_machine_readable()
        data = json.loads(export)
        
        self.assertEqual(data["total_comparisons"], 1)
        self.assertIn("comparison_type_distribution", data)
        self.assertIn("meaningful_shifts", data)
    
    def test_export_comparisons_as_json(self):
        """Test exporting all comparisons as JSON."""
        summary1 = InsightSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_insights=3,
            insight_type_distribution={"convergence": 3},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        summary2 = InsightSummary(
            summary_id="summary-002",
            timestamp="2026-04-07T13:00:00Z",
            total_insights=5,
            insight_type_distribution={"convergence": 3, "divergence": 2},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        self.history.compare_significance(summary1, summary2)
        self.history.compare_significance(summary2, summary1)
        
        export = self.history.export_comparisons_as_json()
        comparisons = json.loads(export)
        
        self.assertEqual(len(comparisons), 2)
    
    def test_export_significance_trends_as_json(self):
        """Test exporting significance trends as JSON."""
        history = [
            InsightHistoryRecord(
                history_id="history-001",
                timestamp="2026-04-07T12:00:00Z",
                insight_summary_id="summary-001",
                correlation_ids={},
                insight_count=2,
                insight_types={"convergence": 2},
                shift_count=0,
                shift_types={},
                convergence_patterns={"action_a": 2},
                divergence_patterns={},
                sequence=1,
                window_start="2026-04-07T12:00:00Z",
                window_end="2026-04-07T13:00:00Z",
            ),
            InsightHistoryRecord(
                history_id="history-002",
                timestamp="2026-04-07T13:00:00Z",
                insight_summary_id="summary-002",
                correlation_ids={},
                insight_count=4,
                insight_types={"convergence": 3, "divergence": 1},
                shift_count=0,
                shift_types={},
                convergence_patterns={"action_a": 3},
                divergence_patterns={"action_b": 1},
                sequence=2,
                window_start="2026-04-07T13:00:00Z",
                window_end="2026-04-07T14:00:00Z",
            ),
        ]
        
        self.history.analyze_significance_trends(history)
        export = self.history.export_significance_trends_as_json()
        trends = json.loads(export)
        
        self.assertGreater(len(trends), 0)
    
    def test_export_meaningful_shifts_as_json(self):
        """Test exporting meaningful shifts as JSON."""
        history = [
            InsightHistoryRecord(
                history_id="history-001",
                timestamp="2026-04-07T12:00:00Z",
                insight_summary_id="summary-001",
                correlation_ids={},
                insight_count=2,
                insight_types={"convergence": 2},
                shift_count=0,
                shift_types={},
                convergence_patterns={},
                divergence_patterns={},
                sequence=1,
                window_start="2026-04-07T12:00:00Z",
                window_end="2026-04-07T13:00:00Z",
            ),
            InsightHistoryRecord(
                history_id="history-002",
                timestamp="2026-04-07T13:00:00Z",
                insight_summary_id="summary-002",
                correlation_ids={},
                insight_count=5,
                insight_types={"convergence": 3, "divergence": 2},
                shift_count=0,
                shift_types={},
                convergence_patterns={},
                divergence_patterns={},
                sequence=2,
                window_start="2026-04-07T13:00:00Z",
                window_end="2026-04-07T14:00:00Z",
            ),
        ]
        
        shifts = self.history.detect_significant_shifts(history)
        export = self.history.export_meaningful_shifts_as_json()
        meaningful = json.loads(export)
        
        self.assertGreater(len(meaningful), 0)


class TestIntegration(unittest.TestCase):
    """Test integration with other layers."""
    
    def test_integrate_with_v85_insights(self):
        """Test integration hook with v85 insights."""
        from weslr.operator_insight_history import integrate_with_v85_insights
        
        store = InsightHistoryStore()
        result = integrate_with_v85_insights(store)
        
        self.assertEqual(result["hooked"], True)
        self.assertEqual(result["measures"], "insight_history_integration")
    
    def test_correlate_with_v78_traces(self):
        """Test correlation hook with v78 traces."""
        from weslr.operator_insight_history import correlate_with_v78_traces
        
        store = InsightHistoryStore()
        result = correlate_with_v78_traces(store)
        
        self.assertEqual(result["hooked"], True)
        self.assertEqual(result["measures"], "trace_correlation_integration")


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with v85 layer."""
    
    def test_no_breaking_changes(self):
        """Test that v86 does not break v85."""
        # v86 should not modify v85 behavior
        history = OperatorInsightHistory()
        
        # Add summary - should work independently
        summary1 = InsightSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_insights=3,
            insight_type_distribution={"convergence": 3},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        summary2 = InsightSummary(
            summary_id="summary-002",
            timestamp="2026-04-07T13:00:00Z",
            total_insights=5,
            insight_type_distribution={"convergence": 3, "divergence": 2},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        comparison = history.compare_significance(summary1, summary2)
        self.assertIsNotNone(comparison.comparison_id)
        
        # Export - should work independently
        export = history.export_operator_readable()
        self.assertIn("COMPARATIVE SIGNIFICANCE", export)
    
    def test_correlation_ids_compatibility(self):
        """Test correlation ID compatibility with v78."""
        store = InsightHistoryStore()
        
        summary = InsightSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_insights=3,
            insight_type_distribution={"convergence": 3},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        correlation_ids = {
            "flow_id": "flow-123",
            "request_id": "req-456",
            "handshake_id": "hs-789",
            "deadline_id": "dl-012",
        }
        
        record = store.add_insight_summary(summary, correlation_ids)
        
        for cid in correlation_ids:
            self.assertIn(cid, record.correlation_ids)
    
    def test_heuristic_significance_not_certainty(self):
        """Test that significance is heuristic, not certainty."""
        history = OperatorInsightHistory()
        history.store = InsightHistoryStore()  # Direct access
        
        summary1 = InsightSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_insights=2,
            insight_type_distribution={"convergence": 2},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        summary2 = InsightSummary(
            summary_id="summary-002",
            timestamp="2026-04-07T13:00:00Z",
            total_insights=5,
            insight_type_distribution={"convergence": 3, "divergence": 2},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        comparison = history.compare_significance(summary1, summary2)
        
        # Heuristic significance should be present but not certainties
        self.assertIn(comparison.significance_shift, ["stable", "increasing", "decreasing"])
        self.assertTrue(comparison.meaningful_shift)
        
        # Reason should exist
        self.assertIsNotNone(comparison.meaningful_shift_reason)
        self.assertGreater(len(comparison.meaningful_shift_reason), 0)


if __name__ == "__main__":
    unittest.main()
