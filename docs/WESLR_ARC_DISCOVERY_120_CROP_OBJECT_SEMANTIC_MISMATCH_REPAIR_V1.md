# WESLR ARC Discovery 120 — crop_object Semantic Mismatch Repair Report (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `REPAIR_ARC_DISCOVERY_120_CROP_OBJECT_ORACLE_SOLVER_SEMANTIC_MISMATCH_V1`
**Start HEAD**: `825d3ae9`
**End HEAD**: `83e325bc`
**Date**: 2026-07-02

---

## 1. Preflight

| Check | Result |
|-------|--------|
| `pwd` | `/data/data/com.termux/files/home/weslr-pr47-clean` ✅ |
| `git status` | one modified file (`weslr/tests/continuity/governance_scorecards.json` — auto-generated timestamp drift, not related) ✅ |
| `git branch --show-current` | `occ-discovery-doctrine-implementation-20260613` ✅ |
| `git rev-parse --short HEAD` | `825d3ae9` ✅ matches expected |

**Actual preflight HEAD**: `825d3ae9`
**Metadata mismatch noted**: no — receipt HEAD matches actual. Fallback runner/report HEAD `6008c2b9` is the prior commit, not a mismatch.

---

## 2. Root Cause Confirmation

### Oracle `crop_object` behavior (`arc_bh80_oracle.py`)

The oracle `reference_primitive("crop_object", grid, params)`:
1. Finds the largest connected component using its own `_connected_components()` + `_largest_component()`
2. Computes the bbox of that largest component only
3. Crops the grid to that bbox

### Solver `crop_object` behavior before repair (`arc_synthetic_3_step_real_dispatch.py`)

The solver mapped `crop_object` → `crop_to_non_background_bbox` in `NAME_TO_ADAPTER_ID`, which:
1. Finds the bounding box of ALL non-background pixels (including distractors)
2. Crops the grid to that all-encompassing bbox

### Divergence

When distractors are present, the all-non-bg bbox is larger than the largest-component bbox. This caused different output dimensions and content downstream.

### Confirmed on failing tasks

| Task | Oracle dims | Solver dims (before) | Solver dims (after) |
|------|-------------|---------------------|---------------------|
| T120_084 | 4×3 | 7×5 | 4×3 ✅ |
| T120_093 | 4×4 | 7×7 | 4×4 ✅ |

### BH80 impact analysis

All 5 BH80 tasks using `crop_object` (BH80_007, BH80_008, BH80_042, BH80_052, BH80_058) have **zero distractors**. With zero distractors, the all-non-bg bbox equals the largest-component bbox, so the existing behavior was accidentally correct for BH80. The fix does not change BH80 behavior.

---

## 3. Semantic Contract Chosen

**`crop_object` crops to the largest connected component's bounding box.**

This is the oracle's existing contract, and it is the correct semantic for "crop to the object" (singular). The alternative — crop to all non-background bbox — is the contract for a different primitive (e.g., `crop_to_non_background_bbox`), not for `crop_object`.

The solver was using `crop_to_non_background_bbox` as a proxy, which is incorrect when multiple components exist. The fix aligns the solver to the oracle contract.

### Relationship to other primitives

| Primitive | Semantic | Crop target |
|-----------|----------|-------------|
| `crop_object` | Crop to largest object | Largest connected component bbox |
| `crop` | Crop to largest object | Largest connected component bbox (already aligned) |
| `extract` | Extract largest object | Largest connected component as sub-grid |
| `extract_changed_region` | Crop to largest component bbox | Largest connected component bbox |

`crop_object` and `crop` are now equivalent (both crop to largest component bbox). They remain distinct names for semantic clarity but produce identical output.

---

## 4. Files Changed

| File | Change | Lines |
|------|--------|-------|
| `weslr/arc_synthetic_3_step_real_dispatch.py` | Added `crop_object` custom wrapper (largest component bbox) | +10 |
| `weslr/tests/test_crop_object_semantic_repair_v1.py` | 13 focused tests | +198 (new file) |

### Files not modified

- Oracle (`arc_bh80_oracle.py`) — unchanged ✅
- Semantic scorer (`arc_bh80_semantic_scorer.py`) — unchanged ✅
- Materializer (`arc_bh80_materializer.py`) — unchanged ✅
- 120 generator (`arc_discovery_120_generator.py`) — unchanged ✅
- 120 pilot runner (`arc_discovery_120_semantic_pilot.py`) — unchanged ✅
- Native arc oracle/solver — unchanged ✅
- Protected files — unchanged ✅

---

## 5. Tests Added

| Test class | Tests | Purpose |
|------------|-------|---------|
| TestCropObjectLargestComponentBbox | 5 | Unit tests for crop_object with distractors, edge cases, empty grid |
| TestT120Chains | 2 | Integration tests for T120_084 and T120_093 full 3-step chains |
| TestBH80Regression | 2 | BH80 crop_object tasks remain exact; full BH80 80/80 |
| Test120ScoredResult | 4 | 120 scored 110/110; probes unscored; anti-cheat pass; clean gate |
| **Total** | **13** | All PASS ✅ |

---

## 6. Results

### 6.1 BH80 Before/After

| Metric | Before | After |
|--------|--------|-------|
| BH80 semantic_exact | 80/80 | 80/80 ✅ |

### 6.2 120 Scored Before/After

