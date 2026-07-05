# WESLR ARC-AGI2 Diversified Marker Copy Repair V1

## Metadata

| Field | Value |
|-------|-------|
| Repository | `/data/data/com.termux/files/home/weslr-pr47-clean` |
| Branch | `main` |
| Start HEAD | `ff458e54c67a3d42bb508128e1dd0ae790834c6d` |
| End HEAD | (committed after validation) |
| Previous lane | `WESLR_ARC_AGI2_DIVERSIFIED_HOLE_ROW_COLUMN_REPAIR_V1` |
| Previous verdict | `diversified_hole_row_column_repair_v1_passed_ready_for_marker_copy_repair_or_final_diversified_score_lane` |

## Preflight

Actual preflight HEAD: `ff458e54c67a3d42bb508128e1dd0ae790834c6d`
Expected HEAD: `ff458e54c67a3d42bb508128e1dd0ae790834c6d`
Match: YES

## Previous Diversified Benchmark Baseline

| Metric | Value |
|--------|-------|
| Combined solve rate | 76.5% (202/264) |
| Exceptions | 0 |
| Adversarial boundary | PASS |
| Exact-two-output | PASS |
| Deterministic replay | PASS |
| Expected-output isolation | PASS |

## Diagnosis for `copy_object_to_marker`

| Aspect | Finding |
|--------|---------|
| Primitive discovery | 5 accepted, 14 rejected, 6 uncertain |
| Family discovery | `color_role` accepted (0.94 confidence) — **wrong family** |
| Selected by runner | YES — `color_role` selected as single-step |
| Failure cause | **Wrong family selected** — `color_role` has higher priority than any marker-copy family. The color_role adapter produces a color-replacement output that doesn't match the expected marker-copy transform. |
| Expected transform | Copy the source object (2×2 block) so its top-right corner aligns with the marker position. The copy extends downward and leftward from the marker. Source object is preserved. |
| Why solver fell back | `color_role` produced wrong output, and no marker-copy adapter existed |

## Implementation

### New files
- `weslr/arc_marker_copy_v1.py` — marker-copy capability module
- `weslr/arc_agi2_marker_copy_candidate_adapter_v1.py` — adapter for aggregator integration
- `weslr/tests/test_arc_marker_copy_v1.py` — 12 focused tests

### Modified files
- `weslr/arc_agi2_capability_candidate_aggregator_v1.py` — added `marker_copy_solver` to `SOURCE_KIND_TO_FAMILY_V1`, added `marker_copy` case in `_family_for_attempt`, added adapter import and call in `_build_source_packets`, updated `FAMILY_PRIORITY_V1` and `SOURCE_ADAPTER_PRIORITY_V1`
- `weslr/arc_family_discovery_engine_v1.py` — added `marker_copy` to `FAMILY_PRIORITY_V1` (priority 3, above `color_role` at 4), added solver candidates and family hypothesis for `marker_copy`
- `weslr/arc_universal_family_runner_v1.py` — added `marker_copy` to `EXECUTABLE_FAMILY_ORDER_V1`

### Priority change
`marker_copy` was given priority 3 (above `color_role` at 4) because:
- The marker-copy capability is more specific and produces correct output
- `color_role` was incorrectly selected and produced wrong output
- This is a targeted priority adjustment for synthetic-only capability

## Capability Implementation Summary

The `arc_marker_copy_v1.py` module implements:

1. **Connected component detection** (`_find_connected_objects`):
   - 4-directional flood-fill to find all non-background objects
   - Returns bounding box dimensions and cell list for each object

2. **Pattern inference** (`_infer_marker_copy_pattern`):
   - Identifies the marker (single-cell object) and source object (multi-cell object)
   - Verifies the copy placement: source object is copied so its top-right corner aligns with the marker
   - Returns source color, marker color, source dimensions, and placement direction

