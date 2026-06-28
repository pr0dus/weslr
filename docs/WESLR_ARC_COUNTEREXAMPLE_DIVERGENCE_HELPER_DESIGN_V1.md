# WESLR ARC COUNTEREXAMPLE DIVERGENCE HELPER DESIGN V1

## 1. Executive verdict
`arc_counterexample_divergence_helper_design_ready`

## 2. Purpose and mathematical grounding

### Purpose
Design a pure helper that identifies where candidate grammars diverge from each other by generating counterexample-style shadow cases.

### Mathematical Grounding
- **Counterexample-guided inductive synthesis (CEGIS)**: Generate discriminating cases
- **Model checking / falsification**: Find conditions that falsify a grammar
- **Proof by counterexample**: Show grammar inadequacy
- **Property-based testing**: Test grammars against edge cases
- **Discriminating examples**: Find minimal differences
- **Version-space reduction**: Narrow the space of viable grammars

## 3. Helper roadmap position

| # | Helper | Status |
|---|--------|--------|
| 1 | Relation-First Compiler Helper | Complete |
| 2 | Ledger-Guided Micro-Theory Retry Loop Helper | Complete (functional run) |
| 3 | Constraint Satisfaction / Rival Grammar Helper | Complete (functional run) |
| 4 | **Counterexample / Divergence Helper** | **Current lane** |
| 5 | Invariant / Symmetry Helper | Not yet |
| 6 | Minimum Description Length / Compression Helper | Not yet |
| 7 | Sequential Statistical Promotion Gate Helper | Not yet |
| 8 | Object Graph Correspondence Helper | Not yet |

## 4. Input model

```python
helper_input = {
    "task_id": str,
    "train_examples": list[dict],
    "test_input_descriptor": dict,
    "candidate_grammars": list[dict],
    "rival_grammar_pairs": list[tuple[str, str]],
    "allowed_shadow_case_scope": str,  # "train_derived" only
    "ledger_rejection_context": dict | None,
    "constraint_helper_status": dict | None,
    "allowed_evidence_scope": "train_only",  # Fixed
    "synthetic_probe_results_allowed_as_evidence": False,  # Fixed
    "hidden_test_output_available": False,  # Fixed
}
```

## 5. Candidate grammar comparison model

```python
grammar_comparison = {
    "grammar_a_id": str,
    "grammar_b_id": str,
    "shared_train_support": list[str],
    "known_difference_axis": str,
    "predicted_output_a_descriptor": dict,
    "predicted_output_b_descriptor": dict,
    "divergence_condition": dict | None,
    "train_evidence_resolution_status": str,  # "resolved" / "unresolved"
}
```

## 6. Divergence axes

| Axis | Description |
|------|-------------|
| target_selection_divergence | Grammars select different targets |
| action_divergence | Grammars propose different actions |
| representation_divergence | Grammars use different representations |
| object_correspondence_divergence | Grammars map objects differently |
| symmetry_divergence | Grammars handle symmetry differently |
| negative_evidence_divergence | Grammars explain absence differently |
| boundary_condition_divergence | Grammars handle boundaries differently |
| coordinate_vs_relation_divergence | Grammars prefer coordinate vs relation |
| helper_trap_divergence | Grammars fall into helper traps differently |
| beautiful_wrong_rule_divergence | Grammars accept beautiful wrong differently |

## 7. Counterexample / shadow-case design

### Shadow case structure

```python
shadow_case = {
    "shadow_case_id": str,
    "description": str,
    "minimal_condition_changed": dict,
    "grammar_a_prediction": dict,
    "grammar_b_prediction": dict,
    "divergence_detected": bool,
    "uses_train_evidence_only": bool,  # True
    "treated_as_evidence": False,  # Core law
    "may_eliminate_grammar": False,  # Core law
    "may_raise_confidence": False,  # Core law
}
```

### Core law
The helper may generate a shadow case where grammars differ. It may NOT claim which grammar is correct unless train evidence already resolves it.

## 8. Train-evidence resolution rule

