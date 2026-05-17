"""Controlled local ChatResponder shadow execution helper layer V1.

This module provides metadata-only wrappers for a future separately approved
controlled ChatResponder shadow execution lane. It deliberately does not import
or instantiate ChatResponder, call models/search/advisors, persist files, write
.weslr state, store raw prompt/response text, or make official claims.
"""

from __future__ import annotations

import copy
import re
from dataclasses import asdict, is_dataclass
from typing import Any, Callable, Mapping

from weslr.chatresponder_shadow_observation_helpers import preflight_chatresponder_shadow_prompt_v1
from weslr.controlled_behavior_prompt_set import (
    build_default_controlled_behavior_prompt_set_v1,
    validate_controlled_behavior_prompt_set_v1,
)
from weslr.controlled_local_runtime_guards import guard_controlled_local_runtime_prompt_item_v1

OBSERVATION_MODE_V1 = "chatresponder_shadow_execution"
CONFIG_TYPE_V1 = "weslr_chatresponder_shadow_execution_config_v1"
BLOCKER_CONTRACT_TYPE_V1 = "weslr_chatresponder_shadow_execution_blocker_contract_v1"
PREFLIGHT_TYPE_V1 = "weslr_chatresponder_shadow_execution_preflight_v1"
OBSERVATION_TYPE_V1 = "weslr_chatresponder_shadow_execution_observation_v1"
RESULT_TYPE_V1 = "weslr_chatresponder_shadow_execution_result_v1"
SCHEMA_VERSION_V1 = "1.0"

