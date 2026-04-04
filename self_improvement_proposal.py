"""Weslr Self-Improvement Proposal Layer.

Creates, lists, and manages improvement proposals.
Handles human approval workflow for safe bounded evolution.
Phase 1B: Added test prompts, expected outputs, rollback commands, and patch plans.
Phase 1C: Added operator-only visibility filtering via Weslr profiles.
"""

from __future__ import annotations

import json
import time
from pathlib import Path


PROPOSALS_FILE = "self_improvement_proposals.json"
APPROVAL_LOG_FILE = "self_improvement_approval_log.json"
BASE_DIR = Path(__file__).resolve().parent


def _is_public_visible() -> bool:
    """Check if self-improvement proposals should be visible to public.
    
    In public_test mode, proposals are operator-only and hidden from public.
    Only operators can see and interact with proposals.
    
    Returns:
        True if visible to public, False if operator-only
    """
    try:
        from weslr.profiles import is_self_improvement_public
        return is_self_improvement_public()
    except Exception:
        # Default to private for safety
        return False


def _filter_for_visibility(proposals: list[dict]) -> list[dict]:
    """Filter proposals based on visibility settings.
    
    When public_visible is False, return empty list to prevent exposure.
    When public_visible is True, return all proposals.
    
    Args:
        proposals: List of proposal dictionaries
        
    Returns:
        Filtered list of proposals
    """
    if _is_public_visible():
        return proposals
    # Operator-only mode: return empty list to prevent exposure
    return []


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
        # Phase 1D: explicit review state
        "status": "pending_review",  # New proposals start in pending review
        "review": {
            "state": "pending",  # pending | approved | denied | applied
            "requested_at": now_ts,
            "reviewed_by": None,
            "reviewed_at": None,
            "review_notes": None,
            "review_type": "operator",  # operator | automated
        },
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
        # Phase 1C: visibility metadata
        "visibility": "operator_only",  # Always operator-only in public_test
    }

    # Load existing, append, save
    proposals = load_proposals()
    proposals.append(proposal)
    save_proposals(proposals)

    return {
        "ok": True,
        "proposal_id": proposal_id,
        "title": title,
        "status": "pending_review",  # Phase 1D: new proposals start in pending review
        "created_at": now_ts,
        "has_tests": len(test_prompts or []) > 0,
        "has_rollback": rollback_command is not None,
        "visibility": "operator_only",
        "review_state": "pending",  # Phase 1D: explicit review state
    }


def list_proposals(
    status: str | None = None,
    review_state: str | None = None,
    limit: int = 50,
) -> dict:
    """List proposals, optionally filtered by status or review state.

    Args:
        status: Filter by status (pending_review | approved | rejected | applied)
        review_state: Filter by review state (pending | approved | denied | applied)
        limit: Maximum results to return

    Returns:
        dict with proposals list and metadata
    """
    proposals = load_proposals()

    # Apply visibility filter - in public_test mode, return empty list
    proposals = _filter_for_visibility(proposals)

    # Apply review_state filter first (more specific)
    if review_state and proposals:
        proposals = [p for p in proposals if p.get("review", {}).get("state") == review_state]
    
    # Apply status filter if no review_state filter and proposals are visible
    if status and proposals and not review_state:
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
        # Phase 1C: indicate visibility mode
        "public_visible": _is_public_visible(),
    }


def get_proposal(proposal_id: str) -> dict | None:
    """Get a specific proposal by ID.
    
    In operator-only mode, returns None to prevent exposure.
    """
    # Check visibility first
    if not _is_public_visible():
        # Operator-only mode: return None to prevent exposure
        # Operators can use internal functions to access proposals directly
        return None
    
    proposals = load_proposals()
    for p in proposals:
        if p.get("id") == proposal_id:
            return p
    return None


def get_proposal_operator(proposal_id: str) -> dict | None:
    """Get a specific proposal by ID - operator only.
    
    This function bypasses visibility filtering for operator use.
    Should only be called by operator code paths.
    
    Args:
        proposal_id: ID of proposal to retrieve
        
    Returns:
        dict with proposal details or None if not found
    """
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
    # Use the new update_review_state function
    result = update_review_state(
        proposal_id=proposal_id,
        new_state="approved",
        reviewed_by=approved_by,
        review_notes="Proposal approved - Phase 1A",
        review_type="operator",
    )
    
    if result.get("ok"):
        # Add Phase 1A note for backwards compatibility
        result["note"] = "Phase 1A: No code changes applied. Status updated to approved."
    
    return result


