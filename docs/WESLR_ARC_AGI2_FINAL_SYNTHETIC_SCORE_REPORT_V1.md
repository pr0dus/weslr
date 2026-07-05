# WESLR ARC-AGI-2 Final Synthetic Score Report V1

## 1. Scope Statement

- **Synthetic-only:** This report covers the WESLR internal synthetic benchmark only.
- **No public ARC data:** No public ARC-AGI-2 data was read, scored, or used in any way.
- **No public ARC score:** This is not an official ARC-AGI-2 result. No public leaderboard score is reported.
- **No Kaggle submission:** No submission was made to Kaggle or any public competition.
- **Internal families:** All benchmark families are WESLR-designed synthetic families. They do not represent public ARC-AGI-2 task distribution.

## 2. Repo State

| Field | Value |
|-------|-------|
| Repo | `/data/data/com.termux/files/home/weslr-pr47-clean` |
| Branch | `main` |
| Start HEAD | `3d79e25564b42c8757d03660e782716193d8704b` |
| End HEAD | (recorded in chat after commit) |
| Actual preflight HEAD | `3d79e25564b42c8757d03660e782716193d8704b` |
| Commit status | Clean — all changes committed |
| Dirty file status | Untracked unrelated file `docs/WESLR_ARC_AGI2_TASK_FEATURE_SIGNATURE_EXTRACTOR_V1.md` remains untouched |
| Generated logs committed | No — all logs written to `/data/data/com.termux/files/home/weslr-arc-run-logs/` (outside repo) |

## 3. Final Benchmark Result

### Dev Split (seed=2435, 3 tasks per family)

| Metric | Value |
|--------|-------|
| Total tasks | 81 |
| Solved | 60 |
| Unsolved | 21 |
| Fallback-only | 18 |
| Exceptions | 0 |
| Solve percentage | 74.1% |

### Heldout Split (seed=82435, 5 tasks per family)

| Metric | Value |
|--------|-------|
| Total tasks | 135 |
| Solved | 100 |
| Unsolved | 35 |
| Fallback-only | 30 |
| Exceptions | 0 |
| Solve percentage | 74.1% |

### Combined

| Metric | Value |
|--------|-------|
| Total tasks | 216 |
| Solved | 160 |
| Unsolved | 56 |
| Fallback-only | 48 |
| Exceptions | 0 |
| Solve percentage | 74.1% |

## 4. Logged Run Evidence

### Run Metadata

| Field | Value |
|-------|-------|
| run_id | `arc-synth-20260705T193456` |
| Log directory | `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T193456/` |
| events.jsonl | `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T193456/events.jsonl` |
| run.log | `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T193456/run.log` |
| summary.json | `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T193456/summary.json` |

### Analyzer Command

```
python -c "
from weslr.arc_synthetic_run_log_analyzer_v1 import load_events, load_summary, analyze_events
events = load_events('<events.jsonl>')
summary = load_summary('<summary.json>')
analysis = analyze_events(events, summary)
print(json.dumps(analysis, indent=2, sort_keys=True))
"
```

### Analyzer Result

| Metric | Value |
|--------|-------|
| Total events | 762 |
| Event count by level | DEBUG=432, INFO=280, WARNING=48, SUMMARY=2 |
| Event count by phase | run_start=1, generation=218, solver_execution=216, evaluation=274, failure_classification=48, audit=3, run_summary=1, run_end=1 |
| Event count by type | run_started=1, split_started=2, task_generated=216, task_started=216, task_solved=160, task_unsolved=56, fallback_used=48, adversarial_rejection=56, split_summary=2, exact_two_output_check=1, deterministic_replay_check=1, expected_output_isolation_check=1, run_summary=1, run_finished=1 |
| Consistency checks | All clean — 0 missing events, 0 task count mismatches, 0 summary inconsistencies |

## 5. Integrity Checks

| Check | Status |
|-------|--------|
| Exact-two-output | PASS |
| Deterministic replay | PASS |
| Expected-output isolation | PASS |
| Split disjointness | PASS |
| Malformed outputs | 0 |
| Exceptions | 0 |
| Leakage audit | PASS |
| Unsafe metadata | 0 |
| Expected-output leakage | 0 |
| Raw-grid leakage | 0 |
| Public-data boundary | No public ARC data read or scored |

## 6. Adversarial Boundary Status

All 7 adversarial families are now correctly rejected:

| Family | Expected Behavior | Actual Behavior | Pass/Fail |
|--------|------------------|-----------------|-----------|
| inconsistent_train_examples | reject | rejected | PASS |
| ambiguous_multiple_rules | reject | rejected | PASS |
| unsupported_primitive_chain | reject | rejected | PASS |
| near_match_one_cell | reject | rejected | PASS |
| same_palette_wrong_geometry | reject | rejected | PASS |
| same_geometry_wrong_recolor | reject | rejected | PASS |
| count_tie_ambiguity | reject | rejected | PASS |

**Note:** The benchmark-definition repair (lane `WESLR_ARC_AGI2_BENCHMARK_DEFINITION_REPAIR_V1`) removed false-positive identity adversarial solves. Adversarial rejection failures are now **zero** across both splits.

## 7. Capability Coverage Summary

### Single-Step Primitive Families (20 families, all solved)

