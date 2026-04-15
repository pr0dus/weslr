# weslr/security.py — SS-TDE + CEA Security Foundation
# Minimum safe foundation: token schema, lifecycle primitives, trust-level scaffold, audit log.
#
# DO NOT yet wire full runtime enforcement into all chat flows.
# DO NOT yet add trusted device UI or camera/voice verification.
# This module provides the foundation; runtime integration is a separate slice.

from __future__ import annotations

import time
import secrets
import enum
from typing import Any


# =============================================================================
# TRUST LEVELS (SS-TDE + CEA scaffold)
# =============================================================================

class TrustLevel(enum.IntEnum):
    """SS-TDE trust levels. Higher levels require more verification."""
    CONVERSATIONAL = 0   # Normal chat, no special verification
    SENSITIVE = 1       # Contextual acknowledgment before acting
    ELEVATED = 2        # Explicit in-session confirmation ("type yes to confirm")
    HIGH_RISK = 3      # Trusted device escalation + challenge/response + time-bounded token
    CRITICAL = 4        # Multi-party verification + audit + cooldown


# =============================================================================
# ACTION RISK CLASSIFICATION (scaffold)
# =============================================================================
# Maps action identifiers to the minimum trust level required.
# This is the risk classifier foundation — expand by subclassing or config.

ACTION_RISK_LEVELS: dict[str, TrustLevel] = {
    # L0 — Conversational (default for chat)
    "chat:message": TrustLevel.CONVERSATIONAL,
    "chat:query": TrustLevel.CONVERSATIONAL,
    "chat:self_report": TrustLevel.CONVERSATIONAL,
    # L1 — Sensitive (contextual acknowledgment)
    "preferences:set": TrustLevel.SENSITIVE,
    "profile:update": TrustLevel.SENSITIVE,
    # L2 — Elevated (explicit in-session confirmation)
    "message:send": TrustLevel.ELEVATED,
    "document:share": TrustLevel.ELEVATED,
    "contact:add": TrustLevel.ELEVATED,
    # L3 — High-Risk (trusted device escalation required)
    "delete:world": TrustLevel.HIGH_RISK,
    "api:external_call": TrustLevel.HIGH_RISK,
    "permission:grant": TrustLevel.HIGH_RISK,
    "external:post": TrustLevel.HIGH_RISK,
    "security:change": TrustLevel.HIGH_RISK,
    # L4 — Critical (multi-party verification required)
    "database:wipe": TrustLevel.CRITICAL,
    "permission:revoke_all": TrustLevel.CRITICAL,
    "unrecoverable:state_change": TrustLevel.CRITICAL,
}


def classify_action(action_id: str) -> TrustLevel:
    """Return the minimum trust level required for a given action.

    Returns CONVERSATIONAL as default for unknown actions.
    Subclass or replace this to build a richer risk classifier.
    """
    return ACTION_RISK_LEVELS.get(action_id, TrustLevel.CONVERSATIONAL)


# =============================================================================
# CLEARANCE TOKEN SCHEMA
# =============================================================================

def _generate_token_id() -> str:
    """Generate a cryptographically random token ID."""
    return secrets.token_urlsafe(24)


def new_clearance_token(
    actor_id: str,
    session_id: str,
    action_scope: str | list[str],
    trust_level: TrustLevel,
    ttl_seconds: int = 60,
) -> dict:
    """Create a new clearance token.

    Args:
        actor_id: Who requested the token
        session_id: Which session this token belongs to
        action_scope: The action or list of actions this token authorizes
        trust_level: The clearance level this token grants
        ttl_seconds: Time-to-live in seconds (default 60)

    Returns:
        A clearance token dict
    """
    now = time.time()
    return {
        "token_id": _generate_token_id(),
        "actor_id": actor_id,
        "session_id": session_id,
        "action_scope": action_scope if isinstance(action_scope, list) else [action_scope],
        "trust_level": int(trust_level),
        "granted_at": now,
        "expires_at": now + ttl_seconds,
        "used_at": None,
        "revoked": False,
        "revoked_at": None,
    }


# =============================================================================
# TOKEN STORE (in-process, session-scoped)
# =============================================================================
# Tokens are held in memory only. They are NOT persisted to disk.
# All tokens for a session are revoked when the session closes.

_TOKEN_STORE: dict[str, dict] = {}  # token_id -> token dict
_TOKEN_BY_SESSION: dict[str, set[str]] = {}  # session_id -> set of token_ids


