# WESLR ARC CONSTRAINT SATISFACTION RIVAL GRAMMAR HELPER FUNCTIONAL CASE 7 REPAIR V1

## 1. Issue found
**Yes.** Case 7 "consistency_is_not_truth" was incorrectly returning "candidate_deserved_if_unique_and_forced" when only one grammar was consistent but not forced by train evidence.

The core law violation: Consistency alone is NOT proof of truth. A grammar may be consistent but not forced by train evidence — it should not receive a "deserved" status.

## 2. Code changed
**Yes.** Modified `_determine_overall_status()` in `arc_constraint_satisfaction_rival_grammar_helper.py`:

- Added check: If only 1 grammar among 1 candidate is consistent, return "grammar_consistent" (NOT forced)
- Only return "candidate_deserved_if_unique_and_forced" when multiple candidates existed and only 1 survived (forced by train evidence)

## 3. Tests changed
**Yes.** Added explicit test `test_consistency_is_not_forced_grammar()`:
- Verifies single consistent grammar returns "grammar_consistent"
- Verifies "helper_generates_final_answer = False"
- Verifies "final_answer_authority = ledger"

## 4. Corrected case 7 result

| Before | After |
|--------|-------|
| candidate_deserved_if_unique_and_forced | grammar_consistent |
| helper_generates_final_answer: False | helper_generates_final_answer: False |
| final_answer_authority: ledger | final_answer_authority: ledger |

**Now correctly distinguishes**:
- "grammar_consistent": One grammar consistent, but NOT forced by train evidence
- "candidate_deserved_if_unique_and_forced": Multiple candidates existed, only one survived (forced by train evidence)

## 5. Helper 3 remains complete
**Yes.** All other functionality intact:
- Multi-grammar rival cases still work
- Elimination by train evidence still works
- Unsupported assumption blocking still works
- All metrics still computed correctly

## 6. Helper 4 design remains valid
**Yes.** The Counterexample/Divergence Helper design (helper 4) is unaffected:
- Helper 3 now correctly returns "grammar_consistent" for non-forced cases
- Helper 4 can still detect divergence between grammars
- The repair strengthens the boundary between consistency and forced uniqueness

## 7. Recommended next lane
`IMPLEMENT_ARC_COUNTEREXAMPLE_DIVERGENCE_HELPER_V1`

---
Issue confirmed: yes
Code changed: yes
Tests changed: yes
Corrected case 7 status: grammar_consistent
Consistency no longer treated as truth: yes
Ledger boundary preserved: yes
Helper 3 remains complete: yes
Helper 4 design remains valid: yes
Validation: PASS (29 tests)
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: case_7_repair_complete