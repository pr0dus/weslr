# WESLR ARC RIVAL GRAMMAR FALSE UNIQUENESS AFTER TRACE GROUNDING REPAIR REVIEW V1

## 1. Executive verdict
`arc_rival_grammar_false_uniqueness_after_trace_grounding_repair_review_valid_with_notes`

## 2. Review scope
- Reviewed only the repair report, pre-rerun verification report, repaired generator / assembler / replay modules, and the targeted generator / assembler / replay tests.
- Re-ran only targeted local checks and requested validations.
- Did **not** run the full V5 replay.
- Did **not** modify runtime, emitter, protected files, or `.weslr`.

## 3. Rival-context detection review
### Valid findings
- Rival context is detected from real local task / candidate state, not from expected answers.
- Generator detection uses:
  - `task_id` / `group_id` containing `rival_grammar`
  - `expected_frontier_failure` containing `rival_grammar`
  - explicit rival-context hints
  - rival grammar fields
  - unresolved rival fields
  - competing grammar markers
  - multiple-plausible-transformation markers
  - incomplete rival-proof field families
- Assembler re-detects rival context independently from candidate flags using task-level and candidate-level state, so a missing generator flag does not bypass enforcement.
- Targeted local check confirmed that a candidate with `rival_context_detected = false` is still rejected when the task metadata marks the known rival replay family.

### Review note
- The generator currently treats any forced constraint containing the substring `grammar` or `rival` as rival context.
- This is conservative and safe for the local synthetic review lane, but it is broader than the specific `v4_rival_grammar_replay_6` family.
- In targeted local sanity checks, an otherwise ordinary train-forced case with a forced constraint like `grammar_consistent` was marked rival-context only because of that text match.
- This does **not** create expected-answer leakage or runtime behavior, but it is a potential overblocking heuristic and should be narrowed later if broader local diagnostic families start using grammar-shaped wording without real rival discrimination.

## 4. No construction-mode bypass review
- **Valid.**
- The repaired generator truthfully downgrades rival-context train-forced candidates lacking rival proof:
  - `construction_trace_complete` no longer stays true
  - `forced_uniqueness_trace_present` no longer stays true
  - `ambiguity_check` becomes unresolved
  - unresolved rival state is preserved
- The assembler also enforces rival-proof requirements regardless of construction mode.
- This closes the prior train-forced bypass and also preserves the explicit-grammar rival-proof requirement.
- No evidence was found that another existing candidate mode can still claim uniqueness while rival context remains unresolved.

## 5. Candidate trace truthfulness review
- **Valid.**
- In rival context, train-grounded constraints are now necessary but not sufficient.
- Missing rival proof correctly prevents a candidate from remaining complete.
- Missing rival proof also prevents a candidate from remaining uniquely forced.
- Missing rival proof is recorded in `missing_required_trace_fields`.
- Unresolved rival state is preserved through `unresolved_rivals` rather than hidden.
- Targeted inspection of the repaired train-forced rival path confirmed that unique-force text is cleared instead of being left behind as misleading residue.

## 6. Assembler enforcement review
- **Valid.**
- The assembler independently re-detects rival context from:
  - task metadata
  - candidate rival fields
  - unresolved rival state
  - rival-context hint state
- It rejects rival-context candidates missing any of the required rival-proof fields:
  - rival grammar set
  - surviving grammar
  - rival elimination trace
  - surviving-grammar train evidence
  - rival outputs considered
  - rejected rival reasons
  - proof that the surviving grammar uniquely forces output
- Rejection routes to `safe_failure_required` through `unresolved_rivals`, not to a plain non-safe rejection.
- Targeted local check confirmed that assembler re-detection still blocks a candidate even when the generator-supplied rival flag is manually absent.

## 7. Known-bad six task ID review
- **Valid.**
- Targeted local review of the six stable known-bad ids confirmed:
  - none become `candidate_deserved`
  - all six safe-fail
  - all six increment unresolved-rival safe-failure metrics
  - no expected-answer field is used to make the rejection decision
- This is an intentionally conservative safety outcome.
- The review accepts that previously exact cases in this six-id family may now safe-fail until genuine rival proof exists.

## 8. Safe-failure routing review
- **Valid.**
- Safe-failure routing remains preserved for:
  - insufficient evidence
  - incomplete trace
  - unresolved rival
  - missing rival proof in rival context
- Targeted local checks confirmed the repaired rival case now contributes to task-level `safe_failure_required` instead of collapsing into a plain `candidate_not_deserved` outcome.

## 9. Metrics review
- **Valid with one note.**
- The reviewed counters are live and state-driven, not constants:
  - `rival_context_detected_count`
  - `rival_context_missing_proof_count`
  - `rival_context_safe_failure_count`
  - `train_forced_rival_bypass_blocked_count`
- Targeted checks showed:
  - known-bad six aggregate -> all four counters increment to 6 where expected
  - ordinary non-rival train-forced case -> rival-context counters stay at 0
- Review note:
  - because forced-constraint substring matching can mark some ordinary grammar-worded cases as rival context, the counters may overcount conservative rival detections in future local diagnostics unless that heuristic is narrowed.

## 10. Expected-answer boundary review
- **Valid.**
- No expected/scoring field is used in:
  - candidate generation
  - trace grounding
  - rival proof
  - forced uniqueness
  - assembler deservedness
- The generator/replay ordering remains:
  - candidate generation first
  - ledger evaluation second
  - scoring-only use after ledger decision
- Forbidden scoring keys remain fail-closed at assembler level.

## 11. Regression risk review
### Confirmed not regressed
- Non-rival train-forced candidates can still remain complete and deserved when train-grounded evidence is sufficient.
- Assembler safety was not weakened.
- Emitter hard-stop behavior was not weakened in the targeted replay tests.
- Protected files were untouched.
- `.weslr` was untouched.

### Review note / residual risk
- A conservative overblocking risk exists in generator rival-context detection because of broad forced-constraint substring matching on `grammar` / `rival`.
- In this review, that did not break the requested safety objective and did not affect the known-bad family incorrectly.
- I do **not** consider this a blocker for the current repair review, but it is a real note for future narrowing if broader local diagnostic traffic starts using grammar-worded constraints without true rival discrimination.

## 12. Validation summary
- Targeted review checks confirmed:
  - known-bad six all safe-fail
  - ordinary non-rival train-forced candidate still passes
  - assembler re-detects rival context without trusting generator flag
  - forced-constraint string matching is conservative and somewhat broad
- Requested validations passed:
  - generator tests
  - assembler tests
  - replay tests
  - release gate
  - `git diff --check`
  - release check script
  - source-repo health check script

## 13. Recommended next safe local follow-up
`RUN_ARC_GENERATIVE_BRIDGE_V5_REPLAY_AFTER_RIVAL_FALSE_UNIQUENESS_REPAIR_V1`
