# weslr/bootstrap.py — Institutional Bootstrap Trust Foundation
# Minimum safe foundation: bootstrap trust anchor schema, lifecycle helpers, timeline terminology.
#
# DO NOT yet send real emails or build activation link UI.
# DO NOT yet register real device tokens in production flow.
# This module provides the foundation; email/UI integration is a separate slice.

from __future__ import annotations

import hashlib
import secrets
import time
from typing import Any


# =============================================================================
# TERMINOLOGY NOTE
# =============================================================================
# WESLR uses "timeline" instead of "session" throughout this module.
# A timeline is the persistent identity record for a human-WESLR relationship.
# A session is a discrete connection event — timelines are the correct unit.
# =============================================================================


# =============================================================================
# BOOTSTRAP TRUST ANCHOR SCHEMA
# =============================================================================
# The bootstrap trust anchor is the root identity record created when a user
# completes the deployment bootstrap flow. All later SS-TDE/CEA flows
# reference this anchor via timeline_id.

BOOTSTRAP_ANCHOR_KINDS = [
    "secret_words",    # 3–4 word challenge phrase (hashed)
    "device",          # First trusted device registration
    "email_verified",  # Email address confirmed at bootstrap
]


def new_timeline_id(user_id: str) -> str:
    """Generate a new persistent timeline_id for a user.

    timeline_id is the persistent identifier for a human's ongoing
    relationship with WESLR. It is created at bootstrap and survives
    dormancy and re-engagement.

    Args:
        user_id: The user identifier from the institution roster

    Returns:
        A unique timeline_id string.
    """
    random_suffix = secrets.token_urlsafe(16)
    return f"tl_{user_id}_{random_suffix}"


def new_activation_token() -> str:
    """Generate a cryptographically random one-time activation token.

    Used in the bootstrap activation link. Expires after use or TTL.
    """
    return secrets.token_urlsafe(24)


def hash_secret_words(words: str | list[str]) -> str:
    """Hash a secret words phrase for storage.

    The raw words are never stored — only a salted hash.
    Args:
        words: Either a string of words (space-separated) or a list of word strings.
    Returns:
        A hex-encoded salted hash of the words.
    """
    if isinstance(words, list):
        words = " ".join(words)
    words = words.strip().lower()
    # Salted hash — uses the words themselves as the salt source for simplicity
    return hashlib.sha256(words.encode("utf-8")).hexdigest() + ":" + words


def verify_secret_words(words: str | list[str], secret_hash: str) -> bool:
    """Verify secret words against a stored hash.

    Args:
        words: The challenge phrase to verify
        secret_hash: The stored hash (hash:plaintext format)

    Returns:
        True if the words match the stored hash.
    """
    if isinstance(words, list):
        words = " ".join(words)
    words = words.strip().lower()
    stored = hashlib.sha256(words.encode("utf-8")).hexdigest()
    return stored == secret_hash.split(":")[0]


# =============================================================================
# BOOTSTRAP RECORD STATE FACTORY
# =============================================================================

def new_pending_bootstrap(
    user_id: str,
    email: str,
    display_name: str,
    institution_id: str | None = None,
    ttl_hours: int = 24,
) -> dict:
    """Create a new pending bootstrap record.

    This record is created when WESLR receives a user from the institution
    roster and before the user completes activation. The record is in
    PENDING status until the user completes the full activation flow.

    Args:
        user_id: The user identifier from the institution roster
        email: The user's institutional email address
        display_name: The user's display name
        institution_id: Optional institution identifier
        ttl_hours: Hours until this pending record expires (default 24)

    Returns:
        A bootstrap record dict.
    """
    now = time.time()
    expires_at = now + (ttl_hours * 3600)
    return {
        "user_id": user_id,
        "email": email,
        "display_name": display_name,
        "institution_id": institution_id or "default",
        "status": "PENDING",  # PENDING | COMPLETED | EXPIRED | REVOKED
        "timeline_id": None,  # assigned on completion
        "activation_token": new_activation_token(),
        "activation_sent_at": now,
        "activation_expires_at": expires_at,
        "secret_words_hash": None,
        "first_trusted_device_id": None,
        "bootstrap_verified_at": None,
        "bootstrap_completed_at": None,
        "revoked_at": None,
        "revoked_reason": None,
    }


