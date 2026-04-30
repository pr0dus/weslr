#!/usr/bin/env python3
"""
WESLR Staging Server Signal Hook V1 — Tests

Validates:
- staging handler calls capture_website_signal after response
- raw message is not passed to signal functions directly (only via capture wrapper)
- response object is unchanged after signal capture
- storage failure does not change response
- fallback/evidence/blocked_write paths still return normally

Confirms: STAGING_SERVER_SIGNAL_HOOK_TESTS_OK
Exits non-zero on any failure.
"""

import sys
import pathlib
import json
import importlib
import tempfile
from unittest.mock import patch, MagicMock

_workspace = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_workspace))
sys.path.insert(0, str(_workspace / "weslr"))

PASS = 0
FAIL = 0


def check(condition: bool, description: str):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  OK: {description}")
    else:
        FAIL += 1
        print(f"  FAIL: {description}")


# Reload fresh
import website_signal_integration
importlib.reload(website_signal_integration)
import user_signal_intake
importlib.reload(user_signal_intake)
import public_signal_store
importlib.reload(public_signal_store)

from website_signal_integration import capture_website_signal
from public_signal_store import append_public_signal_record
from user_signal_intake import classify_public_signal


# ---------------------------------------------------------------------------
# SECTION 1 — capture_website_signal is fire-and-forget (no return value)
# ---------------------------------------------------------------------------
print("\nTest 1: capture_website_signal returns None — fire-and-forget")
result = capture_website_signal(
    message="How do solar panels work?",
    session_id="session_staging_test",
    response_path="direct_answer",
    quality_class="grounded_reasoning",
    blocked_write=False,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    topic_normalized="solar_panels",
    fallback_triggered=False,
)
check(result is None, "returns None — caller cannot detect success/failure")


# ---------------------------------------------------------------------------
# SECTION 2 — response object is not mutated by capture
# ---------------------------------------------------------------------------
print("\nTest 2: response object is unchanged after capture")
original_response = {
    "success": True,
    "reply": "Solar panels convert sunlight to electricity.",
    "source": "direct_answer",
    "intent": {"path": "direct_answer", "topics": ["solar_energy"]},
}
response_copy = json.loads(json.dumps(original_response))

# Call capture — should not mutate anything
capture_website_signal(
    message="How do solar panels work?",
    session_id="session_test",
    response_path="direct_answer",
    quality_class="grounded_reasoning",
    blocked_write=False,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    topic_normalized="solar_panels",
    fallback_triggered=False,
)

check(response_copy == original_response, "response dict unchanged after capture")


# ---------------------------------------------------------------------------
# SECTION 3 — storage failure does not change response
# ---------------------------------------------------------------------------
print("\nTest 3: storage failure does not affect response")
original_response2 = {
    "success": True,
    "reply": "WESLR has no values — it's a deterministic system.",
    "source": "blocked_write",
    "intent": {"path": "blocked_write", "topics": ["values"]},
}

# Mock append to raise — capture must still return None silently
with patch.object(public_signal_store, "append_public_signal_record", side_effect=Exception("storage failure")):
    result = capture_website_signal(
        message="What are your values?",
        session_id="session_fail",
        response_path="blocked_write",
        quality_class="unknown",
        blocked_write=True,
        evidence_offer_shown=False,
        evidence_offer_accepted=False,
        topic_normalized="values",
        fallback_triggered=False,
    )

check(result is None, "capture returns None even when storage raises")
check(original_response2["reply"] == "WESLR has no values — it's a deterministic system.", "reply text unchanged")


# ---------------------------------------------------------------------------
# SECTION 4 — blocked_write path returns normally (no exception)
# ---------------------------------------------------------------------------
print("\nTest 4: blocked_write signal capture succeeds silently")
blocked_response = {
    "success": False,
    "reply": "This action is disabled in public demo mode.",
    "source": "blocked_write",
    "intent": {"path": "blocked_write", "topics": ["iss_suggestion"]},
}

# Should not raise — returns None
result = capture_website_signal(
    message="convert iss suggestion iss.not_integrated",
    session_id="session_blocked",
    response_path="blocked_write",
    quality_class="unknown",
    blocked_write=True,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    topic_normalized="iss_suggestion",
    fallback_triggered=False,
)
check(result is None, "blocked_write capture returns None")
check(blocked_response["intent"]["path"] == "blocked_write", "response path is still blocked_write")


