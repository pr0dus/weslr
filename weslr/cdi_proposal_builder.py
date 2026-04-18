from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set

STORAGE_DECISIONS = Path(__file__).resolve().parent.parent / "weslr_cdi_decisions.jsonl"
STORAGE_PROPOSALS = Path(__file__).resolve().parent.parent / "weslr_cdi_proposals.jsonl"
STORAGE_PROPOSALS.parent.mkdir(exist_ok=True)
ALLOWED_STATUS = "approved_for_cdi_proposal"


def _write_record(record: Dict[str, Any]) -> None:
    with STORAGE_PROPOSALS.open("a", encoding="utf-8") as fd:
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


def _load_existing_proposals() -> Set[str]:
    return {record.get("decision_id") for record in _load_jsonl(STORAGE_PROPOSALS) if record.get("decision_id")}


def _build_summary(decision: Dict[str, Any]) -> str:
    category = decision.get("category", "inadequacy")
    return f"Address repeated {category} failure with CDI review"[:120]


def build_proposals(now: datetime | None = None) -> List[Dict[str, Any]]:
    now = now or datetime.utcnow()
    decisions = _load_jsonl(STORAGE_DECISIONS)
    existing = _load_existing_proposals()
    proposals: List[Dict[str, Any]] = []

    for decision in decisions:
        decision_id = decision.get("decision_id")
        status = decision.get("decision_status")
        operator_action = decision.get("operator_action")
        if not decision_id or decision_id in existing:
            continue
        if status != ALLOWED_STATUS or operator_action != "approve_for_proposal":
            continue
        proposal = {
            "proposal_id": f"proposal_{uuid.uuid4().hex[:8]}",
            "timestamp": now.replace(microsecond=0).isoformat() + "Z",
            "decision_id": decision_id,
            "intake_id": decision.get("intake_id"),
            "trigger_id": decision.get("trigger_id"),
            "category": decision.get("category"),
            "proposal_summary": _build_summary(decision),
            "proposal_reason": decision.get("decision_reason"),
            "lineage_ref": decision.get("lineage_ref"),
            "evidence_refs": decision.get("evidence_refs", []),
            "governance_status": "pending_governance_review",
            "intake_status": decision.get("decision_status"),
        }
        _write_record(proposal)
        proposals.append(proposal)
        existing.add(decision_id)
    return proposals


def list_proposals() -> List[Dict[str, Any]]:
    return _load_jsonl(STORAGE_PROPOSALS)
