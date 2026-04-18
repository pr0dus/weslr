"""Controlled Remote Execution Envelope (v62)

Safe distributed execution wrapper on top of v61 proposals.
Provides approval-gated, trust-first, rollback-aware execution
with full traceability. No background workers, no schedulers,
no autonomous execution — explicit envelope lifecycle only.

Architecture:
  - ExecutionLifecycleState — execution lifecycle states
  - ExecutionRequestEnvelope — canonical execution container
  - ExecutionGates — trust/health/approval/safety gates
  - RollbackPath — rollback tracking and traceability
  - ExecutionAuditTrace — full execution audit logging
  - ExplicitExecutionController — single-point control surface

Rules:
  - Approval-gated execution only
  - Trust-first validation
  - Rollback-aware at every step
  - Fully traceable
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - No automatic task runners
  - No cron/timers/background workers
  - No remote policy mutation
  - No TIA/C#
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Tuple

from .remote_action_proposal import (
    RemoteActionProposal,
    ProposalStatus,
    RejectionReason,
    RejectionCategory,
    ApprovalMode,
    AuditEventType,
    TargetNodeSelection,
    CapabilityBoundaryCheck,
    TrustHealthGate,
    ProofSafetyHooks,
    ProposalAuditTrace,
)
from .node_identity import (
    NodeIdentity,
    NodeCapabilitySummary,
    NodeTrustState,
    NodeTrustStatus,
    NodeHealthStatus,
)
from .node_registry import NodeRegistry


# ============================================================================
# EXECUTION LIFECYCLE STATES
# ============================================================================


class ExecutionLifecycleState(str, Enum):
    """Lifecycle states for controlled remote execution."""
    QUEUED = "queued"                           # Envelope created, awaiting gates
    AWAITING_APPROVAL = "awaiting_approval"     # Proposal submitted, awaiting approval
    AUTHORIZED = "authorized"                   # All gates passed, ready to dispatch
    DISPATCHED = "dispatched"                   # Sent to target node
    ACKNOWLEDGED = "acknowledged"               # Target acknowledged receipt
    COMPLETED = "completed"                     # Execution finished successfully
    FAILED = "failed"                           # Execution failed
    ROLLED_BACK = "rolled_back"                 # Execution rolled back
    REJECTED = "rejected"                       # Rejected at any gate


class RollbackFeasibility(str, Enum):
    """Feasibility of rollback for an execution."""
    FULL = "full"               # Complete rollback possible
    PARTIAL = "partial"         # Partial rollback possible
    NONE = "none"               # Rollback not possible
    UNKNOWN = "unknown"         # Feasibility not yet determined


class ExecutionEventType(str, Enum):
    """Types of execution audit events."""
    ENVELOPE_CREATED = "envelope_created"
    QUEUED = "queued"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    TRUST_GATE_PASSED = "trust_gate_passed"
    TRUST_GATE_FAILED = "trust_gate_failed"
    HEALTH_GATE_PASSED = "health_gate_passed"
    HEALTH_GATE_FAILED = "health_gate_failed"
    SAFETY_GATE_PASSED = "safety_gate_passed"
    SAFETY_GATE_FAILED = "safety_gate_failed"
    AUTHORIZED = "authorized"
    DISPATCHED = "dispatched"
    ACKNOWLEDGED = "acknowledged"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK_INITIATED = "rollback_initiated"
    ROLLBACK_COMPLETED = "rollback_completed"
    ROLLBACK_FAILED = "rollback_failed"
    REJECTED = "rejected"
    EXPIRED = "expired"


# ============================================================================
# ROLLBACK PATH
# ============================================================================


@dataclass
class RollbackPath:
    """Tracks rollback feasibility and execution for an execution envelope."""
    
    feasibility: str = RollbackFeasibility.UNKNOWN.value
    status: str = "not_started"  # not_started, in_progress, completed, failed
    reason: Optional[str] = None
    rollback_attempted_at: Optional[str] = None
    rollback_completed_at: Optional[str] = None
    rollback_events: List[Dict[str, Any]] = field(default_factory=list)
    
    def mark_feasible(self, feasibility: str, reason: Optional[str] = None) -> None:
        """Mark rollback feasibility."""
        self.feasibility = feasibility
        if reason:
            self.reason = reason
    
    def initiate_rollback(self, reason: str) -> bool:
        """Initiate rollback. Returns True if rollback can proceed."""
        if self.feasibility == RollbackFeasibility.NONE.value:
            return False
        
        self.status = "in_progress"
        self.reason = reason
        self.rollback_attempted_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return True
    
    def complete_rollback(self) -> None:
        """Mark rollback as completed."""
        self.status = "completed"
        self.rollback_completed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def fail_rollback(self, error: str) -> None:
        """Mark rollback as failed."""
        self.status = "failed"
        self.rollback_events.append({
            "event": "rollback_failed",
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        })
    
    def can_rollback(self) -> bool:
        """Check if rollback is possible."""
        return self.feasibility in (RollbackFeasibility.FULL.value, RollbackFeasibility.PARTIAL.value)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "feasibility": self.feasibility,
            "status": self.status,
            "reason": self.reason,
            "rollback_attempted_at": self.rollback_attempted_at,
            "rollback_completed_at": self.rollback_completed_at,
            "rollback_events": self.rollback_events
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RollbackPath":
        return cls(
            feasibility=data.get("feasibility", RollbackFeasibility.UNKNOWN.value),
            status=data.get("status", "not_started"),
            reason=data.get("reason"),
            rollback_attempted_at=data.get("rollback_attempted_at"),
            rollback_completed_at=data.get("rollback_completed_at"),
            rollback_events=data.get("rollback_events", [])
        )


# ============================================================================
# EXECUTION REQUEST ENVELOPE
# ============================================================================


@dataclass
class ExecutionRequestEnvelope:
    """Canonical container for a controlled remote execution request.
    
    Ties to a v61 RemoteActionProposal for approval gating.
    Tracks full execution lifecycle with rollback awareness.
    """
    
    # Identity
    request_id: str
    proposal_id: str  # References v61 proposal
    source_node_id: str
    target_node_id: str
    
    # Execution definition
    execution_intent: str  # Description of what will be executed
    action_type: str       # Action type from proposal
    action_payload: Dict[str, Any] = field(default_factory=dict)
    capability_requirements: List[Tuple[str, Optional[str]]] = field(default_factory=list)
    
    # Lifecycle
    state: str = ExecutionLifecycleState.QUEUED.value
    state_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    expires_at: Optional[str] = None
    authorized_at: Optional[str] = None
    dispatched_at: Optional[str] = None
    acknowledged_at: Optional[str] = None
    completed_at: Optional[str] = None
    failed_at: Optional[str] = None
    
    # Gates
    trust_gate_passed: bool = False
    health_gate_passed: bool = False
    approval_gate_passed: bool = False
    safety_gate_passed: bool = False
    gate_failures: List[Dict[str, Any]] = field(default_factory=list)
    
    # Rollback
    rollback_path: RollbackPath = field(default_factory=RollbackPath)
    
    # Results
    execution_result: Optional[Dict[str, Any]] = None
    failure_reason: Optional[str] = None
    rejection_reason: Optional[RejectionReason] = None
    
    def __post_init__(self):
        """Initialize state history with creation event."""
        if not self.state_history:
            self._transition_to(ExecutionLifecycleState.QUEUED.value, "Envelope created")
    
    def _transition_to(self, new_state: str, reason: str) -> None:
        """Transition to new state with history."""
        old_state = self.state
        self.state = new_state
        self.state_history.append({
            "from": old_state,
            "to": new_state,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        })
    
    def is_terminal(self) -> bool:
        """Check if execution is in terminal state."""
        return self.state in (
            ExecutionLifecycleState.COMPLETED.value,
            ExecutionLifecycleState.FAILED.value,
            ExecutionLifecycleState.ROLLED_BACK.value,
            ExecutionLifecycleState.REJECTED.value
        )
    
    def can_dispatch(self) -> bool:
        """Check if envelope is ready for dispatch."""
        return self.state == ExecutionLifecycleState.AUTHORIZED.value
    
    def can_rollback(self) -> bool:
        """Check if rollback is possible."""
        return self.rollback_path.can_rollback() and self.state not in (
            ExecutionLifecycleState.ROLLED_BACK.value,
            ExecutionLifecycleState.COMPLETED.value
        )
    
    def check_expiry(self) -> bool:
        """Check if execution has expired."""
        if not self.expires_at:
            return False
        try:
            expiry = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > expiry:
                if not self.is_terminal():
                    self._transition_to(ExecutionLifecycleState.FAILED.value, "TTL exceeded")
                return True
        except Exception:
            pass
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "proposal_id": self.proposal_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "execution_intent": self.execution_intent,
            "action_type": self.action_type,
            "action_payload": self.action_payload,
            "capability_requirements": self.capability_requirements,
            "state": self.state,
            "state_history": self.state_history,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "authorized_at": self.authorized_at,
            "dispatched_at": self.dispatched_at,
            "acknowledged_at": self.acknowledged_at,
            "completed_at": self.completed_at,
            "failed_at": self.failed_at,
            "trust_gate_passed": self.trust_gate_passed,
            "health_gate_passed": self.health_gate_passed,
            "approval_gate_passed": self.approval_gate_passed,
            "safety_gate_passed": self.safety_gate_passed,
            "gate_failures": self.gate_failures,
            "rollback_path": self.rollback_path.to_dict(),
            "execution_result": self.execution_result,
            "failure_reason": self.failure_reason,
            "rejection_reason": self.rejection_reason.to_dict() if self.rejection_reason else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionRequestEnvelope":
        envelope = cls(
            request_id=data["request_id"],
            proposal_id=data["proposal_id"],
            source_node_id=data["source_node_id"],
            target_node_id=data["target_node_id"],
            execution_intent=data["execution_intent"],
            action_type=data["action_type"],
            action_payload=data.get("action_payload", {}),
            capability_requirements=data.get("capability_requirements", []),
            state=data.get("state", ExecutionLifecycleState.QUEUED.value),
            state_history=data.get("state_history", []),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            expires_at=data.get("expires_at"),
            authorized_at=data.get("authorized_at"),
            dispatched_at=data.get("dispatched_at"),
            acknowledged_at=data.get("acknowledged_at"),
            completed_at=data.get("completed_at"),
            failed_at=data.get("failed_at"),
            trust_gate_passed=data.get("trust_gate_passed", False),
            health_gate_passed=data.get("health_gate_passed", False),
            approval_gate_passed=data.get("approval_gate_passed", False),
            safety_gate_passed=data.get("safety_gate_passed", False),
            gate_failures=data.get("gate_failures", []),
            rollback_path=RollbackPath.from_dict(data.get("rollback_path", {})),
            execution_result=data.get("execution_result"),
            failure_reason=data.get("failure_reason")
        )
        if data.get("rejection_reason"):
            envelope.rejection_reason = RejectionReason.from_dict(data["rejection_reason"])
        return envelope


# ============================================================================
# EXECUTION GATES
# ============================================================================


@dataclass
class ExecutionGates:
    """Collection of gates for execution authorization."""
    
    registry: NodeRegistry
    min_trust: str = NodeTrustStatus.TRUSTED.value
    safety_hooks: ProofSafetyHooks = field(default_factory=ProofSafetyHooks)
    
    def evaluate_trust_gate(self, envelope: ExecutionRequestEnvelope) -> Tuple[bool, Optional[RejectionReason]]:
        """Evaluate trust gate for execution."""
        entry = self.registry.get_entry(envelope.target_node_id)
        if not entry:
            return False, RejectionReason(
                category=RejectionCategory.TARGET_UNREACHABLE.value,
                description=f"Target {envelope.target_node_id} not in registry"
            )
        
        if not entry.trust_state:
            return False, RejectionReason(
                category=RejectionCategory.TRUST_INSUFFICIENT.value,
                description="No trust state available"
            )
        
        # Check trust level
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
        
        return True, None
    
    def evaluate_health_gate(self, envelope: ExecutionRequestEnvelope) -> Tuple[bool, Optional[RejectionReason]]:
        """Evaluate health gate for execution."""
        entry = self.registry.get_entry(envelope.target_node_id)
        if not entry or not entry.trust_state:
            return False, RejectionReason(
                category=RejectionCategory.HEALTH_DEGRADED.value,
                description="No health data available"
            )
        
        if entry.trust_state.health_status == NodeHealthStatus.UNHEALTHY.value:
            return False, RejectionReason(
                category=RejectionCategory.HEALTH_DEGRADED.value,
                description=f"Target health is {entry.trust_state.health_status}",
                retry_possible=True,
                retry_after_seconds=60
            )
        
        return True, None
    
    def evaluate_safety_gate(self, envelope: ExecutionRequestEnvelope) -> Tuple[bool, List[str]]:
        """Evaluate safety hooks for execution."""
        # Create a lightweight proposal-like object for safety hooks
        class ProposalProxy:
            def __init__(self, envelope):
                self.action_type = envelope.action_type
                self.action_payload = envelope.action_payload
                self.source_node_id = envelope.source_node_id
                self.target_node_id = envelope.target_node_id
        
        proxy = ProposalProxy(envelope)
        passed, failures = self.safety_hooks.validate(proxy)
        return passed, failures
    
    def evaluate_all_gates(self, envelope: ExecutionRequestEnvelope) -> Tuple[bool, List[RejectionReason]]:
        """Evaluate all gates. Returns (all_passed, failures)."""
        failures = []
        
        # Trust gate
        trust_passed, trust_failure = self.evaluate_trust_gate(envelope)
        if trust_passed:
            envelope.trust_gate_passed = True
        else:
            failures.append(trust_failure)
            envelope.gate_failures.append({"gate": "trust", "reason": trust_failure.to_dict()})
        
        # Health gate
        health_passed, health_failure = self.evaluate_health_gate(envelope)
        if health_passed:
            envelope.health_gate_passed = True
        else:
            failures.append(health_failure)
            envelope.gate_failures.append({"gate": "health", "reason": health_failure.to_dict()})
        
        # Safety gate
        safety_passed, safety_failures = self.evaluate_safety_gate(envelope)
        if safety_passed:
            envelope.safety_gate_passed = True
        else:
            for failure in safety_failures:
                reason = RejectionReason(
                    category=RejectionCategory.SAFETY_CHECK_FAILED.value,
                    description=failure
                )
                failures.append(reason)
                envelope.gate_failures.append({"gate": "safety", "reason": reason.to_dict()})
        
        return len(failures) == 0, failures


# ============================================================================
# EXECUTION AUDIT TRACE
# ============================================================================


@dataclass
class ExecutionAuditEvent:
    """Single execution audit event."""
    
    event_id: str
    event_type: str
    request_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    node_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "node_id": self.node_id,
            "details": self.details
        }


class ExecutionAuditTrace:
    """Tracks audit events for execution envelopes."""
    
    def __init__(self, local_node_id: str):
        self.local_node_id = local_node_id
        self._events: List[ExecutionAuditEvent] = []
        self._by_request: Dict[str, List[ExecutionAuditEvent]] = {}
    
    def log_event(
        self,
        request_id: str,
        event_type: str,
        details: Optional[Dict] = None,
        node_id: Optional[str] = None
    ) -> ExecutionAuditEvent:
        """Log an execution audit event."""
        event = ExecutionAuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            request_id=request_id,
            node_id=node_id or self.local_node_id,
            details=details or {}
        )
        
        self._events.append(event)
        
        if request_id not in self._by_request:
            self._by_request[request_id] = []
        self._by_request[request_id].append(event)
        
        return event
    
    def get_events(self, request_id: str) -> List[ExecutionAuditEvent]:
        """Get all events for a request."""
        return self._by_request.get(request_id, [])
    
    def get_trace(self, request_id: str) -> List[Dict[str, Any]]:
        """Get full audit trace for a request."""
        events = self.get_events(request_id)
        return [e.to_dict() for e in sorted(events, key=lambda x: x.timestamp)]
    
    def get_stats(self) -> Dict[str, int]:
        """Get audit statistics."""
        return {
            "total_events": len(self._events),
            "requests_tracked": len(self._by_request)
        }


# ============================================================================
# EXPLICIT EXECUTION CONTROLLER
# ============================================================================


class ExplicitExecutionController:
    """Single-point control surface for execution lifecycle.
    
    No background workers, no schedulers, no autonomous execution.
    All transitions happen through explicit method calls.
    """
    
    def __init__(
        self,
        local_node_id: str,
        registry: NodeRegistry,
        gates: Optional[ExecutionGates] = None,
        audit_trace: Optional[ExecutionAuditTrace] = None
    ):
        self.local_node_id = local_node_id
        self.registry = registry
        self.gates = gates or ExecutionGates(registry)
        self.audit = audit_trace or ExecutionAuditTrace(local_node_id)
        self._envelopes: Dict[str, ExecutionRequestEnvelope] = {}
    
    def create_envelope(
        self,
        proposal: RemoteActionProposal,
        execution_intent: str,
        capability_requirements: Optional[List[Tuple[str, Optional[str]]]] = None,
        expires_in_seconds: int = 3600
    ) -> ExecutionRequestEnvelope:
        """Create execution envelope from proposal."""
        request_id = str(uuid.uuid4())
        
        expiry = datetime.now(timezone.utc) + __import__('datetime').timedelta(seconds=expires_in_seconds)
        expires_at = expiry.isoformat().replace("+00:00", "Z")
        
        envelope = ExecutionRequestEnvelope(
            request_id=request_id,
            proposal_id=proposal.proposal_id,
            source_node_id=self.local_node_id,
            target_node_id=proposal.target_node_id,
            execution_intent=execution_intent,
            action_type=proposal.action_type,
            action_payload=proposal.action_payload,
            capability_requirements=capability_requirements or [],
            expires_at=expires_at
        )
        
        self._envelopes[request_id] = envelope
        
        # Log creation
        self.audit.log_event(
            request_id=request_id,
            event_type=ExecutionEventType.ENVELOPE_CREATED.value,
            details={"proposal_id": proposal.proposal_id, "intent": execution_intent}
        )
        
        return envelope
    
    def evaluate_gates(self, request_id: str) -> Tuple[bool, List[RejectionReason]]:
        """Evaluate all gates for an envelope."""
        envelope = self._envelopes.get(request_id)
        if not envelope:
            raise ValueError(f"Envelope {request_id} not found")
        
        all_passed, failures = self.gates.evaluate_all_gates(envelope)
        
        # Log results
        if all_passed:
            self.audit.log_event(
                request_id=request_id,
                event_type=ExecutionEventType.TRUST_GATE_PASSED.value
            )
            self.audit.log_event(
                request_id=request_id,
                event_type=ExecutionEventType.HEALTH_GATE_PASSED.value
            )
            self.audit.log_event(
                request_id=request_id,
                event_type=ExecutionEventType.SAFETY_GATE_PASSED.value
            )
        else:
            for failure in failures:
                event_type = ExecutionEventType.REJECTED.value
                if failure.category == RejectionCategory.TRUST_INSUFFICIENT.value:
                    event_type = ExecutionEventType.TRUST_GATE_FAILED.value
                elif failure.category == RejectionCategory.HEALTH_DEGRADED.value:
                    event_type = ExecutionEventType.HEALTH_GATE_FAILED.value
                elif failure.category == RejectionCategory.SAFETY_CHECK_FAILED.value:
                    event_type = ExecutionEventType.SAFETY_GATE_FAILED.value
                
                self.audit.log_event(
                    request_id=request_id,
                    event_type=event_type,
                    details={"category": failure.category, "description": failure.description}
                )
            
            # Reject envelope
            envelope.rejection_reason = failures[0]
            envelope._transition_to(ExecutionLifecycleState.REJECTED.value, f"Gate failed: {failures[0].category}")
            self.audit.log_event(
                request_id=request_id,
                event_type=ExecutionEventType.REJECTED.value,
                details={"reasons": [f.to_dict() for f in failures]}
            )
        
        return all_passed, failures
    
    def request_approval(self, request_id: str) -> None:
        """Transition envelope to awaiting approval."""
        envelope = self._envelopes.get(request_id)
        if not envelope:
            raise ValueError(f"Envelope {request_id} not found")
        
        if envelope.state != ExecutionLifecycleState.QUEUED.value:
            raise ValueError(f"Cannot request approval from state {envelope.state}")
        
        envelope._transition_to(ExecutionLifecycleState.AWAITING_APPROVAL.value, "Approval requested")
        self.audit.log_event(
            request_id=request_id,
            event_type=ExecutionEventType.APPROVAL_REQUESTED.value
        )
    
    def grant_approval(self, request_id: str, approver_id: str) -> None:
        """Grant approval for execution."""
        envelope = self._envelopes.get(request_id)
        if not envelope:
            raise ValueError(f"Envelope {request_id} not found")
        
        if envelope.state != ExecutionLifecycleState.AWAITING_APPROVAL.value:
            raise ValueError(f"Cannot approve from state {envelope.state}")
        
        envelope.approval_gate_passed = True
        envelope.authorized_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        envelope._transition_to(ExecutionLifecycleState.AUTHORIZED.value, f"Approved by {approver_id}")
        
        self.audit.log_event(
            request_id=request_id,
            event_type=ExecutionEventType.APPROVAL_GRANTED.value,
            details={"approver": approver_id}
        )
        self.audit.log_event(
            request_id=request_id,
            event_type=ExecutionEventType.AUTHORIZED.value
        )
    
    def deny_approval(self, request_id: str, reason: str) -> None:
        """Deny approval for execution."""
        envelope = self._envelopes.get(request_id)
        if not envelope:
            raise ValueError(f"Envelope {request_id} not found")
        
        envelope.rejection_reason = RejectionReason(
            category=RejectionCategory.MANUAL_REJECTION.value,
            description=reason
        )
        envelope._transition_to(ExecutionLifecycleState.REJECTED.value, f"Approval denied: {reason}")
        
        self.audit.log_event(
            request_id=request_id,
            event_type=ExecutionEventType.APPROVAL_DENIED.value,
            details={"reason": reason}
        )
        self.audit.log_event(
            request_id=request_id,
            event_type=ExecutionEventType.REJECTED.value
        )
    
    def dispatch(self, request_id: str) -> None:
        """Dispatch authorized execution to target."""
        envelope = self._envelopes.get(request_id)
        if not envelope:
            raise ValueError(f"Envelope {request_id} not found")
        
        if envelope.state != ExecutionLifecycleState.AUTHORIZED.value:
            raise ValueError(f"Cannot dispatch from state {envelope.state}")
        
        envelope.dispatched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        envelope._transition_to(ExecutionLifecycleState.DISPATCHED.value, "Dispatched to target")
        
        self.audit.log_event(
            request_id=request_id,
            event_type=ExecutionEventType.DISPATCHED.value,
            details={"target": envelope.target_node_id}
        )
    
    def acknowledge(self, request_id: str) -> None:
        """Mark execution as acknowledged by target."""
        envelope = self._envelopes.get(request_id)
        if not envelope:
            raise ValueError(f"Envelope {request_id} not found")
        
        if envelope.state != ExecutionLifecycleState.DISPATCHED.value:
            raise ValueError(f"Cannot acknowledge from state {envelope.state}")
        
        envelope.acknowledged_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        envelope._transition_to(ExecutionLifecycleState.ACKNOWLEDGED.value, "Target acknowledged")
        
        self.audit.log_event(
            request_id=request_id,
            event_type=ExecutionEventType.ACKNOWLEDGED.value
        )
    
    def complete(self, request_id: str, result: Dict[str, Any]) -> None:
        """Mark execution as completed with result."""
        envelope = self._envelopes.get(request_id)
        if not envelope:
            raise ValueError(f"Envelope {request_id} not found")
        
        if envelope.state != ExecutionLifecycleState.ACKNOWLEDGED.value:
            raise ValueError(f"Cannot complete from state {envelope.state}")
        
        envelope.execution_result = result
        envelope.completed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        envelope._transition_to(ExecutionLifecycleState.COMPLETED.value, "Execution completed")
        
        self.audit.log_event(
            request_id=request_id,
            event_type=ExecutionEventType.COMPLETED.value,
            details={"result": result}
        )
    
    def fail(self, request_id: str, reason: str) -> None:
        """Mark execution as failed."""
        envelope = self._envelopes.get(request_id)
        if not envelope:
            raise ValueError(f"Envelope {request_id} not found")
        
        if envelope.is_terminal():
            raise ValueError(f"Cannot fail from terminal state {envelope.state}")
        
        envelope.failure_reason = reason
        envelope.failed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        envelope._transition_to(ExecutionLifecycleState.FAILED.value, f"Execution failed: {reason}")
        
        self.audit.log_event(
            request_id=request_id,
            event_type=ExecutionEventType.FAILED.value,
            details={"reason": reason}
        )
    
    def initiate_rollback(self, request_id: str, reason: str) -> bool:
        """Initiate rollback for execution."""
        envelope = self._envelopes.get(request_id)
        if not envelope:
            raise ValueError(f"Envelope {request_id} not found")
        
        if not envelope.rollback_path.can_rollback():
            return False
        
        can_initiate = envelope.rollback_path.initiate_rollback(reason)
        if not can_initiate:
            return False
        
        self.audit.log_event(
            request_id=request_id,
            event_type=ExecutionEventType.ROLLBACK_INITIATED.value,
            details={"reason": reason}
        )
        
        return True
    
    def complete_rollback(self, request_id: str) -> None:
        """Complete rollback for execution."""
        envelope = self._envelopes.get(request_id)
        if not envelope:
            raise ValueError(f"Envelope {request_id} not found")
        
        envelope.rollback_path.complete_rollback()
        envelope._transition_to(ExecutionLifecycleState.ROLLED_BACK.value, "Rollback completed")
        
        self.audit.log_event(
            request_id=request_id,
            event_type=ExecutionEventType.ROLLBACK_COMPLETED.value
        )
    
    def get_envelope(self, request_id: str) -> Optional[ExecutionRequestEnvelope]:
        """Get envelope by request ID."""
        return self._envelopes.get(request_id)
    
    def get_all_envelopes(self) -> List[ExecutionRequestEnvelope]:
        """Get all tracked envelopes."""
        return list(self._envelopes.values())
