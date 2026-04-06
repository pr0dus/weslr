"""Tests for Remote Governance Awareness (v59)

Behavioral tests for distributed governance awareness layer.
"""

import json
import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.remote_governance_awareness import (
    RemoteGovernanceState,
    RemoteComplianceStatus,
    GovernanceDelegation,
    PolicyReference,
    CrossNodePolicyConflict,
    GovernanceAwarenessRegistry,
    PolicyScopeBoundary,
    ConflictDetector,
    GovernanceCapabilityAdvertisement,
    GovernanceScope,
    DelegationStatus,
    ComplianceStatus,
    GovernanceCapability,
    ConflictSeverity,
)


class TestPolicyReference(unittest.TestCase):
    """Test policy reference operations."""

    def test_policy_reference_creation(self):
        """Policy reference stores basic info."""
        ref = PolicyReference(
            policy_id="policy-1",
            policy_version="1.0",
            source_node_id="node-1",
            scope=GovernanceScope.SHARED.value
        )

        self.assertEqual(ref.policy_id, "policy-1")
        self.assertEqual(ref.policy_version, "1.0")
        self.assertEqual(ref.source_node_id, "node-1")
        self.assertEqual(ref.scope, GovernanceScope.SHARED.value)

    def test_policy_reference_serialization(self):
        """Round-trip serialization works."""
        ref = PolicyReference(
            policy_id="policy-1",
            policy_version="1.0",
            source_node_id="node-1",
            scope=GovernanceScope.SHARED.value,
            checksum="abc123"
        )

        data = ref.to_dict()
        restored = PolicyReference.from_dict(data)

        self.assertEqual(restored.policy_id, ref.policy_id)
        self.assertEqual(restored.policy_version, ref.policy_version)
        self.assertEqual(restored.checksum, ref.checksum)


class TestGovernanceDelegation(unittest.TestCase):
    """Test governance delegation lifecycle."""

    def test_delegation_creation(self):
        """Delegation stores basic info."""
        delegation = GovernanceDelegation(
            delegation_id="del-1",
            from_node_id="controller",
            to_node_id="worker",
            delegated_policies=["policy-1"],
            delegated_scope=GovernanceScope.SHARED.value
        )

        self.assertEqual(delegation.from_node_id, "controller")
        self.assertEqual(delegation.to_node_id, "worker")
        self.assertEqual(delegation.status, DelegationStatus.PENDING.value)

    def test_delegation_activation(self):
        """Delegation can be activated."""
        delegation = GovernanceDelegation(
            delegation_id="del-1",
            from_node_id="controller",
            to_node_id="worker"
        )

        self.assertFalse(delegation.is_active())

        delegation.activate()

        self.assertEqual(delegation.status, DelegationStatus.ACTIVE.value)
        self.assertTrue(delegation.is_active())
        self.assertIsNotNone(delegation.effective_at)

    def test_delegation_revocation(self):
        """Delegation can be revoked."""
        delegation = GovernanceDelegation(
            delegation_id="del-1",
            from_node_id="controller",
            to_node_id="worker"
        )
        delegation.activate()

        self.assertTrue(delegation.is_active())

        delegation.revoke("controller", "Testing revocation")

        self.assertEqual(delegation.status, DelegationStatus.REVOKED.value)
        self.assertFalse(delegation.is_active())
        self.assertEqual(delegation.revoked_by, "controller")

    def test_delegation_expiry(self):
        """Expired delegation reports inactive."""
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat().replace("+00:00", "Z")

        delegation = GovernanceDelegation(
            delegation_id="del-1",
            from_node_id="controller",
            to_node_id="worker",
            status=DelegationStatus.ACTIVE.value,
            expires_at=past
        )

        self.assertFalse(delegation.is_active())

    def test_delegation_serialization(self):
        """Round-trip serialization preserves state."""
        delegation = GovernanceDelegation(
            delegation_id="del-1",
            from_node_id="controller",
            to_node_id="worker",
            delegated_policies=["policy-1", "policy-2"]
        )
        delegation.activate()

        data = delegation.to_dict()
        restored = GovernanceDelegation.from_dict(data)

        self.assertEqual(restored.delegation_id, delegation.delegation_id)
        self.assertEqual(restored.delegated_policies, delegation.delegated_policies)
        self.assertEqual(restored.status, delegation.status)


