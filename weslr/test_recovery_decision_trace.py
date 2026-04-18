"""Test suite for v78 Operator Decision Trace + Correlated Recommendation Export.

Tests:
  - DecisionTraceRecord basic behavior and serialization
  - Correlation by flow_id, request_id, handshake_id, deadline_id
  - Rationale trace generation
  - Confidence guidance trace (operator guidance, not certainty)
  - Safe-next-action trace
  - Integration with v76/v77 layers
  - Decision trace summary generation
  - Machine-readable export
"""

from __future__ import annotations

import json
import unittest

from weslr.recovery_decision_trace import (
    DecisionTraceExporter,
    DecisionTraceRecord,
    DecisionTraceSummary,
    integrate_with_v76_exporter,
    integrate_with_v77_review_surface,
)
from weslr.recovery_recommendation_review import RecoveryRecommendationReviewSurface
from weslr.distributed_diagnostic_hooks import (
    FailureClassification,
    FailureStage,
    FailureType,
)


class MockDiagnosticHooks:
    """Mock v70 diagnostic hooks for testing."""
    
    def __init__(self):
        self._classifications: Dict[str, Dict[str, Any]] = {}
    
    def get_failure_classification(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Mock failure classification lookup."""
        return self._classifications.get(flow_id)
    
    def add_classification(self, flow_id: str, classification: Dict[str, Any]):
        """Add a mock classification."""
        self._classifications[flow_id] = classification


class MockRecoveryRecommendationExporter:
    """Mock v76 exporter for integration testing."""
    
    def __init__(self):
        self._records: List[Dict[str, Any]] = []
    
    def add_record(self, record: Dict[str, Any]):
        self._records.append(record)
    
    def export_machine_readable(self) -> List[Dict[str, Any]]:
        return self._records.copy()


# ============================================================================
# TEST DECISION TRACE RECORD
# ============================================================================


class TestDecisionTraceRecord(unittest.TestCase):
    """Test DecisionTraceRecord basic behavior."""
    
    def test_creation_and_serialization(self):
        """Test record creation and JSON serialization."""
        record = DecisionTraceRecord(
            trace_id="trace_12345678",
            recommendation_id="recovery_1",
            timestamp="2026-04-07T10:00:00Z",
            correlation_ids={"flow_id": "flow_abc", "request_id": "req_xyz"},
            rationale="Test rationale",
            confidence_level="medium",
            confidence_explanation="Test explanation",
            safe_next_action={
                "recommended_action": "Test action",
                "risk_level": "medium",
                "required_verification": ["Verify test"],
                "fallback_options": ["Fallback option"],
            },
        )
        
        # Test to_dict
        data = record.to_dict()
        self.assertEqual(data["trace_id"], "trace_12345678")
        self.assertEqual(data["recommendation_id"], "recovery_1")
        self.assertEqual(data["rationale"], "Test rationale")
        self.assertEqual(data["confidence_level"], "medium")
        
        # Test to_json
        json_str = record.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["trace_id"], "trace_12345678")
    
    def test_from_dict_roundtrip(self):
        """Test from_dict/roundtrip preservation."""
        original = DecisionTraceRecord(
            trace_id="trace_12345678",
            recommendation_id="recovery_1",
            timestamp="2026-04-07T10:00:00Z",
            correlation_ids={"flow_id": "flow_abc"},
            rationale="Test",
            confidence_level="high",
            confidence_explanation="Explanation",
            safe_next_action={"recommended_action": "Action", "risk_level": "low", "required_verification": [], "fallback_options": []},
        )
        
        data = original.to_dict()
        restored = DecisionTraceRecord.from_dict(data)
        
        self.assertEqual(restored.trace_id, original.trace_id)
        self.assertEqual(restored.rationale, original.rationale)
        self.assertEqual(restored.confidence_level, original.confidence_level)
    
    def test_correlation_ids_preservation(self):
        """Test correlation IDs are preserved in all operations."""
        record = DecisionTraceRecord(
            trace_id="trace_12345678",
            recommendation_id="recovery_1",
            timestamp="2026-04-07T10:00:00Z",
            correlation_ids={
                "flow_id": "flow_abc",
                "request_id": "req_xyz",
                "handshake_id": "hs_def",
                "deadline_id": "dl_ghi",
            },
            rationale="Test",
            confidence_level="medium",
            confidence_explanation="Explanation",
            safe_next_action={
                "recommended_action": "Action",
                "risk_level": "low",
                "required_verification": [],
                "fallback_options": [],
            },
        )
        
        data = record.to_dict()
        self.assertEqual(data["correlation_ids"]["flow_id"], "flow_abc")
        self.assertEqual(data["correlation_ids"]["request_id"], "req_xyz")
        self.assertEqual(data["correlation_ids"]["handshake_id"], "hs_def")
        self.assertEqual(data["correlation_ids"]["deadline_id"], "dl_ghi")


# ============================================================================
# TEST DECISION TRACE EXPORTER
# ============================================================================


class TestDecisionTraceExporter(unittest.TestCase):
    """Test DecisionTraceExporter export behavior."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_hooks = MockDiagnosticHooks()
        self.exporter = DecisionTraceExporter(self.mock_hooks)
    
    def test_export_decision_trace_basic(self):
        """Test basic decision trace export."""
        recommendation = {
            "recommendation_id": "recovery_1",
            "stage": "proposal",
            "failure_type": "proposal_rejected",
            "likely_cause": "Proposal rejected",
            "recovery_hint": "Review criteria",
            "confidence": "medium",
            "correlation_ids": {"flow_id": "flow_abc"},
            "generated_at": "2026-04-07T10:00:00Z",
        }
        
        trace = self.exporter.export_decision_trace(recommendation)
        
        self.assertEqual(trace.recommendation_id, "recovery_1")
        self.assertEqual(trace.rationale, "Based on analysis of proposal_rejected at proposal stage: Proposal rejected")
        self.assertEqual(trace.confidence_level, "medium")
        self.assertIn("operator guidance", trace.confidence_explanation.lower())
    
    def test_export_with_failure_classification(self):
        """Test export with failure classification."""
        classification = FailureClassification(
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            stage=FailureStage.PROPOSAL.value,
            node_id="node_1",
            observed_error="Proposal was rejected by validation gates",
        )
        
        recommendation = {
            "recommendation_id": "recovery_1",
            "stage": "proposal",
            "failure_type": "proposal_rejected",
            "likely_cause": "Proposal rejected by validation gates",
            "recovery_hint": "Review rejection reason",
            "confidence": "high",
            "correlation_ids": {"flow_id": "flow_abc"},
            "generated_at": "2026-04-07T10:00:00Z",
        }
        
        trace = self.exporter.export_decision_trace(
            recommendation=recommendation,
            failure_classification=classification,
        )
        
        self.assertEqual(trace.failure_classification, classification)
        # Rationale includes likely_cause from recommendation when both exist
        self.assertIn("proposal rejected by validation gates", trace.rationale.lower())
    
    def test_export_with_review_surface(self):
        """Test export with v77 review surface."""
        review_surface = RecoveryRecommendationReviewSurface()
        recommendations = [
            {
                "recommendation_id": "recovery_1",
                "stage": "proposal",
                "failure_type": "proposal_rejected",
                "likely_cause": "Proposal rejected",
                "contributing_factors": [],
                "recovery_hint": "Review criteria",
                "confidence": "high",
                "hint_certainty": "suggestion",
                "correlation_ids": {"flow_id": "flow_abc"},
                "generated_at": "2026-04-07T10:00:00Z",
            },
        ]
        review_surface.load_recommendations(recommendations)
        
        recommendation = {
            "recommendation_id": "recovery_1",
            "correlation_ids": {"flow_id": "flow_abc"},
        }
        
        trace = self.exporter.export_decision_trace(
            recommendation=recommendation,
            review_surface=review_surface,
        )
        
        sna = trace.safe_next_action
        self.assertIn("recommended_action", sna)
        self.assertIn("risk_level", sna)
        self.assertEqual(sna["risk_level"], "low")  # High confidence = low risk
    
    def test_export_by_correlation_flow_id(self):
        """Test filtering by flow_id."""
        trace1 = self.exporter.export_decision_trace({
            "recommendation_id": "recovery_1",
            "correlation_ids": {"flow_id": "flow_abc"},
        })
        trace2 = self.exporter.export_decision_trace({
            "recommendation_id": "recovery_2",
            "correlation_ids": {"flow_id": "flow_abc"},
        })
        trace3 = self.exporter.export_decision_trace({
            "recommendation_id": "recovery_3",
            "correlation_ids": {"flow_id": "flow_xyz"},
        })
        
        filtered = self.exporter.export_by_correlation(flow_id="flow_abc")
        
        self.assertEqual(len(filtered), 2)
        rec_ids = [t.recommendation_id for t in filtered]
        self.assertIn("recovery_1", rec_ids)
        self.assertIn("recovery_2", rec_ids)
    
    def test_export_by_correlation_request_id(self):
        """Test filtering by request_id."""
        self.exporter.export_decision_trace({
            "recommendation_id": "recovery_1",
            "correlation_ids": {"flow_id": "flow_xyz", "request_id": "req_abc"},
        })
        trace2 = self.exporter.export_decision_trace({
            "recommendation_id": "recovery_2",
            "correlation_ids": {"flow_id": "flow_xyz", "request_id": "req_abc"},
        })
        self.exporter.export_decision_trace({
            "recommendation_id": "recovery_3",
            "correlation_ids": {"flow_id": "flow_abc", "request_id": "req_xyz"},
        })
        
        filtered = self.exporter.export_by_correlation(request_id="req_abc")
        
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].recommendation_id, "recovery_1")
        self.assertEqual(filtered[1].recommendation_id, "recovery_2")
    
    def test_export_by_correlation_handshake_id(self):
        """Test filtering by handshake_id."""
        trace = self.exporter.export_decision_trace({
            "recommendation_id": "recovery_1",
            "correlation_ids": {"handshake_id": "hs_abc"},
        })
        
        filtered = self.exporter.export_by_correlation(handshake_id="hs_abc")
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].recommendation_id, trace.recommendation_id)
    
    def test_export_by_correlation_deadline_id(self):
        """Test filtering by deadline_id."""
        trace = self.exporter.export_decision_trace({
            "recommendation_id": "recovery_1",
            "correlation_ids": {"deadline_id": "dl_abc"},
        })
        
        filtered = self.exporter.export_by_correlation(deadline_id="dl_abc")
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].recommendation_id, trace.recommendation_id)
    
    def test_export_operator_summary(self):
        """Test operator-readable summary generation."""
        self.exporter.export_decision_trace({
            "recommendation_id": "recovery_1",
            "stage": "proposal",
            "likely_cause": "Proposal rejected",
            "recovery_hint": "Review criteria",
            "confidence": "medium",
            "correlation_ids": {"flow_id": "flow_abc"},
        })
        
        summary = self.exporter.export_operator_summary()
        
        self.assertIn("=== OPERATOR DECISION TRACE SUMMARY ===", summary)
        self.assertIn("Total Decision Traces: 1", summary)
        self.assertIn("recovery_1", summary)
        self.assertIn("Proposal rejected", summary)
    
    def test_export_machine_readable(self):
        """Test machine-readable export."""
        self.exporter.export_decision_trace({
            "recommendation_id": "recovery_1",
            "correlation_ids": {},
        })
        
        records = self.exporter.export_machine_readable()
        
        self.assertEqual(len(records), 1)
        self.assertIn("trace_id", records[0])
        self.assertIn("rationale", records[0])
        self.assertIn("confidence_level", records[0])
        self.assertIn("safe_next_action", records[0])


