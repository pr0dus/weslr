"""Metadata-only helpers for the WESLR internal evaluation rehearsal runner v1.

This module is intentionally pure, deterministic, and fail-closed. It consumes
validated internal evaluation dataset registry metadata, builds metadata-only
run plans, normalizes qualitative outcomes, maps failures to capability gaps,
and assembles internal review packets.

It does not execute benchmarks, download datasets, inspect hidden/private/
semi-private benchmark material, call providers/models/search/advisors, wire
runtime/chat/live/public/voice behavior, write dot-weslr state, or grant any
official claim or authority.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping

from weslr.internal_evaluation_dataset_registry import (
    ANSWER_KEY_POLICY_LABELS_V1,
    BLOCKED_USE_LABELS_V1,
    CONTAMINATION_RISK_LABELS_V1,
    EXPECTED_OUTPUT_POLICY_LABELS_V1,
    EXPOSURE_LEVEL_LABELS_V1,
    LICENSE_STATUS_LABELS_V1,
    SAFE_RECOMMENDED_NEXT_LANES_V1,
    SOURCE_TYPE_LABELS_V1,
    SOURCE_REVIEW_STATUS_LABELS_V1,
    TEST_FAMILY_LABELS_V1,
    UNKNOWN_ENGINE_ALLOWED_ROLES_V1,
    UNKNOWN_ENGINE_FORBIDDEN_ROLES_V1,
    validate_internal_evaluation_dataset_registry_batch_v1,
    validate_internal_evaluation_dataset_registry_record_v1,
)

RUNNER_VERSION_V1 = "v1"
RUNNER_SCHEMA_VERSION_V1 = "internal_evaluation_rehearsal_runner_schema_v1"

RUN_PHASE_LABELS_V1 = {
    "phase_0_preflight",
    "phase_1_run_plan_construction",
    "phase_2_controlled_internal_execution",
    "phase_3_outcome_normalization",
    "phase_4_gap_mapping",
    "phase_5_review_packet_and_next_lane_recommendation",
}

RESULT_LABELS_V1 = {
    "pass_internal_rehearsal",
    "partial_internal_rehearsal",
    "fail_internal_rehearsal",
    "blocked_by_registry",
    "blocked_by_source_governance",
    "blocked_by_contamination",
    "blocked_by_answer_key_policy",
    "blocked_by_private_data",
    "blocked_by_hidden_material",
    "blocked_by_runtime_boundary",
    "blocked_by_official_claim_boundary",
    "needs_operator_review",
    "inconclusive_internal_rehearsal",
}

FAILURE_LABELS_V1 = {
    "abstraction_failure",
    "composition_failure",
    "contextual_application_failure",
    "stale_or_missing_evidence_failure",
    "false_memory_or_continuity_failure",
    "correction_drop_failure",
    "canned_or_generic_response_failure",
    "candidate_ranking_failure",
    "unsafe_envelope_failure",
    "overconfidence_failure",
    "uncertainty_explanation_failure",
    "human_intent_modeling_failure",
    "action_governance_failure",
    "unknown_engine_projection_mismatch",
    "contamination_boundary_failure",
    "answer_key_policy_failure",
    "source_governance_failure",
}

MISSING_CAPABILITY_LABELS_V1 = {
    "missing_abstraction_helper",
    "missing_composition_planner",
    "missing_context_gating",
    "missing_evidence_currentness_tracker",
    "missing_memory_boundary_helper",
    "missing_correction_assimilation_helper",
    "missing_non_canned_response_formation",
    "missing_candidate_rejection_helper",
    "missing_safe_envelope_checker",
    "missing_uncertainty_framing",
    "missing_human_intent_modeling",
    "missing_action_governance_boundary",
    "missing_unknown_engine_projection_comparison",
    "missing_gap_compression_helper",
}

BLOCKED_LABELS_V1 = {
    "blocked_by_registry",
    "blocked_by_source_governance",
    "blocked_by_contamination",
    "blocked_by_answer_key_policy",
    "blocked_by_private_data",
    "blocked_by_hidden_material",
    "blocked_by_runtime_boundary",
    "blocked_by_official_claim_boundary",
    "blocked_by_unknown_source_type",
    "blocked_by_unknown_license_status",
    "blocked_by_unknown_exposure_level",
    "blocked_by_unknown_test_family",
    "blocked_by_unknown_engine_authority",
    "blocked_by_forbidden_next_lane",
}

SAFE_NEXT_LANES_V1 = {
    "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1",
    "RUN_WESLR_INTERNAL_EVALUATION_BASELINE_V1",
    "REVIEW_WESLR_INTERNAL_EVALUATION_BASELINE_RESULT_V1",
    "DESIGN_WESLR_CAPABILITY_GAP_CLOSURE_PLAN_V1",
    "IMPLEMENT_SELECTED_MISSING_HELPERS_OR_REASONING_EXPANSIONS_V1",
    "RERUN_WESLR_INTERNAL_EVALUATION_REHEARSAL_V1",
    "DESIGN_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_V1",
    "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_V1",
}

FORBIDDEN_NEXT_LANE_NAMES_V1 = {
    "DESIGN_POST_LEVEL_7_SAFE_LIVE_RESPONSE_BOUNDARY_V1",
}

FORBIDDEN_NEXT_LANE_PREFIXES_V1 = (
    "LIVE_",
    "RUNTIME_",
    "PUBLIC_",
    "VOICE_",
    "OFFICIAL_",
    "CERTIFIED_",
    "TURING_",
    "BENCHMARK_",
    "SELF_MODIFICATION_",
    "AUTONOMOUS_",
    "LEARNING_PROMOTION_",
)

UNKNOWN_ENGINE_ALLOWED_ROLES_V1 = UNKNOWN_ENGINE_ALLOWED_ROLES_V1
UNKNOWN_ENGINE_FORBIDDEN_ROLES_V1 = UNKNOWN_ENGINE_FORBIDDEN_ROLES_V1

REVIEW_ONLY_PLAN_LABEL_V1 = "needs_operator_review"

_OUTCOME_FORBIDDEN_KEY_NAMES_V1 = {
    "raw_answer",
    "raw_answer_text",
    "raw_response",
    "raw_response_text",
    "final_answer",
    "final_answer_text",
    "provider_output",
    "model_output",
    "search_output",
    "advisor_output",
    "runtime_output",
    "private_content",
    "hidden_prompt",
    "live_dialogue_transcript",
    "answer_key_raw",
    "answer_key_text",
    "answer_draft_text",
}

_FORBIDDEN_VALUE_MARKERS_V1 = {
    "official benchmark": "blocked_by_official_claim_boundary",
    "passed turing": "blocked_by_official_claim_boundary",
    "turing test passed": "blocked_by_official_claim_boundary",
    "certified": "blocked_by_official_claim_boundary",
    "product ready": "blocked_by_official_claim_boundary",
    "private content": "blocked_by_private_data",
    "hidden prompt": "blocked_by_hidden_material",
    "raw answer": "blocked_by_runtime_boundary",
    "final answer": "blocked_by_runtime_boundary",
    "provider output": "blocked_by_runtime_boundary",
    "model output": "blocked_by_runtime_boundary",
    "search output": "blocked_by_runtime_boundary",
    "advisor output": "blocked_by_runtime_boundary",
    "dot_weslr": "blocked_by_runtime_boundary",
}

_FAILURE_TO_MISSING_CAPABILITY_V1 = {
    "abstraction_failure": ["missing_abstraction_helper"],
    "composition_failure": ["missing_composition_planner"],
    "contextual_application_failure": ["missing_context_gating"],
    "stale_or_missing_evidence_failure": ["missing_evidence_currentness_tracker"],
    "false_memory_or_continuity_failure": ["missing_memory_boundary_helper"],
    "correction_drop_failure": ["missing_correction_assimilation_helper"],
    "canned_or_generic_response_failure": ["missing_non_canned_response_formation"],
    "candidate_ranking_failure": ["missing_candidate_rejection_helper"],
    "unsafe_envelope_failure": ["missing_safe_envelope_checker"],
    "overconfidence_failure": ["missing_uncertainty_framing"],
    "uncertainty_explanation_failure": ["missing_uncertainty_framing"],
    "human_intent_modeling_failure": ["missing_human_intent_modeling"],
    "action_governance_failure": ["missing_action_governance_boundary"],
    "unknown_engine_projection_mismatch": ["missing_unknown_engine_projection_comparison"],
    "contamination_boundary_failure": ["missing_gap_compression_helper"],
    "answer_key_policy_failure": ["missing_gap_compression_helper"],
    "source_governance_failure": ["missing_gap_compression_helper"],
}


def _is_missing(value: Any) -> bool:
    return value is None or value == ""


def _ensure_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return [str(value)]


def _dedupe_labels(values: Iterable[Any], *, allowed: set[str] | None = None) -> list[str]:
    labels: list[str] = []
    for item in values:
        label = str(item)
        if allowed is not None and label not in allowed:
            continue
        if label not in labels:
            labels.append(label)
    return labels


def _sort_counter(counter: Counter[str]) -> dict[str, int]:
    return {key: int(counter[key]) for key in sorted(counter)}


def _json_safe_scalar(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, bytes):
        return "[redacted-bytes]"
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe_scalar(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple, set)):
        items = list(value) if not isinstance(value, set) else sorted(value, key=repr)
        return [_json_safe_scalar(item) for item in items]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe_scalar(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe_scalar(vars(value))
    return f"[redacted:{type(value).__name__}]"


def to_internal_evaluation_rehearsal_runner_json_safe_v1(value: Any) -> Any:
    """Convert supported runner structures to JSON-safe plain Python data."""

    return _json_safe_scalar(value)


def _is_forbidden_next_lane(next_lane: str) -> bool:
    if next_lane in FORBIDDEN_NEXT_LANE_NAMES_V1:
        return True
    return any(next_lane.startswith(prefix) for prefix in FORBIDDEN_NEXT_LANE_PREFIXES_V1)


def _is_safe_next_lane(next_lane: str) -> bool:
    return next_lane in SAFE_NEXT_LANES_V1 and not _is_forbidden_next_lane(next_lane)


def _normalize_result_label(label: Any) -> str:
    value = str(label) if label is not None else ""
    if value in RESULT_LABELS_V1:
        return value
    return "inconclusive_internal_rehearsal"


def _normalize_failure_labels(values: Any) -> list[str]:
    return _dedupe_labels(_ensure_list(values), allowed=FAILURE_LABELS_V1)


def _normalize_missing_capability_labels(values: Any) -> list[str]:
    return _dedupe_labels(_ensure_list(values), allowed=MISSING_CAPABILITY_LABELS_V1)


def _normalize_role_labels(values: Any) -> list[str]:
    return _dedupe_labels(_ensure_list(values))


def _collect_marker_hits(value: Any) -> list[str]:
    blob = str(to_internal_evaluation_rehearsal_runner_json_safe_v1(value)).lower()
    hits = []
    for marker, label in _FORBIDDEN_VALUE_MARKERS_V1.items():
        if marker in blob and label not in hits:
            hits.append(label)
    return hits


def _record_safe_summary_from_registry_validation(validation: Mapping[str, Any]) -> dict[str, Any]:
    normalized = validation.get("normalized_record", {}) if isinstance(validation, Mapping) else {}
    classification = normalized.get("source_type", "unknown")
    return {
        "dataset_id": normalized.get("dataset_id", ""),
        "dataset_name": normalized.get("dataset_name", ""),
        "source_family": normalized.get("source_family", ""),
        "source_type": classification,
        "exposure_level": normalized.get("exposure_level", "unknown"),
        "license_status": normalized.get("license_status", "unknown"),
        "source_review_status": normalized.get("source_review_status", "unreviewed"),
        "lineage_source_type": normalized.get("lineage_source_type", ""),
        "lineage_preserved": bool(normalized.get("lineage_preserved", False)),
        "contamination_risk": normalized.get("contamination_risk", "unknown"),
        "answer_key_policy": normalized.get("answer_key_policy", "blocked"),
        "expected_output_policy": normalized.get("expected_output_policy", "metadata_only"),
        "mapped_test_families": _dedupe_labels(normalized.get("mapped_test_families", []), allowed=TEST_FAMILY_LABELS_V1),
        "allowed_use_labels": _dedupe_labels(normalized.get("allowed_use_labels", [])),
        "blocked_use_labels": _dedupe_labels(normalized.get("blocked_use_labels", []), allowed=BLOCKED_LABELS_V1 | {"blocked"}),
        "development_allowed": bool(normalized.get("development_allowed", False)),
        "sealed_internal_eval_allowed": bool(normalized.get("sealed_internal_eval_allowed", False)),
        "synthetic_mutation_allowed": bool(normalized.get("synthetic_mutation_allowed", False)),
        "registry_valid": bool(validation.get("valid", False)),
        "registry_blocked": bool(validation.get("blocked", False)),
        "registry_blocked_labels": _dedupe_labels(validation.get("blocked_labels", [])),
    }


def _summarize_registry_validation_batch(batch: Mapping[str, Any]) -> dict[str, Any]:
    records = batch.get("records", []) if isinstance(batch, Mapping) else []
    summaries = [to_internal_evaluation_rehearsal_runner_json_safe_v1(item.get("normalized_record", {})) for item in records if isinstance(item, Mapping)]
    source_type_counts = Counter(str(item.get("source_type", "unknown")) for item in summaries)
    contamination_counts = Counter(str(item.get("contamination_risk", "unknown")) for item in summaries)
    answer_key_counts = Counter(str(item.get("answer_key_policy", "blocked")) for item in summaries)
    expected_output_counts = Counter(str(item.get("expected_output_policy", "metadata_only")) for item in summaries)
    test_family_counts = Counter(
        family
        for item in summaries
        for family in _ensure_list(item.get("mapped_test_families", []))
    )
    blocked_counts = Counter(
        label
        for item in records
        if isinstance(item, Mapping)
        for label in _ensure_list(item.get("blocked_labels", []))
    )
    return {
        "total_records": int(batch.get("total_records", len(records)) or 0),
        "valid_records": int(batch.get("valid_records", 0) or 0),
        "blocked_records": int(batch.get("blocked_records", 0) or 0),
        "source_type_counts": _sort_counter(source_type_counts),
        "contamination_risk_counts": _sort_counter(contamination_counts),
        "answer_key_policy_counts": _sort_counter(answer_key_counts),
        "expected_output_policy_counts": _sort_counter(expected_output_counts),
        "test_family_counts": _sort_counter(test_family_counts),
        "blocked_label_counts": _sort_counter(blocked_counts),
        "aggregate_blocked_labels": _dedupe_labels(batch.get("aggregate_blocked_labels", []), allowed=BLOCKED_LABELS_V1 | {"blocked", "source_review_required", "missing_required_fields"}),
        "aggregate_contamination_risk": batch.get("aggregate_contamination_risk", "unknown"),
    }


def validate_internal_evaluation_rehearsal_preflight_v1(
    *,
    registry_records: Iterable[Mapping[str, Any]] | None = None,
    run_metadata: Mapping[str, Any] | None = None,
    run_plan: Mapping[str, Any] | None = None,
    registry_batch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Check registry and run metadata before any rehearsal plan is considered safe."""

    metadata = to_internal_evaluation_rehearsal_runner_json_safe_v1(run_metadata or {})
    plan = to_internal_evaluation_rehearsal_runner_json_safe_v1(run_plan or {})
    registry_records_list = list(registry_records or [])

    if registry_batch is None:
        registry_batch = validate_internal_evaluation_dataset_registry_batch_v1(registry_records_list)
    registry_batch_safe = to_internal_evaluation_rehearsal_runner_json_safe_v1(registry_batch)

    blocked_labels: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(registry_batch_safe, Mapping):
        blocked_labels.append("blocked_by_registry")
        errors.append("registry_batch_not_mapping")
        registry_batch_safe = {}

    if registry_batch_safe.get("blocked_records", 0):
        blocked_labels.append("blocked_by_registry")
        errors.append("blocked_registry_records_present")

    if registry_batch_safe.get("valid") is False:
        blocked_labels.append("blocked_by_registry")
        errors.append("registry_batch_invalid")

    registry_records_safe = registry_batch_safe.get("records", []) if isinstance(registry_batch_safe, Mapping) else []
    for record in registry_records_safe:
        if not isinstance(record, Mapping):
            blocked_labels.append("blocked_by_registry")
            errors.append("registry_record_not_mapping")
            continue
        normalized = record.get("normalized_record", {})
        if not record.get("valid", False):
            blocked_labels.append("blocked_by_registry")
        if record.get("blocked", False):
            blocked_labels.extend(_ensure_list(record.get("blocked_labels", [])))
        if normalized.get("source_type") in {"semi_private", "private", "hidden_blocked", "unknown_license_blocked_until_reviewed", "raw_private_user_data_blocked", "generated_mutation_from_blocked_source_blocked"}:
            blocked_labels.append("blocked_by_source_governance")
        if normalized.get("contamination_risk") in {"high", "extreme", "unknown"}:
            if normalized.get("source_type") != "synthetic_weslr_created":
                blocked_labels.append("blocked_by_contamination")
        if normalized.get("answer_key_policy") == "blocked" and normalized.get("source_type") != "synthetic_weslr_created":
            blocked_labels.append("blocked_by_answer_key_policy")
        if bool(normalized.get("raw_private_data_allowed", False)):
            blocked_labels.append("blocked_by_private_data")
        if bool(normalized.get("hidden_material_allowed", False)):
            blocked_labels.append("blocked_by_hidden_material")
        if bool(normalized.get("official_claim_allowed", False)) or bool(normalized.get("public_claim_allowed", False)):
            blocked_labels.append("blocked_by_official_claim_boundary")

    for flag in (
        "official_claim_allowed",
        "public_claim_allowed",
        "runtime_authority_allowed",
        "voice_authority_allowed",
        "answer_authority_granted",
        "composition_authority_granted",
    ):
        if bool(metadata.get(flag, False)):
            blocked_labels.append("blocked_by_official_claim_boundary" if "claim" in flag else "blocked_by_runtime_boundary")
            errors.append(f"forbidden_flag_true:{flag}")

    for flag in ("runtime_authority_allowed", "voice_authority_allowed"):
        if bool(plan.get(flag, False)):
            blocked_labels.append("blocked_by_runtime_boundary")
            errors.append(f"forbidden_plan_flag_true:{flag}")

    unknown_engine_roles = _dedupe_labels(
        metadata.get("unknown_engine_role", []) or plan.get("unknown_engine_role", []),
        allowed=UNKNOWN_ENGINE_ALLOWED_ROLES_V1 | UNKNOWN_ENGINE_FORBIDDEN_ROLES_V1,
    )
    if any(role in UNKNOWN_ENGINE_FORBIDDEN_ROLES_V1 for role in unknown_engine_roles):
        blocked_labels.append("blocked_by_unknown_engine_authority")
        errors.append("unknown_engine_forbidden_role_present")
    if any(role not in UNKNOWN_ENGINE_ALLOWED_ROLES_V1 for role in unknown_engine_roles):
        if unknown_engine_roles:
            blocked_labels.append("blocked_by_unknown_engine_authority")
            errors.append("unknown_engine_role_not_allowed")

    next_lane = str(metadata.get("next_lane") or plan.get("next_lane") or plan.get("recommended_next_lane") or "")
    if next_lane:
        if _is_forbidden_next_lane(next_lane):
            blocked_labels.append("blocked_by_forbidden_next_lane")
            errors.append("forbidden_next_lane")
        elif not _is_safe_next_lane(next_lane):
            warnings.append("unrecognized_next_lane")
            errors.append("unrecognized_next_lane")

    if bool(metadata.get("review_only", False)) or bool(plan.get("review_only", False)):
        warnings.append("review_only_plan")

    blocked_labels = _dedupe_labels(blocked_labels, allowed=BLOCKED_LABELS_V1 | {"blocked", "blocked_by_unknown_engine_authority"})
    status_label = "needs_operator_review" if not errors and not blocked_labels else _choose_blocked_result_label(blocked_labels)

    return {
        "valid": not errors and not blocked_labels,
        "blocked": bool(blocked_labels or errors),
        "blocked_labels": blocked_labels,
        "errors": _dedupe_labels(errors),
        "warnings": _dedupe_labels(warnings),
        "status_label": status_label,
        "registry_batch": registry_batch_safe,
        "run_metadata": metadata,
        "run_plan": plan,
        "operator_approval_required": True,
        "unknown_engine_authority_allowed": False,
        "official_claim_allowed": False,
        "public_claim_allowed": False,
        "runtime_authority_allowed": False,
        "voice_authority_allowed": False,
        "next_lane_safe": bool(next_lane and _is_safe_next_lane(next_lane)),
        "next_lane_forbidden": bool(next_lane and _is_forbidden_next_lane(next_lane)),
    }


