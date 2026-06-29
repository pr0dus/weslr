# WESLR ARC GENERATIVE BRIDGE V5 REPLAY AFTER RIVAL FALSE UNIQUENESS REPAIR RUN V1

## 1. Executive verdict
`arc_generative_bridge_v5_replay_after_rival_false_uniqueness_repair_assembler_repair_recommended`

## 2. Run scope
- Ran **48 local synthetic tasks**.
- Coverage remained **8 groups × 6 tasks**.
- This remained **synthetic-only**.
- No public ARC / Kaggle data was used.
- No replay-to-runtime wiring occurred.
- Expected-answer scoring stayed **after ledger decision only**.

## 3. Comparison against previous bridge replay
Previous registered replay baseline:
- attempted_tasks: 48
- candidate_generated_tasks: 48
- candidate_deserved_tasks: 6
- task_exact_count: 3
- deserved_exact_count: 3
- undeserved_exact_count: 0
- deserved_but_wrong_count: 3
- safe_failure_count: 0
- overconfident_wrong_count: 0
- candidate_not_deserved_count: 42
- candidate_blocked_count: 0
- emitter_gate_passed: no
- hard stop reason: `deserved_but_wrong`

Current replay after rival false-uniqueness repair:
- attempted_tasks: 48 (unchanged)
- candidate_generated_tasks: 48 (unchanged)
- candidate_deserved_tasks: 12 (**up from 6**)
- task_exact_count: 5 (**up from 3**)
- deserved_exact_count: 5 (**up from 3**)
- undeserved_exact_count: 0 (unchanged)
- deserved_but_wrong_count: 7 (**up from 3**)
- safe_failure_count: 36 (**up from 0**)
- overconfident_wrong_count: 0 (unchanged)
- candidate_not_deserved_count: 36 (**down from 42**)
- candidate_blocked_count: 0 (unchanged)
- emitter_gate_passed: no (unchanged)
- hard stop reason: `deserved_but_wrong` (unchanged)

Interpretation of the comparison:
- the rival-grammar family is no longer unsafe-deserved
- safe failure was strongly restored
- but unsafe deservedness was **not** eliminated globally
- instead, deserved-but-wrong shifted and increased in other groups

## 4. Task-level metrics
- attempted_tasks: 48
- candidate_generated_tasks: 48
- candidate_deserved_tasks: 12
- task_exact_count: 5
- task_exact_rate: 0.10416666666666667
- deserved_exact_count: 5
- undeserved_exact_count: 0
- deserved_but_wrong_count: 7
- safe_failure_count: 36
- overconfident_wrong_count: 0
- candidate_not_deserved_count: 36
- candidate_blocked_count: 0
- helper_laundering_violation_count: 0
- final_answer_emitted_count: 0
- public_claim_allowed_count: 0
- helper_output_as_evidence_count: 0

## 5. Generation, trace-grounding, and rival-context metrics
- candidate_generation_attempt_count: 48
- candidate_generated_count: 48
- candidate_generation_blocked_count: 0
- relation_first_rewrite_candidate_count: 0
- object_correspondence_candidate_count: 6
- invariant_preserving_candidate_count: 6
- composed_transform_candidate_count: 6
- train_forced_transformation_candidate_count: 24
- explicit_grammar_candidate_count: 6
- partial_candidate_descriptor_count: 0
- ledger_review_required_count: 48
- construction_trace_complete_count: 12
- forced_uniqueness_trace_present_count: 12
- rival_elimination_trace_present_count: 0
- train_evidence_grounded_count: 18
- candidate_trace_missing_required_fields_count: 36
- candidate_trace_source_grounded_count: 48
- candidate_trace_incomplete_count: 36
- rival_context_detected_count: 6
- rival_context_missing_proof_count: 6
- rival_context_safe_failure_count: 6
- train_forced_rival_bypass_blocked_count: 6

