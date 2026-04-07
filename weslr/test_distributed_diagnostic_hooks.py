"""Tests for Cross-Node Diagnostic Reasoning Hooks (v70)

Behavioral tests for failure classification, stage-local diagnosis,
cross-stage correlation, and diagnostic summary generation.

Test Doctrine version: 1.0.0 (2026-04-07)
"""

import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.distributed_diagnostic_hooks import (
    FailureType,
    FailureStage,
    FailureClassification,
    FailureClassifier,
    StageDiagnosis,
    StageDiagnosisBuilder,
    CrossStageCorrelation,
    CrossStageCorrelator,
    DiagnosticSummary,
    DiagnosticSummaryBuilder,
    DiagnosticHooks,
    create_diagnostic_hooks,
)
from weslr.execution_telemetry import (
    TelemetryEventEmitter,
    TelemetryEvent,
    TelemetryEventType,
)
from weslr.remote_action_proposal import RemoteActionProposal, ProposalStatus


# ============================================================================
# FAILURE CLASSIFICATION TESTS
# ============================================================================


class TestFailureClassificationModel(unittest.TestCase):
    """Test failure classification data models."""

    def test_classification_creation(self):
        """FailureClassification created with required fields."""
        classification = FailureClassification(
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            stage=FailureStage.PROPOSAL.value,
            node_id="node-a",
            observed_error="Rejected by trust gate"
        )
        
        self.assertEqual(classification.failure_type, FailureType.PROPOSAL_REJECTED.value)
        self.assertEqual(classification.stage, FailureStage.PROPOSAL.value)
        self.assertEqual(classification.node_id, "node-a")
        self.assertEqual(classification.observed_error, "Rejected by trust gate")

    def test_classification_serialization(self):
        """FailureClassification serializes to dict."""
        classification = FailureClassification(
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            stage=FailureStage.HANDSHAKE.value,
            observed_error="Handshake timeout"
        )
        
        data = classification.to_dict()
        
        self.assertEqual(data["failure_type"], FailureType.HANDSHAKE_FAILED.value)
        self.assertEqual(data["stage"], FailureStage.HANDSHAKE.value)
        self.assertEqual(data["observed_error"], "Handshake timeout")

    def test_classification_deserialization(self):
        """FailureClassification deserializes from dict."""
        data = {
            "failure_type": FailureType.DEADLINE_BREACHED.value,
            "stage": FailureStage.DEADLINE.value,
            "node_id": "node-b",
            "observed_error": "Deadline exceeded",
            "correlation_ids": {"flow_id": "flow-123"}
        }
        
        classification = FailureClassification.from_dict(data)
        
        self.assertEqual(classification.failure_type, FailureType.DEADLINE_BREACHED.value)
        self.assertEqual(classification.stage, FailureStage.DEADLINE.value)
        self.assertEqual(classification.observed_error, "Deadline exceeded")
        self.assertEqual(classification.correlation_ids["flow_id"], "flow-123")


