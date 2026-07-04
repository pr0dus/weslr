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


def _color_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 0], [0, 1, 0], [0, 0, 0]], "output": [[0, 4, 0], [0, 4, 0], [0, 0, 0]]},
        {"input": [[0, 1, 0], [0, 1, 0], [0, 0, 0]], "output": [[0, 4, 0], [0, 4, 0], [0, 0, 0]]},
    ]
    return {"task_id": "color_case", "train_pairs": train_pairs, "test_input": [[0, 1, 0], [0, 1, 0], [0, 0, 0]], "expected_output": [[0, 4, 0], [0, 4, 0], [0, 0, 0]]}


def _resize_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[1, 2]], "output": [[1, 2, 1, 2]]},
        {"input": [[3, 4]], "output": [[3, 4, 3, 4]]},
    ]
    return {"task_id": "resize_case", "train_pairs": train_pairs, "test_input": [[5, 6]], "expected_output": [[5, 6, 5, 6]]}


def _count_line_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 0], [0, 0, 2], [0, 0, 0]], "output": [[7, 7]]},
        {"input": [[0, 3, 0], [0, 0, 4], [0, 0, 0]], "output": [[7, 7]]},
    ]
    return {"task_id": "count_line_case", "train_pairs": train_pairs, "test_input": [[0, 5, 0], [0, 0, 6], [0, 0, 0]], "expected_output": [[7, 7]]}


def _count_square_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 0], [0, 0, 2], [0, 0, 0]], "output": [[9, 9], [9, 9]]},
        {"input": [[0, 3, 0], [0, 0, 4], [0, 0, 0]], "output": [[9, 9], [9, 9]]},
    ]
    return {"task_id": "count_square_case", "train_pairs": train_pairs, "test_input": [[0, 5, 0], [0, 0, 6], [0, 0, 0]], "expected_output": [[9, 9], [9, 9]]}


def _count_duplicate_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 0], [2, 0, 0], [0, 0, 0]], "output": [[8, 8]]},
        {"input": [[0, 3, 0], [4, 0, 0], [0, 0, 0]], "output": [[8, 8]]},
    ]
    return {"task_id": "count_duplicate_case", "train_pairs": train_pairs, "test_input": [[0, 5, 0], [6, 0, 0], [0, 0, 0]], "expected_output": [[8, 8]]}


def _count_only_case() -> dict[str, object]:
    train_pairs = [
        {"input": [[0, 1, 0], [0, 0, 2], [0, 0, 0]], "output": [[5, 5], [5, 5]]},
        {"input": [[0, 3, 0], [0, 0, 4], [0, 0, 0]], "output": [[5, 5], [5, 5]]},
    ]
    return {"task_id": "count_only_case", "train_pairs": train_pairs, "test_input": [[0, 7, 0], [0, 0, 8], [0, 0, 0]], "expected_output": [[5, 5], [5, 5]]}


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


def test_color_role_participates_and_wins() -> None:
    case = _color_case()
    packet = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["source_family"] == "color_role"
    assert len(packet["attempts"]) == 2


def test_resize_tile_participates_and_wins() -> None:
    case = _resize_case()
    packet = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["source_family"] == "resize_tile"
    assert len(packet["attempts"]) == 2


def test_count_quantity_participates_and_wins() -> None:
    case = _count_only_case()
    packet = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["grid"] == case["expected_output"]
    assert packet["attempts"][0]["metadata"]["source_family"] == "count_quantity"


def test_count_quantity_duplicate_outputs_dedupe_correctly() -> None:
    case = _count_duplicate_case()
    packet = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["metadata"]["dedupe_count"] > 0
    assert packet["attempts"][0]["metadata"]["source_family"] == "count_quantity"
    assert packet["attempts"][0]["metadata"].get("duplicate_family_labels")


def test_count_quantity_duplicate_outputs_can_be_disabled() -> None:
    case = _count_only_case()
    packet = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"], enabled_families=["object_bbox", "shape_geometry", "color_role", "resize_tile", "fallback"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["attempts"][0]["metadata"]["source_family"] == "fallback"


def test_color_role_duplicate_outputs_dedupe_correctly() -> None:
    case = _color_case()
    packet = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"], enabled_families=["color_role", "fallback"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["metadata"]["dedupe_count"] > 0
    assert packet["attempts"][0]["metadata"]["source_family"] == "color_role"
    assert packet["attempts"][1]["metadata"]["source_family"] == "fallback"
    assert packet["attempts"][0]["metadata"].get("duplicate_family_labels")


def test_no_candidate_case_falls_back_safely() -> None:
    case = _fallback_case()
    packet = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert validate_arc_agi2_top2_attempt_packet_v1(packet)["valid"] is True
    assert packet["metadata"]["used_fallback"] is True
    assert packet["attempts"][0]["metadata"]["source_family"] == "fallback"
    assert packet["attempts"][1]["metadata"]["source_family"] == "fallback"
    assert len(packet["attempts"]) == 2


def test_ranking_is_stable_across_repeated_calls() -> None:
    case = _count_only_case()
    first = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    second = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(case["train_pairs"], case["test_input"], task_id=case["task_id"])
    assert first == second


def test_enabled_family_switch_controls_candidate_sources() -> None:
    color_case = _color_case()
    resize_case = _resize_case()
    count_case = _count_only_case()
    object_only = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(_bbox_case()["train_pairs"], _bbox_case()["test_input"], task_id="bbox_case", enabled_families=["object_bbox", "fallback"])
    color_disabled = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(color_case["train_pairs"], color_case["test_input"], task_id=color_case["task_id"], enabled_families=["object_bbox", "shape_geometry", "resize_tile", "count_quantity", "fallback"])
    resize_enabled = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(resize_case["train_pairs"], resize_case["test_input"], task_id=resize_case["task_id"], enabled_families=["resize_tile", "fallback"])
    count_disabled = build_arc_agi2_capability_candidate_top2_attempt_packet_v1(count_case["train_pairs"], count_case["test_input"], task_id=count_case["task_id"], enabled_families=["object_bbox", "shape_geometry", "color_role", "resize_tile", "fallback"])
    assert object_only["attempts"][0]["metadata"]["source_family"] == "object_bbox"
    assert color_disabled["attempts"][0]["metadata"]["source_family"] == "fallback"
    assert resize_enabled["attempts"][0]["metadata"]["source_family"] == "resize_tile"
    assert count_disabled["attempts"][0]["metadata"]["source_family"] == "fallback"


def test_trace_is_metadata_only() -> None:
    case = _count_only_case()
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
    cases = [_bbox_case(), _geometry_case(), _color_case(), _resize_case(), _count_only_case(), _count_duplicate_case(), _fallback_case()]
    summary = run_arc_agi2_capability_candidate_aggregator_mini_suite_v1(cases)
    assert summary["case_count"] == 7
    assert summary["bbox_solved_count"] >= 1
    assert summary["geometry_solved_count"] >= 1
    assert summary["color_role_solved_count"] >= 1
    assert summary["resize_tile_solved_count"] >= 1
    assert summary["count_quantity_solved_count"] >= 2
    assert summary["fallback_count"] >= 1
    assert summary["malformed_count"] == 0
    assert summary["exactly_two_output_pass"] is True
