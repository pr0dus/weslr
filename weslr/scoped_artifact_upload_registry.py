"""Scoped artifact/upload registry metadata helpers for WESLR.

This module is intentionally import-safe and side-effect-free. It builds and
validates metadata envelopes only. It does not read artifact/upload content,
filesystems, databases, auth/session state, browser/runtime state, providers,
models, search/advisors, network resources, or `.weslr` state, and it does not
generate final/user-facing answers.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Mapping

from weslr.read_authorization import (
    authorize_scoped_read_v1,
    build_read_authorization_request_v1,
    summarize_read_authorization_v1,
    to_read_authorization_json_safe_v1,
)
from weslr.source_scope import summarize_source_scope_v1, validate_source_scope_v1

SCHEMA_VERSION = "weslr.scoped_artifact_upload_registry.v1"

ARTIFACT_UPLOAD_KINDS = {
    "artifact",
    "upload",
    "artifact_metadata",
    "upload_metadata",
    "provenance_summary",
}

ALLOWED_ACCESS_MODES = {
    "metadata_only_preview",
    "redacted_summary_candidate",
    "continuity_anchor_metadata",
    "provenance_summary_metadata",
    "blocked_no_access",
}

FORBIDDEN_ACCESS_MODES = {
    "raw_artifact_content",
    "raw_upload_content",
    "cross_user_artifact_access",
    "global_artifact_registry",
    "dot_weslr_artifact_state",
    "runtime_transcript_upload",
    "browser_public_upload_state",
    "provider_output_ingestion",
    "final_answer_artifact_injection",
    "unrestricted_artifact_dump",
}

DENIED_AUTHORITY_FIELDS = (
    "grants_runtime_authority",
    "permits_public_browser_runtime",
    "permits_provider_calls",
    "permits_dot_weslr_public_state",
    "permits_final_answer_generation",
    "permits_unscoped_artifact_reads",
    "permits_cross_user_artifact_access",
    "permits_raw_artifact_content",
    "permits_raw_upload_content",
    "permits_database_reads",
    "permits_authentication_decisions",
    "permits_upload_ingestion",
    "permits_filesystem_scanning",
)

DEFAULT_DENIED_AUTHORITY = {field: False for field in DENIED_AUTHORITY_FIELDS}

ALLOW_DECISIONS = {"allow_metadata_only", "allow_read_for_internal_shadow_use"}

FORBIDDEN_MARKERS = {
    ".weslr": "dot_weslr_marker",
    "tl_default": "tl_default_marker",
    "global_artifact_registry": "global_artifact_registry_marker",
    "process_global": "process_global_marker",
    "process-global": "process_global_marker",
    "default_timeline": "default_timeline_marker",
    "query_string": "query_string_identity_marker",
    "query-string": "query_string_identity_marker",
    "final_answer": "final_answer_authority_marker",
    "user_output": "final_answer_authority_marker",
    "reply_text": "final_answer_authority_marker",
    "runtime_chat": "runtime_authority_marker",
    "chat_runtime": "runtime_authority_marker",
    "browser_runtime": "runtime_authority_marker",
    "provider_call": "provider_or_search_authority_marker",
    "model_call": "provider_or_search_authority_marker",
    "search_call": "provider_or_search_authority_marker",
    "advisor_call": "provider_or_search_authority_marker",
}

CONTENT_KEYS = {
    "content",
    "raw_content",
    "raw_artifact_content",
    "raw_upload_content",
    "artifact_content",
    "upload_content",
    "artifact_bytes",
    "upload_bytes",
    "transcript_text",
    "final_answer_text",
}

SCOPE_KEYS = (
    "tenant_id",
    "account_id",
    "user_id",
    "guest_id",
    "session_id",
    "conversation_id",
    "workspace_id",
    "project_id",
)


def _is_blank(value: Any) -> bool:
    return value is None or value == ""


def _is_json_safe(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_is_json_safe(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_json_safe(item) for key, item in value.items())
    return False


def _json_safe_copy(value: Any) -> Any:
    if not _is_json_safe(value):
        raise ValueError("scoped artifact/upload registry metadata is not JSON-safe")
    return json.loads(json.dumps(value, sort_keys=True))


def _as_record(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("metadata must be a mapping")
    return deepcopy(dict(value))


def _normalize_denied_authority(denied_authority: Mapping[str, Any] | None = None) -> dict[str, Any]:
    denied = dict(DEFAULT_DENIED_AUTHORITY)
    if denied_authority is not None:
        denied.update(dict(denied_authority))
    return denied


def _scope_metadata(scope: Mapping[str, Any] | None) -> dict[str, Any]:
    source = dict(scope or {})
    return {key: source.get(key) for key in SCOPE_KEYS}


def _scope_is_missing(scope: Any) -> bool:
    return not isinstance(scope, Mapping) or all(_is_blank(scope.get(key)) for key in SCOPE_KEYS)


def _collect_marker_reasons(value: Any) -> list[str]:
    reasons: list[str] = []
    if isinstance(value, str):
        lowered = value.lower()
        for marker, reason in FORBIDDEN_MARKERS.items():
            if marker in lowered:
                reasons.append(reason)
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if key in {"denied_authority", "blocked_reason_labels", "decision_reason_labels", "required_followup"}:
                continue
            if key in CONTENT_KEYS and not _is_blank(item):
                reasons.append(f"raw_content_field_present:{key}")
            reasons.extend(_collect_marker_reasons(item))
    elif isinstance(value, list):
        for item in value:
            reasons.extend(_collect_marker_reasons(item))
    return sorted(set(reasons))


def _requested_scope_match_label(requester: Mapping[str, Any] | None, target: Mapping[str, Any] | None) -> str:
    if _scope_is_missing(requester) or _scope_is_missing(target):
        return "missing_scope"
    requester_scope = dict(requester or {})
    target_scope = dict(target or {})
    if requester_scope.get("tenant_id") != target_scope.get("tenant_id"):
        return "cross_tenant"
    if requester_scope.get("account_id") and target_scope.get("account_id") and requester_scope.get("account_id") != target_scope.get("account_id"):
        return "cross_user"
    if requester_scope.get("user_id") and target_scope.get("user_id") and requester_scope.get("user_id") != target_scope.get("user_id"):
        return "cross_user"
    if requester_scope.get("guest_id") and (target_scope.get("account_id") or target_scope.get("user_id")):
        return "guest_to_authenticated"
    if (requester_scope.get("account_id") or requester_scope.get("user_id")) and target_scope.get("guest_id"):
        return "authenticated_to_guest"
    if requester_scope.get("session_id") and target_scope.get("session_id") and requester_scope.get("session_id") != target_scope.get("session_id"):
        return "same_user_different_session"
    if requester_scope.get("conversation_id") and target_scope.get("conversation_id") and requester_scope.get("conversation_id") != target_scope.get("conversation_id"):
        return "same_user_different_conversation"
    return "same_scope"


def _blocked_validation(reasons: list[str]) -> dict[str, Any]:
    return {
        "valid": False,
        "validation_status": "blocked_no_access",
        "blocked_reasons": sorted(set(reasons)),
        "access_mode": "blocked_no_access",
        "content_included": False,
        "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
    }


def build_scoped_artifact_upload_registry_entry_v1(
    *,
    registry_entry_id: str,
    artifact_or_upload_kind: str,
    source_scope: Mapping[str, Any] | None,
    owner_scope: Mapping[str, Any] | None,
    requester_scope: Mapping[str, Any] | None,
    target_scope: Mapping[str, Any] | None,
    requested_use_context: str,
    requested_content_mode: str,
    access_mode: str = "metadata_only_preview",
    privacy_label: str = "unknown",
    retention_label: str = "unknown",
    provenance_label: str = "unknown",
    currentness_label: str = "unknown",
    policy_label: str = "unknown",
    public_browser_context: bool = False,
    runtime_context_label: str = "internal_metadata",
    authorization_request: Mapping[str, Any] | None = None,
    authorization_id: str | None = None,
    denied_authority: Mapping[str, Any] | None = None,
    **metadata: Any,
) -> dict[str, Any]:
    """Build a JSON-safe metadata-only scoped access request.

    No artifact/upload content is read. When ``authorization_request`` is not
    supplied, a central read-authorization request is built from the same
    explicit metadata so authorization can be evaluated later.
    """

    owner = _scope_metadata(owner_scope)
    requester = _scope_metadata(requester_scope)
    target = _scope_metadata(target_scope)
    auth_request = authorization_request
    if auth_request is None:
        auth_request = build_read_authorization_request_v1(
            authorization_id=authorization_id or f"auth_{registry_entry_id}",
            source_scope=source_scope,
            requested_read_kind=artifact_or_upload_kind,
            requested_use_context=requested_use_context,
            requester_scope=requester,
            target_scope=target,
            public_browser_context=public_browser_context,
            runtime_context_label=runtime_context_label,
            privacy_label=privacy_label,
            retention_label=retention_label,
            provenance_label=provenance_label,
            currentness_label=currentness_label,
            policy_label=policy_label,
            owner_scope_match_label=_requested_scope_match_label(owner, requester),
        )

    request: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "registry_entry_id": registry_entry_id,
        "artifact_or_upload_kind": artifact_or_upload_kind,
        "source_scope": _json_safe_copy(dict(source_scope)) if isinstance(source_scope, Mapping) else source_scope,
        "owner_scope": owner,
        "requester_scope": requester,
        "target_scope": target,
        "requested_use_context": requested_use_context,
        "requested_content_mode": requested_content_mode,
        "access_mode": access_mode,
        "privacy_label": privacy_label,
        "retention_label": retention_label,
        "provenance_label": provenance_label,
        "currentness_label": currentness_label,
        "policy_label": policy_label,
        "public_browser_context": bool(public_browser_context),
        "runtime_context_label": runtime_context_label,
        "authorization_request": _json_safe_copy(dict(auth_request)) if isinstance(auth_request, Mapping) else auth_request,
        "denied_authority": _normalize_denied_authority(denied_authority),
    }
    request.update(metadata)
    return _json_safe_copy(request)


def validate_scoped_artifact_upload_registry_entry_v1(request_metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Validate request metadata before any future access can be considered."""

    try:
        request = _as_record(request_metadata)
    except TypeError:
        return _blocked_validation(["request_metadata_not_mapping"])

    if not _is_json_safe(request):
        return _blocked_validation(["non_json_safe_metadata"])

    reasons: list[str] = []
    if request.get("schema_version") != SCHEMA_VERSION:
        reasons.append("missing_or_unsupported_schema_version")
    if _is_blank(request.get("registry_entry_id")):
        reasons.append("missing_registry_entry_id")
    if request.get("artifact_or_upload_kind") not in ARTIFACT_UPLOAD_KINDS:
        reasons.append("unsupported_artifact_or_upload_kind")

    access_mode = request.get("access_mode")
    content_mode = request.get("requested_content_mode")
    if access_mode in FORBIDDEN_ACCESS_MODES or content_mode in FORBIDDEN_ACCESS_MODES:
        reasons.append(f"forbidden_access_mode:{access_mode if access_mode in FORBIDDEN_ACCESS_MODES else content_mode}")
    if access_mode not in ALLOWED_ACCESS_MODES:
        reasons.append("unsupported_access_mode")
    if content_mode not in ALLOWED_ACCESS_MODES:
        reasons.append("unsupported_content_mode")

    denied = request.get("denied_authority")
    if not isinstance(denied, Mapping):
        reasons.append("missing_denied_authority")
        denied = {}
    for field in DENIED_AUTHORITY_FIELDS:
        if field not in denied:
            reasons.append(f"missing_denied_authority:{field}")
        elif denied.get(field) is not False:
            reasons.append(f"denied_authority_true:{field}")

    source_scope = request.get("source_scope")
    if not isinstance(source_scope, Mapping):
        reasons.append("missing_source_scope")
        source_validation = None
    else:
        source_validation = validate_source_scope_v1(
            source_scope,
            required_use_context=request.get("requested_use_context") if isinstance(request.get("requested_use_context"), str) else None,
            public_browser=bool(request.get("public_browser_context")),
        )
        if not source_validation.get("valid"):
            reasons.extend(f"source_scope:{reason}" for reason in source_validation.get("blocked_reasons", ["invalid_source_scope"]))

    authorization_request = request.get("authorization_request")
    if not isinstance(authorization_request, Mapping):
        reasons.append("missing_read_authorization")

    owner_scope = request.get("owner_scope")
    requester_scope = request.get("requester_scope")
    target_scope = request.get("target_scope")
    if _scope_is_missing(owner_scope):
        reasons.append("missing_owner_scope")
    if _scope_is_missing(requester_scope):
        reasons.append("missing_requester_scope")
    if _scope_is_missing(target_scope):
        reasons.append("missing_target_scope")

    ownership_match = _requested_scope_match_label(owner_scope, requester_scope)
    requester_target_match = _requested_scope_match_label(requester_scope, target_scope)
    if ownership_match in {"cross_tenant", "cross_user"}:
        reasons.append("ownership_mismatch")
    if ownership_match in {"guest_to_authenticated", "authenticated_to_guest"}:
        reasons.append(ownership_match)
    if requester_target_match in {"cross_tenant", "cross_user"}:
        reasons.append(requester_target_match)
    if requester_target_match in {"guest_to_authenticated", "authenticated_to_guest", "same_user_different_session", "same_user_different_conversation"}:
        reasons.append(requester_target_match)

    if request.get("public_browser_context") and request.get("privacy_label") in {"user_private", "tenant_private", "operator_private", "raw_private"}:
        reasons.append("public_browser_context_requested_private_state")
    if request.get("privacy_label") == "raw_private" or request.get("requested_content_mode") in {"raw_artifact_content", "raw_upload_content"}:
        reasons.append("raw_artifact_or_upload_content_requested")
    if request.get("currentness_label") in {"stale", "unknown"} and request.get("requested_use_context") in {"candidate_metadata", "authority_checkpoint"}:
        reasons.append("stale_or_unknown_source_requested_as_truth")
    if request.get("provenance_label") in {"inferred", "unknown"} and request.get("requested_use_context") in {"candidate_metadata", "authority_checkpoint"}:
        reasons.append("untrusted_source_requested_as_truth")

    reasons.extend(_collect_marker_reasons(request))

    if reasons:
        out = _blocked_validation(reasons)
        if source_validation is not None:
            out["source_scope_summary"] = summarize_source_scope_v1(source_validation)
        return out

    out = _json_safe_copy(request)
    out["valid"] = True
    out["validation_status"] = "valid"
    out["blocked_reasons"] = []
    out["access_mode"] = access_mode
    out["content_included"] = False
    out["source_scope_summary"] = summarize_source_scope_v1(source_validation) if source_validation is not None else None
    out["denied_authority"] = dict(DEFAULT_DENIED_AUTHORITY)
    return out


