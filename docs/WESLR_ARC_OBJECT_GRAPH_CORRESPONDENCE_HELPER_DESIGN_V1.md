# WESLR ARC OBJECT GRAPH CORRESPONDENCE HELPER DESIGN V1

## 1. Executive verdict
`arc_object_graph_correspondence_helper_design_ready`

## 2. Purpose and mathematical grounding

### Purpose
Design a pure helper that maps objects, roles, and relations across train input/output pairs and test input descriptors.

### Mathematical Grounding
- **Graph theory**: Nodes (objects) and edges (relations)
- **Graph matching**: Finding structural correspondences between graphs
- **Bipartite matching**: One-to-one mappings between object sets
- **Graph isomorphism / subgraph isomorphism**: Structural equivalence detection
- **Relational structures**: Preserved/changed relations between objects
- **Labeled graphs**: Objects with attributes as node labels
- **Role assignment**: Mapping objects to functional roles
- **Constraint-based matching**: Matching under train constraints
- **Equivalence classes**: Objects belonging to same equivalence class
- **Partial bijections / partial correspondences**: Incomplete mappings

## 3. Helper roadmap position

| # | Helper | Status |
|---|--------|--------|
| 1 | Relation-First Compiler Helper | Complete |
| 2 | Ledger-Guided Micro-Theory Retry Loop Helper | Complete (functional) |
| 3 | Constraint Satisfaction / Rival Grammar Helper | Complete (functional + repair) |
| 4 | Counterexample / Divergence Helper | Complete (functional + repair) |
| 5 | Invariant / Symmetry Helper | Complete (functional + repair) |
| 6 | Minimum Description Length / Compression Helper | Complete (functional) |
| 7 | Sequential Statistical Promotion Gate Helper | Complete (functional) |
| 8 | **Object Graph Correspondence Helper** | **Current lane** |

## 4. Input model

```python
helper_input = {
    "task_id": str,
    "train_examples": list[dict],
    "test_input_descriptor": dict,
    "candidate_grammars": list[dict],
    "candidate_object_graphs": list[dict],
    "candidate_correspondences": list[dict],
    "constraint_helper_status": dict | None,
    "divergence_helper_status": dict | None,
    "invariant_symmetry_helper_status": dict | None,
    "mdl_helper_status": dict | None,
    "allowed_evidence_scope": "train_only",  # Fixed
    "hidden_test_output_available": False,  # Fixed
    "synthetic_probe_results_allowed_as_evidence": False,  # Fixed
}
```

## 5. Object graph model

```python
object_graph = {
    "graph_id": str,
    "objects": list[dict],
    "object_attributes": dict,
    "relations": list[dict],
    "relation_types": list[str],
    "connected_components": list[list[str]],
    "graph_scope": str,
    "source_example_id": str,
    "treated_as_evidence": False,  # Core law
}
```

### Supported object attributes
- color
- size
- shape_signature
- bounding_box
- centroid
- area
- perimeter
- component_id
- boundary_contact
- symmetry_signature
- role_label

### Supported relation types
- adjacency
- containment
- above_below
- left_right
- distance
- alignment
- same_color
- same_shape
- same_size
- touches_boundary
- inside_outside
- relative_order

## 6. Correspondence model

```python
correspondence = {
    "correspondence_id": str,
    "source_object_id": str,
    "target_object_id": str,
    "mapping_type": str,
    "role_preserved": bool,
    "attributes_preserved": list[str],
    "attributes_changed": list[str],
    "relations_preserved": list[str],
    "relations_changed": list[str],
    "train_support": list[str],
    "violating_train_examples": list[str],
    "forced_by_train_evidence": bool,
    "ambiguous_with": list[str],
    "treated_as_evidence": False,  # Core law
}
```

### Supported mapping types
- identity_mapping
- move_mapping
- recolor_mapping
- copy_mapping
- delete_mapping
- create_mapping
- complete_mapping
- mirror_mapping
- rotate_mapping
- expand_contract_mapping
- relation_role_mapping
- partial_mapping

## 7. Correspondence checks

| Check | Description |
|-------|-------------|
| object_identity_preservation | Same object identity across transformation |
| object_role_preservation | Role preserved across transformation |
| attribute_preservation | Attributes preserved or changed |
| relation_preservation | Relations preserved or changed |
| one_to_one_mapping | Single source to single target |
| one_to_many_mapping | Single source to multiple targets |
| many_to_one_mapping | Multiple sources to single target |
| partial_mapping | Incomplete mapping |
| subgraph_correspondence | Subgraph structure correspondence |
| ambiguous_mapping | Multiple possible mappings |
| train_forced_mapping | Train evidence forces mapping |
| unsupported_assumption | Unsupported mapping assumption |
| candidate_violation | Grammar violates correspondence |

