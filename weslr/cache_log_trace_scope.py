"""Pure metadata helpers for WESLR cache/log/trace scoping.

This module is intentionally import-safe and side-effect-free. It validates and
summarizes explicit diagnostic metadata only. It never reads cache values, log
text, trace payloads, transcripts, filesystems, databases, provider outputs,
browser/runtime/session/auth state, or `.weslr` state, and it never generates
final/user-facing answers.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Mapping

from weslr.read_authorization import (
    authorize_scoped_read_v1,
    build_read_authorization_request_v1,
)
from weslr.source_scope import validate_source_scope_v1

SCHEMA_VERSION = "weslr.cache_log_trace_scope.v1"

SURFACE_KINDS = {
    "cache_entry",
    "log",
    "trace",
    "diagnostic",
    "runtime_transcript",
    "provider_trace",
    "tool_trace",
    "evaluation_trace",
    "audit_trace",
    "error_report",
    "telemetry_summary",
}

ALLOWED_ACCESS_MODES = {
    "metadata_only_preview",
    "redacted_diagnostic_summary",
    "aggregate_count_summary",
    "provenance_summary_metadata",
    "blocked_no_access",
}

FORBIDDEN_ACCESS_MODES = {
    "raw_log_text",
    "raw_trace_payload",
    "raw_cache_value",
    "runtime_transcript_dump",
    "provider_trace_dump",
    "tool_trace_dump",
    "cross_user_trace_access",
    "global_log_scan",
    "dot_weslr_trace_state",
    "final_answer_trace_injection",
    "unrestricted_diagnostic_dump",
}

DENIED_AUTHORITY_FIELDS = (
    "grants_runtime_authority",
    "permits_public_browser_runtime",
    "permits_provider_calls",
    "permits_dot_weslr_public_state",
    "permits_final_answer_generation",
    "permits_unscoped_diagnostic_reads",
    "permits_cross_user_diagnostic_access",
    "permits_raw_log_text",
    "permits_raw_trace_payload",
    "permits_raw_cache_value",
    "permits_database_reads",
    "permits_authentication_decisions",
    "permits_filesystem_scanning",
    "permits_telemetry_ingestion",
)

DEFAULT_DENIED_AUTHORITY = {field: False for field in DENIED_AUTHORITY_FIELDS}

CONTENT_FLAG_FIELDS = (
    "content_included",
    "raw_trace_included",
    "raw_log_included",
    "raw_cache_value_included",
)

RAW_CONTENT_FIELDS = {
    "raw_log_text",
    "raw_trace_payload",
    "raw_cache_value",
    "runtime_transcript_dump",
    "provider_trace_dump",
    "tool_trace_dump",
    "transcript_text",
    "trace_payload",
    "log_text",
    "cache_value",
    "content",
    "raw_content",
}

PRIVATE_LABELS = {"user_private", "tenant_private", "operator_private", "raw_private"}
TRUTH_AUTHORITY_MARKERS = {"truth", "truth_authority", "source_of_truth", "answer_truth"}
UNTRUSTED_CURRENTNESS_LABELS = {"stale", "unknown"}
UNTRUSTED_PROVENANCE_LABELS = {"untrusted", "unknown", "inferred"}
FINAL_RUNTIME_PROVIDER_MARKERS = {
    "final_answer",
    "user_output",
    "reply_text",
    "runtime_chat",
    "chat_runtime",
    "browser_runtime",
    "provider_call",
    "model_call",
    "search_call",
    "advisor_call",
}
UNSAFE_MARKER_VALUES = {
    ".weslr",
    "tl_default",
    "global",
    "process_global",
    "process-global",
    "default_timeline",
    "default timeline",
}

READ_KIND_BY_SURFACE = {
    "cache_entry": "cache",
    "log": "log",
    "trace": "trace",
    "diagnostic": "trace",
    "runtime_transcript": "transcript",
    "provider_trace": "trace",
    "tool_trace": "trace",
    "evaluation_trace": "trace",
    "audit_trace": "trace",
    "error_report": "log",
    "telemetry_summary": "trace",
}

USE_CONTEXT_BY_ACCESS_MODE = {
    "metadata_only_preview": "candidate_metadata",
    "redacted_diagnostic_summary": "candidate_metadata",
    "aggregate_count_summary": "candidate_metadata",
    "provenance_summary_metadata": "authority_checkpoint",
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
        raise ValueError("cache/log/trace scope metadata is not JSON-safe")
    return json.loads(json.dumps(value, sort_keys=True))


def _as_record(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("cache/log/trace scope metadata must be a mapping")
    return deepcopy(dict(value))


def _scope_metadata(scope: Mapping[str, Any] | None) -> dict[str, Any]:
    source = dict(scope or {})
    return {key: source.get(key) for key in SCOPE_KEYS}


def _scope_missing(scope: Any) -> bool:
    return not isinstance(scope, Mapping) or all(_is_blank(scope.get(key)) for key in SCOPE_KEYS)


def _derive_scope_match_label(requester: Mapping[str, Any], target: Mapping[str, Any]) -> str:
    if requester.get("tenant_id") != target.get("tenant_id"):
        return "cross_tenant"
    if requester.get("account_id") and target.get("account_id") and requester.get("account_id") != target.get("account_id"):
        return "cross_user"
    if requester.get("user_id") and target.get("user_id") and requester.get("user_id") != target.get("user_id"):
        return "cross_user"
    if requester.get("guest_id") and (target.get("account_id") or target.get("user_id")):
        return "guest_to_authenticated"
    if (requester.get("account_id") or requester.get("user_id")) and target.get("guest_id"):
        return "authenticated_to_guest"
    if requester.get("session_id") and target.get("session_id") and requester.get("session_id") != target.get("session_id"):
        return "same_user_different_session"
    if requester.get("conversation_id") and target.get("conversation_id") and requester.get("conversation_id") != target.get("conversation_id"):
        return "same_user_different_conversation"
    return "same_scope"


def _iter_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key)
            yield from _iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)


def _marker_reasons(record: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    strings = list(_iter_strings(record))
    lowered = {item.lower() for item in strings}
    if ".weslr" in lowered or record.get("uses_global_dot_weslr"):
        reasons.append("global_dot_weslr_marker_rejected")
    if "tl_default" in lowered:
        reasons.append("tl_default_invalid_shared_scope")
    if lowered & {"global", "process_global", "process-global", "default_timeline", "default timeline"}:
        reasons.append("global_or_process_default_timeline_marker_rejected")
    if record.get("identity_source") in {"query_string", "query-string"} or record.get("query_string_user_id"):
        reasons.append("query_string_identity_not_authority")
    if any(marker in lowered for marker in TRUTH_AUTHORITY_MARKERS) or record.get("requested_as_truth") is True:
        reasons.append("cache_log_trace_not_truth_authority")
    if record.get("diagnostic_as_truth") is True:
        reasons.append("diagnostic_metadata_not_truth_authority")
    if any(marker in lowered for marker in FINAL_RUNTIME_PROVIDER_MARKERS):
        reasons.append("final_runtime_provider_search_authority_rejected")
    return reasons


def _blocked(record: Mapping[str, Any], reasons: list[str], *, status: str = "blocked_no_access") -> dict[str, Any]:
    out = _json_safe_copy(dict(record)) if _is_json_safe(record) else {"schema_version": SCHEMA_VERSION}
    out["valid"] = False
    out["validation_status"] = status
    out["access_mode"] = "blocked_no_access"
    out["blocked_reasons"] = sorted(set(reasons))
    out["denied_authority"] = dict(DEFAULT_DENIED_AUTHORITY)
    for field in CONTENT_FLAG_FIELDS:
        out[field] = False
    return out


def build_cache_log_trace_scope_record_v1(
    *,
    record_id: str,
    surface_kind: str,
    source_scope: Mapping[str, Any] | None,
    owner_scope: Mapping[str, Any] | None,
    requester_scope: Mapping[str, Any] | None,
    target_scope: Mapping[str, Any] | None,
    access_mode: str = "metadata_only_preview",
    read_authorization: Mapping[str, Any] | None = None,
    retention_label: str = "unknown",
    privacy_label: str = "unknown",
    provenance_label: str = "unknown",
    currentness_label: str = "unknown",
    redaction_status: str = "redacted_metadata_only",
    policy_label: str = "synthetic_metadata_only",
    authorized_use_contexts: list[str] | None = None,
    public_browser_context: bool = False,
    content_included: bool = False,
    raw_trace_included: bool = False,
    raw_log_included: bool = False,
    raw_cache_value_included: bool = False,
    denied_authority: Mapping[str, Any] | None = None,
    **metadata: Any,
) -> dict[str, Any]:
    """Build an explicit metadata-only cache/log/trace scope record."""

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_id": record_id,
        "surface_kind": surface_kind,
        "source_scope": _json_safe_copy(dict(source_scope)) if isinstance(source_scope, Mapping) else source_scope,
        "owner_scope": _json_safe_copy(_scope_metadata(owner_scope)),
        "requester_scope": _json_safe_copy(_scope_metadata(requester_scope)),
        "target_scope": _json_safe_copy(_scope_metadata(target_scope)),
        "access_mode": access_mode,
        "read_authorization": _json_safe_copy(dict(read_authorization)) if isinstance(read_authorization, Mapping) else read_authorization,
        "retention_label": retention_label,
        "privacy_label": privacy_label,
        "provenance_label": provenance_label,
        "currentness_label": currentness_label,
        "redaction_status": redaction_status,
        "content_included": bool(content_included),
        "raw_trace_included": bool(raw_trace_included),
        "raw_log_included": bool(raw_log_included),
        "raw_cache_value_included": bool(raw_cache_value_included),
        "policy_label": policy_label,
        "authorized_use_contexts": list(authorized_use_contexts or ["candidate_metadata"]),
        "public_browser_context": bool(public_browser_context),
        "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
    }
    if denied_authority is not None:
        record["denied_authority"].update(dict(denied_authority))
    record.update(metadata)
    return _json_safe_copy(record)


def validate_cache_log_trace_scope_record_v1(scope_record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate diagnostic surface scope metadata and fail closed."""

    try:
        record = _as_record(scope_record)
    except TypeError:
        return _blocked({"schema_version": SCHEMA_VERSION}, ["record_metadata_not_mapping"], status="blocked_unsafe_metadata")

    if not _is_json_safe(record):
        return _blocked({"schema_version": SCHEMA_VERSION}, ["non_json_safe_metadata"], status="blocked_unsafe_metadata")

    reasons: list[str] = []
    if record.get("schema_version") != SCHEMA_VERSION:
        reasons.append("missing_or_unsupported_schema_version")
    if _is_blank(record.get("record_id")):
        reasons.append("missing_record_id")
    if record.get("surface_kind") not in SURFACE_KINDS:
        reasons.append("unsupported_surface_kind")

    access_mode = record.get("access_mode")
    if access_mode in FORBIDDEN_ACCESS_MODES:
        reasons.append(f"forbidden_access_mode:{access_mode}")
    elif access_mode not in ALLOWED_ACCESS_MODES:
        reasons.append("unsupported_access_mode")

    source_scope = record.get("source_scope")
    if not isinstance(source_scope, Mapping):
        reasons.append("missing_source_scope")
        source_validation = None
    else:
        source_validation = validate_source_scope_v1(
            source_scope,
            required_use_context="candidate_metadata",
            public_browser=bool(record.get("public_browser_context")),
        )
        if not source_validation.get("valid"):
            reasons.extend(f"source_scope:{reason}" for reason in source_validation.get("blocked_reasons", ["invalid_source_scope"]))

    for name in ("owner_scope", "requester_scope", "target_scope"):
        if _scope_missing(record.get(name)):
            reasons.append(f"missing_{name}")

    if isinstance(record.get("requester_scope"), Mapping) and isinstance(record.get("target_scope"), Mapping):
        match = _derive_scope_match_label(record["requester_scope"], record["target_scope"])
        if match in {"cross_tenant", "cross_user", "guest_to_authenticated", "authenticated_to_guest", "same_user_different_session", "same_user_different_conversation"}:
            reasons.append(match)

    if isinstance(record.get("owner_scope"), Mapping) and isinstance(record.get("target_scope"), Mapping):
        owner_match = _derive_scope_match_label(record["owner_scope"], record["target_scope"])
        if owner_match in {"cross_tenant", "cross_user"}:
            reasons.append(f"owner_target_{owner_match}")

    if record.get("public_browser_context") and (
        record.get("privacy_label") in PRIVATE_LABELS
        or (isinstance(source_scope, Mapping) and source_scope.get("source_owner_kind") == "operator_local")
        or record.get("surface_kind") in {"runtime_transcript", "provider_trace", "tool_trace"}
    ):
        reasons.append("public_browser_context_requested_private_or_operator_local_trace")

    for field in CONTENT_FLAG_FIELDS:
        if record.get(field) is not False:
            reasons.append(f"content_flag_true:{field}")
    for field in RAW_CONTENT_FIELDS:
        if field in record and record.get(field) not in (None, "", False):
            reasons.append(f"raw_content_field_present:{field}")

    denied = record.get("denied_authority")
    if not isinstance(denied, Mapping):
        reasons.append("missing_denied_authority")
        denied = {}
    for field in DENIED_AUTHORITY_FIELDS:
        if field not in denied:
            reasons.append(f"missing_denied_authority:{field}")
        elif denied.get(field) is not False:
            reasons.append(f"denied_authority_true:{field}")

    reasons.extend(_marker_reasons(record))

    if record.get("requested_as_truth") is True and (
        record.get("currentness_label") in UNTRUSTED_CURRENTNESS_LABELS
        or record.get("provenance_label") in UNTRUSTED_PROVENANCE_LABELS
    ):
        reasons.append("stale_or_untrusted_diagnostic_requested_as_truth")

    read_authorization = record.get("read_authorization")
    if access_mode != "blocked_no_access":
        if not isinstance(read_authorization, Mapping):
            reasons.append("missing_read_authorization")
        elif read_authorization.get("decision") not in {"allow_metadata_only", "allow_read_for_internal_shadow_use"}:
            reasons.append("read_authorization_denied")

    if reasons:
        return _blocked(record, reasons)

    out = _json_safe_copy(record)
    out["valid"] = True
    out["validation_status"] = "valid" if access_mode != "blocked_no_access" else "blocked_no_access"
    out["blocked_reasons"] = []
    out["source_scope_validation"] = source_validation if source_validation is not None else None
    out["denied_authority"] = dict(DEFAULT_DENIED_AUTHORITY)
    for field in CONTENT_FLAG_FIELDS:
        out[field] = False
    return out