def authorize_scoped_artifact_upload_access_v1(request_metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate adapter request and central read authorization metadata only."""

    validation = validate_scoped_artifact_upload_registry_entry_v1(request_metadata)
    request = _as_record(request_metadata) if isinstance(request_metadata, Mapping) and _is_json_safe(request_metadata) else {}
    if not validation.get("valid"):
        return {
            "schema_version": SCHEMA_VERSION,
            "registry_entry_id": request.get("registry_entry_id"),
            "authorization_status": "blocked",
            "access_status": "blocked_no_access",
            "access_mode": "blocked_no_access",
            "content_included": False,
            "blocked_reason_labels": validation.get("blocked_reasons", ["invalid_request"]),
            "central_authorization_decision": None,
            "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
        }

    if request.get("access_mode") == "blocked_no_access":
        return {
            "schema_version": SCHEMA_VERSION,
            "registry_entry_id": request.get("registry_entry_id"),
            "authorization_status": "blocked",
            "access_status": "blocked_no_access",
            "access_mode": "blocked_no_access",
            "content_included": False,
            "blocked_reason_labels": ["explicit_blocked_no_access_mode"],
            "central_authorization_decision": None,
            "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
        }

    central_decision = authorize_scoped_read_v1(request["authorization_request"])
    decision_label = central_decision.get("decision")
    if decision_label not in ALLOW_DECISIONS:
        return {
            "schema_version": SCHEMA_VERSION,
            "registry_entry_id": request.get("registry_entry_id"),
            "authorization_status": "blocked",
            "access_status": "blocked_no_access",
            "access_mode": "blocked_no_access",
            "content_included": False,
            "blocked_reason_labels": sorted(set(["read_authorization_not_allowed", *(central_decision.get("blocked_reason_labels") or [])])),
            "central_authorization_decision": central_decision,
            "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
        }

    requested_mode = request.get("access_mode")
    if requested_mode == "redacted_summary_candidate" and decision_label != "allow_read_for_internal_shadow_use":
        return {
            "schema_version": SCHEMA_VERSION,
            "registry_entry_id": request.get("registry_entry_id"),
            "authorization_status": "blocked",
            "access_status": "blocked_no_access",
            "access_mode": "blocked_no_access",
            "content_included": False,
            "blocked_reason_labels": ["redacted_summary_candidate_requires_internal_shadow_authorization"],
            "central_authorization_decision": central_decision,
            "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "registry_entry_id": request.get("registry_entry_id"),
        "authorization_status": "allowed",
        "access_status": "metadata_only_allowed",
        "access_mode": requested_mode,
        "content_included": False,
        "blocked_reason_labels": [],
        "central_authorization_decision": central_decision,
        "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
    }


def build_scoped_artifact_upload_access_envelope_v1(
    request_metadata: Mapping[str, Any],
    authorization_decision: Mapping[str, Any] | None = None,
    *,
    observed_gaps: list[str] | None = None,
    next_safe_steps: list[str] | None = None,
) -> dict[str, Any]:
    """Build a metadata-only access envelope with content always excluded."""

    request = _as_record(request_metadata)
    decision = dict(authorization_decision or authorize_scoped_artifact_upload_access_v1(request))
    central = decision.get("central_authorization_decision") if isinstance(decision.get("central_authorization_decision"), Mapping) else None
    source_summary = None
    if isinstance(request.get("source_scope"), Mapping):
        validation = validate_source_scope_v1(request["source_scope"])
        source_summary = summarize_source_scope_v1(validation)

    envelope = {
        "schema_version": SCHEMA_VERSION,
        "registry_entry_id": request.get("registry_entry_id"),
        "authorization_decision": decision,
        "access_status": decision.get("access_status", "blocked_no_access"),
        "access_mode": decision.get("access_mode", "blocked_no_access"),
        "content_included": False,
        "redaction_status": "content_excluded_metadata_only",
        "scope_summary": source_summary,
        "authorization_summary": summarize_read_authorization_v1(central) if central else None,
        "provenance_summary": {"provenance_label": request.get("provenance_label")},
        "currentness_summary": {"currentness_label": request.get("currentness_label")},
        "blocked_reason_labels": sorted(set(decision.get("blocked_reason_labels") or [])),
        "observed_gaps": sorted(set(observed_gaps or [])),
        "next_safe_steps": sorted(set(next_safe_steps or ["none"])),
        "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
    }
    return _json_safe_copy(envelope)


def validate_scoped_artifact_upload_access_envelope_v1(envelope_metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a metadata-only adapter envelope."""

    try:
        envelope = _as_record(envelope_metadata)
    except TypeError:
        return _blocked_validation(["envelope_metadata_not_mapping"])
    if not _is_json_safe(envelope):
        return _blocked_validation(["non_json_safe_metadata"])

    reasons: list[str] = []
    if envelope.get("schema_version") != SCHEMA_VERSION:
        reasons.append("missing_or_unsupported_schema_version")
    if envelope.get("access_mode") not in ALLOWED_ACCESS_MODES:
        reasons.append("unsupported_access_mode")
    if envelope.get("content_included") is not False:
        reasons.append("content_included_must_be_false")
    reasons.extend(_collect_marker_reasons({k: v for k, v in envelope.items() if k not in {"blocked_reason_labels"}}))

    denied = envelope.get("denied_authority")
    if not isinstance(denied, Mapping):
        reasons.append("missing_denied_authority")
        denied = {}
    for field in DENIED_AUTHORITY_FIELDS:
        if field not in denied:
            reasons.append(f"missing_denied_authority:{field}")
        elif denied.get(field) is not False:
            reasons.append(f"denied_authority_true:{field}")

    if reasons:
        return _blocked_validation(reasons)
    return {
        "valid": True,
        "validation_status": "valid",
        "blocked_reasons": [],
        "access_mode": envelope.get("access_mode"),
        "content_included": False,
        "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
    }


def summarize_scoped_artifact_upload_registry_v1(envelope_or_request: Mapping[str, Any]) -> dict[str, Any]:
    """Return compact metadata summary without raw artifact/upload content."""

    record = _json_safe_copy(_as_record(envelope_or_request))
    if "authorization_decision" in record:
        return {
            "schema_version": record.get("schema_version"),
            "registry_entry_id": record.get("registry_entry_id"),
            "access_status": record.get("access_status"),
            "access_mode": record.get("access_mode"),
            "content_included": False,
            "redaction_status": record.get("redaction_status"),
            "blocked_reason_labels": record.get("blocked_reason_labels", []),
            "scope_summary": record.get("scope_summary"),
            "provenance_summary": record.get("provenance_summary"),
            "currentness_summary": record.get("currentness_summary"),
            "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
        }
    return {
        "schema_version": record.get("schema_version"),
        "registry_entry_id": record.get("registry_entry_id"),
        "artifact_or_upload_kind": record.get("artifact_or_upload_kind"),
        "access_mode": record.get("access_mode"),
        "requested_use_context": record.get("requested_use_context"),
        "requested_content_mode": record.get("requested_content_mode"),
        "content_included": False,
        "privacy_label": record.get("privacy_label"),
        "provenance_label": record.get("provenance_label"),
        "currentness_label": record.get("currentness_label"),
        "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
    }


def to_scoped_artifact_upload_registry_json_safe_v1(metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Return JSON-safe adapter metadata or raise ValueError."""

    return _json_safe_copy(_as_record(metadata))


def render_scoped_artifact_upload_registry_markdown_v1(envelope_or_request: Mapping[str, Any]) -> str:
    """Render internal-review Markdown for metadata only, never final text."""

    summary = summarize_scoped_artifact_upload_registry_v1(envelope_or_request)
    lines = ["# Scoped Artifact Upload Registry Metadata V1", ""]
    for key in (
        "schema_version",
        "registry_entry_id",
        "artifact_or_upload_kind",
        "access_status",
        "access_mode",
        "requested_use_context",
        "requested_content_mode",
        "redaction_status",
    ):
        value = summary.get(key)
        if value is not None:
            lines.append(f"- `{key}`: `{value}`")
    lines.append("- `content_included`: `false`")
    lines.append("- `metadata_only`: `true`")
    lines.append("- `grants_runtime_authority`: `false`")
    lines.append("- `permits_provider_calls`: `false`")
    lines.append("- `permits_final_answer_generation`: `false`")
    return "\n".join(lines) + "\n"
