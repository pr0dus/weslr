"""WESLR ARC-style held-out compositional synthetic generator V1.

Synthetic-only held-out task generation for depth-2/3 primitive compositions.
This module stays separate from the known-family regression suite and does not
implement program search, held-out evaluation execution, public ARC/Kaggle
ingestion, score claims, provider/model APIs, ChatResponder wiring, website/
runtime wiring, or `.weslr` writes.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from typing import Any, Mapping, Sequence

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
from weslr.arc_style_typed_primitive_signatures import (
    EXPECTED_PRIMITIVE_NAMES_V1,
    get_arc_style_typed_primitive_signature_v1,
    validate_arc_style_typed_primitive_signature_v1,
)

SCHEMA_VERSION_V1 = "ArcStyleHeldoutCompositionalSyntheticGeneratorV1"
SUITE_ID_V1 = "arc_style_heldout_compositional_synthetic_suite_v1"
TASK_SOURCE_INTERNAL_HELDOUT_COMPOSITIONAL_V1 = "internal_synthetic_heldout_compositional_v1"
DEFAULT_HELDOUT_SEED_V1 = 20260625
RECIPE_VARIANTS_PER_FAMILY_V1 = 2

HELDOUT_RECIPE_FAMILIES_V1 = (
    "extract_object_then_recolor",
    "move_then_border",
    "rotate_then_recolor",
    "remove_noise_then_complete_line",
    "count_object_then_emit_pattern",
    "reflect_then_recolor",
    "fill_region_then_extract_object",
)

RECIPE_DEFINITIONS_V1 = {
    "extract_object_then_recolor": {
        "depth": 2,
        "primitive_sequence": ("extract_largest_object", "recolor_symbol"),
        "transformation_labels": ("extract", "recolor", "heldout_composition"),
    },
    "move_then_border": {
        "depth": 2,
        "primitive_sequence": ("move_single_object", "border_frame"),
        "transformation_labels": ("move", "border", "heldout_composition"),
    },
    "rotate_then_recolor": {
        "depth": 2,
        "primitive_sequence": ("rotate_object_90", "recolor_symbol"),
        "transformation_labels": ("rotate", "recolor", "heldout_composition"),
    },
    "remove_noise_then_complete_line": {
        "depth": 2,
        "primitive_sequence": ("remove_background_noise", "line_completion"),
        "transformation_labels": ("denoise", "line_completion", "heldout_composition"),
    },
    "count_object_then_emit_pattern": {
        "depth": 2,
        "primitive_sequence": ("remove_background_noise", "object_count_to_pattern"),
        "transformation_labels": ("count", "pattern", "heldout_composition"),
    },
    "reflect_then_recolor": {
        "depth": 2,
        "primitive_sequence": ("reflect_object_horizontal_or_vertical", "recolor_symbol"),
        "transformation_labels": ("reflect", "recolor", "heldout_composition"),
    },
    "fill_region_then_extract_object": {
        "depth": 2,
        "primitive_sequence": ("fill_region", "extract_largest_object"),
        "transformation_labels": ("fill", "extract", "heldout_composition"),
    },
}

REQUIRED_RECIPE_FIELDS_V1 = (
    "recipe_id",
    "recipe_family_id",
    "variant_index",
    "task_id",
    "seed",
    "depth",
    "primitive_sequence",
    "train_pair_count",
    "test_input_count",
    "generation_parameters",
    "leakage_flags",
    "provenance_metadata",
    "boundary_flags",
)

REQUIRED_TASK_FIELDS_V1 = (
    "recipe_id",
    "recipe_family_id",
    "task_id",
    "variant_index",
    "seed",
    "depth",
    "primitive_sequence",
    "task_packet",
    "evaluation_metadata",
    "provenance_metadata",
    "leakage_flags",
    "boundary_flags",
)

REQUIRED_SUITE_FIELDS_V1 = (
    "suite_id",
    "recipe_specs",
    "tasks",
    "generator_metadata",
    "boundary_flags",
)

REQUIRED_LEAKAGE_FLAG_NAMES_V1 = (
    "synthetic_only",
    "heldout_compositional",
    "uses_public_arc_data",
    "uses_kaggle_data",
    "uses_solution_file",
    "uses_answer_key",
    "uses_test_output_for_candidate_generation",
    "uses_task_id_shortcut",
    "uses_notes_shortcut",
    "uses_provider_model_api",
)

REQUIRED_BOUNDARY_FLAG_NAMES_V1 = (
    "metadata_only",
    "heldout_compositional",
    "no_public_arc_data",
    "no_kaggle_data",
    "no_solution_file",
    "no_answer_key",
    "no_test_output_access_for_solver",
    "no_task_id_shortcut",
    "no_notes_shortcut",
    "no_provider_model_api",
    "no_chat_responder",
    "no_runtime_wiring",
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


def to_arc_style_heldout_compositional_suite_json_safe_v1(value: Any) -> Any:
    safe = _json_safe(value)
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def _grid(rows: int, cols: int, fill: int = 0) -> list[list[int]]:
    return [[fill for _ in range(cols)] for _ in range(rows)]


def _clone_grid(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _set_cell(grid: list[list[int]], row: int, col: int, value: int) -> None:
    grid[row][col] = value


def _set_rect(grid: list[list[int]], top: int, left: int, bottom: int, right: int, value: int) -> None:
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            grid[row][col] = value


def _neighbors(row: int, col: int) -> list[tuple[int, int]]:
    return [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]


def _connected_components(grid: Sequence[Sequence[int]], background_value: int = 0) -> list[list[tuple[int, int]]]:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(rows):
        for col in range(cols):
            if (row, col) in seen:
                continue
            if grid[row][col] == background_value:
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
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] == background_value:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            components.append(component)
    components.sort(key=lambda cells: (-len(cells), min(cells)))
    return components


def _extract_largest_object(grid: Sequence[Sequence[int]], background_value: int = 0) -> list[list[int]]:
    output = _grid(len(grid), len(grid[0]) if grid else 0, background_value)
    components = _connected_components(grid, background_value=background_value)
    if not components:
        return output
    component = components[0]
    color = grid[component[0][0]][component[0][1]]
    for row, col in component:
        output[row][col] = color
    return output


def _recolor_symbol(grid: Sequence[Sequence[int]], from_value: int, to_value: int) -> list[list[int]]:
    output = _clone_grid(grid)
    for row, row_values in enumerate(output):
        for col, value in enumerate(row_values):
            if value == from_value:
                output[row][col] = to_value
    return output


def _move_single_object(
    grid: Sequence[Sequence[int]],
    *,
    object_value: int,
    background_value: int,
    direction: str,
    steps: int,
) -> list[list[int]]:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    delta_by_direction = {
        "up": (-steps, 0),
        "down": (steps, 0),
        "left": (0, -steps),
        "right": (0, steps),
        "up_left": (-steps, -steps),
        "up_right": (-steps, steps),
        "down_left": (steps, -steps),
        "down_right": (steps, steps),
    }
    if direction not in delta_by_direction:
        return _clone_grid(grid)
    delta_row, delta_col = delta_by_direction[direction]
    object_cells = [(row, col) for row in range(rows) for col in range(cols) if grid[row][col] == object_value]
    output = _grid(rows, cols, background_value)
    for row, col in object_cells:
        new_row = row + delta_row
        new_col = col + delta_col
        if 0 <= new_row < rows and 0 <= new_col < cols:
            output[new_row][new_col] = object_value
    return output


def _add_border_frame(grid: Sequence[Sequence[int]], frame_value: int) -> list[list[int]]:
    output = _clone_grid(grid)
    rows = len(output)
    cols = len(output[0]) if rows else 0
    if not rows or not cols:
        return output
    for col in range(cols):
        output[0][col] = frame_value
        output[rows - 1][col] = frame_value
    for row in range(rows):
        output[row][0] = frame_value
        output[row][cols - 1] = frame_value
    return output


def _rotate_90(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(reversed(col)) for col in zip(*grid)]


def _reflect_grid(grid: Sequence[Sequence[int]], axis: str) -> list[list[int]]:
    if axis == "horizontal":
        return [list(reversed(row)) for row in grid]
    if axis == "vertical":
        return [list(row) for row in reversed(grid)]
    return _clone_grid(grid)


def _reflect_object_in_bbox(grid: Sequence[Sequence[int]], axis: str) -> list[list[int]]:
    object_cells = [(row, col) for row, row_values in enumerate(grid) for col, value in enumerate(row_values) if value != 0]
    if not object_cells:
        return _clone_grid(grid)
    top = min(row for row, _ in object_cells)
    left = min(col for _, col in object_cells)
    bottom = max(row for row, _ in object_cells)
    right = max(col for _, col in object_cells)
    output = _grid(len(grid), len(grid[0]) if grid else 0, 0)
    for row, col in object_cells:
        value = grid[row][col]
        if axis == "horizontal":
            new_row = row
            new_col = right - (col - left)
        else:
            new_row = bottom - (row - top)
            new_col = col
        output[new_row][new_col] = value
    return output


def _remove_background_noise(grid: Sequence[Sequence[int]], background_value: int = 0) -> list[list[int]]:
    output = _clone_grid(grid)
    for component in _connected_components(grid, background_value=background_value):
        if len(component) <= 1:
            for row, col in component:
                output[row][col] = background_value
    return output


def _complete_line(grid: Sequence[Sequence[int]], *, axis: str, line_index: int, line_value: int, background_value: int = 0) -> list[list[int]]:
    output = _clone_grid(grid)
    rows = len(output)
    cols = len(output[0]) if rows else 0
    if axis == "horizontal" and 0 <= line_index < rows:
        active_cols = [col for col in range(cols) if output[line_index][col] == line_value]
        if active_cols:
            for col in range(min(active_cols), max(active_cols) + 1):
                output[line_index][col] = line_value
    elif axis == "vertical" and 0 <= line_index < cols:
        active_rows = [row for row in range(rows) if output[row][line_index] == line_value]
        if active_rows:
            for row in range(min(active_rows), max(active_rows) + 1):
                output[row][line_index] = line_value
    return output


def _count_objects(grid: Sequence[Sequence[int]], background_value: int = 0) -> int:
    return len(_connected_components(grid, background_value=background_value))


def _emit_count_pattern(count: int, pattern_value: int, background_value: int = 0) -> list[list[int]]:
    width = max(1, int(count))
    return [[pattern_value for _ in range(width)]]


def _fill_region(grid: Sequence[Sequence[int]], *, fill_value: int, background_value: int = 0) -> list[list[int]]:
    output = _clone_grid(grid)
    rows = len(output)
    cols = len(output[0]) if rows else 0
    if rows < 3 or cols < 3:
        return output
    top = None
    left = None
    bottom = None
    right = None
    for row in range(rows):
        for col in range(cols):
            if output[row][col] != background_value:
                top = row if top is None else min(top, row)
                left = col if left is None else min(left, col)
                bottom = row if bottom is None else max(bottom, row)
                right = col if right is None else max(right, col)
    if top is None or left is None or bottom is None or right is None:
        return output
    if bottom - top < 2 or right - left < 2:
        return output
    for row in range(top + 1, bottom):
        for col in range(left + 1, right):
            output[row][col] = fill_value
    return output


def _safe_flag_mapping(names: tuple[str, ...], *, true_names: Sequence[str]) -> dict[str, bool]:
    true_set = set(true_names)
    return {name: (name in true_set) for name in names}


def _normalize_leakage_flags(value: Any) -> dict[str, bool]:
    mapping = value if isinstance(value, Mapping) else {}
    return {name: bool(mapping.get(name, False)) for name in REQUIRED_LEAKAGE_FLAG_NAMES_V1}


def _normalize_boundary_flags(value: Any) -> dict[str, bool]:
    mapping = value if isinstance(value, Mapping) else {}
    return {name: bool(mapping.get(name, False)) for name in REQUIRED_BOUNDARY_FLAG_NAMES_V1}


def _leakage_flags_are_clean(flags: Mapping[str, Any]) -> bool:
    return bool(flags.get("synthetic_only", False)) and all(
        not bool(flags.get(name, False))
        for name in REQUIRED_LEAKAGE_FLAG_NAMES_V1
        if name != "synthetic_only"
    )


def _boundary_flags_are_clean(flags: Mapping[str, Any]) -> bool:
    return all(bool(flags.get(name, False)) for name in REQUIRED_BOUNDARY_FLAG_NAMES_V1)


def _base_generation_parameters(recipe_family_id: str, variant_index: int, seed: int) -> dict[str, Any]:
    rows = 5 + variant_index
    cols = 5 + ((variant_index + len(recipe_family_id)) % 2)
    base_color = 1 + ((seed + variant_index) % 8)
    accent_color = 1 + ((seed + variant_index + 3) % 8)
    secondary_color = 1 + ((seed + variant_index + 5) % 8)
    pattern_color = 1 + ((seed + variant_index + 7) % 8)
    return {
        "rows": rows,
        "cols": cols,
        "background_color": 0,
        "base_color": base_color,
        "accent_color": accent_color,
        "secondary_color": secondary_color,
        "pattern_color": pattern_color,
        "seed": seed,
        "variant_index": variant_index,
        "recipe_family_id": recipe_family_id,
    }


def _recipe_seed(recipe_family_id: str, variant_index: int, seed: int | None = None) -> int:
    base = DEFAULT_HELDOUT_SEED_V1 if seed is None else int(seed)
    family_offset = HELDOUT_RECIPE_FAMILIES_V1.index(recipe_family_id) * 17 if recipe_family_id in HELDOUT_RECIPE_FAMILIES_V1 else 0
    return base + family_offset + variant_index


def _primitive_sequence_is_supported(sequence: Sequence[Any]) -> bool:
    for primitive_name in sequence:
        if _safe_text(primitive_name) not in EXPECTED_PRIMITIVE_NAMES_V1:
            return False
        if not validate_arc_style_typed_primitive_signature_v1(get_arc_style_typed_primitive_signature_v1(_safe_text(primitive_name))).get("valid", False):
            return False
    return True


def build_arc_style_heldout_composition_recipe_v1(
    *,
    recipe_family_id: str,
    variant_index: int,
    task_id: str,
    seed: int,
    depth: int,
    primitive_sequence: Sequence[Any],
    train_pair_count: int,
    test_input_count: int,
    generation_parameters: Mapping[str, Any],
    leakage_flags: Mapping[str, Any] | None = None,
    provenance_metadata: Mapping[str, Any] | None = None,
    boundary_flags: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    recipe_id = f"{recipe_family_id}_variant_{variant_index}_v1"
    return {
        "recipe_id": recipe_id,
        "recipe_family_id": _safe_text(recipe_family_id),
        "variant_index": int(variant_index),
        "task_id": _safe_text(task_id),
        "seed": int(seed),
        "depth": int(depth),
        "primitive_sequence": [_safe_text(item) for item in primitive_sequence],
        "train_pair_count": int(train_pair_count),
        "test_input_count": int(test_input_count),
        "generation_parameters": _json_safe(dict(generation_parameters)),
        "leakage_flags": _normalize_leakage_flags(leakage_flags or {}),
        "provenance_metadata": _json_safe(
            dict(
                provenance_metadata
                or {
                    "source": "internal_synthetic_heldout_compositional_v1",
                    "heldout_compositional": True,
                    "synthetic_only": True,
                }
            )
        ),
        "boundary_flags": _normalize_boundary_flags(
            boundary_flags
            or {
                "metadata_only": True,
                "heldout_compositional": True,
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
            }
        ),
    }


def _recipe_validation_common(recipe: Mapping[str, Any]) -> list[str]:
    blocked: list[str] = []
    missing = [field for field in REQUIRED_RECIPE_FIELDS_V1 if field not in recipe]
    if missing:
        blocked.append("missing_required_fields")
        blocked.extend(f"missing:{field}" for field in missing)
        return blocked
    if _safe_text(recipe.get("recipe_family_id")) not in HELDOUT_RECIPE_FAMILIES_V1:
        blocked.append("recipe_family_id_not_supported")
    if _safe_text(recipe.get("recipe_id")) == "":
        blocked.append("empty_recipe_id")
    if not isinstance(recipe.get("variant_index"), int) or recipe.get("variant_index") not in (0, 1):
        blocked.append("variant_index_invalid")
    if not isinstance(recipe.get("seed"), int):
        blocked.append("seed_not_int")
    if not isinstance(recipe.get("depth"), int) or recipe.get("depth") not in (2, 3):
        blocked.append("depth_invalid")
    if not isinstance(recipe.get("primitive_sequence"), list) or len(recipe.get("primitive_sequence")) not in (2, 3):
        blocked.append("primitive_sequence_invalid")
    elif not _primitive_sequence_is_supported(recipe.get("primitive_sequence", [])):
        blocked.append("primitive_sequence_unsupported")
    if not isinstance(recipe.get("generation_parameters"), Mapping):
        blocked.append("generation_parameters_not_mapping")
    if not isinstance(recipe.get("provenance_metadata"), Mapping):
        blocked.append("provenance_metadata_not_mapping")
    if not isinstance(recipe.get("boundary_flags"), Mapping):
        blocked.append("boundary_flags_not_mapping")
    if not isinstance(recipe.get("leakage_flags"), Mapping):
        blocked.append("leakage_flags_not_mapping")
    else:
        leakage_flags = _normalize_leakage_flags(recipe.get("leakage_flags"))
        if not _leakage_flags_are_clean(leakage_flags):
            blocked.append("leakage_flags_not_clean")
    if not isinstance(recipe.get("boundary_flags"), Mapping) or not _boundary_flags_are_clean(_normalize_boundary_flags(recipe.get("boundary_flags"))):
        blocked.append("boundary_flags_not_clean")
    if not isinstance(recipe.get("train_pair_count"), int) or recipe.get("train_pair_count") < 1:
        blocked.append("train_pair_count_invalid")
    if not isinstance(recipe.get("test_input_count"), int) or recipe.get("test_input_count") < 1:
        blocked.append("test_input_count_invalid")
    return blocked


def validate_arc_style_heldout_composition_recipe_v1(recipe: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "recipe_id": None,
        "recipe_family_id": None,
        "blocked_reason_labels": [],
    }
    if not isinstance(recipe, Mapping):
        result["blocked_reason_labels"].append("recipe_not_mapping")
        return result
    result["blocked_reason_labels"].extend(_recipe_validation_common(recipe))
    result["recipe_id"] = _safe_text(recipe.get("recipe_id"))
    result["recipe_family_id"] = _safe_text(recipe.get("recipe_family_id"))
    result["valid"] = not result["blocked_reason_labels"]
    return result


def build_initial_arc_style_heldout_composition_recipes_v1(seed: int | None = None) -> list[dict[str, Any]]:
    recipes: list[dict[str, Any]] = []
    for family_index, recipe_family_id in enumerate(HELDOUT_RECIPE_FAMILIES_V1):
        for variant_index in range(RECIPE_VARIANTS_PER_FAMILY_V1):
            recipe_seed = _recipe_seed(recipe_family_id, variant_index, seed)
            params = _base_generation_parameters(recipe_family_id, variant_index, recipe_seed)
            depth = 2 if (family_index + variant_index) % 3 != 2 else 3
            if recipe_family_id == "fill_region_then_extract_object" and variant_index == 1:
                depth = 3
            task_id = f"heldout_{recipe_family_id}_variant_{variant_index}_v1"
            primitive_sequence = RECIPE_DEFINITIONS_V1[recipe_family_id]["primitive_sequence"]
            if depth == 3:
                primitive_sequence = ("copy_grid",) + primitive_sequence
            recipe = build_arc_style_heldout_composition_recipe_v1(
                recipe_family_id=recipe_family_id,
                variant_index=variant_index,
                task_id=task_id,
                seed=recipe_seed,
                depth=depth,
                primitive_sequence=primitive_sequence,
                train_pair_count=2,
                test_input_count=1,
                generation_parameters=params,
                leakage_flags={"synthetic_only": True},
            )
            recipes.append(recipe)
    return recipes


def _recipe_task_bundle(recipe: Mapping[str, Any]) -> dict[str, Any]:
    recipe_family_id = _safe_text(recipe.get("recipe_family_id"))
    variant_index = int(recipe.get("variant_index", 0))
    params = recipe.get("generation_parameters", {}) if isinstance(recipe.get("generation_parameters"), Mapping) else {}
    rows = int(params.get("rows", 5))
    cols = int(params.get("cols", 5))
    background = int(params.get("background_color", 0))
    base_color = int(params.get("base_color", 1))
    accent_color = int(params.get("accent_color", 2))
    secondary_color = int(params.get("secondary_color", 3))
    pattern_color = int(params.get("pattern_color", 4))
    seed = int(recipe.get("seed", DEFAULT_HELDOUT_SEED_V1))

    train_pairs: list[dict[str, Any]] = []
    test_inputs: list[dict[str, Any]] = []
    expected_outputs: list[dict[str, Any]] = []

    def add_pair(pair_id: str, input_grid: list[list[int]], output_grid: list[list[int]], notes: str) -> None:
        train_pairs.append(build_arc_style_grid_train_pair_v1(pair_id, input_grid, output_grid, notes))

    if recipe_family_id == "extract_object_then_recolor":
        source_color = base_color
        target_color = accent_color
        for idx in range(int(recipe.get("train_pair_count", 2))):
            input_grid = _grid(rows, cols, background)
            _set_rect(input_grid, 1, 1, 2, 2, source_color)
            _set_cell(input_grid, rows - 2, cols - 2, secondary_color)
            output_grid = _recolor_symbol(_extract_largest_object(input_grid, background), source_color, target_color)
            add_pair(f"{recipe['recipe_id']}_train_{idx}", input_grid, output_grid, "extract the largest object, then recolor it")
        test_grid = _grid(rows, cols, background)
        _set_rect(test_grid, 1, 2, 3, 3, source_color)
        _set_cell(test_grid, 0, cols - 1, secondary_color)
        expected_grid = _recolor_symbol(_extract_largest_object(test_grid, background), source_color, target_color)
    elif recipe_family_id == "move_then_border":
        object_color = base_color
        frame_color = accent_color
        directions = ["down_right", "up_right"]
        direction = directions[variant_index]
        for idx in range(int(recipe.get("train_pair_count", 2))):
            input_grid = _grid(rows, cols, background)
            _set_rect(input_grid, 1 + idx, 1, 1 + idx, 2, object_color)
            moved = _move_single_object(input_grid, object_value=object_color, background_value=background, direction=direction, steps=1)
            output_grid = _add_border_frame(moved, frame_value=frame_color)
            add_pair(f"{recipe['recipe_id']}_train_{idx}", input_grid, output_grid, "move the object, then frame the grid")
        test_grid = _grid(rows, cols, background)
        _set_rect(test_grid, 2, 1 + variant_index, 2, 2 + variant_index, object_color)
        expected_grid = _add_border_frame(
            _move_single_object(test_grid, object_value=object_color, background_value=background, direction=direction, steps=1),
            frame_value=frame_color,
        )
    elif recipe_family_id == "rotate_then_recolor":
        source_color = base_color
        target_color = accent_color
        for idx in range(int(recipe.get("train_pair_count", 2))):
            input_grid = _grid(rows, cols, background)
            _set_cell(input_grid, 1, 1 + idx, source_color)
            _set_cell(input_grid, 2, 1 + idx, source_color)
            _set_cell(input_grid, 2, 2 + idx, source_color)
            rotated = _rotate_90(input_grid)
            output_grid = _recolor_symbol(rotated, source_color, target_color)
            add_pair(f"{recipe['recipe_id']}_train_{idx}", input_grid, output_grid, "rotate the object, then recolor it")
        test_grid = _grid(rows, cols, background)
        _set_cell(test_grid, 1 + variant_index, 1, source_color)
        _set_cell(test_grid, 2 + variant_index, 1, source_color)
        _set_cell(test_grid, 2 + variant_index, 2, source_color)
        expected_grid = _recolor_symbol(_rotate_90(test_grid), source_color, target_color)
    elif recipe_family_id == "remove_noise_then_complete_line":
        line_value = base_color
        for idx in range(int(recipe.get("train_pair_count", 2))):
            input_grid = _grid(rows, cols, background)
            row_index = 2
            for col in (0, 1, 3, 4):
                _set_cell(input_grid, row_index, col, line_value)
            _set_cell(input_grid, 0, idx, secondary_color)
            _set_cell(input_grid, rows - 1, cols - 1 - idx, secondary_color)
            cleaned = _remove_background_noise(input_grid, background_value=background)
            output_grid = _complete_line(cleaned, axis="horizontal", line_index=row_index, line_value=line_value, background_value=background)
            add_pair(f"{recipe['recipe_id']}_train_{idx}", input_grid, output_grid, "remove noise, then complete the line")
        test_grid = _grid(rows, cols, background)
        row_index = 1 + variant_index
        for col in (0, 1, 3, 4):
            _set_cell(test_grid, row_index, col, line_value)
        _set_cell(test_grid, rows - 1, 0, secondary_color)
        expected_grid = _complete_line(
            _remove_background_noise(test_grid, background_value=background),
            axis="horizontal",
            line_index=row_index,
            line_value=line_value,
            background_value=background,
        )
    elif recipe_family_id == "count_object_then_emit_pattern":
        pattern_value = pattern_color
        for idx in range(int(recipe.get("train_pair_count", 2))):
            input_grid = _grid(rows, cols, background)
            object_count = 3 + variant_index
            for obj_idx in range(object_count):
                row = 1 + obj_idx
                col = 1 + ((obj_idx + idx) % 2)
                _set_rect(input_grid, row, col, row, col + 1, base_color)
            _set_cell(input_grid, 0, cols - 1, secondary_color)
            cleaned = _remove_background_noise(input_grid, background_value=background)
            count = _count_objects(cleaned, background_value=background)
            output_grid = _emit_count_pattern(count, pattern_value, background_value=background)
            add_pair(f"{recipe['recipe_id']}_train_{idx}", input_grid, output_grid, "count the objects, then emit the pattern")
        test_grid = _grid(rows, cols, background)
        object_count = 3 + variant_index
        for obj_idx in range(object_count):
            row = 1 + obj_idx
            col = 1 + ((obj_idx + 1) % 2)
            _set_rect(test_grid, row, col, row, col + 1, base_color)
        _set_cell(test_grid, rows - 1, cols - 1, secondary_color)
        expected_grid = _emit_count_pattern(_count_objects(_remove_background_noise(test_grid, background_value=background), background_value=background), pattern_value, background_value=background)
    elif recipe_family_id == "reflect_then_recolor":
        source_color = base_color
        target_color = accent_color
        axis = "horizontal" if variant_index == 0 else "vertical"
        for idx in range(int(recipe.get("train_pair_count", 2))):
            input_grid = _grid(rows, cols, background)
            _set_cell(input_grid, 1 + idx, 1, source_color)
            _set_cell(input_grid, 2 + idx, 1, source_color)
            _set_cell(input_grid, 2 + idx, 2, source_color)
            reflected = _reflect_object_in_bbox(input_grid, axis)
            output_grid = _recolor_symbol(reflected, source_color, target_color)
            add_pair(f"{recipe['recipe_id']}_train_{idx}", input_grid, output_grid, "reflect the object, then recolor it")
        test_grid = _grid(rows, cols, background)
        _set_cell(test_grid, 1 + variant_index, 1, source_color)
        _set_cell(test_grid, 2 + variant_index, 1, source_color)
        _set_cell(test_grid, 2 + variant_index, 2, source_color)
        expected_grid = _recolor_symbol(_reflect_object_in_bbox(test_grid, axis), source_color, target_color)
    elif recipe_family_id == "fill_region_then_extract_object":
        border_color = base_color
        fill_color = accent_color
        for idx in range(int(recipe.get("train_pair_count", 2))):
            input_grid = _grid(rows, cols, background)
            _set_rect(input_grid, 1, 1, rows - 2, cols - 2, background)
            for col in range(1, cols - 1):
                input_grid[1][col] = border_color
                input_grid[rows - 2][col] = border_color
            for row in range(1, rows - 1):
                input_grid[row][1] = border_color
                input_grid[row][cols - 2] = border_color
            _set_cell(input_grid, rows - 1, cols - 1, secondary_color)
            filled = _fill_region(input_grid, fill_value=fill_color, background_value=background)
            output_grid = _extract_largest_object(filled, background_value=background)
            add_pair(f"{recipe['recipe_id']}_train_{idx}", input_grid, output_grid, "fill the region, then extract the largest object")
        test_grid = _grid(rows, cols, background)
        for col in range(1, cols - 1):
            test_grid[1][col] = border_color
            test_grid[rows - 2][col] = border_color
        for row in range(1, rows - 1):
            test_grid[row][1] = border_color
            test_grid[row][cols - 2] = border_color
        _set_cell(test_grid, 0, 0, secondary_color)
        expected_grid = _extract_largest_object(_fill_region(test_grid, fill_value=fill_color, background_value=background), background_value=background)
    else:
        input_grid = _grid(rows, cols, background)
        output_grid = _clone_grid(input_grid)
        add_pair(f"{recipe['recipe_id']}_train_0", input_grid, output_grid, "fallback identity")
        test_grid = _grid(rows, cols, background)
        expected_grid = _clone_grid(test_grid)

    test_input = {
        "test_input_id": f"{recipe['task_id']}_test_0",
        "input_grid": test_grid,
        "notes": f"heldout compositional test input for {recipe_family_id}",
    }
    expected_outputs.append(
        {
            "test_input_id": test_input["test_input_id"],
            "output_grid": expected_grid,
            "output_grid_metadata": build_arc_style_grid_metadata_v1(expected_grid),
            "notes": f"evaluation-only output for {recipe_family_id}",
            "synthetic_only": True,
            "heldout_compositional": True,
            "no_solver_access": True,
        }
    )

    task_packet = build_arc_style_grid_task_packet_v1(
        task_id=_safe_text(recipe.get("task_id")),
        task_source=TASK_SOURCE_INTERNAL_HELDOUT_COMPOSITIONAL_V1,
        train_pairs=train_pairs,
        test_input=test_grid,
        trace={
            "schema_version": SCHEMA_VERSION_V1,
            "heldout_compositional": True,
            "internal_synthetic_only": True,
            "no_public_arc_data": True,
            "no_kaggle_data": True,
            "no_solution_file": True,
            "no_answer_key": True,
            "no_test_output_access_for_solver": True,
            "no_task_id_shortcut": True,
            "no_notes_shortcut": True,
            "no_provider_model_api": True,
            "recipe_family_id": recipe_family_id,
            "recipe_id": recipe.get("recipe_id"),
            "variant_index": variant_index,
            "seed": seed,
            "depth": recipe.get("depth"),
            "primitive_sequence": list(recipe.get("primitive_sequence", [])),
        },
    )
    task_packet.setdefault("trace", {})
    task_packet["trace"].update(
        {
            "heldout_compositional": True,
            "evaluation_outputs_separated": True,
            "solver_visible_expected_outputs_absent": True,
            "recipe_family_id": recipe_family_id,
            "recipe_id": recipe.get("recipe_id"),
            "variant_index": variant_index,
            "seed": seed,
        }
    )
    return {
        "recipe_id": recipe.get("recipe_id"),
        "recipe_family_id": recipe_family_id,
        "task_id": _safe_text(recipe.get("task_id")),
        "variant_index": variant_index,
        "seed": seed,
        "depth": int(recipe.get("depth", 2)),
        "primitive_sequence": list(recipe.get("primitive_sequence", [])),
        "task_packet": task_packet,
        "evaluation_metadata": {
            "schema_version": SCHEMA_VERSION_V1,
            "heldout_compositional": True,
            "synthetic_only": True,
            "expected_outputs": expected_outputs,
            "expected_output_count": len(expected_outputs),
            "solver_visible_expected_outputs_absent": True,
        },
        "provenance_metadata": {
            "source": "internal_synthetic_heldout_compositional_v1",
            "heldout_compositional": True,
            "synthetic_only": True,
            "recipe_family_id": recipe_family_id,
            "recipe_id": recipe.get("recipe_id"),
            "seed": seed,
            "depth": int(recipe.get("depth", 2)),
            "primitive_sequence": list(recipe.get("primitive_sequence", [])),
            "recipe_signature_names": list(recipe.get("primitive_sequence", [])),
            "typed_primitive_signatures_referenced": True,
        },
        "leakage_flags": _normalize_leakage_flags(recipe.get("leakage_flags")),
        "boundary_flags": _normalize_boundary_flags(recipe.get("boundary_flags")),
    }


def generate_arc_style_heldout_compositional_task_v1(recipe: Mapping[str, Any]) -> dict[str, Any]:
    return _recipe_task_bundle(recipe)


def generate_arc_style_heldout_compositional_suite_v1(
    recipe_specs: Sequence[Mapping[str, Any]] | None = None,
    *,
    seed: int | None = None,
) -> dict[str, Any]:
    specs = [
        _json_safe(spec)
        for spec in (
            recipe_specs if recipe_specs is not None else build_initial_arc_style_heldout_composition_recipes_v1(seed=seed)
        )
    ]
    tasks = [generate_arc_style_heldout_compositional_task_v1(spec) for spec in specs]
    suite = {
        "suite_id": SUITE_ID_V1,
        "recipe_specs": specs,
        "tasks": tasks,
        "generator_metadata": {
            "schema_version": SCHEMA_VERSION_V1,
            "synthetic_only": True,
            "heldout_compositional": True,
            "recipe_count": len(specs),
            "task_count": len(tasks),
            "recipe_families": list(HELDOUT_RECIPE_FAMILIES_V1),
            "variant_count_per_family": RECIPE_VARIANTS_PER_FAMILY_V1,
            "typed_primitive_signatures_referenced": True,
            "no_public_arc_data": True,
            "no_kaggle_data": True,
            "no_solution_file": True,
            "no_answer_key": True,
            "no_test_output_access_for_solver": True,
            "no_task_id_shortcut": True,
            "no_notes_shortcut": True,
            "no_provider_model_api": True,
        },
        "boundary_flags": {
            "metadata_only": True,
            "heldout_compositional": True,
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
    return suite


def validate_arc_style_heldout_compositional_task_v1(task: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "task_id": None,
        "recipe_id": None,
        "blocked_reason_labels": [],
    }
    if not isinstance(task, Mapping):
        result["blocked_reason_labels"].append("task_not_mapping")
        return result
    missing = [field for field in REQUIRED_TASK_FIELDS_V1 if field not in task]
    if missing:
        result["blocked_reason_labels"].append("missing_required_fields")
        result["blocked_reason_labels"].extend(f"missing:{field}" for field in missing)
        return result
    result["task_id"] = _safe_text(task.get("task_id"))
    result["recipe_id"] = _safe_text(task.get("recipe_id"))
    if result["recipe_id"] == "":
        result["blocked_reason_labels"].append("empty_recipe_id")
    if result["task_id"] == "":
        result["blocked_reason_labels"].append("empty_task_id")
    if result["recipe_id"] not in {f"{family}_variant_0_v1" for family in HELDOUT_RECIPE_FAMILIES_V1} | {f"{family}_variant_1_v1" for family in HELDOUT_RECIPE_FAMILIES_V1}:
        result["blocked_reason_labels"].append("recipe_id_not_supported")

    recipe_validation = validate_arc_style_heldout_composition_recipe_v1({
        "recipe_id": task.get("recipe_id"),
        "recipe_family_id": task.get("recipe_family_id"),
        "variant_index": task.get("variant_index"),
        "task_id": task.get("task_id"),
        "seed": task.get("seed"),
        "depth": task.get("depth"),
        "primitive_sequence": task.get("primitive_sequence"),
        "train_pair_count": len(task.get("task_packet", {}).get("train_pairs", [])) if isinstance(task.get("task_packet"), Mapping) else 0,
        "test_input_count": 1,
        "generation_parameters": task.get("provenance_metadata", {}),
        "leakage_flags": task.get("leakage_flags"),
        "provenance_metadata": task.get("provenance_metadata"),
        "boundary_flags": task.get("boundary_flags"),
    })
    if not recipe_validation["valid"]:
        result["blocked_reason_labels"].append(f"recipe_invalid:{result['recipe_id']}")
        result["blocked_reason_labels"].extend(recipe_validation["blocked_reason_labels"])

    task_packet = task.get("task_packet")
    packet_validation = validate_arc_style_grid_task_packet_v1(task_packet)
    if not packet_validation["valid"]:
        result["blocked_reason_labels"].append("task_packet_invalid")
        result["blocked_reason_labels"].extend(packet_validation["blocked_reason_labels"])
    else:
        if task_packet.get("task_source") != TASK_SOURCE_INTERNAL_HELDOUT_COMPOSITIONAL_V1:
            result["blocked_reason_labels"].append("task_source_not_heldout_internal")
        trace = task_packet.get("trace", {}) if isinstance(task_packet.get("trace"), Mapping) else {}
        if not bool(trace.get("heldout_compositional", False)):
            result["blocked_reason_labels"].append("task_trace_not_heldout_compositional")
        if not bool(trace.get("internal_synthetic_only", False)):
            result["blocked_reason_labels"].append("task_trace_not_synthetic_only")
        if not bool(trace.get("solver_visible_expected_outputs_absent", False)):
            result["blocked_reason_labels"].append("solver_visible_expected_outputs_must_be_absent")
        for forbidden_key in ("expected_outputs", "answer_key", "solution", "test_output", "public_arc_source", "kaggle_source"):
            if forbidden_key in task_packet:
                result["blocked_reason_labels"].append(f"forbidden_solver_visible_field:{forbidden_key}")

    evaluation_metadata = task.get("evaluation_metadata")
    if not isinstance(evaluation_metadata, Mapping):
        result["blocked_reason_labels"].append("evaluation_metadata_not_mapping")
    else:
        expected_outputs = evaluation_metadata.get("expected_outputs")
        if not isinstance(expected_outputs, list) or len(expected_outputs) != 1:
            result["blocked_reason_labels"].append("expected_outputs_count_invalid")
        else:
            for expected_output in expected_outputs:
                if not isinstance(expected_output, Mapping):
                    result["blocked_reason_labels"].append("expected_output_not_mapping")
                    continue
                if not expected_output.get("synthetic_only", False):
                    result["blocked_reason_labels"].append("expected_output_not_synthetic_only")
                if not expected_output.get("heldout_compositional", False):
                    result["blocked_reason_labels"].append("expected_output_not_heldout_compositional")
                output_grid = expected_output.get("output_grid")
                output_validation = build_arc_style_grid_metadata_v1(output_grid)
                if output_validation["invalid_cells"] or not output_validation["trace"]["rectangular"]:
                    result["blocked_reason_labels"].append("expected_output_grid_invalid")
        if not bool(evaluation_metadata.get("solver_visible_expected_outputs_absent", False)):
            result["blocked_reason_labels"].append("evaluation_outputs_not_separated")

    if not isinstance(task.get("provenance_metadata"), Mapping):
        result["blocked_reason_labels"].append("provenance_metadata_not_mapping")
    if not isinstance(task.get("boundary_flags"), Mapping):
        result["blocked_reason_labels"].append("boundary_flags_not_mapping")
    else:
        boundary_flags = _normalize_boundary_flags(task.get("boundary_flags"))
        if not _boundary_flags_are_clean(boundary_flags):
            result["blocked_reason_labels"].append("boundary_flags_not_clean")
    leakage_flags = _normalize_leakage_flags(task.get("leakage_flags"))
    if not _leakage_flags_are_clean(leakage_flags):
        result["blocked_reason_labels"].append("leakage_flags_not_clean")

    result["valid"] = not result["blocked_reason_labels"]
    return result


def validate_arc_style_heldout_compositional_suite_v1(suite: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "suite_id": None,
        "blocked_reason_labels": [],
        "task_validation_count": 0,
        "recipe_validation_count": 0,
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

    recipe_specs = suite.get("recipe_specs")
    if not isinstance(recipe_specs, list):
        result["blocked_reason_labels"].append("recipe_specs_not_list")
        recipe_specs = []
    tasks = suite.get("tasks")
    if not isinstance(tasks, list):
        result["blocked_reason_labels"].append("tasks_not_list")
        tasks = []

    recipe_ids: list[str] = []
    recipe_family_counts: Counter[str] = Counter()
    for recipe in recipe_specs:
        recipe_validation = validate_arc_style_heldout_composition_recipe_v1(recipe)
        result["recipe_validation_count"] += 1
        if not recipe_validation["valid"]:
            result["blocked_reason_labels"].append(f"recipe_invalid:{recipe_validation.get('recipe_id')}")
            result["blocked_reason_labels"].extend(recipe_validation["blocked_reason_labels"])
        else:
            recipe_id = _safe_text(recipe.get("recipe_id"))
            recipe_ids.append(recipe_id)
            recipe_family_counts[_safe_text(recipe.get("recipe_family_id"))] += 1
    duplicate_recipe_ids = [recipe_id for recipe_id, count in Counter(recipe_ids).items() if count > 1]
    if duplicate_recipe_ids:
        result["blocked_reason_labels"].append("duplicate_recipe_ids")
        result["blocked_reason_labels"].extend(f"duplicate:{recipe_id}" for recipe_id in duplicate_recipe_ids)

    if len(tasks) != len(recipe_specs):
        result["blocked_reason_labels"].append("task_count_mismatch")

    seen_task_ids: set[str] = set()
    for task in tasks:
        task_validation = validate_arc_style_heldout_compositional_task_v1(task)
        result["task_validation_count"] += 1
        if not task_validation["valid"]:
            result["blocked_reason_labels"].append(f"task_invalid:{task_validation.get('task_id')}")
            result["blocked_reason_labels"].extend(task_validation["blocked_reason_labels"])
        else:
            task_id = _safe_text(task.get("task_id"))
            if task_id in seen_task_ids:
                result["blocked_reason_labels"].append("duplicate_task_ids")
            seen_task_ids.add(task_id)
            if _safe_text(task.get("recipe_family_id")) not in HELDOUT_RECIPE_FAMILIES_V1:
                result["blocked_reason_labels"].append("task_recipe_family_not_supported")

    missing_families = [family for family in HELDOUT_RECIPE_FAMILIES_V1 if recipe_family_counts[family] < RECIPE_VARIANTS_PER_FAMILY_V1]
    if missing_families:
        result["blocked_reason_labels"].append("missing_required_recipe_variants")
        result["blocked_reason_labels"].extend(f"missing_family:{family}" for family in missing_families)

    if not isinstance(suite.get("generator_metadata"), Mapping):
        result["blocked_reason_labels"].append("generator_metadata_not_mapping")
    else:
        generator_metadata = suite.get("generator_metadata", {})
        if not bool(generator_metadata.get("synthetic_only", False)):
            result["blocked_reason_labels"].append("generator_metadata_not_synthetic_only")
        if not bool(generator_metadata.get("heldout_compositional", False)):
            result["blocked_reason_labels"].append("generator_metadata_not_heldout_compositional")
        if not bool(generator_metadata.get("typed_primitive_signatures_referenced", False)):
            result["blocked_reason_labels"].append("typed_primitive_signatures_not_referenced")
    if not isinstance(suite.get("boundary_flags"), Mapping):
        result["blocked_reason_labels"].append("boundary_flags_not_mapping")
    elif not _boundary_flags_are_clean(_normalize_boundary_flags(suite.get("boundary_flags"))):
        result["blocked_reason_labels"].append("boundary_flags_not_clean")

    result["valid"] = not result["blocked_reason_labels"]
    return result


def summarize_arc_style_heldout_compositional_suite_v1(suite: Any) -> dict[str, Any]:
    validation = validate_arc_style_heldout_compositional_suite_v1(suite)
    if not isinstance(suite, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "suite_id": None,
            "valid": False,
            "recipe_count": 0,
            "task_count": 0,
            "recipe_family_count": 0,
            "variant_count_per_family": 0,
            "depth_values": [],
            "recipe_families": [],
            "solver_visible_expected_outputs_absent": True,
            "evaluation_outputs_separated": True,
            "typed_primitive_signatures_referenced": True,
            "blocked_reason_labels": validation["blocked_reason_labels"],
        }
    recipe_specs = suite.get("recipe_specs", []) if isinstance(suite.get("recipe_specs"), list) else []
    tasks = suite.get("tasks", []) if isinstance(suite.get("tasks"), list) else []
    recipe_families: list[str] = []
    depth_values: list[int] = []
    variant_counts: Counter[str] = Counter()
    for recipe in recipe_specs:
        if not isinstance(recipe, Mapping):
            continue
        family = _safe_text(recipe.get("recipe_family_id"))
        if family and family not in recipe_families:
            recipe_families.append(family)
        variant_counts[family] += 1
        depth = recipe.get("depth")
        if isinstance(depth, int) and depth not in depth_values:
            depth_values.append(depth)
    solver_visible_expected_outputs_absent = True
    evaluation_outputs_separated = True
    for task in tasks:
        if not isinstance(task, Mapping):
            continue
        solver_visible_expected_outputs_absent = solver_visible_expected_outputs_absent and bool(task.get("evaluation_metadata", {}).get("solver_visible_expected_outputs_absent", False))
        evaluation_outputs_separated = evaluation_outputs_separated and bool(task.get("task_packet", {}).get("trace", {}).get("solver_visible_expected_outputs_absent", False))
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "suite_id": _safe_text(suite.get("suite_id")),
        "valid": validation["valid"],
        "recipe_count": len(recipe_specs),
        "task_count": len(tasks),
        "recipe_family_count": len(recipe_families),
        "variant_count_per_family": max(variant_counts.values()) if variant_counts else 0,
        "depth_values": sorted(depth_values),
        "recipe_families": recipe_families,
        "solver_visible_expected_outputs_absent": solver_visible_expected_outputs_absent,
        "evaluation_outputs_separated": evaluation_outputs_separated,
        "typed_primitive_signatures_referenced": True,
        "blocked_reason_labels": validation["blocked_reason_labels"],
    }


__all__ = [
    "DEFAULT_HELDOUT_SEED_V1",
    "HELDOUT_RECIPE_FAMILIES_V1",
    "RECIPE_VARIANTS_PER_FAMILY_V1",
    "SCHEMA_VERSION_V1",
    "SUITE_ID_V1",
    "TASK_SOURCE_INTERNAL_HELDOUT_COMPOSITIONAL_V1",
    "build_arc_style_heldout_composition_recipe_v1",
    "build_initial_arc_style_heldout_composition_recipes_v1",
    "generate_arc_style_heldout_compositional_suite_v1",
    "generate_arc_style_heldout_compositional_task_v1",
    "summarize_arc_style_heldout_compositional_suite_v1",
    "to_arc_style_heldout_compositional_suite_json_safe_v1",
    "validate_arc_style_heldout_composition_recipe_v1",
    "validate_arc_style_heldout_compositional_recipe_v1",
    "validate_arc_style_heldout_compositional_suite_v1",
    "validate_arc_style_heldout_compositional_task_v1",
]


# Backward-compatible alias kept internal to this module for the requested API name.
def validate_arc_style_heldout_compositional_recipe_v1(recipe: Any) -> dict[str, Any]:
    return validate_arc_style_heldout_composition_recipe_v1(recipe)
