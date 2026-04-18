# deterministic_synthesis.py - WESLR v94g: Deterministic Insight Synthesis Layer
# Read-only synthesis layer that groups, synthesizes, and exports insight patterns
# from existing records only. No optimization, no remediation, no orchestration,
# no backend/service/UI, no TIA/C#, no predictive modeling, no recommendations.
# No architecture/operator/release file changes. No mutation of source records.

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .audit_ledger import AuditLedger, AuditLedgerEngine, LedgerEvent
from .change_proposals import ChangeProposal, ProposalState, ProposalType
from .recovery_recommendation_export import (
    RecoveryRecommendationExportRecord,
    RecoveryRecommendationExporter,
)
from .recovery_decision_trace import (
    DecisionTraceRecord,
    DecisionTraceSummary,
)


# ============================================================================
# ENUMS
# ============================================================================


class SynthesisType(str, Enum):
    """Types of deterministic synthesis outputs."""
    PATTERN_GROUPING = "pattern_grouping"
    APPROVAL_REASON_GROUPING = "approval_reason_grouping"
    PROPOSAL_OUTCOME_GROUPING = "proposal_outcome_grouping"
    CONFIDENCE_TREND_SUMMARY = "confidence_trend_summary"
    BOTTLENECK_RECURRENCE_SUMMARY = "bottleneck_recurrence_summary"


