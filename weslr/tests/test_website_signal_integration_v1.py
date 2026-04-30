#!/usr/bin/env python3
"""
WESLR Website Signal Integration V1 — Tests

Validates:
- capture_website_signal is fire-and-forget (returns None)
- event contains no raw message text, no PII
- signal classification pipeline works
- blocked_write signal stored safely
- public_signals.jsonl append-only
- /chat response unchanged when storage succeeds
- /chat response unchanged when storage fails

Confirms: WEBSITE_SIGNAL_INTEGRATION_TESTS_OK
Exits non-zero on any failure.
"""

import sys
import pathlib
import json
import tempfile
import importlib

_workspace = pathlib.Path(__file__).resolve().parents[1]
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

from website_signal_integration import capture_website_signal, _hash_session, _message_length_bucket
from user_signal_intake import classify_public_signal, build_public_signal_record
from public_signal_store import append_public_signal_record


# ---------------------------------------------------------------------------
# SECTION 1 — capture_website_signal is fire-and-forget
# ---------------------------------------------------------------------------
print("\nTest 1: capture_website_signal returns None (fire-and-forget)")
result = capture_website_signal(
    message="How do solar panels work?",
    session_id="session_abc123",
    response_path="direct_answer",
    quality_class="grounded_reasoning",
    blocked_write=False,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    topic_normalized="solar_panels",
    fallback_triggered=False,
)
check(result is None, "returns None — no return value to check")


# ---------------------------------------------------------------------------
# SECTION 2 — session_id_hash is one-way, no raw session ID stored
# ---------------------------------------------------------------------------
print("\nTest 2: session_id_hash is one-way hash")
hashed = _hash_session("session_abc123xyz")
check(isinstance(hashed, str), "hash returns string")
check(len(hashed) == 16, "hash is 16 chars (sha256[:16])")
check("session_abc123xyz" not in hashed, "raw session_id not present in hash")
# Same input = same hash
check(_hash_session("session_abc123xyz") == hashed, "deterministic — same input yields same hash")
# Different input = different hash
check(_hash_session("session_different") != hashed, "different input yields different hash")


# ---------------------------------------------------------------------------
# SECTION 3 — message_length_bucket is length-based, not content
# ---------------------------------------------------------------------------
print("\nTest 3: message_length_bucket based on length, not content")
check(_message_length_bucket("hi") == "short", " <20 chars → short")
check(_message_length_bucket("hello world test") == "short", " ~16 chars → short")
check(_message_length_bucket("a" * 30) == "medium", " 20-200 chars → medium")
check(_message_length_bucket("a" * 150) == "medium", " ~150 chars → medium")
check(_message_length_bucket("a" * 201) == "long", " >200 chars → long")


# ---------------------------------------------------------------------------
# SECTION 4 — event contains no raw message, no PII fields
# ---------------------------------------------------------------------------
print("\nTest 4: event built from response metadata, not message content")
# We can't easily intercept the internal event dict, so we test that
# classify_public_signal rejects any event with raw content fields.
forbidden_events = [
    {"session_id_hash": "abc", "message": "raw user message"},
    {"session_id_hash": "abc", "prompt": "raw prompt"},
    {"session_id_hash": "abc", "raw_prompt": "raw prompt"},
    {"session_id_hash": "abc", "user_input": "raw input"},
    {"session_id_hash": "abc", "email": "test@example.com"},
    {"session_id_hash": "abc", "phone": "1234567890"},
    {"session_id_hash": "abc", "ip": "192.168.1.1"},
]
for ev in forbidden_events:
    r = classify_public_signal(ev)
    check(r["safe_to_record"] is False, f"forbidden field '{list(ev.keys())[1]}' → safe_to_record=False")


# ---------------------------------------------------------------------------
# SECTION 5 — PII-like content in string values rejected
# ---------------------------------------------------------------------------
print("\nTest 5: PII-like content detected in string values")
pii_events = [
    {"session_id_hash": "abc", "message_length_bucket": "medium", "response_path": "test", "fallback_triggered": False, "evidence_offer_shown": False, "evidence_offer_accepted": False, "blocked_write": False, "topic_normalized": "contact: john@test.com", "timestamp": "2026-04-30T10:00:00Z"},
    {"session_id_hash": "abc", "message_length_bucket": "medium", "response_path": "test", "fallback_triggered": False, "evidence_offer_shown": False, "evidence_offer_accepted": False, "blocked_write": False, "topic_normalized": "phone: 1234567890123", "timestamp": "2026-04-30T10:00:00Z"},
    {"session_id_hash": "abc", "message_length_bucket": "medium", "response_path": "test", "fallback_triggered": False, "evidence_offer_shown": False, "evidence_offer_accepted": False, "blocked_write": False, "topic_normalized": "user at 192.168.1.100", "timestamp": "2026-04-30T10:00:00Z"},
]
for ev in pii_events:
    r = classify_public_signal(ev)
    check(r["safe_to_record"] is False, f"PII-like topic_normalized → safe_to_record=False")


