from __future__ import annotations

import pytest

from weslr.arc_count_quantity_relations_v1 import (
    count_color_histogram_v1,
    count_column_foreground_counts_v1,
    count_connected_components_v1,
    count_foreground_cells_v1,
    count_foreground_objects_v1,
    count_objects_by_color_v1,
    count_quantity_summary_v1,
    count_row_foreground_counts_v1,
    count_unique_foreground_colors_v1,
    grid_height_v1,
    grid_width_v1,
    infer_background_value_strict_v1,
    largest_object_size_v1,
    smallest_object_size_v1,
    solve_count_quantity_task,
)


def _object_count_line_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 0], [0, 0, 2], [0, 0, 0]], "output": [[7, 7]]},
        {"input": [[0, 3, 0], [0, 0, 4], [0, 0, 0]], "output": [[7, 7]]},
    ]
    return {"train_pairs": train_pairs, "test_input": [[0, 5, 0], [0, 0, 6], [0, 0, 0]], "expected_output": [[7, 7]]}


def _object_count_vertical_line_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 0], [2, 0, 0], [0, 0, 0]], "output": [[8], [8]]},
        {"input": [[0, 3, 0], [4, 0, 0], [0, 0, 0]], "output": [[8], [8]]},
    ]
    return {"train_pairs": train_pairs, "test_input": [[0, 5, 0], [6, 0, 0], [0, 0, 0]], "expected_output": [[8], [8]]}


def _foreground_cell_count_line_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 1], [0, 0, 2], [0, 0, 0]], "output": [[6], [6], [6]]},
        {"input": [[0, 3, 3], [0, 0, 4], [0, 0, 0]], "output": [[6], [6], [6]]},
    ]
    return {"train_pairs": train_pairs, "test_input": [[0, 5, 5], [0, 0, 6], [0, 0, 0]], "expected_output": [[6], [6], [6]]}


def _unique_color_count_line_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 0, 1], [0, 2, 0], [0, 0, 0]], "output": [[4, 4]]},
        {"input": [[3, 0, 3], [0, 4, 0], [0, 0, 0]], "output": [[4, 4]]},
    ]
    return {"train_pairs": train_pairs, "test_input": [[5, 0, 5], [0, 6, 0], [0, 0, 0]], "expected_output": [[4, 4]]}


def _object_count_square_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 0], [0, 0, 2], [0, 0, 0]], "output": [[9, 9], [9, 9]]},
        {"input": [[0, 3, 0], [0, 0, 4], [0, 0, 0]], "output": [[9, 9], [9, 9]]},
    ]
    return {"train_pairs": train_pairs, "test_input": [[0, 5, 0], [0, 0, 6], [0, 0, 0]], "expected_output": [[9, 9], [9, 9]]}


def _most_frequent_color_mask_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 1], [0, 1, 2], [0, 0, 0]], "output": [[0, 1, 1], [0, 1, 0], [0, 0, 0]]},
        {"input": [[0, 1, 1], [0, 1, 3], [0, 0, 0]], "output": [[0, 1, 1], [0, 1, 0], [0, 0, 0]]},
    ]
    return {"train_pairs": train_pairs, "test_input": [[0, 1, 1], [0, 1, 4], [0, 0, 0]], "expected_output": [[0, 1, 1], [0, 1, 0], [0, 0, 0]]}


def _largest_object_crop_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 2, 2]], "output": [[1, 1], [1, 1]]},
        {"input": [[0, 3, 3, 0], [0, 3, 3, 0], [0, 0, 4, 4]], "output": [[3, 3], [3, 3]]},
    ]
    return {"train_pairs": train_pairs, "test_input": [[0, 5, 5, 0], [0, 5, 5, 0], [0, 0, 6, 6]], "expected_output": [[5, 5], [5, 5]]}


