# simulation.py - WESLR v44: Simulation / Dry-Run Impact Layer
# Creates a governed dry-run layer so WESLR can simulate likely effects, risk shifts,
# trust shifts, and escalation probability before a proposal or recommendation is surfaced.
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


class SimulationType(str, Enum):
    """Types of simulations."""
    PROPOSAL_IMPACT = "proposal_impact"  # Impact of a proposal
    RECOMMENDATION_IMPLICATIONS = "recommendation_implications"  # Implications of a recommendation
    ACTION_CONSEQUENCES = "action_consequences"  # Consequences of an action
    STATE_TRANSITION = "state_transition"  # Transition to a new state
    RISK_EXPOSURE = "risk_exposure"  # Risk exposure simulation
    TRUST_DYNAMICS = "trust_dynamics"  # Trust relationship simulation


class ImpactLevel(str, Enum):
    """Level of impact."""
    NONE = "none"  # No impact
    MINIMAL = "minimal"  # Negligible impact
    MODERATE = "moderate"  # Noticeable but manageable impact
    SIGNIFICANT = "significant"  # Substantial impact
    CRITICAL = "critical"  # Critical impact requiring immediate attention


class ConfidenceLevel(str, Enum):
    """Confidence level for simulation results."""
    LOW = "low"  # 0.0-0.4: High uncertainty
    MEDIUM = "medium"  # 0.4-0.7: Moderate uncertainty
    HIGH = "high"  # 0.7-0.9: Low uncertainty
    VERY_HIGH = "very_high"  # 0.9-1.0: Very low uncertainty


class RollbackFeasibility(str, Enum):
    """Feasibility of rollback."""
    EASY = "easy"  # Simple rollback available
    MODERATE = "moderate"  # Requires some effort
    DIFFICULT = "difficult"  # Complex rollback
    IMPOSSIBLE = "impossible"  # No rollback possible


class SimulationStatus(str, Enum):
    """Status of a simulation."""
    PENDING = "pending"  # Pending execution
    RUNNING = "running"  # Currently executing
    COMPLETE = "complete"  # Completed successfully
    PARTIAL = "partial"  # Partial results
    FAILED = "failed"  # Simulation failed


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class ImpactProjection:
    """Projection of impact for a simulated action."""
    
    impact_id: str
    category: str  # ImpactLevel.value
    magnitude: float = 0.0  # 0.0-1.0
    scope: List[str] = field(default_factory=list)  # Affected areas
    
    # Expected change
    expected_change: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5  # 0.0-1.0
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "impact_id": self.impact_id,
            "category": self.category,
            "magnitude": self.magnitude,
            "scope": self.scope,
            "expected_change": self.expected_change,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ImpactProjection:
        data["scope"] = data.get("scope", [])
        data["expected_change"] = data.get("expected_change", {})
        return cls(**data)


@dataclass
class SimulationResult:
    """Complete simulation result."""
    
    simulation_id: str
    simulation_type: str  # SimulationType.value
    
    # Input
    action: str
    context: Optional[str] = None
    
    # Outputs
    expected_impact: List[Dict[str, Any]] = field(default_factory=list)
    risk_delta: float = 0.0  # Change in risk (positive = increase)
    trust_delta: float = 0.0  # Change in trust (positive = increase)
    tension_delta: float = 0.0  # Change in tension (positive = increase)
    escalation_probability: float = 0.0  # 0.0-1.0
    
    # Rollback
    rollback_feasibility: str = RollbackFeasibility.MODERATE.value
    rollback_complexity: int = 3  # 1-10
    
    # Confidence
    confidence_level: str = ConfidenceLevel.MEDIUM.value
    confidence_range: Dict[str, float] = field(default_factory=lambda: {"min": 0.3, "max": 0.7})
    
    # Dry-run explanation
    explanation: Optional[str] = None
    assumptions: List[str] = field(default_factory=list)
    
    # Status
    status: str = SimulationStatus.PENDING.value
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    completed_at: Optional[str] = None
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "simulation_type": self.simulation_type,
            "action": self.action,
            "context": self.context,
            "expected_impact": self.expected_impact,
            "risk_delta": self.risk_delta,
            "trust_delta": self.trust_delta,
            "tension_delta": self.tension_delta,
            "escalation_probability": self.escalation_probability,
            "rollback_feasibility": self.rollback_feasibility,
            "rollback_complexity": self.rollback_complexity,
            "confidence_level": self.confidence_level,
            "confidence_range": self.confidence_range,
            "explanation": self.explanation,
            "assumptions": self.assumptions,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SimulationResult:
        data["expected_impact"] = data.get("expected_impact", [])
        data["assumptions"] = data.get("assumptions", [])
        data["confidence_range"] = data.get("confidence_range", {"min": 0.3, "max": 0.7})
        return cls(**data)


