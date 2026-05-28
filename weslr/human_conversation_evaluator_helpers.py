"""Metadata-only helpers for WESLR human conversation evaluator boundary v1.

This module is intentionally pure, deterministic, and fail-closed.
It converts approved synthetic/redacted conversation scenario metadata into
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

HELPER_TYPE_V1 = "weslr_human_conversation_evaluator_helpers_v1"
BOUNDARY_TYPE_V1 = "human_conversation_evaluator_boundary_v1"
CASE_TYPE_V1 = "human_conversation_evaluator_case_v1"
PLAN_TYPE_V1 = "human_conversation_evaluator_plan_v1"
OBSERVATION_TYPE_V1 = "human_conversation_evaluator_observation_v1"
RESULT_PACKET_TYPE_V1 = "human_conversation_evaluator_result_packet_v1"

ALLOWED_CASE_FAMILIES_V1 = {
    "human_conversation_rehearsal",
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

DIMENSION_LABELS_V1 = {
    "intent_tracking",
    "continuity_tracking",
    "correction_assimilation",
    "human_concern_tracking",
    "specificity_non_cannedness",
    "uncertainty_honesty",
    "evidence_boundary_awareness",
    "action_governance_awareness",
    "tone_and_priority_fit",
    "safe_next_step_quality",
}

RESULT_LABELS_V1 = {
    "pass_internal_conversation_rehearsal",
    "partial_internal_conversation_rehearsal",
    "fail_internal_conversation_rehearsal",
    "inconclusive_internal_conversation_rehearsal",
    "blocked_by_source_governance",
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
    "missing_conversation_descriptor",
    "missing_expected_result_label",
    "missing_expected_dimension_labels",
    "missing_allowed_execution_mode",
    "missing_operator_review_requirement",
    "unknown_case_family",
    "unknown_source_type",
    "blocked_source_type",
    "blocked_source_label",
    "unknown_expected_result_label",
    "unknown_dimension_label",
    "unknown_execution_mode",
    "operator_review_not_required",
    "raw_transcript_provided",
    "raw_response_text_provided",
    "raw_private_content_requested",
    "raw_transcript_storage_requested",
    "raw_response_storage_requested",
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
    "predict_conversation_failure_zones",
    "suggest_synthetic_scenario_variants",
    "compare_predicted_vs_observed_failure_labels",
    "compress_repeated_conversation_gaps",
}

FORBIDDEN_UNKNOWN_ENGINE_ROLES_V1 = {
    "authority",
    "scoring",
    "certification",
    "official_turing_judge",
    "future_certainty",
    "source_license_approval",
    "runtime_live_control",
    "automatic_self_modification",
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


def to_human_conversation_evaluator_json_safe_v1(value: Any) -> Any:
    """Convert supported evaluator structures to deterministic JSON-safe data."""

    return _json_safe(value)


def _descriptor_from_case(case: Mapping[str, Any], case_family: str) -> str:
    descriptor = _safe_str(
        case.get("conversation_scenario_redacted_or_synthetic_descriptor")
        or case.get("conversation_descriptor_redacted_or_synthetic")
        or case.get("synthetic_descriptor")
        or case.get("conversation_descriptor")
    )
    if descriptor:
        return descriptor
    if any(
        _safe_str(case.get(key))
        for key in (
            "raw_transcript",
            "transcript_text",
            "live_chat_text",
            "conversation_text",
            "raw_response_text",
            "response_text",
            "prompt",
            "final_answer",
        )
    ):
        return "[redacted:conversation_scenario]"
    return f"[synthetic:{case_family or 'human_conversation_rehearsal'}]"


def _normalize_unknown_engine_roles(value: Any) -> list[str]:
    return _safe_list(value)


def _validate_unknown_engine_roles(roles: Any) -> tuple[list[str], list[str]]:
    normalized = _normalize_unknown_engine_roles(roles)
    blocked: list[str] = []
    for role in normalized:
        if role in FORBIDDEN_UNKNOWN_ENGINE_ROLES_V1:
            blocked.append("forbidden_unknown_engine_role")
        elif role not in ALLOWED_UNKNOWN_ENGINE_ROLES_V1:
            blocked.append("unknown_unknown_engine_role")
    return normalized, _unique_sorted(blocked)


def _collect_authority_flags(record: Mapping[str, Any]) -> list[str]:
    flags: list[str] = []
    for flag in DENIED_AUTHORITY_FLAGS_V1:
        if _safe_bool(record.get(flag)):
            flags.append(flag)
    return _unique_sorted(flags)


def build_human_conversation_evaluator_case_v1(
    case_item: Mapping[str, Any] | None = None,
    registry_item: Mapping[str, Any] | None = None,
    session_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a metadata-only conversation evaluator case."""

    case = _as_mapping(case_item)
    registry = _as_mapping(registry_item)
    context = _as_mapping(session_context)

    case_family = _safe_str(case.get("case_family") or registry.get("case_family") or "human_conversation_rehearsal")
    source_type = _safe_str(case.get("source_type") or registry.get("source_type") or "synthetic_weslr_created")
    source_label = _safe_str(case.get("source_label") or registry.get("source_label") or source_type or "redacted_metadata_only")
    registry_record_id = _safe_str(
        case.get("registry_record_id") or registry.get("registry_record_id") or registry.get("record_id") or registry.get("id")
    )
    case_id = _safe_str(case.get("case_id") or case.get("id") or registry.get("case_id") or registry.get("id") or registry_record_id)
    expected_result_label = _safe_str(case.get("expected_result_label") or registry.get("expected_result_label") or "needs_operator_review")
    expected_dimension_labels = _unique_sorted(case.get("expected_dimension_labels") or registry.get("expected_dimension_labels") or [])
    allowed_execution_mode = _safe_str(case.get("allowed_execution_mode") or registry.get("allowed_execution_mode") or "metadata_only")
    operator_review_required = True if case.get("operator_review_required") is None and registry.get("operator_review_required") is None else _safe_bool(
        case.get("operator_review_required") if case.get("operator_review_required") is not None else registry.get("operator_review_required")
    )

    conversation_descriptor = _descriptor_from_case(case, case_family)

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
        "conversation_scenario_redacted_or_synthetic_descriptor": conversation_descriptor,
        "expected_result_label": expected_result_label,
        "expected_dimension_labels": expected_dimension_labels,
        "allowed_execution_mode": allowed_execution_mode,
        "operator_review_required": operator_review_required,
        "official_claim_allowed": False,
        "public_claim_allowed": False,
        "turing_claim_allowed": False,
        "intelligence_claim_allowed": False,
        "certification_claim_allowed": False,
        "public_readiness_claim_allowed": False,
        "voice_readiness_claim_allowed": False,
        "live_user_safety_readiness_claim_allowed": False,
        "benchmark_score_allowed": False,
        "model_superiority_allowed": False,
        "runtime_authority_allowed": False,
        "voice_authority_allowed": False,
        "unknown_engine_authority_allowed": False,
        "final_answer_authority_allowed": False,
        "user_facing_prose_authority_allowed": False,
        "public_live_authority_allowed": False,
        "public_ux_authority_allowed": False,
        "live_runtime_authority_allowed": False,
        "model_call_authority_allowed": False,
        "search_call_authority_allowed": False,
        "advisor_call_authority_allowed": False,
        "raw_persistence_allowed": False,
        "private_memory_allowed": False,
        "automatic_lesson_promotion_allowed": False,
        "unknown_engine_roles": _normalize_unknown_engine_roles(case.get("unknown_engine_roles") or registry.get("unknown_engine_roles")),
        "raw_private_data_requested": _safe_bool(case.get("raw_private_data_requested") or registry.get("raw_private_data_requested")),
        "raw_transcript_requested": _safe_bool(case.get("raw_transcript_requested") or registry.get("raw_transcript_requested")),
        "raw_transcript_storage_requested": _safe_bool(case.get("raw_transcript_storage_requested") or registry.get("raw_transcript_storage_requested")),
        "raw_response_storage_requested": _safe_bool(case.get("raw_response_storage_requested") or registry.get("raw_response_storage_requested")),
        "provider_model_output_requested": _safe_bool(case.get("provider_model_output_requested") or registry.get("provider_model_output_requested")),
        "hidden_material_requested": _safe_bool(case.get("hidden_material_requested") or registry.get("hidden_material_requested")),
        "benchmark_material_requested": _safe_bool(case.get("benchmark_material_requested") or registry.get("benchmark_material_requested")),
        "live_user_content_requested": _safe_bool(case.get("live_user_content_requested") or registry.get("live_user_content_requested")),
        "dot_weslr_requested": _safe_bool(case.get("dot_weslr_requested") or registry.get("dot_weslr_requested")),
        "private_memory_scope_requested": _safe_bool(case.get("private_memory_scope_requested") or registry.get("private_memory_scope_requested")),
        "public_readiness_claim_requested": _safe_bool(case.get("public_readiness_claim_requested") or registry.get("public_readiness_claim_requested")),
        "voice_readiness_claim_requested": _safe_bool(case.get("voice_readiness_claim_requested") or registry.get("voice_readiness_claim_requested")),
        "live_user_safety_readiness_claim_requested": _safe_bool(case.get("live_user_safety_readiness_claim_requested") or registry.get("live_user_safety_readiness_claim_requested")),
        "benchmark_score_requested": _safe_bool(case.get("benchmark_score_requested") or registry.get("benchmark_score_requested")),
        "model_superiority_requested": _safe_bool(case.get("model_superiority_requested") or registry.get("model_superiority_requested")),
        "official_claim_requested": _safe_bool(case.get("official_claim_requested") or registry.get("official_claim_requested")),
        "turing_claim_requested": _safe_bool(case.get("turing_claim_requested") or registry.get("turing_claim_requested")),
        "intelligence_claim_requested": _safe_bool(case.get("intelligence_claim_requested") or registry.get("intelligence_claim_requested")),
        "certification_claim_requested": _safe_bool(case.get("certification_claim_requested") or registry.get("certification_claim_requested")),
        "conversation_context": {
            "repo_root": _safe_str(context.get("repo_root") or case.get("repo_root") or registry.get("repo_root")),
            "session_key": _safe_str(context.get("session_key") or case.get("session_key") or registry.get("session_key")),
        },
        "case_labels": _safe_list(case.get("case_labels") or registry.get("case_labels")),
        "source_tags": _safe_list(case.get("source_tags") or registry.get("source_tags")),
    }

    return to_human_conversation_evaluator_json_safe_v1(record)


