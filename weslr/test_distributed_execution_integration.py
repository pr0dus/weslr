"""Tests for Distributed Execution Integration Layer (v64)

Behavioral tests for v61+v62+v63 integration flow.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.distributed_execution_integration import (
    ExecutionFlowState,
    FlowStage,
    StageCorrelation,
    RejectionPropagation,
    FailurePropagation,
    RollbackCoordination,
    IntegratedAuditTrace,
    ExecutionOrchestrator,
)
from weslr.remote_action_proposal import (
    RemoteActionProposal,
    ProposalStatus,
    RejectionReason,
    RejectionCategory,
)
from weslr.node_registry import NodeRegistry
from weslr.node_identity import (
    NodeIdentity,
    NodeTrustState,
    NodeRole,
    NodeTrustStatus,
    NodeHealthStatus,
)


class TestExecutionFlowState(unittest.TestCase):
    """Test execution flow state tracking."""

    def test_creation_defaults(self):
        """Flow created at proposal_created stage."""
        flow = ExecutionFlowState(flow_id="flow-1")
        
        self.assertEqual(flow.current_stage, FlowStage.PROPOSAL_CREATED.value)
        self.assertEqual(len(flow.stage_history), 1)
        self.assertFalse(flow.is_complete)

    def test_mark_proposal_approved(self):
        """Proposal approved stage transition."""
        flow = ExecutionFlowState(flow_id="flow-1")
        flow.mark_proposal_approved("prop-1")
        
        self.assertEqual(flow.current_stage, FlowStage.PROPOSAL_APPROVED.value)
        self.assertEqual(flow.proposal_id, "prop-1")

    def test_mark_envelope_created(self):
        """Envelope created stage transition."""
        flow = ExecutionFlowState(flow_id="flow-1")
        flow.mark_envelope_created("req-1")
        
        self.assertEqual(flow.current_stage, FlowStage.ENVELOPE_CREATED.value)
        self.assertEqual(flow.request_id, "req-1")

    def test_mark_execution_completed(self):
        """Execution completed stage transition."""
        flow = ExecutionFlowState(flow_id="flow-1")
        flow.mark_execution_completed()
        
        self.assertTrue(flow.is_complete)
        self.assertEqual(flow.current_stage, FlowStage.EXECUTION_COMPLETED.value)

    def test_mark_execution_failed(self):
        """Execution failed stage transition."""
        flow = ExecutionFlowState(flow_id="flow-1")
        flow.mark_execution_failed("Timeout")
        
        self.assertTrue(flow.is_failed)
        self.assertEqual(flow.current_stage, FlowStage.EXECUTION_FAILED.value)

    def test_mark_execution_rejected(self):
        """Execution rejected stage transition."""
        flow = ExecutionFlowState(flow_id="flow-1")
        flow.mark_execution_rejected("Trust insufficient")
        
        self.assertTrue(flow.is_rejected)
        self.assertEqual(flow.current_stage, FlowStage.EXECUTION_REJECTED.value)

    def test_stage_history(self):
        """Stage transitions logged."""
        flow = ExecutionFlowState(flow_id="flow-1")
        flow.mark_proposal_approved("prop-1")
        flow.mark_envelope_created("req-1")
        
        self.assertEqual(len(flow.stage_history), 3)
        self.assertEqual(flow.stage_history[1]["to"], FlowStage.PROPOSAL_APPROVED.value)

    def test_serialization(self):
        """Round-trip serialization works."""
        flow = ExecutionFlowState(flow_id="flow-1")
        flow.mark_proposal_approved("prop-1")
        flow.mark_envelope_created("req-1")
        
        data = flow.to_dict()
        
        self.assertEqual(data["flow_id"], "flow-1")
        self.assertEqual(data["proposal_id"], "prop-1")
        self.assertEqual(data["request_id"], "req-1")


class TestStageCorrelation(unittest.TestCase):
    """Test stage correlation continuity."""

    def test_link_proposal(self):
        """Proposal linked to flow."""
        corr = StageCorrelation(flow_id="flow-1")
        corr.link_proposal("prop-1")
        
        self.assertEqual(corr.proposal_id, "prop-1")
        self.assertEqual(corr.correlation_map["proposal"], "prop-1")

    def test_link_envelope(self):
        """Envelope linked to flow."""
        corr = StageCorrelation(flow_id="flow-1")
        corr.link_envelope("req-1")
        
        self.assertEqual(corr.request_id, "req-1")
        self.assertEqual(corr.correlation_map["envelope"], "req-1")

    def test_link_receipt(self):
        """Receipt linked to flow."""
        corr = StageCorrelation(flow_id="flow-1")
        corr.link_receipt("rec-1")
        corr.link_receipt("rec-2")
        
        self.assertEqual(len(corr.receipt_ids), 2)
        self.assertIn("rec-1", corr.receipt_ids)

    def test_get_correlated_ids(self):
        """All correlated IDs retrieved."""
        corr = StageCorrelation(flow_id="flow-1")
        corr.link_proposal("prop-1")
        corr.link_envelope("req-1")
        
        ids = corr.get_correlated_ids()
        
        self.assertEqual(ids["flow_id"], "flow-1")
        self.assertEqual(ids["proposal_id"], "prop-1")
        self.assertEqual(ids["request_id"], "req-1")


class TestRejectionPropagation(unittest.TestCase):
    """Test rejection propagation."""

    def test_propagate_from_proposal(self):
        """Rejection propagated from proposal."""
        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="node-a",
            target_node_id="node-b",
            action_type="sync_continuity"
        )
        proposal.reject(RejectionReason(
            category=RejectionCategory.TRUST_INSUFFICIENT.value,
            description="Trust too low"
        ))
        
        rejection = RejectionPropagation(
            flow_id="flow-1",
            rejection_source="proposal"
        )
        rejection.propagate_from_proposal(proposal)
        
        self.assertEqual(rejection.rejection_source, "proposal")
        self.assertIn("proposal", rejection.propagated_stages)
        self.assertIsNotNone(rejection.rejection_reason)

    def test_propagate_from_envelope(self):
        """Rejection propagated from envelope."""
        from weslr.controlled_execution_envelope import ExecutionRequestEnvelope
        
        envelope = ExecutionRequestEnvelope(
            request_id="req-1",
            proposal_id="prop-1",
            source_node_id="node-a",
            target_node_id="node-b",
            execution_intent="Test",
            action_type="sync_continuity"
        )
        envelope.rejection_reason = RejectionReason(
            category=RejectionCategory.HEALTH_DEGRADED.value,
            description="Target unhealthy"
        )
        
        rejection = RejectionPropagation(
            flow_id="flow-1",
            rejection_source="envelope"
        )
        rejection.propagate_from_envelope(envelope)
        
        self.assertEqual(rejection.rejection_source, "envelope")
        self.assertEqual(rejection.rejection_reason.category, RejectionCategory.HEALTH_DEGRADED.value)


class TestFailurePropagation(unittest.TestCase):
    """Test failure propagation."""

    def test_propagate_from_envelope(self):
        """Failure propagated from envelope."""
        from weslr.controlled_execution_envelope import ExecutionRequestEnvelope
        
        envelope = ExecutionRequestEnvelope(
            request_id="req-1",
            proposal_id="prop-1",
            source_node_id="node-a",
            target_node_id="node-b",
            execution_intent="Test",
            action_type="sync_continuity"
        )
        envelope.failure_reason = "Network timeout"
        
        failure = FailurePropagation(
            flow_id="flow-1",
            failure_source="envelope"
        )
        failure.propagate_from_envelope(envelope)
        
        self.assertEqual(failure.failure_source, "envelope")
        self.assertEqual(failure.failure_reason, "Network timeout")
        self.assertEqual(failure.failure_context["envelope_id"], "req-1")


class TestRollbackCoordination(unittest.TestCase):
    """Test rollback coordination."""

    def test_initiate_rollback(self):
        """Rollback initiated."""
        rollback = RollbackCoordination(flow_id="flow-1")
        rollback.initiate_rollback("Execution failed")
        
        self.assertTrue(rollback.rollback_initiated)
        self.assertEqual(rollback.rollback_reason, "Execution failed")
        self.assertIsNotNone(rollback.rollback_initiated_at)

    def test_mark_stage_rollback(self):
        """Stage rollback marked."""
        rollback = RollbackCoordination(flow_id="flow-1")
        rollback.mark_stage_rollback("envelope")
        rollback.mark_stage_rollback("receipt")
        
        self.assertIn("envelope", rollback.affected_stages)
        self.assertIn("receipt", rollback.affected_stages)

    def test_complete_rollback(self):
        """Rollback completed."""
        rollback = RollbackCoordination(flow_id="flow-1")
        rollback.initiate_rollback("Test")
        rollback.complete_rollback()
        
        self.assertTrue(rollback.rollback_completed)
        self.assertIsNotNone(rollback.rollback_completed_at)


class TestIntegratedAuditTrace(unittest.TestCase):
    """Test integrated audit trace."""

    def setUp(self):
        self.audit = IntegratedAuditTrace("local")

    def test_log_flow_event(self):
        """Flow events logged."""
        corr = StageCorrelation(flow_id="flow-1")
        corr.link_proposal("prop-1")
        
        self.audit.log_flow_event(
            flow_id="flow-1",
            stage="proposal",
            event_type="flow_created",
            correlation=corr
        )
        
        trace = self.audit.get_flow_trace("flow-1")
        self.assertEqual(len(trace), 1)
        self.assertEqual(trace[0]["stage"], "proposal")

    def test_get_flow_trace(self):
        """Full trace retrieved for flow."""
        self.audit.log_flow_event("flow-1", "proposal", "created")
        self.audit.log_flow_event("flow-1", "envelope", "created")
        self.audit.log_flow_event("flow-2", "proposal", "created")
        
        trace = self.audit.get_flow_trace("flow-1")
        self.assertEqual(len(trace), 2)


class TestExecutionOrchestrator(unittest.TestCase):
    """Test execution orchestrator integration."""

    def setUp(self):
        self.registry = NodeRegistry()
        
        # Set up local node
        self.local = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(
            node_id=self.local.node_id,
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        self.registry.register_local(self.local, local_trust)
        
        # Set up remote node
        self.remote = NodeIdentity.create_local("remote", NodeRole.WORKER)
        self.remote.node_id = "remote-1"
        self.remote.is_local = False
        
        remote_trust = NodeTrustState(
            node_id="remote-1",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        self.registry.register_remote(self.remote, remote_trust)
        
        # Create orchestrator
        self.orchestrator = ExecutionOrchestrator(
            local_node_id=self.local.node_id,
            registry=self.registry
        )
        
        # Create approved proposal
        self.proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id=self.local.node_id,
            target_node_id="remote-1",
            action_type="sync_continuity"
        )
        self.proposal.submit()
        self.proposal.start_validation()
        self.proposal.mark_validated([{"passed": True}])

    def test_create_flow(self):
        """Flow created from proposal."""
        flow = self.orchestrator.create_flow(self.proposal)
        
        self.assertIsNotNone(flow.flow_id)
        self.assertEqual(flow.proposal_id, "prop-1")
        self.assertEqual(flow.current_stage, FlowStage.PROPOSAL_CREATED.value)

    def test_approved_to_envelope(self):
        """Approved proposal converted to envelope."""
        flow = self.orchestrator.create_flow(self.proposal)
        
        envelope, error = self.orchestrator.approved_to_envelope(
            flow_id=flow.flow_id,
            proposal=self.proposal,
            execution_intent="Sync continuity data",
            skip_handshake=True
        )
        
        self.assertIsNotNone(envelope)
        self.assertIsNone(error)
        self.assertEqual(envelope.proposal_id, "prop-1")
        
        # Check flow updated
        updated_flow = self.orchestrator.get_flow(flow.flow_id)
        self.assertEqual(updated_flow.current_stage, FlowStage.ENVELOPE_CREATED.value)

    def test_approved_to_envelope_rejects_unapproved(self):
        """Unapproved proposal rejected."""
        unapproved = RemoteActionProposal(
            proposal_id="prop-2",
            proposing_node_id=self.local.node_id,
            target_node_id="remote-1",
            action_type="sync_continuity"
        )
        
        flow = self.orchestrator.create_flow(unapproved)
        
        envelope, error = self.orchestrator.approved_to_envelope(
            flow_id=flow.flow_id,
            proposal=unapproved,
            execution_intent="Test"
        )
        
        self.assertIsNone(envelope)
        self.assertIsNotNone(error)
        self.assertIn("not approved", error.lower())

    def test_evaluate_and_authorize(self):
        """Gates evaluated and envelope authorized."""
        flow = self.orchestrator.create_flow(self.proposal)
        
        envelope, _ = self.orchestrator.approved_to_envelope(
            flow_id=flow.flow_id,
            proposal=self.proposal,
            execution_intent="Sync data",
            skip_handshake=True
        )
        
        success, error = self.orchestrator.evaluate_and_authorize(flow.flow_id)
        
        self.assertTrue(success)
        self.assertIsNone(error)
        
        updated_flow = self.orchestrator.get_flow(flow.flow_id)
        self.assertEqual(updated_flow.current_stage, FlowStage.ENVELOPE_AUTHORIZED.value)

    def test_dispatch_and_receive_receipt(self):
        """Envelope dispatched and receipt received."""
        flow = self.orchestrator.create_flow(self.proposal)
        
        envelope, _ = self.orchestrator.approved_to_envelope(
            flow_id=flow.flow_id,
            proposal=self.proposal,
            execution_intent="Sync data",
            skip_handshake=True
        )
        
        self.orchestrator.evaluate_and_authorize(flow.flow_id)
        
        receipt, error = self.orchestrator.dispatch_and_receive_receipt(flow.flow_id)
        
        self.assertIsNotNone(receipt)
        self.assertIsNone(error)
        
        updated_flow = self.orchestrator.get_flow(flow.flow_id)
        self.assertEqual(updated_flow.current_stage, FlowStage.RECEIPT_RECEIVED.value)

    def test_complete_flow(self):
        """Flow marked as completed."""
        flow = self.orchestrator.create_flow(self.proposal)
        
        envelope, _ = self.orchestrator.approved_to_envelope(
            flow_id=flow.flow_id,
            proposal=self.proposal,
            execution_intent="Sync data",
            skip_handshake=True
        )
        
        self.orchestrator.evaluate_and_authorize(flow.flow_id)
        self.orchestrator.dispatch_and_receive_receipt(flow.flow_id)
        
        self.orchestrator.complete_flow(flow.flow_id, {"status": "success", "records": 100})
        
        updated_flow = self.orchestrator.get_flow(flow.flow_id)
        self.assertTrue(updated_flow.is_complete)
        self.assertEqual(updated_flow.current_stage, FlowStage.EXECUTION_COMPLETED.value)

    def test_fail_flow(self):
        """Flow marked as failed."""
        flow = self.orchestrator.create_flow(self.proposal)
        
        self.orchestrator.fail_flow(flow.flow_id, "Network timeout")
        
        updated_flow = self.orchestrator.get_flow(flow.flow_id)
        self.assertTrue(updated_flow.is_failed)
        self.assertEqual(updated_flow.current_stage, FlowStage.EXECUTION_FAILED.value)

    def test_initiate_and_complete_rollback(self):
        """Rollback initiated and completed."""
        flow = self.orchestrator.create_flow(self.proposal)
        
        envelope, _ = self.orchestrator.approved_to_envelope(
            flow_id=flow.flow_id,
            proposal=self.proposal,
            execution_intent="Sync data",
            skip_handshake=True
        )
        
        success = self.orchestrator.initiate_rollback(flow.flow_id, "Execution failed")
        self.assertTrue(success)
        
        self.orchestrator.complete_rollback(flow.flow_id)
        
        updated_flow = self.orchestrator.get_flow(flow.flow_id)
        self.assertTrue(updated_flow.is_rolled_back)

    def test_end_to_end_flow(self):
        """Complete end-to-end execution flow."""
        # Create flow
        flow = self.orchestrator.create_flow(self.proposal)
        flow_id = flow.flow_id
        
        # Proposal → Envelope (skip handshake for backward compat)
        envelope, error = self.orchestrator.approved_to_envelope(
            flow_id=flow_id,
            proposal=self.proposal,
            execution_intent="Synchronize continuity data",
            skip_handshake=True
        )
        self.assertIsNotNone(envelope)
        
        # Evaluate gates and authorize
        success, error = self.orchestrator.evaluate_and_authorize(flow_id)
        self.assertTrue(success)
        
        # Dispatch and receive receipt
        receipt, error = self.orchestrator.dispatch_and_receive_receipt(flow_id)
        self.assertIsNotNone(receipt)
        
        # Complete
        self.orchestrator.complete_flow(flow_id, {"status": "success"})
        
        # Verify final state
        final_flow = self.orchestrator.get_flow(flow_id)
        self.assertTrue(final_flow.is_complete)
        self.assertEqual(final_flow.current_stage, FlowStage.EXECUTION_COMPLETED.value)
        
        # Verify correlation
        correlation = self.orchestrator.get_correlation(flow_id)
        self.assertEqual(correlation.proposal_id, "prop-1")
        self.assertIsNotNone(correlation.request_id)
        self.assertGreater(len(correlation.receipt_ids), 0)
        
        # Verify audit trace
        trace = self.orchestrator.get_flow_trace(flow_id)
        self.assertGreater(len(trace), 0)


if __name__ == "__main__":
    unittest.main()
