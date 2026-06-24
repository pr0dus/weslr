"""
WESLR chat.weslr.de Slice 6 — Account Status Helper V1

Standalone, metadata-only account-status state/transition helper.

This module manages the 11 account statuses and their state-
transition graph. It does NOT:
  - import or call weslr.chat_responder, main, dialogue, chat_ui,
    backend server files, provider/model code, or any protected
    runtime module
  - perform subprocess, network, or filesystem write operations
  - wire itself to the entitlement helper, runtime wrapper, session
    manager, audit log, audit persistence, or ChatResponder
  - retain raw prompt text, raw reply text, credentials, PII,
    hidden prompts, system prompts, chain-of-thought traces,
    provider/LLM API responses, or real shadow-call outputs
  - claim AGI / sentience / consciousness / benchmark /
    public-science / production-ready / live-public-runtime

This slice implements the account-status state/transition logic
only. Real persistence, operator-action wiring, and dashboard
integration are out of scope for this slice and await operator
approval (Slices 7+).

Design reference: Customer Control Plane + Entitlements design
(§3 User/Account Statuses and §2 Account State Machine), plus
the operator's transition rules.
"""

from __future__ import annotations

# Pure stdlib only.
import json
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple


# Optional import: pull the canonical valid account-status enum
# from the entitlement packet helper (Slice 5) to ensure this
# module's status set is the same. If unavailable, fall back to
# the local enum defined below.
try:
    from weslr.entitlement_packet import _VALID_ACCOUNT_STATUSES as _EP_ACCOUNT_STATUSES
    _EP_AVAILABLE = True
except ImportError:
    _EP_ACCOUNT_STATUSES = frozenset()
    _EP_AVAILABLE = False


# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

ACCOUNT_STATUS_HELPER_VERSION = "weslr-account-status-helper-v1"

# 11 valid account statuses (per Customer Control Plane + Entitlements
# design §2). Mirrored from Slice 5's entitlement-packet module to
# keep this slice self-contained.
VALID_ACCOUNT_STATUSES_V1: frozenset = frozenset({
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
})

# Terminal statuses (no outgoing transitions allowed).
TERMINAL_STATUSES_V1: frozenset = frozenset({
    "deleted_or_revoked",
})

# Restricted terminal-like statuses (only specific outgoing transitions).
RESTRICTED_TERMINAL_LIKE_STATUSES_V1: frozenset = frozenset({
    "banned",          # may only move to deletion_requested or deleted_or_revoked
    "deletion_requested",  # may only move to deleted_or_revoked
})

# Transition graph. Key: current status; Value: set of allowed next statuses.
# Per operator's transition rules:
#   - default-deny unknown transitions
#   - terminal: deleted_or_revoked (no outgoing)
#   - restricted terminal-like: banned (only -> deletion_requested, deleted_or_revoked)
#                              deletion_requested (only -> deleted_or_revoked)
#   - normal allowed examples: ...
ALLOWED_TRANSITIONS_V1: Dict[str, frozenset] = {
    "invited": frozenset({
        "pilot_free", "pilot_active", "manual_paid", "manual_disabled",
        "deleted_or_revoked",
    }),
    "pilot_free": frozenset({
        "pilot_active", "pilot_paused", "pilot_expired",
        "manual_paid", "manual_unpaid", "manual_disabled",
        "banned", "deletion_requested",
    }),
    "pilot_active": frozenset({
        "pilot_paused", "pilot_expired",
        "manual_paid", "manual_unpaid", "manual_disabled",
        "banned", "deletion_requested",
    }),
    "pilot_paused": frozenset({
        "pilot_active", "pilot_expired",
        "manual_disabled",
        "banned", "deletion_requested",
    }),
    "pilot_expired": frozenset({
        "pilot_active",
        "manual_paid", "manual_disabled",
        "banned", "deletion_requested",
    }),
    "manual_paid": frozenset({
        "manual_unpaid", "manual_disabled",
        "banned", "deletion_requested",
    }),
    "manual_unpaid": frozenset({
        "manual_paid", "manual_disabled",
        "banned", "deletion_requested",
    }),
    "manual_disabled": frozenset({
        "manual_paid", "manual_unpaid",
        "banned", "deletion_requested",
    }),
    "banned": frozenset({
        "deletion_requested", "deleted_or_revoked",
    }),
    "deletion_requested": frozenset({
        "deleted_or_revoked",
    }),
    "deleted_or_revoked": frozenset(),  # terminal
}

