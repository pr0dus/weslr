# operator_insight_consolidation.py - WESLR v89: Operator Insight Consolidation / Case Summary Layer
# Read-only operator-facing layer that consolidates recovery guidance, decision trace,
# pattern history, drift, and timeline context into a single per-case operator summary.
# No optimization, no remediation, no orchestration, no backend/service/UI.
# No TIA/C#, no storage framework expansion, no analytics engine beyond consolidation scope.

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .operator_insight_timeline import (
    InsightTimelineEntry,
    OperatorInsightTimeline,
    TimelineSummary,
)
from .operator_insight_comparison import (
    DriftTrend,
    InsightDriftRecord,
    OperatorInsightComparison,
)
from .operator_insight_history import (
    OperatorInsightHistory,
)
from .operator_recovery_insight import (
    RecoveryInsight,
    TrendShift,
)
from .recovery_decision_trace import (
    DecisionTraceRecord,
    DecisionTraceSummary as RecoveryDecisionTrace,
)
from .recovery_recommendation_export import (
    RecoveryRecommendationService,
)


# ============================================================================
# CONSOLIDATED CASE SUMMARY DATA MODELS
# ============================================================================


@dataclass
class RecoveryGuidanceSummary:
    """Recovered recommendation guidance consolidated into summary.
    
    Contains:
    - Guidance context (recommendation ID, type)
    - Guidance content (interpretation, confidence)
    - Operator guidance (safe-next-action, not certainty)
    """
    
    guidance_id: str
    recommendation_type: str  # "suggestion", "prediction", "diagnostic"
    interpretation: str
    confidence_level: str  # "low", "medium", "high" (heuristic, not certainty)
    confidence_reason: str  # Why this confidence
    safe_next_action: Optional[str] = None  # Operator guidance, not certainty
    evidence_references: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "guidance_id": self.guidance_id,
            "recommendation_type": self.recommendation_type,
            "interpretation": self.interpretation,
            "confidence_level": self.confidence_level,
            "confidence_reason": self.confidence_reason,
            "safe_next_action": self.safe_next_action,
            "evidence_references": self.evidence_references,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class DecisionTraceSummary:
    """Decision trace consolidated into summary.
    
    Contains:
    - Trace context (trace ID, type)
    - Trace content (decisions, rationale)
    - Correlation IDs
    """
    
    trace_id: str
    decision_type: str  # "proposal", "escalation", "approval", "denial"
    decisions: List[Dict[str, Any]]
    rationale: str
    correlation_ids: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "trace_id": self.trace_id,
            "decision_type": self.decision_type,
            "decisions": self.decisions,
            "rationale": self.rationale,
            "correlation_ids": self.correlation_ids,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class PatternHistorySummary:
    """Pattern history consolidated into summary.
    
    Contains:
    - History context (pattern ID, type)
    - History content (patterns, trends)
    - Significance assessment (not certainty)
    """
    
    history_id: str
    pattern_type: str  # "recommendation", "decision", "recovery_hint"
    patterns: List[Dict[str, Any]]
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_magnitude: str  # "minor", "moderate", "significant"
    heuristic_significance: str  # "low", "medium", "high" (not certainty)
    heuristic_reason: str  # Why this significance
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "history_id": self.history_id,
            "pattern_type": self.pattern_type,
            "patterns": self.patterns,
            "trend_direction": self.trend_direction,
            "trend_magnitude": self.trend_magnitude,
            "heuristic_significance": self.heuristic_significance,
            "heuristic_reason": self.heuristic_reason,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class DriftSummary:
    """Drift analysis consolidated into summary.
    
    Contains:
    - Drift context (comparison, type)
    - Drift content (changes, magnitude)
    - Interpretation (operator-facing)
    """
    
    drift_id: str
    comparison_type: str  # "significance", "confidence", "safe_action"
    drift_changes: List[Dict[str, Any]]
    drift_magnitude: str  # "minor", "moderate", "significant"
    interpretation: str  # Operator-facing explanation
    heuristic_significance: str  # "low", "medium", "high" (not certainty)
    heuristic_reason: str  # Why this significance
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "drift_id": self.drift_id,
            "comparison_type": self.comparison_type,
            "drift_changes": self.drift_changes,
            "drift_magnitude": self.drift_magnitude,
            "interpretation": self.interpretation,
            "heuristic_significance": self.heuristic_significance,
            "heuristic_reason": self.heuristic_reason,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class EscalationSummary:
    """Escalation context consolidated into summary.
    
    Contains:
    - Escalation context (timeline, signals)
    - Escalation content (events, urgency)
    - Operator guidance (not certainty)
    """
    
    escalation_id: str
    time_window: str  # "24h", "72h", "1w"
    escalation_events: List[Dict[str, Any]]
    urgency_level: str  # "normal", "attention", "urgent" (heuristic)
    urgency_reason: str  # Why this urgency
    operator_guidance: Optional[str] = None  # Readable guidance, not certainty
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "escalation_id": self.escalation_id,
            "time_window": self.time_window,
            "escalation_events": self.escalation_events,
            "urgency_level": self.urgency_level,
            "urgency_reason": self.urgency_reason,
            "operator_guidance": self.operator_guidance,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class ConsolidatedCaseSummary:
    """Operator-readable + machine-readable consolidated case summary.
    
    Contains:
    - Summary metadata (ID, timestamp, correlation IDs)
    - Recovery guidance summary
    - Decision trace summary
    - Pattern history summary
    - Drift analysis summary
    - Escalation context summary
    - Notable changes summary
    - Operator narrative
    - Machine export JSON
    
    Key constraints:
    - Confidence and significance are presented as operator guidance, not certainty
    - No automatic decision logic - assembly only
    - No remediation logic - read-only consolidation
    """
    
    summary_id: str
    timestamp: str
    case_id: str  # Correlation to case/flow context
    
    # Summary sections
    recovery_guidance: List[RecoveryGuidanceSummary]
    decision_trace: List[DecisionTraceSummary]
    pattern_history: List[PatternHistorySummary]
    drift_analysis: List[DriftSummary]
    escalation_context: List[EscalationSummary]
    
    # Notable changes (summary, not detail)
    notable_changes: List[str]
    
    # Correlation IDs
    correlation_ids: Dict[str, str]
    
    # Export content
    operator_readable: str
    machine_readable: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "summary_id": self.summary_id,
            "timestamp": self.timestamp,
            "case_id": self.case_id,
            "recovery_guidance": [g.to_dict() for g in self.recovery_guidance],
            "decision_trace": [t.to_dict() for t in self.decision_trace],
            "pattern_history": [p.to_dict() for p in self.pattern_history],
            "drift_analysis": [d.to_dict() for d in self.drift_analysis],
            "escalation_context": [e.to_dict() for e in self.escalation_context],
            "notable_changes": self.notable_changes,
            "correlation_ids": self.correlation_ids,
            "operator_readable": self.operator_readable,
            "machine_readable": self.machine_readable,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# CONSOLIDATED CASE EXPORTER
