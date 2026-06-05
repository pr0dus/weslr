"""Metadata-only helpers for WESLR project-chat runtime dry-run consumption plans V1.

This module is intentionally pure, deterministic, synthetic/example-safe,
and fail-closed. It builds and validates metadata-only consumption plans that
say what a future runtime shell would be allowed to prepare next.

It does not perform file I/O, network I/O, shell execution, runtime wiring,
retrieval, model calls, tool execution, external actions, persistence, or
final answer generation.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from weslr.project_chat_answer_plan_metadata_helpers import (
    DENIED_AUTHORITY_FIELDS_V1 as ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1,
    build_project_chat_answer_plan_v1,
    validate_project_chat_answer_plan_v1,
)
from weslr.project_chat_runtime_dry_run_metadata import (
    build_project_chat_runtime_dry_run_v1,
    validate_project_chat_runtime_dry_run_v1,
)

HELPER_TYPE_V1 = "weslr_project_chat_runtime_dry_run_consumption_plan_v1"
SCHEMA_VERSION_V1 = "project_chat_runtime_dry_run_consumption_plan_v1"

CONSUMPTION_ACTIONS_V1 = (
    "remain_dry_run_only",
    "block_due_to_boundary",
    "ask_clarifying_question_metadata_only",
    "request_user_approval_metadata_only",
    "request_operator_review_metadata_only",
    "prepare_answer_plan_metadata_only",
    "prepare_retrieval_request_metadata_only",
    "prepare_tool_lane_candidate_metadata_only",
    "prepare_persistence_candidate_metadata_only",
    "blocked_private_mechanism_boundary",
    "blocked_runtime_wiring_boundary",
    "blocked_final_answer_boundary",
)

CONSUMPTION_STATUSES_V1 = (
    "consumption_plan_valid_metadata_only",
    "clarification_required",
    "approval_required",
    "operator_review_required",
    "blocked",
    "invalid",
)

_DEFAULT_FALSE_DENIED_AUTHORITY = {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1}
_BLOCKED_ACTIONS = {
    "block_due_to_boundary",
    "blocked_private_mechanism_boundary",
    "blocked_runtime_wiring_boundary",
    "blocked_final_answer_boundary",
}
_META_ONLY_ACTIONS = {
    "remain_dry_run_only",
    "ask_clarifying_question_metadata_only",
    "request_user_approval_metadata_only",
    "request_operator_review_metadata_only",
    "prepare_answer_plan_metadata_only",
    "prepare_retrieval_request_metadata_only",
    "prepare_tool_lane_candidate_metadata_only",
    "prepare_persistence_candidate_metadata_only",
}


def allowed_project_chat_dry_run_consumption_actions_v1() -> tuple[str, ...]:
    return CONSUMPTION_ACTIONS_V1



def allowed_project_chat_dry_run_consumption_statuses_v1() -> tuple[str, ...]:
    return CONSUMPTION_STATUSES_V1



def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}



def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())



def _safe_bool(value: Any) -> bool:
    return bool(value) is True



def _safe_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        items = [value]
    elif isinstance(value, Mapping):
        items = list(value.keys())
    else:
        try:
            items = list(value)
        except TypeError:
            items = [value]
    return [_safe_str(item) for item in items if _safe_str(item)]



def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered



def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=lambda item: _safe_str(item))]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _safe_str(value)



def _stable_digest(payload: Mapping[str, Any]) -> str:
    safe_payload = _json_safe(payload)
    blob = json.dumps(safe_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()



def _normalize_refs(value: Any) -> list[str]:
    return _dedupe(_safe_list(value))



def _normalize_flags(value: Any) -> list[str]:
    return _dedupe(_safe_list(value))



def _normalize_denied_authority(value: Any) -> dict[str, bool]:
    payload = dict(_DEFAULT_FALSE_DENIED_AUTHORITY)
    raw = _as_mapping(value)
    for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1:
        payload[field] = _safe_bool(raw.get(field, False))
    return payload



def _coalesce_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = {}
    if isinstance(payload, Mapping):
        data.update(payload)
    elif payload is not None:
        data["payload"] = payload
    data.update(overrides)
    return data



def _default_user_visible_status(consumption_plan: Mapping[str, Any]) -> str:
    status = _safe_str(consumption_plan.get("consumption_status"))
    action = _safe_str(consumption_plan.get("consumption_action"))
    if status == "blocked" or action in _BLOCKED_ACTIONS:
        return "dry-run consumption blocked"
    if status == "operator_review_required" or action == "request_operator_review_metadata_only":
        return "operator review required"
    if status == "approval_required" or action == "request_user_approval_metadata_only":
        return "approval required"
    if status == "clarification_required" or action == "ask_clarifying_question_metadata_only":
        return "clarification needed"
    if action == "prepare_answer_plan_metadata_only":
        return "answer-plan metadata only"
    if action == "prepare_retrieval_request_metadata_only":
        return "retrieval request metadata only"
    if action == "prepare_tool_lane_candidate_metadata_only":
        return "tool-lane candidate metadata only"
    if action == "prepare_persistence_candidate_metadata_only":
        return "persistence candidate metadata only"
    return "dry-run consumption metadata only"



def _default_operator_visible_summary(consumption_plan: Mapping[str, Any]) -> str:
    dry_run_validation = _as_mapping(consumption_plan.get("dry_run_validation"))
    return (
        f"{_safe_str(consumption_plan.get('consumption_action'))} | "
        f"{_safe_str(consumption_plan.get('consumption_status'))} | "
        f"dry_run={_safe_str(dry_run_validation.get('dry_run_status'))} | "
        f"answer_plan={_safe_str(_as_mapping(consumption_plan.get('answer_plan_validation')).get('answer_status'))}"
    )



def _default_answer_plan_payload(consumption_plan: Mapping[str, Any]) -> dict[str, Any]:
    consumption_action = _safe_str(consumption_plan.get("consumption_action"))
    dry_run_validation = _as_mapping(consumption_plan.get("dry_run_validation"))
    dry_run = _as_mapping(consumption_plan.get("dry_run_metadata"))
    dry_run_decision = _safe_str(dry_run.get("dry_run_decision"))
    retrieval_need = _safe_str(dry_run.get("retrieval_need_class"))

    mode = "clarifying_question"
    scope = "current_message_only"
    status = "clarification_required"
    if consumption_action == "prepare_answer_plan_metadata_only" or dry_run_decision == "proceed_to_answer_plan_metadata":
        if retrieval_need in {"approved_evidence_packet", "approved_evidence", "approved"}:
            mode = "evidence_grounded_answer"
            scope = "approved_evidence_packet"
            status = "plan_valid_metadata_only"
        elif consumption_action == "prepare_tool_lane_candidate_metadata_only":
            mode = "tool_request_boundary_response"
            scope = "tool_lane_candidate_only"
            status = "plan_valid_metadata_only"
        elif consumption_action == "prepare_persistence_candidate_metadata_only":
            mode = "blocked_boundary_response"
            scope = "blocked_no_authority"
            status = "blocked"
        else:
            mode = "project_start_guidance"
            scope = "project_metadata_only"
            status = "plan_valid_metadata_only"
    elif consumption_action == "prepare_retrieval_request_metadata_only":
        mode = "surface_gap_review_summary"
        scope = "surface_gap_review_only"
        status = "plan_valid_metadata_only"
    elif consumption_action == "prepare_tool_lane_candidate_metadata_only":
        mode = "tool_request_boundary_response"
        scope = "tool_lane_candidate_only"
        status = "plan_valid_metadata_only"
    elif consumption_action == "prepare_persistence_candidate_metadata_only":
        mode = "blocked_boundary_response"
        scope = "blocked_no_authority"
        status = "blocked"
    elif dry_run_validation.get("dry_run_status") == "operator_review_required":
        mode = "operator_review_required_response"
        scope = "operator_review_required"
        status = "operator_review_required"
    return {
        "project_id": _safe_str(consumption_plan.get("project_id")),
        "owner_user_scope": _safe_str(consumption_plan.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(consumption_plan.get("tenant_account_scope")),
        "source_scope": _safe_str(consumption_plan.get("source_scope")),
        "user_intent_class": _safe_str(dry_run.get("user_intent_class")) or _safe_str(consumption_plan.get("source_scope")) or "project-chat",
        "answer_mode": mode,
        "allowed_answer_scope": scope,
        "answer_status": status,
        "evidence_packet_refs": _normalize_refs(dry_run.get("evidence_packet_refs")),
        "project_state_refs": _normalize_refs(dry_run.get("project_state_refs")),
        "memory_state_refs": _normalize_refs(dry_run.get("memory_state_refs")),
        "continuity_state_refs": _normalize_refs(dry_run.get("continuity_state_refs")),
        "gap_analysis_refs": _normalize_refs(dry_run.get("gap_analysis_refs")),
        "tool_lane_candidate_refs": _normalize_refs(dry_run.get("tool_lane_candidate_refs")) or _normalize_refs(consumption_plan.get("tool_lane_candidate_refs")),
        "operator_visibility_refs": _normalize_refs(consumption_plan.get("operator_visibility_refs")),
        "approval_refs": _normalize_refs(consumption_plan.get("approval_refs")),
        "user_visible_status": _safe_str(consumption_plan.get("user_visible_status")) or _default_user_visible_status(consumption_plan),
        "operator_visible_summary": _safe_str(consumption_plan.get("operator_visible_summary")) or "dry-run consumption answer-plan metadata",
        "denied_authority": _normalize_denied_authority(consumption_plan.get("denied_authority")),
    }



def _build_default_dry_run_payload(consumption_plan: Mapping[str, Any]) -> dict[str, Any]:
    action = _safe_str(consumption_plan.get("consumption_action"))
    status = _safe_str(consumption_plan.get("consumption_status"))
    dry_run_status = "dry_run_valid_metadata_only"
    dry_run_decision = "proceed_to_answer_plan_metadata"
    if action == "ask_clarifying_question_metadata_only" or status == "clarification_required":
        dry_run_status = "clarification_required"
        dry_run_decision = "ask_clarifying_question"
    elif action == "request_user_approval_metadata_only" or status == "approval_required":
        dry_run_status = "approval_required"
        dry_run_decision = "request_user_approval"
    elif action == "request_operator_review_metadata_only" or status == "operator_review_required":
        dry_run_status = "operator_review_required"
        dry_run_decision = "request_operator_review"
    elif action in _BLOCKED_ACTIONS or status == "blocked":
        dry_run_status = "blocked"
        dry_run_decision = "block_due_to_boundary"
    return {
        "project_id": _safe_str(consumption_plan.get("project_id")),
        "owner_user_scope": _safe_str(consumption_plan.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(consumption_plan.get("tenant_account_scope")),
        "source_scope": _safe_str(consumption_plan.get("source_scope")),
        "user_intent_class": _safe_str(consumption_plan.get("source_scope")) or "project-chat",
        "dry_run_status": dry_run_status,
        "dry_run_decision": dry_run_decision,
        "retrieval_need_class": "none",
        "user_visible_status": _default_user_visible_status(consumption_plan),
        "operator_visible_summary": "dry-run consumption metadata only",
        "denied_authority": dict(_DEFAULT_FALSE_DENIED_AUTHORITY),
    }



def _normalize_dry_run_metadata(value: Any, consumption_plan: Mapping[str, Any]) -> dict[str, Any]:
    raw = _as_mapping(value)
    if not raw:
        raw = _build_default_dry_run_payload(consumption_plan)
    candidate = build_project_chat_runtime_dry_run_v1(raw)
    validation = validate_project_chat_runtime_dry_run_v1(candidate)
    return {"dry_run": validation["dry_run"], "dry_run_validation": validation}



def _normalize_answer_plan_metadata(value: Any, consumption_plan: Mapping[str, Any]) -> dict[str, Any]:
    raw = _as_mapping(value)
    if not raw:
        raw = _default_answer_plan_payload(consumption_plan)
    candidate = build_project_chat_answer_plan_v1(raw)
    validation = validate_project_chat_answer_plan_v1(candidate)
    return {"answer_plan": validation["answer_plan"], "answer_plan_validation": validation}



def _build_default_consumption_status_and_action(dry_run_validation: Mapping[str, Any]) -> tuple[str, str, str]:
    dry_run = _as_mapping(dry_run_validation.get("dry_run"))
    decision = _safe_str(dry_run.get("dry_run_decision"))
    status = _safe_str(dry_run.get("dry_run_status"))
    if dry_run_validation.get("blocked"):
        return "blocked", "block_due_to_boundary", "block_due_to_boundary"
    if status == "clarification_required" or decision == "ask_clarifying_question":
        return "clarification_required", "ask_clarifying_question_metadata_only", "ask_clarifying_question_metadata_only"
    if status == "approval_required" or decision == "request_user_approval":
        return "approval_required", "request_user_approval_metadata_only", "request_user_approval_metadata_only"
    if status == "operator_review_required" or decision == "request_operator_review":
        return "operator_review_required", "request_operator_review_metadata_only", "request_operator_review_metadata_only"
    if status == "blocked" or decision.startswith("block_due_to_"):
        return "blocked", "block_due_to_boundary", "block_due_to_boundary"
    return "consumption_plan_valid_metadata_only", "prepare_answer_plan_metadata_only", "prepare_answer_plan_metadata_only"



def _stage_from_action(action: str) -> str:
    if action == "ask_clarifying_question_metadata_only":
        return "clarification_required"
    if action == "request_user_approval_metadata_only":
        return "approval_required"
    if action == "request_operator_review_metadata_only":
        return "operator_review_required"
    if action in _BLOCKED_ACTIONS:
        return "blocked"
    return "consumption_plan_valid_metadata_only"



def _classify_consumption_plan_candidate(candidate: Mapping[str, Any], blocked: bool) -> str:
    if blocked:
        return "blocked" if _safe_str(candidate.get("consumption_status")) != "invalid" else "invalid"
    action = _safe_str(candidate.get("consumption_action"))
    if action == "ask_clarifying_question_metadata_only":
        return "clarification_required"
    if action == "request_user_approval_metadata_only":
        return "approval_required"
    if action == "request_operator_review_metadata_only":
        return "operator_review_required"
    if action == "prepare_answer_plan_metadata_only":
        return "answer_plan_metadata_only"
    if action == "prepare_retrieval_request_metadata_only":
        return "retrieval_request_metadata_only"
    if action == "prepare_tool_lane_candidate_metadata_only":
        return "tool_lane_candidate_metadata_only"
    if action == "prepare_persistence_candidate_metadata_only":
        return "persistence_candidate_metadata_only"
    if action == "remain_dry_run_only":
        return "dry_run_only"
    return "blocked"



def _safe_stage_results(consumption_plan: Mapping[str, Any], dry_run_validation: Mapping[str, Any], answer_plan_validation: Mapping[str, Any]) -> list[dict[str, Any]]:
    if action == "ask_clarifying_question_metadata_only":
        return "clarification_required"
    if action == "request_user_approval_metadata_only":
        return "approval_required"
    if action == "request_operator_review_metadata_only":
        return "operator_review_required"
    if action in _BLOCKED_ACTIONS:
        return "blocked"
    return "consumption_plan_valid_metadata_only"



def _safe_stage_results(consumption_plan: Mapping[str, Any], dry_run_validation: Mapping[str, Any], answer_plan_validation: Mapping[str, Any]) -> list[dict[str, Any]]:
    dry_run = _as_mapping(dry_run_validation.get("dry_run"))
    action = _safe_str(consumption_plan.get("consumption_action"))
    status = _safe_str(consumption_plan.get("consumption_status"))
    return [
        {
            "stage": "dry_run_metadata_resolution",
            "status": _safe_str(dry_run_validation.get("dry_run_status")) or "invalid",
            "decision": _safe_str(dry_run_validation.get("dry_run_decision")) or "block_due_to_boundary",
            "dry_run_id": _safe_str(dry_run.get("dry_run_id")),
        },
        {
            "stage": "answer_plan_metadata_resolution",
            "status": "invalid" if answer_plan_validation.get("blocked") else "resolved",
            "decision": "block_due_to_boundary" if answer_plan_validation.get("blocked") else "prepare_answer_plan_metadata_only",
            "answer_plan_ref": _safe_str(consumption_plan.get("answer_plan_ref")),
        },
        {
            "stage": "consumption_action_resolution",
            "status": _stage_from_action(action),
            "decision": action or "block_due_to_boundary",
            "consumption_status": status,
        },
        {
            "stage": "final_answer_generation_boundary",
            "status": "blocked_boundary",
            "decision": "block_due_to_boundary",
            "note": "final answer generation remains blocked",
        },
    ]



def build_project_chat_dry_run_consumption_plan_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _coalesce_payload(payload, **overrides)

    consumption_plan = {
        "schema_version": _safe_str(data.get("schema_version")) or SCHEMA_VERSION_V1,
        "consumption_plan_id": _safe_str(data.get("consumption_plan_id")),
        "dry_run_ref": _safe_str(data.get("dry_run_ref")),
        "dry_run_metadata": _as_mapping(data.get("dry_run_metadata")),
        "project_id": _safe_str(data.get("project_id")),
        "owner_user_scope": _safe_str(data.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(data.get("tenant_account_scope")),
        "source_scope": _safe_str(data.get("source_scope")),
        "consumption_status": _safe_str(data.get("consumption_status")),
        "consumption_action": _safe_str(data.get("consumption_action")),
        "allowed_next_metadata_step": _safe_str(data.get("allowed_next_metadata_step")),
        "blocked_authority": _safe_str(data.get("blocked_authority")),
        "approval_refs": _normalize_refs(data.get("approval_refs")),
        "operator_visibility_refs": _normalize_refs(data.get("operator_visibility_refs")),
        "evidence_packet_refs": _normalize_refs(data.get("evidence_packet_refs")),
        "answer_plan_ref": _safe_str(data.get("answer_plan_ref")),
        "answer_plan_metadata": _as_mapping(data.get("answer_plan_metadata")),
        "tool_lane_candidate_refs": _normalize_refs(data.get("tool_lane_candidate_refs")),
        "persistence_candidate_refs": _normalize_refs(data.get("persistence_candidate_refs")),
        "uncertainty_flags": _normalize_flags(data.get("uncertainty_flags")),
        "stale_state_flags": _normalize_flags(data.get("stale_state_flags")),
        "contradiction_flags": _normalize_flags(data.get("contradiction_flags")),
        "missing_evidence_flags": _normalize_flags(data.get("missing_evidence_flags")),
        "privacy_flags": _normalize_flags(data.get("privacy_flags")),
        "limitations": _normalize_flags(data.get("limitations")),
        "user_visible_status": _safe_str(data.get("user_visible_status")),
        "operator_visible_summary": _safe_str(data.get("operator_visible_summary")),
        "denied_authority": _normalize_denied_authority(data.get("denied_authority")),
        "helper_type": HELPER_TYPE_V1,
        "raw_content_stored": False,
    }

    dry_run_payload = data.get("dry_run_metadata") if isinstance(data.get("dry_run_metadata"), Mapping) else data.get("dry_run_payload")
    dry_run_bundle = _normalize_dry_run_metadata(dry_run_payload, consumption_plan)
    consumption_plan["dry_run_metadata"] = dry_run_bundle["dry_run"]
    consumption_plan["dry_run_validation"] = dry_run_bundle["dry_run_validation"]

    if not consumption_plan["project_id"]:
        consumption_plan["project_id"] = _safe_str(consumption_plan["dry_run_metadata"].get("project_id"))
    if not consumption_plan["owner_user_scope"]:
        consumption_plan["owner_user_scope"] = _safe_str(consumption_plan["dry_run_metadata"].get("owner_user_scope"))
    if not consumption_plan["tenant_account_scope"]:
        consumption_plan["tenant_account_scope"] = _safe_str(consumption_plan["dry_run_metadata"].get("tenant_account_scope"))
    if not consumption_plan["source_scope"]:
        consumption_plan["source_scope"] = _safe_str(consumption_plan["dry_run_metadata"].get("source_scope"))

    if not consumption_plan["dry_run_ref"]:
        dry_run_id = _safe_str(consumption_plan["dry_run_metadata"].get("dry_run_id"))
        if dry_run_id:
            consumption_plan["dry_run_ref"] = f"dry-run-ref-{dry_run_id}"
    if not consumption_plan["answer_plan_ref"]:
        consumption_plan["answer_plan_ref"] = f"answer-plan-ref-{_safe_str(consumption_plan['dry_run_metadata'].get('answer_plan_ref')) or _safe_str(consumption_plan['dry_run_metadata'].get('dry_run_id'))}"

    if not consumption_plan["consumption_status"] or not consumption_plan["consumption_action"] or not consumption_plan["allowed_next_metadata_step"]:
        status, action, next_step = _build_default_consumption_status_and_action(consumption_plan["dry_run_validation"])
        if not consumption_plan["consumption_status"]:
            consumption_plan["consumption_status"] = status
        if not consumption_plan["consumption_action"]:
            consumption_plan["consumption_action"] = action
        if not consumption_plan["allowed_next_metadata_step"]:
            consumption_plan["allowed_next_metadata_step"] = next_step

    if not consumption_plan["consumption_plan_id"]:
        digest_source = {k: v for k, v in consumption_plan.items() if k not in {"consumption_plan_id", "operator_visible_summary", "user_visible_status"}}
        consumption_plan["consumption_plan_id"] = f"project-chat-runtime-dry-run-consumption-plan-{_stable_digest(digest_source)[:16]}"

    if not consumption_plan["answer_plan_metadata"]:
        answer_plan_bundle = _normalize_answer_plan_metadata(data.get("answer_plan_metadata") or data.get("answer_plan_payload"), consumption_plan)
    else:
        answer_plan_bundle = _normalize_answer_plan_metadata(consumption_plan["answer_plan_metadata"], consumption_plan)
    consumption_plan["answer_plan_metadata"] = answer_plan_bundle["answer_plan"]
    consumption_plan["answer_plan_validation"] = answer_plan_bundle["answer_plan_validation"]

    if not consumption_plan["user_visible_status"]:
        consumption_plan["user_visible_status"] = _default_user_visible_status(consumption_plan)
    if not consumption_plan["operator_visible_summary"]:
        consumption_plan["operator_visible_summary"] = _default_operator_visible_summary(consumption_plan)

    if not data.get("stage_results"):
        consumption_plan["stage_results"] = _safe_stage_results(consumption_plan, consumption_plan["dry_run_validation"], consumption_plan["answer_plan_validation"])
    else:
        consumption_plan["stage_results"] = _json_safe(data.get("stage_results"))

    probe_answer_plan = build_project_chat_answer_plan_v1(
        {
            "project_id": consumption_plan["project_id"],
            "owner_user_scope": consumption_plan["owner_user_scope"],
            "tenant_account_scope": consumption_plan["tenant_account_scope"],
            "source_scope": consumption_plan["source_scope"],
            "user_intent_class": _safe_str(consumption_plan["dry_run_metadata"].get("user_intent_class")) or "project-chat",
            "answer_mode": "clarifying_question",
            "allowed_answer_scope": "current_message_only",
            "answer_status": "clarification_required",
            "user_visible_status": consumption_plan["user_visible_status"],
            "operator_visible_summary": consumption_plan["operator_visible_summary"],
            "denied_authority": dict(_DEFAULT_FALSE_DENIED_AUTHORITY),
        }
    )
    consumption_plan["status_probe_validation"] = validate_project_chat_answer_plan_v1(probe_answer_plan)

    return consumption_plan



def validate_project_chat_dry_run_consumption_plan_v1(plan: Any) -> dict[str, Any]:
    candidate = build_project_chat_dry_run_consumption_plan_v1(plan)
    blocked_labels: list[str] = []

    if candidate.get("schema_version") != SCHEMA_VERSION_V1:
        blocked_labels.append("unknown_schema_version")

    required_fields = (
        "consumption_plan_id",
        "dry_run_ref",
        "dry_run_metadata",
        "project_id",
        "owner_user_scope",
        "tenant_account_scope",
        "source_scope",
        "consumption_status",
        "consumption_action",
        "allowed_next_metadata_step",
        "answer_plan_ref",
        "answer_plan_metadata",
        "user_visible_status",
    )
    for field in required_fields:
        value = candidate.get(field)
        if field == "dry_run_metadata" or field == "answer_plan_metadata":
            if not isinstance(value, Mapping):
                blocked_labels.append(f"missing_{field}")
            continue
        if not _safe_str(value):
            blocked_labels.append(f"missing_{field}")

    action = _safe_str(candidate.get("consumption_action"))
    status = _safe_str(candidate.get("consumption_status"))
    if action not in CONSUMPTION_ACTIONS_V1:
        blocked_labels.append("unknown_consumption_action")
    if status not in CONSUMPTION_STATUSES_V1:
        blocked_labels.append("unknown_consumption_status")

    dry_run_validation = _as_mapping(candidate.get("dry_run_validation"))
    dry_run = _as_mapping(dry_run_validation.get("dry_run"))
    nested_dry_run_valid = bool(dry_run_validation) and not dry_run_validation.get("blocked")
    if not nested_dry_run_valid:
        blocked_labels.append("invalid_nested_dry_run_metadata")

    dry_run_status = _safe_str(dry_run.get("dry_run_status"))
    dry_run_decision = _safe_str(dry_run.get("dry_run_decision"))
    if dry_run_status == "blocked" or dry_run_decision.startswith("block_due_to_"):
        if action not in _BLOCKED_ACTIONS and action != "remain_dry_run_only":
            blocked_labels.append("blocked_dry_run_must_remain_blocked_or_dry_run_only")
    if dry_run_status == "clarification_required" or dry_run_decision == "ask_clarifying_question":
        if action != "ask_clarifying_question_metadata_only":
            blocked_labels.append("clarification_must_remain_clarification_metadata_only")
    if dry_run_status == "approval_required" or dry_run_decision == "request_user_approval":
        if action != "request_user_approval_metadata_only":
            blocked_labels.append("approval_must_remain_approval_metadata_only")
    if dry_run_status == "operator_review_required" or dry_run_decision == "request_operator_review":
        if action != "request_operator_review_metadata_only":
            blocked_labels.append("operator_review_must_remain_operator_review_metadata_only")
    if dry_run_status == "dry_run_valid_metadata_only" or dry_run_decision == "proceed_to_answer_plan_metadata":
        if action not in {
            "remain_dry_run_only",
            "prepare_answer_plan_metadata_only",
            "prepare_retrieval_request_metadata_only",
            "prepare_tool_lane_candidate_metadata_only",
            "prepare_persistence_candidate_metadata_only",
        }:
            blocked_labels.append("proceed_to_answer_plan_metadata_requires_metadata_only_action")

    answer_plan_metadata = _as_mapping(candidate.get("answer_plan_metadata"))
    if action == "prepare_answer_plan_metadata_only" and not _safe_str(answer_plan_metadata.get("answer_mode")):
        blocked_labels.append("missing_answer_plan_metadata")

    if action == "prepare_retrieval_request_metadata_only" and not candidate.get("evidence_packet_refs"):
        blocked_labels.append("retrieval_request_metadata_requires_refs")
    if action == "prepare_tool_lane_candidate_metadata_only" and not candidate.get("tool_lane_candidate_refs"):
        blocked_labels.append("tool_lane_candidate_metadata_requires_refs")

    if action == "blocked_private_mechanism_boundary" and status != "blocked":
        blocked_labels.append("private_mechanism_boundary_requires_blocked_status")
    if action == "blocked_runtime_wiring_boundary" and status != "blocked":
        blocked_labels.append("runtime_wiring_boundary_requires_blocked_status")
    if action == "blocked_final_answer_boundary" and status != "blocked":
        blocked_labels.append("final_answer_boundary_requires_blocked_status")

    if candidate.get("status_probe_validation", {}).get("blocked"):
        blocked_labels.append("user_visible_status_forbidden_phrase")

    for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1:
        if field not in _as_mapping(candidate.get("denied_authority")):
            blocked_labels.append(f"missing_denied_authority_{field}")
        elif _safe_bool(_as_mapping(candidate.get("denied_authority")).get(field, False)):
            blocked_labels.append(f"denied_authority_asserted_{field}")

    user_visible_status = _safe_str(candidate.get("user_visible_status"))
    if not user_visible_status:
        blocked_labels.append("missing_user_visible_status")

    if any(marker in user_visible_status for marker in ("Unknown Engine",)):
        blocked_labels.append("unknown_engine_in_user_visible_status")

    answer_plan_validation = _as_mapping(candidate.get("answer_plan_validation"))
    if answer_plan_validation.get("blocked"):
        blocked_labels.append("answer_plan_metadata_invalid")

    stage_results = candidate.get("stage_results", [])
    if not isinstance(stage_results, list):
        blocked_labels.append("missing_stage_results")
        stage_results = []
    for item in stage_results:
        if not isinstance(item, Mapping):
            blocked_labels.append("invalid_stage_result_shape")
            continue
        stage_name = _safe_str(item.get("stage"))
        stage_status = _safe_str(item.get("status"))
        stage_decision = _safe_str(item.get("decision"))
        if not stage_name:
            blocked_labels.append("missing_stage_name")
        if not stage_status:
            blocked_labels.append(f"missing_stage_status_{stage_name or 'missing'}")
        if not stage_decision:
            blocked_labels.append(f"missing_stage_decision_{stage_name or 'missing'}")

    blocked = bool(blocked_labels)
    if not blocked and status == "invalid":
        blocked = True
        blocked_labels.append("invalid_consumption_plan")

    classification = _classify_consumption_plan_candidate(candidate, blocked)
    result = {
        "blocked": blocked,
        "blocked_labels": _dedupe(blocked_labels),
        "consumption_status": status,
        "consumption_action": action,
        "consumption_plan": candidate,
        "dry_run_validation": dry_run_validation,
        "answer_plan_validation": answer_plan_validation,
        "classification": classification,
    }
    return result



def classify_project_chat_dry_run_consumption_plan_v1(plan: Any) -> dict[str, Any]:
    candidate = build_project_chat_dry_run_consumption_plan_v1(plan)
    validation = validate_project_chat_dry_run_consumption_plan_v1(candidate)
    classification = _classify_consumption_plan_candidate(candidate, validation["blocked"])
    return {
        "classification": classification,
        "blocked": validation["blocked"],
        "consumption_status": validation["consumption_status"],
        "consumption_action": validation["consumption_action"],
    }



def summarize_project_chat_dry_run_consumption_plan_v1(plan: Any) -> dict[str, Any]:
    candidate = build_project_chat_dry_run_consumption_plan_v1(plan)
    validation = validate_project_chat_dry_run_consumption_plan_v1(candidate)
    summary_text = (
        f"{_safe_str(candidate.get('consumption_action'))} | "
        f"{_safe_str(candidate.get('consumption_status'))} | "
        f"dry_run={_safe_str(_as_mapping(candidate.get('dry_run_validation')).get('dry_run_status'))}"
    )
    if validation["blocked"]:
        summary_text = "metadata-only consumption plan blocked"
    return {
        "summary_text": summary_text,
        "summary_status": validation["consumption_status"],
        "summary_action": validation["consumption_action"],
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
    }



def to_project_chat_dry_run_consumption_plan_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)



def build_initial_project_chat_dry_run_consumption_plan_examples_v1() -> list[dict[str, Any]]:
    examples = [
        build_project_chat_dry_run_consumption_plan_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "dry_run_metadata": {
                    "project_id": "project-001",
                    "owner_user_scope": "owner-user",
                    "tenant_account_scope": "tenant-a",
                    "source_scope": "project_metadata_only",
                    "user_intent_class": "project-chat",
                    "dry_run_status": "dry_run_valid_metadata_only",
                    "dry_run_decision": "proceed_to_answer_plan_metadata",
                    "retrieval_need_class": "none",
                    "user_visible_status": "metadata only",
                    "operator_visible_summary": "metadata only",
                    "denied_authority": dict(_DEFAULT_FALSE_DENIED_AUTHORITY),
                },
                "consumption_status": "consumption_plan_valid_metadata_only",
                "consumption_action": "prepare_answer_plan_metadata_only",
                "allowed_next_metadata_step": "prepare_answer_plan_metadata_only",
                "user_visible_status": "answer-plan metadata only",
                "operator_visible_summary": "answer-plan metadata only",
                "denied_authority": dict(_DEFAULT_FALSE_DENIED_AUTHORITY),
            }
        ),
        build_project_chat_dry_run_consumption_plan_v1(
            {
                "project_id": "project-002",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "dry_run_metadata": {
                    "project_id": "project-002",
                    "owner_user_scope": "owner-user",
                    "tenant_account_scope": "tenant-a",
                    "source_scope": "project_metadata_only",
                    "user_intent_class": "project-chat",
                    "dry_run_status": "clarification_required",
                    "dry_run_decision": "ask_clarifying_question",
                    "retrieval_need_class": "none",
                    "user_visible_status": "clarification needed",
                    "operator_visible_summary": "clarification needed",
                    "denied_authority": dict(_DEFAULT_FALSE_DENIED_AUTHORITY),
                },
                "consumption_status": "clarification_required",
                "consumption_action": "ask_clarifying_question_metadata_only",
                "allowed_next_metadata_step": "ask_clarifying_question_metadata_only",
                "user_visible_status": "clarification needed",
                "operator_visible_summary": "clarification metadata only",
                "denied_authority": dict(_DEFAULT_FALSE_DENIED_AUTHORITY),
            }
        ),
    ]
    return examples
