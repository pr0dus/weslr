from __future__ import annotations

import pytest

from weslr.arc_object_extraction_v1 import (
    crop_grid_to_bbox_v1,
    crop_selected_color_object_v1,
    crop_to_foreground_bbox_v1,
    crop_to_largest_object_bbox_v1,
    extract_objects_v1,
    infer_background_value_v1,
    translate_object_v1,
    validate_grid_v1,
)


def test_single_object_extraction() -> None:
    grid = [[0, 0, 0], [0, 1, 1], [0, 1, 1]]
    result = extract_objects_v1(grid)
    assert result["background_value"] == 0
    assert result["object_count"] == 1
    obj = result["objects"][0]
    assert obj["bbox"] == [1, 1, 2, 2]
    assert obj["size"] == 4
    assert obj["canonical_shape"] == [[0, 0], [0, 1], [1, 0], [1, 1]]


def test_two_separated_objects_same_color_are_separate_components() -> None:
    grid = [[1, 0, 0, 1], [1, 0, 0, 1], [0, 0, 0, 0]]
    result = extract_objects_v1(grid, background_value=0)
    assert result["object_count"] == 2
    assert [obj["bbox"] for obj in result["objects"]] == [[0, 0, 1, 0], [0, 3, 1, 3]]
    assert {obj["color"] for obj in result["objects"]} == {1}


def test_two_separated_objects_different_colors_are_separate_components() -> None:
    grid = [[2, 0, 0, 3], [2, 0, 0, 3], [0, 0, 0, 0]]
    result = extract_objects_v1(grid, background_value=0)
    assert result["object_count"] == 2
    assert {obj["color"] for obj in result["objects"]} == {2, 3}


def test_object_touching_edge_is_extracted() -> None:
    grid = [[4, 4, 0], [0, 4, 0], [0, 0, 0]]
    result = extract_objects_v1(grid, background_value=0)
    assert result["objects"][0]["touches_boundary"] is True


def test_object_with_hole_is_marked() -> None:
    grid = [
        [0, 0, 0, 0, 0],
        [0, 5, 5, 5, 0],
        [0, 5, 0, 5, 0],
        [0, 5, 5, 5, 0],
        [0, 0, 0, 0, 0],
    ]
    result = extract_objects_v1(grid)
    obj = next(obj for obj in result["objects"] if obj["color"] == 5)
    assert obj["has_hole"] is True


def test_background_is_inferred_by_frequency() -> None:
    grid = [[7, 7, 7], [7, 9, 7], [7, 7, 7]]
    assert infer_background_value_v1(validate_grid_v1(grid)) == 7


def test_bool_cells_are_rejected() -> None:
    with pytest.raises(ValueError, match="non_integer_cell"):
        extract_objects_v1([[True, 0], [0, 0]])


def test_ragged_grids_are_rejected() -> None:
    with pytest.raises(ValueError, match="ragged_grid"):
        extract_objects_v1([[0, 1], [0]])


def test_crop_helpers_work() -> None:
    grid = [[0, 0, 0], [0, 6, 6], [0, 6, 6]]
    assert crop_grid_to_bbox_v1(grid, [1, 1, 2, 2]) == [[6, 6], [6, 6]]
    assert crop_to_foreground_bbox_v1(grid) == [[6, 6], [6, 6]]
    assert crop_to_largest_object_bbox_v1(grid) == [[6, 6], [6, 6]]
    assert crop_selected_color_object_v1(grid, color=6) == [[6, 6], [6, 6]]


def test_translation_helper_preserves_shape_and_color() -> None:
    grid = [[0, 0, 0, 0], [0, 8, 8, 0], [0, 8, 8, 0], [0, 0, 0, 0]]
    translated = translate_object_v1(grid, delta_row=1, delta_col=1)
    assert translated == [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 8, 8], [0, 0, 8, 8]]


def test_translation_out_of_bounds_rejected() -> None:
    grid = [[0, 9], [0, 0]]
    with pytest.raises(ValueError, match="translation_out_of_bounds"):
        translate_object_v1(grid, delta_row=-1, delta_col=0)
