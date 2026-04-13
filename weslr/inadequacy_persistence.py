from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

STORAGE_PATH = Path(__file__).resolve().parent.parent / "weslr_inadequacy_events.jsonl"
STORAGE_PATH.parent.mkdir(exist_ok=True)


def _value_or_default(metadata: Dict[str, Any], key: str, default: Any) -> Any:
    value = metadata.get(key)
    return default if value is None else value


def record_inadequacy_event(metadata: Dict[str, Any]) -> None:
    if not metadata:
        return
    runtime_state = metadata.get("runtime_state")
    if runtime_state == "healthy" or runtime_state is None:
        return

    event = {
        "event_id": f"inadequacy_{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "protected_core",
        "path": _value_or_default(metadata, "path", "chat"),
        "provider": _value_or_default(metadata, "provider", "fallback"),
        "runtime_state": runtime_state,
        "runtime_state_reason": _value_or_default(metadata, "runtime_state_reason", "unknown"),
        "fallback_used": bool(metadata.get("fallback_used")),
        "rescue_used": bool(metadata.get("rescue_used")),
        "category": f"inadequacy:{runtime_state}",
    }

    # optional: attach request fingerprint if provided (safe and bounded)
    fingerprint = metadata.get("request_fingerprint")
    if fingerprint and isinstance(fingerprint, str) and len(fingerprint) <= 64:
        event["request_fingerprint"] = fingerprint

    with STORAGE_PATH.open("a", encoding="utf-8") as fd:
        fd.write(json.dumps(event, ensure_ascii=False) + "\n")
