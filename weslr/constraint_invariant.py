# constraint_invariant.py - WESLR v45: Constraint / Invariant Layer
# Creates a governed invariant layer so WESLR can recognize hard constraints and protected
# baselines that must not be violated even when goals, simulations, or short-term benefits suggest otherwise.
# Additive only, transparent, reversible, role-aware, non-manipulative.
# No repo drift (local to WESLR scope).

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================================
# ENUMS
# ============================================================================


class ConstraintType(str, Enum):
    """Types of hard constraints."""
    # Hard constraints - absolute prohibitions
    ETHICAL = "ethical"  # Ethical boundaries (e.g., no deception, no harm)
    LEGAL = "legal"  # Legal requirements (e.g., GDPR, copyright)
    SECURITY = "security"  # Security boundaries (e.g., no exfiltration)
    PRIVACY = "privacy"  # Privacy boundaries (e.g., no unauthorized data access)
    
    # Protected baselines - must not be violated
    TRUST = "trust"  # Trust baseline must not be eroded
    OPERATIONAL = "operational"  # Operational continuity must be preserved
    REPUTATION = "reputation"  # Reputation baseline must not be damaged
    
    # Domain-specific constraints
    DOMAIN = "domain"  # Domain-specific rules (e.g., medical, financial)
    
    OTHER = "other"


class InvariantType(str, Enum):
    """Types of invariant relationships."""
    # Hard invariants - must always hold
    LOGICAL = "logical"  # Logical consistency (e.g., A implies B)
    CAUSAL = "causal"  # Causal relationships (e.g., X causes Y)
    TEMPORAL = "temporal"  # Temporal ordering (e.g., A before B)
    QUANTITATIVE = "quantitative"  # Numeric bounds (e.g., value in range)
    
    # Role-based invariants
    ROLE = "role"  # Role-specific obligations
    
    OTHER = "other"


class ViolationSeverity(str, Enum):
    """Severity of constraint/invariant violation."""
    LOW = "low"  # Minor deviation, easily correctable
    MEDIUM = "medium"  # Noticeable violation, requires intervention
    HIGH = "high"  # Significant violation, blocks action
    CRITICAL = "critical"  # Severe violation, immediate block and audit


class InvariantHoldBackCondition(str, Enum):
    """Conditions under which an invariant hold-back applies."""
    ALWAYS = "always"  # Always hold back until condition satisfied
    CONDITIONAL = "conditional"  # Hold back only if specific conditions met
    GRADUAL = "gradual"  # Gradual hold-back based on violation severity
    EMERGENCY_OVERRIDE = "emergency_override"  # Hold-back with emergency override path


class ExplanationType(str, Enum):
    """Types of explanations for invariant blocks."""
    DESCRIPTION = "description"  # What was blocked and why
    ALTERNATIVES = "alternatives"  # Alternative paths that satisfy invariant
    MITIGATIONS = "mitigations"  # How to mitigate the violation
    EMERGENCY = "emergency"  # Emergency override instructions


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class HardConstraint:
    """Hard constraint that must not be violated."""
    
    constraint_id: str
    constraint_type: str  # ConstraintType.value
    description: str
    
    # Scope
    applies_to: List[str] = field(default_factory=list)  # Affected object types
    scope: List[str] = field(default_factory=list)  # Applicable domains
    
    # Violation properties
    violation_severity: str = ViolationSeverity.HIGH.value
    automatic_block: bool = True  # Block automatically or require review
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "constraint_id": self.constraint_id,
            "constraint_type": self.constraint_type,
            "description": self.description,
            "applies_to": self.applies_to,
            "scope": self.scope,
            "violation_severity": self.violation_severity,
            "automatic_block": self.automatic_block,
            "created_at": self.created_at,
            "author": self.author,
            "enabled": self.enabled,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HardConstraint:
        data["applies_to"] = data.get("applies_to", [])
        data["scope"] = data.get("scope", [])
        return cls(**data)


@dataclass
class ProtectedBaseline:
    """Protected baseline that must not be violated."""
    
    baseline_id: str
    baseline_type: str  # InvariantType.value or custom
    description: str
    
    # Thresholds
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None
    target_value: Optional[float] = None
    
    # Violation properties
    violation_severity: str = ViolationSeverity.HIGH.value
    automatic_block: bool = True
    
    # Reversion
    reversion_threshold: float = 0.5  # How much violation allows automatic reversion
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_id": self.baseline_id,
            "baseline_type": self.baseline_type,
            "description": self.description,
            "min_threshold": self.min_threshold,
            "max_threshold": self.max_threshold,
            "target_value": self.target_value,
            "violation_severity": self.violation_severity,
            "automatic_block": self.automatic_block,
            "reversion_threshold": self.reversion_threshold,
            "created_at": self.created_at,
            "author": self.author,
            "enabled": self.enabled,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProtectedBaseline:
        return cls(**data)


