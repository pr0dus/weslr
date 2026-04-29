"""
WESLR Signal Pattern Observer V1 — Tests

Tests:
- grouping correctness
- frequency calculation
- session diversity calculation
- time span calculation
- deterministic output
- no-write proof
"""

import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from weslr.signal_pattern_observer import (
    RawSignal,
    PatternGroup,
    group_signals,
    calculate_pattern_metrics,
    observe_patterns,
    _normalize_signal_type,
    _make_pattern_id,
)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def sig(
    signal_type: str,
    session_id: str,
    timestamp: float,
    topic: str | None = None,
    **kwargs,
) -> dict:
    d = {
        "signal_type": signal_type,
        "session_id": session_id,
        "timestamp": timestamp,
        "signal_id": f"{signal_type}_{session_id}_{timestamp}",
    }
    if topic is not None:
        d["topic_normalized"] = topic
    d.update(kwargs)
    return d


# ----------------------------------------------------------------------
# Grouping Correctness
# ----------------------------------------------------------------------

def test_grouping_single_type():
    """Multiple signals of same type and topic → one group."""
    signals = [
        sig("S1", "s1", 1000, "topic_a"),
        sig("S1", "s1", 1001, "topic_a"),
        sig("S1", "s2", 1002, "topic_a"),
    ]
    raw = [RawSignal.from_dict(s) for s in signals]
    groups = group_signals(raw)

    assert len(groups) == 1
    assert groups[0].signal_type == "S1"
    assert groups[0].topic_normalized == "topic_a"
    print("test_grouping_single_type: PASS")


def test_grouping_multiple_types():
    """Different signal types → separate groups."""
    signals = [
        sig("S1", "s1", 1000, "topic_a"),
        sig("S2", "s1", 1001, "topic_a"),
        sig("S1", "s1", 1002, "topic_b"),
    ]
    raw = [RawSignal.from_dict(s) for s in signals]
    groups = group_signals(raw)

    assert len(groups) == 3
    types = {g.signal_type for g in groups}
    assert types == {"S1", "S2"}
    topics = {g.topic_normalized for g in groups}
    assert topics == {"topic_a", "topic_b"}
    print("test_grouping_multiple_types: PASS")


def test_grouping_different_topics():
    """Same signal type, different topics → separate groups."""
    signals = [
        sig("S1", "s1", 1000, "topic_a"),
        sig("S1", "s1", 1001, "topic_b"),
        sig("S1", "s1", 1002, "topic_a"),
    ]
    raw = [RawSignal.from_dict(s) for s in signals]
    groups = group_signals(raw)

    assert len(groups) == 2
    topic_groups = {g.topic_normalized: g for g in groups}
    assert topic_groups["topic_a"].frequency == 2
    assert topic_groups["topic_b"].frequency == 1
    print("test_grouping_different_topics: PASS")


# ----------------------------------------------------------------------
# Frequency Calculation
# ----------------------------------------------------------------------

def test_frequency_single_session():
    """All signals from one session → frequency = count."""
    signals = [
        sig("S1", "s1", 1000, "topic_a"),
        sig("S1", "s1", 1001, "topic_a"),
        sig("S1", "s1", 1002, "topic_a"),
        sig("S1", "s1", 1003, "topic_a"),
    ]
    raw = [RawSignal.from_dict(s) for s in signals]
    groups = group_signals(raw)

    assert len(groups) == 1
    assert groups[0].frequency == 4
    print("test_frequency_single_session: PASS")


def test_frequency_multiple_sessions():
    """Signals from multiple sessions → frequency = total count."""
    signals = [
        sig("S1", "s1", 1000, "topic_a"),
        sig("S1", "s2", 1001, "topic_a"),
        sig("S1", "s3", 1002, "topic_a"),
    ]
    raw = [RawSignal.from_dict(s) for s in signals]
    groups = group_signals(raw)

    assert len(groups) == 1
    assert groups[0].frequency == 3
    print("test_frequency_multiple_sessions: PASS")


