# WESLR Native Primitive Oracle Promotion Pipeline — Design (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `DESIGN_WESLR_NATIVE_PRIMITIVE_ORACLE_PROMOTION_PIPELINE_V1`
**Start HEAD**: `6c170798`

---

## 1. Promotion Problem Statement

The candidate generator produces 32 alien-language primitive candidates across 9 families. None can be used directly because:

| Gap | Why it blocks |
|-----|---------------|
| Alien expression may be valid but unimplemented | The expression `λG.Σ[obj|argmin(col)]⇒extract` is syntactically valid and hashable, but no code executes it |
| No oracle exists | No independent reference implementation — semantic comparison impossible |
| No solver wrapper exists | No dispatch target — solver cannot execute the primitive |
| No positive examples | No input/output pairs proving correct behavior |
| No negative controls | No proof that no-op or order variants produce different output |
| No BH80 regression proof | No evidence that adding this primitive doesn't break existing 80/80 |
| No audit artifacts | No content hash verification, trace, invariant checks, or regression impact summary |

**Therefore: candidates cannot be counted as solved.** The promotion pipeline exists to close each gap, one stage at a time, with hard blocks at every transition.

---

## 2. First Promotion Batch Selection

From the 32 candidates, select 3–5 for the first promotion batch:

### Selection criteria

| Criterion | Requirement |
|-----------|-------------|
| Type signature | Grid → Grid only (no Count, Object, ObjectSet outputs) |
| Complexity | Simple, single-operation semantics (no conditionals, no multi-object relations) |
| Oracle implementability | Can be implemented in <50 lines of independent Python |
| Solver implementability | Can be implemented as a dispatch wrapper in <50 lines |
| Testability | Can produce at least 3 positive examples and 2 negative controls |
| BH80 safety | Does not modify or interfere with existing BH80 primitives |
| No external data | No public/hidden ARC data needed |

### Recommended first batch (4 candidates)

| # | Candidate | Family | Expression | Reason |
|---|-----------|--------|------------|--------|
| 1 | `color_invert` | color_transform | `κ(invert)⇒recolor` | Simplest: invert all non-bg colors. Easy oracle + solver. |
| 2 | `mask_border_only` | mask_algebra | `Ω(mask∧border)⇢color(2)` | Similar to existing `extract_boundary` but mask-based. Tests mask algebra. |
| 3 | `constr_draw_rect_around` | construction_transform | `ξ(draw(rect,bbox(obj)))⇒overlay` | Construction is a new capability. Tests drawing primitives. |
| 4 | `geom_flip_vertical` | geometry_transform | `γ(flip(axis=row))⇒reflect` | Simple geometric flip. Already partially implemented in oracle as `transform`. |

### Excluded from first batch

| Family | Reason |
|--------|--------|
| object_selector | Requires multi-object scene complexity — defer to batch 2 |
| topology_transform | Complex connectivity changes — defer to batch 2 |
| relation_transform | Multi-object relations — defer to batch 3 |
| conditional_transform | Conditional execution — defer to batch 3 |
| pattern_transform | Pattern detection complexity — defer to batch 2 |

---

## 3. Oracle Definition Process

For each selected candidate:

### Step 1: Parse the alien expression
- Deserialize the internal expression into an operator graph
- Verify type signature (Grid → Grid)
- Extract parameters (if any)

### Step 2: Implement reference semantics
- Write independent Python code in `weslr/native_arc_oracle.py`
- Must NOT import `arc_synthetic_3_step_real_dispatch` or `arc_bh80_solver_adapter`
- Must use own connected-components, bbox, and helper functions (can share with `arc_bh80_oracle.py` helpers)
- Must be deterministic
- Must handle empty grids, single-cell grids, and edge cases

### Step 3: Generate positive examples
- Create 3+ input grids with known expected outputs
- Examples must cover: simple case, edge case, multi-object case
- Examples must be deterministic and reproducible

### Step 4: Generate negative controls
- No-op variant: replace with `pattern_output` (identity-ish) → must produce different output
- Order-reversal variant: if the primitive is part of a chain, reverse order → must differ
- Unsupported variant: replace with fake primitive → must return unsupported

### Step 5: Verify invariants
- Grid dimensions preserved/changed as declared
- Background handling deterministic
- No task-id or metadata access

---

## 4. Solver Implementation Process

For each selected candidate:

### Step 1: Create dispatch wrapper
- Add a wrapper in `weslr/arc_synthetic_3_step_real_dispatch.py` (or a new native dispatch module)
- Must match oracle semantics exactly
- Must NOT call oracle code
- Must handle empty grids and edge cases identically to oracle

### Step 2: Register in NAME_TO_ADAPTER_ID (if adapter-based)
- Or create a custom wrapper if the primitive doesn't fit the adapter model

