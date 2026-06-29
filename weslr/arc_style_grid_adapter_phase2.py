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
    "fill_region",
    "erase_background",
    "complete_symmetry",
    "extract_object",
    "extract_largest_object",
    "remove_background_noise",
    "line_completion",
    "object_count_to_pattern",
    "construct_count_pattern",
    "crop_to_non_background_bbox",
    "place_object_on_new_canvas",
    "preserve_input_canvas",
    "rotate_object_canvas",
    "rotate_object_90",
    "reflect_object_horizontal_or_vertical",
    "combine_objects",
    "resize_scale",
    "border_frame",
)

SUPPORTED_EXECUTABLE_PRIMITIVE_IDS_V1 = (
    "copy",
    "move",
    "recolor",
    "fill",
    "fill_region",
    "complete_symmetry",
    "border_frame",
    "extract_largest_object",
    "remove_background_noise",
    "line_completion",
    "object_count_to_pattern",
    "construct_count_pattern",
    "crop_to_non_background_bbox",
    "place_object_on_new_canvas",
    "preserve_input_canvas",
    "rotate_object_canvas",
    "rotate_object_90",
    "reflect_object_horizontal_or_vertical",
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


def _reflect_object_grid_with_padding(grid: list[list[Any]], *, object_value: Any, background_value: Any | None, axis: str) -> list[list[Any]]:
    """Reflect object in grid with padding detection for synthetic ARC tasks.

    This handles the case where the shape has empty padding cells that need to be
    included in the reflection to preserve the shape pattern.

    Args:
        grid: Input grid
        object_value: The value of the object to reflect
        background_value: Background value
        axis: "horizontal" or "vertical"

    Returns:
        Grid with object reflected
    """
    if not grid:
        return _copy_grid(grid)

    rows = len(grid)
    cols = len(grid[0]) if grid else 0
    out = [row[:] for row in grid]

    if axis == "horizontal":
        # Group by rows to detect padding
        row_data: list[tuple[int, int, int, int]] = []  # (row, min_c, max_c, count)
        for r in range(rows):
            row_cols = sorted(c for c in range(cols) if grid[r][c] == object_value)
            if row_cols:
                row_data.append((r, row_cols[0], row_cols[-1], len(row_cols)))

        if not row_data:
            return out

        min_r = min(r for r, _, _, _ in row_data)
        max_r = max(r for r, _, _, _ in row_data)
        min_c = min(c for r, c, _, _ in row_data)
        max_c = max(c for r, _, c, _ in row_data)

        # Check for left padding if sparse row exists (single object cell)
        for r, row_min, row_max, count in row_data:
            if count == 1 and row_min > 0:
                if grid[r][row_min - 1] == background_value:
                    min_c = row_min - 1
                    break

        # Extract subgrid, reflect, and place back
        subgrid = [row[min_c:max_c + 1] for row in grid[min_r:max_r + 1]]
        reflected = [list(reversed(row)) for row in subgrid]

        for r_idx, r in enumerate(range(min_r, max_r + 1)):
            for c_idx, c in enumerate(range(min_c, max_c + 1)):
                out[r][c] = reflected[r_idx][c_idx]

    else:  # vertical
        # Group by columns to detect padding
        col_data: list[tuple[int, int, int, int]] = []  # (col, min_r, max_r, count)
        for c in range(cols):
            col_rows = sorted(r for r in range(rows) if grid[r][c] == object_value)
            if col_rows:
                col_data.append((c, col_rows[0], col_rows[-1], len(col_rows)))

        if not col_data:
            return out

        min_c = min(c for c, _, _, _ in col_data)
        max_c = max(c for c, _, _, _ in col_data)
        min_r = min(r for c, r, _, _ in col_data)
        max_r = max(r for c, _, r, _ in col_data)

        # Check for top padding if sparse column exists (single object cell)
        for c, col_min, col_max, count in col_data:
            if count == 1 and col_min > 0:
                if grid[col_min - 1][c] == background_value:
                    min_r = col_min - 1
                    break

        # Extract subgrid, reflect, and place back
        subgrid = [row[min_c:max_c + 1] for row in grid[min_r:max_r + 1]]
        reflected = [list(row) for row in reversed(subgrid)]

        for r_idx, r in enumerate(range(min_r, max_r + 1)):
            for c_idx, c in enumerate(range(min_c, max_c + 1)):
                out[r][c] = reflected[r_idx][c_idx]

    return out


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
        "up_left": (-steps, -steps),
        "up_right": (-steps, steps),
        "down_left": (steps, -steps),
        "down_right": (steps, steps),
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


def _outer_border_coordinates(grid: Sequence[Sequence[Any]]) -> list[tuple[int, int]]:
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    cells = {(0, column_index) for column_index in range(width)}
    cells.update({(height - 1, column_index) for column_index in range(width)})
    cells.update({(row_index, 0) for row_index in range(height)})
    cells.update({(row_index, width - 1) for row_index in range(height)})
    return sorted(cells)


def _inner_area_coordinates(grid: Sequence[Sequence[Any]]) -> list[tuple[int, int]]:
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    return [(row_index, column_index) for row_index in range(1, height - 1) for column_index in range(1, width - 1)]


def _background_value_from_grid(grid: Sequence[Sequence[Any]]) -> Any | None:
    if not grid:
        return None
    counts = Counter(cell for row in grid for cell in row)
    return counts.most_common(1)[0][0] if counts else None


def _grid_has_only_valid_arc_cells(grid: Sequence[Sequence[Any]]) -> bool:
    if not grid or not isinstance(grid, Sequence):
        return False
    widths = {len(row) for row in grid if isinstance(row, Sequence)}
    if len(widths) != 1 or 0 in widths:
        return False
    for row in grid:
        if not isinstance(row, Sequence):
            return False
        for cell in row:
            if isinstance(cell, bool) or not isinstance(cell, int):
                return False
            if cell < 0 or cell > 9:
                return False
    return True


def _dominant_non_background_value(grid: Sequence[Sequence[Any]], background_value: Any | None) -> Any | None:
    counts = Counter(cell for row in grid for cell in row if cell != background_value)
    if counts:
        return counts.most_common(1)[0][0]
    counts = Counter(cell for row in grid for cell in row)
    return counts.most_common(1)[0][0] if counts else None


def _largest_component_cells(grid: Sequence[Sequence[Any]], background_value: Any | None) -> list[tuple[int, int]]:
    components = _connected_components(grid, background_value)
    if not components:
        return []
    return max(components, key=lambda component: (len(component), -_bounding_box_for_cells(component)[0], -_bounding_box_for_cells(component)[1], str(grid[component[0][0]][component[0][1]])))


def _rotate_bbox_grid(grid: list[list[Any]], *, cells: Sequence[tuple[int, int]], background_value: Any | None, clockwise: bool = True) -> list[list[Any]]:
    if not cells:
        return _copy_grid(grid)
    row_start, column_start, row_end, column_end = _bounding_box_for_cells(cells)
    subgrid = [row[column_start : column_end + 1] for row in grid[row_start : row_end + 1]]
    if clockwise:
        rotated = [list(reversed(col)) for col in zip(*subgrid)]
    else:
        rotated = [list(col) for col in zip(*reversed(subgrid))]
    out = _copy_grid(grid)
    for row_index in range(row_start, row_end + 1):
        for column_index in range(column_start, column_end + 1):
            out[row_index][column_index] = background_value
    for row_offset, row in enumerate(rotated):
        for column_offset, cell in enumerate(row):
            target_row = row_start + row_offset
            target_column = column_start + column_offset
            if 0 <= target_row < len(out) and 0 <= target_column < len(out[target_row]):
                out[target_row][target_column] = cell
    return out


def _rotate_subgrid(subgrid: Sequence[Sequence[Any]], angle: int) -> list[list[Any]]:
    normalized = int(angle) % 360
    rotated = [list(row) for row in subgrid]
    if normalized == 90:
        return [list(reversed(column)) for column in zip(*rotated)]
    if normalized == 180:
        return [list(reversed(row)) for row in reversed(rotated)]
    if normalized == 270:
        return [list(column) for column in zip(*reversed(rotated))]
    return [list(row) for row in rotated]


def _rotated_canvas_coordinate(row: int, column: int, *, height: int, width: int, angle: int) -> tuple[int, int]:
    normalized = int(angle) % 360
    if normalized == 90:
        return column, height - 1 - row
    if normalized == 180:
        return height - 1 - row, width - 1 - column
    if normalized == 270:
        return width - 1 - column, row
    return row, column


def _rotate_object_canvas_grid(
    grid: list[list[Any]],
    *,
    angle: Any,
    background_value: Any | None,
    object_value: Any | None = None,
    canvas_policy: str = "preserve_input_canvas",
    anchor_policy: str = "same_anchor",
    canvas_height: Any | None = None,
    canvas_width: Any | None = None,
    anchor_row: Any | None = None,
    anchor_column: Any | None = None,
) -> tuple[list[list[Any]], str | None]:
    if not _grid_has_only_valid_arc_cells(grid):
        return _copy_grid(grid), "invalid_grid"
    try:
        normalized_angle = int(angle)
    except (TypeError, ValueError):
        return _copy_grid(grid), "invalid_angle"
    if normalized_angle not in {90, 180, 270}:
        return _copy_grid(grid), "invalid_angle"
    background = background_value
    if background is None:
        background = _background_value_from_grid(grid)
    if isinstance(background, bool) or not isinstance(background, int) or background < 0 or background > 9:
        return _copy_grid(grid), "invalid_background"
    value = object_value
    if value is None:
        value = _dominant_non_background_value(grid, background)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 9:
        return _copy_grid(grid), "invalid_object_value"
    cells = _cells_for_value(grid, value)
    if not cells:
        return _copy_grid(grid), "missing_object_cells"
    row_start, column_start, row_end, column_end = _bounding_box_for_cells(cells)
    subgrid = [row[column_start : column_end + 1] for row in grid[row_start : row_end + 1]]
    rotated = _rotate_subgrid(subgrid, normalized_angle)

    input_height = len(grid)
    input_width = len(grid[0]) if grid else 0
    if canvas_policy == "rotate_input_canvas":
        target_height = input_width if normalized_angle in {90, 270} else input_height
        target_width = input_height if normalized_angle in {90, 270} else input_width
    else:
        if canvas_height is not None and canvas_width is not None:
            try:
                target_height = int(canvas_height)
                target_width = int(canvas_width)
            except (TypeError, ValueError):
                return _copy_grid(grid), "invalid_canvas"
        else:
            target_height = input_height
            target_width = input_width

    if target_height <= 0 or target_width <= 0 or target_height > 30 or target_width > 30:
        return _copy_grid(grid), "invalid_canvas"

    if anchor_policy == "rotate_with_input_canvas":
        rotated_cells = [_rotated_canvas_coordinate(row, column, height=input_height, width=input_width, angle=normalized_angle) for row, column in cells]
        target_anchor_row = min(row for row, _ in rotated_cells)
        target_anchor_column = min(column for _, column in rotated_cells)
    elif anchor_policy == "explicit_anchor":
        try:
            target_anchor_row = int(anchor_row)
            target_anchor_column = int(anchor_column)
        except (TypeError, ValueError):
            return _copy_grid(grid), "invalid_anchor"
    else:
        target_anchor_row = row_start
        target_anchor_column = column_start

    if target_anchor_row < 0 or target_anchor_column < 0:
        return _copy_grid(grid), "invalid_anchor"
    rotated_height = len(rotated)
    rotated_width = len(rotated[0]) if rotated else 0
    if rotated_height == 0 or rotated_width == 0:
        return _copy_grid(grid), "invalid_rotation"
    if target_anchor_row + rotated_height > target_height or target_anchor_column + rotated_width > target_width:
        return _copy_grid(grid), "placement_overflow"

    out = [[background for _ in range(target_width)] for _ in range(target_height)]
    for row_offset, row in enumerate(rotated):
        for column_offset, cell in enumerate(row):
            out[target_anchor_row + row_offset][target_anchor_column + column_offset] = cell
    return out, None


def _reflect_bbox_grid(grid: list[list[Any]], *, cells: Sequence[tuple[int, int]], background_value: Any | None, axis: str) -> list[list[Any]]:
    if not cells:
        return _copy_grid(grid)
    row_start, column_start, row_end, column_end = _bounding_box_for_cells(cells)
    subgrid = [row[column_start : column_end + 1] for row in grid[row_start : row_end + 1]]
    if axis == "horizontal":
        reflected = [list(reversed(row)) for row in subgrid]
    else:
        reflected = [list(row) for row in reversed(subgrid)]
    out = _copy_grid(grid)
    for row_index in range(row_start, row_end + 1):
        for column_index in range(column_start, column_end + 1):
            out[row_index][column_index] = background_value
    for row_offset, row in enumerate(reflected):
        for column_offset, cell in enumerate(row):
            target_row = row_start + row_offset
            target_column = column_start + column_offset
            if 0 <= target_row < len(out) and 0 <= target_column < len(out[target_row]):
                out[target_row][target_column] = cell
    return out


def _fill_region_from_outer_border(grid: list[list[Any]], *, fill_value: Any | None = None, border_value: Any | None = None) -> list[list[Any]]:
    if not grid or not grid[0]:
        return _copy_grid(grid)
    out = _copy_grid(grid)
    if border_value is None:
        border_values = Counter(grid[row][column] for row, column in _outer_border_coordinates(grid))
        border_value = border_values.most_common(1)[0][0] if border_values else _background_value_from_grid(grid)
    if fill_value is None:
        fill_value = _dominant_non_background_value(grid, border_value)
    for row_index, column_index in _inner_area_coordinates(grid):
        out[row_index][column_index] = fill_value
    return out


def _line_completion_grid(grid: list[list[Any]], *, row_index: int | None = None, line_value: Any | None = None, background_value: Any | None = None, span_start_column: int | None = None, span_end_column: int | None = None) -> list[list[Any]]:
    if not grid or not grid[0]:
        return _copy_grid(grid)
    out = _copy_grid(grid)
    if background_value is None:
        background_value = _background_value_from_grid(grid)
    if row_index is None:
        row_index = max(range(len(grid)), key=lambda index: sum(1 for cell in grid[index] if cell != background_value))
    row = list(grid[row_index])
    non_background_columns = [column_index for column_index, cell in enumerate(row) if cell != background_value]
    if line_value is None:
        line_value = _dominant_non_background_value([row], background_value)
    if line_value is None:
        return out
    if non_background_columns:
        inferred_start_column = min(non_background_columns)
        inferred_end_column = max(non_background_columns)
    else:
        inferred_start_column = 0
        inferred_end_column = len(out[row_index]) - 1
    if span_start_column is None:
        span_start_column = inferred_start_column
    if span_end_column is None:
        span_end_column = inferred_end_column
    start_column = max(0, min(len(out[row_index]) - 1, int(span_start_column)))
    end_column = max(start_column, min(len(out[row_index]) - 1, int(span_end_column)))
    for column_index in range(start_column, end_column + 1):
        out[row_index][column_index] = line_value
    return out


def _object_count_to_pattern_grid(grid: list[list[Any]], *, count: int | None = None, pattern_value: Any | None = None, row_index: int | None = None, background_value: Any | None = None) -> list[list[Any]]:
    if not grid or not grid[0]:
        return _copy_grid(grid)
    if background_value is None:
        background_value = _background_value_from_grid(grid)
    out = [[background_value for _ in row] for row in grid]
    if count is None:
        count = sum(1 for row in grid for cell in row if cell != background_value)
    if pattern_value is None:
        pattern_value = _dominant_non_background_value(grid, background_value)
    if row_index is None:
        row_index = len(grid) // 2
    for column_index in range(min(count, len(out[row_index]))):
        out[row_index][column_index] = pattern_value
    return out


def _grid_is_rectangular(grid: Sequence[Sequence[Any]]) -> bool:
    return bool(grid) and all(isinstance(row, Sequence) and not isinstance(row, (str, bytes, bytearray)) and len(row) == len(grid[0]) for row in grid)


def _grid_cells_are_safe(grid: Sequence[Sequence[Any]]) -> bool:
    for row in grid:
        for cell in row:
            if isinstance(cell, bool) or not isinstance(cell, int) or not 0 <= cell <= 9:
                return False
    return True


def _safe_input_grid(grid: Sequence[Sequence[Any]]) -> bool:
    return _grid_is_rectangular(grid) and _grid_cells_are_safe(grid)


def _construct_count_pattern_grid(grid: list[list[Any]], *, count: int | None = None, pattern_value: Any | None = None, background_value: Any | None = None, row_index: int | None = None) -> list[list[Any]]:
    if not _safe_input_grid(grid):
        return _copy_grid(grid)
    if background_value is None:
        background_value = _background_value_from_grid(grid)
    if count is None:
        distinct_non_background_values = {cell for row in grid for cell in row if cell != background_value}
        count = len(distinct_non_background_values)
        if count == 0:
            components = _connected_components(grid, background_value)
            count = len(components)
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        return _copy_grid(grid)
    if pattern_value is None:
        pattern_value = _dominant_non_background_value(grid, background_value)
    if pattern_value is None:
        return _copy_grid(grid)
    height = 1 if row_index is None else max(1, int(row_index) + 1)
    width = count
    if width > 25 or height > 25:
        return _copy_grid(grid)
    out = [[background_value for _ in range(width)] for _ in range(height)]
    placement_row = 0 if row_index is None else min(max(0, int(row_index)), height - 1)
    for column_index in range(width):
        out[placement_row][column_index] = pattern_value
    return out


def _crop_to_non_background_bbox_grid(grid: list[list[Any]], *, background_value: Any | None = None) -> list[list[Any]]:
    if not _safe_input_grid(grid):
        return _copy_grid(grid)
    background = background_value if background_value is not None else _background_value_from_grid(grid)
    if background is None:
        return _copy_grid(grid)
    cells = [(row_index, column_index) for row_index, row in enumerate(grid) for column_index, cell in enumerate(row) if cell != background]
    if not cells:
        return _copy_grid(grid)
    row_start, column_start, row_end, column_end = _bounding_box_for_cells(cells)
    if row_start > row_end or column_start > column_end:
        return _copy_grid(grid)
    return [list(row[column_start : column_end + 1]) for row in grid[row_start : row_end + 1]]


def _place_object_on_new_canvas(grid: list[list[Any]], *, canvas_height: int | None = None, canvas_width: int | None = None, background_value: Any | None = None, anchor_row: int | None = None, anchor_column: int | None = None, object_value: Any | None = None) -> list[list[Any]]:
    if not _safe_input_grid(grid):
        return _copy_grid(grid)
    background = background_value if background_value is not None else _background_value_from_grid(grid)
    if background is None:
        return _copy_grid(grid)
    values = [cell for row in grid for cell in row if cell != background]
    if object_value is None:
        distinct_values = {cell for cell in values}
        if len(distinct_values) != 1:
            return _copy_grid(grid)
        object_value = next(iter(distinct_values))
    cells = [(row_index, column_index) for row_index, row in enumerate(grid) for column_index, cell in enumerate(row) if cell == object_value]
    if not cells:
        return _copy_grid(grid)
    row_start, column_start, row_end, column_end = _bounding_box_for_cells(cells)
    object_height = row_end - row_start + 1
    object_width = column_end - column_start + 1
    height = int(canvas_height) if isinstance(canvas_height, int) and not isinstance(canvas_height, bool) and canvas_height > 0 else len(grid)
    width = int(canvas_width) if isinstance(canvas_width, int) and not isinstance(canvas_width, bool) and canvas_width > 0 else len(grid[0])
    if height > 25 or width > 25:
        return _copy_grid(grid)
    anchor_r = int(anchor_row) if isinstance(anchor_row, int) and not isinstance(anchor_row, bool) else 0
    anchor_c = int(anchor_column) if isinstance(anchor_column, int) and not isinstance(anchor_column, bool) else 0
    if anchor_r < 0 or anchor_c < 0 or anchor_r + object_height > height or anchor_c + object_width > width:
        return _copy_grid(grid)
    out = [[background for _ in range(width)] for _ in range(height)]
    for row_index, column_index in cells:
        target_row = anchor_r + (row_index - row_start)
        target_column = anchor_c + (column_index - column_start)
        out[target_row][target_column] = grid[row_index][column_index]
    return out


def _preserve_input_canvas_grid(grid: list[list[Any]], *, background_value: Any | None = None) -> list[list[Any]]:
    if not _safe_input_grid(grid):
        return _copy_grid(grid)
    if background_value is not None and background_value != _background_value_from_grid(grid):
        return _copy_grid(grid)
    return _copy_grid(grid)


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
    if primitive_id == "fill_region":
        fill_value = params.get("fill_value")
        if fill_value is None:
            fill_value = _dominant_non_background_value(grid, params.get("border_value", background_value))
        return _fill_region_from_outer_border(
            grid,
            fill_value=fill_value,
            border_value=params.get("border_value", background_value),
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
    if primitive_id == "extract_largest_object":
        background = params.get("background_value", background_value)
        cells = _largest_component_cells(grid, background)
        if not cells:
            trace["unsupported_reason"] = "missing_largest_component"
            return _copy_grid(grid), trace
        out = [[background for _ in row] for row in grid]
        for row_index, column_index in cells:
            out[row_index][column_index] = grid[row_index][column_index]
        return out, trace
    if primitive_id == "remove_background_noise":
        background = params.get("background_value", background_value)
        cells = _largest_component_cells(grid, background)
        if not cells:
            trace["unsupported_reason"] = "missing_largest_component"
            return _copy_grid(grid), trace
        out = [[background for _ in row] for row in grid]
        for row_index, column_index in cells:
            out[row_index][column_index] = grid[row_index][column_index]
        return out, trace
    if primitive_id == "line_completion":
        return _line_completion_grid(
            grid,
            row_index=params.get("row_index"),
            line_value=params.get("line_value"),
            background_value=params.get("background_value", background_value),
            span_start_column=params.get("span_start_column"),
            span_end_column=params.get("span_end_column"),
        ), trace
    if primitive_id == "object_count_to_pattern":
        return _object_count_to_pattern_grid(
            grid,
            count=int(params["count"]) if "count" in params and str(params.get("count", "")).isdigit() else params.get("count"),
            pattern_value=params.get("pattern_value"),
            row_index=int(params["row_index"]) if "row_index" in params and str(params.get("row_index", "")).isdigit() else params.get("row_index"),
            background_value=params.get("background_value", background_value),
        ), trace
    if primitive_id == "construct_count_pattern":
        return _construct_count_pattern_grid(
            grid,
            count=int(params["count"]) if "count" in params and str(params.get("count", "")).isdigit() else params.get("count"),
            pattern_value=params.get("pattern_value"),
            background_value=params.get("background_value", background_value),
            row_index=int(params["row_index"]) if "row_index" in params and str(params.get("row_index", "")).isdigit() else params.get("row_index"),
        ), trace
    if primitive_id == "crop_to_non_background_bbox":
        return _crop_to_non_background_bbox_grid(
            grid,
            background_value=params.get("background_value", background_value),
        ), trace
    if primitive_id == "place_object_on_new_canvas":
        return _place_object_on_new_canvas(
            grid,
            canvas_height=params.get("canvas_height"),
            canvas_width=params.get("canvas_width"),
            background_value=params.get("background_value", background_value),
            anchor_row=params.get("anchor_row"),
            anchor_column=params.get("anchor_column"),
            object_value=params.get("object_value"),
        ), trace
    if primitive_id == "preserve_input_canvas":
        return _preserve_input_canvas_grid(grid, background_value=params.get("background_value", background_value)), trace
    if primitive_id == "rotate_object_canvas":
        rotated_grid, unsupported_reason = _rotate_object_canvas_grid(
            grid,
            angle=params.get("angle"),
            background_value=params.get("background_value", background_value),
            object_value=params.get("object_value"),
            canvas_policy=_safe_text(params.get("canvas_policy"), "preserve_input_canvas"),
            anchor_policy=_safe_text(params.get("anchor_policy"), "same_anchor"),
            canvas_height=params.get("canvas_height"),
            canvas_width=params.get("canvas_width"),
            anchor_row=params.get("anchor_row"),
            anchor_column=params.get("anchor_column"),
        )
        if unsupported_reason:
            trace["unsupported_reason"] = unsupported_reason
        return rotated_grid, trace
    if primitive_id == "rotate_object_90":
        background = params.get("background_value", background_value)
        object_value = params.get("object_value")
        if object_value is None:
            object_value = _dominant_non_background_value(grid, background)
        cells = _cells_for_value(grid, object_value) if object_value is not None else []
        if not cells:
            trace["unsupported_reason"] = "missing_object_cells"
            return _copy_grid(grid), trace
        return _rotate_bbox_grid(grid, cells=cells, background_value=background, clockwise=True), trace
    if primitive_id == "reflect_object_horizontal_or_vertical":
        background = params.get("background_value", background_value)
        object_value = params.get("object_value")
        if object_value is None:
            object_value = _dominant_non_background_value(grid, background)
        if object_value is None:
            trace["unsupported_reason"] = "missing_object_value"
            return _copy_grid(grid), trace
        axis = _safe_text(params.get("axis"), "horizontal")
        # Use padding-aware reflection for synthetic tasks
        return _reflect_object_grid_with_padding(grid, object_value=object_value, background_value=background, axis=axis if axis in {"horizontal", "vertical"} else "horizontal"), trace
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
    if primitive_id in {"complete_symmetry", "border_frame", "fill_region", "extract_largest_object", "remove_background_noise", "line_completion", "object_count_to_pattern", "construct_count_pattern", "crop_to_non_background_bbox", "place_object_on_new_canvas", "preserve_input_canvas", "rotate_object_canvas", "rotate_object_90", "reflect_object_horizontal_or_vertical"}:
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
    if toy_task_type == "fill_region":
        outer_border = _outer_border_coordinates(input_grid)
        border_value = input_grid[0][0] if input_grid and input_grid[0] else background_value
        fill_value = _dominant_non_background_value(output_grid, border_value)
        candidate = build_arc_style_grid_candidate_result_v1(
            f"{task_packet.get('task_id')}:fill_region",
            candidate_type="fill_region_candidate",
            primitive_sequence=[{"primitive_id": "fill_region", "parameters": {"fill_value": fill_value, "border_value": border_value}}],
            train_fit_status="unknown",
            confidence_metadata={"confidence": "high"},
            calibration_metadata={"calibration": "phase2_toy"},
        )
        validation = validate_arc_style_train_pair_with_candidate_v1(pair, candidate)
        candidate["train_fit_status"] = "fit" if validation["exact_match"] else "mismatch"
        candidate["partial_fit_metadata"] = validation["partial_match_metadata"]
        candidate["unsupported_assumptions"] = [] if validation["exact_match"] else ["fill_region_candidate_inexact"]
        candidate["rejection_reasons"] = [] if validation["exact_match"] else [validation["mismatch_category"]]
        candidate["trace"] = {"validation": validation, "toy_task_type": toy_task_type, "outer_border_count": len(outer_border)}
        return candidate
    if toy_task_type == "extract_largest_object":
        candidate_background = background_value if background_value is not None else _background_value_from_grid(input_grid)
        largest_cells = _largest_component_cells(input_grid, candidate_background)
        if largest_cells:
            candidate = build_arc_style_grid_candidate_result_v1(
                f"{task_packet.get('task_id')}:extract_largest_object",
                candidate_type="extract_largest_object_candidate",
                primitive_sequence=[{"primitive_id": "extract_largest_object", "parameters": {"background_value": candidate_background}}],
                train_fit_status="unknown",
                confidence_metadata={"confidence": "high"},
                calibration_metadata={"calibration": "phase2_toy"},
            )
            validation = validate_arc_style_train_pair_with_candidate_v1(pair, candidate)
            candidate["train_fit_status"] = "fit" if validation["exact_match"] else "mismatch"
            candidate["partial_fit_metadata"] = validation["partial_match_metadata"]
            candidate["unsupported_assumptions"] = [] if validation["exact_match"] else ["extract_largest_object_candidate_inexact"]
            candidate["rejection_reasons"] = [] if validation["exact_match"] else [validation["mismatch_category"]]
            candidate["trace"] = {"validation": validation, "toy_task_type": toy_task_type}
            return candidate
    if toy_task_type == "remove_background_noise":
        candidate_background = background_value if background_value is not None else _background_value_from_grid(input_grid)
        candidate = build_arc_style_grid_candidate_result_v1(
            f"{task_packet.get('task_id')}:remove_background_noise",
            candidate_type="remove_background_noise_candidate",
            primitive_sequence=[{"primitive_id": "remove_background_noise", "parameters": {"background_value": candidate_background}}],
            train_fit_status="unknown",
            confidence_metadata={"confidence": "high"},
            calibration_metadata={"calibration": "phase2_toy"},
        )
        validation = validate_arc_style_train_pair_with_candidate_v1(pair, candidate)
        candidate["train_fit_status"] = "fit" if validation["exact_match"] else "mismatch"
        candidate["partial_fit_metadata"] = validation["partial_match_metadata"]
        candidate["unsupported_assumptions"] = [] if validation["exact_match"] else ["remove_background_noise_candidate_inexact"]
        candidate["rejection_reasons"] = [] if validation["exact_match"] else [validation["mismatch_category"]]
        candidate["trace"] = {"validation": validation, "toy_task_type": toy_task_type}
        return candidate
    if toy_task_type == "line_completion":
        candidate_background = background_value if background_value is not None else _background_value_from_grid(input_grid)
        line_row = max(range(len(input_grid)), key=lambda index: sum(1 for cell in input_grid[index] if cell != candidate_background)) if input_grid else 0
        line_value = _dominant_non_background_value(output_grid, candidate_background)
        output_row = next((row for row in output_grid if any(cell != candidate_background for cell in row)), [])
        span_start_column = min((column_index for column_index, cell in enumerate(output_row) if cell != candidate_background), default=0)
        span_end_column = max((column_index for column_index, cell in enumerate(output_row) if cell != candidate_background), default=max(0, len(output_row) - 1))
        candidate = build_arc_style_grid_candidate_result_v1(
            f"{task_packet.get('task_id')}:line_completion",
            candidate_type="line_completion_candidate",
            primitive_sequence=[{"primitive_id": "line_completion", "parameters": {"row_index": line_row, "line_value": line_value, "background_value": candidate_background, "span_start_column": span_start_column, "span_end_column": span_end_column}}],
            train_fit_status="unknown",
            confidence_metadata={"confidence": "high"},
            calibration_metadata={"calibration": "phase2_toy"},
        )
        validation = validate_arc_style_train_pair_with_candidate_v1(pair, candidate)
        candidate["train_fit_status"] = "fit" if validation["exact_match"] else "mismatch"
        candidate["partial_fit_metadata"] = validation["partial_match_metadata"]
        candidate["unsupported_assumptions"] = [] if validation["exact_match"] else ["line_completion_candidate_inexact"]
        candidate["rejection_reasons"] = [] if validation["exact_match"] else [validation["mismatch_category"]]
        candidate["trace"] = {"validation": validation, "toy_task_type": toy_task_type}
        return candidate
    if toy_task_type == "object_count_to_pattern":
        candidate_background = background_value if background_value is not None else _background_value_from_grid(input_grid)
        count = sum(1 for row in input_grid for cell in row if cell != candidate_background)
        pattern_value = _dominant_non_background_value(output_grid, candidate_background)
        candidate = build_arc_style_grid_candidate_result_v1(
            f"{task_packet.get('task_id')}:object_count_to_pattern",
            candidate_type="object_count_to_pattern_candidate",
            primitive_sequence=[{"primitive_id": "object_count_to_pattern", "parameters": {"count": count, "pattern_value": pattern_value, "row_index": len(input_grid) // 2 if input_grid else 0, "background_value": candidate_background}}],
            train_fit_status="unknown",
            confidence_metadata={"confidence": "high"},
            calibration_metadata={"calibration": "phase2_toy"},
        )
        validation = validate_arc_style_train_pair_with_candidate_v1(pair, candidate)
        candidate["train_fit_status"] = "fit" if validation["exact_match"] else "mismatch"
        candidate["partial_fit_metadata"] = validation["partial_match_metadata"]
        candidate["unsupported_assumptions"] = [] if validation["exact_match"] else ["object_count_to_pattern_candidate_inexact"]
        candidate["rejection_reasons"] = [] if validation["exact_match"] else [validation["mismatch_category"]]
        candidate["trace"] = {"validation": validation, "toy_task_type": toy_task_type}
        return candidate
    if toy_task_type == "rotate_object_90":
        candidate_background = background_value if background_value is not None else _background_value_from_grid(input_grid)
        object_value = _dominant_non_background_value(input_grid, candidate_background)
        candidate = build_arc_style_grid_candidate_result_v1(
            f"{task_packet.get('task_id')}:rotate_object_90",
            candidate_type="rotate_object_90_candidate",
            primitive_sequence=[{"primitive_id": "rotate_object_90", "parameters": {"object_value": object_value, "background_value": candidate_background}}],
            train_fit_status="unknown",
            confidence_metadata={"confidence": "high"},
            calibration_metadata={"calibration": "phase2_toy"},
        )
        validation = validate_arc_style_train_pair_with_candidate_v1(pair, candidate)
        candidate["train_fit_status"] = "fit" if validation["exact_match"] else "mismatch"
        candidate["partial_fit_metadata"] = validation["partial_match_metadata"]
        candidate["unsupported_assumptions"] = [] if validation["exact_match"] else ["rotate_object_90_candidate_inexact"]
        candidate["rejection_reasons"] = [] if validation["exact_match"] else [validation["mismatch_category"]]
        candidate["trace"] = {"validation": validation, "toy_task_type": toy_task_type}
        return candidate
    if toy_task_type == "reflect_object_horizontal_or_vertical":
        candidate_background = background_value if background_value is not None else _background_value_from_grid(input_grid)
        object_value = _dominant_non_background_value(input_grid, candidate_background)
        horizontal_candidate = _reflect_bbox_grid(_copy_grid(input_grid), cells=_cells_for_value(input_grid, object_value), background_value=candidate_background, axis="horizontal") if object_value is not None else _copy_grid(input_grid)
        vertical_candidate = _reflect_bbox_grid(_copy_grid(input_grid), cells=_cells_for_value(input_grid, object_value), background_value=candidate_background, axis="vertical") if object_value is not None else _copy_grid(input_grid)
        axis = "horizontal" if horizontal_candidate == output_grid else ("vertical" if vertical_candidate == output_grid else "horizontal")
        candidate = build_arc_style_grid_candidate_result_v1(
            f"{task_packet.get('task_id')}:reflect_object_horizontal_or_vertical",
            candidate_type="reflect_object_horizontal_or_vertical_candidate",
            primitive_sequence=[{"primitive_id": "reflect_object_horizontal_or_vertical", "parameters": {"axis": axis, "object_value": object_value, "background_value": candidate_background}}],
            train_fit_status="unknown",
            confidence_metadata={"confidence": "high"},
            calibration_metadata={"calibration": "phase2_toy"},
        )
        validation = validate_arc_style_train_pair_with_candidate_v1(pair, candidate)
        candidate["train_fit_status"] = "fit" if validation["exact_match"] else "mismatch"
        candidate["partial_fit_metadata"] = validation["partial_match_metadata"]
        candidate["unsupported_assumptions"] = [] if validation["exact_match"] else ["reflect_object_horizontal_or_vertical_candidate_inexact"]
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
            "primitive_id": "fill_region",
            "category": "fill_region",
            "description": "Fill the interior of a bordered synthetic region with a selected value.",
            "required_inputs": ["fill_value"],
            "allowed_assumptions": ["border_value_known", "interior_region_known"],
            "failure_mode_labels": ["transformation_mismatch", "cell_values_mismatch"],
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
            "primitive_id": "extract_largest_object",
            "category": "extract_largest_object",
            "description": "Extract the largest connected synthetic object from the grid.",
            "required_inputs": ["background_value"],
            "allowed_assumptions": ["largest_component_known"],
            "failure_mode_labels": ["transformation_mismatch", "cell_values_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": True,
        },
        {
            "primitive_id": "remove_background_noise",
            "category": "remove_background_noise",
            "description": "Remove background noise by preserving the dominant connected object.",
            "required_inputs": ["background_value"],
            "allowed_assumptions": ["dominant_component_known"],
            "failure_mode_labels": ["transformation_mismatch", "cell_values_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": True,
        },
        {
            "primitive_id": "line_completion",
            "category": "line_completion",
            "description": "Complete a broken line within a bounded synthetic grid.",
            "required_inputs": ["row_index", "line_value"],
            "allowed_assumptions": ["line_row_known"],
            "failure_mode_labels": ["transformation_mismatch", "cell_values_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": True,
        },
        {
            "primitive_id": "object_count_to_pattern",
            "category": "object_count_to_pattern",
            "description": "Convert a counted object signal into a bounded pattern row.",
            "required_inputs": ["count", "pattern_value"],
            "allowed_assumptions": ["count_signal_known"],
            "failure_mode_labels": ["transformation_mismatch", "cell_values_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": True,
        },
        {
            "primitive_id": "construct_count_pattern",
            "category": "construct_count_pattern",
            "description": "Construct a bounded count-encoded pattern on a new canvas using train-only shape and background proposals.",
            "required_inputs": ["count", "pattern_value"],
            "allowed_assumptions": ["count_signal_known", "train_only_shape_proposal", "train_only_background_proposal"],
            "failure_mode_labels": ["transformation_mismatch", "cell_values_mismatch", "output_formatting_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": True,
        },
        {
            "primitive_id": "crop_to_non_background_bbox",
            "category": "crop_to_non_background_bbox",
            "description": "Crop a grid to its tight non-background bounding box.",
            "required_inputs": ["background_value"],
            "allowed_assumptions": ["background_known_or_inferable"],
            "failure_mode_labels": ["output_formatting_mismatch", "dimensions_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": True,
        },
        {
            "primitive_id": "place_object_on_new_canvas",
            "category": "place_object_on_new_canvas",
            "description": "Place a single object or tight bbox onto a bounded new canvas with explicit background.",
            "required_inputs": ["canvas_height", "canvas_width", "background_value"],
            "allowed_assumptions": ["train_only_canvas_shape_proposal", "train_only_background_proposal"],
            "failure_mode_labels": ["dimensions_mismatch", "out_of_bounds", "unsupported_candidate"],
            "bounded_depth_allowed": True,
            "is_executable_now": True,
        },
        {
            "primitive_id": "preserve_input_canvas",
            "category": "preserve_input_canvas",
            "description": "Preserve the input canvas shape and background unchanged.",
            "required_inputs": [],
            "allowed_assumptions": ["canvas_shape_known"],
            "failure_mode_labels": ["cell_values_mismatch", "dimensions_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": True,
        },
        {
            "primitive_id": "rotate_object_canvas",
            "category": "rotate_object_canvas",
            "description": "Rotate a detected object bbox with bounded canvas and anchor policies inferred from train-only evidence.",
            "required_inputs": ["angle"],
            "allowed_assumptions": ["single_object_known", "bounded_canvas_policy", "bounded_anchor_policy", "train_only_parameter_proposal"],
            "failure_mode_labels": ["dimensions_mismatch", "out_of_bounds", "unsupported_candidate", "transformation_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": True,
        },
        {
            "primitive_id": "rotate_object_90",
            "category": "rotate_object_90",
            "description": "Rotate a single synthetic object by 90 degrees within its bounding box.",
            "required_inputs": ["object_value"],
            "allowed_assumptions": ["single_object_known"],
            "failure_mode_labels": ["transformation_mismatch", "cell_values_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": True,
        },
        {
            "primitive_id": "reflect_object_horizontal_or_vertical",
            "category": "reflect_object_horizontal_or_vertical",
            "description": "Reflect a single synthetic object horizontally or vertically within its bounding box.",
            "required_inputs": ["axis", "object_value"],
            "allowed_assumptions": ["axis_known", "single_object_known"],
            "failure_mode_labels": ["transformation_mismatch", "cell_values_mismatch"],
            "bounded_depth_allowed": True,
            "is_executable_now": True,
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
