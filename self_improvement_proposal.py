"""Weslr Self-Improvement Proposal Layer.

Creates, lists, and manages improvement proposals.
Handles human approval workflow for safe bounded evolution.
Phase 1B: Added test prompts, expected outputs, rollback commands, and patch plans.
"""

from __future__ import annotations

import json
import time
from pathlib import Path


PROPOSALS_FILE = "self_improvement_proposals.json"
APPROVAL_LOG_FILE = "self_improvement_approval_log.json"
BASE_DIR = Path(__file__).resolve().parent


def get_proposals_path() -> Path:
    """Get path to proposals storage file."""
    return BASE_DIR / PROPOSALS_FILE


def get_approval_log_path() -> Path:
    """Get path to approval log storage file."""
    return BASE_DIR / APPROVAL_LOG_FILE


def load_proposals() -> list[dict]:
    """Load all proposals from storage."""
    path = get_proposals_path()
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_proposals(proposals: list[dict]) -> None:
    """Save proposals to storage."""
    path = get_proposals_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(proposals, f, indent=2)


def load_approval_log() -> list[dict]:
    """Load approval log from storage."""
    path = get_approval_log_path()
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_approval_log(log: list[dict]) -> None:
    """Save approval log to storage."""
    path = get_approval_log_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)


def is_protected_file(filepath: str) -> bool:
    """Check if a file is protected from modification."""
    from self_modifier import is_protected_file as check
    return check(filepath)


def create_proposal(
    observation_ids: list[str],
    title: str,
    problem: str,
    likely_cause: str,
    files_to_change: list[str],
    expected_benefit: str,
    risk_level: str = "low",
    test_prompts: list[dict] | None = None,
    expected_outputs: list[dict] | None = None,
    rollback_command: str | None = None,
    patch_plan: dict | None = None,
    test_exempt: bool = False,
    test_exempt_justification: str | None = None,
) -> dict:
    """Create a new improvement proposal.

    Args:
        observation_ids: List of observation IDs this proposal addresses
        title: Short description of the fix
        problem: Detailed problem description
        likely_cause: Root cause analysis
        files_to_change: List of files to modify
        expected_benefit: Expected improvement
        risk_level: low | medium | high (default: low)
        test_prompts: List of test prompts with expected outputs (Phase 1B)
        expected_outputs: List of expected output specifications (Phase 1B)
        rollback_command: Shell command to rollback change (Phase 1B)
        patch_plan: Optional dry-run patch plan (Phase 1B)

    Returns:
        dict with proposal details or error
    """
    allowed_risk_levels = ["low", "medium", "high"]
    if risk_level not in allowed_risk_levels:
        return {
            "ok": False,
            "error": f"Invalid risk_level. Must be one of: {allowed_risk_levels}",
        }

    # Check if any file is protected
    protected_files = []
    for filepath in files_to_change:
        if is_protected_file(filepath):
            protected_files.append(filepath)

    if protected_files:
        return {
            "ok": False,
            "error": f"Protected files cannot be modified in Phase 1A: {protected_files}",
            "protected_files": protected_files,
        }

    now_ts = int(time.time() * 1000)  # Use milliseconds for uniqueness
    proposal_id = f"prop-{now_ts}-{len(load_proposals())}"  # Append count to ensure uniqueness

    proposal = {
        "id": proposal_id,
        "observation_ids": observation_ids,
        "title": title,
        "problem": problem,
        "likely_cause": likely_cause,
        "files_to_change": files_to_change,
        "expected_benefit": expected_benefit,
        "risk_level": risk_level,
        "created_at": now_ts,
        "status": "proposed",
        "approval": {
            "requested_at": now_ts,
            "approved_by": None,
            "approved_at": None,
            "denied_at": None,
            "denial_reason": None,
        },
        # Phase 1B additions
        "test_prompts": test_prompts or [],
        "expected_outputs": expected_outputs or [],
        "rollback_command": rollback_command,
        "patch_plan": patch_plan,
        # Phase 1C safety additions
        "test_exempt": test_exempt,
        "test_exempt_justification": test_exempt_justification,
    }

    # Load existing, append, save
    proposals = load_proposals()
    proposals.append(proposal)
    save_proposals(proposals)

    return {
        "ok": True,
        "proposal_id": proposal_id,
        "title": title,
        "status": "status",
        "created_at": now_ts,
        "has_tests": len(test_prompts or []) > 0,
        "has_rollback": rollback_command is not None,
    }


