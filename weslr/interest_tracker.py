"""
Weslr Interest Tracker — v1 (Phase 0)

Lightweight registry for tracking operator-relevant themes.
Read-only interest creation only. No occurrence tracking yet.
No background scanning, no autonomous behavior.

Schema:
  id          — 8-char hex (uuid[:8])
  name        — unique normalized identifier (lowercase, underscores)
  display_name — human-friendly name (can contain spaces)
  status      — always "active" in v1
  created_at  — ISO timestamp
  last_seen_at — ISO timestamp (set to created_at on creation)
  occurrence_count — always 0 in v1 (reserved for future)
  tags        — list of normalized tag strings
  occurrences — empty list in v1 (reserved for future)
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Storage path ──────────────────────────────────────────────────────────────

_INTERESTS_PATH: Optional[Path] = None


def _interests_path() -> Path:
    global _INTERESTS_PATH
    if _INTERESTS_PATH is not None:
        return _INTERESTS_PATH
    base = os.environ.get("WESLR_STATE_DIR", "/data/data/com.termux/files/home/.openclaw/workspace")
    _INTERESTS_PATH = Path(base) / "weslr" / "interests.json"
    return _INTERESTS_PATH


def set_interests_path(path: Path) -> None:
    """Override the storage path (for testing)."""
    global _INTERESTS_PATH
    _INTERESTS_PATH = path


# ── Normalization helpers ─────────────────────────────────────────────────────

def normalize_name(name: str) -> str:
    """Convert display name to normalized internal name."""
    # lowercase, replace spaces/hyphens with underscores, keep alphanumeric/underscore
    normalized = name.lower().strip()
    normalized = re.sub(r"[\s\-]+", "_", normalized)
    normalized = re.sub(r"[^a-z0-9_]", "", normalized)
    normalized = normalized.strip("_")
    if not normalized:
        raise ValueError("name cannot be empty after normalization")
    return normalized


def normalize_tags(tags: List[str]) -> List[str]:
    """Normalize a list of tags."""
    result = []
    for t in tags:
        t = t.lower().strip().replace(" ", "_")
        if t and t != "," and len(t) > 0:
            result.append(t)
    return sorted(set(result))


# ── Core I/O ──────────────────────────────────────────────────────────────────

def _load() -> Dict[str, List[Dict[str, Any]]]:
    """Load interests registry. Returns empty structure if missing or corrupt."""
    path = _interests_path()
    if not path.exists():
        return {"interests": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "interests" not in data:
            return {"interests": []}
        return data
    except (json.JSONDecodeError, OSError):
        return {"interests": []}


def _save(data: Dict[str, List[Dict[str, Any]]]) -> None:
    """Save interests registry atomically via rename."""
    path = _interests_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.rename(path)


# ── Interest creation (Phase 0 only) ─────────────────────────────────────────

MAX_INTERESTS = 50


def create_interest(
    name: str,
    tags: Optional[List[str]] = None,
    display_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new interest.

    Raises:
        ValueError if name is empty, duplicate, or cap reached.
    """
    if not name or not name.strip():
        raise ValueError("name cannot be empty")

    normalized = normalize_name(name)
    if len(normalized) < 2:
        raise ValueError("name too short after normalization")

    data = _load()

    # Check duplicate
    for existing in data["interests"]:
        if normalize_name(existing["name"]) == normalized:
            raise ValueError(f"interest with name '{normalized}' already exists")

    # Check cap
    if len(data["interests"]) >= MAX_INTERESTS:
        raise ValueError(f"cap reached: max {MAX_INTERESTS} interests")

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    interest = {
        "id": str(uuid.uuid4())[:8],
        "name": normalized,
        "display_name": display_name.strip() if display_name else name.strip(),
        "status": "active",
        "created_at": now,
        "last_seen_at": now,
        "occurrence_count": 0,
        "tags": normalize_tags(tags or []),
        "occurrences": [],  # reserved for future
    }

    data["interests"].insert(0, interest)  # newest first
    _save(data)
    return interest


