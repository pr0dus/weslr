"""
WESLR chat.weslr.de Slice 5 — Entitlement Packet Helper V1

Standalone, metadata-only helper for building, validating, and
querying WESLR entitlement packets.

This module implements the entitlement-packet data model from the
Customer Control Plane + Entitlements design (canonical HEAD
`c58d545a`). It is a pure-metadata helper: no I/O, no persistence,
no network, no subprocess, no ChatResponder, no payment provider,
no dashboard, no billing integration.

The entitlement packet is the **only** thing the runtime wrapper
consults (via the session's capability_set). This module does NOT
wire itself to the runtime wrapper or to the session manager. It
exposes standalone functions for the control plane to call when
recomputing the entitlement packet after account-state or
subscription-state changes.

Critical design invariant (per design §4.2):
  - Default-deny: any packet with empty `allowed_capabilities`
    is denied
  - `allowed_capabilities` must be a strict subset of
    `SAFE_ACTIONS_V1` from the runtime wrapper
  - Subscription/abo state maps to the entitlement packet; the
    runtime wrapper never asks "what is the subscription?" — it
    only asks "is this action in the session's capability set?"

Forbidden claims (per `weslr.de` policy and `weslr` invariants):
  - Not AGI / sentience / consciousness / self-awareness
  - Not autonomous self-improvement
  - Not benchmark / public-science / production-ready
  - Not live-public-runtime
"""

from __future__ import annotations

# Pure stdlib only.
import json
import uuid
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Import ONLY the runtime wrapper's safe-action set, to validate
# that any `allowed_capabilities` value is a strict subset. This
# module does NOT import the runtime wrapper's `authorize_runtime_action_v1`
# or any other runtime entry point. The validation is a structural
# check, not a runtime invocation.
try:
    from weslr.runtime_wrapper import SAFE_ACTIONS_V1 as _RUNTIME_SAFE_ACTIONS_V1
    _RUNTIME_SAFE_ACTIONS_AVAILABLE = True
except ImportError:
    _RUNTIME_SAFE_ACTIONS_V1 = frozenset()
    _RUNTIME_SAFE_ACTIONS_AVAILABLE = False


# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

ENTITLEMENT_PACKET_VERSION = "weslr-entitlement-packet-v1"

# Valid account statuses (must align with the design's user/account
# status enum; mirrored here for self-containment so the helper can
# be tested without importing the not-yet-implemented account-status
# helper). Mapping rules are defined in design §4.2.
_VALID_ACCOUNT_STATUSES = frozenset({
    "invited",
    "pilot_free",
    "pilot_active",
    "pilot_paused",
    "pilot_expired",
    "manual_paid",
    "manual_unpaid",
    "manual_disabled",
    "banned",
    "deletion_requested",
    "deleted_or_revoked",
    # The "operator" role is for operator-side control plane actions
    # (force-logout, rotate, etc.) — not for chat customers.
    "operator",
})

# Valid subscription/abo statuses (mirrored from design §3.1).
_VALID_SUBSCRIPTION_STATUSES = frozenset({
    "no_subscription",
    "free_pilot",
    "trialing",
    "active",
    "past_due",
    "unpaid",
    "canceled",
    "refunded",
    "disputed",
    "grace_period",
    "disabled_for_nonpayment",
})

# Default capability-set mapping per design §4.2.
# For each (account_status, subscription_status) pair, the packet
# receives a strict subset of SAFE_ACTIONS_V1. Empty list = no
# capabilities (the packet is still valid, but the runtime wrapper
# will deny any action on it).
_DEFAULT_CAPABILITY_MAP: Dict[Tuple[str, str], List[str]] = {
    # Pilot users (free)
    ("pilot_free", "free_pilot"): ["health_check_read", "status_read"],
    ("pilot_active", "free_pilot"): ["health_check_read", "status_read"],
    # Pilot users in grace / past-due (reduced)
    ("pilot_expired", "grace_period"): ["status_read"],
    # Manual paid users
    ("manual_paid", "active"): ["health_check_read", "status_read", "operator_review_packet_read"],
    # Manual unpaid during grace
    ("manual_unpaid", "grace_period"): ["status_read"],
    # Operator role: full read-only set + audit log access
    ("operator", "active"): ["health_check_read", "status_read", "operator_review_packet_read"],
}

