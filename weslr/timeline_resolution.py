"""
weslr/timeline_resolution.py
=============================
Timeline-Native Continuity Resolution — V1 (First Safe Slice)

Thread-aware resolution layer on top of existing artifact persistence.
Implements the smallest safe first slice from:
  docs/TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md

This module is additive only — no runtime behavior changes,
no routing changes, no scoring changes, no governance changes.
Fully reversible: removal of this file restores prior state.

THIS SLICE ONLY:
  - thread-aware resolution for "this" / "improve this" / "explain this"
  - active thread registry per user
  - artifact linked to active thread on creation
  - fallback to existing session-keyed registry

NOT YET IMPLEMENTED (future slices):
  - lineage chain tracking
  - timeline event fallback
  - institution/role authorization scope

RESOLUTION CASCADE (this slice):
  Level 1: Active thread → most recent artifact in active thread
  Level 2: Existing session-keyed registry fallback
  Level 3: Safe no-resolution (no crash, safe empty message)

NO MODIFICATIONS TO:
  - weslr/artifact_store.py
  - dialogue.py
  - weslr/thread_tracker.py (read-only usage)
  - weslr/threads.json schema
  - interests.json
  - threads.json
  - any routing or governance module
"""

from __future__ import annotations

import json
import sys
import time as _time
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Ensure workspace on path for dialogue/thread_tracker/artifact_store ─────
_BASE = Path(__file__).resolve().parent.parent
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))


# ============================================================================
# PATH CONSTANTS
# ============================================================================

CONTINUITY_DIR = _BASE / "continuity"
ACTIVE_THREAD_REGISTRY_FILE = CONTINUITY_DIR / "active_thread_registry.json"


# ============================================================================
# ACTIVE THREAD REGISTRY — per-user active thread pointer
# ============================================================================
# Additive storage: does not modify threads.json schema.
# New file: continuity/active_thread_registry.json
# Schema:
#   {
#     "active_threads": {
#       "<user_id>": {
#         "thread_id": "<thread_id>",
#         "thread_name": "<thread_name>",
#         "set_at": "<ISO timestamp>",
#       }
#     }
#   }

def _ensure_dir() -> None:
    CONTINUITY_DIR.mkdir(parents=True, exist_ok=True)


def _load_active_thread_registry() -> Dict[str, Any]:
    """Load active thread registry. Returns empty structure if missing."""
    _ensure_dir()
    if not ACTIVE_THREAD_REGISTRY_FILE.exists():
        return {"active_threads": {}}
    try:
        with open(ACTIVE_THREAD_REGISTRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"active_threads": {}}


def _save_active_thread_registry(data: Dict[str, Any]) -> None:
    """Save active thread registry."""
    _ensure_dir()
    with open(ACTIVE_THREAD_REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ============================================================================
# ACTIVE THREAD MANAGEMENT
# ============================================================================

def set_active_thread(user_id: str, thread_id: str, thread_name: str = "") -> bool:
    """Set the active thread for a user.

    Args:
        user_id: The user/operator identifier
        thread_id: The thread ID to set as active
        thread_name: Human-readable thread name (optional, for metadata)

    Returns:
        True if set successfully, False otherwise
    """
    if not user_id or not thread_id:
        return False

    # Validate thread exists in thread_tracker
    try:
        from weslr.thread_tracker import get_thread
        thread = get_thread(thread_id)
        if not thread:
            return False
        if not thread_name:
            thread_name = thread.get("name", "")
    except Exception:
        return False

    data = _load_active_thread_registry()
    data["active_threads"][user_id] = {
        "thread_id": thread_id,
        "thread_name": thread_name,
        "set_at": _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()),
    }
    _save_active_thread_registry(data)
    return True


def get_active_thread(user_id: str) -> Optional[Dict[str, str]]:
    """Get the active thread info for a user.

    Args:
        user_id: The user/operator identifier

    Returns:
        Dict with thread_id and thread_name, or None if no active thread
    """
    if not user_id:
        return None
    data = _load_active_thread_registry()
    entry = data.get("active_threads", {}).get(user_id)
    if not entry:
        return None
    return {
        "thread_id": entry.get("thread_id"),
        "thread_name": entry.get("thread_name", ""),
    }


def clear_active_thread(user_id: str) -> bool:
    """Clear the active thread for a user (no active thread = thread-neutral)."""
    if not user_id:
        return False
    data = _load_active_thread_registry()
    if user_id in data.get("active_threads", {}):
        del data["active_threads"][user_id]
        _save_active_thread_registry(data)
    return True


# ============================================================================
# ARTIFACT RESOLUTION
# ============================================================================

