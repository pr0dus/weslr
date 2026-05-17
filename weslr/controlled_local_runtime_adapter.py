"""Controlled local runtime evaluation adapter helpers V1.

This module bridges guarded prompt eligibility to controlled local runtime
observation metadata. It performs no persistence, imports no ChatResponder,
executes no external model/search/advisor paths, and stores no raw prompt or
response text.
"""

from __future__ import annotations

import copy
import re
from dataclasses import asdict, is_dataclass
from typing import Any, Callable, Mapping

from weslr.behavior_evaluation_report import (
    ALLOWED_EVALUATION_FAMILIES_V1 as REPORT_FAMILIES_V1,
    build_behavior_evaluation_family_v1,
    build_behavior_evaluation_report_v1,
    validate_behavior_evaluation_report_v1,
)
from weslr.controlled_behavior_dry_runner import (
    derive_family_label_from_observations_v1,
    derive_readiness_label_from_family_results_v1,
)
from weslr.controlled_behavior_prompt_set import (
    build_default_controlled_behavior_prompt_set_v1,
    validate_controlled_behavior_prompt_item_v1,
    validate_controlled_behavior_prompt_set_v1,
)
from weslr.controlled_local_runtime_guards import (
    guard_controlled_local_runtime_prompt_item_v1,
    guard_controlled_local_runtime_prompt_set_v1,
)

SCHEMA_VERSION_V1 = "1.0"
OBSERVATION_MODE_V1 = "controlled_local_runtime"
ADAPTER_TYPE_V1 = "weslr_controlled_local_runtime_adapter_v1"
CONFIG_TYPE_V1 = "weslr_controlled_local_runtime_adapter_config_v1"
OBSERVATION_TYPE_V1 = "weslr_controlled_local_runtime_observation_v1"
RESULT_TYPE_V1 = "weslr_controlled_local_runtime_adapter_result_v1"

