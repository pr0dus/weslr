# WESLR ARC-AGI2 Real Public Local Score Coverage + Failure Diagnosis V1

- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `main`
- Start HEAD: `e6baaa53d02e60f37824a4922f2af99b7e2f9675`
- End HEAD: `e6baaa53d02e60f37824a4922f2af99b7e2f9675`
- Commit status: clean before this report write
- Actual preflight HEAD: `e6baaa53d02e60f37824a4922f2af99b7e2f9675`
- Previous score summary: total `1120`, correct `0`, incorrect `240`, malformed `0`, missing `880`, non-official exact-match rate `0.0`, candidate unchanged `yes`, solver run in score lane `no`, Kaggle submission `no`, official percentage `none/0`
- Candidate artifact path: `/data/data/com.termux/files/home/arc-agi2-public-source/solver_candidate_dry_run_v1/solver_candidates_no_scoring.json`
- Candidate artifact hash: `0f1aef7bfe3cf379fb1a027c546e597e8926166f844b79d0f5ad3bc863d0e891`

## Coverage audit

Scorer source files used:
- `arc-agi_training_solutions.json` → `1000` tasks
- `arc-agi_evaluation_solutions.json` → `120` tasks

Scorer total: `1120` solution tasks.

Candidate artifact coverage:
- `candidate_task_count`: `240`
- `candidate_test_input_count`: `259`
- candidate split coverage: `arc-agi_test_challenges.json` only (`240` tasks)

Per-file task coverage:
- `arc-agi_training_challenges.json`: candidate intersection `240`
- `arc-agi_training_solutions.json`: candidate intersection `240`
- `arc-agi_evaluation_challenges.json`: candidate intersection `0`
- `arc-agi_evaluation_solutions.json`: candidate intersection `0`
- `arc-agi_test_challenges.json`: candidate intersection `240`
- `sample_submission.json`: candidate intersection `240`

Interpretation:
- The scorer aggregated training + evaluation solutions only.
- The frozen artifact covered only 240 tasks, all keyed to the test-challenge split metadata.
- The `880` missing items are dominated by coverage/split mismatch plus incompleteness, not by per-task format failure.

## ID mapping audit

- Candidate task ids matched the scorer’s training solution task ids for the 240 present tasks.
- No anonymization mismatch observed.
- No prefix/suffix mismatch observed.
- No ordering-only assumption observed.
- The visible mismatch is file/split selection: artifact metadata points at `arc-agi_test_challenges.json`, while scoring consumed training + evaluation solution files.

## Present-candidate audit

For the 240 present tasks:
- present candidate count: `240`
- exact-two-output compliance: pass
- malformed packets by attempt-length check: `0`
- candidate packet attempt count: exactly `2` for all packets
- valid integer-grid comparison format: accepted by checker
- candidate artifacts compared against intended references: yes, for the 240 overlapping training-solution ids

Score-result interpretation for present tasks:
- correct: `0`
- incorrect: `240`
- malformed: `0`

This points to solver/output mismatch on the present coverage, not a candidate-shape failure.

## Score interpretation

Selected classification: `coverage_mismatch_dominant`

Why:
- `880/1120` were missing because the frozen artifact only covered 240 tasks.
- the 240 present tasks were format-valid but all scored incorrect.
- the dominant issue is incomplete coverage of the scored solution set, with a secondary solver/generalization miss on the present tasks.

## Contamination boundary

- The public solution files were accessed in the previous score lane.
- Any future solver improvement on this public set is post-score and solution-exposed.
- A clean future blind claim would require a new held-out source or separate private/Kaggle evaluation, not this public solution-exposed set.

## Lane status

- Official/public ARC data committed: no
- Solver run in this diagnostic lane: no
- Candidate generation in this diagnostic lane: no
- Scoring changed from previous lane: no
- Kaggle submission made: no
- Official percentage remains: `none/0`

## Readiness verdict

`local_score_diagnosis_passed_coverage_mismatch_dominant`

## Recommended next lane

Owner decision on whether to freeze the Kaggle package or hold for any non-blind remediation discussion.