class TestRemoteComplianceStatus(unittest.TestCase):
    """Test compliance status tracking."""

    def test_compliance_defaults(self):
        """Compliance defaults to unknown."""
        status = RemoteComplianceStatus(node_id="node-1")

        self.assertEqual(status.status, ComplianceStatus.UNKNOWN.value)
        self.assertEqual(status.violations, [])

    def test_mark_compliant(self):
        """Can mark as compliant."""
        status = RemoteComplianceStatus(node_id="node-1")
        status.mark_compliant()

        self.assertEqual(status.status, ComplianceStatus.COMPLIANT.value)
        self.assertIsNotNone(status.reported_at)

    def test_mark_non_compliant(self):
        """Can mark as non-compliant with violations."""
        status = RemoteComplianceStatus(node_id="node-1")
        violations = [{"rule": "r1", "message": "Violation"}]
        status.mark_non_compliant(violations)

        self.assertEqual(status.status, ComplianceStatus.NON_COMPLIANT.value)
        self.assertEqual(status.violations, violations)

    def test_compliance_staleness(self):
        """Old compliance status is stale."""
        old_time = (datetime.now(timezone.utc) - timedelta(seconds=400)).isoformat().replace("+00:00", "Z")
        status = RemoteComplianceStatus(node_id="node-1", reported_at=old_time)

        self.assertTrue(status.is_stale(max_age_seconds=300))
        self.assertFalse(status.is_stale(max_age_seconds=500))

    def test_compliance_serialization(self):
        """Round-trip serialization works."""
        status = RemoteComplianceStatus(node_id="node-1")
        status.mark_compliant()

        data = status.to_dict()
        restored = RemoteComplianceStatus.from_dict(data)

        self.assertEqual(restored.node_id, status.node_id)
        self.assertEqual(restored.status, status.status)


class TestRemoteGovernanceState(unittest.TestCase):
    """Test remote governance state."""

    def test_remote_state_creation(self):
        """Remote state stores policies and delegations."""
        state = RemoteGovernanceState(
            node_id="remote-1",
            active_policies=[
                PolicyReference("p1", "1.0", "remote-1", GovernanceScope.SHARED.value)
            ],
            advertised_capabilities=[GovernanceCapability.POLICY_ENFORCEMENT.value]
        )

        self.assertEqual(state.node_id, "remote-1")
        self.assertEqual(len(state.active_policies), 1)
        self.assertTrue(state.has_capability(GovernanceCapability.POLICY_ENFORCEMENT.value))

    def test_remote_state_staleness(self):
        """Old snapshots are stale."""
        old_time = (datetime.now(timezone.utc) - timedelta(seconds=400)).isoformat().replace("+00:00", "Z")
        state = RemoteGovernanceState(node_id="remote-1", snapshot_at=old_time)

        self.assertTrue(state.is_stale(max_age_seconds=300))

    def test_get_delegation_to(self):
        """Can find delegation to specific node."""
        delegation = GovernanceDelegation(
            delegation_id="del-1",
            from_node_id="remote-1",
            to_node_id="local-1",
            status=DelegationStatus.ACTIVE.value
        )

        state = RemoteGovernanceState(
            node_id="remote-1",
            incoming_delegations=[delegation]
        )

        found = state.get_delegation_to("local-1")
        self.assertIsNotNone(found)
        self.assertEqual(found.delegation_id, "del-1")

    def test_get_active_delegations_from(self):
        """Can find active delegations from node."""
        active = GovernanceDelegation(
            delegation_id="del-1",
            from_node_id="local-1",
            to_node_id="remote-1",
            status=DelegationStatus.ACTIVE.value
        )
        pending = GovernanceDelegation(
            delegation_id="del-2",
            from_node_id="local-1",
            to_node_id="remote-2",
            status=DelegationStatus.PENDING.value
        )

        state = RemoteGovernanceState(
            node_id="remote-1",
            active_delegations=[active, pending]
        )

        found = state.get_active_delegations_from("local-1")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].delegation_id, "del-1")

    def test_remote_state_serialization(self):
        """Round-trip serialization works."""
        state = RemoteGovernanceState(
            node_id="remote-1",
            active_policies=[
                PolicyReference("p1", "1.0", "remote-1", GovernanceScope.SHARED.value)
            ],
            advertised_capabilities=[GovernanceCapability.AUDIT_LOGGING.value]
        )

        data = state.to_dict()
        restored = RemoteGovernanceState.from_dict(data)

        self.assertEqual(restored.node_id, state.node_id)
        self.assertEqual(len(restored.active_policies), 1)
        self.assertEqual(restored.advertised_capabilities, state.advertised_capabilities)