| Metric | Before | After |
|--------|--------|-------|
| scored_exact | 108/110 | **110/110** ✅ |
| failed | 2 | **0** ✅ |
| unsupported | 0 | 0 |
| structural_pass | 110 | 110 |
| semantic_exact_rate | 98.18% | **100.00%** ✅ |

### 6.3 T120_084 Result

| Metric | Before | After |
|--------|--------|-------|
| Result | failed | **semantic_exact** ✅ |

### 6.4 T120_093 Result

| Metric | Before | After |
|--------|--------|-------|
| Result | failed | **semantic_exact** ✅ |

### 6.5 Subset Results After Repair

| Subset | Total | semantic_exact |
|--------|-------|---------------|
| BH80 | 80 | 80/80 (100%) |
| color_invert | 10 | 10/10 (100%) |
| old-primitive harder | 10 | 10/10 (100%) |
| adversarial/control | 10 | 10/10 (100%) |

### 6.6 Candidate Probes

| Metric | Value |
|--------|-------|
| candidate_probe_counted_as_solved | **0** ✅ |

---

## 7. Anti-Cheat Rerun Results

| # | Control | Result |
|---|---------|--------|
| 1 | No default `[[1]]` scenes | ✅ PASS |
| 2 | Oracle output diversity ≥ 30 | ✅ PASS (33) |
| 3 | Solver output diversity ≥ 20 | ✅ PASS (33) |
| 4 | No-op shadow control | ✅ PASS |
| 5 | Primitive-order negative control | ✅ PASS |
| 6 | Unsupported primitive sentinel | ✅ PASS |
| 7 | Oracle avoids solver dispatch | ✅ PASS |
| 8 | Semantic scorer uses grid equality | ✅ PASS |
| 9 | structural_pass separate | ✅ PASS |
| 10 | Unpromoted primitive blocked | ✅ PASS |
| 11 | Candidate probe separation | ✅ PASS |
| 12 | Scene_spec read audit | ✅ PASS |
| 13 | Output diversity audit | ✅ PASS |

**All 13 anti-cheat controls: PASS** ✅

---

## 8. Gate Results

| Gate | Threshold | Actual | Reached |
|------|-----------|--------|---------|
| Scored clean | 110/110 | 110/110 | ✅ Yes |
| Scored preferred | ≥ 103/110 | 110/110 | ✅ Yes |
| Scored strong | ≥ 99/110 | 110/110 | ✅ Yes |
| Scored minimal | ≥ 94/110 | 110/110 | ✅ Yes |
| BH80 clean | 80/80 | 80/80 | ✅ Yes |
| BH80 preferred | ≥ 75/80 | 80/80 | ✅ Yes |
| BH80 strong | ≥ 72/80 | 80/80 | ✅ Yes |
| BH80 minimal | ≥ 68/80 | 80/80 | ✅ Yes |

**All gates reached, including clean.** ✅

---

## 9. Validation

| Check | Result |
|-------|--------|
| `py_compile` touched module | PASS ✅ |
| Focused pytest (13 tests) | 13/13 PASS ✅ |
| Related suites (167 tests) | 167/167 PASS ✅ |
| `git diff --check` | clean ✅ |
| `python weslr/tests/release_gate_v1.py` | `WESLR_RELEASE_GATE_V1_OK` ✅ |
| `./scripts/weslr_release_check.sh` | `WESLR_RELEASE_CHECK_OK` ✅ |
| `./scripts/chat_weslr_de_health_check.sh --mode source-repo` | PASS=6 FAIL=0 WARN=3 ✅ |

---

## 10. Receipt

| Field | Value |
|-------|-------|
| Start HEAD | `825d3ae9` |
| End HEAD | `83e325bc` |
| Commit | yes (`83e325bc`) |
| Actual preflight HEAD | `825d3ae9` |
| Metadata mismatch noted | no |
| crop_object root cause confirmed | yes ✅ (solver used all-non-bg bbox, oracle uses largest component bbox) |
| solver aligned to oracle | yes ✅ |
| oracle changed | no ✅ |
| scorer unchanged | yes ✅ |
| BH80 before/after | 80/80 → 80/80 ✅ |
| 120 scored_exact before/after | 108/110 → 110/110 ✅ |
| T120_084 fixed | yes ✅ |
| T120_093 fixed | yes ✅ |
| candidate probes counted as solved 0 | yes ✅ |
| anti-cheat controls pass | yes ✅ (13/13) |
| reached clean 110/110 | yes ✅ |
| validation | PASS ✅ |
| push avoided | yes ✅ |
| recommended next lane | `DESIGN_ARC_NATIVE_PROMOTION_BATCH_2_V1` |

---

## 11. Next Lane Recommendation

**Recommended next lane**: `DESIGN_ARC_NATIVE_PROMOTION_BATCH_2_V1`

The 120-suite scored gate is now clean (110/110). The BH80 sub-gate is clean (80/80). All anti-cheat controls pass. The next productive direction is promotion batch 2 for candidate primitives.

The candidate probes (T120_101–T120_110) all returned unsupported because no oracle or solver implementations exist for the 10 unpromoted candidates. Promotion batch 2 should:

1. Implement oracle + solver for the highest-priority candidates:
   - `mask_border_only`
   - `geom_flip_vertical`
   - `topo_fill_holes`
   - `constr_draw_rect_around`
2. Run the 9-stage promotion pipeline for each
3. Move promoted candidates from `candidate_probe` to `scored` in the 120 suite
4. Rerun the 120 semantic pilot with expanded scored set
5. Verify BH80 remains 80/80 and anti-cheat controls remain 13/13