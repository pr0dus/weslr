# operator_insight_timeline.py - WESLR v88: Operator Insight Timeline / Escalation Context Layer
# Read-only operator-facing layer that sequences insight shifts over time and shows
# escalation context around those changes.
# No optimization, no remediation, no orchestration, no backend/service/UI.
# No TIA/C#, no storage framework expansion, no analytics engine beyond timeline scope.

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .operator_recovery_insight import (
    InsightSummary,
    RecoveryInsight,
)
from .operator_insight_history import (
    ComparativeSignificance,
    InsightHistoryRecord,
)


# ============================================================================
# INSIGHT TIMELINE DATA MODELS
# ============================================================================


@dataclass
class InsightTimelineEntry:
    """Single insight change point in timeline.
    
    Contains:
    - Timeline metadata (timestamp, entry ID)
    - Insight context (insight ID, type, correlation IDs)
    - Change data (before/after values, deltas)
    - Escalation context (severity level, rationale)
    """
    
    entry_id: str
    timestamp: str
    insight_id: str
    drift_type: str  # "insight_count", "significance", "confidence_guidance", "safe_next_action"
    
    # Change data
    before_value: Any
    after_value: Any
    significance_delta: float
    confidence_delta: float
    
    # Escalation context (heuristic, not certainty)
    escalation_level: str  # "normal", "attention", "urgent"
    escalation_reason: str
    
    # Correlation IDs
    correlation_ids: Dict[str, str]
    
    # Optional fields (must come last for dataclass)
    safe_action_shift: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "insight_id": self.insight_id,
            "drift_type": self.drift_type,
            "before_value": self.before_value,
            "after_value": self.after_value,
            "significance_delta": self.significance_delta,
            "confidence_delta": self.confidence_delta,
            "safe_action_shift": self.safe_action_shift,
            "escalation_level": self.escalation_level,
            "escalation_reason": self.escalation_reason,
            "correlation_ids": self.correlation_ids,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class TimelineSummary:
    """Operator-readable + machine-readable timeline summary.
    
    Contains:
    - Summary metadata (time range, change counts)
    - Escalation summary (event counts)
    - Operator narrative
    - Machine export JSON
    """
    
    summary_id: str
    timestamp: str
    time_range_start: str
    time_range_end: str
    total_changes: int
    escalation_events: int
    drift_type_distribution: Dict[str, int]
    
    # Export content
    operator_readable: str
    machine_readable: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "summary_id": self.summary_id,
            "timestamp": self.timestamp,
            "time_range_start": self.time_range_start,
            "time_range_end": self.time_range_end,
            "total_changes": self.total_changes,
            "escalation_events": self.escalation_events,
            "drift_type_distribution": self.drift_type_distribution,
            "operator_readable": self.operator_readable,
            "machine_readable": self.machine_readable,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# INSIGHT TIMELINE STORE (Lightweight, Non-Persistent)
# ============================================================================


