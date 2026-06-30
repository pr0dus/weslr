"""WESLR ARC-style synthetic task-family generators V1.

Deterministic synthetic-only ARC-style task generation for stress-testing the
schema helpers, phase-2 adapter boundary, dry-run logic, and ARC-AGI-2 top-2
submission contract compatibility.

This module does not ingest Kaggle data, ARC public data, hidden benchmark data,
solutions, answer keys, provider APIs, payment APIs, website/runtime wiring, or
`.weslr` state.
"""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Callable, Mapping, Sequence

from weslr.arc_agi2_submission_contract import (
    build_arc_agi2_attempt_v1,
    build_arc_agi2_top2_attempt_packet_v1,
    validate_arc_agi2_top2_attempt_packet_v1,
)
from weslr.arc_style_grid_schema_helpers import (
    TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
    build_arc_style_grid_metadata_v1,
    build_arc_style_grid_task_packet_v1,
    build_arc_style_grid_train_pair_v1,
    summarize_arc_style_grid_task_packet_v1,
    to_arc_style_grid_task_json_safe_v1,
    validate_arc_style_grid_task_packet_v1,
    validate_arc_style_grid_train_pair_v1,
)

SCHEMA_VERSION_V1 = "ArcStyleSyntheticTaskGeneratorsV1"
SUITE_ID_V1 = "arc_style_synthetic_task_suite_v1"
SYNTHETIC_ONLY_TASK_SOURCE_V1 = TASK_SOURCE_INTERNAL_SYNTHETIC_V1

REQUIRED_GENERATOR_SPEC_FIELDS_V1 = (
    "spec_id",
    "task_id",
    "family_id",
    "variant_index",
    "train_pair_count",
    "test_input_count",
    "difficulty_label",
    "transformation_labels",
    "generation_parameters",
    "leakage_flags",
)

REQUIRED_TASK_FAMILY_FIELDS_V1 = (
    "task_id",
    "family_id",
    "variant_index",
    "train_pairs",
    "test_inputs",
    "validation_metadata",
    "generator_metadata",
    "transformation_labels",
    "difficulty_label",
    "leakage_flags",
)

REQUIRED_SUITE_FIELDS_V1 = (
    "suite_id",
    "generator_specs",
    "tasks",
    "top2_contract_compatibility_checked",
    "generator_metadata",
)

REQUIRED_FAMILIES_V1 = (
    "copy_grid",
    "recolor_symbol",
    "move_single_object",
    "fill_region",
    "complete_symmetry",
    "border_frame",
    "extract_largest_object",
    "remove_background_noise",
    "line_completion",
    "object_count_to_pattern",
    "rotate_object_90",
    "reflect_object_horizontal_or_vertical",
)

LEAKAGE_FLAG_NAMES_V1 = (
    "synthetic_only",
    "uses_kaggle_data",
    "uses_arc_public_data",
    "uses_hidden_private_data",
    "uses_solution_file",
    "uses_answer_key",
    "uses_test_output_for_candidate_generation",
)

DITHER_DIFFICULTY_BY_VARIANT_V1 = {
    0: "easy",
    1: "medium",
    2: "hard",
}

FAMILY_TRANSFORMATION_LABELS_V1 = {
    "copy_grid": ("copy", "exact_match"),
    "recolor_symbol": ("recolor", "symbol_transform"),
    "move_single_object": ("translate", "single_object_move"),
    "fill_region": ("fill", "region_completion"),
    "complete_symmetry": ("mirror", "symmetry_completion"),
    "border_frame": ("frame", "border_completion"),
    "extract_largest_object": ("extract", "largest_object"),
    "remove_background_noise": ("denoise", "background_cleanup"),
    "line_completion": ("line_completion", "gap_filling"),
    "object_count_to_pattern": ("count", "count_to_pattern"),
    "rotate_object_90": ("rotate_90", "object_rotation"),
    "reflect_object_horizontal_or_vertical": ("reflect", "object_reflection"),
}

