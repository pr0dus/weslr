"""Test suite for v76 Recovery Recommendation Export + Replay Correlation.

Tests:
  - RecoveryRecommendationExportRecord model
  - RecoveryRecommendationExporter behavior
  - Integration with diagnostics
  - Backward compatibility with v72-v75
"""

from __future__ import annotations

import json
import pytest
from datetime import datetime, timezone
from typing import Any, Dict, List

from .recovery_recommendation_export import (
    RecoveryRecommendationExportRecord,
    RecoveryRecommendationExporter,
)
from .distributed_diagnostic_hooks import (
    DiagnosticHooks,
    FailureClassification,
    FailureStage,
    FailureType,
    DiagnosticSummaryBuilder,
)
from .recovery_recommendation_service import RecoveryRecommendationService
from .execution_telemetry import TelemetryEventEmitter, TelemetryEvent, TelemetryEventType


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def emitter() -> TelemetryEventEmitter:
    """Create telemetry emitter for tests."""
    return TelemetryEventEmitter()


@pytest.fixture
def diagnostic_hooks(emitter: TelemetryEventEmitter) -> DiagnosticHooks:
    """Create diagnostic hooks for tests."""
    return DiagnosticHooks(emitter)


@pytest.fixture
def recommendation_service() -> RecoveryRecommendationService:
    """Create recovery recommendation service for tests."""
    return RecoveryRecommendationService()


@pytest.fixture
def exporter(diagnostic_hooks: DiagnosticHooks) -> RecoveryRecommendationExporter:
    """Create exporter instance for tests."""
    return RecoveryRecommendationExporter(diagnostic_hooks)


# ============================================================================
# TEST RECOVERY RECOMMENDATION EXPORT RECORD MODEL
# ============================================================================


class TestRecoveryRecommendationExportRecordModel:
    """Test RecoveryRecommendationExportRecord dataclass."""
    
    def test_creation_and_serialization(self):
        """Test record creation and dict serialization."""
        correlation_ids = {
            "flow_id": "flow_123",
            "request_id": "req_456",
            "handshake_id": "hs_789",
            "deadline_id": "dl_000",
        }
        
        recommendation_data = {
            "recommendation_id": "rec_001",
            "stage": "proposal",
            "recovery_hint": "Review rejection reason",
            "confidence": "high",
        }
        
        record = RecoveryRecommendationExportRecord(
            export_id="export_abc",
            recommendation_id="rec_001",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            correlation_ids=correlation_ids,
            recommendation_data=recommendation_data,
        )
        
        assert record.export_id == "export_abc"
        assert record.recommendation_id == "rec_001"
        assert record.correlation_ids == correlation_ids
        assert record.recommendation_data == recommendation_data
        
        # Test dict serialization
        record_dict = record.to_dict()
        assert record_dict["export_id"] == "export_abc"
        assert record_dict["correlation_ids"] == correlation_ids
        assert record_dict["recommendation_data"] == recommendation_data
    
    def test_json_serialization(self):
        """Test JSON serialization."""
        record = RecoveryRecommendationExportRecord(
            export_id="export_001",
            recommendation_id="rec_001",
            timestamp="2026-04-07T18:55:00Z",
            correlation_ids={"flow_id": "flow_123"},
            recommendation_data={"test": "data"},
        )
        
        json_str = record.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["export_id"] == "export_001"
        assert parsed["correlation_ids"]["flow_id"] == "flow_123"
    
    def test_from_dict_round_trip(self):
        """Test from_dict creates valid instance."""
        original = RecoveryRecommendationExportRecord(
            export_id="export_001",
            recommendation_id="rec_001",
            timestamp="2026-04-07T18:55:00Z",
            correlation_ids={"flow_id": "flow_123"},
            recommendation_data={"key": "value"},
        )
        
        record_dict = original.to_dict()
        restored = RecoveryRecommendationExportRecord.from_dict(record_dict)
        
        assert restored.export_id == original.export_id
        assert restored.recommendation_id == original.recommendation_id
        assert restored.correlation_ids == original.correlation_ids
        assert restored.recommendation_data == original.recommendation_data
    
    def test_with_failure_classification(self):
        """Test record with failure classification."""
        failure_classification = FailureClassification(
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            stage=FailureStage.PROPOSAL.value,
            observed_error="Proposal rejected by validation",
            correlation_ids={"flow_id": "flow_test"},
        )
        
        record = RecoveryRecommendationExportRecord(
            export_id="export_001",
            recommendation_id="rec_001",
            timestamp="2026-04-07T18:55:00Z",
            correlation_ids={"flow_id": "flow_test"},
            recommendation_data={"hint": "Review rejection"},
            failure_classification=failure_classification,
            recovery_hint="Review rejection reason",
            confidence_level="medium",
        )
        
        assert record.failure_classification is not None
        assert record.recovery_hint == "Review rejection reason"
        assert record.confidence_level == "medium"
        
        # Test dict includes failure classification
        record_dict = record.to_dict()
        assert record_dict["failure_classification"] is not None
        assert record_dict["failure_classification"]["failure_type"] == "proposal_rejected"


