"""Distributed Execution Telemetry Layer (v68)

Passive telemetry/observability for distributed execution flow.
Records flow lifecycle events, handshake metrics, deadline breaches,
dispatch/receipt timing, and rollback/failure tracking.

Architecture:
  - TelemetryEventType — event type enumeration
  - TelemetryEvent — single telemetry record
  - TelemetryEventEmitter — centralized, passive event collector
  - TelemetryMetrics — aggregated metrics summary

Rules:
  - Telemetry is passive — no flow control
  - Events emitted by observers, not controllers
  - Correlation via flow/request/session IDs
  - Audit export hooks for external ingestion
  - No telemetry backend/service
  - No scheduler/retry engine
  - No consensus
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - No TIA/C#
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# TELEMETRY EVENT TYPES
# ============================================================================


class TelemetryEventType(str, Enum):
    """Types of telemetry events emitted during distributed execution."""
    # Flow lifecycle
    FLOW_CREATED = "flow_created"
    FLOW_COMPLETED = "flow_completed"
    FLOW_FAILED = "flow_failed"
    FLOW_CANCELLED = "flow_cancelled"
    FLOW_REJECTED = "flow_rejected"
    FLOW_ROLLBACK_INITIATED = "flow_rollback_initiated"
    FLOW_ROLLBACK_COMPLETED = "flow_rollback_completed"
    
    # Handshake metrics
    HANDSHAKE_SUCCESS = "handshake_success"
    HANDSHAKE_FAILURE = "handshake_failure"
    
    # Deadline metrics
    DEADLINE_BREACH = "deadline_breach"
    
    # Dispatch/receipt timing
    DISPATCH_SENT = "dispatch_sent"
    DISPATCH_RECEIVED = "dispatch_received"
    RECEIPT_RECEIVED = "receipt_received"
    ACKNOWLEDGMENT_SENT = "acknowledgment_sent"
    
    # Execution state changes
    ENVELOPE_CREATED = "envelope_created"
    ENVELOPE_AUTHORIZED = "envelope_authorized"
    ENVELOPE_DISPATCHED = "envelope_dispatched"
    GATES_EVALUATED = "gates_evaluated"
    GATES_PASSED = "gates_passed"
    GATES_FAILED = "gates_failed"


# ============================================================================
# TELEMETRY EVENT MODEL
# ============================================================================


@dataclass
class TelemetryEvent:
    """Single telemetry event record."""
    
    event_id: str
    event_type: str
    timestamp: datetime
    flow_id: Optional[str] = None
    request_id: Optional[str] = None
    handshake_id: Optional[str] = None
    deadline_id: Optional[str] = None
    duration_ms: Optional[float] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    correlation_ids: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dict."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat().replace("+00:00", "Z"),
            "flow_id": self.flow_id,
            "request_id": self.request_id,
            "handshake_id": self.handshake_id,
            "deadline_id": self.deadline_id,
            "duration_ms": self.duration_ms,
            "properties": self.properties,
            "correlation_ids": self.correlation_ids
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TelemetryEvent":
        """Deserialize event from dict."""
        timestamp_str = data.get("timestamp", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except Exception:
            timestamp = datetime.now(timezone.utc)
        
        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            event_type=data["event_type"],
            timestamp=timestamp,
            flow_id=data.get("flow_id"),
            request_id=data.get("request_id"),
            handshake_id=data.get("handshake_id"),
            deadline_id=data.get("deadline_id"),
            duration_ms=data.get("duration_ms"),
            properties=data.get("properties", {}),
            correlation_ids=data.get("correlation_ids", {})
        )
    
    def to_json(self) -> str:
        """Serialize event to JSON string."""
        return json.dumps(self.to_dict())


# ============================================================================
# TELEMETRY EVENT EMITTER
# ============================================================================


class TelemetryEventEmitter:
    """Centralized, passive telemetry event collector.
    
    Observes execution flow and collects events for analysis.
    Does NOT control execution flow.
    """
    
    def __init__(self):
        self._events: List[TelemetryEvent] = []
        self._events_by_flow: Dict[str, List[TelemetryEvent]] = {}
        self._events_by_type: Dict[str, List[TelemetryEvent]] = {}
    
    def emit_event(self, event: TelemetryEvent) -> None:
        """Record a telemetry event.
        
        This is a passive observer - it records events but does not
        modify execution flow or behavior.
        """
        self._events.append(event)
        
        if event.flow_id:
            if event.flow_id not in self._events_by_flow:
                self._events_by_flow[event.flow_id] = []
            self._events_by_flow[event.flow_id].append(event)
        
        if event.event_type not in self._events_by_type:
            self._events_by_type[event.event_type] = []
        self._events_by_type[event.event_type].append(event)
    
    def create_event(
        self,
        event_type: str,
        flow_id: Optional[str] = None,
        request_id: Optional[str] = None,
        handshake_id: Optional[str] = None,
        deadline_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        properties: Optional[Dict[str, Any]] = None,
        correlation_ids: Optional[Dict[str, str]] = None
    ) -> TelemetryEvent:
        """Create and emit a telemetry event."""
        event = TelemetryEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            flow_id=flow_id,
            request_id=request_id,
            handshake_id=handshake_id,
            deadline_id=deadline_id,
            duration_ms=duration_ms,
            properties=properties or {},
            correlation_ids=correlation_ids or {}
        )
        self.emit_event(event)
        return event
    
    def get_events_by_flow(self, flow_id: str) -> List[TelemetryEvent]:
        """Get all events for a flow."""
        return self._events_by_flow.get(flow_id, [])
    
    def get_events_by_type(self, event_type: str) -> List[TelemetryEvent]:
        """Get all events of a specific type."""
        return self._events_by_type.get(event_type, [])
    
    def get_all_events(self) -> List[TelemetryEvent]:
        """Get all recorded events."""
        return self._events.copy()
    
    def get_metrics(self) -> Dict[str, int]:
        """Get aggregated metrics summary."""
        metrics = {}
        for event_type, events in self._events_by_type.items():
            metrics[event_type] = len(events)
        return metrics
    
    def export_as_json(self) -> str:
        """Export all events as JSON for audit purposes."""
        events_data = [e.to_dict() for e in self._events]
        return json.dumps(events_data, indent=2)
    
    def export_by_flow(self) -> Dict[str, List[Dict[str, Any]]]:
        """Export events grouped by flow ID."""
        result = {}
        for flow_id, events in self._events_by_flow.items():
            result[flow_id] = [e.to_dict() for e in events]
        return result
    
    def clear(self) -> None:
        """Clear all recorded events."""
        self._events.clear()
        self._events_by_flow.clear()
        self._events_by_type.clear()
    
    def get_all_flows(self) -> List[str]:
        """Get all unique flow IDs."""
        return list(self._events_by_flow.keys())
    
    def get_flow_count(self) -> int:
        """Get count of tracked flows."""
        return len(self._events_by_flow)
    
    def _now(self) -> datetime:
        """Get current timestamp."""
        return datetime.now(timezone.utc)


# ============================================================================
# TELEMETRY OBSERVER
# ============================================================================


class TelemetryObserver:
    """Passive observer that adds telemetry hooks to execution objects.
    
    This class provides methods to add telemetry to existing objects
    without modifying their core logic.
    """
    
    @staticmethod
    def observe_flow_lifecycle(
        emitter: TelemetryEventEmitter,
        flow_id: str,
        request_id: Optional[str] = None,
        handshake_id: Optional[str] = None,
        deadline_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create correlation context for flow lifecycle telemetry."""
        correlation_ids = {
            "flow_id": flow_id,
            "request_id": request_id or "none",
            "handshake_id": handshake_id or "none",
            "deadline_id": deadline_id or "none"
        }
        return {
            "emitter": emitter,
            "correlation_ids": correlation_ids,
            "start_time": datetime.now(timezone.utc)
        }
    
    @staticmethod
    def record_flow_completed(
        context: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record flow completion event."""
        emitter = context["emitter"]
        emitter.create_event(
            event_type=TelemetryEventType.FLOW_COMPLETED.value,
            flow_id=context["correlation_ids"]["flow_id"],
            request_id=context["correlation_ids"]["request_id"],
            duration_ms=TelemetryObserver._calculate_duration(context),
            properties={"result": result} if result else {}
        )
    
    @staticmethod
    def record_flow_failed(
        context: Dict[str, Any],
        reason: str
    ) -> None:
        """Record flow failure event."""
        emitter = context["emitter"]
        emitter.create_event(
            event_type=TelemetryEventType.FLOW_FAILED.value,
            flow_id=context["correlation_ids"]["flow_id"],
            request_id=context["correlation_ids"]["request_id"],
            duration_ms=TelemetryObserver._calculate_duration(context),
            properties={"reason": reason}
        )
    
    @staticmethod
    def record_handshake_success(
        emitter: TelemetryEventEmitter,
        flow_id: str,
        handshake_id: str,
        handshake_result: Dict[str, Any]
    ) -> None:
        """Record successful handshake."""
        emitter.create_event(
            event_type=TelemetryEventType.HANDSHAKE_SUCCESS.value,
            flow_id=flow_id,
            handshake_id=handshake_id,
            properties={"handshake_result": handshake_result}
        )
    
    @staticmethod
    def record_handshake_failure(
        emitter: TelemetryEventEmitter,
        flow_id: str,
        handshake_id: str,
        failure_reason: str
    ) -> None:
        """Record failed handshake."""
        emitter.create_event(
            event_type=TelemetryEventType.HANDSHAKE_FAILURE.value,
            flow_id=flow_id,
            handshake_id=handshake_id,
            properties={"failure_reason": failure_reason}
        )
    
    @staticmethod
    def record_deadline_breach(
        emitter: TelemetryEventEmitter,
        flow_id: str,
        deadline_id: str,
        breach_reason: str
    ) -> None:
        """Record deadline breach."""
        emitter.create_event(
            event_type=TelemetryEventType.DEADLINE_BREACH.value,
            flow_id=flow_id,
            deadline_id=deadline_id,
            properties={"breach_reason": breach_reason}
        )
    
    @staticmethod
    def record_dispatch_sent(
        emitter: TelemetryEventEmitter,
        flow_id: str,
        request_id: str
    ) -> None:
        """Record dispatch sent."""
        emitter.create_event(
            event_type=TelemetryEventType.DISPATCH_SENT.value,
            flow_id=flow_id,
            request_id=request_id
        )
    
    @staticmethod
    def record_receipt_received(
        emitter: TelemetryEventEmitter,
        flow_id: str,
        request_id: str,
        receipt_id: str
    ) -> None:
        """Record receipt received."""
        emitter.create_event(
            event_type=TelemetryEventType.RECEIPT_RECEIVED.value,
            flow_id=flow_id,
            request_id=request_id,
            correlation_ids={"receipt_id": receipt_id}
        )
    
    @staticmethod
    def _calculate_duration(context: Dict[str, Any]) -> Optional[float]:
        """Calculate duration in milliseconds since start."""
        start_time = context.get("start_time")
        if not start_time:
            return None
        end_time = datetime.now(timezone.utc)
        delta = end_time - start_time
        return delta.total_seconds() * 1000
