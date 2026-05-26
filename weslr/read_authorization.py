"""Pure metadata helpers for WESLR central read authorization.

This module is intentionally import-safe and side-effect-free. It decides read
authorization metadata only. It does not read memory, context, evidence,
artifacts, uploads, caches, logs, traces, filesystems, databases, providers,
network resources, browser/runtime state, authentication state, or `.weslr`
state, and it does not generate final/user-facing answers.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Mapping

from weslr.source_scope import validate_source_scope_v1

SCHEMA_VERSION = "weslr.read_authorization.v1"

DENIED_AUTHORITY_FIELDS = (
    "grants_runtime_authority",
    "permits_public_browser_runtime",
    "permits_unscoped_memory_reads",
    "permits_cross_user_context",
    "permits_provider_calls",
    "permits_dot_weslr_public_state",
    "permits_final_answer_generation",
    "permits_authentication_decisions",
    "permits_database_reads",
    "permits_memory_reads_without_adapter",
)

DEFAULT_DENIED_AUTHORITY = {field: False for field in DENIED_AUTHORITY_FIELDS}

STATEFUL_READ_KINDS = {
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
    "queue",
    "daemon",
    "background_result",
}

ALLOW_METADATA_USE_CONTEXTS = {
    "candidate_metadata",
    "authority_checkpoint",
}

ALLOW_INTERNAL_SHADOW_USE_CONTEXTS = {
    "shadow_validation",
    "safe_assembly_shadow",
    "internal_review",
}

UNSUPPORTED_USE_CONTEXTS = {
    "unknown",
    "public_browser",
}

RUNTIME_AUTHORITY_USE_CONTEXTS = {
    "runtime_chat",
    "chat_runtime",
    "browser_runtime",
}

PROVIDER_AUTHORITY_USE_CONTEXTS = {
    "provider_call",
    "model_call",
    "search_call",
    "advisor_call",
    "external_call",
}

FINAL_ANSWER_USE_CONTEXTS = {
    "final_answer",
    "user_output",
    "reply_text",
    "preview",
}

SAFE_POLICY_LABELS = {
    "synthetic_metadata_only",
    "metadata_only",
    "internal_shadow",
    "reviewed_internal_shadow",
}

UNKNOWN_POLICY_LABELS = {None, "", "unknown", "missing"}

PRIVATE_LABELS = {"user_private", "tenant_private", "operator_private", "raw_private"}

UNTRUSTED_CURRENTNESS_LABELS = {"stale", "unknown"}
UNTRUSTED_PROVENANCE_LABELS = {"inferred", "unknown"}

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

CANDIDATE_FORBIDDEN_FLAGS = (
    *DENIED_AUTHORITY_FIELDS,
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
        raise ValueError("read authorization metadata is not JSON-safe")
    return json.loads(json.dumps(value, sort_keys=True))


def _as_record(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("metadata must be a mapping")
    return deepcopy(dict(value))


def _normalize_denied_authority(denied_authority: Mapping[str, Any] | None) -> dict[str, Any]:
    denied = dict(DEFAULT_DENIED_AUTHORITY)
    if denied_authority is not None:
        denied.update(dict(denied_authority))
    return denied


def _scope_metadata(scope: Mapping[str, Any] | None) -> dict[str, Any]:
    source = dict(scope or {})
    return {key: source.get(key) for key in SCOPE_KEYS}


def _source_scope_summary(source_scope: Mapping[str, Any] | None, validation: Mapping[str, Any] | None = None) -> dict[str, Any]:
    scope = dict(source_scope or {})
    validated = dict(validation or {})
    return {
        "source_scope_id": scope.get("source_scope_id"),
        "source_kind": scope.get("source_kind"),
        "source_owner_kind": scope.get("source_owner_kind"),
        "validation_status": validated.get("validation_status") or scope.get("validation_status"),
        "privacy_label": scope.get("privacy_label"),
        "currentness_label": scope.get("currentness_label"),
        "provenance_label": scope.get("provenance_label"),
        "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
    }


def _make_decision(
    request: Mapping[str, Any],
    decision: str,
    *,
    decision_reason_labels: list[str] | None = None,
    blocked_reason_labels: list[str] | None = None,
    required_followup: list[str] | None = None,
    source_scope_validation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source_scope = request.get("source_scope") if isinstance(request.get("source_scope"), Mapping) else None
    record = {
        "schema_version": SCHEMA_VERSION,
        "authorization_id": request.get("authorization_id"),
        "decision": decision,
        "decision_reason_labels": sorted(set(decision_reason_labels or [])),
        "blocked_reason_labels": sorted(set(blocked_reason_labels or [])),
        "required_followup": sorted(set(required_followup or ["none"])),
        "source_scope_summary": _source_scope_summary(source_scope, source_scope_validation),
        "requested_read_kind": request.get("requested_read_kind"),
        "requested_use_context": request.get("requested_use_context"),
        "owner_scope_match_label": request.get("owner_scope_match_label") or _derive_owner_scope_match_label(request),
        "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
    }
    return _json_safe_copy(record)


def _derive_owner_scope_match_label(request: Mapping[str, Any]) -> str:
    requester = request.get("requester_scope")
    target = request.get("target_scope")
    if not isinstance(requester, Mapping) or not isinstance(target, Mapping):
        return "unknown"
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


def build_read_authorization_request_v1(
    *,
    authorization_id: str,
    source_scope: Mapping[str, Any] | None,
    requested_read_kind: str,
    requested_use_context: str,
    requester_scope: Mapping[str, Any] | None,
    target_scope: Mapping[str, Any] | None,
    public_browser_context: bool = False,
    runtime_context_label: str = "internal_metadata",
    privacy_label: str = "unknown",
    retention_label: str = "unknown",
    provenance_label: str = "unknown",
    currentness_label: str = "unknown",
    policy_label: str = "unknown",
    owner_scope_match_label: str | None = None,
    denied_authority: Mapping[str, Any] | None = None,
    **metadata: Any,
) -> dict[str, Any]:
    """Build a JSON-safe central read authorization request.

    The request is metadata only and is not a capability token.
    """

    request: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "authorization_id": authorization_id,
        "source_scope": _json_safe_copy(dict(source_scope)) if isinstance(source_scope, Mapping) else source_scope,
        "requested_read_kind": requested_read_kind,
        "requested_use_context": requested_use_context,
        "requester_scope": _json_safe_copy(_scope_metadata(requester_scope)),
        "target_scope": _json_safe_copy(_scope_metadata(target_scope)),
        "public_browser_context": bool(public_browser_context),
        "runtime_context_label": runtime_context_label,
        "privacy_label": privacy_label,
        "retention_label": retention_label,
        "provenance_label": provenance_label,
        "currentness_label": currentness_label,
        "policy_label": policy_label,
        "owner_scope_match_label": owner_scope_match_label,
        "denied_authority": _normalize_denied_authority(denied_authority),
    }
    request.update(metadata)
    return _json_safe_copy(request)


def validate_read_authorization_request_v1(request_metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Validate request metadata without authorizing or performing a read."""

    try:
        request = _as_record(request_metadata)
    except TypeError:
        return {
            "valid": False,
            "validation_status": "blocked_unsafe_request",
            "blocked_reasons": ["request_metadata_not_mapping"],
            "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
        }

    if not _is_json_safe(request):
        return {
            "valid": False,
            "validation_status": "blocked_unsafe_request",
            "blocked_reasons": ["non_json_safe_value"],
            "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
        }

    reasons: list[str] = []
    if request.get("schema_version") != SCHEMA_VERSION:
        reasons.append("missing_or_unsupported_schema_version")
    if _is_blank(request.get("authorization_id")):
        reasons.append("missing_authorization_id")
    if _is_blank(request.get("requested_read_kind")):
        reasons.append("missing_requested_read_kind")
    if _is_blank(request.get("requested_use_context")):
        reasons.append("missing_requested_use_context")

    requester = request.get("requester_scope")
    if not isinstance(requester, Mapping) or all(_is_blank(requester.get(key)) for key in SCOPE_KEYS):
        reasons.append("missing_requester_scope")

    target = request.get("target_scope")
    if not isinstance(target, Mapping) or all(_is_blank(target.get(key)) for key in SCOPE_KEYS):
        reasons.append("missing_target_scope")

    denied = request.get("denied_authority")
    if not isinstance(denied, Mapping):
        reasons.append("missing_denied_authority")
        denied = {}
    for field in DENIED_AUTHORITY_FIELDS:
        if field not in denied:
            reasons.append(f"missing_denied_authority:{field}")
        elif denied.get(field) is not False:
            reasons.append(f"denied_authority_true:{field}")

    if request.get("query_string_user_id") or request.get("identity_source") in {"query_string", "query-string"}:
        reasons.append("query_string_user_id_not_identity_authority")

    text_values = [str(value) for value in request.values() if isinstance(value, str)]
    if ".weslr" in text_values or request.get("uses_global_dot_weslr") or request.get("dot_weslr_public_state"):
        reasons.append("global_dot_weslr_invalid_for_authorization")
    if "tl_default" in text_values:
        reasons.append("tl_default_invalid_shared_user_scope")
    if request.get("scope_inference") in {"process_global", "process-global", "thread_local", "thread-local", "default_timeline"}:
        reasons.append("process_global_or_default_timeline_inference_rejected")

    if reasons:
        return {
            "valid": False,
            "validation_status": "blocked_missing_scope" if any(r.startswith("missing_") for r in reasons) else "blocked_unsafe_request",
            "blocked_reasons": sorted(set(reasons)),
            "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
        }

    out = _json_safe_copy(request)
    out["valid"] = True
    out["validation_status"] = "valid"
    out["blocked_reasons"] = []
    out["denied_authority"] = dict(DEFAULT_DENIED_AUTHORITY)
    return out


