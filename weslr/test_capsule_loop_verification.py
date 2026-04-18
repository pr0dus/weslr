"""Test suite for Capsule Loop Verification (v93g)

Test Doctrine v1.0.0
Test Doctrine version: 1.0.0 (2026-04-08)

Tests for v93g: Capsule End-to-End Silent Continuity Loop Verification.
Verifies capture→store→load→validate→decision→apply cycle end to end.

Test Categories:
- Model Tests: Dataclass fields, serialization, constants
- Behavior Tests: Full loop execution, decision mapping
- Integration Tests: Hooks into v93a-v93f, backward compatibility
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
from weslr.capsule_loop_verification import (
    CapsuleLoopVerifier,
    capture_if_valid_context,
)


# ===== Model Tests =====


class TestCapsuleLoopVerifierModel(unittest.TestCase):
    """Test CapsuleLoopVerifier data models and serialization."""
    
    def test_loop_verification_result_dataclass(self):
        """Test LoopVerificationResult dataclass fields."""
        from weslr.capsule_loop_verification import LoopVerificationResult
        
        result = LoopVerificationResult.verified({"step": "test"})
        
        self.assertEqual(result.status, "verified")
        self.assertEqual(result.reason, "full_loop_verified")
        self.assertEqual(result.loop_steps, {"step": "test"})
        self.assertIn("timestamp", result.__dict__)
    
    def test_loop_verification_result_to_dict(self):
        """Test LoopVerificationResult to_dict serialization."""
        from weslr.capsule_loop_verification import LoopVerificationResult
        
        result = LoopVerificationResult.verified({"step": "test"})
        data = result.to_dict()
        
        self.assertEqual(data["status"], "verified")
        self.assertEqual(data["reason"], "full_loop_verified")
        self.assertIn("timestamp", data)
    
    def test_loop_verification_result_failed(self):
        """Test LoopVerificationResult failed factory."""
        from weslr.capsule_loop_verification import LoopVerificationResult
        
        result = LoopVerificationResult.failed("test_reason", {"step": "failed"})
        
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.reason, "test_reason")
    
    def test_constants_defined(self):
        """Test max capsule age constant is defined and reasonable."""
        # MAX_CAPSULE_AGE_SECONDS is defined in capsule_policy.py (v93d)
        from weslr.capsule_policy import MAX_CAPSULE_AGE_SECONDS
        
        # Should be 24 hours in seconds
        self.assertEqual(MAX_CAPSULE_AGE_SECONDS, 24 * 60 * 60)
        self.assertGreater(MAX_CAPSULE_AGE_SECONDS, 0)


# ===== Behavior Tests =====


class TestCapsuleLoopVerifierBehavior(unittest.TestCase):
    """Test CapsuleLoopVerifier full loop execution behavior."""
    
    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.verifier = CapsuleLoopVerifier(base_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_loop_verified(self):
        """Test full loop verification succeeds with valid context."""
        context = {
            "layer_name": "test_layer",
            "task_id": "test_task",
            "phase": "implementation",
            "short_task_summary": "Test verification",
        }
        
        result = self.verifier.verify_full_loop(context)
        
        self.assertEqual(result["status"], "verified")
        self.assertIn("loop_steps", result)
        self.assertIn("capture", result["loop_steps"])
        self.assertIn("store", result["loop_steps"])
        self.assertIn("load", result["loop_steps"])
        self.assertIn("validate", result["loop_steps"])
        self.assertIn("decision", result["loop_steps"])
        self.assertIn("apply", result["loop_steps"])
    
    def test_capture_boundary_validation(self):
        """Test capture boundary correctly validates context."""
        # Valid context
        context = {
            "layer_name": "test",
            "task_id": "task1",
            "phase": "implementation",
            "short_task_summary": "Test",
        }
        
        result = self.verifier._capture_context(context)
        self.assertEqual(result["status"], "captured")
        
        # Invalid context - missing required field
        invalid_context = {
            "layer_name": "",
            "task_id": "task1",
            "phase": "implementation",
            "short_task_summary": "Test",
        }
        
        result = self.verifier._capture_context(invalid_context)
        self.assertEqual(result["status"], "skipped")
    
    def test_restore_boundary_validation(self):
        """Test restore boundary correctly loads and validates capsule."""
        context = {
            "layer_name": "test",
            "task_id": "task1",
            "phase": "implementation",
            "short_task_summary": "Test",
        }
        
        # Capture and store
        capture_result = self.verifier._capture_context(context)
        self.assertEqual(capture_result["status"], "captured")
        
        store_result = self.verifier._store_capsule(capture_result["capsule"])
        self.assertEqual(store_result["status"], "stored")
        
        # Load
        load_result = self.verifier._load_capsule()
        self.assertEqual(load_result["status"], "loaded")
        
        # Validate
        validate_result = self.verifier._validate_capsule(load_result["capsule"])
        self.assertEqual(validate_result["status"], "valid")
    
    def test_freshness_policy_integration(self):
        """Test freshness policy integration in loop verification."""
        context = {
            "layer_name": "test",
            "task_id": "task1",
            "phase": "implementation",
            "short_task_summary": "Test",
        }
        
        # Capture and store
        capture_result = self.verifier._capture_context(context)
        store_result = self.verifier._store_capsule(capture_result["capsule"])
        
        # Load and validate
        load_result = self.verifier._load_capsule()
        validate_result = self.verifier._validate_capsule(load_result["capsule"])
        
        # Should be fresh
        self.assertEqual(validate_result["status"], "valid")
    
    def test_stale_invalid_rejection(self):
        """Test stale/invalid capsule rejection."""
        # Create stale capsule (old timestamp)
        old_timestamp = "2026-04-01T00:00:00Z"
        stale_capsule = ActiveWorkCapsule(
            layer_name="test",
            task_id="task1",
            phase="implementation",
            approved_files=[],
            pending_tests=[],
            seal_criteria=[],
            short_task_summary="Stale test",
            active_constraints=[],
            timestamp=old_timestamp,
        )
        
        store_result = self.verifier._store_capsule(stale_capsule)
        self.assertEqual(store_result["status"], "stored")
        
        load_result = self.verifier._load_capsule()
        validate_result = self.verifier._validate_capsule(load_result["capsule"])
        
        # Should be rejected as stale
        self.assertEqual(validate_result["status"], "rejected")
    
    def test_silent_decision_behavior(self):
        """Test decision behavior is silent/internal only."""
        context = {
            "layer_name": "test",
            "task_id": "task1",
            "phase": "implementation",
            "short_task_summary": "Test",
        }
        
        # Capture and store
        capture_result = self.verifier._capture_context(context)
        store_result = self.verifier._store_capsule(capture_result["capsule"])
        
        # Load
        self.verifier._load_capsule()
        
        # Decision should be silent/internal
        decision_result = self.verifier._make_decision({})
        self.assertEqual(decision_result["status"], "apply")
        self.assertIn("reason", decision_result)
    
    def test_export_verification_summary(self):
        """Test export verification summary produces valid output."""
        summary = self.verifier.export_verification_summary()
        
        self.assertIn("verification_summary", summary)
        self.assertIn("details", summary)
        self.assertIn("timestamp", summary["verification_summary"])


# ===== Integration Tests =====


class TestCapsuleLoopVerifierIntegration(unittest.TestCase):
    """Test CapsuleLoopVerifier integration with v93a-v93f components."""
    
    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.verifier = CapsuleLoopVerifier(base_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_capture_integration_with_v93f(self):
        """Test capture integration with v93f capture_if_valid_context."""
        context = {
            "layer_name": "test",
            "task_id": "task1",
            "phase": "implementation",
            "short_task_summary": "Test",
        }
        
        result = self.verifier._capture_context(context)
        self.assertEqual(result["status"], "captured")
        self.assertIn("capsule", result)
        self.assertIsInstance(result["capsule"], ActiveWorkCapsule)
    
    def test_restore_integration_with_v93c(self):
        """Test restore integration with v93c CapsuleRebuilder."""
        context = {
            "layer_name": "test",
            "task_id": "task1",
            "phase": "implementation",
            "short_task_summary": "Test",
        }
        
        # Capture and store
        capture_result = self.verifier._capture_context(context)
        self.verifier._store_capsule(capture_result["capsule"])
        
        # Load using CapsuleRebuilder
        capsule = self.verifier._load_capsule()["capsule"]
        self.assertIsInstance(capsule, ActiveWorkCapsule)
    
    def test_freshness_policy_integration_with_v93d(self):
        """Test freshness policy integration with v93d CapsuleFreshnessPolicy."""
        context = {
            "layer_name": "test",
            "task_id": "task1",
            "phase": "implementation",
            "short_task_summary": "Test",
        }
        
        # Capture, store, load
        capture_result = self.verifier._capture_context(context)
        self.verifier._store_capsule(capture_result["capsule"])
        load_result = self.verifier._load_capsule()
        
        # Validate using v93d policy
        validate_result = self.verifier._validate_capsule(load_result["capsule"])
        self.assertIn("freshness", validate_result)
    
    def test_decision_integration_with_v93e(self):
        """Test decision integration with v93e resume_from_capsule logic."""
        context = {
            "layer_name": "test",
            "task_id": "task1",
            "phase": "implementation",
            "short_task_summary": "Test",
        }
        
        # Capture, store, load, validate
        capture_result = self.verifier._capture_context(context)
        self.verifier._store_capsule(capture_result["capsule"])
        load_result = self.verifier._load_capsule()
        validate_result = self.verifier._validate_capsule(load_result["capsule"])
        
        # Make decision using v93e logic
        decision_result = self.verifier._make_decision(validate_result["context"])
        self.assertIn("status", decision_result)
    
    def test_boundary_interaction_integration(self):
        """Test capture boundary + restore boundary interaction."""
        context = {
            "layer_name": "test",
            "task_id": "task1",
            "phase": "implementation",
            "short_task_summary": "Test",
        }
        
        # Capture
        capture_result = self.verifier._capture_context(context)
        self.assertEqual(capture_result["status"], "captured")
        
        # Store
        store_result = self.verifier._store_capsule(capture_result["capsule"])
        self.assertEqual(store_result["status"], "stored")
        
        # Load (restore boundary)
        load_result = self.verifier._load_capsule()
        self.assertEqual(load_result["status"], "loaded")
        
        # Verify capsule matches original
        original_capsule = capture_result["capsule"]
        loaded_capsule = load_result["capsule"]
        
        self.assertEqual(original_capsule.layer_name, loaded_capsule.layer_name)
        self.assertEqual(original_capsule.task_id, loaded_capsule.task_id)
    
    def test_freshness_policy_integration_with_loop(self):
        """Test freshness policy integration in full loop."""
        context = {
            "layer_name": "test",
            "task_id": "task1",
            "phase": "implementation",
            "short_task_summary": "Test",
        }
        
        result = self.verifier.verify_full_loop(context)
        self.assertEqual(result["status"], "verified")
        self.assertIn("validate", result["loop_steps"])
        self.assertIn("freshness", result["loop_steps"]["validate"])
    
    def test_stale_invalid_rejection_integration(self):
        """Test stale/invalid rejection integration in loop."""
        # Create stale capsule
        old_timestamp = "2026-04-01T00:00:00Z"
        stale_capsule = ActiveWorkCapsule(
            layer_name="test",
            task_id="task1",
            phase="implementation",
            approved_files=[],
            pending_tests=[],
            seal_criteria=[],
            short_task_summary="Stale test",
            active_constraints=[],
            timestamp=old_timestamp,
        )
        
        # Store and run loop
        self.verifier._store_capsule(stale_capsule)
        
        # Load and validate
        load_result = self.verifier._load_capsule()
        validate_result = self.verifier._validate_capsule(load_result["capsule"])
        
        self.assertEqual(validate_result["status"], "rejected")


# ===== BackwardCompatibility Tests =====


class TestCapsuleLoopVerifierBackwardCompatibility(unittest.TestCase):
    """Test CapsuleLoopVerifier backward compatibility with v93a-v93f."""
    
    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.verifier = CapsuleLoopVerifier(base_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_existing_functions_unchanged(self):
        """Test existing capture functions remain callable."""
        # v93f capture_if_valid_context
        context = {
            "layer_name": "test",
            "task_id": "task1",
            "phase": "implementation",
            "short_task_summary": "Test",
        }
        
        result = capture_if_valid_context(
            layer_name=context["layer_name"],
            task_id=context["task_id"],
            phase=context["phase"],
            short_task_summary=context["short_task_summary"],
        )
        
        self.assertEqual(result["status"], "captured")
    
    def test_no_breaking_changes_to_existing_api(self):
        """Test no breaking changes to v93a-v93f APIs."""
        # v93a ActiveWorkCapsule - verify basic construction and serialization
        capsule = ActiveWorkCapsule(
            layer_name="test",
            task_id="task1",
            phase="implementation",
            approved_files=["test_file.py"],
            pending_tests=["test_function"],
            seal_criteria=["test_criteria"],
            short_task_summary="Test",
            active_constraints=["no_tia"],
            timestamp="2026-04-08T00:00:00Z",
        )
        
        # Verify capsule is valid and can be serialized
        self.assertTrue(capsule.is_valid())
        
        # v93c CapsuleRebuilder
        from weslr.capsule_recovery import CapsuleRebuilder
        context = CapsuleRebuilder.rebuild_from_capsule(capsule)
        
        self.assertIn("current_layer", context)
        self.assertIn("current_task_id", context)
    
    def test_import_paths_unchanged(self):
        """Test import paths for v93a-v93f components unchanged."""
        from weslr.active_work_capsule import ActiveWorkCapsule
        from weslr.capsule_policy import CapsuleFreshnessPolicy
        from weslr.capsule_recovery import CapsuleRebuilder
        
        self.assertTrue(callable(ActiveWorkCapsule))
        self.assertTrue(callable(CapsuleFreshnessPolicy))
        self.assertTrue(callable(CapsuleRebuilder))
    
    def test_constants_unchanged(self):
        """Test v93a-v93f constants remain unchanged."""
        from weslr.capsule_policy import MAX_CAPSULE_AGE_SECONDS
        
        # Should be 24 hours
        self.assertEqual(MAX_CAPSULE_AGE_SECONDS, 24 * 60 * 60)


# ===== Additional v93g Specific Tests =====


class TestCapsuleLoopVerifierV93G(unittest.TestCase):
    """Test v93g specific verification scenarios."""
    
    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.verifier = CapsuleLoopVerifier(base_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_boundary_interaction_verification(self):
        """Test boundary interaction verification."""
        result = self.verifier.verify_boundary_interaction()
        
        self.assertEqual(result["status"], "verified")
        self.assertIn("reason", result)
    
    def test_freshness_policy_verification(self):
        """Test freshness policy integration verification."""
        result = self.verifier.verify_freshness_policy_integration()
        
        self.assertEqual(result["status"], "verified")
        self.assertIn("freshness", result)
    
    def test_stale_invalid_rejection_verification(self):
        """Test stale/invalid rejection verification."""
        result = self.verifier.verify_stale_invalid_rejection()
        
        self.assertEqual(result["status"], "verified")
        self.assertIn("details", result)
    
    def test_silent_decision_verification(self):
        """Test silent decision behavior verification."""
        result = self.verifier.verify_silent_decision_behavior()
        
        self.assertEqual(result["status"], "verified")
        self.assertIn("reason", result)
    
    def test_full_loop_with_all_fields(self):
        """Test full loop with all optional fields."""
        context = {
            "layer_name": "test_layer",
            "task_id": "test_task",
            "phase": "implementation",
            "short_task_summary": "Test with all fields",
            "approved_files": ["file1.py", "file2.py"],
            "pending_tests": ["test_file1", "test_file2"],
            "seal_criteria": ["all_tests_pass", "format_check"],
            "active_constraints": ["no_tia", "no_csharp"],
        }
        
        result = self.verifier.verify_full_loop(context)
        
        self.assertEqual(result["status"], "verified")
        self.assertIn("apply", result["loop_steps"])
    
    def test_export_summary_structure(self):
        """Test export verification summary structure."""
        summary = self.verifier.export_verification_summary()
        
        # Check structure
        self.assertIn("verification_summary", summary)
        self.assertIn("status", summary["verification_summary"])
        self.assertIn("timestamp", summary["verification_summary"])
        self.assertIn("details", summary)
        
        # Check details structure
        details = summary["details"]
        self.assertIn("boundary_interaction", details)
        self.assertIn("freshness_policy_integration", details)
        self.assertIn("stale_invalid_rejection", details)
        self.assertIn("silent_decision_behavior", details)
    
    def test_full_loop_failure_for_invalid_phase(self):
        """Test full loop fails for invalid phase."""
        context = {
            "layer_name": "test",
            "task_id": "task1",
            "phase": "invalid_phase",  # Not implementation or seal
            "short_task_summary": "Test",
        }
        
        result = self.verifier.verify_full_loop(context)
        
        self.assertEqual(result["status"], "failed")
        self.assertIn("capture", result["loop_steps"])
        self.assertIn("reason", result)


# ===== Capture If Valid Context Tests =====


class TestCaptureIfValidContext(unittest.TestCase):
    """Test capture_if_valid_context function."""
    
    def test_capture_valid_context(self):
        """Test capture with valid context."""
        context = {
            "layer_name": "test",
            "task_id": "task1",
            "phase": "implementation",
            "short_task_summary": "Test",
        }
        
        result = capture_if_valid_context(
            layer_name=context["layer_name"],
            task_id=context["task_id"],
            phase=context["phase"],
            short_task_summary=context["short_task_summary"],
        )
        
        self.assertEqual(result["status"], "captured")
        self.assertIn("capsule", result)
        self.assertIsInstance(result["capsule"], ActiveWorkCapsule)
    
    def test_capture_invalid_phase(self):
        """Test capture with invalid phase."""
        context = {
            "layer_name": "test",
            "task_id": "task1",
            "phase": "invalid",
            "short_task_summary": "Test",
        }
        
        result = capture_if_valid_context(
            layer_name=context["layer_name"],
            task_id=context["task_id"],
            phase=context["phase"],
            short_task_summary=context["short_task_summary"],
        )
        
        self.assertEqual(result["status"], "skipped")
        self.assertIn("phase_not_captureworthy", result["reason"])
    
    def test_capture_missing_required_field(self):
        """Test capture with missing required field."""
        result = capture_if_valid_context(
            layer_name="",
            task_id="task1",
            phase="implementation",
            short_task_summary="Test",
        )
        
        self.assertEqual(result["status"], "skipped")
        self.assertIn("empty_required_field", result["reason"])
    
    def test_capture_null_required_field(self):
        """Test capture with null required field."""
        result = capture_if_valid_context(
            layer_name=None,
            task_id="task1",
            phase="implementation",
            short_task_summary="Test",
        )
        
        self.assertEqual(result["status"], "skipped")
        self.assertIn("missing_required_field", result["reason"])


if __name__ == "__main__":
    unittest.main()
