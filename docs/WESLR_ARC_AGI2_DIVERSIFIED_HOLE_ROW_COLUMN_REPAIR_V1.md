# WESLR ARC-AGI2 Diversified Hole + Row/Column Repair V1

## Metadata

| Field | Value |
|-------|-------|
| Repository | `/data/data/com.termux/files/home/weslr-pr47-clean` |
| Branch | `main` |
| Start HEAD | `2eda0c33efd3de3052cdd42b36fbf3f06d5e6f78` |
| End HEAD | (committed after validation) |
| Previous lane | `WESLR_ARC_AGI2_DIVERSIFIED_SYMMETRY_LINE_REPAIR_V1` |
| Previous verdict | `diversified_symmetry_line_repair_v1_passed_ready_for_hole_or_row_column_repair_lane` |

## Preflight

Actual preflight HEAD: `2eda0c33efd3de3052cdd42b36fbf3f06d5e6f78`
Expected HEAD: `2eda0c33efd3de3052cdd42b36fbf3f06d5e6f78`
Match: YES

## Previous Diversified Benchmark Baseline

| Metric | Value |
|--------|-------|
| Combined solve rate | 72.0% (190/264) |
| Exceptions | 0 |
| Adversarial boundary | PASS |
| Exact-two-output | PASS |
| Deterministic replay | PASS |
| Expected-output isolation | PASS |

## Diagnosis for Each Primary Target Family

### `fill_enclosed_hole`

| Aspect | Finding |
|--------|---------|
| Primitive discovery | 4 accepted, 14 rejected, 7 uncertain |
| Family discovery | `color_role` accepted (0.99 confidence) — **wrong family** |
| Selected by runner | YES — `color_role` selected as single-step |
| Failure cause | **Wrong family selected** — `color_role` has higher priority than any hole-specific family. The color_role adapter replaces 0s with the train's fill color (1) instead of the test's border color (3), producing wrong output. |
| Expected transform | Fill enclosed background holes with the surrounding border color |
| Why solver fell back | Solver didn't fall back — it produced wrong output via `color_role` |

### `extract_row_or_column_by_marker`

| Aspect | Finding |
|--------|---------|
| Primitive discovery | 1 accepted, 14 rejected, 10 uncertain |
| Family discovery | `color_role` accepted (0.95 confidence) — **wrong family** |
| Selected by runner | YES — `color_role` selected as single-step |
| Failure cause | **Wrong family selected** — `color_role` has higher priority. The color_role adapter produces a color-replacement output that doesn't match the expected row extraction. |
| Expected transform | Extract the row (or column) between two marker cells, replacing the right/bottom marker with 0 |
| Why solver fell back | `color_role` produced wrong output, and no hole/row-column adapter existed |

## Implementation

### New files
- `weslr/arc_hole_row_column_v1.py` — hole filling and row/column extraction capability module
- `weslr/arc_agi2_hole_row_column_candidate_adapter_v1.py` — adapter for aggregator integration
- `weslr/tests/test_arc_hole_row_column_v1.py` — 11 focused tests

### Modified files
- `weslr/arc_agi2_capability_candidate_aggregator_v1.py` — added `hole_row_column_solver` to `SOURCE_KIND_TO_FAMILY_V1`, added `hole_row_column` case in `_family_for_attempt`, added adapter import and call in `_build_source_packets`, updated `FAMILY_PRIORITY_V1` and `SOURCE_ADAPTER_PRIORITY_V1`
- `weslr/arc_family_discovery_engine_v1.py` — added `hole_row_column` to `FAMILY_PRIORITY_V1` (priority 2, above `color_role`), added solver candidates and family hypothesis for `hole_row_column`, fixed duplicate priority values for composition families
- `weslr/arc_universal_family_runner_v1.py` — added `hole_row_column` to `EXECUTABLE_FAMILY_ORDER_V1`

### Priority change
`hole_row_column` was given priority 2 (above `color_role` at 3) because:
- The hole/row-column capability is more specific and produces correct output for these tasks
- `color_role` was incorrectly selected and produced wrong output
- This is a targeted priority adjustment for synthetic-only capability

## Capability Implementation Summary

The `arc_hole_row_column_v1.py` module implements:

