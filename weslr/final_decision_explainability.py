# final_decision_explainability.py - WESLR v54: Final Decision Explainability Layer
# Creates a governed explainability layer so every final recommendation can produce a
# clear human-readable explanation bundle.
# Additive only, transparent, reversible, role-aware, non-manipulative.
# No repo drift (local to WESLR scope).

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from . import final_decision_composer
from . import recommendation_delivery
from . import recommendation_presentation_mode


# ============================================================================
# ENUMS
# ============================================================================


class ExplanationFormat(str, Enum):
    """Output format for explanation bundle."""
    TEXT = "text"  # Plain text narrative
    MARKDOWN = "markdown"  # Markdown with structure
    STRUCTURED_TEXT = "structured_text"  # Structured text with section markers


class ExplanationDepth(str, Enum):
    """Depth of explanation to provide."""
    MINIMAL = "minimal"  # Very brief explanation
    STANDARD = "standard"  # Balanced explanation
    ENHANCED = "enhanced"  # Detailed reasoning
    EXHAUSTIVE = "exhaustive"  # Multiple angles, chain of thought


class ExplanationFocus(str, Enum):
    """Primary focus of explanation."""
    DECISION = "decision"  # Focus on the decision itself
    REASONING = "reasoning"  # Focus on the reasoning chain
    EVIDENCE = "evidence"  # Focus on supporting evidence
    ALTERNATIVES = "alternatives"  # Focus on blocked alternatives
    GOVERNANCE = "governance"  # Focus on governing rules
    RECOVERY = "recovery"  # Focus on recovery path


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class ExplanationSection:
    """A single section of the explanation bundle."""
    
    section_id: str  # Unique identifier
    section_title: str  # Human-readable title
    section_content: str  # Content of this section
    section_order: int = 0  # Order in the bundle
    is_optional: bool = False  # Can be omitted if not applicable


@dataclass
class ExplanationBundle:
    """Complete explanation bundle for a final recommendation."""
    
    bundle_id: str  # Unique identifier
    recommendation_id: str  # Reference to FinalRecommendation
    recommendation_type: str  # e.g., "action", "defer", "investigate"
    
    # Required sections
    decision_summary: ExplanationSection
    primary_rationale: ExplanationSection
    evidence_summary: ExplanationSection
    blocked_alternatives: ExplanationSection
    governing_rules: ExplanationSection
    
    # Optional sections
    trust_timing_influence: Optional[ExplanationSection] = None
    recovery_path: Optional[ExplanationSection] = None
    escalation_handoff: Optional[ExplanationSection] = None
    concise_why_summary: Optional[ExplanationSection] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    created_by: Optional[str] = None
    explanation_depth: str = ExplanationDepth.STANDARD.value
    explanation_format: str = ExplanationFormat.TEXT.value
    domain: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "bundle_id": self.bundle_id,
            "recommendation_id": self.recommendation_id,
            "recommendation_type": self.recommendation_type,
            "decision_summary": self.decision_summary.to_dict(),
            "primary_rationale": self.primary_rationale.to_dict(),
            "evidence_summary": self.evidence_summary.to_dict(),
            "blocked_alternatives": self.blocked_alternatives.to_dict(),
            "governing_rules": self.governing_rules.to_dict(),
            "created_at": self.created_at,
            "created_by": self.created_by,
            "explanation_depth": self.explanation_depth,
            "explanation_format": self.explanation_format,
        }
        if self.trust_timing_influence:
            result["trust_timing_influence"] = self.trust_timing_influence.to_dict()
        if self.recovery_path:
            result["recovery_path"] = self.recovery_path.to_dict()
        if self.escalation_handoff:
            result["escalation_handoff"] = self.escalation_handoff.to_dict()
        if self.concise_why_summary:
            result["concise_why_summary"] = self.concise_why_summary.to_dict()
        return result
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_markdown(self) -> str:
        """Render explanation bundle as markdown."""
        parts = []
        parts.append(f"# Recommendation: {self.recommendation_id}")
        parts.append(f"Type: {self.recommendation_type}")
        parts.append("")
        
        for section in [self.decision_summary, self.primary_rationale, self.evidence_summary,
                        self.blocked_alternatives, self.governing_rules,
                        self.trust_timing_influence, self.recovery_path,
                        self.escalation_handoff, self.concise_why_summary]:
            if section:
                parts.append(f"## {section.section_title}")
                parts.append(section.section_content)
                parts.append("")
        
        return "\n".join(parts)
    
    def to_text(self) -> str:
        """Render explanation bundle as plain text."""
        parts = []
        parts.append(f"Recommendation: {self.recommendation_id}")
        parts.append(f"Type: {self.recommendation_type}")
        parts.append("")
        
        for section in [self.decision_summary, self.primary_rationale, self.evidence_summary,
                        self.blocked_alternatives, self.governing_rules,
                        self.trust_timing_influence, self.recovery_path,
                        self.escalation_handoff, self.concise_why_summary]:
            if section:
                parts.append(f"--- {section.section_title} ---")
                parts.append(section.section_content)
                parts.append("")
        
        return "\n".join(parts)


