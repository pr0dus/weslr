"""
WESLR Pattern Comparison Layer V1 — Tests

Tests:
- new pattern
- disappearing pattern
- stable pattern
- strengthening pattern
- weakening pattern
- pattern_id matching
- no pressure category fields present
- no recommendation fields present
- deterministic output
- no-write proof
- empty previous/current handling
"""

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from weslr.pattern_comparison import (
    compare_pattern_runs,
    ComparisonResult,
    PatternComparison,
    _compute_confidence,
    _classify_status,
)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def pat(
    pattern_id: str,
    signal_type: str = "S1",
    topic: str = "topic_x",
    frequency: int = 1,
    session_diversity: int = 1,
    consistency: float = 0.8,
) -> dict:
    return {
        "pattern_id": pattern_id,
        "signal_type": signal_type,
        "topic_normalized": topic,
        "frequency": frequency,
        "session_diversity": session_diversity,
        "consistency": consistency,
    }


# ----------------------------------------------------------------------
# Status Classification
# ----------------------------------------------------------------------

def test_new_pattern():
    """Pattern only in current → status = new."""
    prev = []
    curr = [pat("aaa", frequency=3, session_diversity=2, consistency=0.7)]
    result = compare_pattern_runs(prev, curr)

    assert len(result.comparisons) == 1
    c = result.comparisons[0]
    assert c.status == "new"
    assert c.pattern_id == "aaa"
    assert c.frequency_delta == 3
    print("test_new_pattern: PASS")


def test_disappearing_pattern():
    """Pattern only in previous → status = disappearing."""
    prev = [pat("aaa", frequency=3, session_diversity=2, consistency=0.7)]
    curr = []
    result = compare_pattern_runs(prev, curr)

    assert len(result.comparisons) == 1
    c = result.comparisons[0]
    assert c.status == "disappearing"
    assert c.pattern_id == "aaa"
    assert c.frequency_delta == -3
    print("test_disappearing_pattern: PASS")


def test_stable_pattern():
    """Small deltas → status = stable."""
    prev = [pat("aaa", frequency=5, session_diversity=3, consistency=0.7)]
    curr = [pat("aaa", frequency=5, session_diversity=3, consistency=0.72)]
    result = compare_pattern_runs(prev, curr)

    assert len(result.comparisons) == 1
    c = result.comparisons[0]
    assert c.status == "stable"
    assert c.frequency_delta == 0
    assert abs(c.consistency_delta - 0.02) < 0.001
    print("test_stable_pattern: PASS")


def test_strengthening_pattern():
    """Frequency up + consistency not down → status = strengthening."""
    prev = [pat("aaa", frequency=4, session_diversity=3, consistency=0.6)]
    curr = [pat("aaa", frequency=7, session_diversity=3, consistency=0.75)]
    result = compare_pattern_runs(prev, curr)

    assert len(result.comparisons) == 1
    c = result.comparisons[0]
    assert c.status == "strengthening"
    assert c.frequency_delta == 3
    assert c.consistency_delta > 0
    print("test_strengthening_pattern: PASS")


def test_weakening_by_frequency():
    """Frequency dropped → status = weakening."""
    prev = [pat("aaa", frequency=8, session_diversity=3, consistency=0.8)]
    curr = [pat("aaa", frequency=3, session_diversity=3, consistency=0.8)]
    result = compare_pattern_runs(prev, curr)

    assert len(result.comparisons) == 1
    c = result.comparisons[0]
    assert c.status == "weakening"
    assert c.frequency_delta == -5
    print("test_weakening_by_frequency: PASS")


def test_weakening_by_consistency_drop():
    """Consistency dropped >0.15 → status = weakening even if frequency stable."""
    prev = [pat("aaa", frequency=5, session_diversity=3, consistency=0.8)]
    curr = [pat("aaa", frequency=5, session_diversity=3, consistency=0.5)]
    result = compare_pattern_runs(prev, curr)

    assert len(result.comparisons) == 1
    c = result.comparisons[0]
    assert c.status == "weakening"
    assert c.consistency_delta == -0.3
    print("test_weakening_by_consistency_drop: PASS")


