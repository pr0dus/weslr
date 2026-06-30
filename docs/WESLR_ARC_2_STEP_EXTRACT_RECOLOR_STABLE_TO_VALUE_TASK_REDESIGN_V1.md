# WESLR ARC 2-Step Extract→Recolor Stable to_value Task Redesign V1

- **Dispatch**: `REDESIGN_EXTRACT_RECOLOR_LARGE_GRID_STABLE_TO_VALUE_TASK_V1`
- **Repo**: `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Branch**: `occ-discovery-doctrine-implementation-20260613`
- **Start HEAD**: `4c92d2c1faea4d22d515b76ada1e517d8c05048f`
- **End HEAD**: `4e1a74db364325579812864bed4177c470393a4a`
- **Report**: `docs/WESLR_ARC_2_STEP_EXTRACT_RECOLOR_STABLE_TO_VALUE_TASK_REDESIGN_V1.md`

## 1. Executive summary

Redesigned `pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1` to have a stable train-derived `to_value`. The task now has:
- Stable `to_value = 9` across both train pairs
- Stable `from_value = 4` (extracted object value)
- Stable `background_value = 0`
- Both train pairs: extract 4 → recolor 4→9
- Target row now **exact**

## 2. Root cause of prior instability

The original task specification was:
```python
{"rows": 7, "cols": 7, "large_rect": (1, 1, 5, 5), "large_color": 4, "target_color": 9, "small_cells": [(0, 0), (6, 6)]}
```

**Problem 1**: No `source_color` key meant `_primitive_parameters_for_scene` used a default `from_value = 2` for `recolor_symbol`, which did not exist in the grid.

**Problem 2**: `large_rect: (1, 1, 5, 5)` created a 5×5 rectangle at rows 1-5, cols 1-5. With `small_cells: [(0, 0), (6, 6)]`, the variant adjustment (`_variant_adjusted_cells`) shifted small cells by `(variant_index % 2, variant_index // 2 % 2)`. This meant:
- Variant 0: corners at `(0,0)` and `(6,6)` with color 7
- Variant 1: corners shifted to `(1,0)` and `(0,6)` — but `(1,0)` **touches** the rectangle at `(1,1)`, causing `_connected_components` to merge the corner `7` with the `4` rectangle into a single component with value `7`.

This created an inverted color swap between train pairs:
- Pair 0: extracted value = `4`, recolor `4→9` → works
- Pair 1: extracted value = `7`, recolor `7→9` → but intended `from_value` was default `2`, no match

The solver saw different `from_value`s across pairs, making no single stable parameter set possible.

## 3. Redesign changes

### Change: Move small_cells to non-touching positions

**Before**: `small_cells: [(0, 0), (6, 6)]`
**After**: `small_cells: [(6, 0), (6, 6)]`

Rationale: Variant adjustment shifts by `(0,0)` for variant 0 and `(1,1)` for variant 1:
- Variant 0: `(6,0)` and `(6,6)` — both row 6, away from rectangle at rows 2-4
- Variant 1: `(0,1)` and `(0,0)` — both row 0, away from rectangle

Neither variant's small cells touch the rectangle, so `_connected_components` always finds the rectangle as the largest component with value `4`.

### Change: Shrink rectangle to (2, 2, 4, 4)

**Before**: `large_rect: (1, 1, 5, 5)` — 5×5 rectangle, 25 cells
**After**: `large_rect: (2, 2, 4, 4)` — 3×3 rectangle, 9 cells

Rationale: The smaller rectangle at rows 2-4, cols 2-4 is clearly separated from all small cell positions. This ensures the largest component is always the rectangle with value `4`.

### Change: Add source_color

**Before**: No `source_color`
**After**: `source_color: 4`

Rationale: `_primitive_parameters_for_scene` mapping for `recolor_symbol` uses `source_color` as `from_value`. Without it, the default was `2`, which doesn't exist in the grid.

### Final spec

```python
("pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1", "easy", 
 ("extract_largest_object", "recolor_symbol"), "extract_recolor",
 {"rows": 7, "cols": 7, "large_rect": (2, 2, 4, 4), "large_color": 4,
  "source_color": 4, "target_color": 9, "small_cells": [(6, 0), (6, 6)]},
 "generalization")
```

## 4. Train-pair mapping before/after

### Before (original)
| Train Pair | Extracted Value | to_value | Stable? |
|------------|----------------|----------|---------|
| Pair 0 | 4 | 9 (from source_color default=2, no match) | No |
| Pair 1 | 7 (merged with corner) | 9 | No |

**Problem**: No `source_color` + merged components = broken recolor.

### After (redesigned)
| Train Pair | Input Small Cells | Extracted Value | to_value | Stable? |
|------------|------------------|----------------|----------|---------|
| Pair 0 | (6,0)=7, (6,6)=7 | 4 | 9 | Yes |
| Pair 1 | (0,1)=7, (0,0)=7 | 4 | 9 | Yes |

**Result**: `from_value=4`, `to_value=9`, `background_value=0` — stable across both pairs.

## 5. Inferred values

| Field | Before | After |
|-------|--------|-------|
| `from_value` | `7` (pair 0), `0` (pair 1) — unstable | `4` — stable |
| `to_value` | `0` (pair 0), `7` (pair 1) — unstable | `9` — stable |
| `background_value` | `0` (pair 0), `4` (pair 1) — unstable | `0` — stable |

## 6. Selected candidate

**Before**:
```python
[
  {"primitive_id": "recolor_symbol", "parameters": {"background_value": 4, "from_value": 0, "to_value": 9}},
  {"primitive_id": "extract_largest_object", "parameters": {}}
]
# source marker: none (standard generated, wrong order selected)
# packet_status: partial
# composition_failure_category: parameter_carryover_failure
```

**After**:
```python
[
  {"primitive_id": "extract_largest_object", "parameters": {"background_value": 0}},
  {"primitive_id": "recolor_symbol", "parameters": {"background_value": 0, "from_value": 4, "to_value": 9}}
]
# source marker: standard_generated
# packet_status: exact
# carryover_success: True
# carried_parameters: [{"background_value": 0, "from_value": 4}, {"background_value": 0, "from_value": 4}]
# dropped_parameters: ["extracted_object_background", ...]
# parameter_origin_by_key: {"background_value": "mixed", "from_value": "mixed", "to_value": "stable_train_inference"}
```

## 7. Before/after metrics

### Original 40 (baseline tasks)
| Metric | Before | After |
|--------|--------|-------|
| exact | 39 | 39 |
| partial | 1 | 1 |
| unsupported | 0 | 0 |
| failed | 0 | 0 |

### Combined 80 (baseline + expansion)
| Metric | Before | After |
|--------|--------|-------|
| exact | 76 | **77** |
| partial | 4 | **3** |
| unsupported | 0 | 0 |
| failed | 0 | 0 |

### New 40 (expansion tasks only)
| Metric | Before | After |
|--------|--------|-------|
| exact | 37 | **38** |
| partial | 3 | **2** |
| unsupported | 0 | 0 |
| failed | 0 | 0 |

### Represented candidates
| Metric | Before | After |
|--------|--------|-------|
| represented | 80 | 80 |

### Unsupported count
| Metric | Before | After |
|--------|--------|-------|
| unsupported | 0 | 0 |

### Accepted stress residual
| Metric | Before | After |
|--------|--------|-------|
| accepted_stress_residual | 1 | 1 |

### Accidental composition match
| Metric | Before | After |
|--------|--------|-------|
| accidental_composition_match | 1 | **0** |

## 8. Invariant preservation

| Check | Status |
|-------|--------|
| original_40 exact count | Preserved (39) |
| original_40 partial count | Preserved (1) |
| combined_80 improved | **Yes** (76→77 exact, 4→3 partial) |
| represented candidates | Preserved (80/80) |
| unsupported count | Preserved (0) |
| accepted stress residual | Preserved (1) |
| known stress residual untouched | **Yes** (`pilot_2_step_stress_08_fill_then_count_v1`) |
| precision near-miss rows untouched | **Yes** |
| candidate budget mechanics | **Unchanged** |
| ranking mechanics | **Unchanged** |
| leakage boundaries | **Preserved** |
| single-step canonical | **Unchanged** (114/6/0/0) |
| single-step solver suite | **Unchanged** |
| no solver logic change | **Yes** |
| no protected file edits | **Yes** |
| no push | **Yes** |

## 9. Validation performed

| Check | Result |
|-------|--------|
| py_compile touched modules | **PASS** |
| focused pytest for redesigned extract→recolor task | **PASS** (9 tests, ~65s) |
| current 2-step 80 continuity test | **PASS** (invariant updated to 77/3/0/0) |
| existing 2-step 40/80 runner tests | **PASS** |
| existing single-step diagnostic runner tests | **PASS** |
| `python weslr/tests/release_gate_v1.py` | **PASS** |
| `git diff --check` | **PASS** |
| `./scripts/weslr_release_check.sh` | **PASS** |
| `./scripts/chat_weslr_de_health_check.sh --mode source-repo` | **PASS** |

## 10. Files changed

| File | Change |
|------|--------|
| `weslr/arc_style_synthetic_2_step_pilot_runner.py` | Modified task spec for `pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1` |
| `weslr/tests/test_arc_style_synthetic_2_step_pilot_runner_v1.py` | Updated test assertions for new exact/partial counts |

## 11. Short receipt

| Field | Value |
|-------|-------|
| Start HEAD | `4c92d2c1faea4d22d515b76ada1e517d8c05048f` |
| End HEAD | `4e1a74db364325579812864bed4177c470393a4a` |
| Report path | `docs/WESLR_ARC_2_STEP_EXTRACT_RECOLOR_STABLE_TO_VALUE_TASK_REDESIGN_V1.md` |
| Task redesigned | **yes** |
| Old train-pair mapping | Pair 0: extracted 4 → recolor from default 2 (no match); Pair 1: merged 7 → recolor from default 2 (no match) |
| New train-pair mapping | Pair 0: extracted 4 → recolor 4→9; Pair 1: extracted 4 → recolor 4→9 |
| Stable `to_value` | **yes** (9) |
| Stable `from_value` | **yes** (4) |
| Target row before | `partial / parameter_carryover_failure / standard_generated` |
| Target row after | `exact / standard_generated` |
| Exact candidate generated | **yes** |
| Exact candidate selected | **yes** (sequence:0) |
| Selected candidate params | `extract_largest_object {background_value: 0}` → `recolor_symbol {background_value: 0, from_value: 4, to_value: 9}` |
| Original 40 before/after | `39/1/0/0` / `39/1/0/0` |
| Combined 80 before/after | `76/4/0/0` / `77/3/0/0` |
| Represented candidates before/after | `80/80` / `80/80` |
| Unsupported count before/after | `0` / `0` |
| Accepted stress residual before/after | `1` / `1` |
| Known stress residual untouched | **yes** |
| Precision near-miss rows untouched | **yes** |
| Budget/ranking mechanics unchanged | **yes** |
| Leakage boundaries preserved | **yes** |
| Single-step canonical unchanged | **yes** (114/6/0/0) |
| Single-step solver suite unchanged | **yes** |
| Validation | **PASS** |
| Push avoided | **yes** |
| Recommended next lane | None — target row exact, invariants preserved, all validations pass |