FAMILY_AXIS_BY_VARIANT_V1 = {
    0: "horizontal",
    1: "vertical",
    2: "horizontal",
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


def to_arc_style_synthetic_task_suite_json_safe_v1(value: Any) -> Any:
    safe = _json_safe(value)
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def to_arc_style_synthetic_task_suite_json_safe_v1_alias(value: Any) -> Any:
    return to_arc_style_synthetic_task_suite_json_safe_v1(value)


def _grid(rows: int, cols: int, fill: int = 0) -> list[list[int]]:
    return [[fill for _ in range(cols)] for _ in range(rows)]


def _clone_grid(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _set_cell(grid: list[list[int]], row: int, col: int, value: int) -> None:
    grid[row][col] = value


def _set_region(grid: list[list[int]], rows: Sequence[int], cols: Sequence[int], value: int) -> None:
    for row in rows:
        for col in cols:
            grid[row][col] = value


def _transpose(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def _reflect_horizontal(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _reflect_vertical(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(grid)]


def _rotate_90(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(reversed(col)) for col in zip(*grid)]


def _bounding_box(cells: Sequence[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _extract_object_cells(grid: Sequence[Sequence[int]], color: int) -> list[tuple[int, int]]:
    cells: list[tuple[int, int]] = []
    for row_index, row in enumerate(grid):
        for col_index, cell in enumerate(row):
            if cell == color:
                cells.append((row_index, col_index))
    return cells


def _place_object(grid: list[list[int]], cells: Sequence[tuple[int, int]], color: int) -> None:
    for row, col in cells:
        grid[row][col] = color


def _make_train_pair(pair_id: str, input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]], notes: str) -> dict[str, Any]:
    return build_arc_style_grid_train_pair_v1(pair_id, input_grid, output_grid, notes)


def _build_generator_spec(
    *,
    family_id: str,
    variant_index: int,
    task_id: str,
    train_pair_count: int,
    test_input_count: int,
    difficulty_label: str,
    transformation_labels: Sequence[str],
    generation_parameters: Mapping[str, Any],
    leakage_flags: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "spec_id": f"{family_id}_variant_{variant_index}_spec_v1",
        "task_id": _safe_text(task_id),
        "family_id": _safe_text(family_id),
        "variant_index": int(variant_index),
        "train_pair_count": int(train_pair_count),
        "test_input_count": int(test_input_count),
        "difficulty_label": _safe_text(difficulty_label),
        "transformation_labels": [_safe_text(label) for label in transformation_labels if _safe_text(label)],
        "generation_parameters": _json_safe(dict(generation_parameters)),
        "leakage_flags": _normalize_leakage_flags(leakage_flags or {}),
    }


def _normalize_leakage_flags(value: Any) -> dict[str, bool]:
    mapping = value if isinstance(value, Mapping) else {}
    return {name: bool(mapping.get(name, False)) for name in LEAKAGE_FLAG_NAMES_V1}


def _leakage_flags_are_clean(flags: Mapping[str, Any]) -> bool:
    return bool(flags.get("synthetic_only", False)) and all(
        not bool(flags.get(name, False)) for name in LEAKAGE_FLAG_NAMES_V1 if name != "synthetic_only"
    )


def _validate_generator_spec_shape(spec: Mapping[str, Any]) -> list[str]:
    blocked: list[str] = []
    missing = [field for field in REQUIRED_GENERATOR_SPEC_FIELDS_V1 if field not in spec]
    if missing:
        blocked.append("missing_required_fields")
        blocked.extend(f"missing:{field}" for field in missing)
        return blocked
    family_id = _safe_text(spec.get("family_id"))
    if family_id not in REQUIRED_FAMILIES_V1:
        blocked.append("family_id_not_supported")
    if _safe_text(spec.get("task_id")) == "":
        blocked.append("empty_task_id")
    try:
        variant_index = int(spec.get("variant_index", -1))
    except Exception:
        variant_index = -1
    try:
        train_pair_count = int(spec.get("train_pair_count", 0))
    except Exception:
        train_pair_count = 0
    try:
        test_input_count = int(spec.get("test_input_count", 0))
    except Exception:
        test_input_count = 0
    if variant_index < 0:
        blocked.append("variant_index_negative")
    if train_pair_count < 1:
        blocked.append("train_pair_count_invalid")
    if test_input_count < 1:
        blocked.append("test_input_count_invalid")
    if _safe_text(spec.get("difficulty_label")) == "":
        blocked.append("difficulty_label_empty")
    labels = spec.get("transformation_labels")
    if not isinstance(labels, list) or not labels:
        blocked.append("transformation_labels_invalid")
    if not isinstance(spec.get("generation_parameters"), Mapping):
        blocked.append("generation_parameters_not_mapping")
    leakage = _normalize_leakage_flags(spec.get("leakage_flags"))
    if not _leakage_flags_are_clean(leakage):
        blocked.append("leakage_flags_not_clean")
    return blocked


def build_arc_style_synthetic_generator_spec_v1(
    *,
    family_id: str,
    variant_index: int,
    task_id: str,
    train_pair_count: int,
    test_input_count: int,
    difficulty_label: str,
    transformation_labels: Sequence[str],
    generation_parameters: Mapping[str, Any],
    leakage_flags: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return _build_generator_spec(
        family_id=family_id,
        variant_index=variant_index,
        task_id=task_id,
        train_pair_count=train_pair_count,
        test_input_count=test_input_count,
        difficulty_label=difficulty_label,
        transformation_labels=transformation_labels,
        generation_parameters=generation_parameters,
        leakage_flags=leakage_flags,
    )


def validate_arc_style_synthetic_generator_spec_v1(spec: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "spec_id": None,
        "task_id": None,
        "family_id": None,
        "blocked_reason_labels": [],
    }
    if not isinstance(spec, Mapping):
        result["blocked_reason_labels"].append("spec_not_mapping")
        return result
    result["blocked_reason_labels"].extend(_validate_generator_spec_shape(spec))
    result["spec_id"] = _safe_text(spec.get("spec_id"))
    result["task_id"] = _safe_text(spec.get("task_id"))
    result["family_id"] = _safe_text(spec.get("family_id"))
    result["valid"] = not result["blocked_reason_labels"]
    return result


def _make_base_variant_parameters(family_id: str, variant_index: int) -> dict[str, Any]:
    rows = 4 + variant_index
    cols = 4 + (variant_index % 2)
    background_color = 0
    object_color = 1 + variant_index
    accent_color = 4 + variant_index
    secondary_color = 7 + variant_index
    return {
        "rows": rows,
        "cols": cols,
        "background_color": background_color,
        "object_color": object_color,
        "accent_color": accent_color,
        "secondary_color": secondary_color,
        "variant_index": variant_index,
        "family_id": family_id,
        "train_pair_count": 2 + (variant_index % 2),
        "test_input_count": 1 + (variant_index % 2),
        "difficulty_label": DITHER_DIFFICULTY_BY_VARIANT_V1[variant_index],
    }


def build_initial_arc_style_synthetic_generator_specs_v1() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for family_id in REQUIRED_FAMILIES_V1:
        for variant_index in range(3):
            parameters = _make_base_variant_parameters(family_id, variant_index)
            task_id = f"synthetic_{family_id}_variant_{variant_index + 1}_v1"
            specs.append(
                build_arc_style_synthetic_generator_spec_v1(
                    family_id=family_id,
                    variant_index=variant_index,
                    task_id=task_id,
                    train_pair_count=parameters["train_pair_count"],
                    test_input_count=parameters["test_input_count"],
                    difficulty_label=parameters["difficulty_label"],
                    transformation_labels=FAMILY_TRANSFORMATION_LABELS_V1[family_id],
                    generation_parameters=parameters,
                    leakage_flags={"synthetic_only": True},
                )
            )
    return specs


def _family_copy_grid(spec: Mapping[str, Any]) -> dict[str, Any]:
    params = spec["generation_parameters"]
    rows = int(params["rows"])
    cols = int(params["cols"])
    color = int(params["object_color"])
    variant_index = int(params.get("variant_index", 0))
    test_inputs = []
    expected = []
    train_pairs = []
    for idx in range(int(spec["train_pair_count"])):
        input_grid = _grid(rows, cols, 0)
        if variant_index == 1 and idx == 0:
            _set_cell(input_grid, 0, 0, color)
            _set_cell(input_grid, 0, 1, color)
        elif variant_index == 1 and idx == 2:
            _set_cell(input_grid, 1 % rows, 3 % cols, color)
        else:
            _set_cell(input_grid, idx % rows, idx % cols, color)
        if idx % 2 == 1 and variant_index != 1:
            _set_cell(input_grid, rows - 1, cols - 1, params["accent_color"])
        output_grid = _clone_grid(input_grid)
        train_pairs.append(_make_train_pair(f"{spec['task_id']}_train_{idx}", input_grid, output_grid, "copy the grid exactly"))
    for idx in range(int(spec["test_input_count"])):
        test_grid = _grid(rows, cols, 0)
        if variant_index == 1 and idx == 0:
            _set_cell(test_grid, 0, 1, color)
            _set_cell(test_grid, 0, 2, color)
        else:
            _set_cell(test_grid, idx % rows, (idx + 1) % cols, color)
        if idx % 2 == 1 and variant_index != 1:
            _set_cell(test_grid, 0, 0, params["accent_color"])
        test_inputs.append({"test_input_id": f"test_{idx}", "input_grid": test_grid, "notes": "copy task"})
        expected.append({"test_input_id": f"test_{idx}", "output_grid": _clone_grid(test_grid), "notes": "copy output", "synthetic_only": True})
    return {"train_pairs": train_pairs, "test_inputs": test_inputs, "expected_outputs": expected}


def _family_recolor_symbol(spec: Mapping[str, Any]) -> dict[str, Any]:
    params = spec["generation_parameters"]
    rows = int(params["rows"])
    cols = int(params["cols"])
    source_color = int(params["object_color"])
    target_color = int(params["accent_color"])
    train_pairs = []
    test_inputs = []
    expected = []
    for idx in range(int(spec["train_pair_count"])):
        input_grid = _grid(rows, cols, 0)
        _set_cell(input_grid, idx % rows, idx % cols, source_color)
        _set_cell(input_grid, (idx + 1) % rows, (idx + 1) % cols, source_color)
        output_grid = _clone_grid(input_grid)
        _set_cell(output_grid, idx % rows, idx % cols, target_color)
        _set_cell(output_grid, (idx + 1) % rows, (idx + 1) % cols, target_color)
        train_pairs.append(_make_train_pair(f"{spec['task_id']}_train_{idx}", input_grid, output_grid, "recolor the repeated symbol"))
    for idx in range(int(spec["test_input_count"])):
        test_grid = _grid(rows, cols, 0)
        _set_cell(test_grid, idx % rows, (idx + 1) % cols, source_color)
        _set_cell(test_grid, (idx + 2) % rows, (idx + 2) % cols, source_color)
        test_inputs.append({"test_input_id": f"test_{idx}", "input_grid": test_grid, "notes": "recolor task"})
        output_grid = _clone_grid(test_grid)
        _set_cell(output_grid, idx % rows, (idx + 1) % cols, target_color)
        _set_cell(output_grid, (idx + 2) % rows, (idx + 2) % cols, target_color)
        expected.append({"test_input_id": f"test_{idx}", "output_grid": output_grid, "notes": "recolor output", "synthetic_only": True})
    return {"train_pairs": train_pairs, "test_inputs": test_inputs, "expected_outputs": expected}


def _family_move_single_object(spec: Mapping[str, Any]) -> dict[str, Any]:
    params = spec["generation_parameters"]
    rows = int(params["rows"])
    cols = int(params["cols"])
    color = int(params["object_color"])
    train_pairs = []
    test_inputs = []
    expected = []
    for idx in range(int(spec["train_pair_count"])):
        input_grid = _grid(rows, cols, 0)
        input_row = 1
        input_col = 1 + idx
        output_row = input_row + 1
        output_col = input_col + 1
        _set_cell(input_grid, input_row, input_col, color)
        output_grid = _grid(rows, cols, 0)
        _set_cell(output_grid, output_row, output_col, color)
        train_pairs.append(_make_train_pair(f"{spec['task_id']}_train_{idx}", input_grid, output_grid, "move the single object"))
    for idx in range(int(spec["test_input_count"])):
        input_grid = _grid(rows, cols, 0)
        input_row = 1 + idx
        input_col = 1
        output_row = input_row + 1
        output_col = input_col + 1
        _set_cell(input_grid, input_row, input_col, color)
        output_grid = _grid(rows, cols, 0)
        _set_cell(output_grid, output_row, output_col, color)
        test_inputs.append({"test_input_id": f"test_{idx}", "input_grid": input_grid, "notes": "move task"})
        expected.append({"test_input_id": f"test_{idx}", "output_grid": output_grid, "notes": "move output", "synthetic_only": True})
    return {"train_pairs": train_pairs, "test_inputs": test_inputs, "expected_outputs": expected}


def _family_fill_region(spec: Mapping[str, Any]) -> dict[str, Any]:
    params = spec["generation_parameters"]
    rows = int(params["rows"])
    cols = int(params["cols"])
    fill_color = int(params["accent_color"])
    border_color = int(params["object_color"])
    train_pairs = []
    test_inputs = []
    expected = []
    for idx in range(int(spec["train_pair_count"])):
        input_grid = _grid(rows, cols, 0)
        for col in range(cols):
            input_grid[0][col] = border_color
            input_grid[rows - 1][col] = border_color
        for row in range(rows):
            input_grid[row][0] = border_color
            input_grid[row][cols - 1] = border_color
        output_grid = _clone_grid(input_grid)
        for row in range(1, rows - 1):
            for col in range(1, cols - 1):
                output_grid[row][col] = fill_color
        train_pairs.append(_make_train_pair(f"{spec['task_id']}_train_{idx}", input_grid, output_grid, "fill the enclosed region"))
    for idx in range(int(spec["test_input_count"])):
        input_grid = _grid(rows, cols, 0)
        for col in range(cols):
            input_grid[0][col] = border_color
            input_grid[rows - 1][col] = border_color
        for row in range(rows):
            input_grid[row][0] = border_color
            input_grid[row][cols - 1] = border_color
        test_inputs.append({"test_input_id": f"test_{idx}", "input_grid": input_grid, "notes": "fill region task"})
        output_grid = _clone_grid(input_grid)
        for row in range(1, rows - 1):
            for col in range(1, cols - 1):
                output_grid[row][col] = fill_color
        expected.append({"test_input_id": f"test_{idx}", "output_grid": output_grid, "notes": "filled region", "synthetic_only": True})
    return {"train_pairs": train_pairs, "test_inputs": test_inputs, "expected_outputs": expected}


def _family_complete_symmetry(spec: Mapping[str, Any]) -> dict[str, Any]:
    params = spec["generation_parameters"]
    rows = int(params["rows"])
    cols = int(params["cols"])
    color = int(params["object_color"])
    train_pairs = []
    test_inputs = []
    expected = []
    for idx in range(int(spec["train_pair_count"])):
        input_grid = _grid(rows, cols, 0)
        _set_cell(input_grid, 0, idx % cols, color)
        _set_cell(input_grid, rows - 1, (cols - 1) - (idx % cols), color)
        output_grid = _clone_grid(input_grid)
        for row in range(rows):
            for col in range(cols):
                if output_grid[row][col] == color:
                    output_grid[row][cols - 1 - col] = color
                    output_grid[rows - 1 - row][col] = color
        train_pairs.append(_make_train_pair(f"{spec['task_id']}_train_{idx}", input_grid, output_grid, "complete the symmetry"))
    for idx in range(int(spec["test_input_count"])):
        input_grid = _grid(rows, cols, 0)
        _set_cell(input_grid, 0, idx % cols, color)
        _set_cell(input_grid, rows - 1, cols - 1 - (idx % cols), color)
        test_inputs.append({"test_input_id": f"test_{idx}", "input_grid": input_grid, "notes": "symmetry task"})
        output_grid = _clone_grid(input_grid)
        for row in range(rows):
            for col in range(cols):
                if output_grid[row][col] == color:
                    output_grid[row][cols - 1 - col] = color
                    output_grid[rows - 1 - row][col] = color
        expected.append({"test_input_id": f"test_{idx}", "output_grid": output_grid, "notes": "symmetry output", "synthetic_only": True})
    return {"train_pairs": train_pairs, "test_inputs": test_inputs, "expected_outputs": expected}


def _family_border_frame(spec: Mapping[str, Any]) -> dict[str, Any]:
    params = spec["generation_parameters"]
    rows = int(params["rows"])
    cols = int(params["cols"])
    frame_color = int(params["accent_color"])
    inner_color = int(params["object_color"])
    train_pairs = []
    test_inputs = []
    expected = []
    for idx in range(int(spec["train_pair_count"])):
        input_grid = _grid(rows, cols, 0)
        _set_cell(input_grid, rows // 2, cols // 2, inner_color)
        output_grid = _clone_grid(input_grid)
        for row in range(rows):
            output_grid[row][0] = frame_color
            output_grid[row][cols - 1] = frame_color
        for col in range(cols):
            output_grid[0][col] = frame_color
            output_grid[rows - 1][col] = frame_color
        train_pairs.append(_make_train_pair(f"{spec['task_id']}_train_{idx}", input_grid, output_grid, "add a border frame"))
    for idx in range(int(spec["test_input_count"])):
        input_grid = _grid(rows, cols, 0)
        _set_cell(input_grid, rows // 2, cols // 2, inner_color)
        test_inputs.append({"test_input_id": f"test_{idx}", "input_grid": input_grid, "notes": "border task"})
        output_grid = _clone_grid(input_grid)
        for row in range(rows):
            output_grid[row][0] = frame_color
            output_grid[row][cols - 1] = frame_color
        for col in range(cols):
            output_grid[0][col] = frame_color
            output_grid[rows - 1][col] = frame_color
        expected.append({"test_input_id": f"test_{idx}", "output_grid": output_grid, "notes": "border output", "synthetic_only": True})
    return {"train_pairs": train_pairs, "test_inputs": test_inputs, "expected_outputs": expected}


def _family_extract_largest_object(spec: Mapping[str, Any]) -> dict[str, Any]:
    params = spec["generation_parameters"]
    rows = int(params["rows"])
    cols = int(params["cols"])
    small_color = int(params["object_color"])
    large_color = int(params["accent_color"])
    train_pairs = []
    test_inputs = []
    expected = []
    for idx in range(int(spec["train_pair_count"])):
        input_grid = _grid(rows, cols, 0)
        _set_cell(input_grid, 0, idx % cols, small_color)
        _set_cell(input_grid, rows - 1, cols - 1 - idx % cols, small_color)
        _set_region(input_grid, range(1, rows - 1), range(1, cols - 1), large_color)
        output_grid = _grid(rows, cols, 0)
        _set_region(output_grid, range(1, rows - 1), range(1, cols - 1), large_color)
        train_pairs.append(_make_train_pair(f"{spec['task_id']}_train_{idx}", input_grid, output_grid, "extract the largest object"))
    for idx in range(int(spec["test_input_count"])):
        input_grid = _grid(rows, cols, 0)
        _set_cell(input_grid, 0, idx % cols, small_color)
        _set_cell(input_grid, rows - 1, cols - 1 - idx % cols, small_color)
        _set_region(input_grid, range(1, rows - 1), range(1, cols - 1), large_color)
        test_inputs.append({"test_input_id": f"test_{idx}", "input_grid": input_grid, "notes": "largest object task"})
        output_grid = _grid(rows, cols, 0)
        _set_region(output_grid, range(1, rows - 1), range(1, cols - 1), large_color)
        expected.append({"test_input_id": f"test_{idx}", "output_grid": output_grid, "notes": "largest object output", "synthetic_only": True})
    return {"train_pairs": train_pairs, "test_inputs": test_inputs, "expected_outputs": expected}


def _family_remove_background_noise(spec: Mapping[str, Any]) -> dict[str, Any]:
    params = spec["generation_parameters"]
    rows = int(params["rows"])
    cols = int(params["cols"])
    object_color = int(params["object_color"])
    noise_color = int(params["secondary_color"])
    train_pairs = []
    test_inputs = []
    expected = []
    for idx in range(int(spec["train_pair_count"])):
        input_grid = _grid(rows, cols, 0)
        _set_region(input_grid, range(1, rows - 1), range(1, cols - 1), object_color)
        _set_cell(input_grid, 0, idx % cols, noise_color)
        _set_cell(input_grid, rows - 1, cols - 1 - idx % cols, noise_color)
        output_grid = _grid(rows, cols, 0)
        _set_region(output_grid, range(1, rows - 1), range(1, cols - 1), object_color)
        train_pairs.append(_make_train_pair(f"{spec['task_id']}_train_{idx}", input_grid, output_grid, "remove background noise"))
    for idx in range(int(spec["test_input_count"])):
        input_grid = _grid(rows, cols, 0)
        _set_region(input_grid, range(1, rows - 1), range(1, cols - 1), object_color)
        _set_cell(input_grid, 0, idx % cols, noise_color)
        _set_cell(input_grid, rows - 1, cols - 1 - idx % cols, noise_color)
        test_inputs.append({"test_input_id": f"test_{idx}", "input_grid": input_grid, "notes": "denoise task"})
        output_grid = _grid(rows, cols, 0)
        _set_region(output_grid, range(1, rows - 1), range(1, cols - 1), object_color)
        expected.append({"test_input_id": f"test_{idx}", "output_grid": output_grid, "notes": "clean output", "synthetic_only": True})
    return {"train_pairs": train_pairs, "test_inputs": test_inputs, "expected_outputs": expected}


def _family_line_completion(spec: Mapping[str, Any]) -> dict[str, Any]:
    params = spec["generation_parameters"]
    rows = int(params["rows"])
    cols = int(params["cols"])
    line_color = int(params["object_color"])
    train_pairs = []
    test_inputs = []
    expected = []
    row_index = rows // 2
    for idx in range(int(spec["train_pair_count"])):
        input_grid = _grid(rows, cols, 0)
        for col in range(cols):
            if col != idx % cols:
                input_grid[row_index][col] = line_color
        output_grid = _grid(rows, cols, 0)
        for col in range(cols):
            output_grid[row_index][col] = line_color
        train_pairs.append(_make_train_pair(f"{spec['task_id']}_train_{idx}", input_grid, output_grid, "complete the broken line"))
    for idx in range(int(spec["test_input_count"])):
        input_grid = _grid(rows, cols, 0)
        for col in range(cols):
            if col != (idx + 1) % cols:
                input_grid[row_index][col] = line_color
        test_inputs.append({"test_input_id": f"test_{idx}", "input_grid": input_grid, "notes": "line completion task"})
        output_grid = _grid(rows, cols, 0)
        for col in range(cols):
            output_grid[row_index][col] = line_color
        expected.append({"test_input_id": f"test_{idx}", "output_grid": output_grid, "notes": "completed line", "synthetic_only": True})
    return {"train_pairs": train_pairs, "test_inputs": test_inputs, "expected_outputs": expected}


def _family_object_count_to_pattern(spec: Mapping[str, Any]) -> dict[str, Any]:
    params = spec["generation_parameters"]
    rows = int(params["rows"])
    cols = int(params["cols"])
    object_color = int(params["object_color"])
    pattern_color = int(params["accent_color"])
    train_pairs = []
    test_inputs = []
    expected = []
    count = 2 + int(spec["variant_index"])
    for idx in range(int(spec["train_pair_count"])):
        input_grid = _grid(rows, cols, 0)
        for obj_index in range(count):
            _set_cell(input_grid, obj_index % rows, obj_index % cols, object_color)
        output_grid = _grid(rows, cols, 0)
        for obj_index in range(count):
            _set_cell(output_grid, rows // 2, obj_index % cols, pattern_color)
        train_pairs.append(_make_train_pair(f"{spec['task_id']}_train_{idx}", input_grid, output_grid, "convert the object count into a pattern"))
    for idx in range(int(spec["test_input_count"])):
        test_count = count + idx
        input_grid = _grid(rows, cols, 0)
        for obj_index in range(test_count):
            _set_cell(input_grid, obj_index % rows, obj_index % cols, object_color)
        test_inputs.append({"test_input_id": f"test_{idx}", "input_grid": input_grid, "notes": "count to pattern task"})
        output_grid = _grid(rows, cols, 0)
        for obj_index in range(test_count):
            _set_cell(output_grid, rows // 2, obj_index % cols, pattern_color)
        expected.append({"test_input_id": f"test_{idx}", "output_grid": output_grid, "notes": "count pattern output", "synthetic_only": True})
    return {"train_pairs": train_pairs, "test_inputs": test_inputs, "expected_outputs": expected}


def _family_rotate_object_90(spec: Mapping[str, Any]) -> dict[str, Any]:
    params = spec["generation_parameters"]
    rows = int(params["rows"])
    cols = int(params["cols"])
    color = int(params["object_color"])
    train_pairs = []
    test_inputs = []
    expected = []
    shape = [[0, color, 0], [color, color, color]]
    rotated_shape = _rotate_90(shape)
    base_row = rows // 2 - 1
    base_col = cols // 2 - 1
    for idx in range(int(spec["train_pair_count"])):
        input_grid = _grid(rows, cols, 0)
        for r, row in enumerate(shape):
            for c, cell in enumerate(row):
                if cell:
                    input_grid[base_row + r][base_col + c] = color
        output_grid = _grid(rows, cols, 0)
        for r, row in enumerate(rotated_shape):
            for c, cell in enumerate(row):
                if cell:
                    output_grid[base_row + r][base_col + c] = color
        train_pairs.append(_make_train_pair(f"{spec['task_id']}_train_{idx}", input_grid, output_grid, "rotate the object by 90 degrees"))
    for idx in range(int(spec["test_input_count"])):
        input_grid = _grid(rows, cols, 0)
        for r, row in enumerate(shape):
            for c, cell in enumerate(row):
                if cell:
                    input_grid[base_row + r][base_col + c] = color
        test_inputs.append({"test_input_id": f"test_{idx}", "input_grid": input_grid, "notes": "rotation task"})
        output_grid = _grid(rows, cols, 0)
        for r, row in enumerate(rotated_shape):
            for c, cell in enumerate(row):
                if cell:
                    output_grid[base_row + r][base_col + c] = color
        expected.append({"test_input_id": f"test_{idx}", "output_grid": output_grid, "notes": "rotated output", "synthetic_only": True})
    return {"train_pairs": train_pairs, "test_inputs": test_inputs, "expected_outputs": expected}


def _family_reflect_object(spec: Mapping[str, Any]) -> dict[str, Any]:
    params = spec["generation_parameters"]
    rows = int(params["rows"])
    cols = int(params["cols"])
    color = int(params["object_color"])
    axis = FAMILY_AXIS_BY_VARIANT_V1[int(spec["variant_index"])]
    train_pairs = []
    test_inputs = []
    expected = []
    input_shape = [[0, color, 0], [0, color, color]]
    reflected_shape = _reflect_horizontal(input_shape) if axis == "horizontal" else _reflect_vertical(input_shape)
    base_row = rows // 2 - 1
    base_col = cols // 2 - 1
    for idx in range(int(spec["train_pair_count"])):
        input_grid = _grid(rows, cols, 0)
        for r, row in enumerate(input_shape):
            for c, cell in enumerate(row):
                if cell:
                    input_grid[base_row + r][base_col + c] = color
        output_grid = _grid(rows, cols, 0)
        for r, row in enumerate(reflected_shape):
            for c, cell in enumerate(row):
                if cell:
                    output_grid[base_row + r][base_col + c] = color
        train_pairs.append(_make_train_pair(f"{spec['task_id']}_train_{idx}", input_grid, output_grid, f"reflect the object {axis}"))
    for idx in range(int(spec["test_input_count"])):
        input_grid = _grid(rows, cols, 0)
        for r, row in enumerate(input_shape):
            for c, cell in enumerate(row):
                if cell:
                    input_grid[base_row + r][base_col + c] = color
        test_inputs.append({"test_input_id": f"test_{idx}", "input_grid": input_grid, "notes": f"reflect {axis} task"})
        output_grid = _grid(rows, cols, 0)
        for r, row in enumerate(reflected_shape):
            for c, cell in enumerate(row):
                if cell:
                    output_grid[base_row + r][base_col + c] = color
        expected.append({"test_input_id": f"test_{idx}", "output_grid": output_grid, "notes": f"reflected {axis} output", "synthetic_only": True})
    return {"train_pairs": train_pairs, "test_inputs": test_inputs, "expected_outputs": expected}


_FAMILY_BUILDERS: dict[str, Callable[[Mapping[str, Any]], dict[str, Any]]] = {
    "copy_grid": _family_copy_grid,
    "recolor_symbol": _family_recolor_symbol,
    "move_single_object": _family_move_single_object,
    "fill_region": _family_fill_region,
    "complete_symmetry": _family_complete_symmetry,
    "border_frame": _family_border_frame,
    "extract_largest_object": _family_extract_largest_object,
    "remove_background_noise": _family_remove_background_noise,
    "line_completion": _family_line_completion,
    "object_count_to_pattern": _family_object_count_to_pattern,
    "rotate_object_90": _family_rotate_object_90,
    "reflect_object_horizontal_or_vertical": _family_reflect_object,
}


def _build_arc_style_packets_for_task(
    *,
    task_id: str,
    train_pairs: Sequence[Mapping[str, Any]],
    test_inputs: Sequence[Mapping[str, Any]],
    family_id: str,
    variant_index: int,
) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    for test_input in test_inputs:
        packet = build_arc_style_grid_task_packet_v1(
            task_id=task_id,
            task_source=SYNTHETIC_ONLY_TASK_SOURCE_V1,
            train_pairs=train_pairs,
            test_input=test_input["input_grid"],
            candidate_outputs=[],
            validation_results=[],
            failure_notes=[],
            trace={
                "toy_task": True,
                "internal_synthetic_only": True,
                "toy_task_type": family_id,
                "synthetic_generator_family_id": family_id,
                "synthetic_generator_variant_index": variant_index,
                "synthetic_expected_output_hidden": True,
            },
        )
        packets.append(packet)
    return packets


def _candidate_like_from_expected_output(task_id: str, test_input_id: str, output_grid: Sequence[Sequence[int]], rank: int, label: str) -> dict[str, Any]:
    return build_arc_agi2_attempt_v1(
        attempt_id=f"{task_id}:{test_input_id}:candidate_{rank}",
        grid=output_grid,
        source_candidate_id=f"{task_id}:{test_input_id}:candidate_{rank}",
        rank=rank,
        confidence_label=label,
        evidence_labels=["synthetic_expected_output", label],
        leakage_flags={
            "synthetic_only": True,
            "uses_kaggle_data": False,
            "uses_arc_public_data": False,
            "uses_hidden_private_data": False,
            "uses_solution_file": False,
            "uses_answer_key": False,
            "uses_test_output_for_candidate_generation": False,
        },
        metadata={"synthetic_only": True, "source_kind": "synthetic_expected_output"},
    )


def _check_top2_contract_compatibility(task_id: str, validation_metadata: Mapping[str, Any]) -> dict[str, Any]:
    checked_test_input_ids: list[str] = []
    for expected_output in validation_metadata.get("expected_outputs", []):
        test_input_id = _safe_text(expected_output.get("test_input_id"))
        output_grid = expected_output.get("output_grid")
        if not test_input_id:
            continue
        checked_test_input_ids.append(test_input_id)
        primary = _candidate_like_from_expected_output(task_id, test_input_id, output_grid, 1, "high")
        distractor_grid = _clone_grid(output_grid)
        if distractor_grid and distractor_grid[0]:
            distractor_grid[0][0] = (distractor_grid[0][0] + 1) if isinstance(distractor_grid[0][0], int) else 9
        secondary = _candidate_like_from_expected_output(task_id, test_input_id, distractor_grid, 2, "medium")
        packet = build_arc_agi2_top2_attempt_packet_v1(
            task_id=task_id,
            test_input_index=len(checked_test_input_ids) - 1,
            candidate_packets=[primary, secondary],
        )
        validation = validate_arc_agi2_top2_attempt_packet_v1(packet)
        if not validation["valid"]:
            raise ValueError(f"top2 contract compatibility failed for {task_id}:{test_input_id}: {validation['blocked_reason_labels']}")
    return {
        "top2_contract_compatibility_checked": True,
        "checked_test_input_ids": checked_test_input_ids,
    }


def generate_arc_style_synthetic_task_family_v1(spec: Mapping[str, Any]) -> dict[str, Any]:
    spec_validation = validate_arc_style_synthetic_generator_spec_v1(spec)
    if not spec_validation["valid"]:
        raise ValueError(f"invalid generator spec: {spec_validation['blocked_reason_labels']}")

    builder = _FAMILY_BUILDERS[_safe_text(spec["family_id"])]
    generated = builder(spec)
    train_pairs = generated["train_pairs"]
    test_inputs = generated["test_inputs"]
    expected_outputs = generated["expected_outputs"]

    validation_metadata = {
        "synthetic_only": True,
        "expected_outputs": expected_outputs,
        "expected_output_count": len(expected_outputs),
        "task_source": SYNTHETIC_ONLY_TASK_SOURCE_V1,
    }
    compatibility = _check_top2_contract_compatibility(_safe_text(spec["task_id"]), validation_metadata)

    arc_style_task_packets = _build_arc_style_packets_for_task(
        task_id=_safe_text(spec["task_id"]),
        train_pairs=train_pairs,
        test_inputs=test_inputs,
        family_id=_safe_text(spec["family_id"]),
        variant_index=int(spec["variant_index"]),
    )

    generator_metadata = {
        "spec_id": _safe_text(spec["spec_id"]),
        "suite_id": SUITE_ID_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "task_source": SYNTHETIC_ONLY_TASK_SOURCE_V1,
        "arc_style_task_packets": arc_style_task_packets,
        "arc_style_task_packet_validations": [validate_arc_style_grid_task_packet_v1(packet) for packet in arc_style_task_packets],
        "arc_style_task_packet_summaries": [summarize_arc_style_grid_task_packet_v1(packet) for packet in arc_style_task_packets],
        "top2_contract_compatibility_checked": compatibility["top2_contract_compatibility_checked"],
        "top2_contract_checked_test_input_ids": compatibility["checked_test_input_ids"],
        "generator_parameters": _json_safe(dict(spec["generation_parameters"])),
        "variant_index": int(spec["variant_index"]),
        "family_id": _safe_text(spec["family_id"]),
    }

    task_family = {
        "task_id": _safe_text(spec["task_id"]),
        "family_id": _safe_text(spec["family_id"]),
        "variant_index": int(spec["variant_index"]),
        "train_pairs": [_json_safe(pair) for pair in train_pairs],
        "test_inputs": [_json_safe(test_input) for test_input in test_inputs],
        "validation_metadata": _json_safe(validation_metadata),
        "generator_metadata": _json_safe(generator_metadata),
        "transformation_labels": [_safe_text(label) for label in spec["transformation_labels"]],
        "difficulty_label": _safe_text(spec["difficulty_label"]),
        "leakage_flags": _normalize_leakage_flags(spec.get("leakage_flags")),
    }
    return task_family


def validate_arc_style_synthetic_task_family_v1(task_family: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "task_id": None,
        "family_id": None,
        "blocked_reason_labels": [],
        "train_pair_validation_count": 0,
        "test_input_validation_count": 0,
        "expected_output_validation_count": 0,
    }
    if not isinstance(task_family, Mapping):
        result["blocked_reason_labels"].append("task_family_not_mapping")
        return result
    missing = [field for field in REQUIRED_TASK_FAMILY_FIELDS_V1 if field not in task_family]
    if missing:
        result["blocked_reason_labels"].append("missing_required_fields")
        result["blocked_reason_labels"].extend(f"missing:{field}" for field in missing)
        return result

    result["task_id"] = _safe_text(task_family.get("task_id"))
    result["family_id"] = _safe_text(task_family.get("family_id"))
    if not result["task_id"]:
        result["blocked_reason_labels"].append("empty_task_id")
    if result["family_id"] not in REQUIRED_FAMILIES_V1:
        result["blocked_reason_labels"].append("family_id_not_supported")

    train_pairs = task_family.get("train_pairs")
    if not isinstance(train_pairs, list) or not train_pairs:
        result["blocked_reason_labels"].append("train_pairs_invalid")
        train_pairs = []
    for train_pair in train_pairs:
        pair_validation = validate_arc_style_grid_train_pair_v1(train_pair)
        result["train_pair_validation_count"] += 1
        if not pair_validation["valid"]:
            result["blocked_reason_labels"].append(f"train_pair_invalid:{pair_validation.get('pair_id')}")
            result["blocked_reason_labels"].extend(pair_validation["blocked_reason_labels"])

    test_inputs = task_family.get("test_inputs")
    if not isinstance(test_inputs, list) or not test_inputs:
        result["blocked_reason_labels"].append("test_inputs_invalid")
        test_inputs = []
    for test_input in test_inputs:
        if not isinstance(test_input, Mapping):
            result["blocked_reason_labels"].append("test_input_not_mapping")
            continue
        test_validation = build_arc_style_grid_metadata_v1(test_input.get("input_grid"))
        result["test_input_validation_count"] += 1
        if not test_validation["trace"]["rectangular"] or test_validation["invalid_cells"]:
            result["blocked_reason_labels"].append("invalid_test_input_grid")
        if _safe_text(test_input.get("test_input_id")) == "":
            result["blocked_reason_labels"].append("empty_test_input_id")

    validation_metadata = task_family.get("validation_metadata")
    if not isinstance(validation_metadata, Mapping):
        result["blocked_reason_labels"].append("validation_metadata_not_mapping")
        validation_metadata = {}
    if not bool(validation_metadata.get("synthetic_only", False)):
        result["blocked_reason_labels"].append("validation_metadata_not_synthetic_only")

    expected_outputs = validation_metadata.get("expected_outputs")
    if not isinstance(expected_outputs, list) or len(expected_outputs) != len(test_inputs):
        result["blocked_reason_labels"].append("expected_outputs_count_mismatch")
        expected_outputs = []
    for expected_output in expected_outputs:
        if not isinstance(expected_output, Mapping):
            result["blocked_reason_labels"].append("expected_output_not_mapping")
            continue
        output_validation = build_arc_style_grid_metadata_v1(expected_output.get("output_grid"))
        result["expected_output_validation_count"] += 1
        if not output_validation["trace"]["rectangular"] or output_validation["invalid_cells"]:
            result["blocked_reason_labels"].append("invalid_expected_output_grid")
        if not bool(expected_output.get("synthetic_only", False)):
            result["blocked_reason_labels"].append("expected_output_not_synthetic_only")

    leakage = _normalize_leakage_flags(task_family.get("leakage_flags"))
    if not _leakage_flags_are_clean(leakage):
        result["blocked_reason_labels"].append("leakage_flags_not_clean")

    generator_metadata = task_family.get("generator_metadata")
    if not isinstance(generator_metadata, Mapping):
        result["blocked_reason_labels"].append("generator_metadata_not_mapping")
    else:
        arc_style_task_packets = generator_metadata.get("arc_style_task_packets")
        if not isinstance(arc_style_task_packets, list):
            result["blocked_reason_labels"].append("arc_style_task_packets_not_list")
        elif len(arc_style_task_packets) != len(test_inputs):
            result["blocked_reason_labels"].append("arc_style_task_packets_count_mismatch")
        else:
            for packet in arc_style_task_packets:
                packet_validation = validate_arc_style_grid_task_packet_v1(packet)
                if not packet_validation["valid"]:
                    result["blocked_reason_labels"].append(f"arc_style_task_packet_invalid:{packet_validation.get('task_id')}")
                    result["blocked_reason_labels"].extend(packet_validation["blocked_reason_labels"])
        if not bool(generator_metadata.get("top2_contract_compatibility_checked", False)):
            result["blocked_reason_labels"].append("top2_contract_compatibility_not_checked")

    result["valid"] = not result["blocked_reason_labels"]
    return result


def generate_arc_style_synthetic_task_suite_v1(
    generator_specs: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    specs = [
        _json_safe(spec)
        for spec in (generator_specs if generator_specs is not None else build_initial_arc_style_synthetic_generator_specs_v1())
    ]
    tasks = [generate_arc_style_synthetic_task_family_v1(spec) for spec in specs]
    suite = {
        "suite_id": SUITE_ID_V1,
        "generator_specs": specs,
        "tasks": tasks,
        "top2_contract_compatibility_checked": all(bool(task.get("generator_metadata", {}).get("top2_contract_compatibility_checked", False)) for task in tasks),
        "generator_metadata": {
            "schema_version": SCHEMA_VERSION_V1,
            "synthetic_only": True,
            "task_family_count": len(tasks),
            "family_ids": [task.get("family_id") for task in tasks],
            "top2_contract_compatibility_checked": all(bool(task.get("generator_metadata", {}).get("top2_contract_compatibility_checked", False)) for task in tasks),
        },
    }
    return suite


def validate_arc_style_synthetic_task_suite_v1(suite: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "suite_id": None,
        "blocked_reason_labels": [],
        "task_validation_count": 0,
    }
    if not isinstance(suite, Mapping):
        result["blocked_reason_labels"].append("suite_not_mapping")
        return result
    missing = [field for field in REQUIRED_SUITE_FIELDS_V1 if field not in suite]
    if missing:
        result["blocked_reason_labels"].append("missing_required_fields")
        result["blocked_reason_labels"].extend(f"missing:{field}" for field in missing)
        return result
    result["suite_id"] = _safe_text(suite.get("suite_id"))
    if result["suite_id"] != SUITE_ID_V1:
        result["blocked_reason_labels"].append("suite_id_mismatch")

    generator_specs = suite.get("generator_specs")
    if not isinstance(generator_specs, list):
        result["blocked_reason_labels"].append("generator_specs_not_list")
        generator_specs = []
    tasks = suite.get("tasks")
    if not isinstance(tasks, list):
        result["blocked_reason_labels"].append("tasks_not_list")
        tasks = []
    if len(tasks) < 36:
        result["blocked_reason_labels"].append("task_count_below_minimum")

    observed_families: list[str] = []
    for spec in generator_specs:
        spec_validation = validate_arc_style_synthetic_generator_spec_v1(spec)
        if not spec_validation["valid"]:
            result["blocked_reason_labels"].append(f"generator_spec_invalid:{spec_validation.get('spec_id')}")
            result["blocked_reason_labels"].extend(spec_validation["blocked_reason_labels"])

    for task in tasks:
        task_validation = validate_arc_style_synthetic_task_family_v1(task)
        result["task_validation_count"] += 1
        if not task_validation["valid"]:
            result["blocked_reason_labels"].append(f"task_invalid:{task_validation.get('task_id')}")
            result["blocked_reason_labels"].extend(task_validation["blocked_reason_labels"])
        else:
            observed_families.append(_safe_text(task.get("family_id")))

    required_families_missing = [family for family in REQUIRED_FAMILIES_V1 if family not in observed_families]
    if required_families_missing:
        result["blocked_reason_labels"].append("missing_required_families")
        result["blocked_reason_labels"].extend(f"missing_family:{family}" for family in required_families_missing)

    if not bool(suite.get("top2_contract_compatibility_checked", False)):
        result["blocked_reason_labels"].append("top2_contract_compatibility_not_checked")

    if not isinstance(suite.get("generator_metadata"), Mapping):
        result["blocked_reason_labels"].append("generator_metadata_not_mapping")
    elif not bool(suite.get("generator_metadata", {}).get("synthetic_only", False)):
        result["blocked_reason_labels"].append("suite_generator_metadata_not_synthetic_only")

    result["valid"] = not result["blocked_reason_labels"]
    return result


def summarize_arc_style_synthetic_task_suite_v1(suite: Any) -> dict[str, Any]:
    validation = validate_arc_style_synthetic_task_suite_v1(suite)
    if not isinstance(suite, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "suite_id": None,
            "valid": False,
            "family_count": 0,
            "task_count": 0,
            "train_pair_count": 0,
            "test_input_count": 0,
            "difficulty_labels": [],
            "transformation_labels": [],
            "families": [],
            "leakage_clean": False,
            "top2_contract_compatibility_checked": False,
            "blocked_reason_labels": validation["blocked_reason_labels"],
        }

    tasks = suite.get("tasks", []) if isinstance(suite.get("tasks"), list) else []
    family_ids: list[str] = []
    difficulty_labels: list[str] = []
    transformation_labels: list[str] = []
    train_pair_count = 0
    test_input_count = 0
    leakage_clean = True
    top2_checked = True
    for task in tasks:
        if not isinstance(task, Mapping):
            continue
        family_id = _safe_text(task.get("family_id"))
        if family_id and family_id not in family_ids:
            family_ids.append(family_id)
        difficulty_label = _safe_text(task.get("difficulty_label"))
        if difficulty_label and difficulty_label not in difficulty_labels:
            difficulty_labels.append(difficulty_label)
        for label in task.get("transformation_labels", []) if isinstance(task.get("transformation_labels"), list) else []:
            label_text = _safe_text(label)
            if label_text and label_text not in transformation_labels:
                transformation_labels.append(label_text)
        train_pair_count += len(task.get("train_pairs", [])) if isinstance(task.get("train_pairs"), list) else 0
        test_input_count += len(task.get("test_inputs", [])) if isinstance(task.get("test_inputs"), list) else 0
        leakage_clean = leakage_clean and _leakage_flags_are_clean(task.get("leakage_flags", {}))
        top2_checked = top2_checked and bool(task.get("generator_metadata", {}).get("top2_contract_compatibility_checked", False))

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "suite_id": _safe_text(suite.get("suite_id")),
        "valid": validation["valid"],
        "family_count": len(family_ids),
        "task_count": len(tasks),
        "train_pair_count": train_pair_count,
        "test_input_count": test_input_count,
        "difficulty_labels": difficulty_labels,
        "transformation_labels": transformation_labels,
        "families": family_ids,
        "leakage_clean": leakage_clean,
        "top2_contract_compatibility_checked": top2_checked,
        "blocked_reason_labels": validation["blocked_reason_labels"],
    }



__all__ = [
    "SCHEMA_VERSION_V1",
    "SUITE_ID_V1",
    "SYNTHETIC_ONLY_TASK_SOURCE_V1",
    "REQUIRED_FAMILIES_V1",
    "build_arc_style_synthetic_generator_spec_v1",
    "build_initial_arc_style_synthetic_generator_specs_v1",
    "generate_arc_style_synthetic_task_family_v1",
    "generate_arc_style_synthetic_task_suite_v1",
    "summarize_arc_style_synthetic_task_suite_v1",
    "to_arc_style_synthetic_task_suite_json_safe_v1",
    "validate_arc_style_synthetic_generator_spec_v1",
    "validate_arc_style_synthetic_task_family_v1",
    "validate_arc_style_synthetic_task_suite_v1",
]
