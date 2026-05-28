"""Metadata-only helpers for WESLR context pressure and compression evaluation v1.

This module is intentionally pure, deterministic, and fail-closed.
It converts approved synthetic/redacted context-pressure scenario metadata into
validation results, non-executing plans, redacted observations, and operator
review packets.

It does not perform file I/O, network I/O, subprocess execution, runtime/chat
wiring, live response routing, provider/model/search/advisor calls, dot-weslr
IO, or any official scoring work.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, is_dataclass
from typing import Any, Iterable, Mapping

HELPER_TYPE_V1 = "weslr_context_pressure_and_compression_helpers_v1"
BOUNDARY_TYPE_V1 = "context_pressure_and_compression_evaluation_v1"
CASE_TYPE_V1 = "context_pressure_case_v1"
PLAN_TYPE_V1 = "context_pressure_evaluation_plan_v1"
OBSERVATION_TYPE_V1 = "context_pressure_observation_v1"
RESULT_PACKET_TYPE_V1 = "context_pressure_result_packet_v1"

ALLOWED_CASE_FAMILIES_V1 = {
    "context_pressure_rehearsal",
}

ALLOWED_SOURCE_TYPES_V1 = {
    "synthetic_weslr_created",
    "generated_mutation_from_allowed_source",
}

BLOCKED_SOURCE_TYPES_V1 = {
    "public_open",
    "semi_private",
    "private",
    "hidden_blocked",
    "unknown_license_blocked_until_reviewed",
    "raw_private_user_data_blocked",
    "generated_mutation_from_blocked_source_blocked",
}

ALLOWED_SOURCE_LABELS_V1 = {
    "synthetic_weslr_created",
    "generated_mutation_from_allowed_source",
    "redacted_metadata_only",
}

ALLOWED_EXECUTION_MODE_LABELS_V1 = {
    "metadata_only",
    "future_controlled_internal_execution",
}

PLAN_STATUS_LABELS_V1 = {
    "blocked",
    "pending_operator_review",
    "pending_future_controlled_execution",
}

RISK_FAMILY_LABELS_V1 = {
    "meaning_compression_loss",
    "long_context_continuity_drift",
    "stale_context_reuse",
    "correction_state_loss",
    "evidence_boundary_loss",
    "governance_boundary_loss",
    "task_state_fragmentation",
    "intent_priority_drift",
    "contradiction_resolution_failure",
    "unsafe_context_overreach",
    "false_memory_from_summary",
    "relevant_context_omission",
    "irrelevant_context_overweighting",
    "pressure_induced_generic_response",
}

DIMENSION_LABELS_V1 = {
    "meaning_retention",
    "continuity_retention",
    "correction_retention",
    "evidence_scope_retention",
    "governance_boundary_retention",
    "stale_context_detection",
    "contradiction_handling",
    "relevance_selection",
    "uncertainty_preservation",
    "human_intent_preservation",
    "task_state_integrity",
    "safe_compression_behavior",
}

RESULT_LABELS_V1 = {
    "pass_internal_context_pressure_rehearsal",
    "partial_internal_context_pressure_rehearsal",
    "fail_internal_context_pressure_rehearsal",
    "inconclusive_internal_context_pressure_rehearsal",
    "blocked_by_privacy_boundary",
    "blocked_by_runtime_boundary",
    "needs_operator_review",
}

BLOCKED_LABELS_V1 = {
    "missing_case_id",
    "missing_case_family",
    "missing_source_type",
    "missing_source_label",
    "missing_registry_record_id",
    "missing_context_pressure_descriptor",
    "missing_expected_result_label",
    "missing_expected_dimension_labels",
    "missing_expected_risk_families",
    "missing_allowed_execution_mode",
    "missing_operator_review_requirement",
    "unknown_case_family",
    "unknown_source_type",
    "blocked_source_type",
    "blocked_source_label",
    "unknown_expected_result_label",
    "unknown_dimension_label",
    "unknown_risk_family",
    "unknown_execution_mode",
    "operator_review_not_required",
    "raw_private_content_requested",
    "raw_transcript_provided",
    "raw_transcript_storage_requested",
    "raw_response_text_provided",
    "provider_model_output_requested",
    "live_user_content_requested",
    "hidden_material_requested",
    "benchmark_material_requested",
    "dot_weslr_requested",
    "private_memory_scope_requested",
    "public_live_authority_requested",
    "public_ux_authority_requested",
    "voice_authority_requested",
    "final_answer_authority_requested",
    "runtime_authority_requested",
    "live_runtime_authority_requested",
    "model_call_authority_requested",
    "search_call_authority_requested",
    "advisor_call_authority_requested",
    "benchmark_submission_requested",
    "official_claim_requested",
    "turing_claim_requested",
    "intelligence_claim_requested",
    "certification_claim_requested",
    "public_readiness_requested",
    "voice_readiness_requested",
    "live_user_safety_readiness_requested",
    "benchmark_score_requested",
    "model_superiority_requested",
    "raw_persistence_requested",
    "private_memory_requested",
    "unknown_engine_authority_requested",
    "automatic_lesson_promotion_requested",
    "unknown_unknown_engine_role",
    "forbidden_unknown_engine_role",
    "unknown_authority_flag",
    "invalid_request_shape",
    "source_registry_missing",
}

DENIED_AUTHORITY_FLAGS_V1 = {
    "public_live_authority",
    "public_ux_authority",
    "voice_authority",
    "final_answer_authority",
    "runtime_wiring_authority",
    "live_runtime_authority",
    "model_call_authority",
    "search_call_authority",
    "advisor_call_authority",
    "benchmark_submission_authority",
    "official_claim_authority",
    "public_claim_authority",
    "turing_claim_authority",
    "intelligence_claim_authority",
    "certification_claim_authority",
    "public_readiness_claim_authority",
    "voice_readiness_claim_authority",
    "live_user_safety_readiness_claim_authority",
    "benchmark_score_authority",
    "model_superiority_authority",
    "raw_persistence_authority",
    "private_memory_authority",
    "unknown_engine_authority",
    "automatic_lesson_promotion_authority",
}

ALLOWED_UNKNOWN_ENGINE_ROLES_V1 = {
    "predict_context_pressure_failure_zones",
    "propose_synthetic_pressure_scenarios",
    "compare_predicted_vs_observed_pressure_failures",
    "compress_repeated_context_pressure_gaps",
}

FORBIDDEN_UNKNOWN_ENGINE_ROLES_V1 = {
    "authority",
    "scoring",
    "certification",
    "future_certainty",
    "source_license_approval",
    "runtime_live_control",
    "automatic_self_modification",
}

PHASE_A_METADATA_VALIDATION_V1 = "phase_a_metadata_validation"
PHASE_B_CONTEXT_DESCRIPTOR_VALIDATION_V1 = "phase_b_context_descriptor_validation"
PHASE_C_NON_EXECUTING_PLAN_V1 = "phase_c_non_executing_plan"
PHASE_D_OBSERVATION_NORMALIZATION_V1 = "phase_d_observation_normalization"
PHASE_E_GAP_REPORT_PACKET_V1 = "phase_e_gap_report_packet"
PHASE_F_OPERATOR_REVIEW_V1 = "phase_f_operator_review"

PHASE_LABELS_V1 = {
    PHASE_A_METADATA_VALIDATION_V1,
    PHASE_B_CONTEXT_DESCRIPTOR_VALIDATION_V1,
    PHASE_C_NON_EXECUTING_PLAN_V1,
    PHASE_D_OBSERVATION_NORMALIZATION_V1,
    PHASE_E_GAP_REPORT_PACKET_V1,
    PHASE_F_OPERATOR_REVIEW_V1,
}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _safe_bool(value: Any) -> bool:
    return bool(value) is True


def _safe_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        values = list(value.keys())
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = [value]
    out: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = _safe_str(item)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return out


def _unique_sorted(labels: Iterable[str]) -> list[str]:
    if isinstance(labels, (str, bytes)):
        items = [labels]
    else:
        items = list(labels)
    return sorted(set(_safe_list(items)))


def _json_sort_key(value: Any) -> tuple[str, str]:
    return (type(value).__name__, repr(value))


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        safe_items = [_json_safe(item) for item in value]
        return sorted(safe_items, key=_json_sort_key)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return f"[redacted:{type(value).__name__}]"


def to_context_pressure_json_safe_v1(value: Any) -> Any:
    """Convert supported context-pressure structures to deterministic JSON-safe data."""

    return _json_safe(value)


def _descriptor_from_case(case: Mapping[str, Any], case_family: str) -> str:
    descriptor = _safe_str(
        case.get("context_pressure_scenario_redacted_or_synthetic_descriptor")
        or case.get("context_chain_redacted_or_synthetic_descriptor")
        or case.get("context_descriptor_redacted_or_synthetic")
        or case.get("compressed_context_descriptor")
        or case.get("synthetic_descriptor")
        or case.get("context_descriptor")
    )
    if descriptor:
        return descriptor
    if any(
        _safe_str(case.get(key))
        for key in (
            "raw_context",
            "raw_transcript",
            "raw_response_text",
            "context_chain_text",
            "context_text",
            "live_user_chat_text",
            "prompt",
        )
    ):
        return "[redacted:context_pressure_case]"
    return f"[synthetic:{case_family or 'context_pressure_rehearsal'}]"


def _normalize_unknown_engine_roles(value: Any) -> list[str]:
    return _safe_list(value)


def _collect_authority_flags(record: Mapping[str, Any]) -> list[str]:
    flags: list[str] = []
    for flag in DENIED_AUTHORITY_FLAGS_V1:
        if _safe_bool(record.get(flag)):
            flags.append(flag)
    return _unique_sorted(flags)


def _collect_known_truthy_flags(record: Mapping[str, Any], keys: Iterable[str]) -> list[str]:
    flags: list[str] = []
    for key in keys:
        if _safe_bool(record.get(key)):
            flags.append(key)
    return _unique_sorted(flags)


def build_context_pressure_case_v1(
    case_item: Mapping[str, Any] | None = None,
    registry_item: Mapping[str, Any] | None = None,
    session_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a metadata-only context pressure case."""

    case = _as_mapping(case_item)
    registry = _as_mapping(registry_item)
    context = _as_mapping(session_context)

    case_family = _safe_str(case.get("case_family") or registry.get("case_family") or "context_pressure_rehearsal")
    source_type = _safe_str(case.get("source_type") or registry.get("source_type") or "synthetic_weslr_created")
    source_label = _safe_str(case.get("source_label") or registry.get("source_label") or source_type or "redacted_metadata_only")
    registry_record_id = _safe_str(
        case.get("registry_record_id") or registry.get("registry_record_id") or registry.get("record_id") or registry.get("id")
    )
    case_id = _safe_str(case.get("case_id") or case.get("id") or registry.get("case_id") or registry.get("id") or registry_record_id)
    context_pressure_descriptor = _descriptor_from_case(case, case_family)
    expected_result_label = _safe_str(case.get("expected_result_label") or registry.get("expected_result_label") or "needs_operator_review")
    expected_dimension_labels = _unique_sorted(case.get("expected_dimension_labels") or registry.get("expected_dimension_labels") or [])
    expected_risk_families = _unique_sorted(case.get("expected_risk_families") or registry.get("expected_risk_families") or [])
    allowed_execution_mode = _safe_str(case.get("allowed_execution_mode") or registry.get("allowed_execution_mode") or "metadata_only")
    operator_review_required = True if case.get("operator_review_required") is None and registry.get("operator_review_required") is None else _safe_bool(
        case.get("operator_review_required") if case.get("operator_review_required") is not None else registry.get("operator_review_required")
    )

    record = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "case_type": CASE_TYPE_V1,
        "case_status": "draft",
        "case_id": case_id,
        "case_family": case_family,
        "source_type": source_type,
        "source_label": source_label,
        "registry_record_id": registry_record_id,
        "context_pressure_scenario_redacted_or_synthetic_descriptor": context_pressure_descriptor,
        "expected_result_label": expected_result_label,
        "expected_dimension_labels": expected_dimension_labels,
        "expected_risk_families": expected_risk_families,
        "allowed_execution_mode": allowed_execution_mode,
        "operator_review_required": operator_review_required,
        "unknown_engine_roles": _normalize_unknown_engine_roles(case.get("unknown_engine_roles") or registry.get("unknown_engine_roles") or []),
        "case_labels": _safe_list(case.get("case_labels") or registry.get("case_labels") or []),
        "source_tags": _safe_list(case.get("source_tags") or registry.get("source_tags") or []),
        "context_tags": _safe_list(case.get("context_tags") or registry.get("context_tags") or []),
        "notes_redacted": _safe_str(case.get("notes_redacted") or registry.get("notes_redacted") or ""),
        "session_context": {
            "repo_root": _safe_str(context.get("repo_root")),
            "session_key": _safe_str(context.get("session_key")),
        },
        "official_claim_allowed": False,
        "public_claim_allowed": False,
        "runtime_authority_allowed": False,
        "live_runtime_authority_allowed": False,
        "voice_authority_allowed": False,
        "final_answer_authority_allowed": False,
        "unknown_engine_authority_allowed": False,
    }
    return _json_safe(record)