3. **Copy execution** (`_copy_object_to_marker`):
   - Places the copy so its top-right corner is at the marker position
   - Copy extends downward and leftward from the marker
   - Handles partial copies when the copy would extend out of bounds
   - Preserves the original source object
   - Only copies cells that were part of the source object shape

## Tests Added

`weslr/tests/test_arc_marker_copy_v1.py` — 12 tests:

- `TestInference`: 4 tests — pattern inference, connected objects, source finding, marker finding
- `TestExecution`: 3 tests — solves, all variants solve, different seeds solve
- `TestFullPipeline`: 2 tests — universal runner solves, evaluation passes
- `TestNoLeakage`: 1 test — expected_output not in solver packet
- `TestDeterminism`: 1 test — same seed same result
- `TestAdapterPacket`: 1 test — adapter produces valid top-2 packet

## Baseline Old Benchmark Result

```
run_id: arc-synth-20260705T202039
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
| Combined solved | 202 | **208** | **+6** |
| Combined unsolved | 62 | 56 | -6 |
| Fallback-only | 46 | 40 | -6 |
| Exceptions | 0 | 0 | 0 |
| Solve rate | 76.5% | **78.8%** | **+2.3pp** |
| Adversarial pass | 56 | 56 | 0 |
| Adversarial fail | 0 | 0 | 0 |

## `copy_object_to_marker` Before/After

| Split | Before | After |
|-------|--------|-------|
| Dev | 0/3 | **3/3** |
| Heldout | 0/3 | **3/3** |
| Total | 0/6 | **6/6** |

## Event Log Paths

- Baseline: `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T202039/`
- Diversified: `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T202048/`

## Analyzer Result

Combined stats from `build_heldout_synthetic_discovery_benchmark_v1`:

- Combined solved: 208/264 (78.8%)
- Combined unsolved: 56
- Fallback-only: 40
- Exceptions: 0
- Exact-two-output: PASS (both splits)
- Adversarial pass: 56 (both splits)
- Adversarial fail: 0 (both splits)

## Validation Results

| Check | Status |
|-------|--------|
| `py_compile` on changed files | PASS |
| Focused tests (12 tests) | PASS |
| Baseline benchmark | PASS (100/135, 0 exceptions) |
| Diversified benchmark | PASS (208/264, 0 exceptions) |
| `git diff --check` | PASS (clean) |
| Release gate | PASS |
| Release check | PASS |
| Health check (source-repo) | PASS (6/6 mandatory) |
| Protected files unchanged | PASS |
| Unrelated dirty file untouched | PASS |
| No public ARC data | PASS |
| No Kaggle submission | PASS |

## Limitations

1. **Fixed placement direction**: assumes top-right alignment (marker at top-right of copy, extending downward and leftward). Other placement directions are not supported.
2. **Single source, single marker**: requires exactly one multi-cell source object and one single-cell marker. Multiple sources or markers are rejected.
3. **Priority adjustment**: `marker_copy` was given priority 3 (above `color_role` at 4). This is correct for synthetic-only tasks but may need review for real ARC tasks.
4. **No composition support**: marker-copy is not composable with other families.
5. **All 8 diversified families now solved**: no remaining unsolved diversified families.

## Next Recommended Lane

`WESLR_ARC_AGI2_FINAL_DIVERSIFIED_SYNTHETIC_SCORE_REPORT_V1`

This lane should produce a final consolidated report of the diversified synthetic benchmark score after all three repair lanes.

## Readiness Verdict

```
diversified_marker_copy_repair_v1_passed_ready_for_final_diversified_synthetic_score_report_lane
```

**Reasoning:**
- `copy_object_to_marker` improved from 0/6 to 6/6
- Combined solve rate improved from 76.5% to 78.8% (+2.3pp)
- All 8 diversified families now solved
- No new exceptions introduced
- Baseline benchmark remains clean
- All validation checks pass
- No public ARC data read
- No Kaggle submission
