#!/usr/bin/env python3
"""WESLR first tool lanes contract helpers V1.

Metadata-only helpers for the first selected tool lanes. These helpers classify,
validate, summarize, and normalize contract metadata without executing actions,
wiring runtime behavior, persisting state, or mutating user/project/memory data.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict, Iterable, Mapping

SCHEMA_VERSION_V1 = "first_tool_lanes_contract_v1"
MAX_FAILURE_COUNT_V1 = 3

APPROVED_FIRST_TOOL_LANES_V1 = (
    "draft_artifact_creation",
    "project_plan_checklist",
    "scoped_memory_project_update_proposal",
    "safe_internal_report_generation",
    "support_escalation_record",
)

BLOCKED_FIRST_TOOL_LANES_V1 = (
    "external_sending_posting",
    "public_publishing",
    "destructive_action",
    "payments_contracts_legal_medical_financial_authority",
    "broad_third_party_integration",
    "autonomous_tool_discovery",
    "automatic_behavior_update",
    "runtime_chat_wiring",
    "public_product_readiness",
)

ALL_FIRST_TOOL_LANES_V1 = APPROVED_FIRST_TOOL_LANES_V1 + BLOCKED_FIRST_TOOL_LANES_V1

LANE_LABELS_V1 = {
    "draft_artifact_creation": "Draft / artifact creation",
    "project_plan_checklist": "Project plan / checklist",
    "scoped_memory_project_update_proposal": "Scoped memory / project update proposal",
    "safe_internal_report_generation": "Safe internal report generation",
    "support_escalation_record": "Support / escalation record",
    "external_sending_posting": "External sending / posting",
    "public_publishing": "Public publishing",
    "destructive_action": "Destructive action",
    "payments_contracts_legal_medical_financial_authority": "Payments / contracts / legal / medical / financial authority",
    "broad_third_party_integration": "Broad third-party integration",
    "autonomous_tool_discovery": "Autonomous tool discovery",
    "automatic_behavior_update": "Automatic behavior update",
    "runtime_chat_wiring": "Runtime chat wiring",
    "public_product_readiness": "Public product readiness",
    "unknown_lane": "Unknown lane",
}

ACTION_CLASSES_V1 = {
    "draft_artifact_creation": "draft_artifact_creation",
    "project_plan_checklist": "project_plan_checklist",
    "scoped_memory_project_update_proposal": "scoped_memory_project_update_proposal",
    "safe_internal_report_generation": "safe_internal_report_generation",
    "support_escalation_record": "support_escalation_record",
    "external_sending_posting": "external_sending_posting",
    "public_publishing": "public_publishing",
    "destructive_action": "destructive_action",
    "payments_contracts_legal_medical_financial_authority": "payments_contracts_legal_medical_financial_authority",
    "broad_third_party_integration": "broad_third_party_integration",
    "autonomous_tool_discovery": "autonomous_tool_discovery",
    "automatic_behavior_update": "automatic_behavior_update",
    "runtime_chat_wiring": "runtime_chat_wiring",
    "public_product_readiness": "public_product_readiness",
    "unknown_lane": "unknown_lane",
}

_DENIED_AUTHORITY_FIELDS = (
    "runtime_wiring_authority",
    "tool_execution_authority",
    "external_sending_authority",
    "public_publishing_authority",
    "destructive_action_authority",
    "third_party_account_authority",
    "storage_database_authority",
    "memory_mutation_authority",
    "project_state_mutation_authority",
    "behavior_pack_promotion_authority",
    "public_product_readiness_authority",
)

APPROVAL_STATUSES_V1 = {
    "not_required_internal_only",
    "user_confirmation_required",
    "operator_approval_required",
    "separate_review_required",
    "blocked",
    "approved_metadata_only",
}

EXECUTION_STATUSES_V1 = {
    "not_executed",
    "planned_metadata_only",
    "proposed_metadata_only",
    "blocked",
    "failed_metadata_only",
    "deprecated_metadata_only",
}

RISK_LEVELS_V1 = {
    "low_internal",
    "medium_user_affecting",
    "high_operator_review",
    "blocked_external",
    "blocked_destructive",
    "blocked_runtime",
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


def _normalise_lane_input(requested_lane_or_action: Any) -> str:
    return _compact_text(requested_lane_or_action, default="").strip().lower()


def _is_shared_scope(text: str) -> bool:
    return any(marker in text for marker in ("shared", "system", "cross-user", "cross user", "tenant", "account-wide", "workspace-wide"))


def _keyword_requested(text: str, keyword: str) -> bool:
    if keyword not in text:
        return False
    negations = (
        f"not {keyword}",
        f"don't {keyword}",
        f"do not {keyword}",
        f"without {keyword}",
        f"no {keyword}",
        f"never {keyword}",
    )
    return not any(marker in text for marker in negations)


def _is_external_request(text: str) -> bool:
    markers = ("send", "sending", "post", "posting", "publish", "publishing", "share externally", "external share", "export", "exported", "public export", "public posting")
    return any(_keyword_requested(text, marker) for marker in markers)


def _is_destructive_request(text: str) -> bool:
    markers = ("delete", "destroy", "remove", "overwrite", "revoke", "wipe", "pay", "payment", "contract", "legal", "medical", "financial")
    return any(_keyword_requested(text, marker) for marker in markers)


def _is_third_party_request(text: str) -> bool:
    markers = ("third-party", "third party", "integration", "external account", "external system", "third party system")
    return any(_keyword_requested(text, marker) for marker in markers)


def _is_runtime_request(text: str) -> bool:
    markers = ("runtime", "wire", "wiring", "chat wiring", "activate", "activation", "live", "deploy")
    return any(_keyword_requested(text, marker) for marker in markers)


def _is_public_request(text: str) -> bool:
    markers = ("public", "publicly", "public-ready", "public readiness", "product readiness", "publish", "publishing", "export")
    return any(_keyword_requested(text, marker) for marker in markers)


def _is_execution_request(text: str) -> bool:
    markers = ("execute", "executing", "run", "perform", "do it", "carry out", "launch")
    return any(_keyword_requested(text, marker) for marker in markers)


def classify_first_tool_lane_v1(requested_lane_or_action: Any) -> Dict[str, Any]:
    """Classify a requested lane/action into an approved or blocked lane metadata label."""
    text = _normalise_lane_input(requested_lane_or_action)
    if not text:
        return {
            "classification": "blocked",
            "lane_id": "unknown_lane",
            "lane_label": LANE_LABELS_V1["unknown_lane"],
            "matched_rule": "empty_input",
        }

    exact_matches = {
        "draft_artifact_creation": "draft_artifact_creation",
        "draft / artifact creation": "draft_artifact_creation",
        "project_plan_checklist": "project_plan_checklist",
        "project plan checklist": "project_plan_checklist",
        "project plan / checklist": "project_plan_checklist",
        "scoped_memory_project_update_proposal": "scoped_memory_project_update_proposal",
        "scoped memory project update proposal": "scoped_memory_project_update_proposal",
        "safe_internal_report_generation": "safe_internal_report_generation",
        "safe internal report generation": "safe_internal_report_generation",
        "support_escalation_record": "support_escalation_record",
        "support escalation record": "support_escalation_record",
        "external_sending_posting": "external_sending_posting",
        "external sending posting": "external_sending_posting",
        "public_publishing": "public_publishing",
        "public publishing": "public_publishing",
        "destructive_action": "destructive_action",
        "destructive action": "destructive_action",
        "payments_contracts_legal_medical_financial_authority": "payments_contracts_legal_medical_financial_authority",
        "payments contracts legal medical financial authority": "payments_contracts_legal_medical_financial_authority",
        "broad_third_party_integration": "broad_third_party_integration",
        "broad third party integration": "broad_third_party_integration",
        "autonomous_tool_discovery": "autonomous_tool_discovery",
        "autonomous tool discovery": "autonomous_tool_discovery",
        "automatic_behavior_update": "automatic_behavior_update",
        "automatic behavior update": "automatic_behavior_update",
        "runtime_chat_wiring": "runtime_chat_wiring",
        "runtime chat wiring": "runtime_chat_wiring",
        "public_product_readiness": "public_product_readiness",
        "public product readiness": "public_product_readiness",
    }
    if text in exact_matches:
        lane_id = exact_matches[text]
        classification = "approved" if lane_id in APPROVED_FIRST_TOOL_LANES_V1 else "blocked"
        return {
            "classification": classification,
            "lane_id": lane_id,
            "lane_label": LANE_LABELS_V1[lane_id],
            "matched_rule": f"exact:{text}",
        }

    if any(marker in text for marker in ("draft", "artifact", "checklist", "project plan", "project-plan")):
        return {
            "classification": "approved",
            "lane_id": "draft_artifact_creation" if "draft" in text or "artifact" in text else "project_plan_checklist",
            "lane_label": LANE_LABELS_V1["draft_artifact_creation" if "draft" in text or "artifact" in text else "project_plan_checklist"],
            "matched_rule": "keyword:planning_or_draft",
        }
    if any(marker in text for marker in ("memory", "proposal", "continuity", "confirm memory", "project memory")):
        return {
            "classification": "approved",
            "lane_id": "scoped_memory_project_update_proposal",
            "lane_label": LANE_LABELS_V1["scoped_memory_project_update_proposal"],
            "matched_rule": "keyword:memory_or_proposal",
        }
    if any(marker in text for marker in ("report", "summary", "review packet")):
        return {
            "classification": "approved",
            "lane_id": "safe_internal_report_generation",
            "lane_label": LANE_LABELS_V1["safe_internal_report_generation"],
            "matched_rule": "keyword:report",
        }
    if any(marker in text for marker in ("support", "escalation", "incident")):
        return {
            "classification": "approved",
            "lane_id": "support_escalation_record",
            "lane_label": LANE_LABELS_V1["support_escalation_record"],
            "matched_rule": "keyword:support",
        }

    if _is_external_request(text):
        return {
            "classification": "blocked",
            "lane_id": "external_sending_posting",
            "lane_label": LANE_LABELS_V1["external_sending_posting"],
            "matched_rule": "keyword:external",
        }
    if _is_destructive_request(text):
        return {
            "classification": "blocked",
            "lane_id": "destructive_action",
            "lane_label": LANE_LABELS_V1["destructive_action"],
            "matched_rule": "keyword:destructive",
        }
    if _is_third_party_request(text):
        return {
            "classification": "blocked",
            "lane_id": "broad_third_party_integration",
            "lane_label": LANE_LABELS_V1["broad_third_party_integration"],
            "matched_rule": "keyword:third_party",
        }
    if _is_runtime_request(text):
        return {
            "classification": "blocked",
            "lane_id": "runtime_chat_wiring",
            "lane_label": LANE_LABELS_V1["runtime_chat_wiring"],
            "matched_rule": "keyword:runtime",
        }
    if _is_public_request(text):
        return {
            "classification": "blocked",
            "lane_id": "public_product_readiness" if "readiness" in text or "product" in text else "public_publishing",
            "lane_label": LANE_LABELS_V1["public_product_readiness" if "readiness" in text or "product" in text else "public_publishing"],
            "matched_rule": "keyword:public",
        }

    return {
        "classification": "blocked",
        "lane_id": "unknown_lane",
        "lane_label": LANE_LABELS_V1["unknown_lane"],
        "matched_rule": "no_match",
    }


def _lane_profile(lane_id: str) -> Dict[str, Any]:
    lane = lane_id if lane_id in ALL_FIRST_TOOL_LANES_V1 else "unknown_lane"
    if lane == "draft_artifact_creation":
        return {
            "lane_label": LANE_LABELS_V1[lane],
            "action_class": ACTION_CLASSES_V1[lane],
            "risk_level": "low_internal",
            "approval_status": "not_required_internal_only",
            "execution_status": "planned_metadata_only",
            "rollback_deprecation_status": "rollback_available_metadata_only",
            "blocked_reason": "",
            "user_visible_status_phrase": "I can draft it, but I will not send it.",
            "requires_user_confirmation": False,
            "requires_operator_approval": False,
            "requires_separate_review": False,
            "allowed_now": True,
        }
    if lane == "project_plan_checklist":
        return {
            "lane_label": LANE_LABELS_V1[lane],
            "action_class": ACTION_CLASSES_V1[lane],
            "risk_level": "low_internal",
            "approval_status": "not_required_internal_only",
            "execution_status": "planned_metadata_only",
            "rollback_deprecation_status": "rollback_available_metadata_only",
            "blocked_reason": "",
            "user_visible_status_phrase": "This is a plan, not an executed action.",
            "requires_user_confirmation": False,
            "requires_operator_approval": False,
            "requires_separate_review": False,
            "allowed_now": True,
        }
    if lane == "scoped_memory_project_update_proposal":
        return {
            "lane_label": LANE_LABELS_V1[lane],
            "action_class": ACTION_CLASSES_V1[lane],
            "risk_level": "medium_user_affecting",
            "approval_status": "user_confirmation_required",
            "execution_status": "proposed_metadata_only",
            "rollback_deprecation_status": "rollback_available_metadata_only",
            "blocked_reason": "",
            "user_visible_status_phrase": "Should I update this project memory?",
            "requires_user_confirmation": True,
            "requires_operator_approval": False,
            "requires_separate_review": False,
            "allowed_now": True,
        }
    if lane == "safe_internal_report_generation":
        return {
            "lane_label": LANE_LABELS_V1[lane],
            "action_class": ACTION_CLASSES_V1[lane],
            "risk_level": "low_internal",
            "approval_status": "not_required_internal_only",
            "execution_status": "planned_metadata_only",
            "rollback_deprecation_status": "rollback_available_metadata_only",
            "blocked_reason": "",
            "user_visible_status_phrase": "This is an internal report unless approved for export.",
            "requires_user_confirmation": False,
            "requires_operator_approval": False,
            "requires_separate_review": False,
            "allowed_now": True,
        }
    if lane == "support_escalation_record":
        return {
            "lane_label": LANE_LABELS_V1[lane],
            "action_class": ACTION_CLASSES_V1[lane],
            "risk_level": "high_operator_review",
            "approval_status": "user_confirmation_required",
            "execution_status": "proposed_metadata_only",
            "rollback_deprecation_status": "rollback_available_metadata_only",
            "blocked_reason": "",
            "user_visible_status_phrase": "I can record this for support/escalation visibility.",
            "requires_user_confirmation": True,
            "requires_operator_approval": True,
            "requires_separate_review": False,
            "allowed_now": True,
        }

    if lane == "external_sending_posting":
        return {
            "lane_label": LANE_LABELS_V1[lane],
            "action_class": ACTION_CLASSES_V1[lane],
            "risk_level": "blocked_external",
            "approval_status": "blocked",
            "execution_status": "blocked",
            "rollback_deprecation_status": "blocked_metadata_only",
            "blocked_reason": "external sending/posting is blocked or requires separate approval",
            "user_visible_status_phrase": "This action is blocked because it would send or post externally.",
            "requires_user_confirmation": False,
            "requires_operator_approval": False,
            "requires_separate_review": True,
            "allowed_now": False,
        }
    if lane == "public_publishing":
        return {
            "lane_label": LANE_LABELS_V1[lane],
            "action_class": ACTION_CLASSES_V1[lane],
            "risk_level": "blocked_external",
            "approval_status": "blocked",
            "execution_status": "blocked",
            "rollback_deprecation_status": "blocked_metadata_only",
            "blocked_reason": "public publishing is blocked or requires separate approval",
            "user_visible_status_phrase": "This action is blocked because it would publish publicly.",
            "requires_user_confirmation": False,
            "requires_operator_approval": False,
            "requires_separate_review": True,
            "allowed_now": False,
        }
    if lane == "destructive_action":
        return {
            "lane_label": LANE_LABELS_V1[lane],
            "action_class": ACTION_CLASSES_V1[lane],
            "risk_level": "blocked_destructive",
            "approval_status": "blocked",
            "execution_status": "blocked",
            "rollback_deprecation_status": "blocked_metadata_only",
            "blocked_reason": "destructive action is blocked",
            "user_visible_status_phrase": "This action is blocked because it is destructive.",
            "requires_user_confirmation": False,
            "requires_operator_approval": False,
            "requires_separate_review": True,
            "allowed_now": False,
        }
    if lane == "payments_contracts_legal_medical_financial_authority":
        return {
            "lane_label": LANE_LABELS_V1[lane],
            "action_class": ACTION_CLASSES_V1[lane],
            "risk_level": "blocked_destructive",
            "approval_status": "blocked",
            "execution_status": "blocked",
            "rollback_deprecation_status": "blocked_metadata_only",
            "blocked_reason": "payments/contracts/legal/medical/financial authority is blocked",
            "user_visible_status_phrase": "This action is blocked because it requires restricted authority.",
            "requires_user_confirmation": False,
            "requires_operator_approval": True,
            "requires_separate_review": True,
            "allowed_now": False,
        }
    if lane == "broad_third_party_integration":
        return {
            "lane_label": LANE_LABELS_V1[lane],
            "action_class": ACTION_CLASSES_V1[lane],
            "risk_level": "blocked_external",
            "approval_status": "blocked",
            "execution_status": "blocked",
            "rollback_deprecation_status": "blocked_metadata_only",
            "blocked_reason": "broad third-party integration is blocked",
            "user_visible_status_phrase": "This action is blocked because it would reach a third party.",
            "requires_user_confirmation": False,
            "requires_operator_approval": True,
            "requires_separate_review": True,
            "allowed_now": False,
        }
    if lane == "autonomous_tool_discovery":
        return {
            "lane_label": LANE_LABELS_V1[lane],
            "action_class": ACTION_CLASSES_V1[lane],
            "risk_level": "blocked_runtime",
            "approval_status": "blocked",
            "execution_status": "blocked",
            "rollback_deprecation_status": "blocked_metadata_only",
            "blocked_reason": "autonomous tool discovery is blocked",
            "user_visible_status_phrase": "This action is blocked because autonomous tool discovery is not allowed.",
            "requires_user_confirmation": False,
            "requires_operator_approval": True,
            "requires_separate_review": True,
            "allowed_now": False,
        }
    if lane == "automatic_behavior_update":
        return {
            "lane_label": LANE_LABELS_V1[lane],
            "action_class": ACTION_CLASSES_V1[lane],
            "risk_level": "blocked_runtime",
            "approval_status": "blocked",
            "execution_status": "blocked",
            "rollback_deprecation_status": "blocked_metadata_only",
            "blocked_reason": "automatic behavior update is blocked",
            "user_visible_status_phrase": "This action is blocked because it would update behavior automatically.",
            "requires_user_confirmation": False,
            "requires_operator_approval": True,
            "requires_separate_review": True,
            "allowed_now": False,
        }
    if lane == "runtime_chat_wiring":
        return {
            "lane_label": LANE_LABELS_V1[lane],
            "action_class": ACTION_CLASSES_V1[lane],
            "risk_level": "blocked_runtime",
            "approval_status": "blocked",
            "execution_status": "blocked",
            "rollback_deprecation_status": "blocked_metadata_only",
            "blocked_reason": "runtime chat wiring is blocked",
            "user_visible_status_phrase": "This action is blocked because it would wire runtime chat behavior.",
            "requires_user_confirmation": False,
            "requires_operator_approval": True,
            "requires_separate_review": True,
            "allowed_now": False,
        }
    if lane == "public_product_readiness":
        return {
            "lane_label": LANE_LABELS_V1[lane],
            "action_class": ACTION_CLASSES_V1[lane],
            "risk_level": "blocked_runtime",
            "approval_status": "blocked",
            "execution_status": "blocked",
            "rollback_deprecation_status": "blocked_metadata_only",
            "blocked_reason": "public product readiness claims are blocked",
            "user_visible_status_phrase": "This action is blocked because public product readiness is not approved.",
            "requires_user_confirmation": False,
            "requires_operator_approval": True,
            "requires_separate_review": True,
            "allowed_now": False,
        }

    return {
        "lane_label": LANE_LABELS_V1["unknown_lane"],
        "action_class": ACTION_CLASSES_V1["unknown_lane"],
        "risk_level": "blocked_runtime",
        "approval_status": "blocked",
        "execution_status": "blocked",
        "rollback_deprecation_status": "blocked_metadata_only",
        "blocked_reason": "unknown lane or action is blocked",
        "user_visible_status_phrase": "This action is blocked because the lane is unknown.",
        "requires_user_confirmation": False,
        "requires_operator_approval": True,
        "requires_separate_review": True,
        "allowed_now": False,
    }


def _derive_flags(requested_action: str, lane_id: str) -> Dict[str, bool]:
    text = requested_action.lower()
    external = _is_external_request(text) or lane_id in {"external_sending_posting", "public_publishing"}
    destructive = _is_destructive_request(text) or lane_id in {"destructive_action", "payments_contracts_legal_medical_financial_authority"}
    third_party = _is_third_party_request(text) or lane_id == "broad_third_party_integration"
    runtime = _is_runtime_request(text) or lane_id in {"runtime_chat_wiring", "autonomous_tool_discovery", "automatic_behavior_update"}
    public_export = _is_public_request(text) or lane_id in {"public_publishing", "public_product_readiness"}
    return {
        "external_action_requested": external,
        "destructive_action_requested": destructive,
        "third_party_action_requested": third_party,
        "runtime_activation_requested": runtime,
        "public_export_requested": public_export,
    }


def _approval_from_flags(base_status: str, lane_id: str, flags: Mapping[str, bool], owner_user_scope: str, tenant_account_scope: str, requested_action: str) -> tuple[str, bool, bool, bool, bool, str, str]:
    approval_status = base_status
    execution_status = "planned_metadata_only" if lane_id in {"draft_artifact_creation", "project_plan_checklist", "safe_internal_report_generation"} else "proposed_metadata_only"
    allowed_now = True
    blocked_reason = ""
    requires_user_confirmation = base_status == "user_confirmation_required"
    requires_operator_approval = base_status == "operator_approval_required"
    requires_separate_review = base_status == "separate_review_required"

    if lane_id in BLOCKED_FIRST_TOOL_LANES_V1:
        approval_status = "blocked"
        execution_status = "blocked"
        allowed_now = False
        blocked_reason = _lane_profile(lane_id)["blocked_reason"]
        requires_user_confirmation = False
        requires_operator_approval = lane_id in {"payments_contracts_legal_medical_financial_authority", "broad_third_party_integration", "autonomous_tool_discovery", "automatic_behavior_update", "runtime_chat_wiring", "public_product_readiness"}
        requires_separate_review = True
        return approval_status, allowed_now, requires_user_confirmation, requires_operator_approval, requires_separate_review, execution_status, blocked_reason

    if lane_id == "scoped_memory_project_update_proposal":
        if _is_shared_scope(owner_user_scope) or _is_shared_scope(tenant_account_scope) or _is_shared_scope(requested_action):
            approval_status = "operator_approval_required"
            requires_user_confirmation = False
            requires_operator_approval = True
        else:
            approval_status = "user_confirmation_required"
            requires_user_confirmation = True
            requires_operator_approval = False
    elif lane_id == "support_escalation_record":
        if "personal data" in requested_action.lower() or "personal_data" in requested_action.lower():
            approval_status = "user_confirmation_required"
            requires_user_confirmation = True
        if _is_shared_scope(owner_user_scope) or _is_shared_scope(tenant_account_scope) or _is_shared_scope(requested_action):
            approval_status = "operator_approval_required"
            requires_user_confirmation = False
            requires_operator_approval = True
    elif lane_id == "safe_internal_report_generation":
        if flags["public_export_requested"]:
            approval_status = "separate_review_required"
            requires_separate_review = True
            allowed_now = False
            execution_status = "blocked"
            blocked_reason = "export/public use requires separate approval"
    elif lane_id == "project_plan_checklist":
        requested = requested_action.lower()
        if any(marker in requested for marker in ("execute", "executing", "run", "perform", "carry out", "launch")):
            approval_status = "separate_review_required"
            requires_separate_review = True
            allowed_now = False
            execution_status = "blocked"
            blocked_reason = "plan execution is blocked until later approval"
    elif lane_id in {"draft_artifact_creation", "support_escalation_record", "scoped_memory_project_update_proposal"}:
        if flags["external_action_requested"] or flags["public_export_requested"]:
            approval_status = "separate_review_required"
            requires_separate_review = True
            allowed_now = False
            execution_status = "blocked"
            blocked_reason = "external sending/publishing/export requires separate approval"

    if flags["destructive_action_requested"]:
        approval_status = "blocked"
        allowed_now = False
        execution_status = "blocked"
        blocked_reason = "destructive action is blocked"
        requires_user_confirmation = False
        requires_operator_approval = True
        requires_separate_review = True
    if flags["third_party_action_requested"]:
        approval_status = "blocked"
        allowed_now = False
        execution_status = "blocked"
        blocked_reason = "third-party action is blocked"
        requires_user_confirmation = False
        requires_operator_approval = True
        requires_separate_review = True
    if flags["runtime_activation_requested"]:
        approval_status = "blocked"
        allowed_now = False
        execution_status = "blocked"
        blocked_reason = "runtime activation or chat wiring is blocked"
        requires_user_confirmation = False
        requires_operator_approval = True
        requires_separate_review = True
    if flags["external_action_requested"] and lane_id not in {"draft_artifact_creation", "project_plan_checklist", "safe_internal_report_generation"}:
        if approval_status != "blocked":
            approval_status = "separate_review_required"
        allowed_now = False
        if not blocked_reason:
            blocked_reason = "external sending/posting/export requires separate approval"
        execution_status = "blocked"
        requires_separate_review = True
    if flags["public_export_requested"] and lane_id not in {"safe_internal_report_generation"}:
        if approval_status != "blocked":
            approval_status = "separate_review_required"
        allowed_now = False
        if not blocked_reason:
            blocked_reason = "public export requires separate approval"
        execution_status = "blocked"
        requires_separate_review = True

    if approval_status == "blocked":
        allowed_now = False
        execution_status = "blocked"
    if approval_status == "separate_review_required":
        allowed_now = False
        if not blocked_reason:
            blocked_reason = "separate review required before proceeding"
    return approval_status, allowed_now, requires_user_confirmation, requires_operator_approval, requires_separate_review, execution_status, blocked_reason


def _build_denied_authority_map() -> Dict[str, bool]:
    return {field: False for field in _DENIED_AUTHORITY_FIELDS}


def build_first_tool_lane_contract_v1(
    requested_lane_or_action: Any,
    *,
    lane_id: str | None = None,
    project_id: Any = "project_unassigned",
    memory_reference_ids: Any = None,
    owner_user_scope: Any = "self",
    tenant_account_scope: Any = "self",
    requested_action: Any | None = None,
    risk_level: str | None = None,
    approval_status: str | None = None,
    execution_status: str | None = None,
    failure_count: Any = 0,
    rollback_deprecation_status: str | None = None,
    blocked_reason: Any | None = None,
    audit_note: Any | None = None,
    created_marker: Any | None = None,
    updated_marker: Any | None = None,
    operator_visibility: bool = True,
    user_visible_status_phrase: Any | None = None,
    external_action_requested: bool | None = None,
    destructive_action_requested: bool | None = None,
    third_party_action_requested: bool | None = None,
    runtime_activation_requested: bool | None = None,
    public_export_requested: bool | None = None,
    requires_user_confirmation: bool | None = None,
    requires_operator_approval: bool | None = None,
    requires_separate_review: bool | None = None,
) -> Dict[str, Any]:
    """Build a metadata-only first-tool-lane contract.

    The contract is intentionally non-executing and purely descriptive.
    """
    classification = classify_first_tool_lane_v1(lane_id if lane_id is not None else requested_lane_or_action)
    resolved_lane_id = lane_id or classification["lane_id"]
    if resolved_lane_id not in ALL_FIRST_TOOL_LANES_V1:
        resolved_lane_id = "unknown_lane"
    profile = _lane_profile(resolved_lane_id)

    safe_requested_action = _compact_text(requested_action if requested_action is not None else requested_lane_or_action, default="")
    safe_project_id = _compact_text(project_id, default="project_unassigned")
    safe_owner_scope = _compact_text(owner_user_scope, default="self")
    safe_tenant_scope = _compact_text(tenant_account_scope, default="self")
    safe_memory_refs = _listify(memory_reference_ids)
    safe_failure_count = int(failure_count) if isinstance(failure_count, bool) is False else int(bool(failure_count))
    if safe_failure_count < 0:
        safe_failure_count = 0
    if safe_failure_count > MAX_FAILURE_COUNT_V1:
        safe_failure_count = MAX_FAILURE_COUNT_V1

    derived_flags = _derive_flags(safe_requested_action, resolved_lane_id)
    if external_action_requested is not None:
        derived_flags["external_action_requested"] = bool(external_action_requested)
    if destructive_action_requested is not None:
        derived_flags["destructive_action_requested"] = bool(destructive_action_requested)
    if third_party_action_requested is not None:
        derived_flags["third_party_action_requested"] = bool(third_party_action_requested)
    if runtime_activation_requested is not None:
        derived_flags["runtime_activation_requested"] = bool(runtime_activation_requested)
    if public_export_requested is not None:
        derived_flags["public_export_requested"] = bool(public_export_requested)

    base_approval_status = approval_status or profile["approval_status"]
    base_execution_status = execution_status or profile["execution_status"]
    base_risk_level = risk_level or profile["risk_level"]
    base_rollback = rollback_deprecation_status or profile["rollback_deprecation_status"]
    base_blocked_reason = _compact_text(blocked_reason, default=profile["blocked_reason"])
    base_user_phrase = _compact_text(user_visible_status_phrase, default=profile["user_visible_status_phrase"])
    base_created = _compact_text(created_marker, default=f"created_metadata_only_v1:{resolved_lane_id}")
    base_updated = _compact_text(updated_marker, default=f"updated_metadata_only_v1:{resolved_lane_id}")
    base_audit = _compact_text(audit_note, default=f"metadata-only contract for {resolved_lane_id}; no runtime action authorized")

    approval_status_out, allowed_now_out, requires_user_confirmation_out, requires_operator_approval_out, requires_separate_review_out, execution_status_out, blocked_reason_out = _approval_from_flags(
        base_approval_status,
        resolved_lane_id,
        derived_flags,
        safe_owner_scope,
        safe_tenant_scope,
        safe_requested_action,
    )

    if blocked_reason_out and not base_blocked_reason:
        base_blocked_reason = blocked_reason_out
    if not allowed_now_out and base_blocked_reason:
        base_user_phrase = f"This action is blocked because {base_blocked_reason}."
    elif execution_status_out == "blocked":
        base_user_phrase = profile["user_visible_status_phrase"]
    if safe_failure_count > 0 and execution_status_out != "blocked":
        execution_status_out = "failed_metadata_only"
        base_user_phrase = f"{base_user_phrase} This failed; I will not claim success."

    if resolved_lane_id == "unknown_lane":
        approval_status_out = "blocked"
        execution_status_out = "blocked"
        allowed_now_out = False
        base_blocked_reason = base_blocked_reason or "unknown lane or action is blocked"
        requires_user_confirmation_out = False
        requires_operator_approval_out = True
        requires_separate_review_out = True
        base_risk_level = "blocked_runtime"

    contract: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION_V1,
        "lane_id": resolved_lane_id,
        "lane_label": profile["lane_label"],
        "action_class": profile["action_class"],
        "project_id": safe_project_id,
        "memory_reference_ids": safe_memory_refs,
        "owner_user_scope": safe_owner_scope,
        "tenant_account_scope": safe_tenant_scope,
        "requested_action": safe_requested_action,
        "risk_level": base_risk_level,
        "approval_status": approval_status_out,
        "execution_status": execution_status_out,
        "failure_count": safe_failure_count,
        "rollback_deprecation_status": base_rollback,
        "blocked_reason": base_blocked_reason,
        "audit_note": base_audit,
        "created_marker": base_created,
        "updated_marker": base_updated,
        "operator_visibility": bool(operator_visibility),
        "user_visible_status_phrase": base_user_phrase,
        "external_action_requested": bool(derived_flags["external_action_requested"]),
        "destructive_action_requested": bool(derived_flags["destructive_action_requested"]),
        "third_party_action_requested": bool(derived_flags["third_party_action_requested"]),
        "runtime_activation_requested": bool(derived_flags["runtime_activation_requested"]),
        "public_export_requested": bool(derived_flags["public_export_requested"]),
        "requires_user_confirmation": bool(requires_user_confirmation_out),
        "requires_operator_approval": bool(requires_operator_approval_out),
        "requires_separate_review": bool(requires_separate_review_out),
        "allowed_now": bool(allowed_now_out),
    }
    denied_authority = _build_denied_authority_map()
    contract.update(denied_authority)
    contract["denied_authority"] = copy.deepcopy(denied_authority)
    return to_first_tool_lane_contract_json_safe_v1(contract)


def validate_first_tool_lane_contract_v1(contract: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate first-tool-lane contract metadata without raising for normal invalid input."""
    safe = _json_safe(contract)
    violations: list[Dict[str, str]] = []

    def add(category: str, path: str, message: str) -> None:
        violations.append({"category": category, "path": path or "$", "message": message})

    required_fields = [
        "schema_version",
        "lane_id",
        "lane_label",
        "action_class",
        "project_id",
        "memory_reference_ids",
        "owner_user_scope",
        "tenant_account_scope",
        "requested_action",
        "risk_level",
        "approval_status",
        "execution_status",
        "failure_count",
        "rollback_deprecation_status",
        "blocked_reason",
        "audit_note",
        "created_marker",
        "updated_marker",
        "operator_visibility",
        "user_visible_status_phrase",
        "external_action_requested",
        "destructive_action_requested",
        "third_party_action_requested",
        "runtime_activation_requested",
        "public_export_requested",
        "requires_user_confirmation",
        "requires_operator_approval",
        "requires_separate_review",
        "allowed_now",
        "denied_authority",
    ] + list(_DENIED_AUTHORITY_FIELDS)

    for field in required_fields:
        if field not in safe:
            add("missing_field", field, f"missing required field: {field}")

    if safe.get("schema_version") != SCHEMA_VERSION_V1:
        add("schema", "schema_version", f"schema_version must be {SCHEMA_VERSION_V1}")
    lane_id = _compact_text(safe.get("lane_id"), default="")
    if lane_id not in ALL_FIRST_TOOL_LANES_V1 and lane_id != "unknown_lane":
        add("lane", "lane_id", "unknown lane must fail closed")
    if lane_id == "unknown_lane":
        add("lane", "lane_id", "unknown lane or action is not allowed")

    if lane_id in ALL_FIRST_TOOL_LANES_V1 and safe.get("lane_label") != LANE_LABELS_V1.get(lane_id):
        add("schema", "lane_label", "lane_label must match lane_id")
    if lane_id in ALL_FIRST_TOOL_LANES_V1 and safe.get("action_class") != ACTION_CLASSES_V1.get(lane_id):
        add("schema", "action_class", "action_class must match lane_id")

    if not isinstance(safe.get("project_id"), str) or not safe.get("project_id"):
        add("scope", "project_id", "project_id must be a non-empty string")
    if not isinstance(safe.get("memory_reference_ids"), list):
        add("source", "memory_reference_ids", "memory_reference_ids must be a list")
    if not isinstance(safe.get("owner_user_scope"), str) or not safe.get("owner_user_scope"):
        add("scope", "owner_user_scope", "owner_user_scope must be a non-empty string")
    if not isinstance(safe.get("tenant_account_scope"), str) or not safe.get("tenant_account_scope"):
        add("scope", "tenant_account_scope", "tenant_account_scope must be a non-empty string")
    if not isinstance(safe.get("requested_action"), str) or not safe.get("requested_action"):
        add("status", "requested_action", "requested_action must be a non-empty string")

    if safe.get("risk_level") not in RISK_LEVELS_V1:
        add("schema", "risk_level", "risk_level must be one of the approved metadata levels")
    if safe.get("approval_status") not in APPROVAL_STATUSES_V1:
        add("status", "approval_status", "approval_status must be one of the approved metadata values")
    if safe.get("execution_status") not in EXECUTION_STATUSES_V1:
        add("status", "execution_status", "execution_status must be one of the approved metadata values")

    failure_count = safe.get("failure_count")
    if not isinstance(failure_count, int) or isinstance(failure_count, bool):
        add("status", "failure_count", "failure_count must be an integer")
    elif failure_count < 0 or failure_count > MAX_FAILURE_COUNT_V1:
        add("status", "failure_count", f"failure_count must be between 0 and {MAX_FAILURE_COUNT_V1}")
    if failure_count and safe.get("execution_status") not in {"failed_metadata_only", "blocked", "deprecated_metadata_only"}:
        add("failure", "execution_status", "failure metadata must not claim success")

    if not isinstance(safe.get("operator_visibility"), bool) or safe.get("operator_visibility") is not True:
        add("visibility", "operator_visibility", "operator_visibility must be true")

    phrase = _compact_text(safe.get("user_visible_status_phrase"), default="")
    if not phrase:
        add("status", "user_visible_status_phrase", "user_visible_status_phrase must be present")
    elif lane_id == "draft_artifact_creation" and "draft" not in phrase.lower():
        add("status", "user_visible_status_phrase", "draft lane phrase must mention draft")
    elif lane_id == "project_plan_checklist" and "plan" not in phrase.lower():
        add("status", "user_visible_status_phrase", "project plan lane phrase must mention plan")
    elif lane_id == "scoped_memory_project_update_proposal" and not any(token in phrase.lower() for token in ("memory", "proposal")):
        add("status", "user_visible_status_phrase", "memory lane phrase must mention memory or proposal")
    elif lane_id == "safe_internal_report_generation" and "report" not in phrase.lower():
        add("status", "user_visible_status_phrase", "report lane phrase must mention report")
    elif lane_id == "support_escalation_record" and not any(token in phrase.lower() for token in ("support", "escalation")):
        add("status", "user_visible_status_phrase", "support lane phrase must mention support or escalation")
    elif lane_id in BLOCKED_FIRST_TOOL_LANES_V1 and "blocked" not in phrase.lower():
        add("status", "user_visible_status_phrase", "blocked lane phrase must mention blocked")

    blocked_reason = _compact_text(safe.get("blocked_reason"), default="")
    if lane_id in BLOCKED_FIRST_TOOL_LANES_V1 and not blocked_reason:
        add("blocked", "blocked_reason", "blocked contracts must include blocked_reason")
    if lane_id not in BLOCKED_FIRST_TOOL_LANES_V1 and safe.get("approval_status") == "blocked" and not blocked_reason:
        add("blocked", "blocked_reason", "blocked contracts must include blocked_reason")

    if safe.get("approval_status") == "blocked" and safe.get("allowed_now") is not False:
        add("status", "allowed_now", "blocked contracts must not be allowed now")
    if safe.get("execution_status") == "blocked" and safe.get("allowed_now") is not False:
        add("status", "allowed_now", "blocked contracts must not be allowed now")
    if safe.get("approval_status") == "separate_review_required" and safe.get("allowed_now") is not False:
        add("status", "allowed_now", "separate review required contracts must not be allowed now")

    denied = safe.get("denied_authority")
    if not isinstance(denied, Mapping):
        add("authority", "denied_authority", "denied_authority must be a mapping")
    else:
        for field in _DENIED_AUTHORITY_FIELDS:
            if denied.get(field) is not False:
                add("authority", f"denied_authority.{field}", f"{field} must be false")
            if safe.get(field) is not False:
                add("authority", field, f"{field} must be false")

    if safe.get("external_action_requested") is True and safe.get("approval_status") == "not_required_internal_only":
        add("boundary", "external_action_requested", "external actions must not be marked internal-only")
    if safe.get("destructive_action_requested") is True and safe.get("approval_status") != "blocked":
        add("boundary", "destructive_action_requested", "destructive actions must be blocked")
    if safe.get("third_party_action_requested") is True and safe.get("approval_status") != "blocked":
        add("boundary", "third_party_action_requested", "third-party actions must be blocked")
    if safe.get("runtime_activation_requested") is True and safe.get("approval_status") != "blocked":
        add("boundary", "runtime_activation_requested", "runtime activation must be blocked")
    if safe.get("public_export_requested") is True and safe.get("approval_status") not in {"blocked", "separate_review_required"}:
        add("boundary", "public_export_requested", "public export must be blocked or require separate review")

    if safe.get("approval_status") == "blocked" and safe.get("execution_status") not in {"blocked", "failed_metadata_only", "deprecated_metadata_only"}:
        add("status", "execution_status", "blocked contracts must remain blocked")

    return {
        "validation_schema": "first_tool_lanes_contract_validation_v1",
        "validation_status": "accepted" if not violations else "rejected",
        "valid": not violations,
        "violation_count": len(violations),
        "lane_id": lane_id or "unknown_lane",
        "violations": violations,
    }


