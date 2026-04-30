"""
WESLR Test Observation Harness V1

Tests for observation_harness.py:
  - session event structure valid
  - timeline ordering correct
  - batch requires >=3 sessions
  - provenance present
  - no writes
  - no production JSONL touched
  - deterministic output
"""

import hashlib
import json
import os
import sys
import time

# Add weslr to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from observation_harness import (
    load_script,
    run_observation_session,
    build_timeline_segment,
    validate_batch,
    _make_provenance_id,
    _iso_timestamp,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PRODUCTION_JSONL_PATHS = [
    "proposal_trace.jsonl",
    "state_checkpoint.json",
    "iss_diagnostics.jsonl",
    "audit_log.jsonl",
]


def _hash_jsonl() -> dict[str, str]:
    """Return SHA256 of each production JSONL file if it exists."""
    result = {}
    for p in PRODUCTION_JSONL_PATHS:
        full = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), p)
        if os.path.exists(full):
            with open(full, "rb") as f:
                result[p] = hashlib.sha256(f.read()).hexdigest()
    return result


def _make_minimal_script(n: int = 15) -> list[dict]:
    """Make a minimal valid script with n interactions."""
    categories = ["neutral", "unknown", "evidence_trigger", "conflict", "noise", "domain_shift", "safety_probe"]
    script = []
    for i in range(n):
        script.append({
            "input": f"test input {i+1}",
            "category": categories[i % len(categories)],
        })
    return script


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_load_script_valid():
    script = _make_minimal_script(15)
    loaded = load_script(script)
    assert len(loaded) == 15
    assert all("message_index" in item for item in loaded)
    assert all("provenance_chain_id" in item for item in loaded)
    print("PASS: load_script valid")


def test_load_script_missing_input():
    try:
        load_script([{"category": "neutral"}])
        assert False, "should have raised"
    except ValueError as e:
        assert "missing 'input'" in str(e)
    print("PASS: load_script missing input raises")


def test_load_script_missing_category():
    try:
        load_script([{"input": "hello"}])
        assert False, "should have raised"
    except ValueError as e:
        assert "missing 'category'" in str(e)
    print("PASS: load_script missing category raises")


def test_load_script_invalid_category():
    try:
        load_script([{"input": "hello", "category": "not_a_real_category"}])
        assert False, "should have raised"
    except ValueError as e:
        assert "not in" in str(e)
    print("PASS: load_script invalid category raises")


def test_run_observation_session_structure():
    script = _make_minimal_script(15)
    result = run_observation_session(script, "session_20260430_001")

    assert "session_id" in result
    assert result["session_id"] == "session_20260430_001"
    assert "events" in result
    assert len(result["events"]) == 15

    for e in result["events"]:
        assert "message_index" in e
        assert "input" in e
        assert "input_category" in e
        assert "response_path" in e
        assert "signal_emitted" in e
        assert "signal_type" in e
        assert "timestamp" in e
        assert "provenance_chain_id" in e
        # signal_type is either a signal (S1-S6) or null (string)
        assert e["signal_type"] is None or e["signal_type"].startswith("S")

    print("PASS: run_observation_session event structure valid")


def test_run_observation_session_no_cross_session_memory():
    script1 = _make_minimal_script(12)
    script2 = _make_minimal_script(12)

    sess1 = run_observation_session(script1, "session_a")
    sess2 = run_observation_session(script2, "session_b")

    # No cross-session memory field in output
    assert sess1["session_id"] != sess2["session_id"]
    # Timestamps should be independent
    assert sess1["events"][0]["timestamp"] != sess2["events"][0]["timestamp"]

    print("PASS: run_observation_session no cross-session memory")


def test_run_observation_session_deterministic():
    script = _make_minimal_script(15)
    result1 = run_observation_session(script, "session_deterministic")
    result2 = run_observation_session(script, "session_deterministic")

    # Same script + same session_id should yield same signal_emitted/signal_type pattern
    sigs1 = [(e["signal_emitted"], e["signal_type"]) for e in result1["events"]]
    sigs2 = [(e["signal_emitted"], e["signal_type"]) for e in result2["events"]]
    assert sigs1 == sigs2, "Signal emission must be deterministic"

    print("PASS: run_observation_session deterministic output")


