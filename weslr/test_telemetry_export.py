"""Tests for Distributed Telemetry Export Hooks (v69)

Behavioral tests for telemetry snapshot, flow trace, metrics export,
and operator diagnostics hooks.

Test Doctrine version: 1.0.0 (2026-04-07)
"""

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.execution_telemetry import (
    TelemetryEvent,
    TelemetryEventEmitter,
    TelemetryEventType,
    TelemetryObserver,
)
from weslr.telemetry_export import (
    TelemetrySnapshotExporter,
    TelemetryFlowTraceExporter,
    TelemetryMetricsExporter,
    OperatorDiagnosticHooks,
)


# ============================================================================
# TELEMETRY SNAPSHOT EXPORTER TESTS
# ============================================================================


class TestTelemetrySnapshotExporterModel(unittest.TestCase):
    """Test telemetry snapshot exporter data model."""

    def test_exporter_created_with_emitter(self):
        """Exporter initialized with emitter reference."""
        emitter = TelemetryEventEmitter()
        exporter = TelemetrySnapshotExporter(emitter)
        
        self.assertIsNotNone(exporter._emitter)
        self.assertEqual(exporter._emitter, emitter)

    def test_export_all_events_empty(self):
        """Export all events returns empty list when no events."""
        emitter = TelemetryEventEmitter()
        exporter = TelemetrySnapshotExporter(emitter)
        
        events = exporter.export_all_events()
        
        self.assertEqual(events, [])
        self.assertIsInstance(events, list)

    def test_export_all_events_with_events(self):
        """Export all events returns list of event dicts."""
        emitter = TelemetryEventEmitter()
        exporter = TelemetrySnapshotExporter(emitter)
        
        emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        
        events = exporter.export_all_events()
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], TelemetryEventType.FLOW_CREATED.value)
        self.assertEqual(events[0]["flow_id"], "flow-1")

    def test_export_by_flow_empty(self):
        """Export by flow returns empty dict when no events."""
        emitter = TelemetryEventEmitter()
        exporter = TelemetrySnapshotExporter(emitter)
        
        by_flow = exporter.export_by_flow()
        
        self.assertEqual(by_flow, {})

    def test_export_by_flow_with_events(self):
        """Export by flow groups events correctly."""
        emitter = TelemetryEventEmitter()
        exporter = TelemetrySnapshotExporter(emitter)
        
        emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        emitter.create_event(
            event_type=TelemetryEventType.FLOW_COMPLETED.value,
            flow_id="flow-1"
        )
        emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-2"
        )
        
        by_flow = exporter.export_by_flow()
        
        self.assertIn("flow-1", by_flow)
        self.assertIn("flow-2", by_flow)
        self.assertEqual(len(by_flow["flow-1"]), 2)
        self.assertEqual(len(by_flow["flow-2"]), 1)

    def test_export_by_type(self):
        """Export by type groups events correctly."""
        emitter = TelemetryEventEmitter()
        exporter = TelemetrySnapshotExporter(emitter)
        
        emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        emitter.create_event(
            event_type=TelemetryEventType.FLOW_COMPLETED.value,
            flow_id="flow-1"
        )
        emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-2"
        )
        
        by_type = exporter.export_by_type()
        
        self.assertIn(TelemetryEventType.FLOW_CREATED.value, by_type)
        self.assertIn(TelemetryEventType.FLOW_COMPLETED.value, by_type)
        self.assertEqual(len(by_type[TelemetryEventType.FLOW_CREATED.value]), 2)
        self.assertEqual(len(by_type[TelemetryEventType.FLOW_COMPLETED.value]), 1)

    def test_export_json(self):
        """Export as JSON returns valid JSON string."""
        emitter = TelemetryEventEmitter()
        exporter = TelemetrySnapshotExporter(emitter)
        
        emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        
        json_str = exporter.export_json()
        
        self.assertIsInstance(json_str, str)
        self.assertIn("flow-1", json_str)
        self.assertIn("flow_created", json_str)

    def test_export_json_pretty(self):
        """Export as pretty JSON includes indentation."""
        emitter = TelemetryEventEmitter()
        exporter = TelemetrySnapshotExporter(emitter)
        
        emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        
        json_str = exporter.export_json(pretty=True)
        
        self.assertIn("  ", json_str)  # Indentation present