def evaluate_first_tool_lane_approval_v1(contract: Mapping[str, Any]) -> Dict[str, Any]:
    """Return approval/blocked/deferred metadata for a first-tool-lane contract."""
    safe = _json_safe(contract)
    validation = validate_first_tool_lane_contract_v1(safe)
    approval_status = _compact_text(safe.get("approval_status"), default="blocked")
    execution_status = _compact_text(safe.get("execution_status"), default="blocked")
    blocked = approval_status == "blocked" or execution_status == "blocked" or not validation["valid"]
    deferred = approval_status in {"user_confirmation_required", "operator_approval_required", "separate_review_required"}
    if blocked:
        decision = "blocked"
    elif safe.get("failure_count", 0):
        decision = "deferred"
    elif deferred:
        decision = "deferred"
    else:
        decision = "approved_metadata_only"
    return {
        "decision": decision,
        "blocked": blocked,
        "deferred": deferred or decision == "deferred",
        "allowed_now": bool(safe.get("allowed_now", False)) and not blocked,
        "approval_status": approval_status,
        "execution_status": execution_status,
        "requires_user_confirmation": bool(safe.get("requires_user_confirmation", False)),
        "requires_operator_approval": bool(safe.get("requires_operator_approval", False)),
        "requires_separate_review": bool(safe.get("requires_separate_review", False)),
        "blocked_reason": _compact_text(safe.get("blocked_reason"), default=""),
        "validation_status": validation["validation_status"],
        "violation_count": validation["violation_count"],
    }


