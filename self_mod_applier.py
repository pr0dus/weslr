# self_mod_applier.py - Apply approved self-modifications
from __future__ import annotations

import json
import time
from pathlib import Path


MOD_LOG_PATH = "self_mod_log.json"
CHECKPOINT_DIR = "checkpoints"
# LEGACY/EXPERIMENTAL: This module is NOT the canonical improvement/governance lane.
# Canonical lane: adequacy → CDI proposal (with lineage/evidence) → operator approve/deny/refine → execution eligibility (governed).
# Do not treat this file as protected-core improvement; keep it isolated/experimental.
PROTECTED_FILES = {"main.py", "sim.py", "agent_runtime.py", "llm_runtime.py", "continuity.py", "relational.py", "perception.py"}


def get_mod_log_path() -> Path:
    """Get path to self-modification log."""
    circleforge_dir = Path(__file__).parent
    return circleforge_dir / MOD_LOG_PATH


def get_checkpoint_dir() -> Path:
    """Get path to checkpoints directory."""
    circleforge_dir = Path(__file__).parent
    return circleforge_dir / CHECKPOINT_DIR


def ensure_checkpoint_dir() -> None:
    """Ensure checkpoint directory exists."""
    checkpoint_dir = get_checkpoint_dir()
    checkpoint_dir.mkdir(exist_ok=True)


def load_mod_log() -> list[dict]:
    """Load modification log."""
    log_path = get_mod_log_path()
    if not log_path.exists():
        return []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_mod_log(log: list[dict]) -> None:
    """Save modification log."""
    log_path = get_mod_log_path()
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)


def create_checkpoint(file_path: str) -> dict:
    """Create a checkpoint of the current file state."""
    ensure_checkpoint_dir()
    circleforge_dir = Path(__file__).parent
    full_path = circleforge_dir / file_path

    if not full_path.exists():
        return {"ok": False, "error": f"File not found: {full_path}"}

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {"ok": False, "error": f"Could not read file: {e}"}

    now_ts = int(time.time())
    checkpoint_name = f"{file_path.replace('/', '_').replace('.py', '')}_{now_ts}.bak"

    checkpoint_path = get_checkpoint_dir() / checkpoint_name
    try:
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        return {"ok": False, "error": f"Could not create checkpoint: {e}"}

    return {
        "ok": True,
        "file_path": file_path,
        "checkpoint_name": checkpoint_name,
        "content_length": len(content),
        "checkpoint_path": str(checkpoint_path),
        "created_at": now_ts,
    }


def log_modification(file_path: str, change: str, rationale: str, approved_by: str, success: bool, error: str = "") -> dict:
    """Log a modification to the self_mod_log.json."""
    now_ts = int(time.time())
    log_path = get_mod_log_path()

    entry = {
        "id": f"mod-{now_ts}",
        "timestamp": now_ts,
        "file_path": file_path,
        "change": change,
        "rationale": rationale,
        "approved_by": approved_by,
        "success": success,
        "error": error,
    }

    log = load_mod_log()
    log.append(entry)
    save_mod_log(log)

    return entry


def apply_modification(file_path: str, change: str, rationale: str, approved_by: str = "human") -> dict:
    """Apply an approved modification to a file."""
    # First create a checkpoint
    checkpoint = create_checkpoint(file_path)
    if not checkpoint.get("ok"):
        return checkpoint

    circleforge_dir = Path(__file__).parent
    full_path = circleforge_dir / file_path

    if not full_path.exists():
        return {"ok": False, "error": f"File not found: {full_path}"}

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            current_content = f.read()
    except Exception as e:
        return {"ok": False, "error": f"Could not read file: {e}"}

    # Apply the change (simple append for now)
    new_content = current_content + "\n" + change

    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        # Rollback on error
        try:
            with open(checkpoint.get("checkpoint_path"), "r", encoding="utf-8") as f:
                original_content = f.read()
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(original_content)
        except Exception:
            pass
        return {"ok": False, "error": f"Could not write file: {e}"}

    # Log the modification
    log_entry = log_modification(file_path, change, rationale, approved_by, True)

    return {
        "ok": True,
        "file_path": file_path,
        "change": change,
        "checkpoint": checkpoint,
        "log_entry": log_entry,
        "new_content_length": len(new_content),
        "applied_at": int(time.time()),
    }


