# operator_case_comparison.py - WESLR v90: Operator Case Comparison / Escalation Summary Layer
# Read-only operator-facing layer that compares consolidated case summaries across incidents
# and highlights escalation-summary differences.
# No optimization, no remediation, no orchestration, no backend/service/UI.
# No TIA/C#, no storage framework expansion, no analytics engine beyond comparison scope.

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .operator_insight_consolidation import (
    ConsolidatedCaseSummary,
    ConsolidatedCaseExporter,
    RecoveryGuidanceSummary,
    DecisionTraceSummary,
    PatternHistorySummary,
    DriftSummary,
    EscalationSummary,
)


# ============================================================================
# CASE COMPARISON DATA MODELS
# ============================================================================


@dataclass
class ComparisonResult:
    """Single comparison result between two case summaries.
    
    Contains:
    - Comparison metadata (timestamp, case references)
    - Comparison content (shared fields, differences)
    - Interpretation (operator-facing explanation)
    """
    
    comparison_id: str
    timestamp: str
    case1_id: str
    case2_id: str
    
    # Comparison content
    shared_fields: Dict[str, Any]
    differences: Dict[str, Any]
    
    # Comparison type
    comparison_type: str  # "escalation_context", "confidence_guidance", "safe_action"
    
    # Comparison assessment
    comparison_magnitude: str  # "minor", "moderate", "significant"
    meaningful_comparison: bool
    meaningful_comparison_reason: str
    
    # Correlation IDs
    correlation_ids: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "comparison_id": self.comparison_id,
            "timestamp": self.timestamp,
            "case1_id": self.case1_id,
            "case2_id": self.case2_id,
            "comparison_type": self.comparison_type,
            "comparison_magnitude": self.comparison_magnitude,
            "meaningful_comparison": self.meaningful_comparison,
            "meaningful_comparison_reason": self.meaningful_comparison_reason,
            "shared_fields": self.shared_fields,
            "differences": self.differences,
            "correlation_ids": self.correlation_ids,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class EscalationDifference:
    """Escalation context difference between two cases.
    
    Contains:
    - Difference metadata (case references, timestamps)
    - Difference content (urgency shifts, event count changes)
    - Interpretation (operator-facing explanation)
    """
    
    difference_id: str
    case1_id: str
    case2_id: str
    timestamp: str
    
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
            "difference_id": self.difference_id,
            "case1_id": self.case1_id,
            "case2_id": self.case2_id,
            "timestamp": self.timestamp,
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
class ConfidenceDifference:
    """Confidence-guidance difference between two cases.
    
    Contains:
    - Difference metadata (case references, timestamps)
    - Difference content (confidence level shifts, guidance changes)
    - Interpretation (operator-facing explanation)
    """
    
    difference_id: str
    case1_id: str
    case2_id: str
    timestamp: str
    
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
            "difference_id": self.difference_id,
            "case1_id": self.case1_id,
            "case2_id": self.case2_id,
            "timestamp": self.timestamp,
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
class SafeActionDifference:
    """Safe-next-action difference between two cases.
    
    Contains:
    - Difference metadata (case references, timestamps)
    - Difference content (action shifts, evidence changes)
    - Interpretation (operator-facing explanation)
    """
    
    difference_id: str
    case1_id: str
    case2_id: str
    timestamp: str
    
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
            "difference_id": self.difference_id,
            "case1_id": self.case1_id,
            "case2_id": self.case2_id,
            "timestamp": self.timestamp,
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
class CaseComparisonSummary:
    """Operator-readable + machine-readable case comparison summary.
    
    Contains:
    - Summary metadata (ID, timestamp, case references)
    - Comparison results (all comparison types)
    - Notable differences (summary, not detail)
    - Operator narrative
    - Machine export JSON
    
    Key constraints:
    - All differences are presented as operator guidance, not certainty
    - No automatic decision logic - comparison only
    - No remediation logic - read-only comparison
    """
    
    summary_id: str
    timestamp: str
    case1_id: str
    case2_id: str
    
    # Comparison sections
    escalation_differences: List[EscalationDifference]
    confidence_differences: List[ConfidenceDifference]
    safe_action_differences: List[SafeActionDifference]
    
    # Notable differences (summary, not detail)
    notable_differences: List[str]
    
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
            "escalation_differences": [d.to_dict() for d in self.escalation_differences],
            "confidence_differences": [d.to_dict() for d in self.confidence_differences],
            "safe_action_differences": [d.to_dict() for d in self.safe_action_differences],
            "notable_differences": self.notable_differences,
            "correlation_ids": self.correlation_ids,
            "operator_readable": self.operator_readable,
            "machine_readable": self.machine_readable,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# CASE COMPARISON EXPORTER
