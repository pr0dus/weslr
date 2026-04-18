"""Tests for Distributed Execution Telemetry Layer (v68)

Behavioral tests for telemetry event emission, metrics, and audit export.
"""

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.execution_telemetry import (
    TelemetryEventType,
    TelemetryEvent,
    TelemetryEventEmitter,
    TelemetryObserver,
)


class TestTelemetryEvent(unittest.TestCase):
    """Test telemetry event model."""

    def test_creation_defaults(self):
        """Event created with required fields."""
        event = TelemetryEvent(
            event_id="evt-1",
            event_type=TelemetryEventType.FLOW_CREATED.value,
            timestamp=datetime.now(timezone.utc)
        )
        
        self.assertEqual(event.event_id, "evt-1")
        self.assertEqual(event.event_type, TelemetryEventType.FLOW_CREATED.value)
        self.assertIsNone(event.flow_id)
        self.assertEqual(event.properties, {})

    def test_with_correlation(self):
        """Event with correlation IDs."""
        event = TelemetryEvent(
            event_id="evt-1",
            event_type=TelemetryEventType.FLOW_COMPLETED.value,
            timestamp=datetime.now(timezone.utc),
            flow_id="flow-1",
            request_id="req-1",
            correlation_ids={"handshake_id": "hs-1"}
        )
        
        self.assertEqual(event.flow_id, "flow-1")
        self.assertEqual(event.request_id, "req-1")
        self.assertEqual(event.correlation_ids["handshake_id"], "hs-1")

    def test_with_duration(self):
        """Event with duration in milliseconds."""
        event = TelemetryEvent(
            event_id="evt-1",
            event_type=TelemetryEventType.FLOW_COMPLETED.value,
            timestamp=datetime.now(timezone.utc),
            flow_id="flow-1",
            duration_ms=1234.56
        )
        
        self.assertEqual(event.duration_ms, 1234.56)

    def test_serialization(self):
        """Round-trip serialization works."""
        event = TelemetryEvent(
            event_id="evt-1",
            event_type=TelemetryEventType.FLOW_CREATED.value,
            timestamp=datetime.now(timezone.utc),
            flow_id="flow-1",
            request_id="req-1",
            properties={"key": "value"}
        )
        
        data = event.to_dict()
        restored = TelemetryEvent.from_dict(data)
        
        self.assertEqual(restored.event_id, "evt-1")
        self.assertEqual(restored.flow_id, "flow-1")
        self.assertEqual(restored.properties["key"], "value")

    def test_json_serialization(self):
        """Event serialized to JSON."""
        event = TelemetryEvent(
            event_id="evt-1",
            event_type=TelemetryEventType.FLOW_CREATED.value,
            timestamp=datetime.now(timezone.utc),
            flow_id="flow-1"
        )
        
        json_str = event.to_json()
        restored = TelemetryEvent.from_dict(event.to_dict())
        
        self.assertIsNotNone(json_str)
        self.assertEqual(restored.event_id, "evt-1")


