"""WESLR ARC-style grid solver dry run Phase 3.

Phase 3 only: bounded candidate generation and deterministic dry-run over the
internal synthetic toy tasks from Phase 1/2.

This module does not implement public ARC ingestion, solver runtime beyond the
bounded dry run, competition submission, benchmark scoring claims, provider
calls, model calls, payment calls, ChatResponder wiring, website/runtime
wiring, or `.weslr` writes.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from typing import Any, Mapping, Sequence

from weslr.arc_style_grid_adapter_phase2 import (
    ADAPTER_TYPE_V1 as PHASE2_ADAPTER_TYPE_V1,
    PHASE_NUMBER_V1 as PHASE2_NUMBER_V1,
    SUPPORTED_EXECUTABLE_PRIMITIVE_IDS_V1,
    build_arc_style_phase2_adapter_packet_v1,
    extract_arc_style_object_candidates_v1,
    summarize_arc_style_phase2_adapter_packet_v1,
    to_arc_style_phase2_adapter_json_safe_v1,
    validate_arc_style_phase2_adapter_packet_v1,
    validate_arc_style_train_pair_with_candidate_v1,
)
from weslr.arc_style_grid_schema_helpers import (
    SCHEMA_VERSION_V1 as PHASE1_SCHEMA_VERSION_V1,
    TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
    TOY_TASK_TYPES_V1,
    build_internal_arc_style_grid_toy_tasks_v1,
    summarize_arc_style_grid_task_packet_v1,
    to_arc_style_grid_task_json_safe_v1,
    validate_arc_style_grid_task_packet_v1,
)

SCHEMA_VERSION_V1 = "ArcStyleGridSolverDryRunV1"
SOLVER_TYPE_V1 = "arc_style_grid_solver_dry_run_v1"
PHASE_NUMBER_V1 = 3
MAX_CANDIDATES_PER_TASK_V1 = 2
MAX_PRIMITIVE_SEQUENCE_DEPTH_V1 = 2

REQUIRED_TASK_RESULT_FIELDS_V1 = (
    "task_id",
    "task_source",
    "toy_task_type",
    "candidate_count",
    "selected_candidate_id",
    "selected_primitive_sequence",
    "train_fit_status",
    "exact_match_count",
    "partial_match_count",
    "unsupported_count",
    "rejected_candidates",
    "failure_notes",
    "trace",
    "no_score_claim",
)

REQUIRED_RESULT_FIELDS_V1 = (
    "solver_type",
    "phase_number",
    "schema_version",
    "task_count",
    "candidate_count",
    "selected_exact_match_count",
    "selected_partial_match_count",
    "selected_unsupported_count",
    "task_results",
    "failure_ledger",
    "failure_notes",
    "trace",
    "no_score_claim",
)

FAILURE_CATEGORIES_V1 = (
    "failed_primitive",
    "failed_object_extraction",
    "failed_color_mapping",
    "overfit_rule",
    "underfit_rule",
    "ambiguity",
    "unsupported_candidate",
    "missed_transformation_family",
    "repeated_failure_category",
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


def to_arc_style_solver_dry_run_json_safe_v1(value: Any) -> Any:
    safe = _json_safe(value)
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def _task_type(task_packet: Mapping[str, Any]) -> str:
    trace = task_packet.get("trace", {}) if isinstance(task_packet.get("trace"), Mapping) else {}
    return _safe_text(trace.get("toy_task_type"))


def _task_id(task_packet: Mapping[str, Any]) -> str:
    return _safe_text(task_packet.get("task_id"))


def _input_grid(task_packet: Mapping[str, Any]) -> list[list[Any]]:
    train_pairs = task_packet.get("train_pairs", []) if isinstance(task_packet.get("train_pairs"), list) else []
    if not train_pairs:
        return []
    first = train_pairs[0]
    input_grid = first.get("input_grid") if isinstance(first, Mapping) else []
    return [list(row) for row in input_grid] if isinstance(input_grid, list) else []


def _output_grid(task_packet: Mapping[str, Any]) -> list[list[Any]]:
    train_pairs = task_packet.get("train_pairs", []) if isinstance(task_packet.get("train_pairs"), list) else []
    if not train_pairs:
        return []
    first = train_pairs[0]
    output_grid = first.get("output_grid") if isinstance(first, Mapping) else []
    return [list(row) for row in output_grid] if isinstance(output_grid, list) else []


def _background_value(task_packet: Mapping[str, Any]) -> Any:
    train_pairs = task_packet.get("train_pairs", []) if isinstance(task_packet.get("train_pairs"), list) else []
    if not train_pairs:
        return None
    first = train_pairs[0]
    metadata = first.get("input_grid_metadata", {}) if isinstance(first, Mapping) else {}
    return metadata.get("background_color") if isinstance(metadata, Mapping) else None


def _non_background_value(grid: Sequence[Sequence[Any]], background_value: Any) -> Any:
    counts = Counter(cell for row in grid for cell in row if cell != background_value)
    if counts:
        return counts.most_common(1)[0][0]
    counts = Counter(cell for row in grid for cell in row)
    return counts.most_common(1)[0][0] if counts else None


def _changed_cells(input_grid: Sequence[Sequence[Any]], output_grid: Sequence[Sequence[Any]]) -> list[tuple[int, int, Any, Any]]:
    changed: list[tuple[int, int, Any, Any]] = []
    height = max(len(input_grid), len(output_grid))
    width = max((len(row) for row in input_grid), default=0)
    width = max(width, max((len(row) for row in output_grid), default=0))
    for row_index in range(height):
        for column_index in range(width):
            input_value = input_grid[row_index][column_index] if row_index < len(input_grid) and column_index < len(input_grid[row_index]) else None
            output_value = output_grid[row_index][column_index] if row_index < len(output_grid) and column_index < len(output_grid[row_index]) else None
            if input_value != output_value:
                changed.append((row_index, column_index, input_value, output_value))
    return changed


def _infer_recolor_parameters(input_grid: Sequence[Sequence[Any]], output_grid: Sequence[Sequence[Any]]) -> tuple[Any, Any] | None:
    changed = _changed_cells(input_grid, output_grid)
    if not changed:
        return None
    from_values = {item[2] for item in changed}
    to_values = {item[3] for item in changed}
    if len(from_values) == 1 and len(to_values) == 1:
        return next(iter(from_values)), next(iter(to_values))
    return None


def _infer_move_parameters(input_grid: Sequence[Sequence[Any]], output_grid: Sequence[Sequence[Any]], background_value: Any) -> dict[str, Any] | None:
    input_cells = [(row_index, column_index) for row_index, row in enumerate(input_grid) for column_index, cell in enumerate(row) if cell != background_value]
    output_cells = [(row_index, column_index) for row_index, row in enumerate(output_grid) for column_index, cell in enumerate(row) if cell != background_value]
    if not input_cells or len(input_cells) != len(output_cells):
        return None
    delta_rows = {out_row - in_row for (in_row, _), (out_row, _) in zip(sorted(input_cells), sorted(output_cells))}
    delta_columns = {out_column - in_column for (_, in_column), (_, out_column) in zip(sorted(input_cells), sorted(output_cells))}
    if len(delta_rows) != 1 or len(delta_columns) != 1:
        return None
    delta_row = next(iter(delta_rows))
    delta_column = next(iter(delta_columns))
    if delta_row and delta_column:
        return None
    if delta_row > 0:
        direction = "down"
        steps = delta_row
    elif delta_row < 0:
        direction = "up"
        steps = -delta_row
    elif delta_column > 0:
        direction = "right"
        steps = delta_column
    elif delta_column < 0:
        direction = "left"
        steps = -delta_column
    else:
        return None
    object_values = [cell for row in input_grid for cell in row if cell != background_value]
    object_value = object_values[0] if object_values else None
    return {"direction": direction, "steps": steps, "object_value": object_value, "background_value": background_value}


def _build_candidate_packet(
    *,
    task_id: str,
    primitive_id: str,
    primitive_sequence: Sequence[Any],
    source: str,
    required_constraints: Sequence[str],
    unsupported_assumptions: Sequence[str],
    generation_trace: Mapping[str, Any],
    bounded_depth: int,
    is_executable: bool,
    candidate_rank: int,
    candidate_role: str,
) -> dict[str, Any]:
    return {
        "candidate_id": f"{task_id}:{primitive_id}:{candidate_rank}",
        "task_id": task_id,
        "primitive_id": primitive_id,
        "primitive_sequence": [_json_safe(item) for item in primitive_sequence],
        "source": _safe_text(source),
        "required_constraints": [_safe_text(item) for item in required_constraints],
        "unsupported_assumptions": [_safe_text(item) for item in unsupported_assumptions],
        "generation_trace": _json_safe(dict(generation_trace)),
        "bounded_depth": int(bounded_depth),
        "is_executable": bool(is_executable),
        "candidate_rank": int(candidate_rank),
        "candidate_role": _safe_text(candidate_role),
        "train_fit_status": "unknown",
    }


def generate_arc_style_candidate_rules_v1(task_packet: Mapping[str, Any], object_extraction: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    task_id = _task_id(task_packet)
    task_type = _task_type(task_packet)
    input_grid = _input_grid(task_packet)
    output_grid = _output_grid(task_packet)
    background_value = _background_value(task_packet)
    if background_value is None and input_grid:
        background_value = _non_background_value(input_grid, None)
    if object_extraction is None:
        object_extraction = extract_arc_style_object_candidates_v1(input_grid, task_id=task_id)
    trace_base = {
        "schema_version": SCHEMA_VERSION_V1,
        "task_id": task_id,
        "task_type": task_type,
        "phase1_schema_version": PHASE1_SCHEMA_VERSION_V1,
        "phase2_adapter_type": PHASE2_ADAPTER_TYPE_V1,
        "phase2_number": PHASE2_NUMBER_V1,
        "max_candidates_per_task": MAX_CANDIDATES_PER_TASK_V1,
        "max_primitive_sequence_depth": MAX_PRIMITIVE_SEQUENCE_DEPTH_V1,
        "object_extraction_counts": {
            "connected_components": len(object_extraction.get("object_candidates", [])),
            "color_groups": len(object_extraction.get("color_group_candidates", [])),
            "symmetry_hints": len(object_extraction.get("symmetry_hints", [])),
            "line_hints": len(object_extraction.get("line_hints", [])),
            "border_frame_hints": len(object_extraction.get("border_frame_hints", [])),
        },
        "internal_synthetic_only": True,
        "no_arc_dataset_ingestion": True,
        "no_public_arc_sample_ingestion": True,
        "no_solver_runtime": True,
        "no_candidate_search": False,
        "deterministic_order": True,
    }

    candidates: list[dict[str, Any]] = []
    if task_type == "copy_grid":
        candidates.append(
            _build_candidate_packet(
                task_id=task_id,
                primitive_id="copy",
                primitive_sequence=[{"primitive_id": "copy", "parameters": {}}],
                source="internal_toy_exact_copy",
                required_constraints=["grid_shape_preserved"],
                unsupported_assumptions=[],
                generation_trace={**trace_base, "candidate_kind": "exact", "failure_family": None},
                bounded_depth=1,
                is_executable=True,
                candidate_rank=0,
                candidate_role="primary_exact",
            )
        )
        fallback_value = background_value if background_value is not None else _non_background_value(input_grid, None)
        candidates.append(
            _build_candidate_packet(
                task_id=task_id,
                primitive_id="fill",
                primitive_sequence=[{"primitive_id": "fill", "parameters": {"fill_value": fallback_value, "fill_entire_grid": True}}],
                source="internal_toy_bounded_fallback",
                required_constraints=["whole_grid_fill"],
                unsupported_assumptions=["copy_like_input_not_assumed"],
                generation_trace={**trace_base, "candidate_kind": "fallback", "failure_family": "overfit_rule", "fallback_reason": "whole_grid_fill_not_matching_copy"},
                bounded_depth=1,
                is_executable=True,
                candidate_rank=1,
                candidate_role="fallback_overfit",
            )
        )
    elif task_type == "recolor_symbol":
        recolor_parameters = _infer_recolor_parameters(input_grid, output_grid)
        if recolor_parameters is not None:
            from_value, to_value = recolor_parameters
            candidates.append(
                _build_candidate_packet(
                    task_id=task_id,
                    primitive_id="recolor",
                    primitive_sequence=[{"primitive_id": "recolor", "parameters": {"from_value": from_value, "to_value": to_value}}],
                    source="internal_toy_exact_recolor",
                    required_constraints=["single_symbol_delta"],
                    unsupported_assumptions=[],
                    generation_trace={**trace_base, "candidate_kind": "exact", "failure_family": None, "recolor_from": from_value, "recolor_to": to_value},
                    bounded_depth=1,
                    is_executable=True,
                    candidate_rank=0,
                    candidate_role="primary_exact",
                )
            )
        candidates.append(
            _build_candidate_packet(
                task_id=task_id,
                primitive_id="copy",
                primitive_sequence=[{"primitive_id": "copy", "parameters": {}}],
                source="internal_toy_bounded_fallback",
                required_constraints=["color_change_required"],
                unsupported_assumptions=["no_color_change_assumed"],
                generation_trace={**trace_base, "candidate_kind": "fallback", "failure_family": "underfit_rule", "fallback_reason": "copy_cannot_recolor"},
                bounded_depth=1,
                is_executable=True,
                candidate_rank=1,
                candidate_role="fallback_underfit",
            )
        )
    elif task_type == "move_single_object":
        move_parameters = _infer_move_parameters(input_grid, output_grid, background_value)
        if move_parameters is not None:
            candidates.append(
                _build_candidate_packet(
                    task_id=task_id,
                    primitive_id="move",
                    primitive_sequence=[{"primitive_id": "move", "parameters": move_parameters}],
                    source="internal_toy_exact_move",
                    required_constraints=["single_object_translation"],
                    unsupported_assumptions=[],
                    generation_trace={**trace_base, "candidate_kind": "exact", "failure_family": None, **move_parameters},
                    bounded_depth=1,
                    is_executable=True,
                    candidate_rank=0,
                    candidate_role="primary_exact",
                )
            )
        candidates.append(
            _build_candidate_packet(
                task_id=task_id,
                primitive_id="copy",
                primitive_sequence=[{"primitive_id": "copy", "parameters": {}}],
                source="internal_toy_bounded_fallback",
                required_constraints=["movement_required"],
                unsupported_assumptions=["no_movement_assumed"],
                generation_trace={**trace_base, "candidate_kind": "fallback", "failure_family": "underfit_rule", "fallback_reason": "copy_cannot_move_object"},
                bounded_depth=1,
                is_executable=True,
                candidate_rank=1,
                candidate_role="fallback_underfit",
            )
        )
    elif task_type == "complete_symmetry":
        candidates.append(
            _build_candidate_packet(
                task_id=task_id,
                primitive_id="complete_symmetry",
                primitive_sequence=[{"primitive_id": "complete_symmetry", "parameters": {"axes": ["horizontal", "vertical"], "background_value": background_value}}],
                source="internal_toy_exact_symmetry",
                required_constraints=["mirror_completion"],
                unsupported_assumptions=[],
                generation_trace={**trace_base, "candidate_kind": "exact", "failure_family": None, "axes": ["horizontal", "vertical"]},
                bounded_depth=1,
                is_executable=True,
                candidate_rank=0,
                candidate_role="primary_exact",
            )
        )
        candidates.append(
            _build_candidate_packet(
                task_id=task_id,
                primitive_id="copy",
                primitive_sequence=[{"primitive_id": "copy", "parameters": {}}],
                source="internal_toy_bounded_fallback",
                required_constraints=["mirror_completion_required"],
                unsupported_assumptions=["no_mirroring_assumed"],
                generation_trace={**trace_base, "candidate_kind": "fallback", "failure_family": "underfit_rule", "fallback_reason": "copy_cannot_complete_symmetry"},
                bounded_depth=1,
                is_executable=True,
                candidate_rank=1,
                candidate_role="fallback_underfit",
            )
        )
    elif task_type == "fill":
        fill_value = _non_background_value(output_grid, background_value)
        if fill_value is None:
            fill_value = _non_background_value(input_grid, background_value)
        candidates.append(
            _build_candidate_packet(
                task_id=task_id,
                primitive_id="fill",
                primitive_sequence=[{"primitive_id": "fill", "parameters": {"fill_value": fill_value, "fill_entire_grid": True}}],
                source="internal_toy_exact_fill",
                required_constraints=["uniform_full_grid_fill"],
                unsupported_assumptions=[],
                generation_trace={**trace_base, "candidate_kind": "exact", "failure_family": None, "fill_value": fill_value},
                bounded_depth=1,
                is_executable=True,
                candidate_rank=0,
                candidate_role="primary_exact",
            )
        )
        candidates.append(
            _build_candidate_packet(
                task_id=task_id,
                primitive_id="copy",
                primitive_sequence=[{"primitive_id": "copy", "parameters": {}}],
                source="internal_toy_bounded_fallback",
                required_constraints=["full_fill_not_assumed"],
                unsupported_assumptions=["full_fill_not_assumed"],
                generation_trace={**trace_base, "candidate_kind": "fallback", "failure_family": "underfit_rule", "fallback_reason": "copy_cannot_fill"},
                bounded_depth=1,
                is_executable=True,
                candidate_rank=1,
                candidate_role="fallback_underfit",
            )
        )
    elif task_type == "border_frame_fill":
        fill_value = _non_background_value(output_grid, background_value)
        if fill_value is None:
            fill_value = _non_background_value(input_grid, background_value)
        candidates.append(
            _build_candidate_packet(
                task_id=task_id,
                primitive_id="fill",
                primitive_sequence=[{"primitive_id": "fill", "parameters": {"fill_value": fill_value, "fill_entire_grid": True}}],
                source="internal_toy_exact_fill",
                required_constraints=["uniform_full_grid_fill"],
                unsupported_assumptions=[],
                generation_trace={**trace_base, "candidate_kind": "exact", "failure_family": None, "fill_value": fill_value},
                bounded_depth=1,
                is_executable=True,
                candidate_rank=0,
                candidate_role="primary_exact",
            )
        )
        candidates.append(
            _build_candidate_packet(
                task_id=task_id,
                primitive_id="border_frame",
                primitive_sequence=[{"primitive_id": "border_frame", "parameters": {"frame_value": fill_value, "fill_entire_grid": False, "thickness": 1}}],
                source="internal_toy_bounded_fallback",
                required_constraints=["border_only_not_full_fill"],
                unsupported_assumptions=["full_grid_fill_not_assumed"],
                generation_trace={**trace_base, "candidate_kind": "fallback", "failure_family": "missed_transformation_family", "fallback_reason": "border_frame_only_not_full_fill"},
                bounded_depth=1,
                is_executable=True,
                candidate_rank=1,
                candidate_role="fallback_missed_family",
            )
        )
    else:
        candidates.append(
            _build_candidate_packet(
                task_id=task_id,
                primitive_id="copy",
                primitive_sequence=[{"primitive_id": "copy", "parameters": {}}],
                source="internal_toy_bounded_fallback",
                required_constraints=["task_family_unknown"],
                unsupported_assumptions=["ambiguity_present"],
                generation_trace={**trace_base, "candidate_kind": "fallback", "failure_family": "ambiguity", "fallback_reason": "task_type_not_supported"},
                bounded_depth=1,
                is_executable=True,
                candidate_rank=0,
                candidate_role="fallback_ambiguity",
            )
        )
        candidates.append(
            _build_candidate_packet(
                task_id=task_id,
                primitive_id="fill",
                primitive_sequence=[{"primitive_id": "fill", "parameters": {"fill_value": background_value, "fill_entire_grid": True}}],
                source="internal_toy_bounded_fallback",
                required_constraints=["task_family_unknown"],
                unsupported_assumptions=["ambiguity_present"],
                generation_trace={**trace_base, "candidate_kind": "fallback", "failure_family": "ambiguity", "fallback_reason": "task_type_not_supported"},
                bounded_depth=1,
                is_executable=True,
                candidate_rank=1,
                candidate_role="fallback_ambiguity",
            )
        )

    return candidates[:MAX_CANDIDATES_PER_TASK_V1]


def _candidate_validation_ranking(candidate_result: Mapping[str, Any]) -> tuple[int, int, int, int, int, int]:
    exact = 1 if candidate_result.get("exact_match") else 0
    unsupported = 1 if candidate_result.get("unsupported_candidate") else 0
    mismatch_count = int(candidate_result.get("mismatch_count", 10**6))
    partial = 1 if candidate_result.get("partial_match_count", 0) else 0
    depth = int(candidate_result.get("bounded_depth", 0))
    rank = int(candidate_result.get("candidate_rank", 0))
    return (-exact, unsupported, mismatch_count, -partial, depth, rank)


def _record_failure(ledger: dict[str, Any], *, category: str, task_id: str, candidate_id: str, primitive_id: str, reason: str, mismatch_category: str | None = None) -> None:
    entry = {
        "category": _safe_text(category),
        "task_id": _safe_text(task_id),
        "candidate_id": _safe_text(candidate_id),
        "primitive_id": _safe_text(primitive_id),
        "reason": _safe_text(reason),
        "mismatch_category": _safe_text(mismatch_category) if mismatch_category is not None else None,
    }
    ledger.setdefault("entries", []).append(entry)
    counts = ledger.setdefault("category_counts", {})
    counts[entry["category"]] = counts.get(entry["category"], 0) + 1
    if counts[entry["category"]] > 1:
        repeated = ledger.setdefault("repeated_failure_categories", [])
        if entry["category"] not in repeated:
            repeated.append(entry["category"])


def _evaluate_candidate_against_task(task_packet: Mapping[str, Any], candidate_packet: Mapping[str, Any]) -> dict[str, Any]:
    train_pairs = task_packet.get("train_pairs", []) if isinstance(task_packet.get("train_pairs"), list) else []
    pair_validations: list[dict[str, Any]] = []
    exact_pair_count = 0
    partial_pair_count = 0
    unsupported_pair_count = 0
    mismatch_count = 0
    mismatch_categories: list[str] = []
    failure_localization: list[dict[str, Any]] = []

    for pair in train_pairs:
        validation = validate_arc_style_train_pair_with_candidate_v1(pair, candidate_packet)
        pair_validations.append(validation)
        if validation.get("exact_match"):
            exact_pair_count += 1
        elif validation.get("unsupported_candidate"):
            unsupported_pair_count += 1
        else:
            partial_pair_count += 1
        comparison = validation.get("partial_match_metadata", {}).get("comparison", {}) if isinstance(validation.get("partial_match_metadata"), Mapping) else {}
        mismatch_count += int(comparison.get("value_mismatch_count", 0))
        mismatch_categories.append(_safe_text(validation.get("mismatch_category")))
        failure_localization.append(_json_safe(validation.get("failure_localization", {})))

    exact_match = bool(train_pairs) and exact_pair_count == len(train_pairs)
    unsupported_candidate = bool(train_pairs) and unsupported_pair_count > 0 and not exact_match
    partial_match = bool(train_pairs) and partial_pair_count > 0 and not exact_match and not unsupported_candidate
    if exact_match:
        train_fit_status = "fit"
    elif partial_match:
        train_fit_status = "partial_fit"
    elif unsupported_candidate:
        train_fit_status = "unsupported"
    else:
        train_fit_status = "mismatch"

    return {
        "candidate_id": _safe_text(candidate_packet.get("candidate_id")),
        "task_id": _safe_text(candidate_packet.get("task_id") or task_packet.get("task_id")),
        "primitive_id": _safe_text(candidate_packet.get("primitive_id")),
        "candidate_rank": int(candidate_packet.get("candidate_rank", 0)),
        "bounded_depth": int(candidate_packet.get("bounded_depth", 0)),
        "candidate_packet": _json_safe(candidate_packet),
        "pair_validations": pair_validations,
        "exact_match": exact_match,
        "partial_match": partial_match,
        "unsupported_candidate": unsupported_candidate,
        "train_fit_status": train_fit_status,
        "exact_pair_count": exact_pair_count,
        "partial_match_count": partial_pair_count,
        "unsupported_pair_count": unsupported_pair_count,
        "mismatch_count": mismatch_count,
        "mismatch_categories": sorted({category for category in mismatch_categories if category}),
        "failure_localization": failure_localization,
        "mismatch_category": "exact_match" if exact_match else (mismatch_categories[0] if mismatch_categories else "unsupported_candidate"),
        "selected_primitive_sequence": _json_safe(candidate_packet.get("primitive_sequence", [])),
        "rejection_reason": None,
        "candidate_role": _safe_text(candidate_packet.get("candidate_role")),
        "generation_trace": _json_safe(candidate_packet.get("generation_trace", {})),
        "required_constraints": _json_safe(candidate_packet.get("required_constraints", [])),
        "unsupported_assumptions": _json_safe(candidate_packet.get("unsupported_assumptions", [])),
        "source": _safe_text(candidate_packet.get("source")),
        "is_executable": bool(candidate_packet.get("is_executable", False)),
    }


def build_arc_style_solver_dry_run_result_v1(*, task_results: Sequence[Mapping[str, Any]], failure_ledger: Mapping[str, Any] | None = None, trace: Mapping[str, Any] | None = None) -> dict[str, Any]:
    task_results_out = [_json_safe(item) for item in task_results]
    candidate_count = sum(int(task_result.get("candidate_count", 0)) for task_result in task_results_out if isinstance(task_result, Mapping))
    selected_exact_match_count = sum(1 for task_result in task_results_out if isinstance(task_result, Mapping) and task_result.get("train_fit_status") == "fit")
    selected_partial_match_count = sum(1 for task_result in task_results_out if isinstance(task_result, Mapping) and task_result.get("train_fit_status") == "partial_fit")
    selected_unsupported_count = sum(1 for task_result in task_results_out if isinstance(task_result, Mapping) and task_result.get("train_fit_status") == "unsupported")
    failure_notes: list[str] = []
    for task_result in task_results_out:
        if isinstance(task_result, Mapping):
            for note in task_result.get("failure_notes", []):
                note_text = _safe_text(note)
                if note_text and note_text not in failure_notes:
                    failure_notes.append(note_text)
    result = {
        "solver_type": SOLVER_TYPE_V1,
        "phase_number": PHASE_NUMBER_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "task_count": len(task_results_out),
        "candidate_count": candidate_count,
        "selected_exact_match_count": selected_exact_match_count,
        "selected_partial_match_count": selected_partial_match_count,
        "selected_unsupported_count": selected_unsupported_count,
        "exact_match_count": selected_exact_match_count,
        "partial_match_count": selected_partial_match_count,
        "unsupported_count": selected_unsupported_count,
        "task_results": task_results_out,
        "failure_ledger": _json_safe(dict(failure_ledger or {})),
        "failure_notes": failure_notes,
        "trace": _json_safe({
            "schema_version": SCHEMA_VERSION_V1,
            "phase1_schema_version": PHASE1_SCHEMA_VERSION_V1,
            "phase2_adapter_type": PHASE2_ADAPTER_TYPE_V1,
            "phase2_number": PHASE2_NUMBER_V1,
            "task_count": len(task_results_out),
            "candidate_count": candidate_count,
            "internal_synthetic_only": True,
            "no_arc_dataset_ingestion": True,
            "no_public_arc_sample_ingestion": True,
            "no_solver_runtime": True,
            "bounded_candidate_generation": True,
            "max_candidates_per_task": MAX_CANDIDATES_PER_TASK_V1,
            "max_primitive_sequence_depth": MAX_PRIMITIVE_SEQUENCE_DEPTH_V1,
        } if trace is None else {**trace}),
        "no_score_claim": True,
    }
    return result


def _build_task_result(
    *,
    task_packet: Mapping[str, Any],
    object_extraction: Mapping[str, Any],
    candidate_evaluations: Sequence[Mapping[str, Any]],
    failure_ledger: dict[str, Any],
) -> dict[str, Any]:
    task_id = _task_id(task_packet)
    task_type = _task_type(task_packet)
    exact_candidates = [candidate for candidate in candidate_evaluations if candidate.get("exact_match")]
    partial_candidates = [candidate for candidate in candidate_evaluations if candidate.get("partial_match")]
    unsupported_candidates = [candidate for candidate in candidate_evaluations if candidate.get("unsupported_candidate")]
    selected_candidate = None
    if exact_candidates:
        selected_candidate = sorted(exact_candidates, key=_candidate_validation_ranking)[0]
    elif partial_candidates:
        selected_candidate = sorted(partial_candidates, key=_candidate_validation_ranking)[0]
    elif unsupported_candidates:
        selected_candidate = sorted(unsupported_candidates, key=_candidate_validation_ranking)[0]
    elif candidate_evaluations:
        selected_candidate = sorted(candidate_evaluations, key=_candidate_validation_ranking)[0]

    rejected_candidates: list[dict[str, Any]] = []
    for evaluation in candidate_evaluations:
        if selected_candidate is not None and evaluation.get("candidate_id") == selected_candidate.get("candidate_id"):
            continue
        primitive_id = _safe_text(evaluation.get("primitive_id"))
        mismatch_category = _safe_text(evaluation.get("mismatch_category"))
        role = _safe_text(evaluation.get("candidate_role"))
        if evaluation.get("unsupported_candidate"):
            ledger_category = "unsupported_candidate"
        elif role == "fallback_overfit":
            ledger_category = "overfit_rule"
        elif role == "fallback_underfit":
            ledger_category = "underfit_rule"
        elif role == "fallback_missed_family":
            ledger_category = "missed_transformation_family"
        elif role == "fallback_ambiguity":
            ledger_category = "ambiguity"
        elif primitive_id == "recolor" and mismatch_category != "exact_match":
            ledger_category = "failed_color_mapping"
        elif primitive_id in {"copy", "move", "fill", "complete_symmetry", "border_frame"} and mismatch_category != "exact_match":
            ledger_category = "missed_transformation_family"
        else:
            ledger_category = "failed_primitive"
        reason = evaluation.get("generation_trace", {}).get("failure_family") if isinstance(evaluation.get("generation_trace"), Mapping) else None
        reason_text = _safe_text(reason or mismatch_category)
        rejected_candidates.append(
            {
                "candidate_id": evaluation.get("candidate_id"),
                "primitive_id": primitive_id,
                "mismatch_category": mismatch_category,
                "rejection_reason": reason_text,
                "failure_ledger_category": ledger_category,
                "exact_match": bool(evaluation.get("exact_match")),
                "partial_match": bool(evaluation.get("partial_match")),
                "unsupported_candidate": bool(evaluation.get("unsupported_candidate")),
            }
        )
        _record_failure(
            failure_ledger,
            category=ledger_category,
            task_id=task_id,
            candidate_id=_safe_text(evaluation.get("candidate_id")),
            primitive_id=primitive_id,
            reason=reason_text,
            mismatch_category=mismatch_category,
        )

    selected_primitive_sequence = _json_safe(selected_candidate.get("selected_primitive_sequence", [])) if selected_candidate else []
    if selected_candidate is None:
        train_fit_status = "unsupported"
        selected_candidate_id = None
    else:
        train_fit_status = _safe_text(selected_candidate.get("train_fit_status", "unknown"))
        selected_candidate_id = selected_candidate.get("candidate_id")
    exact_match_count = sum(1 for item in candidate_evaluations if item.get("exact_match"))
    partial_match_count = sum(1 for item in candidate_evaluations if item.get("partial_match"))
    unsupported_count = sum(1 for item in candidate_evaluations if item.get("unsupported_candidate"))
    candidate_count = len(candidate_evaluations)
    failure_notes = []
    for item in rejected_candidates:
        note = item.get("failure_ledger_category")
        if note and note not in failure_notes:
            failure_notes.append(note)
    trace = {
        "schema_version": SCHEMA_VERSION_V1,
        "task_id": task_id,
        "task_type": task_type,
        "phase1_schema_version": PHASE1_SCHEMA_VERSION_V1,
        "phase2_adapter_type": PHASE2_ADAPTER_TYPE_V1,
        "phase2_number": PHASE2_NUMBER_V1,
        "candidate_order": [evaluation.get("candidate_id") for evaluation in candidate_evaluations],
        "selected_candidate_ranking": _candidate_validation_ranking(selected_candidate) if selected_candidate else None,
        "object_extraction_counts": {
            "connected_components": len(object_extraction.get("object_candidates", [])),
            "color_groups": len(object_extraction.get("color_group_candidates", [])),
            "symmetry_hints": len(object_extraction.get("symmetry_hints", [])),
            "line_hints": len(object_extraction.get("line_hints", [])),
            "border_frame_hints": len(object_extraction.get("border_frame_hints", [])),
        },
        "candidate_summary": [
            {
                "candidate_id": evaluation.get("candidate_id"),
                "primitive_id": evaluation.get("primitive_id"),
                "train_fit_status": evaluation.get("train_fit_status"),
                "mismatch_category": evaluation.get("mismatch_category"),
            }
            for evaluation in candidate_evaluations
        ],
        "internal_synthetic_only": True,
        "no_arc_dataset_ingestion": True,
        "no_public_arc_sample_ingestion": True,
        "no_solver_runtime": True,
        "bounded_candidate_generation": True,
        "max_candidates_per_task": MAX_CANDIDATES_PER_TASK_V1,
        "max_primitive_sequence_depth": MAX_PRIMITIVE_SEQUENCE_DEPTH_V1,
    }
    task_result = {
        "task_id": task_id,
        "task_source": _safe_text(task_packet.get("task_source")),
        "toy_task_type": task_type,
        "candidate_count": candidate_count,
        "selected_candidate_id": selected_candidate_id,
        "selected_primitive_sequence": selected_primitive_sequence,
        "train_fit_status": train_fit_status,
        "exact_match_count": exact_match_count,
        "partial_match_count": partial_match_count,
        "unsupported_count": unsupported_count,
        "rejected_candidates": rejected_candidates,
        "failure_notes": failure_notes,
        "trace": trace,
        "no_score_claim": True,
        "object_extraction": _json_safe(object_extraction),
        "candidate_packets": [_json_safe(candidate.get("candidate_packet", {})) for candidate in candidate_evaluations],
        "candidate_evaluations": [_json_safe(candidate) for candidate in candidate_evaluations],
        "failure_ledger_summary": {
            "entries_count": len(failure_ledger.get("entries", [])),
            "category_counts": _json_safe(failure_ledger.get("category_counts", {})),
            "repeated_failure_categories": list(failure_ledger.get("repeated_failure_categories", [])),
        },
    }
    return task_result


def run_arc_style_bounded_solver_dry_run_v1(task_packets: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    tasks = list(task_packets) if task_packets is not None else build_internal_arc_style_grid_toy_tasks_v1()
    task_results: list[dict[str, Any]] = []
    failure_ledger: dict[str, Any] = {
        "entries": [],
        "category_counts": {},
        "repeated_failure_categories": [],
    }

    for task_packet in tasks:
        phase1_validation = validate_arc_style_grid_task_packet_v1(task_packet)
        if not phase1_validation.get("valid"):
            task_id = _task_id(task_packet)
            failure_notes = ["failed_object_extraction", "failed_primitive"]
            _record_failure(
                failure_ledger,
                category="failed_object_extraction",
                task_id=task_id,
                candidate_id=f"{task_id}:invalid_task",
                primitive_id="",
                reason="invalid_phase1_task_packet",
                mismatch_category="invalid_task_packet",
            )
            task_results.append(
                {
                    "task_id": task_id,
                    "task_source": _safe_text(task_packet.get("task_source")),
                    "toy_task_type": _task_type(task_packet),
                    "candidate_count": 0,
                    "selected_candidate_id": None,
                    "selected_primitive_sequence": [],
                    "train_fit_status": "invalid",
                    "exact_match_count": 0,
                    "partial_match_count": 0,
                    "unsupported_count": 0,
                    "rejected_candidates": [],
                    "failure_notes": failure_notes,
                    "trace": {
                        "schema_version": SCHEMA_VERSION_V1,
                        "task_id": task_id,
                        "task_validation": phase1_validation,
                        "internal_synthetic_only": True,
                        "no_arc_dataset_ingestion": True,
                        "no_public_arc_sample_ingestion": True,
                        "no_solver_runtime": True,
                    },
                    "no_score_claim": True,
                    "object_extraction": {},
                    "candidate_packets": [],
                    "candidate_evaluations": [],
                    "failure_ledger_summary": {
                        "entries_count": len(failure_ledger.get("entries", [])),
                        "category_counts": _json_safe(failure_ledger.get("category_counts", {})),
                        "repeated_failure_categories": list(failure_ledger.get("repeated_failure_categories", [])),
                    },
                }
            )
            continue

        object_extraction = extract_arc_style_object_candidates_v1(task_packet.get("test_input"), task_id=_task_id(task_packet))
        if not object_extraction.get("object_candidates"):
            _record_failure(
                failure_ledger,
                category="failed_object_extraction",
                task_id=_task_id(task_packet),
                candidate_id=f"{_task_id(task_packet)}:object-extraction-miss",
                primitive_id="",
                reason="no_object_candidates",
                mismatch_category="object_extraction_empty",
            )
        candidate_packets = generate_arc_style_candidate_rules_v1(task_packet, object_extraction)
        candidate_evaluations = [_evaluate_candidate_against_task(task_packet, candidate) for candidate in candidate_packets]
        task_results.append(
            _build_task_result(
                task_packet=task_packet,
                object_extraction=object_extraction,
                candidate_evaluations=candidate_evaluations,
                failure_ledger=failure_ledger,
            )
        )

    result = build_arc_style_solver_dry_run_result_v1(
        task_results=task_results,
        failure_ledger=failure_ledger,
        trace={
            "schema_version": SCHEMA_VERSION_V1,
            "task_ids": [task_result.get("task_id") for task_result in task_results],
            "toy_task_types": list(TOY_TASK_TYPES_V1),
            "task_source": TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
            "internal_synthetic_only": True,
            "no_arc_dataset_ingestion": True,
            "no_public_arc_sample_ingestion": True,
            "no_solver_runtime": True,
            "bounded_candidate_generation": True,
            "max_candidates_per_task": MAX_CANDIDATES_PER_TASK_V1,
            "max_primitive_sequence_depth": MAX_PRIMITIVE_SEQUENCE_DEPTH_V1,
            "no_score_claim": True,
        },
    )
    result["task_sources"] = [TASK_SOURCE_INTERNAL_SYNTHETIC_V1 for _ in task_results]
    result["toy_task_types"] = list(TOY_TASK_TYPES_V1)
    result["candidate_generation_policy"] = {
        "deterministic_order": True,
        "candidate_rank_strategy": "exact_first_then_lowest_mismatch_then_unsupported",
        "primitive_sequence_depth_limit": MAX_PRIMITIVE_SEQUENCE_DEPTH_V1,
        "candidate_limit_per_task": MAX_CANDIDATES_PER_TASK_V1,
        "supported_primitive_ids": list(SUPPORTED_EXECUTABLE_PRIMITIVE_IDS_V1),
        "internal_synthetic_only": True,
    }
    result["failure_ledger"]["failure_categories"] = list(FAILURE_CATEGORIES_V1)
    return result


def validate_arc_style_solver_dry_run_result_v1(result: Any) -> dict[str, Any]:
    validation = {
        "valid": False,
        "blocked_reason_labels": [],
    }
    if not isinstance(result, Mapping):
        validation["blocked_reason_labels"].append("result_not_mapping")
        return validation
    missing = [field for field in REQUIRED_RESULT_FIELDS_V1 if field not in result]
    if missing:
        validation["blocked_reason_labels"].append("missing_required_fields")
        validation["blocked_reason_labels"].extend(f"missing:{field}" for field in missing)
        return validation
    if result.get("no_score_claim") is not True:
        validation["blocked_reason_labels"].append("no_score_claim_not_true")
    if result.get("solver_type") != SOLVER_TYPE_V1:
        validation["blocked_reason_labels"].append("solver_type_mismatch")
    if result.get("phase_number") != PHASE_NUMBER_V1:
        validation["blocked_reason_labels"].append("phase_number_mismatch")
    if not isinstance(result.get("task_results"), list):
        validation["blocked_reason_labels"].append("task_results_not_list")
    else:
        for task_result in result.get("task_results", []):
            if not isinstance(task_result, Mapping):
                validation["blocked_reason_labels"].append("task_result_not_mapping")
                continue
            missing_task = [field for field in REQUIRED_TASK_RESULT_FIELDS_V1 if field not in task_result]
            if missing_task:
                validation["blocked_reason_labels"].append("task_result_missing_required_fields")
                validation["blocked_reason_labels"].extend(f"task_missing:{field}" for field in missing_task)
            if task_result.get("no_score_claim") is not True:
                validation["blocked_reason_labels"].append(f"task_no_score_claim_not_true:{task_result.get('task_id')}")
            if not isinstance(task_result.get("rejected_candidates"), list):
                validation["blocked_reason_labels"].append(f"task_rejected_candidates_not_list:{task_result.get('task_id')}")
            if not isinstance(task_result.get("candidate_packets"), list):
                validation["blocked_reason_labels"].append(f"task_candidate_packets_not_list:{task_result.get('task_id')}")
    if not isinstance(result.get("failure_ledger"), Mapping):
        validation["blocked_reason_labels"].append("failure_ledger_not_mapping")
    if not isinstance(result.get("trace"), Mapping):
        validation["blocked_reason_labels"].append("trace_not_mapping")
    if not validation["blocked_reason_labels"]:
        validation["valid"] = True
    return validation


def summarize_arc_style_solver_dry_run_result_v1(result: Any) -> dict[str, Any]:
    validation = validate_arc_style_solver_dry_run_result_v1(result)
    if not isinstance(result, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "solver_type": SOLVER_TYPE_V1,
            "phase_number": PHASE_NUMBER_V1,
            "valid": False,
            "task_count": 0,
            "candidate_count": 0,
            "selected_exact_match_count": 0,
            "selected_partial_match_count": 0,
            "selected_unsupported_count": 0,
            "failure_categories": list(FAILURE_CATEGORIES_V1),
            "blocked_reason_labels": validation["blocked_reason_labels"],
        }
    failure_ledger = result.get("failure_ledger", {}) if isinstance(result.get("failure_ledger"), Mapping) else {}
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "solver_type": _safe_text(result.get("solver_type")),
        "phase_number": int(result.get("phase_number", PHASE_NUMBER_V1)),
        "valid": validation["valid"],
        "task_count": int(result.get("task_count", 0)),
        "candidate_count": int(result.get("candidate_count", 0)),
        "selected_exact_match_count": int(result.get("selected_exact_match_count", 0)),
        "selected_partial_match_count": int(result.get("selected_partial_match_count", 0)),
        "selected_unsupported_count": int(result.get("selected_unsupported_count", 0)),
        "exact_match_count": int(result.get("exact_match_count", result.get("selected_exact_match_count", 0))),
        "partial_match_count": int(result.get("partial_match_count", result.get("selected_partial_match_count", 0))),
        "unsupported_count": int(result.get("unsupported_count", result.get("selected_unsupported_count", 0))),
        "task_ids": [task_result.get("task_id") for task_result in result.get("task_results", []) if isinstance(task_result, Mapping)],
        "toy_task_types": _json_safe(result.get("toy_task_types", [])),
        "failure_categories": _json_safe(failure_ledger.get("failure_categories", FAILURE_CATEGORIES_V1)),
        "failure_category_counts": _json_safe(failure_ledger.get("category_counts", {})),
        "repeated_failure_categories": _json_safe(failure_ledger.get("repeated_failure_categories", [])),
        "blocked_reason_labels": validation["blocked_reason_labels"],
    }


__all__ = [
    "SCHEMA_VERSION_V1",
    "SOLVER_TYPE_V1",
    "PHASE_NUMBER_V1",
    "MAX_CANDIDATES_PER_TASK_V1",
    "MAX_PRIMITIVE_SEQUENCE_DEPTH_V1",
    "generate_arc_style_candidate_rules_v1",
    "run_arc_style_bounded_solver_dry_run_v1",
    "build_arc_style_solver_dry_run_result_v1",
    "validate_arc_style_solver_dry_run_result_v1",
    "summarize_arc_style_solver_dry_run_result_v1",
    "to_arc_style_solver_dry_run_json_safe_v1",
]
