# final_decision_composer.py - WESLR v51: Recommendation Assembly / Final Decision Composer
# Creates a governed final-decision assembly layer so WESLR can combine guidance, policy,
# trust, timing, tension, invariants, simulation, escalation, and recovery into one
# coherent recommendation object.
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


class ConfidenceLevel(str, Enum):
    """Confidence level for final recommendation."""
    LOW = "low"  # < 50% confidence
    MODERATE = "moderate"  # 50-75% confidence
    HIGH = "high"  # 75-90% confidence
    VERY_HIGH = "very_high"  # > 90% confidence


class TimingPosture(str, Enum):
    """Timing posture for the recommendation."""
    IMMEDIATE = "immediate"  # Act now
    SHORT_TERM = "short_term"  # Within 24 hours
    MEDIUM_TERM = "medium_term"  # Within 7 days
    LONG_TERM = "long_term"  # Within 30 days
    AS_NEEDED = "as_needed"  # When conditions align


class TrustPosture(str, Enum):
    """Trust posture for the recommendation."""
    CAUTIOUS = "cautious"  # High caution, low trust
    STANDARD = "standard"  # Normal trust level
    ENHANCED = "enhanced"  # Elevated trust based on evidence
    FULL = "full"  # Full confidence, minimal oversight


class EscalationRequirement(str, Enum):
    """Escalation requirement for the recommendation."""
    NONE = "none"  # No escalation needed
    OPERATOR = "operator"  # Requires operator review
    SENIOR = "senior"  # Requires senior operator review
    EMERGENCY = "emergency"  # Requires immediate escalation
    OPTIONAL = "optional"  # Escalation available but not required


class RecoveryPath(str, Enum):
    """Recovery path if the recommendation is executed and fails."""
    NONE = "none"  # No defined recovery path
    AUTO_REVERT = "auto_revert"  # Automatic revert
    OPERATOR_INTERVENTION = "operator_intervention"  # Requires operator action
    GRADUAL_REVERT = "gradual_revert"  # Gradual rollback with monitoring
    fallback = "fallback"  # Fallback to previous state


class BlockedAlternative(str, Enum):
    """Alternative that was blocked or softened by this recommendation."""
    REJECTED = "rejected"  # Fully rejected alternative
    POSTPONED = "postponed"  # Postponed with scheduled review
    MODIFIED = "modified"  # Modified to be compatible
    CONSIDERED = "considered"  # Considered but not chosen


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class RecommendationBundle:
    """A bundle of evidence supporting the recommendation."""
    
    evidence_ids: List[str] = field(default_factory=list)  # References to evidence items
    evidence_sources: List[str] = field(default_factory=list)  # Source identifiers
    confidence: float = 0.0  # 0.0-1.0
    confidence_basis: Optional[str] = None  # Explanation of confidence
    supporting_factors: List[str] = field(default_factory=list)  # What supports this
    opposing_factors: List[str] = field(default_factory=list)  # What opposes this
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_ids": self.evidence_ids,
            "evidence_sources": self.evidence_sources,
            "confidence": self.confidence,
            "confidence_basis": self.confidence_basis,
            "supporting_factors": self.supporting_factors,
            "opposing_factors": self.opposing_factors,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RecommendationBundle:
        data.setdefault("evidence_ids", [])
        data.setdefault("evidence_sources", [])
        data.setdefault("supporting_factors", [])
        data.setdefault("opposing_factors", [])
        return cls(**data)


@dataclass
class ActiveTension:
    """An active tension that influenced the recommendation."""
    
    tension_id: str  # Unique identifier
    tension_type: str  # e.g., "safety_vs_efficiency", "speed_vs_quality"
    resolution: str  # How the tension was resolved
    affected_rules: List[str] = field(default_factory=list)  # Rules affected
    outcome: str = "resolved"  # Resolution outcome
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tension_id": self.tension_id,
            "tension_type": self.tension_type,
            "resolution": self.resolution,
            "affected_rules": self.affected_rules,
            "outcome": self.outcome,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ActiveTension:
        data.setdefault("affected_rules", [])
        return cls(**data)