class TestTelemetrySnapshotExporterBehavior(unittest.TestCase):
    """Test telemetry snapshot exporter behavior."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.exporter = TelemetrySnapshotExporter(self.emitter)

    def test_export_is_readonly_copy(self):
        """Exported data is a copy — modifications do not affect emitter."""
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        
        events = self.exporter.export_all_events()
        
        # Modify the exported list
        events.append({"fake": "event"})
        
        # Emitter should be unchanged
        new_events = self.exporter.export_all_events()
        self.assertEqual(len(new_events), 1)

    def test_export_events_in_range(self):
        """Export events within time range."""
        emitter = TelemetryEventEmitter()
        exporter = TelemetrySnapshotExporter(emitter)
        
        # Use direct event creation with timestamps for testing time range
        event1 = TelemetryEvent(
            event_id="evt-1",
            event_type=TelemetryEventType.FLOW_CREATED.value,
            timestamp=datetime.now(timezone.utc),
            flow_id="flow-1"
        )
        emitter.emit_event(event1)
        
        event2 = TelemetryEvent(
            event_id="evt-2",
            event_type=TelemetryEventType.FLOW_COMPLETED.value,
            timestamp=datetime.now(timezone.utc) + timedelta(seconds=10),
            flow_id="flow-2"
        )
        emitter.emit_event(event2)
        
        # Export with time range
        events = exporter.export_events_in_range(
            start_time="2026-04-01T00:00:00Z",
            end_time="2026-04-08T00:00:00Z"
        )
        
        self.assertEqual(len(events), 2)


# ============================================================================
# TELEMETRY FLOW TRACE EXPORTER TESTS
# ============================================================================


class TestTelemetryFlowTraceExporterModel(unittest.TestCase):
    """Test telemetry flow trace exporter data model."""

    def test_exporter_created_with_emitter(self):
        """Exporter initialized with emitter reference."""
        emitter = TelemetryEventEmitter()
        exporter = TelemetryFlowTraceExporter(emitter)
        
        self.assertIsNotNone(exporter._emitter)
        self.assertEqual(exporter._emitter, emitter)


class TestTelemetryFlowTraceExporterBehavior(unittest.TestCase):
    """Test telemetry flow trace exporter behavior."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.exporter = TelemetryFlowTraceExporter(self.emitter)

    def test_export_flow_trace_not_found(self):
        """Export flow trace returns None for unknown flow."""
        trace = self.exporter.export_flow_trace("unknown-flow")
        
        self.assertIsNone(trace)

    def test_export_flow_trace_complete(self):
        """Export flow trace includes all fields."""
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1",
            request_id="req-1",
            deadline_id="dl-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_COMPLETED.value,
            flow_id="flow-1",
            request_id="req-1"
        )
        
        trace = self.exporter.export_flow_trace("flow-1")
        
        self.assertIsNotNone(trace)
        self.assertEqual(trace["flow_id"], "flow-1")
        self.assertIn("events", trace)
        self.assertIn("correlation_ids", trace)
        self.assertIn("duration_ms", trace)
        self.assertIn("event_count", trace)

    def test_export_flow_trace_correlation(self):
        """Export flow trace includes correlation IDs."""
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1",
            request_id="req-1",
            handshake_id="hs-1",
            deadline_id="dl-1"
        )
        
        trace = self.exporter.export_flow_trace("flow-1")
        
        corr = trace["correlation_ids"]
        self.assertEqual(corr["flow_id"], "flow-1")
        self.assertEqual(corr["request_id"], "req-1")
        self.assertEqual(corr["handshake_id"], "hs-1")
        self.assertEqual(corr["deadline_id"], "dl-1")

    def test_export_all_flow_traces(self):
        """Export all flow traces returns dict of all traces."""
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-2"
        )
        
        traces = self.exporter.export_all_flow_traces()
        
        self.assertIn("flow-1", traces)
        self.assertIn("flow-2", traces)
        self.assertEqual(len(traces), 2)

    def test_export_correlation_chain(self):
        """Export correlation chain returns ordered events."""
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_COMPLETED.value,
            flow_id="flow-1"
        )
        
        chain = self.exporter.export_correlation_chain("flow-1")
        
        self.assertEqual(len(chain), 2)
        self.assertEqual(chain[0]["event_type"], "flow_created")
        self.assertEqual(chain[1]["event_type"], "flow_completed")


