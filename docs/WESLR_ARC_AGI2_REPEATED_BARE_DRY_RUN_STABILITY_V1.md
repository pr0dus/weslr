# WESLR ARC-AGI-2 Repeated Bare Dry Run Stability V1

## Metadata

| Field | Value |
|-------|-------|
| Repository | `/data/data/com.termux/files/home/weslr-pr47-clean` |
| Branch | `main` |
| Start HEAD | `6feca1131a4d370717ee8f794f3e0e2554372b04` |
| End HEAD | (committed below) |
| Preflight match | YES |
| Lane type | Repeated bare dry run stability |
| Previous lane | `WESLR_ARC_AGI2_KAGGLE_SUBMISSION_FORMAT_REPAIR_V1` |
| Previous verdict | `kaggle_submission_format_repair_v1_passed_ready_for_repeated_bare_dry_run_stability_lane` |

## Preflight HEAD Verification

| Check | Result |
|-------|--------|
| Expected HEAD prefix | `6feca113` |
| Actual HEAD | `6feca1131a4d370717ee8f794f3e0e2554372b04` |
| Match | YES |

## Run Command

```bash
python scripts/run_kaggle_format_submission_dry_run_v1.py --bare \
  --output-json <run_dir>/submission_kaggle_format.json \
  --work-dir <run_dir>
```

Orchestrated by:
```bash
python scripts/run_repeated_bare_dry_run_v1.py
```

## Number of Runs

**5** bare-mode executions, unattended.

## Per-Run Table

| Run | Exit Code | Total Time | Solve Time | Output Size | Output SHA256 (prefix) |
|-----|-----------|------------|------------|-------------|------------------------|
| 01 | 0 | 141.164s | 140.680s | 2,423,978 | `78f295d33a665325` |
| 02 | 0 | 130.595s | 130.082s | 2,423,978 | `78f295d33a665325` |
| 03 | 0 | 126.203s | 125.506s | 2,423,978 | `78f295d33a665325` |
| 04 | 0 | 145.728s | 145.233s | 2,423,978 | `78f295d33a665325` |
| 05 | 0 | 135.848s | 135.263s | 2,423,978 | `78f295d33a665325` |

## Output Hash Comparison

| Check | Result |
|-------|--------|
| All 5 output SHA256 match | **YES** |
| Canonical hash | `78f295d33a665325393ee03bd40cf0816beccbd32787d321522f180a2a3eb7c9` |

**Verdict: Fully deterministic.** All 5 runs produced byte-identical output.

## Output Size Comparison

| Metric | Value |
|--------|-------|
| Min | 2,423,978 bytes |
| Max | 2,423,978 bytes |
| Mean | 2,423,978 bytes |
| All identical | YES |

**Verdict: Output size is stable and identical across all runs.** At ~2.4 MB, the output is reasonable for a Kaggle submission (typical limit is 20-100 MB).

## Timing Summary

| Metric | Total Runtime | Solve Time |
|--------|--------------|------------|
| Min | 126.203s | 125.506s |
| Max | 145.728s | 145.233s |
| Mean | 135.908s | 135.263s |
| Median | 135.848s | 135.263s |
| Std Dev | ~7.5s | ~7.5s |

**Slowest phase:** Solve time dominates (~99.5% of total). Import, parse, convert, write, and validate together account for <1s.

**Timing variance:** ~15% range (126s-146s). This is expected on a shared Android device with background processes. The solve phase is CPU-bound and deterministic in algorithm, so variance is from system load, not solver instability.

**Per-test-input runtime:** ~0.79s average (135s / 172 test inputs).

## Format Validation Summary

| Check | Run 01 | Run 02 | Run 03 | Run 04 | Run 05 |
|-------|--------|--------|--------|--------|--------|
| Valid JSON | PASS | PASS | PASS | PASS | PASS |
| 120 task entries | PASS | PASS | PASS | PASS | PASS |
| 172 test input packets | PASS | PASS | PASS | PASS | PASS |
| Exactly two attempts | PASS | PASS | PASS | PASS | PASS |
| Valid grids | PASS | PASS | PASS | PASS | PASS |
| Integer cells 0-9 | PASS | PASS | PASS | PASS | PASS |
| No WESLR metadata | PASS | PASS | PASS | PASS | PASS |
| No forbidden keys | PASS | PASS | PASS | PASS | PASS |
| No local paths | PASS | PASS | PASS | PASS | PASS |