# ============================================================================
# TEST DECISION TRACE SUMMARY
# ============================================================================


class TestDecisionTraceSummary(unittest.TestCase):
    """Test DecisionTraceSummary aggregation."""
    
    def test_empty_summary(self):
        """Test summary with no traces."""
        summary = DecisionTraceSummary()
        result = summary.build_summary()
        
        self.assertEqual(result["total_traces"], 0)
        self.assertEqual(result["confidence_distribution"], {})
        self.assertIsNone(result["most_common_cause"])
    
    def test_basic_summary_aggregation(self):
        """Test basic summary aggregation."""
        summary = DecisionTraceSummary()
        
        traces = [
            DecisionTraceRecord(
                trace_id="trace_1",
                recommendation_id="recovery_1",
                timestamp="2026-04-07T10:00:00Z",
                correlation_ids={"flow_id": "flow_abc"},
                rationale="Rationale 1",
                confidence_level="high",
                confidence_explanation="Explanation",
                safe_next_action={
                    "recommended_action": "Action 1",
                    "risk_level": "low",
                    "required_verification": [],
                    "fallback_options": [],
                },
                likely_cause="Cause A",
            ),
            DecisionTraceRecord(
                trace_id="trace_2",
                recommendation_id="recovery_2",
                timestamp="2026-04-07T10:01:00Z",
                correlation_ids={"flow_id": "flow_abc"},
                rationale="Rationale 2",
                confidence_level="medium",
                confidence_explanation="Explanation",
                safe_next_action={
                    "recommended_action": "Action 2",
                    "risk_level": "medium",
                    "required_verification": [],
                    "fallback_options": [],
                },
                likely_cause="Cause A",
            ),
        ]
        
        summary.add_traces(traces)
        result = summary.build_summary()
        
        self.assertEqual(result["total_traces"], 2)
        self.assertEqual(result["confidence_distribution"]["high"], 1)
        self.assertEqual(result["confidence_distribution"]["medium"], 1)
        self.assertEqual(result["most_common_cause"], "Cause A")
    
    def test_operator_summary(self):
        """Test operator-readable summary."""
        summary = DecisionTraceSummary()
        
        traces = [
            DecisionTraceRecord(
                trace_id="trace_1",
                recommendation_id="recovery_1",
                timestamp="2026-04-07T10:00:00Z",
                correlation_ids={"flow_id": "flow_abc"},
                rationale="Rationale",
                confidence_level="high",
                confidence_explanation="Explanation",
                safe_next_action={
                    "recommended_action": "Action",
                    "risk_level": "low",
                    "required_verification": [],
                    "fallback_options": [],
                },
            ),
        ]
        
        summary.add_traces(traces)
        result = summary.build_operator_summary()
        
        self.assertIn("=== OPERATOR DECISION TRACE SUMMARY ===", result)
        self.assertIn("Total Traces: 1", result)
        self.assertIn("high: 1", result)
        self.assertIn("Action", result)


