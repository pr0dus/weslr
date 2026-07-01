# ARC Synthetic 3‑Step – Solver/Oracle Primitive Alignment Report (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `ALIGN_SOLVER_PRIMITIVES_TO_ORACLE_SEMANTICS_V1`
**Start HEAD**: `4e849260`

---

## 1. Preflight

| Check | Result |
|-------|--------|
| `pwd` | `/data/data/com.termux/files/home/weslr-pr47-clean` ✅ |
| `git status` | clean ✅ |
| `git branch --show-current` | `occ-discovery-doctrine-implementation-20260613` ✅ |
| `git rev-parse --short HEAD` | `4e849260` ✅ |
| Metadata mismatch | none ✅ |

---

## 2. Primitives Aligned

| # | Primitive | Old solver behavior | New solver behavior (aligned to oracle) |
|---|-----------|---------------------|----------------------------------------|
| 1 | `extract` / `extract_object` / `extract_largest_object` | Returned full grid via adapter | Crops to bounding box of largest component |
| 2 | `extract_changed_region` | Returned grid unchanged with bbox metadata | Crops to bounding box of largest component |
| 3 | `normalize_position` | Computed centroid metadata, grid unchanged | Translates grid so centroid is centered |
| 4 | `isolate_largest` | Returned grid unchanged with bbox metadata | Removes non‑largest components, keeps only largest |
| 5 | `extract_boundary` | Returned grid unchanged with bbox metadata | Highlights bounding‑box boundary cells on grid |

### `recolor` background detection
The solver's `recolor` uses `_background_value_from_grid()` which finds the most common value. The oracle uses the same logic. After the alignment of `extract` (which now crops), the grids entering `recolor` are more consistent between solver and oracle, reducing background detection mismatches.

### Oracle unchanged
The oracle was **not modified** in this lane. All alignment was on the solver side. ✅

---

## 3. Files Modified

| File | Change |
|------|--------|
| `weslr/arc_synthetic_3_step_real_dispatch.py` | 5 primitive wrappers realigned: `extract`, `extract_changed_region`, `normalize_position`, `isolate_largest`, `extract_boundary` |

No other files modified. Oracle, materializer, scorer, enriched scenes, tests — all unchanged. ✅

---

## 4. Semantic Pilot Rerun

| Metric | Before alignment | After alignment |
|--------|-----------------|-----------------|
| **semantic_exact** | 27 | **50** |
| **failed** | 53 | **30** |
| **unsupported** | 0 | 0 |
| **structural_pass** | 80 | 80 |
| **semantic_exact_rate** | 33.8% | **62.5%** |

### Gate attainment after alignment
| Gate | Requirement | Achieved |
|------|-------------|----------|
| Semantic Minimal | 68/80 (85%) | NOT REACHED (50) ❌ |
| Semantic Strong | 72/80 (90%) | NOT REACHED (50) ❌ |
| Semantic Clean | 80/80 (100%) | NOT REACHED (50) ❌ |

### Improvement
- **+23 semantic_exact** (27 → 50)
- **+28.7 percentage points** (33.8% → 62.5%)
- **−23 failures** (53 → 30)

---

## 5. Remaining Failure Clusters (30 tasks)

All 30 remaining failures are **same‑dimension, different‑content** — no dimension mismatches remain.

### By family

| Family | Failed | Total | Failure rate |
|--------|--------|-------|-------------|
| F004 | 1 | 2 | 50% |
| F005 | 2 | 2 | 100% |
| F006 | 3 | 3 | 100% |
| F007 | 2 | 2 | 100% |
| F008 | 1 | 2 | 50% |
| BH‑B | 5 | 10 | 50% |
| BH‑C | 6 | 14 | 43% |
| BH‑D | 3 | 6 | 50% |
| BH‑F | 5 | 7 | 71% |
| BH‑G | 2 | 8 | 25% |

### Root cause clusters

**Cluster 1: `recolor` after crop/extract — background detection mismatch**
When `extract` or `crop` produces a grid where the background is the majority, `recolor` correctly replaces non‑background with 2. But when the crop produces a grid where the object fills most of the grid, the most‑common‑value detection may pick the object color as "background" instead of 0.

**Cluster 2: `normalize_position` translation rounding**
The solver and oracle may use different rounding for the centroid‑to‑center translation, causing off‑by‑one cell placement.

**Cluster 3: `place_back` canvas context**
The solver's `place_back` uses the adapter (no original canvas context), while the oracle's `place_back` creates a canvas from params. Without passing original size through the solver adapter, `place_back` behavior diverges.

**Cluster 4: `recolor_boundary` vs `extract_boundary` interaction**
After `extract_boundary` now highlights boundary cells, `recolor_boundary` may apply differently than the oracle expects.

---

## 6. Anti‑Cheat Controls

| Check | Result |
|-------|--------|
| No `[[1]]` scenes | ✅ |
| Oracle output diversity | 27 unique ✅ |
| Solver output diversity | 56 unique ✅ |
| No‑op control | PASS ✅ |
| Primitive‑order control | PASS ✅ |
| Unsupported sentinel | PASS ✅ |
| Oracle avoids solver dispatch | PASS ✅ |
| Semantic scorer uses grid equality | PASS ✅ |
| structural_pass separate | PASS ✅ |

All 9 anti‑cheat controls still pass. ✅

---

## 7. Test Results

| Check | Result |
|-------|--------|
| `py_compile` | PASS ✅ |
| Focused pytest (70 tests) | 70/70 PASS ✅ |
| `git diff --check` | clean ✅ |
| `python weslr/tests/release_gate_v1.py` | `WESLR_RELEASE_GATE_V1_OK` ✅ |
| `./scripts/weslr_release_check.sh` | `WESLR_RELEASE_CHECK_OK` ✅ |
| `./scripts/chat_weslr_de_health_check.sh --mode source-repo` | PASS=6 FAIL=0 ✅ |

---

## Receipt

| Field | Value |
|-------|-------|
| **Start HEAD** | `4e849260` |
| **End HEAD** | `768c7b93` |
| **Commit** | yes (`768c7b93`) |
| **Actual preflight HEAD** | `4e849260` ✅ |
| **Metadata mismatch noted** | no ✅ |
| **extract/extract_object/extract_changed_region aligned** | yes ✅ |
| **normalize_position aligned** | yes ✅ |
| **isolate_largest aligned** | yes ✅ |
| **extract_boundary aligned** | yes ✅ |
| **recolor/background behavior aligned** | partially (improved via extract alignment, residual background detection mismatches remain) ⚠️ |
| **Oracle unchanged** | yes ✅ |
| **Semantic scorer unchanged** | yes ✅ |
| **Anti‑cheat controls pass** | yes ✅ |
| **BH80 semantic rerun performed** | yes ✅ |
| **Previous semantic_exact** | 27/80 (33.8%) ✅ |
| **New semantic_exact** | **50/80 (62.5%)** |
| **Validation** | PASS ✅ |
| **Push avoided** | yes ✅ |
| **Recommended next lane** | `REPAIR_REMAINING_SEMANTIC_MISMATCHES_V1` |