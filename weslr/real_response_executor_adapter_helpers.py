"""Real response executor or adapter helper boundary V1.

Pure metadata-only helpers for a future controlled internal evaluation lane.
This module does not import runtime responders, call models/search/advisors, persist
files, write workspace state, or execute any live response path.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "1.0"
HELPER_TYPE_V1 = "weslr_real_response_executor_adapter_helpers_v1"
BOUNDARY_TYPE_V1 = "real_response_executor_or_adapter_boundary_v1"

ALLOWED_TASK_FAMILIES_V1 = {
    "ordinary_task_behavior",
    "non_canned_cognition",
    "conduct_alignment",
    "live_slice_behavior_existing_plan_helper_only",
}

ALLOWED_SOURCE_CLASSES_V1 = {
    "synthetic_weslr_created",
    "generated_mutation_from_allowed_source",
}

BLOCKED_SOURCE_LABELS_V1 = {
    "public_open",
    "semi_private",
    "private",
    "hidden_blocked",
    "unknown_license_blocked_until_reviewed",
    "raw_private_user_data_blocked",
    "generated_mutation_from_blocked_source_blocked",
}

ALLOWED_SOURCE_LABELS_V1 = ALLOWED_SOURCE_CLASSES_V1

DENIED_AUTHORITY_FLAGS_V1 = {
    "public_live_authority",
    "public_ux_authority",
    "voice_authority",
    "final_answer_authority",
    "runtime_wiring_authority",
    "benchmark_submission_authority",
    "official_claim_authority",
    "raw_persistence_authority",
    "private_memory_authority",
    "model_call_authority",
    "search_call_authority",
    "advisor_call_authority",
    "unknown_engine_authority",
    "automatic_lesson_promotion_authority",
}

ALLOWED_UNKNOWN_ENGINE_ROLES_V1 = {
    "predict_failure_zones",
    "compare_predicted_vs_observed_labels",
    "compress_repeated_gaps",
    "suggest_synthetic_test_families",
}

FORBIDDEN_UNKNOWN_ENGINE_ROLES_V1 = {
    "authority",
    "truth_certification",
    "official_scoring",
    "runtime_live_control",
    "source_license_approval",
    "automatic_self_modification",
    "future_certainty",
}

PLAN_STATUS_PENDING_OPERATOR_REVIEW_V1 = "pending_operator_review"
PLAN_STATUS_BLOCKED_V1 = "blocked"
PLAN_STATUS_ALLOWED_PENDING_OPERATOR_REVIEW_V1 = PLAN_STATUS_PENDING_OPERATOR_REVIEW_V1

OBSERVATION_LABEL_PASS_V1 = "pass_internal_evaluation"
OBSERVATION_LABEL_FAIL_V1 = "fail_internal_evaluation"
OBSERVATION_LABEL_BLOCKED_V1 = "blocked_by_boundary"
OBSERVATION_LABEL_NEEDS_REVIEW_V1 = "needs_review"
OBSERVATION_LABEL_INCONCLUSIVE_V1 = "inconclusive_internal_evaluation"

ALLOWED_RESULT_LABELS_V1 = {
    OBSERVATION_LABEL_PASS_V1,
    OBSERVATION_LABEL_FAIL_V1,
    OBSERVATION_LABEL_BLOCKED_V1,
    OBSERVATION_LABEL_NEEDS_REVIEW_V1,
    OBSERVATION_LABEL_INCONCLUSIVE_V1,
}

ALLOWED_GAP_LABELS_V1 = {
    "missing_executor_adapter_boundary",
    "missing_task_corpus_execution_path",
    "missing_operator_review_packet",
    "missing_preflight_gate",
    "missing_metadata_only_result_policy",
    "missing_raw_response_redaction",
    "missing_denied_authority_tracking",
}

ALLOWED_PREDICTED_LABELS_V1 = {
    "predicted_matches_observed",
    "predicted_differs_from_observed",
    "predicted_underpredicted",
    "predicted_overpredicted",
}

ALLOWED_OBSERVED_LABELS_V1 = {
    "observed_matches_prediction",
    "observed_differs_from_prediction",
    "observed_more_severe_than_predicted",
    "observed_less_severe_than_predicted",
}

BLOCK_REASON_LABELS_V1 = {
    "missing_repo_root",
    "missing_session_key",
    "task_family_not_allowed",
    "source_class_missing",
    "source_label_missing",
    "registry_metadata_missing",
    "registry_id_missing",
    "blocked_source_label",
    "source_class_not_allowed",
    "private_memory_requested",
    "dot_weslr_requested",
    "public_live_voice_authority_requested",
    "final_answer_authority_requested",
    "official_claim_requested",
    "feature_flag_enabled",
    "raw_persistence_requested",
    "unknown_engine_authority_requested",
    "raw_response_text_provided",
    "unknown_result_label",
    "unknown_gap_label",
    "unknown_predicted_label",
    "unknown_observed_label",
    "unsupported_authority_flag_requested",
    "invalid_request_shape",
}

REQUEST_TYPE_V1 = "real_response_executor_adapter_request_v1"
CALL_PLAN_TYPE_V1 = "real_response_executor_adapter_call_plan_v1"
OBSERVATION_TYPE_V1 = "real_response_executor_adapter_observation_v1"
RESULT_PACKET_TYPE_V1 = "real_response_executor_adapter_result_packet_v1"


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _safe_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        values = value
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


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return repr(value)


def to_real_response_executor_adapter_json_safe_v1(obj: Any) -> Any:
    """Return a deep JSON-safe copy. This is not a sanitizer."""
    return _json_safe(obj)


def _normalize_authority_flags(value: Any) -> list[str]:
    flags = _safe_list(value)
    return [flag for flag in flags if flag in DENIED_AUTHORITY_FLAGS_V1 or flag not in {""}]


def _normalize_unknown_engine_roles(value: Any) -> list[str]:
    roles = _safe_list(value)
    return roles


def _is_blocked_source_label(source_label: str) -> bool:
    return source_label in BLOCKED_SOURCE_LABELS_V1 or source_label == ""


def _is_allowed_task_family(task_family: str) -> bool:
    return task_family in ALLOWED_TASK_FAMILIES_V1


def _is_allowed_source_class(source_class: str) -> bool:
    return source_class in ALLOWED_SOURCE_CLASSES_V1


def _build_blocked_request(
    *,
    request_type: str,
    task_family: str,
    source_class: str,
    source_label: str,
    registry_id: str,
    repo_root: str,
    session_key: str,
    denied_authority_flags: list[str],
    unknown_engine_roles: list[str],
    raw_response_storage_requested: bool,
    feature_flag_enabled: bool,
    block_reason_labels: list[str],
) -> dict[str, Any]:
    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "request_type": request_type,
        "request_status": PLAN_STATUS_BLOCKED_V1,
        "task_family": task_family,
        "source_class": source_class,
        "source_label": source_label,
        "registry_id": registry_id,
        "repo_root": repo_root,
        "session_key": session_key,
        "denied_authority_flags": denied_authority_flags,
        "unknown_engine_roles": unknown_engine_roles,
        "raw_response_storage_requested": bool(raw_response_storage_requested),
        "feature_flag_enabled": bool(feature_flag_enabled),
        "allowed": False,
        "blocked": True,
        "block_reason_labels": block_reason_labels,
        "result_label": OBSERVATION_LABEL_BLOCKED_V1,
        "final_answer_authority": False,
        "user_facing_prose_authority": False,
        "live_runtime_authority": False,
        "public_ux_authority": False,
    }


def build_real_response_executor_adapter_request_v1(
    task_item: Mapping[str, Any] | None = None,
    registry_item: Mapping[str, Any] | None = None,
    session_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a metadata-only request for the future helper/adapter boundary."""

    task = _as_mapping(task_item)
    registry = _as_mapping(registry_item)
    context = _as_mapping(session_context)

    request_type = REQUEST_TYPE_V1
    task_family = _safe_str(task.get("task_family") or registry.get("task_family") or task.get("family"))
    source_class = _safe_str(task.get("source_class") or registry.get("source_class") or registry.get("source") or task.get("source"))
    source_label = _safe_str(task.get("source_label") or registry.get("source_label") or registry.get("source_tag"))
    registry_id = _safe_str(task.get("registry_id") or registry.get("registry_id") or registry.get("id"))
    repo_root = _safe_str(context.get("repo_root") or task.get("repo_root") or registry.get("repo_root"))
    session_key = _safe_str(context.get("session_key") or task.get("session_key") or registry.get("session_key"))

    approved_synthetic_only = True
    requested_task_id = _safe_str(task.get("task_id") or task.get("id") or registry.get("task_id"))
    task_metadata = {
        "task_id": requested_task_id,
        "task_family": task_family,
        "source_class": source_class,
        "source_label": source_label,
        "registry_id": registry_id,
        "repo_root": repo_root,
        "session_key": session_key,
        "task_labels": _safe_list(task.get("task_labels") or registry.get("task_labels")),
        "source_tags": _safe_list(task.get("source_tags") or registry.get("source_tags")),
        "approved_synthetic_only": approved_synthetic_only,
    }

    authority = {
        "public_live_authority": False,
        "public_ux_authority": False,
        "voice_authority": False,
        "final_answer_authority": False,
        "runtime_wiring_authority": False,
        "benchmark_submission_authority": False,
        "official_claim_authority": False,
        "raw_persistence_authority": False,
        "private_memory_authority": False,
        "model_call_authority": False,
        "search_call_authority": False,
        "advisor_call_authority": False,
        "unknown_engine_authority": False,
        "automatic_lesson_promotion_authority": False,
    }

    request = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "request_type": request_type,
        "request_status": "draft",
        "task_metadata": task_metadata,
        "registry_metadata": {
            "registry_id": registry_id,
            "source_class": source_class,
            "source_label": source_label,
        },
        "session_context": {
            "repo_root": repo_root,
            "session_key": session_key,
        },
        "denied_authority_flags": list(DENIED_AUTHORITY_FLAGS_V1),
        "unknown_engine_roles": [],
        "authority": authority,
        "raw_response_storage_requested": False,
        "feature_flag_enabled": False,
        "result_label": OBSERVATION_LABEL_NEEDS_REVIEW_V1,
        "gap_labels": [],
        "predicted_labels": [],
        "observed_labels": [],
        "raw_response_text": None,
        "raw_response_text_requested": False,
    }

    return to_real_response_executor_adapter_json_safe_v1(request)


