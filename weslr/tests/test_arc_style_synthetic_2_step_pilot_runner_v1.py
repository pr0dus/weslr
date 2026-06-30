from __future__ import annotations

import ast
import inspect
import json
from typing import Any

from weslr.arc_style_synthetic_2_step_pilot_runner import (
    EXPANDED_PILOT_TASK_COUNT_V1,
    FAILURE_TAXONOMY_V1,
    MODE_ORDER_V1,
    PILOT_TASK_COUNT_V1,
    RUNNER_ID_V1,
    build_arc_style_synthetic_2_step_80_pilot_plan_v1,
    build_arc_style_synthetic_2_step_pilot_plan_v1,
    run_arc_style_synthetic_2_step_40_pilot_diagnostic_v1,
    run_arc_style_synthetic_2_step_80_pilot_diagnostic_v1,
    summarize_arc_style_synthetic_2_step_40_pilot_diagnostic_v1,
    to_arc_style_synthetic_2_step_pilot_json_safe_v1,
)
from weslr.arc_style_synthetic_diagnostic_runner import run_arc_style_synthetic_120_diagnostic_runner_v1

FORBIDDEN_IMPORT_FRAGMENTS = (
    "provider",
    "payment",
    "chat_responder",
    "respond_chat",
    "openai",
    "anthropic",
    "google",
    "ollama",
    "requests",
    "pathlib",
    "subprocess",
)


def _json_safe(value: Any) -> Any:
    safe = to_arc_style_synthetic_2_step_pilot_json_safe_v1(value)
    json.dumps(safe, ensure_ascii=False)
    return safe


def test_2_step_pilot_plan_builds_all_40_tasks_across_4_modes() -> None:
    plan = build_arc_style_synthetic_2_step_pilot_plan_v1()
    assert plan["runner_id"] == RUNNER_ID_V1
    assert len(plan["task_specs"]) == PILOT_TASK_COUNT_V1
    assert len(plan["entries"]) == PILOT_TASK_COUNT_V1 * 4
    buckets = [item["difficulty_bucket"] for item in plan["task_specs"]]
    assert buckets.count("easy") == 20
    assert buckets.count("medium") == 10
    assert buckets.count("stress") == 10
    assert plan["modes"] == list(MODE_ORDER_V1)


def test_2_step_pilot_runner_is_deterministic_and_json_safe() -> None:
    first = run_arc_style_synthetic_2_step_40_pilot_diagnostic_v1()
    second = run_arc_style_synthetic_2_step_40_pilot_diagnostic_v1()
    assert summarize_arc_style_synthetic_2_step_40_pilot_diagnostic_v1(first) == summarize_arc_style_synthetic_2_step_40_pilot_diagnostic_v1(second)
    assert _json_safe(first) == _json_safe(second)
    assert json.dumps(first, ensure_ascii=False)


