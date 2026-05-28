"""Metadata-only helpers for WESLR internal task corpus execution path v1.

This module is intentionally pure, deterministic, and fail-closed.
It converts approved task-corpus metadata into validation results, non-executing
plans, adapter preflight metadata mirrors, observation metadata, and operator
review packets.

It does not perform file I/O, network I/O, subprocess execution, runtime/chat
wiring, live response routing, provider/model/search/advisor calls, dot-weslr
IO, or any official scoring work.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, is_dataclass
from typing import Any, Iterable, Mapping

from weslr.internal_evaluation_dataset_registry import (
    ANSWER_KEY_POLICY_LABELS_V1,
    CONTAMINATION_RISK_LABELS_V1,
    EXPECTED_OUTPUT_POLICY_LABELS_V1,
    SOURCE_TYPE_LABELS_V1,
    TEST_FAMILY_LABELS_V1,
)

HELPER_TYPE_V1 = "weslr_internal_task_corpus_execution_path_helpers_v1"
BOUNDARY_TYPE_V1 = "internal_task_corpus_execution_path_v1"

ALLOWED_TASK_FAMILIES_V1 = set(TEST_FAMILY_LABELS_V1)
ALLOWED_SOURCE_TYPES_V1 = {
    "synthetic_weslr_created",
    "generated_mutation_from_allowed_source",
}
BLOCKED_SOURCE_TYPES_V1 = set(SOURCE_TYPE_LABELS_V1) - ALLOWED_SOURCE_TYPES_V1

ALLOWED_CONTAMINATION_RISK_LABELS_V1 = set(CONTAMINATION_RISK_LABELS_V1)
ALLOWED_EXPECTED_OUTPUT_POLICY_LABELS_V1 = set(EXPECTED_OUTPUT_POLICY_LABELS_V1) - {"blocked"}
ALLOWED_ANSWER_KEY_POLICY_LABELS_V1 = set(ANSWER_KEY_POLICY_LABELS_V1) - {"blocked"}
ALLOWED_EXECUTION_MODE_LABELS_V1 = {
    "metadata_only",
    "future_controlled_internal_execution",
}
ALLOWED_PLAN_STATUS_LABELS_V1 = {
    "blocked",
    "pending_operator_review",
    "pending_future_controlled_execution",
}

PHASE_A_REGISTRY_VALIDATION_V1 = "phase_a_registry_validation"
PHASE_B_CORPUS_RECORD_VALIDATION_V1 = "phase_b_corpus_record_validation"
PHASE_C_ADAPTER_PREFLIGHT_V1 = "phase_c_adapter_preflight"
PHASE_D_NON_EXECUTING_CALL_PLAN_V1 = "phase_d_non_executing_call_plan"
PHASE_E_FUTURE_SEPARATELY_APPROVED_CONTROLLED_EXECUTION_V1 = (
    "phase_e_future_separately_approved_controlled_execution"
)
PHASE_F_OBSERVATION_NORMALIZATION_V1 = "phase_f_observation_normalization"
PHASE_G_GAP_REPORT_PACKET_V1 = "phase_g_gap_report_packet"
PHASE_H_OPERATOR_REVIEW_V1 = "phase_h_operator_review"

PHASE_LABELS_V1 = {
    PHASE_A_REGISTRY_VALIDATION_V1,
    PHASE_B_CORPUS_RECORD_VALIDATION_V1,
    PHASE_C_ADAPTER_PREFLIGHT_V1,
    PHASE_D_NON_EXECUTING_CALL_PLAN_V1,
    PHASE_E_FUTURE_SEPARATELY_APPROVED_CONTROLLED_EXECUTION_V1,
    PHASE_F_OBSERVATION_NORMALIZATION_V1,
    PHASE_G_GAP_REPORT_PACKET_V1,
    PHASE_H_OPERATOR_REVIEW_V1,
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
    "official_claim_allowed",
    "public_claim_allowed",
    "raw_persistence_authority",
    "private_memory_authority",
    "unknown_engine_authority",
    "automatic_lesson_promotion_authority",
}

ALLOWED_UNKNOWN_ENGINE_ROLES_V1 = {
    "propose_synthetic_task_variants",
    "predict_likely_failure_zones",
    "compare_predicted_vs_observed_labels",
    "compress_repeated_gap_patterns",
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

BLOCKED_LABELS_V1 = {
    "missing_task_id",
    "missing_task_family",
    "missing_source_type",
    "missing_registry_record_id",
    "missing_contamination_risk",
    "missing_expected_output_policy",
    "missing_answer_key_policy",
    "missing_task_prompt_descriptor",
    "missing_allowed_execution_mode",
    "missing_operator_review_requirement",
    "unknown_task_family",
    "unknown_source_type",
    "blocked_source_type",
    "unknown_contamination_risk",
    "unknown_expected_output_policy",
    "unknown_answer_key_policy",
    "blocked_answer_key_policy",
    "unknown_execution_mode",
    "blocked_execution_label",
    "unknown_blocked_execution_label",
    "operator_review_not_required",
    "official_claim_requested",
    "public_claim_requested",
    "runtime_authority_requested",
    "voice_authority_requested",
    "final_answer_authority_requested",
    "public_live_authority_requested",
    "public_ux_authority_requested",
    "live_runtime_authority_requested",
    "model_call_authority_requested",
    "search_call_authority_requested",
    "advisor_call_authority_requested",
    "benchmark_submission_requested",
    "raw_persistence_requested",
    "private_memory_requested",
    "unknown_engine_authority_requested",
    "automatic_lesson_promotion_requested",
    "dot_weslr_requested",
    "private_memory_scope_requested",
    "hidden_material_requested",
    "benchmark_material_requested",
    "live_user_content_requested",
    "raw_private_content_requested",
    "raw_response_text_provided",
    "unknown_unknown_engine_role",
    "forbidden_unknown_engine_role",
    "unknown_authority_flag",
    "invalid_request_shape",
}

CORPUS_RECORD_TYPE_V1 = "internal_task_corpus_record_v1"
EXECUTION_PLAN_TYPE_V1 = "internal_task_corpus_execution_plan_v1"
ADAPTER_PREFLIGHT_PACKET_TYPE_V1 = "internal_task_corpus_adapter_preflight_packet_v1"
OBSERVATION_TYPE_V1 = "internal_task_corpus_observation_v1"
RESULT_PACKET_TYPE_V1 = "internal_task_corpus_result_packet_v1"


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
    return sorted(set(_safe_list(list(labels) if not isinstance(labels, (str, bytes)) else [labels])))


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return f"[redacted:{type(value).__name__}]"


def to_internal_task_corpus_execution_path_json_safe_v1(value: Any) -> Any:
    """Convert supported corpus structures to deterministic JSON-safe data."""

    return _json_safe(value)


def _descriptor_from_task(task: Mapping[str, Any], task_family: str) -> str:
    descriptor = _safe_str(
        task.get("task_prompt_redacted_or_synthetic_descriptor")
        or task.get("task_prompt_descriptor")
        or task.get("synthetic_descriptor")
    )
    if descriptor:
        return descriptor
    if any(_safe_str(task.get(key)) for key in ("task_prompt", "prompt", "raw_prompt", "task_text")):
        return "[redacted:task_prompt]"
    return f"[synthetic:{task_family or 'unknown_task_family'}]"


def _normalize_unknown_engine_roles(value: Any) -> list[str]:
    return _safe_list(value)


def build_internal_task_corpus_record_v1(
    task_item: Mapping[str, Any] | None = None,
    registry_item: Mapping[str, Any] | None = None,
    session_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a metadata-only internal task corpus record."""

    task = _as_mapping(task_item)
    registry = _as_mapping(registry_item)
    context = _as_mapping(session_context)

    task_family = _safe_str(task.get("task_family") or registry.get("task_family") or task.get("family"))
    source_type = _safe_str(task.get("source_type") or registry.get("source_type") or task.get("source") or registry.get("source"))
    registry_record_id = _safe_str(
        task.get("registry_record_id") or registry.get("registry_record_id") or registry.get("record_id") or registry.get("id")
    )
    task_id = _safe_str(task.get("task_id") or task.get("id") or registry.get("task_id") or registry.get("id") or registry_record_id)

    contamination_risk = _safe_str(task.get("contamination_risk") or registry.get("contamination_risk") or "unknown")
    expected_output_policy = _safe_str(task.get("expected_output_policy") or registry.get("expected_output_policy") or "metadata_only")
    answer_key_policy = _safe_str(task.get("answer_key_policy") or registry.get("answer_key_policy") or "metadata_only")
    allowed_execution_mode = _safe_str(task.get("allowed_execution_mode") or registry.get("allowed_execution_mode") or "metadata_only")
    blocked_execution_labels = _unique_sorted(
        task.get("blocked_execution_labels") or registry.get("blocked_execution_labels") or []
    )
    operator_review_required = True if task.get("operator_review_required") is None and registry.get("operator_review_required") is None else _safe_bool(
        task.get("operator_review_required") if task.get("operator_review_required") is not None else registry.get("operator_review_required")
    )

    record = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "record_type": CORPUS_RECORD_TYPE_V1,
        "record_status": "draft",
        "task_id": task_id,
        "task_family": task_family,
        "source_type": source_type,
        "registry_record_id": registry_record_id,
        "contamination_risk": contamination_risk,
        "expected_output_policy": expected_output_policy,
        "answer_key_policy": answer_key_policy,
        "task_prompt_redacted_or_synthetic_descriptor": _descriptor_from_task(task, task_family),
        "allowed_execution_mode": allowed_execution_mode,
        "blocked_execution_labels": blocked_execution_labels,
        "operator_review_required": operator_review_required,
        "official_claim_allowed": False,
        "public_claim_allowed": False,
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
        "unknown_engine_roles": _normalize_unknown_engine_roles(task.get("unknown_engine_roles") or registry.get("unknown_engine_roles")),
        "raw_private_data_requested": _safe_bool(task.get("raw_private_data_requested") or registry.get("raw_private_data_requested")),
        "hidden_material_requested": _safe_bool(task.get("hidden_material_requested") or registry.get("hidden_material_requested")),
        "benchmark_material_requested": _safe_bool(task.get("benchmark_material_requested") or registry.get("benchmark_material_requested")),
        "live_user_content_requested": _safe_bool(task.get("live_user_content_requested") or registry.get("live_user_content_requested")),
        "dot_weslr_requested": _safe_bool(task.get("dot_weslr_requested") or registry.get("dot_weslr_requested")),
        "private_memory_scope_requested": _safe_bool(task.get("private_memory_scope_requested") or registry.get("private_memory_scope_requested")),
        "corpus_context": {
            "repo_root": _safe_str(context.get("repo_root") or task.get("repo_root") or registry.get("repo_root")),
            "session_key": _safe_str(context.get("session_key") or task.get("session_key") or registry.get("session_key")),
        },
        "source_descriptor": _safe_str(task.get("source_descriptor") or registry.get("source_descriptor") or ""),
        "task_labels": _safe_list(task.get("task_labels") or registry.get("task_labels")),
        "source_tags": _safe_list(task.get("source_tags") or registry.get("source_tags")),
    }

    return to_internal_task_corpus_execution_path_json_safe_v1(record)


