# household_context.py - v29: Household / Multi-Person Context Layer
# Creates a governed multi-person context layer so WESLR can reason about
# shared household or family situations without collapsing privacy boundaries.
# Additive only, transparent, permission-aware, suggestion-based, non-manipulative, reversible.
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


class RecommendationScope(str, Enum):
    """Scope level for recommendations."""
    INDIVIDUAL = "individual"  # For one person only
    SHARED = "shared"  # For all household members
    HOUSEHOLD = "household"  # Explicit household-level recommendation


class PersonRole(str, Enum):
    """Household member roles."""
    ADULT = "adult"
    CHILD = "child"
    GUEST = "guest"
    VISITOR = "visitor"
    PET = "pet"  # For pet-related context
    OTHER = "other"


class VisibilityPermission(str, Enum):
    """Permissions for what data can be shared."""
    PRIVATE = "private"  # Only visible to person
    FAMILY = "family"  # Visible to family members
    HOUSEHOLD = "household"  # Visible to all in household
    SHARED = "shared"  # Explicitly shared with specific people


class ConflictStatus(str, Enum):
    """Status for potential conflicts in shared contexts."""
    NONE = "none"  # No conflict detected
    LOW = "low"  # Minor potential conflict
    MEDIUM = "medium"  # Moderate potential conflict
    HIGH = "high"  # Significant potential conflict
    ACTIVE = "active"  # Current active conflict


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class HouseholdMember:
    """Represents a household member with their context."""
    
    person_id: str  # Unique identifier for this person
    name: Optional[str] = None  # Display name
    role: str = PersonRole.ADULT.value  # Member's role
    visibility_permission: str = VisibilityPermission.PRIVATE.value  # Default permission
    
    # Profile attributes
    communication_style: str = "concise"  # concise, detailed, analytical, narrative
    domain_familiarity: str = "intermediate"  # beginner, intermediate, advanced, expert
    
    # Privacy settings
    share_routines: bool = False  # Whether routine data can be shared
    share_goals: bool = False  # Whether goals can be shared
    share_state: bool = False  # Whether current state can be shared
    
    # Metadata
    added_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "person_id": self.person_id,
            "name": self.name,
            "role": self.role,
            "visibility_permission": self.visibility_permission,
            "communication_style": self.communication_style,
            "domain_familiarity": self.domain_familiarity,
            "share_routines": self.share_routines,
            "share_goals": self.share_goals,
            "share_state": self.share_state,
            "added_at": self.added_at,
            "last_updated": self.last_updated,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HouseholdMember:
        """Create from dictionary representation."""
        return cls(**data)
    
    def can_share_routines(self) -> bool:
        """Check if this person has agreed to share routines."""
        return self.share_routines and self.visibility_permission in [
            VisibilityPermission.FAMILY.value,
            VisibilityPermission.HOUSEHOLD.value,
            VisibilityPermission.SHARED.value,
        ]
    
    def can_share_goals(self) -> bool:
        """Check if this person has agreed to share goals."""
        return self.share_goals and self.visibility_permission in [
            VisibilityPermission.FAMILY.value,
            VisibilityPermission.HOUSEHOLD.value,
            VisibilityPermission.SHARED.value,
        ]
    
    def get_shared_scope(self) -> List[str]:
        """Get list of scopes this person can see."""
        scopes = ["individual"]
        if self.can_share_routines():
            scopes.append("shared_routines")
        if self.can_share_goals():
            scopes.append("shared_goals")
        if self.visibility_permission in [
            VisibilityPermission.HOUSEHOLD.value,
            VisibilityPermission.SHARED.value,
        ]:
            scopes.append("household")
        return scopes


