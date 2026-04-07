# test_operator_insight_consolidation.py - WESLR v89: Operator Insight Consolidation Tests
# Tests for v89 Operator Insight Consolidation / Case Summary Layer.
# Read-only operator-facing layer tests only.
# No optimization, no remediation, no orchestration, no backend/service/UI.
# No TIA/C#, no storage framework expansion, no analytics engine beyond consolidation scope.

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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


def create_test_recovery_service() -> RecoveryRecommendationServiceMock:
    """Create mock v75 recovery recommendation service for testing."""
    service = RecoveryRecommendationServiceMock()
    
    # Add test recommendations
    service.add_recommendation(
        recommendation_id="rec_001",
        recommendation_type="suggestion",
        interpretation="System health issue detected",
        confidence_level="high",
        confidence_reason="Multiple correlated signals",
        confidence_guidance="Review system health, check logs",
        evidence_references=["log_entry_123", "metric_456"],
    )
    service.add_recommendation(
        recommendation_id="rec_002",
        recommendation_type="prediction",
        interpretation="Performance degradation likely",
        confidence_level="medium",
        confidence_reason="Trend pattern detected",
        confidence_guidance="Monitor performance metrics",
        evidence_references=["trend_789", "history_012"],
    )
    service.add_recommendation(
        recommendation_id="rec_003",
        recommendation_type="diagnostic",
        interpretation="Resource contention detected",
        confidence_level="low",
        confidence_reason="Single signal pattern",
        confidence_guidance=None,
        evidence_references=["signal_345"],
    )
    
    return service


def create_test_decision_trace() -> DecisionTraceSummaryMock:
    """Create mock v78 decision trace for testing."""
    trace = DecisionTraceSummaryMock()
    
    # Add test decision records
    trace.add_decision_record(
        trace_id="trace_001",
        decision_type="proposal",
        timestamp="2026-04-07T12:00:00Z",
        decision="approve",
        rationale="Recovered from previous error state",
        correlation_ids={"flow_id": "flow_001", "request_id": "req_001"},
    )
    trace.add_decision_record(
        trace_id="trace_002",
        decision_type="approval",
        timestamp="2026-04-07T12:05:00Z",
        decision="approve",
        rationale="Recommendation validated by operator",
        correlation_ids={"flow_id": "flow_001", "request_id": "req_001"},
    )
    
    return trace


def create_test_pattern_history() -> OperatorInsightHistoryMock:
    """Create mock v84 pattern history for testing."""
    history = OperatorInsightHistoryMock()
    
    # Add test pattern history records
    history.add_record(
        history_id="history_001",
        pattern_type="recommendation",
        pattern_id="pattern_001",
        trend_direction="increasing",
        trend_magnitude="moderate",
        heuristic_significance="high",
        heuristic_significance_reason="Significant trend change",
        correlation_ids={"flow_id": "flow_001", "request_id": "req_001"},
    )
    history.add_record(
        history_id="history_002",
        pattern_type="recovery_hint",
        pattern_id="pattern_002",
        trend_direction="stable",
        trend_magnitude="minor",
        heuristic_significance="medium",
        heuristic_significance_reason="Consistent pattern",
        correlation_ids={"flow_id": "flow_001", "request_id": "req_001"},
    )
    
    return history


def create_test_insight_comparison() -> OperatorInsightComparisonMock:
    """Create mock v87 insight comparison for testing."""
    comparison = OperatorInsightComparisonMock()
    
    # Add test drift records
    comparison.add_drift_record(
        drift_id="drift_001",
        comparison_type="significance",
        summary1_id="summary_old",
        summary2_id="summary_new",
        drift_type="increasing",
        drift_magnitude="significant",
        meaningful_drift=True,
        meaningful_drift_reason="Major insight shift",
        correlation_ids={"flow_id": "flow_001", "request_id": "req_001"},
    )
    comparison.add_drift_record(
        drift_id="drift_002",
        comparison_type="confidence",
        summary1_id="summary_old",
        summary2_id="summary_new",
        drift_type="stable",
        drift_magnitude="minor",
        meaningful_drift=False,
        meaningful_drift_reason="Minor confidence adjustment",
        correlation_ids={"flow_id": "flow_001", "request_id": "req_001"},
    )
    
    return comparison


