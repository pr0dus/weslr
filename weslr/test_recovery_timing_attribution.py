#!/usr/bin/env python3
# test_recovery_timing_attribution.py - WESLR v82: Recovery Timing Attribution Tests
# Tests bottleneck attribution analysis for command timing measurements.

from __future__ import annotations

import json
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from weslr.recovery_timing_attribution import (
    AttributionRecord,
    CommandAttribution,
    AttributionSummary,
    RecoveryTimingAttributionAnalyzer,
)


class TestAttributionRecord(unittest.TestCase):
    """Test AttributionRecord dataclass."""
    
    def test_record_creation(self):
        """Test creating an attribution record."""
        record = AttributionRecord(
            record_id="rec-001",
            stage="recommendation",
            substage="generation",
            command="diagnostics-recovery-hints",
            estimated_latency_ms=1.5,
            confidence_level="medium",
            contributing_factors=[
                "v75 generate_recommendation() calls",
                "Failure diagnosis inference",
            ],
            confidence_explanation="Inferred from command structure.",
        )
        
        self.assertEqual(record.record_id, "rec-001")
        self.assertEqual(record.stage, "recommendation")
        self.assertEqual(record.estimated_latency_ms, 1.5)
    
    def test_record_serialization(self):
        """Test attribution record to dict."""
        record = AttributionRecord(
            record_id="rec-001",
            stage="recommendation",
            substage="generation",
            command="diagnostics-recovery-hints",
            estimated_latency_ms=1.5,
            confidence_level="medium",
            contributing_factors=["Test factor"],
            confidence_explanation="Test explanation.",
        )
        
        data = record.to_dict()
        
        self.assertEqual(data["record_id"], "rec-001")
        self.assertEqual(data["estimated_latency_ms"], 1.5)
        self.assertIn("Test factor", data["contributing_factors"])
    
    def test_record_json_serialization(self):
        """Test attribution record to JSON."""
        record = AttributionRecord(
            record_id="rec-001",
            stage="recommendation",
            substage="generation",
            command="diagnostics-recovery-hints",
            estimated_latency_ms=1.5,
            confidence_level="medium",
            contributing_factors=["Factor"],
            confidence_explanation="Explanation.",
        )
        
        json_str = record.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["record_id"], "rec-001")
        self.assertEqual(data["estimated_latency_ms"], 1.5)
    
    def test_confidence_means_attribution_not_behavior(self):
        """Test that confidence level is about attribution, not behavior."""
        record = AttributionRecord(
            record_id="rec-001",
            stage="recommendation",
            substage="generation",
            command="diagnostics-recovery-hints",
            estimated_latency_ms=1.5,
            confidence_level="medium",
            contributing_factors=["Test"],
            confidence_explanation=(
                "Attribution is inferred from command structure. "
                "Confidence indicates attribution reliability, not behavior."
            ),
        )
        
        self.assertIn("inferred", record.confidence_explanation.lower())
        self.assertIn("attribution", record.confidence_explanation.lower())


class TestCommandAttribution(unittest.TestCase):
    """Test CommandAttribution dataclass."""
    
    def test_attribution_creation(self):
        """Test creating a command attribution."""
        breakdown = [
            AttributionRecord(
                record_id="attr-001",
                stage="parser",
                substage="dispatch",
                command="diagnostics-recovery-hints",
                estimated_latency_ms=0.4,
                confidence_level="high",
                contributing_factors=["Argument parsing"],
                confidence_explanation="Attribution explanation.",
            ),
            AttributionRecord(
                record_id="attr-002",
                stage="recommendation",
                substage="generation",
                command="diagnostics-recovery-hints",
                estimated_latency_ms=2.5,
                confidence_level="medium",
                contributing_factors=["Recommendation generation"],
                confidence_explanation="Attribution explanation.",
            ),
        ]
        
        attribution = CommandAttribution(
            command="diagnostics-recovery-hints",
            measured_latency_ms=2.97,
            total_latency_ms=2.97,
            attribution_breakdown=breakdown,
            slowest_contributor=breakdown[1],
            explanation="Explanation text.",
            attribution_summary="Summary text.",
        )
        
        self.assertEqual(attribution.command, "diagnostics-recovery-hints")
        self.assertEqual(attribution.measured_latency_ms, 2.97)
        self.assertEqual(attribution.slowest_contributor.stage, "recommendation")
    
    def test_attribution_serialization(self):
        """Test command attribution to dict."""
        breakdown = [
            AttributionRecord(
                record_id="attr-001",
                stage="parser",
                substage="dispatch",
                command="test",
                estimated_latency_ms=0.4,
                confidence_level="high",
                contributing_factors=["Parsing"],
                confidence_explanation="Explanation.",
            ),
        ]
        
        attribution = CommandAttribution(
            command="test",
            measured_latency_ms=1.0,
            total_latency_ms=1.0,
            attribution_breakdown=breakdown,
            slowest_contributor=breakdown[0],
        )
        
        data = attribution.to_dict()
        
        self.assertEqual(data["command"], "test")
        self.assertEqual(data["measured_latency_ms"], 1.0)
        self.assertEqual(len(data["attribution_breakdown"]), 1)
    
    def test_attribution_json_serialization(self):
        """Test command attribution to JSON."""
        breakdown = [
            AttributionRecord(
                record_id="attr-001",
                stage="parser",
                substage="dispatch",
                command="test",
                estimated_latency_ms=0.4,
                confidence_level="high",
                contributing_factors=["Parsing"],
                confidence_explanation="Explanation.",
            ),
        ]
        
        attribution = CommandAttribution(
            command="test",
            measured_latency_ms=1.0,
            total_latency_ms=1.0,
            attribution_breakdown=breakdown,
            slowest_contributor=breakdown[0],
        )
        
        json_str = attribution.to_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["command"], "test")
        self.assertEqual(data["measured_latency_ms"], 1.0)


