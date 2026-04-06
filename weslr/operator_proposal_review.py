# operator_proposal_review.py - Self-Architecture Core v13: Operator Proposal Review Surface
# Make governed change proposals easy to inspect and manage in live operator flow.
# Additive only, operator-first, reversible, governed. No autonomous execution.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from change_proposals import (
    ChangeProposal,
    ExecutionGate,
    ProposalState,
)


@dataclass
class OperatorReviewOutput:
    """Operator-facing review output for a proposal."""
    
    proposal_id: str
    title: str
    description: str
    
    # Summary
    summary: str = ""
    priority: str = "medium"  # low, medium, high
    
    # Source
    source: Dict[str, Any] = field(default_factory=dict)
    
    # Scope
    affected_subsystems: List[str] = field(default_factory=list)
    
    # Assessment
    risk_level: str = "medium"
    estimated_effort: int = 50
    calibration_confidence: float = 0.5
    
    # Rationale & Context
    rationale: str = ""
    forecast_summary: Optional[str] = None
    expected_outcomes: List[str] = field(default_factory=list)
    precedent_context: Optional[str] = None
    memory_references: List[str] = field(default_factory=list)
    
    # Governance
    validation_requirements: List[str] = field(default_factory=list)
    rollback_expectations: List[str] = field(default_factory=list)
    
    # v20: Evidence integration
    evidence_claim_ids: List[str] = field(default_factory=list)
    evidence_chain_ids: List[str] = field(default_factory=list)
    evidence_summary: str = ""
    evidence_confidence: float = 0.0
    
    # v21: Domain integration (additive, reversible)
    domain_tag: Optional[str] = None
    domain_profile_id: Optional[str] = None
    
    # v22: Edge reliability integration (additive, reversible)
    operation_mode: Optional[str] = None
    available_capabilities: List[str] = field(default_factory=list)
    unavailable_capabilities: List[str] = field(default_factory=list)
    
    # State
    current_state: str = "pending_review"
    approval_state: str = "pending"
    created_at: str = ""
    updated_at: str = ""
    
    # Audit history
    audit_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Available actions
    available_actions: List[str] = field(default_factory=list)
    
    # Metadata
    operator_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "title": self.title,
            "description": self.description,
            "summary": self.summary,
            "priority": self.priority,
            "source": self.source,
            "affected_subsystems": self.affected_subsystems,
            "risk_level": self.risk_level,
            "estimated_effort": self.estimated_effort,
            "calibration_confidence": self.calibration_confidence,
            "rationale": self.rationale,
            "forecast_summary": self.forecast_summary,
            "expected_outcomes": self.expected_outcomes,
            "precedent_context": self.precedent_context,
            "memory_references": self.memory_references,
            "validation_requirements": self.validation_requirements,
            "rollback_expectations": self.rollback_expectations,
            # v20: Evidence integration
            "evidence_claim_ids": self.evidence_claim_ids,
            "evidence_chain_ids": self.evidence_chain_ids,
            "evidence_summary": self.evidence_summary,
            "evidence_confidence": self.evidence_confidence,
            # v21: Domain integration
            "domain_tag": self.domain_tag,
            "domain_profile_id": self.domain_profile_id,
            # v22: Reliability integration
            "operation_mode": self.operation_mode,
            "available_capabilities": self.available_capabilities,
            "unavailable_capabilities": self.unavailable_capabilities,
            "current_state": self.current_state,
            "approval_state": self.approval_state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "audit_history": self.audit_history,
            "available_actions": self.available_actions,
            "operator_notes": self.operator_notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OperatorReviewOutput:
        data["evidence_claim_ids"] = data.get("evidence_claim_ids", [])
        data["evidence_chain_ids"] = data.get("evidence_chain_ids", [])
        data["evidence_summary"] = data.get("evidence_summary", "")
        data["evidence_confidence"] = data.get("evidence_confidence", 0.0)
        # v21: Domain integration
        data["domain_tag"] = data.get("domain_tag", None)
        data["domain_profile_id"] = data.get("domain_profile_id", None)
        # v22: Reliability integration
        data["operation_mode"] = data.get("operation_mode", None)
        data["available_capabilities"] = data.get("available_capabilities", [])
        data["unavailable_capabilities"] = data.get("unavailable_capabilities", [])
        return cls(**data)

    def format_for_display(self) -> str:
        """Format for human-readable console display."""
        lines = []
        lines.append(f"{'=' * 60}")
        lines.append(f"PROPOSAL: {self.proposal_id}")
        lines.append(f"TITLE: {self.title}")
        lines.append(f"{'=' * 60}")
        lines.append("")
        lines.append(f"DESCRIPTION:\n{self.description}")
        lines.append("")
        lines.append(f"SUMMARY: {self.summary}")
        lines.append(f"PRIORITY: {self.priority}")
        lines.append("")
        lines.append(f"AFFECTED SUBSYSTEMS: {', '.join(self.affected_subsystems) if self.affected_subsystems else 'None'}")
        lines.append("")
        lines.append(f"RISK LEVEL: {self.risk_level}")
        lines.append(f"ESTIMATED EFFORT: {self.estimated_effort}")
        lines.append(f"CALIBRATION CONFIDENCE: {self.calibration_confidence:.2f}")
        lines.append("")
        if self.rationale:
            lines.append(f"RATIONALE:\n{self.rationale}")
            lines.append("")
        if self.forecast_summary:
            lines.append(f"FORECAST SUMMARY:\n{self.forecast_summary}")
            lines.append("")
        if self.expected_outcomes:
            lines.append(f"EXPECTED OUTCOMES:")
            for outcome in self.expected_outcomes:
                lines.append(f"  - {outcome}")
            lines.append("")
        if self.precedent_context:
            lines.append(f"PRECEDENT CONTEXT: {self.precedent_context}")
            lines.append("")
        if self.memory_references:
            lines.append(f"MEMORY REFERENCES: {', '.join(self.memory_references)}")
            lines.append("")
        lines.append(f"VALIDATION REQUIREMENTS: {', '.join(self.validation_requirements) if self.validation_requirements else 'None'}")
        lines.append(f"ROLLBACK EXPECTATIONS: {', '.join(self.rollback_expectations) if self.rollback_expectations else 'None'}")
        lines.append("")
        lines.append(f"CURRENT STATE: {self.current_state}")
        lines.append(f"APPROVAL STATE: {self.approval_state}")
        lines.append(f"CREATED: {self.created_at}")
        lines.append(f"UPDATED: {self.updated_at}")
        lines.append("")
        lines.append(f"AVAILABLE ACTIONS: {', '.join(self.available_actions) if self.available_actions else 'None'}")
        lines.append("")
        if self.audit_history:
            lines.append("AUDIT HISTORY:")
            for entry in self.audit_history:
                ts = entry.get("timestamp", "unknown")
                actor = entry.get("actor", "system")
                action = entry.get("action", "unknown")
                details = entry.get("details", {})
                lines.append(f"  [{ts}] {actor}: {action}")
                if details:
                    for k, v in details.items():
                        lines.append(f"      {k}: {v}")
            lines.append("")
        if self.operator_notes:
            lines.append(f"OPERATOR NOTES: {self.operator_notes}")
            lines.append("")
        lines.append(f"{'=' * 60}")
        return "\n".join(lines)