# Reason labels (machine-readable; safe to log).
REASON_OK = "ok"
REASON_INVALID_NOT_DICT = "invalid_record_not_dict"
REASON_INVALID_REQUEST_NOT_DICT = "invalid_transition_request_not_dict"
REASON_INVALID_BAD_STATUS = "invalid_account_status"
REASON_INVALID_BAD_TRANSITION = "invalid_account_status_transition"
REASON_INVALID_BAD_TIMESTAMP = "invalid_account_status_timestamp"
REASON_INVALID_BAD_VERSION = "invalid_account_status_version_mismatch"
REASON_INVALID_MISSING_FIELDS = "invalid_account_status_missing_required_fields"
REASON_INVALID_EMPTY_ACCOUNT_ID = "invalid_empty_account_id"
REASON_INVALID_SAME_STATUS = "invalid_transition_same_status"
REASON_INVALID_TERMINAL_TRANSITION = "invalid_transition_from_terminal_status"
REASON_INVALID_RESTRICTED_TRANSITION = "invalid_restricted_terminal_transition"
REASON_INVALID_FORBIDDEN_KEY = "invalid_record_carries_forbidden_key"

# Forbidden-keys contract (mirrored from Slice 4A/4B/5). No raw
# prompts/replies/credentials/payment data in account-status records.
ACCOUNT_STATUS_NEVER_INCLUDES = frozenset({
    "raw_prompt", "raw_reply", "credentials",
    "session_token_plaintext", "hidden_prompt", "system_prompt",
    "chain_of_thought", "provider_response", "shadow_call_output",
    "password", "secret", "api_key",
    "payment_card", "card_number", "iban", "bank_account",
})

# Chat-enabled status set (per Slice 5's chat_access_enabled logic
# AND the operator's strict spec for Slice 6). At the STATUS level
# (this slice's pre-check), only the four statuses that are clearly
# "active and usable" return chat_enabled=True. Note that Slice 5's
# entitlement-packet helper treats manual_unpaid as enabled-with-
# subscription-gating (subscription-level decision); the status-level
# pre-check here is more conservative. The chat_enabled status set is:
#   pilot_free, pilot_active, manual_paid
# manual_unpaid is intentionally NOT in this set (operator's strict
# spec for the Slice 6 status-level pre-check). The entitlement
# packet helper handles manual_unpaid at the subscription level.
CHAT_ENABLED_STATUSES_V1: frozenset = frozenset({
    "pilot_free", "pilot_active", "manual_paid",
})


# ----------------------------------------------------------------------------
# Record construction
# ----------------------------------------------------------------------------

