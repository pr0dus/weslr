#!/usr/bin/env python3
"""
WESLR Test Harness V1
Runs: T1 (route), T2 (schema guards), T3 (malformed-line read), T4 (no-write safety), T6 (full smoke)
Confirms: TEST_HARNESS_V1_OK
Side effect: T2 appends valid schema-smoke records to real JSONL files.
"""

import sys
import hashlib
import tempfile
import os
import pathlib

_workspace = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_workspace))
sys.path.insert(0, str(_workspace / "weslr"))

from interpretation import interpret_human_turn
from weslr import proposal_traceability, implementation_planning
from weslr.iss import diagnostic_records


def _file_hash(p):
    if not p.exists():
        return None
    return hashlib.md5(p.read_bytes()).hexdigest()


def _t1_routes():
    """T1 — Deterministic route tests."""
    cases = [
        ("show iss probes",         "ISS_probe_registry_query", "probe_count",  int),
        ("show probe registry",     "ISS_probe_registry_query", "probe_count",  int),
        ("list probes",            "ISS_probe_registry_query", "probe_count",  int),
        ("what can iss check",      "ISS_probe_registry_query", "probe_count",  int),
        ("plan probe probe.front_door.chat",  "ISS_probe_plan",  "probe_plan", dict),
        ("how would you check probe.trace.proposals", "ISS_probe_plan", "probe_plan", dict),
        ("plan probe unknown.probe", "ISS_probe_plan",        "probe_plan", type(None)),
        ("show diagnostics",        "ISS_query_all",          "diagnostics", list),
        ("show iss diagnostics",    "ISS_query_all",          "diagnostics", list),
        ("list diagnostics",        "ISS_query_all",          "diagnostics", list),
        ("show gaps",               "ISS_query_gaps",         "gaps",        list),
        ("show probe results",      "ISS_query_probes",        "probes",      list),
        ("show system overview",    "operator_overview",       "overview",    dict),
        ("weslr overview",          "operator_overview",       "overview",    dict),
        ("system overview",        "operator_overview",       "overview",    dict),
        ("show full status",        "operator_overview",       "overview",    dict),
        ("show weslr status",       "state_checkpoint_query",  "state_checkpoint", dict),
        ("show architecture status","state_checkpoint_query","state_checkpoint", dict),
        ("show state checkpoint",   "state_checkpoint_query", "state_checkpoint", dict),
        ("weslr checkpoint",        "state_checkpoint_query",  "state_checkpoint", dict),
        ("system checkpoint",       "state_checkpoint_query",  "state_checkpoint", dict),
        ("explain plan iss.not_integrated", "plan_explanation", "plan_explanation", dict),
        ("execute probe probe.front_door.chat", "ISS_probe_execution", "probe_execution", dict),
        ("tell me about solar panels", None, None, None),
    ]

    passed = 0
    for msg, exp_path, key, typ in cases:
        r = interpret_human_turn(msg)
        if r.get("path") != exp_path:
            print(f"T1 FAIL: {msg!r} -> {r.get('path')!r} (expected {exp_path!r})")
            continue
        if key is None:
            passed += 1
        elif typ is type(None):
            if r.get(key) is None:
                passed += 1
            else:
                print(f"T1 FAIL: {msg!r} key {key!r} should be None")
        elif isinstance(r.get(key), typ):
            passed += 1
        else:
            print(f"T1 FAIL: {msg!r} key {key!r} type {type(r.get(key)).__name__} (expected {typ.__name__})")

    print(f"T1: {passed}/{len(cases)} passed")
    return passed == len(cases)


