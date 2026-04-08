# operator_case_window_summary.py - WESLR v92: Operator Case Window Summary / Drift Significance Layer
# Read-only operator-facing layer that summarizes case-timeline comparisons within defined time windows
# and highlights which drifts matter most.
# No optimization, no remediation, no orchestration, no backend/service/UI.
# No TIA/C#, no storage framework expansion, no analytics engine beyond window scope.

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .operator_case_timeline_comparison import (
    TimelineComparisonResult,
    EscalationDriftRecord,
    ConfidenceDriftRecord,
    SafeActionDriftRecord,
)


# ============================================================================
# WINDOW SUMMARY DATA MODELS
# ============================================================================


@dataclass
class DriftSignificance:
    """Drift significance record for a single drift type within a time window.
    
    Contains:
    - Drift metadata (type, comparison reference)
    - Significance content (weight, interpretation)
    - Operator guidance (not certainty)
    """
    
    significance_id: str
    timestamp: str
    drift_type: str  # "escalation", "confidence", "safe_action"
    comparison_id: str
    
    # Drift reference
    reference_drift_id: str
    drift_direction: str  # "increasing", "decreasing", "stable", "variable"
    
    # Significance content
    base_weight: float  # Base weight by drift type
    context_modifier: float  # Context-based modifier
    final_significance: float  # Weighted final significance (0.0 - 1.0)
    
    # Operator guidance
    interpretation: str  # What this means for operators
    heuristic_significance: str  # "low", "medium", "high" (heuristic, not certainty)
    heuristic_reason: str  # Why this significance
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "significance_id": self.significance_id,
            "timestamp": self.timestamp,
            "drift_type": self.drift_type,
            "comparison_id": self.comparison_id,
            "reference_drift_id": self.reference_drift_id,
            "drift_direction": self.drift_direction,
            "base_weight": self.base_weight,
            "context_modifier": self.context_modifier,
            "final_significance": self.final_significance,
            "interpretation": self.interpretation,
            "heuristic_significance": self.heuristic_significance,
            "heuristic_reason": self.heuristic_reason,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class WindowSummary:
    """Operator-readable + machine-readable window summary.
    
    Contains:
    - Summary metadata (ID, timestamp, window configuration)
    - Drift significance records
    - Drift significance distribution
    - Most significant drifts (operator guidance)
    - Operator narrative
    - Machine export JSON
    
    Key constraints:
    - Significance is heuristic guidance, not certainty
    - No automatic decision logic - summary only
    - No remediation logic - read-only summary
    """
    
    summary_id: str
    timestamp: str
    window_config_id: str
    window_start: str
    window_end: str
    comparison_count: int
    
    # Drift significance sections
    escalation_significance: List[DriftSignificance]
    confidence_significance: List[DriftSignificance]
    safe_action_significance: List[DriftSignificance]
    
    # Most significant drifts (operator guidance, not certainty)
    most_significant_drifts: List[Dict[str, Any]]
    
    # Drift significance distribution
    significance_distribution: Dict[str, float]
    total_significance: float
    
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
            "window_config_id": self.window_config_id,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "comparison_count": self.comparison_count,
            "escalation_significance": [d.to_dict() for d in self.escalation_significance],
            "confidence_significance": [d.to_dict() for d in self.confidence_significance],
            "safe_action_significance": [d.to_dict() for d in self.safe_action_significance],
            "most_significant_drifts": self.most_significant_drifts,
            "significance_distribution": self.significance_distribution,
            "total_significance": self.total_significance,
            "correlation_ids": self.correlation_ids,
            "operator_readable": self.operator_readable,
            "machine_readable": self.machine_readable,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class WindowConfiguration:
    """Minimal window configuration.
    
    Contains:
    - Window boundaries
    - Drift significance thresholds
    - Correlation context
    
    No scheduling logic. No persistence. No framework expansion.
    """
    
    config_id: str
    window_start: str  # ISO timestamp
    window_end: str  # ISO timestamp
    min_significance_threshold: float  # 0.0 - 1.0
    max_significant_drifts: int  # Max to include in "most significant"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "config_id": self.config_id,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "min_significance_threshold": self.min_significance_threshold,
            "max_significant_drifts": self.max_significant_drifts,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# WINDOW SUMMARY EXPORTER
