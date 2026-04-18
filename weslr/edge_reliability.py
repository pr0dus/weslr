"""Edge Reliability / Offline-First Layer (v22)

Prepares WESLR for degraded/offline/edge operation so the deterministic governed
core remains usable even when network/model/external sources are unavailable.

Architecture:
  - OperationMode enum — online, degraded, offline
  - EdgeReliabilityState — current availability of providers and capabilities
  - EdgeReliabilityEngine — assessment and status reporting
  - Integration hooks — governance and operator surfaces reflect reliability

Rules:
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - Operator-first (status visible to operators)
  - No runtime redesign unless proven necessary
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================================
# ENUMS
# ============================================================================


class OperationMode(str, Enum):
    """WESLR operation mode based on resource availability."""
    ONLINE = "online"              # All providers and external sources available
    DEGRADED = "degraded"          # Some providers unavailable, fallback active
    OFFLINE = "offline"            # No external sources, deterministic core only


class ProviderStatus(str, Enum):
    """Status of an external provider."""
    AVAILABLE = "available"
    UNREACHABLE = "unreachable"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"  # Available but with reduced capacity


class ExternalSourceStatus(str, Enum):
    """Status of an external data/source provider."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class ProviderAvailability:
    """Availability status of an external provider."""
    provider_type: str  # e.g., "llm", "api", "database", "storage"
    provider_name: str  # e.g., "openai", "claude", "local-llm"
    status: str = ProviderStatus.AVAILABLE.value
    last_check_at: Optional[str] = None
    error_message: Optional[str] = None
    degraded_threshold: Optional[float] = None  # 0.0-1.0, below this triggers degraded mode


