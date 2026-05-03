"""
Action Runner Dummy — dry-run stub for approved actions.

Logs what would be executed without making any actual changes.
This demonstrates the execution pattern while keeping side effects at zero.

Real execution hook: integrate with OpenClaw tool runner or direct hardware control
in a future phase (requires WESLR_ACTION_EXECUTION_ENABLED=true and operator approval).
"""
from __future__ import annotations

import json
import os
import pathlib
from datetime import datetime, timezone
from typing import Any, Dict

from weslr.action_proposals import (
    _STATUS_APPROVED,
    _STATUS_EXECUTED,
    list_approved_actions,
    mark_executed,
)

_ENABLED = os.environ.get("WESLR_ACTION_EXECUTION_ENABLED", "false").lower() in ("true", "1", "yes")
_DRY_RUN_LOG = ".weslr/action_runner_dry_run.jsonl"


def run_approved_actions() -> Dict[str, Any]:
    """Process all approved-but-not-executed actions in dry-run mode.

    When WESLR_ACTION_EXECUTION_ENABLED=true, logs what would be executed.
    When false (default), only logs to dry_run log — no side effects.

    Returns dict with executed_count, dry_run_count, log_path.
    """
    approved = list_approved_actions()
    if not approved:
        return {"executed_count": 0, "dry_run_count": 0, "message": "No approved actions pending."}

    executed = 0
    dry_run = 0

    for action in approved:
        action_id = action.get("action_id", "?")
        action_type = action.get("action_type", "?")
        params = action.get("params", {})
        description = action.get("description", "")

        # Simulate execution based on action type
        result = _simulate_action(action_type, params, description)
        result["action_id"] = action_id
        result["dry_run"] = not _ENABLED

        # Log to dry-run log regardless
        _log_dry_run(result)

        if _ENABLED:
            # Real execution would happen here
            # For now, just mark as executed
            mark_executed(action_id)
            executed += 1
        else:
            # No execution — just log
            dry_run += 1

    return {
        "executed_count": executed,
        "dry_run_count": dry_run,
        "log_path": _DRY_RUN_LOG,
        "message": (
            f"Processed {len(approved)} approved action(s): "
            f"{executed} executed, {dry_run} logged as dry-run. "
            f"Set WESLR_ACTION_EXECUTION_ENABLED=true to enable real execution."
        ),
    }


def _simulate_action(action_type: str, params: Dict[str, Any], description: str) -> Dict[str, Any]:
    """Simulate execution of a single action type and return what would happen."""
    ts = datetime.now(timezone.utc).isoformat()

    if action_type == "simulation":
        return {
            "simulated": True,
            "action_type": action_type,
            "description": description,
            "params": params,
            "what_would_happen": (
                f"Run simulation job: {params.get('job_name', 'unnamed')}. "
                f"Engine: {params.get('engine', 'unknown')}. "
                f"Duration: {params.get('estimated_duration', 'unknown')}"
            ),
            "timestamp": ts,
        }
    elif action_type == "email":
        to = params.get("to", "?")
        subject = params.get("subject", "")
        body = params.get("body", "")[:80] + "..." if len(params.get("body", "")) > 80 else params.get("body", "")
        return {
            "simulated": True,
            "action_type": action_type,
            "description": description,
            "what_would_happen": f"Send email to {to} with subject '{subject}'. Body preview: {body}",
            "params": params,
            "timestamp": ts,
        }
    elif action_type == "robot_move":
        target = params.get("target", "?")
        speed = params.get("speed", "normal")
        return {
            "simulated": True,
            "action_type": action_type,
            "description": description,
            "what_would_happen": f"Move robot arm to {target} at {speed} speed.",
            "params": params,
            "timestamp": ts,
        }
    elif action_type == "printer_job":
        file_path = params.get("file_path", "?")
        copies = params.get("copies", 1)
        return {
            "simulated": True,
            "action_type": action_type,
            "description": description,
            "what_would_happen": f"Print {copies} copy(ies) of '{file_path}'.",
            "params": params,
            "timestamp": ts,
        }
    elif action_type == "http_request":
        method = params.get("method", "GET")
        url = params.get("url", "?")
        return {
            "simulated": True,
            "action_type": action_type,
            "description": description,
            "what_would_happen": f"{method} request to {url}.",
            "params": params,
            "timestamp": ts,
        }
    elif action_type == "shell_command":
        cmd = params.get("command", "")
        return {
            "simulated": True,
            "action_type": action_type,
            "description": description,
            "what_would_happen": f"Execute shell command: {cmd}",
            "params": params,
            "timestamp": ts,
            "warning": "shell_command requires WESLR_ACTION_EXECUTION_ENABLED=true",
        }
    else:
        return {
            "simulated": False,
            "action_type": action_type,
            "description": description,
            "what_would_happen": "Unknown action type — no-op.",
            "params": params,
            "timestamp": ts,
        }


def _log_dry_run(result: Dict[str, Any]) -> None:
    """Append a dry-run result to the JSONL log."""
    log_path = pathlib.Path(_DRY_RUN_LOG)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")


def is_execution_enabled() -> bool:
    """Return True if real action execution is enabled (requires explicit opt-in)."""
    return _ENABLED