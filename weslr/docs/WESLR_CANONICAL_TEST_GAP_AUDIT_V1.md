# WESLR Canonical Test Gap Audit V1

**Date:** 2026-04-29
**Status:** `WESLR_CANONICAL_TEST_GAP_AUDIT_DEFINED`

---

## Root Cause

**Problem:** `weslr/tests/__init__.py` is a large monolithic import file that loads ~20 modules at the top level on first import. When a test file is loaded via the unittest discovery mechanism that triggers `__init__.py` loading, Python executes all those imports before the test file itself can run.

The specific failure chain:

```
weslr.tests.test_evidence_graph_overlay_v1
  → (via some import path) imports from weslr.tests.__init__
    → from weslr.suggestion_assessment import apply_assessment_to_candidate
      → from architecture_memory import (← bare import, no package prefix)
        → ModuleNotFoundError: No module named 'architecture_memory'
```

**Why OCC passed:** OCC's test files (`test_evidence_graph_overlay_v1.py`, `test_graph_evidence_presentation_v1.py`) **bypass `weslr/tests/__init__.py`** by using direct file loading:

```python
spec = importlib.util.spec_from_file_location("evidence_graph_overlay", "weslr/evidence_graph_overlay.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
```

This avoids triggering `__init__.py`'s top-level imports.

**Why OCW fails:** OCW's test discovery or import mechanism (possibly `from weslr.tests.test_evidence_graph_overlay_v1 import *` or `unittest` discovery via `weslr.tests`) triggers `__init__.py` loading before the test file, causing the cascade.

---

## Affected Tests

| Test File | OCW Import Problem | OCC Approach |
|----------|-------------------|-------------|
| `test_evidence_graph_overlay_v1.py` | `ModuleNotFoundError` via `__init__.py` | Direct `importlib.util` loading |
| `test_graph_evidence_presentation_v1.py` | `ModuleNotFoundError` via `__init__.py` | Direct `importlib.util` loading |
| `test_signal_alerting_v1.py` | Passes (self-contained) | Standard unittest |
| `test_context_decay_policy_v1.py` | Passes (self-contained) | Standard unittest |
| `test_omnichat_runtime_v1.py` | Passes (self-contained) | Standard unittest |
| `test_multi_graph_traversal_v1.py` | Passes (self-contained) | Standard unittest |
| `test_context_selector_graph_v1.py` | Passes (self-contained) | Standard unittest |
| `test_graph_response_expansion_v1.py` | Passes (self-contained) | Standard unittest |
| `release_gate_v1.py` | Passes (standalone) | Direct exec |
| `public_readiness_tests.py` | Passes (standalone) | Direct exec |

**Root modules that fail when loaded through `__init__.py`:**

- `weslr.suggestion_assessment` — imports `architecture_memory` without package prefix
- All other modules transitively blocked by the above

---

## Canonical Way to Run Each Test

All tests pass when run as standalone scripts with `PYTHONPATH=.`:

```bash
PYTHONPATH=. python3 weslr/tests/release_gate_v1.py
PYTHONPATH=. python3 weslr/tests/public_readiness_tests.py
PYTHONPATH=. python3 weslr/tests/test_multi_graph_traversal_v1.py
PYTHONPATH=. python3 weslr/tests/test_context_selector_graph_v1.py
PYTHONPATH=. python3 weslr/tests/test_graph_response_expansion_v1.py
PYTHONPATH=. python3 weslr/tests/test_evidence_graph_overlay_v1.py
PYTHONPATH=. python3 weslr/tests/test_graph_evidence_presentation_v1.py
PYTHONPATH=. python3 weslr/tests/test_signal_alerting_v1.py
PYTHONPATH=. python3 weslr/tests/test_context_decay_policy_v1.py
PYTHONPATH=. python3 weslr/tests/test_omnichat_runtime_v1.py
```

**All 10 tests pass on OCC.**

---

## Recommended Fix

### Immediate fix (no refactor):
Test files must **not** import through `weslr.tests.__init__.py`. Use direct file loading (as already done by `test_evidence_graph_overlay_v1.py` and `test_graph_evidence_presentation_v1.py`), or ensure OCW runs tests as standalone scripts with `PYTHONPATH=.`.

### Long-term fix:
**Fix the bare import in `weslr.suggestion_assessment`:**

```python
# Current (broken):
from architecture_memory import ...

# Fix:
from weslr.architecture_memory import ...
```

This single fix resolves the entire cascade. Once fixed, `__init__.py` can be imported safely and OCW's standard unittest discovery will work.

### Why not remove imports from `__init__.py`:
`__init__.py` serves a purpose — it allows `from weslr.tests import TestClass` style imports and exposes the `run_tests()` helper. Removing imports would break that functionality.

---

## Fix Order

1. **Fix `weslr/suggestion_assessment.py` line 16** — add `weslr.` prefix to `architecture_memory` import
2. **Verify** — run `PYTHONPATH=. python3 -c "from weslr.tests import run_tests"` to confirm no `ModuleNotFoundError`
3. **All tests should pass** under standard unittest discovery after the fix

---

## OCC Validation Results

```
release_gate_v1.py                  → WESLR_RELEASE_GATE_V1_OK
public_readiness_tests.py           → PUBLIC_READINESS_TESTS_OK
test_multi_graph_traversal_v1.py   → 16/16 OK
test_context_selector_graph_v1.py  → 27/27 OK
test_graph_response_expansion_v1.py → 18/18 OK
test_evidence_graph_overlay_v1.py  → 10/10 OK  (direct importlib loading)
test_graph_evidence_presentation_v1.py → 8/8 OK  (direct importlib loading)
test_signal_alerting_v1.py          → OK
test_context_decay_policy_v1.py    → OK
test_omnichat_runtime_v1.py        → 7/7 OK
```

**All 10 test files pass.**

---

## Verdict

**`WESLR_CANONICAL_TEST_GAP_AUDIT_DEFINED`**

Root cause: bare import in `weslr/suggestion_assessment.py` causes `__init__.py` to fail when loaded by OCW's test discovery mechanism. OCC's test files work around this by bypassing `__init__.py` via direct file loading. Fix: add `weslr.` prefix to the bare import.
