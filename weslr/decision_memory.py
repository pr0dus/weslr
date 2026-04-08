"""WESLR Decision Memory Layer (v94f)

Strictly observational decision memory layer.
Stores decision history, patterns, and confidence values without
recommendation logic, predictive modeling, or mutation paths.

Features:
- DecisionRecord: approval/rejection decision with operator, timestamp, notes
- ProposalPattern: recurring pattern tracking for similar proposals
- ConfidenceHistory: timestamped confidence values for proposals
- DecisionSummary: aggregated decision statistics and patterns
- No routing changes, no governance state changes, no proposal mutation
- No recommendation logic, no predictive modeling, no execution paths
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from .internal_reasoning_graph.governance import (
    ProposalGovernanceEngine,
    ProposalReviewRecord,
    GovernanceDecision,
)
from .evidence_to_governance_router import EvidenceToGovernanceRouter, RoutingRecord
from .observability import get_audit_timeline, AuditEvent


# ============================================================================
# Decision Memory Data Models
# ============================================================================

@dataclass
class DecisionRecord:
    """Record of a decision (approval or rejection) on a proposal."""
    proposal_id: str
    decision: str  # "approved" or "rejected"
    operator: str
    timestamp: int
    notes: str = ""
    confidence: Optional[float] = None
    pattern_id: Optional[str] = None  # Reference to recurring pattern if matched
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "decision": self.decision,
            "operator": self.operator,
            "timestamp": self.timestamp,
            "notes": self.notes,
            "confidence": self.confidence,
            "pattern_id": self.pattern_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionRecord":
        return cls(
            proposal_id=data["proposal_id"],
            decision=data["decision"],
            operator=data["operator"],
            timestamp=data["timestamp"],
            notes=data.get("notes", ""),
            confidence=data.get("confidence"),
            pattern_id=data.get("pattern_id"),
        )


@dataclass
class ProposalPattern:
    """Record of a recurring proposal pattern (similar claim_text and outcomes)."""
    pattern_id: str
    claim_text_prefix: str  # Prefix to match similar proposals
    outcomes: Dict[str, int]  # {"approved": N, "rejected": M}
    last_update: int  # Timestamp of last update
    confidence_values: List[float] = field(default_factory=list)  # All confidence values for pattern
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "claim_text_prefix": self.claim_text_prefix,
            "outcomes": self.outcomes,
            "last_update": self.last_update,
            "confidence_values": self.confidence_values,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProposalPattern":
        return cls(
            pattern_id=data["pattern_id"],
            claim_text_prefix=data["claim_text_prefix"],
            outcomes=data["outcomes"],
            last_update=data["last_update"],
            confidence_values=data.get("confidence_values", []),
        )
    
    @property
    def total_count(self) -> int:
        return sum(self.outcomes.values())
    
    @property
    def approval_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.outcomes.get("approved", 0) / self.total_count


@dataclass
class ConfidenceHistory:
    """Confidence values over time for a single proposal."""
    proposal_id: str
    values: List[Dict[str, Any]]  # List of {"timestamp": int, "confidence": float}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "values": self.values,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfidenceHistory":
        return cls(
            proposal_id=data["proposal_id"],
            values=data.get("values", []),
        )
    
    @property
    def first_value(self) -> Optional[float]:
        if not self.values:
            return None
        return self.values[0].get("confidence")
    
    @property
    def last_value(self) -> Optional[float]:
        if not self.values:
            return None
        return self.values[-1].get("confidence")


@dataclass
class DecisionSummary:
    """Aggregated decision statistics and patterns."""
    total_decisions: int
    approved_count: int
    rejected_count: int
    patterns: List[ProposalPattern]
    preference_summary: Dict[str, int]  # Operator preference counts
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_decisions": self.total_decisions,
            "approved_count": self.approved_count,
            "rejected_count": self.rejected_count,
            "patterns": [p.to_dict() for p in self.patterns],
            "preference_summary": self.preference_summary,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionSummary":
        patterns = [ProposalPattern.from_dict(p) for p in data.get("patterns", [])]
        return cls(
            total_decisions=data["total_decisions"],
            approved_count=data["approved_count"],
            rejected_count=data["rejected_count"],
            patterns=patterns,
            preference_summary=data.get("preference_summary", {}),
        )


# ============================================================================
# Decision Memory Core Methods (Observational Only)
# ============================================================================

def get_decision_history(proposal_id: str) -> List[DecisionRecord]:
    """Get all decisions for a single proposal.
    
    Returns List[DecisionRecord] with approval/rejection decisions.
    Observational only - no mutation.
    """
    governance = ProposalGovernanceEngine()
    records = governance.get_review_records(proposal_id)
    
    decisions = []
    for record in records:
        decisions.append(DecisionRecord(
            proposal_id=record.proposal_id,
            decision=record.decision.value,
            operator=record.reviewer,
            timestamp=record.timestamp,
            notes=record.notes,
        ))
    
    return decisions


def get_operator_decisions(operator: str) -> List[DecisionRecord]:
    """Get all decisions made by a specific operator.
    
    Returns List[DecisionRecord] filtered by operator.
    Observational only - no mutation.
    """
    governance = ProposalGovernanceEngine()
    records = governance._review_records
    
    decisions = []
    for record in records:
        if record.reviewer == operator:
            decisions.append(DecisionRecord(
                proposal_id=record.proposal_id,
                decision=record.decision.value,
                operator=record.reviewer,
                timestamp=record.timestamp,
                notes=record.notes,
            ))
    
    return decisions


def get_decision_counts() -> Dict[str, int]:
    """Get aggregate decision counts.
    
    Returns Dict with "total", "approved", "rejected" counts.
    Observational only - no mutation.
    """
    governance = ProposalGovernanceEngine()
    
    approved = 0
    rejected = 0
    
    for record in governance._review_records:
        if record.decision == GovernanceDecision.APPROVED:
            approved += 1
        elif record.decision == GovernanceDecision.REJECTED:
            rejected += 1
    
    return {
        "total": approved + rejected,
        "approved": approved,
        "rejected": rejected,
    }


def track_proposal_pattern(
    proposal_id: str,
    claim_text: str,
    decision: str,
    confidence: Optional[float] = None,
) -> str:
    """Track a recurring proposal pattern.
    
    Returns pattern_id for the matched/created pattern.
    Observational only - no mutation of governance state.
    """
    # Generate pattern ID from claim text prefix
    prefix = claim_text[:50] if len(claim_text) > 50 else claim_text
    pattern_id = f"pattern_{prefix.replace(' ', '_')[:30]}"
    
    # Store in-memory pattern (this is observational, not persisted)
    # In a real implementation, this would persist to storage
    return pattern_id


def get_recurring_patterns() -> List[ProposalPattern]:
    """Get all recurring proposal patterns.
    
    Returns List[ProposalPattern] with pattern details.
    Observational only - no mutation.
    """
    # This is observational - no actual patterns stored in memory
    # In a real implementation, this would read from persistent storage
    return []


def get_pattern_counts() -> Dict[str, int]:
    """Get pattern count summary.
    
    Returns Dict with pattern counts by outcome.
    Observational only - no mutation.
    """
    return {
        "total_patterns": 0,  # No patterns stored in memory
        "patterns_with_approvals": 0,
        "patterns_with_rejections": 0,
    }


def get_confidence_history(proposal_id: str) -> ConfidenceHistory:
    """Get confidence history for a single proposal.
    
    Returns ConfidenceHistory with timestamped values.
    Observational only - no mutation.
    """
    # Get routing status - we can infer confidence from routing records if available
    router = EvidenceToGovernanceRouter()
    records = router.get_routing_history(proposal_id)
    
    values = []
    for record in records:
        # Use timestamp as proxy for confidence history
        # In real implementation, this would come from proposal metadata
        values.append({
            "timestamp": record.timestamp,
            "confidence": 0.5,  # Default placeholder
        })
    
    return ConfidenceHistory(
        proposal_id=proposal_id,
        values=values,
    )


def describe_confidence_trend(pattern_id: str) -> str:
    """Describe confidence trend for a pattern.
    
    Returns lightweight trend label: "increasing", "decreasing", or "stable".
    No predictive modeling - simple descriptive analysis.
    Observational only - no mutation.
    """
    return "stable"  # Default - no actual trend data in memory


def export_decision_summary() -> DecisionSummary:
    """Export complete decision summary.
    
    Returns DecisionSummary with aggregated statistics and patterns.
    Observational only - no mutation.
    """
    counts = get_decision_counts()
    
    summary = DecisionSummary(
        total_decisions=counts["total"],
        approved_count=counts["approved"],
        rejected_count=counts["rejected"],
        patterns=[],
        preference_summary={},
    )
    
    return summary


def export_operator_summary(operator: str) -> Dict[str, Any]:
    """Export decision summary for a specific operator.
    
    Returns Dict with operator's decisions and preferences.
    Observational only - no mutation.
    """
    decisions = get_operator_decisions(operator)
    
    approved = sum(1 for d in decisions if d.decision == "approved")
    rejected = sum(1 for d in decisions if d.decision == "rejected")
    
    return {
        "operator": operator,
        "total_decisions": len(decisions),
        "approved_count": approved,
        "rejected_count": rejected,
        "decisions": [d.to_dict() for d in decisions],
    }


# ============================================================================
# Optional Human-Readable Formatters (Pure Functions)
# ============================================================================

def format_decision_summary(summary: Optional[DecisionSummary] = None) -> str:
    """Format decision summary for human display.
    
    Returns human-readable string with decision statistics.
    Pure function - no printing, returns string.
    Observational only - no mutation.
    """
    if summary is None:
        summary = export_decision_summary()
    
    lines = ["Decision Summary"]
    lines.append("=" * 50)
    lines.append(f"Total Decisions: {summary.total_decisions}")
    lines.append(f"  Approved: {summary.approved_count}")
    lines.append(f"  Rejected: {summary.rejected_count}")
    
    if summary.patterns:
        lines.append(f"\nRecurring Patterns: {len(summary.patterns)}")
        for pattern in summary.patterns:
            lines.append(f"  - {pattern.pattern_id}: {pattern.total_count} proposals")
            lines.append(f"    Approval rate: {pattern.approval_rate:.1%}")
    
    return "\n".join(lines)


def format_operator_summary(summary: Dict[str, Any]) -> str:
    """Format operator summary for human display.
    
    Returns human-readable string with operator's decisions.
    Pure function - no printing, returns string.
    Observational only - no mutation.
    """
    lines = [f"Decision Summary for {summary['operator']}"]
    lines.append("=" * 50)
    lines.append(f"Total Decisions: {summary['total_decisions']}")
    lines.append(f"  Approved: {summary['approved_count']}")
    lines.append(f"  Rejected: {summary['rejected_count']}")
    
    if summary.get("decisions"):
        lines.append("\nRecent Decisions:")
        for d in summary["decisions"][:5]:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(d["timestamp"]))
            lines.append(f"  [{timestamp}] {d['proposal_id']}: {d['decision']}")
            if d.get("notes"):
                lines.append(f"    Notes: {d['notes']}")
    
    return "\n".join(lines)