def deny_proposal(proposal_id: str, reason: str) -> dict:
    """Deny a proposal.

    Args:
        proposal_id: ID of proposal to deny
        reason: Reason for denial

    Returns:
        dict with denial details or error
    """
    # Use the new update_review_state function
    result = update_review_state(
        proposal_id=proposal_id,
        new_state="denied",
        reviewed_by="human",
        review_notes=reason,
        review_type="operator",
    )
    
    return result


def update_review_state(
    proposal_id: str,
    new_state: str,
    reviewed_by: str,
    review_notes: str | None = None,
    review_type: str = "operator",
) -> dict:
    """Update the review state of a proposal.
    
    This is the primary operator review state transition function.
    It enforces explicit state transitions and tracks who reviewed.
    
    States:
        - pending: New proposal awaiting review
        - approved: Proposal approved by operator
        - denied: Proposal denied by operator
        - applied: Proposal applied to codebase
    
    Args:
        proposal_id: ID of proposal to update
        new_state: New review state (pending | approved | denied | applied)
        reviewed_by: Who performed the review (e.g., "human", "automated")
        review_notes: Optional notes about the review decision
        review_type: Type of review (operator | automated)
        
    Returns:
        dict with review update details or error
    """
    # Validate state
    allowed_states = ["pending", "approved", "denied", "applied"]
    if new_state not in allowed_states:
        return {
            "ok": False,
            "error": f"Invalid review_state. Must be one of: {allowed_states}",
        }
    
    # Get proposal (operator access, bypasses visibility)
    proposal = get_proposal_operator(proposal_id)
    if not proposal:
        return {
            "ok": False,
            "error": f"Proposal not found: {proposal_id}",
        }

    now_ts = int(time.time())

    # Update review metadata
    proposal["review"]["state"] = new_state
    proposal["review"]["reviewed_by"] = reviewed_by
    proposal["review"]["reviewed_at"] = now_ts
    proposal["review"]["review_notes"] = review_notes
    proposal["review"]["review_type"] = review_type
    
    # Update status based on review state
    if new_state == "approved":
        proposal["status"] = "approved"
        proposal["approval"]["approved_by"] = reviewed_by
        proposal["approval"]["approved_at"] = now_ts
    elif new_state == "denied":
        proposal["status"] = "rejected"
        proposal["approval"]["denied_at"] = now_ts
        proposal["approval"]["denial_reason"] = review_notes or "Operator denied"
    elif new_state == "applied":
        proposal["status"] = "applied"
        proposal["applied_at"] = now_ts
        proposal["applied_by"] = reviewed_by

    # Save proposal
    proposals = load_proposals()
    for i, p in enumerate(proposals):
        if p.get("id") == proposal_id:
            proposals[i] = proposal
            break
    save_proposals(proposals)

    # Record in review log
    review_entry = {
        "id": f"rev-{now_ts}",
        "proposal_id": proposal_id,
        "action": f"review_{new_state}",
        "reviewed_by": reviewed_by,
        "review_state": new_state,
        "review_notes": review_notes,
        "timestamp": now_ts,
    }

    # Append to approval log (shared log for simplicity)
    log = load_approval_log()
    log.append(review_entry)
    save_approval_log(log)

    return {
        "ok": True,
        "proposal_id": proposal_id,
        "review_state": new_state,
        "reviewed_by": reviewed_by,
        "reviewed_at": now_ts,
    }


def build_proposal_report() -> dict:
    """Build a summary report of all proposals.
    
    In operator-only mode, returns reduced report without proposal details.
    """
    proposals = load_proposals()
    log = load_approval_log()

    # Apply visibility filter - count but don't expose details
    public_visible = _is_public_visible()
    
    # Phase 1D: Updated status counts to include review states
    status_counts = {"pending_review": 0, "approved": 0, "rejected": 0, "applied": 0}
    review_state_counts = {"pending": 0, "approved": 0, "denied": 0, "applied": 0}
    with_tests = 0
    with_rollback = 0
    with_patch_plan = 0

    for p in proposals:
        # Phase 1D: Count by review_state first (more granular)
        review_state = p.get("review", {}).get("state", "pending")
        if review_state in review_state_counts:
            review_state_counts[review_state] += 1
        
        # Also count by status for backwards compatibility
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

    result = {
        "ok": True,
        "total_proposals": len(proposals),
        "by_status": status_counts,
        "total_approvals": len(log),
        "with_tests": with_tests,
        "with_rollback": with_rollback,
        "with_patch_plan": with_patch_plan,
        "generated_at": int(time.time()),
        "public_visible": public_visible,
        # Phase 1D: Review state counts (more granular than status)
        "by_review_state": review_state_counts,
    }

    # Only include proposal details if visible to public
    if public_visible:
        result["proposals"] = proposals
    else:
        # Operator-only: include summary but not full details
        result["summary_only"] = True

    return result