def test_stable_when_consistency_slightly_down():
    """Consistency drop <0.15 and frequency flat → stable."""
    prev = [pat("aaa", frequency=5, session_diversity=3, consistency=0.8)]
    curr = [pat("aaa", frequency=5, session_diversity=3, consistency=0.7)]
    result = compare_pattern_runs(prev, curr)

    assert len(result.comparisons) == 1
    c = result.comparisons[0]
    assert c.status == "stable"
    print("test_stable_when_consistency_slightly_down: PASS")


# ----------------------------------------------------------------------
# Pattern ID Matching
# ----------------------------------------------------------------------

def test_pattern_id_matching():
    """Same pattern_id across runs is compared correctly."""
    prev = [pat("aaa", frequency=3, session_diversity=2, consistency=0.6)]
    curr = [pat("aaa", frequency=5, session_diversity=2, consistency=0.7)]
    result = compare_pattern_runs(prev, curr)

    assert len(result.comparisons) == 1
    assert result.comparisons[0].pattern_id == "aaa"
    assert result.comparisons[0].frequency_delta == 2
    print("test_pattern_id_matching: PASS")


def test_multiple_patterns_all_matched():
    """Multiple patterns in both runs → all matched correctly."""
    prev = [
        pat("aaa", signal_type="S1", frequency=3, consistency=0.6),
        pat("bbb", signal_type="S2", frequency=5, consistency=0.7),
        pat("ccc", signal_type="S1", frequency=2, consistency=0.5),
    ]
    curr = [
        pat("aaa", signal_type="S1", frequency=6, consistency=0.8),
        pat("bbb", signal_type="S2", frequency=3, consistency=0.5),
    ]
    result = compare_pattern_runs(prev, curr)

    assert len(result.comparisons) == 3
    by_id = {c.pattern_id: c for c in result.comparisons}

    assert by_id["aaa"].status == "strengthening"
    assert by_id["bbb"].status == "weakening"
    assert by_id["ccc"].status == "disappearing"
    print("test_multiple_patterns_all_matched: PASS")


def test_pattern_id_not_matched_by_signal_type():
    """Same signal_type + topic, different pattern_id → separate patterns."""
    prev = [pat("aaa", signal_type="S1", topic="topic_x", frequency=3)]
    curr = [pat("bbb", signal_type="S1", topic="topic_x", frequency=5)]
    result = compare_pattern_runs(prev, curr)

    # Different pattern_ids — both should appear as new/disappearing
    assert len(result.comparisons) == 2
    statuses = {c.pattern_id: c.status for c in result.comparisons}
    assert statuses["aaa"] == "disappearing"
    assert statuses["bbb"] == "new"
    print("test_pattern_id_not_matched_by_signal_type: PASS")


# ----------------------------------------------------------------------
# No Pressure Category Fields
# ----------------------------------------------------------------------

def test_no_pressure_category_in_output():
    """Comparison output must not contain pressure category fields."""
    prev = [pat("aaa")]
    curr = [pat("aaa", frequency=5, consistency=0.9)]
    result = compare_pattern_runs(prev, curr)

    for c in result.comparisons:
        d = c.__dict__
        forbidden = ["stability", "optimization", "expansion", "pressure"]
        for key in d:
            if any(f in str(key).lower() for f in forbidden):
                raise AssertionError(f"Forbidden field '{key}' found in comparison output")
        # Also check status values — no pressure terms
        assert c.status in ("new", "stable", "strengthening", "weakening", "disappearing", "unknown")
    print("test_no_pressure_category_in_output: PASS")


def test_no_recommendation_fields():
    """Comparison output must not contain recommendation fields."""
    prev = [pat("aaa")]
    curr = [pat("aaa", frequency=5, consistency=0.9)]
    result = compare_pattern_runs(prev, curr)

    result_dict = result.to_dict()
    forbidden_keys = ["recommend", "action", "proposal", "alert", "priority", "score"]
    json_str = json.dumps(result_dict).lower()
    for key in forbidden_keys:
        if key in json_str:
            raise AssertionError(f"Forbidden keyword '{key}' found in comparison output")
    print("test_no_recommendation_fields: PASS")