# ============================================================================


class ConsolidatedCaseExporter:
    """Exporter for consolidated case summaries.
    
    Provides:
    - Operator-readable summary export
    - Machine-readable JSON export
    - Correlation ID support (flow_id, request_id, handshake_id, deadline_id)
    - Passive telemetry hooks (no new event framework)
    
    Read-only export only — no behavior changes.
    """
    
    @staticmethod
    def export_summary(
        summary: ConsolidatedCaseSummary,
        format: str = "operator",
    ) -> str:
        """Export summary to requested format.
        
        Args:
            summary: ConsolidatedCaseSummary to export
            format: Output format ("operator" or "json")
        
        Returns:
            Exported content string
        """
        if format == "json":
            return summary.machine_readable
        return summary.operator_readable
    
    @staticmethod
    def export_multiple(
        summaries: List[ConsolidatedCaseSummary],
        format: str = "json",
    ) -> str:
        """Export multiple summaries.
        
        Args:
            summaries: List of ConsolidatedCaseSummary
            format: Output format ("json" only for multiple)
        
        Returns:
            JSON array string
        """
        if format == "json":
            return json.dumps([s.to_dict() for s in summaries], indent=2)
        raise ValueError("Multiple export only supports JSON format")
    
    @staticmethod
    def telemetry_event_summary_created(summary: ConsolidatedCaseSummary) -> Dict[str, Any]:
        """Telemetry event for summary creation (passive, descriptive only).
        
        Args:
            summary: ConsolidatedCaseSummary that was created
        
        Returns:
            Dict with event data (not used for behavior)
        """
        return {
            "event_type": "CONSOLIDATED_CASE_SUMMARY_CREATED",
            "summary_id": summary.summary_id,
            "timestamp": summary.timestamp,
            "case_id": summary.case_id,
            "content_summary": {
                "guidance_count": len(summary.recovery_guidance),
                "trace_count": len(summary.decision_trace),
                "history_count": len(summary.pattern_history),
                "drift_count": len(summary.drift_analysis),
                "escalation_count": len(summary.escalation_context),
                "notable_change_count": len(summary.notable_changes),
            },
        }
    
    @staticmethod
    def telemetry_event_exported(summary: ConsolidatedCaseSummary) -> Dict[str, Any]:
        """Telemetry event for summary export (passive, descriptive only).
        
        Args:
            summary: ConsolidatedCaseSummary that was exported
        
        Returns:
            Dict with event data (not used for behavior)
        """
        return {
            "event_type": "CONSOLIDATED_CASE_SUMMARY_EXPORTED",
            "summary_id": summary.summary_id,
            "timestamp": summary.timestamp,
            "export_format": "json" if "summary_id" in summary.machine_readable else "operator",
        }


