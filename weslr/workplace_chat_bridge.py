"""WESLR Workplace Chat Bridge V1

Read-only bridge that intercepts workplace overview queries
and answers them with build_workplace_text() output.

Optionally augments with generated experiment suggestions from
the experiment proposal generator (dry-run only).

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

# Feature flag: include generated experiment suggestions in workplace response
_INCLUDE_GENERATED_SUGGESTIONS = True

# ---------------------------------------------------------------------------
# Generated suggestions helper
# ---------------------------------------------------------------------------

def _build_generated_suggestions_section(
    user_id: str = "arthur",
    timeline_base_dir: str = ".weslr/timelines",
    limit: int = 3,
) -> str:
    """Build a read-only text section of generated experiment suggestions.

    Calls generate_experiment_proposals(dry_run=True) and formats the
    results as bullet points. Returns empty string if no proposals generated.

    Args:
        user_id: User timeline to base suggestions on
        timeline_base_dir: Timeline base directory
        limit: Maximum number of suggestions to include

    Returns:
        Multi-line text section, or empty string if no suggestions.
    """
    try:
        from weslr.experiment_proposal_generator import generate_experiment_proposals
    except Exception:
        return ""

    try:
        result = generate_experiment_proposals(
            user_id=user_id,
            dry_run=True,
            path=None,
        )
    except Exception:
        return ""

    generated = result.get("generated", [])
    if not generated:
        return ""

    lines = [
        "Generated experiment suggestions (based on your recent work)",
        "(Not yet approved or queued — review before acting)",
        "-" * 52,
    ]
    for proposal in generated[:limit]:
        title = proposal.get("title", "?")
        desc = proposal.get("description", "")[:120]
        conf = proposal.get("confidence", 0.0)
        lines.append(f"  • {title}")
        if desc:
            lines.append(f"    {desc}{'...' if len(proposal.get('description','')) > 120 else ''}")
        lines.append(f"    [confidence: {conf:.0%}]")
        lines.append("")

    return "\n".join(lines).rstrip()


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
    include_generated_suggestions: bool = True,
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
        text = None

    reply = text or "Workplace overview is not available right now."

    # ── Generated experiment suggestions (dry-run) ───────────────────────
    generated_section = ""
    if include_generated_suggestions:
        generated_section = _build_generated_suggestions_section(
            user_id=user_id,
            timeline_base_dir=timeline_base_dir,
        )
        if generated_section:
            reply = reply.rstrip() + "\n\n" + generated_section

    pending_count = overview.get("counts", {}).get("pending_experiments", 0)
    ideas_count = overview.get("counts", {}).get("ideas", 0)
    generated_count = 0
    if include_generated_suggestions:
        try:
            from weslr.experiment_proposal_generator import generate_experiment_proposals
            result = generate_experiment_proposals(
                user_id=user_id,
                dry_run=True,
                path=proposal_path,
            )
            generated_count = result.get("total_count", 0)
        except Exception:
            pass

    return {
        "path": "workplace_overview",
        "response_contract": "system_answer",
        "reply": reply,
        "_workplace_metadata": {
            "workplace_used": True,
            "authority": "read_only_workplace",
            "automatic_action": False,
            "hidden_learning": False,
            "raw_prompt_stored": False,
            "pending_experiments": pending_count,
            "recent_ideas": ideas_count,
            "generated_suggestions": generated_count,
        },
    }