# ============================================================================


class CaseComparisonExporter:
    """Exporter for case comparison summaries.
    
    Provides:
    - Operator-readable summary export
    - Machine-readable JSON export
    - Correlation ID support (flow_id, request_id, handshake_id, deadline_id)
    - Passive telemetry hooks (no new event framework)
    
    Read-only export only — no behavior changes.
    """
    
    @staticmethod
    def export_summary(
        summary: CaseComparisonSummary,
        format: str = "operator",
    ) -> str:
        """Export summary to requested format.
        
        Args:
            summary: CaseComparisonSummary to export
            format: Output format ("operator" or "json")
        
        Returns:
            Exported content string
        """
        if format == "json":
            return summary.machine_readable
        return summary.operator_readable
    
    @staticmethod
    def export_multiple(
        summaries: List[CaseComparisonSummary],
        format: str = "json",
    ) -> str:
        """Export multiple summaries.
        
        Args:
            summaries: List of CaseComparisonSummary
            format: Output format ("json" only for multiple)
        
        Returns:
            JSON array string
        """
        if format == "json":
            return json.dumps([s.to_dict() for s in summaries], indent=2)
        raise ValueError("Multiple export only supports JSON format")
    
    @staticmethod
    def telemetry_event_summary_created(summary: CaseComparisonSummary) -> Dict[str, Any]:
        """Telemetry event for summary creation (passive, descriptive only).
        
        Args:
            summary: CaseComparisonSummary that was created
        
        Returns:
            Dict with event data (not used for behavior)
        """
        return {
            "event_type": "CASE_COMPARISON_SUMMARY_CREATED",
            "summary_id": summary.summary_id,
            "timestamp": summary.timestamp,
            "case1_id": summary.case1_id,
            "case2_id": summary.case2_id,
            "content_summary": {
                "escalation_diff_count": len(summary.escalation_differences),
                "confidence_diff_count": len(summary.confidence_differences),
                "safe_action_diff_count": len(summary.safe_action_differences),
                "notable_diff_count": len(summary.notable_differences),
            },
        }
    
    @staticmethod
    def telemetry_event_exported(summary: CaseComparisonSummary) -> Dict[str, Any]:
        """Telemetry event for summary export (passive, descriptive only).
        
        Args:
            summary: CaseComparisonSummary that was exported
        
        Returns:
            Dict with event data (not used for behavior)
        """
        return {
            "event_type": "CASE_COMPARISON_SUMMARY_EXPORTED",
            "summary_id": summary.summary_id,
            "timestamp": summary.timestamp,
            "export_format": "json" if "summary_id" in summary.machine_readable else "operator",
        }


# ============================================================================
# OPERATOR CASE COMPARISON LAYER
# ============================================================================