class TestFailureClassifierBehavior(unittest.TestCase):
    """Test failure classifier behavior."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.classifier = FailureClassifier(self.emitter)
    
    def test_classify_completed_flow(self):
        """Completed flow returns no failure."""
        # Create a flow that completed successfully
        flow_id = "flow-completed"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_CREATED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e2",
                event_type=TelemetryEventType.FLOW_COMPLETED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        classification = self.classifier.classify_flow_failure(flow_id)
        self.assertIsNone(classification)
    
    def test_classify_failed_flow(self):
        """Failed flow returns classification."""
        flow_id = "flow-failed"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id,
                properties={"error": "Execution failed", "reason": "timeout"}
            )
        )
        
        classification = self.classifier.classify_flow_failure(flow_id)
        self.assertIsNotNone(classification)
        self.assertEqual(classification.stage, FailureStage.ENVELOPE.value)
        self.assertEqual(classification.failure_type, FailureType.UNKNOWN.value)
    
    def test_classify_rejected_flow(self):
        """Rejected flow returns classification."""
        flow_id = "flow-rejected"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_REJECTED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id,
                properties={"error": "Proposal rejected", "reason": "trust"}
            )
        )
        
        classification = self.classifier.classify_flow_failure(flow_id)
        self.assertIsNotNone(classification)
        self.assertEqual(classification.stage, FailureStage.PROPOSAL.value)
        self.assertEqual(classification.failure_type, FailureType.PROPOSAL_REJECTED.value)
    
    def test_classify_handshake_failure(self):
        """Handshake failure flow returns classification."""
        flow_id = "handshake-failed"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.HANDSHAKE_FAILURE.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id,
                properties={"error": "Handshake timeout"}
            )
        )
        
        classification = self.classifier.classify_flow_failure(flow_id)
        self.assertIsNotNone(classification)
        self.assertEqual(classification.stage, FailureStage.HANDSHAKE.value)
        self.assertEqual(classification.failure_type, FailureType.HANDSHAKE_FAILED.value)
    
    def test_classify_deadline_breach(self):
        """Deadline breach flow returns classification."""
        flow_id = "deadline-breach"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.DEADLINE_BREACH.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        classification = self.classifier.classify_flow_failure(flow_id)
        self.assertIsNotNone(classification)
        self.assertEqual(classification.stage, FailureStage.DEADLINE.value)
        self.assertEqual(classification.failure_type, FailureType.DEADLINE_BREACHED.value)
    
    def test_classify_all_failures(self):
        """Classify all failures across multiple flows."""
        # Flow 1 - failed
        flow1 = "flow-1"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="f1e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow1
            )
        )
        
        # Flow 2 - completed
        flow2 = "flow-2"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="f2e1",
                event_type=TelemetryEventType.FLOW_CREATED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow2
            )
        )
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="f2e2",
                event_type=TelemetryEventType.FLOW_COMPLETED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow2
            )
        )
        
        classifications = self.classifier.classify_all_failures()
        self.assertEqual(len(classifications), 1)
        self.assertEqual(classifications[0].flow_id if hasattr(classifications[0], 'flow_id') else classifications[0].correlation_ids.get('flow_id'), flow1)


# ============================================================================
# STAGE DIAGNOSIS TESTS
# ============================================================================


class TestStageDiagnosisModel(unittest.TestCase):
    """Test stage diagnosis data models."""

    def test_diagnosis_creation(self):
        """StageDiagnosis created with required fields."""
        diagnosis = StageDiagnosis(
            stage=FailureStage.PROPOSAL.value,
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            observed_errors=["Rejected by trust gate"],
            likely_cause="Trust threshold not met"
        )
        
        self.assertEqual(diagnosis.stage, FailureStage.PROPOSAL.value)
        self.assertEqual(diagnosis.failure_type, FailureType.PROPOSAL_REJECTED.value)
        self.assertEqual(diagnosis.likely_cause, "Trust threshold not met")

    def test_diagnosis_serialization(self):
        """StageDiagnosis serializes to dict."""
        diagnosis = StageDiagnosis(
            stage=FailureStage.HANDSHAKE.value,
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            likely_cause="Protocol mismatch",
            recovery_hint="Update protocol version"
        )
        
        data = diagnosis.to_dict()
        
        self.assertEqual(data["stage"], FailureStage.HANDSHAKE.value)
        self.assertEqual(data["likely_cause"], "Protocol mismatch")
        self.assertEqual(data["recovery_hint"], "Update protocol version")

    def test_diagnosis_deserialization(self):
        """StageDiagnosis deserializes from dict."""
        data = {
            "stage": FailureStage.DEADLINE.value,
            "failure_type": FailureType.DEADLINE_BREACHED.value,
            "observed_errors": ["Task took too long"],
            "likely_cause": "Task complexity exceeded estimate",
            "recovery_hint": "Increase deadline or split task"
        }
        
        diagnosis = StageDiagnosis.from_dict(data)
        
        self.assertEqual(diagnosis.stage, FailureStage.DEADLINE.value)
        self.assertEqual(diagnosis.likely_cause, "Task complexity exceeded estimate")
        self.assertEqual(diagnosis.recovery_hint, "Increase deadline or split task")


class TestStageDiagnosisBuilderBehavior(unittest.TestCase):
    """Test stage diagnosis builder behavior."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.classifier = FailureClassifier(self.emitter)
        self.builder = StageDiagnosisBuilder()
    
    def test_build_diagnosis_proposal(self):
        """Build diagnosis for proposal failure."""
        classification = FailureClassification(
            failure_type=FailureType.PROPOSAL_REJECTED.value,
            stage=FailureStage.PROPOSAL.value,
            observed_error="Rejected by trust gate",
            context={"flow_id": "flow-123"}
        )
        
        diagnosis = self.builder.build_diagnosis(classification)
        
        self.assertEqual(diagnosis.stage, FailureStage.PROPOSAL.value)
        self.assertEqual(diagnosis.failure_type, FailureType.PROPOSAL_REJECTED.value)
        self.assertIsNotNone(diagnosis.likely_cause)
        self.assertIsNotNone(diagnosis.recovery_hint)
        # Recovery hint should be a suggestion
        self.assertIsNotNone(diagnosis.recovery_hint)
    
    def test_build_diagnosis_handshake(self):
        """Build diagnosis for handshake failure."""
        classification = FailureClassification(
            failure_type=FailureType.HANDSHAKE_FAILED.value,
            stage=FailureStage.HANDSHAKE.value,
            observed_error="Handshake timeout",
            context={"flow_id": "handshake-456"}
        )
        
        diagnosis = self.builder.build_diagnosis(classification)
        
        self.assertEqual(diagnosis.stage, FailureStage.HANDSHAKE.value)
        self.assertIsNotNone(diagnosis.likely_cause)
        self.assertIsNotNone(diagnosis.recovery_hint)
    
    def test_build_diagnosis_deadline(self):
        """Build diagnosis for deadline failure."""
        classification = FailureClassification(
            failure_type=FailureType.DEADLINE_BREACHED.value,
            stage=FailureStage.DEADLINE.value,
            observed_error="Deadline exceeded",
            context={"flow_id": "deadline-789"}
        )
        
        diagnosis = self.builder.build_diagnosis(classification)
        
        self.assertEqual(diagnosis.stage, FailureStage.DEADLINE.value)
        self.assertIsNotNone(diagnosis.likely_cause)
        self.assertIsNotNone(diagnosis.recovery_hint)


