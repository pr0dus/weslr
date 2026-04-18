# personalization_profile.py - Self-Architecture Core v24: Adaptive Personalization Profile Layer
# User-model foundation for WESLR to adapt over time to habits, style, profession, learning pace, household context.
# Additive only, operator/user-first, transparent, reversible, suggestion-based, never hidden steering.
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


class CommunicationStyle(str, Enum):
    """Preferred communication style for user interaction."""
    CONCISE = "concise"  # Direct, minimal explanation
    DETAILED = "detailed"  # Thorough explanations, context-rich
    ANALYTICAL = "analytical"  # Data-driven, structured reasoning
    NARRATIVE = "narrative"  # Story-driven, contextual
    MIXED = "mixed"  # Adapts to context


class DomainFamiliarity(str, Enum):
    """User's familiarity with the domain/subject area."""
    BEGINNER = "beginner"  # Needs foundational explanations
    INTERMEDIATE = "intermediate"  # Understands concepts but not nuances
    ADVANCED = "advanced"  # Deep understanding, can handle abstractions
    EXPERT = "expert"  # Authority-level, can skip fundamentals
    HYBRID = "hybrid"  # Varies by subdomain


class PlanningDepth(str, Enum):
    """User's preferred depth of planning/forecasts."""
    SKETCHY = "sketchy"  # High-level overview
    BALANCED = "balanced"  # Reasonable detail
    THOROUGH = "thorough"  # Comprehensive breakdown
    MICROSCOPIC = "microscopic"  # Every detail considered


class LearningPace(str, Enum):
    """User's preferred learning pace for new concepts."""
    SLOW = "slow"  # Gradual, repeated exposure
    STEADY = "steady"  # Consistent progression
    RAPID = "rapid"  # Quick adoption, iterative learning
    SPORADIC = "sporadic"  # As-needed, intermittent


class RoutineStability(str, Enum):
    """User's preference for routine consistency vs flexibility."""
    HIGH_STABILITY = "high_stability"  # Strong routines, predictable
    MODERATE_STABILITY = "moderate_stability"  # Some flexibility
    LOW_STABILITY = "low_stability"  # Embraces change, adapts quickly
    DYNAMIC = "dynamic"  # Constantly evolving patterns


class GuidanceTolerance(str, Enum):
    """User's comfort with guidance and suggestion frequency."""
    INDEPENDENT = "independent"  # Minimal suggestions, prefer autonomy
    GUIDED = "guided"  # Some suggestions, prefer direction
    SUPPORTIVE = "supportive"  # Many suggestions, welcome context


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class ProfileField:
    """A single personalization field with confidence tracking."""
    
    # Configuration
    field_name: str
    value: str  # Enum value as string
    weight: float = 1.0  # Relative importance (0.0-1.0)
    
    # Evidence and confidence
    evidence_count: int = 0
    last_updated: Optional[str] = None
    confidence: float = 0.5  # 0.0-1.0
    confidence_source: Optional[str] = None  # "user_feedback", "observed_pattern", "expert_default"
    
    # Metadata
    last_evidence_at: Optional[str] = None
    update_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "field_name": self.field_name,
            "value": self.value,
            "weight": self.weight,
            "evidence_count": self.evidence_count,
            "last_updated": self.last_updated,
            "confidence": self.confidence,
            "confidence_source": self.confidence_source,
            "last_evidence_at": self.last_evidence_at,
            "update_count": self.update_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProfileField:
        """Create from dictionary representation."""
        return cls(**data)
    
    def update(self, new_value: str, confidence_source: str = "observed_pattern", weight: Optional[float] = None) -> ProfileField:
        """Update the field with new evidence."""
        self.value = new_value
        self.evidence_count += 1
        self.update_count += 1
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.last_evidence_at = self.last_updated
        self.confidence_source = confidence_source
        
        # Confidence increases with evidence (saturating at 0.95)
        self.confidence = min(0.95, 0.5 + (self.evidence_count * 0.05))
        
        if weight is not None:
            self.weight = weight
        
        return self


