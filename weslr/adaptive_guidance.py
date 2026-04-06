# adaptive_guidance.py - Self-Architecture Core v27: Adaptive Guidance / Recommendation Context Layer
# Combine user profile, domain context, evidence quality, and safety/governance state into
# context-sensitive recommendation behavior.
# Additive only, transparent, suggestion-based, non-manipulative, reversible.
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


class RecommendationStrength(str, Enum):
    """Strength of recommendation."""
    WEAK = "weak"  # Tentative, informational
    MODERATE = "moderate"  # Suggested with some confidence
    STRONG = "strong"  # Recommended with high confidence
    DEFAULT = "default"  # Standard, no special emphasis


class GuidanceContextMode(str, Enum):
    """Mode for guidance context application."""
    ACTIVE = "active"  # Apply guidance context to recommendations
    RESTRICTED = "restricted"  # Apply guidance context with restrictions
    SILENT = "silent"  # Apply guidance context without explicit output
    OFF = "off"  # Disable guidance context


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class EvidenceQuality:
    """Quality assessment of evidence supporting a recommendation."""
    
    confidence: float = 0.5  # 0.0-1.0
    confidence_source: str = "default"  # e.g., "analysis", "measurement", "user_feedback"
    confidence_basis: Optional[str] = None  # Explanation of confidence level
    
    # Support metrics
    evidence_count: int = 0  # Number of supporting pieces
    supporting_sources: List[str] = field(default_factory=list)  # Source IDs
    
    # Quality indicators
    is_consistent: bool = True  # Consistent with known facts
    has_counter_evidence: bool = False  # Contradicted by other evidence
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "confidence": self.confidence,
            "confidence_source": self.confidence_source,
            "confidence_basis": self.confidence_basis,
            "evidence_count": self.evidence_count,
            "supporting_sources": self.supporting_sources,
            "is_consistent": self.is_consistent,
            "has_counter_evidence": self.has_counter_evidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceQuality:
        """Create from dictionary representation."""
        data["supporting_sources"] = data.get("supporting_sources", [])
        return cls(**data)
    
    def get_strength(self) -> RecommendationStrength:
        """Get recommendation strength based on quality."""
        if self.confidence < 0.4:
            return RecommendationStrength.WEAK.value
        elif self.confidence < 0.7:
            return RecommendationStrength.MODERATE.value
        elif self.confidence < 0.9:
            return RecommendationStrength.STRONG.value
        return RecommendationStrength.DEFAULT.value


@dataclass
class UserProfileContext:
    """User profile context for guidance adjustment."""
    
    # Profile attributes
    communication_style: str = "concise"  # concise, detailed, analytical, narrative
    domain_familiarity: str = "intermediate"  # beginner, intermediate, advanced, expert
    planning_depth: str = "balanced"  # sketchy, balanced, thorough, microscopic
    learning_pace: str = "steady"  # slow, steady, rapid, sporadic
    guidance_tolerance: str = "guided"  # independent, guided, supportive
    
    # Preferences
    max_suggestions_per_session: int = 5
    suggestion_cap: int = 5
    
    # Metadata
    profile_version: int = 1
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "communication_style": self.communication_style,
            "domain_familiarity": self.domain_familiarity,
            "planning_depth": self.planning_depth,
            "learning_pace": self.learning_pace,
            "guidance_tolerance": self.guidance_tolerance,
            "max_suggestions_per_session": self.max_suggestions_per_session,
            "suggestion_cap": self.suggestion_cap,
            "profile_version": self.profile_version,
            "last_updated": self.last_updated,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UserProfileContext:
        """Create from dictionary representation."""
        return cls(**data)
    
    def can_suggest(self) -> bool:
        """Check if user is open to suggestions."""
        return self.guidance_tolerance in ["guided", "supportive"]
    
    def get_max_suggestions(self) -> int:
        """Get maximum suggestions allowed for this profile."""
        if self.guidance_tolerance == "independent":
            return 2
        elif self.guidance_tolerance == "guided":
            return 5
        elif self.guidance_tolerance == "supportive":
            return 10
        return 5


