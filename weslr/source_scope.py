"""Pure metadata helpers for WESLR source-scope records.

This module is intentionally import-safe and side-effect-free. It does not read
filesystem state, runtime state, authentication state, databases, providers,
network resources, browser requests, memory, evidence, artifacts, uploads,
caches, logs, traces, or `.weslr` state.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Mapping

SCHEMA_VERSION = "weslr.source_scope.v1"

DENIED_AUTHORITY_FIELDS = (
    "grants_runtime_authority",
    "permits_public_browser_runtime",
    "permits_unscoped_memory_reads",
    "permits_cross_user_context",
    "permits_provider_calls",
    "permits_dot_weslr_public_state",
    "permits_final_answer_generation",
    "permits_authentication_decisions",
)

DEFAULT_DENIED_AUTHORITY = {field: False for field in DENIED_AUTHORITY_FIELDS}

SCOPE_FIELDS = (
    "source_scope_id",
    "tenant_id",
    "account_id",
    "user_id",
    "guest_id",
    "session_id",
    "conversation_id",
    "workspace_id",
    "project_id",
    "artifact_id",
    "upload_id",
    "memory_scope_id",
    "evidence_scope_id",
    "cache_scope_id",
    "trace_scope_id",
    "locale",
    "language",
    "source_kind",
    "source_ref",
    "source_owner_kind",
    "allowed_use_contexts",
    "retention_label",
    "privacy_label",
    "currentness_label",
    "provenance_label",
    "validation_status",
    "source_created_at",
    "source_currentness_label",
)

STATEFUL_SOURCE_KINDS = {
    "memory",
    "context",
    "evidence",
    "artifact",
    "upload",
    "cache",
    "log",
    "trace",
    "transcript",
    "profile",
    "timeline",
    "candidate",
}

RESOURCE_SCOPE_REQUIREMENTS = {
    "memory": "memory_scope_id",
    "evidence": "evidence_scope_id",
    "artifact": "artifact_id",
    "upload": "upload_id",
    "cache": "cache_scope_id",
    "trace": "trace_scope_id",
}

UNSAFE_IDENTITY_SOURCES = {
    "query_string",
    "query-string",
    "display_name",
    "profile_claim",
    "browser_local_label",
    "request_parameter",
}

UNSAFE_SCOPE_INFERENCE = {
    "process_global",
    "process-global",
    "thread_local",
    "thread-local",
    "cwd",
    "current_working_directory",
    "active_artifact_pointer",
    "active_upload_pointer",
    "default_timeline",
}

CANDIDATE_FORBIDDEN_FLAGS = (
    "grants_runtime_authority",
    "permits_public_browser_runtime",
    "permits_provider_calls",
    "permits_dot_weslr_public_state",
    "permits_final_answer_generation",
    "runtime_authority",
    "public_browser_runtime",
    "provider_call_allowed",
    "dot_weslr_public_state_allowed",
    "final_answer_generation_allowed",
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
        raise ValueError("source scope contains non-JSON-safe metadata")
    # Round-trip through JSON to avoid carrying custom mapping/list subclasses.
    return json.loads(json.dumps(value, sort_keys=True))


def _as_record(source_scope: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(source_scope, Mapping):
        raise TypeError("source_scope must be a mapping")
    return deepcopy(dict(source_scope))


def _blocked(status: str, reasons: list[str], record: dict[str, Any]) -> dict[str, Any]:
    out = _json_safe_copy(record)
    out["validation_status"] = status
    out["valid"] = False
    out["blocked_reasons"] = sorted(set(reasons))
    out["denied_authority"] = _json_safe_copy(out.get("denied_authority", {}))
    return out


def build_source_scope_v1(
    *,
    source_scope_id: str,
    tenant_id: str | None = None,
    account_id: str | None = None,
    user_id: str | None = None,
    guest_id: str | None = None,
    session_id: str | None = None,
    conversation_id: str | None = None,
    workspace_id: str | None = None,
    project_id: str | None = None,
    artifact_id: str | None = None,
    upload_id: str | None = None,
    memory_scope_id: str | None = None,
    evidence_scope_id: str | None = None,
    cache_scope_id: str | None = None,
    trace_scope_id: str | None = None,
    locale: str | None = None,
    language: str | None = None,
    source_kind: str,
    source_ref: str,
    source_owner_kind: str,
    allowed_use_contexts: list[str] | None = None,
    retention_label: str = "unknown",
    privacy_label: str = "unknown",
    currentness_label: str = "unknown",
    provenance_label: str = "unknown",
    source_created_at: str | None = None,
    source_currentness_label: str | None = None,
    denied_authority: Mapping[str, bool] | None = None,
    **metadata: Any,
) -> dict[str, Any]:
    """Build a metadata-only source-scope record from explicit fields.

    The helper performs no reads and grants no authority. Extra keyword metadata
    is accepted only when JSON-safe so synthetic tests can model negative cases.
    """

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "source_scope_id": source_scope_id,
        "tenant_id": tenant_id,
        "account_id": account_id,
        "user_id": user_id,
        "guest_id": guest_id,
        "session_id": session_id,
        "conversation_id": conversation_id,
        "workspace_id": workspace_id,
        "project_id": project_id,
        "artifact_id": artifact_id,
        "upload_id": upload_id,
        "memory_scope_id": memory_scope_id,
        "evidence_scope_id": evidence_scope_id,
        "cache_scope_id": cache_scope_id,
        "trace_scope_id": trace_scope_id,
        "locale": locale,
        "language": language,
        "source_kind": source_kind,
        "source_ref": source_ref,
        "source_owner_kind": source_owner_kind,
        "allowed_use_contexts": list(allowed_use_contexts or []),
        "retention_label": retention_label,
        "privacy_label": privacy_label,
        "currentness_label": currentness_label,
        "provenance_label": provenance_label,
        "validation_status": "invalid",
        "source_created_at": source_created_at,
        "source_currentness_label": source_currentness_label,
        "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
    }
    if denied_authority is not None:
        record["denied_authority"].update(dict(denied_authority))
    record.update(metadata)
    return _json_safe_copy(record)


def validate_source_scope_v1(
    source_scope: Mapping[str, Any],
    *,
    required_use_context: str | None = None,
    public_browser: bool = False,
    require_conversation: bool = True,
    require_session: bool = True,
) -> dict[str, Any]:
    """Validate scope metadata and fail closed for missing/unsafe scope.

    The return value is validation metadata. It is not read authorization.
    """

    record = _as_record(source_scope)
    reasons: list[str] = []

    if not _is_json_safe(record):
        return _blocked("blocked_unsafe_scope", ["non_json_safe_value"], {"denied_authority": {}})

    if record.get("schema_version") not in (SCHEMA_VERSION, None):
        reasons.append("unsupported_schema_version")
    if record.get("schema_version") is None and record.get("schema") != SCHEMA_VERSION:
        reasons.append("missing_schema_version")

    denied = record.get("denied_authority")
    if not isinstance(denied, Mapping):
        reasons.append("missing_denied_authority")
        denied = {}
    for field in DENIED_AUTHORITY_FIELDS:
        if field not in denied:
            reasons.append(f"missing_denied_authority:{field}")
        elif denied.get(field) is not False:
            reasons.append(f"denied_authority_true:{field}")

    if _is_blank(record.get("tenant_id")):
        reasons.append("missing_tenant_id")
    if require_session and _is_blank(record.get("session_id")):
        reasons.append("missing_session_id")
    if require_conversation and _is_blank(record.get("conversation_id")):
        reasons.append("missing_conversation_id")

    has_account_user = not _is_blank(record.get("account_id")) and not _is_blank(record.get("user_id"))
    has_guest = not _is_blank(record.get("guest_id"))
    if not has_account_user and not has_guest:
        reasons.append("missing_account_user_or_guest_identity")
    if has_guest and (not _is_blank(record.get("account_id")) or not _is_blank(record.get("user_id"))):
        reasons.append("unsafe_guest_authenticated_mix")

    identity_source = record.get("identity_source") or record.get("user_id_source") or record.get("identity_authority")
    if identity_source in UNSAFE_IDENTITY_SOURCES:
        reasons.append("unsafe_identity_source")
    if record.get("query_string_user_id") and not record.get("authenticated_identity_binding"):
        reasons.append("query_string_user_id_not_identity_authority")

    values = [str(value) for value in record.values() if isinstance(value, str)]
    if ".weslr" in values or record.get("uses_global_dot_weslr") or record.get("dot_weslr_public_state"):
        reasons.append("global_dot_weslr_invalid_for_public_scope")
    if "tl_default" in values:
        reasons.append("tl_default_invalid_shared_user_scope")

    scope_inference = record.get("scope_inference") or record.get("inferred_from")
    if scope_inference in UNSAFE_SCOPE_INFERENCE:
        reasons.append("process_global_or_implicit_scope_inference_rejected")

    source_kind = record.get("source_kind")
    if source_kind in RESOURCE_SCOPE_REQUIREMENTS:
        required_field = RESOURCE_SCOPE_REQUIREMENTS[source_kind]
        if _is_blank(record.get(required_field)):
            reasons.append(f"unscoped_{source_kind}")
    if source_kind in STATEFUL_SOURCE_KINDS and _is_blank(record.get("source_scope_id")):
        reasons.append("missing_source_scope_id")

    if record.get("cross_user") or record.get("cross_user_context"):
        if record.get("source_owner_kind") != "anonymized_aggregate" or record.get("contains_raw_private_material"):
            reasons.append("unsafe_cross_user_source_mixing")
    if record.get("anonymous") and record.get("contains_raw_private_material"):
        reasons.append("unsafe_anonymous_raw_private_material")

    if public_browser and record.get("source_owner_kind") == "operator_local":
        reasons.append("operator_local_not_public_browser_scope")
    if public_browser and "public_browser" not in record.get("allowed_use_contexts", []):
        if required_use_context == "public_browser":
            reasons.append("public_browser_use_context_not_allowed")

    if required_use_context and required_use_context not in record.get("allowed_use_contexts", []):
        reasons.append("required_use_context_not_allowed")

    if reasons:
        missing = any(reason.startswith("missing_") for reason in reasons)
        return _blocked("blocked_missing_scope" if missing else "blocked_unsafe_scope", reasons, record)

    out = _json_safe_copy(record)
    out["validation_status"] = "valid"
    out["valid"] = True
    out["blocked_reasons"] = []
    out["denied_authority"] = dict(DEFAULT_DENIED_AUTHORITY)
    return out


def require_source_scope_for_candidate_v1(candidate_metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Require valid source scope before candidate metadata can be considered.

    This does not form a response and does not authorize reads.
    """

    candidate = _as_record(candidate_metadata)
    if not _is_json_safe(candidate):
        return {
            "valid": False,
            "validation_status": "blocked_unsafe_scope",
            "blocked_reasons": ["non_json_safe_candidate_metadata"],
            "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
        }

    reasons: list[str] = []
    for flag in CANDIDATE_FORBIDDEN_FLAGS:
        if candidate.get(flag) is True:
            reasons.append(f"candidate_implies_forbidden_authority:{flag}")

    referenced = candidate.get("referenced_source_kinds", [])
    if isinstance(referenced, str):
        referenced = [referenced]
    if any(kind in STATEFUL_SOURCE_KINDS for kind in referenced) and "source_scope" not in candidate:
        reasons.append("candidate_references_stateful_source_without_scope")

    source_scope = candidate.get("source_scope")
    if not isinstance(source_scope, Mapping):
        reasons.append("missing_source_scope")
        validation = None
    else:
        validation = validate_source_scope_v1(source_scope, required_use_context="candidate_metadata")
        if not validation.get("valid"):
            reasons.extend(validation.get("blocked_reasons", ["invalid_source_scope"]))

    if reasons:
        return {
            "valid": False,
            "validation_status": "blocked_missing_scope" if "missing_source_scope" in reasons else "blocked_unsafe_scope",
            "blocked_reasons": sorted(set(reasons)),
            "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
        }

    return {
        "valid": True,
        "validation_status": "valid",
        "blocked_reasons": [],
        "source_scope_summary": summarize_source_scope_v1(validation or source_scope),
        "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
    }


