#!/usr/bin/env python3
# test_operator_insight_comparison.py - WESLR v87: Operator Insight Comparison / Drift Tests
# Tests drift comparison layer across incidents and time windows.

from __future__ import annotations

import json
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from weslr.operator_insight_comparison import (
    InsightDriftRecord,
    DriftTrend,
    DriftSummary,
    InsightDriftStore,
    OperatorInsightComparison,
)


class TestInsightDriftRecord(unittest.TestCase):
    """Test InsightDriftRecord dataclass."""
    
    def test_drift_record_creation(self):
        """Test creating an insight drift record."""
        record = InsightDriftRecord(
            drift_id="drift-001",
            timestamp="2026-04-07T12:00:00Z",
            comparison_type="insight_summary",
            summary1_id="summary-001",
            summary2_id="summary-002",
            shared_fields={"total_insights": 5},
            differences={"insight_count": (3, 5)},
            drift_type="increasing",
            drift_magnitude="moderate",
            meaningful_drift=True,
            meaningful_drift_reason="Significant increase detected.",
            correlation_ids={"flow_id": "flow-123"},
        )
        
        self.assertEqual(record.drift_id, "drift-001")
        self.assertEqual(record.drift_type, "increasing")
    
    def test_drift_record_serialization(self):
        """Test drift record to dict."""
        record = InsightDriftRecord(
            drift_id="drift-001",
            timestamp="2026-04-07T12:00:00Z",
            comparison_type="significance",
            summary1_id="summary-001",
            summary2_id="summary-002",
            shared_fields={},
            differences={},
            drift_type="stable",
            drift_magnitude="minor",
            meaningful_drift=False,
            meaningful_drift_reason="No change.",
            correlation_ids={},
        )
        
        data = record.to_dict()
        
        self.assertEqual(data["drift_type"], "stable")
        self.assertFalse(data["meaningful_drift"])
    
    def test_drift_record_json_serialization(self):
        """Test drift record to JSON."""
        record = InsightDriftRecord(
            drift_id="drift-001",
            timestamp="2026-04-07T12:00:00Z",
            comparison_type="confidence",
            summary1_id="summary-001",
            summary2_id="summary-002",
            shared_fields={},
            differences={},
            drift_type="decreasing",
            drift_magnitude="moderate",
            meaningful_drift=True,
            meaningful_drift_reason="Decrease detected.",
            correlation_ids={},
        )
        
        json_str = record.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["drift_type"], "decreasing")
        self.assertTrue(data["meaningful_drift"])


