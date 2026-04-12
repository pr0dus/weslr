"""Lightweight consolidated chat hints (hidden continuity cues).

This is intentionally minimal: a small per-identity hint store to subtly improve
chat replies without exposing internal priorities or transcripts.
"""

from typing import Dict, List, Optional, Tuple

# In-memory hint store keyed by (workspace_id, user_id)
_HINTS: Dict[Tuple[Optional[str], Optional[str]], List[str]] = {}


def get_hints(workspace_id: Optional[str], user_id: Optional[str]) -> List[str]:
    return list(_HINTS.get((workspace_id, user_id), []))


def add_hint(workspace_id: Optional[str], user_id: Optional[str], hint: str) -> None:
    if not user_id:
        return
    key = (workspace_id, user_id)
    hints = _HINTS.get(key, [])
    if hint and hint not in hints:
        # keep small, unique list
        hints = (hints + [hint])[-8:]
    _HINTS[key] = hints


def set_hints(workspace_id: Optional[str], user_id: Optional[str], hints: List[str]) -> None:
    if not user_id:
        return
    key = (workspace_id, user_id)
    _HINTS[key] = list(hints)[-8:]


def clear_hints(workspace_id: Optional[str], user_id: Optional[str]) -> None:
    key = (workspace_id, user_id)
    _HINTS.pop(key, None)
