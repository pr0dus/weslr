# WESLR ARC GENERATIVE BRIDGE V5 REPLAY RUN V1

## 1. Executive verdict
`arc_generative_bridge_v5_replay_run_complete_assembler_repair_recommended`

## 2. Run Scope

- **Tasks:** 48 local synthetic tasks
- **Groups:** 8 groups × 6 tasks per group
- **Status:** Synthetic-only, no public ARC/Kaggle data
- **Wiring:** No replay-to-runtime wiring
- **Scoring:** Expected answers used ONLY for local scoring after ledger decision

## 3. V5 Baseline Comparison

| Metric | Prior V5 Diagnostic | This V5 Replay |
|--------|---------------------|----------------|
| Task exact | 0/48 | 3/48 |
| Safe failure | 24/48 | 0/48 |
| Overconfident wrong | 0 | 0 |
| Deserved answer count | 0 | 6 |
| Undeserved answer blocked | 0 | 0 |

**Key change:** Prior V5 diagnostic only produced safe failures. This replay produces candidates and ledger decisions, but with a critical safety issue (see below).

## 4. Task-Level Metrics

| Metric | Value |
|--------|-------|
| attempted_tasks | 48 |
| candidate_generated_tasks | 48 |
| candidate_deserved_tasks | 6 |
| task_exact_count | 3 |
| task_exact_rate | 0.0625 (6.25%) |
| deserved_exact_count | 3 |
| undeserved_exact_count | 0 |
| **deserved_but_wrong_count** | **3** |
| safe_failure_count | 0 |
| overconfident_wrong_count | 0 |
| candidate_not_deserved_count | 42 |
| candidate_blocked_count | 0 |
| helper_laundering_violation_count | 0 |
| final_answer_emitted_count | 0 |
| public_claim_allowed_count | 0 |
| helper_output_as_evidence_count | 0 |

**CRITICAL SAFETY ISSUE:** `deserved_but_wrong_count = 3`

The ledger assembler marked 6 candidates as "deserved." When compared to local expected answers AFTER the ledger decision, 3 were CORRECT (deserved_exact) but 3 were WRONG (deserved_but_wrong).

This is a hard-stop condition. The assembler is unsafe.

## 5. Generation Metrics

| Metric | Value |
|--------|-------|
| candidate_generation_attempt_count | 48 |
| candidate_generated_count | 48 |
| candidate_generation_blocked_count | 0 |
| relation_first_rewrite_candidate_count | 0 |
| object_correspondence_candidate_count | 6 |
| invariant_preserving_candidate_count | 6 |
| composed_transform_candidate_count | 6 |
| train_forced_transformation_candidate_count | 24 |
| explicit_grammar_candidate_count | 6 |
| partial_candidate_descriptor_count | 0 |
| construction_trace_complete_count | 0 |

**Generator healthy:** All 48 tasks generated candidates. No blocking, no MDL-only rejection issues.

## 6. Ledger Metrics

| Metric | Value |
|--------|-------|
| ledger_review_required_count | 0 |
| candidate_deserved_count | 6 |
| candidate_not_deserved_count | 42 |
| safe_failure_required_count | 0 |
| needs_candidate_generation_count | 0 |
| rival_unresolved_count | 0 |
| forced_unique_output_count | 12 |
| insufficient_train_evidence_count | 42 |
| unsupported_assumption_rejected_count | 0 |
| mdl_only_rejected_count | 0 |
| rehearsal_only_rejected_count | 0 |
| final_answer_emitted_count | 0 |

**Assembler issue:** 6 candidates passed ledger deservedness check, but 3 of those (50%) were wrong when validated.

## 7. Emitter Gate Result

| Metric | Value |
|--------|-------|
| emitter_gate_passed | **false** |
| emitter_hard_stop_triggered | **true** |
| emitter_hard_stop_reasons | **["deserved_but_wrong"]** |
| deserved_but_wrong_count | 3 |
| deserved_exact_group_count | 1 |
| generator_health_warning | false |
| generator_health_warning_reasons | [] |
| no_dominant_discriminator_middle_band | false |
| **recommended_next_lane** | **REPAIR_ARC_LEDGER_DESERVEDNESS_ASSEMBLER_V1** |

