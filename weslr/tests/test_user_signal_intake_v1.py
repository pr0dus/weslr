#!/usr/bin/env python3
"""
WESLR User Signal Intake V1 — Tests

Covers all 21 required assertions from SPEC.
Confirms: USER_SIGNAL_INTAKE_TESTS_OK
Exits non-zero on any failure.
"""

import sys
import pathlib
import ast
import re

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "weslr"))

from user_signal_intake import (
    contains_forbidden_field,
    detect_pii_like_content,
    classify_public_signal,
    build_public_signal_record,
)

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


def ev(**kwargs):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# SECTION 1 — fallback_triggered creates S4
# ---------------------------------------------------------------------------
print("Test 1: fallback_triggered creates S4")
r = classify_public_signal(ev(
    session_id_hash="abc123",
    message_length_bucket="medium",
    response_path="handler_fallback_response",
    fallback_triggered=True,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    blocked_write=False,
    topic_normalized="solar_panel",
    timestamp="2026-04-30T10:00:00Z",
))
check(r["signal_type"] == "S4", "fallback_triggered → S4")
check(r["safe_to_record"] is True, "safe_to_record is True")


# ---------------------------------------------------------------------------
# SECTION 2 — evidence_offer_shown creates S2
# ---------------------------------------------------------------------------
print("\nTest 2: evidence_offer_shown creates S2")
r = classify_public_signal(ev(
    session_id_hash="abc123",
    message_length_bucket="medium",
    response_path="handler_evidence_overlay",
    fallback_triggered=False,
    evidence_offer_shown=True,
    evidence_offer_accepted=False,
    blocked_write=False,
    topic_normalized="installation",
    timestamp="2026-04-30T10:01:00Z",
))
check(r["signal_type"] == "S2", "evidence_offer_shown → S2")


# ---------------------------------------------------------------------------
# SECTION 3 — evidence_offer_accepted creates S2
# ---------------------------------------------------------------------------
print("\nTest 3: evidence_offer_accepted creates S2")
r = classify_public_signal(ev(
    session_id_hash="abc123",
    message_length_bucket="long",
    response_path="handler_evidence_overlay",
    fallback_triggered=False,
    evidence_offer_shown=True,
    evidence_offer_accepted=True,
    blocked_write=False,
    topic_normalized="warranty",
    timestamp="2026-04-30T10:02:00Z",
))
check(r["signal_type"] == "S2", "evidence_offer_accepted → S2")


# ---------------------------------------------------------------------------
# SECTION 4 — improvement response_path creates S5
# ---------------------------------------------------------------------------
print("\nTest 4: improvement response_path creates S5")
for path in ["handler_improvement_query", "handler_proposal_draft"]:
    r = classify_public_signal(ev(
        session_id_hash="abc123",
        message_length_bucket="short",
        response_path=path,
        fallback_triggered=False,
        evidence_offer_shown=False,
        evidence_offer_accepted=False,
        blocked_write=False,
        topic_normalized=None,
        timestamp="2026-04-30T10:03:00Z",
    ))
    check(r["signal_type"] == "S5", f"{path} → S5")


# ---------------------------------------------------------------------------
# SECTION 5 — unknown path creates S1 when fallback not triggered
# ---------------------------------------------------------------------------
print("\nTest 5: unknown path creates S1 (no fallback)")
for path in ["handler_unknown_topic", "fallback_safe_response"]:
    r = classify_public_signal(ev(
        session_id_hash="abc123",
        message_length_bucket="medium",
        response_path=path,
        fallback_triggered=False,
        evidence_offer_shown=False,
        evidence_offer_accepted=False,
        blocked_write=False,
        topic_normalized="some_topic",
        timestamp="2026-04-30T10:04:00Z",
    ))
    check(r["signal_type"] == "S1", f"{path} → S1 (fallback not triggered)")


# ---------------------------------------------------------------------------
# SECTION 6 — fallback_safe with fallback_triggered creates S4
# ---------------------------------------------------------------------------
print("\nTest 6: fallback_safe + fallback_triggered → S4")
r = classify_public_signal(ev(
    session_id_hash="abc123",
    message_length_bucket="medium",
    response_path="fallback_safe_response",
    fallback_triggered=True,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    blocked_write=False,
    topic_normalized="some_topic",
    timestamp="2026-04-30T10:05:00Z",
))
check(r["signal_type"] == "S4", "fallback_triggered overrides unknown path → S4")


# ---------------------------------------------------------------------------
# SECTION 7 — blocked_write is safe but signal_type null
# ---------------------------------------------------------------------------
print("\nTest 7: blocked_write is safe but signal_type null")
r = classify_public_signal(ev(
    session_id_hash="abc123",
    message_length_bucket="long",
    response_path="handler_write_blocked",
    fallback_triggered=False,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    blocked_write=True,
    topic_normalized=None,
    timestamp="2026-04-30T10:06:00Z",
))
check(r["signal_type"] is None, "blocked_write → signal_type null")
check(r["safe_to_record"] is True, "blocked_write → safe_to_record True")
check(r["reason"] == "blocked_write_observed", "reason is blocked_write_observed")


