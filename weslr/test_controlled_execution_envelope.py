"""Tests for Controlled Remote Execution Envelope (v62)

Behavioral tests for safe distributed execution wrapper.
"""

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.controlled_execution_envelope import (
    ExecutionRequestEnvelope,
    ExecutionLifecycleState,
    RollbackPath,
    RollbackFeasibility,
    ExecutionGates,
    ExecutionAuditTrace,
    ExecutionEventType,
    ExplicitExecutionController,
)
from weslr.remote_action_proposal import (
    RemoteActionProposal,
    ProposalStatus,
    RejectionReason,
    RejectionCategory,
    ApprovalMode,
)
from weslr.node_identity import (
    NodeIdentity,
    NodeCapabilitySummary,
    NodeCapability,
    NodeTrustState,
    NodeRole,
    NodeTrustStatus,
    NodeHealthStatus,
)
from weslr.node_registry import NodeRegistry


class TestRollbackPath(unittest.TestCase):
    """Test rollback path tracking."""

    def test_creation_defaults(self):
        """Rollback path created with unknown feasibility."""
        path = RollbackPath()
        self.assertEqual(path.feasibility, RollbackFeasibility.UNKNOWN.value)
        self.assertEqual(path.status, "not_started")

    def test_mark_feasible(self):
        """Feasibility can be marked."""
        path = RollbackPath()
        path.mark_feasible(RollbackFeasibility.FULL.value, "Safe to rollback")
        
        self.assertEqual(path.feasibility, RollbackFeasibility.FULL.value)
        self.assertEqual(path.reason, "Safe to rollback")

    def test_can_rollback(self):
        """Can rollback checks feasibility."""
        path = RollbackPath()
        self.assertFalse(path.can_rollback())
        
        path.mark_feasible(RollbackFeasibility.FULL.value)
        self.assertTrue(path.can_rollback())
        
        path.mark_feasible(RollbackFeasibility.NONE.value)
        self.assertFalse(path.can_rollback())

    def test_initiate_rollback(self):
        """Rollback can be initiated."""
        path = RollbackPath()
        path.mark_feasible(RollbackFeasibility.FULL.value)
        
        can_initiate = path.initiate_rollback("Test rollback")
        self.assertTrue(can_initiate)
        self.assertEqual(path.status, "in_progress")
        self.assertEqual(path.reason, "Test rollback")
        self.assertIsNotNone(path.rollback_attempted_at)

    def test_initiate_fails_when_not_feasible(self):
        """Cannot initiate when not feasible."""
        path = RollbackPath()
        path.mark_feasible(RollbackFeasibility.NONE.value)
        
        can_initiate = path.initiate_rollback("Test rollback")
        self.assertFalse(can_initiate)

    def test_complete_rollback(self):
        """Rollback can be completed."""
        path = RollbackPath()
        path.mark_feasible(RollbackFeasibility.FULL.value)
        path.initiate_rollback("Test")
        path.complete_rollback()
        
        self.assertEqual(path.status, "completed")
        self.assertIsNotNone(path.rollback_completed_at)

    def test_fail_rollback(self):
        """Rollback can fail."""
        path = RollbackPath()
        path.mark_feasible(RollbackFeasibility.FULL.value)
        path.initiate_rollback("Test")
        path.fail_rollback("Error occurred")
        
        self.assertEqual(path.status, "failed")
        self.assertEqual(len(path.rollback_events), 1)

    def test_serialization(self):
        """Round-trip serialization works."""
        path = RollbackPath()
        path.mark_feasible(RollbackFeasibility.PARTIAL.value, "Partial rollback possible")
        
        data = path.to_dict()
        restored = RollbackPath.from_dict(data)
        
        self.assertEqual(restored.feasibility, RollbackFeasibility.PARTIAL.value)
        self.assertEqual(restored.reason, "Partial rollback possible")