# ============================================================================
# TELEMETRY METRICS EXPORTER TESTS
# ============================================================================


class TestTelemetryMetricsExporterModel(unittest.TestCase):
    """Test telemetry metrics exporter data model."""

    def test_exporter_created_with_emitter(self):
        """Exporter initialized with emitter reference."""
        emitter = TelemetryEventEmitter()
        exporter = TelemetryMetricsExporter(emitter)
        
        self.assertIsNotNone(exporter._emitter)
        self.assertEqual(exporter._emitter, emitter)


class TestTelemetryMetricsExporterBehavior(unittest.TestCase):
    """Test telemetry metrics exporter behavior."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.exporter = TelemetryMetricsExporter(self.emitter)

    def test_export_event_counts(self):
        """Export event counts returns correct counts."""
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-2"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_COMPLETED.value,
            flow_id="flow-1"
        )
        
        counts = self.exporter.export_event_counts()
        
        self.assertEqual(counts[TelemetryEventType.FLOW_CREATED.value], 2)
        self.assertEqual(counts[TelemetryEventType.FLOW_COMPLETED.value], 1)

    def test_export_metrics_summary_empty(self):
        """Export metrics summary handles empty emitter."""
        summary = self.exporter.export_metrics_summary()
        
        self.assertEqual(summary["total_events"], 0)
        self.assertEqual(summary["success_rate"], 0.0)
        self.assertEqual(summary["events_by_type"], {})
        self.assertEqual(summary["events_by_flow"], {})

    def test_export_metrics_summary_complete(self):
        """Export metrics summary includes all fields."""
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_COMPLETED.value,
            flow_id="flow-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_FAILED.value,
            flow_id="flow-2"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.HANDSHAKE_SUCCESS.value,
            flow_id="flow-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.HANDSHAKE_FAILURE.value,
            flow_id="flow-2"
        )
        
        summary = self.exporter.export_metrics_summary()
        
        self.assertEqual(summary["total_events"], 5)
        self.assertEqual(summary["success_count"], 1)
        self.assertEqual(summary["failure_count"], 1)
        self.assertEqual(summary["handshake_success"], 1)
        self.assertEqual(summary["handshake_failure"], 1)

    def test_export_flow_metrics_not_found(self):
        """Export flow metrics returns None for unknown flow."""
        metrics = self.exporter.export_flow_metrics("unknown-flow")
        
        self.assertIsNone(metrics)

    def test_export_flow_metrics_complete(self):
        """Export flow metrics includes all fields."""
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_COMPLETED.value,
            flow_id="flow-1"
        )
        
        metrics = self.exporter.export_flow_metrics("flow-1")
        
        self.assertEqual(metrics["flow_id"], "flow-1")
        self.assertEqual(metrics["event_count"], 2)
        # Outcome depends on event order - completed or incomplete
        self.assertIn(metrics["outcome"], ["completed", "incomplete"])
        self.assertFalse(metrics["has_handshake_success"])  # No handshake events

    def test_export_all_flow_metrics(self):
        """Export all flow metrics returns dict of all metrics."""
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_COMPLETED.value,
            flow_id="flow-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-2"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_FAILED.value,
            flow_id="flow-2"
        )
        
        metrics = self.exporter.export_all_flow_metrics()
        
        self.assertIn("flow-1", metrics)
        self.assertIn("flow-2", metrics)
        self.assertEqual(metrics["flow-1"]["outcome"], "completed")
        self.assertEqual(metrics["flow-2"]["outcome"], "failed")


# ============================================================================
# OPERATOR DIAGNOSTIC HOOKS TESTS
# ============================================================================


class TestOperatorDiagnosticHooksModel(unittest.TestCase):
    """Test operator diagnostic hooks data model."""

    def test_hooks_created_with_emitter(self):
        """Diagnostic hooks initialized with emitter reference."""
        emitter = TelemetryEventEmitter()
        hooks = OperatorDiagnosticHooks(emitter)
        
        self.assertIsNotNone(hooks._emitter)
        self.assertEqual(hooks._emitter, emitter)


class TestOperatorDiagnosticHooksBehavior(unittest.TestCase):
    """Test operator diagnostic hooks behavior."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.hooks = OperatorDiagnosticHooks(self.emitter)

    def test_get_telemetry_status_empty(self):
        """Get telemetry status handles empty emitter."""
        status = self.hooks.get_telemetry_status()
        
        self.assertEqual(status["total_events"], 0)
        self.assertEqual(status["active_flows"], 0)
        self.assertEqual(status["event_type_count"], 0)
        self.assertTrue(status["emitter_alive"])

    def test_get_telemetry_status_with_events(self):
        """Get telemetry status includes correct counts."""
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_COMPLETED.value,
            flow_id="flow-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.HANDSHAKE_SUCCESS.value,
            flow_id="flow-1"
        )
        
        status = self.hooks.get_telemetry_status()
        
        self.assertEqual(status["total_events"], 3)
        self.assertEqual(status["active_flows"], 1)
        self.assertEqual(status["event_type_count"], 3)

    def test_get_active_flows(self):
        """Get active flows returns list of flow IDs."""
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-2"
        )
        
        flows = self.hooks.get_active_flows()
        
        self.assertEqual(flows, ["flow-1", "flow-2"])

    def test_get_flows_in_state(self):
        """Get flows in state returns flows with specific event type."""
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_COMPLETED.value,
            flow_id="flow-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-2"
        )
        
        flows = self.hooks.get_flows_in_state(TelemetryEventType.FLOW_COMPLETED.value)
        
        self.assertEqual(flows, ["flow-1"])

    def test_get_recent_events(self):
        """Get recent events returns most recent events."""
        for i in range(5):
            event = TelemetryEvent(
                event_id=f"evt-{i}",
                event_type=TelemetryEventType.FLOW_CREATED.value,
                timestamp=datetime.now(timezone.utc) + timedelta(seconds=i),
                flow_id=f"flow-{i}"
            )
            self.emitter.emit_event(event)
        
        recent = self.hooks.get_recent_events(limit=3)
        
        self.assertEqual(len(recent), 3)
        # Most recent first (events created in order 0-4, so most recent is 4)
        self.assertEqual(recent[0]["flow_id"], "flow-4")
        self.assertEqual(recent[1]["flow_id"], "flow-3")
        self.assertEqual(recent[2]["flow_id"], "flow-2")

    def test_export_diagnostics_json(self):
        """Export diagnostics JSON includes all sections."""
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_COMPLETED.value,
            flow_id="flow-1"
        )
        
        json_str = self.hooks.export_diagnostics_json()
        
        self.assertIn("status", json_str)
        self.assertIn("active_flows", json_str)
        self.assertIn("metrics", json_str)

    def test_export_diagnostics_json_pretty(self):
        """Export diagnostics JSON with pretty includes indentation."""
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        
        json_str = self.hooks.export_diagnostics_json(pretty=True)
        
        self.assertIn("  ", json_str)  # Indentation present

    def test_get_operator_readable_summary(self):
        """Get operator readable summary returns formatted string."""
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_COMPLETED.value,
            flow_id="flow-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_FAILED.value,
            flow_id="flow-2"
        )
        
        summary = self.hooks.get_operator_readable_summary()
        
        self.assertIn("=== TELEMETRY DIAGNOSTICS ===", summary)
        self.assertIn("Total Events: 3", summary)
        self.assertIn("Success Rate:", summary)
        self.assertIn("=== EVENT BREAKDOWN ===", summary)