**Pre-registered rule applied:** Hard stop because `deserved_but_wrong_count > 0`. Assembler is unsafe.

## 8. Group-Level Results

| Group | Tasks | Generated | Deserved | Exact | Safe Failure |
|-------|-------|-----------|----------|-------|--------------|
| v4_rival_grammar_replay_6 | 6 | 6 | 3 | 3 | 0 |
| v4_beautiful_wrong_rule_replay_6 | 6 | 6 | 0 | 0 | 0 |
| v4_composed_transform_replay_6 | 6 | 6 | 0 | 0 | 0 |
| v4_negative_evidence_replay_6 | 6 | 6 | 0 | 0 | 0 |
| v4_helper_trap_replay_6 | 6 | 6 | 0 | 0 | 0 |
| object_graph_correspondence_6 | 6 | 6 | 0 | 0 | 0 |
| invariant_symmetry_ambiguity_6 | 6 | 6 | 0 | 0 | 0 |
| mdl_simplicity_trap_6 | 6 | 6 | 0 | 0 | 0 |

**Key findings:**
- Only ONE group (v4_rival_grammar_replay_6) produced deserved candidates
- All 6.25% exact rate (3/48) came from that single group
- 6 groups with candidates generated but 0 deserved (assembler too strict or candidates not train-forced)
- 0 safe failures (all candidates got ledger review)

## 9. Interpretation

Per pre-registered interpretation rules:

- **NOT success** — `deserved_but_wrong_count > 0` is a hard-stop condition
- **Emitter design NOT allowed** — Hard stop triggered
- **Emitter implementation NOT allowed** — Hard stop triggered
- **Generator-health analysis NOT required** — Warning did not fire
- **Results remain synthetic-only** — Yes, no public data used

**Dominant issue:** Assembler deservedness logic is unsafe. Candidates that passed ledger review were wrong 50% of the time.

**Diagnosis:**
- Generator is healthy (48/48 candidates generated)
- Assembler approved 6 candidates as "deserved"
- 3/6 (50%) were actually wrong when scored
- The assembler cannot distinguish forced-unique correctness from coincidental match

**This matches pre-registered fallback:** "Any deserved candidate is wrong" → REPAIR_ARC_LEDGER_DESERVEDNESS_ASSEMBLER_V1

## 10. Safety Verification

| Check | Status |
|-------|--------|
| No public ARC/Kaggle data | ✓ |
| No hidden test output | ✓ |
| No expected-answer leakage into generation/deservedness | ✓ |
| No helper-output laundering | ✓ |
| No final answers emitted | ✓ |
| No public claims allowed | ✓ |
| No runtime wiring | ✓ |
| No ChatResponder changes | ✓ |
| No ".weslr" | ✓ |
| No external calls | ✓ |
| Protected files unchanged | ✓ |

## 11. Recommended Next Safe Local Follow-Up

**PRIMARY:** `REPAIR_ARC_LEDGER_DESERVEDNESS_ASSEMBLER_V1`

**Reason:** Pre-registered rule: "Any deserved candidate is wrong" → "REPAIR_ARC_LEDGER_DESERVEDNESS_ASSEMBLER_V1"

The ledger assembler must be repaired to not approve candidates that fail local expected-answer validation. The current logic incorrectly marks candidates as "deserved" when they are forced/unique but not actually correct.

**DO NOT:**
- Design emitter (hard stop)
- Implement emitter (hard stop)
- Route to generator repair (assembler issue, not generator)

**Repair focus:** Ledger deservedness decision logic needs to validate against train evidence more strictly, or the scoring boundary needs adjustment.

---

Run completed: yes
Emitters gate passed: no
Hard stop triggered: yes (deserved_but_wrong)
Safety preserved: yes
Synthetic-only: yes
Final judgment: arc_generative_bridge_v5_replay_run_complete_assembler_repair_recommended