@dataclass
class GuidanceContext:
    """Complete guidance context for recommendation generation.
    
    Combines user profile, domain context, evidence quality, and safety/governance state.
    """
    
    # Context components
    user_profile: Optional[UserProfileContext] = None
    domain_context: Optional[Dict[str, Any]] = None
    
    # Evidence context
    evidence_quality: Optional[EvidenceQuality] = None
    
    # Governance context
    safety_approved: bool = False
    safety_blocked: bool = False
    safety_blocked_reasons: List[str] = field(default_factory=list)
    
    # Guidance settings
    guidance_mode: str = GuidanceContextMode.ACTIVE.value
    recommendation_strength: str = RecommendationStrength.DEFAULT.value
    min_confidence_required: float = 0.0  # Minimum confidence to output recommendation
    
    # Output control
    explanation_basis: Optional[str] = None  # Basis for explanation
    can_silence: bool = True  # Can this output be silenced?
    hold_back_if_weak: bool = True  # Hold back weak recommendations
    
    # Metadata
    assessed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    assessed_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "user_profile": self.user_profile.to_dict() if self.user_profile else None,
            "domain_context": self.domain_context,
            "evidence_quality": self.evidence_quality.to_dict() if self.evidence_quality else None,
            "safety_approved": self.safety_approved,
            "safety_blocked": self.safety_blocked,
            "safety_blocked_reasons": self.safety_blocked_reasons,
            "guidance_mode": self.guidance_mode,
            "recommendation_strength": self.recommendation_strength,
            "min_confidence_required": self.min_confidence_required,
            "explanation_basis": self.explanation_basis,
            "can_silence": self.can_silence,
            "hold_back_if_weak": self.hold_back_if_weak,
            "assessed_at": self.assessed_at,
            "assessed_by": self.assessed_by,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GuidanceContext:
        """Create from dictionary representation."""
        profile_data = data.get("user_profile")
        data["user_profile"] = UserProfileContext.from_dict(profile_data) if profile_data else None
        
        quality_data = data.get("evidence_quality")
        data["evidence_quality"] = EvidenceQuality.from_dict(quality_data) if quality_data else None
        
        data["safety_blocked_reasons"] = data.get("safety_blocked_reasons", [])
        return cls(**data)
    
    def get_effective_strength(self) -> RecommendationStrength:
        """Get effective recommendation strength considering context."""
        # Check if blocked
        if self.safety_blocked:
            return RecommendationStrength.WEAK.value
        
        # Check evidence quality
        if self.evidence_quality:
            quality_strength = self.evidence_quality.get_strength()
            if quality_strength == RecommendationStrength.WEAK.value:
                if self.hold_back_if_weak:
                    return RecommendationStrength.WEAK.value
            return quality_strength
        
        return self.recommendation_strength
    
    def should_output(self) -> bool:
        """Check if this guidance should produce output."""
        # Check safety
        if self.safety_blocked:
            return False
        
        # Check confidence threshold
        if self.evidence_quality:
            if self.evidence_quality.confidence < self.min_confidence_required:
                return False
        
        # Check guidance mode
        if self.guidance_mode == GuidanceContextMode.OFF.value:
            return False
        
        # Check silence conditions
        if self.can_silence and not self.should_explain():
            return False
        
        return True
    
    def should_explain(self) -> bool:
        """Check if explanation should be included."""
        if not self.explanation_basis:
            return False
        
        # Check user profile
        if self.user_profile:
            if self.user_profile.communication_style == "concise":
                return False
        
        return True
    
    def get_recommendation_hint(self) -> str:
        """Get a human-readable hint about the recommendation."""
        strength = self.get_effective_strength()
        
        if strength == RecommendationStrength.WEAK.value:
            return "This is informational - consider but don't act immediately"
        elif strength == RecommendationStrength.MODERATE.value:
            return "This is a suggestion - review and consider"
        elif strength == RecommendationStrength.STRONG.value:
            return "This is recommended - consider prioritizing"
        
        return "Standard recommendation"


