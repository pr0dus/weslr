"""ChatResponder shadow observation helper layer V1.

This module prepares metadata-only shadow observation records for a future
controlled local ChatResponder lane. It deliberately does not import or call
ChatResponder, execute prompts, call models/search/advisors, persist files, or
write WESLR runtime state.
"""

from __future__ import annotations

import copy
import re
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

from weslr.controlled_behavior_prompt_set import (
    build_default_controlled_behavior_prompt_set_v1,
    validate_controlled_behavior_prompt_item_v1,
    validate_controlled_behavior_prompt_set_v1,
)
from weslr.controlled_local_runtime_guards import guard_controlled_local_runtime_prompt_item_v1

OBSERVATION_MODE_V1 = "chatresponder_shadow"
HELPER_TYPE_V1 = "weslr_chatresponder_shadow_observation_helpers_v1"
CONFIG_TYPE_V1 = "weslr_chatresponder_shadow_config_v1"
PREFLIGHT_TYPE_V1 = "weslr_chatresponder_shadow_preflight_v1"
OBSERVATION_TYPE_V1 = "weslr_chatresponder_shadow_observation_v1"
PROMPT_SET_PREFLIGHT_TYPE_V1 = "weslr_chatresponder_shadow_prompt_set_preflight_v1"
SCHEMA_VERSION_V1 = "1.0"

ALLOWED_SHADOW_FAMILIES_V1 = {
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
}
BLOCKED_PATH_LABELS_V1 = {
    "model_path_blocked",
    "search_path_blocked",
    "advisor_path_blocked",
    "write_path_blocked",
    "weslr_state_blocked",
    "status_path_blocked",
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
    "unsafe_prompt_marker_blocked",
    "unsupported_family_blocked",
}
ALLOWED_PROPERTY_LABELS_V1 = {
    "pass_property",
    "fail_property",
    "needs_review",
    "not_observed",
    "blocked_by_boundary",
}
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


def to_chatresponder_shadow_json_safe_v1(obj: Any) -> Any:
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
        if label and label not in seen:
            out.append(label)
            seen.add(label)
    return out


def _safe_summary(text: str = "") -> str:
    # Metadata-only summary; never echo prompt/response content.
    cleaned = " ".join(str(text or "").split())[:160]
    return cleaned or "Shadow preflight metadata recorded without raw prompt or response text."


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


def _text_reason_labels(prompt_item: Mapping[str, Any]) -> list[str]:
    text = str(prompt_item.get("prompt_text") or "").lower()
    family = str(prompt_item.get("family") or "")
    labels: list[str] = []
    if bool(prompt_item.get("requires_model_call")) or "model" in text:
        labels.append("model_path_blocked")
    if bool(prompt_item.get("requires_search")) or any(m in text for m in ("search", "look up", "latest")):
        labels.append("search_path_blocked")
    if bool(prompt_item.get("requires_advisor_call")) or "advisor" in text:
        labels.append("advisor_path_blocked")
    if bool(prompt_item.get("requires_memory_write")) or bool(prompt_item.get("requires_write_path")) or any(m in text for m in ("write file", "persist", "save state")):
        labels.append("write_path_blocked")
    if bool(prompt_item.get("requires_memory_write")) or bool(prompt_item.get("requires_weslr_state")) or ".weslr" in text:
        labels.append("weslr_state_blocked")
    if "status" in text or "provider state" in text:
        labels.append("status_path_blocked")
    if family == "evidence_source_boundaries" or any(m in text for m in ("current event", "source", "sources", "prove this")):
        labels.append("currentness_source_blocked")
    if "hidden prompt" in text or "system prompt" in text:
        labels.append("hidden_prompt_blocked")
    if "answer key" in text:
        labels.append("answer_key_blocked")
    if "protected material" in text:
        labels.append("protected_prompt_blocked")
    if family == "self_identity_boundaries" or any(m in text for m in ("what are you", "conscious", "sentient", "alive", "soul", "pretending to be human")):
        labels.append("self_identity_blocked")
    if family == "memory_honesty" or "remember" in text or "memory" in text:
        labels.append("memory_namespace_required")
    if family == "continuity_relationship" or any(m in text for m in ("continue from", "earlier", "stopped expanding")):
        labels.append("continuity_context_required")
    if bool(prompt_item.get("requires_default_enablement")) or "enable by default" in text or "default enable" in text:
        labels.append("default_enablement_blocked")
    if bool(prompt_item.get("requires_branch_expansion")) or "branch expansion" in text or "expand branch" in text:
        labels.append("branch_expansion_blocked")
    if bool(prompt_item.get("requires_raw_prompt_storage")):
        labels.append("raw_prompt_storage_blocked")
    if bool(prompt_item.get("requires_raw_response_storage")):
        labels.append("raw_response_storage_blocked")
    if any(m in text for m in ("password", "secret key", "private key", "api key")) or bool(prompt_item.get("unsafe_prompt_marker")):
        labels.append("unsafe_prompt_marker_blocked")
    return _unique([label for label in labels if label in BLOCKED_PATH_LABELS_V1])


