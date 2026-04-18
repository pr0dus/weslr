# operator_recovery_insight.py - WESLR v85: Operator Recovery Insight Layer
# Read-only operator-facing insight layer that turns recovery pattern history,
# comparison, and decision traces into higher-level operator insights.
# No optimization, no remediation, no orchestration, no backend/service/UI.
# No TIA/C#, no analytics engine beyond insight scope.

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
from .recovery_pattern_history import (
    PatternHistoryRecord,
    RecoveryPatternHistory,
    TrendSummary,
)


# ============================================================================
# INSIGHT DATA MODELS
# ============================================================================


@dataclass
class RecoveryInsight:
    """Single recovery insight with significance and guidance.
    
    Contains:
    - Insight metadata (type, timestamp, correlation IDs)
    - Insight content (interpretation, significance)
    - Guidance level (low/medium/high)
    - Confidence indication (not certainty)
    """
    
    insight_id: str
    timestamp: str
    insight_type: str  # "trend_shift", "convergence", "divergence", "repeated_pattern"
    pattern_id: str  # Reference to pattern history record
    correlation_ids: Dict[str, str]
    
    # Insight content
    interpretation: str  # Human-readable interpretation
    significance: str  # "low", "medium", "high"
    significance_reason: str  # Why this significance
    guidance: Optional[str] = None  # Operator guidance
    
    # Pattern context
    pattern_type: str = ""  # "recommendation", "decision_trace"
    historical_context: str = ""  # Context from history
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "insight_id": self.insight_id,
            "timestamp": self.timestamp,
            "insight_type": self.insight_type,
            "pattern_id": self.pattern_id,
            "correlation_ids": self.correlation_ids,
            "interpretation": self.interpretation,
            "significance": self.significance,
            "significance_reason": self.significance_reason,
            "guidance": self.guidance,
            "pattern_type": self.pattern_type,
            "historical_context": self.historical_context,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class TrendShift:
    """Trend shift detection with interpretation.
    
    Contains:
    - Shift metadata (type, direction, magnitude)
    - Interpretation (operator-facing explanation)
    - Significance assessment (not certainty)
    """
    
    shift_id: str
    timestamp: str
    trend_type: str  # "confidence", "safe_action", "recovery_hint"
    direction: str  # "increasing", "decreasing", "stable", "variable"
    magnitude: str  # "minor", "moderate", "significant"
    
    # Interpretation
    interpretation: str  # What this means for operators
    significance: str  # "low", "medium", "high"
    significance_reason: str  # Why this significance
    
    # Pattern reference
    pattern_type: str
    reference_pattern_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "shift_id": self.shift_id,
            "timestamp": self.timestamp,
            "trend_type": self.trend_type,
            "direction": self.direction,
            "magnitude": self.magnitude,
            "interpretation": self.interpretation,
            "significance": self.significance,
            "significance_reason": self.significance_reason,
            "pattern_type": self.pattern_type,
            "reference_pattern_id": self.reference_pattern_id,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class InsightSummary:
    """Operator-readable insight summary with machine-readable export.
    
    Contains:
    - Insight type distribution
    - Trend shift summary
    - Convergence/divergence patterns
    - Repeated pattern significance
    """
    
    summary_id: str
    timestamp: str
    total_insights: int
    insight_type_distribution: Dict[str, int]
    trend_shifts: List[Dict[str, Any]]
    convergence_patterns: Dict[str, int]  # action type -> convergence count
    divergence_patterns: Dict[str, int]  # action type -> divergence count
    repeated_pattern_significance: Dict[str, int]
    operator_readable: str  # Multi-line narrative
    machine_readable: str  # JSON string
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "summary_id": self.summary_id,
            "timestamp": self.timestamp,
            "total_insights": self.total_insights,
            "insight_type_distribution": self.insight_type_distribution,
            "trend_shifts": self.trend_shifts,
            "convergence_patterns": self.convergence_patterns,
            "divergence_patterns": self.divergence_patterns,
            "repeated_pattern_significance": self.repeated_pattern_significance,
            "operator_readable": self.operator_readable,
            "machine_readable": self.machine_readable,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# OPERATOR RECOVERY INSIGHT LAYER
