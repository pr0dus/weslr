"""
weslr/user_timeline_memory.py
=============================
User Timeline Memory — V1 (First Safe Jarvis-like Memory Experiment)

Append-only user timeline that stores short session summary events.
Does NOT store raw prompts, full transcripts, or hidden learning signals.
Does NOT execute actions automatically.

Purpose:
    First minimal building block for "I remember what we talked about last time."
    Explicit write only — no automatic runtime call, no chat injection yet.

Path:
    .weslr/timelines/user_<normalized_user_id>/events.jsonl

Rules (strict):
    - Summary required, max 1000 chars
    - No raw_prompt_stored, no hidden_learning, no automatic_action
    - No external calls, no Ollama imports
    - Additive only — does not modify existing JSONL governance logs

Author: OCC (WESLR governed intelligence)
Version: 1.0.0
"""

from __future__ import annotations

import json
import os
import re
import time as _time
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Safe filename character map ──────────────────────────────────────────────
_SAFE_CHARS_RE = re.compile(r"[^a-z0-9_-]")
_MULTI_DASH_RE = re.compile(r"-+")


# ============================================================================
# 1. normalize_user_id
# ============================================================================

def normalize_user_id(user_id: str) -> str:
    """Normalize user_id to safe lowercase filename base.

    Rules:
        - lowercase
        - only a-z, 0-9, _, -
        - collapse multiple dashes to one
        - strip leading/trailing dashes
        - default 'default_user' if result is empty

    Args:
        user_id: Raw user identifier

    Returns:
        Safe normalized string
    """
    if not user_id or not isinstance(user_id, str):
        return "default_user"
    normalized = _SAFE_CHARS_RE.sub("", user_id.lower().strip())
    normalized = _MULTI_DASH_RE.sub("-", normalized).strip("-")
    if not normalized:
        return "default_user"
    return normalized


# ============================================================================
# 2. get_user_timeline_path
# ============================================================================

def get_user_timeline_path(
    user_id: str,
    base_dir: str = ".weslr/timelines",
) -> Path:
    """Return the path to a user's timeline events file.

    Path format:
        <base_dir>/user_<normalized_user_id>/events.jsonl

    Args:
        user_id: Raw user identifier
        base_dir: Base directory for all timelines

    Returns:
        Path to the user's events.jsonl file
    """
    normalized = normalize_user_id(user_id)
    return Path(base_dir) / f"user_{normalized}" / "events.jsonl"


# ============================================================================
# 3. build_session_summary_event
# ============================================================================

MAX_SUMMARY_LENGTH = 1000
VALID_SOURCES = {"manual", "voice", "chat", "operator"}


def build_session_summary_event(
    user_id: str,
    summary: str,
    source: str = "manual",
    tags: Optional[List[str]] = None,
) -> dict:
    """Build a single user session summary event record.

    Rules:
        - summary is required and max 1000 chars
        - source must be one of: manual, voice, chat, operator
        - tags must be a list or None
        - raw_prompt_stored, hidden_learning, automatic_action always False
        - authority is always 'user_timeline_memory'

    Args:
        user_id: Raw user identifier
        summary: Short human-authored session summary
        source: Origin of the summary
        tags: Optional list of string tags

    Returns:
        dict event record

    Raises:
        ValueError: If summary is missing or exceeds 1000 chars
    """
    if not summary or not isinstance(summary, str):
        raise ValueError("summary is required and must be a non-empty string")
    summary = summary.strip()
    if not summary:
        raise ValueError("summary is required and must be a non-empty string")
    if len(summary) > MAX_SUMMARY_LENGTH:
        raise ValueError(
            f"summary exceeds maximum length of {MAX_SUMMARY_LENGTH} chars "
            f"(got {len(summary)})"
        )
    if source not in VALID_SOURCES:
        raise ValueError(
            f"source must be one of: {', '.join(sorted(VALID_SOURCES))}"
        )

    return {
        "record_type": "user_session_summary_event_v1",
        "user_id": normalize_user_id(user_id),
        "summary": summary,
        "source": source,
        "tags": list(tags) if tags else [],
        "timestamp": _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()),
        "authority": "user_timeline_memory",
        "automatic_action": False,
        "raw_prompt_stored": False,
        "hidden_learning": False,
    }


# ============================================================================
# 4. append_session_summary
# ============================================================================

def append_session_summary(
    user_id: str,
    summary: str,
    source: str = "manual",
    tags: Optional[List[str]] = None,
    base_dir: str = ".weslr/timelines",
) -> dict:
    """Append exactly one JSONL event to the user's timeline.

    Creates the directory if it does not exist.
    This is an explicit write function only — no automatic runtime call.

    Args:
        user_id: Raw user identifier
        summary: Short session summary
        source: Origin of the summary
        tags: Optional list of tags
        base_dir: Base timeline directory

    Returns:
        dict with keys: event, path, status
    """
    event = build_session_summary_event(user_id, summary, source, tags)

    path = get_user_timeline_path(user_id, base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)

    line = json.dumps(event, ensure_ascii=False)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    return {
        "event": event,
        "path": str(path),
        "status": "appended",
    }


# ============================================================================
# 5. load_recent_session_summaries
# ============================================================================

def load_recent_session_summaries(
    user_id: str,
    limit: int = 5,
    base_dir: str = ".weslr/timelines",
) -> List[dict]:
    """Load the most recent session summary events for a user.

    Reads the user's events.jsonl and returns the latest `limit` valid events.
    Malformed lines are skipped silently.

    Args:
        user_id: Raw user identifier
        limit: Maximum number of events to return (default 5)
        base_dir: Base timeline directory

    Returns:
        List of event dicts, most recent first
    """
    path = get_user_timeline_path(user_id, base_dir)
    if not path.exists():
        return []

    events: List[dict] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    # Skip malformed lines silently
                    continue
    except OSError:
        return []

    # Return most recent first: slice last `limit` items and reverse
    recent = events[-limit:] if limit > 0 else events
    return list(reversed(recent))


# ============================================================================
# 6. build_continuity_note
# ============================================================================

def build_continuity_note(
    user_id: str,
    limit: int = 3,
    base_dir: str = ".weslr/timelines",
) -> dict:
    """Build a human-readable continuity note from recent session summaries.

    Uses only summary text from stored events.
    Does NOT invent context or infer sensitive attributes.

    Args:
        user_id: Raw user identifier
        limit: Number of recent events to consider (default 3)
        base_dir: Base timeline directory

    Returns:
        dict with record_type, user_id, message, events_used, authority,
        automatic_action=False, hidden_learning=False
    """
    events = load_recent_session_summaries(user_id, limit=limit, base_dir=base_dir)

    if not events:
        return {
            "record_type": "user_continuity_note_v1",
            "user_id": normalize_user_id(user_id),
            "message": "I do not have prior timeline notes yet.",
            "events_used": 0,
            "authority": "user_timeline_memory",
            "automatic_action": False,
            "hidden_learning": False,
        }

    if len(events) == 1:
        message = f"Last time, we worked on: {events[0]['summary']}"
    else:
        lines = ["Recently, we worked on:"]
        for i, event in enumerate(events, 1):
            lines.append(f" {i}. {event['summary']}")
        message = "\n".join(lines)

    return {
        "record_type": "user_continuity_note_v1",
        "user_id": normalize_user_id(user_id),
        "message": message,
        "events_used": len(events),
        "authority": "user_timeline_memory",
        "automatic_action": False,
        "hidden_learning": False,
    }