"""Metadata-only memory state helpers v1."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "memory_state_model_v1"
PACKET_TYPE_V1 = "memory_state_model_packet_v1"

_ALLOWED_STATUSES_V1 = (
    "absent",
    "proposed",
    "provisional",
    "confirmed",
    "stale",
    "contradicted",
    "invalidated",
    "archived_deprecated",
    "blocked",
    "pending_approval",
    "failed",
)

_ALLOWED_TYPES_V1 = (
    "preference",
    "project_context",
    "user_correction",
    "constraint",
    "decision",
    "artifact_reference",
    "support_context",
    "operator_note",
    "candidate_learning_pattern",
    "blocked_memory",
)

_ALLOWED_SCOPES_V1 = (
    "session_only",
    "project_scoped",
    "user_scoped",
    "tenant_account_scoped",
    "operator_scoped",
    "system_wide_candidate",
    "system_wide_approved",
)

_DENIED_AUTHORITY_FIELDS_V1 = (
    "runtime_wiring_authority",
    "chat_" "responder_authority",
    "storage_database_authority",
    "weslr_io_authority",
    "memory_persistence_authority",
    "memory_mutation_authority",
    "project_state_mutation_authority",
    "external_action_authority",
    "cross_user_leakage_authority",
    "hidden_memory_authority",
    "hidden_personalization_authority",
    "perfect_memory_claim_authority",
    "behavior_update_authority",
    "public_product_readiness_authority",
)

_CORE_ITEM_FIELDS_V1 = (
    "schema_version",
    "memory_id",
    "memory_type",
    "scope",
    "owner_user_scope",
    "tenant_account_scope",
    "project_id",
    "session_id",
    "status",
    "source_type",
    "source_ref",
    "evidence_count",
    "confidence_level",
    "visibility",
    "correction_path",
    "export_relevance",
    "deletion_relevance",
    "revocation_relevance",
    "stale",
    "contradicted",
    "invalidated",
    "pending_approval",
    "blocked_reason",
    "user_visible_summary",
    "operator_visible_summary",
    "audit_note",
    "created_marker",
    "updated_marker",
    "denied_authority",
)

_CORE_PACKET_FIELDS_V1 = (
    "schema_version",
    "packet_id",
    "packet_type",
    "owner_user_scope",
    "tenant_account_scope",
    "active_project_id",
    "active_session_id",
    "items",
    "counts",
    "visible_memory_summary",
    "pending_approvals",
    "blocked_items",
    "stale_items",
    "contradicted_items",
    "invalidated_items",
    "candidate_learning_patterns",
    "operator_visible_items",
    "export_relevant_items",
    "deletion_relevant_items",
    "revocation_relevant_items",
    "limitations",
    "denied_authority",
)

_PRIVATE_MARKERS = (
    "private",
    "secret",
    "password",
    "token",
    "confidential",
    "raw dump",
    "raw_private",
    "ssn",
    "email:",
    "@",
)


def _compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        text = " ".join(value.split())
        return text if text else default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return _compact_text(str(value), default=default)


def _has_text(value: Any) -> bool:
    return bool(_compact_text(value, default=""))


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return copy.deepcopy(value)
    if isinstance(value, tuple):
        return list(copy.deepcopy(value))
    if isinstance(value, set):
        return sorted(copy.deepcopy(value), key=repr)
    return [copy.deepcopy(value)]


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return repr(value)


def _stable_marker(prefix: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def _normalize_denied_authority(value: Any = None) -> dict[str, Any]:
    denied = {field: False for field in _DENIED_AUTHORITY_FIELDS_V1}
    if isinstance(value, Mapping):
        for field in _DENIED_AUTHORITY_FIELDS_V1:
            if field in value:
                denied[field] = False
    return denied


def _build_denied_authority() -> dict[str, Any]:
    return _normalize_denied_authority()


def _default_status_for_type(memory_type: str, scope: str) -> str:
    if memory_type == "candidate_learning_pattern":
        return "proposed"
    if memory_type == "blocked_memory":
        return "blocked"
    if scope == "system_wide_candidate":
        return "proposed"
    if scope == "system_wide_approved":
        return "confirmed"
    if memory_type in {"operator_note", "support_context", "artifact_reference"}:
        return "provisional"
    return "confirmed"


def _default_visibility_for_scope(scope: str) -> str:
    return scope if scope in _ALLOWED_SCOPES_V1 else "session_only"


def _default_summary_for_item(memory_type: str, status: str) -> str:
    return f"memory state {memory_type} ({status})"


def _risk_from_status(status: str) -> str:
    if status in {"confirmed"}:
        return "active"
    if status in {"proposed", "provisional", "stale", "pending_approval"}:
        return "review_required"
    if status in {"absent", "blocked", "contradicted", "invalidated", "archived_deprecated", "failed"}:
        return "blocked"
    return "blocked"


def _is_cross_user_like(*values: Any) -> bool:
    text = " ".join(_compact_text(value, default="").lower() for value in values)
    markers = ("shared", "global", "cross-user", "cross user", "tenant-wide", "account-wide", "workspace-wide", "org-wide", "system-wide")
    return any(marker in text for marker in markers)


def _looks_private_like(*values: Any) -> bool:
    text = " ".join(_compact_text(value, default="").lower() for value in values)
    return any(marker in text for marker in _PRIVATE_MARKERS)


def _redact_private_text(value: Any, default: str = "") -> str:
    text = _compact_text(value, default=default)
    if not text:
        return default
    if _looks_private_like(text):
        return "redacted_content"
    return text


def allowed_memory_state_statuses_v1() -> tuple[str, ...]:
    return _ALLOWED_STATUSES_V1


def allowed_memory_state_types_v1() -> tuple[str, ...]:
    return _ALLOWED_TYPES_V1


def allowed_memory_state_scopes_v1() -> tuple[str, ...]:
    return _ALLOWED_SCOPES_V1


def build_memory_state_item_v1(
    *,
    memory_id: Any = None,
    memory_type: Any = "project_context",
    scope: Any = "project_scoped",
    owner_user_scope: Any = "",
    tenant_account_scope: Any = "",
    project_id: Any = "",
    session_id: Any = "",
    status: Any = None,
    source_type: Any = "synthetic",
    source_ref: Any = None,
    evidence_count: Any = 0,
    confidence_level: Any = "",
    visibility: Any = None,
    correction_path: Any = "review_or_refresh",
    export_relevance: Any = False,
    deletion_relevance: Any = False,
    revocation_relevance: Any = False,
    stale: Any = False,
    contradicted: Any = False,
    invalidated: Any = False,
    pending_approval: Any = False,
    blocked_reason: Any = "",
    user_visible_summary: Any = None,
    operator_visible_summary: Any = None,
    audit_note: Any = "",
    created_marker: Any = None,
    updated_marker: Any = None,
    denied_authority: Any = None,
) -> dict[str, Any]:
    memory_id_text = _compact_text(memory_id)
    memory_type_text = _compact_text(memory_type, default="project_context")
    scope_text = _compact_text(scope, default="project_scoped")
    owner_text = _compact_text(owner_user_scope)
    tenant_text = _compact_text(tenant_account_scope)
    project_text = _compact_text(project_id)
    session_text = _compact_text(session_id)
    status_text = _compact_text(status) or _default_status_for_type(memory_type_text, scope_text)
    source_type_text = _compact_text(source_type, default="synthetic")
    source_ref_text = _redact_private_text(source_ref)
    confidence_text = _compact_text(confidence_level) or ("reviewed" if status_text == "confirmed" else "uncertain")
    visibility_text = _compact_text(visibility) or _default_visibility_for_scope(scope_text)
    correction_path_text = _compact_text(correction_path, default="review_or_refresh")
    blocked_reason_text = _redact_private_text(blocked_reason)
    user_summary_text = _redact_private_text(user_visible_summary) or _default_summary_for_item(memory_type_text, status_text)
    operator_summary_text = _redact_private_text(operator_visible_summary)
    audit_note_text = _redact_private_text(audit_note)
    created_marker_text = _compact_text(created_marker)
    updated_marker_text = _compact_text(updated_marker)
    evidence_count_int = _safe_int(evidence_count, default=0)
    seed = {
        "memory_id": memory_id_text,
        "memory_type": memory_type_text,
        "scope": scope_text,
        "owner_user_scope": owner_text,
        "tenant_account_scope": tenant_text,
        "project_id": project_text,
        "session_id": session_text,
        "status": status_text,
        "source_ref": source_ref_text,
    }
    item = {
        "schema_version": SCHEMA_VERSION_V1,
        "memory_id": memory_id_text or _stable_marker("memory", seed),
        "memory_type": memory_type_text,
        "scope": scope_text,
        "owner_user_scope": owner_text,
        "tenant_account_scope": tenant_text,
        "project_id": project_text,
        "session_id": session_text,
        "status": status_text,
        "source_type": source_type_text,
        "source_ref": source_ref_text or _stable_marker("memory_source", seed),
        "evidence_count": max(0, evidence_count_int),
        "confidence_level": confidence_text,
        "visibility": visibility_text,
        "correction_path": correction_path_text,
        "export_relevance": bool(export_relevance),
        "deletion_relevance": bool(deletion_relevance),
        "revocation_relevance": bool(revocation_relevance),
        "stale": bool(stale),
        "contradicted": bool(contradicted),
        "invalidated": bool(invalidated),
        "pending_approval": bool(pending_approval),
        "blocked_reason": blocked_reason_text,
        "user_visible_summary": user_summary_text,
        "operator_visible_summary": operator_summary_text,
        "audit_note": audit_note_text,
        "created_marker": created_marker_text or _stable_marker("created", seed),
        "updated_marker": updated_marker_text or _stable_marker("updated", {**seed, "created_marker": created_marker_text}),
        "denied_authority": _build_denied_authority() if denied_authority is None else _normalize_denied_authority(denied_authority),
    }
    return _json_safe(item)


def _item_has_text(item: Mapping[str, Any], field: str) -> bool:
    return field in item and _has_text(item.get(field))


def validate_memory_state_item_v1(item: Any) -> dict[str, Any]:
    violations: list[str] = []
    if not isinstance(item, Mapping):
        violations.append("item must be a mapping")
        return {"valid": False, "violation_count": len(violations), "violations": violations, "classification": {"status": "unknown", "type": "unknown", "scope": "unknown", "risk": "blocked"}}

    item = _json_safe(copy.deepcopy(item))

    for field in _CORE_ITEM_FIELDS_V1:
        if field not in item:
            violations.append(f"missing field: {field}")

    if not _item_has_text(item, "schema_version"):
        violations.append("schema_version missing or blank")
    elif _compact_text(item.get("schema_version")) != SCHEMA_VERSION_V1:
        violations.append("schema_version mismatch")

    memory_id = _compact_text(item.get("memory_id"))
    memory_type = _compact_text(item.get("memory_type"))
    scope = _compact_text(item.get("scope"))
    owner = _compact_text(item.get("owner_user_scope"))
    tenant = _compact_text(item.get("tenant_account_scope"))
    project_id = _compact_text(item.get("project_id"))
    session_id = _compact_text(item.get("session_id"))
    status = _compact_text(item.get("status"))
    source_type = _compact_text(item.get("source_type"))
    source_ref = _compact_text(item.get("source_ref"))
    visibility = _compact_text(item.get("visibility"))
    correction_path = _compact_text(item.get("correction_path"))
    blocked_reason = _compact_text(item.get("blocked_reason"))
    user_visible_summary = _compact_text(item.get("user_visible_summary"))
    operator_visible_summary = _compact_text(item.get("operator_visible_summary"))
    audit_note = _compact_text(item.get("audit_note"))
    confidence_level = _compact_text(item.get("confidence_level"))

    if not _has_text(memory_id):
        violations.append("memory_id missing or blank")
    if not _has_text(memory_type):
        violations.append("memory_type missing or blank")
    if not _has_text(scope):
        violations.append("scope missing or blank")
    if not _has_text(owner):
        violations.append("owner_user_scope missing or blank")
    if not _has_text(status):
        violations.append("status missing or blank")
    if not _has_text(source_type):
        violations.append("source_type missing or blank")
    if not _has_text(source_ref):
        violations.append("source_ref missing or blank")
    if not _has_text(visibility):
        violations.append("visibility missing or blank")
    if not _has_text(correction_path):
        violations.append("correction_path missing or blank")
    if not _has_text(user_visible_summary):
        violations.append("user_visible_summary missing or blank")
    if not _has_text(operator_visible_summary):
        violations.append("operator_visible_summary missing or blank")
    if not _has_text(confidence_level):
        violations.append("confidence_level missing or blank")
    if not _item_has_text(item, "evidence_count"):
        violations.append("evidence_count missing or blank")
    if not _has_text(_compact_text(item.get("created_marker"))):
        violations.append("created_marker missing or blank")
    if not _has_text(_compact_text(item.get("updated_marker"))):
        violations.append("updated_marker missing or blank")

    if memory_type not in _ALLOWED_TYPES_V1:
        violations.append(f"unknown memory type: {memory_type or '<blank>'}")
    if status not in _ALLOWED_STATUSES_V1:
        violations.append(f"unknown status: {status or '<blank>'}")
    if scope not in _ALLOWED_SCOPES_V1:
        violations.append(f"unknown scope: {scope or '<blank>'}")

    evidence_count = _safe_int(item.get("evidence_count"), default=-1)
    if evidence_count < 0:
        violations.append("evidence_count must be non-negative")

    if _looks_private_like(source_type, source_ref, user_visible_summary, operator_visible_summary, audit_note):
        violations.append("raw private memory content must be redacted")

    if scope == "session_only":
        if _has_text(project_id):
            violations.append("session_only memory cannot silently become project-scoped")
        if _has_text(tenant):
            violations.append("session_only memory cannot silently become tenant-scoped")
    if scope == "project_scoped" and not _has_text(project_id):
        violations.append("project_scoped memory requires project_id")
    if scope == "user_scoped" and not _has_text(owner):
        violations.append("user_scoped memory requires owner_user_scope")
    if scope == "tenant_account_scoped" and not _has_text(tenant):
        violations.append("tenant_account_scoped memory requires tenant_account_scope")
    if scope in {"system_wide_candidate", "system_wide_approved"}:
        if not _has_text(operator_visible_summary):
            violations.append("system-wide memory requires operator review metadata")
        if not _has_text(audit_note):
            violations.append("system-wide memory requires operator review metadata")
        if status == "absent":
            violations.append("system-wide memory cannot be absent")
        if scope == "system_wide_candidate" and status not in {"proposed", "provisional", "pending_approval"}:
            violations.append("system-wide candidate memory must remain a candidate")
        if scope == "system_wide_approved" and status != "confirmed":
            violations.append("system-wide approved memory must be confirmed")
        if scope == "system_wide_approved" and bool(item.get("pending_approval")):
            violations.append("system-wide approved memory cannot remain pending approval")

    if _is_cross_user_like(memory_id, owner, tenant, project_id, session_id, user_visible_summary, operator_visible_summary):
        if scope not in {"system_wide_candidate", "system_wide_approved", "operator_scoped"}:
            violations.append("cross-user/global memory fails closed")
        elif scope in {"system_wide_candidate", "system_wide_approved"} and not _has_text(audit_note):
            violations.append("cross-user/global memory requires governed operator metadata")

    if status == "blocked" and not _has_text(blocked_reason):
        violations.append("blocked memory requires blocked_reason")
    if status == "pending_approval" and not bool(item.get("pending_approval")):
        violations.append("pending approval memory must remain visible")
    if status == "stale" and not bool(item.get("stale")):
        violations.append("stale status must surface stale=true")
    if status == "contradicted" and not bool(item.get("contradicted")):
        violations.append("contradicted status must surface contradicted=true")
    if status == "invalidated" and not bool(item.get("invalidated")):
        violations.append("invalidated status must surface invalidated=true")
    if status == "absent" and _has_text(user_visible_summary):
        violations.append("absent memory should not present as confirmed context")

    if bool(item.get("stale")) and status not in {"stale", "archived_deprecated", "contradicted", "invalidated"}:
        violations.append("stale memory must be surfaced")
    if bool(item.get("contradicted")) and status not in {"contradicted", "invalidated", "archived_deprecated"}:
        violations.append("contradicted memory cannot drive action")
    if bool(item.get("invalidated")) and status not in {"invalidated", "archived_deprecated"}:
        violations.append("invalidated memory cannot be active")

    if bool(item.get("pending_approval")) and status not in {"pending_approval", "proposed", "provisional"}:
        violations.append("pending approvals remain visible")
    if status in {"proposed", "provisional"} and bool(item.get("pending_approval")) and scope == "session_only":
        violations.append("session-only candidate memory cannot silently become global")

    if memory_type == "candidate_learning_pattern" and status not in {"proposed", "provisional", "pending_approval", "confirmed", "stale", "contradicted", "invalidated", "archived_deprecated"}:
        violations.append("candidate learning patterns cannot become rules without review")
    if memory_type == "blocked_memory" and status != "blocked":
        violations.append("blocked memory must remain blocked")

    if not _has_text(correction_path):
        violations.append("correction_path missing or blank")

    if not _has_text(_compact_text(item.get("denied_authority"))):
        violations.append("denied_authority missing or blank")
    denied = item.get("denied_authority")
    if not isinstance(denied, Mapping):
        violations.append("denied_authority must be a mapping")
    else:
        for field in _DENIED_AUTHORITY_FIELDS_V1:
            if field not in denied:
                violations.append(f"missing denied authority: {field}")
            elif denied.get(field) is not False:
                violations.append(f"denied authority must remain blocked: {field}")

    classification = classify_memory_state_item_v1(item)
    return {"valid": not violations, "violation_count": len(violations), "violations": violations, "classification": classification}


def classify_memory_state_item_v1(item: Any) -> dict[str, Any]:
    if not isinstance(item, Mapping):
        return {"status": "unknown", "type": "unknown", "scope": "unknown", "risk": "blocked"}
    normalized = _json_safe(copy.deepcopy(item))
    status = _compact_text(normalized.get("status"), default="unknown")
    memory_type = _compact_text(normalized.get("memory_type"), default="unknown")
    scope = _compact_text(normalized.get("scope"), default="unknown")
    if status not in _ALLOWED_STATUSES_V1:
        status = "unknown"
    if memory_type not in _ALLOWED_TYPES_V1:
        memory_type = "unknown"
    if scope not in _ALLOWED_SCOPES_V1:
        scope = "unknown"
    return {"status": status, "type": memory_type, "scope": scope, "risk": _risk_from_status(status)}


def build_memory_state_packet_v1(
    *,
    packet_id: Any = None,
    owner_user_scope: Any = "",
    tenant_account_scope: Any = "",
    active_project_id: Any = "",
    active_session_id: Any = "",
    items: Any = None,
    limitations: Any = None,
    denied_authority: Any = None,
) -> dict[str, Any]:
    packet_id_text = _compact_text(packet_id)
    owner_text = _compact_text(owner_user_scope)
    tenant_text = _compact_text(tenant_account_scope)
    project_text = _compact_text(active_project_id)
    session_text = _compact_text(active_session_id)
    items_list = _json_safe(_listify(items))
    seed = {
        "packet_id": packet_id_text,
        "owner_user_scope": owner_text,
        "tenant_account_scope": tenant_text,
        "active_project_id": project_text,
        "active_session_id": session_text,
    }
    normalized_items: list[dict[str, Any]] = []
    for index, item in enumerate(items_list):
        if isinstance(item, Mapping):
            normalized_items.append(_json_safe(copy.deepcopy(item)))
        else:
            normalized_items.append({"value": _json_safe(item), "index": index})
    counts = {
        "item_count": len(normalized_items),
        "status_counts": {},
        "type_counts": {},
        "scope_counts": {},
        "pending_count": 0,
        "blocked_count": 0,
        "stale_count": 0,
        "contradicted_count": 0,
        "invalidated_count": 0,
        "candidate_learning_pattern_count": 0,
    }
    pending_approvals: list[dict[str, Any]] = []
    blocked_items: list[dict[str, Any]] = []
    stale_items: list[dict[str, Any]] = []
    contradicted_items: list[dict[str, Any]] = []
    invalidated_items: list[dict[str, Any]] = []
    candidate_learning_patterns: list[dict[str, Any]] = []
    operator_visible_items: list[dict[str, Any]] = []
    export_relevant_items: list[dict[str, Any]] = []
    deletion_relevant_items: list[dict[str, Any]] = []
    revocation_relevant_items: list[dict[str, Any]] = []
    visible_memory_summary: list[str] = []

    for item in normalized_items:
        status = _compact_text(item.get("status"), default="unknown")
        memory_type = _compact_text(item.get("memory_type"), default="unknown")
        scope = _compact_text(item.get("scope"), default="unknown")
        counts["status_counts"][status] = counts["status_counts"].get(status, 0) + 1
        counts["type_counts"][memory_type] = counts["type_counts"].get(memory_type, 0) + 1
        counts["scope_counts"][scope] = counts["scope_counts"].get(scope, 0) + 1
        if bool(item.get("pending_approval")):
            counts["pending_count"] += 1
            pending_approvals.append(item)
        if status == "blocked" or bool(item.get("blocked_reason")):
            counts["blocked_count"] += 1
            blocked_items.append(item)
        if bool(item.get("stale")) or status == "stale":
            counts["stale_count"] += 1
            stale_items.append(item)
        if bool(item.get("contradicted")) or status == "contradicted":
            counts["contradicted_count"] += 1
            contradicted_items.append(item)
        if bool(item.get("invalidated")) or status == "invalidated":
            counts["invalidated_count"] += 1
            invalidated_items.append(item)
        if memory_type == "candidate_learning_pattern":
            counts["candidate_learning_pattern_count"] += 1
            candidate_learning_patterns.append(item)
        if scope in {"operator_scoped", "system_wide_candidate", "system_wide_approved"}:
            operator_visible_items.append(item)
        if bool(item.get("export_relevance")):
            export_relevant_items.append(item)
        if bool(item.get("deletion_relevance")):
            deletion_relevant_items.append(item)
        if bool(item.get("revocation_relevance")):
            revocation_relevant_items.append(item)
        visible_memory_summary.append(_compact_text(item.get("user_visible_summary"), default=_default_summary_for_item(memory_type, status)))

    packet = {
        "schema_version": SCHEMA_VERSION_V1,
        "packet_id": packet_id_text or _stable_marker("memory_packet", seed),
        "packet_type": PACKET_TYPE_V1,
        "owner_user_scope": owner_text,
        "tenant_account_scope": tenant_text,
        "active_project_id": project_text,
        "active_session_id": session_text,
        "items": normalized_items,
        "counts": _json_safe(counts),
        "visible_memory_summary": _json_safe(visible_memory_summary),
        "pending_approvals": _json_safe(pending_approvals),
        "blocked_items": _json_safe(blocked_items),
        "stale_items": _json_safe(stale_items),
        "contradicted_items": _json_safe(contradicted_items),
        "invalidated_items": _json_safe(invalidated_items),
        "candidate_learning_patterns": _json_safe(candidate_learning_patterns),
        "operator_visible_items": _json_safe(operator_visible_items),
        "export_relevant_items": _json_safe(export_relevant_items),
        "deletion_relevant_items": _json_safe(deletion_relevant_items),
        "revocation_relevant_items": _json_safe(revocation_relevant_items),
        "limitations": _json_safe(_listify(limitations)),
        "denied_authority": _build_denied_authority() if denied_authority is None else _normalize_denied_authority(denied_authority),
    }
    return _json_safe(packet)


def validate_memory_state_packet_v1(packet: Any) -> dict[str, Any]:
    violations: list[str] = []
    if not isinstance(packet, Mapping):
        violations.append("packet must be a mapping")
        return {"valid": False, "violation_count": len(violations), "violations": violations, "classification": {"status": "unknown", "type": "unknown", "scope": "unknown", "risk": "blocked"}}

    packet = _json_safe(copy.deepcopy(packet))

    for field in _CORE_PACKET_FIELDS_V1:
        if field not in packet:
            violations.append(f"missing field: {field}")

    if not _item_has_text(packet, "schema_version"):
        violations.append("schema_version missing or blank")
    elif _compact_text(packet.get("schema_version")) != SCHEMA_VERSION_V1:
        violations.append("schema_version mismatch")

    packet_id = _compact_text(packet.get("packet_id"))
    packet_type = _compact_text(packet.get("packet_type"))
    owner = _compact_text(packet.get("owner_user_scope"))
    tenant = _compact_text(packet.get("tenant_account_scope"))
    project_id = _compact_text(packet.get("active_project_id"))
    session_id = _compact_text(packet.get("active_session_id"))
    limitations = packet.get("limitations")
    denied = packet.get("denied_authority")

    if not _has_text(packet_id):
        violations.append("packet_id missing or blank")
    if packet_type != PACKET_TYPE_V1:
        violations.append("packet_type mismatch")
    if not _has_text(owner):
        violations.append("owner_user_scope missing or blank")
    if not _has_text(tenant):
        violations.append("tenant_account_scope missing or blank")
    if not _has_text(project_id) and not _has_text(session_id):
        violations.append("packet must retain project or session linkage metadata")
    if not isinstance(packet.get("items"), list):
        violations.append("items must be a list")
    if not isinstance(packet.get("counts"), Mapping):
        violations.append("counts must be a mapping")
    if not isinstance(denied, Mapping):
        violations.append("denied_authority must be a mapping")
    else:
        for field in _DENIED_AUTHORITY_FIELDS_V1:
            if field not in denied:
                violations.append(f"missing denied authority: {field}")
            elif denied.get(field) is not False:
                violations.append(f"denied authority must remain blocked: {field}")

    if not isinstance(limitations, list):
        violations.append("limitations must be a list")

    items = packet.get("items") if isinstance(packet.get("items"), list) else []
    valid_items: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        item_result = validate_memory_state_item_v1(item)
        if not item_result["valid"]:
            violations.append(f"invalid item at index {index}: {', '.join(item_result['violations'])}")
        else:
            valid_items.append(_json_safe(item))

    if not valid_items and items:
        violations.append("packet must contain at least one valid memory item")

    classification = {"status": "confirmed" if not violations else "blocked", "type": "packet", "scope": "packet", "risk": "active" if not violations else "blocked"}
    return {"valid": not violations, "violation_count": len(violations), "violations": violations, "classification": classification}


def summarize_memory_state_packet_v1(packet: Any) -> dict[str, Any]:
    normalized = _json_safe(copy.deepcopy(packet)) if isinstance(packet, Mapping) else {}
    items = normalized.get("items") if isinstance(normalized, Mapping) and isinstance(normalized.get("items"), list) else []
    counts = normalized.get("counts") if isinstance(normalized, Mapping) and isinstance(normalized.get("counts"), Mapping) else {}
    summary = {
        "packet_id": _compact_text(normalized.get("packet_id"), default="unknown_packet"),
        "packet_type": _compact_text(normalized.get("packet_type"), default=PACKET_TYPE_V1),
        "item_count": _safe_int(counts.get("item_count", len(items)), default=len(items)),
        "pending_count": _safe_int(counts.get("pending_count", 0)),
        "blocked_count": _safe_int(counts.get("blocked_count", 0)),
        "stale_count": _safe_int(counts.get("stale_count", 0)),
        "contradicted_count": _safe_int(counts.get("contradicted_count", 0)),
        "invalidated_count": _safe_int(counts.get("invalidated_count", 0)),
        "candidate_learning_pattern_count": _safe_int(counts.get("candidate_learning_pattern_count", 0)),
        "visible_memory_summary": _json_safe(normalized.get("visible_memory_summary", [])),
        "pending_approvals": _json_safe(normalized.get("pending_approvals", [])),
        "blocked_items": _json_safe(normalized.get("blocked_items", [])),
        "limitations": _json_safe(normalized.get("limitations", [])),
    }
    return _json_safe(summary)


def to_memory_state_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def build_initial_memory_state_examples_v1() -> list[dict[str, Any]]:
    items = [
        build_memory_state_item_v1(
            memory_id="memory_alpha_preference",
            memory_type="preference",
            scope="user_scoped",
            owner_user_scope="operator",
            tenant_account_scope="self",
            project_id="project_alpha",
            session_id="session_alpha",
            status="confirmed",
            source_type="direct_user_confirmation",
            source_ref="synthetic_preference",
            evidence_count=2,
            confidence_level="high",
            user_visible_summary="User prefers concise, surgical reports.",
            operator_visible_summary="Confirmed user preference for concise output.",
            audit_note="synthetic example memory",
            export_relevance=True,
        ),
        build_memory_state_item_v1(
            memory_id="memory_alpha_candidate",
            memory_type="candidate_learning_pattern",
            scope="system_wide_candidate",
            owner_user_scope="operator",
            tenant_account_scope="self",
            project_id="project_alpha",
            session_id="session_alpha",
            status="pending_approval",
            source_type="session_summary",
            source_ref="synthetic_candidate",
            evidence_count=3,
            confidence_level="medium",
            user_visible_summary="A repeated pattern may be useful, but it is not a rule.",
            operator_visible_summary="Candidate pattern for review only.",
            audit_note="synthetic candidate pattern",
            pending_approval=True,
        ),
    ]
    packet = build_memory_state_packet_v1(
        packet_id="memory_alpha_packet",
        owner_user_scope="operator",
        tenant_account_scope="self",
        active_project_id="project_alpha",
        active_session_id="session_alpha",
        items=items,
        limitations=["synthetic example"],
    )
    return [packet, {"items": items, "summary": summarize_memory_state_packet_v1(packet), "synthetic": True}]
