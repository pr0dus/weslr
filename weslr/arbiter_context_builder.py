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
# Entity timeline events
# ──────────────────────────────────────────────────────────────────────────────

def _load_entity_timeline_events(
    user_id: str,
    current_message: str,
    recent_timeline_events: List[Dict[str, Any]],
    limit: int = 3,
    base_dir: str = ".weslr/timelines",
) -> List[Dict[str, Any]]:
    """Load the most relevant entity timeline events based on current message.

    Detects entity IDs mentioned in recent session events or via keyword
    matching against known entity timelines, then loads the most recent
    events for up to `limit` entity timelines.

    Args:
        user_id: User whose timeline is the context.
        current_message: The current user message (used for keyword matching).
        recent_timeline_events: Recent session timeline events.
        limit: Maximum number of entity timelines to load.
        base_dir: Base timeline directory.

    Returns:
        List of entity timeline events, most recent first.
    """
    try:
        from weslr.entity_timeline_memory import (
            normalize_entity_id,
            load_entity_events,
            list_entity_timelines,
            suggest_entity_for_context,
        )
    except Exception:
        return []

    # Collect entity IDs mentioned in recent timeline events
    candidate_ids: List[str] = []
    for event in recent_timeline_events:
        meta = event.get("metadata", {})
        if isinstance(meta, dict):
            entity_refs = meta.get("entities_mentioned", [])
            candidate_ids.extend(entity_refs)
        tags = event.get("tags", [])
        if isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, str) and "_" in tag:
                    candidate_ids.append(tag)

    # Also check all known entity timelines for keyword match against message
    all_entity_ids = list_entity_timelines(base_dir=base_dir)
    suggested = suggest_entity_for_context(current_message, all_entity_ids)
    if suggested and suggested not in candidate_ids:
        candidate_ids.append(suggested)

    if not candidate_ids:
        return []

    # Deduplicate while preserving order
    seen = set()
    unique_ids = []
    for eid in candidate_ids:
        normalized = normalize_entity_id(eid)
        if normalized not in seen:
            seen.add(normalized)
            unique_ids.append(normalized)

    # Load most recent events for each, up to limit
    entity_events: List[Dict[str, Any]] = []
    for entity_id in unique_ids[:limit]:
        events = load_entity_events(entity_id, limit=5, base_dir=base_dir)
        for event in events:
            event["_entity_id"] = entity_id
            entity_events.append(event)

    return entity_events


# ──────────────────────────────────────────────────────────────────────────────
# Main context builder
# ──────────────────────────────────────────────────────────────────────────────

def build_arbiter_context(
    user_id: str = "arthur",
    current_message: str = "",
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
            - entity_timeline_events: list (from entity_timeline_memory)
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
                "metadata": event.get("metadata", {}),
            })
    except Exception:
        pass

    # ── Entity timeline events ─────────────────────────────────────────────
    entity_timeline_events = _load_entity_timeline_events(
        user_id=user_id,
        current_message=current_message,
        recent_timeline_events=recent_timeline_events,
        limit=3,
        base_dir=timeline_base_dir,
    )

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
        "entity_timeline_events": entity_timeline_events,
        "workplace_overview": workplace_overview_text,
        "pending_experiment_proposals": pending_proposals,
        "session_turn_history": turn_history,
        "capability_scores": [],  # Populated by arbiter's _score_capabilities
        "authority": "read_only_context",
        "automatic_action": False,
    }
