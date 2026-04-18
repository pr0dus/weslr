# operator_case_timeline_comparison.py - WESLR v91: Operator Case Timeline Comparison / Escalation Drift Layer
# Read-only operator-facing layer that compares case comparison summaries across incidents
# and time windows, highlighting where escalation patterns drift.
# No optimization, no remediation, no orchestration, no backend/service/UI.
# No TIA/C#, no storage framework expansion, no analytics engine beyond comparison scope.

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .operator_case_comparison import (
    CaseComparisonSummary,
    CaseComparisonExporter,
    CaseComparisonSummary as CaseComparisonRecord,
)


# ============================================================================
# TIMELINE COMPARISON DATA MODELS
# ============================================================================


@dataclass
class EscalationDriftRecord:
    """Single escalation drift record tracking changes across case comparisons.
    
    Contains:
    - Drift metadata (timestamp, comparison references)
    - Drift content (urgency shifts, event count changes)
    - Interpretation (operator-facing explanation)
    """
    
    drift_id: str
    timestamp: str
    comparison_id: str
    case1_id: str
    case2_id: str
    
    # Urgency context
    case1_urgency: str  # "normal", "attention", "urgent"
    case2_urgency: str  # "normal", "attention", "urgent"
    urgency_shift: str  # "increasing", "decreasing", "stable"
    
    # Event count changes
    case1_event_count: int
    case2_event_count: int
    event_delta: int
    
    # Operator guidance
    interpretation: str  # What this means for operators
    heuristic_significance: str  # "low", "medium", "high" (heuristic, not certainty)
    heuristic_reason: str  # Why this significance
    
    # Correlation IDs
    correlation_ids: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "drift_id": self.drift_id,
            "timestamp": self.timestamp,
            "comparison_id": self.comparison_id,
            "case1_id": self.case1_id,
            "case2_id": self.case2_id,
            "case1_urgency": self.case1_urgency,
            "case2_urgency": self.case2_urgency,
            "urgency_shift": self.urgency_shift,
            "case1_event_count": self.case1_event_count,
            "case2_event_count": self.case2_event_count,
            "event_delta": self.event_delta,
            "interpretation": self.interpretation,
            "heuristic_significance": self.heuristic_significance,
            "heuristic_reason": self.heuristic_reason,
            "correlation_ids": self.correlation_ids,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class ConfidenceDriftRecord:
    """Confidence-guidance drift record tracking changes across case comparisons.
    
    Contains:
    - Drift metadata (timestamp, comparison references)
    - Drift content (confidence level shifts, guidance changes)
    - Interpretation (operator-facing explanation)
    """
    
    drift_id: str
    timestamp: str
    comparison_id: str
    case1_id: str
    case2_id: str
    
    # Confidence context
    case1_confidence: str  # "low", "medium", "high"
    case2_confidence: str  # "low", "medium", "high"
    confidence_shift: str  # "increasing", "decreasing", "stable"
    
    # Guidance changes
    guidance_context: str
    guidance_change: str  # "added", "removed", "updated", "unchanged"
    
    # Operator guidance
    interpretation: str  # What this means for operators
    heuristic_significance: str  # "low", "medium", "high" (heuristic, not certainty)
    heuristic_reason: str  # Why this significance
    
    # Correlation IDs
    correlation_ids: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "drift_id": self.drift_id,
            "timestamp": self.timestamp,
            "comparison_id": self.comparison_id,
            "case1_id": self.case1_id,
            "case2_id": self.case2_id,
            "case1_confidence": self.case1_confidence,
            "case2_confidence": self.case2_confidence,
            "confidence_shift": self.confidence_shift,
            "guidance_context": self.guidance_context,
            "guidance_change": self.guidance_change,
            "interpretation": self.interpretation,
            "heuristic_significance": self.heuristic_significance,
            "heuristic_reason": self.heuristic_reason,
            "correlation_ids": self.correlation_ids,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class SafeActionDriftRecord:
    """Safe-next-action drift record tracking changes across case comparisons.
    
    Contains:
    - Drift metadata (timestamp, comparison references)
    - Drift content (action shifts, evidence changes)
    - Interpretation (operator-facing explanation)
    """
    
    drift_id: str
    timestamp: str
    comparison_id: str
    case1_id: str
    case2_id: str
    
    # Action context
    case1_action: Optional[str]
    case2_action: Optional[str]
    action_shift: str  # "increasing", "decreasing", "stable", "new", "removed"
    
    # Evidence changes
    evidence_context: str
    evidence_change: str  # "added", "removed", "updated", "unchanged"
    
    # Operator guidance
    interpretation: str  # What this means for operators
    heuristic_significance: str  # "low", "medium", "high" (heuristic, not certainty)
    heuristic_reason: str  # Why this significance
    
    # Correlation IDs
    correlation_ids: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "drift_id": self.drift_id,
            "timestamp": self.timestamp,
            "comparison_id": self.comparison_id,
            "case1_id": self.case1_id,
            "case2_id": self.case2_id,
            "case1_action": self.case1_action,
            "case2_action": self.case2_action,
            "action_shift": self.action_shift,
            "evidence_context": self.evidence_context,
            "evidence_change": self.evidence_change,
            "interpretation": self.interpretation,
            "heuristic_significance": self.heuristic_significance,
            "heuristic_reason": self.heuristic_reason,
            "correlation_ids": self.correlation_ids,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class DriftTrend:
    """Drift trend over time or across incidents.
    
    Contains:
    - Trend metadata (type, direction, magnitude)
    - Interpretation (operator-facing explanation)
    - Heuristic significance (not certainty)
    """
    
    trend_id: str
    timestamp: str
    trend_type: str  # "escalation", "confidence", "safe_action_convergence"
    direction: str  # "increasing", "decreasing", "stable", "variable"
    magnitude: str  # "minor", "moderate", "significant"
    
    # Interpretation
    interpretation: str  # What this means for operators
    heuristic_significance: str  # "low", "medium", "high" (heuristic, not certainty)
    heuristic_reason: str  # Why this significance
    
    # Pattern reference
    reference_comparison_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "trend_id": self.trend_id,
            "timestamp": self.timestamp,
            "trend_type": self.trend_type,
            "direction": self.direction,
            "magnitude": self.magnitude,
            "interpretation": self.interpretation,
            "heuristic_significance": self.heuristic_significance,
            "heuristic_reason": self.heuristic_reason,
            "reference_comparison_id": self.reference_comparison_id,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class TimelineComparisonResult:
    """Operator-readable + machine-readable timeline comparison result.
    
    Contains:
    - Summary metadata (ID, timestamp, case references)
    - Drift records (all drift types)
    - Drift distribution summary
    - Drift trends
    - Operator narrative
    - Machine export JSON
    
    Key constraints:
    - All drifts are presented as operator guidance, not certainty
    - No automatic decision logic - comparison only
    - No remediation logic - read-only comparison
    """
    
    summary_id: str
    timestamp: str
    case1_id: str
    case2_id: str
    
    # Drift sections
    escalation_drifts: List[EscalationDriftRecord]
    confidence_drifts: List[ConfidenceDriftRecord]
    safe_action_drifts: List[SafeActionDriftRecord]
    
    # Drift distribution
    drift_distribution: Dict[str, int]
    meaningful_drifts: int
    
    # Drift trends
    drift_trends: List[Dict[str, Any]]
    
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
            "case1_id": self.case1_id,
            "case2_id": self.case2_id,
            "escalation_drifts": [d.to_dict() for d in self.escalation_drifts],
            "confidence_drifts": [d.to_dict() for d in self.confidence_drifts],
            "safe_action_drifts": [d.to_dict() for d in self.safe_action_drifts],
            "drift_distribution": self.drift_distribution,
            "meaningful_drifts": self.meaningful_drifts,
            "drift_trends": self.drift_trends,
            "correlation_ids": self.correlation_ids,
            "operator_readable": self.operator_readable,
            "machine_readable": self.machine_readable,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# TIMELINE COMPARISON EXPORTER