class SynthesisScope(str, Enum):
    """Scope of synthesis analysis."""
    GLOBAL = "global"  # All records
    CONTEXT = "context"  # Within specific context
    OPERATOR = "operator"  # Per-operator analysis
    TIME_WINDOW = "time_window"  # Within time range


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class PatternGrouping:
    """Stable pattern grouping from existing records.
    
    Contains:
    - Pattern ID and type
    - Grouping criteria
    - Member records (IDs only, no deep inspection)
    - Frequency metrics
    """
    
    pattern_id: str
    pattern_type: str  # "repetition", "correlation", "sequence"
    criteria: Dict[str, Any]
    member_record_ids: List[str]
    frequency: int
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "criteria": self.criteria,
            "member_record_ids": self.member_record_ids,
            "frequency": self.frequency,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class ApprovalReasonGrouping:
    """Repeated approval/rejection reason grouping.
    
    Contains:
    - Reason ID and type
    - Grouping criteria (reason text)
    - Member record IDs
    - Frequency and approval rates
    """
    
    reason_id: str
    reason_type: str  # "approval", "rejection", "escalation"
    reason_text: str
    member_record_ids: List[str]
    frequency: int
    approval_rate: float
    first_occurrence: Optional[str] = None
    last_occurrence: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "reason_id": self.reason_id,
            "reason_type": self.reason_type,
            "reason_text": self.reason_text,
            "member_record_ids": self.member_record_ids,
            "frequency": self.frequency,
            "approval_rate": self.approval_rate,
            "first_occurrence": self.first_occurrence,
            "last_occurrence": self.last_occurrence,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class ProposalOutcomeGrouping:
    """Recurring proposal outcome grouping.
    
    Contains:
    - Outcome ID and type
    - Outcome category (approved/denied/deferred)
    - Member proposal IDs
    - Frequency and patterns
    """
    
    outcome_id: str
    outcome_category: str  # "approved", "denied", "deferred", "deprecated"
    member_proposal_ids: List[str]
    frequency: int
    average_effort: Optional[int] = None
    average_risk_level: Optional[str] = None
    first_proposal: Optional[str] = None
    last_proposal: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "outcome_id": self.outcome_id,
            "outcome_category": self.outcome_category,
            "member_proposal_ids": self.member_proposal_ids,
            "frequency": self.frequency,
            "average_effort": self.average_effort,
            "average_risk_level": self.average_risk_level,
            "first_proposal": self.first_proposal,
            "last_proposal": self.last_proposal,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class ConfidenceTrendSummary:
    """Confidence trend summary synthesis.
    
    Contains:
    - Trend ID and type
    - Before/after confidence levels
    - Direction and magnitude
    - Member records
    """
    
    trend_id: str
    trend_type: str  # "increasing", "decreasing", "stable", "variable"
    before_confidence: float
    after_confidence: float
    confidence_change: float
    confidence_direction: str  # "up", "down", "stable", "variable"
    member_record_ids: List[str]
    frequency: int
    first_record: Optional[str] = None
    last_record: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "trend_id": self.trend_id,
            "trend_type": self.trend_type,
            "before_confidence": self.before_confidence,
            "after_confidence": self.after_confidence,
            "confidence_change": self.confidence_change,
            "confidence_direction": self.confidence_direction,
            "member_record_ids": self.member_record_ids,
            "frequency": self.frequency,
            "first_record": self.first_record,
            "last_record": self.last_record,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class BottleneckRecurrenceSummary:
    """Bottleneck recurrence summary grounded in existing records only.
    
    Contains:
    - Bottleneck ID and type
    - Bottleneck category
    - Member bottleneck instances
    - Frequency and patterns
    """
    
    bottleneck_id: str
    bottleneck_type: str  # "approval_delay", "escalation", "validation", "approval"
    bottleneck_category: str  # "process", "resource", "information", "policy"
    member_bottleneck_ids: List[str]
    frequency: int
    average_duration: Optional[int] = None  # in minutes
    most_common_context: Optional[str] = None
    first_occurrence: Optional[str] = None
    last_occurrence: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "bottleneck_id": self.bottleneck_id,
            "bottleneck_type": self.bottleneck_type,
            "bottleneck_category": self.bottleneck_category,
            "member_bottleneck_ids": self.member_bottleneck_ids,
            "frequency": self.frequency,
            "average_duration": self.average_duration,
            "most_common_context": self.most_common_context,
            "first_occurrence": self.first_occurrence,
            "last_occurrence": self.last_occurrence,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class DeterministicSynthesisResult:
    """Complete deterministic synthesis result.
    
    Contains all synthesis outputs in machine-readable format.
    """
    
    result_id: str
    synthesis_type: str
    synthesis_scope: str
    created_at: str
    
    # Synthesis outputs
    pattern_groupings: List[PatternGrouping] = field(default_factory=list)
    approval_reason_groupings: List[ApprovalReasonGrouping] = field(default_factory=list)
    proposal_outcome_groupings: List[ProposalOutcomeGrouping] = field(default_factory=list)
    confidence_trend_summaries: List[ConfidenceTrendSummary] = field(default_factory=list)
    bottleneck_recurrence_summaries: List[BottleneckRecurrenceSummary] = field(default_factory=list)
    
    # Metadata
    source_record_count: int = 0
    processing_duration_ms: Optional[int] = None
    operator_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "result_id": self.result_id,
            "synthesis_type": self.synthesis_type,
            "synthesis_scope": self.synthesis_scope,
            "created_at": self.created_at,
            "pattern_groupings": [pg.to_dict() for pg in self.pattern_groupings],
            "approval_reason_groupings": [arg.to_dict() for arg in self.approval_reason_groupings],
            "proposal_outcome_groupings": [pog.to_dict() for pog in self.proposal_outcome_groupings],
            "confidence_trend_summaries": [cts.to_dict() for cts in self.confidence_trend_summaries],
            "bottleneck_recurrence_summaries": [brs.to_dict() for brs in self.bottleneck_recurrence_summaries],
            "source_record_count": self.source_record_count,
            "processing_duration_ms": self.processing_duration_ms,
            "operator_notes": self.operator_notes,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# DETERMINISTIC SYNTHESIS ENGINE
# ============================================================================


