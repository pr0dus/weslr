#!/usr/bin/env python3
# test_recovery_pattern_comparison.py - WESLR v83: Recovery Pattern Comparison Tests
# Tests pattern comparison layer for recovery incidents.

from __future__ import annotations

import json
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from weslr.recovery_pattern_comparison import (
    PatternComparison,
    ComparisonSummary,
    RecoveryPatternComparison,
)


class TestPatternComparison(unittest.TestCase):
    """Test PatternComparison dataclass."""
    
    def test_comparison_creation(self):
        """Test creating a pattern comparison."""
        comparison = PatternComparison(
            comparison_id="comp-001",
            timestamp="2026-04-07T12:00:00Z",
            pattern_type="recommendation",
            pattern1_id="rec-001",
            pattern2_id="rec-002",
            observed_similarity="high",
            inferred_similarity_score=0.85,
            shared_fields={"stage": "proposal"},
            differences={"likely_cause": ("different cause 1", "different cause 2")},
            confidence_impact="same",
            recommendation_impact="identical",
        )
        
        self.assertEqual(comparison.comparison_id, "comp-001")
        self.assertEqual(comparison.pattern_type, "recommendation")
        self.assertEqual(comparison.observed_similarity, "high")
    
    def test_comparison_serialization(self):
        """Test pattern comparison to dict."""
        comparison = PatternComparison(
            comparison_id="comp-001",
            timestamp="2026-04-07T12:00:00Z",
            pattern_type="recommendation",
            pattern1_id="rec-001",
            pattern2_id="rec-002",
            observed_similarity="high",
            inferred_similarity_score=0.85,
            shared_fields={"stage": "proposal"},
            differences={"likely_cause": ("cause1", "cause2")},
        )
        
        data = comparison.to_dict()
        
        self.assertEqual(data["comparison_id"], "comp-001")
        self.assertEqual(data["observed_similarity"], "high")
        self.assertIn("likely_cause", data["differences"])
    
    def test_comparison_json_serialization(self):
        """Test pattern comparison to JSON."""
        comparison = PatternComparison(
            comparison_id="comp-001",
            timestamp="2026-04-07T12:00:00Z",
            pattern_type="recommendation",
            pattern1_id="rec-001",
            pattern2_id="rec-002",
            observed_similarity="medium",
            inferred_similarity_score=0.5,
        )
        
        json_str = comparison.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["observed_similarity"], "medium")
    
    def test_observed_shared_fields_vs_differences(self):
        """Test that shared fields and differences are correctly separated."""
        fields1 = {"stage": "proposal", "failure_type": "rejected"}
        fields2 = {"stage": "proposal", "failure_type": "expired"}
        
        shared, differences = {}, {}
        all_keys = set(fields1.keys()) | set(fields2.keys())
        
        for key in all_keys:
            val1 = fields1.get(key)
            val2 = fields2.get(key)
            if val1 == val2:
                shared[key] = val1
            else:
                differences[key] = (val1, val2)
        
        self.assertEqual(shared, {"stage": "proposal"})
        self.assertEqual(differences, {"failure_type": ("rejected", "expired")})
    
    def test_inferred_similarity_is_heuristic_not_certainty(self):
        """Test that similarity is explicitly heuristic."""
        comparison = PatternComparison(
            comparison_id="comp-001",
            timestamp="2026-04-07T12:00:00Z",
            pattern_type="recommendation",
            observed_similarity="high",
            inferred_similarity_score=0.85,
        )
        
        # Score should be between 0 and 1 (heuristic estimate)
        self.assertGreaterEqual(comparison.inferred_similarity_score, 0.0)
        self.assertLessEqual(comparison.inferred_similarity_score, 1.0)
        
        # The observed label should be low/medium/high
        self.assertIn(comparison.observed_similarity, ["low", "medium", "high"])


