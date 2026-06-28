# WESLR ARC MINIMUM DESCRIPTION LENGTH COMPRESSION HELPER DESIGN V1

## 1. Executive verdict
`arc_mdl_compression_helper_design_ready`

## 2. Purpose and mathematical grounding

### Purpose
Design a pure helper that evaluates candidate grammars using compression / description-length diagnostics.

### Mathematical Grounding
- **Minimum Description Length (MDL)**: Model selection principle balancing fit and complexity
- **Algorithmic information theory**: Formal basis for compression reasoning
- **Kolmogorov-style compression reasoning**: Theoretical foundation for description length
- **Model selection penalties**: Complexity penalties for model selection
- **Occam bounds / parsimony principles**: Simplicity preference with evidence requirements
- **Regularization against arbitrary exception lists**: Penalty for exception-heavy grammars

## 3. Helper roadmap position

| # | Helper | Status |
|---|--------|--------|
| 1 | Relation-First Compiler Helper | Complete |
| 2 | Ledger-Guided Micro-Theory Retry Loop Helper | Complete (functional) |
| 3 | Constraint Satisfaction / Rival Grammar Helper | Complete (functional + repair) |
| 4 | Counterexample / Divergence Helper | Complete (functional + repair) |
| 5 | Invariant / Symmetry Helper | Complete (functional + repair) |
| 6 | **Minimum Description Length / Compression Helper** | **Current lane** |
| 7 | Sequential Statistical Promotion Gate Helper | Not yet |
| 8 | Object Graph Correspondence Helper | Not yet |

## 4. Input model

```python
helper_input = {
    "task_id": str,
    "train_examples": list[dict],
    "test_input_descriptor": dict,
    "candidate_grammars": list[dict],
    "constraint_helper_status": dict | None,
    "divergence_helper_status": dict | None,
    "invariant_symmetry_helper_status": dict | None,
    "allowed_evidence_scope": "train_only",  # Fixed
    "hidden_test_output_available": False,  # Fixed
    "synthetic_probe_results_allowed_as_evidence": False,  # Fixed
}
```

## 5. Grammar compression model

```python
grammar_compression = {
    "grammar_id": str,
    "rule_count": int,
    "primitive_count": int,
    "condition_count": int,
    "exception_count": int,
    "assumption_count": int,
    "special_case_count": int,
    "train_examples_explained": list[str],
    "train_examples_unexplained": list[str],
    "description_length_estimate": int,
    "overfit_markers": list[str],
    "underfit_markers": list[str],
    "treated_as_evidence": False,  # Core law
}
```

## 6. Description-length components

| Component | Description |
|-----------|-------------|
| base_rule_cost | Cost of base rules in grammar |
| primitive_operation_cost | Cost of primitive operations |
| condition_cost | Cost of conditional logic |
| exception_penalty | Penalty for each exception |
| unsupported_assumption_penalty | Penalty for unsupported assumptions |
| special_case_penalty | Penalty for special cases |
| unexplained_train_feature_penalty | Penalty for unexplained train features |
| invariant_symmetry_violation_penalty | Penalty for invariant/symmetry violations |
| rival_grammar_survival_penalty | Penalty if rivals remain train-consistent |
| underfit_penalty | Penalty for underfitting train |
| overfit_penalty | Penalty for overfitting |

## 7. Compression comparison rule

| Condition | Output |
|-----------|--------|
| One grammar shorter, rivals remain train-consistent | candidate_simpler_but_not_forced |
| Two grammars similar length | compression_tie |
| Grammar requires many exceptions | grammar_has_exception_penalty |
| Grammar relies on unsupported assumptions | grammar_has_assumption_penalty |
| Grammar compresses train but rivals alive | Do NOT treat as deserved |
| Compression preference conflicts with train evidence | Train evidence wins |

## 8. Relationship to helpers 3, 4, and 5

