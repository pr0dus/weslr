#!/usr/bin/env python3
"""
WESLR OmniChat Runtime V1 — Tests
Validates:
  1. "what is WESLR" → guided path
  2. "show system overview" → deterministic path
  3. "convert iss suggestion iss.not_integrated" in public_demo_readonly → blocked_write
  4. "Hey" in public_demo_readonly → fallback with helpful text
  5. Public readiness tests pass
  6. Release gate passes

Confirms: OMNICHAT_RUNTIME_V1_OK
Exits non-zero on any failure.
"""

import sys
import pathlib

_workspace = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_workspace))
sys.path.insert(0, str(_workspace / "weslr"))

# Apply public_demo_readonly mode before any other imports
import interpretation

interpretation.set_weslr_mode("public_demo_readonly")

from interpretation import interpret_human_turn, _WESLR_MODE


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _run(label: str, message: str, *, mode: str = "public_demo_readonly", assertions: list) -> bool:
    """Run one test case. Returns True if passed."""
    interpretation.set_weslr_mode(mode)
    try:
        resp = interpret_human_turn(message)
    except Exception as e:
        print(f"  FAIL [{label}]: raised {type(e).__name__}: {e}")
        return False
    errors = []
    for key, expected, check in assertions:
        actual = resp.get(key)
        if not check(actual, expected):
            errors.append(f"  FAIL [{label}]: {key}={actual!r}, expected {expected!r}")
    if errors:
        for e in errors:
            print(e)
        return False
    print(f"  PASS [{label}]")
    return True


def _has_text(resp: dict, text: str) -> bool:
    return text in (resp.get("response_text") or "")


def _path_equals(actual, expected):
    return actual == expected


# ─── Test 1 ───────────────────────────────────────────────────────────────────

def test_what_is_weslr():
    print("\n[T1] 'what is WESLR' → guided response")
    interpretation.set_weslr_mode("public_demo_readonly")
    resp = interpret_human_turn("what is WESLR")
    policy = resp.get("_omnichat_policy", {})
    ok_path = resp.get("path") == "system_definition_query"
    ok_policy = policy.get("final_response_type") == "guided"
    ok_omnichat = "_omnichat_policy" in resp
    ok_expanded = "expanded_response" in resp
    ok_exp_guidance = bool(resp.get("expanded_response", {}).get("guidance"))
    if not (ok_path and ok_policy and ok_omnichat and ok_expanded and ok_exp_guidance):
        print(f"  FAIL: path={resp.get('path')}, type={policy.get('final_response_type')}")
        print(f"        _omnichat_policy={ok_omnichat}, expanded={ok_expanded}, guidance={ok_exp_guidance}")
        return False
    print("  PASS [T1]")
    return True


# ─── Test 2 ───────────────────────────────────────────────────────────────────

def test_show_system_overview():
    print("\n[T2] 'show system overview' → deterministic response")
    interpretation.set_weslr_mode("public_demo_readonly")
    resp = interpret_human_turn("show system overview")
    policy = resp.get("_omnichat_policy", {})
    ok_path = resp.get("path") == "operator_overview"
    ok_policy = policy.get("final_response_type") == "deterministic"
    ok_omnichat = "_omnichat_policy" in resp
    ok_expanded = "expanded_response" in resp
    if not (ok_path and ok_policy and ok_omnichat and ok_expanded):
        print(f"  FAIL: path={resp.get('path')}, type={policy.get('final_response_type')}")
        print(f"        _omnichat_policy={ok_omnichat}, expanded={ok_expanded}")
        return False
    print("  PASS [T2]")
    return True


# ─── Test 3 ───────────────────────────────────────────────────────────────────

def test_blocked_write_public_demo():
    print("\n[T3] 'convert iss suggestion iss.not_integrated' in public_demo_readonly → blocked_write")
    interpretation.set_weslr_mode("public_demo_readonly")
    resp = interpret_human_turn("convert iss suggestion iss.not_integrated")
    policy = resp.get("_omnichat_policy", {})
    ok_path = resp.get("path") == "blocked_write"
    ok_policy = policy.get("final_response_type") == "blocked_write"
    ok_no_write_confirmed = resp.get("write_confirmed") is not True
    if not (ok_path and ok_policy and ok_no_write_confirmed):
        print(f"  FAIL: path={resp.get('path')}, type={policy.get('final_response_type')}")
        print(f"        write_confirmed={resp.get('write_confirmed')}")
        return False
    print("  PASS [T3]")
    return True


