from __future__ import annotations

import json

from weslr.arc_agi2_resize_tile_candidate_adapter_v1 import (
    build_arc_agi2_resize_tile_submission_v1,
    build_arc_agi2_resize_tile_top2_attempt_packet_v1,
    run_arc_agi2_resize_tile_candidate_mini_suite_v1,
)
from weslr.arc_agi2_submission_contract import (
    build_arc_agi2_submission_packet_v1,
    build_arc_agi2_submission_task_entry_v1,
    validate_arc_agi2_submission_packet_v1,
    validate_arc_agi2_top2_attempt_packet_v1,
)


def _tile_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 2]], "output": [[1, 2, 1, 2]]},
        {"input": [[3, 4]], "output": [[3, 4, 3, 4]]},
    ]
    return {"task_id": "tile_case", "train_pairs": train_pairs, "test_input": [[5, 6]], "expected_output": [[5, 6, 5, 6]]}


def _scale_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 2], [3, 4]], "output": [[1, 1, 2, 2], [1, 1, 2, 2], [3, 3, 4, 4], [3, 3, 4, 4]]},
        {"input": [[5, 6], [7, 8]], "output": [[5, 5, 6, 6], [5, 5, 6, 6], [7, 7, 8, 8], [7, 7, 8, 8]]},
    ]
    return {"task_id": "scale_case", "train_pairs": train_pairs, "test_input": [[9, 1], [2, 3]], "expected_output": [[9, 9, 1, 1], [9, 9, 1, 1], [2, 2, 3, 3], [2, 2, 3, 3]]}


def _border_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 1], [1, 1]], "output": [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]},
        {"input": [[2, 2], [2, 2]], "output": [[0, 0, 0, 0], [0, 2, 2, 0], [0, 2, 2, 0], [0, 0, 0, 0]]},
    ]
    return {"task_id": "border_case", "train_pairs": train_pairs, "test_input": [[3, 3], [3, 3]], "expected_output": [[0, 0, 0, 0], [0, 3, 3, 0], [0, 3, 3, 0], [0, 0, 0, 0]]}


def _fallback_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 2]], "output": [[1, 2, 1]]},
        {"input": [[3, 4]], "output": [[3, 4, 3, 4]]},
    ]
    return {"task_id": "fallback_case", "train_pairs": train_pairs, "test_input": [[5, 6]]}


def test_tile_repeat_becomes_attempt_1() -> None:
    case = _tile_case()
    packet = build_arc_agi2_resize_tile_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["resize_family"] == "tile_repeat"


def test_integer_scale_becomes_attempt_1() -> None:
    case = _scale_case()
    packet = build_arc_agi2_resize_tile_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["resize_family"] == "integer_scale"


def test_border_padding_becomes_attempt_1() -> None:
    case = _border_case()
    packet = build_arc_agi2_resize_tile_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["resize_family"] == "border_padding"


def test_no_candidate_case_falls_back_safely() -> None:
    case = _fallback_case()
    packet = build_arc_agi2_resize_tile_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["metadata"]["used_fallback"] is True
    assert packet["attempts"][0]["metadata"]["source_kind"] == "safe_deterministic_fallback"


def test_exactly_two_attempts_always() -> None:
    for case in (_tile_case(), _scale_case(), _border_case(), _fallback_case()):
        packet = build_arc_agi2_resize_tile_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
        assert len(packet["attempts"]) == 2
        assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True


def test_deterministic_ordering_and_metadata_safe_trace() -> None:
    case = _tile_case()
    first = build_arc_agi2_resize_tile_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    second = build_arc_agi2_resize_tile_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert first == second
    blob = json.dumps({"metadata": first["metadata"], "attempt_metadata": [attempt["metadata"] for attempt in first["attempts"]]}, sort_keys=True).lower()
    assert "expected_output" not in blob
    assert "reference_output" not in blob
    assert "train_pairs" not in blob


def test_submission_contract_compatibility() -> None:
    case = _tile_case()
    packet = build_arc_agi2_resize_tile_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    task_entry = build_arc_agi2_submission_task_entry_v1(task_id=case["task_id"], test_input_packets=[packet])
    submission = build_arc_agi2_submission_packet_v1(task_entries=[task_entry])
    submission_via_helper = build_arc_agi2_resize_tile_submission_v1([packet])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert validate_arc_agi2_submission_packet_v1(submission)["valid"] is True
    assert validate_arc_agi2_submission_packet_v1(submission_via_helper)["valid"] is True


def test_mini_suite_summary() -> None:
    cases = [_tile_case(), _scale_case(), _border_case(), _fallback_case()]
    summary = run_arc_agi2_resize_tile_candidate_mini_suite_v1(cases)
    assert summary["case_count"] == 4
    assert summary["solved_count"] == 3
    assert summary["exact_match_count"] == 3
    assert summary["fallback_count"] == 1
    assert summary["malformed_count"] == 0
    assert summary["exactly_two_output_pass"] is True
