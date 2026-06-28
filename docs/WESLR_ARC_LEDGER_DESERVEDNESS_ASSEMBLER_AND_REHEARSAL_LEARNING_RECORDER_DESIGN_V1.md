# WESLR ARC LEDGER DESERVEDNESS ASSEMBLER AND REHEARSAL LEARNING RECORDER DESIGN V1

## 1. Executive verdict
`arc_ledger_deservedness_assembler_rehearsal_recorder_design_ready`

## 2. V5 Result Interpretation

**V5 findings explained:**

| V5 Question | Answer |
|-------------|--------|
| Why exact = 0? | Diagnostic-only helpers, no answer generation |
| Why deserved = 0? | No assembler to check train-forced uniqueness |
| Why undeserved blocked = 0? | No candidates generated to block |

**Missing bridges exposed:**
- `ledger_deservedness_assembler` — checks if train evidence forces uniqueness
- `controlled_answer_candidate_generator` — safe candidate construction from forced constraints

**This design addresses both gaps.**

---

## 3. Ledger Deservedness Assembler Design

### Purpose
The assembler receives diagnostic output from the helper stack and determines whether any candidate deserves ledger approval.

### Input (from helpers)
```python
{
    "helper_diagnostics": {...},           # All helper outputs
    "candidate_grammars": [...],           # Grammar candidates
    "forced_constraints": [...],          # Train-forced constraints
    "train_evidence_support": {...},       # Train output alignment
    "unresolved_rival_grammars": [...],    # Multiple grammars
    "ambiguity_flags": {...},               # Ambiguity detected
    "invariant_symmetry_findings": [...],  # Invariant/symmetry
    "object_correspondence_findings": [...], # Object mappings
    "mdl_diagnostics": {...},              # MDL signals
    "divergence_findings": [...],           # Counterexample results
    "constraint_findings": {...},          # Constraint satisfaction
}
```

### Output (to ledger)
```python
{
    "decision": "candidate_deserved" | "candidate_not_deserved" | "safe_failure_required",
    "candidate_descriptor": {...},          # If candidate_deserved
    "deservedness_traces": [...],           # Why it deserves
    "forced_unique_output_available": bool,
    "unresolved_rivals": [...],
    "insufficient_train_evidence": bool,
    "needs_candidate_generation": bool,
    "ledger_review_required": bool,
}
```

### Core Law
> **A candidate can become deserved only if train evidence plus diagnostics force a unique output or a bounded top candidate under the local synthetic policy.**

**What CAN create deservedness:**
- Train evidence forces a unique output
- Object correspondence maps to unique output
- Invariant/symmetry forces specific transformation
- Relation-first rewrite produces unique result
- Composed transforms have only one valid execution

**What CANNOT create deservedness:**
- Repeated rehearsal alone
- Elegance/beauty alone
- MDL simplicity alone
- Helper preference alone
- Rival grammar without train evidence

### Decision Logic
```
IF train evidence forces unique output:
    -> candidate_deserved
ELIF forced constraints + limited candidates <= N:
    -> candidate_deserved (bounded)
ELIF ambiguity detected:
    -> safe_failure_required
ELIF unresolved rivals > 1:
    -> candidate_not_deserved
ELIF insufficient train evidence:
    -> safe_failure_required
ELSE:
    -> candidate_not_deserved
```

---

## 4. Controlled Answer Candidate Generator Boundary

### Purpose
Generate candidate outputs from forced constraints WITHOUT guessing.

### Inputs (from assembler)
```python
{
    "train_forced_transformations": [...],
    "object_graph_correspondences": [...],
    "invariant_preserving_transformations": [...],
    "relation_first_rewrites": [...],
    "composed_transform_candidates": [...],
    "explicit_candidate_grammars": [...],
}
```

### What it CAN construct from
1. **Train-forced transformations** — transformations directly supported by train inputs/outputs
2. **Object graph correspondences** — mappings between objects that have train evidence
3. **Invariant-preserving transformations** — transformations that preserve detected invariants
4. **Relation-first rewrites** — grammar rewrites that maintain relations
5. **Composed transform candidates** — composed transforms where each component is train-supported
6. **Explicit candidate grammars** — grammars explicitly enumerated from train evidence

