# WESLR ARC V5 KNOWN BAD CASES AND SAFE FAILURE ROUTING PRE-RERUN VERIFICATION V1

## 1. Executive verdict
`arc_v5_known_bad_cases_pre_rerun_verification_needs_repair`

## 2. Scope
- Reviewed the original V5 replay run report, diagnosis report, assembler repair/report chain, and trace-grounding repair/report chain.
- Performed targeted local verification only.
- Did **not** run the full 48-task replay.
- Did **not** modify runtime, emitter, protected files, or `.weslr`.

## 3. Original six deserved cases identified
The original six deserved task ids from `v4_rival_grammar_replay_6` are:
- `v5_replay_v4_rival_grammar_replay_6_01`
- `v5_replay_v4_rival_grammar_replay_6_02`
- `v5_replay_v4_rival_grammar_replay_6_03`
- `v5_replay_v4_rival_grammar_replay_6_04`
- `v5_replay_v4_rival_grammar_replay_6_05`
- `v5_replay_v4_rival_grammar_replay_6_06`

Important note:
- The old reports agree that there were 6 deserved cases and 3 exact / 3 wrong in aggregate.
- But the diagnosis table’s per-task exact/wrong labels conflict with that aggregate.
- Direct code review shows the old replay scoring used `random.seed(hash(task_id) % 2**31)`, which means the exact/wrong split was process-dependent rather than a stable property of the task ids.
- So the six task ids are stable, but the historic exact-vs-wrong per-task labeling is not fully trustworthy as a durable artifact.

## 4. Original three deserved-but-wrong cases replayed
Using the current repaired generator + current repaired assembler on the original six rival-grammar tasks:
- all 6 tasks still generate a complete `train_forced_transformation_candidate`
- all 6 candidates still have `missing_required_trace_fields = []`
- all 6 still produce assembler decision `candidate_deserved`
- task-level safe failure remains false for all 6

In the current verification process, 3 of those 6 still score wrong **after** ledger decision:
- `v5_replay_v4_rival_grammar_replay_6_01`
- `v5_replay_v4_rival_grammar_replay_6_02`
- `v5_replay_v4_rival_grammar_replay_6_05`

These remain wrong only in scoring-after-ledger, but the critical finding is unchanged:
- wrong rival-grammar cases still become `candidate_deserved`
- therefore the known bad condition is **not** repaired for this path

## 5. Original three deserved-exact cases replayed
In the current verification process, 3 of the same 6 tasks score exact after ledger decision:
- `v5_replay_v4_rival_grammar_replay_6_03`
- `v5_replay_v4_rival_grammar_replay_6_04`
- `v5_replay_v4_rival_grammar_replay_6_06`

Signal interpretation:
- some correct cases still have a deserved path
- but wrong cases still also have a deserved path
- this is unsafe and blocks the rerun

## 6. Rival-grammar false-uniqueness check
- **Failed.**
- The original rival-grammar group tasks still produce `candidate_deserved` without any candidate-level rival grammar set, surviving grammar, or rival elimination trace.
- They are emitted as `train_forced_transformation_candidate` with complete trace flags and train-grounded constraint fields, but they still do not prove rival-grammar elimination.
- Because wrong cases still pass deservedness, the rival-grammar false-uniqueness bug remains live in the pre-rerun targeted check.

## 7. Safe-failure routing for insufficient evidence
- **Valid in the targeted routing check.**
- A generated candidate with complete review state but `train_evidence_grounded = false` now produces:
  - `candidate_not_deserved_count = 1`
  - `safe_failure_required_count = 1`
  - task-level `safe_failure = true`
  - `safe_failure_from_insufficient_evidence_count = 1`
- The old collapse pattern (`insufficient_train_evidence_count > 0` with `safe_failure_count = 0`) does not persist in this targeted route.

## 8. Safe-failure routing for incomplete trace
- **Valid in the targeted routing check.**
- A generated/replayed candidate with incomplete construction trace now produces:
  - candidate rejection
  - task-level `safe_failure = true`
  - `safe_failure_required_count = 1`
  - `safe_failure_from_incomplete_trace_count = 1`

## 9. Safe-failure routing for unresolved rival
- **Valid in the targeted routing check.**
- A candidate carrying rival grammar state without surviving grammar / rival elimination proof now produces:
  - candidate rejection
  - task-level `safe_failure = true`
  - `safe_failure_required_count = 1`
  - `safe_failure_from_unresolved_rival_count = 1`
  - `rival_unresolved_count = 1`

## 10. Expected-answer boundary confirmation
- Candidate generation remains before ledger evaluation.
- Ledger evaluation remains before scoring.
- The assembler input path still excludes expected-answer fields during targeted checks.
- Expected answers were used only after ledger decision for local verification labeling.
- The assembler still has fail-closed protection against scoring-only key leakage inside assembler input.

## 11. Interpretation
Two different conclusions emerged:

1. **Safe-failure routing repair is working in targeted checks.**
   - insufficient evidence, incomplete trace, and unresolved rival all preserve task-level safe failure when no candidate deserves approval.

2. **The original rival-grammar known-bad condition is still not safe enough for rerun.**
   - all six original `v4_rival_grammar_replay_6` tasks still become `candidate_deserved`
   - three of those still score wrong after ledger decision in the current verification process
   - therefore the rerun should not proceed yet

The pre-rerun blocker is not safe-failure routing anymore.
The blocker is residual false deservedness in the rival-grammar known-bad family.

## 12. Recommended next safe local follow-up
`REPAIR_ARC_RIVAL_GRAMMAR_FALSE_UNIQUENESS_AFTER_TRACE_GROUNDING_V1`
