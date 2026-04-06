# model_assisted_not_model_dependent.py - WESLR v56: Model-Assisted Not Model-Dependent Hardening Layer
# Creates a governed model-assisted operation layer so WESLR can operate without model dependency
# using fallback chains, deterministic logic, and operator-assisted operation.
# Additive only, transparent, reversible, role-aware, non-manipulative.
# No repo drift (local to WESLR scope).

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from . import intervention_timing
from . import deployment_persona


# ============================================================================
# ENUMS
# ============================================================================


class ModelAvailability(str, Enum):
    """Model availability status."""
    AVAILABLE = "available"  # Model is available and functional
    DEGRADED = "degraded"  # Model available but limited
    UNAVAILABLE = "unavailable"  # Model not available
    UNKNOWN = "unknown"  # Model status unknown


class FallbackStrategy(str, Enum):
    """Fallback strategy when model unavailable."""
    OPERATOR_ASSISTED = "operator_assisted"  # Rely on operator guidance
    DETERMINISTIC = "deterministic"  # Use deterministic fallback logic
    CACHED = "cached"  # Use cached recommendations
    SAFETY_FIRST = "safety_first"  # Use safety-first fallback
    DEGRADED_MODE = "degraded_mode"  # Reduced functionality mode


class DegradedModeCapability(str, Enum):
    """Capabilities available in degraded mode."""
    NONE = "none"  # No capabilities
    EVALUATION = "evaluation"  # Can evaluate suggestions
    STORAGE = "storage"  # Can store and retrieve
    TIMING = "timing"  # Can evaluate timing
    ESCALATION = "escalation"  # Can handle escalation
    SAFETY = "safety"  # Can enforce safety constraints


class OperatorAssistedMode(str, Enum):
    """Mode for operator-assisted operation."""
    PASIVE = "pasive"  # Wait for operator prompt
    ACTIVE = "active"  # Proactively ask for guidance
    QUERY = "query"  # Query-based assistance


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class ModelStatus:
    """Current model availability status."""
    
    status: str = ModelAvailability.UNKNOWN.value
    last_check: str = ""
    confidence: float = 0.0
    degradation_reason: Optional[str] = None
    estimated_recovery_time: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "last_check": self.last_check,
            "confidence": self.confidence,
            "degradation_reason": self.degradation_reason,
            "estimated_recovery_time": self.estimated_recovery_time,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ModelStatus:
        return cls(**data)


@dataclass
class FallbackChain:
    """Chain of fallback strategies to attempt."""
    
    chain_id: str = "default"  # Unique identifier (default for backward compat)
    fallback_strategies: List[str] = field(default_factory=list)  # Ordered strategies
    default_strategy: str = FallbackStrategy.OPERATOR_ASSISTED.value
    fallback_timeout_seconds: int = 30  # Timeout for each fallback attempt
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "fallback_strategies": self.fallback_strategies,
            "default_strategy": self.default_strategy,
            "fallback_timeout_seconds": self.fallback_timeout_seconds,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FallbackChain:
        data["fallback_strategies"] = data.get("fallback_strategies", [])
        return cls(**data)


@dataclass
class DegradedModeState:
    """State of degraded mode operation."""
    
    enabled: bool = False
    capabilities: List[str] = field(default_factory=list)
    confidence_threshold: float = 0.3  # Minimum confidence to proceed
    safety_enforcement: bool = True  # Always enforce safety in degraded mode
    escalation_required: bool = True  # Escalate uncertain decisions
    
    # Cached state
    last_cached_recommendation: Optional[str] = None
    cached_at: Optional[str] = None
    cache_valid_until: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "capabilities": self.capabilities,
            "confidence_threshold": self.confidence_threshold,
            "safety_enforcement": self.safety_enforcement,
            "escalation_required": self.escalation_required,
            "last_cached_recommendation": self.last_cached_recommendation,
            "cached_at": self.cached_at,
            "cache_valid_until": self.cache_valid_until,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DegradedModeState:
        data["capabilities"] = data.get("capabilities", [])
        return cls(**data)


