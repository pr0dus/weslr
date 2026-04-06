# capability_boundary.py - WESLR v40: Capability / Permission Boundary Layer
# Creates a governed capability boundary layer so WESLR can explicitly know what each
# deployment role is permitted to recommend, plan, surface, or block.
# Additive only, transparent, reversible, role-based (not identity), non-manipulative.
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


class CapabilityType(str, Enum):
    """Types of capabilities WESLR can have."""
    # Informational
    READ_DATA = "read_data"
    READ_FILES = "read_files"
    READ_MEMORY = "read_memory"
    ANALYZE = "analyze"
    ANALYZE_CODE = "analyze_code"
    ANALYZE_HEALTH = "analyze_health"
    
    # Configuration changes
    CONFIGURE = "configure"
    UPDATE_CONFIG = "update_config"
    DELETE_CONFIG = "delete_config"
    
    # External system interaction
    API_CALL = "api_call"
    HTTP_REQUEST = "http_request"
    DATABASE_WRITE = "database_write"
    
    # System modification
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    SYSTEM_COMMAND = "system_command"
    
    # Actuation (high-risk)
    ACTUATE = "actuate"
    EXECUTE = "execute"
    
    # Autonomous actions (highest risk)
    AUTONOMOUS = "autonomous"
    
    # Planning and recommendation
    PLAN = "plan"
    RECOMMEND = "recommend"
    FORECAST = "forecast"
    
    # Governance
    SURFACE = "surface"  # Surface to operator
    BLOCK = "block"  # Block actions
    GATE = "gate"  # Gate execution
    AUDIT = "audit"
    
    OTHER = "other"


class CapabilityAction(str, Enum):
    """Allowed actions on capabilities."""
    ALLOW = "allow"
    RESTRICT = "restrict"
    PROHIBIT = "prohibit"
    APPROVAL_GATED = "approval_gated"
    DEGRADED = "degraded"  # Use limited capabilities in degraded mode


class CapabilityScope(str, Enum):
    """Scope of capability application."""
    GLOBAL = "global"  # Applies everywhere
    LOCAL = "local"  # Applies to local operations only
    EXTERNAL = "external"  # Applies to external systems
    INTERNAL = "internal"  # Applies to internal state only
    SURFACE = "surface"  # Applies to operator-facing surfaces
    EXECUTION = "execution"  # Applies to execution actions


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class CapabilityPermission:
    """Permission configuration for a capability."""
    
    capability: str  # CapabilityType.value
    action: str  # CapabilityAction.value
    scope: str = CapabilityScope.GLOBAL.value
    
    # Constraints
    max_frequency_hz: Optional[float] = None
    max_batch_size: Optional[int] = None
    requires_online: Optional[bool] = None
    max_latency_ms: Optional[int] = None
    
    # Approval requirements
    approval_required: bool = False
    approval_timeout_ms: int = 30000  # Default 30 seconds
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "capability": self.capability,
            "action": self.action,
            "scope": self.scope,
            "max_frequency_hz": self.max_frequency_hz,
            "max_batch_size": self.max_batch_size,
            "requires_online": self.requires_online,
            "max_latency_ms": self.max_latency_ms,
            "approval_required": self.approval_required,
            "approval_timeout_ms": self.approval_timeout_ms,
            "created_at": self.created_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CapabilityPermission:
        return cls(**data)
    
    def is_allowed(self) -> bool:
        """Check if this permission allows the action."""
        return self.action in [CapabilityAction.ALLOW.value, CapabilityAction.APPROVAL_GATED.value]
    
    def is_restricted(self) -> bool:
        """Check if this permission restricts the action."""
        return self.action == CapabilityAction.RESTRICT.value
    
    def is_prohibited(self) -> bool:
        """Check if this permission prohibits the action."""
        return self.action == CapabilityAction.PROHIBIT.value