class TestTelemetryEventEmitter(unittest.TestCase):
    """Test telemetry event emitter."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()

    def test_emit_event(self):
        """Event recorded."""
        event = TelemetryEvent(
            event_id="evt-1",
            event_type=TelemetryEventType.FLOW_CREATED.value,
            timestamp=datetime.now(timezone.utc),
            flow_id="flow-1"
        )
        
        self.emitter.emit_event(event)
        
        events = self.emitter.get_all_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, TelemetryEventType.FLOW_CREATED.value)

    def test_create_event(self):
        """Event created and emitted."""
        event = self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        
        self.assertIsNotNone(event.event_id)
        events = self.emitter.get_all_events()
        self.assertEqual(len(events), 1)

    def test_get_events_by_flow(self):
        """Events retrieved by flow ID."""
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
        
        flow1_events = self.emitter.get_events_by_flow("flow-1")
        self.assertEqual(len(flow1_events), 2)
        
        flow2_events = self.emitter.get_events_by_flow("flow-2")
        self.assertEqual(len(flow2_events), 1)

    def test_get_events_by_type(self):
        """Events retrieved by type."""
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
        
        created_events = self.emitter.get_events_by_type(TelemetryEventType.FLOW_CREATED.value)
        self.assertEqual(len(created_events), 2)

    def test_get_metrics(self):
        """Metrics summary retrieved."""
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
        
        metrics = self.emitter.get_metrics()
        
        self.assertEqual(metrics[TelemetryEventType.FLOW_CREATED.value], 2)
        self.assertEqual(metrics[TelemetryEventType.FLOW_COMPLETED.value], 1)

    def test_export_as_json(self):
        """Events exported as JSON."""
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        
        json_str = self.emitter.export_as_json()
        
        self.assertIsNotNone(json_str)
        self.assertIn("flow-1", json_str)

    def test_export_by_flow(self):
        """Events exported grouped by flow."""
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_COMPLETED.value,
            flow_id="flow-1"
        )
        
        by_flow = self.emitter.export_by_flow()
        
        self.assertIn("flow-1", by_flow)
        self.assertEqual(len(by_flow["flow-1"]), 2)

    def test_clear(self):
        """Events cleared."""
        self.emitter.create_event(
            event_type=TelemetryEventType.FLOW_CREATED.value,
            flow_id="flow-1"
        )
        self.emitter.clear()
        
        self.assertEqual(len(self.emitter.get_all_events()), 0)


class TestTelemetryObserver(unittest.TestCase):
    """Test telemetry observer methods."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()

    def test_flow_lifecycle_observation(self):
        """Flow lifecycle events recorded."""
        context = TelemetryObserver.observe_flow_lifecycle(
            self.emitter,
            flow_id="flow-1",
            request_id="req-1"
        )
        
        self.assertIn("emitter", context)
        self.assertIn("correlation_ids", context)
        self.assertIn("start_time", context)
        
        # Record completion
        TelemetryObserver.record_flow_completed(context)
        
        events = self.emitter.get_events_by_type(TelemetryEventType.FLOW_COMPLETED.value)
        self.assertEqual(len(events), 1)

    def test_flow_failure_observation(self):
        """Flow failure events recorded."""
        context = TelemetryObserver.observe_flow_lifecycle(
            self.emitter,
            flow_id="flow-1"
        )
        
        TelemetryObserver.record_flow_failed(context, "Network timeout")
        
        events = self.emitter.get_events_by_type(TelemetryEventType.FLOW_FAILED.value)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].properties["reason"], "Network timeout")

    def test_handshake_success_observation(self):
        """Handshake success events recorded."""
        TelemetryObserver.record_handshake_success(
            self.emitter,
            flow_id="flow-1",
            handshake_id="hs-1",
            handshake_result={"session_id": "sess-1"}
        )
        
        events = self.emitter.get_events_by_type(TelemetryEventType.HANDSHAKE_SUCCESS.value)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].handshake_id, "hs-1")

    def test_handshake_failure_observation(self):
        """Handshake failure events recorded."""
        TelemetryObserver.record_handshake_failure(
            self.emitter,
            flow_id="flow-1",
            handshake_id="hs-1",
            failure_reason="Trust insufficient"
        )
        
        events = self.emitter.get_events_by_type(TelemetryEventType.HANDSHAKE_FAILURE.value)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].properties["failure_reason"], "Trust insufficient")

    def test_deadline_breach_observation(self):
        """Deadline breach events recorded."""
        TelemetryObserver.record_deadline_breach(
            self.emitter,
            flow_id="flow-1",
            deadline_id="dl-1",
            breach_reason="Execution exceeded deadline"
        )
        
        events = self.emitter.get_events_by_type(TelemetryEventType.DEADLINE_BREACH.value)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].deadline_id, "dl-1")

    def test_dispatch_observation(self):
        """Dispatch events recorded."""
        TelemetryObserver.record_dispatch_sent(
            self.emitter,
            flow_id="flow-1",
            request_id="req-1"
        )
        
        events = self.emitter.get_events_by_type(TelemetryEventType.DISPATCH_SENT.value)
        self.assertEqual(len(events), 1)

    def test_receipt_observation(self):
        """Receipt events recorded."""
        TelemetryObserver.record_receipt_received(
            self.emitter,
            flow_id="flow-1",
            request_id="req-1",
            receipt_id="rec-1"
        )
        
        events = self.emitter.get_events_by_type(TelemetryEventType.RECEIPT_RECEIVED.value)
        self.assertEqual(len(events), 1)


if __name__ == "__main__":
    unittest.main()