# Default quota values (overridable per call).
_DEFAULT_MAX_MESSAGES_PER_DAY = 100
_DEFAULT_MAX_SESSIONS = 1
_OPERATOR_MAX_MESSAGES_PER_DAY = 1000
_OPERATOR_MAX_SESSIONS = 5

# Forbidden-keys contract (mirrored from Slice 4A/4B for the
# entitlement-packet record itself; no raw prompts/replies/credentials
# may appear in the packet).
ENTITLEMENT_NEVER_INCLUDES = frozenset({
    "raw_prompt", "raw_reply", "credentials",
    "session_token_plaintext", "hidden_prompt", "system_prompt",
    "chain_of_thought", "provider_response", "shadow_call_output",
    "password", "secret", "api_key",
    # Financial / payment data (metadata-only safe; never raw)
    "payment_card", "card_number", "iban", "bank_account",
})


# Reason labels (machine-readable; safe to log; never expose internal text).
REASON_OK = "ok"
REASON_INVALID_NOT_DICT = "invalid_packet_not_dict"
REASON_INVALID_MISSING_FIELDS = "invalid_packet_missing_required_fields"
REASON_INVALID_BAD_ACCOUNT_STATUS = "invalid_account_status"
REASON_INVALID_BAD_SUBSCRIPTION_STATUS = "invalid_subscription_status"
REASON_INVALID_CAPABILITIES_NOT_LIST = "invalid_capabilities_not_list"
REASON_INVALID_CAPABILITIES_NOT_SUBSET = "invalid_capabilities_not_subset_of_safe_actions"
REASON_INVALID_FORBIDDEN_KEY = "invalid_packet_carries_forbidden_key"
REASON_INVALID_NON_DICT_REQUEST = "invalid_compute_request_not_dict"
REASON_INVALID_EMPTY_ACCOUNT_ID = "invalid_empty_account_id"
REASON_INVALID_EMPTY_ENTITLEMENT_ID = "invalid_empty_entitlement_id"
REASON_INVALID_QUOTA_NOT_INT = "invalid_quota_not_int"
REASON_INVALID_BOOLEAN_NOT_BOOL = "invalid_boolean_not_bool"
REASON_INVALID_BAD_TIMESTAMP = "invalid_bad_timestamp"
REASON_INVALID_BAD_VERSION = "invalid_packet_version_mismatch"


# ----------------------------------------------------------------------------
# Data model
# ----------------------------------------------------------------------------

