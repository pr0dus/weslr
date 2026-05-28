"""Metadata-only helpers for WESLR internal task corpus controlled execution boundary v1.

This module is intentionally pure, deterministic, and fail-closed.
It models approved task-corpus execution requests, preflight validation, non-
executing plans, metadata observations, operator review packets, batch
validation, summaries, and JSON-safe conversion.

It does not perform file I/O, network I/O, subprocess execution, runtime/chat
wiring, live response routing, provider/model/search/advisor calls, dot-weslr
IO, or any official scoring work.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, is_dataclass
from typing import Any, Iterable, Mapping

HELPER_TYPE_V1 = "weslr_internal_task_corpus_controlled_execution_helpers_v1"
BOUNDARY_TYPE_V1 = "internal_task_corpus_controlled_execution_boundary_v1"
REQUEST_TYPE_V1 = "internal_task_corpus_controlled_execution_request_v1"
PLAN_TYPE_V1 = "internal_task_corpus_controlled_execution_plan_v1"
OBSERVATION_TYPE_V1 = "internal_task_corpus_controlled_execution_observation_v1"
RESULT_PACKET_TYPE_V1 = "internal_task_corpus_controlled_execution_result_packet_v1"

ALLOWED_SOURCE_CLASSES_V1 = {
    "public_open",
    "synthetic_weslr_created",
}

BLOCKED_SOURCE_CLASSES_V1 = {
    "private",
    "semi_private",
    "hidden",
    "unknown",
}

RESULT_LABELS_V1 = {
    "pass_internal_task_rehearsal",
    "partial_internal_task_rehearsal",
    "fail_internal_task_rehearsal",
    "inconclusive_internal_task_rehearsal",
    "blocked_by_source_governance",
    "blocked_by_privacy_boundary",
    "blocked_by_runtime_boundary",
    "blocked_by_adapter_preflight",
    "needs_operator_review",
}

PLAN_STATUS_LABELS_V1 = {
    "blocked",
    "pending_operator_review",
    "pending_future_controlled_execution",
}

ALLOWED_UNKNOWN_ENGINE_ROLES_V1 = {
    "predict_controlled_execution_failure_zones",
    "suggest_synthetic_task_variants",
    "compare_predicted_vs_observed_metadata_failures",
    "compress_repeated_failure_patterns",
}

FORBIDDEN_UNKNOWN_ENGINE_ROLES_V1 = {
    "authority",
    "scoring",
    "certification",
    "official judge",
    "official_judge",
    "future certainty",
    "source/license approval",
    "runtime/live control",
    "automatic self-modification",
}

BLOCKED_LABELS_V1 = {
    "missing_task_id",
    "missing_task_family",
    "missing_source_class",
    "missing_source_label",
    "missing_registry_record_id",
    "missing_registry_approval",
    "missing_execution_plan_preflight",
    "missing_adapter_preflight",
    "missing_operator_approval",
    "missing_result_artifact_metadata_only",
    "unknown_source_class",
    "blocked_source_class",
    "unknown_result_label",
    "unknown_unknown_engine_role",
    "forbidden_unknown_engine_role",
    "raw_private_data_requested",
    "raw_prompt_provided",
    "raw_response_text_provided",
    "raw_transcript_provided",
    "raw_context_provided",
    "raw_prompt_storage_requested",
    "raw_response_storage_requested",
    "raw_transcript_storage_requested",
    "raw_context_storage_requested",
    "dot_weslr_requested",
    "private_memory_scope_requested",
    "live_user_content_requested",
    "hidden_material_requested",
    "benchmark_material_requested",
    "provider_model_output_requested",
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
    "raw_persistence_requested",
    "private_memory_requested",
    "unknown_engine_authority_requested",
    "automatic_lesson_promotion_requested",
    "invalid_request_shape",
    "source_registry_missing",
    "source_registry_not_approved",
    "operator_approval_not_present",
    "result_artifact_not_metadata_only",
}

DENIED_AUTHORITY_FLAGS_V1 = {
    "public_live_authority",
    "public_live_authority_requested",
    "public_ux_authority",
    "public_ux_authority_requested",
    "voice_authority",
    "voice_authority_requested",
    "final_answer_authority",
    "final_answer_authority_requested",
    "runtime_wiring_authority",
    "runtime_authority",
    "runtime_authority_requested",
    "live_runtime_authority",
    "live_runtime_authority_requested",
    "model_call_authority",
    "model_call_authority_requested",
    "search_call_authority",
    "search_call_authority_requested",
    "advisor_call_authority",
    "advisor_call_authority_requested",
    "benchmark_submission_authority",
    "benchmark_submission_requested",
    "official_claim_authority",
    "official_claim_requested",
    "public_claim_allowed",
    "official_claim_allowed",
    "turing_claim_requested",
    "intelligence_claim_requested",
    "certification_claim_requested",
    "raw_persistence_authority",
    "raw_persistence_requested",
    "private_memory_authority",
    "private_memory_requested",
    "unknown_engine_authority",
    "unknown_engine_authority_requested",
    "automatic_lesson_promotion_authority",
    "automatic_lesson_promotion_requested",
}

PLAN_PHASE_A_V1 = "phase_a_registry_and_source_validation"
PLAN_PHASE_B_V1 = "phase_b_preflight_validation"
PLAN_PHASE_C_V1 = "phase_c_non_executing_plan"
PLAN_PHASE_D_V1 = "phase_d_future_controlled_execution_gate"
PLAN_PHASE_E_V1 = "phase_e_observation_normalization"
PLAN_PHASE_F_V1 = "phase_f_result_packet"
PLAN_PHASE_G_V1 = "phase_g_operator_review"

PLAN_PHASE_LABELS_V1 = {
    PLAN_PHASE_A_V1,
    PLAN_PHASE_B_V1,
    PLAN_PHASE_C_V1,
    PLAN_PHASE_D_V1,
    PLAN_PHASE_E_V1,
    PLAN_PHASE_F_V1,
    PLAN_PHASE_G_V1,
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


def to_internal_task_corpus_controlled_execution_json_safe_v1(value: Any) -> Any:
    """Convert supported controlled-execution structures to deterministic JSON-safe data."""

    return _json_safe(value)


def _descriptor_from_task(task: Mapping[str, Any], task_family: str) -> str:
    descriptor = _safe_str(
        task.get("task_prompt_redacted_or_synthetic_descriptor")
        or task.get("task_prompt_descriptor")
        or task.get("synthetic_descriptor")
    )
    if descriptor:
        return descriptor
    if any(_safe_str(task.get(key)) for key in ("task_prompt", "prompt", "raw_prompt", "task_text", "context")):
        return "[redacted:internal_task_corpus_controlled_execution_request]"
    return f"[synthetic:{task_family or 'internal_task_corpus_rehearsal'}]"


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


def _collect_denied_authority_flags(record: Mapping[str, Any]) -> list[str]:
    flags: list[str] = []
    authority = _as_mapping(record.get("authority"))
    for flag in DENIED_AUTHORITY_FLAGS_V1:
        if _safe_bool(record.get(flag)) or _safe_bool(authority.get(flag)):
            flags.append(flag)
    return _unique_sorted(flags)


def _raw_present(record: Mapping[str, Any], keys: Iterable[str]) -> bool:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str):
            if _safe_str(value):
                return True
        elif _safe_bool(value):
            return True
    return False


def build_internal_task_corpus_controlled_execution_request_v1(
    task_item: Mapping[str, Any] | None = None,
    registry_item: Mapping[str, Any] | None = None,
    session_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a JSON-safe metadata-only controlled execution request."""

    task = _as_mapping(task_item)
    registry = _as_mapping(registry_item)
    context = _as_mapping(session_context)

    task_family = _safe_str(task.get("task_family") or registry.get("task_family") or "internal_task_corpus_rehearsal")
    source_class = _safe_str(task.get("source_class") or registry.get("source_class") or "synthetic_weslr_created")
    source_label = _safe_str(task.get("source_label") or registry.get("source_label") or source_class or "redacted_metadata_only")
    registry_record_id = _safe_str(
        task.get("registry_record_id") or registry.get("registry_record_id") or registry.get("record_id") or registry.get("id")
    )
    task_id = _safe_str(task.get("task_id") or task.get("id") or registry.get("task_id") or registry.get("id") or registry_record_id)

    request = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "request_type": REQUEST_TYPE_V1,
        "request_status": "draft",
        "task_metadata": {
            "task_id": task_id,
            "task_family": task_family,
            "source_class": source_class,
            "source_label": source_label,
            "registry_record_id": registry_record_id,
            "task_prompt_redacted_or_synthetic_descriptor": _descriptor_from_task(task, task_family),
            "task_labels": _safe_list(task.get("task_labels") or registry.get("task_labels")),
            "source_tags": _safe_list(task.get("source_tags") or registry.get("source_tags")),
            "source_descriptor": _safe_str(task.get("source_descriptor") or registry.get("source_descriptor")),
        },
        "source_metadata": {
            "source_class": source_class,
            "source_label": source_label,
            "registry_approved": _safe_bool(task.get("registry_approved") if task.get("registry_approved") is not None else registry.get("registry_approved")),
            "registry_source_approved": _safe_bool(task.get("registry_source_approved") if task.get("registry_source_approved") is not None else registry.get("registry_source_approved")),
        },
        "session_context": {
            "repo_root": _safe_str(context.get("repo_root") or task.get("repo_root") or registry.get("repo_root")),
            "session_key": _safe_str(context.get("session_key") or task.get("session_key") or registry.get("session_key")),
        },
        "execution_gate": {
            "execution_plan_preflight_passed": _safe_bool(
                task.get("execution_plan_preflight_passed")
                if task.get("execution_plan_preflight_passed") is not None
                else registry.get("execution_plan_preflight_passed")
            ),
            "adapter_preflight_passed": _safe_bool(
                task.get("adapter_preflight_passed") if task.get("adapter_preflight_passed") is not None else registry.get("adapter_preflight_passed")
            ),
            "operator_approval_required": _safe_bool(
                task.get("operator_approval_required")
                if task.get("operator_approval_required") is not None
                else registry.get("operator_approval_required")
                if registry.get("operator_approval_required") is not None
                else True
            ),
            "operator_approval_present": _safe_bool(
                task.get("operator_approval_present")
                if task.get("operator_approval_present") is not None
                else registry.get("operator_approval_present")
            ),
            "result_artifact_metadata_only": _safe_bool(
                task.get("result_artifact_metadata_only")
                if task.get("result_artifact_metadata_only") is not None
                else registry.get("result_artifact_metadata_only")
                if registry.get("result_artifact_metadata_only") is not None
                else True
            ),
            "future_controlled_execution_requested": _safe_bool(
                task.get("future_controlled_execution_requested")
                if task.get("future_controlled_execution_requested") is not None
                else registry.get("future_controlled_execution_requested")
            ),
        },
        "authority": {
            "public_live_authority": False,
            "public_ux_authority": False,
            "voice_authority": False,
            "final_answer_authority": False,
            "runtime_wiring_authority": False,
            "runtime_authority": False,
            "live_runtime_authority": False,
            "model_call_authority": False,
            "search_call_authority": False,
            "advisor_call_authority": False,
            "benchmark_submission_authority": False,
            "official_claim_authority": False,
            "public_claim_allowed": False,
            "official_claim_allowed": False,
            "turing_claim_requested": False,
            "intelligence_claim_requested": False,
            "certification_claim_requested": False,
            "raw_persistence_authority": False,
            "private_memory_authority": False,
            "unknown_engine_authority": False,
            "automatic_lesson_promotion_authority": False,
        },
        "unknown_engine_roles": _normalize_unknown_engine_roles(task.get("unknown_engine_roles") or registry.get("unknown_engine_roles")),
        "denied_authority_flags": [],
        "result_label": "needs_operator_review",
        "raw_private_data_requested": _safe_bool(task.get("raw_private_data_requested") or registry.get("raw_private_data_requested")),
        "raw_prompt_requested": _safe_bool(task.get("raw_prompt_requested") or registry.get("raw_prompt_requested")),
        "raw_response_requested": _safe_bool(task.get("raw_response_requested") or registry.get("raw_response_requested")),
        "raw_transcript_requested": _safe_bool(task.get("raw_transcript_requested") or registry.get("raw_transcript_requested")),
        "raw_context_requested": _safe_bool(task.get("raw_context_requested") or registry.get("raw_context_requested")),
        "raw_prompt_present": _raw_present(task, ("raw_prompt", "prompt", "task_prompt", "raw_text")),
        "raw_response_text_present": _raw_present(task, ("raw_response_text", "response_text", "final_answer", "answer_text")),
        "raw_transcript_present": _raw_present(task, ("raw_transcript", "transcript_text", "conversation_text", "live_chat_text")),
        "raw_context_present": _raw_present(task, ("raw_context", "context_text", "context_chain_text", "context")),
        "raw_persistence_requested": _safe_bool(task.get("raw_persistence_requested") or registry.get("raw_persistence_requested")),
        "private_memory_requested": _safe_bool(task.get("private_memory_requested") or registry.get("private_memory_requested")),
        "private_memory_scope_requested": _safe_bool(task.get("private_memory_scope_requested") or registry.get("private_memory_scope_requested")),
        "dot_weslr_requested": _safe_bool(task.get("dot_weslr_requested") or registry.get("dot_weslr_requested")),
        "live_user_content_requested": _safe_bool(task.get("live_user_content_requested") or registry.get("live_user_content_requested")),
        "hidden_material_requested": _safe_bool(task.get("hidden_material_requested") or registry.get("hidden_material_requested")),
        "benchmark_material_requested": _safe_bool(task.get("benchmark_material_requested") or registry.get("benchmark_material_requested")),
        "provider_model_output_requested": _safe_bool(task.get("provider_model_output_requested") or registry.get("provider_model_output_requested")),
        "public_live_authority_requested": _safe_bool(task.get("public_live_authority_requested") or registry.get("public_live_authority_requested")),
        "public_ux_authority_requested": _safe_bool(task.get("public_ux_authority_requested") or registry.get("public_ux_authority_requested")),
        "voice_authority_requested": _safe_bool(task.get("voice_authority_requested") or registry.get("voice_authority_requested")),
        "final_answer_authority_requested": _safe_bool(task.get("final_answer_authority_requested") or registry.get("final_answer_authority_requested")),
        "runtime_authority_requested": _safe_bool(task.get("runtime_authority_requested") or registry.get("runtime_authority_requested")),
        "live_runtime_authority_requested": _safe_bool(task.get("live_runtime_authority_requested") or registry.get("live_runtime_authority_requested")),
        "model_call_authority_requested": _safe_bool(task.get("model_call_authority_requested") or registry.get("model_call_authority_requested")),
        "search_call_authority_requested": _safe_bool(task.get("search_call_authority_requested") or registry.get("search_call_authority_requested")),
        "advisor_call_authority_requested": _safe_bool(task.get("advisor_call_authority_requested") or registry.get("advisor_call_authority_requested")),
        "benchmark_submission_requested": _safe_bool(task.get("benchmark_submission_requested") or registry.get("benchmark_submission_requested")),
        "official_claim_requested": _safe_bool(task.get("official_claim_requested") or registry.get("official_claim_requested")),
        "turing_claim_requested": _safe_bool(task.get("turing_claim_requested") or registry.get("turing_claim_requested")),
        "intelligence_claim_requested": _safe_bool(task.get("intelligence_claim_requested") or registry.get("intelligence_claim_requested")),
        "certification_claim_requested": _safe_bool(task.get("certification_claim_requested") or registry.get("certification_claim_requested")),
        "automatic_lesson_promotion_requested": _safe_bool(task.get("automatic_lesson_promotion_requested") or registry.get("automatic_lesson_promotion_requested")),
    }
    request["denied_authority_flags"] = _collect_denied_authority_flags(request)
    return to_internal_task_corpus_controlled_execution_json_safe_v1(request)


