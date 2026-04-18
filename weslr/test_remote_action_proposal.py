"""Tests for Remote Action Proposal / Orchestration Guardrails (v61)

Behavioral tests for safe remote action proposal layer.
"""

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.remote_action_proposal import (
    RemoteActionProposal,
    ProposalStatus,
    RejectionCategory,
    RejectionReason,
    ApprovalMode,
    AuditEventType,
    TargetNodeSelection,
    CapabilityBoundaryCheck,
    TrustHealthGate,
    ProofSafetyHooks,
    ApprovalRequirement,
    EscalationPath,
    ProposalAuditTrace,
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


class TestRejectionReason(unittest.TestCase):
    """Test rejection reason structure."""

    def test_creation(self):
        """Rejection reason stores category and description."""
        reason = RejectionReason(
            category=RejectionCategory.TRUST_INSUFFICIENT.value,
            description="Trust level too low"
        )

        self.assertEqual(reason.category, RejectionCategory.TRUST_INSUFFICIENT.value)
        self.assertEqual(reason.description, "Trust level too low")

    def test_with_remediation(self):
        """Rejection can include remediation hints."""
        reason = RejectionReason(
            category=RejectionCategory.HEALTH_DEGRADED.value,
            description="Health degraded",
            retry_possible=True,
            retry_after_seconds=300,
            remediation_suggestion="Wait for health recovery"
        )

        self.assertTrue(reason.retry_possible)
        self.assertEqual(reason.retry_after_seconds, 300)

    def test_serialization(self):
        """Round-trip serialization works."""
        reason = RejectionReason(
            category=RejectionCategory.CAPABILITY_MISSING.value,
            description="Missing capability",
            details={"cap": "compute"}
        )

        data = reason.to_dict()
        restored = RejectionReason.from_dict(data)

        self.assertEqual(restored.category, reason.category)
        self.assertEqual(restored.details["cap"], "compute")


class TestRemoteActionProposal(unittest.TestCase):
    """Test proposal lifecycle."""

    def test_creation_defaults(self):
        """Proposal created in DRAFT status."""
        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="node-a",
            target_node_id="node-b",
            action_type="sync_continuity"
        )

        self.assertEqual(proposal.status, ProposalStatus.DRAFT.value)
        self.assertEqual(proposal.proposing_node_id, "node-a")
        self.assertEqual(proposal.target_node_id, "node-b")

    def test_submit_transition(self):
        """Submit transitions to PENDING."""
        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="node-a",
            target_node_id="node-b",
            action_type="sync_continuity"
        )

        proposal.submit()

        self.assertEqual(proposal.status, ProposalStatus.PENDING.value)
        self.assertIsNotNone(proposal.submitted_at)

    def test_validation_success(self):
        """Validation success transitions to APPROVED in automatic mode with no gates."""
        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="node-a",
            target_node_id="node-b",
            action_type="sync_continuity"
        )
        proposal.submit()
        proposal.start_validation()

        proposal.mark_validated([{"passed": True, "check": "test"}])

        # In automatic mode with no gates, goes directly to APPROVED
        self.assertEqual(proposal.status, ProposalStatus.APPROVED.value)

    def test_validation_failure(self):
        """Validation failure rejects proposal."""
        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="node-a",
            target_node_id="node-b",
            action_type="sync_continuity"
        )
        proposal.submit()
        proposal.start_validation()

        proposal.mark_validated([{"passed": False, "check": "test"}])

        self.assertEqual(proposal.status, ProposalStatus.REJECTED.value)
        self.assertIsNotNone(proposal.rejection_reason)

    def test_gate_clearing(self):
        """Clearing all gates triggers approval check."""
        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="node-a",
            target_node_id="node-b",
            action_type="sync_continuity"
        )
        proposal.submit()
        proposal.start_validation()

        # Add gates first, then validate
        proposal.add_gate_requirement("proof-a")
        proposal.add_gate_requirement("proof-b")

        proposal.mark_validated([{"passed": True}])

        # Should be GATED with gates pending
        self.assertEqual(proposal.status, ProposalStatus.GATED.value)

        proposal.clear_gate("proof-a")
        self.assertEqual(proposal.status, ProposalStatus.GATED.value)  # Still gated

        proposal.clear_gate("proof-b")
        # Now should be approved (automatic mode)
        self.assertEqual(proposal.status, ProposalStatus.APPROVED.value)  # Auto-approved

    def test_manual_approval(self):
        """Manual approval mode requires explicit approval."""
        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="node-a",
            target_node_id="node-b",
            action_type="sync_continuity",
            approval_mode=ApprovalMode.MANUAL.value
        )
        proposal.submit()
        proposal.start_validation()
        proposal.add_gate_requirement("proof-1")  # Add gate to prevent auto-approval
        proposal.mark_validated([{"passed": True}])

        # With manual mode and gates pending, stays in GATED
        self.assertEqual(proposal.status, ProposalStatus.GATED.value)

        proposal.clear_gate("proof-1")  # Clear the gate

        # Still in GATED because manual mode requires explicit approval
        self.assertEqual(proposal.status, ProposalStatus.GATED.value)

        result = proposal.approve("operator-1")
        self.assertTrue(result)
        self.assertEqual(proposal.status, ProposalStatus.APPROVED.value)

    def test_multi_party_approval(self):
        """Multi-party mode requires N approvals."""
        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="node-a",
            target_node_id="node-b",
            action_type="sync_continuity",
            approval_mode=ApprovalMode.MULTI_PARTY.value,
            approvals_required=2
        )
        proposal.submit()
        proposal.start_validation()
        proposal.mark_validated([{"passed": True}])

        result = proposal.approve("approver-1")
        self.assertFalse(result)  # Not yet approved
        self.assertEqual(proposal.status, ProposalStatus.GATED.value)

        result = proposal.approve("approver-2")
        self.assertTrue(result)  # Now approved
        self.assertEqual(proposal.status, ProposalStatus.APPROVED.value)

    def test_reject_external(self):
        """External rejection with full reason."""
        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="node-a",
            target_node_id="node-b",
            action_type="sync_continuity"
        )
        proposal.submit()

        reason = RejectionReason(
            category=RejectionCategory.POLICY_VIOLATION.value,
            description="Violates safety policy"
        )
        proposal.reject(reason)

        self.assertEqual(proposal.status, ProposalStatus.REJECTED.value)
        self.assertEqual(proposal.rejection_reason.category, RejectionCategory.POLICY_VIOLATION.value)

    def test_escalate(self):
        """Proposal can be escalated."""
        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="node-a",
            target_node_id="node-b",
            action_type="sync_continuity"
        )
        proposal.submit()

        proposal.escalate("esc-path-1", "controller-node")

        self.assertEqual(proposal.status, ProposalStatus.ESCALATED.value)
        self.assertEqual(proposal.escalated_to, "controller-node")
        self.assertEqual(proposal.escalation_path_id, "esc-path-1")

    def test_expiry_check(self):
        """Expired proposals marked as expired."""
        past = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat().replace("+00:00", "Z")

        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="node-a",
            target_node_id="node-b",
            action_type="sync_continuity",
            expires_at=past
        )
        proposal.submit()

        is_expired = proposal.check_expiry()
        self.assertTrue(is_expired)
        self.assertEqual(proposal.status, ProposalStatus.EXPIRED.value)

    def test_status_history(self):
        """Status transitions are logged."""
        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="node-a",
            target_node_id="node-b",
            action_type="sync_continuity"
        )
        proposal.submit()
        proposal.start_validation()

        self.assertEqual(len(proposal.status_history), 2)
        self.assertEqual(proposal.status_history[0]["from"], ProposalStatus.DRAFT.value)
        self.assertEqual(proposal.status_history[0]["to"], ProposalStatus.PENDING.value)

    def test_can_execute(self):
        """Approved proposals can execute."""
        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="node-a",
            target_node_id="node-b",
            action_type="sync_continuity"
        )
        self.assertFalse(proposal.can_execute())

        proposal.submit()
        proposal.start_validation()
        proposal.mark_validated([{"passed": True}])

        # In automatic mode, goes directly to APPROVED
        self.assertEqual(proposal.status, ProposalStatus.APPROVED.value)
        self.assertTrue(proposal.can_execute())


