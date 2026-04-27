# WESLR Test Strategy — V1

**Version:** 1.0
**Status:** active reference
**Created:** 2026-04-27

---

## Overview

WESLR is a governed deterministic query system. Tests verify the correctness and stability of handler dispatch, schema enforcement, JSONL integrity, and regression coverage. No automated test framework is currently deployed; tests are run manually but documented precisely enough to be automated later.

---

## Test Categories

### T1 — Deterministic Route Tests

**Purpose:** Verify that each input maps to the correct handler path and response structure.

**How to run:**
```python
from interpretation import interpret_human_turn

SMOKE = [
    # ISS probe registry query
    ("show iss probes",          "ISS_probe_registry_query", {"probe_count": 4}),
    ("show probe registry",     "ISS_probe_registry_query", {"probe_count": 4}),
    ("list probes",             "ISS_probe_registry_query", {"probe_count": 4}),
    ("what can iss check",      "ISS_probe_registry_query", {"probe_count": 4}),

    # ISS probe plan
    ("plan probe probe.front_door.chat",  "ISS_probe_plan",  {"probe_plan": object}),
    ("how would you check probe.trace.proposals", "ISS_probe_plan", {"probe_plan": object}),
    ("plan probe unknown.probe",  "ISS_probe_plan", {"probe_plan": None}),

    # ISS diagnostics query
    ("show diagnostics",        "ISS_query_all",     {"diagnostics": list}),
    ("show iss diagnostics",    "ISS_query_all",     {"diagnostics": list}),
    ("list diagnostics",        "ISS_query_all",     {"diagnostics": list}),
    ("show gaps",               "ISS_query_gaps",    {"gaps": list}),
    ("show probe results",      "ISS_query_probes",  {"probes": list}),

    # Operator overview
    ("show system overview",    "operator_overview", {"overview": dict}),
    ("weslr overview",           "operator_overview", {"overview": dict}),
    ("system overview",         "operator_overview", {"overview": dict}),
    ("show full status",        "operator_overview", {"overview": dict}),

    # State checkpoint query
    ("show weslr status",        "state_checkpoint_query", {"state_checkpoint": dict}),
    ("show architecture status", "state_checkpoint_query", {"state_checkpoint": dict}),
    ("show state checkpoint",    "state_checkpoint_query", {"state_checkpoint": dict}),
    ("weslr checkpoint",         "state_checkpoint_query", {"state_checkpoint": dict}),
    ("system checkpoint",       "state_checkpoint_query", {"state_checkpoint": dict}),

    # Plan explanation
    ("explain plan iss.not_integrated", "plan_explanation", {"plan_explanation": dict}),

    # ISS probe execution (inline, unchanged)
    ("execute probe probe.front_door.chat", "ISS_probe_execution", {"probe_execution": dict}),

    # Open prompts
    ("tell me about solar panels", None, {}),
]

for msg, expected_path, expected_payload in SMOKE:
    r = interpret_human_turn(msg)
    assert r.get("path") == expected_path, f"{msg!r}: expected {expected_path!r}, got {r.get('path')!r}"
    for key, val in expected_payload.items():
        if val is object:
            assert key in r and r[key] is not None, f"{msg!r}: expected {key} present"
        elif val is list:
            assert key in r and isinstance(r[key], list), f"{msg!r}: expected {key} as list"
        elif val is dict:
            assert key in r and isinstance(r[key], dict), f"{msg!r}: expected {key} as dict"
        elif val is None:
            assert key not in r or r[key] is None, f"{msg!r}: expected {key} absent or None"
print("T1_DETERMINISTIC_ROUTE_SMOKE_OK")
```

**Pass criteria:** All routes match expected path. All expected payload fields present. Open prompts return `path=None`.

---

### T2 — Write-Side Schema Guard Tests

**Purpose:** Verify that invalid records are rejected before reaching JSONL files.

