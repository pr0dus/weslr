from __future__ import annotations

import json

from weslr.arc_agi2_object_bbox_candidate_adapter_v1 import (
    build_arc_agi2_object_bbox_submission_v1,
    build_arc_agi2_object_bbox_top2_attempt_packet_v1,
    run_arc_agi2_object_bbox_candidate_mini_suite_v1,
)
from weslr.arc_agi2_submission_contract import (
    build_arc_agi2_submission_packet_v1,
    build_arc_agi2_submission_task_entry_v1,
    validate_arc_agi2_submission_packet_v1,
    validate_arc_agi2_top2_attempt_packet_v1,
)


def _crop_all_foreground_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 0, 0], [0, 1, 1], [0, 1, 1]], "output": [[1, 1], [1, 1]]},
        {"input": [[0, 0, 0, 0], [0, 0, 2, 2], [0, 0, 2, 2], [0, 0, 0, 0]], "output": [[2, 2], [2, 2]]},
    ]
    return {"task_id": "crop_all_foreground_case", "train_pairs": train_pairs, "test_input": [[0, 0, 0], [0, 3, 3], [0, 3, 3]], "expected_output": [[3, 3], [3, 3]]}


def _crop_largest_object_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 0, 0, 0, 0], [0, 4, 4, 4, 0], [0, 4, 4, 4, 0], [0, 0, 0, 7, 7], [0, 0, 0, 7, 7]], "output": [[4, 4, 4], [4, 4, 4]]},
        {"input": [[0, 0, 0, 0, 0], [0, 8, 8, 8, 0], [0, 8, 8, 8, 0], [0, 0, 0, 9, 9], [0, 0, 0, 9, 9]], "output": [[8, 8, 8], [8, 8, 8]]},
    ]
    return {"task_id": "crop_largest_object_case", "train_pairs": train_pairs, "test_input": [[0, 0, 0, 0, 0], [0, 6, 6, 6, 0], [0, 6, 6, 6, 0], [0, 0, 0, 5, 5], [0, 0, 0, 5, 5]], "expected_output": [[6, 6, 6], [6, 6, 6]]}


def _selected_color_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 0, 0, 0, 0], [0, 1, 1, 1, 0], [0, 1, 1, 1, 0], [0, 0, 0, 7, 7], [0, 0, 0, 7, 7]], "output": [[7, 7], [7, 7]]},
        {"input": [[0, 0, 0, 0, 0], [0, 2, 2, 2, 0], [0, 2, 2, 2, 0], [0, 0, 0, 7, 7], [0, 0, 0, 7, 7]], "output": [[7, 7], [7, 7]]},
    ]
    return {"task_id": "selected_color_case", "train_pairs": train_pairs, "test_input": [[0, 0, 0, 0, 0], [0, 3, 3, 3, 0], [0, 3, 3, 3, 0], [0, 0, 0, 7, 7], [0, 0, 0, 7, 7]], "expected_output": [[7, 7], [7, 7]]}


def _translation_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 0, 0, 0], [0, 9, 9, 0], [0, 9, 9, 0], [0, 0, 0, 0]], "output": [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 9, 9], [0, 0, 9, 9]]},
        {"input": [[0, 0, 0, 0], [0, 5, 5, 0], [0, 5, 5, 0], [0, 0, 0, 0]], "output": [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 5, 5], [0, 0, 5, 5]]},
    ]
    return {"task_id": "translation_case", "train_pairs": train_pairs, "test_input": [[0, 0, 0, 0], [0, 6, 6, 0], [0, 6, 6, 0], [0, 0, 0, 0]], "expected_output": [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 6, 6], [0, 0, 6, 6]]}


def _inconsistent_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 0, 0], [0, 1, 1], [0, 1, 1]], "output": [[1, 1], [1, 1]]},
        {"input": [[0, 0, 0, 0], [0, 2, 2, 0], [0, 2, 2, 0], [0, 0, 0, 0]], "output": [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 2, 2], [0, 0, 2, 2]]},
    ]
    return {"task_id": "inconsistent_case", "train_pairs": train_pairs, "test_input": [[0, 0, 0], [0, 5, 5], [0, 5, 5]]}


def test_crop_all_foreground_becomes_attempt_1() -> None:
    case = _crop_all_foreground_case()
    packet = build_arc_agi2_object_bbox_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["solver_family"] == "bbox_crop_all_foreground"


def test_crop_largest_object_becomes_attempt_1() -> None:
    case = _crop_largest_object_case()
    packet = build_arc_agi2_object_bbox_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["solver_family"] == "bbox_crop_largest_object"


def test_selected_color_crop_becomes_attempt_1() -> None:
    case = _selected_color_case()
    packet = build_arc_agi2_object_bbox_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["solver_family"] == "bbox_crop_selected_color_object"


def test_translate_object_becomes_attempt_1() -> None:
    case = _translation_case()
    packet = build_arc_agi2_object_bbox_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["solver_family"] == "translation_single_object"


def test_inconsistent_train_examples_fall_back_safely() -> None:
    case = _inconsistent_case()
    packet = build_arc_agi2_object_bbox_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["metadata"]["used_fallback"] is True
    assert packet["attempts"][0]["metadata"]["source_kind"] == "safe_deterministic_fallback"
    assert len(packet["attempts"]) == 2


def test_exactly_two_attempts_are_always_emitted() -> None:
    for case in (_crop_all_foreground_case(), _crop_largest_object_case(), _selected_color_case(), _translation_case(), _inconsistent_case()):
        packet = build_arc_agi2_object_bbox_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
        assert len(packet["attempts"]) == 2
        assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True


def test_candidate_format_matches_existing_submission_contract() -> None:
    case = _crop_all_foreground_case()
    packet = build_arc_agi2_object_bbox_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    task_entry = build_arc_agi2_submission_task_entry_v1(task_id=case["task_id"], test_input_packets=[packet])
    submission = build_arc_agi2_submission_packet_v1(task_entries=[task_entry])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert validate_arc_agi2_submission_packet_v1(submission)["valid"] is True


def test_no_expected_outputs_appear_in_trace_metadata() -> None:
    case = _translation_case()
    packet = build_arc_agi2_object_bbox_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    blob = json.dumps({"packet_metadata": packet["metadata"], "attempt_metadata": [attempt["metadata"] for attempt in packet["attempts"]]}, sort_keys=True).lower()
    assert "expected_output" not in blob
    assert "reference_output" not in blob


def test_deterministic_ordering_across_repeated_runs() -> None:
    case = _selected_color_case()
    first = build_arc_agi2_object_bbox_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    second = build_arc_agi2_object_bbox_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert first == second


def test_mini_run_summary_reports_expected_counts() -> None:
    cases = [
        _crop_all_foreground_case(),
        _crop_largest_object_case(),
        _selected_color_case(),
        _translation_case(),
        _inconsistent_case(),
    ]
    summary = run_arc_agi2_object_bbox_candidate_mini_suite_v1(cases)
    assert summary["case_count"] == 5
    assert summary["solved_count"] == 4
    assert summary["exact_match_count"] == 4
    assert summary["fallback_count"] == 1
    assert summary["malformed_count"] == 0
    assert summary["exactly_two_output_pass"] is True