class TestTargetNodeSelection(unittest.TestCase):
    """Test target node selection."""

    def test_matches_trusted_healthy(self):
        """Matches trusted healthy node with capabilities."""
        selector = TargetNodeSelection(
            required_capabilities=[("compute", "cpu")],
            min_trust_level=NodeTrustStatus.TRUSTED.value
        )

        identity = NodeIdentity.create_local("test", NodeRole.WORKER)
        caps = NodeCapabilitySummary(
            node_id=identity.node_id,
            capabilities=[NodeCapability("compute", "cpu", "1.0")]
        )
        trust = NodeTrustState(
            node_id=identity.node_id,
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )

        matches, reason = selector.matches(identity, caps, trust, True)
        self.assertTrue(matches)

    def test_rejects_untrusted(self):
        """Rejects untrusted node."""
        selector = TargetNodeSelection(
            min_trust_level=NodeTrustStatus.TRUSTED.value
        )

        identity = NodeIdentity.create_local("test", NodeRole.WORKER)
        caps = NodeCapabilitySummary(node_id=identity.node_id)
        trust = NodeTrustState(
            node_id=identity.node_id,
            trust_status=NodeTrustStatus.PROVISIONAL.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )

        matches, reason = selector.matches(identity, caps, trust, True)
        self.assertFalse(matches)
        self.assertIn("trust", reason.lower())

    def test_rejects_missing_capability(self):
        """Rejects node without required capability."""
        selector = TargetNodeSelection(
            required_capabilities=[("compute", "gpu")]
        )

        identity = NodeIdentity.create_local("test", NodeRole.WORKER)
        caps = NodeCapabilitySummary(
            node_id=identity.node_id,
            capabilities=[NodeCapability("compute", "cpu", "1.0")]
        )
        trust = NodeTrustState(
            node_id=identity.node_id,
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )

        matches, reason = selector.matches(identity, caps, trust, True)
        self.assertFalse(matches)
        self.assertIn("capability", reason.lower())

    def test_rejects_unreachable(self):
        """Rejects unreachable node when required."""
        selector = TargetNodeSelection(require_reachable=True)

        identity = NodeIdentity.create_local("test", NodeRole.WORKER)
        caps = NodeCapabilitySummary(node_id=identity.node_id)
        trust = NodeTrustState(
            node_id=identity.node_id,
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )

        matches, reason = selector.matches(identity, caps, trust, False)
        self.assertFalse(matches)
        self.assertIn("reachable", reason.lower())