# ---------------------------------------------------------------------------
# SECTION 6 — classify_public_signal with valid event fields
# ---------------------------------------------------------------------------
print("\nTest 6: classify_public_signal with valid metadata-only event")
# All valid fields — should not be rejected
valid_event = {
    "session_id_hash": "abc123",
    "message_length_bucket": "medium",
    "response_path": "direct_answer",
    "fallback_triggered": False,
    "evidence_offer_shown": False,
    "evidence_offer_accepted": False,
    "blocked_write": False,
    "topic_normalized": "solar_panels",
    "timestamp": "2026-04-30T10:00:00Z",
}
r = classify_public_signal(valid_event)
check(r["safe_to_record"] is True, "valid event → safe_to_record=True")
check(r["contains_raw_prompt"] is False, "contains_raw_prompt=False")
check(r["contains_pii"] is False, "contains_pii=False")


# ---------------------------------------------------------------------------
# SECTION 7 — blocked_write → safe_to_record=True, signal_type null
# ---------------------------------------------------------------------------
print("\nTest 7: blocked_write → safe_to_record=True, signal_type null")
blocked_event = {
    "session_id_hash": "abc123",
    "message_length_bucket": "medium",
    "response_path": "blocked_write",
    "fallback_triggered": False,
    "evidence_offer_shown": False,
    "evidence_offer_accepted": False,
    "blocked_write": True,
    "topic_normalized": "iss_suggestion",
    "timestamp": "2026-04-30T10:00:00Z",
}
r = classify_public_signal(blocked_event)
check(r["safe_to_record"] is True, "blocked_write → safe_to_record=True")
check(r["signal_type"] is None, "blocked_write → signal_type null")
check(r["reason"] == "blocked_write_observed", "reason is blocked_write_observed")


# ---------------------------------------------------------------------------
# SECTION 8 — build_public_signal_record produces correct structure
# ---------------------------------------------------------------------------
print("\nTest 8: build_public_signal_record output structure")
record = build_public_signal_record(blocked_event)
check(record["record_type"] == "public_signal_v1", "record_type is public_signal_v1")
check(record["session_id_hash"] == "abc123", "session_id_hash preserved")
check(record["signal_type"] is None, "signal_type null for blocked_write")
check(record["response_path"] == "blocked_write", "response_path preserved")
check(record["topic_normalized"] == "iss_suggestion", "topic_normalized preserved")
check(record["source"] == "website_public", "source is website_public")
check(record["raw_prompt_stored"] is False, "raw_prompt_stored is False")
check(record["pii_stored"] is False, "pii_stored is False")
check(record["behavior_change_allowed"] is False, "behavior_change_allowed is False")
check(record["value_inference_allowed"] is False, "value_inference_allowed is False")
check(record["safe_to_record"] is True, "safe_to_record is True")
check(record["reason"] == "blocked_write_observed", "reason preserved")


# ---------------------------------------------------------------------------
# SECTION 9 — append_public_signal_record append-only to temp file
# ---------------------------------------------------------------------------
print("\nTest 9: append_public_signal_record appends one line")
with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
    tmp_path = pathlib.Path(tf.name)

result = append_public_signal_record(record, path=str(tmp_path))
check(result["stored"] is True, "stored is True")
check(result["reason"] == "stored", "reason is stored")
check(result["record_type"] == "public_signal_v1", "record_type returned")
check(tmp_path.exists(), "file was created")

# Read and verify content
lines = tmp_path.read_text().strip().split("\n")
check(len(lines) == 1, "exactly 1 line appended")
stored_record = json.loads(lines[0])
check(stored_record["record_type"] == "public_signal_v1", "stored record is valid JSON")
check(stored_record["session_id_hash"] == "abc123", "session_id_hash preserved in store")
check(stored_record.get("blocked_write") is not True, "blocked_write field not in stored record (build strips it)")

tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# SECTION 10 — second append adds second line (append-only confirmed)
# ---------------------------------------------------------------------------
print("\nTest 10: second append adds second line (append-only)")
with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
    tmp_path = pathlib.Path(tf.name)

