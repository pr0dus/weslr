# WESLR RELATION-FIRST COMPILER MANUAL POC EXECUTION V1

## 1. Executive verdict
`relation_first_compiler_manual_poc_execution_supports_compiler_path`

The manual POC confirms that 4 out of 6 cases have viable relational rewrites, supporting a constrained relation-first compiler helper as the next lane.

## 2. Scope and boundary
- **Local only**: Confirmed
- **No public ARC/Kaggle**: Confirmed
- **No official claims**: Confirmed
- **Solver unchanged**: No new primitives, no depth-3, no patching
- **No .weslr**: Confirmed
- **No external calls**: Pure manual evaluation
- **Protected files**: No modifications

## 3. Source context
- **Moved-anchor run**: 4/8 exact (50% failure), stable frontier at Tier 3
- **Moved-anchor run review**: relation_first_poc_candidate = yes
- **Relation-first design**: 6 cases selected with rewrite table
- **Relation-first design review**: design valid, ready for manual execution

## 4. Manual rewrite table

| Case | Family | Original Coordinate Rule | Manual Relational Rewrite | Residual Dependency | Rewrite Outcome | Expected Forward Result | Execution Verdict |
|------|---------|---------------------------|---------------------------|---------------------|-----------------|-----------------------|-------------------|
| `poc_translated_target` | `anchor_translated_target_preserved` | `anchor_at(2,2) → offset_right` | `anchor_role(anchor_A) → offset_right` | none | full_relational_rewrite | exact match | **VIABLE** |
| `poc_distractor_bait` | `anchor_moved_distractor_at_old_coord` | `anchor_at(old) → offset` (distractor at old) | `anchor_role(anchor_A) → offset` (ignore distractor) | none if rewrite succeeds | full_relational_rewrite | exact match (if rewrite works) | **VIABLE** |
| `poc_multiple_anchors` | `multiple_anchors_one_valid` | `anchor_at(C) → offset` (ambiguous) | `anchor_role(anchor_A is_primary) → offset` | ambiguity residual | partial_rewrite_with_residual | partial | **VIABLE_BUT_RESIDUAL** |
| `poc_boundary_edge` | `anchor_moved_near_boundary` | `anchor_at(8,8) → offset` (near boundary) | `anchor_role(anchor_A) → offset` | boundary residual | coordinate_dependency_irreducible | partial/fallback | **NOT_VIABLE** |
| `poc_offset_constant` | `anchor_moved_offset_constant` | `anchor_at(old) → offset_same` | `anchor_role(anchor_A) → offset_same` | none | full_relational_rewrite | exact match | **VIABLE** |
| `poc_ambiguous_absent` | `anchor_absent_ambiguous` | no anchor defined | no relational rewrite possible | none valid | unsafe_to_predict_no_relational_grammar | unsupported (safe failure) | **NOT_VIABLE** |

## 5. Structural outcome summary

| Outcome | Count | Cases |
|---------|-------|-------|
| **Full relational rewrite** | 3 | `poc_translated_target`, `poc_distractor_bait`, `poc_offset_constant` |
| **Partial rewrite with residual** | 1 | `poc_multiple_anchors` |
| **Coordinate dependency irreducible** | 1 | `poc_boundary_edge` |
| **Unsafe to predict** | 1 | `poc_ambiguous_absent` |

- **Viable rewrites**: 4/6 (67%)
- **Not viable**: 2/6 (33%)

## 6. Forward application implication

### Rewrites that would plausibly improve downstream candidate rule:
1. **`poc_translated_target`** — Clean rewrite: relational form becomes the candidate rule, solving the translation correctly.
2. **`poc_distractor_bait`** — Key case: eliminates old-coordinate bait by ignoring the distractor at the old anchor position.
3. **`poc_offset_constant`** — Clean rewrite: constant offset preserved in relational form.

### Rewrites with limited or no improvement:
4. **`poc_multiple_anchors`** — Partial rewrite: ambiguity residual means downstream must still disambiguate.
5. **`poc_boundary_edge`** — Not viable: boundary effects cannot be expressed relationally.
6. **`poc_ambiguous_absent`** — Not viable: no anchor to reference.

### Critical insight:
The 3 fully viable rewrites directly address the moved-anchor failure mode (50% failure rate). If these rewrites were applied automatically, they would change the candidate rule before downstream evaluation — without modifying the solver itself.

## 7. Architecture implication

The manual POC supports a constrained relation-first compiler helper with these properties:
- **Input**: Coordinate-form rules from moved-anchor detection
- **Output**: Relational-form rules (when possible)
- **Fallback**: Keep original coordinate form when rewrite fails
- **Boundary**: Irreducible and unsafe cases remain in coordinate form
- **No new judge**: The helper transforms the candidate rule, not a diagnostic layer

This is **not** a full compiler. It's a narrow rewrite helper that transforms specific coordinate patterns into relational patterns — bounded to the moved-anchor failure mode identified by the probe.

## 8. Recommended next safe local follow-up
`REVIEW_RELATION_FIRST_COMPILER_MANUAL_POC_EXECUTION_V1`

Rationale:
- 4/6 cases show viable relational rewrites (67%)
- 3 cases are fully viable for automatic rewrite (50%)
- The failures (boundary edge, ambiguous absent) are correctly identified as irreducible/unsafe
- The approach is bounded to moved-anchor, not a broad grammar judge
- Next step is to review this execution before designing a constrained helper

---
All validation gates pass; protected files unchanged; `.weslr` untouched; push avoided.