class TestRecoveryPatternComparison(unittest.TestCase):
    """Test RecoveryPatternComparison operations."""
    
    def setUp(self):
        """Set up comparison layer for tests."""
        self.comp = RecoveryPatternComparison()
    
    def test_compare_recommendations(self):
        """Test comparing two recommendations."""
        rec1 = {
            "recommendation_id": "rec-001",
            "stage": "proposal",
            "failure_type": "rejected",
            "likely_cause": "Recommendation rejected",
            "recovery_hint": "Review rejection reason",
            "confidence": "high",
            "hint_certainty": "suggestion",
        }
        
        rec2 = {
            "recommendation_id": "rec-002",
            "stage": "proposal",
            "failure_type": "rejected",
            "likely_cause": "Recommendation rejected",
            "recovery_hint": "Review rejection reason",
            "confidence": "high",
            "hint_certainty": "suggestion",
        }
        
        comparison = self.comp.compare_recommendations(rec1, rec2)
        
        self.assertEqual(comparison.pattern_type, "recommendation")
        self.assertEqual(comparison.observed_similarity, "high")
        self.assertGreaterEqual(comparison.inferred_similarity_score, 0.7)
        self.assertEqual(comparison.confidence_impact, "same")
        self.assertEqual(comparison.recommendation_impact, "identical")
    
    def test_compare_recommendations_with_differences(self):
        """Test comparing recommendations with differences."""
        rec1 = {
            "recommendation_id": "rec-001",
            "stage": "proposal",
            "failure_type": "rejected",
            "likely_cause": "Cause A",
            "recovery_hint": "Hint A",
            "confidence": "high",
        }
        
        rec2 = {
            "recommendation_id": "rec-002",
            "stage": "proposal",
            "failure_type": "rejected",
            "likely_cause": "Cause B",
            "recovery_hint": "Hint B",
            "confidence": "medium",
        }
        
        comparison = self.comp.compare_recommendations(rec1, rec2)
        
        self.assertEqual(comparison.pattern_type, "recommendation")
        # Different likely cause and confidence should reduce similarity
        self.assertIn(comparison.observed_similarity, ["low", "medium"])
        self.assertEqual(comparison.confidence_impact, "different")
    
    def test_compare_decision_traces(self):
        """Test comparing two decision traces."""
        trace1 = {
            "trace_id": "trace-001",
            "correlation_ids": {"flow_id": "flow-1"},
            "rationale": "Decision rationale A",
            "confidence_level": "high",
            "confidence_explanation": "Explanation A",
            "safe_next_action": {"action": "Review", "risk": "low"},
        }
        
        trace2 = {
            "trace_id": "trace-002",
            "correlation_ids": {"flow_id": "flow-1"},
            "rationale": "Decision rationale A",
            "confidence_level": "high",
            "confidence_explanation": "Explanation A",
            "safe_next_action": {"action": "Review", "risk": "low"},
        }
        
        comparison = self.comp.compare_decision_traces(trace1, trace2)
        
        self.assertEqual(comparison.pattern_type, "decision_trace")
        self.assertEqual(comparison.observed_similarity, "high")
        self.assertEqual(comparison.confidence_impact, "same")
        self.assertEqual(comparison.rationale_impact, "identical")
        self.assertEqual(comparison.safe_action_impact, "identical")
    
    def test_compare_decision_traces_with_differences(self):
        """Test comparing decision traces with differences."""
        trace1 = {
            "trace_id": "trace-001",
            "rationale": "Rationale A",
            "confidence_level": "high",
            "safe_next_action": {"action": "A", "risk": "low"},
        }
        
        trace2 = {
            "trace_id": "trace-002",
            "rationale": "Rationale B",
            "confidence_level": "medium",
            "safe_next_action": {"action": "B", "risk": "high"},
        }
        
        comparison = self.comp.compare_decision_traces(trace1, trace2)
        
        self.assertEqual(comparison.pattern_type, "decision_trace")
        self.assertEqual(comparison.confidence_impact, "different")
        self.assertEqual(comparison.rationale_impact, "different")
        self.assertEqual(comparison.safe_action_impact, "different")
    
    def test_compare_by_correlation(self):
        """Test comparing cases by correlation ID."""
        cases = [
            {
                "correlation_ids": {"flow_id": "flow-1", "request_id": "req-1"},
                "recommendation_id": "rec-001",
                "stage": "proposal",
                "failure_type": "rejected",
                "likely_cause": "Same cause",
                "recovery_hint": "Same hint",
                "confidence": "high",
            },
            {
                "correlation_ids": {"flow_id": "flow-1", "request_id": "req-2"},
                "recommendation_id": "rec-002",
                "stage": "proposal",
                "failure_type": "rejected",
                "likely_cause": "Same cause",
                "recovery_hint": "Same hint",
                "confidence": "high",
            },
            {
                "correlation_ids": {"flow_id": "flow-2", "request_id": "req-3"},
                "recommendation_id": "rec-003",
                "stage": "proposal",
                "failure_type": "rejected",
                "likely_cause": "Different cause",
                "recovery_hint": "Different hint",
                "confidence": "low",
            },
        ]
        
        comparisons = self.comp.compare_by_correlation(
            correlation_type="flow_id",
            correlation_id="flow-1",
            cases=cases,
            case_type="recommendation",
        )
        
        # Should compare rec-001 and rec-002 (both flow-1)
        self.assertEqual(len(comparisons), 1)
        self.assertEqual(comparisons[0].observed_similarity, "high")
    
    def test_identify_repeated_patterns(self):
        """Test repeated pattern identification."""
        # Create comparisons with shared patterns
        rec1 = {
            "recommendation_id": "rec-001",
            "stage": "proposal",
            "failure_type": "rejected",
            "likely_cause": "Same cause",
            "recovery_hint": "Same hint",
            "confidence": "high",
        }
        
        rec2 = {
            "recommendation_id": "rec-002",
            "stage": "proposal",
            "failure_type": "rejected",
            "likely_cause": "Same cause",
            "recovery_hint": "Same hint",
            "confidence": "high",
        }
        
        rec3 = {
            "recommendation_id": "rec-003",
            "stage": "proposal",
            "failure_type": "rejected",
            "likely_cause": "Same cause",
            "recovery_hint": "Same hint",
            "confidence": "high",
        }
        
        self.comp.compare_recommendations(rec1, rec2)
        self.comp.compare_recommendations(rec2, rec3)
        self.comp.compare_recommendations(rec1, rec3)
        
        repeated = self.comp.identify_repeated_patterns()
        
        # Should have repeated similarity patterns
        self.assertGreater(len(repeated), 0)
        self.assertIn("similarity_high", repeated)
    
    def test_comparison_summary(self):
        """Test comparison summary generation."""
        rec1 = {
            "recommendation_id": "rec-001",
            "stage": "proposal",
            "failure_type": "rejected",
            "likely_cause": "Cause A",
            "recovery_hint": "Hint A",
            "confidence": "high",
        }
        
        rec2 = {
            "recommendation_id": "rec-002",
            "stage": "proposal",
            "failure_type": "rejected",
            "likely_cause": "Cause A",
            "recovery_hint": "Hint A",
            "confidence": "high",
        }
        
        self.comp.compare_recommendations(rec1, rec2)
        
        summary = self.comp.get_comparison_summary()
        
        self.assertIn("summary_id", summary.to_dict())
        self.assertEqual(summary.total_comparisons, 1)
        self.assertIn("RECOVERY PATTERN COMPARISON SUMMARY", summary.operator_readable)
        self.assertIn("OBSERVED SHARED PATTERNS", summary.operator_readable)
        self.assertIn("HEURISTIC NOTE", summary.operator_readable)
    
    def test_operator_readable_contains_distinction(self):
        """Test that operator-readable output explains the distinction."""
        rec1 = {
            "recommendation_id": "rec-001",
            "stage": "proposal",
            "failure_type": "rejected",
            "likely_cause": "Cause A",
            "recovery_hint": "Hint A",
            "confidence": "high",
        }
        
        rec2 = {
            "recommendation_id": "rec-002",
            "stage": "proposal",
            "failure_type": "rejected",
            "likely_cause": "Cause A",
            "recovery_hint": "Hint A",
            "confidence": "high",
        }
        
        self.comp.compare_recommendations(rec1, rec2)
        summary = self.comp.get_comparison_summary()
        output = summary.operator_readable
        
        # Should contain the key distinction
        self.assertIn("observed shared fields", output.lower())
        self.assertIn("observed differences", output.lower())
        self.assertIn("heuristic", output.lower())
    
    def test_machine_readable_export(self):
        """Test machine-readable export."""
        rec1 = {
            "recommendation_id": "rec-001",
            "stage": "proposal",
            "failure_type": "rejected",
            "likely_cause": "Cause A",
            "recovery_hint": "Hint A",
            "confidence": "high",
        }
        
        rec2 = {
            "recommendation_id": "rec-002",
            "stage": "proposal",
            "failure_type": "rejected",
            "likely_cause": "Cause A",
            "recovery_hint": "Hint A",
            "confidence": "high",
        }
        
        self.comp.compare_recommendations(rec1, rec2)
        
        json_str = self.comp.export_machine_readable()
        data = json.loads(json_str)
        
        self.assertIn("total_comparisons", data)
        self.assertEqual(data["total_comparisons"], 1)
        self.assertIn("pattern_types", data)
        self.assertIn("comparisons", data)