## Exactly-Two-Output Status

**PASS** — All 5 runs have exactly 2 attempts per test input (172 test entries × 2 attempts = 344 grids per run).

## Deterministic Stability Status

**PASS** — All 5 runs produce byte-identical output (SHA256 match across all runs).

## Public-Data Boundary Status

| Check | Result |
|-------|--------|
| Solution files opened | **NO** (all 5 runs) |
| Scoring occurred | **NO** (all 5 runs) |
| Kaggle submission occurred | **NO** (all 5 runs) |
| Generated outputs/logs outside repo | YES |
| Public data copied into repo | NO |

## Risky Pattern Search Result

### Submission JSON files (all 5 runs)

| Pattern | Found? | Classification |
|---------|--------|---------------|
| `/data/data/com.termux` | NO | ✅ Clean |
| `arc-agi2-public-source` | NO | ✅ Clean |
| `expected_output` | NO | ✅ Clean |
| `solution` | NO | ✅ Clean |
| `public_solution` | NO | ✅ Clean |
| `answer_key` | NO | ✅ Clean |
| `kaggle_ready` | NO | ✅ Clean |
| `synthetic_only` | NO | ✅ Clean |
| `schema_version` | NO | ✅ Clean |
| `metadata` | NO | ✅ Clean |
| `requests` | NO | ✅ Clean |
| `http` | NO | ✅ Clean |
| `openai` | NO | ✅ Clean |
| `anthropic` | NO | ✅ Clean |
| `google` | NO | ✅ Clean |
| `subprocess` | NO | ✅ Clean |

### Run log files (all 5 runs)

| Pattern | Found? | Classification |
|---------|--------|---------------|
| `/data/data/com.termux` | YES | ✅ Acceptable — in `output_path` field of log JSON |
| `solution` | YES | ✅ Acceptable — in `no_solution_read` boolean field name |
| `metadata` | YES | ✅ Acceptable — in `metadata_clean` boolean field name |

All other patterns: clean.

## OCC/No-Watch Execution

The 5 runs were executed unattended via the orchestration script. The total wall time was approximately 11 minutes 20 seconds (680s for 5 runs). This is consistent with running 5 sequential ~136s solves.

**Observation:** The orchestration script added minimal overhead (~0.5s per run for file I/O and hash computation). The solve time dominates.

## Remaining Risks

1. **Kaggle hardware performance**: The ~136s average runtime on Termux/Android is not representative of Kaggle hardware. Actual Kaggle performance may differ significantly (likely faster on dedicated CPU/GPU instances).

2. **Output file size**: At ~2.4 MB, the output is reasonable but should be verified against Kaggle's specific submission size limits for ARC-AGI-2.

3. **Solver quality unknown**: The solver produced deterministic output for all 172 test inputs without crashing, but output quality was not evaluated. Real ARC-AGI-2 tasks may expose solver capability gaps.

4. **Kaggle notebook bundle**: The current staged package requires the WESLR repo to be accessible via `WESLR_REPO_ROOT`. A Kaggle notebook would need to bundle both the staging package and the solver modules.

5. **Timing variance**: ~15% variance (126-146s) is acceptable for a development environment but should be monitored on Kaggle hardware.

## Next Recommended Lane

`WESLR_ARC_AGI2_KAGGLE_NOTEBOOK_BUNDLE_REVIEW_V1`

This lane should:
- Review the staged package for Kaggle notebook compatibility
- Determine what needs to be bundled alongside the staging package
- Verify the solver modules can be copied/installed in a Kaggle environment
- Document the exact submission workflow
- No scoring
- No solution file reads
- No Kaggle submission

## Readiness Verdict

```
repeated_bare_dry_run_stability_v1_passed_ready_for_kaggle_notebook_bundle_review_lane
```

### Criteria met:
- ✅ All 5 bare runs exit 0
- ✅ All output hashes match (byte-identical)
- ✅ All outputs validate (120 tasks, 172 test inputs, exactly-two-output)
- ✅ No forbidden keys appear in output
- ✅ No solution files are opened
- ✅ No scoring occurs
- ✅ No Kaggle submission occurs
- ✅ Source-repo health check passes (6/6 mandatory)
