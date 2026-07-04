from __future__ import annotations

import pytest

from weslr.arc_color_role_abstraction_v1 import (
    color_histogram_v1,
    color_positions_v1,
    color_role_summary_v1,
    foreground_color_set_v1,
    infer_background_color_v1,
    infer_color_role_hypotheses_v1,
    solve_color_role_task,
)


def test_background_by_frequency_and_foreground_detection() -> None:
    grid = [[0, 1, 1], [0, 2, 2], [0, 0, 0]]
    assert infer_background_color_v1(grid) == 0
    assert foreground_color_set_v1(grid) == {1, 2}
    assert color_histogram_v1(grid) == {0: 5, 1: 2, 2: 2}
    assert color_positions_v1(grid)[1] == [(0, 1), (0, 2)]
    summary = color_role_summary_v1(grid)
    assert summary["background_color"] == 0
    assert summary["foreground_colors"] == [1, 2]
    assert summary["object_count"] == 2


def test_reject_bool_and_ragged_grids() -> None:
    with pytest.raises(ValueError, match="non_integer_cell"):
        infer_background_color_v1([[True, 0], [0, 0]])
    with pytest.raises(ValueError, match="ragged_grid"):
        color_histogram_v1([[0, 1], [0]])


def test_global_color_replacement_recolors_source_color() -> None:
    train_pairs = [
        {"input": [[0, 1, 0], [0, 1, 0], [0, 0, 0]], "output": [[0, 4, 0], [0, 4, 0], [0, 0, 0]]},
        {"input": [[0, 1, 0], [0, 1, 0], [0, 0, 0]], "output": [[0, 4, 0], [0, 4, 0], [0, 0, 0]]},
    ]
    candidates = solve_color_role_task(train_pairs, [[0, 1, 0], [0, 1, 0], [0, 0, 0]])
    assert candidates[0]["family"] == "object_source_color_recolor"
    assert candidates[0]["output"] == [[0, 4, 0], [0, 4, 0], [0, 0, 0]]


def test_foreground_recolor() -> None:
    train_pairs = [
        {"input": [[0, 1, 2], [0, 1, 2], [0, 0, 0]], "output": [[0, 3, 3], [0, 3, 3], [0, 0, 0]]},
        {"input": [[0, 4, 5], [0, 4, 5], [0, 0, 0]], "output": [[0, 3, 3], [0, 3, 3], [0, 0, 0]]},
    ]
    candidates = solve_color_role_task(train_pairs, [[0, 6, 7], [0, 6, 7], [0, 0, 0]])
    assert candidates[0]["family"] == "foreground_recolor"
    assert candidates[0]["output"] == [[0, 3, 3], [0, 3, 3], [0, 0, 0]]


def test_background_recolor() -> None:
    train_pairs = [
        {"input": [[0, 1, 1], [0, 1, 1], [0, 0, 0]], "output": [[9, 1, 1], [9, 1, 1], [9, 9, 9]]},
        {"input": [[0, 2, 2], [0, 2, 2], [0, 0, 0]], "output": [[9, 2, 2], [9, 2, 2], [9, 9, 9]]},
    ]
    candidates = solve_color_role_task(train_pairs, [[0, 3, 3], [0, 3, 3], [0, 0, 0]])
    assert candidates[0]["family"] == "background_recolor"
    assert candidates[0]["output"] == [[9, 3, 3], [9, 3, 3], [9, 9, 9]]


def test_color_swap() -> None:
    train_pairs = [
        {"input": [[0, 1, 2], [0, 1, 2], [0, 0, 0]], "output": [[0, 2, 1], [0, 2, 1], [0, 0, 0]]},
        {"input": [[0, 1, 2], [0, 1, 2], [0, 0, 0]], "output": [[0, 2, 1], [0, 2, 1], [0, 0, 0]]},
    ]
    candidates = solve_color_role_task(train_pairs, [[0, 1, 2], [0, 1, 2], [0, 0, 0]])
    assert candidates[0]["family"] == "color_swap"
    assert candidates[0]["output"] == [[0, 2, 1], [0, 2, 1], [0, 0, 0]]


def test_inconsistent_train_recolor_is_rejected() -> None:
    train_pairs = [
        {"input": [[0, 1, 0], [0, 1, 0]], "output": [[0, 4, 0], [0, 4, 0]]},
        {"input": [[0, 1, 0], [0, 1, 0]], "output": [[0, 5, 0], [0, 5, 0]]},
    ]
    assert solve_color_role_task(train_pairs, [[0, 1, 0], [0, 1, 0]]) == []


def test_no_change_rule_is_rejected() -> None:
    train_pairs = [
        {"input": [[0, 1, 0], [0, 1, 0]], "output": [[0, 1, 0], [0, 1, 0]]},
        {"input": [[0, 2, 0], [0, 2, 0]], "output": [[0, 2, 0], [0, 2, 0]]},
    ]
    assert infer_color_role_hypotheses_v1(train_pairs, [[0, 1, 0], [0, 1, 0]]) == []


def test_preserve_dimensions() -> None:
    train_pairs = [
        {"input": [[0, 1, 0], [0, 1, 0]], "output": [[0, 4, 0], [0, 4, 0]]},
        {"input": [[0, 2, 0], [0, 2, 0]], "output": [[0, 4, 0], [0, 4, 0]]},
    ]
    candidates = solve_color_role_task(train_pairs, [[0, 3, 0], [0, 3, 0]])
    assert len(candidates[0]["output"]) == 2
    assert len(candidates[0]["output"][0]) == 3