@dataclass
class PersonalizationProfile:
    """Adaptive personalization profile for a user.
    
    Collects and maintains user preferences across multiple dimensions.
    All fields are optional and default to "mixed" or neutral values.
    """
    
    # Communication preferences
    communication_style: str = CommunicationStyle.MIXED.value
    preferred_language: Optional[str] = None  # e.g., "en", "en-GB"
    
    # Domain/context preferences
    domain_familiarity: str = DomainFamiliarity.HYBRID.value
    primary_profession: Optional[str] = None  # e.g., "developer", "manager", "writer"
    
    # Planning preferences
    planning_depth: str = PlanningDepth.BALANCED.value
    tolerance_for_uncertainty: float = 0.5  # 0.0-1.0
    
    # Learning preferences
    learning_pace: str = LearningPace.STEADY.value
    preferred_learning_modality: Optional[str] = None  # e.g., "visual", "hands-on", "reading"
    
    # Routine preferences
    routine_stability: str = RoutineStability.MODERATE_STABILITY.value
    max_change_per_day: int = 3  # Maximum suggested changes per day
    
    # Guidance preferences
    guidance_tolerance: str = GuidanceTolerance.GUIDED.value
    max_suggestions_per_session: int = 5
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    profile_version: int = 1
    
    # Individual fields (for granular updates)
    _fields: Dict[str, ProfileField] = field(default_factory=dict, repr=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "communication_style": self.communication_style,
            "preferred_language": self.preferred_language,
            "domain_familiarity": self.domain_familiarity,
            "primary_profession": self.primary_profession,
            "planning_depth": self.planning_depth,
            "tolerance_for_uncertainty": self.tolerance_for_uncertainty,
            "learning_pace": self.learning_pace,
            "preferred_learning_modality": self.preferred_learning_modality,
            "routine_stability": self.routine_stability,
            "max_change_per_day": self.max_change_per_day,
            "guidance_tolerance": self.guidance_tolerance,
            "max_suggestions_per_session": self.max_suggestions_per_session,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "profile_version": self.profile_version,
            "fields": {k: v.to_dict() for k, v in self._fields.items()},
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PersonalizationProfile:
        """Create from dictionary representation."""
        fields_data = data.get("_fields", data.get("fields", {}))
        data["_fields"] = {k: ProfileField.from_dict(v) for k, v in fields_data.items()}
        # Remove 'fields' key if present to avoid duplicate in __init__
        if "fields" in data:
            del data["fields"]
        return cls(**data)
    
    # -------------------------------------------------------------------------
    # Field management
    # -------------------------------------------------------------------------
    
    def get_field(self, field_name: str) -> Optional[ProfileField]:
        """Get a profile field by name."""
        return self._fields.get(field_name)
    
    def set_field(
        self,
        field_name: str,
        value: str,
        confidence_source: str = "observed_pattern",
        weight: Optional[float] = None,
    ) -> PersonalizationProfile:
        """Set a profile field with evidence tracking."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.last_updated = now
        
        field = self._fields.get(field_name)
        if field is None:
            field = ProfileField(
                field_name=field_name,
                value=value,
                weight=weight if weight is not None else 1.0,
                confidence_source=confidence_source,
            )
            self._fields[field_name] = field
        else:
            field.update(value, confidence_source, weight)
        
        # Also update the main profile attribute if it's a standard field
        standard_fields = [
            "communication_style",
            "domain_familiarity",
            "planning_depth",
            "learning_pace",
            "routine_stability",
            "guidance_tolerance",
        ]
        if field_name in standard_fields:
            setattr(self, field_name, value)
        
        return self
    
    def update_field(
        self,
        field_name: str,
        new_value: str,
        confidence_source: str = "observed_pattern",
        weight: Optional[float] = None,
    ) -> PersonalizationProfile:
        """Alias for set_field (more semantically clear for updates)."""
        return self.set_field(field_name, new_value, confidence_source, weight)
    
    def get_field_confidence(self, field_name: str) -> float:
        """Get confidence for a specific field."""
        field = self._fields.get(field_name)
        return field.confidence if field else 0.0
    
    def get_all_confidences(self) -> Dict[str, float]:
        """Get confidence for all fields."""
        return {name: field.confidence for name, field in self._fields.items()}
    
    def get_average_confidence(self) -> float:
        """Get average confidence across all fields."""
        if not self._fields:
            return 0.0
        return sum(field.confidence for field in self._fields.values()) / len(self._fields)
    
    # -------------------------------------------------------------------------
    # Profile-based recommendations
    # -------------------------------------------------------------------------
    
    def get_communication_hint(self) -> str:
        """Get a hint about preferred communication style."""
        if self.communication_style == CommunicationStyle.CONCISE.value:
            return "prefers brief, direct responses"
        elif self.communication_style == CommunicationStyle.DETAILED.value:
            return "prefers thorough explanations with context"
        elif self.communication_style == CommunicationStyle.ANALYTICAL.value:
            return "prefers structured, data-driven reasoning"
        elif self.communication_style == CommunicationStyle.NARRATIVE.value:
            return "prefers story-driven, contextual framing"
        return "prefers context-appropriate communication"
    
    def get_domain_hint(self) -> str:
        """Get a hint about domain familiarity level."""
        if self.domain_familiarity == DomainFamiliarity.BEGINNER.value:
            return "needs foundational explanations"
        elif self.domain_familiarity == DomainFamiliarity.INTERMEDIATE.value:
            return "understands concepts but benefits from contextual support"
        elif self.domain_familiarity == DomainFamiliarity.ADVANCED.value:
            return "handles abstractions well"
        elif self.domain_familiarity == DomainFamiliarity.EXPERT.value:
            return "can skip fundamentals, dive straight to nuances"
        return "has hybrid familiarity that varies by subdomain"
    
    def get_planning_hint(self) -> str:
        """Get a hint about planning depth preference."""
        if self.planning_depth == PlanningDepth.SKETCHY.value:
            return "prefers high-level overviews"
        elif self.planning_depth == PlanningDepth.BALANCED.value:
            return "prefers reasonable detail"
        elif self.planning_depth == PlanningDepth.THOROUGH.value:
            return "prefers comprehensive breakdowns"
        return "prefers detailed, microscopic planning"
    
    def get_suggestion_cap(self) -> int:
        """Get maximum suggestions per session based on guidance tolerance."""
        if self.guidance_tolerance == GuidanceTolerance.INDEPENDENT.value:
            return 2
        elif self.guidance_tolerance == GuidanceTolerance.GUIDED.value:
            return 5
        elif self.guidance_tolerance == GuidanceTolerance.SUPPORTIVE.value:
            return 10
        return 15
    
    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------
    
    def get_profile_summary(self) -> Dict[str, Any]:
        """Get a human-readable summary of the profile."""
        return {
            "communication_style": self.communication_style,
            "domain_familiarity": self.domain_familiarity,
            "planning_depth": self.planning_depth,
            "learning_pace": self.learning_pace,
            "routine_stability": self.routine_stability,
            "guidance_tolerance": self.guidance_tolerance,
            "average_confidence": round(self.get_average_confidence(), 2),
            "field_count": len(self._fields),
        }


# ============================================================================
# PROFILE ENGINE
# ============================================================================


class PersonalizationEngine:
    """Engine for managing and applying personalization profiles.
    
    Operates independently - no network access required.
    All changes are transparent and reversible.
    """
    
    def __init__(self, storage_path: Optional[Any] = None):
        """Initialize personalization engine."""
        self.storage_path = storage_path
        self.profiles: Dict[str, PersonalizationProfile] = {}  # profile_id -> Profile
    
    def create_profile(self, profile_id: str) -> PersonalizationProfile:
        """Create a new personalization profile."""
        profile = PersonalizationProfile()
        self.profiles[profile_id] = profile
        return profile
    
    def get_profile(self, profile_id: str) -> Optional[PersonalizationProfile]:
        """Get a profile by ID."""
        return self.profiles.get(profile_id)
    
    def update_profile(
        self,
        profile_id: str,
        field_name: str,
        value: str,
        confidence_source: str = "observed_pattern",
    ) -> PersonalizationProfile:
        """Update a profile field with evidence."""
        profile = self.profiles.get(profile_id)
        if not profile:
            profile = self.create_profile(profile_id)
        profile.update_field(field_name, value, confidence_source)
        return profile
    
    def get_profile_summary(self, profile_id: str) -> Dict[str, Any]:
        """Get a summary of a profile."""
        profile = self.get_profile(profile_id)
        if not profile:
            return {"error": "profile_not_found"}
        return profile.get_profile_summary()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary."""
        return {
            "profile_count": len(self.profiles),
            "profiles": {k: v.to_dict() for k, v in self.profiles.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def apply_profile_to_narrative(narrative_dict: Dict[str, Any], profile: Optional[PersonalizationProfile] = None) -> Dict[str, Any]:
    """Apply profile context to narrative generation.
    
    This is purely additive — no migration required.
    Profile-aware narratives adjust style based on user preferences.
    """
    if profile is None:
        return narrative_dict
    
    narrative_dict["profile_hint"] = profile.get_profile_summary()
    narrative_dict["communication_hint"] = profile.get_communication_hint()
    narrative_dict["domain_hint"] = profile.get_domain_hint()
    narrative_dict["planning_hint"] = profile.get_planning_hint()
    
    return narrative_dict


def apply_profile_to_recommendation(recommendation_dict: Dict[str, Any], profile: Optional[PersonalizationProfile] = None) -> Dict[str, Any]:
    """Apply profile context to recommendations.
    
    This is purely additive — no migration required.
    Profile-aware recommendations adjust depth and style.
    """
    if profile is None:
        return recommendation_dict
    
    suggestion_cap = profile.get_suggestion_cap()
    recommendation_dict["profile_context"] = profile.get_profile_summary()
    recommendation_dict["suggestion_cap"] = suggestion_cap
    recommendation_dict["suggestions_remaining"] = max(0, suggestion_cap - recommendation_dict.get("suggestion_count", 0))
    
    return recommendation_dict


def integrate_with_governance_context(governance_dict: Dict[str, Any], profile: Optional[PersonalizationProfile] = None) -> Dict[str, Any]:
    """Add profile context to governance view.
    
    This is purely additive — no migration required.
    Profile context helps operators understand user preferences during review.
    """
    if profile is None:
        return governance_dict
    
    governance_dict["user_profile_hint"] = profile.get_profile_summary()
    governance_dict["preferred_communication"] = profile.communication_style
    governance_dict["domain_familiarity"] = profile.domain_familiarity
    governance_dict["guidance_tolerance"] = profile.guidance_tolerance
    
    return governance_dict


def integrate_with_proposal_realization(realization_dict: Dict[str, Any], profile: Optional[PersonalizationProfile] = None) -> Dict[str, Any]:
    """Add profile context to proposal realization.
    
    This is purely additive — no migration required.
    Profile context helps tailor the implementation plan to user preferences.
    """
    if profile is None:
        return realization_dict
    
    realization_dict["user_profile_context"] = profile.get_profile_summary()
    realization_dict["planning_depth_preference"] = profile.planning_depth
    realization_dict["learning_pace_preference"] = profile.learning_pace
    realization_dict["max_suggestions_per_session"] = profile.get_suggestion_cap()
    
    return realization_dict