def build_entitlement_packet_v1(
    *,
    account_id: str,
    account_status: str,
    subscription_status: str,
    entitlement_id: Optional[str] = None,
    entitlement_version: Optional[str] = None,
    entitlement_computed_at: Optional[str] = None,
    entitlement_computed_by: str = "system:recompute",
    allowed_capabilities: Optional[List[str]] = None,
    max_messages_per_day: int = _DEFAULT_MAX_MESSAGES_PER_DAY,
    max_sessions: int = _DEFAULT_MAX_SESSIONS,
    file_upload_allowed: bool = False,
    project_memory_allowed: bool = False,
    marketplace_artifact_access_allowed: bool = False,
    model_tool_access_allowed: bool = False,
    chat_access_enabled: bool = True,
    operator_can_force_logout: bool = False,
    operator_can_pause: bool = False,
    operator_can_rotate_credentials: bool = False,
    operator_can_revoke_capability: bool = False,
    operator_can_extend_grace: bool = False,
    entitlement_expiry: Optional[str] = None,
    entitlement_grace_period_end: Optional[str] = None,
    audit_log_ref: Optional[str] = "",
) -> Dict[str, Any]:
    """
    Build a deterministic entitlement packet (no I/O).

    The packet is a plain dict. Raw content is NOT retained. The
    `raw_content_retained` invariant is always False. The
    `allowed_capabilities` defaults to a strict subset of the
    runtime wrapper's `SAFE_ACTIONS_V1` based on the
    (account_status, subscription_status) mapping.
    """
    if entitlement_id is None:
        entitlement_id = str(uuid.uuid4())
    if entitlement_version is None:
        entitlement_version = ENTITLEMENT_PACKET_VERSION
    if allowed_capabilities is None:
        allowed_capabilities = _DEFAULT_CAPABILITY_MAP.get(
            (account_status, subscription_status), []
        )
    return {
        "entitlement_version": str(entitlement_version),
        "entitlement_id": str(entitlement_id),
        "account_id": str(account_id) if account_id is not None else "",
        "account_status": str(account_status) if account_status is not None else "",
        "subscription_status": str(subscription_status) if subscription_status is not None else "",
        "entitlement_computed_at": str(entitlement_computed_at) if entitlement_computed_at is not None else "",
        "entitlement_computed_by": str(entitlement_computed_by) if entitlement_computed_by is not None else "",
        "allowed_capabilities": list(allowed_capabilities) if allowed_capabilities else [],
        "max_messages_per_day": int(max_messages_per_day),
        "max_sessions": int(max_sessions),
        "file_upload_allowed": bool(file_upload_allowed),
        "project_memory_allowed": bool(project_memory_allowed),
        "marketplace_artifact_access_allowed": bool(marketplace_artifact_access_allowed),
        "model_tool_access_allowed": bool(model_tool_access_allowed),
        "chat_access_enabled": bool(chat_access_enabled),
        "operator_override_flags": {
            "operator_can_force_logout": bool(operator_can_force_logout),
            "operator_can_pause": bool(operator_can_pause),
            "operator_can_rotate_credentials": bool(operator_can_rotate_credentials),
            "operator_can_revoke_capability": bool(operator_can_revoke_capability),
            "operator_can_extend_grace": bool(operator_can_extend_grace),
        },
        "entitlement_expiry": str(entitlement_expiry) if entitlement_expiry is not None else "",
        "entitlement_grace_period_end": str(entitlement_grace_period_end) if entitlement_grace_period_end is not None else "",
        "audit_log_ref": str(audit_log_ref) if audit_log_ref else "",
        "raw_content_retained": False,
    }