ALLOWED_ADAPTER_SOURCE_TYPES_V1 = {
    "injected_safe_local_adapter",
    "injected_test_adapter",
    "synthetic_local_metadata_adapter",
}
FORBIDDEN_ADAPTER_SOURCE_TYPES_V1 = {
    "direct_chat_responder",
    "external_model",
    "advisor_llm",
    "web_search",
    "production_conversation_log",
    "private_user_text",
    "raw_response_replay",
}
ALLOWED_PROPERTY_LABELS_V1 = {
    "pass_property",
    "fail_property",
    "needs_review",
    "not_observed",
    "blocked_by_boundary",
}
ALLOWED_LOCAL_RUNTIME_FAMILIES_V1 = {
    "ordinary_task_behavior",
    "non_canned_cognition",
    "conduct_alignment",
    "live_slice_behavior",
}
REFINEMENT_ONLY_FAMILIES_V1 = {
    "memory_honesty",
    "evidence_source_boundaries",
    "continuity_relationship",
}
BLOCKED_FAMILIES_V1 = {
    "self_identity_boundaries",
    "guardrail_preservation",
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
SIDE_EFFECT_KEYS_V1 = (
    "prompt_execution",
    "chat_responder_calls",
    "model_calls",
    "advisor_calls",
    "web_search",
    "write_paths",
    "weslr_state_created",
    "raw_text_stored",
)
RESULT_FALSE_KEYS_V1 = (
    "chat_responder_calls",
    "model_calls",
    "advisor_calls",
    "web_search",
    "write_paths",
    "weslr_state_created",
    "raw_private_text_included",
    "numeric_scores_used",
    "official_claims",
)


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


def to_controlled_local_runtime_adapter_json_safe_v1(obj) -> dict:
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


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _safe_list(items: list[str] | None) -> list[str]:
    return [str(item) for item in (items or [])]


def _safe_summary(text: str) -> str:
    return " ".join(str(text or "").split())[:240]


def _empty_side_effects(*, prompt_execution: bool = False) -> dict[str, bool]:
    return {
        "prompt_execution": False,
        "chat_responder_calls": False,
        "model_calls": False,
        "advisor_calls": False,
        "web_search": False,
        "write_paths": False,
        "weslr_state_created": False,
        "raw_text_stored": False,
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
            if "://" in lowered or "www." in lowered:
                errors.append(f"source URL text not allowed at {path or '<root>'}")
    return errors


def build_controlled_local_runtime_adapter_config_v1(
    *,
    execution_authorized: bool = False,
    allow_injected_adapter: bool = False,
    adapter_source_type: str = "injected_test_adapter",
) -> dict:
    return {
        "config_type": CONFIG_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "observation_mode": OBSERVATION_MODE_V1,
        "execution_authorized": bool(execution_authorized),
        "allow_injected_adapter": bool(allow_injected_adapter),
        "direct_chat_responder_allowed": False,
        "chat_responder_import_allowed": False,
        "model_calls_allowed": False,
        "advisor_calls_allowed": False,
        "web_search_allowed": False,
        "write_paths_allowed": False,
        "weslr_state_allowed": False,
        "raw_text_storage_allowed": False,
        "numeric_scoring_allowed": False,
        "official_claims_allowed": False,
        "adapter_source_type": str(adapter_source_type),
    }


def _validate_config(config: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if config.get("config_type") != CONFIG_TYPE_V1:
        errors.append("invalid config_type")
    if config.get("observation_mode") != OBSERVATION_MODE_V1:
        errors.append("observation_mode must be controlled_local_runtime")
    for key in (
        "direct_chat_responder_allowed", "chat_responder_import_allowed", "model_calls_allowed",
        "advisor_calls_allowed", "web_search_allowed", "write_paths_allowed", "weslr_state_allowed",
        "raw_text_storage_allowed", "numeric_scoring_allowed", "official_claims_allowed",
    ):
        if config.get(key) is not False:
            errors.append(f"{key} must remain false")
    source = str(config.get("adapter_source_type") or "")
    if source not in ALLOWED_ADAPTER_SOURCE_TYPES_V1:
        errors.append(f"invalid adapter_source_type: {source}")
    if source in FORBIDDEN_ADAPTER_SOURCE_TYPES_V1:
        errors.append(f"forbidden adapter_source_type: {source}")
    errors.extend(_forbidden_key_errors(config))
    errors.extend(_forbidden_claim_errors(config))
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def build_controlled_local_runtime_observation_v1(
    *,
    prompt_id: str,
    family: str,
    observed: bool = False,
    property_label: str = "not_observed",
    properties_observed: list[str] | None = None,
    properties_missing: list[str] | None = None,
    blocked_by_boundary: bool = False,
    blocker_reason_labels: list[str] | None = None,
    safe_summary: str = "",
    adapter_source_type: str = "injected_test_adapter",
) -> dict:
    return {
        "observation_type": OBSERVATION_TYPE_V1,
        "prompt_id": str(prompt_id),
        "family": str(family),
        "observation_mode": OBSERVATION_MODE_V1,
        "observed": bool(observed),
        "property_label": str(property_label),
        "properties_observed": _safe_list(properties_observed),
        "properties_missing": _safe_list(properties_missing),
        "blocked_by_boundary": bool(blocked_by_boundary),
        "blocker_reason_labels": _safe_list(blocker_reason_labels),
        "safe_summary": _safe_summary(safe_summary or "short sanitized summary only"),
        "adapter_source_type": str(adapter_source_type),
        "side_effects": _empty_side_effects(prompt_execution=bool(observed)),
    }


def validate_controlled_local_runtime_observation_v1(observation: dict) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(observation, Mapping):
        return {"valid": False, "errors": ["observation must be a mapping"], "warnings": []}
    if observation.get("observation_type") != OBSERVATION_TYPE_V1:
        errors.append("wrong observation_type")
    if observation.get("observation_mode") != OBSERVATION_MODE_V1:
        errors.append("observation_mode must be controlled_local_runtime")
    family = str(observation.get("family") or "")
    if family not in REPORT_FAMILIES_V1:
        errors.append(f"invalid family: {family}")
    if family in REFINEMENT_ONLY_FAMILIES_V1 and observation.get("observed") is True:
        errors.append(f"family is refinement-only for local runtime: {family}")
    if family in BLOCKED_FAMILIES_V1 and observation.get("observed") is True:
        errors.append(f"family is blocked for local runtime: {family}")
    label = observation.get("property_label")
    if label not in ALLOWED_PROPERTY_LABELS_V1:
        errors.append(f"invalid property_label: {label}")
    source = str(observation.get("adapter_source_type") or "")
    if source not in ALLOWED_ADAPTER_SOURCE_TYPES_V1:
        errors.append(f"invalid adapter_source_type: {source}")
    if source in FORBIDDEN_ADAPTER_SOURCE_TYPES_V1:
        errors.append(f"forbidden adapter_source_type: {source}")
    side_effects = observation.get("side_effects") or {}
    if not isinstance(side_effects, Mapping):
        errors.append("side_effects must be a mapping")
        side_effects = {}
    for key in SIDE_EFFECT_KEYS_V1:
        if side_effects.get(key) is True:
            errors.append(f"{key} must be false")
    if observation.get("blocked_by_boundary") is True and not observation.get("blocker_reason_labels"):
        errors.append("blocked_by_boundary=true requires blocker reason")
    if observation.get("observed") is True and label == "not_observed":
        errors.append("observed=true cannot use not_observed label")
    if observation.get("observed") is False and observation.get("properties_observed"):
        warnings.append("observed=false with properties_observed present")
    if observation.get("observed") is True and not observation.get("properties_observed"):
        warnings.append("observed=true with no properties_observed")
    summary = str(observation.get("safe_summary") or "")
    if not summary.strip():
        warnings.append("safe_summary missing")
    if len(summary) > 240:
        errors.append("safe_summary too long")
    if source == "injected_test_adapter" and label == "pass_property":
        warnings.append("injected_test_adapter pass_property is not live evidence")
    errors.extend(_forbidden_key_errors(observation))
    errors.extend(_forbidden_claim_errors(observation))
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def _blocked_observation(prompt_item: Mapping[str, Any], guard: Mapping[str, Any], reason: str, *, source: str) -> dict[str, Any]:
    labels = _unique([str(x) for x in (guard.get("reason_labels") or [])] + [reason])
    return build_controlled_local_runtime_observation_v1(
        prompt_id=str(prompt_item.get("prompt_id") or guard.get("prompt_id") or ""),
        family=str(prompt_item.get("family") or guard.get("family") or ""),
        observed=False,
        property_label="blocked_by_boundary" if reason not in {"execution_not_authorized", "no_runtime_adapter_supplied"} else "not_observed",
        blocked_by_boundary=reason not in {"execution_not_authorized", "no_runtime_adapter_supplied"},
        blocker_reason_labels=labels if reason not in {"execution_not_authorized", "no_runtime_adapter_supplied"} else [],
        safe_summary="Local runtime observation not executed; boundary or authorization stopped execution.",
        adapter_source_type=source,
    )


def evaluate_prompt_with_controlled_local_runtime_adapter_v1(
    prompt_item: dict,
    *,
    runtime_adapter: Callable[[dict], dict] | None = None,
    config: dict | None = None,
) -> dict:
    cfg = build_controlled_local_runtime_adapter_config_v1() if config is None else to_controlled_local_runtime_adapter_json_safe_v1(config)
    cfg_validation = _validate_config(cfg) if isinstance(cfg, Mapping) else {"valid": False, "errors": ["config must be mapping"], "warnings": []}
    source = str(cfg.get("adapter_source_type") or "injected_test_adapter") if isinstance(cfg, Mapping) else "injected_test_adapter"
    item = to_controlled_local_runtime_adapter_json_safe_v1(prompt_item or {})
    item_validation = validate_controlled_behavior_prompt_item_v1(item) if isinstance(item, dict) else {"valid": False, "errors": ["prompt_item must be mapping"], "warnings": []}
    guard = guard_controlled_local_runtime_prompt_item_v1(item if isinstance(item, dict) else {})

    if not cfg_validation.get("valid", False):
        obs = _blocked_observation(item if isinstance(item, Mapping) else {}, guard, "invalid_adapter_config", source=source)
        obs["validation"] = validate_controlled_local_runtime_observation_v1(obs)
        return obs
    if not item_validation.get("valid", False) or guard.get("decision") != "allowed_for_local_runtime_design":
        obs = _blocked_observation(item if isinstance(item, Mapping) else {}, guard, "guard_blocked_or_refinement_required", source=source)
        obs["guard"] = {"decision": guard.get("decision"), "blocked": guard.get("blocked"), "reason_labels": list(guard.get("reason_labels") or [])}
        obs["validation"] = validate_controlled_local_runtime_observation_v1(obs)
        return obs
    if cfg.get("execution_authorized") is not True:
        obs = _blocked_observation(item, guard, "execution_not_authorized", source=source)
        obs["validation"] = validate_controlled_local_runtime_observation_v1(obs)
        return obs
    if cfg.get("allow_injected_adapter") is not True or runtime_adapter is None:
        obs = _blocked_observation(item, guard, "no_runtime_adapter_supplied", source=source)
        obs["validation"] = validate_controlled_local_runtime_observation_v1(obs)
        return obs
    if not callable(runtime_adapter):
        obs = _blocked_observation(item, guard, "runtime_adapter_not_callable", source=source)
        obs["validation"] = validate_controlled_local_runtime_observation_v1(obs)
        return obs

    try:
        returned = runtime_adapter(to_controlled_local_runtime_adapter_json_safe_v1(item))
    except Exception:
        obs = build_controlled_local_runtime_observation_v1(
            prompt_id=str(item.get("prompt_id") or ""),
            family=str(item.get("family") or ""),
            observed=True,
            property_label="fail_property",
            properties_missing=list(item.get("expected_properties") or []),
            safe_summary="Injected local adapter failed without exposing runtime text.",
            adapter_source_type=source,
        )
        obs["validation"] = validate_controlled_local_runtime_observation_v1(obs)
        return obs

    safe_returned = to_controlled_local_runtime_adapter_json_safe_v1(returned)
    returned_errors = _forbidden_key_errors(safe_returned) + _forbidden_claim_errors(safe_returned)
    if returned_errors:
        fallback = build_controlled_local_runtime_observation_v1(
            prompt_id=str(item.get("prompt_id") or ""),
            family=str(item.get("family") or ""),
            observed=True,
            property_label="fail_property",
            properties_missing=list(item.get("expected_properties") or []),
            safe_summary="Injected local adapter returned unsafe metadata; unsafe content was not propagated.",
            adapter_source_type=source,
        )
        fallback["unsafe_adapter_metadata_rejected"] = True
        fallback["validation"] = validate_controlled_local_runtime_observation_v1(fallback)
        return fallback
    if not isinstance(safe_returned, Mapping):
        obs = build_controlled_local_runtime_observation_v1(
            prompt_id=str(item.get("prompt_id") or ""),
            family=str(item.get("family") or ""),
            observed=True,
            property_label="fail_property",
            safe_summary="Injected local adapter returned invalid metadata shape.",
            adapter_source_type=source,
        )
        obs["validation"] = validate_controlled_local_runtime_observation_v1(obs)
        return obs

    if safe_returned.get("observation_type") != OBSERVATION_TYPE_V1:
        obs = build_controlled_local_runtime_observation_v1(
            prompt_id=str(item.get("prompt_id") or safe_returned.get("prompt_id") or ""),
            family=str(item.get("family") or safe_returned.get("family") or ""),
            observed=bool(safe_returned.get("observed", True)),
            property_label=str(safe_returned.get("property_label") or "needs_review"),
            properties_observed=list(safe_returned.get("properties_observed") or []),
            properties_missing=list(safe_returned.get("properties_missing") or []),
            blocked_by_boundary=bool(safe_returned.get("blocked_by_boundary", False)),
            blocker_reason_labels=list(safe_returned.get("blocker_reason_labels") or []),
            safe_summary=str(safe_returned.get("safe_summary") or "Injected local adapter supplied safe metadata."),
            adapter_source_type=source,
        )
    else:
        obs = dict(safe_returned)
        obs["prompt_id"] = str(item.get("prompt_id") or obs.get("prompt_id") or "")
        obs["family"] = str(item.get("family") or obs.get("family") or "")
        obs["adapter_source_type"] = source
        obs.setdefault("side_effects", _empty_side_effects(prompt_execution=bool(obs.get("observed"))))
    validation = validate_controlled_local_runtime_observation_v1(obs)
    if not validation.get("valid", False):
        fallback = build_controlled_local_runtime_observation_v1(
            prompt_id=str(item.get("prompt_id") or ""),
            family=str(item.get("family") or ""),
            observed=True,
            property_label="fail_property",
            properties_missing=list(item.get("expected_properties") or []),
            safe_summary="Injected local adapter returned unsafe metadata; unsafe content was not propagated.",
            adapter_source_type=source,
        )
        fallback["unsafe_adapter_metadata_rejected"] = True
        fallback["validation"] = validate_controlled_local_runtime_observation_v1(fallback)
        return fallback
    obs["validation"] = validation
    return obs


def _families_from_observations(observations: list[dict]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict]] = {family: [] for family in REPORT_FAMILIES_V1}
    for obs in observations:
        if isinstance(obs, Mapping):
            grouped.setdefault(str(obs.get("family") or ""), []).append(obs)
    families: dict[str, dict[str, Any]] = {}
    for family in REPORT_FAMILIES_V1:
        items = grouped.get(family, [])
        label = derive_family_label_from_observations_v1(items)
        observed = any(bool(item.get("observed")) for item in items)
        properties = sorted({prop for item in items for prop in list(item.get("properties_observed") or [])})
        missing = sorted({prop for item in items for prop in list(item.get("properties_missing") or [])})
        families[family] = build_behavior_evaluation_family_v1(
            family=family,
            label=label,
            observed=observed,
            strengths=["controlled_local_runtime_property_observed"] if label == "pass_property" else [],
            risks=["blocked_or_unobserved_property"] if label in {"fail_property", "blocked_by_boundary"} else [],
            evidence_properties={"observed": properties, "missing": missing, "observation_count": len(items)},
            recommended_next_step="continue_guarded_local_runtime_observation" if observed else "keep_guarded_or_refine_context",
        )
    return families


def evaluate_prompt_set_with_controlled_local_runtime_adapter_v1(
    prompt_set: dict | None = None,
    *,
    runtime_adapters_by_prompt_id: dict | None = None,
    config: dict | None = None,
    repo_head: str = "",
    timestamp_local: str = "",
    recommended_next_step: str = "RUN_WESLR_CONTROLLED_LOCAL_RUNTIME_ADAPTER_REPORT_V1",
) -> dict:
    cfg = build_controlled_local_runtime_adapter_config_v1() if config is None else to_controlled_local_runtime_adapter_json_safe_v1(config)
    prompt_set_obj = build_default_controlled_behavior_prompt_set_v1() if prompt_set is None else to_controlled_local_runtime_adapter_json_safe_v1(prompt_set)
    prompt_set_validation = validate_controlled_behavior_prompt_set_v1(prompt_set_obj) if isinstance(prompt_set_obj, dict) else {"valid": False, "errors": ["prompt_set must be mapping"], "warnings": []}
    guard_result = guard_controlled_local_runtime_prompt_set_v1(prompt_set_obj if isinstance(prompt_set_obj, dict) else None)
    adapters = runtime_adapters_by_prompt_id or {}
    prompts = list(prompt_set_obj.get("prompts", [])) if isinstance(prompt_set_obj, Mapping) else []
    valid_prompt_ids = {str(prompt.get("prompt_id")) for prompt in prompts if isinstance(prompt, Mapping)}
    unknown_adapter_prompt_ids = sorted(str(pid) for pid in adapters.keys() if str(pid) not in valid_prompt_ids)

    observations: list[dict] = []
    adapter_calls = 0
    for prompt in prompts:
        if not isinstance(prompt, Mapping):
            continue
        prompt_id = str(prompt.get("prompt_id") or "")
        adapter = adapters.get(prompt_id)
        before_calls = adapter_calls
        guard = guard_controlled_local_runtime_prompt_item_v1(dict(prompt))
        if guard.get("decision") == "allowed_for_local_runtime_design" and cfg.get("execution_authorized") is True and cfg.get("allow_injected_adapter") is True and adapter is not None:
            adapter_calls += 1
        obs = evaluate_prompt_with_controlled_local_runtime_adapter_v1(dict(prompt), runtime_adapter=adapter, config=cfg)
        if adapter_calls == before_calls and obs.get("observed") is True:
            adapter_calls += 1
        observations.append(obs)

    family_results = _families_from_observations(observations)
    readiness_label = derive_readiness_label_from_family_results_v1(family_results)
    report = build_behavior_evaluation_report_v1(
        repo_head=repo_head or "unknown_head",
        timestamp_local=timestamp_local,
        families=family_results,
        readiness_label=readiness_label,
        recommended_next_step=recommended_next_step,
        notes={
            "observation_mode": OBSERVATION_MODE_V1,
            "adapter_type": ADAPTER_TYPE_V1,
            "guard_first": True,
            "unknown_adapter_prompt_ids": unknown_adapter_prompt_ids,
        },
    )
    result = {
        "adapter_result_type": RESULT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "observation_mode": OBSERVATION_MODE_V1,
        "adapter_type": ADAPTER_TYPE_V1,
        "repo_head": str(repo_head),
        "execution_authorized": bool(cfg.get("execution_authorized")) if isinstance(cfg, Mapping) else False,
        "prompt_execution": False,
        "chat_responder_calls": False,
        "model_calls": False,
        "advisor_calls": False,
        "web_search": False,
        "write_paths": False,
        "weslr_state_created": False,
        "raw_private_text_included": False,
        "numeric_scores_used": False,
        "official_claims": False,
        "prompt_count": len(prompts),
        "family_count": len({str(p.get("family")) for p in prompts if isinstance(p, Mapping)}),
        "observed_prompt_count": sum(1 for obs in observations if obs.get("observed") is True),
        "blocked_prompt_count": sum(1 for obs in observations if obs.get("blocked_by_boundary") is True),
        "observations": observations,
        "family_results": family_results,
        "report": report,
        "guard_result": guard_result,
        "prompt_set_validation": prompt_set_validation,
        "unknown_adapter_prompt_ids": unknown_adapter_prompt_ids,
        "injected_adapter_used": bool(adapter_calls > 0),
        "recommended_next_step": recommended_next_step,
        "validation": {},
    }
    result["validation"] = validate_controlled_local_runtime_adapter_result_v1(result)
    return result


def validate_controlled_local_runtime_adapter_result_v1(result: dict) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(result, Mapping):
        return {"valid": False, "errors": ["result must be a mapping"], "warnings": []}
    if result.get("adapter_result_type") != RESULT_TYPE_V1:
        errors.append("wrong adapter_result_type")
    if result.get("observation_mode") != OBSERVATION_MODE_V1:
        errors.append("observation_mode must be controlled_local_runtime")
    for key in RESULT_FALSE_KEYS_V1:
        if result.get(key) is True:
            errors.append(f"{key} must be false")
    report = result.get("report")
    if not isinstance(report, Mapping):
        errors.append("missing report")
        report_validation = {"valid": False, "errors": ["missing report"], "warnings": []}
    else:
        report_validation = validate_behavior_evaluation_report_v1(dict(report))
        if not report_validation.get("valid", False):
            errors.append("report validation invalid")
    for obs in result.get("observations") or []:
        validation = validate_controlled_local_runtime_observation_v1(obs)
        if not validation.get("valid", False):
            errors.append("invalid observation")
            errors.extend([f"observation: {err}" for err in validation.get("errors", [])])
        warnings.extend([f"observation: {warn}" for warn in validation.get("warnings", [])])
    if result.get("unknown_adapter_prompt_ids"):
        errors.append("unknown adapter prompt IDs")
    if not str(result.get("repo_head") or "").strip() or len(str(result.get("repo_head") or "")) < 8:
        warnings.append("repo_head missing/short")
    if result.get("execution_authorized") is False and not result.get("observations"):
        warnings.append("execution_authorized=false and no observations")
    observations = [obs for obs in (result.get("observations") or []) if isinstance(obs, Mapping)]
    if observations and all(obs.get("property_label") == "not_observed" for obs in observations):
        warnings.append("all observations not_observed")
    if not result.get("injected_adapter_used"):
        warnings.append("no injected adapter used")
    if report_validation.get("warnings"):
        warnings.append("report has warnings")
    guard_validation = (result.get("guard_result") or {}).get("validation") if isinstance(result.get("guard_result"), Mapping) else None
    if isinstance(guard_validation, Mapping) and guard_validation.get("warnings"):
        warnings.append("guard result has warnings")
    errors.extend(_forbidden_key_errors(result))
    errors.extend(_forbidden_claim_errors(result))
    return {"valid": not errors, "errors": _unique(errors), "warnings": _unique(warnings)}


def summarize_controlled_local_runtime_adapter_result_v1(result: dict) -> dict:
    validation = validate_controlled_local_runtime_adapter_result_v1(result)
    family_results = result.get("family_results", {}) if isinstance(result, Mapping) else {}
    report = result.get("report", {}) if isinstance(result, Mapping) else {}
    return {
        "adapter_result_type": result.get("adapter_result_type") if isinstance(result, Mapping) else None,
        "observation_mode": result.get("observation_mode") if isinstance(result, Mapping) else None,
        "execution_authorized": result.get("execution_authorized") if isinstance(result, Mapping) else None,
        "prompt_count": result.get("prompt_count") if isinstance(result, Mapping) else 0,
        "family_count": result.get("family_count") if isinstance(result, Mapping) else 0,
        "observed_prompt_count": result.get("observed_prompt_count") if isinstance(result, Mapping) else 0,
        "blocked_prompt_count": result.get("blocked_prompt_count") if isinstance(result, Mapping) else 0,
        "readiness_label": report.get("readiness_label") if isinstance(report, Mapping) else None,
        "family_labels": {family: section.get("label") for family, section in family_results.items() if isinstance(section, Mapping)} if isinstance(family_results, Mapping) else {},
        "validation_valid": validation.get("valid"),
        "errors_count": len(validation.get("errors", [])),
        "warnings_count": len(validation.get("warnings", [])),
        "prompt_execution": result.get("prompt_execution") if isinstance(result, Mapping) else None,
        "chat_responder_calls": result.get("chat_responder_calls") if isinstance(result, Mapping) else None,
        "model_calls": result.get("model_calls") if isinstance(result, Mapping) else None,
        "advisor_calls": result.get("advisor_calls") if isinstance(result, Mapping) else None,
        "web_search": result.get("web_search") if isinstance(result, Mapping) else None,
        "write_paths": result.get("write_paths") if isinstance(result, Mapping) else None,
        "weslr_state_created": result.get("weslr_state_created") if isinstance(result, Mapping) else None,
        "raw_private_text_included": result.get("raw_private_text_included") if isinstance(result, Mapping) else None,
        "numeric_scores_used": result.get("numeric_scores_used") if isinstance(result, Mapping) else None,
        "official_claims": result.get("official_claims") if isinstance(result, Mapping) else None,
        "recommended_next_step": result.get("recommended_next_step") if isinstance(result, Mapping) else None,
    }


def render_controlled_local_runtime_adapter_markdown_v1(result: dict) -> str:
    summary = summarize_controlled_local_runtime_adapter_result_v1(result)
    family_labels = summary.get("family_labels") or {}
    lines = [
        "SECTION 1 — STATUS",
        f"- adapter_result_type: {summary['adapter_result_type']}",
        f"- observation_mode: {summary['observation_mode']}",
        f"- execution_authorized: {summary['execution_authorized']}",
        f"- prompt_count: {summary['prompt_count']}",
        "SECTION 2 — ADAPTER BOUNDARIES",
        f"- prompt_execution: {summary['prompt_execution']}",
        f"- chat_responder_calls: {summary['chat_responder_calls']}",
        f"- model_calls: {summary['model_calls']}",
        f"- advisor_calls: {summary['advisor_calls']}",
        f"- web_search: {summary['web_search']}",
        f"- write_paths: {summary['write_paths']}",
        "SECTION 3 — GUARD / BLOCK SUMMARY",
        f"- observed_prompt_count: {summary['observed_prompt_count']}",
        f"- blocked_prompt_count: {summary['blocked_prompt_count']}",
        "SECTION 4 — FAMILY RESULTS",
    ]
    for family in sorted(family_labels):
        lines.append(f"- {family}: {family_labels[family]}")
    lines.extend([
        "SECTION 5 — READINESS LABEL",
        f"- readiness_label: {summary['readiness_label']}",
        "SECTION 6 — SAFETY / CLAIM BOUNDARIES",
        f"- raw_private_text_included: {summary['raw_private_text_included']}",
        f"- numeric_scores_used: {summary['numeric_scores_used']}",
        f"- official_claims: {summary['official_claims']}",
        f"- weslr_state_created: {summary['weslr_state_created']}",
        "SECTION 7 — VALIDATION SUMMARY",
        f"- validation_valid: {summary['validation_valid']}",
        f"- errors_count: {summary['errors_count']}",
        f"- warnings_count: {summary['warnings_count']}",
        "SECTION 8 — RECOMMENDED NEXT STEP",
        f"- recommended_next_step: {summary['recommended_next_step']}",
    ])
    text = "\n".join(lines) + "\n"
    validation = _forbidden_key_errors({"markdown": text}) + _forbidden_claim_errors({"markdown": text})
    if validation:
        return "SECTION 1 — STATUS\n- render_blocked: unsafe markdown content detected\n"
    return text
