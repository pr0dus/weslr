# WESLR Test Harness V1

## How to Run

```bash
python3 weslr/tests/test_harness_v1.py
```

## Expected Output

```
==================================================
WESLR Test Harness V1
==================================================
T1: 24/24 passed
T2: 6/6 invalid writes rejected (0 production records written)
T3.1 load_trace: OK (3/3 valid, 2 malformed skipped)
T3.2 load_implementation_plans: OK (3/3 valid, 2 malformed skipped)
T3.3 load_iss_diagnostics: OK (3/3 valid, 2 malformed skipped)
T3.4 missing file: OK (all 3 loaders return [])
T3: 4/4 subtests passed
T4: 3/3 file hash checks passed
T6: 31/31 commands returned valid responses
==================================================
TEST_HARNESS_V1_OK
```

## What Each Test Does

| Test | Category | What it checks |
|---|---|---|
| T1 | Deterministic routes | Every input maps to the correct handler path and payload fields |
| T2 | Write-side schema guards | Invalid records raise `ValueError` before reaching JSONL |
| T3 | JSONL malformed-line read | Load functions skip bad lines using temp files |
| T4 | No-write safety | File hashes unchanged after read-only commands |
| T6 | Full smoke | All commands return a valid response dict with no crashes |

## JSONL Isolation

**No production JSONL files are modified by this test harness.**

- T2 uses a temp directory with monkeypatched module constants. All valid and invalid writes go to temp files only. Production file constants are restored in a `finally` block.
- T3 uses temp files only (no production file touch).
- T4 and T6 are read-only — no JSONL writes.

Run the harness as many times as you like. Production JSONL line counts remain unchanged.

## Running Individual Tests

```python
from weslr.tests.test_harness_v1 import _t1_routes, _t2_schema_guards, _t3_malformed_line_read, _t4_no_write_safety, _t6_full_smoke

_t1_routes()       # read-only
_t2_schema_guards() # temp files only
_t3_malformed_line_read() # temp files only
_t4_no_write_safety()  # read-only
_t6_full_smoke()   # read-only
```

## Test Coverage

- **T1** — 24 route cases covering all deterministic handlers (registry + inline)
- **T2** — 6 invalid write rejection cases
- **T3** — 4 subtests (3 loaders + missing file)
- **T4** — 3 file hash comparisons
- **T6** — 31 command smoke cases

## Non-Goals

- T5 (regression layer-by-layer) is documented in `TEST_STRATEGY_V1.md` but not yet in this harness
- Automated test runner (pytest integration) is planned but not yet set up
- Performance benchmarking is out of scope