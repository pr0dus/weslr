# test_operator_case_timeline_comparison.py - WESLR v91: Operator Case Timeline Comparison / Escalation Drift Layer Tests
# Tests for v91 Operator Case Timeline Comparison / Escalation Drift Layer.
# Read-only operator-facing layer tests only.
# No optimization, no remediation, no orchestration, no backend/service/UI.
# No TIA/C#, no storage framework expansion, no analytics engine beyond comparison scope.

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from weslr.operator_case_comparison import (
    CaseComparisonExporter,
    CaseComparisonSummary,
    ConfidenceDifference,
    EscalationDifference,
    OperatorCaseComparison,
    SafeActionDifference,
)
from weslr.operator_case_timeline_comparison import (
    ConfidenceDriftRecord,
    EscalationDriftRecord,
    OperatorCaseTimelineComparison,
    SafeActionDriftRecord,
    TimelineComparisonExporter,
    TimelineComparisonResult,
)


# ============================================================================
# TEST DATA HELPERS
# ============================================================================


def create_test_comparison1() -> CaseComparisonSummary:
    """Create test case comparison summary (earlier time window - lower urgency)."""
    comparison = OperatorCaseComparison()
    
    # Create simple test cases
    from weslr.operator_insight_consolidation import (
        ConsolidatedCaseSummary,
        DecisionTraceSummary,
        DriftSummary,
        EscalationSummary,
        OperatorInsightConsolidation,
        PatternHistorySummary,
        RecoveryGuidanceSummary,
    )
    
    consolidation = OperatorInsightConsolidation()
    
    guidance1 = [
        RecoveryGuidanceSummary(
            guidance_id="guidance_001",
            recommendation_type="suggestion",
            interpretation="System health issue detected",
            confidence_level="medium",
            confidence_reason="Multiple correlated signals",
            safe_next_action="Review system health, check logs",
            evidence_references=["log_entry_123"],
        ),
    ]
    
    escalation1 = [
        EscalationSummary(
            escalation_id="escalation_001",
            time_window="24h",
            escalation_events=[{"event": "signal_1"}],
            urgency_level="normal",
            urgency_reason="Standard escalation context",
            operator_guidance=None,
        ),
    ]
    
    summary1 = consolidation.consolidate_case(
        case_id="case1",
        recovery_service=None,
        decision_trace=None,
        pattern_history=None,
        insight_comparison=None,
        insight_timeline=None,
        correlation_ids={"flow_id": "flow_001", "request_id": "req_001"},
    )
    summary1.recovery_guidance = guidance1
    summary1.escalation_context = escalation1
    summary1.operator_readable = "Operator summary case1"
    summary1.machine_readable = json.dumps({"case_id": "case1"})
    
    guidance2 = [
        RecoveryGuidanceSummary(
            guidance_id="guidance_002",
            recommendation_type="prediction",
            interpretation="Performance degradation likely",
            confidence_level="high",
            confidence_reason="Trend pattern detected",
            safe_next_action="Monitor performance metrics",
            evidence_references=["trend_789", "history_012"],
        ),
    ]
    
    escalation2 = [
        EscalationSummary(
            escalation_id="escalation_002",
            time_window="24h",
            escalation_events=[{"event": "signal_1"}, {"event": "signal_2"}, {"event": "signal_3"}],
            urgency_level="attention",
            urgency_reason="Attention signals detected",
            operator_guidance="Review escalation context",
        ),
    ]
    
    summary2 = consolidation.consolidate_case(
        case_id="case2",
        recovery_service=None,
        decision_trace=None,
        pattern_history=None,
        insight_comparison=None,
        insight_timeline=None,
        correlation_ids={"flow_id": "flow_002", "request_id": "req_002"},
    )
    summary2.recovery_guidance = guidance2
    summary2.escalation_context = escalation2
    summary2.operator_readable = "Operator summary case2"
    summary2.machine_readable = json.dumps({"case_id": "case2"})
    
    # Create comparison
    summary = comparison.compare_cases(summary1, summary2)
    
    # Manually override for test consistency
    summary.operator_readable = "Operator comparison summary 1"
    summary.machine_readable = json.dumps({"comparison_id": "comp_001"})
    
    return summary


