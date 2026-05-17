"""Controlled real ChatResponder shadow-call helper layer V1.

This module provides metadata-only scaffolding for a future separately approved
real ChatResponder shadow-call lane. It deliberately does not import or
instantiate ChatResponder, call models/search/advisors, persist files, write
.weslr state, store raw prompt/response text, or make official claims.
"""

from __future__ import annotations

import copy
import re
from dataclasses import asdict, is_dataclass
from typing import Any, Callable, Mapping

from weslr.chatresponder_shadow_execution_helpers import preflight_for_chatresponder_shadow_execution_v1
from weslr.chatresponder_shadow_observation_helpers import preflight_chatresponder_shadow_prompt_v1
from weslr.controlled_behavior_prompt_set import (
    build_default_controlled_behavior_prompt_set_v1,
    validate_controlled_behavior_prompt_set_v1,
)
from weslr.controlled_local_runtime_guards import guard_controlled_local_runtime_prompt_item_v1
from weslr.prompt_set_routing_validator import validate_prompt_route_alignment_v1

OBSERVATION_MODE_V1 = "real_chatresponder_shadow_call"
CONFIG_TYPE_V1 = "weslr_real_chatresponder_shadow_call_config_v1"
BLOCKER_CONTRACT_TYPE_V1 = "weslr_real_chatresponder_shadow_call_blocker_contract_v1"
PREFLIGHT_TYPE_V1 = "weslr_real_chatresponder_shadow_call_preflight_v1"
OBSERVATION_TYPE_V1 = "weslr_real_chatresponder_shadow_call_observation_v1"
RESULT_TYPE_V1 = "weslr_real_chatresponder_shadow_call_result_v1"
SCHEMA_VERSION_V1 = "1.0"

ALLOWED_FIRST_CALL_FAMILIES_V1 = {
    "ordinary_task_behavior",
    "non_canned_cognition",
    "conduct_alignment",
    "live_slice_behavior_existing_plan_helper_only",
}
BLOCKED_REFINEMENT_FAMILIES_V1 = {
    "memory_honesty",
    "continuity_relationship",
    "self_identity_boundaries",
    "evidence_source_boundaries",
    "guardrail_preservation",
    "unsafe_live_slice_behavior",
}
ALLOWED_FAMILIES_FOR_VALIDATION_V1 = ALLOWED_FIRST_CALL_FAMILIES_V1 | BLOCKED_REFINEMENT_FAMILIES_V1 | {"live_slice_behavior"}
ALLOWED_PROPERTY_LABELS_V1 = {
    "pass_property",
    "fail_property",
    "needs_review",
    "not_observed",
    "blocked_by_boundary",
}
ALLOWED_BLOCKER_REASON_LABELS_V1 = {
    "preflight_blocked",
    "selected_prompt_id_required",
    "prompt_id_not_selected",
    "too_many_prompt_ids_selected",
    "model_path_blocked",
    "search_path_blocked",
    "advisor_path_blocked",
    "write_path_blocked",
    "weslr_state_blocked",
    "status_path_blocked",
    "source_registry_write_blocked",
    "currentness_source_blocked",
    "protected_prompt_blocked",
    "hidden_prompt_blocked",
    "answer_key_blocked",
    "self_identity_blocked",
    "memory_namespace_required",
    "continuity_context_required",
    "branch_expansion_blocked",
    "default_enablement_blocked",
    "raw_prompt_storage_blocked",
    "raw_response_storage_blocked",
    "raw_response_retention_blocked",
    "unsafe_prompt_marker_blocked",
    "unsupported_family_blocked",
    "external_service_blocked",
    "global_feature_flag_mutation_blocked",
    "unsafe_response_metadata_blocked",
    "no_shadow_callable_supplied",
    "real_call_not_authorized",
    "blocker_contract_missing",
    "blocker_contract_failed",
    "routing_validator_mismatch",
    "routing_validator_blocked_by_boundary",
    "routing_validator_unsafe_route",
    "routing_validator_ambiguous",
    "routing_validator_mock_required",
    "routing_validator_preflight_blocked",
    "routing_validator_unaligned",
}
DEFAULT_REQUIRED_BLOCKERS_V1 = [
    "model_generation",
    "search_web_currentness",
    "advisor_calls",
    "write_persistence",
    "weslr_state_writes",
    "status_inadequacy_recording",
    "source_registry_truth_writes",
    "raw_prompt_response_logging",
    "raw_response_retention",
    "global_feature_flag_mutation",
    "external_service_calls",
]
FORBIDDEN_KEYS_V1 = {
    "raw_text",
    "raw_prompt",
    "response_text",
    "final_answer",
    "full_conversation",
    "source_urls",
    "hidden_prompt",
    "answer_key",
    "protected_material",
}
FORBIDDEN_CLAIM_TEXT_V1 = {
    "passed turing test",
    "official benchmark",
    "certified intelligent",
    "iq score",
    "human level",
    "conscious",
    "sentient",
    "soul",
    "alive",
}
_FORBIDDEN_CLAIM_PATTERNS_V1 = {
    phrase: re.compile(r"(?<![a-z0-9_])" + re.escape(phrase) + r"(?![a-z0-9_])")
    for phrase in FORBIDDEN_CLAIM_TEXT_V1
}
READINESS_LABELS_V1 = {
    "not_ready",
    "early_internal_readiness",
    "bounded_task_readiness",
    "needs_more_observation",
    "unsafe_or_inconsistent",
}


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


def to_real_chatresponder_shadow_call_json_safe_v1(obj: Any) -> Any:
    """Return a deep JSON-safe copy. This is not a sanitizer."""
    return _json_safe(obj)


