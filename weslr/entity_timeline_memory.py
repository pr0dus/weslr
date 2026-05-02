"""
WESLR Entity Timeline Memory V1

Per-entity timelines that remember everything Weslr knows about
a specific person, project, institution, or external entity.

Storage:  .weslr/timelines/tl_entity_<entity_id>/events.jsonl
Format:   append-only JSONL, record_type=entity_timeline_event_v1
Authority: entity_memory_only

Strict rules:
  ❌ No raw user prompts stored
  ❌ No automatic entity creation — only explicit or 2+ mentions
  ❌ No execution, no external calls, no Ollama
  ❌ No modification of governance JSONL files
"""

from __future__ import annotations

import json
import pathlib
import re
from typing import Any, Dict, List, Optional

# ============================================================================
# 1. normalize_entity_id
# ============================================================================

def normalize_entity_id(name: str) -> str:
    """Normalize an entity name into a stable entity ID.

    Rules:
      - Lowercase
      - Collapse internal whitespace/underscores to single underscore
      - Replace hyphens with underscores
      - Strip leading/trailing underscores

    Example:
      "Robotic Arm"   → "robotic_arm"
      "Project Phoenix" → "project_phoenix"
      "person::sarah"  → "person_sarah"
    """
    if not name or not isinstance(name, str):
        return ""
    normalized = name.lower().strip()
    # Replace hyphens, colons (single and double), and whitespace with underscores
    normalized = re.sub(r"[-:_\s]+", "_", normalized)
    # Collapse multiple underscores
    normalized = re.sub(r"_+", "_", normalized)
    # Strip leading/trailing underscores
    normalized = normalized.strip("_")
    return normalized


# ============================================================================
# 2. get_entity_timeline_path
# ============================================================================

def get_entity_timeline_path(
    entity_id: str,
    base_dir: str = ".weslr/timelines",
) -> pathlib.Path:
    """Return the path to an entity's events.jsonl file.

    Creates the directory if it doesn't exist.
    """
    entity_id = normalize_entity_id(entity_id)
    path = pathlib.Path(base_dir) / f"tl_entity_{entity_id}" / "events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


# ============================================================================
# 3. append_entity_event
# ============================================================================

