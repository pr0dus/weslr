# WESLR ARC UNKNOWN ENGINE LEVEL LADDER SYNTHETIC SMOKE V2

## 1. Executive verdict
`arc_unknown_engine_level_ladder_synthetic_smoke_v2_passed_internal_threshold`

## 2. Scope and boundary
Confirmed for this lane:
- internal synthetic only
- no public ARC data
- no Kaggle data
- no official claims
- no solver behavior changes
- no generator behavior changes
- no hardening run
- no `.weslr` writes
- no external calls

Important governance note:
- This V2 pass does **not** authorize level hardening.
- Smoke V3, V4, and V5 must also remain `task_exact_rate >= 0.85` before any post-smoke hardening discussion can occur.

## 3. Command and environment
Command used:
```bash
python -c "import sys; sys.path.append('/data/data/com.termux/files/home/weslr-pr47-clean'); from weslr.arc_style_synthetic_solver_suite import run_arc_style_synthetic_solver_suite_v1; print(run_arc_style_synthetic_solver_suite_v1())"
```

Environment:
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Current HEAD: `613b09384da4a47b14ff512a9db196e181584773`

Deterministic / reproducible status:
- Not formally certified in this lane
- Current rerun reproduced the known post-repair metric surface and threshold basis on the same branch state

## 4. Task-level metrics
- Attempted tasks: **36**
- Task exact count: **31**
- Task partial count: **2**
- Task unsupported count: **3**
- Task failed count: **0**
- Task exact rate: **0.8611111111111112** (`31 / 36`)
- Task partial rate: **0.05555555555555555**
- Task unsupported rate: **0.08333333333333333**
- Internal threshold: **0.85**
- Threshold basis: **`task_exact_rate`**
- `internal_pass_85`: **true**
- `level_hardening_allowed` field: **true**
- `level_hardening_reason`: **`task_exact_rate_meets_internal_threshold`**

Governance interpretation:
- V2 task-level status: **pass** against the 85% internal threshold
- Level hardening must still remain **deferred** until Smoke V3, V4, and V5 also stay at or above the same task-level threshold

## 5. Packet-level metrics
- Top-2 packet count: **48**
- Packet exact count: **41**
- Packet partial count: **3**
- Packet unsupported count: **4**
- Packet failed count: **0**
- Packet exact rate: **0.8541666666666666** (`41 / 48`)
- Packet partial rate: **0.0625**
- Packet unsupported rate: **0.08333333333333333**

Diagnostic note:
- Packet metrics are **diagnostic only**
- Packet exact alone must never authorize hardening
- Task exact remains the primary gate metric

## 6. Frontier analysis
Current output frontier fields:
- `hardest_exact_tier = null`
- `hardest_partial_tier = null`
- `first_stable_failure_frontier = null`
- `remaining_partial_families = []`
- `remaining_blocker_families = []`
- `remaining_unsupported_families = []`
- `next_recommended_pressure_family = null`

Interpretation:
- Frontier placeholders are present as expected on the repaired metric surface
- This V2 run does not yet add a richer frontier analysis layer beyond the placeholder fields currently emitted by the suite

## 7. V2/V5 gate status
- Smoke V2 status: **pass** against the 85% internal threshold
- Remaining required confirmations: **Smoke V3, V4, and V5**
- Level hardening authorization: **blocked until V5 still stays >= 0.85 on `task_exact_rate` across the required sequence**

## 8. Recommended next safe local follow-up
`REVIEW_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_SYNTHETIC_SMOKE_V2`

Reason:
- V2 passed on the repaired task-level metric surface
- the correct next step is to review the V2 result before scheduling the next confirmation run