@dataclass
class DryRunSummary:
    """Summary of dry-run simulation results."""
    
    summary_id: str
    affected_object_id: str
    affected_object_type: str
    
    # Simulation results
    simulations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Aggregate analysis
    aggregate_risk_delta: float = 0.0
    aggregate_trust_delta: float = 0.0
    aggregate_escalation_probability: float = 0.0
    
    # Top concerns
    top_concerns: List[str] = field(default_factory=list)
    
    # Recommendation
    recommendation: Optional[str] = None
    confidence_level: str = ConfidenceLevel.MEDIUM.value
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "affected_object_id": self.affected_object_id,
            "affected_object_type": self.affected_object_type,
            "simulation_count": len(self.simulations),
            "simulations": self.simulations,
            "aggregate_risk_delta": self.aggregate_risk_delta,
            "aggregate_trust_delta": self.aggregate_trust_delta,
            "aggregate_escalation_probability": self.aggregate_escalation_probability,
            "top_concerns": self.top_concerns,
            "recommendation": self.recommendation,
            "confidence_level": self.confidence_level,
            "created_at": self.created_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DryRunSummary:
        # Filter out computed fields
        data = {k: v for k, v in data.items() if k in ["summary_id", "affected_object_id", "affected_object_type", "simulations", "aggregate_risk_delta", "aggregate_trust_delta", "aggregate_escalation_probability", "top_concerns", "recommendation", "confidence_level", "created_at", "author"]}
        data["simulations"] = data.get("simulations", [])
        data["top_concerns"] = data.get("top_concerns", [])
        return cls(**data)


# ============================================================================
# SIMULATION ENGINE
# ============================================================================


