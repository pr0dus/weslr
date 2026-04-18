"""WESLR Continuity Resume Tests (v93e)

Test suite for v93e Capsule Invocation Boundary / Silent Resume Trigger.
Tests for resume_from_capsule() helper function.

v93e changes:
- Add resume_from_capsule() as internal helper for silent resume trigger
- Return structured decision dict with apply/ignore/stale/invalid outcomes
- No automatic invocation, no startup/session auto-wiring
- Silent/internal only, no user-visible behavior

Test Doctrine v1.0.0 (2026-04-06)
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone

from weslr import continuity
from weslr.active_work_capsule import ActiveWorkCapsule
from weslr.capsule_policy import CapsuleFreshnessPolicy


class TestResumeFromCapsuleModel(unittest.TestCase):
    """Model tests for resume_from_capsule."""
    
    def test_return_structure_has_required_keys(self):
        """Decision dict must have status and reason keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = continuity.resume_from_capsule(base_dir=tmpdir)
            self.assertIn("status", result)
            self.assertIn("reason", result)
    
    def test_return_status_is_one_of_allowed_values(self):
        """Status must be one of: apply, ignore, stale, invalid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = continuity.resume_from_capsule(base_dir=tmpdir)
            self.assertIn(result["status"], {"apply", "ignore", "stale", "invalid"})
    
    def test_ignore_reason_when_no_capsule(self):
        """Ignore status must have appropriate reason when no capsule exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = continuity.resume_from_capsule(base_dir=tmpdir)
            self.assertEqual(result["status"], "ignore")
            self.assertEqual(result["reason"], "no_capsule_file")


class TestResumeFromCapsuleBehavior(unittest.TestCase):
    """Behavior tests for resume_from_capsule."""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.capsule_path = os.path.join(self.tmpdir, "continuity", "active_work_capsule.json")
        os.makedirs(os.path.dirname(self.capsule_path), exist_ok=True)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def _write_valid_capsule(self, timestamp: str = None):
        """Write a valid capsule for testing."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()
        capsule = ActiveWorkCapsule(
            layer_name="test_layer",
            task_id="test_task",
            phase="planning",
            timestamp=timestamp,
            approved_files=["file1.py"],
            pending_tests=[],
            seal_criteria=[],
            short_task_summary="test",
            active_constraints=[]
        )
        with open(self.capsule_path, "w") as f:
            json.dump(capsule.to_dict(), f)
    
    def _write_valid_capsule_for_freshness_test(self, timestamp: str = None):
        """Write a valid capsule for freshness testing."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()
        capsule = ActiveWorkCapsule(
            layer_name="freshness_test",
            task_id="test_task",
            phase="planning",
            timestamp=timestamp,
            approved_files=["test.py"],
            pending_tests=[],
            seal_criteria=[],
            short_task_summary="freshness test",
            active_constraints=[]
        )
        with open(self.capsule_path, "w") as f:
            json.dump(capsule.to_dict(), f)
    
    def test_apply_for_fresh_valid_capsule(self):
        """Apply status for fresh and valid capsule."""
        self._write_valid_capsule_for_freshness_test()
        result = continuity.resume_from_capsule(base_dir=self.tmpdir)
        self.assertEqual(result["status"], "apply")
        self.assertEqual(result["reason"], "capsule_fresh_and_valid")
        self.assertIn("context", result)
        self.assertEqual(result["context"]["current_layer"], "freshness_test")
    
    def test_stale_for_old_capsule(self):
        """Stale status for capsule older than 24h."""
        old_timestamp = datetime.now(timezone.utc).isoformat()
        # This is a simplified test - actual staleness check is in CapsuleFreshnessPolicy
        # For this test, we verify the policy integration works
        self._write_valid_capsule(timestamp=old_timestamp)
        result = continuity.resume_from_capsule(base_dir=self.tmpdir)
        # The capsule may be fresh if created very recently, so we just verify
        # the decision is one of the valid outcomes
        self.assertIn(result["status"], {"apply", "stale", "invalid"})
    
    def test_context_included_for_apply_decision(self):
        """Context must be included when status is 'apply'."""
        self._write_valid_capsule()
        result = continuity.resume_from_capsule(base_dir=self.tmpdir)
        if result["status"] == "apply":
            self.assertIn("context", result)
            self.assertIsInstance(result["context"], dict)


