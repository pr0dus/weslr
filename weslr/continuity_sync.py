"""Cross-Instance Continuity Sync (v58)

Continuity synchronization layer across multiple WESLR nodes.
Defines sync model, eligibility rules, trust boundaries,
stale/partial state handling, and conflict resolution.

Architecture:
  - ContinuitySyncState — canonical sync unit
  - SyncEligibility — rules for what can sync
  - SyncTrustBoundary — trust validation for sync
  - ContinuitySyncEngine — sync lifecycle and conflict resolution
  - DegradedPartitionMode — partition tolerance handling

Rules:
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - Backward compatible (local-only mode works without sync)
  - No remote execution
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .node_identity import (
    NodeIdentity,
    NodeTrustState,
    NodeTrustStatus,
    NodeHealthStatus
)
from .unified_continuity import ContinuityScope


# ============================================================================
# ENUMS
# ============================================================================


class SyncStatus(str, Enum):
    """Status of a continuity sync operation."""
    PENDING = "pending"           # Awaiting sync
    IN_PROGRESS = "in_progress"   # Currently syncing
    SYNCED = "synced"             # Successfully synced
    CONFLICT = "conflict"         # Conflict detected, needs resolution
    REJECTED = "rejected"         # Rejected by trust boundary
    STALE = "stale"               # Stale data, sync skipped
    FAILED = "failed"             # Sync failed


class SyncConflictResolution(str, Enum):
    """Strategy for resolving sync conflicts."""
    SOURCE_WINS = "source_wins"   # Remote/source version wins
    TARGET_WINS = "target_wins"   # Local/target version wins
    TIMESTAMP_WINS = "timestamp_wins"  # Most recent wins
    VERSION_WINS = "version_wins" # Highest version wins
    MANUAL = "manual"             # Manual resolution required
    MERGE = "merge"               # Attempt merge (if possible)


class PartitionMode(str, Enum):
    """Mode for handling network partitions."""
    FULL = "full"                 # Full sync available
    DEGRADED = "degraded"         # Limited sync, local priority
    ISOLATED = "isolated"         # No sync, local-only mode


class SyncDirection(str, Enum):
    """Direction of sync operation."""
    PUSH = "push"                 # Local to remote
    PULL = "pull"                 # Remote to local
    BIDIRECTIONAL = "bidirectional"  # Both directions


class StateSyncability(str, Enum):
    """Whether a state element can be synced."""
    SYNCABLE = "syncable"         # Can sync across nodes
    LOCAL_ONLY = "local_only"     # Never sync
    NODE_BOUND = "node_bound"     # Bound to specific node


# ============================================================================
# SYNC ELIGIBILITY
# ============================================================================


@dataclass
class SyncEligibilityRule:
    """Rule for determining if state can sync."""
    scope: str                    # Scope this rule applies to
    syncability: str = StateSyncability.SYNCABLE.value
    requires_trust: str = NodeTrustStatus.TRUSTED.value
    requires_health: str = NodeHealthStatus.HEALTHY.value
    max_sync_age_seconds: int = 86400  # 24 hours default
    encryption_required: bool = False
    
    def check(
        self,
        scope: str,
        trust_state: NodeTrustState,
        state_age_seconds: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Check if state meets eligibility criteria.
        
        Returns (eligible, reason).
        """
        # Check if scope matches
        if self.scope != scope and self.scope != "*":
            return False, f"Scope {scope} does not match rule scope {self.scope}"
        
        # Check syncability
        if self.syncability == StateSyncability.LOCAL_ONLY.value:
            return False, "State marked local-only"
        
        # Check trust
        trust_order = [
            NodeTrustStatus.REVOKED.value,
            NodeTrustStatus.UNTRUSTED.value,
            NodeTrustStatus.PENDING.value,
            NodeTrustStatus.PROVISIONAL.value,
            NodeTrustStatus.TRUSTED.value
        ]
        
        required_idx = trust_order.index(self.requires_trust)
        actual_idx = trust_order.index(trust_state.trust_status) \
            if trust_state.trust_status in trust_order else 0
        
        if actual_idx < required_idx:
            return False, f"Trust level {trust_state.trust_status} below required {self.requires_trust}"
        
        # Check health
        if trust_state.health_status == NodeHealthStatus.UNHEALTHY.value:
            return False, "Node health is unhealthy"
        
        # Check age
        if state_age_seconds is not None and state_age_seconds > self.max_sync_age_seconds:
            return False, f"State age {state_age_seconds}s exceeds max {self.max_sync_age_seconds}s"
        
        return True, "Eligible"