def issue_clearance_token(
    actor_id: str,
    session_id: str,
    action_scope: str | list[str],
    trust_level: TrustLevel,
    ttl_seconds: int = 60,
) -> dict:
    """Issue a new clearance token and store it in the in-process token store.

    Args:
        actor_id: Who is requesting elevation
        session_id: The session this token belongs to
        action_scope: Action or list of actions authorized by this token
        trust_level: Minimum trust level required (must match or exceed action requirement)
        ttl_seconds: Time-to-live in seconds

    Returns:
        The newly created token dict (includes token_id)
    """
    token = new_clearance_token(actor_id, session_id, action_scope, trust_level, ttl_seconds)
    _TOKEN_STORE[token["token_id"]] = token
    _TOKEN_BY_SESSION.setdefault(session_id, set()).add(token["token_id"])
    return token


def validate_clearance_token(token_id: str, action_scope: str) -> tuple[bool, str]:
    """Validate a clearance token for a given action.

    Args:
        token_id: The token ID to validate
        action_scope: The action being attempted

    Returns:
        (is_valid, reason) — is_valid is True if the token is present, not expired,
        not revoked, and action_scope is within the token's authorized scope.
    """
    token = _TOKEN_STORE.get(token_id)
    if token is None:
        return False, "token_not_found"
    if token.get("revoked"):
        return False, "token_revoked"
    now = time.time()
    if now > token["expires_at"]:
        return False, "token_expired"
    # One-time use: already used
    if token.get("used_at") is not None:
        return False, "token_already_used"
    # Check action is in scope
    allowed = token.get("action_scope", [])
    if action_scope not in allowed:
        return False, "action_not_in_scope"
    return True, "valid"


def use_clearance_token(token_id: str) -> None:
    """Mark a one-time token as used after successful execution.

    For one-time-use tokens, this is called immediately after successful execution.
    Short-window tokens are invalidated on expiry instead.
    """
    if token_id in _TOKEN_STORE:
        _TOKEN_STORE[token_id]["used_at"] = time.time()


def revoke_clearance_token(token_id: str, revoked_by: str | None = None) -> bool:
    """Revoke a clearance token immediately.

    Args:
        token_id: The token to revoke
        revoked_by: Who or what initiated the revocation (actor_id or "operator")

    Returns:
        True if the token was found and revoked; False if not found.
    """
    token = _TOKEN_STORE.get(token_id)
    if token is None:
        return False
    token["revoked"] = True
    token["revoked_at"] = time.time()
    token["revoked_by"] = revoked_by
    return True


def revoke_all_session_tokens(session_id: str, revoked_by: str | None = None) -> int:
    """Revoke all active tokens for a given session.

    Called automatically when a session closes.

    Args:
        session_id: The session whose tokens should be revoked
        revoked_by: Who or what initiated the revocation

    Returns:
        The number of tokens revoked.
    """
    token_ids = _TOKEN_BY_SESSION.pop(session_id, set())
    count = 0
    for tid in token_ids:
        if revoke_clearance_token(tid, revoked_by):
            count += 1
    return count


def get_active_tokens(session_id: str) -> list[dict]:
    """Return all active (non-expired, non-revoked, non-used) tokens for a session."""
    now = time.time()
    token_ids = _TOKEN_BY_SESSION.get(session_id, set())
    active = []
    for tid in token_ids:
        token = _TOKEN_STORE.get(tid)
        if not token:
            continue
        if token.get("revoked"):
            continue
        if token["expires_at"] < now:
            continue
        if token.get("used_at") is not None:
            continue
        active.append(token)
    return active


def clear_expired_tokens() -> int:
    """Purge expired, revoked, and used tokens from the in-process store.

    Returns the number of tokens purged.
    """
    now = time.time()
    purged = 0
    expired_ids = [
        tid for tid, t in _TOKEN_STORE.items()
        if t.get("revoked") or t["expires_at"] < now or t.get("used_at") is not None
    ]
    for tid in expired_ids:
        _TOKEN_STORE.pop(tid, None)
        purged += 1
    # Clean session mappings for expired tokens
    for sid in list(_TOKEN_BY_SESSION.keys()):
        _TOKEN_BY_SESSION[sid] = {
            tid for tid in _TOKEN_BY_SESSION[sid]
            if tid in _TOKEN_STORE
        }
        if not _TOKEN_BY_SESSION[sid]:
            _TOKEN_BY_SESSION.pop(sid, None)
    return purged


