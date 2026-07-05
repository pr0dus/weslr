"""ARC-AGI-2 capability candidate aggregator V1.

Coordinates the object/bbox, shape-geometry, color-role, resize/tile, and
count/quantity synthetic adapters into one stable top-2 attempt path. It
deduplicates identical outputs, applies a fixed family priority, and falls
back deterministically when no capability candidate is available.

Synthetic-only. No public ARC ingestion. No scoring claims. No Kaggle writes.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence

from weslr.arc_agi2_object_bbox_candidate_adapter_v1 import (
    ADAPTER_NAME_V1 as OBJECT_BBOX_ADAPTER_NAME_V1,
    build_arc_agi2_object_bbox_top2_attempt_packet_v1,
)
from weslr.arc_agi2_color_role_candidate_adapter_v1 import (
    ADAPTER_NAME_V1 as COLOR_ROLE_ADAPTER_NAME_V1,
    build_arc_agi2_color_role_top2_attempt_packet_v1,
)
from weslr.arc_agi2_resize_tile_candidate_adapter_v1 import (
    ADAPTER_NAME_V1 as RESIZE_TILE_ADAPTER_NAME_V1,
    build_arc_agi2_resize_tile_top2_attempt_packet_v1,
)
from weslr.arc_agi2_count_quantity_candidate_adapter_v1 import (
    ADAPTER_NAME_V1 as COUNT_QUANTITY_ADAPTER_NAME_V1,
    build_arc_agi2_count_quantity_top2_attempt_packet_v1,
)
from weslr.arc_agi2_shape_geometry_candidate_adapter_v1 import (
    ADAPTER_NAME_V1 as SHAPE_GEOMETRY_ADAPTER_NAME_V1,
    build_arc_agi2_shape_geometry_top2_attempt_packet_v1,
)
from weslr.arc_agi2_symmetry_line_candidate_adapter_v1 import (
    ADAPTER_NAME_V1 as SYMMETRY_LINE_ADAPTER_NAME_V1,
    build_arc_agi2_symmetry_line_top2_attempt_packet_v1,
)
from weslr.arc_agi2_submission_contract import (
    build_arc_agi2_submission_packet_v1,
    build_arc_agi2_submission_task_entry_v1,
    build_arc_agi2_top2_attempt_packet_v1,
    validate_arc_agi2_top2_attempt_packet_v1,
)

SCHEMA_VERSION_V1 = "ArcAgi2CapabilityCandidateAggregatorV1"
AGGREGATOR_NAME_V1 = "arc_agi2_capability_candidate_aggregator_v1"

FAMILY_PRIORITY_V1 = {
    "object_bbox": 0,
    "shape_geometry": 1,
    "color_role": 2,
    "resize_tile": 3,
    "count_quantity": 4,
    "fallback": 5,
}

SOURCE_ADAPTER_PRIORITY_V1 = {
    OBJECT_BBOX_ADAPTER_NAME_V1: 0,
    SHAPE_GEOMETRY_ADAPTER_NAME_V1: 1,
    COLOR_ROLE_ADAPTER_NAME_V1: 2,
    RESIZE_TILE_ADAPTER_NAME_V1: 3,
    COUNT_QUANTITY_ADAPTER_NAME_V1: 4,
    AGGREGATOR_NAME_V1: 5,
}

SOURCE_KIND_TO_FAMILY_V1 = {
    "object_bbox_solver": "object_bbox",
    "shape_geometry_solver": "shape_geometry",
    "color_role_solver": "color_role",
    "resize_tile_solver": "resize_tile",
    "count_quantity_solver": "count_quantity",
    "symmetry_line_solver": "symmetry_line",
    "safe_deterministic_fallback": "fallback",
}

TRIMMED_METADATA_KEYS_V1 = {
    "adapter_name",
    "schema_version",
    "task_id",
    "test_input_index",
    "source_kind",
    "source_adapter",
    "source_family",
    "source_family_label",
    "family_priority",
    "train_fit",
    "candidate_score",
    "validation_status",
    "trace_label",
    "trace_labels",
    "solver_family",
    "solver_family_rank",
    "shape_family",
    "shape_family_order",
    "color_family",
    "color_family_rank",
    "resize_family",
    "resize_family_rank",
    "count_family",
    "count_family_rank",
    "rule",
    "rule_family",
    "output_mode",
    "transform_parameters",
    "fallback_kind",
    "synthetic_only",
    "duplicate_family_labels",
    "duplicate_source_candidate_ids",
    "dedupe_reason",
}


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int)):
        return str(value)
    return default if value == "" else str(value)


def _grid_copy(grid: Any) -> list[list[Any]]:
    if not isinstance(grid, Sequence) or isinstance(grid, (str, bytes, bytearray)):
        return []
    copied: list[list[Any]] = []
    for row in deepcopy(list(grid)):
        if isinstance(row, Sequence) and not isinstance(row, (str, bytes, bytearray)):
            copied.append(list(row))
    return copied


def _grid_signature(grid: Any) -> str:
    return repr(deepcopy(grid))


def _task_id(value: Any) -> str:
    text = _safe_text(value, "arc_agi2_capability_candidate_task")
    return text or "arc_agi2_capability_candidate_task"


def _test_input_index(value: Any) -> int:
    try:
        return max(0, int(value))
    except Exception:
        return 0


def _family_for_attempt(attempt: Mapping[str, Any]) -> tuple[str, str]:
    metadata = attempt.get("metadata") if isinstance(attempt.get("metadata"), Mapping) else {}
    source_kind = _safe_text(metadata.get("source_kind") or attempt.get("source_kind"), "candidate_like")
    family = SOURCE_KIND_TO_FAMILY_V1.get(source_kind, "fallback")
    label = "fallback"
    if family == "object_bbox":
        label = _safe_text(metadata.get("solver_family") or attempt.get("source_candidate_id"), "object_bbox")
    elif family == "shape_geometry":
        label = _safe_text(metadata.get("shape_family") or attempt.get("source_candidate_id"), "shape_geometry")
    elif family == "color_role":
        label = _safe_text(metadata.get("color_family") or attempt.get("source_candidate_id"), "color_role")
    elif family == "resize_tile":
        label = _safe_text(metadata.get("resize_family") or attempt.get("source_candidate_id"), "resize_tile")
    elif family == "count_quantity":
        label = _safe_text(metadata.get("count_family") or attempt.get("source_candidate_id"), "count_quantity")
    elif family == "symmetry_line":
        label = _safe_text(metadata.get("source_family") or attempt.get("source_candidate_id"), "symmetry_line")
    elif family == "fallback":
        label = _safe_text(metadata.get("fallback_kind") or attempt.get("source_candidate_id"), "fallback")
    return family, label


def _family_priority(family: str) -> int:
    return FAMILY_PRIORITY_V1.get(family, 99)


def _source_adapter_priority(source_adapter: str) -> int:
    return SOURCE_ADAPTER_PRIORITY_V1.get(source_adapter, 99)


def _confidence_score_label(candidate: Mapping[str, Any]) -> str:
    label = _safe_text(candidate.get("confidence_label"), "unknown")
    if label:
        return label
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), Mapping) else {}
    return _safe_text(metadata.get("confidence_label"), "unknown") or "unknown"


def _train_fit_value(candidate: Mapping[str, Any]) -> bool:
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), Mapping) else {}
    if "train_fit" in metadata:
        return bool(metadata.get("train_fit", False))
    status = _safe_text(metadata.get("validation_status"), "unknown")
    return status in {"exact_match", "fit"}


def _candidate_score(candidate: Mapping[str, Any]) -> int:
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), Mapping) else {}
    raw = metadata.get("candidate_score")
    try:
        return int(raw)
    except Exception:
        confidence = _confidence_score_label(candidate).lower()
        return {
            "confirmed": 40,
            "high": 30,
            "medium": 20,
            "low": 10,
            "unknown": 0,
        }.get(confidence, 0)


def _trace_label(candidate: Mapping[str, Any]) -> str:
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), Mapping) else {}
    labels = metadata.get("trace_labels")
    if isinstance(labels, Sequence) and labels and not isinstance(labels, (str, bytes, bytearray)):
        return _safe_text(labels[0], "")
    for key in ("trace_label", "source_kind", "source_adapter"):
        value = _safe_text(metadata.get(key), "")
        if value:
            return value
    return _safe_text(candidate.get("source_candidate_id"), "candidate")


def _compact_metadata(source_metadata: Mapping[str, Any], *, keep_keys: set[str]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key in keep_keys:
        if key in source_metadata:
            compact[key] = deepcopy(source_metadata[key])
    return compact


def _normalize_source_attempt(
    *,
    task_id: str,
    test_input_index: int,
    source_adapter: str,
    source_packet_metadata: Mapping[str, Any],
    attempt: Mapping[str, Any],
    source_order: int,
) -> dict[str, Any]:
    family_group, family_label = _family_for_attempt(attempt)
    metadata = attempt.get("metadata") if isinstance(attempt.get("metadata"), Mapping) else {}
    source_candidate_id = _safe_text(attempt.get("source_candidate_id"), f"{task_id}:{test_input_index}:{source_adapter}:{source_order}")
    normalized_source_candidate_id = f"{task_id}:{test_input_index}:{_source_adapter_priority(source_adapter):02d}:{_family_priority(family_group):02d}:{family_label}:{source_candidate_id}"
    compact_trace = _compact_metadata(
        {**dict(source_packet_metadata), **dict(metadata)},
        keep_keys=TRIMMED_METADATA_KEYS_V1,
    )
    compact_trace.update(
        {
            "task_id": task_id,
            "test_input_index": test_input_index,
            "source_adapter": source_adapter,
            "source_family": family_group,
            "source_family_label": family_label,
            "family_priority": _family_priority(family_group),
            "train_fit": _train_fit_value(attempt),
            "candidate_score": _candidate_score(attempt),
            "trace_label": _trace_label(attempt),
            "synthetic_only": True,
        }
    )
    if family_group == "fallback":
        compact_trace.setdefault("dedupe_reason", "fallback_candidate")
    return {
        "candidate_id": normalized_source_candidate_id,
        "source_candidate_id": normalized_source_candidate_id,
        "source_kind": family_group if family_group != "fallback" else "safe_deterministic_fallback",
        "synthetic_only": True,
        "grid": deepcopy(attempt.get("grid")),
        "confidence_label": _confidence_score_label(attempt),
        "evidence_labels": list(attempt.get("evidence_labels", [])) if isinstance(attempt.get("evidence_labels"), list) else [],
        "leakage_flags": deepcopy(attempt.get("leakage_flags", {})) if isinstance(attempt.get("leakage_flags"), Mapping) else {},
        "metadata": compact_trace,
    }


def _safe_fallback_candidates(
    *,
    task_id: str,
    test_input_index: int,
    test_input: Any,
    used_signatures: set[str],
) -> list[dict[str, Any]]:
    input_grid = _grid_copy(test_input)
    if not input_grid:
        input_grid = [[0]]
    height = len(input_grid)
    width = len(input_grid[0]) if input_grid and input_grid[0] else 1

    candidate_grids: list[tuple[str, list[list[Any]]]] = []
    candidate_grids.append(("identity_copy", _grid_copy(input_grid)))
    candidate_grids.append(("zero_grid", [[0 for _ in range(width)] for _ in range(height)]))
    candidate_grids.append(("first_row_zero", [[0 for _ in range(width)]] + [list(row) for row in input_grid[1:]] if height > 1 else [[0 for _ in range(width)]]))
    candidate_grids.append(("first_col_zero", [[0] + list(row[1:]) if row else [0] for row in input_grid]))
    corner = [[0 for _ in range(width)] for _ in range(height)]
    corner[0][0] = 1
    candidate_grids.append(("corner_marker", corner))

    fallbacks: list[dict[str, Any]] = []
    for fallback_index, (kind, grid) in enumerate(candidate_grids):
        signature = _grid_signature(grid)
        if signature in used_signatures:
            continue
        used_signatures.add(signature)
        fallbacks.append(
            {
                "candidate_id": f"{task_id}:{test_input_index}:fallback:{kind}",
                "source_candidate_id": f"{task_id}:{test_input_index}:99:02:fallback:{kind}",
                "source_kind": "safe_deterministic_fallback",
                "synthetic_only": True,
                "grid": grid,
                "confidence_label": "low" if fallback_index == 0 else "unknown",
                "evidence_labels": ["safe_fallback", kind, "deterministic"],
                "leakage_flags": {
                    "uses_test_output": False,
                    "uses_solution_file": False,
                    "uses_answer_key": False,
                    "uses_hidden_private_data": False,
                    "uses_task_id_shortcut": False,
                    "uses_notes_shortcut": False,
                    "lookup_table_detected": False,
                },
                "metadata": {
                    "adapter_name": AGGREGATOR_NAME_V1,
                    "schema_version": SCHEMA_VERSION_V1,
                    "task_id": task_id,
                    "test_input_index": test_input_index,
                    "source_adapter": AGGREGATOR_NAME_V1,
                    "source_family": "fallback",
                    "source_family_label": kind,
                    "family_priority": _family_priority("fallback"),
                    "fallback_kind": kind,
                    "synthetic_only": True,
                    "trace_label": f"fallback:{kind}",
                    "trace_labels": ["fallback", kind, "safe"],
                    "candidate_score": 10 if fallback_index == 0 else 0,
                    "train_fit": False,
                    "dedupe_reason": "generated_fallback",
                },
            }
        )
        if len(fallbacks) >= 2:
            break
    return fallbacks


def _rank_key(candidate: Mapping[str, Any]) -> tuple[Any, ...]:
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), Mapping) else {}
    return (
        0 if bool(metadata.get("train_fit", False)) else 1,
        -int(metadata.get("candidate_score", _candidate_score(candidate)) or 0),
        _family_priority(_safe_text(metadata.get("source_family"), "fallback")),
        _source_adapter_priority(_safe_text(metadata.get("source_adapter"), AGGREGATOR_NAME_V1)),
        len(_safe_text(metadata.get("trace_label"), "")),
        _safe_text(candidate.get("source_candidate_id")),
        _grid_signature(candidate.get("grid")),
    )


def _dedupe_candidates(candidates: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    kept: list[dict[str, Any]] = []
    seen: dict[str, dict[str, Any]] = {}
    dedupe_count = 0
    for candidate in sorted([dict(candidate) for candidate in candidates], key=_rank_key):
        signature = _grid_signature(candidate.get("grid"))
        metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), Mapping) else {}
        family_label = _safe_text(metadata.get("source_family_label"), _safe_text(metadata.get("source_family"), "fallback"))
        source_adapter = _safe_text(metadata.get("source_adapter"), AGGREGATOR_NAME_V1)
        if signature not in seen:
            candidate = deepcopy(candidate)
            candidate_metadata = candidate.setdefault("metadata", {})
            candidate_metadata.setdefault("duplicate_family_labels", [])
            candidate_metadata.setdefault("duplicate_source_candidate_ids", [])
            candidate_metadata.setdefault("dedupe_reason", "primary_unique_output")
            seen[signature] = candidate
            kept.append(candidate)
            continue

        dedupe_count += 1
        primary = seen[signature]
        primary_metadata = primary.setdefault("metadata", {})
        duplicate_family_labels = list(primary_metadata.get("duplicate_family_labels", []))
        duplicate_source_candidate_ids = list(primary_metadata.get("duplicate_source_candidate_ids", []))
        duplicate_family_labels.extend([family_label])
        duplicate_source_candidate_ids.extend([_safe_text(candidate.get("source_candidate_id"), "")])
        if source_adapter and source_adapter not in duplicate_family_labels:
            duplicate_family_labels.append(source_adapter)
        primary_metadata["duplicate_family_labels"] = sorted({label for label in duplicate_family_labels if label})
        primary_metadata["duplicate_source_candidate_ids"] = sorted({label for label in duplicate_source_candidate_ids if label})
        primary_metadata["dedupe_reason"] = "duplicate_output_removed"
    return kept, dedupe_count


def _build_source_packets(
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Any,
    *,
    task_id: str,
    test_input_index: int,
    enabled_families: set[str],
) -> list[dict[str, Any]]:
    source_packets: list[dict[str, Any]] = []
    if "object_bbox" in enabled_families:
        packet = build_arc_agi2_object_bbox_top2_attempt_packet_v1(
            train_pairs,
            test_input,
            task_id=task_id,
            test_input_index=test_input_index,
        )
        source_packets.append({"family": "object_bbox", "adapter": OBJECT_BBOX_ADAPTER_NAME_V1, "packet": packet})
    if "shape_geometry" in enabled_families:
        packet = build_arc_agi2_shape_geometry_top2_attempt_packet_v1(
            train_pairs,
            test_input,
            task_id=task_id,
            test_input_index=test_input_index,
        )
        source_packets.append({"family": "shape_geometry", "adapter": SHAPE_GEOMETRY_ADAPTER_NAME_V1, "packet": packet})
    if "color_role" in enabled_families:
        packet = build_arc_agi2_color_role_top2_attempt_packet_v1(
            train_pairs,
            test_input,
            task_id=task_id,
            test_input_index=test_input_index,
        )
        source_packets.append({"family": "color_role", "adapter": COLOR_ROLE_ADAPTER_NAME_V1, "packet": packet})
    if "resize_tile" in enabled_families:
        packet = build_arc_agi2_resize_tile_top2_attempt_packet_v1(
            train_pairs,
            test_input,
            task_id=task_id,
            test_input_index=test_input_index,
        )
        source_packets.append({"family": "resize_tile", "adapter": RESIZE_TILE_ADAPTER_NAME_V1, "packet": packet})
    if "count_quantity" in enabled_families:
        packet = build_arc_agi2_count_quantity_top2_attempt_packet_v1(
            train_pairs,
            test_input,
            task_id=task_id,
            test_input_index=test_input_index,
        )
        source_packets.append({"family": "count_quantity", "adapter": COUNT_QUANTITY_ADAPTER_NAME_V1, "packet": packet})
    if "symmetry_line" in enabled_families:
        packet = build_arc_agi2_symmetry_line_top2_attempt_packet_v1(
            train_pairs,
            test_input,
            task_id=task_id,
            test_input_index=test_input_index,
        )
        source_packets.append({"family": "symmetry_line", "adapter": SYMMETRY_LINE_ADAPTER_NAME_V1, "packet": packet})
    return source_packets


def build_arc_agi2_capability_candidate_top2_attempt_packet_v1(
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Any,
    *,
    task_id: Any = "arc_agi2_capability_candidate_task",
    test_input_index: Any = 0,
    enabled_families: Sequence[str] | None = None,
    trace: bool = False,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    task_id_text = _task_id(task_id)
    test_input_index_int = _test_input_index(test_input_index)
    enabled = {"object_bbox", "shape_geometry", "color_role", "resize_tile", "count_quantity", "symmetry_line", "fallback"}
    if enabled_families is not None:
        enabled = { _safe_text(item) for item in enabled_families if _safe_text(item) }
        if not enabled:
            enabled = {"fallback"}
    source_packets = _build_source_packets(train_pairs, test_input, task_id=task_id_text, test_input_index=test_input_index_int, enabled_families=enabled)
    normalized_candidates: list[dict[str, Any]] = []
    malformed_count = 0
    source_packet_summaries: list[dict[str, Any]] = []
    for source_index, source in enumerate(source_packets):
        packet = source["packet"]
        validation = validate_arc_agi2_top2_attempt_packet_v1(packet)
        source_packet_summaries.append(
            {
                "family": source["family"],
                "adapter": source["adapter"],
                "valid": bool(validation.get("valid", False)),
                "attempt_count": len(packet.get("attempts", [])) if isinstance(packet, Mapping) and isinstance(packet.get("attempts"), list) else 0,
            }
        )
        if not validation.get("valid", False):
            malformed_count += 1
            continue
        packet_metadata = packet.get("metadata") if isinstance(packet.get("metadata"), Mapping) else {}
        attempts = packet.get("attempts", []) if isinstance(packet.get("attempts"), list) else []
        for attempt_index, attempt in enumerate(attempts):
            if not isinstance(attempt, Mapping):
                malformed_count += 1
                continue
            normalized_candidates.append(
                _normalize_source_attempt(
                    task_id=task_id_text,
                    test_input_index=test_input_index_int,
                    source_adapter=source["adapter"],
                    source_packet_metadata=packet_metadata,
                    attempt=attempt,
                    source_order=source_index * 10 + attempt_index,
                )
            )

    unique_candidates, dedupe_count = _dedupe_candidates(normalized_candidates)
    used_signatures = {_grid_signature(candidate.get("grid")) for candidate in unique_candidates}
    if len(unique_candidates) < 2:
        unique_candidates.extend(
            _safe_fallback_candidates(
                task_id=task_id_text,
                test_input_index=test_input_index_int,
                test_input=test_input,
                used_signatures=used_signatures,
            )
        )

    unique_candidates = sorted(unique_candidates, key=_rank_key)
    candidate_packets = unique_candidates[:2]
    used_fallback = any(_safe_text(candidate.get("source_kind")) == "safe_deterministic_fallback" for candidate in candidate_packets)
    packet_metadata = {
        "adapter_name": AGGREGATOR_NAME_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "task_id": task_id_text,
        "test_input_index": test_input_index_int,
        "enabled_families": sorted(enabled),
        "source_packet_summaries": source_packet_summaries,
        "normalized_candidate_count": len(normalized_candidates),
        "unique_candidate_count": len(unique_candidates),
        "dedupe_count": dedupe_count,
        "malformed_count": malformed_count,
        "used_fallback": used_fallback,
        "synthetic_only": True,
        "trace_labels": ["capability_candidate_aggregator", "top2_attempts", "synthetic_only"],
    }
    if trace:
        packet_metadata["trace_enabled"] = True
    if isinstance(metadata, Mapping):
        packet_metadata.update({k: deepcopy(v) for k, v in metadata.items()})
    packet = build_arc_agi2_top2_attempt_packet_v1(
        task_id=task_id_text,
        test_input_index=test_input_index_int,
        candidate_packets=candidate_packets,
        metadata=packet_metadata,
    )
    return packet


def build_arc_agi2_capability_candidate_submission_v1(
    task_packets: Sequence[Mapping[str, Any]],
    *,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    task_entries = []
    for packet in task_packets:
        task_entries.append(
            build_arc_agi2_submission_task_entry_v1(
                task_id=_safe_text(packet.get("task_id")),
                test_input_packets=[packet],
                metadata={"adapter_name": AGGREGATOR_NAME_V1, "synthetic_only": True},
            )
        )
    return build_arc_agi2_submission_packet_v1(
        task_entries=task_entries,
        metadata={"adapter_name": AGGREGATOR_NAME_V1, "synthetic_only": True, **(dict(metadata or {}))},
    )


def run_arc_agi2_capability_candidate_aggregator_mini_suite_v1(
    cases: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    bbox_solved_count = 0
    geometry_solved_count = 0
    color_role_solved_count = 0
    resize_tile_solved_count = 0
    count_quantity_solved_count = 0
    fallback_count = 0
    dedupe_count = 0
    malformed_count = 0
    exactly_two_output_pass = True
    for index, case in enumerate(cases):
        task_id = _safe_text(case.get("task_id"), f"case_{index}")
        packet = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(
            case.get("train_pairs", []),
            case.get("test_input"),
            task_id=task_id,
            test_input_index=case.get("test_input_index", 0),
            enabled_families=case.get("enabled_families"),
            trace=bool(case.get("trace", False)),
            metadata=case.get("metadata"),
        )
        validation = validate_arc_agi2_top2_attempt_packet_v1(packet)
        attempts = packet.get("attempts", []) if isinstance(packet, Mapping) else []
        exactly_two_output_pass = exactly_two_output_pass and bool(validation.get("valid", False)) and len(attempts) == 2
        if not validation.get("valid", False):
            malformed_count += 1
        else:
            packet_meta = packet.get("metadata", {}) if isinstance(packet.get("metadata"), Mapping) else {}
            if int(packet_meta.get("dedupe_count", 0) or 0) > 0:
                dedupe_count += int(packet_meta.get("dedupe_count", 0) or 0)
            if bool(packet_meta.get("used_fallback", False)):
                fallback_count += 1
            if any(_safe_text(attempt.get("metadata", {}).get("source_family")) == "object_bbox" for attempt in attempts if isinstance(attempt, Mapping)):
                bbox_solved_count += 1
            if any(_safe_text(attempt.get("metadata", {}).get("source_family")) == "shape_geometry" for attempt in attempts if isinstance(attempt, Mapping)):
                geometry_solved_count += 1
            if any(_safe_text(attempt.get("metadata", {}).get("source_family")) == "color_role" for attempt in attempts if isinstance(attempt, Mapping)):
                color_role_solved_count += 1
            if any(_safe_text(attempt.get("metadata", {}).get("source_family")) == "resize_tile" for attempt in attempts if isinstance(attempt, Mapping)):
                resize_tile_solved_count += 1
            if any(_safe_text(attempt.get("metadata", {}).get("source_family")) == "count_quantity" for attempt in attempts if isinstance(attempt, Mapping)):
                count_quantity_solved_count += 1
        results.append({"task_id": task_id, "packet": packet, "validation": validation})
    return {
        "case_count": len(cases),
        "bbox_solved_count": bbox_solved_count,
        "geometry_solved_count": geometry_solved_count,
        "color_role_solved_count": color_role_solved_count,
        "resize_tile_solved_count": resize_tile_solved_count,
        "count_quantity_solved_count": count_quantity_solved_count,
        "fallback_count": fallback_count,
        "dedupe_count": dedupe_count,
        "malformed_count": malformed_count,
        "exactly_two_output_pass": exactly_two_output_pass,
        "results": results,
    }


__all__ = [
    "AGGREGATOR_NAME_V1",
    "SCHEMA_VERSION_V1",
    "build_arc_agi2_capability_candidate_submission_v1",
    "build_arc_agi2_capability_candidate_top2_attempt_packet_v1",
    "run_arc_agi2_capability_candidate_aggregator_mini_suite_v1",
]
