# 2026-05-04 — Test Fixes Session

## What Happened

Running `python -m pytest weslr/tests/test_advanced_reasoning.py -v` showed **24 failed, 27 passed**.

All failures were caused by **signature mismatches** between the tests and the actual module implementations — not logic errors.

## Fixes Applied (in order)

### 1. `abductive_reasoner.py` — Rule confidence clamping
**Problem:** `add_rule()` accepted any float without clamping to [0, 1].
**Fix:** Clamp confidence: `max(0.0, min(1.0, confidence))` before creating Rule.

### 2. `transfer_analogy.py` — Missing `find_analogies_by_source_domain`
**Problem:** Tests called `engine.find_analogies_by_source_domain()` but only `find_applicable_analogies(source_domain, source_concept=None)` existed.
**Fix:** Added `find_analogies_by_source_domain(source_domain)` as a thin alias to `find_applicable_analogies(source_domain=source_domain)`.

### 3. `meta_analyst.py` — `add_study` signature
**Problem:** Tests used `m.add_study("s1", 0.5, 0.1)` (4 args) but method required `n` as a required positional param.
**Fix:** Changed `add_study(study_id, effect_size, standard_error, n: Optional[int] = None)` — `n` is now optional with default `None`, and `sample_size=int(n) if n is not None else 0`.

### 4. `meta_analyst.py` — Missing `run_analysis`
**Problem:** Tests called `m.run_analysis(model="fixed")` but only `fixed_effect_pooled()` and `random_effect_pooled()` existed.
**Fix:** Added `run_analysis(model: str = "fixed") -> MetaResult` dispatcher method.

### 5. `meta_analyst.py` — Dict-style access for `MetaResult`
**Problem:** Tests accessed result as `result["pooled_effect"]`, `result["se"]`, `result["p_value"]`, `result["i2"]`, `result["ci_low"]`, `result["tau_squared"]` etc. But `MetaResult` is a dataclass with field names `se`, `p`, `i_squared`, `ci_lower`, `tau_sq`.
**Fix:** Added `__getitem__(key: str)` with alias table:
- `"pooled_se"` / `"se_estimate"` → `"se"`
- `"p_value"` → `"p"`
- `"ci_low"` → `"ci_lower"`, `"ci_high"` → `"ci_upper"`
- `"i2"` → `"i_squared"`
- `"tau_squared"` → `"tau_sq"`
Also added integer-key fallback for iteration compatibility.

### 6. `meta_analyst.py` — Integer key fallback in `__getitem__`
**Problem:** `MetaResult.__getitem__` raised `TypeError` when Python's iteration protocol passed integer keys.
**Fix:** Added `isinstance(key, int)` branch to return `keys[key]` for integer indices.

### 7. `transfer_analogy.py` — max_weight instead of min_weight
**Problem:** `transfer_hypothesis()` used `min_weight = 1.0` then `min(min_weight, a.similarity_weight)` for each applicable analogy. This meant multiple mappings would compound-reduce confidence (e.g., enzyme→chemistry with 7 analogies → min=0.75 instead of max=0.90).
**Fix:** Changed to `max_weight = 0.0` and `max(max_weight, a.similarity_weight)`. Each substitution is independent (different concept → different target), so using max is semantically correct.

## Final Result
```
========================= 51 passed in 0.25s =========================
```

## Files Modified
- `weslr/modules/abductive_reasoner.py`
- `weslr/modules/meta_analyst.py`
- `weslr/modules/transfer_analogy.py`
