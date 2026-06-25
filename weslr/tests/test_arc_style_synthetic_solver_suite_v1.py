from __future__ import annotations

import json

from weslr.arc_style_synthetic_solver_suite import (
    FAILURE_CATEGORIES_V1,
    build_arc_style_synthetic_solver_failure_ledger_v1,
    run_arc_style_synthetic_solver_suite_v1,
    summarize_arc_style_synthetic_solver_suite_result_v1,
    to_arc_style_synthetic_solver_suite_json_safe_v1,
    validate_arc_style_synthetic_solver_suite_result_v1,
)
from weslr.arc_agi2_submission_contract import validate_arc_agi2_top2_attempt_packet_v1


def test_solver_suite_runs_and_summary_is_json_safe() -> None:
    result = run_arc_style_synthetic_solver_suite_v1()
    validation = validate_arc_style_synthetic_solver_suite_result_v1(result)
    summary = summarize_arc_style_synthetic_solver_suite_result_v1(result)
    assert validation["valid"] is True
    assert summary["valid"] is True
    assert result["synthetic_internal_result"] is True
    assert result["generated_task_count"] == 36
    assert result["attempted_task_count"] == 36
    assert result["top2_packet_count"] >= 36
    assert result["synthetic_unsupported_count"] < 28
    assert json.dumps(to_arc_style_synthetic_solver_suite_json_safe_v1(result), ensure_ascii=False)


def test_solver_suite_handles_multiple_test_inputs_and_builds_submission_packet() -> None:
    result = run_arc_style_synthetic_solver_suite_v1()
    assert any(len(task_result["packet_results"]) > 1 for task_result in result["task_results"])
    assert result["submission_packet_validation"]["valid"] is True
    assert len(result["task_entries"]) == 36
    assert all(len(entry["test_input_packets"]) == len(task_result["packet_results"]) for entry, task_result in zip(result["task_entries"], result["task_results"]))


def test_solver_suite_records_unsupported_families_honestly() -> None:
    result = run_arc_style_synthetic_solver_suite_v1()
    ledger = result["failure_ledger"]
    category_counts = ledger["category_counts"]
    assert result["synthetic_unsupported_count"] < 28
    assert category_counts.get("unsupported_transformation_family", 0) > 0
    assert category_counts.get("unsupported_transformation_family", 0) < 28
    assert category_counts.get("missing_primitive_executor", 0) < 28
    unsupported_family_ids = [family_id for family_id, summary in result["family_level_summary"].items() if summary["synthetic_unsupported_count"] > 0]
    assert unsupported_family_ids
    assert "reflect_object_horizontal_or_vertical" in unsupported_family_ids
    assert set(FAILURE_CATEGORIES_V1).issuperset(set(ledger["category_counts"].keys()))


def test_solver_suite_deterministic_and_leakage_safe() -> None:
    first = run_arc_style_synthetic_solver_suite_v1()
    second = run_arc_style_synthetic_solver_suite_v1()
    assert summarize_arc_style_synthetic_solver_suite_result_v1(first) == summarize_arc_style_synthetic_solver_suite_result_v1(second)
    assert to_arc_style_synthetic_solver_suite_json_safe_v1(first) == to_arc_style_synthetic_solver_suite_json_safe_v1(second)
    assert first["leakage_flags"]["synthetic_only"] is True
    assert first["leakage_flags"]["kaggle_ready"] is False
    assert first["leakage_flags"]["official_score_claim"] is False
    assert all(value is False for key, value in first["authority_flags"].items())
    assert first["denied_authority"]


def test_top2_validation_works_on_synthetic_suite_packets() -> None:
    result = run_arc_style_synthetic_solver_suite_v1()
    first_packet = result["task_results"][0]["packet_results"][0]["top2_packet"]
    validation = validate_arc_agi2_top2_attempt_packet_v1(first_packet)
    assert validation["valid"] is True
    assert len(first_packet["attempts"]) == 2


def test_failure_ledger_has_family_level_information() -> None:
    result = run_arc_style_synthetic_solver_suite_v1()
    ledger = build_arc_style_synthetic_solver_failure_ledger_v1(result["failure_ledger"]["entries"])
    assert ledger["family_counts"]
    assert ledger["family_category_counts"]
    assert all("family_id" in entry for entry in ledger["entries"])
    assert all(category in FAILURE_CATEGORIES_V1 for category in ledger["category_counts"].keys())
    assert json.dumps(ledger, ensure_ascii=False)
