"""Distributed Telemetry Export Hooks (v69)

Structured export and operator-readable observability hooks for v68 telemetry.

Architecture:
  - TelemetrySnapshotExporter — telemetry snapshot export (events, by_flow, by_type)
  - TelemetryFlowTraceExporter — flow trace export with correlation IDs
  - TelemetryMetricsExporter — metrics summary export
  - OperatorDiagnosticHooks — operator diagnostics hooks

Rules:
  - Telemetry is passive — no flow control
  - Export hooks are read-only inspection
  - Correlation by flow/request/session/deadline IDs
  - No telemetry backend/service
  - No scheduler/retry engine
  - No consensus
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - No TIA/C#
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .execution_telemetry import (
    TelemetryEventEmitter,
    TelemetryEvent,
    TelemetryEventType,
    TelemetryObserver,
)


# ============================================================================
# TELEMETRY SNAPSHOT EXPORTER
# ============================================================================


class TelemetrySnapshotExporter:
    """Export telemetry as structured snapshots for operator-readable observability.
    
    Provides read-only inspection of telemetry state without modifying it.
    """
    
    def __init__(self, emitter: TelemetryEventEmitter):
        """Initialize exporter with emitter reference."""
        self._emitter = emitter
    
    def export_all_events(self) -> List[Dict[str, Any]]:
        """Export all events as a list of dictionaries.
        
        Returns a snapshot of all recorded telemetry events.
        This is a read-only copy — modifications do not affect the emitter.
        """
        return [event.to_dict() for event in self._emitter.get_all_events()]
    
    def export_by_flow(self) -> Dict[str, List[Dict[str, Any]]]:
        """Export events grouped by flow ID.
        
        Each flow key contains an array of events in chronological order.
        """
        return self._emitter.export_by_flow()
    
    def export_by_type(self) -> Dict[str, List[Dict[str, Any]]]:
        """Export events grouped by event type."""
        result: Dict[str, List[Dict[str, Any]]] = {}
        for event_type, events in self._emitter._events_by_type.items():
            result[event_type] = [e.to_dict() for e in events]
        return result
    
    def export_events_in_range(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Export events within a time range.
        
        Args:
            start_time: ISO format start time (inclusive), defaults to all events
            end_time: ISO format end time (inclusive), defaults to all events
        
        Returns:
            Events matching the time range filter
        """
        events = []
        for event in self._emitter.get_all_events():
            event_time = event.timestamp.isoformat()
            if start_time and event_time < start_time:
                continue
            if end_time and event_time > end_time:
                continue
            events.append(event.to_dict())
        return events
    
    def export_json(self, pretty: bool = False) -> str:
        """Export all events as JSON string.
        
        Args:
            pretty: If True, format with indentation for readability
        """
        data = self.export_all_events()
        if pretty:
            return json.dumps(data, indent=2)
        return json.dumps(data)


# ============================================================================
# TELEMETRY FLOW TRACE EXPORTER
# ============================================================================