@dataclass
class SharedContext:
    """Context that is shared among household members."""
    
    context_id: str  # Unique identifier for shared context
    context_type: str  # e.g., "routine", "goal", "task", "event"
    scope: str = RecommendationScope.HOUSEHOLD.value  # Scope level
    
    # Content
    title: Optional[str] = None
    description: Optional[str] = None
    members_involved: List[str] = field(default_factory=list)  # person_ids involved
    
    # Permissions and constraints
    visibility_permission: str = VisibilityPermission.HOUSEHOLD.value
    can_view: List[str] = field(default_factory=list)  # person_ids who can view
    can_edit: List[str] = field(default_factory=list)  # person_ids who can edit
    
    # Conflict awareness
    conflict_status: str = ConflictStatus.NONE.value
    conflict_notes: Optional[str] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    created_by: Optional[str] = None
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    last_updated_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "context_id": self.context_id,
            "context_type": self.context_type,
            "scope": self.scope,
            "title": self.title,
            "description": self.description,
            "members_involved": self.members_involved,
            "visibility_permission": self.visibility_permission,
            "can_view": self.can_view,
            "can_edit": self.can_edit,
            "conflict_status": self.conflict_status,
            "conflict_notes": self.conflict_notes,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "last_updated": self.last_updated,
            "last_updated_by": self.last_updated_by,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SharedContext:
        """Create from dictionary representation."""
        data["members_involved"] = data.get("members_involved", [])
        data["can_view"] = data.get("can_view", [])
        data["can_edit"] = data.get("can_edit", [])
        return cls(**data)
    
    def get_member_count(self) -> int:
        """Get number of members involved in this context."""
        return len(self.members_involved)
    
    def is_household_scope(self) -> bool:
        """Check if this context is at household level."""
        return self.scope == RecommendationScope.HOUSEHOLD.value
    
    def should_hold_back_for_conflict(self) -> bool:
        """Check if recommendations should be held back due to conflict."""
        return self.conflict_status in [ConflictStatus.MEDIUM.value, ConflictStatus.HIGH.value, ConflictStatus.ACTIVE.value]


@dataclass
class HouseholdContext:
    """Complete household context including members and shared contexts."""
    
    household_id: str  # Unique identifier for this household
    name: Optional[str] = None  # Display name
    
    # Members
    members: Dict[str, HouseholdMember] = field(default_factory=dict)  # person_id -> Member
    
    # Shared contexts
    shared_contexts: Dict[str, SharedContext] = field(default_factory=dict)  # context_id -> Context
    
    # Configuration
    enable_shared_contexts: bool = True
    enable_conflict_detection: bool = True
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "household_id": self.household_id,
            "name": self.name,
            "members": {k: v.to_dict() for k, v in self.members.items()},
            "shared_contexts": {k: v.to_dict() for k, v in self.shared_contexts.items()},
            "enable_shared_contexts": self.enable_shared_contexts,
            "enable_conflict_detection": self.enable_conflict_detection,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HouseholdContext:
        """Create from dictionary representation."""
        members_data = data.get("members", {})
        shared_data = data.get("shared_contexts", {})
        
        members = {k: HouseholdMember.from_dict(v) for k, v in members_data.items()}
        shared_contexts = {k: SharedContext.from_dict(v) for k, v in shared_data.items()}
        
        return cls(
            household_id=data.get("household_id", ""),
            name=data.get("name"),
            members=members,
            shared_contexts=shared_contexts,
            enable_shared_contexts=data.get("enable_shared_contexts", True),
            enable_conflict_detection=data.get("enable_conflict_detection", True),
        )
    
    def get_member(self, person_id: str) -> Optional[HouseholdMember]:
        """Get a member by ID."""
        return self.members.get(person_id)
    
    def add_member(self, member: HouseholdMember) -> None:
        """Add a member to the household."""
        self.members[member.person_id] = member
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def remove_member(self, person_id: str) -> bool:
        """Remove a member by ID."""
        if person_id in self.members:
            del self.members[person_id]
            self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            return True
        return False
    
    def get_shared_contexts_for_member(self, person_id: str) -> List[SharedContext]:
        """Get shared contexts that a member can see."""
        if not self.enable_shared_contexts:
            return []
        
        member = self.get_member(person_id)
        if not member:
            return []
        
        visible_scopes = member.get_shared_scope()
        
        return [
            ctx for ctx in self.shared_contexts.values()
            if ctx.context_id not in visible_scopes or
               (ctx.visibility_permission in visible_scopes and
                person_id in ctx.can_view)
        ]
    
    def create_shared_context(
        self,
        context_type: str,
        members_involved: List[str],
        visibility_permission: str = VisibilityPermission.HOUSEHOLD.value,
    ) -> SharedContext:
        """Create a new shared context."""
        context_id = f"shared_{context_type}_{len(self.shared_contexts) + 1}"
        
        context = SharedContext(
            context_id=context_id,
            context_type=context_type,
            scope=RecommendationScope.HOUSEHOLD.value,
            members_involved=members_involved,
            visibility_permission=visibility_permission,
            can_view=members_involved.copy(),
            can_edit=members_involved.copy(),
        )
        
        self.shared_contexts[context_id] = context
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        return context
    
    def update_conflict_status(
        self,
        context_id: str,
        conflict_status: str,
        notes: Optional[str] = None,
    ) -> bool:
        """Update conflict status for a shared context."""
        if context_id not in self.shared_contexts:
            return False
        
        context = self.shared_contexts[context_id]
        context.conflict_status = conflict_status
        context.conflict_notes = notes
        context.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return True