class InsightTimelineStore:
    """Lightweight store for insight timeline entries.
    
    Additive only - no new persistence subsystem or storage framework expansion.
    Non-persistent - stores entries in memory only.
    
    Provides:
    - Store and retrieve timeline entries
    - Query by correlation IDs (flow_id, request_id, etc.)
    - Escalation context tracking (normal/attention/urgent)
    - Drift type filtering (significance, confidence, safe_action)
    """
    
    def __init__(self):
        """Initialize timeline store."""
        self._entries: List[InsightTimelineEntry] = []
        self._sequence_counter: int = 0
    
    def add_entry(
        self,
        entry: InsightTimelineEntry,
    ) -> None:
        """Add a timeline entry.
        
        Args:
            entry: InsightTimelineEntry to add
        """
        self._sequence_counter += 1
        self._entries.append(entry)
    
    def get_timeline(self) -> List[InsightTimelineEntry]:
        """Get all timeline entries.
        
        Returns:
            List of all InsightTimelineEntry
        """
        return self._entries
    
    def get_timeline_for_request(
        self,
        request_id: str,
    ) -> List[InsightTimelineEntry]:
        """Get timeline entries for a specific request.
        
        Args:
            request_id: Request ID to filter by
        
        Returns:
            List of InsightTimelineEntry for request
        """
        return [
            e for e in self._entries
            if e.correlation_ids.get("request_id") == request_id
        ]
    
    def get_timeline_for_flow(
        self,
        flow_id: str,
    ) -> List[InsightTimelineEntry]:
        """Get timeline entries for a specific flow.
        
        Args:
            flow_id: Flow ID to filter by
        
        Returns:
            List of InsightTimelineEntry for flow
        """
        return [
            e for e in self._entries
            if e.correlation_ids.get("flow_id") == flow_id
        ]
    
    def get_significance_shifts(self) -> List[InsightTimelineEntry]:
        """Get all significance shift entries.
        
        Returns:
            List of InsightTimelineEntry with drift_type="significance"
        """
        return [
            e for e in self._entries
            if e.drift_type == "significance"
        ]
    
    def get_confidence_shifts(self) -> List[InsightTimelineEntry]:
        """Get all confidence-guidance shift entries.
        
        Returns:
            List of InsightTimelineEntry with drift_type="confidence_guidance"
        """
        return [
            e for e in self._entries
            if e.drift_type == "confidence_guidance"
        ]
    
    def get_safe_action_shifts(self) -> List[InsightTimelineEntry]:
        """Get all safe-next-action shift entries.
        
        Returns:
            List of InsightTimelineEntry with drift_type="safe_next_action"
        """
        return [
            e for e in self._entries
            if e.drift_type == "safe_next_action"
        ]
    
    def get_entries_by_escalation(
        self,
        escalation_level: str,
    ) -> List[InsightTimelineEntry]:
        """Get entries filtered by escalation level.
        
        Args:
            escalation_level: Filter level ("normal", "attention", "urgent")
        
        Returns:
            List of InsightTimelineEntry with matching escalation level
        """
        return [
            e for e in self._entries
            if e.escalation_level == escalation_level
        ]
    
    def get_escalation_context(
        self,
        hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """Get escalation context for recent changes.
        
        Args:
            hours: Time window in hours
        
        Returns:
            List of escalation context dicts
        """
        now = datetime.now(timezone.utc)
        cutoff = now.timestamp() - (hours * 3600)
        
        escalation_context = []
        for entry in self._entries:
            entry_ts = datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
            if entry_ts.timestamp() >= cutoff:
                escalation_context.append({
                    "entry_id": entry.entry_id,
                    "timestamp": entry.timestamp,
                    "drift_type": entry.drift_type,
                    "escalation_level": entry.escalation_level,
                    "escalation_reason": entry.escalation_reason,
                    "correlation_ids": entry.correlation_ids,
                })
        
        return escalation_context
    
    def get_escalation_summary(self) -> Dict[str, int]:
        """Get escalation level distribution.
        
        Returns:
            Dict with counts for each escalation level
        """
        summary = {"normal": 0, "attention": 0, "urgent": 0}
        for entry in self._entries:
            summary[entry.escalation_level] = summary.get(entry.escalation_level, 0) + 1
        return summary
    
    def export_operator_readable(self) -> str:
        """Export timeline as operator-readable string.
        
        Returns:
            Multi-line narrative of timeline events
        """
        if not self._entries:
            return "No insight timeline data available. Record insight changes first."
        
        lines = [
            "=" * 70,
            "OPERATOR INSIGHT TIMELINE SUMMARY",
            "=" * 70,
            f"Total Entries: {len(self._entries)}",
            "",
            "-" * 70,
            "ESCALATION CONTEXT",
            "-" * 70,
        ]
        
        escalation_summary = self.get_escalation_summary()
        for level in ["urgent", "attention", "normal"]:
            if escalation_summary.get(level, 0) > 0:
                lines.append(f"  {level.upper()}: {escalation_summary[level]}")
        
        lines.extend([
            "",
            "-" * 70,
            "DRIFT TYPE DISTRIBUTION",
            "-" * 70,
        ])
        
        drift_types = {}
        for entry in self._entries:
            dt = entry.drift_type
            drift_types[dt] = drift_types.get(dt, 0) + 1
        
        for dt, count in sorted(drift_types.items()):
            lines.append(f"  {dt}: {count}")
        
        lines.extend([
            "",
            "-" * 70,
            "TIMELINE ENTRIES",
            "-" * 70,
        ])
        
        for entry in self._entries[-20:]:  # Last 20 entries
            lines.append(
                f"  [{entry.escalation_level.upper()}] {entry.drift_type}: "
                f"{entry.insight_id} ({entry.timestamp})"
            )
        
        lines.extend([
            "",
            "-" * 70,
            "HEURISTIC NOTE",
            "-" * 70,
            "Escalation levels are heuristic assessments, not certainties.",
            "",
            "Key distinctions:",
            "- Heuristic escalation: Operator guidance, not automatic action",
            "- Normal: Typical pattern changes, standard monitoring",
            "- Attention: Unusual pattern changes, review recommended",
            "- Urgent: Significant pattern changes, operator review required",
            "- Drift detection: Observations over time, not predictions",
            "",
            "This timeline layer provides operator-facing insight tracking,",
            "not automatic decision-making or remediation.",
            "",
            "=" * 70,
        ])
        
        return "\n".join(lines)
    
    def export_machine_readable(self) -> str:
        """Export timeline as JSON string.
        
        Returns:
            JSON string of all timeline entries
        """
        return json.dumps([e.to_dict() for e in self._entries], indent=2)
    
    def export_drift_type_json(self, drift_type: str) -> str:
        """Export entries filtered by drift type.
        
        Args:
            drift_type: Filter by drift type
        
        Returns:
            JSON string of matching entries
        """
        entries = [e for e in self._entries if e.drift_type == drift_type]
        return json.dumps([e.to_dict() for e in entries], indent=2)
    
    def export_timeline_json(self) -> str:
        """Export all entries as JSON string.
        
        Returns:
            JSON string of all timeline entries
        """
        return self.export_machine_readable()


# ============================================================================
# OPERATOR INSIGHT TIMELINE LAYER
# ============================================================================


class OperatorInsightTimeline:
    """Timeline layer for insight tracking and escalation context.
    
    Provides read-only timeline tracking:
    - Record insight changes over time
    - Track significance, confidence, and safe_action shifts
    - Escalation context around insight changes (normal/attention/urgent)
    - Query timeline by correlation IDs
    - Operator-readable timeline summary
    - Machine-readable timeline export
    
    Correlation support:
    - flow_id
    - request_id
    - handshake_id
    - deadline_id
    
    Read-only analysis only — no behavior changes.
    """
    
    def __init__(self):
        """Initialize operator insight timeline layer."""
        self._timeline_store = InsightTimelineStore()
    
    def record_insight_change(
        self,
        current_insight: RecoveryInsight,
        previous_insight: Optional[RecoveryInsight] = None,
        correlation_ids: Optional[Dict[str, str]] = None,
    ) -> InsightTimelineEntry:
        """Record an insight change in the timeline.
        
        Args:
            current_insight: Current RecoveryInsight
            previous_insight: Previous RecoveryInsight if available
            correlation_ids: Optional correlation IDs for context
        
        Returns:
            InsightTimelineEntry created
        """
        drift_type = self._determine_drift_type(current_insight, previous_insight)
        before_value, after_value = self._get_value_change(current_insight, previous_insight)
        significance_delta = self._calculate_significance_delta(current_insight, previous_insight)
        confidence_delta = self._calculate_confidence_delta(current_insight, previous_insight)
        safe_action_shift = self._determine_safe_action_shift(current_insight, previous_insight)
        escalation_level, escalation_reason = self._assess_escalation(
            drift_type, significance_delta, confidence_delta, current_insight
        )
        
        entry = InsightTimelineEntry(
            entry_id=f"timeline_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            insight_id=current_insight.insight_id,
            drift_type=drift_type,
            before_value=before_value,
            after_value=after_value,
            significance_delta=significance_delta,
            confidence_delta=confidence_delta,
            safe_action_shift=safe_action_shift,
            escalation_level=escalation_level,
            escalation_reason=escalation_reason,
            correlation_ids=correlation_ids or current_insight.correlation_ids,
        )
        
        self._timeline_store.add_entry(entry)
        return entry
    
    def _determine_drift_type(
        self,
        current: RecoveryInsight,
        previous: Optional[RecoveryInsight],
    ) -> str:
        """Determine drift type from insight change."""
        if previous is None:
            return "insight_count"  # New insight
        
        if current.significance != previous.significance:
            return "significance"
        if current.guidance != previous.guidance:
            return "confidence_guidance"
        return "safe_next_action"
    
    def _get_value_change(
        self,
        current: RecoveryInsight,
        previous: Optional[RecoveryInsight],
    ) -> tuple[Any, Any]:
        """Get before/after values for change tracking."""
        if previous is None:
            return None, current.significance
        return previous.significance, current.significance
    
    def _calculate_significance_delta(
        self,
        current: RecoveryInsight,
        previous: Optional[RecoveryInsight],
    ) -> float:
        """Calculate significance delta between insights."""
        if previous is None:
            return 1.0  # New insight
        
        significance_map = {"low": 0.0, "medium": 0.5, "high": 1.0}
        current_val = significance_map.get(current.significance, 0.0)
        previous_val = significance_map.get(previous.significance, 0.0)
        return current_val - previous_val
    
    def _calculate_confidence_delta(
        self,
        current: RecoveryInsight,
        previous: Optional[RecoveryInsight],
    ) -> float:
        """Calculate confidence guidance delta."""
        if previous is None:
            return 0.0
        # Simplified: no confidence delta tracking in v85 data model
        return 0.0
    
    def _determine_safe_action_shift(
        self,
        current: RecoveryInsight,
        previous: Optional[RecoveryInsight],
    ) -> Optional[str]:
        """Determine safe-next-action shift."""
        if previous is None:
            return None
        
        if current.guidance and previous.guidance and current.guidance != previous.guidance:
            return f"{previous.guidance} -> {current.guidance}"
        return None
    
    def _assess_escalation(
        self,
        drift_type: str,
        significance_delta: float,
        confidence_delta: float,
        current: RecoveryInsight,
    ) -> tuple[str, str]:
        """Assess escalation level (heuristic, not certainty)."""
        # New insight (insight_count) always normal
        if drift_type == "insight_count":
            return "normal", "Standard insight count tracking"
        
        # Significant significance change triggers attention
        if significance_delta < -0.5 or significance_delta > 0.5:
            return "attention", "Significant significance change detected"
        
        # High significance insight triggers attention
        if current.significance == "high":
            return "attention", "High significance insight change"
        
        return "normal", "Standard insight change"
    
    def get_timeline(self) -> List[InsightTimelineEntry]:
        """Get all timeline entries.
        
        Returns:
            List of all InsightTimelineEntry
        """
        return self._timeline_store.get_timeline()
    
    def get_timeline_for_request(
        self,
        request_id: str,
    ) -> List[InsightTimelineEntry]:
        """Get timeline entries for a specific request.
        
        Args:
            request_id: Request ID to filter by
        
        Returns:
            List of InsightTimelineEntry for request
        """
        return self._timeline_store.get_timeline_for_request(request_id)
    
    def get_timeline_for_flow(
        self,
        flow_id: str,
    ) -> List[InsightTimelineEntry]:
        """Get timeline entries for a specific flow.
        
        Args:
            flow_id: Flow ID to filter by
        
        Returns:
            List of InsightTimelineEntry for flow
        """
        return self._timeline_store.get_timeline_for_flow(flow_id)
    
    def get_significance_shifts(self) -> List[InsightTimelineEntry]:
        """Get all significance shift entries.
        
        Returns:
            List of InsightTimelineEntry with drift_type="significance"
        """
        return self._timeline_store.get_significance_shifts()
    
    def get_confidence_shifts(self) -> List[InsightTimelineEntry]:
        """Get all confidence-guidance shift entries.
        
        Returns:
            List of InsightTimelineEntry with drift_type="confidence_guidance"
        """
        return self._timeline_store.get_confidence_shifts()
    
    def get_safe_action_shifts(self) -> List[InsightTimelineEntry]:
        """Get all safe-next-action shift entries.
        
        Returns:
            List of InsightTimelineEntry with drift_type="safe_next_action"
        """
        return self._timeline_store.get_safe_action_shifts()
    
    def get_escalation_context(
        self,
        hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """Get escalation context for recent changes.
        
        Args:
            hours: Time window in hours
        
        Returns:
            List of escalation context dicts
        """
        return self._timeline_store.get_escalation_context(hours)
    
    def get_summary_window(
        self,
        hours: int = 24,
    ) -> TimelineSummary:
        """Get timeline summary for time window.
        
        Args:
            hours: Time window in hours
        
        Returns:
            TimelineSummary with operator and machine readable content
        """
        entries = self.get_timeline()
        if not entries:
            return TimelineSummary(
                summary_id=f"summary_{uuid.uuid4().hex[:12]}",
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                time_range_start="N/A",
                time_range_end="N/A",
                total_changes=0,
                escalation_events=0,
                drift_type_distribution={},
                operator_readable="No insight timeline data available. Record insight changes first.",
                machine_readable=json.dumps({"error": "No timeline data"}, indent=2),
            )
        
        # Get time range
        timestamps = [datetime.fromisoformat(e.timestamp.replace("Z", "+00:00")) for e in entries]
        time_range_start = min(timestamps).isoformat()
        time_range_end = max(timestamps).isoformat()
        
        # Count changes
        total_changes = len(entries)
        escalation_summary = self._timeline_store.get_escalation_summary()
        escalation_events = escalation_summary.get("attention", 0) + escalation_summary.get("urgent", 0)
        
        # Count drift types
        drift_type_dist = {}
        for entry in entries:
            dt = entry.drift_type
            drift_type_dist[dt] = drift_type_dist.get(dt, 0) + 1
        
        # Generate operator-readable summary
        lines = [
            "=" * 70,
            "OPERATOR INSIGHT TIMELINE SUMMARY",
            "=" * 70,
            f"Summary ID: {uuid.uuid4().hex[:12]}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
            f"Time Range: {time_range_start} to {time_range_end}",
            f"Total Changes: {total_changes}",
            f"Escalation Events: {escalation_events}",
            "",
            "-" * 70,
            "ESCALATION DISTRIBUTION",
            "-" * 70,
        ]
        
        for level in ["urgent", "attention", "normal"]:
            count = escalation_summary.get(level, 0)
            if count > 0:
                lines.append(f"  {level.upper()}: {count}")
        
        lines.extend([
            "",
            "-" * 70,
            "DRIFT TYPE DISTRIBUTION",
            "-" * 70,
        ])
        
        for dt, count in sorted(drift_type_dist.items()):
            lines.append(f"  {dt}: {count}")
        
        lines.extend([
            "",
            "-" * 70,
            "HEURISTIC NOTE",
            "-" * 70,
            "Escalation levels and drift detection are heuristics, not certainties.",
            "",
            "Key distinctions:",
            "- Heuristic escalation: Operator guidance, not automatic action",
            "- Normal: Typical pattern changes, standard monitoring",
            "- Attention: Unusual pattern changes, review recommended",
            "- Urgent: Significant pattern changes, operator review required",
            "- Drift detection: Observations over time, not predictions",
            "",
            "This timeline layer provides operator-facing insight tracking,",
            "not automatic decision-making or remediation.",
            "",
            "=" * 70,
        ])
        
        operator_summary = "\n".join(lines)
        machine_summary = json.dumps({
            "summary_id": uuid.uuid4().hex[:12],
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "time_range_start": time_range_start,
            "time_range_end": time_range_end,
            "total_changes": total_changes,
            "escalation_events": escalation_events,
            "drift_type_distribution": drift_type_dist,
            "entries": [e.to_dict() for e in entries],
        }, indent=2)
        
        return TimelineSummary(
            summary_id=uuid.uuid4().hex[:12],
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            total_changes=total_changes,
            escalation_events=escalation_events,
            drift_type_distribution=drift_type_dist,
            operator_readable=operator_summary,
            machine_readable=machine_summary,
        )
    
    def get_escalation_summary(self) -> Dict[str, int]:
        """Get escalation level distribution.
        
        Returns:
            Dict with counts for each escalation level
        """
        return self._timeline_store.get_escalation_summary()
    
    def export_operator_readable(self) -> str:
        """Export timeline as operator-readable string."""
        summary = self.get_summary_window()
        return summary.operator_readable
    
    def export_machine_readable(self) -> str:
        """Export timeline as JSON string."""
        return self._timeline_store.export_machine_readable()
    
    def export_timeline_json(self) -> str:
        """Export all entries as JSON string."""
        return self._timeline_store.export_timeline_json()
    
    def export_drift_type_json(self, drift_type: str) -> str:
        """Export entries filtered by drift type."""
        return self._timeline_store.export_drift_type_json(drift_type)


# ============================================================================
# INTEGRATION HELPERS (Additive Only)
# ============================================================================


def integrate_with_v85_insights(timeline: OperatorInsightTimeline) -> Dict[str, Any]:
    """Integration hook for v85 recovery insights — read-only timeline only.
    
    No behavior changes to existing insight logic.
    """
    return {"hooked": True, "measures": "insight_timeline_integration"}


def correlate_with_v78_traces(timeline: OperatorInsightTimeline) -> Dict[str, Any]:
    """Correlation hook for v78 traces — read-only timeline only.
    
    No behavior changes to existing trace logic.
    """
    return {"hooked": True, "measures": "trace_correlation_integration"}