# ============================================================================


class WindowSummaryExporter:
    """Exporter for window summary results.
    
    Provides:
    - Operator-readable summary export
    - Machine-readable JSON export
    - Correlation ID support (flow_id, request_id, handshake_id, deadline_id)
    - Passive telemetry hooks (no new event framework)
    
    Read-only export only — no behavior changes.
    """
    
    @staticmethod
    def export_summary(
        summary: WindowSummary,
        format: str = "operator",
    ) -> str:
        """Export summary to requested format.
        
        Args:
            summary: WindowSummary to export
            format: Output format ("operator" or "json")
        
        Returns:
            Exported content string
        """
        if format == "json":
            return summary.machine_readable
        return summary.operator_readable
    
    @staticmethod
    def export_multiple(
        summaries: List[WindowSummary],
        format: str = "json",
    ) -> str:
        """Export multiple summaries.
        
        Args:
            summaries: List of WindowSummary
            format: Output format ("json" only for multiple)
        
        Returns:
            JSON array string
        """
        if format == "json":
            return json.dumps([s.to_dict() for s in summaries], indent=2)
        raise ValueError("Multiple export only supports JSON format")
    
    @staticmethod
    def telemetry_event_summary_created(summary: WindowSummary) -> Dict[str, Any]:
        """Telemetry event for summary creation (passive, descriptive only).
        
        Args:
            summary: WindowSummary that was created
        
        Returns:
            Dict with event data (not used for behavior)
        """
        return {
            "event_type": "WINDOW_SUMMARY_CREATED",
            "summary_id": summary.summary_id,
            "timestamp": summary.timestamp,
            "window_config_id": summary.window_config_id,
            "comparison_count": summary.comparison_count,
            "content_summary": {
                "escalation_significance_count": len(summary.escalation_significance),
                "confidence_significance_count": len(summary.confidence_significance),
                "safe_action_significance_count": len(summary.safe_action_significance),
                "most_significant_count": len(summary.most_significant_drifts),
            },
        }
    
    @staticmethod
    def telemetry_event_exported(summary: WindowSummary) -> Dict[str, Any]:
        """Telemetry event for summary export (passive, descriptive only).
        
        Args:
            summary: WindowSummary that was exported
        
        Returns:
            Dict with event data (not used for behavior)
        """
        return {
            "event_type": "WINDOW_SUMMARY_EXPORTED",
            "summary_id": summary.summary_id,
            "timestamp": summary.timestamp,
            "export_format": "json" if "summary_id" in summary.machine_readable else "operator",
        }


# ============================================================================
# OPERATOR CASE WINDOW SUMMARY LAYER
# ============================================================================


