# WESLR ARC CONTROLLED ANSWER CANDIDATE GENERATOR DESIGN V1

## 1. Executive verdict
`arc_controlled_answer_candidate_generator_design_ready`

## 2. Purpose

The **Controlled Answer Candidate Generator** bridges diagnostic output → candidate output descriptor.

**Why it exists:**
- V5 showed diagnostics produce 0 exact answers
- Ledger Deservedness Assembler cannot approve without candidates
- Helpers 1-8 produce diagnostics, not candidates
- This generator creates candidate descriptors from forced constraints

**Core principle:**
> Generator creates candidates, NOT final answers. Every candidate must pass through ledger deservedness assembler.

---

## 3. Input Model

```python
{
    "task_id": str,
    "train_examples": [...],
    "test_input_descriptor": {...},
    "forced_constraints": [...],
    "train_forced_transformations": [...],
    "object_graph_correspondences": [...],
    "invariant_preserving_transformations": [...],
    "relation_first_rewrites": [...],
    "composed_transform_candidates": [...],
    "explicit_candidate_grammars": [...],
    "unresolved_rival_grammars": [...],
    "unsupported_assumption_list": [...],
    "helper_diagnostics": {
        "helper_1_relation_first": {...},
        "helper_2_retry_loop": {...},
        "helper_3_constraint": {...},
        "helper_4_divergence": {...},
        "helper_5_invariant_symmetry": {...},
        "helper_6_mdl": {...},
        "helper_7_promotion": {...},
        "helper_8_object_graph": {...},
    }
}
```

---

## 4. Candidate Construction Modes

### Mode 1: relation_first_rewrite_candidate
- **Required inputs**: relation_first_rewrite from Helper 1
- **Allowed constraints**: train-forced relations only
- **Blocked assumptions**: guessed relations, non-train relations
- **Trace**: requires step_id, source_helper="helper_1", train_support=True

### Mode 2: object_correspondence_candidate
- **Required inputs**: object graph correspondence from Helper 8
- **Allowed constraints**: train-evidence-backed object mappings
- **Blocked assumptions**: ambiguous mappings, unforced correspondences
- **Trace**: requires step_id, source_helper="helper_8", correspondence_type="train_forced"

### Mode 3: invariant_preserving_candidate
- **Required inputs**: invariant/symmetry from Helper 5
- **Allowed constraints**: preserved invariants with train support
- **Blocked assumptions**: plausible but unforced invariants
- **Trace**: requires step_id, source_helper="helper_5", train_support=True

### Mode 4: composed_transform_candidate
- **Required inputs**: composed transforms where each component has train support
- **Allowed constraints**: train-supported component transforms
- **Blocked assumptions**: invented compositions, unverified sequences
- **Trace**: requires step_id for each component, all train_support=True

### Mode 5: train_forced_transformation_candidate
- **Required inputs**: transformation directly evidenced in train examples
- **Allowed constraints**: train input→output mapping
- **Blocked assumptions**: extrapolations beyond train support
- **Trace**: requires step_id, source="train_example", train_support=True

### Mode 6: explicit_grammar_candidate
- **Required inputs**: explicit grammar with train-derived rules
- **Allowed constraints**: train-derived rule applications
- **Blocked assumptions**: invented rules, elegance-only selection
- **Trace**: requires step_id, rule_source="train", train_support=True

### Mode 7: partial_candidate_descriptor
- **Purpose**: When candidate is plausible but incomplete
- **Output**: Partial descriptor with gaps identified
- **Required**: gap_analysis, unsupported_components
- **Always requires ledger review**: Yes

---

## 5. Candidate Descriptor Model

```python
{
    "candidate_id": str,                    # Unique per task
    "task_id": str,
    "construction_mode": str,              # One of 7 modes
    "output_shape_descriptor": {...},       # Grid dimensions
    "object_operations": [...],            # Object transformations
    "color_operations": [...],             # Color transformations
    "spatial_operations": [...],           # Spatial transformations
    "relation_operations": [...],         # Relation transformations
    "invariant_preservation_claims": [...], # Invariant claims
    "object_correspondence_claims": [...], # Correspondence claims
    "source_constraints": [...],           # Constraints used
    "unsupported_assumptions": [...],      # Assumptions without train support
    "unresolved_rivals": [...],            # Unresolved rival grammars
    "construction_trace": [...],          # Step-by-step trace
    "requires_ledger_review": True,       # ALWAYS TRUE
    "treated_as_final_answer": False,     # ALWAYS FALSE
    "generation_status": "generated" | "partial" | "blocked",
    "block_reason": str | None,            # If blocked
}
```

---

## 6. Construction Trace Model

```python
{
    "step_id": int,
    "source_helper": str,                  # Which helper provided input
    "source_constraint": str,               # Constraint used
    "operation": str,                      # Operation performed
    "train_support": bool,                  # Has train evidence?
    "assumption_status": "forced" | "plausible" | "unsupported",
    "rival_impact": "none" | "narrows" | "unresolved",
    "ledger_relevance": "required" | "advisory" | "none",
    "evidence_status": "train_explicit" | "train_implied" | "none",
}
```

---

## 7. Blocking Rules

Generation MUST be blocked if:

| Condition | Block | Reason |
|-----------|-------|--------|
| No forced constraints exist | YES | Cannot generate without train support |
| Unresolved rivals > 1 | YES | Different outputs possible |
| Object correspondence ambiguous | YES | Multiple valid mappings |
| Invariant/symmetry plausible but not forced | YES | Not uniquely determined |
| MDL simplicity is only reason | YES | Elegance ≠ proof |
| Transformation requires unsupported assumption | YES | Guessing |
| Hidden test output requested | YES | Evidence laundering |
| Public ARC answer requested | YES | Evidence laundering |
| Would bypass ledger | YES | Safety boundary |

