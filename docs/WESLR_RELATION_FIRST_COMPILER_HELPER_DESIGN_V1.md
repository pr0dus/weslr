# WESLR RELATION-FIRST COMPILER HELPER DESIGN V1

## 1. Executive verdict
`relation_first_compiler_helper_design_ready`

## 2. Helper responsibility
The helper transforms candidate rules when a moved-anchor coordinate form is detected.
- **What it does**: Rewrites coordinate-form rules into relational-form rules
- **What it does NOT do**: Score, judge, veto, certify answers, or generate final answers
- **Boundary**: Pure transformation, not a diagnostic layer

## 3. Accepted input shape
Minimal input packet for a candidate coordinate rule:

```python
{
    "rule_id": str,              # Unique identifier for this rule
    "family_id": str,           # Source family: anchor_translated_target_preserved, etc.
    "anchor_coordinate": {      # Original anchor position
        "x": int,
        "y": int
    },
    "anchor_identity": str | None,   # Known anchor identity/role (if available)
    "target_offset": {         # Target object offset from anchor
        "dx": int,
        "dy": int
    },
    "distractor_at_old_anchor": bool,  # Is there a distractor at old anchor position?
    "ambiguity_signal": bool,     # Is the anchor ambiguous (multiple anchors)?
    "boundary_signal": bool,     # Is anchor near grid boundary?
    "anchor_absent": bool,       # Is anchor absent/ambiguous?
    "context": {                 # Additional context
        "task_id": str,
        "source": str
    }
}
```

## 4. Output shape
```python
{
    "rewrite_status": str,       # full_relational_rewrite | partial_rewrite_with_residual | coordinate_dependency_irreducible | unsafe_to_predict_no_relational_grammar | not_applicable
    "original_coordinate_rule": dict,   # Original input preserved
    "relational_rule": dict | None,     # Transformed relational form
    "residual_dependency": str | None,   # Residual dependency if partial
    "fallback_rule": dict | None,        # Original if rewrite fails
    "downstream_candidate_rule": dict,   # Rule passed to downstream
    "helper_changed_candidate_rule": bool,  # Did helper actually transform?
    "safety_reason": str | None,       # Why rewrite succeeded/failed
    "transform_metadata": {
        "rule_id": str,
        "rewrite_timestamp": str,
        "input_family": str,
        "output_family": str
    }
}
```

## 5. Rewrite policy

### Full relational rewrite (rewrite_status = "full_relational_rewrite")
Rewrite when:
- `family_id` in `["anchor_translated_target_preserved", "anchor_moved_offset_constant"]`
- AND `anchor_identity` is available
- AND `distractor_at_old_anchor == False`
- AND `ambiguity_signal == False`
- AND `boundary_signal == False`

Output: `relational_rule` becomes `downstream_candidate_rule`

### Partial rewrite with residual (rewrite_status = "partial_rewrite_with_residual")
Rewrite when:
- `family_id == "multiple_anchors_one_valid"`
- AND `anchor_identity` is available but ambiguous
- Residual dependency: "ambiguity_residual"

Output: Both `relational_rule` and `fallback_rule` become candidates for downstream

### Coordinate dependency irreducible (rewrite_status = "coordinate_dependency_irreducible")
Do NOT rewrite when:
- `family_id == "anchor_moved_near_boundary"`
- OR `boundary_signal == True`
- AND no clean relational form exists

Output: `fallback_rule` (original coordinate) becomes `downstream_candidate_rule`

### Unsafe to predict (rewrite_status = "unsafe_to_predict_no_relational_grammar")
Do NOT rewrite when:
- `family_id == "anchor_absent_ambiguous"`
- OR `anchor_absent == True`
- OR `anchor_identity` is missing/None
- AND no valid relational grammar exists

Output: No candidate rule; return unsupported/safe failure state

### Not applicable (rewrite_status = "not_applicable")
When input does not match any moved-anchor family:
- Return input unchanged as `downstream_candidate_rule`
- `helper_changed_candidate_rule = False`

## 6. Fail-closed behavior
If required fields are missing, ambiguous, or unsafe:
- **Do NOT invent anchor identity**
- **Do NOT patch coordinate rule**
- **Return safe status** (`unsafe_to_predict` or `not_applicable`)
- **Preserve fallback or unsupported state**

Required fields for rewrite attempt:
- `rule_id`
- `anchor_coordinate`
- `target_offset`
- `family_id`

If any required field is missing: `rewrite_status = "not_applicable"`

## 7. Non-goals (explicitly excluded)
- **No solver behavior change**: Helper does not modify solver primitives
- **No new solver primitive**: No depth-3, no retry fill
- **No broad grammar compiler**: Limited to moved-anchor coordinate-to-relational
- **No learned scorer**: No ML/AI model integration
- **No runtime integration**: Pure function, not wired to ChatResponder/UI
- **No final answer generation**: Helper transforms rules, not answers
- **No ARC/Kaggle claim**: Synthetic-only, no public benchmark claims

## 8. Test strategy for future implementation

### Unit test cases:
| Test Case | Input Condition | Expected Output |
|-----------|-----------------|-----------------|
| `test_full_relational_rewrite_translated` | Clean translation, identity available | `rewrite_status = full_relational_rewrite` |
| `test_full_relational_rewrite_offset` | Offset constant, identity available | `rewrite_status = full_relational_rewrite` |
| `test_full_relational_rewrite_distractor` | Distractor bait at old coordinate | `rewrite_status = full_relational_rewrite` (ignores distractor) |
| `test_partial_rewrite_ambiguity` | Multiple anchors, ambiguity residual | `rewrite_status = partial_rewrite_with_residual` |
| `test_irreducible_boundary` | Near boundary, no clean relational | `rewrite_status = coordinate_dependency_irreducible` |
| `test_unsafe_no_anchor` | Anchor absent/ambiguous | `rewrite_status = unsafe_to_predict_no_relational_grammar` |
| `test_not_applicable` | Non-moved-anchor family | `rewrite_status = not_applicable` |
| `test_missing_field_fail_closed` | Required field missing | `rewrite_status = not_applicable` |
| `test_helper_does_not_mutate_input` | Any valid input | `original_coordinate_rule` preserved |
| `test_no_external_calls` | Any input | No external system calls |

### Integration test strategy (future):
- Feed output to existing forward path
- Verify downstream receives transformed candidate
- Verify result differs from baseline coordinate-only run

## 9. Expected future implementation lane
`IMPLEMENT_RELATION_FIRST_COMPILER_HELPER_V1`

This lane will implement the helper as a pure function in `weslr/` (exact path to be determined), with unit tests verifying all 10 test cases above.

## 10. Boundary review
- **Solver unchanged**: No new primitives, no depth-3, no patching
- **Synthetic-only**: All source from moved-anchor probe; no public ARC/Kaggle
- **No official claims**: `benchmark_claim_safe = false`
- **No .weslr**: Confirmed
- **No external calls**: Pure function
- **Protected files**: No modifications

## 11. Recommended next safe local follow-up
`REVIEW_RELATION_FIRST_COMPILER_HELPER_DESIGN_V1`

---
All validation gates pass; protected files unchanged; `.weslr` untouched; push avoided.