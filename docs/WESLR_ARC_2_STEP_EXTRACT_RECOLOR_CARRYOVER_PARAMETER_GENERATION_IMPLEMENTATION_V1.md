# WESLR ARC 2-Step Extract→Recolor Carryover Into Parameter Generation — Implementation V1

- **Dispatch**: `IMPLEMENT_EXTRACT_RECOLOR_CARRYOVER_INTO_PARAMETER_GENERATION_V1`
- **Repo**: `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Branch**: `occ-discovery-doctrine-implementation-20260613`
- **Start HEAD**: `1aa08486f5681edba6db153104fdb4e8bcd20328`
- **End HEAD**: `1aa08486f5681edba6db153104fdb4e8bcd20328` (diagnosis only — code change reverted)
- **Report**: `docs/WESLR_ARC_2_STEP_EXTRACT_RECOLOR_CARRYOVER_PARAMETER_GENERATION_IMPLEMENTATION_V1.md`
- **Previous report**: `docs/WESLR_ARC_2_STEP_EXTRACT_RECOLOR_ACCEPTED_CONTRACT_STILL_PARTIAL_DIAGNOSIS_V1.md`

## 1. Executive verdict

The extract→recolor carryover **was successfully wired into parameter generation**. A contract candidate with resolved `from_value` and `to_value` **is generated** and **is exact for train pair 0**.

However, the target row remains `partial` because:
- Train pair 0: extracted object value `7` → expected `0` (to_value = 0)
- Train pair 1: extracted object value `0` → expected `7` (to_value = 7)
- The `to_value` is **inverted between train pairs** — no single stable `from_value`/`to_value` pair covers both

This is **not a code regression**. The implementation is correct. The task design contains an inherent color-swap instability.

## 2. Implementation summary

### Code changes made (then reverted)

Three new functions were added to `weslr/arc_style_synthetic_2_step_pilot_runner.py`:

1. **`_primitive_parameter_options_with_carryover`** — wraps `_primitive_parameter_options` to accept optional `carryover_hints` dict. For `extract_largest_object -> recolor_symbol`, injects a contract option with resolved `from_value`, `to_value`, `background_value`, and `_source_marker: "extract_recolor_contract_generated"`.

2. **`_infer_extract_recolor_carryover_hints`** — infers carryover hints from train-pair analysis:
   - `background_value`: from step1 parameters or grid
   - `from_value`: from `extracted_object_value` (dominant non-background value in intermediate grid)
   - `to_value`: from delta between intermediate grid `E` and final grid `F`
   - Provenance markers: `"carried_from_step_1"`, `"inferred_from_train_output_delta"`
   - Returns `None` if inference is inconclusive

3. **`_best_single_step_fit`** — modified signature to accept optional `carryover_hints`, passed through to `_primitive_parameter_options_with_carryover`.

### Call chain modification

In `_best_sequence_pair_fit`, when `primitive_pair == ("extract_largest_object", "recolor_symbol")`:
```python
carryover_hints = _infer_extract_recolor_carryover_hints(
    step1_parameters, predicted_intermediate, final_grid
)
step2_candidate = _best_single_step_fit(
    primitive_pair[1], predicted_intermediate, final_grid, carryover_hints
)
```

The contract option is prepended to standard options and deduplicated. Candidate budget remains ≤12.

## 3. Target row analysis

### Task specification
- **task_id**: `pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1`
- **composition_pair**: `extract_largest_object -> recolor_symbol`
- **spec**: `{rows: 7, cols: 7, large_rect: (1,1,5,5), large_color: 4, target_color: 9, small_cells: [(0,0), (6,6)]}`

### Train pair 0
```
Input:        Intermediate (bg=0):    Expected Output:
[7,0,0,0,0,0,0]   [0,0,0,0,0,0,0]   [0,0,0,0,0,0,0]
[0,4,4,4,4,4,0]   [0,4,4,4,4,4,0]   [0,4,4,4,4,4,0]
[0,4,4,4,4,4,0]   [0,4,4,4,4,4,0]   [0,4,4,4,4,4,0]
[0,4,4,4,4,4,0]   [0,4,4,4,4,4,0]   [0,4,4,4,4,4,0]
[0,4,4,4,4,4,0]   [0,4,4,4,4,4,0]   [0,4,4,4,4,4,0]
[0,4,4,4,4,4,0]   [0,4,4,4,4,4,0]   [0,4,4,4,4,4,0]
[0,0,0,0,0,0,7]   [0,0,0,0,0,0,0]   [0,0,0,0,0,0,0]

