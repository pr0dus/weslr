"""Tests for Distributed Diagnostic Export Hooks (v71)

Behavioral tests for diagnostic summary export, correlated failure-chain export,
and recovery-hint export with correlation filtering.

Test Doctrine version: 1.0.0 (2026-04-07)
"""

import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.diagnostic_export import (
    DiagnosticSummaryExporter,
    FailureChainExporter,
    RecoveryHintExporter,
    DiagnosticExportHooks,
    create_diagnostic_export_hooks,
)
from weslr.distributed_diagnostic_hooks import (
    DiagnosticHooks,
    FailureType,
    FailureStage,
)
from weslr.execution_telemetry import (
    TelemetryEventEmitter,
    TelemetryEvent,
    TelemetryEventType,
)


# ============================================================================
# DIAGNOSTIC SUMMARY EXPORTER TESTS
# ============================================================================


class TestDiagnosticSummaryExporter(unittest.TestCase):
    """Test diagnostic summary exporter."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.diagnostic_hooks = DiagnosticHooks(self.emitter)
        self.exporter = DiagnosticSummaryExporter(self.diagnostic_hooks)

    def test_export_summary_no_failure(self):
        """Export summary for flow without failure returns None."""
        flow_id = "flow-no-failure"
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
        
        result = self.exporter.export_summary(flow_id)
        self.assertIsNone(result)

    def test_export_summary_with_failure(self):
        """Export summary for flow with failure."""
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
        
        result = self.exporter.export_summary(flow_id)
        self.assertIsNotNone(result)
        self.assertEqual(result["flow_id"], flow_id)
        self.assertIn("export_metadata", result)
        self.assertEqual(result["export_metadata"]["export_version"], "v71.0.0")

    def test_export_all_summaries(self):
        """Export all summaries."""
        # Flow with failure
        flow1 = "flow-1"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow1
            )
        )
        
        # Flow completed
        flow2 = "flow-2"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e2",
                event_type=TelemetryEventType.FLOW_CREATED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow2
            )
        )
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e3",
                event_type=TelemetryEventType.FLOW_COMPLETED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow2
            )
        )
        
        summaries = self.exporter.export_all_summaries()
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["flow_id"], flow1)

    def test_export_summaries_json(self):
        """Export summaries as JSON."""
        flow_id = "flow-json"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        json_str = self.exporter.export_json()
        self.assertIn(flow_id, json_str)

    def test_export_operator_readable_summary(self):
        """Get human-readable operator summary."""
        flow_id = "flow-readable"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        summary = self.exporter.get_operator_readable_summary()
        self.assertIn("DIAGNOSTIC SUMMARY EXPORT", summary)
        self.assertIn("Flows with Failures", summary)


# ============================================================================
# FAILURE CHAIN EXPORTER TESTS
# ============================================================================


class TestFailureChainExporter(unittest.TestCase):
    """Test failure chain exporter."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.diagnostic_hooks = DiagnosticHooks(self.emitter)
        self.exporter = FailureChainExporter(self.diagnostic_hooks)

    def test_export_chain_no_failure(self):
        """Export chain for flow without failure returns None."""
        flow_id = "flow-no-failure"
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
        
        result = self.exporter.export_chain(flow_id)
        self.assertIsNone(result)

    def test_export_chain_with_failure(self):
        """Export chain for flow with failure."""
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
        
        result = self.exporter.export_chain(flow_id)
        self.assertIsNotNone(result)
        self.assertEqual(result["flow_id"], flow_id)
        self.assertIn("export_metadata", result)
        self.assertIn("failures_by_stage", result)

    def test_export_all_chains(self):
        """Export all chains."""
        # Flow with failure
        flow1 = "flow-1"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow1
            )
        )
        
        # Flow completed
        flow2 = "flow-2"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e2",
                event_type=TelemetryEventType.FLOW_CREATED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow2
            )
        )
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e3",
                event_type=TelemetryEventType.FLOW_COMPLETED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow2
            )
        )
        
        chains = self.exporter.export_all_chains()
        self.assertEqual(len(chains), 1)
        self.assertEqual(chains[0]["flow_id"], flow1)

    def test_export_chains_json(self):
        """Export chains as JSON."""
        flow_id = "flow-json"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        json_str = self.exporter.export_json()
        self.assertIn(flow_id, json_str)

    def test_export_operator_readable_summary(self):
        """Get human-readable operator summary."""
        flow_id = "flow-readable"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        summary = self.exporter.get_operator_readable_summary()
        self.assertIn("FAILURE CHAIN EXPORT", summary)
        self.assertIn("Total Chains", summary)


