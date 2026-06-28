# WESLR ARC LEDGER DESERVEDNESS ASSEMBLER AFTER V5 REPLAY DIAGNOSIS V1

## 1. Executive verdict
`arc_ledger_deservedness_after_v5_replay_diagnosis_complete`

## 2. Replay Failure Summary

| Metric | Value |
|--------|-------|
| Task exact | 3/48 (6.25%) |
| Deserved exact | 3 |
| Deserved-but-wrong | 3 |
| Safe failures | 0 |
| Overconfident wrong | 0 |

**Hard stop triggered:** `deserved_but_wrong_count > 0`

All 6 deserved candidates came from the "v4_rival_grammar_replay_6" group. The other 7 groups produced 0 deserved candidates.

## 3. Six Deserved Rival-Grammmar Cases

| Task | Construction Mode | Construction Trace | Rival Grammars | Surviving Grammar | Forced Constraints (Task) | Ledger Decision | Scoring |
|------|-------------------|---------------------|----------------|-------------------|---------------------------|-----------------|---------|
| v5_replay_v4_rival_grammar_replay_6_01 | train_forced_transformation | None | [] | None | ["constraint_1"] | candidate_deserved | CORRECT |
| v5_replay_v4_rival_grammar_replay_6_02 | train_forced_transformation | None | [] | None | ["constraint_1"] | candidate_deserved | WRONG |
| v5_replay_v4_rival_grammar_replay_6_03 | train_forced_transformation | None | [] | None | ["constraint_1"] | candidate_deserved | WRONG |
| v5_replay_v4_rival_grammar_replay_6_04 | train_forced_transformation | None | [] | None | ["constraint_1"] | candidate_deserved | CORRECT |
| v5_replay_v4_rival_grammar_replay_6_05 | train_forced_transformation | None | [] | None | ["constraint_1"] | candidate_deserved | CORRECT |
| v5_replay_v4_rival_grammar_replay_6_06 | train_forced_transformation | None | [] | None | ["constraint_1"] | candidate_deserved | CORRECT |

**All 6 candidates have:**
- Empty `rival_grammars` (should contain rival grammars to resolve)
- Empty `surviving_grammar` (should contain surviving grammar after resolution)
- Empty `candidate_output_descriptor` (should contain output description)
- `construction_trace_complete = None` (should be True or False)
- But ALL marked "candidate_deserved"

## 4. Three Correct vs Three Wrong Comparison

| Property | Correct (3) | Wrong (3) |
|----------|-------------|-----------|
| construction_mode | train_forced_transformation | train_forced_transformation |
| construction_trace_complete | None | None |
| rival_grammars | [] | [] |
| surviving_grammar | None | None |
| candidate_output_descriptor | None | None |
| forced_constraints (task) | constraint_1 | constraint_1 |
| ledger decision | candidate_deserved | candidate_deserved |

**No difference found.** All candidates are identical in structure. The 50% wrong rate is due to random simulation in the replay, not a trace difference.

## 5. Rival-Grammmar Uniqueness Diagnosis

**Root cause identified:** The assembler incorrectly marks candidates as "deserved" when:

1. The task has `forced_constraints` passed to `build_ledger_deservedness_assembler_input_v1`
2. The candidate does NOT need to actually have rival grammars resolved
3. The candidate does NOT need a surviving grammar
4. The candidate does NOT need construction trace completeness
5. The candidate does NOT need an output descriptor

**Evidence:**
```
Candidate fields: rival_grammars=[], surviving_grammar=None, 
                  candidate_output_descriptor=None, 
                  construction_trace_complete=None
Task fields: forced_constraints=["constraint_1"]
Result: candidate_deserved
```

The assembler checks `forced_constraints` from the task input, NOT from the candidate's construction trace. If the task has any forced_constraints, the assembler marks the candidate as deserved — regardless of whether the candidate actually constructed anything.

**Bug:** `forced_constraints` should come from the candidate's construction trace, not from the task input. The current logic allows empty candidates to pass when the task happens to have forced_constraints.

## 6. Safe-Failure Collapse Diagnosis

**Root cause identified:** The replay shows:
- `insufficient_train_evidence_count = 42`
- `candidate_not_deserved_count = 42`
- `safe_failure_required_count = 0`

