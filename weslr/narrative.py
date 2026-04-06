# narrative.py - Self-Architecture Core v9: Unified Operator Narrative Layer
# Unifies all decision signals into one coherent operator-facing assessment.
# Additive only, operator-first, reversible, governed.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class RecommendationType(str, Enum):
    """Types of recommendations."""
    ACCEPT = "accept"
    REJECT = "reject"
    DELAY = "delay"
    ARCHIVE = "archive"
    REVIEW = "review"


class NarrativeSection(str, Enum):
    """Sections of the unified narrative."""
    SUMMARY = "summary"
    WHY_SURFACED = "why_surfaced"
    SUBSYSTEM_IMPACT = "subsystem_impact"
    RISK_EFFORT = "risk_effort"
    ARCHITECTURAL_FIT = "architectural_fit"
    MEMORY_PRECEDENT = "memory_precedent"
    CONSISTENCY = "consistency_status"
    TRADEOFF = "tradeoff_context"
    RECOMMENDATION = "final_recommendation"
    TIMING = "timing"


@dataclass
class NarrativeBlock:
    """A section of the unified narrative."""
    section: str
    title: str
    content: str
    details: Optional[Dict[str, Any]] = None
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section": self.section,
            "title": self.title,
            "content": self.content,
            "details": self.details,
            "confidence": self.confidence,
        }


@dataclass
class UnifiedNarrative:
    """Unified operator-facing narrative for a suggestion."""
    
    narrative_id: str
    title: str
    domain: str
    
    # Core sections
    summary: NarrativeBlock
    why_surfaced: NarrativeBlock
    subsystem_impact: NarrativeBlock
    risk_effort: NarrativeBlock
    architectural_fit: NarrativeBlock
    memory_precedent: NarrativeBlock
    consistency: NarrativeBlock
    recommendation: NarrativeBlock
    timing: NarrativeBlock
    tradeoff: Optional[NarrativeBlock] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    suggestion_id: Optional[str] = None
    source: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "narrative_id": self.narrative_id,
            "title": self.title,
            "domain": self.domain,
            "summary": self.summary.to_dict(),
            "why_surfaced": self.why_surfaced.to_dict(),
            "subsystem_impact": self.subsystem_impact.to_dict(),
            "risk_effort": self.risk_effort.to_dict(),
            "architectural_fit": self.architectural_fit.to_dict(),
            "memory_precedent": self.memory_precedent.to_dict(),
            "consistency": self.consistency.to_dict(),
            "recommendation": self.recommendation.to_dict(),
            "timing": self.timing.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.tradeoff:
            result["tradeoff"] = self.tradeoff.to_dict()
        if self.author:
            result["author"] = self.author
        if self.suggestion_id:
            result["suggestion_id"] = self.suggestion_id
        if self.source:
            result["source"] = self.source
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UnifiedNarrative:
        # Extract blocks
        summary = NarrativeBlock(**data.get("summary", {}))
        why_surfaced = NarrativeBlock(**data.get("why_surfaced", {}))
        subsystem_impact = NarrativeBlock(**data.get("subsystem_impact", {}))
        risk_effort = NarrativeBlock(**data.get("risk_effort", {}))
        architectural_fit = NarrativeBlock(**data.get("architectural_fit", {}))
        memory_precedent = NarrativeBlock(**data.get("memory_precedent", {}))
        consistency = NarrativeBlock(**data.get("consistency", {}))
        recommendation = NarrativeBlock(**data.get("recommendation", {}))
        timing = NarrativeBlock(**data.get("timing", {}))
        tradeoff_data = data.get("tradeoff")
        tradeoff = NarrativeBlock(**tradeoff_data) if tradeoff_data else None

        narrative = cls(
            narrative_id=data.get("narrative_id", ""),
            title=data.get("title", ""),
            domain=data.get("domain", ""),
            summary=summary,
            why_surfaced=why_surfaced,
            subsystem_impact=subsystem_impact,
            risk_effort=risk_effort,
            architectural_fit=architectural_fit,
            memory_precedent=memory_precedent,
            consistency=consistency,
            tradeoff=tradeoff,
            recommendation=recommendation,
            timing=timing,
        )
        narrative.created_at = data.get("created_at", "")
        narrative.updated_at = data.get("updated_at", "")
        narrative.author = data.get("author")
        narrative.suggestion_id = data.get("suggestion_id")
        narrative.source = data.get("source")
        return narrative


