"""WESLR ARC-style synthetic 2-step 40-task pilot runner V1.

Design-constrained diagnostic scaffold for a deterministic 40-task synthetic
2-step ARC-style pilot. This module is measurement-only and intentionally does
not modify solver inference logic, single-step runner behavior, candidate output
surfaces, replay/scoring/final-answer behavior, public ARC/Kaggle participation,
or `.weslr` state.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import json
from typing import Any, Mapping, Sequence

from weslr.arc_style_grid_generalization_stress import perturb_arc_style_task_metadata_v1
from weslr.arc_style_grid_schema_helpers import build_arc_style_grid_task_packet_v1, build_arc_style_grid_train_pair_v1
from weslr.arc_style_grid_solver_dry_run import run_arc_style_bounded_solver_dry_run_v1
from weslr.arc_style_synthetic_solver_suite import (
    DEFAULT_DENIED_AUTHORITY_V1,
    _build_packet_result,
    _normalize_leakage_flags,
    _safe_text,
    build_arc_style_synthetic_solver_failure_ledger_v1,
)

SCHEMA_VERSION_V1 = "ArcStyleSynthetic2StepPilotRunnerV1"
RUNNER_ID_V1 = "arc_style_synthetic_2_step_40_pilot_runner_v1"
RUNNER_ENTRY_POINT_V1 = "weslr.arc_style_synthetic_2_step_pilot_runner.run_arc_style_synthetic_2_step_40_pilot_diagnostic_v1"
TASK_SOURCE_INTERNAL_2_STEP_PILOT_V1 = "internal_synthetic_2_step_pilot_v1"
PILOT_TASK_COUNT_V1 = 40
TRAIN_PAIR_COUNT_V1 = 2
TEST_INPUT_COUNT_V1 = 1
MODE_ORDER_V1 = (
    "full_metadata",
    "toy_task_type_preserved_guardrail",
    "fully_stripped_lower_bound",
    "shuffled_renamed",
)
FAILURE_TAXONOMY_V1 = (
    "right_primitives_wrong_order",
    "first_step_correct_second_wrong",
    "first_step_wrong_second_correct",
    "one_primitive_missing",
    "shortcut_single_step_false_solution",
    "ambiguous_train_evidence",
    "generator_ambiguity",
    "parameter_inference_failure",
    "execution_failure",
)
EXPECTED_STATUS_KEYS_V1 = ("exact", "partial", "unsupported", "failed")


EASY_TASK_SPECS_V1 = (
    ("pilot_2_step_easy_01_remove_noise_then_extract_v1", "easy", ("remove_background_noise", "extract_largest_object"), "noise_extract"),
    ("pilot_2_step_easy_02_remove_noise_then_recolor_v1", "easy", ("remove_background_noise", "recolor_symbol"), "noise_recolor"),
    ("pilot_2_step_easy_03_extract_then_recolor_v1", "easy", ("extract_largest_object", "recolor_symbol"), "extract_recolor"),
    ("pilot_2_step_easy_04_move_then_border_v1", "easy", ("move_single_object", "border_frame"), "move_border"),
    ("pilot_2_step_easy_05_copy_then_recolor_v1", "easy", ("copy_grid", "recolor_symbol"), "copy_recolor"),
    ("pilot_2_step_easy_06_copy_then_border_v1", "easy", ("copy_grid", "border_frame"), "copy_border"),
    ("pilot_2_step_easy_07_fill_then_recolor_v1", "easy", ("fill_region", "recolor_symbol"), "fill_recolor"),
    ("pilot_2_step_easy_08_fill_then_line_v1", "easy", ("fill_region", "line_completion"), "fill_line"),
    ("pilot_2_step_easy_09_symmetry_then_recolor_v1", "easy", ("complete_symmetry", "recolor_symbol"), "symmetry_recolor"),
    ("pilot_2_step_easy_10_count_then_border_v1", "easy", ("object_count_to_pattern", "border_frame"), "count_border"),
    ("pilot_2_step_easy_11_line_then_recolor_v1", "easy", ("line_completion", "recolor_symbol"), "line_recolor"),
    ("pilot_2_step_easy_12_recolor_then_border_v1", "easy", ("recolor_symbol", "border_frame"), "recolor_border"),
    ("pilot_2_step_easy_13_extract_then_border_v1", "easy", ("extract_largest_object", "border_frame"), "extract_border"),
    ("pilot_2_step_easy_14_remove_noise_then_border_v1", "easy", ("remove_background_noise", "border_frame"), "noise_border"),
    ("pilot_2_step_easy_15_move_then_recolor_v1", "easy", ("move_single_object", "recolor_symbol"), "move_recolor"),
    ("pilot_2_step_easy_16_symmetry_then_border_v1", "easy", ("complete_symmetry", "border_frame"), "symmetry_border"),
    ("pilot_2_step_easy_17_copy_then_line_v1", "easy", ("copy_grid", "line_completion"), "copy_line"),
    ("pilot_2_step_easy_18_fill_then_border_v1", "easy", ("fill_region", "border_frame"), "fill_border"),
    ("pilot_2_step_easy_19_line_then_border_v1", "easy", ("line_completion", "border_frame"), "line_border"),
    ("pilot_2_step_easy_20_extract_then_symmetry_v1", "easy", ("extract_largest_object", "complete_symmetry"), "extract_symmetry"),
)

MEDIUM_TASK_SPECS_V1 = (
    ("pilot_2_step_medium_01_rotate_then_recolor_v1", "medium", ("rotate_object_90", "recolor_symbol"), "rotate_recolor"),
    ("pilot_2_step_medium_02_reflect_then_move_v1", "medium", ("reflect_object_horizontal_or_vertical", "move_single_object"), "reflect_move"),
    ("pilot_2_step_medium_03_rotate_then_reflect_v1", "medium", ("rotate_object_90", "reflect_object_horizontal_or_vertical"), "rotate_reflect"),
    ("pilot_2_step_medium_04_reflect_then_recolor_v1", "medium", ("reflect_object_horizontal_or_vertical", "recolor_symbol"), "reflect_recolor"),
    ("pilot_2_step_medium_05_remove_noise_then_count_v1", "medium", ("remove_background_noise", "object_count_to_pattern"), "noise_count"),
    ("pilot_2_step_medium_06_extract_then_count_v1", "medium", ("extract_largest_object", "object_count_to_pattern"), "extract_count"),
    ("pilot_2_step_medium_07_symmetry_then_line_v1", "medium", ("complete_symmetry", "line_completion"), "symmetry_line"),
    ("pilot_2_step_medium_08_move_then_symmetry_v1", "medium", ("move_single_object", "complete_symmetry"), "move_symmetry"),
    ("pilot_2_step_medium_09_fill_then_symmetry_v1", "medium", ("fill_region", "complete_symmetry"), "fill_symmetry"),
    ("pilot_2_step_medium_10_count_then_recolor_v1", "medium", ("object_count_to_pattern", "recolor_symbol"), "count_recolor"),
)

STRESS_TASK_SPECS_V1 = (
    ("pilot_2_step_stress_01_rotate_then_border_v1", "stress", ("rotate_object_90", "border_frame"), "rotate_border"),
    ("pilot_2_step_stress_02_reflect_then_border_v1", "stress", ("reflect_object_horizontal_or_vertical", "border_frame"), "reflect_border"),
    ("pilot_2_step_stress_03_rotate_then_move_v1", "stress", ("rotate_object_90", "move_single_object"), "rotate_move"),
    ("pilot_2_step_stress_04_reflect_then_symmetry_v1", "stress", ("reflect_object_horizontal_or_vertical", "complete_symmetry"), "reflect_symmetry"),
    ("pilot_2_step_stress_05_remove_noise_then_symmetry_v1", "stress", ("remove_background_noise", "complete_symmetry"), "noise_symmetry"),
    ("pilot_2_step_stress_06_extract_then_line_v1", "stress", ("extract_largest_object", "line_completion"), "extract_line"),
    ("pilot_2_step_stress_07_count_then_line_v1", "stress", ("object_count_to_pattern", "line_completion"), "count_line"),
    ("pilot_2_step_stress_08_fill_then_count_v1", "stress", ("fill_region", "object_count_to_pattern"), "fill_count"),
    ("pilot_2_step_stress_09_symmetry_then_count_v1", "stress", ("complete_symmetry", "object_count_to_pattern"), "symmetry_count"),
    ("pilot_2_step_stress_10_move_then_reflect_v1", "stress", ("move_single_object", "reflect_object_horizontal_or_vertical"), "move_reflect"),
)

TASK_SPECS_V1 = EASY_TASK_SPECS_V1 + MEDIUM_TASK_SPECS_V1 + STRESS_TASK_SPECS_V1


_SHORTCUT_PRIMITIVES_V1 = {"copy"}
SOLVER_PRIMITIVE_ID_ALIASES_V1 = {
    "copy_grid": "copy",
    "recolor_symbol": "recolor",
    "move_single_object": "move",
    "fill_region": "fill_region",
    "extract_largest_object": "extract_largest_object",
    "border_frame": "border_frame",
    "complete_symmetry": "complete_symmetry",
    "line_completion": "line_completion",
    "object_count_to_pattern": "object_count_to_pattern",
    "remove_background_noise": "remove_background_noise",
    "rotate_object_90": "rotate_object_90",
    "reflect_object_horizontal_or_vertical": "reflect_object_horizontal_or_vertical",
}


SCENE_PARAMETERS_BY_TYPE_V1: dict[str, dict[str, Any]] = {
    "noise_extract": {"rows": 6, "cols": 6, "large_color": 2, "noise_color": 8, "large_rect": (1, 1, 4, 4), "noise_cells": [(0, 0), (5, 5)]},
    "noise_recolor": {"rows": 6, "cols": 6, "source_color": 2, "target_color": 5, "large_rect": (1, 1, 4, 4), "noise_color": 8, "noise_cells": [(0, 5), (5, 0)]},
    "extract_recolor": {"rows": 6, "cols": 6, "large_color": 3, "target_color": 6, "small_color": 7, "large_rect": (1, 1, 4, 4), "small_cells": [(0, 0), (5, 5)]},
    "move_border": {"rows": 6, "cols": 6, "object_color": 3, "frame_color": 8, "direction": "right", "steps": 1, "shape": "domino_h"},
    "copy_recolor": {"rows": 6, "cols": 6, "source_color": 4, "target_color": 6, "shape": "l3"},
    "copy_border": {"rows": 6, "cols": 6, "object_color": 3, "frame_color": 8, "shape": "single"},
    "fill_recolor": {"rows": 6, "cols": 6, "border_color": 3, "fill_color": 4, "target_color": 7},
    "fill_line": {"rows": 6, "cols": 6, "border_color": 3, "fill_color": 4, "line_value": 4, "axis": "horizontal", "line_index": 2, "gap_index": 3},
    "symmetry_recolor": {"rows": 6, "cols": 6, "source_color": 2, "target_color": 5, "seed_cells": [(0, 1), (5, 4)]},
    "count_border": {"rows": 6, "cols": 6, "object_color": 2, "pattern_color": 7, "frame_color": 8, "count": 3, "row_index": 3},
    "line_recolor": {"rows": 6, "cols": 6, "line_value": 2, "target_color": 5, "axis": "horizontal", "line_index": 3, "gap_index": 2},
    "recolor_border": {"rows": 6, "cols": 6, "source_color": 2, "target_color": 6, "frame_color": 8, "shape": "plus_small"},
    "extract_border": {"rows": 6, "cols": 6, "large_color": 2, "small_color": 6, "frame_color": 8, "large_rect": (1, 1, 4, 4), "small_cells": [(0, 5), (5, 0)]},
    "noise_border": {"rows": 6, "cols": 6, "object_color": 2, "noise_color": 7, "frame_color": 8, "large_rect": (1, 1, 4, 4), "noise_cells": [(0, 0), (0, 5)]},
    "move_recolor": {"rows": 6, "cols": 6, "object_color": 3, "target_color": 6, "direction": "down", "steps": 1, "shape": "domino_v"},
    "symmetry_border": {"rows": 6, "cols": 6, "object_color": 2, "frame_color": 8, "seed_cells": [(0, 2), (5, 3)]},
    "copy_line": {"rows": 6, "cols": 6, "line_value": 2, "axis": "horizontal", "line_index": 3, "gap_index": 4},
    "fill_border": {"rows": 6, "cols": 6, "border_color": 2, "fill_color": 4, "frame_color": 8},
    "line_border": {"rows": 6, "cols": 6, "line_value": 2, "axis": "horizontal", "line_index": 2, "gap_index": 1, "frame_color": 8},
    "extract_symmetry": {"rows": 6, "cols": 6, "large_color": 2, "small_color": 6, "large_rect": (1, 1, 4, 4), "small_cells": [(0, 0), (0, 5)]},
    "rotate_recolor": {"rows": 6, "cols": 6, "object_color": 2, "target_color": 6, "shape": "l3"},
    "reflect_move": {"rows": 6, "cols": 6, "object_color": 2, "axis": "horizontal", "direction": "right", "steps": 1, "shape": "asym_l"},
    "rotate_reflect": {"rows": 6, "cols": 6, "object_color": 2, "axis": "vertical", "shape": "l3"},
    "reflect_recolor": {"rows": 6, "cols": 6, "object_color": 2, "target_color": 5, "axis": "vertical", "shape": "asym_l"},
    "noise_count": {"rows": 6, "cols": 6, "object_color": 2, "noise_color": 7, "pattern_color": 5, "count": 3, "row_index": 3, "object_cells": [(1, 1), (1, 4), (4, 2)], "noise_cells": [(0, 0), (5, 5)]},
    "extract_count": {"rows": 6, "cols": 6, "large_color": 2, "small_color": 7, "pattern_color": 5, "row_index": 3, "large_cells": [(1, 1), (1, 2), (2, 1), (2, 2)], "small_cells": [(5, 5)]},
    "symmetry_line": {"rows": 6, "cols": 6, "line_value": 2, "seed_cells": [(2, 1), (2, 4)], "axis": "horizontal", "line_index": 2, "gap_index": 3},
    "move_symmetry": {"rows": 6, "cols": 6, "object_color": 3, "direction": "right", "steps": 1, "shape": "domino_h"},
    "fill_symmetry": {"rows": 6, "cols": 6, "border_color": 2, "fill_color": 4, "seed_cells": [(0, 2)]},
    "count_recolor": {"rows": 6, "cols": 6, "object_color": 2, "pattern_color": 4, "target_color": 7, "count": 3, "row_index": 3},
    "rotate_border": {"rows": 6, "cols": 6, "object_color": 2, "frame_color": 8, "shape": "l3"},
    "reflect_border": {"rows": 6, "cols": 6, "object_color": 2, "frame_color": 8, "axis": "horizontal", "shape": "asym_l"},
    "rotate_move": {"rows": 6, "cols": 6, "object_color": 2, "direction": "right", "steps": 1, "shape": "l3"},
    "reflect_symmetry": {"rows": 6, "cols": 6, "object_color": 2, "axis": "vertical", "shape": "asym_l"},
    "noise_symmetry": {"rows": 6, "cols": 6, "object_color": 2, "noise_color": 7, "large_rect": (1, 1, 4, 4), "noise_cells": [(0, 0), (5, 5)]},
    "extract_line": {"rows": 6, "cols": 6, "large_color": 2, "small_color": 7, "large_rect": (1, 1, 4, 4), "small_cells": [(0, 0)], "axis": "horizontal", "line_index": 2, "line_value": 2},
    "count_line": {"rows": 6, "cols": 6, "object_color": 2, "pattern_color": 4, "count": 3, "row_index": 3, "axis": "horizontal", "line_index": 3},
    "fill_count": {"rows": 6, "cols": 6, "border_color": 2, "fill_color": 4, "pattern_color": 7, "row_index": 3},
    "symmetry_count": {"rows": 6, "cols": 6, "object_color": 2, "pattern_color": 7, "row_index": 3, "seed_cells": [(0, 1)]},
    "move_reflect": {"rows": 6, "cols": 6, "object_color": 2, "direction": "right", "steps": 1, "axis": "horizontal", "shape": "asym_l"},
}


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


def to_arc_style_synthetic_2_step_pilot_json_safe_v1(value: Any) -> Any:
    safe = _json_safe(value)
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def _grid(rows: int, cols: int, fill: int = 0) -> list[list[int]]:
    return [[fill for _ in range(cols)] for _ in range(rows)]


def _clone_grid(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _set_cell(grid: list[list[int]], row: int, col: int, value: int) -> None:
    if 0 <= row < len(grid) and 0 <= col < len(grid[row]):
        grid[row][col] = value


def _set_rect(grid: list[list[int]], top: int, left: int, bottom: int, right: int, value: int) -> None:
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            _set_cell(grid, row, col, value)


def _background_value_from_grid(grid: Sequence[Sequence[int]]) -> int:
    counts = Counter(cell for row in grid for cell in row)
    return int(counts.most_common(1)[0][0]) if counts else 0


def _non_background_value(grid: Sequence[Sequence[int]], background_value: int) -> int | None:
    counts = Counter(cell for row in grid for cell in row if cell != background_value)
    return int(counts.most_common(1)[0][0]) if counts else None


def _neighbors(row: int, col: int) -> list[tuple[int, int]]:
    return [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]


def _connected_components(grid: Sequence[Sequence[int]], background_value: int = 0) -> list[list[tuple[int, int]]]:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(rows):
        for col in range(cols):
            if (row, col) in seen or grid[row][col] == background_value:
                continue
            stack = [(row, col)]
            component: list[tuple[int, int]] = []
            seen.add((row, col))
            while stack:
                current_row, current_col = stack.pop()
                component.append((current_row, current_col))
                for next_row, next_col in _neighbors(current_row, current_col):
                    if not (0 <= next_row < rows and 0 <= next_col < cols):
                        continue
                    if (next_row, next_col) in seen or grid[next_row][next_col] == background_value:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            components.append(component)
    components.sort(key=lambda cells: (-len(cells), min(cells)))
    return components


def _shape_cells(shape: str, *, origin_row: int, origin_col: int) -> list[tuple[int, int]]:
    relative = {
        "single": [(0, 0)],
        "domino_h": [(0, 0), (0, 1)],
        "domino_v": [(0, 0), (1, 0)],
        "l3": [(0, 1), (1, 0), (1, 1)],
        "asym_l": [(0, 1), (1, 1), (1, 2)],
        "plus_small": [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
    }.get(shape, [(0, 0)])
    return [(origin_row + row, origin_col + col) for row, col in relative]


def _paint_shape(grid: list[list[int]], shape: str, *, origin_row: int, origin_col: int, value: int) -> None:
    for row, col in _shape_cells(shape, origin_row=origin_row, origin_col=origin_col):
        _set_cell(grid, row, col, value)


def _copy_grid(grid: Sequence[Sequence[int]], **_: Any) -> list[list[int]]:
    return _clone_grid(grid)


def _recolor_symbol(grid: Sequence[Sequence[int]], *, from_value: int | None = None, to_value: int | None = None, background_value: int = 0) -> list[list[int]]:
    source = _clone_grid(grid)
    actual_from = from_value if from_value is not None else _non_background_value(source, background_value)
    if actual_from is None or to_value is None:
        return source
    for row_index, row in enumerate(source):
        for col_index, value in enumerate(row):
            if value == actual_from:
                source[row_index][col_index] = to_value
    return source


def _move_single_object(grid: Sequence[Sequence[int]], *, direction: str, steps: int = 1, object_value: int | None = None, background_value: int = 0) -> list[list[int]]:
    delta_map = {
        "up": (-steps, 0),
        "down": (steps, 0),
        "left": (0, -steps),
        "right": (0, steps),
    }
    if direction not in delta_map:
        return _clone_grid(grid)
    value = object_value if object_value is not None else _non_background_value(grid, background_value)
    if value is None:
        return _clone_grid(grid)
    delta_row, delta_col = delta_map[direction]
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    output = _grid(rows, cols, background_value)
    for row in range(rows):
        for col in range(cols):
            if grid[row][col] != value:
                continue
            new_row = row + delta_row
            new_col = col + delta_col
            if 0 <= new_row < rows and 0 <= new_col < cols:
                output[new_row][new_col] = value
    return output


def _fill_region(grid: Sequence[Sequence[int]], *, fill_value: int, background_value: int = 0) -> list[list[int]]:
    output = _clone_grid(grid)
    rows = len(output)
    cols = len(output[0]) if rows else 0
    top = left = bottom = right = None
    for row in range(rows):
        for col in range(cols):
            if output[row][col] != background_value:
                top = row if top is None else min(top, row)
                left = col if left is None else min(left, col)
                bottom = row if bottom is None else max(bottom, row)
                right = col if right is None else max(right, col)
    if top is None or bottom is None or left is None or right is None or bottom - top < 2 or right - left < 2:
        return output
    for row in range(top + 1, bottom):
        for col in range(left + 1, right):
            output[row][col] = fill_value
    return output


def _extract_largest_object(grid: Sequence[Sequence[int]], *, background_value: int = 0) -> list[list[int]]:
    output = _grid(len(grid), len(grid[0]) if grid else 0, background_value)
    components = _connected_components(grid, background_value=background_value)
    if not components:
        return output
    component = components[0]
    value = grid[component[0][0]][component[0][1]]
    for row, col in component:
        output[row][col] = value
    return output


def _border_frame(grid: Sequence[Sequence[int]], *, frame_value: int) -> list[list[int]]:
    output = _clone_grid(grid)
    rows = len(output)
    cols = len(output[0]) if rows else 0
    if not rows or not cols:
        return output
    for row in range(rows):
        output[row][0] = frame_value
        output[row][cols - 1] = frame_value
    for col in range(cols):
        output[0][col] = frame_value
        output[rows - 1][col] = frame_value
    return output


def _complete_symmetry(grid: Sequence[Sequence[int]], *, axes: Sequence[str] | None = None, background_value: int = 0) -> list[list[int]]:
    axes = tuple(axes or ("horizontal", "vertical"))
    output = _clone_grid(grid)
    rows = len(output)
    cols = len(output[0]) if rows else 0
    for row in range(rows):
        for col in range(cols):
            value = output[row][col]
            if value == background_value:
                continue
            targets = [(row, col)]
            if "horizontal" in axes:
                targets.append((rows - 1 - row, col))
            if "vertical" in axes:
                targets.append((row, cols - 1 - col))
            if "horizontal" in axes and "vertical" in axes:
                targets.append((rows - 1 - row, cols - 1 - col))
            for target_row, target_col in targets:
                output[target_row][target_col] = value
    return output


def _line_completion(
    grid: Sequence[Sequence[int]],
    *,
    axis: str,
    line_index: int,
    line_value: int,
    background_value: int = 0,
) -> list[list[int]]:
    output = _clone_grid(grid)
    rows = len(output)
    cols = len(output[0]) if rows else 0
    if axis == "horizontal" and 0 <= line_index < rows:
        active = [col for col in range(cols) if output[line_index][col] == line_value]
        if active:
            for col in range(min(active), max(active) + 1):
                output[line_index][col] = line_value
    elif axis == "vertical" and 0 <= line_index < cols:
        active = [row for row in range(rows) if output[row][line_index] == line_value]
        if active:
            for row in range(min(active), max(active) + 1):
                output[row][line_index] = line_value
    return output


def _remove_background_noise(grid: Sequence[Sequence[int]], *, background_value: int = 0) -> list[list[int]]:
    output = _clone_grid(grid)
    for component in _connected_components(grid, background_value=background_value):
        if len(component) <= 1:
            for row, col in component:
                output[row][col] = background_value
    return output


def _object_count_to_pattern(
    grid: Sequence[Sequence[int]],
    *,
    count: int | None = None,
    pattern_value: int,
    row_index: int,
    background_value: int = 0,
) -> list[list[int]]:
    output = _grid(len(grid), len(grid[0]) if grid else 0, background_value)
    actual_count = count if count is not None else len(_connected_components(grid, background_value=background_value))
    if not output:
        return output
    width = len(output[0])
    start = max(0, min(width - 1, 1))
    end = min(width - 1, start + max(0, int(actual_count)) - 1)
    if 0 <= row_index < len(output):
        for col in range(start, end + 1):
            output[row_index][col] = pattern_value
    return output


def _rotate_object_90(grid: Sequence[Sequence[int]], *, background_value: int = 0) -> list[list[int]]:
    output = _grid(len(grid), len(grid[0]) if grid else 0, background_value)
    components = _connected_components(grid, background_value=background_value)
    if not components:
        return _clone_grid(grid)
    component = components[0]
    top = min(row for row, _ in component)
    left = min(col for _, col in component)
    bottom = max(row for row, _ in component)
    right = max(col for _, col in component)
    height = bottom - top + 1
    width = right - left + 1
    for row, col in component:
        value = grid[row][col]
        local_row = row - top
        local_col = col - left
        new_row = top + local_col
        new_col = left + (height - 1 - local_row)
        if 0 <= new_row < len(output) and 0 <= new_col < len(output[new_row]):
            output[new_row][new_col] = value
    return output


def _reflect_object_horizontal_or_vertical(
    grid: Sequence[Sequence[int]], *, axis: str, background_value: int = 0
) -> list[list[int]]:
    output = _grid(len(grid), len(grid[0]) if grid else 0, background_value)
    components = _connected_components(grid, background_value=background_value)
    if not components:
        return _clone_grid(grid)
    component = components[0]
    top = min(row for row, _ in component)
    left = min(col for _, col in component)
    bottom = max(row for row, _ in component)
    right = max(col for _, col in component)
    for row, col in component:
        value = grid[row][col]
        if axis == "horizontal":
            new_row, new_col = row, right - (col - left)
        else:
            new_row, new_col = bottom - (row - top), col
        output[new_row][new_col] = value
    return output


_PRIMITIVE_EXECUTORS_V1 = {
    "copy_grid": _copy_grid,
    "recolor_symbol": _recolor_symbol,
    "move_single_object": _move_single_object,
    "fill_region": _fill_region,
    "extract_largest_object": _extract_largest_object,
    "border_frame": _border_frame,
    "complete_symmetry": _complete_symmetry,
    "line_completion": _line_completion,
    "remove_background_noise": _remove_background_noise,
    "object_count_to_pattern": _object_count_to_pattern,
    "rotate_object_90": _rotate_object_90,
    "reflect_object_horizontal_or_vertical": _reflect_object_horizontal_or_vertical,
}


def _apply_primitive(grid: Sequence[Sequence[int]], primitive_id: str, parameters: Mapping[str, Any]) -> list[list[int]]:
    executor = _PRIMITIVE_EXECUTORS_V1[primitive_id]
    return executor(_clone_grid(grid), **dict(parameters))


def _apply_sequence(grid: Sequence[Sequence[int]], sequence: Sequence[Mapping[str, Any]]) -> list[list[int]]:
    output = _clone_grid(grid)
    for step in sequence:
        output = _apply_primitive(output, _safe_text(step.get("primitive_id")), step.get("parameters", {}))
    return output


def _variant_adjusted_cells(cells: Sequence[tuple[int, int]], variant_index: int) -> list[tuple[int, int]]:
    return [((row + (variant_index % 2)) % 6, (col + ((variant_index // 2) % 2)) % 6) for row, col in cells]


def _build_scene_input(scene_type: str, variant_index: int) -> list[list[int]]:
    params = deepcopy(SCENE_PARAMETERS_BY_TYPE_V1[scene_type])
    rows = int(params.get("rows", 6))
    cols = int(params.get("cols", 6))
    grid = _grid(rows, cols, 0)

    if scene_type in {"noise_extract", "noise_recolor", "extract_recolor", "extract_border", "noise_border", "noise_symmetry", "extract_line", "extract_symmetry"}:
        rect = params.get("large_rect", (1, 1, 4, 4))
        color = int(params.get("large_color", params.get("object_color", 2)))
        _set_rect(grid, *rect, color)
        for row, col in _variant_adjusted_cells(params.get("noise_cells", params.get("small_cells", [])), variant_index):
            _set_cell(grid, row, col, int(params.get("noise_color", params.get("small_color", 7))))
    elif scene_type in {"move_border", "move_recolor", "move_symmetry", "move_reflect", "copy_recolor", "copy_border", "recolor_border", "rotate_recolor", "rotate_border", "rotate_move", "rotate_reflect", "reflect_move", "reflect_recolor", "reflect_border", "reflect_symmetry"}:
        origin_row = 1 + (variant_index % 2)
        origin_col = 1 + ((variant_index // 2) % 2)
        shape = _safe_text(params.get("shape"), "single")
        _paint_shape(grid, shape, origin_row=origin_row, origin_col=origin_col, value=int(params.get("object_color", params.get("source_color", 2))))
    elif scene_type in {"fill_recolor", "fill_line", "fill_border", "fill_symmetry", "fill_count"}:
        border_color = int(params.get("border_color", 2))
        for col in range(cols):
            grid[0][col] = border_color
            grid[rows - 1][col] = border_color
        for row in range(rows):
            grid[row][0] = border_color
            grid[row][cols - 1] = border_color
    elif scene_type in {"symmetry_recolor", "symmetry_border", "symmetry_line", "symmetry_count"}:
        object_color = int(params.get("source_color", params.get("object_color", 2)))
        for row, col in _variant_adjusted_cells(params.get("seed_cells", []), variant_index):
            _set_cell(grid, row, col, object_color)
    elif scene_type in {"count_border", "count_recolor", "count_line"}:
        object_color = int(params.get("object_color", 2))
        count = int(params.get("count", 3)) + (variant_index % 2)
        cells = [(1, 1), (1, 4), (4, 2), (4, 4)]
        for row, col in cells[:count]:
            _set_cell(grid, row, col, object_color)
    elif scene_type in {"noise_count"}:
        object_color = int(params.get("object_color", 2))
        for row, col in params.get("object_cells", []):
            _set_cell(grid, row, col, object_color)
        for row, col in _variant_adjusted_cells(params.get("noise_cells", []), variant_index):
            _set_cell(grid, row, col, int(params.get("noise_color", 7)))
    elif scene_type in {"extract_count"}:
        large_color = int(params.get("large_color", 2))
        for row, col in params.get("large_cells", []):
            _set_cell(grid, row, col, large_color)
        for row, col in _variant_adjusted_cells(params.get("small_cells", []), variant_index):
            _set_cell(grid, row, col, int(params.get("small_color", 7)))
    elif scene_type in {"line_recolor", "copy_line", "line_border"}:
        line_value = int(params.get("line_value", 2))
        line_index = int(params.get("line_index", rows // 2))
        gap_index = (int(params.get("gap_index", 2)) + variant_index) % cols
        for col in range(cols):
            if col != gap_index:
                grid[line_index][col] = line_value
    else:
        raise AssertionError(f"unsupported scene_type={scene_type}")
    return grid


def _primitive_parameters_for_scene(scene_type: str, variant_index: int) -> dict[str, dict[str, Any]]:
    params = deepcopy(SCENE_PARAMETERS_BY_TYPE_V1[scene_type])
    background = 0
    count = int(params.get("count", 3)) + (variant_index % 2)
    mapping = {
        "copy_grid": {},
        "recolor_symbol": {
            "from_value": int(params.get("source_color", params.get("object_color", params.get("fill_color", params.get("pattern_color", 2))))),
            "to_value": int(params.get("target_color", 7)),
            "background_value": background,
        },
        "move_single_object": {
            "direction": _safe_text(params.get("direction"), "right"),
            "steps": int(params.get("steps", 1)),
            "object_value": int(params.get("object_color", 2)),
            "background_value": background,
        },
        "fill_region": {
            "fill_value": int(params.get("fill_color", 4)),
            "background_value": background,
        },
        "extract_largest_object": {"background_value": background},
        "border_frame": {"frame_value": int(params.get("frame_color", 8))},
        "complete_symmetry": {"axes": ["horizontal", "vertical"], "background_value": background},
        "line_completion": {
            "axis": _safe_text(params.get("axis"), "horizontal"),
            "line_index": int(params.get("line_index", 3)),
            "line_value": int(params.get("line_value", params.get("fill_color", params.get("object_color", params.get("pattern_color", 2))))),
            "background_value": background,
        },
        "object_count_to_pattern": {
            "count": None,
            "pattern_value": int(params.get("pattern_color", 7)),
            "row_index": int(params.get("row_index", 3)),
            "background_value": background,
        },
        "remove_background_noise": {"background_value": background},
        "rotate_object_90": {"background_value": background},
        "reflect_object_horizontal_or_vertical": {
            "axis": _safe_text(params.get("axis"), "horizontal"),
            "background_value": background,
        },
    }
    if scene_type == "extract_count":
        mapping["object_count_to_pattern"]["count"] = None
        mapping["object_count_to_pattern"]["pattern_value"] = int(params.get("pattern_color", 5))
    if scene_type == "count_border":
        mapping["object_count_to_pattern"]["pattern_value"] = int(params.get("pattern_color", 7))
    if scene_type == "count_recolor":
        mapping["object_count_to_pattern"]["pattern_value"] = int(params.get("pattern_color", 4))
    if scene_type == "count_line":
        mapping["object_count_to_pattern"]["pattern_value"] = int(params.get("pattern_color", 4))
    if scene_type == "noise_count":
        mapping["object_count_to_pattern"]["pattern_value"] = int(params.get("pattern_color", 5))
    return mapping


def _build_task_from_spec(task_id: str, difficulty_bucket: str, primitive_pair: Sequence[str], scene_type: str) -> dict[str, Any]:
    intended_sequence: list[dict[str, Any]] = []
    parameters_by_primitive = _primitive_parameters_for_scene(scene_type, 0)
    for primitive_id in primitive_pair:
        intended_sequence.append({"primitive_id": primitive_id, "parameters": deepcopy(parameters_by_primitive[primitive_id])})
    train_pairs = []
    expected_outputs = []
    test_inputs = []
    intermediate_outputs = []
    for variant_index in range(TRAIN_PAIR_COUNT_V1 + TEST_INPUT_COUNT_V1):
        input_grid = _build_scene_input(scene_type, variant_index)
        local_params = _primitive_parameters_for_scene(scene_type, variant_index)
        sequence = [{"primitive_id": primitive_id, "parameters": deepcopy(local_params[primitive_id])} for primitive_id in primitive_pair]
        first_output = _apply_primitive(input_grid, primitive_pair[0], sequence[0]["parameters"])
        final_output = _apply_sequence(input_grid, sequence)
        if variant_index < TRAIN_PAIR_COUNT_V1:
            train_pairs.append(
                build_arc_style_grid_train_pair_v1(
                    f"{task_id}_train_{variant_index}",
                    input_grid,
                    final_output,
                    f"2-step {primitive_pair[0]} then {primitive_pair[1]} synthetic pilot",
                )
            )
        else:
            test_inputs.append({"test_input_id": f"test_{variant_index - TRAIN_PAIR_COUNT_V1}", "input_grid": input_grid, "notes": scene_type})
            expected_outputs.append({"test_input_id": f"test_{variant_index - TRAIN_PAIR_COUNT_V1}", "output_grid": final_output, "notes": scene_type, "synthetic_only": True})
            intermediate_outputs.append(first_output)
    composition_pair = f"{primitive_pair[0]} -> {primitive_pair[1]}"
    trace = {
        "toy_task": True,
        "internal_synthetic_only": True,
        "toy_task_type": composition_pair,
        "composition_pair": composition_pair,
        "difficulty_bucket": difficulty_bucket,
        "synthetic_2_step_pilot": True,
        "uses_train_output_for_transformation_inference": True,
        "uses_test_output": False,
        "uses_task_id_for_candidate_selection": False,
        "uses_notes_for_candidate_selection": False,
        "lookup_table_detected": False,
    }
    packet = build_arc_style_grid_task_packet_v1(
        task_id=task_id,
        task_source=TASK_SOURCE_INTERNAL_2_STEP_PILOT_V1,
        train_pairs=train_pairs,
        test_input=test_inputs[0]["input_grid"],
        candidate_outputs=[],
        validation_results=[],
        failure_notes=[],
        trace=trace,
    )
    return {
        "task_id": task_id,
        "source_task_id": task_id,
        "difficulty_bucket": difficulty_bucket,
        "composition_pair": composition_pair,
        "primitive_pair": list(primitive_pair),
        "scene_type": scene_type,
        "task_packet": packet,
        "expected_outputs": expected_outputs,
        "intermediate_outputs": intermediate_outputs,
        "intended_sequence": intended_sequence,
        "leakage_flags": {
            "synthetic_only": True,
            "uses_public_arc_data": False,
            "uses_kaggle_data": False,
            "uses_solution_file": False,
            "uses_answer_key": False,
            "uses_test_output_for_candidate_generation": False,
            "uses_task_id_shortcut": False,
            "uses_notes_shortcut": False,
            "uses_provider_model_api": False,
        },
        "boundary_flags": {
            "metadata_only": True,
            "no_public_arc_data": True,
            "no_kaggle_data": True,
            "no_solution_file": True,
            "no_answer_key": True,
            "no_test_output_access_for_solver": True,
            "no_task_id_shortcut": True,
            "no_notes_shortcut": True,
            "no_provider_model_api": True,
            "no_chat_responder": True,
            "no_runtime_wiring": True,
        },
    }


def _rebuild_packet(packet: Mapping[str, Any], *, mode: str, suffix: str, preserve_toy_task_type: bool) -> dict[str, Any]:
    original_trace = packet.get("trace", {}) if isinstance(packet.get("trace"), Mapping) else {}
    trace = {
        "internal_synthetic_only": True,
        "synthetic_2_step_pilot": True,
        "diagnostic_mode": mode,
        "uses_train_output_for_transformation_inference": True,
        "uses_test_output": False,
        "uses_task_id_for_candidate_selection": False,
        "uses_notes_for_candidate_selection": False,
        "lookup_table_detected": False,
    }
    if preserve_toy_task_type:
        toy_task_type = _safe_text(original_trace.get("toy_task_type"))
        if toy_task_type:
            trace["toy_task_type"] = toy_task_type
        composition_pair = _safe_text(original_trace.get("composition_pair"))
        if composition_pair:
            trace["composition_pair"] = composition_pair
        difficulty_bucket = _safe_text(original_trace.get("difficulty_bucket"))
        if difficulty_bucket:
            trace["difficulty_bucket"] = difficulty_bucket
    return build_arc_style_grid_task_packet_v1(
        task_id=f"{_safe_text(packet.get('task_id'))}{suffix}",
        task_source=_safe_text(packet.get("task_source"), TASK_SOURCE_INTERNAL_2_STEP_PILOT_V1),
        train_pairs=packet.get("train_pairs", []) if isinstance(packet.get("train_pairs"), list) else [],
        test_input=(packet.get("test_input") or {}).get("cell_values", []),
        candidate_outputs=[],
        validation_results=[],
        failure_notes=[],
        trace=trace,
    )


def build_arc_style_synthetic_2_step_pilot_plan_v1() -> dict[str, Any]:
    if len(TASK_SPECS_V1) != PILOT_TASK_COUNT_V1:
        raise AssertionError(f"task_specs={len(TASK_SPECS_V1)} expected={PILOT_TASK_COUNT_V1}")
    base_tasks = [_build_task_from_spec(task_id, bucket, pair, scene_type) for task_id, bucket, pair, scene_type in TASK_SPECS_V1]
    entries: list[dict[str, Any]] = []
    for task in base_tasks:
        packet = task["task_packet"]
        mode_packets = {
            "full_metadata": packet,
            "toy_task_type_preserved_guardrail": _rebuild_packet(
                packet,
                mode="toy_task_type_preserved_guardrail",
                suffix="__toy_task_type_preserved_guardrail",
                preserve_toy_task_type=True,
            ),
            "fully_stripped_lower_bound": _rebuild_packet(
                packet,
                mode="fully_stripped_lower_bound",
                suffix="__fully_stripped_lower_bound",
                preserve_toy_task_type=False,
            ),
            "shuffled_renamed": perturb_arc_style_task_metadata_v1(
                packet,
                task_id=f"{task['task_id']}__shuffled_renamed",
                notes=[],
                reverse_train_pairs=True,
                reorder_trace_fields=True,
                trace_overrides={"diagnostic_mode": "shuffled_renamed", "synthetic_2_step_pilot": True},
            ),
        }
        for mode in MODE_ORDER_V1:
            entries.append({
                "diagnostic_mode": mode,
                "task_id": _safe_text(mode_packets[mode].get("task_id")),
                "source_task_id": task["source_task_id"],
                "composition_pair": task["composition_pair"],
                "difficulty_bucket": task["difficulty_bucket"],
                "test_input_index": 0,
                "packet": _json_safe(mode_packets[mode]),
                "expected_grid": _json_safe(task["expected_outputs"][0]["output_grid"]),
                "input_grid": _json_safe(task["task_packet"]["test_input"]["cell_values"]),
                "intermediate_grid": _json_safe(task["intermediate_outputs"][0]),
                "intended_sequence": _json_safe(task["intended_sequence"]),
                "primitive_pair": list(task["primitive_pair"]),
                "leakage_flags": _json_safe(task["leakage_flags"]),
                "boundary_flags": _json_safe(task["boundary_flags"]),
            })
    expected_entry_count = PILOT_TASK_COUNT_V1 * len(MODE_ORDER_V1)
    if len(entries) != expected_entry_count:
        raise AssertionError(f"entries={len(entries)} expected={expected_entry_count}")
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "runner_id": RUNNER_ID_V1,
        "entry_point": RUNNER_ENTRY_POINT_V1,
        "pilot_task_count": PILOT_TASK_COUNT_V1,
        "modes": list(MODE_ORDER_V1),
        "task_specs": [
            {
                "task_id": task_id,
                "difficulty_bucket": bucket,
                "primitive_pair": list(pair),
                "composition_pair": f"{pair[0]} -> {pair[1]}",
                "scene_type": scene_type,
            }
            for task_id, bucket, pair, scene_type in TASK_SPECS_V1
        ],
        "entries": entries,
    }


def _normalized_solver_sequence(sequence: Sequence[Any]) -> list[str]:
    normalized: list[str] = []
    for item in sequence:
        if isinstance(item, Mapping):
            normalized.append(_safe_text(item.get("primitive_id")))
        else:
            normalized.append(_safe_text(item))
    return [item for item in normalized if item]


def _normalized_intended_sequence(sequence: Sequence[Any]) -> list[str]:
    normalized: list[str] = []
    for item in sequence:
        primitive_id = _safe_text(item.get("primitive_id")) if isinstance(item, Mapping) else _safe_text(item)
        normalized.append(SOLVER_PRIMITIVE_ID_ALIASES_V1.get(primitive_id, primitive_id))
    return [item for item in normalized if item]


def _classify_composition_failure(
    *,
    packet_status: str,
    selected_sequence: Sequence[Any],
    intended_sequence: Sequence[Any],
    difficulty_bucket: str,
) -> str:
    selected_ids = _normalized_solver_sequence(selected_sequence)
    intended_ids = _normalized_intended_sequence(intended_sequence)
    if packet_status == "exact" and selected_ids == intended_ids:
        return ""
    if len(selected_ids) >= 2 and len(intended_ids) >= 2 and selected_ids[:2] == list(reversed(intended_ids[:2])):
        return "right_primitives_wrong_order"
    if len(selected_ids) == 1 and selected_ids[0] in intended_ids:
        if packet_status == "exact":
            return "shortcut_single_step_false_solution"
        return "one_primitive_missing"
    if len(selected_ids) >= 1 and selected_ids[0] == intended_ids[0] and packet_status != "exact":
        return "first_step_correct_second_wrong"
    if len(selected_ids) >= 1 and selected_ids[-1] == intended_ids[-1] and packet_status != "exact":
        return "first_step_wrong_second_correct"
    if selected_ids == intended_ids and packet_status in {"partial", "unsupported"}:
        return "parameter_inference_failure"
    if packet_status == "failed":
        return "execution_failure"
    if difficulty_bucket == "stress" and packet_status in {"partial", "unsupported"}:
        return "ambiguous_train_evidence"
    if not selected_ids and packet_status in {"unsupported", "failed"}:
        return "generator_ambiguity"
    if packet_status in {"partial", "unsupported"}:
        return "parameter_inference_failure"
    return ""


def _mode_summary(mode: str, entries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    packets = [entry.get("packet") for entry in entries if isinstance(entry.get("packet"), Mapping)]
    dry_run = run_arc_style_bounded_solver_dry_run_v1(packets)
    task_results = dry_run.get("task_results", []) if isinstance(dry_run.get("task_results"), list) else []
    failures: list[dict[str, Any]] = []
    evaluations: list[dict[str, Any]] = []
    pair_summary: dict[str, dict[str, int]] = defaultdict(lambda: {key: 0 for key in EXPECTED_STATUS_KEYS_V1})
    bucket_summary: dict[str, dict[str, int]] = defaultdict(lambda: {key: 0 for key in EXPECTED_STATUS_KEYS_V1})
    failure_taxonomy_counts: Counter[str] = Counter()

    for entry, task_result in zip(entries, task_results):
        packet_result = _build_packet_result(
            task_id=_safe_text(entry.get("task_id")),
            family_id=_safe_text(entry.get("composition_pair")),
            variant_index=0,
            test_input_index=int(entry.get("test_input_index", 0)),
            packet=entry.get("packet", {}),
            task_result=task_result,
            expected_grid=entry.get("expected_grid", []),
            input_grid=entry.get("input_grid", []),
            failures=failures,
        )
        packet_status = _safe_text(packet_result.get("packet_status"))
        if packet_status not in EXPECTED_STATUS_KEYS_V1:
            packet_status = "failed"
        selected_sequence = task_result.get("selected_primitive_sequence", []) if isinstance(task_result.get("selected_primitive_sequence"), list) else []
        composition_failure = _classify_composition_failure(
            packet_status=packet_status,
            selected_sequence=selected_sequence,
            intended_sequence=entry.get("intended_sequence", []),
            difficulty_bucket=_safe_text(entry.get("difficulty_bucket")),
        )
        if composition_failure:
            failure_taxonomy_counts[composition_failure] += 1
        pair_summary[_safe_text(entry.get("composition_pair"))][packet_status] += 1
        bucket_summary[_safe_text(entry.get("difficulty_bucket"))][packet_status] += 1
        evaluations.append({
            "diagnostic_mode": _safe_text(entry.get("diagnostic_mode")),
            "task_id": _safe_text(entry.get("task_id")),
            "source_task_id": _safe_text(entry.get("source_task_id")),
            "composition_pair": _safe_text(entry.get("composition_pair")),
            "difficulty_bucket": _safe_text(entry.get("difficulty_bucket")),
            "test_input_index": int(entry.get("test_input_index", 0)),
            "selected_candidate_id": _safe_text(task_result.get("selected_candidate_id")),
            "selected_primitive_sequence": _json_safe(selected_sequence),
            "train_fit_status": _safe_text(task_result.get("train_fit_status")),
            "packet_status": packet_status,
            "non_exact_reason": _safe_text(",".join(_safe_text(note) for note in task_result.get("failure_notes", []) if _safe_text(note))
            ),
            "composition_failure_category": composition_failure,
            "expected_exact_match": packet_status == "exact",
            "leakage_flags": _json_safe(entry.get("leakage_flags", {})),
            "solver_leakage_trace": _json_safe(dry_run.get("trace", {})),
        })

    counts = Counter(item["packet_status"] for item in evaluations)
    return {
        "diagnostic_mode": mode,
        "packet_count": len(evaluations),
        "exact": counts.get("exact", 0),
        "partial": counts.get("partial", 0),
        "unsupported": counts.get("unsupported", 0),
        "failed": counts.get("failed", 0),
        "evaluations": evaluations,
        "pair_summary": {key: dict(value) for key, value in sorted(pair_summary.items())},
        "bucket_summary": {key: dict(value) for key, value in sorted(bucket_summary.items())},
        "failure_taxonomy_counts": {key: int(failure_taxonomy_counts.get(key, 0)) for key in FAILURE_TAXONOMY_V1},
        "failure_ledger": build_arc_style_synthetic_solver_failure_ledger_v1(failures),
        "dry_run_summary": {
            "selected_exact_match_count": int(dry_run.get("selected_exact_match_count", 0)),
            "selected_partial_match_count": int(dry_run.get("selected_partial_match_count", 0)),
            "selected_unsupported_count": int(dry_run.get("selected_unsupported_count", 0)),
            "trace": _json_safe(dry_run.get("trace", {})),
        },
    }


def run_arc_style_synthetic_2_step_40_pilot_diagnostic_v1() -> dict[str, Any]:
    plan = build_arc_style_synthetic_2_step_pilot_plan_v1()
    entries = plan["entries"]
    mode_to_entries: dict[str, list[dict[str, Any]]] = {mode: [] for mode in MODE_ORDER_V1}
    for entry in entries:
        mode_to_entries[_safe_text(entry.get("diagnostic_mode"))].append(dict(entry))
    mode_results = {mode: _mode_summary(mode, mode_to_entries[mode]) for mode in MODE_ORDER_V1}

    primary = mode_results["toy_task_type_preserved_guardrail"]
    trace_flags = {
        "uses_test_output": False,
        "uses_task_id_for_candidate_selection": False,
        "uses_notes_for_candidate_selection": False,
        "lookup_table_detected": False,
    }
    for mode in MODE_ORDER_V1:
        trace = mode_results[mode]["dry_run_summary"]["trace"]
        for key in trace_flags:
            trace_flags[key] = trace_flags[key] or bool(trace.get(key, False))

    result = {
        "schema_version": SCHEMA_VERSION_V1,
        "runner_id": RUNNER_ID_V1,
        "entry_point": RUNNER_ENTRY_POINT_V1,
        "deterministic": True,
        "synthetic_internal_result": True,
        "pilot_task_count": PILOT_TASK_COUNT_V1,
        "train_pair_count": TRAIN_PAIR_COUNT_V1,
        "test_input_count": TEST_INPUT_COUNT_V1,
        "attribution_modes": list(MODE_ORDER_V1),
        "difficulty_split": {"easy": 20, "medium": 10, "stress": 10},
        "task_inventory": _json_safe(plan.get("task_specs", [])),
        "mode_results": mode_results,
        "pilot_result": {
            "exact": int(primary["exact"]),
            "partial": int(primary["partial"]),
            "unsupported": int(primary["unsupported"]),
            "failed": int(primary["failed"]),
        },
        "pair_level_breakdown": _json_safe(primary["pair_summary"]),
        "bucket_level_breakdown": _json_safe(primary["bucket_summary"]),
        "failure_taxonomy_breakdown": _json_safe(primary["failure_taxonomy_counts"]),
        "evaluations": _json_safe(primary["evaluations"]),
        "all_mode_evaluations": {mode: _json_safe(mode_results[mode]["evaluations"]) for mode in MODE_ORDER_V1},
        "leakage_flags": _normalize_leakage_flags({}),
        "trace_flags": trace_flags,
        "denied_authority": list(DEFAULT_DENIED_AUTHORITY_V1),
        "authority_flags": {name: False for name in DEFAULT_DENIED_AUTHORITY_V1},
        "failure_taxonomy": list(FAILURE_TAXONOMY_V1),
        "no_score_claim": True,
        "official_score_claim": False,
        "boundary_preservation": {
            "solver_logic_changed": False,
            "single_step_runner_changed": False,
            "candidate_output_surface_wired": False,
            "replay_scoring_final_answer_added": False,
            "arc_agi2_participation_changed": False,
            "weslr_state_touched": False,
        },
    }
    return to_arc_style_synthetic_2_step_pilot_json_safe_v1(result)


def summarize_arc_style_synthetic_2_step_40_pilot_diagnostic_v1(result: Mapping[str, Any]) -> dict[str, Any]:
    pilot_result = result.get("pilot_result", {}) if isinstance(result, Mapping) else {}
    pair_level_breakdown = result.get("pair_level_breakdown", {}) if isinstance(result, Mapping) else {}
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "runner_id": _safe_text(result.get("runner_id")) if isinstance(result, Mapping) else "",
        "pilot_task_count": int(result.get("pilot_task_count", 0)) if isinstance(result, Mapping) else 0,
        "exact": int(pilot_result.get("exact", 0)) if isinstance(pilot_result, Mapping) else 0,
        "partial": int(pilot_result.get("partial", 0)) if isinstance(pilot_result, Mapping) else 0,
        "unsupported": int(pilot_result.get("unsupported", 0)) if isinstance(pilot_result, Mapping) else 0,
        "failed": int(pilot_result.get("failed", 0)) if isinstance(pilot_result, Mapping) else 0,
        "pair_count": len(pair_level_breakdown) if isinstance(pair_level_breakdown, Mapping) else 0,
        "attribution_modes": list(result.get("attribution_modes", [])) if isinstance(result, Mapping) else [],
    }


__all__ = [
    "FAILURE_TAXONOMY_V1",
    "MODE_ORDER_V1",
    "PILOT_TASK_COUNT_V1",
    "RUNNER_ENTRY_POINT_V1",
    "RUNNER_ID_V1",
    "SCHEMA_VERSION_V1",
    "TASK_SOURCE_INTERNAL_2_STEP_PILOT_V1",
    "build_arc_style_synthetic_2_step_pilot_plan_v1",
    "run_arc_style_synthetic_2_step_40_pilot_diagnostic_v1",
    "summarize_arc_style_synthetic_2_step_40_pilot_diagnostic_v1",
    "to_arc_style_synthetic_2_step_pilot_json_safe_v1",
]
