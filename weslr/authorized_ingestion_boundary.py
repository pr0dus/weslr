"""WESLR Authorized Ingestion Boundary V1.

Deterministic, metadata-only helpers for representing safe source-handling
boundaries before any evidence-intake packet is built.

This module preserves discovery direction while refusing unsafe access,
retention, evidence conversion, authority escalation, or public claims.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "authorized_ingestion_boundary_v1"
HELPER_FAMILY_V1 = "authorized_ingestion_boundary"

_ALLOWED_INGESTION_AUTHORIZATION_STATES_V1 = (
    "not_authorized",
    "operator_requested_metadata_only",
    "operator_supplied_summary_only",
    "operator_supplied_document_metadata_only",
    "future_private_source_review_required",
    "blocked_sensitive_source",
    "blocked_unknown_source",
    "blocked_cross_user_or_tenant",
    "needs_repair",
)

_ALLOWED_SOURCE_ACCESS_MODES_V1 = (
    "no_access",
    "metadata_descriptor_only",
    "owner_supplied_summary",
    "owner_supplied_redacted_excerpt",
    "owner_supplied_document_reference",
    "future_connector_requires_review",
    "blocked",
)

_ALLOWED_RAW_CONTENT_HANDLING_STATES_V1 = (
    "raw_content_forbidden",
    "raw_content_not_retained",
    "redacted_excerpt_only",
    "summary_only",
    "future_retention_requires_design",
    "blocked",
)

_ALLOWED_INGESTION_OUTPUT_FORMS_V1 = (
    "no_output",
    "metadata_only",
    "redacted_summary_only",
    "evidence_intake_candidate_only",
    "operator_review_packet_only",
    "blocked",
)

_ALLOWED_DISCOVERY_DOMAINS_V1 = (
    "science",
    "engineering",
    "materials",
    "energy",
    "medicine_life_sciences_metadata_only",
    "mathematics",
    "communications",
    "physics",
    "ai_architectures",
    "patents_public_technical_literature",
    "owner_supplied_observations",
    "internal_project_artifacts",
    "anomalous_signals",
    "cross_domain_analogies",
)

_AUTHORITY_FALSE_FLAGS_V1 = (
    "runtime_authorized",
    "source_ingestion_authorized",
    "public_claim_authorized",
    "final_answer_authority",
    "provider_model_call_authority",
    "provider_authority",
    "model_authority",
    "tool_execution_authority",
    "retrieval_tool_authority",
    "web_authority",
    "weslr_io_authorized",
    "weslr_read_authorized",
    "weslr_write_authorized",
    "weslr_persistence_authorized",
    "database_write_authorized",
    "memory_mutation_authorized",
    "project_mutation_authorized",
    "hidden_private_protected_authorized",
    "cross_user_leakage_authorized",
    "public_science_claim_authorized",
    "proof_claim_authorized",
    "benchmark_claim_authorized",
    "agi_claim_authorized",
    "automatic_discovery_authorized",
)

_AUTHORITY_TEXT_MARKERS_V1 = (
    "discovery",
    "proof",
    "benchmark",
    "score",
    "agi",
    "intelligence",
    "sentience",
    "consciousness",
    "public claim authorized",
    "final answer authority",
    "runtime authorization",
    "source ingestion authorization",
    "provider/model/tool/retrieval/web implication",
    "provider/model/tool/web/retrieval",
    ".weslr implication",
    ".weslr read/write implication",
    ".weslr persistence/state implication",
    "persistence/database implication",
    "memory/project mutation implication",
    "cross-user leakage",
    "hidden/private/protected markers",
)

_HIDDEN_PRIVATE_PROTECTED_MARKERS_V1 = (
    "hidden prompt",
    "system prompt",
    "private text",
    "secret",
    "api key",
    "protected file",
    "protected",
    "private",
)

_SAFE_METADATA_REQUIRED_TRUE_FLAGS_V1 = (
    "safe",
    "metadata_only",
    "json_safe",
    "non_public",
    "no_runtime_wiring",
    "no_model_provider_calls",
    "no_tool_execution",
    "no_retrieval",
    "no_web_calls",
    "no_source_ingestion",
    "no_raw_content_retention",
    "no_weslr_io",
    "no_weslr_read",
    "no_weslr_write",
    "no_weslr_persistence",
    "no_database_writes",
    "no_memory_mutation",
    "no_project_mutation",
    "no_public_claim_authority",
    "no_final_answer_authority",
    "no_discovery_claims",
    "no_proof_claims",
    "no_benchmark_claims",
    "no_score_claims",
    "no_agi_claims",
    "no_public_science_claims",
    "no_hidden_private_protected_markers",
)

_REQUIRED_FIELD_NAMES_V1 = (
    "ingestion_boundary_id",
    "requested_source_kind",
    "requested_access_mode",
    "authorization_state",
    "source_scope",
    "owner_or_operator_request_status",
    "privacy_sensitivity",
    "safety_sensitivity",
    "cross_user_or_tenant_risk",
    "raw_content_handling",
    "retention_policy",
    "allowed_output_form",
    "evidence_intake_link_allowed",
    "operator_review_required",
    "blocked_reason",
    "required_redactions",
    "forbidden_interpretations",
    "authority_status",
    "safe_metadata",
    "search_direction_allowed",
    "ingestion_authorized",
    "raw_retention_allowed",
    "public_claim_allowed",
    "final_answer_authority",
    "discovery_domains_preserved",
)

_REQUIRED_TEXT_FIELDS_V1 = (
    "ingestion_boundary_id",
    "requested_source_kind",
    "requested_access_mode",
    "authorization_state",
    "source_scope",
    "owner_or_operator_request_status",
    "privacy_sensitivity",
    "safety_sensitivity",
    "cross_user_or_tenant_risk",
    "raw_content_handling",
    "retention_policy",
    "allowed_output_form",
    "blocked_reason",
)

_REQUIRED_BOOL_FIELDS_V1 = (
    "evidence_intake_link_allowed",
    "operator_review_required",
    "search_direction_allowed",
    "ingestion_authorized",
    "raw_retention_allowed",
    "public_claim_allowed",
    "final_answer_authority",
)

_REQUIRED_LIST_FIELDS_V1 = (
    "required_redactions",
    "forbidden_interpretations",
    "discovery_domains_preserved",
)

_CANONICAL_FORBIDDEN_INTERPRETATIONS_V1 = [
    "this is proven",
    "this is discovered",
    "this is public truth",
    "this is a final answer",
    "this authorizes ingestion",
    "this authorizes runtime",
    "this authorizes provider/tool/web use",
    "this authorizes .weslr access",
    "this authorizes persistence",
]


def allowed_ingestion_authorization_states_v1() -> tuple[str, ...]:
    return _ALLOWED_INGESTION_AUTHORIZATION_STATES_V1


def allowed_source_access_modes_v1() -> tuple[str, ...]:
    return _ALLOWED_SOURCE_ACCESS_MODES_V1


def allowed_raw_content_handling_states_v1() -> tuple[str, ...]:
    return _ALLOWED_RAW_CONTENT_HANDLING_STATES_V1


def allowed_ingestion_output_forms_v1() -> tuple[str, ...]:
    return _ALLOWED_INGESTION_OUTPUT_FORMS_V1


def allowed_discovery_domains_v1() -> tuple[str, ...]:
    return _ALLOWED_DISCOVERY_DOMAINS_V1


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        merged.update(payload)
    for key, value in overrides.items():
        if value is not None:
            merged[key] = value
    return merged


def _compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _normalize_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    elif isinstance(value, tuple):
        items = list(value)
    elif isinstance(value, set):
        items = sorted(value, key=repr)
    else:
        text = _compact_text(value)
        return [text] if text else []
    normalized: list[str] = []
    for item in items:
        text = _compact_text(item)
        if text:
            normalized.append(text)
    return normalized


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return f"<non-json-safe:{type(value).__name__}>"


def _build_default_authority_status() -> dict[str, Any]:
    authority_status = {flag: False for flag in _AUTHORITY_FALSE_FLAGS_V1}
    authority_status.update(
        {
            "all_authority_flags_false": True,
            "status": "metadata_only",
            "boundary_notes": "metadata-only authorized ingestion boundary",
        }
    )
    return authority_status


def _build_default_safe_metadata() -> dict[str, Any]:
    return {
        "safe": True,
        "metadata_only": True,
        "json_safe": True,
        "non_public": True,
        "no_runtime_wiring": True,
        "no_model_provider_calls": True,
        "no_tool_execution": True,
        "no_retrieval": True,
        "no_web_calls": True,
        "no_source_ingestion": True,
        "no_raw_content_retention": True,
        "no_weslr_io": True,
        "no_weslr_read": True,
        "no_weslr_write": True,
        "no_weslr_persistence": True,
        "no_database_writes": True,
        "no_memory_mutation": True,
        "no_project_mutation": True,
        "no_public_claim_authority": True,
        "no_final_answer_authority": True,
        "no_discovery_claims": True,
        "no_proof_claims": True,
        "no_benchmark_claims": True,
        "no_score_claims": True,
        "no_agi_claims": True,
        "no_public_science_claims": True,
        "no_hidden_private_protected_markers": True,
        "search_direction_allowed": True,
        "ingestion_authorized": False,
        "raw_retention_allowed": False,
        "evidence_intake_link_allowed": False,
        "public_claim_allowed": False,
        "final_answer_authority": False,
        "discovery_preservation": True,
    }


def _build_default_boundary_packet() -> dict[str, Any]:
    return {
        "ingestion_boundary_id": "default_authorized_ingestion_boundary",
        "requested_source_kind": "owner_supplied_observation",
        "requested_access_mode": "no_access",
        "authorization_state": "not_authorized",
        "source_scope": "broad inquiry only; no source access yet",
        "owner_or_operator_request_status": "operator request not yet supplied",
        "privacy_sensitivity": "unassessed",
        "safety_sensitivity": "unassessed",
        "cross_user_or_tenant_risk": "unassessed",
        "raw_content_handling": "raw_content_forbidden",
        "retention_policy": "no retention",
        "allowed_output_form": "no_output",
        "evidence_intake_link_allowed": False,
        "operator_review_required": False,
        "blocked_reason": "metadata-only discovery preservation boundary",
        "required_redactions": [],
        "forbidden_interpretations": list(_CANONICAL_FORBIDDEN_INTERPRETATIONS_V1),
        "authority_status": _build_default_authority_status(),
        "safe_metadata": _build_default_safe_metadata(),
        "search_direction_allowed": True,
        "search_direction_blocked_reason": "",
        "ingestion_authorized": False,
        "raw_retention_allowed": False,
        "public_claim_allowed": False,
        "final_answer_authority": False,
        "discovery_domains_preserved": list(_ALLOWED_DISCOVERY_DOMAINS_V1),
    }


def build_authorized_ingestion_boundary_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    packet = _build_default_boundary_packet()
    packet.update(_merge_payload(payload, **overrides))
    packet["required_redactions"] = _normalize_text_list(packet.get("required_redactions"))
    packet["forbidden_interpretations"] = _normalize_text_list(packet.get("forbidden_interpretations"))
    packet["discovery_domains_preserved"] = _normalize_text_list(packet.get("discovery_domains_preserved"))
    if isinstance(packet.get("authority_status"), Mapping):
        packet["authority_status"] = dict(packet["authority_status"])
    if isinstance(packet.get("safe_metadata"), Mapping):
        packet["safe_metadata"] = dict(packet["safe_metadata"])
    return packet


def _blocked(labels: list[str], summary: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": False,
        "blocked": True,
        "blocked_labels": labels,
        "validation_posture": "blocked",
        "summary_text": summary,
    }


def _valid(summary: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": True,
        "blocked": False,
        "blocked_labels": [],
        "validation_posture": "valid",
        "summary_text": summary,
    }


def _authority_status_is_fail_closed(authority_status: Any) -> tuple[bool, list[str]]:
    if not isinstance(authority_status, Mapping):
        return False, ["invalid_authority_status"]
    labels: list[str] = []
    for flag in _AUTHORITY_FALSE_FLAGS_V1:
        if flag not in authority_status:
            labels.append(f"missing_authority_status_{flag}")
        elif authority_status[flag] is not False:
            labels.append(f"unsafe_authority_flag_{flag}")
    if authority_status.get("all_authority_flags_false") is not True:
        labels.append("unsafe_authority_flags")
    if _compact_text(authority_status.get("status")) != "metadata_only":
        labels.append("unsafe_authority_status")
    notes = _compact_text(authority_status.get("boundary_notes"))
    if not notes:
        labels.append("missing_authority_status_boundary_notes")
    elif _contains_any_marker(notes, _AUTHORITY_TEXT_MARKERS_V1):
        labels.append("unsafe_authority_text")
    return not labels, labels


def _safe_metadata_is_fail_closed(safe_metadata: Any) -> tuple[bool, list[str]]:
    if not isinstance(safe_metadata, Mapping):
        return False, ["invalid_safe_metadata"]
    labels: list[str] = []
    for flag in _SAFE_METADATA_REQUIRED_TRUE_FLAGS_V1:
        if flag == "search_direction_allowed":
            continue
        if safe_metadata.get(flag) is not True:
            labels.append(f"missing_safe_metadata_{flag}")
    if safe_metadata.get("ingestion_authorized") is not False:
        labels.append("unsafe_ingestion_authorized_flag")
    if safe_metadata.get("raw_retention_allowed") is not False:
        labels.append("unsafe_raw_retention_allowed_flag")
    if safe_metadata.get("public_claim_allowed") is not False:
        labels.append("unsafe_public_claim_allowed_flag")
    if safe_metadata.get("final_answer_authority") is not False:
        labels.append("unsafe_final_answer_authority_flag")
    if safe_metadata.get("discovery_preservation") is not True:
        labels.append("missing_safe_metadata_discovery_preservation")
    notes = _compact_text(safe_metadata.get("boundary_notes"))
    if notes and _contains_any_marker(notes, _AUTHORITY_TEXT_MARKERS_V1):
        labels.append("unsafe_safe_metadata_text")
    return not labels, labels


def _contains_any_marker(value: str, markers: tuple[str, ...]) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in markers)


def validate_authorized_ingestion_boundary_packet_v1(packet: Any) -> dict[str, Any]:
    if not isinstance(packet, Mapping):
        return _blocked(["invalid_packet_type"], "Invalid authorized ingestion boundary packet.")

    labels: list[str] = []
    for field in _REQUIRED_FIELD_NAMES_V1:
        if field not in packet:
            labels.append(f"missing_{field}")

    if labels:
        return _blocked(labels, "Missing required authorized ingestion boundary fields.")

    for field in _REQUIRED_TEXT_FIELDS_V1:
        if not _compact_text(packet.get(field)):
            labels.append(f"missing_{field}")

    for field in _REQUIRED_BOOL_FIELDS_V1:
        if not isinstance(packet.get(field), bool):
            labels.append(f"invalid_{field}")

    for field in _REQUIRED_LIST_FIELDS_V1:
        value = packet.get(field)
        if not isinstance(value, list):
            labels.append(f"invalid_{field}")
        elif field == "forbidden_interpretations" and not value:
            labels.append(f"missing_{field}")
        elif field == "discovery_domains_preserved":
            domains = [_compact_text(item) for item in value if _compact_text(item)]
            if not domains or any(domain not in _ALLOWED_DISCOVERY_DOMAINS_V1 for domain in domains):
                labels.append("invalid_discovery_domains_preserved")

    if _compact_text(packet.get("requested_access_mode")) not in _ALLOWED_SOURCE_ACCESS_MODES_V1:
        labels.append("invalid_requested_access_mode")
    if _compact_text(packet.get("authorization_state")) not in _ALLOWED_INGESTION_AUTHORIZATION_STATES_V1:
        labels.append("invalid_authorization_state")
    if _compact_text(packet.get("raw_content_handling")) not in _ALLOWED_RAW_CONTENT_HANDLING_STATES_V1:
        labels.append("unsafe_raw_content_handling")
    if _compact_text(packet.get("allowed_output_form")) not in _ALLOWED_INGESTION_OUTPUT_FORMS_V1:
        labels.append("invalid_allowed_output_form")

    authority_status_ok, authority_labels = _authority_status_is_fail_closed(packet.get("authority_status"))
    if not authority_status_ok:
        labels.extend(authority_labels)

    safe_metadata_ok, safe_metadata_labels = _safe_metadata_is_fail_closed(packet.get("safe_metadata"))
    if not safe_metadata_ok:
        labels.extend(safe_metadata_labels)

    forbidden_interpretations = _normalize_text_list(packet.get("forbidden_interpretations"))
    if not forbidden_interpretations:
        labels.append("missing_forbidden_interpretations")
    elif not set(_CANONICAL_FORBIDDEN_INTERPRETATIONS_V1).issubset(set(forbidden_interpretations)):
        labels.append("missing_forbidden_interpretations")

    discovery_domains = _normalize_text_list(packet.get("discovery_domains_preserved"))
    if not discovery_domains:
        labels.append("missing_discovery_domains_preserved")
    elif any(domain not in _ALLOWED_DISCOVERY_DOMAINS_V1 for domain in discovery_domains):
        labels.append("invalid_discovery_domains_preserved")

    if packet.get("ingestion_authorized") is True and _compact_text(packet.get("authorization_state")) == "not_authorized":
        labels.append("source_ingestion_authorization_without_boundary_pass")

    if packet.get("evidence_intake_link_allowed") is True and packet.get("ingestion_authorized") is not True:
        labels.append("evidence_intake_link_allowed_without_ingestion_authorization")

    if packet.get("public_claim_allowed") is True:
        labels.append("public_claim_authorization")
    if packet.get("final_answer_authority") is True:
        labels.append("final_answer_authority")
    if packet.get("raw_retention_allowed") is True:
        labels.append("unsafe_retention_policy")

    if not isinstance(packet.get("search_direction_allowed"), bool):
        labels.append("invalid_search_direction_allowed")
    if not isinstance(packet.get("ingestion_authorized"), bool):
        labels.append("invalid_ingestion_authorized")

    text_fields = (
        "ingestion_boundary_id",
        "requested_source_kind",
        "requested_access_mode",
        "authorization_state",
        "source_scope",
        "owner_or_operator_request_status",
        "privacy_sensitivity",
        "safety_sensitivity",
        "cross_user_or_tenant_risk",
        "raw_content_handling",
        "retention_policy",
        "allowed_output_form",
        "blocked_reason",
    )
    for field in text_fields:
        if not _compact_text(packet.get(field)):
            labels.append(f"missing_{field}")

    blocked_reason = _compact_text(packet.get("blocked_reason"))
    if _contains_any_marker(blocked_reason, ("hidden prompt", "system prompt", "private", "secret", "api key", "protected", "credential")):
        labels.append("hidden_private_protected_markers")

    for field in _AUTHORITY_FALSE_FLAGS_V1:
        if isinstance(packet.get("authority_status"), Mapping) and packet["authority_status"].get(field) is True:
            labels.append(f"unsafe_authority_flag_{field}")

    if isinstance(packet.get("authority_status"), Mapping):
        auth_text = " ".join(
            _compact_text(item)
            for item in (
                packet["authority_status"].get("boundary_notes"),
                packet["authority_status"].get("status"),
            )
        ).strip()
        if auth_text and _contains_any_marker(auth_text, _AUTHORITY_TEXT_MARKERS_V1):
            labels.append("unsafe_authority_text")

    if blocked_reason and _contains_any_marker(blocked_reason, _AUTHORITY_TEXT_MARKERS_V1):
        labels.append("unsafe_authority_text")

    if _contains_any_marker(_compact_text(packet.get("source_scope")), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        labels.append("hidden_private_protected_markers")

    try:
        json.dumps(packet, sort_keys=True)
    except TypeError:
        labels.append("non_json_safe_output")

    if labels:
        summary = "Invalid authorized ingestion boundary packet."
        if any(label.startswith("missing_") for label in labels):
            summary = "Missing required authorized ingestion boundary fields."
        return _blocked(sorted(set(labels)), summary)

    return _valid("Valid authorized ingestion boundary packet.")


def summarize_authorized_ingestion_boundary_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_authorized_ingestion_boundary_packet_v1(packet)
    if not isinstance(packet, Mapping):
        return {
            "ingestion_boundary_id": "",
            "requested_source_kind": "",
            "requested_access_mode": "",
            "authorization_state": "",
            "raw_content_handling": "",
            "allowed_output_form": "",
            "evidence_intake_link_allowed": False,
            "search_direction_allowed": False,
            "ingestion_authorized": False,
            "raw_retention_allowed": False,
            "public_claim_allowed": False,
            "final_answer_authority": False,
            "discovery_domains_count": 0,
            "operator_review_required": False,
            "blocked_reason": "",
            "validation_posture": validation["validation_posture"],
        }
    discovery_domains = _normalize_text_list(packet.get("discovery_domains_preserved"))
    return {
        "ingestion_boundary_id": _compact_text(packet.get("ingestion_boundary_id")),
        "requested_source_kind": _compact_text(packet.get("requested_source_kind")),
        "requested_access_mode": _compact_text(packet.get("requested_access_mode")),
        "authorization_state": _compact_text(packet.get("authorization_state")),
        "raw_content_handling": _compact_text(packet.get("raw_content_handling")),
        "allowed_output_form": _compact_text(packet.get("allowed_output_form")),
        "evidence_intake_link_allowed": bool(packet.get("evidence_intake_link_allowed")),
        "search_direction_allowed": bool(packet.get("search_direction_allowed")),
        "ingestion_authorized": bool(packet.get("ingestion_authorized")),
        "raw_retention_allowed": bool(packet.get("raw_retention_allowed")),
        "public_claim_allowed": bool(packet.get("public_claim_allowed")),
        "final_answer_authority": bool(packet.get("final_answer_authority")),
        "discovery_domains_count": len(discovery_domains),
        "operator_review_required": bool(packet.get("operator_review_required")),
        "blocked_reason": _compact_text(packet.get("blocked_reason")),
        "validation_posture": validation["validation_posture"],
    }


def to_authorized_ingestion_boundary_json_safe_v1(packet: Any) -> Any:
    return _json_safe(deepcopy(packet))


def build_initial_authorized_ingestion_boundary_examples_v1() -> list[dict[str, Any]]:
    metadata_only_boundary = build_authorized_ingestion_boundary_packet_v1(
        {
            "ingestion_boundary_id": "owner_summary_metadata_only_boundary",
            "requested_source_kind": "owner_supplied_document",
            "requested_access_mode": "owner_supplied_summary",
            "authorization_state": "operator_supplied_summary_only",
            "source_scope": "owner supplied summary metadata only; no raw source intake",
            "owner_or_operator_request_status": "owner supplied summary with operator metadata review",
            "privacy_sensitivity": "metadata-only low privacy sensitivity",
            "safety_sensitivity": "metadata-only low safety sensitivity",
            "cross_user_or_tenant_risk": "not_cross_user_or_tenant",
            "raw_content_handling": "summary_only",
            "retention_policy": "no raw retention; summary metadata only",
            "allowed_output_form": "metadata_only",
            "evidence_intake_link_allowed": False,
            "operator_review_required": True,
            "blocked_reason": "metadata-only summary path is permitted; raw content remains withheld",
            "required_redactions": [],
            "forbidden_interpretations": list(_CANONICAL_FORBIDDEN_INTERPRETATIONS_V1),
            "authority_status": _build_default_authority_status(),
            "safe_metadata": {
                **_build_default_safe_metadata(),
                "ingestion_authorized": False,
                "evidence_intake_link_allowed": False,
                "raw_retention_allowed": False,
                "public_claim_allowed": False,
                "final_answer_authority": False,
                "discovery_preservation": True,
            },
            "search_direction_allowed": True,
            "search_direction_blocked_reason": "",
            "ingestion_authorized": False,
            "raw_retention_allowed": False,
            "public_claim_allowed": False,
            "final_answer_authority": False,
        }
    )
    broad_search_not_ingestion = build_authorized_ingestion_boundary_packet_v1(
        {
            "ingestion_boundary_id": "broad_search_direction_not_ingestion_boundary",
            "requested_source_kind": "unknown_source",
            "requested_access_mode": "no_access",
            "authorization_state": "not_authorized",
            "source_scope": "broad search direction only; no source access yet",
            "owner_or_operator_request_status": "no operator request yet",
            "privacy_sensitivity": "unassessed",
            "safety_sensitivity": "unassessed",
            "cross_user_or_tenant_risk": "unassessed",
            "raw_content_handling": "raw_content_forbidden",
            "retention_policy": "no retention",
            "allowed_output_form": "operator_review_packet_only",
            "evidence_intake_link_allowed": False,
            "operator_review_required": True,
            "blocked_reason": "broad search direction remains allowed; ingestion is not yet authorized",
            "required_redactions": [],
            "forbidden_interpretations": list(_CANONICAL_FORBIDDEN_INTERPRETATIONS_V1),
            "authority_status": _build_default_authority_status(),
            "safe_metadata": {
                **_build_default_safe_metadata(),
                "ingestion_authorized": False,
                "evidence_intake_link_allowed": False,
                "raw_retention_allowed": False,
                "public_claim_allowed": False,
                "final_answer_authority": False,
                "discovery_preservation": True,
            },
            "search_direction_allowed": True,
            "search_direction_blocked_reason": "",
            "ingestion_authorized": False,
            "raw_retention_allowed": False,
            "public_claim_allowed": False,
            "final_answer_authority": False,
        }
    )
    return [metadata_only_boundary, broad_search_not_ingestion]