class OperatorProposalReview:
    """Operator-facing proposal review interface.
    
    Supports:
    - list proposals
    - show proposal detail
    - approve / deny / defer
    - show audit history
    - show rollback expectations
    """
    
    def __init__(self, storage_path: Optional[Path] = None, gate: ExecutionGate = None):
        # Use provided gate or create new with storage path
        if gate is not None:
            self.gate = gate
            self.storage_path = gate.storage_path
        else:
            self.storage_path = storage_path or Path("continuity/change_proposals.json")
            self.gate = ExecutionGate(storage_path=self.storage_path)
    
    def list_proposals(self) -> List[Dict[str, Any]]:
        """List all proposals with summary information."""
        proposals = self.gate.get_all_proposals()
        
        result = []
        for p in proposals:
            result.append({
                "proposal_id": p["proposal_id"],
                "title": p["title"],
                "state": p["state"],
                "approval_state": p["approval_state"],
                "affected_subsystems": p.get("affected_subsystems", []),
                "risk_level": p.get("risk_level", "medium"),
                "created_at": p.get("created_at", ""),
                "audit_count": len(p.get("audit_history", [])),
            })
        
        return result
    
    def get_proposal_detail(self, proposal_id: str) -> Optional[OperatorReviewOutput]:
        """Get detailed review output for a proposal."""
        proposal = self.gate.get_proposal(proposal_id)
        if not proposal:
            return None
        
        review_output = self.gate.generate_proposal_review_output(proposal_id)
        if not review_output:
            return None
        
        # Build operator review output
        return OperatorReviewOutput(
            proposal_id=proposal.proposal_id,
            title=proposal.title,
            description=proposal.description,
            summary=f"Proposed {len(proposal.affected_subsystems)} subsystem change(s)",
            priority=self._map_risk_to_priority(proposal.risk_level),
            source={
                "suggestion": proposal.source_suggestion,
                "scenario": proposal.source_scenario,
                "submitted_by": proposal.submitted_by,
                "created_at": proposal.created_at,
            },
            affected_subsystems=proposal.affected_subsystems,
            risk_level=proposal.risk_level,
            estimated_effort=proposal.estimated_effort,
            calibration_confidence=proposal.calibration_confidence,
            rationale=proposal.rationale,
            forecast_summary=proposal.forecast_summary,
            expected_outcomes=proposal.expected_outcomes,
            precedent_context=proposal.precedent_context,
            memory_references=proposal.memory_references,
            validation_requirements=proposal.validation_requirements,
            rollback_expectations=proposal.rollback_expectations,
            current_state=proposal.state,
            approval_state=proposal.approval_state,
            created_at=proposal.created_at,
            updated_at=proposal.updated_at,
            audit_history=proposal.audit_history,
            available_actions=self._get_available_actions(proposal.state),
        )
    
    def _map_risk_to_priority(self, risk: str) -> str:
        """Map risk level to priority."""
        mapping = {
            "low": "low",
            "medium": "medium",
            "high": "high",
        }
        return mapping.get(risk, "medium")
    
    def _get_available_actions(self, current_state: str) -> List[str]:
        """Get available actions based on current state."""
        actions = []
        
        if current_state == ProposalState.PENDING_REVIEW.value:
            actions.extend(["approve", "deny", "defer"])
        elif current_state == ProposalState.DRAFT.value:
            actions.extend(["submit_for_review", "discard"])
        elif current_state == ProposalState.APPROVED.value:
            actions.extend(["execute", "rollback"])
        elif current_state == ProposalState.DENIED.value:
            actions.extend(["resubmit"])
        elif current_state == ProposalState.DEFERRED.value:
            actions.extend(["approve", "deny", "defer", "resubmit"])
        
        return actions
    
    def approve_proposal(self, proposal_id: str, actor: str = "operator", details: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Approve a proposal."""
        proposal = self.gate.review_proposal(proposal_id, "approve", actor, details)
        if not proposal:
            return None
        return {
            "success": True,
            "proposal_id": proposal_id,
            "new_state": proposal.state,
            "approval_state": proposal.approval_state,
            "reviewed_at": proposal.reviewed_at,
        }
    
    def deny_proposal(self, proposal_id: str, actor: str = "operator", details: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Deny a proposal."""
        proposal = self.gate.review_proposal(proposal_id, "deny", actor, details)
        if not proposal:
            return None
        return {
            "success": True,
            "proposal_id": proposal_id,
            "new_state": proposal.state,
            "approval_state": proposal.approval_state,
        }
    
    def defer_proposal(self, proposal_id: str, actor: str = "operator", details: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Defer a proposal."""
        proposal = self.gate.review_proposal(proposal_id, "defer", actor, details)
        if not proposal:
            return None
        return {
            "success": True,
            "proposal_id": proposal_id,
            "new_state": proposal.state,
            "approval_state": proposal.approval_state,
        }
    
    def get_audit_history(self, proposal_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get audit history for a proposal."""
        return self.gate.get_proposal_audit_history(proposal_id)
    
    def get_pending_proposals(self) -> List[Dict[str, Any]]:
        """Get all pending review proposals."""
        return self.gate.get_pending_proposals()
    
    def get_approved_proposals(self) -> List[Dict[str, Any]]:
        """Get all approved proposals."""
        return self.gate.get_approved_proposals()
    
    def generate_review_summary(self) -> Dict[str, Any]:
        """Generate operator-facing review summary."""
        all_proposals = self.list_proposals()
        
        return {
            "total_proposals": len(all_proposals),
            "pending_review": len([p for p in all_proposals if p["state"] == ProposalState.PENDING_REVIEW.value]),
            "approved": len([p for p in all_proposals if p["state"] == ProposalState.APPROVED.value]),
            "denied": len([p for p in all_proposals if p["state"] == ProposalState.DENIED.value]),
            "deferred": len([p for p in all_proposals if p["state"] == ProposalState.DEFERRED.value]),
            "total_risk_high": len([p for p in all_proposals if p["risk_level"] == "high"]),
            "last_updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }


def list_proposals() -> List[Dict[str, Any]]:
    """Convenience function to list all proposals."""
    storage_path = Path("/data/data/com.termux/files/home/.openclaw/workspace/continuity/change_proposals.json")
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    review = OperatorProposalReview(storage_path=storage_path)
    return review.list_proposals()


def show_proposal(proposal_id: str) -> Optional[OperatorReviewOutput]:
    """Convenience function to show proposal detail."""
    storage_path = Path("/data/data/com.termux/files/home/.openclaw/workspace/continuity/change_proposals.json")
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    review = OperatorProposalReview(storage_path=storage_path)
    return review.get_proposal_detail(proposal_id)


def approve_proposal(proposal_id: str, actor: str = "operator", details: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Convenience function to approve a proposal."""
    storage_path = Path("/data/data/com.termux/files/home/.openclaw/workspace/continuity/change_proposals.json")
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    review = OperatorProposalReview(storage_path=storage_path)
    return review.approve_proposal(proposal_id, actor, details)


def deny_proposal(proposal_id: str, actor: str = "operator", details: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Convenience function to deny a proposal."""
    storage_path = Path("/data/data/com.termux/files/home/.openclaw/workspace/continuity/change_proposals.json")
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    review = OperatorProposalReview(storage_path=storage_path)
    return review.deny_proposal(proposal_id, actor, details)


def defer_proposal(proosal_id: str, actor: str = "operator", details: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Convenience function to defer a proposal."""
    # Use workspace continuity path for consistency
    storage_path = Path("/data/data/com.termux/files/home/.openclaw/workspace/continuity/change_proposals.json")
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    review = OperatorProposalReview(storage_path=storage_path)
    return review.defer_proposal(proosal_id, actor, details)


def get_audit_history(proposal_id: str) -> Optional[List[Dict[str, Any]]]:
    """Convenience function to get audit history."""
    storage_path = Path("/data/data/com.termux/files/home/.openclaw/workspace/continuity/change_proposals.json")
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    review = OperatorProposalReview(storage_path=storage_path)
    return review.get_audit_history(proposal_id)


def get_review_summary() -> Dict[str, Any]:
    """Convenience function to get review summary."""
    storage_path = Path("/data/data/com.termux/files/home/.openclaw/workspace/continuity/change_proposals.json")
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    review = OperatorProposalReview(storage_path=storage_path)
    return review.generate_review_summary()


if __name__ == "__main__":
    # CLI interface
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python operator_proposal_review.py <command> [args]")
        print("Commands:")
        print("  list")
        print("  show <proposal_id>")
        print("  approve <proposal_id>")
        print("  deny <proposal_id>")
        print("  defer <proposal_id>")
        print("  audit <proposal_id>")
        print("  summary")
        sys.exit(1)
    
    command = sys.argv[1]
    review = OperatorProposalReview()
    
    if command == "list":
        proposals = review.list_proposals()
        if not proposals:
            print("No proposals found.")
        else:
            print("Proposals:")
            for p in proposals:
                print(f"  [{p['proposal_id']}] {p['title']} [{p['state']}] ({p['risk_level']} risk)")
    
    elif command == "show":
        if len(sys.argv) < 3:
            print("Usage: python operator_proposal_review.py show <proposal_id>")
            sys.exit(1)
        proposal_id = sys.argv[2]
        detail = review.get_proposal_detail(proposal_id)
        if detail:
            print(detail.format_for_display())
        else:
            print(f"Proposal not found: {proposal_id}")
    
    elif command == "approve":
        if len(sys.argv) < 3:
            print("Usage: python operator_proposal_review.py approve <proposal_id>")
            sys.exit(1)
        proposal_id = sys.argv[2]
        result = review.approve_proposal(proposal_id)
        if result:
            print(f"Approved: {proposal_id}")
            print(f"New state: {result['new_state']}")
        else:
            print(f"Proposal not found: {proposal_id}")
    
    elif command == "deny":
        if len(sys.argv) < 3:
            print("Usage: python operator_proposal_review.py deny <proposal_id>")
            sys.exit(1)
        proposal_id = sys.argv[2]
        result = review.deny_proposal(proposal_id)
        if result:
            print(f"Denied: {proposal_id}")
            print(f"New state: {result['new_state']}")
        else:
            print(f"Proposal not found: {proposal_id}")
    
    elif command == "defer":
        if len(sys.argv) < 3:
            print("Usage: python operator_proposal_review.py defer <proposal_id>")
            sys.exit(1)
        proposal_id = sys.argv[2]
        result = review.defer_proposal(proposal_id)
        if result:
            print(f"Deferred: {proposal_id}")
            print(f"New state: {result['new_state']}")
        else:
            print(f"Proposal not found: {proposal_id}")
    
    elif command == "audit":
        if len(sys.argv) < 3:
            print("Usage: python operator_proposal_review.py audit <proposal_id>")
            sys.exit(1)
        proposal_id = sys.argv[2]
        audit = review.get_audit_history(proposal_id)
        if audit:
            for entry in audit:
                print(f"[{entry.get('timestamp', 'unknown')}] {entry.get('actor', 'system')}: {entry.get('action', 'unknown')}")
        else:
            print(f"Proposal not found: {proposal_id}")
    
    elif command == "summary":
        summary = review.generate_review_summary()
        print(json.dumps(summary, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
