from __future__ import annotations

import ast
import inspect
import json
from typing import Any

from weslr.arc_style_grid_generalization_stress import (
    MIN_VARIANT_COUNT_V1,
    SUPPORTED_FAMILIES_V1,
    build_arc_style_synthetic_generalization_tasks_v1,
    perturb_arc_style_task_metadata_v1,
    run_arc_style_generalization_stress_v1,
    summarize_arc_style_generalization_stress_packet_v1,
    to_arc_style_generalization_stress_json_safe_v1,
    validate_arc_style_generalization_stress_packet_v1,
)
from weslr.arc_style_grid_solver_dry_run import generate_arc_style_candidate_rules_v1, run_arc_style_bounded_solver_dry_run_v1

FORBIDDEN_IMPORT_FRAGMENTS = (
    "provider",
    "payment",
    "chat_responder",
    "respond_chat",
    "openai",
    "anthropic",
    "google",
    "ollama",
)


def _json_safe(value: Any) -> Any:
    safe = to_arc_style_generalization_stress_json_safe_v1(value)
    json.dumps(safe, ensure_ascii=False)
    return safe


def _task_by_family(tasks: list[dict[str, Any]], family: str) -> dict[str, Any]:
    for task in tasks:
        if task["trace"]["toy_task_type"] == family:
            return task
    raise AssertionError(family)


def test_generalization_tasks_cover_supported_families_and_count() -> None:
    tasks = build_arc_style_synthetic_generalization_tasks_v1()
    families = {task["trace"]["toy_task_type"] for task in tasks if task["trace"]["toy_task_type"] in SUPPORTED_FAMILIES_V1}
    assert len(tasks) >= MIN_VARIANT_COUNT_V1
    assert families == set(SUPPORTED_FAMILIES_V1)
    assert all(task["task_source"] == "internal_synthetic_toy_tasks_v1" for task in tasks)
    assert all(task["trace"]["internal_synthetic_only"] is True for task in tasks)


def test_metadata_perturbation_changes_ids_notes_and_pair_order_without_changing_grids() -> None:
    task = _task_by_family(build_arc_style_synthetic_generalization_tasks_v1(), "move_single_object")
    perturbed = perturb_arc_style_task_metadata_v1(
        task,
        task_id="renamed_task",
        notes=["mutated-note"],
        reverse_train_pairs=True,
        reorder_trace_fields=True,
        trace_overrides={"extra_marker": True},
    )
    assert perturbed["task_id"] == "renamed_task"
    assert perturbed["failure_notes"] == ["mutated-note"]
    assert perturbed["train_pairs"][0]["pair_id"] != task["train_pairs"][0]["pair_id"] or len(task["train_pairs"]) == 1
    assert _json_safe(task["train_pairs"])[0]["input_grid"] == _json_safe(perturbed["train_pairs"])[-1]["input_grid"]
    assert perturbed["trace"]["extra_marker"] is True


def test_variant_metadata_shuffles_do_not_change_solver_selection_for_same_semantics() -> None:
    tasks = build_arc_style_synthetic_generalization_tasks_v1()
    left = _task_by_family(tasks, "copy_grid")
    right = perturb_arc_style_task_metadata_v1(
        left,
        task_id="copy_renamed_for_stress",
        notes="",
        reverse_train_pairs=True,
        reorder_trace_fields=True,
        trace_overrides={"variant_key": "copy_shuffled"},
    )
    packet = run_arc_style_bounded_solver_dry_run_v1([left, right])
    results = {result["task_id"]: result for result in packet["task_results"]}
    assert results[left["task_id"]]["selected_primitive_sequence"] == results[right["task_id"]]["selected_primitive_sequence"]
    assert results[left["task_id"]]["selected_candidate_id"].split(":")[1] == results[right["task_id"]]["selected_candidate_id"].split(":")[1]


def test_renamed_task_ids_and_empty_notes_do_not_change_selected_primitive() -> None:
    task = _task_by_family(build_arc_style_synthetic_generalization_tasks_v1(), "recolor_symbol")
    renamed = perturb_arc_style_task_metadata_v1(task, task_id="recolored_again", notes=[])
    packet = run_arc_style_bounded_solver_dry_run_v1([task, renamed])
    base, perturbed = packet["task_results"]
    assert base["selected_primitive_sequence"] == perturbed["selected_primitive_sequence"]
    assert base["selected_candidate_id"].split(":")[1] == perturbed["selected_candidate_id"].split(":")[1]


def test_lie_about_family_in_task_id_or_notes_does_not_control_selection() -> None:
    task = _task_by_family(build_arc_style_synthetic_generalization_tasks_v1(), "move_single_object")
    lied = perturb_arc_style_task_metadata_v1(
        task,
        task_id="this_is_not_a_move_task",
        notes=["this is definitely a copy task"],
        trace_overrides={"toy_task_type": "copy_grid", "claimed_family": "copy_grid"},
    )
    packet = run_arc_style_bounded_solver_dry_run_v1([task, lied])
    base, perturbed = packet["task_results"]
    assert base["selected_primitive_sequence"] == perturbed["selected_primitive_sequence"]
    assert base["selected_candidate_id"].split(":")[1] == perturbed["selected_candidate_id"].split(":")[1]