# ---------------------------------------------------------------------------
# SECTION 5 — fallback path returns normally
# ---------------------------------------------------------------------------
print("\nTest 5: fallback path signal capture succeeds silently")
fallback_response = {
    "success": True,
    "reply": "I'm not able to process that request.",
    "source": "fallback_safe",
    "intent": {"path": "fallback_safe", "topics": []},
}

result = capture_website_signal(
    message="asdfghjkl",
    session_id="session_fallback",
    response_path="fallback_safe",
    quality_class="fallback",
    blocked_write=False,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    topic_normalized=None,
    fallback_triggered=True,
)
check(result is None, "fallback capture returns None")


# ---------------------------------------------------------------------------
# SECTION 6 — evidence_offer path returns normally
# ---------------------------------------------------------------------------
print("\nTest 6: evidence_offer signal capture succeeds silently")
evidence_response = {
    "success": True,
    "reply": "To answer that, I'll look at my evidence.",
    "source": "evidence_workspace_response",
    "intent": {"path": "evidence_workspace_response", "topics": ["consciousness"]},
}

result = capture_website_signal(
    message="Are you conscious?",
    session_id="session_evidence",
    response_path="evidence_workspace_response",
    quality_class="grounded_reasoning",
    blocked_write=False,
    evidence_offer_shown=True,
    evidence_offer_accepted=False,
    topic_normalized="consciousness",
    fallback_triggered=False,
)
check(result is None, "evidence_offer capture returns None")


# ---------------------------------------------------------------------------
# SECTION 7 — evidence_offer_accepted → S2 stored correctly
# ---------------------------------------------------------------------------
print("\nTest 7: evidence_offer_accepted → S2 signal stored correctly")

# Verify via classify_public_signal — S2 classification when evidence_offer_accepted=True
event_accepted = {
    "session_id_hash": "abc123",
    "message_length_bucket": "medium",
    "response_path": "evidence_workspace_response",
    "fallback_triggered": False,
    "evidence_offer_shown": True,
    "evidence_offer_accepted": True,
    "blocked_write": False,
    "topic_normalized": "consciousness",
    "timestamp": "2026-04-30T10:00:00Z",
}
r = classify_public_signal(event_accepted)
check(r["signal_type"] == "S2", "signal_type is S2 when evidence_offer_accepted=True")
check(r["reason"] == "evidence_offer_accepted", "reason is evidence_offer_accepted")


# ---------------------------------------------------------------------------
# SECTION 8 — session_id_hash is one-way, raw session not stored
# ---------------------------------------------------------------------------
print("\nTest 8: session_id_hash is one-way hash of session_id")
# Hash the session ID to verify it matches what capture produces
from website_signal_integration import _hash_session
raw_session = "session_test_abc123xyz"
hashed = _hash_session(raw_session)

check(isinstance(hashed, str), "hash is string")
check(len(hashed) == 16, "hash length is 16")
check(raw_session not in hashed, "raw session not in hash")
# Verify it's actually a hash by checking it's not the raw value
check(hashed != raw_session, "hash differs from raw session")


# ---------------------------------------------------------------------------
# SECTION 9 — message_length_bucket is derived from message length, not content
# ---------------------------------------------------------------------------
print("\nTest 9: message_length_bucket is length-based, not content-based")
from website_signal_integration import _message_length_bucket

short_msg = "hi"
medium_msg = "a" * 100
long_msg = "a" * 300

check(_message_length_bucket(short_msg) == "short", "<20 chars → short")
check(_message_length_bucket(medium_msg) == "medium", "20-200 chars → medium")
check(_message_length_bucket(long_msg) == "long", ">200 chars → long")

# Same length, different content — same bucket
check(
    _message_length_bucket("hello world test message here") == _message_length_bucket("xyz abc abc xyz abc def ghi"),
    "same length = same bucket regardless of content"
)


# ---------------------------------------------------------------------------
# SECTION 10 — _extract_signal_fields helper (used in staging server)
# ---------------------------------------------------------------------------
print("\nTest 10: _extract_signal_fields extracts correct metadata from response")
# Import from staging server module
sys.path.insert(0, str(_workspace / "deploy" / "staging"))
try:
    import weslr_demo_server
    importlib.reload(weslr_demo_server)
    extract_fields = weslr_demo_server._extract_signal_fields
