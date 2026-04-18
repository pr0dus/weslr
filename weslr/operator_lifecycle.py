# operator_lifecycle.py - WESLR v48: Operator Lifecycle / Timeline Surface
# Creates a governed operator-facing lifecycle view so WESLR can clearly show how a
# proposal, recommendation, escalation, or recovery path evolved over time and what
# the next safe states are.
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


class LifecycleStatus(str, Enum):
    """Status of a lifecycle instance."""
    INITIATED = "initiated"  # Created but not active
    ACTIVE = "active"  # Currently in progress
    PAUSED = "paused"  # Temporarily suspended
    RESOLVED = "resolved"  # Successfully completed
    ESCALATED = "escalated"  # Escalated to higher authority
    ROLLED_BACK = "rolled_back"  # Reverted to previous state
    ABANDONED = "abandoned"  # Cancelled or废弃


class TransitionType(str, Enum):
    """Types of transitions in a lifecycle."""
    PROPOSAL_CREATED = "proposal_created"
    PROPOSAL_UPDATED = "proposal_updated"
    PROPOSAL_APPROVED = "proposal_approved"
    PROPOSAL_DENIED = "proposal_denied"
    PROPOSAL_DEPRECATED = "proposal_deprecated"
    
    RECOMMENDATION_CREATED = "recommendation_created"
    RECOMMENDATION_UPDATED = "recommendation_updated"
    RECOMMENDATION_APPLIED = "recommendation_applied"
    RECOMMENDATION_IGNORED = "recommendation_ignored"
    
    ESCALATION_TRIGGERED = "escalation_triggered"
    ESCALATION_RESOLVED = "escalation_resolved"
    
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_COMPLETED = "recovery_completed"
    RECOVERY_FAILED = "recovery_failed"
    
    STATE_CHANGED = "state_changed"
    CONTEXT_CHANGED = "context_changed"
    
    OTHER = "other"


class TimelineVisibility(str, Enum):
    """Visibility level for timeline events."""
    PRIVATE = "private"  # Only visible to operator
    OPERATOR = "operator"  # Visible to operators
    ADMIN = "admin"  # Visible to administrators
    PUBLIC = "public"  # Publicly visible (audit trail)


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class LifecycleTransition:
    """A single transition in the lifecycle timeline."""
    
    transition_id: str
    transition_type: str  # TransitionType.value
    timestamp: str
    source: str = "system"  # AuditSource.value
    
    # Affected object
    affected_object_id: Optional[str] = None
    affected_object_type: Optional[str] = None
    
    # State
    from_state: Optional[Dict[str, Any]] = None
    to_state: Optional[Dict[str, Any]] = None
    current_state: Optional[Dict[str, Any]] = None
    
    # Context
    context_id: Optional[str] = None
    deployment_role: Optional[str] = None
    
    # Approval outcome
    approval_status: Optional[str] = None  # approved/denied/escalated
    approval_notes: Optional[str] = None
    
    # Evidence
    evidence_references: List[str] = field(default_factory=list)
    
    # Metadata
    level: str = "info"  # AuditLevel.value
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "transition_type": self.transition_type,
            "timestamp": self.timestamp,
            "source": self.source,
            "affected_object_id": self.affected_object_id,
            "affected_object_type": self.affected_object_type,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "current_state": self.current_state,
            "context_id": self.context_id,
            "deployment_role": self.deployment_role,
            "approval_status": self.approval_status,
            "approval_notes": self.approval_notes,
            "evidence_references": self.evidence_references,
            "level": self.level,
            "created_at": self.created_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LifecycleTransition:
        data["evidence_references"] = data.get("evidence_references", [])
        data.setdefault("source", "system")
        data.setdefault("level", "info")
        return cls(**data)


