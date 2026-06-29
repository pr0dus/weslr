# WESLR ARC MDL PROVENANCE AND COMPOSED TRACE SURFACE GAP DIAGNOSIS V1

## 1. Executive verdict
`arc_mdl_provenance_and_composed_trace_surface_gap_diagnosis_needs_repair`

## 2. Scope
- Local diagnosis/report only.
- No replay repair applied.
- No generator / assembler / runtime / emitter mutation.
- No full 48-task replay rerun.
- Expected/scoring answers were not used in generation, diagnostic logic, or deservedness.
- Expected/scoring answers were inspected only in relation to post-ledger scoring/provenance behavior.
- No `.weslr`.
- No external calls.
- Protected files unchanged.

Artifacts/code inspected:
- `docs/WESLR_ARC_GENERATIVE_BRIDGE_V5_REPLAY_AFTER_RIVAL_FALSE_UNIQUENESS_REPAIR_RUN_V1.md`
- `docs/WESLR_ARC_NON_RIVAL_TRACE_COMPLETE_FALSE_POSITIVES_SPLIT_DIAGNOSIS_V1.md`
- `docs/WESLR_ARC_COMPOSED_AND_MDL_FALSE_POSITIVE_ROOT_CAUSE_ATTRIBUTION_V1.md`
- `docs/WESLR_ARC_COMPOSED_AND_MDL_ALTERNATIVE_ENUMERATION_DIAGNOSTIC_RUN_V1.md`
- `docs/WESLR_ARC_COMPOSED_AND_MDL_ALTERNATIVE_ENUMERATION_DIAGNOSTIC_IMPLEMENTATION_REVIEW_V1.md`
- `weslr/arc_generative_bridge_v5_replay.py`
- `weslr/arc_controlled_answer_candidate_generator.py`
- `weslr/arc_composed_mdl_alternative_enumeration_diagnostic.py`
- `weslr/tests/test_arc_generative_bridge_v5_replay_v1.py`

Targeted local reconstructions used:
- six-task current replay reconstruction for `mdl_simplicity_trap_6`
- one representative generated composed candidate from `v4_composed_transform_replay_6`

## 3. MDL false-positive provenance investigation
### A. What the historical artifacts say
Observed artifact conflict:
- replay run report: confirms aggregate `deserved_but_wrong_count = 3` for MDL family scope, but does not preserve durable per-task IDs
- split diagnosis: marks `v5_replay_mdl_simplicity_trap_6_43` and `v5_replay_mdl_simplicity_trap_6_44` as `deserved_but_wrong`, and `45`-`48` as `exact`
- later attribution report: marks `v5_replay_mdl_simplicity_trap_6_44`, `45`, and `46` as `deserved_but_wrong`
- latest diagnostic run report carried forward the split-diagnosis pair `43` and `44` as the only stable known-bad MDL IDs and explicitly left the third unresolved

### B. What the live replay code does now
Observed in `weslr/arc_generative_bridge_v5_replay.py`:
- ledger decision happens first
- only after `candidate_deserved` is true, a synthetic scoring split assigns `deserved_exact` vs `deserved_but_wrong`
- the split is implemented as:
  - `random.seed(hash(task_id) % 2**31)`
  - then `random.random() < 0.5`
- this means the post-ledger exact/wrong label depends on Python's salted `hash(task_id)` value, which is process-dependent unless `PYTHONHASHSEED` is fixed

### C. Targeted local reconstruction results
Current reconstruction was intentionally limited to the six `mdl_simplicity_trap_6` tasks.
This is **not** proof of the historical run's exact/wrong split.
It is only a diagnosis of whether the current replay path can provide a stable source of truth.

Results:
- same-process reruns were internally stable during one interpreter lifetime
- separate Python processes produced different wrong-ID sets

Observed separate-process examples:
- process A wrong IDs: `44`, `45`, `48`
- process B wrong IDs: `43`, `44`

Implications:
- current replay scoring is not durable enough to recover the historical third MDL false-positive ID
- current replay scoring is not stable enough to serve as an authoritative future test oracle unless hash seed and per-task outputs are explicitly fixed/preserved

### D. Stability judgment
No authoritative durable raw per-task MDL truth source was found in current local artifacts.
The only fully direct source would have been preserved raw per-task replay output from the original run, but that output is not present as a durable artifact.