# ----------------------------------------------------------------------
# Session Diversity Calculation
# ----------------------------------------------------------------------

def test_session_diversity_single():
    """All signals from same session → diversity = 1."""
    signals = [
        sig("S1", "s1", 1000, "topic_a"),
        sig("S1", "s1", 1001, "topic_a"),
        sig("S1", "s1", 1002, "topic_a"),
    ]
    raw = [RawSignal.from_dict(s) for s in signals]
    groups = group_signals(raw)

    assert groups[0].session_diversity == 1
    print("test_session_diversity_single: PASS")


def test_session_diversity_multiple():
    """Signals from multiple sessions → unique session count."""
    signals = [
        sig("S1", "s1", 1000, "topic_a"),
        sig("S1", "s2", 1001, "topic_a"),
        sig("S1", "s1", 1002, "topic_a"),
        sig("S1", "s3", 1003, "topic_a"),
        sig("S1", "s2", 1004, "topic_a"),
    ]
    raw = [RawSignal.from_dict(s) for s in signals]
    groups = group_signals(raw)

    assert groups[0].session_diversity == 3  # s1, s2, s3
    print("test_session_diversity_multiple: PASS")


def test_session_diversity_dedup():
    """Same session repeated → deduplicated in diversity count."""
    signals = [
        sig("S1", "s1", 1000, "topic_a"),
        sig("S1", "s1", 1001, "topic_a"),
        sig("S1", "s1", 1002, "topic_a"),
        sig("S1", "s2", 1003, "topic_a"),
    ]
    raw = [RawSignal.from_dict(s) for s in signals]
    groups = group_signals(raw)

    assert groups[0].session_diversity == 2  # s1, s2 — s1 counted once
    print("test_session_diversity_dedup: PASS")


# ----------------------------------------------------------------------
# Time Span Calculation
# ----------------------------------------------------------------------

def test_time_span_single_signal():
    """Single signal → time_span = 0."""
    signals = [sig("S1", "s1", 1000, "topic_a")]
    raw = [RawSignal.from_dict(s) for s in signals]
    groups = group_signals(raw)

    assert groups[0].time_span == 0.0
    print("test_time_span_single_signal: PASS")


def test_time_span_multiple_signals():
    """Multiple signals → time_span = last - first."""
    signals = [
        sig("S1", "s1", 1000, "topic_a"),
        sig("S1", "s1", 1050, "topic_a"),
        sig("S1", "s1", 1100, "topic_a"),
    ]
    raw = [RawSignal.from_dict(s) for s in signals]
    groups = group_signals(raw)

    assert groups[0].time_span == 100.0
    print("test_time_span_multiple_signals: PASS")


def test_time_span_out_of_order():
    """Signals with timestamps not in order → still correct (sorted internally)."""
    signals = [
        sig("S1", "s1", 1100, "topic_a"),
        sig("S1", "s1", 1000, "topic_a"),
        sig("S1", "s1", 1050, "topic_a"),
    ]
    raw = [RawSignal.from_dict(s) for s in signals]
    groups = group_signals(raw)

    assert groups[0].time_span == 100.0  # 1100 - 1000
    print("test_time_span_out_of_order: PASS")


# ----------------------------------------------------------------------
# Consistency Calculation
# ----------------------------------------------------------------------

def test_consistency_single_session_repeated():
    """Same session repeated → high consistency."""
    signals = [
        sig("S1", "s1", 1000, "topic_a"),
        sig("S1", "s1", 1001, "topic_a"),
        sig("S1", "s1", 1002, "topic_a"),
    ]
    raw = [RawSignal.from_dict(s) for s in signals]
    groups = group_signals(raw)

    # Single session, low time span → consistency close to 1.0
    assert groups[0].consistency >= 0.9
    print("test_consistency_single_session_repeated: PASS")