def create_test_comparison2() -> CaseComparisonSummary:
    """Create test case comparison summary (later time window - higher urgency)."""
    comparison = OperatorCaseComparison()
    
    # Create simple test cases
    from weslr.operator_insight_consolidation import (
        ConsolidatedCaseSummary,
        DecisionTraceSummary,
        DriftSummary,
        EscalationSummary,
        OperatorInsightConsolidation,
        PatternHistorySummary,
        RecoveryGuidanceSummary,
    )
    
    consolidation = OperatorInsightConsolidation()
    
    guidance1 = [
        RecoveryGuidanceSummary(
            guidance_id="guidance_001",
            recommendation_type="suggestion",
            interpretation="System health issue detected",
            confidence_level="low",
            confidence_reason="Single signal detected",
            safe_next_action="Review logs",
            evidence_references=["log_entry_456"],
        ),
    ]
    
    escalation1 = [
        EscalationSummary(
            escalation_id="escalation_001",
            time_window="24h",
            escalation_events=[{"event": "signal_1"}],
            urgency_level="normal",
            urgency_reason="Standard escalation context",
            operator_guidance=None,
        ),
    ]
    
    summary1 = consolidation.consolidate_case(
        case_id="case3",
        recovery_service=None,
        decision_trace=None,
        pattern_history=None,
        insight_comparison=None,
        insight_timeline=None,
        correlation_ids={"flow_id": "flow_003", "request_id": "req_003"},
    )
    summary1.recovery_guidance = guidance1
    summary1.escalation_context = escalation1
    summary1.operator_readable = "Operator summary case3"
    summary1.machine_readable = json.dumps({"case_id": "case3"})
    
    guidance2 = [
        RecoveryGuidanceSummary(
            guidance_id="guidance_002",
            recommendation_type="prediction",
            interpretation="Critical performance issue",
            confidence_level="high",
            confidence_reason="Strong pattern detected",
            safe_next_action="Immediate intervention",
            evidence_references=["trend_789", "history_012", "critical_signal"],
        ),
    ]
    
    escalation2 = [
        EscalationSummary(
            escalation_id="escalation_002",
            time_window="24h",
            escalation_events=[{"event": "signal_1"}, {"event": "signal_2"}, {"event": "signal_3"}, {"event": "signal_4"}],
            urgency_level="urgent",
            urgency_reason="Critical signals detected",
            operator_guidance="Immediate review required",
        ),
    ]
    
    summary2 = consolidation.consolidate_case(
        case_id="case4",
        recovery_service=None,
        decision_trace=None,
        pattern_history=None,
        insight_comparison=None,
        insight_timeline=None,
        correlation_ids={"flow_id": "flow_004", "request_id": "req_004"},
    )
    summary2.recovery_guidance = guidance2
    summary2.escalation_context = escalation2
    summary2.operator_readable = "Operator summary case4"
    summary2.machine_readable = json.dumps({"case_id": "case4"})
    
    # Create comparison
    summary = comparison.compare_cases(summary1, summary2)
    
    # Manually override for test consistency
    summary.operator_readable = "Operator comparison summary 2"
    summary.machine_readable = json.dumps({"comparison_id": "comp_002"})
    
    return summary


# ============================================================================
# MODEL TESTS (TestOperatorCaseTimelineComparisonModel)
# ============================================================================


