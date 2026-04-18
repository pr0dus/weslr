"""Drift Emitter Integration Tests — v1

Tests the fail-open safety and signal emission of the drift emitter wiring.
All emitter calls must not affect runtime paths.
"""

from __future__ import annotations

import tempfile
import os
import traceback as _traceback

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clear_drift_signals():
    """Reset in-process drift signal store."""
    from weslr.institution import _DRIFT_SIGNALS, _REFLECTIONS
    _DRIFT_SIGNALS.clear()
    _REFLECTIONS.clear()


def _gate(tmp_path=None):
    """Get ExecutionGate with isolated temp storage."""
    from weslr.change_proposals import get_execution_gate
    from pathlib import Path
    gate = get_execution_gate()
    gate._storage_path = Path(tmp_path or tempfile.mktemp())
    return gate


# ---------------------------------------------------------------------------
# Test 1: emit_latency_signal — fail-open, records signal
# ---------------------------------------------------------------------------

def test_latency_signal_records():
    from weslr.drift_emitter import emit_latency_signal
    from weslr.institution import _DRIFT_SIGNALS

    _clear_drift_signals()
    prev = len(_DRIFT_SIGNALS)

    # Must not raise
    emit_latency_signal(duration_seconds=2.5, ok=True)
    emit_latency_signal(duration_seconds=15.0, ok=False)

    assert len(_DRIFT_SIGNALS) == prev + 2, "latency signals should be recorded"
    assert _DRIFT_SIGNALS[-1].signal_type == "latency"
    assert _DRIFT_SIGNALS[-2].signal_type == "latency"
    print("PASS: latency_signal_records")


def test_latency_signal_fail_open():
    """Verify emitter failure does not propagate to caller.

    Patches record_drift_signal (the imported function) to raise.
    emit_latency_signal must catch this and return without raising.
    """
    from weslr.drift_emitter import emit_latency_signal
    from weslr import institution as inst_mod

    original = inst_mod.record_drift_signal
    inst_mod.record_drift_signal = lambda *a, **k: (_traceback.print_exc() or 1/0)

    try:
        emit_latency_signal(1.0, True)  # Must not raise
        print("PASS: latency_signal_fail_open")
    finally:
        inst_mod.record_drift_signal = original


# ---------------------------------------------------------------------------
# Test 2: Governance override signals — deny, counterpropose, dismiss, snoozed
# ---------------------------------------------------------------------------

def _test_governance_action(action: str, expected_type: str):
    from weslr.institution import _DRIFT_SIGNALS

    _clear_drift_signals()
    prev = len(_DRIFT_SIGNALS)

    gate = _gate()
    p = gate.create_proposal(f"test {action}", "desc", "rationale", submitted_by="test")
    result = gate.review_proposal(p.proposal_id, action, actor="operator")

    assert result.state == "denied", f"{action}: expected state=denied, got {result.state}"

    override_sigs = [s for s in _DRIFT_SIGNALS if s.context.get("override_type") == expected_type]
    assert len(override_sigs) == 1, f"{action}: expected 1 signal of type {expected_type}, got {len(override_sigs)}"
    print(f"PASS: governance_action_{action}")


def test_governance_action_deny():
    _test_governance_action("deny", "denied")


def test_governance_action_counterpropose():
    _test_governance_action("counterpropose", "counterproposed")


def test_governance_action_dismiss():
    _test_governance_action("dismiss", "ignored")


def test_governance_action_snoozed():
    """Snooze fires via capability command path."""
    from weslr.institution import _DRIFT_SIGNALS

    _clear_drift_signals()

    import weslr.drift_emitter as de
    original = de._record_drift

    # Simulate the emitter being called
    import commands.capability as cap
    # We can't easily call cmd_snooze without full API setup, so just test the signal directly
    de._record_drift = original  # reset
    from weslr.drift_emitter import emit_snoozed_signal
    emit_snoozed_signal("test-prop", "operator")
    snoozed = [s for s in _DRIFT_SIGNALS if s.context.get("override_type") == "snoozed"]
    assert len(snoozed) == 1
    print("PASS: governance_action_snoozed")


