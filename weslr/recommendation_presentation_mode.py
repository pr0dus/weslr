# recommendation_presentation_mode.py - WESLR v53: Recommendation Presentation Mode Layer
# Creates a governed presentation mode layer so WESLR can adapt recommendation presentation
# to context, audience, domain, role, strictness needs, and explanation depth.
# Additive only, transparent, reversible, role-aware, non-manipulative.
# No repo drift (local to WESLR scope).

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from . import recommendation_delivery


# ============================================================================
# ENUMS
# ============================================================================


class PresentationContext(str, Enum):
    """Context in which recommendation is presented."""
    OPERATOR_DIRECT = "operator_direct"  # Direct operator interaction
    OPERATOR_REPORT = "operator_report"  # Operator report / dashboard
    SYSTEM_INTEGRATION = "system_integration"  # System-to-system integration
    AUDIT_COMPLIANCE = "audit_compliance"  # Audit or compliance review
    DEBUG_ANALYSIS = "debug_analysis"  # Development/debug analysis


class PresentationMode(str, Enum):
    """Presentation mode for recommendation output."""
    STANDARD = "standard"  # Normal presentation
    SUMMARY = "summary"  # Brief summary only
    DETAILED = "detailed"  # Full detail with explanations
    STRUCTURED = "structured"  # Structured format (JSON/YAML)
    VISUAL = "visual"  # Visual or graphical representation
    NARRATIVE = "narrative"  # Story-driven narrative


class ContextualAdaptation(str, Enum):
    """Adaptation strategy based on context."""
    NONE = "none"  # No adaptation
    AUTOMATIC = "automatic"  # Automatic adaptation based on context
    MANUAL_OVERRIDE = "manual_override"  # Manual override of automatic
    HYBRID = "hybrid"  # Automatic with manual override support


class ToneStrategy(str, Enum):
    """Tone strategy for presentation."""
    NEUTRAL = "neutral"  # Neutral, professional tone
    SUPPORTIVE = "supportive"  # Supportive, reassuring tone
    DIRECT = "direct"  # Direct, clear tone
    FORMAL = "formal"  # Formal, official tone
    CASUAL = "casual"  # Casual, approachable tone


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class PresentationConfiguration:
    """Configuration for presentation mode of a recommendation."""
    
    context: str = PresentationContext.OPERATOR_DIRECT.value
    mode: str = PresentationMode.STANDARD.value
    contextual_adaptation: str = ContextualAdaptation.AUTOMATIC.value
    tone_strategy: str = ToneStrategy.NEUTRAL.value
    
    # Adaptation targets
    target_audience: Optional[str] = None
    target_domain: Optional[str] = None
    target_role: Optional[str] = None
    target_strictness: Optional[str] = None
    
    # Delivery configuration override (extends recommendation_delivery)
    delivery_config: Optional[Dict[str, Any]] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    created_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "context": self.context,
            "mode": self.mode,
            "contextual_adaptation": self.contextual_adaptation,
            "tone_strategy": self.tone_strategy,
            "target_audience": self.target_audience,
            "target_domain": self.target_domain,
            "target_role": self.target_role,
            "target_strictness": self.target_strictness,
            "delivery_config": self.delivery_config,
            "created_at": self.created_at,
            "created_by": self.created_by,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PresentationConfiguration:
        return cls(
            context=data.get("context", cls.__dataclass_fields__["context"].default),
            mode=data.get("mode", cls.__dataclass_fields__["mode"].default),
            contextual_adaptation=data.get("contextual_adaptation", cls.__dataclass_fields__["contextual_adaptation"].default),
            tone_strategy=data.get("tone_strategy", cls.__dataclass_fields__["tone_strategy"].default),
            target_audience=data.get("target_audience"),
            target_domain=data.get("target_domain"),
            target_role=data.get("target_role"),
            target_strictness=data.get("target_strictness"),
            delivery_config=data.get("delivery_config"),
            created_at=data.get("created_at", cls().created_at),
            created_by=data.get("created_by"),
        )
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> PresentationConfiguration:
        return cls.from_dict(json.loads(json_str))


