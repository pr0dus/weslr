# WESLR ARC RIVAL GRAMMAR FALSE UNIQUENESS AFTER TRACE GROUNDING REPAIR V1

## 1. Executive verdict
`arc_rival_grammar_false_uniqueness_after_trace_grounding_repaired_but_needs_review`

## 2. Pre-rerun verification finding
The pre-rerun verification found that the original six stable rival-grammar task ids from `v4_rival_grammar_replay_6` still became `candidate_deserved` after the earlier trace-grounding repair.

Critical failure shape:
- they were emitted as `train_forced_transformation_candidate`
- they carried train-grounded constraint fields
- they were marked `construction_trace_complete = true`
- they were marked `forced_uniqueness_trace_present = true`
- but they still lacked candidate-level rival proof fields
- therefore rival uncertainty could bypass deservedness checks through the train-forced path

## 3. Root cause
The prior repair tightened candidate trace grounding and assembler fail-closed behavior, but rival-proof requirements were still effectively mode-specific.

The remaining leak was:
- explicit grammar candidates could be treated as rival cases
- but known rival-context train-forced candidates were not truthfully downgraded when rival proof was absent
- so a train-grounded constraint packet could still look complete even when rival elimination had never been shown

In short: rival context existed at the task family level, but the train-forced candidate path could still present itself as uniquely forced without rival elimination evidence.

## 4. Rival-context detection repair
Added explicit rival-context detection in controlled candidate generation and ledger evaluation.

Rival context now triggers from real task/candidate state, including:
- `task_id` / `group_id` containing `rival_grammar`
- `expected_frontier_failure` containing `rival_grammar`
- explicit rival-context hint fields
- candidate or task rival grammar fields
- unresolved rival fields
- competing grammar markers
- multiple-plausible-transformation markers
- rival/grammar-signaling forced constraints
- incomplete rival fields in an otherwise rival-shaped candidate

Generator candidates now carry:
- `rival_context_detected`
- `rival_context_reasons`

Assembler also re-detects rival context from task-level and candidate-level state so a missing generator flag cannot bypass enforcement.

## 5. No construction-mode bypass repair
The repair removes the construction-mode loophole.

In rival context, a `train_forced_transformation_candidate` can no longer count as complete or uniquely forced unless it also includes rival proof:
- rival grammar set
- surviving grammar
- rival elimination trace
- surviving-grammar train evidence
- rival outputs considered
- rejected rival reasons
- surviving grammar uniquely forces output

If rival context is detected and that proof is missing:
- `construction_trace_complete = false`
- `forced_uniqueness_trace_present = false`
- `ambiguity_check = unresolved`
- `unresolved_rivals` is extended with `rival_context_unresolved`
- unique-force text is cleared
- candidate cannot become deserved

## 6. Candidate trace truthfulness repair
Train-grounded constraints are now treated as necessary but not sufficient in rival context.

A rival-context candidate is no longer allowed to claim completeness just because it has:
- source train ids
- a train-grounded transformation rule
- train-grounded forced constraints

When rival context exists, missing rival proof is now recorded in `missing_required_trace_fields` and truthfully keeps the candidate incomplete.

## 7. Assembler enforcement repair
Assembler enforcement was expanded so rival-proof checks apply regardless of construction mode.

Assembler now:
- detects rival context from task/candidate state
- rejects rival-context candidates that still carry unresolved rivals
- rejects rival-context candidates missing rival proof even if their mode is `train_forced_transformation_candidate`
- increments dedicated rival-context metrics on actual rejection paths
- increments `train_forced_rival_bypass_blocked_count` when the blocked candidate is train-forced

This preserves fail-closed behavior and does not weaken any existing safety rejection.

## 8. Known-bad case tests
Added targeted tests for the six stable rival-context task ids:
- `v5_replay_v4_rival_grammar_replay_6_01`
- `v5_replay_v4_rival_grammar_replay_6_02`
- `v5_replay_v4_rival_grammar_replay_6_03`
- `v5_replay_v4_rival_grammar_replay_6_04`
- `v5_replay_v4_rival_grammar_replay_6_05`
- `v5_replay_v4_rival_grammar_replay_6_06`

Targeted local verification after repair shows:
- `candidate_deserved_tasks = 0`
- `safe_failure_count = 6`
- `safe_failure_from_unresolved_rival_count = 6`
- `rival_context_detected_count = 6`
- `rival_context_missing_proof_count = 6`
- `rival_context_safe_failure_count = 6`
- `train_forced_rival_bypass_blocked_count = 6`

This means no stable known-bad rival-context case now becomes deserved without rival proof.

## 9. Safe-failure preservation
The earlier safe-failure repair remains preserved in local validation.

Validated preserved routes:
- insufficient evidence -> safe failure
- incomplete trace -> safe failure
- unresolved rival -> safe failure

No regression was introduced in the assembler’s task-level safe-failure aggregation.

## 10. Expected-answer boundary preservation
Expected-answer fields were not introduced into:
- generator deservedness logic
- trace grounding
- rival proof
- forced uniqueness
- assembler deservedness

Scoring-only fields remain outside candidate generation and ledger decision.
Targeted tests continue to verify generation before ledger and ledger before scoring.

## 11. Metrics
Added / repaired the following live metrics:
- `rival_context_detected_count`
- `rival_context_missing_proof_count`
- `rival_context_safe_failure_count`
- `train_forced_rival_bypass_blocked_count`

These increment from actual candidate/task state in generator/replay/assembler paths.
They are not constants.

## 12. Safety boundaries
This lane stayed within the requested boundary:
- local only
- no full V5 replay run
- no push
- no public ARC/Kaggle data
- no external calls
- no hidden-test output use
- no expected-answer leakage into generation or deservedness
- no runtime solver wiring
- no ChatResponder changes
- no emitter implementation
- no `.weslr`
- protected files left unchanged

## 13. Recommended next safe local follow-up
`REVIEW_ARC_RIVAL_GRAMMAR_FALSE_UNIQUENESS_AFTER_TRACE_GROUNDING_REPAIR_V1`