# ============================================================================
# CROSS-STAGE CORRELATION TESTS
# ============================================================================


class TestCrossStageCorrelationModel(unittest.TestCase):
    """Test cross-stage correlation data models."""

    def test_correlation_creation(self):
        """CrossStageCorrelation created with flow ID."""
        correlation = CrossStageCorrelation(flow_id="flow-123")
        
        self.assertEqual(correlation.flow_id, "flow-123")
        self.assertEqual(len(correlation.failures_by_stage), 0)

    def test_correlation_serialization(self):
        """CrossStageCorrelation serializes to dict."""
        correlation = CrossStageCorrelation(
            flow_id="flow-456",
            primary_cause="Handshake failure",
            cascade_triggers=["Cascade: envelope failed after handshake"],
            recovery_hint="Verify handshake configuration"
        )
        
        data = correlation.to_dict()
        
        self.assertEqual(data["flow_id"], "flow-456")
        self.assertEqual(data["primary_cause"], "Handshake failure")
        self.assertEqual(len(data["cascade_triggers"]), 1)


class TestCrossStageCorrelatorBehavior(unittest.TestCase):
    """Test cross-stage correlator behavior."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.correlator = CrossStageCorrelator(self.emitter)
    
    def test_correlate_completed_flow(self):
        """Completed flow returns no correlation."""
        flow_id = "flow-completed"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_CREATED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e2",
                event_type=TelemetryEventType.FLOW_COMPLETED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        correlation = self.correlator.correlate_flow(flow_id)
        self.assertIsNone(correlation)
    
    def test_correlate_failed_flow(self):
        """Failed flow returns correlation."""
        flow_id = "flow-failed"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id,
                properties={"error": "Execution failed"}
            )
        )
        
        correlation = self.correlator.correlate_flow(flow_id)
        self.assertIsNotNone(correlation)
        self.assertEqual(correlation.flow_id, flow_id)
    
    def test_correlate_multiple_failures(self):
        """Multiple failure stages in correlation."""
        flow_id = "multi-failure"
        
        # Handshake failure
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="h1",
                event_type=TelemetryEventType.HANDSHAKE_FAILURE.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id,
                properties={"error": "Handshake failed"}
            )
        )
        
        # Envelope failure (cascade)
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id,
                properties={"error": "Execution failed"}
            )
        )
        
        correlation = self.correlator.correlate_flow(flow_id)
        self.assertIsNotNone(correlation)
        # Should have multiple stages
        self.assertGreater(len(correlation.failures_by_stage), 0)
    
    def test_correlate_all_flows(self):
        """Correlate all flows with failures."""
        # Flow 1 - failed
        flow1 = "flow-1"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="f1e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow1
            )
        )
        
        # Flow 2 - completed
        flow2 = "flow-2"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="f2e1",
                event_type=TelemetryEventType.FLOW_CREATED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow2
            )
        )
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="f2e2",
                event_type=TelemetryEventType.FLOW_COMPLETED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow2
            )
        )
        
        correlations = self.correlator.correlate_all_flows()
        self.assertEqual(len(correlations), 1)
        self.assertEqual(correlations[0].flow_id, flow1)


# ============================================================================
# DIAGNOSTIC SUMMARY TESTS
# ============================================================================


class TestDiagnosticSummaryModel(unittest.TestCase):
    """Test diagnostic summary data models."""

    def test_summary_creation(self):
        """DiagnosticSummary created with flow ID."""
        summary = DiagnosticSummary(flow_id="flow-123")
        
        self.assertEqual(summary.flow_id, "flow-123")
        self.assertEqual(summary.status, "unknown")

    def test_summary_serialization(self):
        """DiagnosticSummary serializes to dict."""
        summary = DiagnosticSummary(
            flow_id="flow-456",
            status="needs_review",
            root_cause_summary=["Trust gate failed"],
            recovery_hints=["Review trust configuration"]
        )
        
        data = summary.to_dict()
        
        self.assertEqual(data["flow_id"], "flow-456")
        self.assertEqual(data["status"], "needs_review")
        self.assertEqual(len(data["root_cause_summary"]), 1)


class TestDiagnosticSummaryBuilderBehavior(unittest.TestCase):
    """Test diagnostic summary builder behavior."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.correlator = CrossStageCorrelator(self.emitter)
        self.summary_builder = DiagnosticSummaryBuilder()
    
    def test_build_summary_single_failure(self):
        """Build summary for single failure."""
        flow_id = "flow-1"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        correlation = self.correlator.correlate_flow(flow_id)
        self.assertIsNotNone(correlation)
        
        summary = self.summary_builder.build_summary(correlation)
        
        self.assertEqual(summary.flow_id, flow_id)
        self.assertEqual(summary.status, "needs_review")
    
    def test_build_summary_multiple_flows(self):
        """Build summaries for multiple flows."""
        # Flow 1 - failed
        flow1 = "flow-1"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="f1e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow1
            )
        )
        
        # Flow 2 - rejected
        flow2 = "flow-2"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="f2e1",
                event_type=TelemetryEventType.FLOW_REJECTED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow2
            )
        )
        
        correlations = self.correlator.correlate_all_flows()
        summaries = self.summary_builder.build_summary_list(correlations)
        
        self.assertEqual(len(summaries), 2)


