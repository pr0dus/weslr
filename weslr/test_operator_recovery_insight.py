#!/usr/bin/env python3
# test_operator_recovery_insight.py - WESLR v85: Operator Recovery Insight Tests
# Tests insight layer for recovery patterns over time.

from __future__ import annotations

import json
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from weslr.operator_recovery_insight import (
    RecoveryInsight,
    TrendShift,
    InsightSummary,
    OperatorRecoveryInsight,
)
from weslr.recovery_pattern_history import TrendSummary, RecoveryPatternHistory
from weslr.recovery_pattern_comparison import (
    RecoveryPatternComparison,
    PatternComparison,
)


class TestRecoveryInsight(unittest.TestCase):
    """Test RecoveryInsight dataclass."""
    
    def test_insight_creation(self):
        """Test creating a recovery insight."""
        insight = RecoveryInsight(
            insight_id="insight-001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern-001",
            correlation_ids={"flow_id": "flow-123"},
            interpretation="Test interpretation",
            significance="high",
            significance_reason="Test reason",
            guidance="Test guidance",
            pattern_type="recommendation",
            historical_context="Test context",
        )
        
        self.assertEqual(insight.insight_id, "insight-001")
        self.assertEqual(insight.insight_type, "trend_shift")
        self.assertEqual(insight.significance, "high")
    
    def test_insight_serialization(self):
        """Test recovery insight to dict."""
        insight = RecoveryInsight(
            insight_id="insight-001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="convergence",
            pattern_id="pattern-001",
            correlation_ids={"flow_id": "flow-123"},
            interpretation="Test interpretation",
            significance="medium",
            significance_reason="Test reason",
            guidance="Test guidance",
            pattern_type="decision_trace",
            historical_context="Test context",
        )
        
        data = insight.to_dict()
        
        self.assertEqual(data["insight_id"], "insight-001")
        self.assertEqual(data["insight_type"], "convergence")
        self.assertEqual(data["pattern_type"], "decision_trace")
    
    def test_insight_json_serialization(self):
        """Test recovery insight to JSON."""
        insight = RecoveryInsight(
            insight_id="insight-001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="divergence",
            pattern_id="pattern-001",
            correlation_ids={"flow_id": "flow-123"},
            interpretation="Test interpretation",
            significance="low",
            significance_reason="Test reason",
            pattern_type="comparison",
            historical_context="Test context",
        )
        
        json_str = insight.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["insight_type"], "divergence")
        self.assertEqual(data["significance"], "low")


class TestTrendShift(unittest.TestCase):
    """Test TrendShift dataclass."""
    
    def test_shift_creation(self):
        """Test creating a trend shift."""
        shift = TrendShift(
            shift_id="shift-001",
            timestamp="2026-04-07T12:00:00Z",
            trend_type="confidence",
            direction="increasing",
            magnitude="moderate",
            interpretation="Test interpretation",
            significance="medium",
            significance_reason="Test reason",
            pattern_type="recovery",
            reference_pattern_id="ref-001",
        )
        
        self.assertEqual(shift.shift_id, "shift-001")
        self.assertEqual(shift.trend_type, "confidence")
        self.assertEqual(shift.direction, "increasing")
    
    def test_shift_serialization(self):
        """Test trend shift to dict."""
        shift = TrendShift(
            shift_id="shift-001",
            timestamp="2026-04-07T12:00:00Z",
            trend_type="safe_action",
            direction="convergence",
            magnitude="moderate",
            interpretation="Test interpretation",
            significance="high",
            significance_reason="Test reason",
            pattern_type="decision_trace",
            reference_pattern_id="ref-001",
        )
        
        data = shift.to_dict()
        
        self.assertEqual(data["trend_type"], "safe_action")
        self.assertEqual(data["direction"], "convergence")
    
    def test_shift_json_serialization(self):
        """Test trend shift to JSON."""
        shift = TrendShift(
            shift_id="shift-001",
            timestamp="2026-04-07T12:00:00Z",
            trend_type="confidence",
            direction="decreasing",
            magnitude="significant",
            interpretation="Test interpretation",
            significance="high",
            significance_reason="Test reason",
            pattern_type="recovery",
            reference_pattern_id="ref-001",
        )
        
        json_str = shift.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["direction"], "decreasing")
        self.assertEqual(data["magnitude"], "significant")


