#!/usr/bin/env python3
"""Canned helper shadow comparison helpers V1.

Compares labeled legacy/canned helper surfaces against the unified response
formation shadow object. This module is shadow-only: it does not call live chat,
wire runtime behavior, call models/advisors/search, execute solvers, persist
state, or produce final live answers.
"""

from __future__ import annotations

import copy
import hashlib
import re
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional

from weslr.unified_response_formation_shadow import (
    FRONTIER_KEY_V1,
    build_unified_response_formation_shadow_v1,
    to_unified_response_formation_shadow_json_safe_v1,
)

COMPARISON_TYPE_V1 = "canned_helper_shadow_comparison_v1"
SCHEMA_VERSION_V1 = "1.0"

CANNED_HELPER_INVENTORY_V1: Dict[str, Dict[str, Any]] = {
    "chat_responder_topic_helper": {
        "legacy_surface": "chat_responder_topic_helper",
        "allowed_role": "ordinary_cognition",
        "demotion_candidate": True,
        "risk_reason": "fixed topic helper can bypass unified state/context/evidence/ranking path",
        "can_compare_in_shadow": True,
        "must_not_replace_live_without_owner_approval": True,
    },
    "chat_responder_low_focus_fallback": {
        "legacy_surface": "chat_responder_low_focus_fallback",
        "allowed_role": "fallback_surface",
        "demotion_candidate": True,
        "risk_reason": "fixed low-focus fallback can sound like cognition without enough state grounding",
        "can_compare_in_shadow": True,
        "must_not_replace_live_without_owner_approval": True,
    },
    "chat_responder_vague_fallback": {
        "legacy_surface": "chat_responder_vague_fallback",
        "allowed_role": "fallback_surface",
        "demotion_candidate": True,
        "risk_reason": "generic vague fallback should become clarification/state-aware candidate metadata",
        "can_compare_in_shadow": True,
        "must_not_replace_live_without_owner_approval": True,
    },
    "omnichat_contract_reply": {
        "legacy_surface": "omnichat_contract_reply",
        "allowed_role": "fallback_surface",
        "demotion_candidate": True,
        "risk_reason": "contract copy is acceptable as UI contract text, not as core cognition",
        "can_compare_in_shadow": True,
        "must_not_replace_live_without_owner_approval": True,
    },
    "deterministic_handler_status_surface": {
        "legacy_surface": "deterministic_handler_status_surface",
        "allowed_role": "status_surface",
        "demotion_candidate": False,
        "risk_reason": "deterministic read-only command/status surfaces may remain deterministic",
        "can_compare_in_shadow": True,
        "must_not_replace_live_without_owner_approval": True,
    },
    "capability_welcome_fallback": {
        "legacy_surface": "capability_welcome_fallback",
        "allowed_role": "fallback_surface",
        "demotion_candidate": True,
        "risk_reason": "welcome fallback is bounded onboarding copy, not unified cognition",
        "can_compare_in_shadow": True,
        "must_not_replace_live_without_owner_approval": True,
    },
    "continuity_note_bridge": {
        "legacy_surface": "continuity_note_bridge",
        "allowed_role": "status_surface",
        "demotion_candidate": False,
        "risk_reason": "continuity note may be state-derived status; keep bounded and non-authoritative",
        "can_compare_in_shadow": True,
        "must_not_replace_live_without_owner_approval": True,
    },
    "evidence_bridge_guardrail_or_fallback": {
        "legacy_surface": "evidence_bridge_guardrail_or_fallback",
        "allowed_role": "guardrail",
        "demotion_candidate": False,
        "risk_reason": "evidence bridge boundaries are guardrails/fallbacks, not ordinary cognition",
        "can_compare_in_shadow": True,
        "must_not_replace_live_without_owner_approval": True,
    },
    "unknown_legacy_surface": {
        "legacy_surface": "unknown_legacy_surface",
        "allowed_role": "unknown",
        "demotion_candidate": False,
        "risk_reason": "unknown legacy surface requires more inspection before disposition",
        "can_compare_in_shadow": True,
        "must_not_replace_live_without_owner_approval": True,
    },
}

