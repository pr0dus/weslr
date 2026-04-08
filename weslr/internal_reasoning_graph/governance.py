"""Internal Reasoning Graph Governance Engine

Governance engine for internal reasoning graph proposals.
Enforces strict approval requirements and audit trails.

Features:
  - Proposal lifecycle: DRAFT -> SUBMITTED -> REVIEWING -> APPROVED/REJECTED
  - Explicit review-gated transitions (operator approval required)
  - No automatic approval path
  - No automatic application path
  - Audit trail for all governance decisions
  - Read-only status queries (no silent mutation)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .models import Node, NodeFactory, ProposalStatus


class GovernanceAction(str, Enum):
    """Governance actions."""
    SUBMIT = "submit"
    START_REVIEW = "start_review"
    APPROVE = "approve"
    REJECT = "reject"
    MARK_PENDING = "mark_pending"


class GovernanceDecision(str, Enum):
    """Governance decisions."""
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"


@dataclass
class ProposalReviewRecord:
    """Record of a governance decision on a proposal."""
    proposal_id: str
    decision: GovernanceDecision
    _reviewer: str  # Internal field to avoid conflict with property
    timestamp: int
    notes: str = ""
    
    @property
    def reviewer(self) -> str:
        return self._reviewer
    
    @reviewer.setter
    def reviewer(self, value: str) -> None:
        self._reviewer = value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "reviewer": self.reviewer,
            "decision": self.decision.value,
            "timestamp": self.timestamp,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProposalReviewRecord:
        return cls(
            proposal_id=data["proposal_id"],
            decision=GovernanceDecision(data["decision"]),
            _reviewer=data.get("reviewer", data.get("reviewed_by", "")),
            timestamp=data["timestamp"],
            notes=data.get("notes", ""),
        )


@dataclass
class ProposalHistoryRecord:
    """Record of a status change in proposal lifecycle."""
    proposal_id: str
    timestamp: int
    status: str
    actor: str
    action: GovernanceAction
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "timestamp": self.timestamp,
            "status": self.status,
            "actor": self.actor,
            "action": self.action.value,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProposalHistoryRecord:
        return cls(
            proposal_id=data["proposal_id"],
            timestamp=data["timestamp"],
            status=data["status"],
            actor=data["actor"],
            action=GovernanceAction(data["action"]),
            notes=data.get("notes", ""),
        )


@dataclass
class GovernanceEngineState:
    """State of the governance engine."""
    enabled: bool = True
    require_operator_review: bool = True
    require_operator_approval: bool = True
    allow_auto_application: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "require_operator_review": self.require_operator_review,
            "require_operator_approval": self.require_operator_approval,
            "allow_auto_application": self.allow_auto_application,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GovernanceEngineState:
        return cls(
            enabled=data.get("enabled", True),
            require_operator_review=data.get("require_operator_review", True),
            require_operator_approval=data.get("require_operator_approval", True),
            allow_auto_application=data.get("allow_auto_application", False),
        )


class ProposalGovernanceEngine:
    """Governance engine for internal reasoning graph proposals.
    
    Enforces strict approval requirements and audit trails.
    All state transitions require explicit operator action.
    """
    
    def __init__(self, state: Optional[GovernanceEngineState] = None):
        self.state = state or GovernanceEngineState()
        self._review_records: List[ProposalReviewRecord] = []
        self._history_records: List[ProposalHistoryRecord] = []
    
    # =========================================================================
    # Proposal Lifecycle Management
    # =========================================================================
    
    def register_proposal(self, node: Node, actor: str = "system") -> Node:
        """Register a proposal - automatic, no operator approval needed.
        
        Only changes proposal status to SUBMITTED.
        """
        current_status = node.metadata.get("governance_status", ProposalStatus.PENDING.value)
        
        if current_status not in ["draft", ProposalStatus.PENDING.value]:
            raise ValueError(f"Cannot register proposal with status: {current_status}")
        
        # Update proposal status
        node.metadata["governance_status"] = ProposalStatus.PENDING.value
        node.status = "proposed"
        node.updated_at = int(time.time())
        
        # Record history
        record = ProposalHistoryRecord(
            proposal_id=node.id,
            timestamp=node.updated_at,
            status=node.metadata["governance_status"],
            actor=actor,
            action=GovernanceAction.SUBMIT,
            notes="Proposal registered and submitted for review",
        )
        self._history_records.append(record)
        
        return node
    
    def submit_for_review(self, proposal_id: str, reviewer: str, timestamp: Optional[int] = None) -> ProposalReviewRecord:
        """Submit a proposal for formal review - operator-triggered only.
        
        This is NOT automatic. Must be triggered by explicit operator action.
        Changes proposal status to REVIEWING.
        """
        if not self.state.require_operator_review:
            raise RuntimeError("Operator review not required by governance policy")
        
        if timestamp is None:
            timestamp = int(time.time())
        
        record = ProposalReviewRecord(
            proposal_id=proposal_id,
            decision=GovernanceDecision.PENDING,
            _reviewer=reviewer,
            timestamp=timestamp,
            notes="Formal review initiated by operator",
        )
        self._review_records.append(record)
        
        return record
    
    def approve_proposal(self, proposal_id: str, reviewer: str, notes: str = "", timestamp: Optional[int] = None) -> ProposalReviewRecord:
        """Approve a proposal - operator-triggered only.
        
        This is NOT automatic. Must be triggered by explicit operator action.
        """
        if not self.state.require_operator_approval:
            raise RuntimeError("Operator approval not required by governance policy")
        
        if timestamp is None:
            timestamp = int(time.time())
        
        record = ProposalReviewRecord(
            proposal_id=proposal_id,
            decision=GovernanceDecision.APPROVED,
            _reviewer=reviewer,
            timestamp=timestamp,
            notes=notes or "Proposal approved by operator",
        )
        self._review_records.append(record)
        
        # Record history
        history = ProposalHistoryRecord(
            proposal_id=proposal_id,
            timestamp=timestamp,
            status=ProposalStatus.APPROVED.value,
            actor=reviewer,
            action=GovernanceAction.APPROVE,
            notes=notes or "Proposal approved by operator",
        )
        self._history_records.append(history)
        
        return record
    
    def reject_proposal(self, proposal_id: str, reviewer: str, notes: str = "", timestamp: Optional[int] = None) -> ProposalReviewRecord:
        """Reject a proposal - operator-triggered only.
        
        This is NOT automatic. Must be triggered by explicit operator action.
        """
        if not self.state.require_operator_approval:
            raise RuntimeError("Operator approval not required by governance policy")
        
        if timestamp is None:
            timestamp = int(time.time())
        
        record = ProposalReviewRecord(
            proposal_id=proposal_id,
            decision=GovernanceDecision.REJECTED,
            _reviewer=reviewer,
            timestamp=timestamp,
            notes=notes or "Proposal rejected by operator",
        )
        self._review_records.append(record)
        
        # Record history
        history = ProposalHistoryRecord(
            proposal_id=proposal_id,
            timestamp=timestamp,
            status=ProposalStatus.REJECTED.value,
            actor=reviewer,
            action=GovernanceAction.REJECT,
            notes=notes or "Proposal rejected by operator",
        )
        self._history_records.append(history)
        
        return record
    
    # =========================================================================
    # Status Queries (Read-Only)
    # =========================================================================
    
    def get_proposal_status(self, proposal_id: str) -> str:
        """Get current status of a proposal - read-only query."""
        for record in reversed(self._history_records):
            if record.proposal_id == proposal_id:
                return record.status
        return ProposalStatus.PENDING.value
    
    def get_proposal_history(self, proposal_id: str) -> List[ProposalHistoryRecord]:
        """Get history of a proposal - read-only query."""
        return [r for r in self._history_records if r.proposal_id == proposal_id]
    
    def get_review_records(self, proposal_id: str) -> List[ProposalReviewRecord]:
        """Get review records for a proposal - read-only query."""
        return [r for r in self._review_records if r.proposal_id == proposal_id]
    
    def export_governance_summary(self) -> Dict[str, Any]:
        """Export governance summary - operator-readable + machine-readable."""
        return {
            "state": self.state.to_dict(),
            "review_count": len(self._review_records),
            "history_count": len(self._history_records),
            "review_records": [r.to_dict() for r in self._review_records],
            "history_records": [r.to_dict() for r in self._history_records],
        }
    
    # =========================================================================
    # Validation Methods
    # =========================================================================
    
    def can_submit_for_review(self, proposal_id: str) -> bool:
        """Check if proposal can be submitted for review."""
        status = self.get_proposal_status(proposal_id)
        return status == ProposalStatus.PENDING.value
    
    def can_approve(self, proposal_id: str) -> bool:
        """Check if proposal can be approved."""
        status = self.get_proposal_status(proposal_id)
        return status == GovernanceDecision.PENDING.value or status == ProposalStatus.REVIEWING.value
    
    def can_reject(self, proposal_id: str) -> bool:
        """Check if proposal can be rejected."""
        status = self.get_proposal_status(proposal_id)
        return status == GovernanceDecision.PENDING.value or status == ProposalStatus.REVIEWING.value
    
    def can_apply(self, proposal_id: str) -> bool:
        """Check if proposal can be applied - always requires explicit command."""
        # Application is never automatic per governance policy
        return False
    
    # =========================================================================
    # Internal Methods
    # =========================================================================
    
    def _update_proposal_status(self, proposal_id: str, new_status: str, actor: str, action: GovernanceAction) -> None:
        """Internal method to update proposal status."""
        timestamp = int(time.time())
        record = ProposalHistoryRecord(
            proposal_id=proposal_id,
            timestamp=timestamp,
            status=new_status,
            actor=actor,
            action=action,
        )
        self._history_records.append(record)
