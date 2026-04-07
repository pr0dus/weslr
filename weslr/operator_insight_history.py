# operator_insight_history.py - WESLR v86: Operator Insight History / Comparative Significance Layer
# Read-only operator-facing layer that compares insight summaries over time and
# highlights which insight shifts are actually meaningful.
# No optimization, no remediation, no orchestration, no backend/service/UI.
# No TIA/C#, no storage framework expansion, no analytics engine beyond comparison scope.

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .operator_recovery_insight import (
    InsightSummary,
    OperatorRecoveryInsight,
    RecoveryInsight,
    TrendShift,
)


# ============================================================================
# INSIGHT HISTORY DATA MODELS
# ============================================================================


@dataclass
class InsightHistoryRecord:
    """Single insight history record for tracking over time.
    
    Contains:
    - History metadata (timestamp, insight summary reference)
    - Insight summary content
    - Correlation IDs for linking to recovery context
    """
    
    history_id: str
    timestamp: str
    insight_summary_id: str
    correlation_ids: Dict[str, str]
    
    # Insight summary content
    insight_count: int
    insight_types: Dict[str, int]
    shift_count: int
    shift_types: Dict[str, int]
    convergence_patterns: Dict[str, int]
    divergence_patterns: Dict[str, int]
    
    # Historical context
    sequence: int
    window_start: str
    window_end: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "history_id": self.history_id,
            "timestamp": self.timestamp,
            "insight_summary_id": self.insight_summary_id,
            "correlation_ids": self.correlation_ids,
            "insight_count": self.insight_count,
            "insight_types": self.insight_types,
            "shift_count": self.shift_count,
            "shift_types": self.shift_types,
            "convergence_patterns": self.convergence_patterns,
            "divergence_patterns": self.divergence_patterns,
            "sequence": self.sequence,
            "window_start": self.window_start,
            "window_end": self.window_end,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class ComparativeSignificance:
    """Comparative significance record for insight comparisons.
    
    Contains:
    - Comparison metadata (timestamp, comparison IDs)
    - Comparison content (shared fields, differences, significance shift)
    - Interpretation (operator-facing explanation)
    """
    
    comparison_id: str
    timestamp: str
    comparison_type: str  # "insight_summary", "significance", "confidence", "safe_action"
    
    # Comparison content
    shared_fields: Dict[str, Any] = field(default_factory=dict)
    differences: Dict[str, Any] = field(default_factory=dict)
    
    # Significance shift assessment
    significance_shift: Optional[str] = None  # "increasing", "decreasing", "stable", "variable"
    meaningful_shift: bool = False
    meaningful_shift_reason: str = ""
    
    # Pattern identifiers
    summary1_id: str = ""
    summary2_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "comparison_id": self.comparison_id,
            "timestamp": self.timestamp,
            "comparison_type": self.comparison_type,
            "summary1_id": self.summary1_id,
            "summary2_id": self.summary2_id,
            "significance_shift": self.significance_shift,
            "meaningful_shift": self.meaningful_shift,
            "meaningful_shift_reason": self.meaningful_shift_reason,
            "shared_fields": self.shared_fields,
            "differences": self.differences,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class SignificanceTrend:
    """Significance trend over time.
    
    Contains:
    - Trend metadata (type, direction, magnitude)
    - Interpretation (operator-facing explanation)
    - Heuristic significance (not certainty)
    """
    
    trend_id: str
    timestamp: str
    trend_type: str  # "significance", "confidence", "safe_action_convergence"
    direction: str  # "increasing", "decreasing", "stable", "variable"
    magnitude: str  # "minor", "moderate", "significant"
    
    # Interpretation
    interpretation: str  # What this means for operators
    heuristic_significance: str  # "low", "medium", "high" (heuristic, not certainty)
    heuristic_reason: str  # Why this significance
    
    # Pattern reference
    reference_summary_id: str
    
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
            "reference_summary_id": self.reference_summary_id,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class ComparativeSummary:
    """Operator-readable comparative significance summary.
    
    Contains:
    - Summary metadata
    - Comparative data distribution
    - Meaningful shift indicators
    - Operator guidance
    """
    
    summary_id: str
    timestamp: str
    total_comparisons: int
    comparison_type_distribution: Dict[str, int]
    meaningful_shifts: List[Dict[str, Any]]
    significance_trends: List[Dict[str, Any]]
    operator_readable: str  # Multi-line narrative
    machine_readable: str  # JSON string
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "summary_id": self.summary_id,
            "timestamp": self.timestamp,
            "total_comparisons": self.total_comparisons,
            "comparison_type_distribution": self.comparison_type_distribution,
            "meaningful_shifts": self.meaningful_shifts,
            "significance_trends": self.significance_trends,
            "operator_readable": self.operator_readable,
            "machine_readable": self.machine_readable,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# OPERATOR INSIGHT HISTORY LAYER