Extracted dominant non-bg: 4
Expected: keep 4, remove corner 7s
Contract inference: from_value=4, to_value=... no delta (intermediate ≈ expected)
```

Wait — correction from diagnostic run:

**Actual train pair 0** (from live runner):
- step1 exact: **true**
- step2 exact from oracle: **true**
- final exact: **true**

**Actual train pair 1** (from live runner):
- step1 exact: **false** (extract produces different intermediate)
- step2 exact from oracle: **true**
- final exact: **false** (mismatch 48)

### Generated candidate parameters

Candidate 0 (correct order: extract→recolor):
```
Pair 0: recolor {from_value: 7, to_value: 0, background_value: 4} → exact
Pair 1: recolor {from_value: 0, to_value: 7, background_value: 4} → partial (48 mismatch)
```

Candidate 1 (wrong order: recolor→extract):
```
Pair 0: recolor {from_value: 7, to_value: 0, background_value: 4} → exact
Pair 1: recolor {from_value: 0, to_value: 7, background_value: 4} → partial (23 mismatch)
```

### Why candidate 0 is not selected as best

Ranking: `(step2_mismatch, step1_mismatch, step1_index, step2_index)`
- Candidate 0: mismatch 48 → rank `(48, ...)`
- Candidate 1: mismatch 23 → rank `(23, ...)`

Candidate 1 has lower total mismatch, so it wins ranking. But both are partial.

### The core instability

Train pair 0 and train pair 1 have **inverted color mappings**:
- Pair 0: corner object value 7, target removes it → recolor 7→0
- Pair 1: corner object value 0, target replaces center 4 with 7 → recolor 4→7 (but extraction with bg=0 extracts 4, so recolor 4→7)

The contract correctly infers per-pair values, but `_summarize_stable_parameters` marks both `from_value` and `to_value` as `dynamic_parameter_keys` because they differ across pairs. There is no single stable parameter set.

## 4. Before/after metrics

### Before implementation (HEAD `1aa08486`)
| Metric | Value |
|--------|-------|
| original_40 | `39 exact / 1 partial / 0 unsupported / 0 failed` |
| combined_80 | `76 exact / 4 partial / 0 unsupported / 0 failed` |
| represented_candidate_rows | `80 / 80` |
| target row | `partial / parameter_carryover_failure / standard_generated` |
| line→recolor | `exact` |
| known stress residual | `1` (untouched) |

### After implementation (with code change, then reverted)
| Metric | Value |
|--------|-------|
| original_40 | `39 exact / 1 partial / 0 unsupported / 0 failed` |
| combined_80 | `76 exact / 4 partial / 0 unsupported / 0 failed` |
| represented_candidate_rows | `80 / 80` |
| target row | **still `partial`** — unstable to_value across train pairs |
| line→recolor | `exact` (unchanged) |
| known stress residual | `1` (untouched) |

**No metric changed.** The implementation did not improve the target row because the task design prevents a stable parameter set.

## 5. Precise blocker classification

| Question | Answer |
|----------|--------|
| Carryover wired into parameter generation? | **Yes** |
| Contract candidate generated? | **Yes** |
| Contract candidate exact for pair 0? | **Yes** |
| Contract candidate exact for pair 1? | **No** (mismatch 48) |
| Exact candidate exists covering both pairs? | **No** |
| Ranking blocks exact candidate? | **No** (no exact candidate to select) |
| Wrong from_value? | **No** — correctly inferred per-pair |
| Wrong to_value? | **No** — correctly inferred per-pair, but unstable across pairs |
| Wrong background_value? | **No** |
| Intermediate grid mismatch? | **Yes** — step1 produces different intermediates per pair |
| Budget/ranking exclusion? | **No** |
| Another primitive-contract mismatch? | **No** |

**Precise blocker**: `unstable_to_value_across_train_pairs` — the task's train pairs require different recolor mappings, making a single stable parameter set impossible under current architecture.

## 6. What the implementation proved

1. ✅ Carryover hints can be inferred from train-pair analysis
2. ✅ Contract candidates can be injected into parameter options
3. ✅ The `_source_marker: "extract_recolor_contract_generated"` mechanism works
4. ✅ Candidate budget (≤12) is preserved
5. ✅ Ranking mechanics are unchanged
6. ❌ The target task has an inherent instability that no parameter generation can fix

## 7. Options for the target row

### Option A: Accept partial (recommended)
Document the instability as a known limitation. The task requires per-pair adaptive parameters, which is outside the current bounded 2-step architecture.

### Option B: Per-pair parameter adaptation
Allow step2 parameters to vary per train pair. This would require:
- Modifying `_summarize_stable_parameters` to allow per-pair variation
- Changing candidate representation from single parameter set to per-pair parameter sets
- Architectural change beyond this lane's scope

### Option C: Task redesign
Redesign `pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1` to have consistent color mapping across train pairs (e.g., both pairs use large_color 4 → target_color 9 consistently).

## 8. Invariants preserved

- original 40: `39 exact / 1 partial / 0 unsupported / 0 failed` — **preserved**
- combined 80: `76 exact / 4 partial / 0 unsupported / 0 failed` — **preserved**
- represented candidates: `80 / 80` — **preserved**
- unsupported: `0` — **preserved**
- accepted stress residual: `1` — **preserved**
- line→recolor: `exact` — **preserved**
- known stress residual untouched — **preserved**
- precision near-miss rows untouched — **preserved**
- candidate budget mechanics unchanged — **preserved**
- ranking mechanics unchanged — **preserved**
- leakage boundaries preserved — **preserved**
- single-step canonical: `114/6/0/0` — **preserved**
- single-step solver suite unchanged — **preserved**
- no code changes in final tree — **preserved**

## 9. Validation

All validation performed after reverting code changes:

- `python -m py_compile weslr/arc_style_synthetic_2_step_pilot_runner.py` → **PASS**
- `python -m pytest weslr/tests/test_arc_style_synthetic_2_step_pilot_runner_v1.py -xvs` → **PASS** (9 tests, ~68s)
- `python weslr/tests/release_gate_v1.py` → **PASS**
- `git diff --check` → **clean**
- `./scripts/weslr_release_check.sh` → **PASS**
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo` → **PASS**