class TestDriftTrend(unittest.TestCase):
    """Test DriftTrend dataclass."""
    
    def test_trend_creation(self):
        """Test creating a drift trend."""
        trend = DriftTrend(
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
        """Test drift trend to dict."""
        trend = DriftTrend(
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
        """Test drift trend to JSON."""
        trend = DriftTrend(
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


class TestDriftSummary(unittest.TestCase):
    """Test DriftSummary dataclass."""
    
    def test_summary_creation(self):
        """Test creating a drift summary."""
        summary = DriftSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_drifts=5,
            drift_type_distribution={"increasing": 3, "stable": 2},
            meaningful_drifts=[{"drift": "test"}],
            drift_trends=[{"trend": "test"}],
            operator_readable="Summary text",
            machine_readable='{"test": true}',
        )
        
        self.assertEqual(summary.summary_id, "summary-001")
        self.assertEqual(summary.total_drifts, 5)
    
    def test_summary_serialization(self):
        """Test drift summary to dict."""
        summary = DriftSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_drifts=3,
            drift_type_distribution={"decreasing": 3},
            meaningful_drifts=[],
            drift_trends=[],
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        data = summary.to_dict()
        
        self.assertEqual(data["total_drifts"], 3)
    
    def test_summary_json_serialization(self):
        """Test drift summary to JSON."""
        summary = DriftSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_drifts=2,
            drift_type_distribution={"stable": 2},
            meaningful_drifts=[],
            drift_trends=[],
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        json_str = summary.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["total_drifts"], 2)


class TestInsightDriftStore(unittest.TestCase):
    """Test InsightDriftStore class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.store = InsightDriftStore()
    
    def test_add_drift_record(self):
        """Test adding a drift record."""
        drift = type('ComparativeSignificance', (), {
            'comparison_type': 'insight_summary',
            'summary1_id': 'summary-001',
            'summary2_id': 'summary-002',
            'shared_fields': {'total_insights': 5},
            'differences': {'insight_count': (3, 5)},
            'significance_shift': 'increasing',
            'meaningful_shift': True,
            'meaningful_shift_reason': 'Increase detected.',
        })()
        
        record = self.store.add_drift_record(drift, {"flow_id": "flow-123"})
        
        self.assertEqual(record.drift_type, "increasing")
        self.assertEqual(record.correlation_ids["flow_id"], "flow-123")
    
    def test_add_drift_record_no_correlation(self):
        """Test adding drift without correlation IDs."""
        drift = type('ComparativeSignificance', (), {
            'comparison_type': 'insight_summary',
            'summary1_id': 'summary-001',
            'summary2_id': 'summary-002',
            'shared_fields': {},
            'differences': {},
            'significance_shift': 'stable',
            'meaningful_shift': False,
            'meaningful_shift_reason': 'No change.',
        })()
        
        record = self.store.add_drift_record(drift)
        
        self.assertEqual(record.drift_type, "stable")
        self.assertEqual(record.correlation_ids, {})
    
    def test_get_latest_drifts(self):
        """Test getting latest drift records."""
        drift1 = type('ComparativeSignificance', (), {
            'comparison_type': 'insight_summary',
            'summary1_id': 'summary-001',
            'summary2_id': 'summary-002',
            'shared_fields': {},
            'differences': {},
            'significance_shift': 'stable',
            'meaningful_shift': False,
            'meaningful_shift_reason': 'No change.',
        })()
        drift2 = type('ComparativeSignificance', (), {
            'comparison_type': 'insight_summary',
            'summary1_id': 'summary-002',
            'summary2_id': 'summary-003',
            'shared_fields': {},
            'differences': {},
            'significance_shift': 'increasing',
            'meaningful_shift': True,
            'meaningful_shift_reason': 'Increase.',
        })()
        drift3 = type('ComparativeSignificance', (), {
            'comparison_type': 'insight_summary',
            'summary1_id': 'summary-003',
            'summary2_id': 'summary-004',
            'shared_fields': {},
            'differences': {},
            'significance_shift': 'increasing',
            'meaningful_shift': True,
            'meaningful_shift_reason': 'Increase.',
        })()
        
        self.store.add_drift_record(drift1)
        self.store.add_drift_record(drift2)
        self.store.add_drift_record(drift3)
        
        latest = self.store.get_latest_drifts(2)
        
        self.assertEqual(len(latest), 2)
        self.assertEqual(latest[0].summary2_id, "summary-003")
        self.assertEqual(latest[1].summary2_id, "summary-004")
    
    def test_get_drift_by_comparison(self):
        """Test getting drift by comparison pair."""
        drift = type('ComparativeSignificance', (), {
            'comparison_type': 'insight_summary',
            'summary1_id': 'summary-001',
            'summary2_id': 'summary-002',
            'shared_fields': {},
            'differences': {},
            'significance_shift': 'stable',
            'meaningful_shift': False,
            'meaningful_shift_reason': 'No change.',
        })()
        
        record = self.store.add_drift_record(drift)
        
        found = self.store.get_drift_by_comparison("summary-001", "summary-002")
        
        self.assertEqual(found, record)
        self.assertIsNone(self.store.get_drift_by_comparison("summary-001", "nonexistent"))
    
    def test_get_drifts_with_correlation_filter(self):
        """Test getting drifts with correlation filters."""
        drift1 = type('ComparativeSignificance', (), {
            'comparison_type': 'insight_summary',
            'summary1_id': 'summary-001',
            'summary2_id': 'summary-002',
            'shared_fields': {},
            'differences': {},
            'significance_shift': 'stable',
            'meaningful_shift': False,
            'meaningful_shift_reason': 'No change.',
        })()
        drift2 = type('ComparativeSignificance', (), {
            'comparison_type': 'insight_summary',
            'summary1_id': 'summary-002',
            'summary2_id': 'summary-003',
            'shared_fields': {},
            'differences': {},
            'significance_shift': 'increasing',
            'meaningful_shift': True,
            'meaningful_shift_reason': 'Increase.',
        })()
        
        self.store.add_drift_record(drift1, {"flow_id": "flow-123"})
        self.store.add_drift_record(drift2, {"flow_id": "flow-456"})
        
        flow1_drifts = self.store.get_drifts(correlation_type="flow_id", correlation_id="flow-123")
        flow2_drifts = self.store.get_drifts(correlation_type="flow_id", correlation_id="flow-456")
        no_filter_drifts = self.store.get_drifts()
        
        self.assertEqual(len(flow1_drifts), 1)
        self.assertEqual(len(flow2_drifts), 1)
        self.assertEqual(len(no_filter_drifts), 2)


class TestOperatorInsightComparison(unittest.TestCase):
    """Test OperatorInsightComparison class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.comparison = OperatorInsightComparison()
    
    def test_compare_drift_increasing(self):
        """Test comparing drift with increasing insights."""
        record = self.comparison.compare_drift(
            summary1_id="summary-001",
            summary2_id="summary-002",
            total_insights1=3,
            total_insights2=5,
            insight_type_distribution1={"convergence": 3},
            insight_type_distribution2={"convergence": 3, "divergence": 2},
            correlation_ids={"flow_id": "flow-123"},
        )
        
        self.assertEqual(record.drift_type, "increasing")
        self.assertTrue(record.meaningful_drift)
    
    def test_compare_drift_stable(self):
        """Test comparing drift with stable insights."""
        record = self.comparison.compare_drift(
            summary1_id="summary-001",
            summary2_id="summary-002",
            total_insights1=3,
            total_insights2=3,
            insight_type_distribution1={"convergence": 3},
            insight_type_distribution2={"convergence": 3},
        )
        
        self.assertEqual(record.drift_type, "stable")
        self.assertFalse(record.meaningful_drift)
    
    def test_compare_drift_decreasing(self):
        """Test comparing drift with decreasing insights."""
        record = self.comparison.compare_drift(
            summary1_id="summary-001",
            summary2_id="summary-002",
            total_insights1=5,
            total_insights2=2,
            insight_type_distribution1={"convergence": 3, "divergence": 2},
            insight_type_distribution2={"convergence": 2},
        )
        
        self.assertEqual(record.drift_type, "decreasing")
        self.assertTrue(record.meaningful_drift)
    
    def test_analyze_drift_trends_empty(self):
        """Test analyzing trends with no drifts."""
        trends = self.comparison.analyze_drift_trends([])
        
        self.assertEqual(len(trends), 0)
    
    def test_analyze_drift_trends(self):
        """Test analyzing trends with drifts."""
        drifts = [
            InsightDriftRecord(
                drift_id="drift-001",
                timestamp="2026-04-07T12:00:00Z",
                comparison_type="insight_summary",
                summary1_id="summary-001",
                summary2_id="summary-002",
                shared_fields={},
                differences={},
                drift_type="increasing",
                drift_magnitude="moderate",
                meaningful_drift=True,
                meaningful_drift_reason="Increase.",
                correlation_ids={},
            ),
            InsightDriftRecord(
                drift_id="drift-002",
                timestamp="2026-04-07T13:00:00Z",
                comparison_type="insight_summary",
                summary1_id="summary-002",
                summary2_id="summary-003",
                shared_fields={},
                differences={},
                drift_type="increasing",
                drift_magnitude="moderate",
                meaningful_drift=True,
                meaningful_drift_reason="Increase.",
                correlation_ids={},
            ),
            InsightDriftRecord(
                drift_id="drift-003",
                timestamp="2026-04-07T14:00:00Z",
                comparison_type="insight_summary",
                summary1_id="summary-003",
                summary2_id="summary-004",
                shared_fields={},
                differences={},
                drift_type="stable",
                drift_magnitude="minor",
                meaningful_drift=False,
                meaningful_drift_reason="No change.",
                correlation_ids={},
            ),
        ]
        
        trends = self.comparison.analyze_drift_trends(drifts)
        
        # Should detect increasing trend
        self.assertGreater(len(trends), 0)
        self.assertEqual(trends[0].trend_type, "insight_count")
        self.assertEqual(trends[0].direction, "increasing")
    
    def test_get_drift_summary_empty(self):
        """Test getting drift summary with no data."""
        empty_comparison = OperatorInsightComparison()
        summary = empty_comparison.get_drift_summary()
        
        self.assertEqual(summary.total_drifts, 0)
        self.assertIn("No drift", summary.operator_readable)
    
    def test_get_drift_summary(self):
        """Test getting drift summary with data."""
        self.comparison.compare_drift(
            summary1_id="summary-001",
            summary2_id="summary-002",
            total_insights1=3,
            total_insights2=5,
            insight_type_distribution1={"convergence": 3},
            insight_type_distribution2={"convergence": 3, "divergence": 2},
        )
        result = self.comparison.get_drift_summary()
        
        self.assertEqual(result.total_drifts, 1)
        self.assertIn("COMPARISON DRIFT SUMMARY", result.operator_readable)
        self.assertIn("HEURISTIC NOTE", result.operator_readable)
    
    def test_export_operator_readable(self):
        """Test exporting operator-readable summary."""
        self.comparison.compare_drift(
            summary1_id="summary-001",
            summary2_id="summary-002",
            total_insights1=3,
            total_insights2=5,
            insight_type_distribution1={"convergence": 3},
            insight_type_distribution2={"convergence": 3, "divergence": 2},
        )
        export = self.comparison.export_operator_readable()
        
        self.assertIn("OPERATOR INSIGHT COMPARISON DRIFT SUMMARY", export)
        self.assertIn("DRIFT TYPE DISTRIBUTION", export)
        self.assertIn("HEURISTIC NOTE", export)
    
    def test_export_machine_readable(self):
        """Test exporting machine-readable summary."""
        self.comparison.compare_drift(
            summary1_id="summary-001",
            summary2_id="summary-002",
            total_insights1=3,
            total_insights2=5,
            insight_type_distribution1={"convergence": 3},
            insight_type_distribution2={"convergence": 3, "divergence": 2},
        )
        export = self.comparison.export_machine_readable()
        data = json.loads(export)
        
        self.assertEqual(data["total_drifts"], 1)
        self.assertIn("drift_type_distribution", data)
        self.assertIn("meaningful_drifts", data)
    
    def test_export_drifts_as_json(self):
        """Test exporting all drifts as JSON."""
        self.comparison.compare_drift(
            summary1_id="summary-001",
            summary2_id="summary-002",
            total_insights1=3,
            total_insights2=5,
            insight_type_distribution1={"convergence": 3},
            insight_type_distribution2={"convergence": 3, "divergence": 2},
        )
        self.comparison.compare_drift(
            summary1_id="summary-002",
            summary2_id="summary-003",
            total_insights1=5,
            total_insights2=7,
            insight_type_distribution1={"convergence": 3, "divergence": 2},
            insight_type_distribution2={"convergence": 4, "divergence": 3},
        )
        
        export = self.comparison.export_drifts_as_json()
        drifts = json.loads(export)
        
        self.assertEqual(len(drifts), 2)
    
    def test_export_drift_trends_as_json(self):
        """Test exporting drift trends as JSON."""
        drifts = [
            InsightDriftRecord(
                drift_id="drift-001",
                timestamp="2026-04-07T12:00:00Z",
                comparison_type="insight_summary",
                summary1_id="summary-001",
                summary2_id="summary-002",
                shared_fields={},
                differences={},
                drift_type="increasing",
                drift_magnitude="moderate",
                meaningful_drift=True,
                meaningful_drift_reason="Increase.",
                correlation_ids={},
            ),
            InsightDriftRecord(
                drift_id="drift-002",
                timestamp="2026-04-07T13:00:00Z",
                comparison_type="insight_summary",
                summary1_id="summary-002",
                summary2_id="summary-003",
                shared_fields={},
                differences={},
                drift_type="increasing",
                drift_magnitude="moderate",
                meaningful_drift=True,
                meaningful_drift_reason="Increase.",
                correlation_ids={},
            ),
        ]
        
        self.comparison.analyze_drift_trends(drifts)
        export = self.comparison.export_drift_trends_as_json()
        trends = json.loads(export)
        
        self.assertGreater(len(trends), 0)
    
    def test_export_meaningful_drifts_as_json(self):
        """Test exporting meaningful drifts as JSON."""
        drift1 = type('ComparativeSignificance', (), {
            'comparison_type': 'insight_summary',
            'summary1_id': 'summary-001',
            'summary2_id': 'summary-002',
            'shared_fields': {},
            'differences': {},
            'significance_shift': 'stable',
            'meaningful_shift': False,
            'meaningful_shift_reason': 'No change.',
        })()
        drift2 = type('ComparativeSignificance', (), {
            'comparison_type': 'insight_summary',
            'summary1_id': 'summary-002',
            'summary2_id': 'summary-003',
            'shared_fields': {},
            'differences': {},
            'significance_shift': 'increasing',
            'meaningful_shift': True,
            'meaningful_shift_reason': 'Increase.',
        })()
        
        self.comparison._drift_store.add_drift_record(drift1)
        self.comparison._drift_store.add_drift_record(drift2)
        
        export = self.comparison.export_meaningful_drifts_as_json()
        meaningful = json.loads(export)
        
        self.assertEqual(len(meaningful), 1)


class TestIntegration(unittest.TestCase):
    """Test integration with other layers."""
    
    def test_integrate_with_v86_comparison(self):
        """Test integration hook with v86 comparison."""
        from weslr.operator_insight_comparison import integrate_with_v86_comparison
        
        store = InsightDriftStore()
        result = integrate_with_v86_comparison(store)
        
        self.assertEqual(result["hooked"], True)
        self.assertEqual(result["measures"], "drift_comparison_integration")
    
    def test_correlate_with_v78_traces(self):
        """Test correlation hook with v78 traces."""
        from weslr.operator_insight_comparison import correlate_with_v78_traces
        
        store = InsightDriftStore()
        result = correlate_with_v78_traces(store)
        
        self.assertEqual(result["hooked"], True)
        self.assertEqual(result["measures"], "trace_correlation_integration")


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with v86 layer."""
    
    def test_no_breaking_changes(self):
        """Test that v87 does not break v86."""
        comparison = OperatorInsightComparison()
        
        # Compare drift - should work independently
        record = comparison.compare_drift(
            summary1_id="summary-001",
            summary2_id="summary-002",
            total_insights1=3,
            total_insights2=5,
            insight_type_distribution1={"convergence": 3},
            insight_type_distribution2={"convergence": 3, "divergence": 2},
        )
        self.assertIsNotNone(record.drift_id)
        self.assertEqual(record.drift_type, "increasing")
        
        # Export - should work independently
        export = comparison.export_operator_readable()
        self.assertIn("COMPARISON DRIFT SUMMARY", export)
        self.assertIn("HEURISTIC NOTE", export)
    
    def test_correlation_ids_compatibility(self):
        """Test correlation ID compatibility with v78/v86."""
        comparison = OperatorInsightComparison()
        
        record = comparison.compare_drift(
            summary1_id="summary-001",
            summary2_id="summary-002",
            total_insights1=3,
            total_insights2=5,
            insight_type_distribution1={"convergence": 3},
            insight_type_distribution2={"convergence": 3, "divergence": 2},
            correlation_ids={
                "flow_id": "flow-123",
                "request_id": "req-456",
                "handshake_id": "hs-789",
                "deadline_id": "dl-012",
            },
        )
        
        for cid in ["flow_id", "request_id", "handshake_id", "deadline_id"]:
            self.assertIn(cid, record.correlation_ids)
    
    def test_heuristic_significance_not_certainty(self):
        """Test that significance is heuristic, not certainty."""
        comparison = OperatorInsightComparison()
        
        record = comparison.compare_drift(
            summary1_id="summary-001",
            summary2_id="summary-002",
            total_insights1=2,
            total_insights2=5,
            insight_type_distribution1={"convergence": 2},
            insight_type_distribution2={"convergence": 3, "divergence": 2},
        )
        
        # Drift type should be present but not certainties
        self.assertIn(record.drift_type, ["stable", "increasing", "decreasing"])
        self.assertTrue(record.meaningful_drift)
        
        # Reason should exist
        self.assertIsNotNone(record.meaningful_drift_reason)
        self.assertGreater(len(record.meaningful_drift_reason), 0)


if __name__ == "__main__":
    unittest.main()