def _collect_authority_flags(record: Mapping[str, Any]) -> list[str]:
    flags = []
    for flag in DENIED_AUTHORITY_FLAGS_V1:
        if _safe_bool(record.get(flag)):
            flags.append(flag)
    return _unique_sorted(flags)


def _validate_unknown_engine_roles(roles: Any) -> tuple[list[str], list[str]]:
    normalized = _normalize_unknown_engine_roles(roles)
    blocked: list[str] = []
    for role in normalized:
        if role in FORBIDDEN_UNKNOWN_ENGINE_ROLES_V1:
            blocked.append("forbidden_unknown_engine_role")
        elif role not in ALLOWED_UNKNOWN_ENGINE_ROLES_V1:
            blocked.append("unknown_unknown_engine_role")
    return normalized, _unique_sorted(blocked)


def validate_internal_task_corpus_record_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a single corpus record and fail closed on unsafe input."""

    normalized_record = to_internal_task_corpus_execution_path_json_safe_v1(record)
    if not isinstance(normalized_record, dict):
        normalized_record = {}

    blocked_labels: list[str] = []
    errors: list[str] = []

    required_fields = [
        "task_id",
        "task_family",
        "source_type",
        "registry_record_id",
        "contamination_risk",
        "expected_output_policy",
        "answer_key_policy",
        "task_prompt_redacted_or_synthetic_descriptor",
        "allowed_execution_mode",
        "blocked_execution_labels",
        "operator_review_required",
        "official_claim_allowed",
        "public_claim_allowed",
        "runtime_authority_allowed",
        "voice_authority_allowed",
        "unknown_engine_authority_allowed",
    ]
    for field in required_fields:
        if field not in normalized_record or normalized_record.get(field) in (None, "", [], {}) and field != "blocked_execution_labels":
            blocked_labels.append(f"missing_{field}")
            errors.append(f"missing field: {field}")

    task_id = _safe_str(normalized_record.get("task_id"))
    task_family = _safe_str(normalized_record.get("task_family"))
    source_type = _safe_str(normalized_record.get("source_type"))
    registry_record_id = _safe_str(normalized_record.get("registry_record_id"))
    contamination_risk = _safe_str(normalized_record.get("contamination_risk"))
    expected_output_policy = _safe_str(normalized_record.get("expected_output_policy"))
    answer_key_policy = _safe_str(normalized_record.get("answer_key_policy"))
    allowed_execution_mode = _safe_str(normalized_record.get("allowed_execution_mode"))
    blocked_execution_labels = _safe_list(normalized_record.get("blocked_execution_labels"))
    operator_review_required = _safe_bool(normalized_record.get("operator_review_required"))

    if not task_id:
        blocked_labels.append("missing_task_id")
    if not task_family:
        blocked_labels.append("missing_task_family")
    elif task_family not in ALLOWED_TASK_FAMILIES_V1:
        blocked_labels.append("unknown_task_family")
    if not source_type:
        blocked_labels.append("missing_source_type")
    elif source_type in BLOCKED_SOURCE_TYPES_V1:
        blocked_labels.append("blocked_source_type")
    elif source_type not in ALLOWED_SOURCE_TYPES_V1:
        blocked_labels.append("unknown_source_type")
    if not registry_record_id:
        blocked_labels.append("missing_registry_record_id")
    if not contamination_risk:
        blocked_labels.append("missing_contamination_risk")
    elif contamination_risk not in ALLOWED_CONTAMINATION_RISK_LABELS_V1:
        blocked_labels.append("unknown_contamination_risk")
    if not expected_output_policy:
        blocked_labels.append("missing_expected_output_policy")
    elif expected_output_policy not in ALLOWED_EXPECTED_OUTPUT_POLICY_LABELS_V1:
        blocked_labels.append("unknown_expected_output_policy")
    if not answer_key_policy:
        blocked_labels.append("missing_answer_key_policy")
    elif answer_key_policy == "blocked":
        blocked_labels.append("blocked_answer_key_policy")
    elif answer_key_policy not in ALLOWED_ANSWER_KEY_POLICY_LABELS_V1:
        blocked_labels.append("unknown_answer_key_policy")
    if not _safe_str(normalized_record.get("task_prompt_redacted_or_synthetic_descriptor")):
        blocked_labels.append("missing_task_prompt_descriptor")
    if not allowed_execution_mode:
        blocked_labels.append("missing_allowed_execution_mode")
    elif allowed_execution_mode not in ALLOWED_EXECUTION_MODE_LABELS_V1:
        blocked_labels.append("unknown_execution_mode")
    if not operator_review_required:
        blocked_labels.append("operator_review_not_required")

    if blocked_execution_labels:
        for label in blocked_execution_labels:
            if label not in BLOCKED_LABELS_V1:
                blocked_labels.append("unknown_blocked_execution_label")
                break

    raw_content_keys = {
        "raw_private_data_requested",
        "hidden_material_requested",
        "benchmark_material_requested",
        "live_user_content_requested",
        "private_memory_scope_requested",
        "dot_weslr_requested",
        "raw_response_text",
        "raw_response_text_requested",
        "raw_text",
        "prompt",
        "task_prompt",
        "answer_key",
        "final_answer",
        "response_text",
        "live_user_text",
        "benchmark_text",
        "hidden_text",
        "private_text",
    }
    for key in raw_content_keys:
        if _safe_bool(normalized_record.get(key)):
            if key in {"dot_weslr_requested", "private_memory_scope_requested"}:
                blocked_labels.append("dot_weslr_requested")
            else:
                blocked_labels.append("raw_private_content_requested")

    authority_flag_fields = [
        "official_claim_allowed",
        "public_claim_allowed",
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
        if _safe_bool(normalized_record.get(field)):
            if field in {"official_claim_allowed", "public_claim_allowed"}:
                blocked_labels.append("official_claim_requested")
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

    unknown_engine_roles, unknown_engine_block_labels = _validate_unknown_engine_roles(normalized_record.get("unknown_engine_roles"))
    blocked_labels.extend(unknown_engine_block_labels)

    allowed = not blocked_labels
    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "record_type": CORPUS_RECORD_TYPE_V1,
        "record_status": "valid" if allowed else "blocked",
        "valid": allowed,
        "blocked": not allowed,
        "blocked_labels": _unique_sorted(blocked_labels),
        "errors": _unique_sorted(errors),
        "task_id": task_id,
        "task_family": task_family,
        "source_type": source_type,
        "registry_record_id": registry_record_id,
        "contamination_risk": contamination_risk,
        "expected_output_policy": expected_output_policy,
        "answer_key_policy": answer_key_policy,
        "allowed_execution_mode": allowed_execution_mode,
        "operator_review_required": operator_review_required,
        "unknown_engine_roles": unknown_engine_roles,
        "denied_authority_flags": _collect_authority_flags(normalized_record),
        "normalized_record": normalized_record,
    }


def build_internal_task_corpus_execution_plan_v1(
    record: Mapping[str, Any] | None,
    validation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a non-executing multi-phase plan."""

    rec = _as_mapping(record)
    val = _as_mapping(validation) if validation is not None else validate_internal_task_corpus_record_v1(rec)
    valid = _safe_bool(val.get("valid"))
    blocked_labels = _unique_sorted(list(val.get("blocked_labels") or []))
    execution_mode = _safe_str(val.get("allowed_execution_mode") or rec.get("allowed_execution_mode"))

    if not valid:
        plan_status = "blocked"
    elif execution_mode == "future_controlled_internal_execution":
        plan_status = "pending_future_controlled_execution"
    else:
        plan_status = "pending_operator_review"

    phases = [
        {"phase_label": PHASE_A_REGISTRY_VALIDATION_V1, "phase_name": "registry_validation", "phase_status": "complete" if valid else "blocked"},
        {"phase_label": PHASE_B_CORPUS_RECORD_VALIDATION_V1, "phase_name": "corpus_record_validation", "phase_status": "complete" if valid else "blocked"},
        {"phase_label": PHASE_C_ADAPTER_PREFLIGHT_V1, "phase_name": "adapter_preflight", "phase_status": "pending" if valid else "blocked"},
        {"phase_label": PHASE_D_NON_EXECUTING_CALL_PLAN_V1, "phase_name": "non_executing_call_plan", "phase_status": "pending" if valid else "blocked"},
        {"phase_label": PHASE_E_FUTURE_SEPARATELY_APPROVED_CONTROLLED_EXECUTION_V1, "phase_name": "future_separately_approved_controlled_execution", "phase_status": "future_only" if valid else "blocked"},
        {"phase_label": PHASE_F_OBSERVATION_NORMALIZATION_V1, "phase_name": "observation_normalization", "phase_status": "pending" if valid else "blocked"},
        {"phase_label": PHASE_G_GAP_REPORT_PACKET_V1, "phase_name": "gap_report_packet", "phase_status": "pending" if valid else "blocked"},
        {"phase_label": PHASE_H_OPERATOR_REVIEW_V1, "phase_name": "operator_review", "phase_status": "pending" if valid else "blocked"},
    ]

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "plan_type": EXECUTION_PLAN_TYPE_V1,
        "plan_status": plan_status,
        "record_status": val.get("record_status", "blocked"),
        "valid": valid,
        "blocked": not valid,
        "should_execute": False,
        "execution_callable": None,
        "controlled_execution_allowed": False,
        "operator_review_required": True,
        "task_id": _safe_str(val.get("task_id")),
        "task_family": _safe_str(val.get("task_family")),
        "source_type": _safe_str(val.get("source_type")),
        "registry_record_id": _safe_str(val.get("registry_record_id")),
        "blocked_labels": blocked_labels,
        "denied_authority_flags": _collect_authority_flags(val.get("normalized_record") or {}),
        "phases": phases,
    }