def test_2_step_pilot_runner_exposes_inventory_modes_and_taxonomy() -> None:
    result = run_arc_style_synthetic_2_step_40_pilot_diagnostic_v1()
    summary = summarize_arc_style_synthetic_2_step_40_pilot_diagnostic_v1(result)
    assert result["pilot_task_count"] == PILOT_TASK_COUNT_V1
    assert result["difficulty_split"] == {"easy": 20, "medium": 10, "stress": 10}
    assert result["attribution_modes"] == list(MODE_ORDER_V1)
    assert result["failure_taxonomy"] == list(FAILURE_TAXONOMY_V1)
    assert len(result["task_inventory"]) == PILOT_TASK_COUNT_V1
    assert len(result["pair_level_breakdown"]) == PILOT_TASK_COUNT_V1
    assert set(result["bucket_level_breakdown"].keys()) == {"easy", "medium", "stress"}
    assert set(result["failure_taxonomy_breakdown"].keys()) == set(FAILURE_TAXONOMY_V1)
    pilot_total = sum(result["pilot_result"][key] for key in ("exact", "partial", "unsupported", "failed"))
    assert pilot_total == PILOT_TASK_COUNT_V1
    assert summary["pair_count"] == PILOT_TASK_COUNT_V1
    assert summary["attribution_modes"] == list(MODE_ORDER_V1)
    assert result["pilot_result"] == {"exact": 39, "partial": 1, "unsupported": 0, "failed": 0}
    assert result["represented_sequence_rows"] == 40
    assert result["step1_plausible_rows"] >= 33
    assert result["step2_plausible_rows"] >= 37
    assert result["mode_results"]["full_metadata"]["represented_sequence_rows"] == 40
    assert result["mode_results"]["toy_task_type_preserved_guardrail"]["represented_sequence_rows"] == 40
    assert result["mode_results"]["full_metadata"]["exact"] == 39
    assert result["mode_results"]["toy_task_type_preserved_guardrail"]["exact"] == 39
    assert result["mode_results"]["fully_stripped_lower_bound"]["represented_sequence_rows"] == 0
    assert result["no_score_claim"] is True
    assert result["official_score_claim"] is False
    assert result["trace_flags"]["uses_test_output"] is False
    assert result["trace_flags"]["uses_task_id_for_candidate_selection"] is False
    assert result["trace_flags"]["uses_notes_for_candidate_selection"] is False
    assert result["trace_flags"]["lookup_table_detected"] is False


def test_2_step_pilot_rows_have_required_fields_and_clean_leakage_posture() -> None:
    result = run_arc_style_synthetic_2_step_40_pilot_diagnostic_v1()
    rows = result["evaluations"]
    assert len(rows) == PILOT_TASK_COUNT_V1
    required_fields = {
        "diagnostic_mode",
        "task_id",
        "source_task_id",
        "composition_pair",
        "difficulty_bucket",
        "test_input_index",
        "selected_candidate_id",
        "selected_primitive_sequence",
        "train_fit_status",
        "packet_status",
        "non_exact_reason",
        "composition_failure_category",
        "expected_exact_match",
        "represented_sequence",
        "step1_plausible",
        "step2_plausible",
        "step_1_exports",
        "step_2_imports",
        "carried_parameters",
        "dropped_parameters",
        "parameter_origin_by_key",
        "carryover_success",
        "sequence_visibility_reason",
        "pair_evaluations",
        "leakage_flags",
    }
    for row in rows:
        assert required_fields.issubset(row.keys())
        assert row["diagnostic_mode"] == "toy_task_type_preserved_guardrail"
        assert row["difficulty_bucket"] in {"easy", "medium", "stress"}
        assert row["packet_status"] in {"exact", "partial", "unsupported", "failed"}
        assert row["leakage_flags"]["synthetic_only"] is True
        assert row["leakage_flags"]["uses_public_arc_data"] is False
        assert row["leakage_flags"]["uses_kaggle_data"] is False
        assert row["leakage_flags"]["uses_answer_key"] is False
        assert row["leakage_flags"]["uses_test_output_for_candidate_generation"] is False


def test_repaired_2_step_runner_leaves_only_one_residual_partial() -> None:
    result = run_arc_style_synthetic_2_step_40_pilot_diagnostic_v1()
    residual_rows = [row for row in result["evaluations"] if row["packet_status"] != "exact"]
    assert [row["source_task_id"] for row in residual_rows] == ["pilot_2_step_stress_08_fill_then_count_v1"]
    assert residual_rows[0]["composition_failure_category"] == "right_primitives_wrong_order"