class NarrativeEngine:
    """Engine to generate unified narratives from decision signals."""

    def __init__(self):
        self.decision_sources: Dict[str, Any] = {}
        self.memory_context: Optional[Dict[str, Any]] = None
        self.tradeoff_context: Optional[Dict[str, Any]] = None

    def set_decision_sources(self, sources: Dict[str, Any]) -> None:
        """Set decision sources (radar, assessment, etc.)."""
        self.decision_sources = sources

    def set_memory_context(self, context: Dict[str, Any]) -> None:
        """Set architecture memory context."""
        self.memory_context = context

    def set_tradeoff_context(self, context: Dict[str, Any]) -> None:
        """Set tradeoff/comparison context."""
        self.tradeoff_context = context

    def generate_narrative(
        self,
        title: str,
        domain: str,
        suggestion_id: Optional[str] = None,
    ) -> UnifiedNarrative:
        """Generate a unified narrative from decision sources."""
        narrative_id = f"narr-{suggestion_id[-4:] if suggestion_id else 'temp'}"

        # Extract sources
        radar = self.decision_sources.get("radar", {})
        assessment = self.decision_sources.get("assessment", {})
        memory = self.memory_context or {}
        tradeoff = self.tradeoff_context or {}

        # Build summary
        fit_score = assessment.get("fit_score", 0.5)
        priority = assessment.get("priority", "medium")
        summary_content = self._build_summary(title, domain, fit_score, priority)
        summary = NarrativeBlock(
            section=NarrativeSection.SUMMARY.value,
            title="Summary",
            content=summary_content,
        )

        # Why surfaced
        why_content = self._build_why_surfaced(radar, assessment)
        why_surfaced = NarrativeBlock(
            section=NarrativeSection.WHY_SURFACED.value,
            title="Why This Surfaced",
            content=why_content,
        )

        # Subsystem impact
        impact_content = self._build_subsystem_impact(assessment)
        subsystem_impact = NarrativeBlock(
            section=NarrativeSection.SUBSYSTEM_IMPACT.value,
            title="Subsystem Impact",
            content=impact_content,
        )

        # Risk and effort
        risk = assessment.get("implementation_risk", "medium")
        effort = assessment.get("effort_estimate", "medium")
        risk_effort_content = self._build_risk_effort(risk, effort)
        risk_effort = NarrativeBlock(
            section=NarrativeSection.RISK_EFFORT.value,
            title="Risk & Effort",
            content=risk_effort_content,
        )

        # Architectural fit
        fit_content = self._build_architectural_fit(assessment)
        architectural_fit = NarrativeBlock(
            section=NarrativeSection.ARCHITECTURAL_FIT.value,
            title="Architectural Fit",
            content=fit_content,
        )

        # Memory precedent
        memory_content, memory_details = self._build_memory_precedent(memory)
        memory_precedent = NarrativeBlock(
            section=NarrativeSection.MEMORY_PRECEDENT.value,
            title="Memory Precedent",
            content=memory_content,
            details=memory_details,
        )

        # Consistency status
        consistency_content, consistency_details = self._build_consistency(memory)
        consistency = NarrativeBlock(
            section=NarrativeSection.CONSISTENCY.value,
            title="Consistency Status",
            content=consistency_content,
            details=consistency_details,
        )

        # Tradeoff context (if available)
        tradeoff_block = None
        if tradeoff:
            tradeoff_content, tradeoff_details = self._build_tradeoff(tradeoff)
            tradeoff_block = NarrativeBlock(
                section=NarrativeSection.TRADEOFF.value,
                title="Tradeoff Context",
                content=tradeoff_content,
                details=tradeoff_details,
            )

        # Recommendation
        rec_content, rec_details = self._build_recommendation(assessment, memory, tradeoff)
        recommendation = NarrativeBlock(
            section=NarrativeSection.RECOMMENDATION.value,
            title="Final Recommendation",
            content=rec_content,
            details=rec_details,
        )

        # Timing
        timing_content = self._build_timing(assessment, tradeoff)
        timing = NarrativeBlock(
            section=NarrativeSection.TIMING.value,
            title="Timing",
            content=timing_content,
        )

        return UnifiedNarrative(
            narrative_id=narrative_id,
            title=title,
            domain=domain,
            summary=summary,
            why_surfaced=why_surfaced,
            subsystem_impact=subsystem_impact,
            risk_effort=risk_effort,
            architectural_fit=architectural_fit,
            memory_precedent=memory_precedent,
            consistency=consistency,
            tradeoff=tradeoff_block,
            recommendation=recommendation,
            timing=timing,
            suggestion_id=suggestion_id,
        )

    def _build_summary(self, title: str, domain: str, fit_score: float, priority: str) -> str:
        """Build summary block."""
        return (
            f"Suggestion '{title}' in domain '{domain}' "
            f"assessed with fit score {fit_score:.2f} and priority '{priority}'."
        )

    def _build_why_surfaced(self, radar: Dict[str, Any], assessment: Dict[str, Any]) -> str:
        """Build why this surfaced."""
        radar_note = ""
        if radar.get("trend_score"):
            radar_note = f"Radar trend score: {radar['trend_score']:.2f}. "
        elif radar.get("decision_score"):
            radar_note = f"Decision support score: {radar['decision_score']:.2f}. "

        assessment_note = ""
        if assessment.get("priority") == "high":
            assessment_note = "Flagged as high priority. "
        elif assessment.get("priority") == "medium":
            assessment_note = "Flagged as medium priority. "

        return f"{radar_note}{assessment_note}Suggestion was processed through internal assessment pipeline."

    def _build_subsystem_impact(self, assessment: Dict[str, Any]) -> str:
        """Build subsystem impact block."""
        impact = assessment.get("affected_subsystems", [])
        if impact:
            return f"Affects subsystems: {', '.join(impact)}. "
        return "No specific subsystem impact identified."

    def _build_risk_effort(self, risk: str, effort: str) -> str:
        """Build risk and effort block."""
        return f"Implementation risk: {risk}. Effort estimate: {effort}."

    def _build_architectural_fit(self, assessment: Dict[str, Any]) -> str:
        """Build architectural fit block."""
        fit_score = assessment.get("fit_score", 0.5)
        if fit_score >= 0.7:
            return f"Strong architectural fit (score: {fit_score:.2f}). Aligns with current direction."
        elif fit_score >= 0.4:
            return f"Moderate architectural fit (score: {fit_score:.2f}). May require some adaptation."
        else:
            return f"Lower architectural fit (score: {fit_score:.2f}). May need significant redesign."

    def _build_memory_precedent(self, memory: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Build memory precedent block."""
        prior_accepted = memory.get("prior_accepted", [])
        prior_denied = memory.get("prior_denied", [])

        details = {
            "prior_accepted": prior_accepted,
            "prior_denied": prior_denied,
            "count_accepted": len(prior_accepted),
            "count_denied": len(prior_denied),
        }

        if prior_accepted:
            return (
                f"Matches {len(prior_accepted)} prior accepted decision(s). "
                "Consider prior context when evaluating."
            ), details
        elif prior_denied:
            return (
                f"Resembles {len(prior_denied)} prior denied/rejected decision(s). "
                "Review historical context for guidance."
            ), details
        else:
            return "No prior memory found for this suggestion.", details

    def _build_consistency(self, memory: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Build consistency status block."""
        consistency_type = memory.get("consistency_type", "unknown")
        drift_direction = memory.get("drift_direction")
        details = {
            "consistency_type": consistency_type,
            "drift_direction": drift_direction,
        }

        if consistency_type == "consistent":
            return "Consistent with prior accepted direction.", details
        elif consistency_type == "divergent":
            return "Moves away from prior accepted direction.", details
        elif consistency_type == "contradictory":
            return "Directly opposes prior accepted direction.", details
        elif drift_direction:
            return f"Drift detected: {drift_direction}.", details
        else:
            return "No clear consistency pattern identified.", details

    def _build_tradeoff(self, tradeoff: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Build tradeoff context block."""
        details = tradeoff.copy()
        if tradeoff.get("tradeoffs"):
            return (
                "Tradeoffs identified: " + ", ".join(tradeoff["tradeoffs"][:2]) + "."
                if len(tradeoff["tradeoffs"]) > 2
                else "Tradeoffs identified: " + ", ".join(tradeoff["tradeoffs"]) + "."
            ), details
        return "No specific tradeoffs identified.", details

    def _build_recommendation(
        self,
        assessment: Dict[str, Any],
        memory: Dict[str, Any],
        tradeoff: Dict[str, Any],
    ) -> tuple[str, Dict[str, Any]]:
        """Build recommendation block."""
        priority = assessment.get("priority", "medium")
        risk = assessment.get("implementation_risk", "medium")

        # Determine recommendation
        if priority == "high" and risk in ["low", "medium"]:
            rec = "accept"
            rec_text = "RECOMMEND ACCEPTING"
        elif priority == "low":
            rec = "delay"
            rec_text = "RECOMMEND DELAYING"
        elif memory.get("should_archive"):
            rec = "archive"
            rec_text = "RECOMMEND ARCHIVING"
        else:
            rec = "review"
            rec_text = "RECOMMEND FURTHER REVIEW"

        details = {
            "recommendation": rec,
            "priority": priority,
            "risk": risk,
            "should_accept": memory.get("should_accept", False),
            "should_delay": memory.get("delay_recommendation", False),
            "should_archive": memory.get("archive_recommendation", False),
        }

        return f"{rec_text}: {rec.upper()}.", details

    def _build_timing(self, assessment: Dict[str, Any], tradeoff: Dict[str, Any]) -> str:
        """Build timing block."""
        priority = assessment.get("priority", "medium")

        if priority == "high":
            return "Immediate attention required."
        elif priority == "medium":
            return "Plan for next sprint/iteration."
        else:
            return "Schedule for backlog review. Consider delayed implementation."

    def generate_narrative_json(
        self,
        title: str,
        domain: str,
        suggestion_id: Optional[str] = None,
    ) -> str:
        """Generate narrative and return as JSON string."""
        narrative = self.generate_narrative(title, domain, suggestion_id)
        return json.dumps(narrative.to_dict(), indent=2)


def generate_narrative(
    title: str,
    domain: str,
    decision_sources: Dict[str, Any],
    memory_context: Optional[Dict[str, Any]] = None,
    tradeoff_context: Optional[Dict[str, Any]] = None,
    suggestion_id: Optional[str] = None,
) -> UnifiedNarrative:
    """Convenience function to generate a narrative."""
    engine = NarrativeEngine()
    engine.set_decision_sources(decision_sources)
    engine.set_memory_context(memory_context or {})
    engine.set_tradeoff_context(tradeoff_context or {})
    return engine.generate_narrative(title, domain, suggestion_id)