def validate_internal_task_corpus_controlled_execution_preflight_v1(
    request: Mapping[str, Any] | None,
    session_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a controlled-execution request and fail closed on unsafe input."""

    req = _as_mapping(request)
    context = _as_mapping(session_context)
    task_metadata = _as_mapping(req.get("task_metadata"))
    source_metadata = _as_mapping(req.get("source_metadata"))
    gate = _as_mapping(req.get("execution_gate"))
    authority = _as_mapping(req.get("authority"))

    blocked_labels: list[str] = []
    errors: list[str] = []

    task_id = _safe_str(task_metadata.get("task_id") or req.get("task_id"))
    task_family = _safe_str(task_metadata.get("task_family") or req.get("task_family"))
    source_class = _safe_str(source_metadata.get("source_class") or task_metadata.get("source_class") or req.get("source_class"))
    source_label = _safe_str(source_metadata.get("source_label") or task_metadata.get("source_label") or req.get("source_label"))
    registry_record_id = _safe_str(task_metadata.get("registry_record_id") or req.get("registry_record_id") or source_metadata.get("registry_record_id"))
    repo_root = _safe_str((req.get("session_context") or {}).get("repo_root") if isinstance(req.get("session_context"), Mapping) else req.get("repo_root") or context.get("repo_root"))
    session_key = _safe_str((req.get("session_context") or {}).get("session_key") if isinstance(req.get("session_context"), Mapping) else req.get("session_key") or context.get("session_key"))

    if not task_id:
        blocked_labels.append("missing_task_id")
        errors.append("missing task_id")
    if not task_family:
        blocked_labels.append("missing_task_family")
    if not source_class:
        blocked_labels.append("missing_source_class")
    elif source_class in BLOCKED_SOURCE_CLASSES_V1:
        blocked_labels.append("blocked_source_class")
    elif source_class not in ALLOWED_SOURCE_CLASSES_V1:
        blocked_labels.append("unknown_source_class")
    if not source_label:
        blocked_labels.append("missing_source_label")
    if not registry_record_id:
        blocked_labels.append("missing_registry_record_id")
    if not _safe_bool(source_metadata.get("registry_approved") if source_metadata.get("registry_approved") is not None else req.get("registry_approved")):
        blocked_labels.append("missing_registry_approval")
        blocked_labels.append("source_registry_missing")
    if not _safe_bool(gate.get("execution_plan_preflight_passed") if gate.get("execution_plan_preflight_passed") is not None else req.get("execution_plan_preflight_passed")):
        blocked_labels.append("missing_execution_plan_preflight")
    if not _safe_bool(gate.get("adapter_preflight_passed") if gate.get("adapter_preflight_passed") is not None else req.get("adapter_preflight_passed")):
        blocked_labels.append("missing_adapter_preflight")
    result_artifact_metadata_only = _safe_bool(
        gate.get("result_artifact_metadata_only")
        if gate.get("result_artifact_metadata_only") is not None
        else req.get("result_artifact_metadata_only")
        if req.get("result_artifact_metadata_only") is not None
        else True
    )
    if not result_artifact_metadata_only:
        blocked_labels.append("result_artifact_not_metadata_only")
    operator_approval_required = _safe_bool(
        gate.get("operator_approval_required") if gate.get("operator_approval_required") is not None else req.get("operator_approval_required")
        if req.get("operator_approval_required") is not None
        else True
    )
    operator_approval_present = _safe_bool(
        gate.get("operator_approval_present") if gate.get("operator_approval_present") is not None else req.get("operator_approval_present")
    )
    if operator_approval_required and not operator_approval_present:
        blocked_labels.append("missing_operator_approval")
        blocked_labels.append("operator_approval_not_present")

    source_registry_approved = _safe_bool(source_metadata.get("registry_approved") if source_metadata.get("registry_approved") is not None else req.get("registry_approved"))
    if not source_registry_approved:
        blocked_labels.append("source_registry_not_approved")

    raw_flags = [
        "raw_private_data_requested",
        "raw_prompt_requested",
        "raw_response_requested",
        "raw_transcript_requested",
        "raw_context_requested",
        "raw_persistence_requested",
        "private_memory_requested",
        "private_memory_scope_requested",
        "dot_weslr_requested",
        "live_user_content_requested",
        "hidden_material_requested",
        "benchmark_material_requested",
        "provider_model_output_requested",
        "raw_prompt_present",
        "raw_response_text_present",
        "raw_transcript_present",
        "raw_context_present",
        "raw_prompt_storage_requested",
        "raw_response_storage_requested",
        "raw_transcript_storage_requested",
        "raw_context_storage_requested",
    ]
    if any(_safe_bool(req.get(flag)) for flag in raw_flags):
        if _safe_bool(req.get("dot_weslr_requested")):
            blocked_labels.append("dot_weslr_requested")
        if _safe_bool(req.get("private_memory_requested")) or _safe_bool(req.get("private_memory_scope_requested")):
            blocked_labels.append("private_memory_scope_requested")
        if _safe_bool(req.get("live_user_content_requested")):
            blocked_labels.append("live_user_content_requested")
        if _safe_bool(req.get("hidden_material_requested")):
            blocked_labels.append("hidden_material_requested")
        if _safe_bool(req.get("benchmark_material_requested")):
            blocked_labels.append("benchmark_material_requested")
        if _safe_bool(req.get("provider_model_output_requested")):
            blocked_labels.append("provider_model_output_requested")
        if _safe_bool(req.get("raw_prompt_requested")) or _safe_bool(req.get("raw_prompt_present")):
            blocked_labels.append("raw_prompt_provided")
            blocked_labels.append("raw_private_data_requested")
        if _safe_bool(req.get("raw_response_requested")) or _safe_bool(req.get("raw_response_text_present")):
            blocked_labels.append("raw_response_text_provided")
            blocked_labels.append("raw_private_data_requested")
        if _safe_bool(req.get("raw_transcript_requested")) or _safe_bool(req.get("raw_transcript_present")):
            blocked_labels.append("raw_transcript_provided")
            blocked_labels.append("raw_private_data_requested")
        if _safe_bool(req.get("raw_context_requested")) or _safe_bool(req.get("raw_context_present")):
            blocked_labels.append("raw_context_provided")
            blocked_labels.append("raw_private_data_requested")
        if _safe_bool(req.get("raw_persistence_requested")):
            blocked_labels.append("raw_persistence_requested")
        if _safe_bool(req.get("raw_private_data_requested")):
            blocked_labels.append("raw_private_data_requested")

    authority_flags = _collect_denied_authority_flags(req)
    if authority_flags or any(_safe_bool(authority.get(key)) for key in authority):
        for flag in authority_flags:
            if flag in {"public_live_authority", "public_live_authority_requested"}:
                blocked_labels.append("public_live_authority_requested")
            elif flag in {"public_ux_authority", "public_ux_authority_requested"}:
                blocked_labels.append("public_ux_authority_requested")
            elif flag in {"voice_authority", "voice_authority_requested"}:
                blocked_labels.append("voice_authority_requested")
            elif flag in {"final_answer_authority", "final_answer_authority_requested"}:
                blocked_labels.append("final_answer_authority_requested")
            elif flag in {"runtime_authority", "runtime_wiring_authority", "runtime_authority_requested"}:
                blocked_labels.append("runtime_authority_requested")
            elif flag in {"live_runtime_authority", "live_runtime_authority_requested"}:
                blocked_labels.append("live_runtime_authority_requested")
            elif flag in {"model_call_authority", "model_call_authority_requested"}:
                blocked_labels.append("model_call_authority_requested")
            elif flag in {"search_call_authority", "search_call_authority_requested"}:
                blocked_labels.append("search_call_authority_requested")
            elif flag in {"advisor_call_authority", "advisor_call_authority_requested"}:
                blocked_labels.append("advisor_call_authority_requested")
            elif flag in {"benchmark_submission_authority", "benchmark_submission_requested"}:
                blocked_labels.append("benchmark_submission_requested")
            elif flag in {"official_claim_authority", "official_claim_requested", "official_claim_allowed", "public_claim_allowed"}:
                blocked_labels.append("official_claim_requested")
            elif flag in {"turing_claim_requested"}:
                blocked_labels.append("turing_claim_requested")
            elif flag in {"intelligence_claim_requested"}:
                blocked_labels.append("intelligence_claim_requested")
            elif flag in {"certification_claim_requested"}:
                blocked_labels.append("certification_claim_requested")
            elif flag in {"raw_persistence_authority", "raw_persistence_requested"}:
                blocked_labels.append("raw_persistence_requested")
            elif flag in {"private_memory_authority", "private_memory_requested"}:
                blocked_labels.append("private_memory_requested")
            elif flag in {"unknown_engine_authority", "unknown_engine_authority_requested"}:
                blocked_labels.append("unknown_engine_authority_requested")
            elif flag in {"automatic_lesson_promotion_authority", "automatic_lesson_promotion_requested"}:
                blocked_labels.append("automatic_lesson_promotion_requested")
            else:
                blocked_labels.append("unknown_authority_flag")

    unknown_engine_roles = _normalize_unknown_engine_roles(req.get("unknown_engine_roles"))
    unknown_engine_blocked: list[str] = []
    for role in unknown_engine_roles:
        if role in FORBIDDEN_UNKNOWN_ENGINE_ROLES_V1:
            unknown_engine_blocked.append("forbidden_unknown_engine_role")
        elif role not in ALLOWED_UNKNOWN_ENGINE_ROLES_V1:
            unknown_engine_blocked.append("unknown_unknown_engine_role")
    blocked_labels.extend(unknown_engine_blocked)

    allowed = not blocked_labels
    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "request_type": REQUEST_TYPE_V1,
        "request_status": "valid" if allowed else "blocked",
        "valid": allowed,
        "blocked": not allowed,
        "blocked_labels": _unique_sorted(blocked_labels),
        "errors": _unique_sorted(errors),
        "task_id": task_id,
        "task_family": task_family,
        "source_class": source_class,
        "source_label": source_label,
        "registry_record_id": registry_record_id,
        "repo_root": repo_root,
        "session_key": session_key,
        "registry_approved": source_registry_approved,
        "execution_plan_preflight_passed": _safe_bool(gate.get("execution_plan_preflight_passed") if gate.get("execution_plan_preflight_passed") is not None else req.get("execution_plan_preflight_passed")),
        "adapter_preflight_passed": _safe_bool(gate.get("adapter_preflight_passed") if gate.get("adapter_preflight_passed") is not None else req.get("adapter_preflight_passed")),
        "operator_approval_required": operator_approval_required,
        "operator_approval_present": operator_approval_present,
        "result_artifact_metadata_only": result_artifact_metadata_only,
        "denied_authority_flags": _unique_sorted(authority_flags),
        "unknown_engine_roles": unknown_engine_roles,
        "normalized_request": to_internal_task_corpus_controlled_execution_json_safe_v1(req),
    }


def build_internal_task_corpus_controlled_execution_plan_v1(
    request: Mapping[str, Any] | None,
    preflight: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a non-executing controlled-execution plan."""

    req = _as_mapping(request)
    pre = _as_mapping(preflight) if preflight is not None else validate_internal_task_corpus_controlled_execution_preflight_v1(req)
    valid = _safe_bool(pre.get("valid"))
    future_requested = _safe_bool(_as_mapping(req.get("execution_gate")).get("future_controlled_execution_requested") if isinstance(req.get("execution_gate"), Mapping) else req.get("future_controlled_execution_requested"))

    if not valid:
        plan_status = "blocked"
    elif future_requested:
        plan_status = "pending_future_controlled_execution"
    else:
        plan_status = "pending_operator_review"

    phases = [
        {"phase_label": PLAN_PHASE_A_V1, "phase_name": "registry_and_source_validation", "phase_status": "complete" if valid else "blocked"},
        {"phase_label": PLAN_PHASE_B_V1, "phase_name": "preflight_validation", "phase_status": "complete" if valid else "blocked"},
        {"phase_label": PLAN_PHASE_C_V1, "phase_name": "non_executing_plan", "phase_status": "pending" if valid else "blocked"},
        {"phase_label": PLAN_PHASE_D_V1, "phase_name": "future_controlled_execution_gate", "phase_status": "future_only" if valid else "blocked"},
        {"phase_label": PLAN_PHASE_E_V1, "phase_name": "observation_normalization", "phase_status": "pending" if valid else "blocked"},
        {"phase_label": PLAN_PHASE_F_V1, "phase_name": "result_packet", "phase_status": "pending" if valid else "blocked"},
        {"phase_label": PLAN_PHASE_G_V1, "phase_name": "operator_review", "phase_status": "pending" if valid else "blocked"},
    ]

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "plan_type": PLAN_TYPE_V1,
        "plan_status": plan_status,
        "request_status": _safe_str(pre.get("request_status") or "blocked"),
        "valid": valid,
        "blocked": not valid,
        "should_execute": False,
        "execution_callable": None,
        "controlled_execution_allowed": False,
        "operator_review_required": True,
        "task_id": _safe_str(pre.get("task_id") or req.get("task_id")),
        "task_family": _safe_str(pre.get("task_family") or req.get("task_family")),
        "source_class": _safe_str(pre.get("source_class") or req.get("source_class")),
        "registry_record_id": _safe_str(pre.get("registry_record_id") or req.get("registry_record_id")),
        "blocked_labels": _unique_sorted(pre.get("blocked_labels") or []),
        "denied_authority_flags": _unique_sorted(pre.get("denied_authority_flags") or []),
        "phases": phases,
        "normalized_request": to_internal_task_corpus_controlled_execution_json_safe_v1(req),
        "preflight": to_internal_task_corpus_controlled_execution_json_safe_v1(pre),
        "live_call_path": None,
        "chat_responder_call_allowed": False,
        "model_call_allowed": False,
        "search_call_allowed": False,
        "advisor_call_allowed": False,
    }


