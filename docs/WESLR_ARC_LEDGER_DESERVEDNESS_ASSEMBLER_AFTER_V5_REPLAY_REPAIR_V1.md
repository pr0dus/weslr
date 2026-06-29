# WESLR ARC LEDGER DESERVEDNESS ASSEMBLER AFTER V5 REPLAY REPAIR V1

## 1. Executive verdict
`arc_ledger_deservedness_assembler_after_v5_replay_repaired_but_needs_review`

## 2. Diagnosis summary
- Repaired the task-level forced-constraint leak that let candidate deservedness piggyback on task context.
- Repaired the construction-trace enforcement gap by fail-closing candidates without explicit candidate-level trace completeness, source grounding, train grounding, and forced-uniqueness proof.
- Repaired task-level safe-failure routing so insufficient evidence, incomplete traces, and unresolved rivals preserve safe-failure accounting instead of collapsing into plain candidate rejection.

## 3. Candidate-level forced uniqueness repair
- `candidate_deserved` now requires candidate-level proof only.
- Task-level `forced_constraints` remain contextual input, but they no longer independently grant deservedness.
- Required candidate conditions now include:
  - `requires_ledger_review = true`
  - not treated as final answer
  - non-empty construction trace
  - `construction_trace_complete = true`
  - `construction_trace_source_grounded = true`
  - `train_evidence_grounded = true`
  - `forced_uniqueness_trace_present = true`
  - source train IDs or synthetic-local train IDs
  - train-grounded transformation rule
  - train-grounded forced constraints
  - ambiguity check
  - competing-output rejection reason
  - uniquely-forced reason
  - no unsupported assumptions
  - no unresolved rivals
  - no output-affecting ambiguity
  - no helper/rehearsal/MDL-only/scoring leakage evidence

## 4. Rival grammar uniqueness repair
- Rival-grammar cases now fail closed unless the candidate supplies:
  - explicit rival grammar set
  - surviving grammar
  - rival elimination trace
  - surviving-grammar train evidence
  - forced-uniqueness proof
- Missing rival proof now routes to unresolved-rival safe failure instead of candidate deservedness.

## 5. Construction trace enforcement
- Added explicit enforcement for:
  - `construction_trace_complete`
  - `construction_trace_source_grounded`
  - `forced_uniqueness_trace_present`
  - `rival_elimination_trace_present`
  - `train_evidence_grounded`
- Missing or incomplete trace evidence now rejects the candidate and drives task-level safe failure.

## 6. Ledger-review-required enforcement
- Candidates missing `requires_ledger_review` or setting it false can no longer become deserved.
- `ledger_review_required_count` now increments from candidate-level review state and is aggregated through replay metrics.

## 7. Safe-failure routing repair
- If no candidate deserves approval, the task now ends in `safe_failure_required`.
- Safe-failure submetrics now distinguish:
  - insufficient evidence
  - incomplete trace
  - unresolved rival
- Candidate rejection still counts, but it no longer erases task-level safe failure.

## 8. Metrics repair
- Added or repaired:
  - `ledger_review_required_count`
  - `construction_trace_complete_count`
  - `forced_uniqueness_trace_present_count`
  - `rival_elimination_trace_present_count`
  - `train_evidence_grounded_count`
  - `safe_failure_from_insufficient_evidence_count`
  - `safe_failure_from_incomplete_trace_count`
  - `safe_failure_from_unresolved_rival_count`
- Replay aggregation now carries these metrics forward per task and into replay totals.

## 9. Scoring-only boundary preservation
- The assembler now fail-closes if expected-answer or scoring-only fields appear in assembler input or candidate descriptors.
- Replay scoring still occurs only after ledger decision.
- No expected output, deserved-exact result, or post-ledger score is used in candidate deservedness.

## 10. Tests added/updated
- Updated assembler tests to cover all requested fail-closed conditions plus valid rival-grammar success.
- Updated replay tests to cover repaired metric wiring, safe-failure preservation, scoring boundary order, and emitter hard stop retention.

## 11. Safety boundaries
- Local-only repair.
- No replay run lane executed.
- No emitter build or implementation.
- No expected-answer leakage into candidate generation or ledger deservedness.
- No runtime wiring.
- No ChatResponder or protected-file edits.
- No `.weslr` writes.
- No external calls or public ARC/Kaggle usage.

## 12. Recommended next safe local follow-up
`RUN_ARC_GENERATIVE_BRIDGE_V5_REPLAY_AFTER_ASSEMBLER_REPAIR_V1`
