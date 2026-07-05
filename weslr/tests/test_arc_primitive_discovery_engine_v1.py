from __future__ import annotations

import json

import pytest

from weslr.arc_primitive_discovery_engine_v1 import (
    PrimitiveDiscoveryHint,
    PrimitiveDiscoveryResult,
    discover_primitives_for_task,
)


def _collect_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            keys.add(str(key))
            keys.update(_collect_keys(nested))
    elif isinstance(value, list):
        for item in value:
            keys.update(_collect_keys(item))
    return keys


def _crop_pair() -> dict[str, object]:
    return {
        "input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]],
        "output": [[1, 1], [1, 1]],
    }


def _recolor_pair() -> dict[str, object]:
    return {
        "input": [[0, 0, 0], [0, 1, 1], [0, 1, 1]],
        "output": [[0, 0, 0], [0, 2, 2], [0, 2, 2]],
    }


def _scale_pair() -> dict[str, object]:
    return {
        "input": [[1, 2], [3, 4]],
        "output": [[1, 1, 2, 2], [1, 1, 2, 2], [3, 3, 4, 4], [3, 3, 4, 4]],
    }


def _tile_pair() -> dict[str, object]:
    return {
        "input": [[1, 2], [3, 4]],
        "output": [[1, 2, 1, 2], [3, 4, 3, 4], [1, 2, 1, 2], [3, 4, 3, 4]],
    }


def _border_pair() -> dict[str, object]:
    return {
        "input": [[1, 2], [3, 4]],
        "output": [[8, 8, 8, 8], [8, 1, 2, 8], [8, 3, 4, 8], [8, 8, 8, 8]],
    }


def _count_objects_pair() -> dict[str, object]:
    return {
        "input": [[1, 0, 2], [1, 0, 0], [0, 3, 0]],
        "output": [[9, 9, 9]],
    }


def _foreground_count_pair() -> dict[str, object]:
    return {
        "input": [[1, 0, 2], [1, 0, 0], [0, 3, 0]],
        "output": [[7, 7, 7, 7]],
    }


def _geometry_rotate_pair() -> dict[str, object]:
    return {
        "input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]],
        "output": [[1, 1, 1], [0, 1, 0], [0, 0, 0]],
    }


def _geometry_reflect_pair() -> dict[str, object]:
    return {
        "input": [[1, 0, 0], [1, 1, 1], [0, 0, 0]],
        "output": [[0, 0, 1], [1, 1, 1], [0, 0, 0]],
    }


def test_hint_and_result_json_safe_export() -> None:
    hint = PrimitiveDiscoveryHint(
        primitive_name="crop_foreground_bbox",
        family="object_bbox",
        status="accepted",
        confidence=0.9,
        reason="test",
        inferred_parameters={"mode": "foreground_bbox"},
        source_feature_labels=["possible_crop"],
        trace={"decision": "accepted"},
    )
    result = PrimitiveDiscoveryResult(
        accepted_hints=[hint],
        rejected_hints=[],
        uncertain_hints=[],
        primitive_count=1,
        accepted_count=1,
        rejected_count=0,
        uncertain_count=0,
        trace={"synthetic_only": True},
    )
    json.dumps(hint.to_json_safe_dict(), sort_keys=True)
    json.dumps(result.to_json_safe_dict(), sort_keys=True)


def test_deterministic_ordering_and_no_raw_grids_in_export() -> None:
    result = discover_primitives_for_task([_crop_pair()], _crop_pair()["input"])
    exported = result.to_json_safe_dict()
    assert result.to_json_safe_dict() == discover_primitives_for_task([_crop_pair()], _crop_pair()["input"]).to_json_safe_dict()
    keys = _collect_keys(exported)
    assert "grid" not in keys
    assert "raw_grid" not in keys
    assert "expected_output" not in keys
    assert "solution" not in keys
    assert exported["primitive_count"] == exported["accepted_count"] + exported["rejected_count"] + exported["uncertain_count"]


