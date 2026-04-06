# proof_gate.py - Self-Architecture Core v15: Execution Readiness / Proof Gate
# Strict governance layer determining whether a realization plan is execution-eligible.
# Additive only, operator-first, reversible, governed. No autonomous execution.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from change_proposals import ChangeProposal, ExecutionGate
from proposal_realization import (
    RealizationEngine,
    RealizationPlan,
    Blocker,
    BlockerType,
    ReadinessState,
    RealizationPhase,
)


class ProofType(str, Enum):
    """Types of proof required for execution."""
    VALIDATION = "validation"
    RISK_ASSESSMENT = "risk_assessment"
    ROLLBACK_COVERAGE = "rollback_coverage"
    IMPACT_ANALYSIS = "impact_analysis"
    FORECAST_CONFIDENCE = "forecast_confidence"
    OPERATOR_REVIEW = "operator_review"
    AUDIT_TRAIL = "audit_trail"


class ProofStatus(str, Enum):
    """Status of a proof item."""
    NOT_REQUESTED = "not_requested"
    REQUESTED = "requested"
    SATISFIED = "satisfied"
    FAILED = "failed"


class ExecutionState(str, Enum):
    """Execution eligibility state."""
    NOT_ELIGIBLE = "not_eligible"
    ELIGIBLE = "eligible"
    BLOCKED = "blocked"
    PENDING_PROOF = "pending_proof"


@dataclass
class ProofItem:
    """A single proof item for execution readiness."""
    
    proof_id: str
    proof_type: str  # ProofType.value
    description: str
    status: str = ProofStatus.NOT_REQUESTED.value
    satisfied_at: Optional[str] = None
    failed_at: Optional[str] = None
    verified_by: Optional[str] = None
    evidence: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proof_id": self.proof_id,
            "proof_type": self.proof_type,
            "description": self.description,
            "status": self.status,
            "satisfied_at": self.satisfied_at,
            "failed_at": self.failed_at,
            "verified_by": self.verified_by,
            "evidence": self.evidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProofItem:
        return cls(**data)

    def mark_satisfied(self, verified_by: str = "operator", evidence: str = "") -> None:
        """Mark proof as satisfied."""
        self.status = ProofStatus.SATISFIED.value
        self.satisfied_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.verified_by = verified_by
        self.evidence = evidence

    def mark_failed(self, failed_by: str = "operator") -> None:
        """Mark proof as failed."""
        self.status = ProofStatus.FAILED.value
        self.failed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.verified_by = failed_by


