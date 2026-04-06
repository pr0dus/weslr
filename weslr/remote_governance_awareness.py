"""Remote Governance Awareness (v59)

Awareness layer for governance state across distributed WESLR nodes.
Tracks remote governance snapshots, policy scope boundaries,
compliance status, and governance delegation — without
enforcing on remote nodes.

Architecture:
  - RemoteGovernanceState — snapshot from remote node
  - GovernanceScope — policy applicability scope
  - GovernanceDelegation — authority delegation chain
  - RemoteComplianceStatus — compliance tracking
  - PolicyScopeBoundary — scope resolution across nodes
  - CrossNodePolicyConflict — conflict detection
  - GovernanceAwarenessRegistry — multi-node governance tracking
  - GovernanceCapability — capability advertisement

Rules:
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - Awareness only, no remote enforcement
  - Read-only remote governance view
  - No TIA/C#
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .node_identity import (
    NodeIdentity,
    NodeTrustState,
    NodeTrustStatus,
    NodeHealthStatus
)


# ============================================================================
# ENUMS
# ============================================================================


class GovernanceScope(str, Enum):
    """Scope of governance policy applicability."""
    LOCAL = "local"               # Applies only to local node
    SHARED = "shared"             # Applies to all nodes in topology
    DELEGATED = "delegated"       # Authority delegated from another node
    PARTITIONED = "partitioned"   # Node-specific variant


class DelegationStatus(str, Enum):
    """Status of governance delegation."""
    ACTIVE = "active"             # Delegation in force
    SUSPENDED = "suspended"       # Temporarily suspended
    EXPIRED = "expired"           # Past expiry time
    REVOKED = "revoked"           # Explicitly revoked
    PENDING = "pending"           # Awaiting acceptance


class ComplianceStatus(str, Enum):
    """Compliance status of a node to governance policies."""
    COMPLIANT = "compliant"       # Fully compliant
    PARTIAL = "partial"           # Partially compliant
    NON_COMPLIANT = "non_compliant"  # Violations detected
    UNKNOWN = "unknown"           # Status not reported
    EXEMPT = "exempt"             # Explicitly exempted


class GovernanceCapability(str, Enum):
    """Governance capabilities a node can advertise."""
    POLICY_ENFORCEMENT = "policy_enforcement"  # Can enforce policies locally
    AUDIT_LOGGING = "audit_logging"            # Can generate audit logs
    COMPLIANCE_REPORTING = "compliance_reporting"  # Can report compliance
    DELEGATION_ACCEPTANCE = "delegation_acceptance"  # Can accept delegations
    CONFLICT_DETECTION = "conflict_detection"  # Can detect policy conflicts
    POLICY_SUGGESTION = "policy_suggestion"  # Can suggest policy updates


class ConflictSeverity(str, Enum):
    """Severity of cross-node policy conflict."""
    NONE = "none"                 # No conflict
    WARNING = "warning"           # Minor discrepancy
    MODERATE = "moderate"           # Significant mismatch
    CRITICAL = "critical"           # Violation potential
    BLOCKING = "blocking"           # Sync blocked


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class PolicyReference:
    """Reference to a policy from any node."""
    policy_id: str
    policy_version: str
    source_node_id: str
    scope: str = GovernanceScope.LOCAL.value
    checksum: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "source_node_id": self.source_node_id,
            "scope": self.scope,
            "checksum": self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyReference":
        return cls(
            policy_id=data["policy_id"],
            policy_version=data["policy_version"],
            source_node_id=data["source_node_id"],
            scope=data.get("scope", GovernanceScope.LOCAL.value),
            checksum=data.get("checksum")
        )


@dataclass
class GovernanceDelegation:
    """Governance authority delegation between nodes."""
    
    delegation_id: str
    from_node_id: str           # Delegating node
    to_node_id: str             # Receiving node
    
    # Scope
    delegated_policies: List[str] = field(default_factory=list)  # Policy IDs
    delegated_scope: str = GovernanceScope.SHARED.value
    
    # Status
    status: str = DelegationStatus.PENDING.value
    
    # Time bounds
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    effective_at: Optional[str] = None
    expires_at: Optional[str] = None
    
    # Revocation
    revoked_at: Optional[str] = None
    revoked_by: Optional[str] = None
    revocation_reason: Optional[str] = None
    
    def is_active(self) -> bool:
        """Check if delegation is currently active."""
        if self.status != DelegationStatus.ACTIVE.value:
            return False
        
        now = datetime.now(timezone.utc)
        
        # Check effective time
        if self.effective_at:
            effective = datetime.fromisoformat(self.effective_at.replace("Z", "+00:00"))
            if now < effective:
                return False
        
        # Check expiry
        if self.expires_at:
            expires = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            if now > expires:
                return False
        
        return True
    
    def revoke(self, revoked_by: str, reason: str = "") -> None:
        """Revoke this delegation."""
        self.status = DelegationStatus.REVOKED.value
        self.revoked_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.revoked_by = revoked_by
        self.revocation_reason = reason
    
    def activate(self) -> None:
        """Activate this delegation."""
        self.status = DelegationStatus.ACTIVE.value
        if not self.effective_at:
            self.effective_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "delegation_id": self.delegation_id,
            "from_node_id": self.from_node_id,
            "to_node_id": self.to_node_id,
            "delegated_policies": self.delegated_policies,
            "delegated_scope": self.delegated_scope,
            "status": self.status,
            "created_at": self.created_at,
            "effective_at": self.effective_at,
            "expires_at": self.expires_at,
            "revoked_at": self.revoked_at,
            "revoked_by": self.revoked_by,
            "revocation_reason": self.revocation_reason
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GovernanceDelegation":
        return cls(
            delegation_id=data["delegation_id"],
            from_node_id=data["from_node_id"],
            to_node_id=data["to_node_id"],
            delegated_policies=data.get("delegated_policies", []),
            delegated_scope=data.get("delegated_scope", GovernanceScope.SHARED.value),
            status=data.get("status", DelegationStatus.PENDING.value),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            effective_at=data.get("effective_at"),
            expires_at=data.get("expires_at"),
            revoked_at=data.get("revoked_at"),
            revoked_by=data.get("revoked_by"),
            revocation_reason=data.get("revocation_reason")
        )


@dataclass
class RemoteComplianceStatus:
    """Compliance status reported by or inferred for a remote node."""
    
    node_id: str
    status: str = ComplianceStatus.UNKNOWN.value
    
    # Breakdown
    policy_id: Optional[str] = None  # Specific policy being assessed
    violations: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    reported_at: Optional[str] = None
    assessed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    assessed_by: Optional[str] = None  # Node that assessed this
    
    # Drift tracking
    previous_status: Optional[str] = None
    status_changed_at: Optional[str] = None
    
    def mark_compliant(self, reported: bool = True) -> None:
        """Mark as compliant."""
        if self.status != ComplianceStatus.COMPLIANT.value:
            self.previous_status = self.status
            self.status_changed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.status = ComplianceStatus.COMPLIANT.value
        if reported:
            self.reported_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def mark_non_compliant(self, violations: List[Dict[str, Any]], reported: bool = True) -> None:
        """Mark as non-compliant with violations."""
        if self.status != ComplianceStatus.NON_COMPLIANT.value:
            self.previous_status = self.status
            self.status_changed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.status = ComplianceStatus.NON_COMPLIANT.value
        self.violations = violations
        if reported:
            self.reported_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def is_stale(self, max_age_seconds: int = 300) -> bool:
        """Check if compliance status is stale."""
        if not self.reported_at:
            return True
        try:
            reported = datetime.fromisoformat(self.reported_at.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - reported).total_seconds()
            return age > max_age_seconds
        except Exception:
            return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "status": self.status,
            "policy_id": self.policy_id,
            "violations": self.violations,
            "warnings": self.warnings,
            "reported_at": self.reported_at,
            "assessed_at": self.assessed_at,
            "assessed_by": self.assessed_by,
            "previous_status": self.previous_status,
            "status_changed_at": self.status_changed_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RemoteComplianceStatus":
        return cls(
            node_id=data["node_id"],
            status=data.get("status", ComplianceStatus.UNKNOWN.value),
            policy_id=data.get("policy_id"),
            violations=data.get("violations", []),
            warnings=data.get("warnings", []),
            reported_at=data.get("reported_at"),
            assessed_at=data.get("assessed_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            assessed_by=data.get("assessed_by"),
            previous_status=data.get("previous_status"),
            status_changed_at=data.get("status_changed_at")
        )


@dataclass
class RemoteGovernanceState:
    """Governance state snapshot from a remote node.
    
    Read-only view — local node does not modify remote governance.
    """
    
    node_id: str
    
    # Policies active on remote node
    active_policies: List[PolicyReference] = field(default_factory=list)
    
    # Delegations
    active_delegations: List[GovernanceDelegation] = field(default_factory=list)
    incoming_delegations: List[GovernanceDelegation] = field(default_factory=list)
    
    # Compliance
    compliance_status: RemoteComplianceStatus = field(default_factory=lambda: RemoteComplianceStatus(node_id=""))
    
    # Capabilities
    advertised_capabilities: List[str] = field(default_factory=list)
    
    # Metadata
    snapshot_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    received_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    version: str = "v59"
    
    def is_stale(self, max_age_seconds: int = 300) -> bool:
        """Check if snapshot is stale."""
        try:
            snapshot = datetime.fromisoformat(self.snapshot_at.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - snapshot).total_seconds()
            return age > max_age_seconds
        except Exception:
            return True
    
    def has_capability(self, capability: str) -> bool:
        """Check if remote node advertises a capability."""
        return capability in self.advertised_capabilities
    
    def get_active_delegations_from(self, node_id: str) -> List[GovernanceDelegation]:
        """Get delegations from a specific node."""
        return [d for d in self.active_delegations if d.from_node_id == node_id and d.is_active()]
    
    def get_delegation_to(self, node_id: str) -> Optional[GovernanceDelegation]:
        """Get delegation to a specific node."""
        for d in self.incoming_delegations:
            if d.to_node_id == node_id and d.is_active():
                return d
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "active_policies": [p.to_dict() for p in self.active_policies],
            "active_delegations": [d.to_dict() for d in self.active_delegations],
            "incoming_delegations": [d.to_dict() for d in self.incoming_delegations],
            "compliance_status": self.compliance_status.to_dict(),
            "advertised_capabilities": self.advertised_capabilities,
            "snapshot_at": self.snapshot_at,
            "received_at": self.received_at,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RemoteGovernanceState":
        return cls(
            node_id=data["node_id"],
            active_policies=[PolicyReference.from_dict(p) for p in data.get("active_policies", [])],
            active_delegations=[GovernanceDelegation.from_dict(d) for d in data.get("active_delegations", [])],
            incoming_delegations=[GovernanceDelegation.from_dict(d) for d in data.get("incoming_delegations", [])],
            compliance_status=RemoteComplianceStatus.from_dict(data.get("compliance_status", {})) if data.get("compliance_status") else RemoteComplianceStatus(node_id=data["node_id"]),
            advertised_capabilities=data.get("advertised_capabilities", []),
            snapshot_at=data.get("snapshot_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            received_at=data.get("received_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            version=data.get("version", "v59")
        )


# ============================================================================
# POLICY SCOPE BOUNDARY
# ============================================================================


class PolicyScopeBoundary:
    """Resolves policy scope across node boundaries.
    
    Determines which policies apply to which nodes based on
    scope rules and delegations.
    """
    
    def __init__(self, local_node_id: str):
        self.local_node_id = local_node_id
        self._scope_overrides: Dict[str, str] = {}  # policy_id -> scope
    
    def resolve_scope(
        self,
        policy_ref: PolicyReference,
        target_node_id: str
    ) -> str:
        """Resolve effective scope for a policy on a target node."""
        # Check override
        if policy_ref.policy_id in self._scope_overrides:
            return self._scope_overrides[policy_ref.policy_id]
        
        # Delegated scope takes precedence
        if policy_ref.scope == GovernanceScope.DELEGATED.value:
            return GovernanceScope.DELEGATED.value
        
        # Shared applies to all
        if policy_ref.scope == GovernanceScope.SHARED.value:
            return GovernanceScope.SHARED.value
        
        # Local only applies to source node
        if policy_ref.scope == GovernanceScope.LOCAL.value:
            if policy_ref.source_node_id == target_node_id:
                return GovernanceScope.LOCAL.value
            else:
                return GovernanceScope.PARTITIONED.value  # Does not apply
        
        return policy_ref.scope
    
    def applies_to(
        self,
        policy_ref: PolicyReference,
        target_node_id: str
    ) -> bool:
        """Check if policy applies to target node."""
        scope = self.resolve_scope(policy_ref, target_node_id)
        return scope not in (GovernanceScope.PARTITIONED.value,)
    
    def set_scope_override(self, policy_id: str, scope: str) -> None:
        """Override scope resolution for a policy."""
        self._scope_overrides[policy_id] = scope


# ============================================================================
# CROSS-NODE POLICY CONFLICT
# ============================================================================


@dataclass
class CrossNodePolicyConflict:
    """Detected conflict between local and remote policy."""
    
    conflict_id: str
    local_policy: Optional[PolicyReference]
    remote_policy: Optional[PolicyReference]
    remote_node_id: str
    
    conflict_type: str = "mismatch"  # mismatch, missing, version_drift
    severity: str = ConflictSeverity.WARNING.value
    
    description: str = ""
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    # Resolution
    resolution_strategy: str = "timestamp_wins"
    resolved: bool = False
    resolved_at: Optional[str] = None
    resolution_action: Optional[str] = None  # accept_local, accept_remote, merge, manual


class ConflictDetector:
    """Detects conflicts between local and remote governance."""
    
    def __init__(self, local_node_id: str):
        self.local_node_id = local_node_id
    
    def detect_conflicts(
        self,
        local_policies: List[PolicyReference],
        remote_state: RemoteGovernanceState
    ) -> List[CrossNodePolicyConflict]:
        """Detect conflicts between local and remote policies."""
        conflicts = []
        
        # Build lookup
        local_by_id = {p.policy_id: p for p in local_policies}
        remote_by_id = {p.policy_id: p for p in remote_state.active_policies}
        
        # Check for version mismatches
        for policy_id, local_ref in local_by_id.items():
            if policy_id in remote_by_id:
                remote_ref = remote_by_id[policy_id]
                
                # Check shared scope applicability
                if local_ref.scope == GovernanceScope.SHARED.value:
                    if local_ref.policy_version != remote_ref.policy_version:
                        conflict = CrossNodePolicyConflict(
                            conflict_id=f"{self.local_node_id}:{remote_state.node_id}:{policy_id}",
                            local_policy=local_ref,
                            remote_policy=remote_ref,
                            remote_node_id=remote_state.node_id,
                            conflict_type="version_drift",
                            severity=ConflictSeverity.MODERATE.value,
                            description=f"Version mismatch: local={local_ref.policy_version}, remote={remote_ref.policy_version}"
                        )
                        conflicts.append(conflict)
            else:
                # Local policy not present on remote
                if local_ref.scope == GovernanceScope.SHARED.value:
                    conflict = CrossNodePolicyConflict(
                        conflict_id=f"{self.local_node_id}:{remote_state.node_id}:{policy_id}",
                        local_policy=local_ref,
                        remote_policy=None,
                        remote_node_id=remote_state.node_id,
                        conflict_type="missing_on_remote",
                        severity=ConflictSeverity.WARNING.value,
                        description=f"Shared policy {policy_id} not present on remote node"
                    )
                    conflicts.append(conflict)
        
        # Check for policies on remote not present locally
        for policy_id, remote_ref in remote_by_id.items():
            if policy_id not in local_by_id:
                if remote_ref.scope == GovernanceScope.SHARED.value:
                    conflict = CrossNodePolicyConflict(
                        conflict_id=f"{self.local_node_id}:{remote_state.node_id}:{policy_id}",
                        local_policy=None,
                        remote_policy=remote_ref,
                        remote_node_id=remote_state.node_id,
                        conflict_type="missing_local",
                        severity=ConflictSeverity.WARNING.value,
                        description=f"Shared policy {policy_id} present on remote but not locally"
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def assess_conflict_severity(
        self,
        conflict: CrossNodePolicyConflict
    ) -> str:
        """Assess severity of a conflict."""
        if conflict.conflict_type == "version_drift":
            return ConflictSeverity.MODERATE.value
        elif conflict.conflict_type in ("missing_on_remote", "missing_local"):
            return ConflictSeverity.WARNING.value
        return ConflictSeverity.WARNING.value


# ============================================================================
# GOVERNANCE AWARENESS REGISTRY
# ============================================================================


class GovernanceAwarenessRegistry:
    """Registry tracking governance awareness across nodes.
    
    Maintains read-only view of governance state from remote nodes.
    """
    
    def __init__(self, local_node_id: str):
        self.local_node_id = local_node_id
        self._remote_states: Dict[str, RemoteGovernanceState] = {}
        self._compliance_statuses: Dict[str, RemoteComplianceStatus] = {}
        self._delegations: Dict[str, GovernanceDelegation] = {}
        self._conflicts: Dict[str, CrossNodePolicyConflict] = {}
        self._scope_boundary = PolicyScopeBoundary(local_node_id)
    
    def update_remote_state(self, state: RemoteGovernanceState) -> None:
        """Update governance state for a remote node."""
        state.received_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self._remote_states[state.node_id] = state
        
        # Update compliance status
        self._compliance_statuses[state.node_id] = state.compliance_status
    
    def get_remote_state(self, node_id: str) -> Optional[RemoteGovernanceState]:
        """Get governance state for a remote node."""
        return self._remote_states.get(node_id)
    
    def get_all_remote_states(self) -> List[RemoteGovernanceState]:
        """Get all tracked remote governance states."""
        return list(self._remote_states.values())
    
    def get_stale_states(self, max_age_seconds: int = 300) -> List[str]:
        """Get node IDs with stale governance snapshots."""
        stale = []
        for node_id, state in self._remote_states.items():
            if state.is_stale(max_age_seconds):
                stale.append(node_id)
        return stale
    
    def update_compliance(self, status: RemoteComplianceStatus) -> None:
        """Update compliance status for a node."""
        self._compliance_statuses[status.node_id] = status
    
    def get_compliance(self, node_id: str) -> Optional[RemoteComplianceStatus]:
        """Get compliance status for a node."""
        return self._compliance_statuses.get(node_id)
    
    def get_non_compliant_nodes(self) -> List[str]:
        """Get node IDs with non-compliant status."""
        return [
            node_id for node_id, status in self._compliance_statuses.items()
            if status.status == ComplianceStatus.NON_COMPLIANT.value
        ]
    
    def register_delegation(self, delegation: GovernanceDelegation) -> None:
        """Register a governance delegation."""
        self._delegations[delegation.delegation_id] = delegation
    
    def get_delegation(self, delegation_id: str) -> Optional[GovernanceDelegation]:
        """Get a delegation by ID."""
        return self._delegations.get(delegation_id)
    
    def get_active_delegations(self) -> List[GovernanceDelegation]:
        """Get all active delegations."""
        return [d for d in self._delegations.values() if d.is_active()]
    
    def get_delegations_for_node(self, node_id: str) -> List[GovernanceDelegation]:
        """Get delegations involving a node (from or to)."""
        return [
            d for d in self._delegations.values()
            if d.from_node_id == node_id or d.to_node_id == node_id
        ]
    
    def detect_conflicts(
        self,
        local_policies: List[PolicyReference]
    ) -> List[CrossNodePolicyConflict]:
        """Detect conflicts with all remote nodes."""
        detector = ConflictDetector(self.local_node_id)
        all_conflicts = []
        
        for remote_state in self._remote_states.values():
            conflicts = detector.detect_conflicts(local_policies, remote_state)
            for conflict in conflicts:
                self._conflicts[conflict.conflict_id] = conflict
                all_conflicts.append(conflict)
        
        return all_conflicts
    
    def get_conflicts(self, resolved: Optional[bool] = None) -> List[CrossNodePolicyConflict]:
        """Get tracked conflicts."""
        conflicts = self._conflicts.values()
        if resolved is not None:
            conflicts = [c for c in conflicts if c.resolved == resolved]
        return list(conflicts)
    
    def resolve_conflict(self, conflict_id: str, action: str) -> bool:
        """Mark a conflict as resolved."""
        if conflict_id not in self._conflicts:
            return False
        
        conflict = self._conflicts[conflict_id]
        conflict.resolved = True
        conflict.resolved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        conflict.resolution_action = action
        return True
    
    def get_applicable_policies(
        self,
        target_node_id: str
    ) -> List[PolicyReference]:
        """Get policies applicable to a target node from all sources."""
        applicable = []
        
        # Get from remote states
        for remote_state in self._remote_states.values():
            for policy in remote_state.active_policies:
                if self._scope_boundary.applies_to(policy, target_node_id):
                    applicable.append(policy)
        
        return applicable
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of governance awareness."""
        return {
            "tracked_nodes": len(self._remote_states),
            "active_delegations": len(self.get_active_delegations()),
            "pending_conflicts": len(self.get_conflicts(resolved=False)),
            "non_compliant_nodes": len(self.get_non_compliant_nodes()),
            "stale_states": len(self.get_stale_states())
        }


