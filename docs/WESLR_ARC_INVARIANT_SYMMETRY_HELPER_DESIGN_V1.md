# WESLR ARC INVARIANT SYMMETRY HELPER DESIGN V1

## 1. Executive verdict
`arc_invariant_symmetry_helper_design_ready`

## 2. Purpose and mathematical grounding

### Purpose
Design a pure helper that detects preserved structures, invariants, and symmetry relationships between train inputs and outputs.

### Mathematical Grounding
- **Group theory**: Study of symmetry operations and their properties
- **Invariants under transformation**: Properties that remain unchanged
- **Symmetry groups**: Sets of transformations preserving structure
- **Graph isomorphism / structural equivalence**: Structural correspondence
- **Equivalence relations**: Classification of objects by preserved properties
- **Conserved quantities**: Properties that don't change under operations
- **Transformation monoids**: Collections of transformations on a set
- **Orbit/stabilizer reasoning**: Track what changes vs what stays the same

## 3. Helper roadmap position

| # | Helper | Status |
|---|--------|--------|
| 1 | Relation-First Compiler Helper | Complete |
| 2 | Ledger-Guided Micro-Theory Retry Loop Helper | Complete (functional) |
| 3 | Constraint Satisfaction / Rival Grammar Helper | Complete (functional + repair) |
| 4 | Counterexample / Divergence Helper | Complete (functional + repair) |
| 5 | **Invariant / Symmetry Helper** | **Current lane** |
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
    "candidate_transformations": list[dict],
    "candidate_invariants": list[dict],
    "candidate_symmetries": list[dict],
    "constraint_helper_status": dict | None,
    "divergence_helper_status": dict | None,
    "allowed_evidence_scope": "train_only",  # Fixed
    "hidden_test_output_available": False,  # Fixed
    "synthetic_probe_results_allowed_as_evidence": False,  # Fixed
}
```

## 5. Invariant model

```python
invariant = {
    "invariant_id": str,
    "invariant_type": str,
    "description": str,
    "object_scope": str,
    "property_scope": str,
    "relation_scope": str,
    "train_support": list[str],
    "violating_train_examples": list[str],
    "forced_by_train_evidence": bool,
    "treated_as_evidence": False,  # Core law
}
```

### Supported invariant types
- object_count_invariant
- color_set_invariant
- shape_identity_invariant
- adjacency_invariant
- containment_invariant
- relative_position_invariant
- size_invariant
- parity_invariant
- boundary_contact_invariant
- component_connectivity_invariant
- negative_space_invariant
- relation_graph_invariant

## 6. Symmetry model

```python
symmetry = {
    "symmetry_id": str,
    "symmetry_type": str,
    "description": str,
    "transformation": dict,
    "preserved_properties": list[str],
    "broken_properties": list[str],
    "train_support": list[str],
    "violating_train_examples": list[str],
    "forced_by_train_evidence": bool,
    "treated_as_evidence": False,  # Core law
}
```

### Supported symmetry types
- reflection_horizontal
- reflection_vertical
- rotation_90
- rotation_180
- rotation_270
- translation
- scaling_discrete
- color_permutation
- object_permutation
- relation_preserving_map

## 7. Transformation preservation checks

| Check | Description |
|-------|-------------|
| object_count_preservation | Does transformation preserve object count? |
| color_preservation | Are colors preserved? |
| shape_preservation | Are shapes preserved? |
| adjacency_preservation | Are adjacency relations preserved? |
| containment_preservation | Are containment relations preserved? |
| relative_position_preservation | Are relative positions preserved? |
| connectivity_preservation | Is connectivity preserved? |
| symmetry_preservation | Is the symmetry preserved? |
| negative_evidence_preservation | Are negative spaces preserved? |
| boundary_preservation | Are boundaries preserved? |

## 8. Train-evidence forcing rule

| Condition | Output |
|-----------|--------|
| Every train supports invariant AND grammar preserves it | invariant_preserved |
| Grammar violates train-supported invariant | invariant_violated |
| Invariant plausible but not forced by train | candidate_invariant_not_forced |
| Multiple plausible invariants remain | safe_failure_recommended |

## 9. Ledger integration boundary

### May say (diagnostic)
- "This invariant is preserved across train examples."
- "This candidate grammar violates a train-supported invariant."
- "This symmetry is plausible but not forced."
- "Multiple invariant explanations remain alive."
- "Safe failure recommended."

### May NOT say (final answer authority)
- "Choose this grammar."
- "This symmetry proves the answer."
- "Elegant invariant means deserved answer."
- "Generate final output."

Final answer authority remains with the ledger.

## 10. Anti-laundering laws

1. **Invariant candidate is diagnostic, not final evidence** — Don't assert truth
2. **Symmetry elegance is not proof** — Aesthetic ≠ correctness
3. **Train evidence alone may force an invariant** — Only train can force
4. **Synthetic probes cannot force invariants** — Probe ≠ train
5. **Hidden test output cannot be used** — No leakage
6. **Invariant preservation is not truth proof** — Preservation ≠ correctness
7. **Invariant violation may block candidate only when train-supported** — Train-required violation
8. **Helper does not rank grammars** — No scoring
9. **Helper does not repair grammar** — No modification
10. **Helper does not generate final answers** — Diagnostic only

## 11. Metrics design

| Metric | Description |
|--------|-------------|
| candidate_invariant_count | Invariant candidates evaluated |
| invariant_detected_count | Invariants found in data |
| invariant_preserved_count | Grammars preserve invariants |
| invariant_violated_count | Grammars violate invariants |
| candidate_invariant_not_forced_count | Invariants not forced by train |
| candidate_symmetry_count | Symmetry candidates evaluated |
| symmetry_detected_count | Symmetries found in data |
| symmetry_preserved_count | Symmetries preserved |
| symmetry_violated_count | Symmetries violated |
| transformation_preserves_structure_count | Transforms preserve structure |
| transformation_breaks_structure_count | Transforms break structure |
| train_forced_invariant_count | Invariants forced by train |
| synthetic_probe_invariant_blocked_count | Blocked synthetic probe forcing |
| hidden_test_use_blocked_count | Blocked hidden test use |
| safe_failure_recommended_count | Safe failure recommended |
| ledger_boundary_preserved_count | Ledger authority preserved |

## 12. Relationship to helpers 3 and 4

| Helper | Primary Function | Helper 5 Relationship |
|--------|------------------|----------------------|
| 3 | Consistency checking | Helper 5 may explain violations |
| 4 | Divergence detection | Helper 5 may explain divergence source |
| 5 | Invariant/symmetry detection | Works with both to explain structure |

**Flow**:
1. Helper 3 checks which grammars remain train-consistent
2. Helper 4 checks whether grammars diverge under shadow conditions
3. Helper 5 explains WHY: which invariants/symmetries are preserved or violated
4. Helper 5 may recommend safe failure if invariants ambiguous or not forced
5. Helper 5 does NOT replace ledger, helper 3, or helper 4

## 13. Recommended next safe local follow-up
`IMPLEMENT_ARC_INVARIANT_SYMMETRY_HELPER_V1`

Rationale:
- Design is clean and bounded
- Mathematical grounding is explicit (group theory, invariants)
- Relationship to helpers 3 and 4 is clear
- Anti-laundering laws prevent evidence laundering
- Ledger boundary preserved — helper is diagnostic only
- Metrics design is comprehensive

---
Helper roadmap count: 5/8
Mathematical grounding included: yes (group theory, invariants, symmetry)
Input model defined: yes
Invariant model defined: yes (12 types)
Symmetry model defined: yes (10 types)
Transformation checks defined: yes (10 checks)
Train-evidence forcing rule defined: yes
Ledger boundary preserved: yes
Anti-laundering laws included: yes (10 laws)
Metrics defined: yes (16 metrics)
Relationship to helpers 3 and 4 preserved: yes
Validation: PASS
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_invariant_symmetry_helper_design_ready