# ---------------------------------------------------------------------------
# SECTION 8 — normal event is safe with signal_type null
# ---------------------------------------------------------------------------
print("\nTest 8: normal event safe, signal_type null")
r = classify_public_signal(ev(
    session_id_hash="xyz789",
    message_length_bucket="short",
    response_path="handler_capability_discovery",
    fallback_triggered=False,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    blocked_write=False,
    topic_normalized="battery_storage",
    timestamp="2026-04-30T10:07:00Z",
))
check(r["signal_type"] is None, "normal event → signal_type null")
check(r["safe_to_record"] is True, "normal event → safe_to_record True")
check(r["reason"] == "no_signal", "reason is no_signal")


# ---------------------------------------------------------------------------
# SECTION 9 — raw message field rejected
# ---------------------------------------------------------------------------
print("\nTest 9: raw message field rejected")
r = classify_public_signal(ev(
    session_id_hash="abc123",
    message_length_bucket="medium",
    response_path="handler_unrelated_query",
    fallback_triggered=False,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    blocked_write=False,
    topic_normalized="solar",
    timestamp="2026-04-30T10:08:00Z",
    message="install solar on north roof",  # forbidden
))
check(r["safe_to_record"] is False, "message field → safe_to_record False")
check(r["contains_raw_prompt"] is True, "contains_raw_prompt is True")


# ---------------------------------------------------------------------------
# SECTION 10 — prompt field rejected
# ---------------------------------------------------------------------------
print("\nTest 10: prompt field rejected")
r = classify_public_signal(ev(
    session_id_hash="abc123",
    message_length_bucket="medium",
    response_path="handler_unrelated_query",
    fallback_triggered=False,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    blocked_write=False,
    topic_normalized="solar",
    timestamp="2026-04-30T10:09:00Z",
    prompt="how do I install solar",  # forbidden
))
check(r["safe_to_record"] is False, "prompt field → safe_to_record False")
check(r["contains_raw_prompt"] is True, "contains_raw_prompt is True")


# ---------------------------------------------------------------------------
# SECTION 11 — email field rejected
# ---------------------------------------------------------------------------
print("\nTest 11: email field rejected")
r = classify_public_signal(ev(
    session_id_hash="abc123",
    message_length_bucket="medium",
    response_path="handler_unrelated_query",
    fallback_triggered=False,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    blocked_write=False,
    topic_normalized="solar",
    timestamp="2026-04-30T10:10:00Z",
    email="user@example.com",  # forbidden + PII-like
))
check(r["safe_to_record"] is False, "email field → safe_to_record False")
check(r["contains_raw_prompt"] is True, "contains_raw_prompt is True (forbidden field)")
check(r["contains_pii"] is False, "contains_pii is False (forbidden field, not pii)")


# ---------------------------------------------------------------------------
# SECTION 12 — phone field rejected
# ---------------------------------------------------------------------------
print("\nTest 12: phone field rejected")
r = classify_public_signal(ev(
    session_id_hash="abc123",
    message_length_bucket="medium",
    response_path="handler_unrelated_query",
    fallback_triggered=False,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    blocked_write=False,
    topic_normalized="solar",
    timestamp="2026-04-30T10:11:00Z",
    phone="+49 123 4567890",  # forbidden
))
check(r["safe_to_record"] is False, "phone field → safe_to_record False")


# ---------------------------------------------------------------------------
# SECTION 13 — IP field rejected
# ---------------------------------------------------------------------------
print("\nTest 13: IP field rejected")
r = classify_public_signal(ev(
    session_id_hash="abc123",
    message_length_bucket="medium",
    response_path="handler_unrelated_query",
    fallback_triggered=False,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    blocked_write=False,
    topic_normalized="solar",
    timestamp="2026-04-30T10:12:00Z",
    ip="192.168.1.100",  # forbidden
))
check(r["safe_to_record"] is False, "ip field → safe_to_record False")


# ---------------------------------------------------------------------------
# SECTION 14 — PII-like string value rejected
# ---------------------------------------------------------------------------
print("\nTest 14: PII-like string value rejected")
# email-like in a non-forbidden string field
r = classify_public_signal(ev(
    session_id_hash="abc123",
    message_length_bucket="medium",
    response_path="handler_unrelated_query",
    fallback_triggered=False,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    blocked_write=False,
    topic_normalized="solar",
    timestamp="2026-04-30T10:13:00Z",
    custom_field="contact me at user@example.com",
))
check(r["safe_to_record"] is False, "PII-like string → safe_to_record False")
check(r["contains_pii"] is True, "contains_pii is True")

