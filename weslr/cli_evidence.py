"""WESLR Evidence CLI - Control/Inspection Surface (v94d)

CLI commands for evidence assimilation routing and governance workflow.
Control/inspection surface only - no execution/application path.

Commands:
- evidence routes — list all routing states (read-only)
- evidence route <proposal_id> — show routing status and history (read-only)
- evidence submit <proposal_id> --by ... — operator trigger to start review
- evidence approve <proposal_id> --by ... --notes ... — operator trigger to approve
- evidence reject <proposal_id> --by ... --notes ... — operator trigger to reject

Constraints:
- Additive only, no breaking changes
- No execution/application path (deferred to Phase D)
- No hidden mutation (all state changes via governed workflows)
- No auto-approval (all approvals require explicit operator action)
- No TIA/C#, no orchestration, no scheduler/task engine
"""

from __future__ import annotations

import json
from typing import Optional, Dict, Any, List

from .evidence_to_governance_router import (
    EvidenceToGovernanceRouter,
    RoutingState,
    RoutingRecord,
    EvidenceProposalPayload,
    EvidenceProposalWithRouting,
)
from .internal_reasoning_graph.proposal_workflow import ProposalWorkflow
from .internal_reasoning_graph.governance import ProposalGovernanceEngine
from .evidence_intake.ingestion import EvidenceIngestion
from .evidence_intake.models import EvidenceSourceTypeEnum


def emit(data: Dict[str, Any]) -> None:
    """Emit JSON to stdout."""
    print(json.dumps(data, indent=2))


# ============================================================================
# CLI Command Implementations
# ============================================================================

def cmd_evidence_routes(_args) -> None:
    """List all routing states - read-only export."""
    router = EvidenceToGovernanceRouter()
    result = router.export_all_routing()
    emit(result)
    
    total = result.get("total_count", 0)
    print(f"\n--- Routing Summary ({total} total) ---")
    if total > 0:
        for proposal_id, state in result.get("routings", {}).items():
            status = state.get("routing_status", "unknown")
            print(f"[{proposal_id}] Status: {status}")
    else:
        print("No routing records found.")


def cmd_evidence_route(args) -> None:
    """Show routing status and history for a proposal - read-only query."""
    proposal_id = args.proposal_id
    if not proposal_id:
        emit({"error": "Missing required argument: --proposal-id"})
        return
    
    router = EvidenceToGovernanceRouter()
    summary = router.export_routing_summary(proposal_id)
    emit(summary)
    
    status = summary.get("routing_status", "unknown")
    history = summary.get("routing_history", [])
    
    print(f"\n--- Routing Details for {proposal_id} ---")
    print(f"Status: {status}")
    print(f"Created: {summary.get('created_at', 'N/A')}")
    
    if history:
        print(f"\nRouting History ({len(history)} records):")
        for record in history:
            timestamp = record.get("timestamp", "N/A")
            from_status = record.get("from_status", "unknown")
            to_status = record.get("to_status", "unknown")
            actor = record.get("actor", "unknown")
            action = record.get("action", "unknown")
            notes = record.get("notes", "")
            print(f"  [{timestamp}] {from_status} -> {to_status} by {actor} ({action})")
            if notes:
                print(f"    Notes: {notes}")
    else:
        print("No routing history found.")


def cmd_evidence_submit(args) -> None:
    """Operator trigger to submit proposal for review."""
    proposal_id = args.proposal_id
    by = args.by
    
    if not proposal_id:
        emit({"error": "Missing required argument: --proposal-id"})
        return
    if not by:
        emit({"error": "Missing required argument: --by"})
        return
    
    router = EvidenceToGovernanceRouter()
    
    try:
        record = router.submit_for_review(proposal_id, by)
        emit({
            "ok": True,
            "proposal_id": proposal_id,
            "action": "submit_for_review",
            "reviewer": by,
            "record": record.to_dict(),
        })
        print(f"\n✅ Submitted for review: {proposal_id}")
        print(f"   By: {by}")
    except ValueError as e:
        emit({"error": str(e)})
        print(f"\n❌ Submission failed: {e}")


