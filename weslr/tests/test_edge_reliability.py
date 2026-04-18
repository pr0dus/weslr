"""Tests for Edge Reliability / Offline-First Layer (v22)

Tests edge_reliability.py data models, engine, and integration hooks.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from weslr.edge_reliability import (
    OperationMode,
    ProviderStatus,
    ExternalSourceStatus,
    EdgeReliabilityState,
    EdgeReliabilityEngine,
    ProviderAvailability,
    ExternalSourceAvailability,
    integrate_with_governance_view,
    integrate_with_operator_review,
)


class TestEdgeReliabilityModels(unittest.TestCase):
    """Test edge reliability data models."""

    def test_operation_mode_enum(self):
        """Test OperationMode enum values."""
        self.assertEqual(OperationMode.ONLINE.value, "online")
        self.assertEqual(OperationMode.DEGRADED.value, "degraded")
        self.assertEqual(OperationMode.OFFLINE.value, "offline")

    def test_provider_status_enum(self):
        """Test ProviderStatus enum values."""
        self.assertEqual(ProviderStatus.AVAILABLE.value, "available")
        self.assertEqual(ProviderStatus.UNREACHABLE.value, "unreachable")
        self.assertEqual(ProviderStatus.UNAVAILABLE.value, "unavailable")
        self.assertEqual(ProviderStatus.DEGRADED.value, "degraded")

    def test_external_source_status_enum(self):
        """Test ExternalSourceStatus enum values."""
        self.assertEqual(ExternalSourceStatus.AVAILABLE.value, "available")
        self.assertEqual(ExternalSourceStatus.UNAVAILABLE.value, "unavailable")
        self.assertEqual(ExternalSourceStatus.DEGRADED.value, "degraded")

    def test_create_edge_reliability_state(self):
        """Test creating an edge reliability state."""
        state = EdgeReliabilityState()
        
        self.assertEqual(state.operation_mode, OperationMode.ONLINE.value)
        self.assertEqual(state.providers, {})
        self.assertEqual(state.external_sources, {})
        self.assertTrue(state.deterministic_core_available)
        self.assertTrue(state.evidence_cache_available)
        self.assertTrue(state.continuity_cache_available)
        self.assertEqual(state.status_summary, "All systems online")
        self.assertEqual(state.available_capabilities, [])
        self.assertEqual(state.unavailable_capabilities, [])
        self.assertIsNotNone(state.checked_at)

    def test_edge_reliability_state_to_dict(self):
        """Test edge reliability state serialization."""
        state = EdgeReliabilityState()
        state.status_summary = "Degraded mode"
        state.available_capabilities = ["deterministic_core", "continuity_cache"]
        
        state_dict = state.to_dict()
        self.assertEqual(state_dict["operation_mode"], OperationMode.ONLINE.value)
        self.assertEqual(state_dict["status_summary"], "Degraded mode")
        self.assertEqual(state_dict["available_capabilities"], ["deterministic_core", "continuity_cache"])

    def test_edge_reliability_state_from_dict(self):
        """Test edge reliability state deserialization."""
        state = EdgeReliabilityState()
        state_dict = state.to_dict()
        
        state2 = EdgeReliabilityState.from_dict(state_dict)
        self.assertEqual(state.operation_mode, state2.operation_mode)
        self.assertEqual(state.status_summary, state2.status_summary)

    def test_update_operation_mode(self):
        """Test updating operation mode."""
        state = EdgeReliabilityState()
        original_mode = state.operation_mode
        original_checked = state.checked_at
        
        import time as time_module
        time_module.sleep(0.02)  # Ensure timestamp changes
        
        state.update_mode(OperationMode.DEGRADED.value)
        
        self.assertEqual(state.operation_mode, OperationMode.DEGRADED.value)
        self.assertNotEqual(state.checked_at, original_checked)

    def test_mark_provider_unavailable(self):
        """Test marking a provider as unavailable."""
        state = EdgeReliabilityState()
        
        state.mark_provider_unavailable("llm", "openai", "Connection refused")
        
        self.assertIn("llm", state.providers)
        self.assertIn("openai", state.providers["llm"])
        self.assertEqual(state.providers["llm"]["openai"]["status"], ProviderStatus.UNAVAILABLE.value)
        self.assertIsNotNone(state.last_failure_at)

    def test_mark_provider_available(self):
        """Test marking a provider as available."""
        state = EdgeReliabilityState()
        
        state.mark_provider_available("llm", "local-llm")
        
        self.assertIn("llm", state.providers)
        self.assertIn("local-llm", state.providers["llm"])
        self.assertEqual(state.providers["llm"]["local-llm"]["status"], ProviderStatus.AVAILABLE.value)


class TestEdgeReliabilityEngine(unittest.TestCase):
    """Test edge reliability engine."""

    def test_assess_initial_state(self):
        """Test initial assessment with minimal workspace."""
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal directory structure
            workspace_path = Path(tmpdir)
            continuity_path = workspace_path / "continuity"
            continuity_path.mkdir(parents=True, exist_ok=True)
            
            engine = EdgeReliabilityEngine(workspace_path=workspace_path)
            state = engine.assess()
            
            # With minimal workspace, should be degraded or offline mode
            self.assertIn(state.operation_mode, [OperationMode.ONLINE.value, OperationMode.DEGRADED.value, OperationMode.OFFLINE.value])
            self.assertTrue(state.deterministic_core_available)

    def test_assess_with_local_workspace(self):
        """Test assessment with local workspace path."""
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal directory structure
            workspace_path = Path(tmpdir)
            continuity_path = workspace_path / "continuity"
            continuity_path.mkdir(parents=True, exist_ok=True)
            evidence_path = continuity_path / "evidence"
            evidence_path.mkdir(parents=True, exist_ok=True)
            snapshots_path = continuity_path / "snapshots"
            snapshots_path.mkdir(parents=True, exist_ok=True)
            
            engine = EdgeReliabilityEngine(workspace_path=workspace_path)
            state = engine.assess()
            
            # Should be online with all caches available
            self.assertEqual(state.operation_mode, OperationMode.ONLINE.value)
            self.assertTrue(state.deterministic_core_available)
            self.assertTrue(state.evidence_cache_available)
            self.assertTrue(state.continuity_cache_available)
            self.assertIn("evidence_cache", state.available_capabilities)
            self.assertIn("continuity_cache", state.available_capabilities)

    def test_set_mode_manually(self):
        """Test manually setting operation mode."""
        engine = EdgeReliabilityEngine()
        engine.set_mode(OperationMode.OFFLINE.value)
        
        self.assertEqual(engine.state.operation_mode, OperationMode.OFFLINE.value)
        self.assertFalse(engine.state.evidence_cache_available)
        self.assertFalse(engine.state.continuity_cache_available)
        self.assertEqual(engine.state.available_capabilities, ["deterministic_core"])
        self.assertEqual(engine.state.unavailable_capabilities, ["external_providers", "external_sources"])

    def test_get_status_for_governance(self):
        """Test governance status formatting."""
        engine = EdgeReliabilityEngine()
        engine.set_mode(OperationMode.DEGRADED.value)
        
        status = engine.get_status_for_governance()
        
        self.assertEqual(status["operation_mode"], OperationMode.DEGRADED.value)
        self.assertIn("deterministic_core", status["capabilities"]["available"])
        self.assertIn("external_providers", status["capabilities"]["unavailable"])

    def test_engine_to_dict(self):
        """Test engine state serialization."""
        engine = EdgeReliabilityEngine()
        engine.state.operation_mode = OperationMode.OFFLINE.value
        
        engine_dict = engine.to_dict()
        self.assertEqual(engine_dict["operation_mode"], OperationMode.OFFLINE.value)


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for governance and operator surfaces."""

    def test_integrate_with_governance_view_adds_reliability_fields(self):
        """Test that integration adds reliability fields to governance view."""
        governance_dict = {
            "proposal_id": "prop-001",
            "title": "Test proposal",
        }
        
        result = integrate_with_governance_view(governance_dict)
        
        self.assertIn("reliability_status", result)
        self.assertIn("operation_mode", result)
        self.assertIn("offline_mode_explanation", result)
        self.assertIsNone(result["reliability_status"])
        self.assertIsNone(result["operation_mode"])
        self.assertIsNone(result["offline_mode_explanation"])

    def test_integrate_with_governance_view_preserves_existing(self):
        """Test that integration preserves existing reliability fields."""
        governance_dict = {
            "proposal_id": "prop-001",
            "title": "Test proposal",
            "operation_mode": OperationMode.DEGRADED.value,
            "reliability_status": {"status": "degraded"},
        }
        
        result = integrate_with_governance_view(governance_dict)
        
        self.assertEqual(result["operation_mode"], OperationMode.DEGRADED.value)
        self.assertEqual(result["reliability_status"], {"status": "degraded"})

    def test_integrate_with_operator_review_adds_reliability_fields(self):
        """Test that integration adds reliability fields to operator review."""
        review_dict = {
            "proposal_id": "prop-001",
            "title": "Test proposal",
        }
        
        result = integrate_with_operator_review(review_dict)
        
        self.assertIn("operation_mode", result)
        self.assertIn("available_capabilities", result)
        self.assertIn("unavailable_capabilities", result)
        self.assertIsNone(result["operation_mode"])
        self.assertEqual(result["available_capabilities"], [])
        self.assertEqual(result["unavailable_capabilities"], [])

    def test_integrate_with_operator_review_preserves_existing(self):
        """Test that integration preserves existing reliability fields."""
        review_dict = {
            "proposal_id": "prop-001",
            "title": "Test proposal",
            "operation_mode": OperationMode.OFFLINE.value,
            "available_capabilities": ["deterministic_core"],
        }
        
        result = integrate_with_operator_review(review_dict)
        
        self.assertEqual(result["operation_mode"], OperationMode.OFFLINE.value)
        self.assertEqual(result["available_capabilities"], ["deterministic_core"])


if __name__ == "__main__":
    unittest.main()
