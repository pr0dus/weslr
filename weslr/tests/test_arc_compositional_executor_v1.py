from __future__ import annotations

import json

from weslr.arc_compositional_executor_v1 import CompositionalExecutorCandidate, execute_compositional_family_hypothesis
from weslr.arc_family_discovery_engine_v1 import FamilyHypothesis


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


def _hypothesis(family_name: str, primitive_chain: tuple[str, str], *, status: str = "accepted", confidence: float = 0.9) -> FamilyHypothesis:
    return FamilyHypothesis(
        family_name=family_name,
        primitive_chain=primitive_chain,
        status=status,
        confidence=confidence,
        reason="synthetic",
        parameters={},
        train_fit=status == "accepted",
        rejection_reason=None if status == "accepted" else "synthetic_reject",
        source_primitive_hints=primitive_chain,
        trace={"synthetic_only": True},
    )


def _crop_recolor_case() -> tuple[list[dict[str, object]], list[list[int]]]:
    train_pairs = [{"input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "output": [[2, 2], [2, 2]]}]
    return train_pairs, [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]


def _rotate_90_case() -> tuple[list[dict[str, object]], list[list[int]]]:
    train_pairs = [{"input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "output": [[1, 1], [1, 1]]}]
    return train_pairs, [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]


def _rotate_180_case() -> tuple[list[dict[str, object]], list[list[int]]]:
    train_pairs = [{"input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "output": [[1, 1], [1, 1]]}]
    return train_pairs, [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]


def _reflect_horizontal_case() -> tuple[list[dict[str, object]], list[list[int]]]:
    train_pairs = [{"input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "output": [[1, 1], [1, 1]]}]
    return train_pairs, [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]


def _reflect_vertical_case() -> tuple[list[dict[str, object]], list[list[int]]]:
    train_pairs = [{"input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "output": [[1, 1], [1, 1]]}]
    return train_pairs, [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]


def _tile_case() -> tuple[list[dict[str, object]], list[list[int]]]:
    train_pairs = [{"input": [[1, 2], [3, 4]], "output": [[1, 2, 1, 2], [3, 4, 3, 4], [1, 2, 1, 2], [3, 4, 3, 4]]}]
    return train_pairs, [[1, 2], [3, 4]]


def _border_case() -> tuple[list[dict[str, object]], list[list[int]]]:
    train_pairs = [{"input": [[1, 2], [3, 4]], "output": [[9, 9, 9, 9], [9, 5, 6, 9], [9, 7, 8, 9], [9, 9, 9, 9]]}]
    return train_pairs, [[1, 2], [3, 4]]


def _select_recolor_case() -> tuple[list[dict[str, object]], list[list[int]]]:
    train_pairs = [{"input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [2, 2, 0, 0]], "output": [[7, 7], [7, 7]]}]
    return train_pairs, [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [2, 2, 0, 0]]


def test_crop_then_recolor_executes_and_is_json_safe() -> None:
    train_pairs, test_input = _crop_recolor_case()
    candidate = execute_compositional_family_hypothesis(train_pairs, test_input, _hypothesis("crop_then_recolor", ("crop_foreground_bbox", "recolor_global")), trace=True)
    assert candidate.train_fit is True
    assert candidate.output == [[2, 2], [2, 2]]
    exported = candidate.to_json_safe_dict()
    json.dumps(exported, sort_keys=True)
    assert "expected_output" not in json.dumps(exported, sort_keys=True).lower()
    assert _collect_keys(exported).isdisjoint({"expected_output", "raw_grid", "solution"})


def test_crop_then_rotate_and_reflect_variants_execute() -> None:
    train_pairs, test_input = _rotate_90_case()
    rotate_90 = execute_compositional_family_hypothesis(train_pairs, test_input, _hypothesis("crop_then_rotate_or_reflect", ("crop_foreground_bbox", "rotate_object_90")), trace=True)
    assert rotate_90.train_fit is True
    assert rotate_90.output == [[1, 1], [1, 1]]

    train_pairs, test_input = _rotate_180_case()
    rotate_180 = execute_compositional_family_hypothesis(train_pairs, test_input, _hypothesis("crop_then_rotate_or_reflect", ("crop_foreground_bbox", "rotate_object_180")), trace=True)
    assert rotate_180.train_fit is True
    assert rotate_180.output == [[1, 1], [1, 1]]

    train_pairs, test_input = _reflect_horizontal_case()
    reflect_horizontal = execute_compositional_family_hypothesis(train_pairs, test_input, _hypothesis("crop_then_rotate_or_reflect", ("crop_foreground_bbox", "reflect_object_horizontal")), trace=True)
    assert reflect_horizontal.train_fit is True
    assert reflect_horizontal.output == [[1, 1], [1, 1]]

    train_pairs, test_input = _reflect_vertical_case()
    reflect_vertical = execute_compositional_family_hypothesis(train_pairs, test_input, _hypothesis("crop_then_rotate_or_reflect", ("crop_foreground_bbox", "reflect_object_vertical")), trace=True)
    assert reflect_vertical.train_fit is True
    assert reflect_vertical.output == [[1, 1], [1, 1]]


def test_crop_then_tile_executes() -> None:
    train_pairs, test_input = _tile_case()
    candidate = execute_compositional_family_hypothesis(train_pairs, test_input, _hypothesis("crop_then_tile", ("crop_foreground_bbox", "tile_grid")), trace=True)
    assert candidate.train_fit is True
    assert candidate.output == [[1, 2, 1, 2], [3, 4, 3, 4], [1, 2, 1, 2], [3, 4, 3, 4]]


def test_recolor_then_border_executes() -> None:
    train_pairs, test_input = _border_case()
    candidate = execute_compositional_family_hypothesis(train_pairs, test_input, _hypothesis("recolor_then_border", ("recolor_global", "add_uniform_border")), trace=True)
    assert candidate.train_fit is True
    assert candidate.output == [[9, 9, 9, 9], [9, 5, 6, 9], [9, 7, 8, 9], [9, 9, 9, 9]]


def test_select_then_recolor_executes() -> None:
    train_pairs, test_input = _select_recolor_case()
    candidate = execute_compositional_family_hypothesis(train_pairs, test_input, _hypothesis("select_then_recolor", ("select_largest_object", "recolor_global")), trace=True)
    assert candidate.train_fit is True
    assert candidate.output == [[7, 7], [7, 7]]


def test_unsupported_and_over_depth_and_inconsistent_train_reject() -> None:
    train_pairs, test_input = _crop_recolor_case()
    unsupported = execute_compositional_family_hypothesis(train_pairs, test_input, _hypothesis("crop_then_recolor", ("recolor_global", "crop_foreground_bbox")), trace=True)
    assert unsupported.train_fit is False
    assert unsupported.rejection_reason is not None

    depth = execute_compositional_family_hypothesis(
        train_pairs,
        test_input,
        {"family_name": "crop_then_recolor", "primitive_chain": ["a", "b", "c"], "status": "accepted", "confidence": 0.9, "reason": "synthetic", "parameters": {}, "train_fit": True, "rejection_reason": None, "source_primitive_hints": ["a", "b", "c"], "trace": {"synthetic_only": True}},
        trace=True,
    )
    assert depth.train_fit is False
    assert depth.rejection_reason == "primitive_chain_too_long"

    inconsistent = execute_compositional_family_hypothesis(
        [
            {"input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "output": [[2, 2], [2, 2]]},
            {"input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "output": [[3, 3], [3, 3]]},
        ],
        test_input,
        _hypothesis("crop_then_recolor", ("crop_foreground_bbox", "recolor_global")),
        trace=True,
    )
    assert inconsistent.train_fit is False
    assert inconsistent.rejection_reason is not None


def test_invalid_grids_reject_safely() -> None:
    train_pairs = [{"input": [[0, 1], [0]], "output": [[0]]}]
    candidate = execute_compositional_family_hypothesis(train_pairs, [[0]], _hypothesis("crop_then_recolor", ("crop_foreground_bbox", "recolor_global")), trace=True)
    assert candidate.train_fit is False
    assert candidate.rejection_reason is not None

    candidate = execute_compositional_family_hypothesis([{"input": [[True, 0], [0, 0]], "output": [[0, 0], [0, 0]]}], [[0, 0], [0, 0]], _hypothesis("crop_then_recolor", ("crop_foreground_bbox", "recolor_global")), trace=True)
    assert candidate.train_fit is False
    assert candidate.rejection_reason is not None

    candidate = execute_compositional_family_hypothesis([{"input": [], "output": [[0]]}], [[0]], _hypothesis("crop_then_recolor", ("crop_foreground_bbox", "recolor_global")), trace=True)
    assert candidate.train_fit is False
    assert candidate.rejection_reason is not None
