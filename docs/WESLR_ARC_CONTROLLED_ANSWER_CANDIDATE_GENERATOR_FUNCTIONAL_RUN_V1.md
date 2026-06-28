# WESLR ARC CONTROLLED ANSWER CANDIDATE GENERATOR FUNCTIONAL RUN V1

## 1. Executive verdict
`arc_controlled_answer_candidate_generator_functional_run_complete`

## 2. Functional cases run

| # | Case | Result |
|---|------|--------|
| 1 | relation_first_rewrite_candidate_generated | PASS |
| 2 | object_correspondence_candidate_generated | PASS |
| 3 | invariant_preserving_candidate_generated | PASS |
| 4 | composed_transform_candidate_generated | PASS |
| 5 | train_forced_transformation_candidate_generated | PASS |
| 6 | explicit_grammar_candidate_generated | PASS |
| 7 | partial_candidate_descriptor_generated | PASS |
| 8 | no_forced_constraints_blocks_generation | PASS |
| 9 | hidden_test_request_blocks_generation | PASS |
| 10 | public_answer_request_blocks_generation | PASS |
| 11 | rehearsal_policy_preserved | PASS |
| 12 | fresh_holdout_policy_preserved | PASS |
| 13 | ledger_relationship_preserved | PASS |

**Functional cases run: 13**
**Functional cases passed: 13**
**Functional cases failed: 0**

## 3. Metrics summary

| Metric | Value |
|--------|-------|
| candidate_generation_attempt_count | 7 |
| candidate_generated_count | 6 |
| candidate_generation_blocked_count | 3 |
| candidate_requires_ledger_review_count | 6 |

## 4. Safety verification

| Check | Result |
|-------|--------|
| All generated candidates require ledger review | YES ✓ |
| No final answers generated | YES ✓ |
| No deservedness granted by generator | YES ✓ |
| Unsafe paths fail closed | YES ✓ |
| Rehearsal/holdout separation preserved | YES ✓ |
| Runtime behavior unchanged | YES ✓ |

## 5. Construction modes verified

All 7 modes functional:
1. relation_first_rewrite_candidate ✓
2. object_correspondence_candidate ✓
3. invariant_preserving_candidate ✓
4. composed_transform_candidate ✓
5. train_forced_transformation_candidate ✓
6. explicit_grammar_candidate ✓
7. partial_candidate_descriptor ✓

## 6. Blocking rules verified

All blocking rules work:
- No forced constraints → blocked ✓
- Hidden test request → blocked ✓
- Public ARC request → blocked ✓

## 7. Ledger relationship preserved

- `requires_ledger_review = True` ✓
- `generator_grants_deservedness = False` ✓
- `generator_outputs_final_answer = False` ✓

## 8. Policy verification

- Rehearsal allowed but does NOT count toward threshold ✓
- Fresh holdout counts only with no leakage ✓
- Holdout answers must NOT train generator ✓

---

Functional run complete: yes
Functional cases passed: 13/13
Candidate generation attempt count: 7
Candidate generated count: 6
Candidate generation blocked count: 3
All generated candidates require ledger review: yes
No final answers generated: yes
No deservedness granted by generator: yes
Unsafe paths fail closed: yes
Rehearsal/holdout separation preserved: yes
Runtime behavior unchanged: yes
Validation: PASS
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_controlled_answer_candidate_generator_functional_run_complete