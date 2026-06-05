"""Metadata-only private project gap analysis helpers v1."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "private_project_gap_analysis_metadata_v1"

_ALLOWED_ANALYSIS_LEVELS_V1 = (
    "surface_gap_review",
    "deeper_gap_analysis",
    "operator_review_required",
)

_ALLOWED_CONSENT_STATUSES_V1 = (
    "not_required_for_surface",
    "required",
    "requested",
    "granted",
    "declined",
    "revoked",
)

_ALLOWED_APPROVAL_STATUSES_V1 = (
    "not_required",
    "pending_user_confirmation",
    "user_confirmed",
    "operator_review_required",
    "operator_approved",
    "blocked",
)

_ALLOWED_GAP_CATEGORIES_V1 = (
    "missing_goal",
    "unclear_scope",
    "missing_constraints",
    "missing_success_criteria",
    "missing_inputs",
    "missing_output_definition",
    "missing_deadline_or_priority",
    "missing_owner_decision",
    "missing_evidence",
    "weak_assumption",
    "contradiction",
    "stale_context",
    "privacy_sensitive_gap",
    "missing_approval",
    "tool_action_boundary",
    "external_action_boundary",
    "project_state_gap",
    "memory_state_gap",
    "support_escalation_gap",
    "rollout_gap",
)

_DENIED_AUTHORITY_FIELDS_V1 = (
    "runtime_wiring_authority",
    "chat_" "responder_authority",
    "final_answer_generation_authority",
    "storage_database_authority",
    "weslr_io_authority",
    "project_state_mutation_authority",
    "memory_mutation_authority",
    "tool_execution_authority",
    "external_action_authority",
    "hidden_memory_authority",
    "hidden_project_state_authority",
    "private_mechanism_disclosure_authority",
    "cross_user_leakage_authority",
    "public_product_readiness_authority",
)

_REQUIRED_CORE_FIELDS_V1 = (
    "schema_version",
    "analysis_id",
    "analysis_level",
    "project_id",
    "owner_user_scope",
    "tenant_account_scope",
    "source_scope",
    "consent_status",
    "approval_status",
    "privacy_sensitivity",
    "input_metadata_refs",
    "gap_categories",
    "risk_flags",
    "missing_fields",
    "contradictions",
    "weak_evidence_items",
    "blocked_items",
    "suggested_questions",
    "safe_next_steps",
    "operator_visible_summary",
    "user_visible_summary",
    "limitations",
    "requires_user_confirmation",
    "requires_operator_review",
    "deeper_analysis_available",
    "denied_authority",
)

_PRIVATE_MECHANISM_MARKERS = (
    "unknown engine",
    "hidden prompt",
    "secret reasoning",
    "private mechanism",
    "friction mechanism",
    "internal scoring",
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


def allowed_project_gap_analysis_levels_v1() -> tuple[str, ...]:
    return _ALLOWED_ANALYSIS_LEVELS_V1


def allowed_project_gap_categories_v1() -> tuple[str, ...]:
    return _ALLOWED_GAP_CATEGORIES_V1


def allowed_project_gap_consent_statuses_v1() -> tuple[str, ...]:
    return _ALLOWED_CONSENT_STATUSES_V1


def allowed_project_gap_approval_statuses_v1() -> tuple[str, ...]:
    return _ALLOWED_APPROVAL_STATUSES_V1


def _detect_private_mechanism_text(*values: Any) -> bool:
    text = " ".join(_compact_text(value, default="").lower() for value in values)
    return any(marker in text for marker in _PRIVATE_MECHANISM_MARKERS)


def _gap_category_from_field(field: str) -> str:
    mapping = {
        "goal": "missing_goal",
        "scope": "unclear_scope",
        "constraints": "missing_constraints",
        "success_criteria": "missing_success_criteria",
        "known_inputs": "missing_inputs",
        "desired_output": "missing_output_definition",
        "deadline_or_priority": "missing_deadline_or_priority",
        "owner_decision": "missing_owner_decision",
        "evidence": "missing_evidence",
    }
    return mapping.get(field, "missing_evidence")


def _build_gap_categories(missing_fields: list[str], contradictions: list[Any], weak_evidence_items: list[Any], blocked_items: list[Any], risk_flags: list[str], privacy_sensitivity: str, approval_status: str, analysis_level: str) -> list[str]:
    categories: list[str] = []
    for field in missing_fields:
        category = _gap_category_from_field(field)
        if category not in categories:
            categories.append(category)
    if contradictions and "contradiction" not in categories:
        categories.append("contradiction")
    if weak_evidence_items and "missing_evidence" not in categories:
        categories.append("missing_evidence")
    if any("stale" in _compact_text(flag).lower() for flag in risk_flags) and "stale_context" not in categories:
        categories.append("stale_context")
    if any("privacy" in _compact_text(flag).lower() for flag in risk_flags) or privacy_sensitivity in {"high", "sensitive", "private", "personal"}:
        if "privacy_sensitive_gap" not in categories:
            categories.append("privacy_sensitive_gap")
    if blocked_items:
        if "tool" in " ".join(_compact_text(item).lower() for item in blocked_items) and "tool_action_boundary" not in categories:
            categories.append("tool_action_boundary")
        if "external" in " ".join(_compact_text(item).lower() for item in blocked_items) and "external_action_boundary" not in categories:
            categories.append("external_action_boundary")
    if approval_status in {"pending_user_confirmation", "user_confirmed", "operator_review_required", "blocked"} and "missing_approval" not in categories:
        if analysis_level != "surface_gap_review" or blocked_items or risk_flags:
            categories.append("missing_approval")
    if not categories:
        categories.append("missing_evidence")
    return categories


def _build_summary(analysis_level: str, gap_categories: list[str], missing_fields: list[str], risk_flags: list[str], approvals: list[str], user_visible: bool) -> str:
    if user_visible:
        if analysis_level == "surface_gap_review":
            return f"Surface project review: likely gaps={len(gap_categories)}; deeper analysis available if you approve."
        if analysis_level == "deeper_gap_analysis":
            return f"Deeper project analysis: likely gaps={len(gap_categories)}; limitations apply."
        return "This case requires operator review before normal user-visible analysis."
    parts = [f"level={analysis_level}"]
    if gap_categories:
        parts.append(f"gaps={','.join(gap_categories)}")
    if missing_fields:
        parts.append(f"missing={','.join(missing_fields)}")
    if risk_flags:
        parts.append(f"risk_flags={','.join(risk_flags)}")
    if approvals:
        parts.append(f"approvals={','.join(approvals)}")
    return " | ".join(parts)


def build_project_gap_analysis_packet_v1(
    *,
    project_id: Any = "",
    owner_user_scope: Any = "",
    tenant_account_scope: Any = "",
    source_scope: Any = "",
    analysis_level: Any = "surface_gap_review",
    consent_status: Any = "not_required_for_surface",
    approval_status: Any = "not_required",
    privacy_sensitivity: Any = "low",
    input_metadata_refs: Any = None,
    gap_categories: Any = None,
    risk_flags: Any = None,
    missing_fields: Any = None,
    contradictions: Any = None,
    weak_evidence_items: Any = None,
    blocked_items: Any = None,
    suggested_questions: Any = None,
    safe_next_steps: Any = None,
    operator_visible_summary: Any = "",
    user_visible_summary: Any = "",
    limitations: Any = None,
    requires_user_confirmation: Any = None,
    requires_operator_review: Any = None,
    deeper_analysis_available: Any = None,
    denied_authority: Any = None,
) -> dict[str, Any]:
    project_text = _compact_text(project_id)
    owner_text = _compact_text(owner_user_scope)
    tenant_text = _compact_text(tenant_account_scope)
    source_text = _compact_text(source_scope)
    level_text = _compact_text(analysis_level, default="surface_gap_review")
    consent_text = _compact_text(consent_status, default="not_required_for_surface")
    approval_text = _compact_text(approval_status, default="not_required")
    privacy_text = _compact_text(privacy_sensitivity, default="low")
    refs = _listify(input_metadata_refs)
    missing = [field for field in _listify(missing_fields) if _has_text(field)]
    contradictions_list = [item for item in _listify(contradictions) if _has_text(item)]
    weak_evidence_list = [item for item in _listify(weak_evidence_items) if _has_text(item)]
    blocked_list = [item for item in _listify(blocked_items) if _has_text(item)]
    suggested_questions_list = [item for item in _listify(suggested_questions) if _has_text(item)]
    safe_next_steps_list = [item for item in _listify(safe_next_steps) if _has_text(item)]
    risk_flags_list = [item for item in _listify(risk_flags) if _has_text(item)]
    limitation_list = [item for item in _listify(limitations) if _has_text(item)]

    if not project_text:
        project_text = _stable_marker("project_gap_candidate", {"level": level_text, "source": source_text, "owner": owner_text, "tenant": tenant_text})
    if not source_text:
        source_text = _stable_marker("source_scope_candidate", {"project": project_text, "level": level_text, "refs": refs})

    if not missing:
        default_missing = ["goal", "scope"] if level_text == "surface_gap_review" else ["goal", "scope", "constraints"]
        missing = default_missing
    if not gap_categories:
        gap_categories = _build_gap_categories(missing, contradictions_list, weak_evidence_list, blocked_list, risk_flags_list, privacy_text, approval_text, level_text)
    else:
        gap_categories = [item for item in _listify(gap_categories) if _has_text(item)]

    for category in gap_categories:
        if category not in _ALLOWED_GAP_CATEGORIES_V1:
            raise ValueError(f"unknown gap category: {category}")

    if not suggested_questions_list:
        suggested_questions_list = []
        for field in missing:
            if field == "goal":
                suggested_questions_list.append("What is the project goal?")
            elif field == "scope":
                suggested_questions_list.append("What is the project scope?")
            elif field == "constraints":
                suggested_questions_list.append("What constraints should I respect?")
            elif field == "success_criteria":
                suggested_questions_list.append("How will success be recognized?")
            elif field == "known_inputs":
                suggested_questions_list.append("What inputs do you already have?")
            elif field == "desired_output":
                suggested_questions_list.append("What output do you want?")
            elif field == "deadline_or_priority":
                suggested_questions_list.append("What deadline or priority should I use?")
        if not suggested_questions_list:
            suggested_questions_list.append("Would you like a deeper project analysis if you approve it?")

    if not safe_next_steps_list:
        if level_text == "surface_gap_review":
            safe_next_steps_list = ["surface_summary", "ask_clarifying_questions"]
        elif level_text == "deeper_gap_analysis":
            safe_next_steps_list = ["prepare_approval_metadata", "return_structured_gap_report"]
        else:
            safe_next_steps_list = ["await_operator_review"]

    if requires_user_confirmation is None:
        requires_user_confirmation = bool(level_text == "deeper_gap_analysis" or privacy_text in {"high", "sensitive", "private", "personal"} or approval_text == "pending_user_confirmation")
    if requires_operator_review is None:
        requires_operator_review = bool(level_text == "operator_review_required" or privacy_text in {"high", "sensitive", "private", "personal"} or _compact_text(source_text).startswith("system") or "cross" in _compact_text(source_text).lower())
    if deeper_analysis_available is None:
        deeper_analysis_available = bool(level_text == "surface_gap_review" and not requires_operator_review)

    if level_text == "operator_review_required":
        consent_text = "required" if consent_text == "not_required_for_surface" else consent_text
        approval_text = "operator_review_required"
        deeper_analysis_available = False
    elif level_text == "deeper_gap_analysis":
        if approval_text == "not_required":
            approval_text = "pending_user_confirmation"
        if consent_text == "not_required_for_surface":
            consent_text = "required"
    else:
        if consent_text == "not_required_for_surface" and privacy_text in {"high", "sensitive", "private", "personal"}:
            consent_text = "required"

    if not operator_visible_summary:
        operator_visible_summary = _build_summary(level_text, gap_categories, missing, risk_flags_list, [approval_text, consent_text], False)
    if not user_visible_summary:
        user_visible_summary = _build_summary(level_text, gap_categories, missing, risk_flags_list, [approval_text, consent_text], True)

    packet = {
        "schema_version": SCHEMA_VERSION_V1,
        "analysis_id": _stable_marker("analysis", {"project": project_text, "level": level_text, "source": source_text, "refs": refs}),
        "analysis_level": level_text,
        "project_id": project_text,
        "owner_user_scope": owner_text,
        "tenant_account_scope": tenant_text,
        "source_scope": source_text,
        "consent_status": consent_text,
        "approval_status": approval_text,
        "privacy_sensitivity": privacy_text,
        "input_metadata_refs": refs,
        "gap_categories": gap_categories,
        "risk_flags": risk_flags_list,
        "missing_fields": missing,
        "contradictions": contradictions_list,
        "weak_evidence_items": weak_evidence_list,
        "blocked_items": blocked_list,
        "suggested_questions": suggested_questions_list,
        "safe_next_steps": safe_next_steps_list,
        "operator_visible_summary": _compact_text(operator_visible_summary),
        "user_visible_summary": _compact_text(user_visible_summary),
        "limitations": limitation_list or ["metadata-only", "no runtime implementation", "no certainty overclaim"],
        "requires_user_confirmation": bool(requires_user_confirmation),
        "requires_operator_review": bool(requires_operator_review),
        "deeper_analysis_available": bool(deeper_analysis_available),
        "denied_authority": _normalize_denied_authority(denied_authority),
    }
    return _json_safe(packet)


def validate_project_gap_analysis_packet_v1(packet: Any) -> dict[str, Any]:
    violations: list[str] = []
    if not isinstance(packet, Mapping):
        violations.append("packet must be a mapping")
        return {"valid": False, "violation_count": len(violations), "violations": violations, "classification": {"analysis_level": "surface_gap_review", "review_state": "blocked"}}

    packet = _json_safe(copy.deepcopy(packet))
    for field in _REQUIRED_CORE_FIELDS_V1:
        if field not in packet:
            violations.append(f"missing field: {field}")

    if _compact_text(packet.get("schema_version")) != SCHEMA_VERSION_V1:
        violations.append("schema_version mismatch")
    level = _compact_text(packet.get("analysis_level"))
    if level not in _ALLOWED_ANALYSIS_LEVELS_V1:
        violations.append(f"unknown analysis level: {level or '<blank>'}")
    if not _has_text(packet.get("analysis_id")):
        violations.append("analysis_id missing or blank")
    if not _has_text(packet.get("project_id")):
        violations.append("project_id missing or blank")
    if not _has_text(packet.get("owner_user_scope")):
        violations.append("owner_user_scope missing or blank")
    if not _has_text(packet.get("tenant_account_scope")):
        violations.append("tenant_account_scope missing or blank")
    source_scope = _compact_text(packet.get("source_scope"))
    if not source_scope:
        violations.append("source_scope missing or blank")
    consent = _compact_text(packet.get("consent_status"))
    if consent not in _ALLOWED_CONSENT_STATUSES_V1:
        violations.append(f"unknown consent status: {consent or '<blank>'}")
    approval = _compact_text(packet.get("approval_status"))
    if approval not in _ALLOWED_APPROVAL_STATUSES_V1:
        violations.append(f"unknown approval status: {approval or '<blank>'}")
    privacy = _compact_text(packet.get("privacy_sensitivity"), default="low")
    if not isinstance(packet.get("input_metadata_refs"), list):
        violations.append("input_metadata_refs must be a list")
    if not isinstance(packet.get("gap_categories"), list):
        violations.append("gap_categories must be a list")
    if not isinstance(packet.get("risk_flags"), list):
        violations.append("risk_flags must be a list")
    if not isinstance(packet.get("missing_fields"), list):
        violations.append("missing_fields must be a list")
    if not isinstance(packet.get("contradictions"), list):
        violations.append("contradictions must be a list")
    if not isinstance(packet.get("weak_evidence_items"), list):
        violations.append("weak_evidence_items must be a list")
    if not isinstance(packet.get("blocked_items"), list):
        violations.append("blocked_items must be a list")
    if not isinstance(packet.get("suggested_questions"), list):
        violations.append("suggested_questions must be a list")
    if not isinstance(packet.get("safe_next_steps"), list):
        violations.append("safe_next_steps must be a list")
    if not isinstance(packet.get("limitations"), list):
        violations.append("limitations must be a list")
    if not isinstance(packet.get("requires_user_confirmation"), bool):
        violations.append("requires_user_confirmation must be a boolean")
    if not isinstance(packet.get("requires_operator_review"), bool):
        violations.append("requires_operator_review must be a boolean")
    if not isinstance(packet.get("deeper_analysis_available"), bool):
        violations.append("deeper_analysis_available must be a boolean")
    if not _has_text(packet.get("user_visible_summary")):
        violations.append("user_visible_summary missing or blank")
    if not _has_text(packet.get("operator_visible_summary")):
        violations.append("operator_visible_summary missing or blank")
    if _detect_private_mechanism_text(packet.get("user_visible_summary"), packet.get("operator_visible_summary")):
        violations.append("user-visible wording must stay mechanism-neutral")

    for category in packet.get("gap_categories", []):
        if category not in _ALLOWED_GAP_CATEGORIES_V1:
            violations.append(f"unknown gap category: {category}")

    if any(item is None or not _has_text(item) for item in packet.get("suggested_questions", [])):
        violations.append("suggested_questions must be non-empty text items")
    if any(item is None or not _has_text(item) for item in packet.get("safe_next_steps", [])):
        violations.append("safe_next_steps must be non-empty text items")
    if any(item is None or not _has_text(item) for item in packet.get("limitations", [])):
        violations.append("limitations must be non-empty text items")

    if level == "surface_gap_review":
        if packet.get("approval_status") not in {"not_required", "pending_user_confirmation"}:
            violations.append("surface review approval status must stay limited")
        if packet.get("requires_operator_review") and not packet.get("deeper_analysis_available"):
            pass
    elif level == "deeper_gap_analysis":
        if not packet.get("requires_user_confirmation"):
            violations.append("deeper analysis requires explicit user confirmation metadata")
        if packet.get("approval_status") not in {"pending_user_confirmation", "user_confirmed"}:
            violations.append("deeper analysis approval status must reflect approval gating")
    elif level == "operator_review_required":
        if not packet.get("requires_operator_review"):
            violations.append("operator review required level must require operator review")
        if packet.get("deeper_analysis_available"):
            violations.append("operator review required level cannot proceed as normal deeper analysis")

    if privacy in {"high", "sensitive", "private", "personal"} and not packet.get("requires_user_confirmation"):
        violations.append("privacy-sensitive deeper analysis requires confirmation")
    if ("tool_action_boundary" in packet.get("gap_categories", []) or "external_action_boundary" in packet.get("gap_categories", [])) and not any(
        "approval" in _compact_text(flag).lower() or "candidate" in _compact_text(flag).lower()
        for flag in [*packet.get("risk_flags", []), *packet.get("blocked_items", [])]
    ):
        violations.append("tool/external action gaps must remain approval-gated candidates")

    if not isinstance(packet.get("denied_authority"), Mapping):
        violations.append("denied_authority must be a mapping")
    else:
        for field in _DENIED_AUTHORITY_FIELDS_V1:
            if field not in packet["denied_authority"]:
                violations.append(f"missing denied authority: {field}")
            elif packet["denied_authority"].get(field) is not False:
                violations.append(f"denied authority must remain blocked: {field}")

    classification = {
        "analysis_level": level or "surface_gap_review",
        "review_state": "blocked" if violations else "ready",
        "consent_status": consent,
        "approval_status": approval,
        "requires_user_confirmation": bool(packet.get("requires_user_confirmation")),
        "requires_operator_review": bool(packet.get("requires_operator_review")),
        "deeper_analysis_available": bool(packet.get("deeper_analysis_available")),
    }
    return {"valid": not violations, "violation_count": len(violations), "violations": violations, "classification": classification}


def classify_project_gap_analysis_packet_v1(packet: Any) -> dict[str, Any]:
    if not isinstance(packet, Mapping):
        return {
            "analysis_level": "surface_gap_review",
            "review_state": "blocked",
            "surface_review_available": False,
            "deeper_analysis_available": False,
            "operator_review_required": False,
            "has_missing_evidence": False,
            "has_contradictions": False,
            "has_stale_context": False,
        }
    safe = _json_safe(copy.deepcopy(packet))
    validation = validate_project_gap_analysis_packet_v1(safe)
    level = _compact_text(safe.get("analysis_level"), default="surface_gap_review")
    has_missing_evidence = bool(safe.get("weak_evidence_items")) or "missing_evidence" in safe.get("gap_categories", [])
    has_contradictions = bool(safe.get("contradictions")) or "contradiction" in safe.get("gap_categories", [])
    has_stale_context = "stale_context" in safe.get("gap_categories", []) or any("stale" in _compact_text(flag).lower() for flag in safe.get("risk_flags", []))
    surface_review_available = level == "surface_gap_review" and validation["valid"]
    deeper_analysis_available = bool(safe.get("deeper_analysis_available")) and validation["valid"] and level != "operator_review_required"
    operator_review_required = level == "operator_review_required" or bool(safe.get("requires_operator_review"))
    return {
        "analysis_level": level,
        "review_state": validation["classification"]["review_state"],
        "surface_review_available": surface_review_available,
        "deeper_analysis_available": deeper_analysis_available,
        "operator_review_required": operator_review_required,
        "has_missing_evidence": has_missing_evidence,
        "has_contradictions": has_contradictions,
        "has_stale_context": has_stale_context,
        "validation_status": validation["classification"],
    }


def summarize_project_gap_analysis_packet_v1(packet: Any) -> dict[str, Any]:
    safe = _json_safe(copy.deepcopy(packet)) if isinstance(packet, Mapping) else {}
    summary = {
        "analysis_id": _compact_text(safe.get("analysis_id"), default="unknown_analysis"),
        "analysis_level": _compact_text(safe.get("analysis_level"), default="surface_gap_review"),
        "project_id": _compact_text(safe.get("project_id"), default=""),
        "gap_category_count": len(_listify(safe.get("gap_categories"))),
        "missing_field_count": len(_listify(safe.get("missing_fields"))),
        "contradiction_count": len(_listify(safe.get("contradictions"))),
        "weak_evidence_count": len(_listify(safe.get("weak_evidence_items"))),
        "blocked_item_count": len(_listify(safe.get("blocked_items"))),
        "requires_user_confirmation": bool(safe.get("requires_user_confirmation")),
        "requires_operator_review": bool(safe.get("requires_operator_review")),
        "deeper_analysis_available": bool(safe.get("deeper_analysis_available")),
        "user_visible_summary": _compact_text(safe.get("user_visible_summary"), default=""),
        "operator_visible_summary": _compact_text(safe.get("operator_visible_summary"), default=""),
    }
    return _json_safe(summary)


def to_project_gap_analysis_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def build_initial_project_gap_analysis_examples_v1() -> list[dict[str, Any]]:
    examples = [
        build_project_gap_analysis_packet_v1(
            project_id="project_alpha",
            owner_user_scope="self",
            tenant_account_scope="self",
            source_scope="synthetic_project_scoped",
            analysis_level="surface_gap_review",
            consent_status="not_required_for_surface",
            approval_status="not_required",
            privacy_sensitivity="low",
            input_metadata_refs=["synthetic:project_start_packet:alpha"],
            missing_fields=["goal", "scope", "constraints"],
            weak_evidence_items=["goal inferred from brief note"],
            suggested_questions=["What is the project goal?"],
        ),
        build_project_gap_analysis_packet_v1(
            project_id="project_beta",
            owner_user_scope="self",
            tenant_account_scope="self",
            source_scope="synthetic_project_scoped",
            analysis_level="deeper_gap_analysis",
            consent_status="granted",
            approval_status="user_confirmed",
            privacy_sensitivity="low",
            input_metadata_refs=["synthetic:project_state:beta", "synthetic:memory_state:beta"],
            missing_fields=["success_criteria", "deadline_or_priority"],
            contradictions=["scope is both fixed and expanding"],
            weak_evidence_items=["success criteria not yet grounded"],
            safe_next_steps=["clarify success criteria", "collect evidence"],
            requires_user_confirmation=True,
            deeper_analysis_available=True,
        ),
    ]
    return [to_project_gap_analysis_json_safe_v1(example) for example in examples]


__all__ = [
    "SCHEMA_VERSION_V1",
    "allowed_project_gap_analysis_levels_v1",
    "allowed_project_gap_categories_v1",
    "allowed_project_gap_consent_statuses_v1",
    "allowed_project_gap_approval_statuses_v1",
    "build_project_gap_analysis_packet_v1",
    "validate_project_gap_analysis_packet_v1",
    "classify_project_gap_analysis_packet_v1",
    "summarize_project_gap_analysis_packet_v1",
    "to_project_gap_analysis_json_safe_v1",
    "build_initial_project_gap_analysis_examples_v1",
]
