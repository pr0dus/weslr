"""
WESLR chat.weslr.de Slice 2 — Runtime Wrapper Skeleton V1

Deterministic, pure-Python, no-I/O wrapper boundary.

This module provides a metadata-only authorization boundary that decides
whether a runtime action may proceed. It does NOT:
  - import or call weslr.chat_responder, main, dialogue, chat_ui,
    backend server files, provider/model code, or any protected runtime
    module
  - perform subprocess, network, or filesystem write operations
  - retain raw prompt text, raw reply text, credentials, PII,
    hidden prompts, system prompts, chain-of-thought traces,
    provider/LLM API responses, or real shadow-call outputs
  - claim AGI / sentience / consciousness / benchmark / public-science
    / production-ready / live-public-runtime

Default behavior is DENY. Only explicitly listed safe actions may be
authorized. Safe actions are metadata-only (read-only inspections):
  - health_check_read
  - status_read
  - operator_review_packet_read

All other actions return DENIED or FALLBACK with structured metadata.
"""

from __future__ import annotations

# No external imports; pure stdlib only.
import json
from typing import Any, Dict, List, Optional, Tuple


# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

WRAPPER_VERSION = "weslr-runtime-wrapper-v1"

# Explicit safe actions (metadata-only reads; no provider, no provider API,
# no shadow calls, no self-modification, no public claims).
SAFE_ACTIONS_V1 = frozenset({
    "health_check_read",
    "status_read",
    "operator_review_packet_read",
})

# Reason labels (machine-readable; safe to log; never expose internal text).
REASON_DENY_DEFAULT = "deny_default_no_authorization"
REASON_DENY_UNKNOWN_ACTION = "deny_unknown_action"
REASON_DENY_EMPTY_CAPABILITY_SET = "deny_empty_capability_set"
REASON_DENY_PROTECTED_FILE = "deny_protected_file_authority"
REASON_DENY_CHATRESPONDER = "deny_chatresponder_authority"
REASON_DENY_RESPOND_CHAT = "deny_respond_chat_authority"
REASON_DENY_PROVIDER_MODEL = "deny_provider_or_model_authority"
REASON_DENY_INFRA = "deny_infra_change_authority"
REASON_DENY_MEMORY = "deny_memory_change_authority"
REASON_DENY_PROJECT = "deny_project_change_authority"
REASON_DENY_PUBLIC_CLAIM = "deny_public_claim_authority"
REASON_DENY_RUNTIME_MODIFY = "deny_runtime_modify_authority"
REASON_DENY_MALFORMED_PACKET = "deny_malformed_packet"
REASON_FALLBACK_OPERATOR_REVIEW = "fallback_operator_review_required"

DECISION_AUTHORIZED = "authorized"
DECISION_DENIED = "denied"
DECISION_FALLBACK = "fallback"


# ----------------------------------------------------------------------------
# Data model
# ----------------------------------------------------------------------------

def build_runtime_authorization_request_v1(
    *,
    action: str,
    identity_id: str,
    session_id: str,
    capability_set: Optional[List[str]] = None,
    operator_approval_token_present: bool = False,
    red_zone_acknowledged: bool = False,
    requested_at: Optional[str] = None,
    source_context: Optional[Dict[str, Any]] = None,
    # Authority flags — caller declares what authority the request
    # would require. These are typically False for all callers.
    can_call_protected_files: bool = False,
    can_execute_chatresponder: bool = False,
    can_run_respond_chat: bool = False,
    can_call_provider_or_model: bool = False,
    can_modify_runtime: bool = False,
    can_modify_project: bool = False,
    can_modify_memory: bool = False,
    can_change_infra: bool = False,
    can_create_public_claim: bool = False,
) -> Dict[str, Any]:
    """
    Build a deterministic authorization request packet (no I/O).

    The packet is a plain dict, suitable for safe in-memory handoff.
    Raw content is NOT retained in the packet.
    """
    return {
        "wrapper_version": WRAPPER_VERSION,
        "action": str(action) if action is not None else "",
        "identity_id": str(identity_id) if identity_id is not None else "",
        "session_id": str(session_id) if session_id is not None else "",
        "capability_set": list(capability_set) if capability_set else [],
        "operator_approval_token_present": bool(operator_approval_token_present),
        "red_zone_acknowledged": bool(red_zone_acknowledged),
        "requested_at": str(requested_at) if requested_at is not None else "",
        "source_context": dict(source_context) if source_context else {},
        "denied_authority": {
            "can_call_protected_files": bool(can_call_protected_files),
            "can_execute_chatresponder": bool(can_execute_chatresponder),
            "can_run_respond_chat": bool(can_run_respond_chat),
            "can_call_provider_or_model": bool(can_call_provider_or_model),
            "can_modify_runtime": bool(can_modify_runtime),
            "can_modify_project": bool(can_modify_project),
            "can_modify_memory": bool(can_modify_memory),
            "can_change_infra": bool(can_change_infra),
            "can_create_public_claim": bool(can_create_public_claim),
        },
    }