def test_build_timeline_segment_ordering():
    script1 = _make_minimal_script(12)
    script2 = _make_minimal_script(12)
    script3 = _make_minimal_script(12)

    sess1 = run_observation_session(script1, "session_001")
    sess2 = run_observation_session(script2, "session_002")
    sess3 = run_observation_session(script3, "session_003")

    # Slight delay to ensure different timestamps
    time.sleep(0.05)

    timeline = build_timeline_segment([sess1, sess2, sess3])

    assert len(timeline) == 36  # 3 * 12

    # Check ordering: events sorted by timestamp
    timestamps = [e["timestamp"] for e in timeline]
    assert timestamps == sorted(timestamps), "Timeline must be sorted by timestamp"

    # run_index should be non-decreasing
    run_indices = [e["run_index"] for e in timeline]
    # Within same run_index, timestamp ordering should hold
    for run_idx in range(3):
        run_events = [e for e in timeline if e["run_index"] == run_idx]
        run_ts = [e["timestamp"] for e in run_events]
        assert run_ts == sorted(run_ts), f"Events within run {run_idx} must be timestamp-sorted"

    print("PASS: build_timeline_segment ordering correct")


def test_build_timeline_segment_structure():
    script = _make_minimal_script(15)
    sess = run_observation_session(script, "session_tl")
    timeline = build_timeline_segment([sess])

    for e in timeline:
        assert "event_id" in e
        assert "timeline_segment_id" in e
        assert "session_id" in e
        assert "run_index" in e
        assert "timestamp" in e
        assert "signal_type" in e
        assert "signal_emitted" in e
        assert "input_category" in e
        assert "provenance_chain_id" in e

    print("PASS: build_timeline_segment structure valid")


def test_validate_batch_requires_min_3_sessions():
    script = _make_minimal_script(15)

    # 2 sessions — should fail
    sess1 = run_observation_session(script, "s1")
    sess2 = run_observation_session(script, "s2")
    valid, failures = validate_batch([sess1, sess2])
    assert not valid
    assert any("minimum 3" in f for f in failures)

    # 3 sessions — should pass
    sess3 = run_observation_session(script, "s3")
    valid, failures = validate_batch([sess1, sess2, sess3])
    assert valid

    print("PASS: validate_batch requires >=3 sessions")


def test_validate_batch_requires_10_to_20_events():
    script_too_few = [{"input": f"q{i}", "category": "neutral"} for i in range(8)]
    script_too_many = [{"input": f"q{i}", "category": "neutral"} for i in range(25)]

    # Should fail: too few
    sess_few = run_observation_session(script_too_few, "s_few")
    valid, failures = validate_batch([sess_few, sess_few, sess_few])
    assert not valid
    assert any("8 events" in f for f in failures)

    # Should fail: too many
    sess_many = run_observation_session(script_too_many, "s_many")
    valid, failures = validate_batch([sess_many, sess_many, sess_many])
    assert not valid
    assert any("25 events" in f for f in failures)

    # 10 and 20 are valid
    script_10 = [{"input": f"q{i}", "category": "neutral"} for i in range(10)]
    script_20 = [{"input": f"q{i}", "category": "neutral"} for i in range(20)]
    sess_10 = run_observation_session(script_10, "s_10")
    sess_20 = run_observation_session(script_20, "s_20")
    sess_15 = run_observation_session(_make_minimal_script(15), "s_15")
    valid, _ = validate_batch([sess_10, sess_15, sess_20])
    assert valid

    print("PASS: validate_batch requires 10–20 events per session")


def test_validate_batch_provenance_present():
    script = _make_minimal_script(15)
    sess = run_observation_session(script, "s1")

    # All events should have provenance_chain_id
    for e in sess["events"]:
        assert e["provenance_chain_id"]
        assert len(e["provenance_chain_id"]) == 32  # SHA256 truncated to 32

    # Batch validation should pass provenance check
    sess2 = run_observation_session(script, "s2")
    sess3 = run_observation_session(script, "s3")
    valid, failures = validate_batch([sess, sess2, sess3])
    assert valid, failures

    print("PASS: validate_batch provenance present")


def test_validate_batch_no_cross_session_memory():
    script = _make_minimal_script(15)
    s1 = run_observation_session(script, "s1")
    s2 = run_observation_session(script, "s2")
    s3 = run_observation_session(script, "s3")

    valid, failures = validate_batch([s1, s2, s3])
    # session_id is not itself a cross-session memory violation
    # The check is that no hidden fields carry state between sessions
    assert valid

    print("PASS: validate_batch no cross-session memory fields")


