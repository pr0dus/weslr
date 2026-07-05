# WESLR ARC-AGI2 Diversified Symmetry + Line Repair V1

## Metadata

| Field | Value |
|-------|-------|
| Repository | `/data/data/com.termux/files/home/weslr-pr47-clean` |
| Branch | `main` |
| Start HEAD | `6b9b28e431d51f658f62a1332109351a3d2fb709` |
| End HEAD | (committed after validation) |
| Previous lane | `WESLR_ARC_AGI2_DIVERSIFIED_FAILURE_AUDIT_V1` |
| Previous verdict | `diversified_failure_audit_v1_passed_ready_for_symmetry_or_line_repair_lane` |

## Preflight

Actual preflight HEAD: `6b9b28e431d51f658f62a1332109351a3d2fb709`
Expected HEAD: `6b9b28e431d51f658f62a1332109351a3d2fb709`
Match: YES

## Previous Diversified Benchmark Baseline

| Metric | Value |
|--------|-------|
| Combined solve rate | 65.2% (172/264) |
| Exceptions | 0 |
| Adversarial boundary | PASS |
| Exact-two-output | PASS |
| Deterministic replay | PASS |
| Expected-output isolation | PASS |

## Diagnosis for Each Primary Target Family

### `complete_horizontal_symmetry`

| Aspect | Finding |
|--------|---------|
| Primitive discovery | 0 accepted, 19 rejected, 6 uncertain |
| Family discovery | `symmetry_line` accepted (confidence 0.9) |
| Selected by runner | YES — `symmetry_line` in single-step hypotheses |
| Failure cause | **Adapter gap** — aggregator had no symmetry_line adapter registered |
| Expected transform | Mirror left half to right half (or vice versa) |
| Why solver fell back | Aggregator received `symmetry_line` in enabled_families but had no adapter to produce candidates, so only fallback candidates were generated |

### `complete_vertical_symmetry`

| Aspect | Finding |
|--------|---------|
| Primitive discovery | 0 accepted, 19 rejected, 6 uncertain |
| Family discovery | `symmetry_line` accepted (confidence 0.9) |
| Selected by runner | YES — `symmetry_line` in single-step hypotheses |
| Failure cause | **Adapter gap** — same as horizontal symmetry |
| Expected transform | Mirror top half to bottom half (or vice versa) |
| Why solver fell back | Same aggregator gap |

### `extend_line_to_boundary`

| Aspect | Finding |
|--------|---------|
| Primitive discovery | 0 accepted, 19 rejected, 6 uncertain |
| Family discovery | `symmetry_line` accepted (confidence 0.9) |
| Selected by runner | YES — `symmetry_line` in single-step hypotheses |
| Failure cause | **Adapter gap** — same as symmetry families |
| Expected transform | Extend horizontal/vertical line segment to full grid dimension |
| Why solver fell back | Same aggregator gap |

## Files Changed

### New files
- `weslr/arc_agi2_symmetry_line_candidate_adapter_v1.py` — symmetry/line completion adapter
- `weslr/tests/test_arc_symmetry_line_completion_v1.py` — 12 focused tests

### Modified files
- `weslr/arc_agi2_capability_candidate_aggregator_v1.py` — added `symmetry_line_solver` to `SOURCE_KIND_TO_FAMILY_V1`, added `symmetry_line` case in `_family_for_attempt`, added import of symmetry line adapter
- `weslr/arc_family_discovery_engine_v1.py` — added `symmetry_line` to `FAMILY_PRIORITY_V1` (priority 5), added import of `solve_symmetry_line_task`
- `weslr/arc_universal_family_runner_v1.py` — added `symmetry_line` to `EXECUTABLE_FAMILY_ORDER_V1`

## Capability Implementation Summary

The `arc_agi2_symmetry_line_candidate_adapter_v1.py` module implements:

1. **Horizontal symmetry completion** (`_complete_horizontal_symmetry`):
   - Infers direction (left-to-right or right-to-left) from train pairs
   - Mirrors non-background cells across the vertical midline
   - Preserves existing non-background cells (only fills empty cells)
   - Returns `None` if grid width < 2

2. **Vertical symmetry completion** (`_complete_vertical_symmetry`):
   - Infers direction (top-to-bottom or bottom-to-top) from train pairs
   - Mirrors non-background cells across the horizontal midline
   - Preserves existing non-background cells
   - Returns `None` if grid height < 2

