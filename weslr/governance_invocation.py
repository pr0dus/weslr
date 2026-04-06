# governance_invocation.py - Self-Architecture v17: Live Governance Invocation Layer
# Directly callable interface for operator governance queries.
# Additive only, operator-first, reversible. No autonomous execution.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from governance_surface import (
    GovernanceAggregationEngine,
    ProposalGovernanceView,
    get_governance_view,
)


def invoke_governance_single(
    proposal_id: str,
    storage_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Invoke governance view for a single proposal.
    
    Returns:
        Dict with:
        - proposal_id: proposal identifier
        - title: proposal title
        - summary: brief summary
        - why_surfaced: why it surfaced in operator flow
        - subsystem_impact: list of affected subsystems
        - forecast_summary: forecast summary if available
        - forecast_confidence: forecast confidence (0.0-1.0)
        - eligibility: execution eligibility status
        - can_proceed: can proceed to execution
        - blocking_reasons: list of blocking reasons
        - recommended_action: one of (execute, blockers, review, defer)
        - recommended_action_reason: explanation for recommendation
        - status: one of (blocked, eligible, delayed, risky, aligned, ready)
        - raw_view: full ProposalGovernanceView dict representation
    """
    engine = GovernanceAggregationEngine(storage_path=storage_path)
    view = engine.get_governance_view(proposal_id=proposal_id)
    
    if not view:
        return {
            "error": f"Proposal not found: {proposal_id}",
            "proposal_id": proposal_id,
        }
    
    # Determine status from eligibility and other signals
    status = _determine_status(view, engine)
    
    return {
        "proposal_id": view.proposal_id,
        "title": view.title,
        "summary": view.summary,
        "why_surfaced": view.why_surfaced,
        "subsystem_impact": view.subsystem_impact,
        "forecast_summary": view.forecast_summary,
        "forecast_confidence": view.forecast_confidence,
        "eligibility": view.execution_eligibility.get("eligibility", "unknown") if view.execution_eligibility else "unknown",
        "can_proceed": view.can_proceed,
        "blocking_reasons": view.blocking_reasons,
        "recommended_action": view.recommended_action,
        "recommended_action_reason": view.recommended_action_reason,
        "status": status,
        "raw_view": view.to_dict(),
    }


def invoke_governance_compare(
    proposal_ids: List[str],
    storage_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Invoke governance comparison for two proposals.
    
    Args:
        proposal_ids: List of exactly two proposal IDs to compare
        
    Returns:
        Dict with:
        - proposal_1: first proposal governance view
        - proposal_2: second proposal governance view
        - comparison: comparison summary
        - recommendation: which to prioritize
        - raw_views: list of raw ProposalGovernanceView dicts
    """
    if len(proposal_ids) != 2:
        return {
            "error": f"Exactly two proposal IDs required, got {len(proposal_ids)}",
            "proposal_ids": proposal_ids,
        }
    
    engine = GovernanceAggregationEngine(storage_path=storage_path)
    
    views = {}
    for pid in proposal_ids:
        view = engine.get_governance_view(proposal_id=pid)
        if view:
            views[pid] = view
        else:
            views[pid] = None
    
    # Build comparison data
    comparison = _build_comparison(views)
    
    # Determine recommendation
    recommendation = _recommend_between(views, comparison)
    
    return {
        "proposal_1": _view_to_dict(views.get(proposal_ids[0])),
        "proposal_2": _view_to_dict(views.get(proposal_ids[1])),
        "comparison": comparison,
        "recommendation": recommendation,
        "raw_views": [
            _view_to_dict(views.get(proposal_ids[0])),
            _view_to_dict(views.get(proposal_ids[1])),
        ],
    }


def _view_to_dict(view: Optional[ProposalGovernanceView]) -> Optional[Dict[str, Any]]:
    """Convert ProposalGovernanceView to dict, or None."""
    if view is None:
        return None
    return {
        "proposal_id": view.proposal_id,
        "title": view.title,
        "description": view.description,
        "summary": view.summary,
        "why_surfaced": view.why_surfaced,
        "subsystem_impact": view.subsystem_impact,
        "risk_effort": view.risk_effort,
        "forecast_summary": view.forecast_summary,
        "forecast_confidence": view.forecast_confidence,
        "approval_state": view.approval_state,
        "execution_eligibility": view.execution_eligibility,
        "proof_status": view.proof_status,
        "blocking_reasons": view.blocking_reasons,
        "can_proceed": view.can_proceed,
        "recommended_action": view.recommended_action,
        "recommended_action_reason": view.recommended_action_reason,
    }


def _determine_status(view: ProposalGovernanceView, engine: GovernanceAggregationEngine) -> str:
    """Determine proposal status.
    
    Returns one of: blocked, eligible, delayed, risky, aligned, ready
    """
    # Check blocking reasons
    if view.blocking_reasons and view.can_proceed is False:
        return "blocked"
    
    # Check proof gate eligibility
    if view.execution_eligibility:
        eligibility = view.execution_eligibility.get("eligibility", "unknown")
        if eligibility == "eligible" and view.can_proceed:
            return "ready"
    
    # Check confidence score
    if view.forecast_confidence is not None and view.forecast_confidence < 0.5:
        return "delayed"
    
    # Check risk level
    risk_level = view.risk_effort.get("risk_level", "unknown") if view.risk_effort else "unknown"
    if risk_level == "high":
        return "risky"
    
    # Check if aligned with operator intent
    if view.approval_state == "approved":
        return "aligned"
    
    # Default to eligible if no blockers
    if not view.blocking_reasons:
        return "eligible"
    
    return "blocked"


def _build_comparison(views: Dict[str, Optional[ProposalGovernanceView]]) -> Dict[str, Any]:
    """Build comparison data for two proposals."""
    proposal_1_data = views.get(list(views.keys())[0])
    proposal_2_data = views.get(list(views.keys())[1])
    
    # Extract key metrics for comparison
    metrics = {}
    
    for key, view in views.items():
        if view:
            metrics[key] = {
                "confidence": view.forecast_confidence,
                "can_proceed": view.can_proceed,
                "risk_level": view.risk_effort.get("risk_level", "unknown") if view.risk_effort else "unknown",
                "blocking_reasons": len(view.blocking_reasons),
                "status": _determine_status(view, GovernanceAggregationEngine()),
            }
    
    # Build comparison summary
    summary_parts = []
    if proposal_1_data and proposal_2_data:
        if proposal_1_data.forecast_confidence > proposal_2_data.forecast_confidence:
            summary_parts.append(f"{proposal_1_data.proposal_id} has higher confidence ({proposal_1_data.forecast_confidence:.0%} vs {proposal_2_data.forecast_confidence:.0%})")
        if proposal_1_data.can_proceed and not proposal_2_data.can_proceed:
            summary_parts.append(f"{proposal_1_data.proposal_id} is ready for execution, {proposal_2_data.proposal_id} has blockers")
        if proposal_1_data.forecast_confidence < proposal_2_data.forecast_confidence:
            summary_parts.append(f"{proposal_2_data.proposal_id} has higher confidence ({proposal_2_data.forecast_confidence:.0%} vs {proposal_1_data.forecast_confidence:.0%})")
    
    return {
        "summary": "; ".join(summary_parts) if summary_parts else "Direct comparison requires more data",
        "metrics": metrics,
        "proposal_count": len([v for v in views.values() if v is not None]),
    }


def _recommend_between(views: Dict[str, Optional[ProposalGovernanceView]], comparison: Dict[str, Any]) -> Dict[str, Any]:
    """Provide recommendation for which proposal to prioritize."""
    available = [k for k, v in views.items() if v is not None]
    
    if len(available) < 2:
        return {
            "recommendation": None,
            "reason": "Need exactly two valid proposals for comparison",
        }
    
    v1 = views[available[0]]
    v2 = views[available[1]]
    
    # Prefer proposal that can proceed
    if v1.can_proceed and not v2.can_proceed:
        return {
            "recommendation": available[0],
            "reason": f"{v1.proposal_id} is ready for execution ({comparison['metrics'].get(available[0], {}).get('status', 'unknown')})",
        }
    if v2.can_proceed and not v1.can_proceed:
        return {
            "recommendation": available[1],
            "reason": f"{v2.proposal_id} is ready for execution ({comparison['metrics'].get(available[1], {}).get('status', 'unknown')})",
        }
    
    # Prefer higher confidence
    if v1.forecast_confidence >= v2.forecast_confidence:
        return {
            "recommendation": available[0],
            "reason": f"{v1.proposal_id} has higher confidence ({v1.forecast_confidence:.0%} vs {v2.forecast_confidence:.0%})",
        }
    
    return {
        "recommendation": available[1],
        "reason": f"{v2.proposal_id} has higher confidence ({v2.forecast_confidence:.0%} vs {v1.forecast_confidence:.0%})",
    }


def format_invocation_result(result: Dict[str, Any]) -> str:
    """Format invocation result for human-readable display."""
    if "error" in result:
        return f"Error: {result['error']}\nProposal ID: {result.get('proposal_id', 'N/A')}"
    
    # Single proposal view
    if "status" in result and "comparison" not in result:
        lines = [
            "=" * 70,
            f"GOVERNANCE INVOCATION: {result['proposal_id']}",
            "=" * 70,
            "",
            f"TITLE: {result['title']}",
            "",
            "SUMMARY:",
            result.get("summary", "N/A"),
            "",
            "WHY SURFACED:",
            result.get("why_surfaced", "N/A"),
            "",
            "FORECAST:",
            f"  Confidence: {result.get('forecast_confidence', 'N/A')}",
            f"  Summary: {result.get('forecast_summary', 'N/A')}",
            "",
            "ELIGIBILITY:",
            f"  Eligibility: {result.get('eligibility', 'N/A')}",
            f"  Can Proceed: {result.get('can_proceed', 'N/A')}",
            "",
        ]
        
        blocking = result.get("blocking_reasons", [])
        if blocking:
            lines.append("BLOCKING REASONS:")
            for reason in blocking:
                lines.append(f"  - {reason}")
            lines.append("")
        
        lines.extend([
            "STATUS:",
            f"  {result.get('status', 'N/A').upper()}",
            "",
            "RECOMMENDED ACTION:",
            f"  {result.get('recommended_action', 'N/A').upper()}",
            f"  Reason: {result.get('recommended_action_reason', 'N/A')}",
            "",
            "=" * 70,
        ])
        return "\n".join(lines)
    
    # Compare view
    if "comparison" in result and "recommendation" in result:
        lines = [
            "=" * 70,
            "GOVERNANCE COMPARISON",
            "=" * 70,
            "",
        ]
        
        for i, key in enumerate(["proposal_1", "proposal_2"], 1):
            if result.get(key):
                lines.append(f"PROPOSAL {i}:")
                p = result[key]
                lines.append(f"  ID: {p.get('proposal_id', 'N/A')}")
                lines.append(f"  Title: {p.get('title', 'N/A')}")
                lines.append(f"  Confidence: {p.get('forecast_confidence', 'N/A')}")
                lines.append(f"  Can Proceed: {p.get('can_proceed', 'N/A')}")
                lines.append("")
        
        if result.get("comparison", {}).get("summary"):
            lines.extend([
                "COMPARISON:",
                f"  {result['comparison']['summary']}",
                "",
            ])
        
        rec = result.get("recommendation", {})
        if rec.get("recommendation"):
            lines.extend([
                "RECOMMENDATION:",
                f"  {rec['recommendation'].upper()}",
                f"  Reason: {rec.get('reason', 'N/A')}",
                "",
            ])
        
        lines.append("=" * 70)
        return "\n".join(lines)
    
    # Fallback
    return json.dumps(result, indent=2)


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python governance_invocation.py <command> [args]")
        print("Commands:")
        print("  single <proposal_id> [storage_path]")
        print("  compare <proposal_id_1> <proposal_id_2> [storage_path]")
        print("  format <result_json_file>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "single":
        if len(sys.argv) < 3:
            print("Usage: python governance_invocation.py single <proposal_id> [storage_path]")
            sys.exit(1)
        proposal_id = sys.argv[2]
        storage_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
        result = invoke_governance_single(proposal_id, storage_path)
        print(format_invocation_result(result))
    
    elif command == "compare":
        if len(sys.argv) < 4:
            print("Usage: python governance_invocation.py compare <proposal_id_1> <proposal_id_2> [storage_path]")
            sys.exit(1)
        proposal_ids = [sys.argv[2], sys.argv[3]]
        storage_path = Path(sys.argv[4]) if len(sys.argv) > 4 else None
        result = invoke_governance_compare(proposal_ids, storage_path)
        print(format_invocation_result(result))
    
    elif command == "format":
        if len(sys.argv) < 3:
            print("Usage: python governance_invocation.py format <result_json_file>")
            sys.exit(1)
        with open(sys.argv[2]) as f:
            result = json.load(f)
        print(format_invocation_result(result))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
