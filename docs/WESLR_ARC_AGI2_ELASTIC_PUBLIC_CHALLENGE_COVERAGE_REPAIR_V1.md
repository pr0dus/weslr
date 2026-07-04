# WESLR ARC-AGI2 Elastic Public Challenge Coverage Repair V1

- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `main`
- Start HEAD: `4933b614c6115179470dfe6a3a9aca934024a872`
- End HEAD: `6a31cbae01af9e0b2039bc030be67d8be1e0e3b3`
- Commit status: clean at code checkpoint
- Actual preflight HEAD: `4933b614c6115179470dfe6a3a9aca934024a872`

## Previous diagnosis

- Verdict: `local_score_diagnosis_passed_coverage_mismatch_dominant`
- Scorer used `arc-agi_training_solutions.json` = `1000` tasks
- Scorer used `arc-agi_evaluation_solutions.json` = `120` tasks
- Total scoreable public tasks = `1120`
- Frozen candidate artifact covered only `240` tasks
- Artifact covered `arc-agi_test_challenges.json` only
- Missing = `880`
- Present `240` were format-valid but all incorrect
- No anonymization mismatch
- Candidate hash unchanged

## Contamination boundary

- Public solutions were already exposed in the prior local score lane.
- This repair lane is post-exposure.
- Any future solver improvement on this public set cannot be claimed as blind on the same data.

## Files changed

- `weslr/arc_agi2_public_challenge_solver_candidate_runner.py`
- `scripts/run_arc_agi2_public_challenge_solver_candidate_dry_run.py`
- `weslr/tests/test_arc_agi2_public_challenge_solver_candidate_runner_v1.py`

## Target modes implemented

- `public_scoreable`
- `kaggle_test_submission_shape`
- `all_public_challenges_no_score`

## Hardcoded 240 removal result

- Removed global 240-only assumption from candidate generation.
- Counts are now discovered dynamically from selected challenge files.
- Candidate coverage is validated against discovered task/test-input totals.

## Dynamic discovery results

### `public_scoreable`
- Challenge files used: training + evaluation
- Task count: `1120`
- Test-input count: `1248`
- Artifact: `/data/data/com.termux/files/home/arc-agi2-public-source/solver_candidate_dry_run_v2/public_scoreable_candidates_no_submission.json`
- Artifact hash: `eb914bf6616b7ffd0c938488ef417dc4f2db0709d3e43d1f57767eb4c51f6b1e`

### `kaggle_test_submission_shape`
- Challenge files used: test
- Task count: `240`
- Test-input count: `259`
- Sample submission alignment: pass
- Artifact: `/data/data/com.termux/files/home/arc-agi2-public-source/solver_candidate_dry_run_v2/kaggle_test_candidates_no_submission.json`
- Artifact hash: `8a0c88e98ce959a4a9b74e2c178e24dc80a442a28791ded4f467d81320954bde`

### `all_public_challenges_no_score`
- Challenge files used: training + evaluation + test
- Task count: `1360`
- Test-input count: `1507`
- Artifact: `/data/data/com.termux/files/home/arc-agi2-public-source/solver_candidate_dry_run_v2/all_public_challenges_candidates_no_score.json`
- Artifact hash: `c6667dd2e8b84529ca1ee4033f2bf7728794ece0962230adf33b35b069adeb9a`

## Coverage validation

- Complete coverage validation: pass
- Exactly-two-output validation: pass
- Missing candidate handling: fail-closed in tests and validator
- Solution files opened during candidate generation: no
- Solver hashes unchanged: yes
- Raw-grid leakage: false
- Expected-output leakage: false

## Post-exposure local public score

- Scoring performed in this lane: yes
- Label: `post_exposure_local_public_score_non_official`
- Candidate artifact scored: `public_scoreable_candidates_no_submission.json`
- Candidate artifact hash before scoring: `eb914bf6616b7ffd0c938488ef417dc4f2db0709d3e43d1f57767eb4c51f6b1e`
- Candidate artifact hash after scoring: `eb914bf6616b7ffd0c938488ef417dc4f2db0709d3e43d1f57767eb4c51f6b1e`
- Candidate artifact unchanged: yes
- Solution files parsed for scoring: yes
- Solver run in score step: no
- Candidate generation in score step: no
- Total tasks scored: `1120`
- Correct count: `0`
- Incorrect count: `1120`
- Malformed candidate count: `0`
- Missing candidate count: `0`
- Exactly-two-output compliance: pass
- Local public exact-match rate (non-official): `0.0`

## Lane status

- Official/public ARC data committed: no
- Kaggle submission made: no
- Official percentage remains: `0`

## Readiness verdict

`elastic_public_challenge_coverage_repair_passed_with_post_exposure_score`

## Recommended next lane

Owner decision on whether to freeze the Kaggle package or hold for any further non-blind follow-up.
