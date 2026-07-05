"""ARC-AGI-2 compositional executor V1.

Executes bounded two-step family hypotheses on synthetic train/test fixtures.
The executor is exact-match and metadata-safe: it never emits raw train grids,
expected outputs, public labels, or open-ended plans.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from weslr.arc_family_discovery_engine_v1 import FamilyHypothesis
from weslr.arc_object_extraction_v1 import (
    crop_selected_color_object_v1,
    crop_to_foreground_bbox_v1,
    crop_to_largest_object_bbox_v1,
    extract_objects_v1,
    infer_background_value_v1,
    validate_grid_v1,
)
from weslr.arc_resize_tile_canvas_v1 import _pad_grid, _tile_grid
from weslr.arc_shape_geometry_v1 import rebuild_object_into_background_grid_v1, reflect_object_mask_v1, rotate_object_mask_v1

SCHEMA_VERSION_V1 = "ArcCompositionalExecutorV1"
SUPPORTED_TEMPLATES_V1 = (
    "crop_then_recolor",
    "crop_then_rotate_or_reflect",
    "crop_then_tile",
    "recolor_then_border",
    "select_then_recolor",
)

ROTATE_OR_REFLECT_NAMES_V1 = (
    "rotate_object_90",
    "rotate_object_180",
    "rotate_object_270",
    "reflect_object_horizontal",
    "reflect_object_vertical",
)

SELECTOR_NAMES_V1 = (
    "select_largest_object",
    "select_most_frequent_foreground_color",
)


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


def _grid_key(grid: Any) -> str:
    return repr(_json_safe(grid))


def _mapping_consistent(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> dict[int, int] | None:
    if len(input_grid) != len(output_grid) or len(input_grid[0]) != len(output_grid[0]):
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


def _mapping_is_identity(grid: Sequence[Sequence[int]], mapping: Mapping[int, int]) -> bool:
    return all(int(cell) == int(mapping.get(int(cell), int(cell))) for row in grid for cell in row)


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
            try:
                candidates.append(("crop_selected_color_object", crop_selected_color_object_v1(input_grid, color=int(obj["color"]), background_value=background_value)))
            except Exception:
                continue
    except Exception:
        pass
    dedup: list[tuple[str, list[list[int]]]] = []
    seen: set[str] = set()
    for name, grid in candidates:
        key = _grid_key(grid)
        if key not in seen:
            seen.add(key)
            dedup.append((name, grid))
    return dedup


@dataclass(frozen=True)
class CompositionalExecutorCandidate:
    family_name: str
    primitive_chain: tuple[str, ...]
    output: Any
    confidence: float
    train_fit: bool
    trace: dict[str, Any] = field(default_factory=dict)
    rejection_reason: str | None = None

    def to_json_safe_dict(self) -> dict[str, Any]:
        return {
            "family_name": _safe_text(self.family_name),
            "primitive_chain": [_safe_text(item) for item in self.primitive_chain],
            "output": _json_safe(self.output),
            "confidence": float(self.confidence),
            "train_fit": bool(self.train_fit),
            "trace": _json_safe(self.trace),
            "rejection_reason": self.rejection_reason,
        }


def _candidate(
    *,
    family_name: str,
    primitive_chain: Sequence[str],
    output: Any,
    confidence: float,
    train_fit: bool,
    trace: Mapping[str, Any],
    rejection_reason: str | None = None,
) -> CompositionalExecutorCandidate:
    return CompositionalExecutorCandidate(
        family_name=_safe_text(family_name),
        primitive_chain=tuple(_safe_text(name) for name in primitive_chain),
        output=_json_safe(output),
        confidence=float(confidence),
        train_fit=bool(train_fit),
        trace={str(key): _json_safe(value) for key, value in trace.items()},
        rejection_reason=rejection_reason,
    )


def _reject(family_name: str, primitive_chain: Sequence[str], *, reason: str, trace: Mapping[str, Any]) -> CompositionalExecutorCandidate:
    rejected_trace = dict(trace)
    rejected_trace["status"] = "rejected"
    rejected_trace["rejection_reason"] = reason
    rejected_trace["family_name"] = family_name
    rejected_trace["primitive_chain"] = list(primitive_chain)
    return _candidate(
        family_name=family_name,
        primitive_chain=primitive_chain,
        output=None,
        confidence=0.0,
        train_fit=False,
        trace=rejected_trace,
        rejection_reason=reason,
    )


def _normalize_family_hypothesis(value: FamilyHypothesis | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, FamilyHypothesis):
        return {
            "family_name": value.family_name,
            "primitive_chain": list(value.primitive_chain),
            "status": value.status,
            "confidence": float(value.confidence),
            "reason": value.reason,
            "parameters": dict(value.parameters),
            "train_fit": bool(value.train_fit),
            "rejection_reason": value.rejection_reason,
            "source_primitive_hints": list(value.source_primitive_hints),
            "trace": dict(value.trace),
        }
    mapping = dict(value)
    mapping["primitive_chain"] = list(mapping.get("primitive_chain", []))
    mapping["source_primitive_hints"] = list(mapping.get("source_primitive_hints", []))
    mapping["parameters"] = dict(mapping.get("parameters", {})) if isinstance(mapping.get("parameters"), Mapping) else {}
    mapping["trace"] = dict(mapping.get("trace", {})) if isinstance(mapping.get("trace"), Mapping) else {}
    return mapping


def _infer_crop_then_recolor(train_pairs: Sequence[Mapping[str, Any]], test_input: Any, hyp: Mapping[str, Any], *, trace: bool) -> CompositionalExecutorCandidate:
    chosen_crop: str | None = None
    mapping: dict[int, int] | None = None
    selected_color: int | None = None
    pair_traces: list[dict[str, Any]] = []
    for pair_index, pair in enumerate(train_pairs):
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        background = infer_background_value_v1(input_grid)
        pair_choice: tuple[str, list[list[int]], dict[int, int], int | None] | None = None
        for crop_name, cropped in _crop_candidates(input_grid, background_value=background):
            if len(cropped) != len(output_grid) or len(cropped[0]) != len(output_grid[0]):
                continue
            pair_mapping = _mapping_consistent(cropped, output_grid)
            if pair_mapping is None or _mapping_is_identity(cropped, pair_mapping):
                continue
            colors = sorted({int(cell) for row in cropped for cell in row})
            selected = colors[0] if len(colors) == 1 else None
            pair_choice = (crop_name, cropped, pair_mapping, selected)
            break
        if pair_choice is None:
            return _reject("crop_then_recolor", hyp["primitive_chain"], reason=f"train_mismatch:{pair_index}", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "crop_then_recolor", "template": "crop_then_recolor", "train_fit": False})
        crop_name, cropped, pair_mapping, pair_selected = pair_choice
        if chosen_crop is None:
            chosen_crop = crop_name
        elif chosen_crop != crop_name:
            return _reject("crop_then_recolor", hyp["primitive_chain"], reason="crop_primitive_inconsistent", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "crop_then_recolor", "template": "crop_then_recolor", "train_fit": False})
        if mapping is None:
            mapping = pair_mapping
        elif mapping != pair_mapping:
            return _reject("crop_then_recolor", hyp["primitive_chain"], reason="recolor_mapping_inconsistent", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "crop_then_recolor", "template": "crop_then_recolor", "train_fit": False})
        if selected_color is None:
            selected_color = pair_selected
        elif selected_color != pair_selected:
            selected_color = None
        pair_traces.append({"pair_index": pair_index, "crop_primitive": crop_name, "mapping_size": len(pair_mapping)})
    assert chosen_crop is not None and mapping is not None
    background = infer_background_value_v1(validate_grid_v1(test_input))
    for crop_name, cropped in _crop_candidates(validate_grid_v1(test_input), background_value=background):
        if crop_name != chosen_crop:
            continue
        predicted = [[int(mapping.get(int(cell), int(cell))) for cell in row] for row in cropped]
        trace_data = {
            "schema_version": SCHEMA_VERSION_V1,
            "family_name": "crop_then_recolor",
            "template": "crop_then_recolor",
            "primitive_chain": list(hyp["primitive_chain"]),
            "crop_primitive": crop_name,
            "recolor_mapping_size": len(mapping),
            "selected_color": selected_color,
            "pair_traces": pair_traces if trace else [],
            "train_fit": True,
            "execution_kind": "compositional_executor",
        }
        return _candidate(
            family_name="crop_then_recolor",
            primitive_chain=hyp["primitive_chain"],
            output=predicted,
            confidence=120.0,
            train_fit=True,
            trace=trace_data,
        )
    return _reject("crop_then_recolor", hyp["primitive_chain"], reason="test_execution_failed", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "crop_then_recolor", "template": "crop_then_recolor", "train_fit": False})


def _apply_rotation_or_reflection(mask: Sequence[Sequence[int]], transform_name: str) -> list[tuple[int, int]]:
    if transform_name == "rotate_object_90":
        return rotate_object_mask_v1(mask, 1)
    if transform_name == "rotate_object_180":
        return rotate_object_mask_v1(mask, 2)
    if transform_name == "rotate_object_270":
        return rotate_object_mask_v1(mask, 3)
    if transform_name == "reflect_object_horizontal":
        return reflect_object_mask_v1(mask, "horizontal")
    if transform_name == "reflect_object_vertical":
        return reflect_object_mask_v1(mask, "vertical")
    raise ValueError("unsupported_transform")


def _infer_crop_then_rotate_or_reflect(train_pairs: Sequence[Mapping[str, Any]], test_input: Any, hyp: Mapping[str, Any], *, trace: bool) -> CompositionalExecutorCandidate:
    chosen_crop: str | None = None
    chosen_transform: str | None = None
    pair_traces: list[dict[str, Any]] = []
    for pair_index, pair in enumerate(train_pairs):
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        background = infer_background_value_v1(input_grid)
        matched = False
        for crop_name, cropped in _crop_candidates(input_grid, background_value=background):
            objects = extract_objects_v1(cropped, background_value=background)["objects"]
            if len(objects) != 1:
                continue
            obj = objects[0]
            for transform_name in ROTATE_OR_REFLECT_NAMES_V1:
                try:
                    transformed_mask = _apply_rotation_or_reflection(obj["cells"], transform_name)
                    predicted = rebuild_object_into_background_grid_v1(
                        transformed_mask,
                        color=int(obj["color"]),
                        background_value=background,
                        height=len(cropped),
                        width=len(cropped[0]),
                        anchor_row=0,
                        anchor_col=0,
                    )
                except Exception:
                    continue
                if predicted == output_grid:
                    if chosen_crop is None:
                        chosen_crop = crop_name
                    elif chosen_crop != crop_name:
                        return _reject("crop_then_rotate_or_reflect", hyp["primitive_chain"], reason="crop_primitive_inconsistent", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "crop_then_rotate_or_reflect", "template": "crop_then_rotate_or_reflect", "train_fit": False})
                    if chosen_transform is None:
                        chosen_transform = transform_name
                    elif chosen_transform != transform_name:
                        return _reject("crop_then_rotate_or_reflect", hyp["primitive_chain"], reason="transform_inconsistent", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "crop_then_rotate_or_reflect", "template": "crop_then_rotate_or_reflect", "train_fit": False})
                    pair_traces.append({"pair_index": pair_index, "crop_primitive": crop_name, "transform": transform_name})
                    matched = True
                    break
            if matched:
                break
        if not matched:
            return _reject("crop_then_rotate_or_reflect", hyp["primitive_chain"], reason=f"train_mismatch:{pair_index}", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "crop_then_rotate_or_reflect", "template": "crop_then_rotate_or_reflect", "train_fit": False})
    assert chosen_crop is not None and chosen_transform is not None
    input_grid = validate_grid_v1(test_input)
    background = infer_background_value_v1(input_grid)
    for crop_name, cropped in _crop_candidates(input_grid, background_value=background):
        if crop_name != chosen_crop:
            continue
        objects = extract_objects_v1(cropped, background_value=background)["objects"]
        if len(objects) != 1:
            continue
        obj = objects[0]
        transformed_mask = _apply_rotation_or_reflection(obj["cells"], chosen_transform)
        try:
            predicted = rebuild_object_into_background_grid_v1(
                transformed_mask,
                color=int(obj["color"]),
                background_value=background,
                height=len(cropped),
                width=len(cropped[0]),
                anchor_row=0,
                anchor_col=0,
            )
        except Exception:
            continue
        trace_data = {
            "schema_version": SCHEMA_VERSION_V1,
            "family_name": "crop_then_rotate_or_reflect",
            "template": "crop_then_rotate_or_reflect",
            "primitive_chain": list(hyp["primitive_chain"]),
            "crop_primitive": crop_name,
            "transform": chosen_transform,
            "pair_traces": pair_traces if trace else [],
            "train_fit": True,
            "execution_kind": "compositional_executor",
        }
        return _candidate(
            family_name="crop_then_rotate_or_reflect",
            primitive_chain=hyp["primitive_chain"],
            output=predicted,
            confidence=120.0,
            train_fit=True,
            trace=trace_data,
        )
    return _reject("crop_then_rotate_or_reflect", hyp["primitive_chain"], reason="test_execution_failed", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "crop_then_rotate_or_reflect", "template": "crop_then_rotate_or_reflect", "train_fit": False})


def _infer_crop_then_tile(train_pairs: Sequence[Mapping[str, Any]], test_input: Any, hyp: Mapping[str, Any], *, trace: bool) -> CompositionalExecutorCandidate:
    chosen_crop: str | None = None
    repeat_rows: int | None = None
    repeat_cols: int | None = None
    pair_traces: list[dict[str, Any]] = []
    for pair_index, pair in enumerate(train_pairs):
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        background = infer_background_value_v1(input_grid)
        matched = False
        for crop_name, cropped in _crop_candidates(input_grid, background_value=background):
            if len(output_grid) % len(cropped) != 0 or len(output_grid[0]) % len(cropped[0]) != 0:
                continue
            pair_repeat_rows = len(output_grid) // len(cropped)
            pair_repeat_cols = len(output_grid[0]) // len(cropped[0])
            if pair_repeat_rows <= 0 or pair_repeat_cols <= 0:
                continue
            try:
                predicted = _tile_grid([list(row) for row in cropped], pair_repeat_rows, pair_repeat_cols)
            except Exception:
                continue
            if predicted != output_grid:
                continue
            if chosen_crop is None:
                chosen_crop = crop_name
            elif chosen_crop != crop_name:
                return _reject("crop_then_tile", hyp["primitive_chain"], reason="crop_primitive_inconsistent", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "crop_then_tile", "template": "crop_then_tile", "train_fit": False})
            if repeat_rows is None:
                repeat_rows = pair_repeat_rows
            elif repeat_rows != pair_repeat_rows:
                return _reject("crop_then_tile", hyp["primitive_chain"], reason="repeat_rows_inconsistent", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "crop_then_tile", "template": "crop_then_tile", "train_fit": False})
            if repeat_cols is None:
                repeat_cols = pair_repeat_cols
            elif repeat_cols != pair_repeat_cols:
                return _reject("crop_then_tile", hyp["primitive_chain"], reason="repeat_cols_inconsistent", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "crop_then_tile", "template": "crop_then_tile", "train_fit": False})
            pair_traces.append({"pair_index": pair_index, "crop_primitive": crop_name, "repeat_rows": pair_repeat_rows, "repeat_cols": pair_repeat_cols})
            matched = True
            break
        if not matched:
            return _reject("crop_then_tile", hyp["primitive_chain"], reason=f"train_mismatch:{pair_index}", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "crop_then_tile", "template": "crop_then_tile", "train_fit": False})
    assert chosen_crop is not None and repeat_rows is not None and repeat_cols is not None
    input_grid = validate_grid_v1(test_input)
    background = infer_background_value_v1(input_grid)
    for crop_name, cropped in _crop_candidates(input_grid, background_value=background):
        if crop_name != chosen_crop:
            continue
        try:
            predicted = _tile_grid([list(row) for row in cropped], repeat_rows, repeat_cols)
        except Exception:
            continue
        trace_data = {
            "schema_version": SCHEMA_VERSION_V1,
            "family_name": "crop_then_tile",
            "template": "crop_then_tile",
            "primitive_chain": list(hyp["primitive_chain"]),
            "crop_primitive": crop_name,
            "repeat_rows": repeat_rows,
            "repeat_cols": repeat_cols,
            "pair_traces": pair_traces if trace else [],
            "train_fit": True,
            "execution_kind": "compositional_executor",
        }
        return _candidate(
            family_name="crop_then_tile",
            primitive_chain=hyp["primitive_chain"],
            output=predicted,
            confidence=120.0,
            train_fit=True,
            trace=trace_data,
        )
    return _reject("crop_then_tile", hyp["primitive_chain"], reason="test_execution_failed", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "crop_then_tile", "template": "crop_then_tile", "train_fit": False})


def _strip_uniform_border(output_grid: Sequence[Sequence[int]], input_height: int, input_width: int) -> tuple[list[list[int]], dict[str, int]] | None:
    if len(output_grid) < input_height or len(output_grid[0]) < input_width:
        return None
    pad_h = len(output_grid) - input_height
    pad_w = len(output_grid[0]) - input_width
    if pad_h % 2 != 0 or pad_w % 2 != 0:
        return None
    top = bottom = pad_h // 2
    left = right = pad_w // 2
    border_values = set()
    for row_index, row in enumerate(output_grid):
        for column_index, cell in enumerate(row):
            if not (top <= row_index < top + input_height and left <= column_index < left + input_width):
                border_values.add(int(cell))
    if len(border_values) != 1:
        return None
    border_color = next(iter(border_values))
    inner = [list(row[left : left + input_width]) for row in output_grid[top : top + input_height]]
    return inner, {"top": top, "bottom": bottom, "left": left, "right": right, "border_color": border_color}


def _infer_recolor_then_border(train_pairs: Sequence[Mapping[str, Any]], test_input: Any, hyp: Mapping[str, Any], *, trace: bool) -> CompositionalExecutorCandidate:
    mapping: dict[int, int] | None = None
    padding: dict[str, int] | None = None
    pair_traces: list[dict[str, Any]] = []
    for pair_index, pair in enumerate(train_pairs):
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        stripped = _strip_uniform_border(output_grid, len(input_grid), len(input_grid[0]))
        if stripped is None:
            return _reject("recolor_then_border", hyp["primitive_chain"], reason=f"train_mismatch:{pair_index}", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "recolor_then_border", "template": "recolor_then_border", "train_fit": False})
        inner, pad = stripped
        pair_mapping = _mapping_consistent(input_grid, inner)
        if pair_mapping is None or _mapping_is_identity(input_grid, pair_mapping):
            return _reject("recolor_then_border", hyp["primitive_chain"], reason=f"recolor_mapping_invalid:{pair_index}", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "recolor_then_border", "template": "recolor_then_border", "train_fit": False})
        if mapping is None:
            mapping = pair_mapping
        elif mapping != pair_mapping:
            return _reject("recolor_then_border", hyp["primitive_chain"], reason="recolor_mapping_inconsistent", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "recolor_then_border", "template": "recolor_then_border", "train_fit": False})
        if padding is None:
            padding = pad
        elif padding != pad:
            return _reject("recolor_then_border", hyp["primitive_chain"], reason="padding_inconsistent", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "recolor_then_border", "template": "recolor_then_border", "train_fit": False})
        pair_traces.append({"pair_index": pair_index, "padding": [pad["top"], pad["bottom"], pad["left"], pad["right"]], "border_color": pad["border_color"], "mapping_size": len(pair_mapping)})
    assert mapping is not None and padding is not None
    input_grid = validate_grid_v1(test_input)
    recolored = [[int(mapping.get(int(cell), int(cell))) for cell in row] for row in input_grid]
    predicted = _pad_grid(recolored, padding["top"], padding["bottom"], padding["left"], padding["right"], padding["border_color"])
    trace_data = {
        "schema_version": SCHEMA_VERSION_V1,
        "family_name": "recolor_then_border",
        "template": "recolor_then_border",
        "primitive_chain": list(hyp["primitive_chain"]),
        "border_color": padding["border_color"],
        "padding": [padding["top"], padding["bottom"], padding["left"], padding["right"]],
        "recolor_mapping_size": len(mapping),
        "pair_traces": pair_traces if trace else [],
        "train_fit": True,
        "execution_kind": "compositional_executor",
    }
    return _candidate(
        family_name="recolor_then_border",
        primitive_chain=hyp["primitive_chain"],
        output=predicted,
        confidence=120.0,
        train_fit=True,
        trace=trace_data,
    )


def _most_frequent_foreground_color(grid: Sequence[Sequence[int]], background_value: int) -> int | None:
    counts = Counter(cell for row in grid for cell in row if int(cell) != int(background_value))
    if not counts:
        return None
    top = counts.most_common()
    if len(top) > 1 and top[0][1] == top[1][1]:
        return None
    return int(top[0][0])


def _infer_select_then_recolor(train_pairs: Sequence[Mapping[str, Any]], test_input: Any, hyp: Mapping[str, Any], *, trace: bool) -> CompositionalExecutorCandidate:
    selector_name: str | None = None
    mapping: dict[int, int] | None = None
    pair_traces: list[dict[str, Any]] = []
    for pair_index, pair in enumerate(train_pairs):
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        background = infer_background_value_v1(input_grid)
        pair_match: tuple[str, list[list[int]], dict[int, int]] | None = None
        largest_crop = None
        try:
            largest_crop = crop_to_largest_object_bbox_v1(input_grid, background_value=background)
        except Exception:
            largest_crop = None
        if largest_crop is not None and len(largest_crop) == len(output_grid) and len(largest_crop[0]) == len(output_grid[0]):
            pair_mapping = _mapping_consistent(largest_crop, output_grid)
            if pair_mapping is not None and not _mapping_is_identity(largest_crop, pair_mapping):
                pair_match = ("select_largest_object", largest_crop, pair_mapping)
        if pair_match is None:
            color = _most_frequent_foreground_color(input_grid, background)
            if color is not None:
                try:
                    selected_crop = crop_selected_color_object_v1(input_grid, color=color, background_value=background)
                except Exception:
                    selected_crop = None
                if selected_crop is not None and len(selected_crop) == len(output_grid) and len(selected_crop[0]) == len(output_grid[0]):
                    pair_mapping = _mapping_consistent(selected_crop, output_grid)
                    if pair_mapping is not None and not _mapping_is_identity(selected_crop, pair_mapping):
                        pair_match = ("select_most_frequent_foreground_color", selected_crop, pair_mapping)
        if pair_match is None:
            return _reject("select_then_recolor", hyp["primitive_chain"], reason=f"train_mismatch:{pair_index}", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "select_then_recolor", "template": "select_then_recolor", "train_fit": False})
        current_selector, selected_grid, pair_mapping = pair_match
        if selector_name is None:
            selector_name = current_selector
        elif selector_name != current_selector:
            return _reject("select_then_recolor", hyp["primitive_chain"], reason="selector_inconsistent", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "select_then_recolor", "template": "select_then_recolor", "train_fit": False})
        if mapping is None:
            mapping = pair_mapping
        elif mapping != pair_mapping:
            return _reject("select_then_recolor", hyp["primitive_chain"], reason="recolor_mapping_inconsistent", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "select_then_recolor", "template": "select_then_recolor", "train_fit": False})
        pair_traces.append({"pair_index": pair_index, "selector": current_selector, "mapping_size": len(pair_mapping)})
    assert selector_name is not None and mapping is not None
    input_grid = validate_grid_v1(test_input)
    background = infer_background_value_v1(input_grid)
    if selector_name == "select_largest_object":
        selected_grid = crop_to_largest_object_bbox_v1(input_grid, background_value=background)
    else:
        color = _most_frequent_foreground_color(input_grid, background)
        if color is None:
            return _reject("select_then_recolor", hyp["primitive_chain"], reason="selector_not_found", trace={"schema_version": SCHEMA_VERSION_V1, "family_name": "select_then_recolor", "template": "select_then_recolor", "train_fit": False})
        selected_grid = crop_selected_color_object_v1(input_grid, color=color, background_value=background)
    predicted = [[int(mapping.get(int(cell), int(cell))) for cell in row] for row in validate_grid_v1(selected_grid)]
    trace_data = {
        "schema_version": SCHEMA_VERSION_V1,
        "family_name": "select_then_recolor",
        "template": "select_then_recolor",
        "primitive_chain": list(hyp["primitive_chain"]),
        "selector": selector_name,
        "recolor_mapping_size": len(mapping),
        "pair_traces": pair_traces if trace else [],
        "train_fit": True,
        "execution_kind": "compositional_executor",
    }
    return _candidate(
        family_name="select_then_recolor",
        primitive_chain=hyp["primitive_chain"],
        output=predicted,
        confidence=120.0,
        train_fit=True,
        trace=trace_data,
    )


def execute_compositional_family_hypothesis(
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Any,
    family_hypothesis: FamilyHypothesis | Mapping[str, Any],
    *,
    trace: bool = False,
) -> CompositionalExecutorCandidate:
    hyp = _normalize_family_hypothesis(family_hypothesis)
    family_name = _safe_text(hyp.get("family_name"))
    primitive_chain = tuple(_safe_text(name) for name in hyp.get("primitive_chain", []))
    base_trace = {
        "schema_version": SCHEMA_VERSION_V1,
        "family_name": family_name,
        "primitive_chain": list(primitive_chain),
        "train_fit": False,
        "execution_kind": "compositional_executor",
        "trace_enabled": bool(trace),
    }
    if family_name not in SUPPORTED_TEMPLATES_V1:
        return _reject(family_name, primitive_chain, reason="unsupported_family", trace=base_trace)
    if len(primitive_chain) != 2:
        return _reject(family_name, primitive_chain, reason="primitive_chain_too_long", trace=base_trace)
    if family_name == "crop_then_recolor" and not (primitive_chain[0].startswith("crop_") and primitive_chain[1].startswith("recolor_")):
        return _reject(family_name, primitive_chain, reason="primitive_chain_incompatible", trace=base_trace)
    if family_name == "crop_then_rotate_or_reflect" and not (primitive_chain[0].startswith("crop_") and (primitive_chain[1].startswith("rotate_") or primitive_chain[1].startswith("reflect_"))):
        return _reject(family_name, primitive_chain, reason="primitive_chain_incompatible", trace=base_trace)
    if family_name == "crop_then_tile" and not (primitive_chain[0].startswith("crop_") and primitive_chain[1] == "tile_grid"):
        return _reject(family_name, primitive_chain, reason="primitive_chain_incompatible", trace=base_trace)
    if family_name == "recolor_then_border" and not (primitive_chain[0].startswith("recolor_") and primitive_chain[1] == "add_uniform_border"):
        return _reject(family_name, primitive_chain, reason="primitive_chain_incompatible", trace=base_trace)
    if family_name == "select_then_recolor" and not (primitive_chain[0].startswith("select_") and primitive_chain[1].startswith("recolor_")):
        return _reject(family_name, primitive_chain, reason="primitive_chain_incompatible", trace=base_trace)
    try:
        for pair in train_pairs:
            validate_grid_v1(_pair_input(pair))
            validate_grid_v1(_pair_output(pair))
    except Exception as exc:
        return _reject(family_name, primitive_chain, reason=f"invalid_grid:{type(exc).__name__}", trace=base_trace)
    try:
        if family_name == "crop_then_recolor":
            return _infer_crop_then_recolor(train_pairs, test_input, hyp, trace=trace)
        if family_name == "crop_then_rotate_or_reflect":
            return _infer_crop_then_rotate_or_reflect(train_pairs, test_input, hyp, trace=trace)
        if family_name == "crop_then_tile":
            return _infer_crop_then_tile(train_pairs, test_input, hyp, trace=trace)
        if family_name == "recolor_then_border":
            return _infer_recolor_then_border(train_pairs, test_input, hyp, trace=trace)
        if family_name == "select_then_recolor":
            return _infer_select_then_recolor(train_pairs, test_input, hyp, trace=trace)
    except Exception as exc:
        return _reject(family_name, primitive_chain, reason=f"executor_exception:{type(exc).__name__}", trace=base_trace)
    return _reject(family_name, primitive_chain, reason="unsupported_family", trace=base_trace)


def execute_compositional_family_hypotheses(
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Any,
    family_hypotheses: Sequence[FamilyHypothesis | Mapping[str, Any]],
    *,
    trace: bool = False,
) -> list[CompositionalExecutorCandidate]:
    candidates = [execute_compositional_family_hypothesis(train_pairs, test_input, hypothesis, trace=trace) for hypothesis in family_hypotheses]
    return candidates


__all__ = [
    "SCHEMA_VERSION_V1",
    "SUPPORTED_TEMPLATES_V1",
    "CompositionalExecutorCandidate",
    "execute_compositional_family_hypothesis",
    "execute_compositional_family_hypotheses",
]