1. **Hole filling** (`_fill_enclosed_holes`):
   - Detects enclosed background holes via flood-fill (holes that don't reach grid boundary)
   - Infers fill color from test input's border color (non-zero cell adjacent to a hole)
   - Fills all enclosed holes with the inferred color
   - Returns `None` if no holes found

2. **Row extraction by marker** (`_extract_row_by_marker`):
   - Detects two marker cells in the same row
   - Infers marker pattern (mode, colors) from train pairs
   - Extracts the row, replacing the rightmost marker with 0
   - Verifies marker colors match the inferred pattern

3. **Column extraction by marker** (`_extract_column_by_marker`):
   - Detects two marker cells in the same column
   - Infers marker pattern from train pairs
   - Extracts the column, replacing the bottommost marker with 0
   - Verifies marker colors match the inferred pattern

## Tests Added

`weslr/tests/test_arc_hole_row_column_v1.py` — 11 tests:

- `TestInference`: 3 tests — fill color inference, marker pattern inference, enclosed hole detection
- `TestExecution`: 3 tests — hole filling solves, row extraction solves, all variants solve
- `TestFullPipeline`: 2 tests — universal runner solves both, evaluation passes
- `TestNoLeakage`: 1 test — expected_output not in solver packet
- `TestDeterminism`: 1 test — same seed same result
- `TestAdapterPacket`: 1 test — adapter produces valid top-2 packet

## Baseline Old Benchmark Result

```
run_id: arc-synth-20260705T201352
total_tasks: 135
solved: 100
fallback_only: 25
exceptions: 0
adversarial_rejection_pass: 35
adversarial_rejection_fail: 0
exact_two_output_pass: True
deterministic_replay_pass: True
expected_output_isolation_pass: True
```

Baseline remains clean — no regression.

## Diversified Benchmark Before/After Comparison

| Metric | Before Repair | After Repair | Delta |
|--------|---------------|--------------|-------|
| Combined solved | 190 | **202** | **+12** |
| Combined unsolved | 74 | 62 | -12 |
| Fallback-only | 52 | 46 | -6 |
| Exceptions | 0 | 0 | 0 |
| Solve rate | 72.0% | **76.5%** | **+4.5pp** |
| Adversarial pass | 56 | 56 | 0 |
| Adversarial fail | 0 | 0 | 0 |

## Per-Target-Family Before/After Table

| Family | Before (dev) | Before (heldout) | After (dev) | After (heldout) |
|--------|-------------|------------------|-------------|-----------------|
| `fill_enclosed_hole` | 0/3 | 0/3 | **3/3** | **3/3** |
| `extract_row_or_column_by_marker` | 0/3 | 0/3 | **3/3** | **3/3** |
| `copy_object_to_marker` | 0/3 | 0/3 | 0/3 | 0/3 |

Both primary target families now solve 3/3 in both splits. `copy_object_to_marker` remains unsolved (as expected — out of scope).

## Event Log Paths

- Baseline: `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T201352/`
- Diversified: `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T201401/`

## Analyzer Result

Combined stats from `build_heldout_synthetic_discovery_benchmark_v1`:

- Combined solved: 202/264 (76.5%)
- Combined unsolved: 62
- Fallback-only: 46
- Exceptions: 0
- Exact-two-output: PASS (both splits)
- Adversarial pass: 56 (both splits)
- Adversarial fail: 0 (both splits)

## Validation Results

| Check | Status |
|-------|--------|
| `py_compile` on changed files | PASS |
| Focused tests (11 tests) | PASS |
| Baseline benchmark | PASS (100/135, 0 exceptions) |
| Diversified benchmark | PASS (202/264, 0 exceptions) |
| `git diff --check` | PASS (clean) |
| Release gate | PASS |
| Release check | PASS |
| Health check (source-repo) | PASS (6/6 mandatory) |
| Protected files unchanged | PASS |
| Unrelated dirty file untouched | PASS |
| No public ARC data | PASS |
| No Kaggle submission | PASS |

## Limitations

1. **Hole filling is simple**: assumes a single border color surrounds all holes. Does not handle multiple border colors or non-rectangular holes.
2. **Row/column extraction is strict**: requires exactly two marker cells with matching colors. Does not handle single-marker or multi-marker tasks.
3. **Priority adjustment**: `hole_row_column` was given priority 2 (above `color_role` at 3). This is correct for synthetic-only tasks but may need review if real ARC tasks have different characteristics.
4. **No composition support**: hole/row-column is not composable with other families.
5. **`copy_object_to_marker` remains unsolved**: this is expected and out of scope for this lane.

## Next Recommended Lane

`WESLR_ARC_AGI2_DIVERSIFIED_MARKER_COPY_REPAIR_V1`

Target family:
- `copy_object_to_marker`

## Readiness Verdict

```
diversified_hole_row_column_repair_v1_passed_ready_for_marker_copy_repair_or_final_diversified_score_lane
```

**Reasoning:**
- Both primary target families improved from 0/3 to 3/3 in both splits
- Combined solve rate improved from 72.0% to 76.5% (+4.5pp)
- `copy_object_to_marker` remains unsolved (correctly out of scope)
- No new exceptions introduced
- Baseline benchmark remains clean
- All validation checks pass
- No public ARC data read
- No Kaggle submission
