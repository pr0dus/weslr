# proposal_realization.py - Self-Architecture Core v14: Proposal Realization / Safe Execution Planning Layer
# Turn approved change proposals into structured, operator-safe realization plans without executing them.
# Additive only, operator-first, reversible, governed. No autonomous execution.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from change_proposals import ChangeProposal, ExecutionGate, ProposalState

from proof_gate import ProofGateEngine, ExecutionReadiness, ExecutionState


class RealizationPhase(str, Enum):
    """Implementation phases for a realization plan."""
    PREPARATION = "preparation"
    IMPLEMENTATION = "implementation"
    VALIDATION = "validation"
    MONITORING = "monitoring"
    COMPLETE = "complete"


class ReadinessState(str, Enum):
    """Readiness state for safe execution."""
    NOT_READY = "not_ready"
    READY_WITH_BLOCKERS = "ready_with_blockers"
    READY = "ready"
    BLOCKED = "blocked"


class BlockerType(str, Enum):
    """Types of blockers."""
    DEPENDENCY = "dependency"
    VALIDATION = "validation"
    RISK = "risk"
    CONFIGURATION = "configuration"
    RESOURCE = "resource"
    EXTERNAL = "external"


@dataclass
class Blocker:
    """A blocker condition for safe execution."""
    
    blocker_id: str
    blocker_type: str  # BlockerType.value
    description: str
    severity: str = "medium"  # low, medium, high
    resolution_steps: List[str] = field(default_factory=list)
    resolved: bool = False
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "blocker_id": self.blocker_id,
            "blocker_type": self.blocker_type,
            "description": self.description,
            "severity": self.severity,
            "resolution_steps": self.resolution_steps,
            "resolved": self.resolved,
            "detected_at": self.detected_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Blocker:
        data["resolution_steps"] = data.get("resolution_steps", [])
        return cls(**data)


@dataclass
class RollbackCheckpoint:
    """A checkpoint for rollback operations."""
    
    checkpoint_id: str
    description: str
    trigger: str  # "before", "after", "on_failure"
    file_patterns: List[str] = field(default_factory=list)
    state_reference: Optional[str] = None
    verified: bool = False
    verified_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "description": self.description,
            "trigger": self.trigger,
            "file_patterns": self.file_patterns,
            "state_reference": self.state_reference,
            "verified": self.verified,
            "verified_at": self.verified_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RollbackCheckpoint:
        data["file_patterns"] = data.get("file_patterns", [])
        return cls(**data)


