# test_operator_case_comparison.py - WESLR v90: Operator Case Comparison / Escalation Summary Layer Tests
# Tests for v90 Operator Case Comparison / Escalation Summary Layer.
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
from weslr.operator_insight_consolidation import (
    ConsolidatedCaseSummary,
    ConsolidatedCaseExporter,
    DecisionTraceSummary,
    DriftSummary,
    EscalationSummary,
    OperatorInsightConsolidation,
    PatternHistorySummary,
    RecoveryGuidanceSummary,
)


# ============================================================================
# TEST DATA HELPERS
# ============================================================================


def create_test_case1() -> ConsolidatedCaseSummary:
    """Create test consolidated case summary (case1 - lower urgency)."""
    consolidation = OperatorInsightConsolidation()
    
    guidance = [
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
    
    escalation = [
        EscalationSummary(
            escalation_id="escalation_001",
            time_window="24h",
            escalation_events=[{"event": "signal_1"}],
            urgency_level="normal",
            urgency_reason="Standard escalation context",
            operator_guidance=None,
        ),
    ]
    
    summary = consolidation.consolidate_case(
        case_id="case1",
        recovery_service=None,
        decision_trace=None,
        pattern_history=None,
        insight_comparison=None,
        insight_timeline=None,
        correlation_ids={"flow_id": "flow_001", "request_id": "req_001"},
    )
    
    # Manually override with our data
    summary.recovery_guidance = guidance
    summary.escalation_context = escalation
    summary.operator_readable = "Operator summary case1"
    summary.machine_readable = json.dumps({"case_id": "case1"})
    
    return summary


def create_test_case2() -> ConsolidatedCaseSummary:
    """Create test consolidated case summary (case2 - higher urgency)."""
    consolidation = OperatorInsightConsolidation()
    
    guidance = [
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
    
    escalation = [
        EscalationSummary(
            escalation_id="escalation_002",
            time_window="24h",
            escalation_events=[{"event": "signal_1"}, {"event": "signal_2"}, {"event": "signal_3"}],
            urgency_level="attention",
            urgency_reason="Attention signals detected",
            operator_guidance="Review escalation context",
        ),
    ]
    
    summary = consolidation.consolidate_case(
        case_id="case2",
        recovery_service=None,
        decision_trace=None,
        pattern_history=None,
        insight_comparison=None,
        insight_timeline=None,
        correlation_ids={"flow_id": "flow_002", "request_id": "req_002"},
    )
    
    # Manually override with our data
    summary.recovery_guidance = guidance
    summary.escalation_context = escalation
    summary.operator_readable = "Operator summary case2"
    summary.machine_readable = json.dumps({"case_id": "case2"})
    
    return summary


# ============================================================================
# MODEL TESTS (TestOperatorCaseComparisonModel)
# ============================================================================


class TestCaseComparisonModel(unittest.TestCase):
    """Model tests for CaseComparisonSummary."""
    
    def test_creation(self) -> None:
        """Test CaseComparisonSummary creation."""
        summary = CaseComparisonSummary(
            summary_id="summary_001",
            timestamp="2026-04-08T12:00:00Z",
            case1_id="case1",
            case2_id="case2",
            escalation_differences=[],
            confidence_differences=[],
            safe_action_differences=[],
            notable_differences=[],
            correlation_ids={},
            operator_readable="",
            machine_readable="{}",
        )
        
        self.assertEqual(summary.summary_id, "summary_001")
        self.assertEqual(summary.case1_id, "case1")
        self.assertEqual(summary.case2_id, "case2")
    
    def test_to_dict(self) -> None:
        """Test CaseComparisonSummary.to_dict()."""
        summary = CaseComparisonSummary(
            summary_id="summary_002",
            timestamp="2026-04-08T12:00:00Z",
            case1_id="case1",
            case2_id="case2",
            escalation_differences=[],
            confidence_differences=[],
            safe_action_differences=[],
            notable_differences=["Test change"],
            correlation_ids={"flow_id": "flow_002"},
            operator_readable="Operator summary",
            machine_readable="{}",
        )
        
        data = summary.to_dict()
        
        self.assertEqual(data["summary_id"], "summary_002")
        self.assertEqual(data["case1_id"], "case1")
        self.assertEqual(data["notable_differences"], ["Test change"])
    
    def test_to_json(self) -> None:
        """Test CaseComparisonSummary.to_json()."""
        summary = CaseComparisonSummary(
            summary_id="summary_003",
            timestamp="2026-04-08T12:00:00Z",
            case1_id="case1",
            case2_id="case2",
            escalation_differences=[],
            confidence_differences=[],
            safe_action_differences=[],
            notable_differences=[],
            correlation_ids={},
            operator_readable="",
            machine_readable="{}",
        )
        
        json_str = summary.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["summary_id"], "summary_003")
        self.assertIsInstance(data, dict)
    
    def test_escalation_difference_model(self) -> None:
        """Test EscalationDifference model."""
        diff = EscalationDifference(
            difference_id="diff_001",
            case1_id="case1",
            case2_id="case2",
            timestamp="2026-04-08T12:00:00Z",
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
        
        data = diff.to_dict()
        self.assertEqual(data["case1_urgency"], "normal")
        self.assertEqual(data["case2_urgency"], "attention")
    
    def test_confidence_difference_model(self) -> None:
        """Test ConfidenceDifference model."""
        diff = ConfidenceDifference(
            difference_id="diff_002",
            case1_id="case1",
            case2_id="case2",
            timestamp="2026-04-08T12:00:00Z",
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
        
        data = diff.to_dict()
        self.assertEqual(data["case1_confidence"], "medium")
        self.assertEqual(data["case2_confidence"], "high")
    
    def test_safe_action_difference_model(self) -> None:
        """Test SafeActionDifference model."""
        diff = SafeActionDifference(
            difference_id="diff_003",
            case1_id="case1",
            case2_id="case2",
            timestamp="2026-04-08T12:00:00Z",
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
        
        data = diff.to_dict()
        self.assertEqual(data["case1_action"], "Review logs")
        self.assertEqual(data["case2_action"], "Monitor metrics")


# ============================================================================
# BEHAVIOR TESTS (TestOperatorCaseComparisonBehavior)
# ============================================================================


class TestCaseComparisonBehavior(unittest.TestCase):
    """Behavior tests for OperatorCaseComparison."""
    
    def test_comparison_creation(self) -> None:
        """Test case comparison creation."""
        comparison = OperatorCaseComparison()
        
        case1 = create_test_case1()
        case2 = create_test_case2()
        
        summary = comparison.compare_cases(case1, case2)
        
        self.assertEqual(summary.case1_id, "case1")
        self.assertEqual(summary.case2_id, "case2")
    
    def test_export_summary_operator_format(self) -> None:
        """Test CaseComparisonExporter.export_summary(operator format)."""
        comparison = OperatorCaseComparison()
        case1 = create_test_case1()
        case2 = create_test_case2()
        summary = comparison.compare_cases(case1, case2)
        
        operator_output = CaseComparisonExporter.export_summary(summary, format="operator")
        
        self.assertIsInstance(operator_output, str)
        self.assertIn("OPERATOR CASE COMPARISON SUMMARY", operator_output)
    
    def test_export_summary_json_format(self) -> None:
        """Test CaseComparisonExporter.export_summary(json format)."""
        comparison = OperatorCaseComparison()
        case1 = create_test_case1()
        case2 = create_test_case2()
        summary = comparison.compare_cases(case1, case2)
        
        json_output = CaseComparisonExporter.export_summary(summary, format="json")
        
        data = json.loads(json_output)
        self.assertEqual(data["summary_id"], summary.summary_id)
        self.assertEqual(data["case1_id"], "case1")
    
    def test_export_multiple_summaries(self) -> None:
        """Test CaseComparisonExporter.export_multiple()."""
        comparison = OperatorCaseComparison()
        
        case1 = create_test_case1()
        case2 = create_test_case2()
        
        comparison.compare_cases(case1, case2)
        comparison.compare_cases(case1, case2)
        
        summaries = comparison.get_summaries()
        json_output = CaseComparisonExporter.export_multiple(summaries, format="json")
        
        data = json.loads(json_output)
        self.assertEqual(len(data), 2)
    
    def test_export_machine_readable(self) -> None:
        """Test OperatorCaseComparison.export_machine_readable()."""
        comparison = OperatorCaseComparison()
        
        case1 = create_test_case1()
        case2 = create_test_case2()
        comparison.compare_cases(case1, case2)
        
        machine_output = comparison.export_machine_readable()
        data = json.loads(machine_output)
        
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["case1_id"], "case1")
    
    def test_get_summary_by_id(self) -> None:
        """Test OperatorCaseComparison.get_summary()."""
        comparison = OperatorCaseComparison()
        case1 = create_test_case1()
        case2 = create_test_case2()
        summary = comparison.compare_cases(case1, case2)
        
        retrieved = comparison.get_summary(summary.summary_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.summary_id, summary.summary_id)
    
    def test_get_summaries_for_case(self) -> None:
        """Test OperatorCaseComparison.get_summaries_for_case()."""
        comparison = OperatorCaseComparison()
        
        case1 = create_test_case1()
        case2 = create_test_case2()
        
        comparison.compare_cases(case1, case2)
        comparison.compare_cases(case1, case2)
        comparison.compare_cases(case2, case1)
        
        summaries1 = comparison.get_summaries_for_case("case1")
        self.assertEqual(len(summaries1), 3)
        
        summaries2 = comparison.get_summaries_for_case("case2")
        self.assertEqual(len(summaries2), 3)
    
    def test_export_operator_readable_multiple(self) -> None:
        """Test OperatorCaseComparison.export_operator_readable() with multiple."""
        comparison = OperatorCaseComparison()
        
        case1 = create_test_case1()
        case2 = create_test_case2()
        
        comparison.compare_cases(case1, case2)
        comparison.compare_cases(case1, case2)
        
        operator_output = comparison.export_operator_readable()
        
        self.assertIn("ALL CASE COMPARISON SUMMARIES", operator_output)
        self.assertIn("Total Summaries: 2", operator_output)


# ============================================================================
# INTEGRATION TESTS (TestOperatorCaseComparisonIntegration)
# ============================================================================


class TestOperatorCaseComparisonIntegration(unittest.TestCase):
    """Integration tests for OperatorCaseComparison."""
    
    def test_comparison_with_v89_summaries(self) -> None:
        """Test comparison with v89 ConsolidatedCaseSummary."""
        comparison = OperatorCaseComparison()
        
        case1 = create_test_case1()
        case2 = create_test_case2()
        
        summary = comparison.compare_cases(case1, case2)
        
        self.assertEqual(len(summary.escalation_differences), 1)
        self.assertEqual(len(summary.confidence_differences), 1)
        self.assertEqual(len(summary.safe_action_differences), 1)
    
    def test_escalation_difference_detection(self) -> None:
        """Test escalation context difference detection."""
        comparison = OperatorCaseComparison()
        
        case1 = create_test_case1()
        case2 = create_test_case2()
        
        summary = comparison.compare_cases(case1, case2)
        
        escalation_diff = summary.escalation_differences[0]
        self.assertEqual(escalation_diff.urgency_shift, "increasing")
        self.assertEqual(escalation_diff.case1_urgency, "normal")
        self.assertEqual(escalation_diff.case2_urgency, "attention")
    
    def test_confidence_difference_detection(self) -> None:
        """Test confidence guidance difference detection."""
        comparison = OperatorCaseComparison()
        
        case1 = create_test_case1()
        case2 = create_test_case2()
        
        summary = comparison.compare_cases(case1, case2)
        
        confidence_diff = summary.confidence_differences[0]
        self.assertEqual(confidence_diff.confidence_shift, "increasing")
        self.assertEqual(confidence_diff.case1_confidence, "medium")
        self.assertEqual(confidence_diff.case2_confidence, "high")
    
    def test_safe_action_difference_detection(self) -> None:
        """Test safe-next-action difference detection."""
        comparison = OperatorCaseComparison()
        
        case1 = create_test_case1()
        case2 = create_test_case2()
        
        summary = comparison.compare_cases(case1, case2)
        
        safe_action_diff = summary.safe_action_differences[0]
        self.assertEqual(safe_action_diff.action_shift, "updated")
        self.assertIsNotNone(safe_action_diff.case1_action)
        self.assertIsNotNone(safe_action_diff.case2_action)
    
    def test_correlation_id_propagation(self) -> None:
        """Test that correlation IDs propagate through comparison."""
        comparison = OperatorCaseComparison()
        
        case1 = create_test_case1()
        case2 = create_test_case2()
        
        summary = comparison.compare_cases(
            case1, case2,
            correlation_ids={
                "flow_id": "flow_test",
                "request_id": "req_test",
                "handshake_id": "hand_test",
                "deadline_id": "dl_test",
            },
        )
        
        self.assertEqual(summary.correlation_ids["flow_id"], "flow_test")
        self.assertEqual(summary.correlation_ids["request_id"], "req_test")
    
    def test_notable_differences_identification(self) -> None:
        """Test notable differences identification."""
        comparison = OperatorCaseComparison()
        
        case1 = create_test_case1()
        case2 = create_test_case2()
        
        summary = comparison.compare_cases(case1, case2)
        
        # Should detect escalation difference
        notable = summary.notable_differences
        self.assertGreater(len(notable), 0)
        self.assertTrue(any("Escalation" in n for n in notable))


# ============================================================================
# BACKWARD COMPATIBILITY TESTS (TestOperatorCaseComparisonBackwardCompatibility)
# ============================================================================


class TestOperatorCaseComparisonBackwardCompatibility(unittest.TestCase):
    """Backward compatibility tests for OperatorCaseComparison."""
    
    def test_no_breaking_changes(self) -> None:
        """Test that v90 adds no breaking changes to v89."""
        comparison = OperatorCaseComparison()
        
        case1 = create_test_case1()
        case2 = create_test_case2()
        
        # Should work without v89 modifications
        summary = comparison.compare_cases(case1, case2)
        
        # Verify all comparison types
        self.assertEqual(len(summary.escalation_differences), 1)
        self.assertEqual(len(summary.confidence_differences), 1)
        self.assertEqual(len(summary.safe_action_differences), 1)
    
    def test_readonly_behavior_preserved(self) -> None:
        """Test that v90 maintains read-only behavior."""
        comparison = OperatorCaseComparison()
        
        case1 = create_test_case1()
        case2 = create_test_case2()
        
        summary = comparison.compare_cases(case1, case2)
        
        # Verify machine output is JSON (readable, not executable)
        json_output = summary.to_json()
        data = json.loads(json_output)
        
        self.assertIsInstance(data, dict)
        self.assertIn("summary_id", data)
        self.assertNotIn("execute", json_output.lower())
        self.assertNotIn("remediate", json_output.lower())
        self.assertNotIn("automate", json_output.lower())
    
    def test_no_autonomous_decisions(self) -> None:
        """Test that v90 adds no autonomous decision logic."""
        comparison = OperatorCaseComparison()
        
        case1 = create_test_case1()
        case2 = create_test_case2()
        
        summary = comparison.compare_cases(case1, case2)
        
        # Verify no autonomous decision indicators in output
        operator_summary = summary.operator_readable.lower()
        json_summary = summary.machine_readable.lower()
        
        # Should not contain autonomous decision language
        self.assertNotIn("automatically", operator_summary)
        self.assertNotIn("automatically", json_summary)
        self.assertNotIn("make decisions", operator_summary)
        self.assertNotIn("make decisions", json_summary)
    
    def test_export_format_compat(self) -> None:
        """Test that export formats are compatible with v89."""
        comparison = OperatorCaseComparison()
        
        case1 = create_test_case1()
        case2 = create_test_case2()
        
        summary = comparison.compare_cases(case1, case2)
        
        # Test both export formats
        json_output = CaseComparisonExporter.export_summary(summary, format="json")
        operator_output = CaseComparisonExporter.export_summary(summary, format="operator")
        
        # Both should be valid
        json_data = json.loads(json_output)
        self.assertIsInstance(json_data, dict)
        self.assertIsInstance(operator_output, str)
    
    def test_no_new_event_framework(self) -> None:
        """Test that v90 does not add new event framework."""
        comparison = OperatorCaseComparison()
        
        case1 = create_test_case1()
        case2 = create_test_case2()
        
        summary = comparison.compare_cases(case1, case2)
        
        # Verify telemetry events are descriptive only
        event_data = CaseComparisonExporter.telemetry_event_summary_created(summary)
        
        self.assertEqual(event_data["event_type"], "CASE_COMPARISON_SUMMARY_CREATED")
        self.assertIn("summary_id", event_data)
        # Should not control behavior
        self.assertNotIn("action", event_data)
        self.assertNotIn("trigger", event_data)


# ============================================================================
# RUN TESTS
# ============================================================================


if __name__ == "__main__":
    unittest.main(verbosity=2)
