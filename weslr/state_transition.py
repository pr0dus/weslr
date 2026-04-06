# state_transition.py - WESLR v47: State Transition / Outcome Orchestration Layer
# Creates a governed transition layer so WESLR can explicitly represent and manage how
# blocked, deferred, escalated, recovered, approved, or calibrated states evolve over time.
# Additive only, transparent, reversible, role-aware, non-manipulative.
# No repo drift (local to WESLR scope).

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================================
# ENUMS
# ============================================================================


class TransitionState(str, Enum):
    """Possible states for governance objects."""
    # Core states
    DRAFT = "draft"  # Initial state
    PENDING = "pending"  # Awaiting review/approval
    ACTIVE = "active"  # Currently in effect
    BLOCKED = "blocked"  # Blocked by constraints
    DEFERRED = "deferred"  # Postponed
    APPROVED = "approved"  # Approved for execution
    DENIED = "denied"  # Explicitly denied
    EXECUTED = "executed"  # Successfully executed
    FAILED = "failed"  # Execution failed
    ROLLED_BACK = "rolled_back"  # Rolled back after execution
    CANCELLED = "cancelled"  # Cancelled before execution
    
    # Recovery states
    RECOVERED = "recovered"  # Recovered from blocked state
    ESCALATED = "escalated"  # Escalated to human
    CALIBRATED = "calibrated"  # Post-execution calibration
    FEEDBACK_RECEIVED = "feedback_received"  # Feedback received from outcome


class TransitionTrigger(str, Enum):
    """Triggers that cause state transitions."""
    # Creation and submission
    CREATED = "created"  # Object created
    SUBMITTED = "submitted"  # Submitted for review
    
    # Review and approval
    REVIEW_STARTED = "review_started"  # Review process started
    REVIEW_COMPLETE = "review_complete"  # Review process completed
    APPROVED = "approved"  # Approved
    DENIED = "denied"  # Denied
    REJECTED = "rejected"  # Explicitly rejected
    
    # Execution
    EXECUTED = "executed"  # Execution started
    EXECUTION_COMPLETE = "execution_complete"  # Execution completed
    EXECUTION_FAILED = "execution_failed"  # Execution failed
    
    # State changes
    BLOCKED = "blocked"  # Blocked by constraints
    DEFERRED = "deferred"  # Postponed
    CANCELLED = "cancelled"  # Cancelled
    ROLLED_BACK = "rolled_back"  # Rolled back
    ESCALATED = "escalated"  # Escalated to human
    
    # Recovery and feedback
    RECOVERED = "recovered"  # Recovered from blocked state
    CALIBRATED = "calibrated"  # Post-execution calibration
    FEEDBACK_RECEIVED = "feedback_received"  # Feedback received
    TIMED_OUT = "timed_out"  # Timeout occurred