class TelemetryFlowTraceExporter:
    """Export flow traces with full correlation chain for operator diagnostics.
    
    Provides operator-readable trace of execution flows including:
    - Event chain by flow ID
    - Correlation IDs (flow, request, handshake, deadline)
    - Timing information (duration_ms)
    - Event relationships
    """
    
    def __init__(self, emitter: TelemetryEventEmitter):
        """Initialize exporter with emitter reference."""
        self._emitter = emitter
    
    def export_flow_trace(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Export complete trace for a specific flow.
        
        Args:
            flow_id: The flow ID to trace
        
        Returns:
            Trace dict with events, timing, and correlation, or None if flow not found
        """
        events = self._emitter.get_events_by_flow(flow_id)
        if not events:
            return None
        
        # Get first and last event timestamps for duration
        timestamps = [e.timestamp for e in events]
        start_time = min(timestamps)
        end_time = max(timestamps)
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Collect correlation IDs from events
        correlation_ids: Dict[str, Any] = {}
        for event in events:
            if event.flow_id:
                correlation_ids["flow_id"] = event.flow_id
            if event.request_id:
                correlation_ids["request_id"] = event.request_id
            if event.handshake_id:
                correlation_ids["handshake_id"] = event.handshake_id
            if event.deadline_id:
                correlation_ids["deadline_id"] = event.deadline_id
            # Merge correlation_ids from events
            for k, v in event.correlation_ids.items():
                if k not in correlation_ids:
                    correlation_ids[k] = v
        
        return {
            "flow_id": flow_id,
            "start_time": start_time.isoformat().replace("+00:00", "Z"),
            "end_time": end_time.isoformat().replace("+00:00", "Z"),
            "duration_ms": round(duration_ms, 2),
            "event_count": len(events),
            "events": [e.to_dict() for e in events],
            "correlation_ids": correlation_ids
        }
    
    def export_all_flow_traces(self) -> Dict[str, Dict[str, Any]]:
        """Export traces for all flows.
        
        Returns:
            Dict mapping flow_id -> trace dict
        """
        result: Dict[str, Dict[str, Any]] = {}
        
        # Get all unique flow IDs
        flow_ids = set()
        for event in self._emitter.get_all_events():
            if event.flow_id:
                flow_ids.add(event.flow_id)
        
        for flow_id in flow_ids:
            trace = self.export_flow_trace(flow_id)
            if trace:
                result[flow_id] = trace
        
        return result
    
    def export_correlation_chain(self, flow_id: str) -> Optional[List[Dict[str, Any]]]:
        """Export correlation chain for a flow.
        
        Returns events ordered by time with correlation context.
        """
        events = self._emitter.get_events_by_flow(flow_id)
        if not events:
            return None
        
        return [self._build_correlation_chain_item(e) for e in events]
    
    def _build_correlation_chain_item(
        self,
        event: TelemetryEvent
    ) -> Dict[str, Any]:
        """Build a single chain item with correlation context."""
        item: Dict[str, Any] = {
            "event_type": event.event_type,
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat().replace("+00:00", "Z"),
        }
        
        # Add correlation IDs if present
        if event.flow_id:
            item["flow_id"] = event.flow_id
        if event.request_id:
            item["request_id"] = event.request_id
        if event.handshake_id:
            item["handshake_id"] = event.handshake_id
        if event.deadline_id:
            item["deadline_id"] = event.deadline_id
        
        # Add duration if present
        if event.duration_ms is not None:
            item["duration_ms"] = event.duration_ms
        
        # Add properties if present
        if event.properties:
            item["properties"] = event.properties
        
        return item


# ============================================================================
# TELEMETRY METRICS EXPORTER
# ============================================================================


class TelemetryMetricsExporter:
    """Export aggregated telemetry metrics for operator diagnostics.
    
    Provides operator-readable metrics summaries including:
    - Event type counts
    - Flow-level statistics
    - Timing statistics
    - Success/failure ratios
    """
    
    def __init__(self, emitter: TelemetryEventEmitter):
        """Initialize exporter with emitter reference."""
        self._emitter = emitter
    
    def export_event_counts(self) -> Dict[str, int]:
        """Export event type counts.
        
        Returns:
            Dict mapping event_type -> count
        """
        return self._emitter.get_metrics()
    
    def export_metrics_summary(self) -> Dict[str, Any]:
        """Export comprehensive metrics summary.
        
        Includes:
        - Total event count
        - Events by type breakdown
        - Events by flow breakdown
        - Success/failure counts
        """
        events = self._emitter.get_all_events()
        
        # Count by type
        type_counts: Dict[str, int] = {}
        for event in events:
            type_counts[event.event_type] = type_counts.get(event.event_type, 0) + 1
        
        # Count by flow
        flow_counts: Dict[str, int] = {}
        for event in events:
            if event.flow_id:
                flow_counts[event.flow_id] = flow_counts.get(event.flow_id, 0) + 1
        
        # Calculate success/failure counts
        success_count = type_counts.get(TelemetryEventType.FLOW_COMPLETED.value, 0)
        failure_count = type_counts.get(TelemetryEventType.FLOW_FAILED.value, 0)
        rejection_count = type_counts.get(TelemetryEventType.FLOW_REJECTED.value, 0)
        
        # Calculate handshake metrics
        handshake_success = type_counts.get(TelemetryEventType.HANDSHAKE_SUCCESS.value, 0)
        handshake_failure = type_counts.get(TelemetryEventType.HANDSHAKE_FAILURE.value, 0)
        
        # Calculate deadline breach metrics
        deadline_breach = type_counts.get(TelemetryEventType.DEADLINE_BREACH.value, 0)
        
        return {
            "total_events": len(events),
            "events_by_type": type_counts,
            "events_by_flow": flow_counts,
            "success_count": success_count,
            "failure_count": failure_count,
            "rejection_count": rejection_count,
            "handshake_success": handshake_success,
            "handshake_failure": handshake_failure,
            "deadline_breach": deadline_breach,
            "success_rate": round(success_count / len(events) * 100, 2) if events else 0.0
        }
    
    def export_flow_metrics(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Export metrics for a specific flow.
        
        Returns:
            Flow metrics or None if flow not found
        """
        events = self._emitter.get_events_by_flow(flow_id)
        if not events:
            return None
        
        # Count events by type for this flow
        type_counts: Dict[str, int] = {}
        for event in events:
            type_counts[event.event_type] = type_counts.get(event.event_type, 0) + 1
        
        # Determine flow outcome
        has_completion = TelemetryEventType.FLOW_COMPLETED.value in type_counts
        has_failure = TelemetryEventType.FLOW_FAILED.value in type_counts
        has_rejection = TelemetryEventType.FLOW_REJECTED.value in type_counts
        
        outcome = None
        if has_completion:
            outcome = "completed"
        elif has_failure:
            outcome = "failed"
        elif has_rejection:
            outcome = "rejected"
        else:
            outcome = "incomplete"
        
        return {
            "flow_id": flow_id,
            "event_count": len(events),
            "events_by_type": type_counts,
            "outcome": outcome,
            "has_handshake_success": TelemetryEventType.HANDSHAKE_SUCCESS.value in type_counts,
            "has_handshake_failure": TelemetryEventType.HANDSHAKE_FAILURE.value in type_counts,
            "has_deadline_breach": TelemetryEventType.DEADLINE_BREACH.value in type_counts
        }
    
    def export_all_flow_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Export metrics for all flows."""
        result: Dict[str, Dict[str, Any]] = {}
        
        # Get all unique flow IDs
        flow_ids = set()
        for event in self._emitter.get_all_events():
            if event.flow_id:
                flow_ids.add(event.flow_id)
        
        for flow_id in flow_ids:
            metrics = self.export_flow_metrics(flow_id)
            if metrics:
                result[flow_id] = metrics
        
        return result


# ============================================================================
# OPERATOR DIAGNOSTIC HOOKS
# ============================================================================


class OperatorDiagnosticHooks:
    """Operator-facing diagnostic hooks for telemetry inspection.
    
    Provides read-only diagnostic methods for operators to inspect
    telemetry state without modifying it. Designed for operator
    workflow integration and debugging.
    """
    
    def __init__(self, emitter: TelemetryEventEmitter):
        """Initialize diagnostic hooks with emitter reference."""
        self._emitter = emitter
    
    def get_telemetry_status(self) -> Dict[str, Any]:
        """Get high-level telemetry status.
        
        Returns:
            Status dict with current state and counts
        """
        events = self._emitter.get_all_events()
        
        # Get unique flow IDs
        flow_ids = set()
        for event in events:
            if event.flow_id:
                flow_ids.add(event.flow_id)
        
        # Get unique event types
        event_types = set(e.event_type for e in events)
        
        return {
            "total_events": len(events),
            "active_flows": len(flow_ids),
            "event_type_count": len(event_types),
            "event_types": sorted(list(event_types)),
            "emitter_alive": True
        }
    
    def get_active_flows(self) -> List[str]:
        """Get list of active (tracked) flow IDs."""
        flow_ids = set()
        for event in self._emitter.get_all_events():
            if event.flow_id:
                flow_ids.add(event.flow_id)
        return sorted(list(flow_ids))
    
    def get_flows_in_state(self, event_type: str) -> List[str]:
        """Get flow IDs that have events of a specific type.
        
        Args:
            event_type: The event type to filter by
        
        Returns:
            List of flow IDs that have this event type
        """
        flow_ids = set()
        for event in self._emitter.get_events_by_type(event_type):
            if event.flow_id:
                flow_ids.add(event.flow_id)
        return sorted(list(flow_ids))
    
    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent events.
        
        Args:
            limit: Maximum number of events to return
        
        Returns:
            List of recent events (most recent first)
        """
        events = self._emitter.get_all_events()
        return [e.to_dict() for e in reversed(events[-limit:])]
    
    def export_diagnostics_json(self, pretty: bool = False) -> str:
        """Export all diagnostics as JSON string.
        
        Args:
            pretty: If True, format with indentation for readability
        
        Returns:
            JSON string with diagnostics data
        """
        diagnostics = {
            "status": self.get_telemetry_status(),
            "active_flows": self.get_active_flows(),
            "metrics": TelemetryMetricsExporter(self._emitter).export_metrics_summary()
        }
        
        if pretty:
            return json.dumps(diagnostics, indent=2)
        return json.dumps(diagnostics)
    
    def get_operator_readable_summary(self) -> str:
        """Get a human-readable operator summary.
        
        Returns:
            Multi-line string summary for operator consumption
        """
        status = self.get_telemetry_status()
        metrics = TelemetryMetricsExporter(self._emitter).export_metrics_summary()
        
        lines = [
            "=== TELEMETRY DIAGNOSTICS ===",
            f"Total Events: {status['total_events']}",
            f"Active Flows: {status['active_flows']}",
            f"Event Types: {status['event_type_count']}",
            "",
            "=== METRICS SUMMARY ===",
            f"Success Rate: {metrics['success_rate']}%",
            f"Success Count: {metrics['success_count']}",
            f"Failure Count: {metrics['failure_count']}",
            f"Rejection Count: {metrics['rejection_count']}",
            f"Handshake Success: {metrics['handshake_success']}",
            f"Handshake Failure: {metrics['handshake_failure']}",
            f"Deadline Breaches: {metrics['deadline_breach']}",
            "",
            "=== EVENT BREAKDOWN ==="
        ]
        
        for event_type, count in sorted(metrics["events_by_type"].items()):
            lines.append(f"  {event_type}: {count}")
        
        if metrics["events_by_flow"]:
            lines.append("")
            lines.append("=== BY FLOW ===")
            for flow_id, count in sorted(metrics["events_by_flow"].items()):
                lines.append(f"  {flow_id}: {count}")
        
        return "\n".join(lines)
