from __future__ import annotations

import json

from weslr.arc_agi2_color_role_candidate_adapter_v1 import (
    build_arc_agi2_color_role_submission_v1,
    build_arc_agi2_color_role_top2_attempt_packet_v1,
    run_arc_agi2_color_role_candidate_mini_suite_v1,
)
from weslr.arc_agi2_submission_contract import (
    build_arc_agi2_submission_packet_v1,
    build_arc_agi2_submission_task_entry_v1,
    validate_arc_agi2_submission_packet_v1,
    validate_arc_agi2_top2_attempt_packet_v1,
)


def _color_replacement_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 0], [0, 1, 0], [0, 0, 0]], "output": [[0, 4, 0], [0, 4, 0], [0, 0, 0]]},
        {"input": [[0, 1, 0], [0, 1, 0], [0, 0, 0]], "output": [[0, 4, 0], [0, 4, 0], [0, 0, 0]]},
    ]
    return {"task_id": "color_replacement_case", "train_pairs": train_pairs, "test_input": [[0, 1, 0], [0, 1, 0], [0, 0, 0]], "expected_output": [[0, 4, 0], [0, 4, 0], [0, 0, 0]]}


def _color_swap_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 2], [0, 1, 2], [0, 0, 0]], "output": [[0, 2, 1], [0, 2, 1], [0, 0, 0]]},
        {"input": [[0, 1, 2], [0, 1, 2], [0, 0, 0]], "output": [[0, 2, 1], [0, 2, 1], [0, 0, 0]]},
    ]
    return {"task_id": "color_swap_case", "train_pairs": train_pairs, "test_input": [[0, 1, 2], [0, 1, 2], [0, 0, 0]], "expected_output": [[0, 2, 1], [0, 2, 1], [0, 0, 0]]}


def _inconsistent_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 0], [0, 1, 0]], "output": [[0, 4, 0], [0, 4, 0]]},
        {"input": [[0, 1, 0], [0, 1, 0]], "output": [[0, 5, 0], [0, 5, 0]]},
    ]
    return {"task_id": "inconsistent_case", "train_pairs": train_pairs, "test_input": [[0, 1, 0], [0, 1, 0]]}


def test_color_replacement_becomes_attempt_1() -> None:
    case = _color_replacement_case()
    packet = build_arc_agi2_color_role_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["color_family"] == "object_source_color_recolor"


def test_color_swap_becomes_attempt_1() -> None:
    case = _color_swap_case()
    packet = build_arc_agi2_color_role_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["color_family"] == "color_swap"


def test_no_candidate_case_falls_back_safely() -> None:
    case = _inconsistent_case()
    packet = build_arc_agi2_color_role_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["metadata"]["used_fallback"] is True
    assert packet["attempts"][0]["metadata"]["source_kind"] == "safe_deterministic_fallback"


def test_exactly_two_attempts_always() -> None:
    for case in (_color_replacement_case(), _color_swap_case(), _inconsistent_case()):
        packet = build_arc_agi2_color_role_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
        assert len(packet["attempts"]) == 2
        assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True


def test_deterministic_ordering_and_metadata_safe_trace() -> None:
    case = _color_replacement_case()
    first = build_arc_agi2_color_role_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    second = build_arc_agi2_color_role_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert first == second
    blob = json.dumps({"metadata": first["metadata"], "attempt_metadata": [attempt["metadata"] for attempt in first["attempts"]]}, sort_keys=True).lower()
    assert "expected_output" not in blob
    assert "reference_output" not in blob
    assert "train_pairs" not in blob


def test_submission_contract_compatibility() -> None:
    case = _color_replacement_case()
    packet = build_arc_agi2_color_role_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    task_entry = build_arc_agi2_submission_task_entry_v1(task_id=case["task_id"], test_input_packets=[packet])
    submission = build_arc_agi2_submission_packet_v1(task_entries=[task_entry])
    submission_via_helper = build_arc_agi2_color_role_submission_v1([packet])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert validate_arc_agi2_submission_packet_v1(submission)["valid"] is True
    assert validate_arc_agi2_submission_packet_v1(submission_via_helper)["valid"] is True


def test_mini_suite_summary() -> None:
    cases = [_color_replacement_case(), _color_swap_case(), _inconsistent_case()]
    summary = run_arc_agi2_color_role_candidate_mini_suite_v1(cases)
    assert summary["case_count"] == 3
    assert summary["solved_count"] == 2
    assert summary["exact_match_count"] == 2
    assert summary["fallback_count"] == 1
    assert summary["malformed_count"] == 0
    assert summary["exactly_two_output_pass"] is True