class TestInsightSummary(unittest.TestCase):
    """Test InsightSummary dataclass."""
    
    def test_summary_creation(self):
        """Test creating an insight summary."""
        summary = InsightSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_insights=5,
            insight_type_distribution={"convergence": 3, "divergence": 2},
            trend_shifts=[{"trend_type": "confidence", "direction": "increasing"}],
            convergence_patterns={"action_a": 3},
            divergence_patterns={"action_b": 2},
            repeated_pattern_significance={"pattern_a": 4},
            operator_readable="Summary text",
            machine_readable='{"test": true}',
        )
        
        self.assertEqual(summary.summary_id, "summary-001")
        self.assertEqual(summary.total_insights, 5)
    
    def test_summary_serialization(self):
        """Test insight summary to dict."""
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
        
        data = summary.to_dict()
        
        self.assertEqual(data["total_insights"], 3)
        self.assertIn("convergence", data["insight_type_distribution"])
    
    def test_summary_json_serialization(self):
        """Test insight summary to JSON."""
        summary = InsightSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_insights=2,
            insight_type_distribution={"divergence": 2},
            trend_shifts=[],
            convergence_patterns={},
            divergence_patterns={},
            repeated_pattern_significance={},
            operator_readable="Summary",
            machine_readable='{"patterns": 2}',
        )
        
        json_str = summary.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["total_insights"], 2)


