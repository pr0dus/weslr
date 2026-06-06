"""Metadata-only helpers for WESLR project-chat RAG and evidence retrieval V1.

This module is intentionally pure, deterministic, synthetic/example-safe,
and fail-closed.
It builds and validates retrieval-request and evidence-packet metadata only.

It does not perform file I/O, network I/O, shell execution, runtime/chat
wiring, live retrieval, model calls, tool execution, external actions,
persistence, or final answer generation.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

HELPER_TYPE_V1 = "weslr_project_chat_rag_evidence_retrieval_v1"
SCHEMA_VERSION_V1 = "project_chat_rag_evidence_retrieval_v1"

RETRIEVAL_NEEDS_V1 = (
    "no_retrieval_needed",
    "project_metadata_retrieval_needed",
    "approved_project_file_retrieval_needed",
    "memory_continuity_retrieval_needed",
    "local_index_retrieval_needed",
    "external_web_search_needed",
    "user_approval_required_before_retrieval",
    "operator_review_required_before_retrieval",
    "retrieval_blocked",
)

QUERY_CLASSES_V1 = (
    "blocked_query",
    "direct_project_query",
    "freshness_sensitive_web_query",
    "general_web_query",
    "redacted_project_query",
    "source_specific_query",
)

SOURCE_CLASSES_V1 = (
    "approved_project_artifact",
    "approved_uploaded_file",
    "blocked_source",
    "continuity_metadata",
    "external_web_search",
    "gap_analysis_metadata",
    "local_project_index",
    "memory_metadata",
    "operator_review_note",
    "project_files",
    "project_metadata",
    "project_state",
    "searxng_search_result",
    "tool_lane_metadata",
)

RETRIEVAL_ADAPTERS_V1 = (
    "ApprovedProjectArtifactAdapter",
    "ApprovedUploadedFileAdapter",
    "BlockedSourceAdapter",
    "ContinuityStateMetadataAdapter",
    "ExternalWebSearchAdapter",
    "LocalProjectIndexAdapter",
    "MemoryStateMetadataAdapter",
    "PrivateProjectGapMetadataAdapter",
    "ProjectStateMetadataAdapter",
    "SearXNGExternalSearchAdapter",
    "ToolLaneContractMetadataAdapter",
)

FRESHNESS_LABELS_V1 = (
    "fresh_current",
    "fresh_recent",
    "possibly_stale",
    "stale",
    "unknown_freshness",
)

RELEVANCE_LABELS_V1 = (
    "high_relevance",
    "medium_relevance",
    "low_relevance",
    "unknown_relevance",
)

CONFIDENCE_LABELS_V1 = (
    "high_confidence",
    "medium_confidence",
    "low_confidence",
    "uncertain",
)

VERIFICATION_STATUSES_V1 = (
    "blocked",
    "conflict_review_required",
    "freshness_labeled",
    "metadata_only",
    "provenance_labeled",
    "unverified",
)

PRIVACY_LABELS_V1 = (
    "cross_user_blocked",
    "external_unverified",
    "project_private",
    "public",
    "sensitive",
)

QUERY_REDACTION_STATUSES_V1 = (
    "applied",
    "blocked",
    "not_required",
    "required",
)

APPROVAL_STATUSES_V1 = (
    "approved",
    "not_required",
    "pending",
    "rejected",
)

CONSENT_STATUSES_V1 = (
    "blocked",
    "missing",
    "not_required",
    "provided",
)

SOURCE_TYPES_V1 = (
    "approved_project_artifact",
    "approved_uploaded_file",
    "blocked_source",
    "continuity_metadata",
    "external_web_search",
    "gap_analysis_metadata",
    "local_project_index",
    "memory_metadata",
    "operator_review_note",
    "project_files",
    "project_metadata",
    "project_state",
    "searxng_search_result",
    "tool_lane_metadata",
)

DENIED_AUTHORITY_FIELDS_V1 = (
    "runtime_wiring_authority",
    "chat" + "_" + "responder_authority",
    "final_answer_generation_authority",
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
    "public_product_readiness_authority",
)

FORBIDDEN_LEAKAGE_PHRASES_V1 = (
    "unknown engine",
    "." + "weslr",
    "hidden prompt",
    "system prompt",
    "private mechanism",
    "hidden system",
    "raw private",
    "raw secret",
    "secret",
    "tool executed",
    "i executed",
    "i searched",
    "i saved",
    "i found the truth",
    "the web confirms",
    "searxng proves",
    "proof",
    "proven",
    "solved",
    "certified",
    "public readiness",
    "final answer",
)

_DEFAULT_FALSE_DENIED_AUTHORITY = {field: False for field in DENIED_AUTHORITY_FIELDS_V1}


def allowed_project_chat_rag_retrieval_needs_v1() -> tuple[str, ...]:
    return RETRIEVAL_NEEDS_V1


def allowed_project_chat_rag_query_classes_v1() -> tuple[str, ...]:
    return QUERY_CLASSES_V1


def allowed_project_chat_rag_source_classes_v1() -> tuple[str, ...]:
    return SOURCE_CLASSES_V1


def allowed_project_chat_rag_adapters_v1() -> tuple[str, ...]:
    return RETRIEVAL_ADAPTERS_V1


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


def _normalize_denied_authority(value: Any) -> dict[str, bool]:
    payload = dict(_DEFAULT_FALSE_DENIED_AUTHORITY)
    raw = _as_mapping(value)
    for field in DENIED_AUTHORITY_FIELDS_V1:
        payload[field] = _safe_bool(raw.get(field, False))
    return payload


def _normalize_flags(value: Any) -> list[str]:
    return _normalize_list(value)


def _normalize_source_type(value: Any) -> str:
    source_type = _safe_str(value)
    if source_type in SOURCE_TYPES_V1:
        return source_type
    if source_type in {"project_file", "project_artifact", "uploaded_file", "project_document"}:
        return "project_files"
    return source_type


def _infer_retrieval_need_from_source_class(source_class: str, query_class: str, privacy_sensitivity: str) -> str:
    if source_class in {"project_metadata", "project_state", "project_files", "approved_project_artifact", "approved_uploaded_file", "tool_lane_metadata", "gap_analysis_metadata", "operator_review_note"}:
        return "project_metadata_retrieval_needed"
    if source_class in {"memory_metadata", "continuity_metadata"}:
        return "memory_continuity_retrieval_needed"
    if source_class == "local_project_index":
        return "local_index_retrieval_needed"
    if source_class in {"external_web_search", "searxng_search_result"}:
        return "external_web_search_needed"
    if query_class == "blocked_query":
        return "retrieval_blocked"
    if privacy_sensitivity in {"cross_user", "system_wide", "high_stakes"}:
        return "operator_review_required_before_retrieval"
    return "no_retrieval_needed"


def _infer_query_class(retrieval_need_class: str, freshness_sensitive: bool) -> str:
    if retrieval_need_class == "external_web_search_needed":
        return "freshness_sensitive_web_query" if freshness_sensitive else "general_web_query"
    if retrieval_need_class in {
        "project_metadata_retrieval_needed",
        "approved_project_file_retrieval_needed",
        "memory_continuity_retrieval_needed",
        "local_index_retrieval_needed",
    }:
        return "source_specific_query"
    if retrieval_need_class == "retrieval_blocked":
        return "blocked_query"
    if retrieval_need_class in {"user_approval_required_before_retrieval", "operator_review_required_before_retrieval"}:
        return "redacted_project_query"
    return "direct_project_query"


def _infer_retrieval_adapter(source_class: str) -> str:
    return {
        "project_metadata": "ProjectStateMetadataAdapter",
        "project_state": "ProjectStateMetadataAdapter",
        "project_files": "ApprovedProjectArtifactAdapter",
        "approved_project_artifact": "ApprovedProjectArtifactAdapter",
        "approved_uploaded_file": "ApprovedUploadedFileAdapter",
        "memory_metadata": "MemoryStateMetadataAdapter",
        "continuity_metadata": "ContinuityStateMetadataAdapter",
        "gap_analysis_metadata": "PrivateProjectGapMetadataAdapter",
        "tool_lane_metadata": "ToolLaneContractMetadataAdapter",
        "local_project_index": "LocalProjectIndexAdapter",
        "external_web_search": "ExternalWebSearchAdapter",
        "searxng_search_result": "SearXNGExternalSearchAdapter",
        "operator_review_note": "BlockedSourceAdapter",
        "blocked_source": "BlockedSourceAdapter",
    }.get(source_class, "ProjectStateMetadataAdapter")


def _privacy_label_from_sensitivity(privacy_sensitivity: str) -> str:
    return {
        "public": "public",
        "low": "public",
        "sensitive": "sensitive",
        "confidential": "sensitive",
        "project_private": "project_private",
        "cross_user": "cross_user_blocked",
        "system_wide": "cross_user_blocked",
        "high_stakes": "external_unverified",
    }.get(privacy_sensitivity, "project_private")


def _default_query_redaction_status(privacy_sensitivity: str, redaction_required: bool) -> str:
    if redaction_required or privacy_sensitivity in {"sensitive", "confidential", "cross_user", "system_wide", "high_stakes"}:
        return "required"
    return "not_required"


def _find_forbidden_phrase_hits_v1(text: Any) -> list[str]:
    candidate = _safe_str(text).lower()
    hits: list[str] = []
    for phrase in FORBIDDEN_LEAKAGE_PHRASES_V1:
        if phrase.lower() in candidate:
            hits.append(phrase)
    return hits


def _validate_allowed_value(value: str, allowed: tuple[str, ...], label: str, blocked_labels: list[str]) -> bool:
    if not value:
        blocked_labels.append(f"missing_{label}")
        return False
    if value not in allowed:
        blocked_labels.append(f"unknown_{label}")
        return False
    return True


def _maybe_block_for_forbidden_text(field_name: str, text: Any, blocked_labels: list[str]) -> None:
    for phrase in _find_forbidden_phrase_hits_v1(text):
        blocked_labels.append(f"{field_name}_forbidden_phrase_{_slugify_v1(phrase)}")


def _classify_project_chat_retrieval_need_candidate(candidate: Mapping[str, Any], blocked: bool) -> str:
    retrieval_need_class = _safe_str(candidate.get("retrieval_need_class"))
    query_class = _safe_str(candidate.get("query_class"))
    privacy_sensitivity = _safe_str(candidate.get("privacy_sensitivity"))

    if blocked:
        return "retrieval_blocked"
    if retrieval_need_class == "external_web_search_needed":
        if candidate.get("approval_status") != "approved" or not candidate.get("external_query_allowed"):
            return "user_approval_required_before_retrieval"
        if candidate.get("operator_review_required") or privacy_sensitivity in {"cross_user", "system_wide", "high_stakes"}:
            return "operator_review_required_before_retrieval"
        return "external_web_search_needed"
    if retrieval_need_class in {
        "project_metadata_retrieval_needed",
        "approved_project_file_retrieval_needed",
        "memory_continuity_retrieval_needed",
        "local_index_retrieval_needed",
    }:
        return retrieval_need_class
    if retrieval_need_class in {"user_approval_required_before_retrieval", "operator_review_required_before_retrieval", "retrieval_blocked"}:
        return retrieval_need_class
    if query_class == "blocked_query":
        return "retrieval_blocked"
    if privacy_sensitivity in {"cross_user", "system_wide", "high_stakes"}:
        return "operator_review_required_before_retrieval"
    return retrieval_need_class or "no_retrieval_needed"


def _slugify_v1(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", _safe_str(text).lower()).strip("_")
    return slug or "forbidden_phrase"


def _normalize_request(payload: Mapping[str, Any]) -> dict[str, Any]:
    source_class = _normalize_source_type(payload.get("source_class"))
    privacy_sensitivity = _safe_str(payload.get("privacy_sensitivity")) or "project_private"
    retrieval_need_class = _safe_str(payload.get("retrieval_need_class"))
    query_class = _safe_str(payload.get("query_class"))
    freshness_sensitive = _safe_bool(payload.get("freshness_sensitive"))
    if not retrieval_need_class:
        retrieval_need_class = _infer_retrieval_need_from_source_class(source_class, query_class, privacy_sensitivity)
    if not query_class:
        query_class = _infer_query_class(retrieval_need_class, freshness_sensitive)
    retrieval_adapter = _safe_str(payload.get("retrieval_adapter")) or _infer_retrieval_adapter(source_class)
    request = {
        "schema_version": _safe_str(payload.get("schema_version")) or SCHEMA_VERSION_V1,
        "retrieval_request_id": _safe_str(payload.get("retrieval_request_id")),
        "project_id": _safe_str(payload.get("project_id")),
        "owner_user_scope": _safe_str(payload.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(payload.get("tenant_account_scope")),
        "source_scope": _safe_str(payload.get("source_scope")),
        "user_intent_class": _safe_str(payload.get("user_intent_class")),
        "retrieval_need_class": retrieval_need_class,
        "query_class": query_class,
        "retrieval_adapter": retrieval_adapter,
        "source_class": source_class,
        "requested_source_types": _normalize_list(payload.get("requested_source_types")),
        "allowed_source_types": _normalize_list(payload.get("allowed_source_types")),
        "disallowed_source_types": _normalize_list(payload.get("disallowed_source_types")),
        "source_ref": _safe_str(payload.get("source_ref")),
        "source_url": _safe_str(payload.get("source_url")),
        "source_title": _safe_str(payload.get("source_title")),
        "source_timestamp": _safe_str(payload.get("source_timestamp")),
        "retrieved_at_marker": _safe_str(payload.get("retrieved_at_marker")),
        "query_text": _safe_str(payload.get("query_text")),
        "redacted_query_text": _safe_str(payload.get("redacted_query_text")),
        "freshness_label": _safe_str(payload.get("freshness_label")),
        "relevance_label": _safe_str(payload.get("relevance_label")),
        "confidence_label": _safe_str(payload.get("confidence_label")),
        "verification_status": _safe_str(payload.get("verification_status")) or "metadata_only",
        "privacy_label": _safe_str(payload.get("privacy_label")) or _privacy_label_from_sensitivity(privacy_sensitivity),
        "privacy_sensitivity": privacy_sensitivity,
        "query_redaction_status": _safe_str(payload.get("query_redaction_status")) or _default_query_redaction_status(privacy_sensitivity, _safe_bool(payload.get("redaction_required"))),
        "user_approval_ref": _safe_str(payload.get("user_approval_ref")),
        "operator_review_ref": _safe_str(payload.get("operator_review_ref")),
        "approval_status": _safe_str(payload.get("approval_status")) or "not_required",
        "consent_status": _safe_str(payload.get("consent_status")) or "not_required",
        "external_query_allowed": _safe_bool(payload.get("external_query_allowed")),
        "redaction_required": _safe_bool(payload.get("redaction_required")),
        "operator_review_required": _safe_bool(payload.get("operator_review_required")),
        "freshness_sensitive": freshness_sensitive,
        "evidence_summary": _safe_str(payload.get("evidence_summary")),
        "limitations": _normalize_flags(payload.get("limitations")),
        "conflict_flags": _normalize_flags(payload.get("conflict_flags")),
        "missing_evidence_flags": _normalize_flags(payload.get("missing_evidence_flags")),
        "evidence_packet_refs": _normalize_list(payload.get("evidence_packet_refs")),
        "project_state_refs": _normalize_list(payload.get("project_state_refs")),
        "memory_state_refs": _normalize_list(payload.get("memory_state_refs")),
        "continuity_state_refs": _normalize_list(payload.get("continuity_state_refs")),
        "gap_analysis_refs": _normalize_list(payload.get("gap_analysis_refs")),
        "tool_lane_candidate_refs": _normalize_list(payload.get("tool_lane_candidate_refs")),
        "external_search_adapter_refs": _normalize_list(payload.get("external_search_adapter_refs")),
        "direct_to_answer_requested": _safe_bool(payload.get("direct_to_answer_requested")),
        "final_answer_requested": _safe_bool(payload.get("final_answer_requested")),
        "live_retrieval_requested": _safe_bool(payload.get("live_retrieval_requested")),
        "provider_search_requested": _safe_bool(payload.get("provider_search_requested")),
        "tool_execution_requested": _safe_bool(payload.get("tool_execution_requested")),
        "blocked_reason": _safe_str(payload.get("blocked_reason")),
        "helper_type": HELPER_TYPE_V1,
        "denied_authority": _normalize_denied_authority(payload.get("denied_authority")),
    }
    return request


def _normalize_evidence(payload: Mapping[str, Any]) -> dict[str, Any]:
    source_type = _normalize_source_type(payload.get("source_type"))
    privacy_sensitivity = _safe_str(payload.get("privacy_sensitivity")) or "project_private"
    source_title = _safe_str(payload.get("source_title"))
    source_ref = _safe_str(payload.get("source_ref"))
    evidence = {
        "schema_version": _safe_str(payload.get("schema_version")) or SCHEMA_VERSION_V1,
        "evidence_packet_id": _safe_str(payload.get("evidence_packet_id")),
        "retrieval_request_id": _safe_str(payload.get("retrieval_request_id")),
        "project_id": _safe_str(payload.get("project_id")),
        "owner_user_scope": _safe_str(payload.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(payload.get("tenant_account_scope")),
        "source_scope": _safe_str(payload.get("source_scope")),
        "retrieval_need_class": _safe_str(payload.get("retrieval_need_class")),
        "retrieval_adapter": _safe_str(payload.get("retrieval_adapter")) or _infer_retrieval_adapter(source_type),
        "source_type": source_type,
        "source_ref": source_ref,
        "source_url": _safe_str(payload.get("source_url")),
        "source_title": source_title,
        "source_timestamp": _safe_str(payload.get("source_timestamp")),
        "retrieved_at_marker": _safe_str(payload.get("retrieved_at_marker")),
        "freshness_label": _safe_str(payload.get("freshness_label")),
        "relevance_label": _safe_str(payload.get("relevance_label")),
        "confidence_label": _safe_str(payload.get("confidence_label")),
        "verification_status": _safe_str(payload.get("verification_status")) or "metadata_only",
        "privacy_label": _safe_str(payload.get("privacy_label")) or _privacy_label_from_sensitivity(privacy_sensitivity),
        "privacy_sensitivity": privacy_sensitivity,
        "query_redaction_status": _safe_str(payload.get("query_redaction_status")) or _default_query_redaction_status(privacy_sensitivity, _safe_bool(payload.get("redaction_required"))),
        "user_approval_ref": _safe_str(payload.get("user_approval_ref")),
        "operator_review_ref": _safe_str(payload.get("operator_review_ref")),
        "evidence_summary": _safe_str(payload.get("evidence_summary")),
        "limitations": _normalize_flags(payload.get("limitations")),
        "conflict_flags": _normalize_flags(payload.get("conflict_flags")),
        "missing_evidence_flags": _normalize_flags(payload.get("missing_evidence_flags")),
        "requested_source_types": _normalize_list(payload.get("requested_source_types")),
        "allowed_source_types": _normalize_list(payload.get("allowed_source_types")),
        "disallowed_source_types": _normalize_list(payload.get("disallowed_source_types")),
        "evidence_packet_refs": _normalize_list(payload.get("evidence_packet_refs")),
        "project_state_refs": _normalize_list(payload.get("project_state_refs")),
        "memory_state_refs": _normalize_list(payload.get("memory_state_refs")),
        "continuity_state_refs": _normalize_list(payload.get("continuity_state_refs")),
        "gap_analysis_refs": _normalize_list(payload.get("gap_analysis_refs")),
        "tool_lane_candidate_refs": _normalize_list(payload.get("tool_lane_candidate_refs")),
        "external_search_adapter_refs": _normalize_list(payload.get("external_search_adapter_refs")),
        "source_summary_refs": _normalize_list(payload.get("source_summary_refs")),
        "direct_to_answer_requested": _safe_bool(payload.get("direct_to_answer_requested")),
        "final_answer_requested": _safe_bool(payload.get("final_answer_requested")),
        "live_retrieval_requested": _safe_bool(payload.get("live_retrieval_requested")),
        "provider_search_requested": _safe_bool(payload.get("provider_search_requested")),
        "tool_execution_requested": _safe_bool(payload.get("tool_execution_requested")),
        "blocked_reason": _safe_str(payload.get("blocked_reason")),
        "helper_type": HELPER_TYPE_V1,
        "denied_authority": _normalize_denied_authority(payload.get("denied_authority")),
    }
    return evidence


def _coalesce_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = {}
    if isinstance(payload, Mapping):
        data.update(payload)
    elif payload is not None:
        data["payload"] = payload
    data.update(overrides)
    return data


def build_project_chat_rag_request_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _coalesce_payload(payload, **overrides)
    request = _normalize_request(data)

    digest_source = {
        key: value
        for key, value in request.items()
        if key not in {"retrieval_request_id", "evidence_summary"}
    }
    digest = _stable_digest(digest_source)
    if not request["retrieval_request_id"]:
        request["retrieval_request_id"] = f"project-chat-rag-request-{digest[:16]}"

    if not request["evidence_summary"]:
        request["evidence_summary"] = "metadata only"
    return request


def build_project_chat_evidence_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _coalesce_payload(payload, **overrides)
    evidence = _normalize_evidence(data)

    digest_source = {
        key: value
        for key, value in evidence.items()
        if key not in {"evidence_packet_id", "evidence_summary"}
    }
    digest = _stable_digest(digest_source)
    if not evidence["evidence_packet_id"]:
        evidence["evidence_packet_id"] = f"project-chat-evidence-{digest[:16]}"

    if not evidence["evidence_summary"]:
        evidence["evidence_summary"] = "evidence packet metadata only"
    return evidence


def validate_project_chat_rag_request_packet_v1(packet: Any) -> dict[str, Any]:
    candidate = build_project_chat_rag_request_packet_v1(packet)
    blocked_labels: list[str] = []

    if candidate.get("schema_version") != SCHEMA_VERSION_V1:
        blocked_labels.append("unknown_schema_version")

    required_fields = (
        "retrieval_request_id",
        "project_id",
        "owner_user_scope",
        "tenant_account_scope",
        "source_scope",
        "user_intent_class",
        "retrieval_need_class",
        "query_class",
        "retrieval_adapter",
        "source_class",
        "privacy_sensitivity",
        "approval_status",
        "consent_status",
        "query_redaction_status",
        "verification_status",
        "freshness_label",
        "relevance_label",
        "confidence_label",
    )
    for field in required_fields:
        if not _safe_str(candidate.get(field)):
            blocked_labels.append(f"missing_{field}")

    _validate_allowed_value(candidate.get("retrieval_need_class", ""), RETRIEVAL_NEEDS_V1, "retrieval_need_class", blocked_labels)
    _validate_allowed_value(candidate.get("query_class", ""), QUERY_CLASSES_V1, "query_class", blocked_labels)
    _validate_allowed_value(candidate.get("source_class", ""), SOURCE_CLASSES_V1, "source_class", blocked_labels)
    _validate_allowed_value(candidate.get("retrieval_adapter", ""), RETRIEVAL_ADAPTERS_V1, "retrieval_adapter", blocked_labels)
    _validate_allowed_value(candidate.get("freshness_label", ""), FRESHNESS_LABELS_V1, "freshness_label", blocked_labels)
    _validate_allowed_value(candidate.get("relevance_label", ""), RELEVANCE_LABELS_V1, "relevance_label", blocked_labels)
    _validate_allowed_value(candidate.get("confidence_label", ""), CONFIDENCE_LABELS_V1, "confidence_label", blocked_labels)
    _validate_allowed_value(candidate.get("verification_status", ""), VERIFICATION_STATUSES_V1, "verification_status", blocked_labels)
    _validate_allowed_value(candidate.get("privacy_label", ""), PRIVACY_LABELS_V1, "privacy_label", blocked_labels)
    _validate_allowed_value(candidate.get("query_redaction_status", ""), QUERY_REDACTION_STATUSES_V1, "query_redaction_status", blocked_labels)
    _validate_allowed_value(candidate.get("approval_status", ""), APPROVAL_STATUSES_V1, "approval_status", blocked_labels)
    _validate_allowed_value(candidate.get("consent_status", ""), CONSENT_STATUSES_V1, "consent_status", blocked_labels)

    if not _safe_str(candidate.get("query_text")) and not _safe_str(candidate.get("redacted_query_text")):
        blocked_labels.append("missing_query_text")

    if candidate.get("direct_to_answer_requested"):
        blocked_labels.append("direct_to_answer_requested")
    if candidate.get("final_answer_requested"):
        blocked_labels.append("final_answer_requested")
    if candidate.get("live_retrieval_requested"):
        blocked_labels.append("live_retrieval_requested")
    if candidate.get("provider_search_requested"):
        blocked_labels.append("provider_search_requested")
    if candidate.get("tool_execution_requested"):
        blocked_labels.append("tool_execution_requested")

    retrieval_need_class = _safe_str(candidate.get("retrieval_need_class"))
    source_class = _safe_str(candidate.get("source_class"))
    query_text = _safe_str(candidate.get("query_text"))
    redacted_query_text = _safe_str(candidate.get("redacted_query_text"))
    privacy_sensitivity = _safe_str(candidate.get("privacy_sensitivity"))

    if retrieval_need_class == "external_web_search_needed":
        if not candidate.get("external_query_allowed"):
            blocked_labels.append("missing_external_query_permission")
        if candidate.get("approval_status") != "approved":
            blocked_labels.append("missing_user_approval_for_external_search")
        if candidate.get("query_redaction_status") != "applied":
            blocked_labels.append("external_search_requires_applied_redaction")

    if candidate.get("redaction_required") and candidate.get("query_redaction_status") != "applied":
        blocked_labels.append("missing_query_redaction_metadata")

    if privacy_sensitivity in {"sensitive", "confidential", "cross_user", "system_wide", "high_stakes"} and candidate.get("query_redaction_status") != "applied":
        blocked_labels.append("sensitive_query_requires_redacted_metadata")

    if privacy_sensitivity in {"cross_user", "system_wide", "high_stakes"} and not candidate.get("operator_review_required"):
        blocked_labels.append("missing_operator_review_requirement")

    if candidate.get("operator_review_required") and not _safe_str(candidate.get("operator_review_ref")):
        blocked_labels.append("missing_operator_review_ref")

    if candidate.get("external_query_allowed") and retrieval_need_class in {"operator_review_required_before_retrieval", "retrieval_blocked"} and not _safe_str(candidate.get("blocked_reason")):
        blocked_labels.append("missing_blocked_reason")

    if source_class in {"external_web_search", "searxng_search_result"} and retrieval_need_class != "external_web_search_needed":
        blocked_labels.append("source_class_mismatch_for_external_search")
    if source_class in {"memory_metadata", "continuity_metadata"} and retrieval_need_class not in {"memory_continuity_retrieval_needed", "no_retrieval_needed"}:
        blocked_labels.append("source_class_mismatch_for_memory_continuity")
    if source_class in {"local_project_index"} and retrieval_need_class not in {"local_index_retrieval_needed", "no_retrieval_needed"}:
        blocked_labels.append("source_class_mismatch_for_local_index")

    _maybe_block_for_forbidden_text("query_text", query_text, blocked_labels)
    _maybe_block_for_forbidden_text("redacted_query_text", redacted_query_text, blocked_labels)
    _maybe_block_for_forbidden_text("evidence_summary", candidate.get("evidence_summary"), blocked_labels)
    _maybe_block_for_forbidden_text("source_title", candidate.get("source_title"), blocked_labels)
    _maybe_block_for_forbidden_text("source_ref", candidate.get("source_ref"), blocked_labels)
    _maybe_block_for_forbidden_text("source_url", candidate.get("source_url"), blocked_labels)
    _maybe_block_for_forbidden_text("blocked_reason", candidate.get("blocked_reason"), blocked_labels)

    denied = _as_mapping(candidate.get("denied_authority"))
    for field in DENIED_AUTHORITY_FIELDS_V1:
        if field not in denied:
            blocked_labels.append(f"missing_denied_authority_{field}")
        elif _safe_bool(denied.get(field, False)):
            blocked_labels.append(f"denied_authority_asserted_{field}")

    if not candidate.get("external_query_allowed") and retrieval_need_class == "external_web_search_needed":
        blocked_labels.append("external_web_search_requires_permission")

    if not _safe_str(candidate.get("source_class")):
        blocked_labels.append("missing_source_class")

    if not _safe_str(candidate.get("retrieval_adapter")):
        blocked_labels.append("missing_retrieval_adapter")

    blocked = bool(blocked_labels)
    classification = _classify_project_chat_retrieval_need_candidate(candidate, blocked)

    result = {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "retrieval_request": candidate,
        "retrieval_request_id": candidate["retrieval_request_id"],
        "retrieval_need_class": retrieval_need_class,
        "query_class": _safe_str(candidate.get("query_class")),
        "source_class": source_class,
        "retrieval_adapter": _safe_str(candidate.get("retrieval_adapter")),
        "classification": classification,
        "blocked": blocked,
        "blocked_labels": blocked_labels,
        "validation_notes": blocked_labels[:],
        "needs_redaction": candidate.get("query_redaction_status") == "required" or candidate.get("redaction_required"),
        "needs_user_approval": retrieval_need_class == "external_web_search_needed" and candidate.get("approval_status") != "approved",
        "needs_operator_review": bool(candidate.get("operator_review_required")) or privacy_sensitivity in {"cross_user", "system_wide", "high_stakes"},
        "denied_authority": dict(denied),
        "query_redaction_status": _safe_str(candidate.get("query_redaction_status")),
        "privacy_label": _safe_str(candidate.get("privacy_label")),
        "privacy_sensitivity": privacy_sensitivity,
    }
    return result


def classify_project_chat_retrieval_need_v1(packet: Any) -> dict[str, Any]:
    validation = validate_project_chat_rag_request_packet_v1(packet)
    candidate = validation["retrieval_request"]

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "classification": validation["classification"],
        "retrieval_need_class": _safe_str(candidate.get("retrieval_need_class")),
        "query_class": _safe_str(candidate.get("query_class")),
        "source_class": _safe_str(candidate.get("source_class")),
        "retrieval_adapter": _safe_str(candidate.get("retrieval_adapter")),
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "needs_redaction": validation["needs_redaction"],
        "needs_user_approval": validation["needs_user_approval"],
        "needs_operator_review": validation["needs_operator_review"],
        "retrieval_request_id": candidate["retrieval_request_id"],
    }


def validate_project_chat_evidence_packet_v1(packet: Any) -> dict[str, Any]:
    candidate = build_project_chat_evidence_packet_v1(packet)
    blocked_labels: list[str] = []

    if candidate.get("schema_version") != SCHEMA_VERSION_V1:
        blocked_labels.append("unknown_schema_version")

    required_fields = (
        "evidence_packet_id",
        "retrieval_request_id",
        "project_id",
        "owner_user_scope",
        "tenant_account_scope",
        "source_scope",
        "retrieval_need_class",
        "retrieval_adapter",
        "source_type",
        "source_ref",
        "source_title",
        "source_timestamp",
        "retrieved_at_marker",
        "freshness_label",
        "relevance_label",
        "confidence_label",
        "verification_status",
        "privacy_label",
        "query_redaction_status",
        "evidence_summary",
    )
    for field in required_fields:
        if not _safe_str(candidate.get(field)):
            blocked_labels.append(f"missing_{field}")

    _validate_allowed_value(candidate.get("source_type", ""), SOURCE_TYPES_V1, "source_type", blocked_labels)
    _validate_allowed_value(candidate.get("retrieval_adapter", ""), RETRIEVAL_ADAPTERS_V1, "retrieval_adapter", blocked_labels)
    _validate_allowed_value(candidate.get("freshness_label", ""), FRESHNESS_LABELS_V1, "freshness_label", blocked_labels)
    _validate_allowed_value(candidate.get("relevance_label", ""), RELEVANCE_LABELS_V1, "relevance_label", blocked_labels)
    _validate_allowed_value(candidate.get("confidence_label", ""), CONFIDENCE_LABELS_V1, "confidence_label", blocked_labels)
    _validate_allowed_value(candidate.get("verification_status", ""), VERIFICATION_STATUSES_V1, "verification_status", blocked_labels)
    _validate_allowed_value(candidate.get("privacy_label", ""), PRIVACY_LABELS_V1, "privacy_label", blocked_labels)
    _validate_allowed_value(candidate.get("query_redaction_status", ""), QUERY_REDACTION_STATUSES_V1, "query_redaction_status", blocked_labels)

    if candidate.get("direct_to_answer_requested"):
        blocked_labels.append("direct_to_answer_requested")
    if candidate.get("final_answer_requested"):
        blocked_labels.append("final_answer_requested")
    if candidate.get("live_retrieval_requested"):
        blocked_labels.append("live_retrieval_requested")
    if candidate.get("provider_search_requested"):
        blocked_labels.append("provider_search_requested")
    if candidate.get("tool_execution_requested"):
        blocked_labels.append("tool_execution_requested")

    source_type = _safe_str(candidate.get("source_type"))
    if source_type in {"external_web_search", "searxng_search_result"} and not _safe_str(candidate.get("source_url")):
        blocked_labels.append("missing_source_url_for_external_evidence")
    if source_type in {"approved_project_artifact", "approved_uploaded_file", "project_files", "local_project_index"} and not _safe_str(candidate.get("source_ref")):
        blocked_labels.append("missing_source_ref_for_internal_evidence")

    privacy_sensitivity = _safe_str(candidate.get("privacy_sensitivity"))
    if privacy_sensitivity in {"sensitive", "confidential", "cross_user", "system_wide", "high_stakes"} and candidate.get("query_redaction_status") != "applied":
        blocked_labels.append("sensitive_evidence_requires_redacted_metadata")

    if privacy_sensitivity in {"cross_user", "system_wide", "high_stakes"} and not candidate.get("operator_review_ref"):
        blocked_labels.append("missing_operator_review_ref")

    if candidate.get("verification_status") == "blocked" and not _safe_str(candidate.get("blocked_reason")):
        blocked_labels.append("missing_blocked_reason")

    _maybe_block_for_forbidden_text("evidence_summary", candidate.get("evidence_summary"), blocked_labels)
    _maybe_block_for_forbidden_text("source_title", candidate.get("source_title"), blocked_labels)
    _maybe_block_for_forbidden_text("source_ref", candidate.get("source_ref"), blocked_labels)
    _maybe_block_for_forbidden_text("source_url", candidate.get("source_url"), blocked_labels)
    _maybe_block_for_forbidden_text("limitations", candidate.get("limitations"), blocked_labels)

    denied = _as_mapping(candidate.get("denied_authority"))
    for field in DENIED_AUTHORITY_FIELDS_V1:
        if field not in denied:
            blocked_labels.append(f"missing_denied_authority_{field}")
        elif _safe_bool(denied.get(field, False)):
            blocked_labels.append(f"denied_authority_asserted_{field}")

    if not candidate.get("retrieval_request_id"):
        blocked_labels.append("missing_retrieval_request_id")
    if not candidate.get("evidence_packet_id"):
        blocked_labels.append("missing_evidence_packet_id")

    if candidate.get("source_type") == "blocked_source" and not _safe_str(candidate.get("blocked_reason")):
        blocked_labels.append("missing_blocked_reason")

    blocked = bool(blocked_labels)
    classification = "evidence_packet_blocked" if blocked else "evidence_packet_metadata_only"

    if candidate.get("conflict_flags"):
        classification = "evidence_packet_conflict_review_required" if not blocked else classification
    elif candidate.get("missing_evidence_flags") and not blocked:
        classification = "evidence_packet_missing_evidence"
    elif candidate.get("freshness_label") in {"stale", "possibly_stale"} and not blocked:
        classification = "evidence_packet_stale_or_recent"

    result = {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "evidence_packet": candidate,
        "evidence_packet_id": candidate["evidence_packet_id"],
        "retrieval_request_id": candidate["retrieval_request_id"],
        "source_type": _safe_str(candidate.get("source_type")),
        "source_ref": _safe_str(candidate.get("source_ref")),
        "source_url": _safe_str(candidate.get("source_url")),
        "freshness_label": _safe_str(candidate.get("freshness_label")),
        "verification_status": _safe_str(candidate.get("verification_status")),
        "privacy_label": _safe_str(candidate.get("privacy_label")),
        "classification": classification,
        "blocked": blocked,
        "blocked_labels": blocked_labels,
        "validation_notes": blocked_labels[:],
        "conflict_flags": candidate.get("conflict_flags", []),
        "missing_evidence_flags": candidate.get("missing_evidence_flags", []),
        "denied_authority": dict(denied),
    }
    return result


def summarize_project_chat_evidence_packet_v1(packet: Any) -> dict[str, Any]:
    candidate = build_project_chat_evidence_packet_v1(packet)
    validation = validate_project_chat_evidence_packet_v1(candidate)
    summary_text = (
        f"Evidence packet metadata only | source_type={_safe_str(candidate.get('source_type'))} | "
        f"freshness={_safe_str(candidate.get('freshness_label'))} | "
        f"verification={_safe_str(candidate.get('verification_status'))} | "
        f"conflicts={len(candidate.get('conflict_flags', []))} | "
        f"missing={len(candidate.get('missing_evidence_flags', []))}"
    )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "evidence_packet_id": candidate["evidence_packet_id"],
        "retrieval_request_id": candidate["retrieval_request_id"],
        "summary_text": summary_text,
        "source_type": _safe_str(candidate.get("source_type")),
        "source_ref": _safe_str(candidate.get("source_ref")),
        "freshness_label": _safe_str(candidate.get("freshness_label")),
        "verification_status": _safe_str(candidate.get("verification_status")),
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "conflict_flags": candidate.get("conflict_flags", []),
        "missing_evidence_flags": candidate.get("missing_evidence_flags", []),
        "limitations": candidate.get("limitations", []),
        "evidence_summary": _safe_str(candidate.get("evidence_summary")),
    }


def to_project_chat_rag_evidence_json_safe_v1(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): to_project_chat_rag_evidence_json_safe_v1(val) for key, val in value.items()}
    if isinstance(value, list):
        return [to_project_chat_rag_evidence_json_safe_v1(item) for item in value]
    if isinstance(value, tuple):
        return [to_project_chat_rag_evidence_json_safe_v1(item) for item in value]
    if isinstance(value, set):
        return [to_project_chat_rag_evidence_json_safe_v1(item) for item in sorted(value, key=lambda item: _safe_str(item))]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _safe_str(value)


def build_initial_project_chat_rag_evidence_examples_v1() -> list[dict[str, Any]]:
    examples = [
        build_project_chat_rag_request_packet_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "user_intent_class": "project-chat",
                "source_class": "project_metadata",
                "query_text": "project metadata only",
                "retrieval_need_class": "project_metadata_retrieval_needed",
                "query_class": "direct_project_query",
                "retrieval_adapter": "ProjectStateMetadataAdapter",
                "privacy_sensitivity": "low",
                "external_query_allowed": False,
                "redaction_required": False,
                "approval_status": "not_required",
                "consent_status": "not_required",
                "query_redaction_status": "not_required",
            }
        ),
        build_project_chat_rag_request_packet_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "user_intent_class": "project-chat",
                "source_class": "memory_metadata",
                "query_text": "memory and continuity metadata only",
                "retrieval_need_class": "memory_continuity_retrieval_needed",
                "query_class": "source_specific_query",
                "retrieval_adapter": "MemoryStateMetadataAdapter",
                "privacy_sensitivity": "project_private",
                "external_query_allowed": False,
                "redaction_required": False,
                "approval_status": "not_required",
                "consent_status": "provided",
                "query_redaction_status": "not_required",
            }
        ),
        build_project_chat_rag_request_packet_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "user_intent_class": "project-chat",
                "source_class": "local_project_index",
                "query_text": "approved index metadata only",
                "retrieval_need_class": "local_index_retrieval_needed",
                "query_class": "source_specific_query",
                "retrieval_adapter": "LocalProjectIndexAdapter",
                "privacy_sensitivity": "project_private",
                "external_query_allowed": False,
                "redaction_required": False,
                "approval_status": "not_required",
                "consent_status": "provided",
                "query_redaction_status": "not_required",
            }
        ),
        build_project_chat_rag_request_packet_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "user_intent_class": "project-chat",
                "source_class": "external_web_search",
                "query_text": "general web search metadata only",
                "redacted_query_text": "general web search metadata only",
                "retrieval_need_class": "external_web_search_needed",
                "query_class": "general_web_query",
                "retrieval_adapter": "SearXNGExternalSearchAdapter",
                "privacy_sensitivity": "public",
                "external_query_allowed": True,
                "redaction_required": False,
                "approval_status": "approved",
                "consent_status": "not_required",
                "query_redaction_status": "applied",
                "source_url": "https://example.invalid/search",
                "source_title": "general web search metadata only",
            }
        ),
    ]
    return examples


__all__ = [
    "HELPER_TYPE_V1",
    "SCHEMA_VERSION_V1",
    "RETRIEVAL_NEEDS_V1",
    "QUERY_CLASSES_V1",
    "SOURCE_CLASSES_V1",
    "RETRIEVAL_ADAPTERS_V1",
    "FRESHNESS_LABELS_V1",
    "RELEVANCE_LABELS_V1",
    "CONFIDENCE_LABELS_V1",
    "VERIFICATION_STATUSES_V1",
    "PRIVACY_LABELS_V1",
    "QUERY_REDACTION_STATUSES_V1",
    "APPROVAL_STATUSES_V1",
    "CONSENT_STATUSES_V1",
    "SOURCE_TYPES_V1",
    "DENIED_AUTHORITY_FIELDS_V1",
    "allowed_project_chat_rag_retrieval_needs_v1",
    "allowed_project_chat_rag_query_classes_v1",
    "allowed_project_chat_rag_source_classes_v1",
    "allowed_project_chat_rag_adapters_v1",
    "build_project_chat_rag_request_packet_v1",
    "classify_project_chat_retrieval_need_v1",
    "build_project_chat_evidence_packet_v1",
    "validate_project_chat_rag_request_packet_v1",
    "validate_project_chat_evidence_packet_v1",
    "summarize_project_chat_evidence_packet_v1",
    "to_project_chat_rag_evidence_json_safe_v1",
    "build_initial_project_chat_rag_evidence_examples_v1",
]
