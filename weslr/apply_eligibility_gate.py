from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

STORAGE_REVIEWS = Path(__file__).resolve().parent.parent / "weslr_governance_reviews.jsonl"
STORAGE_ELIGIBILITY = Path(__file__).resolve().parent.parent / "weslr_apply_eligibility.jsonl"
STORAGE_ELIGIBILITY.parent.mkdir(exist_ok=True)
ELIGIBLE_STATUSES = {"approved_for_execution_eligibility"}
BLOCKED_STATUSES = {"held", "denied", "needs_more_evidence", "threshold_adjustment_requested"}


def _write_record(record: Dict[str, Any]) -> None:
    with STORAGE_ELIGIBILITY.open("a", encoding="utf-8") as fd:
        fd.write(json.dumps(record, ensure_ascii=False) + "\n")


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    results: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fd:
        for line in fd:
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return results


def _load_existing() -> set[str]:
    return {record.get("review_id") for record in _load_jsonl(STORAGE_ELIGIBILITY) if record.get("review_id")}


def build_eligibility(now: datetime | None = None) -> List[Dict[str, Any]]:
    now = now or datetime.utcnow()
    reviews = _load_jsonl(STORAGE_REVIEWS)
    existing = _load_existing()
    entries: List[Dict[str, Any]] = []

    for review in reviews:
        review_id = review.get("review_id")
        if not review_id or review_id in existing:
            continue
        status = review.get("review_status")
        if status in ELIGIBLE_STATUSES:
            eligibility_status = "eligible_for_future_apply_review"
            reason = "approved_by_governance"
        elif status in BLOCKED_STATUSES:
            eligibility_status = "blocked"
            reason = "governance_block"
        else:
            eligibility_status = "needs_additional_governance"
            reason = "unhandled_status"
        record = {
            "eligibility_id": f"eligibility_{uuid.uuid4().hex[:8]}",
            "timestamp": now.replace(microsecond=0).isoformat() + "Z",
            "proposal_id": review.get("proposal_id"),
            "review_id": review_id,
            "eligibility_reason": reason,
            "eligibility_status": eligibility_status,
            "trigger_id": review.get("trigger_id"),
            "category": review.get("category"),
            "lineage_ref": review.get("lineage_ref"),
        }
        _write_record(record)
        entries.append(record)
        existing.add(review_id)
    return entries


def list_eligibility() -> List[Dict[str, Any]]:
    return _load_jsonl(STORAGE_ELIGIBILITY)