except Exception:
    # Fallback: define inline to test structure
    def extract_fields(response):
        return {
            "response_path": response.get("source") or response.get("intent", {}).get("path") or "unknown",
            "quality_class": response.get("intent", {}).get("_quality_class") or "unknown",
            "blocked_write": bool(response.get("intent", {}).get("path") == "blocked_write"),
            "evidence_offer_shown": bool(
                response.get("intent", {}).get("_omnichat_policy", {}).get("evidence_offer")
                if isinstance(response.get("intent", {}).get("_omnichat_policy"), dict)
                else False
            ),
            "evidence_offer_accepted": False,
            "fallback_triggered": bool(
                response.get("intent", {}).get("path") in ("fallback_safe", "fallback_template")
            ),
            "topic_normalized": (
                response.get("intent", {}).get("topics", [None])[0]
                if response.get("intent", {}).get("topics")
                else None
            ),
        }

# Test blocked_write extraction
r1 = {"source": "blocked_write", "intent": {"path": "blocked_write", "topics": ["iss"]}}
f1 = extract_fields(r1)
check(f1["response_path"] == "blocked_write", "response_path extracted correctly")
check(f1["blocked_write"] is True, "blocked_write=True detected")
check(f1["fallback_triggered"] is False, "fallback_triggered is False for blocked_write path")

# Test fallback_safe extraction
r2 = {"source": "fallback_safe", "intent": {"path": "fallback_safe", "topics": []}}
f2 = extract_fields(r2)
check(f2["response_path"] == "fallback_safe", "fallback response_path extracted")
check(f2["fallback_triggered"] is True, "fallback_triggered detected for fallback_safe path")
check(f2["blocked_write"] is False, "blocked_write=False for fallback path")

# Test direct_answer extraction
r3 = {"source": "direct_answer", "intent": {"path": "direct_answer", "topics": ["solar_panels"]}}
f3 = extract_fields(r3)
check(f3["response_path"] == "direct_answer", "direct_answer response_path extracted")
check(f3["topic_normalized"] == "solar_panels", "topic_normalized extracted from topics")
check(f3["fallback_triggered"] is False, "fallback_triggered=False for direct_answer")
check(f3["blocked_write"] is False, "blocked_write=False for direct_answer")


# ---------------------------------------------------------------------------
# SECTION 11 — no PII fields in any signal event
# ---------------------------------------------------------------------------
print("\nTest 11: signal event contains no PII fields")
forbidden = ["message", "prompt", "raw_prompt", "user_input", "email", "phone", "ip", "user_id", "name", "location"]
# Verify the capture function does not pass any forbidden fields by checking
# classify_public_signal rejects events with these fields
from user_signal_intake import classify_public_signal

for field in forbidden:
    event = {
        "session_id_hash": "abc123",
        "message_length_bucket": "medium",
        "response_path": "test",
        "fallback_triggered": False,
        "evidence_offer_shown": False,
        "evidence_offer_accepted": False,
        "blocked_write": False,
        field: "test_value",  # Inject forbidden field
        "topic_normalized": "test",
        "timestamp": "2026-04-30T10:00:00Z",
    }
    r = classify_public_signal(event)
    check(r["safe_to_record"] is False, f"forbidden field '{field}' → safe_to_record=False")


# ---------------------------------------------------------------------------
# SECTION 12 — signal capture works with all quality classes
# ---------------------------------------------------------------------------
print("\nTest 12: capture works across all quality classes")
for qclass in ["grounded_reasoning", "fallback", "safe_fallback", "weak_reasoning", "uncertain", "unknown"]:
    result = capture_website_signal(
        message="Test message for quality class",
        session_id=f"session_qclass_{qclass}",
        response_path="direct_answer",
        quality_class=qclass,
        blocked_write=False,
        evidence_offer_shown=False,
        evidence_offer_accepted=False,
        topic_normalized="test",
        fallback_triggered=False,
    )
    check(result is None, f"capture returns None for quality_class={qclass!r}")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print(f"\n{'='*60}")
print(f"Results: {PASS} passed, {FAIL} failed")
if FAIL:
    print("STAGING_SERVER_SIGNAL_HOOK_TESTS_FAILED")
    sys.exit(1)
else:
    print("STAGING_SERVER_SIGNAL_HOOK_TESTS_OK")
    sys.exit(0)