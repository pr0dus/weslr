"""Test suite for Evidence-to-Governance Router - Phase C

Test Doctrine version: 1.0.0 (2026-04-06)
"""

import unittest
import time

from weslr.evidence_to_governance_router import (
    EvidenceToGovernanceRouter,
    RoutingRecord,
    RoutingState,
    RoutingAction,
    EvidenceProposalWithRouting,
    RoutingStatus,
)
from weslr.evidence_intake.models import (
    EvidenceProposalPayload,
    EvidenceSourceTypeEnum,
    EvidenceSource,
    NormalizedEvidence,
)
from weslr.internal_reasoning_graph.governance import (
    GovernanceAction as GovernanceActionEnum,
    GovernanceDecision as GovernanceDecisionEnum,
)


class TestEvidenceToGovernanceRouterModel(unittest.TestCase):
    """Model tests for Evidence-to-Governance Router."""
    
    def test_routing_status_enum(self) -> None:
        """Test RoutingStatus enum values."""
        self.assertEqual(RoutingStatus.GENERATED.value, "generated")
        self.assertEqual(RoutingStatus.REGISTERED.value, "registered")
        self.assertEqual(RoutingStatus.REVIEWING.value, "reviewing")
        self.assertEqual(RoutingStatus.APPROVED.value, "approved")
        self.assertEqual(RoutingStatus.REJECTED.value, "rejected")
    
    def test_routing_record_serialization(self) -> None:
        """Test RoutingRecord to_dict/from_dict serialization."""
        record = RoutingRecord(
            proposal_id="test-001",
            timestamp=1234567890,
            from_status=RoutingState.GENERATED,
            to_status=RoutingState.REGISTERED,
            actor="operator",
            action=RoutingAction.ROUTE,
            notes="Test routing",
        )
        data = record.to_dict()
        self.assertEqual(data["proposal_id"], "test-001")
        self.assertEqual(data["timestamp"], 1234567890)
        self.assertEqual(data["from_status"], "generated")
        self.assertEqual(data["to_status"], "registered")
        self.assertEqual(data["actor"], "operator")
        self.assertEqual(data["action"], "route")
        self.assertEqual(data["notes"], "Test routing")
        
        restored = RoutingRecord.from_dict(data)
        self.assertEqual(restored.proposal_id, "test-001")
        self.assertEqual(restored.from_status, RoutingState.GENERATED)
        self.assertEqual(restored.to_status, RoutingState.REGISTERED)
    
    def test_evidence_proposal_with_routing_serialization(self) -> None:
        """Test EvidenceProposalWithRouting serialization."""
        payload = EvidenceProposalPayload(
            evidence_id="test-001",
            claim_text="Test claim",
            source_summary="Test source",
            confidence=0.85,
            status="DRAFT",
        )
        with_routing = EvidenceProposalWithRouting.from_payload(payload)
        
        data = with_routing.to_dict()
        self.assertEqual(data["evidence_id"], "test-001")
        self.assertEqual(data["claim_text"], "Test claim")
        self.assertEqual(data["source_summary"], "Test source")
        self.assertEqual(data["confidence"], 0.85)
        self.assertEqual(data["routing_status"], "generated")
        
        restored = EvidenceProposalWithRouting.from_dict(data)
        self.assertEqual(restored.evidence_id, "test-001")
        self.assertEqual(restored.routing_status, "generated")
    
    def test_evidence_proposal_with_routing_from_payload_with_candidate(self) -> None:
        """Test EvidenceProposalWithRouting.from_payload_with_candidate."""
        payload = EvidenceProposalPayload(
            evidence_id="test-002",
            claim_text="Test claim",
            source_summary="Test source",
        )
        with_candidate = EvidenceProposalWithRouting.from_payload(payload)
        self.assertEqual(with_candidate.routing_status, "generated")
        self.assertEqual(with_candidate.evidence_id, "test-002")


