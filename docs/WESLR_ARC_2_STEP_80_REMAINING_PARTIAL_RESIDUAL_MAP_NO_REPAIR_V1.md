# WESLR ARC 2-Step 80 Remaining Partial Residual Map — No Repair V1

- **Dispatch**: `MAP_REMAINING_ARC_2_STEP_80_PARTIAL_RESIDUALS_NO_REPAIR_V1`
- **Repo**: `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Branch**: `occ-discovery-doctrine-implementation-20260613`
- **Start HEAD**: `e2b4e0c2f32ee73b44c6893e7f660b5a1bf2bf30`
- **End HEAD**: (to be committed)
- **Report**: `docs/WESLR_ARC_2_STEP_80_REMAINING_PARTIAL_RESIDUAL_MAP_NO_REPAIR_V1.md`

## 1. Context

After the extract→recolor stable-to-value redesign, the combined 80 invariant is:
- **77 exact / 3 partial / 0 unsupported / 0 failed**
- **represented candidates: 80 / 80**
- **unsupported: 0**
- **accepted stress residual: 1**
- **original 40: 39 / 1 / 0 / 0**
- **single-step canonical: 114 / 6 / 0 / 0**

This report maps the remaining 3 partial rows. No repairs are attempted. No categories are forced.

## 2. Remaining partial rows summary

| # | Task ID | Primitive Sequence | Difficulty | Status | Category |
|---|---------|-------------------|------------|--------|----------|
| 1 | `pilot_2_step_stress_08_fill_then_count_v1` | `fill_region -> object_count_to_pattern` | stress | partial | `right_primitives_wrong_order` |
| 2 | `pilot_2_step_easy_gen_02_noise_recolor_color_swap_v1` | `remove_background_noise -> recolor_symbol` | easy | partial | `first_step_wrong_second_correct` |
| 3 | `pilot_2_step_medium_ctx_09_extract_recolor_bg_transfer_v1` | `extract_largest_object -> recolor_symbol` | medium | partial | `first_step_wrong_second_correct` |

---

## 3. Detailed mapping

### 3.1 pilot_2_step_stress_08_fill_then_count_v1

**Task specification** (from `ALL_TASK_SPECS_V1`):
- `task_id`: `pilot_2_step_stress_08_fill_then_count_v1`
- `difficulty`: `stress`
- `primitive_pair`: `(fill_region, object_count_to_pattern)`
- `scene_type`: `fill_count`

**Intended sequence**:
```python
[
  {"primitive_id": "fill_region", "parameters": {"fill_value": 4, "background_value": 0}},
  {"primitive_id": "object_count_to_pattern", "parameters": {"count": None, "pattern_value": 7, "row_index": 3, "background_value": 0}}
]
```

**Selected candidate**:
```python
[
  {"primitive_id": "object_count_to_pattern", "parameters": {"count": None, "pattern_value": 7, "row_index": 3, "background_value": 2}},
  {"primitive_id": "fill_region", "parameters": {"fill_value": 0, "background_value": 7}}
]
# Wrong order selected
```

**Train pair analysis**:

Pair 0:
```
Input:           Intermediate (intended):    Output (intended):
[2,2,2,2,2,2]    [2,2,2,2,2,2]              [0,0,0,0,0,0]
[2,0,0,0,0,2]    [2,4,4,4,4,2]              [0,0,0,0,0,0]
[2,0,0,0,0,2]    [2,4,4,4,4,2]              [0,0,0,0,0,0]
[2,0,0,0,0,2]    [2,4,4,4,4,2]              [0,7,0,0,0,0]
[2,0,0,0,0,2]    [2,4,4,4,4,2]              [0,0,0,0,0,0]
[2,2,2,2,2,2]    [2,2,2,2,2,2]              [0,0,0,0,0,0]
```

Pair 1:
```
Input:           Intermediate (intended):    Output (intended):
[2,2,2,2,2,2]    [2,2,2,2,2,2]              [0,0,0,0,0,0]
[2,0,0,0,0,2]    [2,4,4,4,4,2]              [0,0,0,0,0,0]
[2,0,0,0,0,2]    [2,4,4,4,4,2]              [0,0,0,0,0,0]
[2,0,0,0,0,2]    [2,4,4,4,4,2]              [0,7,0,0,0,0]
[2,0,0,0,0,2]    [2,4,4,4,4,2]              [0,0,0,0,0,0]
[2,2,2,2,2,2]    [2,2,2,2,2,2]              [0,0,0,0,0,0]
```

**Candidate generation**:
- Pair 0: step1={'fill_value': 0, 'background_value': 2}, step2={'count': None, 'pattern_value': 7, 'row_index': 3, 'background_value': 2} → step2 exact: False
- Pair 1: same as pair 0 → step2 exact: False

**Analysis**:
The intended `fill_region` fills the interior with 4, then `object_count_to_pattern` with `count=None` must infer the count from the filled region. But the output is a single 7 in a field of 0s, which is a very sparse pattern. The `object_count_to_pattern` primitive with `count=None` appears to require dynamic count inference, which the current solver architecture does not support (it requires a concrete count value).

The selected candidate reverses the order. Both pairs show identical mismatch (21), suggesting the reversed order also fails symmetrically.

**Classification**: `accepted_stress_residual` — This is a deliberately hard "stress" task. The `object_count_to_pattern` with `count=None` is a known limitation. The task was included as an accepted stress residual from the start.

**Confidence**: high
**Repair deferred**: yes
**Real-evidence proceed**: yes

---

### 3.2 pilot_2_step_easy_gen_02_noise_recolor_color_swap_v1

**Task specification** (from `EXPANSION_TASK_SPECS_V1`):
- `task_id`: `pilot_2_step_easy_gen_02_noise_recolor_color_swap_v1`
- `difficulty`: `easy`
- `primitive_pair`: `(remove_background_noise, recolor_symbol)`
- `scene_type`: `noise_recolor`
- `overrides`: `{"source_color": 4, "target_color": 8, "noise_color": 9, "noise_cells": [(0, 6), (6, 0)]}`

**Intended sequence**:
```python
[
  {"primitive_id": "remove_background_noise", "parameters": {"background_value": 0}},
  {"primitive_id": "recolor_symbol", "parameters": {"from_value": 4, "to_value": 8, "background_value": 0}}
]
```

**Selected candidate**:
```python
[
  {"primitive_id": "recolor_symbol", "parameters": {"background_value": 0, "from_value": 9, "to_value": 2}},
  {"primitive_id": "remove_background_noise", "parameters": {"background_value": 0}}
]
# Wrong order selected
```

**Train pair analysis**:

Pair 0:
```
Input:                Intermediate (intended):     Output (intended):
[9, 0, 0, 0, 0, 0]    [0, 0, 0, 0, 0, 0]           [0, 0, 0, 0, 0, 0]
[0, 2, 2, 2, 2, 0]    [0, 2, 2, 2, 2, 0]           [0, 2, 2, 2, 2, 0]
[0, 2, 2, 2, 2, 0]    [0, 2, 2, 2, 2, 0]           [0, 2, 2, 2, 2, 0]
[0, 2, 2, 2, 2, 0]    [0, 2, 2, 2, 2, 0]           [0, 2, 2, 2, 2, 0]
[0, 2, 2, 2, 2, 0]    [0, 2, 2, 2, 2, 0]           [0, 2, 2, 2, 2, 0]
[0, 0, 0, 0, 0, 0]    [0, 0, 0, 0, 0, 0]           [0, 0, 0, 0, 0, 0]
```

Pair 1:
```
Input:                Intermediate (intended):     Output (intended):
[0, 0, 0, 0, 0, 0]    [0, 0, 0, 0, 0, 0]           [0, 0, 0, 0, 0, 0]
[9, 2, 2, 2, 2, 0]    [9, 2, 2, 2, 2, 0]           [9, 2, 2, 2, 2, 0]
[0, 2, 2, 2, 2, 0]    [0, 2, 2, 2, 2, 0]           [0, 2, 2, 2, 2, 0]
[0, 2, 2, 2, 2, 0]    [0, 2, 2, 2, 2, 0]           [0, 2, 2, 2, 2, 0]
[0, 2, 2, 2, 2, 0]    [0, 2, 2, 2, 2, 0]           [0, 2, 2, 2, 2, 0]
[0, 0, 0, 0, 0, 0]    [0, 0, 0, 0, 0, 0]           [0, 0, 0, 0, 0, 0]
```

**Candidate generation**:
- Pair 0: step1={'background_value': 2}, step2={'from_value': 9, 'to_value': 2, 'background_value': 0} → step1 exact: False, step2 exact: False
- Pair 1: step1={'background_value': 0}, step2={'from_value': 9, 'to_value': 2, 'background_value': 0} → step1 exact: True, step2 exact: False

**Analysis**:
The intended `remove_background_noise` with `background_value=0` removes noise cells that are different from the dominant non-background shape. But the behavior differs between train pairs:

- Pair 0: noise at `(0,0)=9` is isolated (only diagonal neighbor is `(1,1)=2`, which is non-adjacent). The noise 9 is removed because it's isolated from the main 2-shape.
- Pair 1: variant adjustment shifts noise cells by `(1,1)` → `(1,0)` and `(0,1)`. But looking at the input, the noise is at `(1,0)=9` which is adjacent to `(1,1)=2`. This makes the 9 part of the 2-component via `_connected_components` (they are neighbors), so the 9 is NOT removed.

This creates an **inconsistent `remove_background_noise` behavior** across train pairs:
- Pair 0: removes 9 → intermediate matches output → exact
- Pair 1: keeps 9 → intermediate differs from output → mismatch

The intended sequence is exact for pair 0 but not for pair 1, because the noise placement creates different component connectivity.

**Classification**: `task_design_issue` — The `noise_cells` placement with variant adjustment causes the noise to be isolated in one variant but touching the shape in the other. This makes `remove_background_noise` behave inconsistently.

**Confidence**: high
**Repair deferred**: yes
**Real-evidence proceed**: yes

---

### 3.3 pilot_2_step_medium_ctx_09_extract_recolor_bg_transfer_v1

**Task specification** (from `EXPANSION_TASK_SPECS_V1`):
- `task_id`: `pilot_2_step_medium_ctx_09_extract_recolor_bg_transfer_v1`
- `difficulty`: `medium`
- `primitive_pair`: `(extract_largest_object, recolor_symbol)`
- `scene_type`: `extract_recolor`
- `overrides`: `{"rows": 7, "cols": 7, "large_rect": (1, 1, 5, 5), "large_color": 5, "target_color": 2, "small_color": 8, "small_cells": [(0, 6), (6, 0)]}`
- `expansion_group`: `parameter_transfer`

**Intended sequence**:
```python
[
  {"primitive_id": "extract_largest_object", "parameters": {"background_value": 0}},
  {"primitive_id": "recolor_symbol", "parameters": {"from_value": 2, "to_value": 2, "background_value": 0}}
]
```

Note: `from_value=2, to_value=2` is a no-op recolor. The `source_color` is not specified in overrides, so `_primitive_parameters_for_scene` falls back to default `from_value=2`.

**Selected candidate**:
```python
[
  {"primitive_id": "recolor_symbol", "parameters": {"background_value": 5, "from_value": 8, "to_value": 0}},
  {"primitive_id": "extract_largest_object", "parameters": {"background_value": 5}}
]
# Wrong order selected
```

**Train pair analysis**:

Pair 0:
```
Input:                Intermediate (intended):     Output (intended):
[0, 0, 0, 0, 0, 0, 8] [0, 0, 0, 0, 0, 0, 0]      [0, 0, 0, 0, 0, 0, 0]
[0, 5, 5, 5, 5, 5, 0] [0, 5, 5, 5, 5, 5, 0]      [0, 5, 5, 5, 5, 5, 0]
[0, 5, 5, 5, 5, 5, 0] [0, 5, 5, 5, 5, 5, 0]      [0, 5, 5, 5, 5, 5, 0]
[0, 5, 5, 5, 5, 5, 0] [0, 5, 5, 5, 5, 5, 0]      [0, 5, 5, 5, 5, 5, 0]
[0, 5, 5, 5, 5, 5, 0] [0, 5, 5, 5, 5, 5, 0]      [0, 5, 5, 5, 5, 5, 0]
[0, 5, 5, 5, 5, 5, 0] [0, 5, 5, 5, 5, 5, 0]      [0, 5, 5, 5, 5, 5, 0]
[8, 0, 0, 0, 0, 0, 0] [0, 0, 0, 0, 0, 0, 0]      [0, 0, 0, 0, 0, 0, 0]
```

Pair 1:
```
Input:                Intermediate (intended):     Output (intended):
[8, 0, 0, 0, 0, 0, 0] [0, 0, 0, 0, 0, 0, 0]      [0, 0, 0, 0, 0, 0, 0]
[0, 5, 5, 5, 5, 5, 8] [0, 5, 5, 5, 5, 5, 5]      [0, 5, 5, 5, 5, 5, 5]
[0, 5, 5, 5, 5, 5, 0] [0, 5, 5, 5, 5, 5, 0]      [0, 5, 5, 5, 5, 5, 0]
[0, 5, 5, 5, 5, 5, 0] [0, 5, 5, 5, 5, 5, 0]      [0, 5, 5, 5, 5, 5, 0]
[0, 5, 5, 5, 5, 5, 0] [0, 5, 5, 5, 5, 5, 0]      [0, 5, 5, 5, 5, 5, 0]
[0, 5, 5, 5, 5, 5, 0] [0, 5, 5, 5, 5, 5, 0]      [0, 5, 5, 5, 5, 5, 0]
[0, 0, 0, 0, 0, 0, 0] [0, 0, 0, 0, 0, 0, 0]      [0, 0, 0, 0, 0, 0, 0]
```

**Candidate generation**:
- Pair 0: step1={'background_value': 8}, step2={'from_value': 8, 'to_value': 5, 'background_value': 0} → step1 exact: False, step2 exact: False
- Pair 1: step1={'background_value': 5}, step2={'from_value': 8, 'to_value': 0, 'background_value': 5} → step1 exact: False, step2 exact: False

**Analysis**:
The intended sequence uses `extract_largest_object` with `background_value=0`, which correctly extracts the 5-rectangle. The intermediate matches the output for both pairs (the intended recolor is a no-op). So the intended sequence SHOULD be exact.

However, the solver generates `extract_largest_object` parameter options from grid values. For pair 0, it considers `background_value=8` (because 8 appears in the grid). With `bg=8`, the largest component is the 0s background, which when extracted gives all 0s — matching the output. This makes `bg=8` appear to be a good step1 parameter.

For pair 1, the solver considers `background_value=5` (because 5 is dominant). With `bg=5`, the 8s become the extracted objects, giving a different intermediate.

The solver's greedy ranking across pairs picks parameters that don't generalize. The intended `bg=0` works for both pairs, but the solver doesn't discover it because:
1. `_background_value_from_grid` returns the most common cell value (0 for pair 0, 5 for pair 1)
2. The generated options include multiple bg candidates
3. The ranking picks different bgs per pair, and no single bg works for both

The task is labeled `parameter_transfer` — it expects the solver to infer that the background value should be transferred from step 1 to step 2. But the actual issue is that the solver can't find a stable `background_value` for `extract_largest_object` across both train pairs.

**Classification**: `unknown` — The task's intended recolor is a no-op (`from_value=2, to_value=2`), which is suspicious. The solver's bg inference varies per pair. This could be a task-design issue (the no-op recolor makes the task ambiguous) or a solver limitation (the bg inference heuristic is too greedy). Without deeper investigation, the root cause is unclear.

**Confidence**: medium
**Repair deferred**: yes
**Real-evidence proceed**: yes

---

## 4. Classification summary

| Task | Classification | Confidence | Known? | Deferred? | Proceed? |
|------|---------------|------------|--------|-----------|----------|
| `pilot_2_step_stress_08_fill_then_count_v1` | `accepted_stress_residual` | high | Yes (stress) | Yes | Yes |
| `pilot_2_step_easy_gen_02_noise_recolor_color_swap_v1` | `task_design_issue` | high | No | Yes | Yes |
| `pilot_2_step_medium_ctx_09_extract_recolor_bg_transfer_v1` | `unknown` | medium | No | Yes | Yes |

## 5. Invariant preservation

| Check | Status |
|-------|--------|
| combined_80 unchanged | **Yes** — 77/3/0/0, not modified by this report |
| represented candidates unchanged | **Yes** — 80/80 |
| unsupported unchanged | **Yes** — 0 |
| code unchanged | **Yes** — report only, no code changes |
| task specs unchanged | **Yes** — no task redesign |
| forced categories avoided | **Yes** — #3 marked as `unknown` where cause is unclear |

## 6. Validation

| Check | Result |
|-------|--------|
| `git diff --check` | **PASS** |
| `python weslr/tests/release_gate_v1.py` | **PASS** |
| `./scripts/weslr_release_check.sh` | **PASS** |
| `./scripts/chat_weslr_de_health_check.sh --mode source-repo` | **PASS** |

## 7. Short receipt

| Field | Value |
|-------|-------|
| Start HEAD | `e2b4e0c2f32ee73b44c6893e7f660b5a1bf2bf30` |
| End HEAD | (to be committed) |
| Report path | `docs/WESLR_ARC_2_STEP_80_REMAINING_PARTIAL_RESIDUAL_MAP_NO_REPAIR_V1.md` |
| Remaining partial count | 3 |
| Combined 80 unchanged | **yes** (77/3/0/0) |
| Represented candidates unchanged | **yes** (80/80) |
| Unsupported unchanged | **yes** (0) |
| Code unchanged | **yes** |
| Task specs unchanged | **yes** |
| Forced categories avoided | **yes** (#3 = `unknown`) |
| Validation | **PASS** |
| Push avoided | **yes** |
| Recommended next lane | `DESIGN_WESLR_FIRST_CONTROLLED_REAL_EVIDENCE_DIRECTION_RUN_V1` |
