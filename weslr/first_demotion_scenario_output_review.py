#!/usr/bin/env python3
"""First demotion scenario output review helpers V1.

Non-live, in-memory qualitative review helpers for the first canned-helper
shadow demotion scenarios. This module reviews existing scenario metadata only:
it does not call live chat, wire runtime behavior, call models/advisors/search,
execute solvers, arbitrate final answers, persist state, or render final
answers.
"""

from __future__ import annotations

import copy
import re
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional

from weslr.first_canned_helper_demotion_shadow_scenarios import (
    ALLOWED_FIRST_CANNED_HELPER_TARGET_BRANCHES_V1,
    build_first_canned_helper_demotion_shadow_scenarios_v1,
)

REVIEW_TYPE_V1 = "first_demotion_scenario_output_review_v1"
REVIEW_BUNDLE_TYPE_V1 = "first_demotion_scenario_output_reviews_bundle_v1"
SUMMARY_TYPE_V1 = "first_demotion_scenario_output_reviews_summary_v1"
SCHEMA_VERSION_V1 = "1.0"

ALLOWED_TARGET_BRANCHES_V1 = frozenset(ALLOWED_FIRST_CANNED_HELPER_TARGET_BRANCHES_V1)
ALLOWED_READINESS_LABELS_V1 = frozenset({
    "shadow_review_ready",
    "needs_more_shadow_detail",
    "not_ready_for_live_design",
    "blocked_high_risk",
    "invalid",
})

CANDIDATE_RANK_ORDER_V1 = [
    "chat_responder_plan_helper",
    "chat_responder_email_helper",
    "chat_responder_lunch_helper",
    "chat_responder_workout_helper",
    "chat_responder_code_bug_helper",
]

COMMON_BOUNDARY_LABELS_V1 = [
    "no_live_replacement",
    "owner_approval_required",
    "no_model_call",
    "no_advisor_call",
    "no_web_search",
    "no_solver_execution",
    "no_answer_arbitration",
    "no_raw_text_storage",
    "no_runtime_wiring",
]

FORBIDDEN_KEYS_V1 = frozenset({
    "raw_text",
    "normalized_text",
    "tokens",
    "safe_prompt",
    "final_answer",
    "response_text",
    "raw_prompt",
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
})

TRUE_FORBIDDEN_FLAGS_V1 = frozenset({
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
    "live_chat_responder_called",
    "chat_responder_called",
})

FORBIDDEN_TEXT_MARKERS_V1 = {
    "hidden_prompt_exposure": ("hidden prompt", "system prompt secret", "hidden system prompt"),
    "answer_key_exposure": ("answer key", "protected test item", "protected benchmark item"),
    "protected_material_exposure": ("protected material", "verbatim protected"),
    "official_evaluation_claim": ("official iq", "certified iq", "official benchmark", "officially certified", "certification claim"),
    "fake_consciousness_claim": ("i am sentient", "i have a soul", "biologically conscious", "theologically conscious", "conscious like a human"),
    "runtime_authorization_drift": ("runtime wiring authorized", "broad runtime replacement", "created .weslr", "write .weslr"),
    "model_or_search_authorization": ("model_calls: true", "advisor_calls: true", "web_search: true", "search_calls: true"),
    "solver_or_arbitration": ("solver_execution: true", "answer_selection_arbitration: true", "answer-selection arbitration"),
    "live_chat_responder_call": ("respond_chat(", "chatresponder.respond_chat", "live chat responder called"),
    "live_ready_label": ("live_ready", "live-ready", "ready_for_live", "safe to replace live"),
}

PRIVATE_LIKE_TOKEN_RE_V1 = re.compile(r"\b(?=[A-Za-z0-9_-]{14,}\b)(?=.*[A-Za-z])(?=.*\d)(?=.*-)[A-Za-z0-9_-]+\b")
URL_RE_V1 = re.compile(r"(?i)\b(?:https?://|www\.)\S+")


