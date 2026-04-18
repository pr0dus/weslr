# alternative_path_recovery.py - WESLR v46: Alternative Path / Recovery Recommendation Layer
# Creates a governed recovery layer so WESLR can propose safer alternatives when a path
# is blocked by invariants, proof gates, capability boundaries, timing, or trust constraints.
# Additive only, transparent, reversible, role-aware, non-manipulative.
# No repo drift (local to WESLR scope).

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import ViolationSeverity from constraint_invariant
try:
    from .constraint_invariant import ViolationSeverity
except ImportError:
    # Fallback enum if constraint_invariant not available
    class ViolationSeverity(str, Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"


# ============================================================================
# ENUMS
# ============================================================================


class BlockedPathType(str, Enum):
    """Types of blocked paths."""
    BLOCKED_BY_CONSTRAINT = "blocked_by_constraint"
    BLOCKED_BY_INVARIANT = "blocked_by_invariant"
    BLOCKED_BY_PROOF_GATE = "blocked_by_proof_gate"
    BLOCKED_BY_EVIDENCE = "blocked_by_evidence"
    BLOCKED_BY_CAPABILITY = "blocked_by_capability"
    BLOCKED_BY_AUTHORITY = "blocked_by_authority"
    BLOCKED_BY_TIMING = "blocked_by_timing"
    BLOCKED_BY_RATE_LIMIT = "blocked_by_rate_limit"
    BLOCKED_BY_TRUST = "blocked_by_trust"
    BLOCKED_BY_RELATIONSHIP = "blocked_by_relationship"
    OTHER = "other"


class BlockingReason(str, Enum):
    """Reasons for blocking."""
    ETHICAL_VIOLATION = "ethical_violation"
    LEGAL_VIOLATION = "legal_violation"
    SECURITY_VIOLATION = "security_violation"
    PRIVACY_VIOLATION = "privacy_violation"
    TRUST_VIOLATION = "trust_violation"
    OPERATIONAL_VIOLATION = "operational_violation"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    FAILED_RISK_ASSESSMENT = "failed_risk_assessment"
    NO_ROLLBACK = "no_rollback"
    LOW_CONFIDENCE = "low_confidence"
    CAPABILITY_PROHIBITED = "capability_prohibited"
    CAPABILITY_RESTRICTED = "capability_restricted"
    NO_AUTHORITY = "no_authority"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    NOT_ALLOWED_AT_TIME = "not_allowed_at_time"
    TRUST_TOO_LOW = "trust_too_low"
    RELATIONSHIP_LIMITED = "relationship_limited"
    UNKNOWN = "unknown"


class SaferAlternativeType(str, Enum):
    """Types of safer alternatives."""
    SAFER_ALTERNATIVE = "safer_alternative"
    LOWER_SCOPE = "lower_scope"
    DELAYED = "delayed"
    EVIDENCE_GATHERING = "evidence_gathering"
    ESCALATION = "escalation"
    SAFER_DELAYED = "safer_delayed"
    ESCALATION_RECOMMENDATION = "escalation_recommendation"


class RecoveryConfidence(str, Enum):
    """Confidence level in recovery recommendation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RecoveryStatus(str, Enum):
    """Status of recovery recommendation."""
    GENERATED = "generated"
    REVIEWED = "reviewed"
    USED = "used"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class BlockedPath:
    """Record of a blocked path."""
    
    blocked_path_id: str
    original_action: str
    blocked_path_type: str  # BlockedPathType.value
    blocking_reason: str  # BlockingReason.value
    
    # Optional fields with defaults
    original_context: Dict[str, Any] = field(default_factory=dict)
    blocking_rule_id: Optional[str] = None
    blocked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    blocking_details: Dict[str, Any] = field(default_factory=dict)
    severity: str = ViolationSeverity.MEDIUM.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "blocked_path_id": self.blocked_path_id,
            "original_action": self.original_action,
            "original_context": self.original_context,
            "blocked_path_type": self.blocked_path_type,
            "blocking_reason": self.blocking_reason,
            "blocking_rule_id": self.blocking_rule_id,
            "blocked_at": self.blocked_at,
            "blocking_details": self.blocking_details,
            "severity": self.severity,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BlockedPath:
        data["original_context"] = data.get("original_context", {})
        data["blocking_details"] = data.get("blocking_details", {})
        return cls(**data)


@dataclass
class SaferAlternative:
    """Safer alternative recommendation."""
    
    alternative_id: str
    blocked_path_id: str
    alternative_type: str  # SaferAlternativeType.value
    alternative_description: str
    
    # Expected outcome
    expected_outcome: Dict[str, Any] = field(default_factory=dict)
    confidence: str = RecoveryConfidence.MEDIUM.value
    
    # Requirements
    required_conditions: List[str] = field(default_factory=list)
    additional_evidence_needed: List[str] = field(default_factory=list)
    
    # Comparison with original
    tradeoffs: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alternative_id": self.alternative_id,
            "blocked_path_id": self.blocked_path_id,
            "alternative_type": self.alternative_type,
            "alternative_description": self.alternative_description,
            "expected_outcome": self.expected_outcome,
            "confidence": self.confidence,
            "required_conditions": self.required_conditions,
            "additional_evidence_needed": self.additional_evidence_needed,
            "tradeoffs": self.tradeoffs,
            "benefits": self.benefits,
            "created_at": self.created_at,
            "author": self.author,
            "enabled": self.enabled,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SaferAlternative:
        data["expected_outcome"] = data.get("expected_outcome", {})
        data["required_conditions"] = data.get("required_conditions", [])
        data["additional_evidence_needed"] = data.get("additional_evidence_needed", [])
        data["tradeoffs"] = data.get("tradeoffs", [])
        data["benefits"] = data.get("benefits", [])
        return cls(**data)


@dataclass
class RecoveryRecommendation:
    """Complete recovery recommendation for a blocked path."""
    
    recovery_id: str
    blocked_path_id: str
    
    # Alternatives
    safer_alternatives: List[str] = field(default_factory=list)
    preferred_alternative_id: Optional[str] = None
    
    # Recovery confidence
    overall_confidence: str = RecoveryConfidence.MEDIUM.value
    risk_reduction: float = 0.0
    
    # Implementation guidance
    implementation_steps: List[str] = field(default_factory=list)
    required_human_review: bool = False
    emergency_override_available: bool = False
    
    # Status
    status: str = RecoveryStatus.GENERATED.value
    reviewed_at: Optional[str] = None
    implemented_at: Optional[str] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "recovery_id": self.recovery_id,
            "blocked_path_id": self.blocked_path_id,
            "safer_alternatives": self.safer_alternatives,
            "preferred_alternative_id": self.preferred_alternative_id,
            "overall_confidence": self.overall_confidence,
            "risk_reduction": self.risk_reduction,
            "implementation_steps": self.implementation_steps,
            "required_human_review": self.required_human_review,
            "emergency_override_available": self.emergency_override_available,
            "status": self.status,
            "reviewed_at": self.reviewed_at,
            "implemented_at": self.implemented_at,
            "created_at": self.created_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RecoveryRecommendation:
        data["safer_alternatives"] = data.get("safer_alternatives", [])
        data["implementation_steps"] = data.get("implementation_steps", [])
        return cls(**data)


@dataclass
class ExplanationForRecovery:
    """Explanation for recovery recommendation."""
    
    explanation_id: str
    recovery_id: str
    
    # Explanation content
    explanation_type: str
    explanation_text: str
    
    # Blocked path context
    original_action: str
    blocking_reason: str
    blocked_at: str
    
    # Alternative details
    recommended_alternative: Optional[str] = None
    why_this_alternative: str = ""
    why_other_alternatives_not_chosen: List[str] = field(default_factory=list)
    
    # Trust and confidence
    confidence: float = 0.5
    risk_reduction_explanation: str = ""
    
    # Status
    status: str = RecoveryStatus.GENERATED.value
    reviewed_at: Optional[str] = None
    used_at: Optional[str] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "explanation_id": self.explanation_id,
            "recovery_id": self.recovery_id,
            "explanation_type": self.explanation_type,
            "explanation_text": self.explanation_text,
            "original_action": self.original_action,
            "blocking_reason": self.blocking_reason,
            "blocked_at": self.blocked_at,
            "recommended_alternative": self.recommended_alternative,
            "why_this_alternative": self.why_this_alternative,
            "why_other_alternatives_not_chosen": self.why_other_alternatives_not_chosen,
            "confidence": self.confidence,
            "risk_reduction_explanation": self.risk_reduction_explanation,
            "status": self.status,
            "reviewed_at": self.reviewed_at,
            "used_at": self.used_at,
            "created_at": self.created_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExplanationForRecovery:
        data["why_other_alternatives_not_chosen"] = data.get("why_other_alternatives_not_chosen", [])
        return cls(**data)


# ============================================================================
# RECOVERY ENGINE
# ============================================================================


class AlternativePathRecoveryEngine:
    """Engine for managing blocked paths and recovery recommendations."""
    
    def __init__(self, storage_path: Optional[str] = None):
        import tempfile
        
        self.storage_path = storage_path or tempfile.mkdtemp(prefix="weslr_recovery_")
        
        # Storage
        self.blocked_paths: Dict[str, BlockedPath] = {}
        self.alternatives: Dict[str, SaferAlternative] = {}
        self.recoveries: Dict[str, RecoveryRecommendation] = {}
        self.explanations: Dict[str, ExplanationForRecovery] = {}
        
        # Load existing if present
        if Path(self.storage_path).exists():
            self._load_from_storage()
    
    def _load_from_storage(self) -> None:
        """Load from storage directory."""
        storage = Path(self.storage_path)
        if not storage.exists():
            storage.mkdir(parents=True, exist_ok=True)
            return
        
        # Load blocked paths
        for file in storage.glob("*_blocked_path.json"):
            try:
                with open(file) as f:
                    data = json.load(f)
                    blocked_path = BlockedPath.from_dict(data)
                    self.blocked_paths[blocked_path.blocked_path_id] = blocked_path
            except Exception:
                pass
        
        # Load alternatives
        for file in storage.glob("*_alternative.json"):
            try:
                with open(file) as f:
                    data = json.load(f)
                    alternative = SaferAlternative.from_dict(data)
                    self.alternatives[alternative.alternative_id] = alternative
            except Exception:
                pass
        
        # Load recoveries
        for file in storage.glob("*_recovery.json"):
            try:
                with open(file) as f:
                    data = json.load(f)
                    recovery = RecoveryRecommendation.from_dict(data)
                    self.recoveries[recovery.recovery_id] = recovery
            except Exception:
                pass
    
    def _save_to_storage(self, obj: Any, prefix: str) -> None:
        """Save object to storage."""
        import os
        
        if not self.storage_path:
            return
        
        obj_id = (
            obj.blocked_path_id if hasattr(obj, 'blocked_path_id')
            else obj.alternative_id if hasattr(obj, 'alternative_id')
            else obj.recovery_id if hasattr(obj, 'recovery_id')
            else obj.explanation_id
        )
        
        # Create storage directory if needed
        storage_path = Path(self.storage_path)
        storage_path.mkdir(parents=True, exist_ok=True)
        
        filepath = os.path.join(self.storage_path, f"{obj_id}_{prefix}.json")
        with open(filepath, "w") as f:
            json.dump(obj.to_dict(), f, indent=2)
    
    # ============================================================================
    # BLOCKED PATH MANAGEMENT
    # ============================================================================
    
    def record_blocked_path(self, blocked_path: BlockedPath) -> None:
        """Record a blocked path."""
        self.blocked_paths[blocked_path.blocked_path_id] = blocked_path
        self._save_to_storage(blocked_path, "blocked_path")
    
    def get_blocked_path(self, blocked_path_id: str) -> Optional[BlockedPath]:
        """Get a blocked path by ID."""
        return self.blocked_paths.get(blocked_path_id)
    
    def get_all_blocked_paths(self) -> List[BlockedPath]:
        """Get all blocked paths."""
        return list(self.blocked_paths.values())
    
    # ============================================================================
    # ALTERNATIVE MANAGEMENT
    # ============================================================================
    
    def add_alternative(self, alternative: SaferAlternative) -> None:
        """Add a safer alternative."""
        self.alternatives[alternative.alternative_id] = alternative
        self._save_to_storage(alternative, "alternative")
    
    def remove_alternative(self, alternative_id: str) -> bool:
        """Remove an alternative."""
        if alternative_id in self.alternatives:
            del self.alternatives[alternative_id]
            return True
        return False
    
    def get_alternative(self, alternative_id: str) -> Optional[SaferAlternative]:
        """Get an alternative by ID."""
        return self.alternatives.get(alternative_id)
    
    def get_all_alternatives(self) -> List[SaferAlternative]:
        """Get all enabled alternatives."""
        return [a for a in self.alternatives.values() if a.enabled]
    
    # ============================================================================
    # RECOVERY MANAGEMENT
    # ============================================================================
    
    def create_recovery(self, recovery: RecoveryRecommendation) -> None:
        """Create a recovery recommendation."""
        self.recoveries[recovery.recovery_id] = recovery
        self._save_to_storage(recovery, "recovery")
    
    def get_recovery(self, recovery_id: str) -> Optional[RecoveryRecommendation]:
        """Get a recovery by ID."""
        return self.recoveries.get(recovery_id)
    
    def get_all_recoveries(self) -> List[RecoveryRecommendation]:
        """Get all recoveries."""
        return list(self.recoveries.values())
    
    # ============================================================================
    # EXPLANATION MANAGEMENT
    # ============================================================================
    
    def create_explanation(self, explanation: ExplanationForRecovery) -> None:
        """Create a recovery explanation."""
        self.explanations[explanation.explanation_id] = explanation
        self._save_to_storage(explanation, "explanation")
    
    def get_explanation(self, explanation_id: str) -> Optional[ExplanationForRecovery]:
        """Get an explanation by ID."""
        return self.explanations.get(explanation_id)
    
    def get_all_explanations(self) -> List[ExplanationForRecovery]:
        """Get all explanations."""
        return list(self.explanations.values())
    
    # ============================================================================
    # RECOVERY GENERATION
    # ============================================================================
    
    def generate_recovery_recommendation(
        self,
        blocked_path: BlockedPath,
    ) -> Optional[RecoveryRecommendation]:
        """Generate a recovery recommendation for a blocked path."""
        import time
        
        recovery_id = f"recovery_{int(time.time() * 1000)}"
        
        # Generate safer alternatives based on blocking reason
        safer_alternatives = []
        
        if blocked_path.blocking_reason in [
            BlockingReason.INSUFFICIENT_EVIDENCE.value,
            BlockingReason.LOW_CONFIDENCE.value,
        ]:
            # Evidence-gathering alternative
            alternative = SaferAlternative(
                alternative_id=f"evidence_gathering_{int(time.time() * 1000)}",
                blocked_path_id=blocked_path.blocked_path_id,
                alternative_type=SaferAlternativeType.EVIDENCE_GATHERING.value,
                alternative_description="Gather additional evidence before attempting action.",
                expected_outcome={"confidence": "high", "risk": "low"},
                confidence=RecoveryConfidence.MEDIUM.value,
                required_conditions=["additional_data_collected"],
                tradeoffs=["delayed_action"],
                benefits=["higher_confidence", "reduced_risk"],
            )
            self.add_alternative(alternative)
            safer_alternatives.append(alternative.alternative_id)
        
        elif blocked_path.blocking_reason in [
            BlockingReason.CAPABILITY_PROHIBITED.value,
            BlockingReason.CAPABILITY_RESTRICTED.value,
            BlockingReason.NO_AUTHORITY.value,
        ]:
            # Escalation alternative
            alternative = SaferAlternative(
                alternative_id=f"escalation_{int(time.time() * 1000)}",
                blocked_path_id=blocked_path.blocked_path_id,
                alternative_type=SaferAlternativeType.ESCALATION.value,
                alternative_description="Escalate to human operator for review and approval.",
                expected_outcome={"human_review": "scheduled", "approved": False},
                confidence=RecoveryConfidence.MEDIUM.value,
                required_conditions=["human_available"],
                additional_evidence_needed=["operator_decision_rationale"],
                tradeoffs=["delayed_by_human_response_time"],
                benefits=["human_judgment", "compliance"],
            )
            self.add_alternative(alternative)
            safer_alternatives.append(alternative.alternative_id)
        
        elif blocked_path.blocking_reason in [
            BlockingReason.TRUST_VIOLATION.value,
            BlockingReason.TRUST_TOO_LOW.value,
            BlockingReason.RELATIONSHIP_LIMITED.value,
        ]:
            # Delayed alternative
            alternative = SaferAlternative(
                alternative_id=f"delayed_{int(time.time() * 1000)}",
                blocked_path_id=blocked_path.blocked_path_id,
                alternative_type=SaferAlternativeType.DELAYED.value,
                alternative_description="Delay action until trust is restored or conditions improve.",
                expected_outcome={"trust": "recovered", "timing": "future"},
                confidence=RecoveryConfidence.HIGH.value,
                required_conditions=["trust_recovered", "timing_favorable"],
                tradeoffs=["delayed_action", "opportunity_cost"],
                benefits=["restored_trust", "longer_term_success"],
            )
            self.add_alternative(alternative)
            safer_alternatives.append(alternative.alternative_id)
        
        else:
            # Lower scope alternative
            alternative = SaferAlternative(
                alternative_id=f"lower_scope_{int(time.time() * 1000)}",
                blocked_path_id=blocked_path.blocked_path_id,
                alternative_type=SaferAlternativeType.LOWER_SCOPE.value,
                alternative_description="Reduce scope to meet constraints while partially achieving goals.",
                expected_outcome={"partial_goals": True, "constraints_satisfied": True},
                confidence=RecoveryConfidence.HIGH.value,
                required_conditions=["scope_reduction_agreed"],
                tradeoffs=["reduced_outcome"],
                benefits=["constraint_satisfied", "action_undertaken"],
            )
            self.add_alternative(alternative)
            safer_alternatives.append(alternative.alternative_id)
        
        # Create recovery recommendation
        recovery = RecoveryRecommendation(
            recovery_id=recovery_id,
            blocked_path_id=blocked_path.blocked_path_id,
            safer_alternatives=safer_alternatives,
            preferred_alternative_id=safer_alternatives[0] if safer_alternatives else None,
            overall_confidence=RecoveryConfidence.MEDIUM.value,
            risk_reduction=0.5,
            implementation_steps=self._generate_implementation_steps(blocked_path, safer_alternatives),
            required_human_review=blocked_path.blocking_reason in [
                BlockingReason.CAPABILITY_PROHIBITED.value,
                BlockingReason.CAPABILITY_RESTRICTED.value,
            ],
            emergency_override_available=blocked_path.severity == ViolationSeverity.LOW.value,
        )
        
        self.create_recovery(recovery)
        
        # Create explanation
        explanation = ExplanationForRecovery(
            explanation_id=f"exp_{recovery_id}",
            recovery_id=recovery_id,
            explanation_type="recovery_recommendation",
            explanation_text=self._generate_recovery_explanation(recovery, blocked_path),
            original_action=blocked_path.original_action,
            blocking_reason=blocked_path.blocking_reason,
            blocked_at=blocked_path.blocked_at,
            recommended_alternative=recovery.preferred_alternative_id,
            why_this_alternative=f"Alternative {recovery.preferred_alternative_id} provides the best balance of safety and goal achievement.",
            why_other_alternatives_not_chosen=[f"Alternative {a} is less optimal" for a in safer_alternatives[1:]] if len(safer_alternatives) > 1 else [],
            confidence=0.7,
            risk_reduction_explanation=f"Recovery reduces risk by {recovery.risk_reduction} compared to original action.",
        )
        self.create_explanation(explanation)
        
        return recovery
    
    def _generate_implementation_steps(
        self,
        blocked_path: BlockedPath,
        safer_alternatives: List[str],
    ) -> List[str]:
        """Generate implementation steps for recovery."""
        steps = []
        
        if safer_alternatives:
            preferred = safer_alternatives[0]
            if "evidence" in preferred:
                steps.append("Identify required additional evidence")
                steps.append("Collect evidence from available sources")
                steps.append("Verify evidence quality and completeness")
                steps.append("Re-attempt original action with new evidence")
            elif "escalation" in preferred:
                steps.append("Prepare handoff package with full context")
                steps.append("Submit to appropriate human reviewer")
                steps.append("Wait for human decision and instructions")
            elif "delayed" in preferred:
                steps.append("Schedule future review date")
                steps.append("Monitor conditions for improvement")
                steps.append("Re-attempt when conditions favorable")
            else:
                steps.append("Define reduced scope that satisfies constraints")
                steps.append("Execute reduced scope version")
                steps.append("Monitor for constraints violation")
        
        steps.append("Document recovery decision and rationale")
        steps.append("Update operator with recovery status")
        
        return steps
    
    def _generate_recovery_explanation(
        self,
        recovery: RecoveryRecommendation,
        blocked_path: BlockedPath,
    ) -> str:
        """Generate human-readable explanation for recovery."""
        return (
            f"Action '{blocked_path.original_action}' was blocked due to {blocked_path.blocking_reason}. "
            f"Recommended recovery: {recovery.preferred_alternative_id or 'Escalation to human'}. "
            f"Expected risk reduction: {recovery.risk_reduction}. "
            f"Confidence in recovery: {recovery.overall_confidence}."
        )
    
    # ============================================================================
    # INTEGRATION HOOKS
    # ============================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary."""
        return {
            "blocked_path_count": len(self.blocked_paths),
            "alternative_count": len(self.alternatives),
            "recovery_count": len(self.recoveries),
            "explanation_count": len(self.explanations),
            "blocked_paths": {k: v.to_dict() for k, v in self.blocked_paths.items()},
            "alternatives": {k: v.to_dict() for k, v in self.alternatives.items()},
            "recoveries": {k: v.to_dict() for k, v in self.recoveries.items()},
            "explanations": {k: v.to_dict() for k, v in self.explanations.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_constraint_invariant_layer(
    constraint_dict: Dict[str, Any],
    recovery_engine: AlternativePathRecoveryEngine = None,
    blocked_action: str = None,
    blocking_rule_id: str = None,
) -> Dict[str, Any]:
    """Add recovery context to constraint/invariant layer.
    
    This is purely additive — no migration required.
    
    v46: Recovery layer provides alternatives when constraints are violated.
    """
    if "recovery_context" not in constraint_dict:
        constraint_dict["recovery_context"] = None
    
    if recovery_engine and blocked_action:
        blocked_path = BlockedPath(
            blocked_path_id=f"blocked_{blocked_action[:20]}_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            original_action=blocked_action,
            original_context={"rule_id": blocking_rule_id},
            blocked_path_type=BlockedPathType.BLOCKED_BY_CONSTRAINT.value,
            blocking_reason=BlockingReason.INSUFFICIENT_EVIDENCE.value,
            blocking_rule_id=blocking_rule_id,
            severity=ViolationSeverity.HIGH.value,
        )
        recovery_engine.record_blocked_path(blocked_path)
        
        recovery = recovery_engine.generate_recovery_recommendation(blocked_path)
        
        constraint_dict["recovery_context"] = {
            "path_blocked": True,
            "recovery_generated": recovery is not None,
            "preferred_alternative_id": recovery.preferred_alternative_id if recovery else None,
            "recovery_id": recovery.recovery_id if recovery else None,
        }
    
    return constraint_dict


def integrate_with_proof_gate(
    proof_dict: Dict[str, Any],
    recovery_engine: AlternativePathRecoveryEngine = None,
    blocked_action: str = None,
    blocking_reason: str = None,
) -> Dict[str, Any]:
    """Add recovery context to proof gate.
    
    This is purely additive — no migration required.
    
    v46: Recovery layer provides alternatives when proof requirements are not met.
    """
    if "recovery_context" not in proof_dict:
        proof_dict["recovery_context"] = None
    
    if recovery_engine and blocked_action:
        blocked_path = BlockedPath(
            blocked_path_id=f"blocked_{blocked_action[:20]}_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            original_action=blocked_action,
            blocked_path_type=BlockedPathType.BLOCKED_BY_PROOF_GATE.value,
            blocking_reason=blocking_reason or BlockingReason.INSUFFICIENT_EVIDENCE.value,
            severity=ViolationSeverity.HIGH.value,
        )
        recovery_engine.record_blocked_path(blocked_path)
        
        recovery = recovery_engine.generate_recovery_recommendation(blocked_path)
        
        proof_dict["recovery_context"] = {
            "path_blocked": True,
            "recovery_generated": recovery is not None,
            "preferred_alternative_id": recovery.preferred_alternative_id if recovery else None,
            "recommended_alternative_type": recovery.preferred_alternative_id.split("_")[0] if recovery and recovery.preferred_alternative_id else None,
        }
    
    return proof_dict


def integrate_with_escalation(
    escalation_dict: Dict[str, Any],
    recovery_engine: AlternativePathRecoveryEngine = None,
    blocked_action: str = None,
    trigger: str = None,
) -> Dict[str, Any]:
    """Add recovery context to escalation.
    
    This is purely additive — no migration required.
    
    v46: Recovery layer provides alternatives that may reduce escalation need.
    """
    if "recovery_context" not in escalation_dict:
        escalation_dict["recovery_context"] = None
    
    if recovery_engine and blocked_action:
        blocked_path = BlockedPath(
            blocked_path_id=f"blocked_{blocked_action[:20]}_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            original_action=blocked_action,
            blocked_path_type=BlockedPathType.BLOCKED_BY_CAPABILITY.value,
            blocking_reason=trigger or BlockingReason.CAPABILITY_PROHIBITED.value,
            severity=ViolationSeverity.HIGH.value,
        )
        recovery_engine.record_blocked_path(blocked_path)
        
        recovery = recovery_engine.generate_recovery_recommendation(blocked_path)
        
        escalation_dict["recovery_context"] = {
            "path_blocked": True,
            "recovery_generated": recovery is not None,
            "preferred_alternative_id": recovery.preferred_alternative_id if recovery else None,
            "recovery_confidence": recovery.overall_confidence if recovery else None,
        }
    
    return escalation_dict


def integrate_with_simulation(
    simulation_dict: Dict[str, Any],
    recovery_engine: AlternativePathRecoveryEngine = None,
    blocked_action: str = None,
    blocking_context: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Add recovery context to simulation.
    
    This is purely additive — no migration required.
    
    v46: Recovery layer provides alternatives for blocked actions in simulation.
    """
    if "recovery_context" not in simulation_dict:
        simulation_dict["recovery_context"] = None
    
    if recovery_engine and blocked_action:
        blocking_reason = blocking_context.get("reason", BlockingReason.INSUFFICIENT_EVIDENCE.value) if blocking_context else BlockingReason.INSUFFICIENT_EVIDENCE.value
        
        blocked_path = BlockedPath(
            blocked_path_id=f"blocked_{blocked_action[:20]}_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            original_action=blocked_action,
            original_context=blocking_context or {},
            blocked_path_type=BlockedPathType.BLOCKED_BY_INVARIANT.value,
            blocking_reason=blocking_reason,
            severity=ViolationSeverity.HIGH.value,
        )
        recovery_engine.record_blocked_path(blocked_path)
        
        recovery = recovery_engine.generate_recovery_recommendation(blocked_path)
        
        simulation_dict["recovery_context"] = {
            "path_blocked": True,
            "recovery_generated": recovery is not None,
            "preferred_alternative_id": recovery.preferred_alternative_id if recovery else None,
            "risk_reduction": recovery.risk_reduction if recovery else 0.0,
        }
    
    return simulation_dict


def integrate_with_compromise_explanation(
    compromise_dict: Dict[str, Any],
    recovery_engine: AlternativePathRecoveryEngine = None,
    blocked_action: str = None,
    blocking_reason: str = None,
) -> Dict[str, Any]:
    """Add recovery context to compromise explanation.
    
    This is purely additive — no migration required.
    
    v46: Recovery layer provides alternatives that explain why compromise occurred.
    """
    if "recovery_context" not in compromise_dict:
        compromise_dict["recovery_context"] = None
    
    if recovery_engine and blocked_action:
        blocked_path = BlockedPath(
            blocked_path_id=f"blocked_{blocked_action[:20]}_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            original_action=blocked_action,
            blocked_path_type=BlockedPathType.BLOCKED_BY_TRUST.value,
            blocking_reason=blocking_reason or BlockingReason.TRUST_TOO_LOW.value,
            severity=ViolationSeverity.HIGH.value,
        )
        recovery_engine.record_blocked_path(blocked_path)
        
        recovery = recovery_engine.generate_recovery_recommendation(blocked_path)
        
        compromise_dict["recovery_context"] = {
            "path_blocked": True,
            "recovery_generated": recovery is not None,
            "preferred_alternative_id": recovery.preferred_alternative_id if recovery else None,
            "recovery_explanation": f"Recovery recommended instead of compromise: {recovery.preferred_alternative_id}" if recovery else None,
        }
    
    return compromise_dict