# ─── Test 4 ───────────────────────────────────────────────────────────────────

def test_fallback_hey():
    print("\n[T4] 'Hey' in public_demo_readonly → fallback with helpful text")
    interpretation.set_weslr_mode("public_demo_readonly")
    resp = interpret_human_turn("Hey")
    policy = resp.get("_omnichat_policy", {})
    ok_path = resp.get("path") == "fallback_safe"
    ok_policy = policy.get("final_response_type") == "fallback"
    ok_text = (
        "what is WESLR" in (resp.get("response_text") or "")
        or "show system" in (resp.get("response_text") or "")
    )
    if not (ok_path and ok_policy and ok_text):
        print(f"  FAIL: path={resp.get('path')}, type={policy.get('final_response_type')}")
        print(f"        response_text={resp.get('response_text')[:100]!r}")
        return False
    print("  PASS [T4]")
    return True


# ─── Test 5: public readiness ─────────────────────────────────────────────────

def test_public_readiness():
    print("\n[T5] Running public_readiness_tests.py ...")
    import subprocess
    result = subprocess.run(
        [sys.executable, "weslr/tests/public_readiness_tests.py"],
        cwd=_workspace,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  FAIL [T5]: public_readiness_tests.py exited {result.returncode}")
        if result.stdout:
            print(result.stdout[-500:])
        if result.stderr:
            print(result.stderr[-500:])
        return False
    print("  PASS [T5]")
    return True


# ─── Test 6: release gate ─────────────────────────────────────────────────────

def test_release_gate():
    print("\n[T6] Running release_gate_v1.py ...")
    import subprocess
    result = subprocess.run(
        [sys.executable, "weslr/tests/release_gate_v1.py"],
        cwd=_workspace,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  FAIL [T6]: release_gate_v1.py exited {result.returncode}")
        if result.stdout:
            print(result.stdout[-500:])
        if result.stderr:
            print(result.stderr[-500:])
        return False
    print("  PASS [T6]")
    return True


# ─── Test 7: no-write proof ───────────────────────────────────────────────────

def test_no_write_proof():
    print("\n[T7] JSONL no-write proof (before vs after) ...")
    import json, hashlib
    from pathlib import Path

    jsonl_files = [
        _workspace / "weslr" / "proposal_trace.jsonl",
        _workspace / "weslr" / "implementation_plans.jsonl",
        _workspace / "weslr" / "iss_diagnostic_records.jsonl",
    ]

    def _hash(p: Path) -> str:
        if not p.exists():
            return "absent"
        return hashlib.md5(p.read_bytes()).hexdigest()

    before = {p.name: _hash(p) for p in jsonl_files}

    # Run a set of diverse queries
    interpretation.set_weslr_mode("public_demo_readonly")
    for msg in [
        "show system overview",
        "show diagnostics",
        "show iss probes",
        "what is WESLR",
        "how is WESLR different",
        "show proposals",
        "show capabilities",
        "Hey",
        "show implementation plans",
        "show state checkpoint",
    ]:
        interpret_human_turn(msg)

    after = {p.name: _hash(p) for p in jsonl_files}
    mismatches = [(n, b, a) for n, (b, a) in zip(jsonl_files, [(before[p.name], after[p.name]) for p in jsonl_files]) if b != a]
    if mismatches:
        for name, b, a in mismatches:
            print(f"  FAIL [T7]: {name} changed: {b} → {a}")
        return False
    print("  PASS [T7]")
    return True


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("WESLR OMNICHAT RUNTIME V1 TESTS")
    print("=" * 60)

    # Reset to public_demo_readonly for all tests
    interpretation.set_weslr_mode("public_demo_readonly")

    results = []

    results.append(("T1 what-is-weslr",      test_what_is_weslr()))
    results.append(("T2 show-system",        test_show_system_overview()))
    results.append(("T3 blocked-write",       test_blocked_write_public_demo()))
    results.append(("T4 fallback-hey",        test_fallback_hey()))
    results.append(("T5 public-readiness",    test_public_readiness()))
    results.append(("T6 release-gate",       test_release_gate()))
    results.append(("T7 no-write-proof",     test_no_write_proof()))

    print("\n" + "=" * 60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"RESULTS: {passed}/{total} passed")
    if passed == total:
        print("OMNICHAT_RUNTIME_V1_OK")
    else:
        failed = [n for n, r in results if not r]
        print(f"FAILED: {', '.join(failed)}")
    print("=" * 60)
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