# ============================================================================
# GUIDANCE ENGINE
# ============================================================================


class AdaptiveGuidanceEngine:
    """Engine for managing adaptive guidance and recommendation context.
    
    Operates independently - no network access required.
    All guidance is transparent and reversible.
    """
    
    def __init__(self, storage_path: Optional[Any] = None):
        """Initialize adaptive guidance engine."""
        self.storage_path = storage_path
        self.contexts: Dict[str, GuidanceContext] = {}  # context_id -> Context
    
    def create_context(
        self,
        context_id: str,
        user_profile: Optional[UserProfileContext] = None,
        domain_context: Optional[Dict[str, Any]] = None,
        evidence_quality: Optional[EvidenceQuality] = None,
    ) -> GuidanceContext:
        """Create a guidance context."""
        context = GuidanceContext(
            user_profile=user_profile,
            domain_context=domain_context,
            evidence_quality=evidence_quality,
        )
        self.contexts[context_id] = context
        return context
    
    def get_context(self, context_id: str) -> Optional[GuidanceContext]:
        """Get a guidance context by ID."""
        return self.contexts.get(context_id)
    
    def assess_recommendation(
        self,
        context_id: str,
        evidence_confidence: float = 0.0,
        domain_context: Optional[Dict[str, Any]] = None,
    ) -> GuidanceContext:
        """Assess a recommendation and update context."""
        context = self.contexts.get(context_id)
        if not context:
            context = self.create_context(context_id)
        
        # Update evidence quality
        if evidence_confidence > 0:
            if not context.evidence_quality:
                context.evidence_quality = EvidenceQuality()
            context.evidence_quality.confidence = evidence_confidence
        
        # Update domain context if provided
        if domain_context:
            context.domain_context = domain_context
        
        context.assessed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        context.assessed_by = "adaptive_guidance_engine_v27"
        
        return context
    
    def get_recommendation_hint(self, context_id: str) -> str:
        """Get a recommendation hint for a context."""
        context = self.get_context(context_id)
        if not context:
            return "No context available"
        return context.get_recommendation_hint()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary."""
        return {
            "context_count": len(self.contexts),
            "contexts": {k: v.to_dict() for k, v in self.contexts.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_narrative(narrative_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add guidance context to narrative generation.
    
    This is purely additive — no migration required.
    """
    if "guidance_hint" not in narrative_dict:
        narrative_dict["guidance_hint"] = None
    if "explanation_basis" not in narrative_dict:
        narrative_dict["explanation_basis"] = None
    if "can_silence" not in narrative_dict:
        narrative_dict["can_silence"] = True
    if "recommendation_strength" not in narrative_dict:
        narrative_dict["recommendation_strength"] = RecommendationStrength.DEFAULT.value
    return narrative_dict


def integrate_with_operator_review(review_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add guidance context to operator proposal review.
    
    This is purely additive — no migration required.
    """
    if "guidance_context" not in review_dict:
        review_dict["guidance_context"] = None
    if "recommendation_hint" not in review_dict:
        review_dict["recommendation_hint"] = None
    if "can_hold_back" not in review_dict:
        review_dict["can_hold_back"] = False
    return review_dict


def integrate_with_governance_view(governance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add guidance context to governance view.
    
    This is purely additive — no migration required.
    """
    if "guidance_hint" not in governance_dict:
        governance_dict["guidance_hint"] = None
    if "explanation_available" not in governance_dict:
        governance_dict["explanation_available"] = False
    if "recommendation_strength" not in governance_dict:
        governance_dict["recommendation_strength"] = RecommendationStrength.DEFAULT.value
    return governance_dict


def integrate_with_proposal_realization(realization_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add guidance context to proposal realization.
    
    This is purely additive — no migration required.
    """
    if "guidance_hint" not in realization_dict:
        realization_dict["guidance_hint"] = None
    if "explanation_basis" not in realization_dict:
        realization_dict["explanation_basis"] = None
    if "can_hold_back" not in realization_dict:
        realization_dict["can_hold_back"] = False
    return realization_dict