FORBIDDEN_KEYS_V1 = {
    "raw_text",
    "normalized_text",
    "tokens",
    "source_urls",
    "source_url",
    "raw_source_text",
    "source_text",
    "hidden_prompt",
    "hidden_prompts",
    "answer_key",
    "answer_keys",
    "protected_material",
    "protected_test_item",
    "protected_test_items",
    "official_iq_score",
    "official_benchmark_score",
    "certification_claim",
    "memory_write",
    "memory_writes",
    "truth_write",
    "truth_writes",
    "registry_write",
    "registry_writes",
}

TRUE_FORBIDDEN_FLAGS_V1 = {
    "safe_to_replace_live",
    "runtime_wiring",
    "live_runtime_output",
    "model_calls",
    "advisor_calls",
    "web_search",
    "search_calls",
    "solver_execution",
    "answer_selection_arbitration",
    "persistence",
    "writes_performed",
    "weslr_state_created",
    "weslr_runtime_state_created",
    "source_registry_write",
    "memory_write",
    "truth_write",
}

FORBIDDEN_TEXT_MARKERS_V1 = {
    "hidden_prompt_exposure": ["hidden prompt", "system prompt secret", "hidden system prompt"],
    "answer_key_exposure": ["answer key", "protected test item", "protected benchmark item"],
    "protected_material_exposure": ["protected material", "verbatim protected"],
    "official_evaluation_claim": ["official iq", "certified iq", "official benchmark", "officially certified", "certification claim"],
    "fake_consciousness_claim": ["i am sentient", "i have a soul", "biologically conscious", "theologically conscious", "conscious like a human"],
    "runtime_authorization_drift": ["runtime wiring authorized", "broad runtime replacement", "created .weslr", "write .weslr"],
    "model_or_search_authorization": ["model_calls: true", "advisor_calls: true", "web_search: true", "search_calls: true"],
    "solver_or_arbitration": ["solver_execution: true", "answer_selection_arbitration: true", "answer-selection arbitration"],
}

PRIVATE_LIKE_TOKEN_RE_V1 = re.compile(r"\b(?=[A-Za-z0-9_-]{14,}\b)(?=.*[A-Za-z])(?=.*(?:\d|[_-]))[A-Za-z0-9_-]+\b")
URL_RE_V1 = re.compile(r"(?i)\b(?:https?://|www\.)\S+")

GUARDRAIL_MARKERS_V1 = (
    "hidden prompt", "system prompt", "developer message", "answer key", "protected test",
    "protected material", "private test item", "official iq", "certified iq",
    "official benchmark", "certification", "copyrighted",
)
SELF_HIGH_RISK_MARKERS_V1 = (
    "are you conscious", "conscious like a human", "sentient", "soul",
    "biologically conscious", "theologically conscious", "officially conscious",
)
ORDINARY_TOPIC_MARKERS_V1 = (
    "lunch", "workout", "gym", "email", "draft", "plan", "schedule",
    "debug", "fix", "build", "deploy", "rollout", "checklist", "steps",
)
VAGUE_MARKERS_V1 = ("help me with this", "help with this", "help me with it", "help me", "what should i do")


