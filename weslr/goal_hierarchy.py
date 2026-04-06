# goal_hierarchy.py - v33: Goal Hierarchy / Priority Framework Layer
# Creates a governed goal/prioritization layer so WESLR can evaluate recommendations
# by alignment with user, household, domain, and long-term priorities.
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


class GoalScope(str, Enum):
    """Scope level for goals."""
    USER = "user"  # Individual user goals
    HOUSEHOLD = "household"  # Shared household goals
    DOMAIN = "domain"  # Domain-specific goals
    SYSTEM = "system"  # System-level goals


class GoalPriority(str, Enum):
    """Priority level for goals."""
    CRITICAL = "critical"  # Must be achieved
    HIGH = "high"  # Should be achieved soon
    MEDIUM = "medium"  # Nice to have
    LOW = "low"  # Optional


class GoalStatus(str, Enum):
    """Status of a goal."""
    PENDING = "pending"  # Not yet started
    IN_PROGRESS = "in_progress"  # Currently working on
    COMPLETED = "completed"  # Achieved
    ARCHIVED = "archived"  # No longer relevant
    ABANDONED = "abandoned"  # Given up on


class PriorityConflict(str, Enum):
    """Conflict resolution status for priorities."""
    NONE = "none"  # No conflict
    DETECTED = "detected"  # Conflict detected, awaiting resolution
    RESOLVED = "resolved"  # Conflict resolved
    ACKNOWLEDGED = "acknowledged"  # Conflict acknowledged but not resolved


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class Goal:
    """Represents a goal with priority, status, and alignment metadata."""
    
    goal_id: str  # Unique identifier
    title: str  # Human-readable title
    description: Optional[str] = None  # Detailed description
    
    # Categorization
    scope: str = GoalScope.USER.value  # user, household, domain, system
    priority: str = GoalPriority.MEDIUM.value  # critical, high, medium, low
    status: str = GoalStatus.PENDING.value  # pending, in_progress, completed, archived, abandoned
    
    # Timeline
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    target_completion: Optional[str] = None  # ISO-8601 timestamp
    actual_completion: Optional[str] = None  # ISO-8601 timestamp
    
    # Alignment metadata
    confidence: float = 0.5  # Confidence in goal validity (0.0-1.0)
    stability: float = 0.5  # Stability of goal priority (0.0-1.0)
    related_goals: List[str] = field(default_factory=list)  # Related goal IDs
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)  # Goal IDs this depends on
    blocking: List[str] = field(default_factory=list)  # Goal IDs this blocks
    
    # Metadata
    created_by: Optional[str] = None
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "goal_id": self.goal_id,
            "title": self.title,
            "description": self.description,
            "scope": self.scope,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "target_completion": self.target_completion,
            "actual_completion": self.actual_completion,
            "confidence": self.confidence,
            "stability": self.stability,
            "related_goals": self.related_goals,
            "depends_on": self.depends_on,
            "blocking": self.blocking,
            "created_by": self.created_by,
            "last_updated": self.last_updated,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Goal:
        """Create from dictionary representation."""
        data["related_goals"] = data.get("related_goals", [])
        data["depends_on"] = data.get("depends_on", [])
        data["blocking"] = data.get("blocking", [])
        return cls(**data)
    
    def is_urgent(self) -> bool:
        """Check if this goal should be prioritized urgently."""
        return self.status == GoalStatus.PENDING.value and self.priority in [
            GoalPriority.CRITICAL.value,
            GoalPriority.HIGH.value,
        ]
    
    def get_completion_rate(self) -> float:
        """Get estimated completion rate based on priority and status."""
        status_weights = {
            GoalStatus.PENDING.value: 0.0,
            GoalStatus.IN_PROGRESS.value: 0.5,
            GoalStatus.COMPLETED.value: 1.0,
            GoalStatus.ARCHIVED.value: 0.0,
            GoalStatus.ABANDONED.value: 0.0,
        }
        priority_weights = {
            GoalPriority.CRITICAL.value: 1.2,
            GoalPriority.HIGH.value: 1.1,
            GoalPriority.MEDIUM.value: 1.0,
            GoalPriority.LOW.value: 0.8,
        }
        return status_weights.get(self.status, 0.0) * priority_weights.get(self.priority, 1.0)
    
    def update_status(self, new_status: str) -> None:
        """Update goal status."""
        self.status = new_status
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        if new_status == GoalStatus.COMPLETED.value:
            self.actual_completion = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        elif new_status == GoalStatus.ABANDONED.value:
            self.actual_completion = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class GoalHierarchy:
    """Hierarchical structure of goals with priority relationships."""
    
    hierarchy_id: str  # Unique identifier
    title: Optional[str] = None  # Display title
    
    # Goal categories
    user_goals: Dict[str, Goal] = field(default_factory=dict)
    household_goals: Dict[str, Goal] = field(default_factory=dict)
    domain_goals: Dict[str, Goal] = field(default_factory=dict)
    system_goals: Dict[str, Goal] = field(default_factory=dict)
    
    # Conflict tracking
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Configuration
    enable_conflict_detection: bool = True
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "hierarchy_id": self.hierarchy_id,
            "title": self.title,
            "user_goals": {k: v.to_dict() for k, v in self.user_goals.items()},
            "household_goals": {k: v.to_dict() for k, v in self.household_goals.items()},
            "domain_goals": {k: v.to_dict() for k, v in self.domain_goals.items()},
            "system_goals": {k: v.to_dict() for k, v in self.system_goals.items()},
            "conflicts": self.conflicts,
            "enable_conflict_detection": self.enable_conflict_detection,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GoalHierarchy:
        """Create from dictionary representation."""
        user_data = data.get("user_goals", {})
        household_data = data.get("household_goals", {})
        domain_data = data.get("domain_goals", {})
        system_data = data.get("system_goals", {})
        conflicts_data = data.get("conflicts", [])
        
        user_goals = {k: Goal.from_dict(v) for k, v in user_data.items()}
        household_goals = {k: Goal.from_dict(v) for k, v in household_data.items()}
        domain_goals = {k: Goal.from_dict(v) for k, v in domain_data.items()}
        system_goals = {k: Goal.from_dict(v) for k, v in system_data.items()}
        
        return cls(
            hierarchy_id=data.get("hierarchy_id", ""),
            title=data.get("title"),
            user_goals=user_goals,
            household_goals=household_goals,
            domain_goals=domain_goals,
            system_goals=system_goals,
            conflicts=conflicts_data,
            enable_conflict_detection=data.get("enable_conflict_detection", True),
        )
    
    def add_goal(self, goal: Goal) -> None:
        """Add a goal to the hierarchy."""
        target_dict = getattr(self, f"{goal.scope}_goals")
        target_dict[goal.goal_id] = goal
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Get a goal by ID across all scopes."""
        for scope_dict in [self.user_goals, self.household_goals, self.domain_goals, self.system_goals]:
            if goal_id in scope_dict:
                return scope_dict[goal_id]
        return None
    
    def remove_goal(self, goal_id: str) -> bool:
        """Remove a goal by ID."""
        for scope_dict in [self.user_goals, self.household_goals, self.domain_goals, self.system_goals]:
            if goal_id in scope_dict:
                del scope_dict[goal_id]
                self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                return True
        return False
    
    def get_prioritized_goals(self, scope: Optional[str] = None) -> List[Goal]:
        """Get goals sorted by priority and urgency."""
        all_goals = []
        if scope:
            target_dict = getattr(self, f"{scope}_goals")
            all_goals = list(target_dict.values())
        else:
            all_goals = (
                list(self.user_goals.values()) +
                list(self.household_goals.values()) +
                list(self.domain_goals.values()) +
                list(self.system_goals.values())
            )
        
        # Sort by completion rate (descending), then priority order
        priority_order = {
            GoalPriority.CRITICAL.value: 0,
            GoalPriority.HIGH.value: 1,
            GoalPriority.MEDIUM.value: 2,
            GoalPriority.LOW.value: 3,
        }
        
        return sorted(
            all_goals,
            key=lambda g: (-g.get_completion_rate(), priority_order.get(g.priority, 2))
        )
    
    def detect_conflicts(self) -> List[Dict[str, Any]]:
        """Detect conflicts between goals."""
        if not self.enable_conflict_detection:
            return []
        
        conflicts = []
        
        # Check for conflicting priorities within the same scope
        for scope_dict in [self.user_goals, self.household_goals, self.domain_goals]:
            goals = list(scope_dict.values())
            for i, g1 in enumerate(goals):
                for g2 in goals[i+1:]:
                    if g1.priority in [GoalPriority.CRITICAL.value, GoalPriority.HIGH.value] and \
                       g2.priority in [GoalPriority.CRITICAL.value, GoalPriority.HIGH.value]:
                        # Same scope, both high priority - potential conflict
                        conflicts.append({
                            "type": "high_priority_same_scope",
                            "goal_1": g1.goal_id,
                            "goal_2": g2.goal_id,
                            "scope": g1.scope,
                            "status": PriorityConflict.DETECTED.value,
                        })
        
        # Check for dependency conflicts
        for goal in self.get_all_goals():
            for dep_id in goal.depends_on:
                dep_goal = self.get_goal(dep_id)
                if dep_goal and dep_goal.status == GoalStatus.ABANDONED.value:
                    conflicts.append({
                        "type": "abandoned_dependency",
                        "goal_id": goal.goal_id,
                        "dependency_id": dep_id,
                        "status": PriorityConflict.DETECTED.value,
                    })
        
        self.conflicts = conflicts
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        return conflicts
    
    def get_all_goals(self) -> List[Goal]:
        """Get all goals from all scopes."""
        return (
            list(self.user_goals.values()) +
            list(self.household_goals.values()) +
            list(self.domain_goals.values()) +
            list(self.system_goals.values())
        )


# ============================================================================
# GOAL HIERARCHY MANAGER
# ============================================================================


class GoalHierarchyManager:
    """Manager for goal hierarchy and priority framework.
    
    Provides add-only, persistent storage with transparency.
    All goals are user/operator reported and reversible.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize goal hierarchy manager."""
        self.storage_path = storage_path or self._get_default_path()
        self.hierarchies: Dict[str, GoalHierarchy] = {}  # hierarchy_id -> Hierarchy
        self._ensure_storage_exists()
        self._load_hierarchies()
    
    def _get_default_path(self) -> str:
        """Get default storage path."""
        return "/data/data/com.termux/files/home/.openclaw/workspace/weslr/goal_hierarchy/"
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _load_hierarchies(self) -> None:
        """Load hierarchies from storage."""
        import os
        if not os.path.exists(self.storage_path):
            return
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith("_hierarchy.json"):
                hierarchy_id = filename[:-15]  # Remove _hierarchy.json
                try:
                    with open(os.path.join(self.storage_path, filename), "r") as f:
                        data = json.load(f)
                        self.hierarchies[hierarchy_id] = GoalHierarchy.from_dict(data)
                except Exception:
                    # Skip malformed files
                    continue
    
    def _save_hierarchy(self, hierarchy_id: str) -> None:
        """Save a hierarchy to storage."""
        import os
        filepath = os.path.join(self.storage_path, f"{hierarchy_id}_hierarchy.json")
        data = self.hierarchies[hierarchy_id].to_dict()
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def create_hierarchy(self, hierarchy_id: str, title: Optional[str] = None) -> GoalHierarchy:
        """Create a new goal hierarchy."""
        hierarchy = GoalHierarchy(hierarchy_id=hierarchy_id, title=title)
        self.hierarchies[hierarchy_id] = hierarchy
        self._save_hierarchy(hierarchy_id)
        return hierarchy
    
    def get_hierarchy(self, hierarchy_id: str) -> Optional[GoalHierarchy]:
        """Get a hierarchy by ID."""
        return self.hierarchies.get(hierarchy_id)
    
    def add_goal(
        self,
        hierarchy_id: str,
        goal: Goal,
    ) -> bool:
        """Add a goal to a hierarchy."""
        hierarchy = self.get_hierarchy(hierarchy_id)
        if not hierarchy:
            return False
        
        hierarchy.add_goal(goal)
        self._save_hierarchy(hierarchy_id)
        return True
    
    def detect_conflicts(self, hierarchy_id: str) -> List[Dict[str, Any]]:
        """Detect conflicts in a hierarchy."""
        hierarchy = self.get_hierarchy(hierarchy_id)
        if not hierarchy:
            return []
        
        return hierarchy.detect_conflicts()
    
    def get_all_hierarchies(self) -> Dict[str, GoalHierarchy]:
        """Get all hierarchies."""
        return self.hierarchies
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manager state to dictionary."""
        return {
            "hierarchy_count": len(self.hierarchies),
            "hierarchies": {hid: h.to_dict() for hid, h in self.hierarchies.items()},
        }


