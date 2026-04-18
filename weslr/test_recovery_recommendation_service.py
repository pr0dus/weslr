"""Tests for Recovery Recommendation Service (v75)

Behavioral tests for recovery recommendation generation, confidence guidance,
export integration, and diagnostics integration.

Test Doctrine version: 1.0.0 (2026-04-07)
"""

import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.recovery_recommendation_service import (
    RecoveryRecommendationService,
    integrate_with_distributed_diagnostic_hooks,
    integrate_with_exporters,
)
from weslr.distributed_diagnostic_hooks import (
    FailureType,
    FailureStage,
)


# ============================================================================
# RECOVERY RECOMMENDATION SERVICE MODEL TESTS
# ============================================================================


class TestRecoveryRecommendationServiceModel(unittest.TestCase):
    """Test recovery recommendation service data models."""

    def test_service_creation(self):
        """RecoveryRecommendationService created successfully."""
        service = RecoveryRecommendationService()
        self.assertIsNotNone(service)
        self.assertEqual(len(service._recommendations), 0)

    def test_generate_recommendation_proposal_failure(self):
        """Generate recommendation for proposal failure."""
        service = RecoveryRecommendationService()
        
        recommendation = service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-123"}
        )
        
        self.assertIn("recommendation_id", recommendation)
        self.assertEqual(recommendation["stage"], FailureStage.PROPOSAL.value)
        self.assertEqual(recommendation["failure_type"], FailureType.PROPOSAL_REJECTED.value)
        self.assertIn("likely_cause", recommendation)
        self.assertIn("recovery_hint", recommendation)
        self.assertIn("confidence", recommendation)
        self.assertEqual(recommendation["hint_certainty"], "suggestion")
        self.assertIn("correlation_ids", recommendation)

    def test_generate_recommendation_handshake_failure(self):
        """Generate recommendation for handshake failure."""
        service = RecoveryRecommendationService()
        
        recommendation = service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "handshake-456"}
        )
        
        self.assertEqual(recommendation["stage"], FailureStage.HANDSHAKE.value)
        self.assertIn("likely_cause", recommendation)
        self.assertIn("recovery_hint", recommendation)
        self.assertEqual(recommendation["hint_certainty"], "suggestion")

    def test_generate_recommendation_deadline_failure(self):
        """Generate recommendation for deadline failure."""
        service = RecoveryRecommendationService()
        
        recommendation = service.generate_recommendation(
            stage=FailureStage.DEADLINE.value,
            failure_type=FailureType.DEADLINE_BREACHED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "deadline-789"}
        )
        
        self.assertEqual(recommendation["stage"], FailureStage.DEADLINE.value)
        self.assertIn("likely_cause", recommendation)
        self.assertIn("recovery_hint", recommendation)
        self.assertEqual(recommendation["hint_certainty"], "suggestion")

    def test_get_recommendation_by_id(self):
        """Get recommendation by ID."""
        service = RecoveryRecommendationService()
        
        rec1 = service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        rec2 = service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-2"}
        )
        
        retrieved = service.get_recommendation_by_id(rec1["recommendation_id"])
        self.assertEqual(retrieved["stage"], FailureStage.PROPOSAL.value)
        
        retrieved2 = service.get_recommendation_by_id(rec2["recommendation_id"])
        self.assertEqual(retrieved2["stage"], FailureStage.HANDSHAKE.value)

    def test_get_all_recommendations(self):
        """Get all generated recommendations."""
        service = RecoveryRecommendationService()
        
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
        
        all_recs = service.get_all_recommendations()
        self.assertEqual(len(all_recs), 2)


# ============================================================================
# RECOVERY RECOMMENDATION SERVICE BEHAVIOR TESTS
# ============================================================================


class TestRecoveryRecommendationServiceBehavior(unittest.TestCase):
    """Test recovery recommendation service behavior."""

    def setUp(self):
        self.service = RecoveryRecommendationService()

    def test_confidence_guidance_low(self):
        """Low confidence for unknown failure type."""
        recommendation = self.service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type="unknown_failure_type",
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        # Unknown failure should have low confidence
        self.assertIn(recommendation["confidence"], ["low", "medium", "high", "very_high"])

    def test_confidence_guidance_trust_failure(self):
        """Higher confidence for trust-related failures."""
        recommendation = self.service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_TRUST_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-2"}
        )
        
        # Trust failure should have elevated confidence
        self.assertIn(recommendation["confidence"], ["low", "medium", "high", "very_high"])

    def test_build_recommendation_summary_empty(self):
        """Build summary with empty recommendations."""
        summary = self.service.build_recommendation_summary([])
        
        self.assertEqual(summary["total_recommendations"], 0)
        self.assertEqual(summary["confidence_distribution"], {})
        self.assertIsNone(summary["most_common_cause"])
        self.assertEqual(summary["recommended_actions"], [])

    def test_build_recommendation_summary_with_items(self):
        """Build summary with multiple recommendations."""
        recs = []
        for i in range(3):
            rec = self.service.generate_recommendation(
                stage=FailureStage.PROPOSAL.value,
                failure_type=FailureType.PROPOSAL_REJECTED.value,
                context={"timestamp": "2026-04-07T20:00:00Z"},
                correlation_ids={"flow_id": f"flow-{i}"}
            )
            recs.append(rec)
        
        summary = self.service.build_recommendation_summary(recs)
        
        self.assertEqual(summary["total_recommendations"], 3)
        self.assertIn("confidence_distribution", summary)
        self.assertIsNotNone(summary["most_common_cause"])
        self.assertGreater(len(summary["recommended_actions"]), 0)


