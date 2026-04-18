# recommendation_delivery.py - WESLR v52: Recommendation Delivery / Presentation Mode Layer
# Creates a governed delivery layer so WESLR can present the same final decision differently
# depending on audience, domain, role, strictness needs, degraded mode, and explanation depth.
# Additive only, transparent, reversible, role-aware, non-manipulative.
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


class DeliveryAudience(str, Enum):
    """Target audience for delivery."""
    OPERATOR = "operator"  # Human operator
    SYSTEM = "system"  # Automated systems
    AUDIT = "audit"  # Compliance/audit systems
    DEBUG = "debug"  # Development/debug purposes


class DeliveryMode(str, Enum):
    """Delivery mode for presentation."""
    STANDARD = "standard"  # Normal presentation
    SUMMARY = "summary"  # Brief summary only
    DETAILED = "detailed"  # Full detail with explanations
    ESCALATION = "escalation"  # Escalation handoff format
    DEGRADED = "degraded"  # Degraded mode presentation


class ExplanationDepth(str, Enum):
    """Depth of explanation to provide."""
    NONE = "none"  # No explanation
    MINIMAL = "minimal"  # Very brief explanation
    STANDARD = "standard"  # Balanced explanation
    ENHANCED = "enhanced"  # Detailed reasoning
    EXHAUSTIVE = "exhaustive"  # Multiple angles, chain of thought


class PhrasingStrictness(str, Enum):
    """Strictness of phrasing/tone."""
    SOFT = "soft"  # Gentle, reassuring tone
    STANDARD = "standard"  # Neutral, professional tone
    STRICT = "strict"  # Direct, firm tone
    MAXIMUM = "maximum"  # Urgent, high-alert tone


class CautionTone(str, Enum):
    """Caution level in presentation."""
    NONE = "none"  # No caution indicators
    MINIMAL = "minimal"  # Subtle caution indicators
    NORMAL = "normal"  # Standard caution indicators
    ELEVATED = "elevated"  # Prominent caution indicators
    MAXIMUM = "maximum"  # Maximum caution indicators