@dataclass
class LifecycleRollbackPoint:
    """A rollback point in the lifecycle timeline."""
    
    rollback_id: str
    transition_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    state_snapshot: Dict[str, Any] = field(default_factory=dict)
    
    # Rollback properties
    rollback_type: str = "full"  # full, partial
    can_revert: bool = True
    notes: Optional[str] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rollback_id": self.rollback_id,
            "transition_id": self.transition_id,
            "timestamp": self.timestamp,
            "state_snapshot": self.state_snapshot,
            "rollback_type": self.rollback_type,
            "can_revert": self.can_revert,
            "notes": self.notes,
            "created_at": self.created_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LifecycleRollbackPoint:
        data["state_snapshot"] = data.get("state_snapshot", {})
        return cls(**data)


@dataclass
class LifecycleTimeline:
    """Complete lifecycle timeline for an object."""
    
    timeline_id: str
    affected_object_id: str
    affected_object_type: str
    
    # Lifecycle state
    status: str = LifecycleStatus.INITIATED.value
    current_state: Dict[str, Any] = field(default_factory=dict)
    
    # Transitions in chronological order
    transitions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Rollback points
    rollback_points: List[Dict[str, Any]] = field(default_factory=list)
    
    # Allowed transitions
    allowed_transitions: List[str] = field(default_factory=list)
    
    # Forensic analysis
    summary: Optional[str] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    # Computed properties (not serialized, for convenience)
    @property
    def transition_count(self) -> int:
        """Return number of transitions."""
        return len(self.transitions)
    
    @property
    def rollback_point_count(self) -> int:
        """Return number of rollback points."""
        return len(self.rollback_points)
    
    def add_transition(self, transition: Dict[str, Any]) -> None:
        """Add a transition to the timeline."""
        self.transitions.append(transition)
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def add_rollback_point(self, rollback: Dict[str, Any]) -> None:
        """Add a rollback point."""
        self.rollback_points.append(rollback)
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def get_transitions_by_type(self, transition_type: str) -> List[Dict[str, Any]]:
        """Get transitions by type."""
        return [t for t in self.transitions if t.get("transition_type") == transition_type]
    
    def get_transitions_by_actor(self, actor_id: str) -> List[Dict[str, Any]]:
        """Get transitions by actor ID."""
        return [t for t in self.transitions if t.get("author") == actor_id]
    
    def get_transitions_by_approval_status(self, status: str) -> List[Dict[str, Any]]:
        """Get transitions by approval status."""
        return [t for t in self.transitions if t.get("approval_status") == status]
    
    def get_next_allowed_states(self) -> List[str]:
        """Get list of next allowed states based on current status."""
        state_transitions = {
            LifecycleStatus.INITIATED.value: [LifecycleStatus.ACTIVE.value],
            LifecycleStatus.ACTIVE.value: [
                LifecycleStatus.RESOLVED.value,
                LifecycleStatus.PAUSED.value,
                LifecycleStatus.ESCALATED.value,
            ],
            LifecycleStatus.PAUSED.value: [
                LifecycleStatus.ACTIVE.value,
                LifecycleStatus.ABANDONED.value,
            ],
            LifecycleStatus.RESOLVED.value: [],
            LifecycleStatus.ESCALATED.value: [
                LifecycleStatus.RESOLVED.value,
                LifecycleStatus.ROLLED_BACK.value,
                LifecycleStatus.ABANDONED.value,
            ],
            LifecycleStatus.ROLLED_BACK.value: [
                LifecycleStatus.ACTIVE.value,
                LifecycleStatus.ABANDONED.value,
            ],
            LifecycleStatus.ABANDONED.value: [],
        }
        return state_transitions.get(self.status, [])
    
    def generate_summary(self) -> str:
        """Generate a concise lifecycle summary."""
        if not self.transitions:
            return "No transitions recorded"
        
        summary_parts = []
        
        # Count event types
        event_types = {}
        for transition in self.transitions:
            transition_type = transition.get("transition_type", "unknown")
            event_types[transition_type] = event_types.get(transition_type, 0) + 1
        
        # Build summary
        event_list = sorted(event_types.items(), key=lambda x: x[1], reverse=True)
        event_str = ", ".join(f"{t}({c})" for t, c in event_list[:5])
        summary_parts.append(f"Transitions: {event_str}")
        
        # Approval summary
        approvals = self.get_transitions_by_approval_status("approved")
        denials = self.get_transitions_by_approval_status("denied")
        summary_parts.append(f"Approvals: {len(approvals)}, Denials: {len(denials)}")
        
        # Actor summary
        actors = set(t.get("author") for t in self.transitions if t.get("author"))
        if actors:
            summary_parts.append(f"Actors: {', '.join(sorted(actors))}")
        
        # Rollback points
        if self.rollback_points:
            summary_parts.append(f"Rollback points: {len(self.rollback_points)}")
        
        self.summary = "; ".join(summary_parts)
        return self.summary
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timeline_id": self.timeline_id,
            "affected_object_id": self.affected_object_id,
            "affected_object_type": self.affected_object_type,
            "status": self.status,
            "current_state": self.current_state,
            "transition_count": len(self.transitions),
            "transitions": self.transitions,
            "rollback_point_count": len(self.rollback_points),
            "rollback_points": self.rollback_points,
            "allowed_transitions": self.allowed_transitions,
            "summary": self.summary,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LifecycleTimeline:
        # Filter out computed properties that aren't constructor args
        computed_fields = {"transition_count", "rollback_point_count"}
        clean_data = {k: v for k, v in data.items() if k not in computed_fields}
        clean_data["transitions"] = clean_data.get("transitions", [])
        clean_data["rollback_points"] = clean_data.get("rollback_points", [])
        clean_data["allowed_transitions"] = clean_data.get("allowed_transitions", [])
        clean_data.setdefault("status", "initiated")
        clean_data.setdefault("current_state", {})
        return cls(**clean_data)