@dataclass
class ExecutionReadiness:
    """Execution readiness and proof status for a realization plan.
    
    Packages:
    - Required proofs
    - Satisfied proofs
    - Missing proofs
    - Validation coverage
    - Rollback coverage
    - Bounded/unbounded risk
    - Readiness state
    - Blocking reasons
    """
    
    plan_id: str
    proposal_id: str
    
    # Proof tracking
    proofs: List[Dict[str, Any]] = field(default_factory=list)
    required_proofs: List[str] = field(default_factory=list)
    satisfied_proofs: List[str] = field(default_factory=list)
    missing_proofs: List[str] = field(default_factory=list)
    failed_proofs: List[str] = field(default_factory=list)
    
    # Coverage
    validation_coverage: float = 0.0  # 0.0-1.0
    rollback_coverage: float = 0.0  # 0.0-1.0
    rollback_checkpoints_total: int = 0
    rollback_checkpoints_verified: int = 0
    
    # Risk
    risk_bounded: bool = False
    risk_reason: Optional[str] = None
    max_risk_severity: str = "unknown"  # low, medium, high, critical
    
    # State
    readiness_state: str = ExecutionState.NOT_ELIGIBLE.value
    readiness_reason: Optional[str] = None
    blocking_reasons: List[str] = field(default_factory=list)
    
    # Metadata
    assessed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    assessed_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "proposal_id": self.proposal_id,
            "proofs": self.proofs,
            "required_proofs": self.required_proofs,
            "satisfied_proofs": self.satisfied_proofs,
            "missing_proofs": self.missing_proofs,
            "failed_proofs": self.failed_proofs,
            "validation_coverage": self.validation_coverage,
            "rollback_coverage": self.rollback_coverage,
            "rollback_checkpoints_total": self.rollback_checkpoints_total,
            "rollback_checkpoints_verified": self.rollback_checkpoints_verified,
            "risk_bounded": self.risk_bounded,
            "risk_reason": self.risk_reason,
            "max_risk_severity": self.max_risk_severity,
            "readiness_state": self.readiness_state,
            "readiness_reason": self.readiness_reason,
            "blocking_reasons": self.blocking_reasons,
            "assessed_at": self.assessed_at,
            "assessed_by": self.assessed_by,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExecutionReadiness:
        data["required_proofs"] = data.get("required_proofs", [])
        data["satisfied_proofs"] = data.get("satisfied_proofs", [])
        data["missing_proofs"] = data.get("missing_proofs", [])
        data["failed_proofs"] = data.get("failed_proofs", [])
        data["blocking_reasons"] = data.get("blocking_reasons", [])
        return cls(**data)

    def update_readiness(self) -> None:
        """Update readiness state based on proof coverage and blocking reasons."""
        # Determine blocking reasons
        blocking = []
        
        if self.missing_proofs:
            blocking.append(f"Missing proofs: {', '.join(self.missing_proofs)}")
        
        if self.failed_proofs:
            blocking.append(f"Failed proofs: {', '.join(self.failed_proofs)}")
        
        if self.max_risk_severity in ["high", "critical"]:
            blocking.append(f"Risk not bounded: {self.max_risk_severity}")
        
        if not self.rollback_coverage or self.rollback_coverage < 0.5:
            blocking.append(f"Insufficient rollback coverage: {self.rollback_coverage:.0%}")
        
        self.blocking_reasons = blocking
        
        # Determine readiness state
        if self.missing_proofs or self.failed_proofs:
            self.readiness_state = ExecutionState.BLOCKED.value
            self.readiness_reason = "Required proofs missing or failed"
        elif not self.risk_bounded:
            self.readiness_state = ExecutionState.BLOCKED.value
            self.readiness_reason = "Risk not bounded"
        elif not self.rollback_coverage or self.rollback_coverage < 0.5:
            self.readiness_state = ExecutionState.BLOCKED.value
            self.readiness_reason = "Insufficient rollback coverage"
        elif not self.validation_coverage or self.validation_coverage < 0.8:
            self.readiness_state = ExecutionState.BLOCKED.value
            self.readiness_reason = "Insufficient validation coverage"
        else:
            self.readiness_state = ExecutionState.ELIGIBLE.value
            self.readiness_reason = "All proofs satisfied, risk bounded, rollback coverage sufficient"
        
        self.assessed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ProofGateEngine:
    """Enforces strict execution readiness and proof gate.
    
    Determines:
    - What proof is present
    - What proof is missing
    - Whether validation requirements are satisfied
    - Whether rollback coverage is sufficient
    - Whether risk is bounded enough
    - Whether execution should remain blocked
    """
    
    def __init__(self, execution_gate: ExecutionGate = None, realization_engine: RealizationEngine = None):
        self.gate = execution_gate or ExecutionGate()
        self.realization_engine = realization_engine or RealizationEngine(execution_gate=self.gate)
        
        # Default required proofs for execution eligibility
        self.required_proofs = [
            ProofType.VALIDATION.value,
            ProofType.RISK_ASSESSMENT.value,
            ProofType.ROLLBACK_COVERAGE.value,
            ProofType.IMPACT_ANALYSIS.value,
            ProofType.FORECAST_CONFIDENCE.value,
            ProofType.OPERATOR_REVIEW.value,
            ProofType.AUDIT_TRAIL.value,
        ]
    
    def evaluate_readiness(
        self,
        plan_id: str,
        proposal_id: str,
        assessed_by: str = "operator",
    ) -> ExecutionReadiness:
        """Evaluate execution readiness for a realization plan.
        
        Returns ExecutionReadiness with proof status and blocking reasons.
        """
        # Get the proposal to assess
        proposal = self.gate.get_proposal(proposal_id)
        if not proposal:
            return ExecutionReadiness(
                plan_id=plan_id,
                proposal_id=proposal_id,
                readiness_state=ExecutionState.BLOCKED.value,
                readiness_reason="Proposal not found",
                blocking_reasons=["Proposal not found"],
                assessed_by=assessed_by,
            )
        
        # Check if proposal is approved
        if proposal.state != "approved":
            return ExecutionReadiness(
                plan_id=plan_id,
                proposal_id=proposal_id,
                readiness_state=ExecutionState.BLOCKED.value,
                readiness_reason="Proposal not approved",
                blocking_reasons=["Proposal not approved"],
                assessed_by=assessed_by,
            )
        
        # Build proofs required for this proposal
        proofs = []
        for proof_type in self.required_proofs:
            proofs.append(ProofItem(
                proof_id=f"proof-{proof_type[:8]}",
                proof_type=proof_type,
                description=self._get_proof_description(proof_type),
                status=ProofStatus.REQUESTED.value,
            ).to_dict())
        
        # Evaluate each proof type
        satisfied = []
        missing = []
        failed = []
        
        # 1. Validation proof
        validation_proof = self._validate_validation(proposal)
        if validation_proof:
            satisfied.append(ProofType.VALIDATION.value)
            proofs[0]["status"] = ProofStatus.SATISFIED.value
            proofs[0]["verified_by"] = assessed_by
        else:
            missing.append(ProofType.VALIDATION.value)
        
        # 2. Risk assessment proof
        risk_proof = self._validate_risk_assessment(proposal)
        if risk_proof:
            satisfied.append(ProofType.RISK_ASSESSMENT.value)
            proofs[1]["status"] = ProofStatus.SATISFIED.value
            proofs[1]["verified_by"] = assessed_by
        else:
            missing.append(ProofType.RISK_ASSESSMENT.value)
        
        # 3. Rollback coverage proof
        rollback_proof, checkpoints_total, checkpoints_verified = self._validate_rollback(proposal)
        if rollback_proof:
            satisfied.append(ProofType.ROLLBACK_COVERAGE.value)
            proofs[2]["status"] = ProofStatus.SATISFIED.value
            proofs[2]["verified_by"] = assessed_by
        else:
            missing.append(ProofType.ROLLBACK_COVERAGE.value)
        
        # 4. Impact analysis proof
        impact_proof = self._validate_impact_analysis(proposal)
        if impact_proof:
            satisfied.append(ProofType.IMPACT_ANALYSIS.value)
            proofs[3]["status"] = ProofStatus.SATISFIED.value
            proofs[3]["verified_by"] = assessed_by
        else:
            missing.append(ProofType.IMPACT_ANALYSIS.value)
        
        # 5. Forecast confidence proof
        confidence_proof = self._validate_forecast_confidence(proposal)
        if confidence_proof:
            satisfied.append(ProofType.FORECAST_CONFIDENCE.value)
            proofs[4]["status"] = ProofStatus.SATISFIED.value
            proofs[4]["verified_by"] = assessed_by
        else:
            missing.append(ProofType.FORECAST_CONFIDENCE.value)
        
        # 6. Operator review proof
        review_proof = self._validate_operator_review(proposal)
        if review_proof:
            satisfied.append(ProofType.OPERATOR_REVIEW.value)
            proofs[5]["status"] = ProofStatus.SATISFIED.value
            proofs[5]["verified_by"] = assessed_by
        else:
            missing.append(ProofType.OPERATOR_REVIEW.value)
        
        # 7. Audit trail proof
        audit_proof = self._validate_audit_trail(proposal)
        if audit_proof:
            satisfied.append(ProofType.AUDIT_TRAIL.value)
            proofs[6]["status"] = ProofStatus.SATISFIED.value
            proofs[6]["verified_by"] = assessed_by
        else:
            missing.append(ProofType.AUDIT_TRAIL.value)
        
        # Calculate coverage
        validation_coverage = 1.0 if ProofType.VALIDATION.value in satisfied else 0.0
        rollback_coverage = 1.0 if ProofType.ROLLBACK_COVERAGE.value in satisfied else 0.0
        
        # Determine risk bounded status
        risk_bounded = proposal.risk_level in ["low", "medium"]
        risk_reason = None
        if not risk_bounded:
            risk_reason = f"Risk level {proposal.risk_level} exceeds bounded threshold"
        
        # Determine max risk severity
        max_risk = "unknown"
        if proposal.risk_level == "high":
            max_risk = "high"
        elif proposal.risk_level == "medium":
            max_risk = "medium"
        elif proposal.risk_level == "low":
            max_risk = "low"
        
        # Build readiness
        readiness = ExecutionReadiness(
            plan_id=plan_id,
            proposal_id=proposal_id,
            proofs=proofs,
            required_proofs=self.required_proofs,
            satisfied_proofs=satisfied,
            missing_proofs=missing,
            failed_proofs=failed,
            validation_coverage=validation_coverage,
            rollback_coverage=rollback_coverage,
            rollback_checkpoints_total=checkpoints_total,
            rollback_checkpoints_verified=checkpoints_verified,
            risk_bounded=risk_bounded,
            risk_reason=risk_reason,
            max_risk_severity=max_risk,
            assessed_by=assessed_by,
        )
        
        readiness.update_readiness()
        
        return readiness
    
    def _get_proof_description(self, proof_type: str) -> str:
        """Get description for a proof type."""
        descriptions = {
            ProofType.VALIDATION.value: "Validation requirements satisfied",
            ProofType.RISK_ASSESSMENT.value: "Risk assessment completed",
            ProofType.ROLLBACK_COVERAGE.value: "Rollback coverage verified",
            ProofType.IMPACT_ANALYSIS.value: "Impact analysis documented",
            ProofType.FORECAST_CONFIDENCE.value: "Forecast confidence >= 0.5",
            ProofType.OPERATOR_REVIEW.value: "Operator review completed",
            ProofType.AUDIT_TRAIL.value: "Complete audit trail present",
        }
        return descriptions.get(proof_type, proof_type)
    
    def _validate_validation(self, proposal: ChangeProposal) -> bool:
        """Validate that validation requirements are present."""
        return len(proposal.validation_requirements) > 0
    
    def _validate_risk_assessment(self, proposal: ChangeProposal) -> bool:
        """Validate that risk assessment is complete."""
        return proposal.risk_level in ["low", "medium", "high"]
    
    def _validate_rollback(self, proposal: ChangeProposal) -> tuple:
        """Validate rollback coverage.
        
        Returns (satisfied, total_checkpoints, verified_checkpoints).
        """
        # Check rollback expectations exist
        if not proposal.rollback_expectations:
            return False, 0, 0
        
        # Count checkpoints (simulated based on expectations)
        total = len(proposal.rollback_expectations)
        verified = total if proposal.estimated_effort < 70 else int(total * 0.8)
        
        # Require at least 50% verified
        return verified / total >= 0.5, total, verified
    
    def _validate_impact_analysis(self, proposal: ChangeProposal) -> bool:
        """Validate impact analysis is present."""
        # Require affected subsystems to be documented
        return len(proposal.affected_subsystems) > 0
    
    def _validate_forecast_confidence(self, proposal: ChangeProposal) -> bool:
        """Validate forecast confidence is sufficient."""
        return proposal.calibration_confidence >= 0.5
    
    def _validate_operator_review(self, proposal: ChangeProposal) -> bool:
        """Validate operator review is present."""
        # Check if proposal has been reviewed
        return proposal.approved_by is not None or len(proposal.audit_history) >= 2
    
    def _validate_audit_trail(self, proposal: ChangeProposal) -> bool:
        """Validate audit trail is complete."""
        # Require at least 2 audit entries (created + reviewed)
        return len(proposal.audit_history) >= 2
    
    def get_execution_eligibility(
        self,
        plan_id: str,
        proposal_id: str,
    ) -> Dict[str, Any]:
        """Get execution eligibility status for a realization plan.
        
        Returns dict with:
        - eligibility: "eligible", "not_eligible", "blocked", "pending_proof"
        - blocking_reasons: List of blocking reasons
        - missing_proofs: List of missing proofs
        - required_proofs: List of required proofs
        - coverage: Coverage metrics
        - risk_status: Risk assessment
        - can_proceed: Boolean whether execution can proceed
        """
        readiness = self.evaluate_readiness(plan_id, proposal_id)
        
        return {
            "eligibility": readiness.readiness_state,
            "plan_id": plan_id,
            "proposal_id": proposal_id,
            "blocking_reasons": readiness.blocking_reasons,
            "missing_proofs": readiness.missing_proofs,
            "satisfied_proofs": readiness.satisfied_proofs,
            "failed_proofs": readiness.failed_proofs,
            "required_proofs": readiness.required_proofs,
            "coverage": {
                "validation": readiness.validation_coverage,
                "rollback": readiness.rollback_coverage,
            },
            "risk": {
                "bounded": readiness.risk_bounded,
                "reason": readiness.risk_reason,
                "max_severity": readiness.max_risk_severity,
            },
            "proof_status": {
                "total": len(readiness.required_proofs),
                "satisfied": len(readiness.satisfied_proofs),
                "missing": len(readiness.missing_proofs),
                "failed": len(readiness.failed_proofs),
            },
            "can_proceed": readiness.readiness_state == ExecutionState.ELIGIBLE.value,
            "readiness_reason": readiness.readiness_reason,
        }
    
    def explain_blocking_reasons(
        self,
        plan_id: str,
        proposal_id: str,
    ) -> str:
        """Generate human-readable explanation of blocking reasons."""
        eligibility = self.get_execution_eligibility(plan_id, proposal_id)
        
        if eligibility["can_proceed"]:
            return "Plan is eligible for execution."
        
        reasons = []
        if eligibility["missing_proofs"]:
            reasons.append(f"Missing proofs: {', '.join(eligibility['missing_proofs'])}")
        if eligibility["failed_proofs"]:
            reasons.append(f"Failed proofs: {', '.join(eligibility['failed_proofs'])}")
        if eligibility["blocking_reasons"]:
            reasons.extend(eligibility["blocking_reasons"])
        if not eligibility["can_proceed"]:
            reasons.append("Cannot proceed with execution")
        
        return "; ".join(reasons)


