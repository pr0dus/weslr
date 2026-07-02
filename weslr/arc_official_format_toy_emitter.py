"""Toy ARC official-format answer emitter.

Deterministic, metadata-only, and fail-closed.
This emitter only accepts synthetic/toy fixtures and emits exactly two
candidate outputs per test input for toy-local evaluation and submission
shape checks.

It does not load official ARC data, implement the official public emitter,
claim official ARC performance, call tools, call models, call the web, or
touch `.weslr` paths.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from weslr.arc_official_contamination_boundary import (
    classify_run_phase,
    summarize_boundary_status,
    validate_contamination_boundary_record,
)
from weslr.arc_official_format_toy_adapter import (
    TOY_DATA_CLASS_V1,
    TOY_RUN_PHASE_V1,
    export_solver_visible_toy_bundle,
    validate_toy_candidate_outputs,
    validate_toy_official_format_bundle,
)

SCHEMA_VERSION_V1 = "arc_official_format_toy_emitter_v1"
TOY_ONLY_V1 = True
NOT_OFFICIAL_SUBMISSION_V1 = True

_FORBIDDEN_EMISSION_KEYS_V1 = {
    "expected_output",
    "expected_outputs",
    "hidden_answer",
    "hidden_answers",
    "official_score",
    "official_arc_performance",
    "official_percentage",
    "local_public_percentage",
}


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


def _contains_forbidden_emission_field(value: Any) -> list[str]:
    issues: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = _text(key)
            if key_text in _FORBIDDEN_EMISSION_KEYS_V1:
                issues.append(key_text)
            issues.extend(_contains_forbidden_emission_field(nested))
    elif isinstance(value, list):
        for nested in value:
            issues.extend(_contains_forbidden_emission_field(nested))
    elif isinstance(value, tuple):
        for nested in value:
            issues.extend(_contains_forbidden_emission_field(nested))
    return issues


def validate_toy_emitter_boundary_record(record: Any) -> dict[str, Any]:
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
        raise ValueError("Toy emitter must validate against phase_1_toy_fixture_adapter")
    return validated


def _preserve_test_identity(test: Mapping[str, Any]) -> dict[str, Any]:
    identity: dict[str, Any] = {}
    for key in ("test_id", "test_name", "case_id", "example_id"):
        if key in test and _text(test.get(key)):
            identity[key] = _text(test.get(key))
    return identity


def emit_toy_official_format_submission(bundle: Any, candidate_outputs: Any) -> dict[str, Any]:
    raw_bundle = _as_mapping(bundle)
    validated_bundle = validate_toy_official_format_bundle(bundle)
    candidate_validation = validate_toy_candidate_outputs(validated_bundle, candidate_outputs)
    visible_bundle = export_solver_visible_toy_bundle(validated_bundle)

    raw_tests = _as_list(raw_bundle.get("test"))
    emitted_tests: list[dict[str, Any]] = []
    for index, test in enumerate(validated_bundle["test"]):
        test_entry = {
            "test_index": index,
            "candidate_count": 2,
            "candidate_outputs": deepcopy(_as_list(candidate_outputs)[index]),
        }
        if index < len(raw_tests):
            test_entry.update(_preserve_test_identity(_as_mapping(raw_tests[index])))
        emitted_tests.append(test_entry)

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
    boundary_result = validate_toy_emitter_boundary_record(boundary_record)
    boundary_summary = summarize_boundary_status(boundary_record)

    submission = {
        "valid": True,
        "schema_version": SCHEMA_VERSION_V1,
        "task_id": validated_bundle["task_id"],
        "toy_only": TOY_ONLY_V1,
        "not_official_submission": NOT_OFFICIAL_SUBMISSION_V1,
        "candidate_outputs": deepcopy(candidate_outputs),
        "tests": emitted_tests,
        "task": {
            "task_id": validated_bundle["task_id"],
        },
        "bundle_provenance": deepcopy(validated_bundle["bundle_provenance"]),
        "solver_visible_bundle": visible_bundle,
        "candidate_validation": candidate_validation,
        "contamination_boundary": boundary_result,
        "boundary_summary": boundary_summary,
        "official_percentage_claimable_text": boundary_summary["official_percentage_claimable_text"],
        "official_percentage_claimable_value": boundary_summary["official_percentage_claimable_value"],
    }
    validate_toy_official_format_submission(submission)
    return submission


def validate_toy_official_format_submission(submission: Any) -> dict[str, Any]:
    data = _as_mapping(submission)
    if not data:
        raise ValueError("Invalid toy submission")
    issues = _contains_forbidden_emission_field(data)
    if issues:
        raise ValueError(f"Invalid toy submission: {sorted(set(issues))}")
    if not data.get("toy_only"):
        raise ValueError("Toy submissions must be marked toy_only")
    if not data.get("not_official_submission"):
        raise ValueError("Toy submissions must be marked not_official_submission")
    task_id = _text(data.get("task_id"))
    if not task_id:
        raise ValueError("Missing task_id")
    tests = data.get("tests")
    if not isinstance(tests, list) or not tests:
        raise ValueError("Missing tests")
    candidate_outputs = data.get("candidate_outputs")
    if not isinstance(candidate_outputs, list) or len(candidate_outputs) != len(tests):
        raise ValueError("Candidate outputs must match number of tests")
    for index, test in enumerate(tests):
        test_data = _as_mapping(test)
        if _text(test_data.get("task_id")) and _text(test_data.get("task_id")) != task_id:
            raise ValueError("Test task_id mismatch")
        if not isinstance(test_data.get("candidate_outputs"), list):
            raise ValueError("Missing candidate outputs for test")
        if len(test_data.get("candidate_outputs")) != 2:
            raise ValueError("Each emitted test must have exactly two candidate outputs")
        if len(candidate_outputs[index]) != 2:
            raise ValueError("Each emitted test must have exactly two candidate outputs")
    boundary = validate_toy_emitter_boundary_record(data.get("contamination_boundary", {}))
    boundary_summary = summarize_boundary_status(data.get("contamination_boundary", {}))
    if boundary["run_phase"] != TOY_RUN_PHASE_V1:
        raise ValueError("Toy emitter must remain in phase_1_toy_fixture_adapter")
    return {
        "valid": True,
        "schema_version": SCHEMA_VERSION_V1,
        "task_id": task_id,
        "toy_only": TOY_ONLY_V1,
        "not_official_submission": NOT_OFFICIAL_SUBMISSION_V1,
        "contamination_boundary": boundary,
        "boundary_summary": boundary_summary,
        "official_percentage_claimable_text": boundary_summary["official_percentage_claimable_text"],
        "official_percentage_claimable_value": boundary_summary["official_percentage_claimable_value"],
    }


def validate_toy_score_claim(claim: Any) -> dict[str, Any]:
    data = _as_mapping(claim)
    if _text(data.get("claim_kind")) in {"official_arc_performance", "official_local_percentage"}:
        raise ValueError("Toy submissions cannot be claimed as official ARC performance")
    if data.get("official_arc_performance") is True:
        raise ValueError("Toy submissions cannot be claimed as official ARC performance")
    return {
        "valid": True,
        "schema_version": SCHEMA_VERSION_V1,
        "toy_only": TOY_ONLY_V1,
        "not_official_submission": NOT_OFFICIAL_SUBMISSION_V1,
    }


__all__ = [
    "SCHEMA_VERSION_V1",
    "TOY_ONLY_V1",
    "NOT_OFFICIAL_SUBMISSION_V1",
    "validate_toy_emitter_boundary_record",
    "emit_toy_official_format_submission",
    "validate_toy_official_format_submission",
    "validate_toy_score_claim",
]
