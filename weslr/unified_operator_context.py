# unified_operator_context.py - v31: Unified Operator Context Surface
# Creates one operator-facing context surface that makes current Weslr state
# understandable and usable in daily operation.
# Additive only, operator-first, transparent, reversible, no repo drift.
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


class ReliabilityMode(str, Enum):
    """Operational reliability mode."""
    NORMAL = "normal"  # Standard operation
    STRICT = "strict"  # Higher confidence thresholds
    FLEXIBLE = "flexible"  # Lower confidence thresholds
    PAUSED = "paused"  # Operator pause mode
    EMERGENCY = "emergency"  # Override safety for critical tasks


class ContextSurfaceStatus(str, Enum):
    """Status of the context surface."""
    ACTIVE = "active"  # Currently active and being used
    IDLE = "idle"  # No active session
    RESUMING = "resuming"  # Recently resumed
    PAUSED = "paused"  # Paused by operator


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class OperatorContextSummary:
    """Operator-facing summary of current system state."""
    
    surface_id: str  # Unique identifier for this context surface
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    # Continuity
    continuity_summary: Optional[Dict[str, Any]] = None
    
    # Personalization
    personalization_summary: Optional[Dict[str, Any]] = None
    
    # Longitudinal patterns
    pattern_summary: Optional[Dict[str, Any]] = None
    
    # Household context
    household_summary: Optional[Dict[str, Any]] = None
    
    # Domain context
    domain_summary: Optional[Dict[str, Any]] = None
    
    # Governance
    governance_summary: Optional[Dict[str, Any]] = None
    
    # Reliability mode
    reliability_mode: str = ReliabilityMode.NORMAL.value
    
    # Evidence/knowledge
    evidence_summary: Optional[Dict[str, Any]] = None
    
    # Current guidance posture
    guidance_posture: Optional[Dict[str, Any]] = None
    
    # Metadata
    status: str = ContextSurfaceStatus.ACTIVE.value
    operator_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "surface_id": self.surface_id,
            "timestamp": self.timestamp,
            "continuity_summary": self.continuity_summary,
            "personalization_summary": self.personalization_summary,
            "pattern_summary": self.pattern_summary,
            "household_summary": self.household_summary,
            "domain_summary": self.domain_summary,
            "governance_summary": self.governance_summary,
            "reliability_mode": self.reliability_mode,
            "evidence_summary": self.evidence_summary,
            "guidance_posture": self.guidance_posture,
            "status": self.status,
            "operator_id": self.operator_id,
            "session_id": self.session_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OperatorContextSummary:
        """Create from dictionary representation."""
        return cls(**data)
    
    def get_status_display(self) -> str:
        """Get human-readable status."""
        return f"{self.status.upper()} | Mode: {self.reliability_mode}"
    
    def get_state_overview(self) -> Dict[str, Any]:
        """Get a comprehensive state overview."""
        return {
            "status": self.status,
            "reliability_mode": self.reliability_mode,
            "continuity": self.continuity_summary.get("status") if self.continuity_summary else "none",
            "patterns": self.pattern_summary.get("pattern_count", 0) if self.pattern_summary else 0,
            "household": self.household_summary.get("household_count", 0) if self.household_summary else 0,
            "governance": self.governance_summary.get("scorecard_count", 0) if self.governance_summary else 0,
            "evidence": self.evidence_summary.get("evidence_count", 0) if self.evidence_summary else 0,
            "guidance_confidence": self.guidance_posture.get("confidence", 0.0) if self.guidance_posture else 0.0,
        }


# ============================================================================
# CONTEXT SURFACE MANAGER
# ============================================================================


