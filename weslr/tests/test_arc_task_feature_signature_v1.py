from __future__ import annotations

import json

import pytest

from weslr.arc_task_feature_signature_v1 import (
    build_arc_task_feature_signature_v1,
    summarize_arc_grid_v1,
    summarize_arc_object_v1,
    summarize_arc_shape_v1,
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


def _recolor_pair(color_in: int, color_out: int) -> dict[str, object]:
    grid_in = [[0, 0, 0], [0, color_in, color_in], [0, color_in, color_in]]
    grid_out = [[0, 0, 0], [0, color_out, color_out], [0, color_out, color_out]]
    return {"input": grid_in, "output": grid_out}


def test_grid_summary_valid_background_and_foreground_set() -> None:
    grid = [[7, 7, 7], [7, 9, 7], [7, 7, 7]]
    summary = summarize_arc_grid_v1(grid)
    assert summary["height"] == 3
    assert summary["width"] == 3
    assert summary["cell_count"] == 9
    assert summary["inferred_background_color"] == 7
    assert summary["foreground_color_set"] == [9]
    assert summary["foreground_cell_count"] == 1
    assert summary["empty_status"] == "non_empty"


def test_grid_summary_rejects_empty_ragged_and_bool_cells() -> None:
    with pytest.raises(ValueError, match="invalid_grid"):
        summarize_arc_grid_v1([])
    with pytest.raises(ValueError, match="ragged_grid"):
        summarize_arc_grid_v1([[0, 1], [0]])
    with pytest.raises(ValueError, match="non_integer_cell"):
        summarize_arc_grid_v1([[True, 0], [0, 0]])


def test_object_summary_single_and_multiple_objects() -> None:
    single = summarize_arc_object_v1([[0, 0, 0], [0, 1, 1], [0, 1, 1]])
    assert single["object_count"] == 1
    assert single["largest_object_size"] == 4
    assert single["smallest_object_size"] == 4
    assert single["foreground_bbox"] == [1, 1, 2, 2]
    assert single["single_object"] is True
    assert single["multi_object"] is False

    multiple = summarize_arc_object_v1([[1, 0, 0, 2], [1, 1, 0, 2], [0, 0, 0, 0]])
    assert multiple["object_count"] == 2
    assert multiple["object_count_by_color"] == {1: 1, 2: 1}
    assert multiple["largest_object_size"] == 3
    assert multiple["smallest_object_size"] == 2
    assert multiple["foreground_bbox"] == [0, 0, 1, 3]
    assert multiple["objects_touch_border"] is True


def test_shape_summary_uses_compact_tokens_and_symmetry_hints() -> None:
    grid = [[0, 0, 0], [0, 1, 1], [0, 1, 1]]
    summary = summarize_arc_shape_v1(grid)
    assert summary["shape_count"] == 1
    assert len(summary["shape_tokens"]) == 1
    assert summary["shape_tokens"][0].startswith("shape:")
    assert "rotational_180" in summary["object_shapes"][0]["symmetry_hints"]
    assert "cells" not in summary["object_shapes"][0]


def test_same_size_relation_signature() -> None:
    pair = {"input": [[0, 1], [1, 0]], "output": [[0, 1], [1, 0]]}
    task = build_arc_task_feature_signature_v1([pair], [[0, 1], [1, 0]])
    relation = task["train_pair_signatures"][0]["size_relation"]
    assert relation["same_size"] is True
    assert relation["output_size_relation"] == "same"
    assert "possible_recolor" not in relation["candidate_primitive_hint_labels"]


def test_crop_scale_tile_recolor_count_and_border_hints() -> None:
    crop_pair = {"input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "output": [[1, 1], [1, 1]]}
    scale_pair = {"input": [[1, 2], [3, 4]], "output": [[1, 1, 2, 2], [1, 1, 2, 2], [3, 3, 4, 4], [3, 3, 4, 4]]}
    tile_pair = {"input": [[1, 2], [3, 4]], "output": [[1, 2, 1, 2], [3, 4, 3, 4], [1, 2, 1, 2], [3, 4, 3, 4]]}
    recolor_pair = _recolor_pair(1, 2)
    count_pair = {"input": [[1, 0, 2], [0, 0, 0], [3, 0, 0]], "output": [[9, 9, 9]]}
    border_pair = {"input": [[1, 2], [3, 4]], "output": [[8, 8, 8, 8], [8, 1, 2, 8], [8, 3, 4, 8], [8, 8, 8, 8]]}

    crop_relation = build_arc_task_feature_signature_v1([crop_pair], [[0, 0], [0, 0]])["train_pair_signatures"][0]["size_relation"]
    assert crop_relation["crop_like_relation_hint"] is True
    assert "possible_crop" in crop_relation["candidate_primitive_hint_labels"]

    scale_relation = build_arc_task_feature_signature_v1([scale_pair], [[1, 1], [1, 1]])["train_pair_signatures"][0]["size_relation"]
    assert scale_relation["integer_scale_relation"] == {"scale_rows": 2, "scale_cols": 2}
    assert "possible_scale" in scale_relation["candidate_primitive_hint_labels"]

    tile_relation = build_arc_task_feature_signature_v1([tile_pair], [[1, 2], [3, 4]])["train_pair_signatures"][0]["size_relation"]
    assert "possible_tile" in tile_relation["candidate_primitive_hint_labels"]
    assert tile_relation["tile_like_relation_hint"] is True

    recolor_relation = build_arc_task_feature_signature_v1([recolor_pair], [[0, 0, 0], [0, 2, 2], [0, 2, 2]])["train_pair_signatures"][0]["size_relation"]
    assert recolor_relation["palette_changed"] is True
    assert "possible_recolor" in recolor_relation["candidate_primitive_hint_labels"]

    count_relation = build_arc_task_feature_signature_v1([count_pair], [[9, 9, 9]])["train_pair_signatures"][0]["size_relation"]
    assert "possible_count_output" in count_relation["candidate_primitive_hint_labels"]

    border_relation = build_arc_task_feature_signature_v1([border_pair], [[8, 8], [8, 8]])["train_pair_signatures"][0]["size_relation"]
    assert "possible_border" in border_relation["candidate_primitive_hint_labels"]


def test_translate_and_rotate_or_reflect_hints() -> None:
    translate_pair = {"input": [[0, 0, 0, 0], [0, 5, 5, 0], [0, 5, 5, 0], [0, 0, 0, 0]], "output": [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 5, 5], [0, 0, 5, 5]]}
    rotate_pair = {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[1, 1, 1], [0, 1, 0], [0, 0, 0]]}
    translate_relation = build_arc_task_feature_signature_v1([translate_pair], [[0, 0, 0, 0], [0, 5, 5, 0], [0, 5, 5, 0], [0, 0, 0, 0]])["train_pair_signatures"][0]["size_relation"]
    assert "possible_translate" in translate_relation["candidate_primitive_hint_labels"]
    rotate_relation = build_arc_task_feature_signature_v1([rotate_pair], [[1, 0, 0], [1, 1, 0], [1, 0, 0]])["train_pair_signatures"][0]["size_relation"]
    assert "possible_rotate_or_reflect" in rotate_relation["candidate_primitive_hint_labels"]