# ============================================================================


class TimelineComparisonExporter:
    """Exporter for timeline comparison results.
    
    Provides:
    - Operator-readable summary export
    - Machine-readable JSON export
    - Correlation ID support (flow_id, request_id, handshake_id, deadline_id)
    - Passive telemetry hooks (no new event framework)
    
    Read-only export only — no behavior changes.
    """
    
    @staticmethod
    def export_summary(
        result: TimelineComparisonResult,
        format: str = "operator",
    ) -> str:
        """Export result to requested format.
        
        Args:
            result: TimelineComparisonResult to export
            format: Output format ("operator" or "json")
        
        Returns:
            Exported content string
        """
        if format == "json":
            return result.machine_readable
        return result.operator_readable
    
    @staticmethod
    def export_multiple(
        results: List[TimelineComparisonResult],
        format: str = "json",
    ) -> str:
        """Export multiple results.
        
        Args:
            results: List of TimelineComparisonResult
            format: Output format ("json" only for multiple)
        
        Returns:
            JSON array string
        """
        if format == "json":
            return json.dumps([r.to_dict() for r in results], indent=2)
        raise ValueError("Multiple export only supports JSON format")
    
    @staticmethod
    def telemetry_event_result_created(result: TimelineComparisonResult) -> Dict[str, Any]:
        """Telemetry event for result creation (passive, descriptive only).
        
        Args:
            result: TimelineComparisonResult that was created
        
        Returns:
            Dict with event data (not used for behavior)
        """
        return {
            "event_type": "TIMELINE_COMPARISON_RESULT_CREATED",
            "summary_id": result.summary_id,
            "timestamp": result.timestamp,
            "case1_id": result.case1_id,
            "case2_id": result.case2_id,
            "content_summary": {
                "escalation_drift_count": len(result.escalation_drifts),
                "confidence_drift_count": len(result.confidence_drifts),
                "safe_action_drift_count": len(result.safe_action_drifts),
                "meaningful_drifts": result.meaningful_drifts,
                "drift_trend_count": len(result.drift_trends),
            },
        }
    
    @staticmethod
    def telemetry_event_exported(result: TimelineComparisonResult) -> Dict[str, Any]:
        """Telemetry event for result export (passive, descriptive only).
        
        Args:
            result: TimelineComparisonResult that was exported
        
        Returns:
            Dict with event data (not used for behavior)
        """
        return {
            "event_type": "TIMELINE_COMPARISON_RESULT_EXPORTED",
            "summary_id": result.summary_id,
            "timestamp": result.timestamp,
            "export_format": "json" if "summary_id" in result.machine_readable else "operator",
        }