def rollback(file_path: str, checkpoint_name: str) -> dict:
    """Roll back a file to a previous checkpoint."""
    checkpoint_path = get_checkpoint_dir() / checkpoint_name

    if not checkpoint_path.exists():
        return {"ok": False, "error": f"Checkpoint not found: {checkpoint_path}"}

    circleforge_dir = Path(__file__).parent
    full_path = circleforge_dir / file_path

    try:
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            original_content = f.read()
    except Exception as e:
        return {"ok": False, "error": f"Could not read checkpoint: {e}"}

    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(original_content)
    except Exception as e:
        return {"ok": False, "error": f"Could not write rollback: {e}"}

    return {
        "ok": True,
        "file_path": file_path,
        "checkpoint_name": checkpoint_name,
        "restored_length": len(original_content),
        "rollback_at": int(time.time()),
    }


def review_pending_modifications() -> dict:
    """Review pending modifications from the log."""
    log = load_mod_log()
    if not log:
        return {"ok": True, "pending": [], "message": "No modifications logged yet."}

    # Group by file
    by_file = {}
    for entry in log:
        file_path = entry.get("file_path", "unknown")
        if file_path not in by_file:
            by_file[file_path] = []
        by_file[file_path].append(entry)

    # Find files with pending (unapproved) modifications
    pending = []
    for file_path, entries in by_file.items():
        for entry in entries:
            if entry.get("success", False):
                # Already applied, skip
                continue
            pending.append({
                "file_path": file_path,
                "change": entry.get("change", ""),
                "rationale": entry.get("rationale", ""),
                "approved_by": entry.get("approved_by", ""),
                "created_at": entry.get("timestamp", 0),
            })

    return {
        "ok": True,
        "total_modifications": len(log),
        "by_file": {fp: len(entries) for fp, entries in by_file.items()},
        "pending": pending,
    }


def build_self_mod_report() -> dict:
    """Build a comprehensive self-modification report."""
    mod_log = load_mod_log()
    checkpoint_dir = get_checkpoint_dir()

    # Count checkpoints
    checkpoint_count = 0
    if checkpoint_dir.exists():
        checkpoint_count = len(list(checkpoint_dir.glob("*.bak")))

    # Group modifications by file
    by_file = {}
    for entry in mod_log:
        file_path = entry.get("file_path", "unknown")
        if file_path not in by_file:
            by_file[file_path] = {"applied": 0, "failed": 0}
        if entry.get("success"):
            by_file[file_path]["applied"] += 1
        else:
            by_file[file_path]["failed"] += 1

    return {
        "mod_log_path": str(get_mod_log_path()),
        "checkpoint_dir": str(checkpoint_dir),
        "total_modifications": len(mod_log),
        "checkpoints": checkpoint_count,
        "by_file": by_file,
        "last_5": mod_log[-5:] if mod_log else [],
        "generated_at": int(time.time()),
    }


def list_checkpoints(file_path: str = "") -> dict:
    """List available checkpoints, optionally filtered by file."""
    checkpoint_dir = get_checkpoint_dir()

    if not checkpoint_dir.exists():
        return {"ok": True, "checkpoints": [], "message": "No checkpoints directory exists."}

    all_checkpoints = []
    for cp in checkpoint_dir.glob("*.bak"):
        all_checkpoints.append(str(cp.name))

    # Filter by file if specified
    if file_path:
        prefix = file_path.replace("/", "_").replace(".py", "")
        all_checkpoints = [c for c in all_checkpoints if c.startswith(prefix)]

    # Sort by timestamp (newest first)
    all_checkpoints.sort(reverse=True)

    return {
        "ok": True,
        "file_path": file_path,
        "checkpoints": all_checkpoints[:20],  # Limit to 20
        "total": len(all_checkpoints),
        "generated_at": int(time.time()),
    }
