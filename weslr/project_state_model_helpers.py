"""Metadata-only project state helpers v1."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "project_state_model_v1"
PACKET_TYPE_V1 = "project_state_model_packet_v1"

_ALLOWED_STATUSES_V1 = (
    "proposed",
    "provisional",
    "active_metadata_only",
    "pending_approval",
    "blocked",
    "stale",
    "contradicted",
    "invalidated",
    "archived_deprecated",
    "failed",
)

_ALLOWED_PHASES_V1 = (
    "intake",
    "clarification",
    "planning",
    "research",
    "drafting",
    "review",
    "blocked",
    "paused",
    "archived",
)

_ALLOWED_SCOPES_V1 = (
    "project_scoped",
    "user_scoped",
    "tenant_account_scoped",
    "operator_scoped",
)

_DENIED_AUTHORITY_FIELDS_V1 = (
    "runtime_wiring_authority",
    "chat_" "responder_authority",
    "storage_database_authority",
    "weslr_io_authority",
    "project_state_persistence_authority",
    "project_state_mutation_authority",
    "memory_mutation_authority",
    "external_action_authority",
    "cross_user_leakage_authority",
    "hidden_project_state_authority",
    "hidden_personalization_authority",
    "public_product_readiness_authority",
)

_CORE_ITEM_FIELDS_V1 = (
    "schema_version",
    "project_id",
    "item_id",
    "owner_user_scope",
    "tenant_account_scope",
    "session_id",
    "project_status",
    "project_phase",
    "state_kind",
    "title",
    "summary",
    "goal",
    "open_questions",
    "constraints",
    "decisions",
    "tasks",
    "blocked_items",
    "linked_memory_refs",
    "linked_artifact_refs",
    "linked_support_refs",
    "source_type",
    "source_ref",
    "visibility",
    "correction_path",
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
    "items",
    "counts",
    "project_summary",
    "open_questions",
    "constraints",
    "decisions",
    "tasks",
    "blocked_items",
    "pending_approvals",
    "stale_items",
    "contradicted_items",
    "invalidated_items",
    "linked_memory_refs",
    "linked_artifact_refs",
    "linked_support_refs",
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


def _is_cross_user_like(*values: Any) -> bool:
    text = " ".join(_compact_text(value, default="").lower() for value in values)
    markers = ("shared", "system", "cross-user", "cross user", "global", "tenant-wide", "account-wide", "workspace-wide", "org-wide")
    return any(marker in text for marker in markers)


def _default_status_for_phase(phase: str) -> str:
    return {
        "intake": "proposed",
        "clarification": "proposed",
        "planning": "provisional",
        "research": "provisional",
        "drafting": "active_metadata_only",
        "review": "pending_approval",
        "blocked": "blocked",
        "paused": "stale",
        "archived": "archived_deprecated",
    }.get(phase, "active_metadata_only")


def _default_visibility_for_scope(scope: str) -> str:
    return scope if scope in _ALLOWED_SCOPES_V1 else "project_scoped"


def _default_summary_for_item(phase: str, status: str) -> str:
    return f"project state {phase} ({status})"


def _build_denied_authority() -> dict[str, Any]:
    return _normalize_denied_authority()


def allowed_project_state_statuses_v1() -> tuple[str, ...]:
    return _ALLOWED_STATUSES_V1


def allowed_project_state_phases_v1() -> tuple[str, ...]:
    return _ALLOWED_PHASES_V1


def allowed_project_state_scopes_v1() -> tuple[str, ...]:
    return _ALLOWED_SCOPES_V1


def build_project_state_item_v1(
    *,
    project_id: Any = None,
    item_id: Any = None,
    owner_user_scope: Any = "",
    tenant_account_scope: Any = "",
    session_id: Any = "",
    project_status: Any = None,
    project_phase: Any = None,
    state_kind: Any = "project_state",
    title: Any = "",
    summary: Any = None,
    goal: Any = "",
    open_questions: Any = None,
    constraints: Any = None,
    decisions: Any = None,
    tasks: Any = None,
    blocked_items: Any = None,
    linked_memory_refs: Any = None,
    linked_artifact_refs: Any = None,
    linked_support_refs: Any = None,
    source_type: Any = "synthetic",
    source_ref: Any = None,
    visibility: Any = None,
    correction_path: Any = "review_and_refresh",
    stale: Any = False,
    contradicted: Any = False,
    invalidated: Any = False,
    pending_approval: Any = False,
    blocked_reason: Any = "",
    audit_note: Any = "",
    created_marker: Any = None,
    updated_marker: Any = None,
    denied_authority: Any = None,
) -> dict[str, Any]:
    project_id_text = _compact_text(project_id)
    item_id_text = _compact_text(item_id)
    owner_text = _compact_text(owner_user_scope)
    tenant_text = _compact_text(tenant_account_scope)
    session_text = _compact_text(session_id)
    phase_text = _compact_text(project_phase) or "intake"
    status_text = _compact_text(project_status) or _default_status_for_phase(phase_text)
    state_kind_text = _compact_text(state_kind, default="project_state")
    title_text = _compact_text(title)
    goal_text = _compact_text(goal)
    summary_text = _compact_text(summary) or _default_summary_for_item(phase_text, status_text)
    source_type_text = _compact_text(source_type, default="synthetic")
    source_ref_text = _compact_text(source_ref)
    visibility_text = _compact_text(visibility) or _default_visibility_for_scope("project_scoped")
    correction_path_text = _compact_text(correction_path, default="review_and_refresh")
    blocked_reason_text = _compact_text(blocked_reason)
    audit_note_text = _compact_text(audit_note)
    created_marker_text = _compact_text(created_marker)
    updated_marker_text = _compact_text(updated_marker)
    seed = {
        "project_id": project_id_text,
        "item_id": item_id_text,
        "owner_user_scope": owner_text,
        "tenant_account_scope": tenant_text,
        "session_id": session_text,
        "project_status": status_text,
        "project_phase": phase_text,
        "state_kind": state_kind_text,
        "title": title_text,
        "source_ref": source_ref_text,
    }
    item = {
        "schema_version": SCHEMA_VERSION_V1,
        "project_id": project_id_text or _stable_marker("project", seed),
        "item_id": item_id_text or _stable_marker("project_item", seed),
        "owner_user_scope": owner_text,
        "tenant_account_scope": tenant_text,
        "session_id": session_text,
        "project_status": status_text,
        "project_phase": phase_text,
        "state_kind": state_kind_text or "project_state",
        "title": title_text or summary_text,
        "summary": summary_text,
        "goal": goal_text,
        "open_questions": _json_safe(_listify(open_questions)),
        "constraints": _json_safe(_listify(constraints)),
        "decisions": _json_safe(_listify(decisions)),
        "tasks": _json_safe(_listify(tasks)),
        "blocked_items": _json_safe(_listify(blocked_items)),
        "linked_memory_refs": _json_safe(_listify(linked_memory_refs)),
        "linked_artifact_refs": _json_safe(_listify(linked_artifact_refs)),
        "linked_support_refs": _json_safe(_listify(linked_support_refs)),
        "source_type": source_type_text,
        "source_ref": source_ref_text or _stable_marker("project_source", seed),
        "visibility": visibility_text,
        "correction_path": correction_path_text,
        "stale": bool(stale),
        "contradicted": bool(contradicted),
        "invalidated": bool(invalidated),
        "pending_approval": bool(pending_approval),
        "blocked_reason": blocked_reason_text,
        "audit_note": audit_note_text,
        "created_marker": created_marker_text or _stable_marker("created", seed),
        "updated_marker": updated_marker_text or _stable_marker("updated", {**seed, "created_marker": created_marker_text}),
        "denied_authority": _build_denied_authority() if denied_authority is None else _normalize_denied_authority(denied_authority),
    }
    return _json_safe(item)


def _item_has_text(item: Mapping[str, Any], field: str) -> bool:
    return field in item and _has_text(item.get(field))


def validate_project_state_item_v1(item: Any) -> dict[str, Any]:
    violations: list[str] = []
    if not isinstance(item, Mapping):
        violations.append("item must be a mapping")
        return {"valid": False, "violation_count": len(violations), "violations": violations, "classification": {"status": "unknown", "phase": "unknown", "scope": "unknown", "risk": "blocked"}}

    item = _json_safe(copy.deepcopy(item))

    for field in _CORE_ITEM_FIELDS_V1:
        if field not in item:
            violations.append(f"missing field: {field}")

    if not _item_has_text(item, "schema_version"):
        violations.append("schema_version missing or blank")
    elif _compact_text(item.get("schema_version")) != SCHEMA_VERSION_V1:
        violations.append("schema_version mismatch")

    project_id = _compact_text(item.get("project_id"))
    item_id = _compact_text(item.get("item_id"))
    owner = _compact_text(item.get("owner_user_scope"))
    tenant = _compact_text(item.get("tenant_account_scope"))
    session_id = _compact_text(item.get("session_id"))
    status = _compact_text(item.get("project_status"))
    phase = _compact_text(item.get("project_phase"))
    state_kind = _compact_text(item.get("state_kind"))
    source_type = _compact_text(item.get("source_type"))
    source_ref = _compact_text(item.get("source_ref"))
    visibility = _compact_text(item.get("visibility"))
    correction_path = _compact_text(item.get("correction_path"))
    blocked_reason = _compact_text(item.get("blocked_reason"))
    audit_note = _compact_text(item.get("audit_note"))

    if not _has_text(project_id):
        violations.append("project_id missing or blank")
    if not _has_text(item_id):
        violations.append("item_id missing or blank")
    if not _has_text(status):
        violations.append("project_status missing or blank")
    if not _has_text(phase):
        violations.append("project_phase missing or blank")
    if not _has_text(state_kind):
        violations.append("state_kind missing or blank")
    if not _has_text(source_type):
        violations.append("source_type missing or blank")
    if not _has_text(source_ref):
        violations.append("source_ref missing or blank")
    if not _has_text(visibility):
        violations.append("visibility missing or blank")
    elif visibility not in _ALLOWED_SCOPES_V1:
        violations.append(f"unknown scope: {visibility or '<blank>'}")
    if not _has_text(correction_path):
        violations.append("correction_path missing or blank")
    if not _has_text(_compact_text(item.get("title"))):
        violations.append("title missing or blank")
    if not _has_text(_compact_text(item.get("summary"))):
        violations.append("summary missing or blank")
    if not _has_text(_compact_text(item.get("goal"))):
        violations.append("goal missing or blank")

    if status not in _ALLOWED_STATUSES_V1:
        violations.append(f"unknown status: {status or '<blank>'}")
    if phase not in _ALLOWED_PHASES_V1:
        violations.append(f"unknown phase: {phase or '<blank>'}")
    if state_kind not in {"project_state", "project_context", "project_frame"}:
        violations.append(f"unknown state_kind: {state_kind or '<blank>'}")

    if phase in {"intake", "clarification", "planning", "research", "drafting", "review", "blocked", "paused", "archived"} and status == "failed" and not _has_text(blocked_reason):
        violations.append("failed project state requires blocked_reason or failure reason")

    if status == "blocked" and not _has_text(blocked_reason):
        violations.append("blocked project state requires blocked_reason")
    if status == "pending_approval" and not bool(item.get("pending_approval")):
        violations.append("pending approval state must remain visible")
    if status == "stale" and not bool(item.get("stale")):
        violations.append("stale status must surface stale=true")
    if status == "contradicted" and not bool(item.get("contradicted")):
        violations.append("contradicted status must surface contradicted=true")
    if status == "invalidated" and not bool(item.get("invalidated")):
        violations.append("invalidated status must surface invalidated=true")
    if bool(item.get("stale")) and status not in {"stale", "archived_deprecated", "contradicted", "invalidated"}:
        violations.append("stale state must be surfaced in status")
    if bool(item.get("contradicted")) and status not in {"contradicted", "invalidated", "archived_deprecated"}:
        violations.append("contradicted state cannot drive action")
    if bool(item.get("invalidated")) and status not in {"invalidated", "archived_deprecated"}:
        violations.append("invalidated state cannot be active")

    if phase == "blocked" and status != "blocked":
        violations.append("blocked phase requires blocked status")
    if phase == "paused" and status not in {"stale", "archived_deprecated", "provisional", "active_metadata_only"}:
        violations.append("paused phase must not present as active execution")
    if phase == "archived" and status not in {"archived_deprecated", "stale"}:
        violations.append("archived phase must surface archived or stale status")

    if _is_cross_user_like(project_id, owner, tenant, session_id, _compact_text(item.get("title")), _compact_text(item.get("summary"))):
        violations.append("cross-user project state fails closed")

    if visibility == "project_scoped" and not project_id:
        violations.append("project_scoped project state requires project_id")
    if visibility == "user_scoped" and not owner:
        violations.append("user_scoped project state requires owner_user_scope")
    if visibility == "tenant_account_scoped" and not tenant:
        violations.append("tenant_account_scoped project state requires tenant_account_scope")
    if visibility == "operator_scoped" and not _has_text(audit_note):
        violations.append("operator-visible project state requires audit_note")

    if not _has_text(item.get("open_questions")) and not isinstance(item.get("open_questions"), list):
        violations.append("open_questions must be list-like")
    if not isinstance(item.get("constraints"), list):
        violations.append("constraints must be list-like")
    if not isinstance(item.get("decisions"), list):
        violations.append("decisions must be list-like")
    if not isinstance(item.get("tasks"), list):
        violations.append("tasks must be list-like")
    if not isinstance(item.get("blocked_items"), list):
        violations.append("blocked_items must be list-like")
    if not isinstance(item.get("linked_memory_refs"), list):
        violations.append("linked_memory_refs must be list-like")
    if not isinstance(item.get("linked_artifact_refs"), list):
        violations.append("linked_artifact_refs must be list-like")
    if not isinstance(item.get("linked_support_refs"), list):
        violations.append("linked_support_refs must be list-like")

    if _safe_int(item.get("evidence_count", 0), 0) < 0:
        violations.append("evidence_count must be zero or greater")
    if not isinstance(item.get("stale"), bool):
        violations.append("stale must be boolean")
    if not isinstance(item.get("contradicted"), bool):
        violations.append("contradicted must be boolean")
    if not isinstance(item.get("invalidated"), bool):
        violations.append("invalidated must be boolean")
    if not isinstance(item.get("pending_approval"), bool):
        violations.append("pending_approval must be boolean")

    denied = item.get("denied_authority")
    if not isinstance(denied, Mapping):
        violations.append("denied_authority must be a mapping")
    else:
        for field in _DENIED_AUTHORITY_FIELDS_V1:
            if field not in denied:
                violations.append(f"denied_authority missing {field}")
            elif denied.get(field) not in (False, 0, None, "blocked"):
                violations.append(f"denied_authority {field} must be false or blocked")

    if item.get("project_status") == "failed" and not _has_text(blocked_reason):
        violations.append("failed project state requires blocked_reason")
    if item.get("project_phase") == "blocked" and not _has_text(blocked_reason):
        violations.append("blocked phase requires blocked_reason")
    if not _has_text(item.get("created_marker")):
        violations.append("created_marker missing or blank")
    if not _has_text(item.get("updated_marker")):
        violations.append("updated_marker missing or blank")

    classification = classify_project_state_item_v1(item)
    valid = len(violations) == 0
    classification["risk"] = classification.get("risk", "blocked") if not valid else classification.get("risk", "metadata_only")
    return {"valid": valid, "violation_count": len(violations), "violations": violations, "classification": classification}


def classify_project_state_item_v1(item: Any) -> dict[str, Any]:
    normalized = _json_safe(copy.deepcopy(item)) if isinstance(item, Mapping) else {"project_status": "unknown", "project_phase": "unknown", "visibility": "unknown"}
    status = _compact_text(normalized.get("project_status"), default="unknown")
    phase = _compact_text(normalized.get("project_phase"), default="unknown")
    scope = _compact_text(normalized.get("visibility"), default="unknown")
    risk = "metadata_only"
    if status in {"blocked", "invalidated", "contradicted", "failed"}:
        risk = "blocked"
    elif status in {"pending_approval", "proposed", "provisional", "stale", "archived_deprecated"}:
        risk = "review_required"
    return {
        "status": status if status in _ALLOWED_STATUSES_V1 else "unknown",
        "phase": phase if phase in _ALLOWED_PHASES_V1 else "unknown",
        "scope": scope if scope in _ALLOWED_SCOPES_V1 else "unknown",
        "risk": risk,
        "item": _json_safe(normalized),
    }


def _ensure_items(value: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for entry in _listify(value):
        if isinstance(entry, Mapping):
            items.append(_json_safe(entry))
        else:
            items.append(build_project_state_item_v1(title=entry, summary=entry, goal=entry, source_ref=entry))
    return items


def build_project_state_packet_v1(
    *,
    packet_id: Any = None,
    packet_type: Any = PACKET_TYPE_V1,
    owner_user_scope: Any = "",
    tenant_account_scope: Any = "",
    active_project_id: Any = "",
    items: Any = None,
    limitations: Any = None,
    denied_authority: Any = None,
) -> dict[str, Any]:
    items_list = _ensure_items(items)
    project_id_text = _compact_text(active_project_id)
    owner_text = _compact_text(owner_user_scope)
    tenant_text = _compact_text(tenant_account_scope)
    packet_seed = {
        "packet_id": _compact_text(packet_id),
        "packet_type": _compact_text(packet_type, default=PACKET_TYPE_V1),
        "owner_user_scope": owner_text,
        "tenant_account_scope": tenant_text,
        "active_project_id": project_id_text,
    }
    open_questions = []
    constraints = []
    decisions = []
    tasks = []
    blocked_items = []
    pending_approvals = []
    stale_items = []
    contradicted_items = []
    invalidated_items = []
    linked_memory_refs = []
    linked_artifact_refs = []
    linked_support_refs = []
    for item in items_list:
        open_questions.extend(_listify(item.get("open_questions")))
        constraints.extend(_listify(item.get("constraints")))
        decisions.extend(_listify(item.get("decisions")))
        tasks.extend(_listify(item.get("tasks")))
        blocked_items.extend(_listify(item.get("blocked_items")))
        if item.get("project_status") == "blocked" or item.get("blocked_reason"):
            blocked_items.append(item.get("item_id"))
        linked_memory_refs.extend(_listify(item.get("linked_memory_refs")))
        linked_artifact_refs.extend(_listify(item.get("linked_artifact_refs")))
        linked_support_refs.extend(_listify(item.get("linked_support_refs")))
        if item.get("pending_approval") or item.get("project_status") == "pending_approval":
            pending_approvals.append(item.get("item_id"))
        if item.get("stale") or item.get("project_status") == "stale":
            stale_items.append(item.get("item_id"))
        if item.get("contradicted") or item.get("project_status") == "contradicted":
            contradicted_items.append(item.get("item_id"))
        if item.get("invalidated") or item.get("project_status") == "invalidated":
            invalidated_items.append(item.get("item_id"))

    counts = {
        "item_count": len(items_list),
        "blocked_count": len(blocked_items),
        "pending_count": len(pending_approvals),
        "stale_count": len(stale_items),
        "contradicted_count": len(contradicted_items),
        "invalidated_count": len(invalidated_items),
    }

    project_summary = _compact_text(items_list[0].get("summary")) if items_list else f"project state packet {project_id_text or packet_seed['packet_id']}"
    packet = {
        "schema_version": SCHEMA_VERSION_V1,
        "packet_id": _compact_text(packet_id) or _stable_marker("project_packet", packet_seed),
        "packet_type": _compact_text(packet_type, default=PACKET_TYPE_V1),
        "owner_user_scope": owner_text,
        "tenant_account_scope": tenant_text,
        "active_project_id": project_id_text or _stable_marker("project_active", packet_seed),
        "items": _json_safe(items_list),
        "counts": _json_safe(counts),
        "project_summary": project_summary,
        "open_questions": _json_safe(open_questions),
        "constraints": _json_safe(constraints),
        "decisions": _json_safe(decisions),
        "tasks": _json_safe(tasks),
        "blocked_items": _json_safe(blocked_items),
        "pending_approvals": _json_safe(pending_approvals),
        "stale_items": _json_safe(stale_items),
        "contradicted_items": _json_safe(contradicted_items),
        "invalidated_items": _json_safe(invalidated_items),
        "linked_memory_refs": _json_safe(linked_memory_refs),
        "linked_artifact_refs": _json_safe(linked_artifact_refs),
        "linked_support_refs": _json_safe(linked_support_refs),
        "limitations": _json_safe(_listify(limitations)),
        "denied_authority": _normalize_denied_authority(denied_authority),
    }
    return _json_safe(packet)


def validate_project_state_packet_v1(packet: Any) -> dict[str, Any]:
    violations: list[str] = []
    if not isinstance(packet, Mapping):
        violations.append("packet must be a mapping")
        return {"valid": False, "violation_count": len(violations), "violations": violations, "classification": {"packet_type": "unknown", "risk": "blocked"}}

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
    active_project_id = _compact_text(packet.get("active_project_id"))

    if not _has_text(packet_id):
        violations.append("packet_id missing or blank")
    if packet_type not in {PACKET_TYPE_V1, "project_state_model_packet", "project_state_packet"}:
        violations.append(f"unknown packet_type: {packet_type or '<blank>'}")
    if not _has_text(owner):
        violations.append("owner_user_scope missing or blank")
    if not _has_text(tenant):
        violations.append("tenant_account_scope missing or blank")
    if not _has_text(active_project_id):
        violations.append("active_project_id missing or blank")

    items = packet.get("items")
    if not isinstance(items, list):
        violations.append("items must be a list")
        items = []

    if not isinstance(packet.get("counts"), Mapping):
        violations.append("counts must be a mapping")
    if not isinstance(packet.get("open_questions"), list):
        violations.append("open_questions must be a list")
    if not isinstance(packet.get("constraints"), list):
        violations.append("constraints must be a list")
    if not isinstance(packet.get("decisions"), list):
        violations.append("decisions must be a list")
    if not isinstance(packet.get("tasks"), list):
        violations.append("tasks must be a list")
    if not isinstance(packet.get("blocked_items"), list):
        violations.append("blocked_items must be a list")
    if not isinstance(packet.get("pending_approvals"), list):
        violations.append("pending_approvals must be a list")
    if not isinstance(packet.get("stale_items"), list):
        violations.append("stale_items must be a list")
    if not isinstance(packet.get("contradicted_items"), list):
        violations.append("contradicted_items must be a list")
    if not isinstance(packet.get("invalidated_items"), list):
        violations.append("invalidated_items must be a list")
    if not isinstance(packet.get("linked_memory_refs"), list):
        violations.append("linked_memory_refs must be a list")
    if not isinstance(packet.get("linked_artifact_refs"), list):
        violations.append("linked_artifact_refs must be a list")
    if not isinstance(packet.get("linked_support_refs"), list):
        violations.append("linked_support_refs must be a list")
    if not isinstance(packet.get("limitations"), list):
        violations.append("limitations must be a list")

    if _is_cross_user_like(active_project_id, owner, tenant):
        violations.append("cross-user project packet fails closed")

    for item in items:
        item_result = validate_project_state_item_v1(item)
        if not item_result["valid"]:
            violations.append(f"item invalid: {item_result['violations'][0]}")

    denied = packet.get("denied_authority")
    if not isinstance(denied, Mapping):
        violations.append("denied_authority must be a mapping")
    else:
        for field in _DENIED_AUTHORITY_FIELDS_V1:
            if field not in denied:
                violations.append(f"denied_authority missing {field}")
            elif denied.get(field) not in (False, 0, None, "blocked"):
                violations.append(f"denied_authority {field} must be false or blocked")

    classification = {"packet_type": packet_type, "risk": "blocked" if violations else "metadata_only"}
    return {"valid": len(violations) == 0, "violation_count": len(violations), "violations": violations, "classification": classification}


def summarize_project_state_packet_v1(packet: Any) -> dict[str, Any]:
    normalized = _json_safe(copy.deepcopy(packet)) if isinstance(packet, Mapping) else {}
    items = _listify(normalized.get("items")) if isinstance(normalized, Mapping) else []
    counts = normalized.get("counts", {}) if isinstance(normalized, Mapping) else {}
    summary = {
        "packet_id": _compact_text(normalized.get("packet_id")) if isinstance(normalized, Mapping) else "",
        "packet_type": _compact_text(normalized.get("packet_type")) if isinstance(normalized, Mapping) else "",
        "project_summary": _compact_text(normalized.get("project_summary")) if isinstance(normalized, Mapping) else "",
        "item_count": _safe_int(counts.get("item_count") if isinstance(counts, Mapping) else len(items), len(items)),
        "blocked_count": _safe_int(counts.get("blocked_count") if isinstance(counts, Mapping) else 0, 0),
        "pending_count": _safe_int(counts.get("pending_count") if isinstance(counts, Mapping) else 0, 0),
        "stale_count": _safe_int(counts.get("stale_count") if isinstance(counts, Mapping) else 0, 0),
        "contradicted_count": _safe_int(counts.get("contradicted_count") if isinstance(counts, Mapping) else 0, 0),
        "invalidated_count": _safe_int(counts.get("invalidated_count") if isinstance(counts, Mapping) else 0, 0),
        "open_questions": _json_safe(_listify(normalized.get("open_questions"))) if isinstance(normalized, Mapping) else [],
        "constraints": _json_safe(_listify(normalized.get("constraints"))) if isinstance(normalized, Mapping) else [],
        "decisions": _json_safe(_listify(normalized.get("decisions"))) if isinstance(normalized, Mapping) else [],
        "tasks": _json_safe(_listify(normalized.get("tasks"))) if isinstance(normalized, Mapping) else [],
        "blocked_items": _json_safe(_listify(normalized.get("blocked_items"))) if isinstance(normalized, Mapping) else [],
        "pending_approvals": _json_safe(_listify(normalized.get("pending_approvals"))) if isinstance(normalized, Mapping) else [],
        "stale_items": _json_safe(_listify(normalized.get("stale_items"))) if isinstance(normalized, Mapping) else [],
        "contradicted_items": _json_safe(_listify(normalized.get("contradicted_items"))) if isinstance(normalized, Mapping) else [],
        "invalidated_items": _json_safe(_listify(normalized.get("invalidated_items"))) if isinstance(normalized, Mapping) else [],
        "linked_memory_refs": _json_safe(_listify(normalized.get("linked_memory_refs"))) if isinstance(normalized, Mapping) else [],
        "linked_artifact_refs": _json_safe(_listify(normalized.get("linked_artifact_refs"))) if isinstance(normalized, Mapping) else [],
        "linked_support_refs": _json_safe(_listify(normalized.get("linked_support_refs"))) if isinstance(normalized, Mapping) else [],
        "limitations": _json_safe(_listify(normalized.get("limitations"))) if isinstance(normalized, Mapping) else [],
    }
    return _json_safe(summary)


def to_project_state_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def build_initial_project_state_examples_v1() -> list[dict[str, Any]]:
    items = [
        build_project_state_item_v1(
            project_id="project_alpha",
            item_id="project_alpha_intake",
            owner_user_scope="operator",
            tenant_account_scope="self",
            session_id="session_alpha",
            project_status="proposed",
            project_phase="intake",
            title="Project Alpha",
            goal="synthetic continuity",
            summary="Initial project framing metadata",
            open_questions=["What is the safe next step?"],
            constraints=["No runtime wiring"],
            decisions=["Use metadata-only helpers"],
            tasks=["review project state"],
            linked_memory_refs=["memory_ref_alpha"],
            linked_artifact_refs=["artifact_ref_alpha"],
            linked_support_refs=["support_ref_alpha"],
            source_ref="synthetic_intake",
            audit_note="synthetic example metadata",
        ),
        build_project_state_item_v1(
            project_id="project_alpha",
            item_id="project_alpha_review",
            owner_user_scope="operator",
            tenant_account_scope="self",
            session_id="session_alpha",
            project_status="pending_approval",
            project_phase="review",
            title="Project Alpha Review",
            goal="safe review metadata",
            summary="Review checkpoint metadata",
            open_questions=["Approve the next safe step?"],
            constraints=["Await confirmation"],
            decisions=["Hold pending approval"],
            tasks=["await operator review"],
            linked_memory_refs=["memory_ref_alpha_review"],
            linked_artifact_refs=["artifact_ref_alpha_review"],
            linked_support_refs=["support_ref_alpha_review"],
            source_ref="synthetic_review",
            audit_note="synthetic example metadata",
            pending_approval=True,
        ),
    ]
    packet = build_project_state_packet_v1(
        packet_id="project_alpha_packet",
        owner_user_scope="operator",
        tenant_account_scope="self",
        active_project_id="project_alpha",
        items=items,
        limitations=["synthetic example"],
    )
    return [packet, {"items": items, "summary": summarize_project_state_packet_v1(packet), "synthetic": True}]