def validate_runtime_authorization_request_v1(packet: Any) -> Tuple[bool, List[str]]:
    """
    Validate the packet structure. Returns (is_valid, error_labels).
    Never raises. Pure structural check; no I/O.
    """
    errors: List[str] = []
    if not isinstance(packet, dict):
        errors.append("packet_not_dict")
        return False, errors
    for key in (
        "wrapper_version",
        "action",
        "identity_id",
        "session_id",
        "capability_set",
        "operator_approval_token_present",
        "red_zone_acknowledged",
        "requested_at",
        "source_context",
        "denied_authority",
    ):
        if key not in packet:
            errors.append(f"missing_field:{key}")
    if "capability_set" in packet and not isinstance(packet["capability_set"], list):
        errors.append("capability_set_not_list")
    if "denied_authority" in packet and not isinstance(packet["denied_authority"], dict):
        errors.append("denied_authority_not_dict")
    # action must be a non-empty string
    if "action" in packet and not isinstance(packet["action"], str):
        errors.append("action_not_string")
    return (len(errors) == 0), errors


# ----------------------------------------------------------------------------
# Authorization decision
# ----------------------------------------------------------------------------

def _check_authority(packet: Dict[str, Any]) -> List[str]:
    """Return list of denial labels for any authority that is set True.

    Deny by default. Any authority flag set to True immediately denies.
    """
    da = packet.get("denied_authority", {}) or {}
    labels: List[str] = []
    flag_to_label = {
        "can_call_protected_files": REASON_DENY_PROTECTED_FILE,
        "can_execute_chatresponder": REASON_DENY_CHATRESPONDER,
        "can_run_respond_chat": REASON_DENY_RESPOND_CHAT,
        "can_call_provider_or_model": REASON_DENY_PROVIDER_MODEL,
        "can_modify_runtime": REASON_DENY_RUNTIME_MODIFY,
        "can_modify_project": REASON_DENY_PROJECT,
        "can_modify_memory": REASON_DENY_MEMORY,
        "can_change_infra": REASON_DENY_INFRA,
        "can_create_public_claim": REASON_DENY_PUBLIC_CLAIM,
    }
    for flag, label in flag_to_label.items():
        if da.get(flag, False) is True:
            labels.append(label)
    return labels


