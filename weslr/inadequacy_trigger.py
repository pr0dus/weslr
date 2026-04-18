from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

STORAGE_PATH = Path(__file__).resolve().parent.parent / "weslr_inadequacy_events.jsonl"
WINDOW_MINUTES = 60
MIN_RECURRENCE = 2


def _parse_timestamp(raw: str) -> datetime:
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        ts = datetime.fromisoformat(raw)
        if ts.tzinfo is not None:
            ts = ts.astimezone(timezone.utc).replace(tzinfo=None)
        return ts
    except Exception:
        return datetime.utcnow()


def _load_events() -> List[Dict[str, Any]]:
    if not STORAGE_PATH.exists():
        return []
    events: List[Dict[str, Any]] = []
    with STORAGE_PATH.open("r", encoding="utf-8") as fd:
        for line in fd:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = _parse_timestamp(payload.get("timestamp", ""))
            payload["timestamp_dt"] = ts
            events.append(payload)
    return events


def find_candidates(now: datetime | None = None) -> List[Dict[str, Any]]:
    now = now or datetime.utcnow()
    window_start = now - timedelta(minutes=WINDOW_MINUTES)
    events = [e for e in _load_events() if e.get("timestamp_dt") >= window_start]
    events.sort(key=lambda e: e["timestamp_dt"])

    groups: Dict[str, List[Dict[str, Any]]] = {}
    for event in events:
        category = event.get("category") or "inadequacy:unknown"
        groups.setdefault(category, []).append(event)

    candidates: List[Dict[str, Any]] = []
    for category, bucket in groups.items():
        if not bucket:
            continue
        runtime_states = {e.get("runtime_state") for e in bucket}
        severity_high = "unavailable" in runtime_states
        recurrence = len(bucket)
        readiness = recurrence >= MIN_RECURRENCE or severity_high
        if not readiness:
            continue
        confidence = min(0.5 + recurrence * 0.1 + (0.2 if severity_high else 0.0), 0.95)
        candidate = {
            "trigger_id": f"trigger_{category}_{uuid.uuid4().hex[:6]}",
            "timestamp": now.replace(microsecond=0).isoformat() + "Z",
            "event_ids": [e.get("event_id") for e in bucket if e.get("event_id")],
            "trigger_reason": (
                "recurrent" if recurrence >= MIN_RECURRENCE else "severity"
            ),
            "severity": "high" if severity_high else "medium",
            "trigger_confidence": round(confidence, 2),
            "candidate_status": "candidate_only",
            "readiness_for_CDI": severity_high or recurrence >= MIN_RECURRENCE,
            "category": category,
            "runtime_states": list(runtime_states),
        }
        candidates.append(candidate)
    return candidates
