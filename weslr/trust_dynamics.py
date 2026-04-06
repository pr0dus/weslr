# trust_dynamics.py - v37: Trust / Relationship Dynamics Layer
# Creates a governed trust-state layer so WESLR can adapt its caution, proactivity,
# and explanation depth based on relationship dynamics and user trust over time.
# Additive only, transparent, reversible, suggestion-based, non-manipulative, no repo drift.
# Local to WESLR scope.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# ENUMS
# ============================================================================


class TrustLevel(str, Enum):
    """Level of trust in the relationship."""
    HIGH = "high"  # Strong trust, minimal caution needed
    MODERATE = "moderate"  # Some trust, balanced approach
    LOW = "low"  # Limited trust, increased caution required
    NEUTRAL = "neutral"  # No established trust pattern


class FrictionLevel(str, Enum):
    """Level of friction in the relationship."""
    LOW = "low"  # Smooth interactions, minimal friction
    MODERATE = "moderate"  # Occasional friction, manageable
    HIGH = "high"  # Frequent friction, requires patience
    RESISTANCE = "resistance"  # Active resistance, needs de-escalation


class GuidanceMode(str, Enum):
    """Mode for guidance delivery based on trust."""
    CONCISE = "concise"  # Minimal explanation, direct
    BALANCED = "balanced"  # Standard explanation depth
    DETAILED = "detailed"  # Comprehensive explanation, reasoning
    REASSURING = "reassuring"  # Extra reassurance, slower pace


class RecoveryState(str, Enum):
    """State of trust recovery after erosion."""
    STABLE = "stable"  # Trust level stable, no active recovery
    RECOVERING = "recovering"  # Actively working on recovery
    REESTABLISHED = "reestablished"  # Trust rebuilt


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class TrustMetrics:
    """Metrics tracking trust state over time."""
    
    # Core trust metrics
    trust_score: float = 0.5  # 0.0-1.0, current trust level
    trust_level: str = TrustLevel.MODERATE.value  # Discrete trust level
    
    # Relationship factors
    total_interactions: int = 0  # Total interactions with the user
    positive_interactions: int = 0  # Positive/successful interactions
    negative_interactions: int = 0  # Negative/rejected interactions
    
    # Temporal metrics
    first_interaction_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    last_interaction_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    # Confidence in assessment
    confidence_score: float = 0.5  # How confident we are in current trust assessment
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "trust_score": self.trust_score,
            "trust_level": self.trust_level,
            "total_interactions": self.total_interactions,
            "positive_interactions": self.positive_interactions,
            "negative_interactions": self.negative_interactions,
            "first_interaction_at": self.first_interaction_at,
            "last_interaction_at": self.last_interaction_at,
            "confidence_score": self.confidence_score,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TrustMetrics:
        """Create from dictionary representation."""
        return cls(**data)
    
    def update_from_interaction(self, is_positive: bool) -> None:
        """Update metrics based on a new interaction."""
        self.total_interactions += 1
        self.last_interaction_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        if is_positive:
            self.positive_interactions += 1
        else:
            self.negative_interactions += 1
        
        # Update trust score based on interaction history
        if self.total_interactions >= 3:
            ratio = self.positive_interactions / self.total_interactions
            self.trust_score = ratio
            self.confidence_score = min(0.95, 0.5 + (self.total_interactions - 1) * 0.05)
        
        # Update trust level based on score
        self._update_trust_level()
    
    def _update_trust_level(self) -> None:
        """Update discrete trust level based on score."""
        if self.trust_score >= 0.7:
            self.trust_level = TrustLevel.HIGH.value
        elif self.trust_score >= 0.4:
            self.trust_level = TrustLevel.MODERATE.value
        else:
            self.trust_level = TrustLevel.LOW.value
    
    def get_trust_level_enum(self) -> TrustLevel:
        """Get trust level as enum."""
        return TrustLevel(self.trust_level)