def validate_real_response_executor_adapter_preflight_v1(
    request: Mapping[str, Any] | None,
    session_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a metadata-only request and fail closed on unsafe input."""

    req = _as_mapping(request)
    context = _as_mapping(session_context)
    task_metadata = _as_mapping(req.get("task_metadata"))
    registry_metadata = _as_mapping(req.get("registry_metadata"))
    request_session = _as_mapping(req.get("session_context"))
    authority = _as_mapping(req.get("authority"))

    task_family = _safe_str(task_metadata.get("task_family") or req.get("task_family"))
    source_class = _safe_str(task_metadata.get("source_class") or registry_metadata.get("source_class") or req.get("source_class"))
    source_label = _safe_str(task_metadata.get("source_label") or registry_metadata.get("source_label") or req.get("source_label"))
    registry_id = _safe_str(task_metadata.get("registry_id") or registry_metadata.get("registry_id") or req.get("registry_id"))
    repo_root = _safe_str(request_session.get("repo_root") or context.get("repo_root") or req.get("repo_root"))
    session_key = _safe_str(request_session.get("session_key") or context.get("session_key") or req.get("session_key"))

    denied_authority_flags = _normalize_authority_flags(req.get("denied_authority_flags") or authority.keys())
    unknown_engine_roles = _normalize_unknown_engine_roles(req.get("unknown_engine_roles"))
    feature_flag_enabled = bool(req.get("feature_flag_enabled"))
    raw_response_storage_requested = bool(req.get("raw_response_storage_requested") or req.get("raw_response_text_requested"))

    block_reason_labels: list[str] = []

    if not repo_root:
        block_reason_labels.append("missing_repo_root")
    if not session_key:
        block_reason_labels.append("missing_session_key")
    if not task_family:
        block_reason_labels.append("task_family_not_allowed")
    elif not _is_allowed_task_family(task_family):
        block_reason_labels.append("task_family_not_allowed")
    if not source_class:
        block_reason_labels.append("source_class_missing")
    elif not _is_allowed_source_class(source_class):
        if source_class in BLOCKED_SOURCE_LABELS_V1:
            block_reason_labels.append("blocked_source_label")
        else:
            block_reason_labels.append("source_class_not_allowed")
    if not source_label:
        block_reason_labels.append("source_label_missing")
    elif _is_blocked_source_label(source_label):
        block_reason_labels.append("blocked_source_label")
    elif source_label not in ALLOWED_SOURCE_LABELS_V1:
        block_reason_labels.append("source_class_not_allowed")
    if not registry_id:
        block_reason_labels.append("registry_id_missing")
    if not registry_metadata:
        block_reason_labels.append("registry_metadata_missing")

    if task_metadata.get("requires_private_memory") is True or req.get("requires_private_memory") is True:
        block_reason_labels.append("private_memory_requested")
    if task_metadata.get("requires_dot_weslr") is True or req.get("requires_dot_weslr") is True:
        block_reason_labels.append("dot_weslr_requested")

    authority_checks = {
        "public_live_authority": req.get("public_live_authority") or authority.get("public_live_authority"),
        "public_ux_authority": req.get("public_ux_authority") or authority.get("public_ux_authority"),
        "voice_authority": req.get("voice_authority") or authority.get("voice_authority"),
        "final_answer_authority": req.get("final_answer_authority") or authority.get("final_answer_authority"),
        "runtime_wiring_authority": req.get("runtime_wiring_authority") or authority.get("runtime_wiring_authority"),
        "benchmark_submission_authority": req.get("benchmark_submission_authority") or authority.get("benchmark_submission_authority"),
        "official_claim_authority": req.get("official_claim_authority") or authority.get("official_claim_authority"),
        "raw_persistence_authority": req.get("raw_persistence_authority") or authority.get("raw_persistence_authority"),
        "private_memory_authority": req.get("private_memory_authority") or authority.get("private_memory_authority"),
        "model_call_authority": req.get("model_call_authority") or authority.get("model_call_authority"),
        "search_call_authority": req.get("search_call_authority") or authority.get("search_call_authority"),
        "advisor_call_authority": req.get("advisor_call_authority") or authority.get("advisor_call_authority"),
        "unknown_engine_authority": req.get("unknown_engine_authority") or authority.get("unknown_engine_authority"),
        "automatic_lesson_promotion_authority": req.get("automatic_lesson_promotion_authority") or authority.get("automatic_lesson_promotion_authority"),
    }

    if any(bool(value) for value in authority_checks.values()):
        for key, value in authority_checks.items():
            if bool(value):
                if key in {"public_live_authority", "public_ux_authority", "voice_authority"}:
                    block_reason_labels.append("public_live_voice_authority_requested")
                elif key == "final_answer_authority":
                    block_reason_labels.append("final_answer_authority_requested")
                elif key == "official_claim_authority":
                    block_reason_labels.append("official_claim_requested")
                elif key in {"raw_persistence_authority", "private_memory_authority"}:
                    block_reason_labels.append("raw_persistence_requested")
                elif key == "unknown_engine_authority":
                    block_reason_labels.append("unknown_engine_authority_requested")
                else:
                    block_reason_labels.append("unsupported_authority_flag_requested")

    if feature_flag_enabled:
        block_reason_labels.append("feature_flag_enabled")
    if raw_response_storage_requested:
        block_reason_labels.append("raw_persistence_requested")

    if req.get("official_claims") is True:
        block_reason_labels.append("official_claim_requested")

    for role in unknown_engine_roles:
        if role in FORBIDDEN_UNKNOWN_ENGINE_ROLES_V1:
            block_reason_labels.append("unknown_engine_authority_requested")
        elif role not in ALLOWED_UNKNOWN_ENGINE_ROLES_V1:
            block_reason_labels.append("unknown_engine_authority_requested")

    allowed = not block_reason_labels
    if allowed:
        return {
            "helper_type": HELPER_TYPE_V1,
            "boundary_type": BOUNDARY_TYPE_V1,
            "preflight_status": PLAN_STATUS_ALLOWED_PENDING_OPERATOR_REVIEW_V1,
            "allowed": True,
            "blocked": False,
            "block_reason_labels": [],
            "task_family": task_family,
            "source_class": source_class,
            "source_label": source_label,
            "registry_id": registry_id,
            "repo_root": repo_root,
            "session_key": session_key,
            "denied_authority_flags": sorted(set(denied_authority_flags)),
            "unknown_engine_roles": [role for role in unknown_engine_roles if role in ALLOWED_UNKNOWN_ENGINE_ROLES_V1],
            "feature_flag_enabled": False,
            "raw_response_storage_requested": False,
            "final_answer_authority": False,
            "user_facing_prose_authority": False,
            "live_runtime_authority": False,
            "public_live_authority": False,
            "official_claims": False,
        }

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "preflight_status": PLAN_STATUS_BLOCKED_V1,
        "allowed": False,
        "blocked": True,
        "block_reason_labels": _unique_sorted(block_reason_labels),
        "task_family": task_family,
        "source_class": source_class,
        "source_label": source_label,
        "registry_id": registry_id,
        "repo_root": repo_root,
        "session_key": session_key,
        "denied_authority_flags": sorted(set(denied_authority_flags)),
        "unknown_engine_roles": [role for role in unknown_engine_roles if role in ALLOWED_UNKNOWN_ENGINE_ROLES_V1],
        "feature_flag_enabled": bool(feature_flag_enabled),
        "raw_response_storage_requested": bool(raw_response_storage_requested),
        "final_answer_authority": bool(authority_checks.get("final_answer_authority")),
        "user_facing_prose_authority": bool(authority_checks.get("public_ux_authority") or authority_checks.get("voice_authority")),
        "live_runtime_authority": bool(authority_checks.get("runtime_wiring_authority") or authority_checks.get("public_live_authority")),
        "public_live_authority": bool(authority_checks.get("public_live_authority")),
        "official_claims": bool(req.get("official_claims") or authority_checks.get("official_claim_authority")),
    }


def _unique_sorted(labels: list[str]) -> list[str]:
    return sorted(set(labels), key=lambda item: item)


def build_real_response_executor_adapter_call_plan_v1(
    request: Mapping[str, Any] | None,
    preflight: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a non-executing call plan."""

    req = _as_mapping(request)
    pre = _as_mapping(preflight) if preflight is not None else validate_real_response_executor_adapter_preflight_v1(req)
    allowed = bool(pre.get("allowed")) and pre.get("preflight_status") == PLAN_STATUS_ALLOWED_PENDING_OPERATOR_REVIEW_V1

    plan_status = PLAN_STATUS_ALLOWED_PENDING_OPERATOR_REVIEW_V1 if allowed else PLAN_STATUS_BLOCKED_V1
    block_reason_labels = _unique_sorted(list(pre.get("block_reason_labels") or []))
    task_metadata = _as_mapping(req.get("task_metadata"))
    task_family = _safe_str(pre.get("task_family") or task_metadata.get("task_family") or req.get("task_family"))

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "plan_type": CALL_PLAN_TYPE_V1,
        "plan_status": plan_status,
        "preflight_status": pre.get("preflight_status", PLAN_STATUS_BLOCKED_V1),
        "preflight_allowed": allowed,
        "task_family": task_family,
        "source_label": _safe_str(pre.get("source_label")),
        "registry_id": _safe_str(pre.get("registry_id")),
        "callable_invocation_allowed": False,
        "live_call_allowed": False,
        "chat_responder_call_allowed": False,
        "model_call_allowed": False,
        "search_call_allowed": False,
        "advisor_call_allowed": False,
        "execution_callable": None,
        "operator_review_required": True,
        "should_execute": False,
        "blocked_reason_labels": block_reason_labels,
        "callable_target_kind": "adapter_wrapper",
        "planned_result_labels": _safe_list(req.get("result_label")),
        "planned_gap_labels": _safe_list(req.get("gap_labels")),
        "planned_predicted_labels": _safe_list(req.get("predicted_labels")),
        "planned_observed_labels": _safe_list(req.get("observed_labels")),
    }