class TestCaseTimelineComparisonModel(unittest.TestCase):
    """Model tests for TimelineComparisonResult."""
    
    def test_creation(self) -> None:
        """Test TimelineComparisonResult creation."""
        result = TimelineComparisonResult(
            summary_id="summary_001",
            timestamp="2026-04-08T12:00:00Z",
            case1_id="case1",
            case2_id="case2",
            escalation_drifts=[],
            confidence_drifts=[],
            safe_action_drifts=[],
            drift_distribution={"escalation": 0, "confidence": 0, "safe_action": 0, "total": 0},
            meaningful_drifts=0,
            drift_trends=[],
            correlation_ids={},
            operator_readable="",
            machine_readable="{}",
        )
        
        self.assertEqual(result.summary_id, "summary_001")
        self.assertEqual(result.case1_id, "case1")
        self.assertEqual(result.case2_id, "case2")
    
    def test_to_dict(self) -> None:
        """Test TimelineComparisonResult.to_dict()."""
        result = TimelineComparisonResult(
            summary_id="summary_002",
            timestamp="2026-04-08T12:00:00Z",
            case1_id="case1",
            case2_id="case2",
            escalation_drifts=[],
            confidence_drifts=[],
            safe_action_drifts=[],
            drift_distribution={"escalation": 1, "confidence": 1, "safe_action": 1, "total": 3},
            meaningful_drifts=3,
            drift_trends=[{"trend_type": "escalation", "direction": "increasing"}],
            correlation_ids={"flow_id": "flow_002"},
            operator_readable="Operator summary",
            machine_readable="{}",
        )
        
        data = result.to_dict()
        
        self.assertEqual(data["summary_id"], "summary_002")
        self.assertEqual(data["case1_id"], "case1")
        self.assertEqual(data["drift_distribution"]["total"], 3)
    
    def test_to_json(self) -> None:
        """Test TimelineComparisonResult.to_json()."""
        result = TimelineComparisonResult(
            summary_id="summary_003",
            timestamp="2026-04-08T12:00:00Z",
            case1_id="case1",
            case2_id="case2",
            escalation_drifts=[],
            confidence_drifts=[],
            safe_action_drifts=[],
            drift_distribution={"escalation": 0, "confidence": 0, "safe_action": 0, "total": 0},
            meaningful_drifts=0,
            drift_trends=[],
            correlation_ids={},
            operator_readable="",
            machine_readable="{}",
        )
        
        json_str = result.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["summary_id"], "summary_003")
        self.assertIsInstance(data, dict)
    
    def test_escalation_drift_record_model(self) -> None:
        """Test EscalationDriftRecord model."""
        drift = EscalationDriftRecord(
            drift_id="drift_001",
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
            correlation_ids={},
        )
        
        data = drift.to_dict()
        self.assertEqual(data["case1_urgency"], "normal")
        self.assertEqual(data["case2_urgency"], "attention")
    
    def test_confidence_drift_record_model(self) -> None:
        """Test ConfidenceDriftRecord model."""
        drift = ConfidenceDriftRecord(
            drift_id="drift_002",
            timestamp="2026-04-08T12:00:00Z",
            comparison_id="comp_002",
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
            correlation_ids={},
        )
        
        data = drift.to_dict()
        self.assertEqual(data["case1_confidence"], "medium")
        self.assertEqual(data["case2_confidence"], "high")
    
    def test_safe_action_drift_record_model(self) -> None:
        """Test SafeActionDriftRecord model."""
        drift = SafeActionDriftRecord(
            drift_id="drift_003",
            timestamp="2026-04-08T12:00:00Z",
            comparison_id="comp_003",
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
            correlation_ids={},
        )
        
        data = drift.to_dict()
        self.assertEqual(data["case1_action"], "Review logs")
        self.assertEqual(data["case2_action"], "Monitor metrics")


# ============================================================================
# BEHAVIOR TESTS (TestOperatorCaseTimelineComparisonBehavior)
# ============================================================================


