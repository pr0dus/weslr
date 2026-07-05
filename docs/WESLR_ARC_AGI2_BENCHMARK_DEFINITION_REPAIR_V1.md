# WESLR ARC-AGI-2 Benchmark Definition Repair V1

## Repo / Branch

- **Repo:** `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Branch:** `main`
- **Start HEAD (expected):** `ba5a9083b53edb01745fb21842a12fc1ac63d74a`
- **Actual preflight HEAD:** `ba5a9083b53edb01745fb21842a12fc1ac63d74a`
- **End HEAD:** (recorded in chat after commit)

## Previous Lane

- **Lane:** `WESLR_ARC_AGI2_ADVERSARIAL_BOUNDARY_AUDIT_V1`
- **Verdict:** `adversarial_boundary_audit_v1_passed_ready_for_benchmark_definition_repair_lane`

## Previous Adversarial Audit Baseline (Heldout)

| Metric | Before |
|--------|--------|
| Solved | 110 |
| Fallback-only | 25 |
| Adversarial rejection pass | 25 |
| Adversarial rejection fail | 10 |
| Exceptions | 0 |
| Exact-two-output | PASS |
| Deterministic replay | PASS |
| Expected-output isolation | PASS |
| Split disjoint | PASS |

## Root Cause Summary

Two adversarial families used identity expected outputs (input == expected_output):

1. **`ambiguous_multiple_rules`**: Cross-shaped grid `[[0,1,0],[1,1,1],[0,1,0]]` with identity train pair and identity expected output. The solver's `object_bbox` / `crop_foreground_bbox` family returns the input unchanged on already-tight grids, accidentally matching the identity expected output.

2. **`unsupported_primitive_chain`**: 2×2 diagonal grid `[[0,1],[1,0]]` with identity train pair and identity expected output. Same `object_bbox` identity mechanism.

Both were **benchmark-definition risks**, not solver bugs. The solver's identity-on-tight-grid behavior is correct for real tasks.

## Diagnosis Before Change

### `ambiguous_multiple_rules`
- **Old input/output relation:** input == output (identity), cross-shaped grid
- **Why old expected output was identity:** Generator used `base` for both `test_input` and `expected_output`
- **Which solver family accidentally matched it:** `object_bbox` (returns input unchanged on already-tight bounding box)
- **New input/output relation:** train maps cross `[[0,1,0],[1,1,1],[0,1,0]]` → corners-only `[[1,0,1],[0,0,0],[1,0,1]]`; test uses different color (2..6) cross → corners-only with that color
- **Why new expected output is non-identity:** Output is corners-only (inverse cross), which differs from the cross input
- **Why new expected output is not trivially produced by existing identity families:** No solver family produces corners-only-from-cross. `object_bbox` returns the input (cross), not the corners. `color_role` maps colors but doesn't change the spatial pattern.

### `unsupported_primitive_chain`
- **Old input/output relation:** input == output (identity), 2×2 diagonal grid
- **Why old expected output was identity:** Generator used `base` for both `test_input` and `expected_output`
- **Which solver family accidentally matched it:** `object_bbox` (returns input unchanged on already-tight grid)
- **New input/output relation:** train maps 2×2 `[[0,1],[1,0]]` → 3×3 `[[0,1,1],[1,1,0],[1,0,0]]` (size expansion); test uses different color (2..6) 2×2 → 3×3 expansion
- **Why new expected output is non-identity:** Output is a 3×3 grid from a 2×2 input (size expansion), which is fundamentally different from the input
- **Why new expected output is not trivially produced by existing identity families:** No solver family does arbitrary 2×2→3×3 size expansion. `scale_cells_integer` scales cell blocks, not the grid dimensions. Fallback returns the 2×2 input, not a 3×3 output.

## Files Changed

1. `weslr/arc_synthetic_discovery_task_generator_v1.py` — revised `_adversarial_ambiguous` and `_adversarial_unsupported` generator functions
2. `weslr/tests/test_arc_synthetic_discovery_task_generator_v1.py` — added 5 new tests for non-identity, non-solvable, and deterministic properties
3. `weslr/tests/test_arc_adversarial_boundary_audit_v1.py` — updated audit test expectations
4. `docs/WESLR_ARC_AGI2_BENCHMARK_DEFINITION_REPAIR_V1.md` — this report

## Generator Definition Changes

### `_adversarial_ambiguous` (before → after)

Before:
- `base = [[0,1,0],[1,1,1],[0,1,0]]`
- train: `(base → base)` (identity)
- test: `base → base` (identity)

After:
- `train_in = [[0,1,0],[1,1,1],[0,1,0]]` (cross, color 1)
- `train_out = [[1,0,1],[0,0,0],[1,0,1]]` (corners only, color 1)
- `test_in = [[0,c,0],[c,c,c],[0,c,0]]` (cross, color c ∈ {2..6})
- `expected = [[c,0,c],[0,0,0],[c,0,c]]` (corners only, color c)
- Variant index determines test color: `2 + (variant_idx % 5)`

### `_adversarial_unsupported` (before → after)

Before:
- `base = [[0,1],[1,0]]`
- train: `(base → base)` (identity)
- test: `base → base` (identity)

After:
- `train_in = [[0,1],[1,0]]` (2×2, color 1)
- `train_out = [[0,1,1],[1,1,0],[1,0,0]]` (3×3 expansion, color 1)
- `test_in = [[0,c],[c,0]]` (2×2, color c ∈ {2..6})
- `expected = [[0,c,c],[c,c,0],[c,0,0]]` (3×3 expansion, color c)
- Variant index determines test color: `2 + (variant_idx % 5)`

## Before/After Adversarial Table (Heldout)

| Family | Before: Solved | Before: Rejected | After: Solved | After: Rejected | Status |
|--------|---------------|-----------------|--------------|-----------------|--------|
| ambiguous_multiple_rules | 5 | 0 | 0 | 5 | ✅ Fixed |
| unsupported_primitive_chain | 5 | 0 | 0 | 5 | ✅ Fixed |
| inconsistent_train_examples | 0 | 5 | 0 | 5 | No change |
| near_match_one_cell | 0 | 5 | 0 | 5 | No change |
| same_palette_wrong_geometry | 0 | 5 | 0 | 5 | No change |
| same_geometry_wrong_recolor | 0 | 5 | 0 | 5 | No change |
| count_tie_ambiguity | 0 | 5 | 0 | 5 | No change |

## Before/After Benchmark Comparison (Heldout)

| Metric | Before | After | Change | Expected? |
|--------|--------|-------|--------|-----------|
| Solved | 110 | 100 | -10 | ✅ Yes — 10 false adversarial solves removed |
| Fallback-only | 25 | 30 | +5 | ✅ Yes — false solves → correct rejections (some become fallback) |
| Adv rejection pass | 25 | 35 | +10 | ✅ Yes — all 7 families now correctly rejected |
| Adv rejection fail | 10 | 0 | -10 | ✅ Yes — all false solves eliminated |
| Composition solved | 25 | 25 | 0 | ✅ No change — compositions unaffected |
| Malformed | 0 | 0 | 0 | ✅ No change |
| Exceptions | 0 | 0 | 0 | ✅ No change |
| Exact-two-output | PASS | PASS | — | ✅ No change |
| Deterministic replay | PASS | PASS | — | ✅ No change |
| Expected-output isolation | PASS | PASS | — | ✅ No change |
| Split disjoint | PASS | PASS | — | ✅ No change |

### Dev Comparison

| Metric | Before | After |
|--------|--------|-------|
| Solved | 66 | 60 |
| Adv rejection pass | 15 | 21 |
| Adv rejection fail | 6 | 0 |

## Why Solved Count Decreased

The heldout solved count decreased from 110 to 100 because the 10 previously false-positive adversarial solves (5 `ambiguous_multiple_rules` + 5 `unsupported_primitive_chain`) are now correctly rejected. This is the expected and desired outcome — the previous score was inflated by adversarial tasks being incorrectly solved.

## Integrity Checks

- **Exact-two-output:** PASS
- **Deterministic replay:** PASS
- **Expected-output isolation:** PASS
- **Split disjoint:** PASS

## Generated Log Paths

- Benchmark after repair: `/data/data/com.termux/files/usr/tmp/weslr_benchmark_after_repair_v1.log`
- Audit after repair: `/data/data/com.termux/files/usr/tmp/weslr_audit_after_repair_v1.json`

(Both outside repo, not committed.)

## Health Check

- **Script:** `./scripts/chat_weslr_de_health_check.sh --mode source-repo`
- **Status:** PASS (6 pass, 0 fail, 3 warn, 0 skip)
- **Warnings:** Runtime network probes skipped (non-runtime host)

## Validation Summary

- `python -m py_compile` on changed Python files: PASS
- Focused generator tests (10 tests): PASS
- Adversarial audit tests (16 tests): PASS
- Heldout benchmark tests (8 tests): PASS
- Heldout benchmark rerun: PASS (baseline recorded above)
- Adversarial audit rerun: PASS (all 7 families correctly rejected)
- `git diff --check`: clean
- `python weslr/tests/release_gate_v1.py`: PASS
- `./scripts/weslr_release_check.sh`: PASS
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`: PASS

## Limitations

- Synthetic generators only; no public ARC data was read or scored
- No Kaggle submission was made
- No solver capability was repaired
- The repair addresses benchmark definition only; solver behavior is unchanged
- The `object_bbox` identity-on-tight-grid behavior remains a solver property that could interact with other adversarial designs in the future

## Next Recommended Lane

`final_synthetic_score_report_lane` — produce a final synthetic score report with the repaired benchmark definitions, documenting the clean adversarial boundary and the honest heldout score.

## Readiness Verdict

`benchmark_definition_repair_v1_passed_ready_for_final_synthetic_score_report_lane`