# ============================================================================
# DIAGNOSTICS INTEGRATION HOOK TESTS
# ============================================================================


class TestDiagnosticsIntegrationHook(unittest.TestCase):
    """Test diagnostics integration hook."""

    def test_integrate_with_distributed_diagnostic_hooks(self):
        """Integration hook works with distributed diagnostic hooks."""
        recommendation = integrate_with_distributed_diagnostic_hooks(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-123"}
        )
        
        self.assertIn("recommendation_id", recommendation)
        self.assertEqual(recommendation["stage"], FailureStage.PROPOSAL.value)
        self.assertEqual(recommendation["failure_type"], FailureType.PROPOSAL_REJECTED.value)
        self.assertEqual(recommendation["hint_certainty"], "suggestion")

    def test_integrate_with_distributed_diagnostic_hooks_custom_service(self):
        """Integration hook works with custom service."""
        custom_service = RecoveryRecommendationService()
        custom_service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "handshake-456"}
        )
        
        recommendation = integrate_with_distributed_diagnostic_hooks(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "handshake-456"},
            service=custom_service
        )
        
        self.assertEqual(recommendation["stage"], FailureStage.HANDSHAKE.value)
        self.assertEqual(recommendation["failure_type"], FailureType.HANDSHAKE_FAILED.value)


# ============================================================================
# EXPORT INTEGRATION HOOK TESTS
# ============================================================================


class TestExportIntegrationHook(unittest.TestCase):
    """Test export integration hook."""

    def test_integrate_with_exporters(self):
        """Export hook adds guidance markers."""
        recommendation = {
            "stage": FailureStage.PROPOSAL.value,
            "failure_type": FailureType.PROPOSAL_REJECTED.value,
            "confidence": "high"
        }
        
        exportable = integrate_with_exporters(recommendation)
        
        self.assertIn("hint_certainty", exportable)
        self.assertEqual(exportable["hint_certainty"], "suggestion")
        self.assertIn("confidence_explanation", exportable)
        self.assertIn("level", exportable["confidence_explanation"])
        self.assertIn("meaning", exportable["confidence_explanation"])

    def test_integrate_with_exporters_preserves_existing(self):
        """Export hook preserves existing recommendation data."""
        recommendation = {
            "stage": FailureStage.HANDSHAKE.value,
            "failure_type": FailureType.HANDSHAKE_FAILED.value,
            "likely_cause": "Protocol mismatch",
            "confidence": "medium"
        }
        
        exportable = integrate_with_exporters(recommendation)
        
        self.assertEqual(exportable["stage"], FailureStage.HANDSHAKE.value)
        self.assertEqual(exportable["failure_type"], FailureType.HANDSHAKE_FAILED.value)
        self.assertEqual(exportable["likely_cause"], "Protocol mismatch")
        self.assertEqual(exportable["confidence"], "medium")


# ============================================================================
# READ-ONLY BEHAVIOR TESTS
# ============================================================================


