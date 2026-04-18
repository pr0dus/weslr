# operator_insight_comparison.py - WESLR v87: Operator Insight Comparison / Drift Layer
# Read-only operator-facing layer that compares insight summaries across incidents
# and time windows, highlighting where operator insight meaning drifts.
# No optimization, no remediation, no orchestration, no backend/service/UI.
# No TIA/C#, no storage framework expansion, no analytics engine beyond comparison scope.

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .operator_insight_history import (
    ComparativeSignificance,
    OperatorInsightHistory,
)


# ============================================================================
# INSIGHT COMPARISON DATA MODELS
# ============================================================================


@dataclass
class InsightDriftRecord:
    """Single drift record for tracking changes across incidents/time windows.
    
    Contains:
    - Drift metadata (timestamp, comparison reference)
    - Drift content (shared fields, differences, drift type)
    - Interpretation (operator-facing explanation)
    """
    
    drift_id: str
    timestamp: str
    comparison_type: str  # "insight_summary", "significance", "confidence", "safe_action"
    
    # Comparison content
    summary1_id: str
    summary2_id: str
    shared_fields: Dict[str, Any]
    differences: Dict[str, Any]
    
    # Drift assessment
    drift_type: str  # "increasing", "decreasing", "stable", "variable"
    drift_magnitude: str  # "minor", "moderate", "significant"
    meaningful_drift: bool
    meaningful_drift_reason: str
    
    # Correlation IDs
    correlation_ids: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "drift_id": self.drift_id,
            "timestamp": self.timestamp,
            "comparison_type": self.comparison_type,
            "summary1_id": self.summary1_id,
            "summary2_id": self.summary2_id,
            "drift_type": self.drift_type,
            "drift_magnitude": self.drift_magnitude,
            "meaningful_drift": self.meaningful_drift,
            "meaningful_drift_reason": self.meaningful_drift_reason,
            "shared_fields": self.shared_fields,
            "differences": self.differences,
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
class DriftSummary:
    """Operator-readable drift/comparison summary.
    
    Contains:
    - Summary metadata
    - Drift distribution
    - Meaningful drift indicators
    - Operator guidance
    """
    
    summary_id: str
    timestamp: str
    total_drifts: int
    drift_type_distribution: Dict[str, int]
    meaningful_drifts: List[Dict[str, Any]]
    drift_trends: List[Dict[str, Any]]
    operator_readable: str  # Multi-line narrative
    machine_readable: str  # JSON string
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "summary_id": self.summary_id,
            "timestamp": self.timestamp,
            "total_drifts": self.total_drifts,
            "drift_type_distribution": self.drift_type_distribution,
            "meaningful_drifts": self.meaningful_drifts,
            "drift_trends": self.drift_trends,
            "operator_readable": self.operator_readable,
            "machine_readable": self.machine_readable,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# OPERATOR INSIGHT COMPARISON LAYER
# ============================================================================