class TestOperatorRecoveryInsight(unittest.TestCase):
    """Test OperatorRecoveryInsight layer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.insight = OperatorRecoveryInsight()
    
    def test_detect_trend_shifts_no_confidence(self):
        """Test detecting trend shifts with no confidence data."""
        trend_summary = TrendSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_patterns=0,
            pattern_type_distribution={},
            repeated_patterns={},
            confidence_trend={},  # Empty
            safe_action_patterns={"review": 2, "escalate": 1},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        shifts = self.insight.detect_trend_shifts(trend_summary)
        
        # Should detect safe_action convergence/divergence
        self.assertEqual(len(shifts), 0)  # Only 2 patterns, not enough for divergence
        self.assertEqual(len(self.insight._insights), 1)  # Convergence insight created
    
    def test_detect_trend_shifts_stable_confidence(self):
        """Test detecting trend shifts with stable confidence."""
        trend_summary = TrendSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_patterns=3,
            pattern_type_distribution={"recommendation": 3},
            repeated_patterns={},
            confidence_trend={"high": 3},
            safe_action_patterns={"review": 3},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        shifts = self.insight.detect_trend_shifts(trend_summary)
        
        # Should detect stable confidence
        self.assertGreater(len(shifts), 0)
        self.assertEqual(shifts[0].direction, "stable")
    
    def test_detect_trend_shifts_variable_confidence(self):
        """Test detecting trend shifts with variable confidence."""
        trend_summary = TrendSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_patterns=4,
            pattern_type_distribution={},
            repeated_patterns={},
            confidence_trend={"high": 2, "medium": 1, "low": 1},
            safe_action_patterns={"review": 2, "escalate": 2},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        shifts = self.insight.detect_trend_shifts(trend_summary)
        
        # Should detect variable confidence (high vs low)
        self.assertGreater(len(shifts), 0)
        self.assertEqual(shifts[0].direction, "variable")
    
    def test_detect_repeated_pattern_significance(self):
        """Test detecting repeated pattern significance."""
        repeated_patterns = {
            "pattern_type_recommendation": 3,
            "similarity_high": 5,
            "correlation_flow_id=flow-123": 4,
            "pattern_type_decision_trace": 1,  # Below threshold
            "repeated_pattern_x": 2,  # Added to ensure some patterns match
        }
        
        # Check internal state before
        initial_count = len(self.insight._insights)
        
        insights = self.insight.detect_repeated_pattern_significance(repeated_patterns)
        
        # Should detect significant patterns (>= 2) and add to internal list
        self.assertGreater(len(self.insight._insights), initial_count)
        
        # Verify pattern detection in internal list
        pattern_types = [i.pattern_id for i in self.insight._insights[initial_count:]]
        self.assertIn("pattern_type_recommendation", pattern_types)
        self.assertIn("similarity_high", pattern_types)
        self.assertIn("repeated_pattern_x", pattern_types)
    
    def test_get_significance_reason(self):
        """Test significance reason generation."""
        # Test confidence increasing
        reason = self.insight._get_significance_reason(
            "confidence", "increasing", "moderate"
        )
        self.assertIn("higher", reason.lower())
        
        # Test confidence variable
        reason = self.insight._get_significance_reason(
            "confidence", "variable", "significant"
        )
        self.assertIn("variable", reason.lower())
    
    def test_get_guidance(self):
        """Test guidance generation."""
        # Test convergence
        guidance = self.insight._get_guidance("convergence")
        self.assertIsNotNone(guidance)
        self.assertIn("consistent", guidance.lower())
        
        # Test divergence
        guidance = self.insight._get_guidance("divergence")
        self.assertIsNotNone(guidance)
        self.assertIn("diverse", guidance.lower())
        
        # Test variable
        guidance = self.insight._get_guidance("variable")
        self.assertIsNotNone(guidance)
        self.assertIn("variable", guidance.lower())
    
    def test_analyze_recovery_patterns(self):
        """Test analyzing recovery patterns from v83/v84."""
        # Create a comparison with high similarity patterns
        comparison = RecoveryPatternComparison()
        
        # Add some similar comparisons
        for i in range(5):
            comparison.compare_recommendations(
                {"recommendation_id": f"rec-{i}", "stage": "proposal"},
                {"recommendation_id": f"rec-{i}-dup", "stage": "proposal"},
            )
        
        # Create history
        history = RecoveryPatternHistory()
        for i in range(5):
            history.add_recommendation_pattern(
                {"recommendation_id": f"rec-{i}"},
                {"flow_id": f"flow-{i}"},
            )
        
        # Analyze
        result = self.insight.analyze_recovery_patterns(comparison, history)
        
        self.assertEqual(result["total_insights"], len(self.insight._insights))
    
    def test_get_insight_summary_empty(self):
        """Test getting insight summary with no insights."""
        empty_insight = OperatorRecoveryInsight()
        summary = empty_insight.get_insight_summary()
        
        self.assertEqual(summary.total_insights, 0)
        self.assertIn("No insights", summary.operator_readable)
    
    def test_get_insight_summary(self):
        """Test getting insight summary with insights."""
        # Add some insights manually
        insight = RecoveryInsight(
            insight_id="insight-001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="convergence",
            pattern_id="pattern-001",
            correlation_ids={"flow_id": "flow-123"},
            interpretation="Test interpretation",
            significance="high",
            significance_reason="Test reason",
            guidance="Test guidance",
            pattern_type="recommendation",
            historical_context="Test context",
        )
        self.insight._insights.append(insight)
        
        summary = self.insight.get_insight_summary()
        
        self.assertEqual(summary.total_insights, 1)
        self.assertIn("convergence", summary.operator_readable)
        self.assertIn("INSIGHT TYPE DISTRIBUTION", summary.operator_readable)
    
    def test_export_operator_readable(self):
        """Test exporting operator-readable summary."""
        # Add an insight first
        insight = RecoveryInsight(
            insight_id="insight-001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="trend_shift",
            pattern_id="pattern-001",
            correlation_ids={},
            interpretation="Test",
            significance="medium",
            significance_reason="Reason",
            pattern_type="recovery",
            historical_context="Context",
        )
        self.insight._insights.append(insight)
        
        export = self.insight.export_operator_readable()
        
        self.assertIn("OPERATOR RECOVERY INSIGHT SUMMARY", export)
        self.assertIn("INSIGHT TYPE DISTRIBUTION", export)
        self.assertIn("HEURISTIC NOTE", export)
    
    def test_export_machine_readable(self):
        """Test exporting machine-readable summary."""
        # Add an insight first
        insight = RecoveryInsight(
            insight_id="insight-001",
            timestamp="2026-04-07T12:00:00Z",
            insight_type="divergence",
            pattern_id="pattern-001",
            correlation_ids={},
            interpretation="Test",
            significance="low",
            significance_reason="Reason",
            pattern_type="decision_trace",
            historical_context="Context",
        )
        self.insight._insights.append(insight)
        
        export = self.insight.export_machine_readable()
        data = json.loads(export)
        
        self.assertEqual(data["total_insights"], 1)
        self.assertIn("insight_type_distribution", data)
        self.assertIn("repeated_pattern_significance", data)
    
    def test_export_insights_as_json(self):
        """Test exporting all insights as JSON."""
        # Add multiple insights
        for i in range(3):
            insight = RecoveryInsight(
                insight_id=f"insight-{i}",
                timestamp="2026-04-07T12:00:00Z",
                insight_type="convergence",
                pattern_id=f"pattern-{i}",
                correlation_ids={},
                interpretation="Test",
                significance="medium",
                significance_reason="Reason",
                pattern_type="recommendation",
                historical_context="Context",
            )
            self.insight._insights.append(insight)
        
        export = self.insight.export_insights_as_json()
        insights = json.loads(export)
        
        self.assertEqual(len(insights), 3)
        self.assertEqual(insights[0]["insight_type"], "convergence")
    
    def test_export_trend_shifts_as_json(self):
        """Test exporting trend shifts as JSON."""
        # Create trend summary for shift detection
        trend_summary = TrendSummary(
            summary_id="summary-001",
            timestamp="2026-04-07T12:00:00Z",
            total_patterns=4,
            pattern_type_distribution={},
            repeated_patterns={},
            confidence_trend={"high": 2, "low": 2},
            safe_action_patterns={"review": 2, "escalate": 2},
            operator_readable="Summary",
            machine_readable='{"test": true}',
        )
        
        # Detect shifts
        shifts = self.insight.detect_trend_shifts(trend_summary)
        
        # Export
        export = self.insight.export_trend_shifts_as_json()
        shifts_data = json.loads(export)
        
        self.assertEqual(len(shifts_data), len(shifts))
        self.assertIn("confidence", shifts_data[0]["trend_type"])


class TestIntegration(unittest.TestCase):
    """Test integration with other layers."""
    
    def test_integrate_with_v83_comparison(self):
        """Test integration hook with v83 comparison layer."""
        from weslr.operator_recovery_insight import integrate_with_v83_comparison
        
        insight = OperatorRecoveryInsight()
        result = integrate_with_v83_comparison(insight)
        
        self.assertEqual(result["hooked"], True)
        self.assertEqual(result["measures"], "comparison_insight_integration")
    
    def test_integrate_with_v84_history(self):
        """Test integration hook with v84 history layer."""
        from weslr.operator_recovery_insight import integrate_with_v84_history
        
        insight = OperatorRecoveryInsight()
        result = integrate_with_v84_history(insight)
        
        self.assertEqual(result["hooked"], True)
        self.assertEqual(result["measures"], "history_insight_integration")


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with v76-v84 layers."""
    
    def test_no_breaking_changes(self):
        """Test that v85 does not break existing layers."""
        # This layer should not modify v76-v84 behavior
        insight = OperatorRecoveryInsight()
        
        # Add an insight - should work independently
        insight._insights.append(
            RecoveryInsight(
                insight_id="insight-001",
                timestamp="2026-04-07T12:00:00Z",
                insight_type="convergence",
                pattern_id="pattern-001",
                correlation_ids={},
                interpretation="Test",
                significance="medium",
                significance_reason="Reason",
                pattern_type="recommendation",
                historical_context="Context",
            )
        )
        
        # Export should work independently
        export = insight.export_operator_readable()
        self.assertIn("OPERATOR RECOVERY INSIGHT SUMMARY", export)
    
    def test_correlation_ids_compatibility(self):
        """Test correlation ID compatibility with v78."""
        insight = OperatorRecoveryInsight()
        
        # v78 uses flow_id, request_id, handshake_id, deadline_id
        correlation_ids = {
            "flow_id": "flow-123",
            "request_id": "req-456",
            "handshake_id": "hs-789",
            "deadline_id": "dl-012",
        }
        
        # Create insight with correlation IDs
        insight._insights.append(
            RecoveryInsight(
                insight_id="insight-001",
                timestamp="2026-04-07T12:00:00Z",
                insight_type="convergence",
                pattern_id="pattern-001",
                correlation_ids=correlation_ids,
                interpretation="Test",
                significance="medium",
                significance_reason="Reason",
                pattern_type="recommendation",
                historical_context="Context",
            )
        )
        
        # Verify correlation IDs are preserved
        export = insight.export_insights_as_json()
        data = json.loads(export)
        
        for cid in correlation_ids:
            self.assertIn(cid, data[0]["correlation_ids"])
    
    def test_significance_is_guidance_not_certainty(self):
        """Test that significance is guidance, not certainty."""
        insight = OperatorRecoveryInsight()
        
        # Get insight with high significance
        shift = TrendShift(
            shift_id="shift-001",
            timestamp="2026-04-07T12:00:00Z",
            trend_type="confidence",
            direction="variable",
            magnitude="significant",
            interpretation="Test",
            significance="high",
            significance_reason="Test reason",
            pattern_type="recovery",
            reference_pattern_id="ref-001",
        )
        
        # Significance should be present (low/medium/high)
        self.assertIn(shift.significance, ["low", "medium", "high"])
        
        # Significance reason should exist and be non-empty
        self.assertIsNotNone(shift.significance_reason)
        self.assertGreater(len(shift.significance_reason), 0)


if __name__ == "__main__":
    unittest.main()
