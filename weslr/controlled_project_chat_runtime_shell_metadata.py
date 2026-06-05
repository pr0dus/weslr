"""Metadata-only helpers for the controlled WESLR project-chat runtime shell.

This module is intentionally pure, deterministic, synthetic/example-safe,
and fail-closed.
It builds and validates shell metadata packets only.

It does not perform file I/O, network I/O, shell execution, runtime wiring,
retrieval, model calls, tool execution, external actions, persistence, UI
consumption, or final answer generation.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

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

HELPER_TYPE_V1 = "weslr_controlled_project_chat_runtime_shell_metadata_v1"
SCHEMA_VERSION_V1 = "project_chat_controlled_runtime_shell_metadata_v1"

SHELL_STATES_V1 = (
    "shell_not_enabled",
    "shell_design_only",
    "shell_metadata_dry_run_only",
    "shell_approval_required",
    "shell_operator_review_required",
    "shell_blocked",
    "shell_ready_for_future_private_dry_run",
    "shell_not_ready_for_live_runtime",
)

SHELL_DECISIONS_V1 = (
    "block_before_runtime",
    "build_dry_run_metadata",
    "build_consumption_plan_metadata",
    "request_clarification_metadata",
    "request_user_approval_metadata",
    "request_operator_review_metadata",
    "prepare_answer_plan_metadata_candidate",
    "prepare_retrieval_request_metadata_candidate",
    "prepare_tool_lane_candidate_metadata",
    "prepare_persistence_candidate_metadata",
    "refuse_private_mechanism_disclosure",
    "refuse_runtime_wiring",
)

SHELL_PACKET_TYPES_V1 = (
    "shell_decision_packet",
    "shell_blocked_packet",
    "shell_clarification_packet",
    "shell_approval_request_packet",
    "shell_operator_review_packet",
    "shell_answer_plan_candidate_packet",
    "shell_retrieval_request_candidate_packet",
    "shell_tool_lane_candidate_packet",
    "shell_persistence_candidate_packet",
    "shell_observability_packet",
)

SHELL_DENIED_AUTHORITY_FIELDS_V1 = (
    "runtime_wiring_authority",
    "chat" + "_" + "responder_authority",
    "final_answer_generation_implementation_authority",
    "retrieval_execution_authority",
    "searxng_execution_authority",
    "storage_database_authority",
    "weslr_io_authority",
    "project_state_mutation_authority",
    "memory_mutation_authority",
    "tool_execution_authority",
    "external_action_authority",
    "ui_consumption_authority",
    "private_mechanism_disclosure_authority",
    "public_product_readiness_authority",
    "autonomous_self_improvement_authority",
)

_DEFAULT_FALSE_DENIED_AUTHORITY = {field: False for field in SHELL_DENIED_AUTHORITY_FIELDS_V1}


def allowed_controlled_project_chat_shell_states_v1() -> tuple[str, ...]:
    return SHELL_STATES_V1



def allowed_controlled_project_chat_shell_decisions_v1() -> tuple[str, ...]:
    return SHELL_DECISIONS_V1



def allowed_controlled_project_chat_shell_packet_types_v1() -> tuple[str, ...]:
    return SHELL_PACKET_TYPES_V1



def to_controlled_project_chat_shell_json_safe_v1(value: Any) -> Any:
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



def _normalize_refs(value: Any) -> list[str]:
    return _dedupe(_safe_list(value))



def _normalize_flags(value: Any) -> list[str]:
    return _dedupe(_safe_list(value))



def _normalize_denied_authority(value: Any) -> dict[str, bool]:
    payload = dict(_DEFAULT_FALSE_DENIED_AUTHORITY)
    raw = _as_mapping(value)
    for field in SHELL_DENIED_AUTHORITY_FIELDS_V1:
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



def _normalize_metadata_field(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in value.items()}
    return {}



def _validate_allowed_value(value: str, allowed: tuple[str, ...], field_name: str, blocked_labels: list[str]) -> None:
    if not value or value not in allowed:
        blocked_labels.append(f"unknown_{field_name}")



def _default_shell_state(decision: str, packet_type: str) -> str:
    if packet_type == "shell_blocked_packet" or decision in {"block_before_runtime", "refuse_private_mechanism_disclosure", "refuse_runtime_wiring"}:
        return "shell_blocked"
    if packet_type == "shell_approval_request_packet" or decision == "request_user_approval_metadata":
        return "shell_approval_required"
    if packet_type == "shell_operator_review_packet" or decision == "request_operator_review_metadata":
        return "shell_operator_review_required"
    if packet_type in {
        "shell_answer_plan_candidate_packet",
        "shell_retrieval_request_candidate_packet",
        "shell_tool_lane_candidate_packet",
        "shell_persistence_candidate_packet",
        "shell_clarification_packet",
    } or decision in {
        "request_clarification_metadata",
        "prepare_answer_plan_metadata_candidate",
        "prepare_retrieval_request_metadata_candidate",
        "prepare_tool_lane_candidate_metadata",
        "prepare_persistence_candidate_metadata",
    }:
        return "shell_metadata_dry_run_only"
    if decision in {"build_dry_run_metadata", "build_consumption_plan_metadata"} or packet_type in {"shell_decision_packet", "shell_observability_packet"}:
        return "shell_design_only"
    return "shell_design_only"



def _default_packet_type(decision: str) -> str:
    if decision in {"block_before_runtime", "refuse_private_mechanism_disclosure", "refuse_runtime_wiring"}:
        return "shell_blocked_packet"
    if decision == "request_clarification_metadata":
        return "shell_clarification_packet"
    if decision == "request_user_approval_metadata":
        return "shell_approval_request_packet"
    if decision == "request_operator_review_metadata":
        return "shell_operator_review_packet"
    if decision == "prepare_answer_plan_metadata_candidate":
        return "shell_answer_plan_candidate_packet"
    if decision == "prepare_retrieval_request_metadata_candidate":
        return "shell_retrieval_request_candidate_packet"
    if decision == "prepare_tool_lane_candidate_metadata":
        return "shell_tool_lane_candidate_packet"
    if decision == "prepare_persistence_candidate_metadata":
        return "shell_persistence_candidate_packet"
    if decision in {"build_dry_run_metadata", "build_consumption_plan_metadata"}:
        return "shell_decision_packet"
    return "shell_observability_packet"



def _default_decision_for_packet_type(packet_type: str) -> str:
    if packet_type == "shell_blocked_packet":
        return "block_before_runtime"
    if packet_type == "shell_clarification_packet":
        return "request_clarification_metadata"
    if packet_type == "shell_approval_request_packet":
        return "request_user_approval_metadata"
    if packet_type == "shell_operator_review_packet":
        return "request_operator_review_metadata"
    if packet_type == "shell_answer_plan_candidate_packet":
        return "prepare_answer_plan_metadata_candidate"
    if packet_type == "shell_retrieval_request_candidate_packet":
        return "prepare_retrieval_request_metadata_candidate"
    if packet_type == "shell_tool_lane_candidate_packet":
        return "prepare_tool_lane_candidate_metadata"
    if packet_type == "shell_persistence_candidate_packet":
        return "prepare_persistence_candidate_metadata"
    if packet_type in {"shell_decision_packet", "shell_observability_packet"}:
        return "build_dry_run_metadata"
    return "build_dry_run_metadata"



def _default_blocked_authority(decision: str, packet_type: str) -> str:
    if decision == "refuse_private_mechanism_disclosure":
        return "private_mechanism_boundary"
    if decision in {"block_before_runtime", "refuse_runtime_wiring"} or packet_type == "shell_blocked_packet":
        return "runtime_wiring_boundary"
    if packet_type == "shell_approval_request_packet" or decision == "request_user_approval_metadata":
        return "approval_boundary"
    if packet_type == "shell_operator_review_packet" or decision == "request_operator_review_metadata":
        return "operator_review_boundary"
    if packet_type == "shell_clarification_packet" or decision == "request_clarification_metadata":
        return "clarification_boundary"
    if packet_type == "shell_answer_plan_candidate_packet" or decision == "prepare_answer_plan_metadata_candidate":
        return "answer_plan_candidate_boundary"
    if packet_type == "shell_retrieval_request_candidate_packet" or decision == "prepare_retrieval_request_metadata_candidate":
        return "retrieval_candidate_boundary"
    if packet_type == "shell_tool_lane_candidate_packet" or decision == "prepare_tool_lane_candidate_metadata":
        return "tool_lane_candidate_boundary"
    if packet_type == "shell_persistence_candidate_packet" or decision == "prepare_persistence_candidate_metadata":
        return "persistence_candidate_boundary"
    if decision in {"build_dry_run_metadata", "build_consumption_plan_metadata"} or packet_type in {"shell_decision_packet", "shell_observability_packet"}:
        return "metadata_orchestration_boundary"
    return "metadata_orchestration_boundary"



def _default_user_visible_status(decision: str, packet_type: str, shell_state: str) -> str:
    if packet_type == "shell_blocked_packet" or shell_state == "shell_blocked":
        return "This is blocked until a future approved boundary exists."
    if packet_type == "shell_clarification_packet" or decision == "request_clarification_metadata":
        return "I need one clarification before continuing."
    if packet_type == "shell_approval_request_packet" or decision == "request_user_approval_metadata":
        return "This needs approval before deeper review."
    if packet_type == "shell_operator_review_packet" or decision == "request_operator_review_metadata":
        return "This needs operator review before continuing."
    if packet_type in {
        "shell_answer_plan_candidate_packet",
        "shell_retrieval_request_candidate_packet",
        "shell_tool_lane_candidate_packet",
        "shell_persistence_candidate_packet",
    }:
        return "This can only be prepared as a candidate."
    if decision in {"build_dry_run_metadata", "build_consumption_plan_metadata"} or packet_type in {"shell_decision_packet", "shell_observability_packet"}:
        return "Metadata only."
    return "Metadata only."



def _default_operator_visible_summary(shell_packet: Mapping[str, Any]) -> str:
    nested_counts = sum(
        1
        for field in (
            "message_metadata",
            "project_state_metadata",
            "memory_state_metadata",
            "continuity_metadata",
            "evidence_retrieval_metadata",
            "answer_plan_metadata",
            "dry_run_metadata",
            "consumption_plan_metadata",
            "operator_review_metadata",
            "approval_metadata",
        )
        if _as_mapping(shell_packet.get(field))
    )
    return (
        f"{_safe_str(shell_packet.get('shell_packet_type'))} | "
        f"{_safe_str(shell_packet.get('shell_decision'))} | "
        f"{_safe_str(shell_packet.get('shell_state'))} | "
        f"nested={nested_counts}"
    )



def _build_default_message_metadata(shell_packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "project_id": _safe_str(shell_packet.get("project_id")),
        "owner_user_scope": _safe_str(shell_packet.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(shell_packet.get("tenant_account_scope")),
        "source_scope": _safe_str(shell_packet.get("source_scope")),
        "message_intent_class": "project-chat",
        "message_status": "metadata only",
        "operator_visible_summary": "message intake metadata only",
        "denied_authority": dict(_DEFAULT_FALSE_DENIED_AUTHORITY),
    }



def _build_default_project_state_metadata(shell_packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "project_id": _safe_str(shell_packet.get("project_id")),
        "owner_user_scope": _safe_str(shell_packet.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(shell_packet.get("tenant_account_scope")),
        "source_scope": _safe_str(shell_packet.get("source_scope")),
        "project_state_status": "metadata only",
        "operator_visible_summary": "project context metadata only",
        "denied_authority": dict(_DEFAULT_FALSE_DENIED_AUTHORITY),
    }



def _build_default_memory_state_metadata(shell_packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "project_id": _safe_str(shell_packet.get("project_id")),
        "owner_user_scope": _safe_str(shell_packet.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(shell_packet.get("tenant_account_scope")),
        "source_scope": _safe_str(shell_packet.get("source_scope")),
        "memory_state_status": "metadata only",
        "operator_visible_summary": "memory metadata only",
        "denied_authority": dict(_DEFAULT_FALSE_DENIED_AUTHORITY),
    }



def _build_default_continuity_metadata(shell_packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "project_id": _safe_str(shell_packet.get("project_id")),
        "owner_user_scope": _safe_str(shell_packet.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(shell_packet.get("tenant_account_scope")),
        "source_scope": _safe_str(shell_packet.get("source_scope")),
        "continuity_status": "metadata only",
        "operator_visible_summary": "continuity metadata only",
        "denied_authority": dict(_DEFAULT_FALSE_DENIED_AUTHORITY),
    }



def _build_default_evidence_retrieval_metadata(shell_packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "project_id": _safe_str(shell_packet.get("project_id")),
        "owner_user_scope": _safe_str(shell_packet.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(shell_packet.get("tenant_account_scope")),
        "source_scope": _safe_str(shell_packet.get("source_scope")),
        "retrieval_need_class": "none",
        "retrieval_status": "metadata only",
        "operator_visible_summary": "retrieval decision metadata only",
        "denied_authority": dict(_DEFAULT_FALSE_DENIED_AUTHORITY),
    }



def _build_default_operator_review_metadata(shell_packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "project_id": _safe_str(shell_packet.get("project_id")),
        "owner_user_scope": _safe_str(shell_packet.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(shell_packet.get("tenant_account_scope")),
        "source_scope": _safe_str(shell_packet.get("source_scope")),
        "operator_review_status": "metadata only",
        "operator_visible_summary": "operator review metadata only",
        "denied_authority": dict(_DEFAULT_FALSE_DENIED_AUTHORITY),
    }



def _build_default_approval_metadata(shell_packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "project_id": _safe_str(shell_packet.get("project_id")),
        "owner_user_scope": _safe_str(shell_packet.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(shell_packet.get("tenant_account_scope")),
        "source_scope": _safe_str(shell_packet.get("source_scope")),
        "approval_status": "metadata only",
        "operator_visible_summary": "approval metadata only",
        "denied_authority": dict(_DEFAULT_FALSE_DENIED_AUTHORITY),
    }



def _base_answer_plan_payload(shell_packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "project_id": _safe_str(shell_packet.get("project_id")),
        "owner_user_scope": _safe_str(shell_packet.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(shell_packet.get("tenant_account_scope")),
        "source_scope": _safe_str(shell_packet.get("source_scope")),
        "user_intent_class": _safe_str(shell_packet.get("message_metadata", {}).get("message_intent_class")) or "project-chat",
        "answer_mode": "clarifying_question",
        "allowed_answer_scope": "current_message_only",
        "answer_status": "clarification_required",
        "user_visible_status": "clarification needed",
        "operator_visible_summary": "clarification required; metadata only",
        "denied_authority": {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
    }



def _base_dry_run_payload(shell_packet: Mapping[str, Any], answer_plan_payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "project_id": _safe_str(shell_packet.get("project_id")),
        "owner_user_scope": _safe_str(shell_packet.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(shell_packet.get("tenant_account_scope")),
        "source_scope": _safe_str(shell_packet.get("source_scope")),
        "user_intent_class": _safe_str(shell_packet.get("message_metadata", {}).get("message_intent_class")) or "project-chat",
        "dry_run_status": "dry_run_valid_metadata_only",
        "dry_run_decision": "proceed_to_answer_plan_metadata",
        "retrieval_need_class": "none",
        "user_visible_status": "metadata only",
        "operator_visible_summary": "shell dry-run metadata only",
        "denied_authority": {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
        "answer_plan_payload": answer_plan_payload,
    }



def _base_consumption_plan_payload(shell_packet: Mapping[str, Any], dry_run_payload: Mapping[str, Any], answer_plan_payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "project_id": _safe_str(shell_packet.get("project_id")),
        "owner_user_scope": _safe_str(shell_packet.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(shell_packet.get("tenant_account_scope")),
        "source_scope": _safe_str(shell_packet.get("source_scope")),
        "dry_run_metadata": dry_run_payload,
        "consumption_status": "consumption_plan_valid_metadata_only",
        "consumption_action": "prepare_answer_plan_metadata_only",
        "allowed_next_metadata_step": "prepare_answer_plan_metadata_only",
        "user_visible_status": "answer-plan metadata only",
        "operator_visible_summary": "answer-plan metadata only",
        "denied_authority": {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
        "answer_plan_metadata": answer_plan_payload,
    }



def build_controlled_project_chat_shell_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _coalesce_payload(payload, **overrides)

    decision = _safe_str(data.get("shell_decision"))
    packet_type = _safe_str(data.get("shell_packet_type"))
    if not decision:
        decision = _default_decision_for_packet_type(packet_type)
    if not packet_type:
        packet_type = _default_packet_type(decision)
    shell_state = _safe_str(data.get("shell_state")) or _default_shell_state(decision, packet_type)

    shell_packet = {
        "schema_version": _safe_str(data.get("schema_version")) or SCHEMA_VERSION_V1,
        "shell_packet_id": _safe_str(data.get("shell_packet_id")),
        "shell_state": shell_state,
        "shell_decision": decision,
        "shell_packet_type": packet_type,
        "project_id": _safe_str(data.get("project_id")),
        "owner_user_scope": _safe_str(data.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(data.get("tenant_account_scope")),
        "source_scope": _safe_str(data.get("source_scope")),
        "message_metadata": _normalize_metadata_field(data.get("message_metadata")),
        "project_state_metadata": _normalize_metadata_field(data.get("project_state_metadata")),
        "memory_state_metadata": _normalize_metadata_field(data.get("memory_state_metadata")),
        "continuity_metadata": _normalize_metadata_field(data.get("continuity_metadata")),
        "evidence_retrieval_metadata": _normalize_metadata_field(data.get("evidence_retrieval_metadata")),
        "answer_plan_metadata": _normalize_metadata_field(data.get("answer_plan_metadata")),
        "dry_run_metadata": _normalize_metadata_field(data.get("dry_run_metadata")),
        "consumption_plan_metadata": _normalize_metadata_field(data.get("consumption_plan_metadata")),
        "operator_review_metadata": _normalize_metadata_field(data.get("operator_review_metadata")),
        "approval_metadata": _normalize_metadata_field(data.get("approval_metadata")),
        "selected_next_metadata_step": _safe_str(data.get("selected_next_metadata_step")),
        "blocked_authority": _safe_str(data.get("blocked_authority")),
        "approval_refs": _normalize_refs(data.get("approval_refs")),
        "operator_visibility_refs": _normalize_refs(data.get("operator_visibility_refs")),
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
    }

    if not shell_packet["project_id"]:
        for nested in (
            shell_packet["message_metadata"],
            shell_packet["project_state_metadata"],
            shell_packet["memory_state_metadata"],
            shell_packet["continuity_metadata"],
            shell_packet["evidence_retrieval_metadata"],
            shell_packet["answer_plan_metadata"],
            shell_packet["dry_run_metadata"],
            shell_packet["consumption_plan_metadata"],
            shell_packet["operator_review_metadata"],
            shell_packet["approval_metadata"],
        ):
            if _safe_str(nested.get("project_id")):
                shell_packet["project_id"] = _safe_str(nested.get("project_id"))
                break
    if not shell_packet["owner_user_scope"]:
        for nested in (
            shell_packet["message_metadata"],
            shell_packet["project_state_metadata"],
            shell_packet["memory_state_metadata"],
            shell_packet["continuity_metadata"],
            shell_packet["evidence_retrieval_metadata"],
            shell_packet["answer_plan_metadata"],
            shell_packet["dry_run_metadata"],
            shell_packet["consumption_plan_metadata"],
            shell_packet["operator_review_metadata"],
            shell_packet["approval_metadata"],
        ):
            if _safe_str(nested.get("owner_user_scope")):
                shell_packet["owner_user_scope"] = _safe_str(nested.get("owner_user_scope"))
                break
    if not shell_packet["tenant_account_scope"]:
        for nested in (
            shell_packet["message_metadata"],
            shell_packet["project_state_metadata"],
            shell_packet["memory_state_metadata"],
            shell_packet["continuity_metadata"],
            shell_packet["evidence_retrieval_metadata"],
            shell_packet["answer_plan_metadata"],
            shell_packet["dry_run_metadata"],
            shell_packet["consumption_plan_metadata"],
            shell_packet["operator_review_metadata"],
            shell_packet["approval_metadata"],
        ):
            if _safe_str(nested.get("tenant_account_scope")):
                shell_packet["tenant_account_scope"] = _safe_str(nested.get("tenant_account_scope"))
                break
    if not shell_packet["source_scope"]:
        for nested in (
            shell_packet["message_metadata"],
            shell_packet["project_state_metadata"],
            shell_packet["memory_state_metadata"],
            shell_packet["continuity_metadata"],
            shell_packet["evidence_retrieval_metadata"],
            shell_packet["answer_plan_metadata"],
            shell_packet["dry_run_metadata"],
            shell_packet["consumption_plan_metadata"],
            shell_packet["operator_review_metadata"],
            shell_packet["approval_metadata"],
        ):
            if _safe_str(nested.get("source_scope")):
                shell_packet["source_scope"] = _safe_str(nested.get("source_scope"))
                break

    if not shell_packet["shell_packet_id"]:
        digest_source = {k: v for k, v in shell_packet.items() if k not in {"shell_packet_id", "operator_visible_summary"}}
        shell_packet["shell_packet_id"] = f"controlled-project-chat-runtime-shell-{_stable_digest(digest_source)[:16]}"

    if not shell_packet["blocked_authority"]:
        shell_packet["blocked_authority"] = _default_blocked_authority(shell_packet["shell_decision"], shell_packet["shell_packet_type"])
    if not shell_packet["selected_next_metadata_step"]:
        shell_packet["selected_next_metadata_step"] = shell_packet["shell_decision"]
    if not shell_packet["user_visible_status"]:
        shell_packet["user_visible_status"] = _default_user_visible_status(shell_packet["shell_decision"], shell_packet["shell_packet_type"], shell_packet["shell_state"])
    if not shell_packet["operator_visible_summary"]:
        shell_packet["operator_visible_summary"] = _default_operator_visible_summary(shell_packet)

    if not shell_packet["message_metadata"]:
        shell_packet["message_metadata"] = _build_default_message_metadata(shell_packet)
    if not shell_packet["project_state_metadata"]:
        shell_packet["project_state_metadata"] = _build_default_project_state_metadata(shell_packet)
    if not shell_packet["memory_state_metadata"]:
        shell_packet["memory_state_metadata"] = _build_default_memory_state_metadata(shell_packet)
    if not shell_packet["continuity_metadata"]:
        shell_packet["continuity_metadata"] = _build_default_continuity_metadata(shell_packet)
    if not shell_packet["evidence_retrieval_metadata"]:
        shell_packet["evidence_retrieval_metadata"] = _build_default_evidence_retrieval_metadata(shell_packet)
    if not shell_packet["operator_review_metadata"]:
        shell_packet["operator_review_metadata"] = _build_default_operator_review_metadata(shell_packet)
    if not shell_packet["approval_metadata"]:
        shell_packet["approval_metadata"] = _build_default_approval_metadata(shell_packet)

    # The nested reviewed metadata packets are optional inputs; if callers do not
    # provide them, we keep safe metadata-only defaults for shell orchestration.
    if not shell_packet["answer_plan_metadata"]:
        answer_plan_payload = _base_answer_plan_payload(shell_packet)
        shell_packet["answer_plan_metadata"] = build_project_chat_answer_plan_v1(answer_plan_payload)
    if not shell_packet["dry_run_metadata"]:
        dry_run_payload = _base_dry_run_payload(shell_packet, shell_packet["answer_plan_metadata"])
        shell_packet["dry_run_metadata"] = build_project_chat_runtime_dry_run_v1(dry_run_payload)
    if not shell_packet["consumption_plan_metadata"]:
        consumption_plan_payload = _base_consumption_plan_payload(shell_packet, shell_packet["dry_run_metadata"], shell_packet["answer_plan_metadata"])
        shell_packet["consumption_plan_metadata"] = build_project_chat_dry_run_consumption_plan_v1(consumption_plan_payload)

    return shell_packet



def _validate_user_visible_status(value: str, blocked_labels: list[str]) -> None:
    lowered = _safe_str(value).lower()
    for phrase in ANSWER_PLAN_USER_VISIBLE_STATUS_FORBIDDEN_PHRASES_V1:
        if phrase and phrase in lowered:
            blocked_labels.append("user_visible_status_forbidden_phrase")
            break



def _nested_validation_or_empty(value: Any, validator, label: str) -> dict[str, Any]:
    candidate = _as_mapping(value)
    if not candidate:
        return {"present": False, "blocked": False, "blocked_labels": [], "classification": "absent"}
    validation = validator(candidate)
    if validation.get("blocked"):
        validation = dict(validation)
        validation.setdefault("blocked_labels", [])
        validation["blocked_labels"] = list(validation["blocked_labels"])
        validation["blocked"] = True
        validation["nested_label"] = label
    return validation



def validate_controlled_project_chat_shell_packet_v1(packet: Any) -> dict[str, Any]:
    candidate = build_controlled_project_chat_shell_packet_v1(packet)
    blocked_labels: list[str] = []

    if candidate.get("schema_version") != SCHEMA_VERSION_V1:
        blocked_labels.append("unknown_schema_version")

    required_fields = (
        "shell_packet_id",
        "shell_state",
        "shell_decision",
        "shell_packet_type",
        "project_id",
        "owner_user_scope",
        "tenant_account_scope",
        "source_scope",
        "selected_next_metadata_step",
        "user_visible_status",
        "operator_visible_summary",
        "blocked_authority",
    )
    for field in required_fields:
        if not _safe_str(candidate.get(field)):
            blocked_labels.append(f"missing_{field}")

    _validate_allowed_value(candidate.get("shell_state", ""), SHELL_STATES_V1, "shell_state", blocked_labels)
    _validate_allowed_value(candidate.get("shell_decision", ""), SHELL_DECISIONS_V1, "shell_decision", blocked_labels)
    _validate_allowed_value(candidate.get("shell_packet_type", ""), SHELL_PACKET_TYPES_V1, "shell_packet_type", blocked_labels)

    _validate_user_visible_status(candidate.get("user_visible_status", ""), blocked_labels)

    for field, value in candidate.get("denied_authority", {}).items():
        if field not in SHELL_DENIED_AUTHORITY_FIELDS_V1:
            blocked_labels.append(f"unknown_denied_authority_field_{field}")
        elif _safe_bool(value):
            blocked_labels.append(f"denied_authority_must_remain_false_{field}")

    if candidate.get("shell_packet_type") == "shell_blocked_packet" and candidate.get("shell_decision") not in {"block_before_runtime", "refuse_private_mechanism_disclosure", "refuse_runtime_wiring"}:
        blocked_labels.append("blocked_packet_requires_blocking_decision")
    if candidate.get("shell_packet_type") == "shell_clarification_packet" and candidate.get("shell_decision") != "request_clarification_metadata":
        blocked_labels.append("clarification_packet_requires_clarification_decision")
    if candidate.get("shell_packet_type") == "shell_approval_request_packet" and candidate.get("shell_decision") != "request_user_approval_metadata":
        blocked_labels.append("approval_packet_requires_approval_decision")
    if candidate.get("shell_packet_type") == "shell_operator_review_packet" and candidate.get("shell_decision") != "request_operator_review_metadata":
        blocked_labels.append("operator_review_packet_requires_operator_review_decision")
    if candidate.get("shell_packet_type") == "shell_answer_plan_candidate_packet" and candidate.get("shell_decision") != "prepare_answer_plan_metadata_candidate":
        blocked_labels.append("answer_plan_candidate_packet_requires_answer_plan_candidate_decision")
    if candidate.get("shell_packet_type") == "shell_retrieval_request_candidate_packet" and candidate.get("shell_decision") != "prepare_retrieval_request_metadata_candidate":
        blocked_labels.append("retrieval_request_candidate_packet_requires_retrieval_candidate_decision")
    if candidate.get("shell_packet_type") == "shell_tool_lane_candidate_packet" and candidate.get("shell_decision") != "prepare_tool_lane_candidate_metadata":
        blocked_labels.append("tool_lane_candidate_packet_requires_tool_candidate_decision")
    if candidate.get("shell_packet_type") == "shell_persistence_candidate_packet" and candidate.get("shell_decision") != "prepare_persistence_candidate_metadata":
        blocked_labels.append("persistence_candidate_packet_requires_persistence_candidate_decision")
    if candidate.get("shell_packet_type") == "shell_decision_packet" and candidate.get("shell_decision") not in {"build_dry_run_metadata", "build_consumption_plan_metadata"}:
        blocked_labels.append("decision_packet_requires_build_decision")
    if candidate.get("shell_packet_type") == "shell_observability_packet" and candidate.get("shell_decision") not in {"build_dry_run_metadata", "build_consumption_plan_metadata"}:
        blocked_labels.append("observability_packet_requires_build_decision")

    dry_run_validation = _nested_validation_or_empty(candidate.get("dry_run_metadata"), validate_project_chat_runtime_dry_run_v1, "invalid_nested_dry_run_metadata")
    if dry_run_validation.get("blocked"):
        blocked_labels.append("invalid_nested_dry_run_metadata")

    consumption_plan_validation = _nested_validation_or_empty(candidate.get("consumption_plan_metadata"), validate_project_chat_dry_run_consumption_plan_v1, "invalid_nested_consumption_plan_metadata")
    if consumption_plan_validation.get("blocked"):
        blocked_labels.append("invalid_nested_consumption_plan_metadata")

    answer_plan_validation = _nested_validation_or_empty(candidate.get("answer_plan_metadata"), validate_project_chat_answer_plan_v1, "invalid_nested_answer_plan_metadata")
    if answer_plan_validation.get("blocked"):
        blocked_labels.append("invalid_nested_answer_plan_metadata")

    if _safe_str(candidate.get("selected_next_metadata_step")) not in SHELL_DECISIONS_V1 and _safe_str(candidate.get("selected_next_metadata_step")) != _safe_str(candidate.get("shell_decision")):
        blocked_labels.append("unknown_selected_next_metadata_step")

    blocked = bool(blocked_labels)
    classification = "blocked" if blocked else _classify_controlled_project_chat_shell_packet(candidate)
    status = "blocked" if blocked else "validated"

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "shell_packet": candidate,
        "blocked": blocked,
        "blocked_labels": blocked_labels,
        "classification": classification if not blocked else "blocked",
        "status": status,
        "shell_state": candidate["shell_state"],
        "shell_decision": candidate["shell_decision"],
        "shell_packet_type": candidate["shell_packet_type"],
        "selected_next_metadata_step": candidate["selected_next_metadata_step"],
        "user_visible_status": candidate["user_visible_status"],
        "operator_visible_summary": candidate["operator_visible_summary"],
        "dry_run_validation": dry_run_validation,
        "consumption_plan_validation": consumption_plan_validation,
        "answer_plan_validation": answer_plan_validation,
    }



def _classify_controlled_project_chat_shell_packet(packet: Mapping[str, Any]) -> str:
    packet_type = _safe_str(packet.get("shell_packet_type"))
    if packet_type == "shell_blocked_packet":
        return "blocked"
    if packet_type == "shell_clarification_packet":
        return "clarification_required"
    if packet_type == "shell_approval_request_packet":
        return "approval_required"
    if packet_type == "shell_operator_review_packet":
        return "operator_review_required"
    if packet_type == "shell_answer_plan_candidate_packet":
        return "answer_plan_candidate"
    if packet_type == "shell_retrieval_request_candidate_packet":
        return "retrieval_request_candidate"
    if packet_type == "shell_tool_lane_candidate_packet":
        return "tool_lane_candidate"
    if packet_type == "shell_persistence_candidate_packet":
        return "persistence_candidate"
    if packet_type == "shell_observability_packet":
        return "observability"
    return "decision"



def classify_controlled_project_chat_shell_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_controlled_project_chat_shell_packet_v1(packet)
    candidate = validation["shell_packet"]
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "classification": validation["classification"],
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "shell_packet_id": candidate["shell_packet_id"],
        "shell_state": candidate["shell_state"],
        "shell_decision": candidate["shell_decision"],
        "shell_packet_type": candidate["shell_packet_type"],
        "selected_next_metadata_step": candidate["selected_next_metadata_step"],
        "user_visible_status": candidate["user_visible_status"],
        "operator_visible_summary": candidate["operator_visible_summary"],
    }



def _summary_text_for_packet(packet: Mapping[str, Any], blocked: bool) -> str:
    status = "blocked" if blocked else _classify_controlled_project_chat_shell_packet(packet)
    return (
        f"{_safe_str(packet.get('shell_packet_type'))} | "
        f"{_safe_str(packet.get('shell_decision'))} | "
        f"{_safe_str(packet.get('shell_state'))} | "
        f"{status}"
    )



def summarize_controlled_project_chat_shell_packet_v1(packet: Any) -> dict[str, Any]:
    candidate = build_controlled_project_chat_shell_packet_v1(packet)
    validation = validate_controlled_project_chat_shell_packet_v1(candidate)
    summary_text = _summary_text_for_packet(candidate, validation["blocked"])
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "shell_packet_id": candidate["shell_packet_id"],
        "summary_text": summary_text,
        "shell_state": candidate["shell_state"],
        "shell_decision": candidate["shell_decision"],
        "shell_packet_type": candidate["shell_packet_type"],
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "selected_next_metadata_step": candidate["selected_next_metadata_step"],
        "user_visible_status": candidate["user_visible_status"],
        "operator_visible_summary": summary_text,
        "dry_run_blocked": validation["dry_run_validation"].get("blocked", False),
        "consumption_plan_blocked": validation["consumption_plan_validation"].get("blocked", False),
        "answer_plan_blocked": validation["answer_plan_validation"].get("blocked", False),
    }



def build_initial_controlled_project_chat_shell_examples_v1() -> list[dict[str, Any]]:
    base_answer_plan = build_project_chat_answer_plan_v1(_base_answer_plan_payload({"project_id": "project-001", "owner_user_scope": "owner-user", "tenant_account_scope": "tenant-a", "source_scope": "project_metadata_only", "message_metadata": {"message_intent_class": "project-chat"}}))
    base_dry_run = build_project_chat_runtime_dry_run_v1(_base_dry_run_payload({"project_id": "project-001", "owner_user_scope": "owner-user", "tenant_account_scope": "tenant-a", "source_scope": "project_metadata_only", "message_metadata": {"message_intent_class": "project-chat"}}, base_answer_plan))
    base_consumption = build_project_chat_dry_run_consumption_plan_v1(_base_consumption_plan_payload({"project_id": "project-001", "owner_user_scope": "owner-user", "tenant_account_scope": "tenant-a", "source_scope": "project_metadata_only", "message_metadata": {"message_intent_class": "project-chat"}}, base_dry_run, base_answer_plan))
    examples = [
        build_controlled_project_chat_shell_packet_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "shell_state": "shell_blocked",
                "shell_decision": "block_before_runtime",
                "shell_packet_type": "shell_blocked_packet",
                "blocked_authority": "runtime_wiring_boundary",
                "user_visible_status": "This is blocked until a future approved boundary exists.",
                "operator_visible_summary": "shell blocked; metadata only",
                "answer_plan_metadata": base_answer_plan,
                "dry_run_metadata": base_dry_run,
                "consumption_plan_metadata": base_consumption,
            }
        ),
        build_controlled_project_chat_shell_packet_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "shell_state": "shell_metadata_dry_run_only",
                "shell_decision": "request_clarification_metadata",
                "shell_packet_type": "shell_clarification_packet",
                "blocked_authority": "clarification_boundary",
                "user_visible_status": "I need one clarification before continuing.",
                "operator_visible_summary": "clarification packet; metadata only",
                "answer_plan_metadata": base_answer_plan,
                "dry_run_metadata": base_dry_run,
                "consumption_plan_metadata": base_consumption,
            }
        ),
        build_controlled_project_chat_shell_packet_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "shell_state": "shell_approval_required",
                "shell_decision": "request_user_approval_metadata",
                "shell_packet_type": "shell_approval_request_packet",
                "blocked_authority": "approval_boundary",
                "user_visible_status": "This needs approval before deeper review.",
                "operator_visible_summary": "approval request packet; metadata only",
                "answer_plan_metadata": base_answer_plan,
                "dry_run_metadata": base_dry_run,
                "consumption_plan_metadata": base_consumption,
            }
        ),
        build_controlled_project_chat_shell_packet_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "shell_state": "shell_operator_review_required",
                "shell_decision": "request_operator_review_metadata",
                "shell_packet_type": "shell_operator_review_packet",
                "blocked_authority": "operator_review_boundary",
                "user_visible_status": "This needs operator review before continuing.",
                "operator_visible_summary": "operator review packet; metadata only",
                "answer_plan_metadata": base_answer_plan,
                "dry_run_metadata": base_dry_run,
                "consumption_plan_metadata": base_consumption,
            }
        ),
        build_controlled_project_chat_shell_packet_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "shell_state": "shell_metadata_dry_run_only",
                "shell_decision": "prepare_answer_plan_metadata_candidate",
                "shell_packet_type": "shell_answer_plan_candidate_packet",
                "blocked_authority": "answer_plan_candidate_boundary",
                "user_visible_status": "This can only be prepared as a candidate.",
                "operator_visible_summary": "answer plan candidate packet; metadata only",
                "answer_plan_metadata": base_answer_plan,
                "dry_run_metadata": base_dry_run,
                "consumption_plan_metadata": base_consumption,
            }
        ),
        build_controlled_project_chat_shell_packet_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "shell_state": "shell_metadata_dry_run_only",
                "shell_decision": "prepare_retrieval_request_metadata_candidate",
                "shell_packet_type": "shell_retrieval_request_candidate_packet",
                "blocked_authority": "retrieval_candidate_boundary",
                "user_visible_status": "This can only be prepared as a candidate.",
                "operator_visible_summary": "retrieval candidate packet; metadata only",
                "answer_plan_metadata": base_answer_plan,
                "dry_run_metadata": base_dry_run,
                "consumption_plan_metadata": base_consumption,
            }
        ),
        build_controlled_project_chat_shell_packet_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "shell_state": "shell_metadata_dry_run_only",
                "shell_decision": "prepare_tool_lane_candidate_metadata",
                "shell_packet_type": "shell_tool_lane_candidate_packet",
                "blocked_authority": "tool_lane_candidate_boundary",
                "user_visible_status": "This can only be prepared as a candidate.",
                "operator_visible_summary": "tool lane candidate packet; metadata only",
                "answer_plan_metadata": base_answer_plan,
                "dry_run_metadata": base_dry_run,
                "consumption_plan_metadata": base_consumption,
            }
        ),
        build_controlled_project_chat_shell_packet_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "shell_state": "shell_metadata_dry_run_only",
                "shell_decision": "prepare_persistence_candidate_metadata",
                "shell_packet_type": "shell_persistence_candidate_packet",
                "blocked_authority": "persistence_candidate_boundary",
                "user_visible_status": "This can only be prepared as a candidate.",
                "operator_visible_summary": "persistence candidate packet; metadata only",
                "answer_plan_metadata": base_answer_plan,
                "dry_run_metadata": base_dry_run,
                "consumption_plan_metadata": base_consumption,
            }
        ),
        build_controlled_project_chat_shell_packet_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "shell_state": "shell_design_only",
                "shell_decision": "build_dry_run_metadata",
                "shell_packet_type": "shell_decision_packet",
                "blocked_authority": "metadata_orchestration_boundary",
                "user_visible_status": "Metadata only.",
                "operator_visible_summary": "decision packet; metadata only",
                "answer_plan_metadata": base_answer_plan,
                "dry_run_metadata": base_dry_run,
                "consumption_plan_metadata": base_consumption,
            }
        ),
        build_controlled_project_chat_shell_packet_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "shell_state": "shell_metadata_dry_run_only",
                "shell_decision": "build_consumption_plan_metadata",
                "shell_packet_type": "shell_observability_packet",
                "blocked_authority": "metadata_orchestration_boundary",
                "user_visible_status": "Metadata only.",
                "operator_visible_summary": "observability packet; metadata only",
                "answer_plan_metadata": base_answer_plan,
                "dry_run_metadata": base_dry_run,
                "consumption_plan_metadata": base_consumption,
            }
        ),
    ]
    return examples