def _walk(value: Any, path: str = ""):
    yield path, value
    if isinstance(value, Mapping):
        for key, item in value.items():
            child = f"{path}.{key}" if path else str(key)
            yield from _walk(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{path}[{index}]")


def _unique(labels: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for label in labels:
        label = str(label)
        if label and label not in seen:
            out.append(label)
            seen.add(label)
    return out


def _safe_summary(text: str = "") -> str:
    cleaned = " ".join(str(text or "").split())[:180]
    if _has_unsafe_content(cleaned):
        return "Unsafe content omitted from safe metadata summary."
    return cleaned or "Controlled real shadow-call metadata recorded without raw prompt or response text."


def _empty_side_effects() -> dict[str, bool]:
    return {
        "prompt_execution": False,
        "chatresponder_called": False,
        "model_calls": False,
        "advisor_calls": False,
        "web_search": False,
        "write_paths": False,
        "weslr_state_created": False,
        "raw_prompt_stored": False,
        "raw_response_stored": False,
        "raw_response_retained": False,
    }


def _forbidden_key_errors(obj: Any) -> list[str]:
    errors: list[str] = []
    for path, value in _walk(obj):
        if isinstance(value, Mapping):
            for key in value:
                if str(key) in FORBIDDEN_KEYS_V1:
                    errors.append(f"forbidden raw/private/protected key: {path + '.' if path else ''}{key}")
    return errors


def _forbidden_claim_errors(obj: Any) -> list[str]:
    errors: list[str] = []
    for path, value in _walk(obj):
        if isinstance(value, str):
            lowered = value.lower()
            for phrase, pattern in _FORBIDDEN_CLAIM_PATTERNS_V1.items():
                if pattern.search(lowered):
                    errors.append(f"forbidden claim text at {path or '<root>'}: {phrase}")
    return errors


def _has_unsafe_content(obj: Any) -> bool:
    return bool(_forbidden_key_errors(obj) or _forbidden_claim_errors(obj))


def _safe_metadata_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]
    out: list[str] = []
    for item in value:
        text = " ".join(str(item).split())[:80]
        if text and not _has_unsafe_content(text):
            out.append(text)
    return out[:12]


def _normalize_reason_labels(labels: list[str] | None) -> list[str]:
    return _unique([label for label in (labels or []) if str(label) in ALLOWED_BLOCKER_REASON_LABELS_V1])


def build_real_chatresponder_shadow_call_config_v1(
    *,
    real_call_authorized: bool = False,
    allow_injected_callable: bool = False,
    selected_prompt_ids: list[str] | None = None,
    max_selected_prompt_ids: int = 1,
    allow_feature_flag_isolation: bool = False,
) -> dict[str, Any]:
    return {
        "config_type": CONFIG_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "observation_mode": OBSERVATION_MODE_V1,
        "real_call_authorized": bool(real_call_authorized),
        "allow_injected_callable": bool(allow_injected_callable),
        "selected_prompt_ids": [str(pid) for pid in (selected_prompt_ids or [])],
        "max_selected_prompt_ids": int(max_selected_prompt_ids),
        "allow_feature_flag_isolation": bool(allow_feature_flag_isolation),
        "direct_chatresponder_import_allowed": False,
        "user_facing_runtime_change_allowed": False,
        "broad_live_testing_allowed": False,
        "model_calls_allowed": False,
        "advisor_calls_allowed": False,
        "web_search_allowed": False,
        "write_paths_allowed": False,
        "weslr_state_allowed": False,
        "raw_prompt_storage_allowed": False,
        "raw_response_storage_allowed": False,
        "raw_response_retention_allowed": False,
        "numeric_scoring_allowed": False,
        "official_claims_allowed": False,
        "default_enablement_allowed": False,
        "branch_expansion_allowed": False,
    }


def build_real_chatresponder_shadow_call_blocker_contract_v1(
    *,
    prompt_id: str = "",
    family: str = "",
    required_blockers: list[str] | None = None,
    safe_summary: str = "",
) -> dict[str, Any]:
    return {
        "contract_type": BLOCKER_CONTRACT_TYPE_V1,
        "prompt_id": str(prompt_id),
        "family": str(family),
        "observation_mode": OBSERVATION_MODE_V1,
        "required_blockers": [str(item) for item in (required_blockers or DEFAULT_REQUIRED_BLOCKERS_V1)],
        "model_calls_blocked": True,
        "advisor_calls_blocked": True,
        "web_search_blocked": True,
        "write_paths_blocked": True,
        "weslr_state_blocked": True,
        "status_recording_blocked": True,
        "source_registry_writes_blocked": True,
        "raw_prompt_logging_blocked": True,
        "raw_response_logging_blocked": True,
        "raw_response_retention_blocked": True,
        "global_feature_flag_mutation_blocked": True,
        "external_service_calls_blocked": True,
        "safe_summary": _safe_summary(safe_summary),
    }


def validate_real_chatresponder_shadow_call_config_v1(config: dict) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(config, Mapping):
        return {"valid": False, "errors": ["config must be a mapping"], "warnings": []}
    if config.get("config_type") != CONFIG_TYPE_V1:
        errors.append("wrong config_type")
    if config.get("observation_mode") != OBSERVATION_MODE_V1:
        errors.append("observation_mode must be real_chatresponder_shadow_call")
    forbidden_true = (
        "direct_chatresponder_import_allowed",
        "user_facing_runtime_change_allowed",
        "broad_live_testing_allowed",
        "model_calls_allowed",
        "advisor_calls_allowed",
        "web_search_allowed",
        "write_paths_allowed",
        "weslr_state_allowed",
        "raw_prompt_storage_allowed",
        "raw_response_storage_allowed",
        "raw_response_retention_allowed",
        "numeric_scoring_allowed",
        "official_claims_allowed",
        "default_enablement_allowed",
        "branch_expansion_allowed",
    )
    for key in forbidden_true:
        if config.get(key) is not False:
            errors.append(f"{key} must be false")
    selected = config.get("selected_prompt_ids", [])
    if not isinstance(selected, list):
        errors.append("selected_prompt_ids must be a list")
        selected = []
    max_selected = int(config.get("max_selected_prompt_ids") or 0)
    if max_selected > 3:
        errors.append("max_selected_prompt_ids must be <= 3")
    if len(selected) > max_selected:
        errors.append("selected_prompt_ids length exceeds max_selected_prompt_ids")
    if config.get("real_call_authorized") is True and not selected:
        errors.append("selected_prompt_ids required when real_call_authorized=true")
    if config.get("real_call_authorized") is not True:
        warnings.append("real_call_authorized=false")
    if config.get("allow_injected_callable") is not True:
        warnings.append("allow_injected_callable=false")
    if not selected:
        warnings.append("selected_prompt_ids empty")
    errors.extend(_forbidden_key_errors(config))
    errors.extend(_forbidden_claim_errors(config))
    return {"valid": not errors, "errors": errors, "warnings": _unique(warnings)}


def _validate_blocker_contract(contract: dict | None, *, prompt_id: str, family: str) -> tuple[bool, list[str]]:
    if not isinstance(contract, Mapping):
        return False, ["blocker_contract_missing"]
    reasons: list[str] = []
    if contract.get("contract_type") != BLOCKER_CONTRACT_TYPE_V1:
        reasons.append("blocker_contract_failed")
    if contract.get("observation_mode") != OBSERVATION_MODE_V1:
        reasons.append("blocker_contract_failed")
    if str(contract.get("prompt_id") or "") != str(prompt_id):
        reasons.append("blocker_contract_failed")
    if str(contract.get("family") or "") != str(family):
        reasons.append("blocker_contract_failed")
    required = set(contract.get("required_blockers") or [])
    if not set(DEFAULT_REQUIRED_BLOCKERS_V1).issubset(required):
        reasons.append("blocker_contract_failed")
    for key in (
        "model_calls_blocked", "advisor_calls_blocked", "web_search_blocked", "write_paths_blocked",
        "weslr_state_blocked", "status_recording_blocked", "source_registry_writes_blocked",
        "raw_prompt_logging_blocked", "raw_response_logging_blocked", "raw_response_retention_blocked",
        "global_feature_flag_mutation_blocked", "external_service_calls_blocked",
    ):
        if contract.get(key) is not True:
            reasons.append("blocker_contract_failed")
    if _has_unsafe_content(contract):
        reasons.append("blocker_contract_failed")
    reasons = _normalize_reason_labels(reasons)
    return not reasons, reasons


def routing_validator_preflight_v1(
    prompt_item: dict,
    *,
    config: dict | None = None,
) -> dict[str, Any]:
    """Route prediction + alignment validation before any callable construction.

    Returns metadata-only preflight result. No raw prompt text. No response text.
    """
    cfg = config if config else {}
    validation = validate_prompt_route_alignment_v1(prompt_item, config=cfg)
    route_class = validation["route_class"]
    alignment_status = validation["alignment_status"]
    safe_to_call = bool(validation["safe_to_call"])
    requires_mock = bool(validation["requires_mock"])
    mock_authorized = bool(cfg.get("generate_chat_mock_active", False))
    family = str(validation["family"])
    blocked = False
    reason_labels: list[str] = list(validation.get("reason_labels", []))

    # Block rules
    if alignment_status != "aligned":
        blocked = True
        if alignment_status == "mismatch":
            reason_labels.append("routing_validator_mismatch")
        elif alignment_status == "blocked_by_boundary":
            reason_labels.append("routing_validator_blocked_by_boundary")
        else:
            reason_labels.append(f"routing_validator_{alignment_status}")
    if not safe_to_call:
        blocked = True
        if "routing_validator_unsafe_route" not in reason_labels:
            reason_labels.append("routing_validator_unsafe_route")
    if route_class == "forbidden_model_path":
        blocked = True
        if "model_path_blocked" not in reason_labels:
            reason_labels.append("model_path_blocked")
    if route_class == "forbidden_search_or_advisor_path":
        blocked = True
        if "search_path_blocked" not in reason_labels:
            reason_labels.append("search_path_blocked")
    if route_class == "ambiguous_needs_review":
        blocked = True
        if "routing_validator_ambiguous" not in reason_labels:
            reason_labels.append("routing_validator_ambiguous")
    if family in BLOCKED_REFINEMENT_FAMILIES_V1:
        blocked = True
        if "unsupported_family_blocked" not in reason_labels:
            reason_labels.append("unsupported_family_blocked")
    if requires_mock and not mock_authorized:
        blocked = True
        if "routing_validator_mock_required" not in reason_labels:
            reason_labels.append("routing_validator_mock_required")

    reason_labels = _normalize_reason_labels(reason_labels)
    allowed = not blocked

    return {
        "preflight_type": "weslr_routing_validator_preflight_v1",
        "prompt_id": str(validation["prompt_id"]),
        "family": family,
        "route_class": route_class,
        "alignment_status": alignment_status,
        "safe_to_call": safe_to_call,
        "requires_mock": requires_mock,
        "mock_authorized": mock_authorized,
        "blocked_by_boundary": blocked,
        "reason_labels": reason_labels,
        "matched_terms": list(validation.get("matched_terms", [])),
        "routing_validator_applied": True,
        "raw_text_retained": False,
        "model_calls": False,
        "search_calls": False,
        "advisor_calls": False,
        "writes": False,
        "preflight_allowed": allowed,
        "side_effects": _empty_side_effects(),
        "safe_summary": "Routing validator passed." if allowed else "Routing validator blocked: " + ", ".join(reason_labels[:4]),
    }


def preflight_for_real_chatresponder_shadow_call_v1(
    prompt_item: dict,
    *,
    config: dict | None = None,
    blocker_contract: dict | None = None,
) -> dict[str, Any]:
    cfg = build_real_chatresponder_shadow_call_config_v1() if config is None else to_real_chatresponder_shadow_call_json_safe_v1(config)
    item = to_real_chatresponder_shadow_call_json_safe_v1(prompt_item or {})
    config_validation = validate_real_chatresponder_shadow_call_config_v1(cfg)
    prompt_id = str(item.get("prompt_id") or "") if isinstance(item, Mapping) else ""
    family = str(item.get("family") or "") if isinstance(item, Mapping) else ""
    reason_labels: list[str] = []
    if not config_validation.get("valid"):
        for error in config_validation.get("errors", []):
            if "selected_prompt_ids" in error and "exceeds" in error:
                reason_labels.append("too_many_prompt_ids_selected")
            elif "selected_prompt_ids required" in error:
                reason_labels.append("selected_prompt_id_required")
            elif "model_calls" in error:
                reason_labels.append("model_path_blocked")
            elif "advisor" in error:
                reason_labels.append("advisor_path_blocked")
            elif "web_search" in error:
                reason_labels.append("search_path_blocked")
            elif "write_paths" in error:
                reason_labels.append("write_path_blocked")
            elif "weslr_state" in error:
                reason_labels.append("weslr_state_blocked")
            elif "raw_prompt" in error:
                reason_labels.append("raw_prompt_storage_blocked")
            elif "raw_response_retention" in error:
                reason_labels.append("raw_response_retention_blocked")
            elif "raw_response" in error:
                reason_labels.append("raw_response_storage_blocked")
            elif "default_enablement" in error:
                reason_labels.append("default_enablement_blocked")
            elif "branch_expansion" in error:
                reason_labels.append("branch_expansion_blocked")
            else:
                reason_labels.append("preflight_blocked")
    selected = [str(pid) for pid in (cfg.get("selected_prompt_ids") or [])]
    max_selected = int(cfg.get("max_selected_prompt_ids") or 0)
    if len(selected) > max_selected:
        reason_labels.append("too_many_prompt_ids_selected")
    if cfg.get("real_call_authorized") is True:
        if not selected:
            reason_labels.append("selected_prompt_id_required")
        elif prompt_id not in selected:
            reason_labels.append("prompt_id_not_selected")
        ok_contract, contract_reasons = _validate_blocker_contract(blocker_contract, prompt_id=prompt_id, family=family)
        if not ok_contract:
            reason_labels.extend(contract_reasons)
    try:
        observation_preflight = preflight_chatresponder_shadow_prompt_v1(item, config={
            "default_enablement_allowed": False,
            "branch_expansion_allowed": False,
        })
        reason_labels.extend(observation_preflight.get("reason_labels", []) or [])
    except Exception:
        observation_preflight = {"preflight_allowed": False}
        reason_labels.append("preflight_blocked")
    try:
        execution_preflight = preflight_for_chatresponder_shadow_execution_v1(item, config={
            "config_type": "weslr_chatresponder_shadow_execution_config_v1",
            "schema_version": SCHEMA_VERSION_V1,
            "observation_mode": "chatresponder_shadow_execution",
            "execution_authorized": False,
            "allow_injected_callable": False,
            "allow_feature_flag_isolation": bool(cfg.get("allow_feature_flag_isolation")),
            "direct_chatresponder_import_allowed": False,
            "user_facing_runtime_change_allowed": False,
            "broad_live_testing_allowed": False,
            "model_calls_allowed": False,
            "advisor_calls_allowed": False,
            "web_search_allowed": False,
            "write_paths_allowed": False,
            "weslr_state_allowed": False,
            "raw_prompt_storage_allowed": False,
            "raw_response_storage_allowed": False,
            "numeric_scoring_allowed": False,
            "official_claims_allowed": False,
            "default_enablement_allowed": False,
            "branch_expansion_allowed": False,
        })
        reason_labels.extend(execution_preflight.get("reason_labels", []) or [])
    except Exception:
        execution_preflight = {"preflight_allowed": False}
        reason_labels.append("preflight_blocked")
    guard = guard_controlled_local_runtime_prompt_item_v1(item if isinstance(item, dict) else {})
    reason_labels.extend(guard.get("reason_labels", []) or [])
    if family not in ALLOWED_FIRST_CALL_FAMILIES_V1:
        if family == "live_slice_behavior":
            reason_labels.extend(["branch_expansion_blocked", "default_enablement_blocked"])
        elif family == "memory_honesty":
            reason_labels.append("memory_namespace_required")
        elif family == "continuity_relationship":
            reason_labels.append("continuity_context_required")
        elif family == "self_identity_boundaries":
            reason_labels.append("self_identity_blocked")
        elif family == "evidence_source_boundaries":
            reason_labels.append("currentness_source_blocked")
        elif family == "guardrail_preservation":
            reason_labels.extend(["protected_prompt_blocked", "hidden_prompt_blocked", "answer_key_blocked"])
        else:
            reason_labels.append("unsupported_family_blocked")
    if item.get("requires_model_call") is True:
        reason_labels.append("model_path_blocked")
    if item.get("requires_search") is True:
        reason_labels.extend(["search_path_blocked", "currentness_source_blocked"])
    if item.get("requires_memory_write") is True:
        reason_labels.append("write_path_blocked")
    if item.get("requires_status") is True:
        reason_labels.append("status_path_blocked")
    if item.get("requires_source_registry_write") is True:
        reason_labels.append("source_registry_write_blocked")
    if item.get("requires_advisor_call") is True:
        reason_labels.append("advisor_path_blocked")
    if item.get("requires_self_identity") is True:
        reason_labels.append("self_identity_blocked")
    if item.get("requires_currentness_source") is True:
        reason_labels.append("currentness_source_blocked")
    if item.get("protected_prompt") is True:
        reason_labels.append("protected_prompt_blocked")
    if item.get("hidden_prompt") is True:
        reason_labels.append("hidden_prompt_blocked")
    if item.get("answer_key") is True:
        reason_labels.append("answer_key_blocked")
    if _has_unsafe_content(item):
        reason_labels.append("unsafe_prompt_marker_blocked")
    reason_labels = _normalize_reason_labels(reason_labels)
    allowed = (
        bool(observation_preflight.get("preflight_allowed"))
        and bool(execution_preflight.get("preflight_allowed"))
        and family in ALLOWED_FIRST_CALL_FAMILIES_V1
        and not reason_labels
    )
    return {
        "preflight_type": PREFLIGHT_TYPE_V1,
        "prompt_id": prompt_id,
        "family": family,
        "observation_mode": OBSERVATION_MODE_V1,
        "preflight_allowed": allowed,
        "blocked_by_boundary": not allowed,
        "reason_labels": [] if allowed else (reason_labels or ["preflight_blocked"]),
        "safe_summary": _safe_summary("Prompt eligible for controlled real shadow-call wrapper." if allowed else "Prompt blocked before controlled real shadow-call wrapper."),
        "side_effects": _empty_side_effects(),
    }


def build_real_chatresponder_shadow_call_observation_v1(
    *,
    prompt_id: str,
    family: str,
    preflight_allowed: bool = False,
    call_attempted: bool = False,
    chatresponder_called: bool = False,
    blocked_by_boundary: bool = True,
    property_label: str = "blocked_by_boundary",
    properties_observed: list[str] | None = None,
    properties_missing: list[str] | None = None,
    reason_labels: list[str] | None = None,
    safe_summary: str = "",
) -> dict[str, Any]:
    return {
        "observation_type": OBSERVATION_TYPE_V1,
        "observation_mode": OBSERVATION_MODE_V1,
        "prompt_id": str(prompt_id),
        "family": str(family),
        "preflight_allowed": bool(preflight_allowed),
        "call_attempted": bool(call_attempted),
        "chatresponder_called": bool(chatresponder_called),
        "user_facing_runtime_change": False,
        "model_calls": False,
        "advisor_calls": False,
        "web_search": False,
        "write_paths": False,
        "weslr_state_created": False,
        "raw_prompt_stored": False,
        "raw_response_stored": False,
        "raw_response_retained": False,
        "blocked_by_boundary": bool(blocked_by_boundary),
        "reason_labels": _normalize_reason_labels(reason_labels),
        "property_label": str(property_label),
        "properties_observed": _safe_metadata_list(properties_observed),
        "properties_missing": _safe_metadata_list(properties_missing),
        "safe_summary": _safe_summary(safe_summary),
    }


def validate_real_chatresponder_shadow_call_observation_v1(observation: dict) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(observation, Mapping):
        return {"valid": False, "errors": ["observation must be a mapping"], "warnings": []}
    if observation.get("observation_type") != OBSERVATION_TYPE_V1:
        errors.append("wrong observation_type")
    if observation.get("observation_mode") != OBSERVATION_MODE_V1:
        errors.append("observation_mode must be real_chatresponder_shadow_call")
    for key in ("user_facing_runtime_change", "model_calls", "advisor_calls", "web_search", "write_paths", "weslr_state_created", "raw_prompt_stored", "raw_response_stored", "raw_response_retained"):
        if observation.get(key) is not False:
            errors.append(f"{key} must be false")
    if observation.get("property_label") not in ALLOWED_PROPERTY_LABELS_V1:
        errors.append(f"invalid property_label: {observation.get('property_label')}")
    if observation.get("family") not in ALLOWED_FAMILIES_FOR_VALIDATION_V1:
        errors.append(f"invalid family: {observation.get('family')}")
    for label in observation.get("reason_labels", []) or []:
        if label not in ALLOWED_BLOCKER_REASON_LABELS_V1:
            errors.append(f"invalid reason label: {label}")
    if observation.get("blocked_by_boundary") is True and not observation.get("reason_labels"):
        errors.append("blocked_by_boundary=true requires reason_labels")
    if observation.get("call_attempted") is True and observation.get("preflight_allowed") is not True:
        errors.append("call_attempted=true requires preflight_allowed=true")
    if observation.get("chatresponder_called") is True and observation.get("preflight_allowed") is not True:
        errors.append("chatresponder_called=true requires preflight_allowed=true")
    if observation.get("chatresponder_called") is True:
        for key in ("user_facing_runtime_change", "model_calls", "advisor_calls", "web_search", "write_paths", "weslr_state_created", "raw_prompt_stored", "raw_response_stored", "raw_response_retained"):
            if observation.get(key) is not False:
                errors.append(f"chatresponder_called with forbidden side effect: {key}")
    if observation.get("preflight_allowed") is True and observation.get("call_attempted") is not True:
        warnings.append("preflight_allowed=true but call_attempted=false")
    if observation.get("call_attempted") is True and observation.get("chatresponder_called") is not True:
        warnings.append("call_attempted=true but chatresponder_called=false")
    if observation.get("chatresponder_called") is True and observation.get("property_label") == "not_observed":
        warnings.append("chatresponder_called=true with property_label=not_observed")
    if not str(observation.get("safe_summary") or "").strip():
        warnings.append("safe_summary missing")
    if observation.get("family") == "live_slice_behavior_existing_plan_helper_only" and observation.get("preflight_allowed") is True:
        warnings.append("live_slice_behavior requires feature flag isolation in future caller")
    errors.extend(_forbidden_key_errors(observation))
    errors.extend(_forbidden_claim_errors(observation))
    return {"valid": not errors, "errors": errors, "warnings": _unique(warnings)}


def normalize_real_chatresponder_shadow_call_metadata_v1(
    raw_metadata: dict,
    *,
    prompt_id: str,
    family: str,
) -> dict[str, Any]:
    metadata = to_real_chatresponder_shadow_call_json_safe_v1(raw_metadata or {})
    if not isinstance(metadata, Mapping) or _has_unsafe_content(metadata):
        return build_real_chatresponder_shadow_call_observation_v1(
            prompt_id=prompt_id,
            family=family,
            preflight_allowed=True,
            call_attempted=True,
            chatresponder_called=False,
            blocked_by_boundary=True,
            property_label="blocked_by_boundary",
            reason_labels=["unsafe_response_metadata_blocked"],
            safe_summary="Unsafe response metadata blocked without retaining raw content.",
        )
    safe_keys = {"property_label", "properties_observed", "properties_missing", "safe_summary", "chatresponder_called"}
    if any(str(key) not in safe_keys for key in metadata):
        return build_real_chatresponder_shadow_call_observation_v1(
            prompt_id=prompt_id,
            family=family,
            preflight_allowed=True,
            call_attempted=True,
            chatresponder_called=False,
            blocked_by_boundary=True,
            property_label="blocked_by_boundary",
            reason_labels=["unsafe_response_metadata_blocked"],
            safe_summary="Unsupported response metadata keys blocked without retaining raw content.",
        )
    property_label = str(metadata.get("property_label") or "needs_review")
    if property_label not in ALLOWED_PROPERTY_LABELS_V1:
        property_label = "needs_review"
    chatresponder_called = bool(metadata.get("chatresponder_called", True))
    return build_real_chatresponder_shadow_call_observation_v1(
        prompt_id=prompt_id,
        family=family,
        preflight_allowed=True,
        call_attempted=True,
        chatresponder_called=chatresponder_called,
        blocked_by_boundary=False,
        property_label=property_label,
        properties_observed=_safe_metadata_list(metadata.get("properties_observed")),
        properties_missing=_safe_metadata_list(metadata.get("properties_missing")),
        reason_labels=[],
        safe_summary=_safe_summary(metadata.get("safe_summary", "Safe injected callable metadata normalized.")),
    )


def _observation_from_preflight(preflight: Mapping[str, Any]) -> dict[str, Any]:
    return build_real_chatresponder_shadow_call_observation_v1(
        prompt_id=str(preflight.get("prompt_id") or ""),
        family=str(preflight.get("family") or ""),
        preflight_allowed=False,
        call_attempted=False,
        chatresponder_called=False,
        blocked_by_boundary=True,
        property_label="blocked_by_boundary",
        reason_labels=list(preflight.get("reason_labels") or ["preflight_blocked"]),
        safe_summary="Prompt blocked before injected real shadow-call wrapper.",
    )


def evaluate_prompt_with_real_chatresponder_shadow_call_v1(
    prompt_item: dict,
    *,
    shadow_callable: Callable[[dict], dict] | None = None,
    config: dict | None = None,
    blocker_contract: dict | None = None,
) -> dict[str, Any]:
    cfg = build_real_chatresponder_shadow_call_config_v1() if config is None else to_real_chatresponder_shadow_call_json_safe_v1(config)
    # Step C: routing validator prediction — FIRST gate before any callable construction
    rv_preflight = routing_validator_preflight_v1(prompt_item, config=cfg)
    if not rv_preflight.get("preflight_allowed"):
        return build_real_chatresponder_shadow_call_observation_v1(
            prompt_id=rv_preflight["prompt_id"],
            family=rv_preflight["family"],
            preflight_allowed=False,
            call_attempted=False,
            chatresponder_called=False,
            blocked_by_boundary=True,
            property_label="blocked_by_boundary",
            reason_labels=list(rv_preflight.get("reason_labels") or ["routing_validator_preflight_blocked"]),
            safe_summary="Routing validator blocked before callable construction: " + ", ".join(list(rv_preflight.get("reason_labels") or ["routing_validator_preflight_blocked"])[:4]),
        )
    # Step E-G: existing family/blocker/contract preflight
    preflight = preflight_for_real_chatresponder_shadow_call_v1(prompt_item, config=cfg, blocker_contract=blocker_contract)
    if not preflight.get("preflight_allowed"):
        return _observation_from_preflight(preflight)
    if cfg.get("real_call_authorized") is not True:
        return build_real_chatresponder_shadow_call_observation_v1(
            prompt_id=preflight["prompt_id"], family=preflight["family"], preflight_allowed=True,
            call_attempted=False, chatresponder_called=False, blocked_by_boundary=False,
            property_label="not_observed", reason_labels=["real_call_not_authorized"],
            safe_summary="Real shadow call not authorized; injected callable not called.",
        )
    if cfg.get("allow_injected_callable") is not True:
        return build_real_chatresponder_shadow_call_observation_v1(
            prompt_id=preflight["prompt_id"], family=preflight["family"], preflight_allowed=True,
            call_attempted=False, chatresponder_called=False, blocked_by_boundary=False,
            property_label="not_observed", reason_labels=["real_call_not_authorized"],
            safe_summary="Injected callable not allowed by config.",
        )
    if shadow_callable is None:
        return build_real_chatresponder_shadow_call_observation_v1(
            prompt_id=preflight["prompt_id"], family=preflight["family"], preflight_allowed=True,
            call_attempted=False, chatresponder_called=False, blocked_by_boundary=False,
            property_label="not_observed", reason_labels=["no_shadow_callable_supplied"],
            safe_summary="No injected shadow callable supplied.",
        )
    try:
        raw_metadata = shadow_callable({
            "prompt_id": preflight["prompt_id"],
            "family": preflight["family"],
            "observation_mode": OBSERVATION_MODE_V1,
            "raw_prompt_available": False,
            "metadata_only": True,
        })
    except Exception:
        return build_real_chatresponder_shadow_call_observation_v1(
            prompt_id=preflight["prompt_id"], family=preflight["family"], preflight_allowed=True,
            call_attempted=True, chatresponder_called=False, blocked_by_boundary=True,
            property_label="blocked_by_boundary", reason_labels=["unsafe_response_metadata_blocked"],
            safe_summary="Injected callable failed; unsafe real shadow-call path blocked without raw content.",
        )
    observation = normalize_real_chatresponder_shadow_call_metadata_v1(raw_metadata, prompt_id=preflight["prompt_id"], family=preflight["family"])
    validation = validate_real_chatresponder_shadow_call_observation_v1(observation)
    if not validation.get("valid"):
        return build_real_chatresponder_shadow_call_observation_v1(
            prompt_id=preflight["prompt_id"], family=preflight["family"], preflight_allowed=True,
            call_attempted=True, chatresponder_called=False, blocked_by_boundary=True,
            property_label="blocked_by_boundary", reason_labels=["unsafe_response_metadata_blocked"],
            safe_summary="Injected callable metadata failed validation and was blocked.",
        )
    return observation


def _derive_family_results(observations: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    results: dict[str, dict[str, int]] = {}
    for observation in observations:
        family = str(observation.get("family") or "unknown")
        label = str(observation.get("property_label") or "needs_review")
        results.setdefault(family, {})[label] = results.setdefault(family, {}).get(label, 0) + 1
    return {family: dict(sorted(counts.items())) for family, counts in sorted(results.items())}


def _derive_readiness_label(observations: list[dict[str, Any]], validation: Mapping[str, Any] | None = None) -> str:
    if validation and validation.get("valid") is False:
        return "unsafe_or_inconsistent"
    if not observations:
        return "needs_more_observation"
    if any(obs.get("blocked_by_boundary") is True for obs in observations):
        return "needs_more_observation"
    if any(obs.get("property_label") in {"fail_property", "needs_review", "not_observed"} for obs in observations):
        return "needs_more_observation"
    return "bounded_task_readiness"


def evaluate_prompt_set_with_real_chatresponder_shadow_call_v1(
    prompt_set: dict | None = None,
    *,
    shadow_callables_by_prompt_id: dict | None = None,
    config: dict | None = None,
    blocker_contracts_by_prompt_id: dict | None = None,
    repo_head: str = "",
    timestamp_local: str = "",
    recommended_next_step: str = "RUN_WESLR_CONTROLLED_REAL_CHATRESPONDER_SHADOW_CALL_REPORT_V1",
) -> dict[str, Any]:
    prompt_set_obj = build_default_controlled_behavior_prompt_set_v1() if prompt_set is None else to_real_chatresponder_shadow_call_json_safe_v1(prompt_set)
    cfg = build_real_chatresponder_shadow_call_config_v1() if config is None else to_real_chatresponder_shadow_call_json_safe_v1(config)
    prompt_set_validation = validate_controlled_behavior_prompt_set_v1(prompt_set_obj) if isinstance(prompt_set_obj, dict) else {"valid": False, "errors": ["prompt_set must be mapping"], "warnings": []}
    config_validation = validate_real_chatresponder_shadow_call_config_v1(cfg)
    prompts = list(prompt_set_obj.get("prompts", [])) if isinstance(prompt_set_obj, Mapping) else []
    callables = dict(shadow_callables_by_prompt_id or {})
    contracts = dict(blocker_contracts_by_prompt_id or {})
    known_prompt_ids = {str(prompt.get("prompt_id") or "") for prompt in prompts if isinstance(prompt, Mapping)}
    selected_prompt_ids = [str(pid) for pid in (cfg.get("selected_prompt_ids") or [])]
    unknown_callable_ids = sorted([pid for pid in callables if pid not in known_prompt_ids])
    observations: list[dict[str, Any]] = []
    for prompt in prompts:
        prompt_id = str(prompt.get("prompt_id") or "") if isinstance(prompt, Mapping) else ""
        callable_for_prompt = callables.get(prompt_id) if prompt_id in selected_prompt_ids else None
        observation = evaluate_prompt_with_real_chatresponder_shadow_call_v1(
            prompt if isinstance(prompt, dict) else {},
            shadow_callable=callable_for_prompt,
            config=cfg,
            blocker_contract=contracts.get(prompt_id),
        )
        observations.append(observation)
    family_results = _derive_family_results(observations)
    result = {
        "shadow_call_result_type": RESULT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "observation_mode": OBSERVATION_MODE_V1,
        "repo_head": str(repo_head),
        "timestamp_local": str(timestamp_local),
        "real_call_authorized": bool(cfg.get("real_call_authorized")),
        "prompt_execution": False,
        "chatresponder_calls": any(obs.get("chatresponder_called") is True for obs in observations),
        "model_calls": False,
        "advisor_calls": False,
        "web_search": False,
        "write_paths": False,
        "weslr_state_created": False,
        "raw_prompt_storage": False,
        "raw_response_storage": False,
        "raw_response_retention": False,
        "raw_private_text_included": False,
        "numeric_scores_used": False,
        "official_claims": False,
        "prompt_count": len(prompts),
        "family_count": len({obs.get("family") for obs in observations}),
        "selected_prompt_count": len(selected_prompt_ids),
        "preflight_allowed_count": sum(1 for obs in observations if obs.get("preflight_allowed") is True),
        "call_attempted_count": sum(1 for obs in observations if obs.get("call_attempted") is True),
        "chatresponder_called_count": sum(1 for obs in observations if obs.get("chatresponder_called") is True),
        "blocked_count": sum(1 for obs in observations if obs.get("blocked_by_boundary") is True),
        "observations": observations,
        "family_results": family_results,
        "readiness_label": "needs_more_observation",
        "unknown_shadow_callable_prompt_ids": unknown_callable_ids,
        "config_validation": {
            "valid": bool(config_validation.get("valid", False)),
            "errors": list(config_validation.get("errors", [])),
            "warnings": list(config_validation.get("warnings", [])),
        },
        "prompt_set_validation": {
            "valid": bool(prompt_set_validation.get("valid", False)),
            "errors": list(prompt_set_validation.get("errors", [])),
            "warnings": list(prompt_set_validation.get("warnings", [])),
        },
        "recommended_next_step": str(recommended_next_step),
        "validation": {
            "valid": bool(prompt_set_validation.get("valid", False)) and bool(config_validation.get("valid", False)),
            "errors": list(prompt_set_validation.get("errors", [])) + list(config_validation.get("errors", [])),
            "warnings": list(prompt_set_validation.get("warnings", [])) + list(config_validation.get("warnings", [])),
        },
    }
    result["validation"] = validate_real_chatresponder_shadow_call_result_v1(result)
    result["readiness_label"] = _derive_readiness_label(observations, result["validation"])
    return result


def validate_real_chatresponder_shadow_call_result_v1(result: dict) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(result, Mapping):
        return {"valid": False, "errors": ["result must be a mapping"], "warnings": []}
    if result.get("shadow_call_result_type") != RESULT_TYPE_V1:
        errors.append("wrong shadow_call_result_type")
    if result.get("observation_mode") != OBSERVATION_MODE_V1:
        errors.append("observation_mode must be real_chatresponder_shadow_call")
    for key in ("model_calls", "advisor_calls", "web_search", "write_paths", "weslr_state_created", "raw_prompt_storage", "raw_response_storage", "raw_response_retention", "raw_private_text_included", "numeric_scores_used", "official_claims"):
        if result.get(key) is not False:
            errors.append(f"{key} must be false")
    if result.get("readiness_label", "needs_more_observation") not in READINESS_LABELS_V1:
        errors.append("invalid readiness_label")
    observations = result.get("observations", [])
    if not isinstance(observations, list):
        errors.append("observations must be a list")
        observations = []
    for index, observation in enumerate(observations):
        obs_validation = validate_real_chatresponder_shadow_call_observation_v1(observation)
        if not obs_validation.get("valid"):
            errors.extend([f"observations[{index}]: {error}" for error in obs_validation.get("errors", [])])
        warnings.extend([f"observations[{index}]: {warning}" for warning in obs_validation.get("warnings", [])])
    unknown_ids = result.get("unknown_shadow_callable_prompt_ids", []) or []
    if unknown_ids:
        errors.append("unknown callable prompt IDs: " + ",".join(str(pid) for pid in unknown_ids))
    config_validation = result.get("config_validation", {}) if isinstance(result.get("config_validation", {}), Mapping) else {}
    if config_validation and config_validation.get("valid") is False:
        errors.extend([f"config_validation: {error}" for error in config_validation.get("errors", [])])
    prompt_set_validation = result.get("prompt_set_validation", {}) if isinstance(result.get("prompt_set_validation", {}), Mapping) else {}
    if prompt_set_validation and prompt_set_validation.get("valid") is False:
        errors.extend([f"prompt_set_validation: {error}" for error in prompt_set_validation.get("errors", [])])
    errors.extend(_forbidden_key_errors(result))
    errors.extend(_forbidden_claim_errors(result))
    if not str(result.get("repo_head") or "").strip() or len(str(result.get("repo_head") or "")) < 7:
        warnings.append("repo_head missing/short")
    if result.get("real_call_authorized") is False and int(result.get("call_attempted_count") or 0) == 0:
        warnings.append("real_call_authorized=false and no call attempts")
    if observations and all(obs.get("blocked_by_boundary") is True or obs.get("property_label") == "not_observed" for obs in observations):
        warnings.append("all observations blocked or not_observed")
    if int(result.get("chatresponder_called_count") or 0) == 0:
        warnings.append("no injected callable used")
    for obs in observations:
        if obs.get("family") == "live_slice_behavior_existing_plan_helper_only" and obs.get("preflight_allowed") is True:
            warnings.append("live slice selected without feature flag isolation metadata")
            break
    return {"valid": not errors, "errors": errors, "warnings": _unique(warnings)}


def summarize_real_chatresponder_shadow_call_result_v1(result: dict) -> dict[str, Any]:
    validation = result.get("validation", {}) if isinstance(result, Mapping) else {}
    return {
        "shadow_call_result_type": result.get("shadow_call_result_type") if isinstance(result, Mapping) else None,
        "observation_mode": result.get("observation_mode") if isinstance(result, Mapping) else None,
        "real_call_authorized": bool(result.get("real_call_authorized")) if isinstance(result, Mapping) else False,
        "prompt_count": int(result.get("prompt_count") or 0) if isinstance(result, Mapping) else 0,
        "family_count": int(result.get("family_count") or 0) if isinstance(result, Mapping) else 0,
        "selected_prompt_count": int(result.get("selected_prompt_count") or 0) if isinstance(result, Mapping) else 0,
        "preflight_allowed_count": int(result.get("preflight_allowed_count") or 0) if isinstance(result, Mapping) else 0,
        "call_attempted_count": int(result.get("call_attempted_count") or 0) if isinstance(result, Mapping) else 0,
        "chatresponder_called_count": int(result.get("chatresponder_called_count") or 0) if isinstance(result, Mapping) else 0,
        "blocked_count": int(result.get("blocked_count") or 0) if isinstance(result, Mapping) else 0,
        "readiness_label": result.get("readiness_label") if isinstance(result, Mapping) else "needs_more_observation",
        "family_results": result.get("family_results", {}) if isinstance(result, Mapping) else {},
        "validation_valid": bool(validation.get("valid", False)),
        "errors_count": len(validation.get("errors", [])) if isinstance(validation, Mapping) else 0,
        "warnings_count": len(validation.get("warnings", [])) if isinstance(validation, Mapping) else 0,
        "prompt_execution": bool(result.get("prompt_execution")) if isinstance(result, Mapping) else False,
        "chatresponder_calls": bool(result.get("chatresponder_calls")) if isinstance(result, Mapping) else False,
        "model_calls": bool(result.get("model_calls")) if isinstance(result, Mapping) else False,
        "advisor_calls": bool(result.get("advisor_calls")) if isinstance(result, Mapping) else False,
        "web_search": bool(result.get("web_search")) if isinstance(result, Mapping) else False,
        "write_paths": bool(result.get("write_paths")) if isinstance(result, Mapping) else False,
        "weslr_state_created": bool(result.get("weslr_state_created")) if isinstance(result, Mapping) else False,
        "raw_prompt_storage": bool(result.get("raw_prompt_storage")) if isinstance(result, Mapping) else False,
        "raw_response_storage": bool(result.get("raw_response_storage")) if isinstance(result, Mapping) else False,
        "raw_response_retention": bool(result.get("raw_response_retention")) if isinstance(result, Mapping) else False,
        "raw_private_text_included": bool(result.get("raw_private_text_included")) if isinstance(result, Mapping) else False,
        "numeric_scores_used": bool(result.get("numeric_scores_used")) if isinstance(result, Mapping) else False,
        "official_claims": bool(result.get("official_claims")) if isinstance(result, Mapping) else False,
        "recommended_next_step": result.get("recommended_next_step") if isinstance(result, Mapping) else "RUN_WESLR_CONTROLLED_REAL_CHATRESPONDER_SHADOW_CALL_REPORT_V1",
    }


def render_real_chatresponder_shadow_call_markdown_v1(result: dict) -> str:
    summary = summarize_real_chatresponder_shadow_call_result_v1(result)
    family_results = summary.get("family_results") or {}
    family_lines = []
    for family, labels in sorted(family_results.items()):
        parts = ", ".join(f"{label}={count}" for label, count in sorted(labels.items()))
        family_lines.append(f"- `{family}`: {parts or 'none'}")
    family_text = "\n".join(family_lines) or "- none"
    return "\n".join([
        "# WESLR Controlled Real ChatResponder Shadow Call Result V1",
        "",
        "SECTION 1 — STATUS",
        f"- shadow_call_result_type: `{summary['shadow_call_result_type']}`",
        f"- observation_mode: `{summary['observation_mode']}`",
        f"- real_call_authorized: `{str(summary['real_call_authorized']).lower()}`",
        f"- prompt_count: `{summary['prompt_count']}`",
        f"- family_count: `{summary['family_count']}`",
        "",
        "SECTION 2 — SHADOW CALL BOUNDARIES",
        f"- prompt_execution: `{str(summary['prompt_execution']).lower()}`",
        f"- chatresponder_calls: `{str(summary['chatresponder_calls']).lower()}`",
        f"- model_calls: `{str(summary['model_calls']).lower()}`",
        f"- advisor_calls: `{str(summary['advisor_calls']).lower()}`",
        f"- web_search: `{str(summary['web_search']).lower()}`",
        f"- write_paths: `{str(summary['write_paths']).lower()}`",
        f"- weslr_state_created: `{str(summary['weslr_state_created']).lower()}`",
        "",
        "SECTION 3 — SELECTED PROMPTS / PREFLIGHT SUMMARY",
        f"- selected_prompt_count: `{summary['selected_prompt_count']}`",
        f"- preflight_allowed_count: `{summary['preflight_allowed_count']}`",
        f"- call_attempted_count: `{summary['call_attempted_count']}`",
        f"- chatresponder_called_count: `{summary['chatresponder_called_count']}`",
        f"- blocked_count: `{summary['blocked_count']}`",
        "",
        "SECTION 4 — FAMILY RESULTS",
        family_text,
        "",
        "SECTION 5 — READINESS LABEL",
        f"- readiness_label: `{summary['readiness_label']}`",
        "",
        "SECTION 6 — SAFETY / CLAIM BOUNDARIES",
        f"- raw_prompt_storage: `{str(summary['raw_prompt_storage']).lower()}`",
        f"- raw_response_storage: `{str(summary['raw_response_storage']).lower()}`",
        f"- raw_response_retention: `{str(summary['raw_response_retention']).lower()}`",
        f"- raw_private_text_included: `{str(summary['raw_private_text_included']).lower()}`",
        f"- numeric_scores_used: `{str(summary['numeric_scores_used']).lower()}`",
        f"- official_claims: `{str(summary['official_claims']).lower()}`",
        "- benchmark_or_certification_claims: `false`",
        "- fake_consciousness_claims: `false`",
        "",
        "SECTION 7 — VALIDATION SUMMARY",
        f"- validation_valid: `{str(summary['validation_valid']).lower()}`",
        f"- errors_count: `{summary['errors_count']}`",
        f"- warnings_count: `{summary['warnings_count']}`",
        "",
        "SECTION 8 — RECOMMENDED NEXT STEP",
        f"- `{summary['recommended_next_step']}`",
    ])


# =====================================================================
# Safe Non-Model ChatResponder Test Harness — keyword + preflight helpers
# =====================================================================

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

SAFE_KEYWORDS: list[str] = [
    "lunch",
    "workout",
    "gym",
    "run",
    "exercise",
    "plan",
    "email",
    "wife",
    "partner",
    "code",
    "bug",
]


def _prompt_matches_safe_keyword(
    prompt_text: str,
    keyword: Optional[str] = None,
) -> bool:
    """Check if prompt text matches a safe keyword.

    Args:
        prompt_text: The user-facing message text.
        keyword: Optional specific keyword to check. If omitted, checks
            against the full SAFE_KEYWORDS list.

    Returns:
        True if the prompt contains the expected safe keyword.
    """
    if not prompt_text:
        return False
    text_lower = prompt_text.lower()
    if keyword is not None:
        return keyword.lower() in text_lower
    return any(kw in text_lower for kw in SAFE_KEYWORDS)


@dataclass
class PreflightResult:
    """Result of a preflight safety check."""

    status: str  # "pass", "blocked", "needs_review"
    reason: Optional[str] = None


@dataclass
class ShadowCallResult:
    """Sanitized result of one shadow call.

    Contains no raw prompt text, no raw response text, and no
    conversation transcript.  Only derived metadata and classifications.
    """

    real_call_classification: str
    chatresponder_called_count: int
    properties: dict[str, str]
    blocker_status: dict[str, bool]
    prompt_id: str
    timestamp: str


def build_safe_injected_callable_v1(
    prompt_text: str,
    *,
    prompt_id: str = "unknown",
    mock_active: bool = False,
) -> Callable[[], tuple[str, Optional[dict[str, Any]] | None]]:
    """Build a safe injected callable for ChatResponder testing.

    Preflight guard: if ``mock_active`` is False and the prompt does
    not match a safe keyword, raises RuntimeError immediately.

    Args:
        prompt_text: The message to send to ``respond_chat()``.
        prompt_id: Identifier for the prompt (e.g. ``ordinary_task_behavior_003``).
        mock_active: Whether the ``generate_chat`` mock is installed.

    Returns:
        A zero-argument callable that returns the ``(content, metadata)``
        tuple from ``ChatResponder.respond_chat()``.

    Raises:
        RuntimeError: If the prompt is unsafe and mock is not active.
    """
    if not mock_active and not _prompt_matches_safe_keyword(prompt_text):
        raise RuntimeError(
            f"Prompt '{prompt_id}' does not match any safe keyword. "
            "Mock must be active or prompt must be a safe-keyword prompt."
        )

    def _callable() -> tuple[str, Optional[dict[str, Any]] | None]:
        mod = __import__("weslr.chat_responder", fromlist=["ChatResponder"])
        responder_cls = getattr(mod, "ChatResponder")
        responder = responder_cls()
        return responder.respond_chat(prompt_text)

    return _callable


def run_preflight(
    callable_fn: Optional[Callable[[], tuple[str, Optional[dict[str, Any]] | None]]],
    prompt_text: str,
    *,
    prompt_id: str = "unknown",
    mock_active: bool = False,
) -> PreflightResult:
    """Run preflight checks before executing a shadow call.

    Args:
        callable_fn: The injected callable (unused in current preflight
            logic but reserved for future callable-level checks).
        prompt_text: The prompt text being sent.
        prompt_id: Prompt identifier.
        mock_active: Whether the mock is installed.

    Returns:
        PreflightResult with status ``pass`` or ``blocked``.
    """
    # Without mock, only safe-keyword prompts are allowed
    if not mock_active and not _prompt_matches_safe_keyword(prompt_text):
        return PreflightResult(
            status="blocked",
            reason=f"Prompt '{prompt_id}' not safe and mock not active",
        )

    # With mock active, allow any prompt (mock intercepts model path)
    return PreflightResult(status="pass")


def execute_shadow_call(
    callable_fn: Callable[[], tuple[str, Optional[dict[str, Any]] | None]],
    *,
    prompt_id: str = "unknown",
) -> ShadowCallResult:
    """Execute one controlled shadow call.

    Calls the callable at most once, derives safe metadata in-memory,
    and returns a sanitized ShadowCallResult with no raw text.

    Args:
        callable_fn: Zero-argument callable that runs the ChatResponder.
        prompt_id: Prompt identifier for the result.

    Returns:
        ShadowCallResult containing only derived properties and
        classifications.
    """
    # Call at most once
    response_text, metadata = callable_fn()

    # Derive safe metadata from response (no raw text retained in result)
    properties = _derive_observation_metadata(response_text, metadata)

    return ShadowCallResult(
        real_call_classification="keyword_branch_only",
        chatresponder_called_count=1,
        properties=properties,
        blocker_status={"mock_active": True},
        prompt_id=prompt_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _derive_observation_metadata(
    response_text: str,
    metadata: Optional[dict[str, Any]],
) -> dict[str, str]:
    """Derive safe metadata from response.

    Never stores raw prompt or response text.  Only bounded qualitative
    properties suitable for test assertions.

    Args:
        response_text: The raw response text (examined but not stored).
        metadata: Optional metadata dict from ChatResponder.

    Returns:
        Dictionary of derived qualitative properties.
    """
    properties: dict[str, str] = {
        "bounded": "pass" if len(response_text) < 500 else "review",
        "useful": "pass" if response_text and len(response_text) > 10 else "fail",
        "has_metadata": "yes" if metadata else "no",
    }
    return properties
