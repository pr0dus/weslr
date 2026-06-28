# WESLR RELATION-FIRST COMPILER MANUAL POC DESIGN V1

## 1. Executive verdict
`relation_first_compiler_manual_poc_design_ready`

## 2. Why relation-first compiler POC
The moved-anchor run confirmed a strong frontier signal (50% failure rate) with specific sub-modes:
- Old anchor coordinate bait (12.5%)
- Relational anchor tracking failures (combined 50%)

The frozen solver can handle some relational cases (50% success rate) but defaults to coordinate binding in others. A **relation-first compiler POC** tests whether we can rewrite coordinate-style rules into relational form *before* the solver evaluates them — changing the reasoning path without modifying the solver itself.

## 3. Relation-first compiler POC definition
| Form | Description | Example |
|------|-------------|---------|
| **Coordinate form** | Rule keyed on absolute anchor coordinates | `anchor_at(old_x, old_y) → target_offset` |
| **Relational form** | Rule keyed on anchor identity/role | `anchor_role(anchor_id) → target_offset` |
| **Partial rewrite** | Some coordinate dependencies remain | Mixed coordinate/relational |
| **Irreducible** | No relational rewrite exists | Must use coordinate form |
| **Unsafe to predict** | No valid relational grammar found | Safe failure expected |

## 4. Manual POC cases selected
| Case ID | Source Family | Rationale |
|---------|----------------|------------|
| `poc_translated_target` | `anchor_translated_target_preserved` | Clean translation — expected full rewrite |
| `poc_distractor_bait` | `anchor_moved_distractor_at_old_coord` | Old coordinate bait failure — key test |
| `poc_multiple_anchors` | `multiple_anchors_one_valid` | Disambiguation — partial rewrite expected |
| `poc_boundary_edge` | `anchor_moved_near_boundary` | Edge effects — may be irreducible |
| `poc_offset_constant` | `anchor_moved_offset_constant` | Offset preserved — expected full rewrite |
| `poc_ambiguous_absent` | `anchor_absent_ambiguous` | Safe failure boundary — expected unsafe_to_predict |

## 5. Manual rewrite table
| Case | Original Rule (coordinate-like) | Proposed Relational Rewrite | Residual Dependency | Rewrite Outcome | Expected Result |
|------|----------------------------------|------------------------------|----------------------|-----------------|-----------------|
| `poc_translated_target` | anchor_at(2,2) → offset_right | anchor_role(anchor_A) → offset_right | none | full_relational_rewrite | exact match |
| `poc_distractor_bait` | anchor_at(old) → offset (with distractor at old) | anchor_role(anchor_A) → offset (ignore distractor) | none if rewrite succeeds | full_relational_rewrite | exact match (if rewrite works) |
| `poc_multiple_anchors` | anchor_at(C) → offset (ambiguous which anchor) | anchor_role(anchor_A is_primary) → offset | ambiguity residual | partial_relational_rewrite_with_residual | partial |
| `poc_boundary_edge` | anchor_at(8,8) → offset (near boundary) | anchor_role(anchor_A) → offset | boundary residual | coordinate_dependency_irreducible | partial/fallback |
| `poc_offset_constant` | anchor_at(old) → offset_same | anchor_role(anchor_A) → offset_same | none | full_relational_rewrite | exact match |
| `poc_ambiguous_absent` | no anchor defined | no relational rewrite possible | none valid | unsafe_to_predict_no_relational_grammar | unsupported (safe failure) |

## 6. Structural pass/fail policy
**Core principle**: Success is not "the ledger says safe."
- **Success** = the relational rewrite *becomes* the candidate rule that downstream components evaluate.
- **Failure modes**:
  - `unsafe_to_predict` = no valid relational grammar exists → correct state is structural no-answer, not post-hoc veto.
  - `coordinate_dependency_irreducible` = coordinate form is the only valid candidate → should remain coordinate, not forced into relational.
  - `partial_rewrite` = relational rewrite exists but has residual dependencies → downstream evaluates with both forms.

**No new judge**: We are not adding a diagnostic layer. We are testing whether the existing forward path can consume relational rewrite forms.

## 7. Rival grammar demotion (narrow role)
The POC does **not** design a broad rival-grammar judge.
- **Narrow scope**: Compare coordinate and relational grammars **only** when both survive as legitimate candidate forms.
- **Demotion rule**: Do not artificially demote one grammar to elevate another. If relational fails, fallback to coordinate; if coordinate is absent, the task is unsupported.

## 8. Manual POC execution plan
A future lane (not this one) will manually apply rewrites to the 6 selected cases and verify:
1. The relational rewrite can be formed as a candidate rule.
2. The existing forward path evaluates the relational form (not the original coordinate form).
3. The result changes compared to the baseline coordinate-only run.

This is a **manual execution lane**, not an automated probe.

## 9. Boundary review
- **Solver unchanged**: No new primitives, no depth-3, no patching.
- **Synthetic-only**: All source cases from moved-anchor probe; no public ARC/Kaggle.
- **No official claims**: `benchmark_claim_safe = false`.
- **No .weslr**: Confirmed.
- **No external calls**: Pure design documentation.
- **Protected files**: No modifications.

## 10. Recommended next safe local follow-up
`REVIEW_RELATION_FIRST_COMPILER_MANUAL_POC_DESIGN_V1`

---
All validation gates pass; protected files unchanged; `.weslr` untouched; push avoided.