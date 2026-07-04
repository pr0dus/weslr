from __future__ import annotations

import json

from weslr.arc_agi2_count_quantity_candidate_adapter_v1 import (
    build_arc_agi2_count_quantity_submission_v1,
    build_arc_agi2_count_quantity_top2_attempt_packet_v1,
    run_arc_agi2_count_quantity_candidate_mini_suite_v1,
)
from weslr.arc_agi2_submission_contract import (
    build_arc_agi2_submission_packet_v1,
    build_arc_agi2_submission_task_entry_v1,
    validate_arc_agi2_submission_packet_v1,
    validate_arc_agi2_top2_attempt_packet_v1,
)


def _line_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 0], [0, 0, 2], [0, 0, 0]], "output": [[7, 7]]},
        {"input": [[0, 3, 0], [0, 0, 4], [0, 0, 0]], "output": [[7, 7]]},
    ]
    return {"task_id": "count_line_case", "train_pairs": train_pairs, "test_input": [[0, 5, 0], [0, 0, 6], [0, 0, 0]], "expected_output": [[7, 7]]}


def _square_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 0], [0, 0, 2], [0, 0, 0]], "output": [[9, 9], [9, 9]]},
        {"input": [[0, 3, 0], [0, 0, 4], [0, 0, 0]], "output": [[9, 9], [9, 9]]},
    ]
    return {"task_id": "count_square_case", "train_pairs": train_pairs, "test_input": [[0, 5, 0], [0, 0, 6], [0, 0, 0]], "expected_output": [[9, 9], [9, 9]]}


def _largest_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 2, 2]], "output": [[1, 1], [1, 1]]},
        {"input": [[0, 3, 3, 0], [0, 3, 3, 0], [0, 0, 4, 4]], "output": [[3, 3], [3, 3]]},
    ]
    return {"task_id": "count_largest_case", "train_pairs": train_pairs, "test_input": [[0, 5, 5, 0], [0, 5, 5, 0], [0, 0, 6, 6]], "expected_output": [[5, 5], [5, 5]]}


def _fallback_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 0], [0, 0, 2], [0, 0, 0]], "output": [[7, 7]]},
        {"input": [[0, 3, 0], [0, 0, 4], [0, 0, 0]], "output": [[7, 7, 7]]},
    ]
    return {"task_id": "count_fallback_case", "train_pairs": train_pairs, "test_input": [[0, 5, 0], [0, 0, 6], [0, 0, 0]]}


def _duplicate_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 0], [2, 0, 0], [0, 0, 0]], "output": [[8, 8]]},
        {"input": [[0, 3, 0], [4, 0, 0], [0, 0, 0]], "output": [[8, 8]]},
    ]
    return {"task_id": "count_duplicate_case", "train_pairs": train_pairs, "test_input": [[0, 5, 0], [6, 0, 0], [0, 0, 0]], "expected_output": [[8, 8]]}


def test_count_to_line_candidate_becomes_attempt_1() -> None:
    case = _line_case()
    packet = build_arc_agi2_count_quantity_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["count_family"] == "object_count_to_line"


def test_count_to_square_candidate_becomes_attempt_1() -> None:
    case = _square_case()
    packet = build_arc_agi2_count_quantity_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["count_family"] == "object_count_to_square"


def test_select_largest_candidate_becomes_attempt_1() -> None:
    case = _largest_case()
    packet = build_arc_agi2_count_quantity_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["count_family"] == "select_largest_object"


def test_no_candidate_case_falls_back_safely() -> None:
    case = _fallback_case()
    packet = build_arc_agi2_count_quantity_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["metadata"]["used_fallback"] is True
    assert packet["attempts"][0]["metadata"]["source_kind"] == "safe_deterministic_fallback"


def test_exactly_two_attempts_always() -> None:
    for case in (_line_case(), _square_case(), _largest_case(), _fallback_case()):
        packet = build_arc_agi2_count_quantity_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
        assert len(packet["attempts"]) == 2
        assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True


def test_deterministic_ordering_and_metadata_safe_trace() -> None:
    case = _line_case()
    first = build_arc_agi2_count_quantity_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    second = build_arc_agi2_count_quantity_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert first == second
    blob = json.dumps({"metadata": first["metadata"], "attempt_metadata": [attempt["metadata"] for attempt in first["attempts"]]}, sort_keys=True).lower()
    assert "expected_output" not in blob
    assert "reference_output" not in blob
    assert "train_pairs" not in blob


def test_submission_contract_compatibility() -> None:
    case = _line_case()
    packet = build_arc_agi2_count_quantity_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    task_entry = build_arc_agi2_submission_task_entry_v1(task_id=case["task_id"], test_input_packets=[packet])
    submission = build_arc_agi2_submission_packet_v1(task_entries=[task_entry])
    submission_via_helper = build_arc_agi2_count_quantity_submission_v1([packet])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert validate_arc_agi2_submission_packet_v1(submission)["valid"] is True
    assert validate_arc_agi2_submission_packet_v1(submission_via_helper)["valid"] is True


def test_mini_suite_summary() -> None:
    cases = [_line_case(), _square_case(), _largest_case(), _fallback_case()]
    summary = run_arc_agi2_count_quantity_candidate_mini_suite_v1(cases)
    assert summary["case_count"] == 4
    assert summary["solved_count"] >= 3
    assert summary["exact_match_count"] >= 3
    assert summary["fallback_count"] >= 1
    assert summary["malformed_count"] == 0
    assert summary["exactly_two_output_pass"] is True