def to_canned_helper_shadow_comparison_json_safe_v1(obj: Any) -> Any:
    """Return a deep JSON-safe copy. This is not a sanitizer and performs no writes."""
    value = copy.deepcopy(obj)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value):
        return to_canned_helper_shadow_comparison_json_safe_v1(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(k): to_canned_helper_shadow_comparison_json_safe_v1(v)
            for k, v in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple, set)):
        return [to_canned_helper_shadow_comparison_json_safe_v1(v) for v in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return to_canned_helper_shadow_comparison_json_safe_v1(value.to_dict())
    if hasattr(value, "__dict__"):
        return to_canned_helper_shadow_comparison_json_safe_v1(vars(value))
    return repr(value)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return copy.deepcopy(value)
    if isinstance(value, tuple):
        return list(copy.deepcopy(value))
    if isinstance(value, set):
        return sorted(copy.deepcopy(value), key=repr)
    return [copy.deepcopy(value)]


def _contains_any(text: str, markers: Iterable[str]) -> bool:
    lowered = (text or "").lower()
    return any(marker in lowered for marker in markers)


def _walk(obj: Any, path: str = "") -> Iterable[tuple[str, Any]]:
    yield path, obj
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            child = f"{path}.{key}" if path else str(key)
            yield from _walk(value, child)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from _walk(value, f"{path}[{index}]")


def _inventory_for(legacy_surface: str) -> Dict[str, Any]:
    return copy.deepcopy(CANNED_HELPER_INVENTORY_V1.get(legacy_surface) or CANNED_HELPER_INVENTORY_V1["unknown_legacy_surface"])


def _legacy_text_profile(text: str) -> Dict[str, Any]:
    text = text or ""
    lowered = text.lower()
    unsafe_markers = []
    for category, markers in FORBIDDEN_TEXT_MARKERS_V1.items():
        if _contains_any(lowered, markers):
            unsafe_markers.append(category)
    if URL_RE_V1.search(text):
        unsafe_markers.append("raw_source_url")
    if PRIVATE_LIKE_TOKEN_RE_V1.search(text):
        unsafe_markers.append("private_like_token")
    return {
        "present": bool(text),
        "length": len(text),
        "fingerprint": hashlib.sha256(text.encode("utf-8")).hexdigest()[:12] if text else "",
        "redacted": bool(text),
        "unsafe_marker_count": len(sorted(set(unsafe_markers))),
        "unsafe_markers": sorted(set(unsafe_markers)),
    }


def _shadow_frontier(shadow: Mapping[str, Any]) -> Mapping[str, Any]:
    return _as_mapping(shadow.get(FRONTIER_KEY_V1))


def _shadow_selected_family(shadow: Mapping[str, Any]) -> str:
    frontier = _shadow_frontier(shadow)
    selected = _as_mapping(shadow.get("selected_preview"))
    return str(frontier.get("selected_candidate_family") or selected.get("candidate_family") or "")


def _shadow_candidate_families(shadow: Mapping[str, Any]) -> List[str]:
    frontier = _shadow_frontier(shadow)
    families = _as_list(frontier.get("candidate_families_considered"))
    if not families:
        families = [p.get("candidate_family") for p in _as_list(shadow.get("candidate_previews")) if isinstance(p, Mapping)]
    return sorted(set(str(f) for f in families if f))


def _shadow_guardrails(shadow: Mapping[str, Any]) -> List[str]:
    return sorted(set(str(g) for g in _as_list(_shadow_frontier(shadow).get("deterministic_guardrails_applied")) if g))


def _shadow_has_self_check(shadow: Mapping[str, Any]) -> bool:
    frontier = _shadow_frontier(shadow)
    dry = _as_mapping(shadow.get("dry_slice_summary"))
    status = frontier.get("self_check_status") or dry.get("self_check_status")
    return bool(status and status != "not_available")


def _detect_legacy_risk_markers(user_message: str, legacy_surface: str, inventory: Mapping[str, Any], profile: Mapping[str, Any]) -> List[str]:
    text = (user_message or "").lower()
    markers: List[str] = ["live_replacement_not_authorized", "owner_approval_required"]
    role = inventory.get("allowed_role")

    if legacy_surface == "chat_responder_topic_helper" or _contains_any(text, ORDINARY_TOPIC_MARKERS_V1):
        markers.extend([
            "fixed_topic_reply",
            "ordinary_cognition_canned",
            "does_not_use_state_context",
            "does_not_use_known_missing_context",
            "does_not_use_evidence_boundary",
            "does_not_use_native_self_check",
        ])
    if legacy_surface in {"chat_responder_vague_fallback", "chat_responder_low_focus_fallback"} or _contains_any(text, VAGUE_MARKERS_V1):
        markers.extend(["generic_vague_fallback", "fallback_surface_not_cognition"])
    if role == "guardrail" or _contains_any(text, GUARDRAIL_MARKERS_V1):
        markers.append("safe_guardrail_surface")
    if role == "status_surface":
        markers.append("status_surface_not_cognition")
    if role == "fallback_surface":
        markers.append("fallback_surface_not_cognition")
    if _contains_any(text, SELF_HIGH_RISK_MARKERS_V1):
        markers.extend(["identity_or_consciousness_script_risk", "prompt_specific_script_risk"])
    if profile.get("unsafe_marker_count"):
        markers.append("legacy_response_text_redacted_or_unsafe")
    return sorted(set(markers))


def _shadow_usefulness_findings(shadow: Mapping[str, Any]) -> List[str]:
    findings: List[str] = []
    frontier = _shadow_frontier(shadow)
    selected = _shadow_selected_family(shadow)
    if selected:
        findings.append("shadow_has_candidate_family")
    if frontier.get("known_context_used") or frontier.get("missing_context"):
        findings.append("shadow_has_known_missing_context")
    if _shadow_has_self_check(shadow):
        findings.append("shadow_has_self_check")
    if _shadow_guardrails(shadow):
        findings.append("shadow_respects_guardrail")
    evidence = _as_mapping(frontier.get("evidence_status"))
    if evidence:
        findings.append("shadow_represents_evidence_boundary")
    if frontier.get("capability_boundary"):
        findings.append("shadow_represents_capability_boundary")
    if frontier.get("memory_boundary"):
        findings.append("shadow_represents_memory_boundary")
    if _as_mapping(frontier.get("relationship_context_used")).get("ranking_signal_used"):
        findings.append("shadow_uses_relationship_marker")
    if _as_mapping(frontier.get("continuity_context_used")).get("ranking_signal_used"):
        findings.append("shadow_uses_continuity_marker")
    findings.extend(["shadow_not_live_ready", "owner_approval_required_before_replacement", "no_live_replacement_authorized"])
    return sorted(set(findings))


def _recommend_disposition(
    *,
    user_message: str,
    legacy_surface: str,
    inventory: Mapping[str, Any],
    risk_markers: List[str],
    selected_family: str,
    guardrails: List[str],
) -> str:
    role = inventory.get("allowed_role")
    text = (user_message or "").lower()
    high_risk_self = "identity_or_consciousness_script_risk" in risk_markers
    guardrail_case = role == "guardrail" or bool(guardrails) or _contains_any(text, GUARDRAIL_MARKERS_V1)

    if high_risk_self:
        return "blocked_high_risk"
    if guardrail_case:
        return "keep_as_guardrail"
    if role == "status_surface":
        return "keep_as_status_surface"
    if legacy_surface == "chat_responder_low_focus_fallback":
        return "keep_as_emergency_fallback"
    if legacy_surface in {"chat_responder_topic_helper", "omnichat_contract_reply", "capability_welcome_fallback"}:
        if selected_family in {"ordinary_task_plan", "clarification", "evidence_provenance", "memory_honest", "boundary_first"}:
            return "demote_after_shadow_validation"
        return "shadow_compare_more"
    if legacy_surface == "chat_responder_vague_fallback":
        if selected_family in {"clarification", "ordinary_task_plan"}:
            return "demote_after_shadow_validation"
        return "shadow_compare_more"
    if role == "unknown":
        return "shadow_compare_more" if selected_family else "do_not_replace_yet"
    return "do_not_replace_yet"


def _next_action_for(disposition: str) -> str:
    return {
        "keep_as_guardrail": "preserve deterministic boundary; compare only metadata before any owner-approved change",
        "keep_as_status_surface": "preserve as deterministic read-only status surface unless owner requests redesign",
        "keep_as_emergency_fallback": "keep as emergency fallback while shadow comparison gathers coverage",
        "shadow_compare_more": "collect more shadow comparisons; do not replace live behavior",
        "demote_after_shadow_validation": "prepare demotion plan after additional shadow validation and owner approval",
        "do_not_replace_yet": "do not replace; inspect legacy surface and shadow gaps first",
        "blocked_high_risk": "route to separate self/identity/consciousness answer review; do not live-replace",
    }.get(disposition, "do not replace live behavior")


def build_canned_helper_shadow_comparison_v1(
    *,
    user_message: str,
    legacy_surface: str,
    legacy_response_text: str = "",
    legacy_metadata: Optional[dict] = None,
    shadow: Optional[dict] = None,
    shadow_builder_kwargs: Optional[dict] = None,
) -> Dict[str, Any]:
    """Build safe in-memory comparison metadata only.

    Does not invoke live chat responder, models, advisor LLMs, web/search,
    solver execution, answer arbitration, persistence, or runtime wiring.
    """
    inventory = _inventory_for(legacy_surface)
    shadow_built = False
    if shadow is None:
        kwargs = dict(shadow_builder_kwargs or {})
        kwargs.setdefault("user_message", user_message or "")
        shadow = build_unified_response_formation_shadow_v1(**kwargs)
        shadow_built = True
    shadow_safe = to_unified_response_formation_shadow_json_safe_v1(shadow)
    frontier = _shadow_frontier(shadow_safe)
    profile = _legacy_text_profile(legacy_response_text or "")
    risk_markers = _detect_legacy_risk_markers(user_message, legacy_surface, inventory, profile)
    selected_family = _shadow_selected_family(shadow_safe)
    candidate_families = _shadow_candidate_families(shadow_safe)
    guardrails = _shadow_guardrails(shadow_safe)
    findings: List[str] = ["legacy_canned_surface_detected"]

    role = str(inventory.get("allowed_role") or "unknown")
    if role == "guardrail" or "safe_guardrail_surface" in risk_markers:
        findings.append("legacy_valid_guardrail")
    if role == "status_surface":
        findings.append("legacy_status_surface_only")
    if role == "fallback_surface":
        findings.append("legacy_fallback_surface_only")
    if inventory.get("demotion_candidate"):
        findings.append("legacy_demotable_after_shadow_validation")
    if "identity_or_consciousness_script_risk" in risk_markers:
        findings.append("high_risk_self_answer_surface")
    if shadow_built:
        findings.append("shadow_built_by_comparison_helper")
    findings.extend(_shadow_usefulness_findings(shadow_safe))

    disposition = _recommend_disposition(
        user_message=user_message,
        legacy_surface=legacy_surface,
        inventory=inventory,
        risk_markers=risk_markers,
        selected_family=selected_family,
        guardrails=guardrails,
    )

    comparison: Dict[str, Any] = {
        "comparison_type": COMPARISON_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "legacy_surface": inventory.get("legacy_surface", "unknown_legacy_surface"),
        "legacy_role": role,
        "legacy_demotable": bool(inventory.get("demotion_candidate")) and disposition not in {"keep_as_guardrail", "keep_as_status_surface", "blocked_high_risk"},
        "legacy_risk_markers": risk_markers,
        "legacy_response_profile": profile,
        "legacy_metadata_profile": {
            "present": legacy_metadata is not None,
            "keys": sorted(str(k)[:64] for k in (legacy_metadata or {}).keys()) if isinstance(legacy_metadata, Mapping) else [],
            "raw_values_copied": False,
        },
        "shadow_available": bool(shadow_safe),
        "shadow_built_by_comparison_helper": shadow_built,
        "shadow_selected_candidate_family": selected_family,
        "shadow_candidate_families": candidate_families,
        "shadow_guardrails": guardrails,
        "shadow_self_check_available": _shadow_has_self_check(shadow_safe),
        "shadow_evidence_status": _as_mapping(frontier.get("evidence_status")).get("status", ""),
        "comparison_findings": sorted(set(findings)),
        "recommended_disposition": disposition,
        "recommended_next_action": _next_action_for(disposition),
        "safe_to_replace_live": False,
        "requires_owner_approval": True,
        "runtime_wiring": False,
        "live_runtime_output": False,
        "model_calls": False,
        "advisor_calls": False,
        "web_search": False,
        "solver_execution": False,
        "answer_selection_arbitration": False,
        "raw_text_stored": False,
    }
    comparison = to_canned_helper_shadow_comparison_json_safe_v1(comparison)
    comparison["validation"] = validate_canned_helper_shadow_comparison_v1(comparison)
    return comparison


def validate_canned_helper_shadow_comparison_v1(comparison: dict) -> dict:
    """Validate comparison metadata safety and non-authoritative boundaries."""
    safe = to_canned_helper_shadow_comparison_json_safe_v1(comparison)
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    def add_error(category: str, path: str, message: str) -> None:
        errors.append({"category": category, "path": path or "$", "message": message})

    def add_warning(category: str, path: str, message: str) -> None:
        warnings.append({"category": category, "path": path or "$", "message": message})

    if not isinstance(safe, Mapping):
        return {"valid": False, "errors": [{"category": "schema", "path": "$", "message": "comparison must be a mapping"}], "warnings": []}

    if safe.get("comparison_type") != COMPARISON_TYPE_V1:
        add_error("schema", "comparison_type", f"comparison_type must be {COMPARISON_TYPE_V1}")
    if safe.get("safe_to_replace_live") is not False:
        add_error("live_replacement", "safe_to_replace_live", "safe_to_replace_live must remain false")
    if safe.get("requires_owner_approval") is not True:
        add_error("owner_approval", "requires_owner_approval", "owner approval must be required")

    for path, value in _walk(safe):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in FORBIDDEN_KEYS_V1:
            add_error("forbidden_key", path, f"{terminal} must not appear")
        if terminal in TRUE_FORBIDDEN_FLAGS_V1 and value is True:
            add_error("forbidden_authorization_or_side_effect", path, f"{terminal}=true is not allowed")
        if isinstance(value, str):
            lowered = value.lower()
            if URL_RE_V1.search(value):
                add_error("raw_source_url", path, "raw source URLs must not appear")
            for category, markers in FORBIDDEN_TEXT_MARKERS_V1.items():
                if _contains_any(lowered, markers):
                    add_error(category, path, "forbidden text marker present")
        elif isinstance(value, Mapping):
            if value.get("source_registry_write") is True or value.get("registry_write") is True:
                add_error("source_registry_write", path, "source registry writes are forbidden")
            if value.get("memory_write") is True or value.get("truth_write") is True:
                add_error("memory_or_truth_write", path, "memory/truth writes are forbidden")
            if value.get("weslr_state_created") is True or value.get("weslr_runtime_state_created") is True:
                add_error("weslr_state_write", path, ".weslr/runtime state creation is forbidden")

    surface = str(safe.get("legacy_surface") or "")
    role = str(safe.get("legacy_role") or "")
    disposition = str(safe.get("recommended_disposition") or "")
    findings = set(str(x) for x in _as_list(safe.get("comparison_findings")))
    risk_markers = set(str(x) for x in _as_list(safe.get("legacy_risk_markers")))

    if surface == "unknown_legacy_surface" or role == "unknown":
        add_warning("unknown_legacy_surface", "legacy_surface", "unknown legacy surface requires more inspection")
    if safe.get("shadow_available") is not True:
        add_warning("shadow_missing", "shadow_available", "no shadow object supplied or built")
    if safe.get("shadow_built_by_comparison_helper") is True:
        add_warning("shadow_built_by_comparison_helper", "shadow_built_by_comparison_helper", "shadow was built by comparison helper rather than supplied")
    if not safe.get("shadow_selected_candidate_family"):
        add_warning("shadow_selected_candidate_missing", "shadow_selected_candidate_family", "shadow selected candidate family missing")
    if not findings:
        add_warning("no_findings", "comparison_findings", "comparison has no findings")
    if not disposition:
        add_warning("missing_recommended_disposition", "recommended_disposition", "recommended disposition missing")

    if role == "ordinary_cognition" and surface != "unknown_legacy_surface" and safe.get("legacy_demotable") is not True:
        add_warning("ordinary_canned_surface_not_demotable", "legacy_demotable", "ordinary canned surface should be marked demotable")
    if role == "guardrail" and safe.get("legacy_demotable") is True:
        add_error("guardrail_marked_demotable", "legacy_demotable", "guardrail surfaces must not be marked demotable")
    if role == "guardrail" and disposition not in {"keep_as_guardrail", "blocked_high_risk"}:
        add_warning("guardrail_surface_not_preserved", "recommended_disposition", "guardrail surface should be preserved")
    if disposition in {"demote_after_shadow_validation"} and safe.get("requires_owner_approval") is not True:
        add_error("owner_approval", "recommended_disposition", "demotion still requires owner approval")
    if disposition in {"demote_after_shadow_validation"} and safe.get("safe_to_replace_live") is True:
        add_error("live_replacement", "recommended_disposition", "disposition must not imply live replacement")
    if "identity_or_consciousness_script_risk" in risk_markers and disposition not in {"blocked_high_risk", "do_not_replace_yet"}:
        add_error("high_risk_self_surface_not_blocked", "recommended_disposition", "high-risk self/consciousness surface must be blocked or deferred")

    profile = _as_mapping(safe.get("legacy_response_profile"))
    if profile.get("present") and not profile.get("redacted"):
        add_warning("legacy_response_text_not_redacted", "legacy_response_profile", "legacy response text present but not redacted")
    if profile.get("unsafe_marker_count"):
        add_warning("legacy_response_text_unsafe_marker", "legacy_response_profile", "legacy response text contained redacted unsafe markers")

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def summarize_canned_helper_shadow_comparison_v1(comparison: dict) -> dict:
    """Return count/status/label-only safe summary."""
    safe = to_canned_helper_shadow_comparison_json_safe_v1(comparison)
    validation = _as_mapping(safe.get("validation"))
    return {
        "comparison_type": safe.get("comparison_type"),
        "schema_version": safe.get("schema_version"),
        "legacy_surface": safe.get("legacy_surface"),
        "legacy_role": safe.get("legacy_role"),
        "legacy_demotable": bool(safe.get("legacy_demotable")),
        "legacy_risk_marker_count": len(_as_list(safe.get("legacy_risk_markers"))),
        "shadow_available": bool(safe.get("shadow_available")),
        "shadow_selected_candidate_family": safe.get("shadow_selected_candidate_family", ""),
        "shadow_candidate_family_count": len(_as_list(safe.get("shadow_candidate_families"))),
        "shadow_guardrail_count": len(_as_list(safe.get("shadow_guardrails"))),
        "finding_count": len(_as_list(safe.get("comparison_findings"))),
        "recommended_disposition": safe.get("recommended_disposition", ""),
        "safe_to_replace_live": False,
        "requires_owner_approval": True,
        "runtime_wiring": False,
        "live_runtime_output": False,
        "validation_valid": validation.get("valid"),
        "validation_error_count": len(_as_list(validation.get("errors"))),
        "validation_warning_count": len(_as_list(validation.get("warnings"))),
    }


def render_canned_helper_shadow_comparison_markdown_v1(comparison: dict) -> str:
    """Render safe count/status/label-only Markdown for comparison inspection."""
    summary = summarize_canned_helper_shadow_comparison_v1(comparison)
    lines = [
        "# Canned Helper Shadow Comparison",
        f"- comparison_type:{summary.get('comparison_type')}",
        f"- legacy_surface:{summary.get('legacy_surface')}",
        f"- legacy_role:{summary.get('legacy_role')}",
        f"- legacy_demotable:{str(summary.get('legacy_demotable')).lower()}",
        f"- risk_markers:{summary.get('legacy_risk_marker_count')}",
        f"- shadow_available:{str(summary.get('shadow_available')).lower()}",
        f"- selected_family:{summary.get('shadow_selected_candidate_family')}",
        f"- candidate_families:{summary.get('shadow_candidate_family_count')}",
        f"- guardrails:{summary.get('shadow_guardrail_count')}",
        f"- findings:{summary.get('finding_count')}",
        f"- disposition:{summary.get('recommended_disposition')}",
        "- safe_to_replace_live:false",
        "- requires_owner_approval:true",
        "- runtime_wiring:false",
        "- live_runtime_output:false",
    ]
    return "\n".join(lines)


__all__ = [
    "COMPARISON_TYPE_V1",
    "SCHEMA_VERSION_V1",
    "CANNED_HELPER_INVENTORY_V1",
    "build_canned_helper_shadow_comparison_v1",
    "validate_canned_helper_shadow_comparison_v1",
    "to_canned_helper_shadow_comparison_json_safe_v1",
    "summarize_canned_helper_shadow_comparison_v1",
    "render_canned_helper_shadow_comparison_markdown_v1",
]
