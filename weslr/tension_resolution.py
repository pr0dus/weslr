# tension_resolution.py - v34: Tension / Tradeoff Resolution Layer
# Creates a governed layer that identifies and resolves conflicts between goals,
# domains, safety constraints, household context, and user preferences.
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


class TensionType(str, Enum):
    """Types of tensions that can arise."""
    GOAL_CONFLICT = "goal_conflict"  # Goals conflict with each other
    PRIORITY_CONFLICT = "priority_conflict"  # Priorities conflict
    SAFETY_PREFERENCE = "safety_preference"  # Safety vs preference tension
    HOUSEHOLD_INDIVIDUAL = "household_individual"  # Household vs individual tension
    SHORT_LONG_TERM = "short_long_term"  # Short-term vs long-term tension
    CONTEXT_CONFLICT = "context_conflict"  # Context domains conflict


class ResolutionStrategy(str, Enum):
    """Strategy for resolving tension."""
    NONE = "none"  # No resolution applied
    COMPROMISE = "compromise"  # Find middle ground
    PRIORITY_OVERRIDE = "priority_override"  # Override lower priority
    DEFER = "defer"  # Defer to later
    REJECT = "reject"  # Reject one option
    SYNTHESIZE = "synthesize"  # Create new synthesized option


class SeverityLevel(str, Enum):
    """Severity level of tension."""
    LOW = "low"  # Minor tension
    MEDIUM = "medium"  # Moderate tension
    HIGH = "high"  # Significant tension
    CRITICAL = "critical"  # Must be resolved


class HoldBackCondition(str, Enum):
    """Condition for hold-back behavior."""
    NONE = "none"  # No hold-back
    TENSION_UNRESOLVED = "tension_unresolved"  # Tension unresolved
    SAFETY_RISK = "safety_risk"  # Potential safety risk
    CONFLICT_ACTIVE = "conflict_active"  # Active conflict


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class Tension:
    """Represents a tension between competing factors."""
    
    tension_id: str  # Unique identifier
    tension_type: str  # Type of tension
    description: str  # Human-readable description
    
    # Involved factors
    factor_a: str  # First factor
    factor_b: str  # Second factor
    factor_a_type: str = "factor"  # Type of factor A
    factor_b_type: str = "factor"  # Type of factor B
    
    # Severity
    severity: str = SeverityLevel.LOW.value
    confidence: float = 0.5  # Confidence in tension detection
    
    # Resolution
    resolution_strategy: Optional[str] = None  # Applied strategy
    resolution_details: Optional[str] = None  # Resolution details
    
    # Timestamps
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    resolved_at: Optional[str] = None  # ISO-8601 timestamp
    
    # Metadata
    detected_by: str = "system"  # "system", "user", "operator"
    priority_reference: Optional[str] = None  # Reference to priority framework
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "tension_id": self.tension_id,
            "tension_type": self.tension_type,
            "description": self.description,
            "factor_a": self.factor_a,
            "factor_b": self.factor_b,
            "factor_a_type": self.factor_a_type,
            "factor_b_type": self.factor_b_type,
            "severity": self.severity,
            "confidence": self.confidence,
            "resolution_strategy": self.resolution_strategy,
            "resolution_details": self.resolution_details,
            "detected_at": self.detected_at,
            "resolved_at": self.resolved_at,
            "detected_by": self.detected_by,
            "priority_reference": self.priority_reference,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Tension:
        """Create from dictionary representation."""
        return cls(**data)
    
    def is_resolved(self) -> bool:
        """Check if this tension has been resolved."""
        return self.resolution_strategy is not None
    
    def apply_resolution(self, strategy: str, details: Optional[str] = None) -> None:
        """Apply a resolution strategy to this tension."""
        self.resolution_strategy = strategy
        self.resolution_details = details
        self.resolved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class TensionSet:
    """Set of tensions related to a recommendation or decision."""
    
    tension_set_id: str  # Unique identifier
    recommendation_id: str  # ID of recommendation this set relates to
    
    # Tensions
    tensions: List[Tension] = field(default_factory=list)
    
    # Resolution status
    has_unresolved: bool = False
    highest_severity: str = SeverityLevel.LOW.value
    
    # Configuration
    enable_hold_back: bool = True  # Enable hold-back when tensions unresolved
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "tension_set_id": self.tension_set_id,
            "recommendation_id": self.recommendation_id,
            "tensions": [t.to_dict() for t in self.tensions],
            "has_unresolved": self.has_unresolved,
            "highest_severity": self.highest_severity,
            "enable_hold_back": self.enable_hold_back,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TensionSet:
        """Create from dictionary representation."""
        tensions_data = data.get("tensions", [])
        tensions = [Tension.from_dict(t) for t in tensions_data]
        
        return cls(
            tension_set_id=data.get("tension_set_id", ""),
            recommendation_id=data.get("recommendation_id", ""),
            tensions=tensions,
            has_unresolved=data.get("has_unresolved", False),
            highest_severity=data.get("highest_severity", SeverityLevel.LOW.value),
            enable_hold_back=data.get("enable_hold_back", True),
        )
    
    def add_tension(self, tension: Tension) -> None:
        """Add a tension to the set."""
        self.tensions.append(tension)
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Update resolution status
        self.has_unresolved = any(not t.is_resolved() for t in self.tensions)
        
        # Update highest severity
        severity_order = [
            SeverityLevel.LOW.value,
            SeverityLevel.MEDIUM.value,
            SeverityLevel.HIGH.value,
            SeverityLevel.CRITICAL.value,
        ]
        for t in self.tensions:
            if t.severity in severity_order:
                idx = severity_order.index(t.severity)
                if severity_order.index(self.highest_severity) < idx:
                    self.highest_severity = t.severity
    
    def get_unresolved_tensions(self) -> List[Tension]:
        """Get tensions that are not yet resolved."""
        return [t for t in self.tensions if not t.is_resolved()]
    
    def get_hold_back_conditions(self) -> List[str]:
        """Get active hold-back conditions."""
        if not self.enable_hold_back:
            return []
        
        conditions = []
        unresolved = self.get_unresolved_tensions()
        
        if unresolved:
            conditions.append(HoldBackCondition.TENSION_UNRESOLVED.value)
        
        # Check for safety-related tensions
        for tension in unresolved:
            if tension.tension_type in [
                TensionType.SAFETY_PREFERENCE.value,
                TensionType.CONTEXT_CONFLICT.value,
            ]:
                if tension.severity in [SeverityLevel.HIGH.value, SeverityLevel.CRITICAL.value]:
                    conditions.append(HoldBackCondition.SAFETY_RISK.value)
                    break
        
        # Check for active conflicts
        for tension in unresolved:
            if tension.tension_type in [
                TensionType.GOAL_CONFLICT.value,
                TensionType.HOUSEHOLD_INDIVIDUAL.value,
            ]:
                conditions.append(HoldBackCondition.CONFLICT_ACTIVE.value)
                break
        
        return conditions