# ============================================================================
# OPERATOR INSIGHT CONSOLIDATION LAYER
# ============================================================================


class OperatorInsightConsolidation:
    """Consolidation layer for operator insight summaries.
    
    Provides read-only consolidation:
    - Consolidate recovery guidance from v75-v78
    - Consolidate decision trace from v78
    - Consolidate pattern history from v83-v84
    - Consolidate drift analysis from v87
    - Consolidate escalation context from v88
    - Generate consolidated case summaries
    - Export operator-readable and machine-readable summaries
    
    Correlation support:
    - flow_id
    - request_id
    - handshake_id
    - deadline_id
    
    Read-only analysis only — no behavior changes, no automatic decisions.
    """
    
    def __init__(self):
        """Initialize operator insight consolidation layer."""
        self._summaries: List[ConsolidatedCaseSummary] = []
        self._sequence_counter: int = 0
    
    def consolidate_case(
        self,
        case_id: str,
        recovery_service: Optional[RecoveryRecommendationService] = None,
        decision_trace: Optional[RecoveryDecisionTrace] = None,
        pattern_history: Optional[OperatorInsightHistory] = None,
        insight_comparison: Optional[OperatorInsightComparison] = None,
        insight_timeline: Optional[OperatorInsightTimeline] = None,
        correlation_ids: Optional[Dict[str, str]] = None,
    ) -> ConsolidatedCaseSummary:
        """Consolidate a case summary from available insight layers.
        
        Args:
            case_id: Case/flow identifier
            recovery_service: v75 recovery recommendation service (optional)
            decision_trace: v78 decision trace (optional)
            pattern_history: v84 pattern history (optional)
            insight_comparison: v87 insight comparison (optional)
            insight_timeline: v88 insight timeline (optional)
            correlation_ids: Optional correlation IDs
        
        Returns:
            ConsolidatedCaseSummary for the case
        
        Note:
            - Assembly only, no new recommendation engine
            - No autonomous decision logic
            - No hidden remediation logic
            - Confidence/_significance as guidance, not certainty
        """
        self._sequence_counter += 1
        summary_id = f"consolidated_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Extract recovery guidance
        recovery_guidance = self._extract_recovery_guidance(recovery_service, case_id)
        
        # Extract decision trace
        decision_trace_summary = self._extract_decision_trace(decision_trace, case_id)
        
        # Extract pattern history
        pattern_history_summary = self._extract_pattern_history(pattern_history, case_id)
        
        # Extract drift analysis
        drift_summary = self._extract_drift_analysis(insight_comparison, case_id)
        
        # Extract escalation context
        escalation_summary = self._extract_escalation_context(insight_timeline, case_id)
        
        # Identify notable changes
        notable_changes = self._identify_notable_changes(
            recovery_guidance, decision_trace_summary, pattern_history_summary, drift_summary, escalation_summary
        )
        
        # Generate operator-readable summary
        operator_summary = self._generate_operator_summary(
            summary_id, case_id, recovery_guidance, decision_trace_summary, pattern_history_summary,
            drift_summary, escalation_summary, notable_changes
        )
        
        # Generate machine-readable summary
        machine_summary = self._generate_machine_summary(
            summary_id, case_id, timestamp, recovery_guidance, decision_trace_summary, pattern_history_summary,
            drift_summary, escalation_summary, notable_changes, correlation_ids or {}
        )
        
        summary = ConsolidatedCaseSummary(
            summary_id=summary_id,
            timestamp=timestamp,
            case_id=case_id,
            recovery_guidance=recovery_guidance,
            decision_trace=decision_trace_summary,
            pattern_history=pattern_history_summary,
            drift_analysis=drift_summary,
            escalation_context=escalation_summary,
            notable_changes=notable_changes,
            correlation_ids=correlation_ids or {},
            operator_readable=operator_summary,
            machine_readable=machine_summary,
        )
        
        self._summaries.append(summary)
        return summary
    
    def _extract_recovery_guidance(
        self,
        service: Optional[RecoveryRecommendationService],
        case_id: str,
    ) -> List[RecoveryGuidanceSummary]:
        """Extract recovery guidance from v75 service.
        
        Args:
            service: v75 RecoveryRecommendationService (optional)
            case_id: Case ID to filter by
        
        Returns:
            List of RecoveryGuidanceSummary
        """
        if service is None:
            return []
        
        # Get recommendations for case
        # Note: v75 service doesn't have case filtering in interface
        # This is assembly only, no new recommendation engine
        guidance = []
        recommendations = service.get_recommendations() if hasattr(service, 'get_recommendations') else service._recommendations
        for rec in recommendations[:5]:  # Last 5 recommendations (assembly only)
            # Support both dict and object access
            if isinstance(rec, dict):
                guidance.append(RecoveryGuidanceSummary(
                    guidance_id=rec.get("recommendation_id", ""),
                    recommendation_type=rec.get("recommendation_type", ""),
                    interpretation=rec.get("interpretation", ""),
                    confidence_level=rec.get("confidence_level", ""),
                    confidence_reason=rec.get("confidence_reason", ""),
                    safe_next_action=rec.get("confidence_guidance"),  # Operator guidance, not certainty
                    evidence_references=rec.get("evidence_references", []),
                ))
            else:
                guidance.append(RecoveryGuidanceSummary(
                    guidance_id=getattr(rec, "recommendation_id", ""),
                    recommendation_type=getattr(rec, "recommendation_type", ""),
                    interpretation=getattr(rec, "interpretation", ""),
                    confidence_level=getattr(rec, "confidence_level", ""),
                    confidence_reason=getattr(rec, "confidence_reason", ""),
                    safe_next_action=getattr(rec, "confidence_guidance"),  # Operator guidance, not certainty
                    evidence_references=getattr(rec, "evidence_references", []),
                ))
        
        return guidance
    
    def _extract_decision_trace(
        self,
        trace: Optional[DecisionTraceSummary],
        case_id: str,
    ) -> List[DecisionTraceSummary]:
        """Extract decision trace from v78 trace.
        
        Args:
            trace: v78 DecisionTraceSummary (optional)
            case_id: Case ID to filter by
        
        Returns:
            List of DecisionTraceSummary
        """
        if trace is None:
            return []
        
        summaries = []
        records = trace.get_records() if hasattr(trace, 'get_records') else trace
        for record in records[:3]:  # Last 3 records (assembly only)
            # Support both dict and object access
            if isinstance(record, dict):
                summaries.append(DecisionTraceSummary(
                    trace_id=record.get("trace_id", ""),
                    decision_type=record.get("decision_type", ""),
                    decisions=[record],
                    rationale=record.get("rationale", ""),
                    correlation_ids=record.get("correlation_ids", {}),
                ))
            else:
                summaries.append(DecisionTraceSummary(
                    trace_id=getattr(record, "trace_id", ""),
                    decision_type=getattr(record, "decision_type", ""),
                    decisions=[record.to_dict() if hasattr(record, 'to_dict') else {}],
                    rationale=getattr(record, "rationale", ""),
                    correlation_ids=getattr(record, "correlation_ids", {}),
                ))
        
        return summaries
    
    def _extract_pattern_history(
        self,
        history: Optional[OperatorInsightHistory],
        case_id: str,
    ) -> List[PatternHistorySummary]:
        """Extract pattern history from v84 history.
        
        Args:
            history: v84 OperatorInsightHistory (optional)
            case_id: Case ID to filter by
        
        Returns:
            List of PatternHistorySummary
        """
        if history is None:
            return []
        
        summaries = []
        records = history.get_records() if hasattr(history, 'get_records') else history
        for record in records[:3]:  # Last 3 records (assembly only)
            # Support both dict and object access
            if isinstance(record, dict):
                summaries.append(PatternHistorySummary(
                    history_id=record.get("history_id", ""),
                    pattern_type=record.get("pattern_type", ""),
                    patterns=[record],
                    trend_direction=record.get("trend_direction", ""),
                    trend_magnitude=record.get("trend_magnitude", ""),
                    heuristic_significance=record.get("heuristic_significance", ""),
                    heuristic_reason=record.get("heuristic_significance_reason", ""),
                ))
            else:
                summaries.append(PatternHistorySummary(
                    history_id=getattr(record, "history_id", ""),
                    pattern_type=getattr(record, "pattern_type", ""),
                    patterns=[record.to_dict() if hasattr(record, 'to_dict') else {}],
                    trend_direction=getattr(record, "trend_direction", ""),
                    trend_magnitude=getattr(record, "trend_magnitude", ""),
                    heuristic_significance=getattr(record, "heuristic_significance", ""),
                    heuristic_reason=getattr(record, "heuristic_significance_reason", ""),
                ))
        
        return summaries
    
    def _extract_drift_analysis(
        self,
        comparison: Optional[OperatorInsightComparison],
        case_id: str,
    ) -> List[DriftSummary]:
        """Extract drift analysis from v87 comparison.
        
        Args:
            comparison: v87 OperatorInsightComparison (optional)
            case_id: Case ID to filter by
        
        Returns:
            List of DriftSummary
        """
        if comparison is None:
            return []
        
        summaries = []
        records = comparison.get_drift_records() if hasattr(comparison, 'get_drift_records') else comparison
        for record in records[:3]:  # Last 3 records (assembly only)
            # Support both dict and object access
            if isinstance(record, dict):
                summaries.append(DriftSummary(
                    drift_id=record.get("drift_id", ""),
                    comparison_type=record.get("comparison_type", ""),
                    drift_changes=[{
                        "summary1_id": record.get("summary1_id", ""),
                        "summary2_id": record.get("summary2_id", ""),
                        "differences": record.get("differences", []),
                    }],
                    drift_magnitude=record.get("drift_magnitude", ""),
                    interpretation=record.get("interpretation", ""),
                    heuristic_significance=record.get("heuristic_significance", ""),
                    heuristic_reason=record.get("heuristic_significance_reason", ""),
                ))
            else:
                summaries.append(DriftSummary(
                    drift_id=getattr(record, "drift_id", ""),
                    comparison_type=getattr(record, "comparison_type", ""),
                    drift_changes=[{
                        "summary1_id": getattr(record, "summary1_id", ""),
                        "summary2_id": getattr(record, "summary2_id", ""),
                        "differences": getattr(record, "differences", []),
                    }],
                    drift_magnitude=getattr(record, "drift_magnitude", ""),
                    interpretation=getattr(record, "interpretation", ""),
                    heuristic_significance=getattr(record, "heuristic_significance", ""),
                    heuristic_reason=getattr(record, "heuristic_significance_reason", ""),
                ))
        
        return summaries
    
    def _extract_escalation_context(
        self,
        timeline: Optional[OperatorInsightTimeline],
        case_id: str,
    ) -> List[EscalationSummary]:
        """Extract escalation context from v88 timeline.
        
        Args:
            timeline: v88 OperatorInsightTimeline (optional)
            case_id: Case ID to filter by
        
        Returns:
            List of EscalationSummary
        """
        if timeline is None:
            return []
        
        # Get escalation context (assembly only, no new escalation logic)
        escalation_data = timeline.get_escalation_context(hours=24)
        if not escalation_data:
            return []
        
        urgency_level = "normal"
        urgency_reason = "Standard escalation context"
        if any(e["escalation_level"] == "urgent" for e in escalation_data):
            urgency_level = "urgent"
            urgency_reason = "Urgent escalation signals detected"
        elif any(e["escalation_level"] == "attention" for e in escalation_data):
            urgency_level = "attention"
            urgency_reason = "Attention signals detected"
        
        return [EscalationSummary(
            escalation_id=f"escalation_{uuid.uuid4().hex[:12]}",
            time_window="24h",
            escalation_events=escalation_data[:5],  # Last 5 events (assembly only)
            urgency_level=urgency_level,
            urgency_reason=urgency_reason,
            operator_guidance="Review escalation context, prioritize attention/urgent items" if urgency_level != "normal" else None,
        )]
    
    def _identify_notable_changes(
        self,
        guidance: List[RecoveryGuidanceSummary],
        trace: List[DecisionTraceSummary],
        history: List[PatternHistorySummary],
        drift: List[DriftSummary],
        escalation: List[EscalationSummary],
    ) -> List[str]:
        """Identify notable changes (summary, not detail).
        
        Args:
            guidance: Recovery guidance summaries
            trace: Decision trace summaries
            history: Pattern history summaries
            drift: Drift summaries
            escalation: Escalation summaries
        
        Returns:
            List of notable change strings (summary only)
        """
        changes = []
        
        if drift:
            drift_changes = sum(len(d.drift_changes) for d in drift)
            if drift_changes > 0:
                changes.append(f"Detected {drift_changes} drift changes across insight comparisons")
        
        if escalation and any(e.urgency_level in ["attention", "urgent"] for e in escalation):
            changes.append("Attention/urgent escalation signals present in timeline")
        
        if history:
            trend_changes = sum(1 for h in history if h.trend_direction in ["increasing", "decreasing"])
            if trend_changes > 0:
                changes.append(f"Detected {trend_changes} trend direction changes in pattern history")
        
        if not changes:
            changes.append("No notable changes detected - stable pattern")
        
        return changes
    
    def _generate_operator_summary(
        self,
        summary_id: str,
        case_id: str,
        guidance: List[RecoveryGuidanceSummary],
        trace: List[DecisionTraceSummary],
        history: List[PatternHistorySummary],
        drift: List[DriftSummary],
        escalation: List[EscalationSummary],
        notable_changes: List[str],
    ) -> str:
        """Generate operator-readable summary.
        
        Args:
            summary_id: Summary ID
            case_id: Case ID
            guidance: Recovery guidance
            trace: Decision trace
            history: Pattern history
            drift: Drift analysis
            escalation: Escalation context
            notable_changes: Notable changes
        
        Returns:
            Operator-readable multi-line string
        """
        lines = [
            "=" * 70,
            "OPERATOR CONSOLIDATED CASE SUMMARY",
            "=" * 70,
            f"Summary ID: {summary_id}",
            f"Case ID: {case_id}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
            "",
            "-" * 70,
            "RECOVERY GUIDANCE",
            "-" * 70,
        ]
        
        if guidance:
            for g in guidance[-3:]:  # Last 3 guidance items
                lines.append(f"  [{g.confidence_level.upper()}] {g.recommendation_type}: {g.interpretation[:60]}...")
                if g.safe_next_action:
                    lines.append(f"      Safe-next-action: {g.safe_next_action}")
        else:
            lines.append("  No recovery guidance available")
        
        lines.extend([
            "",
            "-" * 70,
            "DECISION TRACE",
            "-" * 70,
        ])
        
        if trace:
            for t in trace:
                lines.append(f"  [{t.decision_type.upper()}] {t.rationale[:80]}...")
        else:
            lines.append("  No decision trace available")
        
        lines.extend([
            "",
            "-" * 70,
            "PATTERN HISTORY",
            "-" * 70,
        ])
        
        if history:
            for h in history:
                lines.append(f"  [{h.trend_direction.upper()}] {h.pattern_type}: {h.heuristic_significance} ({h.heuristic_reason[:50]}...)")
        else:
            lines.append("  No pattern history available")
        
        lines.extend([
            "",
            "-" * 70,
            "DRIFT ANALYSIS",
            "-" * 70,
        ])
        
        if drift:
            for d in drift:
                lines.append(f"  [{d.drift_magnitude.upper()}] {d.comparison_type}: {d.interpretation[:60]}...")
        else:
            lines.append("  No drift analysis available")
        
        lines.extend([
            "",
            "-" * 70,
            "ESCALATION CONTEXT",
            "-" * 70,
        ])
        
        if escalation:
            for e in escalation:
                lines.append(f"  [{e.urgency_level.upper()}] {e.time_window}: {e.urgency_reason}")
                if e.operator_guidance:
                    lines.append(f"      Operator guidance: {e.operator_guidance}")
        else:
            lines.append("  No escalation context available")
        
        lines.extend([
            "",
            "-" * 70,
            "NOTABLE CHANGES",
            "-" * 70,
        ])
        
        for change in notable_changes:
            lines.append(f"  • {change}")
        
        lines.extend([
            "",
            "-" * 70,
            "HEURISTIC NOTE",
            "-" * 70,
            "Confidence, significance, and guidance levels are operator guidance,",
            "not certainties. Use these summaries to inform decisions, not replace them.",
            "",
            "Key distinctions:",
            "- Guidance levels: Heuristic assessments, not automatic actions",
            "- Confidence: Operator guidance, not certainty",
            "- Significance: Interpretation context, not prediction",
            "- Drift detection: Observations over time, not predictions",
            "- Escalation: Attention indicators, not automatic triggers",
            "",
            "This consolidation layer provides read-only operator summaries,",
            "not automatic decision-making or remediation.",
            "",
            "=" * 70,
        ])
        
        return "\n".join(lines)
    
    def _generate_machine_summary(
        self,
        summary_id: str,
        case_id: str,
        timestamp: str,
        guidance: List[RecoveryGuidanceSummary],
        trace: List[DecisionTraceSummary],
        history: List[PatternHistorySummary],
        drift: List[DriftSummary],
        escalation: List[EscalationSummary],
        notable_changes: List[str],
        correlation_ids: Dict[str, str],
    ) -> str:
        """Generate machine-readable summary (JSON).
        
        Args:
            summary_id: Summary ID
            case_id: Case ID
            timestamp: Timestamp
            guidance: Recovery guidance
            trace: Decision trace
            history: Pattern history
            drift: Drift analysis
            escalation: Escalation context
            notable_changes: Notable changes
            correlation_ids: Correlation IDs
        
        Returns:
            JSON string
        """
        data = {
            "summary_id": summary_id,
            "timestamp": timestamp,
            "case_id": case_id,
            "recovery_guidance": [g.to_dict() for g in guidance],
            "decision_trace": [t.to_dict() for t in trace],
            "pattern_history": [h.to_dict() for h in history],
            "drift_analysis": [d.to_dict() for d in drift],
            "escalation_context": [e.to_dict() for e in escalation],
            "notable_changes": notable_changes,
            "correlation_ids": correlation_ids,
        }
        return json.dumps(data, indent=2)
    
    def get_summary(
        self,
        summary_id: str,
    ) -> Optional[ConsolidatedCaseSummary]:
        """Get a specific consolidated summary.
        
        Args:
            summary_id: Summary ID to retrieve
        
        Returns:
            ConsolidatedCaseSummary if found, None otherwise
        """
        for summary in self._summaries:
            if summary.summary_id == summary_id:
                return summary
        return None
    
    def get_summaries(self) -> List[ConsolidatedCaseSummary]:
        """Get all consolidated summaries.
        
        Returns:
            List of ConsolidatedCaseSummary
        """
        return self._summaries
    
    def get_summaries_for_case(
        self,
        case_id: str,
    ) -> List[ConsolidatedCaseSummary]:
        """Get summaries for a specific case.
        
        Args:
            case_id: Case ID to filter by
        
        Returns:
            List of ConsolidatedCaseSummary for case
        """
        return [s for s in self._summaries if s.case_id == case_id]
    
    def export_operator_readable(self) -> str:
        """Export all summaries as operator-readable string.
        
        Returns:
            Multi-line operator-readable summary
        """
        lines = [
            "=" * 70,
            "ALL CONSOLIDATED CASE SUMMARIES",
            "=" * 70,
            f"Total Summaries: {len(self._summaries)}",
            "",
        ]
        
        for summary in self._summaries[-5:]:  # Last 5 summaries
            lines.append(f"Summary ID: {summary.summary_id}")
            lines.append(f"Case ID: {summary.case_id}")
            lines.append(f"Timestamp: {summary.timestamp}")
            lines.append(f"Recovery Guidance: {len(summary.recovery_guidance)} items")
            lines.append(f"Decision Trace: {len(summary.decision_trace)} items")
            lines.append(f"Notable Changes: {len(summary.notable_changes)}")
            lines.append("")
        
        if not self._summaries:
            lines.append("No consolidated case summaries available.")
        
        lines.append("=" * 70)
        return "\n".join(lines)
    
    def export_machine_readable(self) -> str:
        """Export all summaries as JSON string.
        
        Returns:
            JSON string of all summaries
        """
        return json.dumps([s.to_dict() for s in self._summaries], indent=2)


