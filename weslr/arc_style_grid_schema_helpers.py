"""WESLR ARC-style grid schema helpers V1.

Phase 1 only: schema helpers, JSON-safe validation, and internal synthetic toy
fixtures. This module does not implement solver runtime, candidate search,
primitive execution, object extraction, ARC dataset ingestion, scoring claims,
or competition adapters.

No provider calls. No model calls. No payment calls. No ChatResponder wiring.
No website/runtime wiring. No `.weslr` writes.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from typing import Any, Iterable, Mapping, Sequence

SCHEMA_VERSION_V1 = "ArcStyleGridSchemaHelpersV1"
GRID_FORMAT_ID_V1 = "arc_style_grid_v1"
TASK_SOURCE_INTERNAL_SYNTHETIC_V1 = "internal_synthetic_toy_tasks_v1"
MAX_GRID_WIDTH_V1 = 30
MAX_GRID_HEIGHT_V1 = 30
ALLOWED_CELL_TYPE_NAMES_V1 = ("int", "short_symbol")
ALLOWED_TRAIN_FIT_STATUSES_V1 = (
    "unknown",
    "fit",
    "partial_fit",
    "mismatch",
    "invalid",
    "unsupported",
)

REQUIRED_TASK_PACKET_FIELDS_V1 = (
    "task_id",
    "task_source",
    "train_pairs",
    "test_input",
    "grid_format",
    "palette",
    "object_candidates",
    "transformation_candidates",
    "constraint_candidates",
    "candidate_outputs",
    "validation_results",
    "failure_notes",
    "trace",
)

REQUIRED_TRAIN_PAIR_FIELDS_V1 = ("pair_id", "input_grid", "output_grid", "notes")
REQUIRED_GRID_METADATA_FIELDS_V1 = (
    "width",
    "height",
    "cell_values",
    "palette_ids",
    "has_background",
    "background_color",
    "invalid_cells",
)
REQUIRED_CANDIDATE_RESULT_FIELDS_V1 = (
    "candidate_id",
    "candidate_type",
    "primitive_sequence",
    "train_fit_status",
    "partial_fit_metadata",
    "unsupported_assumptions",
    "rejection_reasons",
    "confidence_metadata",
    "calibration_metadata",
)

TOY_TASK_TYPES_V1 = (
    "copy_grid",
    "recolor_symbol",
    "move_single_object",
    "complete_symmetry",
    "border_frame_fill",
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


def to_arc_style_grid_task_json_safe_v1(value: Any) -> Any:
    safe = _json_safe(value)
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def _is_short_symbol(value: Any) -> bool:
    return isinstance(value, str) and 1 <= len(value.strip()) <= 3


def _is_allowed_cell(value: Any) -> bool:
    return isinstance(value, int) or _is_short_symbol(value)


def _normalize_row(row: Any) -> list[Any] | None:
    if not isinstance(row, (list, tuple)):
        return None
    return list(row)


def _detect_row_shape(grid: Sequence[Any]) -> tuple[int, int, list[int]]:
    row_lengths: list[int] = []
    for row in grid:
        normalized = _normalize_row(row)
        if normalized is None:
            return 0, 0, []
        row_lengths.append(len(normalized))
    if not row_lengths:
        return 0, 0, []
    return len(row_lengths), row_lengths[0], row_lengths


def _flatten(values: Iterable[Iterable[Any]]) -> list[Any]:
    out: list[Any] = []
    for row in values:
        out.extend(list(row))
    return out


def build_arc_style_grid_metadata_v1(
    grid: Sequence[Any],
    *,
    background_color: Any | None = None,
    max_width: int = MAX_GRID_WIDTH_V1,
    max_height: int = MAX_GRID_HEIGHT_V1,
) -> dict[str, Any]:
    rows, cols, row_lengths = _detect_row_shape(grid)
    invalid_cells: list[dict[str, Any]] = []
    normalized_grid: list[list[Any]] = []
    cell_types: set[str] = set()

    for row_index, row in enumerate(grid):
        normalized_row = _normalize_row(row)
        if normalized_row is None:
            invalid_cells.append({"row": row_index, "column": None, "reason": "row_not_sequence"})
            continue
        normalized_cells: list[Any] = []
        for column_index, cell in enumerate(normalized_row):
            if not _is_allowed_cell(cell):
                invalid_cells.append({"row": row_index, "column": column_index, "reason": "unsupported_cell_type"})
            else:
                cell_types.add("int" if isinstance(cell, int) else "short_symbol")
            normalized_cells.append(cell)
        normalized_grid.append(normalized_cells)

    flattened = _flatten(normalized_grid)
    palette_ids = sorted({cell for cell in flattened if isinstance(cell, (int, str))}, key=lambda item: str(item))
    counts = Counter(flattened)
    inferred_background = background_color
    background_inference_trace: dict[str, Any] = {
        "explicit_background_color": background_color is not None,
        "strategy": "none",
    }
    if inferred_background is None and flattened:
        most_common = counts.most_common(1)[0]
        inferred_background = most_common[0]
        background_inference_trace.update(
            {
                "strategy": "most_common_cell",
                "candidate_background_color": inferred_background,
                "candidate_count": most_common[1],
            }
        )
    elif inferred_background is not None:
        background_inference_trace.update({"strategy": "explicit"})

    has_background = bool(flattened and any(count >= 2 for count in counts.values())) or inferred_background is not None
    metadata = {
        "width": cols if rows else 0,
        "height": rows,
        "cell_values": normalized_grid,
        "palette_ids": palette_ids,
        "has_background": has_background,
        "background_color": inferred_background,
        "invalid_cells": invalid_cells,
        "trace": {
            "schema_version": SCHEMA_VERSION_V1,
            "cell_type_names": sorted(cell_types),
            "row_lengths": row_lengths,
            "row_count": rows,
            "column_count": cols,
            "background_inference": background_inference_trace,
        },
    }

    if rows and cols:
        metadata["trace"]["rectangular"] = all(len(row) == cols for row in normalized_grid)
    else:
        metadata["trace"]["rectangular"] = False

    if rows > max_height or cols > max_width:
        metadata["trace"]["oversized"] = True
    else:
        metadata["trace"]["oversized"] = False
    return metadata


def _validate_grid_payload(grid: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "reasons": [],
        "grid_metadata": None,
    }
    payload = grid
    if isinstance(grid, Mapping) and "cell_values" in grid:
        payload = grid.get("cell_values")
    if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes, bytearray)):
        result["reasons"].append("grid_not_sequence")
        return result
    if len(payload) == 0:
        result["reasons"].append("empty_grid")
        return result

    metadata = build_arc_style_grid_metadata_v1(payload)
    result["grid_metadata"] = metadata
    if metadata["trace"]["oversized"]:
        result["reasons"].append("grid_oversized")
    if metadata["trace"]["rectangular"] is False:
        result["reasons"].append("grid_not_rectangular")
    if metadata["invalid_cells"]:
        result["reasons"].append("invalid_cells_present")
    if metadata["width"] > MAX_GRID_WIDTH_V1 or metadata["height"] > MAX_GRID_HEIGHT_V1:
        result["reasons"].append("grid_over_policy_limit")
    mixed_types = len(metadata["trace"]["cell_type_names"]) > 1
    if mixed_types:
        result["reasons"].append("mixed_cell_types_rejected")
    result["valid"] = not result["reasons"]
    return result


def build_arc_style_grid_train_pair_v1(pair_id: str, input_grid: Sequence[Any], output_grid: Sequence[Any], notes: str = "") -> dict[str, Any]:
    input_validation = _validate_grid_payload(input_grid)
    output_validation = _validate_grid_payload(output_grid)
    return {
        "pair_id": _safe_text(pair_id),
        "input_grid": to_arc_style_grid_task_json_safe_v1(input_grid),
        "output_grid": to_arc_style_grid_task_json_safe_v1(output_grid),
        "notes": _safe_text(notes),
        "input_grid_metadata": input_validation["grid_metadata"],
        "output_grid_metadata": output_validation["grid_metadata"],
        "validation": {
            "valid": input_validation["valid"] and output_validation["valid"],
            "input_reasons": input_validation["reasons"],
            "output_reasons": output_validation["reasons"],
        },
    }


def build_arc_style_grid_candidate_result_v1(
    candidate_id: str,
    *,
    candidate_type: str = "synthetic_candidate",
    primitive_sequence: Sequence[Any] | None = None,
    train_fit_status: str = "unknown",
    partial_fit_metadata: Mapping[str, Any] | None = None,
    unsupported_assumptions: Sequence[Any] | None = None,
    rejection_reasons: Sequence[Any] | None = None,
    confidence_metadata: Mapping[str, Any] | None = None,
    calibration_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if train_fit_status not in ALLOWED_TRAIN_FIT_STATUSES_V1:
        train_fit_status = "unknown"
    return {
        "candidate_id": _safe_text(candidate_id),
        "candidate_type": _safe_text(candidate_type),
        "primitive_sequence": [_json_safe(item) for item in (primitive_sequence or [])],
        "train_fit_status": train_fit_status,
        "partial_fit_metadata": _json_safe(dict(partial_fit_metadata or {})),
        "unsupported_assumptions": [_json_safe(item) for item in (unsupported_assumptions or [])],
        "rejection_reasons": [_json_safe(item) for item in (rejection_reasons or [])],
        "confidence_metadata": _json_safe(dict(confidence_metadata or {})),
        "calibration_metadata": _json_safe(dict(calibration_metadata or {})),
    }


def _build_grid_format_v1() -> dict[str, Any]:
    return {
        "format_id": GRID_FORMAT_ID_V1,
        "allowed_cell_type_names": list(ALLOWED_CELL_TYPE_NAMES_V1),
        "max_width": MAX_GRID_WIDTH_V1,
        "max_height": MAX_GRID_HEIGHT_V1,
        "json_safe": True,
        "phase": 1,
    }


def _merge_palette_from_metadata(*metas: Mapping[str, Any] | None) -> dict[str, Any]:
    palette_ids: list[Any] = []
    background_color = None
    background_inferred = False
    for meta in metas:
        if not isinstance(meta, Mapping):
            continue
        for value in meta.get("palette_ids", []):
            if value not in palette_ids:
                palette_ids.append(value)
        if background_color is None and meta.get("background_color") is not None:
            background_color = meta.get("background_color")
            background_inferred = bool(meta.get("trace", {}).get("background_inference", {}).get("strategy") != "explicit")
    return {
        "palette_ids": palette_ids,
        "background_color": background_color,
        "background_inferred": background_inferred,
    }


def _default_trace_for_task(task_id: str, task_type: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "internal_synthetic_only": True,
        "toy_task": True,
        "toy_task_type": task_type,
        "task_family": "arc_style_grid_phase1",
        "no_arc_dataset_ingestion": True,
        "no_solver_runtime": True,
        "no_candidate_search": True,
        "no_object_extraction_implementation": True,
        "no_primitive_executor": True,
        "task_id": task_id,
    }


def build_arc_style_grid_task_packet_v1(
    *,
    task_id: str,
    task_source: str,
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Sequence[Any],
    grid_format: Mapping[str, Any] | None = None,
    palette: Mapping[str, Any] | None = None,
    object_candidates: Sequence[Any] | None = None,
    transformation_candidates: Sequence[Any] | None = None,
    constraint_candidates: Sequence[Any] | None = None,
    candidate_outputs: Sequence[Any] | None = None,
    validation_results: Sequence[Any] | None = None,
    failure_notes: Sequence[Any] | None = None,
    trace: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    train_pairs_out = [to_arc_style_grid_task_json_safe_v1(pair) for pair in train_pairs]
    train_metadata = []
    for pair in train_pairs:
        if isinstance(pair, Mapping):
            train_metadata.append(pair.get("input_grid_metadata"))
            train_metadata.append(pair.get("output_grid_metadata"))
    test_metadata = build_arc_style_grid_metadata_v1(test_input)
    merged_palette = _merge_palette_from_metadata(*train_metadata, test_metadata)
    palette_out = {
        "palette_ids": list((palette or {}).get("palette_ids", merged_palette["palette_ids"])),
        "background_color": (palette or {}).get("background_color", merged_palette["background_color"]),
        "background_inferred": bool((palette or {}).get("background_inferred", merged_palette["background_inferred"])),
    }
    grid_format_out = dict(grid_format or _build_grid_format_v1())
    grid_format_out.setdefault("format_id", GRID_FORMAT_ID_V1)
    grid_format_out.setdefault("phase", 1)
    grid_format_out.setdefault("json_safe", True)

    task_packet = {
        "task_id": _safe_text(task_id),
        "task_source": _safe_text(task_source),
        "train_pairs": train_pairs_out,
        "test_input": test_metadata,
        "grid_format": _json_safe(grid_format_out),
        "palette": _json_safe(palette_out),
        "object_candidates": [_json_safe(item) for item in (object_candidates or [])],
        "transformation_candidates": [_json_safe(item) for item in (transformation_candidates or [])],
        "constraint_candidates": [_json_safe(item) for item in (constraint_candidates or [])],
        "candidate_outputs": [_json_safe(item) for item in (candidate_outputs or [])],
        "validation_results": [_json_safe(item) for item in (validation_results or [])],
        "failure_notes": [_json_safe(item) for item in (failure_notes or [])],
        "trace": _json_safe(dict(trace or {})),
    }
    task_packet["trace"].update(_default_trace_for_task(task_packet["task_id"], task_packet["trace"].get("toy_task_type", "synthetic")))
    task_packet["trace"]["train_pair_count"] = len(train_pairs_out)
    task_packet["trace"]["toy_task"] = bool(task_packet["trace"].get("toy_task", False))
    task_packet["trace"]["internal_synthetic_only"] = bool(task_packet["trace"].get("internal_synthetic_only", False))
    task_packet["trace"]["palette_id_count"] = len(task_packet["palette"]["palette_ids"])
    return task_packet




def validate_arc_style_grid_candidate_result_v1(candidate: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "candidate_id": None,
        "blocked_reason_labels": [],
    }
    if not isinstance(candidate, Mapping):
        result["blocked_reason_labels"].append("candidate_not_mapping")
        return result
    missing = [field for field in REQUIRED_CANDIDATE_RESULT_FIELDS_V1 if field not in candidate]
    if missing:
        result["blocked_reason_labels"].append("missing_required_fields")
        result["blocked_reason_labels"].extend(f"missing:{field}" for field in missing)
        return result
    result["candidate_id"] = _safe_text(candidate.get("candidate_id"))
    if not result["candidate_id"]:
        result["blocked_reason_labels"].append("empty_candidate_id")
    if _safe_text(candidate.get("train_fit_status"), "unknown") not in ALLOWED_TRAIN_FIT_STATUSES_V1:
        result["blocked_reason_labels"].append("invalid_train_fit_status")
    for field in ("primitive_sequence", "unsupported_assumptions", "rejection_reasons"):
        if not isinstance(candidate.get(field), list):
            result["blocked_reason_labels"].append(f"{field}_not_list")
    for field in ("partial_fit_metadata", "confidence_metadata", "calibration_metadata"):
        if not isinstance(candidate.get(field), Mapping):
            result["blocked_reason_labels"].append(f"{field}_not_mapping")
    result["valid"] = not result["blocked_reason_labels"]
    return result

def validate_arc_style_grid_train_pair_v1(pair: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "pair_id": None,
        "blocked_reason_labels": [],
    }
    if not isinstance(pair, Mapping):
        result["blocked_reason_labels"].append("pair_not_mapping")
        return result
    missing = [field for field in REQUIRED_TRAIN_PAIR_FIELDS_V1 if field not in pair]
    if missing:
        result["blocked_reason_labels"].append("missing_required_fields")
        result["blocked_reason_labels"].extend(f"missing:{field}" for field in missing)
        return result
    input_validation = _validate_grid_payload(pair.get("input_grid"))
    output_validation = _validate_grid_payload(pair.get("output_grid"))
    result["pair_id"] = _safe_text(pair.get("pair_id"))
    if not input_validation["valid"]:
        result["blocked_reason_labels"].append("invalid_input_grid")
        result["blocked_reason_labels"].extend(f"input:{reason}" for reason in input_validation["reasons"])
    if not output_validation["valid"]:
        result["blocked_reason_labels"].append("invalid_output_grid")
        result["blocked_reason_labels"].extend(f"output:{reason}" for reason in output_validation["reasons"])
    result["valid"] = not result["blocked_reason_labels"]
    return result


def validate_arc_style_grid_task_packet_v1(packet: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "task_id": None,
        "task_source": None,
        "blocked_reason_labels": [],
        "grid_validation": None,
        "train_pair_validation_count": 0,
    }
    if not isinstance(packet, Mapping):
        result["blocked_reason_labels"].append("packet_not_mapping")
        return result
    missing = [field for field in REQUIRED_TASK_PACKET_FIELDS_V1 if field not in packet]
    if missing:
        result["blocked_reason_labels"].append("missing_required_fields")
        result["blocked_reason_labels"].extend(f"missing:{field}" for field in missing)
        return result

    result["task_id"] = _safe_text(packet.get("task_id"))
    result["task_source"] = _safe_text(packet.get("task_source"))
    if not result["task_id"]:
        result["blocked_reason_labels"].append("empty_task_id")
    if not result["task_source"]:
        result["blocked_reason_labels"].append("empty_task_source")

    train_pairs = packet.get("train_pairs", [])
    if not isinstance(train_pairs, list):
        result["blocked_reason_labels"].append("train_pairs_not_list")
        train_pairs = []
    for pair in train_pairs:
        pair_result = validate_arc_style_grid_train_pair_v1(pair)
        result["train_pair_validation_count"] += 1
        if not pair_result["valid"]:
            result["blocked_reason_labels"].append(f"train_pair_invalid:{pair_result.get('pair_id')}")
            result["blocked_reason_labels"].extend(pair_result["blocked_reason_labels"])

    test_input = packet.get("test_input")
    test_validation = _validate_grid_payload(test_input)
    result["grid_validation"] = test_validation
    if not test_validation["valid"]:
        result["blocked_reason_labels"].append("invalid_test_input")
        result["blocked_reason_labels"].extend(f"test:{reason}" for reason in test_validation["reasons"])

    if not isinstance(packet.get("grid_format"), Mapping):
        result["blocked_reason_labels"].append("grid_format_not_mapping")
    if not isinstance(packet.get("palette"), Mapping):
        result["blocked_reason_labels"].append("palette_not_mapping")
    for field in ("object_candidates", "transformation_candidates", "constraint_candidates", "candidate_outputs", "validation_results", "failure_notes"):
        if not isinstance(packet.get(field), list):
            result["blocked_reason_labels"].append(f"{field}_not_list")
    if len(result["blocked_reason_labels"]) == 0:
        result["valid"] = True
    return result


def summarize_arc_style_grid_task_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_arc_style_grid_task_packet_v1(packet)
    if not isinstance(packet, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "task_id": None,
            "task_source": None,
            "valid": False,
            "train_pair_count": 0,
            "candidate_output_count": 0,
            "toy_task": False,
            "internal_synthetic_only": False,
            "blocked_reason_labels": validation["blocked_reason_labels"],
        }
    trace = packet.get("trace", {}) if isinstance(packet.get("trace"), Mapping) else {}
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "task_id": _safe_text(packet.get("task_id")),
        "task_source": _safe_text(packet.get("task_source")),
        "valid": validation["valid"],
        "train_pair_count": len(packet.get("train_pairs", [])) if isinstance(packet.get("train_pairs"), list) else 0,
        "candidate_output_count": len(packet.get("candidate_outputs", [])) if isinstance(packet.get("candidate_outputs"), list) else 0,
        "toy_task": bool(trace.get("toy_task", False)),
        "internal_synthetic_only": bool(trace.get("internal_synthetic_only", False)),
        "toy_task_type": _safe_text(trace.get("toy_task_type"), "synthetic"),
        "grid_format_id": _safe_text((packet.get("grid_format") or {}).get("format_id")),
        "palette_id_count": len((packet.get("palette") or {}).get("palette_ids", [])),
        "blocked_reason_labels": validation["blocked_reason_labels"],
    }


def _toy_pair(pair_id: str, input_grid: Sequence[Any], output_grid: Sequence[Any], notes: str) -> dict[str, Any]:
    return build_arc_style_grid_train_pair_v1(pair_id, input_grid, output_grid, notes)


def build_internal_arc_style_grid_toy_tasks_v1() -> list[dict[str, Any]]:
    """Return internal synthetic toy tasks only.

    These fixtures are hand-authored Phase 1 examples for schema validation and
    adapter boundary design. They are not ARC dataset examples.
    """

    tasks: list[dict[str, Any]] = []

    # 1) copy grid
    copy_task = build_arc_style_grid_task_packet_v1(
        task_id="toy_copy_grid_v1",
        task_source=TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
        train_pairs=[_toy_pair("copy_pair_1", [[1, 2], [3, 4]], [[1, 2], [3, 4]], "copy the grid exactly")],
        test_input=[[5, 6], [7, 8]],
        validation_results=[],
        failure_notes=[],
        trace={"toy_task_type": "copy_grid", "internal_synthetic_only": True, "toy_task": True},
    )
    tasks.append(copy_task)

    # 2) recolor one symbol
    recolor_task = build_arc_style_grid_task_packet_v1(
        task_id="toy_recolor_symbol_v1",
        task_source=TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
        train_pairs=[_toy_pair("recolor_pair_1", [["a", "a"], ["a", "b"]], [["a", "a"], ["a", "c"]], "recolor the minority symbol")],
        test_input=[["a", "b"], ["b", "b"]],
        validation_results=[],
        failure_notes=[],
        trace={"toy_task_type": "recolor_symbol", "internal_synthetic_only": True, "toy_task": True},
    )
    tasks.append(recolor_task)

    # 3) move single object
    move_task = build_arc_style_grid_task_packet_v1(
        task_id="toy_move_single_object_v1",
        task_source=TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
        train_pairs=[_toy_pair("move_pair_1", [[0, 0, 0], [0, 9, 0], [0, 0, 0]], [[0, 0, 0], [0, 0, 0], [0, 9, 0]], "move the single object down one cell")],
        test_input=[[0, 0, 0], [0, 7, 0], [0, 0, 0]],
        validation_results=[],
        failure_notes=[],
        trace={"toy_task_type": "move_single_object", "internal_synthetic_only": True, "toy_task": True},
    )
    tasks.append(move_task)

    # 4) complete simple symmetry
    symmetry_task = build_arc_style_grid_task_packet_v1(
        task_id="toy_complete_symmetry_v1",
        task_source=TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
        train_pairs=[_toy_pair("sym_pair_1", [[1, 0, 0], [0, 0, 0], [0, 0, 1]], [[1, 0, 1], [0, 0, 0], [1, 0, 1]], "mirror the diagonal markers into a simple symmetry")],
        test_input=[[2, 0, 0], [0, 0, 0], [0, 0, 2]],
        validation_results=[],
        failure_notes=[],
        trace={"toy_task_type": "complete_symmetry", "internal_synthetic_only": True, "toy_task": True},
    )
    tasks.append(symmetry_task)

    # 5) border / frame fill toy task
    border_task = build_arc_style_grid_task_packet_v1(
        task_id="toy_border_frame_fill_v1",
        task_source=TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
        train_pairs=[_toy_pair("border_pair_1", [[0, 0, 0], [0, 5, 0], [0, 0, 0]], [[5, 5, 5], [5, 5, 5], [5, 5, 5]], "fill or frame the border pattern")],
        test_input=[[0, 0, 0], [0, 4, 0], [0, 0, 0]],
        validation_results=[],
        failure_notes=[],
        trace={"toy_task_type": "border_frame_fill", "internal_synthetic_only": True, "toy_task": True},
    )
    tasks.append(border_task)

    return tasks


def build_internal_arc_style_grid_toy_task_fixtures_v1() -> list[dict[str, Any]]:
    return build_internal_arc_style_grid_toy_tasks_v1()


__all__ = [
    "SCHEMA_VERSION_V1",
    "GRID_FORMAT_ID_V1",
    "TASK_SOURCE_INTERNAL_SYNTHETIC_V1",
    "MAX_GRID_WIDTH_V1",
    "MAX_GRID_HEIGHT_V1",
    "TOY_TASK_TYPES_V1",
    "build_arc_style_grid_metadata_v1",
    "build_arc_style_grid_train_pair_v1",
    "build_arc_style_grid_candidate_result_v1",
    "build_arc_style_grid_task_packet_v1",
    "validate_arc_style_grid_train_pair_v1",
    "validate_arc_style_grid_candidate_result_v1",
    "validate_arc_style_grid_task_packet_v1",
    "summarize_arc_style_grid_task_packet_v1",
    "to_arc_style_grid_task_json_safe_v1",
    "build_internal_arc_style_grid_toy_tasks_v1",
    "build_internal_arc_style_grid_toy_task_fixtures_v1",
]