class SyncEligibility:
    """Determines eligibility for sync operations."""
    
    def __init__(self):
        self._rules: Dict[str, SyncEligibilityRule] = {}
        self._default_rule = SyncEligibilityRule(
            scope="*",
            syncability=StateSyncability.LOCAL_ONLY.value  # Default: don't sync
        )
    
    def set_rule(self, scope: str, rule: SyncEligibilityRule) -> None:
        """Set eligibility rule for a scope."""
        self._rules[scope] = rule
    
    def check_eligibility(
        self,
        scope: str,
        trust_state: NodeTrustState,
        state_age_seconds: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Check if state in scope can sync to target trust state."""
        # Check specific rule first
        if scope in self._rules:
            return self._rules[scope].check(scope, trust_state, state_age_seconds)
        
        # Fall back to wildcard rule
        if "*" in self._rules:
            return self._rules["*"].check(scope, trust_state, state_age_seconds)
        
        # Default: local only
        return self._default_rule.check(scope, trust_state, state_age_seconds)
    
    def is_syncable(self, scope: str) -> bool:
        """Quick check if scope is syncable at all."""
        rule = self._rules.get(scope, self._rules.get("*", self._default_rule))
        return rule.syncability != StateSyncability.LOCAL_ONLY.value
    
    def get_default_eligibility() -> "SyncEligibility":
        """Get default eligibility configuration."""
        eligibility = SyncEligibility()
        
        # Global state: syncable with trust
        eligibility.set_rule("*", SyncEligibilityRule(
            scope="*",
            syncability=StateSyncability.LOCAL_ONLY.value,  # Conservative default
            requires_trust=NodeTrustStatus.TRUSTED.value
        ))
        
        # Session scope: never sync
        eligibility.set_rule(ContinuityScope.SESSION.value, SyncEligibilityRule(
            scope=ContinuityScope.SESSION.value,
            syncability=StateSyncability.LOCAL_ONLY.value
        ))
        
        # Household scope: syncable if trusted
        eligibility.set_rule(ContinuityScope.HOUSEHOLD.value, SyncEligibilityRule(
            scope=ContinuityScope.HOUSEHOLD.value,
            syncability=StateSyncability.SYNCABLE.value,
            requires_trust=NodeTrustStatus.TRUSTED.value
        ))
        
        # Working scope: provisional trust ok
        eligibility.set_rule(ContinuityScope.WORKING.value, SyncEligibilityRule(
            scope=ContinuityScope.WORKING.value,
            syncability=StateSyncability.SYNCABLE.value,
            requires_trust=NodeTrustStatus.PROVISIONAL.value
        ))
        
        return eligibility


# ============================================================================
# SYNC TRUST BOUNDARY
# ============================================================================


@dataclass
class SyncTrustBoundary:
    """Trust boundary for sync operations.
    
    Validates whether a node can participate in sync based on
    trust status, health, and explicit permissions.
    """
    
    local_node_id: str
    
    # Minimum trust level required to sync FROM this node
    min_outbound_trust: str = NodeTrustStatus.PROVISIONAL.value
    
    # Minimum trust level required to sync TO this node
    min_inbound_trust: str = NodeTrustStatus.TRUSTED.value
    
    # Explicit allow/deny lists
    allowed_nodes: Set[str] = field(default_factory=set)
    denied_nodes: Set[str] = field(default_factory=set)
    
    # Require mutual trust
    require_mutual_trust: bool = True
    
    def can_push_to(self, target_trust: NodeTrustState) -> Tuple[bool, str]:
        """Check if we can push sync to target node."""
        # Check deny list
        if target_trust.node_id in self.denied_nodes:
            return False, "Target in deny list"
        
        # Check allow list (if configured)
        if self.allowed_nodes and target_trust.node_id not in self.allowed_nodes:
            return False, "Target not in allow list"
        
        # Check target trust level
        trust_order = [
            NodeTrustStatus.REVOKED.value,
            NodeTrustStatus.UNTRUSTED.value,
            NodeTrustStatus.PENDING.value,
            NodeTrustStatus.PROVISIONAL.value,
            NodeTrustStatus.TRUSTED.value
        ]
        
        min_idx = trust_order.index(self.min_outbound_trust)
        target_idx = trust_order.index(target_trust.trust_status) \
            if target_trust.trust_status in trust_order else 0
        
        if target_idx < min_idx:
            return False, f"Target trust {target_trust.trust_status} below required {self.min_outbound_trust}"
        
        # Check target health
        if target_trust.health_status == NodeHealthStatus.UNHEALTHY.value:
            return False, "Target health is unhealthy"
        
        return True, "Can push"
    
    def can_pull_from(self, source_trust: NodeTrustState) -> Tuple[bool, str]:
        """Check if we can pull sync from source node."""
        # Check deny list
        if source_trust.node_id in self.denied_nodes:
            return False, "Source in deny list"
        
        # Check allow list (if configured)
        if self.allowed_nodes and source_trust.node_id not in self.allowed_nodes:
            return False, "Source not in allow list"
        
        # Check source trust level
        trust_order = [
            NodeTrustStatus.REVOKED.value,
            NodeTrustStatus.UNTRUSTED.value,
            NodeTrustStatus.PENDING.value,
            NodeTrustStatus.PROVISIONAL.value,
            NodeTrustStatus.TRUSTED.value
        ]
        
        min_idx = trust_order.index(self.min_inbound_trust)
        source_idx = trust_order.index(source_trust.trust_status) \
            if source_trust.trust_status in trust_order else 0
        
        if source_idx < min_idx:
            return False, f"Source trust {source_trust.trust_status} below required {self.min_inbound_trust}"
        
        # Check source health
        if source_trust.health_status == NodeHealthStatus.UNHEALTHY.value:
            return False, "Source health is unhealthy"
        
        return True, "Can pull"
    
    def can_sync_with(self, other_trust: NodeTrustState) -> Tuple[bool, str]:
        """Check if bidirectional sync is possible."""
        can_push, push_reason = self.can_push_to(other_trust)
        can_pull, pull_reason = self.can_pull_from(other_trust)
        
        if not can_push and not can_pull:
            return False, f"Cannot push: {push_reason}; Cannot pull: {pull_reason}"
        
        if self.require_mutual_trust and not (can_push and can_pull):
            return False, f"Mutual trust required"
        
        return True, "Sync possible"


# ============================================================================
# CONTINUITY SYNC STATE
# ============================================================================


@dataclass
class ContinuitySyncState:
    """A unit of continuity state ready for sync.
    
    Wraps continuity data with sync metadata for cross-node
    synchronization.
    """
    
    sync_id: str                  # Unique sync identifier
    continuity_id: str            # Original continuity ID
    scope: str                    # Scope level (session, working, household, global)
    
    # Payload
    payload: Dict[str, Any] = field(default_factory=dict)
    payload_hash: str = ""        # SHA256 hash of serialized payload
    
    # Metadata
    source_node_id: str = ""      # Node that created this state
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    version: int = 1              # Incremental version
    
    # Sync metadata
    last_sync_at: Optional[str] = None
    sync_targets: List[str] = field(default_factory=list)  # Node IDs
    
    # State
    status: str = SyncStatus.PENDING.value
    syncability: str = StateSyncability.SYNCABLE.value
    
    def compute_hash(self) -> str:
        """Compute SHA256 hash of payload."""
        serialized = json.dumps(self.payload, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    def validate_hash(self) -> bool:
        """Validate payload against stored hash."""
        if not self.payload_hash:
            return True  # No hash to validate
        return self.payload_hash == self.compute_hash()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sync_id": self.sync_id,
            "continuity_id": self.continuity_id,
            "scope": self.scope,
            "payload": self.payload,
            "payload_hash": self.payload_hash,
            "source_node_id": self.source_node_id,
            "timestamp": self.timestamp,
            "version": self.version,
            "last_sync_at": self.last_sync_at,
            "sync_targets": self.sync_targets,
            "status": self.status,
            "syncability": self.syncability
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContinuitySyncState":
        """Create from dictionary."""
        return cls(
            sync_id=data["sync_id"],
            continuity_id=data["continuity_id"],
            scope=data["scope"],
            payload=data.get("payload", {}),
            payload_hash=data.get("payload_hash", ""),
            source_node_id=data.get("source_node_id", ""),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            version=data.get("version", 1),
            last_sync_at=data.get("last_sync_at"),
            sync_targets=data.get("sync_targets", []),
            status=data.get("status", SyncStatus.PENDING.value),
            syncability=data.get("syncability", StateSyncability.SYNCABLE.value)
        )
    
    def is_stale(self, max_age_seconds: int = 300) -> bool:
        """Check if this sync state is stale."""
        if not self.timestamp:
            return True
        
        try:
            ts = datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - ts).total_seconds()
            return age > max_age_seconds
        except Exception:
            return True
    
    def mark_synced(self, target_node_id: str) -> None:
        """Mark as synced to a target node."""
        self.last_sync_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        if target_node_id not in self.sync_targets:
            self.sync_targets.append(target_node_id)
        self.status = SyncStatus.SYNCED.value


# ============================================================================
# CONFLICT RESOLUTION
# ============================================================================


class ConflictResolver:
    """Resolves conflicts between local and remote sync states."""
    
    def __init__(self, default_strategy: str = SyncConflictResolution.TIMESTAMP_WINS.value):
        self.default_strategy = default_strategy
    
    def resolve(
        self,
        local: ContinuitySyncState,
        remote: ContinuitySyncState,
        strategy: Optional[str] = None
    ) -> Tuple[ContinuitySyncState, str]:
        """Resolve conflict between local and remote state.
        
        Returns (winning_state, resolution_description).
        """
        strategy = strategy or self.default_strategy
        
        # No conflict if same version
        if local.version == remote.version and local.payload_hash == remote.payload_hash:
            return local, "identical"
        
        if strategy == SyncConflictResolution.SOURCE_WINS.value:
            return remote, "source_wins"
        
        elif strategy == SyncConflictResolution.TARGET_WINS.value:
            return local, "target_wins"
        
        elif strategy == SyncConflictResolution.TIMESTAMP_WINS.value:
            try:
                local_ts = datetime.fromisoformat(local.timestamp.replace("Z", "+00:00"))
                remote_ts = datetime.fromisoformat(remote.timestamp.replace("Z", "+00:00"))
                
                if remote_ts > local_ts:
                    return remote, "timestamp_wins_remote"
                else:
                    return local, "timestamp_wins_local"
            except Exception:
                # Fallback to version
                if remote.version > local.version:
                    return remote, "version_wins_remote"
                else:
                    return local, "version_wins_local"
        
        elif strategy == SyncConflictResolution.VERSION_WINS.value:
            if remote.version > local.version:
                return remote, "version_wins_remote"
            else:
                return local, "version_wins_local"
        
        elif strategy == SyncConflictResolution.MANUAL.value:
            # Return local but mark as conflict
            local.status = SyncStatus.CONFLICT.value
            return local, "manual_resolution_required"
        
        else:
            # Default: timestamp wins
            return self.resolve(local, remote, SyncConflictResolution.TIMESTAMP_WINS.value)
    
    def detect_conflict(
        self,
        local: ContinuitySyncState,
        remote: ContinuitySyncState
    ) -> bool:
        """Detect if there's a conflict between states."""
        # Same ID but different content
        if local.continuity_id != remote.continuity_id:
            return False  # Different states
        
        # Different version or hash = potential conflict
        return local.version != remote.version or local.payload_hash != remote.payload_hash


# ============================================================================
# DEGRADED PARTITION MODE
# ============================================================================


@dataclass
class DegradedPartitionMode:
    """Configuration for degraded partition handling.
    
    When network partitions occur, WESLR can continue operating
    in degraded mode with local-only state.
    """
    
    mode: str = PartitionMode.FULL.value
    
    # Thresholds for mode transition
    partition_detection_seconds: int = 30
    degraded_timeout_seconds: int = 300  # 5 minutes to degraded
    isolated_timeout_seconds: int = 1800  # 30 minutes to isolated
    
    # Behavior in degraded mode
    allow_local_writes: bool = True
    queue_outbound_sync: bool = True
    require_explicit_sync: bool = False
    
    # Conflict resolution on partition heal
    on_partition_heal: str = SyncConflictResolution.TIMESTAMP_WINS.value
    
    def is_sync_allowed(self) -> bool:
        """Check if sync operations are allowed in current mode."""
        return self.mode in (PartitionMode.FULL.value, PartitionMode.DEGRADED.value)
    
    def is_full_sync_allowed(self) -> bool:
        """Check if full bidirectional sync is allowed."""
        return self.mode == PartitionMode.FULL.value
    
    def should_queue_sync(self) -> bool:
        """Check if sync should be queued for later."""
        return self.mode in (PartitionMode.DEGRADED.value, PartitionMode.ISOLATED.value) and self.queue_outbound_sync
    
    def transition_to(self, new_mode: str) -> "DegradedPartitionMode":
        """Create new mode configuration with updated mode."""
        return DegradedPartitionMode(
            mode=new_mode,
            partition_detection_seconds=self.partition_detection_seconds,
            degraded_timeout_seconds=self.degraded_timeout_seconds,
            isolated_timeout_seconds=self.isolated_timeout_seconds,
            allow_local_writes=self.allow_local_writes,
            queue_outbound_sync=self.queue_outbound_sync,
            require_explicit_sync=self.require_explicit_sync,
            on_partition_heal=self.on_partition_heal
        )


# ============================================================================
# CONTINUITY SYNC ENGINE
# ============================================================================


class ContinuitySyncEngine:
    """Engine for managing continuity sync across nodes.
    
    Coordinates eligibility checking, trust boundary validation,
    conflict resolution, and partition mode handling.
    """
    
    def __init__(
        self,
        local_identity: NodeIdentity,
        eligibility: Optional[SyncEligibility] = None,
        trust_boundary: Optional[SyncTrustBoundary] = None,
        conflict_resolver: Optional[ConflictResolver] = None,
        partition_mode: Optional[DegradedPartitionMode] = None
    ):
        self.local_identity = local_identity
        self.eligibility = eligibility or SyncEligibility.get_default_eligibility()
        self.trust_boundary = trust_boundary or SyncTrustBoundary(
            local_node_id=local_identity.node_id
        )
        self.conflict_resolver = conflict_resolver or ConflictResolver()
        self.partition_mode = partition_mode or DegradedPartitionMode()
        
        self._sync_queue: List[ContinuitySyncState] = []
        self._conflicts: Dict[str, Tuple[ContinuitySyncState, ContinuitySyncState]] = {}
    
    def prepare_sync_state(
        self,
        continuity_id: str,
        scope: str,
        payload: Dict[str, Any],
        target_nodes: List[str]
    ) -> Optional[ContinuitySyncState]:
        """Prepare a continuity state for sync.
        
        Returns None if not eligible for sync.
        """
        # Check eligibility
        eligible, reason = self.eligibility.check_eligibility(
            scope,
            NodeTrustState(node_id=self.local_identity.node_id, trust_status=NodeTrustStatus.TRUSTED.value),
            0
        )
        
        if not eligible:
            return None
        
        sync_state = ContinuitySyncState(
            sync_id=f"{self.local_identity.node_id}:{continuity_id}:{datetime.now(timezone.utc).timestamp()}",
            continuity_id=continuity_id,
            scope=scope,
            payload=payload,
            source_node_id=self.local_identity.node_id,
            sync_targets=target_nodes
        )
        sync_state.payload_hash = sync_state.compute_hash()
        
        return sync_state
    
    def validate_inbound_sync(
        self,
        sync_state: ContinuitySyncState,
        source_trust: NodeTrustState
    ) -> Tuple[bool, str]:
        """Validate an inbound sync request.
        
        Returns (allowed, reason).
        """
        # Check partition mode
        if not self.partition_mode.is_sync_allowed():
            return False, f"Sync not allowed in {self.partition_mode.mode} mode"
        
        # Check trust boundary
        can_pull, reason = self.trust_boundary.can_pull_from(source_trust)
        if not can_pull:
            return False, reason
        
        # Check hash integrity
        if not sync_state.validate_hash():
            return False, "Hash validation failed"
        
        # Check staleness
        if sync_state.is_stale():
            return False, "Sync state is stale"
        
        return True, "Valid"
    
    def validate_outbound_sync(
        self,
        sync_state: ContinuitySyncState,
        target_trust: NodeTrustState
    ) -> Tuple[bool, str]:
        """Validate an outbound sync request."""
        # Check partition mode
        if not self.partition_mode.is_sync_allowed():
            return False, f"Sync not allowed in {self.partition_mode.mode} mode"
        
        # Check trust boundary
        can_push, reason = self.trust_boundary.can_push_to(target_trust)
        if not can_push:
            return False, reason
        
        # Check eligibility
        state_age = 0  # Assuming fresh
        if sync_state.timestamp:
            try:
                ts = datetime.fromisoformat(sync_state.timestamp.replace("Z", "+00:00"))
                state_age = (datetime.now(timezone.utc) - ts).total_seconds()
            except Exception:
                pass
        
        eligible, el_reason = self.eligibility.check_eligibility(
            sync_state.scope,
            target_trust,
            int(state_age)
        )
        if not eligible:
            return False, el_reason
        
        return True, "Valid"
    
    def handle_inbound_sync(
        self,
        remote_state: ContinuitySyncState,
        local_state: Optional[ContinuitySyncState],
        source_trust: NodeTrustState
    ) -> Tuple[SyncStatus, Optional[ContinuitySyncState]]:
        """Handle an inbound sync state.
        
        Returns (status, resolved_state).
        """
        # Validate
        valid, reason = self.validate_inbound_sync(remote_state, source_trust)
        if not valid:
            remote_state.status = SyncStatus.REJECTED.value
            return SyncStatus.REJECTED, None
        
        # Check for conflict
        if local_state and self.conflict_resolver.detect_conflict(local_state, remote_state):
            winner, resolution = self.conflict_resolver.resolve(local_state, remote_state)
            
            if resolution == "manual_resolution_required":
                self._conflicts[remote_state.continuity_id] = (local_state, remote_state)
                return SyncStatus.CONFLICT, None
            
            winner.status = SyncStatus.SYNCED.value
            return SyncStatus.SYNCED, winner
        
        # No conflict - accept remote
        remote_state.status = SyncStatus.SYNCED.value
        return SyncStatus.SYNCED, remote_state
    
    def get_conflicts(self) -> Dict[str, Tuple[ContinuitySyncState, ContinuitySyncState]]:
        """Get all unresolved conflicts."""
        return self._conflicts.copy()
    
    def resolve_conflict(
        self,
        continuity_id: str,
        chosen: ContinuitySyncState
    ) -> bool:
        """Manually resolve a conflict."""
        if continuity_id not in self._conflicts:
            return False
        
        del self._conflicts[continuity_id]
        chosen.status = SyncStatus.SYNCED.value
        return True
    
    def set_partition_mode(self, mode: str) -> None:
        """Update partition mode."""
        self.partition_mode = self.partition_mode.transition_to(mode)