class HandoffFormat(str, Enum):
    """Format for handoff/escalation."""
    BRIEF = "brief"  # Concise handoff
    COMPLETE = "complete"  # Full context handoff
    STRUCTURED = "structured"  # Structured template handoff


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class DeliveryConfiguration:
    """Configuration for delivery of a recommendation."""
    
    audience: str = DeliveryAudience.OPERATOR.value
    mode: str = DeliveryMode.STANDARD.value
    verbosity: int = 5  # 0-10 scale
    explanation_depth: str = ExplanationDepth.STANDARD.value
    phrasing_strictness: str = PhrasingStrictness.STANDARD.value
    caution_tone: str = CautionTone.NORMAL.value
    summary_mode: bool = False  # True for summary-only output
    degraded_mode: bool = False  # True for degraded mode presentation
    escalation_handoff: bool = False  # True for handoff/escalation presentation
    handoff_format: str = HandoffFormat.BRIEF.value
    
    # Context for rendering
    deployment_role: Optional[str] = None
    domain: Optional[str] = None
    strictness_level: Optional[str] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    created_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "audience": self.audience,
            "mode": self.mode,
            "verbosity": self.verbosity,
            "explanation_depth": self.explanation_depth,
            "phrasing_strictness": self.phrasing_strictness,
            "caution_tone": self.caution_tone,
            "summary_mode": self.summary_mode,
            "degraded_mode": self.degraded_mode,
            "escalation_handoff": self.escalation_handoff,
            "handoff_format": self.handoff_format,
            "deployment_role": self.deployment_role,
            "domain": self.domain,
            "strictness_level": self.strictness_level,
            "created_at": self.created_at,
            "created_by": self.created_by,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DeliveryConfiguration:
        data.setdefault("created_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        data.setdefault("verbosity", 5)
        return cls(**data)
    
    def is_escalation_required(self) -> bool:
        """Check if this delivery mode requires escalation."""
        return self.mode == DeliveryMode.ESCALATION.value or self.escalation_handoff
    
    def get_verbosity_multiplier(self) -> float:
        """Get multiplier for verbosity scaling."""
        # Lower verbosity = shorter output
        return self.verbosity / 10.0
    
    def get_explanation_required(self) -> bool:
        """Check if explanation is required based on strictness and mode."""
        if self.summary_mode:
            return False
        if self.explanation_depth == ExplanationDepth.NONE.value:
            return False
        return True


@dataclass
class RenderedDelivery:
    """A rendered delivery output for a recommendation."""
    
    delivery_id: str
    recommendation_id: str
    delivery_configuration: Dict[str, Any]
    
    # Rendered content
    summary: Optional[str] = None
    detailed: Optional[str] = None
    explanation: Optional[str] = None
    caution_note: Optional[str] = None
    handoff_context: Optional[str] = None
    
    # Metadata
    rendered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    rendered_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "delivery_id": self.delivery_id,
            "recommendation_id": self.recommendation_id,
            "delivery_configuration": self.delivery_configuration,
            "summary": self.summary,
            "detailed": self.detailed,
            "explanation": self.explanation,
            "caution_note": self.caution_note,
            "handoff_context": self.handoff_context,
            "rendered_at": self.rendered_at,
            "rendered_by": self.rendered_by,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RenderedDelivery:
        data.setdefault("rendered_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        return cls(**data)
    
    def get_summary_output(self) -> str:
        """Get the summary output for display."""
        parts = []
        if self.summary:
            parts.append(self.summary)
        if self.caution_note:
            parts.append(f"[CAUTION: {self.caution_note}]")
        return "\n".join(parts) if parts else ""
    
    def get_full_output(self) -> str:
        """Get the full output including all content."""
        parts = []
        if self.summary:
            parts.append(f"SUMMARY:\n{self.summary}\n")
        if self.detailed:
            parts.append(f"DETAILED:\n{self.detailed}\n")
        if self.explanation:
            parts.append(f"EXPLANATION:\n{self.explanation}\n")
        if self.caution_note:
            parts.append(f"[CAUTION: {self.caution_note}]\n")
        if self.handoff_context:
            parts.append(f"HANDOFF CONTEXT:\n{self.handoff_context}\n")
        return "\n".join(parts) if parts else ""


# ============================================================================
# RECOMMENDATION DELIVERY COMPOSER
# ============================================================================


class RecommendationDeliveryComposer:
    """Engine for composing delivery of recommendations.
    
    Takes a final recommendation and renders it differently based on:
    - Audience (operator, system, audit, debug)
    - Mode (standard, summary, detailed, escalation, degraded)
    - Verbosity
    - Explanation depth
    - Phrasing strictness
    - Caution tone
    - Degraded mode
    - Escalation handoff needs
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize recommendation delivery composer."""
        self.storage_path = storage_path or "/data/data/com.termux/files/home/.openclaw/workspace/weslr/delivery/"
        self.renderings: Dict[str, RenderedDelivery] = {}
        self.composition_counter: int = 0
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _generate_delivery_id(self) -> str:
        """Generate unique delivery ID."""
        self.composition_counter += 1
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"delivery_{timestamp}_{self.composition_counter:04d}"
    
    def compose_delivery(
        self,
        recommendation: Dict[str, Any],
        configuration: DeliveryConfiguration,
        created_by: Optional[str] = None,
    ) -> RenderedDelivery:
        """Compose a delivery for a recommendation based on configuration.
        
        This is additive — no migration required.
        """
        delivery_id = self._generate_delivery_id()
        
        # Build base content
        rec_type = recommendation.get("recommendation_type", "action")
        rec_text = recommendation.get("recommendation_text", "")
        confidence = recommendation.get("confidence", 0.5)
        confidence_level = recommendation.get("confidence_level", "moderate")
        timing_posture = recommendation.get("timing_posture", "short_term")
        
        # Build summary based on verbosity
        verbosity_multiplier = configuration.get_verbosity_multiplier()
        summary_lines = []
        if verbosity_multiplier > 0.2:
            summary_lines.append(f"{rec_type.upper()}: {rec_text}")
        if verbosity_multiplier > 0.5:
            summary_lines.append(f"Confidence: {confidence:.0%} ({confidence_level})")
            summary_lines.append(f"Timing: {timing_posture}")
        if verbosity_multiplier > 0.8:
            summary_lines.append(f"Escalation: {recommendation.get('escalation_required', 'none')}")
        
        summary = "\n".join(summary_lines) if summary_lines else ""
        
        # Extract governing rules and active tensions early for reuse
        governing_rules = recommendation.get("governing_rules", [])
        active_tensions = recommendation.get("active_tensions", [])
        
        # Build detailed content
        detailed_lines = []
        if configuration.mode in [DeliveryMode.DETAILED.value, DeliveryMode.ESCALATION.value]:
            detailed_lines.append(f"Recommendation: {rec_text}")
            detailed_lines.append(f"Type: {rec_type}")
            detailed_lines.append(f"Confidence: {confidence:.0%} ({confidence_level})")
            detailed_lines.append(f"Timing: {timing_posture}")
            detailed_lines.append(f"Trust Posture: {recommendation.get('trust_posture', 'standard')}")
            detailed_lines.append(f"Recovery Path: {recommendation.get('recovery_path', 'none')}")
            
            # Add governing rules if available
            if governing_rules:
                detailed_lines.append("Governing Rules:")
                for rule in governing_rules[:3]:
                    detailed_lines.append(f"  - {rule.get('rule_type', 'unknown')}: {rule.get('rule_value', 'unknown')}")
            
            # Add active tensions if available
            if active_tensions:
                detailed_lines.append("Tensions Resolved:")
                for tension in active_tensions[:3]:
                    detailed_lines.append(f"  - {tension.get('tension_type', 'unknown')}: {tension.get('resolution', 'unknown')}")
        
        detailed = "\n".join(detailed_lines) if detailed_lines else None
        
        # Build explanation based on explanation_depth
        explanation = None
        if configuration.get_explanation_required():
            explanation_lines = []
            explanation_lines.append(f"**Recommendation: {rec_text}**")
            explanation_lines.append("")
            explanation_lines.append("## Rationale")
            
            confidence_bundle = recommendation.get("confidence_bundle")
            if confidence_bundle:
                explanation_lines.append(f"**Evidence Confidence**: {confidence_bundle.get('confidence', 0):.0%}")
                if confidence_bundle.get("confidence_basis"):
                    explanation_lines.append(f"*{confidence_bundle.get('confidence_basis')}*")
            
            explanation_lines.append("")
            explanation_lines.append("## Context")
            explanation_lines.append(f"**Timing**: {timing_posture}")
            explanation_lines.append(f"**Trust Posture**: {recommendation.get('trust_posture', 'standard')}")
            
            if active_tensions:
                explanation_lines.append("")
                explanation_lines.append("## Tensions Resolved")
                for tension in active_tensions[:5]:
                    explanation_lines.append(f"- {tension.get('tension_type', 'unknown')}: {tension.get('resolution', 'unknown')}")
            
            if governing_rules:
                explanation_lines.append("")
                explanation_lines.append("## Governing Rules")
                for rule in governing_rules[:5]:
                    explanation_lines.append(f"- {rule.get('rule_type', 'unknown')}: {rule.get('rule_value', 'unknown')}")
            
            explanation = "\n".join(explanation_lines)
        
        # Build caution note based on caution_tone and strictness
        caution_note = None
        if configuration.caution_tone in [CautionTone.ELEVATED.value, CautionTone.MAXIMUM.value]:
            if confidence < 0.8:
                caution_note = "Moderate confidence - review carefully"
            elif configuration.degraded_mode:
                caution_note = "Degraded mode - reduced confidence thresholds"
            elif configuration.mode == DeliveryMode.ESCALATION.value:
                caution_note = "Escalation required - operator review needed"
        
        # Build handoff context for escalation
        handoff_context = None
        if configuration.escalation_handoff or configuration.mode == DeliveryMode.ESCALATION.value:
            handoff_lines = []
            handoff_lines.append("HANDOFF CONTEXT")
            handoff_lines.append(f"Recommendation ID: {recommendation.get('recommendation_id', 'unknown')}")
            handoff_lines.append(f"Type: {rec_type}")
            handoff_lines.append(f"Text: {rec_text}")
            handoff_lines.append(f"Confidence: {confidence:.0%}")
            handoff_lines.append(f"Timing: {timing_posture}")
            handoff_lines.append(f"Escalation: {recommendation.get('escalation_required', 'none')}")
            handoff_lines.append("")
            
            if configuration.handoff_format == HandoffFormat.COMPLETE.value:
                handoff_lines.append("Full Recommendation Details:")
                handoff_lines.append(json.dumps(recommendation, indent=2))
            elif configuration.handoff_format == HandoffFormat.STRUCTURED.value:
                handoff_lines.append("Structured Handoff:")
                handoff_lines.append(f"- recommendation_id: {recommendation.get('recommendation_id', 'unknown')}")
                handoff_lines.append(f"- recommendation_type: {rec_type}")
                handoff_lines.append(f"- confidence: {confidence:.0%}")
                handoff_lines.append(f"- escalation_required: {recommendation.get('escalation_required', 'none')}")
            
            handoff_context = "\n".join(handoff_lines)
        
        rendered = RenderedDelivery(
            delivery_id=delivery_id,
            recommendation_id=recommendation.get("recommendation_id", "unknown"),
            delivery_configuration=configuration.to_dict(),
            summary=summary if not configuration.summary_mode else None,
            detailed=detailed,
            explanation=explanation,
            caution_note=caution_note,
            handoff_context=handoff_context,
            rendered_by=created_by,
        )
        
        self.renderings[delivery_id] = rendered
        self._save_delivery(rendered)
        return rendered
    
    def _save_delivery(self, rendered: RenderedDelivery) -> None:
        """Save delivery to storage."""
        import os
        
        filepath = os.path.join(self.storage_path, f"{rendered.delivery_id}.json")
        with open(filepath, "w") as f:
            json.dump(rendered.to_dict(), f, indent=2)
    
    def get_delivery(self, delivery_id: str) -> Optional[RenderedDelivery]:
        """Get a delivery by ID."""
        return self.renderings.get(delivery_id)
    
    def get_latest_delivery(self) -> Optional[RenderedDelivery]:
        """Get the most recent delivery."""
        if not self.renderings:
            return None
        return max(self.renderings.values(), key=lambda r: r.rendered_at)
    
    def compose_for_operator(
        self,
        recommendation: Dict[str, Any],
        verbosity: int = 5,
        explanation_depth: str = ExplanationDepth.STANDARD.value,
        created_by: Optional[str] = None,
    ) -> RenderedDelivery:
        """Compose delivery for human operator."""
        config = DeliveryConfiguration(
            audience=DeliveryAudience.OPERATOR.value,
            mode=DeliveryMode.STANDARD.value,
            verbosity=verbosity,
            explanation_depth=explanation_depth,
            created_by=created_by,
        )
        return self.compose_delivery(recommendation, config, created_by)
    
    def compose_for_system(
        self,
        recommendation: Dict[str, Any],
        created_by: Optional[str] = None,
    ) -> RenderedDelivery:
        """Compose delivery for automated systems (JSON format)."""
        config = DeliveryConfiguration(
            audience=DeliveryAudience.SYSTEM.value,
            mode=DeliveryMode.STANDARD.value,
            verbosity=2,  # Minimal verbosity for systems
            explanation_depth=ExplanationDepth.NONE.value,
            created_by=created_by,
        )
        return self.compose_delivery(recommendation, config, created_by)
    
    def compose_summary(
        self,
        recommendation: Dict[str, Any],
        created_by: Optional[str] = None,
    ) -> RenderedDelivery:
        """Compose summary-only delivery."""
        config = DeliveryConfiguration(
            audience=DeliveryAudience.OPERATOR.value,
            mode=DeliveryMode.SUMMARY.value,
            verbosity=3,
            summary_mode=True,
            created_by=created_by,
        )
        return self.compose_delivery(recommendation, config, created_by)
    
    def compose_for_escalation(
        self,
        recommendation: Dict[str, Any],
        handoff_format: str = HandoffFormat.BRIEF.value,
        created_by: Optional[str] = None,
    ) -> RenderedDelivery:
        """Compose delivery for escalation handoff."""
        config = DeliveryConfiguration(
            audience=DeliveryAudience.OPERATOR.value,
            mode=DeliveryMode.ESCALATION.value,
            verbosity=8,
            explanation_depth=ExplanationDepth.EXHAUSTIVE.value,
            phrasing_strictness=PhrasingStrictness.STRICT.value,
            caution_tone=CautionTone.ELEVATED.value,
            escalation_handoff=True,
            handoff_format=handoff_format,
            created_by=created_by,
        )
        return self.compose_delivery(recommendation, config, created_by)
    
    def compose_for_degraded_mode(
        self,
        recommendation: Dict[str, Any],
        created_by: Optional[str] = None,
    ) -> RenderedDelivery:
        """Compose delivery for degraded mode (reduced confidence)."""
        config = DeliveryConfiguration(
            audience=DeliveryAudience.OPERATOR.value,
            mode=DeliveryMode.DEGRADED.value,
            verbosity=7,
            explanation_depth=ExplanationDepth.STANDARD.value,
            caution_tone=CautionTone.MAXIMUM.value,
            degraded_mode=True,
            created_by=created_by,
        )
        return self.compose_delivery(recommendation, config, created_by)
    
    def compose_for_audit(
        self,
        recommendation: Dict[str, Any],
        created_by: Optional[str] = None,
    ) -> RenderedDelivery:
        """Compose delivery for audit systems (comprehensive)."""
        config = DeliveryConfiguration(
            audience=DeliveryAudience.AUDIT.value,
            mode=DeliveryMode.DETAILED.value,
            verbosity=10,
            explanation_depth=ExplanationDepth.EXHAUSTIVE.value,
            created_by=created_by,
        )
        return self.compose_delivery(recommendation, config, created_by)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert composer state to dictionary."""
        return {
            "delivery_count": len(self.renderings),
            "composition_counter": self.composition_counter,
            "renderings": {k: v.to_dict() for k, v in self.renderings.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_final_decision_composer(
    composer_dict: Dict[str, Any],
    delivery_composer: RecommendationDeliveryComposer = None,
) -> Dict[str, Any]:
    """Add delivery composer context to final decision composer.
    
    This is purely additive — no migration required.
    
    v52: Delivery composer provides presentation modes for recommendations.
    """
    if "delivery_context" not in composer_dict:
        composer_dict["delivery_context"] = None
    
    if delivery_composer:
        latest = delivery_composer.get_latest_delivery() if hasattr(delivery_composer, "get_latest_delivery") else None
        composer_dict["delivery_context"] = {
            "delivery_storage_path": getattr(delivery_composer, "storage_path", None),
            "delivery_count": len(delivery_composer.renderings) if hasattr(delivery_composer, "renderings") else 0,
            "has_latest_delivery": latest is not None,
            "latest_delivery_id": latest.delivery_id if latest else None,
        }
    
    return composer_dict


def integrate_with_deployment_persona(
    persona_dict: Dict[str, Any],
    delivery_composer: RecommendationDeliveryComposer = None,
) -> Dict[str, Any]:
    """Add delivery context to deployment persona.
    
    This is purely additive — no migration required.
    
    v52: Delivery composer provides role-specific presentation modes.
    """
    if "delivery_context" not in persona_dict:
        persona_dict["delivery_context"] = None
    
    if delivery_composer:
        persona_dict["delivery_context"] = {
            "delivery_storage_path": getattr(delivery_composer, "storage_path", None),
            "delivery_count": len(delivery_composer.renderings) if hasattr(delivery_composer, "renderings") else 0,
        }
    
    return persona_dict


def integrate_with_policy_profile(
    profile_dict: Dict[str, Any],
    delivery_composer: RecommendationDeliveryComposer = None,
) -> Dict[str, Any]:
    """Add delivery context to policy profile.
    
    This is purely additive — no migration required.
    
    v52: Delivery composer provides presentation modes by strictness.
    """
    if "delivery_context" not in profile_dict:
        profile_dict["delivery_context"] = None
    
    if delivery_composer:
        profile_dict["delivery_context"] = {
            "delivery_storage_path": getattr(delivery_composer, "storage_path", None),
            "delivery_count": len(delivery_composer.renderings) if hasattr(delivery_composer, "renderings") else 0,
        }
    
    return profile_dict


def integrate_with_governance_surface(
    governance_dict: Dict[str, Any],
    delivery_composer: RecommendationDeliveryComposer = None,
) -> Dict[str, Any]:
    """Add delivery context to governance surface.
    
    This is purely additive — no migration required.
    
    v52: Delivery composer provides presentation modes for governance decisions.
    """
    if "delivery_context" not in governance_dict:
        governance_dict["delivery_context"] = None
    
    if delivery_composer:
        latest = delivery_composer.get_latest_delivery() if hasattr(delivery_composer, "get_latest_delivery") else None
        governance_dict["delivery_context"] = {
            "delivery_storage_path": getattr(delivery_composer, "storage_path", None),
            "delivery_count": len(delivery_composer.renderings) if hasattr(delivery_composer, "renderings") else 0,
            "has_latest_delivery": latest is not None,
            "latest_delivery_id": latest.delivery_id if latest else None,
        }
    
    return governance_dict


def integrate_with_unified_operator_context(
    operator_dict: Dict[str, Any],
    delivery_composer: RecommendationDeliveryComposer = None,
) -> Dict[str, Any]:
    """Add delivery context to unified operator context.
    
    This is purely additive — no migration required.
    
    v52: Delivery composer provides presentation modes for operator review.
    """
    if "delivery_context" not in operator_dict:
        operator_dict["delivery_context"] = None
    
    if delivery_composer:
        operator_dict["delivery_context"] = {
            "delivery_storage_path": getattr(delivery_composer, "storage_path", None),
            "delivery_count": len(delivery_composer.renderings) if hasattr(delivery_composer, "renderings") else 0,
        }
    
    return operator_dict
