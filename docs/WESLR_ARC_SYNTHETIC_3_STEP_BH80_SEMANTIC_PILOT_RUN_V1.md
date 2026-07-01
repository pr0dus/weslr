# ARC Synthetic 3‑Step – BH80 Semantic Pilot Run (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `RUN_ARC_SYNTHETIC_3_STEP_BH80_SEMANTIC_PILOT_V1`
**Start HEAD**: `788e0c14`

---

## 1. Preflight

| Check | Result |
|-------|--------|
| `pwd` | `/data/data/com.termux/files/home/weslr-pr47-clean` ✅ |
| `git status` | clean ✅ |
| `git branch --show-current` | `occ-discovery-doctrine-implementation-20260613` ✅ |
| `git rev-parse --short HEAD` | `788e0c14` ✅ |
| Metadata mismatch | none — HEAD matches expected ✅ |

---

## 2. Semantic Scoring Method

| Component | Implementation |
|-----------|---------------|
| Input grid | Materialized from enriched scene_spec via `materialize_scene()` |
| Solver | `solver_run_with_input()` — runs `run_primitive()` dispatch on materialized grid |
| Oracle | `run_oracle_pipeline()` — independent reference primitives, no shared code with solver |
| Scorer | `grids_equal(solver_grid, oracle_grid)` — element‑wise and dimension‑wise comparison |
| `semantic_exact` | Solver final grid equals oracle final grid |
| `structural_pass` | All primitives supported (reported separately, never as exact) |

---

## 3. Aggregate Metrics

| Metric | Value |
|--------|-------|
| **semantic_exact** | 27 |
| **failed** | 53 |
| **unsupported** | 0 |
| **structural_pass** | 80 |
| **semantic_exact_rate** | 33.8% |

---

## 4. Gate Attainment

| Gate | Requirement | Achieved |
|------|-------------|----------|
| **Semantic Minimal** | ≥ 68 semantic_exact (85%) | NOT REACHED (27) ❌ |
| **Semantic Strong** | ≥ 72 semantic_exact (90%) | NOT REACHED (27) ❌ |
| **Semantic Clean** | 80/80 semantic_exact (100%) | NOT REACHED (27) ❌ |

---

## 5. Category Breakdown

| Category | Total | semantic_exact | failed | unsupported | structural |
|----------|-------|---------------|--------|-------------|------------|
| Known‑family anchors | 18 | 5 | 13 | 0 | 18 |
| Hybrid | 20 | 9 | 11 | 0 | 20 |
| Mutation | 20 | 7 | 13 | 0 | 20 |
| Unknown‑family | 22 | 6 | 16 | 0 | 22 |
| **Total** | **80** | **27** | **53** | **0** | **80** |

---

## 6. Difficulty Breakdown

| Difficulty | Total | semantic_exact | failed | unsupported |
|------------|-------|---------------|--------|-------------|
| Medium | 16 | 5 | 11 | 0 |
| Hard | 48 | 15 | 33 | 0 |
| Adversarial | 16 | 7 | 9 | 0 |
| **Total** | **80** | **27** | **53** | **0** |

---

## 7. Failure Clusters

### 7.1 By family

| Family | Total | Failed | Failure rate |
|--------|-------|--------|-------------|
| F001 | 2 | 2 | 100% |
| F002 | 2 | 2 | 100% |
| F004 | 2 | 1 | 50% |
| F005 | 2 | 2 | 100% |
| F006 | 3 | 3 | 100% |
| F007 | 2 | 2 | 100% |
| F008 | 2 | 1 | 50% |
| BH‑A | 10 | 1 | 10% |
| BH‑B | 10 | 10 | 100% |
| BH‑C | 14 | 9 | 64% |
| BH‑D | 6 | 4 | 67% |
| BH‑E | 7 | 7 | 100% |
| BH‑F | 7 | 7 | 100% |
| BH‑G | 8 | 2 | 25% |

### 7.2 Root cause clusters

**Cluster 1: `extract` / `extract_object` / `extract_changed_region` dimension mismatch (6+ failures)**
- Solver's `extract` maps to `extract_largest_object` adapter which returns the full grid
- Oracle's `extract` crops to the bounding box of the largest component
- Result: solver produces 10×10, oracle produces 3×3 → `failed`

**Cluster 2: `normalize_position` semantic mismatch (18+ failures, especially BH‑B)**
- Solver's `normalize_position` computes centroid metadata but does NOT translate the grid
- Oracle's `normalize_position` translates the entire grid to center the centroid
- Result: same dimensions but different cell content → `failed`

**Cluster 3: `recolor` background detection mismatch**
- Solver and oracle may detect different background values
- When grid has more non‑background than background cells, detection diverges
- Result: same dimensions but different recolored values → `failed`

**Cluster 4: `extract_boundary` semantic mismatch**
- Solver's `extract_boundary` returns the grid unchanged with bbox metadata
- Oracle's `extract_boundary` highlights boundary cells on the grid
- Result: same dimensions but different content → `failed`

**Cluster 5: `isolate_largest` semantic mismatch**
- Solver's `isolate_largest` returns the grid unchanged with bbox metadata
- Oracle's `isolate_largest` removes non‑largest components from the grid
- Result: same dimensions but different content → `failed`

### 7.3 Highest‑failure families

| Family | Root cause |
|--------|-----------|
| BH‑B (10/10 fail) | All use `normalize_position` — solver doesn't translate grid |
| BH‑E (7/7 fail) | All use `extract` + `transform` — solver `extract` doesn't crop |
| BH‑F (7/7 fail) | All use `normalize_position` + `place_back` — solver doesn't translate |
| F001/F002 (4/4 fail) | `extract`/`extract_object` dimension mismatch |