**How to run:**
```python
import pytest  # run with: pytest T2*

from weslr.proposal_traceability import record_proposal, record_decision
from weslr.implementation_planning import create_implementation_plan, record_implementation_plan
from weslr.iss.diagnostic_records import make_probe_result, make_gap_signal, record_iss_diagnostic

# T2.1 — proposal_id must be non-empty
try:
    record_proposal("", {})
    assert False, "empty proposal_id accepted"
except ValueError:
    pass

# T2.2 — content must be dict
try:
    record_proposal("p1", "not-dict")
    assert False, "non-dict content accepted"
except (ValueError, TypeError):
    pass

# T2.3 — decision proposal_id must be non-empty
try:
    record_decision("", "accepted")
    assert False, "empty decision proposal_id accepted"
except ValueError:
    pass

# T2.4 — execution_allowed=True must be rejected
plan = create_implementation_plan("test", {"summary": "x"})
plan["execution_allowed"] = True
try:
    record_implementation_plan(plan)
    assert False, "execution_allowed=True accepted"
except ValueError:
    pass

# T2.5 — probe status must be valid
try:
    record_iss_diagnostic({"type": "iss_probe_result", "probe_id": "p", "target": "t", "status": "broken", "evidence": {}, "confidence": "h", "timestamp": 1})
    assert False, "invalid probe status accepted"
except ValueError:
    pass

# T2.6 — gap severity must be valid
try:
    record_iss_diagnostic({"type": "iss_gap_signal", "gap_id": "g", "source_probe_id": "p", "summary": "s", "severity": "critical", "evidence": {}, "confidence": "h", "timestamp": 1})
    assert False, "invalid gap severity accepted"
except ValueError:
    pass

print("T2_WRITE_SIDE_SCHEMA_GUARDS_OK")
```

**Pass criteria:** All 6 invalid write attempts raise `ValueError`. No malformed records reach JSONL.

---

### T3 — JSONL Malformed-Line Read Tests

**Purpose:** Verify that loaders skip malformed lines and return valid records.

**How to run:**
```python
import tempfile, pathlib, os, json

# T3.1 — load_trace skips malformed lines
from weslr import proposal_traceability
ORIG_TRACE = proposal_traceability.TRACE_FILE
with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
    f.write(json.dumps({"type": "proposal_created", "proposal_id": "a", "content": {}, "timestamp": 1}) + "\n")
    f.write("NOT JSON\n")
    f.write(json.dumps({"type": "proposal_created", "proposal_id": "b", "content": {}, "timestamp": 2}) + "\n")
    f.write("{ broken\n")
    f.write(json.dumps({"type": "proposal_created", "proposal_id": "c", "content": {}, "timestamp": 3}) + "\n")
    t = f.name
proposal_traceability.TRACE_FILE = pathlib.Path(t)
records = proposal_traceability.load_trace(10)
assert len(records) == 3 and sorted(r["proposal_id"] for r in records) == ["a","b","c"]
proposal_traceability.TRACE_FILE = ORIG_TRACE; os.unlink(t)

# T3.2 — load_implementation_plans skips malformed lines
from weslr import implementation_planning
ORIG_PLAN = implementation_planning.PLAN_FILE
def _plan(pid):
    return {"type": "implementation_plan","plan_id": pid,"proposal_id":"x","status":"planned","execution_allowed":False,"created_at":1,"steps":[{"order":1,"title":"a","kind":"inspect","allowed":True}],"risks":[],"rollback_notes":[],"operator_approval_required":True}
with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
    f.write(json.dumps(_plan("p1")) + "\n"); f.write("bad\n")
    f.write(json.dumps(_plan("p2")) + "\n"); f.write("{oops\n")
    f.write(json.dumps(_plan("p3")) + "\n"); t = f.name
implementation_planning.PLAN_FILE = pathlib.Path(t)
records = implementation_planning.load_implementation_plans(10)
assert len(records) == 3 and sorted(r["plan_id"] for r in records) == ["p1","p2","p3"]
implementation_planning.PLAN_FILE = ORIG_PLAN; os.unlink(t)

# T3.3 — load_iss_diagnostics skips malformed lines
from weslr.iss import diagnostic_records
ORIG_REC = diagnostic_records.RECORD_FILE
with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
    f.write(json.dumps({"type":"iss_probe_result","probe_id":"pr1","target":"t","status":"ok","evidence":{},"confidence":"h","timestamp":1}) + "\n")
    f.write("bad\n")
    f.write(json.dumps({"type":"iss_gap_signal","gap_id":"g1","source_probe_id":"pr1","summary":"s","severity":"low","evidence":{},"confidence":"h","timestamp":2}) + "\n")
    f.write("{oops\n")
    f.write(json.dumps({"type":"iss_probe_result","probe_id":"pr2","target":"t","status":"ok","evidence":{},"confidence":"h","timestamp":3}) + "\n")
    t = f.name
diagnostic_records.RECORD_FILE = pathlib.Path(t)
records = diagnostic_records.load_iss_diagnostics(10)
assert len(records) == 3
diagnostic_records.RECORD_FILE = ORIG_REC; os.unlink(t)

# T3.4 — missing file returns empty list
from weslr import proposal_traceability, implementation_planning
from weslr.iss import diagnostic_records
with tempfile.TemporaryDirectory() as d:
    p = pathlib.Path(d) / "nonexistent.jsonl"
    for mod,ATTR in [(proposal_traceability,"TRACE_FILE"),(implementation_planning,"PLAN_FILE"),(diagnostic_records,"RECORD_FILE")]:
        orig = getattr(mod, ATTR)
        setattr(mod, ATTR, p)
        try:
            assert mod.load_trace() == [] if ATTR=="TRACE_FILE" else (mod.load_implementation_plans() == [] if ATTR=="PLAN_FILE" else mod.load_iss_diagnostics() == [])
        finally:
            setattr(mod, ATTR, orig)

print("T3_JSONL_MALFORMED_LINE_READ_OK")
```