@dataclass
class FrictionFactors:
    """Factors contributing to friction in the relationship."""
    
    # Friction metrics
    friction_score: float = 0.0  # 0.0-1.0, current friction level
    friction_level: str = FrictionLevel.LOW.value
    
    # Friction sources
    rejected_suggestions: int = 0  # Number of rejected suggestions
    ignored_recommendations: int = 0  # Number of ignored recommendations
    interrupted_interactions: int = 0  # Number of times user interrupted
    clarification_requests: int = 0  # Number of clarification requests
    
    # Timing metrics
    average_response_time_seconds: float = 0.0  # Average time to respond
    last_friction_event_at: Optional[str] = None  # When last friction occurred
    
    # Flags for specific friction markers
    has_resistance_markers: bool = False  # Active resistance indicators
    resistance_reasons: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "friction_score": self.friction_score,
            "friction_level": self.friction_level,
            "rejected_suggestions": self.rejected_suggestions,
            "ignored_recommendations": self.ignored_recommendations,
            "interrupted_interactions": self.interrupted_interactions,
            "clarification_requests": self.clarification_requests,
            "average_response_time_seconds": self.average_response_time_seconds,
            "last_friction_event_at": self.last_friction_event_at,
            "has_resistance_markers": self.has_resistance_markers,
            "resistance_reasons": self.resistance_reasons,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FrictionFactors:
        """Create from dictionary representation."""
        data["resistance_reasons"] = data.get("resistance_reasons", [])
        return cls(**data)
    
    def record_rejection(self, reason: Optional[str] = None) -> None:
        """Record a rejected suggestion."""
        self.rejected_suggestions += 1
        self.last_friction_event_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        if reason:
            if reason not in self.resistance_reasons:
                self.resistance_reasons.append(reason)
        
        self._update_friction_level()
    
    def record_ignoring(self) -> None:
        """Record an ignored recommendation."""
        self.ignored_recommendations += 1
        self._update_friction_level()
    
    def _update_friction_level(self) -> None:
        """Update discrete friction level based on score."""
        # Simple heuristic: score based on rejection ratio
        total_friction_events = (
            self.rejected_suggestions +
            self.ignored_recommendations +
            self.interrupted_interactions
        )
        
        if total_friction_events == 0:
            self.friction_score = 0.0
            self.friction_level = FrictionLevel.LOW.value
            self.has_resistance_markers = False
            return
        
        # Calculate friction score
        base_friction = total_friction_events / max(1, self.total_interactions or 1)
        self.friction_score = min(1.0, base_friction)
        
        # Update level
        if self.friction_score >= 0.5:
            self.friction_level = FrictionLevel.RESISTANCE.value
            self.has_resistance_markers = True
        elif self.friction_score >= 0.3:
            self.friction_level = FrictionLevel.HIGH.value
        elif self.friction_score >= 0.15:
            self.friction_level = FrictionLevel.MODERATE.value
        else:
            self.friction_level = FrictionLevel.LOW.value
    
    @property
    def total_interactions(self) -> int:
        """Access total interactions from trust metrics."""
        return 0  # Will be overridden by relationship state
    
    def get_friction_level_enum(self) -> FrictionLevel:
        """Get friction level as enum."""
        return FrictionLevel(self.friction_level)


@dataclass
class RelationshipState:
    """Complete state of the relationship with the user."""
    
    # Identity
    relationship_id: str  # Unique identifier for this relationship
    
    # Core components
    trust_metrics: TrustMetrics = field(default_factory=TrustMetrics)
    friction_factors: FrictionFactors = field(default_factory=FrictionFactors)
    
    # Relationship state
    guidance_mode: str = GuidanceMode.BALANCED.value
    explanation_depth: int = 2  # Depth level: 1=minimal, 2=standard, 3=detailed, 4=reassuring
    
    # Recovery state
    recovery_state: str = RecoveryState.STABLE.value
    recovery_started_at: Optional[str] = None
    recovery_progress: float = 0.0  # 0.0-1.0
    
    # Proactivity settings
    proactivity_score: float = 0.5  # 0.0-1.0, how proactive to be
    max_suggestions_per_session: int = 5
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    last_updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "relationship_id": self.relationship_id,
            "trust_metrics": self.trust_metrics.to_dict(),
            "friction_factors": self.friction_factors.to_dict(),
            "guidance_mode": self.guidance_mode,
            "explanation_depth": self.explanation_depth,
            "recovery_state": self.recovery_state,
            "recovery_started_at": self.recovery_started_at,
            "recovery_progress": self.recovery_progress,
            "proactivity_score": self.proactivity_score,
            "max_suggestions_per_session": self.max_suggestions_per_session,
            "created_at": self.created_at,
            "last_updated_at": self.last_updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RelationshipState:
        """Create from dictionary representation."""
        trust_data = data.get("trust_metrics", {})
        data["trust_metrics"] = TrustMetrics.from_dict(trust_data)
        
        friction_data = data.get("friction_factors", {})
        data["friction_factors"] = FrictionFactors.from_dict(friction_data)
        
        return cls(**data)
    
    def record_interaction(self, is_positive: bool, reason: Optional[str] = None) -> None:
        """Record an interaction and update all related metrics."""
        self.trust_metrics.update_from_interaction(is_positive)
        
        if not is_positive:
            self.friction_factors.record_rejection(reason)
        
        self.last_updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self._update_relationship_state()
    
    def _update_relationship_state(self) -> None:
        """Update guidance mode and explanation depth based on current state."""
        trust_level = self.trust_metrics.get_trust_level_enum()
        friction_level = self.friction_factors.get_friction_level_enum()
        
        # Guidance mode adjustment
        if trust_level == TrustLevel.HIGH and friction_level == FrictionLevel.LOW:
            self.guidance_mode = GuidanceMode.CONCISE.value
            self.explanation_depth = 1
            self.proactivity_score = 0.8
        elif trust_level == TrustLevel.LOW or friction_level in [FrictionLevel.HIGH, FrictionLevel.RESISTANCE]:
            self.guidance_mode = GuidanceMode.REASSURING.value
            self.explanation_depth = 4
            self.proactivity_score = 0.2
        else:
            self.guidance_mode = GuidanceMode.BALANCED.value
            self.explanation_depth = 2
            self.proactivity_score = 0.5
        
        # Recovery state management
        if self.friction_factors.friction_score > 0.3:
            if self.recovery_state != RecoveryState.RECOVERING.value:
                self.recovery_state = RecoveryState.RECOVERING.value
                self.recovery_started_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                self.recovery_progress = 0.0
        elif self.friction_factors.friction_score == 0.0 and self.trust_metrics.trust_score >= 0.6:
            self.recovery_state = RecoveryState.REESTABLISHED.value
            self.recovery_progress = 1.0
        else:
            self.recovery_state = RecoveryState.STABLE.value