@dataclass
class PresentationModeTransition:
    """Represents a transition from one presentation mode to another."""
    
    from_mode: str
    to_mode: str
    context: str = PresentationContext.OPERATOR_DIRECT.value
    reason: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    operator: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_mode": self.from_mode,
            "to_mode": self.to_mode,
            "context": self.context,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "operator": self.operator,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PresentationModeTransition:
        return cls(
            from_mode=data["from_mode"],
            to_mode=data["to_mode"],
            context=data.get("context", cls.__dataclass_fields__["context"].default),
            reason=data.get("reason"),
            timestamp=data.get("timestamp", cls().timestamp),
            operator=data.get("operator"),
        )


# ============================================================================
# PRESENTATION MODE ENGINE
# ============================================================================


class PresentationModeEngine:
    """Engine for managing presentation mode transitions and configuration."""
    
    def __init__(self):
        self.current_mode: PresentationConfiguration = PresentationConfiguration()
        self.mode_history: List[PresentationModeTransition] = []
    
    def set_mode(self, config: PresentationConfiguration, reason: Optional[str] = None) -> None:
        """Set a new presentation mode, recording the transition."""
        transition = PresentationModeTransition(
            from_mode=self.current_mode.mode,
            to_mode=config.mode,
            context=config.context,
            reason=reason,
            operator=None,  # Will be set by operator layer if available
        )
        self.mode_history.append(transition)
        self.current_mode = config
    
    def adapt_to_context(self, context: str, reason: Optional[str] = None) -> None:
        """Automatically adapt presentation mode to context."""
        # Define context-to-mode mapping
        context_mapping = {
            PresentationContext.OPERATOR_REPORT.value: {"mode": PresentationMode.SUMMARY.value},
            PresentationContext.SYSTEM_INTEGRATION.value: {"mode": PresentationMode.STRUCTURED.value},
            PresentationContext.AUDIT_COMPLIANCE.value: {"mode": PresentationMode.DETAILED.value, "tone_strategy": ToneStrategy.FORMAL.value},
            PresentationContext.DEBUG_ANALYSIS.value: {"mode": PresentationMode.DETAILED.value, "tone_strategy": ToneStrategy.NEUTRAL.value},
        }
        
        if context in context_mapping:
            mapping = context_mapping[context]
            config = self.current_mode
            config.mode = mapping.get("mode", config.mode)
            if "tone_strategy" in mapping:
                config.tone_strategy = mapping["tone_strategy"]
            self.set_mode(config, f"Auto-adapt to {context}: {reason}")
    
    def get_current_mode(self) -> PresentationConfiguration:
        """Get current presentation mode configuration."""
        return self.current_mode
    
    def get_mode_history(self) -> List[PresentationModeTransition]:
        """Get mode transition history."""
        return self.mode_history
    
    def export_config(self) -> Dict[str, Any]:
        """Export current mode configuration for external use."""
        config = self.current_mode
        config.delivery_config = config.delivery_config or {}
        return config.to_dict()


# ============================================================================
# PRESENTATION MODE APPLIER
# ============================================================================


class PresentationModeApplier:
    """Applier for presentation mode to recommendation content."""
    
    def __init__(self, engine: PresentationModeEngine):
        self.engine = engine
    
    def apply_to_content(self, content: Dict[str, Any], delivery_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Apply presentation mode to recommendation content."""
        current_mode = self.engine.get_current_mode()
        
        # Build result with presentation mode metadata
        result = {
            "presentation_mode": {
                "context": current_mode.context,
                "mode": current_mode.mode,
                "contextual_adaptation": current_mode.contextual_adaptation,
                "tone_strategy": current_mode.tone_strategy,
                "target_audience": current_mode.target_audience,
                "target_domain": current_mode.target_domain,
                "target_role": current_mode.target_role,
                "target_strictness": current_mode.target_strictness,
            },
            "delivery_config": current_mode.delivery_config or {},
            "content": content,
        }
        
        # Apply delivery config if provided or from presentation mode
        if delivery_config:
            result["delivery_config"] = delivery_config
        elif current_mode.delivery_config:
            result["delivery_config"] = current_mode.delivery_config
        
        return result
    
    def get_adapted_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Get content with automatic context adaptation applied."""
        self.engine.adapt_to_context(self.engine.get_current_mode().context)
        return self.apply_to_content(content)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "PresentationContext",
    "PresentationMode",
    "ContextualAdaptation",
    "ToneStrategy",
    "PresentationConfiguration",
    "PresentationModeTransition",
    "PresentationModeEngine",
    "PresentationModeApplier",
]
