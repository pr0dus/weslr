"""WESLR Observability + Audit Export Layer (v94e)

Side-effect free observability and audit export layer.
Reports existing routing/governance/proposal history without scoring,
recommendation, or hidden analytics.

Core methods return structured data only (Dict/List).
Optional formatter helpers may return human-readable strings.

No mutation paths, no printing in core methods.

Features:
- Audit timeline export (aggregated routing + governance history)
- Routing history export (proposal-specific and global)
- Proposal lifecycle summary (status transitions)
- Governance decision summary (approval/rejection records)
- Operator-readable and machine-readable export formats
"""

from __future__ import annotations

import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .evidence_to_governance_router import (
    EvidenceToGovernanceRouter,
    RoutingRecord,
    RoutingState,
    ProposalPayloadWithCandidate,
)
from .internal_reasoning_graph.proposal_workflow import ProposalWorkflow
from .internal_reasoning_graph.governance import (
    ProposalGovernanceEngine,
    ProposalReviewRecord,
    ProposalHistoryRecord,
    ProposalStatus,
    GovernanceDecision,
    GovernanceAction,
)


# ============================================================================
# Audit Event Data Models
# ============================================================================

@dataclass
class AuditEvent:
    """Represents a single audit event from routing or governance history."""
    timestamp: int
    event_type: str  # "routing" or "governance"
    proposal_id: str
    action: str  # specific action name
    actor: str  # reviewer/operator name
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    notes: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Core Observability Methods (Side-Effect Free)
# ============================================================================

def get_routing_timeline(proposal_id: str) -> List[RoutingRecord]:
    """Get complete routing history for a single proposal.
    
    Returns List[RoutingRecord] with all routing transitions.
    Side-effect free - pure query.
    """
    router = EvidenceToGovernanceRouter()
    return router.get_routing_history(proposal_id)


def get_governance_decisions(proposal_id: str) -> List[ProposalReviewRecord]:
    """Get all governance decisions for a single proposal.
    
    Returns List[ProposalReviewRecord] with all approval/rejection decisions.
    Side-effect free - pure query.
    """
    governance = ProposalGovernanceEngine()
    return governance.get_review_records(proposal_id)


def get_proposal_lifecycle(proposal_id: str) -> Dict[str, Any]:
    """Get complete lifecycle for a single proposal.
    
    Returns Dict with:
    - proposal_id
    - initial_status
    - final_status
    - transitions: List of status changes with timestamps
    - actors: Set of actors involved
    - total_duration: Seconds from first to last activity
    
    Side-effect free - pure query.
    """
    router = EvidenceToGovernanceRouter()
    governance = ProposalGovernanceEngine()
    
    # Get routing status history
    routing_records = router.get_routing_history(proposal_id)
    governance_records = governance.get_proposal_history(proposal_id)
    
    # Collect all status changes
    all_transitions = []
    actors = set()
    
    # Process routing records
    for record in routing_records:
        all_transitions.append({
            "timestamp": record.timestamp,
            "status": record.to_status.value,
            "actor": record.actor,
            "action": record.action.value,
            "source": "routing",
        })
        actors.add(record.actor)
    
    # Process governance history
    for record in governance_records:
        all_transitions.append({
            "timestamp": record.timestamp,
            "status": record.status,
            "actor": record.actor,
            "action": record.action.value,
            "source": "governance",
        })
        actors.add(record.actor)
    
    # Sort by timestamp
    all_transitions.sort(key=lambda x: x["timestamp"])
    
    # Calculate lifecycle info
    if all_transitions:
        initial_status = all_transitions[0]["status"]
        final_status = all_transitions[-1]["status"]
        first_ts = all_transitions[0]["timestamp"]
        last_ts = all_transitions[-1]["timestamp"]
        total_duration = last_ts - first_ts
    else:
        initial_status = "unknown"
        final_status = "unknown"
        total_duration = 0
    
    return {
        "proposal_id": proposal_id,
        "initial_status": initial_status,
        "final_status": final_status,
        "transitions": all_transitions,
        "actors": list(actors),
        "total_duration_seconds": total_duration,
    }


