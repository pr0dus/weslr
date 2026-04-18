from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from weslr.apply_staging_log import list_staging

STORAGE_EXECUTION = Path(__file__).resolve().parent.parent / "weslr_execute_readiness.jsonl"
STORAGE_EXECUTION.parent.mkdir(exist_ok=True)
ALLOWED_STATUS = "staged_for_apply_review"


def _write_record(record: Dict[str, Any]) -> None:
    with STORAGE_EXECUTION.open("a", encoding="utf-8") as fd:
        fd.write(json.dumps(record, ensure_ascii=False) + "\n")


def _load_existing() -> List[Dict[str, Any]]:
    if not STORAGE_EXECUTION.exists():
        return []
    results: List[Dict[str, Any]] = []
    with STORAGE_EXECUTION.open("r", encoding="utf-8") as fd:
        for line in fd:
            line = line.strip()
            if line:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return results


def stage_execution(
    staging_id: str,
    final_operator_confirmation: bool,
    execution_scope: str,
    execution_reason: str,
    rollback_available: bool,
    now: datetime | None = None,
) -> Dict[str, Any]:
    record = next((s for s in list_staging() if s.get("staging_id") == staging_id), None)
    if not record:
        raise ValueError(f"Staging record not found: {staging_id}")
    status = record.get("staging_status")
    if status != ALLOWED_STATUS:
        raise ValueError("Staging record is not eligible for execution readiness")
    execution_status = "ready_for_apply_execution" if final_operator_confirmation else "blocked"
    eligibility = {
        "execution_id": f"execution_{uuid.uuid4().hex[:8]}",
        "timestamp": (now or datetime.utcnow()).replace(microsecond=0).isoformat() + "Z",
        "staging_id": staging_id,
        "proposal_id": record.get("proposal_id"),
        "final_operator_confirmation": final_operator_confirmation,
        "execution_scope": execution_scope,
        "execution_reason": execution_reason,
        "execution_status": execution_status,
        "rollback_available": rollback_available,
        "trigger_id": record.get("trigger_id"),
        "category": record.get("category"),
        "lineage_ref": record.get("lineage_ref"),
    }
    _write_record(eligibility)
    return eligibility


def list_execution_readiness() -> List[Dict[str, Any]]:
    return _load_existing()