def authorize_runtime_action_v1(packet: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decide whether a runtime action may proceed.

    Returns a structured result dict with metadata only. No raw content.
    Default behavior is DENY. Only safe actions in SAFE_ACTIONS_V1 may
    be AUTHORIZED, and only if no authority flag is set and the
    capability_set is non-empty.
    """
    base = {
        "wrapper_version": WRAPPER_VERSION,
        "authorized": False,
        "decision": DECISION_DENIED,
        "reason_labels": [REASON_DENY_DEFAULT],
        "safe_summary": "",
        "requires_operator_review": False,
        "denied_authority": packet.get("denied_authority", {}) if isinstance(packet, dict) else {},
        "raw_content_retained": False,
        "protected_file_called": False,
        "respond_chat_called": False,
        "provider_or_model_called": False,
        "infra_changed": False,
        "memory_changed": False,
        "project_changed": False,
    }

    # Validate the packet first.
    ok, errs = validate_runtime_authorization_request_v1(packet)
    if not ok:
        return {
            **base,
            "reason_labels": [REASON_DENY_MALFORMED_PACKET] + [f"err:{e}" for e in errs],
        }

    action = packet.get("action", "") or ""
    capability_set = packet.get("capability_set", []) or []
    red_zone_acknowledged = bool(packet.get("red_zone_acknowledged", False))
    operator_token = bool(packet.get("operator_approval_token_present", False))

    # 1) Any denied-authority flag → DENIED.
    auth_labels = _check_authority(packet)
    if auth_labels:
        return {
            **base,
            "reason_labels": auth_labels,
            "safe_summary": "denied: authority flag(s) set; default-deny enforced",
        }

    # 2) Empty capability set → DENIED.
    if not capability_set:
        return {
            **base,
            "reason_labels": [REASON_DENY_EMPTY_CAPABILITY_SET],
            "safe_summary": "denied: empty capability set",
        }

    # 3) Unknown action → FALLBACK (operator review).
    if action not in SAFE_ACTIONS_V1:
        return {
            **base,
            "decision": DECISION_FALLBACK,
            "reason_labels": [REASON_DENY_UNKNOWN_ACTION],
            "requires_operator_review": True,
            "safe_summary": "fallback: unknown action requires operator review",
        }

    # 4) Action must be present in the capability_set.
    if action not in capability_set:
        return {
            **base,
            "reason_labels": [REASON_DENY_EMPTY_CAPABILITY_SET],
            "safe_summary": "denied: action not in capability_set",
        }

    # 5) All checks passed — authorize the safe action.
    return {
        **base,
        "authorized": True,
        "decision": DECISION_AUTHORIZED,
        "reason_labels": [],
        "safe_summary": f"authorized: safe action '{action}' for metadata-only read",
        "requires_operator_review": red_zone_acknowledged or operator_token,
    }


# ----------------------------------------------------------------------------
# Summary / serialization
# ----------------------------------------------------------------------------

def summarize_runtime_authorization_result_v1(result: Dict[str, Any]) -> str:
    """Return a short, safe, human-readable summary line. No raw content."""
    if not isinstance(result, dict):
        return "summary:invalid_result"
    decision = result.get("decision", DECISION_DENIED)
    authorized = result.get("authorized", False)
    labels = result.get("reason_labels", []) or []
    label_str = ",".join(str(x) for x in labels) if labels else "none"
    return f"decision={decision} authorized={authorized} reasons={label_str}"


def to_runtime_wrapper_json_safe_v1(value: Any) -> str:
    """Safely serialize any wrapper-internal value to JSON.

    Rejects non-serializable values; never includes raw content.
    """
    try:
        return json.dumps(value, sort_keys=True, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return json.dumps({"serialization_error": True}, ensure_ascii=False)


__all__ = [
    "WRAPPER_VERSION",
    "SAFE_ACTIONS_V1",
    "REASON_DENY_DEFAULT",
    "REASON_DENY_UNKNOWN_ACTION",
    "REASON_DENY_EMPTY_CAPABILITY_SET",
    "REASON_DENY_PROTECTED_FILE",
    "REASON_DENY_CHATRESPONDER",
    "REASON_DENY_RESPOND_CHAT",
    "REASON_DENY_PROVIDER_MODEL",
    "REASON_DENY_INFRA",
    "REASON_DENY_MEMORY",
    "REASON_DENY_PROJECT",
    "REASON_DENY_PUBLIC_CLAIM",
    "REASON_DENY_RUNTIME_MODIFY",
    "REASON_DENY_MALFORMED_PACKET",
    "REASON_FALLBACK_OPERATOR_REVIEW",
    "DECISION_AUTHORIZED",
    "DECISION_DENIED",
    "DECISION_FALLBACK",
    "build_runtime_authorization_request_v1",
    "validate_runtime_authorization_request_v1",
    "authorize_runtime_action_v1",
    "summarize_runtime_authorization_result_v1",
    "to_runtime_wrapper_json_safe_v1",
]
