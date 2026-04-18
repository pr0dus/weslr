from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

from weslr.inadequacy_trigger import find_candidates

STORAGE_PATH = Path(__file__).resolve().parent.parent / "weslr_inadequacy_handoffs.jsonl"
STORAGE_PATH.parent.mkdir(exist_ok=True)


def _write_record(record: Dict[str, Any]) -> None:
    with STORAGE_PATH.open("a", encoding="utf-8") as fd:
        fd.write(json.dumps(record, ensure_ascii=False) + "\n")


def _build_lineage_ref(event: Dict[str, Any]) -> str:
    return f"{event.get('event_id')}@{event.get('timestamp')}"


def _build_evidence_refs(events: Iterable[Dict[str, Any]]) -> List[str]:
    refs = []
    for event in events:
        ts = event.get("timestamp")
        provider = event.get("provider")
        if ts and provider:
            refs.append(f"{provider}:{ts}")
    return refs


def create_handoffs(now: datetime | None = None) -> List[Dict[str, Any]]:
    candidates = find_candidates(now)
    filtered = [c for c in candidates if c.get("readiness_for_CDI")]
    handoffs: List[Dict[str, Any]] = []

    for candidate in filtered:
        event_ids = candidate.get("event_ids", [])
        events = []
        for event_id in event_ids:
            events.extend(
                e
                for e in _load_events()
                if e.get("event_id") == event_id
            )
        record = {
            "handoff_id": f"handoff_{candidate.get('trigger_id')}_{uuid.uuid4().hex[:6]}",
            "timestamp": (now or datetime.utcnow()).replace(microsecond=0).isoformat() + "Z",
            "trigger_id": candidate.get("trigger_id"),
            "event_ids": event_ids,
            "category": candidate.get("category"),
            "runtime_states": candidate.get("runtime_states"),
            "trigger_reason": candidate.get("trigger_reason"),
            "trigger_confidence": candidate.get("trigger_confidence"),
            "readiness_for_CDI": candidate.get("readiness_for_CDI"),
            "lineage_ref": _build_lineage_ref(events[0]) if events else None,
            "evidence_refs": _build_evidence_refs(events),
            "handoff_status": "cdi_candidate_only",
        }
        _write_record(record)
        handoffs.append(record)
    return handoffs


def _load_events() -> List[Dict[str, Any]]:
    from weslr.inadequacy_persistence import _load_events as _load_persistence

    return _load_persistence()
