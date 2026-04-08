"""Test suite for ActiveWorkCapsule - v93a

Test Doctrine v1
Test version: 1.0.0 (2026-04-08)
"""

from __future__ import annotations

import json
import unittest
from typing import Any, Dict

from weslr.active_work_capsule import (
    ActiveWorkCapsule,
    CapsuleSerializer,
    create_capsule,
)


# ===== Test Model =====


class TestActiveWorkCapsuleModel(unittest.TestCase):
    """Model tests for ActiveWorkCapsule."""

    def test_to_dict_serialization(self) -> None:
        """Test that capsule serializes to dictionary correctly."""
        capsule = ActiveWorkCapsule(
            layer_name="test_layer",
            task_id="v93a",
            phase="planning",
            approved_files=["weslr/test_layer.py"],
            pending_tests=["weslr/test_test_layer.py"],
            seal_criteria=["tests_pass"],
            short_task_summary="Test layer implementation",
            active_constraints=["additive_only"],
            timestamp="2026-04-08T00:00:00Z",
        )
        result = capsule.to_dict()
        self.assertEqual(result["layer_name"], "test_layer")
        self.assertEqual(result["task_id"], "v93a")
        self.assertEqual(result["phase"], "planning")
        self.assertEqual(result["approved_files"], ["weslr/test_layer.py"])
        self.assertEqual(result["pending_tests"], ["weslr/test_test_layer.py"])
        self.assertEqual(result["seal_criteria"], ["tests_pass"])
        self.assertEqual(result["short_task_summary"], "Test layer implementation")
        self.assertEqual(result["active_constraints"], ["additive_only"])
        self.assertEqual(result["timestamp"], "2026-04-08T00:00:00Z")

    def test_from_dict_deserialization(self) -> None:
        """Test that capsule deserializes from dictionary correctly."""
        data: Dict[str, Any] = {
            "layer_name": "test_layer",
            "task_id": "v93a",
            "phase": "planning",
            "approved_files": ["weslr/test_layer.py"],
            "pending_tests": ["weslr/test_test_layer.py"],
            "seal_criteria": ["tests_pass"],
            "short_task_summary": "Test layer implementation",
            "active_constraints": ["additive_only"],
            "timestamp": "2026-04-08T00:00:00Z",
        }
        capsule = ActiveWorkCapsule.from_dict(data)
        self.assertEqual(capsule.layer_name, "test_layer")
        self.assertEqual(capsule.task_id, "v93a")
        self.assertEqual(capsule.phase, "planning")
        self.assertEqual(capsule.approved_files, ["weslr/test_layer.py"])
        self.assertEqual(capsule.pending_tests, ["weslr/test_test_layer.py"])
        self.assertEqual(capsule.seal_criteria, ["tests_pass"])
        self.assertEqual(capsule.short_task_summary, "Test layer implementation")
        self.assertEqual(capsule.active_constraints, ["additive_only"])
        self.assertEqual(capsule.timestamp, "2026-04-08T00:00:00Z")

    def test_to_json_serialization(self) -> None:
        """Test that capsule serializes to JSON correctly."""
        capsule = ActiveWorkCapsule(
            layer_name="test_layer",
            task_id="v93a",
            phase="planning",
            approved_files=["weslr/test_layer.py"],
            pending_tests=["weslr/test_test_layer.py"],
            seal_criteria=["tests_pass"],
            short_task_summary="Test layer implementation",
            active_constraints=["additive_only"],
            timestamp="2026-04-08T00:00:00Z",
        )
        json_str = capsule.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["layer_name"], "test_layer")
        self.assertEqual(parsed["task_id"], "v93a")
        self.assertEqual(parsed["phase"], "planning")

    def test_from_json_deserialization(self) -> None:
        """Test that capsule deserializes from JSON correctly."""
        json_str = json.dumps({
            "layer_name": "test_layer",
            "task_id": "v93a",
            "phase": "planning",
            "approved_files": ["weslr/test_layer.py"],
            "pending_tests": ["weslr/test_test_layer.py"],
            "seal_criteria": ["tests_pass"],
            "short_task_summary": "Test layer implementation",
            "active_constraints": ["additive_only"],
            "timestamp": "2026-04-08T00:00:00Z",
        })
        capsule = ActiveWorkCapsule.from_json(json_str)
        self.assertEqual(capsule.layer_name, "test_layer")
        self.assertEqual(capsule.task_id, "v93a")
        self.assertEqual(capsule.phase, "planning")

    def test_json_roundtrip(self) -> None:
        """Test that to_json/from_json preserves data."""
        original = ActiveWorkCapsule(
            layer_name="test_layer",
            task_id="v93a",
            phase="planning",
            approved_files=["weslr/test_layer.py"],
            pending_tests=["weslr/test_test_layer.py"],
            seal_criteria=["tests_pass"],
            short_task_summary="Test layer implementation",
            active_constraints=["additive_only"],
            timestamp="2026-04-08T00:00:00Z",
        )
        json_str = original.to_json()
        restored = ActiveWorkCapsule.from_json(json_str)
        self.assertEqual(original.layer_name, restored.layer_name)
        self.assertEqual(original.task_id, restored.task_id)
        self.assertEqual(original.phase, restored.phase)

    def test_from_dict_roundtrip(self) -> None:
        """Test that to_dict/from_dict preserves data."""
        original = ActiveWorkCapsule(
            layer_name="test_layer",
            task_id="v93a",
            phase="planning",
            approved_files=["weslr/test_layer.py"],
            pending_tests=["weslr/test_test_layer.py"],
            seal_criteria=["tests_pass"],
            short_task_summary="Test layer implementation",
            active_constraints=["additive_only"],
            timestamp="2026-04-08T00:00:00Z",
        )
        data = original.to_dict()
        restored = ActiveWorkCapsule.from_dict(data)
        self.assertEqual(original.layer_name, restored.layer_name)
        self.assertEqual(original.task_id, restored.task_id)
        self.assertEqual(original.phase, restored.phase)