def summarize_source_scope_v1(source_scope: Mapping[str, Any]) -> dict[str, Any]:
    """Return compact metadata summary without exposing raw source content."""

    record = _json_safe_copy(_as_record(source_scope))
    return {
        "schema_version": record.get("schema_version") or record.get("schema"),
        "source_scope_id": record.get("source_scope_id"),
        "tenant_id": record.get("tenant_id"),
        "account_id": record.get("account_id"),
        "user_id": record.get("user_id"),
        "guest_id": record.get("guest_id"),
        "session_id": record.get("session_id"),
        "conversation_id": record.get("conversation_id"),
        "workspace_id": record.get("workspace_id"),
        "project_id": record.get("project_id"),
        "source_kind": record.get("source_kind"),
        "source_owner_kind": record.get("source_owner_kind"),
        "privacy_label": record.get("privacy_label"),
        "currentness_label": record.get("currentness_label"),
        "provenance_label": record.get("provenance_label"),
        "validation_status": record.get("validation_status"),
        "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
    }


def to_source_scope_json_safe_v1(source_scope: Mapping[str, Any]) -> dict[str, Any]:
    """Return a JSON-safe source-scope metadata record or raise ValueError."""

    return _json_safe_copy(_as_record(source_scope))


def render_source_scope_markdown_v1(source_scope: Mapping[str, Any]) -> str:
    """Render safe internal Markdown for review artifacts only.

    The rendering intentionally omits source_ref so it cannot become a raw-content
    display channel.
    """

    summary = summarize_source_scope_v1(source_scope)
    lines = ["# Source Scope Metadata V1", ""]
    for key in (
        "schema_version",
        "source_scope_id",
        "tenant_id",
        "account_id",
        "user_id",
        "guest_id",
        "session_id",
        "conversation_id",
        "workspace_id",
        "project_id",
        "source_kind",
        "source_owner_kind",
        "privacy_label",
        "currentness_label",
        "provenance_label",
        "validation_status",
    ):
        value = summary.get(key)
        if value is not None:
            lines.append(f"- `{key}`: `{value}`")
    lines.append("- `metadata_only`: `true`")
    lines.append("- `grants_runtime_authority`: `false`")
    lines.append("- `permits_final_answer_generation`: `false`")
    return "\n".join(lines) + "\n"
