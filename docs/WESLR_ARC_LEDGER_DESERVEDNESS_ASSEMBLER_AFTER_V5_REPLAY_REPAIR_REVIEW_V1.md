# WESLR ARC LEDGER DESERVEDNESS ASSEMBLER AFTER V5 REPLAY REPAIR REVIEW V1

## 1. Executive verdict
`arc_ledger_deservedness_after_v5_replay_repair_review_needs_repair`

## 2. Review scope
- Reviewed only the repair artifact, diagnosis artifact, replay run artifact, repaired assembler module, repaired replay module, controlled generator module, and the targeted assembler/replay/generator tests.
- Did not rerun the replay lane.
- Did not modify runtime, emitter, protected files, or `.weslr`.

## 3. Candidate-level forced uniqueness review
- **Valid at assembler level:** the repaired assembler no longer grants deservedness from task-level `forced_constraints` alone.
- `evaluate_ledger_deservedness_v1()` now requires candidate-level conditions before deservedness: non-empty trace, trace completeness flag, source grounding flag, train grounding flag, forced-uniqueness flag, train IDs, train-grounded rule, train-grounded forced constraints, ambiguity check, competing-output rejection reason, and uniquely-forced reason.
- “Last surviving rival” without candidate-level proof cannot become deserved.
- **Finding:** this is correctly fail-closed inside the assembler.

## 4. Rival grammar uniqueness review
- **Valid at assembler level:** rival-grammar cases now require candidate-level rival set, surviving grammar, rival elimination trace, and surviving-grammar train evidence.
- Missing rival elimination proof or missing surviving grammar routes to candidate rejection plus task-level safe failure.
- This closes the exact diagnosis bug where empty rival fields still became deserved.

## 5. Construction trace enforcement review
- **Valid at assembler level:** candidates cannot become deserved if missing:
  - `construction_trace_complete`
  - `construction_trace_source_grounded`
  - `train_evidence_grounded`
  - `forced_uniqueness_trace_present`
  - source train IDs / synthetic-local train IDs
  - train-grounded forced constraints
  - ambiguity check
  - competing-output rejection reason
  - uniquely-forced reason
- Incomplete or missing trace now routes to safe failure rather than deservedness.

## 6. Ledger-review-required enforcement review
- **Valid:** missing `requires_ledger_review` rejects the candidate.
- **Valid:** `requires_ledger_review = false` rejects the candidate.
- **Valid:** `ledger_review_required_count` now increments from actual candidate-level `requires_ledger_review is True` during assembler evaluation and is propagated through replay aggregation.

## 7. Safe-failure routing review
- **Valid at assembler/replay routing level:** if no candidate deserves approval, task decision becomes `safe_failure_required`.
- Candidate rejection still counts separately.
- The new submetrics distinguish insufficient evidence, incomplete trace, and unresolved rival.
- This fixes the prior collapse where generated candidates could still leave safe failure at zero.
- **Note:** ambiguity, missing ledger-review flag, unsupported assumptions, and missing train-grounded constraints all currently funnel through the generic insufficient-evidence safe-failure bucket rather than their own dedicated safe-failure counters. That is acceptable for routing, but it is less granular than the narrative framing.

## 8. Expected-answer/scoring boundary review
- **Valid:** replay task definitions keep `synthetic_expected_answer_for_scoring_only` on the task object, outside assembler input.
- **Valid:** candidate generation happens before ledger assembly.
- **Valid:** ledger decision happens before scoring.
- **Valid:** the assembler fail-closes if scoring-only keys appear inside assembler input or candidate descriptors.
- **Valid:** expected answer does not influence candidate generation or deservedness in the reviewed path.
- **Valid with caution:** the fail-close check does not block replay scoring after ledger decision because scoring stays on the outer task object, not in assembler input.

## 9. Metrics wiring review
- **Valid:** these metrics are real counters, not constants, inside the repaired assembler and replay aggregation:
  - `ledger_review_required_count`
  - `construction_trace_complete_count`
  - `forced_uniqueness_trace_present_count`
  - `rival_elimination_trace_present_count`
  - `train_evidence_grounded_count`
  - `safe_failure_from_insufficient_evidence_count`
  - `safe_failure_from_incomplete_trace_count`
  - `safe_failure_from_unresolved_rival_count`
- **Important review finding:** the live controlled generator still does **not** emit the new candidate fields the assembler now requires (`construction_trace_complete`, `construction_trace_source_grounded`, `train_evidence_grounded`, `forced_uniqueness_trace_present`, train IDs, train-grounded forced constraints, etc.).
- Evidence from the current generator path:
  - generated candidates include a minimal `construction_trace`
  - but omit the new required completeness/grounding/uniqueness fields
  - therefore the repaired assembler will reject live generated candidates as incomplete/insufficient
- Result: the repair fixed the unsafe false-positive deservedness bug, but the current end-to-end generator → assembler path is now likely overcorrected into universal safe failure on replay.

## 10. Regression risk review
- **Regression risk found: yes.**
- The repair does **not** use expected answers to prevent deserved-but-wrong.
- The repair does **not** weaken emitter hard stops.
- The repair does **not** touch protected files.
- The repair does **not** write `.weslr`.
- **But:** with the current generator output shape, the repaired assembler likely makes live generated candidates impossible to deserve on the next replay run unless the generator (or a safe normalization layer) emits the newly-required candidate trace fields.
- This means the repair is safety-improving but not yet fully replay-ready.

## 11. Validation summary
- Reviewed targeted tests for assembler, replay, and controlled generator.
- Validation commands for this review lane passed.
- Protected files remained unchanged.
- `.weslr` remained untouched.

## 12. Recommended next safe local follow-up
`REPAIR_ARC_CONTROLLED_CANDIDATE_TRACE_GROUNDING_FOR_ASSEMBLER_V1`

Rationale:
- Keep the repaired assembler safety boundary.
- Narrowly repair the controlled generator (or a bounded replay-local normalization step) so live generated candidates carry the candidate-level trace completeness and grounding fields now required by the assembler.
- Only after that should the replay be rerun.