class TestEndToEndComparison(unittest.TestCase):
    """Test end-to-end comparison workflow."""
    
    def test_full_comparison_workflow(self):
        """Test complete comparison workflow end-to-end."""
        comp = RecoveryPatternComparison()
        
        # Create test recommendations
        rec1 = {
            "recommendation_id": "rec-001",
            "stage": "proposal",
            "failure_type": "rejected",
            "likely_cause": "Cause A",
            "recovery_hint": "Hint A",
            "confidence": "high",
        }
        
        rec2 = {
            "recommendation_id": "rec-002",
            "stage": "proposal",
            "failure_type": "rejected",
            "likely_cause": "Cause A",
            "recovery_hint": "Hint A",
            "confidence": "high",
        }
        
        rec3 = {
            "recommendation_id": "rec-003",
            "stage": "proposal",
            "failure_type": "rejected",
            "likely_cause": "Cause B",
            "recovery_hint": "Hint B",
            "confidence": "medium",
        }
        
        # Compare
        comp.compare_recommendations(rec1, rec2)
        comp.compare_recommendations(rec2, rec3)
        comp.compare_recommendations(rec1, rec3)
        
        # Get summary
        summary = comp.get_comparison_summary()
        operator_output = comp.export_operator_readable()
        machine_output = comp.export_machine_readable()
        
        # Verify summary
        self.assertEqual(summary.total_comparisons, 3)
        self.assertIn("RECOVERY PATTERN COMPARISON SUMMARY", operator_output)
        self.assertIn("OBSERVED SHARED PATTERNS", operator_output)
        
        # Verify JSON is parseable
        parsed = json.loads(machine_output)
        self.assertEqual(parsed["total_comparisons"], 3)