# ----------------------------------------------------------------------
# Deterministic Output
# ----------------------------------------------------------------------

def test_deterministic_same_input():
    """Identical inputs → identical output regardless of call order."""
    prev = [pat("aaa", frequency=3, consistency=0.6)]
    curr = [pat("aaa", frequency=5, consistency=0.7)]

    result1 = compare_pattern_runs(prev, curr, "run_a", "run_b")
    result2 = compare_pattern_runs(prev, curr, "run_a", "run_b")

    assert result1.total_previous == result2.total_previous
    assert result1.total_current == result2.total_current
    assert len(result1.comparisons) == len(result2.comparisons)
    for c1, c2 in zip(result1.comparisons, result2.comparisons):
        assert c1.pattern_id == c2.pattern_id
        assert c1.status == c2.status
        assert c1.frequency_delta == c2.frequency_delta
        assert c1.confidence == c2.confidence
    print("test_deterministic_same_input: PASS")


def test_deterministic_order_independent():
    """Pattern order in input does not affect output ordering."""
    prev = [pat("ccc"), pat("aaa"), pat("bbb")]
    curr = [pat("ccc", frequency=2), pat("aaa", frequency=3)]

    result = compare_pattern_runs(prev, curr)
    pattern_ids = [c.pattern_id for c in result.comparisons]

    # Should be sorted alphabetically for determinism
    assert pattern_ids == sorted(pattern_ids)
    print("test_deterministic_order_independent: PASS")


# ----------------------------------------------------------------------
# No-Write Proof
# ----------------------------------------------------------------------

def test_no_file_write():
    """compare_pattern_runs does not write any files."""
    prev = [pat("aaa")]
    curr = [pat("aaa", frequency=3)]

    jsonl_path = "/data/data/com.termux/files/home/.openclaw/workspace/proposal_trace.jsonl"
    checkpoint_path = "/data/data/com.termux/files/home/.openclaw/workspace/state_checkpoint.json"

    hashes_before = {}
    for path in [jsonl_path, checkpoint_path]:
        try:
            with open(path, "rb") as f:
                hashes_before[path] = hashlib.sha256(f.read()).hexdigest()
        except FileNotFoundError:
            hashes_before[path] = None

    result = compare_pattern_runs(prev, curr)

    for path in [jsonl_path, checkpoint_path]:
        try:
            with open(path, "rb") as f:
                h = hashlib.sha256(f.read()).hexdigest()
                if hashes_before[path] is not None:
                    assert h == hashes_before[path], f"{path} was modified"
        except FileNotFoundError:
            assert hashes_before[path] is None, f"{path} was created"

    print("test_no_file_write: PASS")


# ----------------------------------------------------------------------
# Empty Handling
# ----------------------------------------------------------------------

def test_empty_both():
    """Empty previous and current → empty comparisons."""
    result = compare_pattern_runs([], [])
    assert result.comparisons == []
    assert result.total_previous == 0
    assert result.total_current == 0
    print("test_empty_both: PASS")


def test_empty_previous_only():
    """Empty previous → all current patterns are new."""
    curr = [pat("aaa"), pat("bbb")]
    result = compare_pattern_runs([], curr)

    assert len(result.comparisons) == 2
    statuses = {c.pattern_id: c.status for c in result.comparisons}
    assert all(v == "new" for v in statuses.values())
    print("test_empty_previous_only: PASS")


def test_empty_current_only():
    """Empty current → all previous patterns are disappearing."""
    prev = [pat("aaa"), pat("bbb")]
    result = compare_pattern_runs(prev, [])

    assert len(result.comparisons) == 2
    statuses = {c.pattern_id: c.status for c in result.comparisons}
    assert all(v == "disappearing" for v in statuses.values())
    print("test_empty_current_only: PASS")