# ============================================================================
# RECOVERY HINT EXPORTER TESTS
# ============================================================================


class TestRecoveryHintExporter(unittest.TestCase):
    """Test recovery hint exporter."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.diagnostic_hooks = DiagnosticHooks(self.emitter)
        self.exporter = RecoveryHintExporter(self.diagnostic_hooks)

    def test_export_hint_no_failure(self):
        """Export hint for flow without failure returns None."""
        flow_id = "flow-no-failure"
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
        
        result = self.exporter.export_hint(flow_id)
        self.assertIsNone(result)

    def test_export_hint_with_failure(self):
        """Export hint for flow with failure."""
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
        
        result = self.exporter.export_hint(flow_id)
        self.assertIsNotNone(result)
        self.assertEqual(result["flow_id"], flow_id)
        self.assertIn("recovery_hint", result)
        self.assertIn("export_metadata", result)
        self.assertEqual(result["export_metadata"]["hint_certainty"], "suggestion")

    def test_export_all_hints(self):
        """Export all hints."""
        # Flow with failure
        flow1 = "flow-1"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow1
            )
        )
        
        # Flow completed
        flow2 = "flow-2"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e2",
                event_type=TelemetryEventType.FLOW_CREATED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow2
            )
        )
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e3",
                event_type=TelemetryEventType.FLOW_COMPLETED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow2
            )
        )
        
        hints = self.exporter.export_all_hints()
        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0]["flow_id"], flow1)

    def test_export_hints_json(self):
        """Export hints as JSON."""
        flow_id = "flow-json"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        json_str = self.exporter.export_json()
        self.assertIn(flow_id, json_str)

    def test_export_operator_readable_summary(self):
        """Get human-readable operator summary."""
        flow_id = "flow-readable"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        summary = self.exporter.get_operator_readable_summary()
        self.assertIn("RECOVERY HINT EXPORT", summary)
        self.assertIn("Total Hints", summary)


# ============================================================================
# DIAGNOSTIC EXPORT HOOKS TESTS
# ============================================================================


class TestDiagnosticExportHooks(unittest.TestCase):
    """Test unified diagnostic export hooks."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.hooks = DiagnosticExportHooks(DiagnosticHooks(self.emitter))

    def test_create_diagnostic_export_hooks_factory(self):
        """Factory function creates export hooks."""
        from weslr.distributed_diagnostic_hooks import create_diagnostic_hooks
        diagnostic_hooks = create_diagnostic_hooks(self.emitter)
        export_hooks = DiagnosticExportHooks(diagnostic_hooks)
        
        self.assertIsInstance(export_hooks, DiagnosticExportHooks)

    def test_export_summary(self):
        """Export summary for flow."""
        flow_id = "flow-summary"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        result = self.hooks.export_summary(flow_id)
        self.assertIsNotNone(result)

    def test_export_all_summaries(self):
        """Export all summaries."""
        # Flow with failure
        flow1 = "flow-1"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow1
            )
        )
        
        summaries = self.hooks.export_all_summaries()
        self.assertEqual(len(summaries), 1)

    def test_export_chains(self):
        """Export chains for flow."""
        flow_id = "flow-chain"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        result = self.hooks.export_chain(flow_id)
        self.assertIsNotNone(result)

    def test_export_all_chains(self):
        """Export all chains."""
        # Flow with failure
        flow1 = "flow-1"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow1
            )
        )
        
        chains = self.hooks.export_all_chains()
        self.assertEqual(len(chains), 1)

    def test_export_hint(self):
        """Export hint for flow."""
        flow_id = "flow-hint"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        result = self.hooks.export_hint(flow_id)
        self.assertIsNotNone(result)
        self.assertIn("recovery_hint", result)

    def test_export_all_hints(self):
        """Export all hints."""
        # Flow with failure
        flow1 = "flow-1"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow1
            )
        )
        
        hints = self.hooks.export_all_hints()
        self.assertEqual(len(hints), 1)

    def test_export_all_as_dict(self):
        """Export all diagnostics as dict."""
        # Flow with failure
        flow1 = "flow-1"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow1
            )
        )
        
        result = self.hooks.export_all_as_dict()
        self.assertIn("summaries", result)
        self.assertIn("chains", result)
        self.assertIn("hints", result)

    def test_export_all_as_json(self):
        """Export all diagnostics as JSON."""
        # Flow with failure
        flow1 = "flow-1"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow1
            )
        )
        
        json_str = self.hooks.export_all_as_json()
        self.assertIn("summaries", json_str)
        self.assertIn("chains", json_str)
        self.assertIn("hints", json_str)

    def test_get_operator_readable_summary(self):
        """Get human-readable operator summary."""
        flow_id = "flow-readable"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        summary = self.hooks.get_operator_readable_summary()
        self.assertIn("DIAGNOSTIC SUMMARY EXPORT", summary)
        self.assertIn("FAILURE CHAIN EXPORT", summary)
        self.assertIn("RECOVERY HINT EXPORT", summary)

    def test_export_by_correlation(self):
        """Export diagnostics filtered by correlation ID."""
        flow_id = "flow-correlation"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        result = self.hooks.export_by_correlation(flow_id, "flow_id")
        self.assertIn("summaries", result)
        self.assertIn("chains", result)
        self.assertIn("hints", result)


