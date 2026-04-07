"""Tests for Recovery Recommendation Export + Replay Correlation (v76)

Behavioral tests for recommendation export, replay summaries, and
diagnostic integration with correlation IDs.

Test Doctrine version: 1.0.0 (2026-04-07)
"""

import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.recovery_recommendation_service import (
    RecoveryRecommendationService,
)
from weslr.recovery_recommendation_export import (
    RecoveryRecommendationExporter,
    RecoveryRecommendationReplay,
    RecoveryRecommendationSummaryBuilder,
    create_recommendation_exporter,
    create_recommendation_replay,
    create_recommendation_summary_builder,
    integrate_with_diagnostics,
)
from weslr.distributed_diagnostic_hooks import (
    FailureType,
    FailureStage,
)


# ============================================================================
# RECOVERY RECOMMENDATION EXPORTER MODEL TESTS
# ============================================================================


class TestRecoveryRecommendationExporterModel(unittest.TestCase):
    """Test recovery recommendation exporter data models."""

    def test_exporter_creation(self):
        """RecoveryRecommendationExporter created successfully."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        self.assertIsNotNone(exporter)

    def test_export_all_recommendations_empty(self):
        """Export all recommendations when empty."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        
        recommendations = exporter.export_all_recommendations()
        
        self.assertEqual(len(recommendations), 0)

    def test_export_all_recommendations_with_data(self):
        """Export all recommendations with data."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        
        # Add a recommendation
        service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={
                "flow_id": "flow-123",
                "request_id": "req-456",
            }
        )
        
        recommendations = exporter.export_all_recommendations()
        
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0]["stage"], FailureStage.PROPOSAL.value)
        self.assertEqual(recommendations[0]["failure_type"], FailureType.PROPOSAL_REJECTED.value)
        self.assertEqual(recommendations[0]["hint_certainty"], "suggestion")
        self.assertEqual(recommendations[0]["correlation_trace"]["flow_id"], "flow-123")
        self.assertEqual(recommendations[0]["correlation_trace"]["request_id"], "req-456")

    def test_export_by_flow(self):
        """Export recommendations grouped by flow ID."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        
        service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        service.generate_recommendation(
            stage=FailureStage.ENVELOPE.value,
            failure_type=FailureType.ENVELOPE_GATE_FAILED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        service.generate_recommendation(
            stage=FailureStage.DEADLINE.value,
            failure_type=FailureType.DEADLINE_BREACHED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-2"}
        )
        
        by_flow = exporter.export_by_flow()
        
        self.assertIn("flow-1", by_flow)
        self.assertIn("flow-2", by_flow)
        self.assertEqual(len(by_flow["flow-1"]), 2)
        self.assertEqual(len(by_flow["flow-2"]), 1)

    def test_export_by_stage(self):
        """Export recommendations grouped by failure stage."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        
        service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-2"}
        )
        
        by_stage = exporter.export_by_stage()
        
        self.assertIn(FailureStage.PROPOSAL.value, by_stage)
        self.assertIn(FailureStage.HANDSHAKE.value, by_stage)
        self.assertEqual(len(by_stage[FailureStage.PROPOSAL.value]), 1)
        self.assertEqual(len(by_stage[FailureStage.HANDSHAKE.value]), 1)

    def test_export_json(self):
        """Export recommendations as JSON string."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        
        service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        json_str = exporter.export_json()
        
        self.assertIn("flow_id", json_str)
        self.assertIn("flow-1", json_str)

    def test_export_json_pretty(self):
        """Export recommendations as pretty-printed JSON."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        
        service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        json_str = exporter.export_json(pretty=True)
        
        # Pretty JSON should have indentation
        self.assertIn("  ", json_str)


# ============================================================================
# RECOVERY RECOMMENDATION EXPORTER BEHAVIOR TESTS
# ============================================================================


class TestRecoveryRecommendationExporterBehavior(unittest.TestCase):
    """Test recovery recommendation exporter behavior."""

    def test_export_preserves_read_only(self):
        """Export does not modify underlying recommendations."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        
        service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        # Get recommendation count before export
        before_count = len(service.get_all_recommendations())
        
        # Export
        exporter.export_all_recommendations()
        
        # Check count unchanged
        after_count = len(service.get_all_recommendations())
        self.assertEqual(before_count, after_count)

    def test_export_preserves_hint_certainty(self):
        """Export preserves hint_certainty as 'suggestion'."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        
        rec = service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        exported = exporter._export_recommendation(rec)
        
        self.assertEqual(exported["hint_certainty"], "suggestion")

    def test_export_includes_all_correlation_ids(self):
        """Export includes all correlation IDs."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        
        rec = service.generate_recommendation(
            stage=FailureStage.ENVELOPE.value,
            failure_type=FailureType.ENVELOPE_GATE_FAILED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={
                "flow_id": "flow-1",
                "request_id": "req-1",
                "handshake_id": "hs-1",
                "deadline_id": "dl-1",
            }
        )
        
        exported = exporter._export_recommendation(rec)
        
        trace = exported["correlation_trace"]
        self.assertEqual(trace["flow_id"], "flow-1")
        self.assertEqual(trace["request_id"], "req-1")
        self.assertEqual(trace["handshake_id"], "hs-1")
        self.assertEqual(trace["deadline_id"], "dl-1")


# ============================================================================
# RECOVERY RECOMMENDATION REPLAY MODEL TESTS
# ============================================================================


class TestRecoveryRecommendationReplayModel(unittest.TestCase):
    """Test recovery recommendation replay data models."""

    def test_replay_creation(self):
        """RecoveryRecommendationReplay created successfully."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        replay = RecoveryRecommendationReplay(exporter)
        self.assertIsNotNone(replay)

    def test_build_replay_summary_empty(self):
        """Build replay summary when empty."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        replay = RecoveryRecommendationReplay(exporter)
        
        summary = replay.build_replay_summary()
        
        self.assertEqual(summary["total_recommendations"], 0)
        self.assertEqual(summary["confidence_distribution"], {})
        self.assertEqual(summary["unique_recovery_hints"], [])

    def test_build_replay_summary_with_data(self):
        """Build replay summary with data."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        replay = RecoveryRecommendationReplay(exporter)
        
        # Add recommendations with different confidence levels
        service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-2"}
        )
        
        summary = replay.build_replay_summary()
        
        self.assertEqual(summary["total_recommendations"], 2)
        # Should have confidence distribution (check for key like "low", "medium", etc.)
        self.assertTrue(len(summary["confidence_distribution"]) > 0)
        # Should have stage distribution (check for key like "proposal", "handshake", etc.)
        self.assertTrue(len(summary["stage_distribution"]) > 0)

    def test_build_operator_readable_summary(self):
        """Build human-readable replay summary."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        replay = RecoveryRecommendationReplay(exporter)
        
        service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        summary_str = replay.build_operator_readable_summary()
        
        self.assertIn("RECOVERY RECOMMENDATION REPLAY SUMMARY", summary_str)
        self.assertIn("Total Recommendations: 1", summary_str)

    def test_export_replay_json(self):
        """Export replay summary as JSON."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        replay = RecoveryRecommendationReplay(exporter)
        
        service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        json_str = replay.export_replay_json()
        
        self.assertIn("total_recommendations", json_str)
        self.assertIn("1", json_str)


# ============================================================================
# RECOVERY RECOMMENDATION SUMMARY BUILDER MODEL TESTS
# ============================================================================


class TestRecoveryRecommendationSummaryBuilderModel(unittest.TestCase):
    """Test summary builder data models."""

    def test_builder_creation(self):
        """RecoveryRecommendationSummaryBuilder created successfully."""
        service = RecoveryRecommendationService()
        builder = RecoveryRecommendationSummaryBuilder(service)
        self.assertIsNotNone(builder)

    def test_build_summary_empty(self):
        """Build summary when empty."""
        service = RecoveryRecommendationService()
        builder = RecoveryRecommendationSummaryBuilder(service)
        
        summary = builder.build_summary()
        
        self.assertEqual(summary["total_recommendations"], 0)
        self.assertEqual(summary["recommendations"], [])
        self.assertEqual(summary["confidence_distribution"], {})
        self.assertEqual(summary["correlation_trace_summary"]["flow_ids"], [])

    def test_build_summary_with_data(self):
        """Build summary with data."""
        service = RecoveryRecommendationService()
        builder = RecoveryRecommendationSummaryBuilder(service)
        
        service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={
                "flow_id": "flow-1",
                "request_id": "req-1",
            }
        )
        
        summary = builder.build_summary()
        
        self.assertEqual(summary["total_recommendations"], 1)
        self.assertEqual(len(summary["recommendations"]), 1)
        self.assertEqual(summary["correlation_trace_summary"]["flow_ids"], ["flow-1"])
        self.assertEqual(summary["correlation_trace_summary"]["request_ids"], ["req-1"])

    def test_build_operator_readable_summary(self):
        """Build human-readable summary."""
        service = RecoveryRecommendationService()
        builder = RecoveryRecommendationSummaryBuilder(service)
        
        service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        summary_str = builder.build_operator_readable_summary()
        
        self.assertIn("RECOVERY RECOMMENDATION SUMMARY", summary_str)
        self.assertIn("Total Recommendations: 1", summary_str)
        self.assertIn("flow-1", summary_str)

    def test_export_json(self):
        """Export summary as JSON."""
        service = RecoveryRecommendationService()
        builder = RecoveryRecommendationSummaryBuilder(service)
        
        service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        json_str = builder.export_json()
        
        self.assertIn("total_recommendations", json_str)
        self.assertIn("flow-1", json_str)


# ============================================================================
# FACTORY FUNCTION TESTS
# ============================================================================


class TestFactoryFunctions(unittest.TestCase):
    """Test factory functions for creation patterns."""

    def test_create_recommendation_exporter(self):
        """Factory creates exporter with new service."""
        exporter = create_recommendation_exporter()
        self.assertIsNotNone(exporter)

    def test_create_recommendation_exporter_with_service(self):
        """Factory creates exporter with provided service."""
        service = RecoveryRecommendationService()
        exporter = create_recommendation_exporter(service)
        self.assertIsNotNone(exporter)

    def test_create_recommendation_replay(self):
        """Factory creates replay with exporter."""
        replay = create_recommendation_replay()
        self.assertIsNotNone(replay)

    def test_create_recommendation_replay_with_service(self):
        """Factory creates replay with provided service."""
        service = RecoveryRecommendationService()
        replay = create_recommendation_replay(service=service)
        self.assertIsNotNone(replay)

    def test_create_recommendation_summary_builder(self):
        """Factory creates summary builder."""
        builder = create_recommendation_summary_builder()
        self.assertIsNotNone(builder)

    def test_create_recommendation_summary_builder_with_service(self):
        """Factory creates summary builder with provided service."""
        service = RecoveryRecommendationService()
        builder = create_recommendation_summary_builder(service)
        self.assertIsNotNone(builder)


# ============================================================================
# BACKWARD COMPATIBILITY TESTS
# ============================================================================


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with v72-v75."""

    def test_exporter_works_with_v75_service(self):
        """Exporter works with v75 RecoveryRecommendationService."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        
        rec = service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        exported = exporter._export_recommendation(rec)
        
        self.assertEqual(exported["stage"], FailureStage.PROPOSAL.value)
        self.assertEqual(exported["hint_certainty"], "suggestion")

    def test_replay_works_with_v75_exporter(self):
        """Replay works with v75 exporter."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        replay = RecoveryRecommendationReplay(exporter)
        
        service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        summary = replay.build_replay_summary()
        self.assertEqual(summary["total_recommendations"], 1)

    def test_builder_works_with_v75_service(self):
        """Builder works with v75 service."""
        service = RecoveryRecommendationService()
        builder = RecoveryRecommendationSummaryBuilder(service)
        
        service.generate_recommendation(
            stage=FailureStage.ENVELOPE.value,
            failure_type=FailureType.ENVELOPE_GATE_FAILED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        summary = builder.build_summary()
        self.assertEqual(summary["total_recommendations"], 1)

    def test_integration_with_v74_diagnostics(self):
        """Integration with v74 diagnostic hooks works."""
        from weslr.distributed_diagnostic_hooks import DiagnosticHooks
        from weslr.execution_telemetry import TelemetryEventEmitter
        
        emitter = TelemetryEventEmitter()
        diagnostics = DiagnosticHooks(emitter)
        
        service = RecoveryRecommendationService()
        
        # Should not raise
        result = integrate_with_diagnostics(diagnostics, service)
        self.assertIsInstance(result, list)

    def test_factory_functions_work_with_v75(self):
        """Factory functions work with v75 components."""
        service = RecoveryRecommendationService()
        
        # v75 service should work with v76 factory functions
        exporter = create_recommendation_exporter(service)
        replay = create_recommendation_replay(exporter)
        builder = create_recommendation_summary_builder(service)
        
        service.generate_recommendation(
            stage=FailureStage.DEADLINE.value,
            failure_type=FailureType.DEADLINE_BREACHED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        # All should work
        self.assertIsNotNone(exporter.export_all_recommendations())
        self.assertIsNotNone(replay.build_replay_summary())
        self.assertIsNotNone(builder.build_summary())


# ============================================================================
# CORRELATION INTEGRATION TESTS
# ============================================================================


class TestCorrelationIntegration(unittest.TestCase):
    """Test correlation by flow_id, request_id, handshake_id, deadline_id."""

    def test_exporter_correlates_by_flow_id(self):
        """Exporter correlates recommendations by flow_id."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        
        service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        by_flow = exporter.export_by_flow()
        
        self.assertEqual(len(by_flow["flow-1"]), 2)

    def test_builder_includes_all_correlation_ids(self):
        """Builder includes all correlation IDs in summary."""
        service = RecoveryRecommendationService()
        builder = RecoveryRecommendationSummaryBuilder(service)
        
        service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={
                "flow_id": "flow-1",
                "request_id": "req-1",
                "handshake_id": "hs-1",
                "deadline_id": "dl-1",
            }
        )
        
        summary = builder.build_summary()
        corr = summary["correlation_trace_summary"]
        
        self.assertEqual(corr["flow_ids"], ["flow-1"])
        self.assertEqual(corr["request_ids"], ["req-1"])
        self.assertEqual(corr["handshake_ids"], ["hs-1"])
        self.assertEqual(corr["deadline_ids"], ["dl-1"])

    def test_operator_summary_includes_correlation_trace(self):
        """Operator summary includes correlation trace info."""
        service = RecoveryRecommendationService()
        builder = RecoveryRecommendationSummaryBuilder(service)
        
        service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={
                "flow_id": "flow-1",
                "handshake_id": "hs-1",
            }
        )
        
        summary_str = builder.build_operator_readable_summary()
        
        self.assertIn("CORRELATION TRACE", summary_str)
        self.assertIn("flow-1", summary_str)
        self.assertIn("hs-1", summary_str)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration(unittest.TestCase):
    """Test integration with v75 recommendation service."""

    def test_end_to_end_export_flow(self):
        """End-to-end recommendation export flow."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        replay = RecoveryRecommendationReplay(exporter)
        builder = RecoveryRecommendationSummaryBuilder(service)
        
        # Generate recommendation
        rec = service.generate_recommendation(
            stage=FailureStage.ENVELOPE.value,
            failure_type=FailureType.ENVELOPE_GATE_FAILED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={
                "flow_id": "flow-1",
                "request_id": "req-1",
            }
        )
        
        # Export
        exported = exporter.export_all_recommendations()
        self.assertEqual(len(exported), 1)
        
        # Replay summary
        replay_summary = replay.build_replay_summary()
        self.assertEqual(replay_summary["total_recommendations"], 1)
        
        # Builder summary
        builder_summary = builder.build_summary()
        self.assertEqual(builder_summary["total_recommendations"], 1)
        
        # JSON export
        json_str = exporter.export_json()
        self.assertIn("flow-1", json_str)

    def test_multiple_recommendations_correlation(self):
        """Multiple recommendations with different correlation IDs."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        builder = RecoveryRecommendationSummaryBuilder(service)
        
        # Flow 1 - multiple stages
        service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        # Flow 2 - different
        service.generate_recommendation(
            stage=FailureStage.DEADLINE.value,
            failure_type=FailureType.DEADLINE_BREACHED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-2"}
        )
        
        # Export by flow
        by_flow = exporter.export_by_flow()
        self.assertEqual(len(by_flow), 2)
        self.assertEqual(len(by_flow["flow-1"]), 2)
        
        # Builder summary
        summary = builder.build_summary()
        self.assertEqual(summary["total_recommendations"], 3)
        self.assertEqual(len(summary["correlation_trace_summary"]["flow_ids"]), 2)

    def test_replay_with_multiple_confidence_levels(self):
        """Replay handles multiple confidence levels."""
        service = RecoveryRecommendationService()
        exporter = RecoveryRecommendationExporter(service)
        replay = RecoveryRecommendationReplay(exporter)
        
        # Generate recommendations with different scenarios
        service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_TRUST_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-2"}
        )
        
        summary = replay.build_replay_summary()
        
        self.assertEqual(summary["total_recommendations"], 2)
        # Should have confidence distribution
        self.assertTrue(len(summary["confidence_distribution"]) > 0)


if __name__ == "__main__":
    unittest.main()
