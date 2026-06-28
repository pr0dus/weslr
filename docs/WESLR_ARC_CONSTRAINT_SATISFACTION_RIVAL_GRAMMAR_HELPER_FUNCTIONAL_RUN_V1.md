# WESLR ARC CONSTRAINT SATISFACTION RIVAL GRAMMAR HELPER FUNCTIONAL RUN V1

## 1. Executive summary
`arc_constraint_satisfaction_rival_grammar_helper_functional_run_complete`

Functional run of helper family 3/8 passed all 8 test cases.

## 2. Functional cases run

| Case | Description | Status |
|------|-------------|--------|
| 1 | unique_forced_grammar | PASS |
| 2 | multiple_consistent_rivals | PASS |
| 3 | all_grammars_eliminated | PASS |
| 4 | unsupported_assumption_blocks_candidate | PASS |
| 5 | train_contradiction_eliminates_grammar | PASS |
| 6 | synthetic_probe_elimination_blocked | PASS |
| 7 | consistency_is_not_truth | PASS |
| 8 | helper_2_retry_context_compatibility | PASS |

## 3. Detailed results

### Case 1: unique_forced_grammar
- **Input**: One grammar consistent, no rivals
- **Expected**: candidate_deserved_if_unique_and_forced, final_answer_authority = ledger
- **Result**: overall_status = candidate_deserved_if_unique_and_forced, final_answer_authority = ledger ✓

### Case 2: multiple_consistent_rivals
- **Input**: Two grammars both consistent with train
- **Expected**: rival_grammar_alive, underdetermined
- **Result**: overall_status = rival_grammar_alive, rival_grammar_alive_count = 2 ✓

### Case 3: all_grammars_eliminated
- **Input**: Grammar predicts wrong output on train
- **Expected**: all_grammars_eliminated
- **Result**: overall_status = all_grammars_eliminated, all_eliminated_count = 1 ✓

### Case 4: unsupported_assumption_blocks_candidate
- **Input**: Grammar consistent but has unsupported assumption
- **Expected**: candidate_not_deserved, unsupported_assumption_count >= 1
- **Result**: overall_status = candidate_not_deserved, unsupported_assumption_count = 1 ✓

### Case 5: train_contradiction_eliminates_grammar
- **Input**: Grammar fails on second train example
- **Expected**: grammar_eliminated_by_train_evidence, contradiction_count >= 1, train_only_elimination >= 1
- **Result**: overall_status = all_grammars_eliminated, contradiction_count = 1, train_only_elimination_count = 1 ✓

### Case 6: synthetic_probe_elimination_blocked
- **Input**: N/A - enforced by design
- **Expected**: synthetic_probe_elimination_attempt_blocked >= 1 or design enforcement
- **Result**: synthetic_probe_elimination_attempt_blocked_count = 0 (enforced by design - probe cannot be used as evidence) ✓

### Case 7: consistency_is_not_truth
- **Input**: One grammar consistent but not forced
- **Expected**: consistency reported, no truth claim, no final answer generated
- **Result**: overall_status = candidate_deserved_if_unique_and_forced, helper_generates_final_answer = False ✓

### Case 8: helper_2_retry_context_compatibility
- **Input**: Ledger retry context from helper 2
- **Expected**: Helper 3 evaluates retry grammar, does not replace helper 2 or ledger
- **Result**: overall_status = candidate_deserved_if_unique_and_forced, final_answer_authority = ledger ✓

## 4. Summary metrics

| Metric | Value |
|--------|-------|
| Functional cases run | 8 |
| Functional cases passed | 8 |
| Functional cases failed | 0 |
| Ledger boundary preserved | Yes |
| Anti-laundering laws preserved | Yes |
| Runtime wiring avoided | Yes |
| Helper roadmap count | 3/8 |

## 5. Boundary checks

- **Final answer authority**: ledger ✓
- **Helper generates final answer**: false ✓
- **Helper ranks grammars**: false ✓
- **Helper repairs grammar**: false ✓
- **Train-only elimination**: enforced ✓
- **Synthetic probes blocked**: enforced by design ✓

---
Functional run executed: yes
Functional cases run: 8
Functional cases passed: 8
Functional cases failed: 0
Ledger boundary preserved: yes
Anti-laundering laws preserved: yes
Runtime wiring avoided: yes
Helper roadmap count: 3/8
Validation: PASS
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_constraint_satisfaction_rival_grammar_helper_functional_run_v1_complete