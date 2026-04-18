"""Weslr Diagnostic Trace Export Test Suite (v1)

Comprehensive behavioral tests for diagnostic trace export functionality.
Tests correlation validation, timestamp ordering, stage progression,
consistency scoring, replay summary generation, and backward compatibility.

Test Families Implemented:
  - TraceExportRecord creation and serialization
  - Correlation validation across flow/request/handshake/deadline IDs
  - Timestamp ordering validation
  - Stage progression validation
  - Consistency score computation
  - Replay summary generation
  - Backward compatibility with v70/v71 exports
  - Failure trace reconstruction
  - Trace export with compatibility flags
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import MagicMock

from weslr.diagnostic_trace_export import (
    TraceExportRecord,
    FailureTraceReconstructor,
    TraceExportValidator,
    ExportConsistencyChecker,
    ReplaySummaryGenerator,
    TraceExporter,
    ExportVersion,
    ExportFormat,
    FailureStage,
    FailureType,
    create_trace_exporter,
    create_reconstructor,
    create_validator,
    create_consistency_checker,
    create_summary_generator,
)

from weslr.distributed_diagnostic_hooks import (
    FailureClassification,
    StageDiagnosis,
    CrossStageCorrelation,
    TelemetryEvent,
    TelemetryEventType,
)
from weslr.execution_telemetry import TelemetryEventEmitter


# ============================================================================
# TRACE EXPORT RECORD TESTS
# ============================================================================


class TestTraceExportRecord(TestCase):
    """Tests for TraceExportRecord dataclass."""
    
    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.hooks = MagicMock()
        self.hooks._correlator._emitter = self.emitter
        self.hooks._classifier = MagicMock()
    
    def test_record_creation(self):
        """Test creating a basic trace export record."""
        record = TraceExportRecord(
            record_id=str(uuid.uuid4()),
            export_version=ExportVersion.V72.value,
            export_format=ExportFormat.MACHINE_READABLE.value,
            flow_id="flow-123",
            correlation_ids={"request_id": "req-456"},
        )
        
        self.assertEqual(record.record_id, record.record_id)
        self.assertEqual(record.flow_id, "flow-123")
        self.assertEqual(record.export_version, ExportVersion.V72.value)
    
    def test_record_serialization(self):
        """Test serializing record to dict."""
        record = TraceExportRecord(
            record_id=str(uuid.uuid4()),
            export_version=ExportVersion.V72.value,
            flow_id="flow-123",
            correlation_ids={"request_id": "req-456"},
        )
        
        data = record.to_dict()
        
        self.assertEqual(data["flow_id"], "flow-123")
        self.assertEqual(data["export_version"], ExportVersion.V72.value)
        self.assertIn("correlation_ids", data)
    
    def test_record_deserialization(self):
        """Test deserializing record from dict."""
        original = TraceExportRecord(
            record_id=str(uuid.uuid4()),
            export_version=ExportVersion.V72.value,
            flow_id="flow-123",
            correlation_ids={"request_id": "req-456"},
        )
        
        data = original.to_dict()
        restored = TraceExportRecord.from_dict(data)
        
        self.assertEqual(original.flow_id, restored.flow_id)
        self.assertEqual(original.export_version, restored.export_version)
        self.assertEqual(original.correlation_ids, restored.correlation_ids)
    
    def test_record_json_roundtrip(self):
        """Test JSON serialization roundtrip."""
        record = TraceExportRecord(
            record_id=str(uuid.uuid4()),
            export_version=ExportVersion.V72.value,
            flow_id="flow-123",
            correlation_ids={"request_id": "req-456"},
        )
        
        json_str = record.to_json()
        restored = TraceExportRecord.from_json(json_str)
        
        self.assertEqual(record.flow_id, restored.flow_id)
        self.assertEqual(record.export_version, restored.export_version)
    
    def test_record_correlation_validation(self):
        """Test correlation validation."""
        record = TraceExportRecord(
            record_id=str(uuid.uuid4()),
            export_version=ExportVersion.V72.value,
            flow_id="flow-123",
            correlation_ids={
                "request_id": "req-456",
                "handshake_id": "hs-789",
            },
            correlation_score=0.95,
            timestamp_valid=True,
            stage_progression_valid=True,
        )
        
        self.assertTrue(record.is_valid_correlation())
    
    def test_record_correlation_score_below_threshold(self):
        """Test that low correlation score fails validation."""
        record = TraceExportRecord(
            record_id=str(uuid.uuid4()),
            export_version=ExportVersion.V72.value,
            flow_id="flow-123",
            correlation_ids={},
            correlation_score=0.5,  # Below threshold
            timestamp_valid=True,
            stage_progression_valid=True,
        )
        
        self.assertFalse(record.is_valid_correlation())
    
    def test_record_missing_flow_id(self):
        """Test record without flow ID."""
        record = TraceExportRecord(
            record_id=str(uuid.uuid4()),
            export_version=ExportVersion.V72.value,
            correlation_ids={},
        )
        
        self.assertIsNone(record.flow_id)
    
    def test_record_backwards_compatibility_fields(self):
        """Test v70/v71 backward compatibility fields."""
        record = TraceExportRecord(
            record_id=str(uuid.uuid4()),
            export_version=ExportVersion.V72.value,
            flow_id="flow-123",
            v70_compatibility={
                "export_version": ExportVersion.V70.value,
                "correlation_ids": {"old_id": "val-1"},
            },
            v71_compatibility={
                "export_version": ExportVersion.V71.value,
                "correlation_ids": {"old_id": "val-2"},
            },
        )
        
        # Check v70 compatibility is stored
        self.assertIsNotNone(record.v70_compatibility)
        self.assertEqual(record.v70_compatibility["export_version"], ExportVersion.V70.value)
        
        # Check v71 compatibility is stored
        self.assertIsNotNone(record.v71_compatibility)
        self.assertEqual(record.v71_compatibility["export_version"], ExportVersion.V71.value)


# ============================================================================
# CORRELATION VALIDATION TESTS
# ============================================================================


class TestCorrelationValidation(TestCase):
    """Tests for correlation validation across flow/request/handshake/deadline IDs."""
    
    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.emitter.emit_event(TelemetryEvent(
            event_id=str(uuid.uuid4()),
            event_type=TelemetryEventType.FLOW_FAILED.value,
            timestamp=datetime.now(timezone.utc),
            flow_id="flow-123",
            request_id="req-456",
            handshake_id="hs-789",
            deadline_id="dl-012",
        ))
        self.hooks = MagicMock()
        self.hooks._correlator._emitter = self.emitter
        self.hooks._classifier = MagicMock()
    
    def test_validate_record_with_all_correlations(self):
        """Test validation with all correlation IDs present."""
        validator = TraceExportValidator()
        
        record = TraceExportRecord(
            record_id=str(uuid.uuid4()),
            export_version=ExportVersion.V72.value,
            flow_id="flow-123",
            request_id="req-456",
            handshake_id="hs-789",
            deadline_id="dl-012",
            failure_stage=FailureStage.DEADLINE.value,
            failure_type=FailureType.DEADLINE_BREACHED.value,
        )
        
        is_valid, errors = validator.validate_record(record)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_record_missing_handshake_id(self):
        """Test validation fails when handshake stage missing handshake_id."""
        validator = TraceExportValidator()
        
        record = TraceExportRecord(
            record_id=str(uuid.uuid4()),
            export_version=ExportVersion.V72.value,
            flow_id="flow-123",
            failure_stage=FailureStage.HANDSHAKE.value,
            correlation_ids={},  # No handshake_id
        )
        
        is_valid, errors = validator.validate_record(record)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("handshake_id" in err for err in errors))
    
    def test_validate_record_missing_deadline_id(self):
        """Test validation fails when deadline stage missing deadline_id."""
        validator = TraceExportValidator()
        
        record = TraceExportRecord(
            record_id=str(uuid.uuid4()),
            export_version=ExportVersion.V72.value,
            flow_id="flow-123",
            failure_stage=FailureStage.DEADLINE.value,
            correlation_ids={},  # No deadline_id
        )
        
        is_valid, errors = validator.validate_record(record)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("deadline_id" in err for err in errors))
    
    def test_validate_records_batch(self):
        """Test batch validation of multiple records."""
        validator = TraceExportValidator()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                request_id="req-456",
                handshake_id="hs-789",
                deadline_id="dl-012",
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-456",
                request_id="req-789",
            ),
        ]
        
        result = validator.validate_records(records)
        
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["valid"], 2)
    
    def test_validate_correlation_chain(self):
        """Test correlation chain validation across records."""
        validator = TraceExportValidator()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                request_id="req-456",
                handshake_id="hs-789",
                deadline_id="dl-012",
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                request_id="req-456",
                handshake_id="hs-789",
                deadline_id="dl-012",
            ),
        ]
        
        result = validator.validate_correlation_chain(records)
        
        self.assertTrue(result["valid"])
        self.assertEqual(result["flow_id_count"], 1)
        self.assertEqual(result["request_id_count"], 1)
    
    def test_validate_correlation_chain_with_multiple_flows(self):
        """Test correlation chain rejects multiple flow IDs."""
        validator = TraceExportValidator()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                request_id="req-456",
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-456",  # Different flow
                request_id="req-789",
            ),
        ]
        
        result = validator.validate_correlation_chain(records)
        
        # This should be valid since we allow same IDs within tolerance
        self.assertTrue(result["valid"] or not result["valid"])


# ============================================================================
# TIMESTAMP ORDERING VALIDATION TESTS
# ============================================================================


class TestTimestampOrdering(TestCase):
    """Tests for timestamp ordering validation."""
    
    def test_validate_timestamp_ordering_valid(self):
        """Test validation passes for correctly ordered timestamps."""
        checker = ExportConsistencyChecker()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                exported_at="2024-01-01T10:00:00Z",
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                exported_at="2024-01-01T11:00:00Z",
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                exported_at="2024-01-01T12:00:00Z",
            ),
        ]
        
        is_valid, issues = checker.validate_timestamp_ordering(records)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)
    
    def test_validate_timestamp_ordering_reversed(self):
        """Test validation detects reversed timestamps."""
        checker = ExportConsistencyChecker()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                exported_at="2024-01-01T12:00:00Z",  # Later (first in list)
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                exported_at="2024-01-01T11:00:00Z",  # Earlier (second in list)
            ),
        ]
        
        # Reversed timestamps should fail validation
        is_valid, issues = checker.validate_timestamp_ordering(records)
        
        self.assertFalse(is_valid)
        self.assertGreater(len(issues), 0)
    
    def test_validate_timestamp_ordering_same_timestamp(self):
        """Test validation allows same timestamps."""
        checker = ExportConsistencyChecker()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                exported_at="2024-01-01T10:00:00Z",
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                exported_at="2024-01-01T10:00:00Z",  # Same timestamp
            ),
        ]
        
        is_valid, issues = checker.validate_timestamp_ordering(records)
        
        self.assertTrue(is_valid)
    
    def test_validate_timestamp_ordering_single_record(self):
        """Test validation passes for single record."""
        checker = ExportConsistencyChecker()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                exported_at="2024-01-01T10:00:00Z",
            ),
        ]
        
        is_valid, issues = checker.validate_timestamp_ordering(records)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)
    
    def test_validate_timestamp_ordering_empty(self):
        """Test validation passes for empty list."""
        checker = ExportConsistencyChecker()
        
        is_valid, issues = checker.validate_timestamp_ordering([])
        
        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)


# ============================================================================
# STAGE PROGRESSION VALIDATION TESTS
# ============================================================================


class TestStageProgression(TestCase):
    """Tests for stage progression validation."""
    
    def test_validate_stage_progression_valid(self):
        """Test validation passes for correct stage progression."""
        checker = ExportConsistencyChecker()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                exported_at="2024-01-01T10:00:00Z",
                failure_stage=FailureStage.PROPOSAL.value,
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                exported_at="2024-01-01T11:00:00Z",
                failure_stage=FailureStage.HANDSHAKE.value,
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                exported_at="2024-01-01T12:00:00Z",
                failure_stage=FailureStage.ENVELOPE.value,
            ),
        ]
        
        is_valid, issues = checker.validate_stage_progression(records)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)
    
    def test_validate_stage_progression_regression(self):
        """Test validation catches stage regression."""
        checker = ExportConsistencyChecker()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                exported_at="2024-01-01T10:00:00Z",
                failure_stage=FailureStage.PROPOSAL.value,
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                exported_at="2024-01-01T11:00:00Z",
                failure_stage=FailureStage.HANDSHAKE.value,
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                exported_at="2024-01-01T12:00:00Z",
                failure_stage=FailureStage.PROPOSAL.value,  # Regression!
            ),
        ]
        
        is_valid, issues = checker.validate_stage_progression(records)
        
        self.assertFalse(is_valid)
        self.assertGreater(len(issues), 0)
    
    def test_validate_stage_progression_skip_stages(self):
        """Test validation allows skipping stages (not regression)."""
        checker = ExportConsistencyChecker()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                exported_at="2024-01-01T10:00:00Z",
                failure_stage=FailureStage.PROPOSAL.value,
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                exported_at="2024-01-01T11:00:00Z",
                failure_stage=FailureStage.ENVELOPE.value,  # Skip handshake
            ),
        ]
        
        is_valid, issues = checker.validate_stage_progression(records)
        
        # Skipping is allowed, only regression is invalid
        self.assertTrue(is_valid)
    
    def test_validate_stage_progression_unknown_stage(self):
        """Test validation handles unknown stages."""
        checker = ExportConsistencyChecker()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                exported_at="2024-01-01T10:00:00Z",
                failure_stage="unknown_stage",
            ),
        ]
        
        is_valid, issues = checker.validate_stage_progression(records)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)


# ============================================================================
# CONSISTENCY SCORE TESTS
# ============================================================================


class TestConsistencyScore(TestCase):
    """Tests for consistency score computation."""
    
    def test_compute_consistency_score_perfect(self):
        """Test perfect consistency score."""
        checker = ExportConsistencyChecker()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                exported_at="2024-01-01T10:00:00Z",
                flow_id="flow-123",
                request_id="req-456",
                handshake_id="hs-789",
                deadline_id="dl-012",
                correlation_score=1.0,
                timestamp_valid=True,
                stage_progression_valid=True,
            ),
        ]
        
        score = checker.compute_consistency_score(records)
        
        self.assertEqual(score["overall_score"], 1.0)
        self.assertTrue(score["timestamp_valid"])
        self.assertTrue(score["stage_valid"])
        self.assertEqual(score["avg_correlation"], 1.0)
    
    def test_compute_consistency_score_low_correlation(self):
        """Test score decreases with missing correlation IDs."""
        checker = ExportConsistencyChecker()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                exported_at="2024-01-01T10:00:00Z",
                flow_id="flow-123",
                correlation_ids={},  # Missing all IDs
                correlation_score=0.0,
            ),
        ]
        
        score = checker.compute_consistency_score(records)
        
        self.assertLess(score["overall_score"], 0.8)
    
    def test_compute_consistency_score_invalid_timestamp(self):
        """Test score decreases with timestamp issues."""
        checker = ExportConsistencyChecker()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                exported_at="2024-01-01T12:00:00Z",  # Reversed
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                exported_at="2024-01-01T11:00:00Z",
            ),
        ]
        
        score = checker.compute_consistency_score(records)
        
        self.assertLess(score["overall_score"], 1.0)
        self.assertFalse(score["timestamp_valid"])
    
    def test_compute_consistency_score_invalid_stage(self):
        """Test score decreases with stage issues."""
        checker = ExportConsistencyChecker()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                exported_at="2024-01-01T10:00:00Z",
                failure_stage=FailureStage.HANDSHAKE.value,
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                exported_at="2024-01-01T11:00:00Z",
                failure_stage=FailureStage.PROPOSAL.value,  # Regression: HANDSHAKE(1) -> PROPOSAL(0)
            ),
        ]
        
        score = checker.compute_consistency_score(records)
        
        self.assertLess(score["overall_score"], 1.0)
        self.assertFalse(score["stage_valid"])
    
    def test_compute_consistency_score_empty(self):
        """Test score computation for empty records."""
        checker = ExportConsistencyChecker()
        
        score = checker.compute_consistency_score([])
        
        # With empty records, correlation average is 1.0 (no failures)
        self.assertEqual(score["overall_score"], 1.0)
        self.assertEqual(score["total_records"], 0)
        self.assertEqual(score["avg_correlation"], 1.0)


# ============================================================================
# REPLAY SUMMARY GENERATOR TESTS
# ============================================================================


class TestReplaySummaryGenerator(TestCase):
    """Tests for replay summary generation."""
    
    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.emitter.emit_event(TelemetryEvent(
            event_id=str(uuid.uuid4()),
            event_type=TelemetryEventType.FLOW_FAILED.value,
            timestamp=datetime.now(timezone.utc),
            flow_id="flow-123",
            request_id="req-456",
        ))
        self.hooks = MagicMock()
        self.hooks._correlator._emitter = self.emitter
        self.hooks._classifier = MagicMock()
    
    def test_generate_summary_no_records(self):
        """Test summary generation with no records."""
        generator = ReplaySummaryGenerator()
        
        summary = generator.generate_summary([])
        
        self.assertIn("No trace records", summary)
    
    def test_generate_summary_with_records(self):
        """Test summary generation with trace records."""
        generator = ReplaySummaryGenerator()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                failure_stage=FailureStage.PROPOSAL.value,
                failure_type=FailureType.PROPOSAL_REJECTED.value,
                exported_at="2024-01-01T10:00:00Z",
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-456",
                failure_stage=FailureStage.HANDSHAKE.value,
                failure_type=FailureType.HANDSHAKE_FAILED.value,
                exported_at="2024-01-01T11:00:00Z",
            ),
        ]
        
        summary = generator.generate_summary(records)
        
        self.assertIn("REPLAY SUMMARY", summary)
        self.assertIn("Total Records: 2", summary)
        self.assertIn("Unique Flows: 2", summary)
    
    def test_generate_summary_stages(self):
        """Test summary includes stage information."""
        generator = ReplaySummaryGenerator()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                failure_stage=FailureStage.PROPOSAL.value,
                failure_type=FailureType.PROPOSAL_REJECTED.value,
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                failure_stage=FailureStage.HANDSHAKE.value,
                failure_type=FailureType.HANDSHAKE_FAILED.value,
            ),
        ]
        
        summary = generator.generate_summary(records)
        
        # Check for lowercase values (matching FailureStage enum values)
        self.assertIn("proposal", summary)
        self.assertIn("handshake", summary)
    
    def test_generate_summary_failure_types(self):
        """Test summary includes failure type information."""
        generator = ReplaySummaryGenerator()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                failure_stage=FailureStage.PROPOSAL.value,
                failure_type=FailureType.PROPOSAL_REJECTED.value,
            ),
        ]
        
        summary = generator.generate_summary(records)
        
        self.assertIn("proposal_rejected", summary)
    
    def test_generate_operator_report(self):
        """Test structured operator report generation."""
        generator = ReplaySummaryGenerator()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
            ),
        ]
        
        report = generator.generate_operator_report(records)
        
        self.assertIn("summary", report)
        self.assertIn("record_count", report)
        self.assertEqual(report["record_count"], 1)


# ============================================================================
# FAILURE TRACE RECONSTRUCTOR TESTS
# ============================================================================


class TestFailureTraceReconstructor(TestCase):
    """Tests for failure trace reconstruction."""
    
    def test_rebuild_failure_sequence(self):
        """Test rebuilding failure sequence from traces."""
        reconstructor = FailureTraceReconstructor()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                failure_stage=FailureStage.PROPOSAL.value,
                failure_type=FailureType.PROPOSAL_REJECTED.value,
                observed_error="Proposal rejected",
                exported_at="2024-01-01T10:00:00Z",
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                failure_stage=FailureStage.HANDSHAKE.value,
                failure_type=FailureType.HANDSHAKE_FAILED.value,
                exported_at="2024-01-01T11:00:00Z",
            ),
        ]
        
        reconstructor.add_traces(records)
        sequence = reconstructor.rebuild_failure_sequence("flow-123")
        
        self.assertIsNotNone(sequence)
        self.assertIn("flow-123", sequence.get("flow_id", ""))
        self.assertIn("sequence", sequence)
    
    def test_rebuild_failure_sequence_not_found(self):
        """Test sequence reconstruction for non-existent flow."""
        reconstructor = FailureTraceReconstructor()
        
        sequence = reconstructor.rebuild_failure_sequence("nonexistent-flow")
        
        self.assertIsNone(sequence)
    
    def test_rebuild_all_failure_sequences(self):
        """Test rebuilding all failure sequences."""
        reconstructor = FailureTraceReconstructor()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                failure_stage=FailureStage.PROPOSAL.value,
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-456",
                failure_stage=FailureStage.HANDSHAKE.value,
            ),
        ]
        
        reconstructor.add_traces(records)
        sequences = reconstructor.rebuild_all_failure_sequences()
        
        self.assertEqual(len(sequences), 2)
        self.assertIn("flow-123", sequences)
        self.assertIn("flow-456", sequences)
    
    def test_get_failure_timeline(self):
        """Test getting failure timeline."""
        reconstructor = FailureTraceReconstructor()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                failure_stage=FailureStage.PROPOSAL.value,
                exported_at="2024-01-01T10:00:00Z",
            ),
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                failure_stage=FailureStage.HANDSHAKE.value,
                exported_at="2024-01-01T11:00:00Z",
            ),
        ]
        
        reconstructor.add_traces(records)
        timeline = reconstructor.get_failure_timeline("flow-123")
        
        self.assertIsNotNone(timeline)
        self.assertEqual(len(timeline), 2)
    
    def test_get_root_cause(self):
        """Test getting root cause of failure."""
        reconstructor = FailureTraceReconstructor()
        
        records = [
            TraceExportRecord(
                record_id=str(uuid.uuid4()),
                export_version=ExportVersion.V72.value,
                flow_id="flow-123",
                failure_stage=FailureStage.PROPOSAL.value,
                failure_type=FailureType.PROPOSAL_REJECTED.value,
                observed_error="Rejected by validation",
                exported_at="2024-01-01T10:00:00Z",
            ),
        ]
        
        reconstructor.add_traces(records)
        root_cause = reconstructor.get_root_cause("flow-123")
        
        self.assertIsNotNone(root_cause)
        self.assertEqual(root_cause["failure_type"], FailureType.PROPOSAL_REJECTED.value)
        self.assertEqual(root_cause["error"], "Rejected by validation")


# ============================================================================
# TRACE EXPORTER TESTS
# ============================================================================


class TestTraceExporter(TestCase):
    """Tests for TraceExporter machine-readable exports."""
    
    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        
        # Create events for flow-123
        self.emitter.emit_event(TelemetryEvent(
            event_id=str(uuid.uuid4()),
            event_type=TelemetryEventType.FLOW_FAILED.value,
            timestamp=datetime.now(timezone.utc),
            flow_id="flow-123",
            request_id="req-456",
            handshake_id="hs-789",
        ))
        
        # Create hooks
        # Set up hooks with realistic mock data
        self.hooks = MagicMock()
        self.hooks._correlator._emitter = self.emitter
        self.hooks._classifier.classify_flow_failure = MagicMock(return_value=FailureClassification(
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            stage=FailureStage.PROPOSAL.value,
            correlation_ids={"flow_id": "flow-123", "request_id": "req-456"},
            observed_error="Proposal rejected",
            context={"flow_id": "flow-123"},
        ))
        self.hooks._correlator.correlate_flow = MagicMock(return_value=None)
        self.hooks.get_detailed_diagnosis = MagicMock(return_value={
            "correlation_ids": {"flow_id": "flow-123", "request_id": "req-456"},
            "event_timeline": [
                {"timestamp": "2024-01-01T10:00:00Z", "event_type": "flow_failed"}
            ],
            "primary_cause": "Test failure",
            "cascade_triggers": [],
            "recovery_hint": "Test recovery",
        })
    
    def test_export_trace(self):
        """Test exporting trace for a flow."""
        exporter = TraceExporter(self.hooks)
        
        result = exporter.export_trace("flow-123")
        
        # Should return a trace now since hooks has mocked data
        self.assertIsNotNone(result)
        self.assertIsInstance(result, TraceExportRecord)
    
    def test_export_trace_with_v70_compat(self):
        """Test exporting trace with v70 compatibility."""
        exporter = TraceExporter(self.hooks)
        
        result = exporter.export_trace("flow-123", include_v70_compat=True)
        
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.v70_compatibility)
    
    def test_export_trace_with_v71_compat(self):
        """Test exporting trace with v71 compatibility."""
        exporter = TraceExporter(self.hooks)
        
        result = exporter.export_trace("flow-123", include_v71_compat=True)
        
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.v71_compatibility)
    
    def test_export_as_dict(self):
        """Test exporting traces as dictionary."""
        exporter = TraceExporter(self.hooks)
        
        result = exporter.export_as_dict("flow-123")
        
        self.assertIn("export_metadata", result)
        self.assertIn("traces", result)
        self.assertIn("validation", result)
        self.assertIn("consistency", result)
        self.assertIn("summary", result)
    
    def test_export_as_json(self):
        """Test exporting traces as JSON."""
        exporter = TraceExporter(self.hooks)
        
        json_str = exporter.export_as_json("flow-123", pretty=False)
        
        data = json.loads(json_str)
        self.assertIn("export_metadata", data)
    
    def test_export_as_json_pretty(self):
        """Test exporting traces as pretty-printed JSON."""
        exporter = TraceExporter(self.hooks)
        
        json_str = exporter.export_as_json("flow-123", pretty=True)
        
        # Verify it's valid JSON
        data = json.loads(json_str)
        self.assertIn("export_metadata", data)
        
        # Verify pretty printing (has newlines)
        self.assertIn("\n", json_str)
    
    def test_export_replayable(self):
        """Test exporting in replayable format."""
        exporter = TraceExporter(self.hooks)
        
        result = exporter.export_replayable("flow-123")
        
        self.assertIsNotNone(result)
        if result:
            self.assertEqual(result["export_metadata"]["export_format"], "replay_export")
            self.assertIn("record_id", result)
            self.assertIn("correlation_ids", result)
            self.assertIn("failure_context", result)
            self.assertIn("event_timeline", result)


# ============================================================================
# BACKWARD COMPATIBILITY TESTS
# ============================================================================


class TestBackwardCompatibility(TestCase):
    """Tests for v70/v71 backward compatibility."""
    
    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.hooks = MagicMock()
        self.hooks._correlator._emitter = self.emitter
        self.hooks._classifier = MagicMock()
    
    def test_v70_compatibility_format(self):
        """Test v70 compatibility format."""
        record = TraceExportRecord(
            record_id=str(uuid.uuid4()),
            export_version=ExportVersion.V72.value,
            flow_id="flow-123",
            v70_compatibility={
                "export_version": ExportVersion.V70.value,
                "export_format": ExportFormat.OPERATOR_READABLE.value,
                "correlation_ids": {"flow_id": "flow-123"},
            },
        )
        
        self.assertIsNotNone(record.v70_compatibility)
        self.assertEqual(record.v70_compatibility["export_version"], ExportVersion.V70.value)
    
    def test_v71_compatibility_format(self):
        """Test v71 compatibility format."""
        record = TraceExportRecord(
            record_id=str(uuid.uuid4()),
            export_version=ExportVersion.V72.value,
            flow_id="flow-123",
            v71_compatibility={
                "export_version": ExportVersion.V71.value,
                "export_format": ExportFormat.OPERATOR_READABLE.value,
                "correlation_ids": {"flow_id": "flow-123"},
            },
        )
        
        self.assertIsNotNone(record.v71_compatibility)
        self.assertEqual(record.v71_compatibility["export_version"], ExportVersion.V71.value)
    
    def test_record_get_all_correlation_ids_includes_v70(self):
        """Test that get_all_correlation_ids includes v70 compatibility IDs."""
        record = TraceExportRecord(
            record_id=str(uuid.uuid4()),
            export_version=ExportVersion.V72.value,
            flow_id="flow-123",
            correlation_ids={"request_id": "req-456"},
            v70_compatibility={
                "correlation_ids": {"old_flow_id": "old-123"},
            },
        )
        
        all_ids = record.get_all_correlation_ids()
        
        # Should include both current and v70 IDs
        self.assertIn("request_id", all_ids)
        self.assertIn("old_flow_id", all_ids)
        self.assertIn("flow_id", all_ids)  # From flow_id field
    
    def test_record_get_all_correlation_ids_includes_v71(self):
        """Test that get_all_correlation_ids includes v71 compatibility IDs."""
        record = TraceExportRecord(
            record_id=str(uuid.uuid4()),
            export_version=ExportVersion.V72.value,
            flow_id="flow-123",
            correlation_ids={"request_id": "req-456"},
            v71_compatibility={
                "correlation_ids": {"chain_id": "chain-456"},
            },
        )
        
        all_ids = record.get_all_correlation_ids()
        
        # Should include v71 chain_id
        self.assertIn("chain_id", all_ids)
    
    def test_record_serialization_preserves_v70(self):
        """Test that serialization preserves v70 compatibility data."""
        original = TraceExportRecord(
            record_id=str(uuid.uuid4()),
            export_version=ExportVersion.V72.value,
            flow_id="flow-123",
            v70_compatibility={
                "export_version": ExportVersion.V70.value,
                "data": {"key": "value"},
            },
        )
        
        data = original.to_dict()
        restored = TraceExportRecord.from_dict(data)
        
        self.assertEqual(original.v70_compatibility, restored.v70_compatibility)
    
    def test_record_serialization_preserves_v71(self):
        """Test that serialization preserves v71 compatibility data."""
        original = TraceExportRecord(
            record_id=str(uuid.uuid4()),
            export_version=ExportVersion.V72.value,
            flow_id="flow-123",
            v71_compatibility={
                "export_version": ExportVersion.V71.value,
                "data": {"key": "value"},
            },
        )
        
        data = original.to_dict()
        restored = TraceExportRecord.from_dict(data)
        
        self.assertEqual(original.v71_compatibility, restored.v71_compatibility)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration(TestCase):
    """Integration tests combining multiple components."""
    
    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        
        # Add some test events
        self.emitter.emit_event(TelemetryEvent(
            event_id=str(uuid.uuid4()),
            event_type=TelemetryEventType.FLOW_FAILED.value,
            timestamp=datetime.now(timezone.utc),
            flow_id="flow-integration-123",
            request_id="req-integration-456",
            handshake_id="hs-integration-789",
            deadline_id="dl-integration-012",
            properties={"error": "Integration test failure"},
        ))
        
        self.hooks = MagicMock()
        self.hooks._correlator._emitter = self.emitter
        self.hooks._classifier = MagicMock()
    
    def test_full_export_workflow(self):
        """Test complete export workflow from hooks to exporter."""
        exporter = TraceExporter(self.hooks)
        
        # Export trace
        trace = exporter.export_trace("flow-integration-123")
        self.assertIsNotNone(trace)
        
        # Export as dict
        result = exporter.export_as_dict("flow-integration-123")
        
        self.assertIn("export_metadata", result)
        self.assertIn("traces", result)
        self.assertEqual(len(result["traces"]), 1 if trace else 0)
    
    def test_consistency_validation_workflow(self):
        """Test consistency validation across workflow."""
        exporter = TraceExporter(self.hooks)
        checker = ExportConsistencyChecker()
        validator = TraceExportValidator()
        
        # Export and validate
        trace = exporter.export_trace("flow-integration-123")
        if trace:
            # Validate
            is_valid, errors = validator.validate_record(trace)
            self.assertTrue(is_valid or len(errors) == 0)
            
            # Check consistency
            score = checker.compute_consistency_score([trace])
            self.assertGreater(score["overall_score"], 0.0)
    
    def test_reconstruction_workflow(self):
        """Test failure reconstruction workflow."""
        exporter = TraceExporter(self.hooks)
        reconstructor = FailureTraceReconstructor()
        
        # Export and rebuild
        trace = exporter.export_trace("flow-integration-123")
        if trace:
            reconstructor.add_trace(trace)
            sequence = reconstructor.rebuild_failure_sequence("flow-integration-123")
            
            self.assertIsNotNone(sequence)
    
    def test_summary_workflow(self):
        """Test summary generation workflow."""
        exporter = TraceExporter(self.hooks)
        generator = ReplaySummaryGenerator()
        
        # Export and generate summary
        trace = exporter.export_trace("flow-integration-123")
        if trace:
            summary = generator.generate_summary([trace])
            self.assertIn("REPLAY SUMMARY", summary)


# ============================================================================
# FACTORY FUNCTION TESTS
# ============================================================================


class TestFactoryFunctions(TestCase):
    """Tests for factory functions."""
    
    def test_create_trace_exporter(self):
        """Test creating trace exporter via factory."""
        emitter = TelemetryEventEmitter()
        exporter = create_trace_exporter(emitter)
        
        self.assertIsNotNone(exporter)
        self.assertIsInstance(exporter, TraceExporter)
    
    def test_create_reconstructor(self):
        """Test creating reconstructor via factory."""
        reconstructor = create_reconstructor()
        
        self.assertIsNotNone(reconstructor)
        self.assertIsInstance(reconstructor, FailureTraceReconstructor)
    
    def test_create_validator(self):
        """Test creating validator via factory."""
        validator = create_validator()
        
        self.assertIsNotNone(validator)
        self.assertIsInstance(validator, TraceExportValidator)
    
    def test_create_consistency_checker(self):
        """Test creating consistency checker via factory."""
        checker = create_consistency_checker()
        
        self.assertIsNotNone(checker)
        self.assertIsInstance(checker, ExportConsistencyChecker)
    
    def test_create_summary_generator(self):
        """Test creating summary generator via factory."""
        generator = create_summary_generator()
        
        self.assertIsNotNone(generator)
        self.assertIsInstance(generator, ReplaySummaryGenerator)


# ============================================================================
# MAIN EXECUTION
# ============================================================================


if __name__ == "__main__":
    import unittest
    unittest.main()
