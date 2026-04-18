"""Distributed Fallback Behavior (v73)

Centralized fallback layer so WESLR can continue operating safely when a node,
model path, remote capability, or distributed dependency becomes unavailable
or degraded.

Architecture:
  - FallbackReason — reasons for fallback (timeout, unavailable, degraded, etc.)
  - PathCapability — path capability classification (model_required, deterministic_capable)
  - NodeFallbackStatus — node-level fallback state tracking
  - FallbackPathSelector — remote-unavailable fallback path selection
  - FallbackAuditRecord — audit trail with correlation context
  - FallbackManager — central fallback layer orchestrating behavior

Rules:
  - Read-safe / execution-safe fallback behavior only
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

from .execution_telemetry import TelemetryEventEmitter, TelemetryEvent, TelemetryEventType
from .distributed_diagnostic_hooks import DiagnosticHooks


# ============================================================================
# FALLBACK REASONS
# ============================================================================


class FallbackReason(str, Enum):
    """Reasons for fallback behavior.
    
    These represent the actual causes triggering fallback:
    - timeout: Execution or communication timed out
    - unavailable: Remote dependency unavailable
    - degraded: Remote dependency degraded performance
    - handshake_failed: Handshake with remote node failed
    - deadline_breached: Deadline not met
    - remote_refused: Remote node refused request
    - model_unavailable: Model path or service unavailable
    """
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    HANDSHAKE_FAILED = "handshake_failed"
    DEADLINE_BREACHED = "deadline_breached"
    REMOTE_REFUSED = "remote_refused"
    MODEL_UNAVAILABLE = "model_unavailable"


# ============================================================================
# PATH CAPABILITY CLASSIFICATION
# ============================================================================


class PathCapability(str, Enum):
    """Path capability classification for fallback decisions.
    
    These classify what a path can do, independent of why fallback is needed:
    - model_required: Requires model/LLM inference (cannot fallback to deterministic)
    - deterministic_capable: Can execute without model (deterministic fallback available)
    """
    MODEL_REQUIRED = "model_required"
    DETERMINISTIC_CAPABLE = "deterministic_capable"


# ============================================================================
# FALLBACK STATE ENUM
# ============================================================================


class FallbackState(str, Enum):
    """Fallback state for a node or path.
    
    States:
    - NORMAL: No fallback active, operating normally
    - DEGRADED: Running in degraded mode (some functionality limited)
    - REMOTE_UNAVAILABLE: Remote dependencies unavailable, using fallback
    - LOCAL_ONLY: Running in local-only mode
    - MODEL_REQUIRED: Model required but unavailable, using fallback
    - DETERMINISTIC_ONLY: Running with deterministic operations only
    """
    NORMAL = "normal"
    DEGRADED = "degraded"
    REMOTE_UNAVAILABLE = "remote_unavailable"
    LOCAL_ONLY = "local_only"
    MODEL_REQUIRED = "model_required"
    DETERMINISTIC_ONLY = "deterministic_only"


# ============================================================================
# NODE FALLBACK STATUS
# ============================================================================


@dataclass
class NodeFallbackStatus:
    """Node-level fallback state tracking.
    
    Tracks the current fallback state for a specific node, including
    when it entered fallback and the reason for fallback.
    """
    
    node_id: str
    state: FallbackState = FallbackState.NORMAL
    entered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    reason: Optional[FallbackReason] = None
    path_capability: Optional[PathCapability] = None
    correlation_ids: Dict[str, str] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize status to dict."""
        return {
            "node_id": self.node_id,
            "state": self.state.value,
            "entered_at": self.entered_at,
            "reason": self.reason.value if self.reason else None,
            "path_capability": self.path_capability.value if self.path_capability else None,
            "correlation_ids": self.correlation_ids,
            "details": self.details,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeFallbackStatus":
        """Deserialize status from dict."""
        return cls(
            node_id=data.get("node_id", ""),
            state=FallbackState(data.get("state", "normal")),
            entered_at=data.get("entered_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            reason=FallbackReason(data.get("reason")) if data.get("reason") else None,
            path_capability=PathCapability(data.get("path_capability")) if data.get("path_capability") else None,
            correlation_ids=data.get("correlation_ids", {}),
            details=data.get("details", {}),
        )
    
    def update(
        self,
        state: FallbackState,
        reason: Optional[FallbackReason] = None,
        path_capability: Optional[PathCapability] = None,
        correlation_ids: Optional[Dict[str, str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update fallback status."""
        self.state = state
        self.entered_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.reason = reason
        self.path_capability = path_capability
        if correlation_ids:
            self.correlation_ids.update(correlation_ids)
        if details:
            self.details.update(details)


# ============================================================================
# FALLBACK AUDIT RECORD
# ============================================================================


@dataclass
class FallbackAuditRecord:
    """Audit trail record for fallback events.
    
    Tracks when fallback was triggered, why, and the context
    including correlation with existing flow/request/session/deadline IDs.
    """
    
    audit_id: str
    timestamp: str
    node_id: str
    state_before: FallbackState
    state_after: FallbackState
    reason: FallbackReason
    path_capability: PathCapability
    flow_id: Optional[str] = None
    request_id: Optional[str] = None
    handshake_id: Optional[str] = None
    deadline_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize record to dict."""
        return {
            "audit_id": self.audit_id,
            "timestamp": self.timestamp,
            "node_id": self.node_id,
            "state_before": self.state_before.value,
            "state_after": self.state_after.value,
            "reason": self.reason.value,
            "path_capability": self.path_capability.value,
            "flow_id": self.flow_id,
            "request_id": self.request_id,
            "handshake_id": self.handshake_id,
            "deadline_id": self.deadline_id,
            "details": self.details,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FallbackAuditRecord":
        """Deserialize record from dict."""
        return cls(
            audit_id=data.get("audit_id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            node_id=data.get("node_id", ""),
            state_before=FallbackState(data.get("state_before", "normal")),
            state_after=FallbackState(data.get("state_after", "normal")),
            reason=FallbackReason(data.get("reason", "unavailable")),
            path_capability=PathCapability(data.get("path_capability", "deterministic_capable")),
            flow_id=data.get("flow_id"),
            request_id=data.get("request_id"),
            handshake_id=data.get("handshake_id"),
            deadline_id=data.get("deadline_id"),
            details=data.get("details", {}),
        )


# ============================================================================
# FALLBACK PATH SELECTOR
# ============================================================================


class FallbackPathSelector:
    """Selects fallback paths when remote dependencies are unavailable.
    
    Makes decisions about which fallback path to use based on:
    - Remote availability status
    - Path capability classification (model_required vs deterministic_capable)
    - Local capabilities available
    """
    
    def __init__(self):
        """Initialize path selector."""
        self._local_paths: Dict[str, Dict[str, Any]] = {}
        self._remote_paths: Dict[str, Dict[str, Any]] = {}
    
    def register_local_path(
        self,
        path_id: str,
        capability: PathCapability,
        enabled: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a local fallback path.
        
        Args:
            path_id: Unique path identifier
            capability: Path capability classification
            enabled: Whether this path is currently enabled
            details: Additional path configuration
        """
        self._local_paths[path_id] = {
            "capability": capability.value,
            "enabled": enabled,
            "details": details or {},
        }
    
    def register_remote_path(
        self,
        path_id: str,
        capability: PathCapability,
        available: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a remote path.
        
        Args:
            path_id: Unique path identifier
            capability: Path capability classification
            available: Whether remote dependency is currently available
            details: Additional path configuration
        """
        self._remote_paths[path_id] = {
            "capability": capability.value,
            "available": available,
            "details": details or {},
        }
    
    def select_fallback_path(
        self,
        path_capability: PathCapability,
        reason: FallbackReason,
        correlation_ids: Optional[Dict[str, str]] = None,
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """Select a fallback path when remote is unavailable.
        
        Args:
            path_capability: Required path capability
            reason: Reason for fallback
            correlation_ids: Correlation context
            
        Returns:
            Tuple of (selected_path_id, path_config)
        """
        # Find compatible local paths
        compatible_paths = []
        for path_id, path_config in self._local_paths.items():
            if path_config.get("enabled", False) and path_config.get("capability") == path_capability.value:
                compatible_paths.append((path_id, path_config))
        
        if not compatible_paths:
            return None, {"error": "no_compatible_local_path", "reason": reason.value}
        
        # Select first available path
        selected_path_id, selected_config = compatible_paths[0]
        
        return selected_path_id, {
            **selected_config,
            "selected_reason": reason.value,
            "correlation_ids": correlation_ids or {},
        }
    
    def get_local_path_config(self, path_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a local fallback path."""
        return self._local_paths.get(path_id)
    
    def get_all_local_paths(self) -> List[Dict[str, Any]]:
        """Get all configured local fallback paths."""
        return [
            {"path_id": pid, **config}
            for pid, config in self._local_paths.items()
        ]


# ============================================================================
# FALLBACK MANAGER
# ============================================================================


class FallbackManager:
    """Central fallback layer orchestrating safe fallback behavior.
    
    Coordinates fallback state, path selection, and audit logging.
    """
    
    def __init__(self, emitter: Optional[TelemetryEventEmitter] = None, hooks: Optional[DiagnosticHooks] = None):
        """Initialize fallback manager.
        
        Args:
            emitter: Optional telemetry emitter for audit logging
            hooks: Optional diagnostic hooks for correlation
        """
        self._emitter = emitter
        self._hooks = hooks
        self._path_selector = FallbackPathSelector()
        self._node_statuses: Dict[str, NodeFallbackStatus] = {}
        self._audit_records: List[FallbackAuditRecord] = []
    
    # --- Node Status Management ---
    
    def get_node_status(self, node_id: str) -> Optional[NodeFallbackStatus]:
        """Get current fallback status for a node."""
        return self._node_statuses.get(node_id)
    
    def set_node_fallback(
        self,
        node_id: str,
        state: FallbackState,
        reason: FallbackReason,
        path_capability: PathCapability,
        flow_id: Optional[str] = None,
        request_id: Optional[str] = None,
        handshake_id: Optional[str] = None,
        deadline_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> NodeFallbackStatus:
        """Set node to fallback state.
        
        Args:
            node_id: Node identifier
            state: Target fallback state
            reason: Reason for fallback
            path_capability: Path capability classification
            flow_id: Correlation flow ID (optional)
            request_id: Correlation request ID (optional)
            handshake_id: Correlation handshake ID (optional)
            deadline_id: Correlation deadline ID (optional)
            details: Additional details
            
        Returns:
            Updated NodeFallbackStatus
        """
        # Get or create node status
        status = self._node_statuses.get(node_id)
        if not status:
            status = NodeFallbackStatus(node_id=node_id)
        
        # Record before state
        state_before = status.state
        
        # Update status
        status.update(
            state=state,
            reason=reason,
            path_capability=path_capability,
            correlation_ids={
                "flow_id": flow_id,
                "request_id": request_id,
                "handshake_id": handshake_id,
                "deadline_id": deadline_id,
            } if any([flow_id, request_id, handshake_id, deadline_id]) else {},
            details=details or {},
        )
        
        # Create audit record
        audit = FallbackAuditRecord(
            audit_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            node_id=node_id,
            state_before=state_before,
            state_after=state,
            reason=reason,
            path_capability=path_capability,
            flow_id=flow_id,
            request_id=request_id,
            handshake_id=handshake_id,
            deadline_id=deadline_id,
            details=details or {},
        )
        self._audit_records.append(audit)
        
        # Log to emitter if available
        if self._emitter:
            event_type = TelemetryEventType.FLOW_FAILED.value if state != FallbackState.NORMAL else TelemetryEventType.FLOW_CREATED.value
            properties = {
                "fallback_state": state.value,
                "fallback_audit_id": audit.audit_id,
            }
            if reason:
                properties["fallback_reason"] = reason.value
            self._emitter.emit_event(
                TelemetryEvent(
                    event_id=audit.audit_id,
                    event_type=event_type,
                    timestamp=datetime.now(timezone.utc),
                    flow_id=flow_id,
                    properties=properties,
                )
            )
        
        self._node_statuses[node_id] = status
        return status
    
    def clear_node_fallback(self, node_id: str) -> Optional[NodeFallbackStatus]:
        """Clear fallback state for a node, returning to NORMAL.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Updated status or None if node not found
        """
        status = self._node_statuses.get(node_id)
        if not status:
            return None
        
        return self.set_node_fallback(
            node_id=node_id,
            state=FallbackState.NORMAL,
            reason=None,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
        )
    
    # --- Audit and Diagnostic Export ---
    
    def export_audit_records(self) -> List[Dict[str, Any]]:
        """Export all audit records for diagnostics.
        
        Returns:
            List of audit record dicts
        """
        return [record.to_dict() for record in self._audit_records]
    
    def export_audit_json(self, pretty: bool = False) -> str:
        """Export audit records as JSON.
        
        Args:
            pretty: If True, format with indentation
            
        Returns:
            JSON string
        """
        data = self.export_audit_records()
        if pretty:
            return json.dumps(data, indent=2)
        return json.dumps(data)
    
    def export_by_correlation(
        self,
        correlation_id: str,
        correlation_type: str = "flow_id",
    ) -> List[Dict[str, Any]]:
        """Export audit records filtered by correlation ID.
        
        Args:
            correlation_id: Correlation ID to filter by
            correlation_type: Type of correlation (flow_id, request_id, handshake_id, deadline_id)
            
        Returns:
            List of matching audit records
        """
        return [
            record.to_dict()
            for record in self._audit_records
            if (correlation_type == "flow_id" and record.flow_id == correlation_id)
            or (correlation_type == "request_id" and record.request_id == correlation_id)
            or (correlation_type == "handshake_id" and record.handshake_id == correlation_id)
            or (correlation_type == "deadline_id" and record.deadline_id == correlation_id)
        ]
    
    # --- Path Selection ---
    
    def select_fallback_path(
        self,
        node_id: str,
        path_capability: PathCapability,
        reason: FallbackReason,
        correlation_ids: Optional[Dict[str, str]] = None,
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """Select fallback path for a node in fallback state.
        
        Args:
            node_id: Node identifier
            path_capability: Required path capability
            reason: Reason for fallback
            correlation_ids: Correlation context
            
        Returns:
            Tuple of (selected_path_id, path_config)
        """
        return self._path_selector.select_fallback_path(
            path_capability=path_capability,
            reason=reason,
            correlation_ids=correlation_ids,
        )
    
    def register_local_path(
        self,
        path_id: str,
        capability: PathCapability,
        enabled: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a local fallback path.
        
        Args:
            path_id: Unique path identifier
            capability: Path capability classification
            enabled: Whether this path is currently enabled
            details: Additional path configuration
        """
        self._path_selector.register_local_path(
            path_id=path_id,
            capability=capability,
            enabled=enabled,
            details=details,
        )
    
    def get_all_local_paths(self) -> List[Dict[str, Any]]:
        """Get all configured local fallback paths."""
        return self._path_selector.get_all_local_paths()
    
    def get_path_capability(self, path_id: str) -> Optional[PathCapability]:
        """Get path capability classification."""
        config = self._path_selector.get_local_path_config(path_id)
        if config:
            return PathCapability(config.get("capability", "deterministic_capable"))
        return None


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================


def create_fallback_manager(
    emitter: Optional[TelemetryEventEmitter] = None,
    hooks: Optional[DiagnosticHooks] = None,
) -> FallbackManager:
    """Factory function to create fallback manager.
    
    Args:
        emitter: Optional telemetry emitter for audit logging
        hooks: Optional diagnostic hooks for correlation
        
    Returns:
        FallbackManager instance
    """
    return FallbackManager(emitter=emitter, hooks=hooks)