**Pass criteria:** All malformed lines skipped. Valid records returned. Missing files return `[]`.

---

### T4 — No-Write Safety Tests

**Purpose:** Verify that read-only operations do not modify JSONL files.

**How to run:**
```python
import hashlib, tempfile, pathlib, os, json

def _file_hash(p):
    return hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else None

# Record pre-read hashes
from weslr import proposal_traceability, implementation_planning
from weslr.iss import diagnostic_records

TRACE_PRE  = _file_hash(proposal_traceability.TRACE_FILE)
PLAN_PRE   = _file_hash(implementation_planning.PLAN_FILE)
RECORD_PRE = _file_hash(diagnostic_records.RECORD_FILE)

# Perform all read operations
from interpretation import interpret_human_turn
for msg in ["show diagnostics","show implementation plans","why does plan iss.not_integrated exist",
           "show iss probes","plan probe probe.front_door.chat","show system overview","show weslr status"]:
    interpret_human_turn(msg)

TRACE_POST  = _file_hash(proposal_traceability.TRACE_FILE)
PLAN_POST   = _file_hash(implementation_planning.PLAN_FILE)
RECORD_POST = _file_hash(diagnostic_records.RECORD_FILE)

assert TRACE_PRE == TRACE_POST,  "TRACE_FILE modified by read-only operation"
assert PLAN_PRE == PLAN_POST,   "PLAN_FILE modified by read-only operation"
assert RECORD_PRE == RECORD_POST, "RECORD_FILE modified by read-only operation"

print("T4_NO_WRITE_SAFETY_OK")
```

**Pass criteria:** All file hashes identical before and after read operations. No accidental writes.

---

### T5 — Regression Tests: C1–C6, C7–C9, ISS, Formatter, Registry

**Purpose:** Verify that no regression was introduced in core layer behavior.

**C1 — Self description:**
```
Input: "who are you" / "what are you"
Expected: returns capability description (path may be None in base turn but must not crash)
```

**C2 — Capabilities:**
```
Input: "what can you do" / "what are your capabilities"
Expected: returns capability list (path may be None but must not crash)
```

**C3 — Capability gaps:**
```
Input: "how can you improve"
Expected: returns gap list (path may be None but response_text correct)
```

