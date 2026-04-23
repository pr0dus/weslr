# thread_tracker.py — WESLR Thread Tracker v1
# Minimal thread storage layer. Additive only, reversible.
# No routing influence, no background processing, no auto-linking.

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any


# ============================================================================
# CONSTANTS
# ============================================================================

MAX_THREADS = 100
MAX_ITEMS_PER_THREAD = 200
VALID_STATES = frozenset({"active", "unresolved", "resolved", "dormant"})
VALID_ITEM_TYPES = frozenset({"artifact", "question", "suggestion", "resolution", "note"})
VALID_LINK_TYPES = frozenset({"explicit", "inferred"})
STORAGE_PATH = Path(__file__).parent / "threads.json"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ThreadItem:
    """A single item linked into a thread."""
    item_id: str
    item_type: str          # artifact | question | suggestion | resolution | note
    link_type: str          # explicit | inferred
    added_by: str           # operator | integration:<name>
    added_at: str = ""      # ISO8601 timestamp
    note: str = ""

    def __post_init__(self):
        if not self.added_at:
            self.added_at = datetime.now(timezone.utc).isoformat()


@dataclass
class Thread:
    """A named, temporally ordered sequence of linked items."""
    name: str
    id: str = ""
    state: str = "active"
    created_at: str = ""
    updated_at: str = ""
    tags: List[str] = field(default_factory=list)
    items: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if not self.id:
            self.id = f"thr-{uuid.uuid4().hex[:8]}"
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Thread":
        return Thread(
            id=d.get("id", ""),
            name=d.get("name", ""),
            state=d.get("state", "active"),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            tags=d.get("tags", []),
            items=d.get("items", []),
        )


# ============================================================================
# STORAGE LAYER
# ============================================================================

def _load() -> Dict[str, Any]:
    """Load threads JSON from disk. Returns {"threads": []} if missing."""
    if not STORAGE_PATH.exists():
        return {"threads": []}
    try:
        with open(STORAGE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"threads": []}


def _save(data: Dict[str, Any]) -> None:
    """Persist threads JSON to disk."""
    with open(STORAGE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ============================================================================
# CORE API
# ============================================================================

def create_thread(name: str, tags: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """
    Create a new thread with the given name.
    Returns the created thread dict, or None if the thread limit is reached.
    """
    if len(name) > 100:
        name = name[:100]

    tags = tags or []
    if len(tags) > 10:
        tags = tags[:10]

    data = _load()
    if len(data.get("threads", [])) >= MAX_THREADS:
        # Prune oldest dormant threads and retry
        data["threads"] = [
            t for t in data.get("threads", [])
            if t.get("state") != "dormant"
        ]
        if len(data.get("threads", [])) >= MAX_THREADS:
            return None  # At capacity even after pruning

    thread = Thread(name=name, tags=tags)
    data.setdefault("threads", []).append(thread.to_dict())
    _save(data)
    return thread.to_dict()


def add_item(
    thread_id: str,
    item_type: str,
    item_id: str,
    link_type: str,
    added_by: str,
    note: str = "",
) -> bool:
    """
    Add an item to a thread.
    Returns True if added, False if thread not found or item limit reached.
    """
    if item_type not in VALID_ITEM_TYPES:
        return False
    if link_type not in VALID_LINK_TYPES:
        return False

    data = _load()
    for thread in data.get("threads", []):
        if thread.get("id") == thread_id:
            items = thread.get("items", [])
            if len(items) >= MAX_ITEMS_PER_THREAD:
                # Prune oldest items
                items = items[1:]
            new_item = ThreadItem(
                item_id=item_id,
                item_type=item_type,
                link_type=link_type,
                added_by=added_by,
                note=note[:500] if note else "",
            )
            items.append(asdict(new_item))
            thread["items"] = items
            thread["updated_at"] = datetime.now(timezone.utc).isoformat()
            _save(data)
            return True
    return False


def get_thread(thread_id: str) -> Optional[Dict[str, Any]]:
    """Return the thread dict for the given ID, or None if not found."""
    data = _load()
    for thread in data.get("threads", []):
        if thread.get("id") == thread_id:
            return thread
    return None


def list_threads(
    state: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    List threads, optionally filtered by state.
    Returns up to `limit` threads sorted by updated_at descending.
    """
    data = _load()
    threads = data.get("threads", [])
    if state and state in VALID_STATES:
        threads = [t for t in threads if t.get("state") == state]
    threads.sort(key=lambda t: t.get("updated_at", ""), reverse=True)
    return threads[:limit]


def set_state(thread_id: str, new_state: str) -> bool:
    """Set the state of a thread. Returns True if updated, False if not found."""
    if new_state not in VALID_STATES:
        return False
    data = _load()
    for thread in data.get("threads", []):
        if thread.get("id") == thread_id:
            thread["state"] = new_state
            thread["updated_at"] = datetime.now(timezone.utc).isoformat()
            _save(data)
            return True
    return False


def remove_thread(thread_id: str) -> bool:
    """Remove a thread by ID. Returns True if removed, False if not found."""
    data = _load()
    original = len(data.get("threads", []))
    data["threads"] = [t for t in data.get("threads", []) if t.get("id") != thread_id]
    if len(data["threads"]) < original:
        _save(data)
        return True
    return False


def get_threads_for_item(item_id: str) -> List[Dict[str, Any]]:
    """
    Return thread reference summaries for all threads containing the given item_id.
    Read-only — does not modify threads.json.
    Returns list of dicts with: thread_id, thread_name, state, link_type, added_by, added_at
    """
    data = _load()
    refs = []
    for thread in data.get("threads", []):
        for item in thread.get("items", []):
            if item.get("item_id") == item_id:
                refs.append({
                    "thread_id": thread.get("id"),
                    "thread_name": thread.get("name"),
                    "state": thread.get("state"),
                    "link_type": item.get("link_type"),
                    "added_by": item.get("added_by"),
                    "added_at": item.get("added_at"),
                    "item_id": item.get("item_id"),
                })
    return refs


def get_thread_count() -> int:
    """Return the total number of threads."""
    data = _load()
    return len(data.get("threads", []))


def get_threads_summary() -> Dict[str, int]:
    """Return a summary of thread counts by state."""
    data = _load()
    summary: Dict[str, int] = {s: 0 for s in VALID_STATES}
    for t in data.get("threads", []):
        s = t.get("state", "active")
        if s in summary:
            summary[s] += 1
    return summary