def validate_context_pressure_case_v1(case_item: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Validate a context pressure case and fail closed on unsupported input."""

    case = _as_mapping(case_item)
    blocked_labels: list[str] = []

    case_id = _safe_str(case.get("case_id") or case.get("id"))
    case_family = _safe_str(case.get("case_family") or "")
    source_type = _safe_str(case.get("source_type") or "")
    source_label = _safe_str(case.get("source_label") or "")
    registry_record_id = _safe_str(case.get("registry_record_id") or case.get("record_id") or case.get("id") or "")
    context_pressure_descriptor = _safe_str(
        case.get("context_pressure_scenario_redacted_or_synthetic_descriptor")
        or case.get("context_chain_redacted_or_synthetic_descriptor")
        or case.get("context_descriptor_redacted_or_synthetic")
        or case.get("compressed_context_descriptor")
        or case.get("synthetic_descriptor")
        or case.get("context_descriptor")
    )
    expected_result_label = _safe_str(case.get("expected_result_label") or "")
    expected_dimension_labels = _unique_sorted(case.get("expected_dimension_labels") or [])
    expected_risk_families = _unique_sorted(case.get("expected_risk_families") or [])
    allowed_execution_mode = _safe_str(case.get("allowed_execution_mode") or "")
    operator_review_required = case.get("operator_review_required")
    unknown_engine_roles = _normalize_unknown_engine_roles(case.get("unknown_engine_roles") or [])

    if not case_id:
        blocked_labels.append("missing_case_id")
    if not case_family:
        blocked_labels.append("missing_case_family")
    if not source_type:
        blocked_labels.append("missing_source_type")
    if not source_label:
        blocked_labels.append("missing_source_label")
    if not registry_record_id:
        blocked_labels.append("missing_registry_record_id")
    if not context_pressure_descriptor:
        blocked_labels.append("missing_context_pressure_descriptor")
    if not expected_result_label:
        blocked_labels.append("missing_expected_result_label")
    if not expected_dimension_labels:
        blocked_labels.append("missing_expected_dimension_labels")
    if not expected_risk_families:
        blocked_labels.append("missing_expected_risk_families")
    if not allowed_execution_mode:
        blocked_labels.append("missing_allowed_execution_mode")
    if operator_review_required is None:
        blocked_labels.append("missing_operator_review_requirement")

    if case_family and case_family not in ALLOWED_CASE_FAMILIES_V1:
        blocked_labels.append("unknown_case_family")
    if source_type and source_type not in ALLOWED_SOURCE_TYPES_V1 and source_type in BLOCKED_SOURCE_TYPES_V1:
        blocked_labels.append("blocked_source_type")
    elif source_type and source_type not in ALLOWED_SOURCE_TYPES_V1:
        blocked_labels.append("unknown_source_type")
    if source_label and source_label not in ALLOWED_SOURCE_LABELS_V1:
        blocked_labels.append("blocked_source_label")

    if expected_result_label and expected_result_label not in RESULT_LABELS_V1:
        blocked_labels.append("unknown_expected_result_label")

    for label in expected_dimension_labels:
        if label not in DIMENSION_LABELS_V1:
            blocked_labels.append("unknown_dimension_label")
            break

    for risk in expected_risk_families:
        if risk not in RISK_FAMILY_LABELS_V1:
            blocked_labels.append("unknown_risk_family")
            break

    if allowed_execution_mode and allowed_execution_mode not in ALLOWED_EXECUTION_MODE_LABELS_V1:
        blocked_labels.append("unknown_execution_mode")

    if operator_review_required is False:
        blocked_labels.append("operator_review_not_required")

    raw_truthy_flags = _collect_known_truthy_flags(
        case,
        (
            "raw_private_content_requested",
            "raw_context_requested",
            "raw_context_storage_requested",
            "raw_transcript_requested",
            "raw_transcript_storage_requested",
            "raw_response_text_provided",
            "raw_response_storage_requested",
            "provider_model_output_requested",
            "live_user_content_requested",
            "live_user_chat_requested",
            "hidden_material_requested",
            "benchmark_material_requested",
            "dot_weslr_requested",
            "private_memory_scope_requested",
            "public_live_authority_allowed",
            "public_ux_authority_allowed",
            "voice_authority_allowed",
            "final_answer_authority_allowed",
            "runtime_authority_allowed",
            "live_runtime_authority_allowed",
            "model_call_authority_allowed",
            "search_call_authority_allowed",
            "advisor_call_authority_allowed",
            "benchmark_submission_requested",
            "official_claim_allowed",
            "public_claim_allowed",
            "turing_claim_allowed",
            "intelligence_claim_allowed",
            "certification_claim_allowed",
            "public_readiness_requested",
            "voice_readiness_requested",
            "live_user_safety_readiness_requested",
            "benchmark_score_requested",
            "model_superiority_requested",
            "raw_persistence_requested",
            "private_memory_requested",
            "unknown_engine_authority_allowed",
            "automatic_lesson_promotion_requested",
            "unknown_authority_flag",
            "invalid_request_shape",
            "source_registry_missing",
        ),
    )
    blocked_labels.extend(raw_truthy_flags)

    if case.get("raw_context") or case.get("raw_private_context") or case.get("raw_context_text"):
        blocked_labels.append("raw_private_content_requested")
    if case.get("raw_transcript") or case.get("raw_transcript_text"):
        blocked_labels.append("raw_transcript_provided")
    if case.get("raw_response_text"):
        blocked_labels.append("raw_response_text_provided")
    if case.get("live_user_chat_text"):
        blocked_labels.append("live_user_content_requested")
    if case.get("private_memory") or case.get("private_memory_text"):
        blocked_labels.append("private_memory_requested")
    if case.get("hidden_dataset_requested"):
        blocked_labels.append("hidden_material_requested")
    if case.get("benchmark_dataset_requested"):
        blocked_labels.append("benchmark_material_requested")

    for role in unknown_engine_roles:
        if role in FORBIDDEN_UNKNOWN_ENGINE_ROLES_V1:
            blocked_labels.append("forbidden_unknown_engine_role")
        elif role not in ALLOWED_UNKNOWN_ENGINE_ROLES_V1:
            blocked_labels.append("unknown_unknown_engine_role")

    if any(_safe_bool(case.get(flag)) for flag in DENIED_AUTHORITY_FLAGS_V1):
        blocked_labels.append("unknown_authority_flag")

    source_blocked = source_type in BLOCKED_SOURCE_TYPES_V1 or source_label not in ALLOWED_SOURCE_LABELS_V1
    if source_type in BLOCKED_SOURCE_TYPES_V1:
        blocked_labels.append("blocked_source_type")
    if source_label and source_label not in ALLOWED_SOURCE_LABELS_V1:
        blocked_labels.append("blocked_source_label")

    if source_blocked and "blocked_source_type" not in blocked_labels:
        blocked_labels.append("blocked_source_type")

    blocked_labels = _unique_sorted(blocked_labels)
    case_status = "valid" if not blocked_labels else "blocked"

    normalized_case = build_context_pressure_case_v1(case)
    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "case_type": CASE_TYPE_V1,
        "valid": not blocked_labels,
        "blocked": bool(blocked_labels),
        "case_status": case_status,
        "case_id": case_id,
        "case_family": case_family,
        "source_type": source_type,
        "source_label": source_label,
        "registry_record_id": registry_record_id,
        "context_pressure_descriptor": context_pressure_descriptor,
        "expected_result_label": expected_result_label,
        "expected_dimension_labels": expected_dimension_labels,
        "expected_risk_families": expected_risk_families,
        "allowed_execution_mode": allowed_execution_mode,
        "operator_review_required": _safe_bool(operator_review_required),
        "blocked_labels": blocked_labels,
        "denied_authority_flags": _collect_authority_flags(case),
        "unknown_engine_roles": [
            role for role in unknown_engine_roles if role in ALLOWED_UNKNOWN_ENGINE_ROLES_V1
        ],
        "normalized_case": normalized_case,
        "official_claim_allowed": False,
        "public_claim_allowed": False,
        "runtime_authority_allowed": False,
        "live_runtime_authority_allowed": False,
        "voice_authority_allowed": False,
        "final_answer_authority_allowed": False,
        "unknown_engine_authority_allowed": False,
    }


def build_context_pressure_evaluation_plan_v1(
    case_item: Mapping[str, Any] | None = None,
    validation_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a non-executing context pressure evaluation plan."""

    case = _as_mapping(case_item)
    validation = _as_mapping(validation_result)
    blocked_labels = _unique_sorted(validation.get("blocked_labels") or [])
    operator_review_required = True if validation.get("operator_review_required") is None else _safe_bool(validation.get("operator_review_required"))
    allowed_execution_mode = _safe_str(validation.get("allowed_execution_mode") or case.get("allowed_execution_mode") or "metadata_only")

    if blocked_labels:
        plan_status = "blocked"
    elif allowed_execution_mode == "future_controlled_internal_execution":
        plan_status = "pending_future_controlled_execution"
    else:
        plan_status = "pending_operator_review"

    phases = [
        {
            "phase_label": PHASE_A_METADATA_VALIDATION_V1,
            "phase_name": "metadata_validation",
            "description": "Validate metadata-only context-pressure inputs and blocked labels.",
        },
        {
            "phase_label": PHASE_B_CONTEXT_DESCRIPTOR_VALIDATION_V1,
            "phase_name": "context_descriptor_validation",
            "description": "Check redacted or synthetic context descriptors and reject raw private context.",
        },
        {
            "phase_label": PHASE_C_NON_EXECUTING_PLAN_V1,
            "phase_name": "non_executing_plan",
            "description": "Build a plan that never becomes a live runtime call path.",
        },
        {
            "phase_label": PHASE_D_OBSERVATION_NORMALIZATION_V1,
            "phase_name": "observation_normalization",
            "description": "Redact raw context, transcript, and response text by default.",
        },
        {
            "phase_label": PHASE_E_GAP_REPORT_PACKET_V1,
            "phase_name": "gap_report_packet",
            "description": "Package operator-safe metadata, blocked labels, and denied authority flags.",
        },
        {
            "phase_label": PHASE_F_OPERATOR_REVIEW_V1,
            "phase_name": "operator_review",
            "description": "Leave approval and any future execution boundary to operator review.",
        },
    ]

    plan = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "plan_type": PLAN_TYPE_V1,
        "plan_status": plan_status,
        "case_id": _safe_str(case.get("case_id") or validation.get("case_id") or ""),
        "case_family": _safe_str(case.get("case_family") or validation.get("case_family") or ""),
        "source_type": _safe_str(case.get("source_type") or validation.get("source_type") or ""),
        "source_label": _safe_str(case.get("source_label") or validation.get("source_label") or ""),
        "registry_record_id": _safe_str(case.get("registry_record_id") or validation.get("registry_record_id") or ""),
        "operator_review_required": operator_review_required,
        "should_execute": False,
        "controlled_execution_allowed": False,
        "execution_callable": None,
        "live_call_allowed": False,
        "chat_responder_call_allowed": False,
        "model_call_allowed": False,
        "search_call_allowed": False,
        "advisor_call_allowed": False,
        "phases": phases,
        "blocked_labels": blocked_labels,
        "allowed_execution_mode": allowed_execution_mode,
        "final_answer_authority": False,
        "user_facing_prose_authority": False,
        "live_runtime_authority": False,
        "public_live_authority": False,
        "official_claims": False,
    }
    return _json_safe(plan)


