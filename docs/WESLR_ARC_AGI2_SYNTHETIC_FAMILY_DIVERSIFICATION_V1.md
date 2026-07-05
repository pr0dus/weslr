# WESLR ARC-AGI-2 Synthetic Family Diversification V1

## Repo / Branch

- **Repo:** `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Branch:** `main`
- **Start HEAD (expected):** `94cee9890a14e7169396994387a8e754fa700de8`
- **Actual preflight HEAD:** `94cee9890a14e7169396994387a8e754fa700de8`
- **End HEAD:** (recorded in chat after commit)

## Previous Lane

- **Lane:** `WESLR_ARC_AGI2_REMAINING_FALLBACK_FAMILY_AUDIT_V1`
- **Verdict:** `remaining_fallback_family_audit_v1_passed_ready_for_synthetic_family_diversification_lane`
- **Finding:** All 56 unsolved tasks across dev + heldout are correct adversarial rejections. Zero normal-family failures. Zero unexpected fallback. Zero repair candidates.

## Files Added / Changed

| File | Status |
|------|--------|
| `weslr/arc_synthetic_family_diversification_v1.py` | **Added** — 8 new synthetic family generators |
| `weslr/tests/test_arc_synthetic_family_diversification_v1.py` | **Added** — 9 tests for diversification |
| `weslr/arc_heldout_synthetic_discovery_benchmark_v1.py` | **Modified** — added `include_diversified_families` support |
| `scripts/run_arc_heldout_synthetic_discovery_benchmark_v1.py` | **Modified** — added `--include-diversified-families` flag |
| `docs/WESLR_ARC_AGI2_SYNTHETIC_FAMILY_DIVERSIFICATION_V1.md` | **Added** — this report |

## New Family Definitions

All 8 families are single-step synthetic tasks. Each has 1 train pair and 1 test pair. No public ARC data is used.

### 1. `complete_horizontal_symmetry`
- **Input:** Left half of a horizontally symmetric shape (e.g., 3×2 left half of a 3×4 shape)
- **Output:** Full symmetric shape (left half + horizontal mirror)
- **Train:** Color 1 shape, 5×6 grid
- **Test:** Different color, same shape structure
- **Difficulty:** medium
- **Expected behavior:** The solver must detect the partial shape and mirror it horizontally

### 2. `complete_vertical_symmetry`
- **Input:** Top half of a vertically symmetric shape (e.g., 2×3 top half of a 4×3 shape)
- **Output:** Full symmetric shape (top half + vertical mirror)
- **Train:** Color 1 shape, 6×5 grid
- **Test:** Different color, same shape structure
- **Difficulty:** medium
- **Expected behavior:** The solver must detect the partial shape and mirror it vertically

### 3. `fill_enclosed_hole`
- **Input:** A 5×5 ring (border of color, interior background)
- **Output:** Fully filled 5×5 block of the same color
- **Train:** Color 1 ring
- **Test:** Different color ring
- **Difficulty:** medium
- **Expected behavior:** The solver must detect the enclosed hole and fill it with the object color

### 4. `remove_distractor_object`
- **Input:** 5×5 grid with a 2×2 target block and a single-cell distractor
- **Output:** Only the target block, distractor removed
- **Train:** Target at top-left, distractor at bottom-right
- **Test:** Target at center, distractor at top-left
- **Difficulty:** medium
- **Expected behavior:** The solver must identify which object is the target (the larger one) and remove the distractor

### 5. `copy_object_to_marker`
- **Input:** 5×5 grid with a 2×2 object and a marker cell elsewhere
- **Output:** Original object preserved, plus a copy of the object placed near the marker
- **Train:** Object at top-left, marker at bottom-right
- **Test:** Object at center-left, marker at bottom-right
- **Difficulty:** hard
- **Expected behavior:** The solver must detect the marker, identify the object to copy, and place a copy near the marker

### 6. `extend_line_to_boundary`
- **Input:** 5×5 grid with a partial line (3 cells of a horizontal or vertical line)
- **Output:** Full line extended to grid boundaries
- **Train:** Partial horizontal line at row 2, columns 1-3
- **Test:** Partial vertical line at column 2, rows 1-3
- **Difficulty:** medium
- **Expected behavior:** The solver must detect the line direction and extend it to the grid edges

### 7. `extract_row_or_column_by_marker`
- **Input:** 5×5 grid with a marker cell in the last column of a row containing a colored cell
- **Output:** A 1×5 row extracted from the marked row
- **Train:** Marker at row 2, column 4; colored cell at row 2, column 0
- **Test:** Marker at row 1, column 4; colored cell at row 1, column 1
- **Difficulty:** hard
- **Expected behavior:** The solver must identify the marker, determine which row it points to, and extract that row

### 8. `recolor_by_object_size`
- **Input:** 5×5 grid with two objects: a 2×2 block (4 cells) and a 1×1 dot (1 cell)
- **Output:** The smallest object (1 cell) is recolored to a new color; the larger object unchanged
- **Train:** 2×2 block in color A, dot in color B → dot recolored to new color
- **Test:** Same size relationship, different positions
- **Difficulty:** hard
- **Expected behavior:** The solver must compare object sizes, identify the smallest, and recolor it

## Baseline V1 Benchmark Result (without diversified families)

| Split | Total | Solved | Unsolved | Fallback | Exceptions | Solve % |
|-------|-------|--------|----------|----------|------------|---------|
| Dev | 81 | 60 | 21 | 18 | 0 | 74.1% |
| Heldout | 135 | 100 | 35 | 30 | 0 | 74.1% |
| **Combined** | **216** | **160** | **56** | **48** | **0** | **74.1%** |

- Adversarial rejection pass: 35 (heldout)
- Exact-two-output: PASS
- Deterministic replay: PASS
- Expected-output isolation: PASS
- Split disjoint: PASS
- Leakage audit: PASS

**Log path:** `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T194513/`

## Diversified Benchmark Result (with 8 new families)

| Split | Total | Solved | Unsolved | Fallback | Exceptions | Solve % |
|-------|-------|--------|----------|----------|------------|---------|
| Dev | 105 | 66 | 39 | 33 | 0 | 62.9% |
| Heldout | 159 | 106 | 53 | 45 | 0 | 66.7% |
| **Combined** | **264** | **172** | **92** | **78** | **0** | **65.2%** |

- Adversarial rejection pass: 35 (heldout)
- Exact-two-output: PASS
- Deterministic replay: PASS
- Expected-output isolation: PASS
- Split disjoint: PASS
- Leakage audit: PASS

**Log path:** `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T194852/`

## Per-New-Family Results

### Dev Split (3 tasks per family)

| Family | Generated | Solved | Unsolved | Fallback | Dominant Failure | Likely Missing Capability |
|--------|-----------|--------|----------|----------|------------------|--------------------------|
| complete_horizontal_symmetry | 3 | 0 | 3 | 3 | fallback_only | No symmetry detection |
| complete_vertical_symmetry | 3 | 0 | 3 | 3 | fallback_only | No symmetry detection |
| fill_enclosed_hole | 3 | 0 | 3 | 0 | ambiguous_expected_rejection | No hole-fill primitive |
| remove_distractor_object | 3 | 3 | 0 | 0 | — | Solved! |
| copy_object_to_marker | 3 | 0 | 3 | 3 | fallback_only | No copy-to-marker primitive |
| extend_line_to_boundary | 3 | 0 | 3 | 3 | fallback_only | No line extension primitive |
| extract_row_or_column_by_marker | 3 | 0 | 3 | 3 | fallback_only | No row extraction primitive |
| recolor_by_object_size | 3 | 3 | 0 | 0 | — | Solved! |

### Heldout Split (3 tasks per family)

| Family | Generated | Solved | Unsolved | Fallback | Dominant Failure | Likely Missing Capability |
|--------|-----------|--------|----------|----------|------------------|--------------------------|
| complete_horizontal_symmetry | 3 | 0 | 3 | 3 | fallback_only | No symmetry detection |
| complete_vertical_symmetry | 3 | 0 | 3 | 3 | fallback_only | No symmetry detection |
| fill_enclosed_hole | 3 | 0 | 3 | 0 | ambiguous_expected_rejection | No hole-fill primitive |
| remove_distractor_object | 3 | 3 | 0 | 0 | — | Solved! |
| copy_object_to_marker | 3 | 0 | 3 | 3 | fallback_only | No copy-to-marker primitive |
| extend_line_to_boundary | 3 | 0 | 3 | 3 | fallback_only | No line extension primitive |
| extract_row_or_column_by_marker | 3 | 0 | 3 | 3 | fallback_only | No row extraction primitive |
| recolor_by_object_size | 3 | 3 | 0 | 0 | — | Solved! |

## Score Impact

- **Combined solve rate dropped from 74.1% to 65.2%** (8.9 percentage points)
- **6 of 8 new families are unsolved** — the solver lacks symmetry, hole-fill, copy-to-marker, line-extension, and row-extraction primitives
- **2 of 8 new families are solved** — `remove_distractor_object` and `recolor_by_object_size` are within the solver's existing capabilities
- **0 exceptions** across all new families
- **0 adversarial boundary failures** — the original 7 adversarial families remain correctly rejected

## Event Log Analysis

- **Total events:** 936 (diversified run)
- **By level:** INFO=328, DEBUG=528, WARNING=78, SUMMARY=2
- **By phase:** generation=266, solver_execution=264, evaluation=322, failure_classification=78, audit=3
- **Leakage audit:** PASS (0 unsafe metadata, 0 expected-output leakage, 0 raw-grid leakage)
- **Consistency checks:** All clean

## Integrity Checks

| Check | Status |
|-------|--------|
| Exact-two-output | PASS |
| Deterministic replay | PASS |
| Expected-output isolation | PASS |
| Split disjoint | PASS |
| Leakage audit | PASS |
| Malformed count | 0 |
| Exception count | 0 |
| Public-data boundary | No public ARC data read or scored |
| Generated logs outside repo | Yes — `/data/data/com.termux/files/home/weslr-arc-run-logs/` |

## Validation Summary

| Check | Status |
|-------|--------|
| `python -m py_compile` on changed files | PASS |
| Focused diversification tests (9 tests) | PASS |
| Heldout benchmark tests (8 tests) | PASS |
| Baseline benchmark (no diversified) | PASS — 100 solved, 0 exceptions, identical to prior |
| Diversified benchmark | PASS — 106 solved, 0 exceptions, all integrity checks |
| Analyzer on produced log | PASS — 936 events, all consistency checks clean |
| `git diff --check` | PASS — clean |
| `python weslr/tests/release_gate_v1.py` | PASS |
| `./scripts/weslr_release_check.sh` | PASS |
| `./scripts/chat_weslr_de_health_check.sh --mode source-repo` | PASS — 6 pass, 0 fail, 3 warn (optional network probes on non-runtime host), 0 skip |

## Limitations

1. **Synthetic benchmark only.** All families are WESLR-designed. Performance on public ARC-AGI-2 tasks is unknown.

2. **Single train pair.** Each diversified family has only 1 train pair. This is consistent with the original V1 families but may limit the solver's ability to infer the rule.

3. **Fixed grid sizes.** All families use 5×5 or 6×5 grids. The solver may not generalize to different grid sizes.

4. **No compositions.** The diversified families are single-step only. No multi-step compositions were added.

5. **No solver repair was performed.** The score drop is expected and healthy. The solver was not modified.

6. **`fill_enclosed_hole` is the hardest family.** It is the only family where the solver does not fall back to identity — it produces a wrong answer (ambiguous expected rejection) rather than falling back. This suggests the solver attempts a transformation but gets it wrong.

7. **No public ARC data was used.** The solver has not been evaluated on any public ARC-AGI-2 data.

## Next Recommended Lane

`synthetic_diversified_failure_audit_lane` — audit the 6 unsolved diversified families to classify failure modes (missing primitives vs. routing gaps vs. composition gaps) and determine which families are candidates for solver capability expansion.

## Readiness Verdict

`synthetic_family_diversification_v1_passed_ready_for_diversified_failure_audit_lane`

## Commit Status

Files to commit:
- `weslr/arc_synthetic_family_diversification_v1.py` (new)
- `weslr/tests/test_arc_synthetic_family_diversification_v1.py` (new)
- `weslr/arc_heldout_synthetic_discovery_benchmark_v1.py` (modified)
- `scripts/run_arc_heldout_synthetic_discovery_benchmark_v1.py` (modified)
- `docs/WESLR_ARC_AGI2_SYNTHETIC_FAMILY_DIVERSIFICATION_V1.md` (new)

Unrelated dirty file left untouched:
- `docs/WESLR_ARC_AGI2_TASK_FEATURE_SIGNATURE_EXTRACTOR_V1.md`