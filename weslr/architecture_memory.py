# architecture_memory.py - Self-Architecture Core v7: Longitudinal Architecture Memory / Consistency Layer
# Allow WESLR to remember architectural decisions over time and evaluate consistency.
# Operator-first, additive only, reversible, governed.

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class DecisionStatus(str, Enum):
    """Status of an architectural decision."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DENIED = "denied"
    REJECTED = "rejected"
    SNOOZED = "snoozed"
    ARCHIVED = "archived"


class ConsistencyType(str, Enum):
    """Types of consistency relationships."""
    CONSISTENT = "consistent"       # Aligns with accepted direction
    DIVERGENT = "divergent"         # Moves away from accepted direction
    CONTRADICTORY = "contradictory" # Directly opposes accepted direction
    REINFORCEMENT = "reinforcement" # Same direction, stronger signal
    SIMILAR = "similar"             # Similar in scope but different in details
    DRIFT = "drift"                 # Gradual shift toward local optimization


@dataclass
class ArchitectureDecision:
    """An architectural decision with full metadata."""
    
    id: str
    title: str
    description: str
    
    # Decision metadata
    status: str = DecisionStatus.PENDING.value
    accepted_at: Optional[str] = None
    denied_at: Optional[str] = None
    
    # Suggestion metadata (if derived from a suggestion)
    original_suggestion_id: Optional[str] = None
    suggestion_title: Optional[str] = None
    suggestion_category: Optional[str] = None
    
    # Content
    affected_subsystems: List[str] = field(default_factory=list)
    proposals: List[Dict[str, Any]] = field(default_factory=list)
    
    # Scoring
    effort: float = 5.0
    risk: float = 5.0
    fitness_gains: float = 0.0
    strategic_value: float = 0.0
    quick_win_score: float = 0.0
    coherence_score: float = 0.0
    
    # Consistency markers
    consistency_type: Optional[str] = None
    consistency_rationale: Optional[str] = None
    reference_decisions: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "accepted_at": self.accepted_at,
            "denied_at": self.denied_at,
            "original_suggestion_id": self.original_suggestion_id,
            "suggestion_title": self.suggestion_title,
            "suggestion_category": self.suggestion_category,
            "affected_subsystems": self.affected_subsystems,
            "proposals": self.proposals,
            "effort": self.effort,
            "risk": self.risk,
            "fitness_gains": self.fitness_gains,
            "strategic_value": self.strategic_value,
            "quick_win_score": self.quick_win_score,
            "coherence_score": self.coherence_score,
            "consistency_type": self.consistency_type,
            "consistency_rationale": self.consistency_rationale,
            "reference_decisions": self.reference_decisions,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ArchitectureDecision:
        data["affected_subsystems"] = data.get("affected_subsystems", [])
        data["proposals"] = data.get("proposals", [])
        data["reference_decisions"] = data.get("reference_decisions", [])
        return cls(**data)

    def mark_accepted(self, rationale: str = None) -> None:
        """Mark decision as accepted."""
        self.status = DecisionStatus.ACCEPTED.value
        self.accepted_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.updated_at = self.accepted_at
        if rationale:
            self.consistency_rationale = rationale

    def mark_denied(self, rationale: str = None) -> None:
        """Mark decision as denied."""
        self.status = DecisionStatus.DENIED.value
        self.denied_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.updated_at = self.denied_at
        if rationale:
            self.consistency_rationale = rationale

    def mark_rejected(self, rationale: str = None) -> None:
        """Mark decision as rejected (hard rejection, not just denied)."""
        self.status = DecisionStatus.REJECTED.value
        self.denied_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.updated_at = self.denied_at
        if rationale:
            self.consistency_rationale = rationale


@dataclass
class ConsistencyReport:
    """Report on consistency of a new recommendation."""
    
    recommendation_id: str
    recommendation_title: str
    
    consistency_type: str
    consistency_rationale: str
    
    # Match details
    matching_decisions: List[str] = field(default_factory=list)
    strength_ratio: float = 1.0
    drift_direction: Optional[str] = None
    drift_magnitude: float = 0.0
    
    # Action recommendation
    should_accept: bool = False
    should_reopen: bool = False
    should_archive: bool = False
    action_rationale: str = ""
    
    # Timing
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "recommendation_title": self.recommendation_title,
            "consistency_type": self.consistency_type,
            "consistency_rationale": self.consistency_rationale,
            "matching_decisions": self.matching_decisions,
            "strength_ratio": self.strength_ratio,
            "drift_direction": self.drift_direction,
            "drift_magnitude": self.drift_magnitude,
            "should_accept": self.should_accept,
            "should_reopen": self.should_reopen,
            "should_archive": self.should_archive,
            "action_rationale": self.action_rationale,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConsistencyReport:
        data["matching_decisions"] = data.get("matching_decisions", [])
        return cls(**data)


class ArchitectureMemory:
    """Longitudinal memory for architectural decisions."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("continuity/architecture_memory/decisions.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.decisions: List[ArchitectureDecision] = []
        self._load_decisions()
    
    def _load_decisions(self) -> None:
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.decisions = [ArchitectureDecision.from_dict(d) for d in data.get("decisions", [])]
            except (json.JSONDecodeError, IOError):
                self.decisions = []
    
    def _save_decisions(self) -> None:
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump({
                "decisions": [d.to_dict() for d in self.decisions],
                "last_updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }, f, indent=2)
    
    def add_decision(self, decision: ArchitectureDecision) -> ArchitectureDecision:
        """Add a new decision to memory."""
        if not decision.id:
            decision.id = str(uuid.uuid4())[:8]
        self.decisions.append(decision)
        self._save_decisions()
        return decision
    
    def get_decision(self, decision_id: str) -> Optional[ArchitectureDecision]:
        """Retrieve a decision by ID."""
        for d in self.decisions:
            if d.id == decision_id:
                return d
        return None
    
    def get_accepted_decisions(self) -> List[ArchitectureDecision]:
        """Get all accepted decisions."""
        return [d for d in self.decisions if d.status == DecisionStatus.ACCEPTED.value]
    
    def get_denied_decisions(self) -> List[ArchitectureDecision]:
        """Get all denied/rejected decisions."""
        return [d for d in self.decisions if d.status in [DecisionStatus.DENIED.value, DecisionStatus.REJECTED.value]]
    
    def get_decisions_by_subsystem(self, subsystem: str) -> List[ArchitectureDecision]:
        """Get decisions affecting a specific subsystem."""
        return [d for d in self.decisions if subsystem in d.affected_subsystems]
    
    def get_decisions_by_suggestion(self, suggestion_id: str) -> List[ArchitectureDecision]:
        """Get decisions derived from a suggestion."""
        return [d for d in self.decisions if d.original_suggestion_id == suggestion_id]
    
    def update_decision(self, decision_id: str, **kwargs) -> Optional[ArchitectureDecision]:
        """Update an existing decision."""
        decision = self.get_decision(decision_id)
        if decision:
            for key, value in kwargs.items():
                if hasattr(decision, key):
                    setattr(decision, key, value)
            decision.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            self._save_decisions()
        return decision
    
    def delete_decision(self, decision_id: str) -> bool:
        """Delete a decision (only if not accepted)."""
        for i, d in enumerate(self.decisions):
            if d.id == decision_id:
                if d.status == DecisionStatus.ACCEPTED.value:
                    return False  # Cannot delete accepted decisions
                self.decisions.pop(i)
                self._save_decisions()
                return True
        return False
    
    def search_decisions(self, query: str) -> List[ArchitectureDecision]:
        """Search decisions by title or description."""
        query = query.lower()
        return [
            d for d in self.decisions
            if query in d.title.lower() or query in d.description.lower()
        ]
    
    def get_decision_history(self) -> List[Dict[str, Any]]:
        """Get a timeline of decisions."""
        return [
            {
                "id": d.id,
                "title": d.title,
                "status": d.status,
                "created_at": d.created_at,
                "updated_at": d.updated_at,
            }
            for d in sorted(self.decisions, key=lambda x: x.created_at)
        ]


class ConsistencyEngine:
    """Engine for evaluating consistency of new recommendations."""
    
    @staticmethod
    def _get_decision_by_id(decisions: List[ArchitectureDecision], decision_id: str) -> Optional[ArchitectureDecision]:
        """Helper to get decision by ID from a list."""
        for d in decisions:
            if d.id == decision_id:
                return d
        return None
    
    @staticmethod
    def _get_strength_ratio(
        decision: ArchitectureDecision,
        matching_accepted: List[Tuple[str, float]],
        accepted: List[ArchitectureDecision],
    ) -> float:
        """Calculate strength ratio for a decision vs prior decisions."""
        decision_score = decision.effort + decision.risk + decision.fitness_gains + decision.strategic_value
        
        if len(matching_accepted) == 1:
            prior_id = matching_accepted[0][0]
            prior_decision = ConsistencyEngine._get_decision_by_id(accepted, prior_id)
            if prior_decision:
                prior_score = prior_decision.effort + prior_decision.risk + prior_decision.fitness_gains + prior_decision.strategic_value
                return decision_score / prior_score if prior_score > 0 else 1.0
            return 1.0
        else:
            # For multiple matching, calculate average
            accepted_ids = [m[0] for m in matching_accepted]
            accepted_scores = [m[1] for m in matching_accepted]
            avg_score = sum(accepted[i].effort * accepted_scores[i] for i in range(len(accepted))) / len(accepted)
            return decision_score / avg_score if avg_score > 0 else 1.0
    
    @staticmethod
    def evaluate_consistency(
        decision: ArchitectureDecision,
        memory: ArchitectureMemory,
        weight_threshold: float = 0.7,
    ) -> ConsistencyReport:
        """
        Evaluate if a decision is consistent with prior architectural direction.
        
        Returns a ConsistencyReport with:
        - consistency_type: how the decision relates to prior decisions
        - matching_decisions: IDs of similar prior decisions
        - strength_ratio: how strong this is vs similar prior decisions
        - drift_direction: if drifting toward local optimization or strategic coherence
        - action recommendation: should accept, reopen, or archive?
        """
        accepted = memory.get_accepted_decisions()
        denied = memory.get_denied_decisions()
        
        # Find matching decisions
        matching_accepted = []
        matching_denied = []
        
        for d in accepted:
            match_score = ConsistencyEngine._match_score(decision, d)
            if match_score >= weight_threshold:
                matching_accepted.append((d.id, match_score))
        
        for d in denied:
            match_score = ConsistencyEngine._match_score(decision, d)
            if match_score >= weight_threshold:
                matching_denied.append((d.id, match_score))
        
        # Determine consistency type
        consistency_type = ConsistencyType.CONSISTENT.value
        drift_direction = None
        drift_magnitude = 0.0
        strength_ratio = 1.0
        
        if matching_accepted:
            # Compare with accepted decisions - use first element (id, score)
            accepted_ids = [m[0] for m in matching_accepted]
            accepted_scores = [m[1] for m in matching_accepted]
            avg_effort = sum(accepted[i].effort * accepted_scores[i] for i in range(len(accepted))) / len(accepted)
            avg_risk = sum(accepted[i].risk * accepted_scores[i] for i in range(len(accepted))) / len(accepted)
            
            # Check for drift
            if decision.effort > avg_effort * 1.5:
                drift_direction = "local_optimization"
                drift_magnitude = (decision.effort - avg_effort) / avg_effort
            elif decision.effort < avg_effort * 0.5:
                drift_direction = "strategic_coherence"
                drift_magnitude = (avg_effort - decision.effort) / avg_effort
            
            # Compare strength - use the single decision's values
            strength_ratio = ConsistencyEngine._get_strength_ratio(decision, matching_accepted, accepted)
            
            # Determine type
            if matching_denied:
                # Mixed signals - check which is stronger
                if len(matching_accepted) > len(matching_denied):
                    consistency_type = ConsistencyType.CONSISTENT.value
                else:
                    consistency_type = ConsistencyType.CONTRADICTORY.value
            elif drift_magnitude > 0.5:
                consistency_type = ConsistencyType.DRIFT.value
            else:
                consistency_type = ConsistencyType.CONSISTENT.value
            
            # Determine action
            should_accept = consistency_type in [
                ConsistencyType.CONSISTENT.value,
                ConsistencyType.REINFORCEMENT.value,
            ]
            should_reopen = consistency_type == ConsistencyType.CONTRADICTORY.value
            should_archive = len(matching_accepted) == 0 and len(matching_denied) > 2
        else:
            # No direct match
            if len(matching_denied) > 0:
                consistency_type = ConsistencyType.DIVERGENT.value
                should_accept = False
                should_reopen = True
                should_archive = False
            else:
                # New direction - could be good or bad
                if decision.strategic_value > 7:
                    consistency_type = ConsistencyType.CONSISTENT.value
                    should_accept = True
                    should_reopen = False
                    should_archive = False
                else:
                    consistency_type = ConsistencyType.SIMILAR.value
                    should_accept = False
                    should_reopen = True
                    should_archive = False
        
        # Build rationale
        rationale_parts = []
        if matching_accepted:
            rationale_parts.append(f"Matches {len(matching_accepted)} prior accepted decision(s)")
        if matching_denied:
            rationale_parts.append(f"Resembles {len(matching_denied)} prior denied decision(s)")
        if drift_direction:
            rationale_parts.append(f"Drift detected: {drift_direction}")
        if strength_ratio > 1.0:
            rationale_parts.append(f"Stronger signal than prior similar decisions (x{strength_ratio:.1f})")
        elif strength_ratio < 1.0:
            rationale_parts.append(f"Weaker signal than prior similar decisions (x{strength_ratio:.1f})")
        
        return ConsistencyReport(
            recommendation_id=decision.id,
            recommendation_title=decision.title,
            consistency_type=consistency_type,
            consistency_rationale="; ".join(rationale_parts) if rationale_parts else "No prior decisions found",
            matching_decisions=[m[0] for m in matching_accepted] + [m[0] for m in matching_denied],
            strength_ratio=round(strength_ratio, 2),
            drift_direction=drift_direction,
            drift_magnitude=round(drift_magnitude, 2),
            should_accept=should_accept,
            should_reopen=should_reopen,
            should_archive=should_archive,
            action_rationale=f"{'Accept' if should_accept else 'Reopen/Review'} recommendation",
        )
    
    @staticmethod
    def _match_score(a: ArchitectureDecision, b: ArchitectureDecision) -> float:
        """Compute match score between two decisions (0-1)."""
        score = 0.0
        weight = 0.0
        
        # Subsystem overlap (30%)
        if a.affected_subsystems and b.affected_subsystems:
            common = set(a.affected_subsystems) & set(b.affected_subsystems)
            total = set(a.affected_subsystems) | set(b.affected_subsystems)
            if total:
                score += 0.3 * len(common) / len(total)
                weight += 0.3
        
        # Effort similarity (20%)
        if a.effort > 0 and b.effort > 0:
            effort_ratio = min(a.effort, b.effort) / max(a.effort, b.effort)
            score += 0.2 * effort_ratio
            weight += 0.2
        
        # Risk similarity (20%)
        if a.risk > 0 and b.risk > 0:
            risk_ratio = min(a.risk, b.risk) / max(a.risk, b.risk)
            score += 0.2 * risk_ratio
            weight += 0.2
        
        # Strategic value alignment (30%)
        if a.strategic_value > 0 and b.strategic_value > 0:
            value_ratio = min(a.strategic_value, b.strategic_value) / max(a.strategic_value, b.strategic_value)
            score += 0.3 * value_ratio
            weight += 0.3
        
        return score / weight if weight > 0 else 0.0
    
    @staticmethod
    def detect_drift(
        memory: ArchitectureMemory,
        window_size: int = 5,
        threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Detect if the system is drifting from strategic coherence.
        
        Analyzes recent accepted decisions for drift patterns.
        """
        accepted = memory.get_accepted_decisions()
        if len(accepted) < window_size:
            return {
                "drift_detected": False,
                "message": "Not enough decisions to detect drift",
                "recent_decisions": len(accepted),
                "window_size": window_size,
            }
        
        # Get recent decisions
        recent = accepted[-window_size:]
        
        # Compute average metrics
        avg_effort = sum(d.effort for d in recent) / len(recent)
        avg_risk = sum(d.risk for d in recent) / len(recent)
        avg_strategic = sum(d.strategic_value for d in recent) / len(recent)
        avg_coherence = sum(d.coherence_score for d in recent) / len(recent)
        
        # Check for drift patterns
        effort_trend = []
        for i in range(1, len(recent)):
            if recent[i-1].effort > 0:
                effort_trend.append((recent[i].effort - recent[i-1].effort) / recent[i-1].effort)
        
        # Detect local optimization drift (effort increasing without strategic gain)
        drift_detected = False
        drift_direction = None
        drift_reason = []
        
        if effort_trend and sum(effort_trend) / len(effort_trend) > threshold:
            drift_detected = True
            drift_direction = "local_optimization"
            drift_reason.append("Effort increasing without proportional strategic gain")
        
        if avg_strategic < 5.0 and avg_coherence < 5.0:
            drift_detected = True
            drift_direction = "local_optimization"
            drift_reason.append("Low strategic value and coherence")
        
        if drift_detected:
            return {
                "drift_detected": True,
                "drift_direction": drift_direction,
                "drift_reason": drift_reason,
                "recent_avg_effort": round(avg_effort, 2),
                "recent_avg_strategic": round(avg_strategic, 2),
                "recent_avg_coherence": round(avg_coherence, 2),
                "window_size": window_size,
            }
        
        return {
            "drift_detected": False,
            "message": "No significant drift detected",
            "recent_avg_effort": round(avg_effort, 2),
            "recent_avg_strategic": round(avg_strategic, 2),
            "recent_avg_coherence": round(avg_coherence, 2),
            "window_size": window_size,
        }


# Convenience functions
def create_decision(
    title: str,
    description: str,
    affected_subsystems: List[str] = None,
    author: str = "operator",
) -> ArchitectureDecision:
    """Factory to create a new decision."""
    return ArchitectureDecision(
        id=str(uuid.uuid4())[:8],
        title=title,
        description=description,
        affected_subsystems=affected_subsystems or [],
        author=author,
    )


def from_scenario(scenario, author: str = "operator") -> ArchitectureDecision:
    """Convert a scenario to an architecture decision."""
    return ArchitectureDecision(
        id=str(uuid.uuid4())[:8],
        title=scenario.title,
        description=scenario.description,
        affected_subsystems=scenario.affected_subsystems,
        proposals=[p.to_dict() for p in scenario.proposals],
        effort=scenario.effort,
        risk=scenario.risk,
        fitness_gains=scenario.fitness_gains,
        strategic_value=scenario.strategic_value,
        quick_win_score=scenario.quick_win_score,
        coherence_score=scenario.coherence_score,
        author=author,
    )
