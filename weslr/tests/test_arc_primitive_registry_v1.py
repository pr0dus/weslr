from __future__ import annotations

import json

import pytest

from weslr.arc_primitive_registry_v1 import (
    PrimitiveDescriptor,
    PrimitiveRegistry,
    REQUIRED_DESCRIPTOR_FIELDS_V1,
    UNSAFE_TRACE_METADATA_LABELS_V1,
    build_arc_primitive_registry_v1,
)


EXPECTED_PRIMITIVE_NAMES_V1 = {
    "crop_foreground_bbox",
    "crop_largest_object",
    "crop_selected_color_object",
    "translate_single_object",
    "rotate_object_90",
    "rotate_object_180",
    "rotate_object_270",
    "reflect_object_horizontal",
    "reflect_object_vertical",
    "preserve_shape_translate",
    "recolor_global",
    "recolor_foreground",
    "recolor_source_color",
    "recolor_background",
    "swap_two_colors",
    "tile_grid",
    "scale_cells_integer",
    "add_uniform_border",
    "crop_then_tile",
    "count_objects_to_line",
    "foreground_cell_count_to_line",
    "unique_color_count_to_line",
    "object_count_to_square",
    "select_most_frequent_foreground_color",
    "select_largest_object",
}


def _descriptor(**overrides: object) -> PrimitiveDescriptor:
    base = {
        "primitive_name": "crop_foreground_bbox",
        "family": "object_bbox",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("stable_background",),
        "effect_summary": "Crop the foreground bounding box.",
        "train_inference_fn_name": "arc_object_bbox_solver_v1.solve_object_bbox_task",
        "executor_fn_name": "arc_object_extraction_v1.crop_to_foreground_bbox_v1",
        "inverse_or_comparable_relation": "crop_largest_object",
        "rejection_reasons": ("no_foreground",),
        "trace_safe_metadata": ("primitive_name", "family", "train_fit"),
    }
    base.update(overrides)
    return PrimitiveDescriptor(**base)


def test_descriptor_creation_and_json_safe_export() -> None:
    descriptor = _descriptor()
    exported = descriptor.to_json_safe_dict()
    assert exported["primitive_name"] == "crop_foreground_bbox"
    assert exported["family"] == "object_bbox"
    assert exported["preconditions"] == ["stable_background"]
    assert exported["rejection_reasons"] == ["no_foreground"]
    assert exported["trace_safe_metadata"] == ["primitive_name", "family", "train_fit"]
    json.dumps(exported, sort_keys=True)


def test_descriptor_rejects_missing_required_fields() -> None:
    with pytest.raises(ValueError, match="missing_required_fields"):
        _descriptor(effect_summary="")
    with pytest.raises(ValueError, match="missing_required_fields"):
        _descriptor(family="")
    with pytest.raises(ValueError, match="missing_required_fields"):
        _descriptor(input_type="")


def test_descriptor_rejects_unsafe_trace_metadata_labels() -> None:
    for label in UNSAFE_TRACE_METADATA_LABELS_V1:
        with pytest.raises(ValueError, match="unsafe_trace_metadata_label"):
            _descriptor(trace_safe_metadata=("primitive_name", label))


def test_registry_register_get_and_family_listing() -> None:
    registry = PrimitiveRegistry()
    descriptor = _descriptor(primitive_name="crop_foreground_bbox")
    registry.register(descriptor)
    assert registry.get("crop_foreground_bbox") == descriptor
    assert registry.list_by_family("object_bbox") == [descriptor]


def test_registry_rejects_duplicate_primitive_names() -> None:
    registry = PrimitiveRegistry()
    descriptor = _descriptor(primitive_name="crop_foreground_bbox")
    registry.register(descriptor)
    with pytest.raises(ValueError, match="duplicate_primitive_name"):
        registry.register(descriptor)


def test_builtin_registry_contains_expected_names_and_validates() -> None:
    registry = build_arc_primitive_registry_v1()
    names = [descriptor.primitive_name for descriptor in registry.list_primitives()]
    assert set(names) == EXPECTED_PRIMITIVE_NAMES_V1
    assert len(names) == len(EXPECTED_PRIMITIVE_NAMES_V1)
    validation = registry.validate()
    assert validation["valid"] is True
    assert validation["primitive_count"] == len(EXPECTED_PRIMITIVE_NAMES_V1)
    assert validation["errors"] == []


def test_builtin_registry_manifest_is_json_safe_and_label_safe() -> None:
    registry = build_arc_primitive_registry_v1()
    manifest = registry.export_manifest()
    blob = json.dumps(manifest, sort_keys=True).lower()
    for unsafe in ("raw_grid", "expected_output", "solution", "answer_key", "public_solution"):
        assert unsafe not in blob
    assert manifest["primitive_count"] == len(EXPECTED_PRIMITIVE_NAMES_V1)
    assert len(manifest["primitives"]) == len(EXPECTED_PRIMITIVE_NAMES_V1)


def test_required_descriptor_fields_are_declared() -> None:
    assert set(REQUIRED_DESCRIPTOR_FIELDS_V1) == {
        "primitive_name",
        "family",
        "input_type",
        "output_type",
        "preconditions",
        "effect_summary",
        "train_inference_fn_name",
        "executor_fn_name",
        "inverse_or_comparable_relation",
        "rejection_reasons",
        "trace_safe_metadata",
    }
