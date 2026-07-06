# WESLR ARC-AGI-2 Public Input Shape Dry Run V1

## Metadata

| Field | Value |
|-------|-------|
| Repository | `/data/data/com.termux/files/home/weslr-pr47-clean` |
| Branch | `main` |
| Start HEAD | `3a6cea94437f85c5faf6e713431f93b556648acd` |
| End HEAD | (committed below) |
| Preflight match | YES |
| Lane type | Public input shape dry run of portable submission package |
| Previous lane | `WESLR_ARC_AGI2_KAGGLE_STYLE_SUBMISSION_PACKAGE_DRY_RUN_V1` |
| Previous verdict | `kaggle_style_submission_package_dry_run_v1_passed_ready_for_public_input_shape_dry_run_lane` |

## Preflight HEAD Verification

| Check | Result |
|-------|--------|
| Expected HEAD | `3a6cea94437f85c5faf6e713431f93b556648acd` |
| Actual HEAD | `3a6cea94437f85c5faf6e713431f93b556648acd` |
| Match | YES |

## Public Zip Quarantine Status

| Check | Result |
|-------|--------|
| Public zip exists outside repo | YES |
| Path | `/data/data/com.termux/files/home/arc-agi2-public-source/arc-prize-2026-arc-agi-2.zip` |
| Size | 498,708 bytes |
| SHA256 | `d00746ef4e06a515ad53bde4dff276dc8ef5a26829a0ebeafc8cf8ba6371abaa` |
| SHA256 match | YES |
| Mtime | 2026-07-04 16:34:01 |
| Public data inside repo | NO |
| Generated logs/artifacts inside repo | NO |

## Zip Manifest Summary

| File | Size | Status |
|------|------|--------|
| `arc-agi_evaluation_challenges.json` | 984,679 bytes | Challenge file |
| `arc-agi_evaluation_solutions.json` | 223,838 bytes | **NOT OPENED** |
| `arc-agi_test_challenges.json` | 1,015,295 bytes | **OPENED** (shape dry run) |
| `arc-agi_training_challenges.json` | 4,010,050 bytes | Challenge file (not used) |
| `arc-agi_training_solutions.json` | 658,743 bytes | **NOT OPENED** |
| `sample_submission.json` | 19,936 bytes | Sample submission (not used) |

## Files Opened vs Not Opened

| File | Opened? | Purpose |
|------|---------|---------|
| `arc-agi_test_challenges.json` | YES | Challenge JSON parsed for shape validation and solver input |
| `arc-agi_evaluation_solutions.json` | **NO** | Solution file — never opened |
| `arc-agi_training_solutions.json` | **NO** | Solution file — never opened |
| `sample_submission.json` | NO | Not needed for this lane |

## Public Challenge JSON Parsing

**Decision:** The lane proceeded with parsing the public challenge JSON (`arc-agi_test_challenges.json`).

Rationale: The owner direction explicitly allowed this as an option: "optionally parse public challenge JSON only to validate schema and produce unscored submission outputs."

Constraints followed:
- No raw grids printed
- No task examples printed
- No task IDs printed except in aggregate counts
- No solution files opened
- No scoring
- No answer comparison

## Shape Validation Result

| Check | Result |
|-------|--------|
| Valid JSON structure | PASS |
| Tasks | 240 |
| Total train pairs | 767 |
| Total test inputs | 259 |
| Grid issues | 0 |
| Schema issues | 0 |
| All tasks have train/test fields | PASS |
| Train pairs have input/output | PASS |
| Test items have input (no output) | PASS |
| Grids are rectangular | PASS |
| Grid cells are integers 0-9 | PASS |

## Staged Package Isolation Result

| Check | Result |
|-------|--------|
| Imported from staged package (`src/weslr_arc_solver/`) | PASS |
| No WESLR repo import dependency | PASS (uses `WESLR_REPO_ROOT` env var) |
| No Termux path dependency inside staging package | PASS |
| No internet/network dependency | PASS |
| No OpenClaw/OCC/Nova dependency | PASS |

## Generated Submission Artifact

| Field | Value |
|-------|-------|
| Output path | `/data/data/com.termux/files/home/weslr-arc-public-shape-dry-runs/public_shape_dry_run_v1_submission.json` |
| Location | Outside repo |
| Size | (measured during run) |

## Submission Artifact Validation Result

| Check | Result |
|-------|--------|
| Valid JSON | PASS |
| One entry per task | PASS (240 entries) |
| One output packet per test input | PASS (259 packets) |
| Exactly two attempts per test input | PASS |
| Every attempt has a valid grid | PASS |
| Grid cells are integers 0-9 | PASS |
| No `expected_output` keys | PASS |
| No `solution` keys | PASS |
| No `public_solution` keys | PASS |
| No `answer_key` keys | PASS |
| No absolute local paths in output JSON | PASS |

## Exactly-Two-Output Status

**PASS** — All 259 test inputs have exactly 2 attempts.

## Deterministic Replay Status

**PASS** — Repeated run produces identical output.

## Runtime/Efficiency Rough Measurement

| Metric | Value |
|--------|-------|
| Import time | 0.010s |
| Parse time | 0.049s |
| Solve time | 100.109s |
| Write time | 0.151s |
| Total runtime | 100.373s |
| Tasks | 240 |
| Test inputs | 259 |
| Time per test input | ~0.387s |

