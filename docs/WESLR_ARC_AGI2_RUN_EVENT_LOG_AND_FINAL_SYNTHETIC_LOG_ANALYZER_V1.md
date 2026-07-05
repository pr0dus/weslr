# WESLR ARC-AGI-2 Run Event Log + Final Synthetic Log Analyzer V1

## Repo / Branch

- **Repo:** `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Branch:** `main`
- **Start HEAD (expected):** `6a14afdddf375ee61950ec7a83fb2b9045438c2c`
- **Actual preflight HEAD:** `6a14afdddf375ee61950ec7a83fb2b9045438c2c`
- **End HEAD:** (recorded in chat after commit)

## Files Added/Changed

| File | Action |
|------|--------|
| `weslr/arc_run_event_log_v1.py` | **Added** — structured JSONL event log |
| `weslr/arc_synthetic_run_log_analyzer_v1.py` | **Added** — log analyzer with leakage checks |
| `weslr/arc_heldout_synthetic_discovery_benchmark_v1.py` | **Updated** — event log integration |
| `scripts/run_arc_heldout_synthetic_discovery_benchmark_v1.py` | **Updated** — `--write-event-log` CLI flag |
| `weslr/tests/test_arc_run_event_log_v1.py` | **Added** — 14 event log tests |
| `weslr/tests/test_arc_synthetic_run_log_analyzer_v1.py` | **Added** — 32 analyzer tests |
| `docs/WESLR_ARC_AGI2_RUN_EVENT_LOG_AND_FINAL_SYNTHETIC_LOG_ANALYZER_V1.md` | **Added** — this report |

## Event Schema

Each JSONL line is one JSON object with:

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Unique run identifier |
| `timestamp_utc` | string | ISO-8601 UTC timestamp |
| `elapsed_sec` | float | Seconds since run start |
| `level` | string | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `SUMMARY` |
| `phase` | string | One of 8 required phases |
| `event_type` | string | One of 22 required event types |
| `message` | string | Human-readable message |
| `metadata` | dict | Safe metadata (no raw grids, no expected output) |

## Forbidden Metadata Keys

The following keys are rejected by the event log and detected by the analyzer:

- `raw_grid`, `raw_grids`, `train_grid`, `test_grid`
- `expected_output`, `expected_output_grid`, `expected_outputs`
- `solution_grid`, `answer_key`, `public_solution`

## Log Output Policy

Generated run logs are written to:

```
/data/data/com.termux/files/home/weslr-arc-run-logs/<run_id>/
```

Files per run:
- `events.jsonl` — structured event log
- `run.log` — compact text log
- `summary.json` — run summary

No generated logs are committed to the repo.

## Script Command

```
python scripts/run_arc_heldout_synthetic_discovery_benchmark_v1.py \
  --dev-seed 2435 --heldout-seed 82435 \
  --tasks-per-family-dev 3 --tasks-per-family-heldout 5 \
  --include-adversarial --include-compositions --write-event-log
```

## Generated Log Paths

- Log dir: `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T193141/`
- `events.jsonl`: `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T193141/events.jsonl`
- `run.log`: `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T193141/run.log`
- `summary.json`: `/data/data/com.termux/files/home/weslr-arc-run-logs/arc-synth-20260705T193141/summary.json`

## Analyzer Command

```
python -c "
from weslr.arc_synthetic_run_log_analyzer_v1 import load_events, load_summary, analyze_events
events = load_events('<events.jsonl>')
summary = load_summary('<summary.json>')
analysis = analyze_events(events, summary)
print(json.dumps(analysis, indent=2))
"
```

## Analyzer Result

### Event Counts

| Metric | Value |
|--------|-------|
| Total events | 762 |
| INFO | 280 |
| DEBUG | 432 |
| WARNING | 48 |
| SUMMARY | 2 |

### Event Counts by Phase

| Phase | Count |
|-------|-------|
| run_start | 1 |
| generation | 218 |
| solver_execution | 216 |
| evaluation | 274 |
| failure_classification | 48 |
| audit | 3 |
| run_summary | 1 |
| run_end | 1 |

### Event Counts by Type

| Type | Count |
|------|-------|
| run_started | 1 |
| split_started | 2 |
| task_generated | 216 |
| task_started | 216 |
| task_solved | 160 |
| task_unsolved | 56 |
| fallback_used | 48 |
| adversarial_rejection | 56 |
| split_summary | 2 |
| exact_two_output_check | 1 |
| deterministic_replay_check | 1 |
| expected_output_isolation_check | 1 |
| run_summary | 1 |
| run_finished | 1 |

### Split Summaries

| Split | Solved | Unsolved | Fallback | Adv Pass | Adv Fail |
|-------|--------|----------|----------|----------|----------|
| dev | 60 | 21 | 18 | 21 | 0 |
| heldout | 100 | 35 | 30 | 35 | 0 |

### Fallback Summary

- Total fallback events: 48
- Top fallback families: `inconsistent_train_examples` (8), `unsupported_primitive_chain` (8), `near_match_one_cell` (8), `same_palette_wrong_geometry` (8), `same_geometry_wrong_recolor` (8)

### Adversarial Summary

- Adversarial rejection pass: 56
- Adversarial rejection fail: 0

### Leakage Audit

- **Leakage audit pass:** True
- Unsafe metadata: 0 issues
- Expected output leakage: 0 issues
- Raw grid leakage: 0 issues

### Consistency

- Missing events: 0 issues
- Task count mismatch: 0 issues
- Summary consistency: 0 issues

### Top Failure Categories

- `ambiguous_expected_rejection`: 56

## Integrity Checks

- **Exact-two-output:** PASS
- **Deterministic replay:** PASS
- **Expected-output isolation:** PASS

## Health Check

- **Script:** `./scripts/chat_weslr_de_health_check.sh --mode source-repo`
- **Status:** PASS (6 pass, 0 fail, 3 warn, 0 skip)

## Validation Summary

- `python -m py_compile` on changed Python files: PASS
- Event log tests (14 tests): PASS
- Analyzer tests (32 tests): PASS
- Heldout benchmark tests (8 tests): PASS
- Logged heldout benchmark run: PASS (solved=100, fallback=30, exceptions=0)
- Analyzer on produced log: PASS (leakage audit pass, no issues)
- `git diff --check`: clean
- `python weslr/tests/release_gate_v1.py`: PASS
- `./scripts/weslr_release_check.sh`: PASS
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`: PASS

## Limitations

- Event log is written during benchmark execution; if the process crashes mid-run, the log may be incomplete
- The analyzer checks for forbidden metadata keys but does not inspect nested structures recursively beyond one level
- The text log format is compact but not machine-parseable (use JSONL for analysis)
- No public ARC data was read or scored

## Next Recommended Lane

`final_synthetic_score_report_lane` — produce a final synthetic score report backed by analyzable logs, documenting the clean adversarial boundary and honest heldout score.

## Readiness Verdict

`run_event_log_analyzer_v1_passed_ready_for_final_synthetic_score_report_lane`