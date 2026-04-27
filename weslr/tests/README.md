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
T1: 25/25 passed
T2: 6/6 guard cases passed (0 expected rejections)
T3.1 load_trace: OK (3/3 valid, 2 malformed skipped)
T3.2 load_implementation_plans: OK (3/3 valid, 2 malformed skipped)
T3.3 load_iss_diagnostics: OK (3/3 valid, 2 malformed skipped)
T4: 3/3 file hash checks passed
T6: 30/30 commands returned valid responses
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

## Known Side Effects

**T2 appends valid records to real JSONL files.**

When T2 runs, it writes valid schema-smoke records to confirm that valid writes work:
- 1 `proposal_created` + 1 `proposal_decision` → `proposal_trace.jsonl`
- 1 `implementation_plan` → `implementation_plans.jsonl`
- 1 `iss_probe_result` + 1 `iss_gap_signal` → `iss_diagnostic_records.jsonl`

This is intentional. T2 first exercises valid writes to confirm the write path works, then exercises invalid writes to confirm guards reject them. The net effect is **5 new lines total** appended across the 3 JSONL files during T2.

If you want a clean run without side effects:
1. Back up JSONL files before running
2. Or mock the write functions when running T2

T3 uses **temporary files only** — no effect on real JSONL files during T3.
T4 and T6 are **read-only** — no effect on JSONL files during T4 or T6.

## Running Individual Tests

```python
# T1 only
from weslr.tests.test_harness_v1 import _t1_routes
_t1_routes()

# T2 only (appends to JSONL)
from weslr.tests.test_harness_v1 import _t2_schema_guards
_t2_schema_guards()

# T3 only (temp files, no side effects)
from weslr.tests.test_harness_v1 import _t3_malformed_line_read
_t3_malformed_line_read()

# T4 only (read-only)
from weslr.tests.test_harness_v1 import _t4_no_write_safety
_t4_no_write_safety()

# T6 only (read-only)
from weslr.tests.test_harness_v1 import _t6_full_smoke
_t6_full_smoke()
```

## Test Coverage

- **T1** — 25 route cases covering all deterministic handlers (registry + inline)
- **T2** — 6 invalid write rejection cases
- **T3** — 4 cases (3 loaders + missing file)
- **T4** — 3 file hash comparisons (proposal_trace, implementation_plans, iss_diagnostic_records)
- **T6** — 30 command smoke cases

## Non-Goals

- T5 (regression layer-by-layer) is documented in `TEST_STRATEGY_V1.md` but not yet in this harness
- Automated test runner (pytest integration) is planned but not yet set up
- Performance benchmarking is out of scope
