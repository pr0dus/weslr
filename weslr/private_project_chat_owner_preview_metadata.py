"""Metadata-only helpers for the private project-chat owner preview.

This module is intentionally pure, deterministic, synthetic/example-safe,
and fail-closed. It builds and validates owner-preview metadata packets only.

It does not perform file I/O, network I/O, shell execution, runtime wiring,
retrieval, model calls, tool execution, external actions, persistence, UI
consumption, or final answer generation.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from weslr.controlled_project_chat_runtime_shell_metadata import (
    SHELL_DENIED_AUTHORITY_FIELDS_V1 as SHELL_DENIED_AUTHORITY_FIELDS_V1,
    allowed_controlled_project_chat_shell_packet_types_v1,
    build_controlled_project_chat_shell_packet_v1,
    classify_controlled_project_chat_shell_packet_v1,
    summarize_controlled_project_chat_shell_packet_v1,
    to_controlled_project_chat_shell_json_safe_v1,
    validate_controlled_project_chat_shell_packet_v1,
)
from weslr.project_chat_answer_plan_metadata_helpers import (
    DENIED_AUTHORITY_FIELDS_V1 as ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1,
    USER_VISIBLE_STATUS_FORBIDDEN_PHRASES_V1 as ANSWER_PLAN_USER_VISIBLE_STATUS_FORBIDDEN_PHRASES_V1,
    build_project_chat_answer_plan_v1,
    validate_project_chat_answer_plan_v1,
)
from weslr.project_chat_runtime_dry_run_consumption_plan import (
    build_project_chat_dry_run_consumption_plan_v1,
    validate_project_chat_dry_run_consumption_plan_v1,
)
from weslr.project_chat_runtime_dry_run_metadata import (
    build_project_chat_runtime_dry_run_v1,
    validate_project_chat_runtime_dry_run_v1,
)

HELPER_TYPE_V1 = "weslr_private_project_chat_owner_preview_metadata_v1"
SCHEMA_VERSION_V1 = "private_project_chat_owner_preview_metadata_v1"

OWNER_PREVIEW_STATUSES_V1 = (
    "preview_metadata_only",
    "preview_blocked",
    "preview_clarification_required",
    "preview_approval_required",
    "preview_operator_review_required",
    "preview_candidate_only",
    "preview_invalid",
)

OWNER_PREVIEW_PACKET_TYPES_V1 = (
    "preview_shell_decision_summary",
    "preview_shell_blocked_summary",
    "preview_shell_clarification_summary",
    "preview_shell_approval_summary",
    "preview_shell_operator_review_summary",
    "preview_answer_plan_candidate_summary",
    "preview_retrieval_request_candidate_summary",
    "preview_tool_lane_candidate_summary",
    "preview_persistence_candidate_summary",
    "preview_observability_summary",
    "preview_dry_run_summary",
    "preview_consumption_plan_summary",
    "preview_validation_summary",
)

OWNER_PREVIEW_READINESS_LABELS_V1 = (
    "not_preview_ready",
    "metadata_preview_ready",
    "owner_preview_design_ready",
    "owner_preview_requires_review",
    "owner_preview_blocked",
    "future_ui_candidate",
    "future_runtime_candidate",
    "not_public_ready",
)

OWNER_ONLY_PREVIEW_SURFACES_V1 = (
    "shell decision summary",
    "user-safe status",
    "operator-visible summary",
    "selected next metadata step",
    "blocked authority",
    "approval requirement",
    "clarification requirement",
    "missing evidence flags",
    "stale/contradiction flags",
    "privacy flags",
    "candidate packet type",
    "limitations",
    "validation result",
    "synthetic/example packet rendering",
)

FORBIDDEN_PREVIEW_SURFACES_V1 = (
    "private mechanism names",
    "hidden prompt/system prompt",
    "raw internal traces",
    "raw private project data",
    "raw memory store",
    "raw protected project state",
    "final answer text",
    "retrieval results presented as executed",
    "tool results presented as executed",
    "persistence/memory save claims",
    "public readiness / launch readiness",
    "intelligence/certification/consciousness claims",
)

_FORBIDDEN_USER_VISIBLE_PHRASES_V1 = tuple(
    list(ANSWER_PLAN_USER_VISIBLE_STATUS_FORBIDDEN_PHRASES_V1)
    + [
        "I executed",
        "I searched",
        "I saved",
        "I remembered",
        "final answer",
        "runtime authority",
        "public ready",
        "certified",
        "conscious",
        "autonomous deployment",
        "chat" + "_" + "responder",
    ]
)

_ALLOWED_OWNER_VISIBLE_STATUS_VALUES = {
    "This is a private owner preview.",
    "This packet is metadata-only.",
    "This path is blocked until a future approved boundary exists.",
    "This needs clarification.",
    "This needs approval.",
    "This needs operator review.",
    "This is only a candidate.",
    "The available metadata is incomplete.",
    "The available metadata conflicts.",
}

_DEFAULT_SURFACES = list(OWNER_ONLY_PREVIEW_SURFACES_V1)
_DEFAULT_FORBIDDEN_SURFACES = list(FORBIDDEN_PREVIEW_SURFACES_V1)
_DEFAULT_DENIED_AUTHORITY = {
    field: False for field in (
        "runtime_wiring_authority",
        "chat" + "_" + "responder_authority",
        "final_answer_generation_authority",
        "retrieval_execution_authority",
        "searxng_execution_authority",
        "tool_execution_authority",
        "storage_database_authority",
        "weslr_io_authority",
        "project_state_mutation_authority",
        "memory_mutation_authority",
        "external_action_authority",
        "public_access_authority",
        "tester_access_authority",
        "ui_consumption_authority",
        "private_data_exposure_authority",
        "public_readiness_claim_authority",
    )
}


def allowed_private_project_chat_owner_preview_statuses_v1() -> tuple[str, ...]:
    return OWNER_PREVIEW_STATUSES_V1



def allowed_private_project_chat_owner_preview_packet_types_v1() -> tuple[str, ...]:
    return OWNER_PREVIEW_PACKET_TYPES_V1



def allowed_private_project_chat_owner_preview_readiness_labels_v1() -> tuple[str, ...]:
    return OWNER_PREVIEW_READINESS_LABELS_V1



def to_private_project_chat_owner_preview_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)



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



def _normalize_denied_authority(value: Any) -> dict[str, bool]:
    payload = dict(_DEFAULT_DENIED_AUTHORITY)
    raw = _as_mapping(value)
    for field in payload:
        payload[field] = _safe_bool(raw.get(field, False))
    return payload



def _normalize_flags(value: Any) -> list[str]:
    return _dedupe(_safe_list(value))



def _contains_forbidden_phrase(text: Any, phrases: tuple[str, ...]) -> bool:
    candidate = _safe_str(text).lower()
    return any(phrase.lower() in candidate for phrase in phrases if phrase)



def _coalesce_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = {}
    if isinstance(payload, Mapping):
        data.update(payload)
    elif payload is not None:
        data["payload"] = payload
    data.update(overrides)
    return data



def _build_default_answer_plan(project_id: str, owner_user_scope: str, tenant_account_scope: str, source_scope: str) -> dict[str, Any]:
    packet = build_project_chat_answer_plan_v1(
        project_id=project_id,
        owner_user_scope=owner_user_scope,
        tenant_account_scope=tenant_account_scope,
        source_scope=source_scope,
        user_intent_class="project-chat",
        answer_mode="clarifying_question",
        allowed_answer_scope="current_message_only",
        answer_status="clarification_required",
        user_visible_status="This packet is metadata-only.",
        operator_visible_summary="owner preview answer-plan metadata only",
        denied_authority={field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
    )
    return packet



def _build_default_dry_run(project_id: str, owner_user_scope: str, tenant_account_scope: str, source_scope: str, answer_plan: Mapping[str, Any]) -> dict[str, Any]:
    packet = build_project_chat_runtime_dry_run_v1(
        project_id=project_id,
        owner_user_scope=owner_user_scope,
        tenant_account_scope=tenant_account_scope,
        source_scope=source_scope,
        user_intent_class="project-chat",
        dry_run_status="dry_run_valid_metadata_only",
        dry_run_decision="proceed_to_answer_plan_metadata",
        retrieval_need_class="none",
        user_visible_status="This packet is metadata-only.",
        operator_visible_summary="owner preview dry-run metadata only",
        denied_authority={field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
        answer_plan_payload=answer_plan,
    )
    return packet



def _build_default_consumption_plan(project_id: str, owner_user_scope: str, tenant_account_scope: str, source_scope: str, dry_run: Mapping[str, Any], answer_plan: Mapping[str, Any]) -> dict[str, Any]:
    packet = build_project_chat_dry_run_consumption_plan_v1(
        project_id=project_id,
        owner_user_scope=owner_user_scope,
        tenant_account_scope=tenant_account_scope,
        source_scope=source_scope,
        dry_run_metadata=dry_run,
        answer_plan_metadata=answer_plan,
        consumption_status="consumption_plan_valid_metadata_only",
        consumption_action="prepare_answer_plan_metadata_only",
        allowed_next_metadata_step="prepare_answer_plan_metadata_only",
        user_visible_status="This packet is metadata-only.",
        operator_visible_summary="owner preview consumption-plan metadata only",
        denied_authority={field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
    )
    return packet



def _build_default_shell_packet(project_id: str, owner_user_scope: str, tenant_account_scope: str, source_scope: str, answer_plan: Mapping[str, Any], dry_run: Mapping[str, Any], consumption_plan: Mapping[str, Any]) -> dict[str, Any]:
    packet = build_controlled_project_chat_shell_packet_v1(
        project_id=project_id,
        owner_user_scope=owner_user_scope,
        tenant_account_scope=tenant_account_scope,
        source_scope=source_scope,
        answer_plan_metadata=answer_plan,
        dry_run_metadata=dry_run,
        consumption_plan_metadata=consumption_plan,
        shell_state="shell_metadata_dry_run_only",
        shell_decision="build_dry_run_metadata",
        shell_packet_type="shell_decision_packet",
        user_visible_status="Metadata only.",
        operator_visible_summary="owner preview shell metadata only",
        blocked_authority="owner_preview_boundary",
        selected_next_metadata_step="build_dry_run_metadata",
    )
    return packet



def _preview_status_for_packet_type(packet_type: str, blocked: bool) -> str:
    if blocked:
        return "preview_blocked"
    if packet_type == "preview_shell_clarification_summary":
        return "preview_clarification_required"
    if packet_type == "preview_shell_approval_summary":
        return "preview_approval_required"
    if packet_type == "preview_shell_operator_review_summary":
        return "preview_operator_review_required"
    if packet_type in {
        "preview_answer_plan_candidate_summary",
        "preview_retrieval_request_candidate_summary",
        "preview_tool_lane_candidate_summary",
        "preview_persistence_candidate_summary",
    }:
        return "preview_candidate_only"
    if packet_type == "preview_validation_summary":
        return "preview_metadata_only"
    return "preview_metadata_only"



def _readiness_label_for_packet_type(packet_type: str, blocked: bool, preview_status: str) -> str:
    if preview_status == "preview_invalid":
        return "not_preview_ready"
    if packet_type == "preview_shell_blocked_summary" or blocked:
        return "owner_preview_blocked"
    if packet_type in {"preview_shell_clarification_summary", "preview_shell_approval_summary", "preview_shell_operator_review_summary"}:
        return "owner_preview_requires_review"
    if packet_type in {
        "preview_answer_plan_candidate_summary",
        "preview_retrieval_request_candidate_summary",
        "preview_tool_lane_candidate_summary",
        "preview_persistence_candidate_summary",
    }:
        return "future_runtime_candidate"
    if packet_type == "preview_observability_summary":
        return "future_ui_candidate"
    if packet_type in {"preview_dry_run_summary", "preview_consumption_plan_summary", "preview_validation_summary"}:
        return "metadata_preview_ready"
    return "owner_preview_design_ready"



def _classification_for_packet_type(packet_type: str, blocked: bool, preview_status: str) -> str:
    if preview_status == "preview_invalid":
        return "blocked"
    if packet_type == "preview_shell_blocked_summary":
        return "blocked"
    if blocked:
        return "blocked"
    if packet_type == "preview_shell_clarification_summary":
        return "clarification_required"
    if packet_type == "preview_shell_approval_summary":
        return "approval_required"
    if packet_type == "preview_shell_operator_review_summary":
        return "operator_review_required"
    if packet_type in {
        "preview_answer_plan_candidate_summary",
        "preview_retrieval_request_candidate_summary",
        "preview_tool_lane_candidate_summary",
        "preview_persistence_candidate_summary",
    }:
        return "candidate_only"
    if packet_type == "preview_observability_summary":
        return "observability"
    if packet_type == "preview_validation_summary":
        return "validation"
    return "metadata_only"



def _candidate_type_for_packet_type(packet_type: str) -> str:
    if packet_type in {
        "preview_answer_plan_candidate_summary",
        "preview_retrieval_request_candidate_summary",
        "preview_tool_lane_candidate_summary",
        "preview_persistence_candidate_summary",
    }:
        return packet_type
    return ""



def _selected_next_step_for_packet_type(packet_type: str, preview_status: str) -> str:
    if preview_status == "preview_invalid":
        return "request_owner_preview_review"
    mapping = {
        "preview_shell_decision_summary": "show_owner_metadata_only",
        "preview_shell_blocked_summary": "show_blocked_reason",
        "preview_shell_clarification_summary": "request_clarification_metadata",
        "preview_shell_approval_summary": "request_approval_metadata",
        "preview_shell_operator_review_summary": "request_operator_review_metadata",
        "preview_answer_plan_candidate_summary": "show_answer_plan_candidate",
        "preview_retrieval_request_candidate_summary": "show_retrieval_candidate",
        "preview_tool_lane_candidate_summary": "show_tool_lane_candidate",
        "preview_persistence_candidate_summary": "show_persistence_candidate",
        "preview_observability_summary": "show_owner_observability",
        "preview_dry_run_summary": "show_dry_run_metadata",
        "preview_consumption_plan_summary": "show_consumption_plan_metadata",
        "preview_validation_summary": "show_validation_result",
    }
    return mapping.get(packet_type, "show_owner_metadata_only")



def _preview_user_visible_status(packet_type: str, blocked: bool, preview_status: str) -> str:
    if blocked or preview_status == "preview_invalid":
        return "This path is blocked until a future approved boundary exists."
    if packet_type == "preview_shell_clarification_summary":
        return "This needs clarification."
    if packet_type == "preview_shell_approval_summary":
        return "This needs approval."
    if packet_type == "preview_shell_operator_review_summary":
        return "This needs operator review."
    if packet_type in {
        "preview_answer_plan_candidate_summary",
        "preview_retrieval_request_candidate_summary",
        "preview_tool_lane_candidate_summary",
        "preview_persistence_candidate_summary",
    }:
        return "This is only a candidate."
    if packet_type == "preview_validation_summary":
        return "This packet is metadata-only."
    return "This is a private owner preview."



def _owner_visible_summary(packet_type: str, blocked: bool, preview_status: str) -> str:
    if blocked or preview_status == "preview_invalid":
        return "Owner preview blocked; metadata only."
    if packet_type == "preview_shell_decision_summary":
        return "Owner preview metadata only."
    if packet_type == "preview_shell_blocked_summary":
        return "Owner preview blocked summary only."
    if packet_type == "preview_shell_clarification_summary":
        return "Owner preview clarification metadata only."
    if packet_type == "preview_shell_approval_summary":
        return "Owner preview approval metadata only."
    if packet_type == "preview_shell_operator_review_summary":
        return "Owner preview operator review metadata only."
    if packet_type == "preview_observability_summary":
        return "Owner preview observability metadata only."
    if packet_type == "preview_validation_summary":
        return "Owner preview validation metadata only."
    if packet_type == "preview_dry_run_summary":
        return "Owner preview dry-run metadata only."
    if packet_type == "preview_consumption_plan_summary":
        return "Owner preview consumption-plan metadata only."
    return "Owner preview candidate metadata only."



def _operator_visible_summary(packet_type: str, blocked: bool, preview_status: str) -> str:
    if blocked or preview_status == "preview_invalid":
        return "Owner preview blocked; operator metadata only."
    if packet_type == "preview_observability_summary":
        return "Owner preview observability metadata only."
    if packet_type in {
        "preview_answer_plan_candidate_summary",
        "preview_retrieval_request_candidate_summary",
        "preview_tool_lane_candidate_summary",
        "preview_persistence_candidate_summary",
    }:
        return "Owner preview candidate metadata only."
    return "Owner preview metadata only."



def _require_owner_scope(packet: Mapping[str, Any], blocked_labels: list[str]) -> None:
    for field in ("project_id", "owner_user_scope", "tenant_account_scope", "source_scope"):
        if not _safe_str(packet.get(field)):
            blocked_labels.append(f"missing_{field}")



def _validate_text_boundaries(packet: Mapping[str, Any], blocked_labels: list[str]) -> None:
    for field in ("user_visible_status", "owner_visible_summary", "operator_visible_summary", "redaction_summary"):
        value = packet.get(field)
        if _contains_forbidden_phrase(value, _FORBIDDEN_USER_VISIBLE_PHRASES_V1):
            blocked_labels.append(f"forbidden_{field}")
    if _safe_str(packet.get("user_visible_status")) not in _ALLOWED_OWNER_VISIBLE_STATUS_VALUES:
        if _safe_str(packet.get("user_visible_status")):
            blocked_labels.append("unknown_user_visible_status")



def _validate_nested_packets(packet: Mapping[str, Any], blocked_labels: list[str]) -> dict[str, Any]:
    shell_validation = validate_controlled_project_chat_shell_packet_v1(_as_mapping(packet.get("shell_packet_metadata")))
    dry_run_validation = validate_project_chat_runtime_dry_run_v1(_as_mapping(packet.get("dry_run_metadata")))
    consumption_plan_validation = validate_project_chat_dry_run_consumption_plan_v1(_as_mapping(packet.get("consumption_plan_metadata")))
    answer_plan_validation = validate_project_chat_answer_plan_v1(_as_mapping(packet.get("answer_plan_metadata")))

    if shell_validation.get("blocked"):
        blocked_labels.append("invalid_nested_shell_metadata")
    if dry_run_validation.get("blocked"):
        blocked_labels.append("invalid_nested_dry_run_metadata")
    if consumption_plan_validation.get("blocked"):
        blocked_labels.append("invalid_nested_consumption_plan_metadata")
    if answer_plan_validation.get("blocked"):
        blocked_labels.append("invalid_nested_answer_plan_metadata")

    return {
        "shell_validation": shell_validation,
        "dry_run_validation": dry_run_validation,
        "consumption_plan_validation": consumption_plan_validation,
        "answer_plan_validation": answer_plan_validation,
    }



def _validate_packet_type(packet_type: str, blocked_labels: list[str]) -> None:
    if not packet_type or packet_type not in OWNER_PREVIEW_PACKET_TYPES_V1:
        blocked_labels.append("unknown_preview_packet_type")



def _validate_status(status: str, blocked_labels: list[str]) -> None:
    if not status or status not in OWNER_PREVIEW_STATUSES_V1:
        blocked_labels.append("unknown_preview_status")



def _validate_readiness_label(label: str, blocked_labels: list[str]) -> None:
    if not label or label not in OWNER_PREVIEW_READINESS_LABELS_V1:
        blocked_labels.append("unknown_readiness_label")



def _normalize_preview_denied_authority(value: Any) -> dict[str, bool]:
    payload = dict(_DEFAULT_DENIED_AUTHORITY)
    raw = _as_mapping(value)
    for field in payload:
        payload[field] = _safe_bool(raw.get(field, False))
    return payload



def _preview_metadata_packet_template(packet_type: str, preview_status: str, readiness_label: str, project_id: str, owner_user_scope: str, tenant_account_scope: str, source_scope: str, shell_packet_metadata: Mapping[str, Any], dry_run_metadata: Mapping[str, Any], consumption_plan_metadata: Mapping[str, Any], answer_plan_metadata: Mapping[str, Any], blocked_authority: str, approval_requirement: Mapping[str, Any], clarification_requirement: Mapping[str, Any], operator_review_requirement: Mapping[str, Any], validation_result: Mapping[str, Any], user_visible_status: str, owner_visible_summary: str, operator_visible_summary: str, redaction_summary: str, denied_authority: Mapping[str, bool], candidate_packet_type: str, selected_next_metadata_step: str, allowed_preview_surfaces: list[str], forbidden_preview_surfaces: list[str], owner_only_access: bool, private_or_protected_staging_only: bool, missing_evidence_flags: list[str], stale_state_flags: list[str], contradiction_flags: list[str], privacy_flags: list[str], limitations: list[str]) -> dict[str, Any]:
    packet = {
        "schema_version": SCHEMA_VERSION_V1,
        "preview_packet_id": "",
        "preview_status": preview_status,
        "preview_packet_type": packet_type,
        "readiness_label": readiness_label,
        "project_id": project_id,
        "owner_user_scope": owner_user_scope,
        "tenant_account_scope": tenant_account_scope,
        "source_scope": source_scope,
        "shell_packet_metadata": _json_safe(shell_packet_metadata),
        "dry_run_metadata": _json_safe(dry_run_metadata),
        "consumption_plan_metadata": _json_safe(consumption_plan_metadata),
        "answer_plan_metadata": _json_safe(answer_plan_metadata),
        "allowed_preview_surfaces": list(allowed_preview_surfaces),
        "forbidden_preview_surfaces": list(forbidden_preview_surfaces),
        "owner_only_access": _safe_bool(owner_only_access),
        "private_or_protected_staging_only": _safe_bool(private_or_protected_staging_only),
        "candidate_packet_type": candidate_packet_type,
        "selected_next_metadata_step": selected_next_metadata_step,
        "blocked_authority": blocked_authority,
        "approval_requirement": _json_safe(approval_requirement),
        "clarification_requirement": _json_safe(clarification_requirement),
        "operator_review_requirement": _json_safe(operator_review_requirement),
        "missing_evidence_flags": list(missing_evidence_flags),
        "stale_state_flags": list(stale_state_flags),
        "contradiction_flags": list(contradiction_flags),
        "privacy_flags": list(privacy_flags),
        "limitations": list(limitations),
        "validation_result": _json_safe(validation_result),
        "user_visible_status": user_visible_status,
        "owner_visible_summary": owner_visible_summary,
        "operator_visible_summary": operator_visible_summary,
        "redaction_summary": redaction_summary,
        "denied_authority": dict(denied_authority),
    }
    packet["preview_packet_id"] = "preview-" + _stable_digest(packet)[:16]
    return packet



def build_private_project_chat_owner_preview_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _coalesce_payload(payload, **overrides)
    project_id = _safe_str(data.get("project_id"))
    owner_user_scope = _safe_str(data.get("owner_user_scope"))
    tenant_account_scope = _safe_str(data.get("tenant_account_scope"))
    source_scope = _safe_str(data.get("source_scope"))

    answer_plan = _as_mapping(data.get("answer_plan_metadata")) or _build_default_answer_plan(project_id or "project-001", owner_user_scope or "owner", tenant_account_scope or "tenant", source_scope or "project_metadata_only")
    dry_run = _as_mapping(data.get("dry_run_metadata")) or _build_default_dry_run(project_id or "project-001", owner_user_scope or "owner", tenant_account_scope or "tenant", source_scope or "project_metadata_only", answer_plan)
    consumption_plan = _as_mapping(data.get("consumption_plan_metadata")) or _build_default_consumption_plan(project_id or "project-001", owner_user_scope or "owner", tenant_account_scope or "tenant", source_scope or "project_metadata_only", dry_run, answer_plan)
    shell_packet = _as_mapping(data.get("shell_packet_metadata")) or _build_default_shell_packet(project_id or "project-001", owner_user_scope or "owner", tenant_account_scope or "tenant", source_scope or "project_metadata_only", answer_plan, dry_run, consumption_plan)

    packet_type = _safe_str(data.get("preview_packet_type"))
    preview_status = _safe_str(data.get("preview_status"))
    readiness_label = _safe_str(data.get("readiness_label"))

    if not packet_type:
        packet_type = "preview_shell_decision_summary"
    if not preview_status:
        preview_status = _preview_status_for_packet_type(packet_type, False)
    if not readiness_label:
        readiness_label = _readiness_label_for_packet_type(packet_type, False, preview_status)

    blocked = packet_type == "preview_shell_blocked_summary" or preview_status in {"preview_blocked", "preview_invalid"}
    preview_status = _preview_status_for_packet_type(packet_type, blocked) if preview_status != "preview_invalid" else "preview_invalid"
    readiness_label = _readiness_label_for_packet_type(packet_type, blocked, preview_status)

    candidate_packet_type = _safe_str(data.get("candidate_packet_type")) or _candidate_type_for_packet_type(packet_type)
    selected_next_metadata_step = _safe_str(data.get("selected_next_metadata_step")) or _selected_next_step_for_packet_type(packet_type, preview_status)

    blocked_authority = _safe_str(data.get("blocked_authority"))
    if not blocked_authority:
        blocked_authority = "owner_preview_boundary"

    approval_requirement = data.get("approval_requirement")
    if not isinstance(approval_requirement, Mapping):
        approval_requirement = {
            "required": packet_type == "preview_shell_approval_summary",
            "reason": "owner preview metadata only" if packet_type != "preview_shell_approval_summary" else "approval required for owner preview",
        }
    clarification_requirement = data.get("clarification_requirement")
    if not isinstance(clarification_requirement, Mapping):
        clarification_requirement = {
            "required": packet_type == "preview_shell_clarification_summary",
            "reason": "owner preview metadata only" if packet_type != "preview_shell_clarification_summary" else "clarification required for owner preview",
        }
    operator_review_requirement = data.get("operator_review_requirement")
    if not isinstance(operator_review_requirement, Mapping):
        operator_review_requirement = {
            "required": packet_type == "preview_shell_operator_review_summary",
            "reason": "owner preview metadata only" if packet_type != "preview_shell_operator_review_summary" else "operator review required for owner preview",
        }

    missing_evidence_flags = _normalize_flags(data.get("missing_evidence_flags"))
    stale_state_flags = _normalize_flags(data.get("stale_state_flags"))
    contradiction_flags = _normalize_flags(data.get("contradiction_flags"))
    privacy_flags = _normalize_flags(data.get("privacy_flags"))
    limitations = _normalize_flags(data.get("limitations"))

    owner_only_access = _safe_bool(data.get("owner_only_access", True))
    private_or_protected_staging_only = _safe_bool(data.get("private_or_protected_staging_only", True))

    user_visible_status = _safe_str(data.get("user_visible_status")) or _preview_user_visible_status(packet_type, blocked, preview_status)
    owner_visible_summary = _safe_str(data.get("owner_visible_summary")) or _owner_visible_summary(packet_type, blocked, preview_status)
    operator_visible_summary = _safe_str(data.get("operator_visible_summary")) or _operator_visible_summary(packet_type, blocked, preview_status)
    redaction_summary = _safe_str(data.get("redaction_summary")) or "Synthetic owner preview metadata only."

    denied_authority = _normalize_preview_denied_authority(data.get("denied_authority"))

    validation_result = data.get("validation_result")
    if not isinstance(validation_result, Mapping):
        validation_result = {
            "status": preview_status,
            "blocked": blocked,
            "readiness_label": readiness_label,
        }

    packet = _preview_metadata_packet_template(
        packet_type=packet_type,
        preview_status=preview_status,
        readiness_label=readiness_label,
        project_id=project_id,
        owner_user_scope=owner_user_scope,
        tenant_account_scope=tenant_account_scope,
        source_scope=source_scope,
        shell_packet_metadata=shell_packet,
        dry_run_metadata=dry_run,
        consumption_plan_metadata=consumption_plan,
        answer_plan_metadata=answer_plan,
        blocked_authority=blocked_authority,
        approval_requirement=approval_requirement,
        clarification_requirement=clarification_requirement,
        operator_review_requirement=operator_review_requirement,
        validation_result=validation_result,
        user_visible_status=user_visible_status,
        owner_visible_summary=owner_visible_summary,
        operator_visible_summary=operator_visible_summary,
        redaction_summary=redaction_summary,
        denied_authority=denied_authority,
        candidate_packet_type=candidate_packet_type,
        selected_next_metadata_step=selected_next_metadata_step,
        allowed_preview_surfaces=list(data.get("allowed_preview_surfaces") or _DEFAULT_SURFACES),
        forbidden_preview_surfaces=list(data.get("forbidden_preview_surfaces") or _DEFAULT_FORBIDDEN_SURFACES),
        owner_only_access=owner_only_access,
        private_or_protected_staging_only=private_or_protected_staging_only,
        missing_evidence_flags=missing_evidence_flags,
        stale_state_flags=stale_state_flags,
        contradiction_flags=contradiction_flags,
        privacy_flags=privacy_flags,
        limitations=limitations,
    )
    packet.update({key: _json_safe(val) for key, val in data.items() if key not in packet})
    return packet



def validate_private_project_chat_owner_preview_packet_v1(packet: Any) -> dict[str, Any]:
    raw = _as_mapping(packet)
    blocked_labels: list[str] = []

    _require_owner_scope(raw, blocked_labels)
    _validate_packet_type(_safe_str(raw.get("preview_packet_type")), blocked_labels)
    _validate_status(_safe_str(raw.get("preview_status")), blocked_labels)
    _validate_readiness_label(_safe_str(raw.get("readiness_label")), blocked_labels)
    _validate_text_boundaries(raw, blocked_labels)

    shell_validations = _validate_nested_packets(raw, blocked_labels)

    if not _safe_bool(raw.get("owner_only_access", False)):
        blocked_labels.append("owner_only_access_false")
    if not _safe_bool(raw.get("private_or_protected_staging_only", False)):
        blocked_labels.append("private_or_protected_staging_only_false")

    denied_authority = _normalize_preview_denied_authority(raw.get("denied_authority"))
    for field, value in denied_authority.items():
        if value:
            blocked_labels.append(f"denied_authority_enabled_{field}")

    if not raw.get("allowed_preview_surfaces"):
        blocked_labels.append("missing_allowed_preview_surfaces")
    if not raw.get("forbidden_preview_surfaces"):
        blocked_labels.append("missing_forbidden_preview_surfaces")

    blocked = bool(blocked_labels)
    preview_status = _safe_str(raw.get("preview_status"))
    if blocked and preview_status != "preview_invalid":
        preview_status = "preview_invalid"
    if not preview_status or preview_status not in OWNER_PREVIEW_STATUSES_V1:
        preview_status = "preview_invalid"
        if "unknown_preview_status" not in blocked_labels:
            blocked_labels.append("unknown_preview_status")
        blocked = True

    packet_type = _safe_str(raw.get("preview_packet_type"))
    if not packet_type or packet_type not in OWNER_PREVIEW_PACKET_TYPES_V1:
        if "unknown_preview_packet_type" not in blocked_labels:
            blocked_labels.append("unknown_preview_packet_type")
        blocked = True
        packet_type = "preview_validation_summary"

    readiness_label = _safe_str(raw.get("readiness_label"))
    if not readiness_label or readiness_label not in OWNER_PREVIEW_READINESS_LABELS_V1:
        if "unknown_readiness_label" not in blocked_labels:
            blocked_labels.append("unknown_readiness_label")
        blocked = True
        readiness_label = "not_preview_ready"

    classification = _classification_for_packet_type(packet_type, blocked, preview_status)

    result = {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "preview_packet": _json_safe(raw),
        "blocked": blocked,
        "blocked_labels": _dedupe(blocked_labels),
        "classification": classification,
        "status": preview_status,
        "preview_status": preview_status,
        "preview_packet_type": packet_type,
        "readiness_label": readiness_label,
        "user_visible_status": _safe_str(raw.get("user_visible_status")),
        "owner_visible_summary": _safe_str(raw.get("owner_visible_summary")),
        "operator_visible_summary": _safe_str(raw.get("operator_visible_summary")),
        "redaction_summary": _safe_str(raw.get("redaction_summary")),
        "shell_validation": shell_validations["shell_validation"],
        "dry_run_validation": shell_validations["dry_run_validation"],
        "consumption_plan_validation": shell_validations["consumption_plan_validation"],
        "answer_plan_validation": shell_validations["answer_plan_validation"],
        "denied_authority": denied_authority,
    }
    return result



def classify_private_project_chat_owner_preview_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_private_project_chat_owner_preview_packet_v1(packet)
    classification = validation["classification"]
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "classification": classification,
        "preview_status": validation["preview_status"],
        "readiness_label": validation["readiness_label"],
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "preview_packet_type": validation["preview_packet_type"],
        "preview_packet": validation["preview_packet"],
    }



def summarize_private_project_chat_owner_preview_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_private_project_chat_owner_preview_packet_v1(packet)
    preview_packet = validation["preview_packet"]
    packet_type = validation["preview_packet_type"]
    status = validation["preview_status"]
    readiness_label = validation["readiness_label"]
    blocked = validation["blocked"]
    summary_text = (
        "Private owner preview: metadata-only. "
        f"status={status}; packet={packet_type}; readiness={readiness_label}; blocked={_safe_str(blocked)}."
    )
    if blocked:
        summary_text = "Private owner preview: metadata-only and blocked."
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "summary_text": summary_text,
        "preview_status": status,
        "readiness_label": readiness_label,
        "classification": validation["classification"],
        "blocked": blocked,
        "blocked_labels": validation["blocked_labels"],
        "preview_packet_type": packet_type,
        "preview_packet_id": _safe_str(preview_packet.get("preview_packet_id")),
        "owner_visible_summary": validation["owner_visible_summary"],
        "operator_visible_summary": validation["operator_visible_summary"],
        "user_visible_status": validation["user_visible_status"],
    }



def build_initial_private_project_chat_owner_preview_examples_v1() -> list[dict[str, Any]]:
    base = {
        "project_id": "project-001",
        "owner_user_scope": "owner-user",
        "tenant_account_scope": "tenant-a",
        "source_scope": "project_metadata_only",
    }
    examples: list[dict[str, Any]] = []
    for packet_type in OWNER_PREVIEW_PACKET_TYPES_V1:
        examples.append(
            build_private_project_chat_owner_preview_packet_v1(
                base,
                preview_packet_type=packet_type,
                preview_status=_preview_status_for_packet_type(packet_type, packet_type == "preview_shell_blocked_summary"),
                readiness_label=_readiness_label_for_packet_type(packet_type, packet_type == "preview_shell_blocked_summary", _preview_status_for_packet_type(packet_type, packet_type == "preview_shell_blocked_summary")),
            )
        )
    return examples
