from __future__ import annotations

import ast
import inspect
import json
from typing import Any

from weslr.arc_style_grid_schema_helpers import (
    TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
    TOY_TASK_TYPES_V1,
    build_arc_style_grid_task_packet_v1,
    build_arc_style_grid_train_pair_v1,
    build_internal_arc_style_grid_toy_tasks_v1,
)
from weslr.arc_style_grid_solver_dry_run import (
    MAX_CANDIDATES_PER_TASK_V1,
    MAX_PRIMITIVE_SEQUENCE_DEPTH_V1,
    SOLVER_TYPE_V1,
    build_arc_style_solver_dry_run_result_v1,
    generate_arc_style_candidate_rules_v1,
    infer_arc_style_primitive_candidates_from_grid_delta_v1,
    run_arc_style_bounded_solver_dry_run_v1,
    summarize_arc_style_solver_dry_run_result_v1,
    to_arc_style_solver_dry_run_json_safe_v1,
    validate_arc_style_solver_dry_run_result_v1,
)

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
    safe = to_arc_style_solver_dry_run_json_safe_v1(value)
    json.dumps(safe, ensure_ascii=False)
    return safe


def _task_by_type(task_type: str) -> dict[str, Any]:
    for task in build_internal_arc_style_grid_toy_tasks_v1():
        if task["trace"]["toy_task_type"] == task_type:
            return task
    raise AssertionError(task_type)


def test_candidate_generation_is_deterministic_and_bounded() -> None:
    task = _task_by_type("recolor_symbol")
    first = generate_arc_style_candidate_rules_v1(task)
    second = generate_arc_style_candidate_rules_v1(task)
    inference = infer_arc_style_primitive_candidates_from_grid_delta_v1(task)
    assert _json_safe(first) == _json_safe(second)
    assert 1 <= len(first) <= MAX_CANDIDATES_PER_TASK_V1
    assert all(candidate["bounded_depth"] <= MAX_PRIMITIVE_SEQUENCE_DEPTH_V1 for candidate in first)
    assert all(candidate["is_executable"] is True for candidate in first)
    assert all(candidate["task_id"] == task["task_id"] for candidate in first)
    assert all(candidate["generation_trace"]["uses_train_output_for_transformation_inference"] is True for candidate in first)
    assert all(candidate["generation_trace"]["uses_test_output"] is False for candidate in first)
    assert all(candidate["generation_trace"]["uses_task_id_for_candidate_selection"] is False for candidate in first)
    assert all(candidate["generation_trace"]["uses_notes_for_candidate_selection"] is False for candidate in first)
    assert all(candidate["generation_trace"]["lookup_table_detected"] is False for candidate in first)
    assert all(candidate["generation_trace"]["structural_evidence_labels"] for candidate in first)
    assert inference["uses_train_output_for_transformation_inference"] is True
    assert inference["uses_test_output"] is False
    assert inference["uses_task_id_for_candidate_selection"] is False
    assert inference["uses_notes_for_candidate_selection"] is False
    assert inference["lookup_table_detected"] is False
    assert inference["structural_evidence_labels"]


def test_internal_toy_tasks_solve_exactly() -> None:
    packet = run_arc_style_bounded_solver_dry_run_v1()
    validation = validate_arc_style_solver_dry_run_result_v1(packet)
    summary = summarize_arc_style_solver_dry_run_result_v1(packet)
    assert validation["valid"] is True
    assert summary["solver_type"] == SOLVER_TYPE_V1
    assert packet["no_score_claim"] is True
    assert packet["task_count"] == 5
    assert packet["selected_exact_match_count"] == 5
    assert packet["selected_partial_match_count"] == 0
    assert packet["selected_unsupported_count"] == 0
    assert summary["selected_exact_match_count"] == 5
    assert len(packet["task_results"]) == 5
    assert all(result["train_fit_status"] == "fit" for result in packet["task_results"])
    assert all(result["selected_candidate_id"] for result in packet["task_results"])
    assert all(result["candidate_count"] <= MAX_CANDIDATES_PER_TASK_V1 for result in packet["task_results"])
    assert all(result["no_score_claim"] is True for result in packet["task_results"])
    assert all(result["task_source"] == TASK_SOURCE_INTERNAL_SYNTHETIC_V1 for result in packet["task_results"])
    assert packet["trace"]["uses_train_output_for_transformation_inference"] is True
    assert packet["trace"]["uses_test_output"] is False
    assert packet["trace"]["uses_task_id_for_candidate_selection"] is False
    assert packet["trace"]["uses_notes_for_candidate_selection"] is False
    assert packet["trace"]["lookup_table_detected"] is False


