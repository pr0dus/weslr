"""Operator Decision Trace + Correlated Recommendation Export (v78)

Read-only decision trace layer on top of v77 review surface.
Provides correlated decision records with rationale, confidence guidance,
and safe-next-action trace for distributed recovery recommendations.

Architecture:
  - DecisionTraceRecord — Machine-readable trace record
  - DecisionTraceExporter — Export hooks for diagnostics
  - DecisionTraceSummary — Operator-readable decision summary

Rules:
  - Read-only export only
  - Correlation by flow_id, request_id, handshake_id, deadline_id
  - Rationale trace (operator-facing explanation)
  - Confidence guidance trace (reliability, not certainty)
  - Safe-next-action trace (recommended action, risk level, fallbacks)
  - Machine-readable JSON export
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - No orchestration, sharding, aggregation
  - No scheduler/task engine
  - No TIA/C#
  - No backend/service/UI
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .distributed_diagnostic_hooks import (
    DiagnosticHooks,
    FailureClassification,
    FailureStage,
    FailureType,
)
from .recovery_recommendation_review import RecoveryRecommendationReviewSurface


# ============================================================================
# DECISION TRACE RECORD
# ============================================================================


@dataclass
class DecisionTraceRecord:
    """Machine-readable decision trace record for operator workflow.
    
    Links v77 recovery recommendations to distributed diagnostic trace
    chains via flow_id, request_id, handshake_id, and deadline_id.
    
    Contains:
      - Rationale trace (operator-facing explanation)
      - Confidence guidance trace (reliability indicator, not certainty)
      - Safe-next-action trace (recommended action, risk, verification, fallback)
    """
    
    trace_id: str
    recommendation_id: str
    timestamp: str
    correlation_ids: Dict[str, str]
    
    # Decision components
    rationale: str
    confidence_level: str
    confidence_explanation: str
    safe_next_action: Dict[str, Any]
    
    # Diagnostics integration
    failure_classification: Optional[FailureClassification] = None
    recovery_hint: Optional[str] = None
    likely_cause: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize record to dict."""
        return {
            "trace_id": self.trace_id,
            "recommendation_id": self.recommendation_id,
            "timestamp": self.timestamp,
            "correlation_ids": self.correlation_ids,
            "rationale": self.rationale,
            "confidence_level": self.confidence_level,
            "confidence_explanation": self.confidence_explanation,
            "safe_next_action": self.safe_next_action,
            "failure_classification": (
                self.failure_classification.to_dict()
                if self.failure_classification
                else None
            ),
            "recovery_hint": self.recovery_hint,
            "likely_cause": self.likely_cause,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionTraceRecord":
        """Deserialize record from dict."""
        return cls(
            trace_id=data.get("trace_id", str(uuid.uuid4())),
            recommendation_id=data.get("recommendation_id", ""),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            correlation_ids=data.get("correlation_ids", {}),
            rationale=data.get("rationale", ""),
            confidence_level=data.get("confidence_level", "medium"),
            confidence_explanation=data.get("confidence_explanation", ""),
            safe_next_action=data.get("safe_next_action", {}),
            failure_classification=(
                FailureClassification.from_dict(data["failure_classification"])
                if data.get("failure_classification")
                else None
            ),
            recovery_hint=data.get("recovery_hint"),
            likely_cause=data.get("likely_cause"),
        )

    def to_json(self, pretty: bool = True) -> str:
        """Serialize to JSON string."""
        if pretty:
            return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
        return json.dumps(self.to_dict(), ensure_ascii=False)


# ============================================================================
# DECISION TRACE EXPORTER
# ============================================================================


class DecisionTraceExporter:
    """Export hooks for decision traces into diagnostic trace chains.
    
    Provides read-only export of v77 recommendations with full decision trace.
    Does NOT execute or orchestrate recovery actions.
    """
    
    def __init__(self, diagnostic_hooks: DiagnosticHooks):
        """Initialize exporter with diagnostic hooks reference."""
        self._diagnostic_hooks = diagnostic_hooks
        self._export_records: Dict[str, DecisionTraceRecord] = {}
    
    def export_decision_trace(
        self,
        recommendation: Dict[str, Any],
        failure_classification: Optional[FailureClassification] = None,
        review_surface: Optional[RecoveryRecommendationReviewSurface] = None,
    ) -> DecisionTraceRecord:
        """Export a decision trace for a recovery recommendation.
        
        Args:
            recommendation: Recommendation dict from v77 review surface
            failure_classification: Optional failure classification for correlation
            review_surface: Optional v77 review surface for additional context
            
        Returns:
            Decision trace record with full decision context
        """
        trace_id = f"trace_{uuid.uuid4().hex[:8]}"
        recommendation_id = recommendation.get("recommendation_id", "")
        correlation_ids = recommendation.get("correlation_ids", {})
        
        # Build rationale from failure context
        rationale = self._build_rationale(
            recommendation.get("likely_cause"),
            recommendation.get("stage"),
            recommendation.get("failure_type"),
            failure_classification,
        )
        
        # Build confidence explanation (operator guidance)
        confidence_level = recommendation.get("confidence", "medium")
        confidence_explanation = (
            f"Operator guidance level: {confidence_level}. "
            f"This indicates reliability of the recommendation, "
            f"not guaranteed success of the recovery action."
        )
        
        # Build safe-next-action from review surface or inference
        safe_next_action = self._build_safe_next_action(
            recommendation,
            review_surface,
        )
        
        record = DecisionTraceRecord(
            trace_id=trace_id,
            recommendation_id=recommendation_id,
            timestamp=recommendation.get("generated_at", ""),
            correlation_ids=correlation_ids,
            rationale=rationale,
            confidence_level=confidence_level,
            confidence_explanation=confidence_explanation,
            safe_next_action=safe_next_action,
            failure_classification=failure_classification,
            recovery_hint=recommendation.get("recovery_hint"),
            likely_cause=recommendation.get("likely_cause"),
        )
        
        self._export_records[trace_id] = record
        return record
    
    def _build_rationale(
        self,
        likely_cause: Optional[str],
        stage: Optional[str],
        failure_type: Optional[str],
        failure_classification: Optional[FailureClassification],
    ) -> str:
        """Build operator-facing rationale explanation."""
        if likely_cause:
            return f"Based on analysis of {failure_type or 'unknown'} at {stage or 'unknown'} stage: {likely_cause}"
        
        if failure_classification and failure_classification.observed_error:
            return f"Based on observed error: {failure_classification.observed_error}"
        
        return "Recommendation generated based on available diagnostic context"
    
    def _build_safe_next_action(
        self,
        recommendation: Dict[str, Any],
        review_surface: Optional[RecoveryRecommendationReviewSurface],
    ) -> Dict[str, Any]:
        """Build safe-next-action dict from recommendation or review surface."""
        # Try review surface first
        if review_surface:
            return review_surface.get_safe_next_action()
        
        # Fallback inference from recommendation
        confidence = recommendation.get("confidence", "medium")
        stage = recommendation.get("stage", "unknown")
        
        # Determine risk level based on confidence
        if confidence in ("high", "very_high"):
            risk_level = "low"
        elif confidence in ("medium",):
            risk_level = "medium"
        else:
            risk_level = "high"
        
        # Required verification based on stage
        verification_steps = []
        if stage == "proposal":
            verification_steps.append("Verify proposal validation criteria")
        elif stage == "handshake":
            verification_steps.append("Verify node capability and trust state")
        elif stage == "envelope":
            verification_steps.append("Verify gate status and target availability")
        elif stage == "deadline":
            verification_steps.append("Verify execution duration and heartbeat status")
        else:
            verification_steps.append("Review raw event logs for failure context")
        
        # Fallback options
        fallback_options = [
            "Retry with increased timeout thresholds",
            "Switch to alternative target node",
            "Reduce scope and retry with simpler proposal",
            "Escalate to operator for manual review",
        ]
        
        # Recommended action from recovery hint
        recommended_action = recommendation.get("recovery_hint")
        if not recommended_action:
            recommended_action = "Review recovery hints and apply most appropriate action"
        
        return {
            "recommended_action": recommended_action,
            "risk_level": risk_level,
            "required_verification": verification_steps,
            "fallback_options": fallback_options,
        }
    
    def export_by_correlation(
        self,
        flow_id: Optional[str] = None,
        request_id: Optional[str] = None,
        handshake_id: Optional[str] = None,
        deadline_id: Optional[str] = None,
    ) -> List[DecisionTraceRecord]:
        """Export decision traces filtered by correlation ID.
        
        Args:
            flow_id: Filter by flow ID
            request_id: Filter by request ID
            handshake_id: Filter by handshake ID
            deadline_id: Filter by deadline ID
            
        Returns:
            List of matching decision trace records
        """
        matching: List[DecisionTraceRecord] = []
        
        for record in self._export_records.values():
            rec_ids = record.correlation_ids
            
            if flow_id and rec_ids.get("flow_id") == flow_id:
                matching.append(record)
            elif request_id and rec_ids.get("request_id") == request_id:
                matching.append(record)
            elif handshake_id and rec_ids.get("handshake_id") == handshake_id:
                matching.append(record)
            elif deadline_id and rec_ids.get("deadline_id") == deadline_id:
                matching.append(record)
            elif not any([flow_id, request_id, handshake_id, deadline_id]):
                matching.append(record)
        
        return matching
    
    def export_operator_summary(self) -> str:
        """Generate operator-readable summary of all exports.
        
        Returns:
            Multi-line string with decision trace details
        """
        lines: List[str] = []
        lines.append("=== OPERATOR DECISION TRACE SUMMARY ===")
        
        if not self._export_records:
            lines.append("No decision traces exported.")
            return "\n".join(lines)
        
        lines.append(f"Total Decision Traces: {len(self._export_records)}")
        lines.append("")
        
        for i, record in enumerate(self._export_records.values(), 1):
            lines.append(f"--- Decision Trace #{i} ---")
            lines.append(f"  Trace ID: {record.trace_id}")
            lines.append(f"  Recommendation ID: {record.recommendation_id}")
            lines.append(f"  Timestamp: {record.timestamp}")
            
            correlation_parts = []
            if record.correlation_ids.get("flow_id"):
                correlation_parts.append(f"flow_id={record.correlation_ids['flow_id']}")
            if record.correlation_ids.get("request_id"):
                correlation_parts.append(f"request_id={record.correlation_ids['request_id']}")
            if record.correlation_ids.get("handshake_id"):
                correlation_parts.append(f"handshake_id={record.correlation_ids['handshake_id']}")
            if record.correlation_ids.get("deadline_id"):
                correlation_parts.append(f"deadline_id={record.correlation_ids['deadline_id']}")
            
            if correlation_parts:
                lines.append(f"  Correlations: {', '.join(correlation_parts)}")
            
            lines.append(f"  Rationale: {record.rationale}")
            lines.append(f"  Confidence: {record.confidence_level} — {record.confidence_explanation}")
            
            sna = record.safe_next_action
            lines.append(f"  Recommended Action: {sna.get('recommended_action', 'N/A')}")
            lines.append(f"  Risk Level: {sna.get('risk_level', 'unknown')}")
            lines.append(f"  Verification Required: {', '.join(sna.get('required_verification', []))}")
            lines.append("")
        
        return "\n".join(lines)
    
    def export_machine_readable(self) -> List[Dict[str, Any]]:
        """Export all records as machine-readable JSON-compatible list.
        
        Returns:
            List of decision trace record dictionaries
        """
        return [record.to_dict() for record in self._export_records.values()]


# ============================================================================
# DECISION TRACE SUMMARY
# ============================================================================


class DecisionTraceSummary:
    """Operator-readable summary of decision traces.
    
    Aggregates multiple decision traces into a readable overview.
    """
    
    def __init__(self):
        """Initialize summary builder."""
        self._traces: List[DecisionTraceRecord] = []
    
    def add_traces(self, traces: List[DecisionTraceRecord]) -> None:
        """Add decision traces to summary.
        
        Args:
            traces: List of decision trace records
        """
        self._traces.extend(traces)
    
    def build_summary(self) -> Dict[str, Any]:
        """Build aggregated summary.
        
        Returns:
            Summary dict with:
            - total_traces: Count
            - confidence_distribution: Operator guidance breakdown
            - most_common_cause: Most frequent likely cause
            - recommended_actions: Deduplicated safe-next-actions
            - correlation_coverage: Summary of correlation ID coverage
        """
        if not self._traces:
            return {
                "total_traces": 0,
                "confidence_distribution": {},
                "most_common_cause": None,
                "recommended_actions": [],
                "correlation_coverage": {},
            }
        
        # Count confidence levels
        confidence_dist: Dict[str, int] = {}
        for trace in self._traces:
            conf = trace.confidence_level
            confidence_dist[conf] = confidence_dist.get(conf, 0) + 1
        
        # Find most common cause
        cause_counts: Dict[str, int] = {}
        for trace in self._traces:
            cause = trace.likely_cause or "Unknown"
            cause_counts[cause] = cause_counts.get(cause, 0) + 1
        
        most_common_cause = (
            max(cause_counts.keys(), key=lambda k: cause_counts[k])
            if cause_counts else None
        )
        
        # Deduplicate recommended actions
        actions = list(set(
            trace.safe_next_action.get("recommended_action", "None")
            for trace in self._traces
            if trace.safe_next_action.get("recommended_action")
        ))
        
        # Correlation coverage
        correlation_coverage: Dict[str, int] = {}
        for trace in self._traces:
            for key in ["flow_id", "request_id", "handshake_id", "deadline_id"]:
                if trace.correlation_ids.get(key):
                    correlation_coverage[key] = correlation_coverage.get(key, 0) + 1
        
        return {
            "total_traces": len(self._traces),
            "confidence_distribution": confidence_dist,
            "most_common_cause": most_common_cause,
            "recommended_actions": actions,
            "correlation_coverage": correlation_coverage,
        }
    
    def build_operator_summary(self) -> str:
        """Build operator-readable multi-line summary.
        
        Returns:
            Multi-line string for operator console
        """
        summary = self.build_summary()
        
        lines = [
            "=== OPERATOR DECISION TRACE SUMMARY ===",
            f"Total Traces: {summary['total_traces']}",
            "",
            "=== CONFIDENCE DISTRIBUTION ===",
        ]
        
        for conf, count in sorted(summary["confidence_distribution"].items()):
            lines.append(f"  {conf}: {count}")
        
        lines.append("")
        lines.append("=== MOST COMMON CAUSE ===")
        lines.append(f"  {summary['most_common_cause'] or 'Unknown'}")
        
        lines.append("")
        lines.append("=== RECOMMENDED ACTIONS ===")
        for action in summary["recommended_actions"]:
            lines.append(f"  - {action}")
        
        if summary["correlation_coverage"]:
            lines.append("")
            lines.append("=== CORRELATION COVERAGE ===")
            for key, count in sorted(summary["correlation_coverage"].items()):
                lines.append(f"  {key}: {count} traces")
        
        return "\n".join(lines)


# ============================================================================
# INTEGRATION HOOKS
# ============================================================================


def integrate_with_v77_review_surface(
    review_surface: RecoveryRecommendationReviewSurface,
    diagnostic_hooks: Optional[DiagnosticHooks] = None,
) -> DecisionTraceExporter:
    """Integrate v77 review surface with v78 decision trace exporter.
    
    This is purely additive — no migration required.
    
    v77: RecoveryRecommendationReviewSurface presents recommendations for review.
    v78: DecisionTraceExporter exports decision traces with full correlation.
    
    Args:
        review_surface: v77 review surface instance
        diagnostic_hooks: Optional v70 diagnostic hooks for failure context
        
    Returns:
        DecisionTraceExporter with v77 recommendations exported as decision traces
    """
    exporter = DecisionTraceExporter(diagnostic_hooks) if diagnostic_hooks else DecisionTraceExporter(None)
    
    # Get all recommendations from v77 review surface
    recommendations = review_surface.get_alternative_recommendations()
    
    for rec in recommendations:
        # Build failure classification from v77 data
        failure_classification = None
        if diagnostic_hooks:
            flow_id = rec.get("correlation_ids", {}).get("flow_id")
            if flow_id:
                classification = diagnostic_hooks.get_failure_classification(flow_id)
                if classification:
                    failure_classification = FailureClassification.from_dict(classification)
        
        exporter.export_decision_trace(
            recommendation=rec,
            failure_classification=failure_classification,
            review_surface=review_surface,
        )
    
    return exporter


def integrate_with_v76_exporter(
    v76_exporter: Any,
    diagnostic_hooks: Optional[DiagnosticHooks] = None,
) -> DecisionTraceExporter:
    """Integrate v76 recovery recommendation exporter with v78 decision trace.
    
    Provides decision trace layer on top of v76 export format.
    
    Args:
        v76_exporter: v76 RecoveryRecommendationExporter instance
        diagnostic_hooks: Optional v70 diagnostic hooks
        
    Returns:
        DecisionTraceExporter with v76 exports converted to decision traces
    """
    exporter = DecisionTraceExporter(diagnostic_hooks) if diagnostic_hooks else DecisionTraceExporter(None)
    
    v76_records = v76_exporter.export_machine_readable()
    
    for record_data in v76_records:
        # Extract recommendation data from v76 format
        recommendation_data = record_data.get("recommendation_data", {})
        
        # Build recommendation dict compatible with v78
        recommendation = {
            "recommendation_id": record_data.get("recommendation_id"),
            "generated_at": record_data.get("timestamp"),
            "correlation_ids": record_data.get("correlation_ids", {}),
            "recovery_hint": record_data.get("recovery_hint"),
            "confidence": record_data.get("confidence_level"),
            "likely_cause": recommendation_data.get("likely_cause"),
            "stage": recommendation_data.get("stage"),
            "failure_type": recommendation_data.get("failure_type"),
        }
        
        failure_classification = None
        if record_data.get("failure_classification"):
            failure_classification = FailureClassification.from_dict(
                record_data["failure_classification"]
            )
        
        exporter.export_decision_trace(
            recommendation=recommendation,
            failure_classification=failure_classification,
        )
    
    return exporter