def _normalize_observation_item(observation: Mapping[str, Any]) -> dict[str, Any]:
    blocked_labels: list[str] = []
    result_label = _safe_str(observation.get("result_label") or observation.get("expected_result_label") or "needs_operator_review")
    if result_label and result_label not in RESULT_LABELS_V1:
        blocked_labels.append("unknown_expected_result_label")
        result_label = "needs_operator_review"

    dimension_labels = _unique_sorted(observation.get("dimension_labels") or observation.get("observed_dimension_labels") or [])
    for label in dimension_labels:
        if label not in DIMENSION_LABELS_V1:
            blocked_labels.append("unknown_dimension_label")
            dimension_labels = [item for item in dimension_labels if item in DIMENSION_LABELS_V1]
            break

    risk_family_labels = _unique_sorted(observation.get("risk_family_labels") or observation.get("gap_labels") or [])
    for label in risk_family_labels:
        if label not in RISK_FAMILY_LABELS_V1 and not label.startswith("missing_") and not label.startswith("predicted_") and not label.startswith("observed_"):
            blocked_labels.append("unknown_risk_family")
            risk_family_labels = [item for item in risk_family_labels if item in RISK_FAMILY_LABELS_V1 or item.startswith("missing_") or item.startswith("predicted_") or item.startswith("observed_")]
            break

    predicted_labels = _unique_sorted(observation.get("predicted_labels") or [])
    observed_labels = _unique_sorted(observation.get("observed_labels") or [])

    raw_context_present = "raw_context" in observation or "raw_private_context" in observation or "raw_context_text" in observation
    raw_transcript_present = "raw_transcript" in observation or "raw_transcript_text" in observation
    raw_response_text_present = "raw_response_text" in observation or "raw_response" in observation

    result = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "observation_type": OBSERVATION_TYPE_V1,
        "result_label": result_label,
        "dimension_labels": dimension_labels,
        "risk_family_labels": risk_family_labels,
        "predicted_labels": predicted_labels,
        "observed_labels": observed_labels,
        "gap_labels": _unique_sorted(observation.get("gap_labels") or []),
        "raw_context_present": raw_context_present,
        "raw_context_retained": False if raw_context_present else False,
        "raw_context_redacted": bool(raw_context_present),
        "raw_transcript_present": raw_transcript_present,
        "raw_transcript_retained": False if raw_transcript_present else False,
        "raw_transcript_redacted": bool(raw_transcript_present),
        "raw_response_text_present": raw_response_text_present,
        "raw_response_text_retained": False if raw_response_text_present else False,
        "raw_response_text_redacted": bool(raw_response_text_present),
        "final_answer_authority": False,
        "user_facing_prose_authority": False,
        "live_runtime_authority": False,
        "public_live_authority": False,
        "official_claims": False,
        "blocked_labels": _unique_sorted(blocked_labels),
        "denied_authority_flags": _unique_sorted(
            flag for flag in _safe_list(observation.get("denied_authority_flags") or []) if flag in DENIED_AUTHORITY_FLAGS_V1
        ),
    }
    return result


