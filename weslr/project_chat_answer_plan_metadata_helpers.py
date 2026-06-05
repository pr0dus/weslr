"""Metadata-only helpers for WESLR project-chat answer planning V1.

This module is intentionally pure, deterministic, synthetic/example-safe,
and fail-closed.
It builds and validates answer-plan metadata packets only.

It does not perform file I/O, network I/O, shell execution, runtime/chat
wiring, retrieval, model calls, tool execution, external actions, persistence,
or final answer generation.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

HELPER_TYPE_V1 = "weslr_project_chat_answer_plan_metadata_helpers_v1"
SCHEMA_VERSION_V1 = "project_chat_answer_plan_metadata_v1"

ANSWER_MODES_V1 = (
    "blocked_boundary_response",
    "candidate_project_summary",
    "clarifying_question",
    "contradiction_resolution_request",
    "deeper_analysis_requires_approval",
    "evidence_grounded_answer",
    "operator_review_required_response",
    "project_start_guidance",
    "surface_gap_review_summary",
    "tool_request_boundary_response",
    "uncertain_or_missing_evidence_answer",
)

ANSWER_SCOPES_V1 = (
    "approved_evidence_packet",
    "approved_memory_limited",
    "approved_project_context",
    "blocked_no_authority",
    "current_message_only",
    "deeper_analysis_approval_required",
    "operator_review_required",
    "project_metadata_only",
    "surface_gap_review_only",
    "tool_lane_candidate_only",
)

ANSWER_STATUSES_V1 = (
    "approval_required",
    "blocked",
    "clarification_required",
    "invalid",
    "operator_review_required",
    "plan_valid_metadata_only",
)

DENIED_AUTHORITY_FIELDS_V1 = (
    "runtime_wiring_authority",
    "project_chat_runtime_authority",
    "final_answer_generation_implementation_authority",
    "storage_database_authority",
    "weslr_io_authority",
    "project_state_mutation_authority",
    "memory_mutation_authority",
    "tool_execution_authority",
    "external_action_authority",
    "hidden_memory_authority",
    "hidden_project_state_authority",
    "private_mechanism_disclosure_authority",
    "cross_user_leakage_authority",
    "unapproved_external_query_authority",
    "retrieval_truth_authority",
    "unsupported_certainty_authority",
    "public_product_readiness_authority",
    "autonomous_self_improvement_authority",
)

_DEFAULT_FALSE_DENIED_AUTHORITY = {field: False for field in DENIED_AUTHORITY_FIELDS_V1}


def allowed_project_chat_answer_modes_v1() -> tuple[str, ...]:
    return ANSWER_MODES_V1


def allowed_project_chat_answer_scopes_v1() -> tuple[str, ...]:
    return ANSWER_SCOPES_V1


def allowed_project_chat_answer_statuses_v1() -> tuple[str, ...]:
    return ANSWER_STATUSES_V1


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
        return [_json_safe(item) for item in sorted(value, key=lambda x: _safe_str(x))]
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
    for field in DENIED_AUTHORITY_FIELDS_V1:
        payload[field] = _safe_bool(raw.get(field, False))
    return payload


def _normalize_plan(payload: Mapping[str, Any]) -> dict[str, Any]:
    plan = {
        "schema_version": _safe_str(payload.get("schema_version")) or SCHEMA_VERSION_V1,
        "answer_plan_id": _safe_str(payload.get("answer_plan_id")),
        "project_id": _safe_str(payload.get("project_id")),
        "owner_user_scope": _safe_str(payload.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(payload.get("tenant_account_scope")),
        "source_scope": _safe_str(payload.get("source_scope")),
        "user_intent_class": _safe_str(payload.get("user_intent_class")),
        "answer_mode": _safe_str(payload.get("answer_mode")),
        "allowed_answer_scope": _safe_str(payload.get("allowed_answer_scope")),
        "answer_status": _safe_str(payload.get("answer_status")),
        "evidence_packet_refs": _normalize_refs(payload.get("evidence_packet_refs")),
        "project_state_refs": _normalize_refs(payload.get("project_state_refs")),
        "memory_state_refs": _normalize_refs(payload.get("memory_state_refs")),
        "continuity_state_refs": _normalize_refs(payload.get("continuity_state_refs")),
        "gap_analysis_refs": _normalize_refs(payload.get("gap_analysis_refs")),
        "tool_lane_candidate_refs": _normalize_refs(payload.get("tool_lane_candidate_refs")),
        "operator_visibility_refs": _normalize_refs(payload.get("operator_visibility_refs")),
        "uncertainty_flags": _normalize_flags(payload.get("uncertainty_flags")),
        "stale_state_flags": _normalize_flags(payload.get("stale_state_flags")),
        "contradiction_flags": _normalize_flags(payload.get("contradiction_flags")),
        "missing_evidence_flags": _normalize_flags(payload.get("missing_evidence_flags")),
        "privacy_flags": _normalize_flags(payload.get("privacy_flags")),
        "approval_refs": _normalize_refs(payload.get("approval_refs")),
        "blocked_authority": _safe_str(payload.get("blocked_authority")),
        "limitations": _normalize_flags(payload.get("limitations")),
        "user_visible_status": _safe_str(payload.get("user_visible_status")),
        "operator_visible_summary": _safe_str(payload.get("operator_visible_summary")),
        "denied_authority": _normalize_denied_authority(payload.get("denied_authority")),
        "helper_type": HELPER_TYPE_V1,
        "raw_content_stored": False,
    }
    return plan


def _coalesce_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = {}
    if isinstance(payload, Mapping):
        data.update(payload)
    elif payload is not None:
        data["payload"] = payload
    data.update(overrides)
    return data


def _default_user_visible_status(plan: Mapping[str, Any]) -> str:
    mode = _safe_str(plan.get("answer_mode"))
    status = _safe_str(plan.get("answer_status"))
    if status == "blocked" or mode == "blocked_boundary_response":
        return "blocked boundary response"
    if status == "operator_review_required" or mode == "operator_review_required_response":
        return "operator review required"
    if status == "approval_required" or mode == "deeper_analysis_requires_approval":
        return "approval required before deeper analysis"
    if status == "clarification_required" or mode == "clarifying_question":
        return "clarification needed"
    if mode == "project_start_guidance":
        return "project start guidance"
    if mode == "candidate_project_summary":
        return "candidate project summary"
    if mode == "surface_gap_review_summary":
        return "surface gap review summary"
    if mode == "evidence_grounded_answer":
        return "evidence grounded answer"
    if mode == "uncertain_or_missing_evidence_answer":
        return "uncertain or missing evidence"
    if mode == "contradiction_resolution_request":
        return "contradiction resolution needed"
    if mode == "tool_request_boundary_response":
        return "tool request boundary response"
    return "metadata only"


def _blocked_authority_name(plan: Mapping[str, Any]) -> str:
    blocked = _safe_str(plan.get("blocked_authority"))
    if blocked:
        return blocked
    denied = _as_mapping(plan.get("denied_authority"))
    for field in DENIED_AUTHORITY_FIELDS_V1:
        if _safe_bool(denied.get(field, False)):
            return field
    return ""


def _validate_allowed_value(value: str, allowed: tuple[str, ...], label: str, blocked_labels: list[str]) -> bool:
    if not value:
        blocked_labels.append(f"missing_{label}")
        return False
    if value not in allowed:
        blocked_labels.append(f"unknown_{label}")
        return False
    return True


def _summary_text_for_plan(plan: Mapping[str, Any], blocked: bool) -> str:
    evidence_count = len(_normalize_refs(plan.get("evidence_packet_refs")))
    return (
        f"{_safe_str(plan.get('answer_mode'))} | "
        f"{_safe_str(plan.get('answer_status'))} | "
        f"scope={_safe_str(plan.get('allowed_answer_scope'))} | "
        f"evidence_refs={evidence_count} | "
        f"blocked={blocked}"
    )


def build_project_chat_answer_plan_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _coalesce_payload(payload, **overrides)
    plan = _normalize_plan(data)

    digest_source = {
        key: value
        for key, value in plan.items()
        if key not in {"answer_plan_id", "operator_visible_summary", "user_visible_status"}
    }
    digest = _stable_digest(digest_source)
    if not plan["answer_plan_id"]:
        plan["answer_plan_id"] = f"project-chat-answer-plan-{digest[:16]}"

    if not plan["user_visible_status"]:
        plan["user_visible_status"] = _default_user_visible_status(plan)
    return plan


def validate_project_chat_answer_plan_v1(plan: Any) -> dict[str, Any]:
    candidate = build_project_chat_answer_plan_v1(plan)
    blocked_labels: list[str] = []

    if candidate.get("schema_version") != SCHEMA_VERSION_V1:
        blocked_labels.append("unknown_schema_version")

    required_fields = (
        "answer_plan_id",
        "project_id",
        "owner_user_scope",
        "tenant_account_scope",
        "source_scope",
        "user_intent_class",
        "answer_mode",
        "allowed_answer_scope",
        "answer_status",
    )
    for field in required_fields:
        if not _safe_str(candidate.get(field)):
            blocked_labels.append(f"missing_{field}")

    mode = _safe_str(candidate.get("answer_mode"))
    scope = _safe_str(candidate.get("allowed_answer_scope"))
    status = _safe_str(candidate.get("answer_status"))

    _validate_allowed_value(mode, ANSWER_MODES_V1, "answer_mode", blocked_labels)
    _validate_allowed_value(scope, ANSWER_SCOPES_V1, "answer_scope", blocked_labels)
    _validate_allowed_value(status, ANSWER_STATUSES_V1, "answer_status", blocked_labels)

    evidence_refs = _normalize_refs(candidate.get("evidence_packet_refs"))
    candidate["evidence_packet_refs"] = evidence_refs

    if mode == "evidence_grounded_answer" and not evidence_refs:
        blocked_labels.append("missing_evidence_packet_refs")
    if scope == "approved_evidence_packet" and not evidence_refs:
        blocked_labels.append("missing_approved_evidence_packet_refs")
    if mode == "deeper_analysis_requires_approval" and not _normalize_refs(candidate.get("approval_refs")):
        blocked_labels.append("missing_approval_refs")
    if mode == "blocked_boundary_response" and not _blocked_authority_name(candidate):
        blocked_labels.append("missing_blocked_authority")
    if mode == "operator_review_required_response" and not (_normalize_refs(candidate.get("operator_visibility_refs")) or _safe_str(candidate.get("operator_visible_summary"))):
        blocked_labels.append("missing_operator_visibility_refs")
    if mode == "tool_request_boundary_response" and scope != "tool_lane_candidate_only":
        blocked_labels.append("tool_request_scope_must_be_tool_lane_candidate_only")

    if candidate.get("contradiction_flags") and mode not in {"contradiction_resolution_request", "uncertain_or_missing_evidence_answer", "clarifying_question"}:
        blocked_labels.append("contradiction_requires_resolution")
    if candidate.get("missing_evidence_flags") and mode not in {"uncertain_or_missing_evidence_answer", "clarifying_question"}:
        blocked_labels.append("missing_evidence_requires_uncertainty")
    if candidate.get("stale_state_flags") and mode == "evidence_grounded_answer":
        blocked_labels.append("stale_state_requires_non_grounded_mode")

    denied = _as_mapping(candidate.get("denied_authority"))
    for field in DENIED_AUTHORITY_FIELDS_V1:
        if field not in denied:
            blocked_labels.append(f"missing_denied_authority_{field}")
        elif _safe_bool(denied.get(field, False)):
            blocked_labels.append(f"denied_authority_asserted_{field}")

    user_visible_status = _safe_str(candidate.get("user_visible_status"))
    if not user_visible_status:
        blocked_labels.append("missing_user_visible_status")
    if "Unknown Engine" in user_visible_status:
        blocked_labels.append("unknown_engine_in_user_visible_status")
    private_markers = ("private_runtime_surface", "private_file_marker", "private_control_surface")
    if any(marker in user_visible_status for marker in private_markers):
        blocked_labels.append("private_mechanism_name_in_user_visible_status")

    blocked_authority = _blocked_authority_name(candidate)
    if blocked_authority:
        candidate["blocked_authority"] = blocked_authority

    valid = not blocked_labels
    if not valid:
        answer_status = "invalid"
    else:
        answer_status = status

    result = {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "answer_plan": candidate,
        "answer_plan_id": candidate["answer_plan_id"],
        "answer_mode": mode,
        "allowed_answer_scope": scope,
        "answer_status": answer_status,
        "valid_metadata_only": valid,
        "blocked": not valid,
        "blocked_labels": blocked_labels,
        "validation_notes": blocked_labels[:],
        "user_visible_status": user_visible_status,
        "operator_visible_summary": _safe_str(candidate.get("operator_visible_summary")),
        "denied_authority": dict(denied),
    }
    if not valid and answer_status == "invalid":
        result["answer_plan"]["answer_status"] = "invalid"
    return result


def classify_project_chat_answer_plan_v1(plan: Any) -> dict[str, Any]:
    validation = validate_project_chat_answer_plan_v1(plan)
    candidate = validation["answer_plan"]
    mode = _safe_str(candidate.get("answer_mode"))
    status = _safe_str(validation.get("answer_status"))

    if validation["blocked"]:
        classification = "blocked"
    elif status == "invalid":
        classification = "invalid"
    elif mode == "clarifying_question":
        classification = "clarification_required"
    elif mode == "project_start_guidance":
        classification = "project_start_guidance"
    elif mode == "candidate_project_summary":
        classification = "candidate_project_summary"
    elif mode == "surface_gap_review_summary":
        classification = "surface_gap_review_summary"
    elif mode == "deeper_analysis_requires_approval":
        classification = "approval_required"
    elif mode == "evidence_grounded_answer":
        classification = "evidence_grounded"
    elif mode == "uncertain_or_missing_evidence_answer":
        classification = "uncertain_or_missing_evidence"
    elif mode == "contradiction_resolution_request":
        classification = "contradiction_resolution"
    elif mode == "tool_request_boundary_response":
        classification = "tool_boundary"
    elif mode == "operator_review_required_response":
        classification = "operator_review_required"
    else:
        classification = "metadata_only"

    if candidate.get("contradiction_flags") and classification not in {"contradiction_resolution", "blocked"}:
        classification = "contradiction_resolution"
    if candidate.get("missing_evidence_flags") and classification == "evidence_grounded":
        classification = "uncertain_or_missing_evidence"
    if candidate.get("stale_state_flags") and classification == "evidence_grounded":
        classification = "uncertain_or_missing_evidence"

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "classification": classification,
        "answer_status": validation["answer_status"],
        "answer_mode": mode,
        "allowed_answer_scope": _safe_str(candidate.get("allowed_answer_scope")),
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "needs_approval": classification in {"approval_required", "operator_review_required"},
        "needs_clarification": classification == "clarification_required",
        "needs_operator_review": classification == "operator_review_required",
        "needs_uncertainty": classification == "uncertain_or_missing_evidence",
        "answer_plan_id": candidate["answer_plan_id"],
    }


def summarize_project_chat_answer_plan_v1(plan: Any) -> dict[str, Any]:
    candidate = build_project_chat_answer_plan_v1(plan)
    validation = validate_project_chat_answer_plan_v1(candidate)
    summary_text = _summary_text_for_plan(candidate, validation["blocked"])
    candidate["operator_visible_summary"] = summary_text
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "answer_plan_id": candidate["answer_plan_id"],
        "summary_text": summary_text,
        "answer_mode": _safe_str(candidate.get("answer_mode")),
        "answer_status": _safe_str(candidate.get("answer_status")),
        "allowed_answer_scope": _safe_str(candidate.get("allowed_answer_scope")),
        "evidence_packet_count": len(candidate.get("evidence_packet_refs", [])),
        "stale_state_flag_count": len(candidate.get("stale_state_flags", [])),
        "contradiction_flag_count": len(candidate.get("contradiction_flags", [])),
        "missing_evidence_flag_count": len(candidate.get("missing_evidence_flags", [])),
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "limitations": candidate.get("limitations", []),
        "user_visible_status": _safe_str(candidate.get("user_visible_status")),
        "operator_visible_summary": _safe_str(candidate.get("operator_visible_summary")),
    }


def to_project_chat_answer_plan_json_safe_v1(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): to_project_chat_answer_plan_json_safe_v1(val) for key, val in value.items()}
    if isinstance(value, list):
        return [to_project_chat_answer_plan_json_safe_v1(item) for item in value]
    if isinstance(value, tuple):
        return [to_project_chat_answer_plan_json_safe_v1(item) for item in value]
    if isinstance(value, set):
        return [to_project_chat_answer_plan_json_safe_v1(item) for item in sorted(value, key=lambda item: _safe_str(item))]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _safe_str(value)


def build_initial_project_chat_answer_plan_examples_v1() -> list[dict[str, Any]]:
    examples = [
        build_project_chat_answer_plan_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "current_message_only",
                "user_intent_class": "clarification",
                "answer_mode": "clarifying_question",
                "allowed_answer_scope": "current_message_only",
                "answer_status": "clarification_required",
                "user_visible_status": "clarification needed",
                "operator_visible_summary": "clarification required; metadata only",
            }
        ),
        build_project_chat_answer_plan_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "user_intent_class": "project_start",
                "answer_mode": "project_start_guidance",
                "allowed_answer_scope": "project_metadata_only",
                "answer_status": "plan_valid_metadata_only",
                "user_visible_status": "project start guidance",
            }
        ),
        build_project_chat_answer_plan_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "approved_evidence_packet",
                "user_intent_class": "evidence_grounded",
                "answer_mode": "evidence_grounded_answer",
                "allowed_answer_scope": "approved_evidence_packet",
                "answer_status": "plan_valid_metadata_only",
                "evidence_packet_refs": ["evidence-001"],
                "user_visible_status": "evidence grounded answer",
            }
        ),
    ]
    return examples


__all__ = [
    "HELPER_TYPE_V1",
    "SCHEMA_VERSION_V1",
    "ANSWER_MODES_V1",
    "ANSWER_SCOPES_V1",
    "ANSWER_STATUSES_V1",
    "DENIED_AUTHORITY_FIELDS_V1",
    "allowed_project_chat_answer_modes_v1",
    "allowed_project_chat_answer_scopes_v1",
    "allowed_project_chat_answer_statuses_v1",
    "build_project_chat_answer_plan_v1",
    "validate_project_chat_answer_plan_v1",
    "classify_project_chat_answer_plan_v1",
    "summarize_project_chat_answer_plan_v1",
    "to_project_chat_answer_plan_json_safe_v1",
    "build_initial_project_chat_answer_plan_examples_v1",
]
