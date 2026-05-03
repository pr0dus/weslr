"""
WESLR Project Registry V1

Append-only project registry for scoping facts and entity timelines.
Each project has a stable project_id (PRJ-YYYYMMDD-NNN format).

Storage: .weslr/project_registry.jsonl
Authority: project_registry_only

Rules:
    - No raw prompts stored, no hidden learning, no automatic execution
    - Projects are append-only; deletion is out of scope for V1
    - Active project stored in-memory per session_id
"""

from __future__ import annotations

import json
import pathlib
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

DEFAULT_REGISTRY_PATH = ".weslr/project_registry.jsonl"

# In-memory store for active project per session_id
# Key: session_id (str) → value: project_id (str)
_ACTIVE_PROJECT_STORE: Dict[str, str] = {}


# ──────────────────────────────────────────────────────────────────────────────
# Normalization helpers
# ──────────────────────────────────────────────────────────────────────────────

def _normalize_project_name(name: str) -> str:
    """Normalize project name to lowercase safe identifier."""
    if not name or not isinstance(name, str):
        return ""
    normalized = name.lower().strip()
    normalized = re.sub(r"[-:_\s]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized


# ──────────────────────────────────────────────────────────────────────────────
# Register project
# ──────────────────────────────────────────────────────────────────────────────

def register_project(
    name: str,
    description: str,
    owner_user_id: str,
    registry_path: str = DEFAULT_REGISTRY_PATH,
) -> Dict[str, Any]:
    """Register a new project and write to project_registry.jsonl.

    Args:
        name: Human-readable project name
        description: Short project description
        owner_user_id: User who owns this project
        registry_path: Path to the JSONL registry

    Returns:
        dict with keys: project, path, status: "registered"

    Raises:
        ValueError: If name is empty or project with same name+owner exists
    """
    if not name or not isinstance(name, str) or not name.strip():
        raise ValueError("project name is required")

    name = name.strip()
    normalized_name = _normalize_project_name(name)
    owner = owner_user_id.strip()

    # Check for duplicate name for same owner
    existing = _find_project_by_name(name, owner, registry_path=registry_path)
    if existing:
        raise ValueError(f"project '{name}' already exists for owner '{owner}'")

    # Generate project_id: PRJ-YYYYMMDD-NNN
    project_id = _generate_project_id(registry_path)

    event = {
        "record_type": "project_registration_v1",
        "project_id": project_id,
        "name": name,
        "normalized_name": normalized_name,
        "description": description.strip() if description else "",
        "owner_user_id": owner,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authority": "project_registry_only",
        "automatic_action": False,
        "hidden_learning": False,
        "raw_prompt_stored": False,
    }

    path = pathlib.Path(registry_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    line = json.dumps(event, ensure_ascii=False)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    return {"project": event, "path": str(path), "status": "registered"}


def _generate_project_id(registry_path: str) -> str:
    """Generate next PRJ-YYYYMMDD-NNN ID."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"PRJ-{date_str}-"

    # Count existing entries for today
    count = 0
    path = pathlib.Path(registry_path)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        pid = rec.get("project_id", "")
                        if pid.startswith(prefix):
                            num = int(pid[len(prefix):])
                            count = max(count, num)
                    except Exception:
                        continue
        except Exception:
            pass

    return f"{prefix}{count + 1:03d}"


def _find_project_by_name(
    name: str,
    owner: str,
    registry_path: str,
) -> Optional[Dict[str, Any]]:
    """Find a project by name and owner. Returns None if not found."""
    path = pathlib.Path(registry_path)
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("name") == name and rec.get("owner_user_id") == owner:
                        return rec
                except Exception:
                    continue
    except Exception:
        pass
    return None


# ──────────────────────────────────────────────────────────────────────────────
# List projects
# ──────────────────────────────────────────────────────────────────────────────

def list_projects(
    owner_user_id: Optional[str] = None,
    registry_path: str = DEFAULT_REGISTRY_PATH,
) -> List[Dict[str, Any]]:
    """List all projects, optionally filtered by owner.

    Args:
        owner_user_id: If set, only return projects owned by this user
        registry_path: Path to the JSONL registry

    Returns:
        List of project dicts, most recent first
    """
    path = pathlib.Path(registry_path)
    if not path.exists():
        return []

    results: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if owner_user_id and rec.get("owner_user_id") != owner_user_id:
                        continue
                    results.append(rec)
                except Exception:
                    continue
    except Exception:
        return []

    return list(reversed(results))


# ──────────────────────────────────────────────────────────────────────────────
# Get project
# ──────────────────────────────────────────────────────────────────────────────

def get_project(
    project_id: str,
    registry_path: str = DEFAULT_REGISTRY_PATH,
) -> Optional[Dict[str, Any]]:
    """Get a single project by project_id. Returns None if not found."""
    path = pathlib.Path(registry_path)
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("project_id") == project_id:
                        return rec
                except Exception:
                    continue
    except Exception:
        pass
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Active project management
# ──────────────────────────────────────────────────────────────────────────────

def set_active_project(
    project_id: str,
    session_id: str,
    registry_path: str = DEFAULT_REGISTRY_PATH,
) -> Dict[str, Any]:
    """Set the active project for a given session.

    Args:
        project_id: The project to set as active
        session_id: The session identifier
        registry_path: Path to the project registry

    Returns:
        dict with keys: project_id, session_id, status
    """
    # Validate project exists
    project = get_project(project_id, registry_path=registry_path)
    if not project:
        return {"project_id": project_id, "session_id": session_id, "status": "not_found"}

    _ACTIVE_PROJECT_STORE[session_id] = project_id
    return {
        "project_id": project_id,
        "session_id": session_id,
        "project_name": project.get("name", ""),
        "status": "active",
    }


def get_active_project(session_id: str) -> Optional[str]:
    """Get the active project_id for a session, or None if not set."""
    return _ACTIVE_PROJECT_STORE.get(session_id)


def clear_active_project(session_id: str) -> None:
    """Clear the active project for a session."""
    _ACTIVE_PROJECT_STORE.pop(session_id, None)