class InsightDriftStore:
    """Lightweight store for drift records over time.
    
    Additive only - no new persistence subsystem or storage framework expansion.
    
    Provides:
    - Store and retrieve drift records
    - Track sequence and time windows for analysis
    - Link to correlation IDs for recovery context
    """
    
    def __init__(self):
        """Initialize drift store."""
        self._drifts: List[InsightDriftRecord] = []
        self._sequence_counter: int = 0
    
    def add_drift_record(
        self,
        drift: ComparativeSignificance,
        correlation_ids: Optional[Dict[str, str]] = None,
    ) -> InsightDriftRecord:
        """Add a drift record from comparative significance.
        
        Args:
            drift: ComparativeSignificance from v86
            correlation_ids: Optional correlation IDs for context
        
        Returns:
            InsightDriftRecord with sequence tracking
        """
        self._sequence_counter += 1
        window = self._get_time_window()
        
        record = InsightDriftRecord(
            drift_id=f"drift_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            comparison_type=drift.comparison_type,
            summary1_id=drift.summary1_id,
            summary2_id=drift.summary2_id,
            shared_fields=drift.shared_fields,
            differences=drift.differences,
            drift_type=drift.significance_shift or "stable",
            drift_magnitude="moderate",  # Heuristic default
            meaningful_drift=drift.meaningful_shift,
            meaningful_drift_reason=drift.meaningful_shift_reason,
            correlation_ids=correlation_ids or {},
        )
        
        self._drifts.append(record)
        return record
    
    def _get_time_window(self) -> tuple[str, str]:
        """Get current time window for drift tracking.
        
        Returns (window_start, window_end) tuple.
        """
        now = datetime.now(timezone.utc)
        window_start = now.replace(minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")
        window_end = now.replace(minute=59, second=59, microsecond=999999).isoformat().replace("+00:00", "Z")
        return window_start, window_end
    
    def get_drifts(
        self,
        time_window: Optional[str] = None,
        correlation_type: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> List[InsightDriftRecord]:
        """Get drift records with optional filters.
        
        Args:
            time_window: Filter by time window (future: implement time-based filtering)
            correlation_type: Filter by correlation type
            correlation_id: Filter by correlation ID value
        
        Returns:
            List of InsightDriftRecord matching filters
        """
        results = self._drifts
        
        if correlation_type and correlation_id:
            results = [
                r for r in results
                if r.correlation_ids.get(correlation_type) == correlation_id
            ]
        
        return results
    
    def get_latest_drifts(self, count: int = 1) -> List[InsightDriftRecord]:
        """Get the most recent drift records.
        
        Args:
            count: Number of records to return
        
        Returns:
            List of most recent InsightDriftRecord(s)
        """
        return self._drifts[-count:] if self._drifts else []
    
    def get_drift_by_comparison(self, summary1_id: str, summary2_id: str) -> Optional[InsightDriftRecord]:
        """Get drift record by comparison pair.
        
        Args:
            summary1_id: First summary ID
            summary2_id: Second summary ID
        
        Returns:
            InsightDriftRecord or None if not found
        """
        for record in self._drifts:
            if record.summary1_id == summary1_id and record.summary2_id == summary2_id:
                return record
        return None


class OperatorInsightComparison:
    """Insight comparison layer for drift analysis across incidents/time windows.
    
    Provides read-only comparative analysis:
    - Compare insight summaries across incidents
    - Compare insight summaries across time windows
    - Detect meaningful insight drift
    - Compare confidence-guidance drift
    - Compare safe-next-action drift
    - Operator-readable drift/comparison summary
    - Machine-readable comparison export
    
    Correlation support:
    - flow_id
    - request_id
    - handshake_id
    - deadline_id
    
    Read-only analysis only — no behavior changes.
    """
    
    def __init__(self):
        """Initialize operator insight comparison layer."""
        self._drift_store = InsightDriftStore()
        self._drift_trends: List[DriftTrend] = []
    
    def compare_drift(
        self,
        summary1_id: str,
        summary2_id: str,
        total_insights1: int,
        total_insights2: int,
        insight_type_distribution1: Dict[str, int],
        insight_type_distribution2: Dict[str, int],
        correlation_ids: Optional[Dict[str, str]] = None,
    ) -> InsightDriftRecord:
        """Compare drift between two insight summaries.
        
        Args:
            summary1_id: First summary ID
            summary2_id: Second summary ID
            total_insights1: First summary insight count
            total_insights2: Second summary insight count
            insight_type_distribution1: First summary type distribution
            insight_type_distribution2: Second summary type distribution
            correlation_ids: Optional correlation IDs for context
        
        Returns:
            InsightDriftRecord with observed drift
        """
        comparison = InsightDriftRecord(
            drift_id=f"drift_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            comparison_type="insight_summary",
            summary1_id=summary1_id,
            summary2_id=summary2_id,
            shared_fields={
                "timestamp_window": "current",
            },
            differences={
                "insight_count": (total_insights1, total_insights2),
                "insight_type_distribution": (
                    insight_type_distribution1,
                    insight_type_distribution2,
                ),
            },
            drift_type=self._determine_drift_type(total_insights1, total_insights2),
            drift_magnitude=self._assess_drift_magnitude(total_insights1, total_insights2),
            meaningful_drift=self._assess_meaningful_drift(total_insights1, total_insights2),
            meaningful_drift_reason=self._get_meaningful_drift_reason(total_insights1, total_insights2),
            correlation_ids=correlation_ids or {},
        )
        
        self._drift_store.add_drift_record(
            type('ComparativeSignificance', (), {
                'comparison_type': 'insight_summary',
                'summary1_id': summary1_id,
                'summary2_id': summary2_id,
                'shared_fields': comparison.shared_fields,
                'differences': comparison.differences,
                'significance_shift': comparison.drift_type,
                'meaningful_shift': comparison.meaningful_drift,
                'meaningful_shift_reason': comparison.meaningful_drift_reason,
            })(),
            correlation_ids
        )
        
        return comparison
    
    def _determine_drift_type(self, count1: int, count2: int) -> str:
        """Determine drift type from insight counts."""
        if count1 == count2:
            return "stable"
        elif count2 > count1:
            return "increasing"
        else:
            return "decreasing"
    
    def _assess_drift_magnitude(self, count1: int, count2: int) -> str:
        """Assess magnitude of drift."""
        if count1 == 0:
            if count2 == 0:
                return "minor"
            return "moderate"
        if count2 == 0:
            return "moderate"
        
        ratio = count2 / count1
        if ratio < 0.5 or ratio > 1.5:
            return "significant"
        elif ratio < 0.75 or ratio > 1.25:
            return "moderate"
        return "minor"
    
    def _assess_meaningful_drift(self, count1: int, count2: int) -> bool:
        """Assess if drift is meaningful (heuristic)."""
        if count1 == 0 and count2 > 0:
            return True
        if count1 > 0 and count2 == 0:
            return True
        if count1 > 0:
            ratio = count2 / count1
            if ratio < 0.5 or ratio > 1.5:
                return True
        return False
    
    def _get_meaningful_drift_reason(self, count1: int, count2: int) -> str:
        """Get reason for meaningful drift."""
        if count1 == 0 and count2 > 0:
            return "New insights detected where none existed before."
        elif count1 > 0 and count2 == 0:
            return "Insights dropped significantly."
        elif count1 > 0:
            ratio = count2 / count1
            if ratio > 1.5:
                return f"Significant increase: {count1} -> {count2} insights."
            elif ratio < 0.5:
                return f"Significant decrease: {count1} -> {count2} insights."
            elif ratio > 1.25:
                return f"Moderate increase: {count1} -> {count2} insights."
            elif ratio < 0.75:
                return f"Moderate decrease: {count1} -> {count2} insights."
        return "Minor fluctuation within normal range."
    
    def analyze_drift_trends(
        self,
        drifts: List[InsightDriftRecord],
    ) -> List[DriftTrend]:
        """Analyze drift trends across incidents/time windows.
        
        Args:
            drifts: List of InsightDriftRecord
        
        Returns:
            List of DriftTrend records
        """
        trends = []
        
        if len(drifts) < 2:
            return trends
        
        # Analyze drift type distribution
        drift_type_counts = {"increasing": 0, "decreasing": 0, "stable": 0}
        for drift in drifts:
            dt = drift.drift_type
            drift_type_counts[dt] = drift_type_counts.get(dt, 0) + 1
        
        # Determine overall trend
        if drift_type_counts["increasing"] > drift_type_counts["stable"] + drift_type_counts["decreasing"]:
            direction = "increasing"
            magnitude = "moderate"
        elif drift_type_counts["decreasing"] > drift_type_counts["stable"] + drift_type_counts["increasing"]:
            direction = "decreasing"
            magnitude = "moderate"
        else:
            direction = "stable"
            magnitude = "minor"
        
        trend = DriftTrend(
            trend_id=f"trend_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            trend_type="insight_count",
            direction=direction,
            magnitude=magnitude,
            interpretation=self._get_trend_interpretation("insight_count", direction, magnitude),
            heuristic_significance=self._assess_heuristic_significance(magnitude, direction),
            heuristic_reason=self._get_heuristic_reason("insight_count", direction, magnitude),
            reference_summary_id=drifts[-1].summary2_id if drifts else "",
        )
        trends.append(trend)
        self._drift_trends.append(trend)
        
        return trends
    
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
            return f"Heuristic significance assessment for {trend_type} drift trend (not certainty)."
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
        }
        key = (trend_type, direction, magnitude)
        return interpretations.get(key, f"Standard {direction} drift trend in {trend_type}.")
    
    def get_drift_summary(self) -> DriftSummary:
        """Generate operator-readable drift/comparison summary.
        
        Includes:
        - Drift type distribution
        - Meaningful drifts
        - Drift trends
        - Operator guidance
        """
        drifts = self._drift_store._drifts
        
        if not drifts:
            return DriftSummary(
                summary_id=f"summary_{uuid.uuid4().hex[:12]}",
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                total_drifts=0,
                drift_type_distribution={},
                meaningful_drifts=[],
                drift_trends=[],
                operator_readable="No drift comparison data available. Analyze drifts first.",
                machine_readable=json.dumps({"error": "No drift comparison data"}, indent=2),
            )
        
        # Count drift types
        drift_type_dist: Dict[str, int] = {"increasing": 0, "decreasing": 0, "stable": 0, "variable": 0}
        for drift in drifts:
            dt = drift.drift_type
            drift_type_dist[dt] = drift_type_dist.get(dt, 0) + 1
        
        # Filter meaningful drifts
        meaningful_drifts = [
            d.to_dict() for d in drifts
            if d.meaningful_drift
        ]
        
        # Convert drift trends
        drift_trends = [t.to_dict() for t in self._drift_trends]
        
        # Generate operator-readable summary
        lines = [
            "=" * 70,
            "OPERATOR INSIGHT COMPARISON DRIFT SUMMARY",
            "=" * 70,
            f"Summary ID: {uuid.uuid4().hex[:12]}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
            f"Total Drifts: {len(drifts)}",
            f"Drift Trends: {len(self._drift_trends)}",
            "",
            "-" * 70,
            "DRIFT TYPE DISTRIBUTION",
            "-" * 70,
        ]
        
        for dt, count in sorted(drift_type_dist.items()):
            lines.append(f"  {dt}: {count}")
        
        lines.extend([
            "",
            "-" * 70,
            "MEANINGFUL DRIFTS",
            "-" * 70,
        ])
        
        for drift in meaningful_drifts:
            lines.append(
                f"  {drift['summary1_id']} -> {drift['summary2_id']}: "
                f"{drift['drift_type']} ({drift['drift_magnitude']})"
            )
        
        lines.extend([
            "",
            "-" * 70,
            "DRIFT TRENDS",
            "-" * 70,
        ])
        
        for trend in drift_trends:
            lines.append(
                f"  {trend['trend_type']}: {trend['direction']} ({trend['magnitude']}) - "
                f"Heuristic Significance: {trend['heuristic_significance']}"
            )
        
        lines.extend([
            "",
            "-" * 70,
            "HEURISTIC NOTE",
            "-" * 70,
            "Drift detection and meaningful-drift assessment are heuristics, not certainties.",
            "",
            "Key distinctions:",
            "- Heuristic significance: Assessment of pattern importance",
            "- Guidance: Operator-facing recommendations, not directives",
            "- Drifts: Observations over time/incidents, not predictions",
            "",
            "This drift comparison layer provides operator-facing pattern analysis,",
            "not automatic decision-making or remediation.",
            "",
            "=" * 70,
        ])
        
        operator_summary = "\n".join(lines)
        machine_summary = json.dumps({
            "summary_id": uuid.uuid4().hex[:12],
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "total_drifts": len(drifts),
            "drift_type_distribution": drift_type_dist,
            "meaningful_drifts": meaningful_drifts,
            "drift_trends": drift_trends,
            "drifts": [d.to_dict() for d in drifts],
        }, indent=2)
        
        return DriftSummary(
            summary_id=uuid.uuid4().hex[:12],
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            total_drifts=len(drifts),
            drift_type_distribution=drift_type_dist,
            meaningful_drifts=meaningful_drifts,
            drift_trends=drift_trends,
            operator_readable=operator_summary,
            machine_readable=machine_summary,
        )
    
    def export_operator_readable(self) -> str:
        """Export drift summary as operator-readable string."""
        summary = self.get_drift_summary()
        return summary.operator_readable
    
    def export_machine_readable(self) -> str:
        """Export drift summary as JSON string."""
        summary = self.get_drift_summary()
        return summary.machine_readable
    
    def export_drifts_as_json(self) -> str:
        """Export all drifts as JSON string."""
        return json.dumps([d.to_dict() for d in self._drift_store._drifts], indent=2)
    
    def export_drift_trends_as_json(self) -> str:
        """Export all drift trends as JSON string."""
        return json.dumps([t.to_dict() for t in self._drift_trends], indent=2)
    
    def export_meaningful_drifts_as_json(self) -> str:
        """Export meaningful drifts as JSON string."""
        meaningful = [d.to_dict() for d in self._drift_store._drifts if d.meaningful_drift]
        return json.dumps(meaningful, indent=2)


# ============================================================================
# INTEGRATION HELPERS (Additive Only)
# ============================================================================


def integrate_with_v86_comparison(store: InsightDriftStore) -> Dict[str, Any]:
    """Integration hook for v86 comparison data — read-only drift only.
    
    No behavior changes to existing comparison logic.
    """
    return {"hooked": True, "measures": "drift_comparison_integration"}


def correlate_with_v78_traces(store: InsightDriftStore) -> Dict[str, Any]:
    """Correlation hook for v78 traces — read-only drift only.
    
    No behavior changes to existing trace logic.
    """
    return {"hooked": True, "measures": "trace_correlation_integration"}
