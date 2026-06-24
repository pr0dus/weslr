"""WESLR ARC-style grid adapter Phase 2.

Phase 2 only: primitive registry metadata, deterministic object extraction
helpers, and a narrow train-pair validator over the internal synthetic toy
tasks from Phase 1.

This module does not implement candidate search, solver runtime, ARC dataset
ingestion, official benchmark scoring, or competition submission adapters.

No provider calls. No model calls. No payment calls. No ChatResponder wiring.
No website/runtime wiring. No `.weslr` writes.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import json
from statistics import mean
from typing import Any, Iterable, Mapping, Sequence

from weslr.arc_style_grid_schema_helpers import (
    GRID_FORMAT_ID_V1,
    TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
    TOY_TASK_TYPES_V1,
    build_arc_style_grid_metadata_v1,
    build_internal_arc_style_grid_toy_tasks_v1,
    build_arc_style_grid_candidate_result_v1,
    build_arc_style_grid_train_pair_v1,
    build_arc_style_grid_task_packet_v1,
    summarize_arc_style_grid_task_packet_v1,
    to_arc_style_grid_task_json_safe_v1,
    validate_arc_style_grid_candidate_result_v1,
    validate_arc_style_grid_task_packet_v1,
    validate_arc_style_grid_train_pair_v1,
)

SCHEMA_VERSION_V1 = "ArcStyleGridAdapterPhase2V1"
ADAPTER_TYPE_V1 = "arc_style_grid_adapter_phase2_v1"
PHASE_NUMBER_V1 = 2

PRIMITIVE_CATEGORIES_V1 = (
    "copy",
    "move",
    "rotate",
    "reflect",
    "crop",
    "extend",
    "recolor",
    "count",
    "fill",
    "erase_background",
    "complete_symmetry",
    "extract_object",
    "combine_objects",
    "resize_scale",
    "border_frame",
)

SUPPORTED_EXECUTABLE_PRIMITIVE_IDS_V1 = (
    "copy",
    "move",
    "recolor",
    "fill",
    "complete_symmetry",
    "border_frame",
)

DEFERRED_PRIMITIVE_IDS_V1 = tuple(pid for pid in PRIMITIVE_CATEGORIES_V1 if pid not in SUPPORTED_EXECUTABLE_PRIMITIVE_IDS_V1)

REQUIRED_PRIMITIVE_REGISTRY_FIELDS_V1 = (
    "primitive_id",
    "category",
    "description",
    "required_inputs",
    "allowed_assumptions",
    "failure_mode_labels",
    "bounded_depth_allowed",
    "is_executable_now",
)

REQUIRED_PHASE2_PACKET_FIELDS_V1 = (
    "adapter_type",
    "phase_number",
    "primitive_registry",
    "task_packets",
    "toy_task_count",
    "exact_match_count",
    "partial_match_count",
    "unsupported_count",
    "failure_notes",
    "trace",
)

REQUIRED_TASK_PACKET_FIELDS_V1 = (
    "task_id",
    "task_source",
    "toy_task_type",
    "phase1_validation",
    "grid_format",
    "task_trace",
    "object_extraction",
    "train_pair_validations",
    "validation_summary",
    "failure_notes",
    "trace",
)

REQUIRED_OBJECT_CANDIDATE_FIELDS_V1 = (
    "object_id",
    "object_type",
    "cells",
    "value",
    "bounding_box",
    "size",
    "centroid_or_anchor",
    "confidence_metadata",
    "trace",
)

REQUIRED_TRAIN_PAIR_VALIDATION_FIELDS_V1 = (
    "pair_id",
    "candidate_id",
    "exact_match",
    "partial_match_metadata",
    "mismatch_category",
    "failure_localization",
    "unsupported_candidate",
    "trace",
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
    value = deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    return _safe_text(value)


def to_arc_style_phase2_adapter_json_safe_v1(value: Any) -> Any:
    safe = _json_safe(value)
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def _grid_from_payload(payload: Any) -> list[list[Any]]:
    if isinstance(payload, Mapping) and "cell_values" in payload:
        payload = payload.get("cell_values")
    if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes, bytearray)):
        return []
    grid: list[list[Any]] = []
    for row in payload:
        if isinstance(row, (list, tuple)):
            grid.append(list(row))
    return grid


def _grid_dimensions(grid: Sequence[Sequence[Any]]) -> tuple[int, int]:
    if not grid:
        return 0, 0
    return len(grid[0]), len(grid)


def _in_bounds(grid: Sequence[Sequence[Any]], row: int, column: int) -> bool:
    return 0 <= row < len(grid) and (len(grid[row]) == 0 or 0 <= column < len(grid[row]))


def _neighbors(row: int, column: int) -> list[tuple[int, int]]:
    return [(row - 1, column), (row + 1, column), (row, column - 1), (row, column + 1)]


def _background_value_from_metadata(metadata: Mapping[str, Any]) -> Any:
    return metadata.get("background_color")


def _non_background_value(grid: Sequence[Sequence[Any]], background_value: Any) -> Any:
    counts = Counter(cell for row in grid for cell in row if cell != background_value)
    if counts:
        return counts.most_common(1)[0][0]
    counts = Counter(cell for row in grid for cell in row)
    return counts.most_common(1)[0][0] if counts else None


def _cells_for_value(grid: Sequence[Sequence[Any]], value: Any) -> list[tuple[int, int]]:
    cells: list[tuple[int, int]] = []
    for row_index, row in enumerate(grid):
        for column_index, cell in enumerate(row):
            if cell == value:
                cells.append((row_index, column_index))
    return cells


def _bounding_box_for_cells(cells: Sequence[tuple[int, int]]) -> list[int]:
    if not cells:
        return [0, 0, 0, 0]
    rows = [row for row, _ in cells]
    columns = [column for _, column in cells]
    return [min(rows), min(columns), max(rows), max(columns)]


def _centroid_for_cells(cells: Sequence[tuple[int, int]]) -> dict[str, float]:
    if not cells:
        return {"row": 0.0, "column": 0.0}
    return {"row": round(mean(row for row, _ in cells), 3), "column": round(mean(column for _, column in cells), 3)}


def _cells_to_list(cells: Sequence[tuple[int, int]]) -> list[list[int]]:
    return [[row, column] for row, column in cells]


def _object_candidate(
    object_id: str,
    object_type: str,
    cells: Sequence[tuple[int, int]],
    value: Any,
    *,
    confidence: str = "medium",
    reason: str = "candidate_based_hint",
    extra_trace: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    trace = {
        "schema_version": SCHEMA_VERSION_V1,
        "reason": reason,
        "candidate_based": True,
    }
    if isinstance(extra_trace, Mapping):
        trace.update(extra_trace)
    return {
        "object_id": _safe_text(object_id),
        "object_type": _safe_text(object_type),
        "cells": _cells_to_list(cells),
        "value": value,
        "bounding_box": _bounding_box_for_cells(cells),
        "size": len(cells),
        "centroid_or_anchor": _centroid_for_cells(cells),
        "confidence_metadata": {"confidence": confidence, "reason": reason},
        "trace": trace,
    }


def _connected_components(grid: Sequence[Sequence[Any]], background_value: Any | None) -> list[list[tuple[int, int]]]:
    visited: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row_index, row in enumerate(grid):
        for column_index, cell in enumerate(row):
            if (row_index, column_index) in visited:
                continue
            if background_value is not None and cell == background_value:
                visited.add((row_index, column_index))
                continue
            stack = [(row_index, column_index)]
            component: list[tuple[int, int]] = []
            while stack:
                current_row, current_column = stack.pop()
                if (current_row, current_column) in visited:
                    continue
                if not _in_bounds(grid, current_row, current_column):
                    continue
                if grid[current_row][current_column] != cell:
                    continue
                visited.add((current_row, current_column))
                component.append((current_row, current_column))
                for next_row, next_column in _neighbors(current_row, current_column):
                    if _in_bounds(grid, next_row, next_column) and (next_row, next_column) not in visited:
                        stack.append((next_row, next_column))
            if component:
                components.append(sorted(component))
    components.sort(key=lambda comp: (_bounding_box_for_cells(comp)[0], _bounding_box_for_cells(comp)[1], len(comp), str(grid[comp[0][0]][comp[0][1]])))
    return components


def _color_groups(grid: Sequence[Sequence[Any]]) -> list[dict[str, Any]]:
    groups: dict[Any, list[tuple[int, int]]] = defaultdict(list)
    for row_index, row in enumerate(grid):
        for column_index, cell in enumerate(row):
            groups[cell].append((row_index, column_index))
    outputs: list[dict[str, Any]] = []
    for index, (value, cells) in enumerate(sorted(groups.items(), key=lambda item: str(item[0]))):
        outputs.append(
            _object_candidate(
                f"color_group:{index}:{value}",
                "color_group",
                cells,
                value,
                confidence="high" if len(cells) > 1 else "medium",
                reason="same_value_group",
                extra_trace={"group_value": value, "group_size": len(cells)},
            )
        )
    return outputs


def _symmetry_hints(grid: Sequence[Sequence[Any]], background_value: Any | None) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    height = len(grid)
    width = len(grid[0]) if grid else 0
    if not grid or not width:
        return hints
    if all(row == list(reversed(row)) for row in grid):
        cells = [(row_index, column_index) for row_index, row in enumerate(grid) for column_index, _ in enumerate(row)]
        hints.append(
            _object_candidate(
                "symmetry:horizontal",
                "symmetry_hint",
                cells,
                background_value,
                confidence="low",
                reason="row_palindrome_pattern",
                extra_trace={"axis": "vertical", "symmetry_type": "horizontal_mirror_hint"},
            )
        )
    if grid == list(reversed(grid)):
        cells = [(row_index, column_index) for row_index, row in enumerate(grid) for column_index, _ in enumerate(row)]
        hints.append(
            _object_candidate(
                "symmetry:vertical",
                "symmetry_hint",
                cells,
                background_value,
                confidence="low",
                reason="column_palindrome_pattern",
                extra_trace={"axis": "horizontal", "symmetry_type": "vertical_mirror_hint"},
            )
        )
    return hints


def _line_hints(grid: Sequence[Sequence[Any]], background_value: Any | None) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    for row_index, row in enumerate(grid):
        if row and len(set(row)) == 1 and (background_value is None or row[0] != background_value):
            cells = [(row_index, column_index) for column_index in range(len(row))]
            hints.append(
                _object_candidate(
                    f"row_line:{row_index}",
                    "row_line_hint",
                    cells,
                    row[0],
                    confidence="medium",
                    reason="uniform_row_hint",
                    extra_trace={"row_index": row_index},
                )
            )
    width = len(grid[0]) if grid else 0
    for column_index in range(width):
        column = [row[column_index] for row in grid if len(row) > column_index]
        if column and len(set(column)) == 1 and (background_value is None or column[0] != background_value):
            cells = [(row_index, column_index) for row_index, row in enumerate(grid) if len(row) > column_index]
            hints.append(
                _object_candidate(
                    f"column_line:{column_index}",
                    "column_line_hint",
                    cells,
                    column[0],
                    confidence="medium",
                    reason="uniform_column_hint",
                    extra_trace={"column_index": column_index},
                )
            )
    return hints


def _border_frame_hints(grid: Sequence[Sequence[Any]], background_value: Any | None) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    if not grid or not grid[0]:
        return hints
    top = list(grid[0])
    bottom = list(grid[-1])
    left = [row[0] for row in grid if row]
    right = [row[-1] for row in grid if row]
    border_cells = [(0, column_index) for column_index in range(len(top))] + [(len(grid) - 1, column_index) for column_index in range(len(bottom))]
    border_cells += [(row_index, 0) for row_index, row in enumerate(grid) if row] + [(row_index, len(row) - 1) for row_index, row in enumerate(grid) if row]
    border_counts = Counter([grid[row][column] for row, column in border_cells if len(grid[row]) > column])
    if border_counts:
        value, count = border_counts.most_common(1)[0]
        border_total = len(border_cells)
        if count >= max(1, border_total // 2) and (background_value is None or value != background_value):
            hints.append(
                _object_candidate(
                    "border_frame:outer",
                    "border_frame_hint",
                    sorted(set(border_cells)),
                    value,
                    confidence="medium",
                    reason="dominant_border_value",
                    extra_trace={"border_count": count, "border_total": border_total},
                )
            )
    if len(grid) >= 3 and len(grid[0]) >= 3:
        center_row = len(grid) // 2
        center_column = len(grid[0]) // 2
        center_value = grid[center_row][center_column]
        if background_value is not None and center_value != background_value:
            hints.append(
                _object_candidate(
                    "border_frame:center",
                    "border_frame_hint",
                    [(center_row, center_column)],
                    center_value,
                    confidence="low",
                    reason="non_background_center_signal",
                    extra_trace={"center_row": center_row, "center_column": center_column},
                )
            )
    return hints


def extract_arc_style_object_candidates_v1(grid_or_metadata: Any, *, task_id: str | None = None) -> dict[str, Any]:
    grid = _grid_from_payload(grid_or_metadata)
    metadata = build_arc_style_grid_metadata_v1(grid)
    background_value = _background_value_from_metadata(metadata)
    components = _connected_components(grid, background_value)
    object_candidates = [
        _object_candidate(
            f"component:{index}",
            "connected_component",
            component,
            grid[component[0][0]][component[0][1]],
            confidence="high" if len(component) > 1 else "medium",
            reason="same_value_connected_component",
            extra_trace={"component_index": index, "component_size": len(component)},
        )
        for index, component in enumerate(components)
    ]
    if background_value is not None:
        background_cells = _cells_for_value(grid, background_value)
        if background_cells:
            object_candidates.append(
                _object_candidate(
                    "background:0",
                    "background_candidate",
                    background_cells,
                    background_value,
                    confidence="high",
                    reason="most_common_cell_background",
                    extra_trace={"background_value": background_value},
                )
            )
    color_group_candidates = _color_groups(grid)
    symmetry_hints = _symmetry_hints(grid, background_value)
    line_hints = _line_hints(grid, background_value)
    border_frame_hints = _border_frame_hints(grid, background_value)

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "task_id": _safe_text(task_id),
        "grid_metadata": metadata,
        "object_candidates": object_candidates,
        "color_group_candidates": color_group_candidates,
        "symmetry_hints": symmetry_hints,
        "line_hints": line_hints,
        "border_frame_hints": border_frame_hints,
        "trace": {
            "connected_component_count": len(object_candidates),
            "color_group_count": len(color_group_candidates),
            "symmetry_hint_count": len(symmetry_hints),
            "line_hint_count": len(line_hints),
            "border_frame_hint_count": len(border_frame_hints),
            "background_value": background_value,
            "task_id": _safe_text(task_id),
        },
    }


def _parse_primitive_step(step: Any) -> dict[str, Any]:
    if isinstance(step, str):
        return {"primitive_id": step, "parameters": {}}
    if isinstance(step, Mapping):
        primitive_id = _safe_text(step.get("primitive_id") or step.get("category"))
        parameters = step.get("parameters") if isinstance(step.get("parameters"), Mapping) else {
            key: value
            for key, value in step.items()
            if key not in {"primitive_id", "category", "description", "required_inputs"}
        }
        return {"primitive_id": primitive_id, "parameters": dict(parameters)}
    return {"primitive_id": "", "parameters": {}}


def _copy_grid(grid: list[list[Any]]) -> list[list[Any]]:
    return deepcopy(grid)


def _recolor_grid(grid: list[list[Any]], *, from_value: Any, to_value: Any) -> list[list[Any]]:
    out = _copy_grid(grid)
    for row_index, row in enumerate(out):
        for column_index, cell in enumerate(row):
            if cell == from_value:
                out[row_index][column_index] = to_value
    return out


def _move_single_object(grid: list[list[Any]], *, direction: str, steps: int = 1, object_value: Any | None = None, background_value: Any | None = None) -> list[list[Any]]:
    if not grid or not grid[0]:
        return _copy_grid(grid)
    background = background_value
    if background is None:
        background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    value = object_value
    if value is None:
        value = _non_background_value(grid, background)
    cells = _cells_for_value(grid, value)
    if not cells:
        return _copy_grid(grid)
    delta_map = {
        "up": (-steps, 0),
        "down": (steps, 0),
        "left": (0, -steps),
        "right": (0, steps),
    }
    if direction not in delta_map:
        return _copy_grid(grid)
    delta_row, delta_column = delta_map[direction]
    out = [[background for _ in row] for row in grid]
    for row_index, column_index in cells:
        new_row = row_index + delta_row
        new_column = column_index + delta_column
        if 0 <= new_row < len(grid) and 0 <= new_column < len(grid[new_row]):
            out[new_row][new_column] = grid[row_index][column_index]
    return out


def _complete_symmetry(grid: list[list[Any]], *, axes: Sequence[str] | None = None, background_value: Any | None = None) -> list[list[Any]]:
    if not grid or not grid[0]:
        return _copy_grid(grid)
    axes = tuple(axes or ("horizontal", "vertical"))
    background = background_value
    if background is None:
        background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    out = _copy_grid(grid)
    height = len(grid)
    width = len(grid[0])
    for row_index, row in enumerate(grid):
        for column_index, cell in enumerate(row):
            if cell == background:
                continue
            targets = [(row_index, column_index)]
            if "horizontal" in axes:
                targets.append((height - 1 - row_index, column_index))
            if "vertical" in axes:
                targets.append((row_index, width - 1 - column_index))
            if "horizontal" in axes and "vertical" in axes:
                targets.append((height - 1 - row_index, width - 1 - column_index))
            for target_row, target_column in targets:
                if 0 <= target_row < height and 0 <= target_column < len(out[target_row]):
                    out[target_row][target_column] = cell
    return out


def _fill_border_or_frame(grid: list[list[Any]], *, frame_value: Any | None = None, fill_entire_grid: bool = False, thickness: int = 1) -> list[list[Any]]:
    if not grid or not grid[0]:
        return _copy_grid(grid)
    value = frame_value
    if value is None:
        counts = Counter(cell for row in grid for cell in row if cell is not None)
        value = counts.most_common(1)[0][0] if counts else 0
    out = _copy_grid(grid)
    if fill_entire_grid:
        return [[value for _ in row] for row in grid]
    height = len(grid)
    width = len(grid[0])
    for row_index in range(height):
        for column_index in range(width):
            if row_index < thickness or row_index >= height - thickness or column_index < thickness or column_index >= width - thickness:
                out[row_index][column_index] = value
    return out


def _apply_primitive_step(grid: list[list[Any]], step: Any, *, background_value: Any | None = None) -> tuple[list[list[Any]], dict[str, Any]]:
    parsed = _parse_primitive_step(step)
    primitive_id = parsed["primitive_id"]
    params = parsed["parameters"]
    trace = {"primitive_id": primitive_id, "parameters": _json_safe(params)}
    if primitive_id == "copy":
        return _copy_grid(grid), trace
    if primitive_id == "recolor":
        if "from_value" not in params or "to_value" not in params:
            trace["unsupported_reason"] = "missing_recolor_parameters"
            return _copy_grid(grid), trace
        return _recolor_grid(grid, from_value=params["from_value"], to_value=params["to_value"]), trace
    if primitive_id == "move":
        direction = _safe_text(params.get("direction"))
        steps = int(params.get("steps", 1) or 1)
        return _move_single_object(
            grid,
            direction=direction,
            steps=steps,
            object_value=params.get("object_value"),
            background_value=params.get("background_value", background_value),
        ), trace
    if primitive_id == "fill":
        if "fill_value" not in params:
            trace["unsupported_reason"] = "missing_fill_value"
            return _copy_grid(grid), trace
        if bool(params.get("fill_entire_grid", True)):
            return [[params["fill_value"] for _ in row] for row in grid], trace
        return _fill_border_or_frame(
            grid,
            frame_value=params["fill_value"],
            fill_entire_grid=False,
            thickness=int(params.get("thickness", 1) or 1),
        ), trace
    if primitive_id == "complete_symmetry":
        axes = params.get("axes") if isinstance(params.get("axes"), (list, tuple)) else None
        return _complete_symmetry(grid, axes=axes, background_value=params.get("background_value", background_value)), trace
    if primitive_id == "border_frame":
        return _fill_border_or_frame(
            grid,
            frame_value=params.get("frame_value"),
            fill_entire_grid=bool(params.get("fill_entire_grid", False)),
            thickness=int(params.get("thickness", 1) or 1),
        ), trace
    trace["unsupported_reason"] = "primitive_not_executable_now"
    return _copy_grid(grid), trace


def _compare_grids(expected: Sequence[Sequence[Any]], predicted: Sequence[Sequence[Any]]) -> dict[str, Any]:
    expected_grid = [list(row) for row in expected]
    predicted_grid = [list(row) for row in predicted]
    exact_match = expected_grid == predicted_grid
    mismatch_cells = []
    height = max(len(expected_grid), len(predicted_grid))
    width = max((len(row) for row in expected_grid), default=0)
    width = max(width, max((len(row) for row in predicted_grid), default=0))
    for row_index in range(height):
        for column_index in range(width):
            expected_value = expected_grid[row_index][column_index] if row_index < len(expected_grid) and column_index < len(expected_grid[row_index]) else None
            predicted_value = predicted_grid[row_index][column_index] if row_index < len(predicted_grid) and column_index < len(predicted_grid[row_index]) else None
            if expected_value != predicted_value:
                mismatch_cells.append({"row": row_index, "column": column_index, "expected": expected_value, "predicted": predicted_value})
    return {
        "exact_match": exact_match,
        "mismatch_cells": mismatch_cells,
        "dimensions_match": len(expected_grid) == len(predicted_grid) and all(len(row) == len(predicted_grid[index]) for index, row in enumerate(expected_grid) if index < len(predicted_grid)),
        "value_mismatch_count": len(mismatch_cells),
    }


def _failure_category_for_candidate(primitive_id: str, comparison: Mapping[str, Any], supported: bool) -> str:
    if not supported:
        return "unsupported_candidate"
    if comparison.get("exact_match"):
        return "exact_match"
    if not comparison.get("dimensions_match"):
        return "dimensions_mismatch"
    if primitive_id == "recolor":
        return "color_mapping_mismatch"
    if primitive_id == "move":
        return "object_movement_mismatch"
    if primitive_id in {"complete_symmetry", "border_frame"}:
        return "transformation_mismatch"
    return "cell_values_mismatch"


def validate_arc_style_train_pair_with_candidate_v1(train_pair: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
    pair_id = _safe_text(train_pair.get("pair_id")) if isinstance(train_pair, Mapping) else ""
    candidate_id = _safe_text(candidate.get("candidate_id")) if isinstance(candidate, Mapping) else ""
    result = {
        "pair_id": pair_id,
        "candidate_id": candidate_id,
        "exact_match": False,
        "partial_match_metadata": {},
        "mismatch_category": "unsupported_candidate",
        "failure_localization": {},
        "unsupported_candidate": True,
        "trace": {},
    }
    if not isinstance(train_pair, Mapping) or not isinstance(candidate, Mapping):
        result["trace"]["reason"] = "train_pair_or_candidate_not_mapping"
        return result
    train_validation = validate_arc_style_grid_train_pair_v1(train_pair)
    if not train_validation["valid"]:
        result["mismatch_category"] = "invalid_train_pair"
        result["failure_localization"] = {"train_pair_reasons": train_validation["blocked_reason_labels"]}
        result["trace"]["train_pair_validation"] = train_validation
        return result

    primitive_sequence = candidate.get("primitive_sequence", [])
    parsed_sequence = [_parse_primitive_step(step) for step in primitive_sequence] if isinstance(primitive_sequence, list) else []
    if not parsed_sequence:
        result["mismatch_category"] = "unsupported_candidate"
        result["failure_localization"] = {"reason": "empty_primitive_sequence"}
        result["trace"]["supported"] = False
        return result

    primitive_id = parsed_sequence[0]["primitive_id"]
    supported = primitive_id in SUPPORTED_EXECUTABLE_PRIMITIVE_IDS_V1
    result["unsupported_candidate"] = not supported
    input_grid = _grid_from_payload(train_pair.get("input_grid"))
    expected_output = _grid_from_payload(train_pair.get("output_grid"))
    predicted = _copy_grid(input_grid)
    step_traces = []
    background_value = train_pair.get("input_grid_metadata", {}).get("background_color") if isinstance(train_pair.get("input_grid_metadata"), Mapping) else None
    for step in primitive_sequence:
        predicted, step_trace = _apply_primitive_step(predicted, step, background_value=background_value)
        step_traces.append(step_trace)
    comparison = _compare_grids(expected_output, predicted)
    result["exact_match"] = bool(comparison["exact_match"] and supported)
    result["partial_match_metadata"] = {
        "comparison": comparison,
        "predicted_grid": predicted,
        "expected_grid": expected_output,
        "input_grid": input_grid,
    }
    result["mismatch_category"] = _failure_category_for_candidate(primitive_id, comparison, supported)
    result["failure_localization"] = {
        "dimensions": {
            "input": [len(input_grid), len(input_grid[0]) if input_grid else 0],
            "expected": [len(expected_output), len(expected_output[0]) if expected_output else 0],
            "predicted": [len(predicted), len(predicted[0]) if predicted else 0],
        },
        "mismatch_cells": comparison["mismatch_cells"][:10],
    }
    result["trace"] = {
        "primitive_sequence": _json_safe(primitive_sequence),
        "primitive_step_traces": step_traces,
        "supported": supported,
        "comparison": comparison,
    }
    if result["exact_match"]:
        result["mismatch_category"] = "exact_match"
        result["failure_localization"] = {"reason": "none"}
    return result


def _infer_candidate_for_toy_task(task_packet: Mapping[str, Any]) -> dict[str, Any]:
    toy_task_type = _safe_text(task_packet.get("trace", {}).get("toy_task_type") if isinstance(task_packet.get("trace"), Mapping) else "")
    train_pairs = task_packet.get("train_pairs", []) if isinstance(task_packet.get("train_pairs"), list) else []
    if not train_pairs:
        return build_arc_style_grid_candidate_result_v1(
            f"{task_packet.get('task_id', 'unknown')}:unsupported",
            candidate_type=f"{toy_task_type}_candidate",
            primitive_sequence=[],
            train_fit_status="unsupported",
            partial_fit_metadata={"reason": "no_train_pairs"},
            unsupported_assumptions=["no_train_pairs"],
            rejection_reasons=["no_train_pairs"],
            confidence_metadata={"confidence": "low"},
            calibration_metadata={"calibration": "unset"},
        )
    pair = train_pairs[0]
    input_grid = _grid_from_payload(pair.get("input_grid"))
    output_grid = _grid_from_payload(pair.get("output_grid"))
    input_meta = pair.get("input_grid_metadata", {}) if isinstance(pair.get("input_grid_metadata"), Mapping) else {}
    background_value = input_meta.get("background_color")
    if toy_task_type == "copy_grid":
        candidate = build_arc_style_grid_candidate_result_v1(
            f"{task_packet.get('task_id')}:copy",
            candidate_type="copy_candidate",
            primitive_sequence=[{"primitive_id": "copy", "parameters": {}}],
            train_fit_status="unknown",
            confidence_metadata={"confidence": "high"},
            calibration_metadata={"calibration": "phase2_toy"},
        )
        validation = validate_arc_style_train_pair_with_candidate_v1(pair, candidate)
        candidate["train_fit_status"] = "fit" if validation["exact_match"] else "mismatch"
        candidate["partial_fit_metadata"] = validation["partial_match_metadata"]
        candidate["unsupported_assumptions"] = [] if validation["exact_match"] else ["copy_candidate_inexact"]
        candidate["rejection_reasons"] = [] if validation["exact_match"] else [validation["mismatch_category"]]
        candidate["trace"] = {"validation": validation, "toy_task_type": toy_task_type}
        return candidate
    if toy_task_type == "recolor_symbol":
        diffs = []
        for row_index, row in enumerate(input_grid):
            for column_index, cell in enumerate(row):
                expected_value = output_grid[row_index][column_index] if row_index < len(output_grid) and column_index < len(output_grid[row_index]) else None
                if cell != expected_value:
                    diffs.append((cell, expected_value))
        if len(diffs) == 1:
            from_value, to_value = diffs[0]
            candidate = build_arc_style_grid_candidate_result_v1(
                f"{task_packet.get('task_id')}:recolor",
                candidate_type="recolor_candidate",
                primitive_sequence=[{"primitive_id": "recolor", "parameters": {"from_value": from_value, "to_value": to_value}}],
                train_fit_status="unknown",
                confidence_metadata={"confidence": "high"},
                calibration_metadata={"calibration": "phase2_toy"},
            )
            validation = validate_arc_style_train_pair_with_candidate_v1(pair, candidate)
            candidate["train_fit_status"] = "fit" if validation["exact_match"] else "mismatch"
            candidate["partial_fit_metadata"] = validation["partial_match_metadata"]
            candidate["unsupported_assumptions"] = [] if validation["exact_match"] else ["recolor_candidate_inexact"]
            candidate["rejection_reasons"] = [] if validation["exact_match"] else [validation["mismatch_category"]]
            candidate["trace"] = {"validation": validation, "toy_task_type": toy_task_type}
            return candidate
        return build_arc_style_grid_candidate_result_v1(
            f"{task_packet.get('task_id')}:recolor-unsupported",
            candidate_type="recolor_candidate",
            primitive_sequence=[{"primitive_id": "recolor", "parameters": {}}],
            train_fit_status="unsupported",
            partial_fit_metadata={"reason": "could_not_infer_recolor_map"},
            unsupported_assumptions=["could_not_infer_recolor_map"],
            rejection_reasons=["could_not_infer_recolor_map"],
            confidence_metadata={"confidence": "low"},
            calibration_metadata={"calibration": "phase2_toy"},
        )
    if toy_task_type == "move_single_object":
        input_background = background_value if background_value is not None else Counter(cell for row in input_grid for cell in row).most_common(1)[0][0]
        input_value = _non_background_value(input_grid, input_background)
        input_cells = _cells_for_value(input_grid, input_value)
        output_cells = _cells_for_value(output_grid, input_value)
        if len(input_cells) == len(output_cells) and input_cells and output_cells:
            delta_row = output_cells[0][0] - input_cells[0][0]
            delta_column = output_cells[0][1] - input_cells[0][1]
            direction = None
            if delta_row > 0 and delta_column == 0:
                direction = "down"
            elif delta_row < 0 and delta_column == 0:
                direction = "up"
            elif delta_column > 0 and delta_row == 0:
                direction = "right"
            elif delta_column < 0 and delta_row == 0:
                direction = "left"
            if direction is not None:
                candidate = build_arc_style_grid_candidate_result_v1(
                    f"{task_packet.get('task_id')}:move",
                    candidate_type="move_candidate",
                    primitive_sequence=[{"primitive_id": "move", "parameters": {"direction": direction, "steps": abs(delta_row or delta_column), "object_value": input_value, "background_value": input_background}}],
                    train_fit_status="unknown",
                    confidence_metadata={"confidence": "high"},
                    calibration_metadata={"calibration": "phase2_toy"},
                )
                validation = validate_arc_style_train_pair_with_candidate_v1(pair, candidate)
                candidate["train_fit_status"] = "fit" if validation["exact_match"] else "mismatch"
                candidate["partial_fit_metadata"] = validation["partial_match_metadata"]
                candidate["unsupported_assumptions"] = [] if validation["exact_match"] else ["move_candidate_inexact"]
                candidate["rejection_reasons"] = [] if validation["exact_match"] else [validation["mismatch_category"]]
                candidate["trace"] = {"validation": validation, "toy_task_type": toy_task_type}
                return candidate
        return build_arc_style_grid_candidate_result_v1(
            f"{task_packet.get('task_id')}:move-unsupported",
            candidate_type="move_candidate",
            primitive_sequence=[{"primitive_id": "move", "parameters": {}}],
            train_fit_status="unsupported",
            partial_fit_metadata={"reason": "could_not_infer_move_direction"},
            unsupported_assumptions=["could_not_infer_move_direction"],
            rejection_reasons=["could_not_infer_move_direction"],
            confidence_metadata={"confidence": "low"},
            calibration_metadata={"calibration": "phase2_toy"},
        )
    if toy_task_type == "complete_symmetry":
        candidate = build_arc_style_grid_candidate_result_v1(
            f"{task_packet.get('task_id')}:symmetry",
            candidate_type="symmetry_candidate",
            primitive_sequence=[{"primitive_id": "complete_symmetry", "parameters": {"axes": ["horizontal", "vertical"], "background_value": background_value}}],
            train_fit_status="unknown",
            confidence_metadata={"confidence": "medium"},
            calibration_metadata={"calibration": "phase2_toy"},
        )
        validation = validate_arc_style_train_pair_with_candidate_v1(pair, candidate)
        candidate["train_fit_status"] = "fit" if validation["exact_match"] else "mismatch"
        candidate["partial_fit_metadata"] = validation["partial_match_metadata"]
        candidate["unsupported_assumptions"] = [] if validation["exact_match"] else ["symmetry_candidate_inexact"]
        candidate["rejection_reasons"] = [] if validation["exact_match"] else [validation["mismatch_category"]]
        candidate["trace"] = {"validation": validation, "toy_task_type": toy_task_type}
        return candidate
    if toy_task_type == "border_frame_fill":
        center_row = len(input_grid) // 2 if input_grid else 0
        center_column = len(input_grid[0]) // 2 if input_grid and input_grid[0] else 0
        inferred_value = input_grid[center_row][center_column] if input_grid and input_grid[0] else background_value
        candidate = build_arc_style_grid_candidate_result_v1(
            f"{task_packet.get('task_id')}:border_frame",
            candidate_type="border_frame_candidate",
            primitive_sequence=[{"primitive_id": "border_frame", "parameters": {"frame_value": inferred_value, "fill_entire_grid": True}}],
            train_fit_status="unknown",
            confidence_metadata={"confidence": "medium"},
            calibration_metadata={"calibration": "phase2_toy"},
        )
        validation = validate_arc_style_train_pair_with_candidate_v1(pair, candidate)
        candidate["train_fit_status"] = "fit" if validation["exact_match"] else "mismatch"
        candidate["partial_fit_metadata"] = validation["partial_match_metadata"]
        candidate["unsupported_assumptions"] = [] if validation["exact_match"] else ["border_frame_candidate_inexact"]
        candidate["rejection_reasons"] = [] if validation["exact_match"] else [validation["mismatch_category"]]
        candidate["trace"] = {"validation": validation, "toy_task_type": toy_task_type}
        return candidate
    return build_arc_style_grid_candidate_result_v1(
        f"{task_packet.get('task_id')}:unsupported",
        candidate_type=f"{toy_task_type}_candidate",
        primitive_sequence=[],
        train_fit_status="unsupported",
        partial_fit_metadata={"reason": "toy_task_type_not_supported_now"},
        unsupported_assumptions=["toy_task_type_not_supported_now"],
        rejection_reasons=["toy_task_type_not_supported_now"],
        confidence_metadata={"confidence": "low"},
        calibration_metadata={"calibration": "phase2_toy"},
    )


def build_arc_style_primitive_registry_v1() -> list[dict[str, Any]]:
    registry = [
        {
            "primitive_id": "copy",
            "category": "copy",
            "description": "Copy the input grid unchanged.",
            "required_inputs": [],
            "allowed_assumptions": ["grid_shape_preserved"],
            "failure_mode_labels": ["dimensions_mismatch", "cell_values_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": True,
        },
        {
            "primitive_id": "move",
            "category": "move",
            "description": "Translate a single-object candidate by a bounded direction and step count.",
            "required_inputs": ["direction", "steps"],
            "allowed_assumptions": ["single_object", "background_known_or_inferable"],
            "failure_mode_labels": ["object_movement_mismatch", "out_of_bounds"],
            "bounded_depth_allowed": True,
            "is_executable_now": True,
        },
        {
            "primitive_id": "rotate",
            "category": "rotate",
            "description": "Rotate a candidate grid or object by a fixed angle.",
            "required_inputs": ["angle"],
            "allowed_assumptions": ["angle_is_discrete"],
            "failure_mode_labels": ["orientation_mismatch", "dimensions_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": False,
        },
        {
            "primitive_id": "reflect",
            "category": "reflect",
            "description": "Reflect a candidate grid or object across a selected axis.",
            "required_inputs": ["axis"],
            "allowed_assumptions": ["axis_is_known"],
            "failure_mode_labels": ["orientation_mismatch", "dimensions_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": False,
        },
        {
            "primitive_id": "crop",
            "category": "crop",
            "description": "Crop a rectangular region from a grid.",
            "required_inputs": ["bounding_box"],
            "allowed_assumptions": ["region_is_known"],
            "failure_mode_labels": ["output_formatting_mismatch", "dimensions_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": False,
        },
        {
            "primitive_id": "extend",
            "category": "extend",
            "description": "Extend a grid with bounded padding or repeated structure.",
            "required_inputs": ["padding"],
            "allowed_assumptions": ["padding_is_known"],
            "failure_mode_labels": ["dimensions_mismatch", "pattern_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": False,
        },
        {
            "primitive_id": "recolor",
            "category": "recolor",
            "description": "Replace one value with another over selected cells.",
            "required_inputs": ["from_value", "to_value"],
            "allowed_assumptions": ["value_mapping_known"],
            "failure_mode_labels": ["color_mapping_mismatch", "cell_values_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": True,
        },
        {
            "primitive_id": "count",
            "category": "count",
            "description": "Count values, components, or regions and emit metadata only.",
            "required_inputs": ["count_target"],
            "allowed_assumptions": ["count_target_is_known"],
            "failure_mode_labels": ["candidate_not_applicable", "metadata_only"],
            "bounded_depth_allowed": True,
            "is_executable_now": False,
        },
        {
            "primitive_id": "fill",
            "category": "fill",
            "description": "Fill a bounded region or entire grid with a selected value.",
            "required_inputs": ["fill_value"],
            "allowed_assumptions": ["fill_region_known"],
            "failure_mode_labels": ["output_formatting_mismatch", "cell_values_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": True,
        },
        {
            "primitive_id": "erase_background",
            "category": "erase_background",
            "description": "Remove or replace the background value as metadata only.",
            "required_inputs": ["background_value"],
            "allowed_assumptions": ["background_known"],
            "failure_mode_labels": ["background_mismatch", "metadata_only"],
            "bounded_depth_allowed": True,
            "is_executable_now": False,
        },
        {
            "primitive_id": "complete_symmetry",
            "category": "complete_symmetry",
            "description": "Complete a simple symmetry pattern by reflecting non-background cells.",
            "required_inputs": ["axes"],
            "allowed_assumptions": ["axes_known", "non_background_signal_known"],
            "failure_mode_labels": ["transformation_mismatch", "cell_values_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": True,
        },
        {
            "primitive_id": "extract_object",
            "category": "extract_object",
            "description": "Extract object candidates as metadata only; do not execute solver runtime.",
            "required_inputs": ["object_candidate"],
            "allowed_assumptions": ["object_candidate_known"],
            "failure_mode_labels": ["metadata_only", "unsupported_candidate"],
            "bounded_depth_allowed": True,
            "is_executable_now": False,
        },
        {
            "primitive_id": "combine_objects",
            "category": "combine_objects",
            "description": "Combine multiple object candidates into a bounded candidate output.",
            "required_inputs": ["object_candidates"],
            "allowed_assumptions": ["object_candidates_known"],
            "failure_mode_labels": ["unsupported_candidate", "transformation_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": False,
        },
        {
            "primitive_id": "resize_scale",
            "category": "resize_scale",
            "description": "Resize or scale a grid by a bounded factor.",
            "required_inputs": ["scale_factor"],
            "allowed_assumptions": ["scale_factor_known"],
            "failure_mode_labels": ["dimensions_mismatch", "unsupported_candidate"],
            "bounded_depth_allowed": True,
            "is_executable_now": False,
        },
        {
            "primitive_id": "border_frame",
            "category": "border_frame",
            "description": "Apply a border or frame operation, including bounded full-grid fill for internal toy tasks.",
            "required_inputs": ["frame_value"],
            "allowed_assumptions": ["frame_value_known"],
            "failure_mode_labels": ["cell_values_mismatch", "output_formatting_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": True,
        },
    ]
    return registry


def _build_phase2_task_trace(task_packet: Mapping[str, Any], object_extraction: Mapping[str, Any], validation_results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    trace = {
        "schema_version": SCHEMA_VERSION_V1,
        "adapter_type": ADAPTER_TYPE_V1,
        "task_id": _safe_text(task_packet.get("task_id")),
        "toy_task_type": _safe_text(task_packet.get("trace", {}).get("toy_task_type") if isinstance(task_packet.get("trace"), Mapping) else ""),
        "internal_synthetic_only": True,
        "no_arc_dataset_ingestion": True,
        "no_solver_runtime": True,
        "no_candidate_search": True,
        "no_object_extraction_implementation": False,
        "no_primitive_executor": False,
        "validation_count": len(validation_results),
        "object_candidate_count": len(object_extraction.get("object_candidates", [])),
        "color_group_candidate_count": len(object_extraction.get("color_group_candidates", [])),
        "symmetry_hint_count": len(object_extraction.get("symmetry_hints", [])),
        "line_hint_count": len(object_extraction.get("line_hints", [])),
        "border_frame_hint_count": len(object_extraction.get("border_frame_hints", [])),
    }
    return trace


def build_arc_style_train_pair_phase2_validation_v1(task_packet: Mapping[str, Any], train_pair: Mapping[str, Any]) -> dict[str, Any]:
    toy_task_type = _safe_text(task_packet.get("trace", {}).get("toy_task_type") if isinstance(task_packet.get("trace"), Mapping) else "")
    candidate = _infer_candidate_for_toy_task(task_packet)
    validation = validate_arc_style_train_pair_with_candidate_v1(train_pair, candidate)
    validation["toy_task_type"] = toy_task_type
    return validation


def build_arc_style_phase2_adapter_packet_v1(task_packets: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    tasks = list(task_packets) if task_packets is not None else build_internal_arc_style_grid_toy_tasks_v1()
    primitive_registry = build_arc_style_primitive_registry_v1()
    task_results: list[dict[str, Any]] = []
    exact_match_count = 0
    partial_match_count = 0
    unsupported_count = 0
    failure_notes: list[str] = []

    for task_packet in tasks:
        phase1_validation = validate_arc_style_grid_task_packet_v1(task_packet)
        task_trace = task_packet.get("trace", {}) if isinstance(task_packet.get("trace"), Mapping) else {}
        object_extraction = extract_arc_style_object_candidates_v1(task_packet.get("test_input"), task_id=task_packet.get("task_id"))
        train_pair_validations: list[dict[str, Any]] = []
        train_pairs = task_packet.get("train_pairs", []) if isinstance(task_packet.get("train_pairs"), list) else []
        for train_pair in train_pairs:
            validation = build_arc_style_train_pair_phase2_validation_v1(task_packet, train_pair)
            train_pair_validations.append(validation)
            if validation["exact_match"]:
                exact_match_count += 1
            elif validation["unsupported_candidate"]:
                unsupported_count += 1
            else:
                partial_match_count += 1
                if validation["mismatch_category"] not in failure_notes:
                    failure_notes.append(validation["mismatch_category"])
            if validation["unsupported_candidate"] and validation["mismatch_category"] not in failure_notes:
                failure_notes.append(validation["mismatch_category"])
        validation_summary = {
            "exact_match_count": sum(1 for item in train_pair_validations if item["exact_match"]),
            "unsupported_count": sum(1 for item in train_pair_validations if item["unsupported_candidate"]),
            "partial_match_count": sum(1 for item in train_pair_validations if not item["exact_match"] and not item["unsupported_candidate"]),
        }
        task_result = {
            "task_id": _safe_text(task_packet.get("task_id")),
            "task_source": _safe_text(task_packet.get("task_source")),
            "toy_task_type": _safe_text(task_trace.get("toy_task_type")),
            "phase1_validation": phase1_validation,
            "grid_format": _json_safe(task_packet.get("grid_format", {"format_id": GRID_FORMAT_ID_V1})),
            "task_trace": _json_safe(task_trace),
            "object_extraction": object_extraction,
            "train_pair_validations": train_pair_validations,
            "validation_summary": validation_summary,
            "failure_notes": list(dict.fromkeys(failure_notes)),
            "trace": _build_phase2_task_trace(task_packet, object_extraction, train_pair_validations),
        }
        task_results.append(task_result)

    packet = {
        "adapter_type": ADAPTER_TYPE_V1,
        "phase_number": PHASE_NUMBER_V1,
        "primitive_registry": primitive_registry,
        "task_packets": task_results,
        "toy_task_count": len(task_results),
        "exact_match_count": exact_match_count,
        "partial_match_count": partial_match_count,
        "unsupported_count": unsupported_count,
        "failure_notes": list(dict.fromkeys(failure_notes)),
        "trace": {
            "schema_version": SCHEMA_VERSION_V1,
            "toy_task_types": list(TOY_TASK_TYPES_V1),
            "internal_synthetic_only": True,
            "no_arc_dataset_ingestion": True,
            "no_solver_runtime": True,
            "no_candidate_search": True,
            "no_public_arc_sample_ingestion": True,
            "primitive_registry_count": len(primitive_registry),
        },
    }
    return packet


def validate_arc_style_phase2_adapter_packet_v1(packet: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "blocked_reason_labels": [],
        "toy_task_count": 0,
    }
    if not isinstance(packet, Mapping):
        result["blocked_reason_labels"].append("packet_not_mapping")
        return result
    missing = [field for field in REQUIRED_PHASE2_PACKET_FIELDS_V1 if field not in packet]
    if missing:
        result["blocked_reason_labels"].append("missing_required_fields")
        result["blocked_reason_labels"].extend(f"missing:{field}" for field in missing)
        return result
    if not isinstance(packet.get("primitive_registry"), list):
        result["blocked_reason_labels"].append("primitive_registry_not_list")
    else:
        for entry in packet.get("primitive_registry", []):
            if not isinstance(entry, Mapping):
                result["blocked_reason_labels"].append("primitive_registry_entry_not_mapping")
                continue
            for field in REQUIRED_PRIMITIVE_REGISTRY_FIELDS_V1:
                if field not in entry:
                    result["blocked_reason_labels"].append(f"primitive_missing:{field}")
            if entry.get("primitive_id") not in PRIMITIVE_CATEGORIES_V1:
                result["blocked_reason_labels"].append(f"unknown_primitive:{entry.get('primitive_id')}")
    if not isinstance(packet.get("task_packets"), list):
        result["blocked_reason_labels"].append("task_packets_not_list")
        task_packets = []
    else:
        task_packets = packet.get("task_packets", [])
    result["toy_task_count"] = len(task_packets)
    for task_packet in task_packets:
        if not isinstance(task_packet, Mapping):
            result["blocked_reason_labels"].append("task_packet_not_mapping")
            continue
        for field in REQUIRED_TASK_PACKET_FIELDS_V1:
            if field not in task_packet:
                result["blocked_reason_labels"].append(f"task_missing:{field}")
        if not isinstance(task_packet.get("object_extraction"), Mapping):
            result["blocked_reason_labels"].append("object_extraction_not_mapping")
        else:
            extraction = task_packet.get("object_extraction", {})
            for field in ("object_candidates", "color_group_candidates", "symmetry_hints", "line_hints", "border_frame_hints"):
                if field not in extraction or not isinstance(extraction.get(field), list):
                    result["blocked_reason_labels"].append(f"extraction_missing_or_not_list:{field}")
            for candidate in extraction.get("object_candidates", []):
                if not isinstance(candidate, Mapping):
                    result["blocked_reason_labels"].append("object_candidate_not_mapping")
                    continue
                for field in REQUIRED_OBJECT_CANDIDATE_FIELDS_V1:
                    if field not in candidate:
                        result["blocked_reason_labels"].append(f"object_candidate_missing:{field}")
        if not isinstance(task_packet.get("train_pair_validations"), list):
            result["blocked_reason_labels"].append("train_pair_validations_not_list")
        else:
            for validation in task_packet.get("train_pair_validations", []):
                if not isinstance(validation, Mapping):
                    result["blocked_reason_labels"].append("train_pair_validation_not_mapping")
                    continue
                for field in REQUIRED_TRAIN_PAIR_VALIDATION_FIELDS_V1:
                    if field not in validation:
                        result["blocked_reason_labels"].append(f"train_pair_validation_missing:{field}")
    if not isinstance(packet.get("trace"), Mapping):
        result["blocked_reason_labels"].append("trace_not_mapping")
    if not result["blocked_reason_labels"]:
        result["valid"] = True
    return result


def summarize_arc_style_phase2_adapter_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_arc_style_phase2_adapter_packet_v1(packet)
    if not isinstance(packet, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "toy_task_count": 0,
            "exact_match_count": 0,
            "unsupported_count": 0,
            "partial_match_count": 0,
            "executable_primitive_count": 0,
            "deferred_primitive_count": len(PRIMITIVE_CATEGORIES_V1),
            "toy_task_types": list(TOY_TASK_TYPES_V1),
            "blocked_reason_labels": validation["blocked_reason_labels"],
        }
    registry = packet.get("primitive_registry", []) if isinstance(packet.get("primitive_registry"), list) else []
    task_packets = packet.get("task_packets", []) if isinstance(packet.get("task_packets"), list) else []
    exact_match_count = 0
    unsupported_count = 0
    partial_match_count = 0
    for task_packet in task_packets:
        for validation_result in task_packet.get("train_pair_validations", []) if isinstance(task_packet, Mapping) else []:
            if validation_result.get("exact_match"):
                exact_match_count += 1
            elif validation_result.get("unsupported_candidate"):
                unsupported_count += 1
            else:
                partial_match_count += 1
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": validation["valid"],
        "toy_task_count": len(task_packets),
        "exact_match_count": exact_match_count,
        "unsupported_count": unsupported_count,
        "partial_match_count": partial_match_count,
        "executable_primitive_count": sum(1 for entry in registry if isinstance(entry, Mapping) and entry.get("is_executable_now") is True),
        "deferred_primitive_count": sum(1 for entry in registry if isinstance(entry, Mapping) and entry.get("is_executable_now") is False),
        "toy_task_types": list(TOY_TASK_TYPES_V1),
        "blocked_reason_labels": validation["blocked_reason_labels"],
    }


__all__ = [
    "SCHEMA_VERSION_V1",
    "ADAPTER_TYPE_V1",
    "PHASE_NUMBER_V1",
    "PRIMITIVE_CATEGORIES_V1",
    "SUPPORTED_EXECUTABLE_PRIMITIVE_IDS_V1",
    "DEFERRED_PRIMITIVE_IDS_V1",
    "build_arc_style_primitive_registry_v1",
    "extract_arc_style_object_candidates_v1",
    "validate_arc_style_train_pair_with_candidate_v1",
    "build_arc_style_train_pair_phase2_validation_v1",
    "build_arc_style_phase2_adapter_packet_v1",
    "validate_arc_style_phase2_adapter_packet_v1",
    "summarize_arc_style_phase2_adapter_packet_v1",
    "to_arc_style_phase2_adapter_json_safe_v1",
]
