#!/usr/bin/env python3
"""Plan helper demotion pre-live plan helpers V1.

In-memory planning/test metadata for a possible future owner-approved demotion
of exactly one canned chat_responder branch: chat_responder_plan_helper. This
module does not implement the demotion, does not edit chat_responder.py, does
not wire runtime behavior, does not call live chat, does not call
models/advisors/search, does not execute solvers, does not arbitrate final
answers, does not persist state, and does not produce live output.
"""

from __future__ import annotations

import copy
import re
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Mapping

PLAN_TYPE_V1 = "plan_helper_demotion_prelive_plan_v1"
SUMMARY_TYPE_V1 = "plan_helper_demotion_prelive_plan_summary_v1"
SCHEMA_VERSION_V1 = "1.0"
TARGET_BRANCH_V1 = "chat_responder_plan_helper"
TARGET_FILE_V1 = "weslr/chat_responder.py"
FEATURE_FLAG_V1 = "WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1"
REQUIRED_OWNER_APPROVAL_MARKER_V1 = "APPROVE_WESLR_PLAN_HELPER_LIVE_DEMOTION_SLICE_V1"
REQUIRED_LIVE_TASK_NAME_V1 = "IMPLEMENT_WESLR_PLAN_HELPER_LIVE_DEMOTION_SLICE_V1"
LIVE_TASK_MUST_DECLARE_V1 = "WESLR_RUNTIME_CHANGE live behavior"
FUTURE_LIVE_TEST_FILE_V1 = "weslr/tests/test_plan_helper_live_demotion_slice_v1.py"
OPTIONAL_FUTURE_HELPER_FILE_V1 = "weslr/plan_helper_live_demotion_slice.py"
ALIGNMENT_LAYER_V1 = "WESLR_RUNTIME_CHANGE_prelive_helper_test_source_only"

EXCLUDED_BRANCHES_V1 = (
    "chat_responder_lunch_helper",
    "chat_responder_workout_helper",
    "chat_responder_email_helper",
    "chat_responder_code_bug_helper",
    "chat_responder_wife_partner_interpersonal_helper",
    "chat_responder_low_focus_fallback",
    "chat_responder_vague_fallback",
    "chat_responder_model_unavailable_fallback",
    "chat_responder_model_rescue_path",
    "chat_responder_model_backed_response_path",
    "chat_responder_meaning_vector_write_capable_path",
    "chat_responder_memory_capture_relationship_capture_paths",
    "limited_frontier_identity_self_consciousness_system_benchmark_responses",
    "limited_ordinary_task_renderer_except_non_live_reference",
    "state_grounded_self_system_memory_answers",
    "official_or_benchmark_boundary_surfaces",
    "protected_prompt_solution_key_boundaries",
    "evidence_bridge_search_pubmed_paths",
    "deterministic_write_capable_handlers",
    "deterministic_external_search_handlers",
    "staging_arbiter_raw_message_logging",
    "status_command_surfaces",
    "blocked_write_guidance",
)

FORBIDDEN_KEYS_V1 = frozenset({
    "raw_text",
    "normalized_text",
    "tokens",
    "final_answer",
    "response_text",
    "raw_prompt",
    "safe_prompt",
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
    "truth_write",
    "truth_writes",
    "registry_write",
    "registry_writes",
})