# ============================================================================
# GOVERNANCE CAPABILITY
# ============================================================================


class GovernanceCapabilityAdvertisement:
    """Advertises local governance capabilities to remote nodes."""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self._capabilities: Set[str] = set()
        self._metadata: Dict[str, Any] = {}
    
    def add_capability(self, capability: str, metadata: Optional[Dict] = None) -> None:
        """Add a governance capability."""
        self._capabilities.add(capability)
        if metadata:
            self._metadata[capability] = metadata
    
    def remove_capability(self, capability: str) -> None:
        """Remove a governance capability."""
        self._capabilities.discard(capability)
        self._metadata.pop(capability, None)
    
    def has_capability(self, capability: str) -> bool:
        """Check if capability is advertised."""
        return capability in self._capabilities
    
    def get_capabilities(self) -> List[str]:
        """Get all advertised capabilities."""
        return list(self._capabilities)
    
    def to_advertisement(self) -> Dict[str, Any]:
        """Create advertisement payload."""
        return {
            "node_id": self.node_id,
            "capabilities": list(self._capabilities),
            "metadata": self._metadata,
            "advertised_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
    
    @classmethod
    def create_default(cls, node_id: str, role: str = "worker") -> "GovernanceCapabilityAdvertisement":
        """Create default capability advertisement for a role."""
        adv = cls(node_id)
        
        # All nodes can do basic compliance reporting
        adv.add_capability(GovernanceCapability.COMPLIANCE_REPORTING.value)
        
        if role in ("controller", "worker"):
            adv.add_capability(GovernanceCapability.AUDIT_LOGGING.value)
            adv.add_capability(GovernanceCapability.CONFLICT_DETECTION.value)
        
        if role == "controller":
            adv.add_capability(GovernanceCapability.POLICY_ENFORCEMENT.value)
            adv.add_capability(GovernanceCapability.DELEGATION_ACCEPTANCE.value)
            adv.add_capability(GovernanceCapability.POLICY_SUGGESTION.value)
        
        return adv