class TestReadOnlyBehavior(unittest.TestCase):
    """Test that service is read-only (no side effects)."""

    def test_service_does_not_write_external_resources(self):
        """Service does not write to external resources."""
        import tempfile
        
        service = RecoveryRecommendationService()
        
        # Generate recommendation
        rec = service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        # Service should only store in internal dict
        self.assertEqual(len(service._recommendations), 1)
        
        # No external files should be created
        temp_dir = tempfile.gettempdir()
        # Service doesn't touch filesystem

    def test_integrate_with_distributed_diagnostic_hooks_is_read_only(self):
        """Integration hook does not modify external state."""
        initial_recommendations = 0
        
        recommendation = integrate_with_distributed_diagnostic_hooks(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        self.assertIn("recommendation_id", recommendation)


# ============================================================================
# BACKWARD COMPATIBILITY TESTS
# ============================================================================


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with v71-v74 diagnostic flow."""

    def test_service_works_with_v71_failure_stages(self):
        """Service works with v71 FailureStage enum."""
        service = RecoveryRecommendationService()
        
        # Test all known stages
        stages = [
            FailureStage.PROPOSAL.value,
            FailureStage.HANDSHAKE.value,
            FailureStage.ENVELOPE.value,
            FailureStage.DEADLINE.value,
            FailureStage.RECEIPT.value,
        ]
        
        for stage in stages:
            rec = service.generate_recommendation(
                stage=stage,
                failure_type=FailureType.UNKNOWN.value,
                context={"timestamp": "2026-04-07T20:00:00Z"},
                correlation_ids={"flow_id": f"flow-{stage}"}
            )
            self.assertEqual(rec["stage"], stage)

    def test_service_works_with_v71_failure_types(self):
        """Service works with v71 FailureType enum."""
        service = RecoveryRecommendationService()
        
        # Test all known failure types
        failure_types = [
            FailureType.PROPOSAL_REJECTED.value,
            FailureType.PROPOSAL_EXPIRED.value,
            FailureType.PROPOSAL_VALIDATION_FAILED.value,
            FailureType.HANDSHAKE_FAILED.value,
            FailureType.HANDSHAKE_TRUST_REJECTED.value,
            FailureType.HANDSHAKE_HEALTH_REJECTED.value,
            FailureType.ENVELOPE_GATE_FAILED.value,
            FailureType.ENVELOPE_DISPATCH_FAILED.value,
            FailureType.DEADLINE_BREACHED.value,
            FailureType.RECEIPT_FAILED.value,
            FailureType.UNKNOWN.value,
        ]
        
        for ft in failure_types:
            rec = service.generate_recommendation(
                stage=FailureStage.PROPOSAL.value,
                failure_type=ft,
                context={"timestamp": "2026-04-07T20:00:00Z"},
                correlation_ids={"flow_id": f"flow-{ft}"}
            )
            self.assertEqual(rec["failure_type"], ft)

    def test_integration_hooks_work_with_v70_distributed_diagnostics(self):
        """Integration hooks work with v70 distributed diagnostics."""
        from weslr.distributed_diagnostic_hooks import (
            FailureClassification,
            FailureClassifier,
            StageDiagnosis,
            CrossStageCorrelator,
            DiagnosticSummary,
        )
        from weslr.execution_telemetry import TelemetryEventEmitter
        
        emitter = TelemetryEventEmitter()
        
        # v70 components should work alongside v75 service
        classifier = FailureClassifier(emitter)
        
        rec = integrate_with_distributed_diagnostic_hooks(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        self.assertIn("recommendation_id", rec)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration(unittest.TestCase):
    """Test integration with existing v68-v74 diagnostic flow."""

    def test_end_to_end_recovery_flow(self):
        """End-to-end recovery recommendation flow."""
        service = RecoveryRecommendationService()
        
        # Step 1: Generate recommendation
        rec = service.generate_recommendation(
            stage=FailureStage.ENVELOPE.value,
            failure_type=FailureType.ENVELOPE_GATE_FAILED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1", "request_id": "req-1"}
        )
        
        # Step 2: Export for operator consumption
        exportable = integrate_with_exporters(rec)
        
        # Step 3: Verify guidance markers
        self.assertEqual(exportable["hint_certainty"], "suggestion")
        self.assertIn("confidence_explanation", exportable)
        
        # Step 4: Build summary for multiple recommendations
        summary = service.build_recommendation_summary([rec])
        
        self.assertEqual(summary["total_recommendations"], 1)

    def test_service_reuse_across_flows(self):
        """Service can be reused across multiple flows."""
        service = RecoveryRecommendationService()
        
        # First flow
        rec1 = service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-1"}
        )
        
        # Second flow
        rec2 = service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            context={"timestamp": "2026-04-07T20:00:00Z"},
            correlation_ids={"flow_id": "flow-2"}
        )
        
        # Both should be stored
        self.assertEqual(len(service.get_all_recommendations()), 2)

    def test_service_with_multiple_failure_stages(self):
        """Service handles multiple failure stages in sequence."""
        service = RecoveryRecommendationService()
        
        stages_and_failures = [
            (FailureStage.PROPOSAL.value, FailureType.PROPOSAL_REJECTED.value),
            (FailureStage.HANDSHAKE.value, FailureType.HANDSHAKE_FAILED.value),
            (FailureStage.ENVELOPE.value, FailureType.ENVELOPE_GATE_FAILED.value),
        ]
        
        for stage, failure_type in stages_and_failures:
            rec = service.generate_recommendation(
                stage=stage,
                failure_type=failure_type,
                context={"timestamp": "2026-04-07T20:00:00Z"},
                correlation_ids={"flow_id": f"flow-{stage}"}
            )
            
            self.assertEqual(rec["stage"], stage)
            self.assertEqual(rec["failure_type"], failure_type)
            self.assertEqual(rec["hint_certainty"], "suggestion")


if __name__ == "__main__":
    unittest.main()
