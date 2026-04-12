from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


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
