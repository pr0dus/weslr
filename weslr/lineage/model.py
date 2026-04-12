from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

# Optional import guard to avoid hard dependency when converting existing proposals
try:  # pragma: no cover - optional dependency
    from weslr.change_proposals import ChangeProposal  # type: ignore
except Exception:  # pragma: no cover
    ChangeProposal = None  # type: ignore


class Status(Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    SUPERSEDED = "superseded"


@dataclass(frozen=True)
class LineageOrigin:
    proposal_id: str
    source_loop_id: str
    workspace_id: str
    user_id: str
    trigger_reason: str
    originating_evidence_signal: str
    timestamp: str  # RFC3339
    confidence: float
    linked_checkpoint: str

    @staticmethod
    def from_change_proposal(
        proposal: "ChangeProposal" | object,
        *,
        workspace_id: str,
        user_id: str,
        trigger_reason: str,
        originating_evidence_signal: str,
        linked_checkpoint: str,
        confidence: Optional[float] = None,
    ) -> "LineageOrigin":
        """Map an existing proposal record to a lineage origin, reusing IDs/timestamps.

        - proposal_id and created_at are reused (no duplication of identifiers or time).
        - confidence defaults to proposal.evidence_confidence when available.
        - workspace_id/user_id/trigger/evidence/checkpoint are provided by caller to maintain scope.
        """

        pid = getattr(proposal, "proposal_id", None) or getattr(proposal, "id", None)
        created = getattr(proposal, "created_at", None) or getattr(proposal, "timestamp", None)
        prop_conf = getattr(proposal, "evidence_confidence", None)

        if pid is None or created is None:
            raise ValueError("proposal must provide proposal_id and created_at/timestamp")

        use_confidence = confidence if confidence is not None else (prop_conf if prop_conf is not None else 0.0)

        return LineageOrigin(
            proposal_id=str(pid),
            source_loop_id=getattr(proposal, "source_scenario", "unknown"),
            workspace_id=workspace_id,
            user_id=user_id,
            trigger_reason=trigger_reason,
            originating_evidence_signal=originating_evidence_signal,
            timestamp=str(created),
            confidence=float(use_confidence),
            linked_checkpoint=linked_checkpoint,
        )


@dataclass(frozen=True)
class AuditEntry:
    proposal_id: str
    action: str  # view | export | status_change
    actor: str
    timestamp: str  # RFC3339
    context: Optional[str] = None


@dataclass(frozen=True)
class StatusEntry:
    proposal_id: str
    from_status: Optional[Status]
    to_status: Status
    actor: str
    timestamp: str  # RFC3339
    note: Optional[str] = None


@dataclass
class LineageRecord:
    origin: LineageOrigin
    current_status: Status
    status_history: List[StatusEntry] = field(default_factory=list)
    audit_log: List[AuditEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "origin": self.origin.__dict__,
            "current_status": self.current_status.value,
            "status_history": [
                {
                    "proposal_id": e.proposal_id,
                    "from_status": e.from_status.value if e.from_status else None,
                    "to_status": e.to_status.value,
                    "actor": e.actor,
                    "timestamp": e.timestamp,
                    "note": e.note,
                }
                for e in self.status_history
            ],
            "audit_log": [
                {
                    "proposal_id": a.proposal_id,
                    "action": a.action,
                    "actor": a.actor,
                    "timestamp": a.timestamp,
                    "context": a.context,
                }
                for a in self.audit_log
            ],
        }
