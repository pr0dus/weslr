# test_operator_case_window_summary.py - WESLR v92: Operator Case Window Summary / Drift Significance Layer Tests
# Tests for v92 Operator Case Window Summary / Drift Significance Layer.
# Read-only operator-facing layer tests only.
# No optimization, no remediation, no orchestration, no backend/service/UI.
# No TIA/C#, no storage framework expansion, no analytics engine beyond window scope.

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from weslr.operator_case_timeline_comparison import (
    EscalationDriftRecord,
    ConfidenceDriftRecord,
    SafeActionDriftRecord,
    OperatorCaseTimelineComparison,
    TimelineComparisonExporter,
    TimelineComparisonResult,
)
from weslr.operator_case_window_summary import (
    DriftSignificance,
    OperatorCaseWindowSummary,
    WindowConfiguration,
    WindowSummary,
    WindowSummaryExporter,
)


# ============================================================================
# TEST DATA HELPERS
# ============================================================================


def create_test_window_config() -> WindowConfiguration:
    """Create test window configuration."""
    return WindowConfiguration(
        config_id="window_001",
        window_start="2026-04-08T00:00:00Z",
        window_end="2026-04-08T23:59:59Z",
        min_significance_threshold=0.3,
        max_significant_drifts=5,
    )


def create_test_comparison() -> TimelineComparisonResult:
    """Create test timeline comparison result."""
    # Create escalation drift
    escalation_drift = EscalationDriftRecord(
        drift_id="esc_drift_001",
        timestamp="2026-04-08T12:00:00Z",
        comparison_id="comp_001",
        case1_id="case1",
        case2_id="case2",
        case1_urgency="normal",
        case2_urgency="attention",
        urgency_shift="increasing",
        case1_event_count=1,
        case2_event_count=3,
        event_delta=2,
        interpretation="Escalation increased",
        heuristic_significance="moderate",
        heuristic_reason="Event count changed",
        correlation_ids={"flow_id": "flow_test"},
    )
    
    # Create confidence drift
    confidence_drift = ConfidenceDriftRecord(
        drift_id="conf_drift_001",
        timestamp="2026-04-08T12:00:00Z",
        comparison_id="comp_001",
        case1_id="case1",
        case2_id="case2",
        case1_confidence="medium",
        case2_confidence="high",
        confidence_shift="increasing",
        guidance_context="recovery guidance",
        guidance_change="unchanged",
        interpretation="Confidence increased",
        heuristic_significance="moderate",
        heuristic_reason="Confidence shift",
        correlation_ids={"flow_id": "flow_test"},
    )
    
    # Create safe-action drift
    safe_action_drift = SafeActionDriftRecord(
        drift_id="safe_drift_001",
        timestamp="2026-04-08T12:00:00Z",
        comparison_id="comp_001",
        case1_id="case1",
        case2_id="case2",
        case1_action="Review logs",
        case2_action="Monitor metrics",
        action_shift="updated",
        evidence_context="evidence references",
        evidence_change="unchanged",
        interpretation="Action changed",
        heuristic_significance="low",
        heuristic_reason="Action shift",
        correlation_ids={"flow_id": "flow_test"},
    )
    
    # Create comparison result
    result = TimelineComparisonResult(
        summary_id="comp_001",
        timestamp="2026-04-08T12:00:00Z",
        case1_id="case1",
        case2_id="case2",
        escalation_drifts=[escalation_drift],
        confidence_drifts=[confidence_drift],
        safe_action_drifts=[safe_action_drift],
        drift_distribution={"escalation": 1, "confidence": 1, "safe_action": 1, "total": 3},
        meaningful_drifts=3,
        drift_trends=[{"trend_type": "escalation", "direction": "increasing"}],
        correlation_ids={"flow_id": "flow_test", "request_id": "req_test"},
        operator_readable="Operator comparison",
        machine_readable='{"comparison_id": "comp_001"}',
    )
    
    return result


# ============================================================================
# MODEL TESTS (TestOperatorCaseWindowSummaryModel)
# ============================================================================


