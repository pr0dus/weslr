"""Remote Action Proposal / Orchestration Guardrails (v61)

Safe proposal layer for remote actions between WESLR nodes.
Provides proposal modeling, validation, gating, and escalation
without actual remote execution.

Architecture:
  - ProposalStatus — proposal lifecycle states
  - RejectionReason — structured rejection reasons
  - RemoteActionProposal — canonical proposal model
  - TargetNodeSelection — target selection criteria
  - CapabilityBoundaryCheck — capability validation
  - TrustHealthGate — trust/health validation
  - ProofSafetyHooks — safety validation hooks
  - ApprovalRequirement — approval rules
  - EscalationPath — escalation routing
  - ProposalAuditTrace — audit event tracking

Rules:
  - Proposal/gate/escalate only — no execution
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - No remote code execution
  - No TIA/C#
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Tuple, Set

from .node_identity import (
    NodeIdentity,
    NodeCapabilitySummary,
    NodeTrustState,
    NodeTrustStatus,
    NodeHealthStatus,
)
from .node_registry import NodeRegistry


# ============================================================================
# ENUMS
# ============================================================================


class ProposalStatus(str, Enum):
    """Lifecycle states for remote action proposals."""
    DRAFT = "draft"                   # Being composed
    PENDING = "pending"               # Submitted, awaiting validation
    VALIDATING = "validating"         # Undergoing capability/trust checks
    GATED = "gated"                   # Blocked on safety/proof requirements
    APPROVED = "approved"             # Cleared for execution (proposal only, not executed)
    REJECTED = "rejected"             # Failed validation/gating
    ESCALATED = "escalated"           # Sent to higher authority
    EXPIRED = "expired"               # TTL exceeded


class RejectionCategory(str, Enum):
    """Categories of proposal rejection."""
    CAPABILITY_MISSING = "capability_missing"
    TRUST_INSUFFICIENT = "trust_insufficient"
    HEALTH_DEGRADED = "health_degraded"
    SAFETY_CHECK_FAILED = "safety_check_failed"
    POLICY_VIOLATION = "policy_violation"
    TIMEOUT = "timeout"
    MANUAL_REJECTION = "manual_rejection"
    TARGET_UNREACHABLE = "target_unreachable"


class ApprovalMode(str, Enum):
    """Mode of approval required."""
    AUTOMATIC = "automatic"           # Auto-approved if gates pass
    MANUAL = "manual"                 # Requires human review
    MULTI_PARTY = "multi_party"       # Requires N approvals
    CONTROLLER = "controller"         # Requires controller node approval


class AuditEventType(str, Enum):
    """Types of audit events."""
    PROPOSAL_CREATED = "proposal_created"
    PROPOSAL_SUBMITTED = "proposal_submitted"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"
    GATE_PASSED = "gate_passed"
    GATE_BLOCKED = "gate_blocked"
    APPROVAL_GRANTED = "approval_granted"
    REJECTION_ISSUED = "rejection_issued"
    ESCALATION_TRIGGERED = "escalation_triggered"
    PROPOSAL_EXPIRED = "proposal_expired"


# ============================================================================
# REJECTION REASON
# ============================================================================


@dataclass
class RejectionReason:
    """Structured reason for proposal rejection."""
    
    category: str
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    rejected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    rejected_by: Optional[str] = None  # Node or operator ID
    
    # Remediation hints
    retry_possible: bool = False
    retry_after_seconds: Optional[int] = None
    remediation_suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "description": self.description,
            "details": self.details,
            "rejected_at": self.rejected_at,
            "rejected_by": self.rejected_by,
            "retry_possible": self.retry_possible,
            "retry_after_seconds": self.retry_after_seconds,
            "remediation_suggestion": self.remediation_suggestion
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RejectionReason":
        return cls(
            category=data["category"],
            description=data["description"],
            details=data.get("details", {}),
            rejected_at=data.get("rejected_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            rejected_by=data.get("rejected_by"),
            retry_possible=data.get("retry_possible", False),
            retry_after_seconds=data.get("retry_after_seconds"),
            remediation_suggestion=data.get("remediation_suggestion")
        )


# ============================================================================
# REMOTE ACTION PROPOSAL
# ============================================================================


@dataclass
class RemoteActionProposal:
    """A proposal for a remote action to be performed by another node.
    
    This is a proposal only — no execution happens here.
    """
    
    proposal_id: str
    
    # Identity
    proposing_node_id: str
    target_node_id: str
    
    # Action definition
    action_type: str              # e.g., "sync_continuity", "report_status", "suggest_policy"
    action_version: str = "1.0"
    action_payload: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    submitted_at: Optional[str] = None
    expires_at: Optional[str] = None
    
    # Status
    status: str = ProposalStatus.DRAFT.value
    status_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Validation results
    validation_results: List[Dict[str, Any]] = field(default_factory=list)
    
    # Gating
    gated_at: Optional[str] = None
    gate_requirements: List[str] = field(default_factory=list)  # Requirements to clear
    gates_cleared: List[str] = field(default_factory=list)       # Requirements met
    
    # Approval
    approval_mode: str = ApprovalMode.AUTOMATIC.value
    approvals_received: List[str] = field(default_factory=list)  # Approver IDs
    approvals_required: int = 1
    
    # Rejection
    rejection_reason: Optional[RejectionReason] = None
    
    # Escalation
    escalated_to: Optional[str] = None
    escalation_path_id: Optional[str] = None
    
    # Safety
    safety_proofs: Dict[str, Any] = field(default_factory=dict)
    
    def submit(self) -> None:
        """Submit proposal for validation."""
        self._transition_to(ProposalStatus.PENDING.value, "Proposal submitted")
        self.submitted_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def start_validation(self) -> None:
        """Mark as under validation."""
        self._transition_to(ProposalStatus.VALIDATING.value, "Validation started")
    
    def mark_validated(self, results: List[Dict[str, Any]]) -> None:
        """Mark validation complete."""
        self.validation_results = results
        all_passed = all(r.get("passed", False) for r in results)
        if all_passed:
            # If automatic mode and no gates required, go directly to approved
            if self.approval_mode == ApprovalMode.AUTOMATIC.value and not self.gate_requirements:
                self.approve("system")
            else:
                self._transition_to(ProposalStatus.GATED.value, "Validation passed, awaiting gates")
        else:
            failed = [r for r in results if not r.get("passed", False)]
            self._reject(
                RejectionCategory.SAFETY_CHECK_FAILED.value,
                f"Validation failed: {len(failed)} checks failed",
                {"failed_checks": failed}
            )
    
    def add_gate_requirement(self, requirement: str) -> None:
        """Add a gate requirement."""
        if requirement not in self.gate_requirements:
            self.gate_requirements.append(requirement)
    
    def clear_gate(self, requirement: str, proof: Optional[Dict] = None) -> None:
        """Clear a gate requirement."""
        if requirement in self.gate_requirements and requirement not in self.gates_cleared:
            self.gates_cleared.append(requirement)
            if proof:
                self.safety_proofs[requirement] = proof
            
            # Check if all gates cleared
            if set(self.gates_cleared) >= set(self.gate_requirements):
                self._check_approval_ready()
    
    def _check_approval_ready(self) -> None:
        """Check if proposal is ready for approval."""
        if self.approval_mode == ApprovalMode.AUTOMATIC.value:
            self.approve("system")
        else:
            self._transition_to(ProposalStatus.GATED.value, "Awaiting approval")
    
    def approve(self, approver_id: str) -> bool:
        """Add approval to proposal."""
        if approver_id not in self.approvals_received:
            self.approvals_received.append(approver_id)
        
        if len(self.approvals_received) >= self.approvals_required:
            self._transition_to(ProposalStatus.APPROVED.value, f"Approved by {len(self.approvals_received)} approvers")
            return True
        
        return False
    
    def _reject(self, category: str, description: str, details: Optional[Dict] = None) -> None:
        """Reject the proposal."""
        self.rejection_reason = RejectionReason(
            category=category,
            description=description,
            details=details or {}
        )
        self._transition_to(ProposalStatus.REJECTED.value, f"Rejected: {description}")
    
    def reject(self, reason: RejectionReason) -> None:
        """External rejection with full reason."""
        self.rejection_reason = reason
        self._transition_to(ProposalStatus.REJECTED.value, f"Rejected: {reason.description}")
    
    def escalate(self, escalation_path_id: str, escalated_to: str) -> None:
        """Escalate proposal to higher authority."""
        self.escalation_path_id = escalation_path_id
        self.escalated_to = escalated_to
        self._transition_to(ProposalStatus.ESCALATED.value, f"Escalated to {escalated_to}")
    
    def check_expiry(self) -> bool:
        """Check if proposal has expired."""
        if not self.expires_at:
            return False
        try:
            expiry = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > expiry:
                if self.status not in (ProposalStatus.APPROVED.value, ProposalStatus.REJECTED.value, ProposalStatus.ESCALATED.value):
                    self._transition_to(ProposalStatus.EXPIRED.value, "TTL exceeded")
                return True
        except Exception:
            pass
        return False
    
    def _transition_to(self, new_status: str, reason: str) -> None:
        """Transition to new status with history."""
        old_status = self.status
        self.status = new_status
        self.status_history.append({
            "from": old_status,
            "to": new_status,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        })
    
    def can_execute(self) -> bool:
        """Check if proposal is approved for execution.
        
        Note: This only checks approval status. Actual execution
        is outside scope — this is proposal/guardrails only.
        """
        return self.status == ProposalStatus.APPROVED.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "proposing_node_id": self.proposing_node_id,
            "target_node_id": self.target_node_id,
            "action_type": self.action_type,
            "action_version": self.action_version,
            "action_payload": self.action_payload,
            "created_at": self.created_at,
            "submitted_at": self.submitted_at,
            "expires_at": self.expires_at,
            "status": self.status,
            "status_history": self.status_history,
            "validation_results": self.validation_results,
            "gated_at": self.gated_at,
            "gate_requirements": self.gate_requirements,
            "gates_cleared": self.gates_cleared,
            "approval_mode": self.approval_mode,
            "approvals_received": self.approvals_received,
            "approvals_required": self.approvals_required,
            "rejection_reason": self.rejection_reason.to_dict() if self.rejection_reason else None,
            "escalated_to": self.escalated_to,
            "escalation_path_id": self.escalation_path_id,
            "safety_proofs": self.safety_proofs
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RemoteActionProposal":
        proposal = cls(
            proposal_id=data["proposal_id"],
            proposing_node_id=data["proposing_node_id"],
            target_node_id=data["target_node_id"],
            action_type=data["action_type"]
        )
        proposal.action_version = data.get("action_version", "1.0")
        proposal.action_payload = data.get("action_payload", {})
        proposal.created_at = data.get("created_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        proposal.submitted_at = data.get("submitted_at")
        proposal.expires_at = data.get("expires_at")
        proposal.status = data.get("status", ProposalStatus.DRAFT.value)
        proposal.status_history = data.get("status_history", [])
        proposal.validation_results = data.get("validation_results", [])
        proposal.gated_at = data.get("gated_at")
        proposal.gate_requirements = data.get("gate_requirements", [])
        proposal.gates_cleared = data.get("gates_cleared", [])
        proposal.approval_mode = data.get("approval_mode", ApprovalMode.AUTOMATIC.value)
        proposal.approvals_received = data.get("approvals_received", [])
        proposal.approvals_required = data.get("approvals_required", 1)
        proposal.escalated_to = data.get("escalated_to")
        proposal.escalation_path_id = data.get("escalation_path_id")
        proposal.safety_proofs = data.get("safety_proofs", {})
        
        if data.get("rejection_reason"):
            proposal.rejection_reason = RejectionReason.from_dict(data["rejection_reason"])
        
        return proposal


# ============================================================================
# TARGET NODE SELECTION
# ============================================================================


@dataclass
class TargetNodeSelection:
    """Criteria for selecting target nodes for proposals."""
    
    # Capability filters
    required_capabilities: List[Tuple[str, Optional[str]]] = field(default_factory=list)
    min_capacity: Optional[float] = None
    
    # Trust filters
    min_trust_level: str = NodeTrustStatus.PROVISIONAL.value
    require_healthy: bool = True
    
    # Reachability
    require_reachable: bool = True
    
    # Limits
    max_targets: int = 1
    target_preference: str = "any"  # any, controller, worker, edge
    
    def matches(self, identity: NodeIdentity, capabilities: NodeCapabilitySummary, trust: NodeTrustState, is_reachable: bool) -> Tuple[bool, str]:
        """Check if a node matches selection criteria."""
        # Check reachability
        if self.require_reachable and not is_reachable:
            return False, "Not reachable"
        
        # Check trust
        trust_order = [
            NodeTrustStatus.REVOKED.value,
            NodeTrustStatus.UNTRUSTED.value,
            NodeTrustStatus.PENDING.value,
            NodeTrustStatus.PROVISIONAL.value,
            NodeTrustStatus.TRUSTED.value
        ]
        min_idx = trust_order.index(self.min_trust_level)
        node_idx = trust_order.index(trust.trust_status) if trust.trust_status in trust_order else 0
        if node_idx < min_idx:
            return False, f"Trust level {trust.trust_status} below required {self.min_trust_level}"
        
        # Check health
        if self.require_healthy and trust.health_status != NodeHealthStatus.HEALTHY.value:
            return False, f"Health status {trust.health_status} not healthy"
        
        # Check capabilities
        for cap_type, cap_name in self.required_capabilities:
            if not capabilities.has_capability(cap_type, cap_name):
                return False, f"Missing capability {cap_type}/{cap_name or 'any'}"
        
        return True, "Matches"
    
    def select_from_registry(self, registry: NodeRegistry) -> List[str]:
        """Select matching nodes from registry."""
        matches = []
        
        for entry in registry.get_all_entries():
            if entry.node_id == registry.local_node_id:
                continue  # Skip self
            
            if not entry.identity or not entry.capabilities or not entry.trust_state:
                continue
            
            matches_criteria, _ = self.matches(
                entry.identity,
                entry.capabilities,
                entry.trust_state,
                entry.is_reachable
            )
            
            if matches_criteria:
                matches.append(entry.node_id)
        
        return matches[:self.max_targets]


# ============================================================================
# CAPABILITY BOUNDARY CHECK
# ============================================================================


class CapabilityBoundaryCheck:
    """Validates that target nodes have required capabilities."""
    
    def __init__(self, registry: NodeRegistry):
        self.registry = registry
    
    def check(
        self,
        target_node_id: str,
        required_capabilities: List[Tuple[str, Optional[str]]]
    ) -> Tuple[bool, List[str]]:
        """Check if target has required capabilities.
        
        Returns (has_all, missing_capabilities).
        """
        entry = self.registry.get_entry(target_node_id)
        if not entry or not entry.capabilities:
            return False, [f"No capabilities registered for {target_node_id}"]
        
        missing = []
        for cap_type, cap_name in required_capabilities:
            if not entry.capabilities.has_capability(cap_type, cap_name):
                missing.append(f"{cap_type}/{cap_name or 'any'}")
        
        return len(missing) == 0, missing
    
    def validate_proposal(self, proposal: RemoteActionProposal) -> Dict[str, Any]:
        """Validate proposal target capabilities."""
        # Extract required capabilities from action type
        required = self._get_required_capabilities(proposal.action_type)
        
        has_all, missing = self.check(proposal.target_node_id, required)
        
        return {
            "check": "capability_boundary",
            "passed": has_all,
            "details": {
                "required": required,
                "missing": missing
            }
        }
    
    def _get_required_capabilities(self, action_type: str) -> List[Tuple[str, Optional[str]]]:
        """Get required capabilities for an action type."""
        # Default: no specific capability required
        capability_map = {
            "sync_continuity": [("core", "continuity")],
            "report_status": [("core", "status-reporting")],
            "suggest_policy": [("governance", "policy-suggestion")],
        }
        return capability_map.get(action_type, [])


# ============================================================================
# TRUST/HEALTH GATE
# ============================================================================


class TrustHealthGate:
    """Gate that validates trust and health before proposal acceptance."""
    
    def __init__(self, registry: NodeRegistry, min_trust: str = NodeTrustStatus.TRUSTED.value):
        self.registry = registry
        self.min_trust = min_trust
    
    def validate(self, proposal: RemoteActionProposal) -> Tuple[bool, Optional[RejectionReason]]:
        """Validate proposal against trust/health requirements."""
        entry = self.registry.get_entry(proposal.target_node_id)
        if not entry:
            return False, RejectionReason(
                category=RejectionCategory.TARGET_UNREACHABLE.value,
                description=f"Target {proposal.target_node_id} not in registry",
                retry_possible=False
            )
        
        if not entry.trust_state:
            return False, RejectionReason(
                category=RejectionCategory.TRUST_INSUFFICIENT.value,
                description="No trust state available",
                retry_possible=False
            )
        
        # Check trust
        trust_order = [
            NodeTrustStatus.REVOKED.value,
            NodeTrustStatus.UNTRUSTED.value,
            NodeTrustStatus.PENDING.value,
            NodeTrustStatus.PROVISIONAL.value,
            NodeTrustStatus.TRUSTED.value
        ]
        min_idx = trust_order.index(self.min_trust)
        node_idx = trust_order.index(entry.trust_state.trust_status) \
            if entry.trust_state.trust_status in trust_order else 0
        
        if node_idx < min_idx:
            return False, RejectionReason(
                category=RejectionCategory.TRUST_INSUFFICIENT.value,
                description=f"Trust level {entry.trust_state.trust_status} below required {self.min_trust}",
                retry_possible=True,
                retry_after_seconds=300
            )
        
        # Check health
        if entry.trust_state.health_status == NodeHealthStatus.UNHEALTHY.value:
            return False, RejectionReason(
                category=RejectionCategory.HEALTH_DEGRADED.value,
                description=f"Target health is {entry.trust_state.health_status}",
                retry_possible=True,
                retry_after_seconds=60
            )
        
        return True, None


# ============================================================================
# PROOF/SAFETY HOOKS
# ============================================================================


class ProofSafetyHooks:
    """Hooks for safety validation before proposal approval.
    
    Extensions can register hooks to provide additional validation.
    """
    
    def __init__(self):
        self._hooks: List[Callable[[RemoteActionProposal], Tuple[bool, Optional[str]]]] = []
    
    def register_hook(self, hook: Callable[[RemoteActionProposal], Tuple[bool, Optional[str]]]) -> None:
        """Register a safety validation hook."""
        self._hooks.append(hook)
    
    def validate(self, proposal: RemoteActionProposal) -> Tuple[bool, List[str]]:
        """Run all safety hooks.
        
        Returns (all_passed, failure_reasons).
        """
        failures = []
        
        for hook in self._hooks:
            passed, reason = hook(proposal)
            if not passed:
                failures.append(reason or "Safety check failed")
        
        return len(failures) == 0, failures
    
    def clear_hooks(self) -> None:
        """Clear all registered hooks."""
        self._hooks = []


# ============================================================================
# APPROVAL REQUIREMENT
# ============================================================================


@dataclass
class ApprovalRequirement:
    """Defines approval rules for proposals."""
    
    mode: str = ApprovalMode.AUTOMATIC.value
    required_approvers: List[str] = field(default_factory=list)  # Specific approver IDs
    min_approver_count: int = 1
    require_controller: bool = False
    
    def is_satisfied(self, proposal: RemoteActionProposal, registry: NodeRegistry) -> Tuple[bool, str]:
        """Check if approval requirements are satisfied."""
        if proposal.status != ProposalStatus.GATED.value and proposal.status != ProposalStatus.PENDING.value:
            return False, f"Invalid status: {proposal.status}"
        
        current_count = len(proposal.approvals_received)
        
        if current_count < self.min_approver_count:
            return False, f"Need {self.min_approver_count} approvals, have {current_count}"
        
        # Check specific approvers
        if self.required_approvers:
            missing = [a for a in self.required_approvers if a not in proposal.approvals_received]
            if missing:
                return False, f"Missing required approvals from: {missing}"
        
        # Check controller approval if required
        if self.require_controller:
            controllers = registry.get_controllers()
            controller_ids = {c.node_id for c in controllers}
            has_controller = any(a in controller_ids for a in proposal.approvals_received)
            if not has_controller:
                return False, "Controller approval required"
        
        return True, "Requirements satisfied"


# ============================================================================
# ESCALATION PATH
# ============================================================================


@dataclass
class EscalationPath:
    """Defines where to send rejected/for-review proposals."""
    
    path_id: str
    name: str
    
    # Target
    target_node_id: Optional[str] = None
    target_role: Optional[str] = None  # e.g., "controller"
    
    # Conditions
    on_rejection_categories: List[str] = field(default_factory=list)
    on_manual_review: bool = True
    
    # Timeout
    response_timeout_seconds: int = 3600  # 1 hour default
    
    def should_escalate(self, proposal: RemoteActionProposal) -> bool:
        """Check if proposal should be escalated via this path."""
        if proposal.status == ProposalStatus.ESCALATED.value:
            return False
        
        if proposal.rejection_reason and proposal.rejection_reason.category in self.on_rejection_categories:
            return True
        
        if self.on_manual_review and proposal.approval_mode == ApprovalMode.MANUAL.value:
            return True
        
        return False
    
    def get_target(self, registry: NodeRegistry) -> Optional[str]:
        """Get escalation target node ID."""
        if self.target_node_id:
            return self.target_node_id
        
        if self.target_role:
            if self.target_role == "controller":
                controllers = registry.get_controllers()
                if controllers:
                    return controllers[0].node_id
        
        return None


# ============================================================================
# PROPOSAL AUDIT TRACE
# ============================================================================


@dataclass
class AuditEvent:
    """Single audit event."""
    
    event_id: str
    event_type: str
    proposal_id: str
    
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    node_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "proposal_id": self.proposal_id,
            "timestamp": self.timestamp,
            "node_id": self.node_id,
            "details": self.details
        }


class ProposalAuditTrace:
    """Tracks audit events for proposals."""
    
    def __init__(self, local_node_id: str):
        self.local_node_id = local_node_id
        self._events: List[AuditEvent] = []
        self._by_proposal: Dict[str, List[AuditEvent]] = {}
    
    def log_event(
        self,
        proposal_id: str,
        event_type: str,
        details: Optional[Dict] = None,
        node_id: Optional[str] = None
    ) -> AuditEvent:
        """Log an audit event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            proposal_id=proposal_id,
            node_id=node_id or self.local_node_id,
            details=details or {}
        )
        
        self._events.append(event)
        
        if proposal_id not in self._by_proposal:
            self._by_proposal[proposal_id] = []
        self._by_proposal[proposal_id].append(event)
        
        return event
    
    def get_events(self, proposal_id: str) -> List[AuditEvent]:
        """Get all events for a proposal."""
        return self._by_proposal.get(proposal_id, [])
    
    def get_trace(self, proposal_id: str) -> List[Dict[str, Any]]:
        """Get full audit trace for a proposal."""
        events = self.get_events(proposal_id)
        return [e.to_dict() for e in sorted(events, key=lambda x: x.timestamp)]
    
    def get_stats(self) -> Dict[str, int]:
        """Get audit statistics."""
        return {
            "total_events": len(self._events),
            "proposals_tracked": len(self._by_proposal)
        }
