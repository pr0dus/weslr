# WESLR ARC GENERATIVE BRIDGE V5 REPLAY EMITTER DECISION RULE ADDENDUM V1

## 1. Executive verdict
`arc_generative_bridge_v5_replay_emitter_decision_rule_ready`

## 2. Purpose

Lock a pre-registered decision rule for whether the V5 replay results justify designing a Safe Answer Emitter. This prevents post-hoc rationalization where any result is interpreted as "build emitter next" simply because emitter is the tempting path.

The rule must depend on **deserved, correct, safety-preserving bridge performance** — not merely candidate generation.

## 3. Post-Hoc Rationalization Risk

Without pre-registration, these failure modes become likely:

- Treating candidate generation as solving
- Treating deservedness as correctness without checking
- Building an emitter from one narrow task family
- Accepting exactness from undeserved candidates
- Accepting helper-output laundering
- Accepting collapse in safe-failure discipline
- Accepting final/public answer behavior
- Rationalizing weak results into emitter lane

**This addendum locks the decision rule BEFORE any replay results are read.**

## 4. Deserved Correctness Check

The old condition "candidate_deserved_count == deserved_exact_count" is structurally automatic. It must be clarified.

**Definition:**

For every candidate marked "candidate_deserved" by the ledger assembler:

1. The replay compares that candidate against the held-back synthetic expected answer **only after** the ledger decision
2. Then compute:

```
deserved_but_wrong_count = candidate_deserved_count - deserved_exact_count
```

Where:
- `candidate_deserved_count`: Every candidate approved by ledger assembler
- `deserved_exact_count`: Approved candidates that match held-back expected answer during local scoring
- `deserved_but_wrong_count`: Approved candidates that FAIL local expected-answer scoring

**Emitter gate requires:** `deserved_but_wrong_count == 0`

This prevents the gate from becoming automatically true by construction.

## 5. "Deserved_but_wrong_count" Metric

| Metric | Definition |
|--------|------------|
| `deserved_but_wrong_count` | Number of ledger-deserved candidates that fail local expected-answer scoring after ledger decision |

**Hard stop:** If `deserved_but_wrong_count > 0`, do not design emitter. Recommended lane: `REPAIR_ARC_LEDGER_DESERVEDNESS_ASSEMBLER_V1`.

A wrong deserved candidate means deservedness and correctness diverged — severe assembler/bridge safety issue.

## 6. Scoring Order

The scoring order must be explicit:

1. **Build task** — task_id, train_examples, test_input, expected_answer
2. **Generate candidate descriptor** — via ControlledCandidateGenerator
3. **Ledger assembler decides deservedness** — evaluate_ledger_deservedness_v1
4. **Only AFTER ledger decision**, compare ledger-deserved candidates to held-back local expected answer
5. **Record:**
   - `deserved_exact_count`
   - `deserved_but_wrong_count`
   - `undeserved_exact_count`
   - `overconfident_wrong_count`

**CRITICAL:** Expected answers may be used ONLY for local scoring after ledger decision. Expected answers must NEVER influence:
- Candidate generation
- Helper diagnostics
- Ledger deservedness decisions
- Safe failure decisions
- Repair hypotheses within the same evaluation pass

## 7. Hard Stop Conditions

Do NOT recommend emitter if any of these occur:

- `overconfident_wrong_count > 0`
- `undeserved_exact_count > 0`
- `deserved_but_wrong_count > 0`
- `helper_laundering_violation_count > 0`
- `final_answer_emitted_count > 0`
- `public_claim_allowed_count > 0`
- `helper_output_as_evidence_count > 0`
- Exact improvement came through undeserved candidates
- Safe failure collapsed below acceptable diagnostic floor
- Ledger authority not preserved
- Runtime wiring changed
- Public/official claim behavior appeared

## 8. Emitter Threshold

Emitter design is allowed ONLY if ALL are true:

| Condition | Threshold |
|-----------|------------|
| `deserved_exact_count` | ≥ 6 |
| `candidate_deserved_count` | ≥ 6 |
| `deserved_but_wrong_count` | == 0 |
| Deserved exacts occur in | ≥ 2 different task groups |
| `overconfident_wrong_count` | == 0 |
| `undeserved_exact_count` | == 0 |
| `helper_laundering_violation_count` | == 0 |
| `final_answer_emitted_count` | == 0 |
| `public_claim_allowed_count` | == 0 |
| `helper_output_as_evidence_count` | == 0 |
| Ledger authority | Preserved |
| Runtime behavior | Unchanged |
| No public ARC/Kaggle claims | True |

## 9. Why 6/48 is the Emitter Threshold