def authorize_cache_log_trace_access_v1(scope_record: Mapping[str, Any]) -> dict[str, Any]:
    """Authorize metadata-only diagnostic access using central read authorization."""

    validation = validate_cache_log_trace_scope_record_v1(scope_record)
    if not validation.get("valid") or validation.get("access_mode") == "blocked_no_access":
        return {
            "schema_version": SCHEMA_VERSION,
            "record_id": validation.get("record_id"),
            "decision": "blocked_no_access",
            "access_mode": "blocked_no_access",
            "blocked_reasons": validation.get("blocked_reasons", []),
            "required_followup": ["request_scope_or_policy"],
            "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
        }

    requested_read_kind = READ_KIND_BY_SURFACE.get(validation.get("surface_kind"), "trace")
    requested_use_context = USE_CONTEXT_BY_ACCESS_MODE.get(validation.get("access_mode"), "candidate_metadata")
    request = build_read_authorization_request_v1(
        authorization_id=f"cache_log_trace_auth:{validation.get('record_id')}",
        source_scope=validation.get("source_scope"),
        requested_read_kind=requested_read_kind,
        requested_use_context=requested_use_context,
        requester_scope=validation.get("requester_scope"),
        target_scope=validation.get("target_scope"),
        public_browser_context=bool(validation.get("public_browser_context")),
        runtime_context_label="internal_metadata",
        privacy_label=validation.get("privacy_label"),
        retention_label=validation.get("retention_label"),
        provenance_label=validation.get("provenance_label"),
        currentness_label=validation.get("currentness_label"),
        policy_label=validation.get("policy_label"),
    )
    decision = authorize_scoped_read_v1(request)
    allowed = decision.get("decision") in {"allow_metadata_only", "allow_read_for_internal_shadow_use"}
    return {
        "schema_version": SCHEMA_VERSION,
        "record_id": validation.get("record_id"),
        "decision": "allow_metadata_only" if allowed else "blocked_no_access",
        "central_read_authorization_decision": decision.get("decision"),
        "access_mode": validation.get("access_mode") if allowed else "blocked_no_access",
        "blocked_reasons": [] if allowed else decision.get("blocked_reason_labels", ["read_authorization_denied"]),
        "required_followup": decision.get("required_followup", ["none"]),
        "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
    }