| Condition | Output |
|-----------|--------|
| Train evidence contradicts one grammar | "train_evidence_resolves_divergence" |
| Only synthetic shadow case separates grammars | "train_evidence_does_not_resolve_divergence" |
| Divergence affects test prediction AND train doesn't resolve | "safe_failure_recommended" |

## 9. Ledger integration boundary

### May say (diagnostic)
- "Grammar A and Grammar B diverge under this minimal condition."
- "Train evidence does not resolve the divergence."
- "The divergence affects the test prediction."
- "Safe failure is recommended."

### May NOT say (final answer authority)
- "Choose Grammar A."
- "Grammar A is more likely."
- "Grammar A passed the counterexample."
- "The counterexample proves truth."
- "Generate final answer."

Final answer authority remains with the ledger.

## 10. Anti-laundering laws

1. **Counterexample is diagnostic, not evidence** — Probe results don't prove truth
2. **Synthetic shadow case is not train evidence** — Only train evidence can eliminate
3. **Divergence does not crown a winner** — Probe survival doesn't mean correctness
4. **Probe survival does not increase truth** — Surviving probe ≠ proven grammar
5. **Train evidence alone may eliminate grammar** — Only train can eliminate
6. **Unresolved divergence blocks deservedness** — Can't claim answer if rivals remain
7. **Helper does not generate final answers** — Diagnostic only
8. **Helper does not repair grammar** — No modification
9. **Helper does not rank grammars** — No scoring
10. **Helper does not use hidden test output** — No leakage

## 11. Metrics design

| Metric | Description |
|--------|-------------|
| candidate_grammar_pair_count | Pairs compared |
| divergence_detected_count | Pairs with divergence |
| no_divergence_detected_count | Pairs without divergence |
| minimal_discriminating_condition_count | Minimal conditions found |
| train_resolved_divergence_count | Train evidence resolves |
| train_unresolved_divergence_count | Train evidence doesn't resolve |
| safe_failure_recommended_count | Safe failure recommended |
| counterexample_non_evidential_count | Counterexamples marked non-evidential |
| probe_elimination_blocked_count | Blocked probe-based elimination |
| probe_confidence_increase_blocked_count | Blocked confidence from probe |
| hidden_test_use_blocked_count | Blocked hidden test use |
| rival_grammar_preserved_count | Rivals preserved |
| ledger_boundary_preserved_count | Ledger authority preserved |

## 12. Relationship to helper 3

| Aspect | Helper 3 | Helper 4 |
|--------|----------|----------|
| Primary function | Consistency checking | Divergence detection |
| Input | Candidate grammars, train examples | Pairs of remaining grammars |
| Output | Consistent/eliminated/rival_alive | Divergence status |
| Elimination | Train evidence only | N/A (diagnostic only) |
| Authority | Ledger gate preserved | Ledger gate preserved |

**Flow**:
1. Helper 3 checks which grammars remain consistent with train evidence
2. Helper 4 checks whether remaining grammars diverge under nearby conditions
3. Helper 4 cannot eliminate grammars by probe
4. Helper 4 gives the ledger a reason to preserve underdetermination when divergence matters
5. Helper 4 strengthens safe failure, not final-answer generation

## 13. Recommended next safe local follow-up
`IMPLEMENT_ARC_COUNTEREXAMPLE_DIVERGENCE_HELPER_V1`

Rationale:
- Design is clean and bounded
- Mathematical grounding is explicit (CEGIS, model checking, falsification)
- Anti-laundering laws prevent evidence laundering
- Ledger boundary preserved — helper is diagnostic only
- Metrics design is comprehensive
- Relationship to helper 3 is clear and complementary

---
Helper roadmap count: 4/8
Mathematical grounding included: yes (CEGIS, model checking, falsification)
Input model defined: yes
Grammar comparison model defined: yes
Divergence axes defined: yes (10 axes)
Shadow-case design defined: yes
Train-evidence resolution rule defined: yes
Ledger boundary preserved: yes
Anti-laundering laws included: yes (10 laws)
Metrics defined: yes (13 metrics)
Relationship to helper 3 preserved: yes
Validation: PASS
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_counterexample_divergence_helper_design_ready