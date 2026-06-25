from __future__ import annotations

import json
from typing import Any

from weslr.arc_agi2_submission_contract import (
    build_arc_agi2_attempt_v1,
    build_arc_agi2_submission_packet_v1,
    build_arc_agi2_submission_task_entry_v1,
    build_arc_agi2_top2_attempt_packet_v1,
    build_internal_arc_agi2_synthetic_submission_fixtures_v1,
    rank_arc_agi2_candidate_attempts_top2_v1,
    serialize_arc_agi2_submission_json_safe_v1,
    summarize_arc_agi2_submission_packet_v1,
    to_arc_agi2_submission_json_safe_v1,
    validate_arc_agi2_attempt_v1,
    validate_arc_agi2_submission_packet_v1,
    validate_arc_agi2_submission_task_entry_v1,
    validate_arc_agi2_top2_attempt_packet_v1,
)


def _json_safe(value: Any) -> Any:
    safe = to_arc_agi2_submission_json_safe_v1(value)
    json.dumps(safe, ensure_ascii=False)
    return safe


def test_attempt_builder_and_validator_pass() -> None:
    attempt = build_arc_agi2_attempt_v1(
        attempt_id="task-x:0:cand-a:rank1",
        grid=[[1, 1], [1, 1]],
        source_candidate_id="cand-a",
        rank=1,
        confidence_label="high",
        evidence_labels=["copy", "synthetic_fixture"],
        leakage_flags={},
        metadata={"synthetic_only": True},
    )
    validation = validate_arc_agi2_attempt_v1(attempt)
    assert validation["valid"] is True
    assert attempt["rank"] == 1
    assert attempt["leakage_flags"]["uses_test_output"] is False
    assert json.dumps(_json_safe(attempt), ensure_ascii=False)


def test_ranker_is_deterministic_and_uses_local_metadata_only() -> None:
    fixtures = build_internal_arc_agi2_synthetic_submission_fixtures_v1()["internal_candidates"]
    candidates = fixtures["fit_pair"] + [fixtures["invalid_grid_candidate"]]
    first = rank_arc_agi2_candidate_attempts_top2_v1(candidates, task_id="task-rank", test_input_index=0)
    second = rank_arc_agi2_candidate_attempts_top2_v1(candidates, task_id="task-rank", test_input_index=0)
    assert _json_safe(first) == _json_safe(second)
    assert [attempt["rank"] for attempt in first] == [1, 2]
    assert first[0]["source_candidate_id"] == "cand_a"
    assert first[1]["source_candidate_id"] == "cand_b"
    assert all(attempt["metadata"]["synthetic_only"] is True for attempt in first)
    assert all(attempt["leakage_flags"]["uses_test_output"] is False for attempt in first)


def test_top2_packet_validates_and_flags_duplicate_grids() -> None:
    packet = build_internal_arc_agi2_synthetic_submission_fixtures_v1()["duplicate_attempt_grid_valid"]
    validation = validate_arc_agi2_top2_attempt_packet_v1(packet)
    assert validation["valid"] is True
    assert validation["duplicate_attempt_grid"] is True
    assert packet["duplicate_attempt_grid"] is True
    assert len(packet["attempts"]) == 2
    assert packet["attempts"][0]["grid"] == packet["attempts"][1]["grid"]


def test_top2_packet_exact_two_attempts_required() -> None:
    one_attempt = build_internal_arc_agi2_synthetic_submission_fixtures_v1()["invalid_one_attempt_packet"]
    three_attempts = build_internal_arc_agi2_synthetic_submission_fixtures_v1()["invalid_three_attempt_packet"]
    one_validation = validate_arc_agi2_top2_attempt_packet_v1(one_attempt)
    three_validation = validate_arc_agi2_top2_attempt_packet_v1(three_attempts)
    assert one_validation["valid"] is False
    assert three_validation["valid"] is False
    assert "attempt_count_must_be_two" in one_validation["blocked_reason_labels"]
    assert "attempt_count_must_be_two" in three_validation["blocked_reason_labels"]


def test_rank_collision_rejected() -> None:
    packet = build_internal_arc_agi2_synthetic_submission_fixtures_v1()["rank_collision_packet"]
    validation = validate_arc_agi2_top2_attempt_packet_v1(packet)
    assert validation["valid"] is False
    assert any(label == "rank_collision_or_missing_ranks" for label in validation["blocked_reason_labels"])


def test_invalid_grid_rejected() -> None:
    packet = build_internal_arc_agi2_synthetic_submission_fixtures_v1()["invalid_grid_packet"]
    validation = validate_arc_agi2_top2_attempt_packet_v1(packet)
    assert validation["valid"] is False
    assert any(label == "invalid_grid" for label in validation["blocked_reason_labels"])


