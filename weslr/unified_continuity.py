# unified_continuity.py - v30: Unified Continuity / Context Consolidation Layer
# Consolidates user profile, longitudinal patterns, household context, domain context,
# governance state, and recent evidence/knowledge context into one stable resumable view.
# Additive only, transparent, reversible, operator-first, no repo drift.
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


class ContinuityScope(str, Enum):
    """Scope level for continuity consolidation."""
    SESSION = "session"  # Current session only
    WORKING = "working"  # Working set for current task
    HOUSEHOLD = "household"  # Shared household context
    GLOBAL = "global"  # Persistent global state


class ContinuityStatus(str, Enum):
    """Status of continuity state."""
    ACTIVE = "active"  # Currently being used
    PAUSED = "paused"  # Paused but resumable
    RESUMED = "resumed"  # Recently resumed from pause
    SNAPSHOT = "snapshot"  # Saved snapshot for later resumption
    EXPIRED = "expired"  # Too old to resume


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class ConsolidatedContinuity:
    """Unified continuity state consolidating all context sources."""
    
    continuity_id: str  # Unique identifier for this continuity state
    scope: str = ContinuityScope.SESSION.value  # Scope level
    
    # Core state
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    session_id: Optional[str] = None  # Session identifier
    operator_id: Optional[str] = None  # Operator identifier
    
    # Consolidated contexts
    profile_state: Optional[Dict[str, Any]] = None  # UserProfileContext from adaptive_guidance
    pattern_state: Optional[Dict[str, Any]] = None  # PatternMemoryStorage snapshot
    household_state: Optional[Dict[str, Any]] = None  # HouseholdContext
    domain_state: Optional[Dict[str, Any]] = None  # Current domain context
    governance_state: Optional[Dict[str, Any]] = None  # Governance/proposal state
    evidence_state: Optional[Dict[str, Any]] = None  # Recent evidence/knowledge
    
    # Continuity markers
    confidence: float = 0.5  # Confidence in this state (0.0-1.0)
    status: str = ContinuityStatus.ACTIVE.value
    last_activity: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    # Evidence trail
    consolidated_from: List[str] = field(default_factory=list)  # Sources that contributed
    consolidation_log: List[Dict[str, Any]] = field(default_factory=list)  # Full log
    
    # Metadata
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "continuity_id": self.continuity_id,
            "scope": self.scope,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "operator_id": self.operator_id,
            "profile_state": self.profile_state,
            "pattern_state": self.pattern_state,
            "household_state": self.household_state,
            "domain_state": self.domain_state,
            "governance_state": self.governance_state,
            "evidence_state": self.evidence_state,
            "confidence": self.confidence,
            "status": self.status,
            "last_activity": self.last_activity,
            "consolidated_from": self.consolidated_from,
            "consolidation_log": self.consolidation_log,
            "version": self.version,
            "created_at": self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConsolidatedContinuity:
        """Create from dictionary representation."""
        data["consolidated_from"] = data.get("consolidated_from", [])
        data["consolidation_log"] = data.get("consolidation_log", [])
        return cls(**data)
    
    def add_source(self, source_name: str, source_data: Dict[str, Any]) -> None:
        """Add a source to the consolidation."""
        self.consolidated_from.append(source_name)
        self.consolidation_log.append({
            "source": source_name,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "size": len(json.dumps(source_data)),
        })
    
    def update_confidence(self, new_confidence: float) -> None:
        """Update confidence level."""
        self.confidence = max(0.0, min(1.0, new_confidence))
        self.last_activity = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def pause(self) -> None:
        """Pause this continuity state."""
        self.status = ContinuityStatus.PAUSED.value
        self.last_activity = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def resume(self) -> None:
        """Resume this continuity state."""
        self.status = ContinuityStatus.RESUMED.value
        self.last_activity = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def is_expired(self, max_age_hours: float = 24.0) -> bool:
        """Check if this continuity state is expired."""
        try:
            created = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            age_hours = (now - created).total_seconds() / 3600
            return age_hours > max_age_hours
        except Exception:
            return True
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a human-readable summary of the continuity state."""
        return {
            "continuity_id": self.continuity_id,
            "scope": self.scope,
            "status": self.status,
            "confidence": self.confidence,
            "sources": len(self.consolidated_from),
            "sources_list": self.consolidated_from,
            "age_hours": self._get_age_hours(),
        }
    
    def _get_age_hours(self) -> float:
        """Get age in hours."""
        try:
            created = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return (now - created).total_seconds() / 3600
        except Exception:
            return 0.0


@dataclass
class ContinuitySnapshot:
    """Snapshot of continuity state for resumption."""
    
    continuity_id: str
    snapshot_id: str
    scope: str = ContinuityScope.SESSION.value
    
    # Full state
    full_state: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    expires_at: str = field(default_factory=lambda: (
        datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    ))  # Will be overridden with actual expiration
    
    # Resumption data
    current_context: Optional[str] = None  # Current working context
    last_action: Optional[str] = None  # Last action performed
    pending_tasks: List[str] = field(default_factory=list)  # Tasks waiting completion
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "continuity_id": self.continuity_id,
            "snapshot_id": self.snapshot_id,
            "scope": self.scope,
            "full_state": self.full_state,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "current_context": self.current_context,
            "last_action": self.last_action,
            "pending_tasks": self.pending_tasks,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ContinuitySnapshot:
        """Create from dictionary representation."""
        data["pending_tasks"] = data.get("pending_tasks", [])
        return cls(**data)
    
    def set_expiration(self, hours: float = 24.0) -> None:
        """Set expiration timestamp."""
        try:
            created = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
            from datetime import timedelta
            expires = created + timedelta(hours=hours)
            self.expires_at = expires.isoformat().replace("+00:00", "Z")
        except Exception:
            self.expires_at = self.created_at


# ============================================================================
# CONTINUITY MANAGER
# ============================================================================


class UnifiedContinuityManager:
    """Manager for unified continuity state and snapshots.
    
    Provides add-only, persistent storage with transparency.
    All continuity remains operator-first and reversible.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize unified continuity manager."""
        self.storage_path = storage_path or self._get_default_path()
        self.current_continuity: Optional[ConsolidatedContinuity] = None
        self.snapshots: Dict[str, ContinuitySnapshot] = {}  # snapshot_id -> Snapshot
        self._ensure_storage_exists()
        self._load_snapshots()
    
    def _get_default_path(self) -> str:
        """Get default storage path."""
        return "/data/data/com.termux/files/home/.openclaw/workspace/weslr/unified_continuity/"
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _load_snapshots(self) -> None:
        """Load snapshots from storage."""
        import os
        if not os.path.exists(self.storage_path):
            return
        
        for filename in os.listdir(self.storage_path):
            if filename.startswith("snapshot_") and filename.endswith(".json"):
                snapshot_id = filename[len("snapshot_"):-5]  # Remove prefix and .json
                try:
                    with open(os.path.join(self.storage_path, filename), "r") as f:
                        data = json.load(f)
                        self.snapshots[snapshot_id] = ContinuitySnapshot.from_dict(data)
                except Exception:
                    # Skip malformed files
                    continue
    
    def _save_snapshot(self, snapshot_id: str) -> None:
        """Save a snapshot to storage."""
        import os
        filepath = os.path.join(self.storage_path, f"snapshot_{snapshot_id}.json")
        data = self.snapshots[snapshot_id].to_dict()
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def create_continuity(
        self,
        continuity_id: str,
        scope: str = ContinuityScope.SESSION.value,
    ) -> ConsolidatedContinuity:
        """Create a new unified continuity state."""
        continuity = ConsolidatedContinuity(
            continuity_id=continuity_id,
            scope=scope,
        )
        self.current_continuity = continuity
        return continuity
    
    def get_continuity(self) -> Optional[ConsolidatedContinuity]:
        """Get current continuity state."""
        return self.current_continuity
    
    def consolidate_profile(
        self,
        continuity_id: str,
        profile_state: Dict[str, Any],
    ) -> None:
        """Consolidate profile state into continuity."""
        continuity = self.get_continuity()
        if not continuity or continuity.continuity_id != continuity_id:
            raise ValueError(f"Continuity {continuity_id} not found or mismatch")
        
        continuity.profile_state = profile_state
        continuity.add_source("profile", profile_state)
        continuity.update_confidence(continuity.confidence + 0.1)
    
    def consolidate_patterns(
        self,
        continuity_id: str,
        pattern_state: Dict[str, Any],
    ) -> None:
        """Consolidate pattern state into continuity."""
        continuity = self.get_continuity()
        if not continuity or continuity.continuity_id != continuity_id:
            raise ValueError(f"Continuity {continuity_id} not found or mismatch")
        
        continuity.pattern_state = pattern_state
        continuity.add_source("patterns", pattern_state)
        continuity.update_confidence(continuity.confidence + 0.05)
    
    def consolidate_household(
        self,
        continuity_id: str,
        household_state: Dict[str, Any],
    ) -> None:
        """Consolidate household state into continuity."""
        continuity = self.get_continuity()
        if not continuity or continuity.continuity_id != continuity_id:
            raise ValueError(f"Continuity {continuity_id} not found or mismatch")
        
        continuity.household_state = household_state
        continuity.add_source("household", household_state)
        continuity.update_confidence(continuity.confidence + 0.1)
    
    def consolidate_domain(
        self,
        continuity_id: str,
        domain_state: Dict[str, Any],
    ) -> None:
        """Consolidate domain state into continuity."""
        continuity = self.get_continuity()
        if not continuity or continuity.continuity_id != continuity_id:
            raise ValueError(f"Continuity {continuity_id} not found or mismatch")
        
        continuity.domain_state = domain_state
        continuity.add_source("domain", domain_state)
        continuity.update_confidence(continuity.confidence + 0.1)
    
    def consolidate_governance(
        self,
        continuity_id: str,
        governance_state: Dict[str, Any],
    ) -> None:
        """Consolidate governance state into continuity."""
        continuity = self.get_continuity()
        if not continuity or continuity.continuity_id != continuity_id:
            raise ValueError(f"Continuity {continuity_id} not found or mismatch")
        
        continuity.governance_state = governance_state
        continuity.add_source("governance", governance_state)
        continuity.update_confidence(continuity.confidence + 0.1)
    
    def consolidate_evidence(
        self,
        continuity_id: str,
        evidence_state: Dict[str, Any],
    ) -> None:
        """Consolidate evidence state into continuity."""
        continuity = self.get_continuity()
        if not continuity or continuity.continuity_id != continuity_id:
            raise ValueError(f"Continuity {continuity_id} not found or mismatch")
        
        continuity.evidence_state = evidence_state
        continuity.add_source("evidence", evidence_state)
        continuity.update_confidence(continuity.confidence + 0.1)
    
    def pause_continuity(self, continuity_id: str) -> bool:
        """Pause current continuity state."""
        continuity = self.get_continuity()
        if not continuity or continuity.continuity_id != continuity_id:
            return False
        
        continuity.pause()
        return True
    
    def resume_continuity(self, continuity_id: str) -> bool:
        """Resume a continuity state."""
        continuity = self.get_continuity()
        if not continuity or continuity.continuity_id != continuity_id:
            return False
        
        continuity.resume()
        return True
    
    def take_snapshot(
        self,
        continuity_id: str,
        snapshot_id: str,
        scope: str = ContinuityScope.SESSION.value,
    ) -> ContinuitySnapshot:
        """Take a snapshot of current continuity state."""
        continuity = self.get_continuity()
        if not continuity or continuity.continuity_id != continuity_id:
            raise ValueError(f"Continuity {continuity_id} not found")
        
        snapshot = ContinuitySnapshot(
            continuity_id=continuity_id,
            snapshot_id=snapshot_id,
            scope=scope,
            full_state=continuity.to_dict(),
            current_context=continuity.get_summary(),
            pending_tasks=[],
        )
        
        snapshot.set_expiration(hours=24.0)
        self.snapshots[snapshot_id] = snapshot
        self._save_snapshot(snapshot_id)
        
        return snapshot
    
    def restore_snapshot(self, snapshot_id: str) -> bool:
        """Restore from a snapshot."""
        if snapshot_id not in self.snapshots:
            return False
        
        snapshot = self.snapshots[snapshot_id]
        
        # Load snapshot state into current continuity
        continuity_data = snapshot.full_state
        continuity = ConsolidatedContinuity.from_dict(continuity_data)
        self.current_continuity = continuity
        
        return True
    
    def expire_snapshots(self) -> List[str]:
        """Expire snapshots older than 24 hours."""
        import os
        expired = []
        current_time = datetime.now(timezone.utc)
        
        for snapshot_id, snapshot in list(self.snapshots.items()):
            try:
                expires = datetime.fromisoformat(snapshot.expires_at.replace("Z", "+00:00"))
                if current_time > expires:
                    expired.append(snapshot_id)
                    del self.snapshots[snapshot_id]
                    filepath = os.path.join(self.storage_path, f"snapshot_{snapshot_id}.json")
                    if os.path.exists(filepath):
                        os.remove(filepath)
            except Exception:
                expired.append(snapshot_id)
                del self.snapshots[snapshot_id]
        
        return expired
    
    def get_all_snapshots(self) -> Dict[str, ContinuitySnapshot]:
        """Get all snapshots."""
        return self.snapshots
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manager state to dictionary."""
        return {
            "continuity_count": 1 if self.current_continuity else 0,
            "current_continuity": self.current_continuity.to_dict() if self.current_continuity else None,
            "snapshot_count": len(self.snapshots),
            "snapshots": {sid: s.to_dict() for sid, s in self.snapshots.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_narrative(narrative_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add unified continuity context to narrative generation.
    
    This is purely additive — no migration required.
    """
    if "continuity_context" not in narrative_dict:
        narrative_dict["continuity_context"] = None
    if "continuity_source" not in narrative_dict:
        narrative_dict["continuity_source"] = None
    return narrative_dict


def integrate_with_adaptive_guidance(guidance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add unified continuity insights to adaptive guidance.
    
    This is purely additive — no migration required.
    """
    if "continuity_context" not in guidance_dict:
        guidance_dict["continuity_context"] = None
    if "confidence_from_continuity" not in guidance_dict:
        guidance_dict["confidence_from_continuity"] = 0.0
    if "should_pause_for_context" not in guidance_dict:
        guidance_dict["should_pause_for_context"] = False
    return guidance_dict


def integrate_with_governance(governance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add unified continuity awareness to governance context.
    
    This is purely additive — no migration required.
    """
    if "continuity_snapshot_id" not in governance_dict:
        governance_dict["continuity_snapshot_id"] = None
    if "continuity_scope" not in governance_dict:
        governance_dict["continuity_scope"] = ContinuityScope.SESSION.value
    return governance_dict


def integrate_with_operator_review(review_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add unified continuity context to operator proposal review.
    
    This is purely additive — no migration required.
    """
    if "continuity_state" not in review_dict:
        review_dict["continuity_state"] = None
    if "continuity_confidence" not in review_dict:
        review_dict["continuity_confidence"] = 0.0
    if "can_resume_continuity" not in review_dict:
        review_dict["can_resume_continuity"] = False
    return review_dict