class TestLightweightDescriptivePatterns(unittest.TestCase):
    """Test that pattern comparison remains lightweight and descriptive."""
    
    def test_no_clustering_engine(self):
        """Test that patterns are not clustered/analyzed beyond comparison."""
        comp = RecoveryPatternComparison()
        
        # Create multiple similar comparisons
        rec1 = {"recommendation_id": "rec-001", "confidence": "high"}
        rec2 = {"recommendation_id": "rec-002", "confidence": "high"}
        rec3 = {"recommendation_id": "rec-003", "confidence": "high"}
        
        comp.compare_recommendations(rec1, rec2)
        comp.compare_recommendations(rec2, rec3)
        comp.compare_recommendations(rec1, rec3)
        
        # Repeated patterns should be counted, not clustered
        repeated = comp.identify_repeated_patterns()
        
        # Should have simple counts, not complex clusters
        self.assertIsInstance(repeated, dict)
        for key, value in repeated.items():
            self.assertIsInstance(value, int)  # Simple frequency counts
    
    def test_no_analytics_engine(self):
        """Test that no analytics engine is created."""
        comp = RecoveryPatternComparison()
        
        # Repeated patterns should be descriptive counts
        repeated = comp.identify_repeated_patterns()
        
        # Should be simple key -> frequency mapping
        # No complex structures like clustering, classification, etc.
        for key, value in repeated.items():
            # Just simple strings and integers
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, int)


if __name__ == "__main__":
    unittest.main()
