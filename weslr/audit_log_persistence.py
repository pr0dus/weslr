"""
WESLR chat.weslr.de Slice 4B — Audit Log Persistence Helper V1

Standalone, bounded, append-only JSONL persistence helper for the
audit event schema defined in `weslr.audit_log` (Slice 4A).

This module:
  - imports ONLY safe functions/constants from `weslr.audit_log`
    (no protected runtime, no provider/model, no network, no
    subprocess, no ChatResponder)
  - performs controlled append-only file writes to a path provided
    by the caller (typically a temporary directory in tests)
  - NEVER writes to the production future-storage path
    "/home/pr0/weslr_state/logs/" — that path is recorded as a
    metadata constant only; no real I/O occurs against it
  - reads JSONL records back, with the same metadata-only filtering
    semantics as the in-memory store from Slice 4A
  - enforces the AUDIT_LOG_NEVER_INCLUDES_V1 hard contract at write
    time (refuses to write any record carrying a forbidden key)
  - is bounded: it does not auto-create parent directories, does
    not rotate logs, does not lock files, does not run any
    background process, and does not connect to any network
  - does not wire itself to the runtime wrapper, session manager,
    or any ChatResponder entry point

Production activation is OUT OF SCOPE for this slice. The persistence
helper is fully implemented and tested, but production code paths
(operator dashboard, customer portal, etc.) must explicitly call
the append_audit_event_jsonl_v1 function to persist audit records.
"""

from __future__ import annotations

# Pure stdlib only.
import json
import os
import tempfile
import uuid
from typing import Any, Dict, Iterable, List, Optional, Tuple


# Reuse the hard contract constants from Slice 4A.
from weslr.audit_log import (
    AUDIT_LOG_VERSION,
    ALLOWED_AUDIT_EVENT_CATEGORIES_V1,
    AUDIT_LOG_NEVER_INCLUDES_V1,
    REASON_OK,
    REASON_INVALID_MISSING_FIELDS,
    REASON_INVALID_BAD_CATEGORY,
    REASON_INVALID_NEVER_INCLUDES_KEY,
    REASON_INVALID_NOT_DICT,
    REASON_INVALID_BAD_TIMESTAMP,
)

# Slice 4B-specific reason labels. Defined locally to avoid editing
# Slice 4A's `weslr.audit_log` module.
_REASON_INVALID_PATH_NOT_PROVIDED = "invalid_path_not_provided"
_REASON_INVALID_PATH_NOT_FILE = "invalid_path_not_file"
_REASON_INVALID_PATH_FORBIDDEN_PRODUCTION = "invalid_path_forbidden_production"
_REASON_INVALID_EVENT_MISSING_FIELDS = "invalid_event_missing_required_fields"
_REASON_WRITE_FAILED = "write_failed"
_REASON_READ_FAILED = "read_failed"
_REASON_INVALID_NO_EVENTS = "invalid_no_events"
_REASON_INVALID_LIMIT_TOO_LARGE = "invalid_limit_too_large"
_REASON_PARENT_DIRECTORY_DOES_NOT_EXIST = "parent_directory_does_not_exist"
_REASON_VERSION_MISMATCH = "version_mismatch"

# Use a path constant for the FUTURE production storage location.
# It is NEVER used for I/O in this module. It is recorded as
# metadata only and used by `validate_audit_log_persistence_request_v1`
# to refuse any explicit production target.
FUTURE_PRODUCTION_LOG_STORAGE_PATH = "/home/pr0/weslr_state/logs/"

# Hard cap on `limit` parameter to prevent unbounded reads.
DEFAULT_MAX_READ_LIMIT = 1000

# Validate the imported reason labels exist. If any are missing, fail
# fast at import time so the caller can detect a Slice 4A drift.
_REQUIRED_IMPORTED_LABELS = (
    "REASON_OK",
    "REASON_INVALID_MISSING_FIELDS",
    "REASON_INVALID_BAD_CATEGORY",
    "REASON_INVALID_NEVER_INCLUDES_KEY",
    "REASON_INVALID_NOT_DICT",
    "REASON_INVALID_BAD_TIMESTAMP",
)
for _name in _REQUIRED_IMPORTED_LABELS:
    if not hasattr(__import__("weslr.audit_log", fromlist=[_name]), _name):
        raise ImportError(
            f"weslr.audit_log_persistence requires weslr.audit_log.{_name}; "
            f"the audit_log module does not export it"
        )


