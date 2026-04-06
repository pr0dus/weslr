"""Tests for Cross-Instance Continuity Sync (v58)

Behavioral tests for continuity synchronization layer.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.continuity_sync import (
    ContinuitySyncState,
    ContinuitySyncEngine,
    SyncEligibility,
    SyncEligibilityRule,
    SyncTrustBoundary,
    ConflictResolver,
    DegradedPartitionMode,
    SyncStatus,
    SyncConflictResolution,
    PartitionMode,
    StateSyncability,
)
from weslr.node_identity import (
    NodeIdentity,
    NodeTrustState,
    NodeRole,
    NodeTrustStatus,
    NodeHealthStatus
)
from weslr.unified_continuity import ContinuityScope


class TestSyncEligibility(unittest.TestCase):
    """Test sync eligibility rules."""
    
    def test_session_scope_never_syncs(self):
        """Session scope is local-only."""
        eligibility = SyncEligibility.get_default_eligibility()
        
        trust = NodeTrustState(
            node_id="test",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        
        eligible, reason = eligibility.check_eligibility(
            ContinuityScope.SESSION.value,
            trust,
            0
        )
        
        self.assertFalse(eligible)
        self.assertIn("local-only", reason.lower())
    
    def test_household_scope_requires_trust(self):
        """Household scope requires trusted node."""
        eligibility = SyncEligibility.get_default_eligibility()
        
        # Trusted node should succeed
        trusted = NodeTrustState(
            node_id="test",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        eligible, _ = eligibility.check_eligibility(
            ContinuityScope.HOUSEHOLD.value,
            trusted,
            0
        )
        self.assertTrue(eligible)
        
        # Provisional should fail
        provisional = NodeTrustState(
            node_id="test",
            trust_status=NodeTrustStatus.PROVISIONAL.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        eligible, reason = eligibility.check_eligibility(
            ContinuityScope.HOUSEHOLD.value,
            provisional,
            0
        )
        self.assertFalse(eligible)
        self.assertIn("trust", reason.lower())
    
    def test_working_scope_accepts_provisional(self):
        """Working scope accepts provisional trust."""
        eligibility = SyncEligibility.get_default_eligibility()
        
        provisional = NodeTrustState(
            node_id="test",
            trust_status=NodeTrustStatus.PROVISIONAL.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        eligible, _ = eligibility.check_eligibility(
            ContinuityScope.WORKING.value,
            provisional,
            0
        )
        self.assertTrue(eligible)
    
    def test_unhealthy_node_blocked(self):
        """Unhealthy nodes cannot sync."""
        eligibility = SyncEligibility.get_default_eligibility()
        
        unhealthy = NodeTrustState(
            node_id="test",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.UNHEALTHY.value
        )
        eligible, reason = eligibility.check_eligibility(
            ContinuityScope.HOUSEHOLD.value,
            unhealthy,
            0
        )
        self.assertFalse(eligible)
        self.assertIn("health", reason.lower())
    
    def test_stale_state_blocked(self):
        """Stale state is blocked by max age."""
        eligibility = SyncEligibility()
        eligibility.set_rule("test", SyncEligibilityRule(
            scope="test",
            syncability=StateSyncability.SYNCABLE.value,
            max_sync_age_seconds=60
        ))
        
        trust = NodeTrustState(
            node_id="test",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        
        # Fresh state
        eligible, _ = eligibility.check_eligibility("test", trust, 30)
        self.assertTrue(eligible)
        
        # Stale state
        eligible, reason = eligibility.check_eligibility("test", trust, 120)
        self.assertFalse(eligible)
        self.assertIn("age", reason.lower())
    
    def test_is_syncable_quick_check(self):
        """Quick syncability check works."""
        eligibility = SyncEligibility.get_default_eligibility()
        
        self.assertFalse(eligibility.is_syncable(ContinuityScope.SESSION.value))
        self.assertTrue(eligibility.is_syncable(ContinuityScope.HOUSEHOLD.value))


class TestSyncTrustBoundary(unittest.TestCase):
    """Test sync trust boundaries."""
    
    def test_can_push_to_trusted(self):
        """Can push to trusted healthy node."""
        boundary = SyncTrustBoundary(local_node_id="local")
        
        target = NodeTrustState(
            node_id="remote",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        
        can_push, _ = boundary.can_push_to(target)
        self.assertTrue(can_push)
    
    def test_can_push_rejected_for_pending(self):
        """Cannot push to pending trust node."""
        boundary = SyncTrustBoundary(local_node_id="local")
        
        target = NodeTrustState(
            node_id="remote",
            trust_status=NodeTrustStatus.PENDING.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        
        can_push, reason = boundary.can_push_to(target)
        self.assertFalse(can_push)
        self.assertIn("trust", reason.lower())
    
    def test_can_pull_requires_higher_trust(self):
        """Pull requires higher trust than push by default."""
        boundary = SyncTrustBoundary(local_node_id="local")
        
        provisional = NodeTrustState(
            node_id="remote",
            trust_status=NodeTrustStatus.PROVISIONAL.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        
        # Can push to provisional
        can_push, _ = boundary.can_push_to(provisional)
        self.assertTrue(can_push)
        
        # Cannot pull from provisional
        can_pull, reason = boundary.can_pull_from(provisional)
        self.assertFalse(can_pull)
        self.assertIn("trust", reason.lower())
    
    def test_deny_list_blocks(self):
        """Denied nodes cannot sync."""
        boundary = SyncTrustBoundary(
            local_node_id="local",
            denied_nodes={"untrusted-node"}
        )
        
        target = NodeTrustState(
            node_id="untrusted-node",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        
        can_push, reason = boundary.can_push_to(target)
        self.assertFalse(can_push)
        self.assertIn("deny", reason.lower())
    
    def test_allow_list_restricts(self):
        """Allow list restricts sync to listed nodes."""
        boundary = SyncTrustBoundary(
            local_node_id="local",
            allowed_nodes={"allowed-node"}
        )
        
        allowed = NodeTrustState(
            node_id="allowed-node",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        blocked = NodeTrustState(
            node_id="blocked-node",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        
        self.assertTrue(boundary.can_push_to(allowed)[0])
        self.assertFalse(boundary.can_push_to(blocked)[0])
    
    def test_mutual_trust_required(self):
        """Mutual trust requires both directions."""
        boundary = SyncTrustBoundary(
            local_node_id="local",
            min_outbound_trust=NodeTrustStatus.PROVISIONAL.value,
            min_inbound_trust=NodeTrustStatus.TRUSTED.value,
            require_mutual_trust=True
        )
        
        # Provisional trust - can push but not pull
        provisional = NodeTrustState(
            node_id="remote",
            trust_status=NodeTrustStatus.PROVISIONAL.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        
        # Can do single-direction but not mutual
        can_sync, reason = boundary.can_sync_with(provisional)
        self.assertFalse(can_sync)
        self.assertIn("mutual", reason.lower())
        
        # Trusted - both directions work
        trusted = NodeTrustState(
            node_id="remote",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        can_sync, _ = boundary.can_sync_with(trusted)
        self.assertTrue(can_sync)
    
    def test_no_mutual_trust_allows_single_direction(self):
        """Without mutual trust requirement, single direction allowed."""
        boundary = SyncTrustBoundary(
            local_node_id="local",
            min_outbound_trust=NodeTrustStatus.PROVISIONAL.value,
            min_inbound_trust=NodeTrustStatus.TRUSTED.value,
            require_mutual_trust=False
        )
        
        provisional = NodeTrustState(
            node_id="remote",
            trust_status=NodeTrustStatus.PROVISIONAL.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        
        # Can sync (one direction)
        can_sync, _ = boundary.can_sync_with(provisional)
        self.assertTrue(can_sync)


class TestContinuitySyncState(unittest.TestCase):
    """Test sync state operations."""
    
    def test_compute_hash(self):
        """Hash computed from payload."""
        state = ContinuitySyncState(
            sync_id="test:1:123",
            continuity_id="cont-1",
            scope="household",
            payload={"key": "value", "num": 42}
        )
        
        hash1 = state.compute_hash()
        hash2 = state.compute_hash()
        
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA256 hex
    
    def test_hash_changes_with_payload(self):
        """Hash changes when payload changes."""
        state = ContinuitySyncState(
            sync_id="test:1:123",
            continuity_id="cont-1",
            scope="household",
            payload={"key": "value"}
        )
        
        hash1 = state.compute_hash()
        state.payload["key"] = "changed"
        hash2 = state.compute_hash()
        
        self.assertNotEqual(hash1, hash2)
    
    def test_validate_hash(self):
        """Hash validation detects tampering."""
        state = ContinuitySyncState(
            sync_id="test:1:123",
            continuity_id="cont-1",
            scope="household",
            payload={"key": "value"}
        )
        state.payload_hash = state.compute_hash()
        
        # Valid
        self.assertTrue(state.validate_hash())
        
        # Tampered
        state.payload["key"] = "changed"
        self.assertFalse(state.validate_hash())
    
    def test_staleness_detection(self):
        """Stale state detected by age."""
        from datetime import datetime, timezone, timedelta
        
        # Fresh state
        state = ContinuitySyncState(
            sync_id="test:1:123",
            continuity_id="cont-1",
            scope="household",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
        self.assertFalse(state.is_stale(max_age_seconds=300))
        
        # Old state
        old_time = (datetime.now(timezone.utc) - timedelta(seconds=400)).isoformat().replace("+00:00", "Z")
        state.timestamp = old_time
        self.assertTrue(state.is_stale(max_age_seconds=300))
    
    def test_mark_synced(self):
        """Marking synced updates targets and status."""
        state = ContinuitySyncState(
            sync_id="test:1:123",
            continuity_id="cont-1",
            scope="household"
        )
        
        self.assertEqual(state.status, SyncStatus.PENDING.value)
        self.assertEqual(len(state.sync_targets), 0)
        
        state.mark_synced("remote-node-1")
        
        self.assertEqual(state.status, SyncStatus.SYNCED.value)
        self.assertIn("remote-node-1", state.sync_targets)
        self.assertIsNotNone(state.last_sync_at)
    
    def test_serialization(self):
        """Round-trip serialization works."""
        original = ContinuitySyncState(
            sync_id="test:1:123",
            continuity_id="cont-1",
            scope="household",
            payload={"data": "value"},
            source_node_id="local",
            sync_targets=["remote-1"],
            status=SyncStatus.SYNCED.value
        )
        original.payload_hash = original.compute_hash()
        
        data = original.to_dict()
        restored = ContinuitySyncState.from_dict(data)
        
        self.assertEqual(restored.sync_id, original.sync_id)
        self.assertEqual(restored.continuity_id, original.continuity_id)
        self.assertEqual(restored.payload, original.payload)
        self.assertEqual(restored.sync_targets, original.sync_targets)


class TestConflictResolver(unittest.TestCase):
    """Test conflict resolution strategies."""
    
    def setUp(self):
        self.resolver = ConflictResolver()
        
        self.local = ContinuitySyncState(
            sync_id="local:1:100",
            continuity_id="cont-1",
            scope="household",
            payload={"value": 1},
            version=1,
            timestamp="2026-04-06T10:00:00Z"
        )
        self.local.payload_hash = self.local.compute_hash()
        
        self.remote = ContinuitySyncState(
            sync_id="remote:1:200",
            continuity_id="cont-1",
            scope="household",
            payload={"value": 2},
            version=2,
            timestamp="2026-04-06T11:00:00Z"
        )
        self.remote.payload_hash = self.remote.compute_hash()
    
    def test_no_conflict_identical(self):
        """Identical states have no conflict."""
        remote_same = ContinuitySyncState(
            sync_id="remote:1:200",
            continuity_id="cont-1",
            scope="household",
            payload={"value": 1},
            version=1,
            timestamp="2026-04-06T10:00:00Z"
        )
        remote_same.payload_hash = remote_same.compute_hash()
        
        has_conflict = self.resolver.detect_conflict(self.local, remote_same)
        self.assertFalse(has_conflict)
    
    def test_conflict_detected(self):
        """Different versions/hashes indicate conflict."""
        has_conflict = self.resolver.detect_conflict(self.local, self.remote)
        self.assertTrue(has_conflict)
    
    def test_source_wins_strategy(self):
        """Source wins strategy selects remote."""
        winner, reason = self.resolver.resolve(
            self.local,
            self.remote,
            SyncConflictResolution.SOURCE_WINS.value
        )
        
        self.assertEqual(winner.sync_id, self.remote.sync_id)
        self.assertEqual(reason, "source_wins")
    
    def test_target_wins_strategy(self):
        """Target wins strategy selects local."""
        winner, reason = self.resolver.resolve(
            self.local,
            self.remote,
            SyncConflictResolution.TARGET_WINS.value
        )
        
        self.assertEqual(winner.sync_id, self.local.sync_id)
        self.assertEqual(reason, "target_wins")
    
    def test_timestamp_wins_strategy(self):
        """Timestamp wins strategy selects newer."""
        winner, reason = self.resolver.resolve(
            self.local,
            self.remote,
            SyncConflictResolution.TIMESTAMP_WINS.value
        )
        
        # Remote is newer
        self.assertEqual(winner.sync_id, self.remote.sync_id)
        self.assertEqual(reason, "timestamp_wins_remote")
    
    def test_timestamp_wins_local_when_newer(self):
        """Timestamp wins selects local when local is newer."""
        local_newer = ContinuitySyncState(
            sync_id="local:1:100",
            continuity_id="cont-1",
            scope="household",
            payload={"value": 1},
            version=2,
            timestamp="2026-04-06T12:00:00Z"
        )
        local_newer.payload_hash = local_newer.compute_hash()
        
        winner, reason = self.resolver.resolve(
            local_newer,
            self.remote,
            SyncConflictResolution.TIMESTAMP_WINS.value
        )
        
        self.assertEqual(winner.sync_id, local_newer.sync_id)
        self.assertEqual(reason, "timestamp_wins_local")
    
    def test_manual_strategy_marks_conflict(self):
        """Manual strategy leaves conflict for resolution."""
        winner, reason = self.resolver.resolve(
            self.local,
            self.remote,
            SyncConflictResolution.MANUAL.value
        )
        
        self.assertEqual(winner.status, SyncStatus.CONFLICT.value)
        self.assertEqual(reason, "manual_resolution_required")


class TestDegradedPartitionMode(unittest.TestCase):
    """Test partition mode handling."""
    
    def test_full_mode_allows_sync(self):
        """Full mode allows all sync."""
        mode = DegradedPartitionMode(mode=PartitionMode.FULL.value)
        
        self.assertTrue(mode.is_sync_allowed())
        self.assertTrue(mode.is_full_sync_allowed())
        self.assertFalse(mode.should_queue_sync())
    
    def test_degraded_mode_allows_limited_sync(self):
        """Degraded mode allows limited sync."""
        mode = DegradedPartitionMode(mode=PartitionMode.DEGRADED.value)
        
        self.assertTrue(mode.is_sync_allowed())
        self.assertFalse(mode.is_full_sync_allowed())
        self.assertTrue(mode.should_queue_sync())
    
    def test_isolated_mode_blocks_sync(self):
        """Isolated mode blocks sync."""
        mode = DegradedPartitionMode(mode=PartitionMode.ISOLATED.value)
        
        self.assertFalse(mode.is_sync_allowed())
        self.assertFalse(mode.is_full_sync_allowed())
        self.assertTrue(mode.should_queue_sync())
    
    def test_mode_transition(self):
        """Mode can transition to new state."""
        mode = DegradedPartitionMode(mode=PartitionMode.FULL.value)
        
        new_mode = mode.transition_to(PartitionMode.DEGRADED.value)
        
        self.assertEqual(new_mode.mode, PartitionMode.DEGRADED.value)
        self.assertEqual(mode.mode, PartitionMode.FULL.value)  # Original unchanged


class TestContinuitySyncEngine(unittest.TestCase):
    """Test sync engine integration."""
    
    def setUp(self):
        self.local_identity = NodeIdentity.create_local("local", NodeRole.CONTROLLER)
        self.engine = ContinuitySyncEngine(self.local_identity)
    
    def test_prepare_sync_state_eligible(self):
        """Can prepare sync state for eligible scope."""
        state = self.engine.prepare_sync_state(
            continuity_id="cont-1",
            scope=ContinuityScope.HOUSEHOLD.value,
            payload={"data": "value"},
            target_nodes=["remote-1"]
        )
        
        self.assertIsNotNone(state)
        self.assertEqual(state.continuity_id, "cont-1")
        self.assertEqual(state.scope, ContinuityScope.HOUSEHOLD.value)
        self.assertIn("remote-1", state.sync_targets)
        self.assertTrue(state.payload_hash)
    
    def test_prepare_sync_state_ineligible(self):
        """Cannot prepare sync state for ineligible scope."""
        state = self.engine.prepare_sync_state(
            continuity_id="cont-1",
            scope=ContinuityScope.SESSION.value,  # Local-only
            payload={"data": "value"},
            target_nodes=["remote-1"]
        )
        
        self.assertIsNone(state)
    
    def test_validate_inbound_sync(self):
        """Inbound sync validated against trust."""
        sync_state = ContinuitySyncState(
            sync_id="remote:1:123",
            continuity_id="cont-1",
            scope=ContinuityScope.HOUSEHOLD.value,
            payload={"data": "value"},
            source_node_id="remote-1"
        )
        sync_state.payload_hash = sync_state.compute_hash()
        
        trusted = NodeTrustState(
            node_id="remote-1",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        
        valid, reason = self.engine.validate_inbound_sync(sync_state, trusted)
        self.assertTrue(valid)
    
    def test_validate_inbound_rejects_untrusted(self):
        """Inbound sync rejected for untrusted node."""
        sync_state = ContinuitySyncState(
            sync_id="remote:1:123",
            continuity_id="cont-1",
            scope=ContinuityScope.HOUSEHOLD.value,
            payload={"data": "value"}
        )
        
        untrusted = NodeTrustState(
            node_id="remote-1",
            trust_status=NodeTrustStatus.UNTRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        
        valid, reason = self.engine.validate_inbound_sync(sync_state, untrusted)
        self.assertFalse(valid)
        self.assertIn("trust", reason.lower())
    
    def test_validate_inbound_rejects_stale(self):
        """Inbound sync rejected for stale state."""
        from datetime import datetime, timezone, timedelta
        
        old_time = (datetime.now(timezone.utc) - timedelta(seconds=400)).isoformat().replace("+00:00", "Z")
        sync_state = ContinuitySyncState(
            sync_id="remote:1:123",
            continuity_id="cont-1",
            scope=ContinuityScope.HOUSEHOLD.value,
            payload={"data": "value"},
            timestamp=old_time
        )
        
        trusted = NodeTrustState(
            node_id="remote-1",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        
        valid, reason = self.engine.validate_inbound_sync(sync_state, trusted)
        self.assertFalse(valid)
        self.assertIn("stale", reason.lower())
    
    def test_handle_inbound_no_conflict(self):
        """Inbound sync accepted when no conflict."""
        remote_state = ContinuitySyncState(
            sync_id="remote:1:123",
            continuity_id="cont-1",
            scope=ContinuityScope.HOUSEHOLD.value,
            payload={"data": "remote"},
            source_node_id="remote-1",
            version=1
        )
        remote_state.payload_hash = remote_state.compute_hash()
        
        trusted = NodeTrustState(
            node_id="remote-1",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        
        status, resolved = self.engine.handle_inbound_sync(remote_state, None, trusted)
        
        self.assertEqual(status, SyncStatus.SYNCED)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.payload, {"data": "remote"})
    
    def test_handle_inbound_conflict_resolved(self):
        """Inbound conflict resolved by strategy - using SOURCE_WINS."""
        from datetime import datetime, timezone
        from weslr.continuity_sync import ConflictResolver

        # Use current timestamps so they pass staleness check
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Create fresh engine with SOURCE_WINS strategy (explicit)
        engine = ContinuitySyncEngine(
            self.local_identity,
            conflict_resolver=ConflictResolver(SyncConflictResolution.SOURCE_WINS.value)
        )

        local_state = ContinuitySyncState(
            sync_id="local:1:100",
            continuity_id="cont-1",
            scope=ContinuityScope.HOUSEHOLD.value,
            payload={"data": "local"},
            source_node_id="local",
            version=1,
            timestamp=now
        )
        local_state.payload_hash = local_state.compute_hash()

        remote_state = ContinuitySyncState(
            sync_id="remote:1:200",
            continuity_id="cont-1",
            scope=ContinuityScope.HOUSEHOLD.value,
            payload={"data": "remote"},
            source_node_id="remote-1",
            version=2,
            timestamp=now
        )
        remote_state.payload_hash = remote_state.compute_hash()

        trusted = NodeTrustState(
            node_id="remote-1",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )

        status, resolved = engine.handle_inbound_sync(remote_state, local_state, trusted)

        # Source wins - remote should be accepted
        self.assertEqual(status, SyncStatus.SYNCED)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.payload, {"data": "remote"})
    
    def test_partition_mode_blocks_sync(self):
        """Sync blocked in isolated mode."""
        self.engine.set_partition_mode(PartitionMode.ISOLATED.value)
        
        sync_state = ContinuitySyncState(
            sync_id="remote:1:123",
            continuity_id="cont-1",
            scope=ContinuityScope.HOUSEHOLD.value,
            payload={"data": "value"}
        )
        
        trusted = NodeTrustState(
            node_id="remote-1",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        
        valid, reason = self.engine.validate_inbound_sync(sync_state, trusted)
        self.assertFalse(valid)
        self.assertIn("isolated", reason.lower())
    
    def test_conflict_tracking(self):
        """Conflicts tracked for manual resolution."""
        engine = ContinuitySyncEngine(
            self.local_identity,
            conflict_resolver=ConflictResolver(SyncConflictResolution.MANUAL.value)
        )
        
        local_state = ContinuitySyncState(
            sync_id="local:1:100",
            continuity_id="cont-1",
            scope=ContinuityScope.HOUSEHOLD.value,
            payload={"data": "local"},
            source_node_id="local",
            version=1
        )
        local_state.payload_hash = local_state.compute_hash()
        
        remote_state = ContinuitySyncState(
            sync_id="remote:1:200",
            continuity_id="cont-1",
            scope=ContinuityScope.HOUSEHOLD.value,
            payload={"data": "remote"},
            source_node_id="remote-1",
            version=2
        )
        remote_state.payload_hash = remote_state.compute_hash()
        
        trusted = NodeTrustState(
            node_id="remote-1",
            trust_status=NodeTrustStatus.TRUSTED.value,
            health_status=NodeHealthStatus.HEALTHY.value
        )
        
        status, _ = engine.handle_inbound_sync(remote_state, local_state, trusted)
        
        self.assertEqual(status, SyncStatus.CONFLICT)
        self.assertIn("cont-1", engine.get_conflicts())
        
        # Resolve
        resolved = engine.resolve_conflict("cont-1", local_state)
        self.assertTrue(resolved)
        self.assertNotIn("cont-1", engine.get_conflicts())


if __name__ == "__main__":
    unittest.main()
