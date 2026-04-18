"""Tests for Distributed Fallback Behavior (v73)

Comprehensive behavioral tests for fallback state management, path selection,
audit logging, and correlation with existing flow/request/session/deadline IDs.

Test Families Implemented:
  - FallbackReason enum validation
  - PathCapability classification
  - NodeFallbackStatus creation and state transitions
  - FallbackAuditRecord generation and export
  - FallbackPathSelector path selection logic
  - FallbackManager node fallback orchestration
  - Correlation with flow/request/session/deadline IDs
  - Audit record filtering by correlation ID
  - Path registration and capability classification
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import MagicMock

from weslr.distributed_fallback import (
    FallbackReason,
    PathCapability,
    FallbackState,
    NodeFallbackStatus,
    FallbackAuditRecord,
    FallbackPathSelector,
    FallbackManager,
    create_fallback_manager,
)
from weslr.execution_telemetry import (
    TelemetryEventEmitter,
    TelemetryEvent,
    TelemetryEventType,
)


# ============================================================================
# FALLBACK REASON ENUM TESTS
# ============================================================================


class TestFallbackReason(TestCase):
    """Tests for FallbackReason enum."""

    def test_all_reasons_defined(self):
        """Test all expected reasons are defined."""
        expected_reasons = [
            "timeout",
            "unavailable",
            "degraded",
            "handshake_failed",
            "deadline_breached",
            "remote_refused",
            "model_unavailable",
        ]
        actual_reasons = [r.value for r in FallbackReason]
        self.assertEqual(actual_reasons, expected_reasons)

    def test_reason_values(self):
        """Test reason string values."""
        self.assertEqual(FallbackReason.TIMEOUT.value, "timeout")
        self.assertEqual(FallbackReason.UNAVAILABLE.value, "unavailable")
        self.assertEqual(FallbackReason.DEGRADED.value, "degraded")
        self.assertEqual(FallbackReason.HANDSHAKE_FAILED.value, "handshake_failed")
        self.assertEqual(FallbackReason.DEADLINE_BREACHED.value, "deadline_breached")
        self.assertEqual(FallbackReason.REMOTE_REFUSED.value, "remote_refused")
        self.assertEqual(FallbackReason.MODEL_UNAVAILABLE.value, "model_unavailable")


# ============================================================================
# PATH CAPABILITY ENUM TESTS
# ============================================================================


class TestPathCapability(TestCase):
    """Tests for PathCapability enum."""

    def test_all_capabilities_defined(self):
        """Test all expected capabilities are defined."""
        expected_capabilities = [
            "model_required",
            "deterministic_capable",
        ]
        actual_capabilities = [c.value for c in PathCapability]
        self.assertEqual(actual_capabilities, expected_capabilities)

    def test_capability_values(self):
        """Test capability string values."""
        self.assertEqual(PathCapability.MODEL_REQUIRED.value, "model_required")
        self.assertEqual(PathCapability.DETERMINISTIC_CAPABLE.value, "deterministic_capable")


# ============================================================================
# FALLBACK STATE ENUM TESTS
# ============================================================================


class TestFallbackState(TestCase):
    """Tests for FallbackState enum."""

    def test_all_states_defined(self):
        """Test all expected states are defined."""
        expected_states = [
            "normal",
            "degraded",
            "remote_unavailable",
            "local_only",
            "model_required",
            "deterministic_only",
        ]
        actual_states = [s.value for s in FallbackState]
        self.assertEqual(actual_states, expected_states)


# ============================================================================
# NODE FALLBACK STATUS TESTS
# ============================================================================


class TestNodeFallbackStatus(TestCase):
    """Tests for NodeFallbackStatus dataclass."""

    def test_status_creation(self):
        """Test creating a basic fallback status."""
        status = NodeFallbackStatus(
            node_id="node-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
        )
        self.assertEqual(status.node_id, "node-123")
        self.assertEqual(status.state, FallbackState.REMOTE_UNAVAILABLE)

    def test_status_to_dict(self):
        """Test serializing status to dict."""
        status = NodeFallbackStatus(
            node_id="node-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
        )
        data = status.to_dict()
        self.assertEqual(data["node_id"], "node-123")
        self.assertEqual(data["state"], "remote_unavailable")
        self.assertEqual(data["reason"], "unavailable")

    def test_status_from_dict(self):
        """Test deserializing status from dict."""
        original = NodeFallbackStatus(
            node_id="node-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
        )
        data = original.to_dict()
        restored = NodeFallbackStatus.from_dict(data)
        self.assertEqual(original.node_id, restored.node_id)
        self.assertEqual(original.state, restored.state)

    def test_status_update(self):
        """Test updating fallback status."""
        status = NodeFallbackStatus(node_id="node-123", state=FallbackState.NORMAL)
        status.update(
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.MODEL_REQUIRED,
        )
        self.assertEqual(status.state, FallbackState.REMOTE_UNAVAILABLE)
        self.assertEqual(status.reason, FallbackReason.UNAVAILABLE)

    def test_status_with_correlation_ids(self):
        """Test status with correlation IDs."""
        status = NodeFallbackStatus(
            node_id="node-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            correlation_ids={
                "flow_id": "flow-456",
                "request_id": "req-789",
            },
        )
        self.assertEqual(status.correlation_ids["flow_id"], "flow-456")
        self.assertEqual(status.correlation_ids["request_id"], "req-789")


# ============================================================================
# FALLBACK AUDIT RECORD TESTS
# ============================================================================


class TestFallbackAuditRecord(TestCase):
    """Tests for FallbackAuditRecord dataclass."""

    def test_record_creation(self):
        """Test creating an audit record."""
        record = FallbackAuditRecord(
            audit_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            node_id="node-123",
            state_before=FallbackState.NORMAL,
            state_after=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-456",
        )
        self.assertEqual(record.node_id, "node-123")
        self.assertEqual(record.flow_id, "flow-456")

    def test_record_to_dict(self):
        """Test serializing record to dict."""
        record = FallbackAuditRecord(
            audit_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            node_id="node-123",
            state_before=FallbackState.NORMAL,
            state_after=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-456",
        )
        data = record.to_dict()
        self.assertEqual(data["node_id"], "node-123")
        self.assertEqual(data["flow_id"], "flow-456")
        self.assertEqual(data["reason"], "unavailable")

    def test_record_from_dict(self):
        """Test deserializing record from dict."""
        original = FallbackAuditRecord(
            audit_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            node_id="node-123",
            state_before=FallbackState.NORMAL,
            state_after=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
        )
        data = original.to_dict()
        restored = FallbackAuditRecord.from_dict(data)
        self.assertEqual(original.audit_id, restored.audit_id)
        self.assertEqual(original.state_before, restored.state_before)


# ============================================================================
# FALLBACK PATH SELECTOR TESTS
# ============================================================================


class TestFallbackPathSelector(TestCase):
    """Tests for FallbackPathSelector class."""

    def test_selector_creation(self):
        """Test creating path selector."""
        selector = FallbackPathSelector()
        self.assertIsNotNone(selector)

    def test_register_local_path(self):
        """Test registering a local fallback path."""
        selector = FallbackPathSelector()
        selector.register_local_path(
            path_id="local-path-1",
            capability=PathCapability.DETERMINISTIC_CAPABLE,
            enabled=True,
        )
        paths = selector.get_all_local_paths()
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0]["path_id"], "local-path-1")

    def test_register_remote_path(self):
        """Test registering a remote path."""
        selector = FallbackPathSelector()
        selector.register_remote_path(
            path_id="remote-path-1",
            capability=PathCapability.DETERMINISTIC_CAPABLE,
            available=False,
        )

    def test_select_fallback_path(self):
        """Test selecting a fallback path."""
        selector = FallbackPathSelector()
        selector.register_local_path(
            path_id="local-path-1",
            capability=PathCapability.DETERMINISTIC_CAPABLE,
            enabled=True,
        )
        selector.register_local_path(
            path_id="local-path-2",
            capability=PathCapability.MODEL_REQUIRED,
            enabled=True,
        )

        # Select deterministic-capable path
        selected_id, config = selector.select_fallback_path(
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            reason=FallbackReason.UNAVAILABLE,
        )
        self.assertEqual(selected_id, "local-path-1")
        self.assertEqual(config["correlation_ids"], {})

    def test_select_fallback_path_no_compatible(self):
        """Test selecting fallback path with no compatible options."""
        selector = FallbackPathSelector()
        selector.register_local_path(
            path_id="local-path-1",
            capability=PathCapability.DETERMINISTIC_CAPABLE,
            enabled=False,  # Disabled
        )

        selected_id, config = selector.select_fallback_path(
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            reason=FallbackReason.UNAVAILABLE,
        )
        self.assertIsNone(selected_id)
        self.assertIn("error", config)

    def test_select_fallback_path_with_correlation(self):
        """Test selecting fallback path with correlation IDs."""
        selector = FallbackPathSelector()
        selector.register_local_path(
            path_id="local-path-1",
            capability=PathCapability.DETERMINISTIC_CAPABLE,
            enabled=True,
        )

        selected_id, config = selector.select_fallback_path(
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            reason=FallbackReason.UNAVAILABLE,
            correlation_ids={"flow_id": "flow-123", "request_id": "req-456"},
        )
        self.assertEqual(config["correlation_ids"]["flow_id"], "flow-123")
        self.assertEqual(config["correlation_ids"]["request_id"], "req-456")


# ============================================================================
# FALLBACK MANAGER TESTS
# ============================================================================


class TestFallbackManager(TestCase):
    """Tests for FallbackManager class."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.hooks = MagicMock()
        self.manager = FallbackManager(emitter=self.emitter, hooks=self.hooks)

    def test_manager_creation(self):
        """Test creating fallback manager."""
        self.assertIsNotNone(self.manager)
        self.assertIsNotNone(self.manager._path_selector)

    def test_set_node_fallback(self):
        """Test setting node to fallback state."""
        status = self.manager.set_node_fallback(
            node_id="node-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-456",
        )
        self.assertEqual(status.node_id, "node-123")
        self.assertEqual(status.state, FallbackState.REMOTE_UNAVAILABLE)

    def test_set_node_fallback_with_all_correlations(self):
        """Test setting node fallback with all correlation IDs."""
        status = self.manager.set_node_fallback(
            node_id="node-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.TIMEOUT,
            path_capability=PathCapability.MODEL_REQUIRED,
            flow_id="flow-456",
            request_id="req-789",
            handshake_id="hs-012",
            deadline_id="dl-345",
        )
        self.assertEqual(status.correlation_ids["flow_id"], "flow-456")
        self.assertEqual(status.correlation_ids["request_id"], "req-789")
        self.assertEqual(status.correlation_ids["handshake_id"], "hs-012")
        self.assertEqual(status.correlation_ids["deadline_id"], "dl-345")

    def test_clear_node_fallback(self):
        """Test clearing node fallback state."""
        status = self.manager.set_node_fallback(
            node_id="node-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
        )
        cleared = self.manager.clear_node_fallback("node-123")
        self.assertEqual(cleared.state, FallbackState.NORMAL)

    def test_clear_node_fallback_not_found(self):
        """Test clearing fallback state for unknown node."""
        result = self.manager.clear_node_fallback("unknown-node")
        self.assertIsNone(result)

    def test_export_audit_records(self):
        """Test exporting audit records."""
        self.manager.set_node_fallback(
            node_id="node-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-456",
        )
        records = self.manager.export_audit_records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["node_id"], "node-123")
        self.assertEqual(records[0]["flow_id"], "flow-456")

    def test_export_audit_json(self):
        """Test exporting audit records as JSON."""
        self.manager.set_node_fallback(
            node_id="node-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
        )
        json_str = self.manager.export_audit_json(pretty=False)
        data = json.loads(json_str)
        self.assertEqual(len(data), 1)

    def test_export_by_correlation_flow_id(self):
        """Test exporting audits filtered by flow_id."""
        self.manager.set_node_fallback(
            node_id="node-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-456",
        )
        records = self.manager.export_by_correlation("flow-456", "flow_id")
        self.assertEqual(len(records), 1)

    def test_export_by_correlation_no_match(self):
        """Test exporting audits filtered with no match."""
        records = self.manager.export_by_correlation("nonexistent-flow", "flow_id")
        self.assertEqual(len(records), 0)

    def test_register_local_path(self):
        """Test registering local fallback path."""
        self.manager.register_local_path(
            path_id="local-path-1",
            capability=PathCapability.DETERMINISTIC_CAPABLE,
            enabled=True,
        )
        paths = self.manager.get_all_local_paths()
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0]["path_id"], "local-path-1")

    def test_select_fallback_path(self):
        """Test selecting fallback path via manager."""
        self.manager.register_local_path(
            path_id="local-path-1",
            capability=PathCapability.DETERMINISTIC_CAPABLE,
            enabled=True,
        )
        selected_id, config = self.manager.select_fallback_path(
            node_id="node-123",
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            reason=FallbackReason.UNAVAILABLE,
        )
        self.assertEqual(selected_id, "local-path-1")

    def test_get_path_capability(self):
        """Test getting path capability."""
        self.manager.register_local_path(
            path_id="local-path-1",
            capability=PathCapability.MODEL_REQUIRED,
            enabled=True,
        )
        capability = self.manager.get_path_capability("local-path-1")
        self.assertEqual(capability, PathCapability.MODEL_REQUIRED)

    def test_get_node_status(self):
        """Test getting node status."""
        status = self.manager.set_node_fallback(
            node_id="node-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
        )
        retrieved = self.manager.get_node_status("node-123")
        self.assertEqual(retrieved.state, FallbackState.REMOTE_UNAVAILABLE)