class TestCapabilityBoundaryCheck(unittest.TestCase):
    """Test capability boundary validation."""

    def setUp(self):
        # Create minimal registry
        self.registry = NodeRegistry()
        self.local = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(node_id=self.local.node_id, trust_status=NodeTrustStatus.TRUSTED.value)
        self.registry.register_local(self.local, local_trust)

        self.checker = CapabilityBoundaryCheck(self.registry)

    def test_has_capabilities(self):
        """Node with capabilities passes check."""
        remote = NodeIdentity.create_local("remote", NodeRole.WORKER)
        remote.node_id = "remote-1"
        remote.is_local = False

        caps = NodeCapabilitySummary(
            node_id="remote-1",
            capabilities=[
                NodeCapability("compute", "cpu", "1.0"),
                NodeCapability("storage", "disk", "1.0")
            ]
        )
        trust = NodeTrustState(node_id="remote-1", trust_status=NodeTrustStatus.TRUSTED.value)

        self.registry.register_remote(remote, trust, caps)

        has_all, missing = self.checker.check("remote-1", [("compute", "cpu")])
        self.assertTrue(has_all)
        self.assertEqual(missing, [])

    def test_missing_capabilities(self):
        """Node missing capabilities fails check."""
        remote = NodeIdentity.create_local("remote", NodeRole.WORKER)
        remote.node_id = "remote-1"
        remote.is_local = False

        caps = NodeCapabilitySummary(
            node_id="remote-1",
            capabilities=[NodeCapability("compute", "cpu", "1.0")]
        )
        trust = NodeTrustState(node_id="remote-1", trust_status=NodeTrustStatus.TRUSTED.value)

        self.registry.register_remote(remote, trust, caps)

        has_all, missing = self.checker.check("remote-1", [("compute", "gpu")])
        self.assertFalse(has_all)
        self.assertIn("compute/gpu", missing)