## 6. Ledger metrics
- candidate_deserved_count: 12
- candidate_not_deserved_count: 36
- safe_failure_required_count: 36
- needs_candidate_generation_count: 0
- rival_unresolved_count: 6
- forced_unique_output_count: 12
- insufficient_train_evidence_count: 30
- unsupported_assumption_rejected_count: 0
- mdl_only_rejected_count: 0
- rehearsal_only_rejected_count: 0
- hidden_test_blocked_count: 0
- public_arc_answer_blocked_count: 0
- helper_output_as_evidence_blocked_count: 0
- safe_failure_from_insufficient_evidence_count: 0
- safe_failure_from_incomplete_trace_count: 30
- safe_failure_from_unresolved_rival_count: 6
- final_answer_emitted_count: 0

## 7. Emitter gate result
- emitter_gate_passed: false
- emitter_hard_stop_triggered: true
- emitter_hard_stop_reasons: [`deserved_but_wrong`]
- deserved_but_wrong_count: 7
- deserved_exact_group_count: 2
- generator_health_warning: false
- generator_health_warning_reasons: []
- no_dominant_discriminator_middle_band: false
- recommended_next_lane: `REPAIR_ARC_LEDGER_DESERVEDNESS_ASSEMBLER_V1`

Pre-registered rule application:
- emitter boundary design is **not allowed** because required thresholds did not pass
- emitter implementation is **not allowed**

## 8. Group-level results
### v4_rival_grammar_replay_6
- tasks attempted: 6
- candidates generated: 6
- candidates deserved: 0
- deserved exacts: 0
- undeserved exacts: 0
- deserved-but-wrong: 0
- safe failures: 6
- blocked candidates: 0
- trace-complete candidates: 0
- forced-uniqueness-trace candidates: 0
- rival-context detected candidates: 6
- rival-context safe failures: 6
- dominant success reason: none
- dominant failure reason: rival context missing proof -> unresolved rival safe failure
- missing bridge: rival-proofed candidate path that can survive ledger without unsafe deservedness

### v4_beautiful_wrong_rule_replay_6
- tasks attempted: 6
- candidates generated: 6
- candidates deserved: 0
- deserved exacts: 0
- undeserved exacts: 0
- deserved-but-wrong: 0
- safe failures: 6
- blocked candidates: 0
- trace-complete candidates: 0
- forced-uniqueness-trace candidates: 0
- rival-context detected candidates: 0
- rival-context safe failures: 0
- dominant success reason: none
- dominant failure reason: incomplete construction trace safe failure
- missing bridge: train-grounded completion path for beautiful-wrong-rule family

### v4_composed_transform_replay_6
- tasks attempted: 6
- candidates generated: 6
- candidates deserved: 6
- deserved exacts: 2
- undeserved exacts: 0
- deserved-but-wrong: 4
- safe failures: 0
- blocked candidates: 0
- trace-complete candidates: 6
- forced-uniqueness-trace candidates: 6
- rival-context detected candidates: 0
- rival-context safe failures: 0
- dominant success reason: composed transform candidate reaches complete forced-unique train-grounded ledger path
- dominant failure reason: deserved-but-wrong persists after ledger approval
- missing bridge: discrimination layer separating valid composed exacts from unsafe composed deservedness

### v4_negative_evidence_replay_6
- tasks attempted: 6
- candidates generated: 6
- candidates deserved: 0
- deserved exacts: 0
- undeserved exacts: 0
- deserved-but-wrong: 0
- safe failures: 6
- blocked candidates: 0
- trace-complete candidates: 0
- forced-uniqueness-trace candidates: 0
- rival-context detected candidates: 0
- rival-context safe failures: 0
- dominant success reason: none
- dominant failure reason: incomplete construction trace safe failure
- missing bridge: negative-evidence-aware candidate completion path

