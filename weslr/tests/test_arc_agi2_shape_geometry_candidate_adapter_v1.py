from __future__ import annotations

import json

from weslr.arc_agi2_shape_geometry_candidate_adapter_v1 import (
    build_arc_agi2_shape_geometry_submission_v1,
    build_arc_agi2_shape_geometry_top2_attempt_packet_v1,
    run_arc_agi2_shape_geometry_candidate_mini_suite_v1,
)
from weslr.arc_agi2_submission_contract import (
    build_arc_agi2_submission_packet_v1,
    build_arc_agi2_submission_task_entry_v1,
    validate_arc_agi2_submission_packet_v1,
    validate_arc_agi2_top2_attempt_packet_v1,
)


def _rotate_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[1, 1, 1], [0, 1, 0], [0, 0, 0]]},
        {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[1, 1, 1], [0, 1, 0], [0, 0, 0]]},
    ]
    return {"task_id": "rotate_case", "train_pairs": train_pairs, "test_input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "expected_output": [[1, 1, 1], [0, 1, 0], [0, 0, 0]]}


def _reflect_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[0, 1, 0], [1, 1, 0], [0, 1, 0]]},
        {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[0, 1, 0], [1, 1, 0], [0, 1, 0]]},
    ]
    return {"task_id": "reflect_case", "train_pairs": train_pairs, "test_input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "expected_output": [[0, 1, 0], [1, 1, 0], [0, 1, 0]]}


def _translation_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 0, 0, 0], [1, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]], "output": [[0, 0, 0, 0], [0, 1, 0, 0], [0, 1, 1, 0], [0, 1, 0, 0]]},
        {"input": [[1, 0, 0, 0], [1, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]], "output": [[0, 0, 0, 0], [0, 1, 0, 0], [0, 1, 1, 0], [0, 1, 0, 0]]},
    ]
    return {"task_id": "translation_case", "train_pairs": train_pairs, "test_input": [[1, 0, 0, 0], [1, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]], "expected_output": [[0, 0, 0, 0], [0, 1, 0, 0], [0, 1, 1, 0], [0, 1, 0, 0]]}


def _inconsistent_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[1, 1, 1], [0, 1, 0], [0, 0, 0]]},
        {"input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]], "output": [[0, 0, 1], [0, 1, 1], [1, 0, 0]]},
    ]
    return {"task_id": "inconsistent_case", "train_pairs": train_pairs, "test_input": [[1, 0, 0], [1, 1, 0], [1, 0, 0]]}


def test_rotation_candidate_becomes_attempt_1() -> None:
    case = _rotate_case()
    packet = build_arc_agi2_shape_geometry_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["shape_family"] == "rotate_90_single_object"


def test_reflection_candidate_becomes_attempt_1() -> None:
    case = _reflect_case()
    packet = build_arc_agi2_shape_geometry_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["shape_family"] == "reflect_vertical_single_object"


def test_no_candidate_case_falls_back_safely() -> None:
    case = _inconsistent_case()
    packet = build_arc_agi2_shape_geometry_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["metadata"]["used_fallback"] is True
    assert packet["attempts"][0]["metadata"]["source_kind"] == "safe_deterministic_fallback"


def test_exactly_two_attempts_always() -> None:
    for case in (_rotate_case(), _reflect_case(), _translation_case(), _inconsistent_case()):
        packet = build_arc_agi2_shape_geometry_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
        assert len(packet["attempts"]) == 2
        assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True


def test_deterministic_ordering_and_metadata_safe_trace() -> None:
    case = _translation_case()
    first = build_arc_agi2_shape_geometry_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    second = build_arc_agi2_shape_geometry_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert first == second
    blob = json.dumps({"metadata": first["metadata"], "attempt_metadata": [attempt["metadata"] for attempt in first["attempts"]]}, sort_keys=True).lower()
    assert "expected_output" not in blob
    assert "reference_output" not in blob


def test_candidate_format_matches_existing_submission_contract() -> None:
    case = _rotate_case()
    packet = build_arc_agi2_shape_geometry_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    task_entry = build_arc_agi2_submission_task_entry_v1(task_id=case["task_id"], test_input_packets=[packet])
    submission = build_arc_agi2_submission_packet_v1(task_entries=[task_entry])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert validate_arc_agi2_submission_packet_v1(submission)["valid"] is True


def test_mini_suite_summary() -> None:
    cases = [_rotate_case(), _reflect_case(), _translation_case(), _inconsistent_case()]
    summary = run_arc_agi2_shape_geometry_candidate_mini_suite_v1(cases)
    assert summary["case_count"] == 4
    assert summary["solved_count"] == 3
    assert summary["exact_match_count"] == 3
    assert summary["fallback_count"] == 1
    assert summary["malformed_count"] == 0
    assert summary["exactly_two_output_pass"] is True
