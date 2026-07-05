from __future__ import annotations

import json

import pytest

from weslr.arc_family_discovery_engine_v1 import FamilyDiscoveryResult, FamilyHypothesis, discover_families_for_task
from weslr.arc_primitive_discovery_engine_v1 import PrimitiveDiscoveryHint, PrimitiveDiscoveryResult, discover_primitives_for_task
from weslr.arc_primitive_registry_v1 import build_arc_primitive_registry_v1


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


def _crop_task() -> list[dict[str, object]]:
    return [{"input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "output": [[1, 1], [1, 1]]}]


def _recolor_task() -> list[dict[str, object]]:
    return [{"input": [[0, 0, 0], [0, 1, 1], [0, 1, 1]], "output": [[0, 0, 0], [0, 2, 2], [0, 2, 2]]}]


def _rotate_task() -> list[dict[str, object]]:
    return [{"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[1, 1, 1], [0, 1, 0], [0, 0, 0]]}]


def _tile_task() -> list[dict[str, object]]:
    return [{"input": [[1, 2], [3, 4]], "output": [[1, 2, 1, 2], [3, 4, 3, 4], [1, 2, 1, 2], [3, 4, 3, 4]]}]


def _scale_task() -> list[dict[str, object]]:
    return [{"input": [[1, 2], [3, 4]], "output": [[1, 1, 2, 2], [1, 1, 2, 2], [3, 3, 4, 4], [3, 3, 4, 4]]}]


def _count_task() -> list[dict[str, object]]:
    return [{"input": [[1, 0, 2], [1, 0, 0], [0, 3, 0]], "output": [[9, 9, 9]]}]


def _crop_recolor_task() -> list[dict[str, object]]:
    return [{"input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "output": [[2, 2], [2, 2]]}]


def _crop_rotate_task() -> list[dict[str, object]]:
    return [{"input": [[1, 1, 0], [1, 0, 0], [0, 0, 0]], "output": [[1, 1], [0, 1]]}]


def _crop_tile_task() -> list[dict[str, object]]:
    return [{"input": [[0, 0, 0, 0], [0, 5, 6, 0], [0, 7, 8, 0], [0, 0, 0, 0]], "output": [[5, 6, 5, 6], [7, 8, 7, 8], [5, 6, 5, 6], [7, 8, 7, 8]]}]


def _recolor_border_task() -> list[dict[str, object]]:
    return [{"input": [[1, 2], [3, 4]], "output": [[9, 9, 9, 9], [9, 5, 6, 9], [9, 7, 8, 9], [9, 9, 9, 9]]}]


def _select_recolor_task() -> list[dict[str, object]]:
    return [{"input": [[1, 1, 0, 0], [1, 1, 0, 2], [0, 0, 0, 2], [3, 3, 3, 2]], "output": [[7, 7], [7, 7]]}]


def _manual_primitive_result(*, accepted_names: tuple[str, ...] = ("recolor_global",), rejected_crop: bool = False, unknown_primitive: bool = False) -> PrimitiveDiscoveryResult:
    accepted = [
        PrimitiveDiscoveryHint(
            primitive_name=name,
            family={
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
                "crop_then_tile": "resize_tile",
                "count_objects_to_line": "count_quantity",
                "foreground_cell_count_to_line": "count_quantity",
                "unique_color_count_to_line": "count_quantity",
                "object_count_to_square": "count_quantity",
                "select_most_frequent_foreground_color": "count_quantity",
                "select_largest_object": "count_quantity",
            }.get(name, "mystery"),
            status="accepted",
            confidence=0.95,
            reason="manual",
            inferred_parameters={},
            source_feature_labels=["manual"],
            trace={"manual": True},
        )
        for name in accepted_names
    ]
    rejected = []
    if rejected_crop:
        rejected.append(
            PrimitiveDiscoveryHint(
                primitive_name="crop_foreground_bbox",
                family="object_bbox",
                status="rejected",
                confidence=0.1,
                reason="manual_reject",
                inferred_parameters={},
                source_feature_labels=["possible_crop"],
                trace={"manual": True},
            )
        )
    if unknown_primitive:
        accepted.append(
            PrimitiveDiscoveryHint(
                primitive_name="ghost_primitive",
                family="mystery",
                status="accepted",
                confidence=0.99,
                reason="manual_unknown",
                inferred_parameters={},
                source_feature_labels=["ghost"],
                trace={"manual": True},
            )
        )
    return PrimitiveDiscoveryResult(
        accepted_hints=accepted,
        rejected_hints=rejected,
        uncertain_hints=[],
        primitive_count=len(accepted) + len(rejected),
        accepted_count=len(accepted),
        rejected_count=len(rejected),
        uncertain_count=0,
        trace={"manual": True},
    )


def test_family_hypothesis_and_result_json_safe_export_and_depth_limit() -> None:
    hypothesis = FamilyHypothesis(
        family_name="object_bbox",
        primitive_chain=("crop_foreground_bbox",),
        status="accepted",
        confidence=0.9,
        reason="test",
        parameters={"mode": "foreground_bbox"},
        train_fit=True,
        rejection_reason=None,
        source_primitive_hints=("crop_foreground_bbox",),
        trace={"decision": "accepted"},
    )
    result = FamilyDiscoveryResult(
        accepted_families=(hypothesis,),
        rejected_families=(),
        uncertain_families=(),
        family_count=1,
        accepted_count=1,
        rejected_count=0,
        uncertain_count=0,
        trace={"synthetic_only": True},
    )
    json.dumps(hypothesis.to_json_safe_dict(), sort_keys=True)
    json.dumps(result.to_json_safe_dict(), sort_keys=True)
    keys = _collect_keys(result.to_json_safe_dict())
    assert "grid" not in keys
    assert "expected_output" not in keys
    with pytest.raises(ValueError, match="primitive_chain_too_long"):
        FamilyHypothesis(
            family_name="too_deep",
            primitive_chain=("a", "b", "c"),
            status="accepted",
            confidence=0.1,
            reason="too_long",
            parameters={},
            train_fit=False,
            rejection_reason=None,
            source_primitive_hints=(),
            trace={},
        )


def test_single_step_family_discovery_covers_core_families() -> None:
    registry = build_arc_primitive_registry_v1()
    crop_result = discover_families_for_task(_crop_task(), _crop_task()[0]["input"], registry=registry)
    assert any(h.family_name == "object_bbox" and h.status == "accepted" for h in crop_result.accepted_families)

    recolor_result = discover_families_for_task(_recolor_task(), _recolor_task()[0]["input"], registry=registry)
    assert any(h.family_name == "color_role" and h.status == "accepted" for h in recolor_result.accepted_families)

    rotate_result = discover_families_for_task(_rotate_task(), _rotate_task()[0]["input"], registry=registry)
    assert any(h.family_name == "shape_geometry" and h.status == "accepted" for h in rotate_result.accepted_families)

    tile_result = discover_families_for_task(_tile_task(), _tile_task()[0]["input"], registry=registry)
    assert any(h.family_name == "resize_tile" and h.status == "accepted" for h in tile_result.accepted_families)

    count_result = discover_families_for_task(_count_task(), _count_task()[0]["input"], registry=registry)
    assert any(h.family_name == "count_quantity" and h.status == "accepted" for h in count_result.accepted_families)


def test_composition_family_discovery_covers_allowed_templates() -> None:
    registry = build_arc_primitive_registry_v1()
    crop_recolor = discover_families_for_task(_crop_recolor_task(), _crop_recolor_task()[0]["input"], primitive_result=_manual_primitive_result(accepted_names=("crop_foreground_bbox", "recolor_global")), registry=registry)
    assert any(h.family_name == "crop_then_recolor" and h.status == "accepted" for h in crop_recolor.accepted_families)

    crop_rotate = discover_families_for_task(_crop_rotate_task(), _crop_rotate_task()[0]["input"], primitive_result=_manual_primitive_result(accepted_names=("crop_foreground_bbox", "rotate_object_90")), registry=registry)
    assert any(h.family_name == "crop_then_rotate_or_reflect" and h.status == "accepted" for h in crop_rotate.accepted_families)

    crop_tile = discover_families_for_task(_crop_tile_task(), _crop_tile_task()[0]["input"], primitive_result=_manual_primitive_result(accepted_names=("crop_foreground_bbox", "tile_grid")), registry=registry)
    assert any(h.family_name == "crop_then_tile" and h.status == "accepted" for h in crop_tile.accepted_families)

    recolor_border = discover_families_for_task(_recolor_border_task(), _recolor_border_task()[0]["input"], primitive_result=_manual_primitive_result(accepted_names=("recolor_global", "add_uniform_border")), registry=registry)
    assert any(h.family_name == "recolor_then_border" and h.status == "accepted" for h in recolor_border.accepted_families)

    select_recolor = discover_families_for_task(_select_recolor_task(), _select_recolor_task()[0]["input"], primitive_result=_manual_primitive_result(accepted_names=("select_largest_object", "recolor_global")), registry=registry)
    assert any(h.family_name == "select_then_recolor" and h.status == "accepted" for h in select_recolor.accepted_families)


def test_rejected_primitives_and_contradictions_block_composition() -> None:
    registry = build_arc_primitive_registry_v1()
    result = discover_families_for_task(_crop_recolor_task(), _crop_recolor_task()[0]["input"], primitive_result=_manual_primitive_result(rejected_crop=True), registry=registry)
    assert any(h.family_name == "crop_then_recolor" and h.status == "rejected" for h in result.rejected_families)

    contradictory = discover_families_for_task([
        {"input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "output": [[2, 2], [2, 2]]},
        {"input": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], "output": [[0, 0, 0, 0], [0, 2, 2, 0], [0, 2, 2, 0], [0, 0, 0, 0]]},
    ], [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]], registry=registry)
    assert any(h.family_name == "crop_then_recolor" and h.status in {"rejected", "uncertain"} for h in contradictory.rejected_families + contradictory.uncertain_families)


def test_registry_and_primitive_discovery_integration_and_unknown_hint_safety() -> None:
    registry = build_arc_primitive_registry_v1()
    primitive_result = discover_primitives_for_task(_crop_task(), _crop_task()[0]["input"], registry=registry)
    from_auto = discover_families_for_task(_crop_task(), _crop_task()[0]["input"], registry=registry)
    manual = discover_families_for_task(_crop_task(), _crop_task()[0]["input"], primitive_result=primitive_result, registry=registry)
    auto_summary = [(h["family_name"], h["status"], h["primitive_chain"]) for h in from_auto.to_json_safe_dict()["accepted_families"] + from_auto.to_json_safe_dict()["rejected_families"] + from_auto.to_json_safe_dict()["uncertain_families"]]
    manual_summary = [(h["family_name"], h["status"], h["primitive_chain"]) for h in manual.to_json_safe_dict()["accepted_families"] + manual.to_json_safe_dict()["rejected_families"] + manual.to_json_safe_dict()["uncertain_families"]]
    assert auto_summary == manual_summary

    unknown = discover_families_for_task(_crop_task(), _crop_task()[0]["input"], primitive_result=_manual_primitive_result(unknown_primitive=True), registry=registry)
    all_primitive_names = {name for family in unknown.to_json_safe_dict()["accepted_families"] + unknown.to_json_safe_dict()["rejected_families"] + unknown.to_json_safe_dict()["uncertain_families"] for name in family["primitive_chain"]}
    assert "ghost_primitive" not in all_primitive_names
    registry_names = {descriptor.primitive_name for descriptor in registry.list_primitives()}
    assert all(name in registry_names for name in all_primitive_names)


def test_rank_is_deterministic_and_safety_checks_reject_bad_grids() -> None:
    registry = build_arc_primitive_registry_v1()
    first = discover_families_for_task(_recolor_task(), _recolor_task()[0]["input"], registry=registry)
    second = discover_families_for_task(_recolor_task(), _recolor_task()[0]["input"], registry=registry)
    assert first.to_json_safe_dict() == second.to_json_safe_dict()

    with pytest.raises(ValueError, match="ragged_grid"):
        discover_families_for_task([{"input": [[0, 1], [0]], "output": [[0]]}], [[0]])
    with pytest.raises(ValueError, match="non_integer_cell"):
        discover_families_for_task([{"input": [[True, 0], [0, 0]], "output": [[0, 0], [0, 0]]}], [[0, 0], [0, 0]])
    with pytest.raises(ValueError, match="invalid_grid"):
        discover_families_for_task([{"input": [], "output": [[0]]}], [[0]])


def test_result_export_contains_no_expected_output_fields() -> None:
    registry = build_arc_primitive_registry_v1()
    result = discover_families_for_task(_crop_task(), _crop_task()[0]["input"], registry=registry)
    exported = result.to_json_safe_dict()
    keys = _collect_keys(exported)
    assert "expected_output" not in keys
    assert "solution" not in keys
    assert "raw_grid" not in keys
    json.dumps(exported, sort_keys=True)
