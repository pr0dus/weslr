#!/usr/bin/env python3
"""
WESLR Public Signal Store V1 — Tests

Covers all 12 required assertions from SPEC.
Confirms: PUBLIC_SIGNAL_STORE_TESTS_OK
Exits non-zero on any failure.
"""

import sys
import importlib
import json
import pathlib
import tempfile
import hashlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "weslr"))

# Reload to pick up latest source (clears sys.modules cache)
import public_signal_store
importlib.reload(public_signal_store)
import user_signal_intake
importlib.reload(user_signal_intake)

from user_signal_intake import build_public_signal_record
from public_signal_store import (
    validate_public_signal_record,
    append_public_signal_record,
    DEFAULT_PATH,
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
# Helpers
# ---------------------------------------------------------------------------

def _file_hash(p):
    if not p.exists():
        return None
    return hashlib.md5(p.read_bytes()).hexdigest()


def _line_count(p):
    if not p.exists():
        return 0
    content = p.read_text().strip()
    if not content:
        return 0
    return len(content.split("\n"))


# ---------------------------------------------------------------------------
# Build a valid safe record
# ---------------------------------------------------------------------------

def _make_valid_record(**overrides):
    base_event = ev(
        session_id_hash="abc123",
        message_length_bucket="medium",
        response_path="handler_fallback_response",
        fallback_triggered=True,
        evidence_offer_shown=False,
        evidence_offer_accepted=False,
        blocked_write=False,
        topic_normalized="solar_panel",
        timestamp="2026-04-30T10:00:00Z",
    )
    base_event.update(overrides)
    return build_public_signal_record(base_event)


# ---------------------------------------------------------------------------
# SECTION 1 — valid safe record appends one line
# ---------------------------------------------------------------------------
print("Test 1: valid safe record appends one line")
with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
    tmp = pathlib.Path(tf.name)

record = _make_valid_record()
result = append_public_signal_record(record, path=str(tmp))
check(result["stored"] is True, "stored is True")
check(result["reason"] == "stored", "reason is stored")
check(result["record_type"] == "public_signal_v1", "record_type returned")
check(result["path"] == str(tmp), "path returned")
check(tmp.exists(), "file was created")
check(_line_count(tmp) == 1, "exactly 1 line appended")

# cleanup
tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# SECTION 2 — unsafe record rejected
# ---------------------------------------------------------------------------
print("\nTest 2: unsafe record rejected")
with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
    tmp = pathlib.Path(tf.name)

# build_public_signal_record returns safe_to_record=False for forbidden fields
unsafe_event = ev(
    session_id_hash="abc123",
    message_length_bucket="medium",
    response_path="handler_fallback_response",
    fallback_triggered=False,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    blocked_write=False,
    topic_normalized="solar",
    timestamp="2026-04-30T10:00:00Z",
    message="install solar on north roof",  # forbidden
)
unsafe_record = build_public_signal_record(unsafe_event)
result = append_public_signal_record(unsafe_record, path=str(tmp))
check(result["stored"] is False, "stored is False for unsafe record")
check(result["reason"] == "safe_to_record_not_true", "reason is safe_to_record_not_true")
check(not tmp.exists() or _line_count(tmp) == 0, "no lines written")

tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# SECTION 3 — raw prompt field rejected
# ---------------------------------------------------------------------------
print("\nTest 3: raw prompt field rejected")
bad = _make_valid_record()
bad["raw_prompt"] = "some raw prompt"
result = validate_public_signal_record(bad)
check(result["valid"] is False, "raw_prompt key → invalid")
check("raw_prompt" in result["forbidden_fields"], "raw_prompt in forbidden_fields")


# ---------------------------------------------------------------------------
# SECTION 4 — email/phone/IP-like data rejected
# ---------------------------------------------------------------------------
print("\nTest 4: email/phone/IP-like data rejected")

# email-like in a custom field
bad = _make_valid_record()
bad["custom_field"] = "contact user@example.com"
result = validate_public_signal_record(bad)
# This passes validate because custom_field is not a forbidden key
# but the string value passes the pii scan — check in append
with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
    tmp = pathlib.Path(tf.name)
r = append_public_signal_record(bad, path=str(tmp))
check(r["stored"] is False, "email-like string → rejected by append")
check(r["reason"] == "pii_like_content_detected", "reason is pii_like_content_detected")
tmp.unlink(missing_ok=True)

# phone-like
bad = _make_valid_record()
bad["custom_field"] = "call me at 1234567890"
with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
    tmp = pathlib.Path(tf.name)
r = append_public_signal_record(bad, path=str(tmp))
check(r["stored"] is False, "phone-like string → rejected")
check(r["reason"] == "pii_like_content_detected", "reason is pii_like_content_detected")
tmp.unlink(missing_ok=True)

# IPv4
bad = _make_valid_record()
bad["custom_field"] = "IP: 192.168.1.100"
with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
    tmp = pathlib.Path(tf.name)
r = append_public_signal_record(bad, path=str(tmp))
check(r["stored"] is False, "IPv4-like string → rejected")
check(r["reason"] == "pii_like_content_detected", "reason is pii_like_content_detected")
tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# SECTION 5 — behavior_change_allowed true rejected
# ---------------------------------------------------------------------------
print("\nTest 5: behavior_change_allowed true rejected")
bad = _make_valid_record()
bad["behavior_change_allowed"] = True
result = validate_public_signal_record(bad)
check(result["valid"] is False, "behavior_change_allowed=True → invalid")
check(result["reason"] == "behavior_change_allowed_not_false", "reason")


# ---------------------------------------------------------------------------
# SECTION 6 — value_inference_allowed true rejected
# ---------------------------------------------------------------------------
print("\nTest 6: value_inference_allowed true rejected")
bad = _make_valid_record()
bad["value_inference_allowed"] = True
result = validate_public_signal_record(bad)
check(result["valid"] is False, "value_inference_allowed=True → invalid")
check(result["reason"] == "value_inference_allowed_not_false", "reason")


# ---------------------------------------------------------------------------
# SECTION 7 — raw_prompt_stored true rejected
# ---------------------------------------------------------------------------
print("\nTest 7: raw_prompt_stored true rejected")
bad = _make_valid_record()
bad["raw_prompt_stored"] = True
result = validate_public_signal_record(bad)
check(result["valid"] is False, "raw_prompt_stored=True → invalid")
check(result["reason"] == "raw_prompt_stored_not_false", "reason")


# ---------------------------------------------------------------------------
# SECTION 8 — pii_stored true rejected
# ---------------------------------------------------------------------------
print("\nTest 8: pii_stored true rejected")
bad = _make_valid_record()
bad["pii_stored"] = True
result = validate_public_signal_record(bad)
check(result["valid"] is False, "pii_stored=True → invalid")
check(result["reason"] == "pii_stored_not_false", "reason")


# ---------------------------------------------------------------------------
# SECTION 9 — append-only behavior preserves existing lines
# ---------------------------------------------------------------------------
print("\nTest 9: append-only preserves existing lines")
with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
    # Pre-write 3 lines
    tf.write(json.dumps({"n": 1}) + "\n")
    tf.write(json.dumps({"n": 2}) + "\n")
    tf.write(json.dumps({"n": 3}) + "\n")
    tmp = pathlib.Path(tf.name)

check(_line_count(tmp) == 3, "pre-condition: 3 lines exist")

# append 2 more
for i in range(2):
    rec = _make_valid_record(session_id_hash=f"hash{i}")
    r = append_public_signal_record(rec, path=str(tmp))
    check(r["stored"] is True, f"append {i+1} stored")

check(_line_count(tmp) == 5, "5 lines after 2 appends (3 pre + 2 new)")
tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# SECTION 10 — no writes to production truth JSONL files
# ---------------------------------------------------------------------------
print("\nTest 10: production file rejects")

# Patch DEFAULT_PATH temporarily — we test the guard directly
# We test that a record targeting proposal_trace.jsonl is rejected
# by using a tmp file named the same as a production file
import public_signal_store as pss

for prod_file in ["proposal_trace.jsonl", "implementation_plans.jsonl"]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
        # Rename to production filename
        prod_path = tf.name.rsplit("/", 1)[0] + "/" + prod_file
        rec = _make_valid_record()
        r = append_public_signal_record(rec, path=prod_path)
        check(r["stored"] is False, f"{prod_file} → rejected")
        check(r["reason"] == "production_file_rejected", f"{prod_file} reason is production_file_rejected")


# ---------------------------------------------------------------------------
# SECTION 11 — malformed JSON-like record rejected
# ---------------------------------------------------------------------------
print("\nTest 11: malformed JSON-like record rejected")
bad = {"record_type": "not_public_signal_v1", "safe_to_record": True,
       "raw_prompt_stored": False, "pii_stored": False,
       "behavior_change_allowed": False, "value_inference_allowed": False}
result = validate_public_signal_record(bad)
check(result["valid"] is False, "wrong record_type → invalid")
check(result["reason"] == "invalid_record_type", "reason is invalid_record_type")


# ---------------------------------------------------------------------------
# SECTION 12 — return schema correct
# ---------------------------------------------------------------------------
print("\nTest 12: return schema correct")
with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
    tmp = pathlib.Path(tf.name)

rec = _make_valid_record()
r = append_public_signal_record(rec, path=str(tmp))
check("stored" in r, "return has 'stored'")
check("reason" in r, "return has 'reason'")
check("path" in r, "return has 'path'")
check("record_type" in r, "return has 'record_type'")
check(r["record_type"] == "public_signal_v1", "record_type is public_signal_v1")
check(isinstance(r["stored"], bool), "stored is bool")
check(isinstance(r["reason"], str), "reason is str")
check(isinstance(r["path"], str), "path is str")

tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print()
print("=" * 50)
total = PASS + FAIL
print(f"PUBLIC_SIGNAL_STORE_TESTS: {PASS}/{total} passed")
if FAIL == 0:
    print("PUBLIC_SIGNAL_STORE_TESTS_OK")
else:
    print(f"PUBLIC_SIGNAL_STORE_TESTS_FAILED ({FAIL} failures)")
    sys.exit(1)