@dataclass
class RealizationPlan:
    """A safe execution plan for an approved proposal.
    
    Packages:
    - Affected subsystems
    - Likely files/modules impacted
    - Implementation phases
    - Validation requirements
    - Rollback checkpoints
    - Execution readiness state
    - Blocker conditions
    - Operator approval points
    """
    
    plan_id: str
    proposal_id: str
    title: str
    description: str
    
    # Scope
    affected_subsystems: List[str] = field(default_factory=list)
    impacted_modules: List[str] = field(default_factory=list)
    impacted_files: List[str] = field(default_factory=list)
    
    # Phases
    phases: List[str] = field(default_factory=list)
    current_phase: str = RealizationPhase.PREPARATION.value
    
    # Validation
    validation_requirements: List[str] = field(default_factory=list)
    
    # Rollback
    rollback_expectations: List[str] = field(default_factory=list)
    rollback_checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    
    # Blockers
    blockers: List[Dict[str, Any]] = field(default_factory=list)
    blocker_count: int = 0
    blocker_count_by_severity: Dict[str, int] = field(default_factory=lambda: {"low": 0, "medium": 0, "high": 0, "critical": 0})
    
    # Readiness
    readiness_state: str = ReadinessState.NOT_READY.value
    readiness_reason: Optional[str] = None
    
    # Approval points
    approval_points: List[Dict[str, Any]] = field(default_factory=list)
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    approved_blocker_ids: List[str] = field(default_factory=list)
    
    # Execution eligibility (v15)
    execution_eligibility: Optional[Dict[str, Any]] = None
    proof_status: Optional[Dict[str, Any]] = None
    blocking_reasons: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    prepared_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "proposal_id": self.proposal_id,
            "title": self.title,
            "description": self.description,
            "affected_subsystems": self.affected_subsystems,
            "impacted_modules": self.impacted_modules,
            "impacted_files": self.impacted_files,
            "phases": self.phases,
            "current_phase": self.current_phase,
            "validation_requirements": self.validation_requirements,
            "rollback_expectations": self.rollback_expectations,
            "rollback_checkpoints": self.rollback_checkpoints,
            "blockers": self.blockers,
            "blocker_count": self.blocker_count,
            "blocker_count_by_severity": self.blocker_count_by_severity,
            "readiness_state": self.readiness_state,
            "readiness_reason": self.readiness_reason,
            "execution_eligibility": self.execution_eligibility,
            "proof_status": self.proof_status,
            "blocking_reasons": self.blocking_reasons,
            "approval_points": self.approval_points,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "approved_blocker_ids": self.approved_blocker_ids,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "prepared_by": self.prepared_by,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RealizationPlan:
        data["affected_subsystems"] = data.get("affected_subsystems", [])
        data["impacted_modules"] = data.get("impacted_modules", [])
        data["impacted_files"] = data.get("impacted_files", [])
        data["phases"] = data.get("phases", [])
        data["validation_requirements"] = data.get("validation_requirements", [])
        data["rollback_expectations"] = data.get("rollback_expectations", [])
        data["rollback_checkpoints"] = data.get("rollback_checkpoints", [])
        data["blockers"] = data.get("blockers", [])
        data["blocker_count_by_severity"] = data.get("blocker_count_by_severity", {"low": 0, "medium": 0, "high": 0, "critical": 0})
        data["execution_eligibility"] = data.get("execution_eligibility")
        data["proof_status"] = data.get("proof_status")
        data["blocking_reasons"] = data.get("blocking_reasons", [])
        data["approval_points"] = data.get("approval_points", [])
        data["approved_blocker_ids"] = data.get("approved_blocker_ids", [])
        return cls(**data)

    def update_readiness(self) -> None:
        """Update readiness state based on blockers and checkpoints."""
        # Count blockers by severity
        self.blocker_count_by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        unblocked_count = 0
        unblockable_count = 0
        
        for blocker in self.blockers:
            severity = blocker.get("severity", "medium")
            self.blocker_count_by_severity[severity] = self.blocker_count_by_severity.get(severity, 0) + 1
            
            if blocker.get("resolved", False):
                unblocked_count += 1
            elif blocker.get("blocker_type") in [BlockerType.RESOURCE.value, BlockerType.EXTERNAL.value]:
                unblockable_count += 1
        
        # Determine readiness state
        if self.blocker_count == 0:
            self.readiness_state = ReadinessState.READY.value
            self.readiness_reason = "No blockers"
        elif unblocked_count == self.blocker_count:
            self.readiness_state = ReadinessState.READY.value
            self.readiness_reason = "All blockers resolved"
        elif unblockable_count > 0:
            self.readiness_state = ReadinessState.BLOCKED.value
            self.readiness_reason = f"{unblockable_count} unblockable blocker(s) required"
        elif self.blocker_count > 0:
            self.readiness_state = ReadinessState.READY_WITH_BLOCKERS.value
            self.readiness_reason = f"{self.blocker_count} blocker(s) require operator approval"
        else:
            self.readiness_state = ReadinessState.NOT_READY.value
            self.readiness_reason = "Ready for blocker assessment"
        
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def add_blocker(self, blocker_type: str, description: str, severity: str = "medium") -> Blocker:
        """Add a blocker to the plan."""
        blocker = Blocker(
            blocker_id=f"block-{len(self.blockers) + 1:03d}",
            blocker_type=blocker_type,
            description=description,
            severity=severity,
        )
        self.blockers.append(blocker.to_dict())
        self.blocker_count += 1
        self.update_readiness()
        return blocker

    def resolve_blocker(self, blocker_id: str, resolved_by: str = "operator") -> bool:
        """Mark a blocker as resolved."""
        for blocker in self.blockers:
            if blocker["blocker_id"] == blocker_id:
                blocker["resolved"] = True
                self.update_readiness()
                self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                return True
        return False

    def add_checkpoint(self, description: str, trigger: str = "before", file_patterns: List[str] = None) -> RollbackCheckpoint:
        """Add a rollback checkpoint."""
        checkpoint = RollbackCheckpoint(
            checkpoint_id=f"chk-{len(self.rollback_checkpoints) + 1:03d}",
            description=description,
            trigger=trigger,
            file_patterns=file_patterns or [],
        )
        self.rollback_checkpoints.append(checkpoint.to_dict())
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return checkpoint

    def verify_checkpoint(self, checkpoint_id: str) -> bool:
        """Verify a rollback checkpoint."""
        for checkpoint in self.rollback_checkpoints:
            if checkpoint["checkpoint_id"] == checkpoint_id:
                checkpoint["verified"] = True
                checkpoint["verified_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                return True
        return False

    def add_phase(self, phase: str, description: str = "") -> None:
        """Add an implementation phase."""
        if phase not in self.phases:
            self.phases.append(phase)
            if not description:
                description = f"Implementation phase: {phase}"
            self.approval_points.append({
                "phase": phase,
                "description": description,
                "approved": False,
                "approved_by": None,
                "approved_at": None,
            })
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def approve_phase(self, phase: str, approved_by: str = "operator") -> bool:
        """Approve an implementation phase."""
        for point in self.approval_points:
            if point["phase"] == phase:
                point["approved"] = True
                point["approved_by"] = approved_by
                point["approved_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                return True
        return False

    def get_readiness_status(self) -> Dict[str, Any]:
        """Get readiness status for operator review."""
        return {
            "readiness_state": self.readiness_state,
            "readiness_reason": self.readiness_reason,
            "blocker_count": self.blocker_count,
            "blocker_count_by_severity": self.blocker_count_by_severity,
            "unresolved_blockers": [b for b in self.blockers if not b.get("resolved", False)],
            "rollback_checkpoints": len(self.rollback_checkpoints),
            "verified_checkpoints": sum(1 for c in self.rollback_checkpoints if c.get("verified", False)),
            "phases": len(self.phases),
            "completed_phases": sum(1 for p in self.approval_points if p.get("approved", False)),
            "can_proceed": self.readiness_state in [ReadinessState.READY.value, ReadinessState.READY_WITH_BLOCKERS.value],
        }

    def get_implementation_plan(self) -> Dict[str, Any]:
        """Get implementation plan for operator review."""
        return {
            "plan_id": self.plan_id,
            "proposal_id": self.proposal_id,
            "title": self.title,
            "description": self.description,
            "affected_subsystems": self.affected_subsystems,
            "impacted_modules": self.impacted_modules,
            "impacted_files": self.impacted_files,
            "phases": self.phases,
            "current_phase": self.current_phase,
            "readiness": self.get_readiness_status(),
            "rollback": {
                "expectations": self.rollback_expectations,
                "checkpoints": self.rollback_checkpoints,
            },
            "approval_points": self.approval_points,
        }


class RealizationEngine:
    """Builds realization plans from approved change proposals.
    
    Ensures safe execution planning with:
    - Impact identification
    - Validation/rollback requirements
    - Readiness classification
    - Operator approval points
    """
    
    def __init__(self, execution_gate: ExecutionGate = None):
        self.gate = execution_gate or ExecutionGate()
    
    def build_realization_plan(
        self,
        proposal_id: str,
        prepared_by: str = "operator",
    ) -> Optional[RealizationPlan]:
        """Build a realization plan from an approved proposal.
        
        Returns None if proposal not found or not approved.
        """
        proposal = self.gate.get_proposal(proposal_id)
        if not proposal:
            return None
        
        # Check if proposal is approved
        if proposal.state != ProposalState.APPROVED.value:
            return None
        
        # Identify impacted modules/files based on affected subsystems
        impacted_modules = self._map_subsystems_to_modules(proposal.affected_subsystems)
        impacted_files = self._map_subsystems_to_files(proposal.affected_subsystems)
        
        # Build phases
        phases = [
            "preparation",
            "implementation",
            "validation",
            "monitoring",
        ]
        
        # Create validation requirements
        validation_requirements = proposal.validation_requirements.copy()
        
        # Create rollback expectations
        rollback_expectations = proposal.rollback_expectations.copy()
        
        # Identify blockers based on risk and subsystem impact
        blockers = self._identify_blockers(proposal)
        
        # Build plan
        plan = RealizationPlan(
            plan_id=f"plan-{proposal.proposal_id.split('-')[-1]}",
            proposal_id=proposal.proposal_id,
            title=proposal.title,
            description=proposal.description,
            affected_subsystems=proposal.affected_subsystems,
            impacted_modules=impacted_modules,
            impacted_files=impacted_files,
            phases=phases,
            current_phase=RealizationPhase.PREPARATION.value,
            validation_requirements=validation_requirements,
            rollback_expectations=rollback_expectations,
            rollback_checkpoints=self._build_rollback_checkpoints(proposal),
            blockers=blockers,
            blocker_count=len(blockers),
            prepared_by=prepared_by,
        )
        
        # Update readiness
        plan.update_readiness()
        
        # v15: Add execution eligibility via proof gate
        proof_gate = ProofGateEngine(execution_gate=self.gate)
        eligibility = proof_gate.get_execution_eligibility(
            plan_id=plan.plan_id,
            proposal_id=proposal.proposal_id,
        )
        plan.execution_eligibility = eligibility
        plan.proof_status = eligibility.get("proof_status", {})
        plan.blocking_reasons = eligibility.get("blocking_reasons", [])
        
        return plan
    
    def _map_subsystems_to_modules(self, subsystems: List[str]) -> List[str]:
        """Map subsystems to likely impacted modules."""
        mapping = {
            "state": ["state.py", "state_management.py"],
            "continuity": ["continuity.py", "state_continuity.py"],
            "capability_discovery": ["capability_discovery.py", "capability_ingestion.py"],
            "file_ingestion": ["file_ingestion.py", "file_router.py"],
            "forecast": ["forecast.py", "forecast_to_outcome.py"],
            "calibration": ["calibration.py", "forecast.py"],
            "test": ["test_*.py"],
        }
        
        modules = []
        for sub in subsystems:
            if sub in mapping:
                modules.extend(mapping[sub])
            else:
                # Generic mapping for unknown subsystems
                modules.append(f"{sub}.py")
        
        return list(set(modules))  # Remove duplicates
    
    def _map_subsystems_to_files(self, subsystems: List[str]) -> List[str]:
        """Map subsystems to likely impacted files."""
        # In practice, this would analyze git history or dependency graph
        # For now, use module mapping as a heuristic
        return self._map_subsystems_to_modules(subsystems)
    
    def _build_rollback_checkpoints(self, proposal: ChangeProposal) -> List[Dict[str, Any]]:
        """Build rollback checkpoints for a proposal."""
        checkpoints = []
        
        for subsystem in proposal.affected_subsystems:
            checkpoints.append({
                "checkpoint_id": f"chk-{subsystem[:8]}-before",
                "description": f"Pre-change checkpoint for {subsystem}",
                "trigger": "before",
                "file_patterns": [f"{subsystem}.py", f"test_{subsystem}.py"],
                "verified": False,
            })
        
        for outcome in proposal.expected_outcomes:
            checkpoints.append({
                "checkpoint_id": f"chk-{outcome[:8]}-after",
                "description": f"Post-change checkpoint for {outcome}",
                "trigger": "after",
                "file_patterns": [f"{subsystem}.py" for subsystem in proposal.affected_subsystems],
                "verified": False,
            })
        
        return checkpoints
    
    def _identify_blockers(self, proposal: ChangeProposal) -> List[Dict[str, Any]]:
        """Identify blockers for a proposal."""
        blockers = []
        
        # Check risk level
        if proposal.risk_level == "high":
            blockers.append({
                "blocker_id": "block-risk-high",
                "blocker_type": BlockerType.RISK.value,
                "description": f"High risk level ({proposal.risk_level}) requires operator approval",
                "severity": "high",
                "resolution_steps": ["Review risk assessment", "Obtain senior approval", "Document risk acceptance"],
                "resolved": False,
            })
        
        # Check subsystem count
        if len(proposal.affected_subsystems) > 3:
            blockers.append({
                "blocker_id": "block-subsystem-many",
                "blocker_type": BlockerType.RESOURCE.value,
                "description": f"Affects {len(proposal.affected_subsystems)} subsystems - complex change",
                "severity": "medium",
                "resolution_steps": ["Break into smaller changes", "Add more test coverage", "Schedule maintenance window"],
                "resolved": False,
            })
        
        # Check effort estimate
        if proposal.estimated_effort > 80:
            blockers.append({
                "blocker_id": "block-effort-high",
                "blocker_type": BlockerType.RESOURCE.value,
                "description": f"High implementation effort ({proposal.estimated_effort}/100)",
                "severity": "medium",
                "resolution_steps": ["Add more resources", "Schedule dedicated time", "Add contingency buffer"],
                "resolved": False,
            })
        
        # Check calibration confidence
        if proposal.calibration_confidence < 0.5:
            blockers.append({
                "blocker_id": "block-confidence-low",
                "blocker_type": BlockerType.VALIDATION.value,
                "description": f"Low calibration confidence ({proposal.calibration_confidence:.2f})",
                "severity": "medium",
                "resolution_steps": ["Gather more data", "Run additional tests", "Review assumptions"],
                "resolved": False,
            })
        
        # Check forecast summary
        if not proposal.forecast_summary:
            blockers.append({
                "blocker_id": "block-no-forecast",
                "blocker_type": BlockerType.CONFIGURATION.value,
                "description": "Missing forecast summary",
                "severity": "low",
                "resolution_steps": ["Add forecast summary", "Document expected outcomes"],
                "resolved": False,
            })
        
        return blockers
    
    def get_realization_plan(
        self,
        plan_id: str,
    ) -> Optional[RealizationPlan]:
        """Get a realization plan by ID.
        
        Note: In a real implementation, this would load from storage.
        For now, we return None since plans are not persisted.
        """
        # Plans are not persisted in this implementation
        # They are built on-demand from proposals
        return None
    
    def approve_plan(
        self,
        plan_id: str,
        approved_by: str = "operator",
        approved_blocker_ids: List[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Approve a realization plan.
        
        Returns approval result with plan status.
        """
        # Since plans are not persisted, this is a placeholder
        # In a real implementation, this would:
        # 1. Load the plan from storage
        # 2. Update approval fields
        # 3. Save the plan
        
        return {
            "success": True,
            "plan_id": plan_id,
            "approved_by": approved_by,
            "approved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "approved_blocker_ids": approved_blocker_ids or [],
        }
    
    def generate_realization_summary(
        self,
        plan: RealizationPlan,
    ) -> Dict[str, Any]:
        """Generate operator-facing summary for a realization plan."""
        return {
            "plan_id": plan.plan_id,
            "proposal_id": plan.proposal_id,
            "title": plan.title,
            "description": plan.description,
            "readiness": plan.get_readiness_status(),
            "impact": {
                "subsystems": plan.affected_subsystems,
                "modules": plan.impacted_modules,
                "files": plan.impacted_files,
            },
            "phases": plan.phases,
            "current_phase": plan.current_phase,
            "rollback": {
                "expectations": plan.rollback_expectations,
                "checkpoints": len(plan.rollback_checkpoints),
            },
            "approval_points": plan.approval_points,
            "can_proceed": plan.readiness_state in [ReadinessState.READY.value, ReadinessState.READY_WITH_BLOCKERS.value],
            "requires_approval": plan.readiness_state == ReadinessState.READY_WITH_BLOCKERS.value,
        }


def build_realization_plan(
    proposal_id: str,
    prepared_by: str = "operator",
) -> Optional[RealizationPlan]:
    """Convenience function to build a realization plan."""
    engine = RealizationEngine()
    return engine.build_realization_plan(proposal_id, prepared_by)


def approve_realization_plan(
    plan_id: str,
    approved_by: str = "operator",
    approved_blocker_ids: List[str] = None,
) -> Optional[Dict[str, Any]]:
    """Convenience function to approve a realization plan."""
    engine = RealizationEngine()
    return engine.approve_plan(plan_id, approved_by, approved_blocker_ids)


def get_realization_summary(
    plan: RealizationPlan,
) -> Dict[str, Any]:
    """Convenience function to get realization summary."""
    engine = RealizationEngine()
    return engine.generate_realization_summary(plan)


if __name__ == "__main__":
    # CLI interface
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python proposal_realization.py <command> [args]")
        print("Commands:")
        print("  build <proposal_id>")
        print("  summary <plan_id>")
        print("  approve <plan_id>")
        sys.exit(1)
    
    command = sys.argv[1]
    engine = RealizationEngine()
    
    if command == "build":
        if len(sys.argv) < 3:
            print("Usage: python proposal_realization.py build <proposal_id>")
            sys.exit(1)
        proposal_id = sys.argv[2]
        plan = engine.build_realization_plan(proposal_id)
        if plan:
            print(json.dumps(plan.to_dict(), indent=2))
        else:
            print(f"Could not build plan for proposal: {proposal_id}")
    
    elif command == "summary":
        if len(sys.argv) < 3:
            print("Usage: python proposal_realization.py summary <plan_id>")
            sys.exit(1)
        plan_id = sys.argv[2]
        # In a real implementation, this would load the plan from storage
        print(f"Plan summary for: {plan_id}")
        print("Note: Plans are built on-demand, not persisted.")
    
    elif command == "approve":
        if len(sys.argv) < 3:
            print("Usage: python proposal_realization.py approve <plan_id>")
            sys.exit(1)
        plan_id = sys.argv[2]
        result = engine.approve_plan(plan_id)
        if result:
            print(f"Approved: {plan_id}")
            print(json.dumps(result, indent=2))
        else:
            print(f"Could not approve plan: {plan_id}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