3. **Line extension** (`_extend_horizontal_line`, `_extend_vertical_line`):
   - Detects single horizontal or vertical line segments
   - Extends to full grid dimension
   - Preserves original line color
   - Returns `None` if multiple rows/columns or non-contiguous

4. **Inference from train pairs**:
   - `_infer_horizontal_symmetry`: compares input/output pairs to determine mirror direction
   - `_infer_vertical_symmetry`: same for vertical
   - `_infer_line_extension`: checks if train input is a line and output is full-width/height

5. **Adapter integration**:
   - `_candidate_packets_for_top2`: formats candidates for the top-2 attempt contract
   - `build_arc_agi2_symmetry_line_top2_attempt_packet_v1`: builds a valid top-2 attempt packet
   - `build_arc_agi2_symmetry_line_submission_v1`: builds a submission packet

## Tests Added/Updated

`weslr/tests/test_arc_symmetry_line_completion_v1.py` — 12 tests:

- `TestInference`: 3 tests — horizontal symmetry inference, vertical symmetry inference, line extension inference
- `TestExecution`: 4 tests — each family solves, all variants (v0-v2) solve
- `TestFullPipeline`: 2 tests — universal runner solves all three, evaluation passes
- `TestNoLeakage`: 1 test — expected_output not in solver packet
- `TestDeterminism`: 1 test — same seed produces same result
- `TestAdapterPacket`: 1 test — adapter produces valid top-2 packet

## Baseline Old Benchmark Result

```
run_id: arc-synth-20260705T200523
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
| Combined solved | 172 | 190 | **+18** |
| Combined unsolved | 92 | 74 | -18 |
| Fallback-only | 78 | 52 | -26 |
| Exceptions | 0 | 0 | 0 |
| Solve rate | 65.2% | **72.0%** | **+6.8pp** |
| Adversarial pass | 56 | 56 | 0 |
| Adversarial fail | 0 | 0 | 0 |

## Per-Target-Family Before/After Table

| Family | Before (dev) | Before (heldout) | After (dev) | After (heldout) |
|--------|-------------|------------------|-------------|-----------------|
| `complete_horizontal_symmetry` | 0/3 | 0/3 | **3/3** | **3/3** |
| `complete_vertical_symmetry` | 0/3 | 0/3 | **3/3** | **3/3** |
| `extend_line_to_boundary` | 0/3 | 0/3 | **3/3** | **3/3** |

All three primary target families now solve 3/3 in both splits.

## Event Log Paths

- Baseline: `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T200523/`
- Diversified: `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T200531/`

## Analyzer Result

Combined stats from `build_heldout_synthetic_discovery_benchmark_v1`:

- Combined solved: 190/264 (72.0%)
- Combined unsolved: 74
- Fallback-only: 52
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
| Diversified benchmark | PASS (190/264, 0 exceptions) |
| `git diff --check` | PASS (clean) |
| Release gate | PASS |
| Release check | PASS |
| Health check (source-repo) | PASS (6/6 mandatory) |
| Protected files unchanged | PASS |
| No public ARC data | PASS |
| No Kaggle submission | PASS |

## Limitations

1. **Symmetry inference is strict**: requires exact match between input half and output half in train pairs. May fail on tasks with partial symmetry or noise.
2. **Line extension is simple**: extends to full grid dimension unconditionally. Does not handle partial extension or blocking objects.
3. **No primitive-level reasoning**: the symmetry_line family bypasses primitive discovery entirely. This is acceptable for synthetic-only capability but means the solver cannot explain its reasoning in primitive terms.
4. **Single family for three transforms**: all three transforms share the `symmetry_line` family. The adapter distinguishes them via `source_family` metadata.
5. **No composition support**: symmetry/line completion is not composable with other families in this lane.

## Next Recommended Lane

`WESLR_ARC_AGI2_DIVERSIFIED_HOLE_ROW_COLUMN_REPAIR_V1`

Target families (from audit `repair_after_next` priority):
- `fill_enclosed_hole`
- `extract_row_or_column_by_marker`

## Readiness Verdict

```
diversified_symmetry_line_repair_v1_passed_ready_for_hole_or_row_column_repair_lane
```

**Reasoning:**
- All three primary target families improved from 0/3 to 3/3 in both splits
- Combined solve rate improved from 65.2% to 72.0% (+6.8pp)
- No new exceptions introduced
- Baseline benchmark remains clean
- All validation checks pass
- No public ARC data read
- No Kaggle submission
