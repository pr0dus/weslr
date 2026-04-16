# change_proposals.py - Self-Architecture Core v12: Change Proposal Packaging / Execution Gate
# Turn architectural recommendations into structured, operator-governed change proposals.
# Additive only, operator-first, reversible, governed. No autonomous execution.

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ProposalState(str, Enum):
    """State of a change proposal."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    DENIED = "denied"
    DEFERRED = "deferred"
    DEPRECATED = "deprecated"


class ProposalType(str, Enum):
    """Types of change proposals."""
    NEW_SUBSYSTEM = "new_subsystem"
    IMPROVEMENT = "improvement"
    DEPRECATION = "deprecation"
    REFACTOR = "refactor"
    REMOVAL = "removal"
    CONFIGURATION = "configuration"


@dataclass
class AuditEntry:
    """A single audit trail entry."""
    
    timestamp: str
    actor: str  # "operator" or "system"
    action: str  # e.g., "proposal_created", "approved", "denied", "rollback"
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "actor": self.actor,
            "action": self.action,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuditEntry:
        return cls(**data)


@dataclass
class ChangeProposal:
    """A structured change proposal with operator-governed execution.
    
    Packages:
    - What is being proposed
    - Why
    - Affected subsystems
    - Forecast summary
    - Precedent/memory context
    - Risk/effort
    - Calibration confidence
    - Validation requirements
    - Rollback expectations
    - Approval state
    """
    
    proposal_id: str
    title: str
    description: str
    
    # Source
    source_suggestion: Optional[str] = None  # ID of source suggestion if any
    source_scenario: Optional[str] = None  # Scenario name if from scenario
    
    # Scope
    affected_subsystems: List[str] = field(default_factory=list)
    proposed_changes: List[str] = field(default_factory=list)
    
    # Rationale
    rationale: str = ""
    forecast_summary: Optional[str] = None
    expected_outcomes: List[str] = field(default_factory=list)
    
    # Context
    precedent_context: Optional[str] = None  # Link to similar past proposals
    memory_references: List[str] = field(default_factory=list)  # Memory snippet IDs
    
    # Assessment
    risk_level: str = "medium"  # low, medium, high
    estimated_effort: int = 50  # 1-100
    calibration_confidence: float = 0.5  # 0.0-1.0
    
    # Validation
    validation_requirements: List[str] = field(default_factory=list)
    rollback_expectations: List[str] = field(default_factory=list)
    
    # v20: Evidence ontology integration (additive, reversible)
    evidence_claim_ids: List[str] = field(default_factory=list)  # References to evidence claims
    evidence_chain_ids: List[str] = field(default_factory=list)  # Evidence chain IDs for provenance
    evidence_summary: str = ""  # Human-readable evidence summary
    evidence_confidence: float = 0.0  # 0.0-1.0 overall confidence
    
    # v21: Domain overlay integration (additive, reversible)
    domain_context: Optional[Dict[str, Any]] = None  # DomainContext dict reference
    domain_tag: Optional[str] = None  # Single domain tag for simpler references
    
    # v23: Safety contract integration (additive, reversible)
    action_type: Optional[str] = None  # ActionType.value if applicable
    safety_contract: Optional[Dict[str, Any]] = None  # SafetyContract dict reference
    safety_contract_summary: Optional[str] = None  # Human-readable summary
    
    # State
    state: str = ProposalState.PENDING_REVIEW.value
    approval_state: str = "pending"  # For operator clarity
    
    # Audit trail
    audit_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    submitted_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    approved_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "title": self.title,
            "description": self.description,
            "source_suggestion": self.source_suggestion,
            "source_scenario": self.source_scenario,
            "affected_subsystems": self.affected_subsystems,
            "proposed_changes": self.proposed_changes,
            "rationale": self.rationale,
            "forecast_summary": self.forecast_summary,
            "expected_outcomes": self.expected_outcomes,
            "precedent_context": self.precedent_context,
            "memory_references": self.memory_references,
            "risk_level": self.risk_level,
            "estimated_effort": self.estimated_effort,
            "calibration_confidence": self.calibration_confidence,
            "validation_requirements": self.validation_requirements,
            "rollback_expectations": self.rollback_expectations,
            # v20: Evidence integration
            "evidence_claim_ids": self.evidence_claim_ids,
            "evidence_chain_ids": self.evidence_chain_ids,
            "evidence_summary": self.evidence_summary,
            "evidence_confidence": self.evidence_confidence,
            # v21: Domain integration
            "domain_context": self.domain_context,
            "domain_tag": self.domain_tag,
            # v23: Safety contract integration
            "action_type": self.action_type,
            "safety_contract": self.safety_contract,
            "safety_contract_summary": self.safety_contract_summary,
            "state": self.state,
            "approval_state": self.approval_state,
            "audit_history": self.audit_history,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "submitted_by": self.submitted_by,
            "reviewed_at": self.reviewed_at,
            "approved_by": self.approved_by,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChangeProposal:
        data["affected_subsystems"] = data.get("affected_subsystems", [])
        data["proposed_changes"] = data.get("proposed_changes", [])
        data["expected_outcomes"] = data.get("expected_outcomes", [])
        data["memory_references"] = data.get("memory_references", [])
        data["validation_requirements"] = data.get("validation_requirements", [])
        data["rollback_expectations"] = data.get("rollback_expectations", [])
        # v20: Evidence integration
        data["evidence_claim_ids"] = data.get("evidence_claim_ids", [])
        data["evidence_chain_ids"] = data.get("evidence_chain_ids", [])
        data["evidence_summary"] = data.get("evidence_summary", "")
        data["evidence_confidence"] = data.get("evidence_confidence", 0.0)
        # v21: Domain integration
        data["domain_context"] = data.get("domain_context", None)
        data["domain_tag"] = data.get("domain_tag", None)
        # v23: Safety contract integration
        data["action_type"] = data.get("action_type", None)
        data["safety_contract"] = data.get("safety_contract", None)
        data["safety_contract_summary"] = data.get("safety_contract_summary", None)
        data["audit_history"] = data.get("audit_history", [])
        
        # Ensure state enum
        if "state" not in data:
            data["state"] = ProposalState.PENDING_REVIEW.value
        if "approval_state" not in data:
            data["approval_state"] = "pending"
        
        return cls(**data)

    def add_audit_entry(self, action: str, actor: str = "system", details: Dict[str, Any] = None) -> None:
        """Add an audit trail entry."""
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            actor=actor,
            action=action,
            details=details or {},
        )
        self.audit_history.append(entry.to_dict())
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def transition_state(self, new_state: str, actor: str = "operator", details: Dict[str, Any] = None) -> None:
        """Transition to a new state with audit trail."""
        self.state = new_state
        self.approval_state = self._map_state_to_approval(new_state)
        self.add_audit_entry(
            action=f"state_transition:{new_state}",
            actor=actor,
            details=details or {},
        )
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _map_state_to_approval(self, state: str) -> str:
        """Map internal state to operator-facing approval state."""
        mapping = {
            ProposalState.DRAFT.value: "pending",
            ProposalState.PENDING_REVIEW.value: "pending",
            ProposalState.APPROVED.value: "approved",
            ProposalState.DENIED.value: "denied",
            ProposalState.DEFERRED.value: "deferred",
            ProposalState.DEPRECATED.value: "deprecated",
        }
        return mapping.get(state, "unknown")

    def is_approved_for_execution(self) -> bool:
        """Check if proposal is approved for execution."""
        return self.state == ProposalState.APPROVED.value

    def is_reversible(self) -> bool:
        """Check if changes are reversible."""
        # Proposals are additive-only by design, so always reversible
        # Actual reversibility depends on rollback expectations being documented
        return len(self.rollback_expectations) > 0 or "additive" in self.rationale.lower()

    def get_execution_gate_status(self) -> Dict[str, Any]:
        """Get execution gate status for operator review."""
        return {
            "can_execute": self.is_approved_for_execution(),
            "state": self.state,
            "approval_state": self.approval_state,
            "requires_approval": self.state != ProposalState.APPROVED.value,
            "rollback_expectations": self.rollback_expectations,
            "validation_requirements": self.validation_requirements,
            "audit_count": len(self.audit_history),
            "last_audit": self.audit_history[-1] if self.audit_history else None,
        }


class ExecutionGate:
    """Enforces operator-governed execution of change proposals.
    
    Strict rules:
    - Additive only
    - Operator-first
    - Reversible
    - No autonomous execution
    - No repo drift
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("continuity/change_proposals.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.proposals: Dict[str, ChangeProposal] = {}
        self._load_proposals()

    def _load_proposals(self) -> None:
        """Load proposals from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.proposals = {
                        k: ChangeProposal.from_dict(v) 
                        for k, v in data.get("proposals", {}).items()
                    }
            except (json.JSONDecodeError, IOError):
                self.proposals = {}

    def _save_proposals(self) -> None:
        """Save proposals to storage."""
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump({
                "proposals": {k: v.to_dict() for k, v in self.proposals.items()},
                "last_updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }, f, indent=2)

    def create_proposal(
        self,
        title: str,
        description: str,
        affected_subsystems: List[str] = None,
        source_suggestion: str = None,
        submitted_by: str = "operator",
        **kwargs,
    ) -> ChangeProposal:
        """Create a new change proposal in PENDING_REVIEW state."""
        proposal_id = f"prop-{uuid.uuid4().hex[:8]}"
        
        proposal = ChangeProposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            affected_subsystems=affected_subsystems or [],
            source_suggestion=source_suggestion,
            submitted_by=submitted_by,
            **kwargs,
        )
        
        # Initial audit entry
        proposal.add_audit_entry(
            action="proposal_created",
            actor=submitted_by,
            details={"source": source_suggestion},
        )
        
        self.proposals[proposal_id] = proposal
        self._save_proposals()
        
        return proposal

    def package_proposal(
        self,
        suggestion_data: Dict[str, Any],
        source_scenario: str = None,
        submitted_by: str = "operator",
    ) -> ChangeProposal:
        """Package a suggestion into a structured proposal for review.
        
        This is the primary operator-integration entry point.
        """
        # Extract suggestion data
        suggestion_id = suggestion_data.get("id", f"suggest-{uuid.uuid4().hex[:6]}")
        title = suggestion_data.get("title", "Untitled Suggestion")
        description = suggestion_data.get("description", "")
        affected = suggestion_data.get("affected_subsystems", [])
        
        # Extract assessment data
        risk = suggestion_data.get("risk_level", "medium")
        effort = suggestion_data.get("implementation_effort_estimate", 50)
        confidence = suggestion_data.get("calibration_confidence", 0.5)
        
        # Extract context
        forecast = suggestion_data.get("forecast_summary")
        outcomes = suggestion_data.get("expected_outcomes", [])
        precedent = suggestion_data.get("precedent_context")
        memory_refs = suggestion_data.get("memory_references", [])
        rationale = suggestion_data.get("rationale", f"Operator-driven improvement suggestion: {suggestion_id}")
        
        # Build validation requirements
        validation = [
            "self_architecture_review",
            "impact_analysis",
            "rollback_verification",
        ]
        
        # Build rollback expectations
        rollback = [
            "revert file modifications",
            "restore previous configuration",
            "re-run calibration to confirm",
        ]
        
        return self.create_proposal(
            title=title,
            description=description,
            affected_subsystems=affected,
            source_suggestion=suggestion_id,
            source_scenario=source_scenario,
            submitted_by=submitted_by,
            risk_level=risk,
            estimated_effort=effort,
            calibration_confidence=confidence,
            forecast_summary=forecast,
            expected_outcomes=outcomes,
            precedent_context=precedent,
            memory_references=memory_refs,
            rationale=rationale,
            validation_requirements=validation,
            rollback_expectations=rollback,
        )

    def review_proposal(
        self,
        proposal_id: str,
        action: str,
        actor: str = "operator",
        details: Dict[str, Any] = None,
    ) -> Optional[ChangeProposal]:
        """Review and act on a proposal.
        
        Actions:
        - approve: Move to APPROVED state, mark for execution
        - deny: Move to DENIED state, mark as rejected
        - defer: Move to DEFERRED state, schedule for later review
        - counterpropose: Mark as DENIED and emit governance override signal
        - dismiss: Mark as DENIED and emit ignored signal
        
        Returns None if proposal not found.
        """
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return None
        
        if action == "approve":
            proposal.transition_state(
                ProposalState.APPROVED.value,
                actor=actor,
                details=details or {},
            )
            proposal.approved_by = actor
            proposal.reviewed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        elif action == "deny":
            proposal.transition_state(
                ProposalState.DENIED.value,
                actor=actor,
                details=details or {},
            )
            # Emit governance override signal (fail-open)
            try:
                from weslr.drift_emitter import emit_override_signal
                emit_override_signal("denied", proposal_id=str(proposal.proposal_id), human=str(actor))
            except Exception:
                pass
        elif action == "defer":
            proposal.transition_state(
                ProposalState.DEFERRED.value,
                actor=actor,
                details=details or {},
            )
        elif action == "counterpropose":
            # Counter-propose: operator substitutes their own version.
            # Transition to DENIED (rejects WESLR's version) and emit override signal.
            # Full counter-proposal submission (new proposal text) is a future surface enhancement.
            proposal.transition_state(
                ProposalState.DENIED.value,
                actor=actor,
                details=details or {},
            )
            # Emit governance override signal (fail-open)
            try:
                from weslr.drift_emitter import emit_counterproposed_signal
                emit_counterproposed_signal(proposal_id=str(proposal.proposal_id), human=str(actor))
            except Exception:
                pass
        elif action == "dismiss":
            # Dismiss: operator explicitly dismisses without adopting — treated as ignored.
            proposal.transition_state(
                ProposalState.DENIED.value,
                actor=actor,
                details=details or {},
            )
            # Emit governance override signal (fail-open)
            try:
                from weslr.drift_emitter import emit_ignored_signal
                emit_ignored_signal(proposal_id=str(proposal.proposal_id), human=str(actor))
            except Exception:
                pass
        else:
            raise ValueError(f"Unknown action: {action}. Use: approve, deny, defer, counterpropose, dismiss")
        
        self._save_proposals()
        return proposal

    def get_proposal(self, proposal_id: str) -> Optional[ChangeProposal]:
        """Get a proposal by ID."""
        return self.proposals.get(proposal_id)

    def get_proposals_by_state(self, state: str) -> List[ChangeProposal]:
        """Get all proposals in a given state."""
        return [p for p in self.proposals.values() if p.state == state]

    def get_pending_proposals(self) -> List[ChangeProposal]:
        """Get all proposals pending review."""
        return self.get_proposals_by_state(ProposalState.PENDING_REVIEW.value)

    def get_approved_proposals(self) -> List[ChangeProposal]:
        """Get all approved proposals ready for execution."""
        return self.get_proposals_by_state(ProposalState.APPROVED.value)

    def get_all_proposals(self) -> List[Dict[str, Any]]:
        """Get all proposals as dicts for operator review."""
        return [p.to_dict() for p in self.proposals.values()]

    def get_proposal_audit_history(self, proposal_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get audit history for a proposal."""
        proposal = self.proposals.get(proposal_id)
        if proposal:
            return proposal.audit_history
        return None

    def generate_proposal_review_output(
        self,
        proposal_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Generate operator-facing review output for a proposal.
        
        Packages all required information in a single structured output.
        """
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return None
        
        return {
            "proposal_id": proposal.proposal_id,
            "title": proposal.title,
            "description": proposal.description,
            
            # Source context
            "source": {
                "suggestion": proposal.source_suggestion,
                "scenario": proposal.source_scenario,
                "submitted_by": proposal.submitted_by,
                "created_at": proposal.created_at,
            },
            
            # Scope
            "scope": {
                "affected_subsystems": proposal.affected_subsystems,
                "proposed_changes": proposal.proposed_changes,
            },
            
            # Assessment
            "assessment": {
                "risk_level": proposal.risk_level,
                "estimated_effort": proposal.estimated_effort,
                "calibration_confidence": proposal.calibration_confidence,
                "forecast_summary": proposal.forecast_summary,
                "expected_outcomes": proposal.expected_outcomes,
            },
            
            # Context
            "context": {
                "rationale": proposal.rationale,
                "precedent_context": proposal.precedent_context,
                "memory_references": proposal.memory_references,
            },
            
            # Validation & rollback
            "governance": {
                "validation_requirements": proposal.validation_requirements,
                "rollback_expectations": proposal.rollback_expectations,
                "can_execute": proposal.is_approved_for_execution(),
                "is_reversible": proposal.is_reversible(),
            },
            
            # State
            "state": {
                "current": proposal.state,
                "approval_state": proposal.approval_state,
                "updated_at": proposal.updated_at,
            },
            
            # Execution gate
            "execution_gate": proposal.get_execution_gate_status(),
            
            # Audit history
            "audit_history": proposal.audit_history,
        }

    def execute_proposal_if_approved(
        self,
        proposal_id: str,
        execution_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Execute a proposal only if it's in APPROVED state.
        
        Returns execution result dict.
        """
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return {"success": False, "error": "Proposal not found"}
        
        # Execution gate check
        if not proposal.is_approved_for_execution():
            return {
                "success": False,
                "error": "Execution blocked",
                "reason": f"Proposal state is '{proposal.state}', must be 'approved'",
                "can_execute": False,
                "state": proposal.state,
            }
        
        # Simulate execution (actual implementation would call subsystems)
        execution_result = {
            "success": True,
            "proposal_id": proposal_id,
            "executed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "execution_context": execution_context or {},
            "audit": {
                "executed_by": execution_context.get("actor", "system"),
                "blockchain_hash": f"exec-{uuid.uuid4().hex[:8]}",
            },
        }
        
        # Update audit trail
        proposal.add_audit_entry(
            action="execution_completed",
            actor=execution_result["audit"]["executed_by"],
            details=execution_result,
        )
        self._save_proposals()
        
        return execution_result


def create_proposal(
    title: str,
    description: str,
    affected_subsystems: List[str] = None,
    source_suggestion: str = None,
    **kwargs,
) -> ChangeProposal:
    """Convenience function to create a proposal."""
    gate = ExecutionGate()
    return gate.create_proposal(
        title=title,
        description=description,
        affected_subsystems=affected_subsystems or [],
        source_suggestion=source_suggestion,
        **kwargs,
    )


def package_suggestion(
    suggestion_data: Dict[str, Any],
    source_scenario: str = None,
) -> ChangeProposal:
    """Convenience function to package a suggestion."""
    gate = ExecutionGate()
    return gate.package_proposal(suggestion_data, source_scenario)


def get_execution_gate() -> ExecutionGate:
    """Get the global execution gate instance."""
    return ExecutionGate()