def build_internal_task_corpus_adapter_preflight_packet_v1(
    record: Mapping[str, Any] | None,
    validation: Mapping[str, Any] | None = None,
    execution_plan: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a metadata-only adapter preflight mirror packet."""

    rec = _as_mapping(record)
    val = _as_mapping(validation) if validation is not None else validate_internal_task_corpus_record_v1(rec)
    plan = _as_mapping(execution_plan) if execution_plan is not None else build_internal_task_corpus_execution_plan_v1(rec, val)
    valid = _safe_bool(val.get("valid"))
    blocked_labels = _unique_sorted(list(val.get("blocked_labels") or []))

    if not valid:
        packet_status = "blocked"
        preflight_status = "blocked"
    else:
        packet_status = "pending_operator_review"
        preflight_status = "pending_operator_review"

    source_type = _safe_str(val.get("source_type"))
    task_family = _safe_str(val.get("task_family"))
    adapter_rule_blocked_labels = []
    if source_type and source_type in BLOCKED_SOURCE_TYPES_V1:
        adapter_rule_blocked_labels.append("blocked_source_type")
    if task_family and task_family not in ALLOWED_TASK_FAMILIES_V1:
        adapter_rule_blocked_labels.append("unknown_task_family")

    blocked_labels = _unique_sorted(blocked_labels + adapter_rule_blocked_labels)
    packet_status = "blocked" if blocked_labels else packet_status
    preflight_status = "blocked" if blocked_labels else preflight_status

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "packet_type": ADAPTER_PREFLIGHT_PACKET_TYPE_V1,
        "packet_status": packet_status,
        "preflight_status": preflight_status,
        "callable_invocation_allowed": False,
        "live_call_allowed": False,
        "chat_responder_call_allowed": False,
        "model_call_allowed": False,
        "search_call_allowed": False,
        "advisor_call_allowed": False,
        "execution_callable": None,
        "blocked_labels": blocked_labels,
        "denied_authority_flags": _collect_authority_flags(val.get("normalized_record") or {}),
        "task_id": _safe_str(val.get("task_id")),
        "task_family": task_family,
        "source_type": source_type,
        "registry_record_id": _safe_str(val.get("registry_record_id")),
        "operator_review_required": True,
        "adapter_request_summary": {
            "task_family": task_family,
            "source_type": source_type,
            "registry_record_id": _safe_str(val.get("registry_record_id")),
            "callable_invocation_allowed": False,
            "live_call_allowed": False,
            "chat_responder_call_allowed": False,
        },
        "plan_summary": {
            "plan_status": _safe_str(plan.get("plan_status")),
            "should_execute": False,
            "execution_callable": None,
        },
    }


def normalize_internal_task_corpus_observation_v1(observation: Mapping[str, Any] | None) -> dict[str, Any]:
    """Normalize an observation using metadata labels only."""

    obs = _as_mapping(observation)
    result_label = _safe_str(obs.get("result_label"))
    gap_labels = _safe_list(obs.get("gap_labels"))
    predicted_labels = _safe_list(obs.get("predicted_labels"))
    observed_labels = _safe_list(obs.get("observed_labels"))
    blocked_labels = _safe_list(obs.get("blocked_labels"))
    denied_authority_flags = _safe_list(obs.get("denied_authority_flags"))
    block_reason_labels: list[str] = []

    allowed_result_labels = {
        "pass_internal_task_corpus",
        "partial_internal_task_corpus",
        "fail_internal_task_corpus",
        "blocked_by_boundary",
        "needs_operator_review",
        "inconclusive_internal_task_corpus",
    }
    if result_label and result_label not in allowed_result_labels:
        result_label = "blocked_by_boundary"
        block_reason_labels.append("unknown_result_label")

    raw_response_text_present = bool(_safe_str(obs.get("raw_response_text")))
    if raw_response_text_present:
        block_reason_labels.append("raw_response_text_provided")

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "observation_type": OBSERVATION_TYPE_V1,
        "observation_status": "blocked_by_boundary" if block_reason_labels else (result_label or "needs_operator_review"),
        "result_label": result_label or "needs_operator_review",
        "gap_labels": gap_labels,
        "predicted_labels": predicted_labels,
        "observed_labels": observed_labels,
        "blocked_labels": _unique_sorted(blocked_labels + block_reason_labels),
        "denied_authority_flags": _unique_sorted(denied_authority_flags),
        "raw_response_text_present": raw_response_text_present,
        "raw_response_text_retained": False,
        "raw_response_text_redacted": raw_response_text_present,
        "final_answer_authority": False,
        "user_facing_prose_authority": False,
        "live_runtime_authority": False,
        "public_live_authority": False,
        "official_claims": False,
    }


def build_internal_task_corpus_result_packet_v1(
    record: Mapping[str, Any] | None,
    validation: Mapping[str, Any] | None,
    execution_plan: Mapping[str, Any] | None,
    observation: Mapping[str, Any] | None = None,
    adapter_preflight_packet: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a safe operator review packet."""

    rec = _as_mapping(record)
    val = _as_mapping(validation)
    plan = _as_mapping(execution_plan)
    adapter_packet = _as_mapping(adapter_preflight_packet)
    obs = normalize_internal_task_corpus_observation_v1(observation) if observation is not None else {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "observation_type": OBSERVATION_TYPE_V1,
        "observation_status": "needs_operator_review",
        "result_label": "needs_operator_review",
        "gap_labels": [],
        "predicted_labels": [],
        "observed_labels": [],
        "blocked_labels": [],
        "denied_authority_flags": [],
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
        + list(plan.get("blocked_labels") or [])
        + list(adapter_packet.get("blocked_labels") or [])
        + list(obs.get("blocked_labels") or [])
    )
    denied_authority_flags = _unique_sorted(
        list(val.get("denied_authority_flags") or [])
        + list(plan.get("denied_authority_flags") or [])
        + list(adapter_packet.get("denied_authority_flags") or [])
        + list(obs.get("denied_authority_flags") or [])
    )

    packet_status = "blocked" if blocked_labels else _safe_str(plan.get("plan_status") or "pending_operator_review")

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "packet_type": RESULT_PACKET_TYPE_V1,
        "packet_status": packet_status,
        "validation_summary": {
            "record_status": _safe_str(val.get("record_status") or "blocked"),
            "valid": _safe_bool(val.get("valid")),
            "blocked": _safe_bool(val.get("blocked")),
            "blocked_label_count": len(val.get("blocked_labels") or []),
        },
        "execution_plan_summary": {
            "plan_status": _safe_str(plan.get("plan_status") or "blocked"),
            "should_execute": False,
            "controlled_execution_allowed": False,
            "phase_count": len(plan.get("phases") or []),
        },
        "adapter_preflight_summary": {
            "packet_status": _safe_str(adapter_packet.get("packet_status") or "blocked"),
            "preflight_status": _safe_str(adapter_packet.get("preflight_status") or "blocked"),
            "callable_invocation_allowed": False,
            "live_call_allowed": False,
            "chat_responder_call_allowed": False,
        },
        "observation_summary": {
            "observation_status": _safe_str(obs.get("observation_status") or "needs_operator_review"),
            "raw_response_text_present": _safe_bool(obs.get("raw_response_text_present")),
            "raw_response_text_retained": False,
            "raw_response_text_redacted": _safe_bool(obs.get("raw_response_text_redacted")),
        },
        "blocked_labels": blocked_labels,
        "denied_authority_flags": denied_authority_flags,
        "task_id": _safe_str(val.get("task_id") or rec.get("task_id")),
        "task_family": _safe_str(val.get("task_family") or rec.get("task_family")),
        "source_type": _safe_str(val.get("source_type") or rec.get("source_type")),
        "registry_record_id": _safe_str(val.get("registry_record_id") or rec.get("registry_record_id")),
        "final_answer_authority": False,
        "user_facing_prose_authority": False,
        "live_runtime_authority": False,
        "public_live_authority": False,
        "official_claims": False,
        "operator_review_required": True,
    }