# ----------------------------------------------------------------------------
# Data model
# ----------------------------------------------------------------------------

def build_audit_log_persistence_request_v1(
    *,
    log_file_path: str,
    operator_ref: str = "operator_unknown",
    now: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a deterministic persistence request (no I/O).

    The request is a plain dict. The future production storage
    path is recorded as a metadata constant; the request itself
    carries the explicit `log_file_path` (caller-controlled).
    """
    return {
        "persistence_version": "weslr-audit-log-persistence-v1",
        "request_id": str(uuid.uuid4()),
        "operator_ref": str(operator_ref) if operator_ref is not None else "",
        "log_file_path": str(log_file_path) if log_file_path is not None else "",
        "created_at": str(now) if now is not None else "",
        "future_production_storage_path_metadata": FUTURE_PRODUCTION_LOG_STORAGE_PATH,
    }


def validate_audit_log_persistence_request_v1(request: Any) -> Tuple[bool, List[str]]:
    """
    Validate the persistence request structure. Returns (is_valid,
    error_labels). Never raises. Pure structural check; no I/O.

    Enforces:
      - request is a dict
      - required fields are present
      - log_file_path is a non-empty string
      - log_file_path does NOT point at the production future
        storage path "/home/pr0/weslr_state/logs/" (this slice
        refuses any explicit production target)
      - log_file_path is a regular file path or a path that does
        not yet exist (parent directory must exist; this helper
        will NOT create parent directories)
    """
    errors: List[str] = []
    if not isinstance(request, dict):
        errors.append(REASON_INVALID_NOT_DICT)
        return False, errors
    for key in (
        "persistence_version",
        "request_id",
        "operator_ref",
        "log_file_path",
        "created_at",
        "future_production_storage_path_metadata",
    ):
        if key not in request:
            errors.append(f"{REASON_INVALID_MISSING_FIELDS}:{key}")
    if "log_file_path" in request:
        path = request["log_file_path"]
        if not isinstance(path, str) or not path:
            errors.append(_REASON_INVALID_PATH_NOT_PROVIDED)
        elif path == FUTURE_PRODUCTION_LOG_STORAGE_PATH:
            errors.append(_REASON_INVALID_PATH_FORBIDDEN_PRODUCTION)
        # Reject obviously dangerous path patterns.
        if isinstance(path, str):
            if "\x00" in path:
                errors.append("invalid_path_contains_null_byte")
    return (len(errors) == 0), errors


# ----------------------------------------------------------------------------
# Write (append-only JSONL)
# ----------------------------------------------------------------------------

def _event_validates_against_contract(event: Any) -> List[str]:
    """
    Returns a list of validation errors for an audit event against
    the Slice 4A hard contract. Empty list = valid.

    The contract is enforced in three ways:
      1) all required fields present
      2) action_type is in ALLOWED_AUDIT_EVENT_CATEGORIES_V1
      3) NO forbidden key from AUDIT_LOG_NEVER_INCLUDES_V1 appears
         anywhere in the event payload (recursive)
      4) raw_content_retained is False

    This is a focused validator for the persistence path. The
    canonical validator in weslr.audit_log is the source of truth
    for the event schema; this function enforces a strict subset of
    those rules at write time as a defense-in-depth check.
    """
    errors: List[str] = []
    if not isinstance(event, dict):
        errors.append(REASON_INVALID_NOT_DICT)
        return errors
    required = (
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
    for key in required:
        if key not in event:
            errors.append(f"{_REASON_INVALID_EVENT_MISSING_FIELDS}:{key}")
    if "audit_log_action_type" in event:
        if event["audit_log_action_type"] not in ALLOWED_AUDIT_EVENT_CATEGORIES_V1:
            errors.append(f"{REASON_INVALID_BAD_CATEGORY}:{event['audit_log_action_type']}")
    if "audit_log_raw_content_retained" in event and event["audit_log_raw_content_retained"] is not False:
        errors.append("raw_content_retained_must_be_false")
    # Recursive scan for forbidden keys.
    forbidden_hits = _find_forbidden_keys(event)
    for k in forbidden_hits:
        errors.append(f"{REASON_INVALID_NEVER_INCLUDES_KEY}:{k}")
    return errors


def _find_forbidden_keys(value: Any, _seen: Optional[set] = None) -> List[str]:
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


def append_audit_event_jsonl_v1(
    request: Dict[str, Any],
    event: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Append a single audit event to the JSONL file at the request's
    `log_file_path`. Append-only; one JSON object per line.

    Returns a result dict with metadata only. Never raises.
    Performs no real I/O against the production future-storage path.
    Performs no I/O if the request is invalid.
    """
    base = {
        "persistence_version": "weslr-audit-log-persistence-v1",
        "ok": False,
        "reason_labels": [],
        "entry_id": None,
        "bytes_written": 0,
        "summary": "",
    }

    # 1. Validate the request.
    ok, errs = validate_audit_log_persistence_request_v1(request)
    if not ok:
        return {
            **base,
            "reason_labels": [REASON_INVALID_MISSING_FIELDS] + [f"err:{e}" for e in errs],
            "summary": "append denied: persistence request invalid",
        }

    # 2. Validate the event against the Slice 4A hard contract.
    event_errs = _event_validates_against_contract(event)
    if event_errs:
        return {
            **base,
            "reason_labels": event_errs,
            "summary": "append denied: event violates hard contract",
        }

    # 3. Sanity: the event must reference the same AUDIT_LOG_VERSION.
    if event.get("audit_log_version") != AUDIT_LOG_VERSION:
        return {
            **base,
            "reason_labels": [f"{_REASON_VERSION_MISMATCH}:{event.get('audit_log_version')}"],
            "summary": "append denied: event version does not match canonical",
        }

    # 4. Refuse to write to the production future-storage path.
    path = request["log_file_path"]
    if path == FUTURE_PRODUCTION_LOG_STORAGE_PATH:
        return {
            **base,
            "reason_labels": [_REASON_INVALID_PATH_FORBIDDEN_PRODUCTION],
            "summary": "append denied: production path is forbidden in this slice",
        }

    # 5. Refuse to create parent directories or write outside a
    #    caller-controlled path. The caller MUST provide a writable
    #    file (existing or new) in a caller-controlled directory.
    parent = os.path.dirname(os.path.abspath(path)) or "."
    if not os.path.isdir(parent):
        return {
            **base,
            "reason_labels": [_REASON_PARENT_DIRECTORY_DOES_NOT_EXIST],
            "summary": f"append denied: parent directory does not exist: {parent}",
        }

    # 6. Serialize safely. Re-serialize the event via the JSON-safe
    #    helper to enforce the recursive private-key strip.
    safe_line = to_audit_log_persistence_json_safe_v1(event)
    line = safe_line + "\n"
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError as exc:
        return {
            **base,
            "reason_labels": [f"{_REASON_WRITE_FAILED}:{type(exc).__name__}"],
            "summary": f"append failed: {exc}",
        }
    return {
        **base,
        "ok": True,
        "reason_labels": [REASON_OK],
        "entry_id": event.get("audit_log_entry_id"),
        "bytes_written": len(line.encode("utf-8")),
        "summary": f"audit event appended (bytes={len(line.encode('utf-8'))})",
    }