---

## 8. Anti‑Cheat Rerun Results

| Check | Result |
|-------|--------|
| No `[[1]]` scenes | 0 default scenes ✅ |
| Oracle output diversity | 27 unique outputs ✅ |
| Solver output diversity | 56 unique outputs ✅ |
| No‑op shadow control | PASS (outputs differ) ✅ |
| Primitive‑order reversal control | PASS (outputs differ) ✅ |
| Unsupported primitive sentinel | PASS (both return unsupported) ✅ |
| Oracle avoids solver dispatch | PASS (no import) ✅ |
| Semantic scorer uses grid equality | PASS ✅ |
| structural_pass separate from semantic_exact | PASS ✅ |

All 9 anti‑cheat controls pass. The 33.8% result is genuine — the scorer correctly detects semantic mismatches.

---

## 9. Interpretation

### What the 27/80 proves
The semantic scoring system **works**. It correctly distinguishes between:
- Tasks where solver and oracle agree (27 tasks — mostly simple chains like `crop → rotate → recolor` where both produce the same output)
- Tasks where solver and oracle diverge (53 tasks — due to real semantic differences in primitive implementations)

### What the 53 failures mean
The solver dispatch and the oracle have different semantics for several primitives:
1. `extract` — solver returns full grid, oracle crops to bbox
2. `normalize_position` — solver computes metadata only, oracle translates grid
3. `isolate_largest` — solver returns metadata, oracle modifies grid
4. `extract_boundary` — solver returns metadata, oracle highlights cells
5. `extract_changed_region` — solver returns metadata, oracle crops to bbox

These are **real semantic gaps**, not scoring bugs. The anti‑cheat controls confirm the scorer is working correctly.

### Comparison with prior structural 80/80
The prior 80/80 "exact" was **structural dispatch support** — it only checked that primitives didn't crash. The real semantic score is **27/80 (33.8%)**. This is the first honest measurement of solver semantic correctness.

---

## 10. BH80 Semantic Regression Gate Readiness

**The BH80 semantic regression gate mechanism is ready.** The gate thresholds need recalibration based on this baseline:

| Gate | Current threshold | Recommended new baseline |
|------|-------------------|--------------------------|
| Semantic Minimal | 68/80 (85%) | 27/80 (33.8%) — to be raised as primitives are aligned |
| Semantic Strong | 72/80 (90%) | TBD after primitive alignment |
| Semantic Clean | 80/80 (100%) | TBD after full primitive alignment |

The gate can be used immediately to prevent regressions: any solver change that lowers the score below 27 is a regression.

---

## 11. 120 Entry Conditions

| Condition | Met? |
|-----------|------|
| BH80 oracle exists | ✅ |
| BH80 semantic scoring exists | ✅ |
| No‑op controls fail as expected | ✅ |
| Primitive‑order negative controls fail as expected | ✅ |
| scene_spec is actually read | ✅ |
| Output diversity is nontrivial (≥ 20) | ✅ (27 oracle, 56 solver) |
| At least one semantic BH80 run recorded | ✅ (this run) |

**All 7 conditions are met.** The 120‑task expansion may be designed.

However, it is recommended to first align solver primitives with oracle semantics to raise the semantic score above the minimal gate before expanding to 120 tasks.

---

## 12. Validation

| Check | Result |
|-------|--------|
| `py_compile` | PASS ✅ (no code changes) |
| Focused pytest (70 tests) | 70/70 PASS ✅ |
| `git diff --check` | clean ✅ |
| `python weslr/tests/release_gate_v1.py` | `WESLR_RELEASE_GATE_V1_OK` ✅ |
| `./scripts/weslr_release_check.sh` | `WESLR_RELEASE_CHECK_OK` ✅ |
| `./scripts/chat_weslr_de_health_check.sh --mode source-repo` | PASS=6 FAIL=0 ✅ |

---

## Receipt

| Field | Value |
|-------|-------|
| **Start HEAD** | `788e0c14` |
| **End HEAD** | `cf3ae667` |
| **Commit** | yes (`cf3ae667`) |
| **Actual preflight HEAD** | `788e0c14` ✅ |
| **Metadata mismatch noted** | no ✅ |
| **80 tasks generated** | yes ✅ |
| **80 scenes materialized** | yes ✅ |
| **semantic_exact** | 27 |
| **unsupported** | 0 |
| **failed** | 53 |
| **structural_pass** | 80 |
| **semantic_exact_rate** | 33.8% |
| **Reached minimal (68/80)** | no ❌ |
| **Reached strong (72/80)** | no ❌ |
| **Reached clean (80/80)** | no ❌ |
| **No default `[[1]]` scenes** | yes ✅ |
| **Oracle output diversity** | 27 unique ✅ |
| **Solver output diversity** | 56 unique ✅ |
| **No‑op control pass** | yes ✅ |
| **Primitive‑order control pass** | yes ✅ |
| **Unsupported sentinel pass** | yes ✅ |
| **structural_pass separate** | yes ✅ |
| **BH80 semantic regression gate ready** | yes (mechanism ready, thresholds need recalibration) ✅ |
| **120 entry conditions met** | yes (all 7 conditions) ✅ |
| **Validation** | PASS ✅ |
| **Push avoided** | yes ✅ |
| **Recommended next lane** | `ALIGN_SOLVER_PRIMITIVES_TO_ORACLE_SEMANTICS_V1` |