def validate_internal_task_corpus_batch_v1(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate multiple corpus records while preserving per-record results."""

    results = [validate_internal_task_corpus_record_v1(record) for record in records]
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


def summarize_internal_task_corpus_execution_path_v1(value: Mapping[str, Any] | Iterable[Any]) -> dict[str, Any]:
    """Return a safe metadata-only summary of corpus records or validation results."""

    if isinstance(value, Mapping) and "records" in value:
        items = value["records"]
    else:
        items = value

    normalized_results: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, Mapping) and {"valid", "blocked", "normalized_record"}.issubset(set(item.keys())):
            normalized_results.append(
                validate_internal_task_corpus_record_v1(item.get("normalized_record") or {})
            )
        elif isinstance(item, Mapping) and {"valid", "blocked", "blocked_labels"}.issubset(set(item.keys())):
            normalized_results.append(item)
        else:
            normalized_results.append(validate_internal_task_corpus_record_v1(item))

    blocked_labels = _unique_sorted(label for result in normalized_results for label in result.get("blocked_labels", []))
    denied_authority_flags = _unique_sorted(
        flag for result in normalized_results for flag in result.get("denied_authority_flags", [])
    )
    task_family_counts: dict[str, int] = {}
    source_type_counts: dict[str, int] = {}
    plan_status_counts: dict[str, int] = {}
    for result in normalized_results:
        task_family = _safe_str(result.get("task_family") or "unknown")
        source_type = _safe_str(result.get("source_type") or "unknown")
        task_family_counts[task_family] = task_family_counts.get(task_family, 0) + 1
        source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
        plan_status = _safe_str(result.get("plan_status") or result.get("record_status") or "unknown")
        plan_status_counts[plan_status] = plan_status_counts.get(plan_status, 0) + 1

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "total_records": len(normalized_results),
        "valid_records": sum(1 for result in normalized_results if _safe_bool(result.get("valid"))),
        "blocked_records": sum(1 for result in normalized_results if _safe_bool(result.get("blocked"))),
        "blocked_label_count": len(blocked_labels),
        "blocked_labels": blocked_labels,
        "denied_authority_flags": denied_authority_flags,
        "task_family_counts": task_family_counts,
        "source_type_counts": source_type_counts,
        "plan_status_counts": plan_status_counts,
        "record_status_counts": {
            "valid": sum(1 for result in normalized_results if _safe_str(result.get("record_status")) == "valid"),
            "blocked": sum(1 for result in normalized_results if _safe_str(result.get("record_status")) == "blocked"),
        },
        "final_answer_authority": False,
        "user_facing_prose_authority": False,
        "live_runtime_authority": False,
        "public_live_authority": False,
        "official_claims": False,
    }
