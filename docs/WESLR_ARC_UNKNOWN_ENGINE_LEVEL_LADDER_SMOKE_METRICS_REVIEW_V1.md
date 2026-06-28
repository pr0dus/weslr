# WESLR ARC UNKNOWN ENGINE LEVEL LADDER SMOKE METRICS REVIEW V1

## 1. Executive verdict
`arc_unknown_engine_smoke_metrics_repair_blocked_by_branch_state`

The repaired metric surface in `weslr/arc_style_synthetic_solver_suite.py` looks internally consistent for the requested task-level vs packet-level split, and the 85% hardening basis is wired to `task_exact_rate` in the current code path. However, branch provenance is not clean enough to call Smoke V2 safe yet: the requested earlier ARC audit/smoke reference commit `98eed788b2a76ba2b41276ea41fc45c5694fa456` is not present in the local repository object graph, the referenced prior ARC audit/smoke artifacts are not present on this branch, and the requested containment check therefore cannot be proven locally. Separately, the new 3-test suite is too thin to prove the threshold-policy contract against future regressions.

## 2. Branch/ancestry review
- Current branch: `occ-discovery-doctrine-implementation-20260613`
- Current HEAD: `dab72697b027f8b4c9795821282ce91c24f6cb4f`
- Working tree at review start was not clean: `M weslr/tests/release_gate_v1.py`
- `bfd3625aedc507b6c051d8b0edce8b8fc7747b0c` **is** an ancestor of HEAD.
- `98eed788b2a76ba2b41276ea41fc45c5694fa456` could not be verified as an ancestor because it is not present locally (`git rev-list --all` returned no match; `git merge-base --is-ancestor ... HEAD` failed with invalid commit / missing object).
- Recent first-parent history from the current branch tip is continuous from `bfd3625a` to `dab72697`; there is no direct local evidence of a reset on that visible segment.
- Even so, there is a provenance gap: the earlier ARC audit/smoke work cited in the dispatch is not recoverable from the local branch state provided for review. That leaves real divergence / off-branch-work / missing-receipt risk unresolved.

## 3. Metric field review
Current suite output exposes the requested split fields:

### Task-level fields present
- `task_exact_count = 31`
- `task_partial_count = 2`
- `task_unsupported_count = 3`
- `task_failed_count = 0`
- `task_exact_rate = 0.8611111111111112`
- `task_partial_rate = 0.05555555555555555`
- `task_unsupported_rate = 0.08333333333333333`

### Packet-level fields present
- `top2_packet_count = 48`
- `synthetic_exact_count = 41`
- `synthetic_partial_count = 3`
- `synthetic_unsupported_count = 4`
- `packet_exact_rate = 0.8541666666666666`
- `packet_partial_rate = 0.0625`
- `packet_unsupported_rate = 0.08333333333333333`

### Threshold / frontier / boundary fields present
- `internal_threshold = 0.85`
- `threshold_basis = "task_exact_rate"`
- `internal_pass_85 = True`
- `level_hardening_allowed = True`
- `level_hardening_reason = ""`
- Frontier placeholders present: `hardest_exact_tier`, `hardest_partial_tier`, `first_stable_failure_frontier`, `remaining_partial_families`, `remaining_blocker_families`, `remaining_unsupported_families`, `next_recommended_pressure_family`
- Boundary flags present and still fail-closed for public claims: `synthetic_only = True`, `public_arc_used = False`, `kaggle_used = False`, `benchmark_claim_safe = False`

Assessment:
- Question 1: **Yes** — repaired output includes task-level metric fields.
- Question 2: **Yes** — repaired output includes packet-level metric fields.
- Question 9: **Yes** — public ARC/Kaggle boundary fields remain false.

## 4. 85% internal threshold review
Confirmed from the live code path and current suite output:
- Primary metric is `task_exact_rate`.
- `task_exact_rate` is computed from `task_exact_count / attempted_task_count`.
  - Current values: `31 / 36 = 0.8611111111111112`
- `packet_exact_rate` is computed from `synthetic_exact_count / top2_packet_count`.
  - Current values: `41 / 48 = 0.8541666666666666`
- `internal_pass_85` uses task exact, not packet exact.
- `level_hardening_allowed` uses task exact, not packet exact.
- Hardening must not happen from packet exact alone, and the implementation expresses that intent via `threshold_basis = "task_exact_rate"` plus duplicated task-rate threshold checks.

Assessment:
- Question 3: **Yes**.
- Question 4: **Yes**.
- Question 5: **Yes** in the current implementation.
- Question 6: **Yes** in the current implementation.

Important limitation: the current tests do **not** create a discriminating case where `task_exact_rate` and `packet_exact_rate` fall on opposite sides of 0.85. Because the current live output has both rates above 0.85, the tests do not actually prove that a future regression could not switch the threshold basis silently.

## 5. Test coverage review
Observed:
- `weslr/tests/test_arc_unknown_engine_level_ladder_smoke_metrics_v1.py` contains 3 tests.
- The 3 tests pass.
- The tests cover:
  1. `packet_exact_rate` formula.
  2. `task_exact_rate` formula plus current `internal_pass_85` / `level_hardening_allowed` alignment.
  3. Boundary flag consistency.

Coverage judgment:
- Question 10: **3-test coverage is too thin for the metric policy gate before Smoke V2**.
- The suite does **not** prove all requested metric rules strongly enough.
- Missing tests that matter:
  - A negative threshold-basis test where `task_exact_rate >= 0.85` but `packet_exact_rate < 0.85`.
  - The inverse negative test where `packet_exact_rate >= 0.85` but `task_exact_rate < 0.85`.
  - Direct field-presence assertions for the new task-level / packet-level / frontier placeholder fields.
  - Explicit assertions that hardening cannot be unlocked by packet exact alone.
  - A no-behavior-change regression test focused on unchanged solver selection outputs if that policy is important for this lane.

Conclusion: implementation appears correct, but coverage is not yet strong enough to treat the threshold-policy surface as locked.

## 6. Solver/generator behavior review
Confirmed from commit scope and local inspection:
- Repair commit `dab72697b027f8b4c9795821282ce91c24f6cb4f` changed:
  - `weslr/arc_style_synthetic_solver_suite.py`
  - `weslr/tests/test_arc_unknown_engine_level_ladder_smoke_metrics_v1.py`
  - `docs/WESLR_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_SMOKE_METRICS_REPAIR_V1.md`
- No solver primitive files were changed.
- No generator files were changed.
- No new primitives were added.
- No solver behavior change is visible in the reviewed diff; the code change is confined to result-surface metrics / flags in the suite result assembly.
- No generator behavior change is visible except result-surface metric exposure at suite-summary level.
- No public ARC/Kaggle data was used in this review.
- No `.weslr` file was read or written in this review.
- No provider/model/API/external calls were used in this review.
- Protected files remained untouched:
  - `weslr/chat_responder.py`
  - `weslr/main.py`
  - `main.py`
  - `dialogue.py`
  - `chat_ui.py`

Assessment:
- Question 7: **Yes** — no solver behavior change was found in the repair diff.
- Question 8: **Yes** — no generator behavior change was found beyond metric exposure.

## 7. Recommended next safe local follow-up
`REPAIR_BRANCH_STATE_AFTER_SMOKE_METRICS_REPAIR_V1`

Reason:
- The requested earlier ARC audit/smoke reference commit cannot be verified locally.
- Prior ARC audit/smoke artifacts cited in the dispatch are not present on the reviewed branch state.
- Even if the metric repair looks locally correct, provenance is not clean enough yet.
- The test suite is also still too thin for a threshold-policy gate.