# ============================================================================
# TEST DECISION TRACE CORRELATION
# ============================================================================


class TestDecisionTraceCorrelation(unittest.TestCase):
    """Test correlation filtering across all correlation IDs."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_hooks = MockDiagnosticHooks()
        self.exporter = DecisionTraceExporter(self.mock_hooks)
    
    def test_multiple_correlation_ids(self):
        """Test record with multiple correlation IDs."""
        trace = self.exporter.export_decision_trace({
            "recommendation_id": "recovery_1",
            "correlation_ids": {
                "flow_id": "flow_abc",
                "request_id": "req_xyz",
                "handshake_id": "hs_def",
                "deadline_id": "dl_ghi",
            },
        })
        
        # Filter by each ID type
        self.assertEqual(len(self.exporter.export_by_correlation(flow_id="flow_abc")), 1)
        self.assertEqual(len(self.exporter.export_by_correlation(request_id="req_xyz")), 1)
        self.assertEqual(len(self.exporter.export_by_correlation(handshake_id="hs_def")), 1)
        self.assertEqual(len(self.exporter.export_by_correlation(deadline_id="dl_ghi")), 1)
    
    def test_cross_id_correlation_filtering(self):
        """Test that filtering by one ID doesn't return others."""
        self.exporter.export_decision_trace({
            "recommendation_id": "recovery_1",
            "correlation_ids": {"flow_id": "flow_a", "request_id": "req_a"},
        })
        self.exporter.export_decision_trace({
            "recommendation_id": "recovery_2",
            "correlation_ids": {"flow_id": "flow_b", "request_id": "req_b"},
        })
        
        # Should only return flow_a records
        flow_a_records = self.exporter.export_by_correlation(flow_id="flow_a")
        self.assertEqual(len(flow_a_records), 1)
        self.assertEqual(flow_a_records[0].recommendation_id, "recovery_1")
    
    def test_no_filter_returns_all(self):
        """Test that no filter returns all traces."""
        self.exporter.export_decision_trace({"recommendation_id": "r1", "correlation_ids": {}})
        self.exporter.export_decision_trace({"recommendation_id": "r2", "correlation_ids": {}})
        self.exporter.export_decision_trace({"recommendation_id": "r3", "correlation_ids": {}})
        
        all_records = self.exporter.export_by_correlation()
        self.assertEqual(len(all_records), 3)


