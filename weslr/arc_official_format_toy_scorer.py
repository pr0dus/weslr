"""Toy ARC official-format local scorer.

Deterministic, metadata-only, and fail-closed.
This scorer only evaluates synthetic/toy fixtures and validates exact grid
matching against the official-format-shaped toy bundle.

It does not load official ARC data, implement the official public scorer,
call tools, call models, call the web, or touch `.weslr` paths.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

from weslr.arc_official_contamination_boundary import (
    classify_run_phase,
    summarize_boundary_status,
    validate_contamination_boundary_record,
    validate_result_claim,
)
from weslr.arc_official_format_toy_adapter import (
    TOY_DATA_CLASS_V1,
    TOY_RUN_PHASE_V1,
    export_solver_visible_toy_bundle,
    parse_toy_official_format_bundle,
    validate_toy_candidate_outputs,
    validate_toy_official_format_bundle,
)

SCHEMA_VERSION_V1 = "arc_official_format_toy_scorer_v1"
TOY_ONLY_V1 = True
NOT_OFFICIAL_SCORE_V1 = True


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    return " ".join(str(value).split())


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return deepcopy(value)
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _coerce_bundle(bundle: Any) -> dict[str, Any]:
    if isinstance(bundle, str):
        return parse_toy_official_format_bundle(bundle)
    return deepcopy(bundle) if isinstance(bundle, Mapping) else {}


def _exact_grid_equal(left: Any, right: Any) -> bool:
    if not isinstance(left, list) or not isinstance(right, list):
        return False
    if len(left) != len(right):
        return False
    for left_row, right_row in zip(left, right):
        if not isinstance(left_row, list) or not isinstance(right_row, list):
            return False
        if len(left_row) != len(right_row):
            return False
        for left_cell, right_cell in zip(left_row, right_row):
            if type(left_cell) is not type(right_cell):
                return False
            if left_cell != right_cell:
                return False
    return True


def validate_toy_scorer_boundary_record(record: Any) -> dict[str, Any]:
    data = _as_mapping(record)
    normalized = {
        "data_class": _text(data.get("data_class")) or TOY_DATA_CLASS_V1,
        "run_phase": _text(data.get("run_phase")) or TOY_RUN_PHASE_V1,
        "toy_fixture": True,
        "official_data_touched": bool(data.get("official_data_touched")),
        "hidden_private_data_touched": bool(data.get("hidden_private_data_touched")),
        "internet_tool_model_calls_during_solving": bool(data.get("internet_tool_model_calls_during_solving")),
        "expected_output_leakage": bool(data.get("expected_output_leakage")),
        "internal_task_language_leakage": bool(data.get("internal_task_language_leakage")),
        "synthetic_official_score_mixing": bool(data.get("synthetic_official_score_mixing")),
    }
    if data.get("dataset_provenance") is not None:
        normalized["dataset_provenance"] = deepcopy(data.get("dataset_provenance"))
    validated = validate_contamination_boundary_record(normalized)
    if classify_run_phase(validated) != TOY_RUN_PHASE_V1:
        raise ValueError("Toy scorer must validate against phase_1_toy_fixture_adapter")
    return validated


def _validate_candidate_pairs(bundle: Any, candidate_outputs: Any) -> dict[str, Any]:
    validated_candidates = validate_toy_candidate_outputs(bundle, candidate_outputs)
    return validated_candidates


def score_toy_official_format_bundle(bundle: Any, candidate_outputs: Any) -> dict[str, Any]:
    raw_bundle = _coerce_bundle(bundle)
    validated_bundle = validate_toy_official_format_bundle(raw_bundle)
    candidate_validation = _validate_candidate_pairs(raw_bundle, candidate_outputs)
    visible_bundle = export_solver_visible_toy_bundle(raw_bundle)

    tests = _as_list(raw_bundle.get("test"))
    per_test_scores: list[dict[str, Any]] = []
    solved_count = 0

    for index, test in enumerate(tests):
        expected_output = test.get("expected_output")
        if expected_output is None:
            raise ValueError("Missing expected_output for toy scorer")
        candidates = _as_list(_as_list(candidate_outputs)[index]) if isinstance(candidate_outputs, list) and index < len(candidate_outputs) else []
        if len(candidates) != 2:
            raise ValueError("Each test input must have exactly two candidate outputs")
        candidate_1_matches = _exact_grid_equal(candidates[0], expected_output)
        candidate_2_matches = _exact_grid_equal(candidates[1], expected_output)
        solved = candidate_1_matches or candidate_2_matches
        winning_candidate_index = 0 if candidate_1_matches else 1 if candidate_2_matches else None
        if solved:
            solved_count += 1
        per_test_scores.append(
            {
                "test_index": index,
                "candidate_count": 2,
                "candidate_1_matches": candidate_1_matches,
                "candidate_2_matches": candidate_2_matches,
                "winning_candidate_index": winning_candidate_index,
                "solved": solved,
            }
        )

    total_tests = len(tests)
    toy_fraction = 0.0 if total_tests == 0 else solved_count / total_tests
    toy_percentage = toy_fraction * 100.0
    boundary_record = {
        "data_class": TOY_DATA_CLASS_V1,
        "run_phase": TOY_RUN_PHASE_V1,
        "toy_fixture": True,
        "official_data_touched": False,
        "hidden_private_data_touched": False,
        "internet_tool_model_calls_during_solving": False,
        "expected_output_leakage": False,
        "internal_task_language_leakage": False,
        "synthetic_official_score_mixing": False,
        "official_run_proof": False,
        "local_public_run_proof": False,
        "official_percentage": 0,
    }
    boundary_result = validate_toy_scorer_boundary_record(boundary_record)
    boundary_summary = summarize_boundary_status(boundary_record)

    return {
        "valid": True,
        "schema_version": SCHEMA_VERSION_V1,
        "task_id": validated_bundle["task_id"],
        "toy_only": TOY_ONLY_V1,
        "not_official_score": NOT_OFFICIAL_SCORE_V1,
        "per_test_scoring_metadata": per_test_scores,
        "total_test_inputs": total_tests,
        "solved_test_inputs": solved_count,
        "failed_test_inputs": total_tests - solved_count,
        "task_solved": solved_count == total_tests,
        "task_failed": solved_count != total_tests,
        "toy_score_fraction": toy_fraction,
        "toy_score_percentage": toy_percentage,
        "aggregate_toy_percentage": toy_percentage,
        "solver_visible_bundle": visible_bundle,
        "candidate_validation": candidate_validation,
        "contamination_boundary": boundary_result,
        "boundary_summary": boundary_summary,
        "official_percentage_claimable_text": boundary_summary["official_percentage_claimable_text"],
        "official_percentage_claimable_value": boundary_summary["official_percentage_claimable_value"],
    }


def aggregate_toy_official_format_scores(task_runs: Any) -> dict[str, Any]:
    runs = _as_list(task_runs)
    if not runs:
        raise ValueError("Missing toy scorer task runs")

    per_task_results: list[dict[str, Any]] = []
    total_tests = 0
    total_solved = 0
    for index, task_run in enumerate(runs):
        data = _as_mapping(task_run)
        if "bundle" not in data or "candidate_outputs" not in data:
            raise ValueError(f"Missing bundle or candidate_outputs at task run index {index}")
        scored = score_toy_official_format_bundle(data.get("bundle"), data.get("candidate_outputs"))
        per_task_results.append(scored)
        total_tests += scored["total_test_inputs"]
        total_solved += scored["solved_test_inputs"]

    toy_fraction = 0.0 if total_tests == 0 else total_solved / total_tests
    toy_percentage = toy_fraction * 100.0
    boundary_record = {
        "data_class": TOY_DATA_CLASS_V1,
        "run_phase": TOY_RUN_PHASE_V1,
        "toy_fixture": True,
        "official_data_touched": False,
        "hidden_private_data_touched": False,
        "internet_tool_model_calls_during_solving": False,
        "expected_output_leakage": False,
        "internal_task_language_leakage": False,
        "synthetic_official_score_mixing": False,
        "official_run_proof": False,
        "local_public_run_proof": False,
        "official_percentage": 0,
    }
    boundary_result = validate_toy_scorer_boundary_record(boundary_record)
    boundary_summary = summarize_boundary_status(boundary_record)

    return {
        "valid": True,
        "schema_version": SCHEMA_VERSION_V1,
        "toy_only": TOY_ONLY_V1,
        "not_official_score": NOT_OFFICIAL_SCORE_V1,
        "task_results": per_task_results,
        "aggregate_test_inputs": total_tests,
        "aggregate_solved_test_inputs": total_solved,
        "aggregate_failed_test_inputs": total_tests - total_solved,
        "aggregate_toy_fraction": toy_fraction,
        "aggregate_toy_percentage": toy_percentage,
        "contamination_boundary": boundary_result,
        "boundary_summary": boundary_summary,
        "official_percentage_claimable_text": boundary_summary["official_percentage_claimable_text"],
        "official_percentage_claimable_value": boundary_summary["official_percentage_claimable_value"],
    }


def validate_toy_score_claim(claim: Any) -> dict[str, Any]:
    data = _as_mapping(claim)
    validate_result_claim(
        {
            "claim_kind": _text(data.get("claim_kind")) or "synthetic_score",
            "evidence_kind": "synthetic",
            "synthetic_score": data.get("toy_score_percentage"),
            "official_run_proof": False,
            "local_public_run_proof": False,
            "official_arc_performance": False,
            "official_percentage": data.get("official_percentage"),
        }
    )
    if _text(data.get("claim_kind")) in {"official_arc_performance", "official_local_percentage"}:
        raise ValueError("Toy local scorer results cannot be claimed as official ARC performance")
    if data.get("official_arc_performance") is True:
        raise ValueError("Toy local scorer results cannot be claimed as official ARC performance")
    return {
        "valid": True,
        "schema_version": SCHEMA_VERSION_V1,
        "toy_only": TOY_ONLY_V1,
        "not_official_score": NOT_OFFICIAL_SCORE_V1,
    }


__all__ = [
    "SCHEMA_VERSION_V1",
    "TOY_ONLY_V1",
    "NOT_OFFICIAL_SCORE_V1",
    "validate_toy_scorer_boundary_record",
    "score_toy_official_format_bundle",
    "aggregate_toy_official_format_scores",
    "validate_toy_score_claim",
]
