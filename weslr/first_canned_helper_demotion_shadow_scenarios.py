#!/usr/bin/env python3
"""First canned helper demotion shadow scenarios V1.

Shadow-only, in-memory scenario harness for the first approved low-risk
chat_responder helper candidates. This module does not wire runtime behavior,
call live chat, call models/advisors/search, execute solvers, arbitrate final
answers, persist state, or produce final live answers.
"""

from __future__ import annotations

import copy
import re
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from weslr.canned_helper_shadow_comparison import build_canned_helper_shadow_comparison_v1
from weslr.unified_response_formation_shadow import build_unified_response_formation_shadow_v1

SCENARIO_RESULT_TYPE_V1 = "first_canned_helper_demotion_shadow_scenario_v1"
BUNDLE_TYPE_V1 = "first_canned_helper_demotion_shadow_scenarios_bundle_v1"
SUMMARY_TYPE_V1 = "first_canned_helper_demotion_shadow_scenarios_summary_v1"
SCHEMA_VERSION_V1 = "1.0"
SLICE_TYPE_V1 = "first_canned_helper_demotion_shadow_slice_v1"
LAYER_V1 = "WESLR_RUNTIME_CHANGE_helper_test_source_only"

ALLOWED_FIRST_CANNED_HELPER_TARGET_BRANCHES_V1 = frozenset({
    "chat_responder_lunch_helper",
    "chat_responder_workout_helper",
    "chat_responder_plan_helper",
    "chat_responder_email_helper",
    "chat_responder_code_bug_helper",
})

ALLOWED_FIRST_CANNED_HELPER_LEGACY_SURFACES_V1 = frozenset({
    "chat_responder_topic_helper_ordinary",
    "chat_responder_code_bug_helper",
})

DO_NOT_TOUCH_TARGET_BRANCHES_V1 = frozenset({
    "chat_responder_wife_partner_helper",
    "chat_responder_low_focus_fallback",
    "chat_responder_low_focus_model_path_fallback",
    "chat_responder_vague_fallback",
    "chat_responder_vague_model_path_fallback",
    "chat_responder_model_path",
    "chat_responder_model_unavailable_fallback",
    "chat_responder_model_rescue_surface",
    "chat_responder_model_exception_fallback",
    "chat_responder_identity_self_surface",
    "chat_responder_limited_frontier_identity_surface",
    "chat_responder_limited_ordinary_task_surface",
    "chat_responder_meaning_vector_write_capable_path",
    "state_grounded_self_system_answer_surface",
    "evidence_bridge_guardrail_or_fallback",
    "deterministic_handler_write_capable_surface",
    "deterministic_handler_external_search_surface",
    "staging_arbiter_raw_message_log_surface",
    "deterministic_handler_status_surface",
})

COMMON_EXCLUDED_RISKS_V1 = (
    "model_call",
    "web_search",
    "memory_write",
    "identity_self_claim",
    "protected_material",
    "answer_key",
    "hidden_prompt",
)