def test_count_helpers_and_summary() -> None:
    grid = [[0, 1, 0], [2, 0, 0], [0, 0, 3]]
    assert grid_height_v1(grid) == 3
    assert grid_width_v1(grid) == 3
    assert infer_background_value_strict_v1(grid) == 0
    assert count_color_histogram_v1(grid)[0] == 6
    assert count_foreground_cells_v1(grid) == 3
    assert count_connected_components_v1(grid) == 3
    assert count_foreground_objects_v1(grid) == 3
    assert count_objects_by_color_v1(grid) == {1: 1, 2: 1, 3: 1}
    assert count_unique_foreground_colors_v1(grid) == 3
    assert count_row_foreground_counts_v1(grid) == [1, 1, 1]
    assert count_column_foreground_counts_v1(grid) == [1, 1, 1]
    assert largest_object_size_v1(grid) == 1
    assert smallest_object_size_v1(grid) == 1
    summary = count_quantity_summary_v1(grid)
    assert summary["foreground_object_count"] == 3
    assert summary["foreground_cell_count"] == 3
    assert summary["unique_foreground_color_count"] == 3


def test_reject_ragged_bool_and_ambiguous_background() -> None:
    with pytest.raises(ValueError, match="ragged_grid"):
        count_quantity_summary_v1([[0, 1], [0]])
    with pytest.raises(ValueError, match="non_integer_cell"):
        count_quantity_summary_v1([[True, 1], [0, 0]])
    with pytest.raises(ValueError, match="ambiguous_background"):
        infer_background_value_strict_v1([[0, 1], [1, 0]])


def test_object_count_to_line_family() -> None:
    case = _object_count_line_case()
    candidates = solve_count_quantity_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "object_count_to_line"
    assert candidates[0]["output"] == case["expected_output"]


def test_object_count_to_vertical_line_family() -> None:
    case = _object_count_vertical_line_case()
    candidates = solve_count_quantity_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "object_count_to_line"
    assert candidates[0]["output"] == case["expected_output"]


def test_foreground_cell_count_to_line_family() -> None:
    case = _foreground_cell_count_line_case()
    candidates = solve_count_quantity_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "foreground_cell_count_to_line"
    assert candidates[0]["output"] == case["expected_output"]


def test_unique_color_count_to_line_family() -> None:
    case = _unique_color_count_line_case()
    candidates = solve_count_quantity_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "unique_color_count_to_line"
    assert candidates[0]["output"] == case["expected_output"]


def test_object_count_to_square_family() -> None:
    case = _object_count_square_case()
    candidates = solve_count_quantity_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "object_count_to_square"
    assert candidates[0]["output"] == case["expected_output"]


def test_select_most_frequent_foreground_color_family() -> None:
    case = _most_frequent_color_mask_case()
    candidates = solve_count_quantity_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "select_most_frequent_foreground_color"
    assert candidates[0]["output"] == case["expected_output"]


def test_select_largest_object_family() -> None:
    case = _largest_object_crop_case()
    candidates = solve_count_quantity_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "select_largest_object"
    assert candidates[0]["output"] == case["expected_output"]


def test_reject_inconsistent_train_count_rule() -> None:
    train_pairs = [
        {"input": [[0, 1, 0], [0, 0, 2], [0, 0, 0]], "output": [[7, 7]]},
        {"input": [[0, 3, 0], [0, 0, 4], [0, 5, 0]], "output": [[7, 7]]},
    ]
    assert solve_count_quantity_task(train_pairs, [[0, 1, 0], [0, 0, 2], [0, 0, 0]]) == []


def test_reject_ambiguous_tie_for_most_frequent_color_and_largest_object() -> None:
    tie_color_pairs = [
        {"input": [[0, 1, 2], [0, 0, 0]], "output": [[0, 1, 2], [0, 0, 0]]},
        {"input": [[0, 3, 4], [0, 0, 0]], "output": [[0, 3, 4], [0, 0, 0]]},
    ]
    tie_object_pairs = [
        {"input": [[0, 1, 1, 0], [0, 0, 2, 2]], "output": [[1, 1], [0, 0]]},
        {"input": [[0, 3, 3, 0], [0, 0, 4, 4]], "output": [[3, 3], [0, 0]]},
    ]
    assert solve_count_quantity_task(tie_color_pairs, tie_color_pairs[0]["input"]) == []
    assert solve_count_quantity_task(tie_object_pairs, tie_object_pairs[0]["input"]) == []