# =============================================================================
# AUDIT EVENT SCHEMA (append-only, in-process ring buffer + export hook)
# =============================================================================

# In-process audit ring buffer — holds recent audit events in memory.
# Operators can export or persisted to long-term storage via a configured hook.
_MAX_AUDIT_RING = 1000
_AUDIT_RING: list[dict] = []


def log_audit_event(
    event_kind: str,
    actor_id: str,
    session_id: str,
    action_requested: str,
    trust_level_required: TrustLevel,
    verification_method: str,
    outcome: str,
    token_id: str | None = None,
    details: dict | None = None,
    operator_alert: bool = False,
) -> dict:
    """Record an audit event for a clearance elevation attempt or action.

    Args:
        event_kind: Event type identifier (e.g., "clearance_request", "clearance_granted", "clearance_denied", "token_revoked", "token_expired")
        actor_id: Who initiated the action
        session_id: Which session this occurred in
        action_requested: The specific action being attempted or authorized
        trust_level_required: The trust level required for the action
        verification_method: How verification was performed ("trusted_device", "operator_confirmation", "in_session_confirmation", "none")
        outcome: The outcome ("granted", "denied", "revoked", "expired", "failed", "used")
        token_id: The issued token ID if one was granted
        details: Optional additional context
        operator_alert: Whether this event triggered an operator alert

    Returns:
        The audit event dict (also stored in the in-process ring buffer).
    """
    now = time.time()
    event = {
        "event_id": _generate_token_id(),  # monotonic unique ID
        "event_kind": event_kind,
        "actor_id": actor_id,
        "session_id": session_id,
        "action_requested": action_requested,
        "trust_level_required": int(trust_level_required),
        "verification_method": verification_method,
        "outcome": outcome,
        "token_id": token_id,
        "granted_at": now,
        "expires_at": None,
        "used_at": None,
        "details": details or {},
        "operator_alert": operator_alert,
    }
    _AUDIT_RING.append(event)
    if len(_AUDIT_RING) > _MAX_AUDIT_RING:
        _AUDIT_RING.pop(0)
    return event


def get_recent_audit_events(limit: int = 100, session_id: str | None = None) -> list[dict]:
    """Return the most recent audit events, optionally filtered by session."""
    events = _AUDIT_RING[-limit:]
    if session_id:
        events = [e for e in events if e.get("session_id") == session_id]
    return events


def get_audit_events_by_outcome(outcome: str, limit: int = 100) -> list[dict]:
    """Return audit events with a specific outcome."""
    all_events = [e for e in _AUDIT_RING if e.get("outcome") == outcome]
    return all_events[-limit:]


def count_failed_attempts(session_id: str, action_scope: str | None = None) -> int:
    """Count consecutive failed attempts for a session and optionally an action."""
    events = get_recent_audit_events(limit=50, session_id=session_id)
    failures = [
        e for e in events
        if e.get("outcome") in ("denied", "failed") and e.get("action_requested") == action_scope
    ]
    return len(failures)


# =============================================================================
# SS-TDE RISK CLASSIFIER (for natural-language chat input)
# =============================================================================
# Maps message content patterns to the minimum trust level required.
# This is the enforcement hook for the /api/chat risk scan in main.py.

_RISK_PATTERNS: list[tuple[TrustLevel, list[str]]] = [
    # L4 Critical — most dangerous first
    (TrustLevel.CRITICAL, [
        "wipe the database", "wipe all data", "delete everything permanently",
        "revoke all permissions", "revoke everyone's access",
        "destroy the world", "unrecoverable",
        "factory reset all", "reset all permissions",
    ]),
    # L3 High-Risk
    (TrustLevel.HIGH_RISK, [
        "delete the world", "delete my world", "delete all messages",
        "post this publicly", "post to twitter", "post to facebook", "post externally",
        "make an api call", "call the api", "send an external request",
        "change my security", "change security settings", "change password",
        "grant admin", "grant full access", "give me admin",
        "revoke access", "revoke permissions",
        "send this message to", "send this to someone",
        "export all data", "download all my data",
        "access log", "access logs", "show me the audit log",
        "delete my account", "delete account",
    ]),
    # L2 Elevated
    (TrustLevel.ELEVATED, [
        "send a message", "send this message", "share with",
        "share this with", "add a contact", "add contact",
        "post to", "post publicly",
        "change my preference", "change preference",
        "send an email", "send email",
    ]),
    # L1 Sensitive
    (TrustLevel.SENSITIVE, [
        "remember this", "save this", "note this",
        "change your name", "update my profile", "update profile",
        "remember me as",
    ]),
]