# ===== Test Behavior =====


class TestActiveWorkCapsuleBehavior(unittest.TestCase):
    """Behavior tests for ActiveWorkCapsule."""

    def test_construction_with_all_fields(self) -> None:
        """Test capsule construction with all fields provided."""
        capsule = ActiveWorkCapsule(
            layer_name="test_layer",
            task_id="v93a",
            phase="planning",
            approved_files=["weslr/test_layer.py"],
            pending_tests=["weslr/test_test_layer.py"],
            seal_criteria=["tests_pass"],
            short_task_summary="Test layer implementation",
            active_constraints=["additive_only"],
            timestamp="2026-04-08T00:00:00Z",
        )
        self.assertTrue(capsule.is_valid())
        self.assertEqual(capsule.layer_name, "test_layer")

    def test_construction_with_minimal_fields(self) -> None:
        """Test capsule construction with minimal valid fields."""
        capsule = ActiveWorkCapsule(
            layer_name="test_layer",
            task_id="v93a",
            phase="planning",
            approved_files=["weslr/test_layer.py"],
            pending_tests=["weslr/test_test_layer.py"],
            seal_criteria=["tests_pass"],
            short_task_summary="Test",
            active_constraints=["additive_only"],
            timestamp="2026-04-08T00:00:00Z",
        )
        self.assertTrue(capsule.is_valid())

    def test_from_dict_none_field(self) -> None:
        """Test that None for required field is caught."""
        capsule = ActiveWorkCapsule(
            layer_name="test_layer",
            task_id="v93a",
            phase=None,  # Invalid: None for required field
            approved_files=["weslr/test_layer.py"],
            pending_tests=["weslr/test_test_layer.py"],
            seal_criteria=["tests_pass"],
            short_task_summary="Test",
            active_constraints=["additive_only"],
            timestamp="2026-04-08T00:00:00Z",
        )
        self.assertFalse(capsule.is_valid())

    def test_from_dict_empty_list_field(self) -> None:
        """Test that empty list is caught as invalid."""
        capsule = ActiveWorkCapsule(
            layer_name="test_layer",
            task_id="v93a",
            phase="planning",
            approved_files=[],  # Empty list is invalid
            pending_tests=["weslr/test_test_layer.py"],
            seal_criteria=["tests_pass"],
            short_task_summary="Test",
            active_constraints=["additive_only"],
            timestamp="2026-04-08T00:00:00Z",
        )
        self.assertFalse(capsule.is_valid())


# ===== Test Serialization =====


class TestCapsuleSerializerBehavior(unittest.TestCase):
    """Behavior tests for CapsuleSerializer."""

    def test_serialize_deserialize(self) -> None:
        """Test serializer roundtrip."""
        capsule = ActiveWorkCapsule(
            layer_name="test_layer",
            task_id="v93a",
            phase="planning",
            approved_files=["weslr/test_layer.py"],
            pending_tests=["weslr/test_test_layer.py"],
            seal_criteria=["tests_pass"],
            short_task_summary="Test",
            active_constraints=["additive_only"],
            timestamp="2026-04-08T00:00:00Z",
        )
        json_str = CapsuleSerializer.serialize(capsule)
        restored = CapsuleSerializer.deserialize(json_str)
        self.assertEqual(capsule.layer_name, restored.layer_name)
        self.assertEqual(capsule.task_id, restored.task_id)


# ===== Test Factory =====


class TestCreateCapsuleBehavior(unittest.TestCase):
    """Behavior tests for create_capsule factory."""

    def test_create_capsule(self) -> None:
        """Test factory function creates valid capsule."""
        capsule = create_capsule(
            layer_name="test_layer",
            task_id="v93a",
            phase="planning",
            approved_files=["weslr/test_layer.py"],
            pending_tests=["weslr/test_test_layer.py"],
            seal_criteria=["tests_pass"],
            short_task_summary="Test",
            active_constraints=["additive_only"],
        )
        self.assertEqual(capsule.layer_name, "test_layer")
        self.assertEqual(capsule.task_id, "v93a")
        self.assertEqual(capsule.phase, "planning")
        # timestamp should be None from factory, so is_valid() returns False
        self.assertFalse(capsule.is_valid())

    def test_create_capsule_then_set_timestamp(self) -> None:
        """Test factory + timestamp assignment."""
        capsule = create_capsule(
            layer_name="test_layer",
            task_id="v93a",
            phase="planning",
            approved_files=["weslr/test_layer.py"],
            pending_tests=["weslr/test_test_layer.py"],
            seal_criteria=["tests_pass"],
            short_task_summary="Test",
            active_constraints=["additive_only"],
        )
        capsule.timestamp = "2026-04-08T00:00:00Z"
        self.assertTrue(capsule.is_valid())


if __name__ == "__main__":
    unittest.main()