### v4_helper_trap_replay_6
- tasks attempted: 6
- candidates generated: 6
- candidates deserved: 0
- deserved exacts: 0
- undeserved exacts: 0
- deserved-but-wrong: 0
- safe failures: 6
- blocked candidates: 0
- trace-complete candidates: 0
- forced-uniqueness-trace candidates: 0
- rival-context detected candidates: 0
- rival-context safe failures: 0
- dominant success reason: none
- dominant failure reason: incomplete construction trace safe failure
- missing bridge: helper-trap-resistant completion path without helper laundering

### object_graph_correspondence_6
- tasks attempted: 6
- candidates generated: 6
- candidates deserved: 0
- deserved exacts: 0
- undeserved exacts: 0
- deserved-but-wrong: 0
- safe failures: 6
- blocked candidates: 0
- trace-complete candidates: 0
- forced-uniqueness-trace candidates: 0
- rival-context detected candidates: 0
- rival-context safe failures: 0
- dominant success reason: none
- dominant failure reason: incomplete construction trace safe failure
- missing bridge: correspondence completion / uniqueness proof path

### invariant_symmetry_ambiguity_6
- tasks attempted: 6
- candidates generated: 6
- candidates deserved: 0
- deserved exacts: 0
- undeserved exacts: 0
- deserved-but-wrong: 0
- safe failures: 6
- blocked candidates: 0
- trace-complete candidates: 0
- forced-uniqueness-trace candidates: 0
- rival-context detected candidates: 0
- rival-context safe failures: 0
- dominant success reason: none
- dominant failure reason: incomplete construction trace safe failure
- missing bridge: symmetry / ambiguity resolution path that can complete safely

### mdl_simplicity_trap_6
- tasks attempted: 6
- candidates generated: 6
- candidates deserved: 6
- deserved exacts: 3
- undeserved exacts: 0
- deserved-but-wrong: 3
- safe failures: 0
- blocked candidates: 0
- trace-complete candidates: 6
- forced-uniqueness-trace candidates: 6
- rival-context detected candidates: 0
- rival-context safe failures: 0
- dominant success reason: explicit grammar candidate reaches complete forced-unique train-grounded ledger path
- dominant failure reason: deserved-but-wrong persists after ledger approval
- missing bridge: stronger ledger discrimination against wrong-but-trace-complete grammar candidates

## 9. Interpretation
Using the pre-registered interpretation rules only:
- `deserved_but_wrong_count` was **not eliminated**; it increased from 3 to 7
- safe failure **was restored**; current safe failure count is 36
- candidate generation remained **healthy** in the narrow replay sense; 48 / 48 tasks still generated candidates and generator-health warning did not fire
- trace grounding **does reach the assembler**; complete trace / forced uniqueness / train-grounding counts propagate into ledger metrics consistently
- rival-grammar false uniqueness **was blocked**; rival group produced 0 deserved and 6 rival-context safe failures
- broad rival-context detection does **not** appear to overblock this replay run itself; only the rival replay family triggered rival-context counters in the full 48-task run
- some deserved candidates remain wrong; 7 tasks still become deserved-but-wrong
- emitter design is **not allowed**
- emitter implementation is **not allowed**
- generator-health analysis is **not required** by the pre-registered gate
- results remain **synthetic-only**

The dominant current failure is no longer the rival-grammar bypass.
The dominant current failure is residual unsafe deservedness in non-rival groups, especially:
- `v4_composed_transform_replay_6`
- `mdl_simplicity_trap_6`

## 10. Safety verification
Confirmed:
- no public ARC / Kaggle data
- no hidden test output
- no expected-answer leakage into generation / deservedness
- no helper-output laundering
- no final answers emitted
- no public claims allowed
- no runtime wiring
- no ChatResponder changes
- no `.weslr`
- no external calls
- protected files unchanged

## 11. Recommended next safe local follow-up
`REPAIR_ARC_LEDGER_DESERVEDNESS_ASSEMBLER_V1`