def normalize_real_response_executor_adapter_observation_v1(
    observation: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Normalize an observation using metadata labels only."""

    obs = _as_mapping(observation)
    result_label = _safe_str(obs.get("result_label"))
    gap_labels = _safe_list(obs.get("gap_labels"))
    predicted_labels = _safe_list(obs.get("predicted_labels"))
    observed_labels = _safe_list(obs.get("observed_labels"))
    blocked_reason_labels = _safe_list(obs.get("blocked_reason_labels"))
    denied_authority_flags = _safe_list(obs.get("denied_authority_flags"))

    block_reason_labels: list[str] = []

    if result_label and result_label not in ALLOWED_RESULT_LABELS_V1:
        block_reason_labels.append("unknown_result_label")
        result_label = OBSERVATION_LABEL_BLOCKED_V1

    gap_labels = [label for label in gap_labels if label in ALLOWED_GAP_LABELS_V1]
    if obs.get("gap_labels") and len(gap_labels) != len(_safe_list(obs.get("gap_labels"))):
        block_reason_labels.append("unknown_gap_label")

    predicted_labels = [label for label in predicted_labels if label in ALLOWED_PREDICTED_LABELS_V1]
    if obs.get("predicted_labels") and len(predicted_labels) != len(_safe_list(obs.get("predicted_labels"))):
        block_reason_labels.append("unknown_predicted_label")

    observed_labels = [label for label in observed_labels if label in ALLOWED_OBSERVED_LABELS_V1]
    if obs.get("observed_labels") and len(observed_labels) != len(_safe_list(obs.get("observed_labels"))):
        block_reason_labels.append("unknown_observed_label")

    raw_response_text_present = bool(_safe_str(obs.get("raw_response_text")))
    raw_response_text_retained = False
    raw_response_text_redacted = raw_response_text_present
    if raw_response_text_present:
        block_reason_labels.append("raw_response_text_provided")

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "observation_type": OBSERVATION_TYPE_V1,
        "observation_status": OBSERVATION_LABEL_BLOCKED_V1 if block_reason_labels else (result_label or OBSERVATION_LABEL_NEEDS_REVIEW_V1),
        "result_label": result_label or OBSERVATION_LABEL_NEEDS_REVIEW_V1,
        "gap_labels": gap_labels,
        "predicted_labels": predicted_labels,
        "observed_labels": observed_labels,
        "blocked_reason_labels": _unique_sorted(block_reason_labels + blocked_reason_labels),
        "denied_authority_flags": denied_authority_flags,
        "raw_response_text_present": raw_response_text_present,
        "raw_response_text_retained": raw_response_text_retained,
        "raw_response_text_redacted": raw_response_text_redacted,
        "final_answer_authority": False,
        "user_facing_prose_authority": False,
        "live_runtime_authority": False,
        "public_live_authority": False,
        "official_claims": False,
    }


def build_real_response_executor_adapter_result_packet_v1(
    request: Mapping[str, Any] | None,
    preflight: Mapping[str, Any] | None,
    call_plan: Mapping[str, Any] | None,
    observation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a metadata-only packet for operator review."""

    req = _as_mapping(request)
    pre = _as_mapping(preflight)
    plan = _as_mapping(call_plan)
    task_metadata = _as_mapping(req.get("task_metadata"))
    obs = normalize_real_response_executor_adapter_observation_v1(observation) if observation is not None else {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "observation_type": OBSERVATION_TYPE_V1,
        "observation_status": OBSERVATION_LABEL_NEEDS_REVIEW_V1,
        "result_label": OBSERVATION_LABEL_NEEDS_REVIEW_V1,
        "gap_labels": [],
        "predicted_labels": [],
        "observed_labels": [],
        "blocked_reason_labels": [],
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

    packet_status = PLAN_STATUS_BLOCKED_V1 if pre.get("blocked") or plan.get("plan_status") == PLAN_STATUS_BLOCKED_V1 or obs.get("observation_status") == OBSERVATION_LABEL_BLOCKED_V1 else PLAN_STATUS_ALLOWED_PENDING_OPERATOR_REVIEW_V1
    blocked_labels = _unique_sorted(list(pre.get("block_reason_labels") or []) + list(plan.get("blocked_reason_labels") or []) + list(obs.get("blocked_reason_labels") or []))
    denied_authority_flags = _unique_sorted(list(pre.get("denied_authority_flags") or []) + list(obs.get("denied_authority_flags") or []))

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "packet_type": RESULT_PACKET_TYPE_V1,
        "packet_status": packet_status,
        "preflight_status": pre.get("preflight_status", PLAN_STATUS_BLOCKED_V1),
        "plan_status": plan.get("plan_status", PLAN_STATUS_BLOCKED_V1),
        "observation_status": obs.get("observation_status", OBSERVATION_LABEL_NEEDS_REVIEW_V1),
        "task_family": _safe_str(pre.get("task_family") or task_metadata.get("task_family") or req.get("task_family")),
        "registry_id": _safe_str(pre.get("registry_id")),
        "source_label": _safe_str(pre.get("source_label")),
        "blocked_reason_labels": blocked_labels,
        "denied_authority_flags": denied_authority_flags,
        "result_label": obs.get("result_label", OBSERVATION_LABEL_NEEDS_REVIEW_V1),
        "gap_labels": _safe_list(obs.get("gap_labels")),
        "predicted_labels": _safe_list(obs.get("predicted_labels")),
        "observed_labels": _safe_list(obs.get("observed_labels")),
        "preflight_summary": {
            "allowed": bool(pre.get("allowed")),
            "blocked": bool(pre.get("blocked")),
            "block_reason_count": len(pre.get("block_reason_labels") or []),
        },
        "plan_summary": {
            "should_execute": bool(plan.get("should_execute")),
            "callable_invocation_allowed": bool(plan.get("callable_invocation_allowed")),
            "blocked_reason_count": len(plan.get("blocked_reason_labels") or []),
        },
        "observation_summary": {
            "raw_response_text_present": bool(obs.get("raw_response_text_present")),
            "raw_response_text_retained": bool(obs.get("raw_response_text_retained")),
            "raw_response_text_redacted": bool(obs.get("raw_response_text_redacted")),
            "blocked_reason_count": len(obs.get("blocked_reason_labels") or []),
        },
        "final_answer_authority": False,
        "user_facing_prose_authority": False,
        "live_runtime_authority": False,
        "public_live_authority": False,
        "official_claims": False,
    }


def summarize_real_response_executor_adapter_v1(packet: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return safe summary counts and status only."""

    pkt = _as_mapping(packet)
    pre = _as_mapping(pkt.get("preflight_summary"))
    plan = _as_mapping(pkt.get("plan_summary"))
    obs = _as_mapping(pkt.get("observation_summary"))

    blocked_reason_labels = _safe_list(pkt.get("blocked_reason_labels"))
    denied_authority_flags = _safe_list(pkt.get("denied_authority_flags"))
    gap_labels = _safe_list(pkt.get("gap_labels"))
    predicted_labels = _safe_list(pkt.get("predicted_labels"))
    observed_labels = _safe_list(pkt.get("observed_labels"))

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "packet_status": _safe_str(pkt.get("packet_status")),
        "preflight_status": _safe_str(pkt.get("preflight_status")),
        "plan_status": _safe_str(pkt.get("plan_status")),
        "observation_status": _safe_str(pkt.get("observation_status")),
        "blocked_reason_count": len(blocked_reason_labels),
        "denied_authority_flag_count": len(denied_authority_flags),
        "gap_label_count": len(gap_labels),
        "predicted_label_count": len(predicted_labels),
        "observed_label_count": len(observed_labels),
        "raw_response_text_present": bool(obs.get("raw_response_text_present")),
        "raw_response_text_retained": bool(obs.get("raw_response_text_retained")),
        "raw_response_text_redacted": bool(obs.get("raw_response_text_redacted")),
        "preflight_allowed": bool(pre.get("allowed")),
        "preflight_blocked": bool(pre.get("blocked")),
        "plan_should_execute": bool(plan.get("should_execute")),
        "plan_callable_invocation_allowed": bool(plan.get("callable_invocation_allowed")),
        "final_answer_authority": bool(pkt.get("final_answer_authority")),
        "user_facing_prose_authority": bool(pkt.get("user_facing_prose_authority")),
        "live_runtime_authority": bool(pkt.get("live_runtime_authority")),
        "public_live_authority": bool(pkt.get("public_live_authority")),
        "official_claims": bool(pkt.get("official_claims")),
    }