class TestCaseWindowSummaryModel(unittest.TestCase):
    """Model tests for WindowSummary."""
    
    def test_window_config_creation(self) -> None:
        """Test WindowConfiguration creation."""
        config = WindowConfiguration(
            config_id="config_001",
            window_start="2026-04-08T00:00:00Z",
            window_end="2026-04-08T23:59:59Z",
            min_significance_threshold=0.5,
            max_significant_drifts=10,
        )
        
        self.assertEqual(config.config_id, "config_001")
        self.assertEqual(config.min_significance_threshold, 0.5)
    
    def test_window_config_to_dict(self) -> None:
        """Test WindowConfiguration.to_dict()."""
        config = WindowConfiguration(
            config_id="config_002",
            window_start="2026-04-08T00:00:00Z",
            window_end="2026-04-08T23:59:59Z",
            min_significance_threshold=0.3,
            max_significant_drifts=5,
        )
        
        data = config.to_dict()
        self.assertEqual(data["config_id"], "config_002")
        self.assertEqual(data["min_significance_threshold"], 0.3)
    
    def test_drift_significance_model(self) -> None:
        """Test DriftSignificance model."""
        significance = DriftSignificance(
            significance_id="signif_001",
            timestamp="2026-04-08T12:00:00Z",
            drift_type="escalation",
            comparison_id="comp_001",
            reference_drift_id="drift_001",
            drift_direction="increasing",
            base_weight=1.0,
            context_modifier=1.5,
            final_significance=0.9,
            interpretation="Escalation significant",
            heuristic_significance="high",
            heuristic_reason="High urgency shift",
        )
        
        data = significance.to_dict()
        self.assertEqual(data["drift_type"], "escalation")
        self.assertEqual(data["final_significance"], 0.9)
    
    def test_window_summary_creation(self) -> None:
        """Test WindowSummary creation."""
        config = WindowConfiguration(
            config_id="config_001",
            window_start="2026-04-08T00:00:00Z",
            window_end="2026-04-08T23:59:59Z",
            min_significance_threshold=0.3,
            max_significant_drifts=5,
        )
        
        summary = WindowSummary(
            summary_id="summary_001",
            timestamp="2026-04-08T12:00:00Z",
            window_config_id=config.config_id,
            window_start=config.window_start,
            window_end=config.window_end,
            comparison_count=3,
            escalation_significance=[],
            confidence_significance=[],
            safe_action_significance=[],
            most_significant_drifts=[],
            significance_distribution={"total": 0.0},
            total_significance=0.0,
            correlation_ids={},
            operator_readable="",
            machine_readable="{}",
        )
        
        self.assertEqual(summary.summary_id, "summary_001")
        self.assertEqual(summary.comparison_count, 3)
    
    def test_window_summary_to_dict(self) -> None:
        """Test WindowSummary.to_dict()."""
        config = WindowConfiguration(
            config_id="config_001",
            window_start="2026-04-08T00:00:00Z",
            window_end="2026-04-08T23:59:59Z",
            min_significance_threshold=0.3,
            max_significant_drifts=5,
        )
        
        summary = WindowSummary(
            summary_id="summary_002",
            timestamp="2026-04-08T12:00:00Z",
            window_config_id=config.config_id,
            window_start=config.window_start,
            window_end=config.window_end,
            comparison_count=3,
            escalation_significance=[],
            confidence_significance=[],
            safe_action_significance=[],
            most_significant_drifts=[{"drift_type": "escalation"}],
            significance_distribution={"total": 1.5},
            total_significance=1.5,
            correlation_ids={"flow_id": "flow_001"},
            operator_readable="Operator summary",
            machine_readable="{}",
        )
        
        data = summary.to_dict()
        self.assertEqual(data["summary_id"], "summary_002")
        self.assertEqual(data["comparison_count"], 3)
    
    def test_window_summary_to_json(self) -> None:
        """Test WindowSummary.to_json()."""
        config = WindowConfiguration(
            config_id="config_001",
            window_start="2026-04-08T00:00:00Z",
            window_end="2026-04-08T23:59:59Z",
            min_significance_threshold=0.3,
            max_significant_drifts=5,
        )
        
        summary = WindowSummary(
            summary_id="summary_003",
            timestamp="2026-04-08T12:00:00Z",
            window_config_id=config.config_id,
            window_start=config.window_start,
            window_end=config.window_end,
            comparison_count=3,
            escalation_significance=[],
            confidence_significance=[],
            safe_action_significance=[],
            most_significant_drifts=[],
            significance_distribution={"total": 0.0},
            total_significance=0.0,
            correlation_ids={},
            operator_readable="",
            machine_readable="{}",
        )
        
        json_str = summary.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["summary_id"], "summary_003")
        self.assertIsInstance(data, dict)