FIRST_CANNED_HELPER_DEMOTION_SHADOW_SCENARIOS_V1 = (
    {
        "scenario_id": "lunch_helper_shadow_scenario_v1",
        "target_branch": "chat_responder_lunch_helper",
        "legacy_surface": "chat_responder_topic_helper_ordinary",
        "approx_line_range": "1775-1778",
        "safe_prompt": "Help me decide what to eat before an afternoon task.",
        "expected_shadow_families": ["ordinary_task_plan", "clarification", "teaching_explanation"],
        "excluded_risks": list(COMMON_EXCLUDED_RISKS_V1),
        "safe_to_replace_live": False,
        "requires_owner_approval": True,
    },
    {
        "scenario_id": "workout_helper_shadow_scenario_v1",
        "target_branch": "chat_responder_workout_helper",
        "legacy_surface": "chat_responder_topic_helper_ordinary",
        "approx_line_range": "1780-1785",
        "safe_prompt": "Help me choose a light workout before work.",
        "expected_shadow_families": ["ordinary_task_plan", "clarification", "teaching_explanation"],
        "excluded_risks": list(COMMON_EXCLUDED_RISKS_V1),
        "safe_to_replace_live": False,
        "requires_owner_approval": True,
    },
    {
        "scenario_id": "plan_helper_shadow_scenario_v1",
        "target_branch": "chat_responder_plan_helper",
        "legacy_surface": "chat_responder_topic_helper_ordinary",
        "approx_line_range": "1787-1792",
        "safe_prompt": "Help me make a simple plan for this task.",
        "expected_shadow_families": ["ordinary_task_plan", "clarification", "teaching_explanation"],
        "excluded_risks": list(COMMON_EXCLUDED_RISKS_V1),
        "safe_to_replace_live": False,
        "requires_owner_approval": True,
    },
    {
        "scenario_id": "email_helper_shadow_scenario_v1",
        "target_branch": "chat_responder_email_helper",
        "legacy_surface": "chat_responder_topic_helper_ordinary",
        "approx_line_range": "1794-1797",
        "safe_prompt": "Help me draft an email outline.",
        "expected_shadow_families": ["ordinary_task_plan", "clarification", "teaching_explanation"],
        "excluded_risks": list(COMMON_EXCLUDED_RISKS_V1),
        "safe_to_replace_live": False,
        "requires_owner_approval": True,
    },
    {
        "scenario_id": "code_bug_helper_shadow_scenario_v1",
        "target_branch": "chat_responder_code_bug_helper",
        "legacy_surface": "chat_responder_code_bug_helper",
        "approx_line_range": "1802-1803",
        "safe_prompt": "Help me debug a small code bug.",
        "expected_shadow_families": ["ordinary_task_plan", "clarification", "teaching_explanation"],
        "excluded_risks": list(COMMON_EXCLUDED_RISKS_V1),
        "safe_to_replace_live": False,
        "requires_owner_approval": True,
    },
)