# ============================================================================
# OPERATOR CASE TIMELINE COMPARISON LAYER
# ============================================================================


class OperatorCaseTimelineComparison:
    """Timeline comparison layer for operator case comparison summaries.
    
    Provides read-only comparison across time:
    - Compare case-comparison summaries from v90 across incidents
    - Detect escalation drift across time windows
    - Compare confidence-guidance drift at case-comparison level
    - Compare safe-next-action drift at case-comparison level
    - Generate timeline comparison results with drift detection
    - Export operator-readable and machine-readable summaries
    
    Correlation support:
    - flow_id
    - request_id
    - handshake_id
    - deadline_id
    
    Read-only comparison only — no behavior changes, no automatic decisions.
    """
    
    def __init__(self):
        """Initialize operator case timeline comparison layer."""
        self._results: List[TimelineComparisonResult] = []
        self._sequence_counter: int = 0
    
    def compare_timeline(
        self,
        comparison1: CaseComparisonRecord,
        comparison2: CaseComparisonRecord,
        correlation_ids: Optional[Dict[str, str]] = None,
    ) -> TimelineComparisonResult:
        """Compare two case comparison summaries across time.
        
        Args:
            comparison1: First CaseComparisonSummary (earlier time window)
            comparison2: Second CaseComparisonSummary (later time window)
            correlation_ids: Optional correlation IDs
        
        Returns:
            TimelineComparisonResult for the comparison
        
        Note:
            - Comparison only, no new recommendation engine
            - No autonomous decision logic
            - No hidden remediation logic
        """
        self._sequence_counter += 1
        summary_id = f"timeline_comparison_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Extract escalation drifts
        escalation_drifts = self._extract_escalation_drifts(
            comparison1, comparison2, correlation_ids or {}
        )
        
        # Extract confidence drifts
        confidence_drifts = self._extract_confidence_drifts(
            comparison1, comparison2, correlation_ids or {}
        )
        
        # Extract safe-action drifts
        safe_action_drifts = self._extract_safe_action_drifts(
            comparison1, comparison2, correlation_ids or {}
        )
        
        # Calculate drift distribution
        drift_distribution = self._calculate_drift_distribution(
            escalation_drifts, confidence_drifts, safe_action_drifts
        )
        
        # Count meaningful drifts
        meaningful_drifts = self._count_meaningful_drifts(
            escalation_drifts, confidence_drifts, safe_action_drifts
        )
        
        # Generate drift trends
        drift_trends = self._generate_drift_trends(
            escalation_drifts, confidence_drifts, safe_action_drifts, summary_id
        )
        
        # Generate operator-readable summary
        operator_summary = self._generate_operator_summary(
            summary_id, comparison1.case1_id, comparison1.case2_id,
            escalation_drifts, confidence_drifts, safe_action_drifts,
            drift_distribution, drift_trends
        )
        
        # Generate machine-readable summary
        machine_summary = self._generate_machine_summary(
            summary_id, timestamp, comparison1.case1_id, comparison1.case2_id,
            escalation_drifts, confidence_drifts, safe_action_drifts,
            drift_distribution, meaningful_drifts, drift_trends, correlation_ids or {}
        )
        
        result = TimelineComparisonResult(
            summary_id=summary_id,
            timestamp=timestamp,
            case1_id=comparison1.case1_id,
            case2_id=comparison1.case2_id,
            escalation_drifts=escalation_drifts,
            confidence_drifts=confidence_drifts,
            safe_action_drifts=safe_action_drifts,
            drift_distribution=drift_distribution,
            meaningful_drifts=meaningful_drifts,
            drift_trends=drift_trends,
            correlation_ids=correlation_ids or {},
            operator_readable=operator_summary,
            machine_readable=machine_summary,
        )
        
        self._results.append(result)
        return result
    
    def _extract_escalation_drifts(
        self,
        comparison1: CaseComparisonRecord,
        comparison2: CaseComparisonRecord,
        correlation_ids: Dict[str, str],
    ) -> List[EscalationDriftRecord]:
        """Extract escalation drift records between two case comparisons.
        
        Args:
            comparison1: First CaseComparisonSummary (earlier)
            comparison2: Second CaseComparisonSummary (later)
            correlation_ids: Correlation IDs
        
        Returns:
            List of EscalationDriftRecord
        """
        drifts = []
        
        # Extract escalation differences from both comparisons
        case1_escalation = comparison1.escalation_differences if hasattr(comparison1, 'escalation_differences') else []
        case2_escalation = comparison2.escalation_differences if hasattr(comparison2, 'escalation_differences') else []
        
        # Compare escalation patterns
        if case1_escalation and case2_escalation:
            # Get the first escalation difference from each (simplified comparison)
            diff1 = case1_escalation[0] if isinstance(case1_escalation[0], dict) else case1_escalation[0].to_dict() if hasattr(case1_escalation[0], 'to_dict') else {}
            diff2 = case2_escalation[0] if isinstance(case2_escalation[0], dict) else case2_escalation[0].to_dict() if hasattr(case2_escalation[0], 'to_dict') else {}
            
            case1_urgency = diff1.get("case1_urgency", "normal")
            case2_urgency = diff2.get("case2_urgency", "normal")
            
            # Determine urgency shift
            urgency_shift = "stable"
            if case1_urgency == "normal" and case2_urgency in ["attention", "urgent"]:
                urgency_shift = "increasing"
            elif case1_urgency in ["attention", "urgent"] and case2_urgency == "normal":
                urgency_shift = "decreasing"
            elif case1_urgency == "attention" and case2_urgency == "urgent":
                urgency_shift = "increasing"
            elif case1_urgency == "urgent" and case2_urgency == "attention":
                urgency_shift = "decreasing"
            
            case1_event_count = diff1.get("case1_event_count", 0)
            case2_event_count = diff2.get("case2_event_count", 0)
            event_delta = case2_event_count - case1_event_count
            
            # Determine significance
            significance = "low"
            if case1_urgency == "normal" and case2_urgency == "urgent":
                significance = "significant"
            elif case1_urgency == "urgent" and case2_urgency == "normal":
                significance = "significant"
            elif abs(event_delta) > 2:
                significance = "moderate"
            
            interpretation = f"Escalation urgency {'increased' if urgency_shift == 'increasing' else 'decreased' if urgency_shift == 'decreasing' else 'stable'} from {case1_urgency} to {case2_urgency}."
            if abs(event_delta) > 0:
                interpretation += f" Event count changed by {event_delta}."
            
            drifts.append(EscalationDriftRecord(
                drift_id=f"escalation_drift_{uuid.uuid4().hex[:8]}",
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                comparison_id=comparison1.summary_id if hasattr(comparison1, 'summary_id') else comparison1.to_dict().get("summary_id", "unknown"),
                case1_id=comparison1.case1_id if hasattr(comparison1, 'case1_id') else "unknown",
                case2_id=comparison1.case2_id if hasattr(comparison1, 'case2_id') else "unknown",
                case1_urgency=case1_urgency,
                case2_urgency=case2_urgency,
                urgency_shift=urgency_shift,
                case1_event_count=case1_event_count,
                case2_event_count=case2_event_count,
                event_delta=event_delta,
                interpretation=interpretation,
                heuristic_significance=significance,
                heuristic_reason=f"Urgency shift {urgency_shift} with {significance} significance",
                correlation_ids=correlation_ids,
            ))
        
        return drifts
        
    def _extract_confidence_drifts(
        self,
        comparison1: CaseComparisonRecord,
        comparison2: CaseComparisonRecord,
        correlation_ids: Dict[str, str],
    ) -> List[ConfidenceDriftRecord]:
        """Extract confidence-guidance drift records between two case comparisons.
        
        Args:
            comparison1: First CaseComparisonSummary (earlier)
            comparison2: Second CaseComparisonSummary (later)
            correlation_ids: Correlation IDs
        
        Returns:
            List of ConfidenceDriftRecord
        """
        drifts = []
        
        # Extract confidence differences from both comparisons
        case1_confidence = comparison1.confidence_differences if hasattr(comparison1, 'confidence_differences') else []
        case2_confidence = comparison2.confidence_differences if hasattr(comparison2, 'confidence_differences') else []
        
        # Compare confidence patterns
        if case1_confidence and case2_confidence:
            diff1 = case1_confidence[0] if isinstance(case1_confidence[0], dict) else case1_confidence[0].to_dict() if hasattr(case1_confidence[0], 'to_dict') else {}
            diff2 = case2_confidence[0] if isinstance(case2_confidence[0], dict) else case2_confidence[0].to_dict() if hasattr(case2_confidence[0], 'to_dict') else {}
            
            case1_conf = diff1.get("case1_confidence", "medium")
            case2_conf = diff2.get("case2_confidence", "medium")
            
            # Determine confidence shift
            confidence_shift = "stable"
            if case1_conf == "low" and case2_conf in ["medium", "high"]:
                confidence_shift = "increasing"
            elif case1_conf in ["low", "medium"] and case2_conf == "high":
                confidence_shift = "increasing"
            elif case1_conf in ["medium", "high"] and case2_conf == "low":
                confidence_shift = "decreasing"
            elif case1_conf == "high" and case2_conf in ["medium", "low"]:
                confidence_shift = "decreasing"
            
            # Check guidance changes
            case1_has_guidance = diff1.get("case1_action", None) is not None or diff1.get("guidance_change", "unchanged") != "unchanged"
            case2_has_guidance = diff2.get("case2_action", None) is not None or diff2.get("guidance_change", "unchanged") != "unchanged"
            
            guidance_change = "unchanged"
            if case1_has_guidance and case2_has_guidance:
                guidance_change = "unchanged"
            elif case1_has_guidance and not case2_has_guidance:
                guidance_change = "removed"
            elif not case1_has_guidance and case2_has_guidance:
                guidance_change = "added"
            elif case1_has_guidance and case2_has_guidance:
                guidance_change = "updated"
            
            guidance_context = "recovery guidance"
            
            interpretation = f"Confidence guidance {'increased' if confidence_shift == 'increasing' else 'decreased' if confidence_shift == 'decreasing' else 'stable'} from {case1_conf} to {case2_conf}."
            
            significance = "low"
            if case1_conf == "low" and case2_conf == "high":
                significance = "significant"
            elif case1_conf == "high" and case2_conf == "low":
                significance = "significant"
            
            drifts.append(ConfidenceDriftRecord(
                drift_id=f"confidence_drift_{uuid.uuid4().hex[:8]}",
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                comparison_id=comparison1.summary_id if hasattr(comparison1, 'summary_id') else comparison1.to_dict().get("summary_id", "unknown"),
                case1_id=comparison1.case1_id if hasattr(comparison1, 'case1_id') else "unknown",
                case2_id=comparison1.case2_id if hasattr(comparison1, 'case2_id') else "unknown",
                case1_confidence=case1_conf,
                case2_confidence=case2_conf,
                confidence_shift=confidence_shift,
                guidance_context=guidance_context,
                guidance_change=guidance_change,
                interpretation=interpretation,
                heuristic_significance=significance,
                heuristic_reason=f"Confidence shift {confidence_shift} with {significance} significance",
                correlation_ids=correlation_ids,
            ))
        
        return drifts
    
    def _extract_safe_action_drifts(
        self,
        comparison1: CaseComparisonRecord,
        comparison2: CaseComparisonRecord,
        correlation_ids: Dict[str, str],
    ) -> List[SafeActionDriftRecord]:
        """Extract safe-next-action drift records between two case comparisons.
        
        Args:
            comparison1: First CaseComparisonSummary (earlier)
            comparison2: Second CaseComparisonSummary (later)
            correlation_ids: Correlation IDs
        
        Returns:
            List of SafeActionDriftRecord
        """
        drifts = []
        
        # Extract safe action differences from both comparisons
        case1_actions = comparison1.safe_action_differences if hasattr(comparison1, 'safe_action_differences') else []
        case2_actions = comparison2.safe_action_differences if hasattr(comparison2, 'safe_action_differences') else []
        
        # Compare safe-action patterns
        if case1_actions and case2_actions:
            diff1 = case1_actions[0] if isinstance(case1_actions[0], dict) else case1_actions[0].to_dict() if hasattr(case1_actions[0], 'to_dict') else {}
            diff2 = case2_actions[0] if isinstance(case2_actions[0], dict) else case2_actions[0].to_dict() if hasattr(case2_actions[0], 'to_dict') else {}
            
            case1_action = diff1.get("case1_action")
            case2_action = diff2.get("case2_action")
            
            # Determine action shift
            action_shift = "unchanged"
            if case1_action and not case2_action:
                action_shift = "removed"
            elif not case1_action and case2_action:
                action_shift = "added"
            elif case1_action != case2_action:
                action_shift = "updated"
            
            # Check evidence changes
            case1_evidence = diff1.get("case1_event_count", 0) if "case1_event_count" in diff1 else 0
            case2_evidence = diff2.get("case2_event_count", 0) if "case2_event_count" in diff2 else 0
            
            evidence_change = "unchanged"
            if case1_evidence < case2_evidence:
                evidence_change = "added"
            elif case1_evidence > case2_evidence:
                evidence_change = "removed"
            
            evidence_context = "evidence references"
            
            interpretation = f"Safe-next-action {'changed' if action_shift in ['added', 'removed', 'updated'] else 'unchanged'}. Evidence count {'increased' if case2_evidence > case1_evidence else 'decreased' if case2_evidence < case1_evidence else 'stable'}."
            
            significance = "low"
            if action_shift in ["added", "removed"]:
                significance = "moderate"
            
            drifts.append(SafeActionDriftRecord(
                drift_id=f"safe_action_drift_{uuid.uuid4().hex[:8]}",
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                comparison_id=comparison1.summary_id if hasattr(comparison1, 'summary_id') else comparison1.to_dict().get("summary_id", "unknown"),
                case1_id=comparison1.case1_id if hasattr(comparison1, 'case1_id') else "unknown",
                case2_id=comparison1.case2_id if hasattr(comparison1, 'case2_id') else "unknown",
                case1_action=case1_action,
                case2_action=case2_action,
                action_shift=action_shift,
                evidence_context=evidence_context,
                evidence_change=evidence_change,
                interpretation=interpretation,
                heuristic_significance=significance,
                heuristic_reason=f"Action shift {action_shift} with {significance} significance",
                correlation_ids=correlation_ids,
            ))
        
        return drifts
    
    def _calculate_drift_distribution(
        self,
        escalation_drifts: List[EscalationDriftRecord],
        confidence_drifts: List[ConfidenceDriftRecord],
        safe_action_drifts: List[SafeActionDriftRecord],
    ) -> Dict[str, int]:
        """Calculate drift distribution across types.
        
        Args:
            escalation_drifts: Escalation drift records
            confidence_drifts: Confidence drift records
            safe_action_drifts: Safe action drift records
        
        Returns:
            Dict with drift counts by type
        """
        return {
            "escalation": len(escalation_drifts),
            "confidence": len(confidence_drifts),
            "safe_action": len(safe_action_drifts),
            "total": len(escalation_drifts) + len(confidence_drifts) + len(safe_action_drifts),
        }
    
    def _count_meaningful_drifts(
        self,
        escalation_drifts: List[EscalationDriftRecord],
        confidence_drifts: List[ConfidenceDriftRecord],
        safe_action_drifts: List[SafeActionDriftRecord],
    ) -> int:
        """Count meaningful drifts (non-stable shifts).
        
        Args:
            escalation_drifts: Escalation drift records
            confidence_drifts: Confidence drift records
            safe_action_drifts: Safe action drift records
        
        Returns:
            Count of meaningful drifts
        """
        meaningful = 0
        
        # Count non-stable escalation drifts
        for drift in escalation_drifts:
            if drift.urgency_shift != "stable":
                meaningful += 1
        
        # Count non-stable confidence drifts
        for drift in confidence_drifts:
            if drift.confidence_shift != "stable":
                meaningful += 1
        
        # Count non-stable safe-action drifts
        for drift in safe_action_drifts:
            if drift.action_shift not in ["unchanged", "stable"]:
                meaningful += 1
        
        return meaningful
    
    def _generate_drift_trends(
        self,
        escalation_drifts: List[EscalationDriftRecord],
        confidence_drifts: List[ConfidenceDriftRecord],
        safe_action_drifts: List[SafeActionDriftRecord],
        summary_id: str,
    ) -> List[Dict[str, Any]]:
        """Generate drift trends from drift records.
        
        Args:
            escalation_drifts: Escalation drift records
            confidence_drifts: Confidence drift records
            safe_action_drifts: Safe action drift records
            summary_id: Timeline comparison summary ID
        
        Returns:
            List of drift trend dicts
        """
        trends = []
        
        # Generate escalation trend
        if escalation_drifts:
            increasing = sum(1 for d in escalation_drifts if d.urgency_shift == "increasing")
            decreasing = sum(1 for d in escalation_drifts if d.urgency_shift == "decreasing")
            stable = sum(1 for d in escalation_drifts if d.urgency_shift == "stable")
            
            if increasing > decreasing:
                direction = "increasing"
                magnitude = "moderate" if increasing <= 2 else "significant"
            elif decreasing > increasing:
                direction = "decreasing"
                magnitude = "moderate" if decreasing <= 2 else "significant"
            else:
                direction = "stable"
                magnitude = "minor"
            
            trends.append({
                "trend_id": f"escalation_trend_{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "trend_type": "escalation",
                "direction": direction,
                "magnitude": magnitude,
                "interpretation": f"Escalation patterns showing {'increasing' if direction == 'increasing' else 'decreasing' if direction == 'decreasing' else 'stable'} escalation severity.",
                "heuristic_significance": "low" if magnitude == "minor" else "medium",
                "heuristic_reason": f"Direction {direction} with magnitude {magnitude}",
                "reference_comparison_id": summary_id,
            })
        
        # Generate confidence trend
        if confidence_drifts:
            increasing = sum(1 for d in confidence_drifts if d.confidence_shift == "increasing")
            decreasing = sum(1 for d in confidence_drifts if d.confidence_shift == "decreasing")
            stable = sum(1 for d in confidence_drifts if d.confidence_shift == "stable")
            
            if increasing > decreasing:
                direction = "increasing"
                magnitude = "moderate" if increasing <= 2 else "significant"
            elif decreasing > increasing:
                direction = "decreasing"
                magnitude = "moderate" if decreasing <= 2 else "significant"
            else:
                direction = "stable"
                magnitude = "minor"
            
            trends.append({
                "trend_id": f"confidence_trend_{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "trend_type": "confidence",
                "direction": direction,
                "magnitude": magnitude,
                "interpretation": f"Confidence guidance showing {'increasing' if direction == 'increasing' else 'decreasing' if direction == 'decreasing' else 'stable'} confidence over time.",
                "heuristic_significance": "low" if magnitude == "minor" else "medium",
                "heuristic_reason": f"Direction {direction} with magnitude {magnitude}",
                "reference_comparison_id": summary_id,
            })
        
        # Generate safe-action trend
        if safe_action_drifts:
            changing = sum(1 for d in safe_action_drifts if d.action_shift in ["added", "removed", "updated"])
            stable = sum(1 for d in safe_action_drifts if d.action_shift in ["unchanged", "stable"])
            
            if changing > stable:
                direction = "variable"
                magnitude = "moderate" if changing <= 2 else "significant"
            else:
                direction = "stable"
                magnitude = "minor"
            
            trends.append({
                "trend_id": f"safe_action_trend_{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "trend_type": "safe_action_convergence",
                "direction": direction,
                "magnitude": magnitude,
                "interpretation": f"Safe-next-action patterns showing {'variable changes' if direction == 'variable' else 'stable'} safe-next-action selection.",
                "heuristic_significance": "low" if magnitude == "minor" else "medium",
                "heuristic_reason": f"Direction {direction} with magnitude {magnitude}",
                "reference_comparison_id": summary_id,
            })
        
        return trends
    
    def _generate_operator_summary(
        self,
        summary_id: str,
        case1_id: str,
        case2_id: str,
        escalation_drifts: List[EscalationDriftRecord],
        confidence_drifts: List[ConfidenceDriftRecord],
        safe_action_drifts: List[SafeActionDriftRecord],
        drift_distribution: Dict[str, int],
        drift_trends: List[Dict[str, Any]],
    ) -> str:
        """Generate operator-readable summary.
        
        Args:
            summary_id: Summary ID
            case1_id: First case ID
            case2_id: Second case ID
            escalation_drifts: Escalation drift records
            confidence_drifts: Confidence drift records
            safe_action_drifts: Safe action drift records
            drift_distribution: Drift distribution dict
            drift_trends: Drift trends list
        
        Returns:
            Operator-readable multi-line string
        """
        lines = [
            "=" * 70,
            "OPERATOR CASE TIMELINE COMPARISON SUMMARY",
            "=" * 70,
            f"Summary ID: {summary_id}",
            f"Case 1 ID: {case1_id}",
            f"Case 2 ID: {case2_id}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
            "",
            "-" * 70,
            "DRIFT DISTRIBUTION",
            "-" * 70,
            f"  Escalation drifts: {drift_distribution.get('escalation', 0)}",
            f"  Confidence drifts: {drift_distribution.get('confidence', 0)}",
            f"  Safe-action drifts: {drift_distribution.get('safe_action', 0)}",
            f"  Total drifts: {drift_distribution.get('total', 0)}",
            "",
            "-" * 70,
            "ESCALATION DRIFT DETAILS",
            "-" * 70,
        ]
        
        if escalation_drifts:
            for d in escalation_drifts:
                lines.append(f"  [{d.urgency_shift.upper()}] {d.case1_urgency} → {d.case2_urgency}")
                lines.append(f"      Events: {d.case1_event_count} → {d.case2_event_count} (Δ{d.event_delta})")
                lines.append(f"      Interpretation: {d.interpretation[:80]}...")
                lines.append(f"      Significance: {d.heuristic_significance}")
        else:
            lines.append("  No escalation drift detected")
        
        lines.extend([
            "",
            "-" * 70,
            "CONFIDENCE DRIFT DETAILS",
            "-" * 70,
        ])
        
        if confidence_drifts:
            for d in confidence_drifts:
                lines.append(f"  [{d.confidence_shift.upper()}] {d.case1_confidence} → {d.case2_confidence}")
                lines.append(f"      Guidance: {d.guidance_change}")
                lines.append(f"      Interpretation: {d.interpretation[:80]}...")
                lines.append(f"      Significance: {d.heuristic_significance}")
        else:
            lines.append("  No confidence drift detected")
        
        lines.extend([
            "",
            "-" * 70,
            "SAFE-NEXT-ACTION DRIFT DETAILS",
            "-" * 70,
        ])
        
        if safe_action_drifts:
            for d in safe_action_drifts:
                action1 = d.case1_action or "(none)"
                action2 = d.case2_action or "(none)"
                lines.append(f"  [{d.action_shift.upper()}] {action1} → {action2}")
                lines.append(f"      Evidence: {d.evidence_change}")
                lines.append(f"      Interpretation: {d.interpretation[:80]}...")
                lines.append(f"      Significance: {d.heuristic_significance}")
        else:
            lines.append("  No safe-action drift detected")
        
        lines.extend([
            "",
            "-" * 70,
            "DRIFT TRENDS",
            "-" * 70,
        ])
        
        for trend in drift_trends:
            lines.append(f"  [{trend['trend_type'].upper()}] {trend['direction'].upper()}")
            lines.append(f"      Magnitude: {trend['magnitude']}")
            lines.append(f"      Interpretation: {trend['interpretation'][:80]}...")
        
        lines.extend([
            "",
            "-" * 70,
            "HEURISTIC NOTE",
            "-" * 70,
            "Drifts are presented as operator guidance, not certainties.",
            "Use these summaries to inform decisions, not replace them.",
            "",
            "Key distinctions:",
            "- Guidance levels: Heuristic assessments, not automatic actions",
            "- Confidence: Operator guidance, not certainty",
            "- Significance: Interpretation context, not prediction",
            "- Escalation: Attention indicators, not automatic triggers",
            "- Drift: Pattern comparison, not future prediction",
            "",
            "This timeline comparison layer provides read-only comparison",
            "across time windows, not automatic decision-making or remediation.",
            "",
            "=" * 70,
        ])
        
        return "\n".join(lines)
    
    def _generate_machine_summary(
        self,
        summary_id: str,
        timestamp: str,
        case1_id: str,
        case2_id: str,
        escalation_drifts: List[EscalationDriftRecord],
        confidence_drifts: List[ConfidenceDriftRecord],
        safe_action_drifts: List[SafeActionDriftRecord],
        drift_distribution: Dict[str, int],
        meaningful_drifts: int,
        drift_trends: List[Dict[str, Any]],
        correlation_ids: Dict[str, str],
    ) -> str:
        """Generate machine-readable summary (JSON).
        
        Args:
            summary_id: Summary ID
            timestamp: Timestamp
            case1_id: First case ID
            case2_id: Second case ID
            escalation_drifts: Escalation drift records
            confidence_drifts: Confidence drift records
            safe_action_drifts: Safe action drift records
            drift_distribution: Drift distribution dict
            meaningful_drifts: Count of meaningful drifts
            drift_trends: Drift trends list
            correlation_ids: Correlation IDs
        
        Returns:
            JSON string
        """
        data = {
            "summary_id": summary_id,
            "timestamp": timestamp,
            "case1_id": case1_id,
            "case2_id": case2_id,
            "escalation_drifts": [d.to_dict() for d in escalation_drifts],
            "confidence_drifts": [d.to_dict() for d in confidence_drifts],
            "safe_action_drifts": [d.to_dict() for d in safe_action_drifts],
            "drift_distribution": drift_distribution,
            "meaningful_drifts": meaningful_drifts,
            "drift_trends": drift_trends,
            "correlation_ids": correlation_ids,
        }
        return json.dumps(data, indent=2)
    
    def get_result(
        self,
        summary_id: str,
    ) -> Optional[TimelineComparisonResult]:
        """Get a specific timeline comparison result.
        
        Args:
            summary_id: Summary ID to retrieve
        
        Returns:
            TimelineComparisonResult if found, None otherwise
        """
        for result in self._results:
            if result.summary_id == summary_id:
                return result
        return None
    
    def get_results(self) -> List[TimelineComparisonResult]:
        """Get all timeline comparison results.
        
        Returns:
            List of TimelineComparisonResult
        """
        return self._results
    
    def get_results_for_case(
        self,
        case_id: str,
    ) -> List[TimelineComparisonResult]:
        """Get results for a specific case.
        
        Args:
            case_id: Case ID to filter by (case1 or case2)
        
        Returns:
            List of TimelineComparisonResult for case
        """
        return [r for r in self._results if r.case1_id == case_id or r.case2_id == case_id]
    
    def export_operator_readable(self) -> str:
        """Export all results as operator-readable string.
        
        Returns:
            Multi-line operator-readable summary
        """
        lines = [
            "=" * 70,
            "ALL CASE TIMELINE COMPARISON RESULTS",
            "=" * 70,
            f"Total Results: {len(self._results)}",
            "",
        ]
        
        for result in self._results[-5:]:  # Last 5 results
            lines.append(f"Summary ID: {result.summary_id}")
            lines.append(f"Case 1 ID: {result.case1_id}")
            lines.append(f"Case 2 ID: {result.case2_id}")
            lines.append(f"Meaningful Drifts: {result.meaningful_drifts}")
            lines.append("")
        
        if not self._results:
            lines.append("No timeline comparison results available.")
        
        lines.append("=" * 70)
        return "\n".join(lines)
    
    def export_machine_readable(self) -> str:
        """Export all results as JSON string.
        
        Returns:
            JSON string of all results
        """
        return json.dumps([r.to_dict() for r in self._results], indent=2)


# ============================================================================
# INTEGRATION HELPERS (Additive Only)
# ============================================================================


def integrate_with_v90_comparison(timeline_comparison: OperatorCaseTimelineComparison) -> Dict[str, Any]:
    """Integration hook for v90 comparison — read-only comparison only.
    
    No behavior changes to existing comparison logic.
    """
    return {"hooked": True, "measures": "comparison_timeline_integration"}