def validate_human_conversation_evaluator_case_v1(case: Mapping[str, Any] | None) -> dict[str, Any]:
    """Validate a single case and fail closed on unsafe input."""

    normalized_case = to_human_conversation_evaluator_json_safe_v1(case or {})
    if not isinstance(normalized_case, dict):
        normalized_case = {}

    blocked_labels: list[str] = []
    errors: list[str] = []

    required_fields = [
        "case_id",
        "case_family",
        "source_type",
        "source_label",
        "registry_record_id",
        "conversation_scenario_redacted_or_synthetic_descriptor",
        "expected_result_label",
        "expected_dimension_labels",
        "allowed_execution_mode",
        "operator_review_required",
    ]
    for field in required_fields:
        value = normalized_case.get(field)
        if field == "expected_dimension_labels":
            if not _safe_list(value):
                blocked_labels.append("missing_expected_dimension_labels")
                errors.append(f"missing field: {field}")
        elif field == "operator_review_required":
            if field not in normalized_case:
                blocked_labels.append("missing_operator_review_requirement")
                errors.append(f"missing field: {field}")
        elif field not in normalized_case or value in (None, "", [], {}):
            blocked_labels.append(f"missing_{field}")
            errors.append(f"missing field: {field}")

    case_id = _safe_str(normalized_case.get("case_id"))
    case_family = _safe_str(normalized_case.get("case_family"))
    source_type = _safe_str(normalized_case.get("source_type"))
    source_label = _safe_str(normalized_case.get("source_label"))
    registry_record_id = _safe_str(normalized_case.get("registry_record_id"))
    descriptor = _safe_str(normalized_case.get("conversation_scenario_redacted_or_synthetic_descriptor"))
    expected_result_label = _safe_str(normalized_case.get("expected_result_label"))
    expected_dimension_labels = _safe_list(normalized_case.get("expected_dimension_labels"))
    allowed_execution_mode = _safe_str(normalized_case.get("allowed_execution_mode"))
    operator_review_required = _safe_bool(normalized_case.get("operator_review_required"))

    if not case_id:
        blocked_labels.append("missing_case_id")
    if not case_family:
        blocked_labels.append("missing_case_family")
    elif case_family not in ALLOWED_CASE_FAMILIES_V1:
        blocked_labels.append("unknown_case_family")
    if not source_type:
        blocked_labels.append("missing_source_type")
    elif source_type in BLOCKED_SOURCE_TYPES_V1:
        blocked_labels.append("blocked_source_type")
    elif source_type not in ALLOWED_SOURCE_TYPES_V1:
        blocked_labels.append("unknown_source_type")
    if not source_label:
        blocked_labels.append("missing_source_label")
    elif source_label in BLOCKED_SOURCE_TYPES_V1:
        blocked_labels.append("blocked_source_label")
    elif source_label not in ALLOWED_SOURCE_LABELS_V1:
        # Redacted labels are allowed, everything else is considered unknown.
        blocked_labels.append("blocked_source_label")
    if not registry_record_id:
        blocked_labels.append("missing_registry_record_id")
    if not descriptor:
        blocked_labels.append("missing_conversation_descriptor")
    if not expected_result_label:
        blocked_labels.append("missing_expected_result_label")
    elif expected_result_label not in RESULT_LABELS_V1:
        blocked_labels.append("unknown_expected_result_label")
    if not expected_dimension_labels:
        blocked_labels.append("missing_expected_dimension_labels")
    else:
        unknown_dimensions = [label for label in expected_dimension_labels if label not in DIMENSION_LABELS_V1]
        if unknown_dimensions:
            blocked_labels.append("unknown_dimension_label")
    if not allowed_execution_mode:
        blocked_labels.append("missing_allowed_execution_mode")
    elif allowed_execution_mode not in ALLOWED_EXECUTION_MODE_LABELS_V1:
        blocked_labels.append("unknown_execution_mode")
    if not operator_review_required:
        blocked_labels.append("operator_review_not_required")

    raw_content_keys = {
        "raw_transcript",
        "transcript_text",
        "live_chat_text",
        "conversation_text",
        "raw_response_text",
        "response_text",
        "prompt",
        "final_answer",
        "raw_text",
        "live_user_text",
        "private_text",
        "benchmark_text",
        "hidden_text",
        "raw_transcript_requested",
        "raw_transcript_storage_requested",
        "raw_response_storage_requested",
        "provider_model_output_requested",
        "raw_private_data_requested",
        "live_user_content_requested",
        "hidden_material_requested",
        "benchmark_material_requested",
        "dot_weslr_requested",
        "private_memory_scope_requested",
    }
    for key in raw_content_keys:
        value = normalized_case.get(key)
        if isinstance(value, str):
            if _safe_str(value):
                if key in {"raw_transcript", "transcript_text", "live_chat_text", "conversation_text"}:
                    blocked_labels.append("raw_transcript_provided")
                elif key in {"raw_response_text", "response_text", "raw_text", "prompt", "final_answer"}:
                    blocked_labels.append("raw_response_text_provided")
                elif key in {"provider_model_output_requested"}:
                    blocked_labels.append("provider_model_output_requested")
                elif key in {"dot_weslr_requested", "private_memory_scope_requested"}:
                    blocked_labels.append("dot_weslr_requested")
                else:
                    blocked_labels.append("raw_private_content_requested")
        elif _safe_bool(value):
            if key in {"raw_transcript_requested", "raw_transcript_storage_requested"}:
                blocked_labels.append("raw_transcript_storage_requested")
            elif key in {"raw_response_storage_requested"}:
                blocked_labels.append("raw_response_storage_requested")
            elif key in {"provider_model_output_requested"}:
                blocked_labels.append("provider_model_output_requested")
            elif key in {"dot_weslr_requested", "private_memory_scope_requested"}:
                blocked_labels.append("dot_weslr_requested")
            elif key in {"raw_private_data_requested", "live_user_content_requested", "hidden_material_requested", "benchmark_material_requested"}:
                blocked_labels.append("raw_private_content_requested")
            else:
                blocked_labels.append("raw_private_content_requested")

    authority_flag_fields = [
        "official_claim_allowed",
        "public_claim_allowed",
        "turing_claim_allowed",
        "intelligence_claim_allowed",
        "certification_claim_allowed",
        "public_readiness_claim_allowed",
        "voice_readiness_claim_allowed",
        "live_user_safety_readiness_claim_allowed",
        "benchmark_score_allowed",
        "model_superiority_allowed",
        "runtime_authority_allowed",
        "voice_authority_allowed",
        "unknown_engine_authority_allowed",
        "final_answer_authority_allowed",
        "user_facing_prose_authority_allowed",
        "public_live_authority_allowed",
        "public_ux_authority_allowed",
        "live_runtime_authority_allowed",
        "model_call_authority_allowed",
        "search_call_authority_allowed",
        "advisor_call_authority_allowed",
        "raw_persistence_allowed",
        "private_memory_allowed",
        "automatic_lesson_promotion_allowed",
    ]
    for field in authority_flag_fields:
        if _safe_bool(normalized_case.get(field)):
            if field in {"official_claim_allowed", "public_claim_allowed"}:
                blocked_labels.append("official_claim_requested")
            elif field in {"turing_claim_allowed"}:
                blocked_labels.append("turing_claim_requested")
            elif field in {"intelligence_claim_allowed"}:
                blocked_labels.append("intelligence_claim_requested")
            elif field in {"certification_claim_allowed"}:
                blocked_labels.append("certification_claim_requested")
            elif field in {"public_readiness_claim_allowed"}:
                blocked_labels.append("public_readiness_requested")
            elif field in {"voice_readiness_claim_allowed"}:
                blocked_labels.append("voice_readiness_requested")
            elif field in {"live_user_safety_readiness_claim_allowed"}:
                blocked_labels.append("live_user_safety_readiness_requested")
            elif field in {"benchmark_score_allowed"}:
                blocked_labels.append("benchmark_score_requested")
            elif field in {"model_superiority_allowed"}:
                blocked_labels.append("model_superiority_requested")
            elif field in {"runtime_authority_allowed", "live_runtime_authority_allowed", "public_live_authority_allowed"}:
                blocked_labels.append("runtime_authority_requested")
            elif field in {"voice_authority_allowed", "public_ux_authority_allowed", "user_facing_prose_authority_allowed"}:
                blocked_labels.append("voice_authority_requested")
            elif field in {"final_answer_authority_allowed"}:
                blocked_labels.append("final_answer_authority_requested")
            elif field in {"unknown_engine_authority_allowed"}:
                blocked_labels.append("unknown_engine_authority_requested")
            elif field in {"raw_persistence_allowed", "private_memory_allowed"}:
                blocked_labels.append("raw_persistence_requested")
            elif field in {"model_call_authority_allowed", "search_call_authority_allowed", "advisor_call_authority_allowed"}:
                blocked_labels.append("unknown_authority_flag")
            elif field in {"automatic_lesson_promotion_allowed"}:
                blocked_labels.append("automatic_lesson_promotion_requested")
            else:
                blocked_labels.append("unknown_authority_flag")

    unknown_engine_roles, unknown_engine_block_labels = _validate_unknown_engine_roles(normalized_case.get("unknown_engine_roles"))
    blocked_labels.extend(unknown_engine_block_labels)

    allowed = not blocked_labels
    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "case_type": CASE_TYPE_V1,
        "case_status": "valid" if allowed else "blocked",
        "valid": allowed,
        "blocked": not allowed,
        "blocked_labels": _unique_sorted(blocked_labels),
        "errors": _unique_sorted(errors),
        "case_id": case_id,
        "case_family": case_family,
        "source_type": source_type,
        "source_label": source_label,
        "registry_record_id": registry_record_id,
        "expected_result_label": expected_result_label,
        "expected_dimension_labels": expected_dimension_labels,
        "allowed_execution_mode": allowed_execution_mode,
        "operator_review_required": operator_review_required,
        "unknown_engine_roles": unknown_engine_roles,
        "denied_authority_flags": _collect_authority_flags(normalized_case),
        "normalized_case": normalized_case,
    }