def get_interest(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Get interest by id or normalized name.
    Returns None if not found.
    """
    data = _load()
    search = normalize_name(identifier)
    for interest in data["interests"]:
        if interest["id"] == search or normalize_name(interest["name"]) == search:
            return interest
    return None


def list_interests(
    status: Optional[str] = None,
    tag: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List interests, optionally filtered.

    Args:
        status: filter by status ("active", "archived")
        tag: filter by tag (interest must have this tag)
    """
    data = _load()
    results = data["interests"]
    if status:
        results = [i for i in results if i.get("status") == status]
    if tag:
        normalized_tag = tag.lower().strip()
        results = [i for i in results if normalized_tag in i.get("tags", [])]
    return results


# ── Occurrence tracking (Phase 1) ───────────────────────────────────────────────

MAX_OCCURRENCES = 20

VALID_OCCURRENCE_TYPES = frozenset({"artifact", "question", "proposal"})


def add_occurrence(
    interest_id: str,
    occurrence_type: str,
    item_id: str,
    reason: str = "",
) -> Dict[str, Any]:
    """
    Add a manual occurrence to an existing interest.

    Args:
        interest_id:  id of the interest to update
        occurrence_type: one of "artifact", "question", "proposal"
        item_id:      identifier of the triggering item
        reason:       human-readable reason for this occurrence

    Returns:
        The updated interest dict

    Raises:
        ValueError if interest_id not found or occurrence_type invalid
    """
    if occurrence_type not in VALID_OCCURRENCE_TYPES:
        raise ValueError(
            f"occurrence_type must be one of {sorted(VALID_OCCURRENCE_TYPES)}, "
            f"got {occurrence_type!r}"
        )
    if not item_id or not item_id.strip():
        raise ValueError("item_id cannot be empty")

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    data = _load()

    # Locate interest
    target = None
    for interest in data["interests"]:
        if interest["id"] == interest_id:
            target = interest
            break
    if target is None:
        raise ValueError(f"interest not found: {interest_id}")

    # Build new occurrence entry
    occurrence = {
        "type": occurrence_type,
        "item_id": item_id.strip(),
        "triggered_at": now,
        "reason": reason.strip() if reason else "",
    }

    # Append occurrence
    target["occurrences"].insert(0, occurrence)

    # Prune to MAX_OCCURRENCES (keep newest)
    if len(target["occurrences"]) > MAX_OCCURRENCES:
        target["occurrences"] = target["occurrences"][:MAX_OCCURRENCES]

    # Update counters
    target["occurrence_count"] = len(target["occurrences"])
    target["last_seen_at"] = now

    _save(data)
    return target


# ── CLI interface ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    def cmd_create(args: List[str]) -> None:
        if not args:
            print("Usage: interest_tracker.py create <name> [tag,tag,...]")
            sys.exit(1)
        name = args[0]
        tags = []
        if len(args) > 1:
            tags = [t.strip() for t in args[1].split(",") if t.strip()]
        try:
            interest = create_interest(name, tags)
            print(f"Created: [{interest['id']}] {interest['display_name']}")
            print(f"  normalized name: {interest['name']}")
            print(f"  tags: {', '.join(interest['tags']) or '(none)'}")
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    def cmd_list(_args: List[str]) -> None:
        interests = list_interests()
        if not interests:
            print("No interests tracked.")
            return
        for i in interests:
            print(f"[{i['id']}] {i['display_name']} — {i['name']}")
            print(f"  tags: {', '.join(i['tags']) or '(none)'} | occurrences: {i['occurrence_count']} | created: {i['created_at']}")

    def cmd_show(args: List[str]) -> None:
        if not args:
            print("Usage: interest_tracker.py show <id_or_name>")
            sys.exit(1)
        interest = get_interest(args[0])
        if not interest:
            print(f"Interest not found: {args[0]}")
            sys.exit(1)
        print(f"[{interest['id']}] {interest['display_name']}")
        print(f"  normalized name: {interest['name']}")
        print(f"  status: {interest['status']}")
        print(f"  tags: {', '.join(interest['tags']) or '(none)'}")
        print(f"  occurrence_count: {interest['occurrence_count']}")
        print(f"  created_at: {interest['created_at']}")
        print(f"  last_seen_at: {interest['last_seen_at']}")
        print(f"  occurrences: {len(interest.get('occurrences', []))} entries")
        for occ in interest.get("occurrences", []):
            print(f"    [{occ['type']}] {occ['item_id']} — {occ['triggered_at']}")
            if occ.get("reason"):
                print(f"      reason: {occ['reason']}")

    def cmd_add_occurrence(args: List[str]) -> None:
        if len(args) < 3:
            print("Usage: interest_tracker.py add-occurrence <interest_id> <type> <item_id> [reason]")
            sys.exit(1)
        interest_id = args[0]
        occ_type = args[1]
        item_id = args[2]
        reason = args[3] if len(args) > 3 else ""
        try:
            interest = add_occurrence(interest_id, occ_type, item_id, reason)
            print(f"Added: [{interest['id']}] {interest['display_name']} — "
                  f"occurrence_count now {interest['occurrence_count']}")
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    subcommands = {
        "create": (cmd_create, "<name> [tag,tag,...]"),
        "list":   (cmd_list, ""),
        "show":   (cmd_show, "<id_or_name>"),
        "add-occurrence": (cmd_add_occurrence, "<interest_id> <type> <item_id> [reason]"),
    }
    if cmd in subcommands:
        subcommands[cmd][0](sys.argv[2:])
    else:
        print("Commands: create <name> [tags] | list | show <id_or_name> | add-occurrence <id> <type> <item_id> [reason]")