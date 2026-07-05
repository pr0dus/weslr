# WESLR ARC-AGI-2 Diversified Failure Audit V1

## Repo / Branch

- **Repo:** `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Branch:** `main`
- **Start HEAD (expected):** `9b0fdd719d4ff824f887fd46f6f6963a53b3dd60`
- **Actual preflight HEAD:** `9b0fdd719d4ff824f887fd46f6f6963a53b3dd60`
- **End HEAD:** (recorded in chat after commit)

## Previous Lane

- **Lane:** `WESLR_ARC_AGI2_SYNTHETIC_FAMILY_DIVERSIFICATION_V1`
- **Verdict:** `synthetic_family_diversification_v1_passed_ready_for_diversified_failure_audit_lane`
- **Result:** Baseline 74.1% → Diversified 65.2%. 8 new families, 0 exceptions, all integrity checks pass.

## Logged Run Paths

- **run_id:** `arc-synth-20260705T195125`
- **Log dir:** `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T195125/`
- **events.jsonl:** `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T195125/events.jsonl`
- **run.log:** `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T195125/run.log`
- **summary.json:** `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T195125/summary.json`

## Analyzer Result

- Total events: 936
- By level: INFO=328, DEBUG=528, WARNING=78, SUMMARY=2
- By phase: generation=266, solver_execution=264, evaluation=322, failure_classification=78, audit=3
- Leakage audit: PASS (0 unsafe metadata, 0 expected-output leakage, 0 raw-grid leakage)
- Consistency checks: All clean

## Count Reconciliation

### Expected vs Actual

| Metric | Expected | Actual | Match |
|--------|----------|--------|-------|
| Diversified families | 8 | 8 | ✓ |
| Dev diversified tasks | 24 (8 × 3) | 24 | ✓ |
| Heldout diversified tasks | 24 (8 × 3) | 24 | ✓ |
| Total added tasks | 48 | 48 | ✓ |
| Missing dev families | 0 | 0 | ✓ |
| Missing heldout families | 0 | 0 | ✓ |

### Explanation of Count

The owner's expectation of 64 added tasks (8 × 8) assumed heldout=5 for diversified families. However, the `--diversified-tasks-per-family` parameter defaults to **3 for both splits**, not 5. This is by design — the diversified families use a separate parameter from the original corpus. The actual count of 48 (24 dev + 24 heldout) is correct and consistent.

**No count mismatch.** The benchmark configuration is correct. All 8 families are present in both splits with 3 tasks each.

### Generated Diversified Family List

All 8 families are present in both dev and heldout:

| Family | Dev Count | Heldout Count |
|--------|-----------|---------------|
| complete_horizontal_symmetry | 3 | 3 |
| complete_vertical_symmetry | 3 | 3 |
| fill_enclosed_hole | 3 | 3 |
| remove_distractor_object | 3 | 3 |
| copy_object_to_marker | 3 | 3 |
| extend_line_to_boundary | 3 | 3 |
| extract_row_or_column_by_marker | 3 | 3 |
| recolor_by_object_size | 3 | 3 |

## Per-Family Result Table

### Dev Split

| Family | Gen | Solved | Unsolved | Fallback | Exceptions |
|--------|-----|--------|----------|----------|------------|
| complete_horizontal_symmetry | 3 | 0 | 3 | 3 | 0 |
| complete_vertical_symmetry | 3 | 0 | 3 | 3 | 0 |
| fill_enclosed_hole | 3 | 0 | 3 | 0 | 0 |
| remove_distractor_object | 3 | 3 | 0 | 0 | 0 |
| copy_object_to_marker | 3 | 0 | 3 | 3 | 0 |
| extend_line_to_boundary | 3 | 0 | 3 | 3 | 0 |
| extract_row_or_column_by_marker | 3 | 0 | 3 | 3 | 0 |
| recolor_by_object_size | 3 | 3 | 0 | 0 | 0 |

### Heldout Split

| Family | Gen | Solved | Unsolved | Fallback | Exceptions |
|--------|-----|--------|----------|----------|------------|
| complete_horizontal_symmetry | 3 | 0 | 3 | 3 | 0 |
| complete_vertical_symmetry | 3 | 0 | 3 | 3 | 0 |
| fill_enclosed_hole | 3 | 0 | 3 | 0 | 0 |
| remove_distractor_object | 3 | 3 | 0 | 0 | 0 |
| copy_object_to_marker | 3 | 0 | 3 | 3 | 0 |
| extend_line_to_boundary | 3 | 0 | 3 | 3 | 0 |
| extract_row_or_column_by_marker | 3 | 0 | 3 | 3 | 0 |
| recolor_by_object_size | 3 | 3 | 0 | 0 | 0 |

## Solved Diversified Families — Analysis

### `remove_distractor_object` (6/6 solved)

**Why solved:** The solver has object selection primitives (`select_largest_object`) and can remove non-selected objects. The distractor is a single cell while the target is a 2×2 block — the solver correctly identifies the larger object as the target and removes the smaller one.

**Existing capability:** `select_largest_object` + implicit removal of non-selected objects.

**Verdict:** Legitimate solve, not accidental. The solver's existing object selection capability generalizes to this family.

### `recolor_by_object_size` (6/6 solved)

**Why solved:** The solver has recolor primitives (`recolor_foreground`) and object size comparison (from `object_count_to_square`). The smallest object is a single cell, which the solver can identify and recolor.

**Existing capability:** `recolor_foreground` + object size comparison.

**Verdict:** Legitimate solve, not accidental. The solver's existing recolor and size-comparison capabilities generalize to this family.

## Unsolved Diversified Families — Analysis

### `complete_horizontal_symmetry` (0/6 solved, 6 fallback)

**Classification:** `missing_capability`
**Capability layer:** `symmetry_completion`
**Failure mode:** The solver falls back to identity (returns test input unchanged). It has no symmetry detection or completion primitive.
**Priority:** `repair_next`

### `complete_vertical_symmetry` (0/6 solved, 6 fallback)

**Classification:** `missing_capability`
**Capability layer:** `symmetry_completion`
**Failure mode:** Same as horizontal symmetry — the solver has no vertical symmetry primitive.
**Priority:** `repair_next`

### `fill_enclosed_hole` (0/6 solved, 0 fallback)

**Classification:** `missing_capability`
**Capability layer:** `hole_detection`
**Failure mode:** This is the most interesting failure. The solver does NOT fall back to identity — it produces a wrong answer (classified as `ambiguous_expected_rejection`). This means the solver attempts a transformation but gets it wrong. The solver likely tries to apply an existing primitive (e.g., border, recolor) that partially matches but produces incorrect output.
**Priority:** `repair_after_next`

### `copy_object_to_marker` (0/6 solved, 6 fallback)

**Classification:** `missing_capability`
**Capability layer:** `marker_interpretation`
**Failure mode:** The solver falls back to identity. It has no primitive for detecting a marker cell and copying an object to its location.
**Priority:** `repair_later`

### `extend_line_to_boundary` (0/6 solved, 6 fallback)

**Classification:** `missing_capability`
**Capability layer:** `line_extension`
**Failure mode:** The solver falls back to identity. It has no primitive for detecting partial lines and extending them to grid boundaries.
**Priority:** `repair_next`

### `extract_row_or_column_by_marker` (0/6 solved, 6 fallback)

**Classification:** `missing_capability`
**Capability layer:** `row_column_extraction`
**Failure mode:** The solver falls back to identity. It has no primitive for detecting a marker and extracting the marked row.
**Priority:** `repair_after_next`

## Accidental Solve / Over-Acceptance Check

| Family | Status | Accidental? | Reason |
|--------|--------|-------------|--------|
| complete_horizontal_symmetry | unsolved | No | — |
| complete_vertical_symmetry | unsolved | No | — |
| fill_enclosed_hole | unsolved | No | — |
| remove_distractor_object | **solved** | **No** | Solver has object selection + removal |
| copy_object_to_marker | unsolved | No | — |
| extend_line_to_boundary | unsolved | No | — |
| extract_row_or_column_by_marker | unsolved | No | — |
| recolor_by_object_size | **solved** | **No** | Solver has recolor + size comparison |

**No accidental solves detected.** Both solved families are legitimate generalizations of existing solver capabilities.

## Repair Priority Ranking

### `repair_next` — Symmetry Completion + Line Extension

| Family | Capability | Value | Complexity |
|--------|------------|-------|------------|
| complete_horizontal_symmetry | symmetry_completion | High | Medium |
| complete_vertical_symmetry | symmetry_completion | High | Medium |
| extend_line_to_boundary | line_extension | High | Low/Medium |

**Rationale:** Symmetry is a foundational ARC concept. Line extension is a simple geometric primitive. Both are high-value, medium-complexity capabilities that would significantly expand the solver's coverage.

### `repair_after_next` — Hole Detection + Row/Column Extraction

| Family | Capability | Value | Complexity |
|--------|------------|-------|------------|
| fill_enclosed_hole | hole_detection | High | Medium |
| extract_row_or_column_by_marker | row_column_extraction | Medium/High | Medium |

**Rationale:** Hole filling is a common ARC pattern. Row extraction by marker is useful but requires marker interpretation as a prerequisite.

### `repair_later` — Marker-Based Copy

| Family | Capability | Value | Complexity |
|--------|------------|-------|------------|
| copy_object_to_marker | marker_interpretation | High | Higher |

**Rationale:** Marker-based copy requires both marker detection and object copy — a multi-step capability that depends on more fundamental primitives.

### `do_not_repair_currently` — Already Solved

| Family | Reason |
|--------|--------|
| remove_distractor_object | Already solved by existing object selection |
| recolor_by_object_size | Already solved by existing recolor + size comparison |

## Integrity Checks

| Check | Status |
|-------|--------|
| Exact-two-output | PASS |
| Deterministic replay | PASS |
| Expected-output isolation | PASS |
| Leakage audit | PASS |
| Malformed count | 0 |
| Exception count | 0 |
| Adversarial boundary | PASS (35 pass, 0 fail) |
| Public-data boundary | No public ARC data read or scored |
| Generated logs outside repo | Yes — `/data/data/com.termux/files/home/weslr-arc-run-logs/` |
| Generated logs not committed | Confirmed |

## Files Added

| File | Status |
|------|--------|
| `weslr/arc_diversified_failure_audit_v1.py` | **Added** — audit helper module |
| `weslr/tests/test_arc_diversified_failure_audit_v1.py` | **Added** — 13 tests |
| `docs/WESLR_ARC_AGI2_DIVERSIFIED_FAILURE_AUDIT_V1.md` | **Added** — this report |

## Validation Summary

| Check | Status |
|-------|--------|
| `python -m py_compile` on changed files | PASS |
| Focused audit tests (13 tests) | PASS |
| Diversified benchmark run | PASS — 106 solved, 0 exceptions, all integrity checks |
| Analyzer on produced log | PASS — 936 events, all consistency checks clean |
| `git diff --check` | PASS — clean |
| `python weslr/tests/release_gate_v1.py` | PASS |
| `./scripts/weslr_release_check.sh` | PASS |
| `./scripts/chat_weslr_de_health_check.sh --mode source-repo` | PASS — 6 pass, 0 fail, 3 warn (optional network probes on non-runtime host), 0 skip |

## Limitations

1. **Synthetic benchmark only.** All families are WESLR-designed. Performance on public ARC-AGI-2 tasks is unknown.

2. **Single train pair.** Each diversified family has only 1 train pair. The solver may perform differently with more examples.

3. **Fixed grid sizes.** All families use 5×5 or 6×5 grids. Generalization to different grid sizes is untested.

4. **No compositions.** The diversified families are single-step only. Multi-step compositions may reveal different failure modes.

5. **`fill_enclosed_hole` is the hardest family.** It is the only family where the solver does not fall back to identity — it produces a wrong answer. This suggests the solver attempts a transformation but gets it wrong, which is a different failure mode from the other unsolved families.

6. **No public ARC data was used.** The solver has not been evaluated on any public ARC-AGI-2 data.

## Next Recommended Lane

`symmetry_and_line_extension_repair_lane` — add symmetry completion and line extension primitives to the solver. These are the highest-value, lowest-complexity missing capabilities identified by the audit.

## Readiness Verdict

`diversified_failure_audit_v1_passed_ready_for_symmetry_or_line_repair_lane`