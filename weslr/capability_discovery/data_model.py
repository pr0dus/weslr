"""Capability Discovery Radar - Data Models.

Non-Pydantic implementation for Termux/Android compatibility.
"""

from __future__ import annotations

import calendar
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class CapabilityType(str, Enum):
    """Types of capabilities that WESLR might lack."""
    REAL_TIME_COLLAB = "real_time_collab"
    AI_ASSISTED_WRITING = "ai_assisted_writing"
    VISUAL_WORKFLOW_BUILDER = "visual_workflow_builder"
    CROSS_PLATFORM_SYNC = "cross_platform_sync"
    NATIVE_MOBILE = "native_mobile"
    OFFLINE_FIRST = "offline_first"
    MARKDOWN_EXTENSIONS = "markdown_extensions"
    DATA_INTEGRATIONS = "data_integrations"
    AUTOMATION_PATTERNS = "automation_patterns"
    CUSTOM_THEMING = "custom_theming"
    PRIVACY_CONTROLS = "privacy_controls"
    BACKUP_SYNCHRONIZATION = "backup_synchronization"
    API_ACCESS_LEVEL = "api_access_level"
    AUDIT_LOGGING = "audit_logging"
    TEAM_MANAGEMENT = "team_management"
    CUSTOM_WORKFLOW_HOOKS = "custom_workflow_hooks"
    VERSION_HISTORY = "version_history"
    COLLABORATIVE_ANNOTATIONS = "collaborative_annotations"
    OTHER = "other"  # For unknown/unclassified capabilities


class SuggestionStatus(str, Enum):
    """State machine statuses for suggestions."""
    NEW = "new"
    SUGGESTED = "suggested"
    ACCEPTED = "accepted"
    DENIED = "denied"
    SNOOZED = "snoozed"
    ARCHIVED = "archived"


@dataclass
class SourceProvenance:
    """Source tracking for a capability signal."""
    url: str
    title: str
    snippet: str
    relevance_score: float
    signal_type: str
    timestamp: str