def to_first_demotion_scenario_output_review_json_safe_v1(obj: Any) -> Any:
    """Return a deep JSON-safe copy. This is not a sanitizer and performs no writes."""
    value = copy.deepcopy(obj)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value):
        return to_first_demotion_scenario_output_review_json_safe_v1(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(k): to_first_demotion_scenario_output_review_json_safe_v1(v)
            for k, v in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple, set)):
        return [to_first_demotion_scenario_output_review_json_safe_v1(v) for v in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return to_first_demotion_scenario_output_review_json_safe_v1(value.to_dict())
    if hasattr(value, "__dict__"):
        return to_first_demotion_scenario_output_review_json_safe_v1(vars(value))
    return repr(value)


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


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _walk(obj: Any, path: str = "") -> Iterable[tuple[str, Any]]:
    yield path, obj
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            child = f"{path}.{key}" if path else str(key)
            yield from _walk(value, child)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from _walk(value, f"{path}[{index}]")


def _contains_any(text: str, markers: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def _branch_short_name(target_branch: str) -> str:
    return target_branch.replace("chat_responder_", "").replace("_helper", "")


def _branch_specific_profile(target_branch: str, selected_family: str, disposition: str, scenario_valid: bool) -> Dict[str, Any]:
    if not scenario_valid:
        return {
            "quality_label": "invalid_scenario_result",
            "readiness": "invalid",
            "signals": [],
            "missing": ["missing_branch_specific_interpretation"],
            "known": [],
            "missing_context": [],
            "guardrails": [],
            "boundaries": [],
            "differentiation": "invalid",
            "rank_hint": "not_ranked_invalid",
            "next_action": "fix_or_remove_invalid_scenario_metadata",
        }

    ordinary = selected_family == "ordinary_task_plan"
    clarification = selected_family == "clarification"
    demote_after_shadow = disposition == "demote_after_shadow_validation"

    if target_branch == "chat_responder_plan_helper":
        return {
            "quality_label": "strongest_first_design_candidate" if ordinary and demote_after_shadow else "plan_signal_needs_review",
            "readiness": "shadow_review_ready" if ordinary and demote_after_shadow else "needs_more_shadow_detail",
            "signals": ["ordinary_task_plan_match", "branch_specific_signal_present"],
            "missing": [],
            "known": ["ordinary_planning_request", "low_context_private_risk"],
            "missing_context": [],
            "guardrails": ["ordinary_task_guardrail", "no_live_design_authority"],
            "boundaries": [],
            "differentiation": "strong_match_to_ordinary_planning",
            "rank_hint": "rank_1_design_priority",
            "next_action": "use_as_first_future_design_candidate_after_owner_review",
        }
    if target_branch == "chat_responder_email_helper":
        return {
            "quality_label": "strong_but_private_text_sensitive" if clarification else "email_signal_needs_private_boundary_review",
            "readiness": "shadow_review_ready" if clarification else "needs_more_shadow_detail",
            "signals": ["clarification_match", "branch_specific_signal_present"],
            "missing": ["missing_private_text_boundary"] if "private_text_boundary_needed" == "" else [],
            "known": ["drafting_request", "missing_audience_tone_content_likely"],
            "missing_context": ["email_audience", "email_tone", "email_content_boundary"],
            "guardrails": ["no_send_action", "no_private_text_storage"],
            "boundaries": ["private_text_boundary_needed"],
            "differentiation": "strong_clarification_signal_for_email_drafting",
            "rank_hint": "rank_2_design_priority",
            "next_action": "add_private_text_and_send_boundary_detail_before_live_design",
        }
    if target_branch == "chat_responder_lunch_helper":
        return {
            "quality_label": "moderate_low_risk_context_needed",
            "readiness": "needs_more_shadow_detail",
            "signals": ["ordinary_task_plan_match" if ordinary else "branch_specific_signal_weak"],
            "missing": ["missing_preference_context_boundary"],
            "known": ["low_stakes_ordinary_choice"],
            "missing_context": ["food_preferences", "time_available", "current_context"],
            "guardrails": ["low_stakes_only"],
            "boundaries": ["preference_context_boundary_needed"],
            "differentiation": "moderate_low_risk_but_preference_context_needed",
            "rank_hint": "rank_3_design_priority",
            "next_action": "add_preference_and_current_context_detail_before_live_design",
        }
    if target_branch == "chat_responder_workout_helper":
        return {
            "quality_label": "moderate_health_context_needed",
            "readiness": "needs_more_shadow_detail",
            "signals": ["ordinary_task_plan_match" if ordinary else "branch_specific_signal_weak"],
            "missing": ["missing_health_context_boundary"],
            "known": ["ordinary_physical_activity_request"],
            "missing_context": ["current_condition", "injury_limitations", "time_and_intensity"],
            "guardrails": ["health_context_caution"],
            "boundaries": ["health_context_boundary_needed"],
            "differentiation": "moderate_but_health_current_state_context_needed",
            "rank_hint": "rank_4_design_priority",
            "next_action": "add_health_current_state_boundary_detail_before_live_design",
        }
    if target_branch == "chat_responder_code_bug_helper":
        return {
            "quality_label": "weak_debug_specificity_needed",
            "readiness": "needs_more_shadow_detail",
            "signals": ["branch_specific_signal_weak"],
            "missing": ["missing_debug_context_request"],
            "known": ["debug_request_surface"],
            "missing_context": ["code_excerpt", "error_message", "expected_behavior", "environment"],
            "guardrails": ["no_solver_execution", "no_answer_arbitration"],
            "boundaries": ["debug_context_boundary_needed"],
            "differentiation": "weak_generic_debug_signal_needs_context_request",
            "rank_hint": "rank_5_design_priority",
            "next_action": "add_debug_context_request_detail_and_solver_boundary_before_live_design",
        }
    return {
        "quality_label": "out_of_scope_branch",
        "readiness": "invalid",
        "signals": [],
        "missing": ["missing_branch_specific_interpretation"],
        "known": [],
        "missing_context": [],
        "guardrails": [],
        "boundaries": [],
        "differentiation": "invalid_target_branch",
        "rank_hint": "not_ranked_invalid",
        "next_action": "remove_out_of_scope_branch_from_review",
    }


def _base_quality_signals(result: Mapping[str, Any]) -> List[str]:
    signals: List[str] = []
    comparison = _as_mapping(result.get("comparison_metadata"))
    validation = _as_mapping(result.get("validation"))
    if result.get("selected_shadow_candidate_family"):
        signals.append("selected_family_present")
    if result.get("recommended_disposition"):
        signals.append("disposition_present")
    if result.get("comparison_available") is True or result.get("shadow_comparison_available") is True:
        signals.append("comparison_available")
    if validation.get("valid") is True or comparison.get("validation_valid") is True:
        signals.append("validation_valid")
    if result.get("requires_owner_approval") is True:
        signals.append("owner_approval_required")
    if all(result.get(flag) is False for flag in ("safe_to_replace_live", "runtime_wiring", "live_runtime_output", "model_calls", "advisor_calls", "web_search", "solver_execution", "answer_selection_arbitration", "raw_text_stored")):
        signals.append("no_live_flags")
    if result.get("selected_shadow_candidate_family") == "ordinary_task_plan":
        signals.append("ordinary_task_plan_match")
    if result.get("selected_shadow_candidate_family") == "clarification":
        signals.append("clarification_match")
    return signals


def build_first_demotion_scenario_output_review_v1(scenario_result: dict) -> dict:
    """Build safe qualitative review metadata for one first-slice scenario result."""
    result = _as_mapping(to_first_demotion_scenario_output_review_json_safe_v1(scenario_result))
    target = str(result.get("target_branch") or "")
    selected = str(result.get("selected_shadow_candidate_family") or "")
    disposition = str(result.get("recommended_disposition") or "")
    scenario_validation = _as_mapping(result.get("validation"))
    scenario_valid = scenario_validation.get("valid") is True and target in ALLOWED_TARGET_BRANCHES_V1
    profile = _branch_specific_profile(target, selected, disposition, scenario_valid)

    quality_signals = sorted(set(_base_quality_signals(result) + profile["signals"] + [
        "known_missing_context_available" if profile["known"] or profile["missing_context"] else "",
        "self_check_available" if scenario_validation else "",
        "boundary_labels_available" if profile["boundaries"] else "",
    ]) - {""})

    missing_quality_signals = sorted(set(profile["missing"] + [
        "missing_known_context_labels" if not profile["known"] else "",
        "missing_missing_context_labels" if not profile["missing_context"] else "",
        "missing_self_check_label" if not scenario_validation else "",
        "missing_guardrail_labels" if not profile["guardrails"] else "",
        "missing_boundary_labels" if not profile["boundaries"] and target != "chat_responder_plan_helper" else "",
        "missing_branch_specific_interpretation" if profile["quality_label"] in {"invalid_scenario_result", "out_of_scope_branch"} else "",
    ]) - {""})

    boundary_labels = list(COMMON_BOUNDARY_LABELS_V1) + list(profile["boundaries"])
    review: Dict[str, Any] = {
        "review_type": REVIEW_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "target_branch": target,
        "selected_shadow_candidate_family": selected,
        "recommended_disposition": disposition,
        "branch_quality_label": profile["quality_label"],
        "branch_readiness_label": profile["readiness"],
        "quality_signals": quality_signals,
        "missing_quality_signals": missing_quality_signals,
        "risk_labels": [] if scenario_valid else ["invalid_or_out_of_scope_scenario"],
        "known_context_labels": profile["known"],
        "missing_context_labels": profile["missing_context"],
        "self_check_label": "scenario_validation_valid" if scenario_valid else "scenario_validation_invalid",
        "guardrail_labels": sorted(set(profile["guardrails"] + ["no_live_replacement", "owner_approval_required"])),
        "boundary_labels": sorted(set(boundary_labels)),
        "differentiation_label": profile["differentiation"],
        "future_design_rank_hint": profile["rank_hint"],
        "recommended_next_action": profile["next_action"],
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
    review = to_first_demotion_scenario_output_review_json_safe_v1(review)
    review["validation"] = validate_first_demotion_scenario_output_review_v1(review)
    return review


def _extract_results(bundle_or_results: dict | list[dict] | None) -> List[dict]:
    if bundle_or_results is None:
        return _as_list(build_first_canned_helper_demotion_shadow_scenarios_v1().get("scenario_results"))
    if isinstance(bundle_or_results, list):
        return _as_list(bundle_or_results)
    mapping = _as_mapping(bundle_or_results)
    if "scenario_results" in mapping:
        return _as_list(mapping.get("scenario_results"))
    if mapping.get("scenario_result_type"):
        return [dict(mapping)]
    return []


def build_first_demotion_scenario_output_reviews_v1(bundle_or_results: dict | list[dict] | None = None) -> dict:
    """Build a safe qualitative review bundle for first-slice scenario outputs."""
    scenario_results = _extract_results(bundle_or_results)
    reviews = [build_first_demotion_scenario_output_review_v1(dict(result)) for result in scenario_results]
    readiness_counts = {label: sum(1 for review in reviews if review.get("branch_readiness_label") == label) for label in ALLOWED_READINESS_LABELS_V1}
    bundle: Dict[str, Any] = {
        "review_bundle_type": REVIEW_BUNDLE_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "scenario_review_count": len(reviews),
        "shadow_review_ready_count": readiness_counts.get("shadow_review_ready", 0),
        "needs_more_shadow_detail_count": readiness_counts.get("needs_more_shadow_detail", 0),
        "invalid_count": readiness_counts.get("invalid", 0),
        "recommended_first_design_candidate": "chat_responder_plan_helper",
        "candidate_rank_order": list(CANDIDATE_RANK_ORDER_V1),
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
        "scenario_reviews": reviews,
    }
    bundle = to_first_demotion_scenario_output_review_json_safe_v1(bundle)
    bundle["validation"] = validate_first_demotion_scenario_output_reviews_bundle_v1(bundle)
    return bundle


def validate_first_demotion_scenario_output_review_v1(review: dict) -> dict:
    """Validate one qualitative scenario output review."""
    safe = to_first_demotion_scenario_output_review_json_safe_v1(review)
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    def add_error(category: str, path: str, message: str) -> None:
        errors.append({"category": category, "path": path or "$", "message": message})

    def add_warning(category: str, path: str, message: str) -> None:
        warnings.append({"category": category, "path": path or "$", "message": message})

    if not isinstance(safe, Mapping):
        return {"valid": False, "errors": [{"category": "schema", "path": "$", "message": "review must be a mapping"}], "warnings": []}
    if safe.get("review_type") != REVIEW_TYPE_V1:
        add_error("schema", "review_type", f"review_type must be {REVIEW_TYPE_V1}")

    target = str(safe.get("target_branch") or "")
    readiness = str(safe.get("branch_readiness_label") or "")
    quality_label = str(safe.get("branch_quality_label") or "")
    boundary_labels = set(str(x) for x in _as_list(safe.get("boundary_labels")))

    if target not in ALLOWED_TARGET_BRANCHES_V1:
        add_error("target_branch_out_of_scope", "target_branch", "target branch is outside allowed first-slice candidates")
    if readiness not in ALLOWED_READINESS_LABELS_V1:
        add_error("readiness_label", "branch_readiness_label", "readiness label must be non-live and allowed")
    if "live_ready" in readiness or "ready_for_live" in readiness:
        add_error("readiness_live_drift", "branch_readiness_label", "readiness label must not imply live-ready")

    for flag in ("safe_to_replace_live", "runtime_wiring", "live_runtime_output", "model_calls", "advisor_calls", "web_search", "solver_execution", "answer_selection_arbitration", "raw_text_stored"):
        if safe.get(flag) is not False:
            add_error("forbidden_flag", flag, f"{flag} must remain false")
    if safe.get("requires_owner_approval") is not True:
        add_error("owner_approval", "requires_owner_approval", "owner approval must be required")

    if not safe.get("selected_shadow_candidate_family"):
        add_warning("selected_candidate_family_missing", "selected_shadow_candidate_family", "no selected candidate family")
    if not safe.get("recommended_disposition"):
        add_warning("recommended_disposition_missing", "recommended_disposition", "no recommended disposition")
    if not _as_list(safe.get("quality_signals")):
        add_warning("quality_signals_missing", "quality_signals", "no quality signals")
    if not _as_list(safe.get("missing_quality_signals")):
        add_warning("missing_quality_signals_missing", "missing_quality_signals", "no missing-quality signals")
    if not boundary_labels:
        add_warning("boundary_labels_missing", "boundary_labels", "no boundary labels")
    if not safe.get("self_check_label"):
        add_warning("self_check_missing", "self_check_label", "no self-check label")
    if not quality_label:
        add_warning("branch_specific_label_missing", "branch_quality_label", "no branch-specific label")

    if target == "chat_responder_email_helper" and "private_text_boundary_needed" not in boundary_labels:
        add_warning("email_private_boundary_missing", "boundary_labels", "email missing private-text boundary")
    if target == "chat_responder_workout_helper" and "health_context_boundary_needed" not in boundary_labels:
        add_warning("workout_health_boundary_missing", "boundary_labels", "workout missing health-context boundary")
    if target == "chat_responder_lunch_helper" and "preference_context_boundary_needed" not in boundary_labels:
        add_warning("lunch_preference_boundary_missing", "boundary_labels", "lunch missing preference-context boundary")
    if target == "chat_responder_code_bug_helper" and "debug_context_boundary_needed" not in boundary_labels:
        add_warning("code_debug_boundary_missing", "boundary_labels", "code/bug missing debug-context boundary")
    if target == "chat_responder_code_bug_helper" and quality_label == "strongest_first_design_candidate":
        add_warning("code_bug_marked_strongest", "branch_quality_label", "code/bug should not be strongest candidate")

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
            if PRIVATE_LIKE_TOKEN_RE_V1.search(value) and terminal not in {"target_branch", "review_type", "schema_version"}:
                add_error("private_like_text", path, "private-like raw text must not appear")
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

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def validate_first_demotion_scenario_output_reviews_bundle_v1(bundle: dict) -> dict:
    """Validate a qualitative scenario output review bundle."""
    safe = to_first_demotion_scenario_output_review_json_safe_v1(bundle)
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    def add_error(category: str, path: str, message: str) -> None:
        errors.append({"category": category, "path": path or "$", "message": message})

    def add_warning(category: str, path: str, message: str) -> None:
        warnings.append({"category": category, "path": path or "$", "message": message})

    if not isinstance(safe, Mapping):
        return {"valid": False, "errors": [{"category": "schema", "path": "$", "message": "bundle must be a mapping"}], "warnings": []}
    if safe.get("review_bundle_type") != REVIEW_BUNDLE_TYPE_V1:
        add_error("schema", "review_bundle_type", f"review_bundle_type must be {REVIEW_BUNDLE_TYPE_V1}")

    reviews = _as_list(safe.get("scenario_reviews"))
    if safe.get("scenario_review_count") != len(reviews):
        add_error("count_mismatch", "scenario_review_count", "scenario_review_count must match scenario_reviews length")
    if len(reviews) != 5:
        add_warning("non_default_review_count", "scenario_reviews", "default bundle should contain exactly five reviews")
    targets = [str(_as_mapping(review).get("target_branch") or "") for review in reviews]
    if len(reviews) == 5 and set(targets) != set(ALLOWED_TARGET_BRANCHES_V1):
        add_error("target_set", "scenario_reviews", "five-review default bundle must contain exactly the allowed first-slice targets")
    for target in targets:
        if target and target not in ALLOWED_TARGET_BRANCHES_V1:
            add_error("target_branch_out_of_scope", "scenario_reviews", "out-of-scope target appears in bundle")

    rank_order = [str(x) for x in _as_list(safe.get("candidate_rank_order"))]
    if any(target not in ALLOWED_TARGET_BRANCHES_V1 for target in rank_order):
        add_error("rank_order_out_of_scope", "candidate_rank_order", "rank order must use only allowed branches")
    if rank_order and rank_order[0] != "chat_responder_plan_helper":
        add_warning("plan_not_ranked_first", "candidate_rank_order", "plan should be first qualitative design candidate")
    if safe.get("recommended_first_design_candidate") != "chat_responder_plan_helper":
        add_warning("recommended_first_not_plan", "recommended_first_design_candidate", "recommended first candidate should be plan unless explicit safe reason exists")

    for flag in ("safe_to_replace_live", "runtime_wiring", "live_runtime_output", "model_calls", "advisor_calls", "web_search", "solver_execution", "answer_selection_arbitration", "raw_text_stored"):
        if safe.get(flag) is not False:
            add_error("forbidden_flag", flag, f"{flag} must remain false")
    if safe.get("requires_owner_approval") is not True:
        add_error("owner_approval", "requires_owner_approval", "owner approval must be required")

    ready_count = 0
    detail_count = 0
    invalid_count = 0
    for index, review in enumerate(reviews):
        validation = validate_first_demotion_scenario_output_review_v1(dict(_as_mapping(review)))
        if not validation.get("valid"):
            add_error("review_invalid", f"scenario_reviews[{index}]", "scenario review failed validation")
        readiness = _as_mapping(review).get("branch_readiness_label")
        if readiness == "shadow_review_ready":
            ready_count += 1
        if readiness == "needs_more_shadow_detail":
            detail_count += 1
        if readiness == "invalid":
            invalid_count += 1
        if _as_mapping(review).get("target_branch") == "chat_responder_code_bug_helper" and _as_mapping(review).get("branch_quality_label") == "strongest_first_design_candidate":
            add_warning("code_bug_marked_strongest", f"scenario_reviews[{index}].branch_quality_label", "code/bug should not be strongest candidate")

    if safe.get("shadow_review_ready_count") != ready_count:
        add_error("count_mismatch", "shadow_review_ready_count", "shadow_review_ready_count mismatch")
    if safe.get("needs_more_shadow_detail_count") != detail_count:
        add_error("count_mismatch", "needs_more_shadow_detail_count", "needs_more_shadow_detail_count mismatch")
    if safe.get("invalid_count") != invalid_count:
        add_error("count_mismatch", "invalid_count", "invalid_count mismatch")

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
            if PRIVATE_LIKE_TOKEN_RE_V1.search(value):
                add_error("private_like_text", path, "private-like text must not appear")
            for category, markers in FORBIDDEN_TEXT_MARKERS_V1.items():
                if _contains_any(lowered, markers):
                    add_error(category, path, "forbidden text marker present")

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def summarize_first_demotion_scenario_output_reviews_v1(bundle_or_review: dict) -> dict:
    """Return count/status/label-only safe summary for a review bundle or one review."""
    safe = to_first_demotion_scenario_output_review_json_safe_v1(bundle_or_review)
    mapping = _as_mapping(safe)
    if mapping.get("review_type") == REVIEW_TYPE_V1:
        reviews = [mapping]
        validation = _as_mapping(mapping.get("validation"))
    else:
        reviews = _as_list(mapping.get("scenario_reviews"))
        validation = _as_mapping(mapping.get("validation"))
    readiness_counts = {label: sum(1 for review in reviews if _as_mapping(review).get("branch_readiness_label") == label) for label in sorted(ALLOWED_READINESS_LABELS_V1)}
    return {
        "summary_type": SUMMARY_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "scenario_review_count": len(reviews),
        "target_branches": sorted(str(_as_mapping(review).get("target_branch") or "") for review in reviews if _as_mapping(review).get("target_branch")),
        "branch_quality_labels": sorted(str(_as_mapping(review).get("branch_quality_label") or "") for review in reviews if _as_mapping(review).get("branch_quality_label")),
        "branch_readiness_counts": readiness_counts,
        "recommended_first_design_candidate": mapping.get("recommended_first_design_candidate", "chat_responder_plan_helper"),
        "candidate_rank_order": [str(x) for x in _as_list(mapping.get("candidate_rank_order"))] if mapping.get("candidate_rank_order") else list(CANDIDATE_RANK_ORDER_V1),
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
        "validation_valid": validation.get("valid"),
        "validation_error_count": len(_as_list(validation.get("errors"))),
        "validation_warning_count": len(_as_list(validation.get("warnings"))),
    }


def render_first_demotion_scenario_output_reviews_markdown_v1(bundle_or_review: dict) -> str:
    """Render safe count/status/label-only Markdown for inspection."""
    summary = summarize_first_demotion_scenario_output_reviews_v1(bundle_or_review)
    readiness = summary.get("branch_readiness_counts") or {}
    lines = [
        "# First Demotion Scenario Output Reviews",
        f"- summary_type:{summary.get('summary_type')}",
        f"- scenario_review_count:{summary.get('scenario_review_count')}",
        f"- target_branches:{','.join(summary.get('target_branches') or [])}",
        f"- branch_quality_labels:{','.join(summary.get('branch_quality_labels') or [])}",
        "- branch_readiness_counts:" + ",".join(f"{k}={readiness.get(k, 0)}" for k in sorted(readiness)),
        f"- recommended_first_design_candidate:{summary.get('recommended_first_design_candidate')}",
        f"- candidate_rank_order:{','.join(summary.get('candidate_rank_order') or [])}",
        "- safe_to_replace_live:false",
        "- requires_owner_approval:true",
        "- runtime_wiring:false",
        "- live_runtime_output:false",
        "- model_calls:false",
        "- advisor_calls:false",
        "- web_search:false",
        "- solver_execution:false",
        "- answer_selection_arbitration:false",
        "- raw_text_stored:false",
    ]
    return "\n".join(lines)


__all__ = [
    "REVIEW_TYPE_V1",
    "REVIEW_BUNDLE_TYPE_V1",
    "SUMMARY_TYPE_V1",
    "SCHEMA_VERSION_V1",
    "ALLOWED_TARGET_BRANCHES_V1",
    "ALLOWED_READINESS_LABELS_V1",
    "CANDIDATE_RANK_ORDER_V1",
    "build_first_demotion_scenario_output_review_v1",
    "build_first_demotion_scenario_output_reviews_v1",
    "validate_first_demotion_scenario_output_review_v1",
    "validate_first_demotion_scenario_output_reviews_bundle_v1",
    "to_first_demotion_scenario_output_review_json_safe_v1",
    "summarize_first_demotion_scenario_output_reviews_v1",
    "render_first_demotion_scenario_output_reviews_markdown_v1",
]