class TestExecutionRequestEnvelope(unittest.TestCase):
    """Test execution envelope lifecycle."""

    def test_creation_defaults(self):
        """Envelope created in QUEUED state."""
        envelope = ExecutionRequestEnvelope(
            request_id="req-1",
            proposal_id="prop-1",
            source_node_id="node-a",
            target_node_id="node-b",
            execution_intent="Test execution",
            action_type="sync_continuity"
        )
        
        self.assertEqual(envelope.state, ExecutionLifecycleState.QUEUED.value)
        self.assertEqual(envelope.source_node_id, "node-a")
        self.assertEqual(envelope.target_node_id, "node-b")
        self.assertEqual(len(envelope.state_history), 1)

    def test_is_terminal(self):
        """Terminal states detected correctly."""
        terminal_states = [
            ExecutionLifecycleState.COMPLETED.value,
            ExecutionLifecycleState.FAILED.value,
            ExecutionLifecycleState.ROLLED_BACK.value,
            ExecutionLifecycleState.REJECTED.value
        ]
        
        for state in terminal_states:
            envelope = ExecutionRequestEnvelope(
                request_id="req-1",
                proposal_id="prop-1",
                source_node_id="node-a",
                target_node_id="node-b",
                execution_intent="Test",
                action_type="sync_continuity"
            )
            envelope.state = state
            self.assertTrue(envelope.is_terminal())

    def test_can_dispatch(self):
        """Can dispatch only from AUTHORIZED state."""
        envelope = ExecutionRequestEnvelope(
            request_id="req-1",
            proposal_id="prop-1",
            source_node_id="node-a",
            target_node_id="node-b",
            execution_intent="Test",
            action_type="sync_continuity"
        )
        
        self.assertFalse(envelope.can_dispatch())
        
        envelope.state = ExecutionLifecycleState.AUTHORIZED.value
        self.assertTrue(envelope.can_dispatch())

    def test_state_transition(self):
        """State transitions recorded in history."""
        envelope = ExecutionRequestEnvelope(
            request_id="req-1",
            proposal_id="prop-1",
            source_node_id="node-a",
            target_node_id="node-b",
            execution_intent="Test",
            action_type="sync_continuity"
        )
        
        envelope._transition_to(ExecutionLifecycleState.AUTHORIZED.value, "Approved")
        
        self.assertEqual(envelope.state, ExecutionLifecycleState.AUTHORIZED.value)
        self.assertEqual(len(envelope.state_history), 2)
        self.assertEqual(envelope.state_history[-1]["to"], ExecutionLifecycleState.AUTHORIZED.value)

    def test_serialization(self):
        """Round-trip serialization works."""
        envelope = ExecutionRequestEnvelope(
            request_id="req-1",
            proposal_id="prop-1",
            source_node_id="node-a",
            target_node_id="node-b",
            execution_intent="Test execution",
            action_type="sync_continuity",
            action_payload={"key": "value"},
            capability_requirements=[("compute", "cpu")]
        )
        
        data = envelope.to_dict()
        restored = ExecutionRequestEnvelope.from_dict(data)
        
        self.assertEqual(restored.request_id, "req-1")
        self.assertEqual(restored.action_payload["key"], "value")
        self.assertEqual(restored.capability_requirements, [("compute", "cpu")])