def validate_entitlement_packet_v1(packet: Any) -> Tuple[bool, List[str]]:
    """
    Validate the entitlement packet structure. Returns (is_valid,
    error_labels). Never raises. Pure structural check; no I/O.

    Enforces:
      - packet is a dict
      - all required fields are present
      - account_status is in _VALID_ACCOUNT_STATUSES
      - subscription_status is in _VALID_SUBSCRIPTION_STATUSES
      - allowed_capabilities is a list AND a strict subset of
        SAFE_ACTIONS_V1 (if SAFE_ACTIONS_V1 was importable)
      - quota fields are ints
      - boolean fields are bools
      - no forbidden key from ENTITLEMENT_NEVER_INCLUDES appears
        anywhere in the packet (recursive)
    """
    errors: List[str] = []
    if not isinstance(packet, dict):
        errors.append(REASON_INVALID_NOT_DICT)
        return False, errors

    required_fields = (
        "entitlement_version",
        "entitlement_id",
        "account_id",
        "account_status",
        "subscription_status",
        "entitlement_computed_at",
        "entitlement_computed_by",
        "allowed_capabilities",
        "max_messages_per_day",
        "max_sessions",
        "file_upload_allowed",
        "project_memory_allowed",
        "marketplace_artifact_access_allowed",
        "model_tool_access_allowed",
        "chat_access_enabled",
        "operator_override_flags",
        "entitlement_expiry",
        "entitlement_grace_period_end",
        "audit_log_ref",
        "raw_content_retained",
    )
    for key in required_fields:
        if key not in packet:
            errors.append(f"{REASON_INVALID_MISSING_FIELDS}:{key}")

    if "account_status" in packet and packet["account_status"] not in _VALID_ACCOUNT_STATUSES:
        errors.append(f"{REASON_INVALID_BAD_ACCOUNT_STATUS}:{packet['account_status']}")
    if "subscription_status" in packet and packet["subscription_status"] not in _VALID_SUBSCRIPTION_STATUSES:
        errors.append(f"{REASON_INVALID_BAD_SUBSCRIPTION_STATUS}:{packet['subscription_status']}")
    if "entitlement_version" in packet and packet["entitlement_version"] != ENTITLEMENT_PACKET_VERSION:
        errors.append(f"{REASON_INVALID_BAD_VERSION}:{packet['entitlement_version']}")

    if "allowed_capabilities" in packet:
        caps = packet["allowed_capabilities"]
        if not isinstance(caps, list):
            errors.append(REASON_INVALID_CAPABILITIES_NOT_LIST)
        else:
            # Check all entries are strings.
            for c in caps:
                if not isinstance(c, str):
                    errors.append(f"capability_not_string:{type(c).__name__}")
            # Strict subset of SAFE_ACTIONS_V1 (if available). Only
            # check strings (non-strings are already flagged above).
            if _RUNTIME_SAFE_ACTIONS_AVAILABLE:
                invalid_caps = [c for c in caps if isinstance(c, str) and c not in _RUNTIME_SAFE_ACTIONS_V1]
                if invalid_caps:
                    errors.append(
                        f"{REASON_INVALID_CAPABILITIES_NOT_SUBSET}:{','.join(sorted(set(invalid_caps)))}"
                    )

    for quota_key in ("max_messages_per_day", "max_sessions"):
        if quota_key in packet:
            v = packet[quota_key]
            if not isinstance(v, int) or isinstance(v, bool):
                errors.append(f"{REASON_INVALID_QUOTA_NOT_INT}:{quota_key}")
            elif v < 0:
                errors.append(f"{REASON_INVALID_QUOTA_NOT_INT}:{quota_key}:negative")

    for bool_key in (
        "file_upload_allowed",
        "project_memory_allowed",
        "marketplace_artifact_access_allowed",
        "model_tool_access_allowed",
        "chat_access_enabled",
        "raw_content_retained",
    ):
        if bool_key in packet and not isinstance(packet[bool_key], bool):
            errors.append(f"{REASON_INVALID_BOOLEAN_NOT_BOOL}:{bool_key}")

    if "operator_override_flags" in packet and not isinstance(packet["operator_override_flags"], dict):
        errors.append("operator_override_flags_not_dict")

    if "raw_content_retained" in packet and packet["raw_content_retained"] is not False:
        errors.append("raw_content_retained_must_be_false")

    # Recursive scan for forbidden keys.
    forbidden_hits = _find_forbidden_keys(packet)
    for k in forbidden_hits:
        errors.append(f"{REASON_INVALID_FORBIDDEN_KEY}:{k}")

    return (len(errors) == 0), errors


