# recovery_pattern_history.py - WESLR v84: Recovery Pattern History / Trend Layer
# Read-only operator-facing history/trend layer for recovery patterns over time.
# No optimization, no remediation, no orchestration, no backend/service/UI.
# No TIA/C#, no analytics engine beyond history/trend scope.

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .recovery_pattern_comparison import (
    PatternComparison,
    RecoveryPatternComparison,
)


# ============================================================================
# HISTORY DATA MODELS
# ============================================================================


@dataclass
class PatternHistoryRecord:
    """Single recovery pattern history record.
    
    Contains:
    - Pattern metadata (type, timestamp, correlation IDs)
    - Pattern content (recommendation, decision trace, etc.)
    - History position (sequence, time window)
    """
    
    history_id: str
    timestamp: str
    pattern_type: str  # "recommendation", "decision_trace", etc.
    pattern_id: str
    correlation_ids: Dict[str, str]
    
    # Pattern content
    content: Dict[str, Any]
    
    # History context
    sequence: int
    window_start: str
    window_end: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "history_id": self.history_id,
            "timestamp": self.timestamp,
            "pattern_type": self.pattern_type,
            "pattern_id": self.pattern_id,
            "correlation_ids": self.correlation_ids,
            "content": self.content,
            "sequence": self.sequence,
            "window_start": self.window_start,
            "window_end": self.window_end,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class TrendSummary:
    """Trend summary for operator visibility.
    
    Contains:
    - Pattern type distribution
    - Repeated pattern frequency
    - Confidence guidance trends
    - Safe-next-action convergence/divergence patterns
    """
    
    summary_id: str
    timestamp: str
    total_patterns: int
    pattern_type_distribution: Dict[str, int]
    repeated_patterns: Dict[str, int]
    confidence_trend: Dict[str, int]  # confidence level -> count
    safe_action_patterns: Dict[str, int]  # action type -> count
    operator_readable: str  # Multi-line narrative
    machine_readable: str  # JSON string
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "summary_id": self.summary_id,
            "timestamp": self.timestamp,
            "total_patterns": self.total_patterns,
            "pattern_type_distribution": self.pattern_type_distribution,
            "repeated_patterns": self.repeated_patterns,
            "confidence_trend": self.confidence_trend,
            "safe_action_patterns": self.safe_action_patterns,
            "operator_readable": self.operator_readable,
            "machine_readable": self.machine_readable,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# RECOVERY PATTERN HISTORY LAYER
# ============================================================================


