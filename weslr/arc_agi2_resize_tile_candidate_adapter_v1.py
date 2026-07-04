"""ARC-AGI-2 resize / tile / canvas-pattern candidate adapter V1.

Bridges the resize/tile/canvas capability solver into the ARC-AGI-2 top-2
attempt contract. Synthetic-only, deterministic, and metadata-safe.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence

from weslr.arc_agi2_submission_contract import (
    build_arc_agi2_submission_packet_v1,
    build_arc_agi2_submission_task_entry_v1,
    build_arc_agi2_top2_attempt_packet_v1,
    validate_arc_agi2_top2_attempt_packet_v1,
)
from weslr.arc_resize_tile_canvas_v1 import solve_resize_tile_task

SCHEMA_VERSION_V1 = "ArcAgi2ResizeTileCandidateAdapterV1"
ADAPTER_NAME_V1 = "arc_agi2_resize_tile_candidate_adapter_v1"

RESIZE_TILE_FAMILY_EVIDENCE_V1 = {
    "crop_foreground_bbox": ["resize_tile", "crop", "foreground_bbox"],
    "tile_repeat": ["resize_tile", "tile", "repeat"],
    "integer_scale": ["resize_tile", "scale", "integer"],
    "border_padding": ["resize_tile", "border", "padding"],
    "crop_then_tile": ["resize_tile", "crop", "tile"],
}

RESIZE_TILE_FAMILY_ORDER_V1 = {
    "crop_foreground_bbox": 0,
    "tile_repeat": 1,
    "integer_scale": 2,
    "border_padding": 3,
    "crop_then_tile": 4,
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
    return [list(row) for row in deepcopy(list(grid)) if isinstance(row, Sequence) and not isinstance(row, (str, bytes, bytearray))]


def _grid_signature(grid: Any) -> str:
    return repr(deepcopy(grid))


def _task_id(task_id: Any) -> str:
    value = _safe_text(task_id, "arc_agi2_resize_tile_task")
    return value or "arc_agi2_resize_tile_task"


def _test_input_index(value: Any) -> int:
    try:
        return max(0, int(value))
    except Exception:
        return 0


def _candidate_packet_from_resize_candidate(
    *,
    task_id: str,
    test_input_index: int,
    resize_candidate: Mapping[str, Any],
    rank_hint: int,
) -> dict[str, Any]:
    family = _safe_text(resize_candidate.get("family"), "crop_foreground_bbox")
    family_rank = RESIZE_TILE_FAMILY_ORDER_V1.get(family, 99)
    confidence = float(resize_candidate.get("confidence", 1.0) or 1.0)
    output = deepcopy(resize_candidate.get("output"))
    trace = resize_candidate.get("trace") if isinstance(resize_candidate.get("trace"), Mapping) else {}
    metadata = {
        "adapter_name": ADAPTER_NAME_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "task_id": task_id,
        "test_input_index": test_input_index,
        "resize_family": family,
        "resize_family_rank": family_rank,
        "resize_rank_hint": rank_hint,
        "synthetic_only": True,
        "source_kind": "resize_tile_solver",
        "trace_labels": ["resize_tile", family, "synthetic_only"],
    }
    metadata.update({k: deepcopy(v) for k, v in trace.items() if k not in {"output", "expected_output", "grid"}})
    return {
        "candidate_id": f"{task_id}:{test_input_index}:{family_rank:02d}:{family}",
        "source_candidate_id": f"{task_id}:{test_input_index}:{family}",
        "source_kind": "resize_tile_solver",
        "synthetic_only": True,
        "grid": output,
        "confidence_label": "confirmed" if confidence >= 1.0 else ("high" if confidence >= 0.75 else "medium"),
        "evidence_labels": RESIZE_TILE_FAMILY_EVIDENCE_V1.get(family, ["resize_tile", "synthetic_only"]),
        "leakage_flags": {
            "uses_test_output": False,
            "uses_solution_file": False,
            "uses_answer_key": False,
            "uses_hidden_private_data": False,
            "uses_task_id_shortcut": False,
            "uses_notes_shortcut": False,
            "lookup_table_detected": False,
        },
        "metadata": metadata,
    }


def _safe_fallback_candidate_packets(*, task_id: str, test_input_index: int, test_input: Any) -> list[dict[str, Any]]:
    input_grid = _grid_copy(test_input)
    zero_grid = [[0 for _ in row] for row in input_grid] if input_grid else [[0]]
    return [
        {
            "candidate_id": f"{task_id}:{test_input_index}:fallback_copy",
            "source_candidate_id": f"{task_id}:{test_input_index}:fallback_copy",
            "source_kind": "safe_deterministic_fallback",
            "synthetic_only": True,
            "grid": input_grid,
            "confidence_label": "low",
            "evidence_labels": ["safe_fallback", "copy", "deterministic"],
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
                "adapter_name": ADAPTER_NAME_V1,
                "schema_version": SCHEMA_VERSION_V1,
                "task_id": task_id,
                "test_input_index": test_input_index,
                "fallback_kind": "identity_copy",
                "synthetic_only": True,
                "source_kind": "safe_deterministic_fallback",
                "trace_labels": ["fallback", "identity_copy", "safe"],
            },
        },
        {
            "candidate_id": f"{task_id}:{test_input_index}:fallback_zero",
            "source_candidate_id": f"{task_id}:{test_input_index}:fallback_zero",
            "source_kind": "safe_deterministic_fallback",
            "synthetic_only": True,
            "grid": zero_grid,
            "confidence_label": "unknown",
            "evidence_labels": ["safe_fallback", "zero_grid", "deterministic"],
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
                "adapter_name": ADAPTER_NAME_V1,
                "schema_version": SCHEMA_VERSION_V1,
                "task_id": task_id,
                "test_input_index": test_input_index,
                "fallback_kind": "zero_grid",
                "synthetic_only": True,
                "source_kind": "safe_deterministic_fallback",
                "trace_labels": ["fallback", "zero_grid", "safe"],
            },
        },
    ]


def _candidate_packets_for_top2(
    *,
    task_id: str,
    test_input_index: int,
    test_input: Any,
    resize_candidates: Sequence[Mapping[str, Any]],
    fallback_candidate_packets: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    ranked_resize_candidates = sorted(
        [dict(candidate) for candidate in resize_candidates],
        key=lambda candidate: (
            -float(candidate.get("confidence", 0.0) or 0.0),
            RESIZE_TILE_FAMILY_ORDER_V1.get(_safe_text(candidate.get("family"), ""), 99),
            _safe_text(candidate.get("family"), ""),
            _grid_signature(candidate.get("output")),
        ),
    )
    adapted = [
        _candidate_packet_from_resize_candidate(
            task_id=task_id,
            test_input_index=test_input_index,
            resize_candidate=candidate,
            rank_hint=index + 1,
        )
        for index, candidate in enumerate(ranked_resize_candidates)
    ]
    if len(adapted) >= 2:
        return adapted[:2], False

    fallback_packets = [deepcopy(packet) for packet in (fallback_candidate_packets or []) if isinstance(packet, Mapping)]
    if adapted:
        candidate_packets = adapted + fallback_packets
        if len(candidate_packets) < 2:
            candidate_packets.extend(
                _safe_fallback_candidate_packets(task_id=task_id, test_input_index=test_input_index, test_input=test_input)[: 2 - len(candidate_packets)]
            )
        return candidate_packets[:2], True

    if len(fallback_packets) >= 2:
        return fallback_packets[:2], True

    safe_fallbacks = _safe_fallback_candidate_packets(task_id=task_id, test_input_index=test_input_index, test_input=test_input)
    return (fallback_packets + safe_fallbacks)[:2], True


def build_arc_agi2_resize_tile_top2_attempt_packet_v1(
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Any,
    *,
    task_id: Any = "arc_agi2_resize_tile_task",
    test_input_index: Any = 0,
    fallback_candidate_packets: Sequence[Mapping[str, Any]] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    task_id_text = _task_id(task_id)
    test_input_index_int = _test_input_index(test_input_index)
    resize_candidates = solve_resize_tile_task(train_pairs, test_input)
    candidate_packets, used_fallback = _candidate_packets_for_top2(
        task_id=task_id_text,
        test_input_index=test_input_index_int,
        test_input=test_input,
        resize_candidates=resize_candidates,
        fallback_candidate_packets=fallback_candidate_packets,
    )
    packet_metadata = {
        "adapter_name": ADAPTER_NAME_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "task_id": task_id_text,
        "test_input_index": test_input_index_int,
        "resize_candidate_count": len(resize_candidates),
        "used_fallback": used_fallback,
        "synthetic_only": True,
        "trace_labels": ["resize_tile", "top2_attempts", "synthetic_only"],
    }
    if isinstance(metadata, Mapping):
        packet_metadata.update({k: deepcopy(v) for k, v in metadata.items()})
    return build_arc_agi2_top2_attempt_packet_v1(
        task_id=task_id_text,
        test_input_index=test_input_index_int,
        candidate_packets=candidate_packets,
        metadata=packet_metadata,
    )


def build_arc_agi2_resize_tile_submission_v1(
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
                metadata={"adapter_name": ADAPTER_NAME_V1, "synthetic_only": True},
            )
        )
    return build_arc_agi2_submission_packet_v1(
        task_entries=task_entries,
        metadata={"adapter_name": ADAPTER_NAME_V1, "synthetic_only": True, **(dict(metadata or {}))},
    )


def run_arc_agi2_resize_tile_candidate_mini_suite_v1(cases: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    solved_count = 0
    exact_match_count = 0
    fallback_count = 0
    malformed_count = 0
    exactly_two_output_pass = True
    for index, case in enumerate(cases):
        task_id = _safe_text(case.get("task_id"), f"case_{index}")
        packet = build_arc_agi2_resize_tile_top2_attempt_packet_v1(
            case.get("train_pairs", []),
            case.get("test_input"),
            task_id=task_id,
            test_input_index=case.get("test_input_index", 0),
            fallback_candidate_packets=case.get("fallback_candidate_packets"),
            metadata=case.get("metadata"),
        )
        validation = validate_arc_agi2_top2_attempt_packet_v1(packet)
        attempts = packet.get("attempts", []) if isinstance(packet, Mapping) else []
        exactly_two_output_pass = exactly_two_output_pass and bool(validation.get("valid", False)) and len(attempts) == 2
        if not validation.get("valid", False):
            malformed_count += 1
        else:
            expected_output = case.get("expected_output")
            exact = expected_output is not None and attempts[0]["grid"] == expected_output
            if exact:
                solved_count += 1
                exact_match_count += 1
            if int(packet.get("metadata", {}).get("resize_candidate_count", 0) or 0) == 0:
                fallback_count += 1
        results.append({"task_id": task_id, "packet": packet, "validation": validation})
    return {
        "case_count": len(cases),
        "solved_count": solved_count,
        "exact_match_count": exact_match_count,
        "fallback_count": fallback_count,
        "malformed_count": malformed_count,
        "exactly_two_output_pass": exactly_two_output_pass,
        "results": results,
    }


__all__ = [
    "ADAPTER_NAME_V1",
    "SCHEMA_VERSION_V1",
    "build_arc_agi2_resize_tile_submission_v1",
    "build_arc_agi2_resize_tile_top2_attempt_packet_v1",
    "run_arc_agi2_resize_tile_candidate_mini_suite_v1",
]