# ============================================================================
# DIAGNOSTIC HOOKS TESTS
# ============================================================================


class TestDiagnosticHooksModel(unittest.TestCase):
    """Test diagnostic hooks data models."""

    def test_hooks_creation(self):
        """DiagnosticHooks created with emitter."""
        emitter = TelemetryEventEmitter()
        hooks = DiagnosticHooks(emitter)
        
        self.assertEqual(hooks._emitter, emitter)
        self.assertIsNotNone(hooks._classifier)
        self.assertIsNotNone(hooks._correlator)
        self.assertIsNotNone(hooks._summary_builder)

    def test_create_diagnostic_hooks_factory(self):
        """Factory function creates diagnostic hooks."""
        emitter = TelemetryEventEmitter()
        hooks = create_diagnostic_hooks(emitter)
        
        self.assertIsInstance(hooks, DiagnosticHooks)
        self.assertEqual(hooks._emitter, emitter)


class TestDiagnosticHooksBehavior(unittest.TestCase):
    """Test diagnostic hooks behavior."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.hooks = DiagnosticHooks(self.emitter)
    
    def test_get_failure_summary_completed(self):
        """Get summary for completed flow returns None."""
        flow_id = "flow-completed"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_CREATED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e2",
                event_type=TelemetryEventType.FLOW_COMPLETED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        summary = self.hooks.get_failure_summary(flow_id)
        self.assertIsNone(summary)
    
    def test_get_failure_summary_failed(self):
        """Get summary for failed flow."""
        flow_id = "flow-failed"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id,
                properties={"error": "Execution failed"}
            )
        )
        
        summary = self.hooks.get_failure_summary(flow_id)
        self.assertIsNotNone(summary)
        self.assertEqual(summary["flow_id"], flow_id)
    
    def test_get_detailed_diagnosis(self):
        """Get detailed diagnosis for flow."""
        flow_id = "flow-detailed"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.HANDSHAKE_FAILURE.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        diagnosis = self.hooks.get_detailed_diagnosis(flow_id)
        self.assertIsNotNone(diagnosis)
        self.assertEqual(diagnosis["flow_id"], flow_id)
        self.assertIn("failures_by_stage", diagnosis)
    
    def test_classify_all_failures(self):
        """Classify all failures."""
        # Flow 1 - failed
        flow1 = "flow-1"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="f1e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow1
            )
        )
        
        classifications = self.hooks.classify_all_failures()
        self.assertEqual(len(classifications), 1)
    
    def test_get_diagnostic_status(self):
        """Get diagnostic status."""
        # Flow 1 - failed
        flow1 = "flow-1"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="f1e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow1
            )
        )
        
        # Flow 2 - completed
        flow2 = "flow-2"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="f2e1",
                event_type=TelemetryEventType.FLOW_CREATED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow2
            )
        )
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="f2e2",
                event_type=TelemetryEventType.FLOW_COMPLETED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow2
            )
        )
        
        status = self.hooks.get_diagnostic_status()
        
        self.assertIn("total_flows_analyzed", status)
        self.assertIn("flows_with_failures", status)
        self.assertIn("failures_by_type", status)
        self.assertIn("failures_by_stage", status)
    
    def test_get_operator_readable_summary(self):
        """Get human-readable operator summary."""
        flow_id = "flow-readable"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id,
                properties={"error": "Execution failed"}
            )
        )
        
        summary = self.hooks.get_operator_readable_summary()
        self.assertIn("DISTRIBUTED DIAGNOSTIC SUMMARY", summary)
        self.assertIn("Flows with Failures", summary)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestDiagnosticIntegration(unittest.TestCase):
    """Test diagnostic hooks integration with v68 telemetry."""

    def test_hooks_work_with_emitter(self):
        """DiagnosticHooks works with TelemetryEventEmitter."""
        emitter = TelemetryEventEmitter()
        hooks = DiagnosticHooks(emitter)
        
        # Should not raise
        status = hooks.get_diagnostic_status()
        self.assertIn("total_flows_analyzed", status)
    
    def test_hooks_emits_no_events(self):
        """DiagnosticHooks is read-only, no events emitted."""
        emitter = TelemetryEventEmitter()
        hooks = DiagnosticHooks(emitter)
        
        initial_count = len(emitter.get_all_events())
        hooks.get_diagnostic_status()
        final_count = len(emitter.get_all_events())
        
        # Should be read-only, no new events
        self.assertEqual(initial_count, final_count)


# ============================================================================
# BACKWARD COMPATIBILITY TESTS
# ============================================================================


class TestDiagnosticBackwardCompatibility(unittest.TestCase):
    """Test diagnostic hooks backward compatibility."""

    def test_hooks_does_not_break_v68_emitter(self):
        """DiagnosticHooks doesn't break v68 telemetry emitter."""
        emitter = TelemetryEventEmitter()
        
        # v68 emitter operations should still work
        emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_CREATED.value,
                timestamp=emitter._now(),
                flow_id="test-flow"
            )
        )
        
        events = emitter.get_all_events()
        self.assertEqual(len(events), 1)
        
        # Diagnostic hooks should not interfere
        hooks = DiagnosticHooks(emitter)
        status = hooks.get_diagnostic_status()
        self.assertIn("total_flows_analyzed", status)

    def test_hooks_does_not_break_v69_export(self):
        """DiagnosticHooks doesn't break v69 telemetry export."""
        emitter = TelemetryEventEmitter()
        
        # Add some v68 events
        emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_CREATED.value,
                timestamp=emitter._now(),
                flow_id="test-flow"
            )
        )
        emitter.emit_event(
            TelemetryEvent(
                event_id="e2",
                event_type=TelemetryEventType.FLOW_COMPLETED.value,
                timestamp=emitter._now(),
                flow_id="test-flow"
            )
        )
        
        # v69 export hooks should still work
        from weslr.telemetry_export import TelemetrySnapshotExporter
        exporter = TelemetrySnapshotExporter(emitter)
        
        # Should not raise
        events = exporter.export_all_events()
        self.assertEqual(len(events), 2)


if __name__ == "__main__":
    unittest.main()
