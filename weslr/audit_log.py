"""
WESLR chat.weslr.de Slice 4A — Audit Event Schema Helper V1

Deterministic, pure-Python, no-I/O audit event schema and in-memory
store helper.

This module defines the audit event shape, validation, and
in-memory store operations. It does NOT:
  - import or call weslr.chat_responder, main, dialogue, chat_ui,
    backend server files, provider/model code, or any protected
    runtime module
  - perform subprocess, network, or filesystem read/write operations
  - write to "/home/pr0/weslr_state/logs/" (the future real-storage
    path is recorded as a metadata constant only)
  - retain raw prompt text, raw reply text, credentials, PII,
    hidden prompts, system prompts, chain-of-thought traces,
    provider/LLM API responses, real shadow-call outputs, or any
    key in AUDIT_LOG_NEVER_INCLUDES_V1
  - claim AGI / sentience / consciousness / benchmark / public-science
    / production-ready / live-public-runtime
  - be wired to the runtime wrapper, session manager, or any
    ChatResponder entry point

This slice implements the audit event SCHEMA and HELPER only. Real
file persistence is a separate slice (4B) and is out of scope here.
"""

from __future__ import annotations

# Pure stdlib only.
import json
import uuid
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

AUDIT_LOG_VERSION = "weslr-audit-log-v1"

# Allowed event categories (machine-readable; safe to log).
ALLOWED_AUDIT_EVENT_CATEGORIES_V1 = frozenset({
    # User / account events
    "user_created",
    "user_status_changed",
    # Entitlement events
    "entitlement_changed",
    # Session events
    "session_created",
    "session_touched",
    "session_expired",
    "session_force_logged_out",
    # Billing / abo events
    "billing_status_changed",
    "grace_period_started",
    # Access events
    "access_disabled",
    # Operator action events
    "operator_action",
    "support_escalation",
    # Deletion events
    "deletion_requested",
    "deletion_completed",
    # Runtime authorization events
    "runtime_authorization_denied",
    "runtime_authorization_allowed",
})

# Hard contract: the audit log MUST NEVER include these keys.
# Slice 4 implementation (4B) must reject any record that would expose
# a key in this set. Slice 4A enforces this at validation time.
AUDIT_LOG_NEVER_INCLUDES_V1 = frozenset({
    "raw_prompt",
    "raw_reply",
    "credentials",
    "session_token_plaintext",
    "hidden_prompt",
    "system_prompt",
    "chain_of_thought",
    "provider_response",
    "shadow_call_output",
    "password",
    "secret",
    "api_key",
})

# Reason labels (machine-readable; safe to log; never expose internal text).
REASON_OK = "ok"
REASON_INVALID_MISSING_FIELDS = "invalid_missing_required_fields"
REASON_INVALID_BAD_CATEGORY = "invalid_audit_event_category"
REASON_INVALID_NEVER_INCLUDES_KEY = "invalid_never_includes_key_present"
REASON_INVALID_BAD_TIMESTAMP = "invalid_audit_event_timestamp"
REASON_INVALID_NOT_DICT = "invalid_audit_event_not_dict"
REASON_INVALID_STORE_NOT_LIST = "invalid_audit_store_not_list"
REASON_INVALID_NOT_FOUND = "audit_event_not_found"

# Future real-storage path (metadata only; never used for I/O in this slice).
FUTURE_LOG_STORAGE_PATH_METADATA = "/home/pr0/weslr_state/logs/"

# Audit event required fields (must be present and non-empty where applicable).
REQUIRED_AUDIT_EVENT_FIELDS_V1 = (
    "audit_log_entry_id",
    "audit_log_version",
    "audit_log_recorded_at",
    "audit_log_action_type",
    "audit_log_operator_ref",
    "audit_log_target_account_id",
    "audit_log_target_session_id",
    "audit_log_target_resource",
    "audit_log_before_state",
    "audit_log_after_state",
    "audit_log_reason_label",
    "audit_log_summary",
    "audit_log_raw_content_retained",
    "audit_log_never_includes",
    "reason_labels",
)


# ----------------------------------------------------------------------------
# Data model
# ----------------------------------------------------------------------------

