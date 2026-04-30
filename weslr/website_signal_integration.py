"""
WESLR Website Signal Integration V1

Captures anonymized public interaction signals from /chat responses.
Attaches to the response pipeline without modifying behavior.
Uses only response metadata — never raw message content.

Rules:
- return original response unchanged
- no raw prompt storage
- no PII
- no behavior change
- ignore storage failures
- no value inference
- no proposals
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Optional


def _hash_session(session_id: str) -> str:
    """One-way hash of session ID. No cross-reference possible."""
    return hashlib.sha256(session_id.encode()).hexdigest()[:16]


def _message_length_bucket(message: str) -> str:
    """Bucket raw message length, not content."""
    length = len(message)
    if length < 20:
        return "short"
    elif length < 200:
        return "medium"
    return "long"


def capture_website_signal(
    message: str,
    session_id: str,
    response_path: Optional[str],
    quality_class: Optional[str],
    blocked_write: bool,
    evidence_offer_shown: bool,
    evidence_offer_accepted: bool,
    topic_normalized: Optional[str],
    fallback_triggered: bool,
) -> None:
    """
    Build safe event from /chat response metadata and append via pipeline.
    
    Called after response is built — zero impact on the response itself.
    Failures are silent and不影响 the caller.
    """
    try:
        from weslr.user_signal_intake import (
            classify_public_signal,
            build_public_signal_record,
        )
        from weslr.public_signal_store import append_public_signal_record
    except Exception:
        return

    try:
        event = {
            "session_id_hash": _hash_session(session_id),
            "message_length_bucket": _message_length_bucket(message),
            "response_path": response_path or "unknown",
            "fallback_triggered": fallback_triggered,
            "evidence_offer_shown": evidence_offer_shown,
            "evidence_offer_accepted": evidence_offer_accepted,
            "blocked_write": blocked_write,
            "topic_normalized": topic_normalized,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception:
        return

    try:
        classification = classify_public_signal(event)
        record = build_public_signal_record(event)
        append_public_signal_record(record)
    except Exception:
        return