def _choose_blocked_result_label(blocked_labels: Iterable[str]) -> str:
    labels = _dedupe_labels(blocked_labels)
    for candidate in (
        "blocked_by_registry",
        "blocked_by_source_governance",
        "blocked_by_contamination",
        "blocked_by_answer_key_policy",
        "blocked_by_private_data",
        "blocked_by_hidden_material",
        "blocked_by_runtime_boundary",
        "blocked_by_official_claim_boundary",
        "blocked_by_unknown_engine_authority",
        "blocked_by_forbidden_next_lane",
        "needs_operator_review",
    ):
        if candidate in labels:
            return candidate
    return "needs_operator_review"


def build_internal_evaluation_rehearsal_run_plan_v1(
    registry_records: Iterable[Mapping[str, Any]],
    *,
    run_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a metadata-only run plan from validated registry metadata."""

    metadata = to_internal_evaluation_rehearsal_runner_json_safe_v1(run_metadata or {})
    registry_records_list = list(registry_records)
    registry_batch = validate_internal_evaluation_dataset_registry_batch_v1(registry_records_list)
    registry_batch_safe = to_internal_evaluation_rehearsal_runner_json_safe_v1(registry_batch)
    review_only = bool(metadata.get("review_only", False) or metadata.get("plan_review_only", False))

    preflight = validate_internal_evaluation_rehearsal_preflight_v1(
        registry_records=registry_records_list,
        run_metadata=metadata,
        registry_batch=registry_batch_safe,
    )

    planned_records: list[dict[str, Any]] = []
    blocked_records: list[dict[str, Any]] = []
    source_type_counts = Counter()
    contamination_counts = Counter()
    answer_key_counts = Counter()
    expected_output_counts = Counter()
    test_family_counts = Counter()
    lineage_counts = Counter()
    blocked_labels: list[str] = _dedupe_labels(preflight.get("blocked_labels", []), allowed=BLOCKED_LABELS_V1 | {"blocked_by_unknown_engine_authority"})

    for record in registry_batch_safe.get("records", []):
        if not isinstance(record, Mapping):
            continue
        normalized = to_internal_evaluation_rehearsal_runner_json_safe_v1(record.get("normalized_record", {}))
        safe_summary = _record_safe_summary_from_registry_validation(record)
        source_type_counts[str(safe_summary.get("source_type", "unknown"))] += 1
        contamination_counts[str(safe_summary.get("contamination_risk", "unknown"))] += 1
        answer_key_counts[str(safe_summary.get("answer_key_policy", "blocked"))] += 1
        expected_output_counts[str(safe_summary.get("expected_output_policy", "metadata_only"))] += 1
        lineage_counts[str(safe_summary.get("lineage_source_type", "")) or "unknown"] += 1
        for family in _ensure_list(safe_summary.get("mapped_test_families", [])):
            test_family_counts[family] += 1
        if record.get("blocked", False) or not record.get("valid", False):
            blocked_records.append(safe_summary)
        else:
            planned_records.append(safe_summary)

    selected_test_families = _dedupe_labels(
        [family for item in planned_records for family in _ensure_list(item.get("mapped_test_families", []))],
        allowed=TEST_FAMILY_LABELS_V1,
    )
    all_test_families = _dedupe_labels(
        [family for item in registry_batch_safe.get("records", []) if isinstance(item, Mapping) for family in _ensure_list(item.get("normalized_record", {}).get("mapped_test_families", []))],
        allowed=TEST_FAMILY_LABELS_V1,
    )

    blocked_by_plan = bool(blocked_records and not review_only)
    if blocked_by_plan:
        blocked_labels.append("blocked_by_registry")
    if bool(preflight.get("blocked", False)):
        blocked_labels.extend(_ensure_list(preflight.get("blocked_labels", [])))

    if blocked_by_plan:
        result_label = "blocked_by_registry"
    elif blocked_labels:
        result_label = _choose_blocked_result_label(blocked_labels)
    else:
        result_label = "needs_operator_review"

    run_plan = {
        "runner_version": RUNNER_VERSION_V1,
        "schema_version": RUNNER_SCHEMA_VERSION_V1,
        "run_id": str(metadata.get("run_id", "")),
        "run_purpose": str(metadata.get("run_purpose", "internal_evaluation_rehearsal")),
        "run_scope": str(metadata.get("run_scope", "metadata_only_internal_rehearsal")),
        "run_phase_label": "phase_1_run_plan_construction",
        "review_only": review_only,
        "operator_approval_required": True,
        "execution_allowed": False,
        "registry_validation": registry_batch_safe,
        "registry_validation_summary": _summarize_registry_validation_batch(registry_batch_safe),
        "registry_records": [
            _record_safe_summary_from_registry_validation(record)
            for record in registry_batch_safe.get("records", [])
            if isinstance(record, Mapping)
        ],
        "preflight": preflight,
        "planned_records": planned_records,
        "blocked_records": blocked_records,
        "record_count": int(registry_batch_safe.get("total_records", 0) or 0),
        "planned_record_count": len(planned_records),
        "blocked_record_count": len(blocked_records),
        "selected_test_families": selected_test_families,
        "all_test_families": all_test_families,
        "source_type_summary": _sort_counter(source_type_counts),
        "contamination_summary": _sort_counter(contamination_counts),
        "answer_key_policy_summary": _sort_counter(answer_key_counts),
        "expected_output_policy_summary": _sort_counter(expected_output_counts),
        "lineage_summary": _sort_counter(lineage_counts),
        "allowed_use_label_summary": _sort_counter(Counter(label for item in planned_records for label in _ensure_list(item.get("allowed_use_labels", [])))),
        "blocked_use_label_summary": _sort_counter(Counter(label for item in registry_batch_safe.get("records", []) if isinstance(item, Mapping) for label in _ensure_list(item.get("blocked_labels", [])))),
        "blocked_labels": _dedupe_labels(blocked_labels),
        "status_label": result_label,
        "result_label": result_label,
        "safe_next_lanes": sorted(_dedupe_labels(SAFE_NEXT_LANES_V1, allowed=SAFE_NEXT_LANES_V1)),
        "forbidden_next_lanes": sorted(_dedupe_labels(FORBIDDEN_NEXT_LANE_NAMES_V1)),
        "next_lane": str(metadata.get("next_lane", "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1")),
        "recommended_next_lanes": [
            "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1",
            "RUN_WESLR_INTERNAL_EVALUATION_BASELINE_V1",
            "DESIGN_WESLR_CAPABILITY_GAP_CLOSURE_PLAN_V1",
        ],
        "notes_redacted": str(metadata.get("notes_redacted", "")),
        "run_metadata": metadata,
        "run_phase_labels": ["phase_0_preflight", "phase_1_run_plan_construction"],
    }

    run_plan["preflight"]["status_label"] = preflight.get("status_label", run_plan["status_label"])
    return to_internal_evaluation_rehearsal_runner_json_safe_v1(run_plan)


def normalize_internal_evaluation_rehearsal_outcome_v1(outcome: Mapping[str, Any] | str) -> dict[str, Any]:
    """Normalize a metadata-only rehearsal outcome and reject raw answer content."""

    if isinstance(outcome, str):
        return {
            "valid": outcome in RESULT_LABELS_V1,
            "blocked": False,
            "blocked_labels": [],
            "warnings": [],
            "errors": [] if outcome in RESULT_LABELS_V1 else ["unknown_result_label"],
            "result_label": _normalize_result_label(outcome),
            "failure_labels": [],
            "missing_capability_labels": [],
            "predicted_failure_labels": [],
            "observed_failure_labels": [],
            "result_phase_label": "phase_3_outcome_normalization",
            "raw_answer_present": False,
            "official_score": None,
            "notes_redacted": "",
        }

    if not isinstance(outcome, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "blocked_labels": ["blocked_by_registry"],
            "warnings": [],
            "errors": ["outcome_not_mapping"],
            "result_label": "inconclusive_internal_rehearsal",
            "failure_labels": [],
            "missing_capability_labels": [],
            "predicted_failure_labels": [],
            "observed_failure_labels": [],
            "result_phase_label": "phase_3_outcome_normalization",
            "raw_answer_present": False,
            "official_score": None,
            "notes_redacted": "",
        }

    safe_outcome = to_internal_evaluation_rehearsal_runner_json_safe_v1(outcome)
    blocked_labels: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []

    for key, value in safe_outcome.items():
        if key in _OUTCOME_FORBIDDEN_KEY_NAMES_V1:
            blocked_labels.append("blocked_by_runtime_boundary")
            errors.append(f"forbidden_outcome_key:{key}")
        if key in {"official_score", "public_score", "benchmark_score"} and value not in (None, ""):
            blocked_labels.append("blocked_by_official_claim_boundary")
            errors.append(f"forbidden_score_field:{key}")

    blocked_labels.extend(_collect_marker_hits(safe_outcome))

    result_label = _normalize_result_label(safe_outcome.get("result_label", safe_outcome.get("status_label", "")))
    if result_label not in RESULT_LABELS_V1:
        blocked_labels.append("blocked_by_registry")
        errors.append("unknown_result_label")

    failure_labels = _normalize_failure_labels(safe_outcome.get("failure_labels", []))
    missing_capability_labels = _normalize_missing_capability_labels(safe_outcome.get("missing_capability_labels", []))
    predicted_failure_labels = _normalize_failure_labels(safe_outcome.get("predicted_failure_labels", []))
    observed_failure_labels = _normalize_failure_labels(safe_outcome.get("observed_failure_labels", failure_labels))
    test_family_labels = _dedupe_labels(
        _ensure_list(safe_outcome.get("test_family_labels", [])),
        allowed=TEST_FAMILY_LABELS_V1,
    )

    if safe_outcome.get("official_score") not in (None, ""):
        blocked_labels.append("blocked_by_official_claim_boundary")
        errors.append("official_score_present")

    if any(label not in FAILURE_LABELS_V1 for label in failure_labels):
        blocked_labels.append("blocked_by_registry")
        errors.append("unknown_failure_label")
    if any(label not in MISSING_CAPABILITY_LABELS_V1 for label in missing_capability_labels):
        blocked_labels.append("blocked_by_registry")
        errors.append("unknown_missing_capability_label")

    if any(label in {"blocked_by_private_data", "blocked_by_hidden_material"} for label in blocked_labels):
        result_label = "blocked_by_private_data" if "blocked_by_private_data" in blocked_labels else "blocked_by_hidden_material"
    elif "blocked_by_official_claim_boundary" in blocked_labels:
        result_label = "blocked_by_official_claim_boundary"
    elif "blocked_by_runtime_boundary" in blocked_labels:
        result_label = "blocked_by_runtime_boundary"
    elif "blocked_by_registry" in blocked_labels:
        result_label = "blocked_by_registry"
    elif blocked_labels:
        result_label = _choose_blocked_result_label(blocked_labels)
    elif failure_labels and result_label == "pass_internal_rehearsal":
        result_label = "partial_internal_rehearsal"

    normalized = {
        "runner_version": str(safe_outcome.get("runner_version", RUNNER_VERSION_V1)),
        "run_id": str(safe_outcome.get("run_id", "")),
        "run_phase_label": "phase_3_outcome_normalization",
        "result_label": result_label,
        "failure_labels": failure_labels,
        "missing_capability_labels": missing_capability_labels,
        "predicted_failure_labels": predicted_failure_labels,
        "observed_failure_labels": observed_failure_labels,
        "test_family_labels": test_family_labels,
        "source_type": str(safe_outcome.get("source_type", "unknown")),
        "contamination_risk": str(safe_outcome.get("contamination_risk", "unknown")),
        "answer_key_policy": str(safe_outcome.get("answer_key_policy", "blocked")),
        "expected_output_policy": str(safe_outcome.get("expected_output_policy", "metadata_only")),
        "notes_redacted": str(safe_outcome.get("notes_redacted", "")),
        "blocked_labels": _dedupe_labels(blocked_labels, allowed=BLOCKED_LABELS_V1 | {"blocked_by_private_data", "blocked_by_hidden_material", "blocked_by_runtime_boundary", "blocked_by_official_claim_boundary", "blocked_by_registry", "blocked_by_unknown_engine_authority"}),
        "warnings": _dedupe_labels(warnings),
        "errors": _dedupe_labels(errors),
        "valid": not errors and not blocked_labels,
        "blocked": bool(blocked_labels),
        "raw_answer_present": False,
        "official_score": None,
        "public_score": None,
        "result_phase_label": "phase_3_outcome_normalization",
        "operator_approval_required": True,
        "unknown_engine_authority_allowed": False,
        "official_claim_allowed": False,
        "public_claim_allowed": False,
        "runtime_authority_allowed": False,
        "voice_authority_allowed": False,
    }
    return to_internal_evaluation_rehearsal_runner_json_safe_v1(normalized)


def map_internal_evaluation_rehearsal_gaps_v1(
    outcomes: Iterable[Mapping[str, Any] | str],
) -> dict[str, Any]:
    """Aggregate rehearsal failures into missing-capability metadata."""

    normalized_outcomes = [normalize_internal_evaluation_rehearsal_outcome_v1(outcome) for outcome in outcomes]
    failure_counts = Counter(label for outcome in normalized_outcomes for label in outcome.get("failure_labels", []))
    missing_counts = Counter(label for outcome in normalized_outcomes for label in outcome.get("missing_capability_labels", []))
    predicted_counts = Counter(label for outcome in normalized_outcomes for label in outcome.get("predicted_failure_labels", []))
    observed_counts = Counter(label for outcome in normalized_outcomes for label in outcome.get("observed_failure_labels", []))

    mapped_missing = Counter()
    repeated_failure_patterns = Counter()
    comparison_labels: list[str] = []

    for outcome in normalized_outcomes:
        failure_key = tuple(outcome.get("failure_labels", []))
        if failure_key:
            repeated_failure_patterns["|".join(failure_key)] += 1
        for failure in outcome.get("failure_labels", []):
            for capability in _FAILURE_TO_MISSING_CAPABILITY_V1.get(failure, []):
                mapped_missing[capability] += 1
        predicted = set(outcome.get("predicted_failure_labels", []))
        observed = set(outcome.get("observed_failure_labels", []))
        if predicted or observed:
            if predicted == observed:
                comparison_labels.append("predicted_matches_observed")
            else:
                comparison_labels.append("predicted_differs_from_observed")
                if predicted - observed:
                    comparison_labels.append("predicted_overpredicted")
                if observed - predicted:
                    comparison_labels.append("predicted_underpredicted")

    for label, count in missing_counts.items():
        mapped_missing[label] += count

    return {
        "total_outcomes": len(normalized_outcomes),
        "result_label_counts": _sort_counter(Counter(outcome.get("result_label", "inconclusive_internal_rehearsal") for outcome in normalized_outcomes)),
        "failure_label_counts": _sort_counter(failure_counts),
        "missing_capability_counts": _sort_counter(mapped_missing),
        "predicted_failure_label_counts": _sort_counter(predicted_counts),
        "observed_failure_label_counts": _sort_counter(observed_counts),
        "predicted_vs_observed_labels": _dedupe_labels(comparison_labels),
        "predicted_vs_observed_summary": {
            "predicted_match_count": comparison_labels.count("predicted_matches_observed"),
            "predicted_mismatch_count": comparison_labels.count("predicted_differs_from_observed"),
            "predicted_overpredicted_count": comparison_labels.count("predicted_overpredicted"),
            "predicted_underpredicted_count": comparison_labels.count("predicted_underpredicted"),
        },
        "repeated_failure_patterns": dict(sorted(repeated_failure_patterns.items())),
        "unknown_engine_boundary_summary": {
            "allowed_roles": sorted(UNKNOWN_ENGINE_ALLOWED_ROLES_V1),
            "forbidden_roles": sorted(UNKNOWN_ENGINE_FORBIDDEN_ROLES_V1),
            "comparison_labels": _dedupe_labels(comparison_labels),
        },
        "gap_labels": _dedupe_labels(list(mapped_missing.keys())),
        "missing_capability_labels": _dedupe_labels(list(mapped_missing.keys())),
        "phase_label": "phase_4_gap_mapping",
    }


def build_internal_evaluation_gap_report_v1(
    *,
    run_plan: Mapping[str, Any] | None = None,
    outcomes: Iterable[Mapping[str, Any] | str] | None = None,
    run_metadata: Mapping[str, Any] | None = None,
    notes_redacted: str = "",
) -> dict[str, Any]:
    """Build a metadata-only internal rehearsal gap report."""

    plan = to_internal_evaluation_rehearsal_runner_json_safe_v1(run_plan or {})
    metadata = to_internal_evaluation_rehearsal_runner_json_safe_v1(run_metadata or {})
    normalized_outcomes = [normalize_internal_evaluation_rehearsal_outcome_v1(outcome) for outcome in (outcomes or [])]
    gap_mapping = map_internal_evaluation_rehearsal_gaps_v1(normalized_outcomes)

    result_counts = Counter(outcome.get("result_label", "inconclusive_internal_rehearsal") for outcome in normalized_outcomes)
    failure_counts = Counter(label for outcome in normalized_outcomes for label in outcome.get("failure_labels", []))
    missing_counts = Counter(label for outcome in normalized_outcomes for label in outcome.get("missing_capability_labels", []))

    planned_records = plan.get("planned_records", []) if isinstance(plan.get("planned_records", []), list) else []
    contamination_summary = Counter(str(item.get("contamination_risk", "unknown")) for item in planned_records if isinstance(item, Mapping))
    source_summary = Counter(str(item.get("source_type", "unknown")) for item in planned_records if isinstance(item, Mapping))
    answer_key_summary = Counter(str(item.get("answer_key_policy", "blocked")) for item in planned_records if isinstance(item, Mapping))

    planned_record_count = int(plan.get("planned_record_count", len(_ensure_list(plan.get("planned_records", [])))) or 0)
    blocked_record_count = int(plan.get("blocked_record_count", len(_ensure_list(plan.get("blocked_records", [])))) or 0)
    completed_count = sum(1 for outcome in normalized_outcomes if outcome.get("result_label") not in {"blocked_by_registry", "blocked_by_source_governance", "blocked_by_contamination", "blocked_by_answer_key_policy", "blocked_by_private_data", "blocked_by_hidden_material", "blocked_by_runtime_boundary", "blocked_by_official_claim_boundary"})

    repeated_failure_patterns = gap_mapping.get("repeated_failure_patterns", {})
    recommended_gap_closure_lanes = _dedupe_labels(
        [
            "DESIGN_WESLR_CAPABILITY_GAP_CLOSURE_PLAN_V1",
            "IMPLEMENT_SELECTED_MISSING_HELPERS_OR_REASONING_EXPANSIONS_V1",
            "RERUN_WESLR_INTERNAL_EVALUATION_REHEARSAL_V1",
            "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1",
        ],
        allowed=SAFE_NEXT_LANES_V1,
    )

    summary_status = (
        "pass_internal_rehearsal"
        if not result_counts and planned_record_count == 0
        else "needs_operator_review"
        if failure_counts or blocked_record_count or blocked_record_count > completed_count
        else "partial_internal_rehearsal"
        if result_counts.get("partial_internal_rehearsal", 0)
        else "pass_internal_rehearsal"
    )

    report = {
        "report_version": RUNNER_VERSION_V1,
        "runner_version": RUNNER_VERSION_V1,
        "schema_version": RUNNER_SCHEMA_VERSION_V1,
        "run_id": str(metadata.get("run_id", plan.get("run_id", ""))),
        "summary_status": summary_status,
        "total_records_considered": int(plan.get("record_count", planned_record_count + blocked_record_count) or 0),
        "total_records_blocked": blocked_record_count,
        "total_tasks_planned": planned_record_count,
        "total_tasks_completed": completed_count,
        "result_label_counts": _sort_counter(result_counts),
        "failure_label_counts": _sort_counter(failure_counts),
        "missing_capability_counts": _sort_counter(missing_counts or Counter(gap_mapping.get("missing_capability_counts", {}))),
        "contamination_risk_summary": _sort_counter(contamination_summary),
        "source_governance_summary": _sort_counter(source_summary),
        "answer_key_policy_summary": _sort_counter(answer_key_summary),
        "unknown_engine_projection_summary": {
            "allowed_roles": sorted(UNKNOWN_ENGINE_ALLOWED_ROLES_V1),
            "forbidden_roles": sorted(UNKNOWN_ENGINE_FORBIDDEN_ROLES_V1),
            "predicted_vs_observed_labels": gap_mapping.get("predicted_vs_observed_labels", []),
            "predicted_vs_observed_summary": gap_mapping.get("predicted_vs_observed_summary", {}),
        },
        "repeated_failure_patterns": repeated_failure_patterns,
        "recommended_gap_closure_lanes": recommended_gap_closure_lanes,
        "blocked_public_claims": ["official benchmark result", "certified intelligence claim", "Turing-test passing claim", "IQ/intelligence claim"],
        "blocked_live_or_voice_lanes": [
            "DESIGN_POST_LEVEL_7_SAFE_LIVE_RESPONSE_BOUNDARY_V1",
            "LIVE_",
            "RUNTIME_",
            "PUBLIC_",
            "VOICE_",
        ],
        "operator_review_required": True,
        "notes_redacted": str(notes_redacted or metadata.get("notes_redacted", "")),
        "gap_labels": gap_mapping.get("gap_labels", []),
        "missing_capability_labels": gap_mapping.get("missing_capability_labels", []),
        "phase_label": "phase_4_gap_mapping",
        "run_phase_labels": ["phase_3_outcome_normalization", "phase_4_gap_mapping", "phase_5_review_packet_and_next_lane_recommendation"],
        "operator_next_lane": "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1",
    }
    return to_internal_evaluation_rehearsal_runner_json_safe_v1(report)


def build_internal_evaluation_rehearsal_review_packet_v1(
    *,
    registry_status: Mapping[str, Any] | None = None,
    preflight_status: Mapping[str, Any] | None = None,
    run_plan: Mapping[str, Any] | None = None,
    gap_report: Mapping[str, Any] | None = None,
    unknown_engine_boundary_summary: Mapping[str, Any] | None = None,
    blocked_next_lanes: Iterable[str] | None = None,
    recommended_next_lanes: Iterable[str] | None = None,
    notes_redacted: str = "",
) -> dict[str, Any]:
    """Build an operator review packet with clear section boundaries."""

    packet = {
        "packet_version": RUNNER_VERSION_V1,
        "runner_version": RUNNER_VERSION_V1,
        "schema_version": RUNNER_SCHEMA_VERSION_V1,
        "operator_sections": [
            "registry_status",
            "preflight_status",
            "run_plan_summary",
            "gap_report_summary",
            "unknown_engine_boundary_summary",
            "blocked_lanes",
            "recommended_next_lanes",
        ],
        "registry_status": to_internal_evaluation_rehearsal_runner_json_safe_v1(registry_status or {}),
        "preflight_status": to_internal_evaluation_rehearsal_runner_json_safe_v1(preflight_status or {}),
        "run_plan_summary": summarize_internal_evaluation_rehearsal_runner_v1(run_plan or {}),
        "gap_report_summary": summarize_internal_evaluation_rehearsal_runner_v1(gap_report or {}),
        "unknown_engine_boundary_summary": to_internal_evaluation_rehearsal_runner_json_safe_v1(
            unknown_engine_boundary_summary or {
                "allowed_roles": sorted(UNKNOWN_ENGINE_ALLOWED_ROLES_V1),
                "forbidden_roles": sorted(UNKNOWN_ENGINE_FORBIDDEN_ROLES_V1),
                "authority_allowed": False,
            }
        ),
        "blocked_lanes": _dedupe_labels(blocked_next_lanes or [], allowed=FORBIDDEN_NEXT_LANE_NAMES_V1 | set(FORBIDDEN_NEXT_LANE_PREFIXES_V1)),
        "recommended_next_lanes": _dedupe_labels(recommended_next_lanes or [], allowed=SAFE_NEXT_LANES_V1),
        "notes_redacted": str(notes_redacted),
        "operator_review_required": True,
        "public_claim_allowed": False,
        "official_claim_allowed": False,
        "runtime_authority_allowed": False,
        "voice_authority_allowed": False,
        "unknown_engine_authority_allowed": False,
        "final_answer_allowed": False,
        "composition_authority_allowed": False,
    }
    return to_internal_evaluation_rehearsal_runner_json_safe_v1(packet)


def _validate_batch_item(item: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(item, Mapping):
        return {
            "item_type": "invalid",
            "valid": False,
            "blocked": True,
            "blocked_labels": ["blocked_by_registry"],
            "errors": ["item_not_mapping"],
            "warnings": [],
            "normalized_item": to_internal_evaluation_rehearsal_runner_json_safe_v1(item),
        }

    if any(key in item for key in ("planned_records", "registry_validation", "preflight", "status_label", "run_phase_label")):
        plan = to_internal_evaluation_rehearsal_runner_json_safe_v1(item)
        blocked_labels: list[str] = []
        errors: list[str] = []
        warnings: list[str] = []
        if plan.get("execution_allowed") is True:
            blocked_labels.append("blocked_by_runtime_boundary")
            errors.append("execution_allowed_true")
        if bool(plan.get("official_claim_allowed", False)) or bool(plan.get("public_claim_allowed", False)):
            blocked_labels.append("blocked_by_official_claim_boundary")
            errors.append("claim_flag_true")
        if bool(plan.get("runtime_authority_allowed", False)) or bool(plan.get("voice_authority_allowed", False)):
            blocked_labels.append("blocked_by_runtime_boundary")
            errors.append("runtime_or_voice_authority_true")
        next_lane = str(plan.get("next_lane", ""))
        if next_lane and _is_forbidden_next_lane(next_lane):
            blocked_labels.append("blocked_by_forbidden_next_lane")
            errors.append("forbidden_next_lane")
        registry_validation = plan.get("registry_validation", {}) if isinstance(plan.get("registry_validation", {}), Mapping) else {}
        if registry_validation and bool(registry_validation.get("blocked_records", 0)):
            blocked_labels.append("blocked_by_registry")
        if registry_validation and registry_validation.get("valid") is False:
            blocked_labels.append("blocked_by_registry")
        preflight = plan.get("preflight", {}) if isinstance(plan.get("preflight", {}), Mapping) else {}
        if preflight and preflight.get("blocked", False):
            blocked_labels.extend(_ensure_list(preflight.get("blocked_labels", [])))
            errors.extend(_ensure_list(preflight.get("errors", [])))
            warnings.extend(_ensure_list(preflight.get("warnings", [])))
        if plan.get("status_label") not in RESULT_LABELS_V1:
            blocked_labels.append("blocked_by_registry")
            errors.append("unknown_plan_status_label")
        return {
            "item_type": "run_plan",
            "valid": not errors and not blocked_labels,
            "blocked": bool(blocked_labels),
            "blocked_labels": _dedupe_labels(blocked_labels, allowed=BLOCKED_LABELS_V1 | {"blocked_by_unknown_engine_authority"}),
            "errors": _dedupe_labels(errors),
            "warnings": _dedupe_labels(warnings),
            "normalized_item": plan,
        }

    if any(key in item for key in ("result_label", "failure_labels", "predicted_failure_labels", "observed_failure_labels", "official_score")):
        outcome = normalize_internal_evaluation_rehearsal_outcome_v1(item)
        return {
            "item_type": "outcome",
            "valid": bool(outcome.get("valid", False)),
            "blocked": bool(outcome.get("blocked", False)),
            "blocked_labels": _dedupe_labels(outcome.get("blocked_labels", [])),
            "errors": _dedupe_labels(outcome.get("errors", [])),
            "warnings": _dedupe_labels(outcome.get("warnings", [])),
            "normalized_item": outcome,
        }

    validation = validate_internal_evaluation_dataset_registry_record_v1(item)
    return {
        "item_type": "registry_record",
        "valid": bool(validation.get("valid", False)),
        "blocked": bool(validation.get("blocked", False)),
        "blocked_labels": _dedupe_labels(validation.get("blocked_labels", [])),
        "errors": _dedupe_labels(validation.get("errors", [])),
        "warnings": _dedupe_labels(validation.get("warnings", [])),
        "normalized_item": _record_safe_summary_from_registry_validation(validation),
    }


def validate_internal_evaluation_rehearsal_batch_v1(records_or_plans: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate and normalize multiple rehearsal records or plans."""

    results = [_validate_batch_item(item) for item in records_or_plans]
    blocked_labels = _dedupe_labels(
        [label for result in results for label in _ensure_list(result.get("blocked_labels", []))],
        allowed=BLOCKED_LABELS_V1 | {"blocked_by_unknown_engine_authority"},
    )
    return {
        "runner_version": RUNNER_VERSION_V1,
        "schema_version": RUNNER_SCHEMA_VERSION_V1,
        "valid": not any(result.get("blocked", False) or not result.get("valid", False) for result in results),
        "total_records": len(results),
        "valid_records": sum(1 for result in results if result.get("valid", False) and not result.get("blocked", False)),
        "blocked_records": sum(1 for result in results if result.get("blocked", False)),
        "aggregate_blocked_labels": blocked_labels,
        "records": results,
        "operator_approval_required": True,
        "phase_label": "phase_0_preflight",
    }


def summarize_internal_evaluation_rehearsal_runner_v1(value: Mapping[str, Any] | Iterable[Any]) -> dict[str, Any]:
    """Summarize runner plans, outcomes, or reports safely."""

    safe_value = to_internal_evaluation_rehearsal_runner_json_safe_v1(value)
    if isinstance(safe_value, Mapping):
        summary = {
            "kind": "mapping",
            "keys": sorted(str(key) for key in safe_value.keys()),
            "status_label": str(safe_value.get("status_label", safe_value.get("summary_status", safe_value.get("result_label", "inconclusive_internal_rehearsal")))),
            "run_id": str(safe_value.get("run_id", "")),
            "runner_version": str(safe_value.get("runner_version", RUNNER_VERSION_V1)),
            "record_count": int(safe_value.get("record_count", safe_value.get("total_records", len(_ensure_list(safe_value.get("planned_records", []))))) or 0),
            "planned_record_count": int(safe_value.get("planned_record_count", len(_ensure_list(safe_value.get("planned_records", [])))) or 0),
            "blocked_record_count": int(safe_value.get("blocked_record_count", len(_ensure_list(safe_value.get("blocked_records", [])))) or 0),
            "result_label_counts": to_internal_evaluation_rehearsal_runner_json_safe_v1(safe_value.get("result_label_counts", {})),
            "failure_label_counts": to_internal_evaluation_rehearsal_runner_json_safe_v1(safe_value.get("failure_label_counts", {})),
            "missing_capability_counts": to_internal_evaluation_rehearsal_runner_json_safe_v1(safe_value.get("missing_capability_counts", {})),
            "blocked_labels": _dedupe_labels(_ensure_list(safe_value.get("blocked_labels", []))),
            "recommended_next_lanes": _dedupe_labels(_ensure_list(safe_value.get("recommended_next_lanes", [])), allowed=SAFE_NEXT_LANES_V1),
            "operator_review_required": bool(safe_value.get("operator_review_required", True)),
        }
        return to_internal_evaluation_rehearsal_runner_json_safe_v1(summary)
    if isinstance(safe_value, list):
        return {
            "kind": "list",
            "count": len(safe_value),
            "item_kinds": sorted({type(item).__name__ for item in safe_value}),
        }
    return {
        "kind": type(safe_value).__name__,
        "value": safe_value,
    }


__all__ = [
    "BLOCKED_LABELS_V1",
    "FAILURE_LABELS_V1",
    "MISSING_CAPABILITY_LABELS_V1",
    "RESULT_LABELS_V1",
    "RUNNER_SCHEMA_VERSION_V1",
    "RUNNER_VERSION_V1",
    "RUN_PHASE_LABELS_V1",
    "SAFE_NEXT_LANES_V1",
    "UNKNOWN_ENGINE_ALLOWED_ROLES_V1",
    "UNKNOWN_ENGINE_FORBIDDEN_ROLES_V1",
    "build_internal_evaluation_gap_report_v1",
    "build_internal_evaluation_rehearsal_review_packet_v1",
    "build_internal_evaluation_rehearsal_run_plan_v1",
    "map_internal_evaluation_rehearsal_gaps_v1",
    "normalize_internal_evaluation_rehearsal_outcome_v1",
    "summarize_internal_evaluation_rehearsal_runner_v1",
    "to_internal_evaluation_rehearsal_runner_json_safe_v1",
    "validate_internal_evaluation_rehearsal_batch_v1",
    "validate_internal_evaluation_rehearsal_preflight_v1",
]
