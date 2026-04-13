from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

from weslr.inadequacy_intake import STORAGE_INTAKE, _load_jsonl as _load_intakes

STORAGE_DECISIONS = Path(__file__).resolve().parent.parent / "weslr_cdi_decisions.jsonl"
STORAGE_DECISIONS.parent.mkdir(exist_ok=True)
ALLOWED_ACTIONS = {
    "approve_for_proposal": "approved_for_cdi_proposal",
    "hold": "held",
    "deny": "denied",
    "request_more_evidence": "needs_more_evidence",
    "refine_threshold_rule": "threshold_refinement_requested",
}


def _write_record(record: Dict[str, Any]) -> None:
    with STORAGE_DECISIONS.open("a", encoding="utf-8") as fd:
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
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            results.append(payload)
    return results


def _load_existing_decisions() -> Set[str]:
    return {record.get("intake_id") for record in _load_jsonl(STORAGE_DECISIONS) if record.get("intake_id")}


def _find_intake(intake_id: str) -> Dict[str, Any] | None:
    for intake in _load_jsonl(STORAGE_INTAKE):
        if intake.get("intake_id") == intake_id:
            return intake
    return None


def create_decision(
    intake_id: str,
    operator_action: str,
    decision_reason: str,
    operator_notes: str,
    now: datetime | None = None,
) -> Dict[str, Any]:
    if operator_action not in ALLOWED_ACTIONS:
        raise ValueError(f"Unsupported operator_action: {operator_action}")
    intake = _find_intake(intake_id)
    if not intake:
        raise ValueError(f"Intake not found: {intake_id}")
    existing = _load_existing_decisions()
    if intake_id in existing and operator_action == "approve_for_proposal":
        raise ValueError("Intake already has decisions; append additional decisions instead of duplicate approval")
    status = ALLOWED_ACTIONS[operator_action]
    decision = {
        "decision_id": f"decision_{uuid.uuid4().hex[:8]}",
        "timestamp": (now or datetime.utcnow()).replace(microsecond=0).isoformat() + "Z",
        "intake_id": intake_id,
        "operator_action": operator_action,
        "decision_reason": decision_reason,
        "operator_notes": operator_notes,
        "decision_status": status,
        "trigger_id": intake.get("trigger_id"),
        "category": intake.get("category"),
        "readiness_for_CDI": intake.get("readiness_for_CDI"),
        "lineage_ref": intake.get("lineage_ref"),
        "evidence_refs": intake.get("evidence_refs", []),
    }
    _write_record(decision)
    return decision


def list_decisions() -> List[Dict[str, Any]]:
    return _load_jsonl(STORAGE_DECISIONS)
