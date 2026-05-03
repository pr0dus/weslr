"""
Action Proposals — safe external action stubbing (operator-approved only).

Provides a safe, operator-approved mechanism to propose external actions.
No execution occurs without explicit operator approval.

Action types: simulation, email, robot_move, printer_job, http_request, shell_command
shell_command is disabled by default and requires WESLR_ACTION_EXECUTION_ENABLED=true.
"""
from __future__ import annotations

import json
import os
import pathlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_APPROVED_ACTION_TYPES = {"simulation", "email", "robot_move", "printer_job", "http_request"}

# shell_command requires extra flag
_SHELL_COMMAND_ENABLED = os.environ.get("WESLR_ACTION_EXECUTION_ENABLED", "false").lower() in (
    "true", "1", "yes"
)
if _SHELL_COMMAND_ENABLED:
    _APPROVED_ACTION_TYPES.add("shell_command")

_ACTION_LOG_PATH = ".weslr/action_proposals.jsonl"
_STATUS_PENDING = "pending_approval"
_STATUS_APPROVED = "approved"
_STATUS_REJECTED = "rejected"
_STATUS_EXECUTED = "executed"


def propose_action(
    action_type: str,
    params: Dict[str, Any],
    description: str,
) -> Dict[str, Any]:
    """Propose a new action for operator approval.

    Args:
        action_type: one of simulation, email, robot_move, printer_job, http_request
        params: dict of action-specific parameters
        description: human-readable description of the proposed action

    Returns:
        dict with status, action_id, message
    """
    if action_type not in _APPROVED_ACTION_TYPES:
        return {
            "status": "error",
            "action_id": None,
            "message": f"Unknown action type '{action_type}'. "
                        f"Available: {', '.join(sorted(_APPROVED_ACTION_TYPES))}",
        }

    action_id = f"act_{uuid.uuid4().hex[:12]}"
    ts = datetime.now(timezone.utc).isoformat()

    entry = {
        "record_type": "action_proposal_v1",
        "action_id": action_id,
        "action_type": action_type,
        "description": description,
        "params": params,
        "status": _STATUS_PENDING,
        "proposed_at": ts,
        "proposed_by": "weslr_agent",
        "automatic_change": False,
        "hidden_learning": False,
        "raw_prompt_stored": False,
    }

    # Append-only log
    log_path = pathlib.Path(_ACTION_LOG_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return {
        "status": "pending",
        "action_id": action_id,
        "message": f"Action proposed: [{action_type}] {description} — awaiting operator approval.",
    }


def list_pending_actions() -> List[Dict[str, Any]]:
    """Return all pending action proposals."""
    return _load_actions_by_status(_STATUS_PENDING)


def list_approved_actions() -> List[Dict[str, Any]]:
    """Return all approved (not yet executed) action proposals."""
    return _load_actions_by_status(_STATUS_APPROVED)


def approve_action(action_id: str) -> Dict[str, Any]:
    """Approve a pending action proposal.

    Returns dict with status and message.
    """
    return _update_status(action_id, _STATUS_APPROVED)


def reject_action(action_id: str) -> Dict[str, Any]:
    """Reject a pending action proposal.

    Returns dict with status and message.
    """
    return _update_status(action_id, _STATUS_REJECTED)


def mark_executed(action_id: str) -> Dict[str, Any]:
    """Mark an approved action as executed.

    Returns dict with status and message.
    """
    return _update_status(action_id, _STATUS_EXECUTED)


def _load_actions_by_status(target_status: str) -> List[Dict[str, Any]]:
    """Load all actions with a given status."""
    log_path = pathlib.Path(_ACTION_LOG_PATH)
    if not log_path.exists():
        return []

    results: List[Dict[str, Any]] = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("status") == target_status:
                    results.append(rec)
    except OSError:
        pass
    return results


def _update_status(action_id: str, new_status: str) -> Dict[str, Any]:
    """Update the status of an action proposal.

    Appends a new status-change event to the log rather than modifying the existing record.
    Returns dict with status, action_id, message.
    """
    log_path = pathlib.Path(_ACTION_LOG_PATH)
    if not log_path.exists():
        return {"status": "error", "action_id": action_id, "message": "Action log not found."}

    # Check if the action exists
    action = None
    for rec in _load_all_actions():
        if rec.get("action_id") == action_id:
            action = rec
            break

    if action is None:
        return {"status": "error", "action_id": action_id, "message": f"Action '{action_id}' not found."}

    ts = datetime.now(timezone.utc).isoformat()
    status_entry = {
        "record_type": "action_status_change_v1",
        "action_id": action_id,
        "new_status": new_status,
        "changed_at": ts,
        "changed_by": "weslr_operator",
    }

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(status_entry, ensure_ascii=False) + "\n")

    status_messages = {
        _STATUS_APPROVED: f"Action {action_id} approved. Awaiting execution.",
        _STATUS_REJECTED: f"Action {action_id} rejected.",
        _STATUS_EXECUTED: f"Action {action_id} marked as executed.",
    }
    return {
        "status": "ok",
        "action_id": action_id,
        "message": status_messages.get(new_status, f"Action {action_id} status → {new_status}."),
    }


def _load_all_actions() -> List[Dict[str, Any]]:
    """Load all action proposal records from the log."""
    log_path = pathlib.Path(_ACTION_LOG_PATH)
    if not log_path.exists():
        return []

    results: List[Dict[str, Any]] = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("record_type") in ("action_proposal_v1",):
                        results.append(rec)
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return results


def get_action(action_id: str) -> Optional[Dict[str, Any]]:
    """Get a single action proposal by ID."""
    for rec in _load_all_actions():
        if rec.get("action_id") == action_id:
            return rec
    return None


def format_action_summary(action: Dict[str, Any]) -> str:
    """Format an action proposal as a readable string."""
    tid = action.get("action_id", "?")
    atype = action.get("action_type", "?")
    desc = action.get("description", "")
    status = action.get("status", "?")
    proposed = action.get("proposed_at", "")
    params = action.get("params", {})
    params_str = ", ".join(f"{k}={v}" for k, v in params.items())
    return (
        f"ID: {tid}\n"
        f"  Type: {atype}\n"
        f"  Description: {desc}\n"
        f"  Params: {params_str or '(none)'}\n"
        f"  Status: {status}\n"
        f"  Proposed: {proposed}"
    )