class TestPolicyScopeBoundary(unittest.TestCase):
    """Test policy scope resolution."""

    def test_shared_applies_to_all(self):
        """Shared scope applies to all nodes."""
        boundary = PolicyScopeBoundary("local-1")

        policy = PolicyReference("p1", "1.0", "controller", GovernanceScope.SHARED.value)

        self.assertTrue(boundary.applies_to(policy, "node-1"))
        self.assertTrue(boundary.applies_to(policy, "node-2"))

    def test_local_only_applies_to_source(self):
        """Local scope only applies to source node."""
        boundary = PolicyScopeBoundary("local-1")

        policy = PolicyReference("p1", "1.0", "node-1", GovernanceScope.LOCAL.value)

        self.assertTrue(boundary.applies_to(policy, "node-1"))
        self.assertFalse(boundary.applies_to(policy, "node-2"))

    def test_delegated_scope_resolved(self):
        """Delegated scope is preserved."""
        boundary = PolicyScopeBoundary("local-1")

        policy = PolicyReference("p1", "1.0", "controller", GovernanceScope.DELEGATED.value)

        self.assertEqual(
            boundary.resolve_scope(policy, "worker"),
            GovernanceScope.DELEGATED.value
        )

    def test_scope_override(self):
        """Scope can be overridden."""
        boundary = PolicyScopeBoundary("local-1")
        boundary.set_scope_override("p1", GovernanceScope.SHARED.value)

        policy = PolicyReference("p1", "1.0", "node-1", GovernanceScope.LOCAL.value)

        self.assertEqual(
            boundary.resolve_scope(policy, "node-2"),
            GovernanceScope.SHARED.value
        )


class TestConflictDetector(unittest.TestCase):
    """Test conflict detection."""

    def test_no_conflict_identical(self):
        """Identical policies have no conflict."""
        detector = ConflictDetector("local-1")

        local_policies = [
            PolicyReference("p1", "1.0", "local-1", GovernanceScope.SHARED.value)
        ]

        remote_state = RemoteGovernanceState(
            node_id="remote-1",
            active_policies=[
                PolicyReference("p1", "1.0", "local-1", GovernanceScope.SHARED.value)
            ]
        )

        conflicts = detector.detect_conflicts(local_policies, remote_state)
        self.assertEqual(len(conflicts), 0)

    def test_version_drift_detected(self):
        """Version mismatch creates conflict."""
        detector = ConflictDetector("local-1")

        local_policies = [
            PolicyReference("p1", "1.0", "local-1", GovernanceScope.SHARED.value)
        ]

        remote_state = RemoteGovernanceState(
            node_id="remote-1",
            active_policies=[
                PolicyReference("p1", "2.0", "local-1", GovernanceScope.SHARED.value)
            ]
        )

        conflicts = detector.detect_conflicts(local_policies, remote_state)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].conflict_type, "version_drift")

    def test_missing_on_remote_detected(self):
        """Missing shared policy on remote creates conflict."""
        detector = ConflictDetector("local-1")

        local_policies = [
            PolicyReference("p1", "1.0", "local-1", GovernanceScope.SHARED.value)
        ]

        remote_state = RemoteGovernanceState(
            node_id="remote-1",
            active_policies=[]
        )

        conflicts = detector.detect_conflicts(local_policies, remote_state)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].conflict_type, "missing_on_remote")

    def test_local_only_no_conflict(self):
        """Local-only policies don't create conflicts."""
        detector = ConflictDetector("local-1")

        local_policies = [
            PolicyReference("p1", "1.0", "local-1", GovernanceScope.LOCAL.value)
        ]

        remote_state = RemoteGovernanceState(
            node_id="remote-1",
            active_policies=[]
        )

        conflicts = detector.detect_conflicts(local_policies, remote_state)
        self.assertEqual(len(conflicts), 0)


