from __future__ import annotations

import pytest

from weslr.arc_resize_tile_canvas_v1 import (
    grid_dimensions_v1,
    infer_resize_tile_hypotheses_v1,
    output_size_relation_v1,
    solve_resize_tile_task,
)


def _tile_horizontal_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 2]], "output": [[1, 2, 1, 2]]},
        {"input": [[3, 4]], "output": [[3, 4, 3, 4]]},
    ]
    return {"task_id": "tile_horizontal", "train_pairs": train_pairs, "test_input": [[5, 6]], "expected_output": [[5, 6, 5, 6]]}


def _tile_vertical_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1], [2]], "output": [[1], [2], [1], [2]]},
        {"input": [[3], [4]], "output": [[3], [4], [3], [4]]},
    ]
    return {"task_id": "tile_vertical", "train_pairs": train_pairs, "test_input": [[5], [6]], "expected_output": [[5], [6], [5], [6]]}


def _tile_2x2_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 2], [3, 4]], "output": [[1, 2, 1, 2], [3, 4, 3, 4], [1, 2, 1, 2], [3, 4, 3, 4]]},
        {"input": [[5, 6], [7, 8]], "output": [[5, 6, 5, 6], [7, 8, 7, 8], [5, 6, 5, 6], [7, 8, 7, 8]]},
    ]
    return {"task_id": "tile_2x2", "train_pairs": train_pairs, "test_input": [[9, 1], [2, 3]], "expected_output": [[9, 1, 9, 1], [2, 3, 2, 3], [9, 1, 9, 1], [2, 3, 2, 3]]}


def _scale_2x_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 2], [3, 4]], "output": [[1, 1, 2, 2], [1, 1, 2, 2], [3, 3, 4, 4], [3, 3, 4, 4]]},
        {"input": [[5, 6], [7, 8]], "output": [[5, 5, 6, 6], [5, 5, 6, 6], [7, 7, 8, 8], [7, 7, 8, 8]]},
    ]
    return {"task_id": "scale_2x", "train_pairs": train_pairs, "test_input": [[9, 1], [2, 3]], "expected_output": [[9, 9, 1, 1], [9, 9, 1, 1], [2, 2, 3, 3], [2, 2, 3, 3]]}


def _border_padding_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 1], [1, 1]], "output": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]},
        {"input": [[2, 2], [2, 2]], "output": [[0, 0, 0, 0], [0, 2, 2, 0], [0, 2, 2, 0], [0, 0, 0, 0]]},
    ]
    return {"task_id": "border_padding", "train_pairs": train_pairs, "test_input": [[3, 3], [3, 3]], "expected_output": [[0, 0, 0, 0], [0, 3, 3, 0], [0, 3, 3, 0], [0, 0, 0, 0]]}


def _crop_then_tile_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 1, 0], [0, 1, 1, 0]], "output": [[1, 1, 1, 1], [1, 1, 1, 1]]},
        {"input": [[0, 2, 2, 0], [0, 2, 2, 0]], "output": [[2, 2, 2, 2], [2, 2, 2, 2]]},
    ]
    return {"task_id": "crop_then_tile", "train_pairs": train_pairs, "test_input": [[0, 3, 3, 0], [0, 3, 3, 0]], "expected_output": [[3, 3, 3, 3], [3, 3, 3, 3]]}


def test_dimensions_and_size_relation_helpers() -> None:
    assert grid_dimensions_v1([[1, 2], [3, 4]]) == (2, 2)
    relation = output_size_relation_v1([[1, 2], [3, 4]], [[1, 2, 1, 2], [3, 4, 3, 4], [1, 2, 1, 2], [3, 4, 3, 4]])
    assert relation["height_ratio"] == 2
    assert relation["width_ratio"] == 2


def test_whole_input_tile_horizontal() -> None:
    case = _tile_horizontal_case()
    candidates = solve_resize_tile_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "tile_repeat"
    assert candidates[0]["output"] == case["expected_output"]


def test_whole_input_tile_vertical() -> None:
    case = _tile_vertical_case()
    candidates = solve_resize_tile_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "tile_repeat"
    assert candidates[0]["output"] == case["expected_output"]


def test_whole_input_tile_2x2() -> None:
    case = _tile_2x2_case()
    candidates = solve_resize_tile_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "tile_repeat"
    assert candidates[0]["output"] == case["expected_output"]


def test_integer_scale_2x() -> None:
    case = _scale_2x_case()
    candidates = solve_resize_tile_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "integer_scale"
    assert candidates[0]["output"] == case["expected_output"]


def test_border_padding() -> None:
    case = _border_padding_case()
    candidates = solve_resize_tile_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "border_padding"
    assert candidates[0]["output"] == case["expected_output"]


def test_crop_then_tile() -> None:
    case = _crop_then_tile_case()
    candidates = solve_resize_tile_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "crop_then_tile"
    assert candidates[0]["output"] == case["expected_output"]


def test_reject_inconsistent_train_pairs() -> None:
    train_pairs = [
        {"input": [[1, 2]], "output": [[1, 2, 1, 2]]},
        {"input": [[3, 4]], "output": [[3, 4, 3, 4, 3, 4]]},
    ]
    assert solve_resize_tile_task(train_pairs, [[5, 6]]) == []


def test_reject_ragged_and_bool_grids() -> None:
    with pytest.raises(ValueError, match="ragged_grid"):
        solve_resize_tile_task([{"input": [[1, 2], [1]], "output": [[1, 2], [1, 2]]}], [[1, 2], [1, 2]])
    with pytest.raises(ValueError, match="non_integer_cell"):
        solve_resize_tile_task([{"input": [[True, 2], [1, 2]], "output": [[1, 2], [1, 2]]}], [[1, 2], [1, 2]])


def test_infer_resize_tile_hypotheses_returns_ranked_candidates() -> None:
    case = _tile_horizontal_case()
    candidates = infer_resize_tile_hypotheses_v1(case["train_pairs"], case["test_input"])
    assert candidates
    assert candidates[0].family == "tile_repeat"
    assert candidates[0].train_fit is True
