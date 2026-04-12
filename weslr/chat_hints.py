"""Lightweight consolidated chat hints (hidden continuity cues).

This is intentionally minimal: a small per-identity hint store to subtly improve
chat replies without exposing internal priorities or transcripts.
"""

from typing import Dict, List, Optional, Tuple

# In-memory hint store keyed by (workspace_id, user_id)
_HINTS: Dict[Tuple[Optional[str], Optional[str]], List[str]] = {}

# Allowlist of hint categories to keep this layer constrained and safe.
ALLOWED_HINTS = {
    "preference": {"light lunch before workout", "prefers admin after focus", "prefers concise tone"},
    "theme": {"email urgency", "workout planned", "focus block planned"},
    "communication": {"prefers concise", "prefers direct"},
    "cross_topic": {"plan includes workout", "plan includes email"},
}


def get_hints(workspace_id: Optional[str], user_id: Optional[str]) -> List[str]:
    return list(_HINTS.get((workspace_id, user_id), []))


def _normalize(hint: str) -> str:
    return hint.strip().lower()


def _is_allowed(hint: str) -> bool:
    h = _normalize(hint)
    return any(h in bucket for bucket in ALLOWED_HINTS.values())


def add_hint(workspace_id: Optional[str], user_id: Optional[str], hint: str) -> None:
    if not user_id:
        return
    h = _normalize(hint)
    if not _is_allowed(h):
        return
    key = (workspace_id, user_id)
    hints = _HINTS.get(key, [])
    if h and h not in hints:
        # keep small, unique list
        hints = (hints + [h])[-8:]
    _HINTS[key] = hints


def set_hints(workspace_id: Optional[str], user_id: Optional[str], hints: List[str]) -> None:
    if not user_id:
        return
    allowed = []
    for h in hints:
        hn = _normalize(h)
        if _is_allowed(hn):
            allowed.append(hn)
    key = (workspace_id, user_id)
    _HINTS[key] = allowed[-8:]


def clear_hints(workspace_id: Optional[str], user_id: Optional[str]) -> None:
    key = (workspace_id, user_id)
    _HINTS.pop(key, None)