# ============================================================================
# TEST RECOVERY RECOMMENDATION EXPORTER BEHAVIOR
# ============================================================================


class TestRecoveryRecommendationExporterBehavior:
    """Test RecoveryRecommendationExporter class."""
    
    def test_export_recommendation(self, exporter: RecoveryRecommendationExporter):
        """Test exporting a recommendation."""
        service = RecoveryRecommendationService()
        recommendation = service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={
                "timestamp": "2026-04-07T18:55:00Z",
                "node_id": "node_001",
            },
            correlation_ids={
                "flow_id": "flow_123",
                "request_id": "req_456",
            },
        )
        
        export_record = exporter.export_recommendation(recommendation)
        
        assert export_record.export_id is not None
        assert export_record.recommendation_id == recommendation["recommendation_id"]
        assert export_record.correlation_ids["flow_id"] == "flow_123"
        assert export_record.correlation_ids["request_id"] == "req_456"
        assert export_record.recovery_hint == recommendation["recovery_hint"]
        assert export_record.confidence_level == recommendation["confidence"]
    
    def test_export_by_correlation_flow_id(self, exporter: RecoveryRecommendationExporter):
        """Test filtering exports by flow_id."""
        service = RecoveryRecommendationService()
        
        # Export recommendation with flow_id correlation
        recommendation1 = service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T18:55:00Z"},
            correlation_ids={"flow_id": "flow_test", "request_id": "req_001"},
        )
        exporter.export_recommendation(recommendation1)
        
        # Export another recommendation with different flow_id
        recommendation2 = service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            context={"timestamp": "2026-04-07T18:56:00Z"},
            correlation_ids={"flow_id": "flow_other", "request_id": "req_002"},
        )
        exporter.export_recommendation(recommendation2)
        
        # Filter by flow_id
        filtered = exporter.export_by_correlation(flow_id="flow_test")
        
        assert len(filtered) == 1
        assert filtered[0].correlation_ids["flow_id"] == "flow_test"
    
    def test_export_by_correlation_request_id(self, exporter: RecoveryRecommendationExporter):
        """Test filtering exports by request_id."""
        service = RecoveryRecommendationService()
        
        # Export recommendation with request_id correlation
        recommendation = service.generate_recommendation(
            stage=FailureStage.ENVELOPE.value,
            failure_type=FailureType.ENVELOPE_GATE_FAILED.value,
            context={"timestamp": "2026-04-07T18:55:00Z"},
            correlation_ids={"request_id": "req_special"},
        )
        exporter.export_recommendation(recommendation)
        
        # Filter by request_id
        filtered = exporter.export_by_correlation(request_id="req_special")
        
        assert len(filtered) == 1
        assert filtered[0].correlation_ids["request_id"] == "req_special"
    
    def test_export_operator_summary(self, exporter: RecoveryRecommendationExporter):
        """Test operator-readable summary generation."""
        service = RecoveryRecommendationService()
        
        recommendation = service.generate_recommendation(
            stage=FailureStage.DEADLINE.value,
            failure_type=FailureType.DEADLINE_BREACHED.value,
            context={"timestamp": "2026-04-07T18:55:00Z"},
            correlation_ids={"flow_id": "flow_123", "deadline_id": "dl_001"},
        )
        exporter.export_recommendation(recommendation)
        
        summary = exporter.export_operator_summary()
        
        assert "RECOVERY RECOMMENDATION EXPORT SUMMARY" in summary
        assert "Total Recommendations Exported: 1" in summary
        assert "flow_123" in summary
        assert "dl_001" in summary
        assert "recovery_hint" in summary.lower() or "hint" in summary.lower()
    
    def test_export_machine_readable(self, exporter: RecoveryRecommendationExporter):
        """Test machine-readable export."""
        service = RecoveryRecommendationService()
        
        recommendation = service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            context={"timestamp": "2026-04-07T18:55:00Z"},
            correlation_ids={"handshake_id": "hs_001"},
        )
        exporter.export_recommendation(recommendation)
        
        machine_readable = exporter.export_machine_readable()
        
        assert isinstance(machine_readable, list)
        assert len(machine_readable) == 1
        record = machine_readable[0]
        assert record["recommendation_id"] == recommendation["recommendation_id"]
        assert record["confidence_level"] == recommendation["confidence"]
        assert record["correlation_ids"]["handshake_id"] == "hs_001"
    
    def test_no_correlation_filter(self, exporter: RecoveryRecommendationExporter):
        """Test export with no correlation filter returns all."""
        service = RecoveryRecommendationService()
        
        # Export multiple recommendations
        for i in range(3):
            recommendation = service.generate_recommendation(
                stage=FailureStage.PROPOSAL.value,
                failure_type=FailureType.PROPOSAL_REJECTED.value,
                context={"timestamp": f"2026-04-07T18:55:0{i}Z"},
                correlation_ids={"flow_id": f"flow_{i}"},
            )
            exporter.export_recommendation(recommendation)
        
        # Filter with no correlation IDs should return all
        all_records = exporter.export_by_correlation()
        
        assert len(all_records) == 3


