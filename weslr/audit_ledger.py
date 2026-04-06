# audit_ledger.py - WESLR v42: Audit / Traceability Ledger Layer
# Creates a governed audit/traceability layer so WESLR can preserve a durable record of
# decisions, approvals, proof-gate outcomes, escalations, and state transitions.
# Additive only, transparent, reversible, role-aware, non-manipulative.
# No repo drift (local to WESLR scope).

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# ENUMS
# ============================================================================


class LedgerEventType(str, Enum):
    """Types of events that can be recorded in the ledger."""
    # Governance events
    PROPOSAL_CREATED = "proposal_created"
    PROPOSAL_UPDATED = "proposal_updated"
    PROPOSAL_APPROVED = "proposal_approved"
    PROPOSAL_DENIED = "proposal_denied"
    PROPOSAL_DEFERRED = "proposal_deferred"
    PROPOSAL_DEPRECATED = "proposal_deprecated"
    
    # Proof gate events
    PROOF_REQUESTED = "proof_requested"
    PROOF_SATISFIED = "proof_satisfied"
    PROOF_FAILED = "proof_failed"
    EXECUTION_ELIGIBLE = "execution_eligible"
    EXECUTION_BLOCKED = "execution_blocked"
    
    # Escalation events
    ESCALATION_TRIGGERED = "escalation_triggered"
    ESCALATION_APPROVED = "escalation_approved"
    ESCALATION_DENIED = "escalation_denied"
    ESCALATION_ESCALATED = "escalation_escalated"
    
    # State transitions
    STATE_CHANGED = "state_changed"
    CONTEXT_CHANGED = "context_changed"
    
    # System events
    CONFIGURATION_CHANGED = "configuration_changed"
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "systemstopped"
    
    # Handoff events
    HANDOFF_CREATED = "handoff_created"
    HANDOFF_REVIEWED = "handoff_reviewed"
    HANDOFF_TIMED_OUT = "handoff_timed_out"
    
    OTHER = "other"


class AuditSource(str, Enum):
    """Sources of audit events."""
    SYSTEM = "system"  # Automated system events
    OPERATOR = "operator"  # Human operator
    ADMINISTRATOR = "administrator"  # Administrator
    APIS_CALLER = "apis_caller"  # External API caller
    SCHEDULED_TASK = "scheduled_task"  # Scheduled tasks
    INTEGRATION = "integration"  # External integrations


class AuditLevel(str, Enum):
    """Severity level of audit events."""
    DEBUG = "debug"  # Detailed diagnostic info
    INFO = "info"  # General information
    WARN = "warn"  # Warning conditions
    ERROR = "error"  # Error conditions
    CRITICAL = "critical"  # Critical conditions requiring immediate attention


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class LedgerEvent:
    """A single event recorded in the audit ledger."""
    
    event_id: str
    event_type: str  # LedgerEventType.value
    timestamp: str
    source: str = AuditSource.SYSTEM.value
    actor_id: Optional[str] = None  # Human actor if applicable
    actor_role: Optional[str] = None  # Role of actor if applicable
    
    # Affected object
    affected_object_id: Optional[str] = None
    affected_object_type: Optional[str] = None
    
    # Evidence
    evidence_references: List[str] = field(default_factory=list)
    
    # Approval outcome
    approval_status: Optional[str] = None  # approved/denied/escalated
    approval_notes: Optional[str] = None
    
    # State transitions
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    
    # Context
    context_id: Optional[str] = None
    deployment_role: Optional[str] = None
    capability_boundary_id: Optional[str] = None
    escalation_id: Optional[str] = None
    
    # Metadata
    level: str = AuditLevel.INFO.value
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "source": self.source,
            "actor_id": self.actor_id,
            "actor_role": self.actor_role,
            "affected_object_id": self.affected_object_id,
            "affected_object_type": self.affected_object_type,
            "evidence_references": self.evidence_references,
            "approval_status": self.approval_status,
            "approval_notes": self.approval_notes,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "context_id": self.context_id,
            "deployment_role": self.deployment_role,
            "capability_boundary_id": self.capability_boundary_id,
            "escalation_id": self.escalation_id,
            "level": self.level,
            "created_at": self.created_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LedgerEvent:
        data["evidence_references"] = data.get("evidence_references", [])
        return cls(**data)