def _is_existing_plan_helper_boundary(prompt_item: Mapping[str, Any]) -> bool:
    if str(prompt_item.get("family") or "") != "live_slice_behavior":
        return False
    text = " ".join(str(prompt_item.get("prompt_text") or "").lower().split())
    return text in {"plan", "help me plan", "plan my next steps"} and bool(prompt_item.get("requires_feature_flag")) is True


def _shadow_family_allowed(prompt_item: Mapping[str, Any]) -> tuple[bool, list[str], str]:
    family = str(prompt_item.get("family") or "")
    if family in {"ordinary_task_behavior", "non_canned_cognition", "conduct_alignment"}:
        return True, [], family
    if family == "live_slice_behavior" and _is_existing_plan_helper_boundary(prompt_item):
        return True, [], "live_slice_behavior_existing_plan_helper_only"
    if family == "live_slice_behavior":
        return False, ["branch_expansion_blocked", "default_enablement_blocked"], family
    if family == "memory_honesty":
        return False, ["memory_namespace_required"], family
    if family == "continuity_relationship":
        return False, ["continuity_context_required"], family
    if family == "self_identity_boundaries":
        return False, ["self_identity_blocked"], family
    if family == "evidence_source_boundaries":
        return False, ["currentness_source_blocked"], family
    if family == "guardrail_preservation":
        return False, ["protected_prompt_blocked", "hidden_prompt_blocked", "answer_key_blocked"], family
    return False, ["unsupported_family_blocked"], family