# phone-like
r = classify_public_signal(ev(
    session_id_hash="abc123",
    message_length_bucket="medium",
    response_path="handler_unrelated_query",
    fallback_triggered=False,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    blocked_write=False,
    topic_normalized="solar",
    timestamp="2026-04-30T10:14:00Z",
    custom_field="call me at 1234567890",
))
check(r["safe_to_record"] is False, "phone-like string → safe_to_record False")
check(r["contains_pii"] is True, "contains_pii is True")


# ---------------------------------------------------------------------------
# SECTION 15 — output never includes forbidden fields
# ---------------------------------------------------------------------------
print("\nTest 15: output never includes forbidden fields")
FORBIDDEN_OUT = {"message", "raw_message", "prompt", "user_input", "email",
                 "phone", "address", "ip", "user_id", "name", "location"}
test_event = ev(
    session_id_hash="abc123",
    message_length_bucket="medium",
    response_path="handler_fallback_response",
    fallback_triggered=True,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    blocked_write=False,
    topic_normalized="solar",
    timestamp="2026-04-30T10:15:00Z",
)
record = build_public_signal_record(test_event)
for key in record:
    check(key not in FORBIDDEN_OUT, f"output key '{key}' not forbidden")
check(True, "all output keys checked")


# ---------------------------------------------------------------------------
# SECTION 16 — raw_prompt_stored always false
# ---------------------------------------------------------------------------
print("\nTest 16: raw_prompt_stored always false")
events = [
    ev(fallback_triggered=True, evidence_offer_shown=False),
    ev(fallback_triggered=False, evidence_offer_shown=True),
    ev(fallback_triggered=False, evidence_offer_accepted=True),
    ev(response_path="handler_unknown_topic", fallback_triggered=False),
    ev(response_path="handler_improvement_query", fallback_triggered=False),
    ev(blocked_write=True, fallback_triggered=False),
    ev(fallback_triggered=False),
]
for e in events:
    full = dict({"session_id_hash": "x", "message_length_bucket": "short",
                 "response_path": "h", "timestamp": "t"}, **e)
    rec = build_public_signal_record(full)
    check(rec["raw_prompt_stored"] is False, f"raw_prompt_stored is False for {e}")


# ---------------------------------------------------------------------------
# SECTION 17 — pii_stored always false
# ---------------------------------------------------------------------------
print("\nTest 17: pii_stored always false")
for e in events:
    full = dict({"session_id_hash": "x", "message_length_bucket": "short",
                 "response_path": "h", "timestamp": "t"}, **e)
    rec = build_public_signal_record(full)
    check(rec["pii_stored"] is False, f"pii_stored is False for {e}")


# ---------------------------------------------------------------------------
# SECTION 18 — behavior_change_allowed always false
# ---------------------------------------------------------------------------
print("\nTest 18: behavior_change_allowed always false")
for e in events:
    full = dict({"session_id_hash": "x", "message_length_bucket": "short",
                 "response_path": "h", "timestamp": "t"}, **e)
    rec = build_public_signal_record(full)
    check(rec["behavior_change_allowed"] is False, f"behavior_change_allowed is False for {e}")


# ---------------------------------------------------------------------------
# SECTION 19 — value_inference_allowed always false
# ---------------------------------------------------------------------------
print("\nTest 19: value_inference_allowed always false")
for e in events:
    full = dict({"session_id_hash": "x", "message_length_bucket": "short",
                 "response_path": "h", "timestamp": "t"}, **e)
    rec = build_public_signal_record(full)
    check(rec["value_inference_allowed"] is False, f"value_inference_allowed is False for {e}")


# ---------------------------------------------------------------------------
# SECTION 20 — deterministic output for same input
# ---------------------------------------------------------------------------
print("\nTest 20: deterministic output for same input")
base = ev(
    session_id_hash="det123",
    message_length_bucket="medium",
    response_path="handler_fallback_response",
    fallback_triggered=True,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    blocked_write=False,
    topic_normalized="determinism_test",
    timestamp="2026-04-30T10:20:00Z",
)
for _ in range(5):
    r1 = classify_public_signal(base)
    r2 = classify_public_signal(base)
    check(r1 == r2, "5 runs: classify_public_signal is deterministic")


# ---------------------------------------------------------------------------
# SECTION 21 — no-write proof via AST scan
# ---------------------------------------------------------------------------
print("\nTest 21: no-write proof via AST scan")
module_path = pathlib.Path(__file__).resolve().parents[1] / "user_signal_intake.py"
source = module_path.read_text()
tree = ast.parse(source)

write_calls = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        func_name = ""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
        if func_name in {"open", "write", "dump", "dumps"}:
            write_calls.append(func_name)

check(len(write_calls) == 0, f"AST scan: no write calls found (found: {write_calls})")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print()
print("=" * 50)
total = PASS + FAIL
print(f"USER_SIGNAL_INTAKE_TESTS: {PASS}/{total} passed")
if FAIL == 0:
    print("USER_SIGNAL_INTAKE_TESTS_OK")
else:
    print(f"USER_SIGNAL_INTAKE_TESTS_FAILED ({FAIL} failures)")
    sys.exit(1)