| Family | Dev (3/3) | Heldout (5/5) |
|--------|-----------|---------------|
| add_uniform_border | 3/3 | 5/5 |
| count_objects_to_line | 3/3 | 5/5 |
| crop_foreground_bbox | 3/3 | 5/5 |
| crop_largest_object | 3/3 | 5/5 |
| object_count_to_square | 3/3 | 5/5 |
| recolor_foreground | 3/3 | 5/5 |
| reflect_object_horizontal | 3/3 | 5/5 |
| reflect_object_vertical | 3/3 | 5/5 |
| rotate_object_180 | 3/3 | 5/5 |
| rotate_object_90 | 3/3 | 5/5 |
| scale_cells_integer | 3/3 | 5/5 |
| select_largest_object | 3/3 | 5/5 |
| swap_two_colors | 3/3 | 5/5 |
| tile_grid | 3/3 | 5/5 |
| translate_single_object | 3/3 | 5/5 |

**Single-step total:** 15 families × 3 dev + 15 families × 5 heldout = 45 dev + 75 heldout = **120 solved**

### Two-Step Composition Families (5 families, all solved)

| Family | Dev (3/3) | Heldout (5/5) |
|--------|-----------|---------------|
| crop_then_recolor | 3/3 | 5/5 |
| crop_then_rotate_or_reflect | 3/3 | 5/5 |
| crop_then_tile | 3/3 | 5/5 |
| recolor_then_border | 3/3 | 5/5 |
| select_then_recolor | 3/3 | 5/5 |

**Composition total:** 5 families × 3 dev + 5 families × 5 heldout = 15 dev + 25 heldout = **40 solved**

### Adversarial/Rejection Families (7 families, all correctly rejected)

| Family | Dev (3/3) | Heldout (5/5) |
|--------|-----------|---------------|
| inconsistent_train_examples | 0/3 solved, 3 rejected | 0/5 solved, 5 rejected |
| ambiguous_multiple_rules | 0/3 solved, 3 rejected | 0/5 solved, 5 rejected |
| unsupported_primitive_chain | 0/3 solved, 3 rejected | 0/5 solved, 5 rejected |
| near_match_one_cell | 0/3 solved, 3 rejected | 0/5 solved, 5 rejected |
| same_palette_wrong_geometry | 0/3 solved, 3 rejected | 0/5 solved, 5 rejected |
| same_geometry_wrong_recolor | 0/3 solved, 3 rejected | 0/5 solved, 5 rejected |
| count_tie_ambiguity | 0/3 solved, 3 rejected | 0/5 solved, 5 rejected |

**Adversarial total:** 7 families × 3 dev + 7 families × 5 heldout = 21 dev + 35 heldout = **56 correctly rejected**

### Remaining Fallback-Only Families

All 56 unsolved tasks are adversarial/rejection families that are correctly rejected. There are **no remaining fallback-only families** among the non-adversarial families. The 48 fallback events in the log correspond to adversarial tasks where the solver fell back to identity (which is the expected behavior for rejection-expected tasks).

## 8. Progress Timeline

| Lane | Result |
|------|--------|
| Initial synthetic generator | 36 solved, 39 fallback, 6 composition |
| Heldout baseline | 110 solved, 25 fallback, 0 exceptions |
| Exception cluster repair | Exceptions eliminated |
| Fallback cluster repair | Fallback reduced |
| Composition fallback repair | Composition families solved cleanly |
| Adversarial boundary audit | 2/7 families had identity-expected generator issues |
| Benchmark definition repair | 10 false adversarial solves eliminated |
| Event log/analyzer implementation | 762-event logged run, leakage audit PASS |
| **Final synthetic benchmark** | **160 solved, 56 rejected, 0 exceptions, 0 leakage** |

## 9. Honest Limitations

1. **Synthetic benchmark only.** This benchmark uses WESLR-designed synthetic families. It does not measure performance on public ARC-AGI-2 tasks.

2. **Not official ARC.** This is not an official ARC-AGI-2 result. No public leaderboard score exists. No Kaggle submission has been made.

3. **Public ARC result remains none/0.** The solver has not been evaluated on any public ARC-AGI-2 data. Its performance on public tasks is unknown.

4. **Solver may not generalize.** The solver was designed for and tested against these specific synthetic families. It may not generalize to unseen public ARC tasks.

5. **Remaining fallback-only families.** All 56 unsolved tasks are adversarial/rejection families that are correctly rejected. However, the solver's fallback behavior on these tasks (returning identity) is not a meaningful solution — it is the expected rejection behavior.

6. **Benchmark families are designed by us.** The family distribution, difficulty, and composition structure are our own design. They do not represent the distribution of public ARC-AGI-2 tasks.

7. **No learned model.** The solver uses deterministic rule-based family discovery and execution. There is no learned model, no LLM, and no neural network component.

8. **No public-data tuning.** No public ARC-AGI-2 data was used for tuning, validation, or any other purpose.

## 10. Next Recommended Lane

`remaining_fallback_family_audit_lane` — audit the remaining fallback-only families (adversarial/rejection families) to verify that their rejection behavior is correct and that no solver capability gap is being masked by fallback.

Do not recommend public scoring yet. The solver should first be evaluated against a broader set of synthetic families and ideally against public ARC-AGI-2 data in a controlled, governed manner.

## Readiness Verdict

`final_synthetic_score_report_v1_passed_ready_for_remaining_fallback_family_audit_lane`

## Validation Summary

- Final logged benchmark run: PASS (solved=100 heldout, 0 exceptions, 0 leakage)
- Analyzer on produced log: PASS (762 events, all consistency checks clean)
- `git diff --check`: clean
- `python weslr/tests/release_gate_v1.py`: PASS
- `./scripts/weslr_release_check.sh`: PASS
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`: PASS (6 pass, 0 fail, 3 warn, 0 skip)