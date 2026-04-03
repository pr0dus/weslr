"""Continuity Orchestrator v1 Phase 1 — WESLR anchored test script."""

import json
import sys
import os

sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from continuity_orchestrator import (
    build_snapshot,
    save_snapshot,
    load_snapshot,
    list_snapshots,
    calculate_confidence,
    calculate_continuity_debt,
    build_restore_plan,
    restore_from_plan,
    get_current_snapshot_info,
    load_weslr_continuity_state,
    should_attempt_restore,
    check_restore_conditions,
    apply_partial_restore,
    RESTORE_NO_RESTORE,
    RESTORE_PARTIAL_RESTORE,
    RESTORE_BLOCKED,
    RESTORE_SKIPPED_STALE,
)


def test_weslr_state_loading():
    """Test loading real WESLR continuity state."""
    print("=== Test: WESLR Continuity State Loading ===")

    state = load_weslr_continuity_state()

    assert "identity_anchor" in state
    assert "communicator_continuity" in state
    assert "session_continuity" in state
    assert "unresolved_shared_threads" in state
    assert "opportunity_board" in state
    assert "categories" in state
    assert "review_queue" in state
    assert "export_queue" in state
    assert "operator_work" in state  # New field

    print(f"✓ Loaded WESLR state: identity_anchor={state.get('identity_anchor')}")
    print(f"  operator_work items={len(state.get('operator_work', []))}")
    return state


def test_snapshot_fields():
    """Test snapshot includes only WESLR continuity fields."""
    print("\n=== Test: Snapshot Fields (WESLR anchored) ===")

    state = load_weslr_continuity_state()
    snapshot = build_snapshot("test-weslr-001", state)

    # Verify exact fields
    required = [
        "session_id",
        "timestamp",
        "identity_anchor",
        "communicator_continuity",
        "session_continuity",
        "unresolved_shared_threads",
        "opportunity_board",
        "categories",
        "review_queue",
        "export_queue",
        "operator_work",
        "continuity_markers",
        "restore_plan",
    ]
    for field in required:
        assert field in snapshot, f"Missing field: {field}"

    # continuity_markers must contain confidence, debt, fields
    cm = snapshot["continuity_markers"]
    assert "confidence" in cm
    assert "debt" in cm
    assert "fields" in cm

    # restore_plan must target WESLR fields including operator_work
    rp = snapshot["restore_plan"]
    assert "strategy" in rp
    assert rp["strategy"] == "continuity_preservation"
    assert "continuity_fields" in rp
    assert "operator_work" in rp["continuity_fields"]

    print(f"✓ Snapshot has all WESLR continuity fields (9 fields)")
    print(f"  confidence={cm['confidence']}, debt={cm['debt']}")
    return snapshot


def test_confidence_debt():
    """Test confidence/debt uses WESLR continuity signals."""
    print("\n=== Test: Confidence / Debt (WESLR model) ===")

    state = load_weslr_continuity_state()

    conf = calculate_confidence(state)
    debt = calculate_continuity_debt(state)

    # These must be derived from WESLR signals, not generic
    print(f"✓ WESLR confidence={conf}, debt={debt}")
    assert 0 <= conf <= 100
    assert 0 <= debt <= 100

    # Test with degraded state
    degraded = state.copy()
    degraded["unresolved_shared_threads"] = ["thread1", "thread2", "thread3"]
    degraded["review_queue"] = [{"id": "r1"}]
    degraded["identity_anchor"] = None

    conf2 = calculate_confidence(degraded)
    debt2 = calculate_continuity_debt(degraded)

    assert conf2 < conf
    assert debt2 > debt
    print(f"✓ Degraded state: confidence={conf2}, debt={debt2} (sanity check)")


def test_restore_plan():
    """Test restore plan targets WESLR continuity fields."""
    print("\n=== Test: Restore Plan (WESLR fields) ===")

    state = load_weslr_continuity_state()
    plan = build_restore_plan(state)

    assert plan["strategy"] == "continuity_preservation"
    assert plan["fallback"] == "state_core_restore"
    assert len(plan["continuity_fields"]) == 9  # Including operator_work

    for key in plan["continuity_fields"]:
        found = any(item["key"] == key for item in plan["items"])
        assert found, f"Missing in items: {key}"

    print(f"✓ Restore plan targets all 9 WESLR continuity fields")

    result = restore_from_plan({"session_id": "test", "restore_plan": plan}, dry_run=True)
    assert result["fields"] == plan["continuity_fields"]
    print(f"✓ Dry-run restore executed")


def test_restore_decision_logic():
    """Test restore decision logic and conservative partial restore."""
    print("\n=== Test: Restore Decision Logic (v1) ===")

    # Test should_attempt_restore
    should = should_attempt_restore()
    print(f"✓ should_attempt_restore: {should} (state_core validity check)")

    # Test check_restore_conditions
    decision = check_restore_conditions()
    assert "decision" in decision
    assert "reason" in decision
    print(f"✓ check_restore_conditions: {decision['decision']} - {decision['reason']}")

    # Test apply_partial_restore
    result = apply_partial_restore()
    assert "status" in result
    assert "fields_restored" in result
    print(f"✓ apply_partial_restore: status={result['status']}")
    if result["status"] == "success":
        print(f"  Restored: {result['fields_restored']}")
    elif result["status"] == "skipped":
        print(f"  Skipped: {result.get('reason', 'unknown')}")

    # Test decision constants
    assert RESTORE_NO_RESTORE == "no_restore"
    assert RESTORE_PARTIAL_RESTORE == "partial_restore"
    assert RESTORE_BLOCKED == "restore_blocked"
    assert RESTORE_SKIPPED_STALE == "restore_skipped_stale"
    print(f"✓ Restore decision constants verified")


def run_all_tests():
    """Run all tests."""
    print("Continuity Orchestrator v1 Phase 1+2+3 — WESLR Anchored Test Suite")
    print("=" * 60)

    test_weslr_state_loading()
    test_snapshot_fields()
    test_confidence_debt()
    test_restore_plan()
    test_restore_decision_logic()

    print("\n" + "=" * 60)
    print("All tests passed ✓")


if __name__ == "__main__":
    run_all_tests()