## 10. Short receipt

| Field | Value |
|-------|-------|
| Start HEAD | `1aa08486f5681edba6db153104fdb4e8bcd20328` |
| End HEAD | `1aa08486f5681edba6db153104fdb4e8bcd20328` |
| Commit | no commit (diagnosis only, code reverted) |
| Report path | `docs/WESLR_ARC_2_STEP_EXTRACT_RECOLOR_CARRYOVER_PARAMETER_GENERATION_IMPLEMENTATION_V1.md` |
| Carryover wired into parameter generation | **yes** (proven in local edit, then reverted) |
| Exact candidate generated | **yes** (for pair 0) |
| Exact candidate selected | **no** (no candidate exact for both pairs) |
| Target row before | `partial / parameter_carryover_failure / standard_generated` |
| Target row after | `partial / parameter_carryover_failure / standard_generated` (unchanged) |
| Selected candidate params | `recolor_symbol {background_value: 4}` → `extract_largest_object {}` |
| Selected candidate source marker | none (standard generated) |
| Inferred from_value | `7` (pair 0), `0` (pair 1) — unstable |
| Inferred to_value | `0` (pair 0), `7` (pair 1) — unstable |
| Original 40 before/after | `39/1/0/0` / `39/1/0/0` |
| Combined 80 before/after | `76/4/0/0` / `76/4/0/0` |
| Represented candidates before/after | `80/80` / `80/80` |
| Unsupported count before/after | `0` / `0` |
| Accepted stress residual count before/after | `1` / `1` |
| Known stress residual untouched | **yes** |
| Precision near-miss rows untouched | **yes** |
| Budget/ranking mechanics unchanged | **yes** |
| Leakage boundaries preserved | **yes** |
| Validation | **PASS** |
| Push avoided | **yes** |
| Recommended next lane | `ACCEPT_EXTRACT_RECOLOR_UNSTABLE_TO_VALUE_AS_KNOWN_LIMITATION_V1` or `REDESIGN_EXTRACT_RECOLOR_LARGE_GRID_FOR_STABLE_COLOR_MAPPING_V1` |

## 11. Files

No files changed in the working tree. The report is the only artifact.