def complete_bootstrap(
    bootstrap_record: dict,
    secret_words: str | list[str],
    trusted_device_id: str,
) -> dict:
    """Mark a pending bootstrap record as complete.

    This is called after the user has:
    1. Confirmed their identity via the activation link
    2. Received or confirmed their secret words challenge phrase
    3. Registered their first trusted device

    Args:
        bootstrap_record: The pending bootstrap record to complete
        secret_words: The 3–4 word challenge phrase (will be hashed before storage)
        trusted_device_id: The registered first trusted device identifier

    Returns:
        The completed bootstrap record with timeline_id assigned.
    """
    now = time.time()
    record = dict(bootstrap_record)
    record["status"] = "COMPLETED"
    record["timeline_id"] = new_timeline_id(record["user_id"])
    record["secret_words_hash"] = hash_secret_words(secret_words)
    record["first_trusted_device_id"] = trusted_device_id
    record["bootstrap_verified_at"] = now
    record["bootstrap_completed_at"] = now
    record["activation_token"] = None  # invalidate the one-time token
    # Emit bootstrap transition signal (fail-open)
    try:
        from weslr.drift_emitter import emit_bootstrap_signal
        emit_bootstrap_signal("PENDING", "COMPLETED", str(record.get("user_id", "")))
    except Exception:
        pass
    # Persist timeline_id to communicator_self.json so HTTP-layer checks can read it
    try:
        from sim import load_communicator_self, save_communicator_self
        cs = load_communicator_self()
        cs.setdefault("bootstrap", {})["timeline_id"] = record["timeline_id"]
        cs.setdefault("bootstrap", {})["status"] = "COMPLETED"
        save_communicator_self(cs)
    except Exception:
        pass  # Non-blocking — don't fail bootstrap if persistence fails
    return record


def expire_pending_bootstrap(bootstrap_record: dict, reason: str = "expired") -> dict:
    """Mark a pending bootstrap record as expired.

    Args:
        bootstrap_record: The pending bootstrap record to expire
        reason: Why the record was expired (default "expired")

    Returns:
        The expired bootstrap record.
    """
    record = dict(bootstrap_record)
    record["status"] = "EXPIRED"
    record["revoked_at"] = time.time()
    record["revoked_reason"] = reason
    # Emit bootstrap transition signal (fail-open)
    try:
        from weslr.drift_emitter import emit_bootstrap_signal
        emit_bootstrap_signal("PENDING", "EXPIRED", str(record.get("user_id", "")))
    except Exception:
        pass
    return record


def rotate_bootstrap_secret_words(
    bootstrap_record: dict,
    new_secret_words: str | list[str],
) -> dict:
    """Rotate the secret words for a completed bootstrap record.

    Rotation requires a current trusted-device verification challenge
    to be completed before this function is called. This function
    only performs the rotation record update.

    Args:
        bootstrap_record: A completed bootstrap record
        new_secret_words: The new 3–4 word challenge phrase

    Returns:
        The updated bootstrap record with the new secret hash.
    """
    if bootstrap_record.get("status") != "COMPLETED":
        raise ValueError("Cannot rotate secret words for a non-completed bootstrap record")
    record = dict(bootstrap_record)
    record["secret_words_hash"] = hash_secret_words(new_secret_words)
    return record


# =============================================================================
# BOOTSTRAP STATUS QUERY
# =============================================================================

def get_bootstrap_status(bootstrap_record: dict) -> dict:
    """Return a human-readable bootstrap status summary.

    Args:
        bootstrap_record: A bootstrap record dict

    Returns:
        A status dict with keys: status, timeline_id, bootstrap_verified_at,
        days_until_expiry (for pending records), trusted_device_registered.
    """
    record = bootstrap_record
    status = record.get("status", "UNKNOWN")
    now = time.time()
    result = {
        "status": status,
        "timeline_id": record.get("timeline_id"),
        "bootstrap_verified_at": record.get("bootstrap_verified_at"),
        "trusted_device_registered": record.get("first_trusted_device_id") is not None,
        "email": record.get("email"),
        "display_name": record.get("display_name"),
    }
    if status == "PENDING":
        expires_at = record.get("activation_expires_at", now)
        result["days_until_expiry"] = max(0, (expires_at - now) / 86400)
        result["activation_expires_at"] = expires_at
    return result


def is_user_bootstrap_verified(bootstrap_record: dict) -> bool:
    """Return True if the user has completed bootstrap and is verified.

    Args:
        bootstrap_record: A bootstrap record dict

    Returns:
        True if status is COMPLETED and timeline_id is set.
    """
    return (
        bootstrap_record.get("status") == "COMPLETED"
        and bootstrap_record.get("timeline_id") is not None
    )


def is_activation_token_valid(bootstrap_record: dict) -> bool:
    """Return True if the pending activation token is still valid.

    Args:
        bootstrap_record: A bootstrap record dict

    Returns:
        True if the activation token exists and has not expired.
    """
    if bootstrap_record.get("activation_token") is None:
        return False
    now = time.time()
    expires_at = bootstrap_record.get("activation_expires_at", now)
    return expires_at > now


