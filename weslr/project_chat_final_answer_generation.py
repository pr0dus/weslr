"""Metadata-only helpers for WESLR project-chat final answer generation V1.

This module is intentionally pure, deterministic, synthetic/example-safe,
and fail-closed.
It builds and validates final-answer request/packet metadata only.

It does not perform file I/O, network I/O, shell execution, runtime/chat
wiring, retrieval, model calls, tool execution, external actions,
persistence, or user-visible answer delivery.
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
from weslr.project_chat_rag_evidence_retrieval import (
    DENIED_AUTHORITY_FIELDS_V1 as RAG_DENIED_AUTHORITY_FIELDS_V1,
    build_project_chat_evidence_packet_v1,
    validate_project_chat_evidence_packet_v1,
)

HELPER_TYPE_V1 = "weslr_project_chat_final_answer_generation_v1"
SCHEMA_VERSION_V1 = "project_chat_final_answer_generation_v1"

ANSWER_SURFACES_V1 = (
    "internal_controlled",
)

ANSWER_VISIBILITIES_V1 = (
    "internal_controlled",
)

FINAL_ANSWER_STATUSES_V1 = (
    "answer_ready",
    "blocked",
    "invalid",
    "needs_approval",
    "needs_clarification",
    "needs_operator_review",
    "uncertain",
)

FINAL_ANSWER_MODES_V1 = (
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

DENIED_AUTHORITY_FIELDS_V1 = (
    "runtime_wiring_authority",
    "chat" + "_" + "responder_authority",
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
    "provider_call_authority",
    "model_call_authority",
    "search_call_authority",
    "cognitive_research_run_authority",
    "cognitive_engine_authority",
)

FORBIDDEN_USER_VISIBLE_PHRASES_V1 = (
    "unknown engine",
    "." + "weslr",
    "hidden prompt",
    "system prompt",
    "private mechanism",
    "internal mechanism",
    "tool executed",
    "i executed",
    "i searched your private data",
    "i saved this project",
    "i remember this",
    "searxng proves",
    "the web confirms",
    "truth authority",
    "final answer authority",
    "runtime authority",
    "mutation authority",
    "memory authority",
    "tool execution authority",
    "storage authority",
    "public readiness",
    "certified",
    "proof",
    "proven",
    "solved",
    "benchmark",
    "legal certainty",
    "medical certainty",
    "financial certainty",
    "professional certainty",
    "guaranteed",
    "cognitiveresearchrunv1",
    "cognitive research run",
    "cognitive engine",
)

_DEFAULT_FALSE_DENIED_AUTHORITY = {field: False for field in DENIED_AUTHORITY_FIELDS_V1}


def allowed_project_chat_final_answer_surfaces_v1() -> tuple[str, ...]:
    return ANSWER_SURFACES_V1


def allowed_project_chat_final_answer_visibilities_v1() -> tuple[str, ...]:
    return ANSWER_VISIBILITIES_V1


def allowed_project_chat_final_answer_statuses_v1() -> tuple[str, ...]:
    return FINAL_ANSWER_STATUSES_V1


def allowed_project_chat_final_answer_modes_v1() -> tuple[str, ...]:
    return FINAL_ANSWER_MODES_V1


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


def _normalize_list(value: Any) -> list[str]:
    return _dedupe(_safe_list(value))


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
        citations.append({
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
        })
    return citations


def _normalize_flags(value: Any) -> list[str]:
    return _normalize_list(value)


def _normalize_denied_authority(value: Any) -> dict[str, bool]:
    payload = dict(_DEFAULT_FALSE_DENIED_AUTHORITY)
    raw = _as_mapping(value)
    for field in DENIED_AUTHORITY_FIELDS_V1:
        payload[field] = _safe_bool(raw.get(field, False))
    return payload


def _validate_allowed_value(value: str, allowed: tuple[str, ...], label: str, blocked_labels: list[str]) -> bool:
    if not value:
        blocked_labels.append(f"missing_{label}")
        return False
    if value not in allowed:
        blocked_labels.append(f"unknown_{label}")
        return False
    return True


def _find_forbidden_hits_v1(text: Any) -> list[str]:
    candidate = _safe_str(text).lower()
    hits: list[str] = []
    for phrase in FORBIDDEN_USER_VISIBLE_PHRASES_V1:
        if phrase.lower() in candidate:
            hits.append(phrase)
    return hits


def _slugify_v1(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", _safe_str(text).lower()).strip("_")
    return slug or "forbidden_phrase"


def _maybe_block_forbidden_text(field_name: str, text: Any, blocked_labels: list[str]) -> None:
    for phrase in _find_forbidden_hits_v1(text):
        blocked_labels.append(f"{field_name}_forbidden_phrase_{_slugify_v1(phrase)}")


def _coalesce_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = {}
    if isinstance(payload, Mapping):
        data.update(payload)
    elif payload is not None:
        data["payload"] = payload
    data.update(overrides)
    return data


def _normalize_project_context(payload: Any) -> dict[str, Any]:
    raw = _as_mapping(payload)
    return {
        "project_state_refs": _normalize_list(raw.get("project_state_refs")),
        "memory_state_refs": _normalize_list(raw.get("memory_state_refs")),
        "continuity_state_refs": _normalize_list(raw.get("continuity_state_refs")),
        "gap_analysis_refs": _normalize_list(raw.get("gap_analysis_refs")),
        "tool_lane_candidate_refs": _normalize_list(raw.get("tool_lane_candidate_refs")),
        "approval_refs": _normalize_list(raw.get("approval_refs")),
        "user_correction_refs": _normalize_list(raw.get("user_correction_refs")),
        "state_truth_labels": _normalize_list(raw.get("state_truth_labels")),
        "user_visible_status": _safe_str(raw.get("user_visible_status")),
        "operator_visible_summary": _safe_str(raw.get("operator_visible_summary")),
        "limitations": _normalize_flags(raw.get("limitations")),
        "privacy_flags": _normalize_flags(raw.get("privacy_flags")),
        "uncertainty_flags": _normalize_flags(raw.get("uncertainty_flags")),
        "stale_state_flags": _normalize_flags(raw.get("stale_state_flags")),
        "contradiction_flags": _normalize_flags(raw.get("contradiction_flags")),
        "missing_evidence_flags": _normalize_flags(raw.get("missing_evidence_flags")),
    }


def _normalize_request(payload: Mapping[str, Any]) -> dict[str, Any]:
    answer_plan = build_project_chat_answer_plan_v1(payload.get("answer_plan_metadata") or payload.get("answer_plan") or {})
    evidence_packets = payload.get("evidence_packet_metadata") or payload.get("evidence_packets") or []
    if isinstance(evidence_packets, Mapping):
        evidence_packets = [evidence_packets]
    if not isinstance(evidence_packets, list):
        evidence_packets = [evidence_packets]
    project_context = _normalize_project_context(payload.get("project_context_metadata") or payload.get("project_context") or {})

    request = {
        "schema_version": _safe_str(payload.get("schema_version")) or SCHEMA_VERSION_V1,
        "final_answer_request_id": _safe_str(payload.get("final_answer_request_id")),
        "project_id": _safe_str(payload.get("project_id")) or _safe_str(answer_plan.get("project_id")),
        "owner_user_scope": _safe_str(payload.get("owner_user_scope")) or _safe_str(answer_plan.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(payload.get("tenant_account_scope")) or _safe_str(answer_plan.get("tenant_account_scope")),
        "source_scope": _safe_str(payload.get("source_scope")) or _safe_str(answer_plan.get("source_scope")),
        "user_intent_class": _safe_str(payload.get("user_intent_class")) or _safe_str(answer_plan.get("user_intent_class")),
        "answer_plan_metadata": answer_plan,
        "evidence_packet_metadata": [build_project_chat_evidence_packet_v1(item) for item in evidence_packets],
        "project_context_metadata": project_context,
        "answer_surface": _safe_str(payload.get("answer_surface")) or "internal_controlled",
        "answer_visibility": _safe_str(payload.get("answer_visibility")) or "internal_controlled",
        "final_answer_mode": _safe_str(payload.get("final_answer_mode")) or _safe_str(answer_plan.get("answer_mode")),
        "answer_status": _safe_str(payload.get("answer_status")) or _safe_str(answer_plan.get("answer_status")),
        "retrieval_required": _safe_bool(payload.get("retrieval_required")),
        "retrieval_completed": _safe_bool(payload.get("retrieval_completed")),
        "external_search_required": _safe_bool(payload.get("external_search_required")),
        "external_search_approved": _safe_bool(payload.get("external_search_approved")),
        "external_search_redacted": _safe_bool(payload.get("external_search_redacted")),
        "answer_text_proposal": _safe_str(payload.get("answer_text_proposal")),
        "controlled_answer_text_proposal": _safe_str(payload.get("controlled_answer_text_proposal")),
        "operator_visible_summary": _safe_str(payload.get("operator_visible_summary")) or _safe_str(project_context.get("operator_visible_summary")),
        "user_visible_status": _safe_str(payload.get("user_visible_status")) or _safe_str(project_context.get("user_visible_status")),
        "limitations": _normalize_flags(payload.get("limitations")) or _normalize_flags(answer_plan.get("limitations")) or _normalize_flags(project_context.get("limitations")),
        "privacy_flags": _normalize_flags(payload.get("privacy_flags")) or _normalize_flags(project_context.get("privacy_flags")),
        "uncertainty_flags": _normalize_flags(payload.get("uncertainty_flags")) or _normalize_flags(answer_plan.get("uncertainty_flags")) or _normalize_flags(project_context.get("uncertainty_flags")),
        "stale_state_flags": _normalize_flags(payload.get("stale_state_flags")) or _normalize_flags(answer_plan.get("stale_state_flags")) or _normalize_flags(project_context.get("stale_state_flags")),
        "contradiction_flags": _normalize_flags(payload.get("contradiction_flags")) or _normalize_flags(answer_plan.get("contradiction_flags")) or _normalize_flags(project_context.get("contradiction_flags")),
        "missing_evidence_flags": _normalize_flags(payload.get("missing_evidence_flags")) or _normalize_flags(answer_plan.get("missing_evidence_flags")) or _normalize_flags(project_context.get("missing_evidence_flags")),
        "approval_refs": _normalize_list(payload.get("approval_refs")) or _normalize_list(answer_plan.get("approval_refs")) or _normalize_list(project_context.get("approval_refs")),
        "citations": _normalize_citations(payload.get("citations")),
        "blocked_authority": _safe_str(payload.get("blocked_authority")),
        "denied_authority": _normalize_denied_authority(payload.get("denied_authority") or answer_plan.get("denied_authority") or {}),
        "no_user_facing_output": _safe_bool(payload.get("no_user_facing_output")) if payload.get("no_user_facing_output") is not None else True,
        "answer_bounded_internal": _safe_bool(payload.get("answer_bounded_internal")) if payload.get("answer_bounded_internal") is not None else True,
        "controlled_answer_text": _safe_str(payload.get("controlled_answer_text")),
        "helper_type": HELPER_TYPE_V1,
    }
    return request


def _build_citations_from_evidence(evidence_packets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    for packet in evidence_packets:
        citations.append(
            {
                "evidence_packet_id": _safe_str(packet.get("evidence_packet_id")),
                "retrieval_request_id": _safe_str(packet.get("retrieval_request_id")),
                "source_type": _safe_str(packet.get("source_type")),
                "source_ref": _safe_str(packet.get("source_ref")),
                "source_url": _safe_str(packet.get("source_url")),
                "source_title": _safe_str(packet.get("source_title")),
                "freshness_label": _safe_str(packet.get("freshness_label")),
                "verification_status": _safe_str(packet.get("verification_status")),
                "privacy_label": _safe_str(packet.get("privacy_label")),
                "conflict_flags": _normalize_flags(packet.get("conflict_flags")),
                "missing_evidence_flags": _normalize_flags(packet.get("missing_evidence_flags")),
                "limitations": _normalize_flags(packet.get("limitations")),
            }
        )
    return citations


def _derive_controlled_answer_text(candidate: Mapping[str, Any]) -> str:
    mode = _safe_str(candidate.get("final_answer_mode"))
    citations = candidate.get("citations", [])
    limitations = _normalize_flags(candidate.get("limitations"))
    uncertainty_flags = _normalize_flags(candidate.get("uncertainty_flags"))
    missing_evidence_flags = _normalize_flags(candidate.get("missing_evidence_flags"))
    contradiction_flags = _normalize_flags(candidate.get("contradiction_flags"))
    if mode == "clarifying_question":
        text = "Internal controlled answer candidate: clarification needed before a safe answer."
    elif mode == "project_start_guidance":
        text = "Internal controlled answer candidate: project start guidance bounded by approved metadata."
    elif mode == "candidate_project_summary":
        text = "Internal controlled answer candidate: candidate project summary bounded by approved evidence."
    elif mode == "surface_gap_review_summary":
        text = "Internal controlled answer candidate: surface gap review summary bounded by approved evidence."
    elif mode == "deeper_analysis_requires_approval":
        text = "Internal controlled answer candidate: deeper analysis requires explicit approval."
    elif mode == "evidence_grounded_answer":
        text = "Internal controlled answer candidate: evidence-grounded and bounded by citations."
    elif mode == "uncertain_or_missing_evidence_answer":
        text = "Internal controlled answer candidate: evidence is incomplete or uncertain."
    elif mode == "contradiction_resolution_request":
        text = "Internal controlled answer candidate: available evidence conflicts and needs resolution."
    elif mode == "tool_request_boundary_response":
        text = "Internal controlled answer candidate: tool request remains a boundary case."
    elif mode == "blocked_boundary_response":
        text = "Internal controlled answer candidate: blocked by boundary and authority checks."
    elif mode == "operator_review_required_response":
        text = "Internal controlled answer candidate: operator review is required."
    else:
        text = "Internal controlled answer candidate: metadata-only answer packet."
    extra_bits = []
    if citations:
        extra_bits.append(f"citations={len(citations)}")
    if limitations:
        extra_bits.append(f"limitations={len(limitations)}")
    if uncertainty_flags:
        extra_bits.append(f"uncertainty={len(uncertainty_flags)}")
    if missing_evidence_flags:
        extra_bits.append(f"missing={len(missing_evidence_flags)}")
    if contradiction_flags:
        extra_bits.append(f"conflicts={len(contradiction_flags)}")
    if extra_bits:
        text = f"{text} ({'; '.join(extra_bits)})"
    return text


def build_project_chat_final_answer_request_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _coalesce_payload(payload, **overrides)
    request = _normalize_request(data)

    digest_source = {
        key: value
        for key, value in request.items()
        if key not in {"final_answer_request_id", "controlled_answer_text", "operator_visible_summary", "citations"}
    }
    digest = _stable_digest(digest_source)
    if not request["final_answer_request_id"]:
        request["final_answer_request_id"] = f"project-chat-final-answer-request-{digest[:16]}"

    if not request["citations"]:
        request["citations"] = _build_citations_from_evidence(request["evidence_packet_metadata"])

    if not request["controlled_answer_text"] and request["answer_surface"] == "internal_controlled":
        request["controlled_answer_text"] = _derive_controlled_answer_text(request)

    return request


def _validate_denied_authority(candidate: Mapping[str, Any], blocked_labels: list[str]) -> dict[str, bool]:
    denied = _as_mapping(candidate.get("denied_authority"))
    for field in DENIED_AUTHORITY_FIELDS_V1:
        if field not in denied:
            blocked_labels.append(f"missing_denied_authority_{field}")
        elif _safe_bool(denied.get(field, False)):
            blocked_labels.append(f"denied_authority_asserted_{field}")
    return {field: _safe_bool(denied.get(field, False)) for field in DENIED_AUTHORITY_FIELDS_V1}


def _validate_forbidden_texts(candidate: Mapping[str, Any], blocked_labels: list[str]) -> None:
    fields = (
        "controlled_answer_text",
        "controlled_answer_text_proposal",
        "answer_text_proposal",
        "operator_visible_summary",
        "user_visible_status",
        "source_scope",
        "answer_surface",
        "answer_visibility",
        "blocked_authority",
        "final_answer_mode",
    )
    for field in fields:
        _maybe_block_forbidden_text(field, candidate.get(field), blocked_labels)
    for item in candidate.get("citations", []):
        raw = _as_mapping(item)
        _maybe_block_forbidden_text("citation_source_title", raw.get("source_title"), blocked_labels)
        _maybe_block_forbidden_text("citation_source_ref", raw.get("source_ref"), blocked_labels)
        _maybe_block_forbidden_text("citation_source_url", raw.get("source_url"), blocked_labels)


def validate_project_chat_final_answer_request_packet_v1(packet: Any) -> dict[str, Any]:
    candidate = build_project_chat_final_answer_request_packet_v1(packet)
    blocked_labels: list[str] = []

    if candidate.get("schema_version") != SCHEMA_VERSION_V1:
        blocked_labels.append("unknown_schema_version")

    required_fields = (
        "final_answer_request_id",
        "project_id",
        "owner_user_scope",
        "tenant_account_scope",
        "source_scope",
        "user_intent_class",
        "answer_plan_metadata",
        "evidence_packet_metadata",
        "project_context_metadata",
        "answer_surface",
        "answer_visibility",
        "final_answer_mode",
        "answer_status",
    )
    for field in required_fields:
        if field in {"answer_plan_metadata", "evidence_packet_metadata", "project_context_metadata"}:
            continue
        if not _safe_str(candidate.get(field)):
            blocked_labels.append(f"missing_{field}")

    _validate_allowed_value(candidate.get("answer_surface", ""), ANSWER_SURFACES_V1, "answer_surface", blocked_labels)
    _validate_allowed_value(candidate.get("answer_visibility", ""), ANSWER_VISIBILITIES_V1, "answer_visibility", blocked_labels)
    _validate_allowed_value(candidate.get("final_answer_mode", ""), FINAL_ANSWER_MODES_V1, "final_answer_mode", blocked_labels)
    _validate_allowed_value(candidate.get("answer_status", ""), FINAL_ANSWER_STATUSES_V1, "answer_status", blocked_labels)

    answer_plan_validation = validate_project_chat_answer_plan_v1(candidate["answer_plan_metadata"])
    evidence_validations = [validate_project_chat_evidence_packet_v1(packet) for packet in candidate["evidence_packet_metadata"]]

    if answer_plan_validation["blocked"]:
        blocked_labels.append("invalid_answer_plan_metadata")
    if not candidate["evidence_packet_metadata"]:
        blocked_labels.append("missing_evidence_packet_metadata")
    if any(validation["blocked"] for validation in evidence_validations):
        blocked_labels.append("invalid_evidence_packet_metadata")

    if candidate["retrieval_required"] and not candidate["retrieval_completed"]:
        blocked_labels.append("retrieval_required_but_not_completed")
    if candidate["external_search_required"] and not candidate["external_search_approved"]:
        blocked_labels.append("external_search_required_but_not_approved")
    if candidate["external_search_required"] and not candidate["external_search_redacted"]:
        blocked_labels.append("external_search_required_but_not_redacted")

    if candidate["answer_surface"] != "internal_controlled" or candidate["answer_visibility"] != "internal_controlled":
        blocked_labels.append("non_internal_controlled_answer_surface")

    if _safe_str(candidate.get("answer_text_proposal")) and candidate["answer_surface"] != "internal_controlled":
        blocked_labels.append("answer_text_proposal_outside_internal_controlled_surface")

    if _safe_str(candidate.get("controlled_answer_text")) and candidate["answer_surface"] != "internal_controlled":
        blocked_labels.append("controlled_answer_text_outside_internal_controlled_surface")

    if not candidate["answer_plan_metadata"].get("evidence_packet_refs") and not candidate["evidence_packet_metadata"]:
        blocked_labels.append("raw_prompt_alone_is_not_enough")

    if candidate["answer_plan_metadata"].get("answer_mode") == "deeper_analysis_requires_approval" and not candidate["project_context_metadata"].get("approval_refs"):
        blocked_labels.append("deeper_analysis_requires_approval_refs")

    _validate_denied_authority(candidate, blocked_labels)
    _validate_forbidden_texts(candidate, blocked_labels)

    blocked = bool(blocked_labels)
    if blocked:
        answer_status = "invalid"
        controlled_answer_text = ""
    else:
        if candidate["uncertainty_flags"] or candidate["missing_evidence_flags"] or candidate["contradiction_flags"]:
            answer_status = "uncertain"
        elif candidate["answer_plan_metadata"].get("answer_mode") == "clarifying_question":
            answer_status = "needs_clarification"
        elif candidate["answer_plan_metadata"].get("answer_mode") == "deeper_analysis_requires_approval":
            answer_status = "needs_approval"
        elif candidate["project_context_metadata"].get("approval_refs") and candidate["answer_plan_metadata"].get("answer_mode") == "operator_review_required_response":
            answer_status = "needs_operator_review"
        else:
            answer_status = "answer_ready"
        controlled_answer_text = candidate["controlled_answer_text"] or _derive_controlled_answer_text(candidate)

    request_citations = candidate["citations"] or _build_citations_from_evidence(candidate["evidence_packet_metadata"])
    result = {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "final_answer_request": candidate,
        "final_answer_request_id": candidate["final_answer_request_id"],
        "answer_plan_validation": answer_plan_validation,
        "evidence_validations": evidence_validations,
        "answer_status": answer_status,
        "controlled_answer_text": controlled_answer_text,
        "answer_text_bounded": bool(controlled_answer_text) and not blocked,
        "blocked": blocked,
        "blocked_labels": blocked_labels,
        "validation_notes": blocked_labels[:],
        "answer_surface": candidate["answer_surface"],
        "answer_visibility": candidate["answer_visibility"],
        "final_answer_mode": candidate["final_answer_mode"],
        "project_context_metadata": candidate["project_context_metadata"],
        "answer_plan_metadata": candidate["answer_plan_metadata"],
        "evidence_packet_metadata": candidate["evidence_packet_metadata"],
        "citations": request_citations,
        "uncertainty_flags": candidate["uncertainty_flags"],
        "stale_state_flags": candidate["stale_state_flags"],
        "contradiction_flags": candidate["contradiction_flags"],
        "missing_evidence_flags": candidate["missing_evidence_flags"],
        "limitations": candidate["limitations"],
        "approval_refs": candidate["approval_refs"],
        "operator_visible_summary": candidate["operator_visible_summary"],
        "user_visible_status": candidate["user_visible_status"],
        "denied_authority": candidate["denied_authority"],
    }
    return result


def build_project_chat_final_answer_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _coalesce_payload(payload, **overrides)
    request = build_project_chat_final_answer_request_packet_v1(data)
    validation = validate_project_chat_final_answer_request_packet_v1(request)
    packet = dict(validation["final_answer_request"])
    packet.update(
        {
            "schema_version": SCHEMA_VERSION_V1,
            "helper_type": HELPER_TYPE_V1,
            "final_answer_packet_id": _safe_str(data.get("final_answer_packet_id")),
            "final_answer_request_id": validation["final_answer_request_id"],
            "final_answer_status": validation["answer_status"],
            "controlled_answer_text": validation["controlled_answer_text"],
            "answer_text_bounded": validation["answer_text_bounded"],
            "citations": validation["citations"],
            "blocked": validation["blocked"],
            "blocked_labels": validation["blocked_labels"],
            "validation_notes": validation["validation_notes"],
            "answer_plan_validation": validation["answer_plan_validation"],
            "evidence_validations": validation["evidence_validations"],
            "denied_authority": validation["denied_authority"],
            "operator_visible_summary": validation["operator_visible_summary"],
            "user_visible_status": validation["user_visible_status"],
        }
    )
    digest_source = {key: value for key, value in packet.items() if key not in {"final_answer_packet_id", "controlled_answer_text", "operator_visible_summary", "user_visible_status"}}
    digest = _stable_digest(digest_source)
    if not packet["final_answer_packet_id"]:
        packet["final_answer_packet_id"] = f"project-chat-final-answer-{digest[:16]}"
    return packet


def validate_project_chat_final_answer_packet_v1(packet: Any) -> dict[str, Any]:
    candidate = build_project_chat_final_answer_packet_v1(packet)
    blocked_labels: list[str] = []

    if candidate.get("schema_version") != SCHEMA_VERSION_V1:
        blocked_labels.append("unknown_schema_version")

    required_fields = (
        "final_answer_packet_id",
        "final_answer_request_id",
        "final_answer_status",
        "controlled_answer_text",
        "answer_surface",
        "answer_visibility",
        "final_answer_mode",
    )
    for field in required_fields:
        if not _safe_str(candidate.get(field)):
            blocked_labels.append(f"missing_{field}")

    if candidate.get("final_answer_status") == "invalid":
        blocked_labels.append("invalid_final_answer_request")
    if candidate.get("answer_text_bounded") is not True:
        blocked_labels.append("answer_text_not_bounded")

    _validate_denied_authority(candidate, blocked_labels)
    _validate_forbidden_texts(candidate, blocked_labels)

    if not candidate.get("citations"):
        blocked_labels.append("missing_citations")

    if candidate.get("answer_plan_validation", {}).get("blocked"):
        blocked_labels.append("blocked_answer_plan_metadata")
    if any(validation.get("blocked") for validation in candidate.get("evidence_validations", [])):
        blocked_labels.append("blocked_evidence_metadata")

    if candidate.get("retrieval_required") and not candidate.get("retrieval_completed"):
        blocked_labels.append("retrieval_required_but_not_completed")

    if candidate.get("external_search_required") and (not candidate.get("external_search_approved") or not candidate.get("external_search_redacted")):
        blocked_labels.append("external_search_gating_not_satisfied")

    blocked = bool(blocked_labels)
    if blocked:
        final_status = "invalid"
    else:
        final_status = candidate.get("final_answer_status") or "answer_ready"

    result = {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "final_answer_packet": candidate,
        "final_answer_packet_id": candidate["final_answer_packet_id"],
        "final_answer_request_id": candidate["final_answer_request_id"],
        "final_answer_status": final_status,
        "controlled_answer_text": candidate["controlled_answer_text"] if not blocked else "",
        "answer_text_bounded": bool(candidate.get("answer_text_bounded")) and not blocked,
        "blocked": blocked,
        "blocked_labels": blocked_labels,
        "validation_notes": blocked_labels[:],
        "citations": candidate.get("citations", []),
        "answer_plan_validation": candidate.get("answer_plan_validation", {}),
        "evidence_validations": candidate.get("evidence_validations", []),
        "uncertainty_flags": _normalize_flags(candidate.get("uncertainty_flags")),
        "stale_state_flags": _normalize_flags(candidate.get("stale_state_flags")),
        "contradiction_flags": _normalize_flags(candidate.get("contradiction_flags")),
        "missing_evidence_flags": _normalize_flags(candidate.get("missing_evidence_flags")),
        "limitations": _normalize_flags(candidate.get("limitations")),
        "approval_refs": _normalize_list(candidate.get("approval_refs")),
        "operator_visible_summary": _safe_str(candidate.get("operator_visible_summary")),
        "user_visible_status": _safe_str(candidate.get("user_visible_status")),
        "denied_authority": candidate.get("denied_authority", {}),
    }
    return result


def _summarize_final_answer_status(candidate: Mapping[str, Any], blocked: bool) -> str:
    if blocked:
        return "final answer blocked"
    if _normalize_flags(candidate.get("uncertainty_flags")) or _normalize_flags(candidate.get("missing_evidence_flags")):
        return "final answer uncertain"
    if _normalize_flags(candidate.get("contradiction_flags")):
        return "final answer conflict-aware"
    return "final answer metadata only"


def summarize_project_chat_final_answer_packet_v1(packet: Any) -> dict[str, Any]:
    candidate = build_project_chat_final_answer_packet_v1(packet)
    validation = validate_project_chat_final_answer_packet_v1(candidate)
    summary_text = (
        f"{_summarize_final_answer_status(candidate, validation['blocked'])} | "
        f"mode={_safe_str(candidate.get('final_answer_mode'))} | "
        f"citations={len(validation.get('citations', []))} | "
        f"missing={len(validation.get('missing_evidence_flags', []))} | "
        f"conflicts={len(validation.get('contradiction_flags', []))}"
    )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "final_answer_packet_id": validation["final_answer_packet_id"],
        "final_answer_request_id": validation["final_answer_request_id"],
        "summary_text": summary_text,
        "final_answer_status": validation["final_answer_status"],
        "answer_text_bounded": validation["answer_text_bounded"],
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "citations": validation["citations"],
        "uncertainty_flags": validation["uncertainty_flags"],
        "stale_state_flags": validation["stale_state_flags"],
        "contradiction_flags": validation["contradiction_flags"],
        "missing_evidence_flags": validation["missing_evidence_flags"],
        "limitations": validation["limitations"],
        "operator_visible_summary": validation["operator_visible_summary"],
    }


def to_project_chat_final_answer_json_safe_v1(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): to_project_chat_final_answer_json_safe_v1(val) for key, val in value.items()}
    if isinstance(value, list):
        return [to_project_chat_final_answer_json_safe_v1(item) for item in value]
    if isinstance(value, tuple):
        return [to_project_chat_final_answer_json_safe_v1(item) for item in value]
    if isinstance(value, set):
        return [to_project_chat_final_answer_json_safe_v1(item) for item in sorted(value, key=lambda item: _safe_str(item))]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _safe_str(value)


def build_initial_project_chat_final_answer_examples_v1() -> list[dict[str, Any]]:
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
            "denied_authority": {field: False for field in RAG_DENIED_AUTHORITY_FIELDS_V1},
        }
    )
    examples = [
        build_project_chat_final_answer_request_packet_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "user_intent_class": "project-chat",
                "answer_plan_metadata": answer_plan,
                "evidence_packet_metadata": [evidence],
                "project_context_metadata": {
                    "project_state_refs": ["project-state-001"],
                    "memory_state_refs": ["memory-state-001"],
                    "continuity_state_refs": ["continuity-state-001"],
                    "approval_refs": ["approval-001"],
                    "user_visible_status": "evidence grounded answer",
                    "operator_visible_summary": "evidence grounded; metadata only",
                },
                "answer_surface": "internal_controlled",
                "answer_visibility": "internal_controlled",
                "retrieval_required": False,
                "retrieval_completed": True,
                "controlled_answer_text_proposal": "Internal controlled answer candidate: evidence-grounded and bounded by citations.",
                "denied_authority": {field: False for field in DENIED_AUTHORITY_FIELDS_V1},
            }
        ),
        build_project_chat_final_answer_request_packet_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "user_intent_class": "project-chat",
                "answer_plan_metadata": build_project_chat_answer_plan_v1(
                    {
                        "project_id": "project-001",
                        "owner_user_scope": "owner-user",
                        "tenant_account_scope": "tenant-a",
                        "source_scope": "project_metadata_only",
                        "user_intent_class": "project-chat",
                        "answer_mode": "uncertain_or_missing_evidence_answer",
                        "allowed_answer_scope": "approved_evidence_packet",
                        "answer_status": "plan_valid_metadata_only",
                        "missing_evidence_flags": ["missing_project_context"],
                        "user_visible_status": "evidence incomplete",
                    }
                ),
                "evidence_packet_metadata": [evidence],
                "project_context_metadata": {
                    "missing_evidence_flags": ["missing_project_context"],
                    "user_visible_status": "evidence incomplete",
                    "operator_visible_summary": "evidence incomplete; metadata only",
                },
                "answer_surface": "internal_controlled",
                "answer_visibility": "internal_controlled",
                "retrieval_required": False,
                "retrieval_completed": True,
                "controlled_answer_text_proposal": "Internal controlled answer candidate: evidence is incomplete or uncertain.",
                "denied_authority": {field: False for field in DENIED_AUTHORITY_FIELDS_V1},
            }
        ),
        build_project_chat_final_answer_request_packet_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "user_intent_class": "project-chat",
                "answer_plan_metadata": build_project_chat_answer_plan_v1(
                    {
                        "project_id": "project-001",
                        "owner_user_scope": "owner-user",
                        "tenant_account_scope": "tenant-a",
                        "source_scope": "project_metadata_only",
                        "user_intent_class": "project-chat",
                        "answer_mode": "clarifying_question",
                        "allowed_answer_scope": "current_message_only",
                        "answer_status": "clarification_required",
                        "user_visible_status": "clarification needed",
                    }
                ),
                "evidence_packet_metadata": [evidence],
                "project_context_metadata": {
                    "user_visible_status": "clarification needed",
                    "operator_visible_summary": "clarification needed; metadata only",
                },
                "answer_surface": "internal_controlled",
                "answer_visibility": "internal_controlled",
                "retrieval_required": False,
                "retrieval_completed": True,
                "controlled_answer_text_proposal": "Internal controlled answer candidate: clarification needed before a safe answer.",
                "denied_authority": {field: False for field in DENIED_AUTHORITY_FIELDS_V1},
            }
        ),
    ]
    return examples


__all__ = [
    "HELPER_TYPE_V1",
    "SCHEMA_VERSION_V1",
    "ANSWER_SURFACES_V1",
    "ANSWER_VISIBILITIES_V1",
    "FINAL_ANSWER_STATUSES_V1",
    "FINAL_ANSWER_MODES_V1",
    "DENIED_AUTHORITY_FIELDS_V1",
    "allowed_project_chat_final_answer_surfaces_v1",
    "allowed_project_chat_final_answer_visibilities_v1",
    "allowed_project_chat_final_answer_statuses_v1",
    "allowed_project_chat_final_answer_modes_v1",
    "build_project_chat_final_answer_request_packet_v1",
    "validate_project_chat_final_answer_request_packet_v1",
    "build_project_chat_final_answer_packet_v1",
    "validate_project_chat_final_answer_packet_v1",
    "summarize_project_chat_final_answer_packet_v1",
    "to_project_chat_final_answer_json_safe_v1",
    "build_initial_project_chat_final_answer_examples_v1",
]