# ============================================================================
# PRIORITY FRAMEWORK
# ============================================================================


class PriorityFramework:
    """Framework for evaluating recommendations against goal hierarchy.
    
    Provides alignment scoring and conflict detection.
    """
    
    def __init__(self, manager: GoalHierarchyManager):
        """Initialize priority framework."""
        self.manager = manager
    
    def evaluate_recommendation(
        self,
        hierarchy_id: str,
        recommendation_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate a recommendation against the goal hierarchy."""
        hierarchy = self.manager.get_hierarchy(hierarchy_id)
        if not hierarchy:
            return {
                "recommendation_id": recommendation_context.get("recommendation_id"),
                "alignment_score": 0.0,
                "conflict_count": 0,
                "recommendation": "No hierarchy available",
            }
        
        # Check for active conflicts
        conflicts = hierarchy.detect_conflicts()
        conflict_count = len([c for c in conflicts if c.get("status") == PriorityConflict.DETECTED.value])
        
        # Calculate alignment score based on goal priority and scope
        alignment_score = self._calculate_alignment_score(hierarchy, recommendation_context)
        
        # Check for conflicting priorities
        conflicting_goals = self._find_conflicting_goals(hierarchy, recommendation_context)
        
        return {
            "recommendation_id": recommendation_context.get("recommendation_id"),
            "hierarchy_id": hierarchy_id,
            "alignment_score": alignment_score,
            "conflict_count": conflict_count,
            "conflicting_goals": conflicting_goals,
            "recommendation": self._get_recommendation(alignment_score, conflict_count),
            "explanation": self._get_explanation(alignment_score, conflicting_goals),
        }
    
    def _calculate_alignment_score(self, hierarchy: GoalHierarchy, context: Dict[str, Any]) -> float:
        """Calculate alignment score for a recommendation."""
        # Base score from recommendation scope matching
        scope_score = 0.5  # Default neutral
        
        # Get scope from context or default
        recommendation_scope = context.get("scope", GoalScope.USER.value)
        
        if recommendation_scope == GoalScope.USER.value:
            # Check user goals
            active_user_goals = [g for g in hierarchy.user_goals.values() 
                                if g.status == GoalStatus.IN_PROGRESS.value]
            if active_user_goals:
                avg_priority = sum(GOAL_PRIORITY_WEIGHTS.get(g.priority, 0.5) 
                                  for g in active_user_goals) / len(active_user_goals)
                scope_score = avg_priority * 0.7 + 0.3
        elif recommendation_scope == GoalScope.HOUSEHOLD.value:
            # Check household goals
            active_household_goals = [g for g in hierarchy.household_goals.values() 
                                     if g.status == GoalStatus.IN_PROGRESS.value]
            if active_household_goals:
                avg_priority = sum(GOAL_PRIORITY_WEIGHTS.get(g.priority, 0.5) 
                                  for g in active_household_goals) / len(active_household_goals)
                scope_score = avg_priority * 0.7 + 0.3
        
        return min(1.0, max(0.0, scope_score))
    
    def _find_conflicting_goals(self, hierarchy: GoalHierarchy, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find goals that conflict with this recommendation."""
        conflicts = []
        recommendation_scope = context.get("scope", GoalScope.USER.value)
        
        # Check for conflicting high-priority goals
        all_goals = hierarchy.get_all_goals()
        for goal in all_goals:
            if goal.priority in [GoalPriority.CRITICAL.value, GoalPriority.HIGH.value]:
                if goal.scope == recommendation_scope:
                    conflicts.append({
                        "goal_id": goal.goal_id,
                        "title": goal.title,
                        "priority": goal.priority,
                        "conflict_type": "same_scope_high_priority",
                    })
        
        return conflicts
    
    def _get_recommendation(self, alignment_score: float, conflict_count: int) -> str:
        """Get recommendation based on evaluation."""
        if alignment_score >= 0.8 and conflict_count == 0:
            return "Strong alignment with goals - proceed with confidence"
        elif alignment_score >= 0.6 and conflict_count == 0:
            return "Moderate alignment - consider goals before proceeding"
        elif alignment_score >= 0.4 and conflict_count == 0:
            return "Some alignment - review goals for potential adjustments"
        elif alignment_score < 0.4 and conflict_count == 0:
            return "Low alignment - reconsider or clarify goals"
        elif conflict_count > 0:
            return f"Conflicts detected ({conflict_count}) - resolve before proceeding"
        return "Review goals for better alignment"
    
    def _get_explanation(self, alignment_score: float, conflicting_goals: List[Dict[str, Any]]) -> str:
        """Get explanation for alignment score."""
        if not conflicting_goals:
            if alignment_score >= 0.8:
                return "Recommendation aligns well with current goals"
            elif alignment_score >= 0.6:
                return "Recommendation has moderate alignment with current goals"
            else:
                return "Recommendation has low alignment with current goals"
        else:
            goal_titles = ", ".join([g.get("title", "unknown") for g in conflicting_goals])
            return f"Conflicts with high-priority goals: {goal_titles}"


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_adaptive_guidance(guidance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add goal hierarchy context to adaptive guidance.
    
    This is purely additive — no migration required.
    """
    if "goal_alignment" not in guidance_dict:
        guidance_dict["goal_alignment"] = None
    if "conflict_with_goals" not in guidance_dict:
        guidance_dict["conflict_with_goals"] = False
    if "recommendation_scope" not in guidance_dict:
        guidance_dict["recommendation_scope"] = GoalScope.USER.value
    return guidance_dict


def integrate_with_outcome_feedback(feedback_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add goal hierarchy context to outcome feedback.
    
    This is purely additive — no migration required.
    """
    if "goal_alignment" not in feedback_dict:
        feedback_dict["goal_alignment"] = None
    if "goal_conflicts" not in feedback_dict:
        feedback_dict["goal_conflicts"] = []
    return feedback_dict


def integrate_with_operator_context(context_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add goal hierarchy awareness to operator context.
    
    This is purely additive — no migration required.
    """
    if "goal_hierarchy_available" not in context_dict:
        context_dict["goal_hierarchy_available"] = False
    if "active_conflicts" not in context_dict:
        context_dict["active_conflicts"] = []
    if "top_priorities" not in context_dict:
        context_dict["top_priorities"] = []
    return context_dict


# ============================================================================
# CONSTANTS
# ============================================================================

GOAL_PRIORITY_WEIGHTS = {
    GoalPriority.CRITICAL.value: 1.0,
    GoalPriority.HIGH.value: 0.8,
    GoalPriority.MEDIUM.value: 0.5,
    GoalPriority.LOW.value: 0.2,
}
