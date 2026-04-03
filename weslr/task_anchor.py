"""Weslr Platform: Task Anchor (v1)

Weslr-native task state, portable across runtimes.
Tracks current task, status, and commit hash for trajectory preservation.

No runtime-specific dependencies.
No user-facing behavior.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


# Default paths (override via BASE_DIR parameter in functions)
DEFAULT_BASE_DIR = "/data/data/com.termux/files/home/.openclaw/workspace"
DEFAULT_CONTINUITY_DIR = "continuity"
TASK_ANCHOR_FILE = "task_anchor.json"


def get_paths(base_dir: str = None) -> tuple[str, str, str]:
    """Get task anchor paths, configurable via base_dir."""
    base_dir = base_dir or DEFAULT_BASE_DIR
    continuity_dir = os.path.join(base_dir, DEFAULT_CONTINUITY_DIR)
    task_anchor_path = os.path.join(continuity_dir, TASK_ANCHOR_FILE)
    return base_dir, continuity_dir, task_anchor_path


# ===== MINIMUM TASK ANCHOR SCHEMA =====

# Required fields (Weslr-native)
# task_name: string (current task description)
# task_status: "in_progress" | "pending" | "completed"
# last_commit_hash: string (HEAD hash for verification)
# last_updated_at: ISO timestamp (freshness signal)

# Optional fields
# task_description: string (extended description)
# current_step: string (current position in task)
# priority: "low" | "medium" | "high"
# related_context: dict with commit_range, open_issues


def load_task_anchor(base_dir: str = None) -> Dict[str, Any]:
    """Load task anchor from continuity/task_anchor.json."""
    _, _, task_anchor_path = get_paths(base_dir)
    try:
        with open(task_anchor_path) as f:
            return json.load(f)
    except Exception:
        return {}


def save_task_anchor(anchor: Dict[str, Any], base_dir: str = None) -> str:
    """Save task anchor to continuity/task_anchor.json."""
    _, continuity_dir, task_anchor_path = get_paths(base_dir)
    os.makedirs(continuity_dir, exist_ok=True)
    with open(task_anchor_path, "w") as f:
        json.dump(anchor, f, indent=2)
    return task_anchor_path


def validate_task_anchor(anchor: Dict[str, Any]) -> bool:
    """Validate task anchor has required fields."""
    required = ["task_name", "task_status", "last_commit_hash", "last_updated_at"]
    for field in required:
        if field not in anchor:
            return False
    return True


def get_required_fields() -> list[str]:
    """Return list of required task anchor fields."""
    return ["task_name", "task_status", "last_commit_hash", "last_updated_at"]


def create_task_anchor(
    task_name: str,
    task_status: str,
    last_commit_hash: str,
    base_dir: str = None,
) -> Dict[str, Any]:
    """Create a new task anchor with required fields."""
    import datetime
    anchor = {
        "task_name": task_name,
        "task_status": task_status,
        "last_commit_hash": last_commit_hash,
        "last_updated_at": datetime.datetime.utcnow().isoformat() + "Z",
    }
    return anchor


def update_task_anchor(
    anchor: Dict[str, Any],
    task_name: str = None,
    task_status: str = None,
    last_commit_hash: str = None,
    current_step: str = None,
    base_dir: str = None,
) -> Dict[str, Any]:
    """Update existing task anchor with new values."""
    import datetime
    if task_name is not None:
        anchor["task_name"] = task_name
    if task_status is not None:
        anchor["task_status"] = task_status
    if last_commit_hash is not None:
        anchor["last_commit_hash"] = last_commit_hash
    if current_step is not None:
        anchor["current_step"] = current_step
    anchor["last_updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    return anchor


def verify_task_anchor_commit(anchor: Dict[str, Any], current_commit: str) -> tuple[bool, str]:
    """Verify task anchor commit matches current HEAD."""
    anchor_commit = anchor.get("last_commit_hash")
    if anchor_commit == current_commit:
        return True, "commit matches"
    if not anchor_commit:
        return False, "no commit in anchor"
    if not current_commit:
        return False, "no current commit"
    return False, f"commit mismatch (anchor={anchor_commit}, current={current_commit})"


# ===== COMPATIBILITY: check for old paths =====

OLD_ANCHOR_PATHS = [
    "/data/data/com.termux/files/home/.openclaw/workspace/task_anchor.json",
]


def find_task_anchor(base_dir: str = None) -> Optional[str]:
    """Find task anchor in preferred or old locations."""
    # Check preferred location first
    _, _, preferred_path = get_paths(base_dir)
    if os.path.exists(preferred_path):
        return preferred_path
    # Check old paths
    for old_path in OLD_ANCHOR_PATHS:
        if os.path.exists(old_path):
            return old_path
    return None


def load_task_anchor_legacy_fallback(base_dir: str = None) -> Dict[str, Any]:
    """Load task anchor with fallback to old locations."""
    anchor = load_task_anchor(base_dir)
    if anchor:
        return anchor
    # Fallback to old path if exists
    old_path = find_task_anchor(base_dir)
    if old_path:
        try:
            with open(old_path) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


# ===== CONVENIENCE FUNCTIONS =====

def set_current_task(
    task_name: str,
    task_status: str = "in_progress",
    base_dir: str = None,
) -> Dict[str, Any]:
    """Set current task as active task anchor."""
    anchor = create_task_anchor(task_name, task_status, "", base_dir)
    save_task_anchor(anchor, base_dir)
    return anchor


def mark_task_completed(task_name: str, base_dir: str = None) -> Dict[str, Any]:
    """Mark a task as completed."""
    anchor = load_task_anchor(base_dir)
    if not anchor:
        anchor = create_task_anchor(task_name, "completed", "", base_dir)
    anchor["task_status"] = "completed"
    save_task_anchor(anchor, base_dir)
    return anchor


def get_current_task(base_dir: str = None) -> Optional[Dict[str, Any]]:
    """Get current task anchor if valid."""
    anchor = load_task_anchor(base_dir)
    if validate_task_anchor(anchor):
        return anchor
    return None


def get_current_task_name(base_dir: str = None) -> Optional[str]:
    """Get current task name if anchor exists."""
    anchor = get_current_task(base_dir)
    if anchor:
        return anchor.get("task_name")
    return None