# ============================================================================
# TENSION RESOLUTION ENGINE
# ============================================================================


class TensionResolutionEngine:
    """Engine for detecting, analyzing, and resolving tensions.
    
    Provides transparent, reversible tension management.
    """
    
    def __init__(self):
        """Initialize tension resolution engine."""
        self.tension_sets: Dict[str, TensionSet] = {}  # tension_set_id -> Set
        self.tensions: Dict[str, Tension] = {}  # tension_id -> Tension
        self.resolution_history: List[Dict[str, Any]] = []
    
    def detect_tension(
        self,
        recommendation_id: str,
        tension_type: str,
        factor_a: str,
        factor_b: str,
        factor_a_type: str = "factor",
        factor_b_type: str = "factor",
        description: str = "",
        severity: str = SeverityLevel.LOW.value,
        confidence: float = 0.5,
        detected_by: str = "system",
    ) -> Tension:
        """Detect a tension in recommendation context."""
        tension_id = f"tension-{len(self.tensions) + 1:04d}"
        
        tension = Tension(
            tension_id=tension_id,
            tension_type=tension_type,
            factor_a=factor_a,
            factor_b=factor_b,
            factor_a_type=factor_a_type,
            factor_b_type=factor_b_type,
            description=description,
            severity=severity,
            confidence=confidence,
            detected_by=detected_by,
        )
        
        self.tensions[tension_id] = tension
        return tension
    
    def create_tension_set(
        self,
        recommendation_id: str,
    ) -> TensionSet:
        """Create a tension set for a recommendation."""
        tension_set_id = f"set-{len(self.tension_sets) + 1:04d}"
        
        tension_set = TensionSet(
            tension_set_id=tension_set_id,
            recommendation_id=recommendation_id,
        )
        
        self.tension_sets[tension_set_id] = tension_set
        return tension_set
    
    def add_tension_to_set(self, tension_set_id: str, tension: Tension) -> None:
        """Add a tension to a tension set."""
        tension_set = self.tension_sets.get(tension_set_id)
        if not tension_set:
            return
        
        tension_set.add_tension(tension)
        self._update_tension_set_status(tension_set)
    
    def _update_tension_set_status(self, tension_set: TensionSet) -> None:
        """Update tension set status from contained tensions."""
        unresolved = tension_set.get_unresolved_tensions()
        tension_set.has_unresolved = len(unresolved) > 0
        
        severity_order = [
            SeverityLevel.LOW.value,
            SeverityLevel.MEDIUM.value,
            SeverityLevel.HIGH.value,
            SeverityLevel.CRITICAL.value,
        ]
        highest_idx = 0
        for tension in tension_set.tensions:
            if tension.severity in severity_order:
                idx = severity_order.index(tension.severity)
                if idx > highest_idx:
                    highest_idx = idx
        tension_set.highest_severity = severity_order[highest_idx]
    
    def apply_resolution(self, tension_set_id: str, tension_id: str, strategy: str, details: Optional[str] = None) -> bool:
        """Apply a resolution strategy to a tension."""
        tension = self.tensions.get(tension_id)
        if not tension:
            return False
        
        tension.apply_resolution(strategy, details)
        
        # Update tension set status
        for ts in self.tension_sets.values():
            if any(t.tension_id == tension_id for t in ts.tensions):
                self._update_tension_set_status(ts)
                break
        
        # Record in history
        self.resolution_history.append({
            "tension_id": tension_id,
            "resolution": strategy,
            "details": details or "Applied resolution",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        })
        
        return True
    
    def get_tension_set(self, tension_set_id: str) -> Optional[TensionSet]:
        """Get a tension set by ID."""
        return self.tension_sets.get(tension_set_id)
    
    def get_hold_back_status(self, tension_set_id: str) -> Dict[str, Any]:
        """Get hold-back status for a tension set."""
        tension_set = self.get_tension_set(tension_set_id)
        if not tension_set:
            return {
                "hold_back": False,
                "conditions": [],
                "recommendation": "No tension set available",
            }
        
        conditions = tension_set.get_hold_back_conditions()
        hold_back = len(conditions) > 0
        
        return {
            "hold_back": hold_back,
            "conditions": conditions,
            "recommendation": self._get_hold_back_recommendation(conditions),
        }
    
    def _get_hold_back_recommendation(self, conditions: List[str]) -> str:
        """Get recommendation based on hold-back conditions."""
        if not conditions:
            return "No hold-back conditions active"
        
        if HoldBackCondition.TENSION_UNRESOLVED.value in conditions:
            return "Unresolved tensions detected - defer recommendation"
        
        if HoldBackCondition.SAFETY_RISK.value in conditions:
            return "Safety risk detected - prioritize safety over preference"
        
        if HoldBackCondition.CONFLICT_ACTIVE.value in conditions:
            return "Active conflict detected - resolve before proceeding"
        
        return "Review tensions before proceeding"
    
    def synthesize_compromise(
        self,
        factor_a: str,
        factor_b: str,
        strategy: str,
    ) -> Dict[str, Any]:
        """Synthesize a compromise between conflicting factors."""
        return {
            "compromise": f"Compromise between {factor_a} and {factor_b}",
            "strategy": strategy,
            "suggestion": f"Consider {strategy} approach to balance both factors",
        }