def test_each_supported_toy_task_chooses_the_expected_primitive_family() -> None:
    packet = run_arc_style_bounded_solver_dry_run_v1()
    selected_by_type = {result["toy_task_type"]: result for result in packet["task_results"]}
    assert selected_by_type["copy_grid"]["selected_primitive_sequence"][0]["primitive_id"] == "copy"
    assert selected_by_type["recolor_symbol"]["selected_primitive_sequence"][0]["primitive_id"] == "recolor"
    assert selected_by_type["move_single_object"]["selected_primitive_sequence"][0]["primitive_id"] == "move"
    assert selected_by_type["complete_symmetry"]["selected_primitive_sequence"][0]["primitive_id"] == "complete_symmetry"
    assert selected_by_type["border_frame_fill"]["selected_primitive_sequence"][0]["primitive_id"] in {"fill", "border_frame"}
    assert selected_by_type["border_frame_fill"]["train_fit_status"] == "fit"


def test_rejected_candidates_preserve_reasons_and_failure_ledger_records_categories() -> None:
    packet = run_arc_style_bounded_solver_dry_run_v1()
    copy_task = next(result for result in packet["task_results"] if result["toy_task_type"] == "copy_grid")
    assert copy_task["rejected_candidates"]
    assert all(item["rejection_reason"] for item in copy_task["rejected_candidates"])
    assert all(item["failure_ledger_category"] for item in copy_task["rejected_candidates"])
    assert packet["failure_ledger"]["entries"]
    assert packet["failure_ledger"]["category_counts"]
    assert any(category in packet["failure_ledger"]["repeated_failure_categories"] for category in ["underfit_rule", "overfit_rule", "missed_transformation_family"])


def test_failure_ledger_records_mismatch_when_no_exact_solution_exists() -> None:
    input_grid = [[1, 0, 0], [0, 2, 0]]
    output_grid = [[0, 1], [0, 2], [0, 0]]
    pair = build_arc_style_grid_train_pair_v1("custom-rotate-ish-pair", input_grid, output_grid, "custom")
    task_packet = build_arc_style_grid_task_packet_v1(
        task_id="custom_no_exact_v1",
        task_source=TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
        train_pairs=[pair],
        test_input=input_grid,
        trace={"toy_task_type": "unknown_family", "internal_synthetic_only": True, "toy_task": True},
    )
    packet = run_arc_style_bounded_solver_dry_run_v1([task_packet])
    task_result = packet["task_results"][0]
    assert task_result["train_fit_status"] in {"partial_fit", "unsupported", "mismatch"}
    assert task_result["selected_candidate_id"] is not None
    assert task_result["failure_notes"]
    assert task_result["trace"]["uses_train_output_for_transformation_inference"] is True
    assert task_result["trace"]["uses_test_output"] is False
    assert task_result["trace"]["uses_task_id_for_candidate_selection"] is False
    assert task_result["trace"]["uses_notes_for_candidate_selection"] is False
    assert task_result["trace"]["lookup_table_detected"] is False
    assert packet["failure_ledger"]["entries"]
    assert packet["failure_ledger"]["category_counts"]
    assert any(count >= 1 for count in packet["failure_ledger"]["category_counts"].values())


def test_solver_dry_run_result_is_json_safe_and_no_score_claim_is_preserved() -> None:
    packet = run_arc_style_bounded_solver_dry_run_v1()
    safe = _json_safe(packet)
    assert packet["no_score_claim"] is True
    assert json.dumps(safe, ensure_ascii=False)
    assert safe["no_score_claim"] is True
    assert "score" not in packet or packet["no_score_claim"] is True


def test_module_source_has_no_forbidden_provider_or_chat_calls() -> None:
    module = __import__("weslr.arc_style_grid_solver_dry_run", fromlist=["*"])
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
    assert "write(" not in source.lower()
    assert "respond_chat" not in source
    assert "chat_responder" not in source
    assert "openai" not in source.lower()
    assert "anthropic" not in source.lower()