@dataclass
class TrustInvariant:
    """Trust-related invariant that must not be violated."""
    
    invariant_id: str
    invariant_type: str  # InvariantType.value
    description: str
    
    # Trust dimensions
    trust_type: str = "relationship"  # relationship, system, operational
    criticality: str = "high"  # low, medium, high, critical
    
    # Violation response
    violation_severity: str = ViolationSeverity.HIGH.value
    automatic_block: bool = True
    hold_back_condition: str = InvariantHoldBackCondition.ALWAYS.value
    
    # Reversion
    reversion_threshold: float = 0.3
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "invariant_id": self.invariant_id,
            "invariant_type": self.invariant_type,
            "description": self.description,
            "trust_type": self.trust_type,
            "criticality": self.criticality,
            "violation_severity": self.violation_severity,
            "automatic_block": self.automatic_block,
            "hold_back_condition": self.hold_back_condition,
            "reversion_threshold": self.reversion_threshold,
            "created_at": self.created_at,
            "author": self.author,
            "enabled": self.enabled,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TrustInvariant:
        return cls(**data)


@dataclass
class InvariantViolation:
    """Record of an invariant violation."""
    
    violation_id: str
    violated_constraint_id: str
    violated_constraint_type: str  # HardConstraint or ProtectedBaseline
    
    # Violation details
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    context: str = ""
    evidence: List[str] = field(default_factory=list)
    
    # Severity and response
    detected_severity: str = ViolationSeverity.LOW.value
    automatic_blocked: bool = False
    
    # Resolution
    resolved: bool = False
    resolved_at: Optional[str] = None
    resolution_notes: Optional[str] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "violation_id": self.violation_id,
            "violated_constraint_id": self.violated_constraint_id,
            "violated_constraint_type": self.violated_constraint_type,
            "timestamp": self.timestamp,
            "context": self.context,
            "evidence": self.evidence,
            "detected_severity": self.detected_severity,
            "automatic_blocked": self.automatic_blocked,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at,
            "resolution_notes": self.resolution_notes,
            "created_at": self.created_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InvariantViolation:
        data["evidence"] = data.get("evidence", [])
        return cls(**data)


@dataclass
class ExplanationForBlock:
    """Explanation for an invariant block."""
    
    explanation_id: str
    blocked_action: str
    violated_invariant_id: str
    
    # Explanation type
    explanation_type: str  # ExplanationType.value
    explanation_text: str
    
    # Alternatives and mitigations
    alternatives: List[str] = field(default_factory=list)
    mitigations: List[str] = field(default_factory=list)
    emergency_override_instructions: Optional[str] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "explanation_id": self.explanation_id,
            "blocked_action": self.blocked_action,
            "violated_invariant_id": self.violated_invariant_id,
            "explanation_type": self.explanation_type,
            "explanation_text": self.explanation_text,
            "alternatives": self.alternatives,
            "mitigations": self.mitigations,
            "emergency_override_instructions": self.emergency_override_instructions,
            "created_at": self.created_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExplanationForBlock:
        data["alternatives"] = data.get("alternatives", [])
        data["mitigations"] = data.get("mitigations", [])
        return cls(**data)


# ============================================================================
# CONSTRAINT/INVARIANT ENGINE
# ============================================================================