**C4/C5 — Proposal creation:**
```
Input: "make proposal test"
Expected: creates proposal_created record in trace; execution_allowed=False
```

**C6 — Proposal approval:**
```
Input: "accept proposal test"
Expected: creates proposal_decision record in trace
```

**C7 — Proposal traceability:**
```
Input: "why is proposal iss.not_integrated"
Expected: path=proposal_explanation with trace records
```

**C8 — Implementation plans:**
```
Input: "show implementation plans"
Expected: path=C8_plan_query_list, returns all plans
```

**C8Q — Plan query:**
```
Input: "show plan plan-iss.not_integrated-..."
Expected: path=plan_explanation with plan details
```

**C9 — Proposal/plan linkage:**
```
Input: "explain plan iss.not_integrated"
Expected: plan_explanation links plan to proposal to source gap
```

**ISS — Diagnostic subsystem:**
```
Input: "show diagnostics" / "show gaps" / "show probe results"
Expected: ISS_query_all / ISS_query_gaps / ISS_query_probes paths
```

**ISS probe execution:**
```
Input: "execute probe probe.front_door.chat"
Expected: ISS_probe_execution path, confirmation prompt
```

**Formatters (already migrated):**
```
Input: "show system overview" / "show diagnostics" / "show weslr status"
Expected: operator_overview / ISS_query_* / state_checkpoint_query using build_deterministic_response
```

**Registry (already extracted):**
```
Input: "show iss probes" / "plan probe probe.front_door.chat"
Expected: ISS_probe_registry_query / ISS_probe_plan via dispatch_deterministic_handler
```

---

### T6 — Full Smoke Command List

Run all commands in sequence and confirm no crashes:

```python
from interpretation import interpret_human_turn

COMMANDS = [
    # Core layers
    "who are you", "what are you",
    "what can you do", "what are your capabilities",
    "how can you improve",

    # Proposals
    "make proposal test.smoke",
    "accept proposal test.smoke",
    "reject proposal test.smoke",
    "explain proposal iss.not_integrated",

    # Plans
    "show implementation plans",
    "why does plan iss.not_integrated exist",
    "explain plan iss.not_integrated",

    # ISS diagnostics
    "show diagnostics", "show iss diagnostics", "list diagnostics",
    "show gaps", "show iss gaps",
    "show probe results",

    # ISS probes
    "show iss probes", "show probe registry", "list probes", "what can iss check",
    "plan probe probe.front_door.chat", "how would you check probe.trace.proposals",
    "plan probe unknown.probe",
    "execute probe probe.front_door.chat",

    # System overview
    "show system overview", "weslr overview", "system overview", "show full status",
    "show weslr status", "show architecture status", "show state checkpoint",
    "weslr checkpoint", "system checkpoint",

    # Open prompts
    "tell me about solar panels",
    "random nonsense xyz",
]

for cmd in COMMANDS:
    try:
        r = interpret_human_turn(cmd)
        print(f"OK: {cmd!r} -> {r.get('path')!r}")
    except Exception as e:
        print(f"FAIL: {cmd!r} raised {e!r}")

print("T6_FULL_SMOKE_COMPLETE")
```

**Pass criteria:** No exceptions raised. All commands return a dict with at least `message` and `response_text`.

---

## Test Execution Order

Run in this order:
1. T3 (JSONL malformed-line read) — validates loaders before any writes
2. T2 (write-side schema guards) — validates validators; appends test records
3. T1 (deterministic route tests) — validates routes after schema work
4. T4 (no-write safety) — validates reads don't accidentally write
5. T5 (regression) — layer-by-layer validation
6. T6 (full smoke) — end-to-end sanity check

---

## Non-Goals

This test strategy does not include:
- Automated test runner setup (documented for later)
- Performance benchmarking
- Concurrency tests
- Integration tests with OpenClaw core
- Security penetration tests

---

*Test Strategy V1 — 2026-04-27*
*Run order: T3 → T2 → T1 → T4 → T5 → T6*