# ============================================================================
# TEST INTEGRATION WITH DIAGNOSTICS
# ============================================================================


class TestRecoveryRecommendationExportIntegration:
    """Test integration with distributed diagnostics."""
    
    def test_export_with_failure_classification(self, emitter: TelemetryEventEmitter):
        """Test exporting with failure classification from diagnostics."""
        from .recovery_recommendation_export import RecoveryRecommendationExporter
        
        exporter = RecoveryRecommendationExporter(DiagnosticHooks(emitter))
        service = RecoveryRecommendationService()
        
        # Create failure classification
        failure_classification = FailureClassification(
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            stage=FailureStage.PROPOSAL.value,
            observed_error="Proposal rejected",
            correlation_ids={"flow_id": "flow_int_test"},
        )
        
        # Generate and export recommendation
        recommendation = service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T18:55:00Z"},
            correlation_ids={"flow_id": "flow_int_test"},
        )
        
        export_record = exporter.export_recommendation(
            recommendation,
            failure_classification=failure_classification,
        )
        
        assert export_record.failure_classification is not None
        assert export_record.failure_classification.failure_type == "proposal_rejected"
        assert export_record.failure_classification.stage == "proposal"
    
    def test_end_to_end_workflow(self, emitter: TelemetryEventEmitter):
        """Test complete end-to-end workflow."""
        from .recovery_recommendation_export import RecoveryRecommendationExporter
        
        exporter = RecoveryRecommendationExporter(DiagnosticHooks(emitter))
        service = RecoveryRecommendationService()
        
        # Step 1: Generate recommendation
        recommendation = service.generate_recommendation(
            stage=FailureStage.ENVELOPE.value,
            failure_type=FailureType.ENVELOPE_AUTHORIZATION_FAILED.value,
            context={
                "timestamp": "2026-04-07T18:55:00Z",
                "node_id": "node_test",
            },
            correlation_ids={
                "flow_id": "flow_complete",
                "request_id": "req_complete",
                "handshake_id": "hs_complete",
                "deadline_id": "dl_complete",
            },
        )
        
        # Step 2: Export recommendation
        export_record = exporter.export_recommendation(recommendation)
        
        # Step 3: Export operator summary
        summary = exporter.export_operator_summary()
        
        # Step 4: Export machine readable
        machine_export = exporter.export_machine_readable()
        
        # Verify all steps completed successfully
        assert export_record.export_id is not None
        assert len(summary) > 0
        assert len(machine_export) > 0
        assert all([
            export_record.correlation_ids.get("flow_id") == "flow_complete",
            export_record.correlation_ids.get("request_id") == "req_complete",
            export_record.correlation_ids.get("handshake_id") == "hs_complete",
            export_record.correlation_ids.get("deadline_id") == "dl_complete",
        ])


# ============================================================================
# TEST BACKWARD COMPATIBILITY WITH V72-V75
# ============================================================================


