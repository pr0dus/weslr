from __future__ import annotations

import pytest

from weslr.arc_shape_geometry_v1 import (
    canonical_shape_signature_v1,
    compare_shape_signatures_independent_of_position_v1,
    infer_shape_geometry_hypotheses_v1,
    reflect_object_mask_v1,
    rebuild_object_into_background_grid_v1,
    rotate_object_mask_v1,
    solve_shape_geometry_task,
)


def _rotate_90_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[1, 1, 1], [0, 1, 0], [0, 0, 0]]},
        {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[1, 1, 1], [0, 1, 0], [0, 0, 0]]},
    ]
    return {"task_id": "rotate_90_case", "train_pairs": train_pairs, "test_input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "expected_output": [[1, 1, 1], [0, 1, 0], [0, 0, 0]]}


def _rotate_180_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 1, 0], [1, 0, 0], [0, 0, 0]], "output": [[0, 1, 0], [1, 1, 0], [0, 0, 0]]},
        {"input": [[1, 1, 0], [1, 0, 0], [0, 0, 0]], "output": [[0, 1, 0], [1, 1, 0], [0, 0, 0]]},
    ]
    return {"task_id": "rotate_180_case", "train_pairs": train_pairs, "test_input": [[1, 1, 0], [1, 0, 0], [0, 0, 0]], "expected_output": [[0, 1, 0], [1, 1, 0], [0, 0, 0]]}


def _rotate_270_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[0, 1, 0], [1, 1, 1], [0, 0, 0]]},
        {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[0, 1, 0], [1, 1, 1], [0, 0, 0]]},
    ]
    return {"task_id": "rotate_270_case", "train_pairs": train_pairs, "test_input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "expected_output": [[0, 1, 0], [1, 1, 1], [0, 0, 0]]}


def _reflect_horizontal_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[1, 0, 0], [1, 1, 0], [1, 0, 0]]},
        {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[1, 0, 0], [1, 1, 0], [1, 0, 0]]},
    ]
    return {"task_id": "reflect_horizontal_case", "train_pairs": train_pairs, "test_input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "expected_output": [[1, 0, 0], [1, 1, 0], [1, 0, 0]]}


def _reflect_vertical_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[0, 1, 0], [1, 1, 0], [0, 1, 0]]},
        {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[0, 1, 0], [1, 1, 0], [0, 1, 0]]},
    ]
    return {"task_id": "reflect_vertical_case", "train_pairs": train_pairs, "test_input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "expected_output": [[0, 1, 0], [1, 1, 0], [0, 1, 0]]}


def _translation_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 0, 0, 0], [1, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]], "output": [[0, 0, 0, 0], [0, 1, 0, 0], [0, 1, 1, 0], [0, 1, 0, 0]]},
        {"input": [[1, 0, 0, 0], [1, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]], "output": [[0, 0, 0, 0], [0, 1, 0, 0], [0, 1, 1, 0], [0, 1, 0, 0]]},
    ]
    return {"task_id": "translation_case", "train_pairs": train_pairs, "test_input": [[1, 0, 0, 0], [1, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]], "expected_output": [[0, 0, 0, 0], [0, 1, 0, 0], [0, 1, 1, 0], [0, 1, 0, 0]]}


def test_shape_signature_invariant_to_translation() -> None:
    first = canonical_shape_signature_v1([[2, 2], [2, 3], [3, 2]])
    second = canonical_shape_signature_v1([[0, 0], [0, 1], [1, 0]])
    assert first == second
    assert compare_shape_signatures_independent_of_position_v1([[2, 2], [2, 3], [3, 2]], [[0, 0], [0, 1], [1, 0]]) is True


