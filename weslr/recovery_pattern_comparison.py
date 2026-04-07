# recovery_pattern_comparison.py - WESLR v83: Recovery Pattern Comparison Layer
# Read-only operator-facing comparison layer for recovery incidents.
# No optimization, no remediation, no orchestration, no backend/service/UI.
# No TIA/C#, no clustering/analytics engine beyond comparison scope.

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class PatternComparison:
    """Comparison record for two recovery patterns.
    
    Contains:
    - Observed shared fields (what's the same)
    - Observed differences (what differs)
    - Inferred similarity assessment (heuristic, not certainty)
    - Impact assessment (on confidence, recommendation, rationale, safe_action)
    """
    
    comparison_id: str
    timestamp: str
    pattern_type: str  # e.g., "recommendation", "decision_trace", "correlation"
    
    # Observed shared fields (what's the same)
    shared_fields: Dict[str, Any] = field(default_factory=dict)
    
    # Observed differences (what differs)
    differences: Dict[str, Tuple[Any, Any]] = field(default_factory=dict)
    
    # Inferred similarity (heuristic, not certainty)
    observed_similarity: str = "low"  # low/medium/high
    inferred_similarity_score: float = 0.0  # 0.0-1.0 (heuristic estimate)
    
    # Impact assessment
    confidence_impact: Optional[str] = None  # e.g., "similar", "different"
    recommendation_impact: Optional[str] = None
    rationale_impact: Optional[str] = None
    safe_action_impact: Optional[str] = None
    
    # Pattern identifiers
    pattern1_id: str = ""
    pattern2_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "comparison_id": self.comparison_id,
            "timestamp": self.timestamp,
            "pattern_type": self.pattern_type,
            "pattern1_id": self.pattern1_id,
            "pattern2_id": self.pattern2_id,
            "observed_similarity": self.observed_similarity,
            "inferred_similarity_score": self.inferred_similarity_score,
            "shared_fields": self.shared_fields,
            "differences": self.differences,
            "confidence_impact": self.confidence_impact,
            "recommendation_impact": self.recommendation_impact,
            "rationale_impact": self.rationale_impact,
            "safe_action_impact": self.safe_action_impact,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class ComparisonSummary:
    """Operator-readable comparison summary with machine-readable export."""
    
    summary_id: str
    timestamp: str
    total_comparisons: int
    pattern_types: Dict[str, int]  # pattern_type -> count
    shared_patterns: Dict[str, int]  # shared field -> frequency
    repeated_patterns: Dict[str, int]  # repeated pattern -> frequency
    operator_readable: str  # Multi-line narrative
    machine_readable: str  # JSON string
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "summary_id": self.summary_id,
            "timestamp": self.timestamp,
            "total_comparisons": self.total_comparisons,
            "pattern_types": self.pattern_types,
            "shared_patterns": self.shared_patterns,
            "repeated_patterns": self.repeated_patterns,
            "operator_readable": self.operator_readable,
            "machine_readable": self.machine_readable,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# RECOVERY PATTERN COMPARISON LAYER
# ============================================================================