def _get_latest_artifact_in_thread(thread_id: str) -> Optional[Dict[str, Any]]:
    """Get the most recent artifact item in a thread.

    Returns:
        artifact dict with artifact_id and content, or None if no artifacts in thread
    """
    try:
        from weslr.thread_tracker import get_thread
        thread = get_thread(thread_id)
        if not thread:
            return None

        items = thread.get("items", [])
        # Find all artifact items, last one is most recent
        artifact_items = [item for item in reversed(items) if item.get("item_type") == "artifact"]
        if not artifact_items:
            return None

        latest = artifact_items[0]
        artifact_id = latest.get("item_id")

        if not artifact_id:
            return None

        # Retrieve the artifact from artifact store
        try:
            from weslr.artifact_store import get_artifact
            artifact = get_artifact(artifact_id)
            return artifact
        except Exception:
            return None

    except Exception:
        return None


def _get_registry_fallback(user_id: str) -> Optional[str]:
    """Get active artifact from existing session-keyed registry (fallback).

    Returns:
        artifact_id or None
    """
    try:
        from weslr.artifact_store import get_active_artifact
        return get_active_artifact(user_id)
    except Exception:
        return None


def _contamination_check(artifact: Dict[str, Any]) -> bool:
    """Check artifact for obvious contamination signals.

    Returns True if clean (no contamination detected), False otherwise.
    This is a lightweight heuristic check — not a full domain analysis.
    """
    if not artifact:
        return False

    content = str(artifact.get("content", ""))
    context = artifact.get("context", {})

    # Heuristic: if content is empty and this was supposedly a generation artifact, flag
    if not content and context.get("artifact_lifecycle_stage") == "generation":
        return False

    return True


# ============================================================================
# MAIN RESOLUTION FUNCTION
# ============================================================================

