"""WESLR ARC primitive sequence to grid reconstruction V1.

Reconstructs a predicted output grid from a selected primitive sequence and input grid.
Used to materialize candidate outputs from the synthetic ARC-style solver for surface construction.

This module does not implement scoring, candidate_output_surface building, replay wiring,
final-answer emission, ARC-AGI-2 participation, provider/model/tool calls, or `.weslr` writes.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from typing import Any, Mapping, Sequence

from weslr.arc_style_grid_adapter_phase2 import (
    _background_value_from_grid,
    _cells_for_value,
    _dominant_non_background_value,
    _fill_region_from_outer_border,
    _largest_component_cells,
    _line_completion_grid,
    _object_count_to_pattern_grid,
    _reflect_bbox_grid,
    _reflect_object_grid_with_padding,
    _rotate_bbox_grid,
)

SCHEMA_VERSION_V1 = "ArcPrimitiveSequenceGridReconstructionV1"

# Supported primitive IDs that can be reconstructed into output grids
SUPPORTED_PRIMITIVE_IDS_V1 = {
    "copy",
    "recolor",
    "move",
    "fill",
    "fill_region",
    "extract_largest_object",
    "remove_background_noise",
    "line_completion",
    "object_count_to_pattern",
    "rotate_object_90",
    "reflect_object_horizontal_or_vertical",
    "complete_symmetry",
    "border_frame",
}


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int)):
        return str(value)
    return default if value == "" else str(value)


def _clone_grid(grid: Sequence[Sequence[Any]]) -> list[list[Any]]:
    return [list(row) for row in grid]


def _is_valid_grid(grid: Any) -> bool:
    """Check if grid is a valid 2D list of int/bool cells."""
    if not isinstance(grid, list) or not grid:
        return False
    if not all(isinstance(row, list) and row for row in grid):
        return False
    return all(isinstance(cell, (int, bool)) for row in grid for cell in row)


def apply_primitive_sequence_to_grid_v1(
    input_grid: Sequence[Sequence[Any]],
    primitive_sequence: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Apply a primitive sequence to an input grid and return the result.

    Args:
        input_grid: The input grid (2D list of int/bool cells)
        primitive_sequence: List of primitive dicts with primitive_id and parameters

    Returns:
        dict with keys:
        - reconstructed_grid: list[list[Any]] or None if failed
        - reconstruction_success: bool
        - failure_reason: str or None
        - provenance: str ("primitive_sequence_reconstruction")
        - schema_version: str
    """
    if not _is_valid_grid(input_grid):
        return {
            "reconstructed_grid": None,
            "reconstruction_success": False,
            "failure_reason": "invalid_input_grid",
            "provenance": "primitive_sequence_reconstruction",
            "schema_version": SCHEMA_VERSION_V1,
        }

    if not isinstance(primitive_sequence, list) or not primitive_sequence:
        return {
            "reconstructed_grid": None,
            "reconstruction_success": False,
            "failure_reason": "empty_primitive_sequence",
            "provenance": "primitive_sequence_reconstruction",
            "schema_version": SCHEMA_VERSION_V1,
        }

    grid = _clone_grid(input_grid)

    for step in primitive_sequence:
        if not isinstance(step, Mapping):
            return {
                "reconstructed_grid": None,
                "reconstruction_success": False,
                "failure_reason": "invalid_primitive_step",
                "provenance": "primitive_sequence_reconstruction",
                "schema_version": SCHEMA_VERSION_V1,
            }

        primitive_id = _safe_text(step.get("primitive_id"))
        if primitive_id not in SUPPORTED_PRIMITIVE_IDS_V1:
            return {
                "reconstructed_grid": None,
                "reconstruction_success": False,
                "failure_reason": f"unsupported_primitive:{primitive_id}",
                "provenance": "primitive_sequence_reconstruction",
                "schema_version": SCHEMA_VERSION_V1,
            }

        params = step.get("parameters", {}) if isinstance(step.get("parameters"), Mapping) else {}
        result_grid = _apply_single_primitive(grid, primitive_id, params)
        if result_grid is None:
            return {
                "reconstructed_grid": None,
                "reconstruction_success": False,
                "failure_reason": f"primitive_failed:{primitive_id}",
                "provenance": "primitive_sequence_reconstruction",
                "schema_version": SCHEMA_VERSION_V1,
            }
        grid = result_grid

    if not _is_valid_grid(grid):
        return {
            "reconstructed_grid": None,
            "reconstruction_success": False,
            "failure_reason": "output_grid_invalid",
            "provenance": "primitive_sequence_reconstruction",
            "schema_version": SCHEMA_VERSION_V1,
        }

    return {
        "reconstructed_grid": grid,
        "reconstruction_success": True,
        "failure_reason": None,
        "provenance": "primitive_sequence_reconstruction",
        "schema_version": SCHEMA_VERSION_V1,
    }