# ============================================================================
# EXPLAINABILITY ENGINE
# ============================================================================


class FinalDecisionExplainabilityEngine:
    """Engine for generating explanation bundles from final recommendations."""
    
    def __init__(self):
        self.last_bundle: Optional[ExplanationBundle] = None
    
    def generate_explanation(self,
                            recommendation: final_decision_composer.FinalRecommendation,
                            presentation_config: Optional[recommendation_presentation_mode.PresentationConfiguration] = None,
                            delivery_config: Optional[recommendation_delivery.DeliveryConfiguration] = None,
                            depth: str = ExplanationDepth.STANDARD.value,
                            format_: str = ExplanationFormat.TEXT.value) -> ExplanationBundle:
        """Generate a complete explanation bundle for a final recommendation."""
        
        bundle_id = f"exp-{recommendation.recommendation_id}"
        
        # Decision Summary
        decision_summary = ExplanationSection(
            section_id="summary",
            section_title="Decision Summary",
            section_content=self._generate_decision_summary(recommendation),
            section_order=1
        )
        
        # Primary Rationale
        primary_rationale = ExplanationSection(
            section_id="rationale",
            section_title="Primary Rationale",
            section_content=self._generate_primary_rationale(recommendation),
            section_order=2
        )
        
        # Evidence Summary
        evidence_summary = ExplanationSection(
            section_id="evidence",
            section_title="Evidence Summary",
            section_content=self._generate_evidence_summary(recommendation),
            section_order=3
        )
        
        # Blocked Alternatives
        blocked_alternatives = ExplanationSection(
            section_id="alternatives",
            section_title="Blocked / Softened Alternatives",
            section_content=self._generate_blocked_alternatives(recommendation),
            section_order=4
        )
        
        # Governing Rules
        governing_rules = ExplanationSection(
            section_id="governance",
            section_title="Governing Rules",
            section_content=self._generate_governing_rules(recommendation),
            section_order=5
        )
        
        # Trust/Timing Influence (optional)
        trust_timing_influence = None
        if recommendation.trust_basis or recommendation.confidence_bundle:
            trust_timing_influence = ExplanationSection(
                section_id="trust_timing",
                section_title="Trust / Timing Influence",
                section_content=self._generate_trust_timing_influence(recommendation),
                section_order=6,
                is_optional=True
            )
        
        # Recovery Path (optional)
        recovery_path = None
        if recommendation.recovery_path != "none" and recommendation.recovery_description:
            recovery_path = ExplanationSection(
                section_id="recovery",
                section_title="Recovery Path",
                section_content=self._generate_recovery_path(recommendation),
                section_order=7,
                is_optional=True
            )
        
        # Escalation / Handoff (optional)
        escalation_handoff = None
        escalation_reason = self._get_escalation_reason(recommendation)
        if escalation_reason:
            escalation_handoff = ExplanationSection(
                section_id="escalation",
                section_title="Escalation / Handoff",
                section_content=escalation_reason,
                section_order=8,
                is_optional=True
            )
        
        # Concise "Why This" Summary (optional)
        concise_why_summary = None
        if depth in [ExplanationDepth.STANDARD.value, ExplanationDepth.ENHANCED.value]:
            concise_why_summary = ExplanationSection(
                section_id="why_summary",
                section_title="Concise Operator-Readable \"Why This\" Summary",
                section_content=self._generate_why_summary(recommendation, depth),
                section_order=9,
                is_optional=True
            )
        
        bundle = ExplanationBundle(
            bundle_id=bundle_id,
            recommendation_id=recommendation.recommendation_id,
            recommendation_type=recommendation.recommendation_type,
            decision_summary=decision_summary,
            primary_rationale=primary_rationale,
            evidence_summary=evidence_summary,
            blocked_alternatives=blocked_alternatives,
            governing_rules=governing_rules,
            trust_timing_influence=trust_timing_influence,
            recovery_path=recovery_path,
            escalation_handoff=escalation_handoff,
            concise_why_summary=concise_why_summary,
            created_by="weslr_explainability_engine",
            explanation_depth=depth,
            explanation_format=format_
        )
        
        self.last_bundle = bundle
        return bundle
    
    def _generate_decision_summary(self, recommendation: final_decision_composer.FinalRecommendation) -> str:
        """Generate the decision summary section."""
        parts = []
        parts.append(f"**Recommendation**: {recommendation.recommendation_text}")
        parts.append(f"**Confidence**: {recommendation.confidence_level} ({recommendation.confidence:.0%})")
        parts.append(f"**Timing**: {recommendation.timing_posture}")
        parts.append(f"**Trust Posture**: {recommendation.trust_posture}")
        return "\n".join(parts)
    
    def _generate_primary_rationale(self, recommendation: final_decision_composer.FinalRecommendation) -> str:
        """Generate the primary rationale section."""
        parts = []
        parts.append("This recommendation is driven by:")
        
        if recommendation.active_tensions:
            parts.append("- **Tensions resolved**: " + ", ".join(t.get("tension_type", "unknown") for t in recommendation.active_tensions[:3]))
        
        if recommendation.governing_rules:
            parts.append("- **Rules applied**: " + ", ".join(r.get("rule_type", "unknown") for r in recommendation.governing_rules[:3]))
        
        if recommendation.trust_basis:
            parts.append(f"- **Trust basis**: {recommendation.trust_basis}")
        
        if not parts[1:]:
            parts.append("- No specific rationale documented in recommendation")
        
        return "\n".join(parts)
    
    def _generate_evidence_summary(self, recommendation: final_decision_composer.FinalRecommendation) -> str:
        """Generate the evidence summary section."""
        bundle = recommendation.confidence_bundle
        if not bundle:
            return "No confidence bundle available."
        
        parts = []
        parts.append(f"**Confidence**: {bundle.confidence:.0%}")
        if bundle.confidence_basis:
            parts.append(f"**Basis**: {bundle.confidence_basis}")
        
        if bundle.supporting_factors:
            parts.append("**Supporting factors**:")
            for factor in bundle.supporting_factors[:5]:
                parts.append(f"- {factor}")
        
        if bundle.opposing_factors:
            parts.append("**Opposing factors**:")
            for factor in bundle.opposing_factors[:3]:
                parts.append(f"- {factor}")
        
        return "\n".join(parts)
    
    def _generate_blocked_alternatives(self, recommendation: final_decision_composer.FinalRecommendation) -> str:
        """Generate the blocked alternatives section."""
        if not recommendation.blocked_alternatives:
            return "No alternatives were blocked or softened."
        
        parts = []
        parts.append("The following alternatives were considered but blocked/softened:")
        
        for alt in recommendation.blocked_alternatives:
            parts.append(f"- **{alt.get('alternative_id', 'unknown')}**")
            parts.append(f"  - Type: {alt.get('alternative_type', 'unknown')}")
            parts.append(f"  - Reason: {alt.get('blocked_reason', 'unknown')}")
            if alt.get('softened_by'):
                parts.append(f"  - Softened by: {alt['softened_by']}")
        
        return "\n".join(parts)
    
    def _generate_governing_rules(self, recommendation: final_decision_composer.FinalRecommendation) -> str:
        """Generate the governing rules section."""
        if not recommendation.governing_rules:
            return "No governing rules applied to this recommendation."
        
        parts = []
        parts.append("The following rules governed this recommendation:")
        
        for rule in recommendation.governing_rules:
            parts.append(f"- **{rule.get('rule_id', 'unknown')}**")
            parts.append(f"  - Type: {rule.get('rule_type', 'unknown')}")
            parts.append(f"  - Value: {rule.get('rule_value', 'unknown')}")
            parts.append(f"  - Precedence: {rule.get('precedence_level', 'unknown')}")
        
        return "\n".join(parts)
    
    def _generate_trust_timing_influence(self, recommendation: final_decision_composer.FinalRecommendation) -> str:
        """Generate the trust/timing influence section."""
        parts = []
        
        if recommendation.trust_basis:
            parts.append(f"**Trust basis**: {recommendation.trust_basis}")
        
        if recommendation.confidence_bundle:
            parts.append(f"**Confidence basis**: {recommendation.confidence_bundle.confidence_basis or 'Standard assessment'}")
        
        if recommendation.due_by:
            parts.append(f"**Due by**: {recommendation.due_by}")
        
        parts.append(f"**Timing posture**: {recommendation.timing_posture}")
        
        return "\n".join(parts)
    
    def _generate_recovery_path(self, recommendation: final_decision_composer.FinalRecommendation) -> str:
        """Generate the recovery path section."""
        parts = []
        parts.append(f"**Recovery path**: {recommendation.recovery_path}")
        if recommendation.recovery_description:
            parts.append(f"**Description**: {recommendation.recovery_description}")
        
        if recommendation.recovery_triggers:
            parts.append("**Triggers**: " + ", ".join(recommendation.recovery_triggers))
        
        return "\n".join(parts)
    
    def _get_escalation_reason(self, recommendation: final_decision_composer.FinalRecommendation) -> Optional[str]:
        """Get escalation reason string."""
        # Escalation requirement is encoded in recommendation as a string enum
        escalation = getattr(recommendation, 'escalation_requirement', None)
        if escalation and escalation != "none":
            return f"Escalation required: {escalation}"
        return None
    
    def _generate_why_summary(self, recommendation: final_decision_composer.FinalRecommendation, depth: str) -> str:
        """Generate the concise \"Why This\" summary."""
        parts = []
        
        parts.append(f"**Decision**: {recommendation.recommendation_text}")
        
        if recommendation.confidence >= 0.8:
            parts.append(f"**Confidence**: {recommendation.confidence:.0%} — high confidence recommendation")
        elif recommendation.confidence >= 0.5:
            parts.append(f"**Confidence**: {recommendation.confidence:.0%} — moderate confidence recommendation")
        else:
            parts.append(f"**Confidence**: {recommendation.confidence:.0%} — low confidence, proceed with caution")
        
        if recommendation.trust_posture in ["enhanced", "full"]:
            parts.append(f"**Trust posture**: {recommendation.trust_posture} — elevated trust based on evidence")
        
        if recommendation.recovery_path == "none":
            parts.append("**Recovery**: no defined recovery path — outcome is final")
        
        return " ".join(parts)