def normalize_internal_task_corpus_controlled_execution_observation_v1(
    observation: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Normalize an observation using metadata labels only."""

    obs = _as_mapping(observation)
    result_label = _safe_str(obs.get("result_label") or "needs_operator_review")
    gap_labels = _safe_list(obs.get("gap_labels"))
    predicted_labels = _safe_list(obs.get("predicted_labels"))
    observed_labels = _safe_list(obs.get("observed_labels"))
    blocked_labels = _safe_list(obs.get("blocked_labels"))
    denied_authority_flags = _safe_list(obs.get("denied_authority_flags"))
    result_block_labels: list[str] = []

    if result_label not in RESULT_LABELS_V1:
        result_label = "needs_operator_review"
        result_block_labels.append("unknown_result_label")

    raw_prompt_present = _raw_present(obs, ("raw_prompt", "prompt", "task_prompt", "raw_text"))
    raw_response_text_present = _raw_present(obs, ("raw_response_text", "response_text", "final_answer", "answer_text"))
    raw_transcript_present = _raw_present(obs, ("raw_transcript", "transcript_text", "conversation_text", "live_chat_text"))
    raw_context_present = _raw_present(obs, ("raw_context", "context_text", "context_chain_text", "context"))

    if raw_prompt_present:
        result_block_labels.append("raw_prompt_provided")
    if raw_response_text_present:
        result_block_labels.append("raw_response_text_provided")
    if raw_transcript_present:
        result_block_labels.append("raw_transcript_provided")
    if raw_context_present:
        result_block_labels.append("raw_context_provided")

    observation_status = result_label
    if result_block_labels:
        if any(label.startswith("raw_") for label in result_block_labels):
            observation_status = "blocked_by_privacy_boundary"
        else:
            observation_status = "blocked_by_runtime_boundary"

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "observation_type": OBSERVATION_TYPE_V1,
        "observation_status": observation_status,
        "result_label": result_label,
        "gap_labels": gap_labels,
        "predicted_labels": predicted_labels,
        "observed_labels": observed_labels,
        "blocked_labels": _unique_sorted(blocked_labels + result_block_labels),
        "denied_authority_flags": _unique_sorted(denied_authority_flags),
        "raw_prompt_present": raw_prompt_present,
        "raw_prompt_retained": False,
        "raw_prompt_redacted": raw_prompt_present,
        "raw_response_text_present": raw_response_text_present,
        "raw_response_text_retained": False,
        "raw_response_text_redacted": raw_response_text_present,
        "raw_transcript_present": raw_transcript_present,
        "raw_transcript_retained": False,
        "raw_transcript_redacted": raw_transcript_present,
        "raw_context_present": raw_context_present,
        "raw_context_retained": False,
        "raw_context_redacted": raw_context_present,
        "final_answer_authority": False,
        "user_facing_prose_authority": False,
        "live_runtime_authority": False,
        "public_live_authority": False,
        "official_claims": False,
    }


def build_internal_task_corpus_controlled_execution_result_packet_v1(
    request: Mapping[str, Any] | None,
    preflight: Mapping[str, Any] | None,
    plan: Mapping[str, Any] | None,
    observations: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a safe operator review packet."""

    req = _as_mapping(request)
    pre = _as_mapping(preflight)
    pln = _as_mapping(plan)
    obs = normalize_internal_task_corpus_controlled_execution_observation_v1(observations) if observations is not None else {
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
        "raw_prompt_present": False,
        "raw_prompt_retained": False,
        "raw_prompt_redacted": False,
        "raw_response_text_present": False,
        "raw_response_text_retained": False,
        "raw_response_text_redacted": False,
        "raw_transcript_present": False,
        "raw_transcript_retained": False,
        "raw_transcript_redacted": False,
        "raw_context_present": False,
        "raw_context_retained": False,
        "raw_context_redacted": False,
        "final_answer_authority": False,
        "user_facing_prose_authority": False,
        "live_runtime_authority": False,
        "public_live_authority": False,
        "official_claims": False,
    }

    safe_request = {
        "request_status": _safe_str(req.get("request_status") or "draft"),
        "task_metadata": to_internal_task_corpus_controlled_execution_json_safe_v1(req.get("task_metadata") or {}),
        "source_metadata": to_internal_task_corpus_controlled_execution_json_safe_v1(req.get("source_metadata") or {}),
        "session_context": to_internal_task_corpus_controlled_execution_json_safe_v1(req.get("session_context") or {}),
        "execution_gate": {
            "execution_plan_preflight_passed": _safe_bool(_as_mapping(req.get("execution_gate")).get("execution_plan_preflight_passed") if isinstance(req.get("execution_gate"), Mapping) else req.get("execution_plan_preflight_passed")),
            "adapter_preflight_passed": _safe_bool(_as_mapping(req.get("execution_gate")).get("adapter_preflight_passed") if isinstance(req.get("execution_gate"), Mapping) else req.get("adapter_preflight_passed")),
            "operator_approval_required": _safe_bool(_as_mapping(req.get("execution_gate")).get("operator_approval_required") if isinstance(req.get("execution_gate"), Mapping) else req.get("operator_approval_required")),
            "operator_approval_present": _safe_bool(_as_mapping(req.get("execution_gate")).get("operator_approval_present") if isinstance(req.get("execution_gate"), Mapping) else req.get("operator_approval_present")),
            "result_artifact_metadata_only": _safe_bool(_as_mapping(req.get("execution_gate")).get("result_artifact_metadata_only") if isinstance(req.get("execution_gate"), Mapping) else req.get("result_artifact_metadata_only")),
            "future_controlled_execution_requested": _safe_bool(_as_mapping(req.get("execution_gate")).get("future_controlled_execution_requested") if isinstance(req.get("execution_gate"), Mapping) else req.get("future_controlled_execution_requested")),
        },
        "denied_authority_flags": _unique_sorted(req.get("denied_authority_flags") or []),
        "unknown_engine_roles": _unique_sorted(req.get("unknown_engine_roles") or []),
        "result_label": _safe_str(req.get("result_label") or "needs_operator_review"),
    }

    safe_preflight = {
        "request_status": _safe_str(pre.get("request_status") or "blocked"),
        "valid": _safe_bool(pre.get("valid")),
        "blocked": _safe_bool(pre.get("blocked")),
        "blocked_labels": _unique_sorted(pre.get("blocked_labels") or []),
        "denied_authority_flags": _unique_sorted(pre.get("denied_authority_flags") or []),
        "task_id": _safe_str(pre.get("task_id") or ""),
        "task_family": _safe_str(pre.get("task_family") or ""),
        "source_class": _safe_str(pre.get("source_class") or ""),
        "registry_record_id": _safe_str(pre.get("registry_record_id") or ""),
        "registry_approved": _safe_bool(pre.get("registry_approved")),
        "execution_plan_preflight_passed": _safe_bool(pre.get("execution_plan_preflight_passed")),
        "adapter_preflight_passed": _safe_bool(pre.get("adapter_preflight_passed")),
        "operator_approval_required": _safe_bool(pre.get("operator_approval_required")),
        "operator_approval_present": _safe_bool(pre.get("operator_approval_present")),
        "result_artifact_metadata_only": _safe_bool(pre.get("result_artifact_metadata_only")),
        "unknown_engine_roles": _unique_sorted(pre.get("unknown_engine_roles") or []),
    }

    safe_plan = {
        "plan_status": _safe_str(pln.get("plan_status") or "blocked"),
        "valid": _safe_bool(pln.get("valid")),
        "blocked": _safe_bool(pln.get("blocked")),
        "should_execute": False,
        "execution_callable": None,
        "controlled_execution_allowed": False,
        "operator_review_required": True,
        "blocked_labels": _unique_sorted(pln.get("blocked_labels") or []),
        "denied_authority_flags": _unique_sorted(pln.get("denied_authority_flags") or []),
        "phase_count": len(pln.get("phases") or []),
        "phases": to_internal_task_corpus_controlled_execution_json_safe_v1(pln.get("phases") or []),
    }

    safe_observations = {
        "observation_status": _safe_str(obs.get("observation_status") or "needs_operator_review"),
        "result_label": _safe_str(obs.get("result_label") or "needs_operator_review"),
        "gap_labels": _unique_sorted(obs.get("gap_labels") or []),
        "predicted_labels": _unique_sorted(obs.get("predicted_labels") or []),
        "observed_labels": _unique_sorted(obs.get("observed_labels") or []),
        "blocked_labels": _unique_sorted(obs.get("blocked_labels") or []),
        "denied_authority_flags": _unique_sorted(obs.get("denied_authority_flags") or []),
        "prompt_present": _safe_bool(obs.get("raw_prompt_present")),
        "prompt_retained": False,
        "prompt_redacted": _safe_bool(obs.get("raw_prompt_redacted")),
        "response_present": _safe_bool(obs.get("raw_response_text_present")),
        "response_retained": False,
        "response_redacted": _safe_bool(obs.get("raw_response_text_redacted")),
        "transcript_present": _safe_bool(obs.get("raw_transcript_present")),
        "transcript_retained": False,
        "transcript_redacted": _safe_bool(obs.get("raw_transcript_redacted")),
        "context_present": _safe_bool(obs.get("raw_context_present")),
        "context_retained": False,
        "context_redacted": _safe_bool(obs.get("raw_context_redacted")),
        "final_answer_authority": False,
        "user_facing_prose_authority": False,
        "live_runtime_authority": False,
        "public_live_authority": False,
        "official_claims": False,
    }

    blocked_labels = _unique_sorted(
        list(pre.get("blocked_labels") or [])
        + list(pln.get("blocked_labels") or [])
        + list(obs.get("blocked_labels") or [])
    )
    denied_authority_flags = _unique_sorted(
        list(pre.get("denied_authority_flags") or [])
        + list(pln.get("denied_authority_flags") or [])
        + list(obs.get("denied_authority_flags") or [])
    )

    packet_status = "blocked" if blocked_labels else _safe_str(pln.get("plan_status") or "pending_operator_review")

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "packet_type": RESULT_PACKET_TYPE_V1,
        "packet_status": packet_status,
        "request": safe_request,
        "preflight": safe_preflight,
        "plan": safe_plan,
        "observations": safe_observations,
        "blocked_labels": blocked_labels,
        "denied_authority_flags": denied_authority_flags,
        "task_id": _safe_str(pre.get("task_id") or req.get("task_metadata", {}).get("task_id") if isinstance(req.get("task_metadata"), Mapping) else req.get("task_id")),
        "task_family": _safe_str(pre.get("task_family") or req.get("task_metadata", {}).get("task_family") if isinstance(req.get("task_metadata"), Mapping) else req.get("task_family")),
        "source_class": _safe_str(pre.get("source_class") or req.get("task_metadata", {}).get("source_class") if isinstance(req.get("task_metadata"), Mapping) else req.get("source_class")),
        "registry_record_id": _safe_str(pre.get("registry_record_id") or req.get("task_metadata", {}).get("registry_record_id") if isinstance(req.get("task_metadata"), Mapping) else req.get("registry_record_id")),
        "final_answer_authority": False,
        "user_facing_prose_authority": False,
        "live_runtime_authority": False,
        "public_live_authority": False,
        "official_claims": False,
        "operator_review_required": True,
    }


