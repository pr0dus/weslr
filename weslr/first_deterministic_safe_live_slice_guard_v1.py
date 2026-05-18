"""First deterministic-safe live slice guard V1.

Pure metadata guard for the single approved candidate shape. This module does
not execute prompts, route runtime traffic, persist state, or call external
providers.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

FEATURE_FLAG_ENV_V1 = "WESLR_ENABLE_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_V1"
GUARD_VERSION_V1 = "first_deterministic_safe_live_slice_guard_v1"
CANDIDATE_PROMPT_ID_V1 = "ordinary_task_behavior_001"
CANDIDATE_FAMILY_V1 = "ordinary_task_behavior"
CANDIDATE_ROUTE_CLASS_V1 = "safe_keyword_branch"

FORBIDDEN_ROUTE_CLASSES_V1 = {
    "forbidden_model_path",
    "forbidden_search_or_advisor_path",
    "ambiguous_needs_review",
    "requires_generate_chat_mock",
}

FALSE_LIKE_FLAG_VALUES_V1 = {"", "0", "false", "False", "FALSE", "no", "No", "NO", "off", "Off", "OFF"}

FORBIDDEN_OUTPUT_KEYS_V1 = {
    "raw_text",
    "raw_prompt",
    "prompt_text",
    "response_text",
    "final_answer",
    "full_conversation",
    "hidden_prompt",
    "answer_key",
}

BLOCKED_FAMILY_LABELS_V1 = {
    "unsupported_family_blocked",
    "blocked_family",
    "blocked_by_boundary",
}

SEARCH_OR_STATUS_LABEL_PARTS_V1 = (
    "search",
    "advisor",
    "source",
    "currentness",
    "current_status",
    "status_path",
)

MODEL_LABEL_PARTS_V1 = (
    "model_path",
    "model_call",
)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _get_flag_value(env: Mapping[str, Any] | None) -> Any:
    source = os.environ if env is None else env
    return source.get(FEATURE_FLAG_ENV_V1)


def _bool_value(value: Any) -> bool:
    return value is True


def _reason_labels(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]


def _has_label(labels: list[str], candidates: set[str]) -> bool:
    return any(label in candidates for label in labels)


def _has_label_part(labels: list[str], parts: tuple[str, ...]) -> bool:
    return any(part in label for label in labels for part in parts)


def _contains_forbidden_output_key(mapping: Mapping[str, Any]) -> bool:
    return bool(set(str(key) for key in mapping.keys()) & FORBIDDEN_OUTPUT_KEYS_V1)


def evaluate_first_deterministic_safe_live_slice_guard_v1(
    prompt_item: Mapping[str, Any] | None,
    validator_result: Mapping[str, Any] | None,
    env: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return metadata-only allow/block status for the exact candidate.

    Safe default is block. Inputs are treated as metadata dictionaries. The
    returned object intentionally excludes raw/content-bearing fields.
    """

    item = _as_mapping(prompt_item)
    validator = _as_mapping(validator_result)
    labels = _reason_labels(validator.get("reason_labels"))

    prompt_id = str(item.get("prompt_id", ""))
    family = str(item.get("family", ""))
    route_class = str(validator.get("route_class", ""))
    alignment_status = str(validator.get("alignment_status", ""))
    flag_value = _get_flag_value(env)
    feature_flag_enabled = flag_value == "1"

    blocked_by_boundary = _bool_value(validator.get("blocked_by_boundary"))
    safe_to_call = _bool_value(validator.get("safe_to_call"))
    requires_mock = _bool_value(validator.get("requires_mock"))
    routing_validator_applied = _bool_value(validator.get("routing_validator_applied"))

    model_path_reachable = bool(
        validator.get("model_calls")
        or item.get("requires_model_call")
        or route_class == "forbidden_model_path"
        or _has_label_part(labels, MODEL_LABEL_PARTS_V1)
    )
    search_path_reachable = bool(
        validator.get("search_calls")
        or validator.get("advisor_calls")
        or item.get("requires_search")
        or route_class == "forbidden_search_or_advisor_path"
        or _has_label_part(labels, SEARCH_OR_STATUS_LABEL_PARTS_V1)
    )
    write_risk = bool(validator.get("writes") or item.get("requires_memory_write") or validator.get("write_path_present"))
    raw_retention_risk = bool(
        validator.get("raw_text_retained")
        or validator.get("raw_response_retained")
        or validator.get("raw_prompt_retained")
        or _contains_forbidden_output_key(validator)
    )
    weslr_write_risk = bool(validator.get("weslr_writes") or validator.get("dot_weslr_writes") or validator.get("dot_weslr_write_risk"))
    generate_path_reachable = bool(
        validator.get("generate_chat_reachable")
        or validator.get("generate_chat_calls")
        or route_class == "requires_generate_chat_mock"
        or requires_mock
    )
    blocked_family_detected = bool(
        blocked_by_boundary
        or alignment_status == "blocked_by_boundary"
        or _has_label(labels, BLOCKED_FAMILY_LABELS_V1)
    )

    block_reason_labels: list[str] = []
    if not feature_flag_enabled:
        if flag_value in FALSE_LIKE_FLAG_VALUES_V1 or flag_value is None:
            block_reason_labels.append("feature_flag_disabled")
        else:
            block_reason_labels.append("feature_flag_not_exact_1")
    if prompt_id != CANDIDATE_PROMPT_ID_V1:
        block_reason_labels.append("prompt_id_mismatch")
    if family != CANDIDATE_FAMILY_V1:
        block_reason_labels.append("family_mismatch")
    if route_class != CANDIDATE_ROUTE_CLASS_V1:
        block_reason_labels.append("route_class_mismatch")
    if not routing_validator_applied:
        block_reason_labels.append("routing_validator_not_applied_first")
    if alignment_status != "aligned":
        block_reason_labels.append("alignment_not_aligned")
    if not safe_to_call:
        block_reason_labels.append("safe_to_call_false")
    if requires_mock:
        block_reason_labels.append("requires_mock_true")
    if route_class in FORBIDDEN_ROUTE_CLASSES_V1:
        block_reason_labels.append(f"forbidden_route_class:{route_class}")
    if blocked_family_detected:
        block_reason_labels.append("blocked_family_or_boundary_detected")
    if search_path_reachable:
        block_reason_labels.append("source_currentness_search_status_or_advisor_path_detected")
    if write_risk:
        block_reason_labels.append("write_path_risk_detected")
    if raw_retention_risk:
        block_reason_labels.append("raw_retention_risk_detected")
    if weslr_write_risk:
        block_reason_labels.append("dot_weslr_write_risk_detected")
    if model_path_reachable:
        block_reason_labels.append("model_path_reachable")
    if generate_path_reachable:
        block_reason_labels.append("generate_path_reachable")

    allowed = not block_reason_labels

    return {
        "guard_version": GUARD_VERSION_V1,
        "first_deterministic_safe_live_slice_guard_applied": True,
        "feature_flag_enabled": feature_flag_enabled,
        "allowed": allowed,
        "candidate_prompt_id": CANDIDATE_PROMPT_ID_V1,
        "prompt_id": prompt_id,
        "family": family,
        "route_class": route_class,
        "routing_validator_applied": routing_validator_applied,
        "alignment_status": alignment_status,
        "safe_to_call": safe_to_call,
        "requires_mock": requires_mock,
        "blocked_by_boundary": blocked_by_boundary,
        "model_calls": False,
        "search_calls": False,
        "advisor_calls": False,
        "writes": False,
        "raw_text_retained": False,
        "block_reason_labels": block_reason_labels,
    }