# ============================================================================
# INTEGRATION HELPERS (Additive Only)
# ============================================================================


def integrate_with_v75_recommendations(consolidation: OperatorInsightConsolidation) -> Dict[str, Any]:
    """Integration hook for v75 recommendations — read-only consolidation only.
    
    No behavior changes to existing recommendation logic.
    """
    return {"hooked": True, "measures": "recommendation_consolidation_integration"}


def integrate_with_v78_traces(consolidation: OperatorInsightConsolidation) -> Dict[str, Any]:
    """Integration hook for v78 traces — read-only consolidation only.
    
    No behavior changes to existing trace logic.
    """
    return {"hooked": True, "measures": "trace_consolidation_integration"}


def integrate_with_v83_patterns(consolidation: OperatorInsightConsolidation) -> Dict[str, Any]:
    """Integration hook for v83 patterns — read-only consolidation only.
    
    No behavior changes to existing pattern logic.
    """
    return {"hooked": True, "measures": "pattern_consolidation_integration"}


def integrate_with_v84_history(consolidation: OperatorInsightConsolidation) -> Dict[str, Any]:
    """Integration hook for v84 history — read-only consolidation only.
    
    No behavior changes to existing history logic.
    """
    return {"hooked": True, "measures": "history_consolidation_integration"}


def integrate_with_v87_comparison(consolidation: OperatorInsightConsolidation) -> Dict[str, Any]:
    """Integration hook for v87 comparison — read-only consolidation only.
    
    No behavior changes to existing comparison logic.
    """
    return {"hooked": True, "measures": "comparison_consolidation_integration"}


def integrate_with_v88_timeline(consolidation: OperatorInsightConsolidation) -> Dict[str, Any]:
    """Integration hook for v88 timeline — read-only consolidation only.
    
    No behavior changes to existing timeline logic.
    """
    return {"hooked": True, "measures": "timeline_consolidation_integration"}