TRUE_FORBIDDEN_FLAGS_V1 = frozenset({
    "implementation_allowed_now",
    "chat_responder_edit_allowed_now",
    "live_weslr_behavior_changed",
    "safe_to_replace_live",
    "runtime_wiring",
    "live_runtime_output",
    "model_calls",
    "advisor_calls",
    "web_search",
    "search_calls",
    "solver_execution",
    "answer_selection_arbitration",
    "memory_writes",
    "raw_text_stored",
    "weslr_runtime_state_created",
    "weslr_state_created",
    "persistence",
    "writes_performed",
    "source_registry_write",
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
    "broad_route_drift": ("broad router", "all chat_responder branches", "replace all helpers"),
}

_PRIVATE_LIKE_TOKEN_RE_V1 = re.compile(r"\b(?=[A-Za-z0-9_-]{14,}\b)(?=.*[A-Za-z])(?=.*\d)(?=.*-)[A-Za-z0-9_-]+\b")
_URL_RE_V1 = re.compile(r"(?i)\b(?:https?://|www\.)\S+")

_SAFE_MARKER_PATH_SEGMENTS_V1 = frozenset({
    "excluded_branches",
    "future_tests_required",
    "target_scope",
    "owner_approval_gate",
    "blocked_surfaces",
    "future_live_implementation_prompt_must_include",
})


def to_plan_helper_demotion_prelive_plan_json_safe_v1(obj: Any) -> Any:
    """Return a deep JSON-safe copy. This is not a sanitizer and performs no writes."""
    value = copy.deepcopy(obj)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value):
        return to_plan_helper_demotion_prelive_plan_json_safe_v1(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(k): to_plan_helper_demotion_prelive_plan_json_safe_v1(v)
            for k, v in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple, set)):
        return [to_plan_helper_demotion_prelive_plan_json_safe_v1(v) for v in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return to_plan_helper_demotion_prelive_plan_json_safe_v1(value.to_dict())
    if hasattr(value, "__dict__"):
        return to_plan_helper_demotion_prelive_plan_json_safe_v1(vars(value))
    return repr(value)


def _walk(obj: Any, path: str = "") -> Iterable[tuple[str, Any]]:
    yield path, obj
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            child = f"{path}.{key}" if path else str(key)
            yield from _walk(value, child)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from _walk(value, f"{path}[{index}]")


def _path_has_safe_marker_segment(path: str) -> bool:
    return any(segment in path for segment in _SAFE_MARKER_PATH_SEGMENTS_V1)


def _error(category: str, path: str, detail: str) -> Dict[str, str]:
    return {"category": category, "path": path, "detail": detail}


def _warning(category: str, path: str, detail: str) -> Dict[str, str]:
    return {"category": category, "path": path, "detail": detail}


def _future_diff_plan_v1() -> List[Dict[str, Any]]:
    return [
        {
            "step": 1,
            "label": "allowed_runtime_boundary",
            "only_allowed_runtime_file": TARGET_FILE_V1,
            "only_allowed_branch": TARGET_BRANCH_V1,
            "approx_allowed_line_range": "1787-1792",
            "allowed_test_file_pattern": FUTURE_LIVE_TEST_FILE_V1,
            "allowed_optional_helper_file_if_needed": OPTIONAL_FUTURE_HELPER_FILE_V1,
            "implementation_allowed_now": False,
        },
        {
            "step": 2,
            "label": "add_disabled_feature_flag_inside_plan_branch_boundary",
            "feature_flag": FEATURE_FLAG_V1,
            "feature_flag_default": False,
            "feature_flag_default_may_change_only_with_explicit_owner_approval": True,
            "implementation_allowed_now": False,
        },
        {
            "step": 3,
            "label": "exact_plan_trigger_only",
            "target_branch": TARGET_BRANCH_V1,
            "one_branch_only": True,
            "allowed_trigger_scope": "existing plan branch trigger only",
            "implementation_allowed_now": False,
        },
        {
            "step": 4,
            "label": "call_existing_unified_response_formation_substrate_only",
            "selected_candidate_family": "ordinary_task_plan",
            "no_new_router": True,
            "no_model_search_advisor_code": True,
            "implementation_allowed_now": False,
        },
        {
            "step": 5,
            "label": "preserve_old_canned_plan_fallback",
            "old_canned_path_shadowed": TARGET_BRANCH_V1,
            "fallback_required": True,
            "fallback_when_feature_flag_disabled": True,
            "fallback_when_formation_fails": True,
            "implementation_allowed_now": False,
        },
        {
            "step": 6,
            "label": "attach_safe_metadata_contract",
            "metadata_contract": {
                "old_canned_path_shadowed": TARGET_BRANCH_V1,
                "selected_candidate_family": "ordinary_task_plan",
                "fallback_available": True,
                "owner_approval_granted": False,
                "metadata_is_owner_approval": False,
                "canned_response_replaced": False,
            },
            "implementation_allowed_now": False,
        },
        {
            "step": 7,
            "label": "blocked_future_diff_surfaces",
            "no_other_chat_responder_branches": True,
            "no_main_py": True,
            "no_staging_server": True,
            "no_voice_ui_persistence_files": True,
            "no_model_search_advisor_code": True,
            "no_memory_truth_provenance_registry_writes": True,
            "no_status_guardrail_self_identity_evidence_branches": True,
            "implementation_allowed_now": False,
        },
        {
            "step": 8,
            "label": "add_tests_before_or_alongside_future_code",
            "allowed_test_file_pattern": FUTURE_LIVE_TEST_FILE_V1,
            "implementation_allowed_now": False,
        },
        {
            "step": 9,
            "label": "document_exact_rollback_before_edit",
            "rollback_required": True,
            "implementation_allowed_now": False,
        },
    ]

def _future_tests_required_v1() -> List[str]:
    return [
        "feature flag default false",
        "feature flag disabled keeps old canned plan fallback",
        "feature flag enabled affects plan branch only",
        "exact plan trigger only",
        "non-plan lunch helper unchanged",
        "non-plan workout helper unchanged",
        "non-plan email helper unchanged",
        "non-plan code bug helper unchanged",
        "guardrails unchanged",
        "self identity protected official boundary surfaces unchanged",
        "evidence search unchanged",
        "memory write paths unchanged",
        "no memory writes",
        "no model advisor search calls",
        "no model calls",
        "no advisor calls",
        "no web search calls",
        "no solver execution",
        "no answer selection arbitration",
        "no .weslr state creation",
        "no raw private text storage",
        "no broad route replacement",
        "no unrelated files changed",
        "fallback path used if formation fails",
        "old canned behavior still available by direct fallback assertion",
        "metadata includes old_canned_path_shadowed",
        "metadata includes selected_candidate_family ordinary_task_plan or clarification",
        "rollback path documented",
        "release gate and release check pass",
    ]

def build_plan_helper_demotion_prelive_plan_v1() -> Dict[str, Any]:
    """Build an in-memory pre-live plan object for future plan-helper demotion review."""
    target_scope = {
        "target_file": TARGET_FILE_V1,
        "target_branch": TARGET_BRANCH_V1,
        "approx_line_range": "1787-1792",
        "legacy_surface": "chat_responder_topic_helper_ordinary",
        "one_branch_only": True,
        "non_plan_branches_unchanged": True,
        "guardrails_unchanged": True,
        "self_identity_protected_official_boundaries_unchanged": True,
        "evidence_search_paths_unchanged": True,
        "memory_write_paths_unchanged": True,
        "blocked_surfaces": list(EXCLUDED_BRANCHES_V1),
    }
    rollback_plan = [
        "git rev-parse HEAD",
        "git diff --stat",
        "git diff",
        f"disable {FEATURE_FLAG_V1}",
        "git revert <live-slice-commit>",
        "restore old chat_responder_plan_helper branch from previous commit",
        f"python -m pytest -q {FUTURE_LIVE_TEST_FILE_V1}",
        "python3 weslr/tests/release_gate_v1.py",
        "bash scripts/weslr_release_check.sh",
    ]
    smoke_tests = [
        "manual chat smoke: plan prompt with flag disabled returns legacy fallback path",
        "manual chat smoke: non-plan lunch/workout/email/code prompts unchanged",
        "manual chat smoke: protected and status boundary prompts unchanged",
        "manual metadata smoke: no model/search/advisor/write/.weslr flags set",
    ]
    owner_gate = [
        f"exact owner approval marker required: {REQUIRED_OWNER_APPROVAL_MARKER_V1}",
        f"exact live implementation task name required: {REQUIRED_LIVE_TASK_NAME_V1}",
        f"future task declares {LIVE_TASK_MUST_DECLARE_V1}",
        f"target branch remains exactly {TARGET_BRANCH_V1}",
        f"target file remains exactly {TARGET_FILE_V1}",
        "no unrelated files changed",
        "rollback commands included before edit",
        "tests before or alongside implementation",
        "fallback preserved",
        "feature flag default false unless owner explicitly approves enabling",
        "no model advisor search calls",
        "no model calls",
        "no advisor calls",
        "no web search calls",
        "no memory writes",
        "no .weslr runtime state",
        "no raw private text storage",
        "no solver execution",
        "no answer-selection arbitration",
        "no broad runtime replacement",
        "release gate and release check pass",
        "release gate required",
        "release check required",
        "manual smoke tests are defined and run",
        "manual smoke tests required",
    ]
    implementation_approval_packet = {
        "approval_packet_type": "plan_helper_live_demotion_approval_packet_v1",
        "approval_status": "not_requested",
        "owner_approval_granted": False,
        "required_owner_phrase": REQUIRED_OWNER_APPROVAL_MARKER_V1,
        "approved_target_branch": TARGET_BRANCH_V1,
        "approved_target_file": TARGET_FILE_V1,
        "approved_scope": "one_branch_only",
        "feature_flag_default": False,
        "fallback_required": True,
        "rollback_required": True,
        "metadata_is_approval": False,
    }
    future_live_implementation_prompt_must_include = [
        "exact owner approval phrase",
        LIVE_TASK_MUST_DECLARE_V1,
        f"target branch {TARGET_BRANCH_V1}",
        "feature flag default false unless explicitly approved",
        "fallback preserved",
        "rollback commands",
        "tests before/alongside implementation",
        "no unrelated files",
        "no broad runtime replacement",
        "no model/search/advisor/memory/.weslr/raw-text paths",
    ]
    plan: Dict[str, Any] = {
        "plan_type": PLAN_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "target_branch": TARGET_BRANCH_V1,
        "target_file": TARGET_FILE_V1,
        "approx_line_range": "1787-1792",
        "legacy_surface": "chat_responder_topic_helper_ordinary",
        "selected_shadow_family": "ordinary_task_plan",
        "quality_label": "strongest_first_design_candidate",
        "alignment_layer": ALIGNMENT_LAYER_V1,
        "live_weslr_behavior_changed": False,
        "metadata_is_owner_approval": False,
        "owner_approval_granted": False,
        "owner_approval_required_before_implementation": True,
        "required_owner_approval_marker": REQUIRED_OWNER_APPROVAL_MARKER_V1,
        "required_live_task_name": REQUIRED_LIVE_TASK_NAME_V1,
        "live_task_must_declare": LIVE_TASK_MUST_DECLARE_V1,
        "implementation_allowed_now": False,
        "chat_responder_edit_allowed_now": False,
        "feature_flag": FEATURE_FLAG_V1,
        "feature_flag_default": False,
        "fallback_required": True,
        "rollback_required": True,
        "safe_to_replace_live": False,
        "runtime_wiring": False,
        "live_runtime_output": False,
        "model_calls": False,
        "advisor_calls": False,
        "web_search": False,
        "solver_execution": False,
        "answer_selection_arbitration": False,
        "memory_writes": False,
        "raw_text_stored": False,
        "weslr_runtime_state_created": False,
        "live_chat_responder_called": False,
        "target_scope": target_scope,
        "excluded_branches": list(EXCLUDED_BRANCHES_V1),
        "future_diff_plan": _future_diff_plan_v1(),
        "future_tests_required": _future_tests_required_v1(),
        "rollback_plan": rollback_plan,
        "smoke_tests": smoke_tests,
        "owner_approval_gate": owner_gate,
        "implementation_approval_packet": implementation_approval_packet,
        "future_live_implementation_prompt_must_include": future_live_implementation_prompt_must_include,
    }
    plan["validation"] = validate_plan_helper_demotion_prelive_plan_v1(plan)
    return plan


def validate_plan_helper_demotion_prelive_plan_v1(plan: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate pre-live plan metadata and reject live-behavior drift."""
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    if not isinstance(plan, Mapping):
        return {"valid": False, "errors": [_error("not_mapping", "", "plan must be a mapping")], "warnings": []}

    required_equals = {
        "plan_type": PLAN_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "target_branch": TARGET_BRANCH_V1,
        "target_file": TARGET_FILE_V1,
        "selected_shadow_family": "ordinary_task_plan",
        "quality_label": "strongest_first_design_candidate",
        "alignment_layer": ALIGNMENT_LAYER_V1,
        "feature_flag": FEATURE_FLAG_V1,
        "required_owner_approval_marker": REQUIRED_OWNER_APPROVAL_MARKER_V1,
        "required_live_task_name": REQUIRED_LIVE_TASK_NAME_V1,
        "live_task_must_declare": LIVE_TASK_MUST_DECLARE_V1,
    }
    for key, expected in required_equals.items():
        if plan.get(key) != expected:
            errors.append(_error("unexpected_value", key, f"expected {expected!r}"))

    false_required = [
        "implementation_allowed_now",
        "chat_responder_edit_allowed_now",
        "live_weslr_behavior_changed",
        "metadata_is_owner_approval",
        "owner_approval_granted",
        "safe_to_replace_live",
        "runtime_wiring",
        "live_runtime_output",
        "model_calls",
        "advisor_calls",
        "web_search",
        "solver_execution",
        "answer_selection_arbitration",
        "memory_writes",
        "raw_text_stored",
        "weslr_runtime_state_created",
    ]
    for key in false_required:
        if plan.get(key) is not False:
            errors.append(_error("flag_must_be_false", key, f"{key} must be false"))

    true_required = [
        "owner_approval_required_before_implementation",
        "fallback_required",
        "rollback_required",
    ]
    for key in true_required:
        if plan.get(key) is not True:
            errors.append(_error("flag_must_be_true", key, f"{key} must be true"))

    if plan.get("feature_flag_default") is not False:
        errors.append(_error("feature_flag_default_must_be_false", "feature_flag_default", "feature flag must default false"))

    owner_gate_text = "\n".join(str(item).lower() for item in plan.get("owner_approval_gate", []))
    required_gate_clauses = {
        "owner_approval_marker": REQUIRED_OWNER_APPROVAL_MARKER_V1.lower(),
        "live_task_name": REQUIRED_LIVE_TASK_NAME_V1.lower(),
        "live_task_declaration": LIVE_TASK_MUST_DECLARE_V1.lower(),
        "target_branch": TARGET_BRANCH_V1.lower(),
        "target_file": TARGET_FILE_V1.lower(),
        "no_unrelated_files": "no unrelated files changed",
        "rollback_before_edit": "rollback commands included before edit",
        "tests_before_or_alongside": "tests before or alongside implementation",
        "fallback_preserved": "fallback preserved",
        "feature_flag_default_false": "feature flag default false",
        "no_model_calls": "no model calls",
        "no_advisor_calls": "no advisor calls",
        "no_web_search_calls": "no web search calls",
        "no_memory_writes": "no memory writes",
        "no_weslr_state": "no .weslr runtime state",
        "no_raw_private_text": "no raw private text storage",
        "no_solver_execution": "no solver execution",
        "no_answer_selection_arbitration": "no answer-selection arbitration",
        "no_broad_runtime_replacement": "no broad runtime replacement",
        "release_gate_required": "release gate required",
        "release_check_required": "release check required",
        "manual_smoke_tests_required": "manual smoke tests required",
    }
    for category, clause in required_gate_clauses.items():
        if clause not in owner_gate_text:
            errors.append(_error("owner_approval_gate_clause_missing", f"owner_approval_gate.{category}", clause))

    rollback_items = [str(item).lower() for item in plan.get("rollback_plan", [])]
    rollback_text = "\n".join(rollback_items)
    required_rollback_clauses = {
        "save_current_commit": "git rev-parse head",
        "diff_stat": "git diff --stat",
        "diff_full": "git diff",
        "feature_flag_off": f"disable {FEATURE_FLAG_V1}".lower(),
        "git_revert": "git revert <live-slice-commit>",
        "focused_tests": "python -m pytest -q",
        "release_gate": "python3 weslr/tests/release_gate_v1.py",
        "release_check": "bash scripts/weslr_release_check.sh",
    }
    for category, clause in required_rollback_clauses.items():
        if category == "diff_full":
            present = clause in rollback_items
        else:
            present = clause in rollback_text
        if not present:
            errors.append(_error("rollback_clause_missing", f"rollback_plan.{category}", clause))

    future_diff = plan.get("future_diff_plan")
    future_diff_text = repr(future_diff).lower()
    required_future_diff_clauses = {
        "target_file": TARGET_FILE_V1.lower(),
        "target_branch": TARGET_BRANCH_V1.lower(),
        "line_range": "1787-1792",
        "test_file": FUTURE_LIVE_TEST_FILE_V1.lower(),
        "optional_helper": OPTIONAL_FUTURE_HELPER_FILE_V1.lower(),
        "no_main_py": "no_main_py",
        "no_staging_server": "no_staging_server",
        "no_voice_ui_persistence": "no_voice_ui_persistence_files",
        "no_model_search_advisor": "no_model_search_advisor_code",
        "no_memory_registry": "no_memory_truth_provenance_registry_writes",
        "no_status_guardrail_self_identity_evidence": "no_status_guardrail_self_identity_evidence_branches",
    }
    for category, clause in required_future_diff_clauses.items():
        if clause not in future_diff_text:
            errors.append(_error("future_diff_boundary_missing", f"future_diff_plan.{category}", clause))
    forbidden_future_diff_markers = (
        "lunch", "workout", "email", "code bug", "code/bug", "wife", "partner",
        "low-focus", "low_focus", "vague fallback", "model path", "identity/self",
        "evidence/search", "deterministic write", "staging raw log", "main.py",
        "deploy/staging", "voice file", "ui/frontend", "persistence file", "memory write",
        "source registry write", "broad router", "all chat_responder branches",
    )
    for marker in forbidden_future_diff_markers:
        if marker in future_diff_text:
            errors.append(_error("future_diff_forbidden_surface", "future_diff_plan", marker))

    tests_text = "\n".join(str(item).lower() for item in plan.get("future_tests_required", []))
    required_future_tests = {
        "feature_flag_default_false": "feature flag default false",
        "flag_disabled_old_fallback": "feature flag disabled keeps old canned plan fallback",
        "flag_enabled_plan_only": "feature flag enabled affects plan branch only",
        "exact_plan_trigger_only": "exact plan trigger only",
        "no_broad_route_replacement": "no broad route replacement",
        "no_unrelated_files": "no unrelated files changed",
        "no_solver_execution": "no solver execution",
        "no_answer_selection_arbitration": "no answer selection arbitration",
        "fallback_when_fails": "fallback path used if formation fails",
        "old_canned_direct_fallback": "old canned behavior still available by direct fallback assertion",
    }
    for category, clause in required_future_tests.items():
        if clause not in tests_text:
            errors.append(_error("future_test_requirement_missing", f"future_tests_required.{category}", clause))

    packet = plan.get("implementation_approval_packet")
    if not isinstance(packet, Mapping):
        errors.append(_error("implementation_approval_packet_missing", "implementation_approval_packet", "approval packet must be present"))
    else:
        packet_required_equals = {
            "approval_packet_type": "plan_helper_live_demotion_approval_packet_v1",
            "approval_status": "not_requested",
            "required_owner_phrase": REQUIRED_OWNER_APPROVAL_MARKER_V1,
            "approved_target_branch": TARGET_BRANCH_V1,
            "approved_target_file": TARGET_FILE_V1,
            "approved_scope": "one_branch_only",
        }
        for key, expected in packet_required_equals.items():
            if packet.get(key) != expected:
                errors.append(_error("approval_packet_value_drift", f"implementation_approval_packet.{key}", f"expected {expected!r}"))
        packet_false_required = ["owner_approval_granted", "metadata_is_approval", "feature_flag_default"]
        for key in packet_false_required:
            if packet.get(key) is not False:
                errors.append(_error("approval_packet_flag_must_be_false", f"implementation_approval_packet.{key}", f"{key} must be false"))
        for key in ["fallback_required", "rollback_required"]:
            if packet.get(key) is not True:
                errors.append(_error("approval_packet_flag_must_be_true", f"implementation_approval_packet.{key}", f"{key} must be true"))

    prompt_text = "\n".join(str(item).lower() for item in plan.get("future_live_implementation_prompt_must_include", []))
    required_prompt_clauses = [
        "exact owner approval phrase",
        LIVE_TASK_MUST_DECLARE_V1.lower(),
        TARGET_BRANCH_V1.lower(),
        "feature flag default false",
        "fallback preserved",
        "rollback commands",
        "tests before/alongside implementation",
        "no unrelated files",
        "no broad runtime replacement",
        "no model/search/advisor/memory/.weslr/raw-text paths",
    ]
    for clause in required_prompt_clauses:
        if clause not in prompt_text:
            errors.append(_error("future_prompt_requirement_missing", "future_live_implementation_prompt_must_include", clause))

    target_scope = plan.get("target_scope")
    if not isinstance(target_scope, Mapping):
        errors.append(_error("target_scope_missing", "target_scope", "target scope must be a mapping"))
    else:
        if target_scope.get("target_branch") != TARGET_BRANCH_V1:
            errors.append(_error("target_scope_branch_drift", "target_scope.target_branch", "target scope must target plan helper only"))
        if target_scope.get("target_file") != TARGET_FILE_V1:
            errors.append(_error("target_scope_file_drift", "target_scope.target_file", "target scope file must be chat_responder.py"))
        if target_scope.get("one_branch_only") is not True:
            errors.append(_error("target_scope_not_one_branch", "target_scope.one_branch_only", "target scope must be one branch only"))
        target_repr = repr(target_scope)
        for branch in EXCLUDED_BRANCHES_V1:
            if branch == TARGET_BRANCH_V1:
                continue
            if target_scope.get("target_branch") == branch:
                errors.append(_error("excluded_branch_targeted", "target_scope.target_branch", branch))
            if branch in target_repr and branch not in target_scope.get("blocked_surfaces", []):
                errors.append(_error("excluded_branch_in_target_scope", "target_scope", branch))

    excluded = plan.get("excluded_branches")
    if not isinstance(excluded, list) or len(set(excluded)) < 10:
        errors.append(_error("excluded_branches_missing", "excluded_branches", "excluded branches must be explicitly listed"))
    elif TARGET_BRANCH_V1 in excluded:
        errors.append(_error("target_branch_excluded", "excluded_branches", "target branch must not be excluded"))

    for path, value in _walk(plan):
        if path.endswith(".validation") or ".validation." in path:
            continue
        key = path.split(".")[-1]
        key = re.sub(r"\[\d+\]$", "", key)
        if key in FORBIDDEN_KEYS_V1:
            errors.append(_error("forbidden_key", path, key))
        if key in TRUE_FORBIDDEN_FLAGS_V1 and value is True:
            errors.append(_error("forbidden_true_flag", path, key))
        if isinstance(value, str):
            if _URL_RE_V1.search(value):
                errors.append(_error("url_not_allowed", path, "source urls are not allowed in plan metadata"))
            if _PRIVATE_LIKE_TOKEN_RE_V1.search(value):
                errors.append(_error("private_like_token", path, "private-like token detected"))
            if not _path_has_safe_marker_segment(path):
                lowered = value.lower()
                for category, markers in FORBIDDEN_TEXT_MARKERS_V1.items():
                    if any(marker in lowered for marker in markers):
                        errors.append(_error(category, path, "forbidden text marker"))

    if not plan.get("future_diff_plan"):
        warnings.append(_warning("future_diff_plan_missing", "future_diff_plan", "future diff plan missing"))
    if not plan.get("future_tests_required"):
        warnings.append(_warning("future_tests_missing", "future_tests_required", "future tests missing"))
    if not plan.get("rollback_plan"):
        warnings.append(_warning("rollback_plan_missing", "rollback_plan", "rollback plan missing"))
    if not plan.get("smoke_tests"):
        warnings.append(_warning("smoke_tests_missing", "smoke_tests", "smoke tests missing"))
    if not plan.get("owner_approval_gate"):
        warnings.append(_warning("owner_approval_gate_missing", "owner_approval_gate", "owner approval gate missing"))
    if not plan.get("selected_shadow_family"):
        warnings.append(_warning("selected_shadow_family_missing", "selected_shadow_family", "selected shadow family missing"))
    if not plan.get("quality_label"):
        warnings.append(_warning("quality_label_missing", "quality_label", "quality label missing"))

    tests_text = "\n".join(str(item).lower() for item in plan.get("future_tests_required", []))
    if "non-plan" not in tests_text:
        warnings.append(_warning("non_plan_unchanged_tests_missing", "future_tests_required", "non-plan unchanged tests missing"))
    if "release gate" not in tests_text or "release check" not in tests_text:
        warnings.append(_warning("release_gate_check_missing", "future_tests_required", "release gate/check requirement missing"))

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def summarize_plan_helper_demotion_prelive_plan_v1(plan: Mapping[str, Any]) -> Dict[str, Any]:
    """Return count/status/label-only summary metadata for safe inspection."""
    return {
        "summary_type": SUMMARY_TYPE_V1,
        "plan_type": plan.get("plan_type"),
        "target_branch": plan.get("target_branch"),
        "target_file": plan.get("target_file"),
        "implementation_allowed_now": bool(plan.get("implementation_allowed_now")),
        "chat_responder_edit_allowed_now": bool(plan.get("chat_responder_edit_allowed_now")),
        "live_weslr_behavior_changed": bool(plan.get("live_weslr_behavior_changed")),
        "owner_approval_required": bool(plan.get("owner_approval_required_before_implementation")),
        "owner_approval_granted": bool(plan.get("owner_approval_granted")),
        "metadata_is_owner_approval": bool(plan.get("metadata_is_owner_approval")),
        "required_owner_approval_marker_present": plan.get("required_owner_approval_marker") == REQUIRED_OWNER_APPROVAL_MARKER_V1,
        "feature_flag": plan.get("feature_flag"),
        "feature_flag_default": bool(plan.get("feature_flag_default")),
        "fallback_required": bool(plan.get("fallback_required")),
        "rollback_required": bool(plan.get("rollback_required")),
        "rollback_command_count": len(plan.get("rollback_plan") or []),
        "future_diff_step_count": len(plan.get("future_diff_plan") or []),
        "future_test_count": len(plan.get("future_tests_required") or []),
        "excluded_branch_count": len(plan.get("excluded_branches") or []),
        "exact_diff_boundary_present": any(
            isinstance(item, Mapping)
            and item.get("only_allowed_runtime_file") == TARGET_FILE_V1
            and item.get("only_allowed_branch") == TARGET_BRANCH_V1
            and item.get("approx_allowed_line_range") == "1787-1792"
            for item in (plan.get("future_diff_plan") or [])
        ),
        "safe_to_replace_live": bool(plan.get("safe_to_replace_live")),
        "runtime_wiring": bool(plan.get("runtime_wiring")),
        "live_runtime_output": bool(plan.get("live_runtime_output")),
        "validation_valid": bool((plan.get("validation") or {}).get("valid")),
    }


def render_plan_helper_demotion_prelive_plan_markdown_v1(plan: Mapping[str, Any]) -> str:
    """Render safe count/status/label-only Markdown for inspection."""
    summary = summarize_plan_helper_demotion_prelive_plan_v1(plan)
    lines = [
        "# Plan Helper Demotion Pre-live Plan V1",
        "",
        f"- plan_type: {summary['plan_type']}",
        f"- target_branch: {summary['target_branch']}",
        f"- target_file: {summary['target_file']}",
        f"- implementation_allowed_now: {summary['implementation_allowed_now']}",
        f"- chat_responder_edit_allowed_now: {summary['chat_responder_edit_allowed_now']}",
        f"- live_weslr_behavior_changed: {summary['live_weslr_behavior_changed']}",
        f"- owner_approval_required: {summary['owner_approval_required']}",
        f"- owner_approval_granted: {summary['owner_approval_granted']}",
        f"- metadata_is_owner_approval: {summary['metadata_is_owner_approval']}",
        f"- required_owner_approval_marker_present: {summary['required_owner_approval_marker_present']}",
        f"- feature_flag: {summary['feature_flag']}",
        f"- feature_flag_default: {summary['feature_flag_default']}",
        f"- fallback_required: {summary['fallback_required']}",
        f"- rollback_required: {summary['rollback_required']}",
        f"- rollback_command_count: {summary['rollback_command_count']}",
        f"- future_diff_step_count: {summary['future_diff_step_count']}",
        f"- future_test_count: {summary['future_test_count']}",
        f"- excluded_branch_count: {summary['excluded_branch_count']}",
        f"- exact_diff_boundary_present: {summary['exact_diff_boundary_present']}",
        f"- safe_to_replace_live: {summary['safe_to_replace_live']}",
        f"- runtime_wiring: {summary['runtime_wiring']}",
        f"- live_runtime_output: {summary['live_runtime_output']}",
        f"- validation_valid: {summary['validation_valid']}",
    ]
    return "\n".join(lines)