def _t2_schema_guards():
    """T2 — Write-side schema guard tests. Valid writes execute (appends to JSONL)."""
    from weslr.proposal_traceability import record_proposal, record_decision
    from weslr.implementation_planning import create_implementation_plan, record_implementation_plan
    from weslr.iss.diagnostic_records import make_probe_result, make_gap_signal, record_iss_diagnostic

    record_proposal("t2.schema.smoke", {"summary": "T2 smoke test"})
    record_decision("t2.schema.smoke", "accepted")
    plan = create_implementation_plan("t2.schema.smoke", {"summary": "T2 smoke test"})
    record_implementation_plan(plan)
    probe = make_probe_result("t2.probe.smoke", "t2 target", "ok", {"mode": "test"}, "high")
    record_iss_diagnostic(probe)
    gap = make_gap_signal("gap.t2.smoke", "t2.probe.smoke", "T2 gap smoke", "low", {"mode": "test"}, "high")
    record_iss_diagnostic(gap)

    failed = 0
    try:
        record_proposal("", {})
        print("T2 FAIL: empty proposal_id accepted")
        failed += 1
    except ValueError:
        pass

    try:
        record_proposal("p1", "not-dict")
        print("T2 FAIL: non-dict content accepted")
        failed += 1
    except (ValueError, TypeError):
        pass

    try:
        record_decision("", "accepted")
        print("T2 FAIL: empty decision proposal_id accepted")
        failed += 1
    except ValueError:
        pass

    bad_plan = dict(plan)
    bad_plan["execution_allowed"] = True
    try:
        record_implementation_plan(bad_plan)
        print("T2 FAIL: execution_allowed=True accepted")
        failed += 1
    except ValueError:
        pass

    try:
        record_iss_diagnostic({
            "type": "iss_probe_result", "probe_id": "p", "target": "t",
            "status": "broken", "evidence": {}, "confidence": "h", "timestamp": 1
        })
        print("T2 FAIL: invalid probe status accepted")
        failed += 1
    except ValueError:
        pass

    try:
        record_iss_diagnostic({
            "type": "iss_gap_signal", "gap_id": "g", "source_probe_id": "p",
            "summary": "s", "severity": "critical", "evidence": {}, "confidence": "h", "timestamp": 1
        })
        print("T2 FAIL: invalid gap severity accepted")
        failed += 1
    except ValueError:
        pass

    print(f"T2: {6 - failed}/6 invalid writes rejected (T2 valid writes appended 5 records to JSONL)")
    return failed == 0


def _t3_malformed_line_read():
    """T3 — JSONL malformed-line read tests using temp files only."""
    import json

    subtests = 0
    passed = 0

    # T3.1 load_trace
    ORIG_TRACE = proposal_traceability.TRACE_FILE
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for pid in ["a", "b", "c"]:
            f.write(json.dumps({"type": "proposal_created", "proposal_id": pid, "content": {}, "timestamp": 1}) + "\n")
        f.write("NOT JSON\n")
        f.write("{ broken\n")
        tmp_trace = f.name
    proposal_traceability.TRACE_FILE = pathlib.Path(tmp_trace)
    subtests += 1
    try:
        records = proposal_traceability.load_trace(10)
        ids = sorted(r["proposal_id"] for r in records)
        if ids == ["a", "b", "c"]:
            passed += 1
            print("T3.1 load_trace: OK (3/3 valid, 2 malformed skipped)")
        else:
            print(f"T3.1 FAIL: got {ids}")
    finally:
        proposal_traceability.TRACE_FILE = ORIG_TRACE
        os.unlink(tmp_trace)

    # T3.2 load_implementation_plans
    ORIG_PLAN = implementation_planning.PLAN_FILE
    def _plan(pid):
        return {
            "type": "implementation_plan", "plan_id": pid, "proposal_id": "x", "status": "planned",
            "execution_allowed": False, "created_at": 1,
            "steps": [{"order": 1, "title": "a", "kind": "inspect", "allowed": True}],
            "risks": [], "rollback_notes": [], "operator_approval_required": True
        }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for pid in ["p1", "p2", "p3"]:
            f.write(json.dumps(_plan(pid)) + "\n")
        f.write("bad\n")
        f.write("{oops\n")
        tmp_plan = f.name
    implementation_planning.PLAN_FILE = pathlib.Path(tmp_plan)
    subtests += 1
    try:
        records = implementation_planning.load_implementation_plans(10)
        ids = sorted(r["plan_id"] for r in records)
        if ids == ["p1", "p2", "p3"]:
            passed += 1
            print("T3.2 load_implementation_plans: OK (3/3 valid, 2 malformed skipped)")
        else:
            print(f"T3.2 FAIL: got {ids}")
    finally:
        implementation_planning.PLAN_FILE = ORIG_PLAN
        os.unlink(tmp_plan)

    # T3.3 load_iss_diagnostics
    ORIG_REC = diagnostic_records.RECORD_FILE
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(json.dumps({"type": "iss_probe_result", "probe_id": "pr1", "target": "t", "status": "ok", "evidence": {}, "confidence": "h", "timestamp": 1}) + "\n")
        f.write("bad\n")
        f.write(json.dumps({"type": "iss_gap_signal", "gap_id": "g1", "source_probe_id": "pr1", "summary": "s", "severity": "low", "evidence": {}, "confidence": "h", "timestamp": 2}) + "\n")
        f.write("{oops\n")
        f.write(json.dumps({"type": "iss_probe_result", "probe_id": "pr2", "target": "t", "status": "ok", "evidence": {}, "confidence": "h", "timestamp": 3}) + "\n")
        tmp_rec = f.name
    diagnostic_records.RECORD_FILE = pathlib.Path(tmp_rec)
    subtests += 1
    try:
        records = diagnostic_records.load_iss_diagnostics(10)
        if len(records) == 3:
            passed += 1
            print("T3.3 load_iss_diagnostics: OK (3/3 valid, 2 malformed skipped)")
        else:
            print(f"T3.3 FAIL: got {len(records)}")
    finally:
        diagnostic_records.RECORD_FILE = ORIG_REC
        os.unlink(tmp_rec)

    # T3.4 missing file returns empty list (3 separate checks, 1 subtest)
    subtests += 1
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "nonexistent.jsonl"
        all_ok = True
        for mod, attr in [
            (proposal_traceability, "TRACE_FILE"),
            (implementation_planning, "PLAN_FILE"),
            (diagnostic_records, "RECORD_FILE"),
        ]:
            orig = getattr(mod, attr)
            setattr(mod, attr, p)
            try:
                if attr == "TRACE_FILE":
                    result = mod.load_trace()
                elif attr == "PLAN_FILE":
                    result = mod.load_implementation_plans()
                else:
                    result = mod.load_iss_diagnostics()
                if result != []:
                    all_ok = False
                    print(f"T3.4 FAIL: {attr} missing file did not return []")
            finally:
                setattr(mod, attr, orig)
        if all_ok:
            passed += 1
            print("T3.4 missing file: OK (all 3 loaders return [])")

    print(f"T3: {passed}/{subtests} subtests passed")
    return passed == subtests


