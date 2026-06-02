"""Metadata-only document access and PII scrubbing boundary helpers v1.

This module classifies explicit metadata only. It does not inspect real
content, read files, vectorize, retrieve, call models/providers, write memory,
or touch `.weslr`.

It defines a compact boundary between document accessibility, privacy
sensitivity, PII handling, retrieval readiness, citation readiness, and daemon
verdict propagation.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

HELPER_TYPE_V1 = "document_access_pii_boundary_v1"
PACKET_TYPE_V1 = "document_access_packet_v1"
SUMMARY_TYPE_V1 = "document_access_packet_summary_v1"

ALLOWED_ACCESS_LEVELS_V1 = {
    "owner_private",
    "operator_internal",
    "project_internal",
    "workspace_shared",
    "public_source",
    "public_website_source",
    "third_party_source",
    "unknown_access",
    "access_blocked",
}

ALLOWED_PRIVACY_SENSITIVITY_LEVELS_V1 = {
    "non_sensitive",
    "low_sensitivity",
    "medium_sensitivity",
    "high_sensitivity",
    "restricted_sensitive",
    "unknown_sensitivity",
}

ALLOWED_USE_PERMISSIONS_V1 = {
    "may_read_metadata",
    "may_read_summary",
    "may_read_content",
    "may_index",
    "may_vectorize",
    "may_quote",
    "may_cite_private",
    "may_cite_public",
    "may_use_for_answer",
    "may_use_for_public_claim",
    "may_use_for_action",
    "blocked",
}

ALLOWED_PII_CATEGORIES_V1 = {
    "personal_name",
    "email_address",
    "phone_number",
    "postal_address",
    "precise_location",
    "government_id",
    "financial_data",
    "payment_data",
    "health_data",
    "biometric_data",
    "child_data",
    "employment_data",
    "legal_data",
    "authentication_secret",
    "api_key_or_token",
    "private_message",
    "unknown_pii",
}

ALLOWED_SCRUBBING_MODES_V1 = {
    "no_scrub_required",
    "metadata_only",
    "summary_only",
    "redact_direct_identifiers",
    "redact_sensitive_fields",
    "hash_reference_only",
    "block_content_use",
    "block_public_use",
    "owner_review_required",
    "operator_review_required",
}

ALLOWED_RUNTIME_GATE_STATUSES_V1 = {
    "access_allowed",
    "access_blocked",
    "privacy_blocked",
    "summary_only",
    "public_use_blocked",
    "operator_review_required",
}

ALLOWED_SOURCE_SCOPES_V1 = {
    "owner_private",
    "operator_internal",
    "project_internal",
    "workspace_shared",
    "public_source",
    "public_website_source",
    "third_party_source",
    "unknown_access",
    "access_blocked",
}

ALLOWED_SOURCE_TYPES_V1 = {
    "file",
    "memory",
    "artifact",
    "source_node",
    "retrieved_document",
    "uploaded_file",
    "web_source",
    "unknown_source",
}

ALLOWED_FIELD_HINTS_V1 = (
    "hidden_prompt",
    "raw_private",
    "private_data",
    "secret",
    "token",
    "key",
    "api_key",
    "credential",
    "password",
)

ALLOWED_CLAIM_PHRASES_V1 = (
    "gdpr compliant",
    "gdpr certification",
    "security certification",
    "official security",
    "production ready",
    "public ready",
    "public readiness",
    "proof certainty",
    "truth certainty",
    "proof claim",
    "truth claim",
    "agi",
    "consciousness",
    "sentience",
    "turing",
)

DEFAULT_SAFE_METADATA_V1 = {
    "metadata_only": True,
    "internal_only": True,
}

DEFAULT_ACCESS_LEVEL_V1 = "unknown_access"
DEFAULT_PRIVACY_SENSITIVITY_V1 = "unknown_sensitivity"
DEFAULT_SCRUBBING_MODE_V1 = "metadata_only"
DEFAULT_SOURCE_TYPE_V1 = "unknown_source"
DEFAULT_SOURCE_SCOPE_V1 = "unknown_access"
DEFAULT_RUNTIME_GATE_STATUS_V1 = "access_blocked"
DEFAULT_RETENTION_POLICY_REF_V1 = "retention_policy_required"
DEFAULT_RECOMMENDED_NEXT_GATE_V1 = "classify access and privacy metadata before retrieval, citation, or indexing"


class ValidationError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Safe helpers
# ---------------------------------------------------------------------------


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value).strip()
    return default if value == "" else str(value).strip()



def _normalize_text(value: Any) -> str:
    return " ".join(_safe_text(value).replace("_", " ").split()).lower()



def _safe_bool(value: Any) -> bool:
    return bool(value) is True



def _json_sort_key(value: Any) -> tuple[str, str]:
    return (type(value).__name__, repr(value))



def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        items = [_json_safe(item) for item in value]
        return sorted(items, key=_json_sort_key)
    return _safe_text(value)



def to_document_access_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)



def _contains_forbidden_field(value: Any) -> str:
    if value is None:
        return ""
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalize_text(key)
            key_raw = _safe_text(key).lower()
            if any(hint.replace("_", " ") in key_text or hint in key_raw for hint in ALLOWED_FIELD_HINTS_V1):
                return _safe_text(key)
            nested = _contains_forbidden_field(item)
            if nested:
                return nested
        return ""
    if isinstance(value, (list, tuple, set)):
        for item in value:
            nested = _contains_forbidden_field(item)
            if nested:
                return nested
        return ""
    return ""



def _contains_forbidden_claim_marker(value: Any) -> bool:
    if value is None:
        return False
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return any(_contains_forbidden_claim_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_claim_marker(item) for item in value)
    text = _normalize_text(value)
    raw = _safe_text(value).lower()
    return any(phrase in text or phrase in raw for phrase in ALLOWED_CLAIM_PHRASES_V1)



def _safe_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]



def _unique_text_list(values: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in _safe_list(values):
        text = _safe_text(item)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return out



def _normalize_required_text(value: Any, *, allowed: set[str], field_name: str) -> str:
    text = _safe_text(value)
    if text not in allowed:
        raise ValidationError(f"unknown_{field_name}")
    return text



def _normalize_metadata(value: Any) -> dict[str, Any]:
    if value is None:
        return dict(DEFAULT_SAFE_METADATA_V1)
    safe = _json_safe(value)
    if not isinstance(safe, Mapping):
        raise ValidationError("safe_metadata_must_be_mapping")
    out = {str(key): _json_safe(val) for key, val in safe.items()}
    out.setdefault("metadata_only", True)
    out.setdefault("internal_only", True)
    return out



def _has_restricted_pii(categories: list[str]) -> bool:
    return any(category in {"authentication_secret", "api_key_or_token", "government_id", "child_data", "health_data", "legal_data", "biometric_data", "private_message"} for category in categories)



def _is_identifier_pii(categories: list[str]) -> bool:
    return any(category in {"personal_name", "email_address", "phone_number", "postal_address", "precise_location", "government_id"} for category in categories)



def _requires_review(categories: list[str]) -> bool:
    return any(category in {"child_data", "health_data", "legal_data", "biometric_data", "authentication_secret", "api_key_or_token"} for category in categories)


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------


def classify_document_access_v1(*, source_scope: Any = None, access_level: Any = None, source_type: Any = None, **metadata: Any) -> str:
    access_text = _safe_text(access_level)
    scope_text = _safe_text(source_scope)
    if access_text and access_text in ALLOWED_ACCESS_LEVELS_V1 and access_text != "unknown_access":
        return access_text
    if scope_text and scope_text in ALLOWED_ACCESS_LEVELS_V1:
        return scope_text
    if access_text == "unknown_access" and scope_text in ALLOWED_ACCESS_LEVELS_V1:
        return scope_text
    source_type_text = _safe_text(source_type)
    if source_type_text == "uploaded_file" and not access_text:
        return "project_internal"
    return "unknown_access"



def classify_pii_sensitivity_v1(*, detected_pii_categories: Any = None, source_scope: Any = None, access_level: Any = None, **metadata: Any) -> str:
    categories = _unique_text_list(detected_pii_categories)
    if any(category not in ALLOWED_PII_CATEGORIES_V1 for category in categories):
        return "unknown_sensitivity"
    if not categories:
        access = classify_document_access_v1(source_scope=source_scope, access_level=access_level, **metadata)
        return {
            "public_source": "non_sensitive",
            "public_website_source": "non_sensitive",
            "third_party_source": "low_sensitivity",
            "workspace_shared": "low_sensitivity",
            "project_internal": "medium_sensitivity",
            "operator_internal": "medium_sensitivity",
            "owner_private": "high_sensitivity",
            "access_blocked": "restricted_sensitive",
        }.get(access, "unknown_sensitivity")
    if any(category in {"authentication_secret", "api_key_or_token"} for category in categories):
        return "restricted_sensitive"
    if any(category in {"child_data", "health_data", "legal_data", "biometric_data", "government_id"} for category in categories):
        return "restricted_sensitive"
    if any(category in {"financial_data", "payment_data", "private_message"} for category in categories):
        return "high_sensitivity"
    if any(category in {"email_address", "phone_number", "postal_address", "precise_location", "employment_data"} for category in categories):
        return "medium_sensitivity"
    if any(category in {"personal_name"} for category in categories):
        return "low_sensitivity"
    return "unknown_sensitivity"



def select_scrubbing_mode_v1(*, access_level: Any = None, privacy_sensitivity: Any = None, detected_pii_categories: Any = None, **metadata: Any) -> str:
    access = _safe_text(access_level)
    privacy = _safe_text(privacy_sensitivity)
    categories = _unique_text_list(detected_pii_categories)

    if "authentication_secret" in categories or "api_key_or_token" in categories:
        return "block_content_use"
    if any(category in {"child_data", "health_data", "legal_data", "biometric_data"} for category in categories):
        return "operator_review_required"
    if privacy == "restricted_sensitive":
        return "owner_review_required" if access == "owner_private" else "operator_review_required"
    if _is_identifier_pii(categories):
        return "redact_direct_identifiers"
    if privacy in {"high_sensitivity", "medium_sensitivity"}:
        return "redact_sensitive_fields"
    if access in {"public_source", "public_website_source"}:
        return "no_scrub_required"
    if access in {"owner_private", "operator_internal", "project_internal", "workspace_shared", "third_party_source"}:
        return "summary_only"
    return DEFAULT_SCRUBBING_MODE_V1


# ---------------------------------------------------------------------------
# Packet builder / validation
# ---------------------------------------------------------------------------


def build_document_access_packet_v1(
    *,
    document_access_packet_id: str,
    source_id: str,
    source_type: str = DEFAULT_SOURCE_TYPE_V1,
    source_name: str = "",
    source_scope: str = DEFAULT_SOURCE_SCOPE_V1,
    access_level: str = DEFAULT_ACCESS_LEVEL_V1,
    privacy_sensitivity: str = DEFAULT_PRIVACY_SENSITIVITY_V1,
    detected_pii_categories: Any = None,
    scrubbing_mode: str = DEFAULT_SCRUBBING_MODE_V1,
    allowed_uses: Any = None,
    blocked_uses: Any = None,
    raw_content_allowed: bool = False,
    summary_allowed: bool = False,
    indexing_allowed: bool = False,
    vectorization_allowed: bool = False,
    private_citation_allowed: bool = False,
    public_citation_allowed: bool = False,
    answer_use_allowed: bool = False,
    public_claim_use_allowed: bool = False,
    action_use_allowed: bool = False,
    owner_review_required: bool = False,
    operator_review_required: bool = False,
    deletion_required_on_request: bool = False,
    export_required_on_request: bool = False,
    retention_policy_ref: str = DEFAULT_RETENTION_POLICY_REF_V1,
    source_evidence_graph_allowed: bool = False,
    rag_routing_allowed: bool = False,
    daemon_packet_allowed: bool = False,
    recommended_next_gate: str = DEFAULT_RECOMMENDED_NEXT_GATE_V1,
    runtime_authority: bool = False,
    writes_state: bool = False,
    model_provider_used: bool = False,
    public_claim_allowed: bool = False,
    proof_claim_allowed: bool = False,
    learning_claimed: bool = False,
    safe_metadata: Any = None,
    **extra: Any,
) -> dict[str, Any]:
    packet = {
        "document_access_packet_id": _safe_text(document_access_packet_id),
        "source_id": _safe_text(source_id),
        "source_type": _safe_text(source_type),
        "source_name": _safe_text(source_name),
        "source_scope": _safe_text(source_scope),
        "access_level": _safe_text(access_level),
        "privacy_sensitivity": _safe_text(privacy_sensitivity),
        "detected_pii_categories": _unique_text_list(detected_pii_categories),
        "scrubbing_mode": _safe_text(scrubbing_mode),
        "allowed_uses": _unique_text_list(allowed_uses),
        "blocked_uses": _unique_text_list(blocked_uses),
        "raw_content_allowed": _safe_bool(raw_content_allowed),
        "summary_allowed": _safe_bool(summary_allowed),
        "indexing_allowed": _safe_bool(indexing_allowed),
        "vectorization_allowed": _safe_bool(vectorization_allowed),
        "private_citation_allowed": _safe_bool(private_citation_allowed),
        "public_citation_allowed": _safe_bool(public_citation_allowed),
        "answer_use_allowed": _safe_bool(answer_use_allowed),
        "public_claim_use_allowed": _safe_bool(public_claim_use_allowed),
        "action_use_allowed": _safe_bool(action_use_allowed),
        "owner_review_required": _safe_bool(owner_review_required),
        "operator_review_required": _safe_bool(operator_review_required),
        "deletion_required_on_request": _safe_bool(deletion_required_on_request),
        "export_required_on_request": _safe_bool(export_required_on_request),
        "retention_policy_ref": _safe_text(retention_policy_ref),
        "source_evidence_graph_allowed": _safe_bool(source_evidence_graph_allowed),
        "rag_routing_allowed": _safe_bool(rag_routing_allowed),
        "daemon_packet_allowed": _safe_bool(daemon_packet_allowed),
        "recommended_next_gate": _safe_text(recommended_next_gate),
        "runtime_authority": _safe_bool(runtime_authority),
        "writes_state": _safe_bool(writes_state),
        "model_provider_used": _safe_bool(model_provider_used),
        "public_claim_allowed": _safe_bool(public_claim_allowed),
        "proof_claim_allowed": _safe_bool(proof_claim_allowed),
        "learning_claimed": _safe_bool(learning_claimed),
        "safe_metadata": _normalize_metadata(safe_metadata),
    }
    if extra:
        packet["safe_metadata"]["extra_metadata"] = _json_safe(extra)

    # Auto-classify missing metadata only from supplied metadata.
    if packet["access_level"] == DEFAULT_ACCESS_LEVEL_V1 or packet["access_level"] == "":
        packet["access_level"] = classify_document_access_v1(
            source_scope=packet["source_scope"],
            source_type=packet["source_type"],
            access_level=packet["access_level"],
        )
    if packet["privacy_sensitivity"] == DEFAULT_PRIVACY_SENSITIVITY_V1 or packet["privacy_sensitivity"] == "":
        packet["privacy_sensitivity"] = classify_pii_sensitivity_v1(
            detected_pii_categories=packet["detected_pii_categories"],
            source_scope=packet["source_scope"],
            access_level=packet["access_level"],
        )
    if packet["scrubbing_mode"] == DEFAULT_SCRUBBING_MODE_V1 or packet["scrubbing_mode"] == "":
        packet["scrubbing_mode"] = select_scrubbing_mode_v1(
            access_level=packet["access_level"],
            privacy_sensitivity=packet["privacy_sensitivity"],
            detected_pii_categories=packet["detected_pii_categories"],
        )

    validate_document_access_packet_v1(packet)
    return packet



def validate_document_access_packet_v1(packet: Any) -> bool:
    packet = to_document_access_json_safe_v1(packet)
    if not isinstance(packet, Mapping):
        raise ValidationError("packet_must_be_mapping")

    if _contains_forbidden_field(packet):
        raise ValidationError("hidden_prompt_or_raw_private_field")
    if _contains_forbidden_claim_marker(packet):
        raise ValidationError("claim_marker_blocked")

    access_level = _safe_text(packet.get("access_level"))
    privacy_sensitivity = _safe_text(packet.get("privacy_sensitivity"))
    scrubbing_mode = _safe_text(packet.get("scrubbing_mode"))
    source_type = _safe_text(packet.get("source_type"))
    source_scope = _safe_text(packet.get("source_scope"))
    detected_pii_categories = _unique_text_list(packet.get("detected_pii_categories"))
    allowed_uses = _unique_text_list(packet.get("allowed_uses"))
    blocked_uses = _unique_text_list(packet.get("blocked_uses"))

    if access_level not in ALLOWED_ACCESS_LEVELS_V1:
        raise ValidationError("unknown_access_level")
    if privacy_sensitivity not in ALLOWED_PRIVACY_SENSITIVITY_LEVELS_V1:
        raise ValidationError("unknown_privacy_sensitivity")
    if scrubbing_mode not in ALLOWED_SCRUBBING_MODES_V1:
        raise ValidationError("unknown_scrubbing_mode")
    if source_scope not in ALLOWED_SOURCE_SCOPES_V1:
        raise ValidationError("unknown_access_level")
    if source_type not in ALLOWED_SOURCE_TYPES_V1:
        raise ValidationError("unknown_source_type")

    for use in allowed_uses + blocked_uses:
        if use not in ALLOWED_USE_PERMISSIONS_V1:
            raise ValidationError("unknown_use_permission")

    for category in detected_pii_categories:
        if category not in ALLOWED_PII_CATEGORIES_V1:
            raise ValidationError("unknown_pii_category")

    if packet.get("runtime_authority") is True:
        raise ValidationError("runtime_authority_true")
    if packet.get("writes_state") is True:
        raise ValidationError("writes_state_true")
    if packet.get("model_provider_used") is True:
        raise ValidationError("model_provider_used_true")
    if packet.get("public_claim_allowed") is True:
        raise ValidationError("public_claim_allowed_true")
    if packet.get("proof_claim_allowed") is True:
        raise ValidationError("proof_claim_allowed_true")
    if packet.get("learning_claimed") is True:
        raise ValidationError("learning_claimed_true")

    if packet.get("action_use_allowed") is True:
        raise ValidationError("action_use_allowed_true")

    if packet.get("daemon_packet_allowed") is True and packet.get("raw_content_allowed") is True:
        raise ValidationError("daemon_packet_raw_content_blocked")

    if packet.get("vectorization_allowed") is True:
        if not packet.get("retention_policy_ref") or packet.get("retention_policy_ref") == DEFAULT_RETENTION_POLICY_REF_V1:
            raise ValidationError("vectorization_policy_missing")
        if not packet.get("deletion_required_on_request"):
            raise ValidationError("vectorization_deletion_missing")
        if not packet.get("export_required_on_request"):
            raise ValidationError("vectorization_export_missing")

    if access_level in {"owner_private", "access_blocked"} and packet.get("public_citation_allowed") is True:
        raise ValidationError("public_citation_blocked_for_private_source")
    if access_level in {"owner_private", "operator_internal", "project_internal", "workspace_shared", "access_blocked"} and packet.get("public_claim_use_allowed") is True:
        raise ValidationError("public_claim_use_blocked_for_private_evidence")

    if access_level == "owner_private" and packet.get("public_citation_allowed") is True:
        raise ValidationError("public_citation_blocked_for_private_source")
    if privacy_sensitivity in {"restricted_sensitive", "high_sensitivity"} and packet.get("raw_content_allowed") is True:
        raise ValidationError("raw_content_blocked_for_sensitive_data")
    if privacy_sensitivity in {"restricted_sensitive", "high_sensitivity"} and packet.get("public_citation_allowed") is True:
        raise ValidationError("public_citation_blocked_for_sensitive_data")
    if privacy_sensitivity in {"restricted_sensitive", "high_sensitivity"} and packet.get("public_claim_use_allowed") is True:
        raise ValidationError("public_claim_use_blocked_for_sensitive_data")

    if any(category in {"authentication_secret", "api_key_or_token"} for category in detected_pii_categories):
        if scrubbing_mode != "block_content_use":
            raise ValidationError("api_key_or_token_must_block_content_use")
        if packet.get("summary_allowed") is True or packet.get("raw_content_allowed") is True:
            raise ValidationError("api_key_or_token_must_not_be_summarized")

    if any(category in {"child_data", "health_data", "legal_data", "biometric_data"} for category in detected_pii_categories):
        if privacy_sensitivity != "restricted_sensitive":
            raise ValidationError("restricted_sensitive_required")
        if not (packet.get("owner_review_required") and packet.get("operator_review_required")):
            raise ValidationError("review_required_for_sensitive_data")
        if scrubbing_mode not in {"owner_review_required", "operator_review_required", "block_content_use", "block_public_use"}:
            raise ValidationError("review_scrubbing_mode_required")

    if "child_data" in detected_pii_categories:
        if privacy_sensitivity != "restricted_sensitive":
            raise ValidationError("child_data_restricted_sensitive_required")
        if not (packet.get("owner_review_required") and packet.get("operator_review_required")):
            raise ValidationError("child_data_review_required")

    if any(category in {"email_address", "phone_number", "postal_address", "precise_location", "government_id"} for category in detected_pii_categories):
        if scrubbing_mode not in {"redact_direct_identifiers", "redact_sensitive_fields", "metadata_only", "summary_only", "hash_reference_only"}:
            raise ValidationError("direct_identifier_redaction_required")

    if packet.get("raw_content_allowed") is True and access_level in {"owner_private", "operator_internal", "project_internal", "workspace_shared", "third_party_source", "access_blocked"}:
        if privacy_sensitivity in {"restricted_sensitive", "high_sensitivity", "medium_sensitivity"}:
            raise ValidationError("raw_content_blocked_for_sensitive_or_private_data")

    if packet.get("summary_allowed") is True and packet.get("scrubbing_mode") == "block_content_use":
        raise ValidationError("summary_blocked_by_content_use_mode")

    if packet.get("source_evidence_graph_allowed") is True and access_level == "access_blocked":
        raise ValidationError("graph_blocked_for_blocked_access")

    if packet.get("rag_routing_allowed") is True and access_level == "access_blocked":
        raise ValidationError("rag_blocked_for_blocked_access")

    if packet.get("daemon_packet_allowed") is True and packet.get("raw_content_allowed") is True:
        raise ValidationError("daemon_packet_raw_content_blocked")

    if packet.get("daemon_packet_allowed") is True and packet.get("privacy_sensitivity") == "restricted_sensitive":
        if packet.get("raw_content_allowed") is True:
            raise ValidationError("daemon_packet_raw_sensitive_blocked")

    if packet.get("public_citation_allowed") is True and access_level == "owner_private":
        raise ValidationError("public_citation_blocked_for_private_source")

    if packet.get("public_claim_use_allowed") is True and access_level in {"owner_private", "operator_internal", "project_internal", "workspace_shared", "access_blocked"}:
        raise ValidationError("public_claim_use_blocked_for_private_evidence")

    if packet.get("safe_metadata") and _contains_forbidden_claim_marker(packet.get("safe_metadata")):
        raise ValidationError("claim_marker_blocked")

    return True



def summarize_document_access_packet_v1(packet: Any) -> dict[str, Any]:
    packet = to_document_access_json_safe_v1(packet)
    validate_document_access_packet_v1(packet)
    return {
        "summary_type": SUMMARY_TYPE_V1,
        "document_access_packet_id": packet.get("document_access_packet_id"),
        "source_id": packet.get("source_id"),
        "access_level": packet.get("access_level"),
        "privacy_sensitivity": packet.get("privacy_sensitivity"),
        "scrubbing_mode": packet.get("scrubbing_mode"),
        "allowed_uses": packet.get("allowed_uses", []),
        "blocked_uses": packet.get("blocked_uses", []),
        "source_evidence_graph_allowed": bool(packet.get("source_evidence_graph_allowed")),
        "rag_routing_allowed": bool(packet.get("rag_routing_allowed")),
        "daemon_packet_allowed": bool(packet.get("daemon_packet_allowed")),
        "recommended_next_gate": packet.get("recommended_next_gate"),
    }


# ---------------------------------------------------------------------------
# Initial examples
# ---------------------------------------------------------------------------


def _example_base(
    *,
    document_access_packet_id: str,
    source_id: str,
    source_type: str,
    source_name: str,
    source_scope: str,
    access_level: str,
    privacy_sensitivity: str,
    detected_pii_categories: Any,
    scrubbing_mode: str,
    allowed_uses: Any,
    blocked_uses: Any,
    raw_content_allowed: bool,
    summary_allowed: bool,
    indexing_allowed: bool,
    vectorization_allowed: bool,
    private_citation_allowed: bool,
    public_citation_allowed: bool,
    answer_use_allowed: bool,
    public_claim_use_allowed: bool,
    action_use_allowed: bool,
    owner_review_required: bool,
    operator_review_required: bool,
    deletion_required_on_request: bool,
    export_required_on_request: bool,
    retention_policy_ref: str,
    source_evidence_graph_allowed: bool,
    rag_routing_allowed: bool,
    daemon_packet_allowed: bool,
    recommended_next_gate: str,
) -> dict[str, Any]:
    return build_document_access_packet_v1(
        document_access_packet_id=document_access_packet_id,
        source_id=source_id,
        source_type=source_type,
        source_name=source_name,
        source_scope=source_scope,
        access_level=access_level,
        privacy_sensitivity=privacy_sensitivity,
        detected_pii_categories=detected_pii_categories,
        scrubbing_mode=scrubbing_mode,
        allowed_uses=allowed_uses,
        blocked_uses=blocked_uses,
        raw_content_allowed=raw_content_allowed,
        summary_allowed=summary_allowed,
        indexing_allowed=indexing_allowed,
        vectorization_allowed=vectorization_allowed,
        private_citation_allowed=private_citation_allowed,
        public_citation_allowed=public_citation_allowed,
        answer_use_allowed=answer_use_allowed,
        public_claim_use_allowed=public_claim_use_allowed,
        action_use_allowed=action_use_allowed,
        owner_review_required=owner_review_required,
        operator_review_required=operator_review_required,
        deletion_required_on_request=deletion_required_on_request,
        export_required_on_request=export_required_on_request,
        retention_policy_ref=retention_policy_ref,
        source_evidence_graph_allowed=source_evidence_graph_allowed,
        rag_routing_allowed=rag_routing_allowed,
        daemon_packet_allowed=daemon_packet_allowed,
        recommended_next_gate=recommended_next_gate,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        proof_claim_allowed=False,
        learning_claimed=False,
        safe_metadata={"example_name": document_access_packet_id, **DEFAULT_SAFE_METADATA_V1},
    )



def build_initial_document_access_examples_v1() -> list[dict[str, Any]]:
    return [
        _example_base(
            document_access_packet_id="public_source_may_be_summarized_and_cited_publicly",
            source_id="src_public_001",
            source_type="web_source",
            source_name="public article",
            source_scope="public_source",
            access_level="public_source",
            privacy_sensitivity="non_sensitive",
            detected_pii_categories=[],
            scrubbing_mode="no_scrub_required",
            allowed_uses=["may_read_metadata", "may_read_summary", "may_read_content", "may_index", "may_vectorize", "may_quote", "may_cite_public", "may_use_for_answer"],
            blocked_uses=["may_cite_private", "may_use_for_public_claim", "may_use_for_action"],
            raw_content_allowed=True,
            summary_allowed=True,
            indexing_allowed=True,
            vectorization_allowed=False,
            private_citation_allowed=False,
            public_citation_allowed=True,
            answer_use_allowed=True,
            public_claim_use_allowed=False,
            action_use_allowed=False,
            owner_review_required=False,
            operator_review_required=False,
            deletion_required_on_request=False,
            export_required_on_request=False,
            retention_policy_ref="public_source_retention_policy_v1",
            source_evidence_graph_allowed=True,
            rag_routing_allowed=True,
            daemon_packet_allowed=False,
            recommended_next_gate="public source may proceed through summary, citation, and RAG",
        ),
        _example_base(
            document_access_packet_id="owner_private_document_supports_private_answer_not_public_citation",
            source_id="src_owner_private_001",
            source_type="file",
            source_name="owner note",
            source_scope="owner_private",
            access_level="owner_private",
            privacy_sensitivity="high_sensitivity",
            detected_pii_categories=["private_message"],
            scrubbing_mode="summary_only",
            allowed_uses=["may_read_metadata", "may_read_summary", "may_use_for_answer"],
            blocked_uses=["may_cite_public", "may_use_for_public_claim", "may_use_for_action"],
            raw_content_allowed=False,
            summary_allowed=True,
            indexing_allowed=False,
            vectorization_allowed=False,
            private_citation_allowed=True,
            public_citation_allowed=False,
            answer_use_allowed=True,
            public_claim_use_allowed=False,
            action_use_allowed=False,
            owner_review_required=True,
            operator_review_required=False,
            deletion_required_on_request=True,
            export_required_on_request=True,
            retention_policy_ref="owner_private_retention_policy_v1",
            source_evidence_graph_allowed=True,
            rag_routing_allowed=True,
            daemon_packet_allowed=True,
            recommended_next_gate="private answer only; do not expose public citations",
        ),
        _example_base(
            document_access_packet_id="access_restricted_document_blocks_rag_retrieval",
            source_id="src_blocked_001",
            source_type="retrieved_document",
            source_name="blocked document",
            source_scope="access_blocked",
            access_level="access_blocked",
            privacy_sensitivity="restricted_sensitive",
            detected_pii_categories=["private_message"],
            scrubbing_mode="block_content_use",
            allowed_uses=["may_read_metadata"],
            blocked_uses=["may_read_content", "may_index", "may_vectorize", "may_cite_public", "may_use_for_answer", "may_use_for_public_claim", "may_use_for_action"],
            raw_content_allowed=False,
            summary_allowed=False,
            indexing_allowed=False,
            vectorization_allowed=False,
            private_citation_allowed=False,
            public_citation_allowed=False,
            answer_use_allowed=False,
            public_claim_use_allowed=False,
            action_use_allowed=False,
            owner_review_required=False,
            operator_review_required=True,
            deletion_required_on_request=True,
            export_required_on_request=True,
            retention_policy_ref="blocked_access_retention_policy_v1",
            source_evidence_graph_allowed=False,
            rag_routing_allowed=False,
            daemon_packet_allowed=True,
            recommended_next_gate="blocked access; route only compact metadata",
        ),
        _example_base(
            document_access_packet_id="email_phone_requires_identifier_redaction",
            source_id="src_pii_001",
            source_type="file",
            source_name="contact sheet",
            source_scope="project_internal",
            access_level="project_internal",
            privacy_sensitivity="medium_sensitivity",
            detected_pii_categories=["email_address", "phone_number"],
            scrubbing_mode="redact_direct_identifiers",
            allowed_uses=["may_read_metadata", "may_read_summary", "may_use_for_answer"],
            blocked_uses=["may_cite_public", "may_use_for_public_claim", "may_use_for_action"],
            raw_content_allowed=False,
            summary_allowed=True,
            indexing_allowed=True,
            vectorization_allowed=False,
            private_citation_allowed=True,
            public_citation_allowed=False,
            answer_use_allowed=True,
            public_claim_use_allowed=False,
            action_use_allowed=False,
            owner_review_required=False,
            operator_review_required=False,
            deletion_required_on_request=True,
            export_required_on_request=True,
            retention_policy_ref="pii_redaction_retention_policy_v1",
            source_evidence_graph_allowed=True,
            rag_routing_allowed=True,
            daemon_packet_allowed=True,
            recommended_next_gate="redact direct identifiers before reuse",
        ),
        _example_base(
            document_access_packet_id="api_key_blocks_content_use",
            source_id="src_secret_001",
            source_type="file",
            source_name="credential export",
            source_scope="owner_private",
            access_level="owner_private",
            privacy_sensitivity="restricted_sensitive",
            detected_pii_categories=["api_key_or_token"],
            scrubbing_mode="block_content_use",
            allowed_uses=["may_read_metadata"],
            blocked_uses=["may_read_content", "may_index", "may_vectorize", "may_cite_public", "may_use_for_answer", "may_use_for_public_claim", "may_use_for_action"],
            raw_content_allowed=False,
            summary_allowed=False,
            indexing_allowed=False,
            vectorization_allowed=False,
            private_citation_allowed=False,
            public_citation_allowed=False,
            answer_use_allowed=False,
            public_claim_use_allowed=False,
            action_use_allowed=False,
            owner_review_required=True,
            operator_review_required=True,
            deletion_required_on_request=True,
            export_required_on_request=True,
            retention_policy_ref="secret_block_retention_policy_v1",
            source_evidence_graph_allowed=True,
            rag_routing_allowed=False,
            daemon_packet_allowed=True,
            recommended_next_gate="block content use; do not summarize secrets or tokens",
        ),
        _example_base(
            document_access_packet_id="child_data_restricted_sensitive",
            source_id="src_child_001",
            source_type="memory",
            source_name="child note",
            source_scope="operator_internal",
            access_level="operator_internal",
            privacy_sensitivity="restricted_sensitive",
            detected_pii_categories=["child_data"],
            scrubbing_mode="operator_review_required",
            allowed_uses=["may_read_metadata", "may_read_summary"],
            blocked_uses=["may_cite_public", "may_use_for_public_claim", "may_use_for_action", "may_vectorize"],
            raw_content_allowed=False,
            summary_allowed=True,
            indexing_allowed=False,
            vectorization_allowed=False,
            private_citation_allowed=True,
            public_citation_allowed=False,
            answer_use_allowed=True,
            public_claim_use_allowed=False,
            action_use_allowed=False,
            owner_review_required=True,
            operator_review_required=True,
            deletion_required_on_request=True,
            export_required_on_request=True,
            retention_policy_ref="restricted_sensitive_retention_policy_v1",
            source_evidence_graph_allowed=True,
            rag_routing_allowed=True,
            daemon_packet_allowed=True,
            recommended_next_gate="restricted-sensitive handling with review",
        ),
        _example_base(
            document_access_packet_id="health_legal_data_owner_operator_review",
            source_id="src_health_legal_001",
            source_type="artifact",
            source_name="medical-legal bundle",
            source_scope="operator_internal",
            access_level="operator_internal",
            privacy_sensitivity="restricted_sensitive",
            detected_pii_categories=["health_data", "legal_data"],
            scrubbing_mode="operator_review_required",
            allowed_uses=["may_read_metadata", "may_read_summary"],
            blocked_uses=["may_cite_public", "may_use_for_public_claim", "may_use_for_action", "may_vectorize"],
            raw_content_allowed=False,
            summary_allowed=True,
            indexing_allowed=False,
            vectorization_allowed=False,
            private_citation_allowed=True,
            public_citation_allowed=False,
            answer_use_allowed=True,
            public_claim_use_allowed=False,
            action_use_allowed=False,
            owner_review_required=True,
            operator_review_required=True,
            deletion_required_on_request=True,
            export_required_on_request=True,
            retention_policy_ref="health_legal_retention_policy_v1",
            source_evidence_graph_allowed=True,
            rag_routing_allowed=False,
            daemon_packet_allowed=True,
            recommended_next_gate="owner/operator review required before any reuse",
        ),
        _example_base(
            document_access_packet_id="uploaded_project_file_summary_only_graph_allowed",
            source_id="src_project_file_001",
            source_type="uploaded_file",
            source_name="project upload",
            source_scope="project_internal",
            access_level="project_internal",
            privacy_sensitivity="medium_sensitivity",
            detected_pii_categories=["employment_data"],
            scrubbing_mode="summary_only",
            allowed_uses=["may_read_metadata", "may_read_summary", "may_use_for_answer"],
            blocked_uses=["may_cite_public", "may_use_for_public_claim", "may_use_for_action"],
            raw_content_allowed=False,
            summary_allowed=True,
            indexing_allowed=True,
            vectorization_allowed=False,
            private_citation_allowed=True,
            public_citation_allowed=False,
            answer_use_allowed=True,
            public_claim_use_allowed=False,
            action_use_allowed=False,
            owner_review_required=False,
            operator_review_required=False,
            deletion_required_on_request=True,
            export_required_on_request=True,
            retention_policy_ref="project_upload_retention_policy_v1",
            source_evidence_graph_allowed=True,
            rag_routing_allowed=True,
            daemon_packet_allowed=True,
            recommended_next_gate="summary-only graph entry permitted",
        ),
        _example_base(
            document_access_packet_id="private_evidence_blocks_public_website_claim",
            source_id="src_private_claim_001",
            source_type="file",
            source_name="private evidence",
            source_scope="owner_private",
            access_level="owner_private",
            privacy_sensitivity="high_sensitivity",
            detected_pii_categories=["private_message"],
            scrubbing_mode="summary_only",
            allowed_uses=["may_read_metadata", "may_read_summary", "may_use_for_answer"],
            blocked_uses=["may_cite_public", "may_use_for_public_claim", "may_use_for_action"],
            raw_content_allowed=False,
            summary_allowed=True,
            indexing_allowed=False,
            vectorization_allowed=False,
            private_citation_allowed=True,
            public_citation_allowed=False,
            answer_use_allowed=True,
            public_claim_use_allowed=False,
            action_use_allowed=False,
            owner_review_required=True,
            operator_review_required=False,
            deletion_required_on_request=True,
            export_required_on_request=True,
            retention_policy_ref="private_evidence_retention_policy_v1",
            source_evidence_graph_allowed=True,
            rag_routing_allowed=True,
            daemon_packet_allowed=True,
            recommended_next_gate="private evidence may not support public website claims",
        ),
        _example_base(
            document_access_packet_id="daemon_receives_access_blocked_compact_verdict",
            source_id="src_daemon_001",
            source_type="source_node",
            source_name="daemon verdict seed",
            source_scope="access_blocked",
            access_level="access_blocked",
            privacy_sensitivity="restricted_sensitive",
            detected_pii_categories=["unknown_pii"],
            scrubbing_mode="block_content_use",
            allowed_uses=["may_read_metadata"],
            blocked_uses=["may_read_content", "may_index", "may_vectorize", "may_cite_public", "may_use_for_answer", "may_use_for_public_claim", "may_use_for_action"],
            raw_content_allowed=False,
            summary_allowed=False,
            indexing_allowed=False,
            vectorization_allowed=False,
            private_citation_allowed=False,
            public_citation_allowed=False,
            answer_use_allowed=False,
            public_claim_use_allowed=False,
            action_use_allowed=False,
            owner_review_required=False,
            operator_review_required=True,
            deletion_required_on_request=True,
            export_required_on_request=True,
            retention_policy_ref="daemon_compact_verdict_policy_v1",
            source_evidence_graph_allowed=False,
            rag_routing_allowed=False,
            daemon_packet_allowed=True,
            recommended_next_gate="daemon gets compact access-blocked verdict only",
        ),
    ]