@dataclass
class OperatorAssistedContext:
    """Context for operator-assisted operation."""
    
    mode: str = OperatorAssistedMode.PASIVE.value
    pending_queries: List[str] = field(default_factory=list)  # Pending operator queries
    last_assistance_request: Optional[str] = None
    assistance_timeout_seconds: int = 60  # Timeout for operator response
    fallback_on_timeout: str = FallbackStrategy.DETERMINISTIC.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "pending_queries": self.pending_queries,
            "last_assistance_request": self.last_assistance_request,
            "assistance_timeout_seconds": self.assistance_timeout_seconds,
            "fallback_on_timeout": self.fallback_on_timeout,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OperatorAssistedContext:
        data["pending_queries"] = data.get("pending_queries", [])
        return cls(**data)


@dataclass
class ModelAssistedContext:
    """Complete context for model-assisted operation."""
    
    model_status: ModelStatus = field(default_factory=ModelStatus)
    fallback_chain: FallbackChain = field(default_factory=FallbackChain)
    degraded_mode_state: DegradedModeState = field(default_factory=DegradedModeState)
    operator_assisted_context: OperatorAssistedContext = field(default_factory=OperatorAssistedContext)
    
    # Timestamps
    last_model_check: str = ""
    last_fallback_triggered: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_status": self.model_status.to_dict(),
            "fallback_chain": self.fallback_chain.to_dict(),
            "degraded_mode_state": self.degraded_mode_state.to_dict(),
            "operator_assisted_context": self.operator_assisted_context.to_dict(),
            "last_model_check": self.last_model_check,
            "last_fallback_triggered": self.last_fallback_triggered,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ModelAssistedContext:
        data["model_status"] = ModelStatus.from_dict(data.get("model_status", {}))
        data["fallback_chain"] = FallbackChain.from_dict(data.get("fallback_chain", {}))
        data["degraded_mode_state"] = DegradedModeState.from_dict(data.get("degraded_mode_state", {}))
        data["operator_assisted_context"] = OperatorAssistedContext.from_dict(data.get("operator_assisted_context", {}))
        return cls(**data)


# ============================================================================
# MODEL-ASSISTED NOT MODEL-DEPENDENT ENGINE
# ============================================================================