def build_audit_event_v1(
    *,
    audit_log_action_type: str,
    audit_log_operator_ref: str,
    audit_log_recorded_at: Optional[str] = None,
    audit_log_entry_id: Optional[str] = None,
    audit_log_target_account_id: str = "",
    audit_log_target_session_id: str = "",
    audit_log_target_resource: str = "",
    audit_log_before_state: Optional[Dict[str, Any]] = None,
    audit_log_after_state: Optional[Dict[str, Any]] = None,
    audit_log_reason_label: str = "",
    audit_log_summary: str = "",
    reason_labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Build a deterministic audit event record (no I/O).

    The event is a plain dict. Raw content is NOT retained. The
    audit_log_raw_content_retained invariant is always False. The
    audit_log_never_includes list always enumerates the hard-
    contract keys that the audit log must never expose.
    """
    if audit_log_entry_id is None:
        audit_log_entry_id = str(uuid.uuid4())
    return {
        "audit_log_version": AUDIT_LOG_VERSION,
        "audit_log_entry_id": str(audit_log_entry_id),
        "audit_log_recorded_at": str(audit_log_recorded_at) if audit_log_recorded_at is not None else "",
        "audit_log_action_type": str(audit_log_action_type) if audit_log_action_type is not None else "",
        "audit_log_operator_ref": str(audit_log_operator_ref) if audit_log_operator_ref is not None else "",
        "audit_log_target_account_id": str(audit_log_target_account_id) if audit_log_target_account_id is not None else "",
        "audit_log_target_session_id": str(audit_log_target_session_id) if audit_log_target_session_id is not None else "",
        "audit_log_target_resource": str(audit_log_target_resource) if audit_log_target_resource is not None else "",
        "audit_log_before_state": dict(audit_log_before_state) if audit_log_before_state else {},
        "audit_log_after_state": dict(audit_log_after_state) if audit_log_after_state else {},
        "audit_log_reason_label": str(audit_log_reason_label) if audit_log_reason_label is not None else "",
        "audit_log_summary": str(audit_log_summary) if audit_log_summary is not None else "",
        "audit_log_raw_content_retained": False,
        "audit_log_never_includes": sorted(AUDIT_LOG_NEVER_INCLUDES_V1),
        "reason_labels": list(reason_labels) if reason_labels else [REASON_OK],
        "future_log_storage_path_metadata": FUTURE_LOG_STORAGE_PATH_METADATA,
    }


def validate_audit_event_v1(event: Any) -> Tuple[bool, List[str]]:
    """
    Validate the audit event structure. Returns (is_valid, error_labels).
    Never raises. Pure structural check; no I/O.

    Enforces:
      - event is a dict
      - all required fields are present
      - audit_log_action_type is in the allowed categories
      - audit_log_raw_content_retained is False
      - no forbidden key from AUDIT_LOG_NEVER_INCLUDES_V1 appears
        anywhere in the event (recursively), including nested in
        before_state, after_state, source_context, or any other
        nested dict/list
      - audit_log_before_state / audit_log_after_state are dicts
    """
    errors: List[str] = []
    if not isinstance(event, dict):
        errors.append(REASON_INVALID_NOT_DICT)
        return False, errors
    for key in REQUIRED_AUDIT_EVENT_FIELDS_V1:
        if key not in event:
            errors.append(f"{REASON_INVALID_MISSING_FIELDS}:{key}")
    if "audit_log_action_type" in event:
        if event["audit_log_action_type"] not in ALLOWED_AUDIT_EVENT_CATEGORIES_V1:
            errors.append(f"{REASON_INVALID_BAD_CATEGORY}:{event['audit_log_action_type']}")
    if "audit_log_raw_content_retained" in event and event["audit_log_raw_content_retained"] is not False:
        errors.append("raw_content_retained_must_be_false")
    # Recursively scan the entire event for forbidden keys.
    forbidden_hits = _find_forbidden_keys(event)
    for forbidden_key in forbidden_hits:
        errors.append(f"{REASON_INVALID_NEVER_INCLUDES_KEY}:{forbidden_key}")
    if "audit_log_never_includes" in event:
        if not isinstance(event["audit_log_never_includes"], list):
            errors.append("never_includes_must_be_list")
    for state_key in ("audit_log_before_state", "audit_log_after_state"):
        if state_key in event and not isinstance(event[state_key], dict):
            errors.append(f"{state_key}_not_dict")
    if "reason_labels" in event and not isinstance(event["reason_labels"], list):
        errors.append("reason_labels_not_list")
    return (len(errors) == 0), errors


def _find_forbidden_keys(value: Any, _seen: Optional[set] = None) -> List[str]:
    """
    Recursively find any forbidden key from AUDIT_LOG_NEVER_INCLUDES_V1
    anywhere in the value. Returns a list of forbidden key names found.
    The audit_log_never_includes key itself is allowed to list the
    forbidden keys (that's the contract).
    """
    if _seen is None:
        _seen = set()
    hits: List[str] = []
    if isinstance(value, dict):
        if id(value) in _seen:
            return hits
        _seen = _seen | {id(value)}
        for k, v in value.items():
            if k == "audit_log_never_includes":
                # The contract list itself names the forbidden keys; skip.
                continue
            if k in AUDIT_LOG_NEVER_INCLUDES_V1:
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


# ----------------------------------------------------------------------------
# In-memory store operations
# ----------------------------------------------------------------------------

def append_audit_event_to_in_memory_store_v1(
    store: List[Dict[str, Any]],
    event: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Append a validated audit event to the injected in-memory store.

    Returns a result dict with metadata only. The event must be
    pre-validated (the caller is responsible for calling
    validate_audit_event_v1 first). This function performs a second
    validation pass as a safety net.

    Never raises. Never writes to disk.
    """
    base = {
        "audit_log_version": AUDIT_LOG_VERSION,
        "ok": False,
        "reason_labels": [],
        "entry_id": None,
        "summary": "",
    }

    if not isinstance(store, list):
        return {
            **base,
            "reason_labels": [REASON_INVALID_STORE_NOT_LIST],
            "summary": "append denied: store must be a list",
        }

    ok, errs = validate_audit_event_v1(event)
    if not ok:
        return {
            **base,
            "reason_labels": [REASON_INVALID_MISSING_FIELDS] + [f"err:{e}" for e in errs],
            "summary": "append denied: validation failed",
        }

    # Append a defensive copy so the caller cannot mutate the stored event.
    store.append(dict(event))
    return {
        **base,
        "ok": True,
        "reason_labels": [REASON_OK],
        "entry_id": event["audit_log_entry_id"],
        "summary": f"audit event appended for action_type='{event['audit_log_action_type']}'",
    }


def list_audit_events_from_in_memory_store_v1(
    store: List[Dict[str, Any]],
    *,
    account_id: Optional[str] = None,
    session_id: Optional[str] = None,
    action_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List audit events from the injected in-memory store, with
    optional filters.

    Filters are applied as AND-conditions; passing no filters
    returns all events. Returns a result dict with metadata only;
    never mutates the store.
    """
    base = {
        "audit_log_version": AUDIT_LOG_VERSION,
        "ok": False,
        "reason_labels": [],
        "count": 0,
        "events": [],
        "summary": "",
    }

    if not isinstance(store, list):
        return {
            **base,
            "reason_labels": [REASON_INVALID_STORE_NOT_LIST],
            "summary": "list denied: store must be a list",
        }

    results: List[Dict[str, Any]] = []
    for ev in store:
        if not isinstance(ev, dict):
            continue
        if account_id is not None and ev.get("audit_log_target_account_id") != account_id:
            continue
        if session_id is not None and ev.get("audit_log_target_session_id") != session_id:
            continue
        if action_type is not None and ev.get("audit_log_action_type") != action_type:
            continue
        results.append(dict(ev))

    return {
        **base,
        "ok": True,
        "reason_labels": [REASON_OK],
        "count": len(results),
        "events": results,
        "summary": f"list returned {len(results)} event(s)",
    }


# ----------------------------------------------------------------------------
# Summary / serialization
# ----------------------------------------------------------------------------

def summarize_audit_event_v1(event: Any) -> str:
    """Return a short, safe, human-readable summary line. No raw content."""
    if not isinstance(event, dict):
        return "summary:invalid_audit_event"
    action_type = event.get("audit_log_action_type", "")
    operator_ref = event.get("audit_log_operator_ref", "")
    target_account = event.get("audit_log_target_account_id", "")
    target_session = event.get("audit_log_target_session_id", "")
    reason = event.get("audit_log_reason_label", "")
    return (
        f"action={action_type} operator={operator_ref} "
        f"account={target_account} session={target_session} reason={reason}"
    )


def to_audit_log_json_safe_v1(value: Any) -> str:
    """
    Safely serialize any audit-log value to JSON.

    Strips private keys from the value before serialization. Falls
    back to a safe marker for unserializable input. Never includes
    raw prompts, credentials, hidden prompts, or chain-of-thought.
    """
    safe_value = _strip_private_keys(value)
    try:
        return json.dumps(safe_value, sort_keys=True, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return json.dumps({"serialization_error": True}, ensure_ascii=False)


# ----------------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------------

def _strip_private_keys(value: Any, _seen: Optional[set] = None) -> Any:
    """Recursively remove private keys from dicts; cycle detection."""
    if _seen is None:
        _seen = set()
    if isinstance(value, dict):
        if id(value) in _seen:
            return "<cyclic>"
        _seen = _seen | {id(value)}
        cleaned: Dict[str, Any] = {}
        for k, v in value.items():
            if k in AUDIT_LOG_NEVER_INCLUDES_V1:
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
    "AUDIT_LOG_VERSION",
    "ALLOWED_AUDIT_EVENT_CATEGORIES_V1",
    "AUDIT_LOG_NEVER_INCLUDES_V1",
    "REASON_OK",
    "REASON_INVALID_MISSING_FIELDS",
    "REASON_INVALID_BAD_CATEGORY",
    "REASON_INVALID_NEVER_INCLUDES_KEY",
    "REASON_INVALID_BAD_TIMESTAMP",
    "REASON_INVALID_NOT_DICT",
    "REASON_INVALID_STORE_NOT_LIST",
    "REASON_INVALID_NOT_FOUND",
    "FUTURE_LOG_STORAGE_PATH_METADATA",
    "REQUIRED_AUDIT_EVENT_FIELDS_V1",
    "build_audit_event_v1",
    "validate_audit_event_v1",
    "summarize_audit_event_v1",
    "append_audit_event_to_in_memory_store_v1",
    "list_audit_events_from_in_memory_store_v1",
    "to_audit_log_json_safe_v1",
]