def test_supported_variants_remain_solved_after_metadata_perturbation() -> None:
    packet = run_arc_style_generalization_stress_v1()
    validation = validate_arc_style_generalization_stress_packet_v1(packet)
    summary = summarize_arc_style_generalization_stress_packet_v1(packet)
    assert validation["valid"] is True
    assert summary["variant_count"] == packet["variant_count"]
    assert packet["no_score_claim"] is True
    assert packet["exact_match_count"] >= 18
    assert packet["partial_match_count"] >= 0
    assert packet["unsupported_count"] >= 1
    assert packet["failure_ledger_summary"]["entries_count"] > 0
    assert all(task_result["no_score_claim"] is True for task_result in packet["task_results"])
    assert all(task_result["task_source"] == "internal_synthetic_toy_tasks_v1" for task_result in packet["task_results"])
    assert packet["trace"]["uses_train_output_for_transformation_inference"] is True
    assert packet["trace"]["uses_test_output"] is False
    assert packet["trace"]["uses_task_id_for_candidate_selection"] is False
    assert packet["trace"]["uses_notes_for_candidate_selection"] is False
    assert packet["trace"]["lookup_table_detected"] is False
    assert all(result["trace"]["structural_evidence_labels"] for result in packet["task_results"])
    assert all(result["trace"]["uses_test_output"] is False for result in packet["task_results"])
    assert all(result["trace"]["lookup_table_detected"] is False for result in packet["task_results"])


def test_anti_leakage_checks_are_present_and_ids_or_notes_do_not_control_selection() -> None:
    tasks = build_arc_style_synthetic_generalization_tasks_v1()
    move_task = _task_by_family(tasks, "move_single_object")
    renamed = perturb_arc_style_task_metadata_v1(move_task, task_id="do_not_use_family_name", notes=["noise only"])
    packet = run_arc_style_bounded_solver_dry_run_v1([move_task, renamed])
    base = packet["task_results"][0]
    perturbed = packet["task_results"][1]
    assert packet["no_score_claim"] is True
    assert packet["task_results"]
    assert base["selected_primitive_sequence"] == perturbed["selected_primitive_sequence"]
    assert base["selected_candidate_id"].split(":")[1] == perturbed["selected_candidate_id"].split(":")[1]
    assert base["trace"]["uses_train_output_for_transformation_inference"] is True
    assert base["trace"]["uses_test_output"] is False
    assert base["trace"]["uses_task_id_for_candidate_selection"] is False
    assert base["trace"]["uses_notes_for_candidate_selection"] is False
    assert base["trace"]["lookup_table_detected"] is False
    assert perturbed["trace"]["structural_evidence_labels"]
    assert all(candidate["generation_trace"]["structural_evidence_labels"] for candidate in packet["task_results"][0]["candidate_packets"])
    stress = run_arc_style_generalization_stress_v1([move_task, renamed])
    assert stress["anti_leakage_checks"]["task_id_dependency_avoided"] is True
    assert stress["anti_leakage_checks"]["notes_dependency_avoided"] is True
    assert stress["anti_leakage_checks"]["expected_output_leakage_avoided"] is True
    assert stress["anti_leakage_checks"]["uses_train_output_for_transformation_inference"] is True
    assert stress["anti_leakage_checks"]["uses_test_output"] is False
    assert stress["anti_leakage_checks"]["uses_task_id_for_candidate_selection"] is False
    assert stress["anti_leakage_checks"]["uses_notes_for_candidate_selection"] is False
    assert stress["anti_leakage_checks"]["lookup_table_detected"] is False


def test_unsupported_decoys_remain_unsupported() -> None:
    tasks = build_arc_style_synthetic_generalization_tasks_v1()
    unsupported = [task for task in tasks if task["trace"]["toy_task_type"] in {"rotate", "reflect"}]
    assert len(unsupported) == 2
    packet = run_arc_style_bounded_solver_dry_run_v1(unsupported)
    assert all(result["train_fit_status"] != "fit" for result in packet["task_results"])
    assert all(result["selected_candidate_id"] for result in packet["task_results"])
    assert all(result["selected_primitive_sequence"][0]["primitive_id"] in {"rotate", "reflect"} for result in packet["task_results"])


def test_candidate_generation_exposes_structural_evidence_trace() -> None:
    task = _task_by_family(build_arc_style_synthetic_generalization_tasks_v1(), "border_frame_fill")
    candidates = generate_arc_style_candidate_rules_v1(task)
    assert candidates
    assert all(candidate["generation_trace"]["uses_train_output_for_transformation_inference"] is True for candidate in candidates)
    assert all(candidate["generation_trace"]["uses_test_output"] is False for candidate in candidates)
    assert all(candidate["generation_trace"]["uses_task_id_for_candidate_selection"] is False for candidate in candidates)
    assert all(candidate["generation_trace"]["uses_notes_for_candidate_selection"] is False for candidate in candidates)
    assert all(candidate["generation_trace"]["lookup_table_detected"] is False for candidate in candidates)
    assert all(candidate["generation_trace"]["structural_evidence_labels"] for candidate in candidates)


def test_module_source_has_no_forbidden_provider_or_chat_calls() -> None:
    module = __import__("weslr.arc_style_grid_generalization_stress", fromlist=["*"])
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
    assert "competition" not in source.lower()
    assert "kaggle" not in source.lower()