def test_consistency_spread_across_sessions():
    """Signals spread over many sessions with wide time span → lower consistency."""
    signals = [
        sig("S1", "s1", 1000000, "topic_a"),
        sig("S1", "s2", 2000000, "topic_a"),
        sig("S1", "s3", 3000000, "topic_a"),
        sig("S1", "s4", 9000000, "topic_a"),  # 100-day span normalizes time_span
    ]
    raw = [RawSignal.from_dict(s) for s in signals]
    groups = group_signals(raw)

    # High diversity (4) relative to frequency (4), large time span → lower consistency
    assert groups[0].consistency < 0.5
    print("test_consistency_spread_across_sessions: PASS")


# ----------------------------------------------------------------------
# Deterministic Output
# ----------------------------------------------------------------------

def test_deterministic_same_input():
    """Identical inputs → identical outputs regardless of call order."""
    signals = [
        sig("S1", "s1", 1000, "topic_a"),
        sig("S1", "s2", 1001, "topic_a"),
    ]

    result1 = observe_patterns(signals, "session_a")
    result2 = observe_patterns(signals, "session_a")

    assert result1.total_signals_observed == result2.total_signals_observed
    assert len(result1.patterns) == len(result2.patterns)

    for g1, g2 in zip(result1.patterns, result2.patterns):
        assert g1.pattern_id == g2.pattern_id
        assert g1.frequency == g2.frequency
        assert g1.session_diversity == g2.session_diversity
    print("test_deterministic_same_input: PASS")


def test_deterministic_pattern_id():
    """Same type + topic → same pattern_id across runs."""
    sig_a = sig("S1", "s1", 1000, "topic_a")
    sig_b = sig("S1", "s2", 2000, "topic_a")

    raw_a = [RawSignal.from_dict(sig_a)]
    raw_b = [RawSignal.from_dict(sig_b)]

    groups_a = group_signals(raw_a)
    groups_b = group_signals(raw_b)

    assert groups_a[0].pattern_id == groups_b[0].pattern_id
    print("test_deterministic_pattern_id: PASS")


def test_different_topics_different_ids():
    """Same signal type, different topics → different pattern_ids."""
    signals = [
        sig("S1", "s1", 1000, "topic_a"),
        sig("S1", "s1", 1001, "topic_b"),
    ]
    raw = [RawSignal.from_dict(s) for s in signals]
    groups = group_signals(raw)

    assert groups[0].pattern_id != groups[1].pattern_id
    print("test_different_topics_different_ids: PASS")


# ----------------------------------------------------------------------
# No-Write Proof
# ----------------------------------------------------------------------

def test_no_file_write():
    """observe_patterns does not write any files."""
    signals = [sig("S1", "s1", 1000, "topic_a")]

    jsonl_path = "/data/data/com.termux/files/home/.openclaw/workspace/proposal_trace.jsonl"
    checkpoint_path = "/data/data/com.termux/files/home/.openclaw/workspace/state_checkpoint.json"

    hashes_before = {}
    for path in [jsonl_path, checkpoint_path]:
        try:
            with open(path, "rb") as f:
                hashes_before[path] = hashlib.sha256(f.read()).hexdigest()
        except FileNotFoundError:
            hashes_before[path] = None

    result = observe_patterns(signals, "test_session")

    for path in [jsonl_path, checkpoint_path]:
        try:
            with open(path, "rb") as f:
                h = hashlib.sha256(f.read()).hexdigest()
                if hashes_before[path] is not None:
                    assert h == hashes_before[path], f"{path} was modified"
        except FileNotFoundError:
            assert hashes_before[path] is None, f"{path} was created"

    print("test_no_file_write: PASS")