ALLOWED_EXECUTION_FAMILIES_V1 = {
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
ALLOWED_FAMILIES_FOR_VALIDATION_V1 = ALLOWED_EXECUTION_FAMILIES_V1 | BLOCKED_REFINEMENT_FAMILIES_V1 | {"live_slice_behavior"}
ALLOWED_PROPERTY_LABELS_V1 = {
    "pass_property",
    "fail_property",
    "needs_review",
    "not_observed",
    "blocked_by_boundary",
}
ALLOWED_BLOCKER_REASON_LABELS_V1 = {
    "preflight_blocked",
    "model_path_blocked",
    "search_path_blocked",
    "advisor_path_blocked",
    "write_path_blocked",
    "weslr_state_blocked",
    "status_path_blocked",
    "currentness_source_blocked",
    "source_registry_write_blocked",
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
    "unsafe_prompt_marker_blocked",
    "unsupported_family_blocked",
    "external_service_blocked",
    "global_feature_flag_mutation_blocked",
    "unsafe_execution_metadata_blocked",
    "no_execution_callable_supplied",
    "execution_not_authorized",
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


def to_chatresponder_shadow_execution_json_safe_v1(obj: Any) -> Any:
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
    return cleaned or "Controlled shadow execution metadata recorded without raw prompt or response text."


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
        if text:
            out.append(text)
    return out[:12]


def _normalize_reason_labels(labels: list[str] | None) -> list[str]:
    return _unique([label for label in (labels or []) if str(label) in ALLOWED_BLOCKER_REASON_LABELS_V1])


def build_chatresponder_shadow_execution_config_v1(
    *,
    execution_authorized: bool = False,
    allow_injected_callable: bool = False,
    allow_feature_flag_isolation: bool = False,
) -> dict[str, Any]:
    return {
        "config_type": CONFIG_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "observation_mode": OBSERVATION_MODE_V1,
        "execution_authorized": bool(execution_authorized),
        "allow_injected_callable": bool(allow_injected_callable),
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
        "numeric_scoring_allowed": False,
        "official_claims_allowed": False,
        "default_enablement_allowed": False,
        "branch_expansion_allowed": False,
    }


def build_chatresponder_shadow_execution_blocker_contract_v1(
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
        "global_feature_flag_mutation_blocked": True,
        "safe_summary": _safe_summary(safe_summary),
    }


def preflight_for_chatresponder_shadow_execution_v1(
    prompt_item: dict,
    *,
    config: dict | None = None,
) -> dict[str, Any]:
    cfg = build_chatresponder_shadow_execution_config_v1() if config is None else to_chatresponder_shadow_execution_json_safe_v1(config)
    item = to_chatresponder_shadow_execution_json_safe_v1(prompt_item or {})
    base = preflight_chatresponder_shadow_prompt_v1(item, config={
        "default_enablement_allowed": bool(cfg.get("default_enablement_allowed", False)),
        "branch_expansion_allowed": bool(cfg.get("branch_expansion_allowed", False)),
    })
    guard = guard_controlled_local_runtime_prompt_item_v1(item if isinstance(item, dict) else {})
    family = str(base.get("family") or (item.get("family") if isinstance(item, Mapping) else ""))
    reason_labels: list[str] = []
    reason_labels.extend(base.get("reason_labels", []) or [])
    reason_labels.extend(guard.get("reason_labels", []) or [])
    if family not in ALLOWED_EXECUTION_FAMILIES_V1:
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
    if any(cfg.get(k) is True for k in (
        "model_calls_allowed", "advisor_calls_allowed", "web_search_allowed", "write_paths_allowed",
        "weslr_state_allowed", "raw_prompt_storage_allowed", "raw_response_storage_allowed",
        "default_enablement_allowed", "branch_expansion_allowed",
    )):
        reason_labels.append("unsafe_execution_metadata_blocked")
    if _has_unsafe_content(item):
        reason_labels.append("unsafe_prompt_marker_blocked")
    reason_labels = _normalize_reason_labels(reason_labels)
    allowed = bool(base.get("preflight_allowed")) and family in ALLOWED_EXECUTION_FAMILIES_V1 and not reason_labels
    return {
        "preflight_type": PREFLIGHT_TYPE_V1,
        "prompt_id": str(base.get("prompt_id") or ""),
        "family": family,
        "observation_mode": OBSERVATION_MODE_V1,
        "preflight_allowed": allowed,
        "blocked_by_boundary": not allowed,
        "reason_labels": [] if allowed else (reason_labels or ["preflight_blocked"]),
        "safe_summary": _safe_summary("Prompt eligible for controlled shadow execution." if allowed else "Prompt blocked before controlled shadow execution."),
        "side_effects": _empty_side_effects(),
    }


def build_chatresponder_shadow_execution_observation_v1(
    *,
    prompt_id: str,
    family: str,
    preflight_allowed: bool = False,
    execution_attempted: bool = False,
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
        "execution_attempted": bool(execution_attempted),
        "chatresponder_called": bool(chatresponder_called),
        "user_facing_runtime_change": False,
        "model_calls": False,
        "advisor_calls": False,
        "web_search": False,
        "write_paths": False,
        "weslr_state_created": False,
        "raw_prompt_stored": False,
        "raw_response_stored": False,
        "blocked_by_boundary": bool(blocked_by_boundary),
        "reason_labels": _normalize_reason_labels(reason_labels),
        "property_label": str(property_label),
        "properties_observed": _safe_metadata_list(properties_observed),
        "properties_missing": _safe_metadata_list(properties_missing),
        "safe_summary": _safe_summary(safe_summary),
    }


def validate_chatresponder_shadow_execution_observation_v1(observation: dict) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(observation, Mapping):
        return {"valid": False, "errors": ["observation must be a mapping"], "warnings": []}
    if observation.get("observation_type") != OBSERVATION_TYPE_V1:
        errors.append("wrong observation_type")
    if observation.get("observation_mode") != OBSERVATION_MODE_V1:
        errors.append("observation_mode must be chatresponder_shadow_execution")
    for key in ("user_facing_runtime_change", "model_calls", "advisor_calls", "web_search", "write_paths", "weslr_state_created", "raw_prompt_stored", "raw_response_stored"):
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
    if observation.get("execution_attempted") is True and observation.get("preflight_allowed") is not True:
        errors.append("execution_attempted=true requires preflight_allowed=true")
    if observation.get("chatresponder_called") is True and observation.get("preflight_allowed") is not True:
        errors.append("chatresponder_called=true requires preflight_allowed=true")
    if observation.get("chatresponder_called") is True:
        for key in ("user_facing_runtime_change", "model_calls", "advisor_calls", "web_search", "write_paths", "weslr_state_created", "raw_prompt_stored", "raw_response_stored"):
            if observation.get(key) is not False:
                errors.append(f"chatresponder_called with forbidden side effect: {key}")
    if observation.get("preflight_allowed") is True and observation.get("execution_attempted") is not True:
        warnings.append("preflight_allowed=true but execution_attempted=false")
    if observation.get("execution_attempted") is True and observation.get("chatresponder_called") is not True:
        warnings.append("execution_attempted=true but chatresponder_called=false")
    if observation.get("chatresponder_called") is True and observation.get("property_label") == "not_observed":
        warnings.append("chatresponder_called=true with property_label=not_observed")
    if not str(observation.get("safe_summary") or "").strip():
        warnings.append("safe_summary missing")
    if observation.get("family") == "live_slice_behavior_existing_plan_helper_only" and observation.get("preflight_allowed") is True:
        warnings.append("live_slice_behavior requires feature flag isolation in future caller")
    errors.extend(_forbidden_key_errors(observation))
    errors.extend(_forbidden_claim_errors(observation))
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def normalize_chatresponder_shadow_execution_metadata_v1(
    raw_metadata: dict,
    *,
    prompt_id: str,
    family: str,
) -> dict[str, Any]:
    metadata = to_chatresponder_shadow_execution_json_safe_v1(raw_metadata or {})
    if not isinstance(metadata, Mapping) or _has_unsafe_content(metadata):
        return build_chatresponder_shadow_execution_observation_v1(
            prompt_id=prompt_id,
            family=family,
            preflight_allowed=True,
            execution_attempted=True,
            chatresponder_called=False,
            blocked_by_boundary=True,
            property_label="blocked_by_boundary",
            reason_labels=["unsafe_execution_metadata_blocked"],
            safe_summary="Unsafe execution metadata blocked without retaining raw content.",
        )
    property_label = str(metadata.get("property_label") or "needs_review")
    if property_label not in ALLOWED_PROPERTY_LABELS_V1:
        property_label = "needs_review"
    chatresponder_called = bool(metadata.get("chatresponder_called", True))
    return build_chatresponder_shadow_execution_observation_v1(
        prompt_id=prompt_id,
        family=family,
        preflight_allowed=True,
        execution_attempted=True,
        chatresponder_called=chatresponder_called,
        blocked_by_boundary=False,
        property_label=property_label,
        properties_observed=_safe_metadata_list(metadata.get("properties_observed")),
        properties_missing=_safe_metadata_list(metadata.get("properties_missing")),
        reason_labels=[],
        safe_summary=_safe_summary(metadata.get("safe_summary", "Safe injected callable metadata normalized.")),
    )


def _observation_from_preflight(preflight: Mapping[str, Any]) -> dict[str, Any]:
    return build_chatresponder_shadow_execution_observation_v1(
        prompt_id=str(preflight.get("prompt_id") or ""),
        family=str(preflight.get("family") or ""),
        preflight_allowed=False,
        execution_attempted=False,
        chatresponder_called=False,
        blocked_by_boundary=True,
        property_label="blocked_by_boundary",
        reason_labels=list(preflight.get("reason_labels") or ["preflight_blocked"]),
        safe_summary="Prompt blocked before injected callable execution.",
    )


def evaluate_prompt_with_chatresponder_shadow_execution_v1(
    prompt_item: dict,
    *,
    execution_callable: Callable[[dict], dict] | None = None,
    config: dict | None = None,
) -> dict[str, Any]:
    cfg = build_chatresponder_shadow_execution_config_v1() if config is None else to_chatresponder_shadow_execution_json_safe_v1(config)
    preflight = preflight_for_chatresponder_shadow_execution_v1(prompt_item, config=cfg)
    if not preflight.get("preflight_allowed"):
        return _observation_from_preflight(preflight)
    if cfg.get("execution_authorized") is not True:
        return build_chatresponder_shadow_execution_observation_v1(
            prompt_id=preflight["prompt_id"], family=preflight["family"], preflight_allowed=True,
            execution_attempted=False, chatresponder_called=False, blocked_by_boundary=False,
            property_label="not_observed", reason_labels=["execution_not_authorized"],
            safe_summary="Execution not authorized; injected callable not called.",
        )
    if cfg.get("allow_injected_callable") is not True:
        return build_chatresponder_shadow_execution_observation_v1(
            prompt_id=preflight["prompt_id"], family=preflight["family"], preflight_allowed=True,
            execution_attempted=False, chatresponder_called=False, blocked_by_boundary=False,
            property_label="not_observed", reason_labels=["execution_not_authorized"],
            safe_summary="Injected callable not allowed by config.",
        )
    if execution_callable is None:
        return build_chatresponder_shadow_execution_observation_v1(
            prompt_id=preflight["prompt_id"], family=preflight["family"], preflight_allowed=True,
            execution_attempted=False, chatresponder_called=False, blocked_by_boundary=False,
            property_label="not_observed", reason_labels=["no_execution_callable_supplied"],
            safe_summary="No injected callable supplied.",
        )
    try:
        raw_metadata = execution_callable({
            "prompt_id": preflight["prompt_id"],
            "family": preflight["family"],
            "observation_mode": OBSERVATION_MODE_V1,
            "raw_prompt_available": False,
        })
    except Exception:
        return build_chatresponder_shadow_execution_observation_v1(
            prompt_id=preflight["prompt_id"], family=preflight["family"], preflight_allowed=True,
            execution_attempted=True, chatresponder_called=False, blocked_by_boundary=True,
            property_label="blocked_by_boundary", reason_labels=["unsafe_execution_metadata_blocked"],
            safe_summary="Injected callable failed; unsafe execution path blocked without raw content.",
        )
    observation = normalize_chatresponder_shadow_execution_metadata_v1(raw_metadata, prompt_id=preflight["prompt_id"], family=preflight["family"])
    validation = validate_chatresponder_shadow_execution_observation_v1(observation)
    if not validation.get("valid"):
        return build_chatresponder_shadow_execution_observation_v1(
            prompt_id=preflight["prompt_id"], family=preflight["family"], preflight_allowed=True,
            execution_attempted=True, chatresponder_called=False, blocked_by_boundary=True,
            property_label="blocked_by_boundary", reason_labels=["unsafe_execution_metadata_blocked"],
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


def evaluate_prompt_set_with_chatresponder_shadow_execution_v1(
    prompt_set: dict | None = None,
    *,
    execution_callables_by_prompt_id: dict | None = None,
    config: dict | None = None,
    repo_head: str = "",
    timestamp_local: str = "",
    recommended_next_step: str = "RUN_WESLR_CONTROLLED_LOCAL_CHATRESPONDER_SHADOW_EXECUTION_REPORT_V1",
) -> dict[str, Any]:
    prompt_set_obj = build_default_controlled_behavior_prompt_set_v1() if prompt_set is None else to_chatresponder_shadow_execution_json_safe_v1(prompt_set)
    cfg = build_chatresponder_shadow_execution_config_v1() if config is None else to_chatresponder_shadow_execution_json_safe_v1(config)
    validation = validate_controlled_behavior_prompt_set_v1(prompt_set_obj) if isinstance(prompt_set_obj, dict) else {"valid": False, "errors": ["prompt_set must be mapping"], "warnings": []}
    prompts = list(prompt_set_obj.get("prompts", [])) if isinstance(prompt_set_obj, Mapping) else []
    callables = dict(execution_callables_by_prompt_id or {})
    known_prompt_ids = {str(prompt.get("prompt_id") or "") for prompt in prompts if isinstance(prompt, Mapping)}
    unknown_callable_ids = sorted([pid for pid in callables if pid not in known_prompt_ids])
    observations: list[dict[str, Any]] = []
    for prompt in prompts:
        prompt_id = str(prompt.get("prompt_id") or "") if isinstance(prompt, Mapping) else ""
        observation = evaluate_prompt_with_chatresponder_shadow_execution_v1(
            prompt if isinstance(prompt, dict) else {},
            execution_callable=callables.get(prompt_id),
            config=cfg,
        )
        observations.append(observation)
    family_results = _derive_family_results(observations)
    result = {
        "execution_result_type": RESULT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "observation_mode": OBSERVATION_MODE_V1,
        "repo_head": str(repo_head),
        "timestamp_local": str(timestamp_local),
        "execution_authorized": bool(cfg.get("execution_authorized")),
        "prompt_execution": False,
        "chatresponder_calls": any(obs.get("chatresponder_called") is True for obs in observations),
        "model_calls": False,
        "advisor_calls": False,
        "web_search": False,
        "write_paths": False,
        "weslr_state_created": False,
        "raw_prompt_storage": False,
        "raw_response_storage": False,
        "raw_private_text_included": False,
        "numeric_scores_used": False,
        "official_claims": False,
        "prompt_count": len(prompts),
        "family_count": len({obs.get("family") for obs in observations}),
        "preflight_allowed_count": sum(1 for obs in observations if obs.get("preflight_allowed") is True),
        "execution_attempted_count": sum(1 for obs in observations if obs.get("execution_attempted") is True),
        "chatresponder_called_count": sum(1 for obs in observations if obs.get("chatresponder_called") is True),
        "blocked_count": sum(1 for obs in observations if obs.get("blocked_by_boundary") is True),
        "observations": observations,
        "family_results": family_results,
        "readiness_label": "needs_more_observation",
        "unknown_execution_callable_prompt_ids": unknown_callable_ids,
        "recommended_next_step": str(recommended_next_step),
        "validation": {
            "valid": bool(validation.get("valid", False)),
            "errors": list(validation.get("errors", [])),
            "warnings": list(validation.get("warnings", [])),
        },
    }
    result["validation"] = validate_chatresponder_shadow_execution_result_v1(result)
    result["readiness_label"] = _derive_readiness_label(observations, result["validation"])
    return result


def validate_chatresponder_shadow_execution_result_v1(result: dict) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(result, Mapping):
        return {"valid": False, "errors": ["result must be a mapping"], "warnings": []}
    if result.get("execution_result_type") != RESULT_TYPE_V1:
        errors.append("wrong execution_result_type")
    if result.get("observation_mode") != OBSERVATION_MODE_V1:
        errors.append("observation_mode must be chatresponder_shadow_execution")
    for key in ("model_calls", "advisor_calls", "web_search", "write_paths", "weslr_state_created", "raw_prompt_storage", "raw_response_storage", "raw_private_text_included", "numeric_scores_used", "official_claims"):
        if result.get(key) is not False:
            errors.append(f"{key} must be false")
    if result.get("readiness_label", "needs_more_observation") not in READINESS_LABELS_V1:
        errors.append("invalid readiness_label")
    observations = result.get("observations", [])
    if not isinstance(observations, list):
        errors.append("observations must be a list")
        observations = []
    for index, observation in enumerate(observations):
        obs_validation = validate_chatresponder_shadow_execution_observation_v1(observation)
        if not obs_validation.get("valid"):
            errors.extend([f"observations[{index}]: {error}" for error in obs_validation.get("errors", [])])
        warnings.extend([f"observations[{index}]: {warning}" for warning in obs_validation.get("warnings", [])])
    unknown_ids = result.get("unknown_execution_callable_prompt_ids", []) or []
    if unknown_ids:
        errors.append("unknown execution callable prompt IDs: " + ",".join(str(pid) for pid in unknown_ids))
    errors.extend(_forbidden_key_errors(result))
    errors.extend(_forbidden_claim_errors(result))
    if not str(result.get("repo_head") or "").strip() or len(str(result.get("repo_head") or "")) < 7:
        warnings.append("repo_head missing/short")
    if result.get("execution_authorized") is False and int(result.get("execution_attempted_count") or 0) == 0:
        warnings.append("execution_authorized=false and no execution attempts")
    if observations and all(obs.get("blocked_by_boundary") is True or obs.get("property_label") == "not_observed" for obs in observations):
        warnings.append("all observations blocked or not_observed")
    if int(result.get("chatresponder_called_count") or 0) == 0:
        warnings.append("no injected callable used")
    for obs in observations:
        if obs.get("family") == "live_slice_behavior_existing_plan_helper_only" and obs.get("preflight_allowed") is True:
            warnings.append("live slice allowed without feature flag isolation metadata")
            break
    return {"valid": not errors, "errors": errors, "warnings": _unique(warnings)}


def summarize_chatresponder_shadow_execution_result_v1(result: dict) -> dict[str, Any]:
    validation = result.get("validation", {}) if isinstance(result, Mapping) else {}
    return {
        "execution_result_type": result.get("execution_result_type") if isinstance(result, Mapping) else None,
        "observation_mode": result.get("observation_mode") if isinstance(result, Mapping) else None,
        "execution_authorized": bool(result.get("execution_authorized")) if isinstance(result, Mapping) else False,
        "prompt_count": int(result.get("prompt_count") or 0) if isinstance(result, Mapping) else 0,
        "family_count": int(result.get("family_count") or 0) if isinstance(result, Mapping) else 0,
        "preflight_allowed_count": int(result.get("preflight_allowed_count") or 0) if isinstance(result, Mapping) else 0,
        "execution_attempted_count": int(result.get("execution_attempted_count") or 0) if isinstance(result, Mapping) else 0,
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
        "raw_private_text_included": bool(result.get("raw_private_text_included")) if isinstance(result, Mapping) else False,
        "numeric_scores_used": bool(result.get("numeric_scores_used")) if isinstance(result, Mapping) else False,
        "official_claims": bool(result.get("official_claims")) if isinstance(result, Mapping) else False,
        "recommended_next_step": result.get("recommended_next_step") if isinstance(result, Mapping) else "RUN_WESLR_CONTROLLED_LOCAL_CHATRESPONDER_SHADOW_EXECUTION_REPORT_V1",
    }


def render_chatresponder_shadow_execution_markdown_v1(result: dict) -> str:
    summary = summarize_chatresponder_shadow_execution_result_v1(result)
    family_results = summary.get("family_results") or {}
    family_lines = []
    for family, labels in sorted(family_results.items()):
        parts = ", ".join(f"{label}={count}" for label, count in sorted(labels.items()))
        family_lines.append(f"- `{family}`: {parts or 'none'}")
    family_text = "\n".join(family_lines) or "- none"
    return "\n".join([
        "# WESLR Controlled Local ChatResponder Shadow Execution Result V1",
        "",
        "SECTION 1 — STATUS",
        f"- execution_result_type: `{summary['execution_result_type']}`",
        f"- observation_mode: `{summary['observation_mode']}`",
        f"- execution_authorized: `{str(summary['execution_authorized']).lower()}`",
        f"- prompt_count: `{summary['prompt_count']}`",
        f"- family_count: `{summary['family_count']}`",
        "",
        "SECTION 2 — EXECUTION BOUNDARIES",
        f"- prompt_execution: `{str(summary['prompt_execution']).lower()}`",
        f"- chatresponder_calls: `{str(summary['chatresponder_calls']).lower()}`",
        f"- model_calls: `{str(summary['model_calls']).lower()}`",
        f"- advisor_calls: `{str(summary['advisor_calls']).lower()}`",
        f"- web_search: `{str(summary['web_search']).lower()}`",
        f"- write_paths: `{str(summary['write_paths']).lower()}`",
        f"- weslr_state_created: `{str(summary['weslr_state_created']).lower()}`",
        "",
        "SECTION 3 — PREFLIGHT / BLOCK SUMMARY",
        f"- preflight_allowed_count: `{summary['preflight_allowed_count']}`",
        f"- execution_attempted_count: `{summary['execution_attempted_count']}`",
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
        f"- raw_private_text_included: `{str(summary['raw_private_text_included']).lower()}`",
        f"- numeric_scores_used: `{str(summary['numeric_scores_used']).lower()}`",
        f"- official_claims: `{str(summary['official_claims']).lower()}`",
        "- benchmark_or_certification_claims: `false`",
        "",
        "SECTION 7 — VALIDATION SUMMARY",
        f"- validation_valid: `{str(summary['validation_valid']).lower()}`",
        f"- errors_count: `{summary['errors_count']}`",
        f"- warnings_count: `{summary['warnings_count']}`",
        "",
        "SECTION 8 — RECOMMENDED NEXT STEP",
        f"- `{summary['recommended_next_step']}`",
    ])