def test_crop_discovery_accepts_crop_like_and_rejects_same_size() -> None:
    crop_result = discover_primitives_for_task([_crop_pair()], _crop_pair()["input"])
    accepted_names = {hint.primitive_name for hint in crop_result.accepted_hints}
    assert "crop_foreground_bbox" in accepted_names or "crop_largest_object" in accepted_names

    same_size_pair = {"input": [[0, 0], [0, 0]], "output": [[0, 0], [0, 0]]}
    same_result = discover_primitives_for_task([same_size_pair], same_size_pair["input"])
    assert all(hint.primitive_name not in {"crop_foreground_bbox", "crop_largest_object", "crop_selected_color_object"} for hint in same_result.accepted_hints)


def test_recolor_discovery_accepts_palette_change_and_rejects_no_change() -> None:
    recolor_result = discover_primitives_for_task([_recolor_pair()], _recolor_pair()["input"])
    accepted_names = {hint.primitive_name for hint in recolor_result.accepted_hints}
    assert "recolor_global" in accepted_names
    assert any(name in accepted_names for name in {"recolor_background", "recolor_foreground", "recolor_source_color"})

    no_change_pair = {"input": [[0, 1], [1, 0]], "output": [[0, 1], [1, 0]]}
    no_change_result = discover_primitives_for_task([no_change_pair], no_change_pair["input"])
    assert all(hint.primitive_name not in {"recolor_global", "recolor_foreground", "recolor_source_color", "recolor_background", "swap_two_colors"} for hint in no_change_result.accepted_hints)


def test_tile_scale_and_border_discovery() -> None:
    scale_result = discover_primitives_for_task([_scale_pair()], _scale_pair()["input"])
    assert any(hint.primitive_name == "scale_cells_integer" for hint in scale_result.accepted_hints)

    tile_result = discover_primitives_for_task([_tile_pair()], _tile_pair()["input"])
    assert any(hint.primitive_name == "tile_grid" for hint in tile_result.accepted_hints)

    border_result = discover_primitives_for_task([_border_pair()], _border_pair()["input"])
    assert any(hint.primitive_name == "add_uniform_border" for hint in border_result.accepted_hints)

    non_integer_pair = {"input": [[1, 2], [3, 4]], "output": [[1, 1, 2], [1, 1, 2], [3, 3, 4]]}
    non_integer_result = discover_primitives_for_task([non_integer_pair], non_integer_pair["input"])
    assert all(hint.primitive_name != "scale_cells_integer" for hint in non_integer_result.accepted_hints)


def test_count_discovery_accepts_and_rejects_inconsistent_examples() -> None:
    count_result = discover_primitives_for_task([_count_objects_pair()], _count_objects_pair()["input"])
    assert any(hint.primitive_name == "count_objects_to_line" for hint in count_result.accepted_hints)

    foreground_result = discover_primitives_for_task([_foreground_count_pair()], _foreground_count_pair()["input"])
    assert any(hint.primitive_name == "foreground_cell_count_to_line" for hint in foreground_result.accepted_hints)

    inconsistent = discover_primitives_for_task([_count_objects_pair(), _foreground_count_pair()], _count_objects_pair()["input"])
    assert all(hint.primitive_name not in {"count_objects_to_line", "foreground_cell_count_to_line"} for hint in inconsistent.accepted_hints)


def test_geometry_discovery_accepts_rotate_and_reflect_and_rejects_color_only() -> None:
    rotate_result = discover_primitives_for_task([_geometry_rotate_pair()], _geometry_rotate_pair()["input"])
    assert any(hint.primitive_name == "rotate_object_90" for hint in rotate_result.accepted_hints)

    reflect_result = discover_primitives_for_task([_geometry_reflect_pair()], _geometry_reflect_pair()["input"])
    assert any(hint.primitive_name == "reflect_object_vertical" for hint in reflect_result.accepted_hints)

    color_only_pair = _recolor_pair()
    color_only_result = discover_primitives_for_task([color_only_pair], color_only_pair["input"])
    assert all(hint.primitive_name not in {"rotate_object_90", "rotate_object_180", "rotate_object_270", "reflect_object_horizontal", "reflect_object_vertical"} for hint in color_only_result.accepted_hints)
