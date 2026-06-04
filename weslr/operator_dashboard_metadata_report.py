#!/usr/bin/env python3
"""WESLR operator dashboard metadata report helpers V1.

Metadata-only helpers for operator dashboard reporting. These helpers build,
validate, summarize, and normalize dashboard-relevant metadata without UI,
backend, runtime wiring, storage, or action execution.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict, Iterable, Mapping, Sequence

SCHEMA_VERSION_V1 = "operator_dashboard_metadata_report_v1"
REPORT_TYPE_V1 = "operator_dashboard_metadata_report_v1"
SECTION_NAMES_V1 = (
    "overview",
    "approvals_queue",
    "blocked_actions",
    "project_state",
    "memory_state",
    "first_tool_lane_contracts",
    "support_escalation",
    "audit_trail",
    "rollback_deprecation",
    "validation_release_status",
    "incident_risk_flags",
    "lane_expansion_candidates",
)

_DENIED_AUTHORITY_FIELDS = (
    "ui_implementation_authority",
    "backend_api_authority",
    "runtime_wiring_authority",
    "live_dashboard_authority",
    "operator_control_execution_authority",
    "tool_execution_authority",
    "storage_database_authority",
    "memory_mutation_authority",
    "project_state_mutation_authority",
    "cross_user_browsing_authority",
    "raw_private_data_dump_authority",
    "public_product_readiness_authority",
    "behavior_pack_promotion_authority",
)

_REQUIRED_TOP_LEVEL_FIELDS = (
    "schema_version",
    "report_id",
    "report_type",
    "generated_marker",
    "owner_operator_scope",
    "tenant_account_scope",
    "source_scope",
    "sections",
    "counts",
    "risk_flags",
    "blocked_items",
    "pending_approvals",
    "stale_or_contradicted_items",
    "validation_status",
    "protected_file_status",
    "release_gate_status",
    "release_check_status",
    "operator_notes",
    "limitations",
    "denied_authority",
)

_REQUIRED_SECTION_FIELDS = {
    "overview": (),
    "approvals_queue": (
        "approval_id",
        "owner_user_scope",
        "tenant_account_scope",
        "lane_id",
        "action_class",
        "requested_action",
        "risk_level",
        "required_approval_type",
        "approval_status",
        "source_provenance",
        "user_visible_summary",
    ),
    "blocked_actions": (
        "blocked_reason",
        "boundary_triggered",
        "lane_id",
        "action_class",
        "affected_item",
        "user_visible_blocked_phrase",
        "source_provenance",
    ),
    "project_state": (
        "project_id",
        "owner_user_scope",
        "tenant_account_scope",
        "project_status",
        "project_phase",
        "source_provenance",
    ),
    "memory_state": (
        "memory_id",
        "scope",
        "status",
        "type",
        "source_provenance",
    ),
    "first_tool_lane_contracts": (
        "lane_id",
        "action_class",
        "approval_status",
        "execution_status",
        "risk_level",
        "denied_authority",
        "operator_visibility",
        "user_visible_status_phrase",
        "source_provenance",
    ),
    "support_escalation": (
        "support_escalation_id",
        "reason",
        "owner_user_scope",
        "tenant_account_scope",
        "status",
        "last_safe_step",
        "source_provenance",
    ),
    "audit_trail": (
        "initiator",
        "marker",
        "scope",
        "reason",
        "source_provenance",
    ),
    "rollback_deprecation": (
        "source_provenance",
    ),
    "validation_release_status": (
        "latest_validation_status",
        "release_gate_status",
        "release_check_status",
        "protected_file_status",
        "allowed_file_scope",
        "source_provenance",
    ),
    "incident_risk_flags": (
        "flag",
        "scope",
        "source_provenance",
    ),
    "lane_expansion_candidates": (
        "candidate_id",
        "summary",
        "source_provenance",
    ),
}

_SECTION_HINTS = {
    "approvals_queue": ("approval_id",),
    "blocked_actions": ("blocked_reason", "boundary_triggered"),
    "project_state": ("project_id", "project_status"),
    "memory_state": ("memory_id", "status", "type"),
    "first_tool_lane_contracts": ("lane_id", "execution_status", "approval_status"),
    "support_escalation": ("support_escalation_id", "last_safe_step"),
    "audit_trail": ("initiator", "marker"),
    "rollback_deprecation": ("rollback_availability", "deprecation_status"),
    "validation_release_status": ("release_gate_status", "release_check_status"),
    "incident_risk_flags": ("flag",),
    "lane_expansion_candidates": ("candidate_id",),
}


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


def _compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        text = " ".join(value.split())
        return text if text else default
    return _compact_text(str(value), default=default)


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


def _stable_marker(prefix: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def _is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def _normalize_item(item: Any) -> Dict[str, Any]:
    if _is_mapping(item):
        return {str(key): _json_safe(val) for key, val in item.items()}
    if item is None:
        return {}
    return {"value": _compact_text(item)}


def _normalize_items(items: Any) -> list[Dict[str, Any]]:
    return [_normalize_item(item) for item in _listify(items)]


def _scope_text(value: Any) -> str:
    return _compact_text(value, default="").lower()


def _is_governed_metadata_only(packet: Mapping[str, Any]) -> bool:
    return bool(packet.get("governed_metadata_only"))


def _scope_requires_governance(*values: Any) -> bool:
    text = " ".join(_scope_text(value) for value in values)
    markers = (
        "shared",
        "system",
        "cross-user",
        "cross user",
        "global",
        "tenant",
        "account-wide",
        "workspace-wide",
        "org-wide",
    )
    return any(marker in text for marker in markers)


def _summary_from_item(item: Mapping[str, Any], keys: Sequence[str]) -> Dict[str, Any]:
    summary = {}
    for key in keys:
        if key in item:
            summary[key] = _json_safe(item[key])
    return summary


def _ensure_section_list(value: Any) -> list[Dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_normalize_item(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize_item(item) for item in value]
    if isinstance(value, set):
        return [_normalize_item(item) for item in sorted(value, key=repr)]
    if _is_mapping(value):
        return [_normalize_item(value)]
    return [_normalize_item({"value": value})]


def _has_text(value: Any) -> bool:
    return bool(_compact_text(value, default=""))


def _is_false_like(value: Any) -> bool:
    return value in (False, 0, "", None)


def _is_blocked_authority(value: Any) -> bool:
    if isinstance(value, Mapping):
        if "allowed" in value:
            return not bool(value.get("allowed"))
        if "blocked" in value:
            return bool(value.get("blocked"))
        if "status" in value:
            return _compact_text(value.get("status")).lower() in {"blocked", "denied", "false", "no"}
        if value and all(_is_false_like(item) for item in value.values()):
            return True
    if isinstance(value, str):
        return _compact_text(value).lower() in {"blocked", "denied", "false", "no", "not allowed"}
    return bool(value) is False


def _item_has_all_fields(item: Mapping[str, Any], fields: Sequence[str]) -> bool:
    for field in fields:
        if field not in item:
            return False
        if field == "denied_authority":
            if not _is_blocked_authority(item.get(field)):
                return False
        elif field in {"operator_visibility"}:
            if item.get(field) is not True:
                return False
        else:
            if not _has_text(item.get(field)):
                return False
    return True


def _item_missing_fields(item: Mapping[str, Any], fields: Sequence[str]) -> list[str]:
    missing = []
    for field in fields:
        if field not in item:
            missing.append(field)
            continue
        value = item.get(field)
        if field == "denied_authority":
            if not _is_blocked_authority(value):
                missing.append(field)
        elif field in {"operator_visibility"}:
            if value is not True:
                missing.append(field)
        elif not _has_text(value):
            missing.append(field)
    return missing


def _calculate_counts(sections: Mapping[str, Any]) -> Dict[str, Any]:
    counts = {section: len(_ensure_section_list(sections.get(section))) for section in SECTION_NAMES_V1}
    approvals = _ensure_section_list(sections.get("approvals_queue"))
    blocked = _ensure_section_list(sections.get("blocked_actions"))
    projects = _ensure_section_list(sections.get("project_state"))
    memories = _ensure_section_list(sections.get("memory_state"))
    contracts = _ensure_section_list(sections.get("first_tool_lane_contracts"))
    support = _ensure_section_list(sections.get("support_escalation"))
    audit = _ensure_section_list(sections.get("audit_trail"))
    rollback = _ensure_section_list(sections.get("rollback_deprecation"))
    validation = _ensure_section_list(sections.get("validation_release_status"))
    risk = _ensure_section_list(sections.get("incident_risk_flags"))
    candidates = _ensure_section_list(sections.get("lane_expansion_candidates"))

    pending = [item for item in approvals if _compact_text(item.get("approval_status")).lower() not in {"approved_metadata_only", "not_required_internal_only"}]
    stale = [item for item in projects + memories if any(bool(item.get(flag)) for flag in ("stale", "contradicted", "invalidated", "stale_flag", "contradicted_flag", "invalidated_flag"))]
    blocked_items = [item for item in blocked if _has_text(item.get("blocked_reason"))] + [item for item in contracts if _compact_text(item.get("approval_status")).lower() == "blocked"]
    risk_flags = []
    for item in risk:
        flag = _compact_text(item.get("flag"), default="")
        if flag:
            risk_flags.append(flag)
    for item in contracts:
        for flag_key in ("external_action_requested", "destructive_action_requested", "third_party_action_requested", "runtime_activation_requested", "public_export_requested"):
            if item.get(flag_key) is True:
                risk_flags.append(flag_key)
    summary = {
        "total_sections": len(SECTION_NAMES_V1),
        "section_item_counts": counts,
        "total_items": sum(counts.values()),
        "pending_approvals_count": len(pending),
        "blocked_items_count": len(blocked_items),
        "stale_or_contradicted_count": len(stale),
        "risk_flag_count": len({flag for flag in risk_flags if flag}),
        "rollback_item_count": len(rollback),
        "validation_item_count": len(validation),
        "support_item_count": len(support),
        "audit_item_count": len(audit),
        "candidate_item_count": len(candidates),
    }
    summary.update(counts)
    return summary


def _build_denied_authority(overrides: Any = None) -> Dict[str, Any]:
    denied = {field: False for field in _DENIED_AUTHORITY_FIELDS}
    if _is_mapping(overrides):
        for field in _DENIED_AUTHORITY_FIELDS:
            if field in overrides:
                denied[field] = bool(overrides.get(field)) and False
    return denied


def _build_default_sections(overview: Any, approvals_queue: Any, blocked_actions: Any, project_state: Any, memory_state: Any, first_tool_lane_contracts: Any, support_escalation: Any, audit_trail: Any, rollback_deprecation: Any, validation_release_status: Any, incident_risk_flags: Any, lane_expansion_candidates: Any) -> Dict[str, list[Dict[str, Any]]]:
    return {
        "overview": _ensure_section_list(overview),
        "approvals_queue": _ensure_section_list(approvals_queue),
        "blocked_actions": _ensure_section_list(blocked_actions),
        "project_state": _ensure_section_list(project_state),
        "memory_state": _ensure_section_list(memory_state),
        "first_tool_lane_contracts": _ensure_section_list(first_tool_lane_contracts),
        "support_escalation": _ensure_section_list(support_escalation),
        "audit_trail": _ensure_section_list(audit_trail),
        "rollback_deprecation": _ensure_section_list(rollback_deprecation),
        "validation_release_status": _ensure_section_list(validation_release_status),
        "incident_risk_flags": _ensure_section_list(incident_risk_flags),
        "lane_expansion_candidates": _ensure_section_list(lane_expansion_candidates),
    }


def build_operator_dashboard_metadata_packet_v1(
    *,
    report_id: Any = None,
    report_type: Any = REPORT_TYPE_V1,
    generated_marker: Any = None,
    owner_operator_scope: Any = "operator",
    tenant_account_scope: Any = "self",
    source_scope: Any = "synthetic",
    overview: Any = None,
    approvals_queue: Any = None,
    blocked_actions: Any = None,
    project_state: Any = None,
    memory_state: Any = None,
    first_tool_lane_contracts: Any = None,
    support_escalation: Any = None,
    audit_trail: Any = None,
    rollback_deprecation: Any = None,
    validation_release_status: Any = None,
    incident_risk_flags: Any = None,
    lane_expansion_candidates: Any = None,
    operator_notes: Any = None,
    limitations: Any = None,
    denied_authority: Any = None,
    governed_metadata_only: bool = False,
    cross_user_view: bool = False,
    raw_private_data: Any = None,
) -> Dict[str, Any]:
    sections = _build_default_sections(
        overview,
        approvals_queue,
        blocked_actions,
        project_state,
        memory_state,
        first_tool_lane_contracts,
        support_escalation,
        audit_trail,
        rollback_deprecation,
        validation_release_status,
        incident_risk_flags,
        lane_expansion_candidates,
    )
    packet_seed = {
        "report_type": _compact_text(report_type, default=REPORT_TYPE_V1),
        "owner_operator_scope": _compact_text(owner_operator_scope, default="operator"),
        "tenant_account_scope": _compact_text(tenant_account_scope, default="self"),
        "source_scope": _compact_text(source_scope, default="synthetic"),
        "sections": sections,
        "governed_metadata_only": bool(governed_metadata_only),
        "cross_user_view": bool(cross_user_view),
    }
    packet_report_id = _compact_text(report_id, default="") or _stable_marker("operator_dashboard_report", packet_seed)
    packet_generated_marker = _compact_text(generated_marker, default="") or _stable_marker("generated", packet_seed)
    counts = _calculate_counts(sections)
    blocked_items = [
        _summary_from_item(item, ("lane_id", "action_class", "blocked_reason", "boundary_triggered", "approval_status", "source_provenance"))
        for item in sections["blocked_actions"]
        if _has_text(item.get("blocked_reason"))
    ]
    blocked_items.extend(
        _summary_from_item(item, ("lane_id", "action_class", "blocked_reason", "approval_status", "source_provenance"))
        for item in sections["first_tool_lane_contracts"]
        if _compact_text(item.get("approval_status")).lower() == "blocked"
    )
    pending_approvals = [
        _summary_from_item(item, ("approval_id", "lane_id", "action_class", "requested_action", "risk_level", "approval_status", "source_provenance"))
        for item in sections["approvals_queue"]
        if _compact_text(item.get("approval_status")).lower() not in {"approved_metadata_only", "not_required_internal_only"}
    ]
    stale_items = []
    for item in sections["project_state"] + sections["memory_state"]:
        if any(bool(item.get(flag)) for flag in ("stale", "contradicted", "invalidated", "stale_flag", "contradicted_flag", "invalidated_flag")):
            stale_items.append(_summary_from_item(item, ("project_id", "memory_id", "scope", "status", "type", "source_provenance")))
    risk_flags = []
    for item in sections["incident_risk_flags"]:
        flag = _compact_text(item.get("flag"), default="")
        if flag:
            risk_flags.append(flag)
    for item in sections["first_tool_lane_contracts"]:
        for flag_key in ("external_action_requested", "destructive_action_requested", "third_party_action_requested", "runtime_activation_requested", "public_export_requested"):
            if item.get(flag_key) is True:
                risk_flags.append(flag_key)
    if raw_private_data is not None:
        limitations = _listify(limitations) + ["raw private data redacted by default"]
    packet = {
        "schema_version": SCHEMA_VERSION_V1,
        "report_id": packet_report_id,
        "report_type": _compact_text(report_type, default=REPORT_TYPE_V1),
        "generated_marker": packet_generated_marker,
        "owner_operator_scope": _compact_text(owner_operator_scope, default="operator"),
        "tenant_account_scope": _compact_text(tenant_account_scope, default="self"),
        "source_scope": _compact_text(source_scope, default="synthetic"),
        "governed_metadata_only": bool(governed_metadata_only),
        "cross_user_view": bool(cross_user_view),
        "raw_private_data_redacted": raw_private_data is not None,
        "sections": sections,
        "counts": counts,
        "risk_flags": sorted({flag for flag in risk_flags if flag}),
        "blocked_items": blocked_items,
        "pending_approvals": pending_approvals,
        "stale_or_contradicted_items": stale_items,
        "validation_status": {"valid": False, "violation_count": 0, "violations": []},
        "protected_file_status": _ensure_section_list(validation_release_status),
        "release_gate_status": _ensure_section_list(validation_release_status),
        "release_check_status": _ensure_section_list(validation_release_status),
        "operator_notes": _listify(operator_notes),
        "limitations": _listify(limitations),
        "denied_authority": _build_denied_authority(denied_authority),
    }
    packet["validation_status"] = validate_operator_dashboard_metadata_packet_v1(packet)
    return packet


def _validate_section_items(section_name: str, items: Sequence[Mapping[str, Any]]) -> list[str]:
    violations: list[str] = []
    required_fields = _REQUIRED_SECTION_FIELDS.get(section_name, ())
    for index, item in enumerate(items):
        if not _is_mapping(item):
            violations.append(f"{section_name}[{index}] must be a mapping")
            continue
        missing = _item_missing_fields(item, required_fields)
        if missing:
            violations.append(f"{section_name}[{index}] missing: {', '.join(missing)}")
        if section_name == "approvals_queue":
            approval_status = _compact_text(item.get("approval_status")).lower()
            if approval_status == "blocked" and not _has_text(item.get("blocked_reason")):
                violations.append(f"{section_name}[{index}] blocked item needs blocked_reason")
            if not _has_text(item.get("required_approval_type")):
                violations.append(f"{section_name}[{index}] required_approval_type missing")
        elif section_name == "blocked_actions":
            if not _has_text(item.get("blocked_reason")):
                violations.append(f"{section_name}[{index}] blocked_reason missing")
            if not _has_text(item.get("boundary_triggered")):
                violations.append(f"{section_name}[{index}] boundary_triggered missing")
        elif section_name == "project_state":
            if not _has_text(item.get("project_status")) or not _has_text(item.get("project_phase")):
                violations.append(f"{section_name}[{index}] status/phase missing")
        elif section_name == "memory_state":
            if not _has_text(item.get("status")) or not _has_text(item.get("type")):
                violations.append(f"{section_name}[{index}] status/type missing")
        elif section_name == "first_tool_lane_contracts":
            if _compact_text(item.get("approval_status")).lower() == "blocked" or _compact_text(item.get("execution_status")).lower() == "blocked":
                if not _has_text(item.get("blocked_reason")):
                    violations.append(f"{section_name}[{index}] blocked_reason missing")
            if not _is_mapping(item.get("denied_authority")):
                violations.append(f"{section_name}[{index}] denied_authority must be a mapping")
            else:
                for field in _DENIED_AUTHORITY_FIELDS:
                    if field not in item["denied_authority"]:
                        violations.append(f"{section_name}[{index}] denied_authority missing {field}")
                    elif item["denied_authority"].get(field) not in (False, 0, None):
                        violations.append(f"{section_name}[{index}] denied_authority {field} must be blocked")
            if item.get("operator_visibility") is not True:
                violations.append(f"{section_name}[{index}] operator_visibility must be true")
            if not _has_text(item.get("user_visible_status_phrase")):
                violations.append(f"{section_name}[{index}] user_visible_status_phrase missing")
        elif section_name == "support_escalation":
            if not _has_text(item.get("last_safe_step")):
                violations.append(f"{section_name}[{index}] last_safe_step missing")
            if item.get("personal_data_inclusion_flag") is True and not _has_text(item.get("user_approval_status")):
                violations.append(f"{section_name}[{index}] personal data requires approval metadata")
        elif section_name == "audit_trail":
            if not _has_text(item.get("initiator")):
                violations.append(f"{section_name}[{index}] initiator missing")
            if not _has_text(item.get("marker")):
                violations.append(f"{section_name}[{index}] marker missing")
            if not _has_text(item.get("scope")):
                violations.append(f"{section_name}[{index}] scope missing")
            if not _has_text(item.get("reason")):
                violations.append(f"{section_name}[{index}] reason missing")
        elif section_name == "rollback_deprecation":
            if not (_has_text(item.get("rollback_availability")) or _has_text(item.get("deprecation_status"))):
                violations.append(f"{section_name}[{index}] needs rollback_availability or deprecation_status")
        elif section_name == "validation_release_status":
            for field in ("latest_validation_status", "release_gate_status", "release_check_status", "protected_file_status"):
                if not _has_text(item.get(field)):
                    violations.append(f"{section_name}[{index}] {field} missing")
        elif section_name == "incident_risk_flags":
            if not _has_text(item.get("flag")):
                violations.append(f"{section_name}[{index}] flag missing")
        elif section_name == "lane_expansion_candidates":
            if not _has_text(item.get("candidate_id")):
                violations.append(f"{section_name}[{index}] candidate_id missing")
    return violations


def validate_operator_dashboard_metadata_packet_v1(packet: Any) -> Dict[str, Any]:
    violations: list[str] = []
    if not _is_mapping(packet):
        return {"valid": False, "violation_count": 1, "violations": ["packet must be a mapping"]}

    for field in _REQUIRED_TOP_LEVEL_FIELDS:
        if field not in packet:
            violations.append(f"missing top-level field: {field}")
        elif field == "denied_authority":
            denied = packet.get(field)
            if not _is_mapping(denied):
                violations.append("denied_authority must be a mapping")
            else:
                for denied_field in _DENIED_AUTHORITY_FIELDS:
                    if denied_field not in denied:
                        violations.append(f"denied_authority missing {denied_field}")
                    elif denied.get(denied_field) not in (False, 0, None):
                        violations.append(f"denied_authority {denied_field} must be blocked")
        elif field == "validation_status":
            if not _is_mapping(packet.get(field)):
                violations.append("validation_status must be a mapping")
        elif field in {"blocked_items", "pending_approvals", "stale_or_contradicted_items", "operator_notes", "limitations"}:
            if not isinstance(packet.get(field), list):
                violations.append(f"{field} must be a list")
        elif field in {"schema_version", "report_id", "report_type", "generated_marker", "owner_operator_scope", "tenant_account_scope", "source_scope"}:
            if not _has_text(packet.get(field)):
                violations.append(f"{field} missing or blank")

    if _compact_text(packet.get("schema_version")) != SCHEMA_VERSION_V1:
        violations.append("schema_version mismatch")
    if _compact_text(packet.get("report_type")) != REPORT_TYPE_V1:
        violations.append("report_type mismatch")

    sections = packet.get("sections")
    if not _is_mapping(sections):
        violations.append("sections must be a mapping")
        sections = {}
    else:
        section_names = set(sections.keys())
        required_names = set(SECTION_NAMES_V1)
        missing_sections = sorted(required_names - section_names)
        extra_sections = sorted(section_names - required_names)
        if missing_sections:
            violations.append(f"missing sections: {', '.join(missing_sections)}")
        if extra_sections:
            violations.append(f"unknown sections: {', '.join(extra_sections)}")
        for section_name in SECTION_NAMES_V1:
            violations.extend(_validate_section_items(section_name, _ensure_section_list(sections.get(section_name))))

    if _scope_requires_governance(packet.get("owner_operator_scope"), packet.get("tenant_account_scope"), packet.get("source_scope")) and not _is_governed_metadata_only(packet):
        violations.append("cross-user or shared scope requires governed_metadata_only=true")

    if packet.get("cross_user_view") and not _is_governed_metadata_only(packet):
        violations.append("cross_user_view requires governed_metadata_only=true")

    if packet.get("raw_private_data_redacted") not in (True, False):
        violations.append("raw_private_data_redacted must be boolean")

    if packet.get("raw_private_data_redacted") is False and packet.get("limitations") and any("raw private data" in _compact_text(item).lower() for item in packet.get("limitations", [])):
        violations.append("raw private data must be redacted by default")

    if isinstance(sections, Mapping):
        overview = _ensure_section_list(sections.get("overview"))
        if overview:
            for item in overview:
                if _is_mapping(item):
                    if "owner_user_scope" in item and not _has_text(item.get("owner_user_scope")):
                        violations.append("overview owner_user_scope missing")
                    if "source_provenance" in item and not _has_text(item.get("source_provenance")):
                        violations.append("overview source_provenance missing")

    valid = len(violations) == 0
    return {
        "valid": valid,
        "violation_count": len(violations),
        "violations": violations,
        "sections_validated": list(SECTION_NAMES_V1),
    }


def summarize_operator_dashboard_metadata_packet_v1(packet: Any) -> Dict[str, Any]:
    safe = to_operator_dashboard_metadata_json_safe_v1(packet)
    sections = safe.get("sections", {}) if _is_mapping(safe) else {}
    counts = safe.get("counts", {}) if _is_mapping(safe) else {}
    summary = {
        "schema_version": safe.get("schema_version"),
        "report_id": safe.get("report_id"),
        "report_type": safe.get("report_type"),
        "validation_status": safe.get("validation_status"),
        "counts": counts,
        "risk_flags": safe.get("risk_flags", []),
        "blocked_items": safe.get("blocked_items", []),
        "pending_approvals": safe.get("pending_approvals", []),
        "limitations": safe.get("limitations", []),
        "sections_present": sorted(sections.keys()) if isinstance(sections, Mapping) else [],
    }
    return _json_safe(summary)


def to_operator_dashboard_metadata_json_safe_v1(packet: Any) -> Any:
    return _json_safe(packet)


def classify_operator_dashboard_item_v1(item: Any) -> Dict[str, Any]:
    normalized = _normalize_item(item)
    for section_name, hints in _SECTION_HINTS.items():
        if all(hint in normalized for hint in hints):
            return {"section": section_name, "item": _json_safe(normalized)}
    if "approval_id" in normalized:
        return {"section": "approvals_queue", "item": _json_safe(normalized)}
    if "blocked_reason" in normalized:
        return {"section": "blocked_actions", "item": _json_safe(normalized)}
    if "project_id" in normalized:
        return {"section": "project_state", "item": _json_safe(normalized)}
    if "memory_id" in normalized:
        return {"section": "memory_state", "item": _json_safe(normalized)}
    if "lane_id" in normalized and ("approval_status" in normalized or "execution_status" in normalized):
        return {"section": "first_tool_lane_contracts", "item": _json_safe(normalized)}
    if "support_escalation_id" in normalized:
        return {"section": "support_escalation", "item": _json_safe(normalized)}
    if "marker" in normalized and "initiator" in normalized:
        return {"section": "audit_trail", "item": _json_safe(normalized)}
    if "rollback_availability" in normalized or "deprecation_status" in normalized:
        return {"section": "rollback_deprecation", "item": _json_safe(normalized)}
    if "release_gate_status" in normalized or "release_check_status" in normalized:
        return {"section": "validation_release_status", "item": _json_safe(normalized)}
    if "flag" in normalized:
        return {"section": "incident_risk_flags", "item": _json_safe(normalized)}
    if "candidate_id" in normalized:
        return {"section": "lane_expansion_candidates", "item": _json_safe(normalized)}
    return {"section": "unknown", "item": _json_safe(normalized)}


def build_initial_operator_dashboard_metadata_examples_v1() -> list[Dict[str, Any]]:
    examples = [
        build_operator_dashboard_metadata_packet_v1(
            report_id="operator_dashboard_example_001",
            owner_operator_scope="operator",
            tenant_account_scope="self",
            source_scope="synthetic",
            overview=[{"owner_user_scope": "operator", "source_provenance": "synthetic"}],
            approvals_queue=[
                {
                    "approval_id": "approval_001",
                    "owner_user_scope": "self",
                    "tenant_account_scope": "self",
                    "lane_id": "draft_artifact_creation",
                    "action_class": "draft_artifact_creation",
                    "requested_action": "Draft a note",
                    "risk_level": "low_internal",
                    "required_approval_type": "none",
                    "approval_status": "not_required_internal_only",
                    "source_provenance": "synthetic",
                    "user_visible_summary": "Draft only",
                }
            ],
            blocked_actions=[
                {
                    "blocked_reason": "external sharing blocked",
                    "boundary_triggered": "no external export",
                    "lane_id": "public_publishing",
                    "action_class": "public_publishing",
                    "affected_item": "report_001",
                    "user_visible_blocked_phrase": "blocked from public export",
                    "source_provenance": "synthetic",
                }
            ],
            project_state=[
                {
                    "project_id": "project_alpha",
                    "owner_user_scope": "self",
                    "tenant_account_scope": "self",
                    "project_status": "active",
                    "project_phase": "planning",
                    "source_provenance": "synthetic",
                }
            ],
            memory_state=[
                {
                    "memory_id": "memory_alpha",
                    "scope": "self",
                    "status": "provisional",
                    "type": "note",
                    "source_provenance": "synthetic",
                }
            ],
            first_tool_lane_contracts=[
                {
                    "lane_id": "safe_internal_report_generation",
                    "action_class": "safe_internal_report_generation",
                    "approval_status": "not_required_internal_only",
                    "execution_status": "planned_metadata_only",
                    "risk_level": "low_internal",
                    "blocked_reason": "",
                    "denied_authority": {field: False for field in _DENIED_AUTHORITY_FIELDS},
                    "operator_visibility": True,
                    "user_visible_status_phrase": "internal report only",
                    "source_provenance": "synthetic",
                }
            ],
            support_escalation=[
                {
                    "support_escalation_id": "support_001",
                    "reason": "user question",
                    "owner_user_scope": "self",
                    "tenant_account_scope": "self",
                    "status": "open",
                    "last_safe_step": "collect evidence",
                    "source_provenance": "synthetic",
                }
            ],
            audit_trail=[
                {
                    "initiator": "system",
                    "marker": "audit_001",
                    "scope": "self",
                    "reason": "metadata example",
                    "source_provenance": "synthetic",
                }
            ],
            rollback_deprecation=[
                {
                    "rollback_availability": "available",
                    "rollback_target": "report_001",
                    "deprecation_status": "active",
                    "source_provenance": "synthetic",
                }
            ],
            validation_release_status=[
                {
                    "latest_validation_status": "valid",
                    "release_gate_status": "passed",
                    "release_check_status": "passed",
                    "protected_file_status": "unchanged",
                    "allowed_file_scope": "docs-only",
                    "source_provenance": "synthetic",
                }
            ],
            incident_risk_flags=[
                {"flag": "repeated_failure", "scope": "self", "source_provenance": "synthetic"}
            ],
            lane_expansion_candidates=[
                {"candidate_id": "lane_001", "summary": "future scope", "source_provenance": "synthetic"}
            ],
            operator_notes=["synthetic example"],
            limitations=["synthetic only"],
            governed_metadata_only=True,
        ),
        build_operator_dashboard_metadata_packet_v1(
            report_id="operator_dashboard_example_002",
            owner_operator_scope="operator",
            tenant_account_scope="self",
            source_scope="synthetic",
            approvals_queue=[
                {
                    "approval_id": "approval_002",
                    "owner_user_scope": "shared",
                    "tenant_account_scope": "system",
                    "lane_id": "scoped_memory_project_update_proposal",
                    "action_class": "scoped_memory_project_update_proposal",
                    "requested_action": "Propose shared update",
                    "risk_level": "high_operator_review",
                    "required_approval_type": "operator",
                    "approval_status": "operator_approval_required",
                    "source_provenance": "synthetic",
                    "user_visible_summary": "shared scope requires operator review",
                }
            ],
            incident_risk_flags=[
                {"flag": "cross_user_leakage_risk", "scope": "shared", "source_provenance": "synthetic"}
            ],
            validation_release_status=[
                {
                    "latest_validation_status": "blocked",
                    "release_gate_status": "passed",
                    "release_check_status": "passed",
                    "protected_file_status": "unchanged",
                    "allowed_file_scope": "docs-only",
                    "source_provenance": "synthetic",
                }
            ],
            governed_metadata_only=True,
        ),
    ]
    return [to_operator_dashboard_metadata_json_safe_v1(example) for example in examples]