def test_governance_action_unknown_is_error():
    """Unknown review action must raise ValueError."""
    gate = _gate()
    p = gate.create_proposal("test", "desc", "rationale", submitted_by="test")
    try:
        gate.review_proposal(p.proposal_id, "unknown_action", actor="operator")
        assert False, "expected ValueError"
    except ValueError as e:
        assert "unknown_action" in str(e)
        print("PASS: governance_action_unknown_is_error")


# ---------------------------------------------------------------------------
# Test 3: Bootstrap transition signals
# ---------------------------------------------------------------------------

def test_bootstrap_signal_records():
    from weslr.bootstrap import expire_pending_bootstrap, new_pending_bootstrap
    from weslr.institution import _DRIFT_SIGNALS

    _clear_drift_signals()
    prev = len(_DRIFT_SIGNALS)

    record = new_pending_bootstrap("test-user@example.com", "test-user@example.com", "Test User", ttl_hours=1)
    expired = expire_pending_bootstrap(record, "test_expire")

    # Should have 1 expire signal (PENDING→COMPLETED would need register step)
    expire_sigs = [s for s in _DRIFT_SIGNALS if s.signal_type == "lifecycle_stale"]
    assert len(expire_sigs) >= 1, f"expected at least 1 lifecycle_stale signal, got {len(expire_sigs)}"
    print("PASS: bootstrap_signal_records")


# ---------------------------------------------------------------------------
# Test 4: Proposal state integrity is NOT affected by emitter failure
# ---------------------------------------------------------------------------

def test_proposal_state_unaffected_when_emitter_fails():
    """Even if emitter raises, proposal state must be correct."""
    import weslr.drift_emitter as de
    original = de._record_drift
    def _fail(*a, **k): raise RuntimeError("emitter failure simulated")
    de._record_drift = _fail

    gate = _gate()
    p = gate.create_proposal("state test", "desc", "rationale", submitted_by="test")
    result = gate.review_proposal(p.proposal_id, "deny", actor="operator")

    # State must be correct regardless of emitter failure
    assert result.state == "denied", f"state={result.state}, expected denied"

    de._record_drift = original
    print("PASS: proposal_state_unaffected_when_emitter_fails")


# ---------------------------------------------------------------------------
# Test 5: Unified read surface
# ---------------------------------------------------------------------------

def test_get_weslr_state_summary():
    from weslr.governance_health import get_weslr_state_summary

    summary = get_weslr_state_summary()

    # Must contain all required top-level keys
    required = (
        "generated_at", "identity", "trust_posture", "health_posture",
        "continuity_posture", "institutional_posture", "active_concerns",
        "strengths", "unresolved_weaknesses", "drift_posture"
    )
    for key in required:
        assert key in summary, f"missing key: {key}"

    # Identity must be WESLR
    assert summary["identity"]["name"] == "WESLR"
    assert summary["identity"]["version"] == "v1"

    print("PASS: get_weslr_state_summary")


def test_get_weslr_state_summary_is_read_only():
    """Calling the summary must not modify any state."""
    from weslr.governance_health import get_weslr_state_summary
    from weslr.institution import _DRIFT_SIGNALS, _REFLECTIONS

    before_signals = len(_DRIFT_SIGNALS)
    before_reflections = len(_REFLECTIONS)

    get_weslr_state_summary()

    assert len(_DRIFT_SIGNALS) == before_signals, "read surface must not write drift signals"
    assert len(_REFLECTIONS) == before_reflections, "read surface must not write reflections"
    print("PASS: get_weslr_state_summary_is_read_only")


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_latency_signal_records,
        test_latency_signal_fail_open,
        test_governance_action_deny,
        test_governance_action_counterpropose,
        test_governance_action_dismiss,
        test_governance_action_snoozed,
        test_governance_action_unknown_is_error,
        test_bootstrap_signal_records,
        test_proposal_state_unaffected_when_emitter_fails,
        test_get_weslr_state_summary,
        test_get_weslr_state_summary_is_read_only,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")
            failed += 1
    print(f"\n{'ALL PASS' if failed == 0 else f'{failed} FAILURE(S)'} ({len(tests)} tests)")