def build_human_conversation_evaluator_plan_v1(
    case: Mapping[str, Any] | None,
    validation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a non-executing conversation evaluator plan."""

    rec = _as_mapping(case)
    val = _as_mapping(validation) if validation is not None else validate_human_conversation_evaluator_case_v1(rec)
    valid = _safe_bool(val.get("valid"))
    blocked_labels = _unique_sorted(val.get("blocked_labels") or [])
    execution_mode = _safe_str(val.get("allowed_execution_mode") or rec.get("allowed_execution_mode"))

    if not valid:
        plan_status = "blocked"
    elif execution_mode == "future_controlled_internal_execution":
        plan_status = "pending_future_controlled_execution"
    else:
        plan_status = "pending_operator_review"

    phases = [
        {"phase_label": "case_validation", "phase_name": "case_validation", "phase_status": "complete" if valid else "blocked"},
        {"phase_label": "source_registry_gate", "phase_name": "source_registry_gate", "phase_status": "complete" if valid else "blocked"},
        {"phase_label": "non_executing_plan", "phase_name": "non_executing_plan", "phase_status": "pending" if valid else "blocked"},
        {"phase_label": "future_separately_approved_controlled_execution", "phase_name": "future_separately_approved_controlled_execution", "phase_status": "future_only" if valid else "blocked"},
        {"phase_label": "observation_normalization", "phase_name": "observation_normalization", "phase_status": "pending" if valid else "blocked"},
        {"phase_label": "operator_review", "phase_name": "operator_review", "phase_status": "pending" if valid else "blocked"},
    ]

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "plan_type": PLAN_TYPE_V1,
        "plan_status": plan_status,
        "case_status": val.get("case_status", "blocked"),
        "valid": valid,
        "blocked": not valid,
        "should_execute": False,
        "execution_callable": None,
        "controlled_execution_allowed": False,
        "operator_review_required": True,
        "case_id": _safe_str(val.get("case_id")),
        "case_family": _safe_str(val.get("case_family")),
        "source_type": _safe_str(val.get("source_type")),
        "source_label": _safe_str(val.get("source_label")),
        "registry_record_id": _safe_str(val.get("registry_record_id")),
        "expected_result_label": _safe_str(val.get("expected_result_label")),
        "expected_dimension_labels": _unique_sorted(val.get("expected_dimension_labels") or []),
        "blocked_labels": blocked_labels,
        "denied_authority_flags": _collect_authority_flags(val.get("normalized_case") or {}),
        "phases": phases,
    }


def normalize_human_conversation_evaluator_observation_v1(
    observation: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Normalize an observation using metadata labels only."""

    obs = _as_mapping(observation)
    result_label = _safe_str(obs.get("result_label"))
    dimension_labels = _safe_list(obs.get("dimension_labels"))
    gap_labels = _safe_list(obs.get("gap_labels"))
    predicted_labels = _safe_list(obs.get("predicted_labels"))
    observed_labels = _safe_list(obs.get("observed_labels"))
    blocked_labels = _safe_list(obs.get("blocked_labels"))
    denied_authority_flags = _safe_list(obs.get("denied_authority_flags"))
    block_reason_labels: list[str] = []

    if result_label and result_label not in RESULT_LABELS_V1:
        block_reason_labels.append("unknown_result_label")
        result_label = "blocked_by_runtime_boundary"
    elif not result_label:
        result_label = "needs_operator_review"

    if dimension_labels:
        unknown_dimensions = [label for label in dimension_labels if label not in DIMENSION_LABELS_V1]
        if unknown_dimensions:
            block_reason_labels.append("unknown_dimension_label")
            dimension_labels = [label for label in dimension_labels if label in DIMENSION_LABELS_V1]

    raw_transcript_present = bool(_safe_str(obs.get("raw_transcript")) or _safe_str(obs.get("transcript_text")) or _safe_str(obs.get("live_chat_text")) or _safe_str(obs.get("conversation_text")))
    raw_response_text_present = bool(_safe_str(obs.get("raw_response_text")) or _safe_str(obs.get("response_text")) or _safe_str(obs.get("raw_text")))
    if raw_transcript_present:
        block_reason_labels.append("raw_transcript_provided")
    if raw_response_text_present:
        block_reason_labels.append("raw_response_text_provided")

    raw_private_requested = any(
        _safe_bool(obs.get(key))
        for key in (
            "raw_transcript_requested",
            "raw_transcript_storage_requested",
            "raw_response_storage_requested",
            "provider_model_output_requested",
            "raw_private_data_requested",
            "live_user_content_requested",
            "hidden_material_requested",
            "benchmark_material_requested",
            "dot_weslr_requested",
            "private_memory_scope_requested",
        )
    )
    if raw_private_requested:
        if _safe_bool(obs.get("provider_model_output_requested")):
            block_reason_labels.append("provider_model_output_requested")
        elif _safe_bool(obs.get("raw_transcript_storage_requested")):
            block_reason_labels.append("raw_transcript_storage_requested")
        elif _safe_bool(obs.get("raw_response_storage_requested")):
            block_reason_labels.append("raw_response_storage_requested")
        elif _safe_bool(obs.get("dot_weslr_requested")) or _safe_bool(obs.get("private_memory_scope_requested")):
            block_reason_labels.append("dot_weslr_requested")
        else:
            block_reason_labels.append("raw_private_content_requested")

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "observation_type": OBSERVATION_TYPE_V1,
        "observation_status": "blocked_by_runtime_boundary" if block_reason_labels else (result_label or "needs_operator_review"),
        "result_label": result_label,
        "dimension_labels": dimension_labels,
        "gap_labels": gap_labels,
        "predicted_labels": predicted_labels,
        "observed_labels": observed_labels,
        "blocked_labels": _unique_sorted(blocked_labels + block_reason_labels),
        "denied_authority_flags": _unique_sorted(denied_authority_flags),
        "raw_transcript_present": raw_transcript_present,
        "raw_transcript_retained": False,
        "raw_transcript_redacted": raw_transcript_present,
        "raw_response_text_present": raw_response_text_present,
        "raw_response_text_retained": False,
        "raw_response_text_redacted": raw_response_text_present,
        "final_answer_authority": False,
        "user_facing_prose_authority": False,
        "live_runtime_authority": False,
        "public_live_authority": False,
        "official_claims": False,
    }