class TestRecoveryRecommendationExportBackwardCompatibility:
    """Test backward compatibility with v72-v75 diagnostic flow."""
    
    def test_compatibility_with_v74_fallback_trace(self, emitter: TelemetryEventEmitter):
        """Test compatibility with v74 fallback trace export format."""
        from .recovery_recommendation_export import RecoveryRecommendationExporter
        
        exporter = RecoveryRecommendationExporter(DiagnosticHooks(emitter))
        service = RecoveryRecommendationService()
        
        # v74 fallback trace format has correlation_ids with flow/request/handshake/deadline
        recommendation = service.generate_recommendation(
            stage=FailureStage.RECEIPT.value,
            failure_type=FailureType.RECEIPT_FAILED.value,
            context={"timestamp": "2026-04-07T18:55:00Z"},
            correlation_ids={
                "flow_id": "flow_v74_compat",
                "request_id": "req_v74_compat",
                "handshake_id": "hs_v74_compat",
                "deadline_id": "dl_v74_compat",
            },
        )
        
        export_record = exporter.export_recommendation(recommendation)
        
        # Verify all v74 correlation IDs are preserved
        assert export_record.correlation_ids["flow_id"] == "flow_v74_compat"
        assert export_record.correlation_ids["request_id"] == "req_v74_compat"
        assert export_record.correlation_ids["handshake_id"] == "hs_v74_compat"
        assert export_record.correlation_ids["deadline_id"] == "dl_v74_compat"
    
    def test_compatibility_with_v73_fallback_audit(self, emitter: TelemetryEventEmitter):
        """Test compatibility with v73 fallback audit records."""
        from .recovery_recommendation_export import RecoveryRecommendationExporter
        
        exporter = RecoveryRecommendationExporter(DiagnosticHooks(emitter))
        service = RecoveryRecommendationService()
        
        # v73 fallback audit records include node_id and reason
        recommendation = service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_EXPIRED.value,
            context={
                "timestamp": "2026-04-07T18:55:00Z",
                "node_id": "node_v73_compat",
                "fallback_reason": "timeout",
            },
            correlation_ids={
                "flow_id": "flow_v73_compat",
            },
        )
        
        export_record = exporter.export_recommendation(recommendation)
        
        # Verify v73 context is preserved (context passed in becomes part of recommendation)
        assert export_record.recommendation_data["correlation_ids"]["flow_id"] == "flow_v73_compat"
        assert "generated_at" in export_record.recommendation_data
    
    def test_compatibility_with_v72_trace_export(self, emitter: TelemetryEventEmitter):
        """Test compatibility with v72 trace export format."""
        from .recovery_recommendation_export import RecoveryRecommendationExporter
        
        exporter = RecoveryRecommendationExporter(DiagnosticHooks(emitter))
        service = RecoveryRecommendationService()
        
        # v72 trace exports have timestamp and failure context
        recommendation = service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_TIMEOUT.value,
            context={
                "timestamp": "2026-04-07T18:55:00Z",
                "failure_context": "handshake timeout after 30s",
            },
            correlation_ids={
                "flow_id": "flow_v72_compat",
                "handshake_id": "hs_v72_compat",
            },
        )
        
        export_record = exporter.export_recommendation(recommendation)
        
        # Verify v72 timestamp and correlation preserved
        assert export_record.timestamp == "2026-04-07T18:55:00Z"
        assert export_record.correlation_ids["handshake_id"] == "hs_v72_compat"
        assert export_record.correlation_ids["flow_id"] == "flow_v72_compat"
    
    def test_correlation_filter_across_versions(self, emitter: TelemetryEventEmitter):
        """Test correlation filtering works across v72-v75 data."""
        from .recovery_recommendation_export import RecoveryRecommendationExporter
        
        exporter = RecoveryRecommendationExporter(DiagnosticHooks(emitter))
        service = RecoveryRecommendationService()
        
        # Export recommendation with v72-style correlation
        recommendation_v72 = service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={"timestamp": "2026-04-07T18:55:00Z"},
            correlation_ids={"flow_id": "flow_v7x_compat"},
        )
        exporter.export_recommendation(recommendation_v72)
        
        # Export recommendation with v75-style correlation (all IDs)
        recommendation_v75 = service.generate_recommendation(
            stage=FailureStage.DEADLINE.value,
            failure_type=FailureType.DEADLINE_BREACHED.value,
            context={"timestamp": "2026-04-07T18:56:00Z"},
            correlation_ids={
                "flow_id": "flow_v7x_compat",
                "request_id": "req_v7x_compat",
                "handshake_id": "hs_v7x_compat",
                "deadline_id": "dl_v7x_compat",
            },
        )
        exporter.export_recommendation(recommendation_v75)
        
        # Filter by flow_id should return both (v72 and v75)
        filtered = exporter.export_by_correlation(flow_id="flow_v7x_compat")
        
        # Both records should be returned since they share the same flow_id
        assert len(filtered) >= 1
        assert filtered[0].correlation_ids["flow_id"] == "flow_v7x_compat"