class ModelAssistedNotModelDependentEngine:
    """Engine for model-assisted, not model-dependent operation."""
    
    def __init__(self):
        self.context: ModelAssistedContext = ModelAssistedContext()
        self.last_fallback_applied: Optional[FallbackStrategy] = None
        
        # Initialize default fallback chain
        self.set_fallback_chain(FallbackChain(chain_id="default"))
    
    def update_model_status(self, status: ModelAvailability, confidence: float = 0.0, 
                           degradation_reason: Optional[str] = None) -> None:
        """Update model availability status."""
        self.context.model_status = ModelStatus(
            status=status.value,
            last_check=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            confidence=confidence,
            degradation_reason=degradation_reason
        )
        self.context.last_model_check = self.context.model_status.last_check
    
    def get_current_model_status(self) -> ModelStatus:
        """Get current model status."""
        return self.context.model_status
    
    def get_fallback_chain(self) -> FallbackChain:
        """Get active fallback chain."""
        return self.context.fallback_chain
    
    def set_fallback_chain(self, chain: FallbackChain) -> None:
        """Set fallback chain."""
        self.context.fallback_chain = chain
    
    def get_next_fallback_strategy(self) -> FallbackStrategy:
        """Get next fallback strategy from chain."""
        strategies = self.context.fallback_chain.fallback_strategies
        if not strategies:
            return FallbackStrategy(self.context.fallback_chain.default_strategy)
        
        return FallbackStrategy(strategies[0])
    
    def trigger_fallback(self, reason: str) -> FallbackStrategy:
        """Trigger fallback and update context."""
        strategy = self.get_next_fallback_strategy()
        self.last_fallback_applied = strategy
        self.context.last_fallback_triggered = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        return strategy
    
    def enable_degraded_mode(self, capabilities: List[str] = None) -> None:
        """Enable degraded mode with specified capabilities."""
        self.context.degraded_mode_state.enabled = True
        self.context.degraded_mode_state.capabilities = capabilities or [
            DegradatedModeCapability.EVALUATION.value,
            DegradatedModeCapability.STORAGE.value,
            DegradatedModeCapability.TIMING.value
        ]
        self.context.degraded_mode_state.safety_enforcement = True
        self.context.degraded_mode_state.escalation_required = True
    
    def disable_degraded_mode(self) -> None:
        """Disable degraded mode."""
        self.context.degraded_mode_state.enabled = False
        self.context.degraded_mode_state.capabilities = []
    
    def is_degraded_mode_active(self) -> bool:
        """Check if degraded mode is active."""
        return self.context.degraded_mode_state.enabled
    
    def can_proceed_with_confidence(self, confidence: float) -> bool:
        """Check if confidence meets degraded mode threshold."""
        if not self.context.degraded_mode_state.enabled:
            return True  # Normal mode, any confidence ok
        
        return confidence >= self.context.degraded_mode_state.confidence_threshold
    
    def ensure_safety(self) -> bool:
        """Ensure safety constraints are met (always true in degraded mode)."""
        return self.context.degraded_mode_state.safety_enforcement
    
    def set_operator_assisted_mode(self, mode: str, query: Optional[str] = None) -> None:
        """Set operator-assisted operation mode."""
        self.context.operator_assisted_context.mode = mode
        
        if query:
            self.context.operator_assisted_context.pending_queries.append(query)
            self.context.operator_assisted_context.last_assistance_request = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def resolve_operator_query(self, query: str, response: str) -> bool:
        """Resolve a pending operator query."""
        if query not in self.context.operator_assisted_context.pending_queries:
            return False
        
        self.context.operator_assisted_context.pending_queries.remove(query)
        return True
    
    def get_pending_queries(self) -> List[str]:
        """Get pending operator queries."""
        return self.context.operator_assisted_context.pending_queries
    
    def check_fallback_requirements(self, confidence: float, safety_critical: bool = False) -> Dict[str, Any]:
        """Check if fallback requirements are met."""
        result = {
            "needs_fallback": False,
            "reason": [],
            "fallback_strategy": None
        }
        
        # Check model status
        if self.context.model_status.status == ModelAvailability.UNAVAILABLE.value:
            result["needs_fallback"] = True
            result["reason"].append("model_unavailable")
            result["fallback_strategy"] = FallbackStrategy.OPERATOR_ASSISTED
        elif self.context.model_status.status == ModelAvailability.DEGRADED.value:
            if confidence < 0.7:
                result["needs_fallback"] = True
                result["reason"].append("model_degraded_low_confidence")
                result["fallback_strategy"] = FallbackStrategy.DETERMINISTIC
        
        # Check degraded mode
        if self.context.degraded_mode_state.enabled:
            if not self.can_proceed_with_confidence(confidence):
                result["needs_fallback"] = True
                result["reason"].append("confidence_below_degraded_threshold")
                result["fallback_strategy"] = FallbackStrategy.SAFETY_FIRST
        
        # Safety-critical always requires fallback
        if safety_critical and not result["needs_fallback"]:
            result["needs_fallback"] = True
            result["reason"].append("safety_critical")
            result["fallback_strategy"] = FallbackStrategy.SAFETY_FIRST
        
        return result
    
    def get_operator_assisted_context(self) -> OperatorAssistedContext:
        """Get operator-assisted context."""
        return self.context.operator_assisted_context
    
    def get_active_context(self) -> ModelAssistedContext:
        """Get active model-assisted context."""
        return self.context


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ModelAvailability",
    "FallbackStrategy",
    "DegradatedModeCapability",
    "OperatorAssistedMode",
    "ModelStatus",
    "FallbackChain",
    "DegradedModeState",
    "OperatorAssistedContext",
    "ModelAssistedContext",
    "ModelAssistedNotModelDependentEngine",
]
