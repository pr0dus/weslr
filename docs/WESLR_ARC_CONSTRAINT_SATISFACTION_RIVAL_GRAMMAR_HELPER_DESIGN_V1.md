# WESLR ARC CONSTRAINT SATISFACTION RIVAL GRAMMAR HELPER DESIGN V1

## 1. Executive verdict
`arc_constraint_satisfaction_rival_grammar_helper_design_ready`

## 2. Purpose and mathematical grounding

### Purpose
Design a pure helper that treats candidate grammars as constraints and checks which grammars remain legally compatible with train examples.

### Mathematical Grounding
- **Constraint Satisfaction Problems (CSP)**: The helper treats grammar selection as a CSP
- **SAT/SMT-style consistency checking**: Check whether grammar predictions are consistent with train inputs
- **Finite model checking**: Verify grammar predictions against finite train sets
- **Proof obligation checking**: Check whether train evidence forces a unique conclusion
- **Elimination by contradiction**: Grammar is eliminated only when train evidence contradicts it

## 3. Helper roadmap position

| # | Helper | Status |
|---|--------|--------|
| 1 | Relation-First Compiler Helper | Complete |
| 2 | Ledger-Guided Micro-Theory Retry Loop Helper | Complete (functional run) |
| 3 | **Constraint Satisfaction / Rival Grammar Helper** | **Current lane** |
| 4 | Counterexample / Divergence Helper | Not yet |
| 5 | Invariant / Symmetry Helper | Not yet |
| 6 | Minimum Description Length / Compression Helper | Not yet |
| 7 | Sequential Statistical Promotion Gate Helper | Not yet |
| 8 | Object Graph Correspondence Helper | Not yet |

## 4. Input model

```python
helper_input = {
    "task_id": str,
    "train_examples": list[dict],  # Input/output pairs
    "test_input_descriptor": dict,
    "candidate_grammars": list[dict],
    "candidate_predictions": list[dict],
    "ledger_rejection_context": dict | None,
    "allowed_evidence_scope": "train_only",  # Fixed
    "hidden_test_output_available": False,     # Fixed
    "synthetic_probe_results_allowed": False, # Fixed
}
```

## 5. Candidate grammar model

```python
candidate_grammar = {
    "grammar_id": str,
    "private_language": str,
    "target_selection_rule": str,
    "action_rule": str,
    "representation_rule": str,
    "claimed_train_support": list[str],  # Indices of train examples
    "predicted_test_output_descriptor": dict,
    "known_rivals": list[str],  # IDs of rival grammars
    "assumptions": list[str],  # Hidden assumptions
}
```

## 6. Constraint checks

| Check | Description |
|-------|-------------|
| target_consistency | Does grammar predict correct target for all train inputs? |
| action_consistency | Does grammar predict correct action for all train inputs? |
| representation_consistency | Does grammar predict correct representation for all train inputs? |
| train_io_consistency | Do predicted outputs match train outputs? |
| contradiction_check | Does any train example contradict grammar? |
| unexplained_feature_check | Does grammar leave any train output feature unexplained? |
| rival_survival | Are rival grammars still consistent with train? |
| underdetermination_check | Do multiple grammars remain consistent? |
| forced_uniqueness | Does train evidence force a unique output? |

## 7. Rival grammar handling

### Required cases

| Case | Condition | Output |
|------|-----------|--------|
| One grammar consistent | 1 grammar consistent, all rivals eliminated by train | candidate_deserved_if_unique_and_forced |
| Multiple grammars consistent | 2+ grammars consistent | rival_grammar_alive / underdetermined |
| All grammars eliminated | No grammar consistent | all_grammars_eliminated / unsafe |
| Unsupported assumption | Grammar consistent but assumes unsupported input | candidate_not_deserved |

### Core law
Rival grammars are preserved unless train evidence eliminates them. No aesthetic, simplicity, or probe-based elimination.

## 8. Ledger integration boundary

### May say (evidence-status diagnostics)
- "Grammar A is consistent with all train examples."
- "Grammar B is eliminated by train example 2 due to target mismatch."
- "Grammar A and B both remain alive; output is underdetermined."
- "No grammar is consistent with train evidence."
- "Exactly one grammar is forced by train evidence."

### May NOT say (final answer authority)
- "Choose A."
- "A is likely."
- "A is simpler, therefore deserved."
- "A passed more probes."
- "A deserves forward application."

Final answer authority remains with the ledger.

## 9. Anti-laundering laws

1. **Train evidence only eliminates grammars** — Probe failures don't count
2. **Synthetic probes cannot eliminate grammars** — Probe results are non-evidential
3. **Consistency is not proof of truth** — Consistency ≠ correctness
4. **Uniqueness must be forced by train evidence** — Not by confidence scoring
5. **Helper does not rank grammars** — No scores, no rankings
6. **Helper does not create evidence** — Train-only, no probe laundering
7. **Helper does not repair grammar** — No grammar modification
8. **Helper does not generate final answers** — Ledger retains authority

## 10. Metrics design

| Metric | Description |
|--------|-------------|
| candidate_grammar_count | Total candidate grammars |
| grammar_consistent_count | Grammars consistent with train |
| grammar_eliminated_count | Grammars eliminated by train |
| rival_grammar_alive_count | Rival grammars still alive |
| underdetermined_count | Tasks with multiple alive grammars |
| all_eliminated_count | Tasks with no consistent grammar |
| forced_unique_candidate_count | Tasks with forced unique grammar |
| unsupported_assumption_count | Grammars with unsupported assumptions |
| contradiction_count | Train examples contradicting grammars |
| train_only_elimination_count | Eliminations by train only |
| synthetic_probe_elimination_attempt_blocked_count | Blocked probe-based elimination |
| deserved_candidate_count | Grammars that may deserve answer |
| candidate_not_deserved_count | Grammars that don't deserve answer |

## 11. Relationship to helper 2

Helper 2 (Ledger-Guided Micro-Theory Retry Loop) and Helper 3 (Constraint Satisfaction) work together:

| Aspect | Helper 2 | Helper 3 |
|--------|----------|----------|
| Trigger | Ledger rejects candidate | Called as diagnostic or after retry |
| Output | Retry constraint | Consistency diagnostics |
| Authority | Ledger gate preserved | Ledger gate preserved |
| Evidence | Constraint, not evidence | Train-only consistency check |

**Flow**:
1. Helper 2 gives rejection reason and retry constraint
2. Helper 3 evaluates whether retry grammars satisfy train-only constraints
3. Helper 3 reports: consistent / eliminated / rival_alive / underdetermined
4. Helper 3 does NOT replace ledger — it strengthens ledger's evidence review
5. Final answer authority remains with ledger

## 12. Recommended next safe local follow-up
`IMPLEMENT_ARC_CONSTRAINT_SATISFACTION_RIVAL_GRAMMAR_HELPER_V1`

Rationale:
- Design is clean and bounded
- Mathematical grounding is explicit (CSP, SAT/SMT, finite model checking)
- Anti-laundering laws prevent evidence laundering
- Ledger boundary preserved — helper is diagnostic only
- Metrics design is comprehensive
- No helper integration into solver

---
Helper roadmap count: 3/8
Mathematical grounding included: yes (CSP, SAT/SMT, finite model checking)
Input model defined: yes
Candidate grammar model defined: yes
Constraint checks defined: yes (9 checks)
Rival grammar handling defined: yes
Ledger boundary preserved: yes
Anti-laundering laws included: yes (8 laws)
Metrics defined: yes (13 metrics)
Validation: PASS
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_constraint_satisfaction_rival_grammar_helper_design_ready