def append_entity_event(
    entity_id: str,
    user_id: str,
    summary: str,
    source: str,
    metadata: Optional[Dict[str, Any]] = None,
    base_dir: str = ".weslr/timelines",
) -> Dict[str, Any]:
    """Append an entity timeline event.

    Args:
        entity_id:    Normalized entity ID (e.g. "robotic_arm")
        user_id:     The user who spoke about the entity
        summary:     Short plain-language summary (≤500 chars)
        source:      Where this came from:
                       user_message | experiment_result | timeline_summary |
                       experiment_proposal | capability_result | ...
        metadata:    Optional free-form dict for additional context
        base_dir:    Base timeline directory

    Returns:
        dict with keys: event, path, status: "appended"
    """
    entity_id = normalize_entity_id(entity_id)
    summary = str(summary)[:500]

    event = {
        "record_type": "entity_timeline_event_v1",
        "entity_id": entity_id,
        "user_id": user_id,
        "summary": summary,
        "source": source,
        "metadata": metadata if metadata is not None else {},
        "authority": "entity_memory_only",
        "automatic_action": False,
        "hidden_learning": False,
        "raw_prompt_stored": False,
    }

    # Add ISO timestamp
    from datetime import datetime, timezone
    event["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    path = get_entity_timeline_path(entity_id, base_dir=base_dir)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    return {"event": event, "path": str(path), "status": "appended"}


# ============================================================================
# 4. load_entity_events
# ============================================================================

def load_entity_events(
    entity_id: str,
    limit: int = 10,
    base_dir: str = ".weslr/timelines",
) -> List[Dict[str, Any]]:
    """Load the most recent events for an entity timeline.

    Args:
        entity_id: Normalized entity ID
        limit:     Maximum number of events to return
        base_dir:  Base timeline directory

    Returns:
        List of event dicts, most recent first.
        Empty list if the entity timeline doesn't exist.
    """
    entity_id = normalize_entity_id(entity_id)
    path = pathlib.Path(base_dir) / f"tl_entity_{entity_id}" / "events.jsonl"
    if not path.exists():
        return []

    events: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception:
        return []

    # Return most recent first (reverse)
    return list(reversed(events))[-limit:]


# ============================================================================
# 5. list_entity_timelines
# ============================================================================

def list_entity_timelines(
    base_dir: str = ".weslr/timelines",
) -> List[str]:
    """List all entity IDs that have a timeline.

    Returns:
        List of normalized entity IDs (no tl_entity_ prefix).
    """
    base = pathlib.Path(base_dir)
    if not base.exists():
        return []

    entity_ids: List[str] = []
    for d in base.iterdir():
        if d.is_dir() and d.name.startswith("tl_entity_"):
            entity_ids.append(d.name[len("tl_entity_"):])
    return sorted(entity_ids)


# ============================================================================
# 6. extract_entities_from_summary (V1 stub)
# ============================================================================

def extract_entities_from_summary(
    summary_text: str,
    existing_entity_ids: List[str],
) -> List[str]:
    """Extract entity references from a summary text.

    V1: Returns an empty list (manual entity creation only).
    Future versions may use NLP / pattern matching here.

    Args:
        summary_text:      Text to analyze
        existing_entity_ids: Known entity IDs to match against

    Returns:
        List of normalized entity IDs found (V1: always [])
    """
    # V1 stub — manual entity creation only
    return []


# ============================================================================
# 7. suggest_entity_for_context
# ============================================================================

def suggest_entity_for_context(
    current_message: str,
    entity_ids: List[str],
) -> Optional[str]:
    """Find the most relevant entity ID based on keyword overlap.

    Checks if any entity ID (as snake_case words) appears in the
    current message.

    V1 heuristic:
        - Tokenize current_message (strip punctuation, lowercase)
        - For each known entity_id, check if any of its underscore-split
          words appear in the message
        - Return the one with the most word matches

    Args:
        current_message: The current user message
        entity_ids:      List of known entity IDs to match against

    Returns:
        Normalized entity ID if found, else None
    """
    if not current_message or not entity_ids:
        return None

    # Tokenize current message
    msg_lower = current_message.lower()
    msg_words = set(re.findall(r"[a-z0-9]+", msg_lower))

    best_entity = None
    best_score = 0

    for entity_id in entity_ids:
        # Score: count how many underscore-separated words from entity_id
        # appear in the message
        entity_words = entity_id.split("_")
        score = sum(1 for ew in entity_words if ew in msg_words)
        if score > best_score:
            best_score = score
            best_entity = entity_id

    return best_entity if best_score > 0 else None


# ============================================================================
# 8. write_entity_from_user_message
# ============================================================================

def write_entity_from_user_message(
    entity_name: str,
    user_id: str,
    summary: str,
    source: str = "user_message",
    metadata: Optional[Dict[str, Any]] = None,
    base_dir: str = ".weslr/timelines",
) -> Dict[str, Any]:
    """Write an entity event from a user message.

    Convenience wrapper around append_entity_event that normalizes
    the entity name before storing.

    Args:
        entity_name: Human-readable name ("Robotic Arm")
        user_id:     User who mentioned it
        summary:     What was said about the entity
        source:      "user_message" or "user_message:explicit"
        metadata:    Optional extra dict
        base_dir:    Base timeline directory

    Returns:
        Result from append_entity_event
    """
    entity_id = normalize_entity_id(entity_name)
    return append_entity_event(
        entity_id=entity_id,
        user_id=user_id,
        summary=summary,
        source=source,
        metadata=metadata,
        base_dir=base_dir,
    )


# ============================================================================
# 9. build_entity_continuity_note
# ============================================================================

def build_entity_continuity_note(
    entity_id: str,
    limit: int = 3,
    base_dir: str = ".weslr/timelines",
) -> dict:
    """Build a human-readable continuity note from entity timeline events.

    Args:
        entity_id: Normalized entity ID
        limit:     Number of recent events to include (default 3)
        base_dir:  Base timeline directory

    Returns:
        dict with record_type, entity_id, message, events_used, authority,
        automatic_action=False, hidden_learning=False
    """
    entity_id = normalize_entity_id(entity_id)
    events = load_entity_events(entity_id, limit=limit, base_dir=base_dir)

    if not events:
        return {
            "record_type": "entity_continuity_note_v1",
            "entity_id": entity_id,
            "message": f"I don't have any recorded history for {entity_id}.",
            "events_used": 0,
            "authority": "entity_memory_only",
            "automatic_action": False,
            "hidden_learning": False,
        }

    # Format entity display name from entity_id
    display_name = entity_id.replace("_", " ").title()

    lines = [f"What we know about {display_name}:"]
    for i, event in enumerate(events, 1):
        lines.append(f" {i}. {event.get('summary', '')}")

    return {
        "record_type": "entity_continuity_note_v1",
        "entity_id": entity_id,
        "message": "\n".join(lines),
        "events_used": len(events),
        "authority": "entity_memory_only",
        "automatic_action": False,
        "hidden_learning": False,
    }