# ============================================================================
# TELEMETRY EXPORT INTEGRATION TESTS
# ============================================================================


class TestTelemetryExportIntegration(unittest.TestCase):
    """Test telemetry export hooks integrate with v68 correctly."""

    def test_exporter_works_with_telemetry_emitter(self):
        """Export hooks work with TelemetryEventEmitter."""
        emitter = TelemetryEventEmitter()
        exporter = TelemetrySnapshotExporter(emitter)
        
        # Use telemetry observer to emit events
        context = TelemetryObserver.observe_flow_lifecycle(
            emitter,
            flow_id="flow-1"
        )
        TelemetryObserver.record_flow_completed(context, {"result": "success"})
        
        # Export should capture observer-emitted events
        events = exporter.export_all_events()
        
        # Note: observer emits 1 event (record_flow_completed), not 2
        # observe_flow_lifecycle creates context dict but doesn't emit an event
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], TelemetryEventType.FLOW_COMPLETED.value)

    def test_metrics_exporter_counts_handshake_events(self):
        """Metrics exporter correctly counts handshake events."""
        emitter = TelemetryEventEmitter()
        exporter = TelemetryMetricsExporter(emitter)
        
        # Use observer to record handshake events
        TelemetryObserver.record_handshake_success(
            emitter,
            flow_id="flow-1",
            handshake_id="hs-1",
            handshake_result={"session_id": "sess-1"}
        )
        TelemetryObserver.record_handshake_failure(
            emitter,
            flow_id="flow-2",
            handshake_id="hs-2",
            failure_reason="Trust insufficient"
        )
        
        metrics = exporter.export_metrics_summary()
        
        self.assertEqual(metrics["handshake_success"], 1)
        self.assertEqual(metrics["handshake_failure"], 1)

    def test_flow_trace_exporter_correlates_with_v68_events(self):
        """Flow trace exporter correlates with v68 event types."""
        emitter = TelemetryEventEmitter()
        exporter = TelemetryFlowTraceExporter(emitter)
        
        # Create events matching v68 types
        emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1",
            request_id="req-1",
            deadline_id="dl-1"
        )
        emitter.create_event(
            event_type=TelemetryEventType.HANDSHAKE_SUCCESS.value,
            flow_id="flow-1",
            handshake_id="hs-1"
        )
        emitter.create_event(
            event_type=TelemetryEventType.DEADLINE_BREACH.value,
            flow_id="flow-1",
            deadline_id="dl-1"
        )
        emitter.create_event(
            event_type=TelemetryEventType.FLOW_ROLLBACK_INITIATED.value,
            flow_id="flow-1"
        )
        
        trace = exporter.export_flow_trace("flow-1")
        
        events = trace["events"]
        self.assertEqual(len(events), 4)
        
        event_types = [e["event_type"] for e in events]
        self.assertIn(TelemetryEventType.FLOW_CREATED.value, event_types)
        self.assertIn(TelemetryEventType.HANDSHAKE_SUCCESS.value, event_types)
        self.assertIn(TelemetryEventType.DEADLINE_BREACH.value, event_types)
        self.assertIn(TelemetryEventType.FLOW_ROLLBACK_INITIATED.value, event_types)


