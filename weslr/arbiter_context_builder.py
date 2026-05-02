"""
WESLR Arbiter Context Builder V1

Read-only context gathering for the hybrid turn arbiter.
Does NOT write, execute, or call external services.

Authority: read_only_context — only reads existing JSONL and files.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List, Optional


# ──────────────────────────────────────────────────────────────────────────────
# Pending experiment proposals
# ──────────────────────────────────────────────────────────────────────────────

def _load_pending_experiment_proposals(
    path: Optional[str | pathlib.Path] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Load pending experiment proposals from experiment_proposals.jsonl.

    Reads the file and returns proposals where execution_status == "pending".
    Malformed lines are skipped silently.

    Args:
        path: Path to experiment_proposals.jsonl. None = default path.
        limit: Maximum number to return.

    Returns:
        List of proposal dicts.
    """
    if path is None:
        path = pathlib.Path(".weslr") / "experiment_proposals.jsonl"
    else:
        path = pathlib.Path(path)

    if not path.exists():
        return []

    proposals: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # Only include pending proposals
                if record.get("execution_status") == "pending":
                    proposals.append(record)
                    if len(proposals) >= limit:
                        break
    except OSError:
        pass

    return proposals


# ──────────────────────────────────────────────────────────────────────────────
# Workplace overview (from file)
# ──────────────────────────────────────────────────────────────────────────────

def _load_workplace_overview_text(
    path: Optional[str | pathlib.Path] = None,
) -> Optional[str]:
    """Load workplace overview text from a file.

    If the file doesn't exist or can't be read, returns None.
    The file is expected to contain a plain-text workplace overview.

    Args:
        path: Path to workplace overview file. None = default path.

    Returns:
        String content of the file, or None if not found.
    """
    if path is None:
        path = pathlib.Path(".weslr") / "workplace_overview.txt"
    else:
        path = pathlib.Path(path)

    if not path.exists():
        return None

    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Main context builder
# ──────────────────────────────────────────────────────────────────────────────

def build_arbiter_context(
    user_id: str = "arthur",
    session_turn_history: Optional[List[Dict[str, Any]]] = None,
    proposal_path: Optional[str | pathlib.Path] = None,
    workplace_overview_path: Optional[str | pathlib.Path] = None,
    timeline_base_dir: str = ".weslr/timelines",
) -> Dict[str, Any]:
    """Build a full arbiter context dict from all available sources.

    Read-only. No writes, no external calls, no Ollama.

    Args:
        user_id: Which user timeline to read.
        session_turn_history: Optional list of prior analyze_turn results
            from this session (used to populate context.session_turn_history).
        proposal_path: Optional path to experiment_proposals.jsonl.
        workplace_overview_path: Optional path to workplace_overview.txt.
        timeline_base_dir: Base directory for user timelines.

    Returns:
        dict with keys:
            - user_id: str
            - recent_timeline_events: list (from user_timeline_memory)
            - workplace_overview: str | None
            - pending_experiment_proposals: list
            - session_turn_history: list (from param)
            - capability_scores: list (empty in V1 — populated by arbiter)
            - authority: "read_only_context"
            - automatic_action: False
    """
    # ── Timeline events ────────────────────────────────────────────────────
    recent_timeline_events: List[Dict[str, Any]] = []
    try:
        from weslr.user_timeline_memory import load_recent_session_summaries

        events = load_recent_session_summaries(
            user_id=user_id,
            limit=5,
            base_dir=timeline_base_dir,
        )
        # Convert to minimal event dicts for the arbiter
        for event in events:
            recent_timeline_events.append({
                "summary": event.get("summary", ""),
                "timestamp": event.get("timestamp"),
                "source": event.get("source", "unknown"),
                "tags": event.get("tags", []),
            })
    except Exception:
        pass

    # ── Workplace overview (file) ─────────────────────────────────────────
    workplace_overview_text = _load_workplace_overview_text(path=workplace_overview_path)

    # ── Pending experiment proposals ──────────────────────────────────────
    pending_proposals = _load_pending_experiment_proposals(path=proposal_path, limit=10)

    # ── Session turn history (passed in, not read from disk) ──────────────
    # We receive it as a parameter so the server can maintain it in memory
    # across requests within the same session.
    turn_history = list(session_turn_history) if session_turn_history else []

    return {
        "user_id": user_id,
        "recent_timeline_events": recent_timeline_events,
        "workplace_overview": workplace_overview_text,
        "pending_experiment_proposals": pending_proposals,
        "session_turn_history": turn_history,
        "capability_scores": [],  # Populated by arbiter's _score_capabilities
        "authority": "read_only_context",
        "automatic_action": False,
    }
