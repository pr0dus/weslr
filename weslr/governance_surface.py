# governance_surface.py - Self-Architecture Core v16: Unified Operator Governance Surface
# One operator-facing surface that unifies the whole governed decision chain for a proposal.
# Additive only, operator-first, reversible, governed. No autonomous execution.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from change_proposals import ChangeProposal, ExecutionGate, ProposalState
from forecast import ForecastEngine
from narrative import NarrativeBlock, UnifiedNarrative, RecommendationType
from operator_proposal_review import OperatorProposalReview, OperatorReviewOutput
from proposal_realization import RealizationEngine, RealizationPlan
from proof_gate import ProofGateEngine, ExecutionState


@dataclass
class ProposalGovernanceView:
    """Unified operator-facing governance view for a proposal.
    
    Packages:
    - Why it surfaced (narrative context)
    - Subsystem impact
    - Precedent / memory context
    - Forecast
    - Comparison / tradeoff context
    - Realization plan summary
    - Proof gate / execution eligibility
    - Blocking reasons
    - Approval / defer / deny context
    """
    
    proposal_id: str
    title: str
    description: str
    
    # Narrative context
    summary: str = ""
    why_surfaced: str = ""
    subsystem_impact: List[str] = field(default_factory=list)
    risk_effort: Dict[str, Any] = field(default_factory=dict)
    architectural_fit: str = ""
    
    # Forecast and comparison
    forecast_summary: Optional[str] = None
    forecast_confidence: float = 0.0
    tradeoff_context: Optional[str] = None
    comparison_with_alternatives: List[Dict[str, Any]] = field(default_factory=list)
    
    # Realization
    realization_plan_id: Optional[str] = None
    realization_status: Optional[str] = None
    realization_phases: List[str] = field(default_factory=list)
    current_phase: Optional[str] = None
    blockers: List[Dict[str, Any]] = field(default_factory=list)
    
    # Proof gate
    execution_eligibility: Optional[Dict[str, Any]] = None
    proof_status: Optional[Dict[str, Any]] = None
    blocking_reasons: List[str] = field(default_factory=list)
    can_proceed: bool = False
    
    # Operator actions
    approval_state: str = "pending"
    available_actions: List[str] = field(default_factory=list)
    recommended_action: str = "review"
    recommended_action_reason: str = ""
    
    # Audit history
    audit_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    created_at: str = ""
    updated_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "title": self.title,
            "description": self.description,
            "summary": self.summary,
            "why_surfaced": self.why_surfaced,
            "subsystem_impact": self.subsystem_impact,
            "risk_effort": self.risk_effort,
            "architectural_fit": self.architectural_fit,
            "forecast_summary": self.forecast_summary,
            "forecast_confidence": self.forecast_confidence,
            "tradeoff_context": self.tradeoff_context,
            "comparison_with_alternatives": self.comparison_with_alternatives,
            "realization_plan_id": self.realization_plan_id,
            "realization_status": self.realization_status,
            "realization_phases": self.realization_phases,
            "current_phase": self.current_phase,
            "blockers": self.blockers,
            "execution_eligibility": self.execution_eligibility,
            "proof_status": self.proof_status,
            "blocking_reasons": self.blocking_reasons,
            "can_proceed": self.can_proceed,
            "approval_state": self.approval_state,
            "available_actions": self.available_actions,
            "recommended_action": self.recommended_action,
            "recommended_action_reason": self.recommended_action_reason,
            "audit_history": self.audit_history,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProposalGovernanceView:
        data["subsystem_impact"] = data.get("subsystem_impact", [])
        data["comparison_with_alternatives"] = data.get("comparison_with_alternatives", [])
        data["blockers"] = data.get("blockers", [])
        data["realization_phases"] = data.get("realization_phases", [])
        data["blocking_reasons"] = data.get("blocking_reasons", [])
        data["available_actions"] = data.get("available_actions", [])
        return cls(**data)

    def format_for_display(self) -> str:
        """Format for human-readable console display."""
        lines = []
        lines.append("=" * 70)
        lines.append(f"GOVERNANCE VIEW: {self.proposal_id}")
        lines.append(f"TITLE: {self.title}")
        lines.append("=" * 70)
        lines.append("")
        lines.append("SUMMARY:")
        lines.append(self.summary if self.summary else "No summary available")
        lines.append("")
        lines.append("WHY SURFACED:")
        lines.append(self.why_surfaced if self.why_surfaced else "No context available")
        lines.append("")
        if self.subsystem_impact:
            lines.append("SUBSYSTEM IMPACT:")
            for sub in self.subsystem_impact:
                lines.append(f"  - {sub}")
            lines.append("")
        if self.risk_effort:
            lines.append("RISK & EFFORT:")
            risk = self.risk_effort.get("risk_level", "unknown")
            effort = self.risk_effort.get("estimated_effort", 0)
            lines.append(f"  Risk Level: {risk}")
            lines.append(f"  Estimated Effort: {effort}")
            lines.append("")
        lines.append("FORECAST:")
        lines.append(f"  Confidence: {self.forecast_confidence:.0%}")
        if self.forecast_summary:
            lines.append(f"  Summary: {self.forecast_summary}")
        lines.append("")
        lines.append("PROOF GATE / EXECUTION ELIGIBILITY:")
        if self.execution_eligibility:
            eligibility = self.execution_eligibility.get("eligibility", "unknown")
            can_proceed = self.can_proceed
            lines.append(f"  Eligibility: {eligibility}")
            lines.append(f"  Can Proceed: {'Yes' if can_proceed else 'No'}")
            if self.blocking_reasons:
                lines.append("  Blocking Reasons:")
                for reason in self.blocking_reasons:
                    lines.append(f"    - {reason}")
        else:
            lines.append("  No proof gate data available")
        lines.append("")
        lines.append("REALIZATION PLAN:")
        if self.realization_plan_id:
            lines.append(f"  Plan ID: {self.realization_plan_id}")
            lines.append(f"  Status: {self.realization_status}")
            lines.append(f"  Current Phase: {self.current_phase}")
            if self.blockers:
                lines.append(f"  Blockers: {len(self.blockers)}")
        else:
            lines.append("  No realization plan yet")
        lines.append("")
        lines.append("AVAILABLE ACTIONS:")
        if self.available_actions:
            for action in self.available_actions:
                lines.append(f"  - {action}")
        else:
            lines.append("  No actions available")
        lines.append("")
        lines.append("RECOMMENDED ACTION:")
        lines.append(f"  {self.recommended_action.upper()}")
        if self.recommended_action_reason:
            lines.append(f"  Reason: {self.recommended_action_reason}")
        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)