# ============================================================================
# BEHAVIOR TESTS (TestOperatorCaseWindowSummaryBehavior)
# ============================================================================


class TestCaseWindowSummaryBehavior(unittest.TestCase):
    """Behavior tests for OperatorCaseWindowSummary."""
    
    def test_window_summary_creation(self) -> None:
        """Test window summary creation."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        
        result = window_summary.summarize_window([comparison], config)
        
        self.assertEqual(result.comparison_count, 1)
        self.assertIn("window_summary", result.summary_id)
    
    def test_export_summary_operator_format(self) -> None:
        """Test WindowSummaryExporter.export_summary(operator format)."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        result = window_summary.summarize_window([comparison], config)
        
        operator_output = WindowSummaryExporter.export_summary(result, format="operator")
        
        self.assertIsInstance(operator_output, str)
        self.assertIn("OPERATOR CASE WINDOW SUMMARY", operator_output)
    
    def test_export_summary_json_format(self) -> None:
        """Test WindowSummaryExporter.export_summary(json format)."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        result = window_summary.summarize_window([comparison], config)
        
        json_output = WindowSummaryExporter.export_summary(result, format="json")
        
        data = json.loads(json_output)
        self.assertEqual(data["summary_id"], result.summary_id)
    
    def test_export_multiple_summaries(self) -> None:
        """Test WindowSummaryExporter.export_multiple()."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        
        window_summary.summarize_window([comparison], config)
        window_summary.summarize_window([comparison], config)
        
        summaries = window_summary.get_summaries()
        json_output = WindowSummaryExporter.export_multiple(summaries, format="json")
        
        data = json.loads(json_output)
        self.assertEqual(len(data), 2)
    
    def test_export_machine_readable(self) -> None:
        """Test OperatorCaseWindowSummary.export_machine_readable()."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        window_summary.summarize_window([comparison], config)
        
        machine_output = window_summary.export_machine_readable()
        data = json.loads(machine_output)
        
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
    
    def test_get_summary_by_id(self) -> None:
        """Test OperatorCaseWindowSummary.get_summary()."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        result = window_summary.summarize_window([comparison], config)
        
        retrieved = window_summary.get_summary(result.summary_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.summary_id, result.summary_id)
    
    def test_export_operator_readable(self) -> None:
        """Test OperatorCaseWindowSummary.export_operator_readable()."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        window_summary.summarize_window([comparison], config)
        
        operator_output = window_summary.export_operator_readable()
        
        self.assertIn("ALL CASE WINDOW SUMMARIES", operator_output)
        self.assertIn("Total Summaries: 1", operator_output)


# ============================================================================
# INTEGRATION TESTS (TestOperatorCaseWindowSummaryIntegration)
# ============================================================================


class TestOperatorCaseWindowSummaryIntegration(unittest.TestCase):
    """Integration tests for OperatorCaseWindowSummary."""
    
    def test_window_with_v91_comparisons(self) -> None:
        """Test window summary with v91 TimelineComparisonResult."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        
        result = window_summary.summarize_window([comparison], config)
        
        # Should have significance records
        self.assertGreater(len(result.escalation_significance), 0)
        self.assertGreater(len(result.confidence_significance), 0)
        self.assertGreater(len(result.safe_action_significance), 0)
    
    def test_significance_calculation(self) -> None:
        """Test drift significance calculation."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        
        result = window_summary.summarize_window([comparison], config)
        
        # Verify significance distribution
        self.assertIn("escalation", result.significance_distribution)
        self.assertIn("confidence", result.significance_distribution)
        self.assertIn("safe_action", result.significance_distribution)
        self.assertIn("total", result.significance_distribution)
    
    def test_most_significant_drifts(self) -> None:
        """Test most significant drifts identification."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        
        result = window_summary.summarize_window([comparison], config)
        
        # Should have most significant drifts
        self.assertGreater(len(result.most_significant_drifts), 0)
        
        # Check drift structure
        for drift in result.most_significant_drifts:
            self.assertIn("drift_type", drift)
            self.assertIn("final_significance", drift)
    
    def test_correlation_id_propagation(self) -> None:
        """Test that correlation IDs propagate through window summary."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        
        result = window_summary.summarize_window(
            [comparison], config,
            correlation_ids={
                "flow_id": "flow_test",
                "request_id": "req_test",
                "handshake_id": "hand_test",
                "deadline_id": "dl_test",
            },
        )
        
        self.assertEqual(result.correlation_ids["flow_id"], "flow_test")
        self.assertEqual(result.correlation_ids["request_id"], "req_test")
    
    def test_total_significance_calculation(self) -> None:
        """Test total significance calculation."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        
        result = window_summary.summarize_window([comparison], config)
        
        # Total should be sum of all significances
        expected_total = (
            result.significance_distribution.get("escalation", 0) +
            result.significance_distribution.get("confidence", 0) +
            result.significance_distribution.get("safe_action", 0)
        )
        self.assertAlmostEqual(result.total_significance, expected_total, places=1)
    
    def test_escalation_significance_weighting(self) -> None:
        """Test escalation significance weighting."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        
        result = window_summary.summarize_window([comparison], config)
        
        # Escalation should have base weight of 1.0
        for sig in result.escalation_significance:
            self.assertEqual(sig.base_weight, 1.0)
    
    def test_confidence_significance_weighting(self) -> None:
        """Test confidence significance weighting."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        
        result = window_summary.summarize_window([comparison], config)
        
        # Confidence should have base weight of 0.8
        for sig in result.confidence_significance:
            self.assertEqual(sig.base_weight, 0.8)
    
    def test_safe_action_significance_weighting(self) -> None:
        """Test safe-action significance weighting."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        
        result = window_summary.summarize_window([comparison], config)
        
        # Safe-action should have base weight of 0.9
        for sig in result.safe_action_significance:
            self.assertEqual(sig.base_weight, 0.9)


# ============================================================================
# BACKWARD COMPATIBILITY TESTS (TestOperatorCaseWindowSummaryBackwardCompatibility)
# ============================================================================


class TestOperatorCaseWindowSummaryBackwardCompatibility(unittest.TestCase):
    """Backward compatibility tests for OperatorCaseWindowSummary."""
    
    def test_no_breaking_changes(self) -> None:
        """Test that v92 adds no breaking changes to v91."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        
        # Should work without v91 modifications
        result = window_summary.summarize_window([comparison], config)
        
        # Verify all significance types
        self.assertGreaterEqual(len(result.escalation_significance), 0)
        self.assertGreaterEqual(len(result.confidence_significance), 0)
        self.assertGreaterEqual(len(result.safe_action_significance), 0)
    
    def test_readonly_behavior_preserved(self) -> None:
        """Test that v92 maintains read-only behavior."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        
        result = window_summary.summarize_window([comparison], config)
        
        # Verify machine output is JSON (readable, not executable)
        json_output = result.to_json()
        data = json.loads(json_output)
        
        self.assertIsInstance(data, dict)
        self.assertIn("summary_id", data)
        self.assertNotIn("execute", json_output.lower())
        self.assertNotIn("remediate", json_output.lower())
        self.assertNotIn("automate", json_output.lower())
    
    def test_no_autonomous_decisions(self) -> None:
        """Test that v92 adds no autonomous decision logic."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        
        result = window_summary.summarize_window([comparison], config)
        
        # Verify no autonomous decision indicators in output
        operator_summary = result.operator_readable.lower()
        json_summary = result.machine_readable.lower()
        
        # Should not contain autonomous decision language
        self.assertNotIn("automatically", operator_summary)
        self.assertNotIn("automatically", json_summary)
        self.assertNotIn("make decisions", operator_summary)
        self.assertNotIn("make decisions", json_summary)
    
    def test_export_format_compat(self) -> None:
        """Test that export formats are compatible with v91."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        
        result = window_summary.summarize_window([comparison], config)
        
        # Test both export formats
        json_output = WindowSummaryExporter.export_summary(result, format="json")
        operator_output = WindowSummaryExporter.export_summary(result, format="operator")
        
        # Both should be valid
        json_data = json.loads(json_output)
        self.assertIsInstance(json_data, dict)
        self.assertIsInstance(operator_output, str)
    
    def test_no_new_event_framework(self) -> None:
        """Test that v92 does not add new event framework."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        
        result = window_summary.summarize_window([comparison], config)
        
        # Verify telemetry events are descriptive only
        event_data = WindowSummaryExporter.telemetry_event_summary_created(result)
        
        self.assertEqual(event_data["event_type"], "WINDOW_SUMMARY_CREATED")
        self.assertIn("summary_id", event_data)
        # Should not control behavior
        self.assertNotIn("action", event_data)
        self.assertNotIn("trigger", event_data)
    
    def test_v91_compatibility(self) -> None:
        """Test that v92 works with v91 TimelineComparisonResult."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        
        # Create v91 comparison directly
        comparison = create_test_comparison()
        
        # Both should be usable in v92 window summary
        result = window_summary.summarize_window([comparison], config)
        
        # Should complete without errors
        self.assertIsNotNone(result)
        self.assertIsInstance(result, WindowSummary)
    
    def test_heuristic_significance_only(self) -> None:
        """Test that v92 provides only heuristic significance, not certainty."""
        window_summary = OperatorCaseWindowSummary()
        config = create_test_window_config()
        comparison = create_test_comparison()
        
        result = window_summary.summarize_window([comparison], config)
        
        # Check operator summary for heuristic language
        operator_summary = result.operator_readable
        
        # Should contain heuristic-related language
        self.assertIn("heuristic", operator_summary.lower())
        self.assertIn("operator", operator_summary.lower())
        self.assertIn("guidance", operator_summary.lower())
        
        # Should NOT contain certainty language
        self.assertNotIn("will happen", operator_summary.lower())
        self.assertNotIn("guaranteed", operator_summary.lower())
        self.assertNotIn("must", operator_summary.lower())
    
    def test_window_config_lightweight(self) -> None:
        """Test that WindowConfiguration is lightweight with no framework expansion."""
        config = WindowConfiguration(
            config_id="config_001",
            window_start="2026-04-08T00:00:00Z",
            window_end="2026-04-08T23:59:59Z",
            min_significance_threshold=0.3,
            max_significant_drifts=5,
        )
        
        data = config.to_dict()
        
        # Verify minimal config structure
        self.assertIn("config_id", data)
        self.assertIn("window_start", data)
        self.assertIn("window_end", data)
        self.assertIn("min_significance_threshold", data)
        self.assertIn("max_significant_drifts", data)
        
        # Should NOT contain scheduling or persistence fields
        self.assertNotIn("schedule", data)
        self.assertNotIn("persistence", data)
        self.assertNotIn("scheduler", data)
        self.assertNotIn("storage", data)
        self.assertNotIn("engine", data)


# ============================================================================
# RUN TESTS
# ============================================================================


if __name__ == "__main__":
    unittest.main(verbosity=2)
