"""
WESLR User Signal Intake V1

Public-facing, production-safe user signal intake for Website use.
Captures safe, anonymized interaction signals without storing raw prompts,
PII, or changing behavior.

This module does NOT:
- store raw user messages
- store PII
- modify response behavior
- infer values
- create proposals
- change public prompt
- expose internal doctrine
- use LLM for signal interpretation
- write to production JSONL

Pure functions only — no file writes, no persistence.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Forbidden fields — never allowed in intake events
# ---------------------------------------------------------------------------

_FORBIDDEN_FIELDS: frozenset[str] = frozenset({
    "message",
    "raw_message",
    "prompt",
    "user_input",
    "email",
    "phone",
    "address",
    "ip",
    "user_id",
    "name",
    "location",
})

# ---------------------------------------------------------------------------
# Privacy helpers
# ---------------------------------------------------------------------------

def contains_forbidden_field(event: dict) -> bool:
    """
    Return True if event contains any forbidden field.
    Forbidden fields are those that could carry raw user content or PII.

    Does NOT mutate event.
    """
    for key in event:
        if key in _FORBIDDEN_FIELDS:
            return True
    return False


def detect_pii_like_content(event: dict) -> bool:
    """
    Conservative V1 PII detection on string values.

    Detects:
    - email-like patterns (@)
    - phone-like sequences (7+ consecutive digits)
    - IPv4-like patterns
    - street-like markers

    Returns True if PII-like content is detected in any string value.
    Does NOT mutate event.
    """
    patterns = [
        (re.compile(r"@"), "email-like"),
        (re.compile(r"\b\d{7,}\b"), "phone-like"),
        (re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "IPv4-like"),
        (re.compile(r"\b(street|strasse|straße|road|avenue|blvd)\b", re.I), "street-like"),
    ]

    for key, value in event.items():
        if key in _FORBIDDEN_FIELDS:
            continue
        val_str = str(value)
        for pattern, label in patterns:
            if pattern.search(val_str):
                return True

    return False


# ---------------------------------------------------------------------------
# Signal classification
# ---------------------------------------------------------------------------

def classify_public_signal(event: dict) -> dict:
    """
    Classify a public-facing user interaction event.

    INPUT:
        event — dict with fields:
            session_id_hash: str
            message_length_bucket: "short" | "medium" | "long"
            response_path: str
            fallback_triggered: bool
            evidence_offer_shown: bool
            evidence_offer_accepted: bool
            blocked_write: bool
            topic_normalized: str | None
            timestamp: str (ISO-8601)

    RETURN:
        dict with:
            signal_type: "S1" | "S2" | "S4" | "S5" | null
            safe_to_record: bool
            reason: str
            contains_raw_prompt: bool
            contains_pii: bool

    Priority order:
    1. unsafe raw/PII → safe_to_record false
    2. blocked_write → signal_type null, safe_to_record true
    3. evidence S2
    4. fallback S4
    5. unknown S1
    6. improvement S5
    7. no signal
    """
    # Priority 1: unsafe — forbidden fields
    if contains_forbidden_field(event):
        return {
            "signal_type": None,
            "safe_to_record": False,
            "reason": "forbidden_field_detected",
            "contains_raw_prompt": True,
            "contains_pii": False,
        }

    # Priority 1: unsafe — PII-like content
    if detect_pii_like_content(event):
        return {
            "signal_type": None,
            "safe_to_record": False,
            "reason": "pii_like_content_detected",
            "contains_raw_prompt": False,
            "contains_pii": True,
        }

    # Priority 2: blocked write
    if event.get("blocked_write") is True:
        return {
            "signal_type": None,
            "safe_to_record": True,
            "reason": "blocked_write_observed",
            "contains_raw_prompt": False,
            "contains_pii": False,
        }

    # Priority 3: evidence workspace usage → S2
    if event.get("evidence_offer_accepted") is True:
        return {
            "signal_type": "S2",
            "safe_to_record": True,
            "reason": "evidence_offer_accepted",
            "contains_raw_prompt": False,
            "contains_pii": False,
        }

    if event.get("evidence_offer_shown") is True:
        return {
            "signal_type": "S2",
            "safe_to_record": True,
            "reason": "evidence_offer_shown",
            "contains_raw_prompt": False,
            "contains_pii": False,
        }

    # Priority 4: fallback trigger → S4
    if event.get("fallback_triggered") is True:
        return {
            "signal_type": "S4",
            "safe_to_record": True,
            "reason": "fallback_triggered",
            "contains_raw_prompt": False,
            "contains_pii": False,
        }

    # Priority 5: unknown response path → S1
    response_path = str(event.get("response_path", ""))
    if "unknown" in response_path or "fallback_safe" in response_path:
        return {
            "signal_type": "S1",
            "safe_to_record": True,
            "reason": "unknown_response_path",
            "contains_raw_prompt": False,
            "contains_pii": False,
        }

    # Priority 6: improvement path → S5
    if "improvement" in response_path or "proposal" in response_path:
        return {
            "signal_type": "S5",
            "safe_to_record": True,
            "reason": "improvement_response_path",
            "contains_raw_prompt": False,
            "contains_pii": False,
        }

    # Priority 7: no signal
    return {
        "signal_type": None,
        "safe_to_record": True,
        "reason": "no_signal",
        "contains_raw_prompt": False,
        "contains_pii": False,
    }


# ---------------------------------------------------------------------------
# Safe record builder
# ---------------------------------------------------------------------------

def build_public_signal_record(event: dict) -> dict:
    """
    Build a safe, anonymized public signal record from an intake event.

    INPUT:
        event — dict as described in classify_public_signal()

    RETURN:
        dict:
            record_type: "public_signal_v1"
            session_id_hash: str
            signal_type: "S1" | "S2" | "S4" | "S5" | null
            response_path: str
            topic_normalized: str | null
            timestamp: str
            source: "website_public"
            raw_prompt_stored: false
            pii_stored: false
            behavior_change_allowed: false
            value_inference_allowed: false
            safe_to_record: bool
            reason: str

    OUTPUT WILL NEVER CONTAIN:
        - raw message / prompt / user_input
        - email / phone / address / IP / user_id / exact location

    Pure function — no file writes.
    """
    classification = classify_public_signal(event)

    if not classification["safe_to_record"]:
        return {
            "record_type": "public_signal_v1",
            "session_id_hash": None,
            "signal_type": None,
            "response_path": None,
            "topic_normalized": None,
            "timestamp": None,
            "source": "website_public",
            "raw_prompt_stored": False,
            "pii_stored": False,
            "behavior_change_allowed": False,
            "value_inference_allowed": False,
            "safe_to_record": False,
            "reason": classification["reason"],
        }

    return {
        "record_type": "public_signal_v1",
        "session_id_hash": str(event.get("session_id_hash", "")),
        "signal_type": classification["signal_type"],
        "response_path": str(event.get("response_path", "")),
        "topic_normalized": event.get("topic_normalized") or None,
        "timestamp": str(event.get("timestamp", "")),
        "source": "website_public",
        "raw_prompt_stored": False,
        "pii_stored": False,
        "behavior_change_allowed": False,
        "value_inference_allowed": False,
        "safe_to_record": True,
        "reason": classification["reason"],
    }


# ---------------------------------------------------------------------------
# No-write proof via design
# ---------------------------------------------------------------------------
# All functions in this module are pure — no side effects, no file access.
# The module does not call: open(), json.dump(), write(), or any persist function.
# AST scanning tools can verify: no write calls present in this module.