def cmd_evidence_approve(args) -> None:
    """Operator trigger to approve proposal."""
    proposal_id = args.proposal_id
    by = args.by
    notes = args.notes or ""
    
    if not proposal_id:
        emit({"error": "Missing required argument: --proposal-id"})
        return
    if not by:
        emit({"error": "Missing required argument: --by"})
        return
    
    router = EvidenceToGovernanceRouter()
    
    try:
        record = router.approve_proposal(proposal_id, by, notes)
        emit({
            "ok": True,
            "proposal_id": proposal_id,
            "action": "approve",
            "reviewer": by,
            "notes": notes,
            "record": record.to_dict(),
        })
        print(f"\n✅ Approved: {proposal_id}")
        print(f"   By: {by}")
        if notes:
            print(f"   Notes: {notes}")
    except ValueError as e:
        emit({"error": str(e)})
        print(f"\n❌ Approval failed: {e}")


def cmd_evidence_reject(args) -> None:
    """Operator trigger to reject proposal."""
    proposal_id = args.proposal_id
    by = args.by
    notes = args.notes or ""
    
    if not proposal_id:
        emit({"error": "Missing required argument: --proposal-id"})
        return
    if not by:
        emit({"error": "Missing required argument: --by"})
        return
    
    router = EvidenceToGovernanceRouter()
    
    try:
        record = router.reject_proposal(proposal_id, by, notes)
        emit({
            "ok": True,
            "proposal_id": proposal_id,
            "action": "reject",
            "reviewer": by,
            "notes": notes,
            "record": record.to_dict(),
        })
        print(f"\n✅ Rejected: {proposal_id}")
        print(f"   By: {by}")
        if notes:
            print(f"   Notes: {notes}")
    except ValueError as e:
        emit({"error": str(e)})
        print(f"\n❌ Rejection failed: {e}")


# ============================================================================
# CLI Registration
# ============================================================================

def register_commands(subparsers) -> None:
    """Register evidence CLI commands."""
    evidence_parser = subparsers.add_parser("evidence", help="evidence assimilation and routing workflow")
    evidence_sub = evidence_parser.add_subparsers(dest="evidence_cmd", required=True)
    
    # evidence routes - read-only
    routes_parser = evidence_sub.add_parser("routes", help="list all routing states")
    routes_parser.set_defaults(func=cmd_evidence_routes)
    
    # evidence route <proposal_id> - read-only
    route_parser = evidence_sub.add_parser("route", help="show routing status and history for a proposal")
    route_parser.add_argument("--proposal-id", "-p", required=True, help="proposal ID")
    route_parser.set_defaults(func=cmd_evidence_route)
    
    # evidence submit <proposal_id> --by ...
    submit_parser = evidence_sub.add_parser("submit", help="submit a proposal for formal review")
    submit_parser.add_argument("--proposal-id", "-p", required=True, help="proposal ID")
    submit_parser.add_argument("--by", "-b", required=True, help="reviewer name")
    submit_parser.set_defaults(func=cmd_evidence_submit)
    
    # evidence approve <proposal_id> --by ... --notes ...
    approve_parser = evidence_sub.add_parser("approve", help="approve a proposal")
    approve_parser.add_argument("--proposal-id", "-p", required=True, help="proposal ID")
    approve_parser.add_argument("--by", "-b", required=True, help="approver name")
    approve_parser.add_argument("--notes", "-n", default="", help="approval notes")
    approve_parser.set_defaults(func=cmd_evidence_approve)
    
    # evidence reject <proposal_id> --by ... --notes ...
    reject_parser = evidence_sub.add_parser("reject", help="reject a proposal")
    reject_parser.add_argument("--proposal-id", "-p", required=True, help="proposal ID")
    reject_parser.add_argument("--by", "-b", required=True, help="rejecter name")
    reject_parser.add_argument("--notes", "-n", default="", help="rejection notes")
    reject_parser.set_defaults(func=cmd_evidence_reject)