# ============================================================================


class InsightHistoryStore:
    """Lightweight store for insight history over time.
    
    Additive only - no new persistence subsystem or storage framework expansion.
    
    Provides:
    - Store and retrieve insight summaries over time
    - Track sequence and time windows for analysis
    - Link to correlation IDs for recovery context
    """
    
    def __init__(self):
        """Initialize insight history store."""
        self._history: List[InsightHistoryRecord] = []
        self._sequence_counter: int = 0
    
    def add_insight_summary(
        self,
        summary: InsightSummary,
        correlation_ids: Optional[Dict[str, str]] = None,
    ) -> InsightHistoryRecord:
        """Add an insight summary to history.
        
        Args:
            summary: InsightSummary from v85
            correlation_ids: Optional correlation IDs for context
        
        Returns:
            InsightHistoryRecord with sequence tracking
        """
        self._sequence_counter += 1
        window = self._get_time_window()
        
        record = InsightHistoryRecord(
            history_id=f"insight_history_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            insight_summary_id=summary.summary_id,
            correlation_ids=correlation_ids or {},
            insight_count=summary.total_insights,
            insight_types=summary.insight_type_distribution,
            shift_count=len(summary.trend_shifts),
            shift_types=self._count_shift_types(summary),
            convergence_patterns=summary.convergence_patterns,
            divergence_patterns=summary.divergence_patterns,
            sequence=self._sequence_counter,
            window_start=window[0],
            window_end=window[1],
        )
        
        self._history.append(record)
        return record
    
    def _get_time_window(self) -> tuple[str, str]:
        """Get current time window for insight history.
        
        Returns (window_start, window_end) tuple.
        """
        now = datetime.now(timezone.utc)
        window_start = now.replace(minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")
        window_end = now.replace(minute=59, second=59, microsecond=999999).isoformat().replace("+00:00", "Z")
        return window_start, window_end
    
    def _count_shift_types(self, summary: InsightSummary) -> Dict[str, int]:
        """Count trend shift types from summary."""
        counts: Dict[str, int] = {}
        for shift in summary.trend_shifts:
            st = shift.get("trend_type", "unknown")
            counts[st] = counts.get(st, 0) + 1
        return counts
    
    def get_history(
        self,
        time_window: Optional[str] = None,
        correlation_type: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> List[InsightHistoryRecord]:
        """Get insight history with optional filters.
        
        Args:
            time_window: Filter by time window (future: implement time-based filtering)
            correlation_type: Filter by correlation type
            correlation_id: Filter by correlation ID value
        
        Returns:
            List of InsightHistoryRecord matching filters
        """
        results = self._history
        
        if correlation_type and correlation_id:
            results = [
                r for r in results
                if r.correlation_ids.get(correlation_type) == correlation_id
            ]
        
        return results
    
    def get_latest_history(self, count: int = 1) -> List[InsightHistoryRecord]:
        """Get the most recent insight history records.
        
        Args:
            count: Number of records to return
        
        Returns:
            List of most recent InsightHistoryRecord(s)
        """
        return self._history[-count:] if self._history else []
    
    def get_history_by_insight_summary_id(
        self,
        summary_id: str,
    ) -> Optional[InsightHistoryRecord]:
        """Get history record by insight summary ID.
        
        Args:
            summary_id: The insight summary ID to find
        
        Returns:
            InsightHistoryRecord or None if not found
        """
        for record in self._history:
            if record.insight_summary_id == summary_id:
                return record
        return None


class OperatorInsightHistory:
    """Insight history layer for comparative significance analysis.
    
    Provides read-only comparative analysis:
    - Compare insight summaries across time
    - Compare significance shifts across incidents
    - Compare confidence-guidance shifts over time
    - Compare safe-next-action convergence/divergence at the insight level
    - Operator-readable comparative significance summary
    - Machine-readable comparative export
    
    Correlation support:
    - flow_id
    - request_id
    - handshake_id
    - deadline_id
    
    Read-only analysis only — no behavior changes.
    """
    
    def __init__(self):
        """Initialize operator insight history layer."""
        self._store = InsightHistoryStore()
        self._comparisons: List[ComparativeSignificance] = []
        self._significance_trends: List[SignificanceTrend] = []
    
    def compare_significance(
        self,
        summary1: InsightSummary,
        summary2: InsightSummary,
        summary1_id: str = "previous",
        summary2_id: str = "current",
    ) -> ComparativeSignificance:
        """Compare significance between two insight summaries.
        
        Args:
            summary1: First insight summary
            summary2: Second insight summary
            summary1_id: Identifier for first summary
            summary2_id: Identifier for second summary
        
        Returns:
            ComparativeSignificance with observed differences
        """
        comparison = ComparativeSignificance(
            comparison_id=f"comp_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            comparison_type="insight_summary",
            summary1_id=summary1_id,
            summary2_id=summary2_id,
            shared_fields={
                "total_insights": summary1.total_insights,
                "timestamp_window": "current",
            },
            differences={
                "insight_count": (
                    summary1.total_insights,
                    summary2.total_insights,
                ),
                "insight_type_distribution": (
                    summary1.insight_type_distribution,
                    summary2.insight_type_distribution,
                ),
            },
            significance_shift=self._compare_insight_significance(
                summary1.total_insights,
                summary2.total_insights,
            ),
            meaningful_shift=self._assess_meaningful_shift(
                summary1.total_insights,
                summary2.total_insights,
            ),
            meaningful_shift_reason=self._get_meaningful_shift_reason(
                summary1.total_insights,
                summary2.total_insights,
            ),
        )
        
        self._comparisons.append(comparison)
        return comparison
    
    def _compare_insight_significance(
        self,
        count1: int,
        count2: int,
    ) -> Optional[str]:
        """Compare insight counts to determine significance shift."""
        if count1 == count2:
            return "stable"
        elif count2 > count1:
            if count2 > count1 * 1.5:
                return "increasing"
            return "increasing"
        else:
            if count2 < count1 * 0.5:
                return "decreasing"
            return "decreasing"
    
    def _assess_meaningful_shift(
        self,
        count1: int,
        count2: int,
    ) -> bool:
        """Assess if significance shift is meaningful (heuristic)."""
        if count1 == 0 and count2 > 0:
            return True
        if count1 > 0 and count2 == 0:
            return True
        if count2 > count1 * 1.5 or count2 < count1 * 0.5:
            return True
        return False
    
    def _get_meaningful_shift_reason(
        self,
        count1: int,
        count2: int,
    ) -> str:
        """Get reason for meaningful shift."""
        if count1 == 0 and count2 > 0:
            return "New insights detected where none existed before."
        elif count1 > 0 and count2 == 0:
            return "Insights dropped significantly."
        elif count2 > count1 * 1.5:
            return f"Significant increase: {count1} -> {count2} insights."
        elif count2 < count1 * 0.5:
            return f"Significant decrease: {count1} -> {count2} insights."
        else:
            return "Minor fluctuation within normal range."
    
    def analyze_significance_trends(
        self,
        history: List[InsightHistoryRecord],
    ) -> List[SignificanceTrend]:
        """Analyze significance trends across history.
        
        Args:
            history: List of InsightHistoryRecord
        
        Returns:
            List of SignificanceTrend records
        """
        trends = []
        
        if len(history) < 2:
            return trends
        
        # Analyze trend in insight counts
        counts = [h.insight_count for h in history]
        if len(set(counts)) > 1:
            direction = self._determine_trend_direction(counts)
            magnitude = self._assess_magnitude(counts)
            
            trend = SignificanceTrend(
                trend_id=f"trend_{uuid.uuid4().hex[:12]}",
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                trend_type="insight_count",
                direction=direction,
                magnitude=magnitude,
                interpretation=self._get_trend_interpretation(
                    "insight_count",
                    direction,
                    magnitude,
                ),
                heuristic_significance=self._assess_heuristic_significance(magnitude, direction),
                heuristic_reason=self._get_heuristic_reason("insight_count", direction, magnitude),
                reference_summary_id=history[-1].insight_summary_id,
            )
            trends.append(trend)
            self._significance_trends.append(trend)
        
        # Analyze trend in convergence patterns
        convergence_counts = [len(h.convergence_patterns) for h in history]
        if len(set(convergence_counts)) > 1:
            direction = self._determine_trend_direction(convergence_counts)
            magnitude = self._assess_magnitude(convergence_counts)
            
            if magnitude in ["moderate", "significant"]:
                trend = SignificanceTrend(
                    trend_id=f"trend_{uuid.uuid4().hex[:12]}",
                    timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    trend_type="safe_action_convergence",
                    direction=direction,
                    magnitude=magnitude,
                    interpretation=self._get_trend_interpretation(
                        "safe_action_convergence",
                        direction,
                        magnitude,
                    ),
                    heuristic_significance=self._assess_heuristic_significance(magnitude, direction),
                    heuristic_reason=self._get_heuristic_reason(
                        "safe_action_convergence",
                        direction,
                        magnitude,
                    ),
                    reference_summary_id=history[-1].insight_summary_id,
                )
                trends.append(trend)
                self._significance_trends.append(trend)
        
        return trends
    
    def _determine_trend_direction(self, values: List[int]) -> str:
        """Determine trend direction from values."""
        if len(values) < 2:
            return "stable"
        
        first_half = sum(values[:len(values)//2]) / (len(values)//2 or 1)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2 or 1)
        
        if abs(first_half - second_half) < first_half * 0.1:
            return "stable"
        elif second_half > first_half:
            return "increasing"
        else:
            return "decreasing"
    
    def _assess_magnitude(self, values: List[int]) -> str:
        """Assess magnitude of change."""
        if len(values) < 2:
            return "minor"
        
        max_val = max(values)
        min_val = min(values)
        range_val = max_val - min_val
        avg_val = sum(values) / len(values)
        
        if range_val < 2:
            return "minor"
        elif range_val < 4:
            return "moderate"
        else:
            return "significant"
    
    def _assess_heuristic_significance(self, magnitude: str, direction: str) -> str:
        """Assess heuristic significance (not certainty)."""
        if magnitude == "significant" or direction == "decreasing":
            return "high"
        elif magnitude == "moderate":
            return "medium"
        else:
            return "low"
    
    def _get_heuristic_reason(
        self,
        trend_type: str,
        direction: str,
        magnitude: str,
    ) -> str:
        """Get heuristic significance reason (not certainty)."""
        if magnitude == "significant":
            return f"Heuristic significance assessment for {trend_type} trend (not certainty)."
        else:
            return f"Standard heuristic significance (not certainty)."
    
    def _get_trend_interpretation(
        self,
        trend_type: str,
        direction: str,
        magnitude: str,
    ) -> str:
        """Get trend interpretation for operators."""
        interpretations = {
            ("insight_count", "increasing", "moderate"): "Insight count increasing - more patterns being analyzed.",
            ("insight_count", "decreasing", "moderate"): "Insight count decreasing - fewer patterns detected.",
            ("insight_count", "stable", "minor"): "Insight count stable - consistent analysis volume.",
            ("safe_action_convergence", "increasing", "moderate"): "Convergence increasing - more consistent safe-next-actions.",
            ("safe_action_convergence", "decreasing", "moderate"): "Convergence decreasing - more diverse safe-next-actions.",
        }
        key = (trend_type, direction, magnitude)
        return interpretations.get(key, f"Standard {direction} trend in {trend_type}.")
    
    def detect_significant_shifts(
        self,
        history: List[InsightHistoryRecord],
    ) -> List[ComparativeSignificance]:
        """Detect significant shifts in insight history.
        
        Args:
            history: List of InsightHistoryRecord
        
        Returns:
            List of ComparativeSignificance with meaningful shifts
        """
        significant = []
        
        if len(history) < 2:
            return significant
        
        # Compare consecutive records
        for i in range(len(history) - 1):
            comparison = self.compare_significance(
                InsightSummary(
                    summary_id=history[i].insight_summary_id,
                    timestamp=history[i].timestamp,
                    total_insights=history[i].insight_count,
                    insight_type_distribution=history[i].insight_types,
                    trend_shifts=[],  # Simulated
                    convergence_patterns=history[i].convergence_patterns,
                    divergence_patterns=history[i].divergence_patterns,
                    repeated_pattern_significance={},  # Required by v85
                    operator_readable="",
                    machine_readable="",
                ),
                InsightSummary(
                    summary_id=history[i + 1].insight_summary_id,
                    timestamp=history[i + 1].timestamp,
                    total_insights=history[i + 1].insight_count,
                    insight_type_distribution=history[i + 1].insight_types,
                    trend_shifts=[],  # Simulated
                    convergence_patterns=history[i + 1].convergence_patterns,
                    divergence_patterns=history[i + 1].divergence_patterns,
                    repeated_pattern_significance={},  # Required by v85
                    operator_readable="",
                    machine_readable="",
                ),
                summary1_id=history[i].insight_summary_id,
                summary2_id=history[i + 1].insight_summary_id,
            )
            
            if comparison.meaningful_shift:
                significant.append(comparison)
        
        return significant
    
    def get_comparative_summary(self) -> ComparativeSummary:
        """Generate operator-readable comparative significance summary.
        
        Includes:
        - Comparison type distribution
        - Meaningful shifts
        - Significance trends
        - Operator guidance
        """
        if not self._comparisons:
            return ComparativeSummary(
                summary_id=f"summary_{uuid.uuid4().hex[:12]}",
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                total_comparisons=0,
                comparison_type_distribution={},
                meaningful_shifts=[],
                significance_trends=[],
                operator_readable="No comparative significance data available. Analyze insight history first.",
                machine_readable=json.dumps({"error": "No comparative significance data"}, indent=2),
            )
        
        # Count comparison types
        comparison_type_dist: Dict[str, int] = {}
        for comp in self._comparisons:
            ct = comp.comparison_type
            comparison_type_dist[ct] = comparison_type_dist.get(ct, 0) + 1
        
        # Filter meaningful shifts
        meaningful_shifts = [
            c.to_dict() for c in self._comparisons
            if c.meaningful_shift
        ]
        
        # Convert significance trends
        significance_trends = [t.to_dict() for t in self._significance_trends]
        
        # Generate operator-readable summary
        lines = [
            "=" * 70,
            "OPERATOR INSIGHT HISTORY COMPARATIVE SIGNIFICANCE SUMMARY",
            "=" * 70,
            f"Summary ID: {uuid.uuid4().hex[:12]}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
            f"Total Comparisons: {len(self._comparisons)}",
            f"Significance Trends: {len(self._significance_trends)}",
            "",
            "-" * 70,
            "COMPARISON TYPE DISTRIBUTION",
            "-" * 70,
        ]
        
        for ct, count in sorted(comparison_type_dist.items()):
            lines.append(f"  {ct}: {count}")
        
        lines.extend([
            "",
            "-" * 70,
            "MEANINGFUL SHIFTS",
            "-" * 70,
        ])
        
        for shift in meaningful_shifts:
            lines.append(
                f"  {shift['summary1_id']} -> {shift['summary2_id']}: "
                f"{shift['significance_shift']} (meaningful)"
            )
        
        lines.extend([
            "",
            "-" * 70,
            "SIGNIFICANCE TRENDS",
            "-" * 70,
        ])
        
        for trend in significance_trends:
            lines.append(
                f"  {trend['trend_type']}: {trend['direction']} ({trend['magnitude']}) - "
                f"Heuristic Significance: {trend['heuristic_significance']}"
            )
        
        lines.extend([
            "",
            "-" * 70,
            "HEURISTIC NOTE",
            "-" * 70,
            "Comparative significance and meaningful-shift detection are heuristics, not certainties.",
            "",
            "Key distinctions:",
            "- Heuristic significance: Assessment of pattern importance",
            "- Guidance: Operator-facing recommendations, not directives",
            "- Shifts: Observations over time, not predictions",
            "",
            "This comparative significance layer provides operator-facing pattern analysis,",
            "not automatic decision-making or remediation.",
            "",
            "=" * 70,
        ])
        
        operator_summary = "\n".join(lines)
        machine_summary = json.dumps({
            "summary_id": uuid.uuid4().hex[:12],
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "total_comparisons": len(self._comparisons),
            "comparison_type_distribution": comparison_type_dist,
            "meaningful_shifts": meaningful_shifts,
            "significance_trends": significance_trends,
            "comparisons": [c.to_dict() for c in self._comparisons],
        }, indent=2)
        
        return ComparativeSummary(
            summary_id=uuid.uuid4().hex[:12],
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            total_comparisons=len(self._comparisons),
            comparison_type_distribution=comparison_type_dist,
            meaningful_shifts=meaningful_shifts,
            significance_trends=significance_trends,
            operator_readable=operator_summary,
            machine_readable=machine_summary,
        )
    
    def export_operator_readable(self) -> str:
        """Export comparative significance summary as operator-readable string."""
        summary = self.get_comparative_summary()
        return summary.operator_readable
    
    def export_machine_readable(self) -> str:
        """Export comparative significance summary as JSON string."""
        summary = self.get_comparative_summary()
        return summary.machine_readable
    
    def export_comparisons_as_json(self) -> str:
        """Export all comparisons as JSON string."""
        return json.dumps([c.to_dict() for c in self._comparisons], indent=2)
    
    def export_significance_trends_as_json(self) -> str:
        """Export all significance trends as JSON string."""
        return json.dumps([t.to_dict() for t in self._significance_trends], indent=2)
    
    def export_meaningful_shifts_as_json(self) -> str:
        """Export meaningful shifts as JSON string."""
        meaningful = [c.to_dict() for c in self._comparisons if c.meaningful_shift]
        return json.dumps(meaningful, indent=2)


# ============================================================================
# INTEGRATION HELPERS (Additive Only)
# ============================================================================


def integrate_with_v85_insights(store: InsightHistoryStore) -> Dict[str, Any]:
    """Integration hook for v85 insights — read-only history only.
    
    No behavior changes to existing insight logic.
    """
    return {"hooked": True, "measures": "insight_history_integration"}


def correlate_with_v78_traces(store: InsightHistoryStore) -> Dict[str, Any]:
    """Correlation hook for v78 traces — read-only history only.
    
    No behavior changes to existing trace logic.
    """
    return {"hooked": True, "measures": "trace_correlation_integration"}