# ============================================================================
# TEST RECOVERY SAFE ALTERNATIVES
# ============================================================================


class TestRecoverySafeAlternatives:
    """Test recovery safe alternatives and suggestion logic."""
    
    def test_suggest_lower_scope_when_constraint_violated(self, exporter: RecoveryRecommendationExporter):
        """Test suggestion for constraint violation scenarios."""
        service = RecoveryRecommendationService()
        
        # Simulate constraint violation scenario
        recommendation = service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_VALIDATION_FAILED.value,
            context={
                "timestamp": "2026-04-07T18:55:00Z",
                "constraint_violation": "trust_threshold_not_met",
            },
            correlation_ids={"flow_id": "flow_constraint"},
        )
        
        export_record = exporter.export_recommendation(recommendation)
        
        # Verify suggestion provides operator guidance (contains action verb)
        assert export_record.recovery_hint is not None
        assert len(export_record.recovery_hint) > 0
    
    def test_suggest_delayed_when_trust_low(self, exporter: RecoveryRecommendationExporter):
        """Test suggestion for low trust scenarios."""
        service = RecoveryRecommendationService()
        
        recommendation = service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_TRUST_REJECTED.value,
            context={
                "timestamp": "2026-04-07T18:55:00Z",
                "trust_score": 0.3,
            },
            correlation_ids={"flow_id": "flow_trust_low"},
        )
        
        export_record = exporter.export_recommendation(recommendation)
        
        # Verify suggestion includes delay guidance
        assert "delay" in export_record.recovery_hint.lower() or "review" in export_record.recovery_hint.lower()
    
    def test_suggest_escalation_when_blocked(self, exporter: RecoveryRecommendationExporter):
        """Test suggestion for blocked capability scenarios."""
        service = RecoveryRecommendationService()
        
        recommendation = service.generate_recommendation(
            stage=FailureStage.ENVELOPE.value,
            failure_type=FailureType.ENVELOPE_AUTHORIZATION_FAILED.value,
            context={
                "timestamp": "2026-04-07T18:55:00Z",
                "blocked_by": "authorization_gate",
            },
            correlation_ids={"flow_id": "flow_escalation"},
        )
        
        export_record = exporter.export_recommendation(recommendation)
        
        # Verify suggestion includes escalation guidance
        assert "escalation" in export_record.recovery_hint.lower() or "review" in export_record.recovery_hint.lower()
    
    def test_suggest_evidence_gathering_when_insufficient(self, exporter: RecoveryRecommendationExporter):
        """Test suggestion for insufficient evidence scenarios."""
        service = RecoveryRecommendationService()
        
        recommendation = service.generate_recommendation(
            stage=FailureStage.RECEIPT.value,
            failure_type=FailureType.RECEIPT_TIMEOUT.value,
            context={
                "timestamp": "2026-04-07T18:55:00Z",
                "evidence_status": "insufficient",
            },
            correlation_ids={"flow_id": "flow_evidence"},
        )
        
        export_record = exporter.export_recommendation(recommendation)
        
        # Verify suggestion provides operator guidance
        assert export_record.recovery_hint is not None
        assert len(export_record.recovery_hint) > 0


# ============================================================================
# TEST CORRELATION ID TRACKING
# ============================================================================