class DeterministicSynthesisEngine:
    """Engine for deterministic insight synthesis.
    
    Read-only synthesis from existing records only.
    No optimization, no remediation, no orchestration, no recommendations.
    """
    
    def __init__(self, audit_ledger: Optional[AuditLedger] = None):
        """Initialize synthesis engine."""
        self.audit_ledger = audit_ledger
        self._cached_synthesis_results: Dict[str, DeterministicSynthesisResult] = {}
    
    def synthesize_patterns(
        self,
        records: List[Dict[str, Any]],
        pattern_type: str = "repetition",
        min_frequency: int = 2,
    ) -> List[PatternGrouping]:
        """Stable pattern grouping from existing records.
        
        Reads existing records and groups them by pattern.
        No mutation of source records.
        """
        patterns: Dict[str, List[str]] = {}
        
        for record in records:
            # Extract pattern key from record (read-only)
            pattern_key = self._extract_pattern_key(record, pattern_type)
            if pattern_key:
                if pattern_key not in patterns:
                    patterns[pattern_key] = []
                patterns[pattern_key].append(record.get("record_id", "unknown"))
        
        # Filter by minimum frequency (read-only filtering)
        pattern_groupings = []
        for pattern_id, (pattern_key, member_ids) in enumerate(patterns.items()):
            if len(member_ids) >= min_frequency:
                pattern_grouping = PatternGrouping(
                    pattern_id=f"pattern_{pattern_id:03d}",
                    pattern_type=pattern_type,
                    criteria={"key": pattern_key},
                    member_record_ids=member_ids,
                    frequency=len(member_ids),
                )
                pattern_groupings.append(pattern_grouping)
        
        return pattern_groupings
    
    def synthesize_approval_reasons(
        self,
        approval_events: List[Dict[str, Any]],
    ) -> List[ApprovalReasonGrouping]:
        """Repeated approval/rejection reason grouping.
        
        Groups approval events by reason text.
        No mutation of source events.
        """
        reasons: Dict[str, Dict[str, Any]] = {}
        
        for event in approval_events:
            # Extract reason (read-only)
            reason_text = event.get("approval_notes", "no_reason")
            event_id = event.get("event_id", "unknown")
            approval_status = event.get("approval_status", "unknown")
            
            if reason_text not in reasons:
                reasons[reason_text] = {
                    "reason_ids": [],
                    "approved": 0,
                    "total": 0,
                }
            
            reasons[reason_text]["reason_ids"].append(event_id)
            reasons[reason_text]["total"] += 1
            if approval_status == "approved":
                reasons[reason_text]["approved"] += 1
        
        # Build groupings (read-only transformation)
        reason_groupings = []
        for i, (reason_text, data) in enumerate(reasons.items()):
            approval_rate = data["approved"] / data["total"] if data["total"] > 0 else 0.0
            
            reason_grouping = ApprovalReasonGrouping(
                reason_id=f"reason_{i:03d}",
                reason_type="approval" if "approved" in reason_text.lower() else "rejection",
                reason_text=reason_text,
                member_record_ids=data["reason_ids"],
                frequency=data["total"],
                approval_rate=approval_rate,
            )
            reason_groupings.append(reason_grouping)
        
        return reason_groupings
    
    def synthesize_proposal_outcomes(
        self,
        proposals: List[Dict[str, Any]],
    ) -> List[ProposalOutcomeGrouping]:
        """Recurring proposal outcome grouping.
        
        Groups proposals by outcome category.
        No mutation of source proposals.
        """
        outcomes: Dict[str, List[str]] = {}
        
        for proposal in proposals:
            # Extract outcome (read-only)
            outcome_category = proposal.get("state", "unknown")
            proposal_id = proposal.get("proposal_id", "unknown")
            
            if outcome_category not in outcomes:
                outcomes[outcome_category] = []
            outcomes[outcome_category].append(proposal_id)
        
        # Build groupings (read-only transformation)
        outcome_groupings = []
        for i, (category, proposal_ids) in enumerate(outcomes.items()):
            outcome_grouping = ProposalOutcomeGrouping(
                outcome_id=f"outcome_{i:03d}",
                outcome_category=category,
                member_proposal_ids=proposal_ids,
                frequency=len(proposal_ids),
            )
            outcome_groupings.append(outcome_grouping)
        
        return outcome_groupings
    
    def synthesize_confidence_trends(
        self,
        confidence_records: List[Dict[str, Any]],
    ) -> List[ConfidenceTrendSummary]:
        """Confidence trend summary synthesis.
        
        Synthesizes confidence trends from existing records.
        No predictive modeling.
        """
        trends: Dict[str, List[float]] = {}
        
        for record in confidence_records:
            # Extract confidence value (read-only)
            confidence_value = record.get("confidence", 0.5)
            trend_type = record.get("trend_type", "stable")
            
            if trend_type not in trends:
                trends[trend_type] = []
            trends[trend_type].append(confidence_value)
        
        # Build summaries (read-only transformation)
        trend_summaries = []
        for i, (trend_type, values) in enumerate(trends.items()):
            if len(values) < 2:
                continue
            
            before_confidence = values[0]
            after_confidence = values[-1]
            confidence_change = after_confidence - before_confidence
            
            # Determine direction (read-only calculation)
            if confidence_change > 0.05:
                direction = "up"
            elif confidence_change < -0.05:
                direction = "down"
            elif abs(confidence_change) <= 0.05:
                direction = "stable"
            else:
                direction = "variable"
            
            trend_summary = ConfidenceTrendSummary(
                trend_id=f"trend_{i:03d}",
                trend_type=trend_type,
                before_confidence=before_confidence,
                after_confidence=after_confidence,
                confidence_change=confidence_change,
                confidence_direction=direction,
                member_record_ids=[f"record_{j}" for j in range(len(values))],
                frequency=len(values),
            )
            trend_summaries.append(trend_summary)
        
        return trend_summaries
    
    def synthesize_bottleneck_recurrences(
        self,
        bottleneck_events: List[Dict[str, Any]],
    ) -> List[BottleneckRecurrenceSummary]:
        """Bottleneck recurrence summary grounded in existing records only.
        
        Groups bottleneck events by type and category.
        No optimization or remediation.
        """
        bottlenecks: Dict[str, List[str]] = {}
        
        for event in bottleneck_events:
            # Extract bottleneck info (read-only)
            bottleneck_type = event.get("bottleneck_type", "unknown")
            bottleneck_id = event.get("bottleneck_id", "unknown")
            bottleneck_category = event.get("bottleneck_category", "process")
            
            key = f"{bottleneck_type}:{bottleneck_category}"
            if key not in bottlenecks:
                bottlenecks[key] = []
            bottlenecks[key].append(bottleneck_id)
        
        # Build summaries (read-only transformation)
        bottleneck_summaries = []
        for i, (key, bottleneck_ids) in enumerate(bottlenecks.items()):
            bottleneck_type, bottleneck_category = key.split(":", 1)
            
            bottleneck_summary = BottleneckRecurrenceSummary(
                bottleneck_id=f"bottleneck_{i:03d}",
                bottleneck_type=bottleneck_type,
                bottleneck_category=bottleneck_category,
                member_bottleneck_ids=bottleneck_ids,
                frequency=len(bottleneck_ids),
            )
            bottleneck_summaries.append(bottleneck_summary)
        
        return bottleneck_summaries
    
    def synthesize_all(
        self,
        records: List[Dict[str, Any]],
        scope: str = "global",
    ) -> DeterministicSynthesisResult:
        """Complete deterministic synthesis from existing records.
        
        Single-pass read-only analysis.
        No mutation, no optimization, no recommendations.
        """
        import time
        start_time = time.time()
        
        # Extract different record types (read-only)
        approval_events = self._filter_events_by_type(records, "approval")
        proposals = self._filter_records_by_type(records, "proposal")
        confidence_records = self._filter_records_by_type(records, "confidence")
        bottleneck_events = self._filter_records_by_type(records, "bottleneck")
        
        # Perform all synthesis (read-only)
        pattern_groupings = self.synthesize_patterns(records, min_frequency=2)
        approval_reason_groupings = self.synthesize_approval_reasons(approval_events)
        proposal_outcome_groupings = self.synthesize_proposal_outcomes(proposals)
        confidence_trend_summaries = self.synthesize_confidence_trends(confidence_records)
        bottleneck_recurrence_summaries = self.synthesize_bottleneck_recurrences(bottleneck_events)
        
        end_time = time.time()
        processing_duration_ms = int((end_time - start_time) * 1000)
        
        # Build result (read-only composition)
        result = DeterministicSynthesisResult(
            result_id=f"synth_{uuid.uuid4().hex[:8]}",
            synthesis_type="complete",
            synthesis_scope=scope,
            created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            pattern_groupings=pattern_groupings,
            approval_reason_groupings=approval_reason_groupings,
            proposal_outcome_groupings=proposal_outcome_groupings,
            confidence_trend_summaries=confidence_trend_summaries,
            bottleneck_recurrence_summaries=bottleneck_recurrence_summaries,
            source_record_count=len(records),
            processing_duration_ms=processing_duration_ms,
        )
        
        self._cached_synthesis_results[result.result_id] = result
        return result
    
    def _extract_pattern_key(self, record: Dict[str, Any], pattern_type: str) -> Optional[str]:
        """Extract pattern key from record (read-only)."""
        if pattern_type == "repetition":
            # Simple repetition pattern based on pattern_data field or record type + content
            pattern_data = record.get("pattern_data")
            if pattern_data:
                return pattern_data
            # Fallback: record type for simple grouping
            return record.get("record_type", "unknown")
        return None
    
    def _filter_events_by_type(self, records: List[Dict[str, Any]], event_type: str) -> List[Dict[str, Any]]:
        """Filter records by event type (read-only)."""
        return [r for r in records if r.get("event_type") == event_type]
    
    def _filter_records_by_type(self, records: List[Dict[str, Any]], record_type: str) -> List[Dict[str, Any]]:
        """Filter records by type (read-only)."""
        return [r for r in records if r.get("record_type") == record_type]
    
    def get_synthesis_result(self, result_id: str) -> Optional[DeterministicSynthesisResult]:
        """Get cached synthesis result by ID."""
        return self._cached_synthesis_results.get(result_id)
    
    def export_to_json(self, result: DeterministicSynthesisResult, filepath: Optional[str] = None) -> str:
        """Export synthesis result to JSON.
        
        Machine-readable format only.
        """
        json_output = result.to_json()
        if filepath:
            with open(filepath, "w") as f:
                f.write(json_output)
        return json_output


