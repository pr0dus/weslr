from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

STORAGE_PROPOSALS = Path(__file__).resolve().parent.parent / "weslr_cdi_proposals.jsonl"
STORAGE_REVIEWS = Path(__file__).resolve().parent.parent / "weslr_governance_reviews.jsonl"
STORAGE_REVIEWS.parent.mkdir(exist_ok=True)
ALLOWED_ACTIONS = {
    "approved_for_execution_eligibility": "approved_for_execution_eligibility",
    "held_for_refinement": "held",
    "denied": "denied",
    "needs_more_evidence": "needs_more_evidence",
    "needs_threshold_adjustment": "threshold_adjustment_requested",
}


def _write_record(record: Dict[str, Any]) -> None:
    with STORAGE_REVIEWS.open("a", encoding="utf-8") as fd:
        fd.write(json.dumps(record, ensure_ascii=False) + "\n")


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fd:
        for line in fd:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def _find_proposal(proposal_id: str) -> Dict[str, Any] | None:
    for proposal in _load_jsonl(STORAGE_PROPOSALS):
        if proposal.get("proposal_id") == proposal_id:
            return proposal
    return None


def create_review(
    proposal_id: str,
    review_action: str,
    review_reason: str,
    review_notes: str,
    now: datetime | None = None,
) -> Dict[str, Any]:
    if review_action not in ALLOWED_ACTIONS:
        raise ValueError(f"Unsupported review_action: {review_action}")
    proposal = _find_proposal(proposal_id)
    if not proposal:
        raise ValueError(f"Proposal not found: {proposal_id}")
    status = ALLOWED_ACTIONS[review_action]
    record = {
        "review_id": f"review_{uuid.uuid4().hex[:8]}",
        "timestamp": (now or datetime.utcnow()).replace(microsecond=0).isoformat() + "Z",
        "proposal_id": proposal_id,
        "review_action": review_action,
        "review_reason": review_reason,
        "review_notes": review_notes,
        "review_status": status,
        "trigger_id": proposal.get("trigger_id"),
        "category": proposal.get("category"),
        "governance_status": proposal.get("governance_status"),
        "lineage_ref": proposal.get("lineage_ref"),
        "evidence_refs": proposal.get("evidence_refs", []),
    }
    _write_record(record)
    return record


def list_reviews() -> List[Dict[str, Any]]:
    return _load_jsonl(STORAGE_REVIEWS)
