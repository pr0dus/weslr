from __future__ import annotations

import json

import pytest

import weslr.arc_universal_family_runner_v1 as runner_module
from weslr.arc_compositional_executor_v1 import CompositionalExecutorCandidate
from weslr.arc_family_discovery_engine_v1 import FamilyDiscoveryResult, FamilyHypothesis
from weslr.arc_primitive_discovery_engine_v1 import PrimitiveDiscoveryHint, PrimitiveDiscoveryResult


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


def _crop_task() -> dict[str, object]:
    train_pairs = [{"input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "output": [[1, 1], [1, 1]]}]
    return {"train_pairs": train_pairs, "test_input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "expected_output": [[1, 1], [1, 1]]}


def _crop_recolor_task() -> dict[str, object]:
    train_pairs = [{"input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "output": [[2, 2], [2, 2]]}]
    return {"train_pairs": train_pairs, "test_input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "expected_output": [[2, 2], [2, 2]]}


def _composition_rotate_task() -> dict[str, object]:
    train_pairs = [{"input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "output": [[1, 1], [1, 1]]}]
    return {"train_pairs": train_pairs, "test_input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "expected_output": [[1, 1], [1, 1]]}


def _recolor_task() -> dict[str, object]:
    train_pairs = [{"input": [[0, 0], [1, 1]], "output": [[0, 0], [2, 2]]}]
    return {"train_pairs": train_pairs, "test_input": [[0, 0], [1, 1]], "expected_output": [[0, 0], [2, 2]]}


def _rotate_task() -> dict[str, object]:
    train_pairs = [{"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[1, 1, 1], [0, 1, 0], [0, 0, 0]]}]
    return {"train_pairs": train_pairs, "test_input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "expected_output": [[1, 1, 1], [0, 1, 0], [0, 0, 0]]}


def _border_task() -> dict[str, object]:
    train_pairs = [{"input": [[1, 2], [3, 4]], "output": [[9, 9, 9, 9], [9, 5, 6, 9], [9, 7, 8, 9], [9, 9, 9, 9]]}]
    return {"train_pairs": train_pairs, "test_input": [[1, 2], [3, 4]], "expected_output": [[9, 9, 9, 9], [9, 5, 6, 9], [9, 7, 8, 9], [9, 9, 9, 9]]}


def _count_task() -> dict[str, object]:
    train_pairs = [{"input": [[0, 1, 0], [0, 0, 2], [0, 0, 0]], "output": [[7, 7]]}]
    return {"train_pairs": train_pairs, "test_input": [[0, 5, 0], [0, 0, 6], [0, 0, 0]], "expected_output": [[7, 7]]}


def _manual_primitive_result(*, accepted_names: tuple[str, ...] = ("recolor_global",), unknown_primitive: bool = False) -> PrimitiveDiscoveryResult:
    family_by_primitive = {
        "crop_foreground_bbox": "object_bbox",
        "crop_largest_object": "object_bbox",
        "crop_selected_color_object": "object_bbox",
        "translate_single_object": "object_bbox",
        "rotate_object_90": "shape_geometry",
        "rotate_object_180": "shape_geometry",
        "rotate_object_270": "shape_geometry",
        "reflect_object_horizontal": "shape_geometry",
        "reflect_object_vertical": "shape_geometry",
        "preserve_shape_translate": "shape_geometry",
        "recolor_global": "color_role",
        "recolor_foreground": "color_role",
        "recolor_source_color": "color_role",
        "recolor_background": "color_role",
        "swap_two_colors": "color_role",
        "tile_grid": "resize_tile",
        "scale_cells_integer": "resize_tile",
        "add_uniform_border": "resize_tile",
        "count_objects_to_line": "count_quantity",
        "foreground_cell_count_to_line": "count_quantity",
        "unique_color_count_to_line": "count_quantity",
        "object_count_to_square": "count_quantity",
        "select_most_frequent_foreground_color": "count_quantity",
        "select_largest_object": "count_quantity",
    }
    accepted = [
        PrimitiveDiscoveryHint(
            primitive_name=name,
            family=family_by_primitive.get(name, "mystery"),
            status="accepted",
            confidence=0.95,
            reason="manual",
            inferred_parameters={},
            source_feature_labels=["manual"],
            trace={"manual": True},
        )
        for name in accepted_names
    ]
    if unknown_primitive:
        accepted.append(
            PrimitiveDiscoveryHint(
                primitive_name="ghost_primitive",
                family="mystery",
                status="accepted",
                confidence=0.99,
                reason="manual_unknown",
                inferred_parameters={},
                source_feature_labels=["manual_unknown"],
                trace={"manual": True},
            )
        )
    return PrimitiveDiscoveryResult(
        accepted_hints=accepted,
        rejected_hints=[],
        uncertain_hints=[],
        primitive_count=len(accepted),
        accepted_count=len(accepted),
        rejected_count=0,
        uncertain_count=0,
        trace={"synthetic_only": True},
    )


def _family_result(*hypotheses: FamilyHypothesis) -> FamilyDiscoveryResult:
    accepted = tuple(h for h in hypotheses if h.status == "accepted")
    rejected = tuple(h for h in hypotheses if h.status == "rejected")
    uncertain = tuple(h for h in hypotheses if h.status == "uncertain")
    return FamilyDiscoveryResult(
        accepted_families=accepted,
        rejected_families=rejected,
        uncertain_families=uncertain,
        family_count=len(hypotheses),
        accepted_count=len(accepted),
        rejected_count=len(rejected),
        uncertain_count=len(uncertain),
        trace={"synthetic_only": True},
    )


def _hypothesis(family_name: str, primitive_chain: tuple[str, str], *, status: str = "accepted", confidence: float = 0.9) -> FamilyHypothesis:
    return FamilyHypothesis(
        family_name=family_name,
        primitive_chain=primitive_chain,
        status=status,
        confidence=confidence,
        reason="manual",
        parameters={},
        train_fit=status == "accepted",
        rejection_reason=None if status == "accepted" else "manual_reject",
        source_primitive_hints=primitive_chain,
        trace={"manual": True},
    )


def test_result_json_safe_export_exact_two_and_deterministic() -> None:
    case = _crop_task()
    result = runner_module.run_universal_family_solver(case["train_pairs"], case["test_input"])
    exported = result.to_json_safe_dict()
    json.dumps(exported, sort_keys=True)
    assert exported["exact_two_output"] is True
    assert exported["candidate_count"] == 2
    keys = _collect_keys(exported)
    assert "expected_output" not in keys
    assert "raw_grid" not in keys
    assert "solution" not in keys
    blob = json.dumps(exported, sort_keys=True).lower()
    assert "train_pairs" not in blob
    assert "expected_output" not in blob
    repeat = runner_module.run_universal_family_solver(case["train_pairs"], case["test_input"])
    assert repeat.to_json_safe_dict() == exported


def test_single_step_family_execution_routes_through_aggregator() -> None:
    crop = _crop_task()
    recolor = _recolor_task()
    rotate = _rotate_task()
    count = _count_task()
    crop_result = runner_module.run_universal_family_solver(crop["train_pairs"], crop["test_input"])
    recolor_result = runner_module.run_universal_family_solver(recolor["train_pairs"], recolor["test_input"])
    rotate_result = runner_module.run_universal_family_solver(rotate["train_pairs"], rotate["test_input"])
    count_result = runner_module.run_universal_family_solver(count["train_pairs"], count["test_input"])
    assert crop_result.attempt_1.family_name == "object_bbox"
    assert crop_result.attempt_1.output == crop["expected_output"]
    assert recolor_result.attempt_1.family_name == "color_role"
    assert recolor_result.attempt_1.output == recolor["expected_output"]
    assert rotate_result.attempt_1.family_name == "shape_geometry"
    assert rotate_result.attempt_1.output == rotate["expected_output"]
    assert count_result.attempt_1.family_name == "count_quantity"
    assert count_result.attempt_1.output == count["expected_output"]


def test_crop_recolor_and_rotate_and_border_compositions_execute_first(monkeypatch: pytest.MonkeyPatch) -> None:
    crop = _crop_recolor_task()
    rotate = _composition_rotate_task()
    border = _border_task()
    monkeypatch.setattr(
        runner_module,
        "discover_families_for_task",
        lambda *args, **kwargs: _family_result(_hypothesis("crop_then_recolor", ("crop_foreground_bbox", "recolor_global"))),
    )
    crop_result = runner_module.run_universal_family_solver(crop["train_pairs"], crop["test_input"])
    assert crop_result.attempt_1.family_name == "crop_then_recolor"
    assert crop_result.attempt_1.output == crop["expected_output"]
    assert "executed_composition_families" in crop_result.trace
    assert "composition_execution_rejections" not in crop_result.trace or not crop_result.trace["composition_execution_rejections"]

    monkeypatch.setattr(
        runner_module,
        "discover_families_for_task",
        lambda *args, **kwargs: _family_result(_hypothesis("crop_then_rotate_or_reflect", ("crop_foreground_bbox", "rotate_object_90"))),
    )
    rotate_result = runner_module.run_universal_family_solver(rotate["train_pairs"], rotate["test_input"])
    assert rotate_result.attempt_1.family_name == "crop_then_rotate_or_reflect"
    assert rotate_result.attempt_1.output == rotate["expected_output"]
    assert "executed_composition_families" in rotate_result.trace

    monkeypatch.setattr(
        runner_module,
        "discover_families_for_task",
        lambda *args, **kwargs: _family_result(_hypothesis("recolor_then_border", ("recolor_global", "add_uniform_border"))),
    )
    border_result = runner_module.run_universal_family_solver(border["train_pairs"], border["test_input"])
    assert border_result.attempt_1.family_name == "recolor_then_border"
    assert border_result.attempt_1.output == border["expected_output"]
    assert "executed_composition_families" in border_result.trace


def test_composition_execution_failure_falls_back_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    case = _recolor_task()
    monkeypatch.setattr(
        runner_module,
        "discover_families_for_task",
        lambda *args, **kwargs: _family_result(_hypothesis("crop_then_recolor", ("crop_foreground_bbox", "recolor_global"))),
    )
    monkeypatch.setattr(
        runner_module,
        "execute_compositional_family_hypotheses",
        lambda *args, **kwargs: [CompositionalExecutorCandidate(family_name="crop_then_recolor", primitive_chain=("crop_foreground_bbox", "recolor_global"), output=None, confidence=0.0, train_fit=False, trace={"rejection_reason": "forced_failure"}, rejection_reason="forced_failure")],
    )
    result = runner_module.run_universal_family_solver(case["train_pairs"], case["test_input"])
    assert result.fallback_used is True
    assert result.attempt_1.family_name == "fallback"
    assert result.exact_two_output is True


def test_deterministic_ordering_and_trace_stays_metadata_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    case = _recolor_task()
    monkeypatch.setattr(
        runner_module,
        "discover_families_for_task",
        lambda *args, **kwargs: _family_result(_hypothesis("select_then_recolor", ("select_largest_object", "recolor_global"))),
    )
    first = runner_module.run_universal_family_solver(case["train_pairs"], case["test_input"])
    second = runner_module.run_universal_family_solver(case["train_pairs"], case["test_input"])
    assert first.to_json_safe_dict() == second.to_json_safe_dict()
    blob = json.dumps(first.to_json_safe_dict(), sort_keys=True).lower()
    assert "expected_output" not in blob
    assert "raw_grid" not in blob
    assert "train_pairs" not in blob


def test_unknown_primitive_hint_is_handled_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    case = _recolor_task()
    monkeypatch.setattr(runner_module, "discover_primitives_for_task", lambda *args, **kwargs: _manual_primitive_result(accepted_names=("recolor_global",), unknown_primitive=True))
    result = runner_module.run_universal_family_solver(case["train_pairs"], case["test_input"])
    blob = json.dumps(result.to_json_safe_dict(), sort_keys=True).lower()
    assert "ghost_primitive" not in blob
    assert result.attempt_1.family_name in {"color_role", "fallback"}