class TestGovernanceAwarenessRegistry(unittest.TestCase):
    """Test governance awareness registry."""

    def setUp(self):
        self.registry = GovernanceAwarenessRegistry("local-1")

    def test_update_remote_state(self):
        """Can update and retrieve remote state."""
        state = RemoteGovernanceState(
            node_id="remote-1",
            active_policies=[
                PolicyReference("p1", "1.0", "controller", GovernanceScope.SHARED.value)
            ]
        )

        self.registry.update_remote_state(state)

        retrieved = self.registry.get_remote_state("remote-1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.node_id, "remote-1")

    def test_get_stale_states(self):
        """Can identify stale states."""
        old_time = (datetime.now(timezone.utc) - timedelta(seconds=400)).isoformat().replace("+00:00", "Z")

        fresh_state = RemoteGovernanceState(node_id="fresh-1")
        stale_state = RemoteGovernanceState(node_id="stale-1", snapshot_at=old_time)

        self.registry.update_remote_state(fresh_state)
        self.registry.update_remote_state(stale_state)

        stale = self.registry.get_stale_states(max_age_seconds=300)
        self.assertIn("stale-1", stale)
        self.assertNotIn("fresh-1", stale)

    def test_compliance_tracking(self):
        """Can track compliance status."""
        status = RemoteComplianceStatus(node_id="remote-1")
        status.mark_compliant()

        self.registry.update_compliance(status)

        retrieved = self.registry.get_compliance("remote-1")
        self.assertEqual(retrieved.status, ComplianceStatus.COMPLIANT.value)

    def test_get_non_compliant_nodes(self):
        """Can identify non-compliant nodes."""
        compliant = RemoteComplianceStatus(node_id="compliant-1")
        compliant.mark_compliant()

        non_compliant = RemoteComplianceStatus(node_id="bad-1")
        non_compliant.mark_non_compliant([{"rule": "r1"}])

        self.registry.update_compliance(compliant)
        self.registry.update_compliance(non_compliant)

        bad_nodes = self.registry.get_non_compliant_nodes()
        self.assertIn("bad-1", bad_nodes)
        self.assertNotIn("compliant-1", bad_nodes)

    def test_delegation_tracking(self):
        """Can track delegations."""
        delegation = GovernanceDelegation(
            delegation_id="del-1",
            from_node_id="controller",
            to_node_id="local-1",
            status=DelegationStatus.ACTIVE.value
        )

        self.registry.register_delegation(delegation)

        retrieved = self.registry.get_delegation("del-1")
        self.assertEqual(retrieved.delegation_id, "del-1")

        active = self.registry.get_active_delegations()
        self.assertEqual(len(active), 1)

    def test_conflict_detection(self):
        """Can detect conflicts across remote nodes."""
        local_policies = [
            PolicyReference("p1", "1.0", "local-1", GovernanceScope.SHARED.value)
        ]

        remote_state = RemoteGovernanceState(
            node_id="remote-1",
            active_policies=[
                PolicyReference("p1", "2.0", "local-1", GovernanceScope.SHARED.value)
            ]
        )

        self.registry.update_remote_state(remote_state)

        conflicts = self.registry.detect_conflicts(local_policies)
        self.assertEqual(len(conflicts), 1)

    def test_conflict_resolution(self):
        """Can mark conflicts as resolved."""
        conflict = CrossNodePolicyConflict(
            conflict_id="c1",
            local_policy=None,
            remote_policy=None,
            remote_node_id="remote-1"
        )
        self.registry._conflicts["c1"] = conflict

        result = self.registry.resolve_conflict("c1", "accept_remote")
        self.assertTrue(result)
        self.assertTrue(conflict.resolved)
        self.assertEqual(conflict.resolution_action, "accept_remote")

    def test_get_applicable_policies(self):
        """Can get policies applicable to a node."""
        remote_state = RemoteGovernanceState(
            node_id="remote-1",
            active_policies=[
                PolicyReference("p1", "1.0", "remote-1", GovernanceScope.SHARED.value),
                PolicyReference("p2", "1.0", "remote-1", GovernanceScope.LOCAL.value)
            ]
        )

        self.registry.update_remote_state(remote_state)

        applicable = self.registry.get_applicable_policies("local-1")
        self.assertEqual(len(applicable), 1)  # Only shared applies
        self.assertEqual(applicable[0].policy_id, "p1")

    def test_registry_summary(self):
        """Can get summary of registry state."""
        state = RemoteGovernanceState(node_id="remote-1")
        self.registry.update_remote_state(state)

        summary = self.registry.get_summary()
        self.assertEqual(summary["tracked_nodes"], 1)


class TestGovernanceCapabilityAdvertisement(unittest.TestCase):
    """Test capability advertisement."""

    def test_add_capability(self):
        """Can add capabilities."""
        adv = GovernanceCapabilityAdvertisement("node-1")
        adv.add_capability(GovernanceCapability.AUDIT_LOGGING.value)

        self.assertTrue(adv.has_capability(GovernanceCapability.AUDIT_LOGGING.value))
        self.assertIn(GovernanceCapability.AUDIT_LOGGING.value, adv.get_capabilities())

    def test_remove_capability(self):
        """Can remove capabilities."""
        adv = GovernanceCapabilityAdvertisement("node-1")
        adv.add_capability(GovernanceCapability.AUDIT_LOGGING.value)
        adv.remove_capability(GovernanceCapability.AUDIT_LOGGING.value)

        self.assertFalse(adv.has_capability(GovernanceCapability.AUDIT_LOGGING.value))

    def test_default_worker_capabilities(self):
        """Worker has minimal capabilities."""
        adv = GovernanceCapabilityAdvertisement.create_default("worker-1", "worker")

        self.assertTrue(adv.has_capability(GovernanceCapability.COMPLIANCE_REPORTING.value))
        self.assertTrue(adv.has_capability(GovernanceCapability.AUDIT_LOGGING.value))
        self.assertFalse(adv.has_capability(GovernanceCapability.POLICY_ENFORCEMENT.value))

    def test_default_controller_capabilities(self):
        """Controller has full capabilities."""
        adv = GovernanceCapabilityAdvertisement.create_default("ctrl-1", "controller")

        self.assertTrue(adv.has_capability(GovernanceCapability.POLICY_ENFORCEMENT.value))
        self.assertTrue(adv.has_capability(GovernanceCapability.DELEGATION_ACCEPTANCE.value))
        self.assertTrue(adv.has_capability(GovernanceCapability.POLICY_SUGGESTION.value))

    def test_advertisement_payload(self):
        """Advertisement creates valid payload."""
        adv = GovernanceCapabilityAdvertisement("node-1")
        adv.add_capability(GovernanceCapability.AUDIT_LOGGING.value, {"version": "1.0"})

        payload = adv.to_advertisement()

        self.assertEqual(payload["node_id"], "node-1")
        self.assertIn(GovernanceCapability.AUDIT_LOGGING.value, payload["capabilities"])
        self.assertIsNotNone(payload["advertised_at"])


if __name__ == "__main__":
    unittest.main()
