# WESLR ARC LEDGER GUIDED MICRO-THEORY RETRY LOOP DESIGN V1

## 1. Executive verdict
`arc_ledger_guided_micro_theory_retry_loop_design_ready`

## 2. V4 frontier context

The V4 adversarial run exposed a critical gap:
- **Primary frontier**: `rival_grammar_ledger_deservedness`
- **Key insight**: The ledger correctly rejects ambiguous grammars but provides no actionable feedback for retry
- **Problem**: When the ledger says "rejected," Micro-Theory has no constraint to guide a second attempt

The ledger works as a gatekeeper but not as part of a reasoning loop. This design turns the ledger into a bounded reasoning partner.

## 3. Loop definition

### Two-Round Bounded Retry

**Round 1**:
1. Micro-Theory generates candidate grammar A from train evidence
2. Ledger evaluates A
3. If deserved → answer
4. If rejected → emit structured rejection reason

**Round 2**:
1. Micro-Theory receives rejection reason as constraint (NOT evidence)
2. Micro-Theory generates candidate grammar B or revised grammar A2
3. Ledger evaluates again
4. If deserved → answer
5. If still rejected → abstain / unsupported / underdetermined

**Key constraint**: The rejection reason is a constraint, not evidence. It tells Micro-Theory WHAT to avoid, not WHAT to believe.

## 4. Structured ledger rejection reasons

| Reason Code | Human-Readable | Affected | Rival | Retry Allowed | Retry Constraint |
|-------------|----------------|----------|-------|---------------|------------------|
| target_uncertain | Target selection not forced by train | candidate A | yes | yes | "Generate theory that proves target from train" |
| action_uncertain | Action not forced by train | candidate A | yes | yes | "Generate theory that resolves action ambiguity" |
| representation_uncertain | Representation shift not forced by train | candidate A | no | yes | "Generate theory that avoids representation shift" |
| rival_grammar_alive | Multiple grammars fit train equally | candidate A | yes | yes | "Generate theory that resolves Rival B or proves underdetermination" |
| train_evidence_underdetermined | Train evidence doesn't determine test | candidate A | yes | yes | "Generate theory that declares underdetermination if no resolution" |
| beautiful_wrong_rule_not_eliminated | Tempting wrong rule not eliminated | candidate A | yes | yes | "Generate theory that proves beautiful wrong is eliminated by train" |
| probe_divergence_detected | Probe exposed divergence | candidate A | yes | no | (final abstention required) |
| negative_evidence_not_accounted | Negative evidence not explained | candidate A | no | yes | "Generate theory that accounts for negative evidence" |
| helper_trap_detected | Helper eligibility trap present | candidate A | yes | no | (final abstention required) |
| unsafe_hidden_assumption | Hidden assumption not forced by train | candidate A | yes | no | (final abstention required) |
| coincidence_risk | Output pattern may be coincidence | candidate A | no | yes | "Generate theory that proves output is forced, not coincidental" |
| insufficient_forced_output | Output not forced by train | candidate A | no | yes | "Generate theory that proves output is necessary, not optional" |

## 5. Allowed retry constraints

**Allowed** (constraint language):
- "Generate a theory that explicitly proves target selection from train evidence."
- "Generate a theory that resolves or preserves Rival Grammar B."
- "Generate a theory that accounts for negative evidence / absence."
- "Generate a theory that explains why beautiful wrong rule is eliminated by train evidence."
- "Generate a theory that avoids unsupported representation shift."
- "Generate a theory that declares underdetermination if no train-only resolution exists."
- "Generate a theory where output pattern is forced, not coincidental."

## 6. Forbidden retry behavior

**Forbidden**:
- "Choose the rival because the first grammar failed." (post-hoc justification)
- "Use probe success as evidence." (synthetic → evidence laundering)
- "Patch grammar using synthetic probe result." (probe result becomes authority)
- "Retry until any grammar passes." (unbounded search)
- "Prefer the theory with higher apparent score." (score = evidence)
- "Use hidden test output." (leakage)
- "Use helper output as confidence." (helper → authority)
- "Accumulate confidence across retries." (confidence inflation)

## 7. Retry budget and termination

