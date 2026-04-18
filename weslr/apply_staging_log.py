from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from weslr.apply_eligibility_gate import list_eligibility

STORAGE_STAGING = Path(__file__).resolve().parent.parent / "weslr_apply_staging.jsonl"
STORAGE_STAGING.parent.mkdir(exist_ok=True)
ALLOWED_STATUS = "eligible_for_future_apply_review"
BLOCKED_STATUS = {"blocked", "needs_additional_governance"}


def _write_record(record: Dict[str, Any]) -> None:
    with STORAGE_STAGING.open("a", encoding="utf-8") as fd:
        fd.write(json.dumps(record, ensure_ascii=False) + "\n")


def _load_existing() -> List[Dict[str, Any]]:
    if not STORAGE_STAGING.exists():
        return []
    records: List[Dict[str, Any]] = []
    with STORAGE_STAGING.open("r", encoding="utf-8") as fd:
        for line in fd:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def stage_eligible(now: datetime | None = None) -> List[Dict[str, Any]]:
    now = now or datetime.utcnow()
    existing = {record.get("eligibility_id") for record in _load_existing() if record.get("eligibility_id")}
    staging: List[Dict[str, Any]] = []

    for eligibility in list_eligibility():
        ident = eligibility.get("eligibility_id")
        if not ident or ident in existing:
            continue
        status = eligibility.get("eligibility_status")
        if status == ALLOWED_STATUS:
            staging_status = "staged_for_apply_review"
            requires_final_operator_confirmation = True
            reason = "eligible_by_governance"
        elif status in BLOCKED_STATUS:
            staging_status = "blocked"
            requires_final_operator_confirmation = False
            reason = "blocked_by_eligibility"
        else:
            staging_status = "awaiting_final_confirmation"
            requires_final_operator_confirmation = True
            reason = "pending_governance"
        record = {
            "staging_id": f"staging_{uuid.uuid4().hex[:8]}",
            "timestamp": now.replace(microsecond=0).isoformat() + "Z",
            "proposal_id": eligibility.get("proposal_id"),
            "eligibility_id": ident,
            "staging_reason": reason,
            "staging_status": staging_status,
            "requires_final_operator_confirmation": requires_final_operator_confirmation,
            "trigger_id": eligibility.get("trigger_id"),
            "category": eligibility.get("category"),
            "lineage_ref": eligibility.get("lineage_ref"),
        }
        _write_record(record)
        staging.append(record)
        existing.add(ident)
    return staging


def list_staging() -> List[Dict[str, Any]]:
    return _load_existing()
