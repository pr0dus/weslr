from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = [
    "Objective",
    "Completed",
    "Files changed",
    "Behavior changed",
    "Checks performed",
    "Known risks",
    "Next exact step",
    "Resume hint",
]

OPTIONAL_FIELDS = [
    "Identity impact",
]


class ContinuationNoteError(ValueError):
    pass


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except OSError:
        return default
    except json.JSONDecodeError:
        return default


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def load_notes(path: Path) -> list[dict]:
    raw = _read_json(path, [])
    return raw if isinstance(raw, list) else []


def validate_note_fields(note: dict) -> dict:
    normalized = {}
    missing = []
    for field in REQUIRED_FIELDS:
        value = str(note.get(field, "")).strip()
        if not value:
            missing.append(field)
        normalized[field] = value
    if missing:
        raise ContinuationNoteError(f"missing required continuation note field(s): {', '.join(missing)}")
    return normalized


def append_note(path: Path, note: dict, *, author: str = "operator", now_ts: int | None = None) -> dict:
    now_ts = int(now_ts or time.time())
    normalized = validate_note_fields(note)
    # Add identity impact if present (optional field)
    if "Identity impact" in note:
        normalized["Identity impact"] = str(note["Identity impact"]).strip()
    notes = load_notes(path)
    entry = {
        "id": f"continuation-{now_ts}-{len(notes) + 1}",
        "created_at": now_ts,
        "author": author,
        "format": "circleforge.continuation-note.v1",
        **normalized,
    }
    notes.append(entry)
    _write_json(path, notes[-100:])
    return entry


def latest_note(path: Path) -> dict:
    notes = load_notes(path)
    return notes[-1] if notes else {}


def render_note_text(note: dict) -> str:
    if not note:
        return "CONTINUATION NOTE\nObjective: \nCompleted: \nFiles changed: \nBehavior changed: \nChecks performed: \nKnown risks: \nNext exact step: \nResume hint: \nIdentity impact: "
    lines = ["CONTINUATION NOTE"]
    for field in REQUIRED_FIELDS:
        lines.append(f"{field}: {str(note.get(field, '')).strip()}")
    if "Identity impact" in note:
        lines.append(f"Identity impact: {str(note['Identity impact']).strip()}")
    return "\n".join(lines)