def _apply_single_primitive(
    grid: list[list[Any]],
    primitive_id: str,
    params: Mapping[str, Any],
) -> list[list[Any]] | None:
    """Apply a single primitive to the grid and return the result."""
    if primitive_id == "copy":
        return _clone_grid(grid)

    if primitive_id == "recolor":
        from_value = params.get("from_value")
        to_value = params.get("to_value")
        if from_value is None or to_value is None:
            return None
        out = _clone_grid(grid)
        for row_index, row in enumerate(out):
            for column_index, cell in enumerate(row):
                if cell == from_value:
                    out[row_index][column_index] = to_value
        return out

    if primitive_id == "move":
        direction = _safe_text(params.get("direction"))
        steps = int(params.get("steps", 1)) if str(params.get("steps", "1")).isdigit() else 1
        object_value = params.get("object_value")
        background_value = params.get("background_value")
        if background_value is None and grid:
            background_value = _background_value_from_grid(grid)
        if object_value is None and grid:
            values = [cell for row in grid for cell in row if cell != background_value]
            object_value = values[0] if values else None
        if object_value is None:
            return None
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
            return None
        delta_row, delta_col = delta_map[direction]
        out = [[background_value for _ in row] for row in grid]
        for row_index, row in enumerate(grid):
            for column_index, cell in enumerate(row):
                if cell == object_value:
                    new_row = row_index + delta_row
                    new_col = column_index + delta_col
                    if 0 <= new_row < len(grid) and 0 <= new_col < len(grid[new_row]):
                        out[new_row][new_col] = cell
        return out

    if primitive_id == "fill":
        fill_value = params.get("fill_value")
        fill_entire_grid = bool(params.get("fill_entire_grid", False))
        if fill_entire_grid:
            if fill_value is None:
                counts = Counter(cell for row in grid for cell in row)
                fill_value = counts.most_common(1)[0][0]
            return [[fill_value for _ in row] for row in grid]
        # fill_region fallback
        border_value = params.get("border_value")
        if border_value is None and grid:
            border_value = _background_value_from_grid(grid)
        if fill_value is None and grid:
            fill_value = _dominant_non_background_value(grid, border_value)
        return _fill_region_from_outer_border(grid, fill_value=fill_value, border_value=border_value)

    if primitive_id == "fill_region":
        fill_value = params.get("fill_value")
        border_value = params.get("border_value")
        if border_value is None and grid:
            border_value = _background_value_from_grid(grid)
        if fill_value is None and grid:
            fill_value = _dominant_non_background_value(grid, border_value)
        return _fill_region_from_outer_border(grid, fill_value=fill_value, border_value=border_value)

    if primitive_id == "extract_largest_object":
        background_value = params.get("background_value")
        if background_value is None and grid:
            background_value = _background_value_from_grid(grid)
        cells = _largest_component_cells(grid, background_value)
        if not cells:
            return None
        out = [[background_value for _ in row] for row in grid]
        for row_index, column_index in cells:
            out[row_index][column_index] = grid[row_index][column_index]
        return out

    if primitive_id == "remove_background_noise":
        background_value = params.get("background_value")
        if background_value is None and grid:
            background_value = _background_value_from_grid(grid)
        cells = _largest_component_cells(grid, background_value)
        if not cells:
            return None
        out = [[background_value for _ in row] for row in grid]
        for row_index, column_index in cells:
            out[row_index][column_index] = grid[row_index][column_index]
        return out

    if primitive_id == "line_completion":
        row_index = params.get("row_index")
        line_value = params.get("line_value")
        background_value = params.get("background_value")
        if background_value is None and grid:
            background_value = _background_value_from_grid(grid)
        span_start_column = params.get("span_start_column")
        span_end_column = params.get("span_end_column")
        return _line_completion_grid(grid, row_index=row_index, line_value=line_value, background_value=background_value, span_start_column=span_start_column, span_end_column=span_end_column)

    if primitive_id == "object_count_to_pattern":
        count = params.get("count")
        pattern_value = params.get("pattern_value")
        row_index = params.get("row_index")
        background_value = params.get("background_value")
        if background_value is None and grid:
            background_value = _background_value_from_grid(grid)
        return _object_count_to_pattern_grid(grid, count=count, pattern_value=pattern_value, row_index=row_index, background_value=background_value)

    if primitive_id == "rotate_object_90":
        background_value = params.get("background_value")
        if background_value is None and grid:
            background_value = _background_value_from_grid(grid)
        object_value = params.get("object_value")
        if object_value is None and grid:
            object_value = _dominant_non_background_value(grid, background_value)
        cells = _cells_for_value(grid, object_value) if object_value is not None else []
        if not cells:
            return None
        return _rotate_bbox_grid(grid, cells=cells, background_value=background_value)

    if primitive_id == "reflect_object_horizontal_or_vertical":
        background_value = params.get("background_value")
        if background_value is None and grid:
            background_value = _background_value_from_grid(grid)
        object_value = params.get("object_value")
        if object_value is None and grid:
            object_value = _dominant_non_background_value(grid, background_value)
        axis = _safe_text(params.get("axis", "horizontal"))
        if object_value is None:
            return None
        return _reflect_object_grid_with_padding(grid, object_value=object_value, background_value=background_value, axis=axis)

    if primitive_id == "complete_symmetry":
        axes = params.get("axes")
        if not isinstance(axes, list):
            axes = ["horizontal", "vertical"]
        background_value = params.get("background_value")
        if background_value is None and grid:
            counts = Counter(cell for row in grid for cell in row)
            background_value = counts.most_common(1)[0][0]
        out = _clone_grid(grid)
        height = len(grid)
        width = len(grid[0]) if grid else 0
        for row_index, row in enumerate(grid):
            for column_index, cell in enumerate(row):
                if cell == background_value:
                    continue
                targets = [(row_index, column_index)]
                if "horizontal" in axes:
                    targets.append((height - 1 - row_index, column_index))
                if "vertical" in axes:
                    targets.append((row_index, width - 1 - column_index))
                if "horizontal" in axes and "vertical" in axes:
                    targets.append((height - 1 - row_index, width - 1 - column_index))
                for target_row, target_col in targets:
                    out[target_row][target_col] = cell
        return out

    if primitive_id == "border_frame":
        frame_value = params.get("frame_value")
        fill_entire_grid = bool(params.get("fill_entire_grid", False))
        thickness = int(params.get("thickness", 1)) if str(params.get("thickness", "1")).isdigit() else 1
        if frame_value is None and grid:
            counts = Counter(cell for row in grid for cell in row)
            frame_value = counts.most_common(1)[0][0]
        if fill_entire_grid:
            return [[frame_value for _ in row] for row in grid]
        out = _clone_grid(grid)
        height = len(grid)
        width = len(grid[0]) if grid else 0
        for row_index in range(height):
            for column_index in range(width):
                if row_index < thickness or row_index >= height - thickness or column_index < thickness or column_index >= width - thickness:
                    out[row_index][column_index] = frame_value
        return out

    return None


