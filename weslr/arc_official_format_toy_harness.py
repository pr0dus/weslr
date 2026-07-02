"""Toy ARC official-format end-to-end harness.

Deterministic, metadata-only, and fail-closed.
This harness chains the toy adapter -> toy emitter -> toy scorer on synthetic
fixtures only, to prove the official-format shape works before any official
ARC data is touched.

It does not load official ARC data, implement the official public harness,
claim official ARC performance, call tools, call models, call the web, or
touch `.weslr` paths.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Mapping

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
    validate_toy_official_format_bundle,
)
from weslr.arc_official_format_toy_emitter import (
    NOT_OFFICIAL_SUBMISSION_V1,
    TOY_ONLY_V1,
    emit_toy_official_format_submission,
    validate_toy_official_format_submission,
)
from weslr.arc_official_format_toy_scorer import (
    SCHEMA_VERSION_V1 as TOY_SCORER_SCHEMA_VERSION_V1,
    score_toy_official_format_bundle,
)

SCHEMA_VERSION_V1 = "arc_official_format_toy_harness_v1"
TOY_ONLY_V1 = True
NOT_OFFICIAL_SCORE_V1 = True

_FORBIDDEN_LEAK_KEYS_V1 = {
    "expected_output",
    "expected_outputs",
    "hidden_answer",
    "hidden_answers",
    "official_score",
    "official_arc_performance",
    "official_percentage",
    "local_public_percentage",
    "internal_task_language",
}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    return " ".join(str(value).split())


def _contains_forbidden_leak(value: Any) -> list[str]:
    issues: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = _text(key)
            if key_text in _FORBIDDEN_LEAK_KEYS_V1:
                issues.append(key_text)
            issues.extend(_contains_forbidden_leak(nested))
    elif isinstance(value, list):
        for nested in value:
            issues.extend(_contains_forbidden_leak(nested))
    elif isinstance(value, tuple):
        for nested in value:
            issues.extend(_contains_forbidden_leak(nested))
    return issues


def _resolve_candidate_provider(candidate_source: Any, solver_visible_bundle: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    provider_metadata: dict[str, Any] = {}
    if callable(candidate_source):
        provided = candidate_source(deepcopy(solver_visible_bundle))
    elif isinstance(candidate_source, Mapping):
        issues = _contains_forbidden_leak(candidate_source)
        if issues:
            raise ValueError(f"Invalid toy harness candidate provider payload: {sorted(set(issues))}")
        task_id = solver_visible_bundle["task_id"]
        if task_id in candidate_source:
            provided = candidate_source[task_id]
        elif "candidate_outputs" in candidate_source:
            provided = candidate_source["candidate_outputs"]
            provider_metadata = deepcopy(candidate_source.get("provider_metadata", {})) if isinstance(candidate_source.get("provider_metadata"), Mapping) else {}
        else:
            provided = deepcopy(candidate_source)
    else:
        raise ValueError("Toy harness requires a callable provider or candidate map")

    if isinstance(provided, Mapping):
        issues = _contains_forbidden_leak(provided)
        if issues:
            raise ValueError(f"Invalid toy harness candidate provider payload: {sorted(set(issues))}")
        if not provider_metadata and isinstance(provided.get("provider_metadata"), Mapping):
            provider_metadata = deepcopy(provided.get("provider_metadata"))
        if "candidate_outputs" in provided:
            return provided["candidate_outputs"], provider_metadata
        if solver_visible_bundle["task_id"] in provided:
            return provided[solver_visible_bundle["task_id"]], provider_metadata
        raise ValueError("Toy harness candidate provider payload missing candidate_outputs")

    return provided, provider_metadata


def validate_toy_end_to_end_harness_boundary_record(record: Any) -> dict[str, Any]:
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
    if data.get("official_percentage") is not None:
        normalized["official_percentage"] = data.get("official_percentage")
    if data.get("official_run_proof") is not None:
        normalized["official_run_proof"] = data.get("official_run_proof")
    if data.get("local_public_run_proof") is not None:
        normalized["local_public_run_proof"] = data.get("local_public_run_proof")
    if data.get("local_public_percentage_claimed") is not None:
        normalized["local_public_percentage_claimed"] = data.get("local_public_percentage_claimed")
    validated = validate_contamination_boundary_record(normalized)
    if classify_run_phase(validated) != TOY_RUN_PHASE_V1:
        raise ValueError("Toy harness must validate against phase_1_toy_fixture_adapter")
    return validated


def run_toy_official_format_harness(bundle: Any, candidate_source: Any) -> dict[str, Any]:
    raw_bundle = parse_toy_official_format_bundle(bundle) if isinstance(bundle, str) else deepcopy(bundle) if isinstance(bundle, Mapping) else {}
    validated_bundle = validate_toy_official_format_bundle(raw_bundle)
    solver_visible_bundle = export_solver_visible_toy_bundle(validated_bundle)
    candidate_payload, provider_metadata = _resolve_candidate_provider(candidate_source, solver_visible_bundle)

    if not isinstance(candidate_payload, list):
        raise ValueError("Toy harness requires candidate outputs as a list")

    emitted_submission = emit_toy_official_format_submission(validated_bundle, candidate_payload)
    score_result = score_toy_official_format_bundle(raw_bundle, emitted_submission["candidate_outputs"])

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
    boundary_result = validate_toy_end_to_end_harness_boundary_record(boundary_record)
    boundary_summary = summarize_boundary_status(boundary_record)

    result = {
        "valid": True,
        "schema_version": SCHEMA_VERSION_V1,
        "task_id": validated_bundle["task_id"],
        "toy_only": TOY_ONLY_V1,
        "not_official_score": NOT_OFFICIAL_SCORE_V1,
        "bundle_provenance": deepcopy(validated_bundle["bundle_provenance"]),
        "solver_visible_bundle": solver_visible_bundle,
        "candidate_provider_metadata": provider_metadata,
        "emitted_submission": emitted_submission,
        "score_result": score_result,
        "per_task_scoring_metadata": deepcopy(score_result["per_test_scoring_metadata"]),
        "aggregate_toy_fraction": score_result["toy_score_fraction"],
        "aggregate_toy_percentage": score_result["aggregate_toy_percentage"],
        "task_solved": score_result["task_solved"],
        "task_failed": score_result["task_failed"],
        "contamination_boundary": boundary_result,
        "boundary_summary": boundary_summary,
        "official_percentage_claimable_text": boundary_summary["official_percentage_claimable_text"],
        "official_percentage_claimable_value": boundary_summary["official_percentage_claimable_value"],
    }
    validate_toy_official_format_harness_result(result)
    return result


def validate_toy_official_format_harness_result(result: Any) -> dict[str, Any]:
    data = _as_mapping(result)
    if not data:
        raise ValueError("Invalid toy harness result")
    if not data.get("toy_only"):
        raise ValueError("Toy harness results must be marked toy_only")
    if not data.get("not_official_score"):
        raise ValueError("Toy harness results must be marked not_official_score")
    if _contains_forbidden_leak(data):
        raise ValueError("Toy harness results contain forbidden leakage")
    if _text(data.get("task_id")) == "":
        raise ValueError("Missing task_id")
    emitted_submission = data.get("emitted_submission")
    if not isinstance(emitted_submission, Mapping):
        raise ValueError("Missing emitted_submission")
    validate_toy_official_format_submission(emitted_submission)
    score_result = data.get("score_result")
    if not isinstance(score_result, Mapping):
        raise ValueError("Missing score_result")
    if score_result.get("official_percentage_claimable_value") != 0:
        raise ValueError("Official percentage claimable must remain none/0")
    boundary = validate_toy_end_to_end_harness_boundary_record(data.get("contamination_boundary", {}))
    if boundary["run_phase"] != TOY_RUN_PHASE_V1:
        raise ValueError("Toy harness must remain in phase_1_toy_fixture_adapter")
    return {
        "valid": True,
        "schema_version": SCHEMA_VERSION_V1,
        "task_id": _text(data.get("task_id")),
        "toy_only": TOY_ONLY_V1,
        "not_official_score": NOT_OFFICIAL_SCORE_V1,
        "contamination_boundary": boundary,
        "boundary_summary": summarize_boundary_status(data.get("contamination_boundary", {})),
        "official_percentage_claimable_text": _text(data.get("official_percentage_claimable_text")) or "none yet",
        "official_percentage_claimable_value": data.get("official_percentage_claimable_value", 0),
    }


def validate_toy_score_claim(claim: Any) -> dict[str, Any]:
    data = _as_mapping(claim)
    if _text(data.get("claim_kind")) in {"official_arc_performance", "official_local_percentage"}:
        raise ValueError("Toy harness output cannot be claimed as official ARC performance")
    if data.get("official_arc_performance") is True:
        raise ValueError("Toy harness output cannot be claimed as official ARC performance")
    validate_result_claim(
        {
            "claim_kind": _text(data.get("claim_kind")) or "synthetic_score",
            "evidence_kind": "synthetic",
            "synthetic_score": data.get("aggregate_toy_percentage"),
            "official_run_proof": False,
            "local_public_run_proof": False,
            "official_arc_performance": False,
            "official_percentage": data.get("official_percentage"),
        }
    )
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
    "validate_toy_end_to_end_harness_boundary_record",
    "run_toy_official_format_harness",
    "validate_toy_official_format_harness_result",
    "validate_toy_score_claim",
]