### Step 3: Verify via solver adapter
- Run through `solver_run_with_input()` with the same positive examples
- Compare solver output to oracle output — must be `semantic_exact`

### Step 4: Verify negative controls
- No-op replacement through solver → must differ from real primitive output
- Unsupported primitive through solver → must return `unsupported`

---

## 5. Semantic Validation

### Required tests for each promoted primitive

| Test | Requirement |
|------|-------------|
| Oracle/solver agreement on positive examples | `grids_equal(solver_output, oracle_output)` = True for all examples |
| No-op control | Replacing with no-op produces different oracle output |
| Order control (if applicable) | Reversing primitive order in a chain produces different output |
| Unsupported sentinel | Fake primitive returns unsupported from both solver and oracle |
| Output diversity | Primitive produces diverse outputs across different input grids (≥ 3 unique) |
| Semantic exact = grid equality | Scorer uses `grids_equal()`, not structural support |
| Structural pass separate | `structural_pass` boolean separate from `semantic_exact` |

### Test file

Each promoted primitive gets tests in `weslr/tests/test_native_arc_promoted_primitives.py`:

```python
def test_<primitive_id>_semantic_exact():
    """Oracle and solver agree on positive examples."""
    for example in positive_examples:
        input_grid = example["input"]
        _, oracle_out, _ = oracle_run_primitive("<primitive_id>", input_grid)
        _, solver_out = solver_run_primitive("<primitive_id>", input_grid)
        assert grids_equal(solver_out, oracle_out)

def test_<primitive_id>_noop_control():
    """No-op variant produces different output."""
    ...

def test_<primitive_id>_unsupported_sentinel():
    """Fake primitive returns unsupported."""
    ...
```

---

## 6. Audit Artifact Production

For each promoted primitive, produce all 12 audit artifacts:

| Artifact | How produced |
|----------|-------------|
| serialized_internal_expression | From candidate's `internal_expression` field |
| content_hash | `compute_content_hash(internal_expression)` |
| type_signature | From candidate's `TypeSignature` |
| deterministic_execution_trace | Run oracle on positive examples, record step-by-step grid states |
| input_output_examples | 3+ (input_grid, output_grid) pairs |
| oracle_output | Oracle reference outputs for each example |
| solver_output | Solver outputs for each example |
| grid_equality_result | `grids_equal(solver_out, oracle_out)` for each example — all True |
| invariant_checks | Verify declared invariants_preserved and invariants_changed |
| negative_control_results | No-op and order-reversal results — must differ |
| regression_impact_summary | "BH80: 80/80 (no change)" or explain regression |
| human_summary | Optional — lossy approximate description |

All artifacts stored in an `AuditArtifactBundle` and validated via `validate_completeness()`.

---

## 7. Promotion Stage Enforcement

### Stage transitions

```
generated → typed → executable → oracle_defined → solver_targeted →
tested → anti_cheat_validated → regression_safe → promoted
```

| Transition | Required check | Blocking condition |
|------------|---------------|-------------------|
| generated → typed | Type signature valid | Invalid type → discard |
| typed → executable | Runs deterministically on test grids | Crash or non-determinism → discard |
| executable → oracle_defined | Oracle reference implementation exists and passes positive examples | No oracle → block |
| oracle_defined → solver_targeted | Solver dispatch wrapper exists and matches oracle on positive examples | No solver → block |
| solver_targeted → tested | All required tests pass (semantic_exact, no-op, sentinel, diversity) | Test failure → block |
| tested → anti_cheat_validated | All 9 anti-cheat controls pass | Control failure → block |
| anti_cheat_validated → regression_safe | BH80 remains ≥ 72/80 after primitive addition | BH80 < 72 → block |
| regression_safe → promoted | All audit artifacts produced and complete | Missing artifact → block |

### Hard rules

1. **No skipping**: `can_advance_to()` must return True — each stage requires the previous
2. **No promotion without oracle/solver**: Both must be verified
3. **No promotion without all audit artifacts**: `validate_completeness()` must pass
4. **No promotion without BH80 regression check**: Must run BH80 before and after
5. **`can_be_counted_as_solved()`** returns True only when `promotion_stage == PROMOTED`

---

## 8. BH80 Regression Protection

| Checkpoint | Requirement | Action if violated |
|-----------|-------------|-------------------|
| Before primitive addition | BH80 = 80/80 | If not 80/80, fix before proceeding |
| After oracle implementation | BH80 = 80/80 | If < 80, investigate — oracle may have side effects |
| After solver wrapper addition | BH80 = 80/80 | If < 80, solver wrapper broke existing primitives — fix or revert |
| After all tests pass | BH80 ≥ 72/80 | If < 72, block promotion; if < 68, rollback |
| After promotion | BH80 ≥ 72/80 | If < 72, demote primitive and investigate |