### What it MUST NOT do
- Guess freely without train support
- Use hidden test output
- Use public ARC answers
- Learn from holdout answers (directly)
- Convert helper preference into proof
- Bypass ledger

### Output
```python
{
    "candidate_outputs": [...],            # Candidate output descriptors
    "construction_traces": [...],          # How each was built
    "used_constraints": [...],             # Constraints used
    "unsupported_assumptions": [...],      # Assumptions without train support
    "unresolved_rivals": [...],            # Rival grammars not resolved
    "candidate_requires_ledger_review": bool,
}
```

### Boundary Rule
> The generator produces candidates, NOT final answers. All candidates must pass through the ledger deservedness assembler.

---

## 5. Rehearsal Learning Recorder Design

### Purpose
Track internal repeated synthetic practice WITHOUT mutating the solver automatically.

### What it Records
```python
{
    "task_family": str,                    # e.g., "v4_rival_grammar"
    "variant_id": str,                     # e.g., "v5_task_01_variant_a"
    "attempt_number": int,
    "baseline_status": str,                 # "exact" | "partial" | "safe_failure" | "overconfident_wrong"
    "helper_diagnostics": {...},            # All helper outputs
    "generated_candidate_descriptors": [...], # Candidate outputs
    "ledger_decision": str,                 # "candidate_deserved" | etc.
    "missing_bridge": str,                  # What prevented deservedness
    "failure_reason": str,                  # Why it failed
    "repair_hypothesis": str | None,        # Hypothesized fix
    "failure_repeated": bool,               # Has this failure happened before?
    "improvement_from_memorization": bool, # Did improvement come from memorization?
    "fresh_holdout_confirmed": bool,        # Did fresh variant confirm improvement?
}
```

### What it MUST NOT do
- Mutate solver automatically
- Write ".weslr"
- Promote behavior packs
- Use hidden/public test data
- Treat repeated answer exposure as proof

### Anti-Memorization Detection
```python
{
    "same_task_exposure_count": int,        # How many times exact same task seen
    "same_pattern_exposure_count": int,     # How many times same pattern family
    "memorization_risk": "none" | "low" | "medium" | "high",
    "fresh_variant_correct": bool | None,  # Was fresh variant correct?
    "generalization_valid": bool,           # Is improvement real generalization?
}
```

---

## 6. Rehearsal vs Holdout Separation

### Task Sets

| Set | Purpose | Counts toward 85%? |
|-----|---------|-------------------|
| **Rehearsal** | Repeated internal pattern families | No |
| **Mutation/Design** | Where repair hypotheses developed | No |
| **Fresh Holdout** | Unseen variants after changes | **Yes** |
| **Promotion** | Larger unseen synthetic evaluation | Yes (final) |

### Rules
1. Rehearsal improvement does NOT count toward 85%
2. Fresh holdout improvement counts
3. Same-task memorization must be flagged
4. Same-pattern generalization counts only on fresh variants
5. Promotion gate must approve any change before calling it progress

### Flow
```
[Mutation/Design] -> [Repair Hypothesis] -> [Rehearsal Validation]
                                                         |
                                                         v
[Fresh Holdout] <---------------------------------------+
     |
     v
[Promotion Set] -> [Promotion Gate] -> [85% Threshold]
```

---

## 7. Synthetic Threshold Policy

### Internal Target
- **Fresh holdout exact rate**: >85%
- **Overconfident wrong**: 0 or below strict cap (≤1%)
- **Safe failure rate**: Must remain preserved (≥40%)
- **Helper output as evidence**: Must remain FALSE
- **Public claims**: Still forbidden
- **Internal 120**: Blocked until local gates pass

### Policy Rules
1. Fresh holdout exact > 85% = eligible for promotion review
2. Overconfident wrong > 1% = automatic halt
3. Safe failure < 40% = automatic halt
4. Helper output as evidence detected = automatic halt
5. Promotion gate must approve before any behavior change

### Key Point
> **Threshold is internal only and NOT official ARC performance**

---