def test_no_state_carryover():
    """Calling observe_patterns twice with same input produces independent results."""
    signals = [sig("S1", "s1", 1000, "topic_a")]

    result1 = observe_patterns(signals, "session_1")
    result2 = observe_patterns(signals, "session_2")

    # Different session IDs in output
    assert result1.observation_session_id != result2.observation_session_id

    # Patterns are independent — no shared state between calls
    assert len(result1.patterns) == len(result2.patterns)
    print("test_no_state_carryover: PASS")


# ----------------------------------------------------------------------
# Signal Type Normalization
# ----------------------------------------------------------------------

def test_signal_type_normalization():
    """Signal type is normalized to canonical form."""
    assert _normalize_signal_type("S1") == "S1"
    assert _normalize_signal_type("s1") == "S1"
    assert _normalize_signal_type("1") == "S1"
    assert _normalize_signal_type(" s2 ") == "S2"
    print("test_signal_type_normalization: PASS")


# ----------------------------------------------------------------------
# Empty Input
# ----------------------------------------------------------------------

def test_empty_signals():
    """Empty list → empty patterns."""
    result = observe_patterns([], "session_empty")
    assert result.patterns == []
    assert result.total_signals_observed == 0
    print("test_empty_signals: PASS")


def test_metrics_empty():
    """Empty signals → zero metrics."""
    m = calculate_pattern_metrics([])
    assert m["total_signals"] == 0
    assert m["total_sessions"] == 0
    assert m["time_span"] == 0.0
    print("test_metrics_empty: PASS")


# ----------------------------------------------------------------------
# All S Types
# ----------------------------------------------------------------------

def test_all_signal_types():
    """All S1–S6 types are handled correctly."""
    for stype in ["S1", "S2", "S3", "S4", "S5", "S6"]:
        signals = [sig(stype, "s1", 1000, "topic_x")]
        raw = [RawSignal.from_dict(s) for s in signals]
        groups = group_signals(raw)
        assert len(groups) == 1
        assert groups[0].signal_type == stype
    print("test_all_signal_types: PASS")


# ----------------------------------------------------------------------
# Pattern ID Collision Resistance
# ----------------------------------------------------------------------

def test_pattern_id_no_collision():
    """Different (signal_type, topic) pairs produce different pattern IDs."""
    pairs = [
        ("S1", "topic_a"),
        ("S1", "topic_b"),
        ("S2", "topic_a"),
        ("S2", "topic_b"),
    ]
    ids = [_make_pattern_id(s, t) for s, t in pairs]
    assert len(ids) == len(set(ids)), "Pattern ID collision detected"
    print("test_pattern_id_no_collision: PASS")


# ----------------------------------------------------------------------
# Run All
# ----------------------------------------------------------------------

def run_all():
    tests = [
        test_grouping_single_type,
        test_grouping_multiple_types,
        test_grouping_different_topics,
        test_frequency_single_session,
        test_frequency_multiple_sessions,
        test_session_diversity_single,
        test_session_diversity_multiple,
        test_session_diversity_dedup,
        test_time_span_single_signal,
        test_time_span_multiple_signals,
        test_time_span_out_of_order,
        test_consistency_single_session_repeated,
        test_consistency_spread_across_sessions,
        test_deterministic_same_input,
        test_deterministic_pattern_id,
        test_different_topics_different_ids,
        test_no_file_write,
        test_no_state_carryover,
        test_signal_type_normalization,
        test_empty_signals,
        test_metrics_empty,
        test_all_signal_types,
        test_pattern_id_no_collision,
    ]

    passed = 0
    failed = []

    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            failed.append((t.__name__, str(e)))

    print(f"\n{'='*50}")
    if failed:
        print(f"FAILED: {len(failed)}/{len(tests)}")
        for name, err in failed:
            print(f"  {name}: {err}")
        sys.exit(1)
    else:
        print(f"ALL {len(tests)} TESTS PASSED")
        print("WESLR_SIGNAL_PATTERN_OBSERVER_V1_DEFINED")


if __name__ == "__main__":
    run_all()