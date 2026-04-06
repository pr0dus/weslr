# scenario_model.py - Self-Architecture Core v6: Scenario Comparison / Roadmap Tradeoff Layer
# Allow WESLR to compare bundles of changes / roadmap options / sequencing choices in a governed way.
# Operator-first, additive only, reversible, governed.

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class StrategicHorizon(str, Enum):
    """Strategic time horizon."""
    IMMEDIATE = "immediate"        # 0-2 weeks
    SHORT_TERM = "short_term"      # 2-6 weeks
    MEDIUM_TERM = "medium_term"    # 1-3 months
    LONG_TERM = "long_term"        # 3-6+ months


class ScenarioScore:
    """Numeric scores for scenario comparison."""
    
    def __init__(
        self,
        effort: float = 5.0,
        risk: float = 5.0,
        fitness_gains: float = 0.0,
        strategic_value: float = 0.0,
        quick_win_score: float = 0.0,
        coherence_score: float = 0.0,
    ):
        self.effort = effort              # 0-10, lower is better
        self.risk = risk                  # 0-10, lower is better
        self.fitness_gains = fitness_gains  # 0-10, higher is better
        self.strategic_value = strategic_value  # 0-10, higher is better
        self.quick_win_score = quick_win_score  # 0-10, higher is better
        self.coherence_score = coherence_score  # 0-10, higher is better

    def to_dict(self) -> Dict[str, float]:
        return {
            "effort": self.effort,
            "risk": self.risk,
            "fitness_gains": self.fitness_gains,
            "strategic_value": self.strategic_value,
            "quick_win_score": self.quick_win_score,
            "coherence_score": self.coherence_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> ScenarioScore:
        return cls(**data)


@dataclass
class ScenarioProposal:
    """A proposal (change suggestion) included in a scenario."""
    id: str
    title: str
    description: str
    affected_subsystems: List[str] = field(default_factory=list)
    quick_win: bool = False
    strategic: bool = False
    effort: Optional[float] = None
    risk: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "affected_subsystems": self.affected_subsystems,
            "quick_win": self.quick_win,
            "strategic": self.strategic,
            "effort": self.effort,
            "risk": self.risk,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ScenarioProposal:
        data["affected_subsystems"] = data.get("affected_subsystems", [])
        return cls(**data)


@dataclass
class Scenario:
    """A roadmap scenario: bundle of proposals, sequencing, and tradeoffs."""
    
    id: str
    title: str
    description: str
    
    # Content
    proposals: List[ScenarioProposal] = field(default_factory=list)
    affected_subsystems: List[str] = field(default_factory=list)
    
    # Scoring
    effort: float = 5.0
    risk: float = 5.0
    fitness_gains: float = 0.0
    strategic_value: float = 0.0
    quick_win_score: float = 0.0
    coherence_score: float = 0.0
    
    # Metadata
    strategic_horizon: str = StrategicHorizon.SHORT_TERM.value
    sequencing_assumptions: List[str] = field(default_factory=list)
    rationale: Optional[str] = None
    
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "proposals": [p.to_dict() for p in self.proposals],
            "affected_subsystems": self.affected_subsystems,
            "effort": self.effort,
            "risk": self.risk,
            "fitness_gains": self.fitness_gains,
            "strategic_value": self.strategic_value,
            "quick_win_score": self.quick_win_score,
            "coherence_score": self.coherence_score,
            "strategic_horizon": self.strategic_horizon,
            "sequencing_assumptions": self.sequencing_assumptions,
            "rationale": self.rationale,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Scenario:
        data["proposals"] = [ScenarioProposal.from_dict(p) for p in data.get("proposals", [])]
        data["affected_subsystems"] = data.get("affected_subsystems", [])
        data["sequencing_assumptions"] = data.get("sequencing_assumptions", [])
        return cls(**data)

    def add_proposal(self, proposal: ScenarioProposal) -> None:
        """Add a proposal to the scenario."""
        self.proposals.append(proposal)
        if proposal.affected_subsystems:
            for sub in proposal.affected_subsystems:
                if sub not in self.affected_subsystems:
                    self.affected_subsystems.append(sub)
        # Update cumulative metrics
        if proposal.effort:
            self.effort += proposal.effort * 0.5  # Reduce weight for additive scenario
        if proposal.risk:
            self.risk += proposal.risk * 0.5  # Reduce weight for additive scenario
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def compute_scores(self) -> ScenarioScore:
        """Compute combined scores for this scenario."""
        return ScenarioScore(
            effort=min(self.effort, 10.0),
            risk=min(self.risk, 10.0),
            fitness_gains=min(self.fitness_gains + len(self.proposals) * 0.5, 10.0),
            strategic_value=self.strategic_value + (1.0 if any(p.strategic for p in self.proposals) else 0.0),
            quick_win_score=self.quick_win_score + (1.0 if any(p.quick_win for p in self.proposals) else 0.0),
            coherence_score=self.coherence_score + (len(self.proposals) * 0.2),
        )


@dataclass
class TradeoffSummary:
    """Summary of tradeoffs between scenarios."""
    
    better_scenario: str
    tradeoffs: List[str] = field(default_factory=list)
    rationale: Optional[str] = None
    timing_recommendation: Optional[str] = None
    quick_win_interpretation: bool = False
    strategic_interpretation: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "better_scenario": self.better_scenario,
            "tradeoffs": self.tradeoffs,
            "rationale": self.rationale,
            "timing_recommendation": self.timing_recommendation,
            "quick_win_interpretation": self.quick_win_interpretation,
            "strategic_interpretation": self.strategic_interpretation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TradeoffSummary:
        data["tradeoffs"] = data.get("tradeoffs", [])
        return cls(**data)


class RoadmapTradeoffEngine:
    """Engine for comparing scenarios and recommending roadmaps."""
    
    @staticmethod
    def compare_scenarios(
        scenario_a: Scenario,
        scenario_b: Scenario,
        criteria: List[str] = None,
    ) -> TradeoffSummary:
        """
        Compare two scenarios and return which is better + tradeoffs.
        
        Criteria: ["risk", "effort", "fitness", "strategic", "quick_win", "coherence"]
        """
        if criteria is None:
            criteria = ["risk", "effort", "fitness", "strategic", "quick_win", "coherence"]
        
        score_a = scenario_a.compute_scores()
        score_b = scenario_b.compute_scores()
        
        tradeoffs = []
        better = "scenario_a"
        preferred_score_a = 0
        preferred_score_b = 0
        
        # Compare by each criterion
        for crit in criteria:
            val_a = getattr(score_a, crit + ("_score" if crit in ["quick_win", "coherence"] else ""), 0.0)
            val_b = getattr(score_b, crit + ("_score" if crit in ["quick_win", "coherence"] else ""), 0.0)
            
            # For effort and risk, lower is better
            if crit in ["effort", "risk"]:
                if val_a < val_b:
                    preferred_score_a += 1
                    tradeoffs.append(f"{crit}: Scenario A is better (lower {crit})")
                elif val_b < val_a:
                    preferred_score_b += 1
                    better = "scenario_b"
                    tradeoffs.append(f"{crit}: Scenario B is better (lower {crit})")
                else:
                    tradeoffs.append(f"{crit}: Equal effort")
            else:
                # For other criteria, higher is better
                if val_a > val_b:
                    preferred_score_a += 1
                    tradeoffs.append(f"{crit}: Scenario A is better (higher {crit})")
                elif val_b > val_a:
                    preferred_score_b += 1
                    better = "scenario_b"
                    tradeoffs.append(f"{crit}: Scenario B is better (higher {crit})")
                else:
                    tradeoffs.append(f"{crit}: Equal value")
        
        # Build rationale
        rationale_parts = []
        if preferred_score_a > preferred_score_b:
            rationale_parts.append("Scenario A wins on most criteria")
        elif preferred_score_b > preferred_score_a:
            rationale_parts.append("Scenario B wins on most criteria")
        else:
            rationale_parts.append("Split decision - consider sequencing or timing")
        
        # Determine interpretation
        a_quick = any(p.quick_win for p in scenario_a.proposals)
        b_quick = any(p.quick_win for p in scenario_b.proposals)
        a_strategic = any(p.strategic for p in scenario_a.proposals)
        b_strategic = any(p.strategic for p in scenario_b.proposals)
        
        quick_win_interpretation = a_quick and not b_quick
        strategic_interpretation = a_strategic and not b_strategic
        
        if not quick_win_interpretation and not strategic_interpretation:
            if preferred_score_a >= preferred_score_b:
                quick_win_interpretation = a_quick
                strategic_interpretation = a_strategic
            else:
                quick_win_interpretation = b_quick
                strategic_interpretation = b_strategic
        
        # Timing recommendation
        timing = "Immediate execution" if (score_a.quick_win_score > 7 or score_b.quick_win_score > 7) else "Phased rollout"
        if score_a.strategic_value > 7 or score_b.strategic_value > 7:
            timing = "Long-term strategic planning required"
        
        return TradeoffSummary(
            better_scenario=better,
            tradeoffs=tradeoffs,
            rationale="; ".join(rationale_parts),
            timing_recommendation=timing,
            quick_win_interpretation=quick_win_interpretation,
            strategic_interpretation=strategic_interpretation,
        )

    @staticmethod
    def recommend_sequencing(scenarios: List[Scenario]) -> List[str]:
        """Recommend execution order for multiple scenarios."""
        # Sort by quick_win_score descending, then by risk ascending
        sorted_scenarios = sorted(
            scenarios,
            key=lambda s: (-s.compute_scores().quick_win_score, s.compute_scores().risk)
        )
        return [s.id for s in sorted_scenarios]


def create_scenario(
    title: str,
    description: str,
    proposals: List[ScenarioProposal] = None,
    author: str = "operator",
) -> Scenario:
    """Factory to create a new scenario."""
    return Scenario(
        id=str(uuid.uuid4())[:8],
        title=title,
        description=description,
        proposals=proposals or [],
        author=author,
    )


def create_quick_win_scenario(
    title: str,
    description: str,
    proposals: List[ScenarioProposal],
    author: str = "operator",
) -> Scenario:
    """Create a quick-win focused scenario."""
    scenario = create_scenario(title, description, proposals, author)
    scenario.strategic_horizon = StrategicHorizon.IMMEDIATE.value
    scenario.quick_win_score = 8.0
    return scenario


def create_strategic_scenario(
    title: str,
    description: str,
    proposals: List[ScenarioProposal],
    author: str = "operator",
) -> Scenario:
    """Create a strategic long-term scenario."""
    scenario = create_scenario(title, description, proposals, author)
    scenario.strategic_horizon = StrategicHorizon.LONG_TERM.value
    scenario.strategic_value = 8.0
    return scenario
