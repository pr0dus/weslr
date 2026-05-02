"""
weslr/continuity_note_chat_bridge.py
=====================================
Continuity Note Chat Bridge — V1

Provides read-only recall of user timeline summaries for simple continuity queries.
Used in staging runtime to answer "what did we work on last time?" style questions.

Rules (strict):
    - Read-only — no writes, no action execution
    - No Ollama, no evidence search
    - No hidden learning signals
    - No raw prompt storage
    - No automatic memory capture

Author: OCC (WESLR governed intelligence)
Version: 1.0.0
"""

from __future__ import annotations

from typing import Optional

from weslr.user_timeline_memory import build_continuity_note

# ── Continuity query patterns ───────────────────────────────────────────────
# Lowercased, whitespace-normalized list of phrases that indicate
# the user is asking for continuity recall.

_CONTINUITY_PATTERNS = [
    "do you remember what we worked on",
    "remember what we worked on",
    "continue from last time",
    "what did we do last time",
    "what were we working on",
    "what did we work on last time",
    "what did we work on yesterday",
    "what did we discuss last time",
    "do you remember what we discussed",
    "remember what we discussed",
    "what were we doing",
    "what were we working on",
    "continue where we left off",
    "continue from where we left off",
    "pick up where we left off",
    "where did we leave off",
]


def is_continuity_query(message: str) -> bool:
    """Return True if the message is a continuity recall query.

    Detection is case-insensitive and whitespace-tolerant.

    Args:
        message: Raw user message string

    Returns:
        True if message matches a continuity pattern, False otherwise
    """
    if not message or not isinstance(message, str):
        return False

    normalized = " ".join(message.lower().split())

    for pattern in _CONTINUITY_PATTERNS:
        if pattern in normalized:
            return True

    return False


def maybe_answer_with_continuity_note(
    message: str,
    user_id: str = "arthur",
    base_dir: str = ".weslr/timelines",
) -> Optional[dict]:
    """If the message is a continuity query, return a continuity note response.

    Does NOT write anything. Does NOT call Ollama or evidence pipelines.
    Returns None if the message is not a continuity query.

    Args:
        message: Raw user message
        user_id: Which user timeline to read
        base_dir: Timeline base directory

    Returns:
        dict with path, response_contract, reply, _continuity_metadata
        OR None if not a continuity query
    """
    if not is_continuity_query(message):
        return None

    note = build_continuity_note(user_id=user_id, limit=3, base_dir=base_dir)

    return {
        "path": "continuity_note",
        "response_contract": "system_answer",
        "reply": note["message"],
        "_continuity_metadata": {
            "continuity_used": True,
            "authority": "user_timeline_memory",
            "automatic_action": False,
            "hidden_learning": False,
            "raw_prompt_stored": False,
            "events_used": note["events_used"],
        },
    }