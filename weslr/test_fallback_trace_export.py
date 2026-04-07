"""Tests for Fallback Trace Export / Replay Integration (v74)

Comprehensive behavioral tests for fallback trace correlation, capability
visibility, recovery-safe alternative export, replay summary visibility,
and backward compatibility with v72/v73.

Test Families Implemented:
  - FallbackTraceRecord creation and serialization
  - Fallback reason correlation with flow/request/session/deadline IDs
  - Capability classification visibility (model_required vs deterministic_capable)
  - Recovery-safe alternative export and visibility
  - Replay summary fallback visibility
  - Backward compatibility with v72/v73 exports
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import MagicMock

from weslr.fallback_trace_export import (
    FallbackTraceRecord,
    FallbackTraceExporter,
    FallbackTraceReconstructor,
    create_fallback_trace_exporter,
    create_fallback_trace_reconstructor,
)
from weslr.distributed_fallback import (
    FallbackManager,
    FallbackReason,
    PathCapability,
    FallbackState,
    create_fallback_manager,
)
from weslr.distributed_diagnostic_hooks import DiagnosticHooks
from weslr.execution_telemetry import TelemetryEventEmitter


# ============================================================================
# FALLBACK TRACE RECORD TESTS
# ============================================================================


class TestFallbackTraceRecord(TestCase):
    """Tests for FallbackTraceRecord dataclass."""

    def test_record_creation(self):
        """Test creating a basic fallback trace record."""
        record = FallbackTraceRecord(
            trace_id=str(uuid.uuid4()),
            flow_id="flow-123",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            fallback_state=FallbackState.REMOTE_UNAVAILABLE,
            fallback_reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
        )
        self.assertEqual(record.flow_id, "flow-123")
        self.assertEqual(record.fallback_state, FallbackState.REMOTE_UNAVAILABLE)

    def test_record_serialization(self):
        """Test serializing record to dict."""
        record = FallbackTraceRecord(
            trace_id=str(uuid.uuid4()),
            flow_id="flow-123",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            fallback_state=FallbackState.REMOTE_UNAVAILABLE,
            fallback_reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.MODEL_REQUIRED,
        )
        data = record.to_dict()
        self.assertEqual(data["flow_id"], "flow-123")
        self.assertEqual(data["fallback_state"], "remote_unavailable")
        self.assertEqual(data["path_capability"], "model_required")

    def test_record_deserialization(self):
        """Test deserializing record from dict."""
        original = FallbackTraceRecord(
            trace_id=str(uuid.uuid4()),
            flow_id="flow-123",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            fallback_state=FallbackState.REMOTE_UNAVAILABLE,
            fallback_reason=FallbackReason.TIMEOUT,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
        )
        data = original.to_dict()
        restored = FallbackTraceRecord.from_dict(data)
        self.assertEqual(original.flow_id, restored.flow_id)
        self.assertEqual(original.fallback_state, restored.fallback_state)

    def test_record_json_roundtrip(self):
        """Test JSON serialization roundtrip."""
        record = FallbackTraceRecord(
            trace_id=str(uuid.uuid4()),
            flow_id="flow-123",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            fallback_state=FallbackState.REMOTE_UNAVAILABLE,
            fallback_reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
        )
        json_str = record.to_json()
        restored = FallbackTraceRecord.from_json(json_str)
        self.assertEqual(record.flow_id, restored.flow_id)

    def test_record_with_correlation_ids(self):
        """Test record with all correlation IDs."""
        record = FallbackTraceRecord(
            trace_id=str(uuid.uuid4()),
            flow_id="flow-123",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            request_id="req-456",
            handshake_id="hs-789",
            deadline_id="dl-012",
        )
        self.assertEqual(record.request_id, "req-456")
        self.assertEqual(record.handshake_id, "hs-789")
        self.assertEqual(record.deadline_id, "dl-012")


# ============================================================================
# FALLBACK TRACE EXPORTER TESTS
# ============================================================================


class TestFallbackTraceExporter(TestCase):
    """Tests for FallbackTraceExporter class."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.hooks = MagicMock()
        self.fallback_manager = FallbackManager(emitter=self.emitter, hooks=self.hooks)
        # Register a local path first
        self.fallback_manager.register_local_path(
            path_id="local-path-1",
            capability=PathCapability.DETERMINISTIC_CAPABLE,
            enabled=True,
        )
        self.exporter = FallbackTraceExporter(self.fallback_manager)

    def test_export_trace_no_fallback(self):
        """Test exporting trace without fallback state."""
        record = self.exporter.export_trace("flow-123")
        self.assertIsNotNone(record)
        self.assertEqual(record.fallback_state, FallbackState.NORMAL)

    def test_export_trace_with_fallback(self):
        """Test exporting trace with fallback state."""
        self.fallback_manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        record = self.exporter.export_trace("flow-123")
        self.assertEqual(record.fallback_state, FallbackState.REMOTE_UNAVAILABLE)
        self.assertEqual(record.fallback_reason, FallbackReason.UNAVAILABLE)
        self.assertEqual(record.path_capability, PathCapability.DETERMINISTIC_CAPABLE)

    def test_export_all_traces(self):
        """Test exporting all fallback traces."""
        # Add a fallback event
        self.fallback_manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        traces = self.exporter.export_all_traces()
        self.assertEqual(len(traces), 1)
        self.assertEqual(traces[0].flow_id, "flow-123")

    def test_export_as_dict(self):
        """Test exporting traces as dictionary."""
        self.fallback_manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        result = self.exporter.export_as_dict()
        self.assertIn("export_metadata", result)
        self.assertIn("traces", result)
        self.assertIn("capabilities", result)
        self.assertIn("reasons", result)

    def test_export_as_json(self):
        """Test exporting traces as JSON."""
        self.fallback_manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        json_str = self.exporter.export_as_json()
        data = json.loads(json_str)
        self.assertIn("export_metadata", data)
        self.assertIn("traces", data)

    def test_export_by_correlation_flow_id(self):
        """Test exporting traces filtered by flow_id."""
        self.fallback_manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        result = self.exporter.export_by_correlation("flow-123", "flow_id")
        self.assertEqual(len(result), 1)

    def test_export_by_correlation_no_match(self):
        """Test exporting traces filtered with no match."""
        result = self.exporter.export_by_correlation("nonexistent-flow", "flow_id")
        self.assertEqual(len(result), 0)

    def test_operator_readable_summary(self):
        """Test operator-readable summary generation."""
        self.fallback_manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        summary = self.exporter.get_operator_readable_summary()
        self.assertIn("FALLBACK TRACE SUMMARY", summary)
        self.assertIn("flow-123", summary)
        self.assertIn("remote_unavailable", summary)

    def test_export_with_model_required_capability(self):
        """Test export with model_required path capability."""
        self.fallback_manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.MODEL_REQUIRED,
            reason=FallbackReason.MODEL_UNAVAILABLE,
            path_capability=PathCapability.MODEL_REQUIRED,
            flow_id="flow-123",
        )
        
        traces = self.exporter.export_all_traces()
        self.assertEqual(traces[0].path_capability, PathCapability.MODEL_REQUIRED)
        
        result = self.exporter.export_as_dict()
        self.assertEqual(result["capabilities"]["model_required"], 1)

    def test_export_with_deterministic_capability(self):
        """Test export with deterministic_capable path capability."""
        self.fallback_manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.LOCAL_ONLY,
            reason=FallbackReason.DEADLINE_BREACHED,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        result = self.exporter.export_as_dict()
        self.assertEqual(result["capabilities"]["deterministic_capable"], 1)

    def test_export_recovery_safe_alternatives(self):
        """Test export with recovery-safe alternative paths."""
        self.fallback_manager.register_local_path(
            path_id="local-path-1",
            capability=PathCapability.DETERMINISTIC_CAPABLE,
            enabled=True,
        )
        self.fallback_manager.register_local_path(
            path_id="local-path-2",
            capability=PathCapability.MODEL_REQUIRED,
            enabled=True,
        )
        
        result = self.exporter.export_as_dict()
        self.assertIn("recovery_safe_alternatives", result)
        self.assertEqual(len(result["recovery_safe_alternatives"]), 2)