def get_audit_timeline() -> List[AuditEvent]:
    """Get aggregated audit timeline from all routing and governance history.
    
    Returns List[AuditEvent] with events sorted by timestamp.
    Side-effect free - pure query.
    """
    router = EvidenceToGovernanceRouter()
    governance = ProposalGovernanceEngine()
    
    audit_events = []
    
    # Process routing records
    for record in router._routing_records:
        audit_events.append(AuditEvent(
            timestamp=record.timestamp,
            event_type="routing",
            proposal_id=record.proposal_id,
            action=record.action.value,
            actor=record.actor,
            from_status=record.from_status.value if record.from_status else None,
            to_status=record.to_status.value if record.to_status else None,
            notes=record.notes,
        ))
    
    # Process governance review records
    for record in governance._review_records:
        audit_events.append(AuditEvent(
            timestamp=record.timestamp,
            event_type="governance",
            proposal_id=record.proposal_id,
            action="review",
            actor=record.reviewer,
            from_status=None,
            to_status=record.decision.value,
            notes=record.notes,
            details={"review_decision": record.decision.value},
        ))
    
    # Process governance history records
    for record in governance._history_records:
        audit_events.append(AuditEvent(
            timestamp=record.timestamp,
            event_type="governance",
            proposal_id=record.proposal_id,
            action=record.action.value,
            actor=record.actor,
            from_status=None,
            to_status=record.status,
            notes=record.notes,
        ))
    
    # Sort by timestamp
    audit_events.sort(key=lambda x: x.timestamp)
    
    return audit_events


def export_routing_summary() -> Dict[str, Any]:
    """Export all routing states as summary.
    
    Returns Dict with:
    - routings: Dict of proposal_id -> {routing_status, created_at}
    - total_count: Total number of routings
    - count_by_status: Dict of status -> count
    
    Side-effect free - pure query.
    """
    router = EvidenceToGovernanceRouter()
    return router.export_all_routing()


def export_governance_summary() -> Dict[str, Any]:
    """Export all governance decisions as summary.
    
    Returns Dict with:
    - review_records: List of ProposalReviewRecord dicts
    - history_records: List of ProposalHistoryRecord dicts
    - review_count: Total number of review records
    - history_count: Total number of history records
    - decisions_by_type: Dict of approved/rejected/pending count
    
    Side-effect free - pure query.
    """
    governance = ProposalGovernanceEngine()
    summary = governance.export_governance_summary()
    
    # Add decision counts by type
    decisions_by_type = {"approved": 0, "rejected": 0, "pending": 0}
    for record in governance._review_records:
        decisions_by_type[record.decision.value] += 1
    
    summary["decisions_by_type"] = decisions_by_type
    return summary


# ============================================================================
# Optional Human-Readable Formatters (Pure Functions)
# ============================================================================

def format_routing_timeline(proposal_id: str, events: Optional[List[RoutingRecord]] = None) -> str:
    """Format routing timeline for human display.
    
    Returns human-readable string with routing history.
    Pure function - no printing, returns string.
    """
    if events is None:
        events = get_routing_timeline(proposal_id)
    
    if not events:
        return f"No routing history for {proposal_id}"
    
    lines = [f"Routing Timeline for {proposal_id}"]
    lines.append("=" * 50)
    
    for i, record in enumerate(events, 1):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.timestamp))
        lines.append(f"\n[{i}] {timestamp}")
        lines.append(f"    {record.from_status.value or 'N/A'} → {record.to_status.value}")
        lines.append(f"    Actor: {record.actor}")
        lines.append(f"    Action: {record.action.value}")
        if record.notes:
            lines.append(f"    Notes: {record.notes}")
    
    return "\n".join(lines)


def format_governance_decisions(proposal_id: str, records: Optional[List[ProposalReviewRecord]] = None) -> str:
    """Format governance decisions for human display.
    
    Returns human-readable string with decision history.
    Pure function - no printing, returns string.
    """
    if records is None:
        records = get_governance_decisions(proposal_id)
    
    if not records:
        return f"No governance decisions for {proposal_id}"
    
    lines = [f"Governance Decisions for {proposal_id}"]
    lines.append("=" * 50)
    
    for i, record in enumerate(records, 1):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.timestamp))
        lines.append(f"\n[{i}] {timestamp}")
        lines.append(f"    Decision: {record.decision.value}")
        lines.append(f"    Reviewer: {record.reviewer}")
        if record.notes:
            lines.append(f"    Notes: {record.notes}")
    
    return "\n".join(lines)


def format_audit_summary(events: Optional[List[AuditEvent]] = None) -> str:
    """Format audit summary for human display.
    
    Returns human-readable string with aggregated timeline.
    Pure function - no printing, returns string.
    """
    if events is None:
        events = get_audit_timeline()
    
    if not events:
        return "No audit events found"
    
    lines = ["Audit Summary"]
    lines.append("=" * 60)
    lines.append(f"Total Events: {len(events)}")
    
    # Count by type
    by_type = {"routing": 0, "governance": 0}
    for event in events:
        by_type[event.event_type] += 1
    
    lines.append(f"  Routing: {by_type['routing']}")
    lines.append(f"  Governance: {by_type['governance']}")
    lines.append("")
    lines.append("Recent Events:")
    lines.append("-" * 40)
    
    # Show last 10 events
    recent = events[-10:] if len(events) > 10 else events
    for event in recent:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(event.timestamp))
        lines.append(f"  [{timestamp}] {event.proposal_id}: {event.action} ({event.event_type})")
    
    return "\n".join(lines)
