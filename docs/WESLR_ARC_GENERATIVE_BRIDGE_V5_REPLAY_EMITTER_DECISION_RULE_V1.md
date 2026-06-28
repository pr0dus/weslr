# WESLR ARC GENERATIVE BRIDGE V5 REPLAY EMITTER DECISION RULE V1

## 1. Executive verdict
`arc_generative_bridge_v5_replay_emitter_decision_rule_ready`

## 2. Purpose

Pre-register the decision rule for whether the V5 replay results justify designing a Safe Answer Emitter. This prevents post-hoc rationalization where any result becomes "build emitter next."

## 3. Why the Gate Exists

The V5 replay run is effectively the dataset that decides whether WESLR should design a Safe Answer Emitter next. Therefore, the emitter decision must be pre-registered before results are read.

The rule must prevent:
- Treating candidate generation as solving
- Treating deservedness as correctness without checking it
- Building an emitter from one narrow task family
- Accepting exactness from undeserved candidates
- Accepting helper-output laundering
- Accepting safe-failure discipline collapse
- Accepting public/final answer behavior
- Rationalizing weak results into emitter lane

## 4. Deserved Correctness Check

For every candidate marked "candidate_deserved" by the ledger assembler:

1. Compare to held-back synthetic expected answer **only after** the ledger decision
2. Compute:

```
deserved_but_wrong_count = candidate_deserved_count - deserved_exact_count
```

Where:
- `candidate_deserved_count`: Every candidate approved by ledger assembler
- `deserved_exact_count`: Approved candidates matching held-back expected answer
- `deserved_but_wrong_count`: Approved candidates that FAIL local scoring

**Emitter gate requires:** `deserved_but_wrong_count == 0`

This must be computed over the full deserved set, not a subset pinned to match by construction.

## 5. Scoring Order

1. **Build task** — task_id, train_examples, test_input, expected_answer
2. **Generate candidate descriptor** — via ControlledCandidateGenerator
3. **Ledger assembler decides deservedness** — evaluate_ledger_deservedness_v1
4. **Only AFTER ledger decision**, compare to held-back expected answer
5. **Record:** deserved_exact_count, deserved_but_wrong_count, undeserved_exact_count, overconfident_wrong_count

Expected answers used ONLY for local scoring after ledger decision. NEVER influence:
- Helper diagnostics
- Candidate generation
- Ledger deservedness
- Safe failure decisions

## 6. Hard-Stop Conditions

Do NOT recommend emitter if any occur:
- `overconfident_wrong_count > 0`
- `undeserved_exact_count > 0`
- `deserved_but_wrong_count > 0`
- `helper_laundering_violation_count > 0`
- `final_answer_emitted_count > 0`
- `public_claim_allowed_count > 0`
- `helper_output_as_evidence_count > 0`
- Exact improvement through undeserved candidates
- Safe failure collapsed below diagnostic floor
- Ledger authority not preserved
- Runtime wiring changed
- Public/official claim appeared

## 7. Emitter Threshold

Emitter design allowed ONLY if ALL true:
- `deserved_exact_count >= 6`
- `candidate_deserved_count >= 6`
- `deserved_but_wrong_count == 0`
- Deserved exacts in ≥ 2 task groups
- `overconfident_wrong_count == 0`
- `undeserved_exact_count == 0`
- All safety counts = 0

## 8. Why 6/48 Threshold

- 1-2 deserved exacts may be accidental or pattern-specific
- 6/48 (12.5%) is modest but enough for narrow emitter-boundary design if safety is perfect
- ≥2 groups required to avoid single-family emitter
- Threshold permits designing emitter **boundary**, NOT public-answer system
- Passing does NOT mean ARC success
- Passing does NOT authorize runtime wiring
- Passing does NOT authorize public claims

## 9. Fallback Interpretation

| Result | Lane | Interpretation |
|--------|------|-----------------|
| deserved_exact_count == 0 | ANALYZE or REPAIR_GENERATOR | No deserved answers |
| 1-5 deserved_exact | ANALYZE | Signal but not enough breadth |
| Any deserved wrong | REPAIR_ASSEMBLER | Assembler unsafe |
| Any undeserved exact | ANALYZE | Laundering/guessing risk |
| Only one group | ANALYZE | Pattern-specific |

---

Emitter decision rule locked: yes
Deserved-because-wrong metric defined: yes
Scoring order enforced: yes
Hard stops preserved: yes
Emitter threshold preserved: yes
Validation: PASS
Final judgment: arc_generative_bridge_v5_replay_emitter_decision_rule_ready