class RecoveryPatternHistory:
    """History layer for recovery pattern tracking over time.
    
    Provides read-only history/trend analysis:
    - Compare recovery patterns across time
    - Trend visibility for confidence guidance changes
    - Trend visibility for safe-next-action convergence/divergence
    - Repeated pattern history over time
    - Operator-readable history/trend summary
    - Machine-readable trend export
    
    Correlation support:
    - flow_id
    - request_id
    - handshake_id
    - deadline_id
    
    Read-only analysis only — no behavior changes.
    """
    
    def __init__(self):
        """Initialize pattern history layer."""
        self._history: List[PatternHistoryRecord] = []
        self._repeated_patterns: Dict[str, int] = {}
        self._sequence_counter: int = 0
    
    def add_recommendation_pattern(
        self,
        recommendation: Dict[str, Any],
        correlation_ids: Optional[Dict[str, str]] = None,
    ) -> PatternHistoryRecord:
        """Add a recommendation pattern to history.
        
        Args:
            recommendation: Recommendation dict
            correlation_ids: Optional correlation IDs for context
        
        Returns:
            PatternHistoryRecord with sequence tracking
        """
        self._sequence_counter += 1
        window = self._get_time_window()
        
        record = PatternHistoryRecord(
            history_id=f"history_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            pattern_type="recommendation",
            pattern_id=recommendation.get("recommendation_id", f"rec_{self._sequence_counter}"),
            correlation_ids=correlation_ids or {},
            content=recommendation,
            sequence=self._sequence_counter,
            window_start=window[0],
            window_end=window[1],
        )
        
        self._history.append(record)
        self._track_pattern(record)
        
        return record
    
    def add_decision_trace_pattern(
        self,
        decision_trace: Dict[str, Any],
        correlation_ids: Optional[Dict[str, str]] = None,
    ) -> PatternHistoryRecord:
        """Add a decision trace pattern to history.
        
        Args:
            decision_trace: Decision trace dict
            correlation_ids: Optional correlation IDs for context
        
        Returns:
            PatternHistoryRecord with sequence tracking
        """
        self._sequence_counter += 1
        window = self._get_time_window()
        
        record = PatternHistoryRecord(
            history_id=f"history_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            pattern_type="decision_trace",
            pattern_id=decision_trace.get("trace_id", f"trace_{self._sequence_counter}"),
            correlation_ids=correlation_ids or {},
            content=decision_trace,
            sequence=self._sequence_counter,
            window_start=window[0],
            window_end=window[1],
        )
        
        self._history.append(record)
        self._track_pattern(record)
        
        return record
    
    def _get_time_window(self) -> Tuple[str, str]:
        """Get current time window for pattern history.
        
        Returns (window_start, window_end) tuple.
        Window represents the operational time slice for analysis.
        """
        now = datetime.now(timezone.utc)
        # Simple window: current hour
        window_start = now.replace(minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")
        window_end = now.replace(minute=59, second=59, microsecond=999999).isoformat().replace("+00:00", "Z")
        return window_start, window_end
    
    def _track_pattern(self, record: PatternHistoryRecord) -> None:
        """Track pattern for repeated pattern detection (lightweight)."""
        # Track pattern type
        pt = f"pattern_type_{record.pattern_type}"
        self._repeated_patterns[pt] = self._repeated_patterns.get(pt, 0) + 1
        
        # Track correlation patterns if present
        for cid_name, cid_val in record.correlation_ids.items():
            if cid_val:
                key = f"correlation_{cid_name}={cid_val}"
                self._repeated_patterns[key] = self._repeated_patterns.get(key, 0) + 1
    
    def get_pattern_history(
        self,
        pattern_type: Optional[str] = None,
        time_window: Optional[str] = None,
        correlation_type: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> List[PatternHistoryRecord]:
        """Get pattern history with optional filters.
        
        Args:
            pattern_type: Filter by pattern type (recommendation, decision_trace, etc.)
            time_window: Filter by time window (future: implement time-based filtering)
            correlation_type: Filter by correlation type
            correlation_id: Filter by correlation ID value
        
        Returns:
            List of PatternHistoryRecord matching filters
        """
        results = self._history
        
        if pattern_type:
            results = [r for r in results if r.pattern_type == pattern_type]
        
        if correlation_type and correlation_id:
            results = [
                r for r in results
                if r.correlation_ids.get(correlation_type) == correlation_id
            ]
        
        return results
    
    def find_repeated_patterns(self) -> Dict[str, int]:
        """Find repeated patterns in history.
        
        Returns dict of pattern -> frequency (lightweight, descriptive).
        
        This is NOT a clustering/analytics engine — just descriptive counting.
        """
        return dict(self._repeated_patterns)
    
    def get_trend_summary(self) -> TrendSummary:
        """Generate operator-readable trend summary.
        
        Analyzes:
        - Pattern type distribution over time
        - Repeated pattern frequency
        - Confidence guidance trends
        - Safe-next-action convergence/divergence patterns
        """
        if not self._history:
            return TrendSummary(
                summary_id=f"trend_{uuid.uuid4().hex[:12]}",
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                total_patterns=0,
                pattern_type_distribution={},
                repeated_patterns={},
                confidence_trend={},
                safe_action_patterns={},
                operator_readable="No pattern history available.",
                machine_readable=json.dumps({"error": "No pattern history available"}, indent=2),
            )
        
        # Count pattern types
        pattern_type_dist: Dict[str, int] = {}
        for record in self._history:
            pt = record.pattern_type
            pattern_type_dist[pt] = pattern_type_dist.get(pt, 0) + 1
        
        # Get repeated patterns
        repeated = self.find_repeated_patterns()
        
        # Extract confidence trends from decision traces
        confidence_trend: Dict[str, int] = {}
        for record in self._history:
            if record.pattern_type == "decision_trace":
                confidence = record.content.get("confidence_level", "unknown")
                confidence_trend[confidence] = confidence_trend.get(confidence, 0) + 1
        
        # Extract safe-next-action patterns from decision traces
        safe_action_patterns: Dict[str, int] = {}
        for record in self._history:
            if record.pattern_type == "decision_trace":
                safe_action = record.content.get("safe_next_action", {})
                action_type = safe_action.get("type", "unknown")
                safe_action_patterns[action_type] = safe_action_patterns.get(action_type, 0) + 1
        
        # Generate operator-readable summary
        lines = [
            "=" * 70,
            "RECOVERY PATTERN HISTORY TREND SUMMARY",
            "=" * 70,
            f"Summary ID: {uuid.uuid4().hex[:12]}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
            f"Total Patterns: {len(self._history)}",
            f"Sequence Count: {self._sequence_counter}",
            "",
            "-" * 70,
            "PATTERN TYPE DISTRIBUTION",
            "-" * 70,
        ]
        
        for pt, count in sorted(pattern_type_dist.items()):
            lines.append(f"  {pt}: {count}")
        
        lines.extend([
            "",
            "-" * 70,
            "REPEATED PATTERNS (frequency)",
            "-" * 70,
        ])
        
        # Show most common patterns
        for pattern, freq in sorted(repeated.items(), key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"  {pattern}: {freq}")
        
        lines.extend([
            "",
            "-" * 70,
            "CONFIDENCE GUIDANCE TRENDS",
            "-" * 70,
        ])
        
        for conf, count in sorted(confidence_trend.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {conf}: {count}")
        
        lines.extend([
            "",
            "-" * 70,
            "SAFE-NEXT-ACTION PATTERNS",
            "-" * 70,
        ])
        
        for action, count in sorted(safe_action_patterns.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {action}: {count}")
        
        lines.extend([
            "",
            "-" * 70,
            "HEURISTIC NOTE",
            "-" * 70,
            "Pattern analysis is descriptive, not predictive.",
            "",
            "Key distinctions:",
            "- Pattern history: What patterns have been observed over time",
            "- Repeated patterns: Frequency of similar patterns",
            "- Confidence trends: How confidence levels have changed",
            "- Safe-action patterns: What actions are recommended",
            "",
            "This history layer provides operator-facing pattern visibility,",
            "not automatic decision-making or remediation.",
            "",
            "=" * 70,
        ])
        
        operator_summary = "\n".join(lines)
        machine_summary = json.dumps({
            "summary_id": uuid.uuid4().hex[:12],
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "total_patterns": len(self._history),
            "pattern_type_distribution": pattern_type_dist,
            "repeated_patterns": repeated,
            "confidence_trend": confidence_trend,
            "safe_action_patterns": safe_action_patterns,
            "patterns": [r.to_dict() for r in self._history],
        }, indent=2)
        
        return TrendSummary(
            summary_id=uuid.uuid4().hex[:12],
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            total_patterns=len(self._history),
            pattern_type_distribution=pattern_type_dist,
            repeated_patterns=repeated,
            confidence_trend=confidence_trend,
            safe_action_patterns=safe_action_patterns,
            operator_readable=operator_summary,
            machine_readable=machine_summary,
        )
    
    def export_operator_readable(self) -> str:
        """Export trend summary as operator-readable string."""
        summary = self.get_trend_summary()
        return summary.operator_readable
    
    def export_machine_readable(self) -> str:
        """Export trend summary as JSON string."""
        summary = self.get_trend_summary()
        return summary.machine_readable
    
    def export_patterns_as_json(self) -> str:
        """Export all pattern history as JSON string."""
        return json.dumps([r.to_dict() for r in self._history], indent=2)
    
    def export_trend_data_as_json(self) -> str:
        """Export trend summary data as JSON string."""
        summary = self.get_trend_summary()
        return summary.machine_readable


# ============================================================================
# INTEGRATION HELPERS (Additive Only)
# ============================================================================


def integrate_with_v83_comparison(history: RecoveryPatternHistory) -> Dict[str, Any]:
    """Integration hook for v83 comparison layer — read-only history only.
    
    No behavior changes to existing comparison logic.
    """
    return {"hooked": True, "measures": "pattern_history_integration"}


def correlate_with_v78_decision_traces(history: RecoveryPatternHistory) -> Dict[str, Any]:
    """Correlation hook for v78 decision traces — read-only history only.
    
    No behavior changes to existing trace logic.
    """
    return {"hooked": True, "measures": "decision_trace_correlation"}