class TestTrustHealthGate(unittest.TestCase):
    """Test trust/health gating."""

    def setUp(self):
        self.registry = NodeRegistry()
        self.local = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(node_id=self.local.node_id, trust_status=NodeTrustStatus.TRUSTED.value)
        self.registry.register_local(self.local, local_trust)

        self.gate = TrustHealthGate(self.registry)

    def test_passes_trusted_healthy(self):
        """Trusted healthy node passes gate."""
        remote = NodeIdentity.create_local("remote", NodeRole.WORKER)
        remote.node_id = "remote-1"
        remote.is_local = False

        trust = NodeTrustState(
            node_id="remote-1",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        self.registry.register_remote(remote, trust)

        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="local",
            target_node_id="remote-1",
            action_type="sync_continuity"
        )

        passed, reason = self.gate.validate(proposal)
        self.assertTrue(passed)
        self.assertIsNone(reason)

    def test_fails_unhealthy(self):
        """Unhealthy node fails gate."""
        remote = NodeIdentity.create_local("remote", NodeRole.WORKER)
        remote.node_id = "remote-1"
        remote.is_local = False

        trust = NodeTrustState(
            node_id="remote-1",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.UNHEALTHY.value
        )
        self.registry.register_remote(remote, trust)

        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="local",
            target_node_id="remote-1",
            action_type="sync_continuity"
        )

        passed, reason = self.gate.validate(proposal)
        self.assertFalse(passed)
        self.assertIsNotNone(reason)
        self.assertEqual(reason.category, RejectionCategory.HEALTH_DEGRADED.value)


class TestProofSafetyHooks(unittest.TestCase):
    """Test safety validation hooks."""

    def test_register_hook(self):
        """Hooks can be registered."""
        hooks = ProofSafetyHooks()

        def test_hook(proposal):
            return True, None

        hooks.register_hook(test_hook)
        self.assertEqual(len(hooks._hooks), 1)

    def test_hook_pass(self):
        """All hooks passing returns success."""
        hooks = ProofSafetyHooks()

        hooks.register_hook(lambda p: (True, None))
        hooks.register_hook(lambda p: (True, None))

        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="local",
            target_node_id="remote",
            action_type="sync_continuity"
        )

        passed, failures = hooks.validate(proposal)
        self.assertTrue(passed)
        self.assertEqual(failures, [])

    def test_hook_fail(self):
        """Any hook failing returns failure."""
        hooks = ProofSafetyHooks()

        hooks.register_hook(lambda p: (True, None))
        hooks.register_hook(lambda p: (False, "Safety check failed"))

        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="local",
            target_node_id="remote",
            action_type="sync_continuity"
        )

        passed, failures = hooks.validate(proposal)
        self.assertFalse(passed)
        self.assertIn("Safety check failed", failures)

    def test_clear_hooks(self):
        """Hooks can be cleared."""
        hooks = ProofSafetyHooks()
        hooks.register_hook(lambda p: (True, None))

        hooks.clear_hooks()
        self.assertEqual(len(hooks._hooks), 0)


class TestApprovalRequirement(unittest.TestCase):
    """Test approval requirements."""

    def setUp(self):
        self.registry = NodeRegistry()
        self.local = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        local_trust = NodeTrustState(node_id=self.local.node_id, trust_status=NodeTrustStatus.TRUSTED.value)
        self.registry.register_local(self.local, local_trust)

    def test_automatic_satisfied(self):
        """Automatic mode with gates cleared is satisfied."""
        req = ApprovalRequirement(mode=ApprovalMode.AUTOMATIC.value)

        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="local",
            target_node_id="remote",
            action_type="sync_continuity",
            approval_mode=ApprovalMode.AUTOMATIC.value
        )
        proposal.submit()
        proposal.start_validation()
        # In automatic mode with no gates, validation success -> APPROVED
        proposal.mark_validated([{"passed": True}])

        # In automatic mode, proposal is already APPROVED after validation
        self.assertEqual(proposal.status, ProposalStatus.APPROVED.value)

    def test_min_approver_count(self):
        """Requires minimum number of approvers."""
        req = ApprovalRequirement(min_approver_count=2)

        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="local",
            target_node_id="remote",
            action_type="sync_continuity"
        )
        proposal.submit()
        proposal.approvals_received = ["approver-1"]

        satisfied, reason = req.is_satisfied(proposal, self.registry)
        self.assertFalse(satisfied)

        proposal.approvals_received.append("approver-2")
        satisfied, reason = req.is_satisfied(proposal, self.registry)
        self.assertTrue(satisfied)