def list_proposals(
    status: str | None = None,
    limit: int = 50,
) -> dict:
    """List proposals, optionally filtered by status.

    Args:
        status: Filter by status (proposed | approved | rejected)
        limit: Maximum results to return

    Returns:
        dict with proposals list and metadata
    """
    proposals = load_proposals()

    # Apply status filter
    if status:
        proposals = [p for p in proposals if p.get("status") == status]

    # Sort by most recent first
    proposals = sorted(proposals, key=lambda p: p.get("created_at", 0), reverse=True)

    # Apply limit
    proposals = proposals[:limit]

    return {
        "ok": True,
        "total": len(proposals),
        "limit": limit,
        "proposals": proposals,
    }


def get_proposal(proposal_id: str) -> dict | None:
    """Get a specific proposal by ID."""
    proposals = load_proposals()
    for p in proposals:
        if p.get("id") == proposal_id:
            return p
    return None


def approve_proposal(proposal_id: str, approved_by: str) -> dict:
    """Approve a proposal.

    Note: Phase 1A does NOT apply code changes.
    This only updates the proposal status to "approved".

    Args:
        proposal_id: ID of proposal to approve
        approved_by: Who approved (e.g., "human")

    Returns:
        dict with approval details or error
    """
    proposal = get_proposal(proposal_id)
    if not proposal:
        return {
            "ok": False,
            "error": f"Proposal not found: {proposal_id}",
        }

    now_ts = int(time.time())

    # Update proposal
    proposal["status"] = "approved"
    proposal["approval"]["approved_by"] = approved_by
    proposal["approval"]["approved_at"] = now_ts

    # Save proposal
    proposals = load_proposals()
    for i, p in enumerate(proposals):
        if p.get("id") == proposal_id:
            proposals[i] = proposal
            break
    save_proposals(proposals)

    # Record in approval log
    approval_entry = {
        "id": f"approv-{now_ts}",
        "proposal_id": proposal_id,
        "action": "approved",
        "approved_by": approved_by,
        "timestamp": now_ts,
        "notes": f"Proposal approved in Phase 1A (no code applied)",
    }

    log = load_approval_log()
    log.append(approval_entry)
    save_approval_log(log)

    return {
        "ok": True,
        "proposal_id": proposal_id,
        "status": "approved",
        "approved_by": approved_by,
        "approved_at": now_ts,
        "note": "Phase 1A: No code changes applied. Status updated to approved.",
    }


def deny_proposal(proposal_id: str, reason: str) -> dict:
    """Deny a proposal.

    Args:
        proposal_id: ID of proposal to deny
        reason: Reason for denial

    Returns:
        dict with denial details or error
    """
    proposal = get_proposal(proposal_id)
    if not proposal:
        return {
            "ok": False,
            "error": f"Proposal not found: {proposal_id}",
        }

    now_ts = int(time.time())

    # Update proposal
    proposal["status"] = "rejected"
    proposal["approval"]["denied_at"] = now_ts
    proposal["approval"]["denial_reason"] = reason

    # Save proposal
    proposals = load_proposals()
    for i, p in enumerate(proposals):
        if p.get("id") == proposal_id:
            proposals[i] = proposal
            break
    save_proposals(proposals)

    # Record in approval log
    approval_entry = {
        "id": f"approv-{now_ts}",
        "proposal_id": proposal_id,
        "action": "denied",
        "approved_by": None,
        "denial_reason": reason,
        "timestamp": now_ts,
        "notes": f"Proposal denied: {reason}",
    }

    log = load_approval_log()
    log.append(approval_entry)
    save_approval_log(log)

    return {
        "ok": True,
        "proposal_id": proposal_id,
        "status": "rejected",
        "denial_reason": reason,
        "denied_at": now_ts,
    }


def build_proposal_report() -> dict:
    """Build a summary report of all proposals."""
    proposals = load_proposals()
    log = load_approval_log()

    status_counts = {"proposed": 0, "approved": 0, "rejected": 0}
    with_tests = 0
    with_rollback = 0
    with_patch_plan = 0

    for p in proposals:
        status = p.get("status", "unknown")
        if status in status_counts:
            status_counts[status] += 1

        # Count Phase 1B metadata
        if p.get("test_prompts"):
            with_tests += 1
        if p.get("rollback_command"):
            with_rollback += 1
        if p.get("patch_plan"):
            with_patch_plan += 1

    return {
        "ok": True,
        "total_proposals": len(proposals),
        "by_status": status_counts,
        "total_approvals": len(log),
        "with_tests": with_tests,
        "with_rollback": with_rollback,
        "with_patch_plan": with_patch_plan,
        "generated_at": int(time.time()),
    }