def create_test_insight_timeline() -> OperatorInsightTimelineMock:
    """Create mock v88 insight timeline for testing."""
    timeline = OperatorInsightTimelineMock()
    
    # Add test escalation context
    timeline.add_entry(
        entry_id="timeline_001",
        timestamp="2026-04-07T11:00:00Z",
        insight_id="insight_001",
        drift_type="significance",
        before_value="low",
        after_value="high",
        significance_delta=0.5,
        confidence_delta=0.0,
        escalation_level="attention",
        escalation_reason="Significant insight change",
        correlation_ids={"flow_id": "flow_001", "request_id": "req_001"},
    )
    
    return timeline


# ============================================================================
# MOCK CLASSES (For Integration Testing)
# ============================================================================


class RecommendationMock:
    """Mock recommendation object with attributes."""
    
    def __init__(
        self,
        recommendation_id: str,
        recommendation_type: str,
        interpretation: str,
        confidence_level: str,
        confidence_reason: str,
        confidence_guidance: Optional[str],
        evidence_references: List[str],
    ):
        self.recommendation_id = recommendation_id
        self.recommendation_type = recommendation_type
        self.interpretation = interpretation
        self.confidence_level = confidence_level
        self.confidence_reason = confidence_reason
        self.confidence_guidance = confidence_guidance
        self.evidence_references = evidence_references


class RecoveryRecommendationServiceMock:
    """Mock v75 RecoveryRecommendationService for testing."""
    
    def __init__(self):
        """Initialize mock service."""
        self._recommendations: List[RecommendationMock] = []
    
    def add_recommendation(
        self,
        recommendation_id: str,
        recommendation_type: str,
        interpretation: str,
        confidence_level: str,
        confidence_reason: str,
        confidence_guidance: Optional[str],
        evidence_references: List[str],
    ) -> None:
        """Add a test recommendation."""
        self._recommendations.append(RecommendationMock(
            recommendation_id=recommendation_id,
            recommendation_type=recommendation_type,
            interpretation=interpretation,
            confidence_level=confidence_level,
            confidence_reason=confidence_reason,
            confidence_guidance=confidence_guidance,
            evidence_references=evidence_references,
        ))
    
    def get_recommendations(self) -> List[RecommendationMock]:
        """Get all recommendations."""
        return self._recommendations


class DecisionTraceSummaryMock:
    """Mock v78 RecoveryDecisionTrace for testing."""
    
    def __init__(self):
        """Initialize mock trace."""
        self._records: List[Dict[str, Any]] = []
    
    def add_decision_record(
        self,
        trace_id: str,
        decision_type: str,
        timestamp: str,
        decision: str,
        rationale: str,
        correlation_ids: Dict[str, str],
    ) -> None:
        """Add a test decision record."""
        self._records.append({
            "trace_id": trace_id,
            "decision_type": decision_type,
            "timestamp": timestamp,
            "decision": decision,
            "rationale": rationale,
            "correlation_ids": correlation_ids,
        })
    
    def get_records(self) -> List[Dict[str, Any]]:
        """Get all decision records."""
        return self._records


class OperatorInsightHistoryMock:
    """Mock v84 OperatorInsightHistory for testing."""
    
    def __init__(self):
        """Initialize mock history."""
        self._records: List[Dict[str, Any]] = []
    
    def add_record(
        self,
        history_id: str,
        pattern_type: str,
        pattern_id: str,
        trend_direction: str,
        trend_magnitude: str,
        heuristic_significance: str,
        heuristic_significance_reason: str,
        correlation_ids: Dict[str, str],
    ) -> None:
        """Add a test history record."""
        self._records.append({
            "history_id": history_id,
            "pattern_type": pattern_type,
            "pattern_id": pattern_id,
            "trend_direction": trend_direction,
            "trend_magnitude": trend_magnitude,
            "heuristic_significance": heuristic_significance,
            "heuristic_significance_reason": heuristic_significance_reason,
            "correlation_ids": correlation_ids,
        })
    
    def get_records(self) -> List[Dict[str, Any]]:
        """Get all history records."""
        return self._records