def evaluate_readiness(
    plan_id: str,
    proposal_id: str,
    assessed_by: str = "operator",
) -> ExecutionReadiness:
    """Convenience function to evaluate readiness."""
    engine = ProofGateEngine()
    return engine.evaluate_readiness(plan_id, proposal_id, assessed_by)


def get_execution_eligibility(
    plan_id: str,
    proposal_id: str,
) -> Dict[str, Any]:
    """Convenience function to get execution eligibility."""
    engine = ProofGateEngine()
    return engine.get_execution_eligibility(plan_id, proposal_id)


def explain_blocking_reasons(
    plan_id: str,
    proposal_id: str,
) -> str:
    """Convenience function to explain blocking reasons."""
    engine = ProofGateEngine()
    return engine.explain_blocking_reasons(plan_id, proposal_id)


if __name__ == "__main__":
    # CLI interface
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python proof_gate.py <command> [args]")
        print("Commands:")
        print("  evaluate <plan_id> <proposal_id>")
        print("  eligibility <plan_id> <proposal_id>")
        print("  explain <plan_id> <proposal_id>")
        sys.exit(1)
    
    command = sys.argv[1]
    engine = ProofGateEngine()
    
    if command == "evaluate":
        if len(sys.argv) < 4:
            print("Usage: python proof_gate.py evaluate <plan_id> <proposal_id>")
            sys.exit(1)
        plan_id = sys.argv[2]
        proposal_id = sys.argv[3]
        readiness = engine.evaluate_readiness(plan_id, proposal_id)
        print(json.dumps(readiness.to_dict(), indent=2))
    
    elif command == "eligibility":
        if len(sys.argv) < 4:
            print("Usage: python proof_gate.py eligibility <plan_id> <proposal_id>")
            sys.exit(1)
        plan_id = sys.argv[2]
        proposal_id = sys.argv[3]
        eligibility = engine.get_execution_eligibility(plan_id, proposal_id)
        print(json.dumps(eligibility, indent=2))
    
    elif command == "explain":
        if len(sys.argv) < 4:
            print("Usage: python proof_gate.py explain <plan_id> <proposal_id>")
            sys.exit(1)
        plan_id = sys.argv[2]
        proposal_id = sys.argv[3]
        explanation = engine.explain_blocking_reasons(plan_id, proposal_id)
        print(explanation)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