def build_chatresponder_shadow_config_v1(
    *,
    shadow_call_authorized: bool = False,
    allow_chatresponder_call: bool = False,
    allow_feature_flag_isolation: bool = False,
) -> dict[str, Any]:
    return {
        "config_type": CONFIG_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "observation_mode": OBSERVATION_MODE_V1,
        "shadow_call_authorized": bool(shadow_call_authorized),
        "allow_chatresponder_call": bool(allow_chatresponder_call),
        "allow_feature_flag_isolation": bool(allow_feature_flag_isolation),
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


def preflight_chatresponder_shadow_prompt_v1(prompt_item: dict, *, config: dict | None = None) -> dict[str, Any]:
    cfg = build_chatresponder_shadow_config_v1() if config is None else to_chatresponder_shadow_json_safe_v1(config)
    item = to_chatresponder_shadow_json_safe_v1(prompt_item or {})
    prompt_id = str(item.get("prompt_id") or "") if isinstance(item, Mapping) else ""
    family = str(item.get("family") or "") if isinstance(item, Mapping) else ""
    validation = validate_controlled_behavior_prompt_item_v1(item) if isinstance(item, dict) else {"valid": False, "errors": ["prompt_item must be mapping"], "warnings": []}
    guard = guard_controlled_local_runtime_prompt_item_v1(item if isinstance(item, dict) else {})
    family_allowed, family_reasons, shadow_family = _shadow_family_allowed(item if isinstance(item, Mapping) else {})
    reason_labels: list[str] = []
    reason_labels.extend(family_reasons)
    reason_labels.extend([label for label in guard.get("reason_labels", []) if label in BLOCKED_PATH_LABELS_V1])
    reason_labels.extend(_text_reason_labels(item if isinstance(item, Mapping) else {}))
    if not validation.get("valid", False):
        for error in validation.get("errors", []):
            if "requires_model_call" in error:
                reason_labels.append("model_path_blocked")
            elif "requires_search" in error or "source URL" in error:
                reason_labels.append("search_path_blocked")
            elif "requires_memory_write" in error:
                reason_labels.extend(["write_path_blocked", "weslr_state_blocked"])
            elif "raw/private/protected" in error:
                reason_labels.append("unsafe_prompt_marker_blocked")
            else:
                reason_labels.append("unsafe_prompt_marker_blocked")
    if bool(cfg.get("default_enablement_allowed", False)) or bool(item.get("requires_default_enablement", False)):
        reason_labels.append("default_enablement_blocked")
    if bool(cfg.get("branch_expansion_allowed", False)) or bool(item.get("requires_branch_expansion", False)):
        reason_labels.append("branch_expansion_blocked")
    if bool(item.get("requires_raw_prompt_storage", False)):
        reason_labels.append("raw_prompt_storage_blocked")
    if bool(item.get("requires_raw_response_storage", False)):
        reason_labels.append("raw_response_storage_blocked")
    reason_labels = _unique([label for label in reason_labels if label in BLOCKED_PATH_LABELS_V1])
    allowed = bool(validation.get("valid", False)) and family_allowed and not reason_labels
    return {
        "preflight_type": PREFLIGHT_TYPE_V1,
        "prompt_id": prompt_id,
        "family": shadow_family if shadow_family == "live_slice_behavior_existing_plan_helper_only" else family,
        "observation_mode": OBSERVATION_MODE_V1,
        "preflight_allowed": allowed,
        "blocked_by_boundary": not allowed,
        "reason_labels": [] if allowed else (reason_labels or ["unsupported_family_blocked"]),
        "safe_summary": _safe_summary("Prompt eligible for future shadow observation." if allowed else "Prompt blocked before shadow observation."),
        "side_effects": _empty_side_effects(),
    }


def build_chatresponder_shadow_observation_v1(
    *,
    prompt_id: str,
    family: str,
    preflight_allowed: bool = False,
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
        "reason_labels": _unique([str(label) for label in (reason_labels or [])]),
        "property_label": str(property_label),
        "properties_observed": [str(p) for p in (properties_observed or [])],
        "properties_missing": [str(p) for p in (properties_missing or [])],
        "safe_summary": _safe_summary(safe_summary),
    }


def validate_chatresponder_shadow_observation_v1(observation: dict) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(observation, Mapping):
        return {"valid": False, "errors": ["observation must be a mapping"], "warnings": []}
    if observation.get("observation_type") != OBSERVATION_TYPE_V1:
        errors.append("wrong observation_type")
    if observation.get("observation_mode") != OBSERVATION_MODE_V1:
        errors.append("observation_mode must be chatresponder_shadow")
    for key in ("user_facing_runtime_change", "model_calls", "advisor_calls", "web_search", "write_paths", "weslr_state_created", "raw_prompt_stored", "raw_response_stored"):
        if observation.get(key) is not False:
            errors.append(f"{key} must be false")
    if observation.get("property_label") not in ALLOWED_PROPERTY_LABELS_V1:
        errors.append(f"invalid property_label: {observation.get('property_label')}")
    family = observation.get("family")
    if family not in (ALLOWED_SHADOW_FAMILIES_V1 | BLOCKED_REFINEMENT_FAMILIES_V1 | {"live_slice_behavior"}):
        errors.append(f"invalid family: {family}")
    for label in observation.get("reason_labels", []) or []:
        if label not in BLOCKED_PATH_LABELS_V1:
            errors.append(f"invalid reason label: {label}")
    if observation.get("blocked_by_boundary") is True and not observation.get("reason_labels"):
        errors.append("blocked_by_boundary=true requires reason_labels")
    if observation.get("chatresponder_called") is True and observation.get("preflight_allowed") is not True:
        errors.append("chatresponder_called=true requires preflight_allowed=true")
    if observation.get("chatresponder_called") is True:
        for key in ("user_facing_runtime_change", "model_calls", "advisor_calls", "web_search", "write_paths", "weslr_state_created", "raw_prompt_stored", "raw_response_stored"):
            if observation.get(key) is not False:
                errors.append(f"chatresponder_called with forbidden side effect: {key}")
    if observation.get("preflight_allowed") is True and observation.get("chatresponder_called") is not True:
        warnings.append("preflight_allowed=true but chatresponder_called=false")
    if observation.get("chatresponder_called") is True and observation.get("property_label") == "not_observed":
        warnings.append("chatresponder_called=true with property_label=not_observed")
    if not str(observation.get("safe_summary") or "").strip():
        warnings.append("safe_summary missing")
    if family in {"live_slice_behavior", "live_slice_behavior_existing_plan_helper_only"} and observation.get("preflight_allowed") is True:
        warnings.append("live_slice_behavior requires future feature flag isolation")
    errors.extend(_forbidden_key_errors(observation))
    errors.extend(_forbidden_claim_errors(observation))
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def preflight_chatresponder_shadow_prompt_set_v1(prompt_set: dict | None = None, *, config: dict | None = None) -> dict[str, Any]:
    prompt_set_obj = build_default_controlled_behavior_prompt_set_v1() if prompt_set is None else to_chatresponder_shadow_json_safe_v1(prompt_set)
    prompt_set_validation = validate_controlled_behavior_prompt_set_v1(prompt_set_obj) if isinstance(prompt_set_obj, dict) else {"valid": False, "errors": ["prompt_set must be mapping"], "warnings": []}
    prompts = list(prompt_set_obj.get("prompts", [])) if isinstance(prompt_set_obj, Mapping) else []
    records = [preflight_chatresponder_shadow_prompt_v1(prompt, config=config) for prompt in prompts]
    family_decisions: dict[str, dict[str, int]] = {}
    for record in records:
        family = str(record.get("family") or "")
        decision = "preflight_allowed" if record.get("preflight_allowed") else "blocked_by_boundary"
        family_decisions.setdefault(family, {})[decision] = family_decisions.setdefault(family, {}).get(decision, 0) + 1
    allowed_count = sum(1 for record in records if record.get("preflight_allowed") is True)
    blocked_count = len(records) - allowed_count
    result = {
        "preflight_result_type": PROMPT_SET_PREFLIGHT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "observation_mode": OBSERVATION_MODE_V1,
        "prompt_execution": False,
        "chatresponder_calls": False,
        "model_calls": False,
        "advisor_calls": False,
        "web_search": False,
        "write_paths": False,
        "weslr_state_created": False,
        "raw_prompt_storage": False,
        "raw_response_storage": False,
        "numeric_scores_used": False,
        "official_claims": False,
        "prompt_count": len(records),
        "family_count": len({record.get("family") for record in records}),
        "preflight_allowed_count": allowed_count,
        "blocked_count": blocked_count,
        "family_decisions": {k: dict(sorted(v.items())) for k, v in sorted(family_decisions.items())},
        "preflight_records": records,
        "validation": {
            "valid": True,
            "errors": [],
            "warnings": [],
            "prompt_set_validation": {
                "valid": bool(prompt_set_validation.get("valid", False)),
                "errors_count": len(prompt_set_validation.get("errors", [])),
                "warnings_count": len(prompt_set_validation.get("warnings", [])),
            },
        },
    }
    result["validation"] = validate_chatresponder_shadow_prompt_set_preflight_v1(result)
    return result


def validate_chatresponder_shadow_prompt_set_preflight_v1(result: dict) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(result, Mapping):
        return {"valid": False, "errors": ["result must be a mapping"], "warnings": []}
    if result.get("preflight_result_type") != PROMPT_SET_PREFLIGHT_TYPE_V1:
        errors.append("wrong preflight_result_type")
    if result.get("observation_mode") != OBSERVATION_MODE_V1:
        errors.append("observation_mode must be chatresponder_shadow")
    for key in ("prompt_execution", "chatresponder_calls", "model_calls", "advisor_calls", "web_search", "write_paths", "weslr_state_created", "raw_prompt_storage", "raw_response_storage", "numeric_scores_used", "official_claims"):
        if result.get(key) is not False:
            errors.append(f"{key} must be false")
    records = result.get("preflight_records", [])
    if not isinstance(records, list):
        errors.append("preflight_records must be a list")
        records = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping) or record.get("preflight_type") != PREFLIGHT_TYPE_V1:
            errors.append(f"preflight_records[{index}] invalid preflight_type")
            continue
        if record.get("observation_mode") != OBSERVATION_MODE_V1:
            errors.append(f"preflight_records[{index}] invalid observation_mode")
        if record.get("side_effects") != _empty_side_effects():
            errors.append(f"preflight_records[{index}] has side effects")
        for label in record.get("reason_labels", []) or []:
            if label not in BLOCKED_PATH_LABELS_V1:
                errors.append(f"preflight_records[{index}] invalid reason label: {label}")
        if record.get("blocked_by_boundary") is True and not record.get("reason_labels"):
            errors.append(f"preflight_records[{index}] blocked without reason labels")
    if result.get("preflight_allowed_count", 0) == 0:
        warnings.append("no allowed prompt records")
    if result.get("prompt_count", 0) and result.get("blocked_count", 0) == result.get("prompt_count", 0):
        warnings.append("all prompts blocked")
    live_decisions = result.get("family_decisions", {}).get("live_slice_behavior_existing_plan_helper_only")
    if live_decisions and live_decisions.get("preflight_allowed", 0):
        warnings.append("live_slice_behavior allowed records require future feature flag isolation")
    errors.extend(_forbidden_key_errors(result))
    errors.extend(_forbidden_claim_errors(result))
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def summarize_chatresponder_shadow_preflight_v1(result: dict) -> dict[str, Any]:
    validation = result.get("validation") if isinstance(result, Mapping) else None
    if not isinstance(validation, Mapping) or "valid" not in validation:
        validation = validate_chatresponder_shadow_prompt_set_preflight_v1(result)
    return {
        "preflight_result_type": result.get("preflight_result_type") if isinstance(result, Mapping) else None,
        "observation_mode": result.get("observation_mode") if isinstance(result, Mapping) else None,
        "prompt_count": result.get("prompt_count", 0) if isinstance(result, Mapping) else 0,
        "family_count": result.get("family_count", 0) if isinstance(result, Mapping) else 0,
        "preflight_allowed_count": result.get("preflight_allowed_count", 0) if isinstance(result, Mapping) else 0,
        "blocked_count": result.get("blocked_count", 0) if isinstance(result, Mapping) else 0,
        "family_decisions": to_chatresponder_shadow_json_safe_v1(result.get("family_decisions", {})) if isinstance(result, Mapping) else {},
        "prompt_execution": bool(result.get("prompt_execution", False)) if isinstance(result, Mapping) else False,
        "chatresponder_calls": bool(result.get("chatresponder_calls", False)) if isinstance(result, Mapping) else False,
        "model_calls": bool(result.get("model_calls", False)) if isinstance(result, Mapping) else False,
        "advisor_calls": bool(result.get("advisor_calls", False)) if isinstance(result, Mapping) else False,
        "web_search": bool(result.get("web_search", False)) if isinstance(result, Mapping) else False,
        "write_paths": bool(result.get("write_paths", False)) if isinstance(result, Mapping) else False,
        "weslr_state_created": bool(result.get("weslr_state_created", False)) if isinstance(result, Mapping) else False,
        "raw_prompt_storage": bool(result.get("raw_prompt_storage", False)) if isinstance(result, Mapping) else False,
        "raw_response_storage": bool(result.get("raw_response_storage", False)) if isinstance(result, Mapping) else False,
        "numeric_scores_used": bool(result.get("numeric_scores_used", False)) if isinstance(result, Mapping) else False,
        "official_claims": bool(result.get("official_claims", False)) if isinstance(result, Mapping) else False,
        "validation_valid": bool(validation.get("valid", False)),
        "errors_count": len(validation.get("errors", [])),
        "warnings_count": len(validation.get("warnings", [])),
        "recommended_next_step": "Review preflight metadata; authorize any future shadow call in a separate task only after boundary coverage is accepted.",
    }