# ============================================================================
# FALLBACK TRACE RECONSTRUCTOR TESTS
# ============================================================================


class TestFallbackTraceReconstructor(TestCase):
    """Tests for FallbackTraceReconstructor class."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.hooks = MagicMock()
        self.fallback_manager = FallbackManager(emitter=self.emitter, hooks=self.hooks)
        # Register a local path first
        self.fallback_manager.register_local_path(
            path_id="local-path-1",
            capability=PathCapability.DETERMINISTIC_CAPABLE,
            enabled=True,
        )
        self.reconstructor = FallbackTraceReconstructor()
        self.reconstructor.set_fallback_manager(self.fallback_manager)

    def test_rebuild_trace_no_fallback(self):
        """Test rebuilding trace without fallback."""
        self.fallback_manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.NORMAL,
            reason=None,
            path_capability=None,
            flow_id="flow-123",
        )
        
        # Add trace to reconstructor
        exporter = FallbackTraceExporter(self.fallback_manager)
        trace_record = exporter.export_trace("flow-123")
        self.reconstructor.add_traces([trace_record])
        
        trace = self.reconstructor.rebuild_trace("flow-123")
        self.assertIsNotNone(trace)
        self.assertEqual(trace["fallback_state"], "normal")

    def test_rebuild_trace_with_fallback(self):
        """Test rebuilding trace with fallback."""
        self.fallback_manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        # Add trace to reconstructor
        exporter = FallbackTraceExporter(self.fallback_manager)
        trace_record = exporter.export_trace("flow-123")
        self.reconstructor.add_traces([trace_record])
        
        trace = self.reconstructor.rebuild_trace("flow-123")
        self.assertIsNotNone(trace)
        self.assertEqual(trace["fallback_state"], "remote_unavailable")
        self.assertEqual(trace["fallback_reason"], "unavailable")

    def test_rebuild_all_traces(self):
        """Test rebuilding all traces."""
        self.fallback_manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        self.fallback_manager.set_node_fallback(
            node_id="flow-456",
            state=FallbackState.LOCAL_ONLY,
            reason=FallbackReason.DEADLINE_BREACHED,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-456",
        )
        
        # Add traces to reconstructor
        exporter = FallbackTraceExporter(self.fallback_manager)
        traces = exporter.export_all_traces()
        self.reconstructor.add_traces(traces)
        
        rebuilt = self.reconstructor.rebuild_all_traces()
        self.assertEqual(len(rebuilt), 2)
        self.assertEqual(rebuilt[0]["flow_id"], "flow-123")
        self.assertEqual(rebuilt[1]["flow_id"], "flow-456")

    def test_get_fallback_timeline(self):
        """Test getting fallback state timeline."""
        self.fallback_manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        # Add trace to reconstructor
        exporter = FallbackTraceExporter(self.fallback_manager)
        trace_record = exporter.export_trace("flow-123")
        self.reconstructor.add_traces([trace_record])
        
        timeline = self.reconstructor.get_fallback_timeline("flow-123")
        self.assertEqual(len(timeline), 1)
        self.assertEqual(timeline[0]["state"], "remote_unavailable")

    def test_get_recovery_safe_alternatives(self):
        """Test getting recovery-safe alternative paths."""
        self.fallback_manager.register_local_path(
            path_id="local-path-1",
            capability=PathCapability.DETERMINISTIC_CAPABLE,
            enabled=True,
        )
        self.fallback_manager.register_local_path(
            path_id="local-path-2",
            capability=PathCapability.MODEL_REQUIRED,
            enabled=False,  # Disabled but still visible
        )
        
        alternatives = self.reconstructor.get_recovery_safe_alternatives()
        self.assertEqual(len(alternatives), 2)


# ============================================================================
# FACTORY FUNCTION TESTS
# ============================================================================


class TestFactoryFunctions(TestCase):
    """Tests for factory functions."""

    def test_create_fallback_trace_exporter(self):
        """Test creating fallback trace exporter via factory."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = create_fallback_trace_exporter(manager)
        
        self.assertIsNotNone(exporter)
        self.assertIsInstance(exporter, FallbackTraceExporter)

    def test_create_fallback_trace_reconstructor(self):
        """Test creating fallback trace reconstructor via factory."""
        reconstructor = create_fallback_trace_reconstructor()
        
        self.assertIsNotNone(reconstructor)
        self.assertIsInstance(reconstructor, FallbackTraceReconstructor)

    def test_create_reconstructor_with_manager(self):
        """Test creating reconstructor with fallback manager."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        reconstructor = create_fallback_trace_reconstructor(manager)
        
        self.assertIsNotNone(reconstructor._fallback_manager)


# ============================================================================
# CAPABILITY CLASSIFICATION TESTS
# ============================================================================


class TestCapabilityClassification(TestCase):
    """Tests for capability classification visibility."""

    def test_model_required_visibility(self):
        """Test model_required capability visibility in exports."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.MODEL_REQUIRED,
            reason=FallbackReason.MODEL_UNAVAILABLE,
            path_capability=PathCapability.MODEL_REQUIRED,
            flow_id="flow-123",
        )
        
        result = exporter.export_as_dict()
        
        self.assertEqual(result["capabilities"]["model_required"], 1)
        traces = result["traces"]
        self.assertEqual(traces[0]["path_capability"], "model_required")

    def test_deterministic_capable_visibility(self):
        """Test deterministic_capable capability visibility in exports."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.LOCAL_ONLY,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        result = exporter.export_as_dict()
        
        self.assertEqual(result["capabilities"]["deterministic_capable"], 1)
        traces = result["traces"]
        self.assertEqual(traces[0]["path_capability"], "deterministic_capable")


# ============================================================================
# RECOVERY SAFE ALTERNATIVE TESTS
# ============================================================================


class TestRecoverySafeAlternatives(TestCase):
    """Tests for recovery-safe alternative visibility."""

    def test_available_paths_export(self):
        """Test available paths in export."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        # Register multiple local paths
        manager.register_local_path("path-1", PathCapability.DETERMINISTIC_CAPABLE, True)
        manager.register_local_path("path-2", PathCapability.MODEL_REQUIRED, True)
        manager.register_local_path("path-3", PathCapability.DETERMINISTIC_CAPABLE, False)
        
        result = exporter.export_as_dict()
        
        self.assertIn("recovery_safe_alternatives", result)
        self.assertEqual(len(result["recovery_safe_alternatives"]), 3)

    def test_reconstructor_get_alternatives(self):
        """Test reconstructor getting alternatives."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        reconstructor = FallbackTraceReconstructor()
        reconstructor.set_fallback_manager(manager)
        
        manager.register_local_path("path-1", PathCapability.DETERMINISTIC_CAPABLE, True)
        manager.register_local_path("path-2", PathCapability.MODEL_REQUIRED, True)
        
        alternatives = reconstructor.get_recovery_safe_alternatives()
        self.assertEqual(len(alternatives), 2)


# ============================================================================
# REPLAY SUMMARY VISIBILITY TESTS
# ============================================================================


class TestReplaySummaryVisibility(TestCase):
    """Tests for replay summary fallback visibility."""

    def test_summary_shows_fallback_state(self):
        """Test that summary shows fallback state."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        summary = exporter.get_operator_readable_summary()
        
        self.assertIn("flow-123", summary)
        self.assertIn("remote_unavailable", summary)
        self.assertIn("unavailable", summary)

    def test_summary_shows_capability(self):
        """Test that summary shows path capability."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.LOCAL_ONLY,
            reason=FallbackReason.DEADLINE_BREACHED,
            path_capability=PathCapability.MODEL_REQUIRED,
            flow_id="flow-123",
        )
        
        summary = exporter.get_operator_readable_summary()
        
        self.assertIn("flow-123", summary)
        self.assertIn("model_required", summary)

    def test_summary_shows_recovery_alternatives(self):
        """Test that summary shows recovery-safe alternatives."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        # Register local paths
        manager.register_local_path("local-path-1", PathCapability.DETERMINISTIC_CAPABLE, True)
        manager.register_local_path("local-path-2", PathCapability.MODEL_REQUIRED, True)
        exporter = FallbackTraceExporter(manager)
        
        # Add a fallback trace so summary shows recovery alternatives
        manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        summary = exporter.get_operator_readable_summary()
        
        self.assertIn("RECOVERY-SAFE ALTERNATIVES", summary)
        self.assertIn("local-path-1", summary)