class SimulationEngine:
    """Engine for managing dry-run simulations and impact projections.
    
    Provides transparent, reversible simulation capabilities.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize simulation engine."""
        self.storage_path = storage_path or "/data/data/com.termux/files/home/.openclaw/workspace/weslr/simulation/"
        self.simulations: Dict[str, SimulationResult] = {}
        self.dry_runs: Dict[str, DryRunSummary] = {}
        self._ensure_storage_exists()
        self._load_simulations()
        self._load_dry_runs()
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory exists."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _load_simulations(self) -> None:
        """Load simulations from storage."""
        import os
        import glob
        
        if not os.path.exists(self.storage_path):
            return
        
        for filepath in glob.glob(os.path.join(self.storage_path, "*_simulation.json")):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    simulation = SimulationResult.from_dict(data)
                    self.simulations[simulation.simulation_id] = simulation
            except Exception:
                continue
    
    def _load_dry_runs(self) -> None:
        """Load dry runs from storage."""
        import os
        import glob
        
        if not os.path.exists(self.storage_path):
            return
        
        for filepath in glob.glob(os.path.join(self.storage_path, "*_dry_run.json")):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    dry_run = DryRunSummary.from_dict(data)
                    self.dry_runs[dry_run.summary_id] = dry_run
            except Exception:
                continue
    
    def create_simulation(
        self,
        simulation_id: str,
        simulation_type: str,
        action: str,
        context: Optional[str] = None,
        author: Optional[str] = None,
    ) -> SimulationResult:
        """Create a new simulation."""
        simulation = SimulationResult(
            simulation_id=simulation_id,
            simulation_type=simulation_type,
            action=action,
            context=context,
            author=author,
        )
        self.simulations[simulation_id] = simulation
        self._save_simulation(simulation)
        return simulation
    
    def run_simulation(
        self,
        simulation_id: str,
        expected_impact: List[Dict[str, Any]] = None,
        risk_delta: float = 0.0,
        trust_delta: float = 0.0,
        tension_delta: float = 0.0,
        escalation_probability: float = 0.0,
        rollback_feasibility: str = RollbackFeasibility.MODERATE.value,
        rollback_complexity: int = 3,
        confidence_level: str = ConfidenceLevel.MEDIUM.value,
        explanation: Optional[str] = None,
        assumptions: List[str] = None,
    ) -> SimulationResult:
        """Run a simulation and populate results."""
        simulation = self.get_simulation(simulation_id)
        if not simulation:
            raise ValueError(f"Simulation not found: {simulation_id}")
        
        # Set defaults
        if expected_impact is None:
            expected_impact = []
        if assumptions is None:
            assumptions = []
        
        # Update simulation
        simulation.expected_impact = expected_impact
        simulation.risk_delta = risk_delta
        simulation.trust_delta = trust_delta
        simulation.tension_delta = tension_delta
        simulation.escalation_probability = escalation_probability
        simulation.rollback_feasibility = rollback_feasibility
        simulation.rollback_complexity = rollback_complexity
        simulation.confidence_level = confidence_level
        simulation.confidence_range = self._calculate_confidence_range(confidence_level)
        simulation.explanation = explanation
        simulation.assumptions = assumptions
        simulation.status = SimulationStatus.COMPLETE.value
        simulation.completed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        self._save_simulation(simulation)
        return simulation
    
    def _calculate_confidence_range(self, level: str) -> Dict[str, float]:
        """Calculate confidence range based on level."""
        ranges = {
            ConfidenceLevel.LOW.value: {"min": 0.0, "max": 0.4},
            ConfidenceLevel.MEDIUM.value: {"min": 0.3, "max": 0.7},
            ConfidenceLevel.HIGH.value: {"min": 0.6, "max": 0.9},
            ConfidenceLevel.VERY_HIGH.value: {"min": 0.85, "max": 1.0},
        }
        return ranges.get(level, {"min": 0.3, "max": 0.7})
    
    def get_simulation(self, simulation_id: str) -> Optional[SimulationResult]:
        """Get a simulation by ID."""
        return self.simulations.get(simulation_id)
    
    def _save_simulation(self, simulation: SimulationResult) -> None:
        """Save a simulation to storage."""
        import os
        
        filepath = os.path.join(self.storage_path, f"{simulation.simulation_id}_simulation.json")
        with open(filepath, "w") as f:
            json.dump(simulation.to_dict(), f, indent=2)
    
    def create_dry_run_summary(
        self,
        summary_id: str,
        affected_object_id: str,
        affected_object_type: str,
        simulations: List[str],
        author: Optional[str] = None,
    ) -> DryRunSummary:
        """Create a dry-run summary from simulations."""
        summary = DryRunSummary(
            summary_id=summary_id,
            affected_object_id=affected_object_id,
            affected_object_type=affected_object_type,
            author=author,
        )
        
        # Load simulations
        for sim_id in simulations:
            sim = self.get_simulation(sim_id)
            if sim:
                summary.simulations.append(sim.to_dict())
        
        # Aggregate results
        if summary.simulations:
            summary.aggregate_risk_delta = sum(s.get("risk_delta", 0) for s in summary.simulations)
            summary.aggregate_trust_delta = sum(s.get("trust_delta", 0) for s in summary.simulations)
            summary.aggregate_escalation_probability = max(
                s.get("escalation_probability", 0) for s in summary.simulations
            )
        
        self.dry_runs[summary_id] = summary
        self._save_dry_run(summary)
        return summary
    
    def get_dry_run(self, summary_id: str) -> Optional[DryRunSummary]:
        """Get a dry-run summary by ID."""
        return self.dry_runs.get(summary_id)
    
    def _save_dry_run(self, dry_run: DryRunSummary) -> None:
        """Save a dry run to storage."""
        import os
        
        filepath = os.path.join(self.storage_path, f"{dry_run.summary_id}_dry_run.json")
        with open(filepath, "w") as f:
            json.dump(dry_run.to_dict(), f, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary."""
        return {
            "simulation_count": len(self.simulations),
            "dry_run_count": len(self.dry_runs),
            "simulations": {k: v.to_dict() for k, v in self.simulations.items()},
            "dry_runs": {k: v.to_dict() for k, v in self.dry_runs.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_governance_surface(
    governance_dict: Dict[str, Any],
    simulation_engine: SimulationEngine = None,
    affected_object_id: str = None,
) -> Dict[str, Any]:
    """Add dry-run context to governance surface.
    
    This is purely additive — no migration required.
    
    v44: Simulation provides dry-run projections for governance review.
    """
    if "dry_run_context" not in governance_dict:
        governance_dict["dry_run_context"] = None
    
    if simulation_engine and affected_object_id:
        try:
            summary = simulation_engine.get_dry_run(f"dry_run_{affected_object_id}")
            if summary:
                governance_dict["dry_run_context"] = {
                    "aggregate_risk_delta": summary.aggregate_risk_delta,
                    "aggregate_trust_delta": summary.aggregate_trust_delta,
                    "aggregate_escalation_probability": summary.aggregate_escalation_probability,
                    "top_concerns": summary.top_concerns,
                    "recommendation": summary.recommendation,
                }
        except Exception:
            pass  # Silent fallback to default
    
    return governance_dict


def integrate_with_proof_gate(
    proof_dict: Dict[str, Any],
    simulation_engine: SimulationEngine = None,
    simulation_id: str = None,
) -> Dict[str, Any]:
    """Add dry-run context to proof gate.
    
    This is purely additive — no migration required.
    
    v44: Simulation provides dry-run evidence for proof gate.
    """
    if "dry_run_context" not in proof_dict:
        proof_dict["dry_run_context"] = None
    
    if simulation_engine and simulation_id:
        try:
            simulation = simulation_engine.get_simulation(simulation_id)
            if simulation:
                proof_dict["dry_run_context"] = {
                    "simulation_exists": True,
                    "risk_delta": simulation.risk_delta,
                    "escalation_probability": simulation.escalation_probability,
                    "rollback_feasibility": simulation.rollback_feasibility,
                }
        except Exception:
            pass  # Silent fallback to default
    
    return proof_dict


def integrate_with_multi_timescale_planning(
    planning_dict: Dict[str, Any],
    simulation_engine: SimulationEngine = None,
    simulation_id: str = None,
) -> Dict[str, Any]:
    """Add dry-run context to multi-timescale planning.
    
    This is purely additive — no migration required.
    
    v44: Simulation provides impact projections for trajectory planning.
    """
    if "dry_run_context" not in planning_dict:
        planning_dict["dry_run_context"] = None
    
    if simulation_engine and simulation_id:
        try:
            simulation = simulation_engine.get_simulation(simulation_id)
            if simulation:
                planning_dict["dry_run_context"] = {
                    "simulation_exists": True,
                    "expected_impact": simulation.expected_impact,
                    "risk_delta": simulation.risk_delta,
                    "trust_delta": simulation.trust_delta,
                }
        except Exception:
            pass  # Silent fallback to default
    
    return planning_dict


def integrate_with_outcome_feedback(
    feedback_dict: Dict[str, Any],
    simulation_engine: SimulationEngine = None,
    affected_object_id: str = None,
) -> Dict[str, Any]:
    """Add dry-run context to outcome feedback.
    
    This is purely additive — no migration required.
    
    v44: Simulation provides dry-run predictions for feedback comparison.
    """
    if "dry_run_context" not in feedback_dict:
        feedback_dict["dry_run_context"] = None
    
    if simulation_engine and affected_object_id:
        try:
            summary = simulation_engine.get_dry_run(f"dry_run_{affected_object_id}")
            if summary:
                feedback_dict["dry_run_context"] = {
                    "aggregate_risk_delta": summary.aggregate_risk_delta,
                    "aggregate_trust_delta": summary.aggregate_trust_delta,
                    "aggregate_escalation_probability": summary.aggregate_escalation_probability,
                }
        except Exception:
            pass  # Silent fallback to default
    
    return feedback_dict