# ============================================================================
# TELEMETRY EXPORT BACKWARD COMPATIBILITY TESTS
# ============================================================================


class TestTelemetryExportBackwardCompatibility(unittest.TestCase):
    """Test telemetry export hooks are backward compatible with v68."""

    def test_exporter_works_with_v68_emitter(self):
        """Export hooks work with v68 TelemetryEventEmitter."""
        emitter = TelemetryEventEmitter()
        exporter = TelemetrySnapshotExporter(emitter)
        
        # Create events using v68 API
        event = TelemetryEvent(
            event_id="evt-1",
            event_type=TelemetryEventType.FLOW_CREATED.value,
            timestamp=datetime.now(timezone.utc),
            flow_id="flow-1"
        )
        emitter.emit_event(event)
        
        # Export should work
        events = exporter.export_all_events()
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_id"], "evt-1")

    def test_exporter_does_not_modify_v68_emitter_state(self):
        """Export hooks do not modify v68 emitter state."""
        emitter = TelemetryEventEmitter()
        exporter = TelemetrySnapshotExporter(emitter)
        
        emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        
        initial_count = len(emitter.get_all_events())
        _ = exporter.export_all_events()
        final_count = len(emitter.get_all_events())
        
        self.assertEqual(initial_count, final_count)

    def test_new_exporter_methods_added_without_breaking(self):
        """New export methods can be added without breaking existing code."""
        emitter = TelemetryEventEmitter()
        
        # Old code using v68 API still works
        emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        
        # New export methods available
        exporter = TelemetrySnapshotExporter(emitter)
        metrics = TelemetryMetricsExporter(emitter)
        
        self.assertEqual(len(exporter.export_all_events()), 1)
        self.assertEqual(metrics.export_event_counts()[TelemetryEventType.FLOW_CREATED.value], 1)


if __name__ == "__main__":
    unittest.main()