## 8. Train-evidence forcing rule

| Condition | Output |
|-----------|--------|
| Every train supports mapping + no rival remains | object_correspondence_forced_by_train |
| Multiple mappings remain compatible with train | object_correspondence_ambiguous |
| Grammar violates train-supported correspondence | candidate_violates_correspondence |
| Only partial mapping is supported | partial_mapping_detected |
| Ambiguity affects test prediction | safe_failure_recommended |

## 9. Relationship to helpers 3–6

| Helper | Primary Function | Helper 8 Relationship |
|--------|------------------|----------------------|
| 3 | Train consistency | Cannot override underdetermination |
| 4 | Divergence detection | Cannot override unresolved divergence |
| 5 | Invariant/symmetry | Cannot override unforced invariant |
| 6 | MDL compression | Cannot use non-evidential compression |
| 8 | Object correspondence | Adds object-level graph mapping |

**Flow**:
1. Helper 3 checks train consistency and forced uniqueness
2. Helper 4 exposes unresolved divergence
3. Helper 5 identifies invariant/symmetry issues
4. Helper 6 flags compression/overfit diagnostics
5. Helper 8 adds object-level graph correspondence
6. Helper 8 explains why candidate violates train-supported object roles
7. Helper 8 recommends safe failure when ambiguity affects test prediction

## 10. Ledger integration boundary

### May say (diagnostic)
- "Object A corresponds to Object B across train examples."
- "This correspondence is forced by train evidence."
- "This correspondence is ambiguous."
- "Candidate grammar violates train-supported correspondence."
- "Safe failure recommended due to ambiguous object mapping."

### May NOT say (final answer authority)
- "Choose this grammar."
- "Object match proves the answer."
- "Generate final output."
- "Mapping elegance creates deservedness."
- "Hidden test mapping is inferred."

Final answer authority remains with the ledger.

## 11. Anti-laundering laws

1. **Object correspondence is diagnostic, not final proof** — Don't assert truth
2. **Graph match does not prove truth** — Structure ≠ correctness
3. **Train evidence alone may force correspondence** — Only train can force
4. **Ambiguous mappings block deservedness** — Ambiguity prevents authority
5. **Synthetic probes cannot force correspondence** — Probe ≠ train
6. **Hidden test output cannot be used** — No leakage
7. **Correspondence cannot raise confidence by itself** — No confidence increase
8. **Helper does not rank grammars** — No scoring
9. **Helper does not repair grammars** — No modification
10. **Helper does not generate final answers** — Diagnostic only
11. **Partial mapping is not complete proof** — Incomplete ≠ certain
12. **Mapping elegance is not evidence** — Aesthetic ≠ correctness

## 12. Metrics design

| Metric | Description |
|--------|-------------|
| candidate_object_graph_count | Object graphs evaluated |
| candidate_correspondence_count | Correspondence candidates evaluated |
| object_correspondence_detected_count | Correspondences found |
| object_correspondence_forced_count | Forced by train evidence |
| object_correspondence_ambiguous_count | Ambiguous mappings |
| role_correspondence_detected_count | Role mappings found |
| relation_preserved_count | Relations preserved |
| relation_changed_count | Relations changed |
| partial_mapping_detected_count | Partial mappings |
| bijection_detected_count | One-to-one mappings |
| subgraph_match_detected_count | Subgraph matches |
| candidate_violates_correspondence_count | Grammar violations |
| unsupported_mapping_assumption_count | Unsupported assumptions |
| safe_failure_recommended_count | Safe failures recommended |
| hidden_test_mapping_blocked_count | Hidden test use blocked |
| synthetic_probe_mapping_blocked_count | Synthetic probe blocked |
| ledger_boundary_preserved_count | Ledger authority preserved |

## 13. Recommended next safe local follow-up
`IMPLEMENT_ARC_OBJECT_GRAPH_CORRESPONDENCE_HELPER_V1`

Rationale:
- Design is clean and bounded
- Mathematical grounding is explicit (graph theory, matching)
- Relationship to helpers 3–6 is clear
- Anti-laundering laws prevent evidence laundering
- Ledger boundary preserved — helper is diagnostic only
- This completes the helper roadmap 8/8

---
Helper roadmap count: 8/8 (COMPLETE)
Mathematical grounding included: yes (graph theory, matching, isomorphism)
Input model defined: yes
Object graph model defined: yes (11 attributes, 12 relation types)
Correspondence model defined: yes (12 mapping types)
Correspondence checks defined: yes (13 checks)
Train-evidence forcing rule defined: yes (5 rules)
Ledger boundary preserved: yes
Anti-laundering laws included: yes (12 laws)
Metrics defined: yes (17 metrics)
Relationship to helpers 3-6 preserved: yes
Validation: PASS
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_object_graph_correspondence_helper_design_ready