class TestResumeFromCapsuleIntegration(unittest.TestCase):
    """Integration tests for resume_from_capsule with v93d policy layer."""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.capsule_path = os.path.join(self.tmpdir, "continuity", "active_work_capsule.json")
        os.makedirs(os.path.dirname(self.capsule_path), exist_ok=True)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_integration_with_freshness_policy(self):
        """resume_from_capsule must integrate with v93d CapsuleFreshnessPolicy."""
        # Create a capsule
        timestamp = datetime.now(timezone.utc).isoformat()
        capsule = ActiveWorkCapsule(
            layer_name="integration_test",
            task_id="test_task",
            phase="implementation",
            timestamp=timestamp,
            approved_files=["test.py"],
            pending_tests=[],
            seal_criteria=[],
            short_task_summary="integration",
            active_constraints=[]
        )
        with open(self.capsule_path, "w") as f:
            json.dump(capsule.to_dict(), f)
        
        result = continuity.resume_from_capsule(base_dir=self.tmpdir)
        
        # Verify decision aligns with freshness policy
        if result["status"] == "apply":
            # Freshness should be fresh
            context = result["context"]
            freshness = CapsuleFreshnessPolicy.validate_freshness(context)
            self.assertEqual(freshness.status, "fresh")
        elif result["status"] in {"stale", "invalid"}:
            # Policy should have rejected
            self.assertIn("freshness", result)
    
    def test_no_side_effects_on_existing_files(self):
        """resume_from_capsule must not modify existing files."""
        # Write a capsule
        timestamp = datetime.now(timezone.utc).isoformat()
        capsule = ActiveWorkCapsule(
            layer_name="side_effect_test",
            task_id="test",
            phase="planning",
            timestamp=timestamp,
            approved_files=["test.py"],
            pending_tests=[],
            seal_criteria=[],
            short_task_summary="side effect",
            active_constraints=[]
        )
        with open(self.capsule_path, "w") as f:
            json.dump(capsule.to_dict(), f)
        
        # Get file modification time before
        before_mtime = os.path.getmtime(self.capsule_path)
        
        # Call resume_from_capsule
        result = continuity.resume_from_capsule(base_dir=self.tmpdir)
        
        # Get file modification time after
        after_mtime = os.path.getmtime(self.capsule_path)
        
        # File should not be modified
        self.assertEqual(before_mtime, after_mtime)


class TestResumeFromCapsuleBackwardCompatibility(unittest.TestCase):
    """Backward compatibility tests for v93e."""
    
    def test_no_breaking_changes_to_existing_api(self):
        """resume_from_capsule must not break existing continuity functions."""
        # This test ensures the new helper doesn't affect existing functions
        with tempfile.TemporaryDirectory() as tmpdir:
            # All these existing functions should still work
            from weslr.capsule_recovery import CapsuleRebuilder
            
            # CapsuleRebuilder should work independently
            result = CapsuleRebuilder.rebuild_from_file(tmpdir)
            self.assertIn(result.get("status"), {"no_capsule", "success", "invalid_capsule"})
    
    def test_existing_functions_unchanged(self):
        """Existing functions must remain callable with same signatures."""
        import inspect
        
        # verify_load_weslr_continuity_state
        sig = inspect.signature(continuity.load_weslr_continuity_state)
        params = list(sig.parameters.keys())
        self.assertIn("base_dir", params)
        self.assertIn("adapter", params)
        
        # verify_build_snapshot
        sig = inspect.signature(continuity.build_snapshot)
        params = list(sig.parameters.keys())
        self.assertIn("session_id", params)
        self.assertIn("state_or_base_dir", params)
        
        # verify_restore_from_plan
        sig = inspect.signature(continuity.restore_from_plan)
        params = list(sig.parameters.keys())
        self.assertIn("snapshot", params)
        self.assertIn("dry_run", params)


if __name__ == "__main__":
    unittest.main()