### Gate thresholds (from frozen baseline)

| Level | Score | Impact |
|-------|-------|--------|
| Clean | 80/80 | No regression — proceed |
| Preferred | ≥ 75/80 | May proceed to 120 expansion |
| Strong | ≥ 72/80 | Minimum for promotion |
| Minimal | ≥ 68/80 | Absolute floor |
| Critical | < 68/80 | Rollback required |

---

## 9. First Promotion Pilot Recommendation

### Pilot primitive: `color_invert`

| Field | Value |
|-------|-------|
| Candidate ID | `color_invert` |
| Family | color_transform |
| Expression | `κ(invert)⇒recolor` |
| Type | Grid → Grid |
| Semantics | Replace each non-background color `c` with `(10 - c)` |
| Oracle complexity | ~10 lines |
| Solver complexity | ~10 lines |
| Positive examples | 3 (simple, multi-color, edge case) |
| Negative controls | 2 (no-op, order reversal) |

### Pilot lane plan

1. Implement oracle reference for `color_invert` in `weslr/native_arc_oracle.py`
2. Implement solver wrapper in `weslr/arc_synthetic_3_step_real_dispatch.py` (or native dispatch module)
3. Create positive examples (3 input/output pairs)
4. Create negative controls (no-op variant, order reversal)
5. Run semantic tests: oracle vs solver grid equality
6. Run anti-cheat controls: no-op, order, sentinel, diversity
7. Run BH80 regression gate: must remain 80/80
8. Produce all 12 audit artifacts
9. Advance through all 9 promotion stages
10. Verify `can_be_counted_as_solved()` returns True

### Pilot success criteria

- `color_invert` promoted through all 9 stages
- BH80 remains 80/80
- All 12 audit artifacts complete
- All anti-cheat controls pass
- `can_be_counted_as_solved()` returns True

### Pilot failure handling

- If oracle/solver disagree → debug, do not promote
- If BH80 drops → investigate, do not promote
- If anti-cheat fails → strengthen primitive, do not promote
- If audit incomplete → produce missing artifacts, do not promote until complete

---

## 10. Relationship to 120

The 120‑task expansion may include:

| Component | Count | Source |
|-----------|-------|--------|
| Frozen BH80 base | 80 | Existing 80 tasks (unchanged) |
| New native‑language tasks | 40 | Generated from promoted native primitives |
| **Total** | **120** | |

### Rules
- Only **promoted** primitives counted in semantic score
- Candidate (unpromoted) primitives may appear as `candidate` probes but must NOT be counted
- `can_be_counted_as_solved()` must return True for any primitive used in scored tasks
- 120 gates: Minimal ≥ 102/120 (85%), Strong ≥ 108/120 (90%), Clean 120/120 (100%)

---

## 11. Forbidden Claims

- No public ARC data ✅
- No hidden/private ARC data ✅
- No ARC‑AGI score claims ✅
- No external provider/model calls ✅
- No runtime/chat/UI/provider path changes ✅
- No `.weslr` IO ✅
- No public claims ✅
- No weakening of semantic scorer, oracle separation, or anti‑cheat controls ✅

---

## Receipt

| Field | Value |
|-------|-------|
| **Start HEAD** | `6c170798` |
| **End HEAD** | `07090f5a` |
| **Commit** | yes (`07090f5a`) |
| **Actual preflight HEAD** | `6c170798` ✅ |
| **Metadata mismatch noted** | no ✅ |
| **Candidate direct‑use blocked** | yes ✅ |
| **First promotion batch criteria defined** | yes (4 candidates: color_invert, mask_border_only, constr_draw_rect_around, geom_flip_vertical) ✅ |
| **Oracle definition process defined** | yes (5 steps) ✅ |
| **Solver implementation process defined** | yes (4 steps) ✅ |
| **Semantic validation defined** | yes (7 required tests) ✅ |
| **Audit artifact production defined** | yes (12 artifacts) ✅ |
| **Promotion stage enforcement defined** | yes (9 stages, 8 transitions, 5 hard rules) ✅ |
| **BH80 regression protection defined** | yes (5 checkpoints, 5 thresholds) ✅ |
| **First promotion pilot recommended** | yes (`color_invert` — simplest candidate) ✅ |
| **120 relationship preserved** | yes (only promoted primitives counted) ✅ |
| **Validation** | PASS |
| **Push avoided** | yes ✅ |
| **Recommended next lane** | `IMPLEMENT_WESLR_NATIVE_PRIMITIVE_PROMOTION_PILOT_V1` |