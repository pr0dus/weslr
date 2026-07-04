"""ARC-AGI-2 object/bbox candidate adapter V1.

This adapter bridges the object-extraction + bbox capability solver into the
existing ARC-AGI-2 top-2 attempt contract. It is deterministic, metadata-safe,
and synthetic-only.

No public ARC ingestion. No scoring claims. No submission writes.
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
from weslr.arc_object_bbox_solver_v1 import solve_object_bbox_task

SCHEMA_VERSION_V1 = "ArcAgi2ObjectBboxCandidateAdapterV1"
ADAPTER_NAME_V1 = "arc_agi2_object_bbox_candidate_adapter_v1"

OBJECT_BBOX_FAMILY_ORDER_V1 = {
    "bbox_crop_all_foreground": 0,
    "bbox_crop_largest_object": 1,
    "bbox_crop_selected_color_object": 2,
    "translation_single_object": 3,
}

SUPPORTED_FAMILY_EVIDENCE_V1 = {
    "bbox_crop_all_foreground": ["object_bbox", "crop", "foreground_bbox"],
    "bbox_crop_largest_object": ["object_bbox", "crop", "largest_object"],
    "bbox_crop_selected_color_object": ["object_bbox", "crop", "selected_color"],
    "translation_single_object": ["object_bbox", "translate", "single_object"],
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
    return str(deepcopy(grid))


def _task_id(task_id: Any) -> str:
    value = _safe_text(task_id, "arc_agi2_object_bbox_task")
    return value or "arc_agi2_object_bbox_task"


def _test_input_index(value: Any) -> int:
    try:
        return max(0, int(value))
    except Exception:
        return 0


def _candidate_packet_from_solver_candidate(
    *,
    task_id: str,
    test_input_index: int,
    solver_candidate: Mapping[str, Any],
    rank_hint: int,
) -> dict[str, Any]:
    family = _safe_text(solver_candidate.get("family"), "bbox_crop_all_foreground")
    family_rank = OBJECT_BBOX_FAMILY_ORDER_V1.get(family, 99)
    confidence = float(solver_candidate.get("confidence", 1.0) or 1.0)
    output = deepcopy(solver_candidate.get("output"))
    trace = solver_candidate.get("trace") if isinstance(solver_candidate.get("trace"), Mapping) else {}
    metadata = {
        "adapter_name": ADAPTER_NAME_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "task_id": task_id,
        "test_input_index": test_input_index,
        "solver_family": family,
        "solver_family_rank": family_rank,
        "solver_confidence": confidence,
        "solver_rank_hint": rank_hint,
        "synthetic_only": True,
        "source_kind": "object_bbox_solver",
        "trace_labels": ["object_bbox", family, "synthetic_only"],
    }
    metadata.update({k: deepcopy(v) for k, v in trace.items() if k not in {"expected_output", "output", "grid"}})
    return {
        "candidate_id": f"{task_id}:{test_input_index}:{family_rank:02d}:{family}",
        "source_candidate_id": f"{task_id}:{test_input_index}:{family}",
        "source_kind": "object_bbox_solver",
        "synthetic_only": True,
        "grid": output,
        "confidence_label": "confirmed" if confidence >= 1.0 else ("high" if confidence >= 0.75 else "medium"),
        "evidence_labels": SUPPORTED_FAMILY_EVIDENCE_V1.get(family, ["object_bbox", "synthetic_only"]),
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


def _safe_fallback_candidate_packets(
    *,
    task_id: str,
    test_input_index: int,
    test_input: Any,
) -> list[dict[str, Any]]:
    input_grid = _grid_copy(test_input)
    zero_grid = [[0 for _ in row] for row in input_grid] if input_grid else [[0]]
    fallback_a = {
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
    }
    fallback_b = {
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
    }
    return [fallback_a, fallback_b]


def _candidate_packets_for_top2(
    *,
    task_id: str,
    test_input_index: int,
    test_input: Any,
    solver_candidates: Sequence[Mapping[str, Any]],
    fallback_candidate_packets: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    ranked_solver_candidates = sorted(
        [dict(candidate) for candidate in solver_candidates],
        key=lambda candidate: (
            -float(candidate.get("confidence", 0.0) or 0.0),
            OBJECT_BBOX_FAMILY_ORDER_V1.get(_safe_text(candidate.get("family"), ""), 99),
            _safe_text(candidate.get("family"), ""),
            _grid_signature(candidate.get("output")),
        ),
    )
    adapted = [
        _candidate_packet_from_solver_candidate(
            task_id=task_id,
            test_input_index=test_input_index,
            solver_candidate=candidate,
            rank_hint=index + 1,
        )
        for index, candidate in enumerate(ranked_solver_candidates)
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
    candidate_packets = fallback_packets + safe_fallbacks
    return candidate_packets[:2], True


def build_arc_agi2_object_bbox_top2_attempt_packet_v1(
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Any,
    *,
    task_id: Any = "arc_agi2_object_bbox_task",
    test_input_index: Any = 0,
    fallback_candidate_packets: Sequence[Mapping[str, Any]] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    task_id_text = _task_id(task_id)
    test_input_index_int = _test_input_index(test_input_index)
    solver_candidates = solve_object_bbox_task(train_pairs, test_input)
    candidate_packets, used_fallback = _candidate_packets_for_top2(
        task_id=task_id_text,
        test_input_index=test_input_index_int,
        test_input=test_input,
        solver_candidates=solver_candidates,
        fallback_candidate_packets=fallback_candidate_packets,
    )
    packet_metadata = {
        "adapter_name": ADAPTER_NAME_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "task_id": task_id_text,
        "test_input_index": test_input_index_int,
        "solver_candidate_count": len(solver_candidates),
        "used_fallback": used_fallback,
        "synthetic_only": True,
        "trace_labels": ["object_bbox", "top2_attempts", "synthetic_only"],
    }
    if isinstance(metadata, Mapping):
        packet_metadata.update({k: deepcopy(v) for k, v in metadata.items()})
    packet = build_arc_agi2_top2_attempt_packet_v1(
        task_id=task_id_text,
        test_input_index=test_input_index_int,
        candidate_packets=candidate_packets,
        metadata=packet_metadata,
    )
    return packet


def build_arc_agi2_object_bbox_submission_v1(
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
    submission = build_arc_agi2_submission_packet_v1(
        task_entries=task_entries,
        metadata={"adapter_name": ADAPTER_NAME_V1, "synthetic_only": True, **(dict(metadata or {}))},
    )
    return submission


def run_arc_agi2_object_bbox_candidate_mini_suite_v1(
    cases: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    solved_count = 0
    exact_match_count = 0
    fallback_count = 0
    malformed_count = 0
    exactly_two_output_pass = True
    for index, case in enumerate(cases):
        task_id = _safe_text(case.get("task_id"), f"case_{index}")
        packet = build_arc_agi2_object_bbox_top2_attempt_packet_v1(
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
            if int(packet.get("metadata", {}).get("solver_candidate_count", 0) or 0) == 0:
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
    "build_arc_agi2_object_bbox_submission_v1",
    "build_arc_agi2_object_bbox_top2_attempt_packet_v1",
    "run_arc_agi2_object_bbox_candidate_mini_suite_v1",
]