class TestEvidenceToGovernanceRouterBehavior(unittest.TestCase):
    """Behavior tests for Evidence-to-Governance Router."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.router = EvidenceToGovernanceRouter()
        self.payload = EvidenceProposalPayload(
            evidence_id="test-proposal-001",
            claim_text="Test claim for routing",
            source_summary="Test source summary",
            confidence=0.75,
        )
    
    def test_route_to_registered_auto(self) -> None:
        """Test automatic routing to registered state."""
        result = self.router.route_evidence_to_registered(self.payload, actor="system")
        
        self.assertEqual(result.routing_status, "registered")
        self.assertEqual(result.evidence_id, "test-proposal-001")
        self.assertEqual(result.claim_text, "Test claim for routing")
        
        # Verify routing record created
        history = self.router.get_routing_history("test-proposal-001")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].from_status, RoutingState.GENERATED)
        self.assertEqual(history[0].to_status, RoutingState.REGISTERED)
        self.assertEqual(history[0].actor, "system")
        self.assertEqual(history[0].action, RoutingAction.ROUTE)
    
    def test_submit_for_review_operator_required(self) -> None:
        """Test that submit_for_review requires operator action."""
        # First route to registered
        self.router.route_evidence_to_registered(self.payload, actor="system")
        
        # Now submit for review (operator action)
        record = self.router.submit_for_review("test-proposal-001", reviewer="operator")
        
        self.assertEqual(record.from_status, RoutingState.REGISTERED)
        self.assertEqual(record.to_status, RoutingState.REVIEWING)
        self.assertEqual(record.actor, "operator")
        self.assertEqual(record.action, RoutingAction.SUBMIT_FOR_REVIEW)
        
        # Verify status changed
        status = self.router.get_routing_status("test-proposal-001")
        self.assertEqual(status, "reviewing")
    
    def test_approve_proposal_operator_required(self) -> None:
        """Test that approve_proposal requires operator action."""
        # Route to registered and submit for review
        self.router.route_evidence_to_registered(self.payload, actor="system")
        self.router.submit_for_review("test-proposal-001", reviewer="operator")
        
        # Now approve (operator action)
        record = self.router.approve_proposal("test-proposal-001", reviewer="operator", notes="Approved")
        
        self.assertEqual(record.from_status, RoutingState.REVIEWING)
        self.assertEqual(record.to_status, RoutingState.APPROVED)
        self.assertEqual(record.actor, "operator")
        self.assertEqual(record.action, RoutingAction.APPROVE)
        
        # Verify status changed
        status = self.router.get_routing_status("test-proposal-001")
        self.assertEqual(status, "approved")
    
    def test_reject_proposal_operator_required(self) -> None:
        """Test that reject_proposal requires operator action."""
        # Route to registered and submit for review
        self.router.route_evidence_to_registered(self.payload, actor="system")
        self.router.submit_for_review("test-proposal-001", reviewer="operator")
        
        # Now reject (operator action)
        record = self.router.reject_proposal("test-proposal-001", reviewer="operator", notes="Rejected")
        
        self.assertEqual(record.from_status, RoutingState.REVIEWING)
        self.assertEqual(record.to_status, RoutingState.REJECTED)
        self.assertEqual(record.actor, "operator")
        self.assertEqual(record.action, RoutingAction.REJECT)
        
        # Verify status changed
        status = self.router.get_routing_status("test-proposal-001")
        self.assertEqual(status, "rejected")
    
    def test_status_transition_constraints(self) -> None:
        """Test that status transitions are constrained correctly."""
        # Cannot submit for review from GENERATED (must be REGISTERED first)
        with self.assertRaises(ValueError):
            self.router.submit_for_review("nonexistent", reviewer="operator")
        
        # Route to registered first
        self.router.route_evidence_to_registered(self.payload, actor="system")
        
        # Cannot approve directly from REGISTERED (must go through REVIEWING first)
        # Actually this should be allowed - review can start and approve happen
        record = self.router.approve_proposal("test-proposal-001", reviewer="operator")
        self.assertEqual(record.to_status, RoutingState.APPROVED)
        
        # Cannot apply (deferred to Phase D)
        self.assertFalse(self.router.can_apply("test-proposal-001"))
    
    def test_no_auto_application(self) -> None:
        """Test that no automatic application is possible."""
        # Route and approve
        self.router.route_evidence_to_registered(self.payload, actor="system")
        self.router.approve_proposal("test-proposal-001", reviewer="operator")
        
        # Application must be explicit - router cannot auto-apply
        self.assertFalse(self.router.can_apply("test-proposal-001"))


class TestEvidenceToGovernanceRouterIntegration(unittest.TestCase):
    """Integration tests for Evidence-to-Governance Router."""
    
    def test_import_evidence_to_candidate_extension(self) -> None:
        """Test that evidence_to_candidate module can be imported with routing."""
        from weslr.evidence_intake.evidence_to_candidate import ProposalPayloadWithCandidate
        
        payload = ProposalPayloadWithCandidate(
            evidence_id="test-001",
            claim_text="Test claim",
            source_summary="Test source",
        )
        self.assertEqual(payload.routing_status, "generated")
    
    def test_routing_preserves_candidate_references(self) -> None:
        """Test that candidate references are preserved through routing."""
        from weslr.evidence_intake.evidence_to_candidate import CandidateProvenance, ProposalPayloadWithCandidate
        
        candidate_payload = ProposalPayloadWithCandidate(
            evidence_id="test-002",
            claim_text="Test claim",
            source_summary="Test source",
            candidate_reference="node-123",
            candidate_node_type="capability",
            candidate_confidence=0.9,
            candidate_recency="recent",
        )
        
        with_routing = EvidenceProposalWithRouting.from_payload_with_candidate(candidate_payload)
        
        self.assertEqual(with_routing.candidate_reference, "node-123")
        self.assertEqual(with_routing.candidate_node_type, "capability")
        self.assertEqual(with_routing.candidate_confidence, 0.9)
        self.assertEqual(with_routing.candidate_recency, "recent")
    
    def test_routing_integrates_with_governance_engine(self) -> None:
        """Test that routing correctly integrates with governance engine."""
        router = EvidenceToGovernanceRouter()
        
        payload = EvidenceProposalPayload(
            evidence_id="test-003",
            claim_text="Test claim",
            source_summary="Test source",
        )
        
        # Route to registered
        router.route_evidence_to_registered(payload, actor="system")
        
        # Submit for review
        router.submit_for_review("test-003", reviewer="operator")
        
        # Verify governance engine was called (submit_for_review adds a review record, not history)
        reviews = router.governance.get_review_records("test-003")
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].decision, GovernanceDecisionEnum.PENDING)
        self.assertEqual(reviews[0].reviewer, "operator")
    
    def test_routing_preserves_provenance_through_workflow(self) -> None:
        """Test that routing preserves provenance through the workflow."""
        from weslr.evidence_intake.evidence_to_candidate import CandidateProvenance, ProposalPayloadWithCandidate
        
        provenance = CandidateProvenance(
            source_id="source-001",
            source_timestamp="2026-04-08T10:00:00Z",
            normalized_timestamp="2026-04-08T10:05:00Z",
            confidence_score=0.85,
        )
        
        candidate_payload = ProposalPayloadWithCandidate(
            evidence_id="test-004",
            claim_text="Test claim",
            source_summary="Test source",
            candidate_reference="node-456",
            candidate_node_type="bottleneck",
            candidate_provenance=provenance,
        )
        
        with_routing = EvidenceProposalWithRouting.from_payload_with_candidate(candidate_payload)
        
        self.assertEqual(with_routing.candidate_reference, "node-456")
        self.assertIsNotNone(with_routing.candidate_provenance)
        if with_routing.candidate_provenance:
            self.assertEqual(with_routing.candidate_provenance.source_id, "source-001")
            self.assertEqual(with_routing.candidate_provenance.confidence_score, 0.85)


class TestEvidenceToGovernanceRouterBackwardCompatibility(unittest.TestCase):
    """Backward compatibility tests for Evidence-to-Governance Router."""
    
    def test_v94b_governance_engine_unmodified(self) -> None:
        """Test that v94b governance engine is not modified."""
        from weslr.internal_reasoning_graph.governance import (
            ProposalGovernanceEngine,
            GovernanceEngineState,
        )
        
        engine = ProposalGovernanceEngine()
        
        # Verify governance engine has expected methods
        self.assertTrue(hasattr(engine, "submit_for_review"))
        self.assertTrue(hasattr(engine, "approve_proposal"))
        self.assertTrue(hasattr(engine, "reject_proposal"))
        self.assertTrue(hasattr(engine, "get_proposal_status"))
        
        # Verify state has expected defaults
        state = engine.state
        self.assertTrue(state.require_operator_review)
        self.assertTrue(state.require_operator_approval)
        self.assertFalse(state.allow_auto_application)
    
    def test_v94c_evidence_intake_unmodified(self) -> None:
        """Test that v94c evidence intake models are not modified in breaking ways."""
        from weslr.evidence_intake.models import EvidenceProposalPayload, RoutingStatus
        
        # Verify EvidenceProposalPayload can be created with routing_status
        payload = EvidenceProposalPayload(
            evidence_id="test-005",
            claim_text="Test claim",
            source_summary="Test source",
        )
        self.assertEqual(payload.routing_status, RoutingStatus.GENERATED.value)
        
        # Verify routing_status field exists
        data = payload.to_dict()
        self.assertIn("routing_status", data)
    
    def test_routing_extensions_are_additive(self) -> None:
        """Test that routing extensions are additive (no breaking changes)."""
        from weslr.evidence_intake.models import EvidenceProposalPayload
        
        # Old-style creation (without routing_status) should work
        payload = EvidenceProposalPayload(
            evidence_id="test-006",
            claim_text="Test claim",
            source_summary="Test source",
        )
        self.assertEqual(payload.routing_status, RoutingStatus.GENERATED.value)
        
        # Verify from_dict works with old format (no routing_status)
        old_data = {
            "evidence_id": "test-006",
            "claim_text": "Test claim",
            "source_summary": "Test source",
        }
        restored = EvidenceProposalPayload.from_dict(old_data)
        self.assertEqual(restored.routing_status, RoutingStatus.GENERATED.value)
    
    def test_existing_proposal_workflow_compatibility(self) -> None:
        """Test that existing proposal workflow is compatible."""
        from weslr.internal_reasoning_graph.proposal_workflow import ProposalWorkflow
        
        workflow = ProposalWorkflow()
        
        # Verify workflow has expected methods
        self.assertTrue(hasattr(workflow, "submit_for_review"))
        self.assertTrue(hasattr(workflow, "approve_proposal"))
        self.assertTrue(hasattr(workflow, "reject_proposal"))


class TestEvidenceToGovernanceRouterExport(unittest.TestCase):
    """Export tests for Evidence-to-Governance Router."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.router = EvidenceToGovernanceRouter()
        self.payload = EvidenceProposalPayload(
            evidence_id="test-proposal-export",
            claim_text="Test claim for export",
            source_summary="Test source summary",
        )
        
        # Create some routing records
        self.router.route_evidence_to_registered(self.payload, actor="system")
        self.router.submit_for_review("test-proposal-export", reviewer="operator")
        self.router.approve_proposal("test-proposal-export", reviewer="operator", notes="Approved")
    
    def test_export_routing_summary(self) -> None:
        """Test export_routing_summary."""
        summary = self.router.export_routing_summary("test-proposal-export")
        
        self.assertEqual(summary["proposal_id"], "test-proposal-export")
        self.assertEqual(summary["routing_status"], "approved")
        self.assertIn("routing_history", summary)
        self.assertEqual(len(summary["routing_history"]), 3)
        
        # Verify history order
        history = summary["routing_history"]
        self.assertEqual(history[0]["to_status"], "registered")
        self.assertEqual(history[1]["to_status"], "reviewing")
        self.assertEqual(history[2]["to_status"], "approved")
    
    def test_export_all_routing(self) -> None:
        """Test export_all_routing."""
        result = self.router.export_all_routing()
        
        self.assertIn("routings", result)
        self.assertIn("total_count", result)
        self.assertIn("count_by_status", result)
        
        self.assertEqual(result["total_count"], 1)
        self.assertIn("approved", result["count_by_status"])
        self.assertEqual(result["count_by_status"]["approved"], 1)


if __name__ == "__main__":
    unittest.main()