class UnifiedOperatorContextManager:
    """Manager for unified operator context surface.
    
    Provides transparent, operator-first state display with reversibility.
    All state remains additive and non-manipulative.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize unified operator context manager."""
        self.storage_path = storage_path or self._get_default_path()
        self.current_surface: Optional[OperatorContextSummary] = None
        self._ensure_storage_exists()
    
    def _get_default_path(self) -> str:
        """Get default storage path."""
        return "/data/data/com.termux/files/home/.openclaw/workspace/weslr/operator_context/"
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def create_surface(
        self,
        surface_id: str,
        operator_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> OperatorContextSummary:
        """Create a new operator context surface."""
        surface = OperatorContextSummary(
            surface_id=surface_id,
            operator_id=operator_id,
            session_id=session_id,
        )
        self.current_surface = surface
        return surface
    
    def get_surface(self) -> Optional[OperatorContextSummary]:
        """Get current operator context surface."""
        return self.current_surface
    
    def update_continuity(
        self,
        surface_id: str,
        continuity_summary: Dict[str, Any],
    ) -> None:
        """Update continuity summary in context surface."""
        surface = self.get_surface()
        if not surface or surface.surface_id != surface_id:
            raise ValueError(f"Context surface {surface_id} not found or mismatch")
        
        surface.continuity_summary = continuity_summary
        surface.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def update_personalization(
        self,
        surface_id: str,
        personalization_summary: Dict[str, Any],
    ) -> None:
        """Update personalization summary in context surface."""
        surface = self.get_surface()
        if not surface or surface.surface_id != surface_id:
            raise ValueError(f"Context surface {surface_id} not found or mismatch")
        
        surface.personalization_summary = personalization_summary
        surface.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def update_patterns(
        self,
        surface_id: str,
        pattern_summary: Dict[str, Any],
    ) -> None:
        """Update pattern summary in context surface."""
        surface = self.get_surface()
        if not surface or surface.surface_id != surface_id:
            raise ValueError(f"Context surface {surface_id} not found or mismatch")
        
        surface.pattern_summary = pattern_summary
        surface.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def update_household(
        self,
        surface_id: str,
        household_summary: Dict[str, Any],
    ) -> None:
        """Update household summary in context surface."""
        surface = self.get_surface()
        if not surface or surface.surface_id != surface_id:
            raise ValueError(f"Context surface {surface_id} not found or mismatch")
        
        surface.household_summary = household_summary
        surface.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def update_domain(
        self,
        surface_id: str,
        domain_summary: Dict[str, Any],
    ) -> None:
        """Update domain summary in context surface."""
        surface = self.get_surface()
        if not surface or surface.surface_id != surface_id:
            raise ValueError(f"Context surface {surface_id} not found or mismatch")
        
        surface.domain_summary = domain_summary
        surface.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def update_governance(
        self,
        surface_id: str,
        governance_summary: Dict[str, Any],
    ) -> None:
        """Update governance summary in context surface."""
        surface = self.get_surface()
        if not surface or surface.surface_id != surface_id:
            raise ValueError(f"Context surface {surface_id} not found or mismatch")
        
        surface.governance_summary = governance_summary
        surface.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def set_reliability_mode(self, surface_id: str, mode: str) -> bool:
        """Set reliability mode."""
        surface = self.get_surface()
        if not surface or surface.surface_id != surface_id:
            return False
        
        surface.reliability_mode = mode
        surface.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return True
    
    def update_evidence(
        self,
        surface_id: str,
        evidence_summary: Dict[str, Any],
    ) -> None:
        """Update evidence summary in context surface."""
        surface = self.get_surface()
        if not surface or surface.surface_id != surface_id:
            raise ValueError(f"Context surface {surface_id} not found or mismatch")
        
        surface.evidence_summary = evidence_summary
        surface.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def update_guidance_posture(
        self,
        surface_id: str,
        guidance_posture: Dict[str, Any],
    ) -> None:
        """Update guidance posture in context surface."""
        surface = self.get_surface()
        if not surface or surface.surface_id != surface_id:
            raise ValueError(f"Context surface {surface_id} not found or mismatch")
        
        surface.guidance_posture = guidance_posture
        surface.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def pause_surface(self, surface_id: str) -> bool:
        """Pause the context surface."""
        surface = self.get_surface()
        if not surface or surface.surface_id != surface_id:
            return False
        
        surface.status = ContextSurfaceStatus.PAUSED.value
        surface.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return True
    
    def resume_surface(self, surface_id: str) -> bool:
        """Resume the context surface."""
        surface = self.get_surface()
        if not surface or surface.surface_id != surface_id:
            return False
        
        surface.status = ContextSurfaceStatus.ACTIVE.value
        surface.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return True
    
    def get_state_overview(self) -> Optional[Dict[str, Any]]:
        """Get a comprehensive state overview."""
        surface = self.get_surface()
        if not surface:
            return None
        
        return surface.get_state_overview()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manager state to dictionary."""
        return {
            "surface_count": 1 if self.current_surface else 0,
            "current_surface": self.current_surface.to_dict() if self.current_surface else None,
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_governance_view(governance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add operator context surface to governance view.
    
    This is purely additive — no migration required.
    """
    if "operator_context_available" not in governance_dict:
        governance_dict["operator_context_available"] = False
    if "operator_context_status" not in governance_dict:
        governance_dict["operator_context_status"] = None
    if "operator_context_timestamp" not in governance_dict:
        governance_dict["operator_context_timestamp"] = None
    return governance_dict


def integrate_with_operator_review(review_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add operator context surface to operator proposal review.
    
    This is purely additive — no migration required.
    """
    if "operator_context_summary" not in review_dict:
        review_dict["operator_context_summary"] = None
    if "reliability_mode" not in review_dict:
        review_dict["reliability_mode"] = ReliabilityMode.NORMAL.value
    return review_dict


def integrate_with_narrative(narrative_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add operator context awareness to narrative generation.
    
    This is purely additive — no migration required.
    """
    if "operator_context_available" not in narrative_dict:
        narrative_dict["operator_context_available"] = False
    if "operator_session_id" not in narrative_dict:
        narrative_dict["operator_session_id"] = None
    return narrative_dict


def integrate_with_adaptive_guidance(guidance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add operator context to adaptive guidance.
    
    This is purely additive — no migration required.
    """
    if "operator_context_available" not in guidance_dict:
        guidance_dict["operator_context_available"] = False
    if "current_reliability_mode" not in guidance_dict:
        guidance_dict["current_reliability_mode"] = ReliabilityMode.NORMAL.value
    if "guidance_state" not in guidance_dict:
        guidance_dict["guidance_state"] = None
    return guidance_dict


def integrate_with_longitudinal_patterns(patterns_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add operator context to longitudinal patterns.
    
    This is purely additive — no migration required.
    """
    if "operator_context" not in patterns_dict:
        patterns_dict["operator_context"] = None
    if "session_id" not in patterns_dict:
        patterns_dict["session_id"] = None
    return patterns_dict