def test_invalid_top2_attempt_grid_rejected() -> None:
    valid_attempt = build_arc_agi2_attempt_v1(
        attempt_id="task-x:0:cand-a:rank1",
        grid=[[1, 1], [1, 1]],
        source_candidate_id="cand-a",
        rank=1,
        confidence_label="high",
        evidence_labels=["copy"],
        leakage_flags={},
        metadata={"synthetic_only": True},
    )
    invalid_attempt = build_arc_agi2_attempt_v1(
        attempt_id="task-x:0:cand-b:rank2",
        grid=[[10]],
        source_candidate_id="cand-b",
        rank=2,
        confidence_label="low",
        evidence_labels=["copy"],
        leakage_flags={},
        metadata={"synthetic_only": True},
    )
    packet = {
        "task_id": "task-x",
        "test_input_index": 0,
        "attempts": [valid_attempt, invalid_attempt],
        "duplicate_attempt_grid": False,
        "leakage_flags": {"uses_test_output": False, "uses_solution_file": False, "uses_answer_key": False, "uses_hidden_private_data": False, "uses_task_id_shortcut": False, "uses_notes_shortcut": False, "lookup_table_detected": False},
        "metadata": {"synthetic_only": True},
    }
    validation = validate_arc_agi2_top2_attempt_packet_v1(packet)
    assert validation["valid"] is False
    assert any(label == "invalid_grid" for label in validation["blocked_reason_labels"])


def test_leakage_flag_true_rejected() -> None:
    packet = build_internal_arc_agi2_synthetic_submission_fixtures_v1()["leakage_flag_true_packet"]
    validation = validate_arc_agi2_top2_attempt_packet_v1(packet)
    assert validation["valid"] is False
    assert any("uses_test_output" in label for label in validation["blocked_reason_labels"])


def test_multiple_test_inputs_supported_by_task_entry() -> None:
    fixtures = build_internal_arc_agi2_synthetic_submission_fixtures_v1()["single_task_two_test_inputs_valid"]
    entry = fixtures["task_entry"]
    validation = validate_arc_agi2_submission_task_entry_v1(entry)
    assert validation["valid"] is True
    assert len(entry["test_input_packets"]) == 2
    assert [packet["test_input_index"] for packet in entry["test_input_packets"]] == [0, 1]


def test_submission_packet_sorts_deterministically_and_is_json_safe() -> None:
    fixtures = build_internal_arc_agi2_synthetic_submission_fixtures_v1()["deterministic_sorting"]
    packet = fixtures["sorted_submission_packet"]
    validation = validate_arc_agi2_submission_packet_v1(packet)
    summary = summarize_arc_agi2_submission_packet_v1(packet)
    assert validation["valid"] is True
    assert [entry["task_id"] for entry in packet["task_entries"]] == ["task_a", "task_z"]
    assert packet["task_entries"][0]["test_input_packets"][0]["test_input_index"] == 0
    assert summary["task_count"] == 2
    assert summary["synthetic_only"] is True
    assert summary["kaggle_ready"] is False
    assert json.dumps(_json_safe(packet), ensure_ascii=False)


def test_submission_packet_metadata_claims_are_safely_false_or_deferred() -> None:
    packet = build_internal_arc_agi2_synthetic_submission_fixtures_v1()["single_task_single_test_input_valid"]["submission_packet"]
    validation = validate_arc_agi2_submission_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["contract_name"] == "arc_agi2_submission_contract_v1"
    assert packet["contract_version"] == "v1"
    assert packet["synthetic_only"] is True
    assert packet["kaggle_ready"] is False
    assert packet["requires_official_sample_submission_validation"] is True
    assert "kaggle_ready_claim" in packet["denied_authority"]
    assert json.dumps(serialize_arc_agi2_submission_json_safe_v1(packet), ensure_ascii=False)


def test_module_fixtures_cover_positive_and_negative_cases() -> None:
    fixtures = build_internal_arc_agi2_synthetic_submission_fixtures_v1()
    assert "single_task_single_test_input_valid" in fixtures
    assert "single_task_two_test_inputs_valid" in fixtures
    assert "duplicate_attempt_grid_valid" in fixtures
    assert "invalid_one_attempt_packet" in fixtures
    assert "invalid_three_attempt_packet" in fixtures
    assert "rank_collision_packet" in fixtures
    assert "invalid_grid_packet" in fixtures
    assert "leakage_flag_true_packet" in fixtures
    assert "deterministic_sorting" in fixtures
    assert "json_safe_serialization" in fixtures
    assert validate_arc_agi2_top2_attempt_packet_v1(fixtures["single_task_single_test_input_valid"]["top2_packet"])["valid"] is True
    assert validate_arc_agi2_submission_task_entry_v1(fixtures["single_task_two_test_inputs_valid"]["task_entry"])["valid"] is True
    assert validate_arc_agi2_submission_packet_v1(fixtures["single_task_single_test_input_valid"]["submission_packet"])["valid"] is True
