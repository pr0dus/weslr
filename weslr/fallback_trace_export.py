"""Fallback Trace Export / Replay Integration (v74)

Integrate v73 distributed fallback behavior into the existing diagnostic
replay/export stack so fallback activation, path choice, and recovery-safe
alternatives are visible in operator-facing replay and machine-readable exports.

Architecture:
  - FallbackTraceRecord — trace record with fallback context
  - FallbackTraceExporter — export traces with fallback visibility
  - FallbackTraceReconstructor — rebuild traces with fallback path info
  - FallbackTraceSummary — operator-readable fallback summary
  - FallbackTraceExporter — machine-readable fallback trace exports

Rules:
  - Read-only diagnostic/export integration only
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - No telemetry backend/service
  - No scheduler/task engine
  - No consensus
  - No orchestration, sharding, aggregation
  - No TIA/C#
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .distributed_fallback import (
    FallbackManager,
    FallbackReason,
    PathCapability,
    FallbackState,
    NodeFallbackStatus,
    FallbackAuditRecord,
    FallbackPathSelector,
    create_fallback_manager,
)
from .distributed_diagnostic_hooks import DiagnosticHooks, DiagnosticHooks
from .execution_telemetry import TelemetryEventEmitter


# ============================================================================
# FALLBACK TRACE RECORD
# ============================================================================


@dataclass
class FallbackTraceRecord:
    """Trace export record with fallback context.
    
    Extends trace export with fallback state, reason, path capability,
    and recovery-safe alternative visibility.
    """
    
    # Core trace data
    trace_id: str
    flow_id: str
    timestamp: str
    
    # Fallback context
    fallback_state: FallbackState = FallbackState.NORMAL
    fallback_reason: Optional[FallbackReason] = None
    path_capability: Optional[PathCapability] = None
    
    # Path selection info
    selected_path_id: Optional[str] = None
    selected_path_config: Dict[str, Any] = field(default_factory=dict)
    
    # Recovery-safe alternatives
    available_paths: List[Dict[str, Any]] = field(default_factory=list)
    
    # Correlation
    request_id: Optional[str] = None
    handshake_id: Optional[str] = None
    deadline_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize record to dict."""
        return {
            "trace_id": self.trace_id,
            "flow_id": self.flow_id,
            "timestamp": self.timestamp,
            "fallback_state": self.fallback_state.value if self.fallback_state else None,
            "fallback_reason": self.fallback_reason.value if self.fallback_reason else None,
            "path_capability": self.path_capability.value if self.path_capability else None,
            "selected_path_id": self.selected_path_id,
            "selected_path_config": self.selected_path_config,
            "available_paths": self.available_paths,
            "request_id": self.request_id,
            "handshake_id": self.handshake_id,
            "deadline_id": self.deadline_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FallbackTraceRecord":
        """Deserialize record from dict."""
        return cls(
            trace_id=data.get("trace_id", str(uuid.uuid4())),
            flow_id=data.get("flow_id", ""),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            fallback_state=FallbackState(data.get("fallback_state", "normal")),
            fallback_reason=FallbackReason(data.get("fallback_reason")) if data.get("fallback_reason") else None,
            path_capability=PathCapability(data.get("path_capability")) if data.get("path_capability") else None,
            selected_path_id=data.get("selected_path_id"),
            selected_path_config=data.get("selected_path_config", {}),
            available_paths=data.get("available_paths", []),
            request_id=data.get("request_id"),
            handshake_id=data.get("handshake_id"),
            deadline_id=data.get("deadline_id"),
        )
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "FallbackTraceRecord":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


# ============================================================================
# FALLBACK TRACE EXPORTER
# ============================================================================


class FallbackTraceExporter:
    """Export fallback traces with full visibility into fallback behavior.
    
    Integrates v73 fallback behavior into the diagnostic trace export stack.
    """
    
    def __init__(self, fallback_manager: FallbackManager):
        """Initialize exporter with fallback manager reference."""
        self._fallback_manager = fallback_manager
        self._fallback_selector = FallbackPathSelector()
    
    def export_trace(
        self,
        flow_id: str,
        request_id: Optional[str] = None,
        handshake_id: Optional[str] = None,
        deadline_id: Optional[str] = None,
    ) -> Optional[FallbackTraceRecord]:
        """Export trace with fallback context for a specific flow.
        
        Args:
            flow_id: The flow ID to export
            request_id: Request correlation ID (optional)
            handshake_id: Handshake correlation ID (optional)
            deadline_id: Deadline correlation ID (optional)
            
        Returns:
            FallbackTraceRecord or None if no fallback state
        """
        # Get node status for this flow (assume single node for now)
        # In multi-node, would need to aggregate across nodes
        
        # Build record
        record = FallbackTraceRecord(
            trace_id=str(uuid.uuid4()),
            flow_id=flow_id,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            request_id=request_id,
            handshake_id=handshake_id,
            deadline_id=deadline_id,
        )
        
        # Get fallback status for this flow
        status = self._fallback_manager.get_node_status(flow_id)
        if status:
            record.fallback_state = status.state
            record.fallback_reason = status.reason
            record.path_capability = status.path_capability
        
        return record
    
    def export_all_traces(self) -> List[FallbackTraceRecord]:
        """Export all fallback traces.
        
        Returns:
            List of fallback trace records
        """
        # Get flows from fallback manager audit records
        traces = []
        audit_records = self._fallback_manager.export_audit_records()
        
        for audit in audit_records:
            record = FallbackTraceRecord(
                trace_id=audit.get("audit_id", str(uuid.uuid4())),
                flow_id=audit.get("flow_id", "unknown"),
                timestamp=audit.get("timestamp", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
                fallback_state=FallbackState(audit.get("state_after", "normal")),
                fallback_reason=FallbackReason(audit.get("reason", "unavailable")),
                path_capability=PathCapability(audit.get("path_capability", "deterministic_capable")),
                request_id=audit.get("request_id"),
                handshake_id=audit.get("handshake_id"),
                deadline_id=audit.get("deadline_id"),
            )
            
            # Add recovery-safe alternatives
            record.available_paths = self._fallback_manager.get_all_local_paths()
            
            traces.append(record)
        
        return traces
    
    def export_as_dict(self) -> Dict[str, Any]:
        """Export all fallback traces as dictionary.
        
        Returns:
            Dictionary with traces and metadata
        """
        traces = self.export_all_traces()
        trace_dicts = [t.to_dict() for t in traces]
        
        # Count by capability
        model_required_count = sum(1 for t in traces if t.path_capability == PathCapability.MODEL_REQUIRED)
        deterministic_capable_count = sum(1 for t in traces if t.path_capability == PathCapability.DETERMINISTIC_CAPABLE)
        
        # Count by reason
        reason_counts: Dict[str, int] = {}
        for t in traces:
            reason = t.fallback_reason.value if t.fallback_reason else "none"
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        return {
            "export_metadata": {
                "exported_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "export_version": "v74.0.0",
                "trace_count": len(traces),
            },
            "traces": trace_dicts,
            "capabilities": {
                "model_required": model_required_count,
                "deterministic_capable": deterministic_capable_count,
            },
            "reasons": reason_counts,
            "recovery_safe_alternatives": self._fallback_manager.get_all_local_paths(),
        }
    
    def export_as_json(self, pretty: bool = False) -> str:
        """Export all fallback traces as JSON.
        
        Args:
            pretty: If True, format with indentation
            
        Returns:
            JSON string with fallback trace data
        """
        data = self.export_as_dict()
        if pretty:
            return json.dumps(data, indent=2)
        return json.dumps(data)
    
    def export_by_correlation(
        self,
        correlation_id: str,
        correlation_type: str = "flow_id",
    ) -> List[Dict[str, Any]]:
        """Export fallback traces filtered by correlation ID.
        
        Args:
            correlation_id: Correlation ID to filter by
            correlation_type: Type of correlation (flow_id, request_id, handshake_id, deadline_id)
            
        Returns:
            List of matching trace records
        """
        traces = self.export_all_traces()
        
        if correlation_type == "flow_id":
            return [t.to_dict() for t in traces if t.flow_id == correlation_id]
        elif correlation_type == "request_id":
            return [t.to_dict() for t in traces if t.request_id == correlation_id]
        elif correlation_type == "handshake_id":
            return [t.to_dict() for t in traces if t.handshake_id == correlation_id]
        elif correlation_type == "deadline_id":
            return [t.to_dict() for t in traces if t.deadline_id == correlation_id]
        
        return []
    
    def get_operator_readable_summary(self) -> str:
        """Get human-readable operator summary of fallback traces.
        
        Returns:
            Multi-line string for operator console
        """
        traces = self.export_all_traces()
        
        lines = [
            "=== FALLBACK TRACE SUMMARY ===",
            f"Total Traces: {len(traces)}",
            "",
        ]
        
        if not traces:
            lines.append("No fallback traces to report.")
            return "\n".join(lines)
        
        # Group by flow
        by_flow: Dict[str, List[FallbackTraceRecord]] = {}
        for t in traces:
            if t.flow_id not in by_flow:
                by_flow[t.flow_id] = []
            by_flow[t.flow_id].append(t)
        
        for flow_id, flow_traces in by_flow.items():
            lines.append(f"--- Flow: {flow_id} ---")
            
            for trace in flow_traces:
                lines.append(f"  Timestamp: {trace.timestamp}")
                lines.append(f"  Fallback State: {trace.fallback_state.value}")
                
                if trace.fallback_reason:
                    lines.append(f"  Reason: {trace.fallback_reason.value}")
                
                if trace.path_capability:
                    lines.append(f"  Capability: {trace.path_capability.value}")
                
                if trace.selected_path_id:
                    lines.append(f"  Selected Path: {trace.selected_path_id}")
                
                lines.append("")
        
        # Recovery-safe alternatives summary
        lines.append("=== RECOVERY-SAFE ALTERNATIVES ===")
        paths = self._fallback_manager.get_all_local_paths()
        if paths:
            for path in paths:
                lines.append(f"  Path: {path.get('path_id', 'unknown')}")
                lines.append(f"    Capability: {path.get('capability', 'unknown')}")
                lines.append(f"    Enabled: {path.get('enabled', False)}")
                lines.append("")
        else:
            lines.append("  No local fallback paths configured.")
        
        return "\n".join(lines)


# ============================================================================
# FALLBACK TRACE RECONSTRUCTOR
# ============================================================================


class FallbackTraceReconstructor:
    """Rebuild fallback traces with path selection and recovery info.
    
    Provides reconstruction of fallback behavior with visibility into
    path selection and recovery-safe alternatives.
    """
    
    def __init__(self):
        """Initialize reconstructor."""
        self._fallback_manager: Optional[FallbackManager] = None
        self._fallback_selector = FallbackPathSelector()
        self._traces: Dict[str, List[FallbackTraceRecord]] = {}
    
    def set_fallback_manager(self, manager: FallbackManager) -> None:
        """Set fallback manager for reconstruction context."""
        self._fallback_manager = manager
    
    def add_traces(self, records: List[FallbackTraceRecord]) -> None:
        """Add trace records to reconstructor.
        
        Args:
            records: Fallback trace records to add
        """
        for record in records:
            flow_id = record.flow_id
            if flow_id not in self._traces:
                self._traces[flow_id] = []
            self._traces[flow_id].append(record)
    
    def rebuild_trace(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Rebuild fallback trace for a specific flow.
        
        Args:
            flow_id: The flow ID to rebuild
            
        Returns:
            Reconstructed trace dict or None if not found
        """
        if flow_id not in self._traces:
            return None
        
        traces = self._traces[flow_id]
        
        # Get fallback status for this flow
        fallback_state = FallbackState.NORMAL
        fallback_reason: Optional[FallbackReason] = None
        path_capability: Optional[PathCapability] = None
        
        for trace in traces:
            if trace.fallback_state != FallbackState.NORMAL:
                fallback_state = trace.fallback_state
                fallback_reason = trace.fallback_reason
                path_capability = trace.path_capability
                break
        
        # Select fallback path if available
        selected_path_id = None
        selected_path_config = {}
        available_paths = self._fallback_manager.get_all_local_paths() if self._fallback_manager else []
        
        if fallback_state != FallbackState.NORMAL and path_capability:
            path_selector = FallbackPathSelector()
            for path in available_paths:
                path_selector.register_local_path(
                    path_id=path.get("path_id", ""),
                    capability=PathCapability(path.get("capability", "deterministic_capable")),
                    enabled=path.get("enabled", False),
                )
            
            selected_id, config = path_selector.select_fallback_path(
                path_capability=path_capability,
                reason=fallback_reason or FallbackReason.UNAVAILABLE,
            )
            selected_path_id = selected_id
            selected_path_config = config
        
        return {
            "flow_id": flow_id,
            "fallback_state": fallback_state.value,
            "fallback_reason": fallback_reason.value if fallback_reason else None,
            "path_capability": path_capability.value if path_capability else None,
            "selected_path_id": selected_path_id,
            "selected_path_config": selected_path_config,
            "available_paths": available_paths,
            "trace_count": len(traces),
        }
    
    def rebuild_all_traces(self) -> List[Dict[str, Any]]:
        """Rebuild all fallback traces.
        
        Returns:
            List of reconstructed trace dicts
        """
        traces = []
        for flow_id in self._traces:
            trace = self.rebuild_trace(flow_id)
            if trace:
                traces.append(trace)
        return traces
    
    def get_fallback_timeline(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get fallback state timeline for a flow.
        
        Args:
            flow_id: The flow ID to get timeline for
            
        Returns:
            List of state change events
        """
        if flow_id not in self._traces:
            return []
        
        events = []
        for trace in sorted(self._traces[flow_id], key=lambda t: t.timestamp):
            events.append({
                "timestamp": trace.timestamp,
                "state": trace.fallback_state.value,
                "reason": trace.fallback_reason.value if trace.fallback_reason else None,
                "path_capability": trace.path_capability.value if trace.path_capability else None,
            })
        
        return events
    
    def get_recovery_safe_alternatives(self) -> List[Dict[str, Any]]:
        """Get recovery-safe alternative paths.
        
        Returns:
            List of available local fallback paths
        """
        return self._fallback_manager.get_all_local_paths() if self._fallback_manager else []


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================


def create_fallback_trace_exporter(
    fallback_manager: FallbackManager,
) -> FallbackTraceExporter:
    """Factory function to create fallback trace exporter.
    
    Args:
        fallback_manager: Fallback manager instance
        
    Returns:
        FallbackTraceExporter instance
    """
    return FallbackTraceExporter(fallback_manager)


def create_fallback_trace_reconstructor(
    fallback_manager: Optional[FallbackManager] = None,
) -> FallbackTraceReconstructor:
    """Factory function to create fallback trace reconstructor.
    
    Args:
        fallback_manager: Optional fallback manager instance
        
    Returns:
        FallbackTraceReconstructor instance
    """
    reconstructor = FallbackTraceReconstructor()
    if fallback_manager:
        reconstructor.set_fallback_manager(fallback_manager)
    return reconstructor
