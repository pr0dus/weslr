"""WESLR ARC-style synthetic solver-suite integration V1.

Synthetic-only integration of generated ARC-style task families through the
bounded dry-run solver path, with ARC-AGI-2 top-2 attempt conversion and a
failure-ledger summary.

This module does not ingest public ARC data, does not implement a Kaggle
adapter, does not claim any benchmark score, and does not perform provider,
payment, ChatResponder, website/runtime, or `.weslr` operations.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import json
from typing import Any, Mapping, Sequence

from weslr.arc_agi2_submission_contract import (
    build_arc_agi2_attempt_v1,
    build_arc_agi2_submission_packet_v1,
    build_arc_agi2_submission_task_entry_v1,
    build_arc_agi2_top2_attempt_packet_v1,
    validate_arc_agi2_submission_packet_v1,
    validate_arc_agi2_top2_attempt_packet_v1,
)
from weslr.arc_style_grid_adapter_phase2 import SUPPORTED_EXECUTABLE_PRIMITIVE_IDS_V1
from weslr.arc_style_grid_adapter_phase2 import (
    _background_value_from_grid,
    _cells_for_value,
    _dominant_non_background_value,
    _fill_region_from_outer_border,
    _largest_component_cells,
    _line_completion_grid,
    _object_count_to_pattern_grid,
    _reflect_bbox_grid,
    _rotate_bbox_grid,
)
from weslr.arc_style_grid_solver_dry_run import run_arc_style_bounded_solver_dry_run_v1
from weslr.arc_style_synthetic_task_generators import (
    REQUIRED_FAMILIES_V1,
    build_initial_arc_style_synthetic_generator_specs_v1,
    generate_arc_style_synthetic_task_suite_v1,
)

SCHEMA_VERSION_V1 = "ArcStyleSyntheticSolverSuiteV1"
SUITE_ID_V1 = "arc_style_synthetic_solver_suite_v1"

SUPPORTED_SYNTHETIC_FAMILIES_V1 = {
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
}

FAILURE_CATEGORIES_V1 = (
    "unsupported_transformation_family",
    "missing_primitive_executor",
    "candidate_generation_gap",
    "validation_mismatch",
    "ambiguous_candidate_ranking",
    "duplicate_attempt_grid",
    "top2_contract_failure",
    "internal_validation_error",
)

REQUIRED_RESULT_FIELDS_V1 = (
    "suite_id",
    "synthetic_internal_result",
    "generated_task_count",
    "attempted_task_count",
    "top2_packet_count",
    "synthetic_exact_count",
    "synthetic_partial_count",
    "synthetic_unsupported_count",
    "synthetic_failed_count",
    "family_level_summary",
    "failure_ledger",
    "task_results",
    "task_entries",
    "submission_packet",
    "leakage_flags",
    "denied_authority",
    "authority_flags",
    "no_score_claim",
    "official_score_claim",
)

REQUIRED_TASK_RESULT_FIELDS_V1 = (
    "task_id",
    "family_id",
    "variant_index",
    "attempted",
    "packet_results",
    "task_entry",
    "task_status",
    "failure_records",
    "task_failure_categories",
    "synthetic_exact_count",
    "synthetic_partial_count",
    "synthetic_unsupported_count",
    "synthetic_failed_count",
    "family_summary",
    "dry_run_result",
    "validation_metadata",
    "leakage_flags",
    "authority_flags",
)

REQUIRED_PACKET_RESULT_FIELDS_V1 = (
    "task_id",
    "family_id",
    "test_input_index",
    "top2_packet",
    "top2_packet_validation",
    "packet_status",
    "failure_records",
    "candidate_count",
    "exact_match",
    "partial_match",
    "unsupported_candidate",
    "expected_exact_match",
    "solver_candidate_ids",
    "task_source",
    "leakage_flags",
)

DEFAULT_DENIED_AUTHORITY_V1 = (
    "benchmark_score_authority",
    "competition_submission_authority",
    "kaggle_ready_claim",
    "official_score_claim",
    "answer_key_authority",
)

DEFAULT_LEAKAGE_FLAGS_V1 = {
    "synthetic_only": True,
    "uses_kaggle_data": False,
    "uses_arc_public_data": False,
    "uses_hidden_private_data": False,
    "uses_solution_file": False,
    "uses_answer_key": False,
    "uses_test_output_for_candidate_generation": False,
    "kaggle_ready": False,
    "official_score_claim": False,
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


def to_arc_style_synthetic_solver_suite_json_safe_v1(value: Any) -> Any:
    safe = _json_safe(value)
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def _normalize_leakage_flags(value: Any) -> dict[str, bool]:
    mapping = value if isinstance(value, Mapping) else {}
    flags = dict(DEFAULT_LEAKAGE_FLAGS_V1)
    for key in flags:
        flags[key] = bool(mapping.get(key, flags[key]))
    return flags


def _authority_flags() -> dict[str, bool]:
    return {name: False for name in DEFAULT_DENIED_AUTHORITY_V1}


def _background_value(grid_metadata: Mapping[str, Any]) -> Any:
    return grid_metadata.get("background_color") if isinstance(grid_metadata, Mapping) else None


def _clone_grid(grid: Sequence[Sequence[Any]]) -> list[list[Any]]:
    return [list(row) for row in grid]


def _fallback_grid(grid: Sequence[Sequence[Any]], *, variant_seed: int, rank: int) -> list[list[Any]]:
    out = _clone_grid(grid)
    if not out or not out[0]:
        return [[variant_seed + rank]]
    row_index = (variant_seed + rank) % len(out)
    column_index = (variant_seed * 2 + rank) % len(out[0])
    current = out[row_index][column_index]
    if isinstance(current, int):
        out[row_index][column_index] = (current + rank + 1) % 10
    else:
        out[row_index][column_index] = f"{_safe_text(current)}_{rank}"
    return out


def _supported_primitive_grid(candidate_packet: Mapping[str, Any], input_grid: Sequence[Sequence[Any]]) -> list[list[Any]] | None:
    primitive_id = _safe_text(candidate_packet.get("primitive_id"))
    sequence = candidate_packet.get("primitive_sequence", []) if isinstance(candidate_packet.get("primitive_sequence"), list) else []
    params = sequence[0].get("parameters", {}) if sequence and isinstance(sequence[0], Mapping) else {}
    grid = _clone_grid(input_grid)

    if primitive_id == "copy":
        return grid
    if primitive_id == "recolor":
        from_value = params.get("from_value")
        to_value = params.get("to_value")
        if from_value is None or to_value is None:
            return None
        for row_index, row in enumerate(grid):
            for column_index, cell in enumerate(row):
                if cell == from_value:
                    grid[row_index][column_index] = to_value
        return grid
    if primitive_id == "move":
        direction = _safe_text(params.get("direction"))
        steps = int(params.get("steps", 1)) if str(params.get("steps", "1")).isdigit() else 1
        object_value = params.get("object_value")
        background_value = params.get("background_value")
        if background_value is None and grid:
            counts = Counter(cell for row in grid for cell in row)
            background_value = counts.most_common(1)[0][0]
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
        cells = _cells_for_value(grid, object_value) if object_value is not None else []
        if not cells:
            return None
        return _reflect_bbox_grid(grid, cells=cells, background_value=background_value, axis=axis)
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


def _sorted_candidate_evaluations(task_result: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    candidate_evaluations = task_result.get("candidate_evaluations", []) if isinstance(task_result.get("candidate_evaluations"), list) else []

    def _key(ev: Mapping[str, Any]) -> tuple[Any, ...]:
        return (
            not bool(ev.get("exact_match")),
            bool(ev.get("unsupported_candidate")),
            int(ev.get("mismatch_count", 10**6)),
            -int(ev.get("partial_match_count", 0)),
            int(ev.get("bounded_depth", 0)),
            int(ev.get("candidate_rank", 0)),
            _safe_text(ev.get("candidate_id")),
        )

    return sorted([ev for ev in candidate_evaluations if isinstance(ev, Mapping)], key=_key)


def _candidate_rank_signature(ev: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        not bool(ev.get("exact_match")),
        bool(ev.get("unsupported_candidate")),
        int(ev.get("mismatch_count", 10**6)),
        -int(ev.get("partial_match_count", 0)),
        int(ev.get("bounded_depth", 0)),
        int(ev.get("candidate_rank", 0)),
    )


def _build_attempt_from_candidate(
    *,
    task_id: str,
    family_id: str,
    variant_index: int,
    test_input_index: int,
    rank: int,
    candidate_eval: Mapping[str, Any] | None,
    input_grid: Sequence[Sequence[Any]],
    expected_grid: Sequence[Sequence[Any]],
) -> dict[str, Any]:
    if candidate_eval is not None:
        candidate_packet = candidate_eval.get("candidate_packet", {}) if isinstance(candidate_eval.get("candidate_packet"), Mapping) else {}
        attempt_grid = _supported_primitive_grid(candidate_packet, input_grid)
        if attempt_grid is None:
            attempt_grid = _fallback_grid(input_grid, variant_seed=variant_index + test_input_index, rank=rank)
        candidate_id = _safe_text(candidate_eval.get("candidate_id"))
        primitive_id = _safe_text(candidate_eval.get("primitive_id"))
        train_fit_status = _safe_text(candidate_eval.get("train_fit_status"))
        exact_match = bool(candidate_eval.get("exact_match"))
        unsupported_candidate = bool(candidate_eval.get("unsupported_candidate"))
        partial_match = bool(candidate_eval.get("partial_match"))
        source_kind = "dry_run_candidate"
    else:
        candidate_packet = {}
        attempt_grid = _fallback_grid(input_grid, variant_seed=variant_index + test_input_index + 7, rank=rank)
        candidate_id = f"{task_id}:fallback:{test_input_index}:{rank}"
        primitive_id = "fallback"
        train_fit_status = "unsupported"
        exact_match = False
        unsupported_candidate = True
        partial_match = False
        source_kind = "fallback_attempt"

    leakage_flags = _normalize_leakage_flags({})
    metadata = {
        "task_id": task_id,
        "family_id": family_id,
        "variant_index": variant_index,
        "test_input_index": test_input_index,
        "rank": rank,
        "source_kind": source_kind,
        "candidate_id": candidate_id,
        "primitive_id": primitive_id,
        "train_fit_status": train_fit_status,
        "candidate_exact_match": exact_match,
        "candidate_partial_match": partial_match,
        "candidate_unsupported": unsupported_candidate,
        "expected_exact_match": attempt_grid == list(expected_grid),
        "solver_candidate_id": candidate_id,
        "synthetic_internal_result": True,
        "leakage_flags": leakage_flags,
    }
    return build_arc_agi2_attempt_v1(
        attempt_id=f"{task_id}:{test_input_index}:rank{rank}",
        grid=attempt_grid,
        source_candidate_id=candidate_id,
        rank=rank,
        confidence_label=("high" if metadata["expected_exact_match"] else ("medium" if candidate_eval is not None and not unsupported_candidate else "low")),
        evidence_labels=["synthetic_solver_suite", primitive_id, source_kind],
        leakage_flags=leakage_flags,
        metadata=metadata,
    )


def build_arc_style_synthetic_solver_failure_ledger_v1(failure_entries: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    entries = [_json_safe(entry) for entry in (failure_entries or []) if isinstance(entry, Mapping)]
    category_counts = Counter(_safe_text(entry.get("category")) for entry in entries)
    family_category_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    family_counts = Counter()
    for entry in entries:
        family_id = _safe_text(entry.get("family_id"))
        category = _safe_text(entry.get("category"))
        if family_id:
            family_counts[family_id] += 1
            family_category_counts[family_id][category] += 1
    repeated = sorted([category for category, count in category_counts.items() if count > 1])
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "entries": entries,
        "category_counts": dict(category_counts),
        "family_counts": dict(family_counts),
        "family_category_counts": {family_id: dict(counts) for family_id, counts in family_category_counts.items()},
        "repeated_failure_categories": repeated,
    }


def _record_failure(
    failures: list[dict[str, Any]],
    *,
    category: str,
    task_id: str,
    family_id: str,
    variant_index: int,
    test_input_index: int | None,
    reason: str,
    candidate_id: str | None = None,
    primitive_id: str | None = None,
    mismatch_category: str | None = None,
) -> None:
    failures.append(
        {
            "category": _safe_text(category),
            "task_id": _safe_text(task_id),
            "family_id": _safe_text(family_id),
            "variant_index": int(variant_index),
            "test_input_index": None if test_input_index is None else int(test_input_index),
            "candidate_id": _safe_text(candidate_id),
            "primitive_id": _safe_text(primitive_id),
            "reason": _safe_text(reason),
            "mismatch_category": _safe_text(mismatch_category) if mismatch_category is not None else None,
        }
    )


def _task_status_for_counts(*, synthetic_exact_count: int, synthetic_partial_count: int, synthetic_unsupported_count: int, synthetic_failed_count: int) -> str:
    if synthetic_failed_count:
        return "failed"
    if synthetic_exact_count and not synthetic_partial_count and not synthetic_unsupported_count:
        return "exact"
    if synthetic_unsupported_count and not synthetic_exact_count and not synthetic_partial_count:
        return "unsupported"
    if synthetic_partial_count or synthetic_unsupported_count:
        return "partial"
    return "failed"


def _family_support_classification(family_id: str) -> str:
    if family_id in SUPPORTED_SYNTHETIC_FAMILIES_V1:
        return "supported"
    return "unsupported_transformation_family"


def _build_packet_result(
    *,
    task_id: str,
    family_id: str,
    variant_index: int,
    test_input_index: int,
    packet: Mapping[str, Any],
    task_result: Mapping[str, Any],
    expected_grid: Sequence[Sequence[Any]],
    input_grid: Sequence[Sequence[Any]],
    failures: list[dict[str, Any]],
) -> dict[str, Any]:
    ordered = _sorted_candidate_evaluations(task_result)
    candidate_count = len(ordered)
    task_source = _safe_text(packet.get("task_source"))
    top2_attempts: list[dict[str, Any]] = []
    ranking_signatures: list[tuple[Any, ...]] = []
    for rank in (1, 2):
        candidate_eval = ordered[rank - 1] if len(ordered) >= rank else None
        if candidate_eval is None:
            _record_failure(
                failures,
                category="candidate_generation_gap",
                task_id=task_id,
                family_id=family_id,
                variant_index=variant_index,
                test_input_index=test_input_index,
                reason="insufficient_solver_candidates",
            )
        else:
            ranking_signatures.append(_candidate_rank_signature(candidate_eval))
        top2_attempts.append(
            _build_attempt_from_candidate(
                task_id=task_id,
                family_id=family_id,
                variant_index=variant_index,
                test_input_index=test_input_index,
                rank=rank,
                candidate_eval=candidate_eval,
                input_grid=input_grid,
                expected_grid=expected_grid,
            )
        )

    duplicate_attempt_grid = top2_attempts[0]["grid"] == top2_attempts[1]["grid"]
    if duplicate_attempt_grid:
        _record_failure(
            failures,
            category="duplicate_attempt_grid",
            task_id=task_id,
            family_id=family_id,
            variant_index=variant_index,
            test_input_index=test_input_index,
            reason="top2_attempts_share_identical_grid",
        )

    top2_packet = build_arc_agi2_top2_attempt_packet_v1(
        task_id=task_id,
        test_input_index=test_input_index,
        candidate_packets=top2_attempts,
        metadata={
            "task_id": task_id,
            "family_id": family_id,
            "variant_index": variant_index,
            "test_input_index": test_input_index,
            "task_source": task_source,
            "synthetic_internal_result": True,
            "expected_exact_match": top2_attempts[0]["grid"] == list(expected_grid),
            "solver_candidate_count": candidate_count,
            "solver_candidate_ids": [evaluation.get("candidate_id") for evaluation in ordered],
            "solver_ranking_signatures": ranking_signatures,
            "family_support_classification": _family_support_classification(family_id),
            "leakage_flags": _normalize_leakage_flags({}),
        },
    )
    validation = validate_arc_agi2_top2_attempt_packet_v1(top2_packet)
    if not validation["valid"]:
        _record_failure(
            failures,
            category="top2_contract_failure",
            task_id=task_id,
            family_id=family_id,
            variant_index=variant_index,
            test_input_index=test_input_index,
            reason="top2_packet_failed_validation",
        )

    supported_family = family_id in SUPPORTED_SYNTHETIC_FAMILIES_V1
    top1_exact = top2_attempts[0]["grid"] == list(expected_grid)
    top1_partial = supported_family and not top1_exact
    top1_unsupported = not supported_family
    packet_status = "exact" if top1_exact and supported_family else ("unsupported" if top1_unsupported else ("partial" if top1_partial else "failed"))
    if not top1_exact and supported_family:
        _record_failure(
            failures,
            category="validation_mismatch",
            task_id=task_id,
            family_id=family_id,
            variant_index=variant_index,
            test_input_index=test_input_index,
            reason="attempt_grid_did_not_match_expected_output",
        )
    if not supported_family:
        _record_failure(
            failures,
            category="unsupported_transformation_family",
            task_id=task_id,
            family_id=family_id,
            variant_index=variant_index,
            test_input_index=test_input_index,
            reason="synthetic_family_not_supported_by_bounded_solver",
        )
        if ordered:
            _record_failure(
                failures,
                category="missing_primitive_executor",
                task_id=task_id,
                family_id=family_id,
                variant_index=variant_index,
                test_input_index=test_input_index,
                reason="no_supported_primitive_executor_for_family",
                primitive_id=_safe_text(ordered[0].get("primitive_id")),
                candidate_id=_safe_text(ordered[0].get("candidate_id")),
            )
    if len(ordered) >= 2 and _candidate_rank_signature(ordered[0]) == _candidate_rank_signature(ordered[1]):
        _record_failure(
            failures,
            category="ambiguous_candidate_ranking",
            task_id=task_id,
            family_id=family_id,
            variant_index=variant_index,
            test_input_index=test_input_index,
            reason="top_two_candidates_share_same_ranking_signature",
        )

    packet_result = {
        "task_id": task_id,
        "family_id": family_id,
        "variant_index": variant_index,
        "test_input_index": test_input_index,
        "top2_packet": top2_packet,
        "top2_packet_validation": validation,
        "packet_status": packet_status,
        "failure_records": [entry for entry in failures if entry["task_id"] == task_id and entry["family_id"] == family_id and entry["variant_index"] == variant_index and entry["test_input_index"] == test_input_index],
        "candidate_count": candidate_count,
        "exact_match": top1_exact,
        "partial_match": top1_partial,
        "unsupported_candidate": top1_unsupported,
        "expected_exact_match": top1_exact,
        "solver_candidate_ids": [evaluation.get("candidate_id") for evaluation in ordered],
        "task_source": task_source,
        "leakage_flags": _normalize_leakage_flags({}),
    }
    return packet_result


def _build_task_result(
    *,
    task_family: Mapping[str, Any],
    dry_run_task_results: Sequence[Mapping[str, Any]],
    failures: list[dict[str, Any]],
) -> dict[str, Any]:
    task_id = _safe_text(task_family.get("task_id"))
    family_id = _safe_text(task_family.get("family_id"))
    variant_index = int(task_family.get("variant_index", 0))
    validation_metadata = task_family.get("validation_metadata", {}) if isinstance(task_family.get("validation_metadata"), Mapping) else {}
    test_inputs = task_family.get("test_inputs", []) if isinstance(task_family.get("test_inputs"), list) else []
    expected_outputs = validation_metadata.get("expected_outputs", []) if isinstance(validation_metadata.get("expected_outputs"), list) else []

    packet_results: list[dict[str, Any]] = []
    for index, (packet, dry_run_result, expected_output) in enumerate(zip(task_family.get("generator_metadata", {}).get("arc_style_task_packets", []), dry_run_task_results, expected_outputs)):
        packet_result = _build_packet_result(
            task_id=task_id,
            family_id=family_id,
            variant_index=variant_index,
            test_input_index=index,
            packet=packet,
            task_result=dry_run_result,
            expected_grid=expected_output.get("output_grid", []),
            input_grid=test_inputs[index].get("input_grid", []) if index < len(test_inputs) and isinstance(test_inputs[index], Mapping) else [],
            failures=failures,
        )
        packet_results.append(packet_result)

    exact = sum(1 for packet_result in packet_results if packet_result["packet_status"] == "exact")
    partial = sum(1 for packet_result in packet_results if packet_result["packet_status"] == "partial")
    unsupported = sum(1 for packet_result in packet_results if packet_result["packet_status"] == "unsupported")
    failed = sum(1 for packet_result in packet_results if packet_result["packet_status"] == "failed")
    task_status = _task_status_for_counts(
        synthetic_exact_count=exact,
        synthetic_partial_count=partial,
        synthetic_unsupported_count=unsupported,
        synthetic_failed_count=failed,
    )

    failure_categories = sorted({entry["category"] for entry in failures if entry["task_id"] == task_id and entry["family_id"] == family_id and entry["variant_index"] == variant_index})
    task_entry = build_arc_agi2_submission_task_entry_v1(
        task_id=task_id,
        test_input_packets=[packet_result["top2_packet"] for packet_result in packet_results],
        metadata={
            "task_id": task_id,
            "family_id": family_id,
            "variant_index": variant_index,
            "synthetic_internal_result": True,
            "task_status": task_status,
            "failure_categories": failure_categories,
            "leakage_flags": _normalize_leakage_flags({}),
            "authority_flags": _authority_flags(),
        },
        leakage_flags=_normalize_leakage_flags({}),
    )

    return {
        "task_id": task_id,
        "family_id": family_id,
        "variant_index": variant_index,
        "attempted": True,
        "packet_results": packet_results,
        "task_entry": task_entry,
        "task_status": task_status,
        "failure_records": [entry for entry in failures if entry["task_id"] == task_id and entry["family_id"] == family_id and entry["variant_index"] == variant_index],
        "task_failure_categories": failure_categories,
        "synthetic_exact_count": exact,
        "synthetic_partial_count": partial,
        "synthetic_unsupported_count": unsupported,
        "synthetic_failed_count": failed,
        "family_summary": {
            "task_id": task_id,
            "family_id": family_id,
            "variant_index": variant_index,
            "packet_count": len(packet_results),
            "synthetic_exact_count": exact,
            "synthetic_partial_count": partial,
            "synthetic_unsupported_count": unsupported,
            "synthetic_failed_count": failed,
            "task_status": task_status,
            "failure_categories": failure_categories,
        },
        "dry_run_result": {
            "task_id": task_id,
            "candidate_count": sum(int(dry_run_task_result.get("candidate_count", 0)) for dry_run_task_result in dry_run_task_results),
            "selected_candidate_ids": [dry_run_task_result.get("selected_candidate_id") for dry_run_task_result in dry_run_task_results],
            "train_fit_statuses": [dry_run_task_result.get("train_fit_status") for dry_run_task_result in dry_run_task_results],
            "task_results": [_json_safe(dry_run_task_result) for dry_run_task_result in dry_run_task_results],
        },
        "validation_metadata": _json_safe(validation_metadata),
        "leakage_flags": _normalize_leakage_flags({}),
        "authority_flags": _authority_flags(),
    }


def build_arc_style_synthetic_solver_suite_result_v1(
    *,
    suite: Mapping[str, Any],
    task_results: Sequence[Mapping[str, Any]] | None = None,
    failure_ledger: Mapping[str, Any] | None = None,
    task_entries: Sequence[Mapping[str, Any]] | None = None,
    submission_packet: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    failures = [_json_safe(entry) for entry in (failure_ledger.get("entries", []) if isinstance(failure_ledger, Mapping) else [])]
    task_results_out = [_json_safe(item) for item in (task_results or [])]
    task_entries_out = [_json_safe(item) for item in (task_entries or [])]
    submission_packet_out = _json_safe(submission_packet) if submission_packet is not None else build_arc_agi2_submission_packet_v1(task_entries=task_entries_out)
    submission_validation = validate_arc_agi2_submission_packet_v1(submission_packet_out)
    family_level_summary: dict[str, dict[str, Any]] = {}
    for task_result in task_results_out:
        if not isinstance(task_result, Mapping):
            continue
        family_id = _safe_text(task_result.get("family_id"))
        summary = family_level_summary.setdefault(
            family_id,
            {
                "family_id": family_id,
                "task_count": 0,
                "attempted_task_count": 0,
                "top2_packet_count": 0,
                "synthetic_exact_count": 0,
                "synthetic_partial_count": 0,
                "synthetic_unsupported_count": 0,
                "synthetic_failed_count": 0,
                "failure_categories": [],
            },
        )
        summary["task_count"] += 1
        summary["attempted_task_count"] += 1 if task_result.get("attempted", False) else 0
        summary["top2_packet_count"] += len(task_result.get("packet_results", [])) if isinstance(task_result.get("packet_results"), list) else 0
        summary["synthetic_exact_count"] += int(task_result.get("synthetic_exact_count", 0))
        summary["synthetic_partial_count"] += int(task_result.get("synthetic_partial_count", 0))
        summary["synthetic_unsupported_count"] += int(task_result.get("synthetic_unsupported_count", 0))
        summary["synthetic_failed_count"] += int(task_result.get("synthetic_failed_count", 0))
        for category in task_result.get("task_failure_categories", []):
            if category not in summary["failure_categories"]:
                summary["failure_categories"].append(category)

    generated_task_count = len(task_results_out)
    top2_packet_count = sum(len(task_result.get("packet_results", [])) for task_result in task_results_out if isinstance(task_result, Mapping))
    attempted_task_count = sum(1 for task_result in task_results_out if isinstance(task_result, Mapping) and task_result.get("attempted", False))
    synthetic_exact_count = sum(int(task_result.get("synthetic_exact_count", 0)) for task_result in task_results_out if isinstance(task_result, Mapping))
    synthetic_partial_count = sum(int(task_result.get("synthetic_partial_count", 0)) for task_result in task_results_out if isinstance(task_result, Mapping))
    synthetic_unsupported_count = sum(int(task_result.get("synthetic_unsupported_count", 0)) for task_result in task_results_out if isinstance(task_result, Mapping))
    synthetic_failed_count = sum(int(task_result.get("synthetic_failed_count", 0)) for task_result in task_results_out if isinstance(task_result, Mapping))
    result = {
        "suite_id": SUITE_ID_V1,
        "synthetic_internal_result": True,
        "generated_task_count": generated_task_count,
        "attempted_task_count": attempted_task_count,
        "top2_packet_count": top2_packet_count,
        "synthetic_exact_count": synthetic_exact_count,
        "synthetic_partial_count": synthetic_partial_count,
        "synthetic_unsupported_count": synthetic_unsupported_count,
        "synthetic_failed_count": synthetic_failed_count,
        "family_level_summary": family_level_summary,
        "failure_ledger": _json_safe(failure_ledger) if failure_ledger is not None else build_arc_style_synthetic_solver_failure_ledger_v1(failures),
        "task_results": task_results_out,
        "task_entries": task_entries_out,
        "submission_packet": submission_packet_out,
        "submission_packet_validation": submission_validation,
        "leakage_flags": _normalize_leakage_flags({}),
        "denied_authority": list(DEFAULT_DENIED_AUTHORITY_V1),
        "authority_flags": _authority_flags(),
        "no_score_claim": True,
        "official_score_claim": False,
        "synthetic_exact_ratio": (synthetic_exact_count / top2_packet_count) if top2_packet_count else 0.0,
        # Task-level aggregates
        "task_exact_count": sum(1 for tr in task_results_out if tr.get("task_status") == "exact"),
        "task_partial_count": sum(1 for tr in task_results_out if tr.get("task_status") == "partial"),
        "task_unsupported_count": sum(1 for tr in task_results_out if tr.get("task_status") == "unsupported"),
        "task_failed_count": sum(1 for tr in task_results_out if tr.get("task_status") == "failed"),
        # Rates
        "task_exact_rate": (sum(1 for tr in task_results_out if tr.get("task_status") == "exact") / attempted_task_count) if attempted_task_count else 0.0,
        "task_partial_rate": (sum(1 for tr in task_results_out if tr.get("task_status") == "partial") / attempted_task_count) if attempted_task_count else 0.0,
        "task_unsupported_rate": (sum(1 for tr in task_results_out if tr.get("task_status") == "unsupported") / attempted_task_count) if attempted_task_count else 0.0,
        "packet_exact_rate": (synthetic_exact_count / top2_packet_count) if top2_packet_count else 0.0,
        "packet_partial_rate": (synthetic_partial_count / top2_packet_count) if top2_packet_count else 0.0,
        "packet_unsupported_rate": (synthetic_unsupported_count / top2_packet_count) if top2_packet_count else 0.0,
        # Thresholds and hardening flags
        "internal_threshold": 0.85,
        "threshold_basis": "task_exact_rate",
        "internal_pass_85": ((sum(1 for tr in task_results_out if tr.get("task_status") == "exact") / attempted_task_count) if attempted_task_count else 0.0) >= 0.85,
        "level_hardening_allowed": ((sum(1 for tr in task_results_out if tr.get("task_status") == "exact") / attempted_task_count) if attempted_task_count else 0.0) >= 0.85,
        "level_hardening_reason": "",
        # Frontier placeholders (to be filled by higher-level analysis)
        "hardest_exact_tier": None,
        "hardest_partial_tier": None,
        "first_stable_failure_frontier": None,
        "remaining_partial_families": [],
        "remaining_blocker_families": [],
        "remaining_unsupported_families": [],
        "next_recommended_pressure_family": None,
        # Boundary flags
        "synthetic_only": True,
        "public_arc_used": False,
        "kaggle_used": False,
        "benchmark_claim_safe": False,
        "task_family_count": len(family_level_summary),
    }
    return result


def run_arc_style_synthetic_solver_suite_v1(
    suite: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    suite_out = _json_safe(suite) if suite is not None else generate_arc_style_synthetic_task_suite_v1()
    task_families = suite_out.get("tasks", []) if isinstance(suite_out.get("tasks"), list) else []
    all_packets: list[Mapping[str, Any]] = []
    packet_sources: list[dict[str, Any]] = []
    for task_family in task_families:
        if not isinstance(task_family, Mapping):
            continue
        task_id = _safe_text(task_family.get("task_id"))
        family_id = _safe_text(task_family.get("family_id"))
        variant_index = int(task_family.get("variant_index", 0))
        packets = task_family.get("generator_metadata", {}).get("arc_style_task_packets", []) if isinstance(task_family.get("generator_metadata"), Mapping) else []
        for test_input_index, packet in enumerate(packets if isinstance(packets, list) else []):
            all_packets.append(packet)
            packet_sources.append(
                {
                    "task_id": task_id,
                    "family_id": family_id,
                    "variant_index": variant_index,
                    "test_input_index": test_input_index,
                    "expected_output": task_family.get("validation_metadata", {}).get("expected_outputs", [])[test_input_index] if isinstance(task_family.get("validation_metadata"), Mapping) and isinstance(task_family.get("validation_metadata", {}).get("expected_outputs"), list) and test_input_index < len(task_family.get("validation_metadata", {}).get("expected_outputs", [])) else {},
                    "task_family": task_family,
                }
            )

    dry_run_result = run_arc_style_bounded_solver_dry_run_v1(all_packets)
    dry_run_task_results = dry_run_result.get("task_results", []) if isinstance(dry_run_result.get("task_results"), list) else []

    failures: list[dict[str, Any]] = []
    task_results: list[dict[str, Any]] = []
    task_entries: list[dict[str, Any]] = []

    offset = 0
    for task_family in task_families:
        if not isinstance(task_family, Mapping):
            continue
        packets = task_family.get("generator_metadata", {}).get("arc_style_task_packets", []) if isinstance(task_family.get("generator_metadata"), Mapping) else []
        count = len(packets) if isinstance(packets, list) else 0
        family_task_results = dry_run_task_results[offset : offset + count]
        offset += count
        task_result = _build_task_result(task_family=task_family, dry_run_task_results=family_task_results, failures=failures)
        task_results.append(task_result)
        task_entries.append(task_result["task_entry"])

    failure_ledger = build_arc_style_synthetic_solver_failure_ledger_v1(failures)
    result = build_arc_style_synthetic_solver_suite_result_v1(
        suite=suite_out,
        task_results=task_results,
        failure_ledger=failure_ledger,
        task_entries=task_entries,
        submission_packet=build_arc_agi2_submission_packet_v1(task_entries=task_entries),
    )
    return result


def validate_arc_style_synthetic_solver_suite_result_v1(result: Any) -> dict[str, Any]:
    validation = {"valid": False, "suite_id": None, "blocked_reason_labels": []}
    if not isinstance(result, Mapping):
        validation["blocked_reason_labels"].append("result_not_mapping")
        return validation
    missing = [field for field in REQUIRED_RESULT_FIELDS_V1 if field not in result]
    if missing:
        validation["blocked_reason_labels"].append("missing_required_fields")
        validation["blocked_reason_labels"].extend(f"missing:{field}" for field in missing)
        return validation
    validation["suite_id"] = _safe_text(result.get("suite_id"))
    if validation["suite_id"] != SUITE_ID_V1:
        validation["blocked_reason_labels"].append("suite_id_mismatch")
    if result.get("synthetic_internal_result") is not True:
        validation["blocked_reason_labels"].append("synthetic_internal_result_not_true")
    if result.get("no_score_claim") is not True:
        validation["blocked_reason_labels"].append("no_score_claim_not_true")
    if result.get("official_score_claim") is not False:
        validation["blocked_reason_labels"].append("official_score_claim_not_false")
    leakage = _normalize_leakage_flags(result.get("leakage_flags"))
    if not leakage.get("synthetic_only", False):
        validation["blocked_reason_labels"].append("synthetic_only_not_true")
    for key in ("uses_kaggle_data", "uses_arc_public_data", "uses_hidden_private_data", "uses_solution_file", "uses_answer_key", "uses_test_output_for_candidate_generation", "kaggle_ready", "official_score_claim"):
        if leakage.get(key, False):
            validation["blocked_reason_labels"].append(f"leakage_flag_true:{key}")
    authority_flags = result.get("authority_flags") if isinstance(result.get("authority_flags"), Mapping) else {}
    for key, value in authority_flags.items():
        if bool(value):
            validation["blocked_reason_labels"].append(f"authority_flag_true:{key}")
    submission_validation = validate_arc_agi2_submission_packet_v1(result.get("submission_packet"))
    if not submission_validation["valid"]:
        validation["blocked_reason_labels"].append("submission_packet_invalid")
        validation["blocked_reason_labels"].extend(submission_validation["blocked_reason_labels"])
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
            if not isinstance(task_result.get("packet_results"), list):
                validation["blocked_reason_labels"].append(f"packet_results_not_list:{task_result.get('task_id')}")
            else:
                for packet_result in task_result.get("packet_results", []):
                    if not isinstance(packet_result, Mapping):
                        validation["blocked_reason_labels"].append(f"packet_result_not_mapping:{task_result.get('task_id')}")
                        continue
                    missing_packet = [field for field in REQUIRED_PACKET_RESULT_FIELDS_V1 if field not in packet_result]
                    if missing_packet:
                        validation["blocked_reason_labels"].append("packet_result_missing_required_fields")
                        validation["blocked_reason_labels"].extend(f"packet_missing:{field}" for field in missing_packet)
                    if not isinstance(packet_result.get("top2_packet_validation"), Mapping) or not packet_result["top2_packet_validation"].get("valid", False):
                        validation["blocked_reason_labels"].append(f"top2_packet_invalid:{packet_result.get('task_id')}:{packet_result.get('test_input_index')}")
                    if packet_result.get("leakage_flags") and _normalize_leakage_flags(packet_result.get("leakage_flags")) != _normalize_leakage_flags({}):
                        validation["blocked_reason_labels"].append(f"packet_leakage_flag_true:{packet_result.get('task_id')}")
    if not isinstance(result.get("failure_ledger"), Mapping):
        validation["blocked_reason_labels"].append("failure_ledger_not_mapping")
    if not isinstance(result.get("family_level_summary"), Mapping):
        validation["blocked_reason_labels"].append("family_level_summary_not_mapping")
    if not isinstance(result.get("task_entries"), list):
        validation["blocked_reason_labels"].append("task_entries_not_list")
    if not validation["blocked_reason_labels"]:
        validation["valid"] = True
    return validation


def summarize_arc_style_synthetic_solver_suite_result_v1(result: Any) -> dict[str, Any]:
    validation = validate_arc_style_synthetic_solver_suite_result_v1(result)
    if not isinstance(result, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "suite_id": None,
            "valid": False,
            "generated_task_count": 0,
            "attempted_task_count": 0,
            "top2_packet_count": 0,
            "synthetic_exact_count": 0,
            "synthetic_partial_count": 0,
            "synthetic_unsupported_count": 0,
            "synthetic_failed_count": 0,
            "failure_categories": [],
            "family_count": 0,
            "family_level_summary": {},
            "blocked_reason_labels": validation["blocked_reason_labels"],
        }
    failure_ledger = result.get("failure_ledger", {}) if isinstance(result.get("failure_ledger"), Mapping) else {}
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "suite_id": _safe_text(result.get("suite_id")),
        "valid": validation["valid"],
        "generated_task_count": int(result.get("generated_task_count", 0)),
        "attempted_task_count": int(result.get("attempted_task_count", 0)),
        "top2_packet_count": int(result.get("top2_packet_count", 0)),
        "synthetic_exact_count": int(result.get("synthetic_exact_count", 0)),
        "synthetic_partial_count": int(result.get("synthetic_partial_count", 0)),
        "synthetic_unsupported_count": int(result.get("synthetic_unsupported_count", 0)),
        "synthetic_failed_count": int(result.get("synthetic_failed_count", 0)),
        "failure_categories": list((failure_ledger.get("category_counts", {}) or {}).keys()),
        "failure_category_counts": _json_safe(failure_ledger.get("category_counts", {})),
        "family_count": len(result.get("family_level_summary", {})) if isinstance(result.get("family_level_summary"), Mapping) else 0,
        "family_level_summary": _json_safe(result.get("family_level_summary", {})),
        "leakage_flags": _json_safe(result.get("leakage_flags", {})),
        "denied_authority": _json_safe(result.get("denied_authority", [])),
        "blocked_reason_labels": validation["blocked_reason_labels"],
    }


__all__ = [
    "SCHEMA_VERSION_V1",
    "SUITE_ID_V1",
    "SUPPORTED_SYNTHETIC_FAMILIES_V1",
    "FAILURE_CATEGORIES_V1",
    "build_arc_style_synthetic_solver_failure_ledger_v1",
    "build_arc_style_synthetic_solver_suite_result_v1",
    "run_arc_style_synthetic_solver_suite_v1",
    "summarize_arc_style_synthetic_solver_suite_result_v1",
    "to_arc_style_synthetic_solver_suite_json_safe_v1",
    "validate_arc_style_synthetic_solver_suite_result_v1",
]