FORBIDDEN_KEYS_V1 = frozenset({
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
}

PRIVATE_LIKE_TOKEN_RE_V1 = re.compile(r"\b(?=[A-Za-z0-9_-]{14,}\b)(?=.*[A-Za-z])(?=.*\d)(?=.*-)[A-Za-z0-9_-]+\b")
URL_RE_V1 = re.compile(r"(?i)\b(?:https?://|www\.)\S+")


def to_first_canned_helper_demotion_shadow_scenarios_json_safe_v1(obj: Any) -> Any:
    """Return a deep JSON-safe copy. This is not a sanitizer and performs no writes."""
    value = copy.deepcopy(obj)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value):
        return to_first_canned_helper_demotion_shadow_scenarios_json_safe_v1(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(k): to_first_canned_helper_demotion_shadow_scenarios_json_safe_v1(v)
            for k, v in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple, set)):
        return [to_first_canned_helper_demotion_shadow_scenarios_json_safe_v1(v) for v in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return to_first_canned_helper_demotion_shadow_scenarios_json_safe_v1(value.to_dict())
    if hasattr(value, "__dict__"):
        return to_first_canned_helper_demotion_shadow_scenarios_json_safe_v1(vars(value))
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


def _scenario_prompt(scenario: Mapping[str, Any]) -> str:
    prompt = str(scenario.get("safe_prompt") or "")
    if not prompt:
        raise ValueError("scenario safe_prompt is required")
    return prompt


def _validate_allowed_scenario_definition(scenario: Mapping[str, Any]) -> None:
    target = str(scenario.get("target_branch") or "")
    legacy_surface = str(scenario.get("legacy_surface") or "")
    if target not in ALLOWED_FIRST_CANNED_HELPER_TARGET_BRANCHES_V1:
        raise ValueError(f"target_branch is outside first-slice scope: {target or '<missing>'}")
    if target in DO_NOT_TOUCH_TARGET_BRANCHES_V1:
        raise ValueError(f"target_branch is explicitly out of scope: {target}")
    if legacy_surface not in ALLOWED_FIRST_CANNED_HELPER_LEGACY_SURFACES_V1:
        raise ValueError(f"legacy_surface is outside first-slice scope: {legacy_surface or '<missing>'}")
    if scenario.get("safe_to_replace_live") is not False:
        raise ValueError("safe_to_replace_live must be false")
    if scenario.get("requires_owner_approval") is not True:
        raise ValueError("requires_owner_approval must be true")


def build_first_canned_helper_demotion_shadow_scenario_v1(scenario: dict) -> dict:
    """Build one shadow-only scenario result and comparison metadata.

    The safe prompt is used transiently to build shadow/comparison metadata, but
    it is not copied into the returned result.
    """
    if not isinstance(scenario, Mapping):
        raise ValueError("scenario must be a mapping")
    _validate_allowed_scenario_definition(scenario)
    prompt = _scenario_prompt(scenario)

    shadow = build_unified_response_formation_shadow_v1(user_message=prompt)
    comparison = build_canned_helper_shadow_comparison_v1(
        user_message=prompt,
        legacy_surface=str(scenario.get("legacy_surface")),
        shadow=shadow,
    )

    selected_family = str(
        comparison.get("shadow_selected_candidate_family")
        or _as_mapping(shadow.get("selected_preview")).get("candidate_family")
        or ""
    )
    recommended_disposition = str(comparison.get("recommended_disposition") or "")
    result: Dict[str, Any] = {
        "scenario_result_type": SCENARIO_RESULT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "slice_type": SLICE_TYPE_V1,
        "scenario_id": str(scenario.get("scenario_id") or ""),
        "target_branch": str(scenario.get("target_branch") or ""),
        "legacy_surface": str(scenario.get("legacy_surface") or ""),
        "approx_line_range": str(scenario.get("approx_line_range") or ""),
        "expected_shadow_families": [str(x) for x in _as_list(scenario.get("expected_shadow_families"))],
        "excluded_risks": [str(x) for x in _as_list(scenario.get("excluded_risks"))],
        "shadow_available": bool(shadow),
        "comparison_available": bool(comparison),
        "shadow_comparison_available": bool(shadow) and bool(comparison),
        "selected_shadow_candidate_family": selected_family,
        "recommended_disposition": recommended_disposition,
        "demotion_candidate": recommended_disposition in {"demote_after_shadow_validation", "shadow_compare_more"},
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
        "live_weslr_behavior_changed": False,
        "helper_sources_reused": {
            "unified_response_formation_shadow": True,
            "canned_helper_shadow_comparison": True,
            "meaning_reuse_native_dry_pipeline_indirect": True,
        },
        "comparison_metadata": {
            "comparison_type": comparison.get("comparison_type"),
            "legacy_role": comparison.get("legacy_role"),
            "legacy_demotable": bool(comparison.get("legacy_demotable")),
            "first_demotion_candidate_shadow_only": bool(comparison.get("first_demotion_candidate_shadow_only")),
            "shadow_candidate_family_count": len(_as_list(comparison.get("shadow_candidate_families"))),
            "finding_count": len(_as_list(comparison.get("comparison_findings"))),
            "validation_valid": _as_mapping(comparison.get("validation")).get("valid"),
            "safe_to_replace_live": False,
            "runtime_wiring": False,
            "live_runtime_output": False,
        },
    }
    result = to_first_canned_helper_demotion_shadow_scenarios_json_safe_v1(result)
    result["validation"] = validate_first_canned_helper_demotion_shadow_scenario_v1(result)
    return result


def _invalid_scenario_result(scenario: Any, error: Exception) -> Dict[str, Any]:
    mapping = _as_mapping(scenario)
    result: Dict[str, Any] = {
        "scenario_result_type": SCENARIO_RESULT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "slice_type": SLICE_TYPE_V1,
        "scenario_id": str(mapping.get("scenario_id") or "invalid_scenario"),
        "target_branch": str(mapping.get("target_branch") or ""),
        "legacy_surface": str(mapping.get("legacy_surface") or ""),
        "shadow_available": False,
        "comparison_available": False,
        "shadow_comparison_available": False,
        "selected_shadow_candidate_family": "",
        "recommended_disposition": "do_not_replace_yet",
        "demotion_candidate": False,
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
        "live_weslr_behavior_changed": False,
        "validation": {
            "valid": False,
            "errors": [{"category": "scenario_rejected", "path": "target_branch", "message": str(error)}],
            "warnings": [],
        },
    }
    return to_first_canned_helper_demotion_shadow_scenarios_json_safe_v1(result)


def build_first_canned_helper_demotion_shadow_scenarios_v1(scenarios: Optional[list[dict]] = None) -> dict:
    """Build an in-memory bundle of first-slice shadow scenario results."""
    scenario_inputs: Sequence[dict] = scenarios if scenarios is not None else list(FIRST_CANNED_HELPER_DEMOTION_SHADOW_SCENARIOS_V1)
    results: List[Dict[str, Any]] = []
    for scenario in scenario_inputs:
        try:
            results.append(build_first_canned_helper_demotion_shadow_scenario_v1(dict(scenario)))
        except Exception as exc:
            results.append(_invalid_scenario_result(scenario, exc))

    valid_count = sum(1 for result in results if _as_mapping(result.get("validation")).get("valid") is True)
    demotion_candidate_count = sum(1 for result in results if result.get("demotion_candidate") is True)
    owner_approval_required_count = sum(1 for result in results if result.get("requires_owner_approval") is True)
    bundle: Dict[str, Any] = {
        "bundle_type": BUNDLE_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "layer": LAYER_V1,
        "live_weslr_behavior_changed": False,
        "scenario_count": len(results),
        "valid_count": valid_count,
        "invalid_count": len(results) - valid_count,
        "demotion_candidate_count": demotion_candidate_count,
        "owner_approval_required_count": owner_approval_required_count,
        "safe_to_replace_live": False,
        "runtime_wiring": False,
        "live_runtime_output": False,
        "model_calls": False,
        "advisor_calls": False,
        "web_search": False,
        "solver_execution": False,
        "answer_selection_arbitration": False,
        "raw_text_stored": False,
        "scenario_results": results,
    }
    bundle = to_first_canned_helper_demotion_shadow_scenarios_json_safe_v1(bundle)
    bundle["validation"] = validate_first_canned_helper_demotion_shadow_scenarios_bundle_v1(bundle)
    return bundle


def validate_first_canned_helper_demotion_shadow_scenario_v1(result: dict) -> dict:
    """Validate scenario metadata safety and first-slice boundaries."""
    safe = to_first_canned_helper_demotion_shadow_scenarios_json_safe_v1(result)
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    def add_error(category: str, path: str, message: str) -> None:
        errors.append({"category": category, "path": path or "$", "message": message})

    def add_warning(category: str, path: str, message: str) -> None:
        warnings.append({"category": category, "path": path or "$", "message": message})

    if not isinstance(safe, Mapping):
        return {"valid": False, "errors": [{"category": "schema", "path": "$", "message": "scenario result must be a mapping"}], "warnings": []}

    if safe.get("scenario_result_type") != SCENARIO_RESULT_TYPE_V1:
        add_error("schema", "scenario_result_type", f"scenario_result_type must be {SCENARIO_RESULT_TYPE_V1}")
    if safe.get("slice_type") != SLICE_TYPE_V1:
        add_error("schema", "slice_type", f"slice_type must be {SLICE_TYPE_V1}")

    target = str(safe.get("target_branch") or "")
    legacy_surface = str(safe.get("legacy_surface") or "")
    if target not in ALLOWED_FIRST_CANNED_HELPER_TARGET_BRANCHES_V1:
        add_error("target_branch_out_of_scope", "target_branch", "target branch is outside allowed first-slice candidates")
    if target in DO_NOT_TOUCH_TARGET_BRANCHES_V1:
        add_error("do_not_touch_branch", "target_branch", "target branch is explicitly out of scope")
    if legacy_surface not in ALLOWED_FIRST_CANNED_HELPER_LEGACY_SURFACES_V1:
        add_error("legacy_surface_out_of_scope", "legacy_surface", "legacy surface is outside allowed first-slice categories")

    for flag in ("safe_to_replace_live", "runtime_wiring", "live_runtime_output", "model_calls", "advisor_calls", "web_search", "solver_execution", "answer_selection_arbitration", "raw_text_stored"):
        if safe.get(flag) is not False:
            add_error("forbidden_flag", flag, f"{flag} must remain false")
    if safe.get("requires_owner_approval") is not True:
        add_error("owner_approval", "requires_owner_approval", "owner approval must be required")
    if safe.get("live_weslr_behavior_changed") is not False:
        add_error("live_behavior_change", "live_weslr_behavior_changed", "live WESLR behavior must remain unchanged")

    selected_family = str(safe.get("selected_shadow_candidate_family") or "")
    disposition = str(safe.get("recommended_disposition") or "")
    expected_families = set(str(x) for x in _as_list(safe.get("expected_shadow_families")) if str(x))
    validation = _as_mapping(safe.get("validation"))

    if not selected_family:
        add_warning("selected_shadow_candidate_family_missing", "selected_shadow_candidate_family", "selected shadow candidate family missing")
    if safe.get("comparison_available") is not True or safe.get("shadow_comparison_available") is not True:
        add_warning("comparison_missing", "comparison_available", "comparison metadata missing")
    if not disposition:
        add_warning("recommended_disposition_missing", "recommended_disposition", "recommended disposition missing")
    if disposition and disposition not in {"demote_after_shadow_validation", "shadow_compare_more"}:
        add_warning("unexpected_recommended_disposition", "recommended_disposition", "disposition should be demote_after_shadow_validation or shadow_compare_more for first slice")
    if selected_family and expected_families and selected_family not in expected_families:
        add_warning("expected_shadow_family_not_present", "selected_shadow_candidate_family", "selected family is outside the scenario expected shadow families")
    if not validation:
        add_warning("validation_missing", "validation", "validation missing from scenario result")
    if safe.get("requires_owner_approval") is not True:
        add_warning("owner_approval_marker_missing", "requires_owner_approval", "owner approval marker missing")
    if not _as_mapping(safe.get("helper_sources_reused")):
        add_warning("known_context_signal_missing", "helper_sources_reused", "no known helper/source signal present")
    if not selected_family:
        add_warning("self_check_signal_missing", "selected_shadow_candidate_family", "no selected family/self-check-derived signal available")

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
            if PRIVATE_LIKE_TOKEN_RE_V1.search(value) and terminal not in {"scenario_id", "target_branch", "legacy_surface", "scenario_result_type", "slice_type", "schema_version"}:
                add_error("private_like_text", path, "private-like raw text must not appear in scenario result")
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


def validate_first_canned_helper_demotion_shadow_scenarios_bundle_v1(bundle: dict) -> dict:
    """Validate a first-slice scenario bundle."""
    safe = to_first_canned_helper_demotion_shadow_scenarios_json_safe_v1(bundle)
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    def add_error(category: str, path: str, message: str) -> None:
        errors.append({"category": category, "path": path or "$", "message": message})

    def add_warning(category: str, path: str, message: str) -> None:
        warnings.append({"category": category, "path": path or "$", "message": message})

    if not isinstance(safe, Mapping):
        return {"valid": False, "errors": [{"category": "schema", "path": "$", "message": "bundle must be a mapping"}], "warnings": []}
    if safe.get("bundle_type") != BUNDLE_TYPE_V1:
        add_error("schema", "bundle_type", f"bundle_type must be {BUNDLE_TYPE_V1}")
    if safe.get("layer") != LAYER_V1:
        add_error("layer", "layer", f"layer must be {LAYER_V1}")

    results = _as_list(safe.get("scenario_results"))
    targets = [str(_as_mapping(result).get("target_branch") or "") for result in results]
    if safe.get("scenario_count") != len(results):
        add_error("count_mismatch", "scenario_count", "scenario_count must match scenario_results length")
    if len(results) == 5 and set(targets) != set(ALLOWED_FIRST_CANNED_HELPER_TARGET_BRANCHES_V1):
        add_error("target_set", "scenario_results", "five-result default bundle must contain exactly the allowed first-slice targets")
    if len(set(targets)) != len([t for t in targets if t]):
        add_error("duplicate_target_branch", "scenario_results", "target branches must be unique within bundle")

    for flag in ("safe_to_replace_live", "runtime_wiring", "live_runtime_output", "model_calls", "advisor_calls", "web_search", "solver_execution", "answer_selection_arbitration", "raw_text_stored", "live_weslr_behavior_changed"):
        if safe.get(flag) is not False:
            add_error("forbidden_flag", flag, f"{flag} must remain false")

    valid_count = 0
    demotion_count = 0
    owner_count = 0
    for index, result in enumerate(results):
        if not isinstance(result, Mapping):
            add_error("scenario_schema", f"scenario_results[{index}]", "scenario result must be a mapping")
            continue
        scenario_validation = validate_first_canned_helper_demotion_shadow_scenario_v1(dict(result))
        if not scenario_validation.get("valid"):
            add_error("scenario_invalid", f"scenario_results[{index}]", "scenario result failed validation")
        else:
            valid_count += 1
        if result.get("target_branch") in DO_NOT_TOUCH_TARGET_BRANCHES_V1:
            add_error("do_not_touch_branch", f"scenario_results[{index}].target_branch", "do-not-touch branch appears in bundle")
        if result.get("target_branch") not in ALLOWED_FIRST_CANNED_HELPER_TARGET_BRANCHES_V1:
            add_error("target_branch_out_of_scope", f"scenario_results[{index}].target_branch", "out-of-scope target appears in bundle")
        if result.get("demotion_candidate") is True:
            demotion_count += 1
        if result.get("requires_owner_approval") is True:
            owner_count += 1

    if safe.get("valid_count") != valid_count:
        add_error("count_mismatch", "valid_count", "valid_count must match valid scenario results")
    if safe.get("invalid_count") != len(results) - valid_count:
        add_error("count_mismatch", "invalid_count", "invalid_count must match invalid scenario results")
    if safe.get("demotion_candidate_count") != demotion_count:
        add_error("count_mismatch", "demotion_candidate_count", "demotion_candidate_count must match scenario results")
    if safe.get("owner_approval_required_count") != owner_count:
        add_error("count_mismatch", "owner_approval_required_count", "owner_approval_required_count must match scenario results")

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
            if PRIVATE_LIKE_TOKEN_RE_V1.search(value) and "scenario_results" not in path:
                add_error("private_like_text", path, "private-like text must not appear in public bundle fields")
            for category, markers in FORBIDDEN_TEXT_MARKERS_V1.items():
                if _contains_any(lowered, markers):
                    add_error(category, path, "forbidden text marker present")

    if len(results) != 5:
        add_warning("non_default_scenario_count", "scenario_results", "default bundle should contain exactly five scenarios")

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def summarize_first_canned_helper_demotion_shadow_scenarios_v1(bundle_or_result: dict) -> dict:
    """Return count/status/label-only safe summary for a bundle or one result."""
    safe = to_first_canned_helper_demotion_shadow_scenarios_json_safe_v1(bundle_or_result)
    if isinstance(safe, Mapping) and safe.get("scenario_result_type") == SCENARIO_RESULT_TYPE_V1:
        results = [safe]
        validation = _as_mapping(safe.get("validation"))
        live_changed = bool(safe.get("live_weslr_behavior_changed"))
    else:
        results = _as_list(_as_mapping(safe).get("scenario_results"))
        validation = _as_mapping(_as_mapping(safe).get("validation"))
        live_changed = bool(_as_mapping(safe).get("live_weslr_behavior_changed"))
    valid_count = sum(1 for result in results if _as_mapping(_as_mapping(result).get("validation")).get("valid") is True)
    target_branches = sorted(str(_as_mapping(result).get("target_branch") or "") for result in results if _as_mapping(result).get("target_branch"))
    return {
        "summary_type": SUMMARY_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "scenario_count": len(results),
        "valid_count": valid_count,
        "invalid_count": len(results) - valid_count,
        "target_branches": target_branches,
        "allowed_scope": "first_canned_helper_demotion_shadow_slice_only",
        "demotion_candidate_count": sum(1 for result in results if _as_mapping(result).get("demotion_candidate") is True),
        "owner_approval_required_count": sum(1 for result in results if _as_mapping(result).get("requires_owner_approval") is True),
        "safe_to_replace_live": False,
        "runtime_wiring": False,
        "live_runtime_output": False,
        "model_calls": False,
        "advisor_calls": False,
        "web_search": False,
        "solver_execution": False,
        "answer_selection_arbitration": False,
        "raw_text_stored": False,
        "live_weslr_behavior_changed": live_changed,
        "validation_valid": validation.get("valid"),
        "validation_error_count": len(_as_list(validation.get("errors"))),
        "validation_warning_count": len(_as_list(validation.get("warnings"))),
    }


def render_first_canned_helper_demotion_shadow_scenarios_markdown_v1(bundle_or_result: dict) -> str:
    """Render safe count/status/label-only Markdown for inspection."""
    summary = summarize_first_canned_helper_demotion_shadow_scenarios_v1(bundle_or_result)
    lines = [
        "# First Canned Helper Demotion Shadow Scenarios",
        f"- summary_type:{summary.get('summary_type')}",
        f"- scenario_count:{summary.get('scenario_count')}",
        f"- valid_count:{summary.get('valid_count')}",
        f"- invalid_count:{summary.get('invalid_count')}",
        f"- target_branches:{','.join(summary.get('target_branches') or [])}",
        f"- allowed_scope:{summary.get('allowed_scope')}",
        f"- demotion_candidate_count:{summary.get('demotion_candidate_count')}",
        f"- owner_approval_required_count:{summary.get('owner_approval_required_count')}",
        "- safe_to_replace_live:false",
        "- runtime_wiring:false",
        "- live_runtime_output:false",
        "- model_calls:false",
        "- advisor_calls:false",
        "- web_search:false",
        "- solver_execution:false",
        "- answer_selection_arbitration:false",
        "- raw_text_stored:false",
        f"- live_weslr_behavior_changed:{str(summary.get('live_weslr_behavior_changed')).lower()}",
    ]
    return "\n".join(lines)


__all__ = [
    "SCENARIO_RESULT_TYPE_V1",
    "BUNDLE_TYPE_V1",
    "SUMMARY_TYPE_V1",
    "SCHEMA_VERSION_V1",
    "SLICE_TYPE_V1",
    "LAYER_V1",
    "ALLOWED_FIRST_CANNED_HELPER_TARGET_BRANCHES_V1",
    "ALLOWED_FIRST_CANNED_HELPER_LEGACY_SURFACES_V1",
    "DO_NOT_TOUCH_TARGET_BRANCHES_V1",
    "FIRST_CANNED_HELPER_DEMOTION_SHADOW_SCENARIOS_V1",
    "build_first_canned_helper_demotion_shadow_scenario_v1",
    "build_first_canned_helper_demotion_shadow_scenarios_v1",
    "validate_first_canned_helper_demotion_shadow_scenario_v1",
    "validate_first_canned_helper_demotion_shadow_scenarios_bundle_v1",
    "to_first_canned_helper_demotion_shadow_scenarios_json_safe_v1",
    "summarize_first_canned_helper_demotion_shadow_scenarios_v1",
    "render_first_canned_helper_demotion_shadow_scenarios_markdown_v1",
]