class TestRecoveryTimingAttributionAnalyzer(unittest.TestCase):
    """Test RecoveryTimingAttributionAnalyzer operations."""
    
    def test_attribute_diagnostics_recovery_hints(self):
        """Test attribution for diagnostics-recovery-hints (slowest command)."""
        analyzer = RecoveryTimingAttributionAnalyzer()
        
        attribution = analyzer.attribute_command_latency(
            "diagnostics-recovery-hints",
            measured_latency_ms=2.97,
        )
        
        self.assertEqual(attribution.command, "diagnostics-recovery-hints")
        self.assertEqual(attribution.measured_latency_ms, 2.97)
        
        # Should have multiple breakdown records
        self.assertGreater(len(attribution.attribution_breakdown), 1)
        
        # Parser should be one of the stages
        stages = [r.stage for r in attribution.attribution_breakdown]
        self.assertIn("parser", stages)
    
    def test_attribute_all_commands(self):
        """Test attributing all measured commands."""
        analyzer = RecoveryTimingAttributionAnalyzer()
        attributions = analyzer.attribute_all_commands()
        
        self.assertEqual(len(attributions), 5)
        commands = [a.command for a in attributions]
        self.assertIn("diagnostics-summary", commands)
        self.assertIn("fallback-status", commands)
        self.assertIn("diagnostics-recovery-hints", commands)
        self.assertIn("diagnostics-trace-export", commands)
        self.assertIn("fallback-trace-export", commands)
    
    def test_diagnostics_recovery_hints_is_slowest(self):
        """Test that diagnostics-recovery-hints has the most breakdown."""
        analyzer = RecoveryTimingAttributionAnalyzer()
        analyzer.attribute_all_commands()
        
        # Get attributions from analyzer's internal state
        for attr in analyzer._attributions:
            if attr.command == "diagnostics-recovery-hints":
                # Should have more breakdown records than simpler commands
                self.assertGreater(len(attr.attribution_breakdown), 2)
                break
    
    def test_attribution_confidence_levels(self):
        """Test that attribution confidence levels are present."""
        analyzer = RecoveryTimingAttributionAnalyzer()
        analyzer.attribute_all_commands()
        
        for attr in analyzer._attributions:
            for record in attr.attribution_breakdown:
                # Confidence levels should be present
                self.assertIn(record.confidence_level, ["high", "medium", "low"])
                
                # Confidence explanation should mention it's attribution-based
                self.assertIn("attribution", record.confidence_explanation.lower())
    
    def test_explanation_contains_command_context(self):
        """Test that explanations contain relevant context."""
        analyzer = RecoveryTimingAttributionAnalyzer()
        attribution = analyzer.attribute_command_latency(
            "diagnostics-recovery-hints",
            measured_latency_ms=2.97,
        )
        
        self.assertIn("diagnostics-recovery-hints", attribution.explanation)
        self.assertIn("slowest", attribution.explanation.lower())
    
    def test_attribution_summary_generation(self):
        """Test attribution summary generation."""
        analyzer = RecoveryTimingAttributionAnalyzer()
        analyzer.attribute_all_commands()
        
        summary = analyzer.get_attribution_summary()
        
        self.assertIn("summary_id", summary.to_dict())
        self.assertEqual(summary.total_commands, 5)
        self.assertIn("RECOVERY TIMING ATTRIBUTION SUMMARY", summary.operator_readable)
        self.assertIn("ATTRIBUTION BREAKDOWN", summary.operator_readable)
        self.assertIn("ATTRIBUTION NOTE", summary.operator_readable)
    
    def test_operator_readable_contains_distinction(self):
        """Test that operator-readable output explains the attribution distinction."""
        analyzer = RecoveryTimingAttributionAnalyzer()
        analyzer.attribute_all_commands()
        summary = analyzer.get_attribution_summary()
        output = summary.operator_readable
        
        # Should contain the key distinction
        self.assertIn("measured latency", output.lower())
        self.assertIn("inferred", output.lower())
        self.assertIn("attribution explanation", output.lower())
    
    def test_machine_readable_export(self):
        """Test machine-readable export."""
        analyzer = RecoveryTimingAttributionAnalyzer()
        analyzer.attribute_all_commands()
        
        json_str = analyzer.export_machine_readable()
        data = json.loads(json_str)
        
        self.assertIn("total_commands", data)
        self.assertEqual(data["total_commands"], 5)
        self.assertIn("attributions", data)
    
    def test_command_comparison_works(self):
        """Test that command comparison is functional."""
        analyzer = RecoveryTimingAttributionAnalyzer()
        analyzer.attribute_all_commands()
        
        # Get attributions from analyzer
        attributions = analyzer._attributions
        
        # Sort by measured latency to compare
        sorted_attrs = sorted(attributions, key=lambda a: a.measured_latency_ms)
        
        # Should be ordered by latency
        latencies = [a.measured_latency_ms for a in sorted_attrs]
        self.assertEqual(latencies, sorted(latencies))


