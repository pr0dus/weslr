"""WESLR Workplace Chat Bridge V1

Read-only bridge that intercepts workplace overview queries
and answers them with build_workplace_text() output.

Authority: read_only_workplace
No writes, no execution, no approval/rejection.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from weslr.workplace_review_surface import (
    build_workplace_overview,
    build_workplace_text,
)

# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

_WORKPLACE_TRIGGERS = [
    re.compile(r"what are we working on", re.IGNORECASE),
    re.compile(r"show my workplace", re.IGNORECASE),
    re.compile(r"workplace overview", re.IGNORECASE),
    re.compile(r"what ideas are pending", re.IGNORECASE),
    re.compile(r"what experiments are pending", re.IGNORECASE),
    re.compile(r"pending ideas", re.IGNORECASE),
    re.compile(r"pending experiments", re.IGNORECASE),
    re.compile(r"what should we continue", re.IGNORECASE),
    re.compile(r"^/workplace$", re.IGNORECASE),
    re.compile(r"^/ideas$", re.IGNORECASE),
    re.compile(r"^/experiments$", re.IGNORECASE),
]

_IGNORE_PATTERNS = [
    re.compile(r"what is entropy", re.IGNORECASE),
    re.compile(r"what is weslr", re.IGNORECASE),
    re.compile(r"what can you do", re.IGNORECASE),
    re.compile(r"do you remember what we worked on", re.IGNORECASE),
    re.compile(r"^/evidence$", re.IGNORECASE),
    re.compile(r"^/state$", re.IGNORECASE),
    re.compile(r"continuity", re.IGNORECASE),
]


def is_workplace_query(message: str) -> bool:
    """Return True if message is a workplace overview query."""
    # Check ignore first
    for pattern in _IGNORE_PATTERNS:
        if pattern.search(message):
            return False
    # Check triggers
    for pattern in _WORKPLACE_TRIGGERS:
        if pattern.search(message):
            return True
    return False


def maybe_answer_with_workplace(
    message: str,
    user_id: str = "arthur",
    proposal_path: Optional[str] = None,
    timeline_base_dir: str = ".weslr/timelines",
) -> Optional[dict[str, Any]]:
    """Answer with workplace overview if message is a workplace query.

    Returns None if message is not a workplace query.

    Returns a dict with:
        - path: "workplace_overview"
        - response_contract: "system_answer"
        - reply: human-readable workplace text
        - _workplace_metadata: safety + counts
    """
    if not is_workplace_query(message):
        return None

    try:
        overview = build_workplace_overview(
            user_id=user_id,
            proposal_path=proposal_path,
            timeline_base_dir=timeline_base_dir,
        )
    except Exception:
        return None

    try:
        text = build_workplace_text(overview)
    except Exception:
        return None

    pending_count = overview.get("counts", {}).get("pending_experiments", 0)
    ideas_count = overview.get("counts", {}).get("ideas", 0)

    return {
        "path": "workplace_overview",
        "response_contract": "system_answer",
        "reply": text,
        "_workplace_metadata": {
            "workplace_used": True,
            "authority": "read_only_workplace",
            "automatic_action": False,
            "hidden_learning": False,
            "raw_prompt_stored": False,
            "pending_experiments": pending_count,
            "recent_ideas": ideas_count,
        },
    }
