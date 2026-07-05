"""ARC-AGI-2 primitive discovery engine V1.

Metadata-safe applicability discovery over the primitive registry and task
feature signatures. This module does not emit final ARC answers, does not run
public data, and does not execute full hypothesis search.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from weslr.arc_object_extraction_v1 import (
    crop_selected_color_object_v1,
    crop_to_foreground_bbox_v1,
    crop_to_largest_object_bbox_v1,
    extract_objects_v1,
    infer_background_value_v1,
    translate_object_v1,
    validate_grid_v1,
)
from weslr.arc_primitive_registry_v1 import PrimitiveDescriptor, PrimitiveRegistry, build_arc_primitive_registry_v1
from weslr.arc_resize_tile_canvas_v1 import _pad_grid, _repeat_grid, _tile_grid
from weslr.arc_shape_geometry_v1 import canonical_shape_signature_v1, reflect_object_mask_v1, rotate_object_mask_v1
from weslr.arc_task_feature_signature_v1 import build_arc_task_feature_signature_v1

SCHEMA_VERSION_V1 = "ArcPrimitiveDiscoveryEngineV1"

STATUS_ACCEPTED_V1 = "accepted"
STATUS_REJECTED_V1 = "rejected"
STATUS_UNCERTAIN_V1 = "uncertain"

_STATUS_ORDER_V1 = {
    STATUS_ACCEPTED_V1: 0,
    STATUS_REJECTED_V1: 1,
    STATUS_UNCERTAIN_V1: 2,
}


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


def _grid_copy(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _collect_feature_labels(task_signature: Mapping[str, Any]) -> list[str]:
    labels: set[str] = set()
    task_level = task_signature.get("task_level_signature", {})
    for key in (
        "consistent_size_relation_labels",
        "consistent_palette_relation_labels",
        "consistent_object_count_relation_labels",
        "consistent_foreground_count_relation_labels",
        "possible_primitive_hint_intersection",
        "contradiction_labels",
    ):
        value = task_level.get(key, [])
        if isinstance(value, list):
            labels.update(str(item) for item in value)
    for pair_signature in task_signature.get("train_pair_signatures", []):
        if not isinstance(pair_signature, Mapping):
            continue
        labels.update(str(item) for item in pair_signature.get("size_relation_labels", []))
        labels.update(str(item) for item in pair_signature.get("palette_relation_labels", []))
        labels.update(str(item) for item in pair_signature.get("object_count_relation_labels", []))
        labels.update(str(item) for item in pair_signature.get("foreground_count_relation_labels", []))
        size_relation = pair_signature.get("size_relation", {})
        labels.update(str(item) for item in size_relation.get("candidate_primitive_hint_labels", []))
        labels.add(str(size_relation.get("output_size_relation", "")))
        if size_relation.get("same_size"):
            labels.add("same_size")
        if size_relation.get("palette_changed"):
            labels.add("palette_changed")
        if size_relation.get("foreground_count_changed"):
            labels.add("foreground_count_changed")
        if size_relation.get("object_count_changed"):
            labels.add("object_count_changed")
    return sorted(label for label in labels if label)


def _grid_dimensions(grid: Sequence[Sequence[int]]) -> tuple[int, int]:
    return len(grid), len(grid[0])


def _line_shape(grid: Sequence[Sequence[int]]) -> bool:
    height, width = _grid_dimensions(grid)
    return height == 1 or width == 1


def _square_shape(grid: Sequence[Sequence[int]]) -> bool:
    height, width = _grid_dimensions(grid)
    return height == width


def _uniform_grid_color(grid: Sequence[Sequence[int]]) -> int | None:
    colors = {cell for row in grid for cell in row}
    if len(colors) != 1:
        return None
    return next(iter(colors))


def _object_signature(grid: Sequence[Sequence[int]], *, background_value: int | None = None) -> dict[str, Any]:
    normalized = validate_grid_v1(grid)
    background = infer_background_value_v1(normalized, explicit_background=background_value)
    extracted = extract_objects_v1(normalized, background_value=background)
    objects = extracted["objects"]
    sizes = [int(obj["size"]) for obj in objects]
    colors = [int(obj["color"]) for obj in objects]
    bboxes = [list(map(int, obj["bbox"])) for obj in objects]
    return {
        "background": background,
        "object_count": len(objects),
        "object_sizes": sizes,
        "object_colors": colors,
        "bounding_boxes": bboxes,
        "foreground_cell_count": sum(sizes),
        "foreground_colors": sorted(set(colors)),
        "single_object": len(objects) == 1,
        "objects": objects,
        "normalized": normalized,
    }


def _color_mapping_from_pair(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> dict[int, int] | None:
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


def _scale_match(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> dict[str, int] | None:
    in_h, in_w = _grid_dimensions(input_grid)
    out_h, out_w = _grid_dimensions(output_grid)
    if in_h <= 0 or in_w <= 0:
        return None
    if out_h % in_h != 0 or out_w % in_w != 0:
        return None
    scale_rows = out_h // in_h
    scale_cols = out_w // in_w
    if scale_rows <= 1 and scale_cols <= 1:
        return None
    if _repeat_grid(_grid_copy(input_grid), scale_rows, scale_cols) == _grid_copy(output_grid):
        return {"scale_rows": scale_rows, "scale_cols": scale_cols}
    return None


def _tile_match(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> dict[str, int] | None:
    in_h, in_w = _grid_dimensions(input_grid)
    out_h, out_w = _grid_dimensions(output_grid)
    if in_h <= 0 or in_w <= 0:
        return None
    if out_h % in_h != 0 or out_w % in_w != 0:
        return None
    repeat_rows = out_h // in_h
    repeat_cols = out_w // in_w
    if repeat_rows <= 1 and repeat_cols <= 1:
        return None
    if _tile_grid(_grid_copy(input_grid), repeat_rows, repeat_cols) == _grid_copy(output_grid):
        return {"repeat_rows": repeat_rows, "repeat_cols": repeat_cols}
    return None


def _border_match(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> dict[str, int] | None:
    in_h, in_w = _grid_dimensions(input_grid)
    out_h, out_w = _grid_dimensions(output_grid)
    if out_h < in_h or out_w < in_w:
        return None
    pad_h = out_h - in_h
    pad_w = out_w - in_w
    if pad_h % 2 != 0 or pad_w % 2 != 0:
        return None
    top = bottom = pad_h // 2
    left = right = pad_w // 2
    if top == 0 and left == 0:
        return None
    border_color = output_grid[0][0]
    expected = _pad_grid(_grid_copy(input_grid), top, bottom, left, right, border_color)
    if expected == _grid_copy(output_grid):
        return {"top": top, "bottom": bottom, "left": left, "right": right, "border_color": int(border_color)}
    return None


def _crop_then_tile_match(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> dict[str, int] | None:
    try:
        cropped = crop_to_foreground_bbox_v1(input_grid)
    except Exception:
        return None
    return _tile_match(cropped, output_grid)


def _translation_delta(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> tuple[int, int] | None:
    input_info = _object_signature(input_grid)
    output_info = _object_signature(output_grid)
    if not input_info["single_object"] or not output_info["single_object"]:
        return None
    input_obj = input_info["objects"][0]
    output_obj = output_info["objects"][0]
    if canonical_shape_signature_v1(input_obj["cells"]) != canonical_shape_signature_v1(output_obj["cells"]):
        return None
    in_bbox = input_obj["bbox"]
    out_bbox = output_obj["bbox"]
    return int(out_bbox[0]) - int(in_bbox[0]), int(out_bbox[1]) - int(in_bbox[1])


def _rotation_or_reflection_match(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> str | None:
    input_info = _object_signature(input_grid)
    output_info = _object_signature(output_grid)
    if not input_info["single_object"] or not output_info["single_object"]:
        return None
    input_obj = input_info["objects"][0]
    output_obj = output_info["objects"][0]
    input_shape = canonical_shape_signature_v1(input_obj["cells"])
    output_shape = canonical_shape_signature_v1(output_obj["cells"])
    if input_shape == output_shape:
        return None
    if canonical_shape_signature_v1(rotate_object_mask_v1(input_obj["cells"], 1)) == output_shape:
        return "rotate_object_90"
    if canonical_shape_signature_v1(rotate_object_mask_v1(input_obj["cells"], 2)) == output_shape:
        return "rotate_object_180"
    if canonical_shape_signature_v1(rotate_object_mask_v1(input_obj["cells"], 3)) == output_shape:
        return "rotate_object_270"
    if canonical_shape_signature_v1(reflect_object_mask_v1(input_obj["cells"], "horizontal")) == output_shape:
        return "reflect_object_horizontal"
    if canonical_shape_signature_v1(reflect_object_mask_v1(input_obj["cells"], "vertical")) == output_shape:
        return "reflect_object_vertical"
    return None


def _count_line_match(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]], *, use_objects: bool) -> dict[str, Any] | None:
    input_info = _object_signature(input_grid)
    out_h, out_w = _grid_dimensions(output_grid)
    if not _line_shape(output_grid):
        return None
    color = _uniform_grid_color(output_grid)
    if color is None:
        return None
    if use_objects:
        target = input_info["object_count"]
        source_label = "object_count"
    else:
        target = input_info["foreground_cell_count"]
        source_label = "foreground_cell_count"
    if out_h * out_w != target:
        return None
    return {
        "orientation": "horizontal" if out_h == 1 else "vertical",
        "line_color": int(color),
        "count_source": source_label,
        "count_value": int(target),
    }


def _unique_color_count_match(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> dict[str, Any] | None:
    input_info = _object_signature(input_grid)
    out_h, out_w = _grid_dimensions(output_grid)
    if not _line_shape(output_grid):
        return None
    color = _uniform_grid_color(output_grid)
    if color is None:
        return None
    unique_count = len(input_info["foreground_colors"])
    if out_h * out_w != unique_count:
        return None
    return {
        "orientation": "horizontal" if out_h == 1 else "vertical",
        "line_color": int(color),
        "count_value": int(unique_count),
    }


def _square_count_match(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> dict[str, Any] | None:
    input_info = _object_signature(input_grid)
    out_h, out_w = _grid_dimensions(output_grid)
    if not _square_shape(output_grid):
        return None
    color = _uniform_grid_color(output_grid)
    if color is None:
        return None
    if out_h != input_info["object_count"]:
        return None
    return {"fill_color": int(color), "square_size": int(out_h), "count_value": int(input_info["object_count"])}


@dataclass(frozen=True)
class PrimitiveDiscoveryHint:
    primitive_name: str
    family: str
    status: str
    confidence: float
    reason: str
    inferred_parameters: dict[str, Any] = field(default_factory=dict)
    source_feature_labels: list[str] = field(default_factory=list)
    trace: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "primitive_name", _safe_text(self.primitive_name))
        object.__setattr__(self, "family", _safe_text(self.family))
        object.__setattr__(self, "status", _safe_text(self.status))
        object.__setattr__(self, "reason", _safe_text(self.reason))
        object.__setattr__(self, "confidence", float(self.confidence))
        object.__setattr__(self, "inferred_parameters", _json_safe(self.inferred_parameters))
        object.__setattr__(self, "source_feature_labels", sorted(_safe_text(label) for label in self.source_feature_labels if _safe_text(label)))
        object.__setattr__(self, "trace", _json_safe(self.trace))
        if self.status not in _STATUS_ORDER_V1:
            raise ValueError(f"invalid_status:{self.status}")

    def to_json_safe_dict(self) -> dict[str, Any]:
        return {
            "primitive_name": self.primitive_name,
            "family": self.family,
            "status": self.status,
            "confidence": float(self.confidence),
            "reason": self.reason,
            "inferred_parameters": _json_safe(self.inferred_parameters),
            "source_feature_labels": list(self.source_feature_labels),
            "trace": _json_safe(self.trace),
        }


@dataclass(frozen=True)
class PrimitiveDiscoveryResult:
    accepted_hints: list[PrimitiveDiscoveryHint] = field(default_factory=list)
    rejected_hints: list[PrimitiveDiscoveryHint] = field(default_factory=list)
    uncertain_hints: list[PrimitiveDiscoveryHint] = field(default_factory=list)
    primitive_count: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    uncertain_count: int = 0
    trace: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "accepted_hints", tuple(self._sorted_hints(self.accepted_hints, STATUS_ACCEPTED_V1)))
        object.__setattr__(self, "rejected_hints", tuple(self._sorted_hints(self.rejected_hints, STATUS_REJECTED_V1)))
        object.__setattr__(self, "uncertain_hints", tuple(self._sorted_hints(self.uncertain_hints, STATUS_UNCERTAIN_V1)))
        object.__setattr__(self, "primitive_count", int(self.primitive_count))
        object.__setattr__(self, "accepted_count", int(self.accepted_count))
        object.__setattr__(self, "rejected_count", int(self.rejected_count))
        object.__setattr__(self, "uncertain_count", int(self.uncertain_count))
        object.__setattr__(self, "trace", _json_safe(self.trace))

    @staticmethod
    def _sorted_hints(hints: Sequence[PrimitiveDiscoveryHint], status: str) -> list[PrimitiveDiscoveryHint]:
        filtered = [hint for hint in hints if hint.status == status]
        return sorted(filtered, key=lambda hint: (_STATUS_ORDER_V1.get(hint.status, 99), -float(hint.confidence), hint.primitive_name))

    def to_json_safe_dict(self) -> dict[str, Any]:
        return {
            "accepted_hints": [hint.to_json_safe_dict() for hint in self.accepted_hints],
            "rejected_hints": [hint.to_json_safe_dict() for hint in self.rejected_hints],
            "uncertain_hints": [hint.to_json_safe_dict() for hint in self.uncertain_hints],
            "primitive_count": int(self.primitive_count),
            "accepted_count": int(self.accepted_count),
            "rejected_count": int(self.rejected_count),
            "uncertain_count": int(self.uncertain_count),
            "trace": _json_safe(self.trace),
        }


def _make_hint(
    primitive_name: str,
    family: str,
    status: str,
    confidence: float,
    reason: str,
    *,
    inferred_parameters: Mapping[str, Any] | None = None,
    source_feature_labels: Sequence[str] | None = None,
    trace: Mapping[str, Any] | None = None,
) -> PrimitiveDiscoveryHint:
    return PrimitiveDiscoveryHint(
        primitive_name=primitive_name,
        family=family,
        status=status,
        confidence=confidence,
        reason=reason,
        inferred_parameters=dict(inferred_parameters or {}),
        source_feature_labels=list(source_feature_labels or []),
        trace=dict(trace or {}),
    )


def _evaluate_crop_primitive(
    descriptor: PrimitiveDescriptor,
    train_pairs: Sequence[Mapping[str, Any]],
    feature_labels: Sequence[str],
) -> PrimitiveDiscoveryHint:
    pair_results: list[dict[str, Any]] = []
    hard_negative = False
    crop_like = 0
    for index, pair in enumerate(train_pairs):
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        exact = False
        reason = "not_cropped"
        params: dict[str, Any] = {}
        try:
            exact = crop_to_foreground_bbox_v1(input_grid) == output_grid
            if exact:
                params = {"mode": "foreground_bbox"}
                reason = "foreground_bbox_match"
            elif crop_to_largest_object_bbox_v1(input_grid) == output_grid:
                exact = True
                params = {"mode": "largest_object_bbox"}
                reason = "largest_object_bbox_match"
            else:
                input_info = _object_signature(input_grid)
                output_info = _object_signature(output_grid)
                if output_info["object_count"] == 1 and output_info["foreground_cell_count"] < input_info["foreground_cell_count"]:
                    reason = "smaller_output_with_foreground_reduction"
                    crop_like += 1
                if output_info["object_count"] == 1 and output_info["object_count"] <= input_info["object_count"]:
                    params = {"output_object_count": output_info["object_count"]}
        except Exception as exc:
            reason = f"crop_check_failed:{type(exc).__name__}"
            hard_negative = True
        if exact:
            crop_like += 1
        pair_results.append({"pair_index": index, "exact": exact, "reason": reason})
    if hard_negative:
        return _make_hint(
            descriptor.primitive_name,
            descriptor.family,
            STATUS_REJECTED_V1,
            0.1,
            "crop_check_failed",
            inferred_parameters={},
            source_feature_labels=feature_labels,
            trace={"pair_results": pair_results, "decision": "rejected", "family": descriptor.family},
        )
    if crop_like == len(train_pairs) and len(train_pairs) > 0:
        return _make_hint(
            descriptor.primitive_name,
            descriptor.family,
            STATUS_ACCEPTED_V1,
            0.96,
            "exact_crop_match",
            inferred_parameters={"mode": descriptor.primitive_name},
            source_feature_labels=[*feature_labels, "possible_crop"],
            trace={"pair_results": pair_results, "decision": "accepted", "family": descriptor.family},
        )
    if any(result["exact"] for result in pair_results):
        return _make_hint(
            descriptor.primitive_name,
            descriptor.family,
            STATUS_UNCERTAIN_V1,
            0.54,
            "partial_crop_evidence",
            inferred_parameters={},
            source_feature_labels=[*feature_labels, "possible_crop"],
            trace={"pair_results": pair_results, "decision": "uncertain", "family": descriptor.family},
        )
    if "possible_crop" not in feature_labels and all("output_smaller" not in label for label in feature_labels):
        return _make_hint(
            descriptor.primitive_name,
            descriptor.family,
            STATUS_REJECTED_V1,
            0.12,
            "no_crop_evidence",
            inferred_parameters={},
            source_feature_labels=list(feature_labels),
            trace={"pair_results": pair_results, "decision": "rejected", "family": descriptor.family},
        )
    return _make_hint(
        descriptor.primitive_name,
        descriptor.family,
        STATUS_UNCERTAIN_V1,
        0.31,
        "insufficient_crop_evidence",
        inferred_parameters={},
        source_feature_labels=list(feature_labels),
        trace={"pair_results": pair_results, "decision": "uncertain", "family": descriptor.family},
    )


def _evaluate_translation_primitive(
    descriptor: PrimitiveDescriptor,
    train_pairs: Sequence[Mapping[str, Any]],
    feature_labels: Sequence[str],
) -> PrimitiveDiscoveryHint:
    deltas: set[tuple[int, int]] = set()
    pair_results: list[dict[str, Any]] = []
    for index, pair in enumerate(train_pairs):
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        input_info = _object_signature(input_grid)
        output_info = _object_signature(output_grid)
        delta = _translation_delta(input_grid, output_grid)
        exact = delta is not None and delta != (0, 0) and input_info["background"] == output_info["background"] and input_info["object_count"] == output_info["object_count"] and input_info["foreground_cell_count"] == output_info["foreground_cell_count"]
        if delta is not None:
            deltas.add(delta)
        pair_results.append({"pair_index": index, "exact": exact, "delta": list(delta) if delta is not None else None})
    if any(result["exact"] for result in pair_results) and len(deltas) == 1 and len(pair_results) == len(train_pairs):
        delta = next(iter(deltas))
        confidence = 0.98 if descriptor.primitive_name == "translate_single_object" else 0.91
        return _make_hint(
            descriptor.primitive_name,
            descriptor.family,
            STATUS_ACCEPTED_V1,
            confidence,
            "shape_preserving_translation",
            inferred_parameters={"delta_row": delta[0], "delta_col": delta[1]},
            source_feature_labels=[*feature_labels, "same_size", "possible_translate"],
            trace={"pair_results": pair_results, "decision": "accepted", "family": descriptor.family},
        )
    if any(result["exact"] for result in pair_results):
        return _make_hint(
            descriptor.primitive_name,
            descriptor.family,
            STATUS_UNCERTAIN_V1,
            0.54,
            "partial_translation_evidence",
            inferred_parameters={"deltas": [list(delta) for delta in sorted(deltas)]} if deltas else {},
            source_feature_labels=[*feature_labels, "possible_translate"],
            trace={"pair_results": pair_results, "decision": "uncertain", "family": descriptor.family},
        )
    if "same_size" not in feature_labels or "possible_translate" not in feature_labels:
        return _make_hint(
            descriptor.primitive_name,
            descriptor.family,
            STATUS_REJECTED_V1,
            0.11,
            "translation_incompatible_with_task_signature",
            inferred_parameters={},
            source_feature_labels=list(feature_labels),
            trace={"pair_results": pair_results, "decision": "rejected", "family": descriptor.family},
        )
    return _make_hint(
        descriptor.primitive_name,
        descriptor.family,
        STATUS_UNCERTAIN_V1,
        0.28,
        "insufficient_translation_evidence",
        inferred_parameters={},
        source_feature_labels=list(feature_labels),
        trace={"pair_results": pair_results, "decision": "uncertain", "family": descriptor.family},
    )


def _evaluate_geometry_primitive(
    descriptor: PrimitiveDescriptor,
    train_pairs: Sequence[Mapping[str, Any]],
    feature_labels: Sequence[str],
) -> PrimitiveDiscoveryHint:
    pair_results: list[dict[str, Any]] = []
    matched = 0
    rotations: set[str] = set()
    for index, pair in enumerate(train_pairs):
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        relation = _rotation_or_reflection_match(input_grid, output_grid)
        input_info = _object_signature(input_grid)
        output_info = _object_signature(output_grid)
        exact = relation == descriptor.primitive_name and input_info["object_count"] == 1 and output_info["object_count"] == 1 and input_info["background"] == output_info["background"]
        if relation:
            rotations.add(relation)
        if exact:
            matched += 1
        pair_results.append({"pair_index": index, "exact": exact, "relation": relation})
    if matched == len(train_pairs) and matched > 0:
        return _make_hint(
            descriptor.primitive_name,
            descriptor.family,
            STATUS_ACCEPTED_V1,
            0.97,
            "exact_geometry_match",
            inferred_parameters={"transform": descriptor.primitive_name},
            source_feature_labels=[*feature_labels, "possible_rotate_or_reflect"],
            trace={"pair_results": pair_results, "decision": "accepted", "family": descriptor.family},
        )
    if any(result["relation"] for result in pair_results):
        return _make_hint(
            descriptor.primitive_name,
            descriptor.family,
            STATUS_UNCERTAIN_V1,
            0.49,
            "geometry_evidence_but_not_exact",
            inferred_parameters={"candidate_transforms": sorted(rotations)},
            source_feature_labels=[*feature_labels, "possible_rotate_or_reflect"],
            trace={"pair_results": pair_results, "decision": "uncertain", "family": descriptor.family},
        )
    if "possible_rotate_or_reflect" not in feature_labels or "same_size" not in feature_labels:
        return _make_hint(
            descriptor.primitive_name,
            descriptor.family,
            STATUS_REJECTED_V1,
            0.09,
            "geometry_incompatible_with_task_signature",
            inferred_parameters={},
            source_feature_labels=list(feature_labels),
            trace={"pair_results": pair_results, "decision": "rejected", "family": descriptor.family},
        )
    return _make_hint(
        descriptor.primitive_name,
        descriptor.family,
        STATUS_UNCERTAIN_V1,
        0.25,
        "insufficient_geometry_evidence",
        inferred_parameters={},
        source_feature_labels=list(feature_labels),
        trace={"pair_results": pair_results, "decision": "uncertain", "family": descriptor.family},
    )


def _evaluate_color_primitive(
    descriptor: PrimitiveDescriptor,
    train_pairs: Sequence[Mapping[str, Any]],
    feature_labels: Sequence[str],
) -> PrimitiveDiscoveryHint:
    mappings: list[dict[int, int]] = []
    pair_results: list[dict[str, Any]] = []
    for index, pair in enumerate(train_pairs):
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        input_info = _object_signature(input_grid)
        output_info = _object_signature(output_grid)
        mapping = _color_mapping_from_pair(input_grid, output_grid)
        palette_changed = sorted(set(cell for row in input_grid for cell in row)) != sorted(set(cell for row in output_grid for cell in row))
        structure_same = input_info["object_count"] == output_info["object_count"] and input_info["bounding_boxes"] == output_info["bounding_boxes"] and input_info["foreground_cell_count"] == output_info["foreground_cell_count"]
        exact = mapping is not None and palette_changed and structure_same and _grid_dimensions(input_grid) == _grid_dimensions(output_grid)
        if mapping is not None:
            mappings.append(mapping)
        pair_results.append({"pair_index": index, "exact": exact, "palette_changed": palette_changed, "structure_same": structure_same})
    all_same_size = all(_grid_dimensions(validate_grid_v1(_pair_input(pair))) == _grid_dimensions(validate_grid_v1(_pair_output(pair))) for pair in train_pairs)
    any_palette_changed = any(result["palette_changed"] for result in pair_results)
    if descriptor.primitive_name == "swap_two_colors":
        if all(
            len({source for source, target in mapping.items() if source != target}) == 2 and all(mapping.get(target) == source for source, target in list(mapping.items())[:2])
            for mapping in mappings
        ) and any_palette_changed:
            return _make_hint(
                descriptor.primitive_name,
                descriptor.family,
                STATUS_ACCEPTED_V1,
                0.95,
                "exact_two_color_swap",
                inferred_parameters={"mapping_size": 2},
                source_feature_labels=[*feature_labels, "possible_recolor"],
                trace={"pair_results": pair_results, "decision": "accepted", "family": descriptor.family},
            )
    if descriptor.primitive_name == "recolor_background":
        if any_palette_changed and all_same_size:
            return _make_hint(
                descriptor.primitive_name,
                descriptor.family,
                STATUS_ACCEPTED_V1,
                0.92,
                "background_or_global_recolor",
                inferred_parameters={},
                source_feature_labels=[*feature_labels, "possible_recolor"],
                trace={"pair_results": pair_results, "decision": "accepted", "family": descriptor.family},
            )
    if descriptor.primitive_name == "recolor_source_color":
        if any_palette_changed and all_same_size:
            source_colors = sorted({source for mapping in mappings for source, target in mapping.items() if source != target})
            return _make_hint(
                descriptor.primitive_name,
                descriptor.family,
                STATUS_ACCEPTED_V1,
                0.9,
                "source_color_recolor",
                inferred_parameters={"source_colors": source_colors},
                source_feature_labels=[*feature_labels, "possible_recolor"],
                trace={"pair_results": pair_results, "decision": "accepted", "family": descriptor.family},
            )
    if descriptor.primitive_name == "recolor_foreground":
        if any_palette_changed and all_same_size:
            return _make_hint(
                descriptor.primitive_name,
                descriptor.family,
                STATUS_ACCEPTED_V1,
                0.91,
                "foreground_recolor",
                inferred_parameters={},
                source_feature_labels=[*feature_labels, "possible_recolor"],
                trace={"pair_results": pair_results, "decision": "accepted", "family": descriptor.family},
            )
    if descriptor.primitive_name == "recolor_global":
        if any_palette_changed and all_same_size:
            return _make_hint(
                descriptor.primitive_name,
                descriptor.family,
                STATUS_ACCEPTED_V1,
                0.94,
                "global_recolor",
                inferred_parameters={},
                source_feature_labels=[*feature_labels, "possible_recolor"],
                trace={"pair_results": pair_results, "decision": "accepted", "family": descriptor.family},
            )
    if not any_palette_changed:
        return _make_hint(
            descriptor.primitive_name,
            descriptor.family,
            STATUS_REJECTED_V1,
            0.1,
            "palette_unchanged",
            inferred_parameters={},
            source_feature_labels=list(feature_labels),
            trace={"pair_results": pair_results, "decision": "rejected", "family": descriptor.family},
        )
    return _make_hint(
        descriptor.primitive_name,
        descriptor.family,
        STATUS_UNCERTAIN_V1,
        0.34,
        "insufficient_color_evidence",
        inferred_parameters={},
        source_feature_labels=list(feature_labels),
        trace={"pair_results": pair_results, "decision": "uncertain", "family": descriptor.family},
    )


def _evaluate_resize_tile_primitive(
    descriptor: PrimitiveDescriptor,
    train_pairs: Sequence[Mapping[str, Any]],
    feature_labels: Sequence[str],
) -> PrimitiveDiscoveryHint:
    pair_results: list[dict[str, Any]] = []
    exact_matches = 0
    inferred_params: list[dict[str, Any]] = []
    for index, pair in enumerate(train_pairs):
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        input_dims = _grid_dimensions(input_grid)
        output_dims = _grid_dimensions(output_grid)
        size_relation = "same" if input_dims == output_dims else "larger" if output_dims[0] >= input_dims[0] and output_dims[1] >= input_dims[1] else "smaller"
        exact: dict[str, Any] | None = None
        if descriptor.primitive_name == "scale_cells_integer":
            exact = _scale_match(input_grid, output_grid)
        elif descriptor.primitive_name == "tile_grid":
            exact = _tile_match(input_grid, output_grid)
        elif descriptor.primitive_name == "add_uniform_border":
            exact = _border_match(input_grid, output_grid)
        elif descriptor.primitive_name == "crop_then_tile":
            exact = _crop_then_tile_match(input_grid, output_grid)
        if exact is not None:
            exact_matches += 1
            inferred_params.append(exact)
        pair_results.append({"pair_index": index, "exact": exact is not None, "size_relation": size_relation})
    if exact_matches == len(train_pairs) and exact_matches > 0:
        best_params = inferred_params[0] if inferred_params else {}
        source_labels = [*feature_labels, "possible_tile" if descriptor.primitive_name in {"tile_grid", "crop_then_tile"} else "possible_scale", "possible_border" if descriptor.primitive_name == "add_uniform_border" else ""]
        source_labels = [label for label in source_labels if label]
        return _make_hint(
            descriptor.primitive_name,
            descriptor.family,
            STATUS_ACCEPTED_V1,
            0.97,
            "exact_resize_tile_match",
            inferred_parameters=best_params,
            source_feature_labels=source_labels,
            trace={"pair_results": pair_results, "decision": "accepted", "family": descriptor.family},
        )
    if exact_matches > 0:
        return _make_hint(
            descriptor.primitive_name,
            descriptor.family,
            STATUS_UNCERTAIN_V1,
            0.5,
            "partial_resize_tile_evidence",
            inferred_parameters=inferred_params[0] if inferred_params else {},
            source_feature_labels=[*feature_labels, "possible_tile", "possible_scale", "possible_border"],
            trace={"pair_results": pair_results, "decision": "uncertain", "family": descriptor.family},
        )
    if "output_larger" not in feature_labels and "possible_tile" not in feature_labels and "possible_scale" not in feature_labels and "possible_border" not in feature_labels:
        return _make_hint(
            descriptor.primitive_name,
            descriptor.family,
            STATUS_REJECTED_V1,
            0.08,
            "resize_tile_incompatible_with_task_signature",
            inferred_parameters={},
            source_feature_labels=list(feature_labels),
            trace={"pair_results": pair_results, "decision": "rejected", "family": descriptor.family},
        )
    return _make_hint(
        descriptor.primitive_name,
        descriptor.family,
        STATUS_UNCERTAIN_V1,
        0.27,
        "insufficient_resize_tile_evidence",
        inferred_parameters={},
        source_feature_labels=list(feature_labels),
        trace={"pair_results": pair_results, "decision": "uncertain", "family": descriptor.family},
    )


def _evaluate_count_primitive(
    descriptor: PrimitiveDescriptor,
    train_pairs: Sequence[Mapping[str, Any]],
    feature_labels: Sequence[str],
) -> PrimitiveDiscoveryHint:
    pair_results: list[dict[str, Any]] = []
    exact_matches = 0
    inferred_params: list[dict[str, Any]] = []
    for index, pair in enumerate(train_pairs):
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        exact: dict[str, Any] | None = None
        if descriptor.primitive_name in {"count_objects_to_line", "foreground_cell_count_to_line", "unique_color_count_to_line"}:
            exact = _count_line_match(input_grid, output_grid, use_objects=descriptor.primitive_name == "count_objects_to_line")
            if descriptor.primitive_name == "foreground_cell_count_to_line":
                exact = _count_line_match(input_grid, output_grid, use_objects=False)
            if descriptor.primitive_name == "unique_color_count_to_line":
                exact = _unique_color_count_match(input_grid, output_grid)
        elif descriptor.primitive_name == "object_count_to_square":
            exact = _square_count_match(input_grid, output_grid)
        elif descriptor.primitive_name == "select_largest_object":
            try:
                exact = {"selected": True} if crop_to_largest_object_bbox_v1(input_grid) == output_grid else None
            except Exception:
                exact = None
        elif descriptor.primitive_name == "select_most_frequent_foreground_color":
            input_info = _object_signature(input_grid)
            histogram = Counter(cell for row in input_grid for cell in row)
            background = input_info["background"]
            foreground_hist = {color: count for color, count in histogram.items() if color != background}
            if foreground_hist:
                most_common_color, count = sorted(foreground_hist.items(), key=lambda item: (-item[1], item[0]))[0]
                if _uniform_grid_color(output_grid) == most_common_color:
                    exact = {"selected_color": int(most_common_color), "count": int(count)}
        if exact is not None:
            exact_matches += 1
            inferred_params.append(exact)
        pair_results.append({"pair_index": index, "exact": exact is not None, "primitive": descriptor.primitive_name})
    if exact_matches == len(train_pairs) and exact_matches > 0:
        return _make_hint(
            descriptor.primitive_name,
            descriptor.family,
            STATUS_ACCEPTED_V1,
            0.96,
            "exact_count_match",
            inferred_parameters=inferred_params[0] if inferred_params else {},
            source_feature_labels=[*feature_labels, "possible_count_output"],
            trace={"pair_results": pair_results, "decision": "accepted", "family": descriptor.family},
        )
    if exact_matches > 0:
        return _make_hint(
            descriptor.primitive_name,
            descriptor.family,
            STATUS_UNCERTAIN_V1,
            0.51,
            "partial_count_evidence",
            inferred_parameters=inferred_params[0] if inferred_params else {},
            source_feature_labels=[*feature_labels, "possible_count_output"],
            trace={"pair_results": pair_results, "decision": "uncertain", "family": descriptor.family},
        )
    if "possible_count_output" not in feature_labels and not any(label.endswith("_changed") for label in feature_labels):
        return _make_hint(
            descriptor.primitive_name,
            descriptor.family,
            STATUS_REJECTED_V1,
            0.09,
            "count_hint_absent",
            inferred_parameters={},
            source_feature_labels=list(feature_labels),
            trace={"pair_results": pair_results, "decision": "rejected", "family": descriptor.family},
        )
    return _make_hint(
        descriptor.primitive_name,
        descriptor.family,
        STATUS_UNCERTAIN_V1,
        0.26,
        "insufficient_count_evidence",
        inferred_parameters={},
        source_feature_labels=list(feature_labels),
        trace={"pair_results": pair_results, "decision": "uncertain", "family": descriptor.family},
    )


def _evaluate_descriptor(
    descriptor: PrimitiveDescriptor,
    train_pairs: Sequence[Mapping[str, Any]],
    feature_labels: Sequence[str],
) -> PrimitiveDiscoveryHint:
    if descriptor.family == "object_bbox":
        if descriptor.primitive_name in {"crop_foreground_bbox", "crop_largest_object", "crop_selected_color_object"}:
            return _evaluate_crop_primitive(descriptor, train_pairs, feature_labels)
        if descriptor.primitive_name in {"translate_single_object", "preserve_shape_translate"}:
            return _evaluate_translation_primitive(descriptor, train_pairs, feature_labels)
    if descriptor.family == "shape_geometry":
        return _evaluate_geometry_primitive(descriptor, train_pairs, feature_labels)
    if descriptor.family == "color_role":
        return _evaluate_color_primitive(descriptor, train_pairs, feature_labels)
    if descriptor.family == "resize_tile":
        return _evaluate_resize_tile_primitive(descriptor, train_pairs, feature_labels)
    if descriptor.family == "count_quantity":
        return _evaluate_count_primitive(descriptor, train_pairs, feature_labels)
    return _make_hint(
        descriptor.primitive_name,
        descriptor.family,
        STATUS_UNCERTAIN_V1,
        0.2,
        "unsupported_family",
        inferred_parameters={},
        source_feature_labels=list(feature_labels),
        trace={"family": descriptor.family, "decision": "uncertain"},
    )


def _sorted_hints_for_result(hints: Sequence[PrimitiveDiscoveryHint]) -> list[PrimitiveDiscoveryHint]:
    return sorted(hints, key=lambda hint: (_STATUS_ORDER_V1.get(hint.status, 99), -float(hint.confidence), hint.primitive_name))


def discover_primitives_for_task(
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Any | None = None,
    registry: PrimitiveRegistry | Sequence[PrimitiveDescriptor] | None = None,
) -> PrimitiveDiscoveryResult:
    if not isinstance(train_pairs, Sequence) or not train_pairs:
        raise ValueError("empty_train_pairs")
    active_registry = registry
    if active_registry is None:
        active_registry = build_arc_primitive_registry_v1()
    if isinstance(active_registry, PrimitiveRegistry):
        descriptors = active_registry.list_primitives()
        registry_manifest = active_registry.export_manifest()
    else:
        descriptors = sorted(list(active_registry), key=lambda item: _safe_text(getattr(item, "primitive_name", item)))
        registry_manifest = {"primitive_count": len(descriptors)}

    test_input_supplied = test_input is not None
    if test_input is None:
        test_input = _pair_input(train_pairs[0])
    task_signature = build_arc_task_feature_signature_v1(train_pairs, test_input)
    feature_labels = _collect_feature_labels(task_signature)

    hints = [_evaluate_descriptor(descriptor, train_pairs, feature_labels) for descriptor in descriptors]
    sorted_hints = _sorted_hints_for_result(hints)
    accepted_hints = [hint for hint in sorted_hints if hint.status == STATUS_ACCEPTED_V1]
    rejected_hints = [hint for hint in sorted_hints if hint.status == STATUS_REJECTED_V1]
    uncertain_hints = [hint for hint in sorted_hints if hint.status == STATUS_UNCERTAIN_V1]

    return PrimitiveDiscoveryResult(
        accepted_hints=accepted_hints,
        rejected_hints=rejected_hints,
        uncertain_hints=uncertain_hints,
        primitive_count=len(sorted_hints),
        accepted_count=len(accepted_hints),
        rejected_count=len(rejected_hints),
        uncertain_count=len(uncertain_hints),
        trace={
            "schema_version": SCHEMA_VERSION_V1,
            "task_signature_schema": task_signature.get("schema_version", ""),
            "task_feature_labels": feature_labels,
            "registry_primitive_count": registry_manifest.get("primitive_count", len(descriptors)),
            "train_pair_count": len(train_pairs),
            "test_input_provided": test_input_supplied,
        },
    )


__all__ = [
    "PrimitiveDiscoveryHint",
    "PrimitiveDiscoveryResult",
    "discover_primitives_for_task",
]
