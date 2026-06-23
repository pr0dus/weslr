"""
WESLR chat.weslr.de Slice 3 — Session Manager Skeleton V1

Deterministic, pure-Python, no-I/O session manager.

This module manages session records in an injected in-memory store
(e.g. a plain dict). It does NOT:
  - import or call weslr.chat_responder, main, dialogue, chat_ui,
    backend server files, provider/model code, or any protected
    runtime module
  - perform subprocess, network, or filesystem write operations
  - read or write "/home/pr0/weslr_state/sessions/" (the future
    storage path is recorded as metadata only)
  - retain raw prompt text, raw reply text, credentials, PII,
    hidden prompts, system prompts, chain-of-thought traces,
    provider/LLM API responses, or real shadow-call outputs
  - claim AGI / sentience / consciousness / benchmark / public-science
    / production-ready / live-public-runtime
  - silently extend a session's absolute expiry
  - share state between sessions by default

Sessions have bounded lifetime, are isolated, and never share state by
default. Force-logged-out sessions cannot be reactivated by touch.
"""

from __future__ import annotations

# Pure stdlib only.
import json
import uuid
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

SESSION_MANAGER_VERSION = "weslr-session-manager-v1"

# Session lifecycle statuses (machine-readable; safe to log).
SESSION_STATUS_ACTIVE = "active"
SESSION_STATUS_EXPIRED = "expired"
SESSION_STATUS_FORCE_LOGGED_OUT = "force_logged_out"
SESSION_STATUS_UNKNOWN = "unknown"

VALID_SESSION_STATUSES = frozenset({
    SESSION_STATUS_ACTIVE,
    SESSION_STATUS_EXPIRED,
    SESSION_STATUS_FORCE_LOGGED_OUT,
    SESSION_STATUS_UNKNOWN,
})

# Reason labels (machine-readable; safe to log; never expose internal text).
REASON_OK = "ok"
REASON_INVALID_MISSING_IDENTITY = "invalid_missing_identity"
REASON_INVALID_MISSING_SESSION_ID = "invalid_missing_session_id"
REASON_INVALID_MISSING_CAPABILITY_SET = "invalid_missing_capability_set"
REASON_INVALID_MISSING_REQUIRED_FIELDS = "invalid_missing_required_fields"
REASON_INVALID_BAD_STATUS = "invalid_bad_status"
REASON_INVALID_BAD_TIMESTAMP = "invalid_bad_timestamp"
REASON_NOT_FOUND = "session_not_found"
REASON_ALREADY_EXPIRED = "session_already_expired"
REASON_ALREADY_FORCE_LOGGED_OUT = "session_already_force_logged_out"
REASON_CANNOT_TOUCH_EXPIRED = "cannot_touch_expired_session"
REASON_CANNOT_TOUCH_FORCE_LOGGED_OUT = "cannot_touch_force_logged_out_session"
REASON_DEFAULT_EXPIRY_REASON = "operator_or_timeout"

# Default policy values (override per call when needed).
DEFAULT_IDLE_TIMEOUT_SECONDS = 24 * 60 * 60            # 24h
DEFAULT_ABSOLUTE_TIMEOUT_SECONDS = 7 * 24 * 60 * 60   # 7d

# Future real-storage path (metadata only; never used for I/O in this slice).
FUTURE_STORAGE_PATH_METADATA = "/home/pr0/weslr_state/sessions/"


# ----------------------------------------------------------------------------
# Data model
# ----------------------------------------------------------------------------