# ============================================================================
# TEST RATIONALE TRACE
# ============================================================================


class TestDecisionTraceRationale(unittest.TestCase):
    """Test rationale trace generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_hooks = MockDiagnosticHooks()
        self.exporter = DecisionTraceExporter(self.mock_hooks)
    
    def test_rationale_from_likely_cause(self):
        """Test rationale generation from likely cause."""
        recommendation = {
            "recommendation_id": "recovery_1",
            "stage": "handshake",
            "failure_type": "handshake_failed",
            "likely_cause": "Protocol mismatch",
            "recovery_hint": "Verify compatibility",
            "confidence": "high",
            "correlation_ids": {},
        }
        
        trace = self.exporter.export_decision_trace(recommendation)
        
        self.assertIn("handshake_failed", trace.rationale)
        self.assertIn("handshake stage", trace.rationale.lower())
        self.assertIn("Protocol mismatch", trace.rationale)
    
    def test_rationale_from_observed_error(self):
        """Test rationale generation from observed error."""
        classification = FailureClassification(
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            stage=FailureStage.HANDSHAKE.value,
            observed_error="Handshake timeout exceeded",
        )
        
        recommendation = {
            "recommendation_id": "recovery_1",
            "correlation_ids": {},
        }
        
        trace = self.exporter.export_decision_trace(
            recommendation=recommendation,
            failure_classification=classification,
        )
        
        self.assertIn("observed error", trace.rationale.lower())
        self.assertIn("Handshake timeout exceeded", trace.rationale)
    
    def test_rationale_fallback(self):
        """Test fallback rationale when no context available."""
        recommendation = {
            "recommendation_id": "recovery_1",
            "correlation_ids": {},
        }
        
        trace = self.exporter.export_decision_trace(recommendation)
        
        self.assertIn("available diagnostic context", trace.rationale.lower())


# ============================================================================
# TEST CONFIDENCE GUIDANCE TRACE
# ============================================================================


class TestDecisionTraceConfidence(unittest.TestCase):
    """Test confidence guidance trace (operator guidance, not certainty)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_hooks = MockDiagnosticHooks()
        self.exporter = DecisionTraceExporter(self.mock_hooks)
    
    def test_confidence_explanation_not_certainty(self):
        """Test that confidence explanation clarifies it's guidance, not certainty."""
        recommendation = {
            "recommendation_id": "recovery_1",
            "confidence": "high",
            "correlation_ids": {},
        }
        
        trace = self.exporter.export_decision_trace(recommendation)
        
        # Should mention "operator guidance"
        self.assertIn("operator guidance", trace.confidence_explanation.lower())
        # Should clarify it's not guaranteed success
        self.assertTrue(
            "not guaranteed" in trace.confidence_explanation.lower()
            or "reliability" in trace.confidence_explanation.lower()
        )
    
    def test_confidence_levels(self):
        """Test different confidence levels."""
        for level in ["low", "medium", "high", "very_high"]:
            recommendation = {
                "recommendation_id": "recovery_1",
                "confidence": level,
                "correlation_ids": {},
            }
            
            trace = self.exporter.export_decision_trace(recommendation)
            self.assertEqual(trace.confidence_level, level)
    
    def test_confidence_distribution_in_summary(self):
        """Test confidence distribution in summary."""
        summary = DecisionTraceSummary()
        
        traces = [
            DecisionTraceRecord(
                trace_id="t1",
                recommendation_id="r1",
                timestamp="2026-04-07T10:00:00Z",
                correlation_ids={},
                rationale="R",
                confidence_level="high",
                confidence_explanation="E",
                safe_next_action={"recommended_action": "A", "risk_level": "low", "required_verification": [], "fallback_options": []},
            ),
            DecisionTraceRecord(
                trace_id="t2",
                recommendation_id="r2",
                timestamp="2026-04-07T10:01:00Z",
                correlation_ids={},
                rationale="R",
                confidence_level="high",
                confidence_explanation="E",
                safe_next_action={"recommended_action": "A", "risk_level": "low", "required_verification": [], "fallback_options": []},
            ),
            DecisionTraceRecord(
                trace_id="t3",
                recommendation_id="r3",
                timestamp="2026-04-07T10:02:00Z",
                correlation_ids={},
                rationale="R",
                confidence_level="medium",
                confidence_explanation="E",
                safe_next_action={"recommended_action": "A", "risk_level": "medium", "required_verification": [], "fallback_options": []},
            ),
        ]
        
        summary.add_traces(traces)
        result = summary.build_summary()
        
        self.assertEqual(result["confidence_distribution"]["high"], 2)
        self.assertEqual(result["confidence_distribution"]["medium"], 1)