def summarize_cache_log_trace_scope_v1(scope_record: Mapping[str, Any]) -> dict[str, Any]:
    """Return compact metadata summary without raw diagnostic content."""

    record = _json_safe_copy(_as_record(scope_record))
    source_scope = record.get("source_scope") if isinstance(record.get("source_scope"), Mapping) else {}
    return {
        "schema_version": record.get("schema_version"),
        "record_id": record.get("record_id"),
        "surface_kind": record.get("surface_kind"),
        "access_mode": record.get("access_mode"),
        "validation_status": record.get("validation_status"),
        "privacy_label": record.get("privacy_label"),
        "provenance_label": record.get("provenance_label"),
        "currentness_label": record.get("currentness_label"),
        "redaction_status": record.get("redaction_status"),
        "source_scope_id": source_scope.get("source_scope_id"),
        "source_kind": source_scope.get("source_kind"),
        "content_included": False,
        "raw_trace_included": False,
        "raw_log_included": False,
        "raw_cache_value_included": False,
        "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
    }


def build_cache_log_trace_access_envelope_v1(scope_record: Mapping[str, Any]) -> dict[str, Any]:
    """Build a metadata-only access envelope with no raw content."""

    validation = validate_cache_log_trace_scope_record_v1(scope_record)
    authorization = authorize_cache_log_trace_access_v1(scope_record)
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "envelope_kind": "cache_log_trace_access_metadata_v1",
        "record_summary": summarize_cache_log_trace_scope_v1(validation),
        "access_decision": authorization,
        "content_included": False,
        "raw_trace_included": False,
        "raw_log_included": False,
        "raw_cache_value_included": False,
        "raw_transcript_included": False,
        "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
    }
    return _json_safe_copy(envelope)