# ----------------------------------------------------------------------
# Confidence
# ----------------------------------------------------------------------

def test_confidence_new_pattern_high_diversity():
    """New pattern with high session diversity → high confidence."""
    conf = _compute_confidence(session_diversity=5, consistency=0.9, has_previous=False)
    assert conf >= 0.8
    print("test_confidence_new_pattern_high_diversity: PASS")


def test_confidence_new_pattern_low_diversity():
    """New pattern with low session diversity → lower confidence."""
    conf = _compute_confidence(session_diversity=1, consistency=0.5, has_previous=False)
    assert conf < 0.5
    print("test_confidence_new_pattern_low_diversity: PASS")


def test_confidence_existing_pattern():
    """Existing pattern compared → confidence based on diversity + consistency."""
    conf = _compute_confidence(session_diversity=4, consistency=0.9, has_previous=True)
    assert 0.0 <= conf <= 1.0
    print("test_confidence_existing_pattern: PASS")


def test_confidence_clamped():
    """Confidence must be in [0.0, 1.0]."""
    conf_low = _compute_confidence(session_diversity=0, consistency=0.0, has_previous=False)
    conf_high = _compute_confidence(session_diversity=100, consistency=1.0, has_previous=True)
    assert 0.0 <= conf_low <= 1.0
    assert 0.0 <= conf_high <= 1.0
    print("test_confidence_clamped: PASS")


# ----------------------------------------------------------------------
# Delta Calculation
# ----------------------------------------------------------------------

def test_frequency_delta():
    """Frequency delta = current - previous."""
    prev = [pat("aaa", frequency=4)]
    curr = [pat("aaa", frequency=7)]
    result = compare_pattern_runs(prev, curr)
    assert result.comparisons[0].frequency_delta == 3
    print("test_frequency_delta: PASS")


def test_diversity_delta():
    """Session diversity delta = current - previous."""
    prev = [pat("aaa", session_diversity=2)]
    curr = [pat("aaa", session_diversity=5)]
    result = compare_pattern_runs(prev, curr)
    assert result.comparisons[0].diversity_delta == 3
    print("test_diversity_delta: PASS")


def test_consistency_delta():
    """Consistency delta = current - previous."""
    prev = [pat("aaa", consistency=0.6)]
    curr = [pat("aaa", consistency=0.85)]
    result = compare_pattern_runs(prev, curr)
    assert abs(result.comparisons[0].consistency_delta - 0.25) < 0.001
    print("test_consistency_delta: PASS")


# ----------------------------------------------------------------------
# Run ID Tracking
# ----------------------------------------------------------------------

def test_run_ids_preserved():
    """Previous and current run IDs are preserved in output."""
    result = compare_pattern_runs([], [], "run_prev_123", "run_curr_456")
    assert result.previous_run_id == "run_prev_123"
    assert result.current_run_id == "run_curr_456"
    print("test_run_ids_preserved: PASS")


# ----------------------------------------------------------------------
# Run All
# ----------------------------------------------------------------------

def run_all():
    tests = [
        test_new_pattern,
        test_disappearing_pattern,
        test_stable_pattern,
        test_strengthening_pattern,
        test_weakening_by_frequency,
        test_weakening_by_consistency_drop,
        test_stable_when_consistency_slightly_down,
        test_pattern_id_matching,
        test_multiple_patterns_all_matched,
        test_pattern_id_not_matched_by_signal_type,
        test_no_pressure_category_in_output,
        test_no_recommendation_fields,
        test_deterministic_same_input,
        test_deterministic_order_independent,
        test_no_file_write,
        test_empty_both,
        test_empty_previous_only,
        test_empty_current_only,
        test_confidence_new_pattern_high_diversity,
        test_confidence_new_pattern_low_diversity,
        test_confidence_existing_pattern,
        test_confidence_clamped,
        test_frequency_delta,
        test_diversity_delta,
        test_consistency_delta,
        test_run_ids_preserved,
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
        print("WESLR_PATTERN_COMPARISON_LAYER_V1_DEFINED")


if __name__ == "__main__":
    run_all()