class TestExecutionGates(unittest.TestCase):
    """Test execution gates."""

    def setUp(self):
        self.registry = NodeRegistry()
        self.local = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(
            node_id=self.local.node_id,
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        self.registry.register_local(self.local, local_trust)
        
        self.gates = ExecutionGates(self.registry)

    def test_trust_gate_passes(self):
        """Trusted node passes trust gate."""
        remote = NodeIdentity.create_local("remote", NodeRole.WORKER)
        remote.node_id = "remote-1"
        remote.is_local = False
        
        trust = NodeTrustState(
            node_id="remote-1",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        self.registry.register_remote(remote, trust)
        
        envelope = ExecutionRequestEnvelope(
            request_id="req-1",
            proposal_id="prop-1",
            source_node_id="local",
            target_node_id="remote-1",
            execution_intent="Test",
            action_type="sync_continuity"
        )
        
        passed, reason = self.gates.evaluate_trust_gate(envelope)
        self.assertTrue(passed)
        self.assertIsNone(reason)

    def test_trust_gate_fails_untrusted(self):
        """Untrusted node fails trust gate."""
        remote = NodeIdentity.create_local("remote", NodeRole.WORKER)
        remote.node_id = "remote-1"
        remote.is_local = False
        
        trust = NodeTrustState(
            node_id="remote-1",
            trust_status=NodeTrustStatus.PROVISIONAL.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        self.registry.register_remote(remote, trust)
        
        envelope = ExecutionRequestEnvelope(
            request_id="req-1",
            proposal_id="prop-1",
            source_node_id="local",
            target_node_id="remote-1",
            execution_intent="Test",
            action_type="sync_continuity"
        )
        
        passed, reason = self.gates.evaluate_trust_gate(envelope)
        self.assertFalse(passed)
        self.assertIsNotNone(reason)
        self.assertEqual(reason.category, RejectionCategory.TRUST_INSUFFICIENT.value)

    def test_health_gate_passes_healthy(self):
        """Healthy node passes health gate."""
        remote = NodeIdentity.create_local("remote", NodeRole.WORKER)
        remote.node_id = "remote-1"
        remote.is_local = False
        
        trust = NodeTrustState(
            node_id="remote-1",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        self.registry.register_remote(remote, trust)
        
        envelope = ExecutionRequestEnvelope(
            request_id="req-1",
            proposal_id="prop-1",
            source_node_id="local",
            target_node_id="remote-1",
            execution_intent="Test",
            action_type="sync_continuity"
        )
        
        passed, reason = self.gates.evaluate_health_gate(envelope)
        self.assertTrue(passed)
        self.assertIsNone(reason)

    def test_health_gate_fails_unhealthy(self):
        """Unhealthy node fails health gate."""
        remote = NodeIdentity.create_local("remote", NodeRole.WORKER)
        remote.node_id = "remote-1"
        remote.is_local = False
        
        trust = NodeTrustState(
            node_id="remote-1",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.UNHEALTHY.value
        )
        self.registry.register_remote(remote, trust)
        
        envelope = ExecutionRequestEnvelope(
            request_id="req-1",
            proposal_id="prop-1",
            source_node_id="local",
            target_node_id="remote-1",
            execution_intent="Test",
            action_type="sync_continuity"
        )
        
        passed, reason = self.gates.evaluate_health_gate(envelope)
        self.assertFalse(passed)
        self.assertIsNotNone(reason)
        self.assertEqual(reason.category, RejectionCategory.HEALTH_DEGRADED.value)

    def test_evaluate_all_gates(self):
        """All gates evaluated together."""
        remote = NodeIdentity.create_local("remote", NodeRole.WORKER)
        remote.node_id = "remote-1"
        remote.is_local = False
        
        trust = NodeTrustState(
            node_id="remote-1",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        self.registry.register_remote(remote, trust)
        
        envelope = ExecutionRequestEnvelope(
            request_id="req-1",
            proposal_id="prop-1",
            source_node_id="local",
            target_node_id="remote-1",
            execution_intent="Test",
            action_type="sync_continuity"
        )
        
        all_passed, failures = self.gates.evaluate_all_gates(envelope)
        self.assertTrue(all_passed)
        self.assertEqual(len(failures), 0)
        self.assertTrue(envelope.trust_gate_passed)
        self.assertTrue(envelope.health_gate_passed)
        self.assertTrue(envelope.safety_gate_passed)


class TestExecutionAuditTrace(unittest.TestCase):
    """Test execution audit trace."""

    def setUp(self):
        self.trace = ExecutionAuditTrace("local")

    def test_log_event(self):
        """Events can be logged."""
        event = self.trace.log_event(
            request_id="req-1",
            event_type=ExecutionEventType.ENVELOPE_CREATED.value,
            details={"intent": "Test"}
        )
        
        self.assertEqual(event.request_id, "req-1")
        self.assertEqual(event.event_type, ExecutionEventType.ENVELOPE_CREATED.value)

    def test_get_events(self):
        """Events retrieved by request ID."""
        self.trace.log_event("req-1", ExecutionEventType.ENVELOPE_CREATED.value)
        self.trace.log_event("req-1", ExecutionEventType.AUTHORIZED.value)
        self.trace.log_event("req-2", ExecutionEventType.ENVELOPE_CREATED.value)
        
        events = self.trace.get_events("req-1")
        self.assertEqual(len(events), 2)

    def test_get_trace(self):
        """Full trace can be retrieved."""
        self.trace.log_event("req-1", ExecutionEventType.ENVELOPE_CREATED.value)
        self.trace.log_event("req-1", ExecutionEventType.AUTHORIZED.value)
        
        trace = self.trace.get_trace("req-1")
        self.assertEqual(len(trace), 2)
        self.assertEqual(trace[0]["event_type"], ExecutionEventType.ENVELOPE_CREATED.value)

    def test_get_stats(self):
        """Statistics can be retrieved."""
        self.trace.log_event("req-1", ExecutionEventType.ENVELOPE_CREATED.value)
        self.trace.log_event("req-2", ExecutionEventType.ENVELOPE_CREATED.value)
        self.trace.log_event("req-1", ExecutionEventType.AUTHORIZED.value)
        
        stats = self.trace.get_stats()
        self.assertEqual(stats["total_events"], 3)
        self.assertEqual(stats["requests_tracked"], 2)


class TestExplicitExecutionController(unittest.TestCase):
    """Test explicit execution controller."""

    def setUp(self):
        self.registry = NodeRegistry()
        self.local = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(
            node_id=self.local.node_id,
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        self.registry.register_local(self.local, local_trust)
        
        self.remote = NodeIdentity.create_local("remote", NodeRole.WORKER)
        self.remote.node_id = "remote-1"
        self.remote.is_local = False
        
        remote_trust = NodeTrustState(
            node_id="remote-1",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        self.registry.register_remote(self.remote, remote_trust)
        
        self.controller = ExplicitExecutionController(
            local_node_id=self.local.node_id,
            registry=self.registry
        )
        
        self.proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="local",
            target_node_id="remote-1",
            action_type="sync_continuity",
            action_payload={"data": "test"}
        )

    def test_create_envelope(self):
        """Envelope created from proposal."""
        envelope = self.controller.create_envelope(
            proposal=self.proposal,
            execution_intent="Test sync continuity"
        )
        
        self.assertIsNotNone(envelope.request_id)
        self.assertEqual(envelope.proposal_id, "prop-1")
        self.assertEqual(envelope.target_node_id, "remote-1")
        self.assertEqual(envelope.state, ExecutionLifecycleState.QUEUED.value)

    def test_full_execution_flow(self):
        """Complete execution flow from creation to completion."""
        # Create envelope
        envelope = self.controller.create_envelope(
            proposal=self.proposal,
            execution_intent="Test sync continuity"
        )
        request_id = envelope.request_id
        
        # Evaluate gates
        passed, failures = self.controller.evaluate_gates(request_id)
        self.assertTrue(passed)
        
        # Request approval
        self.controller.request_approval(request_id)
        envelope = self.controller.get_envelope(request_id)
        self.assertEqual(envelope.state, ExecutionLifecycleState.AWAITING_APPROVAL.value)
        
        # Grant approval
        self.controller.grant_approval(request_id, "operator-1")
        envelope = self.controller.get_envelope(request_id)
        self.assertEqual(envelope.state, ExecutionLifecycleState.AUTHORIZED.value)
        
        # Dispatch
        self.controller.dispatch(request_id)
        envelope = self.controller.get_envelope(request_id)
        self.assertEqual(envelope.state, ExecutionLifecycleState.DISPATCHED.value)
        
        # Acknowledge
        self.controller.acknowledge(request_id)
        envelope = self.controller.get_envelope(request_id)
        self.assertEqual(envelope.state, ExecutionLifecycleState.ACKNOWLEDGED.value)
        
        # Complete
        self.controller.complete(request_id, {"status": "success"})
        envelope = self.controller.get_envelope(request_id)
        self.assertEqual(envelope.state, ExecutionLifecycleState.COMPLETED.value)
        self.assertEqual(envelope.execution_result["status"], "success")

    def test_approval_denied(self):
        """Approval denial transitions to rejected."""
        envelope = self.controller.create_envelope(
            proposal=self.proposal,
            execution_intent="Test"
        )
        request_id = envelope.request_id
        
        # Evaluate gates first
        self.controller.evaluate_gates(request_id)
        
        # Request and deny approval
        self.controller.request_approval(request_id)
        self.controller.deny_approval(request_id, "Safety concerns")
        
        envelope = self.controller.get_envelope(request_id)
        self.assertEqual(envelope.state, ExecutionLifecycleState.REJECTED.value)
        self.assertIsNotNone(envelope.rejection_reason)

    def test_invalid_state_transitions(self):
        """Invalid state transitions raise errors."""
        envelope = self.controller.create_envelope(
            proposal=self.proposal,
            execution_intent="Test"
        )
        request_id = envelope.request_id
        
        # Cannot dispatch from QUEUED
        with self.assertRaises(ValueError):
            self.controller.dispatch(request_id)
        
        # Cannot acknowledge from QUEUED
        with self.assertRaises(ValueError):
            self.controller.acknowledge(request_id)

    def test_failure_handling(self):
        """Execution can fail."""
        envelope = self.controller.create_envelope(
            proposal=self.proposal,
            execution_intent="Test"
        )
        request_id = envelope.request_id
        
        # Move to dispatched
        self.controller.evaluate_gates(request_id)
        self.controller.request_approval(request_id)
        self.controller.grant_approval(request_id, "op-1")
        self.controller.dispatch(request_id)
        
        # Fail
        self.controller.fail(request_id, "Network error")
        
        envelope = self.controller.get_envelope(request_id)
        self.assertEqual(envelope.state, ExecutionLifecycleState.FAILED.value)
        self.assertEqual(envelope.failure_reason, "Network error")

    def test_rollback_flow(self):
        """Rollback flow works."""
        envelope = self.controller.create_envelope(
            proposal=self.proposal,
            execution_intent="Test"
        )
        request_id = envelope.request_id
        
        # Mark rollback feasible
        envelope.rollback_path.mark_feasible(RollbackFeasibility.FULL.value)
        
        # Initiate rollback
        can_initiate = self.controller.initiate_rollback(request_id, "Test rollback")
        self.assertTrue(can_initiate)
        
        # Complete rollback
        self.controller.complete_rollback(request_id)
        
        envelope = self.controller.get_envelope(request_id)
        self.assertEqual(envelope.state, ExecutionLifecycleState.ROLLED_BACK.value)
        self.assertEqual(envelope.rollback_path.status, "completed")

    def test_audit_events_logged(self):
        """Audit events logged throughout lifecycle."""
        envelope = self.controller.create_envelope(
            proposal=self.proposal,
            execution_intent="Test"
        )
        request_id = envelope.request_id
        
        # Run through lifecycle
        self.controller.evaluate_gates(request_id)
        self.controller.request_approval(request_id)
        self.controller.grant_approval(request_id, "op-1")
        self.controller.dispatch(request_id)
        self.controller.acknowledge(request_id)
        self.controller.complete(request_id, {"status": "ok"})
        
        # Check audit events
        events = self.controller.audit.get_events(request_id)
        event_types = [e.event_type for e in events]
        
        self.assertIn(ExecutionEventType.ENVELOPE_CREATED.value, event_types)
        self.assertIn(ExecutionEventType.AUTHORIZED.value, event_types)
        self.assertIn(ExecutionEventType.DISPATCHED.value, event_types)
        self.assertIn(ExecutionEventType.COMPLETED.value, event_types)

    def test_gates_evaluation_rejects_untrusted(self):
        """Gates reject untrusted target."""
        # Create untrusted remote
        untrusted_remote = NodeIdentity.create_local("untrusted", NodeRole.WORKER)
        untrusted_remote.node_id = "untrusted-1"
        untrusted_remote.is_local = False
        
        untrusted_trust = NodeTrustState(
            node_id="untrusted-1",
            trust_status=NodeTrustStatus.UNTRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        self.registry.register_remote(untrusted_remote, untrusted_trust)
        
        proposal = RemoteActionProposal(
            proposal_id="prop-2",
            proposing_node_id="local",
            target_node_id="untrusted-1",
            action_type="sync_continuity"
        )
        
        envelope = self.controller.create_envelope(
            proposal=proposal,
            execution_intent="Test"
        )
        
        passed, failures = self.controller.evaluate_gates(envelope.request_id)
        self.assertFalse(passed)
        self.assertEqual(envelope.state, ExecutionLifecycleState.REJECTED.value)


if __name__ == "__main__":
    unittest.main()
