# multi_timescale_planning.py - v38: Multi-Timescale Planning / Trajectory Layer
# Creates a governed planning layer that lets WESLR reason across immediate,
# short-term, medium-term, and long-term horizons when forming recommendations.
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


class HorizonType(str, Enum):
    """Time horizon for planning and recommendations."""
    IMMEDIATE = "immediate"  # Actions to take now or within minutes
    SHORT_TERM = "short_term"  # Actions within hours to days
    MEDIUM_TERM = "medium_term"  # Actions within days to weeks
    LONG_TERM = "long_term"  # Actions within weeks to months or longer


class HorizonPriority(str, Enum):
    """Priority level for a horizon."""
    LOW = "low"  # Not urgent, can be deferred
    NORMAL = "normal"  # Standard priority
    HIGH = "high"  # Important, should be addressed soon
    CRITICAL = "critical"  # Urgent, needs immediate attention


class HorizonConflictType(str, Enum):
    """Type of conflict between horizons."""
    RESOURCE = "resource"  # Conflicting resource allocation
    TIMING = "timing"  # Conflicting time requirements
    GOAL = "goal"  # Conflicting goal alignment
    PRIORITY = "priority"  # Conflicting priority rankings


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class HorizonEntry:
    """A single entry in the multi-timescale planning trajectory."""
    
    # Identity
    entry_id: str  # Unique identifier
    horizon_type: str = HorizonType.SHORT_TERM.value  # Time horizon
    
    # Content
    title: str = ""  # Brief description
    description: str = ""  # Detailed explanation
    target_action: str = ""  # What action this represents
    
    # Timeline
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    start_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    deadline_at: Optional[str] = None  # Expected completion time
    duration_seconds: int = 0  # Expected duration in seconds
    
    # Priority and urgency
    priority: str = HorizonPriority.NORMAL.value
    urgency: float = 0.5  # 0.0-1.0
    
    # Confidence
    confidence: float = 0.5  # How confident we are in this trajectory
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)  # IDs of required entries
    blocking_entries: List[str] = field(default_factory=list)  # IDs this blocks
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    source: str = "auto"  # "auto", "user", "inference"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "entry_id": self.entry_id,
            "horizon_type": self.horizon_type,
            "title": self.title,
            "description": self.description,
            "target_action": self.target_action,
            "created_at": self.created_at,
            "start_at": self.start_at,
            "deadline_at": self.deadline_at,
            "duration_seconds": self.duration_seconds,
            "priority": self.priority,
            "urgency": self.urgency,
            "confidence": self.confidence,
            "depends_on": self.depends_on,
            "blocking_entries": self.blocking_entries,
            "tags": self.tags,
            "source": self.source,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HorizonEntry:
        """Create from dictionary representation."""
        data["depends_on"] = data.get("depends_on", [])
        data["blocking_entries"] = data.get("blocking_entries", [])
        data["tags"] = data.get("tags", [])
        return cls(**data)
    
    def get_horizon_enum(self) -> HorizonType:
        """Get horizon type as enum."""
        return HorizonType(self.horizon_type)
    
    def is_overdue(self) -> bool:
        """Check if entry is overdue."""
        if not self.deadline_at:
            return False
        
        try:
            deadline = datetime.fromisoformat(self.deadline_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return now > deadline and self.priority not in [HorizonPriority.LOW.value, HorizonPriority.NORMAL.value]
        except Exception:
            return False
    
    def get_time_remaining_seconds(self) -> Optional[int]:
        """Get remaining time until deadline in seconds."""
        if not self.deadline_at:
            return None
        
        try:
            deadline = datetime.fromisoformat(self.deadline_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return int((deadline - now).total_seconds())
        except Exception:
            return None


@dataclass
class Trajectory:
    """A collection of horizon entries forming a planning trajectory."""
    
    # Identity
    trajectory_id: str  # Unique identifier
    
    # Entries
    entries: List[HorizonEntry] = field(default_factory=list)
    
    # Metadata
    name: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    last_updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "trajectory_id": self.trajectory_id,
            "name": self.name,
            "entries": [e.to_dict() for e in self.entries],
            "created_at": self.created_at,
            "last_updated_at": self.last_updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Trajectory:
        """Create from dictionary representation."""
        entry_data = data.get("entries", [])
        data["entries"] = [HorizonEntry.from_dict(e) for e in entry_data]
        return cls(**data)
    
    def add_entry(self, entry: HorizonEntry) -> None:
        """Add an entry to the trajectory."""
        self.entries.append(entry)
        self.last_updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def get_entries_by_horizon(self, horizon_type: str) -> List[HorizonEntry]:
        """Get all entries for a specific horizon type."""
        return [e for e in self.entries if e.horizon_type == horizon_type]
    
    def get_entry(self, entry_id: str) -> Optional[HorizonEntry]:
        """Get a specific entry by ID."""
        for entry in self.entries:
            if entry.entry_id == entry_id:
                return entry
        return None
    
    def count_entries(self) -> Dict[str, int]:
        """Count entries by horizon type."""
        counts = {
            HorizonType.IMMEDIATE.value: 0,
            HorizonType.SHORT_TERM.value: 0,
            HorizonType.MEDIUM_TERM.value: 0,
            HorizonType.LONG_TERM.value: 0,
        }
        for entry in self.entries:
            counts[entry.horizon_type] = counts.get(entry.horizon_type, 0) + 1
        return counts
    
    def get_horizon_summary(self) -> Dict[str, Any]:
        """Get summary of all horizons."""
        counts = self.count_entries()
        return {
            "immediate_count": counts.get(HorizonType.IMMEDIATE.value, 0),
            "short_term_count": counts.get(HorizonType.SHORT_TERM.value, 0),
            "medium_term_count": counts.get(HorizonType.MEDIUM_TERM.value, 0),
            "long_term_count": counts.get(HorizonType.LONG_TERM.value, 0),
            "total_entries": len(self.entries),
        }


@dataclass
class HorizonConflict:
    """A conflict between entries in different time horizons."""
    
    conflict_id: str  # Unique identifier
    trajectory_id: str  # Related trajectory
    
    # Conflict details
    entry_a_id: str  # First entry ID
    entry_b_id: str  # Second entry ID
    conflict_type: str = HorizonConflictType.RESOURCE.value  # Type of conflict
    
    # Impact
    severity: float = 0.5  # 0.0-1.0
    description: str = ""  # Explanation of conflict
    
    # Resolution
    is_resolved: bool = False
    resolved_at: Optional[str] = None
    resolution_description: Optional[str] = None
    
    # Timestamps
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "conflict_id": self.conflict_id,
            "trajectory_id": self.trajectory_id,
            "entry_a_id": self.entry_a_id,
            "entry_b_id": self.entry_b_id,
            "conflict_type": self.conflict_type,
            "severity": self.severity,
            "description": self.description,
            "is_resolved": self.is_resolved,
            "resolved_at": self.resolved_at,
            "resolution_description": self.resolution_description,
            "detected_at": self.detected_at,
            "created_at": self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HorizonConflict:
        """Create from dictionary representation."""
        return cls(**data)
    
    def resolve(self, resolution: str) -> None:
        """Mark conflict as resolved."""
        self.is_resolved = True
        self.resolved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.resolution_description = resolution


# ============================================================================
# TRAJECTORY MANAGER
# ============================================================================


class TrajectoryManager:
    """Manager for multi-timescale planning trajectories.
    
    Provides transparent, reversible planning management.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize trajectory manager."""
        self.storage_path = storage_path or "/data/data/com.termux/files/home/.openclaw/workspace/weslr/multi_timescale_planning/"
        self.trajectories: Dict[str, Trajectory] = {}  # trajectory_id -> Trajectory
        self.conflicts: Dict[str, HorizonConflict] = {}  # conflict_id -> Conflict
        self._ensure_storage_exists()
        self._load_trajectories()
        self._load_conflicts()
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _load_trajectories(self) -> None:
        """Load trajectories from storage."""
        import os
        if not os.path.exists(self.storage_path):
            return
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith("_trajectory.json"):
                trajectory_id = filename[:-15]  # Remove _trajectory.json
                try:
                    with open(os.path.join(self.storage_path, filename), "r") as f:
                        data = json.load(f)
                        self.trajectories[trajectory_id] = Trajectory.from_dict(data)
                except Exception:
                    continue
    
    def _load_conflicts(self) -> None:
        """Load conflicts from storage."""
        import os
        if not os.path.exists(self.storage_path):
            return
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith("_conflict.json"):
                conflict_id = filename[:-13]  # Remove _conflict.json
                try:
                    with open(os.path.join(self.storage_path, filename), "r") as f:
                        data = json.load(f)
                        self.conflicts[conflict_id] = HorizonConflict.from_dict(data)
                except Exception:
                    continue
    
    def _save_trajectory(self, trajectory_id: str) -> None:
        """Save a trajectory to storage."""
        import os
        filepath = os.path.join(self.storage_path, f"{trajectory_id}_trajectory.json")
        data = self.trajectories[trajectory_id].to_dict()
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def _save_conflict(self, conflict_id: str) -> None:
        """Save a conflict to storage."""
        import os
        filepath = os.path.join(self.storage_path, f"{conflict_id}_conflict.json")
        data = self.conflicts[conflict_id].to_dict()
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def create_trajectory(self, trajectory_id: str, name: str = "") -> Trajectory:
        """Create a new trajectory."""
        trajectory = Trajectory(trajectory_id=trajectory_id, name=name)
        self.trajectories[trajectory_id] = trajectory
        self._save_trajectory(trajectory_id)
        return trajectory
    
    def get_trajectory(self, trajectory_id: str) -> Optional[Trajectory]:
        """Get a trajectory by ID."""
        return self.trajectories.get(trajectory_id)
    
    def get_default_trajectory(self) -> Trajectory:
        """Get the default trajectory (create if needed)."""
        if "default" not in self.trajectories:
            return self.create_trajectory("default", "Default Planning Trajectory")
        return self.trajectories["default"]
    
    def add_entry(
        self,
        trajectory_id: str,
        entry: HorizonEntry,
    ) -> Trajectory:
        """Add an entry to a trajectory."""
        trajectory = self.get_trajectory(trajectory_id)
        if not trajectory:
            trajectory = self.create_trajectory(trajectory_id)
        
        trajectory.add_entry(entry)
        self._save_trajectory(trajectory_id)
        return trajectory
    
    def create_immediate_entry(
        self,
        trajectory_id: str,
        title: str,
        description: str = "",
        target_action: str = "",
        urgency: float = 0.5,
    ) -> HorizonEntry:
        """Create and add an immediate action entry."""
        entry = HorizonEntry(
            entry_id=f"entry-{len(self.trajectories.get(trajectory_id, Trajectory('tmp')).entries) + 1:04d}",
            horizon_type=HorizonType.IMMEDIATE.value,
            title=title,
            description=description,
            target_action=target_action,
            urgency=urgency,
        )
        self.add_entry(trajectory_id, entry)
        return entry
    
    def create_short_term_entry(
        self,
        trajectory_id: str,
        title: str,
        description: str = "",
        target_action: str = "",
        deadline_at: Optional[str] = None,
        priority: str = HorizonPriority.NORMAL.value,
    ) -> HorizonEntry:
        """Create and add a short-term plan entry."""
        entry = HorizonEntry(
            entry_id=f"entry-{len(self.trajectories.get(trajectory_id, Trajectory('tmp')).entries) + 1:04d}",
            horizon_type=HorizonType.SHORT_TERM.value,
            title=title,
            description=description,
            target_action=target_action,
            deadline_at=deadline_at,
            priority=priority,
        )
        self.add_entry(trajectory_id, entry)
        return entry
    
    def create_medium_term_entry(
        self,
        trajectory_id: str,
        title: str,
        description: str = "",
        target_action: str = "",
        duration_seconds: int = 86400,  # 1 day default
        priority: str = HorizonPriority.HIGH.value,
    ) -> HorizonEntry:
        """Create and add a medium-term habit entry."""
        entry = HorizonEntry(
            entry_id=f"entry-{len(self.trajectories.get(trajectory_id, Trajectory('tmp')).entries) + 1:04d}",
            horizon_type=HorizonType.MEDIUM_TERM.value,
            title=title,
            description=description,
            target_action=target_action,
            duration_seconds=duration_seconds,
            priority=priority,
        )
        self.add_entry(trajectory_id, entry)
        return entry
    
    def create_long_term_entry(
        self,
        trajectory_id: str,
        title: str,
        description: str = "",
        target_action: str = "",
        priority: str = HorizonPriority.LOW.value,
        source: str = "inference",
    ) -> HorizonEntry:
        """Create and add a long-term goal entry."""
        entry = HorizonEntry(
            entry_id=f"entry-{len(self.trajectories.get(trajectory_id, Trajectory('tmp')).entries) + 1:04d}",
            horizon_type=HorizonType.LONG_TERM.value,
            title=title,
            description=description,
            target_action=target_action,
            priority=priority,
            source=source,
        )
        self.add_entry(trajectory_id, entry)
        return entry
    
    def detect_conflicts(self, trajectory_id: str) -> List[HorizonConflict]:
        """Detect conflicts within a trajectory."""
        trajectory = self.get_trajectory(trajectory_id)
        if not trajectory:
            return []
        
        conflicts = []
        
        # Simple conflict detection based on dependencies and timing
        for i, entry_a in enumerate(trajectory.entries):
            for entry_b in trajectory.entries[i+1:]:
                # Check for dependency conflicts
                if entry_a.entry_id in entry_b.depends_on and entry_b.entry_id in entry_a.depends_on:
                    conflict = HorizonConflict(
                        conflict_id=f"conflict-{len(self.conflicts) + 1:04d}",
                        trajectory_id=trajectory_id,
                        entry_a_id=entry_a.entry_id,
                        entry_b_id=entry_b.entry_id,
                        conflict_type=HorizonConflictType.GOAL.value,
                        severity=0.8,
                        description="Mutual dependency between entries creates circular dependency",
                    )
                    conflicts.append(conflict)
                
                # Check for timing conflicts (same deadline for different horizons)
                if entry_a.deadline_at and entry_b.deadline_at and entry_a.horizon_type != entry_b.horizon_type:
                    if entry_a.deadline_at == entry_b.deadline_at:
                        conflict = HorizonConflict(
                            conflict_id=f"conflict-{len(self.conflicts) + 1:04d}",
                            trajectory_id=trajectory_id,
                            entry_a_id=entry_a.entry_id,
                            entry_b_id=entry_b.entry_id,
                            conflict_type=HorizonConflictType.TIMING.value,
                            severity=0.5,
                            description="Both entries target the same deadline despite different horizons",
                        )
                        conflicts.append(conflict)
        
        return conflicts
    
    def register_conflict(self, conflict: HorizonConflict) -> None:
        """Register a conflict."""
        self.conflicts[conflict.conflict_id] = conflict
        self._save_conflict(conflict.conflict_id)
    
    def resolve_conflict(self, conflict_id: str, resolution: str) -> bool:
        """Resolve a conflict."""
        conflict = self.conflicts.get(conflict_id)
        if not conflict:
            return False
        
        conflict.resolve(resolution)
        self._save_conflict(conflict_id)
        return True
    
    def get_all_trajectories(self) -> Dict[str, Trajectory]:
        """Get all trajectories."""
        return self.trajectories
    
    def get_all_conflicts(self) -> Dict[str, HorizonConflict]:
        """Get all conflicts."""
        return self.conflicts
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manager state to dictionary."""
        return {
            "trajectory_count": len(self.trajectories),
            "conflict_count": len(self.conflicts),
            "trajectories": {k: v.to_dict() for k, v in self.trajectories.items()},
            "conflicts": {k: v.to_dict() for k, v in self.conflicts.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_goal_hierarchy(hierarchy_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add trajectory context to goal hierarchy.
    
    This is purely additive — no migration required.
    """
    if "trajectory_id" not in hierarchy_dict:
        hierarchy_dict["trajectory_id"] = None
    if "horizon_type" not in hierarchy_dict:
        hierarchy_dict["horizon_type"] = HorizonType.SHORT_TERM.value
    if "trajectory_confidence" not in hierarchy_dict:
        hierarchy_dict["trajectory_confidence"] = 0.5
    return hierarchy_dict


def integrate_with_adaptive_guidance(guidance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add trajectory context to adaptive guidance.
    
    This is purely additive — no migration required.
    """
    if "trajectory_id" not in guidance_dict:
        guidance_dict["trajectory_id"] = None
    if "recommendation_horizon" not in guidance_dict:
        guidance_dict["recommendation_horizon"] = HorizonType.SHORT_TERM.value
    if "horizon_conflicts" not in guidance_dict:
        guidance_dict["horizon_conflicts"] = []
    return guidance_dict


def integrate_with_intervention_timing(timing_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add trajectory context to intervention timing.
    
    This is purely additive — no migration required.
    """
    if "trajectory_id" not in timing_dict:
        timing_dict["trajectory_id"] = None
    if "trajectory_priority" not in timing_dict:
        timing_dict["trajectory_priority"] = HorizonPriority.NORMAL.value
    if "trajectory_urgency" not in timing_dict:
        timing_dict["trajectory_urgency"] = 0.5
    return timing_dict


def integrate_with_trust_dynamics(trust_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add trajectory context to trust dynamics.
    
    This is purely additive — no migration required.
    """
    if "trajectory_id" not in trust_dict:
        trust_dict["trajectory_id"] = None
    if "trajectory_transparency" not in trust_dict:
        trust_dict["trajectory_transparency"] = "standard"  # minimal, standard, elevated
    return trust_dict