- 1-2 deserved exacts may be accidental or pattern-specific
- 6/48 (12.5%) is modest but enough to justify a narrow emitter-boundary design if safety is perfect
- At least 2 groups required to avoid building emitter for one narrow task family
- Threshold permits designing an emitter **boundary**, NOT implementing public-answer system
- Passing does NOT mean ARC success
- Passing does NOT authorize runtime wiring
- Passing does NOT authorize public claims
- Passing does NOT authorize internal 120

## 10. Fallback Interpretation Rules

After future replay, interpret as:

### A. `deserved_exact_count == 0`
- Recommended lane: `ANALYZE_ARC_GENERATIVE_BRIDGE_V5_REPLAY_RESULTS_V1` or `REPAIR_ARC_CONTROLLED_ANSWER_CANDIDATE_GENERATOR_V1`
- Interpretation: Bridge still does not produce deserved answers. Do NOT build emitter.

### B. 1 ≤ `deserved_exact_count` ≤ 5
- Recommended lane: `ANALYZE_ARC_GENERATIVE_BRIDGE_V5_REPLAY_RESULTS_V1`
- Interpretation: Bridge has signal but not enough breadth. Do NOT build emitter yet.

### C. Candidates generated but few/no candidates deserved
- Recommended lane: `REPAIR_ARC_LEDGER_DESERVEDNESS_ASSEMBLER_V1` or `REPAIR_ARC_CONTROLLED_ANSWER_CANDIDATE_GENERATOR_V1`
- Interpretation: Candidate generation or forced-constraint evidence is weak.

### D. Few candidates generated
- Recommended lane: `REPAIR_ARC_CONTROLLED_ANSWER_CANDIDATE_GENERATOR_V1`
- Interpretation: Generator is too weak.

### E. Any deserved candidate is wrong
- Recommended lane: `REPAIR_ARC_LEDGER_DESERVEDNESS_ASSEMBLER_V1`
- Interpretation: Assembler is unsafe.

### F. Any undeserved exact appears
- Recommended lane: `ANALYZE_ARC_GENERATIVE_BRIDGE_V5_REPLAY_RESULTS_V1` → likely repair
- Interpretation: Correctness without deservedness = laundering/guessing risk, NOT success.

### G. Deserved exacts in only one group
- Recommended lane: `ANALYZE_ARC_GENERATIVE_BRIDGE_V5_REPLAY_RESULTS_V1`
- Interpretation: Pattern-specific success. No emitter yet.

## 11. MDL Generator-Health Yellow Flag

**Qualitative diagnostic:** `mdl_only_rejected_count`

**Derived flag:** `generator_health_warning = True` if `mdl_only_rejected_count` is high relative to attempted tasks or candidate generation attempts.

**Interpretation:**
- MDL-only rejection is NOT an automatic emitter hard stop if main safety gate passes
- Rejecting MDL-only candidates means the assembler is doing its job
- But HIGH MDL-only rejection means the generator may be overproducing weak/elegance-driven candidates
- If emitter gate passes BUT `generator_health_warning == True`, recommended next may be:
  - `DESIGN_ARC_SAFE_ANSWER_EMITTER_BOUNDARY_V1` PLUS `ANALYZE_ARC_CONTROLLED_GENERATOR_HEALTH_V1`
- Do NOT blindly proceed to emitter implementation.

## 12. Allowed Next-Lane Recommendations

After future replay, allowed recommendations are:

| Lane | When Allowed |
|------|---------------|
| `DESIGN_ARC_SAFE_ANSWER_EMITTER_BOUNDARY_V1` | Only if emitter gate passes fully |
| `ANALYZE_ARC_GENERATIVE_BRIDGE_V5_REPLAY_RESULTS_V1` | When results are mixed, below threshold, or need diagnosis |
| `REPAIR_ARC_CONTROLLED_ANSWER_CANDIDATE_GENERATOR_V1` | When generation is weak, coverage too low, or generator-health warnings dominate |
| `REPAIR_ARC_LEDGER_DESERVEDNESS_ASSEMBLER_V1` | When deservedness decisions unsafe, too weak, or wrong |
| `BLOCKED_PENDING_OWNER_DECISION` | If safety violation occurs |

## 13. Safety Boundaries

| Boundary | Status |
|----------|--------|
| Local only | Required |
| No public ARC data | Required |
| No hidden test output | Required |
| No synthetic answer leakage into generation | Required |
| No runtime wiring | Required |
| No emitter implementation yet | Required |
| No public claims | Required |
| No ".weslr" | Required |

---

Emitter decision rule pre-registered: yes
Deserved correctness check clarified: yes
Deserved_but_wrong_count metric added: yes
Scoring order clarified: yes
Hard stops preserved: yes
Emitter threshold preserved: yes
Fallback lanes defined: yes
MDL generator-health yellow flag added: yes
Post-hoc rationalization blocked: yes
Recommended next lane: IMPLEMENT_ARC_GENERATIVE_BRIDGE_V5_REPLAY_V1
Validation: PASS
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_generative_bridge_v5_replay_emitter_decision_rule_ready