def authorize_scoped_read_v1(request_metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Return central read authorization decision metadata only."""

    request_validation = validate_read_authorization_request_v1(request_metadata)
    request = _as_record(request_metadata) if isinstance(request_metadata, Mapping) and _is_json_safe(request_metadata) else {}

    if not request_validation.get("valid"):
        blocked = request_validation.get("blocked_reasons", [])
        if any(reason.startswith("missing_denied_authority") or reason.startswith("denied_authority_true") for reason in blocked):
            return _make_decision(request, "deny_runtime_authority", blocked_reason_labels=blocked, required_followup=["request_scope"])
        if "missing_requester_scope" in blocked:
            return _make_decision(request, "deny_missing_requester_scope", blocked_reason_labels=blocked, required_followup=["request_scope"])
        if "missing_target_scope" in blocked:
            return _make_decision(request, "deny_missing_target_scope", blocked_reason_labels=blocked, required_followup=["request_scope"])
        if any("query_string" in reason for reason in blocked):
            return _make_decision(request, "deny_missing_policy", blocked_reason_labels=blocked, required_followup=["request_policy"])
        if any(reason in blocked for reason in ("global_dot_weslr_invalid_for_authorization", "tl_default_invalid_shared_user_scope", "process_global_or_default_timeline_inference_rejected")):
            return _make_decision(request, "deny_missing_policy", blocked_reason_labels=blocked, required_followup=["design_review"])
        return _make_decision(request, "escalate_for_design_review", blocked_reason_labels=blocked, required_followup=["design_review"])

    source_scope = request.get("source_scope")
    if not isinstance(source_scope, Mapping):
        return _make_decision(request, "deny_missing_source_scope", blocked_reason_labels=["missing_source_scope"], required_followup=["request_scope"])

    source_validation = validate_source_scope_v1(
        source_scope,
        required_use_context=request.get("requested_use_context")
        if request.get("requested_use_context") in ALLOW_METADATA_USE_CONTEXTS | ALLOW_INTERNAL_SHADOW_USE_CONTEXTS
        else None,
        public_browser=bool(request.get("public_browser_context")),
    )
    if not source_validation.get("valid"):
        return _make_decision(
            request,
            "deny_invalid_source_scope",
            blocked_reason_labels=source_validation.get("blocked_reasons", ["invalid_source_scope"]),
            required_followup=["request_scope"],
            source_scope_validation=source_validation,
        )

    requested_use = request.get("requested_use_context")
    requested_read = request.get("requested_read_kind")
    privacy = request.get("privacy_label") or source_scope.get("privacy_label")
    provenance = request.get("provenance_label") or source_scope.get("provenance_label")
    currentness = request.get("currentness_label") or source_scope.get("currentness_label")
    policy = request.get("policy_label")
    owner_match = request.get("owner_scope_match_label") or _derive_owner_scope_match_label(request)

    if requested_use in RUNTIME_AUTHORITY_USE_CONTEXTS or request.get("runtime_context_label") in {"runtime_chat", "browser_runtime"}:
        return _make_decision(request, "deny_runtime_authority", blocked_reason_labels=["requested_use_implies_runtime_authority"], required_followup=["design_review"], source_scope_validation=source_validation)
    if requested_use in PROVIDER_AUTHORITY_USE_CONTEXTS:
        return _make_decision(request, "deny_provider_or_external_call", blocked_reason_labels=["requested_use_implies_provider_or_external_call"], required_followup=["design_review"], source_scope_validation=source_validation)
    if requested_use in FINAL_ANSWER_USE_CONTEXTS:
        return _make_decision(request, "deny_final_answer_or_user_output", blocked_reason_labels=["requested_use_implies_final_answer_or_user_output"], required_followup=["design_review"], source_scope_validation=source_validation)
    if requested_use in UNSUPPORTED_USE_CONTEXTS:
        return _make_decision(request, "deny_unsupported_use_context", blocked_reason_labels=["unsupported_use_context"], required_followup=["design_review"], source_scope_validation=source_validation)

    if request.get("public_browser_context") and (privacy in PRIVATE_LABELS or source_scope.get("source_owner_kind") == "operator_local"):
        return _make_decision(request, "deny_public_browser_context", blocked_reason_labels=["public_browser_context_requested_private_or_operator_local_state"], required_followup=["scoped_adapter_required"], source_scope_validation=source_validation)

    if source_scope.get("source_owner_kind") == "anonymized_aggregate" and privacy == "raw_private":
        return _make_decision(request, "deny_private_or_raw_content", blocked_reason_labels=["anonymous_aggregate_carries_raw_private_content"], required_followup=["request_scope"], source_scope_validation=source_validation)

    if owner_match in {"cross_tenant", "cross_user"}:
        decision = "deny_cross_user_or_cross_tenant"
        reason = owner_match
        return _make_decision(request, decision, blocked_reason_labels=[reason], required_followup=["request_policy"], source_scope_validation=source_validation)
    if owner_match in {"guest_to_authenticated", "authenticated_to_guest"}:
        return _make_decision(request, "deny_scope_mismatch", blocked_reason_labels=[owner_match], required_followup=["request_policy"], source_scope_validation=source_validation)
    if owner_match in {"same_user_different_session", "same_user_different_conversation"} and requested_read in STATEFUL_READ_KINDS:
        return _make_decision(request, "deny_scope_mismatch", blocked_reason_labels=[owner_match], required_followup=["request_policy"], source_scope_validation=source_validation)

    if requested_read in STATEFUL_READ_KINDS and (policy in UNKNOWN_POLICY_LABELS or policy not in SAFE_POLICY_LABELS):
        return _make_decision(request, "deny_missing_policy", blocked_reason_labels=["missing_or_unknown_policy_label"], required_followup=["request_policy"], source_scope_validation=source_validation)

    if currentness in UNTRUSTED_CURRENTNESS_LABELS or provenance in UNTRUSTED_PROVENANCE_LABELS:
        return _make_decision(request, "deny_stale_or_untrusted_source", blocked_reason_labels=["stale_or_untrusted_source_metadata"], required_followup=["request_policy"], source_scope_validation=source_validation)

    if requested_use in ALLOW_METADATA_USE_CONTEXTS:
        return _make_decision(request, "allow_metadata_only", decision_reason_labels=["validated_source_scope", "same_scope", "metadata_only"], source_scope_validation=source_validation)
    if requested_use in ALLOW_INTERNAL_SHADOW_USE_CONTEXTS and policy in {"internal_shadow", "reviewed_internal_shadow", "synthetic_metadata_only"}:
        return _make_decision(request, "allow_read_for_internal_shadow_use", decision_reason_labels=["validated_source_scope", "same_scope", "internal_shadow_only"], required_followup=["scoped_adapter_required"], source_scope_validation=source_validation)

    return _make_decision(request, "deny_unsupported_use_context", blocked_reason_labels=["unsupported_use_context"], required_followup=["design_review"], source_scope_validation=source_validation)


def require_read_authorization_for_candidate_v1(candidate_metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Require allow-listed read authorization metadata before candidate use."""

    try:
        candidate = _as_record(candidate_metadata)
    except TypeError:
        return {"valid": False, "validation_status": "blocked_unsafe_candidate", "blocked_reasons": ["candidate_metadata_not_mapping"], "denied_authority": dict(DEFAULT_DENIED_AUTHORITY)}
    if not _is_json_safe(candidate):
        return {"valid": False, "validation_status": "blocked_unsafe_candidate", "blocked_reasons": ["non_json_safe_candidate_metadata"], "denied_authority": dict(DEFAULT_DENIED_AUTHORITY)}

    reasons: list[str] = []
    for flag in CANDIDATE_FORBIDDEN_FLAGS:
        if candidate.get(flag) is True:
            reasons.append(f"candidate_implies_forbidden_authority:{flag}")

    authorization = candidate.get("read_authorization")
    if not isinstance(authorization, Mapping):
        reasons.append("missing_read_authorization")
    else:
        decision = authorization.get("decision")
        if decision not in {"allow_metadata_only", "allow_read_for_internal_shadow_use"}:
            reasons.append("read_authorization_not_allowed")
        denied = authorization.get("denied_authority")
        if not isinstance(denied, Mapping):
            reasons.append("missing_denied_authority")
        else:
            for field in DENIED_AUTHORITY_FIELDS:
                if field not in denied:
                    reasons.append(f"missing_denied_authority:{field}")
                elif denied.get(field) is not False:
                    reasons.append(f"denied_authority_true:{field}")

    if reasons:
        return {
            "valid": False,
            "validation_status": "blocked_missing_authorization" if "missing_read_authorization" in reasons else "blocked_unsafe_authorization",
            "blocked_reasons": sorted(set(reasons)),
            "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
        }

    return {
        "valid": True,
        "validation_status": "valid",
        "blocked_reasons": [],
        "authorization_summary": summarize_read_authorization_v1(authorization),
        "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
    }


def summarize_read_authorization_v1(read_authorization: Mapping[str, Any]) -> dict[str, Any]:
    """Return compact metadata summary without exposing raw source content."""

    record = _json_safe_copy(_as_record(read_authorization))
    return {
        "schema_version": record.get("schema_version"),
        "authorization_id": record.get("authorization_id"),
        "decision": record.get("decision"),
        "requested_read_kind": record.get("requested_read_kind"),
        "requested_use_context": record.get("requested_use_context"),
        "owner_scope_match_label": record.get("owner_scope_match_label"),
        "source_scope_summary": record.get("source_scope_summary"),
        "denied_authority": dict(DEFAULT_DENIED_AUTHORITY),
    }


def to_read_authorization_json_safe_v1(read_authorization: Mapping[str, Any]) -> dict[str, Any]:
    """Return JSON-safe read authorization metadata or raise ValueError."""

    return _json_safe_copy(_as_record(read_authorization))


def render_read_authorization_markdown_v1(read_authorization: Mapping[str, Any]) -> str:
    """Render safe internal Markdown for metadata review only."""

    summary = summarize_read_authorization_v1(read_authorization)
    source_summary = summary.get("source_scope_summary") or {}
    lines = ["# Read Authorization Metadata V1", ""]
    for key in (
        "schema_version",
        "authorization_id",
        "decision",
        "requested_read_kind",
        "requested_use_context",
        "owner_scope_match_label",
    ):
        value = summary.get(key)
        if value is not None:
            lines.append(f"- `{key}`: `{value}`")
    for key in ("source_scope_id", "source_kind", "source_owner_kind", "validation_status"):
        value = source_summary.get(key)
        if value is not None:
            lines.append(f"- `source_{key}`: `{value}`")
    lines.append("- `metadata_only`: `true`")
    lines.append("- `grants_runtime_authority`: `false`")
    lines.append("- `permits_provider_calls`: `false`")
    lines.append("- `permits_final_answer_generation`: `false`")
    return "\n".join(lines) + "\n"