### Retry Budget (V1)
- **max_retry_rounds = 1**
- Default: 1 retry after initial ledger rejection
- No unbounded retry
- No stochastic repeated guessing
- No mutation loop

### Termination States
- `answer_deserved` — Final ledger says deserved
- `unsupported` — No theory is forced by train evidence
- `underdetermined` — Train evidence genuinely underdetermines test
- `unsafe` — Hidden assumptions detected
- `rival_grammars_remain` — Multiple grammars remain after retry
- `retry_budget_exhausted` — Used all retries without deserved answer

**Critical**: No answer may be emitted unless the final ledger pass says `deserved`.

## 8. Anti-laundering laws

1. **Ledger rejection reason is NOT new evidence** — It's a constraint, not a fact about the world
2. **Shadow probe result is NOT train evidence** — Probe success doesn't count for grammar selection
3. **Retry success does NOT prove truth** — Unless train evidence forces the answer
4. **Repeated retries do NOT accumulate confidence** — Each retry is independent
5. **A rival grammar can only be eliminated by train evidence** — Not by retry aesthetics
6. **No in-task repair becomes permanent solver change** — Retry is test-time only
7. **Final answer ALWAYS requires ledger deservedness** — No bypass

## 9. Metrics design

Future implementation metrics:

| Metric | Description |
|--------|-------------|
| initial_candidate_count | Candidates generated in round 1 |
| ledger_rejection_count | Rejections in round 1 |
| retry_attempt_count | Retry attempts in round 2 |
| retry_success_count | Retry that achieved deserved |
| retry_abstain_count | Retry that led to abstain |
| retry_unsafe_count | Retry detected as unsafe |
| rival_grammar_preserved_count | Rival survived retry |
| rival_grammar_legally_eliminated_count | Rival eliminated by train evidence |
| overconfident_wrong_before_retry | Wrong answers in round 1 |
| overconfident_wrong_after_retry | Wrong answers after retry |
| safe_unsupported_preserved_count | Correct unsupported preserved |
| answer_deserved_after_retry_count | Deserved answers after retry |
| rejection_reason_distribution | Counts by reason code |
| retry_constraint_distribution | Counts by constraint type |
| retry_budget_exhausted_count | Runs that used all retries |

## 10. Pass/fail criteria

### Pass Criteria
- [ ] Ledger gives structured rejection reason
- [ ] Rejection reason becomes constraint only (not evidence)
- [ ] Micro-Theory can retry once under constraint
- [ ] Final answer still requires ledger deservedness
- [ ] Unresolved rivalry still blocks answer
- [ ] Safe failure remains available
- [ ] No synthetic/probe evidence becomes authority

### Fail Criteria
- [ ] Retry reason becomes evidence
- [ ] Retry crowns a rival without train proof
- [ ] Retry success accumulates confidence
- [ ] Loop becomes unbounded
- [ ] Solver patches itself
- [ ] Final answer bypasses ledger

## 11. Relation to auto-improvement / auto-promotion

**This is NOT auto-merge. This is NOT autonomous solver modification.**

- This design is test-time reasoning retry only
- No retry results become permanent solver changes
- No retry success promotes a grammar to default

**Future auto-promotion design** (separate from this lane):
- Mathematical gates for promotion
- Holdout variant validation
- Regression gates
- Overconfident-wrong gates
- Safe-unsupported preservation requirements
- Quarantine for failed promotions
- Rollback capability

## 12. Recommended next safe local follow-up
`REVIEW_ARC_LEDGER_GUIDED_MICRO_THEORY_RETRY_LOOP_DESIGN_V1`

Rationale:
- Design is bounded: 1 retry only
- Rejection reason is constraint, not evidence
- Ledger gate is preserved: final answer requires deservedness
- Anti-laundering laws prevent evidence laundering
- Safe failure remains available
- Not auto-merge: test-time only
- Metrics design is comprehensive

---
V4 frontier referenced: yes
Ledger rejection reasons defined: yes (12 reason codes)
Retry constraints defined: yes
Rejection reason treated as constraint not evidence: yes
Retry budget defined: yes (1 round)
Final ledger gate preserved: yes
Anti-laundering laws included: yes (7 laws)
Auto-improvement separated: yes
Validation: PASS
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_ledger_guided_micro_theory_retry_loop_design_ready