# ============================================================================
# TENSION RESOLVER
# ============================================================================


class TensionResolver:
    """Resolver for specific tension types.
    
    Provides resolution strategies for different tension types.
    """
    
    def __init__(self, engine: TensionResolutionEngine):
        """Initialize tension resolver."""
        self.engine = engine
    
    def resolve_goal_conflict(
        self,
        tension: Tension,
        priority_a: float,
        priority_b: float,
    ) -> Dict[str, Any]:
        """Resolve a goal conflict."""
        if priority_a > priority_b * 1.2:
            strategy = ResolutionStrategy.PRIORITY_OVERRIDE.value
            details = f"Prioritizing {tension.factor_a} (higher priority)"
        elif priority_b > priority_a * 1.2:
            strategy = ResolutionStrategy.PRIORITY_OVERRIDE.value
            details = f"Prioritizing {tension.factor_b} (higher priority)"
        else:
            strategy = ResolutionStrategy.COMPROMISE.value
            details = f"Finding compromise between {tension.factor_a} and {tension.factor_b}"
        
        self.engine.apply_resolution(
            tension.tension_id,
            strategy,
            details,
        )
        
        return {
            "strategy": strategy,
            "details": details,
            "tension_id": tension.tension_id,
        }
    
    def resolve_safety_preference(
        self,
        tension: Tension,
        safety_risk: float,
        preference_strength: float,
    ) -> Dict[str, Any]:
        """Resolve a safety vs preference tension."""
        if safety_risk >= 0.6:
            strategy = ResolutionStrategy.REJECT.value
            details = f"Safety risk ({safety_risk:.1f}) overrides preference"
        else:
            strategy = ResolutionStrategy.DEFER.value
            details = f"Deferring to address safety concerns first"
        
        self.engine.apply_resolution(
            tension.tension_id,
            strategy,
            details,
        )
        
        return {
            "strategy": strategy,
            "details": details,
            "tension_id": tension.tension_id,
        }
    
    def resolve_short_long_term(
        self,
        tension: Tension,
        short_term_benefit: float,
        long_term_impact: float,
    ) -> Dict[str, Any]:
        """Resolve a short-term vs long-term tension."""
        # If long-term impact is significant, defer short-term
        if long_term_impact >= 0.7:
            strategy = ResolutionStrategy.DEFER.value
            details = "Prioritizing long-term impact over short-term benefit"
        else:
            strategy = ResolutionStrategy.COMPROMISE.value
            details = "Balancing short-term benefit with long-term impact"
        
        self.engine.apply_resolution(
            tension.tension_id,
            strategy,
            details,
        )
        
        return {
            "strategy": strategy,
            "details": details,
            "tension_id": tension.tension_id,
        }
    
    def resolve_household_individual(
        self,
        tension: Tension,
        household_benefit: float,
        individual_benefit: float,
        household_priority: float,
    ) -> Dict[str, Any]:
        """Resolve a household vs individual tension."""
        if household_priority >= 0.7:
            strategy = ResolutionStrategy.PRIORITY_OVERRIDE.value
            details = "Prioritizing household benefit"
        else:
            strategy = ResolutionStrategy.COMPROMISE.value
            details = "Balancing household and individual benefits"
        
        self.engine.apply_resolution(
            tension.tension_id,
            strategy,
            details,
        )
        
        return {
            "strategy": strategy,
            "details": details,
            "tension_id": tension.tension_id,
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_goal_hierarchy(hierarchy_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add tension resolution context to goal hierarchy.
    
    This is purely additive — no migration required.
    """
    if "active_tensions" not in hierarchy_dict:
        hierarchy_dict["active_tensions"] = []
    if "tension_resolver_available" not in hierarchy_dict:
        hierarchy_dict["tension_resolver_available"] = True
    return hierarchy_dict


def integrate_with_adaptive_guidance(guidance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add tension resolution context to adaptive guidance.
    
    This is purely additive — no migration required.
    """
    if "tension_resolved" not in guidance_dict:
        guidance_dict["tension_resolved"] = False
    if "tension_hold_back" not in guidance_dict:
        guidance_dict["tension_hold_back"] = False
    if "resolution_strategy" not in guidance_dict:
        guidance_dict["resolution_strategy"] = None
    return guidance_dict


def integrate_with_operator_context(context_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add tension resolution awareness to operator context.
    
    This is purely additive — no migration required.
    """
    if "tensions_detected" not in context_dict:
        context_dict["tensions_detected"] = []
    if "hold_back_active" not in context_dict:
        context_dict["hold_back_active"] = False
    if "resolved_tensions" not in context_dict:
        context_dict["resolved_tensions"] = []
    return context_dict


def integrate_with_outcome_feedback(feedback_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add tension resolution context to outcome feedback.
    
    This is purely additive — no migration required.
    """
    if "tension_context" not in feedback_dict:
        feedback_dict["tension_context"] = None
    if "resolution_applied" not in feedback_dict:
        feedback_dict["resolution_applied"] = False
    return feedback_dict