**Note:** This is a local Termux/Android measurement, not Kaggle hardware proof.

## Risky Pattern Search Result

### Staging package (`src/weslr_arc_solver/`)

| Pattern | Matches | Classification |
|---------|---------|---------------|
| `/data/data/com.termux` | 2 | ✅ Acceptable — in `validate_submission_packet()` forbidden-needle check code |
| `arc-agi2-public-source` | 2 | ✅ Acceptable — in `validate_submission_packet()` forbidden-needle check code |
| `expected_output` | 8 | ✅ Acceptable — in docstrings, forbidden-key lists, and scorer parameter |
| `solution` | 4 | ✅ Acceptable — in docstrings and forbidden-key lists |
| `public_solution` | 4 | ✅ Acceptable — in docstrings and forbidden-key lists |
| `answer_key` | 1 | ✅ Acceptable — in `redaction.py` forbidden-key list |
| `requests` | 0 | ✅ Clean |
| `http` | 0 | ✅ Clean |
| `openai` | 0 | ✅ Clean |
| `anthropic` | 0 | ✅ Clean |
| `google` | 0 | ✅ Clean |
| `subprocess` | 0 | ✅ Clean |

### Output JSON

| Pattern | Found? | Classification |
|---------|--------|---------------|
| `/data/data/com.termux` | NO | ✅ Clean |
| `arc-agi2-public-source` | NO | ✅ Clean |
| `expected_output` | NO | ✅ Clean |
| `solution` | NO | ✅ Clean |
| `public_solution` | NO | ✅ Clean |
| `answer_key` | NO | ✅ Clean |

## Public-Data Boundary Assessment

| Check | Status |
|-------|--------|
| Public challenge JSON parsed | YES — `arc-agi_test_challenges.json` only |
| Solution files opened | **NO** |
| Scoring occurred | **NO** |
| Kaggle submission occurred | **NO** |
| Public data copied into repo | NO |
| Generated public-shape outputs committed | NO |
| Task-specific content/grids/examples reported | NO |
| Outputs compared to answers | NO |

## Solver Bug Fix Applied

During the dry run, a crash was encountered in `weslr/arc_hole_row_column_v1.py` at `_infer_fill_color()`. The function assumed `train_in` and `train_out` grids have the same dimensions, but some ARC tasks have different-sized input/output grids, causing an `IndexError`.

**Fix applied:** Added bounds checks before accessing `train_out[r][c]` when `train_in` and `train_out` have different shapes. This is a crash-prevention fix, not a capability change. The fix was necessary to complete the dry run.

## Validation Suite Results

| Check | Result |
|-------|--------|
| `python -m py_compile` on changed Python files | PASS |
| Portability/staging focused tests (25 tests) | 25/25 PASS |
| Public input shape dry-run command | PASS |
| Deterministic rerun check | PASS |
| Risky pattern search | PASS (all acceptable) |
| `git diff --check` | PASS |
| `python weslr/tests/release_gate_v1.py` | PASS |
| `./scripts/weslr_release_check.sh` | PASS |
| `./scripts/chat_weslr_de_health_check.sh --mode source-repo` | PASS (6/6 mandatory) |

## Source-Repo Health Check Status

| Check | Result |
|-------|--------|
| repo branch/HEAD | PASS (main, 3a6cea94) |
| plan doc exists | PASS |
| review doc exists | PASS |
| script executable | PASS |
| release gate recognizes script path | PASS |
| git diff --check | PASS |
| Protected files unchanged | PASS |

## Remaining Risks

1. **Solver capability on real tasks**: The solver ran on all 240 public test tasks and produced output for all 259 test inputs, but output quality was not evaluated. Real ARC-AGI-2 tasks may expose solver capability gaps.

2. **Kaggle hardware performance**: The 100s runtime on Termux/Android is not representative of Kaggle hardware. Actual Kaggle performance may differ significantly.

3. **Submission format compatibility**: The output follows the WESLR submission contract format. A follow-up lane should verify compatibility with the Kaggle sample submission format.

4. **Solver crash robustness**: The bounds-check fix in `arc_hole_row_column_v1.py` addressed one crash, but other solver modules may have similar shape-mismatch assumptions.

## Next Recommended Lane

`WESLR_ARC_AGI2_PUBLIC_EVAL_UNSCORED_CANDIDATE_GENERATION_V1`

This lane should:
- Run the portable solver on the public evaluation challenges
- Generate unscored candidate outputs
- Validate output shape against the sample submission format
- No scoring
- No solution file reads
- No Kaggle submission

## Readiness Verdict

```
public_input_shape_dry_run_v1_passed_ready_for_public_eval_unscored_candidate_generation_lane
```

### Criteria met:
- ✅ Public challenge shape parse succeeds (240 tasks, 259 test inputs)
- ✅ Staged package emits valid unscored submission
- ✅ Exactly-two-output passes
- ✅ Deterministic replay passes
- ✅ No solution files are opened
- ✅ No scoring occurs
- ✅ No Kaggle submission occurs
- ✅ Source-repo health check passes (6/6 mandatory)