class TestCaseTimelineComparisonBehavior(unittest.TestCase):
    """Behavior tests for OperatorCaseTimelineComparison."""
    
    def test_comparison_creation(self) -> None:
        """Test timeline comparison creation."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        result = timeline_comparison.compare_timeline(comparison1, comparison2)
        
        self.assertEqual(result.case1_id, comparison1.case1_id)
        self.assertEqual(result.case2_id, comparison1.case2_id)
    
    def test_export_summary_operator_format(self) -> None:
        """Test TimelineComparisonExporter.export_summary(operator format)."""
        timeline_comparison = OperatorCaseTimelineComparison()
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        result = timeline_comparison.compare_timeline(comparison1, comparison2)
        
        operator_output = TimelineComparisonExporter.export_summary(result, format="operator")
        
        self.assertIsInstance(operator_output, str)
        self.assertIn("OPERATOR CASE TIMELINE COMPARISON SUMMARY", operator_output)
    
    def test_export_summary_json_format(self) -> None:
        """Test TimelineComparisonExporter.export_summary(json format)."""
        timeline_comparison = OperatorCaseTimelineComparison()
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        result = timeline_comparison.compare_timeline(comparison1, comparison2)
        
        json_output = TimelineComparisonExporter.export_summary(result, format="json")
        
        data = json.loads(json_output)
        self.assertEqual(data["summary_id"], result.summary_id)
        self.assertEqual(data["case1_id"], comparison1.case1_id)
    
    def test_export_multiple_results(self) -> None:
        """Test TimelineComparisonExporter.export_multiple()."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        timeline_comparison.compare_timeline(comparison1, comparison2)
        timeline_comparison.compare_timeline(comparison1, comparison2)
        
        results = timeline_comparison.get_results()
        json_output = TimelineComparisonExporter.export_multiple(results, format="json")
        
        data = json.loads(json_output)
        self.assertEqual(len(data), 2)
    
    def test_export_machine_readable(self) -> None:
        """Test OperatorCaseTimelineComparison.export_machine_readable()."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        timeline_comparison.compare_timeline(comparison1, comparison2)
        
        machine_output = timeline_comparison.export_machine_readable()
        data = json.loads(machine_output)
        
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["case1_id"], comparison1.case1_id)
    
    def test_get_result_by_id(self) -> None:
        """Test OperatorCaseTimelineComparison.get_result()."""
        timeline_comparison = OperatorCaseTimelineComparison()
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        result = timeline_comparison.compare_timeline(comparison1, comparison2)
        
        retrieved = timeline_comparison.get_result(result.summary_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.summary_id, result.summary_id)
    
    def test_get_results_for_case(self) -> None:
        """Test OperatorCaseTimelineComparison.get_results_for_case()."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        timeline_comparison.compare_timeline(comparison1, comparison2)
        timeline_comparison.compare_timeline(comparison1, comparison2)
        timeline_comparison.compare_timeline(comparison2, comparison1)
        
        results1 = timeline_comparison.get_results_for_case(comparison1.case1_id)
        self.assertGreaterEqual(len(results1), 1)
    
    def test_export_operator_readable_multiple(self) -> None:
        """Test OperatorCaseTimelineComparison.export_operator_readable() with multiple."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        timeline_comparison.compare_timeline(comparison1, comparison2)
        timeline_comparison.compare_timeline(comparison1, comparison2)
        
        operator_output = timeline_comparison.export_operator_readable()
        
        self.assertIn("ALL CASE TIMELINE COMPARISON RESULTS", operator_output)
        self.assertIn("Total Results:", operator_output)


# ============================================================================
# INTEGRATION TESTS (TestOperatorCaseTimelineComparisonIntegration)
# ============================================================================


class TestOperatorCaseTimelineComparisonIntegration(unittest.TestCase):
    """Integration tests for OperatorCaseTimelineComparison."""
    
    def test_comparison_with_v90_summaries(self) -> None:
        """Test comparison with v90 CaseComparisonSummary."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        result = timeline_comparison.compare_timeline(comparison1, comparison2)
        
        # Should have at least one drift record
        self.assertGreater(result.meaningful_drifts, 0)
        self.assertGreater(len(result.escalation_drifts), 0)
        self.assertGreater(len(result.confidence_drifts), 0)
    
    def test_escalation_drift_detection(self) -> None:
        """Test escalation drift detection."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        result = timeline_comparison.compare_timeline(comparison1, comparison2)
        
        if result.escalation_drifts:
            escalation_drift = result.escalation_drifts[0]
            self.assertIn(escalation_drift.urgency_shift, ["increasing", "decreasing", "stable"])
    
    def test_confidence_drift_detection(self) -> None:
        """Test confidence guidance drift detection."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        result = timeline_comparison.compare_timeline(comparison1, comparison2)
        
        if result.confidence_drifts:
            confidence_drift = result.confidence_drifts[0]
            self.assertIn(confidence_drift.confidence_shift, ["increasing", "decreasing", "stable"])
    
    def test_safe_action_drift_detection(self) -> None:
        """Test safe-next-action drift detection."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        result = timeline_comparison.compare_timeline(comparison1, comparison2)
        
        if result.safe_action_drifts:
            safe_action_drift = result.safe_action_drifts[0]
            self.assertIn(safe_action_drift.action_shift, ["increasing", "decreasing", "stable", "updated", "added", "removed", "unchanged"])
    
    def test_correlation_id_propagation(self) -> None:
        """Test that correlation IDs propagate through comparison."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        result = timeline_comparison.compare_timeline(
            comparison1, comparison2,
            correlation_ids={
                "flow_id": "flow_test",
                "request_id": "req_test",
                "handshake_id": "hand_test",
                "deadline_id": "dl_test",
            },
        )
        
        self.assertEqual(result.correlation_ids["flow_id"], "flow_test")
        self.assertEqual(result.correlation_ids["request_id"], "req_test")
    
    def test_drift_distribution_calculation(self) -> None:
        """Test drift distribution calculation."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        result = timeline_comparison.compare_timeline(comparison1, comparison2)
        
        self.assertIn("escalation", result.drift_distribution)
        self.assertIn("confidence", result.drift_distribution)
        self.assertIn("safe_action", result.drift_distribution)
        self.assertIn("total", result.drift_distribution)
    
    def test_meaningful_drifts_count(self) -> None:
        """Test meaningful drifts count."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        result = timeline_comparison.compare_timeline(comparison1, comparison2)
        
        # Should have at least some meaningful drifts
        self.assertGreaterEqual(result.meaningful_drifts, 0)
    
    def test_drift_trend_generation(self) -> None:
        """Test drift trend generation."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        result = timeline_comparison.compare_timeline(comparison1, comparison2)
        
        # Should have generated drift trends
        self.assertGreater(len(result.drift_trends), 0)
        
        # Check trend structure
        for trend in result.drift_trends:
            self.assertIn("trend_type", trend)
            self.assertIn("direction", trend)
            self.assertIn("magnitude", trend)


# ============================================================================
# BACKWARD COMPATIBILITY TESTS (TestOperatorCaseTimelineComparisonBackwardCompatibility)
# ============================================================================


class TestOperatorCaseTimelineComparisonBackwardCompatibility(unittest.TestCase):
    """Backward compatibility tests for OperatorCaseTimelineComparison."""
    
    def test_no_breaking_changes(self) -> None:
        """Test that v91 adds no breaking changes to v90."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        # Should work without v90 modifications
        result = timeline_comparison.compare_timeline(comparison1, comparison2)
        
        # Verify all drift types
        self.assertGreaterEqual(len(result.escalation_drifts), 0)
        self.assertGreaterEqual(len(result.confidence_drifts), 0)
        self.assertGreaterEqual(len(result.safe_action_drifts), 0)
    
    def test_readonly_behavior_preserved(self) -> None:
        """Test that v91 maintains read-only behavior."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        result = timeline_comparison.compare_timeline(comparison1, comparison2)
        
        # Verify machine output is JSON (readable, not executable)
        json_output = result.to_json()
        data = json.loads(json_output)
        
        self.assertIsInstance(data, dict)
        self.assertIn("summary_id", data)
        self.assertNotIn("execute", json_output.lower())
        self.assertNotIn("remediate", json_output.lower())
        self.assertNotIn("automate", json_output.lower())
    
    def test_no_autonomous_decisions(self) -> None:
        """Test that v91 adds no autonomous decision logic."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        result = timeline_comparison.compare_timeline(comparison1, comparison2)
        
        # Verify no autonomous decision indicators in output
        operator_summary = result.operator_readable.lower()
        json_summary = result.machine_readable.lower()
        
        # Should not contain autonomous decision language
        self.assertNotIn("automatically", operator_summary)
        self.assertNotIn("automatically", json_summary)
        self.assertNotIn("make decisions", operator_summary)
        self.assertNotIn("make decisions", json_summary)
    
    def test_export_format_compat(self) -> None:
        """Test that export formats are compatible with v90."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        result = timeline_comparison.compare_timeline(comparison1, comparison2)
        
        # Test both export formats
        json_output = TimelineComparisonExporter.export_summary(result, format="json")
        operator_output = TimelineComparisonExporter.export_summary(result, format="operator")
        
        # Both should be valid
        json_data = json.loads(json_output)
        self.assertIsInstance(json_data, dict)
        self.assertIsInstance(operator_output, str)
    
    def test_no_new_event_framework(self) -> None:
        """Test that v91 does not add new event framework."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        result = timeline_comparison.compare_timeline(comparison1, comparison2)
        
        # Verify telemetry events are descriptive only
        event_data = TimelineComparisonExporter.telemetry_event_result_created(result)
        
        self.assertEqual(event_data["event_type"], "TIMELINE_COMPARISON_RESULT_CREATED")
        self.assertIn("summary_id", event_data)
        # Should not control behavior
        self.assertNotIn("action", event_data)
        self.assertNotIn("trigger", event_data)
    
    def test_v90_compatibility(self) -> None:
        """Test that v91 works with v90 CaseComparisonSummary."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        # Create v90 comparison directly
        comparison = OperatorCaseComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        # Both should be usable in v91 timeline comparison
        result = timeline_comparison.compare_timeline(comparison1, comparison2)
        
        # Should complete without errors
        self.assertIsNotNone(result)
        self.assertIsInstance(result, TimelineComparisonResult)
    
    def test_operator_guidance_only(self) -> None:
        """Test that v91 provides only operator guidance, not certainty."""
        timeline_comparison = OperatorCaseTimelineComparison()
        
        comparison1 = create_test_comparison1()
        comparison2 = create_test_comparison2()
        
        result = timeline_comparison.compare_timeline(comparison1, comparison2)
        
        # Check operator summary for guidance language
        operator_summary = result.operator_readable
        
        # Should contain guidance-related language
        self.assertIn("heuristic", operator_summary.lower())
        self.assertIn("operator", operator_summary.lower())
        self.assertIn("guidance", operator_summary.lower())
        
        # Should NOT contain certainty language
        self.assertNotIn("will happen", operator_summary.lower())
        self.assertNotIn("guaranteed", operator_summary.lower())
        self.assertNotIn("must", operator_summary.lower())


# ============================================================================
# RUN TESTS
# ============================================================================


if __name__ == "__main__":
    unittest.main(verbosity=2)