def _t4_no_write_safety():
    """T4 — Read-only commands must not modify JSONL file hashes."""
    TRACE_PRE = _file_hash(proposal_traceability.TRACE_FILE)
    PLAN_PRE = _file_hash(implementation_planning.PLAN_FILE)
    REC_PRE = _file_hash(diagnostic_records.RECORD_FILE)

    read_cmds = [
        "show diagnostics", "show implementation plans",
        "why does plan iss.not_integrated exist",
        "show iss probes", "plan probe probe.front_door.chat",
        "show system overview", "show weslr status",
    ]
    for cmd in read_cmds:
        interpret_human_turn(cmd)

    TRACE_POST = _file_hash(proposal_traceability.TRACE_FILE)
    PLAN_POST = _file_hash(implementation_planning.PLAN_FILE)
    REC_POST = _file_hash(diagnostic_records.RECORD_FILE)

    passed = 0
    if TRACE_PRE == TRACE_POST:
        passed += 1
    else:
        print("T4 FAIL: TRACE_FILE modified by read-only operations")
    if PLAN_PRE == PLAN_POST:
        passed += 1
    else:
        print("T4 FAIL: PLAN_FILE modified by read-only operations")
    if REC_PRE == REC_POST:
        passed += 1
    else:
        print("T4 FAIL: RECORD_FILE modified by read-only operations")

    print(f"T4: {passed}/3 file hash checks passed")
    return passed == 3


def _t6_full_smoke():
    """T6 — Full smoke: all commands return valid responses, no crashes."""
    commands = [
        "who are you", "what are you",
        "what can you do", "what are your capabilities",
        "how can you improve",
        "show diagnostics", "show iss diagnostics", "list diagnostics",
        "show gaps", "show iss gaps",
        "show probe results",
        "show iss probes", "show probe registry", "list probes", "what can iss check",
        "plan probe probe.front_door.chat", "how would you check probe.trace.proposals",
        "plan probe unknown.probe",
        "show implementation plans",
        "explain plan iss.not_integrated",
        "show system overview", "weslr overview", "system overview", "show full status",
        "show weslr status", "show architecture status", "show state checkpoint",
        "weslr checkpoint", "system checkpoint",
        "tell me about solar panels",
        "random nonsense xyz",
    ]

    passed = 0
    for cmd in commands:
        try:
            r = interpret_human_turn(cmd)
            if isinstance(r, dict) and "response_text" in r:
                passed += 1
            else:
                print(f"T6 FAIL: {cmd!r} did not return expected dict")
        except Exception as e:
            print(f"T6 FAIL: {cmd!r} raised {e!r}")

    print(f"T6: {passed}/{len(commands)} commands returned valid responses")
    return passed == len(commands)


def main():
    print("=" * 50)
    print("WESLR Test Harness V1")
    print("=" * 50)

    t1_ok = _t1_routes()
    print()
    t2_ok = _t2_schema_guards()
    print()
    t3_ok = _t3_malformed_line_read()
    print()
    t4_ok = _t4_no_write_safety()
    print()
    t6_ok = _t6_full_smoke()
    print()
    print("=" * 50)
    if t1_ok and t2_ok and t3_ok and t4_ok and t6_ok:
        print("TEST_HARNESS_V1_OK")
    else:
        print("TEST_HARNESS_V1_FAILURES")
        sys.exit(1)


if __name__ == "__main__":
    main()
