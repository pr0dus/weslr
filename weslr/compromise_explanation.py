# compromise_explanation.py - v35: Compromise / Why-Not Explanation Layer
# Creates a governed explanation layer helping WESLR explain why a compromise
# was chosen, why a stronger recommendation was not chosen, and why hold-back
# behavior was triggered.
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


class ExplanationType(str, Enum):
    """Types of explanations."""
    COMPROMISE = "compromise"  # Why compromise was chosen
    WHY_NOT_STRONGER = "why_not_stronger"  # Why stronger recommendation was not chosen
    WHY_NOT_ALTERNATIVE = "why_not_alternative"  # Why alternative was not chosen
    HOLD_BACK = "hold_back"  # Why hold-back behavior was triggered
    TENSION_RESOLUTION = "tension_resolution"  # How tension was resolved
    PRIORITY_OVERRIDE = "priority_override"  # Why priority override occurred


class ExplanationStatus(str, Enum):
    """Status of explanation."""
    GENERATED = "generated"  # Explanation generated
    REVIEWED = "reviewed"  # Explanation reviewed
    USED = "used"  # Explanation used in output
    REJECTED = "rejected"  # Explanation rejected by user


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class Explanation:
    """Represents an explanation for a recommendation or decision."""
    
    explanation_id: str  # Unique identifier
    explanation_type: str  # Type of explanation
    recommendation_id: str  # ID of recommendation this explains
    
    # Context (with default to be after required fields)
    context: Dict[str, Any] = field(default_factory=dict)  # Context at time of explanation
    
    # Explanation content (with defaults)
    explanation_text: str = ""
    rationale: str = ""
    confidence: float = 0.5  # Confidence in explanation
    
    # Alternatives considered (optional with defaults)
    alternative_explanation: Optional[str] = None  # Why alternative was not chosen
    stronger_explanation: Optional[str] = None  # Why stronger was not chosen
    
    # Resolution info (for tensions)
    tension_id: Optional[str] = None
    tension_resolution: Optional[str] = None
    tension_resolution_details: Optional[str] = None
    
    # Status
    status: str = ExplanationStatus.GENERATED.value
    reviewed_at: Optional[str] = None
    used_at: Optional[str] = None
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "explanation_id": self.explanation_id,
            "explanation_type": self.explanation_type,
            "recommendation_id": self.recommendation_id,
            "context": self.context,
            "explanation_text": self.explanation_text,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "alternative_explanation": self.alternative_explanation,
            "stronger_explanation": self.stronger_explanation,
            "tension_id": self.tension_id,
            "tension_resolution": self.tension_resolution,
            "tension_resolution_details": self.tension_resolution_details,
            "status": self.status,
            "reviewed_at": self.reviewed_at,
            "used_at": self.used_at,
            "created_at": self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Explanation:
        """Create from dictionary representation."""
        data["context"] = data.get("context", {})
        return cls(**data)
    
    def set_status(self, new_status: str) -> None:
        """Update explanation status."""
        self.status = new_status
        if new_status == ExplanationStatus.REVIEWED.value:
            self.reviewed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        elif new_status == ExplanationStatus.USED.value:
            self.used_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class ExplanationSet:
    """Set of explanations for a recommendation."""
    
    explanation_set_id: str  # Unique identifier
    recommendation_id: str  # ID of recommendation
    
    # Explanations
    explanations: List[Explanation] = field(default_factory=list)
    
    # Status
    status: str = "active"
    
    # Configuration
    include_always: List[str] = field(default_factory=list)  # Always include these explanation IDs
    exclude_always: List[str] = field(default_factory=list)  # Never include these explanation IDs
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "explanation_set_id": self.explanation_set_id,
            "recommendation_id": self.recommendation_id,
            "explanations": [e.to_dict() for e in self.explanations],
            "status": self.status,
            "include_always": self.include_always,
            "exclude_always": self.exclude_always,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExplanationSet:
        """Create from dictionary representation."""
        explanations_data = data.get("explanations", [])
        explanations = [Explanation.from_dict(e) for e in explanations_data]
        include_always = data.get("include_always", [])
        exclude_always = data.get("exclude_always", [])
        
        return cls(
            explanation_set_id=data.get("explanation_set_id", ""),
            recommendation_id=data.get("recommendation_id", ""),
            explanations=explanations,
            status=data.get("status", "active"),
            include_always=include_always,
            exclude_always=exclude_always,
        )
    
    def add_explanation(self, explanation: Explanation) -> None:
        """Add an explanation to the set."""
        self.explanations.append(explanation)
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    def get_active_explanations(self) -> List[Explanation]:
        """Get explanations that are not excluded."""
        return [
            e for e in self.explanations
            if e.explanation_id not in self.exclude_always
        ]
    
    def to_summary(self) -> Dict[str, Any]:
        """Get summary of explanations."""
        return {
            "explanation_set_id": self.explanation_set_id,
            "recommendation_id": self.recommendation_id,
            "explanation_count": len(self.explanations),
            "explanation_types": [e.explanation_type for e in self.explanations],
            "status": self.status,
        }