# ============================================================================
# TRUST STATE MANAGER
# ============================================================================


class TrustStateManager:
    """Manager for relationship states and trust dynamics.
    
    Provides transparent, reversible trust management.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize trust state manager."""
        self.storage_path = storage_path or "/data/data/com.termux/files/home/.openclaw/workspace/weslr/trust_dynamics/"
        self.relationships: Dict[str, RelationshipState] = {}  # relationship_id -> State
        self._ensure_storage_exists()
        self._load_relationships()
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _load_relationships(self) -> None:
        """Load relationships from storage."""
        import os
        if not os.path.exists(self.storage_path):
            return
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith("_relationship.json"):
                relationship_id = filename[:-21]  # Remove _relationship.json
                try:
                    with open(os.path.join(self.storage_path, filename), "r") as f:
                        data = json.load(f)
                        self.relationships[relationship_id] = RelationshipState.from_dict(data)
                except Exception:
                    continue
    
    def _save_relationship(self, relationship_id: str) -> None:
        """Save a relationship to storage."""
        import os
        filepath = os.path.join(self.storage_path, f"{relationship_id}_relationship.json")
        data = self.relationships[relationship_id].to_dict()
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def create_relationship(self, relationship_id: str) -> RelationshipState:
        """Create a new relationship state."""
        state = RelationshipState(relationship_id=relationship_id)
        self.relationships[relationship_id] = state
        self._save_relationship(relationship_id)
        return state
    
    def get_relationship(self, relationship_id: str) -> Optional[RelationshipState]:
        """Get a relationship state by ID."""
        return self.relationships.get(relationship_id)
    
    def get_default_relationship(self) -> RelationshipState:
        """Get the default relationship state (create if needed)."""
        if "default" not in self.relationships:
            return self.create_relationship("default")
        return self.relationships["default"]
    
    def record_interaction(
        self,
        relationship_id: str,
        is_positive: bool,
        reason: Optional[str] = None,
    ) -> RelationshipState:
        """Record an interaction and update relationship state."""
        state = self.get_relationship(relationship_id)
        if not state:
            state = self.create_relationship(relationship_id)
        
        state.record_interaction(is_positive, reason)
        self._save_relationship(relationship_id)
        return state
    
    def record_positive_interaction(self, relationship_id: str, reason: Optional[str] = None) -> RelationshipState:
        """Convenience method to record a positive interaction."""
        return self.record_interaction(relationship_id, True, reason)
    
    def record_negative_interaction(self, relationship_id: str, reason: Optional[str] = None) -> RelationshipState:
        """Convenience method to record a negative interaction."""
        return self.record_interaction(relationship_id, False, reason)
    
    def get_all_relationships(self) -> Dict[str, RelationshipState]:
        """Get all relationship states."""
        return self.relationships
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manager state to dictionary."""
        return {
            "relationship_count": len(self.relationships),
            "relationships": {k: v.to_dict() for k, v in self.relationships.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_adaptive_guidance(guidance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add relationship context to adaptive guidance.
    
    This is purely additive — no migration required.
    """
    if "relationship_context" not in guidance_dict:
        guidance_dict["relationship_context"] = None
    if "guidance_mode" not in guidance_dict:
        guidance_dict["guidance_mode"] = GuidanceMode.BALANCED.value
    if "explanation_depth" not in guidance_dict:
        guidance_dict["explanation_depth"] = 2
    return guidance_dict


def integrate_with_outcome_feedback(feedback_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add relationship context to outcome feedback.
    
    This is purely additive — no migration required.
    """
    if "relationship_id" not in feedback_dict:
        feedback_dict["relationship_id"] = None
    if "trust_impact" not in feedback_dict:
        feedback_dict["trust_impact"] = None
    if "friction_impact" not in feedback_dict:
        feedback_dict["friction_impact"] = None
    return feedback_dict


def integrate_with_intervention_timing(timing_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add relationship context to intervention timing.
    
    This is purely additive — no migration required.
    """
    if "relationship_id" not in timing_dict:
        timing_dict["relationship_id"] = None
    if "caution_level" not in timing_dict:
        timing_dict["caution_level"] = "normal"  # normal, elevated, max
    if "proactive_readiness" not in timing_dict:
        timing_dict["proactive_readiness"] = 0.5
    return timing_dict


def integrate_with_compromise_explanation(explanation_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add relationship context to compromise explanation.
    
    This is purely additive — no migration required.
    """
    if "relationship_id" not in explanation_dict:
        explanation_dict["relationship_id"] = None
    if "explanation_burden" not in explanation_dict:
        explanation_dict["explanation_burden"] = "standard"  # minimal, standard, elevated, max
    return explanation_dict