def test_task_level_intersection_and_contradictions() -> None:
    pair1 = _recolor_pair(1, 2)
    pair2 = _recolor_pair(3, 4)
    signature = build_arc_task_feature_signature_v1([pair1, pair2], [[0, 0, 0], [0, 9, 9], [0, 9, 9]])
    task_level = signature["task_level_signature"]
    assert "possible_recolor" in task_level["possible_primitive_hint_intersection"]
    assert task_level["contradiction_labels"] == []

    crop_pair = {"input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "output": [[1, 1], [1, 1]]}
    scale_pair = {"input": [[1, 2], [3, 4]], "output": [[1, 1, 2, 2], [1, 1, 2, 2], [3, 3, 4, 4], [3, 3, 4, 4]]}
    inconsistent = build_arc_task_feature_signature_v1([crop_pair, scale_pair], [[1, 2], [3, 4]])
    contradictions = inconsistent["task_level_signature"]["contradiction_labels"]
    assert "size_relation_disagreement" in contradictions
    assert "primitive_hint_disagreement" in contradictions


def test_test_input_summary_is_output_free_and_export_is_json_safe() -> None:
    pair = _recolor_pair(1, 2)
    signature = build_arc_task_feature_signature_v1([pair], [[0, 0, 0], [0, 2, 2], [0, 2, 2]])
    test_input_signature = signature["test_input_signature"]
    keys = _collect_keys(test_input_signature)
    assert "output" not in keys
    assert "expected_output" not in keys
    assert "solution" not in keys
    assert "grid" not in keys
    json.dumps(signature)


def test_signature_is_deterministic_across_calls() -> None:
    pair = _recolor_pair(1, 2)
    first = build_arc_task_feature_signature_v1([pair], [[0, 0, 0], [0, 2, 2], [0, 2, 2]])
    second = build_arc_task_feature_signature_v1([pair], [[0, 0, 0], [0, 2, 2], [0, 2, 2]])
    assert first == second