class GovernanceAggregationEngine:
    """Aggregates all governance signals into one unified operator-facing view.
    
    Sources:
    - Narrative (why surfaced, subsystem impact, etc.)
    - Memory / Precedent context
    - Forecast
    - Comparison / Tradeoff context
    - Realization plan
    - Proof gate / Execution eligibility
    """
    
    def __init__(self, storage_path: Optional[Any] = None, gate: ExecutionGate = None):
        # Use provided gate or create new
        if gate is not None:
            self.gate = gate
            self.storage_path = gate.storage_path
        else:
            self.storage_path = storage_path
            self.gate = ExecutionGate(storage_path=storage_path)
        
        # Initialize aggregation engines
        self.forecast_engine = ForecastEngine()
        self.realization_engine = RealizationEngine(execution_gate=self.gate)
        self.proof_gate = ProofGateEngine(execution_gate=self.gate)
        self.operator_review = OperatorProposalReview(gate=self.gate)
    
    def get_governance_view(
        self,
        proposal_id: str,
        assessed_by: str = "operator",
    ) -> Optional[ProposalGovernanceView]:
        """Get unified governance view for a proposal.
        
        Aggregates:
        - Why it surfaced
        - Subsystem impact
        - Precedent / memory context
        - Forecast
        - Comparison / tradeoff context
        - Realization plan summary
        - Proof gate / execution eligibility
        - Blocking reasons
        - Approval / defer / deny context
        """
        # Get the proposal
        proposal = self.gate.get_proposal(proposal_id)
        if not proposal:
            return None
        
        # Get operator review output (narrative, audit history, etc.)
        review = self.operator_review.get_proposal_detail(proposal_id)
        if not review:
            # Create a minimal review output
            review = OperatorReviewOutput(
                proposal_id=proposal.proposal_id,
                title=proposal.title,
                description=proposal.description,
            )
        
        # Build governance view
        view = ProposalGovernanceView(
            proposal_id=proposal.proposal_id,
            title=proposal.title,
            description=proposal.description,
            summary=proposal.forecast_summary or "No forecast summary available",
            why_surfaced=proposal.rationale or "No rationale available",
            subsystem_impact=proposal.affected_subsystems,
            risk_effort={
                "risk_level": proposal.risk_level,
                "estimated_effort": proposal.estimated_effort,
            },
            forecast_summary=proposal.forecast_summary,
            forecast_confidence=proposal.calibration_confidence,
            approval_state=proposal.state,
            audit_history=proposal.audit_history,  # Already a list of dicts
            created_at=proposal.created_at,
            updated_at=proposal.updated_at,
        )
        
        # Get realization plan if available
        plan = self.realization_engine.build_realization_plan(proposal_id)
        if plan:
            view.realization_plan_id = plan.plan_id
            view.realization_status = plan.readiness_state
            view.realization_phases = plan.phases
            view.current_phase = plan.current_phase
            view.blockers = plan.blockers
        
        # Get proof gate / execution eligibility
        eligibility = self.proof_gate.get_execution_eligibility(
            plan_id=view.realization_plan_id or f"plan-{proposal_id.split('-')[-1]}",
            proposal_id=proposal_id,
        )
        view.execution_eligibility = eligibility
        view.proof_status = eligibility.get("proof_status", {})
        view.blocking_reasons = eligibility.get("blocking_reasons", [])
        view.can_proceed = eligibility.get("can_proceed", False)
        
        # Determine recommended action
        view.recommended_action = self._determine_recommended_action(view, proposal)
        view.recommended_action_reason = self._determine_action_reason(view, proposal)
        
        # Get tradeoff context
        view.tradeoff_context = self._get_tradeoff_context(proposal)
        
        # Get comparison with alternatives
        view.comparison_with_alternatives = self._get_comparison_context(proposal)
        
        # Update timestamp
        view.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        return view
    
    def _determine_recommended_action(
        self,
        view: ProposalGovernanceView,
        proposal: ChangeProposal,
    ) -> str:
        """Determine recommended operator action."""
        # Check execution eligibility
        if view.can_proceed:
            return "execute"
        elif view.approval_state == "approved":
            # Blocked but approved - need to address blockers
            return "blockers"
        elif view.approval_state in ["draft", "pending_review"]:
            return "review"
        else:
            return "defer"
    
    def _determine_action_reason(
        self,
        view: ProposalGovernanceView,
        proposal: ChangeProposal,
    ) -> str:
        """Determine reasoning for recommended action."""
        reasons = []
        
        if view.can_proceed:
            reasons.append("All proofs satisfied, risk bounded, ready for execution")
        else:
            if view.blocking_reasons:
                reasons.append(f"Blocking issues: {', '.join(view.blocking_reasons[:2])}")
            if view.execution_eligibility:
                eligibility = view.execution_eligibility.get("eligibility", "unknown")
                reasons.append(f"Eligibility status: {eligibility}")
            if proposal.risk_level == "high":
                reasons.append("High risk requires operator approval")
        
        return "; ".join(reasons)
    
    def _get_tradeoff_context(self, proposal: ChangeProposal) -> Optional[str]:
        """Get tradeoff context for the proposal."""
        if not proposal.expected_outcomes:
            return None
        
        # Get forecast for context
        try:
            forecast = self.forecast_engine.generate_forecast(
                proposal_id=proposal.proposal_id,
                description=proposal.description,
                expected_outcomes=proposal.expected_outcomes,
            )
            return forecast.forecast_summary
        except Exception:
            return None
    
    def _get_comparison_context(self, proposal: ChangeProposal) -> List[Dict[str, Any]]:
        """Get comparison context with alternative approaches."""
        comparisons = []
        
        # Get all proposals to compare with
        all_proposals = self.gate.get_all_proposals()
        
        for p in all_proposals:
            if p["proposal_id"] == proposal.proposal_id:
                continue
            if p["title"] == proposal.title and p["state"] == "approved":
                # Found a similar approved proposal
                comparisons.append({
                    "proposal_id": p["proposal_id"],
                    "title": p["title"],
                    "risk_level": p.get("risk_level", "unknown"),
                    "calibration_confidence": p.get("calibration_confidence", 0.0),
                    "outcome": "approved",
                })
        
        # Limit to top 3 comparisons
        return comparisons[:3]
    
    def format_governance_view(self, view: ProposalGovernanceView) -> str:
        """Format governance view for display."""
        return view.format_for_display()


def get_governance_view(
    proposal_id: str,
    assessed_by: str = "operator",
    storage_path: Optional[Any] = None,
) -> Optional[ProposalGovernanceView]:
    """Convenience function to get governance view."""
    engine = GovernanceAggregationEngine(storage_path=storage_path)
    return engine.get_governance_view(proposal_id, assessed_by)


def format_governance_view(view: ProposalGovernanceView) -> str:
    """Convenience function to format governance view."""
    return view.format_for_display()


if __name__ == "__main__":
    # CLI interface
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python governance_surface.py <command> [args]")
        print("Commands:")
        print("  view <proposal_id>")
        print("  list")
        sys.exit(1)
    
    command = sys.argv[1]
    engine = GovernanceAggregationEngine()
    
    if command == "view":
        if len(sys.argv) < 3:
            print("Usage: python governance_surface.py view <proposal_id>")
            sys.exit(1)
        proposal_id = sys.argv[2]
        view = engine.get_governance_view(proposal_id)
        if view:
            print(view.format_for_display())
        else:
            print(f"Proposal not found: {proposal_id}")
    
    elif command == "list":
        proposals = engine.operator_review.list_proposals()
        for p in proposals:
            print(f"- {p['proposal_id']}: {p['title']} ({p['state']})")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