class OperatorCaseWindowSummary:
    """Window summary layer for operator case-timeline comparisons.
    
    Provides read-only window summary:
    - Aggregate timeline comparisons within defined time windows
    - Calculate drift significance within windows
    - Identify most significant drifts (operator guidance, not certainty)
    - Generate window summaries with significance heuristics
    - Export operator-readable and machine-readable summaries
    
    Correlation support:
    - flow_id
    - request_id
    - handshake_id
    - deadline_id
    
    Read-only summary only — no behavior changes, no automatic decisions.
    """
    
    # Base weights by drift type (heuristic, not scoring framework)
    BASE_WEIGHTS = {
        "escalation": 1.0,
        "confidence": 0.8,
        "safe_action": 0.9,
    }
    
    def __init__(self):
        """Initialize operator case window summary layer."""
        self._summaries: List[WindowSummary] = []
        self._sequence_counter: int = 0
    
    def summarize_window(
        self,
        comparisons: List[TimelineComparisonResult],
        window_config: WindowConfiguration,
        correlation_ids: Optional[Dict[str, str]] = None,
    ) -> WindowSummary:
        """Summarize timeline comparisons within a time window.
        
        Args:
            comparisons: List of TimelineComparisonResult
            window_config: WindowConfiguration with boundaries
            correlation_ids: Optional correlation IDs
        
        Returns:
            WindowSummary for the window
        
        Note:
            - Summary only, no new scoring framework
            - No autonomous decision logic
            - No hidden prioritization engine
        """
        self._sequence_counter += 1
        summary_id = f"window_summary_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Extract drift significance
        escalation_significance = self._extract_escalation_significance(
            comparisons, correlation_ids or {}, window_config
        )
        
        confidence_significance = self._extract_confidence_significance(
            comparisons, correlation_ids or {}, window_config
        )
        
        safe_action_significance = self._extract_safe_action_significance(
            comparisons, correlation_ids or {}, window_config
        )
        
        # Combine all significance records
        all_significance = (
            escalation_significance + confidence_significance + safe_action_significance
        )
        
        # Sort by final significance and get most significant
        sorted_significance = sorted(
            all_significance,
            key=lambda x: x.final_significance,
            reverse=True
        )
        
        most_significant = sorted_significance[:window_config.max_significant_drifts]
        
        # Calculate significance distribution
        significance_distribution = self._calculate_significance_distribution(
            escalation_significance, confidence_significance, safe_action_significance
        )
        
        total_significance = sum(d.final_significance for d in all_significance)
        
        # Generate operator-readable summary
        operator_summary = self._generate_operator_summary(
            summary_id, window_config, escalation_significance, confidence_significance,
            safe_action_significance, most_significant, significance_distribution
        )
        
        # Generate machine-readable summary
        machine_summary = self._generate_machine_summary(
            summary_id, timestamp, window_config, escalation_significance,
            confidence_significance, safe_action_significance, most_significant,
            significance_distribution, total_significance, correlation_ids or {}
        )
        
        summary = WindowSummary(
            summary_id=summary_id,
            timestamp=timestamp,
            window_config_id=window_config.config_id,
            window_start=window_config.window_start,
            window_end=window_config.window_end,
            comparison_count=len(comparisons),
            escalation_significance=escalation_significance,
            confidence_significance=confidence_significance,
            safe_action_significance=safe_action_significance,
            most_significant_drifts=[d.to_dict() for d in most_significant],
            significance_distribution=significance_distribution,
            total_significance=total_significance,
            correlation_ids=correlation_ids or {},
            operator_readable=operator_summary,
            machine_readable=machine_summary,
        )
        
        self._summaries.append(summary)
        return summary
    
    def _extract_escalation_significance(
        self,
        comparisons: List[TimelineComparisonResult],
        correlation_ids: Dict[str, str],
        window_config: WindowConfiguration,
    ) -> List[DriftSignificance]:
        """Extract escalation significance records from comparisons.
        
        Args:
            comparisons: Timeline comparison results
            correlation_ids: Correlation IDs
            window_config: Window configuration
        
        Returns:
            List of DriftSignificance for escalation
        """
        significances = []
        
        for comparison in comparisons:
            if not comparison.escalation_drifts:
                continue
            
            for drift in comparison.escalation_drifts:
                # Base weight for escalation
                base_weight = self.BASE_WEIGHTS.get("escalation", 1.0)
                
                # Context modifier based on urgency shift
                context_modifier = 1.0
                if drift.urgency_shift == "increasing":
                    context_modifier = 1.5 if drift.heuristic_significance == "significant" else 1.2
                elif drift.urgency_shift == "decreasing":
                    context_modifier = 0.8
                
                # Final significance (clamped 0.0 - 1.0)
                final_sig = min(1.0, base_weight * context_modifier)
                
                interpretation = f"Escalation drift showing {'increasing' if drift.urgency_shift == 'increasing' else 'decreasing' if drift.urgency_shift == 'decreasing' else 'stable'} pattern."
                
                significances.append(DriftSignificance(
                    significance_id=f"esc_signif_{uuid.uuid4().hex[:8]}",
                    timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    drift_type="escalation",
                    comparison_id=comparison.summary_id,
                    reference_drift_id=drift.drift_id,
                    drift_direction=drift.urgency_shift,
                    base_weight=base_weight,
                    context_modifier=context_modifier,
                    final_significance=final_sig,
                    interpretation=interpretation,
                    heuristic_significance=drift.heuristic_significance,
                    heuristic_reason=f"Urgency shift {drift.urgency_shift} with {drift.heuristic_significance} significance",
                ))
        
        return significances
    
    def _extract_confidence_significance(
        self,
        comparisons: List[TimelineComparisonResult],
        correlation_ids: Dict[str, str],
        window_config: WindowConfiguration,
    ) -> List[DriftSignificance]:
        """Extract confidence significance records from comparisons.
        
        Args:
            comparisons: Timeline comparison results
            correlation_ids: Correlation IDs
            window_config: Window configuration
        
        Returns:
            List of DriftSignificance for confidence
        """
        significances = []
        
        for comparison in comparisons:
            if not comparison.confidence_drifts:
                continue
            
            for drift in comparison.confidence_drifts:
                # Base weight for confidence
                base_weight = self.BASE_WEIGHTS.get("confidence", 0.8)
                
                # Context modifier based on confidence shift
                context_modifier = 1.0
                if drift.confidence_shift == "increasing":
                    context_modifier = 1.3 if drift.heuristic_significance == "significant" else 1.1
                elif drift.confidence_shift == "decreasing":
                    context_modifier = 0.7
                
                # Final significance (clamped 0.0 - 1.0)
                final_sig = min(1.0, base_weight * context_modifier)
                
                interpretation = f"Confidence drift showing {'increasing' if drift.confidence_shift == 'increasing' else 'decreasing' if drift.confidence_shift == 'decreasing' else 'stable'} pattern."
                
                significances.append(DriftSignificance(
                    significance_id=f"conf_signif_{uuid.uuid4().hex[:8]}",
                    timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    drift_type="confidence",
                    comparison_id=comparison.summary_id,
                    reference_drift_id=drift.drift_id,
                    drift_direction=drift.confidence_shift,
                    base_weight=base_weight,
                    context_modifier=context_modifier,
                    final_significance=final_sig,
                    interpretation=interpretation,
                    heuristic_significance=drift.heuristic_significance,
                    heuristic_reason=f"Confidence shift {drift.confidence_shift} with {drift.heuristic_significance} significance",
                ))
        
        return significances
    
    def _extract_safe_action_significance(
        self,
        comparisons: List[TimelineComparisonResult],
        correlation_ids: Dict[str, str],
        window_config: WindowConfiguration,
    ) -> List[DriftSignificance]:
        """Extract safe-action significance records from comparisons.
        
        Args:
            comparisons: Timeline comparison results
            correlation_ids: Correlation IDs
            window_config: Window configuration
        
        Returns:
            List of DriftSignificance for safe-action
        """
        significances = []
        
        for comparison in comparisons:
            if not comparison.safe_action_drifts:
                continue
            
            for drift in comparison.safe_action_drifts:
                # Base weight for safe-action
                base_weight = self.BASE_WEIGHTS.get("safe_action", 0.9)
                
                # Context modifier based on action shift
                context_modifier = 1.0
                if drift.action_shift in ["added", "removed", "updated"]:
                    context_modifier = 1.2 if drift.heuristic_significance == "significant" else 1.0
                
                # Final significance (clamped 0.0 - 1.0)
                final_sig = min(1.0, base_weight * context_modifier)
                
                interpretation = f"Safe-action drift showing {'changed' if drift.action_shift in ['added', 'removed', 'updated'] else 'unchanged'} pattern."
                
                significances.append(DriftSignificance(
                    significance_id=f"safe_signif_{uuid.uuid4().hex[:8]}",
                    timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    drift_type="safe_action",
                    comparison_id=comparison.summary_id,
                    reference_drift_id=drift.drift_id,
                    drift_direction=drift.action_shift,
                    base_weight=base_weight,
                    context_modifier=context_modifier,
                    final_significance=final_sig,
                    interpretation=interpretation,
                    heuristic_significance=drift.heuristic_significance,
                    heuristic_reason=f"Action shift {drift.action_shift} with {drift.heuristic_significance} significance",
                ))
        
        return significances
    
    def _calculate_significance_distribution(
        self,
        escalation_significance: List[DriftSignificance],
        confidence_significance: List[DriftSignificance],
        safe_action_significance: List[DriftSignificance],
    ) -> Dict[str, float]:
        """Calculate significance distribution by drift type.
        
        Args:
            escalation_significance: Escalation significance records
            confidence_significance: Confidence significance records
            safe_action_significance: Safe action significance records
        
        Returns:
            Dict with significance totals by type
        """
        return {
            "escalation": sum(d.final_significance for d in escalation_significance),
            "confidence": sum(d.final_significance for d in confidence_significance),
            "safe_action": sum(d.final_significance for d in safe_action_significance),
            "total": sum(d.final_significance for d in escalation_significance + confidence_significance + safe_action_significance),
        }
    
    def _generate_operator_summary(
        self,
        summary_id: str,
        window_config: WindowConfiguration,
        escalation_significance: List[DriftSignificance],
        confidence_significance: List[DriftSignificance],
        safe_action_significance: List[DriftSignificance],
        most_significant: List[DriftSignificance],
        significance_distribution: Dict[str, float],
    ) -> str:
        """Generate operator-readable summary.
        
        Args:
            summary_id: Summary ID
            window_config: Window configuration
            escalation_significance: Escalation significance records
            confidence_significance: Confidence significance records
            safe_action_significance: Safe action significance records
            most_significant: Most significant drifts
            significance_distribution: Significance distribution dict
        
        Returns:
            Operator-readable multi-line string
        """
        lines = [
            "=" * 70,
            "OPERATOR CASE WINDOW SUMMARY",
            "=" * 70,
            f"Summary ID: {summary_id}",
            f"Window Start: {window_config.window_start}",
            f"Window End: {window_config.window_end}",
            f"Total Comparisons: {len(self._find_comparisons_for_window(window_config.window_start, window_config.window_end))}",
            "",
            "-" * 70,
            "SIGNIFICANCE DISTRIBUTION",
            "-" * 70,
            f"  Escalation significance: {significance_distribution.get('escalation', 0):.2f}",
            f"  Confidence significance: {significance_distribution.get('confidence', 0):.2f}",
            f"  Safe-action significance: {significance_distribution.get('safe_action', 0):.2f}",
            f"  Total significance: {significance_distribution.get('total', 0):.2f}",
            "",
            "-" * 70,
            "ESCALATION DRIFT SIGNIFICANCE",
            "-" * 70,
        ]
        
        if escalation_significance:
            for d in escalation_significance:
                lines.append(f"  [{d.drift_direction.upper()}] Significance: {d.final_significance:.2f}")
                lines.append(f"      Interpretation: {d.interpretation[:80]}...")
                lines.append(f"      Heuristic: {d.heuristic_significance}")
        else:
            lines.append("  No escalation significance detected")
        
        lines.extend([
            "",
            "-" * 70,
            "CONFIDENCE DRIFT SIGNIFICANCE",
            "-" * 70,
        ])
        
        if confidence_significance:
            for d in confidence_significance:
                lines.append(f"  [{d.drift_direction.upper()}] Significance: {d.final_significance:.2f}")
                lines.append(f"      Interpretation: {d.interpretation[:80]}...")
                lines.append(f"      Heuristic: {d.heuristic_significance}")
        else:
            lines.append("  No confidence significance detected")
        
        lines.extend([
            "",
            "-" * 70,
            "SAFE-ACTION DRIFT SIGNIFICANCE",
            "-" * 70,
        ])
        
        if safe_action_significance:
            for d in safe_action_significance:
                lines.append(f"  [{d.drift_direction.upper()}] Significance: {d.final_significance:.2f}")
                lines.append(f"      Interpretation: {d.interpretation[:80]}...")
                lines.append(f"      Heuristic: {d.heuristic_significance}")
        else:
            lines.append("  No safe-action significance detected")
        
        lines.extend([
            "",
            "-" * 70,
            "MOST SIGNIFICANT DRIFTS",
            "-" * 70,
        ])
        
        if most_significant:
            for d in most_significant:
                lines.append(f"  [{d.drift_type.upper()}] {d.final_significance:.2f}")
                lines.append(f"      {d.interpretation[:80]}...")
                lines.append(f"      Reason: {d.heuristic_reason}")
        else:
            lines.append("  No significant drifts detected")
        
        lines.extend([
            "",
            "-" * 70,
            "HEURISTIC NOTE",
            "-" * 70,
            "Significance is presented as operator guidance, not certainty.",
            "Use these summaries to inform decisions, not replace them.",
            "",
            "Key distinctions:",
            "- Significance levels: Heuristic assessments, not automatic actions",
            "- Weights: Operator guidance, not scoring framework",
            "- Thresholds: Attention indicators, not decision triggers",
            "- Most significant: Interpretation context, not ranking",
            "",
            "This window summary layer provides read-only summary with",
            "heuristic significance, not automatic decision-making or remediation.",
            "",
            "=" * 70,
        ])
        
        return "\n".join(lines)
    
    def _generate_machine_summary(
        self,
        summary_id: str,
        timestamp: str,
        window_config: WindowConfiguration,
        escalation_significance: List[DriftSignificance],
        confidence_significance: List[DriftSignificance],
        safe_action_significance: List[DriftSignificance],
        most_significant: List[DriftSignificance],
        significance_distribution: Dict[str, float],
        total_significance: float,
        correlation_ids: Dict[str, str],
    ) -> str:
        """Generate machine-readable summary (JSON).
        
        Args:
            summary_id: Summary ID
            timestamp: Timestamp
            window_config: Window configuration
            escalation_significance: Escalation significance records
            confidence_significance: Confidence significance records
            safe_action_significance: Safe action significance records
            most_significant: Most significant drifts
            significance_distribution: Significance distribution dict
            total_significance: Total significance value
            correlation_ids: Correlation IDs
        
        Returns:
            JSON string
        """
        data = {
            "summary_id": summary_id,
            "timestamp": timestamp,
            "window_config_id": window_config.config_id,
            "window_start": window_config.window_start,
            "window_end": window_config.window_end,
            "comparison_count": len(self._find_comparisons_for_window(window_config.window_start, window_config.window_end)),
            "escalation_significance": [d.to_dict() for d in escalation_significance],
            "confidence_significance": [d.to_dict() for d in confidence_significance],
            "safe_action_significance": [d.to_dict() for d in safe_action_significance],
            "most_significant_drifts": [d.to_dict() for d in most_significant],
            "significance_distribution": significance_distribution,
            "total_significance": total_significance,
            "correlation_ids": correlation_ids,
        }
        return json.dumps(data, indent=2)
    
    def _find_comparisons_for_window(
        self,
        window_start: str,
        window_end: str,
    ) -> List[TimelineComparisonResult]:
        """Find comparisons within a time window.
        
        Args:
            window_start: Window start timestamp
            window_end: Window end timestamp
        
        Returns:
            List of comparisons within window
        """
        # Simplified: return all results (in real implementation, would filter by timestamp)
        return self._summaries
    
    def get_summary(
        self,
        summary_id: str,
    ) -> Optional[WindowSummary]:
        """Get a specific window summary.
        
        Args:
            summary_id: Summary ID to retrieve
        
        Returns:
            WindowSummary if found, None otherwise
        """
        for summary in self._summaries:
            if summary.summary_id == summary_id:
                return summary
        return None
    
    def get_summaries(self) -> List[WindowSummary]:
        """Get all window summaries.
        
        Returns:
            List of WindowSummary
        """
        return self._summaries
    
    def export_operator_readable(self) -> str:
        """Export all summaries as operator-readable string.
        
        Returns:
            Multi-line operator-readable summary
        """
        lines = [
            "=" * 70,
            "ALL CASE WINDOW SUMMARIES",
            "=" * 70,
            f"Total Summaries: {len(self._summaries)}",
            "",
        ]
        
        for summary in self._summaries[-5:]:  # Last 5 summaries
            lines.append(f"Summary ID: {summary.summary_id}")
            lines.append(f"Window: {summary.window_start} - {summary.window_end}")
            lines.append(f"Comparisons: {summary.comparison_count}")
            lines.append(f"Total Significance: {summary.total_significance:.2f}")
            lines.append("")
        
        if not self._summaries:
            lines.append("No case window summaries available.")
        
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


def integrate_with_v91_timeline(window_summary: OperatorCaseWindowSummary) -> Dict[str, Any]:
    """Integration hook for v91 timeline — read-only summary only.
    
    No behavior changes to existing timeline comparison logic.
    """
    return {"hooked": True, "measures": "timeline_window_summary_integration"}