def normalize_context_pressure_observation_v1(observation_item: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Normalize a metadata-only context-pressure observation."""

    observation = _as_mapping(observation_item)
    normalized = _normalize_observation_item(observation)

    if observation.get("raw_context") or observation.get("raw_private_context") or observation.get("raw_context_text"):
        normalized["blocked_labels"] = _unique_sorted(normalized["blocked_labels"] + ["raw_private_content_requested"])
    if observation.get("raw_transcript") or observation.get("raw_transcript_text"):
        normalized["blocked_labels"] = _unique_sorted(normalized["blocked_labels"] + ["raw_transcript_provided"])
    if observation.get("raw_response_text") or observation.get("raw_response"):
        normalized["blocked_labels"] = _unique_sorted(normalized["blocked_labels"] + ["raw_response_text_provided"])

    return _json_safe(normalized)


def _coerce_observations(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        return [normalize_context_pressure_observation_v1(value)]
    if isinstance(value, (list, tuple, set)):
        observations: list[dict[str, Any]] = []
        for item in value:
            observations.append(normalize_context_pressure_observation_v1(_as_mapping(item)))
        return observations
    return []


def build_context_pressure_result_packet_v1(
    case_item: Mapping[str, Any] | None = None,
    validation_result: Mapping[str, Any] | None = None,
    plan_item: Mapping[str, Any] | None = None,
    observation_item: Mapping[str, Any] | Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a metadata-only operator packet for context-pressure evaluation."""

    case = _as_mapping(case_item)
    validation = _as_mapping(validation_result)
    plan = _as_mapping(plan_item)
    observations = _coerce_observations(observation_item)

    blocked_labels = _unique_sorted(validation.get("blocked_labels") or plan.get("blocked_labels") or [])
    denied_authority_flags = _unique_sorted(
        list(validation.get("denied_authority_flags") or [])
        + list(plan.get("denied_authority_flags") or [])
        + [flag for obs in observations for flag in obs.get("denied_authority_flags", [])]
    )

    packet = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "packet_type": RESULT_PACKET_TYPE_V1,
        "packet_status": plan.get("plan_status") or validation.get("case_status") or "needs_operator_review",
        "case_id": _safe_str(case.get("case_id") or validation.get("case_id") or plan.get("case_id") or ""),
        "case_family": _safe_str(case.get("case_family") or validation.get("case_family") or plan.get("case_family") or ""),
        "source_type": _safe_str(case.get("source_type") or validation.get("source_type") or plan.get("source_type") or ""),
        "source_label": _safe_str(case.get("source_label") or validation.get("source_label") or plan.get("source_label") or ""),
        "registry_record_id": _safe_str(case.get("registry_record_id") or validation.get("registry_record_id") or plan.get("registry_record_id") or ""),
        "case_validation": validation,
        "plan": plan,
        "observations": observations,
        "blocked_labels": blocked_labels,
        "denied_authority_flags": denied_authority_flags,
        "operator_review_required": True if validation.get("operator_review_required") is None else _safe_bool(validation.get("operator_review_required")),
        "final_answer_authority": False,
        "user_facing_prose_authority": False,
        "live_runtime_authority": False,
        "public_live_authority": False,
        "official_claims": False,
    }
    return _json_safe(packet)


