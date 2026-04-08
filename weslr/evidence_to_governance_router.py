"""Evidence-to-Governance Router - Phase C

Evidence-to-governance routing for internal reasoning graph proposals.
Routes evidence-backed proposal payloads into governed candidate registration,
preserving explicit operator review and preventing any auto-approval/auto-application.

Phase C scope:
- EvidenceToGovernanceRouter: Route evidence payloads into governed proposals
- RoutingStatus: Status tracking (GENERATED, REGISTERED, REVIEWING, APPROVED, REJECTED)
- RoutingRecord: Audit trail for routing decisions
- EvidenceProposalWithRouting: Extended payload with routing status

Constraints:
- No execution/application logic (deferred to Phase D)
- No automatic review start (requires operator trigger)
- No automatic approval (requires operator trigger)
- No governance module modification (adapter-style integration)
- No hidden self-application
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .internal_reasoning_graph.governance import (
    ProposalGovernanceEngine,
    GovernanceDecision,
    GovernanceAction,
)
from .internal_reasoning_graph.proposal_workflow import WorkflowState, ProposalWorkflow
from .evidence_intake.models import EvidenceProposalPayload, RoutingStatus
from .evidence_intake.evidence_to_candidate import ProposalPayloadWithCandidate, CandidateProvenance


class RoutingAction(str, Enum):
    """Routing actions."""
    ROUTE = "route"
    SUBMIT_FOR_REVIEW = "submit_for_review"
    APPROVE = "approve"
    REJECT = "reject"


class RoutingState(str, Enum):
    """Routing state."""
    GENERATED = "generated"
    REGISTERED = "registered"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class RoutingRecord:
    """Record of a routing state transition."""
    proposal_id: str
    timestamp: int
    from_status: RoutingState
    to_status: RoutingState
    actor: str
    action: RoutingAction
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "timestamp": self.timestamp,
            "from_status": self.from_status.value,
            "to_status": self.to_status.value,
            "actor": self.actor,
            "action": self.action.value,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RoutingRecord":
        return cls(
            proposal_id=data["proposal_id"],
            timestamp=data["timestamp"],
            from_status=RoutingState(data["from_status"]),
            to_status=RoutingState(data["to_status"]),
            actor=data["actor"],
            action=RoutingAction(data["action"]),
            notes=data.get("notes", ""),
        )


@dataclass
class EvidenceProposalWithRouting:
    """Extended proposal payload with routing status.
    
    This extends EvidenceProposalPayload with routing status tracking,
    preserving the review-gated workflow - no auto-application.
    """
    evidence_id: str
    claim_text: str
    source_summary: str
    confidence: Optional[float] = None
    status: str = "DRAFT"
    routing_status: str = RoutingStatus.GENERATED.value
    
    # Candidate-specific fields (provisional references)
    candidate_reference: Optional[str] = None
    candidate_node_type: Optional[str] = None
    candidate_provenance: Optional[CandidateProvenance] = None
    candidate_confidence: Optional[float] = None
    candidate_recency: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "evidence_id": self.evidence_id,
            "claim_text": self.claim_text,
            "source_summary": self.source_summary,
            "confidence": self.confidence,
            "status": self.status,
            "routing_status": self.routing_status,
            "candidate_reference": self.candidate_reference,
            "candidate_node_type": self.candidate_node_type,
            "candidate_confidence": self.candidate_confidence,
            "candidate_recency": self.candidate_recency,
        }
        if self.candidate_provenance:
            data["candidate_provenance"] = self.candidate_provenance.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceProposalWithRouting":
        candidate_provenance = None
        if data.get("candidate_provenance"):
            candidate_provenance = CandidateProvenance.from_dict(data["candidate_provenance"])
        
        return cls(
            evidence_id=data.get("evidence_id", ""),
            claim_text=data.get("claim_text", ""),
            source_summary=data.get("source_summary", ""),
            confidence=data.get("confidence"),
            status=data.get("status", "DRAFT"),
            routing_status=data.get("routing_status", RoutingStatus.GENERATED.value),
            candidate_reference=data.get("candidate_reference"),
            candidate_node_type=data.get("candidate_node_type"),
            candidate_confidence=data.get("candidate_confidence"),
            candidate_recency=data.get("candidate_recency"),
            candidate_provenance=candidate_provenance,
        )
    
    @classmethod
    def from_payload(cls, payload: EvidenceProposalPayload) -> "EvidenceProposalWithRouting":
        """Create EvidenceProposalWithRouting from EvidenceProposalPayload."""
        return cls(
            evidence_id=payload.evidence_id,
            claim_text=payload.claim_text,
            source_summary=payload.source_summary,
            confidence=payload.confidence,
            status=payload.status,
            routing_status=RoutingStatus.GENERATED.value,
        )
    
    @classmethod
    def from_payload_with_candidate(cls, payload: ProposalPayloadWithCandidate) -> "EvidenceProposalWithRouting":
        """Create EvidenceProposalWithRouting from ProposalPayloadWithCandidate."""
        return cls(
            evidence_id=payload.evidence_id,
            claim_text=payload.claim_text,
            source_summary=payload.source_summary,
            confidence=payload.confidence,
            status=payload.status,
            routing_status=payload.routing_status,
            candidate_reference=payload.candidate_reference,
            candidate_node_type=payload.candidate_node_type,
            candidate_confidence=payload.candidate_confidence,
            candidate_recency=payload.candidate_recency,
            candidate_provenance=payload.candidate_provenance,
        )


class EvidenceToGovernanceRouter:
    """Evidence-to-governance router.
    
    Routes evidence-backed proposal payloads into governed proposal workflow,
    preserving explicit operator review and preventing any auto-approval/auto-application.
    """
    
    def __init__(
        self,
        governance_engine: Optional[ProposalGovernanceEngine] = None,
        proposal_workflow: Optional[ProposalWorkflow] = None,
    ):
        self.governance = governance_engine or ProposalGovernanceEngine()
        self.proposal_workflow = proposal_workflow or ProposalWorkflow(
            governance_engine=self.governance,
        )
        
        self._routing_records: List[RoutingRecord] = []
        self._routing_states: Dict[str, Dict[str, Any]] = {}
    
    # =========================================================================
    # Routing Methods
    # =========================================================================
    
    def route_evidence_to_registered(
        self,
        payload: EvidenceProposalPayload,
        actor: str = "system",
    ) -> EvidenceProposalWithRouting:
        """Route evidence payload to registered state - automatic.
        
        Creates EvidenceProposalWithRouting with REGISTERED status.
        Does NOT trigger review - must be triggered by explicit operator action.
        """
        routing_payload = EvidenceProposalWithRouting.from_payload(payload)
        routing_payload.routing_status = RoutingState.REGISTERED.value
        
        # Record routing
        record = RoutingRecord(
            proposal_id=payload.evidence_id,
            timestamp=int(time.time()),
            from_status=RoutingState.GENERATED,
            to_status=RoutingState.REGISTERED,
            actor=actor,
            action=RoutingAction.ROUTE,
            notes="Evidence payload routed to registered state",
        )
        self._routing_records.append(record)
        self._routing_states[payload.evidence_id] = {
            "routing_status": RoutingState.REGISTERED.value,
            "created_at": record.timestamp,
        }
        
        return routing_payload
    
    def submit_for_review(
        self,
        proposal_id: str,
        reviewer: str,
    ) -> RoutingRecord:
        """Submit a proposal for formal review - operator-triggered only.
        
        This is NOT automatic. Must be triggered by explicit operator action.
        """
        if proposal_id not in self._routing_states:
            raise ValueError(f"Unknown proposal: {proposal_id}")
        
        current_status = self._routing_states[proposal_id]["routing_status"]
        if current_status != RoutingState.REGISTERED.value:
            raise ValueError(f"Cannot submit for review from status: {current_status}")
        
        # Transition to REVIEWING
        timestamp = int(time.time())
        self._routing_states[proposal_id]["routing_status"] = RoutingState.REVIEWING.value
        
        # Use governance engine to track review start
        review_record = self.governance.submit_for_review(proposal_id, reviewer, timestamp)
        
        # Record routing transition
        record = RoutingRecord(
            proposal_id=proposal_id,
            timestamp=timestamp,
            from_status=RoutingState.REGISTERED,
            to_status=RoutingState.REVIEWING,
            actor=reviewer,
            action=RoutingAction.SUBMIT_FOR_REVIEW,
            notes="Formal review initiated by operator",
        )
        self._routing_records.append(record)
        
        return record
    
    def approve_proposal(
        self,
        proposal_id: str,
        reviewer: str,
        notes: str = "",
    ) -> RoutingRecord:
        """Approve a proposal - operator-triggered only.
        
        This is NOT automatic. Must be triggered by explicit operator action.
        """
        if proposal_id not in self._routing_states:
            raise ValueError(f"Unknown proposal: {proposal_id}")
        
        current_status = self._routing_states[proposal_id]["routing_status"]
        if current_status not in [RoutingState.REGISTERED.value, RoutingState.REVIEWING.value]:
            raise ValueError(f"Cannot approve from status: {current_status}")
        
        # Transition to APPROVED
        timestamp = int(time.time())
        self._routing_states[proposal_id]["routing_status"] = RoutingState.APPROVED.value
        
        # Use governance engine to approve
        review_record = self.governance.approve_proposal(proposal_id, reviewer, notes, timestamp)
        
        # Record routing transition
        record = RoutingRecord(
            proposal_id=proposal_id,
            timestamp=timestamp,
            from_status=RoutingState.REVIEWING,
            to_status=RoutingState.APPROVED,
            actor=reviewer,
            action=RoutingAction.APPROVE,
            notes=notes or "Proposal approved by operator",
        )
        self._routing_records.append(record)
        
        return record
    
    def reject_proposal(
        self,
        proposal_id: str,
        reviewer: str,
        notes: str = "",
    ) -> RoutingRecord:
        """Reject a proposal - operator-triggered only.
        
        This is NOT automatic. Must be triggered by explicit operator action.
        """
        if proposal_id not in self._routing_states:
            raise ValueError(f"Unknown proposal: {proposal_id}")
        
        current_status = self._routing_states[proposal_id]["routing_status"]
        if current_status not in [RoutingState.REGISTERED.value, RoutingState.REVIEWING.value]:
            raise ValueError(f"Cannot reject from status: {current_status}")
        
        # Transition to REJECTED
        timestamp = int(time.time())
        self._routing_states[proposal_id]["routing_status"] = RoutingState.REJECTED.value
        
        # Use governance engine to reject
        review_record = self.governance.reject_proposal(proposal_id, reviewer, notes, timestamp)
        
        # Record routing transition
        record = RoutingRecord(
            proposal_id=proposal_id,
            timestamp=timestamp,
            from_status=RoutingState.REVIEWING,
            to_status=RoutingState.REJECTED,
            actor=reviewer,
            action=RoutingAction.REJECT,
            notes=notes or "Proposal rejected by operator",
        )
        self._routing_records.append(record)
        
        return record
    
    # =========================================================================
    # Status Queries (Read-Only)
    # =========================================================================
    
    def get_routing_status(self, proposal_id: str) -> str:
        """Get current routing status for a proposal - read-only query."""
        if proposal_id not in self._routing_states:
            return RoutingState.GENERATED.value
        return self._routing_states[proposal_id]["routing_status"]
    
    def get_routing_history(self, proposal_id: str) -> List[RoutingRecord]:
        """Get routing history for a proposal - read-only query."""
        return [r for r in self._routing_records if r.proposal_id == proposal_id]
    
    def get_routing_records(self, proposal_id: str) -> List[RoutingRecord]:
        """Get routing records for a proposal - read-only query."""
        return self.get_routing_history(proposal_id)
    
    def export_routing_summary(self, proposal_id: str) -> Dict[str, Any]:
        """Export routing summary - operator-readable + machine-readable."""
        if proposal_id not in self._routing_states:
            return {
                "proposal_id": proposal_id,
                "routing_status": RoutingState.GENERATED.value,
                "routing_history": [],
            }
        
        status = self._routing_states[proposal_id]["routing_status"]
        history = self.get_routing_history(proposal_id)
        
        return {
            "proposal_id": proposal_id,
            "routing_status": status,
            "created_at": self._routing_states[proposal_id].get("created_at"),
            "routing_history": [r.to_dict() for r in history],
        }
    
    def export_all_routing(self) -> Dict[str, Any]:
        """Export all routing - operator-readable + machine-readable."""
        routings = {}
        for proposal_id, state in self._routing_states.items():
            routings[proposal_id] = {
                "routing_status": state["routing_status"],
                "created_at": state.get("created_at"),
            }
        
        return {
            "routings": routings,
            "total_count": len(routings),
            "count_by_status": self._count_by_status(),
        }
    
    def _count_by_status(self) -> Dict[str, int]:
        """Count routings by status - internal helper."""
        counts: Dict[str, int] = {}
        for state in self._routing_states.values():
            status = state["routing_status"]
            counts[status] = counts.get(status, 0) + 1
        return counts
    
    # =========================================================================
    # Validation Methods
    # =========================================================================
    
    def can_submit_for_review(self, proposal_id: str) -> bool:
        """Check if proposal can be submitted for review."""
        if proposal_id not in self._routing_states:
            return False
        return self._routing_states[proposal_id]["routing_status"] == RoutingState.REGISTERED.value
    
    def can_approve(self, proposal_id: str) -> bool:
        """Check if proposal can be approved."""
        if proposal_id not in self._routing_states:
            return False
        status = self._routing_states[proposal_id]["routing_status"]
        return status in [RoutingState.REGISTERED.value, RoutingState.REVIEWING.value]
    
    def can_reject(self, proposal_id: str) -> bool:
        """Check if proposal can be rejected."""
        if proposal_id not in self._routing_states:
            return False
        status = self._routing_states[proposal_id]["routing_status"]
        return status in [RoutingState.REGISTERED.value, RoutingState.REVIEWING.value]
    
    def can_apply(self, proposal_id: str) -> bool:
        """Check if proposal can be applied - always requires explicit command.
        
        Note: Application is NOT part of Phase C. Always returns False.
        """
        # Application is deferred to Phase D
        return False