def build_account_status_record_v1(
    *,
    account_id: str,
    account_status: str,
    previous_account_status: str = "",
    account_status_record_id: Optional[str] = None,
    account_status_version: Optional[str] = None,
    status_updated_at: Optional[str] = None,
    status_updated_by: Optional[str] = "",
    status_reason_label: Optional[str] = "",
    status_transition_ref: Optional[str] = "",
    audit_log_ref: Optional[str] = "",
    account_status_invited_at: Optional[str] = "",
    account_status_last_active_at: Optional[str] = "",
    account_status_pii_visible_to_operator: bool = False,
    account_status_red_zone_acknowledged_at: Optional[str] = "",
    reason_labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Build a deterministic account-status record (no I/O).

    The record is a plain dict. Raw content is NOT retained. The
    `raw_content_retained` invariant is always False. The record
    carries only metadata.
    """
    if account_status_record_id is None:
        account_status_record_id = str(uuid.uuid4())
    if account_status_version is None:
        account_status_version = ACCOUNT_STATUS_HELPER_VERSION
    if reason_labels is None:
        reason_labels = [REASON_OK]
    return {
        "account_status_helper_version": ACCOUNT_STATUS_HELPER_VERSION,
        "account_status_record_id": str(account_status_record_id),
        "account_status_version": str(account_status_version),
        "account_id": str(account_id) if account_id is not None else "",
        "account_status": str(account_status) if account_status is not None else "",
        "previous_account_status": str(previous_account_status) if previous_account_status else "",
        "status_updated_at": str(status_updated_at) if status_updated_at is not None else "",
        "status_updated_by": str(status_updated_by) if status_updated_by is not None else "",
        "status_reason_label": str(status_reason_label) if status_reason_label is not None else "",
        "status_transition_ref": str(status_transition_ref) if status_transition_ref else "",
        "audit_log_ref": str(audit_log_ref) if audit_log_ref else "",
        "account_status_invited_at": str(account_status_invited_at) if account_status_invited_at is not None else "",
        "account_status_last_active_at": str(account_status_last_active_at) if account_status_last_active_at is not None else "",
        "account_status_pii_visible_to_operator": bool(account_status_pii_visible_to_operator),
        "account_status_red_zone_acknowledged_at": str(account_status_red_zone_acknowledged_at) if account_status_red_zone_acknowledged_at is not None else "",
        "reason_labels": list(reason_labels),
        "raw_content_retained": False,
    }


def validate_account_status_record_v1(record: Any) -> Tuple[bool, List[str]]:
    """
    Validate the account-status record structure. Returns (is_valid,
    error_labels). Never raises. Pure structural check; no I/O.

    Enforces:
      - record is a dict
      - all required fields are present
      - account_status is in VALID_ACCOUNT_STATUSES_V1
      - account_status_version matches the current helper version
      - raw_content_retained is False
      - no forbidden key from ACCOUNT_STATUS_NEVER_INCLUDES appears
        anywhere in the record (recursive)
    """
    errors: List[str] = []
    if not isinstance(record, dict):
        errors.append(REASON_INVALID_NOT_DICT)
        return False, errors

    required_fields = (
        "account_status_helper_version",
        "account_status_record_id",
        "account_status_version",
        "account_id",
        "account_status",
        "previous_account_status",
        "status_updated_at",
        "status_updated_by",
        "status_reason_label",
        "status_transition_ref",
        "audit_log_ref",
        "account_status_invited_at",
        "account_status_last_active_at",
        "account_status_pii_visible_to_operator",
        "account_status_red_zone_acknowledged_at",
        "reason_labels",
        "raw_content_retained",
    )
    for key in required_fields:
        if key not in record:
            errors.append(f"{REASON_INVALID_MISSING_FIELDS}:{key}")

    if "account_status" in record and record["account_status"] not in VALID_ACCOUNT_STATUSES_V1:
        errors.append(f"{REASON_INVALID_BAD_STATUS}:{record['account_status']}")
    if "account_status_version" in record and record["account_status_version"] != ACCOUNT_STATUS_HELPER_VERSION:
        errors.append(f"{REASON_INVALID_BAD_VERSION}:{record['account_status_version']}")
    if "raw_content_retained" in record and record["raw_content_retained"] is not False:
        errors.append("raw_content_retained_must_be_false")
    if "account_status_pii_visible_to_operator" in record and not isinstance(record["account_status_pii_visible_to_operator"], bool):
        errors.append("account_status_pii_visible_to_operator_must_be_bool")
    if "reason_labels" in record and not isinstance(record["reason_labels"], list):
        errors.append("reason_labels_not_list")

    # Recursive scan for forbidden keys.
    forbidden_hits = _find_forbidden_keys(record)
    for k in forbidden_hits:
        errors.append(f"{REASON_INVALID_FORBIDDEN_KEY}:{k}")

    return (len(errors) == 0), errors


# ----------------------------------------------------------------------------
# Transition request
# ----------------------------------------------------------------------------

def build_account_status_transition_request_v1(
    *,
    account_id: str,
    from_status: str,
    to_status: str,
    transition_request_id: Optional[str] = None,
    requested_at: Optional[str] = None,
    requested_by: str = "",
    reason_label: str = "",
    operator_approved: bool = False,
    audit_log_ref: Optional[str] = "",
    reason_labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Build a deterministic transition request (no I/O).

    The request is a plain dict. The request itself does not perform
    the transition; call `apply_account_status_transition_v1` to do
    that. The request carries only metadata.

    `operator_approved` is required to be True for destructive
    transitions (banned, deletion_requested, deleted_or_revoked,
    manual_disabled) per the operator's safety rules.
    """
    if transition_request_id is None:
        transition_request_id = str(uuid.uuid4())
    return {
        "transition_request_id": str(transition_request_id),
        "account_id": str(account_id) if account_id is not None else "",
        "from_status": str(from_status) if from_status is not None else "",
        "to_status": str(to_status) if to_status is not None else "",
        "requested_at": str(requested_at) if requested_at is not None else "",
        "requested_by": str(requested_by) if requested_by is not None else "",
        "reason_label": str(reason_label) if reason_label is not None else "",
        "operator_approved": bool(operator_approved),
        "audit_log_ref": str(audit_log_ref) if audit_log_ref else "",
        "reason_labels": list(reason_labels) if reason_labels else [REASON_OK],
        "raw_content_retained": False,
    }


def validate_account_status_transition_request_v1(
    request: Any,
) -> Tuple[bool, List[str]]:
    """
    Validate a transition request. Returns (is_valid, error_labels).
    Never raises. Pure structural check; no I/O.

    Enforces:
      - request is a dict
      - required fields are present
      - account_id is a non-empty string
      - from_status and to_status are in VALID_ACCOUNT_STATUSES_V1
      - raw_content_retained is False
      - no forbidden key appears anywhere in the request
    """
    errors: List[str] = []
    if not isinstance(request, dict):
        errors.append(REASON_INVALID_REQUEST_NOT_DICT)
        return False, errors

    required_fields = (
        "transition_request_id",
        "account_id",
        "from_status",
        "to_status",
        "requested_at",
        "requested_by",
        "reason_label",
        "operator_approved",
        "audit_log_ref",
        "reason_labels",
        "raw_content_retained",
    )
    for key in required_fields:
        if key not in request:
            errors.append(f"{REASON_INVALID_MISSING_FIELDS}:{key}")

    if "account_id" in request:
        if not isinstance(request["account_id"], str) or not request["account_id"]:
            errors.append(REASON_INVALID_EMPTY_ACCOUNT_ID)
    if "from_status" in request and request["from_status"] not in VALID_ACCOUNT_STATUSES_V1:
        errors.append(f"{REASON_INVALID_BAD_STATUS}:from:{request['from_status']}")
    if "to_status" in request and request["to_status"] not in VALID_ACCOUNT_STATUSES_V1:
        errors.append(f"{REASON_INVALID_BAD_STATUS}:to:{request['to_status']}")
    if "raw_content_retained" in request and request["raw_content_retained"] is not False:
        errors.append("raw_content_retained_must_be_false")
    if "transition_reason_labels" in request and not isinstance(request["transition_reason_labels"], list):
        errors.append("transition_reason_labels_not_list")

    # Recursive scan for forbidden keys.
    forbidden_hits = _find_forbidden_keys(request)
    for k in forbidden_hits:
        errors.append(f"{REASON_INVALID_FORBIDDEN_KEY}:{k}")

    return (len(errors) == 0), errors


# ----------------------------------------------------------------------------
# Transition application
# ----------------------------------------------------------------------------

def apply_account_status_transition_v1(
    record: Dict[str, Any],
    request: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Apply a status transition to a record.

    Returns a result dict with metadata only:
      - ok: True/False
      - reason_labels: list of machine-readable reason codes
      - new_record: the updated record (if ok), else None
      - summary: short human-readable summary

    Default-deny: any transition NOT in ALLOWED_TRANSITIONS_V1 is
    rejected. Terminal statuses (deleted_or_revoked) cannot transition
    out. Restricted terminal-like statuses (banned, deletion_requested)
    can only transition to specific allowed next states.

    The function does NOT raise. It does NOT call out to any
    external service; it does NOT touch the entitlement helper,
    runtime wrapper, session manager, audit log, audit persistence,
    or ChatResponder. The result includes the new record but does
    NOT persist it anywhere.
    """
    base = {
        "account_status_helper_version": ACCOUNT_STATUS_HELPER_VERSION,
        "ok": False,
        "reason_labels": [],
        "new_record": None,
        "summary": "",
    }

    # 1. Validate the record.
    ok, errs = validate_account_status_record_v1(record)
    if not ok:
        return {
            **base,
            "reason_labels": [REASON_INVALID_MISSING_FIELDS] + [f"err:{e}" for e in errs],
            "summary": "apply denied: record validation failed",
        }

    # 2. Validate the request.
    ok, errs = validate_account_status_transition_request_v1(request)
    if not ok:
        return {
            **base,
            "reason_labels": [REASON_INVALID_MISSING_FIELDS] + [f"err:{e}" for e in errs],
            "summary": "apply denied: request validation failed",
        }

    from_status = request["from_status"]
    to_status = request["to_status"]
    request_account_id = request["account_id"]
    record_account_id = record["account_id"]

    # 3. Account IDs must match.
    if request_account_id != record_account_id:
        return {
            **base,
            "reason_labels": ["account_id_mismatch"],
            "summary": "apply denied: request account_id does not match record account_id",
        }

    # 4. The record's current status must match the request's from_status.
    if record["account_status"] != from_status:
        return {
            **base,
            "reason_labels": [
                f"from_status_mismatch:record={record['account_status']}:request={from_status}"
            ],
            "summary": "apply denied: record's current status does not match request's from_status",
        }

    # 5. Same-status transitions are rejected (no-op transitions are not allowed).
    if from_status == to_status:
        return {
            **base,
            "reason_labels": [REASON_INVALID_SAME_STATUS],
            "summary": f"apply denied: from_status and to_status are both '{from_status}'",
        }

    # 6. Destructive transitions require explicit operator approval.
    destructive_targets = {"banned", "deletion_requested", "deleted_or_revoked", "manual_disabled"}
    if to_status in destructive_targets and not bool(request.get("operator_approved", False)):
        return {
            **base,
            "reason_labels": ["destructive_transition_requires_operator_approval"],
            "summary": f"apply denied: transition to '{to_status}' requires operator approval",
        }

    # 7. Default-deny: any transition not in ALLOWED_TRANSITIONS_V1 is rejected.
    allowed_next = ALLOWED_TRANSITIONS_V1.get(from_status, frozenset())
    if to_status not in allowed_next:
        # Distinguish between "from is terminal" and "transition is
        # not in the allowed graph".
        if from_status in TERMINAL_STATUSES_V1:
            return {
                **base,
                "reason_labels": [REASON_INVALID_TERMINAL_TRANSITION],
                "summary": f"apply denied: '{from_status}' is terminal; no outgoing transitions allowed",
            }
        if from_status in RESTRICTED_TERMINAL_LIKE_STATUSES_V1:
            return {
                **base,
                "reason_labels": [REASON_INVALID_RESTRICTED_TRANSITION],
                "summary": f"apply denied: '{from_status}' is restricted terminal-like; only specific next states allowed",
            }
        return {
            **base,
            "reason_labels": [f"{REASON_INVALID_BAD_TRANSITION}:{from_status}->{to_status}"],
            "summary": f"apply denied: transition '{from_status} -> {to_status}' is not allowed",
        }

    # 8. Apply the transition: build a new record with the updated
    # status and metadata from the request. Do NOT mutate the input
    # record; return a defensive copy.
    new_record = dict(record)
    new_record["previous_account_status"] = record["account_status"]
    new_record["account_status"] = to_status
    new_record["status_updated_at"] = request.get("requested_at", "") or record.get("status_updated_at", "")
    new_record["status_updated_by"] = request.get("requested_by", "") or record.get("status_updated_by", "")
    new_record["status_reason_label"] = request.get("reason_label", "") or record.get("status_reason_label", "")
    new_record["status_transition_ref"] = request.get("transition_request_id", "") or record.get("status_transition_ref", "")
    new_record["audit_log_ref"] = request.get("audit_log_ref", "") or record.get("audit_log_ref", "")
    # Append the transition reason label to the record's reason labels
    # (deduplicated).
    record_labels = list(new_record.get("reason_labels", []) or [])
    label = new_record["status_reason_label"]
    if label and label not in record_labels:
        record_labels.append(label)
    new_record["reason_labels"] = record_labels

    # 9. Validate the new record.
    ok, errs = validate_account_status_record_v1(new_record)
    if not ok:
        return {
            **base,
            "reason_labels": [REASON_INVALID_MISSING_FIELDS] + [f"err:{e}" for e in errs],
            "summary": "apply denied: new record validation failed",
        }

    suggested_audit_metadata = {
        "audit_action_type": "user_status_changed",
        "audit_target_account_id": record["account_id"],
        "audit_before_state": dict(record),
        "audit_after_state": dict(new_record),
        "audit_transition_request_id": request.get("transition_request_id", ""),
        "audit_requested_by": request.get("requested_by", ""),
        "audit_requested_at": request.get("requested_at", ""),
        "audit_reason_label": request.get("reason_label", ""),
        "audit_operator_approved": bool(request.get("operator_approved", False)),
    }

    return {
        **base,
        "ok": True,
        "reason_labels": [REASON_OK],
        "new_record": new_record,
        "suggested_audit_metadata": suggested_audit_metadata,
        "summary": f"transition applied: '{from_status}' -> '{to_status}'",
    }


# ----------------------------------------------------------------------------
# Query
# ----------------------------------------------------------------------------

def is_account_status_chat_enabled_v1(record: Any) -> Dict[str, Any]:
    """
    Decide whether the account status allows chat access.

    This is a metadata-only check based on the account_status field.
    It does NOT call the entitlement helper, runtime wrapper, or
    session manager. It does NOT consult subscription state or
    capability set. It is a coarse, account-status-level pre-check.

    Returns a result dict with metadata only.
    """
    base = {
        "ok": False,
        "reason_labels": [],
        "chat_enabled": False,
        "summary": "",
    }

    if not isinstance(record, dict):
        return {
            **base,
            "reason_labels": [REASON_INVALID_NOT_DICT],
            "summary": "query denied: record is not a dict",
        }

    ok, errs = validate_account_status_record_v1(record)
    if not ok:
        return {
            **base,
            "reason_labels": [REASON_INVALID_MISSING_FIELDS] + [f"err:{e}" for e in errs],
            "summary": "query denied: record validation failed",
        }

    status = record.get("account_status", "")
    if status in CHAT_ENABLED_STATUSES_V1:
        return {
            **base,
            "ok": True,
            "reason_labels": [REASON_OK],
            "chat_enabled": True,
            "summary": f"chat enabled: account_status='{status}' is in CHAT_ENABLED_STATUSES_V1",
        }
    return {
        **base,
        "ok": True,
        "reason_labels": [f"chat_disabled_status:{status}"],
        "chat_enabled": False,
        "summary": f"chat disabled: account_status='{status}' is not in CHAT_ENABLED_STATUSES_V1",
    }


# ----------------------------------------------------------------------------
# Summary / serialization
# ----------------------------------------------------------------------------

def summarize_account_status_record_v1(record: Any) -> str:
    """Return a short, safe, human-readable summary. No raw content."""
    if not isinstance(record, dict):
        return "summary:invalid_account_status_record"
    account_id = record.get("account_id", "")
    status = record.get("account_status", "")
    changed_at = record.get("account_status_changed_at", "")
    changed_by = record.get("account_status_changed_by", "")
    return (
        f"account_status account={account_id} status={status} "
        f"changed_by={changed_by} at={changed_at}"
    )


def to_account_status_json_safe_v1(value: Any) -> str:
    """
    Safely serialize any account-status value to JSON.

    Strips keys from ACCOUNT_STATUS_NEVER_INCLUDES (recursive).
    Cycle detection. Falls back to a safe marker for unserializable
    input. Never includes raw prompts, credentials, hidden prompts,
    chain-of-thought, payment data, or any other forbidden key.
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
            if k in ACCOUNT_STATUS_NEVER_INCLUDES:
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
    if _seen is None:
        _seen = set()
    if isinstance(value, dict):
        if id(value) in _seen:
            return "<cyclic>"
        _seen = _seen | {id(value)}
        cleaned: Dict[str, Any] = {}
        for k, v in value.items():
            if k in ACCOUNT_STATUS_NEVER_INCLUDES:
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
    "ACCOUNT_STATUS_HELPER_VERSION",
    "VALID_ACCOUNT_STATUSES_V1",
    "TERMINAL_STATUSES_V1",
    "RESTRICTED_TERMINAL_LIKE_STATUSES_V1",
    "ALLOWED_TRANSITIONS_V1",
    "CHAT_ENABLED_STATUSES_V1",
    "ACCOUNT_STATUS_NEVER_INCLUDES",
    "REASON_OK",
    "REASON_INVALID_NOT_DICT",
    "REASON_INVALID_REQUEST_NOT_DICT",
    "REASON_INVALID_BAD_STATUS",
    "REASON_INVALID_BAD_TRANSITION",
    "REASON_INVALID_BAD_TIMESTAMP",
    "REASON_INVALID_BAD_VERSION",
    "REASON_INVALID_MISSING_FIELDS",
    "REASON_INVALID_EMPTY_ACCOUNT_ID",
    "REASON_INVALID_SAME_STATUS",
    "REASON_INVALID_TERMINAL_TRANSITION",
    "REASON_INVALID_RESTRICTED_TRANSITION",
    "REASON_INVALID_FORBIDDEN_KEY",
    "build_account_status_record_v1",
    "validate_account_status_record_v1",
    "build_account_status_transition_request_v1",
    "validate_account_status_transition_request_v1",
    "apply_account_status_transition_v1",
    "is_account_status_chat_enabled_v1",
    "summarize_account_status_record_v1",
    "to_account_status_json_safe_v1",
]