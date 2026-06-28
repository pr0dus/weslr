# WESLR ARC UNKNOWN ENGINE SMOKE ARTIFACTS RECOVERY V1

## 1. Executive verdict
`arc_unknown_engine_smoke_artifacts_recovered_ready_for_metric_coverage_tests`

## 2. Recovery basis
- Current branch: `occ-discovery-doctrine-implementation-20260613`
- Current branch HEAD at recovery start: `a24a3f61474a8b8ed42b95d515c4206ab1eb5ae9`
- Missing cited historical reference: `98eed788b2a76ba2b41276ea41fc45c5694fa456`
- `98eed...` present locally: **no**
- Missing original artifacts before recovery:
  - `docs/WESLR_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_AND_FROZEN_SOLVER_STATE_AUDIT_V1.md`
  - `docs/WESLR_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_SYNTHETIC_SMOKE_V1.md`
  - `docs/WESLR_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_SYNTHETIC_SMOKE_REVIEW_V1.md`
- Recovery inputs used:
  1. current branch code inspection
  2. current local execution of `run_arc_style_synthetic_solver_suite_v1()`
  3. current committed smoke-metrics repair and review docs
  4. owner-provided receipt values only when clearly labeled as recovered-from-receipt context
- What cannot be proven:
  - exact historical wording of the missing original artifacts
  - whether the missing docs were ever committed in another clone / branch
  - ancestry or authenticity of the absent `98eed...` commit

## 3. Recovered artifact list
### `docs/WESLR_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_AND_FROZEN_SOLVER_STATE_AUDIT_V1.md`
Contains:
- explicit recovered/current-branch status
- generator found yes/no from current branch
- solver/runner found yes/no from current branch
- safe runner command
- current smoke signal summary
- provenance limitations
- recommended next lane after recovery

### `docs/WESLR_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_SYNTHETIC_SMOKE_V1.md`
Contains:
- recovered smoke command
- generated ladder levels
- attempted tasks
- top-2 packet count
- task exact count/rate
- packet exact count/rate
- partial / unsupported / failed / skipped counts
- trusted frontier note marked as recovered-from-receipt
- boundary statement
- explicit note that this is recovered current-branch documentation, not the original missing artifact

### `docs/WESLR_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_SYNTHETIC_SMOKE_REVIEW_V1.md`
Contains:
- explicit recovered/current-branch review status
- explanation of the original task-vs-packet ambiguity
- task exact as primary metric
- packet exact as diagnostic metric
- 85% hardening rule on `task_exact_rate`
- explicit no-hardening-yet rule pending stronger tests and Smoke V2
- recommended next lane

## 4. Metric integrity note
Confirmed on the current branch:
- task exact is the **primary** internal metric
- packet exact is **diagnostic** only
- the 85% threshold uses **`task_exact_rate`**
- current branch live values remain:
  - `task_exact_count = 31`
  - `attempted_task_count = 36`
  - `task_exact_rate = 0.8611111111111112`
  - `synthetic_exact_count = 41`
  - `top2_packet_count = 48`
  - `packet_exact_rate = 0.8541666666666666`
- Smoke V2 is still required before any hardening decision, and only after metric coverage tests are strengthened

## 5. Boundary review
Confirmed in this recovery lane:
- no public ARC data
- no Kaggle data
- no benchmark claims
- no official scoring claims
- no ARC-AGI-1 / ARC-AGI-2 performance claims
- no solver behavior changes
- no generator behavior changes
- no `.weslr` writes
- no external calls / provider calls / API calls
- no protected files touched

## 6. Recommended next safe local follow-up
`ADD_ARC_UNKNOWN_ENGINE_SMOKE_METRICS_COVERAGE_TESTS_V1`

Reason:
- the missing continuity artifacts are now restored on the current valid branch
- the branch-state provenance gap has been reconciled as far as local evidence allows
- the remaining blocker before Smoke V2 is thin metric-policy coverage, not missing documentation
