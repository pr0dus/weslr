"""ARC official-public two-output emitter shape using dummy/no-data packets only."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence

from weslr.arc_agi2_submission_contract import build_arc_agi2_top2_attempt_packet_v1

SCHEMA_VERSION_V1 = "arc_official_public_data_emitter_v1"


def _safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_safe(item) for item in value]
    if isinstance(value, list):
        return [_safe(item) for item in value]
    if isinstance(value, set):
        return [_safe(item) for item in sorted(value, key=repr)]
    return str(value)


def _grid_copy(grid: Sequence[Sequence[Any]]) -> list[list[Any]]:
    return [list(row) for row in grid]


def _invert_binary_grid(grid: Sequence[Sequence[Any]]) -> list[list[Any]]:
    inverted: list[list[Any]] = []
    for row in grid:
        inverted_row: list[Any] = []
        for cell in row:
            if cell == 0:
                inverted_row.append(1)
            elif cell == 1:
                inverted_row.append(0)
            else:
                inverted_row.append(cell)
        inverted.append(inverted_row)
    return inverted


def _validate_grid(grid: Any) -> None:
    if not isinstance(grid, list) or not grid:
        raise ValueError("candidate output must be a non-empty grid")
    width = None
    for row in grid:
        if not isinstance(row, list) or not row:
            raise ValueError("candidate output must be a non-empty rectangular grid")
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise ValueError("candidate output grid must be rectangular")


def infer_dummy_public_rule_v1(*, train_pairs: Sequence[Mapping[str, Any]]) -> str:
    if not isinstance(train_pairs, Sequence) or not train_pairs:
        return "copy_input"
    copy_fit = True
    invert_fit = True
    for pair in train_pairs:
        if not isinstance(pair, Mapping):
            continue
        input_grid = pair.get("input_grid", [])
        output_grid = pair.get("output_grid", [])
        if input_grid != output_grid:
            copy_fit = False
        if _invert_binary_grid(input_grid) != output_grid:
            invert_fit = False
    if copy_fit:
        return "copy_input"
    if invert_fit:
        return "invert_binary"
    return "copy_input"


def build_arc_official_public_candidate_grids_v1(*, solver_visible_packet: Mapping[str, Any]) -> dict[str, Any]:
    train_pairs = solver_visible_packet.get("train_pairs", []) if isinstance(solver_visible_packet.get("train_pairs"), list) else []
    test_inputs = solver_visible_packet.get("test_inputs", []) if isinstance(solver_visible_packet.get("test_inputs"), list) else []
    if not test_inputs:
        raise ValueError("solver-visible packet has no test inputs")
    test_grid = deepcopy(test_inputs[0].get("input_grid", []))
    _validate_grid(test_grid)
    rule = infer_dummy_public_rule_v1(train_pairs=train_pairs)
    predicted_grid = _grid_copy(test_grid) if rule == "copy_input" else _invert_binary_grid(test_grid)
    baseline_grid = _invert_binary_grid(test_grid) if rule == "copy_input" else _grid_copy(test_grid)
    _validate_grid(predicted_grid)
    _validate_grid(baseline_grid)
    return {
        "rule": rule,
        "predicted_grid": predicted_grid,
        "baseline_grid": baseline_grid,
        "candidate_grids": [predicted_grid, baseline_grid],
    }


def emit_arc_official_public_two_output_packet_v1(*, solver_visible_packet: Mapping[str, Any]) -> dict[str, Any]:
    candidate_grids = build_arc_official_public_candidate_grids_v1(solver_visible_packet=solver_visible_packet)
    task_id = str(solver_visible_packet.get("task_id", ""))
    if not task_id:
        raise ValueError("solver-visible packet missing task id")
    candidate_packets = []
    for index, grid in enumerate(candidate_grids["candidate_grids"]):
        _validate_grid(grid)
        candidate_packets.append(
            {
                "candidate_id": f"{task_id}:candidate:{index + 1}",
                "grid": deepcopy(grid),
                "source_candidate_id": f"{task_id}:candidate:{index + 1}",
                "rank": index + 1,
                "confidence_label": "high" if index == 0 else "low",
                "evidence_labels": ["dummy_no_data_inference" if index == 0 else "dummy_baseline"],
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
                    "candidate_role": "solver" if index == 0 else "baseline",
                    "candidate_score": 100 if index == 0 else 0,
                    "dummy_no_data": True,
                    "solver_visible": True,
                },
            }
        )
    packet = build_arc_agi2_top2_attempt_packet_v1(
        task_id=task_id,
        test_input_index=int(solver_visible_packet.get("test_inputs", [{}])[0].get("test_input_index", 0)),
        candidate_packets=candidate_packets,
        metadata={
            "schema_version": SCHEMA_VERSION_V1,
            "dummy_no_data": True,
            "exact_two_output_required": True,
            "source_kind": "dummy_no_data_fixture_v1",
        },
    )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "dummy_no_data": True,
        "rule": candidate_grids["rule"],
        "candidate_grids": candidate_grids["candidate_grids"],
        "top2_packet": packet,
        "attempt_count": len(packet.get("attempts", [])) if isinstance(packet, Mapping) else 0,
    }


__all__ = [
    "SCHEMA_VERSION_V1",
    "build_arc_official_public_candidate_grids_v1",
    "emit_arc_official_public_two_output_packet_v1",
    "infer_dummy_public_rule_v1",
]