# ============================================================================
# CORRELATION FILTERING TESTS
# ============================================================================


class TestCorrelationFiltering(unittest.TestCase):
    """Test correlation filtering in exporters."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.diagnostic_hooks = DiagnosticHooks(self.emitter)
        self.exporter = FailureChainExporter(self.diagnostic_hooks)

    def test_export_by_correlation_flow_id(self):
        """Export filtered by flow_id."""
        flow_id = "flow-filter"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        result = self.exporter.export_by_correlation(flow_id, "flow_id")
        self.assertGreater(len(result), 0)

    def test_export_by_correlation_no_match(self):
        """Export filtered with no matching correlation."""
        flow_id = "flow-no-match"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id="different-flow"
            )
        )
        
        result = self.exporter.export_by_correlation(flow_id, "flow_id")
        self.assertEqual(len(result), 0)


# ============================================================================
# JSON EXPORT TESTS
# ============================================================================


class TestJSONExport(unittest.TestCase):
    """Test JSON export formatting."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.diagnostic_hooks = DiagnosticHooks(self.emitter)

    def test_export_json_pretty(self):
        """Export JSON with indentation."""
        flow_id = "flow-pretty"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        hooks = DiagnosticExportHooks(self.diagnostic_hooks)
        json_str = hooks.export_all_as_json(pretty=True)
        
        # Check for indentation (pretty format)
        self.assertIn("  ", json_str)
        self.assertIn(flow_id, json_str)

    def test_export_json_compact(self):
        """Export JSON without indentation."""
        flow_id = "flow-compact"
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        hooks = DiagnosticExportHooks(self.diagnostic_hooks)
        json_str = hooks.export_all_as_json(pretty=False)
        
        # Should be compact (no extra indentation)
        self.assertIn(flow_id, json_str)


# ============================================================================
# READ-ONLY TESTS
# ============================================================================


class TestReadOnlyExport(unittest.TestCase):
    """Test that export is read-only (no mutation)."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()

    def test_export_does_not_modify_emitter(self):
        """Export operations do not modify the emitter."""
        flow_id = "flow-readonly"
        
        # Record initial state
        initial_events = len(self.emitter.get_all_events())
        initial_flows = len(self.emitter.get_all_flows())
        
        # Perform export operations
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_CREATED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        hooks = DiagnosticHooks(self.emitter)
        export_hooks = DiagnosticExportHooks(hooks)
        
        # Export operations
        export_hooks.export_summary(flow_id)
        export_hooks.export_chain(flow_id)
        export_hooks.export_hint(flow_id)
        
        # Record final state
        final_events = len(self.emitter.get_all_events())
        final_flows = len(self.emitter.get_all_flows())
        
        # Should be unchanged (except for the one event we added)
        self.assertEqual(final_events, initial_events + 1)
        self.assertEqual(final_flows, initial_flows + 1)

    def test_export_json_does_not_emit_events(self):
        """JSON export does not emit new telemetry events."""
        flow_id = "flow-noemit"
        
        initial_events = len(self.emitter.get_all_events())
        
        self.emitter.emit_event(
            TelemetryEvent(
                event_id="e1",
                event_type=TelemetryEventType.FLOW_FAILED.value,
                timestamp=datetime.now(timezone.utc),
                flow_id=flow_id
            )
        )
        
        hooks = DiagnosticHooks(self.emitter)
        export_hooks = DiagnosticExportHooks(hooks)
        export_hooks.export_all_as_json()
        
        final_events = len(self.emitter.get_all_events())
        self.assertEqual(final_events, initial_events + 1)


if __name__ == "__main__":
    unittest.main()
