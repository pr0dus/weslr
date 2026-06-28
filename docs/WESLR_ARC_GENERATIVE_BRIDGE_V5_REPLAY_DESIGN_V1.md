# WESLR ARC GENERATIVE BRIDGE V5 REPLAY DESIGN V1

## 1. Executive verdict
`arc_generative_bridge_v5_replay_design_ready`

## 2. Purpose

Measure whether the complete bridge stack (`helper diagnostics → controlled candidate generation → ledger deservedness assembly`) produces deserved candidate answers instead of only safe failures.

The V5 diagnostic showed:
- 0 exact (diagnostic-only mode)
- 24 safe failures (50%)
- 0 overconfident wrong
- 0 deserved answers

The question: With the generative bridge, does the picture change?

## 3. V5 Baseline Comparison

| Metric | V5 Diagnostic | V5 Replay Target |
|--------|---------------|------------------|
| attempted_tasks | 48 | 48 |
| task_exact_count | 0 | ? |
| task_exact_rate | 0.0 | ? |
| safe_failure_count | 24 | ? |
| overconfident_wrong_count | 0 | 0 (must stay) |
| candidate_deserved_count | 0 | ? |
| undeserved_exact_count | 0 | ? |

## 4. Replay Pipeline Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        REPLAY PIPELINE                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  A. Build task (task_id, train_examples, test_input, expected_answer)  │
│  B. Read helper diagnostics from helpers 1-8                           │
│  C. Generate candidate descriptors via ControlledCandidateGenerator    │
│  D. Send candidates to LedgerDeservednessAssembler                    │
│  E. Record ledger decision                                            │
│  F. Compare to expected (LOCAL SCORING ONLY, AFTER decision)          │
│  G. Record whether exact was deserved or not deserved                │
│  H. Preserve safe failure if no deserved candidate                    │
└─────────────────────────────────────────────────────────────────────────┘
```

**Critical: Expected answers are used ONLY for local scoring AFTER the ledger decision. They must NOT influence candidate generation.**

## 5. Candidate Generation Policy

For each task, record:

| Field | Description |
|-------|-------------|
| candidate_generation_attempted | Boolean |
| candidate_generated_count | Integer |
| candidate_generation_blocked_count | Integer |
| candidate_generation_block_reason | String (if blocked) |
| construction_mode | String (which mode) |
| construction_trace_complete | Boolean |
| candidate_requires_ledger_review | Boolean (must be True) |
| candidate_treated_as_final_answer | Boolean (must be False) |

## 6. Ledger Deservedness Policy

For each generated candidate, record:

| Field | Description |
|-------|-------------|
| ledger_decision | candidate_deserved / candidate_not_deserved / safe_failure_required |
| candidate_deserved | Boolean |
| candidate_not_deserved | Boolean |
| safe_failure_required | Boolean |
| needs_candidate_generation | Boolean |
| rival_grammar_unresolved | Boolean |
| forced_unique_output_available | Boolean |
| insufficient_train_evidence | Boolean |
| deservedness_trace_complete | Boolean |

## 7. Scoring Policy

| Metric | Description |
|--------|-------------|
| attempted_tasks | Total tasks attempted |
| candidate_generated_tasks | Tasks where candidates were generated |
| candidate_deserved_tasks | Tasks with at least one deserved candidate |
| task_exact_count | Exact matches (deserved AND correct) |
| task_exact_rate | task_exact_count / attempted_tasks |
| deserved_exact_count | Exact matches that were deserved |
| undeserved_exact_count | Exact matches that were NOT deserved (laundering risk!) |
| safe_failure_count | Tasks with safe_failure_required |
| overconfident_wrong_count | Wrong but confident (deserved AND wrong) |
| candidate_not_deserved_count | Candidates rejected |
| candidate_blocked_count | Candidates blocked |
| helper_laundering_violation_count | Cases where helper output became evidence |
| final_answer_emitted_count | Must remain 0 |
| public_claim_allowed_count | Must remain 0 |

**Scoring Rules:**
- Exact only counts if candidate is ledger-deserved
- A correct but not-deserved candidate = "undeserved_exact_count" (NOT success, laundering risk)
- A wrong but deserved candidate = "overconfident_wrong_count" (serious failure)
- If no candidate deserves, safe failure is valid

## 8. Group-Level Analysis Model

For each of the 8 groups:

| Group | Metrics |
|-------|---------|
| v4_rival_grammar_replay_6 | candidates_generated, deserved, exact_deserved, safe_failures, rival_unresolved |
| v4_beautiful_wrong_rule_replay_6 | candidates_generated, deserved, exact_deserved, blocked_beautiful |
| v4_composed_transform_replay_6 | candidates_generated, deserved, exact_deserved, safe_failures |
| v4_negative_evidence_replay_6 | candidates_generated, deserved, exact_deserved, safe_failures |
| v4_helper_trap_replay_6 | candidates_generated, deserved, exact_deserved, blocked_traps |
| object_graph_correspondence_6 | candidates_generated, deserved, exact_deserved, ambiguity_safe_failures |
| invariant_symmetry_ambiguity_6 | candidates_generated, deserved, exact_deserved, ambiguity_safe_failures |
| mdl_simplicity_trap_6 | candidates_generated, deserved, exact_deserved, mdl_rejected |

For each group, identify:
- dominant_success_reason: What bridge component worked
- dominant_failure_reason: What bridge component failed
- missing_bridge: What's still needed

## 9. Interpretation Policy

### Good Outcomes (Bridge Improved Discipline + Solving)
- task_exact_rate becomes nonzero through deserved candidates
- deserved_exact_count increases
- overconfident_wrong remains 0
- safe_failure preserved (>20%)
- helper traps remain blocked
- beautiful wrong rules remain blocked
- MDL-only candidates rejected
- unresolved rivals still block
- no final answers emitted
- no public claims

### Bad Outcomes (Laundering or Guessing)
- exact rate improves through undeserved candidates (undeserved_exact_count > 0)
- candidate generation bypasses ledger
- helper output becomes evidence
- safe_failure collapses (<10%)
- overconfident_wrong increases
- MDL/elegance creates deservedness
- public/final answer emitted

### Neutral/Caution
- exact rate unchanged (0) = bridge exists but tasks still fail
- only safe failures = no candidates deserved
- high undeserved_exact = candidate laundering risk

## 10. Rehearsal-Learning Recorder Hook

Record shape (not persistence):

```python
{
    "task_family": str,
    "variant_id": str,
    "failure_reason": str,  # "no_candidates", "no_deserved", "ambiguous", etc.
    "missing_constraint": str | None,
    "missing_candidate_mode": str | None,
    "missing_deservedness_reason": str,  # "unresolved_rivals", "insufficient_evidence", etc.
    "repair_hypothesis": str | None,
    "memorization_risk": "none" | "low" | "medium" | "high",
    "fresh_holdout_required": bool,
}
```

Do NOT write ".weslr". Do NOT persist. Do NOT mutate solver.

## 11. Safety Boundaries

| Boundary | Status |
|----------|--------|
| Local only | Required |
| No public ARC data | Required |
| No hidden test output | Required |
| No synthetic answer leakage into generation | Required |
| No runtime wiring | Required |
| No ChatResponder changes | Required |
| No final answer emission | Required |
| No public claims | Required |
| No ".weslr" | Required |

## 12. Metrics Summary

### Task Metrics (10)
- attempted_tasks
- candidate_generated_tasks
- candidate_deserved_tasks
- task_exact_count
- task_exact_rate
- deserved_exact_count
- undeserved_exact_count
- safe_failure_count
- overconfident_wrong_count

### Generation Metrics (8)
- candidate_generation_attempt_count
- candidate_generated_count
- candidate_generation_blocked_count
- construction_mode_X_count (7 modes)
- construction_trace_complete_count

### Ledger Metrics (12)
- ledger_review_required_count
- candidate_deserved_count
- candidate_not_deserved_count
- safe_failure_required_count
- needs_candidate_generation_count
- rival_unresolved_count
- forced_unique_output_count
- insufficient_train_evidence_count
- unsupported_assumption_rejected_count
- mdl_only_rejected_count
- rehearsal_only_rejected_count
- final_answer_emitted_count (must be 0)

### Safety Metrics (6)
- helper_output_as_evidence_count
- hidden_test_blocked_count
- public_arc_answer_blocked_count
- final_answer_emitted_count
- public_claim_allowed_count
- helper_laundering_violation_count

## 13. Recommended Next Safe Local Follow-up

**`IMPLEMENT_ARC_GENERATIVE_BRIDGE_V5_REPLAY_V1`**

Rationale:
- Design is clean and complete
- All safety boundaries defined
- Scoring policy distinguishes deserved vs undeserved
- Bridge stack is implemented and tested

---

V5 baseline comparison included: yes
Replay pipeline model defined: yes
Candidate generation policy defined: yes
Ledger deservedness policy defined: yes
Scoring policy defined: yes
Group-level analysis model defined: yes
Rehearsal-learning recorder hook defined: yes
Safety boundaries preserved: yes
Recommended next lane: IMPLEMENT_ARC_GENERATIVE_BRIDGE_V5_REPLAY_V1
Validation: PASS
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_generative_bridge_v5_replay_design_ready