# ============================================================================


class OperatorRecoveryInsight:
    """Insight layer for operator-facing recovery pattern analysis.
    
    Provides read-only insight generation:
    - Notable trend shift detection
    - Confidence guidance trend interpretation
    - Safe-next-action convergence/divergence insight
    - Repeated recovery pattern significance summary
    - Operator-readable insight summary
    - Machine-readable insight export
    
    Correlation support:
    - flow_id
    - request_id
    - handshake_id
    - deadline_id
    
    Read-only analysis only — no behavior changes.
    """
    
    def __init__(self):
        """Initialize operator recovery insight layer."""
        self._insights: List[RecoveryInsight] = []
        self._trend_shifts: List[TrendShift] = []
        self._convergence_patterns: Dict[str, int] = {}
        self._divergence_patterns: Dict[str, int] = {}
        self._repeated_pattern_significance: Dict[str, int] = {}
    
    def detect_trend_shifts(
        self,
        trend_summary: TrendSummary,
        previous_trend: Optional[Dict[str, int]] = None,
    ) -> List[TrendShift]:
        """Detect trend shifts from trend summary.
        
        Args:
            trend_summary: Current trend summary from v84
            previous_trend: Optional previous trend for comparison
        
        Returns:
            List of TrendShift records
        """
        shifts = []
        
        # Analyze confidence trends
        confidence_dist = trend_summary.confidence_trend
        if confidence_dist:
            # Determine direction based on distribution
            if len(confidence_dist) == 1:
                direction = "stable"
                magnitude = "minor"
                interpretation = "Confidence levels remain consistent across patterns."
            else:
                # Check for high vs low distribution
                high_conf = confidence_dist.get("high", 0) + confidence_dist.get("very_high", 0)
                low_conf = confidence_dist.get("low", 0) + confidence_dist.get("very_low", 0)
                
                if high_conf > low_conf * 2:
                    direction = "increasing"
                    magnitude = "moderate"
                    interpretation = "Confidence levels are trending toward higher values."
                elif low_conf > high_conf * 2:
                    direction = "decreasing"
                    magnitude = "moderate"
                    interpretation = "Confidence levels are trending toward lower values."
                else:
                    direction = "variable"
                    magnitude = "significant"
                    interpretation = "Confidence levels show significant variation across patterns."
            
            shift = TrendShift(
                shift_id=f"shift_{uuid.uuid4().hex[:12]}",
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                trend_type="confidence",
                direction=direction,
                magnitude=magnitude,
                interpretation=interpretation,
                significance=self._assess_significance(magnitude, direction),
                significance_reason=self._get_significance_reason(
                    "confidence",
                    direction,
                    magnitude,
                ),
                pattern_type="recovery",
                reference_pattern_id="trend_summary",
            )
            shifts.append(shift)
            self._trend_shifts.append(shift)
        
        # Analyze safe-next-action patterns
        safe_action_dist = trend_summary.safe_action_patterns
        if safe_action_dist and len(safe_action_dist) > 1:
            # Check for convergence or divergence
            total = sum(safe_action_dist.values())
            dominant = max(safe_action_dist.values())
            ratio = dominant / total if total > 0 else 0
            
            if ratio > 0.7:
                direction = "convergence"
                magnitude = "moderate"
                interpretation = f"Safe-next-actions show convergence toward dominant pattern."
                self._convergence_patterns["dominant_action"] = dominant
            elif ratio > 0.4:
                direction = "stable"
                magnitude = "minor"
                interpretation = "Safe-next-actions show moderate diversity."
            else:
                direction = "divergence"
                magnitude = "significant"
                interpretation = "Safe-next-actions show significant diversity across patterns."
                self._divergence_patterns["diverse_actions"] = len(safe_action_dist)
            
            # Create a convergence/divergence insight
            insight = RecoveryInsight(
                insight_id=f"insight_{uuid.uuid4().hex[:12]}",
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                insight_type="convergence" if direction == "convergence" else "divergence",
                pattern_id="safe_action_pattern",
                correlation_ids={},
                interpretation=interpretation,
                significance=self._assess_significance(magnitude, direction),
                significance_reason=f"Safe-next-action {direction} indicates pattern consistency.",
                guidance=self._get_guidance(direction),
                pattern_type="decision_trace",
                historical_context="Multiple decision traces analyzed for action patterns.",
            )
            self._insights.append(insight)
        
        return shifts
    
    def _assess_significance(self, magnitude: str, direction: str) -> str:
        """Assess significance level based on magnitude and direction."""
        if magnitude == "significant" or direction == "divergence":
            return "high"
        elif magnitude == "moderate" or direction == "stable":
            return "medium"
        else:
            return "low"
    
    def _get_significance_reason(
        self,
        trend_type: str,
        direction: str,
        magnitude: str,
    ) -> str:
        """Get significance reason for trend shift.
        
        Note: Significance assessment is heuristic, not certainty.
        """
        reasons = {
            ("confidence", "increasing", "moderate"): "Higher confidence may indicate more reliable patterns.",
            ("confidence", "decreasing", "moderate"): "Lower confidence may indicate less reliable patterns.",
            ("confidence", "variable", "significant"): "Variable confidence suggests pattern inconsistency.",
            ("safe_action", "convergence", "moderate"): "Converging actions indicate consistent recovery paths.",
            ("safe_action", "divergence", "significant"): "Diverging actions suggest varying recovery approaches.",
        }
        result = reasons.get((trend_type, direction, magnitude))
        if result:
            return result
        # Default heuristic assessment
        return f"Standard significance assessment (heuristic, not certainty)."
    
    def _get_guidance(self, direction: str) -> Optional[str]:
        """Get operator guidance based on direction."""
        guidance_map = {
            "convergence": (
                "Consistent safe-next-action patterns suggest reliable recovery paths. "
                "Consider standardizing based on dominant pattern."
            ),
            "divergence": (
                "Diverse safe-next-action patterns suggest varied recovery approaches. "
                "Review each pattern for context-specific suitability."
            ),
            "variable": (
                "Variable patterns suggest context-dependent recovery. "
                "Evaluate each case individually rather than applying generalizations."
            ),
            "stable": (
                "Stable patterns suggest consistent behavior. "
                "Current approach appears reliable."
            ),
        }
        return guidance_map.get(direction)
    
    def detect_repeated_pattern_significance(
        self,
        repeated_patterns: Dict[str, int],
        min_frequency: int = 2,
    ) -> List[RecoveryInsight]:
        """Detect significance of repeated patterns.
        
        Args:
            repeated_patterns: Dict of pattern -> frequency from v84
            min_frequency: Minimum frequency to consider significant
        
        Returns:
            List of RecoveryInsight records
        """
        insights = []
        
        for pattern, frequency in repeated_patterns.items():
            if frequency >= min_frequency:
                # Determine pattern type from name
                if "similarity" in pattern:
                    insight_type = "repeated_pattern"
                    interpretation = (
                        f"Similar patterns observed {frequency} times. "
                        f"Consistent recovery approaches may be emerging."
                    )
                elif "correlation" in pattern:
                    insight_type = "repeated_pattern"
                    interpretation = (
                        f"Correlation pattern '{pattern}' observed {frequency} times. "
                        f"Specific correlation patterns may be indicative."
                    )
                elif "pattern_type" in pattern:
                    insight_type = "repeated_pattern"
                    interpretation = (
                        f"Pattern type '{pattern}' observed {frequency} times. "
                        f"Pattern distribution may be stable."
                    )
                elif "repeated" in pattern:
                    insight_type = "repeated_pattern"
                    interpretation = (
                        f"Repeated pattern '{pattern}' observed {frequency} times. "
                        f"Recovery patterns show consistency."
                    )
                else:
                    continue
                
                insight = RecoveryInsight(
                    insight_id=f"insight_{uuid.uuid4().hex[:12]}",
                    timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    insight_type=insight_type,
                    pattern_id=pattern,
                    correlation_ids={},
                    interpretation=interpretation,
                    significance="medium",
                    significance_reason=f"Pattern repeated {frequency} times suggests non-random occurrence.",
                    guidance=(
                        "Repeated patterns may indicate reliable recovery approaches "
                        "for similar scenarios."
                    ),
                    pattern_type="recovery",
                    historical_context="Multiple patterns analyzed for repetition.",
                )
                self._insights.append(insight)
                self._repeated_pattern_significance[pattern] = frequency
        
        return insights
    
    def analyze_recovery_patterns(
        self,
        comparison: RecoveryPatternComparison,
        history: RecoveryPatternHistory,
    ) -> Dict[str, Any]:
        """Analyze recovery patterns from v83/v84 layers.
        
        Args:
            comparison: v83 RecoveryPatternComparison instance
            history: v84 RecoveryPatternHistory instance
        
        Returns:
            Analysis results dict
        """
        # Get trend summary from v84
        trend_summary = history.get_trend_summary()
        
        # Detect trend shifts
        shifts = self.detect_trend_shifts(trend_summary)
        
        # Detect repeated pattern significance
        repeated = history.find_repeated_patterns()
        repeated_insights = self.detect_repeated_pattern_significance(repeated)
        
        # Analyze comparison patterns
        if comparison._comparisons:
            high_similarity_count = sum(
                1 for c in comparison._comparisons
                if c.observed_similarity in ["high", "medium"]
            )
            if high_similarity_count > len(comparison._comparisons) * 0.7:
                insight = RecoveryInsight(
                    insight_id=f"insight_{uuid.uuid4().hex[:12]}",
                    timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    insight_type="convergence",
                    pattern_id="comparison_patterns",
                    correlation_ids={},
                    interpretation=(
                        "High similarity in comparison patterns suggests consistent "
                        "recovery approaches across incidents."
                    ),
                    significance="high",
                    significance_reason="70%+ patterns show high similarity.",
                    guidance=(
                        "High similarity in patterns suggests established recovery methods "
                        "are applicable across incidents. Consider standardization."
                    ),
                    pattern_type="comparison",
                    historical_context="Comparison patterns analyzed for similarity.",
                )
                self._insights.append(insight)
                self._convergence_patterns["high_similarity"] = high_similarity_count
        
        return {
            "shifts": [s.to_dict() for s in shifts],
            "repeated_insights": [i.to_dict() for i in repeated_insights],
            "total_insights": len(self._insights),
        }
    
    def get_insight_summary(self) -> InsightSummary:
        """Generate operator-readable insight summary."""
        if not self._insights and not self._trend_shifts:
            return InsightSummary(
                summary_id=f"summary_{uuid.uuid4().hex[:12]}",
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                total_insights=0,
                insight_type_distribution={},
                trend_shifts=[],
                convergence_patterns={},
                divergence_patterns={},
                repeated_pattern_significance={},
                operator_readable="No insights available. Analyze recovery patterns first.",
                machine_readable=json.dumps({"error": "No insights available"}, indent=2),
            )
        
        # Count insight types
        insight_type_dist: Dict[str, int] = {}
        for insight in self._insights:
            it = insight.insight_type
            insight_type_dist[it] = insight_type_dist.get(it, 0) + 1
        
        # Count shift types
        shift_dist: Dict[str, int] = {}
        for shift in self._trend_shifts:
            st = f"{shift.trend_type}_{shift.direction}"
            shift_dist[st] = shift_dist.get(st, 0) + 1
        
        # Generate operator-readable summary
        lines = [
            "=" * 70,
            "OPERATOR RECOVERY INSIGHT SUMMARY",
            "=" * 70,
            f"Summary ID: {uuid.uuid4().hex[:12]}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
            f"Total Insights: {len(self._insights)}",
            f"Total Trend Shifts: {len(self._trend_shifts)}",
            "",
            "-" * 70,
            "INSIGHT TYPE DISTRIBUTION",
            "-" * 70,
        ]
        
        for it, count in sorted(insight_type_dist.items()):
            lines.append(f"  {it}: {count}")
        
        lines.extend([
            "",
            "-" * 70,
            "TREND SHIFTS DETECTED",
            "-" * 70,
        ])
        
        for shift in self._trend_shifts:
            lines.append(
                f"  {shift.trend_type}: {shift.direction} ({shift.magnitude}) - "
                f"Significance: {shift.significance}"
            )
        
        lines.extend([
            "",
            "-" * 70,
            "CONVERGENCE PATTERNS",
            "-" * 70,
        ])
        
        for pattern, count in sorted(self._convergence_patterns.items()):
            lines.append(f"  {pattern}: {count}")
        
        lines.extend([
            "",
            "-" * 70,
            "DIVERSION PATTERNS",
            "-" * 70,
        ])
        
        for pattern, count in sorted(self._divergence_patterns.items()):
            lines.append(f"  {pattern}: {count}")
        
        lines.extend([
            "",
            "-" * 70,
            "REPEATED PATTERN SIGNIFICANCE",
            "-" * 70,
        ])
        
        for pattern, count in sorted(self._repeated_pattern_significance.items()):
            lines.append(f"  {pattern}: {count}")
        
        lines.extend([
            "",
            "-" * 70,
            "HEURISTIC NOTE",
            "-" * 70,
            "Insights are interpretations, not certainties.",
            "",
            "Key distinctions:",
            "- Significance: Heuristic assessment of pattern importance",
            "- Guidance: Operator-facing recommendations, not directives",
            "- Trends: Observations over time, not predictions",
            "",
            "This insight layer provides operator-facing pattern analysis,",
            "not automatic decision-making or remediation.",
            "",
            "=" * 70,
        ])
        
        operator_summary = "\n".join(lines)
        machine_summary = json.dumps({
            "summary_id": uuid.uuid4().hex[:12],
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "total_insights": len(self._insights),
            "total_shifts": len(self._trend_shifts),
            "insight_type_distribution": insight_type_dist,
            "shift_dist": shift_dist,
            "convergence_patterns": self._convergence_patterns,
            "divergence_patterns": self._divergence_patterns,
            "repeated_pattern_significance": self._repeated_pattern_significance,
            "insights": [i.to_dict() for i in self._insights],
            "shifts": [s.to_dict() for s in self._trend_shifts],
        }, indent=2)
        
        return InsightSummary(
            summary_id=uuid.uuid4().hex[:12],
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            total_insights=len(self._insights),
            insight_type_distribution=insight_type_dist,
            trend_shifts=[s.to_dict() for s in self._trend_shifts],
            convergence_patterns=self._convergence_patterns,
            divergence_patterns=self._divergence_patterns,
            repeated_pattern_significance=self._repeated_pattern_significance,
            operator_readable=operator_summary,
            machine_readable=machine_summary,
        )
    
    def export_operator_readable(self) -> str:
        """Export insight summary as operator-readable string."""
        summary = self.get_insight_summary()
        return summary.operator_readable
    
    def export_machine_readable(self) -> str:
        """Export insight summary as JSON string."""
        summary = self.get_insight_summary()
        return summary.machine_readable
    
    def export_insights_as_json(self) -> str:
        """Export all insights as JSON string."""
        return json.dumps([i.to_dict() for i in self._insights], indent=2)
    
    def export_trend_shifts_as_json(self) -> str:
        """Export all trend shifts as JSON string."""
        return json.dumps([s.to_dict() for s in self._trend_shifts], indent=2)


# ============================================================================
# INTEGRATION HELPERS (Additive Only)
# ============================================================================


def integrate_with_v83_comparison(insight: OperatorRecoveryInsight) -> Dict[str, Any]:
    """Integration hook for v83 comparison layer — read-only insight only.
    
    No behavior changes to existing comparison logic.
    """
    return {"hooked": True, "measures": "comparison_insight_integration"}


def integrate_with_v84_history(insight: OperatorRecoveryInsight) -> Dict[str, Any]:
    """Integration hook for v84 history layer — read-only insight only.
    
    No behavior changes to existing history logic.
    """
    return {"hooked": True, "measures": "history_insight_integration"}
