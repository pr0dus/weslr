from __future__ import annotations

import json

import pytest

import weslr.arc_universal_family_runner_v1 as runner_module
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
    train_pairs = [{"input": [[0, 0, 0], [0, 1, 0], [0, 0, 0]], "output": [[1]]}]
    return {"train_pairs": train_pairs, "test_input": [[0, 0, 0], [0, 1, 0], [0, 0, 0]], "expected_output": [[1]]}


def _recolor_task() -> dict[str, object]:
    train_pairs = [{"input": [[0, 0], [1, 1]], "output": [[0, 0], [2, 2]]}]
    return {"train_pairs": train_pairs, "test_input": [[0, 0], [1, 1]], "expected_output": [[0, 0], [2, 2]]}


def _rotate_task() -> dict[str, object]:
    train_pairs = [{"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[1, 1, 1], [0, 1, 0], [0, 0, 0]]}]
    return {"train_pairs": train_pairs, "test_input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "expected_output": [[1, 1, 1], [0, 1, 0], [0, 0, 0]]}


def _tile_task() -> dict[str, object]:
    train_pairs = [{"input": [[1, 2]], "output": [[1, 2, 1, 2]]}]
    return {"train_pairs": train_pairs, "test_input": [[3, 4]], "expected_output": [[3, 4, 3, 4]]}


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


def _manual_family_result(*, family_name: str, status: str = "accepted", confidence: float = 0.9) -> FamilyDiscoveryResult:
    hypothesis = FamilyHypothesis(
        family_name=family_name,
        primitive_chain=("recolor_global",) if family_name == "color_role" else ("crop_foreground_bbox",),
        status=status,
        confidence=confidence,
        reason="manual",
        parameters={},
        train_fit=status == "accepted",
        rejection_reason=None if status != "rejected" else "manual_reject",
        source_primitive_hints=("recolor_global",),
        trace={"manual": True},
    )
    accepted = (hypothesis,) if status == "accepted" else ()
    rejected = (hypothesis,) if status == "rejected" else ()
    uncertain = (hypothesis,) if status == "uncertain" else ()
    return FamilyDiscoveryResult(
        accepted_families=accepted,
        rejected_families=rejected,
        uncertain_families=uncertain,
        family_count=1,
        accepted_count=len(accepted),
        rejected_count=len(rejected),
        uncertain_count=len(uncertain),
        trace={"synthetic_only": True},
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
    tile = _tile_task()
    count = _count_task()

    crop_result = runner_module.run_universal_family_solver(crop["train_pairs"], crop["test_input"])
    recolor_result = runner_module.run_universal_family_solver(recolor["train_pairs"], recolor["test_input"])
    rotate_result = runner_module.run_universal_family_solver(rotate["train_pairs"], rotate["test_input"])
    tile_result = runner_module.run_universal_family_solver(tile["train_pairs"], tile["test_input"])
    count_result = runner_module.run_universal_family_solver(count["train_pairs"], count["test_input"])

    assert crop_result.attempt_1.family_name == "object_bbox"
    assert crop_result.attempt_1.output == crop["expected_output"]
    assert recolor_result.attempt_1.family_name == "color_role"
    assert recolor_result.attempt_1.output == recolor["expected_output"]
    assert rotate_result.attempt_1.family_name == "shape_geometry"
    assert rotate_result.attempt_1.output == rotate["expected_output"]
    assert tile_result.attempt_1.family_name == "resize_tile"
    assert tile_result.attempt_1.output == tile["expected_output"]
    assert count_result.attempt_1.family_name == "count_quantity"
    assert count_result.attempt_1.output == count["expected_output"]


def test_discovery_gating_and_fallback_control(monkeypatch: pytest.MonkeyPatch) -> None:
    case = _recolor_task()
    monkeypatch.setattr(runner_module, "discover_families_for_task", lambda *args, **kwargs: _manual_family_result(family_name="color_role", status="rejected"))
    rejected_result = runner_module.run_universal_family_solver(case["train_pairs"], case["test_input"])
    assert rejected_result.fallback_used is True
    assert rejected_result.attempt_1.family_name == "fallback"

    monkeypatch.setattr(runner_module, "discover_families_for_task", lambda *args, **kwargs: _manual_family_result(family_name="color_role", status="uncertain", confidence=0.5))
    uncertain_result = runner_module.run_universal_family_solver(case["train_pairs"], case["test_input"])
    assert uncertain_result.fallback_used is True
    assert uncertain_result.attempt_1.family_name == "fallback"

    allowed_result = runner_module.run_universal_family_solver(case["train_pairs"], case["test_input"], enabled_families=["color_role"])
    assert allowed_result.fallback_used is False
    assert allowed_result.attempt_1.family_name == "color_role"


def test_ranking_dedupes_duplicate_outputs_and_keeps_discovered_family_first(monkeypatch: pytest.MonkeyPatch) -> None:
    case = _recolor_task()
    monkeypatch.setattr(runner_module, "discover_families_for_task", lambda *args, **kwargs: _manual_family_result(family_name="color_role", status="accepted", confidence=0.9))

    def fake_packet(*args, **kwargs):
        grid = [[2, 2], [2, 2]]
        attempt = {
            "attempt_id": "dup:1",
            "grid": grid,
            "source_candidate_id": "dup:1",
            "rank": 1,
            "confidence_label": "high",
            "evidence_labels": ["color_role"],
            "leakage_flags": {},
            "metadata": {
                "source_family": "color_role",
                "source_family_label": "global_color_replacement",
                "source_adapter": "arc_agi2_color_role_candidate_adapter_v1",
                "source_kind": "color_role",
                "candidate_score": 30,
                "confidence_label": "high",
                "dedupe_reason": "primary_unique_output",
                "duplicate_family_labels": [],
                "duplicate_source_candidate_ids": [],
            },
        }
        return {"task_id": "dup", "test_input_index": 0, "attempts": [attempt, dict(attempt)], "duplicate_attempt_grid": False, "leakage_flags": {}, "metadata": {"dedupe_count": 0, "used_fallback": False, "enabled_families": ["color_role"]}}

    monkeypatch.setattr(runner_module, "build_arc_agi2_capability_candidate_top2_attempt_packet_v1", fake_packet)
    first = runner_module.run_universal_family_solver(case["train_pairs"], case["test_input"])
    second = runner_module.run_universal_family_solver(case["train_pairs"], case["test_input"])
    assert first.to_json_safe_dict() == second.to_json_safe_dict()
    assert first.attempt_1.family_name == "color_role"
    assert first.dedupe_count >= 1
    assert first.exact_two_output is True
    assert first.attempt_2.family_name == "fallback"


def test_two_step_policy_marks_discovered_not_executable_and_stays_top2() -> None:
    case = {
        "train_pairs": [{"input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "output": [[2, 2], [2, 2]]}],
        "test_input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]],
    }
    result = runner_module.run_universal_family_solver(case["train_pairs"], case["test_input"])
    trace = result.trace
    assert "discovered_not_executable_v1" in json.dumps(trace, sort_keys=True)
    assert result.exact_two_output is True
    assert len(result.family_discovery_summary["accepted_families"]) >= 1


def test_safety_rejects_bad_grids() -> None:
    with pytest.raises(ValueError):
        runner_module.run_universal_family_solver([{"input": [[0, 1], [0]], "output": [[0]]}], [[0]])
    with pytest.raises(ValueError):
        runner_module.run_universal_family_solver([{"input": [[True, 0], [0, 0]], "output": [[0, 0], [0, 0]]}], [[0, 0], [0, 0]])
    with pytest.raises(ValueError):
        runner_module.run_universal_family_solver([{"input": [], "output": [[0]]}], [[0]])


def test_unknown_primitive_hint_is_handled_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    case = _recolor_task()
    monkeypatch.setattr(runner_module, "discover_primitives_for_task", lambda *args, **kwargs: _manual_primitive_result(accepted_names=("recolor_global",), unknown_primitive=True))
    result = runner_module.run_universal_family_solver(case["train_pairs"], case["test_input"])
    blob = json.dumps(result.to_json_safe_dict(), sort_keys=True).lower()
    assert "ghost_primitive" not in blob
    assert result.attempt_1.family_name in {"color_role", "fallback"}