class RecoveryPatternComparison:
    """Comparison layer for recovery incident patterns.
    
    Provides read-only comparison of recovery patterns:
    - Recommendation patterns
    - Decision trace patterns
    - Correlation-based patterns
    
    Key distinctions:
    - Observed shared fields: What's actually the same
    - Observed differences: What differs
    - Inferred similarity: Heuristic assessment (not certainty)
    
    Read-only analysis only — no behavior changes.
    """
    
    def __init__(self):
        """Initialize pattern comparison layer."""
        self._comparisons: List[PatternComparison] = []
        self._repeated_patterns: Dict[str, int] = {}
    
    def compare_recommendations(
        self,
        recommendation1: Dict[str, Any],
        recommendation2: Dict[str, Any],
        correlation_ids: Optional[Dict[str, str]] = None,
    ) -> PatternComparison:
        """Compare two recovery recommendations.
        
        Args:
            recommendation1: First recommendation dict
            recommendation2: Second recommendation dict
            correlation_ids: Optional correlation IDs for context
        
        Returns:
            PatternComparison with observed similarities and differences
            
        Note: Similarity assessment is heuristic, not certain.
        """
        # Extract fields for comparison
        fields1 = self._extract_recommendation_fields(recommendation1)
        fields2 = self._extract_recommendation_fields(recommendation2)
        
        # Find shared and different fields
        shared, differences = self._compare_fields(fields1, fields2)
        
        # Calculate heuristic similarity
        similarity = self._calculate_heuristic_similarity(fields1, fields2, shared, differences)
        
        comparison = PatternComparison(
            comparison_id=f"comp_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            pattern_type="recommendation",
            pattern1_id=recommendation1.get("recommendation_id", "unknown"),
            pattern2_id=recommendation2.get("recommendation_id", "unknown"),
            shared_fields=shared,
            differences=differences,
            observed_similarity=similarity["observed"],
            inferred_similarity_score=similarity["score"],
            confidence_impact=self._compare_confidence(
                recommendation1.get("confidence", "medium"),
                recommendation2.get("confidence", "medium"),
            ),
            recommendation_impact=self._compare_recovery_hints(
                recommendation1.get("recovery_hint"),
                recommendation2.get("recovery_hint"),
            ),
            rationale_impact=None,  # Recommendations don't have explicit rationale
            safe_action_impact=None,  # Recommendations don't have safe-next-action
        )
        
        self._comparisons.append(comparison)
        self._track_repeated_patterns(comparison)
        
        return comparison
    
    def _extract_recommendation_fields(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Extract fields from recommendation for comparison."""
        return {
            "stage": recommendation.get("stage"),
            "failure_type": recommendation.get("failure_type"),
            "likely_cause": recommendation.get("likely_cause"),
            "recovery_hint": recommendation.get("recovery_hint"),
            "confidence": recommendation.get("confidence"),
            "hint_certainty": recommendation.get("hint_certainty"),
        }
    
    def compare_decision_traces(
        self,
        trace1: Dict[str, Any],
        trace2: Dict[str, Any],
    ) -> PatternComparison:
        """Compare two decision traces.
        
        Args:
            trace1: First decision trace dict
            trace2: Second decision trace dict
        
        Returns:
            PatternComparison with observed similarities and differences
        """
        # Extract fields for comparison
        fields1 = self._extract_decision_trace_fields(trace1)
        fields2 = self._extract_decision_trace_fields(trace2)
        
        # Find shared and different fields
        shared, differences = self._compare_fields(fields1, fields2)
        
        # Calculate heuristic similarity
        similarity = self._calculate_heuristic_similarity(fields1, fields2, shared, differences)
        
        comparison = PatternComparison(
            comparison_id=f"comp_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            pattern_type="decision_trace",
            pattern1_id=trace1.get("trace_id", "unknown"),
            pattern2_id=trace2.get("trace_id", "unknown"),
            shared_fields=shared,
            differences=differences,
            observed_similarity=similarity["observed"],
            inferred_similarity_score=similarity["score"],
            confidence_impact=self._compare_confidence(
                trace1.get("confidence_level", "medium"),
                trace2.get("confidence_level", "medium"),
            ),
            recommendation_impact=None,
            rationale_impact=self._compare_rationale(
                trace1.get("rationale"),
                trace2.get("rationale"),
            ),
            safe_action_impact=self._compare_safe_next_action(
                trace1.get("safe_next_action"),
                trace2.get("safe_next_action"),
            ),
        )
        
        self._comparisons.append(comparison)
        self._track_repeated_patterns(comparison)
        
        return comparison
    
    def _extract_decision_trace_fields(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        """Extract fields from decision trace for comparison."""
        return {
            "correlation_ids": trace.get("correlation_ids"),
            "rationale": trace.get("rationale"),
            "confidence_level": trace.get("confidence_level"),
            "confidence_explanation": trace.get("confidence_explanation"),
            "safe_next_action": trace.get("safe_next_action"),
            "failure_classification": trace.get("failure_classification"),
            "likely_cause": trace.get("likely_cause"),
        }
    
    def compare_by_correlation(
        self,
        correlation_type: str,
        correlation_id: str,
        cases: List[Dict[str, Any]],
        case_type: str = "recommendation",
    ) -> List[PatternComparison]:
        """Compare cases by correlation ID.
        
        Args:
            correlation_type: Type of correlation (flow_id, request_id, etc.)
            correlation_id: The correlation ID value
            cases: List of case dicts to compare
            case_type: Type of cases ("recommendation" or "decision_trace")
        
        Returns:
            List of PatternComparisons for each pair of cases
        """
        comparisons = []
        
        # Filter cases by correlation
        matching_cases = []
        for case in cases:
            correlation_ids = case.get("correlation_ids", {})
            if correlation_ids.get(correlation_type) == correlation_id:
                matching_cases.append(case)
        
        # Compare pairs
        for i in range(len(matching_cases)):
            for j in range(i + 1, len(matching_cases)):
                if case_type == "recommendation":
                    comparison = self.compare_recommendations(
                        matching_cases[i],
                        matching_cases[j],
                        {"correlation_type": correlation_type, "correlation_id": correlation_id},
                    )
                else:
                    comparison = self.compare_decision_traces(
                        matching_cases[i],
                        matching_cases[j],
                    )
                comparisons.append(comparison)
        
        return comparisons
    
    def _compare_fields(
        self,
        fields1: Dict[str, Any],
        fields2: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Tuple[Any, Any]]]:
        """Compare two field sets and return shared and different fields."""
        shared = {}
        differences = {}
        
        all_keys = set(fields1.keys()) | set(fields2.keys())
        
        for key in all_keys:
            val1 = fields1.get(key)
            val2 = fields2.get(key)
            
            if val1 == val2:
                shared[key] = val1
            else:
                differences[key] = (val1, val2)
        
        return shared, differences
    
    def _calculate_heuristic_similarity(
        self,
        fields1: Dict[str, Any],
        fields2: Dict[str, Any],
        shared: Dict[str, Any],
        differences: Dict[str, Tuple[Any, Any]],
    ) -> Dict[str, Any]:
        """Calculate heuristic similarity score.
        
        Returns dict with:
        - observed: low/medium/high (heuristic label)
        - score: 0.0-1.0 (heuristic estimate)
        
        Note: This is NOT certainty — it's a heuristic estimate.
        """
        total_fields = len(set(fields1.keys()) | set(fields2.keys()))
        if total_fields == 0:
            return {"observed": "low", "score": 0.0}
        
        # Count matching fields
        matching_count = len(shared)
        similarity_score = matching_count / total_fields
        
        # Map to heuristic labels
        if similarity_score >= 0.7:
            observed = "high"
        elif similarity_score >= 0.4:
            observed = "medium"
        else:
            observed = "low"
        
        return {"observed": observed, "score": round(similarity_score, 2)}
    
    def _compare_confidence(
        self,
        conf1: Optional[str],
        conf2: Optional[str],
    ) -> Optional[str]:
        """Compare confidence levels."""
        if conf1 is None or conf2 is None:
            return None
        
        if conf1 == conf2:
            return "same"
        elif conf1 in ["high", "very_high"] and conf2 in ["high", "very_high"]:
            return "similar_high"
        elif conf1 in ["low", "very_low"] and conf2 in ["low", "very_low"]:
            return "similar_low"
        else:
            return "different"
    
    def _compare_recovery_hints(
        self,
        hint1: Optional[str],
        hint2: Optional[str],
    ) -> Optional[str]:
        """Compare recovery hints."""
        if hint1 is None or hint2 is None:
            return None
        
        if hint1 == hint2:
            return "identical"
        else:
            return "different"
    
    def _compare_rationale(
        self,
        rationale1: Optional[str],
        rationale2: Optional[str],
    ) -> Optional[str]:
        """Compare rationale explanations."""
        if rationale1 is None or rationale2 is None:
            return None
        
        if rationale1 == rationale2:
            return "identical"
        else:
            return "different"
    
    def _compare_safe_next_action(
        self,
        action1: Optional[Dict[str, Any]],
        action2: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        """Compare safe-next-action structures."""
        if action1 is None or action2 is None:
            return None
        
        action1_str = json.dumps(action1, sort_keys=True)
        action2_str = json.dumps(action2, sort_keys=True)
        
        if action1_str == action2_str:
            return "identical"
        else:
            return "different"
    
    def _track_repeated_patterns(self, comparison: PatternComparison) -> None:
        """Track repeated patterns in comparisons."""
        # Track shared field patterns
        for field_name, value in comparison.shared_fields.items():
            key = f"shared_{field_name}={value}"
            self._repeated_patterns[key] = self._repeated_patterns.get(key, 0) + 1
        
        # Track similar cases
        if comparison.observed_similarity in ["high", "medium"]:
            key = f"similarity_{comparison.observed_similarity}"
            self._repeated_patterns[key] = self._repeated_patterns.get(key, 0) + 1
    
    def identify_repeated_patterns(self) -> Dict[str, int]:
        """Identify repeated patterns from comparisons.
        
        Returns dict of pattern -> frequency (lightweight, descriptive).
        
        This is NOT a clustering/analytics engine — just descriptive counting.
        """
        return dict(self._repeated_patterns)
    
    def get_comparison_summary(self) -> ComparisonSummary:
        """Generate operator-readable comparison summary."""
        if not self._comparisons:
            return ComparisonSummary(
                summary_id=f"summary_{uuid.uuid4().hex[:12]}",
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                total_comparisons=0,
                pattern_types={},
                shared_patterns={},
                repeated_patterns={},
                operator_readable="No comparisons available.",
                machine_readable=json.dumps({"error": "No comparisons available"}, indent=2),
            )
        
        # Count pattern types
        pattern_types: Dict[str, int] = {}
        for comp in self._comparisons:
            pt = comp.pattern_type
            pattern_types[pt] = pattern_types.get(pt, 0) + 1
        
        # Get repeated patterns
        repeated = self.identify_repeated_patterns()
        
        # Generate operator-readable summary
        lines = [
            "=" * 70,
            "RECOVERY PATTERN COMPARISON SUMMARY",
            "=" * 70,
            f"Summary ID: {uuid.uuid4().hex[:12]}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
            f"Total Comparisons: {len(self._comparisons)}",
            "",
            "-" * 70,
            "PATTERN TYPES",
            "-" * 70,
        ]
        
        for pt, count in sorted(pattern_types.items()):
            lines.append(f"  {pt}: {count}")
        
        lines.extend([
            "",
            "-" * 70,
            "OBSERVED SHARED PATTERNS (frequency)",
            "-" * 70,
        ])
        
        # Show most common shared patterns
        for pattern, freq in sorted(repeated.items(), key=lambda x: x[1], reverse=True)[:5]:
            lines.append(f"  {pattern}: {freq}")
        
        lines.extend([
            "",
            "-" * 70,
            "HEURISTIC NOTE",
            "-" * 70,
            "The similarity assessment is heuristic, not certain.",
            "",
            "Key distinctions:",
            "- Observed shared fields: What's actually the same",
            "- Observed differences: What differs",
            "- Inferred similarity: Heuristic assessment (not certainty)",
            "",
            "This comparison layer provides pattern visibility, not predictive",
            "analysis. Similarity scores indicate pattern overlap, not guarantee",
            "of successful recovery approaches.",
            "",
            "=" * 70,
        ])
        
        operator_summary = "\n".join(lines)
        machine_summary = json.dumps({
            "summary_id": uuid.uuid4().hex[:12],
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "total_comparisons": len(self._comparisons),
            "pattern_types": pattern_types,
            "shared_patterns": repeated,
            "comparisons": [c.to_dict() for c in self._comparisons],
        }, indent=2)
        
        return ComparisonSummary(
            summary_id=uuid.uuid4().hex[:12],
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            total_comparisons=len(self._comparisons),
            pattern_types=pattern_types,
            shared_patterns=repeated,
            repeated_patterns=repeated,
            operator_readable=operator_summary,
            machine_readable=machine_summary,
        )
    
    def export_operator_readable(self) -> str:
        """Export comparison summary as operator-readable string."""
        summary = self.get_comparison_summary()
        return summary.operator_readable
    
    def export_machine_readable(self) -> str:
        """Export comparison summary as JSON string."""
        summary = self.get_comparison_summary()
        return summary.machine_readable


# ============================================================================
# INTEGRATION HELPERS (Additive Only)
# ============================================================================


def integrate_with_v75_recommendations(comp: RecoveryPatternComparison) -> Dict[str, Any]:
    """Integration hook for v75 recommendations — read-only comparison only.
    
    No behavior changes to existing recommendation logic.
    """
    return {"hooked": True, "measures": "recommendation_pattern_comparison"}


def integrate_with_v78_decision_traces(comp: RecoveryPatternComparison) -> Dict[str, Any]:
    """Integration hook for v78 decision traces — read-only comparison only.
    
    No behavior changes to existing trace logic.
    """
    return {"hooked": True, "measures": "decision_trace_pattern_comparison"}