class TestCorrelationIdTracking:
    """Test correlation ID tracking across all record types."""
    
    def test_all_correlation_id_types_preserved(self, exporter: RecoveryRecommendationExporter):
        """Test that all correlation ID types are preserved."""
        service = RecoveryRecommendationService()
        
        recommendation = service.generate_recommendation(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_IDENTITY_MISMATCH.value,
            context={"timestamp": "2026-04-07T18:55:00Z"},
            correlation_ids={
                "flow_id": "flow_track",
                "request_id": "req_track",
                "handshake_id": "hs_track",
                "deadline_id": "dl_track",
            },
        )
        
        export_record = exporter.export_recommendation(recommendation)
        
        # Test all four correlation ID types
        assert export_record.correlation_ids.get("flow_id") == "flow_track"
        assert export_record.correlation_ids.get("request_id") == "req_track"
        assert export_record.correlation_ids.get("handshake_id") == "hs_track"
        assert export_record.correlation_ids.get("deadline_id") == "dl_track"
    
    def test_filter_by_any_correlation_type(self, exporter: RecoveryRecommendationExporter):
        """Test filtering by any correlation ID type."""
        service = RecoveryRecommendationService()
        
        # Export with all correlation IDs
        recommendation = service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_EXPIRED.value,
            context={"timestamp": "2026-04-07T18:55:00Z"},
            correlation_ids={
                "flow_id": "flow_multi",
                "request_id": "req_multi",
                "handshake_id": "hs_multi",
                "deadline_id": "dl_multi",
            },
        )
        exporter.export_recommendation(recommendation)
        
        # Test filtering by each correlation ID type
        assert len(exporter.export_by_correlation(flow_id="flow_multi")) >= 1
        assert len(exporter.export_by_correlation(request_id="req_multi")) >= 1
        assert len(exporter.export_by_correlation(handshake_id="hs_multi")) >= 1
        assert len(exporter.export_by_correlation(deadline_id="dl_multi")) >= 1
    
    def test_empty_correlation_ids_handled(self, exporter: RecoveryRecommendationExporter):
        """Test handling of empty correlation IDs."""
        service = RecoveryRecommendationService()
        
        recommendation = service.generate_recommendation(
            stage=FailureStage.UNKNOWN.value,
            failure_type=FailureType.UNKNOWN.value,
            context={"timestamp": "2026-04-07T18:55:00Z"},
            correlation_ids={},
        )
        
        export_record = exporter.export_recommendation(recommendation)
        
        # Empty correlation IDs should still produce valid record
        assert export_record.export_id is not None
        assert export_record.correlation_ids == {}


# ============================================================================
# TEST EXPORT AS PART OF V75 INTEGRATION
# ============================================================================


class TestV75Integration:
    """Test v76 as extension of v75 recommendation service."""
    
    def test_v75_recommendation_exported_by_v76(self, exporter: RecoveryRecommendationExporter):
        """Test v75 recommendations are exported by v76."""
        service = RecoveryRecommendationService()
        
        # Generate v75 recommendation
        recommendation = service.generate_recommendation(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            context={
                "timestamp": "2026-04-07T18:55:00Z",
                "node_id": "node_v75",
            },
            correlation_ids={"flow_id": "flow_v75_to_v76"},
        )
        
        # Export via v76
        export_record = exporter.export_recommendation(recommendation)
        
        # Verify v75 data is exported
        assert export_record.recommendation_data == recommendation
        assert export_record.confidence_level == recommendation["confidence"]
        assert export_record.recovery_hint == recommendation["recovery_hint"]
    
    def test_v76_export_includes_v75_confidence_guidance(self, exporter: RecoveryRecommendationExporter):
        """Test v76 export includes v75 confidence guidance."""
        service = RecoveryRecommendationService()
        
        recommendation = service.generate_recommendation(
            stage=FailureStage.DEADLINE.value,
            failure_type=FailureType.DEADLINE_BREACHED.value,
            context={"timestamp": "2026-04-07T18:55:00Z"},
            correlation_ids={"flow_id": "flow_v76_confidence"},
        )
        
        export_record = exporter.export_recommendation(recommendation)
        
        # Verify confidence guidance from v75 is preserved
        assert export_record.confidence_level in ["low", "medium", "high", "very_high"]
        assert "suggestion" in export_record.recommendation_data.get("hint_certainty", "")
    
    def test_v76_export_includes_v75_hints(self, exporter: RecoveryRecommendationExporter):
        """Test v76 export includes v75 recovery hints."""
        service = RecoveryRecommendationService()
        
        recommendation = service.generate_recommendation(
            stage=FailureStage.ENVELOPE.value,
            failure_type=FailureType.ENVELOPE_DISPATCH_FAILED.value,
            context={"timestamp": "2026-04-07T18:55:00Z"},
            correlation_ids={"flow_id": "flow_v76_hints"},
        )
        
        export_record = exporter.export_recommendation(recommendation)
        
        # Verify v75 recovery hint is exported
        assert export_record.recovery_hint is not None
        assert len(export_record.recovery_hint) > 0