class TransitionConfidence(str, Enum):
    """Confidence level in a transition."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class TransitionReason(str, Enum):
    """Reason for a transition."""
    CONSTRAINT_VIOLATION = "constraint_violation"
    PROOF_GATE_FAILED = "proof_gate_failed"
    CAPABILITY_LIMITED = "capability_limited"
    EVIDENCE_INSUFFICIENT = "evidence_insufficient"
    RISK_TOO_HIGH = "risk_too_high"
    NO_ROLLBACK = "no_rollback"
    HUMAN_APPROVAL_NEEDED = "human_approval_needed"
    SCHEDULED_DELAY = "scheduled_delay"
    RECOVERY_APPLIED = "recovery_applied"
    FEEDBACK_INFORMED = "feedback_informed"
    CALIBRATION_UPDATE = "calibration_update"
    CANCELLATION_REQUESTED = "cancellation_requested"
    EXECUTION_ERROR = "execution_error"
    UNKNOWN = "unknown"


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class StateTransition:
    """Record of a state transition."""
    
    transition_id: str
    object_type: str  # e.g., "change_proposal", "recovery_recommendation", "proposal"
    object_id: str
    previous_state: str  # TransitionState.value
    new_state: str  # TransitionState.value
    trigger: str  # TransitionTrigger.value
    
    # Context
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    actor: Optional[str] = None  # Who triggered the transition
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Confidence and validation
    confidence: str = TransitionConfidence.MEDIUM.value
    validated: bool = True
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "trigger": self.trigger,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "context": self.context,
            "confidence": self.confidence,
            "validated": self.validated,
            "created_at": self.created_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StateTransition:
        data["context"] = data.get("context", {})
        return cls(**data)


@dataclass
class AllowedTransition:
    """Definition of an allowed transition between states."""
    
    allowed_id: str
    from_state: str  # TransitionState.value
    to_state: str  # TransitionState.value
    trigger: str  # TransitionTrigger.value
    
    # Requirements
    required_conditions: List[str] = field(default_factory=list)
    optional_conditions: List[str] = field(default_factory=list)
    
    # Constraints
    min_confidence: str = TransitionConfidence.LOW.value
    max_retries: int = 3
    requires_approval: bool = False
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed_id": self.allowed_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "trigger": self.trigger,
            "required_conditions": self.required_conditions,
            "optional_conditions": self.optional_conditions,
            "min_confidence": self.min_confidence,
            "max_retries": self.max_retries,
            "requires_approval": self.requires_approval,
            "created_at": self.created_at,
            "enabled": self.enabled,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AllowedTransition:
        data["required_conditions"] = data.get("required_conditions", [])
        data["optional_conditions"] = data.get("optional_conditions", [])
        return cls(**data)


@dataclass
class RollbackTransition:
    """Record of a rollback transition."""
    
    rollback_id: str
    transition_id: str  # ID of the transition being rolled back
    original_state: str  # State before the original transition
    rollback_to_state: str  # State to roll back to
    rollback_reason: str  # Why rollback was needed
    
    # Rollback details
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    actor: Optional[str] = None
    rollback_steps: List[str] = field(default_factory=list)
    
    # Status
    completed: bool = True
    failed_at: Optional[str] = None
    failure_reason: Optional[str] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rollback_id": self.rollback_id,
            "transition_id": self.transition_id,
            "original_state": self.original_state,
            "rollback_to_state": self.rollback_to_state,
            "rollback_reason": self.rollback_reason,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "rollback_steps": self.rollback_steps,
            "completed": self.completed,
            "failed_at": self.failed_at,
            "failure_reason": self.failure_reason,
            "created_at": self.created_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RollbackTransition:
        data["rollback_steps"] = data.get("rollback_steps", [])
        return cls(**data)


@dataclass
class TransitionExplanation:
    """Explanation for a state transition."""
    
    explanation_id: str
    transition_id: str
    object_type: str
    object_id: str
    
    # Explanation content
    explanation_type: str
    explanation_text: str
    
    # State context
    previous_state: str
    new_state: str
    trigger: str
    
    # Rationale
    why_transition: str
    why_not_other_transitions: List[str] = field(default_factory=list)
    
    # Confidence
    confidence: float = 0.5
    confidence_reasoning: str = ""
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "explanation_id": self.explanation_id,
            "transition_id": self.transition_id,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "explanation_type": self.explanation_type,
            "explanation_text": self.explanation_text,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "trigger": self.trigger,
            "why_transition": self.why_transition,
            "why_not_other_transitions": self.why_not_other_transitions,
            "confidence": self.confidence,
            "confidence_reasoning": self.confidence_reasoning,
            "created_at": self.created_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TransitionExplanation:
        data["why_not_other_transitions"] = data.get("why_not_other_transitions", [])
        return cls(**data)


# ============================================================================
# TRANSITION ENGINE
# ============================================================================


class StateTransitionEngine:
    """Engine for managing state transitions and their explanations."""
    
    # Pre-initialized allowed transitions (deterministic IDs)
    DEFAULT_ALLOWED_TRANSITIONS = {
        ("draft", "pending", "submitted"),
        ("pending", "approved", "approved"),
        ("pending", "denied", "denied"),
        ("blocked", "recovered", "recovered"),
        ("approved", "executed", "executed"),
        ("executed", "rolled_back", "rolled_back"),
        ("executed", "calibrated", "calibrated"),
    }
    
    def __init__(self, storage_path: Optional[str] = None, in_memory: bool = True):
        import tempfile
        
        # Use in-memory storage by default (no files)
        self.storage_path = None if in_memory else (storage_path or tempfile.mkdtemp(prefix="weslr_transitions_"))
        
        # Storage
        self.transitions: Dict[str, StateTransition] = {}
        self.allowed_transitions: Dict[str, AllowedTransition] = {}
        self.rollbacks: Dict[str, RollbackTransition] = {}
        self.explanations: Dict[str, TransitionExplanation] = {}
        
        # Initialize allowed transitions map
        self._initialize_allowed_transitions()
    
    def _load_from_storage(self) -> None:
        """Load from storage directory."""
        storage = Path(self.storage_path)
        if not storage.exists():
            storage.mkdir(parents=True, exist_ok=True)
            return
        
        # Load transitions
        for file in storage.glob("*_transition.json"):
            try:
                with open(file) as f:
                    data = json.load(f)
                    transition = StateTransition.from_dict(data)
                    self.transitions[transition.transition_id] = transition
            except Exception:
                pass
    
    def _save_to_storage(self, obj: Any, prefix: str) -> None:
        """Save object to storage (in-memory only)."""
        # In-memory only - nothing to save
        pass
    
    def _initialize_allowed_transitions(self) -> None:
        """Initialize default allowed transitions."""
        # Proposal flow
        self.allowed_transitions["draft_to_pending"] = AllowedTransition(
            allowed_id="draft_to_pending",
            from_state=TransitionState.DRAFT.value,
            to_state=TransitionState.PENDING.value,
            trigger=TransitionTrigger.SUBMITTED.value,
            requires_approval=False,
        )
        
        self.allowed_transitions["pending_to_approved"] = AllowedTransition(
            allowed_id="pending_to_approved",
            from_state=TransitionState.PENDING.value,
            to_state=TransitionState.APPROVED.value,
            trigger=TransitionTrigger.APPROVED.value,
            requires_approval=True,
        )
        
        self.allowed_transitions["pending_to_denied"] = AllowedTransition(
            allowed_id="pending_to_denied",
            from_state=TransitionState.PENDING.value,
            to_state=TransitionState.DENIED.value,
            trigger=TransitionTrigger.DENIED.value,
            requires_approval=True,
        )
        
        # Blocked recovery
        self.allowed_transitions["blocked_to_recovered"] = AllowedTransition(
            allowed_id="blocked_to_recovered",
            from_state=TransitionState.BLOCKED.value,
            to_state=TransitionState.RECOVERED.value,
            trigger=TransitionTrigger.RECOVERED.value,
            requires_approval=False,
        )
        
        # Execution flow
        self.allowed_transitions["approved_to_executed"] = AllowedTransition(
            allowed_id="approved_to_executed",
            from_state=TransitionState.APPROVED.value,
            to_state=TransitionState.EXECUTED.value,
            trigger=TransitionTrigger.EXECUTED.value,
            requires_approval=False,
        )
        
        # Rollback flow
        self.allowed_transitions["executed_to_rolled_back"] = AllowedTransition(
            allowed_id="executed_to_rolled_back",
            from_state=TransitionState.EXECUTED.value,
            to_state=TransitionState.ROLLED_BACK.value,
            trigger=TransitionTrigger.ROLLED_BACK.value,
            requires_approval=True,
        )
        
        # Calibration flow
        self.allowed_transitions["executed_to_calibrated"] = AllowedTransition(
            allowed_id="executed_to_calibrated",
            from_state=TransitionState.EXECUTED.value,
            to_state=TransitionState.CALIBRATED.value,
            trigger=TransitionTrigger.CALIBRATED.value,
            requires_approval=False,
        )
    
    # ============================================================================
    # TRANSITION MANAGEMENT
    # ============================================================================
    
    def record_transition(self, transition: StateTransition) -> None:
        """Record a state transition."""
        self.transitions[transition.transition_id] = transition
        self._save_to_storage(transition, "transition")
    
    def get_transition(self, transition_id: str) -> Optional[StateTransition]:
        """Get a transition by ID."""
        return self.transitions.get(transition_id)
    
    def get_all_transitions(self, object_type: Optional[str] = None, object_id: Optional[str] = None) -> List[StateTransition]:
        """Get all transitions, optionally filtered."""
        result = list(self.transitions.values())
        if object_type:
            result = [t for t in result if t.object_type == object_type]
        if object_id:
            result = [t for t in result if t.object_id == object_id]
        return result
    
    # ============================================================================
    # ALLOWED TRANSITION MANAGEMENT
    # ============================================================================
    
    def add_allowed_transition(self, allowed: AllowedTransition) -> None:
        """Add an allowed transition definition."""
        self.allowed_transitions[allowed.allowed_id] = allowed
        self._save_to_storage(allowed, "allowed")
    
    def remove_allowed_transition(self, allowed_id: str) -> bool:
        """Remove an allowed transition."""
        if allowed_id in self.allowed_transitions:
            del self.allowed_transitions[allowed_id]
            return True
        return False
    
    def get_allowed_transition(self, from_state: str, to_state: str) -> Optional[AllowedTransition]:
        """Get an allowed transition by from/to states."""
        for allowed in self.allowed_transitions.values():
            if allowed.from_state == from_state and allowed.to_state == to_state:
                return allowed
        return None
    
    def is_transition_allowed(self, from_state: str, to_state: str, trigger: str) -> bool:
        """Check if a transition is allowed."""
        for allowed in self.allowed_transitions.values():
            if (allowed.from_state == from_state and 
                allowed.to_state == to_state and 
                allowed.trigger == trigger):
                return allowed.enabled
        return False
    
    # ============================================================================
    # ROLLBACK MANAGEMENT
    # ============================================================================
    
    def record_rollback(self, rollback: RollbackTransition) -> None:
        """Record a rollback transition."""
        self.rollbacks[rollback.rollback_id] = rollback
        self._save_to_storage(rollback, "rollback")
    
    def get_rollback(self, rollback_id: str) -> Optional[RollbackTransition]:
        """Get a rollback by ID."""
        return self.rollbacks.get(rollback_id)
    
    def get_all_rollbacks(self) -> List[RollbackTransition]:
        """Get all rollbacks."""
        return list(self.rollbacks.values())
    
    # ============================================================================
    # EXPLANATION MANAGEMENT
    # ============================================================================
    
    def create_explanation(self, explanation: TransitionExplanation) -> None:
        """Create a transition explanation."""
        self.explanations[explanation.explanation_id] = explanation
        self._save_to_storage(explanation, "explanation")
    
    def get_explanation(self, explanation_id: str) -> Optional[TransitionExplanation]:
        """Get an explanation by ID."""
        return self.explanations.get(explanation_id)
    
    def get_all_explanations(self) -> List[TransitionExplanation]:
        """Get all explanations."""
        return list(self.explanations.values())
    
    # ============================================================================
    # TRANSITION GENERATION
    # ============================================================================
    
    def generate_transition(
        self,
        object_type: str,
        object_id: str,
        from_state: str,
        to_state: str,
        trigger: str,
        actor: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        confidence: str = TransitionConfidence.MEDIUM.value,
    ) -> Optional[StateTransition]:
        """Generate a state transition if allowed."""
        import uuid
        
        if not self.is_transition_allowed(from_state, to_state, trigger):
            return None
        
        transition = StateTransition(
            transition_id=f"transition_{uuid.uuid4().hex}",
            object_type=object_type,
            object_id=object_id,
            previous_state=from_state,
            new_state=to_state,
            trigger=trigger,
            actor=actor,
            context=context or {},
            confidence=confidence,
        )
        
        self.record_transition(transition)
        
        # Create explanation
        explanation = TransitionExplanation(
            explanation_id=f"exp_{transition.transition_id}",
            transition_id=transition.transition_id,
            object_type=object_type,
            object_id=object_id,
            explanation_type="state_transition",
            explanation_text=f"Transitioned from {from_state} to {to_state} because {trigger}.",
            previous_state=from_state,
            new_state=to_state,
            trigger=trigger,
            why_transition=f"Trigger {trigger} caused transition from {from_state} to {to_state}.",
            why_not_other_transitions=[f"{t} not applicable" for t in ["rejected", "cancelled"]],
            confidence=0.7,
            confidence_reasoning=f"Transition follows defined allowed transitions for {trigger}.",
        )
        self.create_explanation(explanation)
        
        return transition
    
    def generate_rollback(
        self,
        transition_id: str,
        original_state: str,
        rollback_to_state: str,
        rollback_reason: str,
        actor: Optional[str] = None,
    ) -> Optional[RollbackTransition]:
        """Generate a rollback transition."""
        import uuid
        
        transition = self.transitions.get(transition_id)
        if not transition:
            return None
        
        rollback = RollbackTransition(
            rollback_id=f"rollback_{uuid.uuid4().hex}",
            transition_id=transition_id,
            original_state=original_state,
            rollback_to_state=rollback_to_state,
            rollback_reason=rollback_reason,
            actor=actor,
            rollback_steps=[
                "Revert object to original state",
                "Record rollback reason and actor",
                "Update audit trail",
            ],
        )
        
        self.record_rollback(rollback)
        
        return rollback
    
    # ============================================================================
    # INTEGRATION HOOKS
    # ============================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary."""
        return {
            "transition_count": len(self.transitions),
            "allowed_transition_count": len(self.allowed_transitions),
            "rollback_count": len(self.rollbacks),
            "explanation_count": len(self.explanations),
            "transitions": {k: v.to_dict() for k, v in self.transitions.items()},
            "allowed_transitions": {k: v.to_dict() for k, v in self.allowed_transitions.items()},
            "rollbacks": {k: v.to_dict() for k, v in self.rollbacks.items()},
            "explanations": {k: v.to_dict() for k, v in self.explanations.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_change_proposals(
    proposal_dict: Dict[str, Any],
    transition_engine: StateTransitionEngine = None,
    proposal_id: str = None,
    from_state: str = None,
    to_state: str = None,
    trigger: str = None,
) -> Dict[str, Any]:
    """Add transition context to change proposal.
    
    This is purely additive — no migration required.
    
    v47: State transition layer provides explicit state evolution tracking for proposals.
    """
    if "transition_context" not in proposal_dict:
        proposal_dict["transition_context"] = None
    
    if transition_engine and proposal_id and from_state and to_state and trigger:
        try:
            transition = transition_engine.generate_transition(
                object_type="change_proposal",
                object_id=proposal_id,
                from_state=from_state,
                to_state=to_state,
                trigger=trigger,
            )
            
            if transition:
                proposal_dict["transition_context"] = {
                    "transition_generated": True,
                    "transition_id": transition.transition_id,
                    "previous_state": transition.previous_state,
                    "new_state": transition.new_state,
                    "trigger": transition.trigger,
                }
            else:
                proposal_dict["transition_context"] = {
                    "transition_generated": False,
                    "reason": "transition_not_allowed",
                }
        except Exception:
            pass  # Silent fallback to default
    
    return proposal_dict


def integrate_with_proof_gate(
    proof_dict: Dict[str, Any],
    transition_engine: StateTransitionEngine = None,
    proof_id: str = None,
    from_state: str = None,
    to_state: str = None,
    trigger: str = None,
) -> Dict[str, Any]:
    """Add transition context to proof gate.
    
    This is purely additive — no migration required.
    
    v47: State transition layer provides state evolution for proof items.
    """
    if "transition_context" not in proof_dict:
        proof_dict["transition_context"] = None
    
    if transition_engine and proof_id and from_state and to_state and trigger:
        try:
            transition = transition_engine.generate_transition(
                object_type="proof_item",
                object_id=proof_id,
                from_state=from_state,
                to_state=to_state,
                trigger=trigger,
            )
            
            if transition:
                proof_dict["transition_context"] = {
                    "transition_generated": True,
                    "transition_id": transition.transition_id,
                    "previous_state": transition.previous_state,
                    "new_state": transition.new_state,
                    "trigger": transition.trigger,
                }
            else:
                proof_dict["transition_context"] = {
                    "transition_generated": False,
                    "reason": "transition_not_allowed",
                }
        except Exception:
            pass  # Silent fallback to default
    
    return proof_dict


def integrate_with_escalation(
    escalation_dict: Dict[str, Any],
    transition_engine: StateTransitionEngine = None,
    escalation_id: str = None,
    from_state: str = None,
    to_state: str = None,
    trigger: str = None,
) -> Dict[str, Any]:
    """Add transition context to escalation.
    
    This is purely additive — no migration required.
    
    v47: State transition layer provides state evolution for escalation handoffs.
    """
    if "transition_context" not in escalation_dict:
        escalation_dict["transition_context"] = None
    
    if transition_engine and escalation_id and from_state and to_state and trigger:
        try:
            transition = transition_engine.generate_transition(
                object_type="handoff",
                object_id=escalation_id,
                from_state=from_state,
                to_state=to_state,
                trigger=trigger,
            )
            
            if transition:
                escalation_dict["transition_context"] = {
                    "transition_generated": True,
                    "transition_id": transition.transition_id,
                    "previous_state": transition.previous_state,
                    "new_state": transition.new_state,
                    "trigger": transition.trigger,
                }
            else:
                escalation_dict["transition_context"] = {
                    "transition_generated": False,
                    "reason": "transition_not_allowed",
                }
        except Exception:
            pass  # Silent fallback to default
    
    return escalation_dict


def integrate_with_outcome_feedback(
    feedback_dict: Dict[str, Any],
    transition_engine: StateTransitionEngine = None,
    feedback_id: str = None,
    from_state: str = None,
    to_state: str = None,
    trigger: str = None,
) -> Dict[str, Any]:
    """Add transition context to outcome feedback.
    
    This is purely additive — no migration required.
    
    v47: State transition layer provides state evolution for feedback processing.
    """
    if "transition_context" not in feedback_dict:
        feedback_dict["transition_context"] = None
    
    if transition_engine and feedback_id and from_state and to_state and trigger:
        try:
            transition = transition_engine.generate_transition(
                object_type="recommendation_feedback",
                object_id=feedback_id,
                from_state=from_state,
                to_state=to_state,
                trigger=trigger,
            )
            
            if transition:
                feedback_dict["transition_context"] = {
                    "transition_generated": True,
                    "transition_id": transition.transition_id,
                    "previous_state": transition.previous_state,
                    "new_state": transition.new_state,
                    "trigger": transition.trigger,
                }
            else:
                feedback_dict["transition_context"] = {
                    "transition_generated": False,
                    "reason": "transition_not_allowed",
                }
        except Exception:
            pass  # Silent fallback to default
    
    return feedback_dict


def integrate_with_recovery_layer(
    recovery_dict: Dict[str, Any],
    transition_engine: StateTransitionEngine = None,
    recovery_id: str = None,
    from_state: str = None,
    to_state: str = None,
    trigger: str = None,
) -> Dict[str, Any]:
    """Add transition context to alternative recovery layer.
    
    This is purely additive — no migration required.
    
    v47: State transition layer provides state evolution for recovery recommendations.
    """
    if "transition_context" not in recovery_dict:
        recovery_dict["transition_context"] = None
    
    if transition_engine and recovery_id and from_state and to_state and trigger:
        try:
            transition = transition_engine.generate_transition(
                object_type="recovery_recommendation",
                object_id=recovery_id,
                from_state=from_state,
                to_state=to_state,
                trigger=trigger,
            )
            
            if transition:
                recovery_dict["transition_context"] = {
                    "transition_generated": True,
                    "transition_id": transition.transition_id,
                    "previous_state": transition.previous_state,
                    "new_state": transition.new_state,
                    "trigger": transition.trigger,
                }
            else:
                recovery_dict["transition_context"] = {
                    "transition_generated": False,
                    "reason": "transition_not_allowed",
                }
        except Exception:
            pass  # Silent fallback to default
    
    return recovery_dict