# ============================================================================
# FACTORY FUNCTION TESTS
# ============================================================================


class TestFactoryFunctions(TestCase):
    """Tests for factory functions."""

    def test_create_fallback_manager(self):
        """Test creating fallback manager via factory."""
        emitter = TelemetryEventEmitter()
        hooks = MagicMock()
        manager = create_fallback_manager(emitter=emitter, hooks=hooks)
        self.assertIsNotNone(manager)
        self.assertIsInstance(manager, FallbackManager)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration(TestCase):
    """Integration tests combining multiple components."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.manager = FallbackManager(emitter=self.emitter)

    def test_full_fallback_workflow(self):
        """Test complete fallback workflow."""
        # Set fallback state
        status = self.manager.set_node_fallback(
            node_id="node-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-456",
            request_id="req-789",
        )
        self.assertEqual(status.state, FallbackState.REMOTE_UNAVAILABLE)

        # Export audit
        records = self.manager.export_audit_records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["flow_id"], "flow-456")

        # Select fallback path
        self.manager.register_local_path(
            path_id="local-path-1",
            capability=PathCapability.DETERMINISTIC_CAPABLE,
            enabled=True,
        )
        selected_id, config = self.manager.select_fallback_path(
            node_id="node-123",
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            reason=FallbackReason.UNAVAILABLE,
            correlation_ids={"flow_id": "flow-456"},
        )
        self.assertEqual(selected_id, "local-path-1")
        self.assertEqual(config["correlation_ids"]["flow_id"], "flow-456")

    def test_correlation_filtering_workflow(self):
        """Test correlation filtering across multiple audits."""
        # Create multiple audits with different correlation IDs
        self.manager.set_node_fallback(
            node_id="node-1",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-1",
        )
        self.manager.set_node_fallback(
            node_id="node-2",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.TIMEOUT,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-2",
        )

        # Filter by flow_id
        flow1_audits = self.manager.export_by_correlation("flow-1", "flow_id")
        flow2_audits = self.manager.export_by_correlation("flow-2", "flow_id")
        unrelated_audits = self.manager.export_by_correlation("flow-999", "flow_id")

        self.assertEqual(len(flow1_audits), 1)
        self.assertEqual(len(flow2_audits), 1)
        self.assertEqual(len(unrelated_audits), 0)


# ============================================================================
# CORRELATION VALIDATION TESTS
# ============================================================================


class TestCorrelationValidation(TestCase):
    """Tests for correlation validation in fallback behavior."""

    def test_all_correlation_types(self):
        """Test all correlation ID types are tracked."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)

        status = manager.set_node_fallback(
            node_id="node-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.DEADLINE_BREACHED,
            path_capability=PathCapability.MODEL_REQUIRED,
            flow_id="flow-123",
            request_id="req-456",
            handshake_id="hs-789",
            deadline_id="dl-012",
        )

        self.assertEqual(status.correlation_ids["flow_id"], "flow-123")
        self.assertEqual(status.correlation_ids["request_id"], "req-456")
        self.assertEqual(status.correlation_ids["handshake_id"], "hs-789")
        self.assertEqual(status.correlation_ids["deadline_id"], "dl-012")

    def test_audit_records_preserve_correlations(self):
        """Test audit records preserve correlation IDs."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)

        manager.set_node_fallback(
            node_id="node-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.HANDSHAKE_FAILED,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-456",
            request_id="req-789",
            handshake_id="hs-012",
        )

        records = manager.export_audit_records()
        self.assertEqual(records[0]["flow_id"], "flow-456")
        self.assertEqual(records[0]["request_id"], "req-789")
        self.assertEqual(records[0]["handshake_id"], "hs-012")


# ============================================================================
# REASON PATH CAPABILITY SEPARATION TESTS
# ============================================================================


class TestReasonPathCapabilitySeparation(TestCase):
    """Tests for separation of reasons from path capability classification."""

    def test_reason_independent_from_capability(self):
        """Test that reason and path capability are independent."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)

        # Same reason, different capabilities
        status1 = manager.set_node_fallback(
            node_id="node-1",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
        )
        status2 = manager.set_node_fallback(
            node_id="node-2",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.MODEL_REQUIRED,
        )

        self.assertEqual(status1.reason, FallbackReason.UNAVAILABLE)
        self.assertEqual(status2.reason, FallbackReason.UNAVAILABLE)
        self.assertEqual(status1.path_capability, PathCapability.DETERMINISTIC_CAPABLE)
        self.assertEqual(status2.path_capability, PathCapability.MODEL_REQUIRED)

    def test_capability_independent_from_reason(self):
        """Test that path capability is independent from reason."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)

        # Same capability, different reasons
        status1 = manager.set_node_fallback(
            node_id="node-1",
            state=FallbackState.LOCAL_ONLY,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
        )
        status2 = manager.set_node_fallback(
            node_id="node-2",
            state=FallbackState.LOCAL_ONLY,
            reason=FallbackReason.MODEL_UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
        )

        self.assertEqual(status1.path_capability, PathCapability.DETERMINISTIC_CAPABLE)
        self.assertEqual(status2.path_capability, PathCapability.DETERMINISTIC_CAPABLE)
        self.assertEqual(status1.reason, FallbackReason.UNAVAILABLE)
        self.assertEqual(status2.reason, FallbackReason.MODEL_UNAVAILABLE)


# ============================================================================
# STATE TRANSITION TESTS
# ============================================================================


class TestStateTransitions(TestCase):
    """Tests for fallback state transitions."""

    def test_normal_to_remote_unavailable(self):
        """Test transition from NORMAL to REMOTE_UNAVAILABLE."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)

        status = manager.set_node_fallback(
            node_id="node-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
        )
        self.assertEqual(status.state, FallbackState.REMOTE_UNAVAILABLE)

    def test_remote_unavailable_to_normal(self):
        """Test transition from REMOTE_UNAVAILABLE to NORMAL."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)

        manager.set_node_fallback(
            node_id="node-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
        )
        cleared = manager.clear_node_fallback("node-123")
        self.assertEqual(cleared.state, FallbackState.NORMAL)

    def test_normal_to_local_only(self):
        """Test transition from NORMAL to LOCAL_ONLY."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)

        status = manager.set_node_fallback(
            node_id="node-123",
            state=FallbackState.LOCAL_ONLY,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
        )
        self.assertEqual(status.state, FallbackState.LOCAL_ONLY)

    def test_model_required_fallback(self):
        """Test MODEL_REQUIRED fallback state."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)

        status = manager.set_node_fallback(
            node_id="node-123",
            state=FallbackState.MODEL_REQUIRED,
            reason=FallbackReason.MODEL_UNAVAILABLE,
            path_capability=PathCapability.MODEL_REQUIRED,
        )
        self.assertEqual(status.state, FallbackState.MODEL_REQUIRED)
        self.assertEqual(status.reason, FallbackReason.MODEL_UNAVAILABLE)


# ============================================================================
# DETAIL TRACKING TESTS
# ============================================================================


class TestDetailTracking(TestCase):
    """Tests for detail tracking in fallback behavior."""

    def test_status_details(self):
        """Test status with detailed information."""
        status = NodeFallbackStatus(
            node_id="node-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            details={
                "error": "Connection refused",
                "timeout_ms": 5000,
                "retry_count": 3,
            },
        )
        self.assertEqual(status.details["error"], "Connection refused")

    def test_audit_record_details(self):
        """Test audit record with details."""
        record = FallbackAuditRecord(
            audit_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            node_id="node-123",
            state_before=FallbackState.NORMAL,
            state_after=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            details={"error": "Connection refused", "host": "remote-node-1"},
        )
        data = record.to_dict()
        self.assertEqual(data["details"]["error"], "Connection refused")
        self.assertEqual(data["details"]["host"], "remote-node-1")


# ============================================================================
# MAIN EXECUTION
# ============================================================================


if __name__ == "__main__":
    import unittest
    unittest.main()