class OperatorInsightComparisonMock:
    """Mock v87 OperatorInsightComparison for testing."""
    
    def __init__(self):
        """Initialize mock comparison."""
        self._drift_records: List[Dict[str, Any]] = []
    
    def add_drift_record(
        self,
        drift_id: str,
        comparison_type: str,
        summary1_id: str,
        summary2_id: str,
        drift_type: str,
        drift_magnitude: str,
        meaningful_drift: bool,
        meaningful_drift_reason: str,
        correlation_ids: Dict[str, str],
    ) -> None:
        """Add a test drift record."""
        self._drift_records.append({
            "drift_id": drift_id,
            "comparison_type": comparison_type,
            "summary1_id": summary1_id,
            "summary2_id": summary2_id,
            "drift_type": drift_type,
            "drift_magnitude": drift_magnitude,
            "meaningful_drift": meaningful_drift,
            "meaningful_drift_reason": meaningful_drift_reason,
            "correlation_ids": correlation_ids,
        })
    
    def get_drift_records(self) -> List[Dict[str, Any]]:
        """Get all drift records."""
        return self._drift_records


class OperatorInsightTimelineMock:
    """Mock v88 OperatorInsightTimeline for testing."""
    
    def __init__(self):
        """Initialize mock timeline."""
        self._entries: List[Dict[str, Any]] = []
    
    def add_entry(
        self,
        entry_id: str,
        timestamp: str,
        insight_id: str,
        drift_type: str,
        before_value: Any,
        after_value: Any,
        significance_delta: float,
        confidence_delta: float,
        escalation_level: str,
        escalation_reason: str,
        correlation_ids: Dict[str, str],
    ) -> None:
        """Add a test timeline entry."""
        self._entries.append({
            "entry_id": entry_id,
            "timestamp": timestamp,
            "insight_id": insight_id,
            "drift_type": drift_type,
            "before_value": before_value,
            "after_value": after_value,
            "significance_delta": significance_delta,
            "confidence_delta": confidence_delta,
            "escalation_level": escalation_level,
            "escalation_reason": escalation_reason,
            "correlation_ids": correlation_ids,
        })
    
    def get_escalation_context(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get escalation context."""
        return self._entries
    
    def get_timeline(self) -> List[Dict[str, Any]]:
        """Get all entries."""
        return self._entries
    
    def get_escalation_summary(self) -> Dict[str, int]:
        """Get escalation summary."""
        summary = {"normal": 0, "attention": 0, "urgent": 0}
        for entry in self._entries:
            summary[entry["escalation_level"]] = summary.get(entry["escalation_level"], 0) + 1
        return summary


# ============================================================================
# MODEL TESTS (TestOperatorInsightConsolidationModel)
# ============================================================================


class TestConsolidatedCaseSummaryModel(unittest.TestCase):
    """Model tests for ConsolidatedCaseSummary."""
    
    def test_creation(self) -> None:
        """Test ConsolidatedCaseSummary creation."""
        summary = ConsolidatedCaseSummary(
            summary_id="summary_001",
            timestamp="2026-04-07T12:00:00Z",
            case_id="case_001",
            recovery_guidance=[],
            decision_trace=[],
            pattern_history=[],
            drift_analysis=[],
            escalation_context=[],
            notable_changes=[],
            correlation_ids={},
            operator_readable="",
            machine_readable="",
        )
        
        self.assertEqual(summary.summary_id, "summary_001")
        self.assertEqual(summary.case_id, "case_001")
        self.assertEqual(len(summary.recovery_guidance), 0)
        self.assertEqual(len(summary.decision_trace), 0)
    
    def test_to_dict(self) -> None:
        """Test ConsolidatedCaseSummary.to_dict()."""
        summary = ConsolidatedCaseSummary(
            summary_id="summary_002",
            timestamp="2026-04-07T12:00:00Z",
            case_id="case_002",
            recovery_guidance=[],
            decision_trace=[],
            pattern_history=[],
            drift_analysis=[],
            escalation_context=[],
            notable_changes=["Test change"],
            correlation_ids={"flow_id": "flow_002"},
            operator_readable="Operator summary",
            machine_readable="{}",
        )
        
        data = summary.to_dict()
        
        self.assertEqual(data["summary_id"], "summary_002")
        self.assertEqual(data["case_id"], "case_002")
        self.assertEqual(data["notable_changes"], ["Test change"])
        self.assertEqual(data["correlation_ids"], {"flow_id": "flow_002"})
    
    def test_to_json(self) -> None:
        """Test ConsolidatedCaseSummary.to_json()."""
        summary = ConsolidatedCaseSummary(
            summary_id="summary_003",
            timestamp="2026-04-07T12:00:00Z",
            case_id="case_003",
            recovery_guidance=[],
            decision_trace=[],
            pattern_history=[],
            drift_analysis=[],
            escalation_context=[],
            notable_changes=[],
            correlation_ids={},
            operator_readable="",
            machine_readable="",
        )
        
        json_str = summary.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["summary_id"], "summary_003")
        self.assertIsInstance(data, dict)
    
    def test_recovery_guidance_model(self) -> None:
        """Test RecoveryGuidanceSummary model."""
        guidance = RecoveryGuidanceSummary(
            guidance_id="guidance_001",
            recommendation_type="suggestion",
            interpretation="Test interpretation",
            confidence_level="high",
            confidence_reason="Test reason",
            safe_next_action="Review logs",
            evidence_references=["ref_1"],
        )
        
        data = guidance.to_dict()
        self.assertEqual(data["guidance_id"], "guidance_001")
        self.assertEqual(data["safe_next_action"], "Review logs")
    
    def test_decision_trace_model(self) -> None:
        """Test DecisionTraceSummary model."""
        trace = DecisionTraceSummary(
            trace_id="trace_001",
            decision_type="proposal",
            decisions=[{"decision": "approve"}],
            rationale="Test rationale",
            correlation_ids={"flow_id": "flow_001"},
        )
        
        data = trace.to_dict()
        self.assertEqual(data["trace_id"], "trace_001")
        self.assertEqual(data["decision_type"], "proposal")
    
    def test_pattern_history_model(self) -> None:
        """Test PatternHistorySummary model."""
        history = PatternHistorySummary(
            history_id="history_001",
            pattern_type="recommendation",
            patterns=[{"pattern": "test"}],
            trend_direction="increasing",
            trend_magnitude="moderate",
            heuristic_significance="high",
            heuristic_reason="Test reason",
        )
        
        data = history.to_dict()
        self.assertEqual(data["history_id"], "history_001")
        self.assertEqual(data["trend_direction"], "increasing")
    
    def test_drift_summary_model(self) -> None:
        """Test DriftSummary model."""
        drift = DriftSummary(
            drift_id="drift_001",
            comparison_type="significance",
            drift_changes=[{"change": "test"}],
            drift_magnitude="significant",
            interpretation="Test interpretation",
            heuristic_significance="medium",
            heuristic_reason="Test reason",
        )
        
        data = drift.to_dict()
        self.assertEqual(data["drift_id"], "drift_001")
        self.assertEqual(data["drift_magnitude"], "significant")
    
    def test_escalation_summary_model(self) -> None:
        """Test EscalationSummary model."""
        escalation = EscalationSummary(
            escalation_id="escalation_001",
            time_window="24h",
            escalation_events=[{"event": "test"}],
            urgency_level="attention",
            urgency_reason="Test reason",
            operator_guidance="Review attention items",
        )
        
        data = escalation.to_dict()
        self.assertEqual(data["escalation_id"], "escalation_001")
        self.assertEqual(data["urgency_level"], "attention")
        self.assertEqual(data["operator_guidance"], "Review attention items")


# ============================================================================
# BEHAVIOR TESTS (TestOperatorInsightConsolidationBehavior)
# ============================================================================


class TestConsolidatedCaseSummaryBehavior(unittest.TestCase):
    """Behavior tests for ConsolidatedCaseSummary."""
    
    def test_creation_from_all_sources(self) -> None:
        """Test consolidation from all insight sources."""
        consolidation = OperatorInsightConsolidation()
        
        service = create_test_recovery_service()
        trace = create_test_decision_trace()
        history = create_test_pattern_history()
        comparison = create_test_insight_comparison()
        timeline = create_test_insight_timeline()
        
        summary = consolidation.consolidate_case(
            case_id="case_behavior_001",
            recovery_service=service,
            decision_trace=trace,
            pattern_history=history,
            insight_comparison=comparison,
            insight_timeline=timeline,
            correlation_ids={"flow_id": "flow_behavior_001"},
        )
        
        self.assertEqual(summary.case_id, "case_behavior_001")
        self.assertEqual(len(summary.recovery_guidance), 3)
        self.assertEqual(len(summary.decision_trace), 2)
        self.assertEqual(len(summary.pattern_history), 2)
        self.assertEqual(len(summary.drift_analysis), 2)
        self.assertEqual(len(summary.escalation_context), 1)
        self.assertEqual(len(summary.notable_changes), 3)
    
    def test_export_summary_operator_format(self) -> None:
        """Test ConsolidatedCaseExporter.export_summary(operator format)."""
        consolidation = OperatorInsightConsolidation()
        summary = consolidation.consolidate_case(case_id="export_test_001")
        
        operator_output = ConsolidatedCaseExporter.export_summary(summary, format="operator")
        
        self.assertIsInstance(operator_output, str)
        self.assertIn("OPERATOR CONSOLIDATED CASE SUMMARY", operator_output)
    
    def test_export_summary_json_format(self) -> None:
        """Test ConsolidatedCaseExporter.export_summary(json format)."""
        consolidation = OperatorInsightConsolidation()
        summary = consolidation.consolidate_case(case_id="export_test_002")
        
        json_output = ConsolidatedCaseExporter.export_summary(summary, format="json")
        
        data = json.loads(json_output)
        self.assertEqual(data["summary_id"], summary.summary_id)
        self.assertEqual(data["case_id"], "export_test_002")
    
    def test_export_multiple_summaries(self) -> None:
        """Test ConsolidatedCaseExporter.export_multiple()."""
        consolidation = OperatorInsightConsolidation()
        
        consolidation.consolidate_case(case_id="export_multi_001")
        consolidation.consolidate_case(case_id="export_multi_002")
        consolidation.consolidate_case(case_id="export_multi_003")
        
        summaries = consolidation.get_summaries()
        json_output = ConsolidatedCaseExporter.export_multiple(summaries, format="json")
        
        data = json.loads(json_output)
        self.assertEqual(len(data), 3)
    
    def test_export_machine_readable(self) -> None:
        """Test OperatorInsightConsolidation.export_machine_readable()."""
        consolidation = OperatorInsightConsolidation()
        
        consolidation.consolidate_case(case_id="machine_test_001")
        
        machine_output = consolidation.export_machine_readable()
        data = json.loads(machine_output)
        
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["case_id"], "machine_test_001")
    
    def test_get_summary_by_id(self) -> None:
        """Test OperatorInsightConsolidation.get_summary()."""
        consolidation = OperatorInsightConsolidation()
        summary = consolidation.consolidate_case(case_id="get_test_001")
        
        retrieved = consolidation.get_summary(summary.summary_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.summary_id, summary.summary_id)
    
    def test_get_summaries_for_case(self) -> None:
        """Test OperatorInsightConsolidation.get_summaries_for_case()."""
        consolidation = OperatorInsightConsolidation()
        
        consolidation.consolidate_case(case_id="case_filter_001")
        consolidation.consolidate_case(case_id="case_filter_001")
        consolidation.consolidate_case(case_id="case_filter_002")
        
        summaries = consolidation.get_summaries_for_case("case_filter_001")
        self.assertEqual(len(summaries), 2)
    
    def test_export_operator_readable_multiple(self) -> None:
        """Test OperatorInsightConsolidation.export_operator_readable() with multiple."""
        consolidation = OperatorInsightConsolidation()
        
        consolidation.consolidate_case(case_id="multi_export_001")
        consolidation.consolidate_case(case_id="multi_export_002")
        
        operator_output = consolidation.export_operator_readable()
        
        self.assertIn("ALL CONSOLIDATED CASE SUMMARIES", operator_output)
        self.assertIn("Total Summaries: 2", operator_output)


# ============================================================================
# INTEGRATION TESTS (TestOperatorInsightConsolidationIntegration)
# ============================================================================


class TestOperatorInsightConsolidationIntegration(unittest.TestCase):
    """Integration tests for OperatorInsightConsolidation."""
    
    def test_integration_with_v75_service(self) -> None:
        """Test integration with v75 RecoveryRecommendationService."""
        consolidation = OperatorInsightConsolidation()
        service = create_test_recovery_service()
        
        summary = consolidation.consolidate_case(
            case_id="integ_v75_001",
            recovery_service=service,
        )
        
        self.assertEqual(len(summary.recovery_guidance), 3)
    
    def test_integration_with_v78_trace(self) -> None:
        """Test integration with v78 RecoveryDecisionTrace."""
        consolidation = OperatorInsightConsolidation()
        trace = DecisionTraceSummaryMock()
        trace.add_decision_record(
            trace_id="trace_001",
            decision_type="proposal",
            timestamp="2026-04-07T12:00:00Z",
            decision="approve",
            rationale="Test rationale",
            correlation_ids={"flow_id": "flow_001"},
        )
        
        summary = consolidation.consolidate_case(
            case_id="integ_v78_001",
            decision_trace=trace,
        )
        
        self.assertEqual(len(summary.decision_trace), 1)
    
    def test_integration_with_v84_history(self) -> None:
        """Test integration with v84 OperatorInsightHistory."""
        consolidation = OperatorInsightConsolidation()
        history = create_test_pattern_history()
        
        summary = consolidation.consolidate_case(
            case_id="integ_v84_001",
            pattern_history=history,
        )
        
        self.assertEqual(len(summary.pattern_history), 2)
    
    def test_integration_with_v87_comparison(self) -> None:
        """Test integration with v87 OperatorInsightComparison."""
        consolidation = OperatorInsightConsolidation()
        comparison = create_test_insight_comparison()
        
        summary = consolidation.consolidate_case(
            case_id="integ_v87_001",
            insight_comparison=comparison,
        )
        
        self.assertEqual(len(summary.drift_analysis), 2)
    
    def test_integration_with_v88_timeline(self) -> None:
        """Test integration with v88 OperatorInsightTimeline."""
        consolidation = OperatorInsightConsolidation()
        timeline = create_test_insight_timeline()
        
        summary = consolidation.consolidate_case(
            case_id="integ_v88_001",
            insight_timeline=timeline,
        )
        
        self.assertEqual(len(summary.escalation_context), 1)
    
    def test_full_integration_with_all_layers(self) -> None:
        """Test full integration with v75, v78, v84, v87, v88."""
        consolidation = OperatorInsightConsolidation()
        
        service = create_test_recovery_service()
        trace = create_test_decision_trace()
        history = create_test_pattern_history()
        comparison = create_test_insight_comparison()
        timeline = create_test_insight_timeline()
        
        summary = consolidation.consolidate_case(
            case_id="integ_full_001",
            recovery_service=service,
            decision_trace=trace,
            pattern_history=history,
            insight_comparison=comparison,
            insight_timeline=timeline,
            correlation_ids={
                "flow_id": "flow_full",
                "request_id": "req_full",
                "handshake_id": "hand_full",
                "deadline_id": "dl_full",
            },
        )
        
        # Verify all integrations
        self.assertEqual(len(summary.recovery_guidance), 3)
        self.assertEqual(len(summary.decision_trace), 2)
        self.assertEqual(len(summary.pattern_history), 2)
        self.assertEqual(len(summary.drift_analysis), 2)
        self.assertEqual(len(summary.escalation_context), 1)
        self.assertIn("flow_full", summary.correlation_ids.values())
    
    def test_correlation_id_propagation(self) -> None:
        """Test that correlation IDs propagate through consolidation."""
        consolidation = OperatorInsightConsolidation()
        
        summary = consolidation.consolidate_case(
            case_id="corr_id_test_001",
            correlation_ids={
                "flow_id": "flow_test",
                "request_id": "req_test",
                "handshake_id": "hand_test",
                "deadline_id": "dl_test",
            },
        )
        
        self.assertEqual(summary.correlation_ids["flow_id"], "flow_test")
        self.assertEqual(summary.correlation_ids["request_id"], "req_test")
        self.assertEqual(summary.correlation_ids["handshake_id"], "hand_test")
        self.assertEqual(summary.correlation_ids["deadline_id"], "dl_test")


# ============================================================================
# BACKWARD COMPATIBILITY TESTS (TestOperatorInsightConsolidationBackwardCompatibility)
# ============================================================================


class TestOperatorInsightConsolidationBackwardCompatibility(unittest.TestCase):
    """Backward compatibility tests for OperatorInsightConsolidation."""
    
    def test_no_breaking_changes(self) -> None:
        """Test that v89 adds no breaking changes to existing layers."""
        consolidation = OperatorInsightConsolidation()
        
        # v75
        service = create_test_recovery_service()
        summary1 = consolidation.consolidate_case(case_id="compat_v75_001", recovery_service=service)
        
        # v78
        trace = create_test_decision_trace()
        summary2 = consolidation.consolidate_case(case_id="compat_v78_001", decision_trace=trace)
        
        # v84
        history = create_test_pattern_history()
        summary3 = consolidation.consolidate_case(case_id="compat_v84_001", pattern_history=history)
        
        # v87
        comparison = create_test_insight_comparison()
        summary4 = consolidation.consolidate_case(case_id="compat_v87_001", insight_comparison=comparison)
        
        # v88
        timeline = create_test_insight_timeline()
        summary5 = consolidation.consolidate_case(case_id="compat_v88_001", insight_timeline=timeline)
        
        # All summaries should be created without errors
        self.assertEqual(len(consolidation.get_summaries()), 5)
    
    def test_readonly_behavior_preserved(self) -> None:
        """Test that v89 maintains read-only behavior."""
        consolidation = OperatorInsightConsolidation()
        
        # Create summary
        summary = consolidation.consolidate_case(case_id="readonly_test_001")
        
        # Verify machine output is JSON (readable, not executable)
        json_output = summary.to_json()
        data = json.loads(json_output)
        
        self.assertIsInstance(data, dict)
        self.assertIn("summary_id", data)
        self.assertNotIn("execute", json_output.lower())
        self.assertNotIn("remediate", json_output.lower())
        self.assertNotIn("automate", json_output.lower())
    
    def test_no_autonomous_decisions(self) -> None:
        """Test that v89 adds no autonomous decision logic."""
        consolidation = OperatorInsightConsolidation()
        
        service = create_test_recovery_service()
        summary = consolidation.consolidate_case(
            case_id="auto_test_001",
            recovery_service=service,
        )
        
        # Verify no autonomous decision indicators in output
        operator_summary = summary.operator_readable.lower()
        json_summary = summary.machine_readable.lower()
        
        # Should not contain autonomous decision language
        self.assertNotIn("automatically", operator_summary)
        self.assertNotIn("automatically", json_summary)
        self.assertNotIn("make decisions", operator_summary)
        self.assertNotIn("make decisions", json_summary)
    
    def test_confidence_as_guidance_not_certainty(self) -> None:
        """Test that confidence is presented as guidance, not certainty."""
        consolidation = OperatorInsightConsolidation()
        service = create_test_recovery_service()
        
        summary = consolidation.consolidate_case(
            case_id="confidence_test_001",
            recovery_service=service,
        )
        
        # Verify guidance language in operator summary
        operator_summary = summary.operator_readable
        
        # Should contain "guidance" or "not certainty" indicators
        self.assertIn("guidance", operator_summary.lower())
        self.assertIn("not certainties", operator_summary.lower())
        self.assertIn("not automatic", operator_summary.lower())
    
    def test_export_format_compat(self) -> None:
        """Test that export formats are compatible with v76-v88."""
        consolidation = OperatorInsightConsolidation()
        
        service = create_test_recovery_service()
        summary = consolidation.consolidate_case(
            case_id="export_compat_001",
            recovery_service=service,
        )
        
        # Test both export formats
        json_output = ConsolidatedCaseExporter.export_summary(summary, format="json")
        operator_output = ConsolidatedCaseExporter.export_summary(summary, format="operator")
        
        # Both should be valid
        json_data = json.loads(json_output)
        self.assertIsInstance(json_data, dict)
        self.assertIsInstance(operator_output, str)
    
    def test_no_new_event_framework(self) -> None:
        """Test that v89 does not add new event framework."""
        consolidation = OperatorInsightConsolidation()
        summary = consolidation.consolidate_case(case_id="event_test_001")
        
        # Verify telemetry events are descriptive only
        event_data = ConsolidatedCaseExporter.telemetry_event_summary_created(summary)
        
        self.assertEqual(event_data["event_type"], "CONSOLIDATED_CASE_SUMMARY_CREATED")
        self.assertIn("summary_id", event_data)
        # Should not control behavior
        self.assertNotIn("action", event_data)
        self.assertNotIn("trigger", event_data)


# ============================================================================
# RUN TESTS
# ============================================================================


if __name__ == "__main__":
    unittest.main(verbosity=2)
