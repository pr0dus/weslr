"""
weslr/weight_proposal.py

Governed proposal flow for cognitive weight changes.
Proposals are created from observations but NOT applied automatically.
Operator approval required before any weight update.

Proposal states: proposed → approved → applied
                 proposed → rejected  (never applied)
                 applied → reverted
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Literal
from datetime import datetime, timezone
import json
import os
import uuid

PROPOSAL_DEFAULT_PATH = os.path.expanduser("~/.weslr/weight_proposals.jsonl")
PROJECT_PROPOSAL_PATH = ".weslr_state/weight_proposals.jsonl"

# ── Status ─────────────────────────────────────────────────────────────────

ProposalStatus = Literal[
    "proposed",
    "approved",
    "rejected",
    "applied",
    "reverted",
]

# ── Dataclass ──────────────────────────────────────────────────────────────

@dataclass
class WeightUpdateProposal:
    proposal_id: str
    created_at: str
    updated_at: str
    weight_key: str
    old_value: float
    proposed_value: float
    delta: float
    reason: str
    supporting_observations: list[str]  # observation IDs
    expected_benefit: str
    possible_risk: str
    tests_to_run: list[str]
    status: ProposalStatus
    decided_by: Optional[str] = None
    decided_at: Optional[str] = None
    notes: Optional[str] = None

    def dict(self) -> dict:
        return asdict(self)

    @classmethod
    def create(
        cls,
        weight_key: str,
        old_value: float,
        proposed_value: float,
        reason: str,
        supporting_observations: list[str],
        expected_benefit: str,
        possible_risk: str,
        tests_to_run: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> "WeightUpdateProposal":
        now = _now_iso()
        return cls(
            proposal_id=str(uuid.uuid4())[:8],
            created_at=now,
            updated_at=now,
            weight_key=weight_key,
            old_value=old_value,
            proposed_value=proposed_value,
            delta=proposed_value - old_value,
            reason=reason,
            supporting_observations=supporting_observations,
            expected_benefit=expected_benefit,
            possible_risk=possible_risk,
            tests_to_run=tests_to_run or [],
            status="proposed",
            notes=notes,
        )

    def approve(self, decided_by: str = "operator") -> None:
        self.status = "approved"
        self.decided_by = decided_by
        self.decided_at = _now_iso()

    def reject(self, decided_by: str = "operator") -> None:
        self.status = "rejected"
        self.decided_by = decided_by
        self.decided_at = _now_iso()

    def mark_applied(self) -> None:
        self.status = "applied"
        self.updated_at = _now_iso()

    def mark_reverted(self) -> None:
        self.status = "reverted"
        self.updated_at = _now_iso()


# ── Storage ─────────────────────────────────────────────────────────────────

def proposals_path(path: Optional[str] = None) -> str:
    if path:
        return path
    if os.path.exists(PROJECT_PROPOSAL_PATH):
        return PROJECT_PROPOSAL_PATH
    return PROPOSAL_DEFAULT_PATH


def save_proposal(proposal: WeightUpdateProposal, path: Optional[str] = None) -> None:
    p = proposals_path(path)
    os.makedirs(os.path.dirname(p) if os.path.dirname(p) else ".", exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps(proposal.dict()) + "\n")


def load_proposals(status: Optional[ProposalStatus] = None, limit: int = 100,
                   path: Optional[str] = None) -> list[WeightUpdateProposal]:
    """Load proposals, optionally filtered by status (newest first)."""
    p = proposals_path(path)
    if not os.path.exists(p):
        return []
    proposals: list[WeightUpdateProposal] = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                proposal = WeightUpdateProposal(**d)
                if status is None or proposal.status == status:
                    proposals.append(proposal)
            except Exception:
                continue
            if len(proposals) >= limit:
                break
    proposals.reverse()  # newest first
    return proposals


def update_proposal_status(proposal_id: str, new_status: ProposalStatus,
                           decided_by: str = "operator",
                           path: Optional[str] = None) -> bool:
    """Update the status of a proposal by ID. Rewrites file."""
    p = proposals_path(path)
    if not os.path.exists(p):
        return False
    proposals = load_proposals(limit=10000, path=path)
    updated = False
    for proposal in proposals:
        if proposal.proposal_id == proposal_id:
            proposal.status = new_status
            proposal.decided_by = decided_by
            proposal.decided_at = _now_iso()
            updated = True
            break
    if not updated:
        return False
    with open(p, "w") as f:
        for proposal in proposals:
            f.write(json.dumps(proposal.dict()) + "\n")
    return True


# ── Helper ───────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
