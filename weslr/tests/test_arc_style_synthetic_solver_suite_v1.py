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
    assert result["synthetic_exact_count"] > 14
    assert result["synthetic_unsupported_count"] < 28
    assert json.dumps(to_arc_style_synthetic_solver_suite_json_safe_v1(result), ensure_ascii=False)


def test_solver_suite_handles_multiple_test_inputs_and_builds_submission_packet() -> None:
    result = run_arc_style_synthetic_solver_suite_v1()
    assert any(len(task_result["packet_results"]) > 1 for task_result in result["task_results"])
    assert result["submission_packet_validation"]["valid"] is True
    assert len(result["task_entries"]) == 36
    assert all(len(entry["test_input_packets"]) == len(task_result["packet_results"]) for entry, task_result in zip(result["task_entries"], result["task_results"]))


def test_solver_suite_records_reflect_as_supported_without_non_reflect_regressions() -> None:
    result = run_arc_style_synthetic_solver_suite_v1()
    ledger = result["failure_ledger"]
    category_counts = ledger["category_counts"]
    assert result["synthetic_exact_count"] == 48
    assert result["synthetic_partial_count"] == 0
    assert result["synthetic_unsupported_count"] == 0
    unsupported_family_ids = [family_id for family_id, summary in result["family_level_summary"].items() if summary["synthetic_unsupported_count"] > 0]
    assert unsupported_family_ids == []
    reflect_summary = result["family_level_summary"]["reflect_object_horizontal_or_vertical"]
    assert reflect_summary["synthetic_exact_count"] == 4
    assert reflect_summary["synthetic_partial_count"] == 0
    assert reflect_summary["synthetic_unsupported_count"] == 0
    assert category_counts.get("unsupported_transformation_family", 0) == 0
    assert category_counts.get("missing_primitive_executor", 0) == 0
    assert result["family_level_summary"]["copy_grid"]["synthetic_exact_count"] == 4
    assert result["family_level_summary"]["copy_grid"]["synthetic_partial_count"] == 0
    assert result["family_level_summary"]["object_count_to_pattern"]["synthetic_exact_count"] == 4
    assert result["family_level_summary"]["object_count_to_pattern"]["synthetic_partial_count"] == 0
    assert result["family_level_summary"]["rotate_object_90"]["synthetic_exact_count"] == 4
    assert result["family_level_summary"]["rotate_object_90"]["synthetic_partial_count"] == 0
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
    assert all("family_id" in entry for entry in ledger["entries"])
    assert all(category in FAILURE_CATEGORIES_V1 for category in ledger["category_counts"].keys())
    if ledger["entries"]:
        assert ledger["family_counts"]
        assert ledger["family_category_counts"]
    else:
        assert ledger["family_counts"] == {}
        assert ledger["family_category_counts"] == {}
    assert json.dumps(ledger, ensure_ascii=False)


def test_copy_grid_variant_2_becomes_exact_without_rotate_family_regression() -> None:
    result = run_arc_style_synthetic_solver_suite_v1()
    copy_task = next(task for task in result["task_results"] if task["task_id"] == "synthetic_copy_grid_variant_2_v1")
    assert [packet["packet_status"] for packet in copy_task["packet_results"]] == ["exact", "exact"]
    assert result["family_level_summary"]["rotate_object_90"]["synthetic_exact_count"] == 4
    assert result["family_level_summary"]["rotate_object_90"]["synthetic_partial_count"] == 0


def test_object_count_to_pattern_variant_2_becomes_exact_without_non_object_count_regressions() -> None:
    result = run_arc_style_synthetic_solver_suite_v1()
    object_count_task = next(task for task in result["task_results"] if task["task_id"] == "synthetic_object_count_to_pattern_variant_2_v1")
    assert [packet["packet_status"] for packet in object_count_task["packet_results"]] == ["exact", "exact"]
    assert result["family_level_summary"]["copy_grid"]["synthetic_exact_count"] == 4
    assert result["family_level_summary"]["rotate_object_90"]["synthetic_exact_count"] == 4
    assert result["family_level_summary"]["reflect_object_horizontal_or_vertical"]["synthetic_exact_count"] == 4