def test_80_task_expansion_preserves_original_40_and_tracks_residuals() -> None:
    plan = build_arc_style_synthetic_2_step_80_pilot_plan_v1()
    assert plan["pilot_task_count"] == EXPANDED_PILOT_TASK_COUNT_V1
    assert len(plan["task_specs"]) == EXPANDED_PILOT_TASK_COUNT_V1
    result = run_arc_style_synthetic_2_step_80_pilot_diagnostic_v1()
    assert result["original_40_preserved"] is True
    assert result["original_40_result"] == {"exact": 39, "partial": 1, "unsupported": 0, "failed": 0}
    assert result["new_40_result"] == {"exact": 38, "partial": 2, "unsupported": 0, "failed": 0}
    combined = result["combined_80_result"]
    assert combined == {"exact": 77, "partial": 3, "unsupported": 0, "failed": 0}
    assert sum(combined[key] for key in ("exact", "partial", "unsupported", "failed")) == EXPANDED_PILOT_TASK_COUNT_V1
    assert result["represented_candidate_rows"] == 80
    assert result["accepted_stress_residual_count"] == 1
    assert result["candidate_budget_cutoff_count"] == 0
    assert result["generator_ambiguity_count"] == 0
    assert result["new_unexplained_failures_count"] == 0
    assert result["accidental_composition_match_count"] == 0
    assert len(result["new_40_task_ids"]) == 40


def test_structural_visibility_and_memory_traces_are_bounded_and_targeted() -> None:
    result = run_arc_style_synthetic_2_step_80_pilot_diagnostic_v1()
    line_row = next(row for row in result["evaluations"] if row["source_task_id"] == "pilot_2_step_easy_gen_10_line_recolor_vertical_v1")
    assert line_row["packet_status"] == "exact"
    assert line_row["sequence_visibility_reason"] == "identity_recolor_visibility_repair"
    assert line_row["represented_sequence"] is True
    assert line_row["selected_primitive_sequence"][1]["primitive_id"] == "recolor_symbol"
    assert line_row["selected_primitive_sequence"][1]["parameters"]["from_value"] == 3
    assert line_row["selected_primitive_sequence"][1]["parameters"]["to_value"] == 3

    carryover_row = next(row for row in result["evaluations"] if row["source_task_id"] == "pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1")
    assert carryover_row["packet_status"] == "exact"
    assert carryover_row["sequence_visibility_reason"] == "standard_generated"
    assert carryover_row["step_1_exports"]
    assert carryover_row["parameter_origin_by_key"]

    untouched_noise_row = next(row for row in result["evaluations"] if row["source_task_id"] == "pilot_2_step_easy_gen_02_noise_recolor_color_swap_v1")
    untouched_medium_row = next(row for row in result["evaluations"] if row["source_task_id"] == "pilot_2_step_medium_ctx_09_extract_recolor_bg_transfer_v1")
    stress_row = next(row for row in result["evaluations"] if row["source_task_id"] == "pilot_2_step_stress_08_fill_then_count_v1")
    assert untouched_noise_row["packet_status"] == "partial"
    assert untouched_noise_row["composition_failure_category"] == "first_step_wrong_second_correct"
    assert untouched_medium_row["packet_status"] == "partial"
    assert untouched_medium_row["composition_failure_category"] == "first_step_wrong_second_correct"
    assert stress_row["packet_status"] == "partial"
    assert stress_row["composition_failure_category"] == "right_primitives_wrong_order"


def test_existing_single_step_runner_summary_is_unchanged() -> None:
    result = run_arc_style_synthetic_120_diagnostic_runner_v1()
    assert result["canonical_exact"] == 114
    assert result["canonical_partial"] == 6
    assert result["canonical_unsupported"] == 0
    assert result["canonical_failed"] == 0


def test_module_source_has_no_forbidden_provider_or_chat_calls() -> None:
    module = __import__("weslr.arc_style_synthetic_2_step_pilot_runner", fromlist=["*"])
    source = inspect.getsource(module)
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    forbidden = {
        fragment
        for fragment in FORBIDDEN_IMPORT_FRAGMENTS
        if fragment in imported_modules or any(fragment in mod for mod in imported_modules)
    }
    assert forbidden == set()
    assert "respond_chat(" not in source
    assert "chat_responder." not in source
    assert "openai" not in source.lower()
    assert "anthropic" not in source.lower()
    assert "requests." not in source
    assert "open(" not in source.lower()