# ============================================================================
# BACKWARD COMPATIBILITY TESTS
# ============================================================================


class TestBackwardCompatibility(TestCase):
    """Tests for backward compatibility with v72/v73."""

    def test_v72_traces_work(self):
        """Test that v72 trace exports still work."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        # v72 trace export should not require fallback state
        record = exporter.export_trace("flow-123")
        self.assertIsNotNone(record)
        self.assertEqual(record.fallback_state, FallbackState.NORMAL)

    def test_v73_fallback_status_works(self):
        """Test that v73 fallback status is preserved."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        # v73 fallback status should be accessible
        status = manager.get_node_status("flow-123")
        self.assertIsNotNone(status)
        self.assertEqual(status.state, FallbackState.REMOTE_UNAVAILABLE)

    def test_mixed_v72_v73_traces(self):
        """Test mixing v72 and v73 trace exports."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        # v72 trace (no fallback)
        record1 = exporter.export_trace("flow-1")
        
        # v73 trace (with fallback)
        manager.set_node_fallback(
            node_id="flow-2",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-2",
        )
        record2 = exporter.export_trace("flow-2")
        
        self.assertIsNotNone(record1)
        self.assertIsNotNone(record2)
        self.assertEqual(record1.fallback_state, FallbackState.NORMAL)
        self.assertEqual(record2.fallback_state, FallbackState.REMOTE_UNAVAILABLE)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration(TestCase):
    """Integration tests combining multiple components."""

    def setUp(self):
        self.emitter = TelemetryEventEmitter()
        self.manager = FallbackManager(emitter=self.emitter)
        self.manager.register_local_path(
            path_id="local-path-1",
            capability=PathCapability.DETERMINISTIC_CAPABLE,
            enabled=True,
        )
        self.exporter = FallbackTraceExporter(self.manager)

    def test_full_export_workflow(self):
        """Test complete export workflow."""
        exporter = FallbackTraceExporter(self.manager)
        
        # Set up fallback state
        self.manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
            request_id="req-456",
        )
        
        # Export trace
        trace = exporter.export_trace("flow-123")
        self.assertIsNotNone(trace)
        
        # Export as dict
        result = exporter.export_as_dict()
        self.assertIn("export_metadata", result)
        self.assertEqual(len(result["traces"]), 1)
        
        # Export by correlation
        correlated = exporter.export_by_correlation("flow-123", "flow_id")
        self.assertEqual(len(correlated), 1)

    def test_reconstruction_workflow(self):
        """Test fallback reconstruction workflow."""
        exporter = FallbackTraceExporter(self.manager)
        reconstructor = FallbackTraceReconstructor()
        reconstructor.set_fallback_manager(self.manager)
        
        # Set up and export
        self.manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.LOCAL_ONLY,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        # Add trace to reconstructor
        trace = exporter.export_trace("flow-123")
        reconstructor.add_traces([trace])
        
        # Rebuild
        rebuilt = reconstructor.rebuild_trace("flow-123")
        self.assertIsNotNone(rebuilt)
        self.assertEqual(rebuilt["fallback_state"], "local_only")


# ============================================================================
# CORRELATION TESTS
# ============================================================================


class TestCorrelation(TestCase):
    """Tests for fallback reason correlation with IDs."""

    def test_correlation_with_flow_id(self):
        """Test correlation with flow_id."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        result = exporter.export_by_correlation("flow-123", "flow_id")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["flow_id"], "flow-123")

    def test_correlation_with_request_id(self):
        """Test correlation with request_id."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        record = exporter.export_trace(
            flow_id="flow-123",
            request_id="req-456",
        )
        self.assertEqual(record.request_id, "req-456")

    def test_correlation_with_handshake_id(self):
        """Test correlation with handshake_id."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        record = exporter.export_trace(
            flow_id="flow-123",
            handshake_id="hs-789",
        )
        self.assertEqual(record.handshake_id, "hs-789")

    def test_correlation_with_deadline_id(self):
        """Test correlation with deadline_id."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        record = exporter.export_trace(
            flow_id="flow-123",
            deadline_id="dl-012",
        )
        self.assertEqual(record.deadline_id, "dl-012")


# ============================================================================
# REASON EXPORT TESTS
# ============================================================================


class TestReasonExport(TestCase):
    """Tests for fallback reason export."""

    def test_timeout_reason(self):
        """Test timeout reason export."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.TIMEOUT,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        result = exporter.export_as_dict()
        self.assertEqual(result["reasons"]["timeout"], 1)

    def test_unavailable_reason(self):
        """Test unavailable reason export."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.UNAVAILABLE,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        result = exporter.export_as_dict()
        self.assertEqual(result["reasons"]["unavailable"], 1)

    def test_degraded_reason(self):
        """Test degraded reason export."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.DEGRADED,
            reason=FallbackReason.DEGRADED,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        result = exporter.export_as_dict()
        self.assertEqual(result["reasons"]["degraded"], 1)

    def test_handshake_failed_reason(self):
        """Test handshake_failed reason export."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.HANDSHAKE_FAILED,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        result = exporter.export_as_dict()
        self.assertEqual(result["reasons"]["handshake_failed"], 1)

    def test_deadline_breached_reason(self):
        """Test deadline_breached reason export."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.LOCAL_ONLY,
            reason=FallbackReason.DEADLINE_BREACHED,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        result = exporter.export_as_dict()
        self.assertEqual(result["reasons"]["deadline_breached"], 1)

    def test_remote_refused_reason(self):
        """Test remote_refused reason export."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.REMOTE_UNAVAILABLE,
            reason=FallbackReason.REMOTE_REFUSED,
            path_capability=PathCapability.DETERMINISTIC_CAPABLE,
            flow_id="flow-123",
        )
        
        result = exporter.export_as_dict()
        self.assertEqual(result["reasons"]["remote_refused"], 1)

    def test_model_unavailable_reason(self):
        """Test model_unavailable reason export."""
        emitter = TelemetryEventEmitter()
        manager = FallbackManager(emitter=emitter)
        exporter = FallbackTraceExporter(manager)
        
        manager.set_node_fallback(
            node_id="flow-123",
            state=FallbackState.MODEL_REQUIRED,
            reason=FallbackReason.MODEL_UNAVAILABLE,
            path_capability=PathCapability.MODEL_REQUIRED,
            flow_id="flow-123",
        )
        
        result = exporter.export_as_dict()
        self.assertEqual(result["reasons"]["model_unavailable"], 1)


# ============================================================================
# MAIN EXECUTION
# ============================================================================


if __name__ == "__main__":
    import unittest
    unittest.main()