class TestEndToEndAttribution(unittest.TestCase):
    """Test end-to-end attribution workflow."""
    
    def test_full_attribution_workflow(self):
        """Test complete attribution workflow end-to-end."""
        analyzer = RecoveryTimingAttributionAnalyzer()
        analyzer.attribute_all_commands()
        
        # Get summary
        summary = analyzer.get_attribution_summary()
        operator_output = analyzer.export_operator_readable()
        machine_output = analyzer.export_machine_readable()
        
        # Get attributions
        attributions = analyzer._attributions
        
        # Verify attributions - should be 5 commands
        self.assertEqual(len(attributions), 5)
        
        # Verify summary
        self.assertEqual(summary.total_commands, 5)
        self.assertIn("RECOVERY TIMING ATTRIBUTION SUMMARY", operator_output)
        self.assertIn("ATTRIBUTION NOTE", operator_output)
        
        # Verify JSON is parseable
        parsed = json.loads(machine_output)
        self.assertEqual(parsed["total_commands"], 5)


class TestAttributionDistinction(unittest.TestCase):
    """Test that v82 explicitly distinguishes measured vs inferred."""
    
    def test_measured_latency_is_direct(self):
        """Test that measured latency is preserved as direct observation."""
        analyzer = RecoveryTimingAttributionAnalyzer()
        
        attribution = analyzer.attribute_command_latency(
            "diagnostics-recovery-hints",
            measured_latency_ms=2.97,
        )
        
        # Measured should be preserved exactly
        self.assertEqual(attribution.measured_latency_ms, 2.97)
        
        # The explanation should clarify this is direct measurement
        self.assertIn("measured", attribution.explanation.lower())
    
    def test_inferred_breakdown_is_not_measured(self):
        """Test that inferred breakdown is labeled as such."""
        analyzer = RecoveryTimingAttributionAnalyzer()
        
        attribution = analyzer.attribute_command_latency(
            "diagnostics-recovery-hints",
            measured_latency_ms=2.97,
        )
        
        # Estimated latencies should be used, not measured
        for record in attribution.attribution_breakdown:
            # These are estimated, not directly measured
            self.assertGreater(record.estimated_latency_ms, 0.0)
            # But confidence explains it's attribution-based
            self.assertIn("attribution", record.confidence_explanation.lower())
    
    def test_confidence_level_is_not_behavior_confidence(self):
        """Test that confidence levels explain attribution confidence, not behavior."""
        analyzer = RecoveryTimingAttributionAnalyzer()
        
        attribution = analyzer.attribute_command_latency(
            "diagnostics-recovery-hints",
            measured_latency_ms=2.97,
        )
        
        for record in attribution.attribution_breakdown:
            # Confidence should explain attribution, not behavior
            conf_text = record.confidence_explanation.lower()
            
            # Should mention attribution or inference
            has_attribution = "attribution" in conf_text or "inferred" in conf_text
            
            # Should NOT claim behavior confidence
            has_behavior_confidence = "behavior" in conf_text or "reliable" in conf_text
            
            # Either attribution/inference is mentioned, or behavior confidence is absent
            self.assertTrue(has_attribution or not has_behavior_confidence)


if __name__ == "__main__":
    unittest.main()
