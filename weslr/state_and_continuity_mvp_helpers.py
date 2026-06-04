"""Metadata-only state and continuity helpers v1."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping, Sequence

SCHEMA_VERSION_V1 = "state_and_continuity_mvp_v1"
PACKET_TYPE_V1 = "state_and_continuity_mvp_packet_v1"

_ALLOWED_CATEGORIES_V1 = (
    "user_state",
    "session_state",
    "project_state",
    "memory_state",
    "task_checklist_state",
    "action_tool_state",
    "evidence_source_state",
    "uncertainty_state",
    "boundary_safety_state",
    "learning_candidate_pattern_state",
    "escalation_support_state",
    "operator_visible_state",
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
    "active_metadata_only",
)

_DENIED_AUTHORITY_FIELDS_V1 = (
    "runtime_wiring_authority",
    "chat_" "responder_authority",
    "storage_database_authority",
    "weslr_io_authority",
    "memory_persistence_authority",
    "project_state_mutation_authority",
    "external_action_authority",
    "cross_user_leakage_authority",
    "hidden_personalization_authority",
    "behavior_update_authority",
    "public_product_readiness_authority",
    "consciousness_or_aliveness_claim_authority",
)

_CORE_ITEM_FIELDS_V1 = (
    "schema_version",
    "item_id",
    "category",
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
    "update_authority",
    "correction_path",
    "user_visible_summary",
    "operator_visible_summary",
    "stale",
    "contradicted",
    "invalidated",
    "pending_approval",
    "blocked_reason",
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
    "visible_state_summary",
    "pending_approvals",
    "blocked_items",
    "stale_items",
    "contradicted_items",
    "invalidated_items",
    "uncertainty_items",
    "operator_visible_items",
    "limitations",
    "denied_authority",
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
                denied[field] = False if value.get(field) in (False, None, 0, "", "blocked") else bool(value.get(field)) and False
    return denied


def _normalize_item(item: Any) -> dict[str, Any]:
    if isinstance(item, Mapping):
        normalized = {str(key): _json_safe(val) for key, val in item.items()}
        normalized.setdefault("schema_version", SCHEMA_VERSION_V1)
        normalized.setdefault("denied_authority", _normalize_denied_authority(normalized.get("denied_authority")))
        return normalized
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "item_id": _stable_marker("item", {"value": item}),
        "category": "unknown",
        "scope": "session_only",
        "owner_user_scope": "",
        "tenant_account_scope": "",
        "project_id": "",
        "session_id": "",
        "status": "absent",
        "source_type": "synthetic",
        "source_ref": _stable_marker("source", {"value": item}),
        "evidence_count": 0,
        "confidence_level": "unknown",
        "visibility": "user_visible",
        "update_authority": "metadata_only",
        "correction_path": "review_and_refresh",
        "user_visible_summary": _compact_text(item),
        "operator_visible_summary": _compact_text(item),
        "stale": False,
        "contradicted": False,
        "invalidated": False,
        "pending_approval": False,
        "blocked_reason": "",
        "audit_note": "",
        "created_marker": _stable_marker("created", {"value": item}),
        "updated_marker": _stable_marker("updated", {"value": item}),
        "denied_authority": _normalize_denied_authority(),
    }


def _is_cross_user_like(*values: Any) -> bool:
    text = " ".join(_compact_text(value, default="").lower() for value in values)
    markers = ("shared", "system", "cross-user", "cross user", "global", "tenant-wide", "account-wide", "workspace-wide", "org-wide")
    return any(marker in text for marker in markers)


def _default_status_for_category(category: str) -> str:
    return {
        "user_state": "confirmed",
        "session_state": "active_metadata_only",
        "project_state": "active_metadata_only",
        "memory_state": "provisional",
        "task_checklist_state": "pending_approval",
        "action_tool_state": "pending_approval",
        "evidence_source_state": "confirmed",
        "uncertainty_state": "proposed",
        "boundary_safety_state": "active_metadata_only",
        "learning_candidate_pattern_state": "proposed",
        "escalation_support_state": "pending_approval",
        "operator_visible_state": "active_metadata_only",
    }.get(category, "absent")


def _default_visibility_for_category(category: str) -> str:
    return {
        "operator_visible_state": "operator_visible",
        "escalation_support_state": "user_visible_operator_visible",
        "boundary_safety_state": "user_visible",
    }.get(category, "user_visible")


def _default_summary_for_item(category: str, status: str) -> str:
    templates = {
        "user_state": "user-scoped continuity metadata",
        "session_state": "session continuity metadata",
        "project_state": "project continuity metadata",
        "memory_state": "memory continuity metadata",
        "task_checklist_state": "task checklist metadata",
        "action_tool_state": "action/tool status metadata",
        "evidence_source_state": "evidence and source metadata",
        "uncertainty_state": "uncertainty metadata",
        "boundary_safety_state": "boundary and safety metadata",
        "learning_candidate_pattern_state": "candidate pattern metadata",
        "escalation_support_state": "escalation and support metadata",
        "operator_visible_state": "operator-visible governance metadata",
    }
    base = templates.get(category, "continuity metadata")
    return f"{base} ({status})"


def allowed_state_continuity_categories_v1() -> tuple[str, ...]:
    return _ALLOWED_CATEGORIES_V1


def allowed_state_continuity_scopes_v1() -> tuple[str, ...]:
    return _ALLOWED_SCOPES_V1


def allowed_state_continuity_statuses_v1() -> tuple[str, ...]:
    return _ALLOWED_STATUSES_V1


def build_state_continuity_item_v1(
    *,
    item_id: Any = None,
    category: Any = None,
    scope: Any = None,
    owner_user_scope: Any = "",
    tenant_account_scope: Any = "",
    project_id: Any = "",
    session_id: Any = "",
    status: Any = None,
    source_type: Any = "synthetic",
    source_ref: Any = None,
    evidence_count: Any = 0,
    confidence_level: Any = "unknown",
    visibility: Any = None,
    update_authority: Any = "metadata_only",
    correction_path: Any = "review_and_refresh",
    user_visible_summary: Any = None,
    operator_visible_summary: Any = None,
    stale: Any = False,
    contradicted: Any = False,
    invalidated: Any = False,
    pending_approval: Any = False,
    blocked_reason: Any = "",
    audit_note: Any = "",
    created_marker: Any = None,
    updated_marker: Any = None,
    denied_authority: Any = None,
    governed_metadata_only: bool = False,
    raw_private_content: Any = None,
) -> dict[str, Any]:
    category_text = _compact_text(category)
    scope_text = _compact_text(scope)
    status_text = _compact_text(status) or _default_status_for_category(category_text)
    owner_text = _compact_text(owner_user_scope)
    tenant_text = _compact_text(tenant_account_scope)
    project_text = _compact_text(project_id)
    session_text = _compact_text(session_id)
    visibility_text = _compact_text(visibility) or _default_visibility_for_category(category_text)
    source_type_text = _compact_text(source_type, default="synthetic")
    source_ref_text = _compact_text(source_ref)
    evidence_count_int = max(0, _safe_int(evidence_count, 0))
    confidence_text = _compact_text(confidence_level, default="unknown")
    update_authority_text = _compact_text(update_authority, default="metadata_only")
    correction_path_text = _compact_text(correction_path, default="review_and_refresh")
    blocked_reason_text = _compact_text(blocked_reason)
    audit_note_text = _compact_text(audit_note)
    user_visible_summary_text = _compact_text(user_visible_summary) or _default_summary_for_item(category_text, status_text)
    operator_visible_summary_text = _compact_text(operator_visible_summary) or user_visible_summary_text
    created_marker_text = _compact_text(created_marker)
    updated_marker_text = _compact_text(updated_marker)
    seed = {
        "item_id": _compact_text(item_id),
        "category": category_text,
        "scope": scope_text,
        "owner_user_scope": owner_text,
        "tenant_account_scope": tenant_text,
        "project_id": project_text,
        "session_id": session_text,
        "status": status_text,
        "source_type": source_type_text,
        "source_ref": source_ref_text,
        "visibility": visibility_text,
    }
    item = {
        "schema_version": SCHEMA_VERSION_V1,
        "item_id": _compact_text(item_id) or _stable_marker("state_item", seed),
        "category": category_text,
        "scope": scope_text,
        "owner_user_scope": owner_text,
        "tenant_account_scope": tenant_text,
        "project_id": project_text,
        "session_id": session_text,
        "status": status_text,
        "source_type": source_type_text,
        "source_ref": source_ref_text or _stable_marker("source", seed),
        "evidence_count": evidence_count_int,
        "confidence_level": confidence_text,
        "visibility": visibility_text,
        "update_authority": update_authority_text,
        "correction_path": correction_path_text,
        "user_visible_summary": user_visible_summary_text,
        "operator_visible_summary": operator_visible_summary_text,
        "stale": bool(stale),
        "contradicted": bool(contradicted),
        "invalidated": bool(invalidated),
        "pending_approval": bool(pending_approval),
        "blocked_reason": blocked_reason_text,
        "audit_note": audit_note_text,
        "created_marker": created_marker_text or _stable_marker("created", seed),
        "updated_marker": updated_marker_text or _stable_marker("updated", {**seed, "created_marker": created_marker_text}),
        "denied_authority": _normalize_denied_authority(denied_authority),
        "governed_metadata_only": bool(governed_metadata_only),
    }
    if raw_private_content is not None:
        item["raw_private_data_redacted"] = True
        if not item["audit_note"]:
            item["audit_note"] = "raw private content redacted by default"
        else:
            item["audit_note"] = f"{item['audit_note']} | raw private content redacted by default"
    return _json_safe(item)


def _item_has_text(item: Mapping[str, Any], field: str) -> bool:
    return field in item and _has_text(item.get(field))


def validate_state_continuity_item_v1(item: Any) -> dict[str, Any]:
    violations: list[str] = []
    if not isinstance(item, Mapping):
        violations.append("item must be a mapping")
        return {"valid": False, "violation_count": len(violations), "violations": violations, "classification": {"category": "unknown", "scope": "unknown", "status": "unknown", "risk": "blocked"}}

    item = _normalize_item(item)

    for field in _CORE_ITEM_FIELDS_V1:
        if field not in item:
            violations.append(f"missing field: {field}")

    if not _item_has_text(item, "schema_version"):
        violations.append("schema_version missing or blank")
    elif _compact_text(item.get("schema_version")) != SCHEMA_VERSION_V1:
        violations.append("schema_version mismatch")

    if not _item_has_text(item, "item_id"):
        violations.append("item_id missing or blank")
    if not _item_has_text(item, "category"):
        violations.append("category missing or blank")
    if not _item_has_text(item, "scope"):
        violations.append("scope missing or blank")
    if not _item_has_text(item, "status"):
        violations.append("status missing or blank")
    if not _item_has_text(item, "source_type"):
        violations.append("source_type missing or blank")
    if not _item_has_text(item, "source_ref"):
        violations.append("source_ref missing or blank")

    category = _compact_text(item.get("category"))
    scope = _compact_text(item.get("scope"))
    status = _compact_text(item.get("status"))
    owner = _compact_text(item.get("owner_user_scope"))
    tenant = _compact_text(item.get("tenant_account_scope"))
    project_id = _compact_text(item.get("project_id"))
    session_id = _compact_text(item.get("session_id"))
    visibility = _compact_text(item.get("visibility"))
    update_authority = _compact_text(item.get("update_authority"))
    blocked_reason = _compact_text(item.get("blocked_reason"))
    audit_note = _compact_text(item.get("audit_note"))
    correction_path = _compact_text(item.get("correction_path"))

    if category not in _ALLOWED_CATEGORIES_V1:
        violations.append(f"unknown category: {category or '<blank>'}")
    if scope not in _ALLOWED_SCOPES_V1:
        violations.append(f"unknown scope: {scope or '<blank>'}")
    if status not in _ALLOWED_STATUSES_V1:
        violations.append(f"unknown status: {status or '<blank>'}")

    if _is_cross_user_like(scope, owner, tenant) and not bool(item.get("governed_metadata_only")):
        violations.append("cross-user or global state requires governed_metadata_only=true")

    if scope == "session_only":
        if not session_id:
            violations.append("session_only state requires session_id")
        if project_id:
            violations.append("session_only state must not silently become project scoped")
    elif scope == "project_scoped" and not project_id:
        violations.append("project_scoped state requires project_id")

    if scope == "user_scoped" and not owner:
        violations.append("user_scoped state requires owner_user_scope")
    if scope == "tenant_account_scoped" and not tenant:
        violations.append("tenant_account_scoped state requires tenant_account_scope")
    if scope == "operator_scoped" and not owner:
        violations.append("operator_scoped state requires owner_user_scope")

    if scope in {"system_wide_candidate", "system_wide_approved"}:
        if not bool(item.get("governed_metadata_only")):
            violations.append("system-wide state requires governed_metadata_only=true")
        if not owner:
            violations.append("system-wide state requires owner_user_scope")
        if not tenant:
            violations.append("system-wide state requires tenant_account_scope")
        if "operator" not in update_authority.lower():
            violations.append("system-wide state requires operator review metadata in update_authority")
        if not audit_note:
            violations.append("system-wide state requires audit_note")

    if status == "blocked" and not blocked_reason:
        violations.append("blocked state requires blocked_reason")
    if status == "pending_approval" and not _has_text(item.get("pending_approval")):
        violations.append("pending approval state must remain visible")
    if status == "stale" and not bool(item.get("stale")):
        violations.append("stale status must surface stale=true")
    if status == "contradicted" and not bool(item.get("contradicted")):
        violations.append("contradicted status must surface contradicted=true")
    if status == "invalidated" and not bool(item.get("invalidated")):
        violations.append("invalidated status must surface invalidated=true")
    if bool(item.get("contradicted")) and status not in {"contradicted", "invalidated", "stale"}:
        violations.append("contradicted state cannot be active")
    if bool(item.get("invalidated")) and status != "invalidated":
        violations.append("invalidated state cannot be active")
    if bool(item.get("stale")) and status not in {"stale", "archived_deprecated", "invalidated", "contradicted"}:
        violations.append("stale state must be surfaced in status")

    if category == "boundary_safety_state" and status == "blocked" and not blocked_reason:
        violations.append("boundary_safety_state blocked item requires blocked_reason")
    if category == "escalation_support_state" and (not _has_text(item.get("user_visible_summary")) or not _has_text(item.get("operator_visible_summary"))):
        violations.append("support state must remain visible")
    if category == "operator_visible_state" and not audit_note:
        violations.append("operator-visible state requires audit_note")
    if category == "learning_candidate_pattern_state" and status == "confirmed" and "review" not in audit_note.lower():
        violations.append("candidate pattern requires review metadata before confirmation")
    if category == "action_tool_state" and update_authority.lower() in {"permission_granted", "allowed", "execute"}:
        violations.append("action/tool availability is not permission")

    denied = item.get("denied_authority")
    if not isinstance(denied, Mapping):
        violations.append("denied_authority must be a mapping")
    else:
        for field in _DENIED_AUTHORITY_FIELDS_V1:
            if field not in denied:
                violations.append(f"denied_authority missing {field}")
            elif denied.get(field) not in (False, 0, None, "blocked"):
                violations.append(f"denied_authority {field} must be false or blocked")

    if not _has_text(item.get("user_visible_summary")):
        violations.append("user_visible_summary missing or blank")
    if not _has_text(item.get("operator_visible_summary")):
        violations.append("operator_visible_summary missing or blank")
    if not _has_text(item.get("created_marker")):
        violations.append("created_marker missing or blank")
    if not _has_text(item.get("updated_marker")):
        violations.append("updated_marker missing or blank")
    if not _has_text(correction_path):
        violations.append("correction_path missing or blank")
    if not _has_text(visibility):
        violations.append("visibility missing or blank")
    if not _has_text(update_authority):
        violations.append("update_authority missing or blank")

    if _safe_int(item.get("evidence_count"), -1) < 0:
        violations.append("evidence_count must be zero or greater")
    if not isinstance(item.get("stale"), bool):
        violations.append("stale must be boolean")
    if not isinstance(item.get("contradicted"), bool):
        violations.append("contradicted must be boolean")
    if not isinstance(item.get("invalidated"), bool):
        violations.append("invalidated must be boolean")
    if not isinstance(item.get("pending_approval"), bool):
        violations.append("pending_approval must be boolean")

    if category == "operator_visible_state" and visibility != "operator_visible":
        violations.append("operator-visible state must be operator_visible")

    classification = classify_state_continuity_item_v1(item)
    valid = len(violations) == 0
    classification["risk"] = classification.get("risk", "blocked") if not valid else classification.get("risk", "metadata_only")
    return {"valid": valid, "violation_count": len(violations), "violations": violations, "classification": classification}


def classify_state_continuity_item_v1(item: Any) -> dict[str, Any]:
    normalized = _normalize_item(item)
    category = _compact_text(normalized.get("category"), default="unknown")
    scope = _compact_text(normalized.get("scope"), default="unknown")
    status = _compact_text(normalized.get("status"), default="unknown")
    blocked = bool(normalized.get("blocked_reason")) or status == "blocked"
    risk = "blocked" if blocked else "metadata_only"
    if status in {"failed", "invalidated", "contradicted"}:
        risk = "blocked"
    if status in {"pending_approval", "proposed", "provisional", "stale", "archived_deprecated"} and risk != "blocked":
        risk = "review_required"
    return {
        "category": category if category in _ALLOWED_CATEGORIES_V1 else "unknown",
        "scope": scope if scope in _ALLOWED_SCOPES_V1 else "unknown",
        "status": status if status in _ALLOWED_STATUSES_V1 else "unknown",
        "risk": risk,
        "item": _json_safe(normalized),
    }


def _ensure_items(value: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for entry in _listify(value):
        items.append(_normalize_item(entry))
    return items


def _packet_denied_authority(value: Any = None) -> dict[str, Any]:
    return _normalize_denied_authority(value)


def build_state_continuity_packet_v1(
    *,
    packet_id: Any = None,
    packet_type: Any = PACKET_TYPE_V1,
    owner_user_scope: Any = "",
    tenant_account_scope: Any = "",
    active_project_id: Any = "",
    active_session_id: Any = "",
    items: Any = None,
    limitations: Any = None,
    denied_authority: Any = None,
    governed_metadata_only: bool = False,
    raw_private_content: Any = None,
) -> dict[str, Any]:
    normalized_items = _ensure_items(items)
    packet_seed = {
        "packet_type": _compact_text(packet_type, default=PACKET_TYPE_V1),
        "owner_user_scope": _compact_text(owner_user_scope),
        "tenant_account_scope": _compact_text(tenant_account_scope),
        "active_project_id": _compact_text(active_project_id),
        "active_session_id": _compact_text(active_session_id),
        "items": normalized_items,
        "governed_metadata_only": bool(governed_metadata_only),
    }
    packet = {
        "schema_version": SCHEMA_VERSION_V1,
        "packet_id": _compact_text(packet_id) or _stable_marker("state_packet", packet_seed),
        "packet_type": _compact_text(packet_type, default=PACKET_TYPE_V1),
        "owner_user_scope": _compact_text(owner_user_scope),
        "tenant_account_scope": _compact_text(tenant_account_scope),
        "active_project_id": _compact_text(active_project_id),
        "active_session_id": _compact_text(active_session_id),
        "items": normalized_items,
        "counts": {},
        "visible_state_summary": {},
        "pending_approvals": [],
        "blocked_items": [],
        "stale_items": [],
        "contradicted_items": [],
        "invalidated_items": [],
        "uncertainty_items": [],
        "operator_visible_items": [],
        "limitations": _listify(limitations),
        "denied_authority": _packet_denied_authority(denied_authority),
        "governed_metadata_only": bool(governed_metadata_only),
    }
    if raw_private_content is not None:
        packet["raw_private_data_redacted"] = True
        packet["limitations"] = packet["limitations"] + ["raw private content redacted by default"]
    counts_by_category = {category: 0 for category in _ALLOWED_CATEGORIES_V1}
    counts_by_scope = {scope: 0 for scope in _ALLOWED_SCOPES_V1}
    counts_by_status = {status: 0 for status in _ALLOWED_STATUSES_V1}
    pending_approvals: list[dict[str, Any]] = []
    blocked_items: list[dict[str, Any]] = []
    stale_items: list[dict[str, Any]] = []
    contradicted_items: list[dict[str, Any]] = []
    invalidated_items: list[dict[str, Any]] = []
    uncertainty_items: list[dict[str, Any]] = []
    operator_visible_items: list[dict[str, Any]] = []

    for item in normalized_items:
        category = _compact_text(item.get("category"))
        scope = _compact_text(item.get("scope"))
        status = _compact_text(item.get("status"))
        if category in counts_by_category:
            counts_by_category[category] += 1
        if scope in counts_by_scope:
            counts_by_scope[scope] += 1
        if status in counts_by_status:
            counts_by_status[status] += 1
        if bool(item.get("pending_approval")) or status == "pending_approval":
            pending_approvals.append(_json_safe(item))
        if bool(item.get("blocked_reason")) or status == "blocked":
            blocked_items.append(_json_safe(item))
        if bool(item.get("stale")) or status == "stale":
            stale_items.append(_json_safe(item))
        if bool(item.get("contradicted")) or status == "contradicted":
            contradicted_items.append(_json_safe(item))
        if bool(item.get("invalidated")) or status == "invalidated":
            invalidated_items.append(_json_safe(item))
        if category == "uncertainty_state" or status in {"absent", "proposed", "provisional", "pending_approval"}:
            uncertainty_items.append(_json_safe(item))
        if category == "operator_visible_state" or _compact_text(item.get("visibility")) == "operator_visible":
            operator_visible_items.append(_json_safe(item))

    packet["counts"] = {
        "total_items": len(normalized_items),
        "categories": counts_by_category,
        "scopes": counts_by_scope,
        "statuses": counts_by_status,
        "pending_approvals_count": len(pending_approvals),
        "blocked_items_count": len(blocked_items),
        "stale_items_count": len(stale_items),
        "contradicted_items_count": len(contradicted_items),
        "invalidated_items_count": len(invalidated_items),
        "uncertainty_items_count": len(uncertainty_items),
        "operator_visible_items_count": len(operator_visible_items),
    }
    packet["visible_state_summary"] = {
        "item_count": len(normalized_items),
        "pending_approvals_count": len(pending_approvals),
        "blocked_items_count": len(blocked_items),
        "stale_items_count": len(stale_items),
        "contradicted_items_count": len(contradicted_items),
        "invalidated_items_count": len(invalidated_items),
        "uncertainty_items_count": len(uncertainty_items),
        "operator_visible_items_count": len(operator_visible_items),
        "categories_present": [category for category, count in counts_by_category.items() if count],
    }
    packet["pending_approvals"] = pending_approvals
    packet["blocked_items"] = blocked_items
    packet["stale_items"] = stale_items
    packet["contradicted_items"] = contradicted_items
    packet["invalidated_items"] = invalidated_items
    packet["uncertainty_items"] = uncertainty_items
    packet["operator_visible_items"] = operator_visible_items
    return _json_safe(packet)


def validate_state_continuity_packet_v1(packet: Any) -> dict[str, Any]:
    violations: list[str] = []
    if not isinstance(packet, Mapping):
        violations.append("packet must be a mapping")
        return {"valid": False, "violation_count": len(violations), "violations": violations}

    packet = _json_safe(packet)
    for field in _CORE_PACKET_FIELDS_V1:
        if field not in packet:
            violations.append(f"missing field: {field}")

    if _compact_text(packet.get("schema_version")) != SCHEMA_VERSION_V1:
        violations.append("schema_version mismatch")
    if _compact_text(packet.get("packet_type")) != PACKET_TYPE_V1:
        violations.append("packet_type mismatch")

    for field in ("packet_id", "owner_user_scope", "tenant_account_scope"):
        if not _has_text(packet.get(field)):
            violations.append(f"{field} missing or blank")

    items = packet.get("items")
    if not isinstance(items, list):
        violations.append("items must be a list")
        items = []
    elif not items:
        violations.append("items must not be empty")

    if not isinstance(packet.get("counts"), Mapping):
        violations.append("counts must be a mapping")
    if not isinstance(packet.get("visible_state_summary"), Mapping):
        violations.append("visible_state_summary must be a mapping")

    if not isinstance(packet.get("denied_authority"), Mapping):
        violations.append("denied_authority must be a mapping")
    else:
        denied = packet.get("denied_authority")
        for field in _DENIED_AUTHORITY_FIELDS_V1:
            if field not in denied:
                violations.append(f"denied_authority missing {field}")
            elif denied.get(field) not in (False, 0, None, "blocked"):
                violations.append(f"denied_authority {field} must be false or blocked")

    if _is_cross_user_like(packet.get("owner_user_scope"), packet.get("tenant_account_scope"), packet.get("active_project_id"), packet.get("active_session_id")) and not bool(packet.get("governed_metadata_only")):
        violations.append("cross-user or global packet requires governed_metadata_only=true")

    if bool(packet.get("raw_private_data_redacted")) and any("raw private content" in _compact_text(item).lower() for item in _listify(packet.get("limitations"))):
        pass

    seen_ids: set[str] = set()
    for item in items:
        item_result = validate_state_continuity_item_v1(item)
        if not item_result["valid"]:
            violations.extend(f"item { _compact_text(item.get('item_id')) or '<unknown>' }: {msg}" for msg in item_result["violations"])
        item_id = _compact_text(item.get("item_id"))
        if item_id:
            if item_id in seen_ids:
                violations.append(f"duplicate item_id: {item_id}")
            seen_ids.add(item_id)

    packet_counts = packet.get("counts") if isinstance(packet.get("counts"), Mapping) else {}
    if isinstance(packet_counts, Mapping):
        if _safe_int(packet_counts.get("total_items"), -1) != len(items):
            violations.append("counts.total_items mismatch")
        for field, bucket in (("pending_approvals_count", packet.get("pending_approvals")), ("blocked_items_count", packet.get("blocked_items")), ("stale_items_count", packet.get("stale_items")), ("contradicted_items_count", packet.get("contradicted_items")), ("invalidated_items_count", packet.get("invalidated_items")), ("uncertainty_items_count", packet.get("uncertainty_items")), ("operator_visible_items_count", packet.get("operator_visible_items"))):
            if field in packet_counts and _safe_int(packet_counts.get(field), -1) != len(_listify(bucket)):
                violations.append(f"counts.{field} mismatch")

    valid = len(violations) == 0
    return {"valid": valid, "violation_count": len(violations), "violations": violations}


def summarize_state_continuity_packet_v1(packet: Any) -> dict[str, Any]:
    safe = to_state_continuity_json_safe_v1(packet)
    items = safe.get("items", []) if isinstance(safe, Mapping) else []
    counts = safe.get("counts", {}) if isinstance(safe, Mapping) else {}
    summary = {
        "schema_version": safe.get("schema_version"),
        "packet_id": safe.get("packet_id"),
        "packet_type": safe.get("packet_type"),
        "owner_user_scope": safe.get("owner_user_scope"),
        "tenant_account_scope": safe.get("tenant_account_scope"),
        "active_project_id": safe.get("active_project_id"),
        "active_session_id": safe.get("active_session_id"),
        "item_count": counts.get("total_items", len(items)),
        "pending_approvals_count": counts.get("pending_approvals_count", len(safe.get("pending_approvals", []))),
        "blocked_items_count": counts.get("blocked_items_count", len(safe.get("blocked_items", []))),
        "stale_items_count": counts.get("stale_items_count", len(safe.get("stale_items", []))),
        "contradicted_items_count": counts.get("contradicted_items_count", len(safe.get("contradicted_items", []))),
        "invalidated_items_count": counts.get("invalidated_items_count", len(safe.get("invalidated_items", []))),
        "uncertainty_items_count": counts.get("uncertainty_items_count", len(safe.get("uncertainty_items", []))),
        "operator_visible_items_count": counts.get("operator_visible_items_count", len(safe.get("operator_visible_items", []))),
        "categories_present": safe.get("visible_state_summary", {}).get("categories_present", []) if isinstance(safe.get("visible_state_summary"), Mapping) else [],
        "limitations": safe.get("limitations", []),
    }
    return _json_safe(summary)


def to_state_continuity_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def build_initial_state_continuity_examples_v1() -> list[dict[str, Any]]:
    examples = [
        build_state_continuity_packet_v1(
            packet_id="state_continuity_example_001",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            active_session_id="session_alpha",
            items=[
                build_state_continuity_item_v1(
                    item_id="item_user_001",
                    category="user_state",
                    scope="user_scoped",
                    owner_user_scope="operator",
                    tenant_account_scope="self",
                    status="confirmed",
                    source_type="synthetic",
                    source_ref="user_note_001",
                    evidence_count=2,
                    confidence_level="high",
                    user_visible_summary="user-scoped continuity metadata",
                    operator_visible_summary="user-scoped continuity metadata",
                    audit_note="synthetic example",
                ),
                build_state_continuity_item_v1(
                    item_id="item_session_001",
                    category="session_state",
                    scope="session_only",
                    owner_user_scope="operator",
                    tenant_account_scope="self",
                    session_id="session_alpha",
                    status="active_metadata_only",
                    source_type="synthetic",
                    source_ref="session_note_001",
                    evidence_count=1,
                    confidence_level="medium",
                    user_visible_summary="session continuity metadata",
                    operator_visible_summary="session continuity metadata",
                    audit_note="synthetic example",
                ),
                build_state_continuity_item_v1(
                    item_id="item_project_001",
                    category="project_state",
                    scope="project_scoped",
                    owner_user_scope="operator",
                    tenant_account_scope="self",
                    project_id="project_alpha",
                    status="active_metadata_only",
                    source_type="synthetic",
                    source_ref="project_note_001",
                    evidence_count=3,
                    confidence_level="high",
                    user_visible_summary="project continuity metadata",
                    operator_visible_summary="project continuity metadata",
                    audit_note="synthetic example",
                ),
                build_state_continuity_item_v1(
                    item_id="item_memory_001",
                    category="memory_state",
                    scope="user_scoped",
                    owner_user_scope="operator",
                    tenant_account_scope="self",
                    status="provisional",
                    source_type="synthetic",
                    source_ref="memory_note_001",
                    evidence_count=1,
                    confidence_level="low",
                    user_visible_summary="memory continuity metadata",
                    operator_visible_summary="memory continuity metadata",
                    audit_note="synthetic example",
                ),
                build_state_continuity_item_v1(
                    item_id="item_operator_001",
                    category="operator_visible_state",
                    scope="operator_scoped",
                    owner_user_scope="operator",
                    tenant_account_scope="self",
                    status="active_metadata_only",
                    source_type="synthetic",
                    source_ref="operator_note_001",
                    evidence_count=1,
                    confidence_level="high",
                    visibility="operator_visible",
                    update_authority="operator_review_required",
                    user_visible_summary="operator-visible governance metadata",
                    operator_visible_summary="operator-visible governance metadata",
                    audit_note="synthetic review metadata",
                ),
            ],
            limitations=["synthetic example"],
            governed_metadata_only=False,
        ),
        build_state_continuity_packet_v1(
            packet_id="state_continuity_example_002",
            owner_user_scope="operator",
            tenant_account_scope="system",
            active_project_id="project_beta",
            active_session_id="session_beta",
            items=[
                build_state_continuity_item_v1(
                    item_id="item_candidate_001",
                    category="learning_candidate_pattern_state",
                    scope="system_wide_candidate",
                    owner_user_scope="operator",
                    tenant_account_scope="system",
                    project_id="project_beta",
                    status="proposed",
                    source_type="synthetic",
                    source_ref="candidate_pattern_001",
                    evidence_count=4,
                    confidence_level="medium",
                    update_authority="operator_review_required",
                    user_visible_summary="candidate pattern metadata",
                    operator_visible_summary="candidate pattern metadata",
                    audit_note="operator review metadata for candidate pattern",
                    governed_metadata_only=True,
                ),
                build_state_continuity_item_v1(
                    item_id="item_support_001",
                    category="escalation_support_state",
                    scope="project_scoped",
                    owner_user_scope="operator",
                    tenant_account_scope="system",
                    project_id="project_beta",
                    status="pending_approval",
                    source_type="synthetic",
                    source_ref="support_note_001",
                    evidence_count=1,
                    confidence_level="low",
                    blocked_reason="needs operator review",
                    user_visible_summary="escalation and support metadata",
                    operator_visible_summary="escalation and support metadata",
                    audit_note="synthetic support escalation",
                ),
            ],
            limitations=["synthetic example", "operator review metadata only"],
            governed_metadata_only=True,
        ),
    ]
    return [to_state_continuity_json_safe_v1(example) for example in examples]