def classify_message_for_risk(message: str) -> TrustLevel:
    """Scan message text and return the minimum trust level required.

    Checks from highest risk to lowest, returns the first match.
    Returns CONVERSATIONAL if no dangerous patterns are detected.
    """
    msg_lower = message.lower()
    for level, patterns in _RISK_PATTERNS:
        for pattern in patterns:
            if pattern in msg_lower:
                return level
    return TrustLevel.CONVERSATIONAL


def escalation_response(action_level: TrustLevel) -> dict:
    """Return a structured escalation-required response for L3/L4 requests.

    This is the stub response returned by /chat instead of executing
    a high-risk action inline.
    """
    level_names = {
        TrustLevel.HIGH_RISK: "HIGH_RISK",
        TrustLevel.CRITICAL: "CRITICAL",
    }
    messages = {
        TrustLevel.HIGH_RISK: (
            "I can't complete that request here. It requires a higher level of "
            "verification. Please confirm your identity on a trusted device to proceed."
        ),
        TrustLevel.CRITICAL: (
            "This action requires multi-party verification and operator oversight. "
            "I will alert an operator and await their confirmation before proceeding."
        ),
    }
    return {
        "escalation_required": True,
        "trust_level": level_names.get(action_level, str(action_level)),
        "message": messages.get(action_level, "Verification required."),
        "action": "trusted_device_escalation",
    }


def build_escalation_handoff(
    message: str,
    risk_level: TrustLevel,
    actor_id: str = "anonymous",
    session_id: str = "unknown",
) -> dict:
    """Build a structured escalation handoff object for L3/L4 actions.

    This is the trusted-device escalation stub: a structured object containing
    everything needed to initiate and verify a trusted-device verification flow.
    It is returned alongside the escalation_required response for L3/L4 requests.

    Args:
        message: The original human message that triggered the escalation
        risk_level: The trust level required for the action
        actor_id: Who made the request (actor identifier)
        session_id: Which session the request occurred in

    Returns:
        A structured handoff dict with keys:
        - handoff_id: unique escalation request ID
        - action_requested: truncated original message (max 200 chars)
        - risk_level: "HIGH_RISK" or "CRITICAL"
        - actor_id / session_id: who and where
        - verification_required: human-readable description of what's needed
        - ttl_seconds: time-to-live for the handoff (5 min for L3, 2 min for L4)
        - audit_event_id: links to the audit log entry
        - status: "awaiting_verification"
    """
    import time as _time
    handoff_id = _generate_token_id()
    now = _time.time()
    ttl = 300 if risk_level == TrustLevel.HIGH_RISK else 120
    expires_at = now + ttl
    level_name = "HIGH_RISK" if risk_level == TrustLevel.HIGH_RISK else "CRITICAL"
    verification_required = (
        "Trusted device challenge/response required. "
        "Confirm your identity on a registered device to proceed."
    ) if risk_level == TrustLevel.HIGH_RISK else (
        "Multi-party operator verification required. "
        "Await operator confirmation before proceeding."
    )
    # Log the escalation event and link it to the handoff
    evt = log_audit_event(
        event_kind="escalation_handoff_created",
        actor_id=actor_id,
        session_id=session_id,
        action_requested=message[:200],
        trust_level_required=risk_level,
        verification_method="trusted_device" if risk_level == TrustLevel.HIGH_RISK else "operator_multi_party",
        outcome="pending",
        operator_alert=(risk_level >= TrustLevel.CRITICAL),
        details={"handoff_id": handoff_id},
    )
    return {
        "handoff_id": handoff_id,
        "action_requested": message[:200],
        "risk_level": level_name,
        "actor_id": actor_id,
        "session_id": session_id,
        "verification_required": verification_required,
        "ttl_seconds": ttl,
        "expires_at": expires_at,
        "audit_event_id": evt["event_id"],
        "status": "awaiting_verification",
    }


def count_failed_attempts(session_id: str, action_scope: str | None = None) -> int:
    """Count consecutive failed attempts for a session and optionally an action."""
    events = get_recent_audit_events(limit=50, session_id=session_id)
    failures = [
        e for e in events
        if e.get("outcome") in ("denied", "failed") and e.get("action_requested") == action_scope
    ]
    return len(failures)