def render_chatresponder_shadow_preflight_markdown_v1(result: dict) -> str:
    summary = summarize_chatresponder_shadow_preflight_v1(result)
    lines = [
        "# WESLR ChatResponder Shadow Preflight V1",
        "",
        "SECTION 1 — STATUS",
        f"- preflight_result_type: {summary['preflight_result_type']}",
        f"- observation_mode: {summary['observation_mode']}",
        f"- prompt_count: {summary['prompt_count']}",
        f"- family_count: {summary['family_count']}",
        f"- preflight_allowed_count: {summary['preflight_allowed_count']}",
        f"- blocked_count: {summary['blocked_count']}",
        "",
        "SECTION 2 — SHADOW PREFLIGHT BOUNDARIES",
        f"- prompt_execution: {str(summary['prompt_execution']).lower()}",
        f"- chatresponder_calls: {str(summary['chatresponder_calls']).lower()}",
        f"- model_calls: {str(summary['model_calls']).lower()}",
        f"- advisor_calls: {str(summary['advisor_calls']).lower()}",
        f"- web_search: {str(summary['web_search']).lower()}",
        f"- write_paths: {str(summary['write_paths']).lower()}",
        f"- weslr_state_created: {str(summary['weslr_state_created']).lower()}",
        "",
        "SECTION 3 — FAMILY ELIGIBILITY",
    ]
    for family, decisions in sorted((summary.get("family_decisions") or {}).items()):
        labels = ", ".join(f"{k}={v}" for k, v in sorted(decisions.items()))
        lines.append(f"- {family}: {labels}")
    lines.extend([
        "",
        "SECTION 4 — BLOCKED PATHS",
        "- blocked records render reason labels only",
        "- unsafe paths remain unexecuted",
        "",
        "SECTION 5 — SAFETY / CLAIM BOUNDARIES",
        "- no external model, advisor, web, persistence, or state paths",
        "- no raw input/output dumps, protected items, or private text",
        "- no numeric scoring or public test assertions",
        "",
        "SECTION 6 — VALIDATION SUMMARY",
        f"- validation_valid: {str(summary['validation_valid']).lower()}",
        f"- errors_count: {summary['errors_count']}",
        f"- warnings_count: {summary['warnings_count']}",
        "",
        "SECTION 7 — RECOMMENDED NEXT STEP",
        f"- {summary['recommended_next_step']}",
    ])
    return "\n".join(lines) + "\n"