@dataclass
class ExternalSourceAvailability:
    """Availability status of an external data/source provider."""
    source_type: str  # e.g., "filesystem", "git", "database", "http"
    source_name: str  # e.g., "workspace", "continuity", "evidence-store"
    status: str = ExternalSourceStatus.AVAILABLE.value
    last_check_at: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class EdgeReliabilityState:
    """Current state of WESLR edge reliability.
    
    Tracks what's available and what fallbacks are active.
    """
    operation_mode: str = OperationMode.ONLINE.value
    
    # Provider status
    providers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # External source status
    external_sources: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Deterministic fallback status
    deterministic_core_available: bool = True
    evidence_cache_available: bool = True
    continuity_cache_available: bool = True
    
    # Operator-visible status
    status_summary: str = "All systems online"
    available_capabilities: List[str] = field(default_factory=list)
    unavailable_capabilities: List[str] = field(default_factory=list)
    degraded_capabilities: List[str] = field(default_factory=list)
    
    # Timestamps
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    last_failure_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "operation_mode": self.operation_mode,
            "providers": self.providers,
            "external_sources": self.external_sources,
            "deterministic_core_available": self.deterministic_core_available,
            "evidence_cache_available": self.evidence_cache_available,
            "continuity_cache_available": self.continuity_cache_available,
            "status_summary": self.status_summary,
            "available_capabilities": self.available_capabilities,
            "unavailable_capabilities": self.unavailable_capabilities,
            "degraded_capabilities": self.degraded_capabilities,
            "checked_at": self.checked_at,
            "last_failure_at": self.last_failure_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EdgeReliabilityState:
        """Create from dictionary representation."""
        data["providers"] = data.get("providers", {})
        data["external_sources"] = data.get("external_sources", {})
        data["available_capabilities"] = data.get("available_capabilities", [])
        data["unavailable_capabilities"] = data.get("unavailable_capabilities", [])
        data["degraded_capabilities"] = data.get("degraded_capabilities", [])
        return cls(**data)
    
    def update_mode(self, new_mode: str) -> EdgeReliabilityState:
        """Update operation mode."""
        self.operation_mode = new_mode
        self.checked_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return self
    
    def update_status_summary(self, summary: str) -> EdgeReliabilityState:
        """Update status summary."""
        self.status_summary = summary
        return self
    
    def mark_provider_unavailable(self, provider_type: str, provider_name: str, error: str = "") -> EdgeReliabilityState:
        """Mark a provider as unavailable."""
        if provider_type not in self.providers:
            self.providers[provider_type] = {}
        self.providers[provider_type][provider_name] = {
            "status": ProviderStatus.UNAVAILABLE.value,
            "last_check_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "error_message": error,
        }
        self.last_failure_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return self
    
    def mark_provider_available(self, provider_type: str, provider_name: str) -> EdgeReliabilityState:
        """Mark a provider as available."""
        if provider_type not in self.providers:
            self.providers[provider_type] = {}
        self.providers[provider_type][provider_name] = {
            "status": ProviderStatus.AVAILABLE.value,
            "last_check_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        return self
    
    def mark_external_source_unavailable(self, source_type: str, source_name: str, error: str = "") -> EdgeReliabilityState:
        """Mark an external source as unavailable."""
        if source_type not in self.external_sources:
            self.external_sources[source_type] = {}
        self.external_sources[source_type][source_name] = {
            "status": ExternalSourceStatus.UNAVAILABLE.value,
            "last_check_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "error_message": error,
        }
        self.last_failure_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return self


# ============================================================================
# EDGE RELIABILITY ENGINE
# ============================================================================


class EdgeReliabilityEngine:
    """Engine for assessing and reporting WESLR edge reliability.
    
    Operates independently of external resources where possible.
    """
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        workspace_path: Optional[Path] = None,
    ):
        """Initialize edge reliability engine.
        
        Args:
            storage_path: Path to continuity/storage directory
            workspace_path: Path to workspace directory
        """
        self.storage_path = storage_path
        self.workspace_path = workspace_path or Path(__file__).resolve().parent.parent
        self.state = EdgeReliabilityState()
    
    def assess(self) -> EdgeReliabilityState:
        """Assess current edge reliability state.
        
        Returns the current reliability state without requiring network access.
        """
        # Reset state
        self.state = EdgeReliabilityState()
        
        # Check deterministic core (always available - it's local code)
        self.state.deterministic_core_available = True
        
        # Check evidence cache (local file system)
        evidence_cache_path = self.workspace_path / "continuity" / "evidence"
        if evidence_cache_path.exists() or evidence_cache_path.is_dir():
            self.state.evidence_cache_available = True
            self.state.available_capabilities.append("evidence_cache")
        else:
            self.state.evidence_cache_available = False
            self.state.unavailable_capabilities.append("evidence_cache")
        
        # Check continuity cache (local file system)
        continuity_cache_path = self.workspace_path / "continuity" / "snapshots"
        if continuity_cache_path.exists() or continuity_cache_path.is_dir():
            self.state.continuity_cache_available = True
            self.state.available_capabilities.append("continuity_cache")
        else:
            self.state.continuity_cache_available = False
            self.state.unavailable_capabilities.append("continuity_cache")
        
        # Check storage path if provided
        if self.storage_path and self.storage_path.exists():
            self.state.available_capabilities.append("storage")
        else:
            self.state.unavailable_capabilities.append("storage")
        
        # Determine overall mode
        if self.state.deterministic_core_available and self.state.evidence_cache_available:
            if self.state.continuity_cache_available:
                self.state.operation_mode = OperationMode.ONLINE.value
                self.state.status_summary = "All systems online - deterministic core + cache available"
            else:
                self.state.operation_mode = OperationMode.DEGRADED.value
                self.state.status_summary = "Degraded mode - deterministic core available, continuity limited"
        else:
            self.state.operation_mode = OperationMode.OFFLINE.value
            self.state.status_summary = "Offline mode - deterministic core only"
        
        # Update checked timestamp
        self.state.checked_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        return self.state
    
    def get_status_for_governance(self) -> Dict[str, Any]:
        """Get reliability status formatted for governance output."""
        state = self.state.to_dict()
        
        # Build capability summary
        capabilities = {
            "available": state.get("available_capabilities", []),
            "unavailable": state.get("unavailable_capabilities", []),
            "degraded": state.get("degraded_capabilities", []),
        }
        
        # Build provider status summary
        providers = state.get("providers", {})
        provider_summary = {}
        for ptype, pdict in providers.items():
            for pname, pstatus in pdict.items():
                provider_summary[f"{ptype}/{pname}"] = pstatus.get("status", "unknown")
        
        return {
            "operation_mode": state.get("operation_mode", OperationMode.ONLINE.value),
            "status_summary": state.get("status_summary", "Unknown"),
            "capabilities": capabilities,
            "providers": provider_summary,
            "external_sources": state.get("external_sources", {}),
            "deterministic_core_available": state.get("deterministic_core_available", True),
            "evidence_cache_available": state.get("evidence_cache_available", True),
            "continuity_cache_available": state.get("continuity_cache_available", True),
            "checked_at": state.get("checked_at", ""),
            "last_failure_at": state.get("last_failure_at", None),
        }
    
    def set_mode(self, mode: str) -> None:
        """Set operation mode manually (e.g., for testing or forced offline)."""
        self.state.operation_mode = mode
        self.state.checked_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Update capabilities based on mode
        if mode == OperationMode.OFFLINE.value:
            self.state.evidence_cache_available = False
            self.state.continuity_cache_available = False
            self.state.available_capabilities = ["deterministic_core"]
            self.state.unavailable_capabilities = ["external_providers", "external_sources"]
        elif mode == OperationMode.DEGRADED.value:
            self.state.available_capabilities = ["deterministic_core", "continuity_cache"]
            self.state.unavailable_capabilities = ["external_providers"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary."""
        return {
            "operation_mode": self.state.operation_mode,
            "providers": self.state.providers,
            "external_sources": self.state.external_sources,
            "deterministic_core_available": self.state.deterministic_core_available,
            "evidence_cache_available": self.state.evidence_cache_available,
            "continuity_cache_available": self.state.continuity_cache_available,
            "status_summary": self.state.status_summary,
            "available_capabilities": self.state.available_capabilities,
            "unavailable_capabilities": self.state.unavailable_capabilities,
            "degraded_capabilities": self.state.degraded_capabilities,
            "checked_at": self.state.checked_at,
            "last_failure_at": self.state.last_failure_at,
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_governance_view(governance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add reliability status to governance view.
    
    This is purely additive — no migration required.
    """
    if "reliability_status" not in governance_dict:
        governance_dict["reliability_status"] = None
    if "operation_mode" not in governance_dict:
        governance_dict["operation_mode"] = None
    if "offline_mode_explanation" not in governance_dict:
        governance_dict["offline_mode_explanation"] = None
    return governance_dict


def integrate_with_operator_review(review_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add reliability status to operator review.
    
    This is purely additive — no migration required.
    """
    if "operation_mode" not in review_dict:
        review_dict["operation_mode"] = None
    if "available_capabilities" not in review_dict:
        review_dict["available_capabilities"] = []
    if "unavailable_capabilities" not in review_dict:
        review_dict["unavailable_capabilities"] = []
    return review_dict