def build_session_record_v1(
    *,
    identity_id: str,
    capability_set: Optional[Iterable[str]] = None,
    session_id: Optional[str] = None,
    created_at: Optional[str] = None,
    last_seen_at: Optional[str] = None,
    expires_at: Optional[str] = None,
    red_zone_acknowledged_at: Optional[str] = None,
    state_snapshot_ref: Optional[str] = "",
    audit_log_ref: Optional[str] = "",
    session_status: str = SESSION_STATUS_ACTIVE,
    reason_labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Build a deterministic session record (no I/O).

    The record is a plain dict. Raw content is NOT retained. The
    future storage path is included as a metadata constant only;
    no file I/O occurs.
    """
    if session_id is None:
        session_id = str(uuid.uuid4())
    return {
        "session_manager_version": SESSION_MANAGER_VERSION,
        "session_id": str(session_id),
        "identity_id": str(identity_id) if identity_id is not None else "",
        "created_at": str(created_at) if created_at is not None else "",
        "last_seen_at": str(last_seen_at) if last_seen_at is not None else "",
        "expires_at": str(expires_at) if expires_at is not None else "",
        "capability_set": list(capability_set) if capability_set else [],
        "red_zone_acknowledged_at": (
            str(red_zone_acknowledged_at) if red_zone_acknowledged_at is not None else ""
        ),
        "state_snapshot_ref": str(state_snapshot_ref) if state_snapshot_ref else "",
        "audit_log_ref": str(audit_log_ref) if audit_log_ref else "",
        "session_status": str(session_status),
        "reason_labels": list(reason_labels) if reason_labels else [],
        "raw_content_retained": False,
        "cross_session_shared": False,
        "future_storage_path_metadata": FUTURE_STORAGE_PATH_METADATA,
    }


def validate_session_record_v1(session: Any) -> Tuple[bool, List[str]]:
    """
    Validate the session record structure. Returns (is_valid, error_labels).
    Never raises. Pure structural check; no I/O.
    """
    errors: List[str] = []
    if not isinstance(session, dict):
        errors.append("session_not_dict")
        return False, errors
    for key in (
        "session_manager_version",
        "session_id",
        "identity_id",
        "created_at",
        "last_seen_at",
        "expires_at",
        "capability_set",
        "red_zone_acknowledged_at",
        "state_snapshot_ref",
        "audit_log_ref",
        "session_status",
        "reason_labels",
        "raw_content_retained",
        "cross_session_shared",
    ):
        if key not in session:
            errors.append(f"missing_field:{key}")
    if "session_id" in session and not _is_nonempty_str(session["session_id"]):
        errors.append("empty_session_id")
    if "identity_id" in session and not _is_nonempty_str(session["identity_id"]):
        errors.append("empty_identity_id")
    if "capability_set" in session:
        if not isinstance(session["capability_set"], list):
            errors.append("capability_set_not_list")
        elif len(session["capability_set"]) == 0:
            errors.append("empty_capability_set")
    if "session_status" in session and session["session_status"] not in VALID_SESSION_STATUSES:
        errors.append("invalid_status")
    if "raw_content_retained" in session and session["raw_content_retained"] is not False:
        errors.append("raw_content_retained_must_be_false")
    if "cross_session_shared" in session and session["cross_session_shared"] is not False:
        errors.append("cross_session_shared_must_be_false")
    return (len(errors) == 0), errors


def _is_nonempty_str(v: Any) -> bool:
    return isinstance(v, str) and len(v) > 0


# ----------------------------------------------------------------------------
# Store operations (in-memory dict; injected)
# ----------------------------------------------------------------------------

def create_session_v1(
    store: Dict[str, Dict[str, Any]],
    identity_id: str,
    capability_set: Optional[Iterable[str]],
    *,
    session_id: Optional[str] = None,
    created_at: Optional[str] = None,
    expires_at: Optional[str] = None,
    red_zone_acknowledged_at: Optional[str] = None,
    state_snapshot_ref: Optional[str] = "",
    audit_log_ref: Optional[str] = "",
    reason_labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Create a new session in the injected in-memory store.

    Returns a result dict with `authorized`-style structure (metadata
    only). Never raises. Does not perform filesystem I/O.
    """
    base = _base_result()

    # Validate identity and capability_set first.
    if not _is_nonempty_str(identity_id):
        return {
            **base,
            "ok": False,
            "reason_labels": [REASON_INVALID_MISSING_IDENTITY],
            "session": None,
            "summary": "create_session denied: missing identity_id",
        }
    caps = list(capability_set) if capability_set else []
    if not caps:
        return {
            **base,
            "ok": False,
            "reason_labels": [REASON_INVALID_MISSING_CAPABILITY_SET],
            "session": None,
            "summary": "create_session denied: missing capability_set",
        }

    if not isinstance(store, dict):
        return {
            **base,
            "ok": False,
            "reason_labels": ["invalid_store_not_dict"],
            "session": None,
            "summary": "create_session denied: store must be a dict",
        }

    record = build_session_record_v1(
        identity_id=identity_id,
        capability_set=caps,
        session_id=session_id,
        created_at=created_at,
        last_seen_at=created_at,  # last_seen_at starts equal to created_at
        expires_at=expires_at,
        red_zone_acknowledged_at=red_zone_acknowledged_at,
        state_snapshot_ref=state_snapshot_ref,
        audit_log_ref=audit_log_ref,
        session_status=SESSION_STATUS_ACTIVE,
        reason_labels=[REASON_OK],
    )
    ok, errs = validate_session_record_v1(record)
    if not ok:
        return {
            **base,
            "ok": False,
            "reason_labels": [REASON_INVALID_MISSING_REQUIRED_FIELDS] + [f"err:{e}" for e in errs],
            "session": None,
            "summary": "create_session denied: validation failed",
        }

    # Prevent collision.
    if record["session_id"] in store:
        return {
            **base,
            "ok": False,
            "reason_labels": ["session_id_already_exists"],
            "session": None,
            "summary": "create_session denied: session_id already exists",
        }

    # Store the record (in-memory only).
    store[record["session_id"]] = dict(record)
    return {
        **base,
        "ok": True,
        "reason_labels": [REASON_OK],
        "session": dict(record),
        "summary": f"session created for identity '{identity_id}'",
    }


def get_session_v1(
    store: Dict[str, Dict[str, Any]],
    session_id: str,
    *,
    now: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get a session by id from the injected store.

    Returns a safe result dict. If the session is missing, returns a
    `not_found` result with no raw content. If the session is
    present but its absolute expiry has passed, returns the record
    with session_status="expired" but does NOT mutate the store.
    """
    base = _base_result()

    if not _is_nonempty_str(session_id):
        return {
            **base,
            "ok": False,
            "reason_labels": [REASON_INVALID_MISSING_SESSION_ID],
            "session": None,
            "summary": "get_session denied: missing session_id",
        }
    if not isinstance(store, dict):
        return {
            **base,
            "ok": False,
            "reason_labels": ["invalid_store_not_dict"],
            "session": None,
            "summary": "get_session denied: store must be a dict",
        }

    record = store.get(session_id)
    if record is None:
        return {
            **base,
            "ok": False,
            "reason_labels": [REASON_NOT_FOUND],
            "session": None,
            "summary": f"session '{session_id}' not found",
        }

    # Return a copy with status evaluated against absolute expiry.
    snapshot = dict(record)
    status = _effective_status(record, now=now)
    snapshot["session_status"] = status
    return {
        **base,
        "ok": True,
        "reason_labels": [REASON_OK] if status == SESSION_STATUS_ACTIVE else [f"observed:{status}"],
        "session": snapshot,
        "summary": f"session '{session_id}' observed as {status}",
    }


def touch_session_v1(
    store: Dict[str, Dict[str, Any]],
    session_id: str,
    *,
    now: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Touch a session (update last_seen_at).

    Touching does NOT silently extend the absolute expiry. Touching
    an expired or force-logged-out session returns a denial.
    Touching an unknown session returns not-found.
    """
    base = _base_result()

    if not _is_nonempty_str(session_id):
        return {
            **base,
            "ok": False,
            "reason_labels": [REASON_INVALID_MISSING_SESSION_ID],
            "session": None,
            "summary": "touch denied: missing session_id",
        }
    if not isinstance(store, dict):
        return {
            **base,
            "ok": False,
            "reason_labels": ["invalid_store_not_dict"],
            "session": None,
            "summary": "touch denied: store must be a dict",
        }

    record = store.get(session_id)
    if record is None:
        return {
            **base,
            "ok": False,
            "reason_labels": [REASON_NOT_FOUND],
            "session": None,
            "summary": f"session '{session_id}' not found",
        }

    if record.get("session_status") == SESSION_STATUS_FORCE_LOGGED_OUT:
        return {
            **base,
            "ok": False,
            "reason_labels": [REASON_CANNOT_TOUCH_FORCE_LOGGED_OUT],
            "session": dict(record),
            "summary": "touch denied: session is force-logged-out",
        }

    if _is_expired(record, now=now):
        # Mark as expired (do not silently reactivate).
        record["session_status"] = SESSION_STATUS_EXPIRED
        return {
            **base,
            "ok": False,
            "reason_labels": [REASON_CANNOT_TOUCH_EXPIRED],
            "session": dict(record),
            "summary": "touch denied: session is expired",
        }

    # Update last_seen_at only.
    if now is not None:
        record["last_seen_at"] = str(now)
    return {
        **base,
        "ok": True,
        "reason_labels": [REASON_OK],
        "session": dict(record),
        "summary": f"session '{session_id}' touched",
    }


def expire_session_v1(
    store: Dict[str, Dict[str, Any]],
    session_id: str,
    *,
    reason: str = REASON_DEFAULT_EXPIRY_REASON,
    now: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Mark a session as expired.

    An already-force-logged-out session cannot be transitioned to
    expired (it stays force-logged-out, which is terminal). Unknown
    sessions return not-found. Reason labels are recorded as
    metadata only; no raw content.
    """
    base = _base_result()

    if not _is_nonempty_str(session_id):
        return {
            **base,
            "ok": False,
            "reason_labels": [REASON_INVALID_MISSING_SESSION_ID],
            "session": None,
            "summary": "expire denied: missing session_id",
        }
    if not isinstance(store, dict):
        return {
            **base,
            "ok": False,
            "reason_labels": ["invalid_store_not_dict"],
            "session": None,
            "summary": "expire denied: store must be a dict",
        }

    record = store.get(session_id)
    if record is None:
        return {
            **base,
            "ok": False,
            "reason_labels": [REASON_NOT_FOUND],
            "session": None,
            "summary": f"session '{session_id}' not found",
        }

    if record.get("session_status") == SESSION_STATUS_FORCE_LOGGED_OUT:
        return {
            **base,
            "ok": False,
            "reason_labels": [REASON_ALREADY_FORCE_LOGGED_OUT],
            "session": dict(record),
            "summary": "expire denied: already force-logged-out (terminal)",
        }

    if record.get("session_status") == SESSION_STATUS_EXPIRED:
        return {
            **base,
            "ok": False,
            "reason_labels": [REASON_ALREADY_EXPIRED],
            "session": dict(record),
            "summary": "expire denied: already expired",
        }

    if _is_expired(record, now=now):
        return {
            **base,
            "ok": False,
            "reason_labels": [REASON_ALREADY_EXPIRED],
            "session": dict(record),
            "summary": "expire denied: already expired (absolute)",
        }

    record["session_status"] = SESSION_STATUS_EXPIRED
    safe_reason = _safe_reason_label(reason)
    if safe_reason not in record["reason_labels"]:
        record["reason_labels"].append(safe_reason)
    return {
        **base,
        "ok": True,
        "reason_labels": [safe_reason],
        "session": dict(record),
        "summary": f"session '{session_id}' expired",
    }


def force_logout_session_v1(
    store: Dict[str, Dict[str, Any]],
    session_id: str,
    operator_ref: str,
    *,
    now: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Force-logout a session. Operator reference is recorded as a
    short token; raw content is NOT retained. Force-logout is
    terminal: a force-logged-out session cannot be reactivated.
    """
    base = _base_result()

    if not _is_nonempty_str(session_id):
        return {
            **base,
            "ok": False,
            "reason_labels": [REASON_INVALID_MISSING_SESSION_ID],
            "session": None,
            "summary": "force_logout denied: missing session_id",
        }
    if not _is_nonempty_str(operator_ref):
        return {
            **base,
            "ok": False,
            "reason_labels": ["invalid_missing_operator_ref"],
            "session": None,
            "summary": "force_logout denied: missing operator_ref",
        }
    if not isinstance(store, dict):
        return {
            **base,
            "ok": False,
            "reason_labels": ["invalid_store_not_dict"],
            "session": None,
            "summary": "force_logout denied: store must be a dict",
        }

    record = store.get(session_id)
    if record is None:
        return {
            **base,
            "ok": False,
            "reason_labels": [REASON_NOT_FOUND],
            "session": None,
            "summary": f"session '{session_id}' not found",
        }

    if record.get("session_status") == SESSION_STATUS_FORCE_LOGGED_OUT:
        return {
            **base,
            "ok": False,
            "reason_labels": [REASON_ALREADY_FORCE_LOGGED_OUT],
            "session": dict(record),
            "summary": "force_logout denied: already force-logged-out",
        }

    record["session_status"] = SESSION_STATUS_FORCE_LOGGED_OUT
    safe_operator_ref = _safe_short_ref(operator_ref)
    if safe_operator_ref and safe_operator_ref not in record["reason_labels"]:
        record["reason_labels"].append(safe_operator_ref)
    return {
        **base,
        "ok": True,
        "reason_labels": [REASON_OK],
        "session": dict(record),
        "summary": f"session '{session_id}' force-logged-out by operator",
    }


# ----------------------------------------------------------------------------
# Summary / serialization
# ----------------------------------------------------------------------------

def summarize_session_record_v1(session: Any) -> str:
    """Return a short, safe, human-readable summary line. No raw content."""
    if not isinstance(session, dict):
        return "summary:invalid_session"
    session_id = session.get("session_id", "")
    identity_id = session.get("identity_id", "")
    status = session.get("session_status", SESSION_STATUS_UNKNOWN)
    created = session.get("created_at", "")
    expires = session.get("expires_at", "")
    return f"session_id={session_id} identity={identity_id} status={status} created={created} expires={expires}"


def to_session_manager_json_safe_v1(value: Any) -> str:
    """
    Safely serialize any session-manager value to JSON.

    Strips raw/private keys; falls back to a safe marker for
    unserializable input. Never includes raw prompts, credentials,
    PII, hidden prompts, or chain-of-thought traces.
    """
    safe_value = _strip_private_keys(value)
    try:
        return json.dumps(safe_value, sort_keys=True, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return json.dumps({"serialization_error": True}, ensure_ascii=False)


# ----------------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------------

_PRIVATE_KEYS = frozenset({
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


def _base_result() -> Dict[str, Any]:
    return {
        "session_manager_version": SESSION_MANAGER_VERSION,
        "ok": False,
        "reason_labels": [],
        "session": None,
        "summary": "",
    }


def _strip_private_keys(value: Any, _seen: Optional[set] = None) -> Any:
    """Recursively remove private keys from dicts; lists and scalars pass through.

    Detects cyclic structures to avoid infinite recursion.
    """
    if _seen is None:
        _seen = set()
    if isinstance(value, dict):
        if id(value) in _seen:
            return "<cyclic>"
        _seen = _seen | {id(value)}
        cleaned: Dict[str, Any] = {}
        for k, v in value.items():
            if k in _PRIVATE_KEYS:
                continue
            cleaned[k] = _strip_private_keys(v, _seen)
        return cleaned
    if isinstance(value, list):
        if id(value) in _seen:
            return "<cyclic>"
        _seen = _seen | {id(value)}
        return [_strip_private_keys(item, _seen) for item in value]
    return value


def _safe_reason_label(reason: str) -> str:
    """Coerce an arbitrary reason string to a safe, machine-readable label."""
    if not reason:
        return REASON_DEFAULT_EXPIRY_REASON
    safe = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in str(reason))
    return safe[:64] if safe else REASON_DEFAULT_EXPIRY_REASON


def _safe_short_ref(ref: str) -> str:
    """Coerce an operator reference to a short, safe token. Never the raw ref."""
    if not ref:
        return ""
    safe = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in str(ref))
    return f"operator:{safe[:48]}"


def _is_expired(record: Dict[str, Any], *, now: Optional[str]) -> bool:
    """
    Return True if absolute expiry has passed. Only compares string
    timestamps lexicographically; if timestamps cannot be compared,
    the record is treated as not-yet-expired (no silent extension).
    """
    expires_at = record.get("expires_at", "")
    if not expires_at:
        return False
    if now is None:
        return False
    # Lexicographic compare on ISO-ish timestamps; works for ISO 8601 in UTC.
    return str(now) > str(expires_at)


def _effective_status(record: Dict[str, Any], *, now: Optional[str]) -> str:
    """Compute the effective status (active / expired / force_logged_out / unknown)."""
    current = record.get("session_status", SESSION_STATUS_UNKNOWN)
    if current == SESSION_STATUS_FORCE_LOGGED_OUT:
        return SESSION_STATUS_FORCE_LOGGED_OUT
    if _is_expired(record, now=now):
        return SESSION_STATUS_EXPIRED
    if current in VALID_SESSION_STATUSES:
        return current
    return SESSION_STATUS_UNKNOWN


__all__ = [
    "SESSION_MANAGER_VERSION",
    "SESSION_STATUS_ACTIVE",
    "SESSION_STATUS_EXPIRED",
    "SESSION_STATUS_FORCE_LOGGED_OUT",
    "SESSION_STATUS_UNKNOWN",
    "VALID_SESSION_STATUSES",
    "REASON_OK",
    "REASON_INVALID_MISSING_IDENTITY",
    "REASON_INVALID_MISSING_SESSION_ID",
    "REASON_INVALID_MISSING_CAPABILITY_SET",
    "REASON_INVALID_MISSING_REQUIRED_FIELDS",
    "REASON_INVALID_BAD_STATUS",
    "REASON_INVALID_BAD_TIMESTAMP",
    "REASON_NOT_FOUND",
    "REASON_ALREADY_EXPIRED",
    "REASON_ALREADY_FORCE_LOGGED_OUT",
    "REASON_CANNOT_TOUCH_EXPIRED",
    "REASON_CANNOT_TOUCH_FORCE_LOGGED_OUT",
    "REASON_DEFAULT_EXPIRY_REASON",
    "DEFAULT_IDLE_TIMEOUT_SECONDS",
    "DEFAULT_ABSOLUTE_TIMEOUT_SECONDS",
    "FUTURE_STORAGE_PATH_METADATA",
    "build_session_record_v1",
    "validate_session_record_v1",
    "create_session_v1",
    "get_session_v1",
    "touch_session_v1",
    "expire_session_v1",
    "force_logout_session_v1",
    "summarize_session_record_v1",
    "to_session_manager_json_safe_v1",
]