| Helper | Primary Function | Helper 6 Relationship |
|--------|------------------|----------------------|
| 3 | Train consistency + forced uniqueness | Helper 6 cannot eliminate rivals unless helper 3 says train eliminates |
| 4 | Divergence detection | Helper 6 cannot override unresolved divergence |
| 5 | Invariant/symmetry preservation | Helper 6 cannot turn elegant invariant from helper 5 into proof |
| 6 | MDL compression diagnostics | Works with 3, 4, 5 to order retry attention or flag overfitting |

**Flow**:
1. Helper 3 checks train consistency and forced uniqueness
2. Helper 4 exposes unresolved divergence
3. Helper 5 explains invariant/symmetry preservation or violation
4. Helper 6 flags simpler grammar, overfit grammar, or exception-heavy grammar
5. Helper 6 cannot replace ledger or train evidence authority

## 9. Ledger integration boundary

### May say (diagnostic)
- "Grammar A has shorter description length than Grammar B."
- "Grammar A uses fewer exceptions."
- "Grammar B looks overfit."
- "Grammar A is simpler but not forced."
- "Compression preference is diagnostic only."
- "Safe failure recommended."

### May NOT say (final answer authority)
- "Choose Grammar A."
- "Grammar A is true."
- "Grammar A deserves answer."
- "Compression proves the answer."
- "Generate final output."

Final answer authority remains with the ledger.

## 10. Anti-laundering laws

1. **Compression is diagnostic, not proof** — Don't assert truth
2. **Shorter grammar does not mean true** — Simplicity ≠ correctness
3. **MDL cannot create train evidence** — Only train can create evidence
4. **MDL cannot eliminate train-consistent rivals** — Train consistency required
5. **Compression preference cannot override underdetermination** — Underdetection wins
6. **Compression cannot raise confidence by itself** — No confidence increase
7. **Hidden test output cannot be compressed** — No leakage
8. **Synthetic probes cannot become evidence** — Probe ≠ train
9. **Helper does not rank for final answer authority** — No final ranking
10. **Helper does not generate final answers** — Diagnostic only

## 11. Metrics design

| Metric | Description |
|--------|-------------|
| candidate_grammar_count | Grammars evaluated |
| description_length_estimated_count | Description lengths computed |
| compression_preference_count | Compression preferences stated |
| compression_tie_count | Ties detected |
| exception_penalty_count | Exception penalties flagged |
| assumption_penalty_count | Assumption penalties flagged |
| special_case_penalty_count | Special case penalties flagged |
| overfit_risk_count | Overfit risks flagged |
| underfit_risk_count | Underfit risks flagged |
| candidate_simpler_but_not_forced_count | Simpler but unforced |
| train_consistent_rival_preserved_count | Rivals preserved |
| compression_confidence_increase_blocked_count | Confidence increase blocked |
| hidden_test_compression_blocked_count | Hidden test use blocked |
| synthetic_probe_compression_blocked_count | Synthetic probe blocked |
| safe_failure_recommended_count | Safe failure recommended |
| ledger_boundary_preserved_count | Ledger authority preserved |

## 12. Recommended next safe local follow-up
`IMPLEMENT_ARC_MINIMUM_DESCRIPTION_LENGTH_COMPRESSION_HELPER_V1`

Rationale:
- Design is clean and bounded
- Mathematical grounding is explicit (MDL, algorithmic information theory)
- Relationship to helpers 3, 4, and 5 is clear
- Anti-laundering laws prevent evidence laundering
- Ledger boundary preserved — helper is diagnostic only
- Metrics design is comprehensive

---
Helper roadmap count: 6/8
Mathematical grounding included: yes (MDL, algorithmic information theory, Kolmogorov)
Input model defined: yes
Grammar compression model defined: yes (12 fields)
Description-length components defined: yes (11 components)
Compression comparison rule defined: yes (6 rules)
Ledger boundary preserved: yes
Anti-laundering laws included: yes (10 laws)
Metrics defined: yes (16 metrics)
Relationship to helpers 3/4/5 preserved: yes
Validation: PASS
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_mdl_compression_helper_design_ready