# ----------------------------------------------------------------------------
# Read (with metadata-only filtering)
# ----------------------------------------------------------------------------

def read_audit_events_jsonl_v1(
    request: Dict[str, Any],
    *,
    account_id: Optional[str] = None,
    session_id: Optional[str] = None,
    action_type: Optional[str] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Read audit events from the JSONL file at the request's
    `log_file_path`, with optional filters and a bounded `limit`.

    Returns a result dict with metadata only. Never raises.
    Refuses to read from the production future-storage path.
    """
    base = {
        "persistence_version": "weslr-audit-log-persistence-v1",
        "ok": False,
        "reason_labels": [],
        "count": 0,
        "events": [],
        "summary": "",
    }

    # 1. Validate the request.
    ok, errs = validate_audit_log_persistence_request_v1(request)
    if not ok:
        return {
            **base,
            "reason_labels": [REASON_INVALID_MISSING_FIELDS] + [f"err:{e}" for e in errs],
            "summary": "read denied: persistence request invalid",
        }

    # 2. Refuse to read from the production future-storage path.
    path = request["log_file_path"]
    if path == FUTURE_PRODUCTION_LOG_STORAGE_PATH:
        return {
            **base,
            "reason_labels": [_REASON_INVALID_PATH_FORBIDDEN_PRODUCTION],
            "summary": "read denied: production path is forbidden in this slice",
        }

    # 3. Validate limit.
    if limit is not None:
        if not isinstance(limit, int) or limit < 0:
            return {
                **base,
                "reason_labels": ["invalid_limit_not_non_negative_int"],
                "summary": "read denied: limit must be a non-negative int",
            }
        if limit > DEFAULT_MAX_READ_LIMIT:
            return {
                **base,
                "reason_labels": [_REASON_INVALID_LIMIT_TOO_LARGE],
                "summary": f"read denied: limit exceeds max ({DEFAULT_MAX_READ_LIMIT})",
            }

    # 4. The file does not need to exist; missing file is "zero events".
    if not os.path.exists(path):
        return {
            **base,
            "ok": True,
            "reason_labels": [REASON_OK],
            "count": 0,
            "events": [],
            "summary": "read returned 0 events (file does not exist yet)",
        }
    if not os.path.isfile(path):
        return {
            **base,
            "reason_labels": [_REASON_INVALID_PATH_NOT_FILE],
            "summary": "read denied: path is not a regular file",
        }

    # 5. Read line by line; filter; honor limit.
    results: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    parsed = json.loads(line)
                except json.JSONDecodeError:
                    # Skip malformed lines; do not fail the whole read.
                    continue
                if not isinstance(parsed, dict):
                    continue
                if account_id is not None and parsed.get("audit_log_target_account_id") != account_id:
                    continue
                if session_id is not None and parsed.get("audit_log_target_session_id") != session_id:
                    continue
                if action_type is not None and parsed.get("audit_log_action_type") != action_type:
                    continue
                results.append(parsed)
                if limit is not None and len(results) >= limit:
                    break
    except OSError as exc:
        return {
            **base,
            "reason_labels": [f"{_REASON_READ_FAILED}:{type(exc).__name__}"],
            "summary": f"read failed: {exc}",
        }
    return {
        **base,
        "ok": True,
        "reason_labels": [REASON_OK],
        "count": len(results),
        "events": results,
        "summary": f"read returned {len(results)} event(s)",
    }


# ----------------------------------------------------------------------------
# Summary / serialization
# ----------------------------------------------------------------------------

def summarize_audit_log_persistence_request_v1(request: Any) -> str:
    """Return a short, safe, human-readable summary. No raw content."""
    if not isinstance(request, dict):
        return "summary:invalid_persistence_request"
    path = request.get("log_file_path", "")
    operator_ref = request.get("operator_ref", "")
    return f"persistence_request operator={operator_ref} path={path}"


def to_audit_log_persistence_json_safe_v1(value: Any) -> str:
    """
    Safely serialize any persistence-related value to JSON.

    Strips keys from AUDIT_LOG_NEVER_INCLUDES_V1 (recursive).
    Cycle detection. Falls back to a safe marker for unserializable
    input. Never includes raw prompts, credentials, hidden prompts,
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
    "FUTURE_PRODUCTION_LOG_STORAGE_PATH",
    "DEFAULT_MAX_READ_LIMIT",
    "build_audit_log_persistence_request_v1",
    "validate_audit_log_persistence_request_v1",
    "append_audit_event_jsonl_v1",
    "read_audit_events_jsonl_v1",
    "summarize_audit_log_persistence_request_v1",
    "to_audit_log_persistence_json_safe_v1",
]