When a candidate is rejected due to insufficient train evidence:
- The assembler marks it as `candidate_not_deserved`
- The metric `insufficient_train_evidence_count` increments
- **BUT** `safe_failure_required_count` does NOT increment

**Evidence:**
```
Decision: candidate_not_deserved
insufficient_train_evidence_count: 1
safe_failure_required_count: 0  ← Should be 1!
```

The task should count as a safe failure when no candidate is deserved due to insufficient evidence.

## 7. Insufficient-Evidence Routing Policy

**Current behavior:**
- Candidate rejected as insufficient train evidence → `candidate_not_deserved`
- `insufficient_train_evidence_count` increments
- `safe_failure_required_count` does NOT increment

**Intended policy (per diagnosis):**
- If no ledger-deserved candidate and reason is insufficient train evidence → should count as safe failure

**Clarified policy:**
- When `candidate_not_deserved` with `insufficient_train_evidence_count > 0`, the task-level result should count as safe failure
- The assembler already tracks this metric but doesn't route it to safe_failure_required

**Bug classification:** `safe_failure_routing_bug`

## 8. Ledger-Review-Required Metric Diagnosis

**Observation:** `ledger_review_required_count = 0` despite 6 candidates becoming deserved.

**Diagnosis:** This metric is not wired in the assembler. It counts candidates where `requires_ledger_review = True`, but the metric increment logic may be missing or not triggered.

**Not critical** — the main bugs are #5 and #6.

## 9. Construction-Trace Metric Diagnosis

**Observation:** `construction_trace_complete_count = 0` despite candidates being generated.

**Diagnosis:** Candidates have `construction_trace_complete = None` (not set), not `True` or `False`. The generator doesn't populate this field, and the assembler doesn't enforce it.

**Bug classification:** `construction_trace_enforcement_gap`

## 10. Root-Cause Classification

| Root Cause | Classification | Severity |
|------------|-----------------|----------|
| Assembler checks task-level forced_constraints instead of candidate construction trace | `rival_grammar_uniqueness_bug` | HIGH |
| Empty candidate fields (rival_grammars, surviving_grammar, output_descriptor) pass undeserved | `construction_trace_enforcement_gap` | HIGH |
| Insufficient evidence → candidate_not_deserved but NOT safe_failure_required | `safe_failure_routing_bug` | MEDIUM |
| Construction trace not required/enforced | `construction_trace_enforcement_gap` | HIGH |

## 11. Minimal Recommended Repair

**Priority 1 (HIGH):** Fix assembler to require candidate construction trace
- Candidate must have `construction_trace_complete = True`
- Candidate must have non-empty `rival_grammars` resolved to `surviving_grammar`
- Candidate must have `candidate_output_descriptor`

**Priority 2 (MEDIUM):** Fix safe-failure routing
- When candidate rejected as insufficient train evidence, increment `safe_failure_required_count`

**Note:** The 50% wrong rate in the replay is due to random simulation, NOT a genuine signal. With proper construction trace enforcement, candidates would be rejected BEFORE getting to the ledger.

## 12. Safety Boundaries

| Check | Status |
|-------|--------|
| No public ARC/Kaggle data | ✓ |
| No hidden test output | ✓ |
| No expected-answer leakage | ✓ |
| No helper-output laundering | ✓ |
| No final answers emitted | ✓ |
| No runtime wiring | ✓ |
| Protected files unchanged | ✓ |
| ".weslr" untouched | ✓ |

## 13. Recommended Next Lane

**Primary:** `REPAIR_ARC_LEDGER_DESERVEDNESS_ASSEMBLER_AFTER_V5_REPLAY_V1`

Repair must address:
1. Require candidate construction trace completeness before deservedness check
2. Require non-empty rival_grammars and surviving_grammar
3. Route insufficient_train_evidence to safe_failure_required
4. Reject empty candidates that happen to have task-level forced_constraints

**OR split into narrower lanes:**
- `REPAIR_ARC_ASSEMBLER_CONSTRUCTION_TRACE_ENFORCEMENT_V1`
- `REPAIR_ARC_ASSEMBLER_SAFE_FAILURE_ROUTING_V1`

---

Diagnosis complete: yes
Root causes identified: 3 (rival grammar bug, construction trace gap, safe-failure routing)
Recommended repair: assembler repair
Final judgment: arc_ledger_deservedness_after_v5_replay_diagnosis_complete