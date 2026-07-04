from __future__ import annotations

import json
from pathlib import Path

from weslr.arc_object_bbox_solver_v1 import solve_object_bbox_task


def _crop_task() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 0, 0], [0, 1, 1], [0, 1, 1]], "output": [[1, 1], [1, 1]]},
        {"input": [[0, 0, 0, 0], [0, 0, 2, 2], [0, 0, 2, 2], [0, 0, 0, 0]], "output": [[2, 2], [2, 2]]},
    ]
    test_input = [[0, 0, 0], [0, 3, 3], [0, 3, 3]]
    return {"train_pairs": train_pairs, "test_input": test_input}


def _translation_task() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 0, 0, 0], [0, 4, 4, 0], [0, 4, 4, 0], [0, 0, 0, 0]], "output": [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 4, 4], [0, 0, 4, 4]]},
        {"input": [[5, 5, 0, 0], [5, 5, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], "output": [[0, 0, 0, 0], [0, 5, 5, 0], [0, 5, 5, 0], [0, 0, 0, 0]]},
    ]
    test_input = [[0, 0, 0, 0], [0, 6, 6, 0], [0, 6, 6, 0], [0, 0, 0, 0]]
    return {"train_pairs": train_pairs, "test_input": test_input}


def test_solver_finds_bbox_crop_all_foreground() -> None:
    task = _crop_task()
    candidates = solve_object_bbox_task(task["train_pairs"], task["test_input"])
    assert len(candidates) == 1
    assert candidates[0]["family"] == "bbox_crop_all_foreground"
    assert candidates[0]["output"] == [[3, 3], [3, 3]]
    assert candidates[0]["trace"]["train_fit"] is True


def test_solver_finds_translation_single_object() -> None:
    task = _translation_task()
    candidates = solve_object_bbox_task(task["train_pairs"], task["test_input"])
    assert len(candidates) == 1
    assert candidates[0]["family"] == "translation_single_object"
    assert candidates[0]["output"] == [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 6, 6], [0, 0, 6, 6]]
    assert candidates[0]["trace"]["delta_row"] == 1
    assert candidates[0]["trace"]["delta_col"] == 1


def test_solver_rejects_when_train_pairs_disagree() -> None:
    train_pairs = [
        {"input": [[0, 0, 0], [0, 1, 1], [0, 1, 1]], "output": [[1, 1], [1, 1]]},
        {"input": [[0, 0, 0], [0, 2, 2], [0, 2, 2]], "output": [[2, 2]]},
    ]
    test_input = [[0, 0, 0], [0, 3, 3], [0, 3, 3]]
    assert solve_object_bbox_task(train_pairs, test_input) == []


def test_solver_rejects_translation_when_multiple_objects_ambiguous() -> None:
    train_pairs = [
        {"input": [[0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 2], [0, 0, 0, 2]], "output": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 2, 2]]},
    ]
    test_input = [[0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 2], [0, 0, 0, 2]]
    assert solve_object_bbox_task(train_pairs, test_input) == []


def test_solver_trace_remains_metadata_only() -> None:
    task = _crop_task()
    candidates = solve_object_bbox_task(task["train_pairs"], task["test_input"])
    blob = json.dumps([candidate["trace"] for candidate in candidates]).lower()
    assert "expected_output" not in blob
    assert "reference_output" not in blob
    assert "solution_grid" not in blob


def test_solver_exactly_one_candidate_for_solved_family() -> None:
    task = _translation_task()
    candidates = solve_object_bbox_task(task["train_pairs"], task["test_input"])
    assert len(candidates) == 1