# ============================================================================
# TEST SAFE-NEXT-ACTION TRACE
# ============================================================================


class TestDecisionTraceSafeNextAction(unittest.TestCase):
    """Test safe-next-action trace."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_hooks = MockDiagnosticHooks()
        self.exporter = DecisionTraceExporter(self.mock_hooks)
    
    def test_safe_next_action_structure(self):
        """Test safe-next-action has required structure."""
        recommendation = {
            "recommendation_id": "recovery_1",
            "confidence": "high",
            "correlation_ids": {},
        }
        
        trace = self.exporter.export_decision_trace(recommendation)
        
        sna = trace.safe_next_action
        self.assertIn("recommended_action", sna)
        self.assertIn("risk_level", sna)
        self.assertIn("required_verification", sna)
        self.assertIn("fallback_options", sna)
    
    def test_risk_level_based_on_confidence(self):
        """Test risk level is determined by confidence."""
        # High confidence = low risk
        trace_high = self.exporter.export_decision_trace({
            "recommendation_id": "recovery_1",
            "confidence": "high",
            "correlation_ids": {},
        })
        self.assertEqual(trace_high.safe_next_action["risk_level"], "low")
        
        # Medium confidence = medium risk
        trace_medium = self.exporter.export_decision_trace({
            "recommendation_id": "recovery_2",
            "confidence": "medium",
            "correlation_ids": {},
        })
        self.assertEqual(trace_medium.safe_next_action["risk_level"], "medium")
    
    def test_fallback_options_present(self):
        """Test fallback options are included."""
        trace = self.exporter.export_decision_trace({
            "recommendation_id": "recovery_1",
            "confidence": "low",
            "correlation_ids": {},
        })
        
        fallbacks = trace.safe_next_action["fallback_options"]
        self.assertGreater(len(fallbacks), 0)
        self.assertIn("retry", " ".join(fallbacks).lower())
    
    def test_verification_steps_present(self):
        """Test required verification steps are included."""
        trace = self.exporter.export_decision_trace({
            "recommendation_id": "recovery_1",
            "stage": "proposal",
            "confidence": "high",
            "correlation_ids": {},
        })
        
        verification = trace.safe_next_action["required_verification"]
        self.assertGreater(len(verification), 0)
        self.assertIn("proposal", " ".join(verification).lower())
    
    def test_verification_by_stage(self):
        """Test verification steps vary by stage."""
        proposal_trace = self.exporter.export_decision_trace({
            "recommendation_id": "recovery_1",
            "stage": "proposal",
            "confidence": "high",
            "correlation_ids": {},
        })
        
        deadline_trace = self.exporter.export_decision_trace({
            "recommendation_id": "recovery_2",
            "stage": "deadline",
            "confidence": "high",
            "correlation_ids": {},
        })
        
        # Proposal stage should mention proposal
        self.assertIn("proposal", " ".join(proposal_trace.safe_next_action["required_verification"]).lower())
        # Deadline stage should mention execution/heartbeat (deadline verification)
        deadline_verification = " ".join(deadline_trace.safe_next_action["required_verification"]).lower()
        self.assertTrue("execution" in deadline_verification or "heartbeat" in deadline_verification)


# ============================================================================
# TEST INTEGRATION WITH V76
# ============================================================================


class TestIntegrationWithV76(unittest.TestCase):
    """Test integration with v76 recovery recommendation exporter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_hooks = MockDiagnosticHooks()
    
    def test_integrate_with_v76_exporter(self):
        """Test integration with v76 RecoveryRecommendationExporter."""
        v76_exporter = MockRecoveryRecommendationExporter()
        v76_exporter.add_record({
            "export_id": "rec_export_12345678",
            "recommendation_id": "recovery_1",
            "timestamp": "2026-04-07T10:00:00Z",
            "correlation_ids": {"flow_id": "flow_abc"},
            "recommendation_data": {
                "stage": "proposal",
                "failure_type": "proposal_rejected",
                "likely_cause": "Rejected",
                "recovery_hint": "Review criteria",
            },
            "failure_classification": None,
            "recovery_hint": "Review criteria",
            "confidence_level": "medium",
            "confidence_explanation": "Operator guidance.",
        })
        
        v78_exporter = integrate_with_v76_exporter(v76_exporter, self.mock_hooks)
        
        records = v78_exporter.export_machine_readable()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["recommendation_id"], "recovery_1")


