# weslr_operator_views.py - Weslr Capability Slice: Operator Review Enhancements
# Exposes Weslr's internal assessment fields in the operator review flow for external requests.
# Keep this internal/operator-only; do NOT expose to public-facing output.
# Additive only, reversible.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================================
# OPERATOR VIEW ENHANCEMENTS
# ============================================================================

# v17 governance invocation integration
try:
    from governance_invocation import (
        invoke_governance_single,
        invoke_governance_compare,
        format_invocation_result,
    )
    GOVERNANCE_INVOCATION_AVAILABLE = True
except ImportError:
    GOVERNANCE_INVOCATION_AVAILABLE = False


# ============================================================================
# GOVERNANCE INVOCATION WRAPPERS
# ============================================================================

def operator_invoke_governance_single(
    proposal_id: str,
    storage_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Operator-facing wrapper for governance single invocation."""
    if not GOVERNANCE_INVOCATION_AVAILABLE:
        return {"error": "Governance invocation layer not available", "proposal_id": proposal_id}
    return invoke_governance_single(proposal_id, storage_path)


def operator_invoke_governance_compare(
    proposal_ids: List[str],
    storage_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Operator-facing wrapper for governance comparison invocation."""
    if not GOVERNANCE_INVOCATION_AVAILABLE:
        return {"error": "Governance invocation layer not available", "proposal_ids": proposal_ids}
    return invoke_governance_compare(proposal_ids, storage_path)


def operator_format_governance_result(
    result: Dict[str, Any],
) -> str:
    """Format governance invocation result for operator display."""
    if not GOVERNANCE_INVOCATION_AVAILABLE:
        return json.dumps(result, indent=2)
    return format_invocation_result(result)


# ============================================================================
# OPERATOR VIEW ENHANCEMENTS
# ============================================================================

def enhance_review_candidate_with_weslr_assessment(
    candidate: Dict[str, Any]
) -> Dict[str, Any]:
    """Enhance a review candidate with Weslr assessment if available.

    Args:
        candidate: Proposal candidate dict from suggestion_bridge

    Returns:
        Enhanced candidate with weslr_assessment fields surfaced at top level
        for easy operator access.
    """
    # If no weslr_assessment, return as-is
    if "weslr_assessment" not in candidate:
        return candidate

    assessment = candidate["weslr_assessment"]

    # Create enhanced view that surfaces assessment fields at top level
    # while preserving original structure
    enhanced = candidate.copy()

    # Add assessment-derived fields for easy visibility
    enhanced["weslr_priority"] = assessment.get("priority")
    enhanced["weslr_fit_score"] = assessment.get("fit_score")
    enhanced["weslr_risk"] = assessment.get("implementation_risk")
    enhanced["weslr_recommended_action"] = assessment.get("recommended_action")
    enhanced["weslr_reasoning"] = assessment.get("reasoning")

    # Add status indicator for easy scanning
    status_parts = []
    if assessment.get("priority") == "high":
        status_parts.append("HIGH PRIORITY")
    if assessment.get("implementation_risk") == "high":
        status_parts.append("HIGH RISK")
    enhanced["weslr_status"] = " | ".join(status_parts) if status_parts else "NORMAL"

    return enhanced


def build_operator_review_detail(
    candidate: Dict[str, Any]
) -> Dict[str, Any]:
    """Build detailed operator view for a single candidate.

    Returns:
        Dict with:
        - candidate: original data
        - weslr_assessment: assessment fields
        - enhanced: top-level surfaced fields for visibility
    """
    enhanced = enhance_review_candidate_with_weslr_assessment(candidate)

    return {
        "candidate": candidate,
        "weslr_assessment": candidate.get("weslr_assessment", {}),
        "enhanced": {
            "priority": enhanced.get("weslr_priority"),
            "fit_score": enhanced.get("weslr_fit_score"),
            "risk": enhanced.get("weslr_risk"),
            "recommended_action": enhanced.get("weslr_recommended_action"),
            "reasoning": enhanced.get("weslr_reasoning"),
            "status": enhanced.get("weslr_status"),
        },
    }


def build_operator_review_list(
    candidates: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Build list view for operator review.

    Returns:
        List of enhanced candidates with top-level assessment fields.
    """
    return [enhance_review_candidate_with_weslr_assessment(c) for c in candidates]


def format_assessment_for_display(
    candidate: Dict[str, Any]
) -> str:
    """Format Weslr assessment for human-readable display.

    Returns:
        Multi-line string with assessment summary for operator console.
    """
    if "weslr_assessment" not in candidate:
        return "No Weslr assessment available."

    a = candidate["weslr_assessment"]
    lines = [
        "=== WESLR ASSESSMENT ===",
        f"Priority: {a.get('priority', 'N/A').upper()}",
        f"Fit Score: {a.get('fit_score', 'N/A'):.2f}",
        f"Implementation Risk: {a.get('implementation_risk', 'N/A').upper()}",
        f"Recommended Action: {a.get('recommended_action', 'N/A')}",
        "",
        "Reasoning:",
        f"  {a.get('reasoning', 'N/A')}",
    ]
    return "\n".join(lines)


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python weslr_operator_views.py <command> [args]")
        print("Commands:")
        print("  enhance <candidate_json_file>")
        print("  detail <candidate_json_file>")
        print("  list <candidates_json_file>")
        print("  format <candidate_json_file>")
        print("  governance-single <proposal_id>")
        print("  governance-compare <proposal_id_1> <proposal_id_2>")
        sys.exit(1)
        sys.exit(1)

    command = sys.argv[1]

    if command == "enhance":
        if len(sys.argv) < 3:
            print("Usage: enhance <candidate_json_file>")
            sys.exit(1)
        with open(sys.argv[2]) as f:
            candidate = json.load(f)
        result = enhance_review_candidate_with_weslr_assessment(candidate)
        print(json.dumps(result, indent=2))

    elif command == "detail":
        if len(sys.argv) < 3:
            print("Usage: detail <candidate_json_file>")
            sys.exit(1)
        with open(sys.argv[2]) as f:
            candidate = json.load(f)
        result = build_operator_review_detail(candidate)
        print(json.dumps(result, indent=2))

    elif command == "list":
        if len(sys.argv) < 3:
            print("Usage: list <candidates_json_file>")
            sys.exit(1)
        with open(sys.argv[2]) as f:
            candidates = json.load(f)
        result = build_operator_review_list(candidates)
        print(json.dumps(result, indent=2))

    elif command == "format":
        if len(sys.argv) < 3:
            print("Usage: format <candidate_json_file>")
            sys.exit(1)
        with open(sys.argv[2]) as f:
            candidate = json.load(f)
        result = format_assessment_for_display(candidate)
        print(result)

    elif command == "governance-single":
        if len(sys.argv) < 3:
            print("Usage: governance-single <proposal_id>")
            sys.exit(1)
        proposal_id = sys.argv[2]
        result = operator_invoke_governance_single(proposal_id)
        print(operator_format_governance_result(result))

    elif command == "governance-compare":
        if len(sys.argv) < 4:
            print("Usage: governance-compare <proposal_id_1> <proposal_id_2>")
            sys.exit(1)
        proposal_ids = [sys.argv[2], sys.argv[3]]
        result = operator_invoke_governance_compare(proposal_ids)
        print(operator_format_governance_result(result))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