def compute_entitlement_packet_from_status_v1(
    *,
    account_id: str,
    account_status: str,
    subscription_status: str,
    entitlement_computed_at: Optional[str] = None,
    entitlement_computed_by: str = "system:recompute",
    allow_override_capabilities: Optional[List[str]] = None,
    max_messages_per_day: Optional[int] = None,
    max_sessions: Optional[int] = None,
    entitlement_expiry: Optional[str] = None,
    entitlement_grace_period_end: Optional[str] = None,
    audit_log_ref: Optional[str] = "",
    # Operator override flags; defaults are all False.
    operator_can_force_logout: bool = False,
    operator_can_pause: bool = False,
    operator_can_rotate_credentials: bool = False,
    operator_can_revoke_capability: bool = False,
    operator_can_extend_grace: bool = False,
    # Boolean access flags; defaults depend on account/subscription status.
    chat_access_enabled: Optional[bool] = None,
    file_upload_allowed: Optional[bool] = None,
    project_memory_allowed: Optional[bool] = None,
    marketplace_artifact_access_allowed: Optional[bool] = None,
    model_tool_access_allowed: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Compute an entitlement packet from account and subscription status.

    Returns a result dict with metadata only. If the request is
    invalid, returns ok=False with reason_labels explaining why. The
    function does NOT raise.

    This is the primary control-plane entry point. It maps the
    (account_status, subscription_status) pair to a strict-subset
    capability set per design §4.2.
    """
    base = {
        "entitlement_version": ENTITLEMENT_PACKET_VERSION,
        "ok": False,
        "reason_labels": [],
        "packet": None,
        "summary": "",
    }

    # Validate the compute request.
    if not isinstance(account_id, str) or not account_id:
        return {
            **base,
            "reason_labels": [REASON_INVALID_EMPTY_ACCOUNT_ID],
            "summary": "compute denied: missing or empty account_id",
        }
    if account_status not in _VALID_ACCOUNT_STATUSES:
        return {
            **base,
            "reason_labels": [f"{REASON_INVALID_BAD_ACCOUNT_STATUS}:{account_status}"],
            "summary": f"compute denied: invalid account_status '{account_status}'",
        }
    if subscription_status not in _VALID_SUBSCRIPTION_STATUSES:
        return {
            **base,
            "reason_labels": [f"{REASON_INVALID_BAD_SUBSCRIPTION_STATUS}:{subscription_status}"],
            "summary": f"compute denied: invalid subscription_status '{subscription_status}'",
        }
    if allow_override_capabilities is not None:
        if not isinstance(allow_override_capabilities, list):
            return {
                **base,
                "reason_labels": [REASON_INVALID_CAPABILITIES_NOT_LIST],
                "summary": "compute denied: allow_override_capabilities must be a list",
            }
        if _RUNTIME_SAFE_ACTIONS_AVAILABLE:
            invalid_caps = [c for c in allow_override_capabilities if isinstance(c, str) and c not in _RUNTIME_SAFE_ACTIONS_V1]
            if invalid_caps:
                return {
                    **base,
                    "reason_labels": [
                        f"{REASON_INVALID_CAPABILITIES_NOT_SUBSET}:{','.join(sorted(set(invalid_caps)))}"
                    ],
                    "summary": "compute denied: override capabilities not a strict subset of SAFE_ACTIONS_V1",
                }

    # Default capability set from mapping; allow override if explicitly provided.
    if allow_override_capabilities is not None:
        allowed_capabilities = list(allow_override_capabilities)
    else:
        allowed_capabilities = list(_DEFAULT_CAPABILITY_MAP.get(
            (account_status, subscription_status), []
        ))

    # Quota defaults: operator role gets higher defaults; others get
    # the standard pilot defaults.
    if account_status == "operator":
        default_max_messages = _OPERATOR_MAX_MESSAGES_PER_DAY
        default_max_sessions = _OPERATOR_MAX_SESSIONS
    else:
        default_max_messages = _DEFAULT_MAX_MESSAGES_PER_DAY
        default_max_sessions = _DEFAULT_MAX_SESSIONS
    if max_messages_per_day is None:
        max_messages_per_day = default_max_messages
    if max_sessions is None:
        max_sessions = default_max_sessions

    # Boolean access flag defaults based on status.
    def _bool_or(default: bool, override: Optional[bool]) -> bool:
        return default if override is None else bool(override)

    # chat_access_enabled: enabled iff capabilities are non-empty AND
    # account_status is not in the "no chat" set.
    no_chat_statuses = frozenset({
        "banned", "deleted_or_revoked", "manual_disabled",
        "deletion_requested", "pilot_paused", "invited",
    })
    no_chat_subscriptions = frozenset({
        "unpaid", "refunded", "disputed", "disabled_for_nonpayment",
    })
    default_chat_enabled = (
        bool(allowed_capabilities)
        and account_status not in no_chat_statuses
        and subscription_status not in no_chat_subscriptions
    )
    # file_upload / project_memory / marketplace / model_tool: only
    # enabled for active manual paid and operator; default False.
    if account_status == "operator" or (account_status == "manual_paid" and subscription_status == "active"):
        default_paid = True
    else:
        default_paid = False

    packet = build_entitlement_packet_v1(
        account_id=account_id,
        account_status=account_status,
        subscription_status=subscription_status,
        entitlement_computed_at=entitlement_computed_at,
        entitlement_computed_by=entitlement_computed_by,
        allowed_capabilities=allowed_capabilities,
        max_messages_per_day=max_messages_per_day,
        max_sessions=max_sessions,
        file_upload_allowed=_bool_or(default_paid, file_upload_allowed),
        project_memory_allowed=_bool_or(default_paid, project_memory_allowed),
        marketplace_artifact_access_allowed=_bool_or(default_paid, marketplace_artifact_access_allowed),
        model_tool_access_allowed=_bool_or(default_paid, model_tool_access_allowed),
        chat_access_enabled=_bool_or(default_chat_enabled, chat_access_enabled),
        operator_can_force_logout=operator_can_force_logout,
        operator_can_pause=operator_can_pause,
        operator_can_rotate_credentials=operator_can_rotate_credentials,
        operator_can_revoke_capability=operator_can_revoke_capability,
        operator_can_extend_grace=operator_can_extend_grace,
        entitlement_expiry=entitlement_expiry,
        entitlement_grace_period_end=entitlement_grace_period_end,
        audit_log_ref=audit_log_ref,
    )

    # Run final validation.
    ok, errs = validate_entitlement_packet_v1(packet)
    if not ok:
        return {
            **base,
            "reason_labels": [REASON_INVALID_MISSING_FIELDS] + [f"err:{e}" for e in errs],
            "summary": "compute denied: packet validation failed",
        }

    return {
        **base,
        "ok": True,
        "reason_labels": [REASON_OK],
        "packet": packet,
        "summary": f"entitlement packet computed for {account_status}/{subscription_status}",
    }


# ----------------------------------------------------------------------------
# Query
# ----------------------------------------------------------------------------

def is_action_allowed_by_entitlement_v1(
    packet: Any, action_type: str
) -> Dict[str, Any]:
    """
    Decide whether a given action is allowed by the entitlement packet.

    This is a metadata-only decision: it does NOT call the runtime
    wrapper, does NOT consult the session manager, does NOT touch
    any I/O. It only inspects the packet's `allowed_capabilities`
    list and `chat_access_enabled` flag.

    Returns a result dict with metadata only. The runtime wrapper
    remains the source of truth for runtime authorization; this
    function is a control-plane-level pre-check.
    """
    base = {
        "ok": False,
        "reason_labels": [],
        "allowed": False,
        "summary": "",
    }

    if not isinstance(packet, dict):
        return {
            **base,
            "reason_labels": [REASON_INVALID_NOT_DICT],
            "summary": "denied: packet is not a dict",
        }
    if not isinstance(action_type, str) or not action_type:
        return {
            **base,
            "reason_labels": ["invalid_action_type_not_string"],
            "summary": "denied: action_type must be a non-empty string",
        }

    # First, packet must validate as structurally correct.
    ok, errs = validate_entitlement_packet_v1(packet)
    if not ok:
        return {
            **base,
            "reason_labels": [REASON_INVALID_MISSING_FIELDS] + [f"err:{e}" for e in errs],
            "summary": "denied: packet validation failed",
        }

    # chat_access_enabled must be true.
    if not packet.get("chat_access_enabled", False):
        return {
            **base,
            "reason_labels": ["denied_chat_access_disabled"],
            "allowed": False,
            "summary": "denied: chat_access_enabled is False",
        }

    # Capabilities must include the action.
    caps = packet.get("allowed_capabilities", [])
    if not isinstance(caps, list):
        return {
            **base,
            "reason_labels": [REASON_INVALID_CAPABILITIES_NOT_LIST],
            "allowed": False,
            "summary": "denied: allowed_capabilities is not a list",
        }
    if action_type not in caps:
        return {
            **base,
            "reason_labels": [f"denied_capability_not_in_packet:{action_type}"],
            "allowed": False,
            "summary": f"denied: '{action_type}' not in allowed_capabilities",
        }

    # Strict-subset check: if SAFE_ACTIONS_V1 is importable, the
    # action_type must also be in SAFE_ACTIONS_V1 (defense in depth
    # — a packet that somehow contains a capability outside the
    # runtime safe set is denied even if it lists the action).
    if _RUNTIME_SAFE_ACTIONS_AVAILABLE and action_type not in _RUNTIME_SAFE_ACTIONS_V1:
        return {
            **base,
            "reason_labels": [f"denied_action_not_in_runtime_safe_actions:{action_type}"],
            "allowed": False,
            "summary": f"denied: '{action_type}' is not a runtime safe action",
        }

    return {
        **base,
        "ok": True,
        "reason_labels": [REASON_OK],
        "allowed": True,
        "summary": f"allowed: '{action_type}' is in allowed_capabilities",
    }


# ----------------------------------------------------------------------------
# Summary / serialization
# ----------------------------------------------------------------------------

def summarize_entitlement_packet_v1(packet: Any) -> str:
    """Return a short, safe, human-readable summary. No raw content."""
    if not isinstance(packet, dict):
        return "summary:invalid_entitlement_packet"
    account_id = packet.get("account_id", "")
    account_status = packet.get("account_status", "")
    subscription_status = packet.get("subscription_status", "")
    caps = packet.get("allowed_capabilities", [])
    chat_enabled = packet.get("chat_access_enabled", False)
    return (
        f"entitlement account={account_id} account_status={account_status} "
        f"subscription={subscription_status} caps={len(caps)} chat_enabled={chat_enabled}"
    )


def to_entitlement_packet_json_safe_v1(value: Any) -> str:
    """
    Safely serialize any entitlement-related value to JSON.

    Strips keys from ENTITLEMENT_NEVER_INCLUDES (recursive). Cycle
    detection. Falls back to a safe marker for unserializable input.
    Never includes raw prompts, credentials, hidden prompts,
    chain-of-thought, or any other forbidden key.
    """
    safe_value = _strip_private_keys(value)
    try:
        return json.dumps(safe_value, sort_keys=True, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return json.dumps({"serialization_error": True}, ensure_ascii=False)


# ----------------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------------

def _find_forbidden_keys(value: Any, _seen: Optional[set] = None) -> List[str]:
    if _seen is None:
        _seen = set()
    hits: List[str] = []
    if isinstance(value, dict):
        if id(value) in _seen:
            return hits
        _seen = _seen | {id(value)}
        for k, v in value.items():
            if k in ENTITLEMENT_NEVER_INCLUDES:
                hits.append(k)
            hits.extend(_find_forbidden_keys(v, _seen))
        return hits
    if isinstance(value, list):
        if id(value) in _seen:
            return hits
        _seen = _seen | {id(value)}
        for item in value:
            hits.extend(_find_forbidden_keys(item, _seen))
        return hits
    return hits


def _strip_private_keys(value: Any, _seen: Optional[set] = None) -> Any:
    """Recursively remove private keys; cycle detection."""
    if _seen is None:
        _seen = set()
    if isinstance(value, dict):
        if id(value) in _seen:
            return "<cyclic>"
        _seen = _seen | {id(value)}
        cleaned: Dict[str, Any] = {}
        for k, v in value.items():
            if k in ENTITLEMENT_NEVER_INCLUDES:
                continue
            cleaned[k] = _strip_private_keys(v, _seen)
        return cleaned
    if isinstance(value, list):
        if id(value) in _seen:
            return "<cyclic>"
        _seen = _seen | {id(value)}
        return [_strip_private_keys(item, _seen) for item in value]
    return value


__all__ = [
    "ENTITLEMENT_PACKET_VERSION",
    "ENTITLEMENT_NEVER_INCLUDES",
    "REASON_OK",
    "REASON_INVALID_NOT_DICT",
    "REASON_INVALID_MISSING_FIELDS",
    "REASON_INVALID_BAD_ACCOUNT_STATUS",
    "REASON_INVALID_BAD_SUBSCRIPTION_STATUS",
    "REASON_INVALID_CAPABILITIES_NOT_LIST",
    "REASON_INVALID_CAPABILITIES_NOT_SUBSET",
    "REASON_INVALID_FORBIDDEN_KEY",
    "REASON_INVALID_EMPTY_ACCOUNT_ID",
    "REASON_INVALID_EMPTY_ENTITLEMENT_ID",
    "REASON_INVALID_QUOTA_NOT_INT",
    "REASON_INVALID_BOOLEAN_NOT_BOOL",
    "REASON_INVALID_BAD_TIMESTAMP",
    "REASON_INVALID_BAD_VERSION",
    "build_entitlement_packet_v1",
    "validate_entitlement_packet_v1",
    "compute_entitlement_packet_from_status_v1",
    "is_action_allowed_by_entitlement_v1",
    "summarize_entitlement_packet_v1",
    "to_entitlement_packet_json_safe_v1",
]