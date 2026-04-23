"""Weslr Artifact Store.

Minimal persistent artifact storage for SatUi feedback workflow.
Additive only, fully reversible — no production logic mutation.

This module provides:
- save_artifact(): Store an artifact with generated ID
- get_artifact(): Retrieve by artifact_id
- list_artifacts(): List recent artifacts

ARTIFACT SHAPE
{
    "artifact_id": "art-<timestamp>-<seq>",
    "created_at": "<ISO timestamp>",
    "type": "artifact_revision",
    "content": "...",
    "source": "dialogue",
    "context": {
        "input_message": "...",
        "topics": [...]
    }
}

STORAGE
- Directory: continuity/artifacts/
- One JSON file per artifact: <artifact_id>.json
- Index: continuity/artifacts/index.json (list of all artifact_ids)
"""

from __future__ import annotations

import json
import time as _time
from pathlib import Path
from typing import Any, Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "continuity" / "artifacts"
INDEX_FILE = ARTIFACTS_DIR / "index.json"


def _ensure_artifacts_dir() -> Path:
    """Ensure artifacts directory exists."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    return ARTIFACTS_DIR


def _load_index() -> List[str]:
    """Load artifact ID index."""
    if not INDEX_FILE.exists():
        return []
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_index(index: List[str]) -> None:
    """Save artifact ID index."""
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)


def _generate_artifact_id() -> str:
    """Generate a unique artifact ID."""
    now_ts = int(_time.time() * 1000)
    index = _load_index()
    seq = len([aid for aid in index if aid.startswith(f"art-{now_ts}")]) + 1
    return f"art-{now_ts}-{seq}"


def save_artifact(record: dict) -> str:
    """Save an artifact to disk and update index.

    Args:
        record: Artifact dict. Must contain at minimum:
                - type
                - content
                Optionally: source, context, parent_artifact_ids, root_artifact_id,
                generation

    Returns:
        artifact_id: The assigned artifact ID

    Raises:
        ValueError: If record is missing required fields
    """
    if not isinstance(record, dict):
        raise ValueError("record must be a dict")

    required = ["type", "content"]
    missing = [f for f in required if f not in record]
    if missing:
        raise ValueError(f"record missing required fields: {missing}")

    # Generate ID
    artifact_id = _generate_artifact_id()

    # Build lineage fields (additive — older artifacts without these load safely)
    parent_ids = record.get("parent_artifact_ids", [])
    # root_artifact_id: self if root (not provided), parent's root if derived
    root_artifact_id = record.get("root_artifact_id")
    generation = record.get("generation", 0)

    # Build artifact record
    now_iso = _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())
    artifact: dict[str, Any] = {
        "artifact_id": artifact_id,
        "created_at": now_iso,
        "type": record.get("type", "artifact_revision"),
        "content": record.get("content"),
        "source": record.get("source", "dialogue"),
        "context": record.get("context", {}),
    }

    # Always write lineage fields — explicit contract for all new artifacts.
    # Older artifacts (written before this change) load safely via .get() defaults.
    artifact["parent_artifact_ids"] = parent_ids
    artifact["root_artifact_id"] = root_artifact_id if root_artifact_id else artifact_id
    artifact["generation"] = generation

    # Save artifact file
    _ensure_artifacts_dir()
    artifact_path = ARTIFACTS_DIR / f"{artifact_id}.json"
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    # Update index
    index = _load_index()
    index.append(artifact_id)
    _save_index(index)

    return artifact_id


def get_artifact(artifact_id: str) -> Optional[dict]:
    """Retrieve an artifact by ID.

    Args:
        artifact_id: The artifact ID to look up

    Returns:
        Artifact dict or None if not found
    """
    if not artifact_id:
        return None

    artifact_path = ARTIFACTS_DIR / f"{artifact_id}.json"
    if not artifact_path.exists():
        return None

    try:
        with open(artifact_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def list_artifacts(limit: int = 50) -> list:
    """List recent artifacts, newest first.

    Args:
        limit: Maximum number of artifacts to return (default 50)

    Returns:
        List of artifact dicts (without full content for compactness)
    """
    index = _load_index()
    artifacts = []

    for artifact_id in reversed(index[-limit:]):
        artifact = get_artifact(artifact_id)
        if artifact:
            # Return compact form: strip content to save memory
            artifacts.append({
                "artifact_id": artifact.get("artifact_id"),
                "created_at": artifact.get("created_at"),
                "type": artifact.get("type"),
                "source": artifact.get("source"),
                "context": artifact.get("context", {}),
            })

    return artifacts


def search_artifacts(
    artifact_type: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
) -> list:
    """Search artifacts by type and/or source.

    Args:
        artifact_type: Filter by type (e.g., "artifact_revision")
        source: Filter by source (e.g., "dialogue")
        limit: Maximum number to return

    Returns:
        List of matching artifact dicts
    """
    index = _load_index()
    results = []

    for artifact_id in reversed(index):
        artifact = get_artifact(artifact_id)
        if not artifact:
            continue

        if artifact_type and artifact.get("type") != artifact_type:
            continue
        if source and artifact.get("source") != source:
            continue

        results.append({
            "artifact_id": artifact.get("artifact_id"),
            "created_at": artifact.get("created_at"),
            "type": artifact.get("type"),
            "source": artifact.get("source"),
            "context": artifact.get("context", {}),
        })

        if len(results) >= limit:
            break

    return results


# =============================================================================
# ACTIVE ARTIFACT REGISTRY
# =============================================================================

REGISTRY_FILE = BASE_DIR / "continuity" / "active_artifact_registry.json"


def _load_registry() -> dict:
    """Load active artifact registry."""
    if not REGISTRY_FILE.exists():
        return {}
    try:
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_registry(registry: dict) -> None:
    """Save active artifact registry."""
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)


def set_active_artifact(session_id: str, artifact_id: str) -> None:
    """Set the active artifact for a session.

    Args:
        session_id: The session ID
        artifact_id: The artifact ID to set as active
    """
    registry = _load_registry()
    registry[session_id] = {
        "current_artifact_id": artifact_id,
        "last_updated": int(_time.time() * 1000),
    }
    _save_registry(registry)


def get_active_artifact(session_id: str) -> Optional[str]:
    """Get the active artifact ID for a session.

    Args:
        session_id: The session ID

    Returns:
        artifact_id or None if no active artifact
    """
    registry = _load_registry()
    entry = registry.get(session_id)
    if not entry:
        return None
    return entry.get("current_artifact_id")


def clear_active_artifact(session_id: str) -> None:
    """Clear the active artifact for a session."""
    registry = _load_registry()
    if session_id in registry:
        del registry[session_id]
        _save_registry(registry)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python artifact_store.py <command> [args]")
        print("Commands:")
        print("  save <type> <content>")
        print("  get <artifact_id>")
        print("  list [limit]")
        print("  registry-get <session_id>")
        print("  registry-set <session_id> <artifact_id>")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "save" and len(sys.argv) >= 4:
        artifact_type = sys.argv[2]
        content = " ".join(sys.argv[3:])
        artifact_id = save_artifact({
            "type": artifact_type,
            "content": content,
            "source": "cli",
        })
        print(f"Saved: {artifact_id}")

    elif cmd == "get" and len(sys.argv) >= 3:
        artifact = get_artifact(sys.argv[2])
        if artifact:
            print(json.dumps(artifact, indent=2))
        else:
            print("Not found")

    elif cmd == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        artifacts = list_artifacts(limit)
        print(json.dumps(artifacts, indent=2))

    elif cmd == "registry-get" and len(sys.argv) >= 3:
        aid = get_active_artifact(sys.argv[2])
        print(aid if aid else "None")

    elif cmd == "registry-set" and len(sys.argv) >= 4:
        set_active_artifact(sys.argv[2], sys.argv[3])
        print("OK")

    else:
        print("Unknown command or missing args")
        sys.exit(1)
