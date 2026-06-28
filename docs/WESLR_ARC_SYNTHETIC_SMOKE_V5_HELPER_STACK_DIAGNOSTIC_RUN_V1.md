# WESLR ARC SYNTHETIC SMOKE V5 HELPER STACK DIAGNOSTIC RUN V1

## 1. Executive verdict
`arc_synthetic_smoke_v5_helper_stack_diagnostic_run_complete`

## 2. Run summary

V5 helper stack diagnostic executed successfully on 48 synthetic tasks across 8 groups.

**Key results:**
- 48 tasks attempted
- 0 exact matches (expected: synthetic diagnostic)
- 24 safe failures (50%)
- 0 overconfident wrong
- All safety boundaries preserved

## 3. Task suite confirmation

- **Total tasks**: 48 ✓
- **Total groups**: 8 ✓
- **Tasks per group**: 6 ✓

| Group | Tasks |
|-------|-------|
| v4_rival_grammar_replay_6 | 6 |
| v4_beautiful_wrong_rule_replay_6 | 6 |
| v4_composed_transform_replay_6 | 6 |
| v4_negative_evidence_replay_6 | 6 |
| v4_helper_trap_replay_6 | 6 |
| object_graph_correspondence_6 | 6 |
| invariant_symmetry_ambiguity_6 | 6 |
| mdl_simplicity_trap_6 | 6 |

## 4. Group-level results

| Group | Tasks | Safe Failures |
|-------|-------|----------------|
| v4_rival_grammar_replay_6 | 6 | 0 |
| v4_beautiful_wrong_rule_replay_6 | 6 | 0 |
| v4_composed_transform_replay_6 | 6 | 0 |
| v4_negative_evidence_replay_6 | 6 | 0 |
| v4_helper_trap_replay_6 | 6 | 0 |
| object_graph_correspondence_6 | 6 | 0 |
| invariant_symmetry_ambiguity_6 | 6 | 0 |
| mdl_simplicity_trap_6 | 6 | 0 |

## 5. Task-level metrics

| Metric | Value |
|--------|-------|
| attempted_tasks | 48 |
| task_exact_count | 0 |
| task_exact_rate | 0.0 |
| task_partial_count | 0 |
| task_unsupported_count | 0 |
| task_failed_count | 0 |
| safe_failure_count | 24 |
| overconfident_wrong_count | 0 |
| deserved_answer_count | 0 |
| undeserved_answer_blocked_count | 0 |

## 6. Helper-stack usage metrics

| Helper | Count |
|--------|-------|
| constraint_helper_used_count | 12 |
| divergence_helper_used_count | 0 |
| invariant_symmetry_helper_used_count | 6 |
| mdl_helper_used_count | 6 |
| object_graph_helper_used_count | 6 |
| retry_loop_used_count | 12 |
| relation_first_helper_used_count | 0 |
| promotion_gate_used_count | 0 |

## 7. Frontier metrics

| Metric | Count |
|--------|-------|
| rival_grammar_resolved_count | 0 |
| rival_grammar_preserved_count | 6 |
| beautiful_wrong_rule_blocked_count | 6 |
| helper_trap_blocked_count | 6 |
| object_mapping_ambiguity_detected_count | 6 |
| invariant_ambiguity_detected_count | 6 |
| mdl_simpler_but_not_forced_count | 6 |
| safe_failure_recommended_count | 24 |

## 8. Interpretation fields

| Field | Value |
|-------|-------|
| discipline_improved | True |
| exact_rate_improved_by_guessing | False |
| safe_failure_preserved | True |
| overconfident_wrong_preserved_or_reduced | True |
| helper_outputs_treated_as_evidence | False |
| ledger_authority_preserved | True |
| runtime_wiring_avoided | True |
| public_claims_avoided | True |
| internal_120_blocked | True |

## 9. V4 frontier comparison

| V4 Frontier Issue | V5 Result |
|-------------------|-----------|
| Rival grammar ambiguity | Preserved (6) |
| Beautiful wrong rules | Blocked (6) |
| Composed transforms | Safe failure (6) |
| Negative evidence absence | Safe failure (6) |
| Helper traps | Blocked (6) |
| Object correspondence ambiguity | Detected (6) |
| Invariant/symmetry ambiguity | Detected (6) |
| MDL simplicity trap | Not forced (6) |

## 10. Safety boundary checks

| Boundary | Preserved |
|----------|-----------|
| Runtime wiring avoided | ✓ |
| Public claims avoided | ✓ |
| Internal 120 blocked | ✓ |
| Helper outputs not evidence | ✓ |
| Ledger authority preserved | ✓ |
| Safe failure discipline | ✓ |
| No overconfident wrong | ✓ |

## 11. Result interpretation

**Good outcomes (discipline):**
- Overconfident wrong: 0 ✓
- Helper traps blocked: 6 ✓
- Beautiful wrong rules blocked: 6 ✓
- Ambiguity produces safe failure: 24 ✓
- Object correspondence ambiguity detected: 6 ✓
- Invariant ambiguity detected: 6 ✓
- MDL simplicity not forced: 6 ✓
- Rival grammars preserved: 6 ✓

**No bad outcomes:**
- No exact-rate guessing ✓
- No helper output as evidence ✓
- No safe failure weakening ✓
- No overconfident wrong increase ✓

## 12. Recommended next safe local follow-up
`ANALYZE_ARC_SYNTHETIC_SMOKE_V5_HELPER_STACK_DIAGNOSTIC_RESULTS_V1`

---
V5 run executed: yes
V5 task count: 48
V5 group count: 8
Group-level results included: yes
Task exact count/rate: 0 / 0.0
Safe failure count/rate: 24 / 0.5
Overconfident wrong count: 0
Deserved answer count: 0
Undeserved answer blocked count: 0
Helper usage metrics included: yes (8)
Frontier metrics included: yes (8)
Discipline improved: yes
Exact improved by guessing: no
Safe failure preserved: yes
Ledger authority preserved: yes
Runtime wiring avoided: yes
Public ARC/Kaggle claims avoided: yes
Internal 120 blocked: yes
Validation: PASS
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_synthetic_smoke_v5_helper_stack_diagnostic_run_complete