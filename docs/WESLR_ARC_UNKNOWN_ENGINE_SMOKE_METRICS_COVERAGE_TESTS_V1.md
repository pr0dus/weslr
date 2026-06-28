# WESLR ARC UNKNOWN ENGINE SMOKE METRICS COVERAGE TESTS V1

## 1. Executive verdict
`arc_unknown_engine_smoke_metrics_coverage_tests_added_ready_for_smoke_v2`

## 2. Coverage added
New coverage in `weslr/tests/test_arc_unknown_engine_level_ladder_smoke_metrics_v1.py` now proves more than the original 3-test smoke-metrics surface.

Added tests:
1. **required metric field presence**
   - proves the smoke output exposes task-level counts/rates, packet-level rates, threshold fields, hardening flags, and boundary flags
2. **frontier placeholder field presence**
   - proves the output still carries the expected frontier/report placeholders
3. **formula/denominator checks**
   - proves task rates use `attempted_task_count`
   - proves packet rates use `top2_packet_count`
4. **threshold-basis positive fixture**
   - proves `task_exact_rate >= 0.85` can authorize internal pass/hardening even when `packet_exact_rate < 0.85`
5. **threshold-basis negative fixture**
   - proves `packet_exact_rate >= 0.85` cannot authorize internal pass/hardening when `task_exact_rate < 0.85`
6. **explicit packet-pass/task-fail hardening block**
   - proves packet pass alone cannot unlock hardening
7. **boundary flags consistency**
   - proves synthetic-only / no-public / no-kaggle / no-benchmark-claim flags remain fail-closed
8. **current run sanity**
   - proves current run still advertises `threshold_basis = "task_exact_rate"`, `internal_threshold = 0.85`, nonzero attempted tasks, and top-2 packet count not below attempted tasks

## 3. Threshold policy proof
The strengthened suite now proves the intended policy directly:
- **task exact is primary** because both positive and negative synthetic fixtures route `internal_pass_85` and `level_hardening_allowed` from `task_exact_rate`
- **packet exact is diagnostic** because a packet-pass/task-fail fixture still fails hardening
- **packet pass alone cannot authorize hardening** because the negative fixture has `packet_exact_rate >= 0.85` with `task_exact_rate < 0.85`, yet both `internal_pass_85` and `level_hardening_allowed` remain false
- **task pass can authorize hardening** because the positive fixture has `task_exact_rate >= 0.85` with `packet_exact_rate < 0.85`, yet both `internal_pass_85` and `level_hardening_allowed` remain true

Implementation note:
- a tiny pure helper was added in `weslr/arc_style_synthetic_solver_suite.py` to compute/report policy metrics for fixtures and live result assembly
- the helper does not call the solver or generator
- the helper does not change solver outputs, generated levels, or threshold value
- the live smoke behavior remains metric/report-surface only

## 4. Boundary review
Confirmed in this lane:
- no public ARC data
- no Kaggle data
- no official claims
- no benchmark claims
- no solver behavior changes
- no generator behavior changes
- no `.weslr` writes
- no external calls
- protected files unchanged

## 5. Recommended next safe local follow-up
`RUN_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_SYNTHETIC_SMOKE_V2`

Reason:
- the missing branch artifacts are already recovered
- threshold-policy coverage now proves the task-vs-packet distinction explicitly
- the next safe step is a fresh Smoke V2 confirmation run, still local-only and still not a hardening authorization by itself