class ConstraintInvariantEngine:
    """Engine for managing constraints, baselines, and invariants."""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or "/tmp/weslr_constraints"
        
        # Storage
        self.constraints: Dict[str, HardConstraint] = {}
        self.baselines: Dict[str, ProtectedBaseline] = {}
        self.invariants: Dict[str, TrustInvariant] = {}
        self.violations: Dict[str, InvariantViolation] = {}
        self.explanations: Dict[str, ExplanationForBlock] = {}
        
        # Load existing if present
        if storage_path and Path(self.storage_path).exists():
            self._load_from_storage()
    
    def _load_from_storage(self) -> None:
        """Load from storage directory."""
        import os
        from pathlib import Path
        
        storage = Path(self.storage_path)
        if not storage.exists():
            storage.mkdir(parents=True, exist_ok=True)
            return
        
        # Load constraints
        for file in storage.glob("*_constraint.json"):
            try:
                with open(file) as f:
                    data = json.load(f)
                    constraint = HardConstraint.from_dict(data)
                    self.constraints[constraint.constraint_id] = constraint
            except Exception:
                pass
        
        # Load baselines
        for file in storage.glob("*_baseline.json"):
            try:
                with open(file) as f:
                    data = json.load(f)
                    baseline = ProtectedBaseline.from_dict(data)
                    self.baselines[baseline.baseline_id] = baseline
            except Exception:
                pass
        
        # Load invariants
        for file in storage.glob("*_invariant.json"):
            try:
                with open(file) as f:
                    data = json.load(f)
                    invariant = TrustInvariant.from_dict(data)
                    self.invariants[invariant.invariant_id] = invariant
            except Exception:
                pass
    
    def _save_to_storage(self, obj: Any, prefix: str) -> None:
        """Save object to storage."""
        import os
        
        if not self.storage_path:
            return
        
        obj_id = obj.constraint_id if hasattr(obj, 'constraint_id') else obj.baseline_id if hasattr(obj, 'baseline_id') else obj.invariant_id
        # Create storage directory if needed
        storage_path = Path(self.storage_path)
        storage_path.mkdir(parents=True, exist_ok=True)
        filepath = os.path.join(self.storage_path, f"{obj_id}_{prefix}.json")
        with open(filepath, "w") as f:
            json.dump(obj.to_dict(), f, indent=2)
    
    # ============================================================================
    # CONSTRAINT MANAGEMENT
    # ============================================================================
    
    def add_constraint(self, constraint: HardConstraint) -> None:
        """Add a new hard constraint."""
        self.constraints[constraint.constraint_id] = constraint
        self._save_to_storage(constraint, "constraint")
    
    def remove_constraint(self, constraint_id: str) -> bool:
        """Remove a constraint."""
        if constraint_id in self.constraints:
            del self.constraints[constraint_id]
            return True
        return False
    
    def get_constraint(self, constraint_id: str) -> Optional[HardConstraint]:
        """Get a constraint by ID."""
        return self.constraints.get(constraint_id)
    
    def get_all_constraints(self) -> List[HardConstraint]:
        """Get all enabled constraints."""
        return [c for c in self.constraints.values() if c.enabled]
    
    # ============================================================================
    # BASELINE MANAGEMENT
    # ============================================================================
    
    def add_baseline(self, baseline: ProtectedBaseline) -> None:
        """Add a new protected baseline."""
        self.baselines[baseline.baseline_id] = baseline
        self._save_to_storage(baseline, "baseline")
    
    def remove_baseline(self, baseline_id: str) -> bool:
        """Remove a baseline."""
        if baseline_id in self.baselines:
            del self.baselines[baseline_id]
            return True
        return False
    
    def get_baseline(self, baseline_id: str) -> Optional[ProtectedBaseline]:
        """Get a baseline by ID."""
        return self.baselines.get(baseline_id)
    
    def get_all_baselines(self) -> List[ProtectedBaseline]:
        """Get all enabled baselines."""
        return [b for b in self.baselines.values() if b.enabled]
    
    # ============================================================================
    # INVARIANT MANAGEMENT
    # ============================================================================
    
    def add_invariant(self, invariant: TrustInvariant) -> None:
        """Add a new invariant."""
        self.invariants[invariant.invariant_id] = invariant
        self._save_to_storage(invariant, "invariant")
    
    def remove_invariant(self, invariant_id: str) -> bool:
        """Remove an invariant."""
        if invariant_id in self.invariants:
            del self.invariants[invariant_id]
            return True
        return False
    
    def get_invariant(self, invariant_id: str) -> Optional[TrustInvariant]:
        """Get an invariant by ID."""
        return self.invariants.get(invariant_id)
    
    def get_all_invariants(self) -> List[TrustInvariant]:
        """Get all enabled invariants."""
        return [i for i in self.invariants.values() if i.enabled]
    
    # ============================================================================
    # VIOLATION HANDLING
    # ============================================================================
    
    def record_violation(self, violation: InvariantViolation) -> None:
        """Record a violation."""
        self.violations[violation.violation_id] = violation
    
    def get_violation(self, violation_id: str) -> Optional[InvariantViolation]:
        """Get a violation by ID."""
        return self.violations.get(violation_id)
    
    def resolve_violation(self, violation_id: str, resolution_notes: str) -> bool:
        """Resolve a violation."""
        if violation_id in self.violations:
            violation = self.violations[violation_id]
            violation.resolved = True
            violation.resolved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            violation.resolution_notes = resolution_notes
            return True
        return False
    
    # ============================================================================
    # BLOCK EXPLANATIONS
    # ============================================================================
    
    def create_block_explanation(self, explanation: ExplanationForBlock) -> None:
        """Create an explanation for a block."""
        self.explanations[explanation.explanation_id] = explanation
    
    def get_block_explanation(self, explanation_id: str) -> Optional[ExplanationForBlock]:
        """Get a block explanation by ID."""
        return self.explanations.get(explanation_id)
    
    # ============================================================================
    # VIOLATION DETECTION AND BLOCKING
    # ============================================================================
    
    def check_violation(
        self,
        action: str,
        context: Dict[str, Any],
    ) -> Optional[InvariantViolation]:
        """Check if an action violates any constraints, baselines, or invariants."""
        import time
        
        # Check constraints
        for constraint in self.get_all_constraints():
            if constraint.enabled and self._check_constraint(action, context, constraint):
                violation = InvariantViolation(
                    violation_id=f"violation_{int(time.time() * 1000)}",
                    violated_constraint_id=constraint.constraint_id,
                    violated_constraint_type="HardConstraint",
                    timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    context=context.get("description", ""),
                    detected_severity=constraint.violation_severity,
                    automatic_blocked=constraint.automatic_block,
                )
                self.record_violation(violation)
                return violation
        
        # Check baselines
        for baseline in self.get_all_baselines():
            if baseline.enabled and self._check_baseline(context, baseline):
                violation = InvariantViolation(
                    violation_id=f"violation_{int(time.time() * 1000)}",
                    violated_constraint_id=baseline.baseline_id,
                    violated_constraint_type="ProtectedBaseline",
                    timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    context=context.get("description", ""),
                    detected_severity=baseline.violation_severity,
                    automatic_blocked=baseline.automatic_block,
                )
                self.record_violation(violation)
                return violation
        
        # Check invariants
        for invariant in self.get_all_invariants():
            if invariant.enabled and self._check_invariant(context, invariant):
                violation = InvariantViolation(
                    violation_id=f"violation_{int(time.time() * 1000)}",
                    violated_constraint_id=invariant.invariant_id,
                    violated_constraint_type="TrustInvariant",
                    timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    context=context.get("description", ""),
                    detected_severity=invariant.violation_severity,
                    automatic_blocked=invariant.automatic_block,
                )
                self.record_violation(violation)
                return violation
        
        return None
    
    def _check_constraint(self, action: str, context: Dict[str, Any], constraint: HardConstraint) -> bool:
        """Check if an action violates a constraint."""
        # Simplified check - in practice, this would have domain-specific logic
        action_lower = action.lower()
        context_lower = json.dumps(context).lower()
        
        # Basic heuristic: if constraint applies to this action type
        if any(app in action_lower or app in context_lower for app in constraint.applies_to):
            return True
        return False
    
    def _check_baseline(self, context: Dict[str, Any], baseline: ProtectedBaseline) -> bool:
        """Check if context violates a baseline threshold."""
        # Simplified check - in practice, this would analyze actual values
        if baseline.min_threshold is not None and "value" in context:
            if context["value"] < baseline.min_threshold:
                return True
        if baseline.max_threshold is not None and "value" in context:
            if context["value"] > baseline.max_threshold:
                return True
        return False
    
    def _check_invariant(self, context: Dict[str, Any], invariant: TrustInvariant) -> bool:
        """Check if context violates an invariant."""
        # Simplified check - in practice, this would analyze relationship metrics
        if "trust_level" in context and "min_trust" in context:
            if context["trust_level"] < context["min_trust"]:
                return True
        return False
    
    # ============================================================================
    # INTEGRATION HOOKS (Additive)
    # ============================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary."""
        return {
            "constraint_count": len(self.constraints),
            "baseline_count": len(self.baselines),
            "invariant_count": len(self.invariants),
            "violation_count": len(self.violations),
            "explanation_count": len(self.explanations),
            "constraints": {k: v.to_dict() for k, v in self.constraints.items()},
            "baselines": {k: v.to_dict() for k, v in self.baselines.items()},
            "invariants": {k: v.to_dict() for k, v in self.invariants.items()},
            "violations": {k: v.to_dict() for k, v in self.violations.items()},
            "explanations": {k: v.to_dict() for k, v in self.explanations.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_simulation(
    simulation_dict: Dict[str, Any],
    constraint_engine: ConstraintInvariantEngine = None,
    action: str = None,
) -> Dict[str, Any]:
    """Add invariant constraints to simulation context.
    
    This is purely additive — no migration required.
    
    v45: Constraint layer provides hard constraints for simulation validation.
    """
    if "constraint_context" not in simulation_dict:
        simulation_dict["constraint_context"] = None
    
    if constraint_engine and action:
        try:
            # Simulate checking constraints during dry-run
            # In practice, this would run full check_violation
            simulation_dict["constraint_context"] = {
                "constraints_active": True,
                "constraint_count": len(constraint_engine.get_all_constraints()),
                "baselines_active": len(constraint_engine.get_all_baselines()),
                "invariants_active": len(constraint_engine.get_all_invariants()),
            }
        except Exception:
            pass  # Silent fallback to default
    
    return simulation_dict


def integrate_with_proof_gate(
    proof_dict: Dict[str, Any],
    constraint_engine: ConstraintInvariantEngine = None,
    action: str = None,
    context: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Add invariant constraints to proof gate.
    
    This is purely additive — no migration required.
    
    v45: Constraint layer provides hard constraint checks for proof gate.
    """
    if "constraint_context" not in proof_dict:
        proof_dict["constraint_context"] = None
    
    if constraint_engine and action:
        try:
            # Check for violations
            violation = constraint_engine.check_violation(action, context or {})
            proof_dict["constraint_context"] = {
                "violation_detected": violation is not None,
                "violation_id": violation.violation_id if violation else None,
                "automatic_block": violation.automatic_block if violation else None,
            }
        except Exception:
            pass  # Silent fallback to default
    
    return proof_dict


def integrate_with_tension_resolution(
    tension_dict: Dict[str, Any],
    constraint_engine: ConstraintInvariantEngine = None,
    action: str = None,
) -> Dict[str, Any]:
    """Add invariant constraints to tension resolution.
    
    This is purely additive — no migration required.
    
    v45: Constraint layer provides hard constraints that override tension resolution.
    """
    if "constraint_context" not in tension_dict:
        tension_dict["constraint_context"] = None
    
    if constraint_engine and action:
        try:
            # Check for violations during tension resolution
            violation = constraint_engine.check_violation(action, {})
            tension_dict["constraint_context"] = {
                "constraints_override": violation is not None,
                "violation_id": violation.violation_id if violation else None,
            }
        except Exception:
            pass  # Silent fallback to default
    
    return tension_dict


def integrate_with_goal_hierarchy(
    goal_dict: Dict[str, Any],
    constraint_engine: ConstraintInvariantEngine = None,
    goal_id: str = None,
) -> Dict[str, Any]:
    """Add invariant constraints to goal hierarchy.
    
    This is purely additive — no migration required.
    
    v45: Constraint layer provides hard constraints that goals must satisfy.
    """
    if "constraint_context" not in goal_dict:
        goal_dict["constraint_context"] = None
    
    if constraint_engine and goal_id:
        try:
            # Check if goal violates any constraints
            goal_context = {"description": f"Goal: {goal_id}"}
            violation = constraint_engine.check_violation(f"execute_goal_{goal_id}", goal_context)
            goal_dict["constraint_context"] = {
                "goal_compliant": violation is None,
                "violation_detected": violation is not None,
                "violation_id": violation.violation_id if violation else None,
            }
        except Exception:
            pass  # Silent fallback to default
    
    return goal_dict


def integrate_with_capability_boundary(
    capability_dict: Dict[str, Any],
    constraint_engine: ConstraintInvariantEngine = None,
    capability_type: str = None,
) -> Dict[str, Any]:
    """Add invariant constraints to capability boundary.
    
    This is purely additive — no migration required.
    
    v45: Constraint layer provides hard constraints that capabilities must respect.
    """
    if "constraint_context" not in capability_dict:
        capability_dict["constraint_context"] = None
    
    if constraint_engine and capability_type:
        try:
            capability_dict["constraint_context"] = {
                "constraint_count": len(constraint_engine.get_all_constraints()),
                "enabled_constraints": [c.constraint_id for c in constraint_engine.get_all_constraints()],
            }
        except Exception:
            pass  # Silent fallback to default
    
    return capability_dict