## 4. Authoritative MDL known-bad ID result
Result:
- `mdl_third_false_positive_id_unresolved`

Authoritative third MDL false-positive ID resolved: no.

Authoritative MDL false-positive IDs:
- stable minimum from downstream report agreement: `v5_replay_mdl_simplicity_trap_6_44`
- unstable/conflicted candidates across artifacts/current reconstruction: `43`, `45`, `46`, `48`

Stable source of truth: none found.

Best available source classes, in descending strength:
1. **Missing** raw per-task replay output from the original run — would have been authoritative if preserved
2. downstream report tables — currently conflicting
3. current deterministic-within-process replay reconstruction — not durable because Python hash randomization changes labels across processes
4. downstream inference from aggregate counts — insufficient

Durability judgment for future tests:
- current sources are **not** durable enough to claim full MDL known-bad coverage
- only aggregate MDL wrong-count = 3 is durable from the run report
- the historical third task ID is not trustworthy from current artifacts

Minimum future artifact needed:
- every replay run report must preserve a durable per-task outcome table with task_id, family/group_id, ledger decision, post-ledger status bucket, and hard-stop reason when present

## 5. Artifact conflict summary
Conflicts observed:
- split diagnosis says wrong IDs are `43`, `44`
- attribution says wrong IDs are `44`, `45`, `46`
- current local replay reconstruction can produce `44`, `45`, `48` in one process and `43`, `44` in another
- the prior replay run report preserves only aggregate count `3`, not the stable task IDs

Why the third ID cannot be trusted:
- historical per-task outputs were not durably preserved
- later downstream reports inferred/recorded different task-level sets
- current reconstruction is contaminated by Python hash salt variability because exact/wrong scoring is seeded from `hash(task_id)`
- therefore a current rerun cannot prove the historical exact/wrong split

## 6. Composed trace-surface investigation
Question investigated:
Why did the latest diagnostic run see:
- component list present: no
- alternatives enumerated: no
- component forcedness laundering count: 0

### A. Generator emission check
Observed current composed replay task-builder input in `weslr/arc_generative_bridge_v5_replay.py`:
- `{"composed_transform_candidates": [{"all_components_train_supported": True}]}`

Observed current generated composed candidate behavior in `weslr/arc_controlled_answer_candidate_generator.py`:
- composed candidate eligibility is gated by `all_components_train_supported`
- composed transformation rule is derived generically as `Train examples support the composed transformation chain.`
- composed forced constraint is derived generically as `Every composed transformation component is supported by train examples.`
- no component list, component order, interaction assumption, component support map, subset alternatives, partial-transform surfaces, or explicit full-composition alternatives are emitted by the live generator for this task-builder input

Representative live generated candidate findings:
- `construction_mode = composed_transform_candidate`
- `construction_trace_complete = True`
- `forced_uniqueness_trace_present = True`
- component-level fields present: none
- construction trace contains only generic composed-chain support wording, not unit/component structure

### B. Replay preservation check
The replay path has two different behaviors:
- if `candidate_descriptors_override` is supplied, `_process_task` uses candidate descriptors directly, and the existing test suite confirms replay can propagate supplied trace fields unchanged
- in the actual `v4_composed_transform_replay_6` task-builder path, replay does **not** receive rich component descriptors; it only receives the minimal generator input above and therefore can only process the generic candidate the generator emits

Additional preservation gap:
- `run_generative_bridge_v5_replay_v1()` returns aggregate metrics and group summaries only
- it does **not** preserve durable per-task candidate traces in its returned result artifact
- therefore even if richer traces existed in-process, the standard replay result/report surface currently drops them unless a separate artifact preserves them

### C. Diagnostic input check
The latest diagnostic run report explicitly states it used a **bounded reconstruction** of the 12 target cases and **did not rerun replay**.
Therefore the diagnostic did **not** receive a raw full generation-time candidate artifact from the original replay run.
It received a reconstructed/report-level candidate surface that was already thin.

### D. Root-cause judgment
Primary root cause:
- generator/task-builder trace surface for composed replay cases is too thin

Contributing root causes:
- replay result artifact does not preserve per-task candidate traces durably
- latest diagnostic run used reconstructed/report-level inputs rather than a preserved generation-time trace packet

