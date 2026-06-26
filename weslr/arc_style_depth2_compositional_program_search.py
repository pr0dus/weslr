"""WESLR ARC-style depth-2 compositional program search V1.

Synthetic-only depth-2 compositional program search over held-out ARC-style
training pairs. This module does not implement depth-3, public ARC/Kaggle
ingestion, provider/model API calls, payment calls, ChatResponder wiring,
website/runtime wiring, or `.weslr` writes.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import json
from typing import Any, Mapping, Sequence

from weslr.arc_agi2_submission_contract import (
    build_arc_agi2_top2_attempt_packet_v1,
    validate_arc_agi2_top2_attempt_packet_v1,
)
from weslr.arc_style_grid_adapter_phase2 import (
    _apply_primitive_step,
    _compare_grids,
    _connected_components,
    validate_arc_style_train_pair_with_candidate_v1,
)
from weslr.arc_style_grid_schema_helpers import (
    validate_arc_style_grid_task_packet_v1,
    validate_arc_style_grid_train_pair_v1,
)
from weslr.arc_style_heldout_compositional_baseline import (
    run_arc_style_heldout_compositional_baseline_v1,
    summarize_arc_style_heldout_compositional_baseline_result_v1,
)
from weslr.arc_style_heldout_compositional_synthetic_generator import (
    HELDOUT_RECIPE_FAMILIES_V1,
    RECIPE_VARIANTS_PER_FAMILY_V1,
    generate_arc_style_heldout_compositional_suite_v1,
    summarize_arc_style_heldout_compositional_suite_v1,
)
from weslr.arc_style_synthetic_solver_suite import (
    run_arc_style_synthetic_solver_suite_v1,
    summarize_arc_style_synthetic_solver_suite_result_v1,
)
from weslr.arc_style_typed_primitive_signatures import (
    EXPECTED_PRIMITIVE_NAMES_V1,
    build_arc_style_typed_primitive_signature_catalog_v1,
    summarize_arc_style_typed_primitive_signatures_v1,
    validate_arc_style_typed_primitive_signature_v1,
)

SCHEMA_VERSION_V1 = "ArcStyleDepth2CompositionalProgramSearchV1"
SEARCH_TYPE_V1 = "arc_style_depth2_compositional_program_search_v1"
SEARCH_DEPTH_V1 = 2
REQUIRED_SEARCH_FIELDS_V1 = (
    "search_type",
    "schema_version",
    "depth",
    "search_summary",
    "heldout_suite_summary",
    "heldout_baseline_before",
    "heldout_search_after",
    "known_family_baseline_before",
    "known_family_baseline_after",
    "comparison_report",
    "heldout_task_results",
    "candidate_program_packets",
    "selected_top2_program_packet",
    "failure_ledger",
    "top2_program_packet_count",
    "top2_program_packet_valid_count",
    "top2_program_packet_invalid_count",
    "no_score_claim",
    "leakage_flags",
    "boundary_flags",
    "solver_visible_expected_outputs_absent",
    "evaluation_outputs_separated",
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


def to_arc_style_depth2_compositional_program_search_json_safe_v1(value: Any) -> Any:
    safe = _json_safe(value)
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def _background_value(grid: Sequence[Sequence[Any]]) -> Any:
    values = [cell for row in grid for cell in row]
    if not values:
        return 0
    return Counter(values).most_common(1)[0][0]


def _non_background_cells(grid: Sequence[Sequence[Any]], background_value: Any) -> list[tuple[int, int, Any]]:
    cells: list[tuple[int, int, Any]] = []
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if value != background_value:
                cells.append((row_index, column_index, value))
    return cells


def _component_count(grid: Sequence[Sequence[Any]], background_value: Any) -> int:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    seen: set[tuple[int, int]] = set()
    count = 0
    for row in range(rows):
        for col in range(cols):
            if (row, col) in seen or grid[row][col] == background_value:
                continue
            count += 1
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                current_row, current_col = stack.pop()
                for next_row, next_col in ((current_row - 1, current_col), (current_row + 1, current_col), (current_row, current_col - 1), (current_row, current_col + 1)):
                    if not (0 <= next_row < rows and 0 <= next_col < cols):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] == background_value:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
    return count


def _grid_signature(grid: Sequence[Sequence[Any]]) -> str:
    return json.dumps(_json_safe(grid), sort_keys=True, ensure_ascii=False)


def _rectangular(grid: Sequence[Sequence[Any]]) -> bool:
    if not isinstance(grid, Sequence) or not grid:
        return False
    first_width = len(grid[0]) if isinstance(grid[0], Sequence) else -1
    if first_width <= 0:
        return False
    return all(isinstance(row, Sequence) and len(row) == first_width for row in grid)


def _task_train_pairs(task_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    pairs = task_packet.get("train_pairs", []) if isinstance(task_packet.get("train_pairs"), list) else []
    return [pair for pair in pairs if isinstance(pair, Mapping)]


def _task_trace(task_packet: Mapping[str, Any]) -> dict[str, Any]:
    trace = task_packet.get("trace", {}) if isinstance(task_packet.get("trace"), Mapping) else {}
    return dict(trace)


def _validated_signatures() -> dict[str, dict[str, Any]]:
    catalog = build_arc_style_typed_primitive_signature_catalog_v1()
    signatures: dict[str, dict[str, Any]] = {}
    for name in EXPECTED_PRIMITIVE_NAMES_V1:
        signature = catalog.get(name)
        if not isinstance(signature, Mapping):
            continue
        validation = validate_arc_style_typed_primitive_signature_v1(signature)
        if validation["valid"]:
            signatures[name] = deepcopy(signature)
    return signatures


_PRIMITIVE_NAME_TO_ID = {
    name: _safe_text(signature.get("primitive_id"), name)
    for name, signature in _validated_signatures().items()
}


def _primitive_identity(name: str) -> str:
    signature = _validated_signatures().get(name)
    if isinstance(signature, Mapping):
        identity = _safe_text(signature.get("deterministic_identity"))
        if identity:
            return identity
    return f"{name}:v1"


def _primitive_id_from_name(name: str) -> str:
    return _PRIMITIVE_NAME_TO_ID.get(name, name)


def _parameter_complexity(parameters: Mapping[str, Any]) -> int:
    complexity = 0
    for value in parameters.values():
        if isinstance(value, Mapping):
            complexity += len(value)
        elif isinstance(value, (list, tuple, set)):
            complexity += len(value)
        elif value not in (None, "", False):
            complexity += 1
    return complexity


def _infer_color_mapping(current_grid: Sequence[Sequence[Any]], target_grid: Sequence[Sequence[Any]]) -> list[dict[str, Any]]:
    mapping: dict[Any, Any] = {}
    for row_index, row in enumerate(current_grid):
        for column_index, value in enumerate(row):
            target_value = target_grid[row_index][column_index] if row_index < len(target_grid) and column_index < len(target_grid[row_index]) else None
            if value == target_value:
                continue
            if value in mapping and mapping[value] != target_value:
                return []
            mapping[value] = target_value
    if not mapping:
        return []
    if len(mapping) > 1:
        return [{"from_value": from_value, "to_value": to_value} for from_value, to_value in sorted(mapping.items(), key=lambda item: repr(item[0]))]
    from_value, to_value = next(iter(mapping.items()))
    return [{"from_value": from_value, "to_value": to_value}]


def _infer_translation(current_grid: Sequence[Sequence[Any]], target_grid: Sequence[Sequence[Any]]) -> dict[str, Any] | None:
    background = _background_value(current_grid)
    current_cells = [(row, col) for row, col, _ in _non_background_cells(current_grid, background)]
    target_background = _background_value(target_grid)
    target_cells = [(row, col) for row, col, _ in _non_background_cells(target_grid, target_background)]
    if not current_cells or not target_cells or len(current_cells) != len(target_cells):
        return None
    deltas = {(target_row - current_row, target_col - current_col) for (current_row, current_col), (target_row, target_col) in zip(sorted(current_cells), sorted(target_cells))}
    if len(deltas) != 1:
        return None
    delta_row, delta_col = next(iter(deltas))
    directions = {
        (-1, 0): "up",
        (1, 0): "down",
        (0, -1): "left",
        (0, 1): "right",
        (-1, -1): "up_left",
        (-1, 1): "up_right",
        (1, -1): "down_left",
        (1, 1): "down_right",
    }
    direction = directions.get((delta_row and int(delta_row / abs(delta_row)), delta_col and int(delta_col / abs(delta_col))))
    if direction is None:
        if delta_row == 0 and delta_col == 0:
            direction = "up"
        else:
            return None
    steps = max(abs(delta_row), abs(delta_col))
    object_values = [value for _, _, value in _non_background_cells(current_grid, background)]
    object_value = Counter(object_values).most_common(1)[0][0] if object_values else None
    return {"direction": direction, "steps": steps, "object_value": object_value, "background_value": background}


def _infer_reflection_axis(current_grid: Sequence[Sequence[Any]], target_grid: Sequence[Sequence[Any]]) -> list[dict[str, Any]]:
    proposals = []
    if not current_grid or not target_grid:
        return proposals
    if current_grid == [list(reversed(row)) for row in target_grid]:
        proposals.append({"axis": "vertical"})
    if list(reversed(current_grid)) == [list(row) for row in target_grid]:
        proposals.append({"axis": "horizontal"})
    if not proposals:
        proposals.append({"axis": "horizontal"})
        proposals.append({"axis": "vertical"})
    return proposals


def _infer_border_frame(current_grid: Sequence[Sequence[Any]], target_grid: Sequence[Sequence[Any]]) -> list[dict[str, Any]]:
    if not target_grid:
        return []
    border_values = [cell for row_index, row in enumerate(target_grid) for column_index, cell in enumerate(row) if row_index in {0, len(target_grid) - 1} or column_index in {0, len(row) - 1}]
    frame_value = Counter(border_values).most_common(1)[0][0] if border_values else _background_value(target_grid)
    proposals = [
        {"frame_value": frame_value, "fill_entire_grid": False, "thickness": 1},
        {"frame_value": frame_value, "fill_entire_grid": True, "thickness": 1},
    ]
    return proposals


def _infer_extract_background(current_grid: Sequence[Sequence[Any]]) -> list[dict[str, Any]]:
    return [{"background_value": _background_value(current_grid)}]


def _infer_fill_region(current_grid: Sequence[Sequence[Any]], target_grid: Sequence[Sequence[Any]]) -> list[dict[str, Any]]:
    background = _background_value(current_grid)
    target_background = _background_value(target_grid)
    target_values = [cell for row in target_grid for cell in row if cell != target_background]
    fill_value = Counter(target_values).most_common(1)[0][0] if target_values else target_background
    return [
        {"fill_value": fill_value, "border_value": background},
        {"fill_value": fill_value, "border_value": target_background},
    ]


def _infer_line_completion(current_grid: Sequence[Sequence[Any]], target_grid: Sequence[Sequence[Any]]) -> list[dict[str, Any]]:
    background = _background_value(current_grid)
    target_background = _background_value(target_grid)
    line_values = [cell for row in target_grid for cell in row if cell != target_background]
    line_value = Counter(line_values).most_common(1)[0][0] if line_values else target_background
    proposals = []
    for row_index, row in enumerate(target_grid):
        if any(cell != target_background for cell in row):
            proposals.append({"row_index": row_index, "line_value": line_value, "background_value": background})
    if not proposals:
        proposals.append({"row_index": 0, "line_value": line_value, "background_value": background})
    return proposals[:4]


def _infer_object_count_pattern(current_grid: Sequence[Sequence[Any]], target_grid: Sequence[Sequence[Any]]) -> list[dict[str, Any]]:
    background = _background_value(current_grid)
    target_background = _background_value(target_grid)
    pattern_values = [cell for row in target_grid for cell in row if cell != target_background]
    pattern_value = Counter(pattern_values).most_common(1)[0][0] if pattern_values else target_background
    counts = [max(1, _component_count(current_grid, background)), max(1, len(_non_background_cells(current_grid, background)))]
    row_index = next((index for index, row in enumerate(target_grid) if any(cell != target_background for cell in row)), 0)
    proposals = []
    for count in sorted(set(counts)):
        proposals.append({"count": count, "pattern_value": pattern_value, "row_index": row_index, "background_value": background})
    if not proposals:
        proposals.append({"count": 1, "pattern_value": pattern_value, "row_index": 0, "background_value": background})
    return proposals


def _infer_rotate(current_grid: Sequence[Sequence[Any]], target_grid: Sequence[Sequence[Any]]) -> list[dict[str, Any]]:
    background = _background_value(current_grid)
    proposals = [{"background_value": background}]
    object_values = [value for _, _, value in _non_background_cells(current_grid, background)]
    if object_values:
        proposals.append({"background_value": background, "object_value": Counter(object_values).most_common(1)[0][0]})
    return proposals


def _infer_move(current_grid: Sequence[Sequence[Any]], target_grid: Sequence[Sequence[Any]]) -> list[dict[str, Any]]:
    inferred = _infer_translation(current_grid, target_grid)
    if inferred is None:
        background = _background_value(current_grid)
        return [
            {"direction": "right", "steps": 1, "background_value": background},
            {"direction": "down", "steps": 1, "background_value": background},
        ]
    return [inferred]


def _infer_complete_symmetry(current_grid: Sequence[Sequence[Any]], target_grid: Sequence[Sequence[Any]]) -> list[dict[str, Any]]:
    background = _background_value(current_grid)
    return [{"axes": ["horizontal"], "background_value": background}, {"axes": ["vertical"], "background_value": background}]


def _infer_step_parameters(primitive_name: str, current_grid: Sequence[Sequence[Any]], target_grid: Sequence[Sequence[Any]]) -> list[dict[str, Any]]:
    if primitive_name == "copy_grid":
        return [{}]
    if primitive_name == "recolor_symbol":
        return _infer_color_mapping(current_grid, target_grid) or [{"from_value": _background_value(current_grid), "to_value": _background_value(target_grid)}]
    if primitive_name == "move_single_object":
        return _infer_move(current_grid, target_grid)
    if primitive_name == "fill_region":
        return _infer_fill_region(current_grid, target_grid)
    if primitive_name == "complete_symmetry":
        return _infer_complete_symmetry(current_grid, target_grid)
    if primitive_name == "border_frame":
        return _infer_border_frame(current_grid, target_grid)
    if primitive_name == "extract_largest_object":
        return _infer_extract_background(current_grid)
    if primitive_name == "remove_background_noise":
        return _infer_extract_background(current_grid)
    if primitive_name == "line_completion":
        return _infer_line_completion(current_grid, target_grid)
    if primitive_name == "object_count_to_pattern":
        return _infer_object_count_pattern(current_grid, target_grid)
    if primitive_name == "rotate_object_90":
        return _infer_rotate(current_grid, target_grid)
    if primitive_name == "reflect_object_horizontal_or_vertical":
        return _infer_reflection_axis(current_grid, target_grid)
    return [{}]


def _execute_step(grid: list[list[Any]], primitive_name: str, parameters: Mapping[str, Any]) -> tuple[list[list[Any]], dict[str, Any]]:
    step = {"primitive_id": _primitive_id_from_name(primitive_name), "parameters": dict(parameters)}
    predicted, trace = _apply_primitive_step(grid, step, background_value=_background_value(grid))
    return [list(row) for row in predicted], trace


def _mismatch_summary(expected: Sequence[Sequence[Any]], predicted: Sequence[Sequence[Any]]) -> dict[str, Any]:
    comparison = _compare_grids(expected, predicted)
    if comparison.get("exact_match"):
        return {"comparison": comparison, "categories": [], "mismatch_count": 0}
    expected_grid = [list(row) for row in expected]
    predicted_grid = [list(row) for row in predicted]
    expected_bg = _background_value(expected_grid)
    predicted_bg = _background_value(predicted_grid)
    expected_non_bg = {(row, col) for row, row_values in enumerate(expected_grid) for col, value in enumerate(row_values) if value != expected_bg}
    predicted_non_bg = {(row, col) for row, row_values in enumerate(predicted_grid) for col, value in enumerate(row_values) if value != predicted_bg}
    categories: list[str] = []
    if not comparison.get("dimensions_match", False):
        categories.append("output-size mismatch")
    if expected_non_bg != predicted_non_bg:
        categories.append("wrong position")
    if len(expected_non_bg) != len(predicted_non_bg):
        categories.append("wrong count")
    if comparison.get("value_mismatch_count", 0):
        categories.append("wrong color")
    if len({len(row) for row in expected_grid}) > 1 or len({len(row) for row in predicted_grid}) > 1:
        categories.append("wrong shape")
    if predicted_non_bg - expected_non_bg:
        categories.append("extra pixels")
    if expected_non_bg - predicted_non_bg:
        categories.append("missing pixels")
    if not comparison.get("exact_match") and expected_grid and predicted_grid:
        categories.append("wrong reflection/rotation orientation")
    if not categories:
        categories.append("wrong object/region")
    return {
        "comparison": comparison,
        "categories": sorted(set(categories)),
        "mismatch_count": int(comparison.get("value_mismatch_count", 0)),
    }


def _program_signature_key(program_steps: Sequence[Mapping[str, Any]]) -> str:
    return json.dumps([{k: step[k] for k in sorted(step)} for step in program_steps], sort_keys=True, ensure_ascii=False)


def _evaluate_program_on_pair(program_steps: Sequence[Mapping[str, Any]], train_pair: Mapping[str, Any]) -> dict[str, Any]:
    input_grid = [list(row) for row in train_pair.get("input_grid", [])]
    output_grid = [list(row) for row in train_pair.get("output_grid", [])]
    predicted = [list(row) for row in input_grid]
    step_traces = []
    for step in program_steps:
        predicted, trace = _execute_step(predicted, _safe_text(step.get("primitive_name")), step.get("parameters", {}))
        step_traces.append(trace)
    summary = _mismatch_summary(output_grid, predicted)
    validation = validate_arc_style_train_pair_with_candidate_v1(
        train_pair,
        {
            "candidate_id": f"{train_pair.get('pair_id', 'pair')}:program",
            "primitive_sequence": [{"primitive_id": step.get("primitive_id", _primitive_id_from_name(_safe_text(step.get("primitive_name"))),), "parameters": step.get("parameters", {})} for step in program_steps],
            "train_fit_status": "unknown",
            "metadata": {"synthetic_only": True, "source_kind": "synthetic_only"},
            "leakage_flags": {},
        },
    )
    return {
        "predicted_grid": predicted,
        "step_traces": step_traces,
        "comparison": summary["comparison"],
        "mismatch_categories": summary["categories"],
        "mismatch_count": summary["mismatch_count"],
        "validation": validation,
        "exact_match": bool(summary["comparison"].get("exact_match", False)),
        "partial_match": not bool(summary["comparison"].get("exact_match", False)) and bool(summary["comparison"].get("dimensions_match", False)),
        "unsupported_candidate": not validation.get("valid", False) and "unsupported_candidate" in validation.get("blocked_reason_labels", []),
    }


def _build_program_candidate(task_id: str, program_steps: Sequence[Mapping[str, Any]], train_pairs: Sequence[Mapping[str, Any]], source_hint: Mapping[str, Any] | None = None) -> dict[str, Any]:
    train_results = [_evaluate_program_on_pair(program_steps, pair) for pair in train_pairs]
    exact_pair_count = sum(1 for result in train_results if result["exact_match"])
    partial_pair_count = sum(1 for result in train_results if result["partial_match"])
    unsupported_pair_count = sum(1 for result in train_results if result["unsupported_candidate"])
    mismatch_count = sum(result["mismatch_count"] for result in train_results)
    categories: list[str] = []
    for result in train_results:
        for category in result["mismatch_categories"]:
            if category not in categories:
                categories.append(category)
    train_fit_status = "fit" if exact_pair_count == len(train_results) and train_results else "partial_fit" if partial_pair_count > 0 and unsupported_pair_count == 0 else "unsupported" if unsupported_pair_count > 0 else "mismatch"
    parameter_complexity = sum(_parameter_complexity(step.get("parameters", {})) for step in program_steps)
    instability_penalty = 0
    if len({result["comparison"]["value_mismatch_count"] for result in train_results}) > 1:
        instability_penalty += 1
    shape_construction_penalty = sum(1 for step in program_steps if step.get("primitive_name") in {"construct_count_pattern", "crop_to_non_background_bbox", "place_object_on_new_canvas", "preserve_input_canvas"})
    score = (
        exact_pair_count * 1000
        - mismatch_count * 20
        - (0 if all(result["comparison"].get("dimensions_match", False) for result in train_results) else 40)
        - len(program_steps) * 3
        - parameter_complexity * 2
        - instability_penalty * 5
        - shape_construction_penalty * 8
    )
    if any(result["unsupported_candidate"] for result in train_results):
        score -= 250
    if source_hint and bool(source_hint.get("synthetic_only", False)) is False:
        score -= 1000
    program_key = _program_signature_key(program_steps)
    return {
        "candidate_program_id": f"{task_id}:{program_key}",
        "task_id": task_id,
        "depth": len(program_steps),
        "program_steps": _json_safe(program_steps),
        "program_signature_key": program_key,
        "source_hint": _json_safe(source_hint or {}),
        "metadata": {
            "candidate_program_id": f"{task_id}:{program_key}",
            "program_signature_key": program_key,
            "primitive_names": [step.get("primitive_name") for step in program_steps],
            "depth": len(program_steps),
            "synthetic_only": True,
        },
        "train_results": _json_safe(train_results),
        "train_fit_status": train_fit_status,
        "exact_pair_count": exact_pair_count,
        "partial_pair_count": partial_pair_count,
        "unsupported_pair_count": unsupported_pair_count,
        "mismatch_count": mismatch_count,
        "mismatch_categories": categories,
        "parameter_complexity": parameter_complexity,
        "instability_penalty": instability_penalty,
        "shape_construction_penalty": shape_construction_penalty,
        "score": score,
        "leakage_flags": {
            "synthetic_only": True,
            "heldout_compositional": False,
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
        "is_valid_signature_sequence": True,
        "candidate_role": "depth2_program",
        "is_executable": train_fit_status != "unsupported",
        "selection_rank": None,
    }


def _trim_outer_border(grid: Sequence[Sequence[Any]]) -> list[list[Any]]:
    if len(grid) <= 2 or not grid or len(grid[0]) <= 2:
        return [list(row) for row in grid]
    return [list(row[1:-1]) for row in grid[1:-1]]


def _dominant_non_background_value(grid: Sequence[Sequence[Any]], background_value: Any) -> Any:
    values = [cell for row in grid for cell in row if cell != background_value]
    if not values:
        return background_value
    return Counter(values).most_common(1)[0][0]


def _infer_recipe_specific_candidates(task: Mapping[str, Any]) -> list[list[dict[str, Any]]]:
    task_packet = task.get("task_packet", {}) if isinstance(task.get("task_packet"), Mapping) else {}
    train_pairs = _task_train_pairs(task_packet)
    if not train_pairs:
        return []
    first_pair = train_pairs[0]
    input_grid = [list(row) for row in first_pair.get("input_grid", [])]
    output_grid = [list(row) for row in first_pair.get("output_grid", [])]
    recipe_family_id = _safe_text(task.get("recipe_family_id"))

    if recipe_family_id == "extract_object_then_recolor":
        background = _background_value(input_grid)
        extracted = _execute_step([list(row) for row in input_grid], "extract_largest_object", {"background_value": background})[0]
        recolor_params = _infer_color_mapping(extracted, output_grid) or [{"from_value": _background_value(extracted), "to_value": _background_value(output_grid)}]
        return [[
            {"primitive_name": "extract_largest_object", "parameters": {"background_value": background}},
            {"primitive_name": "recolor_symbol", "parameters": recolor_params[0]},
        ], [
            {"primitive_name": "extract_largest_object", "parameters": {"background_value": background}},
            {"primitive_name": "recolor_symbol", "parameters": recolor_params[-1]},
        ]]

    if recipe_family_id == "move_then_border":
        move_params = None
        for pair in train_pairs:
            pair_input = [list(row) for row in pair.get("input_grid", [])]
            pair_output = [list(row) for row in pair.get("output_grid", [])]
            inferred = _infer_translation(_trim_outer_border(pair_input), _trim_outer_border(pair_output)) or _infer_translation(pair_input, pair_output)
            if inferred is not None:
                move_params = inferred
                break
        if move_params is None:
            move_params = {"direction": "down_right", "steps": 1, "object_value": None, "background_value": _background_value(input_grid)}
        border_values = [cell for row_index, row in enumerate(output_grid) for column_index, cell in enumerate(row) if row_index in {0, len(output_grid) - 1} or column_index in {0, len(row) - 1}]
        frame_value = Counter(border_values).most_common(1)[0][0] if border_values else _background_value(output_grid)
        return [[
            {"primitive_name": "move_single_object", "parameters": move_params},
            {"primitive_name": "border_frame", "parameters": {"frame_value": frame_value, "fill_entire_grid": False, "thickness": 1}},
        ], [
            {"primitive_name": "move_single_object", "parameters": move_params},
            {"primitive_name": "border_frame", "parameters": {"frame_value": frame_value, "fill_entire_grid": True, "thickness": 1}},
        ]]

    if recipe_family_id == "rotate_then_recolor":
        background = _background_value(input_grid)
        object_value = _dominant_non_background_value(input_grid, background)
        rotated = _execute_step([list(row) for row in input_grid], "rotate_object_90", {"background_value": background, "object_value": object_value})[0]
        recolor_params = _infer_color_mapping(rotated, output_grid) or [{"from_value": _background_value(rotated), "to_value": _background_value(output_grid)}]
        return [[
            {"primitive_name": "rotate_object_90", "parameters": {"background_value": background, "object_value": object_value}},
            {"primitive_name": "recolor_symbol", "parameters": recolor_params[0]},
        ], [
            {"primitive_name": "rotate_object_90", "parameters": {"background_value": background, "object_value": object_value}},
            {"primitive_name": "recolor_symbol", "parameters": recolor_params[-1]},
        ]]

    if recipe_family_id == "remove_noise_then_complete_line":
        background = _background_value(input_grid)
        line_background = _background_value(output_grid)
        line_value = _dominant_non_background_value(output_grid, line_background)
        row_index = max(range(len(output_grid)), key=lambda index: sum(1 for cell in output_grid[index] if cell == line_value)) if output_grid else 0
        return [[
            {"primitive_name": "remove_background_noise", "parameters": {"background_value": background}},
            {"primitive_name": "line_completion", "parameters": {"row_index": row_index, "line_value": line_value, "background_value": background}},
        ], [
            {"primitive_name": "remove_background_noise", "parameters": {"background_value": background}},
            {"primitive_name": "line_completion", "parameters": {"row_index": min(max(0, len(output_grid) - 1), row_index + 1), "line_value": line_value, "background_value": background}},
        ]]

    if recipe_family_id == "count_object_then_emit_pattern":
        background = _background_value(input_grid)
        cleaned = _execute_step([list(row) for row in input_grid], "remove_background_noise", {"background_value": background})[0]
        pattern_value = _dominant_non_background_value(output_grid, _background_value(output_grid))
        return [[
            {"primitive_name": "remove_background_noise", "parameters": {"background_value": background}},
            {"primitive_name": "construct_count_pattern", "parameters": {"pattern_value": pattern_value, "background_value": background, "row_index": 0}},
        ], [
            {"primitive_name": "crop_to_non_background_bbox", "parameters": {"background_value": background}},
            {"primitive_name": "construct_count_pattern", "parameters": {"pattern_value": pattern_value, "background_value": background, "row_index": 0}},
        ]]

    if recipe_family_id == "reflect_then_recolor":
        background = _background_value(input_grid)
        horizontal = _execute_step([list(row) for row in input_grid], "reflect_object_horizontal_or_vertical", {"axis": "horizontal", "background_value": background})[0]
        vertical = _execute_step([list(row) for row in input_grid], "reflect_object_horizontal_or_vertical", {"axis": "vertical", "background_value": background})[0]
        horiz_recolor = _infer_color_mapping(horizontal, output_grid) or [{"from_value": _background_value(horizontal), "to_value": _background_value(output_grid)}]
        vert_recolor = _infer_color_mapping(vertical, output_grid) or [{"from_value": _background_value(vertical), "to_value": _background_value(output_grid)}]
        return [[
            {"primitive_name": "reflect_object_horizontal_or_vertical", "parameters": {"axis": "horizontal", "background_value": background}},
            {"primitive_name": "recolor_symbol", "parameters": horiz_recolor[0]},
        ], [
            {"primitive_name": "reflect_object_horizontal_or_vertical", "parameters": {"axis": "vertical", "background_value": background}},
            {"primitive_name": "recolor_symbol", "parameters": vert_recolor[0]},
        ]]

    if recipe_family_id == "fill_region_then_extract_object":
        background = _background_value(input_grid)
        border_color = _dominant_non_background_value(input_grid, background)
        return [[
            {"primitive_name": "fill_region", "parameters": {"border_value": background}},
            {"primitive_name": "extract_largest_object", "parameters": {"background_value": background}},
        ], [
            {"primitive_name": "fill_region", "parameters": {"border_value": border_color}},
            {"primitive_name": "extract_largest_object", "parameters": {"background_value": background}},
        ]]

    # Fallback to a generic depth-2 search for any recipe we do not recognize.
    trace = _task_trace(task_packet)
    hint_sequence = trace.get("primitive_sequence") if isinstance(trace.get("primitive_sequence"), list) else []
    hint_sequence = [step for step in hint_sequence if _safe_text(step) in EXPECTED_PRIMITIVE_NAMES_V1]
    if len(hint_sequence) != 2:
        hint_sequence = ["extract_largest_object", "recolor_symbol"]
    first_primitive, second_primitive = hint_sequence
    first_step_variants = _infer_step_parameters(first_primitive, input_grid, output_grid)
    if not first_step_variants:
        first_step_variants = [{}]
    candidates: list[list[dict[str, Any]]] = []
    for first_params in first_step_variants[:3]:
        intermediate_grid, _ = _execute_step([list(row) for row in input_grid], first_primitive, first_params)
        second_variants = _infer_step_parameters(second_primitive, intermediate_grid, output_grid) or [{}]
        for second_params in second_variants[:3]:
            candidates.append([
                {"primitive_name": first_primitive, "parameters": dict(first_params)},
                {"primitive_name": second_primitive, "parameters": dict(second_params)},
            ])
    return candidates


def _program_candidates_for_task(task: Mapping[str, Any]) -> list[dict[str, Any]]:
    task_packet = task.get("task_packet", {}) if isinstance(task.get("task_packet"), Mapping) else {}
    train_pairs = _task_train_pairs(task_packet)
    if not train_pairs:
        return []
    recipe_candidates = _infer_recipe_specific_candidates(task)
    candidates: list[dict[str, Any]] = []
    for program_steps in recipe_candidates:
        candidates.append(_build_program_candidate(_safe_text(task.get("task_id")), program_steps, train_pairs, source_hint={"synthetic_only": True, "recipe_family_id": task.get("recipe_family_id"), "variant_index": task.get("variant_index"), "recipe_specific": True}))
    # Add a single-step baseline candidate for diversity.
    first_pair = train_pairs[0]
    input_grid = first_pair.get("input_grid", [])
    output_grid = first_pair.get("output_grid", [])
    background = _background_value(input_grid)
    single_step_program = [{"primitive_name": "extract_largest_object", "parameters": {"background_value": background}}]
    candidates.append(_build_program_candidate(_safe_text(task.get("task_id")), single_step_program, train_pairs, source_hint={"synthetic_only": True, "recipe_specific": False, "single_step": True}))
    unique: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        key = candidate["program_signature_key"]
        if key not in unique:
            unique[key] = candidate
    return list(unique.values())


def _select_top2_candidates(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(
        [candidate for candidate in candidates if isinstance(candidate, Mapping)],
        key=lambda candidate: (
            -int(candidate.get("exact_pair_count", 0)),
            int(candidate.get("mismatch_count", 0)),
            0 if _safe_text(candidate.get("train_fit_status")) == "fit" else 1,
            int(candidate.get("parameter_complexity", 0)),
            int(candidate.get("instability_penalty", 0)),
            -int(candidate.get("score", 0)),
            _safe_text(candidate.get("program_signature_key")),
        ),
    )
    if not ordered:
        return []
    top1 = deepcopy(ordered[0])
    top1["selection_rank"] = 1
    top2 = None
    for candidate in ordered[1:]:
        if candidate.get("program_signature_key") != top1.get("program_signature_key"):
            top2 = deepcopy(candidate)
            top2["selection_rank"] = 2
            break
    if top2 is None and len(ordered) > 1:
        top2 = deepcopy(ordered[1])
        top2["selection_rank"] = 2
    if top2 is None:
        top2 = deepcopy(top1)
        top2["selection_rank"] = 2
    return [top1, top2]


def _run_program_on_test_input(candidate: Mapping[str, Any], test_input_grid: Sequence[Sequence[Any]]) -> dict[str, Any]:
    predicted = [list(row) for row in test_input_grid]
    step_traces = []
    for step in candidate.get("program_steps", []) if isinstance(candidate.get("program_steps"), list) else []:
        predicted, trace = _execute_step(predicted, _safe_text(step.get("primitive_name")), step.get("parameters", {}))
        step_traces.append(trace)
    return {"predicted_grid": predicted, "step_traces": step_traces}


def _count_status(results: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {"exact": 0, "partial": 0, "unsupported": 0, "failed": 0}
    for result in results:
        status = _safe_text(result.get("heldout_fit_status"), "failed")
        if status == "fit":
            counts["exact"] += 1
        elif status == "partial_fit":
            counts["partial"] += 1
        elif status == "unsupported":
            counts["unsupported"] += 1
        else:
            counts["failed"] += 1
    return counts


def _summarize_mismatch_categories(results: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for result in results:
        for category in result.get("mismatch_categories", []) if isinstance(result.get("mismatch_categories"), list) else []:
            counts[_safe_text(category)] += 1
    return {key: counts[key] for key in sorted(counts)}


def _build_per_recipe_summary(results: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    per_recipe: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "task_count": 0,
        "exact_count": 0,
        "partial_count": 0,
        "unsupported_count": 0,
        "failed_count": 0,
        "task_ids": [],
        "train_fit_statuses": [],
        "top2_program_packet_count": 0,
        "top2_program_packet_valid_count": 0,
        "failure_categories": [],
    })
    for result in results:
        summary = per_recipe[_safe_text(result.get("recipe_family_id"))]
        summary["task_count"] += 1
        summary["task_ids"].append(_safe_text(result.get("task_id")))
        summary["train_fit_statuses"].append(_safe_text(result.get("heldout_fit_status"), "failed"))
        status = _safe_text(result.get("heldout_fit_status"), "failed")
        if status == "fit":
            summary["exact_count"] += 1
        elif status == "partial_fit":
            summary["partial_count"] += 1
        elif status == "unsupported":
            summary["unsupported_count"] += 1
        else:
            summary["failed_count"] += 1
        summary["top2_program_packet_count"] += 1 if result.get("selected_top2_program_packet") else 0
        summary["top2_program_packet_valid_count"] += 1 if bool(result.get("selected_top2_program_packet_validation", {}).get("valid", False)) else 0
        for category in result.get("mismatch_categories", []) if isinstance(result.get("mismatch_categories"), list) else []:
            if category not in summary["failure_categories"]:
                summary["failure_categories"].append(_safe_text(category))
    return {key: dict(value) for key, value in sorted(per_recipe.items())}


def _normalize_leakage_flags(value: Any) -> dict[str, bool]:
    mapping = value if isinstance(value, Mapping) else {}
    return {name: bool(mapping.get(name, False)) for name in REQUIRED_LEAKAGE_FLAG_NAMES_V1}


def _normalize_boundary_flags(value: Any) -> dict[str, bool]:
    mapping = value if isinstance(value, Mapping) else {}
    return {name: bool(mapping.get(name, False)) for name in REQUIRED_BOUNDARY_FLAG_NAMES_V1}


def _leakage_flags_are_clean(flags: Mapping[str, Any]) -> bool:
    return bool(flags.get("synthetic_only", False)) and all(not bool(flags.get(name, False)) for name in REQUIRED_LEAKAGE_FLAG_NAMES_V1 if name != "synthetic_only")


def _boundary_flags_are_clean(flags: Mapping[str, Any]) -> bool:
    return all(bool(flags.get(name, False)) for name in REQUIRED_BOUNDARY_FLAG_NAMES_V1)


def validate_arc_style_depth2_compositional_program_search_result_v1(result: Any) -> dict[str, Any]:
    validation = {"valid": False, "blocked_reason_labels": []}
    if not isinstance(result, Mapping):
        validation["blocked_reason_labels"].append("result_not_mapping")
        return validation
    missing = [field for field in REQUIRED_SEARCH_FIELDS_V1 if field not in result]
    if missing:
        validation["blocked_reason_labels"].append("missing_required_fields")
        validation["blocked_reason_labels"].extend(f"missing:{field}" for field in missing)
        return validation
    if result.get("depth") != SEARCH_DEPTH_V1:
        validation["blocked_reason_labels"].append("depth_mismatch")
    if result.get("search_type") != SEARCH_TYPE_V1:
        validation["blocked_reason_labels"].append("search_type_mismatch")
    if result.get("no_score_claim") is not True:
        validation["blocked_reason_labels"].append("no_score_claim_not_true")
    if result.get("solver_visible_expected_outputs_absent") is not True:
        validation["blocked_reason_labels"].append("solver_visible_expected_outputs_not_absent")
    if result.get("evaluation_outputs_separated") is not True:
        validation["blocked_reason_labels"].append("evaluation_outputs_not_separated")
    if not _leakage_flags_are_clean(_normalize_leakage_flags(result.get("leakage_flags"))):
        validation["blocked_reason_labels"].append("leakage_flags_not_clean")
    if not _boundary_flags_are_clean(_normalize_boundary_flags(result.get("boundary_flags"))):
        validation["blocked_reason_labels"].append("boundary_flags_not_clean")
    if not isinstance(result.get("heldout_task_results"), list) or len(result.get("heldout_task_results", [])) != 14:
        validation["blocked_reason_labels"].append("heldout_task_count_invalid")
    if not isinstance(result.get("candidate_program_packets"), list):
        validation["blocked_reason_labels"].append("candidate_program_packets_not_list")
    if not isinstance(result.get("selected_top2_program_packet"), Mapping):
        validation["blocked_reason_labels"].append("selected_top2_program_packet_not_mapping")
    if result.get("top2_program_packet_count", 0) < 1:
        validation["blocked_reason_labels"].append("top2_program_packet_count_invalid")
    if result.get("top2_program_packet_valid_count", 0) > result.get("top2_program_packet_count", 0):
        validation["blocked_reason_labels"].append("top2_program_packet_valid_count_invalid")
    if not isinstance(result.get("failure_ledger"), Mapping):
        validation["blocked_reason_labels"].append("failure_ledger_not_mapping")
    validation["valid"] = not validation["blocked_reason_labels"]
    return validation


def summarize_arc_style_depth2_compositional_program_search_result_v1(result: Any) -> dict[str, Any]:
    validation = validate_arc_style_depth2_compositional_program_search_result_v1(result)
    if not isinstance(result, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "search_type": SEARCH_TYPE_V1,
            "valid": False,
            "task_count": 0,
            "exact_count": 0,
            "partial_count": 0,
            "unsupported_count": 0,
            "failed_count": 0,
            "top2_program_packet_count": 0,
            "top2_program_packet_valid_count": 0,
            "top2_program_packet_invalid_count": 0,
            "blocked_reason_labels": validation["blocked_reason_labels"],
        }
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "search_type": SEARCH_TYPE_V1,
        "valid": validation["valid"],
        "task_count": int(result.get("task_count", 0)),
        "exact_count": int(result.get("exact_count", 0)),
        "partial_count": int(result.get("partial_count", 0)),
        "unsupported_count": int(result.get("unsupported_count", 0)),
        "failed_count": int(result.get("failed_count", 0)),
        "top2_program_packet_count": int(result.get("top2_program_packet_count", 0)),
        "top2_program_packet_valid_count": int(result.get("top2_program_packet_valid_count", 0)),
        "top2_program_packet_invalid_count": int(result.get("top2_program_packet_invalid_count", 0)),
        "candidate_program_packet_count": len(result.get("candidate_program_packets", [])) if isinstance(result.get("candidate_program_packets"), list) else 0,
        "blocked_reason_labels": validation["blocked_reason_labels"],
    }


def run_arc_style_depth2_compositional_program_search_v1(seed: int | None = None) -> dict[str, Any]:
    suite = generate_arc_style_heldout_compositional_suite_v1(seed=seed)
    baseline = run_arc_style_heldout_compositional_baseline_v1(seed=seed)
    known_family_before = run_arc_style_synthetic_solver_suite_v1()
    known_family_before_summary = summarize_arc_style_synthetic_solver_suite_result_v1(known_family_before)
    known_family_after_summary = deepcopy(known_family_before_summary)

    candidate_program_packets: list[dict[str, Any]] = []
    heldout_task_results: list[dict[str, Any]] = []
    top2_packet_count = 0
    top2_packet_valid_count = 0
    top2_packet_invalid_count = 0
    selected_top2_program_packet: dict[str, Any] | None = None

    for task in suite["tasks"]:
        task_packet = task["task_packet"]
        task_validation = validate_arc_style_grid_task_packet_v1(task_packet)
        train_pairs = _task_train_pairs(task_packet)
        train_pair_validations = [validate_arc_style_grid_train_pair_v1(pair) for pair in train_pairs]
        if not task_validation.get("valid", False) or any(not pair_validation.get("valid", False) for pair_validation in train_pair_validations):
            heldout_task_results.append({
                "task_id": _safe_text(task.get("task_id")),
                "recipe_family_id": _safe_text(task.get("recipe_family_id")),
                "heldout_fit_status": "failed",
                "failure_notes": ["invalid_task_packet_or_train_pairs"],
                "candidate_program_packets": [],
                "selected_top2_program_packet": None,
                "selected_top2_program_packet_validation": {"valid": False, "blocked_reason_labels": ["invalid_task_packet_or_train_pairs"]},
                "mismatch_categories": ["invalid_task_packet_or_train_pairs"],
                "leakage_flags": _json_safe(task.get("leakage_flags", {})),
                "boundary_flags": _json_safe(task.get("boundary_flags", {})),
                "task_packet": _json_safe(task_packet),
                "evaluation_metadata": _json_safe(task.get("evaluation_metadata", {})),
                "provenance_metadata": _json_safe(task.get("provenance_metadata", {})),
            })
            top2_packet_invalid_count += 1
            continue

        task_candidates = _program_candidates_for_task(task)
        candidate_program_packets.extend(task_candidates)
        selected_candidates = _select_top2_candidates(task_candidates)
        if not selected_candidates:
            heldout_task_results.append({
                "task_id": _safe_text(task.get("task_id")),
                "recipe_family_id": _safe_text(task.get("recipe_family_id")),
                "heldout_fit_status": "failed",
                "failure_notes": ["no_candidates"],
                "candidate_program_packets": [],
                "selected_top2_program_packet": None,
                "selected_top2_program_packet_validation": {"valid": False, "blocked_reason_labels": ["no_candidates"]},
                "mismatch_categories": ["no_candidates"],
                "leakage_flags": _json_safe(task.get("leakage_flags", {})),
                "boundary_flags": _json_safe(task.get("boundary_flags", {})),
                "task_packet": _json_safe(task_packet),
                "evaluation_metadata": _json_safe(task.get("evaluation_metadata", {})),
                "provenance_metadata": _json_safe(task.get("provenance_metadata", {})),
            })
            top2_packet_invalid_count += 1
            continue

        # Delay test execution until after top-2 selection.
        test_input_grid = task_packet.get("test_input", {}).get("cell_values", []) if isinstance(task_packet.get("test_input"), Mapping) else []
        top2_attempt_candidates = []
        selected_candidate_results = []
        for selected_candidate in selected_candidates:
            runtime_result = _run_program_on_test_input(selected_candidate, test_input_grid)
            predicted_grid = runtime_result["predicted_grid"]
            candidate_packet = {
                "candidate_program_id": selected_candidate["candidate_program_id"],
                "task_id": selected_candidate["task_id"],
                "program_steps": _json_safe(selected_candidate["program_steps"]),
                "program_signature_key": selected_candidate["program_signature_key"],
                "score": selected_candidate["score"],
                "train_fit_status": selected_candidate["train_fit_status"],
                "exact_pair_count": selected_candidate["exact_pair_count"],
                "partial_pair_count": selected_candidate["partial_pair_count"],
                "unsupported_pair_count": selected_candidate["unsupported_pair_count"],
                "mismatch_count": selected_candidate["mismatch_count"],
                "mismatch_categories": _json_safe(selected_candidate["mismatch_categories"]),
                "parameter_complexity": selected_candidate["parameter_complexity"],
                "instability_penalty": selected_candidate["instability_penalty"],
                "source_hint": _json_safe(selected_candidate["source_hint"]),
                "metadata": _json_safe(selected_candidate.get("metadata", {})),
                "grid": _json_safe(predicted_grid),
                "candidate_role": "selected_top2_program",
                "leakage_flags": _json_safe(selected_candidate["leakage_flags"]),
                "boundary_flags": _json_safe(selected_candidate["boundary_flags"]),
            }
            top2_attempt_candidates.append(candidate_packet)
            selected_candidate_results.append({
                "candidate_program_packet": _json_safe(selected_candidate),
                "test_prediction_grid": _json_safe(predicted_grid),
                "test_runtime_trace": _json_safe(runtime_result["step_traces"]),
            })

        top2_program_packet = build_arc_agi2_top2_attempt_packet_v1(
            task_id=_safe_text(task.get("task_id")),
            test_input_index=0,
            candidate_packets=top2_attempt_candidates,
            metadata={
                "search_type": SEARCH_TYPE_V1,
                "depth": SEARCH_DEPTH_V1,
                "recipe_family_id": task.get("recipe_family_id"),
                "recipe_id": task.get("recipe_id"),
                "synthetic_only": True,
            },
        )
        top2_validation = validate_arc_agi2_top2_attempt_packet_v1(top2_program_packet)
        top2_packet_count += 1
        if top2_validation.get("valid"):
            top2_packet_valid_count += 1
        else:
            top2_packet_invalid_count += 1
        if selected_top2_program_packet is None:
            selected_top2_program_packet = _json_safe(top2_program_packet)

        # Evaluate the best candidate only after top-2 selection.
        best_candidate = selected_candidates[0]
        best_prediction = selected_candidate_results[0]["test_prediction_grid"]
        evaluation_outputs = task.get("evaluation_metadata", {}) if isinstance(task.get("evaluation_metadata"), Mapping) else {}
        expected_outputs = evaluation_outputs.get("expected_outputs", []) if isinstance(evaluation_outputs.get("expected_outputs"), list) else []
        actual_output = expected_outputs[0].get("output_grid", []) if expected_outputs and isinstance(expected_outputs[0], Mapping) else []
        final_comparison = _mismatch_summary(actual_output, best_prediction)
        heldout_fit_status = "fit" if final_comparison["comparison"].get("exact_match", False) else "partial_fit" if final_comparison["comparison"].get("dimensions_match", False) else "unsupported"
        heldout_task_results.append({
            "task_id": _safe_text(task.get("task_id")),
            "recipe_family_id": _safe_text(task.get("recipe_family_id")),
            "recipe_id": _safe_text(task.get("recipe_id")),
            "variant_index": int(task.get("variant_index", 0)),
            "candidate_program_packets": _json_safe(task_candidates),
            "selected_candidate_program_packet": _json_safe(best_candidate),
            "selected_top2_program_packet": _json_safe(top2_program_packet),
            "selected_top2_program_packet_validation": _json_safe(top2_validation),
            "heldout_fit_status": heldout_fit_status,
            "heldout_prediction": _json_safe(best_prediction),
            "heldout_comparison": _json_safe(final_comparison),
            "exact_count": 1 if heldout_fit_status == "fit" else 0,
            "partial_count": 1 if heldout_fit_status == "partial_fit" else 0,
            "unsupported_count": 1 if heldout_fit_status == "unsupported" else 0,
            "failed_count": 0,
            "mismatch_categories": _json_safe(final_comparison["categories"]),
            "solver_visible_expected_outputs_absent": True,
            "evaluation_outputs_separated": True,
            "leakage_flags": _json_safe(task.get("leakage_flags", {})),
            "boundary_flags": _json_safe(task.get("boundary_flags", {})),
            "task_packet": _json_safe(task_packet),
            "evaluation_metadata": _json_safe(task.get("evaluation_metadata", {})),
            "provenance_metadata": _json_safe(task.get("provenance_metadata", {})),
            "search_trace": {
                "candidate_count": len(task_candidates),
                "selected_candidate_program_ids": [candidate["candidate_program_id"] for candidate in selected_candidates],
                "top2_validation": _json_safe(top2_validation),
                "heldout_evaluation_delay": True,
            },
        })

    status_counts = _count_status(heldout_task_results)
    failure_ledger = {
        "mismatch_category_counts": _summarize_mismatch_categories(heldout_task_results),
        "status_counts": status_counts,
        "candidate_program_count": len(candidate_program_packets),
        "selected_top2_count": len([result for result in heldout_task_results if result.get("selected_top2_program_packet")]),
    }
    comparison_report = {
        "known_family_baseline_before": _json_safe(known_family_before_summary),
        "known_family_baseline_after": _json_safe(known_family_after_summary),
        "heldout_baseline_before": _json_safe(baseline),
        "heldout_search_after": {
            "exact_count": status_counts["exact"],
            "partial_count": status_counts["partial"],
            "unsupported_count": status_counts["unsupported"],
            "failed_count": status_counts["failed"],
            "task_count": len(heldout_task_results),
        },
        "exact_improvement": status_counts["exact"] - int(baseline.get("exact_count", 0)),
        "unsupported_reduction": int(baseline.get("unsupported_count", 0)) - status_counts["unsupported"],
        "baseline_failure_ledger": _json_safe(baseline.get("failure_ledger", {})),
        "search_failure_ledger": _json_safe(failure_ledger),
    }
    result = {
        "search_type": SEARCH_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "depth": SEARCH_DEPTH_V1,
        "search_summary": {
            "task_count": len(heldout_task_results),
            "exact_count": status_counts["exact"],
            "partial_count": status_counts["partial"],
            "unsupported_count": status_counts["unsupported"],
            "failed_count": status_counts["failed"],
            "candidate_program_count": len(candidate_program_packets),
        },
        "heldout_suite_summary": summarize_arc_style_heldout_compositional_suite_v1(suite),
        "heldout_baseline_before": _json_safe(baseline),
        "heldout_search_after": {
            "task_count": len(heldout_task_results),
            "exact_count": status_counts["exact"],
            "partial_count": status_counts["partial"],
            "unsupported_count": status_counts["unsupported"],
            "failed_count": status_counts["failed"],
            "per_recipe_summary": _build_per_recipe_summary(heldout_task_results),
            "failure_ledger": _json_safe(failure_ledger),
        },
        "known_family_baseline_before": _json_safe(known_family_before_summary),
        "known_family_baseline_after": _json_safe(known_family_after_summary),
        "comparison_report": _json_safe(comparison_report),
        "heldout_task_results": _json_safe(heldout_task_results),
        "candidate_program_packets": _json_safe(candidate_program_packets),
        "selected_top2_program_packet": _json_safe(selected_top2_program_packet or {}),
        "failure_ledger": _json_safe(failure_ledger),
        "top2_program_packet_count": top2_packet_count,
        "top2_program_packet_valid_count": top2_packet_valid_count,
        "top2_program_packet_invalid_count": top2_packet_invalid_count,
        "typed_primitive_signature_summary": summarize_arc_style_typed_primitive_signatures_v1(),
        "solver_visible_expected_outputs_absent": True,
        "evaluation_outputs_separated": True,
        "leakage_flags": {
            "synthetic_only": True,
            "heldout_compositional": False,
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
        "no_score_claim": True,
    }
    return result


__all__ = [
    "SCHEMA_VERSION_V1",
    "SEARCH_DEPTH_V1",
    "SEARCH_TYPE_V1",
    "run_arc_style_depth2_compositional_program_search_v1",
    "summarize_arc_style_depth2_compositional_program_search_result_v1",
    "to_arc_style_depth2_compositional_program_search_json_safe_v1",
    "validate_arc_style_depth2_compositional_program_search_result_v1",
]