# ============================================================================
# EXPLANATION GENERATOR
# ============================================================================


class ExplanationGenerator:
    """Generator for explanations based on recommendation context."""
    
    def __init__(self):
        """Initialize explanation generator."""
        self.explanation_sets: Dict[str, ExplanationSet] = {}
        self.explanations: Dict[str, Explanation] = {}
    
    def generate_compromise_explanation(
        self,
        recommendation_id: str,
        chosen_recommendation: str,
        stronger_recommendation: Optional[str],
        stronger_reason: Optional[str],
        compromise_rationale: str,
        tension_id: Optional[str] = None,
        tension_resolution: Optional[str] = None,
        tension_resolution_details: Optional[str] = None,
        confidence: float = 0.7,
    ) -> Explanation:
        """Generate explanation for compromise recommendation."""
        explanation_id = f"exp-{len(self.explanations) + 1:04d}"
        
        explanation_text = "A compromise recommendation was chosen to balance competing priorities."
        
        if stronger_recommendation and stronger_reason:
            stronger_explanation = f"A stronger recommendation ({stronger_recommendation}) was considered but not chosen because: {stronger_reason}"
        else:
            stronger_explanation = "No stronger recommendation was available."
        
        if tension_id and tension_resolution:
            rationale = f"{compromise_rationale}. This resolves tension {tension_id} via {tension_resolution}."
            if tension_resolution_details:
                rationale += f" Details: {tension_resolution_details}"
        else:
            rationale = compromise_rationale
        
        explanation = Explanation(
            explanation_id=explanation_id,
            explanation_type=ExplanationType.COMPROMISE.value,
            recommendation_id=recommendation_id,
            explanation_text=explanation_text,
            rationale=rationale,
            stronger_explanation=stronger_explanation,
            tension_id=tension_id,
            tension_resolution=tension_resolution,
            tension_resolution_details=tension_resolution_details,
            confidence=confidence,
        )
        
        self.explanations[explanation_id] = explanation
        return explanation
    
    def generate_why_not_stronger_explanation(
        self,
        recommendation_id: str,
        chosen_recommendation: str,
        stronger_recommendation: str,
        stronger_reason: str,
        confidence: float = 0.8,
    ) -> Explanation:
        """Generate explanation for why stronger recommendation was not chosen."""
        explanation_id = f"exp-{len(self.explanations) + 1:04d}"
        
        explanation = Explanation(
            explanation_id=explanation_id,
            explanation_type=ExplanationType.WHY_NOT_STRONGER.value,
            recommendation_id=recommendation_id,
            explanation_text=f"A stronger recommendation ({stronger_recommendation}) was considered but not chosen.",
            rationale=stronger_reason,
            stronger_explanation=f"Stronger: {stronger_recommendation}. Reason: {stronger_reason}",
            confidence=confidence,
        )
        
        self.explanations[explanation_id] = explanation
        return explanation
    
    def generate_hold_back_explanation(
        self,
        recommendation_id: str,
        blocked_recommendation: str,
        blocked_reason: str,
        tension_id: Optional[str] = None,
        confidence: float = 0.9,
    ) -> Explanation:
        """Generate explanation for hold-back behavior."""
        explanation_id = f"exp-{len(self.explanations) + 1:04d}"
        
        explanation = Explanation(
            explanation_id=explanation_id,
            explanation_type=ExplanationType.HOLD_BACK.value,
            recommendation_id=recommendation_id,
            explanation_text=f"The stronger recommendation ({blocked_recommendation}) was held back.",
            rationale=blocked_reason,
            alternative_explanation=f"Blocked: {blocked_recommendation}. Reason: {blocked_reason}",
            tension_id=tension_id,
            confidence=confidence,
        )
        
        self.explanations[explanation_id] = explanation
        return explanation
    
    def generate_alternative_explanation(
        self,
        recommendation_id: str,
        chosen_alternative: str,
        blocked_alternative: str,
        blocked_reason: str,
        confidence: float = 0.7,
    ) -> Explanation:
        """Generate explanation for alternative choice."""
        explanation_id = f"exp-{len(self.explanations) + 1:04d}"
        
        explanation = Explanation(
            explanation_id=explanation_id,
            explanation_type=ExplanationType.WHY_NOT_ALTERNATIVE.value,
            recommendation_id=recommendation_id,
            explanation_text=f"Alternative {blocked_alternative} was not chosen.",
            rationale=blocked_reason,
            alternative_explanation=f"Blocked: {blocked_alternative}. Reason: {blocked_reason}",
            confidence=confidence,
        )
        
        self.explanations[explanation_id] = explanation
        return explanation
    
    def create_explanation_set(self, recommendation_id: str) -> ExplanationSet:
        """Create an explanation set for a recommendation."""
        explanation_set_id = f"set-{len(self.explanation_sets) + 1:04d}"
        
        explanation_set = ExplanationSet(
            explanation_set_id=explanation_set_id,
            recommendation_id=recommendation_id,
        )
        
        self.explanation_sets[explanation_set_id] = explanation_set
        return explanation_set
    
    def add_explanation_to_set(
        self,
        explanation_set_id: str,
        explanation: Explanation,
    ) -> bool:
        """Add an explanation to a set."""
        explanation_set = self.explanation_sets.get(explanation_set_id)
        if not explanation_set:
            return False
        
        explanation_set.add_explanation(explanation)
        return True
    
    def get_explanation(self, explanation_id: str) -> Optional[Explanation]:
        """Get an explanation by ID."""
        return self.explanations.get(explanation_id)
    
    def get_explanation_set(self, explanation_set_id: str) -> Optional[ExplanationSet]:
        """Get an explanation set by ID."""
        return self.explanation_sets.get(explanation_set_id)
    
    def get_all_explanations_for_recommendation(self, recommendation_id: str) -> List[Explanation]:
        """Get all explanations for a recommendation."""
        explanations = []
        for es in self.explanation_sets.values():
            if es.recommendation_id == recommendation_id:
                explanations.extend(es.get_active_explanations())
        return explanations
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert generator state to dictionary."""
        return {
            "explanation_count": len(self.explanations),
            "explanation_set_count": len(self.explanation_sets),
            "explanations": {k: v.to_dict() for k, v in self.explanations.items()},
        }


# ============================================================================
# EXPLANATION SUMMARIZER
# ============================================================================


class ExplanationSummarizer:
    """Summarizer for explanation sets."""
    
    def summarize_explanation_set(self, explanation_set: ExplanationSet) -> Dict[str, Any]:
        """Create a summary of an explanation set."""
        active_explanations = explanation_set.get_active_explanations()
        
        if not active_explanations:
            return {
                "explanation_set_id": explanation_set.explanation_set_id,
                "summary": "No explanations available",
                "explanation_count": 0,
            }
        
        explanation_types = [e.explanation_type for e in active_explanations]
        avg_confidence = sum(e.confidence for e in active_explanations) / len(active_explanations)
        
        # Generate summary text
        type_counts = {}
        for et in explanation_types:
            type_counts[et] = type_counts.get(et, 0) + 1
        
        type_descriptions = {
            ExplanationType.COMPROMISE.value: "compromise explanation",
            ExplanationType.WHY_NOT_STRONGER.value: "why-not stronger explanation",
            ExplanationType.HOLD_BACK.value: "hold-back explanation",
            ExplanationType.WHY_NOT_ALTERNATIVE.value: "why-not alternative explanation",
            ExplanationType.TENSION_RESOLUTION.value: "tension resolution explanation",
            ExplanationType.PRIORITY_OVERRIDE.value: "priority override explanation",
        }
        
        type_descriptions_text = ", ".join([
            f"{count} {type_descriptions.get(et, et)}" if count == 1 else f"{count} {type_descriptions.get(et, et)}s"
            for et, count in type_counts.items()
        ])
        
        summary_text = f"Explanation set contains {type_descriptions_text} with average confidence {avg_confidence:.1f}"
        
        return {
            "explanation_set_id": explanation_set.explanation_set_id,
            "summary": summary_text,
            "explanation_count": len(active_explanations),
            "explanation_types": explanation_types,
            "type_counts": type_counts,
            "average_confidence": avg_confidence,
            "include_count": len(explanation_set.include_always),
            "exclude_count": len(explanation_set.exclude_always),
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_adaptive_guidance(guidance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add explanation context to adaptive guidance.
    
    This is purely additive — no migration required.
    """
    if "explanation_available" not in guidance_dict:
        guidance_dict["explanation_available"] = False
    if "explanation_set_id" not in guidance_dict:
        guidance_dict["explanation_set_id"] = None
    if "compromise_explanation" not in guidance_dict:
        guidance_dict["compromise_explanation"] = None
    if "hold_back_explanation" not in guidance_dict:
        guidance_dict["hold_back_explanation"] = None
    return guidance_dict


def integrate_with_narrative(narrative_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add explanation context to narrative generation.
    
    This is purely additive — no migration required.
    """
    if "explanation_basis" not in narrative_dict:
        narrative_dict["explanation_basis"] = None
    if "compromise_explanation" not in narrative_dict:
        narrative_dict["compromise_explanation"] = None
    if "hold_back_explanation" not in narrative_dict:
        narrative_dict["hold_back_explanation"] = None
    return narrative_dict


def integrate_with_operator_context(context_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add explanation awareness to operator context.
    
    This is purely additive — no migration required.
    """
    if "explanation_available" not in context_dict:
        context_dict["explanation_available"] = False
    if "explanation_count" not in context_dict:
        context_dict["explanation_count"] = 0
    if "explanation_types" not in context_dict:
        context_dict["explanation_types"] = []
    return context_dict


def integrate_with_governance_view(governance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add explanation context to governance view.
    
    This is purely additive — no migration required.
    """
    if "explanation_available" not in governance_dict:
        governance_dict["explanation_available"] = False
    if "explanation_summary" not in governance_dict:
        governance_dict["explanation_summary"] = None
    return governance_dict