# ============================================================================
# TIMELINE ENGINE
# ============================================================================


class OperatorLifecycleEngine:
    """Engine for managing operator lifecycle timelines.
    
    Provides transparent, reversible lifecycle tracking for operators.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize operator lifecycle engine."""
        self.storage_path = storage_path or "/data/data/com.termux/files/home/.openclaw/workspace/weslr/operator_lifecycle/"
        self.timelines: Dict[str, LifecycleTimeline] = {}
        self._ensure_storage_exists()
        self._load_timelines()
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _load_timelines(self) -> None:
        """Load timelines from storage."""
        import os
        import glob
        
        if not os.path.exists(self.storage_path):
            return
        
        for filepath in glob.glob(os.path.join(self.storage_path, "*.json")):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    timeline = LifecycleTimeline.from_dict(data)
                    self.timelines[timeline.timeline_id] = timeline
            except Exception:
                continue
    
    def create_timeline(
        self,
        timeline_id: str,
        affected_object_id: str,
        affected_object_type: str,
        author: Optional[str] = None,
    ) -> LifecycleTimeline:
        """Create a new lifecycle timeline."""
        timeline = LifecycleTimeline(
            timeline_id=timeline_id,
            affected_object_id=affected_object_id,
            affected_object_type=affected_object_type,
            author=author,
        )
        self.timelines[timeline_id] = timeline
        self._save_timeline(timeline)
        return timeline
    
    def get_timeline(self, timeline_id: str) -> Optional[LifecycleTimeline]:
        """Get a timeline by ID."""
        return self.timelines.get(timeline_id)
    
    def get_timeline_by_object(self, object_id: str) -> Optional[LifecycleTimeline]:
        """Get a timeline by affected object ID."""
        for timeline in self.timelines.values():
            if timeline.affected_object_id == object_id:
                return timeline
        return None
    
    def _save_timeline(self, timeline: LifecycleTimeline) -> None:
        """Save a timeline to storage."""
        import os
        
        filepath = os.path.join(self.storage_path, f"{timeline.timeline_id}.json")
        with open(filepath, "w") as f:
            json.dump(timeline.to_dict(), f, indent=2)
    
    def record_transition(
        self,
        timeline_id: str,
        transition_type: str,
        affected_object_id: Optional[str] = None,
        from_state: Optional[Dict[str, Any]] = None,
        to_state: Optional[Dict[str, Any]] = None,
        current_state: Optional[Dict[str, Any]] = None,
        context_id: Optional[str] = None,
        approval_status: Optional[str] = None,
        approval_notes: Optional[str] = None,
        actor_id: Optional[str] = None,
        author: Optional[str] = None,
    ) -> LifecycleTransition:
        """Record a transition in the timeline."""
        timeline = self.get_timeline(timeline_id)
        if not timeline:
            raise ValueError(f"Timeline {timeline_id} not found")
        
        transition = LifecycleTransition(
            transition_id=f"transition_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            transition_type=transition_type,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            affected_object_id=affected_object_id or timeline.affected_object_id,
            affected_object_type=timeline.affected_object_type,
            from_state=from_state,
            to_state=to_state,
            current_state=current_state,
            context_id=context_id,
            approval_status=approval_status,
            approval_notes=approval_notes,
            author=author or timeline.author,
        )
        
        timeline.add_transition(transition.to_dict())
        self._save_timeline(timeline)
        
        return transition
    
    def record_rollback_point(
        self,
        timeline_id: str,
        transition_id: str,
        state_snapshot: Dict[str, Any],
        rollback_type: str = "full",
        can_revert: bool = True,
        notes: Optional[str] = None,
        author: Optional[str] = None,
    ) -> LifecycleRollbackPoint:
        """Record a rollback point in the timeline."""
        timeline = self.get_timeline(timeline_id)
        if not timeline:
            raise ValueError(f"Timeline {timeline_id} not found")
        
        rollback = LifecycleRollbackPoint(
            rollback_id=f"rollback_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            transition_id=transition_id,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            state_snapshot=state_snapshot,
            rollback_type=rollback_type,
            can_revert=can_revert,
            notes=notes,
            author=author or timeline.author,
        )
        
        timeline.add_rollback_point(rollback.to_dict())
        self._save_timeline(timeline)
        
        return rollback
    
    def update_status(
        self,
        timeline_id: str,
        status: str,
        current_state: Optional[Dict[str, Any]] = None,
        allowed_transitions: Optional[List[str]] = None,
    ) -> None:
        """Update timeline status."""
        timeline = self.get_timeline(timeline_id)
        if not timeline:
            raise ValueError(f"Timeline {timeline_id} not found")
        
        timeline.status = status
        if current_state:
            timeline.current_state = current_state
        if allowed_transitions:
            timeline.allowed_transitions = allowed_transitions
        timeline.generate_summary()
        self._save_timeline(timeline)
    
    def get_timeline_summary(self, timeline_id: str) -> Dict[str, Any]:
        """Get summary for a timeline."""
        timeline = self.get_timeline(timeline_id)
        if not timeline:
            return {
                "timeline_id": timeline_id,
                "timeline_exists": False,
                "transition_count": 0,
                "status": "not_found",
            }
        
        timeline.generate_summary()
        
        return {
            "timeline_id": timeline.timeline_id,
            "affected_object_id": timeline.affected_object_id,
            "affected_object_type": timeline.affected_object_type,
            "status": timeline.status,
            "current_state": timeline.current_state,
            "transition_count": len(timeline.transitions),
            "rollback_point_count": len(timeline.rollback_points),
            "allowed_transitions": timeline.get_next_allowed_states(),
            "summary": timeline.summary,
            "created_at": timeline.created_at,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary."""
        return {
            "timeline_count": len(self.timelines),
            "timelines": {k: v.to_dict() for k, v in self.timelines.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_state_transition(
    state_dict: Dict[str, Any],
    lifecycle_engine: OperatorLifecycleEngine = None,
    object_id: str = None,
    transition_type: str = None,
) -> Dict[str, Any]:
    """Add lifecycle context to state transitions.
    
    This is purely additive — no migration required.
    
    v48: Lifecycle engine provides timeline surface for state transitions.
    """
    if "lifecycle_context" not in state_dict:
        state_dict["lifecycle_context"] = None
    
    if lifecycle_engine and object_id:
        try:
            summary = lifecycle_engine.get_timeline_summary(object_id)
            state_dict["lifecycle_context"] = {
                "timeline_summary": summary.get("summary", "No summary"),
                "transition_count": summary.get("transition_count", 0),
                "allowed_transitions": summary.get("allowed_transitions", []),
                "has_rollback_points": summary.get("rollback_point_count", 0) > 0,
            }
        except Exception:
            pass  # Silent fallback to default
    
    return state_dict


def integrate_with_audit_ledger(
    audit_dict: Dict[str, Any],
    lifecycle_engine: OperatorLifecycleEngine = None,
    object_id: str = None,
) -> Dict[str, Any]:
    """Add lifecycle context to audit ledger.
    
    This is purely additive — no migration required.
    
    v48: Lifecycle provides timeline traceability for audit events.
    """
    if "lifecycle_context" not in audit_dict:
        audit_dict["lifecycle_context"] = None
    
    if lifecycle_engine and object_id:
        try:
            summary = lifecycle_engine.get_timeline_summary(object_id)
            audit_dict["lifecycle_context"] = {
                "timeline_summary": summary.get("summary", "No summary"),
                "transition_count": summary.get("transition_count", 0),
                "rollback_count": summary.get("rollback_point_count", 0),
            }
        except Exception:
            pass  # Silent fallback to default
    
    return audit_dict


def integrate_with_audit_replay(
    replay_dict: Dict[str, Any],
    lifecycle_engine: OperatorLifecycleEngine = None,
    object_id: str = None,
) -> Dict[str, Any]:
    """Add lifecycle context to audit replay/forensics.
    
    This is purely additive — no migration required.
    
    v48: Lifecycle provides timeline surface for forensics traces.
    """
    if "lifecycle_context" not in replay_dict:
        replay_dict["lifecycle_context"] = None
    
    if lifecycle_engine and object_id:
        try:
            summary = lifecycle_engine.get_timeline_summary(object_id)
            replay_dict["lifecycle_context"] = {
                "timeline_exists": summary.get("transition_count", 0) > 0,
                "timeline_summary": summary.get("summary", "No summary"),
                "allowed_transitions": summary.get("allowed_transitions", []),
                "current_state": summary.get("current_state", {}),
            }
        except Exception:
            pass  # Silent fallback to default
    
    return replay_dict


def integrate_with_operator_views(
    operator_dict: Dict[str, Any],
    lifecycle_engine: OperatorLifecycleEngine = None,
    object_id: str = None,
) -> Dict[str, Any]:
    """Add lifecycle context to operator-facing views.
    
    This is purely additive — no migration required.
    
    v48: Lifecycle provides concise timeline summaries for operators.
    """
    if "lifecycle_context" not in operator_dict:
        operator_dict["lifecycle_context"] = None
    
    if lifecycle_engine and object_id:
        try:
            summary = lifecycle_engine.get_timeline_summary(object_id)
            
            if summary.get("transition_count", 0) > 0:
                operator_dict["lifecycle_context"] = {
                    "timeline_summary": summary.get("summary", "No summary"),
                    "allowed_transitions": summary.get("allowed_transitions", []),
                    "current_status": summary.get("status", "unknown"),
                    "has_rollback_points": summary.get("rollback_point_count", 0) > 0,
                }
        except Exception:
            pass  # Silent fallback to default
    
    return operator_dict


def integrate_with_final_decision_composer(
    operator_dict: Dict[str, Any],
    composer: Any = None,
) -> Dict[str, Any]:
    """Add final decision composer context to operator-facing views.
    
    This is purely additive — no migration required.
    
    v51: Final decision composer provides assembled recommendations for operator review.
    """
    if "final_decision_context" not in operator_dict:
        operator_dict["final_decision_context"] = None
    
    if composer:
        latest = composer.get_latest_recommendation() if hasattr(composer, "get_latest_recommendation") else None
        operator_dict["final_decision_context"] = {
            "composer_storage_path": getattr(composer, "storage_path", None),
            "recommendation_count": len(composer.recommendations) if hasattr(composer, "recommendations") else 0,
            "has_latest_recommendation": latest is not None,
            "latest_recommendation_id": latest.recommendation_id if latest else None,
            "latest_recommendation_type": latest.recommendation_type if latest else None,
        }
    
    return operator_dict
