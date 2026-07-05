"""ARC-AGI-2 family discovery engine V1.

Metadata-safe bounded family hypothesis discovery over primitive discovery
outputs and task feature signatures. This module does not emit final ARC
answers, does not run public ARC data, and does not perform open-ended search.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
import json
from typing import Any, Mapping, Sequence

from weslr.arc_color_role_abstraction_v1 import infer_color_role_hypotheses_v1
from weslr.arc_count_quantity_relations_v1 import infer_count_quantity_hypotheses_v1
from weslr.arc_object_bbox_solver_v1 import solve_object_bbox_task
from weslr.arc_object_extraction_v1 import (
    crop_selected_color_object_v1,
    crop_to_foreground_bbox_v1,
    crop_to_largest_object_bbox_v1,
    extract_objects_v1,
    infer_background_value_v1,
    translate_object_v1,
    validate_grid_v1,
)
from weslr.arc_primitive_discovery_engine_v1 import (
    PrimitiveDiscoveryHint,
    PrimitiveDiscoveryResult,
    discover_primitives_for_task,
)
from weslr.arc_primitive_registry_v1 import PrimitiveDescriptor, PrimitiveRegistry, build_arc_primitive_registry_v1
from weslr.arc_resize_tile_canvas_v1 import _pad_grid, _repeat_grid, _tile_grid, infer_resize_tile_hypotheses_v1
from weslr.arc_shape_geometry_v1 import canonical_shape_signature_v1, infer_shape_geometry_hypotheses_v1, reflect_object_mask_v1, rebuild_object_into_background_grid_v1, rotate_object_mask_v1
from weslr.arc_task_feature_signature_v1 import build_arc_task_feature_signature_v1
from weslr.arc_agi2_symmetry_line_candidate_adapter_v1 import solve_symmetry_line_task
from weslr.arc_hole_row_column_v1 import solve_hole_row_column_task
from weslr.arc_marker_copy_v1 import solve_marker_copy_task

SCHEMA_VERSION_V1 = "ArcFamilyDiscoveryEngineV1"
MAX_PRIMITIVE_CHAIN_LENGTH_V1 = 2
HIGH_CONFIDENCE_UNCERTAIN_THRESHOLD_V1 = 0.8

FAMILY_PRIORITY_V1 = {
    "object_bbox": 0,
    "shape_geometry": 1,
    "hole_row_column": 2,
    "marker_copy": 3,
    "color_role": 4,
    "resize_tile": 5,
    "count_quantity": 6,
    "symmetry_line": 7,
    "crop_then_recolor": 8,
    "crop_then_rotate_or_reflect": 9,
    "crop_then_tile": 10,
    "recolor_then_border": 11,
    "select_then_recolor": 12,
}

ALLOWED_COMPOSITION_TEMPLATES_V1 = (
    "crop_then_recolor",
    "crop_then_rotate_or_reflect",
    "crop_then_tile",
    "recolor_then_border",
    "select_then_recolor",
)

PRIMITIVE_TO_FAMILY_TEMPLATE_V1 = {
    # object_bbox
    "crop_foreground_bbox": "object_bbox",
    "crop_largest_object": "object_bbox",
    "crop_selected_color_object": "object_bbox",
    "translate_single_object": "object_bbox",
    # shape_geometry
    "rotate_object_90": "shape_geometry",
    "rotate_object_180": "shape_geometry",
    "rotate_object_270": "shape_geometry",
    "reflect_object_horizontal": "shape_geometry",
    "reflect_object_vertical": "shape_geometry",
    "preserve_shape_translate": "shape_geometry",
    # color_role
    "recolor_global": "color_role",
    "recolor_foreground": "color_role",
    "recolor_source_color": "color_role",
    "recolor_background": "color_role",
    "swap_two_colors": "color_role",
    # resize_tile
    "tile_grid": "resize_tile",
    "scale_cells_integer": "resize_tile",
    "add_uniform_border": "resize_tile",
    "crop_then_tile": "resize_tile",
    # count_quantity
    "count_objects_to_line": "count_quantity",
    "foreground_cell_count_to_line": "count_quantity",
    "unique_color_count_to_line": "count_quantity",
    "object_count_to_square": "count_quantity",
    "select_most_frequent_foreground_color": "count_quantity",
    "select_largest_object": "count_quantity",
}

OBJECT_BBOX_PRIMITIVES_V1 = ("crop_foreground_bbox", "crop_largest_object", "crop_selected_color_object", "translate_single_object")
SHAPE_GEOMETRY_PRIMITIVES_V1 = ("rotate_object_90", "rotate_object_180", "rotate_object_270", "reflect_object_horizontal", "reflect_object_vertical", "preserve_shape_translate")
COLOR_ROLE_PRIMITIVES_V1 = ("recolor_global", "recolor_foreground", "recolor_source_color", "recolor_background", "swap_two_colors")
RESIZE_TILE_PRIMITIVES_V1 = ("tile_grid", "scale_cells_integer", "add_uniform_border", "crop_then_tile")
COUNT_QUANTITY_PRIMITIVES_V1 = ("count_objects_to_line", "foreground_cell_count_to_line", "unique_color_count_to_line", "object_count_to_square", "select_most_frequent_foreground_color", "select_largest_object")

SOLVER_FAMILY_TO_PRIMITIVE_V1 = {
    # object bbox solver families
    "bbox_crop_all_foreground": "crop_foreground_bbox",
    "bbox_crop_largest_object": "crop_largest_object",
    "bbox_crop_selected_color_object": "crop_selected_color_object",
    "translation_single_object": "translate_single_object",
    # shape geometry solver families
    "rotate_90_single_object": "rotate_object_90",
    "rotate_180_single_object": "rotate_object_180",
    "rotate_270_single_object": "rotate_object_270",
    "reflect_horizontal_single_object": "reflect_object_horizontal",
    "reflect_vertical_single_object": "reflect_object_vertical",
    "translate_single_object": "preserve_shape_translate",
    # color role solver families
    "background_recolor": "recolor_background",
    "object_source_color_recolor": "recolor_source_color",
    "foreground_recolor": "recolor_foreground",
    "color_swap": "swap_two_colors",
    "global_color_replacement": "recolor_global",
    # resize/tile solver families
    "crop_foreground_bbox": "crop_foreground_bbox",
    "tile_repeat": "tile_grid",
    "integer_scale": "scale_cells_integer",
    "border_padding": "add_uniform_border",
    "crop_then_tile": "crop_then_tile",
    # count/quantity solver families
    "object_count_to_line": "count_objects_to_line",
    "foreground_cell_count_to_line": "foreground_cell_count_to_line",
    "unique_color_count_to_line": "unique_color_count_to_line",
    "object_count_to_square": "object_count_to_square",
    "select_most_frequent_foreground_color": "select_most_frequent_foreground_color",
    "select_largest_object": "select_largest_object",
}

SINGLE_STEP_FAMILY_ORDER_V1 = (
    "object_bbox",
    "shape_geometry",
    "color_role",
    "resize_tile",
    "count_quantity",
)

COMPOSITION_FAMILY_ORDER_V1 = ALLOWED_COMPOSITION_TEMPLATES_V1


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int)):
        return str(value)
    return default if value == "" else str(value)


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    return _safe_text(value)


def _pair_input(pair: Mapping[str, Any]) -> Any:
    return pair.get("input", pair.get("input_grid"))


def _pair_output(pair: Mapping[str, Any]) -> Any:
    return pair.get("output", pair.get("output_grid"))


def _grid_dimensions(grid: Sequence[Sequence[int]]) -> tuple[int, int]:
    return len(grid), len(grid[0])


def _map_family_name(solver_family: str) -> str:
    return SOLVER_FAMILY_TO_PRIMITIVE_V1.get(_safe_text(solver_family), _safe_text(solver_family))


def _primitive_family_bucket(primitive_name: str) -> str | None:
    return PRIMITIVE_TO_FAMILY_TEMPLATE_V1.get(_safe_text(primitive_name))


def _hint_status_rank(status: str) -> int:
    return {"accepted": 0, "uncertain": 1, "rejected": 2}.get(_safe_text(status), 3)


def _primitive_chain_key(chain: Sequence[str]) -> tuple[str, ...]:
    return tuple(_safe_text(name) for name in chain)


def _sorted_name_list(values: Sequence[str]) -> list[str]:
    return sorted(_safe_text(value) for value in values if _safe_text(value))


def _normalize_primitive_result(primitive_result: Any) -> PrimitiveDiscoveryResult | None:
    if primitive_result is None:
        return None
    if isinstance(primitive_result, PrimitiveDiscoveryResult):
        return primitive_result
    if hasattr(primitive_result, "accepted_hints") and hasattr(primitive_result, "rejected_hints") and hasattr(primitive_result, "uncertain_hints"):
        accepted = list(getattr(primitive_result, "accepted_hints"))
        rejected = list(getattr(primitive_result, "rejected_hints"))
        uncertain = list(getattr(primitive_result, "uncertain_hints"))
        return PrimitiveDiscoveryResult(
            accepted_hints=accepted,
            rejected_hints=rejected,
            uncertain_hints=uncertain,
            primitive_count=int(getattr(primitive_result, "primitive_count", len(accepted) + len(rejected) + len(uncertain))),
            accepted_count=int(getattr(primitive_result, "accepted_count", len(accepted))),
            rejected_count=int(getattr(primitive_result, "rejected_count", len(rejected))),
            uncertain_count=int(getattr(primitive_result, "uncertain_count", len(uncertain))),
            trace=dict(getattr(primitive_result, "trace", {})) if isinstance(getattr(primitive_result, "trace", {}), Mapping) else {},
        )
    return None


def _collect_primitive_hints(primitive_result: PrimitiveDiscoveryResult) -> tuple[dict[str, PrimitiveDiscoveryHint], dict[str, PrimitiveDiscoveryHint], dict[str, PrimitiveDiscoveryHint]]:
    accepted = {hint.primitive_name: hint for hint in primitive_result.accepted_hints if _safe_text(hint.primitive_name)}
    rejected = {hint.primitive_name: hint for hint in primitive_result.rejected_hints if _safe_text(hint.primitive_name)}
    uncertain = {hint.primitive_name: hint for hint in primitive_result.uncertain_hints if _safe_text(hint.primitive_name)}
    return accepted, rejected, uncertain


def _best_hint_for_bucket(
    accepted: Mapping[str, PrimitiveDiscoveryHint],
    uncertain: Mapping[str, PrimitiveDiscoveryHint],
    rejected: Mapping[str, PrimitiveDiscoveryHint],
    primitive_names: Sequence[str],
) -> PrimitiveDiscoveryHint | None:
    candidates: list[PrimitiveDiscoveryHint] = []
    for name in primitive_names:
        if name in accepted:
            candidates.append(accepted[name])
        elif name in uncertain and uncertain[name].confidence >= HIGH_CONFIDENCE_UNCERTAIN_THRESHOLD_V1:
            candidates.append(uncertain[name])
    if candidates:
        return sorted(candidates, key=lambda hint: (_hint_status_rank(hint.status), -float(hint.confidence), _safe_text(hint.primitive_name)))[0]
    return None


def _hint_labels_from_signature(task_signature: Mapping[str, Any]) -> list[str]:
    labels: set[str] = set()
    task_level = task_signature.get("task_level_signature", {})
    if isinstance(task_level, Mapping):
        for key in (
            "consistent_size_relation_labels",
            "consistent_palette_relation_labels",
            "consistent_object_count_relation_labels",
            "consistent_foreground_count_relation_labels",
            "possible_primitive_hint_intersection",
            "contradiction_labels",
        ):
            value = task_level.get(key, [])
            if isinstance(value, Sequence):
                labels.update(_safe_text(item) for item in value)
    for pair_signature in task_signature.get("train_pair_signatures", []):
        if not isinstance(pair_signature, Mapping):
            continue
        labels.update(_safe_text(item) for item in pair_signature.get("size_relation_labels", []))
        labels.update(_safe_text(item) for item in pair_signature.get("palette_relation_labels", []))
        labels.update(_safe_text(item) for item in pair_signature.get("object_count_relation_labels", []))
        labels.update(_safe_text(item) for item in pair_signature.get("foreground_count_relation_labels", []))
        size_relation = pair_signature.get("size_relation", {})
        if isinstance(size_relation, Mapping):
            labels.update(_safe_text(item) for item in size_relation.get("candidate_primitive_hint_labels", []))
            relation = _safe_text(size_relation.get("output_size_relation"))
            if relation:
                labels.add(relation)
            if size_relation.get("same_size"):
                labels.add("same_size")
            if size_relation.get("palette_changed"):
                labels.add("palette_changed")
            if size_relation.get("foreground_count_changed"):
                labels.add("foreground_count_changed")
            if size_relation.get("object_count_changed"):
                labels.add("object_count_changed")
    return sorted(label for label in labels if label)


def _validate_train_pairs(train_pairs: Sequence[Mapping[str, Any]]) -> None:
    for pair in train_pairs:
        validate_grid_v1(_pair_input(pair))
        validate_grid_v1(_pair_output(pair))


def _copy_grid(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _all_equal(values: Sequence[Any]) -> bool:
    return len({json.dumps(_json_safe(value), sort_keys=True) for value in values}) <= 1


def _uniform_color(grid: Sequence[Sequence[int]]) -> int | None:
    colors = {cell for row in grid for cell in row}
    if len(colors) != 1:
        return None
    return next(iter(colors))


def _strip_uniform_border(output_grid: Sequence[Sequence[int]], input_height: int, input_width: int) -> tuple[list[list[int]], dict[str, Any]] | None:
    out_h, out_w = _grid_dimensions(output_grid)
    if out_h < input_height or out_w < input_width:
        return None
    pad_h = out_h - input_height
    pad_w = out_w - input_width
    if pad_h % 2 != 0 or pad_w % 2 != 0:
        return None
    top = bottom = pad_h // 2
    left = right = pad_w // 2
    border_cells = set()
    for row_index, row in enumerate(output_grid):
        for column_index, cell in enumerate(row):
            inside_row = top <= row_index < top + input_height
            inside_col = left <= column_index < left + input_width
            if not inside_row or not inside_col:
                border_cells.add(cell)
    if len(border_cells) != 1:
        return None
    border_color = next(iter(border_cells))
    inner = [list(row[left : left + input_width]) for row in output_grid[top : top + input_height]]
    return inner, {"top": top, "bottom": bottom, "left": left, "right": right, "border_color": int(border_color)}


def _color_mapping_consistent(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> dict[int, int] | None:
    if _grid_dimensions(input_grid) != _grid_dimensions(output_grid):
        return None
    mapping: dict[int, int] = {}
    for row_in, row_out in zip(input_grid, output_grid):
        for cell_in, cell_out in zip(row_in, row_out):
            current = mapping.get(cell_in)
            if current is None:
                mapping[cell_in] = int(cell_out)
            elif current != int(cell_out):
                return None
    return mapping


def _crop_candidates(input_grid: Sequence[Sequence[int]], *, background_value: int | None = None) -> list[tuple[str, list[list[int]]]]:
    candidates: list[tuple[str, list[list[int]]]] = []
    try:
        candidates.append(("crop_foreground_bbox", crop_to_foreground_bbox_v1(input_grid, background_value=background_value)))
    except Exception:
        pass
    try:
        candidates.append(("crop_largest_object", crop_to_largest_object_bbox_v1(input_grid, background_value=background_value)))
    except Exception:
        pass
    try:
        objects = extract_objects_v1(input_grid, background_value=background_value)["objects"]
        for obj in objects:
            color = int(obj["color"])
            try:
                candidates.append(("crop_selected_color_object", crop_selected_color_object_v1(input_grid, color=color, background_value=background_value)))
            except Exception:
                continue
    except Exception:
        pass
    dedup: list[tuple[str, list[list[int]]]] = []
    seen: set[str] = set()
    for name, grid in candidates:
        key = json.dumps(grid, sort_keys=True)
        if key not in seen:
            seen.add(key)
            dedup.append((name, grid))
    return dedup


def _validate_crop_then_recolor(train_pairs: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    crop_name: str | None = None
    recolor_name: str | None = None
    pair_summaries: list[dict[str, Any]] = []
    for pair in train_pairs:
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        bg = infer_background_value_v1(input_grid)
        pair_ok = False
        pair_crop: str | None = None
        for candidate_name, cropped in _crop_candidates(input_grid, background_value=bg):
            if _grid_dimensions(cropped) != _grid_dimensions(output_grid):
                continue
            mapping = _color_mapping_consistent(cropped, output_grid)
            if mapping is None:
                continue
            if mapping == {cell: cell for row in cropped for cell in row}:
                continue
            pair_ok = True
            pair_crop = candidate_name
            break
        if not pair_ok:
            return None
        if crop_name is None:
            crop_name = pair_crop
        elif crop_name != pair_crop:
            return None
        pair_summaries.append({"crop_primitive": pair_crop, "output_size": list(_grid_dimensions(output_grid))})
    if crop_name is None:
        return None
    recolor_name = "recolor_global"
    return {"family_name": "crop_then_recolor", "primitive_chain": [crop_name, recolor_name], "parameters": {"crop_primitive": crop_name, "recolor_primitive": recolor_name}, "pair_summaries": pair_summaries}


def _validate_crop_then_rotate_or_reflect(train_pairs: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    crop_name: str | None = None
    transform_name: str | None = None
    pair_summaries: list[dict[str, Any]] = []
    for pair in train_pairs:
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        bg = infer_background_value_v1(input_grid)
        pair_ok = False
        pair_crop: str | None = None
        pair_transform: str | None = None
        for candidate_name, cropped in _crop_candidates(input_grid, background_value=bg):
            if candidate_name == "crop_selected_color_object":
                continue
            cropped_bg = bg
            objects = extract_objects_v1(cropped, background_value=cropped_bg)["objects"]
            if len(objects) != 1:
                continue
            obj = objects[0]
            transforms = [
                ("rotate_object_90", rotate_object_mask_v1(obj["cells"], 1)),
                ("rotate_object_180", rotate_object_mask_v1(obj["cells"], 2)),
                ("rotate_object_270", rotate_object_mask_v1(obj["cells"], 3)),
                ("reflect_object_horizontal", reflect_object_mask_v1(obj["cells"], "horizontal")),
                ("reflect_object_vertical", reflect_object_mask_v1(obj["cells"], "vertical")),
            ]
            for name, transformed_mask in transforms:
                try:
                    transformed = rebuild_object_into_background_grid_v1(
                        transformed_mask,
                        color=int(obj["color"]),
                        background_value=int(cropped_bg),
                        height=len(cropped),
                        width=len(cropped[0]),
                        anchor_row=0,
                        anchor_col=0,
                    )
                except Exception:
                    continue
                if transformed == output_grid:
                    pair_ok = True
                    pair_crop = candidate_name
                    pair_transform = name
                    break
            if pair_ok:
                break
        if not pair_ok or pair_crop is None or pair_transform is None:
            return None
        if crop_name is None:
            crop_name = pair_crop
        elif crop_name != pair_crop:
            return None
        if transform_name is None:
            transform_name = pair_transform
        elif transform_name != pair_transform:
            return None
        pair_summaries.append({"crop_primitive": pair_crop, "transform": pair_transform})
    if crop_name is None or transform_name is None:
        return None
    return {"family_name": "crop_then_rotate_or_reflect", "primitive_chain": [crop_name, transform_name], "parameters": {"crop_primitive": crop_name, "geometry_primitive": transform_name}, "pair_summaries": pair_summaries}


def _validate_crop_then_tile(train_pairs: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    crop_name: str | None = None
    repeat_rows: int | None = None
    repeat_cols: int | None = None
    pair_summaries: list[dict[str, Any]] = []
    for pair in train_pairs:
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        bg = infer_background_value_v1(input_grid)
        pair_ok = False
        pair_crop: str | None = None
        pair_repeat: tuple[int, int] | None = None
        for candidate_name, cropped in _crop_candidates(input_grid, background_value=bg):
            c_h, c_w = _grid_dimensions(cropped)
            o_h, o_w = _grid_dimensions(output_grid)
            if o_h % c_h != 0 or o_w % c_w != 0:
                continue
            r_rows = o_h // c_h
            r_cols = o_w // c_w
            tiled = _tile_grid(_copy_grid(cropped), r_rows, r_cols)
            if tiled != output_grid:
                continue
            pair_ok = True
            pair_crop = candidate_name
            pair_repeat = (r_rows, r_cols)
            break
        if not pair_ok or pair_repeat is None:
            return None
        if crop_name is None:
            crop_name = pair_crop
        elif crop_name != pair_crop:
            return None
        if repeat_rows is None:
            repeat_rows, repeat_cols = pair_repeat
        elif (repeat_rows, repeat_cols) != pair_repeat:
            return None
        pair_summaries.append({"crop_primitive": pair_crop, "repeat_rows": pair_repeat[0], "repeat_cols": pair_repeat[1]})
    if crop_name is None or repeat_rows is None or repeat_cols is None:
        return None
    return {"family_name": "crop_then_tile", "primitive_chain": [crop_name, "tile_grid"], "parameters": {"crop_primitive": crop_name, "repeat_rows": repeat_rows, "repeat_cols": repeat_cols}, "pair_summaries": pair_summaries}


def _validate_recolor_then_border(train_pairs: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    pair_summaries: list[dict[str, Any]] = []
    for pair in train_pairs:
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        stripped = _strip_uniform_border(output_grid, len(input_grid), len(input_grid[0]))
        if stripped is None:
            return None
        inner, border_summary = stripped
        mapping = _color_mapping_consistent(input_grid, inner)
        if mapping is None:
            return None
        if mapping == {cell: cell for row in input_grid for cell in row}:
            return None
        pair_summaries.append({"border_color": border_summary["border_color"], "padding": [border_summary["top"], border_summary["bottom"], border_summary["left"], border_summary["right"]]})
    return {"family_name": "recolor_then_border", "primitive_chain": ["recolor_global", "add_uniform_border"], "parameters": {"recolor_primitive": "recolor_global", "border_primitive": "add_uniform_border"}, "pair_summaries": pair_summaries}


def _validate_select_then_recolor(train_pairs: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    pair_summaries: list[dict[str, Any]] = []
    select_name: str | None = None
    for pair in train_pairs:
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        bg = infer_background_value_v1(input_grid)
        selected_grid: list[list[int]] | None = None
        selected_primitive: str | None = None
        try:
            selected_grid = crop_to_largest_object_bbox_v1(input_grid, background_value=bg)
            selected_primitive = "select_largest_object"
        except Exception:
            selected_grid = None
        if selected_grid is None:
            try:
                objects = extract_objects_v1(input_grid, background_value=bg)["objects"]
                counts = Counter(cell for row in input_grid for cell in row if cell != bg)
                if counts:
                    most_common = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
                    selected_grid = crop_selected_color_object_v1(input_grid, color=most_common, background_value=bg)
                    selected_primitive = "select_most_frequent_foreground_color"
            except Exception:
                selected_grid = None
        if selected_grid is None or selected_primitive is None:
            return None
        mapping = _color_mapping_consistent(selected_grid, output_grid)
        if mapping is None:
            return None
        if select_name is None:
            select_name = selected_primitive
        elif select_name != selected_primitive:
            return None
        pair_summaries.append({"select_primitive": selected_primitive, "output_size": list(_grid_dimensions(output_grid))})
    if select_name is None:
        return None
    return {"family_name": "select_then_recolor", "primitive_chain": [select_name, "recolor_global"], "parameters": {"select_primitive": select_name, "recolor_primitive": "recolor_global"}, "pair_summaries": pair_summaries}


def _single_step_family_hypothesis(
    family_name: str,
    primitive_chain: Sequence[str],
    status: str,
    confidence: float,
    reason: str,
    *,
    parameters: Mapping[str, Any] | None = None,
    train_fit: bool = False,
    rejection_reason: str | None = None,
    source_primitive_hints: Sequence[str] | None = None,
    trace: Mapping[str, Any] | None = None,
) -> "FamilyHypothesis":
    return FamilyHypothesis(
        family_name=family_name,
        primitive_chain=tuple(primitive_chain),
        status=status,
        confidence=confidence,
        reason=reason,
        parameters=dict(parameters or {}),
        train_fit=train_fit,
        rejection_reason=rejection_reason,
        source_primitive_hints=tuple(source_primitive_hints or ()),
        trace=dict(trace or {}),
    )


@dataclass(frozen=True)
class FamilyHypothesis:
    family_name: str
    primitive_chain: tuple[str, ...] = field(default_factory=tuple)
    status: str = "uncertain"
    confidence: float = 0.0
    reason: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    train_fit: bool = False
    rejection_reason: str | None = None
    source_primitive_hints: tuple[str, ...] = field(default_factory=tuple)
    trace: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        primitive_chain = tuple(_safe_text(value) for value in self.primitive_chain if _safe_text(value))
        source_primitive_hints = tuple(_safe_text(value) for value in self.source_primitive_hints if _safe_text(value))
        if len(primitive_chain) == 0:
            raise ValueError("primitive_chain_required")
        if len(primitive_chain) > MAX_PRIMITIVE_CHAIN_LENGTH_V1:
            raise ValueError("primitive_chain_too_long")
        object.__setattr__(self, "family_name", _safe_text(self.family_name))
        object.__setattr__(self, "primitive_chain", primitive_chain)
        object.__setattr__(self, "status", _safe_text(self.status))
        object.__setattr__(self, "confidence", float(self.confidence))
        object.__setattr__(self, "reason", _safe_text(self.reason))
        object.__setattr__(self, "parameters", _json_safe(self.parameters))
        object.__setattr__(self, "train_fit", bool(self.train_fit))
        object.__setattr__(self, "rejection_reason", _safe_text(self.rejection_reason) if self.rejection_reason is not None else None)
        object.__setattr__(self, "source_primitive_hints", tuple(sorted(source_primitive_hints)))
        object.__setattr__(self, "trace", _json_safe(self.trace))
        if self.status not in {"accepted", "rejected", "uncertain"}:
            raise ValueError(f"invalid_status:{self.status}")

    def to_json_safe_dict(self) -> dict[str, Any]:
        return {
            "family_name": self.family_name,
            "primitive_chain": list(self.primitive_chain),
            "status": self.status,
            "confidence": float(self.confidence),
            "reason": self.reason,
            "parameters": _json_safe(self.parameters),
            "train_fit": bool(self.train_fit),
            "rejection_reason": self.rejection_reason,
            "source_primitive_hints": list(self.source_primitive_hints),
            "trace": _json_safe(self.trace),
        }


@dataclass(frozen=True)
class FamilyDiscoveryResult:
    accepted_families: tuple[FamilyHypothesis, ...] = field(default_factory=tuple)
    rejected_families: tuple[FamilyHypothesis, ...] = field(default_factory=tuple)
    uncertain_families: tuple[FamilyHypothesis, ...] = field(default_factory=tuple)
    family_count: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    uncertain_count: int = 0
    trace: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        accepted = tuple(self._sorted_hypotheses(self.accepted_families, "accepted"))
        rejected = tuple(self._sorted_hypotheses(self.rejected_families, "rejected"))
        uncertain = tuple(self._sorted_hypotheses(self.uncertain_families, "uncertain"))
        object.__setattr__(self, "accepted_families", accepted)
        object.__setattr__(self, "rejected_families", rejected)
        object.__setattr__(self, "uncertain_families", uncertain)
        object.__setattr__(self, "family_count", int(self.family_count))
        object.__setattr__(self, "accepted_count", int(self.accepted_count))
        object.__setattr__(self, "rejected_count", int(self.rejected_count))
        object.__setattr__(self, "uncertain_count", int(self.uncertain_count))
        object.__setattr__(self, "trace", _json_safe(self.trace))

    @staticmethod
    def _sorted_hypotheses(hypotheses: Sequence[FamilyHypothesis], status: str) -> list[FamilyHypothesis]:
        filtered = [hypothesis for hypothesis in hypotheses if hypothesis.status == status]
        return sorted(
            filtered,
            key=lambda hypothesis: (
                _hint_status_rank(hypothesis.status),
                -float(hypothesis.confidence),
                len(hypothesis.primitive_chain),
                FAMILY_PRIORITY_V1.get(hypothesis.family_name, 99),
                hypothesis.family_name,
                hypothesis.primitive_chain,
            ),
        )

    def to_json_safe_dict(self) -> dict[str, Any]:
        return {
            "accepted_families": [hypothesis.to_json_safe_dict() for hypothesis in self.accepted_families],
            "rejected_families": [hypothesis.to_json_safe_dict() for hypothesis in self.rejected_families],
            "uncertain_families": [hypothesis.to_json_safe_dict() for hypothesis in self.uncertain_families],
            "family_count": int(self.family_count),
            "accepted_count": int(self.accepted_count),
            "rejected_count": int(self.rejected_count),
            "uncertain_count": int(self.uncertain_count),
            "trace": _json_safe(self.trace),
        }


def _build_family_hypothesis(
    family_name: str,
    primitive_chain: Sequence[str],
    status: str,
    confidence: float,
    reason: str,
    *,
    parameters: Mapping[str, Any] | None = None,
    train_fit: bool = False,
    rejection_reason: str | None = None,
    source_primitive_hints: Sequence[str] | None = None,
    trace: Mapping[str, Any] | None = None,
) -> FamilyHypothesis:
    return FamilyHypothesis(
        family_name=family_name,
        primitive_chain=tuple(primitive_chain),
        status=status,
        confidence=confidence,
        reason=reason,
        parameters=dict(parameters or {}),
        train_fit=train_fit,
        rejection_reason=rejection_reason,
        source_primitive_hints=tuple(source_primitive_hints or ()),
        trace=dict(trace or {}),
    )


def _family_from_single_step_solver(
    family_name: str,
    solver_candidates: Sequence[Mapping[str, Any]],
    *,
    primitive_hint_names: Sequence[str],
    accepted_hints: Mapping[str, PrimitiveDiscoveryHint],
    uncertain_hints: Mapping[str, PrimitiveDiscoveryHint],
    rejected_hints: Mapping[str, PrimitiveDiscoveryHint],
) -> FamilyHypothesis:
    best = None
    if solver_candidates:
        best = solver_candidates[0]
    if best is not None:
        solver_family = _safe_text(best.get("family"))
        primitive_name = _map_family_name(solver_family)
        best_confidence = float(best.get("confidence", 0.0) or 0.0)
        if primitive_name in accepted_hints or primitive_name in uncertain_hints:
            hint = accepted_hints.get(primitive_name) or uncertain_hints.get(primitive_name)
            return _build_family_hypothesis(
                family_name=family_name,
                primitive_chain=(primitive_name,),
                status="accepted" if hint and hint.status == "accepted" else "uncertain",
                confidence=best_confidence,
                reason=_safe_text(best.get("trace", {}).get("rule") or solver_family or "solver_fit"),
                parameters=dict(best.get("trace", {})).get("role_summary", {}) if isinstance(best.get("trace", {}), Mapping) else {},
                train_fit=bool(best.get("family")),
                rejection_reason=None,
                source_primitive_hints=primitive_hint_names,
                trace={"solver_family": solver_family, "train_fit": True, "candidate_count": len(solver_candidates)},
            )
        if bool(best.get("family")) and best_confidence >= 0.9 and primitive_name in primitive_hint_names:
            return _build_family_hypothesis(
                family_name=family_name,
                primitive_chain=(primitive_name,),
                status="accepted",
                confidence=best_confidence,
                reason=f"solver_fit_without_primitive_hint:{_safe_text(best.get('trace', {}).get('rule') or solver_family or 'solver_fit')}",
                parameters=dict(best.get("trace", {})).get("role_summary", {}) if isinstance(best.get("trace", {}), Mapping) else {},
                train_fit=True,
                rejection_reason=None,
                source_primitive_hints=primitive_hint_names,
                trace={"solver_family": solver_family, "train_fit": True, "candidate_count": len(solver_candidates), "relaxed_primitive_gate": True},
            )
    best_hint = None
    for name in primitive_hint_names:
        if name in accepted_hints:
            best_hint = accepted_hints[name]
            break
        if name in uncertain_hints and uncertain_hints[name].confidence >= HIGH_CONFIDENCE_UNCERTAIN_THRESHOLD_V1:
            best_hint = uncertain_hints[name]
            break
    if best_hint is not None:
        return _build_family_hypothesis(
            family_name=family_name,
            primitive_chain=(best_hint.primitive_name,),
            status="uncertain" if best_hint.status != "accepted" else "accepted",
            confidence=float(best_hint.confidence),
            reason="primitive_evidence_only",
            parameters={},
            train_fit=False,
            rejection_reason=None,
            source_primitive_hints=primitive_hint_names,
            trace={"solver_fit": False, "primitive_hint": best_hint.primitive_name},
        )
    return _build_family_hypothesis(
        family_name=family_name,
        primitive_chain=(primitive_hint_names[0],),
        status="rejected",
        confidence=0.1,
        reason="no_supporting_primitive",
        parameters={},
        train_fit=False,
        rejection_reason="required_primitives_missing_or_rejected",
        source_primitive_hints=primitive_hint_names,
        trace={"solver_fit": False, "candidate_count": len(solver_candidates)},
    )


def _composition_family_hypothesis(
    family_name: str,
    validation: dict[str, Any] | None,
    required_primitives: Sequence[str],
    accepted_hints: Mapping[str, PrimitiveDiscoveryHint],
    uncertain_hints: Mapping[str, PrimitiveDiscoveryHint],
    rejected_hints: Mapping[str, PrimitiveDiscoveryHint],
) -> FamilyHypothesis:
    source_hints = list(required_primitives)
    if any(name in rejected_hints for name in required_primitives):
        return _build_family_hypothesis(
            family_name=family_name,
            primitive_chain=tuple(required_primitives[:2]),
            status="rejected",
            confidence=0.1,
            reason="required_primitive_rejected",
            parameters={},
            train_fit=False,
            rejection_reason="required_primitive_rejected",
            source_primitive_hints=source_hints,
            trace={"validation": "skipped"},
        )
    if validation is None:
        status = "rejected" if any(name in accepted_hints or (name in uncertain_hints and uncertain_hints[name].confidence >= HIGH_CONFIDENCE_UNCERTAIN_THRESHOLD_V1) for name in required_primitives) else "uncertain"
        reason = "train_consistency_failed" if status == "rejected" else "insufficient_composition_evidence"
        return _build_family_hypothesis(
            family_name=family_name,
            primitive_chain=tuple(required_primitives[:2]),
            status=status,
            confidence=0.2 if status == "rejected" else 0.3,
            reason=reason,
            parameters={},
            train_fit=False,
            rejection_reason=reason if status == "rejected" else None,
            source_primitive_hints=source_hints,
            trace={"validation": "none"},
        )
    chain = validation.get("primitive_chain", tuple(required_primitives[:2]))
    parameters = validation.get("parameters", {})
    train_fit = True
    if family_name in COMPOSITION_FAMILY_ORDER_V1:
        status = "accepted"
        confidence = 0.95
    else:
        status = "uncertain"
        confidence = 0.5
    return _build_family_hypothesis(
        family_name=family_name,
        primitive_chain=tuple(chain[:MAX_PRIMITIVE_CHAIN_LENGTH_V1]),
        status=status,
        confidence=confidence,
        reason=family_name,
        parameters=parameters,
        train_fit=train_fit,
        rejection_reason=None,
        source_primitive_hints=source_hints,
        trace={"validation": validation.get("pair_summaries", []), "template": family_name},
    )


def _select_solver_candidates(train_pairs: Sequence[Mapping[str, Any]], test_input: Any) -> dict[str, list[dict[str, Any]]]:
    return {
        "object_bbox": solve_object_bbox_task(train_pairs, test_input),
        "shape_geometry": [candidate.to_dict() for candidate in infer_shape_geometry_hypotheses_v1(train_pairs, test_input)],
        "color_role": [candidate.to_dict() for candidate in infer_color_role_hypotheses_v1(train_pairs, test_input)],
        "resize_tile": [candidate.to_dict() for candidate in infer_resize_tile_hypotheses_v1(train_pairs, test_input)],
        "count_quantity": [candidate.to_dict() for candidate in infer_count_quantity_hypotheses_v1(train_pairs, test_input)],
        "symmetry_line": solve_symmetry_line_task(train_pairs, test_input),
        "hole_row_column": solve_hole_row_column_task(train_pairs, test_input),
        "marker_copy": solve_marker_copy_task(train_pairs, test_input),
    }


def _deduplicate_hypotheses(hypotheses: Sequence[FamilyHypothesis]) -> list[FamilyHypothesis]:
    ranked = sorted(
        hypotheses,
        key=lambda hypothesis: (
            _hint_status_rank(hypothesis.status),
            -float(hypothesis.confidence),
            len(hypothesis.primitive_chain),
            FAMILY_PRIORITY_V1.get(hypothesis.family_name, 99),
            hypothesis.family_name,
            hypothesis.primitive_chain,
        ),
    )
    seen: set[tuple[str, tuple[str, ...], str]] = set()
    output: list[FamilyHypothesis] = []
    for hypothesis in ranked:
        signature = (hypothesis.family_name, hypothesis.primitive_chain, json.dumps(_json_safe(hypothesis.parameters), sort_keys=True))
        if signature in seen:
            continue
        seen.add(signature)
        output.append(hypothesis)
    return output


def discover_families_for_task(
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Any | None = None,
    primitive_result: PrimitiveDiscoveryResult | None = None,
    registry: PrimitiveRegistry | Sequence[PrimitiveDescriptor] | None = None,
) -> FamilyDiscoveryResult:
    if not isinstance(train_pairs, Sequence) or not train_pairs:
        raise ValueError("empty_train_pairs")
    _validate_train_pairs(train_pairs)
    registry_obj = registry if registry is not None else build_arc_primitive_registry_v1()
    if isinstance(registry_obj, PrimitiveRegistry):
        registry_descriptors = registry_obj.list_primitives()
        registry_manifest = registry_obj.export_manifest()
    else:
        registry_descriptors = list(registry_obj)
        registry_manifest = {"primitive_count": len(registry_descriptors)}

    test_input_supplied = test_input is not None
    if test_input is None:
        test_input = _pair_input(train_pairs[0])

    task_signature = build_arc_task_feature_signature_v1(train_pairs, test_input)
    task_feature_labels = _hint_labels_from_signature(task_signature)
    normalized_primitive_result = _normalize_primitive_result(primitive_result)
    if normalized_primitive_result is None:
        normalized_primitive_result = discover_primitives_for_task(train_pairs, test_input, registry_obj)

    accepted_hints, rejected_hints, uncertain_hints = _collect_primitive_hints(normalized_primitive_result)
    all_hints_by_name = dict(accepted_hints)
    all_hints_by_name.update(uncertain_hints)
    all_hints_by_name.update(rejected_hints)

    solver_candidates = _select_solver_candidates(train_pairs, test_input)

    family_hypotheses: list[FamilyHypothesis] = []
    # Single-step families
    family_hypotheses.append(
        _family_from_single_step_solver(
            "object_bbox",
            solver_candidates["object_bbox"],
            primitive_hint_names=OBJECT_BBOX_PRIMITIVES_V1,
            accepted_hints=accepted_hints,
            uncertain_hints=uncertain_hints,
            rejected_hints=rejected_hints,
        )
    )
    family_hypotheses.append(
        _family_from_single_step_solver(
            "shape_geometry",
            solver_candidates["shape_geometry"],
            primitive_hint_names=SHAPE_GEOMETRY_PRIMITIVES_V1,
            accepted_hints=accepted_hints,
            uncertain_hints=uncertain_hints,
            rejected_hints=rejected_hints,
        )
    )
    family_hypotheses.append(
        _family_from_single_step_solver(
            "color_role",
            solver_candidates["color_role"],
            primitive_hint_names=COLOR_ROLE_PRIMITIVES_V1,
            accepted_hints=accepted_hints,
            uncertain_hints=uncertain_hints,
            rejected_hints=rejected_hints,
        )
    )
    family_hypotheses.append(
        _family_from_single_step_solver(
            "resize_tile",
            solver_candidates["resize_tile"],
            primitive_hint_names=RESIZE_TILE_PRIMITIVES_V1,
            accepted_hints=accepted_hints,
            uncertain_hints=uncertain_hints,
            rejected_hints=rejected_hints,
        )
    )
    family_hypotheses.append(
        _family_from_single_step_solver(
            "count_quantity",
            solver_candidates["count_quantity"],
            primitive_hint_names=COUNT_QUANTITY_PRIMITIVES_V1,
            accepted_hints=accepted_hints,
            uncertain_hints=uncertain_hints,
            rejected_hints=rejected_hints,
        )
    )
    family_hypotheses.append(
        _family_from_single_step_solver(
            "symmetry_line",
            solver_candidates["symmetry_line"],
            primitive_hint_names=("complete_horizontal_symmetry", "complete_vertical_symmetry", "extend_line_to_boundary"),
            accepted_hints=accepted_hints,
            uncertain_hints=uncertain_hints,
            rejected_hints=rejected_hints,
        )
    )
    family_hypotheses.append(
        _family_from_single_step_solver(
            "hole_row_column",
            solver_candidates["hole_row_column"],
            primitive_hint_names=("fill_enclosed_hole", "extract_row_or_column_by_marker"),
            accepted_hints=accepted_hints,
            uncertain_hints=uncertain_hints,
            rejected_hints=rejected_hints,
        )
    )
    family_hypotheses.append(
        _family_from_single_step_solver(
            "marker_copy",
            solver_candidates["marker_copy"],
            primitive_hint_names=("copy_object_to_marker",),
            accepted_hints=accepted_hints,
            uncertain_hints=uncertain_hints,
            rejected_hints=rejected_hints,
        )
    )

    # Composition families
    family_hypotheses.append(
        _composition_family_hypothesis(
            "crop_then_recolor",
            _validate_crop_then_recolor(train_pairs),
            ("crop_foreground_bbox", "recolor_global"),
            accepted_hints,
            uncertain_hints,
            rejected_hints,
        )
    )
    family_hypotheses.append(
        _composition_family_hypothesis(
            "crop_then_rotate_or_reflect",
            _validate_crop_then_rotate_or_reflect(train_pairs),
            ("crop_foreground_bbox", "rotate_object_90"),
            accepted_hints,
            uncertain_hints,
            rejected_hints,
        )
    )
    family_hypotheses.append(
        _composition_family_hypothesis(
            "crop_then_tile",
            _validate_crop_then_tile(train_pairs),
            ("crop_foreground_bbox", "tile_grid"),
            accepted_hints,
            uncertain_hints,
            rejected_hints,
        )
    )
    family_hypotheses.append(
        _composition_family_hypothesis(
            "recolor_then_border",
            _validate_recolor_then_border(train_pairs),
            ("recolor_global", "add_uniform_border"),
            accepted_hints,
            uncertain_hints,
            rejected_hints,
        )
    )
    family_hypotheses.append(
        _composition_family_hypothesis(
            "select_then_recolor",
            _validate_select_then_recolor(train_pairs),
            ("select_largest_object", "recolor_global"),
            accepted_hints,
            uncertain_hints,
            rejected_hints,
        )
    )

    deduped = _deduplicate_hypotheses(family_hypotheses)
    accepted = tuple(hypothesis for hypothesis in deduped if hypothesis.status == "accepted")
    rejected = tuple(hypothesis for hypothesis in deduped if hypothesis.status == "rejected")
    uncertain = tuple(hypothesis for hypothesis in deduped if hypothesis.status == "uncertain")
    return FamilyDiscoveryResult(
        accepted_families=accepted,
        rejected_families=rejected,
        uncertain_families=uncertain,
        family_count=len(deduped),
        accepted_count=len(accepted),
        rejected_count=len(rejected),
        uncertain_count=len(uncertain),
        trace={
            "schema_version": SCHEMA_VERSION_V1,
            "registry_primitive_count": registry_manifest.get("primitive_count", len(registry_descriptors)),
            "primitive_result_used": primitive_result is not None,
            "primitive_result_accepted_count": normalized_primitive_result.accepted_count,
            "task_signature_schema": task_signature.get("schema_version", ""),
            "task_feature_labels": task_feature_labels,
            "train_pair_count": len(train_pairs),
            "test_input_provided": test_input_supplied,
            "family_templates_considered": list(SINGLE_STEP_FAMILY_ORDER_V1) + list(COMPOSITION_FAMILY_ORDER_V1),
            "deduplicated_count": len(deduped),
        },
    )


__all__ = [
    "FamilyDiscoveryResult",
    "FamilyHypothesis",
    "discover_families_for_task",
]