## 8. ARC Prize / Public ARC Later-Stage Boundary

### When to Use Public Materials
- ONLY after synthetic fresh-holdout threshold met
- ONLY official public/allowed materials
- Check rules/license before use
- Separate public evaluation from training

### What is Forbidden
- Scraping arcprize.org hidden tests
- Using public test answers as evidence
- Leaking evaluation set knowledge
- Official ARC claims without official submission

### What is Allowed
- Training on public ARC tasks (with attribution)
- Checking progress on public ARC
- Submitting to official ARC competitions
- Reporting official competition results accurately

### Separation Rule
> Local synthetic metrics kept separate from ARC Prize metrics

---

## 9. Anti-Memorization Rules

1. **Same-task exposure limit**: After 3 repeats of exact same task, flag as memorization risk
2. **Fresh variant requirement**: Improvement valid only if fresh variant correct
3. **Pattern generalization check**: Improvement valid only if same-pattern fresh variant correct
4. **Exposure tracking**: Track all task exposures, flag high-frequency exposures
5. **Memorization detection**: If exact rate on rehearsal >> fresh holdout, flag memorization

---

## 10. Anti-Laundering Laws (from earlier design)

1. Helper output cannot become train evidence
2. Synthetic diagnostics cannot become proof
3. Repeated rehearsal cannot create deservedness
4. Elegance/beauty cannot create deservedness
5. MDL simplicity cannot create deservedness
6. Rival grammars cannot be resolved without train evidence
7. Hidden test output cannot be used
8. Public ARC answers cannot be used as evidence
9. Synthetic holdout answers cannot be used as training
10. Internal 120 cannot be enabled without owner approval
11. Promotion requires statistical gate approval
12. Final answer authority remains with ledger

---

## 11. Metrics Design

### Task Metrics
| Metric | Description |
|--------|-------------|
| rehearsal_task_count | Total rehearsal tasks attempted |
| fresh_holdout_task_count | Fresh holdout tasks attempted |
| same_task_repeat_count | Same task seen multiple times |
| same_pattern_fresh_variant_count | Same pattern, fresh variant |

### Candidate Metrics
| Metric | Description |
|--------|-------------|
| candidate_generated_count | Candidates generated |
| candidate_deserved_count | Candidates earned ledger deservedness |
| candidate_not_deserved_count | Candidates denied |
| safe_failure_required_count | Safe failure required |
| rival_unresolved_count | Rival grammars unresolved |
| forced_unique_output_count | Train-forced unique outputs |

### Safety Metrics
| Metric | Description |
|--------|-------------|
| memorization_risk_count | Tasks flagged as memorization risk |
| fresh_holdout_exact_rate | Exact rate on fresh holdout |
| fresh_holdout_safe_failure_rate | Safe failure rate on fresh holdout |
| overconfident_wrong_count | Overconfident wrong answers |
| helper_output_as_evidence_count | Helper output misused as evidence |
| promotion_gate_required_count | Changes requiring promotion gate |

---

## 12. Recommended Next Safe Local Follow-up

**`DESIGN_ARC_CONTROLLED_Answer_CANDIDATE_GENERATOR_V1`**

Rationale:
- The assembler cannot grant deservedness if no controlled candidate output exists
- Next needed: safe way to generate candidate outputs from forced constraints without guessing
- This is the next missing bridge after the assembler design

**NOT recommended:**
- Implementation yet (design must be reviewed first)
- Runtime wiring (safety boundary)
- Internal 120 (not authorized)

---

V5 result interpreted: yes
Ledger deservedness assembler designed: yes
Controlled answer candidate generator boundary defined: yes
Rehearsal learning recorder designed: yes
Rehearsal vs holdout separation defined: yes
Synthetic threshold policy defined: yes
ARC Prize/public ARC later-stage boundary defined: yes
Anti-memorization rules defined: yes
Anti-laundering laws defined: yes (12 laws)
Metrics defined: yes (17 metrics)
Recommended next lane: DESIGN_ARC_CONTROLLED_ANSWER_CANDIDATE_GENERATOR_V1
Validation: PASS
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_ledger_deservedness_assembler_rehearsal_recorder_design_ready