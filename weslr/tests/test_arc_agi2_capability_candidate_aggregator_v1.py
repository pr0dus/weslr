from __future__ import annotations

import json

from weslr.arc_agi2_capability_candidate_aggregator_v1 import (
    build_arc_agi2_capability_candidate_submission_v1,
    build_arc_agi2_capability_candidate_top2_attempt_packet_v1,
    run_arc_agi2_capability_candidate_aggregator_mini_suite_v1,
)
from weslr.arc_agi2_submission_contract import (
    build_arc_agi2_submission_packet_v1,
    build_arc_agi2_submission_task_entry_v1,
    validate_arc_agi2_submission_packet_v1,
    validate_arc_agi2_top2_attempt_packet_v1,
)


def _bbox_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 0, 0], [0, 1, 1], [0, 1, 1]], "output": [[1, 1], [1, 1]]},
        {"input": [[0, 0, 0, 0], [0, 0, 2, 2], [0, 0, 2, 2], [0, 0, 0, 0]], "output": [[2, 2], [2, 2]]},
    ]
    return {"task_id": "bbox_case", "train_pairs": train_pairs, "test_input": [[0, 0, 0], [0, 3, 3], [0, 3, 3]], "expected_output": [[3, 3], [3, 3]]}


def _geometry_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[1, 1, 1], [0, 1, 0], [0, 0, 0]]},
        {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[1, 1, 1], [0, 1, 0], [0, 0, 0]]},
    ]
    return {"task_id": "geometry_case", "train_pairs": train_pairs, "test_input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "expected_output": [[1, 1, 1], [0, 1, 0], [0, 0, 0]]}


def _duplicate_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 4, 4, 0], [0, 4, 4, 0], [0, 0, 0, 0], [0, 0, 0, 0]], "output": [[0, 0, 0, 0], [0, 0, 0, 0], [0, 4, 4, 0], [0, 4, 4, 0]]},
        {"input": [[0, 5, 5, 0], [0, 5, 5, 0], [0, 0, 0, 0], [0, 0, 0, 0]], "output": [[0, 0, 0, 0], [0, 0, 0, 0], [0, 5, 5, 0], [0, 5, 5, 0]]},
    ]
    return {"task_id": "duplicate_case", "train_pairs": train_pairs, "test_input": [[0, 6, 6, 0], [0, 6, 6, 0], [0, 0, 0, 0], [0, 0, 0, 0]], "expected_output": [[0, 0, 0, 0], [0, 0, 0, 0], [0, 6, 6, 0], [0, 6, 6, 0]]}


def _fallback_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 0, 2], [1, 0, 2], [0, 0, 0]], "output": [[0, 1, 2], [0, 1, 2], [0, 0, 0]]},
        {"input": [[2, 0, 3], [2, 0, 3], [0, 0, 0]], "output": [[0, 0, 3], [0, 2, 3], [0, 0, 0]]},
    ]
    return {"task_id": "fallback_case", "train_pairs": train_pairs, "test_input": [[3, 0, 4], [3, 0, 4], [0, 0, 0]]}


def test_object_bbox_wins_for_bbox_crop() -> None:
    case = _bbox_case()
    packet = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["source_family"] == "object_bbox"
    assert len(packet["attempts"]) == 2


def test_shape_geometry_wins_for_rotation() -> None:
    case = _geometry_case()
    packet = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["source_family"] == "shape_geometry"
    assert len(packet["attempts"]) == 2


def test_dedupe_removes_identical_outputs_when_alternative_exists() -> None:
    case = _duplicate_case()
    packet = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["metadata"]["dedupe_count"] > 0
    assert packet["attempts"][0]["grid"] != packet["attempts"][1]["grid"]
    assert any(attempt["metadata"].get("duplicate_family_labels") for attempt in packet["attempts"])


def test_no_candidate_case_falls_back_safely() -> None:
    case = _fallback_case()
    packet = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["metadata"]["used_fallback"] is True
    assert packet["attempts"][0]["metadata"]["source_family"] == "fallback"
    assert packet["attempts"][1]["metadata"]["source_family"] == "fallback"
    assert len(packet["attempts"]) == 2


def test_ranking_is_stable_across_repeated_calls() -> None:
    case = _duplicate_case()
    first = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    second = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert first == second


def test_enabled_family_switch_controls_candidate_sources() -> None:
    bbox_case = _bbox_case()
    geometry_case = _geometry_case()
    object_only = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(bbox_case["train_pairs"], bbox_case["test_input"], task_id=bbox_case["task_id"], enabled_families=["object_bbox", "fallback"])
    geometry_only = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(geometry_case["train_pairs"], geometry_case["test_input"], task_id=geometry_case["task_id"], enabled_families=["shape_geometry", "fallback"])
    assert object_only["attempts"][0]["metadata"]["source_family"] == "object_bbox"
    assert geometry_only["attempts"][0]["metadata"]["source_family"] == "shape_geometry"


def test_trace_is_metadata_only() -> None:
    case = _duplicate_case()
    packet = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"], trace=True)
    blob = json.dumps({"metadata": packet["metadata"], "attempt_metadata": [attempt["metadata"] for attempt in packet["attempts"]]}, sort_keys=True).lower()
    assert "expected_output" not in blob
    assert "reference_output" not in blob
    assert "train_pairs" not in blob
    assert "raw_train" not in blob


def test_submission_contract_compatibility() -> None:
    case = _bbox_case()
    packet = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    task_entry = build_arc_agi2_submission_task_entry_v1(task_id=case["task_id"], test_input_packets=[packet])
    submission = build_arc_agi2_submission_packet_v1(task_entries=[task_entry])
    submission_via_helper = build_arc_agi2_capability_candidate_submission_v1([packet])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert validate_arc_agi2_submission_packet_v1(submission)["valid"] is True
    assert validate_arc_agi2_submission_packet_v1(submission_via_helper)["valid"] is True


def test_mini_suite_summary() -> None:
    cases = [_bbox_case(), _geometry_case(), _duplicate_case(), _fallback_case()]
    summary = run_arc_agi2_capability_candidate_aggregator_mini_suite_v1(cases)
    assert summary["case_count"] == 4
    assert summary["bbox_solved_count"] >= 1
    assert summary["geometry_solved_count"] >= 1
    assert summary["fallback_count"] >= 1
    assert summary["malformed_count"] == 0
    assert summary["exactly_two_output_pass"] is True