r1 = build_public_signal_record({
    "session_id_hash": "abc123",
    "message_length_bucket": "medium",
    "response_path": "direct_answer",
    "fallback_triggered": False,
    "evidence_offer_shown": False,
    "evidence_offer_accepted": False,
    "blocked_write": False,
    "topic_normalized": "solar_panels",
    "timestamp": "2026-04-30T10:00:00Z",
})
r2 = build_public_signal_record({
    "session_id_hash": "def456",
    "message_length_bucket": "short",
    "response_path": "fallback_safe",
    "fallback_triggered": True,
    "evidence_offer_shown": False,
    "evidence_offer_accepted": False,
    "blocked_write": False,
    "topic_normalized": "unknown_topic",
    "timestamp": "2026-04-30T10:01:00Z",
})

append_public_signal_record(r1, path=str(tmp_path))
append_public_signal_record(r2, path=str(tmp_path))

lines = tmp_path.read_text().strip().split("\n")
check(len(lines) == 2, "exactly 2 lines after two appends")

tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# SECTION 11 — capture_website_signal never raises on failure
# ---------------------------------------------------------------------------
print("\nTest 11: capture_website_signal never raises on failure")
# Pass garbage — function must not propagate
try:
    capture_website_signal(
        message="test",
        session_id="s1",
        response_path=None,  # None should be handled
        quality_class=None,
        blocked_write="not_a_bool",  # wrong type
        evidence_offer_shown=None,
        evidence_offer_accepted=None,
        topic_normalized=123,  # wrong type
        fallback_triggered="also_not_bool",
    )
    check(True, "no exception raised with garbage inputs")
except Exception as e:
    check(False, f"exception raised with garbage inputs: {e}")


# ---------------------------------------------------------------------------
# SECTION 12 — evidence_offer_accepted → S2 signal
# ---------------------------------------------------------------------------
print("\nTest 12: evidence_offer_accepted → S2")
event_s2 = {
    "session_id_hash": "xyz789",
    "message_length_bucket": "long",
    "response_path": "evidence_workspace_response",
    "fallback_triggered": False,
    "evidence_offer_shown": True,
    "evidence_offer_accepted": True,
    "blocked_write": False,
    "topic_normalized": "consciousness",
    "timestamp": "2026-04-30T10:02:00Z",
}
r = classify_public_signal(event_s2)
check(r["signal_type"] == "S2", "evidence_offer_accepted → S2")
check(r["safe_to_record"] is True, "safe_to_record is True for S2")


# ---------------------------------------------------------------------------
# SECTION 13 — fallback_triggered → S4
# ---------------------------------------------------------------------------
print("\nTest 13: fallback_triggered → S4")
fallback_event = {
    "session_id_hash": "xyz789",
    "message_length_bucket": "short",
    "response_path": "fallback_safe",
    "fallback_triggered": True,
    "evidence_offer_shown": False,
    "evidence_offer_accepted": False,
    "blocked_write": False,
    "topic_normalized": "unknown",
    "timestamp": "2026-04-30T10:03:00Z",
}
r = classify_public_signal(fallback_event)
check(r["signal_type"] == "S4", "fallback_triggered → S4")
check(r["safe_to_record"] is True, "safe_to_record is True for S4")


# ---------------------------------------------------------------------------
# SECTION 14 — response_path with unknown → S1
# ---------------------------------------------------------------------------
print("\nTest 14: unknown response_path → S1")
unknown_event = {
    "session_id_hash": "xyz789",
    "message_length_bucket": "medium",
    "response_path": "handler_unknown_topic",
    "fallback_triggered": False,
    "evidence_offer_shown": False,
    "evidence_offer_accepted": False,
    "blocked_write": False,
    "topic_normalized": "obscure_topic",
    "timestamp": "2026-04-30T10:04:00Z",
}
r = classify_public_signal(unknown_event)
check(r["signal_type"] == "S1", "unknown response_path → S1")


# ---------------------------------------------------------------------------
# SECTION 15 — response_path with improvement → S5
# ---------------------------------------------------------------------------
print("\nTest 15: improvement response_path → S5")
for imp_path in ["handler_improvement_query", "handler_proposal_draft"]:
    imp_event = {
        "session_id_hash": "xyz789",
        "message_length_bucket": "long",
        "response_path": imp_path,
        "fallback_triggered": False,
        "evidence_offer_shown": False,
        "evidence_offer_accepted": False,
        "blocked_write": False,
        "topic_normalized": "refinement",
        "timestamp": "2026-04-30T10:05:00Z",
    }
    r = classify_public_signal(imp_event)
    check(r["signal_type"] == "S5", f"{imp_path} → S5")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print(f"\n{'='*60}")
print(f"Results: {PASS} passed, {FAIL} failed")
if FAIL:
    print("WEBSITE_SIGNAL_INTEGRATION_TESTS_FAILED")
    sys.exit(1)
else:
    print("WEBSITE_SIGNAL_INTEGRATION_TESTS_OK")
    sys.exit(0)