def test_rotate_and_reflect_mask_helpers() -> None:
    cells = [(0, 0), (1, 0), (1, 1), (2, 0)]
    assert rotate_object_mask_v1(cells, 1) == [(0, 0), (0, 1), (0, 2), (1, 1)]
    assert rotate_object_mask_v1(cells, 2) == [(0, 1), (1, 0), (1, 1), (2, 1)]
    assert rotate_object_mask_v1(cells, 3) == [(0, 1), (1, 0), (1, 1), (1, 2)]
    assert reflect_object_mask_v1(cells, "horizontal") == [(0, 0), (1, 0), (1, 1), (2, 0)]
    assert reflect_object_mask_v1(cells, "vertical") == [(0, 1), (1, 0), (1, 1), (2, 1)]


def test_rebuild_object_into_background_grid() -> None:
    rebuilt = rebuild_object_into_background_grid_v1([(0, 0), (0, 1), (1, 0)], color=4, background_value=0)
    assert rebuilt == [[4, 4], [4, 0]]


def test_rotate_90_synthetic_task() -> None:
    case = _rotate_90_case()
    candidates = solve_shape_geometry_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "rotate_90_single_object"
    assert candidates[0]["output"] == case["expected_output"]


def test_rotate_180_synthetic_task() -> None:
    case = _rotate_180_case()
    candidates = solve_shape_geometry_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "rotate_180_single_object"
    assert candidates[0]["output"] == case["expected_output"]


def test_rotate_270_synthetic_task() -> None:
    case = _rotate_270_case()
    candidates = solve_shape_geometry_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "rotate_270_single_object"
    assert candidates[0]["output"] == case["expected_output"]


def test_reflect_horizontal_synthetic_task() -> None:
    case = _reflect_horizontal_case()
    candidates = solve_shape_geometry_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "reflect_horizontal_single_object"
    assert candidates[0]["output"] == case["expected_output"]


def test_reflect_vertical_synthetic_task() -> None:
    case = _reflect_vertical_case()
    candidates = solve_shape_geometry_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "reflect_vertical_single_object"
    assert candidates[0]["output"] == case["expected_output"]


def test_translation_synthetic_task() -> None:
    case = _translation_case()
    candidates = solve_shape_geometry_task(case["train_pairs"], case["test_input"])
    assert candidates[0]["family"] == "translate_single_object"
    assert candidates[0]["output"] == case["expected_output"]


def test_inconsistent_train_transforms_are_rejected() -> None:
    train_pairs = [
        {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[1, 1, 1], [0, 1, 0], [0, 0, 0]]},
        {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[0, 0, 1], [0, 1, 1], [1, 0, 0]]},
    ]
    assert solve_shape_geometry_task(train_pairs, [[1, 0, 0], [1, 1, 0], [1, 0, 0]]) == []


def test_ambiguous_multiple_objects_are_rejected() -> None:
    train_pairs = [{"input": [[1, 0, 2], [1, 0, 2], [0, 0, 0]], "output": [[0, 1, 2], [0, 1, 2], [0, 0, 0]]}]
    assert solve_shape_geometry_task(train_pairs, [[0, 1, 2], [0, 1, 2], [0, 0, 0]]) == []


def test_shape_changing_output_is_rejected() -> None:
    train_pairs = [{"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[1, 1, 1], [1, 0, 1], [1, 1, 1]]}]
    assert solve_shape_geometry_task(train_pairs, [[1, 0, 0], [1, 1, 0], [1, 0, 0]]) == []


def test_ragged_and_bool_grids_are_rejected() -> None:
    with pytest.raises(ValueError, match="ragged_grid"):
        solve_shape_geometry_task([{"input": [[1, 0], [1]], "output": [[1, 0], [1, 0]]}], [[1, 0], [1, 0]])
    with pytest.raises(ValueError, match="non_integer_cell"):
        solve_shape_geometry_task([{"input": [[True, 0], [0, 0]], "output": [[1, 0], [0, 0]]}], [[1, 0], [0, 0]])


def test_infer_shape_geometry_hypotheses_returns_ranked_candidates() -> None:
    case = _rotate_90_case()
    candidates = infer_shape_geometry_hypotheses_v1(case["train_pairs"], case["test_input"])
    assert candidates
    assert candidates[0].family == "rotate_90_single_object"
    assert candidates[0].train_fit is True