# ============================================================================
# TEST INTEGRATION WITH V77
# ============================================================================


class TestIntegrationWithV77(unittest.TestCase):
    """Test integration with v77 recovery recommendation review surface."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_hooks = MockDiagnosticHooks()
    
    def test_integrate_with_v77_review_surface(self):
        """Test integration with v77 RecoveryRecommendationReviewSurface."""
        review_surface = RecoveryRecommendationReviewSurface()
        review_surface.load_recommendations([
            {
                "recommendation_id": "recovery_1",
                "stage": "proposal",
                "failure_type": "proposal_rejected",
                "likely_cause": "Rejected",
                "contributing_factors": [],
                "recovery_hint": "Review criteria",
                "confidence": "high",
                "hint_certainty": "suggestion",
                "correlation_ids": {"flow_id": "flow_abc"},
                "generated_at": "2026-04-07T10:00:00Z",
            },
        ])
        
        v78_exporter = integrate_with_v77_review_surface(review_surface, self.mock_hooks)
        
        records = v78_exporter.export_machine_readable()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["recommendation_id"], "recovery_1")
        # Risk level should be low (high confidence)
        self.assertEqual(records[0]["safe_next_action"]["risk_level"], "low")
    
    def test_empty_v77_review_surface(self):
        """Test integration with empty v77 review surface."""
        review_surface = RecoveryRecommendationReviewSurface()
        
        v78_exporter = integrate_with_v77_review_surface(review_surface, self.mock_hooks)
        
        records = v78_exporter.export_machine_readable()
        self.assertEqual(len(records), 0)


# ============================================================================
# TEST BACKWARD COMPATIBILITY
# ============================================================================


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with v76/v77 formats."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_hooks = MockDiagnosticHooks()
        self.exporter = DecisionTraceExporter(self.mock_hooks)
    
    def test_compat_with_v76_record_format(self):
        """Test compatibility with v76 export record format."""
        v76_record = {
            "export_id": "rec_export_12345678",
            "recommendation_id": "recovery_1",
            "timestamp": "2026-04-07T10:00:00Z",
            "correlation_ids": {"flow_id": "flow_abc"},
            "recommendation_data": {
                "stage": "proposal",
                "failure_type": "proposal_rejected",
                "likely_cause": "Rejected",
                "recovery_hint": "Review criteria",
                "confidence": "medium",
            },
            "failure_classification": None,
            "recovery_hint": "Review criteria",
            "confidence_level": "medium",
            "confidence_explanation": "Operator guidance.",
        }
        
        # Import record
        trace = DecisionTraceRecord.from_dict(v76_record)
        
        self.assertEqual(trace.recommendation_id, "recovery_1")
        self.assertEqual(trace.confidence_level, "medium")
    
    def test_compat_with_v77_recommendation_format(self):
        """Test compatibility with v77 recommendation format."""
        v77_recommendation = {
            "recommendation_id": "recovery_1",
            "stage": "proposal",
            "failure_type": "proposal_rejected",
            "likely_cause": "Rejected",
            "contributing_factors": [],
            "recovery_hint": "Review criteria",
            "confidence": "medium",
            "hint_certainty": "suggestion",
            "correlation_ids": {"flow_id": "flow_abc"},
            "generated_at": "2026-04-07T10:00:00Z",
        }
        
        trace = self.exporter.export_decision_trace(v77_recommendation)
        
        self.assertEqual(trace.recommendation_id, "recovery_1")
        self.assertIn("proposal", trace.rationale.lower())
    
    def test_compat_with_v74_fallback_format(self):
        """Test compatibility with v74 fallback trace format."""
        v74_recommendation = {
            "recommendation_id": "recovery_1",
            "stage": "handshake",
            "failure_type": "handshake_failed",
            "likely_cause": "Protocol mismatch",
            "recovery_hint": "Verify compatibility",
            "confidence": "high",
            "hint_certainty": "suggestion",
            "correlation_ids": {},
            "generated_at": "2026-04-07T10:00:00Z",
        }
        
        trace = self.exporter.export_decision_trace(v74_recommendation)
        
        self.assertEqual(trace.recommendation_id, "recovery_1")
        self.assertIn("handshake", trace.rationale.lower())
        # Should have fallback options
        self.assertIn("retry", " ".join(trace.safe_next_action["fallback_options"]).lower())


# ============================================================================
# MAIN
# ============================================================================


if __name__ == "__main__":
    unittest.main()