# ============================================================================
# HOUSEHOLD CONTEXT MANAGER
# ============================================================================


class HouseholdContextManager:
    """Manager for household context and shared contexts.
    
    Provides add-only, persistent storage with transparency.
    All shared contexts are permission-aware and reversible.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize household context manager."""
        self.storage_path = storage_path or self._get_default_path()
        self.households: Dict[str, HouseholdContext] = {}  # household_id -> Context
        self._ensure_storage_exists()
        self._load_households()
    
    def _get_default_path(self) -> str:
        """Get default storage path."""
        return "/data/data/com.termux/files/home/.openclaw/workspace/weslr/household_context/"
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _load_households(self) -> None:
        """Load households from storage."""
        import os
        if not os.path.exists(self.storage_path):
            return
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith(".json"):
                household_id = filename[:-5]  # Remove .json extension
                try:
                    with open(os.path.join(self.storage_path, filename), "r") as f:
                        data = json.load(f)
                        self.households[household_id] = HouseholdContext.from_dict(data)
                except Exception:
                    # Skip malformed files
                    continue
    
    def _save_household(self, household_id: str) -> None:
        """Save a household to storage."""
        if household_id not in self.households:
            return
        
        import os
        filepath = os.path.join(self.storage_path, f"{household_id}.json")
        data = self.households[household_id].to_dict()
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def create_household(self, household_id: str, name: Optional[str] = None) -> HouseholdContext:
        """Create a new household."""
        household = HouseholdContext(
            household_id=household_id,
            name=name,
        )
        self.households[household_id] = household
        self._save_household(household_id)
        return household
    
    def get_household(self, household_id: str) -> Optional[HouseholdContext]:
        """Get a household by ID."""
        return self.households.get(household_id)
    
    def add_member_to_household(
        self,
        household_id: str,
        person_id: str,
        name: Optional[str] = None,
        role: str = PersonRole.ADULT.value,
    ) -> Optional[HouseholdMember]:
        """Add a member to a household."""
        household = self.get_household(household_id)
        if not household:
            return None
        
        member = HouseholdMember(
            person_id=person_id,
            name=name,
            role=role,
        )
        household.add_member(member)
        self._save_household(household_id)
        return member
    
    def get_member(self, household_id: str, person_id: str) -> Optional[HouseholdMember]:
        """Get a member from a household."""
        household = self.get_household(household_id)
        if not household:
            return None
        return household.get_member(person_id)
    
    def create_shared_context(
        self,
        household_id: str,
        context_type: str,
        members_involved: List[str],
        visibility_permission: str = VisibilityPermission.HOUSEHOLD.value,
    ) -> Optional[SharedContext]:
        """Create a shared context in a household."""
        household = self.get_household(household_id)
        if not household:
            return None
        return household.create_shared_context(
            context_type=context_type,
            members_involved=members_involved,
            visibility_permission=visibility_permission,
        )
    
    def update_conflict_status(
        self,
        household_id: str,
        context_id: str,
        conflict_status: str,
        notes: Optional[str] = None,
    ) -> bool:
        """Update conflict status for a shared context."""
        household = self.get_household(household_id)
        if not household:
            return False
        return household.update_conflict_status(context_id, conflict_status, notes)
    
    def get_all_households(self) -> Dict[str, HouseholdContext]:
        """Get all households."""
        return self.households
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manager state to dictionary."""
        return {
            "household_count": len(self.households),
            "households": {
                hid: h.to_dict() for hid, h in self.households.items()
            },
        }


# ============================================================================
# CONFLICT DETECTOR
# ============================================================================


class HouseholdConflictDetector:
    """Detect and manage potential conflicts in shared household contexts.
    
    Analyzes patterns and contexts to identify potential conflicts and
    provide recommendations for conflict resolution.
    """
    
    def __init__(self, manager: HouseholdContextManager):
        """Initialize conflict detector."""
        self.manager = manager
    
    def detect_conflict(
        self,
        household_id: str,
        context_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Detect conflict status for a shared context."""
        household = self.manager.get_household(household_id)
        if not household:
            return None
        
        context = household.shared_contexts.get(context_id)
        if not context:
            return None
        
        # Analyze context for potential conflicts
        member_count = context.get_member_count()
        
        # Simple conflict detection rules
        if member_count <= 1:
            return None  # No conflict with single member
        
        # Check for conflicting states (placeholder logic)
        conflict_status = ConflictStatus.NONE.value
        conflict_notes = None
        
        # Could check for:
        # - Time-based conflicts (e.g., shared device usage at same time)
        # - Goal-based conflicts (e.g., conflicting schedules)
        # - Resource conflicts (e.g., shared spaces)
        
        # For now, use member count as a simple indicator
        if member_count >= 6:
            conflict_status = ConflictStatus.HIGH.value
            conflict_notes = "High member count may increase complexity"
        elif member_count >= 4:
            conflict_status = ConflictStatus.MEDIUM.value
            conflict_notes = "Moderate member count - monitor for conflicts"
        elif member_count >= 2:
            conflict_status = ConflictStatus.LOW.value
            conflict_notes = "Small group - monitor for alignment"
        
        return {
            "context_id": context_id,
            "household_id": household_id,
            "detected_conflict_status": conflict_status,
            "member_count": member_count,
            "conflict_notes": conflict_notes,
            "recommendation": self._get_recommendation(conflict_status),
        }
    
    def _get_recommendation(self, conflict_status: str) -> Optional[str]:
        """Get recommendation based on conflict status."""
        if conflict_status == ConflictStatus.NONE.value:
            return None
        elif conflict_status == ConflictStatus.LOW.value:
            return "Consider checking in with members about shared context"
        elif conflict_status == ConflictStatus.MEDIUM.value:
            return "Reach out to members to discuss shared context alignment"
        elif conflict_status == ConflictStatus.HIGH.value:
            return "Schedule a discussion to address shared context conflicts"
        elif conflict_status == ConflictStatus.ACTIVE.value:
            return "Urgent: Schedule conflict resolution discussion"
        return None
    
    def auto_detect_household_conflicts(self, household_id: str) -> List[Dict[str, Any]]:
        """Auto-detect conflicts across all shared contexts in a household."""
        household = self.manager.get_household(household_id)
        if not household:
            return []
        
        results = []
        for context_id in household.shared_contexts:
            result = self.detect_conflict(household_id, context_id)
            if result:
                results.append(result)
        
        return results


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_profile(profile_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add household context integration to user profile.
    
    This is purely additive — no migration required.
    """
    if "household_id" not in profile_dict:
        profile_dict["household_id"] = None
    if "household_role" not in profile_dict:
        profile_dict["household_role"] = None
    if "share_with_household" not in profile_dict:
        profile_dict["share_with_household"] = False
    return profile_dict


def integrate_with_longitudinal_patterns(patterns_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add household context to longitudinal pattern analysis.
    
    This is purely additive — no migration required.
    """
    if "household_context" not in patterns_dict:
        patterns_dict["household_context"] = None
    if "is_shared_context" not in patterns_dict:
        patterns_dict["is_shared_context"] = False
    if "members_involved" not in patterns_dict:
        patterns_dict["members_involved"] = []
    return patterns_dict


def integrate_with_adaptive_guidance(guidance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add household context to adaptive guidance.
    
    This is purely additive — no migration required.
    """
    if "household_scope" not in guidance_dict:
        guidance_dict["household_scope"] = None
    if "conflict_sensitive" not in guidance_dict:
        guidance_dict["conflict_sensitive"] = False
    if "should_hold_back_for_conflict" not in guidance_dict:
        guidance_dict["should_hold_back_for_conflict"] = False
    return guidance_dict


def integrate_with_narrative(narrative_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add household context to narrative generation.
    
    This is purely additive — no migration required.
    """
    if "household_basis" not in narrative_dict:
        narrative_dict["household_basis"] = None
    if "shared_with_household" not in narrative_dict:
        narrative_dict["shared_with_household"] = False
    return narrative_dict