def validate_cache_log_trace_access_envelope_v1(envelope_metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a cache/log/trace access envelope remains metadata-only."""

    try:
        envelope = _as_record(envelope_metadata)
    except TypeError:
        return _blocked({"schema_version": SCHEMA_VERSION}, ["envelope_metadata_not_mapping"], status="blocked_unsafe_metadata")
    if not _is_json_safe(envelope):
        return _blocked({"schema_version": SCHEMA_VERSION}, ["non_json_safe_metadata"], status="blocked_unsafe_metadata")

    reasons: list[str] = []
    if envelope.get("schema_version") != SCHEMA_VERSION:
        reasons.append("missing_or_unsupported_schema_version")
    if envelope.get("envelope_kind") != "cache_log_trace_access_metadata_v1":
        reasons.append("unsupported_envelope_kind")
    for field in (*CONTENT_FLAG_FIELDS, "raw_transcript_included"):
        if envelope.get(field) is not False:
            reasons.append(f"content_flag_true:{field}")
    for field in RAW_CONTENT_FIELDS:
        if field in envelope and envelope.get(field) not in (None, "", False):
            reasons.append(f"raw_content_field_present:{field}")
    denied = envelope.get("denied_authority")
    if not isinstance(denied, Mapping):
        reasons.append("missing_denied_authority")
    else:
        for field in DENIED_AUTHORITY_FIELDS:
            if field not in denied:
                reasons.append(f"missing_denied_authority:{field}")
            elif denied.get(field) is not False:
                reasons.append(f"denied_authority_true:{field}")
    reasons.extend(_marker_reasons(envelope))

    if reasons:
        return _blocked(envelope, reasons)

    out = _json_safe_copy(envelope)
    out["valid"] = True
    out["validation_status"] = "valid"
    out["blocked_reasons"] = []
    out["denied_authority"] = dict(DEFAULT_DENIED_AUTHORITY)
    return out


def to_cache_log_trace_scope_json_safe_v1(scope_metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Return JSON-safe cache/log/trace scope metadata or raise ValueError."""

    return _json_safe_copy(_as_record(scope_metadata))


def render_cache_log_trace_scope_markdown_v1(scope_metadata: Mapping[str, Any]) -> str:
    """Render safe internal Markdown for metadata review only."""

    summary = summarize_cache_log_trace_scope_v1(scope_metadata)
    lines = ["# Cache Log Trace Scope Metadata V1", ""]
    for key in (
        "schema_version",
        "record_id",
        "surface_kind",
        "access_mode",
        "validation_status",
        "privacy_label",
        "provenance_label",
        "currentness_label",
        "redaction_status",
        "source_scope_id",
        "source_kind",
    ):
        value = summary.get(key)
        if value is not None:
            lines.append(f"- `{key}`: `{value}`")
    lines.append("- `metadata_only`: `true`")
    lines.append("- `content_included`: `false`")
    lines.append("- `raw_trace_included`: `false`")
    lines.append("- `raw_log_included`: `false`")
    lines.append("- `raw_cache_value_included`: `false`")
    lines.append("- `grants_runtime_authority`: `false`")
    lines.append("- `permits_provider_calls`: `false`")
    lines.append("- `permits_final_answer_generation`: `false`")
    return "\n".join(lines) + "\n"