def validate_internal_task_corpus_controlled_execution_batch_v1(
    records: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate multiple requests while preserving per-record results."""

    results: list[dict[str, Any]] = []
    for item in records:
        record = _as_mapping(item)
        request = record.get("request") if isinstance(record.get("request"), Mapping) else record
        preflight = validate_internal_task_corpus_controlled_execution_preflight_v1(request)
        results.append(preflight)

    aggregate_blocked_labels = _unique_sorted(label for result in results for label in result.get("blocked_labels", []))
    aggregate_denied_authority_flags = _unique_sorted(flag for result in results for flag in result.get("denied_authority_flags", []))
    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "valid": all(result["valid"] for result in results) if results else True,
        "total_records": len(results),
        "valid_records": sum(1 for result in results if result["valid"]),
        "blocked_records": sum(1 for result in results if result["blocked"]),
        "aggregate_blocked_labels": aggregate_blocked_labels,
        "aggregate_denied_authority_flags": aggregate_denied_authority_flags,
        "records": results,
    }


def summarize_internal_task_corpus_controlled_execution_v1(
    value: Mapping[str, Any] | Iterable[Any],
) -> dict[str, Any]:
    """Return a safe metadata-only summary of requests or validation results."""

    if isinstance(value, Mapping) and "records" in value:
        items = value["records"]
    else:
        items = value

    normalized_results: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, Mapping) and {"valid", "blocked", "normalized_request"}.issubset(set(item.keys())):
            request = item.get("normalized_request") or {}
            preflight = validate_internal_task_corpus_controlled_execution_preflight_v1(request)
            plan = build_internal_task_corpus_controlled_execution_plan_v1(request, preflight)
            normalized_results.append({**preflight, "plan_status": _safe_str(plan.get("plan_status"))})
        elif isinstance(item, Mapping) and {"valid", "blocked", "blocked_labels"}.issubset(set(item.keys())):
            result = dict(item)
            if "plan_status" not in result:
                request = result.get("normalized_request") or result.get("request") or {}
                preflight = validate_internal_task_corpus_controlled_execution_preflight_v1(request)
                plan = build_internal_task_corpus_controlled_execution_plan_v1(request, preflight)
                result["plan_status"] = _safe_str(plan.get("plan_status"))
            normalized_results.append(result)
        else:
            preflight = validate_internal_task_corpus_controlled_execution_preflight_v1(item)
            plan = build_internal_task_corpus_controlled_execution_plan_v1(item, preflight)
            normalized_results.append({**preflight, "plan_status": _safe_str(plan.get("plan_status"))})

    blocked_labels = _unique_sorted(label for result in normalized_results for label in result.get("blocked_labels", []))
    denied_authority_flags = _unique_sorted(flag for result in normalized_results for flag in result.get("denied_authority_flags", []))
    source_class_counts: dict[str, int] = {}
    plan_status_counts: dict[str, int] = {}
    request_status_counts: dict[str, int] = {}
    result_label_counts: dict[str, int] = {}
    for result in normalized_results:
        source_class = _safe_str(result.get("source_class") or "unknown")
        source_class_counts[source_class] = source_class_counts.get(source_class, 0) + 1
        request_status = _safe_str(result.get("request_status") or "unknown")
        request_status_counts[request_status] = request_status_counts.get(request_status, 0) + 1
        result_label = _safe_str(result.get("result_label") or "needs_operator_review")
        result_label_counts[result_label] = result_label_counts.get(result_label, 0) + 1
        plan_status = _safe_str(result.get("plan_status") or "unknown")
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
        "source_class_counts": source_class_counts,
        "request_status_counts": request_status_counts,
        "plan_status_counts": plan_status_counts,
        "result_label_counts": result_label_counts,
        "record_status_counts": {
            "valid": sum(1 for result in normalized_results if _safe_str(result.get("request_status")) == "valid"),
            "blocked": sum(1 for result in normalized_results if _safe_str(result.get("request_status")) == "blocked"),
        },
        "final_answer_authority": False,
        "user_facing_prose_authority": False,
        "live_runtime_authority": False,
        "public_live_authority": False,
        "official_claims": False,
    }
