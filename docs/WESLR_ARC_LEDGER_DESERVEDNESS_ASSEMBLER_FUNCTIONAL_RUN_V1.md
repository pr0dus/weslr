# WESLR ARC LEDGER DESERVEDNESS ASSEMBLER FUNCTIONAL RUN V1

## 1. Executive verdict
`arc_ledger_deservedness_assembler_functional_run_complete`

## 2. Functional cases run

| # | Case | Result |
|---|------|--------|
| 1 | no_candidates_needs_candidate_generation | PASS |
| 2 | train_forced_unique_candidate_deserved | PASS |
| 3 | unsupported_assumptions_rejected | PASS |
| 4 | unresolved_rivals_block_deservedness | PASS |
| 5 | hidden_test_output_blocks | PASS |
| 6 | public_arc_answer_blocks | PASS |
| 7 | candidate_bypassing_ledger_rejected | PASS |
| 8 | candidate_treated_as_final_answer_rejected | PASS |
| 9 | partial_candidate_not_complete_deserved | PASS |
| 10 | insufficient_train_evidence_safe_failure | PASS |
| 11 | rehearsal_only_support_rejected | PASS |
| 12 | ledger_boundary_preserved | PASS |

**Functional cases run: 12**
**Functional cases passed: 12**
**Functional cases failed: 0**

## 3. Metrics summary

| Metric | Value |
|--------|-------|
| candidate_review_count | 8 |
| candidate_deserved_count | 1 |
| candidate_not_deserved_count | 7 |
| safe_failure_required_count | 2 |
| needs_candidate_generation_count | 1 |
| rival_unresolved_count | 2 |
| forced_unique_output_count | 1 |
| insufficient_train_evidence_count | 2 |
| unsupported_assumption_rejected_count | 1 |
| mdl_only_rejected_count | 0 |
| rehearsal_only_rejected_count | 1 |
| hidden_test_blocked_count | 1 |
| public_arc_answer_blocked_count | 1 |
| helper_output_as_evidence_blocked_count | 1 |
| final_answer_emitted_count | 0 |
| public_claim_allowed_count | 0 |

## 4. Safety verification

| Check | Result |
|-------|--------|
| Train-forced deservedness works | YES ✓ |
| Unsupported candidates rejected | YES ✓ |
| Unresolved rivals block deservedness | YES ✓ |
| Ambiguity safe-fails | YES ✓ |
| No final answers emitted | YES ✓ |
| No public claims allowed | YES ✓ |
| Helper output not treated as evidence | YES ✓ |
| Rehearsal repeat rejected | YES ✓ |
| Runtime behavior unchanged | YES ✓ |

## 5. Ledger boundary verification

| Boundary | Value | Status |
|----------|-------|--------|
| final_answer_emitted | False | ✓ |
| public_claim_allowed | False | ✓ |
| official_arc_claim_allowed | False | ✓ |
| runtime_wiring_changed | False | ✓ |
| helper_output_as_evidence | False | ✓ |
| ledger_decision_only | True | ✓ |

---

Functional run complete: yes
Functional cases passed: 12/12
Train-forced deservedness works: yes
Unsupported candidates rejected: yes
Unresolved rivals block deservedness: yes
Ambiguity safe-fails: yes
No final answers emitted: yes
No public claims allowed: yes
Runtime behavior unchanged: yes
Validation: PASS
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_ledger_deservedness_assembler_functional_run_complete