def _extract_batch_records(value: Any) -> list[Any]:
    if isinstance(value, Mapping) and "records" in value:
        return list(value.get("records") or [])
    if isinstance(value, (list, tuple, set)):
        return list(value)
    if value is None:
        return []
    return [value]


def validate_context_pressure_batch_v1(batch_value: Iterable[Any] | Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Validate a batch of context-pressure cases and preserve per-case status."""

    records: list[dict[str, Any]] = []
    for item in _extract_batch_records(batch_value):
        validation = validate_context_pressure_case_v1(_as_mapping(item))
        records.append(validation)

    aggregate_blocked_labels = _unique_sorted(label for result in records for label in result.get("blocked_labels", []))
    aggregate_denied_authority_flags = _unique_sorted(
        flag for result in records for flag in result.get("denied_authority_flags", [])
    )

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "valid": all(result["valid"] for result in records) if records else True,
        "total_records": len(records),
        "valid_records": sum(1 for result in records if result["valid"]),
        "blocked_records": sum(1 for result in records if result["blocked"]),
        "aggregate_blocked_labels": aggregate_blocked_labels,
        "aggregate_denied_authority_flags": aggregate_denied_authority_flags,
        "records": records,
    }


def summarize_context_pressure_batch_v1(value: Mapping[str, Any] | Iterable[Any]) -> dict[str, Any]:
    """Return a safe metadata-only summary of context-pressure cases or results."""

    if isinstance(value, Mapping) and "records" in value:
        items = value["records"]
    else:
        items = value

    normalized_results: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, Mapping) and {"valid", "blocked", "normalized_case"}.issubset(set(item.keys())):
            normalized_results.append(validate_context_pressure_case_v1(item.get("normalized_case") or {}))
        elif isinstance(item, Mapping) and {"valid", "blocked", "blocked_labels"}.issubset(set(item.keys())):
            normalized_results.append(item)
        else:
            normalized_results.append(validate_context_pressure_case_v1(item))

    blocked_labels = _unique_sorted(label for result in normalized_results for label in result.get("blocked_labels", []))
    denied_authority_flags = _unique_sorted(
        flag for result in normalized_results for flag in result.get("denied_authority_flags", [])
    )
    case_family_counts: dict[str, int] = {}
    source_type_counts: dict[str, int] = {}
    plan_status_counts: dict[str, int] = {}
    result_label_counts: dict[str, int] = {}
    for result in normalized_results:
        case_family = _safe_str(result.get("case_family") or "unknown")
        source_type = _safe_str(result.get("source_type") or "unknown")
        case_family_counts[case_family] = case_family_counts.get(case_family, 0) + 1
        source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
        plan_status = _safe_str(result.get("plan_status") or result.get("case_status") or "unknown")
        plan_status_counts[plan_status] = plan_status_counts.get(plan_status, 0) + 1
        result_label = _safe_str(result.get("expected_result_label") or "unknown")
        result_label_counts[result_label] = result_label_counts.get(result_label, 0) + 1

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "total_records": len(normalized_results),
        "valid_records": sum(1 for result in normalized_results if _safe_bool(result.get("valid"))),
        "blocked_records": sum(1 for result in normalized_results if _safe_bool(result.get("blocked"))),
        "blocked_label_count": len(blocked_labels),
        "blocked_labels": blocked_labels,
        "denied_authority_flags": denied_authority_flags,
        "case_family_counts": case_family_counts,
        "source_type_counts": source_type_counts,
        "plan_status_counts": plan_status_counts,
        "result_label_counts": result_label_counts,
        "case_status_counts": {
            "valid": sum(1 for result in normalized_results if _safe_str(result.get("case_status")) == "valid"),
            "blocked": sum(1 for result in normalized_results if _safe_str(result.get("case_status")) == "blocked"),
        },
        "final_answer_authority": False,
        "user_facing_prose_authority": False,
        "live_runtime_authority": False,
        "public_live_authority": False,
        "official_claims": False,
    }