@dataclass
class AuditLedger:
    """Audit ledger with events and metadata."""
    
    ledger_id: str
    name: str = "audit_ledger"
    description: str = "WESLR audit ledger for governance traceability"
    
    # Events
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def add_event(self, event: Dict[str, Any]) -> None:
        """Add an event to the ledger."""
        self.events.append(event)
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Get events by type."""
        return [e for e in self.events if e.get("event_type") == event_type]
    
    def get_events_by_object(self, object_id: str) -> List[Dict[str, Any]]:
        """Get events by affected object ID."""
        return [e for e in self.events if e.get("affected_object_id") == object_id]
    
    def get_events_by_context(self, context_id: str) -> List[Dict[str, Any]]:
        """Get events by context ID."""
        return [e for e in self.events if e.get("context_id") == context_id]
    
    def get_events_by_actor(self, actor_id: str) -> List[Dict[str, Any]]:
        """Get events by actor ID."""
        return [e for e in self.events if e.get("actor_id") == actor_id]
    
    def get_events_by_timestamp_range(
        self, start_timestamp: str, end_timestamp: str
    ) -> List[Dict[str, Any]]:
        """Get events within a timestamp range."""
        return [
            e
            for e in self.events
            if start_timestamp <= e.get("timestamp", "") <= end_timestamp
        ]
    
    def get_approval_events(self) -> List[Dict[str, Any]]:
        """Get all approval-related events."""
        approval_types = [
            LedgerEventType.PROPOSAL_APPROVED.value,
            LedgerEventType.PROPOSAL_DENIED.value,
            LedgerEventType.ESCALATION_APPROVED.value,
            LedgerEventType.ESCALATION_DENIED.value,
            LedgerEventType.ESCALATION_ESCALATED.value,
        ]
        return [e for e in self.events if e.get("event_type") in approval_types]
    
    def get_trace_summary(self, object_id: str) -> Dict[str, Any]:
        """Get a trace summary for an object."""
        object_events = self.get_events_by_object(object_id)
        
        return {
            "object_id": object_id,
            "event_count": len(object_events),
            "first_event": object_events[0] if object_events else None,
            "last_event": object_events[-1] if object_events else None,
            "event_types": list(set(e.get("event_type") for e in object_events)),
            "approval_count": sum(1 for e in object_events if e.get("approval_status")),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ledger_id": self.ledger_id,
            "name": self.name,
            "description": self.description,
            "event_count": len(self.events),
            "events": self.events,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuditLedger:
        # Filter out computed fields
        data = {k: v for k, v in data.items() if k in ["ledger_id", "name", "description", "events", "created_at", "updated_at", "author"]}
        data["events"] = data.get("events", [])
        return cls(**data)


# ============================================================================
# LEDGER ENGINE
# ============================================================================


class AuditLedgerEngine:
    """Engine for managing audit ledgers and traceability.
    
    Provides transparent, reversible audit logging.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize audit ledger engine."""
        self.storage_path = storage_path or "/data/data/com.termux/files/home/.openclaw/workspace/weslr/audit_ledger/"
        self.ledgers: Dict[str, AuditLedger] = {}
        self._ensure_storage_exists()
        self._load_ledgers()
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _load_ledgers(self) -> None:
        """Load ledgers from storage."""
        import os
        import glob
        
        if not os.path.exists(self.storage_path):
            return
        
        for filepath in glob.glob(os.path.join(self.storage_path, "*.json")):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    ledger = AuditLedger.from_dict(data)
                    self.ledgers[ledger.ledger_id] = ledger
            except Exception:
                continue
    
    def create_ledger(
        self,
        ledger_id: str,
        name: str = "audit_ledger",
        description: str = "WESLR audit ledger for governance traceability",
        author: Optional[str] = None,
    ) -> AuditLedger:
        """Create a new audit ledger."""
        ledger = AuditLedger(
            ledger_id=ledger_id,
            name=name,
            description=description,
            author=author,
        )
        self.ledgers[ledger_id] = ledger
        self._save_ledger(ledger)
        return ledger
    
    def get_ledger(self, ledger_id: str) -> Optional[AuditLedger]:
        """Get a ledger by ID."""
        return self.ledgers.get(ledger_id)
    
    def _save_ledger(self, ledger: AuditLedger) -> None:
        """Save a ledger to storage."""
        import os
        
        filepath = os.path.join(self.storage_path, f"{ledger.ledger_id}.json")
        with open(filepath, "w") as f:
            json.dump(ledger.to_dict(), f, indent=2)
    
    def record_proposal_created(
        self,
        proposal_id: str,
        title: str,
        description: str,
        source: str = AuditSource.SYSTEM.value,
        actor_id: Optional[str] = None,
        context_id: Optional[str] = None,
        author: Optional[str] = None,
    ) -> LedgerEvent:
        """Record proposal creation event."""
        event = LedgerEvent(
            event_id=f"event_{proposal_id}_created",
            event_type=LedgerEventType.PROPOSAL_CREATED.value,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            source=source,
            actor_id=actor_id,
            affected_object_id=proposal_id,
            affected_object_type="proposal",
            context_id=context_id,
            author=author,
        )
        
        # Add to default ledger
        default_ledger = self.get_default_ledger()
        default_ledger.add_event(event.to_dict())
        self._save_ledger(default_ledger)
        
        return event
    
    def record_proposal_approved(
        self,
        proposal_id: str,
        approved_by: str,
        notes: Optional[str] = None,
        context_id: Optional[str] = None,
        author: Optional[str] = None,
    ) -> LedgerEvent:
        """Record proposal approval event."""
        event = LedgerEvent(
            event_id=f"event_{proposal_id}_approved",
            event_type=LedgerEventType.PROPOSAL_APPROVED.value,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            source=AuditSource.OPERATOR.value,
            actor_id=approved_by,
            actor_role="operator",
            affected_object_id=proposal_id,
            affected_object_type="proposal",
            approval_status="approved",
            approval_notes=notes,
            context_id=context_id,
            author=author,
        )
        
        # Add to default ledger
        default_ledger = self.get_default_ledger()
        default_ledger.add_event(event.to_dict())
        self._save_ledger(default_ledger)
        
        return event
    
    def record_proposal_denied(
        self,
        proposal_id: str,
        denied_by: str,
        notes: Optional[str] = None,
        context_id: Optional[str] = None,
        author: Optional[str] = None,
    ) -> LedgerEvent:
        """Record proposal denial event."""
        event = LedgerEvent(
            event_id=f"event_{proposal_id}_denied",
            event_type=LedgerEventType.PROPOSAL_DENIED.value,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            source=AuditSource.OPERATOR.value,
            actor_id=denied_by,
            actor_role="operator",
            affected_object_id=proposal_id,
            affected_object_type="proposal",
            approval_status="denied",
            approval_notes=notes,
            context_id=context_id,
            author=author,
        )
        
        # Add to default ledger
        default_ledger = self.get_default_ledger()
        default_ledger.add_event(event.to_dict())
        self._save_ledger(default_ledger)
        
        return event
    
    def record_proof_requested(
        self,
        proposal_id: str,
        proof_type: str,
        requested_by: str = "system",
        context_id: Optional[str] = None,
        author: Optional[str] = None,
    ) -> LedgerEvent:
        """Record proof request event."""
        event = LedgerEvent(
            event_id=f"event_{proposal_id}_proof_{proof_type}",
            event_type=LedgerEventType.PROOF_REQUESTED.value,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            source=AuditSource.SYSTEM.value,
            actor_id=requested_by,
            affected_object_id=proposal_id,
            affected_object_type="proposal",
            context_id=context_id,
            author=author,
        )
        
        # Add to default ledger
        default_ledger = self.get_default_ledger()
        default_ledger.add_event(event.to_dict())
        self._save_ledger(default_ledger)
        
        return event
    
    def record_escalation_triggered(
        self,
        escalation_id: str,
        trigger: str,
        reason: str,
        required_role: str,
        context_id: Optional[str] = None,
        author: Optional[str] = None,
    ) -> LedgerEvent:
        """Record escalation trigger event."""
        event = LedgerEvent(
            event_id=f"event_{escalation_id}_triggered",
            event_type=LedgerEventType.ESCALATION_TRIGGERED.value,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            source=AuditSource.SYSTEM.value,
            affected_object_id=escalation_id,
            affected_object_type="escalation",
            before_state={"status": "pending"},
            after_state={"status": "pending", "trigger": trigger, "reason": reason},
            context_id=context_id,
            author=author,
        )
        
        # Add to default ledger
        default_ledger = self.get_default_ledger()
        default_ledger.add_event(event.to_dict())
        self._save_ledger(default_ledger)
        
        return event
    
    def record_escalation_approved(
        self,
        escalation_id: str,
        approved_by: str,
        notes: Optional[str] = None,
        context_id: Optional[str] = None,
        author: Optional[str] = None,
    ) -> LedgerEvent:
        """Record escalation approval event."""
        event = LedgerEvent(
            event_id=f"event_{escalation_id}_approved",
            event_type=LedgerEventType.ESCALATION_APPROVED.value,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            source=AuditSource.OPERATOR.value,
            actor_id=approved_by,
            actor_role="operator",
            affected_object_id=escalation_id,
            affected_object_type="escalation",
            approval_status="approved",
            approval_notes=notes,
            before_state={"status": "pending"},
            after_state={"status": "approved"},
            context_id=context_id,
            author=author,
        )
        
        # Add to default ledger
        default_ledger = self.get_default_ledger()
        default_ledger.add_event(event.to_dict())
        self._save_ledger(default_ledger)
        
        return event
    
    def record_escalation_denied(
        self,
        escalation_id: str,
        denied_by: str,
        notes: Optional[str] = None,
        context_id: Optional[str] = None,
        author: Optional[str] = None,
    ) -> LedgerEvent:
        """Record escalation denial event."""
        event = LedgerEvent(
            event_id=f"event_{escalation_id}_denied",
            event_type=LedgerEventType.ESCALATION_DENIED.value,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            source=AuditSource.OPERATOR.value,
            actor_id=denied_by,
            actor_role="operator",
            affected_object_id=escalation_id,
            affected_object_type="escalation",
            approval_status="denied",
            approval_notes=notes,
            before_state={"status": "pending"},
            after_state={"status": "denied"},
            context_id=context_id,
            author=author,
        )
        
        # Add to default ledger
        default_ledger = self.get_default_ledger()
        default_ledger.add_event(event.to_dict())
        self._save_ledger(default_ledger)
        
        return event
    
    def get_default_ledger(self) -> AuditLedger:
        """Get the default audit ledger (create if needed)."""
        default_id = "default"
        if default_id not in self.ledgers:
            return self.create_ledger(default_id)
        return self.ledgers[default_id]
    
    def get_trace_summary(self, object_id: str) -> Dict[str, Any]:
        """Get trace summary for an object from default ledger."""
        default_ledger = self.get_default_ledger()
        return default_ledger.get_trace_summary(object_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary."""
        return {
            "ledger_count": len(self.ledgers),
            "ledgers": {k: v.to_dict() for k, v in self.ledgers.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_proposals(
    proposal_dict: Dict[str, Any],
    ledger_engine: AuditLedgerEngine = None,
    proposal_id: str = None,
) -> Dict[str, Any]:
    """Add ledger context to proposals.
    
    This is purely additive — no migration required.
    
    v42: Ledger provides audit trail and traceability for proposals.
    """
    if "audit_ledger_context" not in proposal_dict:
        proposal_dict["audit_ledger_context"] = None
    
    if ledger_engine and proposal_id:
        try:
            summary = ledger_engine.get_trace_summary(proposal_id)
            proposal_dict["audit_ledger_context"] = {
                "trace_summary": summary,
                "event_count": summary.get("event_count", 0),
                "approval_count": summary.get("approval_count", 0),
            }
        except Exception:
            pass  # Silent fallback to default
    
    return proposal_dict


def integrate_with_proof_gate(
    proof_dict: Dict[str, Any],
    ledger_engine: AuditLedgerEngine = None,
    proposal_id: str = None,
) -> Dict[str, Any]:
    """Add ledger context to proof gate.
    
    This is purely additive — no migration required.
    
    v42: Ledger provides proof audit trail.
    """
    if "audit_ledger_context" not in proof_dict:
        proof_dict["audit_ledger_context"] = None
    
    if ledger_engine and proposal_id:
        try:
            summary = ledger_engine.get_trace_summary(proposal_id)
            proof_dict["audit_ledger_context"] = {
                "trace_summary": summary,
                "proof_event_count": sum(
                    1 for e in summary.get("event_types", [])
                    if "proof" in e.lower()
                ),
            }
        except Exception:
            pass  # Silent fallback to default
    
    return proof_dict


def integrate_with_escalation(
    escalation_dict: Dict[str, Any],
    ledger_engine: AuditLedgerEngine = None,
    escalation_id: str = None,
) -> Dict[str, Any]:
    """Add ledger context to escalation.
    
    This is purely additive — no migration required.
    
    v42: Ledger provides escalation audit trail and approval history.
    """
    if "audit_ledger_context" not in escalation_dict:
        escalation_dict["audit_ledger_context"] = None
    
    if ledger_engine and escalation_id:
        try:
            summary = ledger_engine.get_trace_summary(escalation_id)
            escalation_dict["audit_ledger_context"] = {
                "trace_summary": summary,
                "approval_count": summary.get("approval_count", 0),
            }
        except Exception:
            pass  # Silent fallback to default
    
    return escalation_dict


def integrate_with_governance_surface(
    governance_dict: Dict[str, Any],
    ledger_engine: AuditLedgerEngine = None,
    context_id: str = None,
) -> Dict[str, Any]:
    """Add ledger context to governance surface.
    
    This is purely additive — no migration required.
    
    v42: Ledger surfaces traceability summary clearly to operators.
    """
    if "audit_ledger_context" not in governance_dict:
        governance_dict["audit_ledger_context"] = None
    
    if ledger_engine and context_id:
        try:
            # Get all events for the context
            default_ledger = ledger_engine.get_default_ledger()
            context_events = default_ledger.get_events_by_context(context_id)
            
            governance_dict["audit_ledger_context"] = {
                "event_count": len(context_events),
                "events": context_events[:10],  # First 10 events for review
                "has_approval": any(e.get("approval_status") for e in context_events),
                "traceable": len(context_events) > 0,
            }
        except Exception:
            pass  # Silent fallback to default
    
    return governance_dict