---

## 8. Relationship to Ledger Deservedness Assembler

```
[Helper Diagnostics] → [Controlled Candidate Generator] → [Candidate Descriptors]
                                                                         |
                                                                         v
                                                              [Ledger Deservedness Assembler]
                                                                         |
                                                                         v
                                                         [candidate_deserved | candidate_not_deserved]
```

**Key relationships:**
- Generator proposes candidate descriptors
- Assembler decides deservedness
- Generator NEVER grants deservedness
- Assembler may reject ALL candidates
- Safe failure remains allowed and expected

**Flow:**
1. Generator produces candidate_descriptor (not final answer)
2. Generator marks `requires_ledger_review = True`
3. Generator marks `treated_as_final_answer = False`
4. Candidate goes to Assembler
5. Assembler checks train evidence + diagnostics
6. Assembler returns decision

---

## 9. Relationship to Rehearsal Learning Recorder

```
[Controlled Candidate Generator] → [Rehearsal Recorder]
                                         |
                                         v
                              [Logs all candidates]
                              [Logs rejected candidates]
                              [Logs missing constraints]
                              [Logs repeated failures]
                              [Tracks memorization risk]
```

**Recorder logs:**
- candidate_generated
- candidate_rejected_by_assembler
- missing_constraint_that_blocked
- repeated_failure_pattern
- memorization_risk_flag
- fresh_holdout_result

**Recorder does NOT:**
- Mutate solver
- Write ".weslr"
- Promote behavior packs

---

## 10. Rehearsal/Holdout Policy

| Set | Candidate Generation | Counts to 85%? |
|-----|---------------------|----------------|
| Rehearsal | May generate | No |
| Mutation/Design | May generate | No |
| Fresh Holdout | May generate | **Yes** |
| Promotion | May generate | Yes (final) |

**Rules:**
- Generated answers on rehearsal tasks may inform repair hypotheses
- Fresh holdout counts only if NO answer leakage occurred
- Repeated same-task exactness does NOT count toward threshold
- Fresh variant exactness counts toward threshold
- Holdout answers must NOT be used for training

---

## 11. Anti-Laundering Laws

1. **Candidate generation is not final answering** — Candidates are NOT final answers
2. **Every candidate requires ledger review** — Generator cannot self-approve
3. **Hidden test output cannot be used** — Evidence laundering blocked
4. **Public ARC answers cannot be used** — Evidence laundering blocked
5. **Repeated rehearsal cannot create deservedness** — Memorization ≠ proof
6. **MDL/elegance cannot choose a candidate alone** — Simplicity ≠ proof
7. **Ambiguous correspondence blocks generation** — Multiple valid = block
8. **Unresolved rivals block unique generation** — Different outputs possible
9. **Unforced invariant blocks unique generation** — Not uniquely determined
10. **Unsupported assumptions block generation** — Guessing is blocked
11. **Holdout answers cannot train the generator** — Leakage prevention
12. **Generator cannot mutate solver behavior** — Safety boundary

---

## 12. Metrics Design

### Generation Metrics
| Metric | Description |
|--------|-------------|
| candidate_generation_attempt_count | Total generation attempts |
| candidate_generated_count | Successfully generated |
| candidate_generation_blocked_count | Blocked by rules |

### Review Metrics
| Metric | Description |
|--------|-------------|
| candidate_requires_ledger_review_count | All candidates need review |
| ledger_review_required_count | Same as above |

### Blocking Metrics
| Metric | Description |
|--------|-------------|
| safe_failure_required_count | Generation resulted in safe failure |
| unsupported_assumption_blocked_count | Blocked due to unsupported assumptions |
| unresolved_rival_blocked_count | Blocked due to rivals |
| ambiguous_correspondence_blocked_count | Blocked due to ambiguity |
| unforced_invariant_blocked_count | Blocked due to unforced invariant |
| mdl_only_choice_blocked_count | Blocked due to MDL-only selection |
| hidden_test_request_blocked_count | Blocked hidden test request |
| public_answer_request_blocked_count | Blocked public answer request |

### Safety Metrics
| Metric | Description |
|--------|-------------|
| candidate_treated_as_final_answer_count | Safety violation |
| construction_trace_complete_count | Trace completeness |
| memorization_risk_flag_count | Memorization detected |

---

## 13. Recommended Next Safe Local Follow-up

**`IMPLEMENT_ARC_CONTROLLED_ANSWER_CANDIDATE_GENERATOR_V1`**

Rationale:
- Design is complete and ready
- All 7 construction modes defined
- Blocking rules enforced
- Relationship to assembler defined
- Relationship to recorder defined
- Metrics defined

**NOT recommended:**
- Runtime wiring (safety boundary)
- Internal 120 (not authorized)
- Public ARC data (forbidden in this lane)

---

Controlled generator designed: yes
Candidate construction modes defined: yes (7 modes)
Candidate descriptor model defined: yes
Construction trace model defined: yes
Blocking rules defined: yes (9 rules)
Ledger assembler relationship defined: yes
Rehearsal recorder relationship defined: yes
Rehearsal/holdout policy defined: yes
Anti-laundering laws defined: yes (12 laws)
Metrics defined: yes (16 metrics)
Recommended next lane: IMPLEMENT_ARC_CONTROLLED_ANSWER_CANDIDATE_GENERATOR_V1
Validation: PASS
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_controlled_answer_candidate_generator_design_ready