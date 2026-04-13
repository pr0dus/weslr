from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

STORAGE_SOURCE = Path(__file__).resolve().parent.parent / "weslr_inadequacy_handoffs.jsonl"
STORAGE_INTAKE = Path(__file__).resolve().parent.parent / "weslr_inadequacy_intake.jsonl"
STORAGE_INTAKE.parent.mkdir(exist_ok=True)
MIN_CONFIDENCE = 0.7


def _write_record(record: Dict[str, Any]) -> None:
    with STORAGE_INTAKE.open("a", encoding="utf-8") as fd:
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
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            records.append(payload)
    return records


def _should_qualify(record: Dict[str, Any]) -> (bool, str):
    readiness = record.get("readiness_for_CDI")
    confidence = record.get("trigger_confidence") or 0.0
    if not readiness:
        return False, "not_ready"
    if confidence >= MIN_CONFIDENCE:
        return True, "confidence_threshold"
    if record.get("severity") == "high":
        return True, "severity_override"
    return False, "low_confidence"


def _build_evidence_refs(events: Iterable[Dict[str, Any]]) -> List[str]:
    refs = []
    for event in events:
        ts = event.get("timestamp")
        provider = event.get("provider")
        if ts and provider:
            refs.append(f"{provider}:{ts}")
    return refs


def _load_handoffs() -> List[Dict[str, Any]]:
    return _load_jsonl(STORAGE_SOURCE)


def _load_existing_intakes() -> Set[str]:
    return {record.get("handoff_id") for record in _load_jsonl(STORAGE_INTAKE) if record.get("handoff_id")}


def qualify_handoffs(now: datetime | None = None) -> List[Dict[str, Any]]:
    now = now or datetime.utcnow()
    processed: Set[str] = _load_existing_intakes()
    handoffs = _load_handoffs()
    intake_records: List[Dict[str, Any]] = []

    for handoff in handoffs:
        handoff_id = handoff.get("handoff_id")
        if not handoff_id or handoff_id in processed:
            continue
        qualifies, reason = _should_qualify(handoff)
        intake_status = "qualified_for_cdi_review" if qualifies else "held_back"
        record = {
            "intake_id": f"intake_{handoff_id}_{uuid.uuid4().hex[:6]}",
            "timestamp": now.replace(microsecond=0).isoformat() + "Z",
            "handoff_id": handoff_id,
            "trigger_id": handoff.get("trigger_id"),
            "event_ids": handoff.get("event_ids", []),
            "category": handoff.get("category"),
            "runtime_states": handoff.get("runtime_states"),
            "trigger_reason": handoff.get("trigger_reason"),
            "trigger_confidence": handoff.get("trigger_confidence"),
            "lineage_ref": handoff.get("lineage_ref"),
            "evidence_refs": handoff.get("evidence_refs", []),
            "qualification_reason": reason,
            "intake_status": intake_status,
        }
        _write_record(record)
        intake_records.append(record)
        processed.add(handoff_id)
    return intake_records