class TestEscalationPath(unittest.TestCase):
    """Test escalation paths."""

    def test_should_escalate_on_category(self):
        """Escalates on matching rejection category."""
        path = EscalationPath(
            path_id="esc-1",
            name="Safety Escalation",
            on_rejection_categories=[RejectionCategory.SAFETY_CHECK_FAILED.value]
        )

        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="local",
            target_node_id="remote",
            action_type="sync_continuity"
        )
        proposal.submit()
        proposal.reject(RejectionReason(
            category=RejectionCategory.SAFETY_CHECK_FAILED.value,
            description="Safety check failed"
        ))

        self.assertTrue(path.should_escalate(proposal))

    def test_should_escalate_manual_review(self):
        """Escalates manual review proposals."""
        path = EscalationPath(
            path_id="esc-1",
            name="Manual Review",
            on_manual_review=True
        )

        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="local",
            target_node_id="remote",
            action_type="sync_continuity",
            approval_mode=ApprovalMode.MANUAL.value
        )
        proposal.submit()

        self.assertTrue(path.should_escalate(proposal))

    def test_no_escalate_already_escalated(self):
        """Does not escalate already escalated proposals."""
        path = EscalationPath(
            path_id="esc-1",
            name="Escalation",
            on_rejection_categories=[RejectionCategory.SAFETY_CHECK_FAILED.value]
        )

        proposal = RemoteActionProposal(
            proposal_id="prop-1",
            proposing_node_id="local",
            target_node_id="remote",
            action_type="sync_continuity"
        )
        proposal.submit()
        proposal.escalate("esc-1", "controller")

        self.assertFalse(path.should_escalate(proposal))


class TestProposalAuditTrace(unittest.TestCase):
    """Test audit trace tracking."""

    def setUp(self):
        self.trace = ProposalAuditTrace("local")

    def test_log_event(self):
        """Events can be logged."""
        event = self.trace.log_event(
            proposal_id="prop-1",
            event_type=AuditEventType.PROPOSAL_CREATED.value,
            details={"action": "sync_continuity"}
        )

        self.assertEqual(event.proposal_id, "prop-1")
        self.assertEqual(event.event_type, AuditEventType.PROPOSAL_CREATED.value)

    def test_get_events(self):
        """Events retrieved by proposal ID."""
        self.trace.log_event("prop-1", AuditEventType.PROPOSAL_CREATED.value)
        self.trace.log_event("prop-1", AuditEventType.PROPOSAL_SUBMITTED.value)
        self.trace.log_event("prop-2", AuditEventType.PROPOSAL_CREATED.value)

        events = self.trace.get_events("prop-1")
        self.assertEqual(len(events), 2)

    def test_get_trace(self):
        """Full trace can be retrieved."""
        self.trace.log_event("prop-1", AuditEventType.PROPOSAL_CREATED.value)
        self.trace.log_event("prop-1", AuditEventType.VALIDATION_PASSED.value)

        trace = self.trace.get_trace("prop-1")
        self.assertEqual(len(trace), 2)
        self.assertEqual(trace[0]["event_type"], AuditEventType.PROPOSAL_CREATED.value)

    def test_get_stats(self):
        """Statistics can be retrieved."""
        self.trace.log_event("prop-1", AuditEventType.PROPOSAL_CREATED.value)
        self.trace.log_event("prop-2", AuditEventType.PROPOSAL_CREATED.value)
        self.trace.log_event("prop-1", AuditEventType.PROPOSAL_SUBMITTED.value)

        stats = self.trace.get_stats()
        self.assertEqual(stats["total_events"], 3)
        self.assertEqual(stats["proposals_tracked"], 2)


if __name__ == "__main__":
    unittest.main()
