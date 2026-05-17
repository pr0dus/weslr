"""Controlled local runtime guard helpers V1.

This module implements guard decisions for a future controlled local runtime
evaluation lane. It does not execute prompts, call ChatResponder, call
models/search/advisors, persist files, or write WESLR runtime state.
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

GUARD_CONFIG_TYPE_V1 = "weslr_controlled_local_runtime_guard_config_v1"
PROMPT_GUARD_TYPE_V1 = "weslr_controlled_local_runtime_prompt_guard_v1"
PATH_BLOCK_RECORD_TYPE_V1 = "weslr_controlled_local_runtime_path_block_v1"
PROMPT_SET_GUARD_RESULT_TYPE_V1 = "weslr_controlled_local_runtime_prompt_set_guard_v1"
SCHEMA_VERSION_V1 = "1.0"
OBSERVATION_MODE_TARGET_V1 = "controlled_local_runtime"

ALLOWED_FOR_LOCAL_RUNTIME_DESIGN_FAMILIES_V1 = (
    "ordinary_task_behavior",
    "non_canned_cognition",
    "conduct_alignment",
    "live_slice_behavior_existing_plan_helper_only",
)
NEEDS_STUB_REFINEMENT_FAMILIES_V1 = (
    "memory_honesty",
    "evidence_source_boundaries",
    "continuity_relationship",
)
BLOCKED_UNTIL_SEPARATE_DESIGN_FAMILIES_V1 = (
    "self_identity_boundaries",
    "guardrail_preservation_protected_prompts",
    "live_currentness_source_claims",
    "hidden_prompt_execution",
    "answer_key_execution",
    "protected_material_execution",
    "broad_status_path",
    "broad_write_path",
    "broad_search_path",
    "broad_model_path",
)

ALLOWED_DECISION_LABELS_V1 = {
    "allowed_for_local_runtime_design",
    "needs_stub_refinement",
    "blocked_until_separate_design",
    "blocked_by_boundary",
}
ALLOWED_BLOCKER_REASON_LABELS_V1 = {
    "model_path_blocked",
    "search_path_blocked",
    "advisor_path_blocked",
    "write_path_blocked",
    "weslr_state_blocked",
    "status_path_blocked",
    "source_registry_write_blocked",
    "protected_prompt_blocked",
    "hidden_prompt_blocked",
    "answer_key_blocked",
    "self_identity_blocked",
    "memory_namespace_required",
    "continuity_context_required",
    "source_currentness_design_required",
    "branch_expansion_blocked",
    "default_enablement_blocked",
    "high_stakes_prompt_blocked",
    "raw_private_text_blocked",
    "unsafe_prompt_marker_blocked",
    "unsupported_family_blocked",
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
REQUIRED_FALSE_FLAGS_V1 = (
    "prompt_execution",
    "chat_responder_calls",
    "model_calls",
    "advisor_calls",
    "web_search",
    "write_paths",
    "weslr_state_created",
    "raw_private_text_included",
    "raw_text_stored",
    "numeric_scores_used",
    "official_claims",
    "execution_authorized_now",
    "prompt_executed",
    "chat_responder_called",
    "weslr_state",
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


def to_controlled_local_runtime_guard_json_safe_v1(obj: Any) -> Any:
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
        if label not in seen:
            out.append(label)
            seen.add(label)
    return out


def _safe_summary(text: str) -> str:
    return " ".join(str(text or "").split())[:180] or "guard decision recorded without raw prompt text"


def _empty_side_effects() -> dict[str, bool]:
    return {
        "prompt_execution": False,
        "chat_responder_calls": False,
        "model_calls": False,
        "advisor_calls": False,
        "web_search": False,
        "write_paths": False,
        "weslr_state": False,
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
    return errors


def _unsafe_prompt_reason_labels(prompt_item: Mapping[str, Any]) -> list[str]:
    labels: list[str] = []
    text = str(prompt_item.get("prompt_text") or "").lower()
    family = str(prompt_item.get("family") or "")

    if bool(prompt_item.get("requires_model_call")):
        labels.append("model_path_blocked")
    if bool(prompt_item.get("requires_search")):
        labels.append("search_path_blocked")
    if bool(prompt_item.get("requires_memory_write")):
        labels.append("write_path_blocked")
        labels.append("weslr_state_blocked")
    if bool(prompt_item.get("requires_advisor_call")):
        labels.append("advisor_path_blocked")
    if bool(prompt_item.get("requires_write_path")):
        labels.append("write_path_blocked")
    if bool(prompt_item.get("requires_weslr_state")):
        labels.append("weslr_state_blocked")
    if bool(prompt_item.get("requires_source_registry_write")):
        labels.append("source_registry_write_blocked")

    if "hidden prompt" in text or "system prompt" in text:
        labels.append("hidden_prompt_blocked")
    if "answer key" in text:
        labels.append("answer_key_blocked")
    if "protected material" in text:
        labels.append("protected_prompt_blocked")
    if any(marker in text for marker in ("password", "secret key", "private key", "api key")):
        labels.append("raw_private_text_blocked")
    if any(marker in text for marker in ("current event", "latest", "look up", "search", "source", "sources", "prove this")):
        labels.append("source_currentness_design_required")
        if any(marker in text for marker in ("look up", "search", "latest")):
            labels.append("search_path_blocked")
    if any(marker in text for marker in ("what are you", "conscious", "sentient", "alive", "soul", "pretending to be human")) or family == "self_identity_boundaries":
        labels.append("self_identity_blocked")
    if family == "memory_honesty" or any(marker in text for marker in ("remember", "memory")):
        labels.append("memory_namespace_required")
    if family == "continuity_relationship" or any(marker in text for marker in ("continue from", "earlier", "stopped expanding")):
        labels.append("continuity_context_required")
    if any(marker in text for marker in ("status", "inadequacy", "provider state")):
        labels.append("status_path_blocked")
    if any(marker in text for marker in ("medical", "legal", "financial", "diagnose", "investment")):
        labels.append("high_stakes_prompt_blocked")
    if "default enable" in text or "enable by default" in text or bool(prompt_item.get("requires_default_enablement")):
        labels.append("default_enablement_blocked")
    if "expand branch" in text or "branch expansion" in text or bool(prompt_item.get("requires_branch_expansion")):
        labels.append("branch_expansion_blocked")
    if bool(prompt_item.get("unsafe_prompt_marker")):
        labels.append("unsafe_prompt_marker_blocked")
    return _unique(labels)


def _is_plan_helper_boundary_prompt(prompt_item: Mapping[str, Any]) -> bool:
    if str(prompt_item.get("family") or "") not in {"live_slice_behavior", "live_slice_behavior_existing_plan_helper_only"}:
        return False
    text = " ".join(str(prompt_item.get("prompt_text") or "").lower().split())
    if text not in {"plan", "help me plan", "plan my next steps"}:
        return False
    if bool(prompt_item.get("requires_feature_flag")) is not True:
        return False
    forbidden = (
        "lunch", "eat", "food", "workout", "gym", "run", "exercise", "email", "inbox",
        "wife", "partner", "code", "bug", "hidden prompt", "answer key", "protected",
        "search", "source", "sources", "current", "latest", "look up", "remember", "memory",
        "status", "conscious", "sentient", "alive", "soul",
    )
    return not any(marker in text for marker in forbidden)


def build_controlled_local_runtime_guard_config_v1() -> dict[str, Any]:
    return {
        "config_type": GUARD_CONFIG_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "observation_mode_target": OBSERVATION_MODE_TARGET_V1,
        "prompt_execution_authorized": False,
        "chat_responder_calls_authorized": False,
        "model_calls_authorized": False,
        "advisor_calls_authorized": False,
        "web_search_authorized": False,
        "write_paths_authorized": False,
        "weslr_state_authorized": False,
        "raw_private_text_authorized": False,
        "numeric_scoring_authorized": False,
        "official_claims_authorized": False,
        "allowed_families": list(ALLOWED_FOR_LOCAL_RUNTIME_DESIGN_FAMILIES_V1),
        "needs_refinement_families": list(NEEDS_STUB_REFINEMENT_FAMILIES_V1),
        "blocked_families": list(BLOCKED_UNTIL_SEPARATE_DESIGN_FAMILIES_V1),
        "blocked_reason_labels": sorted(ALLOWED_BLOCKER_REASON_LABELS_V1),
    }


def classify_controlled_local_runtime_family_v1(family: str, *, prompt_item: dict | None = None) -> dict[str, Any]:
    family = str(family or "")
    reason_labels: list[str] = []
    if family in {"ordinary_task_behavior", "non_canned_cognition", "conduct_alignment"}:
        classification = "allowed_for_local_runtime_design"
        allowed = True
        requires_refinement = False
        blocked = False
        summary = f"{family} is eligible for future controlled local runtime design."
    elif family == "live_slice_behavior":
        if prompt_item is not None and _is_plan_helper_boundary_prompt(prompt_item):
            classification = "allowed_for_local_runtime_design"
            allowed = True
            requires_refinement = False
            blocked = False
            summary = "live_slice_behavior is eligible only for existing plan-helper boundary."
        else:
            classification = "blocked_by_boundary"
            allowed = False
            requires_refinement = False
            blocked = True
            reason_labels.extend(["branch_expansion_blocked", "default_enablement_blocked"])
            summary = "live_slice_behavior blocked unless it stays inside existing plan-helper boundary."
    elif family in NEEDS_STUB_REFINEMENT_FAMILIES_V1:
        classification = "needs_stub_refinement"
        allowed = False
        requires_refinement = True
        blocked = False
        summary = f"{family} needs stub or context refinement before local runtime observation."
        if family == "memory_honesty":
            reason_labels.append("memory_namespace_required")
        if family == "continuity_relationship":
            reason_labels.append("continuity_context_required")
        if family == "evidence_source_boundaries":
            reason_labels.append("source_currentness_design_required")
    elif family == "self_identity_boundaries":
        classification = "blocked_until_separate_design"
        allowed = False
        requires_refinement = False
        blocked = True
        reason_labels.append("self_identity_blocked")
        summary = "self_identity_boundaries is blocked until separate design."
    elif family == "guardrail_preservation":
        classification = "blocked_until_separate_design"
        allowed = False
        requires_refinement = False
        blocked = True
        reason_labels.extend(["protected_prompt_blocked", "hidden_prompt_blocked", "answer_key_blocked"])
        summary = "guardrail_preservation protected prompts stay blocked until separate design."
    else:
        classification = "blocked_by_boundary"
        allowed = False
        requires_refinement = False
        blocked = True
        reason_labels.append("unsupported_family_blocked")
        summary = "Unsupported family blocked by boundary."
    return {
        "family": family,
        "classification": classification,
        "allowed": allowed,
        "requires_refinement": requires_refinement,
        "blocked": blocked,
        "reason_labels": _unique(reason_labels),
        "safe_summary": _safe_summary(summary),
    }


def guard_controlled_local_runtime_prompt_item_v1(prompt_item: dict) -> dict[str, Any]:
    item = to_controlled_local_runtime_guard_json_safe_v1(prompt_item or {})
    prompt_id = str(item.get("prompt_id") or "")
    family = str(item.get("family") or "")
    item_validation = validate_controlled_behavior_prompt_item_v1(item) if isinstance(item, dict) else {"valid": False, "errors": ["item must be mapping"], "warnings": []}
    classification = classify_controlled_local_runtime_family_v1(family, prompt_item=item if isinstance(item, dict) else None)
    reason_labels = list(classification.get("reason_labels") or [])
    if not item_validation.get("valid", False):
        for err in item_validation.get("errors", []):
            if "requires_model_call" in err:
                reason_labels.append("model_path_blocked")
            elif "requires_search" in err:
                reason_labels.append("search_path_blocked")
            elif "requires_memory_write" in err:
                reason_labels.extend(["write_path_blocked", "weslr_state_blocked"])
            elif "raw/private/protected" in err:
                reason_labels.append("raw_private_text_blocked")
            else:
                reason_labels.append("unsafe_prompt_marker_blocked")
    reason_labels.extend(_unsafe_prompt_reason_labels(item if isinstance(item, Mapping) else {}))
    reason_labels = _unique([r for r in reason_labels if r in ALLOWED_BLOCKER_REASON_LABELS_V1])

    decision = classification["classification"]
    if reason_labels and decision == "allowed_for_local_runtime_design":
        decision = "blocked_by_boundary"
    blocked = decision in {"blocked_by_boundary", "blocked_until_separate_design"}
    future_eligible = decision == "allowed_for_local_runtime_design"
    safe_summary = (
        "Prompt item eligible for future controlled local runtime design; execution remains unauthorized now."
        if future_eligible
        else "Prompt item blocked or held before controlled local runtime observation."
    )
    if decision == "needs_stub_refinement":
        safe_summary = "Prompt item requires stub/context refinement before local runtime observation."
    return {
        "guard_type": PROMPT_GUARD_TYPE_V1,
        "prompt_id": prompt_id,
        "family": family,
        "decision": decision,
        "allowed_to_execute_future_local_runtime": bool(future_eligible),
        "execution_authorized_now": False,
        "blocked": bool(blocked),
        "reason_labels": reason_labels,
        "safe_summary": _safe_summary(safe_summary),
        "side_effects": _empty_side_effects(),
        "item_validation": {
            "valid": bool(item_validation.get("valid", False)),
            "errors_count": len(item_validation.get("errors", [])),
            "warnings_count": len(item_validation.get("warnings", [])),
        },
    }


def build_controlled_local_runtime_path_block_record_v1(
    *,
    prompt_id: str = "",
    family: str = "",
    reason_labels: list[str] | None = None,
    safe_summary: str = "",
) -> dict[str, Any]:
    labels = [str(label) for label in (reason_labels or ["unsupported_family_blocked"])]
    return {
        "record_type": PATH_BLOCK_RECORD_TYPE_V1,
        "prompt_id": str(prompt_id),
        "family": str(family),
        "blocked_by_boundary": True,
        "reason_labels": _unique(labels),
        "safe_summary": _safe_summary(safe_summary or "Path blocked by controlled local runtime guard boundary."),
        "prompt_executed": False,
        "chat_responder_called": False,
        "model_calls": False,
        "advisor_calls": False,
        "web_search": False,
        "write_paths": False,
        "weslr_state_created": False,
        "raw_text_stored": False,
    }


def guard_controlled_local_runtime_prompt_set_v1(prompt_set: dict | None = None) -> dict[str, Any]:
    prompt_set_obj = build_default_controlled_behavior_prompt_set_v1() if prompt_set is None else to_controlled_local_runtime_guard_json_safe_v1(prompt_set)
    prompt_set_validation = validate_controlled_behavior_prompt_set_v1(prompt_set_obj) if isinstance(prompt_set_obj, dict) else {"valid": False, "errors": ["prompt_set must be mapping"], "warnings": []}
    prompts = list(prompt_set_obj.get("prompts", [])) if isinstance(prompt_set_obj, Mapping) else []
    guards = [guard_controlled_local_runtime_prompt_item_v1(prompt) for prompt in prompts]
    decision_counts: dict[str, int] = {}
    family_decisions: dict[str, dict[str, int]] = {}
    for guard in guards:
        decision = guard["decision"]
        family = guard["family"]
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
        family_decisions.setdefault(family, {})[decision] = family_decisions.setdefault(family, {}).get(decision, 0) + 1
    path_block_records = [
        build_controlled_local_runtime_path_block_record_v1(
            prompt_id=guard["prompt_id"],
            family=guard["family"],
            reason_labels=guard.get("reason_labels") or ["unsupported_family_blocked"],
            safe_summary=guard.get("safe_summary", ""),
        )
        for guard in guards
        if guard.get("blocked")
    ]
    result = {
        "guard_result_type": PROMPT_SET_GUARD_RESULT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
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
        "prompt_count": len(guards),
        "family_count": len({g["family"] for g in guards}),
        "decision_counts": dict(sorted(decision_counts.items())),
        "family_decisions": {k: dict(sorted(v.items())) for k, v in sorted(family_decisions.items())},
        "prompt_guards": guards,
        "path_block_records": path_block_records,
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
    result["validation"] = validate_controlled_local_runtime_prompt_set_guard_v1(result)
    return result


def validate_controlled_local_runtime_guard_config_v1(config: dict) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(config, Mapping):
        return {"valid": False, "errors": ["config must be a mapping"], "warnings": []}
    if config.get("config_type") != GUARD_CONFIG_TYPE_V1:
        errors.append("invalid config_type")
    for key in (
        "prompt_execution_authorized", "chat_responder_calls_authorized", "model_calls_authorized",
        "advisor_calls_authorized", "web_search_authorized", "write_paths_authorized",
        "weslr_state_authorized", "raw_private_text_authorized", "numeric_scoring_authorized",
        "official_claims_authorized",
    ):
        if config.get(key) is not False:
            errors.append(f"{key} must be false")
    if set(config.get("allowed_families", [])) != set(ALLOWED_FOR_LOCAL_RUNTIME_DESIGN_FAMILIES_V1):
        errors.append("allowed_families mismatch")
    if set(config.get("needs_refinement_families", [])) != set(NEEDS_STUB_REFINEMENT_FAMILIES_V1):
        errors.append("needs_refinement_families mismatch")
    if set(config.get("blocked_families", [])) != set(BLOCKED_UNTIL_SEPARATE_DESIGN_FAMILIES_V1):
        errors.append("blocked_families mismatch")
    unknown_reasons = set(config.get("blocked_reason_labels", [])) - ALLOWED_BLOCKER_REASON_LABELS_V1
    if unknown_reasons:
        errors.append(f"unknown blocked reason labels: {sorted(unknown_reasons)}")
    errors.extend(_forbidden_key_errors(config))
    errors.extend(_forbidden_claim_errors(config))
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def validate_controlled_local_runtime_prompt_guard_v1(guard: dict) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(guard, Mapping):
        return {"valid": False, "errors": ["guard must be a mapping"], "warnings": []}
    if guard.get("guard_type") != PROMPT_GUARD_TYPE_V1:
        errors.append("invalid guard_type")
    decision = guard.get("decision")
    if decision not in ALLOWED_DECISION_LABELS_V1:
        errors.append(f"invalid decision label: {decision}")
    for label in guard.get("reason_labels", []) or []:
        if label not in ALLOWED_BLOCKER_REASON_LABELS_V1:
            errors.append(f"invalid reason label: {label}")
    if guard.get("execution_authorized_now") is not False:
        errors.append("execution_authorized_now must be false")
    if guard.get("family") == "unknown_family" and not guard.get("blocked"):
        errors.append("unknown family must be blocked")
    if guard.get("family") == "live_slice_behavior" and guard.get("decision") == "allowed_for_local_runtime_design":
        pid = str(guard.get("prompt_id") or "")
        if pid not in {"live_slice_behavior_001", "live_slice_behavior_002", "live_slice_behavior_003", "live_slice_plan_safe"}:
            errors.append("live_slice_behavior allowed without plan-helper boundary")
    for key, value in (guard.get("side_effects") or {}).items():
        if key in REQUIRED_FALSE_FLAGS_V1 and value is not False:
            errors.append(f"{key} must be false")
    errors.extend(_forbidden_key_errors(guard))
    errors.extend(_forbidden_claim_errors(guard))
    if not str(guard.get("safe_summary") or "").strip():
        warnings.append("safe_summary missing")
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def _validate_path_block_record(record: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if record.get("record_type") != PATH_BLOCK_RECORD_TYPE_V1:
        errors.append("invalid path block record_type")
    if record.get("blocked_by_boundary") is not True:
        errors.append("blocked_by_boundary must be true")
    for key in ("prompt_executed", "chat_responder_called", "model_calls", "advisor_calls", "web_search", "write_paths", "weslr_state_created", "raw_text_stored"):
        if record.get(key) is not False:
            errors.append(f"{key} must be false")
    for label in record.get("reason_labels", []) or []:
        if label not in ALLOWED_BLOCKER_REASON_LABELS_V1:
            errors.append(f"invalid reason label: {label}")
    if not str(record.get("safe_summary") or "").strip():
        warnings.append("path block safe_summary missing")
    return errors, warnings


def validate_controlled_local_runtime_prompt_set_guard_v1(result: dict) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(result, Mapping):
        return {"valid": False, "errors": ["result must be a mapping"], "warnings": []}
    if result.get("guard_result_type") != PROMPT_SET_GUARD_RESULT_TYPE_V1:
        errors.append("invalid guard_result_type")
    for key in ("prompt_execution", "chat_responder_calls", "model_calls", "advisor_calls", "web_search", "write_paths", "weslr_state_created", "raw_private_text_included", "numeric_scores_used", "official_claims"):
        if result.get(key) is not False:
            errors.append(f"{key} must be false")
    for guard in result.get("prompt_guards", []) or []:
        validation = validate_controlled_local_runtime_prompt_guard_v1(guard)
        errors.extend(f"prompt_guard: {err}" for err in validation["errors"])
        warnings.extend(f"prompt_guard: {warn}" for warn in validation["warnings"])
    for record in result.get("path_block_records", []) or []:
        record_errors, record_warnings = _validate_path_block_record(record)
        errors.extend(f"path_block_record: {err}" for err in record_errors)
        warnings.extend(f"path_block_record: {warn}" for warn in record_warnings)
    if not result.get("prompt_guards"):
        warnings.append("no prompt guards present")
    allowed_counts = result.get("decision_counts", {}).get("allowed_for_local_runtime_design", 0)
    if allowed_counts == 0:
        warnings.append("allowed families have zero prompts")
    if result.get("prompt_count") and result.get("decision_counts", {}).get("blocked_by_boundary", 0) == result.get("prompt_count"):
        warnings.append("all prompts blocked")
    if "live_slice_behavior" in result.get("family_decisions", {}):
        warnings.append("live_slice_behavior prompts require careful future flag isolation")
    errors.extend(_forbidden_key_errors(result))
    errors.extend(_forbidden_claim_errors(result))
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def summarize_controlled_local_runtime_prompt_set_guard_v1(result: dict) -> dict[str, Any]:
    validation = result.get("validation") or validate_controlled_local_runtime_prompt_set_guard_v1(result)
    return {
        "guard_result_type": result.get("guard_result_type"),
        "prompt_count": result.get("prompt_count", 0),
        "family_count": result.get("family_count", 0),
        "decision_counts": to_controlled_local_runtime_guard_json_safe_v1(result.get("decision_counts", {})),
        "family_decisions": to_controlled_local_runtime_guard_json_safe_v1(result.get("family_decisions", {})),
        "prompt_execution": bool(result.get("prompt_execution", False)),
        "chat_responder_calls": bool(result.get("chat_responder_calls", False)),
        "model_calls": bool(result.get("model_calls", False)),
        "advisor_calls": bool(result.get("advisor_calls", False)),
        "web_search": bool(result.get("web_search", False)),
        "write_paths": bool(result.get("write_paths", False)),
        "weslr_state_created": bool(result.get("weslr_state_created", False)),
        "raw_private_text_included": bool(result.get("raw_private_text_included", False)),
        "numeric_scores_used": bool(result.get("numeric_scores_used", False)),
        "official_claims": bool(result.get("official_claims", False)),
        "validation_valid": bool(validation.get("valid", False)),
        "errors_count": len(validation.get("errors", [])),
        "warnings_count": len(validation.get("warnings", [])),
    }


def render_controlled_local_runtime_prompt_set_guard_markdown_v1(result: dict) -> str:
    summary = summarize_controlled_local_runtime_prompt_set_guard_v1(result)
    lines = [
        "# WESLR Controlled Local Runtime Prompt Set Guard V1",
        "",
        "SECTION 1 — STATUS",
        f"- guard_result_type: {summary['guard_result_type']}",
        f"- prompt_count: {summary['prompt_count']}",
        f"- family_count: {summary['family_count']}",
        f"- prompt_execution: {str(summary['prompt_execution']).lower()}",
        f"- chat_responder_calls: {str(summary['chat_responder_calls']).lower()}",
        f"- model_calls: {str(summary['model_calls']).lower()}",
        f"- advisor_calls: {str(summary['advisor_calls']).lower()}",
        f"- web_search: {str(summary['web_search']).lower()}",
        f"- write_paths: {str(summary['write_paths']).lower()}",
        f"- weslr_state_created: {str(summary['weslr_state_created']).lower()}",
        "",
        "SECTION 2 — FAMILY ELIGIBILITY",
    ]
    for family, decisions in sorted((summary.get("family_decisions") or {}).items()):
        labels = ", ".join(f"{k}={v}" for k, v in sorted(decisions.items()))
        lines.append(f"- {family}: {labels}")
    lines.extend(["", "SECTION 3 — PROMPT GUARD SUMMARY"])
    for decision, count in sorted((summary.get("decision_counts") or {}).items()):
        lines.append(f"- {decision}: {count}")
    lines.extend([
        "",
        "SECTION 4 — PATH BLOCKERS",
        "- blocked records use reason labels only; no prompt or response text is rendered",
        "- blocked_by_boundary prompts remain unexecuted",
        "",
        "SECTION 5 — SAFETY / CLAIM BOUNDARIES",
        "- no external model, advisor, or web/search calls",
        "- no write paths or runtime state creation",
        "- no raw private text, protected content, answer keys, or prompt dumps",
        "- no numeric scoring or public/official testing claims",
        "",
        "SECTION 6 — VALIDATION SUMMARY",
        f"- validation_valid: {str(summary['validation_valid']).lower()}",
        f"- errors_count: {summary['errors_count']}",
        f"- warnings_count: {summary['warnings_count']}",
        "",
        "SECTION 7 — RECOMMENDED NEXT STEP",
        "- Review guard output; implement adapter only in a separate approved task after blocker coverage is accepted.",
    ])
    return "\n".join(lines) + "\n"
