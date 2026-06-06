"""Metadata-only helpers for WESLR project-chat assembly/orchestration packets V1.

This module is intentionally pure, deterministic, synthetic/example-safe,
and fail-closed.
It assembles project-chat metadata packets only.

It does not perform file I/O, network I/O, shell execution, runtime wiring,
retrieval execution, model calls, tool execution, external actions,
persistence, UI consumption, live chat output, answer delivery, or final
answer generation.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

from weslr.project_chat_answer_plan_metadata_helpers import (
    DENIED_AUTHORITY_FIELDS_V1 as ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1,
    build_project_chat_answer_plan_v1,
    validate_project_chat_answer_plan_v1,
)
from weslr.project_chat_final_answer_generation import (
    FINAL_ANSWER_STATUSES_V1,
    build_project_chat_final_answer_packet_v1,
    validate_project_chat_final_answer_packet_v1,
)
from weslr.project_chat_rag_evidence_retrieval import (
    build_project_chat_evidence_packet_v1,
    validate_project_chat_evidence_packet_v1,
)

HELPER_TYPE_V1 = "weslr_project_chat_assembly_orchestration_packet_v1"
SCHEMA_VERSION_V1 = "project_chat_assembly_orchestration_packet_v1"

ASSEMBLY_MODES_V1 = (
    "blocked_orchestration",
    "candidate_orchestration",
    "metadata_only_assembly",
)

ASSEMBLY_STATUSES_V1 = (
    "assembly_valid_metadata_only",
    "blocked",
    "invalid",
)

DENIED_AUTHORITY_FIELDS_V1 = (
    "runtime_wiring_authority",
    "chat" + "_" + "responder_authority",
    "live_chat_output_authority",
    "answer_delivery_authority",
    "final_answer_generation_implementation_authority",
    "retrieval_execution_authority",
    "provider_call_authority",
    "model_call_authority",
    "search_call_authority",
    "tool_execution_authority",
    "external_action_authority",
    "persistence_authority",
    "storage_database_authority",
    "weslr_io_authority",
    "project_state_mutation_authority",
    "memory_mutation_authority",
    "hidden_memory_authority",
    "hidden_project_state_authority",
    "private_mechanism_disclosure_authority",
    "cross_user_leakage_authority",
    "public_product_readiness_authority",
    "unsupported_certainty_authority",
    "cognitive_research_run_authority",
    "cognitive_engine_authority",
    "autonomous_self_improvement_authority",
)

FORBIDDEN_LEAKAGE_PHRASES_V1 = (
    "unknown engine",
    "." + "weslr",
    "raw transcript",
    "raw prompt",
    "raw message",
    "hidden prompt",
    "system prompt",
    "private mechanism",
    "private content",
    "secret",
    "confidential",
    "live chat",
    "live chat output",
    "chat responder",
    "respond_chat",
    "generate_chat",
    "provider output",
    "model output",
    "search output",
    "tool output",
    "tool executed",
    "i executed",
    "i searched your private data",
    "i saved this project",
    "i remember this",
    "answer delivery",
    "send to user",
    "reply to user",
    "public readiness",
    "certified",
    "proof",
    "solved",
    "benchmark",
    "legal certainty",
    "medical certainty",
    "financial certainty",
    "professional certainty",
    "guaranteed",
    "cognitive engine",
    "cognitive research run",
)

_DEFAULT_FALSE_DENIED_AUTHORITY = {field: False for field in DENIED_AUTHORITY_FIELDS_V1}


def allowed_project_chat_assembly_modes_v1() -> tuple[str, ...]:
    return ASSEMBLY_MODES_V1


def allowed_project_chat_assembly_statuses_v1() -> tuple[str, ...]:
    return ASSEMBLY_STATUSES_V1


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


def _normalize_list(value: Any) -> list[str]:
    return _dedupe(_safe_list(value))


def _normalize_flags(value: Any) -> list[str]:
    return _dedupe(_safe_list(value))


def _normalize_denied_authority(value: Any) -> dict[str, bool]:
    payload = dict(_DEFAULT_FALSE_DENIED_AUTHORITY)
    raw = _as_mapping(value)
    for field in DENIED_AUTHORITY_FIELDS_V1:
        payload[field] = _safe_bool(raw.get(field, False))
    return payload


def _validate_allowed_value(value: str, allowed: tuple[str, ...], label: str, blocked_labels: list[str]) -> None:
    if not value:
        blocked_labels.append(f"missing_{label}")
    elif value not in allowed:
        blocked_labels.append(f"unknown_{label}")


def _coalesce_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = {}
    if isinstance(payload, Mapping):
        data.update(payload)
    elif payload is not None:
        data["payload"] = payload
    data.update(overrides)
    return data


def _normalize_user_request_metadata(payload: Mapping[str, Any]) -> dict[str, Any]:
    raw = _as_mapping(payload.get("user_request_metadata") or payload.get("request_metadata") or payload.get("user_request") or payload)
    return {
        "request_id": _safe_str(raw.get("request_id")) or _safe_str(payload.get("assembly_request_id")),
        "project_id": _safe_str(raw.get("project_id")) or _safe_str(payload.get("project_id")),
        "owner_user_scope": _safe_str(raw.get("owner_user_scope")) or _safe_str(payload.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(raw.get("tenant_account_scope")) or _safe_str(payload.get("tenant_account_scope")),
        "source_scope": _safe_str(raw.get("source_scope")) or _safe_str(payload.get("source_scope")),
        "user_intent_class": _safe_str(raw.get("user_intent_class")) or _safe_str(payload.get("user_intent_class")) or "project-chat",
        "message_ref": _safe_str(raw.get("message_ref")),
        "message_status": _safe_str(raw.get("message_status")) or "metadata only",
        "user_visible_status": _safe_str(raw.get("user_visible_status")) or _safe_str(payload.get("user_visible_status")),
        "operator_visible_summary": _safe_str(raw.get("operator_visible_summary")) or _safe_str(payload.get("operator_visible_summary")),
        "limitations": _normalize_flags(raw.get("limitations") or payload.get("limitations")),
        "privacy_flags": _normalize_flags(raw.get("privacy_flags") or payload.get("privacy_flags")),
        "uncertainty_flags": _normalize_flags(raw.get("uncertainty_flags") or payload.get("uncertainty_flags")),
        "stale_state_flags": _normalize_flags(raw.get("stale_state_flags") or payload.get("stale_state_flags")),
        "contradiction_flags": _normalize_flags(raw.get("contradiction_flags") or payload.get("contradiction_flags")),
        "missing_evidence_flags": _normalize_flags(raw.get("missing_evidence_flags") or payload.get("missing_evidence_flags")),
        "blocked_authority": _safe_str(raw.get("blocked_authority")) or _safe_str(payload.get("blocked_authority")),
        "denied_authority": _normalize_denied_authority(raw.get("denied_authority") or payload.get("denied_authority") or {}),
    }


def _normalize_project_context_metadata(payload: Mapping[str, Any]) -> dict[str, Any]:
    raw = _as_mapping(payload.get("project_context_metadata") or payload.get("project_context") or {})
    return {
        "project_state_refs": _normalize_list(raw.get("project_state_refs")),
        "memory_state_refs": _normalize_list(raw.get("memory_state_refs")),
        "continuity_state_refs": _normalize_list(raw.get("continuity_state_refs")),
        "gap_analysis_refs": _normalize_list(raw.get("gap_analysis_refs")),
        "tool_lane_candidate_refs": _normalize_list(raw.get("tool_lane_candidate_refs")),
        "approval_refs": _normalize_list(raw.get("approval_refs") or payload.get("approval_refs")),
        "user_correction_refs": _normalize_list(raw.get("user_correction_refs")),
        "state_truth_labels": _normalize_list(raw.get("state_truth_labels")),
        "user_visible_status": _safe_str(raw.get("user_visible_status")) or _safe_str(payload.get("user_visible_status")),
        "operator_visible_summary": _safe_str(raw.get("operator_visible_summary")) or _safe_str(payload.get("operator_visible_summary")),
        "limitations": _normalize_flags(raw.get("limitations") or payload.get("limitations")),
        "privacy_flags": _normalize_flags(raw.get("privacy_flags") or payload.get("privacy_flags")),
        "uncertainty_flags": _normalize_flags(raw.get("uncertainty_flags") or payload.get("uncertainty_flags")),
        "stale_state_flags": _normalize_flags(raw.get("stale_state_flags") or payload.get("stale_state_flags")),
        "contradiction_flags": _normalize_flags(raw.get("contradiction_flags") or payload.get("contradiction_flags")),
        "missing_evidence_flags": _normalize_flags(raw.get("missing_evidence_flags") or payload.get("missing_evidence_flags")),
    }


def _normalize_retrieval_need_metadata(payload: Mapping[str, Any], evidence_packets: list[Mapping[str, Any]]) -> dict[str, Any]:
    raw = _as_mapping(payload.get("retrieval_need_metadata") or payload.get("retrieval_need") or {})
    source_evidence = evidence_packets[0] if evidence_packets else {}
    return {
        "retrieval_need_class": _safe_str(raw.get("retrieval_need_class")) or _safe_str(payload.get("retrieval_need_class")) or _safe_str(source_evidence.get("retrieval_need_class")) or "none",
        "query_class": _safe_str(raw.get("query_class")) or _safe_str(source_evidence.get("query_class")),
        "source_class": _safe_str(raw.get("source_class")) or _safe_str(source_evidence.get("source_type")),
        "retrieval_adapter": _safe_str(raw.get("retrieval_adapter")) or _safe_str(source_evidence.get("retrieval_adapter")),
        "retrieval_request_id": _safe_str(raw.get("retrieval_request_id")) or _safe_str(source_evidence.get("retrieval_request_id")),
        "source_ref": _safe_str(raw.get("source_ref")) or _safe_str(source_evidence.get("source_ref")),
        "source_title": _safe_str(raw.get("source_title")) or _safe_str(source_evidence.get("source_title")),
        "source_url": _safe_str(raw.get("source_url")) or _safe_str(source_evidence.get("source_url")),
        "approval_status": _safe_str(raw.get("approval_status")) or _safe_str(source_evidence.get("approval_status")),
        "query_redaction_status": _safe_str(raw.get("query_redaction_status")) or _safe_str(source_evidence.get("query_redaction_status")),
        "retrieval_status": _safe_str(raw.get("retrieval_status")) or _safe_str(source_evidence.get("verification_status")) or "metadata only",
        "privacy_label": _safe_str(raw.get("privacy_label")) or _safe_str(source_evidence.get("privacy_label")),
        "privacy_sensitivity": _safe_str(raw.get("privacy_sensitivity")) or _safe_str(source_evidence.get("privacy_sensitivity")),
        "operator_visible_summary": _safe_str(raw.get("operator_visible_summary")) or "retrieval metadata only",
        "denied_authority": _normalize_denied_authority(raw.get("denied_authority") or payload.get("denied_authority") or {}),
    }


def _normalize_blocked_state(payload: Mapping[str, Any]) -> dict[str, Any]:
    raw = _as_mapping(payload.get("blocked_state") or {})
    return {
        "blocked": _safe_bool(raw.get("blocked")),
        "blocked_labels": _normalize_list(raw.get("blocked_labels") or payload.get("blocked_labels")),
        "blocked_reasons": _normalize_list(raw.get("blocked_reasons") or payload.get("blocked_reasons")),
        "blocked_authority": _safe_str(raw.get("blocked_authority")) or _safe_str(payload.get("blocked_authority")),
        "live_chat_output_blocked": True,
        "answer_delivery_blocked": True,
        "retrieval_execution_blocked": True,
        "persistence_blocked": True,
        "provider_model_search_tool_authority_blocked": True,
        "private_leak_blocked": True,
        "public_ready_claim_blocked": True,
        "cognitive_engine_authority_blocked": True,
    }


def _normalize_missing_evidence_state(payload: Mapping[str, Any], evidence_validations: list[dict[str, Any]]) -> dict[str, Any]:
    raw = _as_mapping(payload.get("missing_evidence_state") or {})
    missing_flags = _normalize_list(raw.get("missing_evidence_flags") or payload.get("missing_evidence_flags"))
    missing_refs = _normalize_list(raw.get("missing_evidence_packet_refs"))
    return {
        "missing_evidence_flags": missing_flags,
        "missing_evidence_packet_refs": missing_refs,
        "requires_evidence": bool(evidence_validations),
        "evidence_validation_blocked": any(validation.get("blocked") for validation in evidence_validations),
        "operator_visible_summary": _safe_str(raw.get("operator_visible_summary")) or "missing-evidence metadata only",
    }


def _normalize_conflict_state(payload: Mapping[str, Any]) -> dict[str, Any]:
    raw = _as_mapping(payload.get("conflict_state") or {})
    return {
        "contradiction_flags": _normalize_list(raw.get("contradiction_flags") or payload.get("contradiction_flags")),
        "stale_state_flags": _normalize_list(raw.get("stale_state_flags") or payload.get("stale_state_flags")),
        "conflict_labels": _normalize_list(raw.get("conflict_labels")),
        "missing_evidence_flags": _normalize_list(raw.get("missing_evidence_flags") or payload.get("missing_evidence_flags")),
        "operator_visible_summary": _safe_str(raw.get("operator_visible_summary")) or "conflict metadata only",
    }


def _normalize_approval_state(payload: Mapping[str, Any], project_context: Mapping[str, Any], answer_plan: Mapping[str, Any]) -> dict[str, Any]:
    raw = _as_mapping(payload.get("approval_state") or {})
    approval_refs = _normalize_list(raw.get("approval_refs") or payload.get("approval_refs") or project_context.get("approval_refs"))
    approval_required = bool(approval_refs) or _safe_str(answer_plan.get("answer_mode")) == "deeper_analysis_requires_approval"
    operator_review_required = _safe_bool(raw.get("operator_review_required")) or _safe_str(answer_plan.get("answer_mode")) == "operator_review_required_response"
    approval_status = _safe_str(raw.get("approval_status")) or ("approved" if approval_refs else "not_required")
    return {
        "approval_refs": approval_refs,
        "approval_required": approval_required,
        "operator_review_required": operator_review_required,
        "approval_status": approval_status,
        "operator_visible_summary": _safe_str(raw.get("operator_visible_summary")) or "approval metadata only",
    }


def _normalize_provenance_chain(
    payload: Mapping[str, Any],
    user_request: Mapping[str, Any],
    evidence_packets: list[Mapping[str, Any]],
    answer_plan: Mapping[str, Any],
    final_answer_packet: Mapping[str, Any],
) -> dict[str, Any]:
    raw = _as_mapping(payload.get("provenance_chain") or {})
    request_step = {
        "kind": "request",
        "request_id": _safe_str(user_request.get("request_id")) or _safe_str(payload.get("assembly_request_id")),
        "project_id": _safe_str(user_request.get("project_id")),
        "owner_user_scope": _safe_str(user_request.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(user_request.get("tenant_account_scope")),
        "source_scope": _safe_str(user_request.get("source_scope")),
        "user_intent_class": _safe_str(user_request.get("user_intent_class")),
    }
    evidence_step = {
        "kind": "evidence",
        "evidence_packet_ids": [_safe_str(packet.get("evidence_packet_id")) for packet in evidence_packets if _safe_str(packet.get("evidence_packet_id"))],
        "retrieval_request_ids": [_safe_str(packet.get("retrieval_request_id")) for packet in evidence_packets if _safe_str(packet.get("retrieval_request_id"))],
        "source_refs": [_safe_str(packet.get("source_ref")) for packet in evidence_packets if _safe_str(packet.get("source_ref"))],
        "verification_statuses": [_safe_str(packet.get("verification_status")) for packet in evidence_packets if _safe_str(packet.get("verification_status"))],
    }
    answer_plan_step = {
        "kind": "answer_plan",
        "answer_plan_id": _safe_str(answer_plan.get("answer_plan_id")),
        "answer_mode": _safe_str(answer_plan.get("answer_mode")),
        "allowed_answer_scope": _safe_str(answer_plan.get("allowed_answer_scope")),
        "answer_status": _safe_str(answer_plan.get("answer_status")),
        "evidence_packet_refs": _normalize_list(answer_plan.get("evidence_packet_refs")),
    }
    final_answer_step = {
        "kind": "final_answer",
        "final_answer_packet_id": _safe_str(final_answer_packet.get("final_answer_packet_id")),
        "final_answer_request_id": _safe_str(final_answer_packet.get("final_answer_request_id")),
        "final_answer_status": _safe_str(final_answer_packet.get("final_answer_status")),
        "answer_text_bounded": _safe_bool(final_answer_packet.get("answer_text_bounded")),
        "citation_count": len(_normalize_list(final_answer_packet.get("citations"))),
    }
    steps = raw.get("steps") if isinstance(raw.get("steps"), list) else [request_step, evidence_step, answer_plan_step, final_answer_step]
    return {
        "steps": steps,
        "chain_status": _safe_str(raw.get("chain_status")) or "metadata_only",
        "step_count": len(steps),
        "request_step": request_step,
        "evidence_step": evidence_step,
        "answer_plan_step": answer_plan_step,
        "final_answer_step": final_answer_step,
        "operator_visible_summary": _safe_str(raw.get("operator_visible_summary")) or "provenance chain metadata only",
    }


def _collect_string_values(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, Mapping):
        for item in value.values():
            values.extend(_collect_string_values(item))
        return values
    if isinstance(value, list):
        for item in value:
            values.extend(_collect_string_values(item))
        return values
    if isinstance(value, tuple):
        for item in value:
            values.extend(_collect_string_values(item))
        return values
    if isinstance(value, set):
        for item in value:
            values.extend(_collect_string_values(item))
        return values
    if isinstance(value, str):
        values.append(value)
    return values


def _slugify_v1(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", _safe_str(text).lower()).strip("_")
    return slug or "forbidden_phrase"


def _find_forbidden_hits_v1(candidate: Any) -> list[str]:
    blob = " \n".join(_collect_string_values(candidate)).lower()
    hits: list[str] = []
    for phrase in FORBIDDEN_LEAKAGE_PHRASES_V1:
        if phrase.lower() in blob:
            hits.append(phrase)
    return _dedupe(hits)


def _default_final_answer_status(
    final_answer_source: Mapping[str, Any],
    answer_plan: Mapping[str, Any],
    project_context: Mapping[str, Any],
    evidence_packets: list[Mapping[str, Any]],
) -> str:
    mode = _safe_str(final_answer_source.get("final_answer_mode")) or _safe_str(answer_plan.get("answer_mode"))
    if _normalize_flags(final_answer_source.get("uncertainty_flags") or answer_plan.get("uncertainty_flags") or project_context.get("uncertainty_flags")) or _normalize_flags(final_answer_source.get("missing_evidence_flags") or answer_plan.get("missing_evidence_flags") or project_context.get("missing_evidence_flags")) or _normalize_flags(final_answer_source.get("contradiction_flags") or answer_plan.get("contradiction_flags") or project_context.get("contradiction_flags")):
        return "uncertain"
    if mode == "clarifying_question":
        return "needs_clarification"
    if mode == "deeper_analysis_requires_approval":
        return "needs_approval"
    if mode == "operator_review_required_response":
        return "needs_operator_review"
    if mode == "uncertain_or_missing_evidence_answer":
        return "uncertain"
    if evidence_packets and any(_safe_str(packet.get("verification_status")) == "conflict_review_required" for packet in evidence_packets):
        return "uncertain"
    candidate = _safe_str(final_answer_source.get("answer_status"))
    if candidate in FINAL_ANSWER_STATUSES_V1:
        return candidate
    return "answer_ready"


def _normalize_citations(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        items = [value]
    elif isinstance(value, list):
        items = value
    else:
        items = [value]
    citations: list[dict[str, Any]] = []
    for item in items:
        raw = _as_mapping(item)
        if not raw:
            continue
        citations.append(
            {
                "evidence_packet_id": _safe_str(raw.get("evidence_packet_id")),
                "retrieval_request_id": _safe_str(raw.get("retrieval_request_id")),
                "source_type": _safe_str(raw.get("source_type")),
                "source_ref": _safe_str(raw.get("source_ref")),
                "source_url": _safe_str(raw.get("source_url")),
                "source_title": _safe_str(raw.get("source_title")),
                "freshness_label": _safe_str(raw.get("freshness_label")),
                "verification_status": _safe_str(raw.get("verification_status")),
                "privacy_label": _safe_str(raw.get("privacy_label")),
                "conflict_flags": _normalize_flags(raw.get("conflict_flags")),
                "missing_evidence_flags": _normalize_flags(raw.get("missing_evidence_flags")),
                "limitations": _normalize_flags(raw.get("limitations")),
            }
        )
    return citations


def _build_synthesized_final_answer_payload(
    payload: Mapping[str, Any],
    user_request: Mapping[str, Any],
    project_context: Mapping[str, Any],
    retrieval_need: Mapping[str, Any],
    evidence_packets: list[Mapping[str, Any]],
    answer_plan: Mapping[str, Any],
) -> dict[str, Any]:
    final_answer_source = _as_mapping(payload.get("final_answer_packet_metadata") or payload.get("final_answer_packet") or {})
    external_search_required = _safe_bool(payload.get("external_search_required")) or _safe_str(retrieval_need.get("retrieval_need_class")) == "external_web_search_needed"
    external_search_approved = _safe_bool(payload.get("external_search_approved"))
    external_search_redacted = _safe_bool(payload.get("external_search_redacted"))
    if evidence_packets:
        external_search_approved = external_search_approved or all(_safe_str(packet.get("approval_status")) in {"approved", "not_required"} for packet in evidence_packets)
        external_search_redacted = external_search_redacted or all(_safe_str(packet.get("query_redaction_status")) in {"applied", "not_required"} for packet in evidence_packets)
    request_payload = {
        "project_id": _safe_str(final_answer_source.get("project_id")) or _safe_str(user_request.get("project_id")) or _safe_str(answer_plan.get("project_id")),
        "owner_user_scope": _safe_str(final_answer_source.get("owner_user_scope")) or _safe_str(user_request.get("owner_user_scope")) or _safe_str(answer_plan.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(final_answer_source.get("tenant_account_scope")) or _safe_str(user_request.get("tenant_account_scope")) or _safe_str(answer_plan.get("tenant_account_scope")),
        "source_scope": _safe_str(final_answer_source.get("source_scope")) or _safe_str(user_request.get("source_scope")) or _safe_str(answer_plan.get("source_scope")),
        "user_intent_class": _safe_str(final_answer_source.get("user_intent_class")) or _safe_str(user_request.get("user_intent_class")) or _safe_str(answer_plan.get("user_intent_class")) or "project-chat",
        "answer_plan_metadata": answer_plan,
        "evidence_packet_metadata": evidence_packets,
        "project_context_metadata": project_context,
        "answer_surface": _safe_str(final_answer_source.get("answer_surface")) or "internal_controlled",
        "answer_visibility": _safe_str(final_answer_source.get("answer_visibility")) or "internal_controlled",
        "final_answer_mode": _safe_str(final_answer_source.get("final_answer_mode")) or _safe_str(answer_plan.get("answer_mode")) or "evidence_grounded_answer",
        "answer_status": _default_final_answer_status(final_answer_source, answer_plan, project_context, evidence_packets),
        "retrieval_required": _safe_bool(final_answer_source.get("retrieval_required")) or bool(evidence_packets),
        "retrieval_completed": _safe_bool(final_answer_source.get("retrieval_completed")) or bool(evidence_packets),
        "external_search_required": external_search_required,
        "external_search_approved": _safe_bool(final_answer_source.get("external_search_approved")) or external_search_approved,
        "external_search_redacted": _safe_bool(final_answer_source.get("external_search_redacted")) or external_search_redacted,
        "controlled_answer_text_proposal": _safe_str(final_answer_source.get("controlled_answer_text_proposal")) or _safe_str(final_answer_source.get("answer_text_proposal")) or _safe_str(payload.get("controlled_answer_text_proposal")),
        "user_visible_status": _safe_str(final_answer_source.get("user_visible_status")) or _safe_str(answer_plan.get("user_visible_status")) or _safe_str(project_context.get("user_visible_status")) or "metadata only",
        "operator_visible_summary": _safe_str(final_answer_source.get("operator_visible_summary")) or _safe_str(payload.get("operator_visible_summary")) or "final answer metadata only",
        "approval_refs": _normalize_list(final_answer_source.get("approval_refs") or payload.get("approval_refs") or project_context.get("approval_refs")),
        "limitations": _normalize_flags(final_answer_source.get("limitations") or payload.get("limitations") or answer_plan.get("limitations") or project_context.get("limitations")),
        "privacy_flags": _normalize_flags(final_answer_source.get("privacy_flags") or payload.get("privacy_flags") or project_context.get("privacy_flags")),
        "uncertainty_flags": _normalize_flags(final_answer_source.get("uncertainty_flags") or payload.get("uncertainty_flags") or answer_plan.get("uncertainty_flags") or project_context.get("uncertainty_flags")),
        "stale_state_flags": _normalize_flags(final_answer_source.get("stale_state_flags") or payload.get("stale_state_flags") or answer_plan.get("stale_state_flags") or project_context.get("stale_state_flags")),
        "contradiction_flags": _normalize_flags(final_answer_source.get("contradiction_flags") or payload.get("contradiction_flags") or answer_plan.get("contradiction_flags") or project_context.get("contradiction_flags")),
        "missing_evidence_flags": _normalize_flags(final_answer_source.get("missing_evidence_flags") or payload.get("missing_evidence_flags") or answer_plan.get("missing_evidence_flags") or project_context.get("missing_evidence_flags")),
        "citations": _normalize_citations(final_answer_source.get("citations") or payload.get("citations")),
        "blocked_authority": _safe_str(final_answer_source.get("blocked_authority")) or _safe_str(payload.get("blocked_authority")),
        "denied_authority": _normalize_denied_authority(final_answer_source.get("denied_authority") or payload.get("denied_authority") or {}),
    }
    if not request_payload["citations"]:
        request_payload["citations"] = _normalize_citations(evidence_packets)
    return request_payload


def build_project_chat_assembly_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _coalesce_payload(payload, **overrides)

    user_request_metadata = _normalize_user_request_metadata(data)
    project_context_metadata = _normalize_project_context_metadata(data)

    evidence_packets_raw = data.get("evidence_packet_metadata") or data.get("evidence_packets") or []
    if isinstance(evidence_packets_raw, Mapping):
        evidence_packets_raw = [evidence_packets_raw]
    if not isinstance(evidence_packets_raw, list):
        evidence_packets_raw = [evidence_packets_raw]
    evidence_packet_metadata = [build_project_chat_evidence_packet_v1(item) for item in evidence_packets_raw]

    retrieval_need_metadata = _normalize_retrieval_need_metadata(data, evidence_packet_metadata)
    answer_plan_metadata = build_project_chat_answer_plan_v1(data.get("answer_plan_metadata") or data.get("answer_plan") or {})
    final_answer_packet_metadata = build_project_chat_final_answer_packet_v1(
        _build_synthesized_final_answer_payload(
            data,
            user_request_metadata,
            project_context_metadata,
            retrieval_need_metadata,
            evidence_packet_metadata,
            answer_plan_metadata,
        )
    )

    evidence_validations = [validate_project_chat_evidence_packet_v1(packet) for packet in evidence_packet_metadata]
    answer_plan_validation = validate_project_chat_answer_plan_v1(answer_plan_metadata)
    final_answer_validation = validate_project_chat_final_answer_packet_v1(final_answer_packet_metadata)

    blocked_state = _normalize_blocked_state(data)
    missing_evidence_state = _normalize_missing_evidence_state(data, evidence_validations)
    conflict_state = _normalize_conflict_state(data)
    approval_state = _normalize_approval_state(data, project_context_metadata, answer_plan_metadata)
    provenance_chain = _normalize_provenance_chain(data, user_request_metadata, evidence_packet_metadata, answer_plan_metadata, final_answer_packet_metadata)

    final_answer_ready = not final_answer_validation["blocked"]
    candidate_blocked = (
        any(validation["blocked"] for validation in evidence_validations)
        or answer_plan_validation["blocked"]
        or final_answer_validation["blocked"]
        or blocked_state["blocked"]
        or bool(_find_forbidden_hits_v1(data))
    )
    blocked_state["blocked"] = candidate_blocked
    blocked_state["blocked_labels"] = _normalize_list(blocked_state.get("blocked_labels"))
    if candidate_blocked and "invalid_assembly_packet" not in blocked_state["blocked_labels"]:
        blocked_state["blocked_labels"].append("invalid_assembly_packet")
    if not candidate_blocked:
        blocked_state["blocked_labels"] = []
    blocked_state["blocked_reasons"] = blocked_state["blocked_labels"][:]

    assembly_mode = _safe_str(data.get("assembly_mode")) or (
        "blocked_orchestration" if candidate_blocked else (
            "candidate_orchestration" if final_answer_ready else "metadata_only_assembly"
        )
    )
    if assembly_mode not in ASSEMBLY_MODES_V1:
        assembly_mode = "blocked_orchestration" if candidate_blocked else "metadata_only_assembly"

    assembly_status = _safe_str(data.get("assembly_status")) or ("blocked" if candidate_blocked else "assembly_valid_metadata_only")
    if assembly_status not in ASSEMBLY_STATUSES_V1:
        assembly_status = "blocked" if candidate_blocked else "assembly_valid_metadata_only"

    assembly_packet = {
        "schema_version": _safe_str(data.get("schema_version")) or SCHEMA_VERSION_V1,
        "assembly_id": _safe_str(data.get("assembly_id")),
        "assembly_mode": assembly_mode,
        "assembly_status": assembly_status,
        "user_request_metadata": user_request_metadata,
        "project_context_metadata": project_context_metadata,
        "retrieval_need_metadata": retrieval_need_metadata,
        "evidence_packet_metadata": evidence_packet_metadata,
        "answer_plan_metadata": answer_plan_metadata,
        "final_answer_packet_metadata": final_answer_packet_metadata,
        "blocked_state": blocked_state,
        "missing_evidence_state": missing_evidence_state,
        "conflict_state": conflict_state,
        "approval_state": approval_state,
        "provenance_chain": provenance_chain,
        "denied_authority": _normalize_denied_authority(data.get("denied_authority") or {}),
        "safe_metadata": {
            "assembly_summary": "metadata only assembly packet",
            "assembly_mode": assembly_mode,
            "assembly_status": assembly_status,
            "evidence_count": len(evidence_packet_metadata),
            "final_answer_status": _safe_str(final_answer_packet_metadata.get("final_answer_status")),
            "answer_mode": _safe_str(answer_plan_metadata.get("answer_mode")),
            "final_answer_ready": final_answer_ready,
            "live_chat_blocked": True,
            "answer_delivery_blocked": True,
            "retrieval_execution_blocked": True,
            "persistence_blocked": True,
            "provider_model_search_tool_authority_blocked": True,
            "private_leak_blocked": True,
            "public_ready_claim_blocked": True,
            "cognitive_engine_authority_blocked": True,
        },
        "helper_type": HELPER_TYPE_V1,
    }

    digest_source = {key: value for key, value in assembly_packet.items() if key not in {"assembly_id", "helper_type"}}
    if not assembly_packet["assembly_id"]:
        assembly_packet["assembly_id"] = f"project-chat-assembly-{_stable_digest(digest_source)[:16]}"
    return assembly_packet


def validate_project_chat_assembly_packet_v1(packet: Any) -> dict[str, Any]:
    candidate = build_project_chat_assembly_packet_v1(packet)
    blocked_labels: list[str] = []

    if candidate.get("schema_version") != SCHEMA_VERSION_V1:
        blocked_labels.append("unknown_schema_version")

    required_fields = (
        "assembly_id",
        "assembly_mode",
        "user_request_metadata",
        "project_context_metadata",
        "retrieval_need_metadata",
        "evidence_packet_metadata",
        "answer_plan_metadata",
        "final_answer_packet_metadata",
        "blocked_state",
        "missing_evidence_state",
        "conflict_state",
        "approval_state",
        "provenance_chain",
        "denied_authority",
        "safe_metadata",
    )
    for field in required_fields:
        if field in {"user_request_metadata", "project_context_metadata", "retrieval_need_metadata", "evidence_packet_metadata", "answer_plan_metadata", "final_answer_packet_metadata", "blocked_state", "missing_evidence_state", "conflict_state", "approval_state", "provenance_chain", "denied_authority", "safe_metadata"}:
            if not _as_mapping(candidate.get(field)) and not isinstance(candidate.get(field), list):
                blocked_labels.append(f"missing_{field}")
        elif not _safe_str(candidate.get(field)):
            blocked_labels.append(f"missing_{field}")

    _validate_allowed_value(candidate.get("assembly_mode", ""), ASSEMBLY_MODES_V1, "assembly_mode", blocked_labels)
    _validate_allowed_value(candidate.get("assembly_status", ""), ASSEMBLY_STATUSES_V1, "assembly_status", blocked_labels)

    user_request_metadata = _as_mapping(candidate.get("user_request_metadata"))
    project_context_metadata = _as_mapping(candidate.get("project_context_metadata"))
    retrieval_need_metadata = _as_mapping(candidate.get("retrieval_need_metadata"))
    required_user_request_fields = ("project_id", "owner_user_scope", "tenant_account_scope", "source_scope", "user_intent_class")
    for field in required_user_request_fields:
        if not _safe_str(user_request_metadata.get(field)):
            blocked_labels.append(f"missing_user_request_metadata_{field}")
    has_project_context = any(
        _normalize_list(project_context_metadata.get(field))
        for field in (
            "project_state_refs",
            "memory_state_refs",
            "continuity_state_refs",
            "gap_analysis_refs",
            "tool_lane_candidate_refs",
            "approval_refs",
            "user_correction_refs",
            "state_truth_labels",
            "limitations",
            "privacy_flags",
            "uncertainty_flags",
            "stale_state_flags",
            "contradiction_flags",
            "missing_evidence_flags",
        )
    ) or any(
        _safe_str(project_context_metadata.get(field))
        for field in (
            "user_visible_status",
            "operator_visible_summary",
        )
    )
    if not has_project_context:
        blocked_labels.append("missing_project_context_metadata")
    if not _safe_str(retrieval_need_metadata.get("retrieval_need_class")):
        blocked_labels.append("missing_retrieval_need_class")
    if not _safe_str(retrieval_need_metadata.get("retrieval_status")):
        blocked_labels.append("missing_retrieval_need_status")

    evidence_validations = [validate_project_chat_evidence_packet_v1(packet) for packet in candidate.get("evidence_packet_metadata", [])]
    answer_plan_validation = validate_project_chat_answer_plan_v1(candidate.get("answer_plan_metadata", {}))
    final_answer_validation = validate_project_chat_final_answer_packet_v1(candidate.get("final_answer_packet_metadata", {}))

    if not candidate.get("evidence_packet_metadata"):
        blocked_labels.append("missing_evidence_packet_metadata")
    if any(validation.get("blocked") for validation in evidence_validations):
        blocked_labels.append("invalid_evidence_packet_metadata")
    if answer_plan_validation.get("blocked"):
        blocked_labels.append("invalid_answer_plan_metadata")
    if final_answer_validation.get("blocked"):
        blocked_labels.append("invalid_final_answer_packet_metadata")
    if candidate.get("final_answer_packet_metadata") and (any(validation.get("blocked") for validation in evidence_validations) or answer_plan_validation.get("blocked")):
        blocked_labels.append("final_answer_requires_valid_evidence_and_answer_plan")

    for field, value in candidate.get("denied_authority", {}).items():
        if field not in DENIED_AUTHORITY_FIELDS_V1:
            blocked_labels.append(f"unknown_denied_authority_field_{field}")
        elif _safe_bool(value):
            blocked_labels.append(f"denied_authority_must_remain_false_{field}")

    blocked_state = _as_mapping(candidate.get("blocked_state"))
    for field in (
        "live_chat_output_blocked",
        "answer_delivery_blocked",
        "retrieval_execution_blocked",
        "persistence_blocked",
        "provider_model_search_tool_authority_blocked",
        "private_leak_blocked",
        "public_ready_claim_blocked",
        "cognitive_engine_authority_blocked",
    ):
        if blocked_state.get(field) is not True:
            blocked_labels.append(f"missing_{field}")

    if _safe_bool(blocked_state.get("blocked")) and not _normalize_list(blocked_state.get("blocked_labels")):
        blocked_labels.append("blocked_state_missing_labels")

    provenance_chain = _as_mapping(candidate.get("provenance_chain"))
    steps = provenance_chain.get("steps") if isinstance(provenance_chain.get("steps"), list) else []
    if len(steps) < 4:
        blocked_labels.append("incomplete_provenance_chain")
    else:
        expected_kinds = ["request", "evidence", "answer_plan", "final_answer"]
        actual_kinds = [_safe_str(step.get("kind")) for step in steps if isinstance(step, Mapping)]
        if actual_kinds[:4] != expected_kinds:
            blocked_labels.append("invalid_provenance_chain_order")

    for phrase in _find_forbidden_hits_v1(candidate):
        blocked_labels.append(f"forbidden_phrase_{_slugify_v1(phrase)}")

    blocked = bool(blocked_labels)
    assembly_status = "blocked" if blocked else _safe_str(candidate.get("assembly_status")) or "assembly_valid_metadata_only"
    if blocked and assembly_status == "assembly_valid_metadata_only":
        assembly_status = "blocked"

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "assembly_packet": candidate,
        "assembly_id": candidate["assembly_id"],
        "assembly_mode": candidate["assembly_mode"],
        "assembly_status": assembly_status,
        "blocked": blocked,
        "blocked_labels": blocked_labels,
        "validation_notes": blocked_labels[:],
        "user_request_metadata": candidate["user_request_metadata"],
        "project_context_metadata": candidate["project_context_metadata"],
        "retrieval_need_metadata": candidate["retrieval_need_metadata"],
        "evidence_packet_metadata": candidate["evidence_packet_metadata"],
        "answer_plan_metadata": candidate["answer_plan_metadata"],
        "final_answer_packet_metadata": candidate["final_answer_packet_metadata"],
        "blocked_state": candidate["blocked_state"],
        "missing_evidence_state": candidate["missing_evidence_state"],
        "conflict_state": candidate["conflict_state"],
        "approval_state": candidate["approval_state"],
        "provenance_chain": candidate["provenance_chain"],
        "denied_authority": candidate["denied_authority"],
        "safe_metadata": candidate["safe_metadata"],
        "evidence_validations": evidence_validations,
        "answer_plan_validation": answer_plan_validation,
        "final_answer_validation": final_answer_validation,
    }


def summarize_project_chat_assembly_packet_v1(packet: Any) -> dict[str, Any]:
    candidate = build_project_chat_assembly_packet_v1(packet)
    validation = validate_project_chat_assembly_packet_v1(candidate)
    summary_text = (
        f"assembly={_safe_str(candidate.get('assembly_mode'))} | "
        f"status={_safe_str(validation.get('assembly_status'))} | "
        f"blocked={validation['blocked']} | "
        f"evidence={len(validation.get('evidence_packet_metadata', []))} | "
        f"plan={_safe_str(validation.get('answer_plan_metadata', {}).get('answer_mode'))} | "
        f"final={_safe_str(validation.get('final_answer_packet_metadata', {}).get('final_answer_status'))}"
    )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "assembly_id": validation["assembly_id"],
        "summary_text": summary_text,
        "assembly_mode": validation["assembly_mode"],
        "assembly_status": validation["assembly_status"],
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "validation_notes": validation["validation_notes"],
        "provenance_chain": validation["provenance_chain"],
        "safe_metadata": validation["safe_metadata"],
    }


def to_project_chat_assembly_packet_json_safe_v1(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): to_project_chat_assembly_packet_json_safe_v1(val) for key, val in value.items()}
    if isinstance(value, list):
        return [to_project_chat_assembly_packet_json_safe_v1(item) for item in value]
    if isinstance(value, tuple):
        return [to_project_chat_assembly_packet_json_safe_v1(item) for item in value]
    if isinstance(value, set):
        return [to_project_chat_assembly_packet_json_safe_v1(item) for item in sorted(value, key=lambda item: _safe_str(item))]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _safe_str(value)


def build_initial_project_chat_assembly_packet_examples_v1() -> list[dict[str, Any]]:
    answer_plan = build_project_chat_answer_plan_v1(
        {
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "user_intent_class": "project-chat",
            "answer_mode": "evidence_grounded_answer",
            "allowed_answer_scope": "approved_evidence_packet",
            "answer_status": "plan_valid_metadata_only",
            "evidence_packet_refs": ["evidence-001"],
            "user_visible_status": "evidence grounded answer",
            "operator_visible_summary": "evidence grounded; metadata only",
        }
    )
    evidence = build_project_chat_evidence_packet_v1(
        {
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "retrieval_request_id": "request-001",
            "retrieval_need_class": "project_metadata_retrieval_needed",
            "retrieval_adapter": "ProjectStateMetadataAdapter",
            "source_type": "project_metadata",
            "source_ref": "project-metadata-001",
            "source_title": "project metadata only",
            "source_timestamp": "2026-06-06T14:00:00Z",
            "retrieved_at_marker": "metadata_only",
            "freshness_label": "fresh_current",
            "relevance_label": "high_relevance",
            "confidence_label": "high_confidence",
            "verification_status": "metadata_only",
            "privacy_label": "public",
            "privacy_sensitivity": "low",
            "query_redaction_status": "not_required",
            "evidence_summary": "evidence packet metadata only",
        }
    )
    valid = build_project_chat_assembly_packet_v1(
        {
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "user_intent_class": "project-chat",
            "user_request_metadata": {
                "request_id": "request-001",
                "message_ref": "message-001",
                "message_status": "metadata only",
                "user_visible_status": "metadata only",
                "operator_visible_summary": "message intake metadata only",
            },
            "project_context_metadata": {
                "project_state_refs": ["project-state-001"],
                "memory_state_refs": ["memory-state-001"],
                "continuity_state_refs": ["continuity-state-001"],
                "gap_analysis_refs": ["gap-001"],
                "approval_refs": ["approval-001"],
                "user_visible_status": "evidence grounded answer",
                "operator_visible_summary": "evidence grounded; metadata only",
            },
            "retrieval_need_metadata": {
                "retrieval_need_class": "project_metadata_retrieval_needed",
                "retrieval_status": "metadata only",
            },
            "evidence_packet_metadata": [evidence],
            "answer_plan_metadata": answer_plan,
            "final_answer_packet_metadata": {
                "controlled_answer_text_proposal": "Internal controlled answer candidate: evidence-grounded and bounded by citations.",
            },
            "safe_metadata": {
                "assembly_summary": "metadata only assembly packet",
            },
        }
    )
    blocked = build_project_chat_assembly_packet_v1(
        {
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "user_intent_class": "project-chat",
            "user_request_metadata": {
                "request_id": "request-002",
                "message_ref": "message-002",
                "raw_transcript_text": "raw transcript should not be accepted",
            },
            "project_context_metadata": {
                "user_visible_status": "clarification needed",
                "operator_visible_summary": "clarification required; metadata only",
            },
            "evidence_packet_metadata": [],
            "answer_plan_metadata": {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "user_intent_class": "project-chat",
                "answer_mode": "evidence_grounded_answer",
                "allowed_answer_scope": "approved_evidence_packet",
                "answer_status": "plan_valid_metadata_only",
                "evidence_packet_refs": [],
                "user_visible_status": "evidence grounded answer",
                "operator_visible_summary": "evidence grounded; metadata only",
            },
            "final_answer_packet_metadata": {
                "controlled_answer_text_proposal": "Internal controlled answer candidate: evidence grounded.",
            },
        }
    )
    return [valid, blocked]