def resolve_active_artifact_for_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Resolve the active artifact for a user using thread-aware cascade.

    Resolution order:
      1. Active thread → most recent artifact in active thread
      2. Registry fallback → existing session-keyed active artifact registry
      3. None → no candidate found

    Args:
        user_id: The user/operator identifier

    Returns:
        Resolution metadata dict with keys:
          - resolved_artifact_id: str or None
          - resolution_path: "active_thread" | "registry_fallback" | "none"
          - thread_id: str or None
          - thread_name: str or None
          - confidence: "high" | "medium" | "none"
          - artifact_content: str or None (content if available)
          - contamination_check: bool (True = clean)
          - note: str
        Returns None only if called incorrectly (no user_id).
    """
    if not user_id:
        return None

    # ── Level 1: Active thread ────────────────────────────────────────────
    active_thread = get_active_thread(user_id)
    if active_thread:
        thread_id = active_thread["thread_id"]
        thread_name = active_thread["thread_name"]

        artifact = _get_latest_artifact_in_thread(thread_id)
        if artifact and artifact.get("artifact_id"):
            contamination = _contamination_check(artifact)
            return {
                "resolved_artifact_id": artifact["artifact_id"],
                "resolution_path": "active_thread",
                "thread_id": thread_id,
                "thread_name": thread_name,
                "confidence": "high",
                "artifact_content": artifact.get("content"),
                "contamination_check": contamination,
                "note": f"Resolved from active thread '{thread_name}'",
            }

    # ── Level 2: Registry fallback ────────────────────────────────────────
    registry_artifact_id = _get_registry_fallback(user_id)
    if registry_artifact_id:
        try:
            from weslr.artifact_store import get_artifact
            artifact = get_artifact(registry_artifact_id)
            if artifact:
                contamination = _contamination_check(artifact)
                return {
                    "resolved_artifact_id": registry_artifact_id,
                    "resolution_path": "registry_fallback",
                    "thread_id": active_thread["thread_id"] if active_thread else None,
                    "thread_name": active_thread["thread_name"] if active_thread else None,
                    "confidence": "medium",
                    "artifact_content": artifact.get("content"),
                    "contamination_check": contamination,
                    "note": "Resolved from session-keyed registry fallback",
                }
        except Exception:
            pass

    # ── Level 3: No candidate ────────────────────────────────────────────
    return {
        "resolved_artifact_id": None,
        "resolution_path": "none",
        "thread_id": None,
        "thread_name": None,
        "confidence": "none",
        "artifact_content": None,
        "contamination_check": True,
        "note": "No active artifact found for this user",
    }


# ============================================================================
# THREAD LINKING — add artifact to active thread on creation
# ============================================================================

def link_artifact_to_active_thread(user_id: str, artifact_id: str) -> bool:
    """Link an artifact to the user's active thread, if one exists.

    This is called by the artifact creation flow (additive integration point).
    Does nothing if no active thread is set for this user.

    Args:
        user_id: The user/operator identifier
        artifact_id: The artifact ID to link

    Returns:
        True if linked, False if no active thread or thread not found
    """
    if not user_id or not artifact_id:
        return False

    active_thread = get_active_thread(user_id)
    if not active_thread:
        return False

    thread_id = active_thread["thread_id"]

    try:
        from weslr.thread_tracker import add_item
        return add_item(
            thread_id=thread_id,
            item_type="artifact",
            item_id=artifact_id,
            link_type="explicit",
            added_by="timeline_resolution",
            note="Linked via timeline_resolution active thread",
        )
    except Exception:
        return False


# ============================================================================
# UTILITY — check if user has any continuity at all
# ============================================================================

def has_continuity(user_id: str) -> bool:
    """Check if user has any continuity object (active thread or registry artifact).

    Useful for SatUi to show whether a user has ongoing work.
    """
    if not user_id:
        return False

    active_thread = get_active_thread(user_id)
    if active_thread:
        thread_id = active_thread["thread_id"]
        artifact = _get_latest_artifact_in_thread(thread_id)
        if artifact:
            return True

    registry_artifact_id = _get_registry_fallback(user_id)
    if registry_artifact_id:
        try:
            from weslr.artifact_store import get_artifact
            artifact = get_artifact(registry_artifact_id)
            if artifact:
                return True
        except Exception:
            pass

    return False


def get_continuity_status(user_id: str) -> Dict[str, Any]:
    """Get a full continuity status snapshot for a user.

    Returns dict with:
      - has_active_thread: bool
      - active_thread_id: str or None
      - active_thread_name: str or None
      - has_artifact_in_thread: bool
      - has_registry_artifact: bool
      - resolved_artifact_id: str or None
      - resolution_path: str
      - confidence: str
    """
    if not user_id:
        return {
            "has_active_thread": False,
            "active_thread_id": None,
            "active_thread_name": None,
            "has_artifact_in_thread": False,
            "has_registry_artifact": False,
            "resolved_artifact_id": None,
            "resolution_path": "none",
            "confidence": "none",
        }

    active_thread = get_active_thread(user_id)
    has_active = active_thread is not None
    thread_id = active_thread["thread_id"] if active_thread else None
    thread_name = active_thread["thread_name"] if active_thread else None

    has_in_thread = False
    if thread_id:
        artifact = _get_latest_artifact_in_thread(thread_id)
        has_in_thread = artifact is not None

    registry_artifact_id = _get_registry_fallback(user_id)
    has_registry = False
    if registry_artifact_id:
        try:
            from weslr.artifact_store import get_artifact
            has_registry = get_artifact(registry_artifact_id) is not None
        except Exception:
            has_registry = False

    resolution = resolve_active_artifact_for_user(user_id)

    return {
        "has_active_thread": has_active,
        "active_thread_id": thread_id,
        "active_thread_name": thread_name,
        "has_artifact_in_thread": has_in_thread,
        "has_registry_artifact": has_registry,
        "resolved_artifact_id": resolution.get("resolved_artifact_id") if resolution else None,
        "resolution_path": resolution.get("resolution_path", "none") if resolution else "none",
        "confidence": resolution.get("confidence", "none") if resolution else "none",
    }


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python timeline_resolution.py <command> [args]")
        print("Commands:")
        print("  set-active <user_id> <thread_id> [thread_name]")
        print("  get-active <user_id>")
        print("  clear-active <user_id>")
        print("  resolve <user_id>")
        print("  link <user_id> <artifact_id>")
        print("  status <user_id>")
        print("  has-continuity <user_id>")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "set-active" and len(sys.argv) >= 4:
        user_id = sys.argv[2]
        thread_id = sys.argv[3]
        thread_name = sys.argv[4] if len(sys.argv) > 4 else ""
        ok = set_active_thread(user_id, thread_id, thread_name)
        print(f"OK={ok}")

    elif cmd == "get-active" and len(sys.argv) >= 3:
        user_id = sys.argv[2]
        result = get_active_thread(user_id)
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("None")

    elif cmd == "clear-active" and len(sys.argv) >= 3:
        user_id = sys.argv[2]
        ok = clear_active_thread(user_id)
        print(f"OK={ok}")

    elif cmd == "resolve" and len(sys.argv) >= 3:
        user_id = sys.argv[2]
        result = resolve_active_artifact_for_user(user_id)
        print(json.dumps(result, indent=2))

    elif cmd == "link" and len(sys.argv) >= 4:
        user_id = sys.argv[2]
        artifact_id = sys.argv[3]
        ok = link_artifact_to_active_thread(user_id, artifact_id)
        print(f"OK={ok}")

    elif cmd == "status" and len(sys.argv) >= 3:
        user_id = sys.argv[2]
        result = get_continuity_status(user_id)
        print(json.dumps(result, indent=2))

    elif cmd == "has-continuity" and len(sys.argv) >= 3:
        user_id = sys.argv[2]
        print("true" if has_continuity(user_id) else "false")

    else:
        print("Unknown command or missing arguments")
        sys.exit(1)