def build_human_conversation_evaluator_result_packet_v1(
    case: Mapping[str, Any] | None,
    validation: Mapping[str, Any] | None,
    plan: Mapping[str, Any] | None,
    observation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a safe operator review packet."""

    rec = _as_mapping(case)
    val = _as_mapping(validation)
    pln = _as_mapping(plan)
    obs = normalize_human_conversation_evaluator_observation_v1(observation) if observation is not None else {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "observation_type": OBSERVATION_TYPE_V1,
        "observation_status": "needs_operator_review",
        "result_label": "needs_operator_review",
        "dimension_labels": [],
        "gap_labels": [],
        "predicted_labels": [],
        "observed_labels": [],
        "blocked_labels": [],
        "denied_authority_flags": [],
        "raw_transcript_present": False,
        "raw_transcript_retained": False,
        "raw_transcript_redacted": False,
        "raw_response_text_present": False,
        "raw_response_text_retained": False,
        "raw_response_text_redacted": False,
        "final_answer_authority": False,
        "user_facing_prose_authority": False,
        "live_runtime_authority": False,
        "public_live_authority": False,
        "official_claims": False,
    }

    blocked_labels = _unique_sorted(
        list(val.get("blocked_labels") or [])
        + list(pln.get("blocked_labels") or [])
        + list(obs.get("blocked_labels") or [])
    )
    denied_authority_flags = _unique_sorted(
        list(val.get("denied_authority_flags") or [])
        + list(pln.get("denied_authority_flags") or [])
        + list(obs.get("denied_authority_flags") or [])
    )
    packet_status = "blocked" if blocked_labels else _safe_str(pln.get("plan_status") or "pending_operator_review")

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "packet_type": RESULT_PACKET_TYPE_V1,
        "packet_status": packet_status,
        "validation_summary": {
            "case_status": _safe_str(val.get("case_status") or "blocked"),
            "valid": _safe_bool(val.get("valid")),
            "blocked": _safe_bool(val.get("blocked")),
            "blocked_label_count": len(val.get("blocked_labels") or []),
        },
        "execution_plan_summary": {
            "plan_status": _safe_str(pln.get("plan_status") or "blocked"),
            "should_execute": False,
            "controlled_execution_allowed": False,
            "phase_count": len(pln.get("phases") or []),
        },
        "observation_summary": {
            "observation_status": _safe_str(obs.get("observation_status") or "needs_operator_review"),
            "result_label": _safe_str(obs.get("result_label") or "needs_operator_review"),
            "raw_transcript_present": _safe_bool(obs.get("raw_transcript_present")),
            "raw_transcript_retained": False,
            "raw_transcript_redacted": _safe_bool(obs.get("raw_transcript_redacted")),
            "raw_response_text_present": _safe_bool(obs.get("raw_response_text_present")),
            "raw_response_text_retained": False,
            "raw_response_text_redacted": _safe_bool(obs.get("raw_response_text_redacted")),
        },
        "blocked_labels": blocked_labels,
        "denied_authority_flags": denied_authority_flags,
        "case_id": _safe_str(val.get("case_id") or rec.get("case_id")),
        "case_family": _safe_str(val.get("case_family") or rec.get("case_family")),
        "source_type": _safe_str(val.get("source_type") or rec.get("source_type")),
        "source_label": _safe_str(val.get("source_label") or rec.get("source_label")),
        "registry_record_id": _safe_str(val.get("registry_record_id") or rec.get("registry_record_id")),
        "final_answer_authority": False,
        "user_facing_prose_authority": False,
        "live_runtime_authority": False,
        "public_live_authority": False,
        "official_claims": False,
        "operator_review_required": True,
    }


def validate_human_conversation_evaluator_batch_v1(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate multiple cases while preserving per-case results."""

    results = [validate_human_conversation_evaluator_case_v1(record) for record in records]
    aggregate_blocked_labels = _unique_sorted(label for result in results for label in result.get("blocked_labels", []))
    aggregate_denied_authority_flags = _unique_sorted(
        flag for result in results for flag in result.get("denied_authority_flags", [])
    )
    return {
        "valid": all(result["valid"] for result in results) if results else True,
        "total_records": len(results),
        "valid_records": sum(1 for result in results if result["valid"]),
        "blocked_records": sum(1 for result in results if result["blocked"]),
        "aggregate_blocked_labels": aggregate_blocked_labels,
        "aggregate_denied_authority_flags": aggregate_denied_authority_flags,
        "records": results,
    }


def summarize_human_conversation_evaluator_v1(value: Mapping[str, Any] | Iterable[Any]) -> dict[str, Any]:
    """Return a safe metadata-only summary of cases or validation results."""

    if isinstance(value, Mapping) and "records" in value:
        items = value["records"]
    else:
        items = value

    normalized_results: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, Mapping) and {"valid", "blocked", "normalized_case"}.issubset(set(item.keys())):
            normalized_results.append(validate_human_conversation_evaluator_case_v1(item.get("normalized_case") or {}))
        elif isinstance(item, Mapping) and {"valid", "blocked", "blocked_labels"}.issubset(set(item.keys())):
            normalized_results.append(item)
        else:
            normalized_results.append(validate_human_conversation_evaluator_case_v1(item))

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
