"""
WESLR Workplace Review Surface V1

Read-only aggregation of experiment proposals, project ideas,
proactive suggestions, continuity context, and next review actions.

V1 scope:
- workplace overview dict
- pending experiment proposal list
- recent idea extraction from timeline
- human-readable workplace text

Authority: read_only_workplace
No writes, no execution, no approval/rejection, no JSONL mutation.
"""

from __future__ import annotations

import pathlib
import re
from typing import Any, Optional

from weslr.experiment_proposal_store import (
    load_experiment_proposals,
)
from weslr.proactive_suggestions import build_proactive_suggestion
from weslr.user_timeline_memory import load_recent_session_summaries

# ---------------------------------------------------------------------------
# Idea extraction pattern
# ---------------------------------------------------------------------------

_IDEA_PATTERN = re.compile(
    r"\b(idea|maybe|could|should|experiment|project|build|test|try|explore|investigate|design|plan)\b",
    re.IGNORECASE,
)


def _is_idea_summary(summary: str) -> bool:
    """Return True if summary looks idea-like."""
    return bool(_IDEA_PATTERN.search(summary))


# ---------------------------------------------------------------------------
# 1. list pending experiment proposals
# ---------------------------------------------------------------------------

def list_pending_experiment_proposals(
    path: Optional[str | pathlib.Path] = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return compact summaries of pending experiment proposals.

    Args:
        path: experiment_proposals.jsonl path. None = default.
        limit: Maximum number to return.

    Returns:
        List of dicts with keys: proposal_id, type, title, confidence,
        risk_level, requires_operator_approval, timeline_id.
    """
    proposals = load_experiment_proposals(path=path, status="pending")
    result = []
    for p in proposals[:limit]:
        result.append({
            "proposal_id": p.get("proposal_id", "unknown"),
            "type": p.get("type", "unknown"),
            "title": p.get("title", ""),
            "confidence": p.get("confidence", 0.0),
            "risk_level": p.get("risk_level", "unknown"),
            "requires_operator_approval": p.get("requires_operator_approval", False),
            "timeline_id": p.get("timeline_id"),
        })
    return result


# ---------------------------------------------------------------------------
# 2. list recent ideas from timeline
# ---------------------------------------------------------------------------

def list_recent_ideas(
    user_id: str = "arthur",
    limit: int = 5,
    timeline_base_dir: str = ".weslr/timelines",
) -> list[dict[str, Any]]:
    """Extract idea-like summaries from recent user timeline events.

    Args:
        user_id: Which user timeline to read
        limit: Maximum number of ideas to return
        timeline_base_dir: Timeline base directory

    Returns:
        List of dicts:
            idea_id: "IDEA-TL-NNN"
            summary: the event summary text
            source: "user_timeline_memory"
            timeline_id: timeline ID
            authority: "read_only_workplace"
    """
    events = load_recent_session_summaries(
        user_id, limit=20, base_dir=timeline_base_dir
    )

    ideas: list[dict[str, Any]] = []
    counter = 1
    for event in events:
        summary = event.get("summary", "")
        if not summary:
            continue
        if _is_idea_summary(summary):
            ideas.append({
                "idea_id": f"IDEA-TL-{counter:03d}",
                "summary": summary,
                "source": "user_timeline_memory",
                "timeline_id": event.get("timeline_id", "unknown"),
                "authority": "read_only_workplace",
            })
            counter += 1
            if counter > limit:
                break

    return ideas


# ---------------------------------------------------------------------------
# 3. build workplace overview
# ---------------------------------------------------------------------------

def build_workplace_overview(
    user_id: str = "arthur",
    proposal_path: Optional[str | pathlib.Path] = None,
    timeline_base_dir: str = ".weslr/timelines",
) -> dict[str, Any]:
    """Build a read-only workplace overview from existing WESLR data.

    Args:
        user_id: Which user timeline to read
        proposal_path: experiment_proposals.jsonl path. None = default.
        timeline_base_dir: Timeline base directory

    Returns:
        dict with:
            record_type: "workplace_overview_v1"
            user_id, summary, sections, counts, authority,
            automatic_action, hidden_learning, raw_prompt_stored
    """
    pending = list_pending_experiment_proposals(path=proposal_path, limit=10)
    ideas = list_recent_ideas(user_id=user_id, limit=5, timeline_base_dir=timeline_base_dir)
    suggestion = build_proactive_suggestion(
        user_id=user_id, base_dir=timeline_base_dir
    )

    # Build next review actions
    next_review_actions: list[str] = []
    if pending:
        next_review_actions.append(
            f"Review {len(pending)} pending experiment proposal{'s' if len(pending) > 1 else ''}"
        )
    if ideas:
        next_review_actions.append("Choose one idea to develop into an experiment")
    if suggestion.get("suggestion_available"):
        next_review_actions.append("Consider the proactive suggestion for next steps")
    if not next_review_actions:
        next_review_actions.append("Continue the latest timeline topic")

    # Build summary
    pending_count = len(pending)
    ideas_count = len(ideas)
    has_suggestion = suggestion.get("suggestion_available", False)

    summary_parts = []
    if pending_count > 0:
        summary_parts.append(f"{pending_count} pending experiment{'s' if pending_count > 1 else ''}")
    if ideas_count > 0:
        summary_parts.append(f"{ideas_count} recent idea{'s' if ideas_count > 1 else ''}")
    if has_suggestion:
        summary_parts.append("1 proactive suggestion")

    if summary_parts:
        summary = "WESLR workplace: " + ", ".join(summary_parts) + "."
    else:
        summary = "WESLR workplace: no pending experiments, ideas, or suggestions right now."

    return {
        "record_type": "workplace_overview_v1",
        "user_id": user_id,
        "summary": summary,
        "sections": {
            "pending_experiments": pending,
            "recent_ideas": ideas,
            "proactive_suggestion": suggestion if has_suggestion else None,
            "continuity": None,  # populated below if possible
            "next_review_actions": next_review_actions,
        },
        "counts": {
            "pending_experiments": pending_count,
            "ideas": ideas_count,
            "suggestions": 1 if has_suggestion else 0,
        },
        "authority": "read_only_workplace",
        "automatic_action": False,
        "hidden_learning": False,
        "raw_prompt_stored": False,
    }


# ---------------------------------------------------------------------------
# 4. build human-readable workplace text
# ---------------------------------------------------------------------------

def build_workplace_text(overview: dict[str, Any]) -> str:
    """Render a workplace overview as human-readable text.

    Args:
        overview: output of build_workplace_overview

    Returns:
        Multi-line human-readable message.
        No internal dumps, no commands required.
    """
    lines = ["Here is your current WESLR workplace.\n"]

    # Pending experiments
    pending = overview.get("sections", {}).get("pending_experiments", [])
    if pending:
        lines.append("Pending Experiments")
        lines.append("-" * 24)
        for p in pending:
            risk = p.get("risk_level", "?").upper()
            conf = p.get("confidence", 0.0)
            title = p.get("title", "?")
            lines.append(f"  [{risk}] {title}")
        lines.append("")
    else:
        lines.append("Pending Experiments: none")
        lines.append("")

    # Recent ideas
    ideas = overview.get("sections", {}).get("recent_ideas", [])
    if ideas:
        lines.append("Recent Ideas")
        lines.append("-" * 16)
        for idea in ideas:
            lines.append(f"  • {idea['summary']}")
        lines.append("")
    else:
        lines.append("Recent Ideas: none")
        lines.append("")

    # Proactive suggestion
    suggestion = overview.get("sections", {}).get("proactive_suggestion")
    if suggestion:
        lines.append("Suggested Next Step")
        lines.append("-" * 22)
        lines.append(f"  {suggestion.get('suggestion', '?')}")
        lines.append("")
    else:
        lines.append("Suggested Next Step: none right now")
        lines.append("")

    # Next review actions
    actions = overview.get("sections", {}).get("next_review_actions", [])
    if actions:
        lines.append("Next Review Actions")
        lines.append("-" * 22)
        for action in actions:
            lines.append(f"  → {action}")
        lines.append("")

    return "\n".join(lines)