@dataclass
class GoverningRule:
    """The governing rule that drives this recommendation."""
    
    rule_id: str  # Unique identifier
    rule_type: str  # e.g., "safety_strictness", "escalation_strictness"
    rule_value: str  # The value or threshold
    precedence_level: str = "medium"  # Precedence level
    override_type: str = "none"  # Override type
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type,
            "rule_value": self.rule_value,
            "precedence_level": self.precedence_level,
            "override_type": self.override_type,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GoverningRule:
        data.setdefault("precedence_level", "medium")
        data.setdefault("override_type", "none")
        return cls(**data)


@dataclass
class BlockedAlternativeEntry:
    """An alternative that was blocked or softened."""
    
    alternative_id: str  # Original alternative identifier
    alternative_type: str  # e.g., "alternative_path", "escalation_path"
    blocked_reason: str  # Why it was blocked
    softened_by: Optional[str] = None  # What softened it
    reevaluation_trigger: Optional[str] = None  # When to reevaluate
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alternative_id": self.alternative_id,
            "alternative_type": self.alternative_type,
            "blocked_reason": self.blocked_reason,
            "softened_by": self.softened_by,
            "reevaluation_trigger": self.reevaluation_trigger,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BlockedAlternativeEntry:
        return cls(**data)


@dataclass
class FinalRecommendation:
    """Final recommendation object assembled from all layers.
    
    Combines:
    - Guidance (what should be done)
    - Policy (what can be done)
    - Trust (how much to trust it)
    - Timing (when to do it)
    - Tension (what tradeoffs were made)
    - Invariants (what cannot be violated)
    - Simulation (what was tested)
    - Escalation (who needs to review)
    - Recovery (what if it fails)
    """
    
    # Core recommendation
    recommendation_id: str  # Unique identifier
    recommendation_type: str  # e.g., "action", "defer", "investigate"
    recommendation_text: str  # Human-readable recommendation
    
    # Assessment
    confidence: float = 0.5  # 0.0-1.0
    confidence_level: str = ConfidenceLevel.MODERATE.value
    confidence_bundle: Optional[RecommendationBundle] = None
    
    # Timing
    timing_posture: str = TimingPosture.SHORT_TERM.value
    due_by: Optional[str] = None  # ISO timestamp
    
    # Trust
    trust_posture: str = TrustPosture.STANDARD.value
    trust_basis: Optional[str] = None  # Explanation of trust level
    
    # Tensions
    active_tensions: List[Dict[str, Any]] = field(default_factory=list)  # Active tensions
    
    # Governing rules
    governing_rules: List[Dict[str, Any]] = field(default_factory=list)  # Governing rules
    
    # Blocked/softened alternatives
    blocked_alternatives: List[Dict[str, Any]] = field(default_factory=list)  # Blocked alternatives
    
    # Recovery
    recovery_path: str = RecoveryPath.NONE.value
    recovery_description: Optional[str] = None  # Description of recovery path
    recovery_triggers: List[str] = field(default_factory=list)  # When to trigger recovery
    
    # Escalation
    escalation_required: str = EscalationRequirement.NONE.value
    escalation_reason: Optional[str] = None  # Why escalation is needed
    escalation_path: Optional[str] = None  # Where to escalate
    
    # Explanation bundle
    explanation_bundle: Dict[str, Any] = field(default_factory=dict)  # Full explanation
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    created_by: Optional[str] = None
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "recommendation_type": self.recommendation_type,
            "recommendation_text": self.recommendation_text,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level,
            "confidence_bundle": self.confidence_bundle.to_dict() if self.confidence_bundle else None,
            "timing_posture": self.timing_posture,
            "due_by": self.due_by,
            "trust_posture": self.trust_posture,
            "trust_basis": self.trust_basis,
            "active_tensions": self.active_tensions,
            "governing_rules": self.governing_rules,
            "blocked_alternatives": self.blocked_alternatives,
            "recovery_path": self.recovery_path,
            "recovery_description": self.recovery_description,
            "recovery_triggers": self.recovery_triggers,
            "escalation_required": self.escalation_required,
            "escalation_reason": self.escalation_reason,
            "escalation_path": self.escalation_path,
            "explanation_bundle": self.explanation_bundle,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "last_updated": self.last_updated,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FinalRecommendation:
        bundle_data = data.get("confidence_bundle")
        data["confidence_bundle"] = RecommendationBundle.from_dict(bundle_data) if bundle_data else None
        
        # Convert lists of dicts to objects for nested dataclasses
        data["active_tensions"] = data.get("active_tensions", [])
        data["governing_rules"] = data.get("governing_rules", [])
        data["blocked_alternatives"] = data.get("blocked_alternatives", [])
        data["recovery_triggers"] = data.get("recovery_triggers", [])
        
        data.setdefault("explanation_bundle", {})
        data.setdefault("created_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        data.setdefault("last_updated", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        
        return cls(**data)
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the recommendation."""
        parts = []
        
        parts.append(f"**{self.recommendation_type.upper()}**")
        parts.append(self.recommendation_text)
        parts.append("")
        parts.append(f"Confidence: {self.confidence:.0%} ({self.confidence_level})")
        parts.append(f"Timing: {self.timing_posture.replace('_', ' ').title()}")
        parts.append(f"Trust: {self.trust_posture.replace('_', ' ').title()}")
        parts.append(f"Escalation: {self.escalation_required.replace('_', ' ').title()}")
        
        if self.active_tensions:
            tensions = [t.get("tension_type", "unknown") for t in self.active_tensions]
            parts.append(f"Tensions resolved: {', '.join(tensions[:3])}")
        
        if self.governing_rules:
            rules = [r.get("rule_type", "unknown") for r in self.governing_rules]
            parts.append(f"Governing rules: {', '.join(rules[:3])}")
        
        if self.blocked_alternatives:
            alternatives = [a.get("alternative_type", "unknown") for a in self.blocked_alternatives]
            parts.append(f"Blocked alternatives: {', '.join(alternatives[:3])}")
        
        if self.recovery_path and self.recovery_path != "none":
            parts.append(f"Recovery: {self.recovery_path.replace('_', ' ').title()}")
        
        return "\n".join(parts)
    
    def get_explanation(self) -> str:
        """Get a detailed explanation from the explanation bundle."""
        explanation = self.explanation_bundle.get("explanation", "")
        if explanation:
            return explanation
        
        # Build explanation from components if bundle is empty
        parts = []
        parts.append(f"Recommendation: {self.recommendation_text}")
        parts.append("")
        parts.append("## Rationale")
        
        if self.confidence_bundle:
            parts.append(f"**Evidence Confidence**: {self.confidence_bundle.confidence:.0%}")
            if self.confidence_bundle.confidence_basis:
                parts.append(f"*{self.confidence_bundle.confidence_basis}*")
        
        if self.active_tensions:
            parts.append("")
            parts.append("## Tensions Resolved")
            for tension in self.active_tensions:
                parts.append(f"- {tension.get('tension_type', 'unknown')}: {tension.get('resolution', 'unknown')}")
        
        if self.governing_rules:
            parts.append("")
            parts.append("## Governing Rules")
            for rule in self.governing_rules:
                parts.append(f"- {rule.get('rule_type', 'unknown')}: {rule.get('rule_value', 'unknown')}")
        
        return "\n".join(parts)


# ============================================================================
# FINAL DECISION COMPOSER
# ============================================================================


class FinalDecisionComposer:
    """Engine for assembling final recommendations from multiple layers.
    
    Combines:
    - Adaptive guidance
    - Policy conflict resolution
    - Governance surface
    - Unified operator context
    
    All composition is additive, transparent, reversible, and role-aware.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize final decision composer."""
        self.storage_path = storage_path or "/data/data/com.termux/files/home/.openclaw/workspace/weslr/final_decision/"
        self.recommendations: Dict[str, FinalRecommendation] = {}
        self.composition_counter: int = 0
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _generate_recommendation_id(self) -> str:
        """Generate unique recommendation ID."""
        self.composition_counter += 1
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"rec_{timestamp}_{self.composition_counter:04d}"
    
    def assemble_recommendation(
        self,
        recommendation_type: str,
        recommendation_text: str,
        guidance_context: Optional[Dict[str, Any]] = None,
        policy_context: Optional[Dict[str, Any]] = None,
        governance_context: Optional[Dict[str, Any]] = None,
        operator_context: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
    ) -> FinalRecommendation:
        """Assemble a final recommendation from multiple context layers.
        
        Additive composition:
        - Guidance provides confidence and timing
        - Policy provides governing rules and tensions
        - Governance provides recovery and escalation
        - Operator context provides trust posture and blocking context
        """
        rec_id = self._generate_recommendation_id()
        
        # Build confidence bundle from guidance context
        confidence_bundle = None
        if guidance_context:
            confidence = guidance_context.get("evidence_quality", {}).get("confidence", 0.5)
            confidence_bundle = RecommendationBundle(
                confidence=confidence,
                confidence_basis=guidance_context.get("evidence_quality", {}).get("confidence_basis"),
                evidence_sources=guidance_context.get("evidence_quality", {}).get("supporting_sources", []),
                supporting_factors=guidance_context.get("evidence_quality", {}).get("supporting_factors", []),
            )
        
        # Build active tensions from policy context
        active_tensions = []
        if policy_context:
            for tension_data in policy_context.get("active_tensions", []):
                active_tensions.append(ActiveTension.from_dict(tension_data).to_dict())
        
        # Build governing rules from policy context
        governing_rules = []
        if policy_context:
            for rule_data in policy_context.get("governing_rules", []):
                governing_rules.append(GoverningRule.from_dict(rule_data).to_dict())
        
        # Build blocked alternatives from policy context
        blocked_alternatives = []
        if policy_context:
            for blocked_data in policy_context.get("blocked_alternatives", []):
                blocked_alternatives.append(BlockedAlternativeEntry.from_dict(blocked_data).to_dict())
        
        # Build recovery path from governance context
        recovery_path = RecoveryPath.NONE.value
        recovery_description = None
        recovery_triggers = []
        if governance_context:
            recovery_path = governance_context.get("recovery_path", RecoveryPath.NONE.value)
            recovery_description = governance_context.get("recovery_description")
            recovery_triggers = governance_context.get("recovery_triggers", [])
        
        # Build escalation from governance context
        escalation_required = EscalationRequirement.NONE.value
        escalation_reason = None
        escalation_path = None
        if governance_context:
            escalation_required = governance_context.get("escalation_required", EscalationRequirement.NONE.value)
            escalation_reason = governance_context.get("escalation_reason")
            escalation_path = governance_context.get("escalation_path")
        
        # Build trust posture from operator context
        trust_posture = TrustPosture.STANDARD.value
        trust_basis = None
        if operator_context:
            trust_posture = operator_context.get("trust_posture", TrustPosture.STANDARD.value)
            trust_basis = operator_context.get("trust_basis")
        
        # Build timing posture from guidance context
        timing_posture = TimingPosture.SHORT_TERM.value
        due_by = None
        if guidance_context:
            timing_posture = guidance_context.get("timing_posture", TimingPosture.SHORT_TERM.value)
            due_by = guidance_context.get("due_by")
        
        # Build explanation bundle from all contexts
        explanation_bundle = {
            "source": "final_decision_composer_v51",
            "recommendation_id": rec_id,
            "recommendation_type": recommendation_type,
        }
        
        # Add guidance explanation
        if guidance_context:
            explanation_bundle["guidance"] = {
                "confidence": confidence_bundle.confidence if confidence_bundle else 0.0,
                "timing": timing_posture,
            }
        
        # Add policy explanation
        if policy_context:
            explanation_bundle["policy"] = {
                "conflict_resolution": policy_context.get("conflict_resolution_context"),
                "governing_rules_count": len(governing_rules),
                "active_tensions_count": len(active_tensions),
            }
        
        # Add governance explanation
        if governance_context:
            explanation_bundle["governance"] = {
                "recovery_path": recovery_path,
                "escalation_required": escalation_required,
            }
        
        # Add operator context explanation
        if operator_context:
            explanation_bundle["operator"] = {
                "trust_posture": trust_posture,
                "reliability_mode": operator_context.get("reliability_mode"),
            }
        
        # Determine confidence level
        confidence = confidence_bundle.confidence if confidence_bundle else 0.5
        confidence_level = ConfidenceLevel.MODERATE.value
        if confidence < 0.4:
            confidence_level = ConfidenceLevel.LOW.value
        elif confidence < 0.7:
            confidence_level = ConfidenceLevel.MODERATE.value
        elif confidence < 0.9:
            confidence_level = ConfidenceLevel.HIGH.value
        else:
            confidence_level = ConfidenceLevel.VERY_HIGH.value
        
        recommendation = FinalRecommendation(
            recommendation_id=rec_id,
            recommendation_type=recommendation_type,
            recommendation_text=recommendation_text,
            confidence=confidence,
            confidence_level=confidence_level,
            confidence_bundle=confidence_bundle,
            timing_posture=timing_posture,
            due_by=due_by,
            trust_posture=trust_posture,
            trust_basis=trust_basis,
            active_tensions=active_tensions,
            governing_rules=governing_rules,
            blocked_alternatives=blocked_alternatives,
            recovery_path=recovery_path,
            recovery_description=recovery_description,
            recovery_triggers=recovery_triggers,
            escalation_required=escalation_required,
            escalation_reason=escalation_reason,
            escalation_path=escalation_path,
            explanation_bundle=explanation_bundle,
            created_by=created_by,
        )
        
        self.recommendations[rec_id] = recommendation
        self._save_recommendation(recommendation)
        return recommendation
    
    def _save_recommendation(self, recommendation: FinalRecommendation) -> None:
        """Save recommendation to storage."""
        import os
        
        filepath = os.path.join(self.storage_path, f"{recommendation.recommendation_id}.json")
        with open(filepath, "w") as f:
            json.dump(recommendation.to_dict(), f, indent=2)
    
    def get_recommendation(self, rec_id: str) -> Optional[FinalRecommendation]:
        """Get a recommendation by ID."""
        return self.recommendations.get(rec_id)
    
    def get_latest_recommendation(self) -> Optional[FinalRecommendation]:
        """Get the most recent recommendation."""
        if not self.recommendations:
            return None
        return max(self.recommendations.values(), key=lambda r: r.created_at)
    
    def compose_from_adaptive_guidance(
        self,
        guidance_context: Dict[str, Any],
        recommendation_text: str,
        created_by: Optional[str] = None,
    ) -> FinalRecommendation:
        """Compose recommendation using adaptive guidance context.
        
        Additive only — no migration required.
        """
        return self.assemble_recommendation(
            recommendation_type="action",
            recommendation_text=recommendation_text,
            guidance_context=guidance_context,
            created_by=created_by,
        )
    
    def compose_from_policy_conflict(
        self,
        policy_context: Dict[str, Any],
        recommendation_text: str,
        created_by: Optional[str] = None,
    ) -> FinalRecommendation:
        """Compose recommendation using policy conflict resolution context.
        
        Additive only — no migration required.
        """
        return self.assemble_recommendation(
            recommendation_type="action",
            recommendation_text=recommendation_text,
            policy_context=policy_context,
            created_by=created_by,
        )
    
    def compose_from_governance(
        self,
        governance_context: Dict[str, Any],
        recommendation_text: str,
        created_by: Optional[str] = None,
    ) -> FinalRecommendation:
        """Compose recommendation using governance context.
        
        Additive only — no migration required.
        """
        return self.assemble_recommendation(
            recommendation_type="action",
            recommendation_text=recommendation_text,
            governance_context=governance_context,
            created_by=created_by,
        )
    
    def compose_from_operator_context(
        self,
        operator_context: Dict[str, Any],
        recommendation_text: str,
        created_by: Optional[str] = None,
    ) -> FinalRecommendation:
        """Compose recommendation using unified operator context.
        
        Additive only — no migration required.
        """
        return self.assemble_recommendation(
            recommendation_type="action",
            recommendation_text=recommendation_text,
            operator_context=operator_context,
            created_by=created_by,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert composer state to dictionary."""
        return {
            "recommendation_count": len(self.recommendations),
            "composition_counter": self.composition_counter,
            "recommendations": {k: v.to_dict() for k, v in self.recommendations.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_adaptive_guidance(guidance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add final decision composer context to adaptive guidance.
    
    This is purely additive — no migration required.
    
    v51: Final decision composer provides recommendation assembly and composition.
    """
    if "final_decision_context" not in guidance_dict:
        guidance_dict["final_decision_context"] = None
    
    return guidance_dict


def integrate_with_policy_conflict_resolution(
    policy_dict: Dict[str, Any],
    composer: FinalDecisionComposer = None,
) -> Dict[str, Any]:
    """Add final decision composer context to policy conflict resolution.
    
    This is purely additive — no migration required.
    
    v51: Final decision composer provides recommendation assembly from policy.
    """
    if "final_decision_context" not in policy_dict:
        policy_dict["final_decision_context"] = None
    
    if composer:
        policy_dict["final_decision_context"] = {
            "composer_storage_path": composer.storage_path,
            "recommendation_count": len(composer.recommendations),
        }
    
    return policy_dict


def integrate_with_governance_surface(
    governance_dict: Dict[str, Any],
    composer: FinalDecisionComposer = None,
) -> Dict[str, Any]:
    """Add final decision composer context to governance surface.
    
    This is purely additive — no migration required.
    
    v51: Final decision composer provides assembled recommendations.
    """
    if "final_decision_context" not in governance_dict:
        governance_dict["final_decision_context"] = None
    
    if composer:
        latest = composer.get_latest_recommendation()
        governance_dict["final_decision_context"] = {
            "composer_storage_path": composer.storage_path,
            "recommendation_count": len(composer.recommendations),
            "has_latest_recommendation": latest is not None,
            "latest_recommendation_id": latest.recommendation_id if latest else None,
            "latest_recommendation_type": latest.recommendation_type if latest else None,
        }
    
    return governance_dict


def integrate_with_unified_operator_context(
    operator_dict: Dict[str, Any],
    composer: FinalDecisionComposer = None,
) -> Dict[str, Any]:
    """Add final decision composer context to unified operator context.
    
    This is purely additive — no migration required.
    
    v51: Final decision composer provides assembled recommendations for operator review.
    """
    if "final_decision_context" not in operator_dict:
        operator_dict["final_decision_context"] = None
    
    if composer:
        operator_dict["final_decision_context"] = {
            "composer_storage_path": composer.storage_path,
            "recommendation_count": len(composer.recommendations),
        }
    
    return operator_dict


# ============================================================================
# INTEGRATION HOOKS FOR v52 DELIVERY (Additive)
# ============================================================================


def integrate_with_recommendation_delivery(
    recommendation_dict: Dict[str, Any],
    delivery_composer: Any = None,
) -> Dict[str, Any]:
    """Add delivery composer context to final decision recommendations.
    
    This is purely additive — no migration required.
    
    v52: Delivery composer provides presentation modes for recommendations.
    """
    if "delivery_context" not in recommendation_dict:
        recommendation_dict["delivery_context"] = None
    
    if delivery_composer:
        latest = delivery_composer.get_latest_delivery() if hasattr(delivery_composer, "get_latest_delivery") else None
        recommendation_dict["delivery_context"] = {
            "delivery_storage_path": getattr(delivery_composer, "storage_path", None),
            "delivery_count": len(delivery_composer.renderings) if hasattr(delivery_composer, "renderings") else 0,
            "has_latest_delivery": latest is not None,
            "latest_delivery_id": latest.delivery_id if latest else None,
        }
    
    return recommendation_dict