Not supported as primary cause in this lane:
- diagnostic implementation inability to use available component structure

Reason:
- the diagnostic helper does contain logic for component lists, order permutations, subset/partial alternatives, interaction assumptions, and full alternative compositions
- the required component structure simply was not present in the candidate surface it received

## 7. Generator/replay/diagnostic trace-surface finding
Answers to the required trace-surface questions:

1. Does the generator currently emit component-level trace fields for composed candidates at generation time?
- No, not in the live replay task-builder path used for `v4_composed_transform_replay_6`.
- The current input only carries `all_components_train_supported = true`, and the generator emits generic chain-support wording rather than explicit component structure.

2. Does the replay preserve those fields through to diagnostic input?
- Not for the current composed replay path, because those fields are not generated there in the first place.
- Replay can pass through supplied candidate fields in override mode, but the standard replay result/report surface does not durably preserve per-task candidate traces.

3. Did the diagnostic receive the full generation-time candidate trace, or only a reconstructed/report-level candidate surface?
- Only a reconstructed/report-level candidate surface.

4. Is the gap caused by generator not emitting component structure, replay dropping component structure, diagnostic adapter not passing component structure, diagnostic implementation unable to use available component structure, report reconstruction too thin, or other?
- Primary: generator/task-builder not emitting component structure for composed replay cases
- Secondary: replay/report artifacts dropping durable per-task trace surfaces
- Secondary: bounded reconstruction too thin

5. Next-lane class for the composed issue alone?
- trace-surface plumbing/preservation

Composed trace surface adequate: no.

## 8. Provenance artifact standard
Recommended standard for every future replay/diagnostic run report using aggregate exact/wrong/deserved counts:

### Required durable per-task outcome table
Each run artifact must preserve one row per task with at least:
- `task_id`
- `group_id` / family
- `candidate_generated`
- `ledger_decision`
- `candidate_deserved`
- `deserved_exact`
- `deserved_but_wrong`
- `safe_failure`
- `candidate_not_deserved`
- `hard_stop_triggered`
- `hard_stop_reason_list`
- `post_ledger_scoring_mechanism`
- `post_ledger_scoring_seed_or_determinism_note`

### Required named durable subsets
The artifact must also preserve explicit task-id lists for:
- `candidate_deserved`
- `deserved_exact`
- `deserved_but_wrong`
- `safe_failure`
- `candidate_not_deserved`
- hard-stop triggering cases

### Required trace-preservation note
For any family-specific diagnosis run, the artifact must state whether the diagnostic input came from:
- raw generation-time candidate trace
- replay-preserved per-task trace
- deterministic reconstruction
- downstream report inference

### Required stability note
If any post-ledger label depends on a randomized/scored mechanism, the artifact must state:
- whether the mechanism is deterministic across processes
- whether `PYTHONHASHSEED` or any other runtime salt can change task labels
- whether the per-task labels are suitable as future regression-test oracles

Provenance reporting standard recommended: yes.

## 9. Safety and expected-answer boundary
Confirmed:
- expected/scoring answers are present in replay tasks only as `synthetic_expected_answer_for_scoring_only`
- generator runs before ledger evaluation
- ledger decision happens before post-ledger exact/wrong scoring
- current lane did not use expected answers inside generation, diagnostic logic, or deservedness reasoning
- targeted MDL reconstruction was used only to diagnose provenance stability of the post-ledger scoring split
- no solver/runtime/emitter/final-answer behavior was changed

Important caution:
- because the current exact/wrong split is assigned after ledger decision from a salted-hash-based RNG seed, it should not be treated as an authoritative historical provenance source without a preserved raw per-task artifact

## 10. Recommended next safe local follow-up
`REPAIR_ARC_REPLAY_PER_TASK_PROVENANCE_REPORTING_V1`

Why this is the single next lane:
- reliable repair-test coverage claims are blocked right now by missing/unstable MDL per-task provenance
- the historical third MDL false-positive ID is not recoverable from durable local evidence
- composed trace-surface preservation also needs work, but provenance failure is the earlier cross-family blocker because it prevents trustworthy known-bad-set assertions
- this repair can also establish the durable per-task artifact shape needed to preserve future composed trace packets instead of losing them to aggregate-only reporting