# ============================================================================
# OPERATOR-FACING TEXT FORMATTER
# ============================================================================


class DeterministicSynthesisFormatter:
    """Operator-readable text formatter for deterministic synthesis results.
    
    Text formatting only - no logic, no recommendations.
    """
    
    @staticmethod
    def format_pattern_grouping(pg: PatternGrouping) -> str:
        """Format pattern grouping for operator readability."""
        lines = [
            f"Pattern Grouping: {pg.pattern_id}",
            f"  Type: {pg.pattern_type}",
            f"  Criteria: {json.dumps(pg.criteria)}",
            f"  Members: {len(pg.member_record_ids)} records",
            f"  Frequency: {pg.frequency}",
        ]
        return "\n".join(lines)
    
    @staticmethod
    def format_approval_reason_grouping(arg: ApprovalReasonGrouping) -> str:
        """Format approval reason grouping for operator readability."""
        lines = [
            f"Approval Reason: {arg.reason_id}",
            f"  Type: {arg.reason_type}",
            f"  Reason: {arg.reason_text}",
            f"  Members: {len(arg.member_record_ids)} events",
            f"  Frequency: {arg.frequency}",
            f"  Approval Rate: {arg.approval_rate:.1%}",
        ]
        return "\n".join(lines)
    
    @staticmethod
    def format_proposal_outcome_grouping(pog: ProposalOutcomeGrouping) -> str:
        """Format proposal outcome grouping for operator readability."""
        lines = [
            f"Proposal Outcome: {pog.outcome_id}",
            f"  Category: {pog.outcome_category}",
            f"  Members: {len(pog.member_proposal_ids)} proposals",
            f"  Frequency: {pog.frequency}",
        ]
        return "\n".join(lines)
    
    @staticmethod
    def format_confidence_trend_summary(cts: ConfidenceTrendSummary) -> str:
        """Format confidence trend summary for operator readability."""
        lines = [
            f"Confidence Trend: {cts.trend_id}",
            f"  Type: {cts.trend_type}",
            f"  Before: {cts.before_confidence:.2f}",
            f"  After: {cts.after_confidence:.2f}",
            f"  Change: {cts.confidence_change:+.2f}",
            f"  Direction: {cts.confidence_direction}",
            f"  Members: {len(cts.member_record_ids)} records",
            f"  Frequency: {cts.frequency}",
        ]
        return "\n".join(lines)
    
    @staticmethod
    def format_bottleneck_recurrence_summary(brs: BottleneckRecurrenceSummary) -> str:
        """Format bottleneck recurrence summary for operator readability."""
        lines = [
            f"Bottleneck: {brs.bottleneck_id}",
            f"  Type: {brs.bottleneck_type}",
            f"  Category: {brs.bottleneck_category}",
            f"  Members: {len(brs.member_bottleneck_ids)} events",
            f"  Frequency: {brs.frequency}",
        ]
        return "\n".join(lines)
    
    @classmethod
    def format_result(cls, result: DeterministicSynthesisResult) -> str:
        """Format complete synthesis result for operator readability."""
        sections = [
            "=" * 60,
            "DETERMINISTIC INSIGHT SYNTHESIS REPORT",
            "=" * 60,
            f"Result ID: {result.result_id}",
            f"Scope: {result.synthesis_scope}",
            f"Created: {result.created_at}",
            f"Source Records: {result.source_record_count}",
            f"Processing Time: {result.processing_duration_ms or 0}ms",
            "",
        ]
        
        # Pattern Groupings
        sections.append("-" * 40)
        sections.append(f"PATTERN GROUPINGS ({len(result.pattern_groupings)})")
        sections.append("-" * 40)
        for pg in result.pattern_groupings:
            sections.append(cls.format_pattern_grouping(pg))
            sections.append("")
        
        # Approval Reason Groupings
        sections.append("-" * 40)
        sections.append(f"APPROVAL REASON GROUPINGS ({len(result.approval_reason_groupings)})")
        sections.append("-" * 40)
        for arg in result.approval_reason_groupings:
            sections.append(cls.format_approval_reason_grouping(arg))
            sections.append("")
        
        # Proposal Outcome Groupings
        sections.append("-" * 40)
        sections.append(f"PROPOSAL OUTCOME GROUPINGS ({len(result.proposal_outcome_groupings)})")
        sections.append("-" * 40)
        for pog in result.proposal_outcome_groupings:
            sections.append(cls.format_proposal_outcome_grouping(pog))
            sections.append("")
        
        # Confidence Trend Summaries
        sections.append("-" * 40)
        sections.append(f"CONFIDENCE TREND SUMMARIES ({len(result.confidence_trend_summaries)})")
        sections.append("-" * 40)
        for cts in result.confidence_trend_summaries:
            sections.append(cls.format_confidence_trend_summary(cts))
            sections.append("")
        
        # Bottleneck Recurrence Summaries
        sections.append("-" * 40)
        sections.append(f"BOTTLENECK RECURRENCE SUMMARIES ({len(result.bottleneck_recurrence_summaries)})")
        sections.append("-" * 40)
        for brs in result.bottleneck_recurrence_summaries:
            sections.append(cls.format_bottleneck_recurrence_summary(brs))
            sections.append("")
        
        return "\n".join(sections)
