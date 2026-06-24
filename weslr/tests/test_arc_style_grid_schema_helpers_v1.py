from __future__ import annotations

import json
from typing import Any

from weslr.arc_style_grid_schema_helpers import (
    TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
    TOY_TASK_TYPES_V1,
    build_arc_style_grid_candidate_result_v1,
    validate_arc_style_grid_candidate_result_v1,
    build_arc_style_grid_metadata_v1,
    build_arc_style_grid_task_packet_v1,
    build_arc_style_grid_train_pair_v1,
    build_internal_arc_style_grid_toy_tasks_v1,
    summarize_arc_style_grid_task_packet_v1,
    to_arc_style_grid_task_json_safe_v1,
    validate_arc_style_grid_task_packet_v1,
    validate_arc_style_grid_train_pair_v1,
)


def _json_safe(value: Any) -> dict[str, Any]:
    safe = to_arc_style_grid_task_json_safe_v1(value)
    json.dumps(safe, ensure_ascii=False)
    return safe


def test_valid_rectangular_integer_grid_passes() -> None:
    meta = build_arc_style_grid_metadata_v1([[1, 2], [3, 4]])
    assert meta["width"] == 2
    assert meta["height"] == 2
    assert meta["palette_ids"] == [1, 2, 3, 4]
    assert meta["trace"]["rectangular"] is True
    assert meta["invalid_cells"] == []


def test_valid_rectangular_symbolic_grid_passes() -> None:
    meta = build_arc_style_grid_metadata_v1([["a", "b"], ["b", "a"]])
    assert meta["width"] == 2
    assert meta["height"] == 2
    assert meta["palette_ids"] == ["a", "b"]
    assert meta["trace"]["cell_type_names"] == ["short_symbol"]


def test_empty_grid_rejected() -> None:
    packet = build_arc_style_grid_task_packet_v1(
        task_id="empty-grid",
        task_source=TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
        train_pairs=[],
        test_input=[],
    )
    validation = validate_arc_style_grid_task_packet_v1(packet)
    assert validation["valid"] is False
    assert "invalid_test_input" in validation["blocked_reason_labels"]
    assert any(label.endswith("empty_grid") for label in validation["blocked_reason_labels"])


def test_non_rectangular_grid_rejected() -> None:
    meta = build_arc_style_grid_metadata_v1([[1, 2], [3]])
    assert meta["trace"]["rectangular"] is False
    packet = build_arc_style_grid_task_packet_v1(
        task_id="non-rectangular",
        task_source=TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
        train_pairs=[],
        test_input=[[1, 2], [3]],
    )
    validation = validate_arc_style_grid_task_packet_v1(packet)
    assert validation["valid"] is False
    assert any(label.endswith("grid_not_rectangular") for label in validation["blocked_reason_labels"])


def test_mixed_cell_types_rejected() -> None:
    meta = build_arc_style_grid_metadata_v1([[1, "a"], [1, "a"]])
    assert sorted(meta["trace"]["cell_type_names"]) == ["int", "short_symbol"]
    packet = build_arc_style_grid_task_packet_v1(
        task_id="mixed-types",
        task_source=TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
        train_pairs=[],
        test_input=[[1, "a"], [1, "a"]],
    )
    validation = validate_arc_style_grid_task_packet_v1(packet)
    assert validation["valid"] is False
    assert any(label.endswith("mixed_cell_types_rejected") for label in validation["blocked_reason_labels"])


def test_oversized_grid_is_rejected_by_policy() -> None:
    oversized = [[0] * 31 for _ in range(2)]
    packet = build_arc_style_grid_task_packet_v1(
        task_id="oversized",
        task_source=TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
        train_pairs=[],
        test_input=oversized,
    )
    validation = validate_arc_style_grid_task_packet_v1(packet)
    assert validation["valid"] is False
    assert any(label.endswith("grid_oversized") or label.endswith("grid_over_policy_limit") for label in validation["blocked_reason_labels"])


def test_palette_metadata_and_background_inference_are_traced() -> None:
    meta = build_arc_style_grid_metadata_v1([[5, 5], [5, 1]])
    assert meta["has_background"] is True
    assert meta["background_color"] == 5
    assert meta["trace"]["background_inference"]["strategy"] == "most_common_cell"
    assert meta["trace"]["background_inference"]["candidate_background_color"] == 5


def test_train_pair_packet_shape_is_stable() -> None:
    pair = build_arc_style_grid_train_pair_v1("pair-1", [[1, 1], [1, 1]], [[1, 1], [1, 1]], "copy")
    assert pair["pair_id"] == "pair-1"
    assert set(pair.keys()) >= {"pair_id", "input_grid", "output_grid", "notes", "input_grid_metadata", "output_grid_metadata", "validation"}
    assert pair["validation"]["valid"] is True
    assert validate_arc_style_grid_train_pair_v1(pair)["valid"] is True


def test_full_task_packet_is_json_safe() -> None:
    pair = build_arc_style_grid_train_pair_v1("pair-json", [[1, 2], [3, 4]], [[1, 2], [3, 4]], "copy")
    packet = build_arc_style_grid_task_packet_v1(
        task_id="task-json",
        task_source=TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
        train_pairs=[pair],
        test_input=[[5, 6], [7, 8]],
    )
    safe = _json_safe(packet)
    assert safe["task_id"] == "task-json"
    assert json.dumps(safe, ensure_ascii=False)


def test_candidate_result_skeleton_validates() -> None:
    candidate = build_arc_style_grid_candidate_result_v1(
        "candidate-1",
        candidate_type="copy_candidate",
        primitive_sequence=["copy"],
        train_fit_status="unknown",
        partial_fit_metadata={"matches": 0},
        unsupported_assumptions=["none"],
        rejection_reasons=[],
        confidence_metadata={"confidence": "low"},
        calibration_metadata={"calibration": "unset"},
    )
    validation = validate_arc_style_grid_candidate_result_v1(candidate)
    assert set(candidate.keys()) >= {
        "candidate_id",
        "candidate_type",
        "primitive_sequence",
        "train_fit_status",
        "partial_fit_metadata",
        "unsupported_assumptions",
        "rejection_reasons",
        "confidence_metadata",
        "calibration_metadata",
    }
    assert candidate["train_fit_status"] == "unknown"
    assert validation["valid"] is True
    assert json.dumps(candidate, ensure_ascii=False)


def test_all_five_toy_tasks_validate_and_are_internal_synthetic_only() -> None:
    toy_tasks = build_internal_arc_style_grid_toy_tasks_v1()
    assert len(toy_tasks) == 5
    toy_types = sorted(task["trace"]["toy_task_type"] for task in toy_tasks)
    assert toy_types == sorted(TOY_TASK_TYPES_V1)
    for task in toy_tasks:
        validation = validate_arc_style_grid_task_packet_v1(task)
        summary = summarize_arc_style_grid_task_packet_v1(task)
        assert task["task_source"] == TASK_SOURCE_INTERNAL_SYNTHETIC_V1
        assert task["trace"]["internal_synthetic_only"] is True
        assert task["trace"]["toy_task"] is True
        assert validation["valid"] is True
        assert summary["toy_task"] is True
        assert summary["internal_synthetic_only"] is True
        assert json.dumps(_json_safe(task), ensure_ascii=False)