# =============================================================================
# IN-PROCESS BOOTSTRAP STORE (stub — replace with DB/Redis in production)
# =============================================================================
# Pending and completed bootstrap records are held in memory.
# In production, replace with a persistent store (Postgres, Redis, etc.).

_BOOTSTRAP_RECORDS: dict[str, dict] = {}  # user_id -> bootstrap record


def store_bootstrap_record(user_id: str, record: dict) -> None:
    """Store a bootstrap record by user_id (in-process)."""
    _BOOTSTRAP_RECORDS[user_id] = record


def get_bootstrap_record(user_id: str) -> dict | None:
    """Retrieve a bootstrap record by user_id (in-process)."""
    return _BOOTSTRAP_RECORDS.get(user_id)


def list_pending_bootstraps(institution_id: str | None = None) -> list[dict]:
    """Return all pending bootstrap records, optionally filtered by institution."""
    records = []
    for record in _BOOTSTRAP_RECORDS.values():
        if record.get("status") != "PENDING":
            continue
        if institution_id and record.get("institution_id") != institution_id:
            continue
        records.append(record)
    return records


def list_completed_bootstraps(institution_id: str | None = None) -> list[dict]:
    """Return all completed bootstrap records, optionally filtered by institution."""
    records = []
    for record in _BOOTSTRAP_RECORDS.values():
        if record.get("status") != "COMPLETED":
            continue
        if institution_id and record.get("institution_id") != institution_id:
            continue
        records.append(record)
    return records


def clear_expired_pending_records() -> int:
    """Purge all expired PENDING bootstrap records from the in-process store.

    Returns the number of records purged.
    """
    now = time.time()
    purged = 0
    for user_id, record in list(_BOOTSTRAP_RECORDS.items()):
        if record.get("status") != "PENDING":
            continue
        expires_at = record.get("activation_expires_at", now)
        if expires_at < now:
            record["status"] = "EXPIRED"
            record["revoked_at"] = now
            record["revoked_reason"] = "activation_link_expired"
            # Emit bootstrap transition signal (fail-open)
            try:
                from weslr.drift_emitter import emit_bootstrap_signal
                emit_bootstrap_signal("PENDING", "EXPIRED", str(user_id))
            except Exception:
                pass
            purged += 1
    return purged


# =============================================================================
# COMPLETED TIMELINE STORE (timeline_id -> bootstrap record)
# =============================================================================
# Once bootstrap is completed, the record is also indexed by timeline_id.
# This enables SS-TDE to look up bootstrap trust status by timeline.

_BOOTSTRAP_BY_TIMELINE: dict[str, dict] = {}  # timeline_id -> completed bootstrap record


def register_completed_bootstrap(bootstrap_record: dict) -> str:
    """Register a completed bootstrap record in both user_id and timeline_id stores.

    Called after complete_bootstrap() succeeds to make the record
    lookup-available by timeline_id for SS-TDE enforcement.

    Args:
        bootstrap_record: A completed bootstrap record (from complete_bootstrap)

    Returns:
        The assigned timeline_id.
    """
    timeline_id = bootstrap_record.get("timeline_id")
    if not timeline_id:
        raise ValueError("Cannot register non-completed bootstrap record")
    user_id = bootstrap_record.get("user_id")
    _BOOTSTRAP_RECORDS[user_id] = bootstrap_record
    _BOOTSTRAP_BY_TIMELINE[timeline_id] = bootstrap_record
    return timeline_id


def get_bootstrap_by_timeline(timeline_id: str) -> dict | None:
    """Retrieve a bootstrap record by timeline_id.

    Used by SS-TDE enforcement to check if a timeline has a valid
    bootstrap trust anchor.

    Args:
        timeline_id: The timeline identifier

    Returns:
        The bootstrap record if found, otherwise None.
    """
    return _BOOTSTRAP_BY_TIMELINE.get(timeline_id)


def is_verified_timeline(timeline_id: str) -> bool:
    """Return True if the timeline has a COMPLETED bootstrap trust anchor.

    This is the root trust check: SS-TDE escalation requires a verified
    bootstrap anchor. Without it, the actor cannot proceed to trusted-device
    verification as if they were already trusted.

    Args:
        timeline_id: The timeline identifier to check

    Returns:
        True if the timeline has completed bootstrap; False otherwise.
    """
    record = _BOOTSTRAP_BY_TIMELINE.get(timeline_id)
    if record is None:
        return False
    return record.get("status") == "COMPLETED" and record.get("timeline_id") is not None