@dataclass
class CapabilityBoundary:
    """Complete capability boundary for a deployment role."""
    
    boundary_id: str
    role: str  # DeploymentRole.value (from v39)
    
    # Capability permissions
    allowed_capabilities: List[Dict[str, Any]] = field(default_factory=list)
    restricted_capabilities: List[Dict[str, Any]] = field(default_factory=list)
    prohibited_capabilities: List[Dict[str, Any]] = field(default_factory=list)
    approval_gated_capabilities: List[Dict[str, Any]] = field(default_factory=list)
    
    # Degraded mode overrides
    degraded_allowed: List[str] = field(default_factory=list)
    degraded_restricted: List[str] = field(default_factory=list)
    degraded_prohibited: List[str] = field(default_factory=list)
    
    # Safety constraints
    max_concurrent_capabilities: int = 5
    max_frequency_per_minute: int = 60
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "boundary_id": self.boundary_id,
            "role": self.role,
            "allowed_capabilities": self.allowed_capabilities,
            "restricted_capabilities": self.restricted_capabilities,
            "prohibited_capabilities": self.prohibited_capabilities,
            "approval_gated_capabilities": self.approval_gated_capabilities,
            "degraded_allowed": self.degraded_allowed,
            "degraded_restricted": self.degraded_restricted,
            "degraded_prohibited": self.degraded_prohibited,
            "max_concurrent_capabilities": self.max_concurrent_capabilities,
            "max_frequency_per_minute": self.max_frequency_per_minute,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CapabilityBoundary:
        return cls(**data)
    
    def update(self, **kwargs) -> CapabilityBoundary:
        """Update boundary and refresh timestamp."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return self


# ============================================================================
# CAPABILITY BOUNDARY REGISTRY
# ============================================================================


def get_capability_boundary_registry() -> Dict[str, CapabilityBoundary]:
    """Get predefined capability boundary configurations.
    
    Returns a registry of standard capability boundaries per deployment role.
    """
    return {
        # Home & Family: Limited, cautious, high approval
        "home_family": CapabilityBoundary(
            boundary_id="home_family_v40",
            role="home_family",
            allowed_capabilities=[
                {"capability": CapabilityType.READ_DATA.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.READ_FILES.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.READ_MEMORY.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.ANALYZE.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.FORECAST.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.SURFACE.value, "action": CapabilityAction.ALLOW.value},
            ],
            restricted_capabilities=[
                {"capability": CapabilityType.API_CALL.value, "action": CapabilityAction.RESTRICT.value},
                {"capability": CapabilityType.HTTP_REQUEST.value, "action": CapabilityAction.RESTRICT.value},
            ],
            prohibited_capabilities=[
                {"capability": CapabilityType.EXECUTE.value, "action": CapabilityAction.PROHIBIT.value},
                {"capability": CapabilityType.ACTUATE.value, "action": CapabilityAction.PROHIBIT.value},
                {"capability": CapabilityType.FILE_WRITE.value, "action": CapabilityAction.PROHIBIT.value},
                {"capability": CapabilityType.SYSTEM_COMMAND.value, "action": CapabilityAction.PROHIBIT.value},
            ],
            approval_gated_capabilities=[
                {"capability": CapabilityType.AUTONOMOUS.value, "action": CapabilityAction.APPROVAL_GATED.value},
                {"capability": CapabilityType.PLAN.value, "action": CapabilityAction.APPROVAL_GATED.value},
                {"capability": CapabilityType.RECOMMEND.value, "action": CapabilityAction.APPROVAL_GATED.value},
            ],
            degraded_allowed=["read_data", "read_memory", "analyze"],
            degraded_restricted=["api_call", "http_request"],
            degraded_prohibited=["execute", "actuate", "autonomous"],
            max_concurrent_capabilities=3,
            max_frequency_per_minute=30,
        ),
        # Education: Balanced, exploratory
        "education": CapabilityBoundary(
            boundary_id="education_v40",
            role="education",
            allowed_capabilities=[
                {"capability": CapabilityType.READ_DATA.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.READ_FILES.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.READ_MEMORY.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.ANALYZE.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.ANALYZE_CODE.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.FORECAST.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.SURFACE.value, "action": CapabilityAction.ALLOW.value},
            ],
            restricted_capabilities=[
                {"capability": CapabilityType.API_CALL.value, "action": CapabilityAction.RESTRICT.value},
            ],
            prohibited_capabilities=[
                {"capability": CapabilityType.EXECUTE.value, "action": CapabilityAction.PROHIBIT.value},
                {"capability": CapabilityType.ACTUATE.value, "action": CapabilityAction.PROHIBIT.value},
                {"capability": CapabilityType.SYSTEM_COMMAND.value, "action": CapabilityAction.PROHIBIT.value},
            ],
            approval_gated_capabilities=[
                {"capability": CapabilityType.AUTONOMOUS.value, "action": CapabilityAction.APPROVAL_GATED.value},
                {"capability": CapabilityType.PLAN.value, "action": CapabilityAction.APPROVAL_GATED.value},
                {"capability": CapabilityType.FILE_WRITE.value, "action": CapabilityAction.APPROVAL_GATED.value},
            ],
            degraded_allowed=["read_data", "read_files", "analyze", "analyze_code"],
            degraded_restricted=["api_call"],
            degraded_prohibited=["execute", "actuate", "autonomous"],
            max_concurrent_capabilities=4,
            max_frequency_per_minute=45,
        ),
        # Hospitals & Medicine: Highly restricted, maximum safety
        "hospitals_medicine": CapabilityBoundary(
            boundary_id="hospitals_medicine_v40",
            role="hospitals_medicine",
            allowed_capabilities=[
                {"capability": CapabilityType.READ_DATA.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.READ_FILES.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.READ_MEMORY.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.ANALYZE_HEALTH.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.AUDIT.value, "action": CapabilityAction.ALLOW.value},
            ],
            restricted_capabilities=[
                {"capability": CapabilityType.ANALYZE.value, "action": CapabilityAction.RESTRICT.value},
                {"capability": CapabilityType.ANALYZE_CODE.value, "action": CapabilityAction.RESTRICT.value},
            ],
            prohibited_capabilities=[
                {"capability": CapabilityType.EXECUTE.value, "action": CapabilityAction.PROHIBIT.value},
                {"capability": CapabilityType.ACTUATE.value, "action": CapabilityAction.PROHIBIT.value},
                {"capability": CapabilityType.AUTONOMOUS.value, "action": CapabilityAction.PROHIBIT.value},
                {"capability": CapabilityType.API_CALL.value, "action": CapabilityAction.PROHIBIT.value},
                {"capability": CapabilityType.HTTP_REQUEST.value, "action": CapabilityAction.PROHIBIT.value},
                {"capability": CapabilityType.FILE_WRITE.value, "action": CapabilityAction.PROHIBIT.value},
                {"capability": CapabilityType.SYSTEM_COMMAND.value, "action": CapabilityAction.PROHIBIT.value},
            ],
            approval_gated_capabilities=[
                {"capability": CapabilityType.FORECAST.value, "action": CapabilityAction.APPROVAL_GATED.value},
                {"capability": CapabilityType.SURFACE.value, "action": CapabilityAction.APPROVAL_GATED.value},
            ],
            degraded_allowed=["read_data", "read_memory", "audit"],
            degraded_restricted=["analyze_health"],
            degraded_prohibited=["execute", "actuate", "autonomous", "api_call"],
            max_concurrent_capabilities=1,
            max_frequency_per_minute=10,
        ),
        # Science & Research: Expanded, exploratory
        "science_research": CapabilityBoundary(
            boundary_id="science_research_v40",
            role="science_research",
            allowed_capabilities=[
                {"capability": CapabilityType.READ_DATA.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.READ_FILES.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.READ_MEMORY.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.ANALYZE.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.ANALYZE_CODE.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.ANALYZE_HEALTH.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.FORECAST.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.SURFACE.value, "action": CapabilityAction.ALLOW.value},
            ],
            restricted_capabilities=[],
            prohibited_capabilities=[
                {"capability": CapabilityType.EXECUTE.value, "action": CapabilityAction.PROHIBIT.value},
                {"capability": CapabilityType.ACTUATE.value, "action": CapabilityAction.PROHIBIT.value},
            ],
            approval_gated_capabilities=[
                {"capability": CapabilityType.AUTONOMOUS.value, "action": CapabilityAction.APPROVAL_GATED.value},
                {"capability": CapabilityType.PLAN.value, "action": CapabilityAction.APPROVAL_GATED.value},
                {"capability": CapabilityType.API_CALL.value, "action": CapabilityAction.APPROVAL_GATED.value},
                {"capability": CapabilityType.DATABASE_WRITE.value, "action": CapabilityAction.APPROVAL_GATED.value},
            ],
            degraded_allowed=["read_data", "read_files", "analyze", "analyze_code", "analyze_health", "forecast"],
            degraded_restricted=["api_call"],
            degraded_prohibited=["execute", "actuate", "autonomous"],
            max_concurrent_capabilities=6,
            max_frequency_per_minute=120,
        ),
        # Industry: Operational, prescriptive
        "industry": CapabilityBoundary(
            boundary_id="industry_v40",
            role="industry",
            allowed_capabilities=[
                {"capability": CapabilityType.READ_DATA.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.READ_FILES.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.READ_MEMORY.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.ANALYZE.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.ANALYZE_HEALTH.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.PLAN.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.RECOMMEND.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.SURFACE.value, "action": CapabilityAction.ALLOW.value},
            ],
            restricted_capabilities=[
                {"capability": CapabilityType.API_CALL.value, "action": CapabilityAction.RESTRICT.value},
            ],
            prohibited_capabilities=[
                {"capability": CapabilityType.EXECUTE.value, "action": CapabilityAction.PROHIBIT.value},
                {"capability": CapabilityType.AUTONOMOUS.value, "action": CapabilityAction.PROHIBIT.value},
            ],
            approval_gated_capabilities=[
                {"capability": CapabilityType.ACTUATE.value, "action": CapabilityAction.APPROVAL_GATED.value},
                {"capability": CapabilityType.SYSTEM_COMMAND.value, "action": CapabilityAction.APPROVAL_GATED.value},
                {"capability": CapabilityType.DATABASE_WRITE.value, "action": CapabilityAction.APPROVAL_GATED.value},
            ],
            degraded_allowed=["read_data", "read_memory", "analyze", "plan", "recommend"],
            degraded_restricted=["api_call", "database_write"],
            degraded_prohibited=["execute", "actuate", "autonomous"],
            max_concurrent_capabilities=4,
            max_frequency_per_minute=60,
        ),
        # Aerospace & Long-Mission: Autonomous with restrictions
        "aerospace_long_mission": CapabilityBoundary(
            boundary_id="aerospace_long_mission_v40",
            role="aerospace_long_mission",
            allowed_capabilities=[
                {"capability": CapabilityType.READ_DATA.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.READ_FILES.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.READ_MEMORY.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.ANALYZE.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.ANALYZE_HEALTH.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.FORECAST.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.PLAN.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.RECOMMEND.value, "action": CapabilityAction.ALLOW.value},
                {"capability": CapabilityType.AUDIT.value, "action": CapabilityAction.ALLOW.value},
            ],
            restricted_capabilities=[
                {"capability": CapabilityType.API_CALL.value, "action": CapabilityAction.RESTRICT.value},
                {"capability": CapabilityType.HTTP_REQUEST.value, "action": CapabilityAction.RESTRICT.value},
            ],
            prohibited_capabilities=[
                {"capability": CapabilityType.EXECUTE.value, "action": CapabilityAction.PROHIBIT.value},
            ],
            approval_gated_capabilities=[
                {"capability": CapabilityType.AUTONOMOUS.value, "action": CapabilityAction.APPROVAL_GATED.value},
                {"capability": CapabilityType.ACTUATE.value, "action": CapabilityAction.APPROVAL_GATED.value},
                {"capability": CapabilityType.FILE_WRITE.value, "action": CapabilityAction.APPROVAL_GATED.value},
            ],
            degraded_allowed=["read_data", "read_files", "read_memory", "analyze", "analyze_health", "forecast", "plan", "recommend", "audit"],
            degraded_restricted=["api_call", "http_request"],
            degraded_prohibited=["execute", "autonomous"],
            max_concurrent_capabilities=3,
            max_frequency_per_minute=30,
        ),
    }


# ============================================================================
# CAPABILITY BOUNDARY ENGINE
# ============================================================================


class CapabilityBoundaryEngine:
    """Engine for managing capability boundaries and permission enforcement.
    
    Provides transparent, reversible capability-based boundary enforcement.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize capability boundary engine."""
        self.storage_path = storage_path or "/data/data/com.termux/files/home/.openclaw/workspace/weslr/capability_boundary/"
        self.boundaries: Dict[str, CapabilityBoundary] = {}
        self.active_boundaries: Dict[str, str] = {}  # context_id -> boundary_id
        self._load_boundaries()
        self._ensure_storage_exists()
    
    def _load_boundaries(self) -> None:
        """Load boundaries from registry."""
        registry = get_capability_boundary_registry()
        self.boundaries = registry
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def get_boundary(self, role: str) -> Optional[CapabilityBoundary]:
        """Get capability boundary by role."""
        return self.boundaries.get(role)
    
    def get_default_boundary(self) -> CapabilityBoundary:
        """Get default capability boundary (home_family)."""
        default_role = "home_family"
        if default_role not in self.boundaries:
            raise ValueError(f"Default boundary for role '{default_role}' not found")
        return self.boundaries[default_role]
    
    def set_active_boundary(self, context_id: str, role: str) -> str:
        """Set active capability boundary for context."""
        if role not in self.boundaries:
            role = "home_family"  # Fallback
        self.active_boundaries[context_id] = role
        return role
    
    def get_active_boundary(self, context_id: str) -> Optional[CapabilityBoundary]:
        """Get active capability boundary for context."""
        role = self.active_boundaries.get(context_id)
        if not role:
            return self.get_default_boundary()
        return self.get_boundary(role)
    
    def check_capability(self, capability: str, action: str, context_id: str) -> Dict[str, Any]:
        """Check if a capability action is permitted for context.
        
        Returns result with:
        - permitted: bool
        - reason: str
        - boundary_info: dict
        """
        boundary = self.get_active_boundary(context_id)
        if not boundary:
            return {
                "permitted": False,
                "reason": "No active boundary",
                "boundary_info": {},
            }
        
        # Check if capability is explicitly permitted (for ALLOW action)
        for cap in boundary.allowed_capabilities:
            if cap.get("capability") == capability and cap.get("action") == CapabilityAction.ALLOW.value:
                if action == CapabilityAction.ALLOW.value:
                    return {
                        "permitted": True,
                        "reason": "Capability explicitly allowed",
                        "boundary_info": boundary.to_dict(),
                    }
        
        # Check if capability is restricted
        for cap in boundary.allowed_capabilities:
            if cap.get("capability") == capability and cap.get("action") == CapabilityAction.ALLOW.value:
                return {
                    "permitted": True,
                    "reason": "Capability explicitly allowed",
                    "boundary_info": boundary.to_dict(),
                }
        
        # Check if capability is restricted
        for cap in boundary.restricted_capabilities:
            if cap.get("capability") == capability:
                return {
                    "permitted": False,
                    "reason": f"Capability restricted: {capability}",
                    "boundary_info": boundary.to_dict(),
                }
        
        # Check if capability is prohibited
        for cap in boundary.prohibited_capabilities:
            if cap.get("capability") == capability:
                return {
                    "permitted": False,
                    "reason": f"Capability prohibited: {capability}",
                    "boundary_info": boundary.to_dict(),
                }
        
        # Check if capability is approval-gated
        for cap in boundary.approval_gated_capabilities:
            if cap.get("capability") == capability:
                return {
                    "permitted": False,
                    "reason": f"Capability requires approval: {capability}",
                    "boundary_info": boundary.to_dict(),
                    "requires_approval": True,
                }
        
        # Default: not permitted unless explicitly allowed
        return {
            "permitted": False,
            "reason": "Capability not explicitly permitted",
            "boundary_info": boundary.to_dict(),
        }
    
    def get_degraded_boundary(self, base_boundary: CapabilityBoundary) -> CapabilityBoundary:
        """Get degraded mode boundary from base boundary."""
        degraded = CapabilityBoundary(
            boundary_id=base_boundary.boundary_id + "_degraded",
            role=base_boundary.role,
            allowed_capabilities=[
                {"capability": c, "action": CapabilityAction.ALLOW.value}
                for c in base_boundary.degraded_allowed
            ],
            restricted_capabilities=[
                {"capability": c, "action": CapabilityAction.RESTRICT.value}
                for c in base_boundary.degraded_restricted
            ],
            prohibited_capabilities=[
                {"capability": c, "action": CapabilityAction.PROHIBIT.value}
                for c in base_boundary.degraded_prohibited
            ],
            approval_gated_capabilities=[
                {"capability": c, "action": CapabilityAction.APPROVAL_GATED.value}
                for c in base_boundary.degraded_prohibited
            ],
            degraded_allowed=base_boundary.degraded_allowed,
            degraded_restricted=base_boundary.degraded_restricted,
            degraded_prohibited=base_boundary.degraded_prohibited,
            max_concurrent_capabilities=max(1, base_boundary.max_concurrent_capabilities // 2),
            max_frequency_per_minute=max(5, base_boundary.max_frequency_per_minute // 2),
        )
        return degraded
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary."""
        return {
            "boundary_count": len(self.boundaries),
            "active_boundary_count": len(self.active_boundaries),
            "boundaries": {k: v.to_dict() for k, v in self.boundaries.items()},
            "active_boundaries": self.active_boundaries,
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_deployment_persona(
    persona_dict: Dict[str, Any],
    boundary_engine: CapabilityBoundaryEngine = None,
    context_id: str = None,
) -> Dict[str, Any]:
    """Add capability boundary context to deployment persona.
    
    This is purely additive — no migration required.
    
    v40: Role-based capability boundaries influence safety and action permissions.
    """
    if "capability_boundary_context" not in persona_dict:
        persona_dict["capability_boundary_context"] = None
    
    if boundary_engine and context_id:
        try:
            boundary = boundary_engine.get_active_boundary(context_id)
            if boundary:
                persona_dict["capability_boundary_context"] = {
                    "boundary_id": boundary.boundary_id,
                    "allowed_count": len(boundary.allowed_capabilities),
                    "restricted_count": len(boundary.restricted_capabilities),
                    "prohibited_count": len(boundary.prohibited_capabilities),
                    "approval_gated_count": len(boundary.approval_gated_capabilities),
                }
        except Exception:
            pass  # Silent fallback to default
    
    return persona_dict


def integrate_with_safety_contract(
    safety_dict: Dict[str, Any],
    boundary_engine: CapabilityBoundaryEngine = None,
    context_id: str = None,
) -> Dict[str, Any]:
    """Add capability boundary context to safety contract.
    
    This is purely additive — no migration required.
    
    v40: Capability boundaries influence safety action permissions.
    """
    if "capability_boundary_context" not in safety_dict:
        safety_dict["capability_boundary_context"] = None
    
    if boundary_engine and context_id:
        try:
            boundary = boundary_engine.get_active_boundary(context_id)
            if boundary:
                safety_dict["capability_boundary_context"] = {
                    "boundary_id": boundary.boundary_id,
                    "max_concurrent_capabilities": boundary.max_concurrent_capabilities,
                    "max_frequency_per_minute": boundary.max_frequency_per_minute,
                }
        except Exception:
            pass  # Silent fallback to default
    
    return safety_dict


def integrate_with_proof_gate(
    proof_dict: Dict[str, Any],
    boundary_engine: CapabilityBoundaryEngine = None,
    context_id: str = None,
) -> Dict[str, Any]:
    """Add capability boundary context to proof gate.
    
    This is purely additive — no migration required.
    
    v40: Capability boundaries influence execution eligibility.
    """
    if "capability_boundary_context" not in proof_dict:
        proof_dict["capability_boundary_context"] = None
    
    if boundary_engine and context_id:
        try:
            boundary = boundary_engine.get_active_boundary(context_id)
            if boundary:
                proof_dict["capability_boundary_context"] = {
                    "boundary_id": boundary.boundary_id,
                    "prohibited_count": len(boundary.prohibited_capabilities),
                }
        except Exception:
            pass  # Silent fallback to default
    
    return proof_dict


def integrate_with_governance_surface(
    governance_dict: Dict[str, Any],
    boundary_engine: CapabilityBoundaryEngine = None,
    context_id: str = None,
) -> Dict[str, Any]:
    """Add capability boundary context to governance surface.
    
    This is purely additive — no migration required.
    
    v40: Capability boundaries influence surface visibility and approval requirements.
    """
    if "capability_boundary_context" not in governance_dict:
        governance_dict["capability_boundary_context"] = None
    
    if boundary_engine and context_id:
        try:
            boundary = boundary_engine.get_active_boundary(context_id)
            if boundary:
                governance_dict["capability_boundary_context"] = {
                    "boundary_id": boundary.boundary_id,
                    "approval_gated_count": len(boundary.approval_gated_capabilities),
                    "prohibited_count": len(boundary.prohibited_capabilities),
                }
        except Exception:
            pass  # Silent fallback to default
    
    return governance_dict