def to_arc_primitive_sequence_grid_reconstruction_json_safe_v1(value: Any) -> Any:
    """Ensure value is JSON-safe for primitive reconstruction results."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(k): to_arc_primitive_sequence_grid_reconstruction_json_safe_v1(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_arc_primitive_sequence_grid_reconstruction_json_safe_v1(item) for item in value]
    return str(value)


def validate_reconstructed_grid_v1(reconstruction_result: Any) -> dict[str, Any]:
    """Validate a reconstruction result dict."""
    validation = {"valid": False, "blocked_reason_labels": []}
    if not isinstance(reconstruction_result, Mapping):
        validation["blocked_reason_labels"].append("result_not_mapping")
        return validation
    if "reconstructed_grid" not in reconstruction_result:
        validation["blocked_reason_labels"].append("missing_reconstructed_grid")
    if "reconstruction_success" not in reconstruction_result:
        validation["blocked_reason_labels"].append("missing_reconstruction_success")
    if "failure_reason" not in reconstruction_result:
        validation["blocked_reason_labels"].append("missing_failure_reason")
    if "provenance" not in reconstruction_result:
        validation["blocked_reason_labels"].append("missing_provenance")
    if validation["blocked_reason_labels"]:
        return validation
    if reconstruction_result.get("reconstruction_success") is True:
        if not _is_valid_grid(reconstruction_result.get("reconstructed_grid")):
            validation["blocked_reason_labels"].append("reconstructed_grid_invalid")
    if not validation["blocked_reason_labels"]:
        validation["valid"] = True
    return validation


__all__ = [
    "SCHEMA_VERSION_V1",
    "SUPPORTED_PRIMITIVE_IDS_V1",
    "apply_primitive_sequence_to_grid_v1",
    "to_arc_primitive_sequence_grid_reconstruction_json_safe_v1",
    "validate_reconstructed_grid_v1",
]