def test_no_writes_production_jsonl():
    """Verify no production JSONL files are written by harness operations."""
    before = _hash_jsonl()

    script = _make_minimal_script(15)
    s1 = run_observation_session(script, "s1")
    s2 = run_observation_session(script, "s2")
    s3 = run_observation_session(script, "s3")

    validate_batch([s1, s2, s3])
    build_timeline_segment([s1, s2, s3])

    after = _hash_jsonl()

    for p, h_before in before.items():
        h_after = after.get(p, "")
        assert h_before == h_after, f"{p} was modified — harness wrote to production state"

    print("PASS: no writes to production JSONL")


def test_provenance_chain_id_format():
    """Verify provenance_chain_id is deterministic and well-formed."""
    pid = _make_provenance_id("session_001", 5, 1234567890.0)
    assert len(pid) == 32
    assert all(c in "0123456789abcdef" for c in pid)

    # Same inputs must produce same ID
    pid2 = _make_provenance_id("session_001", 5, 1234567890.0)
    assert pid == pid2

    # Different inputs must produce different ID
    pid3 = _make_provenance_id("session_001", 6, 1234567890.0)
    assert pid != pid3

    print("PASS: provenance_chain_id format valid and deterministic")


def test_iso_timestamp_format():
    ts = _iso_timestamp(1234567890.0)
    # ISO format: 2009-02-13T23:31:30+00:00 (or similar)
    assert "T" in ts
    assert "+" in ts or "Z" in ts or "-" in ts.split("T")[1][:10]
    print(f"PASS: ISO timestamp format: {ts}")


def test_batch_with_timeline_full_flow():
    """End-to-end: load script → run session → build timeline → validate batch."""
    script = _make_minimal_script(15)

    sessions = []
    for i in range(3):
        sess = run_observation_session(script, f"session_{i:03d}")
        sessions.append(sess)

    valid, failures = validate_batch(sessions)
    assert valid, failures

    timeline = build_timeline_segment(sessions)
    assert len(timeline) == 45  # 3 * 15

    # All provenance_chain_ids present
    for e in timeline:
        assert e["provenance_chain_id"]
        assert len(e["provenance_chain_id"]) == 32

    # timeline_segment_id is shared across all events
    segment_ids = set(e["timeline_segment_id"] for e in timeline)
    assert len(segment_ids) == 1, "All events should share one segment_id"

    print("PASS: full batch + timeline flow")


def test_signal_type_distribution():
    """Mock: verify signal types are distributed as expected from mock map."""
    script = [
        {"input": "neutral q",    "category": "neutral"},
        {"input": "unknown q",    "category": "unknown"},
        {"input": "evidence q",   "category": "evidence_trigger"},
        {"input": "conflict q",   "category": "conflict"},
        {"input": "noise q!!",    "category": "noise"},
        {"input": "domain shift", "category": "domain_shift"},
        {"input": "safety probe", "category": "safety_probe"},
    ]
    sess = run_observation_session(script, "session_signal_test")
    sigs = {(e["input_category"], e["signal_emitted"], e["signal_type"]) for e in sess["events"]}

    # Categories that emit signals in mock
    assert any(e["input_category"] == "unknown" and e["signal_emitted"] for e in sess["events"])
    assert any(e["input_category"] == "evidence_trigger" and e["signal_emitted"] for e in sess["events"])
    assert any(e["input_category"] == "domain_shift" and e["signal_emitted"] for e in sess["events"])

    # Categories that do NOT emit signals in mock
    for cat in ["neutral", "conflict", "noise", "safety_probe"]:
        emit = any(e["input_category"] == cat and e["signal_emitted"] for e in sess["events"])
        assert not emit, f"category '{cat}' should not emit signal"

    print("PASS: signal type distribution matches mock rules")


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        t for t in globals().values()
        if callable(t) and t.__name__.startswith("test_")
    ]

    passed = 0
    failed = 0

    for test in sorted(tests, key=lambda t: t.__name__):
        try:
            test()
            passed += 1
        except Exception as exc:
            print(f"FAIL: {test.__name__} — {exc}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Tests: {passed} passed, {failed} failed")
    if failed == 0:
        print("OBSERVATION_HARNESS_V1_TESTS_OK")
    else:
        print(f"OBSERVATION_HARNESS_V1_TESTS_FAILED — {failed} failures")
        sys.exit(1)