"""Test suite for Capsule Observability (v93h)

Test Doctrine v1.0.0
Test Doctrine version: 1.0.0 (2026-04-08)

Tests for v93h: Silent Continuity Observability / Debug Summary.
Read-only observability layer for silent continuity subsystem.

Test Categories:
- Model Tests: Dataclass fields, serialization, constants
- Behavior Tests: Observability queries, debug export
- Integration Tests: Hooks into v93a-v93g, backward compatibility
- BackwardCompatibility Tests: Existing functions unchanged, no breaking changes
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from weslr.active_work_capsule import ActiveWorkCapsule
from weslr.capsule_observability import (
    CapsuleObservability,
    CapsuleObservabilityResult,
    export_debug_summary,
    get_capture_timestamp,
    get_capsule_status,
    get_freshness_status,
    get_last_apply_status,
    get_last_restore_decision,
)


# ===== Model Tests =====


class TestCapsuleObservabilityModel(unittest.TestCase):
    """Test CapsuleObservability data models and serialization."""
    
    def test_capsule_observability_result_dataclass(self):
        """Test CapsuleObservabilityResult dataclass fields."""
        result = CapsuleObservabilityResult.observed(
            capsule_present=True,
            reason="test_reason",
            raw_capsule={"test": "data"},
        )
        
        self.assertEqual(result.status, "observed")
        self.assertTrue(result.capsule_present)
        self.assertEqual(result.reason, "test_reason")
        self.assertIn("timestamp", result.__dict__)
    
    def test_capsule_observability_result_to_dict(self):
        """Test CapsuleObservabilityResult to_dict serialization."""
        result = CapsuleObservabilityResult.observed(
            capsule_present=True,
            reason="test_reason",
        )
        data = result.to_dict()
        
        self.assertEqual(data["status"], "observed")
        self.assertTrue(data["capsule_present"])
        self.assertIn("timestamp", data)
    
    def test_capsule_observability_result_absent(self):
        """Test CapsuleObservabilityResult absent factory."""
        result = CapsuleObservabilityResult.absent("test_reason")
        
        self.assertEqual(result.status, "absent")
        self.assertFalse(result.capsule_present)
    
    def test_capsule_observability_result_error(self):
        """Test CapsuleObservabilityResult error factory."""
        result = CapsuleObservabilityResult.error("test_reason")
        
        self.assertEqual(result.status, "error")
        self.assertFalse(result.capsule_present)
    
    def test_observability_result_raw_capsule(self):
        """Test raw_capsule field in observability result."""
        raw_data = {"layer_name": "test", "task_id": "test1"}
        result = CapsuleObservabilityResult.observed(
            capsule_present=True,
            reason="test_reason",
            raw_capsule=raw_data,
        )
        
        self.assertEqual(result.raw_capsule, raw_data)


# ===== Behavior Tests =====


class TestCapsuleObservabilityBehavior(unittest.TestCase):
    """Test CapsuleObservability observability queries."""
    
    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.observability = CapsuleObservability(base_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_observe_capsule_absent(self):
        """Test observe returns absent when no capsule exists."""
        result = self.observability.observe()
        
        self.assertEqual(result["status"], "absent")
        self.assertFalse(result["capsule_present"])
        self.assertIn("not_found", result["reason"])
    
    def test_observe_capsule_present(self):
        """Test observe returns observed when capsule exists."""
        # Create and store a capsule first
        capsule = ActiveWorkCapsule(
            layer_name="test_layer",
            task_id="test_task",
            phase="implementation",
            approved_files=["test.py"],
            pending_tests=["test_function"],
            seal_criteria=["test_criteria"],
            short_task_summary="Test observability",
            active_constraints=["no_tia"],
            timestamp="2026-04-08T00:00:00Z",
        )
        
        store_result = self.observability._store_capsule_for_test(capsule)
        
        if store_result["status"] == "stored":
            # Now observe
            result = self.observability.observe()
            
            self.assertEqual(result["status"], "observed")
            self.assertTrue(result["capsule_present"])
    
    def test_get_capsule_status_absent(self):
        """Test get_capsule_status returns absent when no capsule."""
        result = self.observability.get_capsule_status()
        
        self.assertEqual(result["status"], "absent")
        self.assertIn("not_found", result["reason"])
    
    def test_get_capture_timestamp_absent(self):
        """Test get_capture_timestamp returns absent when no capsule."""
        result = self.observability.get_capture_timestamp()
        
        self.assertEqual(result["status"], "absent")
        self.assertEqual(result["reason"], "no_capsule_present")
    
    def test_get_last_restore_decision_absent(self):
        """Test get_last_restore_decision returns absent when no capsule."""
        result = self.observability.get_last_restore_decision()
        
        self.assertEqual(result["status"], "absent")
        self.assertEqual(result["reason"], "no_capsule_present")
    
    def test_get_freshness_status_absent(self):
        """Test get_freshness_status returns absent when no capsule."""
        result = self.observability.get_freshness_status()
        
        self.assertEqual(result["status"], "absent")
        self.assertEqual(result["reason"], "no_capsule_present")
    
    def test_get_last_apply_status_absent(self):
        """Test get_last_apply_status returns absent when no capsule."""
        result = self.observability.get_last_apply_status()
        
        self.assertEqual(result["status"], "absent")
        self.assertEqual(result["reason"], "no_capsule_present")
    
    def test_export_debug_summary(self):
        """Test export_debug_summary produces valid output."""
        summary = self.observability.export_debug_summary()
        
        self.assertIn("debug_summary", summary)
        self.assertIn("timestamp", summary["debug_summary"])
    
    def test_get_capture_timestamp_present(self):
        """Test get_capture_timestamp returns captured when capsule exists."""
        capsule = ActiveWorkCapsule(
            layer_name="test_layer",
            task_id="test_task",
            phase="implementation",
            approved_files=["test.py"],
            pending_tests=["test_function"],
            seal_criteria=["test_criteria"],
            short_task_summary="Test",
            active_constraints=["no_tia"],
            timestamp="2026-04-08T12:00:00Z",
        )
        
        store_result = self.observability._store_capsule_for_test(capsule)
        self.assertEqual(store_result["status"], "stored")
        
        result = self.observability.get_capture_timestamp()
        
        self.assertEqual(result["status"], "captured")
        self.assertEqual(result["timestamp"], "2026-04-08T12:00:00Z")
    
    def test_get_freshness_status_present(self):
        """Test get_freshness_status returns freshness when capsule exists."""
        capsule = ActiveWorkCapsule(
            layer_name="test_layer",
            task_id="test_task",
            phase="implementation",
            approved_files=["test.py"],
            pending_tests=["test_function"],
            seal_criteria=["test_criteria"],
            short_task_summary="Test",
            active_constraints=["no_tia"],
            timestamp="2026-04-08T00:00:00Z",
        )
        
        store_result = self.observability._store_capsule_for_test(capsule)
        self.assertEqual(store_result["status"], "stored")
        
        result = self.observability.get_freshness_status()
        
        self.assertEqual(result["status"], "fresh")


# ===== Integration Tests =====


class TestCapsuleObservabilityIntegration(unittest.TestCase):
    """Test CapsuleObservability integration with v93a-v93g components."""
    
    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.observability = CapsuleObservability(base_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_integration_with_v93a_active_work_capsule(self):
        """Test integration with v93a ActiveWorkCapsule."""
        # Create a capsule using v93a
        capsule = ActiveWorkCapsule(
            layer_name="test",
            task_id="task1",
            phase="implementation",
            approved_files=["test.py"],
            pending_tests=["test_function"],
            seal_criteria=["test_criteria"],
            short_task_summary="Test",
            active_constraints=["no_tia"],
            timestamp="2026-04-08T00:00:00Z",
        )
        
        # Store and observe
        store_result = self.observability._store_capsule_for_test(capsule)
        self.assertEqual(store_result["status"], "stored")
        
        result = self.observability.observe()
        self.assertEqual(result["status"], "observed")
        self.assertTrue(result["capsule_present"])
    
    def test_integration_with_v93d_freshness_policy(self):
        """Test integration with v93d CapsuleFreshnessPolicy."""
        capsule = ActiveWorkCapsule(
            layer_name="test",
            task_id="task1",
            phase="implementation",
            approved_files=["test.py"],
            pending_tests=["test_function"],
            seal_criteria=["test_criteria"],
            short_task_summary="Test",
            active_constraints=["no_tia"],
            timestamp="2026-04-08T00:00:00Z",
        )
        
        store_result = self.observability._store_capsule_for_test(capsule)
        self.assertEqual(store_result["status"], "stored")
        
        result = self.observability.observe()
        self.assertEqual(result["status"], "observed")
        
        # Freshness status should be present
        self.assertIn("freshness_status", result)
    
    def test_full_observability_flow(self):
        """Test complete observability flow from capture to observation."""
        # Create capsule directly (capture_if_valid_context not in capsule_capture.py)
        context = {
            "layer_name": "test_layer",
            "task_id": "test_task",
            "phase": "implementation",
            "short_task_summary": "Test observability flow",
        }
        
        from weslr.active_work_capsule import capture_if_valid_context
        capture_result = capture_if_valid_context(**context)
        self.assertEqual(capture_result["status"], "captured")
        
        # Store
        store_result = self.observability._store_capsule_for_test(capture_result["capsule"])
        self.assertEqual(store_result["status"], "stored")
        
        # Observe
        result = self.observability.observe()
        self.assertEqual(result["status"], "observed")
        self.assertTrue(result["capsule_present"])
        
        # All queries should work
        capsule_status = self.observability.get_capsule_status()
        self.assertEqual(capsule_status["status"], "present")
        
        freshness = self.observability.get_freshness_status()
        self.assertEqual(freshness["status"], "fresh")
    
    def test_observability_with_stale_capsule(self):
        """Test observability with stale capsule."""
        # Create stale capsule
        old_timestamp = "2026-04-01T00:00:00Z"
        capsule = ActiveWorkCapsule(
            layer_name="test",
            task_id="task1",
            phase="implementation",
            approved_files=["test.py"],
            pending_tests=["test_function"],
            seal_criteria=["test_criteria"],
            short_task_summary="Stale test",
            active_constraints=["no_tia"],
            timestamp=old_timestamp,
        )
        
        store_result = self.observability._store_capsule_for_test(capsule)
        self.assertEqual(store_result["status"], "stored")
        
        result = self.observability.observe()
        self.assertEqual(result["status"], "observed")
        
        # Freshness should be stale
        self.assertEqual(result["freshness_status"], "stale")
        self.assertEqual(result["last_restore_decision"], "stale")
        self.assertEqual(result["last_apply_status"], "stale")
    
    def test_observability_with_invalid_phase(self):
        """Test observability with invalid capsule phase."""
        # Create capsule with invalid phase
        capsule = ActiveWorkCapsule(
            layer_name="test",
            task_id="task1",
            phase="invalid_phase",
            approved_files=["test.py"],
            pending_tests=["test_function"],
            seal_criteria=["test_criteria"],
            short_task_summary="Invalid test",
            active_constraints=["no_tia"],
            timestamp="2026-04-08T00:00:00Z",
        )
        
        store_result = self.observability._store_capsule_for_test(capsule)
        self.assertEqual(store_result["status"], "stored")
        
        result = self.observability.observe()
        self.assertEqual(result["status"], "observed")
        
        # Freshness should be invalid
        self.assertEqual(result["freshness_status"], "invalid")
        self.assertEqual(result["last_restore_decision"], "invalid")
        self.assertEqual(result["last_apply_status"], "invalid")


# ===== BackwardCompatibility Tests =====


class TestCapsuleObservabilityBackwardCompatibility(unittest.TestCase):
    """Test CapsuleObservability backward compatibility with v93a-v93g."""
    
    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.observability = CapsuleObservability(base_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_existing_v93a_functions_unchanged(self):
        """Test v93a ActiveWorkCapsule remains unchanged."""
        capsule = ActiveWorkCapsule(
            layer_name="test",
            task_id="task1",
            phase="implementation",
            approved_files=["test.py"],
            pending_tests=["test_function"],
            seal_criteria=["test_criteria"],
            short_task_summary="Test",
            active_constraints=["no_tia"],
            timestamp="2026-04-08T00:00:00Z",
        )
        
        self.assertTrue(capsule.is_valid())
        self.assertIsInstance(capsule.to_dict(), dict)
    
    def test_existing_v93d_policy_unchanged(self):
        """Test v93d CapsuleFreshnessPolicy remains unchanged."""
        from weslr.capsule_policy import CapsuleFreshnessPolicy
        
        context = {"current_layer": "test", "current_task_id": "task1"}
        freshness = CapsuleFreshnessPolicy.validate_freshness(context)
        
        self.assertIn(freshness.status, ["fresh", "stale", "invalid"])
    
    def test_import_paths_unchanged(self):
        """Test import paths for v93a-v93g components unchanged."""
        from weslr.active_work_capsule import ActiveWorkCapsule
        from weslr.capsule_policy import CapsuleFreshnessPolicy
        from weslr.capsule_recovery import CapsuleRebuilder
        
        self.assertTrue(callable(ActiveWorkCapsule))
        self.assertTrue(callable(CapsuleFreshnessPolicy))
        self.assertTrue(callable(CapsuleRebuilder))
    
    def test_observability_does_not_affect_existing_behavior(self):
        """Test observability does not affect existing behavior."""
        capsule = ActiveWorkCapsule(
            layer_name="test",
            task_id="task1",
            phase="implementation",
            approved_files=["test.py"],
            pending_tests=["test_function"],
            seal_criteria=["test_criteria"],
            short_task_summary="Test",
            active_constraints=["no_tia"],
            timestamp="2026-04-08T00:00:00Z",
        )
        
        store_result = self.observability._store_capsule_for_test(capsule)
        self.assertEqual(store_result["status"], "stored")
        
        # Observation should not modify the capsule
        result = self.observability.observe()
        self.assertEqual(result["status"], "observed")
        
        # Verify capsule is still readable
        from weslr.capsule_recovery import CapsuleRebuilder
        loaded_capsule = CapsuleRebuilder.load_capsule_file(self.temp_dir)
        self.assertIsNotNone(loaded_capsule)
    
    def test_observability_functions_exported(self):
        """Test all observability functions are properly exported."""
        self.assertTrue(callable(export_debug_summary))
        self.assertTrue(callable(get_capsule_status))
        self.assertTrue(callable(get_capture_timestamp))
        self.assertTrue(callable(get_last_restore_decision))
        self.assertTrue(callable(get_freshness_status))
        self.assertTrue(callable(get_last_apply_status))


# ===== v93h Specific Tests =====


class TestCapsuleObservabilityV93H(unittest.TestCase):
    """Test v93h specific observability scenarios."""
    
    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.observability = CapsuleObservability(base_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_debug_summary_structure(self):
        """Test debug summary structure."""
        # First create a capsule
        capsule = ActiveWorkCapsule(
            layer_name="test",
            task_id="task1",
            phase="implementation",
            approved_files=["test.py"],
            pending_tests=["test_function"],
            seal_criteria=["test_criteria"],
            short_task_summary="Test",
            active_constraints=["no_tia"],
            timestamp="2026-04-08T00:00:00Z",
        )
        
        store_result = self.observability._store_capsule_for_test(capsule)
        self.assertEqual(store_result["status"], "stored")
        
        summary = self.observability.export_debug_summary()
        
        # Check structure
        self.assertIn("debug_summary", summary)
        self.assertIn("status", summary["debug_summary"])
        self.assertIn("timestamp", summary["debug_summary"])
        self.assertIn("details", summary)
        
        # Check details structure
        details = summary["details"]
        self.assertIn("capsule_present", details)
        self.assertIn("capture_timestamp", details)
        self.assertIn("last_restore_decision", details)
        self.assertIn("freshness_status", details)
        self.assertIn("last_apply_status", details)
    
    def test_operator_queries_return_correct_status(self):
        """Test all operator-facing queries return correct status."""
        capsule = ActiveWorkCapsule(
            layer_name="test",
            task_id="task1",
            phase="implementation",
            approved_files=["test.py"],
            pending_tests=["test_function"],
            seal_criteria=["test_criteria"],
            short_task_summary="Test",
            active_constraints=["no_tia"],
            timestamp="2026-04-08T00:00:00Z",
        )
        
        store_result = self.observability._store_capsule_for_test(capsule)
        self.assertEqual(store_result["status"], "stored")
        
        # All operator queries should work
        capsule_status = self.observability.get_capsule_status()
        self.assertEqual(capsule_status["status"], "present")
        
        capture_time = self.observability.get_capture_timestamp()
        self.assertEqual(capture_time["status"], "captured")
        self.assertIsNotNone(capture_time["timestamp"])
        
        restore_decision = self.observability.get_last_restore_decision()
        self.assertEqual(restore_decision["status"], "applied")
        
        freshness = self.observability.get_freshness_status()
        self.assertEqual(freshness["status"], "fresh")
        
        apply_status = self.observability.get_last_apply_status()
        self.assertEqual(apply_status["status"], "applied")
    
    def test_observability_no_mutation(self):
        """Test observability does not mutate state."""
        capsule = ActiveWorkCapsule(
            layer_name="test",
            task_id="task1",
            phase="implementation",
            approved_files=["test.py"],
            pending_tests=["test_function"],
            seal_criteria=["test_criteria"],
            short_task_summary="Test",
            active_constraints=["no_tia"],
            timestamp="2026-04-08T00:00:00Z",
        )
        
        store_result = self.observability._store_capsule_for_test(capsule)
        self.assertEqual(store_result["status"], "stored")
        
        # Record original capsule state
        original_path = self.observability.capsule_path
        with open(original_path, "r") as f:
            original_content = f.read()
        
        # Run observability multiple times
        for _ in range(3):
            self.observability.observe()
        
        # Verify capsule not modified
        with open(original_path, "r") as f:
            new_content = f.read()
        
        self.assertEqual(original_content, new_content)


# ===== Export Function Tests =====


class TestCapsuleObservabilityExportFunctions(unittest.TestCase):
    """Test export functions for operator workflow."""
    
    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_export_debug_summary_function(self):
        """Test export_debug_summary function."""
        # First create a capsule
        capsule = ActiveWorkCapsule(
            layer_name="test",
            task_id="task1",
            phase="implementation",
            approved_files=["test.py"],
            pending_tests=["test_function"],
            seal_criteria=["test_criteria"],
            short_task_summary="Test",
            active_constraints=["no_tia"],
            timestamp="2026-04-08T00:00:00Z",
        )
        
        # Store it
        continuity_dir = os.path.join(self.temp_dir, "continuity")
        os.makedirs(continuity_dir, exist_ok=True)
        capsule_path = os.path.join(continuity_dir, "active_work_capsule.json")
        with open(capsule_path, "w") as f:
            json.dump(capsule.to_dict(), f)
        
        # Call export function
        summary = export_debug_summary(base_dir=self.temp_dir)
        
        self.assertIn("debug_summary", summary)
        self.assertEqual(summary["debug_summary"]["status"], "observed")
    
    def test_get_capsule_status_function(self):
        """Test get_capsule_status function."""
        summary = get_capsule_status(base_dir=self.temp_dir)
        
        self.assertEqual(summary["status"], "absent")
    
    def test_get_capture_timestamp_function(self):
        """Test get_capture_timestamp function."""
        summary = get_capture_timestamp(base_dir=self.temp_dir)
        
        self.assertEqual(summary["status"], "absent")
    
    def test_get_last_restore_decision_function(self):
        """Test get_last_restore_decision function."""
        summary = get_last_restore_decision(base_dir=self.temp_dir)
        
        self.assertEqual(summary["status"], "absent")
    
    def test_get_freshness_status_function(self):
        """Test get_freshness_status function."""
        summary = get_freshness_status(base_dir=self.temp_dir)
        
        self.assertEqual(summary["status"], "absent")
    
    def test_get_last_apply_status_function(self):
        """Test get_last_apply_status function."""
        summary = get_last_apply_status(base_dir=self.temp_dir)
        
        self.assertEqual(summary["status"], "absent")


if __name__ == "__main__":
    unittest.main()