def summarize_first_tool_lane_contract_v1(contract: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a compact JSON-safe summary of a first-tool-lane contract."""
    safe = _json_safe(contract)
    summary = {
        "schema_version": safe.get("schema_version"),
        "lane_id": safe.get("lane_id"),
        "lane_label": safe.get("lane_label"),
        "action_class": safe.get("action_class"),
        "approval_status": safe.get("approval_status"),
        "execution_status": safe.get("execution_status"),
        "risk_level": safe.get("risk_level"),
        "allowed_now": safe.get("allowed_now"),
        "blocked_reason": safe.get("blocked_reason"),
        "failure_count": safe.get("failure_count"),
        "operator_visibility": safe.get("operator_visibility"),
        "user_visible_status_phrase": safe.get("user_visible_status_phrase"),
        "requested_action": _compact_text(safe.get("requested_action"), default=""),
    }
    summary["validation_status"] = validate_first_tool_lane_contract_v1(safe)
    return to_first_tool_lane_contract_json_safe_v1(summary)


def to_first_tool_lane_contract_json_safe_v1(contract: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a deep JSON-safe copy of a contract-like mapping."""
    return _json_safe(contract)


def build_initial_first_tool_lane_contract_examples_v1() -> list[Dict[str, Any]]:
    """Return synthetic examples only."""
    examples = [
        build_first_tool_lane_contract_v1(
            "draft_artifact_creation",
            project_id="project_alpha",
            memory_reference_ids=["mem_draft_001"],
            owner_user_scope="self",
            tenant_account_scope="self",
            requested_action="Draft a project note",
        ),
        build_first_tool_lane_contract_v1(
            "project_plan_checklist",
            project_id="project_alpha",
            memory_reference_ids=["mem_plan_001"],
            owner_user_scope="self",
            tenant_account_scope="self",
            requested_action="Create a project checklist",
        ),
        build_first_tool_lane_contract_v1(
            "scoped_memory_project_update_proposal",
            project_id="project_alpha",
            memory_reference_ids=["mem_scope_001"],
            owner_user_scope="self",
            tenant_account_scope="self",
            requested_action="Propose an update to project memory",
        ),
        build_first_tool_lane_contract_v1(
            "safe_internal_report_generation",
            project_id="project_alpha",
            memory_reference_ids=["mem_report_001"],
            owner_user_scope="self",
            tenant_account_scope="self",
            requested_action="Generate an internal report",
        ),
        build_first_tool_lane_contract_v1(
            "support_escalation_record",
            project_id="project_alpha",
            memory_reference_ids=["mem_support_001"],
            owner_user_scope="self",
            tenant_account_scope="self",
            requested_action="Record a support escalation note",
        ),
        build_first_tool_lane_contract_v1(
            "external_sending_posting",
            project_id="project_alpha",
            memory_reference_ids=["mem_block_001"],
            owner_user_scope="self",
            tenant_account_scope="self",
            requested_action="Send a message externally",
        ),
        build_first_tool_lane_contract_v1(
            "destructive_action",
            project_id="project_alpha",
            memory_reference_ids=["mem_block_002"],
            owner_user_scope="self",
            tenant_account_scope="self",
            requested_action="Delete a record",
        ),
    ]
    return [to_first_tool_lane_contract_json_safe_v1(example) for example in examples]


__all__ = [
    "SCHEMA_VERSION_V1",
    "APPROVED_FIRST_TOOL_LANES_V1",
    "BLOCKED_FIRST_TOOL_LANES_V1",
    "ALL_FIRST_TOOL_LANES_V1",
    "LANE_LABELS_V1",
    "ACTION_CLASSES_V1",
    "classify_first_tool_lane_v1",
    "build_first_tool_lane_contract_v1",
    "validate_first_tool_lane_contract_v1",
    "evaluate_first_tool_lane_approval_v1",
    "summarize_first_tool_lane_contract_v1",
    "to_first_tool_lane_contract_json_safe_v1",
    "build_initial_first_tool_lane_contract_examples_v1",
]