class OperatorCaseComparison:
    """Case comparison layer for operator case summaries.
    
    Provides read-only comparison:
    - Compare consolidated case summaries from v89
    - Compare escalation-context differences across cases
    - Compare confidence-guidance differences at case level
    - Compare safe-next-action differences at case level
    - Generate case comparison summaries
    - Export operator-readable and machine-readable summaries
    
    Correlation support:
    - flow_id
    - request_id
    - handshake_id
    - deadline_id
    
    Read-only comparison only — no behavior changes, no automatic decisions.
    """
    
    def __init__(self):
        """Initialize operator case comparison layer."""
        self._summaries: List[CaseComparisonSummary] = []
        self._sequence_counter: int = 0
    
    def compare_cases(
        self,
        case1: ConsolidatedCaseSummary,
        case2: ConsolidatedCaseSummary,
        correlation_ids: Optional[Dict[str, str]] = None,
    ) -> CaseComparisonSummary:
        """Compare two consolidated case summaries.
        
        Args:
            case1: First ConsolidatedCaseSummary
            case2: Second ConsolidatedCaseSummary
            correlation_ids: Optional correlation IDs
        
        Returns:
            CaseComparisonSummary for the comparison
        
        Note:
            - Comparison only, no new recommendation engine
            - No autonomous decision logic
            - No hidden remediation logic
        """
        self._sequence_counter += 1
        summary_id = f"comparison_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Extract escalation differences
        escalation_diffs = self._extract_escalation_differences(case1, case2, correlation_ids or {})
        
        # Extract confidence differences
        confidence_diffs = self._extract_confidence_differences(case1, case2, correlation_ids or {})
        
        # Extract safe-action differences
        safe_action_diffs = self._extract_safe_action_differences(case1, case2, correlation_ids or {})
        
        # Identify notable differences
        notable_diffs = self._identify_notable_differences(escalation_diffs, confidence_diffs, safe_action_diffs)
        
        # Generate operator-readable summary
        operator_summary = self._generate_operator_summary(
            summary_id, case1.case_id, case2.case_id, escalation_diffs, confidence_diffs, safe_action_diffs,
            notable_diffs
        )
        
        # Generate machine-readable summary
        machine_summary = self._generate_machine_summary(
            summary_id, case1.case_id, case2.case_id, timestamp, escalation_diffs, confidence_diffs, safe_action_diffs,
            notable_diffs, correlation_ids or {}
        )
        
        summary = CaseComparisonSummary(
            summary_id=summary_id,
            timestamp=timestamp,
            case1_id=case1.case_id,
            case2_id=case2.case_id,
            escalation_differences=escalation_diffs,
            confidence_differences=confidence_diffs,
            safe_action_differences=safe_action_diffs,
            notable_differences=notable_diffs,
            correlation_ids=correlation_ids or {},
            operator_readable=operator_summary,
            machine_readable=machine_summary,
        )
        
        self._summaries.append(summary)
        return summary
    
    def _extract_escalation_differences(
        self,
        case1: ConsolidatedCaseSummary,
        case2: ConsolidatedCaseSummary,
        correlation_ids: Dict[str, str],
    ) -> List[EscalationDifference]:
        """Extract escalation context differences between two cases.
        
        Args:
            case1: First ConsolidatedCaseSummary
            case2: Second ConsolidatedCaseSummary
            correlation_ids: Correlation IDs
        
        Returns:
            List of EscalationDifference
        """
        if not case1.escalation_context or not case2.escalation_context:
            return []
        
        differences = []
        
        # Compare urgency levels
        case1_urgency = "normal"
        for e in case1.escalation_context:
            if e.urgency_level in ["attention", "urgent"]:
                case1_urgency = e.urgency_level
                break
        
        case2_urgency = "normal"
        for e in case2.escalation_context:
            if e.urgency_level in ["attention", "urgent"]:
                case2_urgency = e.urgency_level
                break
        
        urgency_shift = "stable"
        if case1_urgency == "normal" and case2_urgency in ["attention", "urgent"]:
            urgency_shift = "increasing"
        elif case1_urgency in ["attention", "urgent"] and case2_urgency == "normal":
            urgency_shift = "decreasing"
        elif case1_urgency == "attention" and case2_urgency == "urgent":
            urgency_shift = "increasing"
        elif case1_urgency == "urgent" and case2_urgency == "attention":
            urgency_shift = "decreasing"
        
        # Compare event counts
        case1_event_count = sum(len(e.escalation_events) for e in case1.escalation_context)
        case2_event_count = sum(len(e.escalation_events) for e in case2.escalation_context)
        event_delta = case2_event_count - case1_event_count
        
        # Determine significance
        significance = "low"
        if case1_urgency == "normal" and case2_urgency == "urgent":
            significance = "significant"
        elif case1_urgency == "urgent" and case2_urgency == "normal":
            significance = "significant"
        elif abs(event_delta) > 2:
            significance = "moderate"
        
        interpretation = f"Escalation context {'increased' if urgency_shift == 'increasing' else 'decreased' if urgency_shift == 'decreasing' else 'stable'} from {case1_urgency} to {case2_urgency}."
        if abs(event_delta) > 0:
            interpretation += f" Event count changed by {event_delta}."
        
        differences.append(EscalationDifference(
            difference_id=f"escalation_diff_{uuid.uuid4().hex[:8]}",
            case1_id=case1.case_id,
            case2_id=case2.case_id,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
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
        
        return differences
    
    def _extract_confidence_differences(
        self,
        case1: ConsolidatedCaseSummary,
        case2: ConsolidatedCaseSummary,
        correlation_ids: Dict[str, str],
    ) -> List[ConfidenceDifference]:
        """Extract confidence-guidance differences between two cases.
        
        Args:
            case1: First ConsolidatedCaseSummary
            case2: Second ConsolidatedCaseSummary
            correlation_ids: Correlation IDs
        
        Returns:
            List of ConfidenceDifference
        """
        if not case1.recovery_guidance or not case2.recovery_guidance:
            return []
        
        differences = []
        
        # Compare guidance context (simple aggregation)
        case1_confidence = "medium"
        case2_confidence = "medium"
        
        if case1.recovery_guidance:
            confidences = [g.confidence_level for g in case1.recovery_guidance if g.confidence_level]
            if confidences:
                case1_confidence = max(set(confidences), key=confidences.count)
        
        if case2.recovery_guidance:
            confidences = [g.confidence_level for g in case2.recovery_guidance if g.confidence_level]
            if confidences:
                case2_confidence = max(set(confidences), key=confidences.count)
        
        confidence_shift = "stable"
        if case1_confidence == "low" and case2_confidence in ["medium", "high"]:
            confidence_shift = "increasing"
        elif case1_confidence in ["low", "medium"] and case2_confidence == "high":
            confidence_shift = "increasing"
        elif case1_confidence in ["medium", "high"] and case2_confidence == "low":
            confidence_shift = "decreasing"
        elif case1_confidence == "high" and case2_confidence in ["medium", "low"]:
            confidence_shift = "decreasing"
        
        # Check guidance changes
        case1_has_guidance = any(g.safe_next_action for g in case1.recovery_guidance)
        case2_has_guidance = any(g.safe_next_action for g in case2.recovery_guidance)
        
        guidance_change = "unchanged"
        if case1_has_guidance and case2_has_guidance:
            guidance_change = "unchanged"
        elif case1_has_guidance and not case2_has_guidance:
            guidance_change = "removed"
        elif not case1_has_guidance and case2_has_guidance:
            guidance_change = "added"
        
        guidance_context = "recovery guidance"
        
        interpretation = f"Confidence guidance {'increased' if confidence_shift == 'increasing' else 'decreased' if confidence_shift == 'decreasing' else 'stable'} from {case1_confidence} to {case2_confidence}."
        
        significance = "low"
        if case1_confidence == "low" and case2_confidence == "high":
            significance = "significant"
        elif case1_confidence == "high" and case2_confidence == "low":
            significance = "significant"
        
        differences.append(ConfidenceDifference(
            difference_id=f"confidence_diff_{uuid.uuid4().hex[:8]}",
            case1_id=case1.case_id,
            case2_id=case2.case_id,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            case1_confidence=case1_confidence,
            case2_confidence=case2_confidence,
            confidence_shift=confidence_shift,
            guidance_context=guidance_context,
            guidance_change=guidance_change,
            interpretation=interpretation,
            heuristic_significance=significance,
            heuristic_reason=f"Confidence shift {confidence_shift} with {significance} significance",
            correlation_ids=correlation_ids,
        ))
        
        return differences
    
    def _extract_safe_action_differences(
        self,
        case1: ConsolidatedCaseSummary,
        case2: ConsolidatedCaseSummary,
        correlation_ids: Dict[str, str],
    ) -> List[SafeActionDifference]:
        """Extract safe-next-action differences between two cases.
        
        Args:
            case1: First ConsolidatedCaseSummary
            case2: Second ConsolidatedCaseSummary
            correlation_ids: Correlation IDs
        
        Returns:
            List of SafeActionDifference
        """
        if not case1.recovery_guidance or not case2.recovery_guidance:
            return []
        
        differences = []
        
        # Compare safe-next-actions
        case1_actions = [g.safe_next_action for g in case1.recovery_guidance if g.safe_next_action]
        case2_actions = [g.safe_next_action for g in case2.recovery_guidance if g.safe_next_action]
        
        case1_action = case1_actions[0] if case1_actions else None
        case2_action = case2_actions[0] if case2_actions else None
        
        action_shift = "unchanged"
        if case1_action and not case2_action:
            action_shift = "removed"
        elif not case1_action and case2_action:
            action_shift = "added"
        elif case1_action != case2_action:
            action_shift = "updated"
        
        # Check evidence changes
        case1_evidence = sum(len(g.evidence_references) for g in case1.recovery_guidance)
        case2_evidence = sum(len(g.evidence_references) for g in case2.recovery_guidance)
        
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
        
        differences.append(SafeActionDifference(
            difference_id=f"safe_action_diff_{uuid.uuid4().hex[:8]}",
            case1_id=case1.case_id,
            case2_id=case2.case_id,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
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
        
        return differences
    
    def _identify_notable_differences(
        self,
        escalation_diffs: List[EscalationDifference],
        confidence_diffs: List[ConfidenceDifference],
        safe_action_diffs: List[SafeActionDifference],
    ) -> List[str]:
        """Identify notable differences (summary, not detail).
        
        Args:
            escalation_diffs: Escalation differences
            confidence_diffs: Confidence differences
            safe_action_diffs: Safe action differences
        
        Returns:
            List of notable difference strings (summary only)
        """
        changes = []
        
        if escalation_diffs:
            escalation_changes = [d for d in escalation_diffs if d.urgency_shift != "stable"]
            if escalation_changes:
                changes.append(f"Escalation urgency shifted in {len(escalation_changes)} comparison(s)")
        
        if confidence_diffs:
            confidence_changes = [d for d in confidence_diffs if d.confidence_shift != "stable"]
            if confidence_changes:
                changes.append(f"Confidence guidance changed in {len(confidence_changes)} comparison(s)")
        
        if safe_action_diffs:
            action_changes = [d for d in safe_action_diffs if d.action_shift != "unchanged"]
            if action_changes:
                changes.append(f"Safe-next-action changed in {len(action_changes)} comparison(s)")
        
        if not changes:
            changes.append("No notable differences detected - consistent patterns")
        
        return changes
    
    def _generate_operator_summary(
        self,
        summary_id: str,
        case1_id: str,
        case2_id: str,
        escalation_diffs: List[EscalationDifference],
        confidence_diffs: List[ConfidenceDifference],
        safe_action_diffs: List[SafeActionDifference],
        notable_diffs: List[str],
    ) -> str:
        """Generate operator-readable summary.
        
        Args:
            summary_id: Summary ID
            case1_id: First case ID
            case2_id: Second case ID
            escalation_diffs: Escalation differences
            confidence_diffs: Confidence differences
            safe_action_diffs: Safe action differences
            notable_diffs: Notable differences
        
        Returns:
            Operator-readable multi-line string
        """
        lines = [
            "=" * 70,
            "OPERATOR CASE COMPARISON SUMMARY",
            "=" * 70,
            f"Summary ID: {summary_id}",
            f"Case 1 ID: {case1_id}",
            f"Case 2 ID: {case2_id}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
            "",
            "-" * 70,
            "ESCALATION CONTEXT DIFFERENCES",
            "-" * 70,
        ]
        
        if escalation_diffs:
            for d in escalation_diffs:
                lines.append(f"  [{d.urgency_shift.upper()}] {d.case1_urgency} → {d.case2_urgency}")
                lines.append(f"      Events: {d.case1_event_count} → {d.case2_event_count} (Δ{d.event_delta})")
                lines.append(f"      Interpretation: {d.interpretation[:80]}...")
        else:
            lines.append("  No escalation context differences")
        
        lines.extend([
            "",
            "-" * 70,
            "CONFIDENCE GUIDANCE DIFFERENCES",
            "-" * 70,
        ])
        
        if confidence_diffs:
            for d in confidence_diffs:
                lines.append(f"  [{d.confidence_shift.upper()}] {d.case1_confidence} → {d.case2_confidence}")
                lines.append(f"      Guidance: {d.guidance_change}")
                lines.append(f"      Interpretation: {d.interpretation[:80]}...")
        else:
            lines.append("  No confidence guidance differences")
        
        lines.extend([
            "",
            "-" * 70,
            "SAFE-NEXT-ACTION DIFFERENCES",
            "-" * 70,
        ])
        
        if safe_action_diffs:
            for d in safe_action_diffs:
                action1 = d.case1_action or "(none)"
                action2 = d.case2_action or "(none)"
                lines.append(f"  [{d.action_shift.upper()}] {action1} → {action2}")
                lines.append(f"      Evidence: {d.evidence_change}")
                lines.append(f"      Interpretation: {d.interpretation[:80]}...")
        else:
            lines.append("  No safe-next-action differences")
        
        lines.extend([
            "",
            "-" * 70,
            "NOTABLE DIFFERENCES",
            "-" * 70,
        ])
        
        for diff in notable_diffs:
            lines.append(f"  • {diff}")
        
        lines.extend([
            "",
            "-" * 70,
            "HEURISTIC NOTE",
            "-" * 70,
            "Differences are presented as operator guidance, not certainties.",
            "Use these summaries to inform decisions, not replace them.",
            "",
            "Key distinctions:",
            "- Guidance levels: Heuristic assessments, not automatic actions",
            "- Confidence: Operator guidance, not certainty",
            "- Significance: Interpretation context, not prediction",
            "- Escalation: Attention indicators, not automatic triggers",
            "",
            "This comparison layer provides read-only case comparison summaries,",
            "not automatic decision-making or remediation.",
            "",
            "=" * 70,
        ])
        
        return "\n".join(lines)
    
    def _generate_machine_summary(
        self,
        summary_id: str,
        case1_id: str,
        case2_id: str,
        timestamp: str,
        escalation_diffs: List[EscalationDifference],
        confidence_diffs: List[ConfidenceDifference],
        safe_action_diffs: List[SafeActionDifference],
        notable_diffs: List[str],
        correlation_ids: Dict[str, str],
    ) -> str:
        """Generate machine-readable summary (JSON).
        
        Args:
            summary_id: Summary ID
            case1_id: First case ID
            case2_id: Second case ID
            timestamp: Timestamp
            escalation_diffs: Escalation differences
            confidence_diffs: Confidence differences
            safe_action_diffs: Safe action differences
            notable_diffs: Notable differences
            correlation_ids: Correlation IDs
        
        Returns:
            JSON string
        """
        data = {
            "summary_id": summary_id,
            "timestamp": timestamp,
            "case1_id": case1_id,
            "case2_id": case2_id,
            "escalation_differences": [d.to_dict() for d in escalation_diffs],
            "confidence_differences": [d.to_dict() for d in confidence_diffs],
            "safe_action_differences": [d.to_dict() for d in safe_action_diffs],
            "notable_differences": notable_diffs,
            "correlation_ids": correlation_ids,
        }
        return json.dumps(data, indent=2)
    
    def get_summary(
        self,
        summary_id: str,
    ) -> Optional[CaseComparisonSummary]:
        """Get a specific comparison summary.
        
        Args:
            summary_id: Summary ID to retrieve
        
        Returns:
            CaseComparisonSummary if found, None otherwise
        """
        for summary in self._summaries:
            if summary.summary_id == summary_id:
                return summary
        return None
    
    def get_summaries(self) -> List[CaseComparisonSummary]:
        """Get all comparison summaries.
        
        Returns:
            List of CaseComparisonSummary
        """
        return self._summaries
    
    def get_summaries_for_case(
        self,
        case_id: str,
    ) -> List[CaseComparisonSummary]:
        """Get summaries for a specific case.
        
        Args:
            case_id: Case ID to filter by (case1 or case2)
        
        Returns:
            List of CaseComparisonSummary for case
        """
        return [s for s in self._summaries if s.case1_id == case_id or s.case2_id == case_id]
    
    def export_operator_readable(self) -> str:
        """Export all summaries as operator-readable string.
        
        Returns:
            Multi-line operator-readable summary
        """
        lines = [
            "=" * 70,
            "ALL CASE COMPARISON SUMMARIES",
            "=" * 70,
            f"Total Summaries: {len(self._summaries)}",
            "",
        ]
        
        for summary in self._summaries[-5:]:  # Last 5 summaries
            lines.append(f"Summary ID: {summary.summary_id}")
            lines.append(f"Case 1 ID: {summary.case1_id}")
            lines.append(f"Case 2 ID: {summary.case2_id}")
            lines.append(f"Escalation Differences: {len(summary.escalation_differences)}")
            lines.append(f"Confidence Differences: {len(summary.confidence_differences)}")
            lines.append("")
        
        if not self._summaries:
            lines.append("No case comparison summaries available.")
        
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


def integrate_with_v89_consolidation(comparison: OperatorCaseComparison) -> Dict[str, Any]:
    """Integration hook for v89 consolidation — read-only comparison only.
    
    No behavior changes to existing consolidation logic.
    """
    return {"hooked": True, "measures": "consolidation_comparison_integration"}