@dataclass
class CapabilitySuggestion:
    """A capability suggestion generated from external signals."""
    title: str
    capability_type: CapabilityType
    summary: str
    why_it_matters: str
    improvement_area: str
    id: str = ""
    provenance: List[SourceProvenance] = field(default_factory=list)
    
    confidence: float = 0.5
    rank_score: float = 0.0
    status: SuggestionStatus = SuggestionStatus.NEW
    
    created_at: str = ""
    last_seen_at: str = ""
    last_ranked_at: Optional[str] = None
    denied_until: Optional[str] = None
    snoozed_until: Optional[str] = None
    
    # Search / filter fields
    tags: List[str] = field(default_factory=list)
    mentions_count: int = 1
    growth_trend: str = "stable"
    
    # Additional metadata
    first_seen_at: Optional[str] = None
    source_diversity: int = 1
    github_activity: Optional[Dict[str, Any]] = None
    science_relevance: Optional[str] = None
    architectural_fit: str = "medium"
    
    # ============== Initialization ==============
    
    def __post_init__(self):
        """Set defaults after dataclass init."""
        if not self.id:
            self.id = str(uuid.uuid4())
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if not self.created_at:
            self.created_at = now
        if not self.last_seen_at:
            self.last_seen_at = now
        if not self.first_seen_at:
            self.first_seen_at = self.created_at
    
    # ============== Serialization ==============
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "title": self.title,
            "capability_type": self.capability_type.value,
            "summary": self.summary,
            "why_it_matters": self.why_it_matters,
            "improvement_area": self.improvement_area,
            "provenance": [p.__dict__ for p in self.provenance],
            "confidence": self.confidence,
            "rank_score": self.rank_score,
            "status": self.status.value,
            "created_at": self.created_at,
            "last_seen_at": self.last_seen_at,
            "last_ranked_at": self.last_ranked_at,
            "denied_until": self.denied_until,
            "snoozed_until": self.snoozed_until,
            "tags": self.tags,
            "mentions_count": self.mentions_count,
            "growth_trend": self.growth_trend,
            "first_seen_at": self.first_seen_at,
            "source_diversity": self.source_diversity,
            "github_activity": self.github_activity,
            "science_relevance": self.science_relevance,
            "architectural_fit": self.architectural_fit,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CapabilitySuggestion:
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            title=data["title"],
            capability_type=CapabilityType(data["capability_type"]),
            summary=data["summary"],
            why_it_matters=data["why_it_matters"],
            improvement_area=data["improvement_area"],
            provenance=[SourceProvenance(**p) for p in data.get("provenance", [])],
            confidence=data.get("confidence", 0.5),
            rank_score=data.get("rank_score", 0.0),
            status=SuggestionStatus(data.get("status", "new")),
            created_at=data.get("created_at", ""),
            last_seen_at=data.get("last_seen_at", ""),
            last_ranked_at=data.get("last_ranked_at"),
            denied_until=data.get("denied_until"),
            snoozed_until=data.get("snoozed_until"),
            tags=data.get("tags", []),
            mentions_count=data.get("mentions_count", 1),
            growth_trend=data.get("growth_trend", "stable"),
            first_seen_at=data.get("first_seen_at"),
            source_diversity=data.get("source_diversity", 1),
            github_activity=data.get("github_activity"),
            science_relevance=data.get("science_relevance"),
            architectural_fit=data.get("architectural_fit", "medium"),
        )
    
    # ============== Status Transitions ==============
    
    def transition_to(self, new_status: SuggestionStatus) -> None:
        """Update status and timestamp."""
        self.status = new_status
        # Use higher precision timestamp by adding 2 seconds to ensure it's greater
        self.last_seen_at = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime(time.time() + 2)  # Add 2 seconds to ensure uniqueness
        )
    
    def deny(self, hours: int = 24) -> None:
        """Deny this suggestion for N hours."""
        if hours <= 0:
            # Immediately expired - set to a time in the past
            self.denied_until = time.strftime(
                "%Y-%m-%dT%H:%M:%SZ",
                time.gmtime(time.time() - 3600)  # 1 hour in the past
            )
        else:
            self.denied_until = time.strftime(
                "%Y-%m-%dT%H:%M:%SZ",
                time.gmtime(time.time() + hours * 3600)
            )
        self.transition_to(SuggestionStatus.DENIED)
    
    def snooze(self, hours: int = 1) -> None:
        """Snooze this suggestion for N hours."""
        self.snoozed_until = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime(time.time() + hours * 3600)
        )
        self.transition_to(SuggestionStatus.SNOOZED)
    
    def is_denied(self) -> bool:
        """Check if suggestion is currently denied (within 24h)."""
        if self.status != SuggestionStatus.DENIED or not self.denied_until:
            return False
        try:
            deny_dt = time.strptime(self.denied_until, "%Y-%m-%dT%H:%M:%SZ")
            deny_epoch = calendar.timegm(deny_dt)
            return time.time() < deny_epoch
        except Exception:
            return False
    
    def is_snoozed(self) -> bool:
        """Check if suggestion is currently snoozed."""
        if self.status != SuggestionStatus.SNOOZED or not self.snoozed_until:
            return False
        try:
            snooze_dt = time.strptime(self.snoozed_until, "%Y-%m-%dT%H:%M:%SZ")
            snooze_epoch = calendar.timegm(snooze_dt)
            return time.time() < snooze_epoch
        except Exception:
            return False
    
    def is_expired(self) -> bool:
        """Check if suggestion has expired (denied or snoozed)."""
        # A suggestion is expired if it's denied and the denial period has passed
        # OR if it's snoozed and the snooze period has passed
        if self.status == SuggestionStatus.DENIED:
            return self.is_denied_expired()
        if self.status == SuggestionStatus.SNOOZED:
            return self.is_snoozed_expired()
        return False
    
    def is_denied_expired(self) -> bool:
        """Check if 24h denial period has expired."""
        if not self.denied_until:
            # No denial time set - not expired
            return False
        try:
            deny_dt = time.strptime(self.denied_until, "%Y-%m-%dT%H:%M:%SZ")
            deny_epoch = calendar.timegm(deny_dt)
            return time.time() > deny_epoch
        except Exception:
            return True
    
    def is_snoozed_expired(self) -> bool:
        """Check if snooze period has expired."""
        if not self.snoozed_until:
            # No snooze time set - not expired
            return False
        try:
            snooze_dt = time.strptime(self.snoozed_until, "%Y-%m-%dT%H:%M:%SZ")
            snooze_epoch = calendar.timegm(snooze_dt)
            return time.time() > snooze_epoch
        except Exception:
            return True