# ============================================================================
# EXPLANATION DELIVERY APPLIER
# ============================================================================


class ExplanationDeliveryApplier:
    """Applier for presentation mode + delivery mode to explanation output."""
    
    def __init__(self, explainability_engine: FinalDecisionExplainabilityEngine):
        self.engine = explainability_engine
    
    def apply_delivery_mode(self, bundle: ExplanationBundle,
                           delivery_config: recommendation_delivery.DeliveryConfiguration) -> str:
        """Apply delivery mode to explanation bundle output."""
        mode = delivery_config.mode
        
        if mode == recommendation_delivery.DeliveryMode.SUMMARY.value:
            # Extract only decision summary
            return bundle.decision_summary.section_content
        
        if mode == recommendation_delivery.DeliveryMode.DETAILED.value:
            # Full explanation in markdown
            return bundle.to_markdown()
        
        # Standard or degraded mode
        return bundle.to_text()
    
    def apply_presentation_mode(self, bundle: ExplanationBundle,
                               presentation_config: recommendation_presentation_mode.PresentationConfiguration) -> str:
        """Apply presentation mode to explanation bundle output."""
        mode = presentation_config.mode
        
        if mode == recommendation_presentation_mode.PresentationMode.SUMMARY.value:
            return bundle.decision_summary.section_content
        
        if mode == recommendation_presentation_mode.PresentationMode.STRUCTURED.value:
            return bundle.to_json()
        
        if mode == recommendation_presentation_mode.PresentationMode.NARRATIVE.value:
            return self._to_narrative(bundle)
        
        # Standard or detailed
        return bundle.to_markdown()
    
    def _to_narrative(self, bundle: ExplanationBundle) -> str:
        """Render bundle as narrative/story."""
        parts = []
        parts.append(f"## Recommendation: {bundle.recommendation_id}")
        parts.append("")
        parts.append(bundle.decision_summary.section_content)
        parts.append("")
        parts.append("**Why this decision?**")
        parts.append(bundle.primary_rationale.section_content)
        parts.append("")
        parts.append("**What does this mean?**")
        parts.append(bundle.evidence_summary.section_content)
        parts.append("")
        parts.append("**What if this fails?**")
        if bundle.recovery_path:
            parts.append(bundle.recovery_path.section_content)
        else:
            parts.append("No recovery path defined — this is a final decision.")
        
        return "\n".join(parts)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ExplanationFormat",
    "ExplanationDepth",
    "ExplanationFocus",
    "ExplanationSection",
    "ExplanationBundle",
    "FinalDecisionExplainabilityEngine",
    "ExplanationDeliveryApplier",
]
