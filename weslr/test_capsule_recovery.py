"""Test suite for Capsule Recovery - v93a

Test Doctrine v1
Test version: 1.0.0 (2026-04-08)
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from weslr.capsule_recovery import (
    CapsuleRebuilder,
    restore_from_capsule,
)


# ===== Test Behavior =====


class TestCapsuleRebuilderBehavior(unittest.TestCase):
    """Behavior tests for CapsuleRebuilder."""

    def test_rebuild_from_valid_capsule(self) -> None:
        """Test rebuild returns valid context from valid capsule."""
        from weslr.active_work_capsule import ActiveWorkCapsule

        capsule = ActiveWorkCapsule(
            layer_name="test_layer",
            task_id="v93a",
            phase="planning",
            approved_files=["weslr/test_layer.py"],
            pending_tests=["weslr/test_test_layer.py"],
            seal_criteria=["tests_pass"],
            short_task_summary="Test layer",
            active_constraints=["additive_only"],
            timestamp="2026-04-08T00:00:00Z",
        )
        context = CapsuleRebuilder.rebuild_from_capsule(capsule)
        self.assertEqual(context["current_layer"], "test_layer")
        self.assertEqual(context["current_task_id"], "v93a")
        self.assertEqual(context["current_phase"], "planning")
        self.assertEqual(context["approved_files"], {"weslr/test_layer.py"})
        self.assertEqual(context["pending_tests"], {"weslr/test_test_layer.py"})
        self.assertEqual(context["seal_criteria"], ["tests_pass"])
        self.assertEqual(context["short_task_summary"], "Test layer")
        self.assertEqual(context["active_constraints"], ["additive_only"])
        self.assertEqual(context["rebuild_timestamp"], "2026-04-08T00:00:00Z")

    def test_rebuild_from_file_no_file(self) -> None:
        """Test rebuild_from_file returns no_capsule status when file missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = CapsuleRebuilder.rebuild_from_file(tmpdir)
            self.assertEqual(result["status"], "no_capsule")
            self.assertNotIn("context", result)

    def test_rebuild_from_file_valid_capsule(self) -> None:
        """Test rebuild_from_file returns success status with context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create continuity dir and capsule file
            continuity_dir = os.path.join(tmpdir, "continuity")
            os.makedirs(continuity_dir)
            capsule_path = os.path.join(continuity_dir, "active_work_capsule.json")

            capsule_data = {
                "layer_name": "test_layer",
                "task_id": "v93a",
                "phase": "planning",
                "approved_files": ["weslr/test_layer.py"],
                "pending_tests": ["weslr/test_test_layer.py"],
                "seal_criteria": ["tests_pass"],
                "short_task_summary": "Test layer",
                "active_constraints": ["additive_only"],
                "timestamp": "2026-04-08T00:00:00Z",
            }
            with open(capsule_path, "w") as f:
                json.dump(capsule_data, f)

            result = CapsuleRebuilder.rebuild_from_file(tmpdir)
            self.assertEqual(result["status"], "success")
            self.assertIn("context", result)
            self.assertEqual(result["context"]["current_layer"], "test_layer")

    def test_rebuild_from_file_missing_required_fields(self) -> None:
        """Test rebuild_from_file returns no_capsule for invalid JSON structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create continuity dir and capsule file with wrong structure
            continuity_dir = os.path.join(tmpdir, "continuity")
            os.makedirs(continuity_dir)
            capsule_path = os.path.join(continuity_dir, "active_work_capsule.json")

            # Wrong structure (not matching ActiveWorkCapsule)
            capsule_data = {
                "wrong_field": "test",
            }
            with open(capsule_path, "w") as f:
                json.dump(capsule_data, f)

            result = CapsuleRebuilder.rebuild_from_file(tmpdir)
            # from_dict will fail, so load_capsule_file returns None
            self.assertEqual(result["status"], "no_capsule")
            self.assertNotIn("context", result)


# ===== Test Integration =====


class TestCapsuleRebuilderIntegration(unittest.TestCase):
    """Integration tests for CapsuleRebuilder."""

    def test_load_capsule_file_missing(self) -> None:
        """Test load_capsule_file returns None when file missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = CapsuleRebuilder.load_capsule_file(tmpdir)
            self.assertIsNone(result)

    def test_load_capsule_file_valid(self) -> None:
        """Test load_capsule_file loads valid capsule."""
        with tempfile.TemporaryDirectory() as tmpdir:
            continuity_dir = os.path.join(tmpdir, "continuity")
            os.makedirs(continuity_dir)
            capsule_path = os.path.join(continuity_dir, "active_work_capsule.json")

            capsule_data = {
                "layer_name": "test_layer",
                "task_id": "v93a",
                "phase": "planning",
                "approved_files": ["weslr/test_layer.py"],
                "pending_tests": ["weslr/test_test_layer.py"],
                "seal_criteria": ["tests_pass"],
                "short_task_summary": "Test layer",
                "active_constraints": ["additive_only"],
                "timestamp": "2026-04-08T00:00:00Z",
            }
            with open(capsule_path, "w") as f:
                json.dump(capsule_data, f)

            result = CapsuleRebuilder.load_capsule_file(tmpdir)
            self.assertIsNotNone(result)
            self.assertEqual(result.layer_name, "test_layer")
            self.assertEqual(result.task_id, "v93a")
            self.assertEqual(result.phase, "planning")


# ===== Test Top-level Functions =====


class TestRestoreFromCapsuleBehavior(unittest.TestCase):
    """Behavior tests for restore_from_capsule top-level function."""

    def test_restore_no_base_dir(self) -> None:
        """Test restore_from_capsule returns no_base_dir when base_dir=None."""
        result = restore_from_capsule(base_dir=None)
        self.assertEqual(result["status"], "no_base_dir")

    def test_restore_with_tempdir_no_capsule(self) -> None:
        """Test restore_from_capsule returns no_capsule when file missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = restore_from_capsule(base_dir=tmpdir)
            self.assertEqual(result["status"], "no_capsule")

    def test_restore_with_tempdir_valid_capsule(self) -> None:
        """Test restore_from_capsule returns success with valid capsule."""
        with tempfile.TemporaryDirectory() as tmpdir:
            continuity_dir = os.path.join(tmpdir, "continuity")
            os.makedirs(continuity_dir)
            capsule_path = os.path.join(continuity_dir, "active_work_capsule.json")

            capsule_data = {
                "layer_name": "test_layer",
                "task_id": "v93a",
                "phase": "planning",
                "approved_files": ["weslr/test_layer.py"],
                "pending_tests": ["weslr/test_test_layer.py"],
                "seal_criteria": ["tests_pass"],
                "short_task_summary": "Test layer",
                "active_constraints": ["additive_only"],
                "timestamp": "2026-04-08T00:00:00Z",
            }
            with open(capsule_path, "w") as f:
                json.dump(capsule_data, f)

            result = restore_from_capsule(base_dir=tmpdir)
            self.assertEqual(result["status"], "success")
            self.assertIn("context", result)
            self.assertEqual(result["context"]["current_layer"], "test_layer")


if __name__ == "__main__":
    unittest.main()
