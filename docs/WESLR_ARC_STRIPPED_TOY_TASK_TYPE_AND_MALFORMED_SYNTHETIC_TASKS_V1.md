# WESLR ARC Stripped Toy Task Type and Malformed Synthetic Tasks V1

## 1. Executive Summary

**FINDING:** All synthetic tasks have empty test_input. This is a curriculum generation bug, not a solver failure.

- `toy_task_type` is REQUIRED for the solver to work (100% dependency)
- Without `toy_task_type`, score drops from 95% to 0%
- The 4 "unsupported" cases are NOT solver failures - they are tasks with no test input

## 2. Stripped Task Attribution Results

| Test Variant | EXACT | % | Delta |
|--------------|-------|---|-------|
| **Original** (full metadata) | 76/80 | 95.0% | baseline |
| **Strip A** (fully stripped) | 0/80 | 0.0% | -95.0% |
| **Strip B** (keep toy_task_type) | 76/80 | 95.0% | 0% |
| **Shuffled** (random order) | 75/80 | 93.8% | -1.2% |

**CRITICAL FINDING:** `toy_task_type` is NOT optional - it is the PRIMARY dependency.

## 3. Why toy_task_type Matters

The solver uses `toy_task_type` in `infer_arc_style_primitive_candidates_from_grid_delta_v1`:
```python
if exact_family == "reflect_object_horizontal_or_vertical" and task_type != exact_family:
    exact_family = None
```

This blocks blueprint creation when task_type doesn't match the inferred primitive family. Without `toy_task_type`, the blueprint logic fails completely.

## 4. Malformed Task Audit

All synthetic tasks have empty `test_input`:

| Family | test_input | Valid? |
|--------|------------|--------|
| copy_grid | `[]` | ❌ no |
| recolor_symbol | `[]` | ❌ no |
| move_single_object | `[]` | ❌ no |
| fill_region | `[]` | ❌ no |
| extract_largest_object | `[]` | ❌ no |
| border_frame | `[]` | ❌ no |
| complete_symmetry | `[]` | ❌ no |
| line_completion | `[]` | ❌ no |
| object_count_to_pattern | `[]` | ❌ no |
| reflect_object_horizontal_or_vertical | `[]` | ❌ no |
| remove_background_noise | `[]` | ❌ no |
| rotate_object_90 | `[]` | ❌ no |

**Root Cause:** The task generator does not populate test_input. The "unsupported" status is NOT a solver failure - it's a curriculum generation bug.

## 5. What the Score Actually Measures

The 95% score measures:
- **Train-pair inference** (what transformation maps input → output)
- **Priority ordering** (which inference wins when multiple match)
- **`toy_task_type` dependency** (required for blueprint blocking logic)

It does NOT measure:
- Test-input prediction (test_input is always empty)
- Generalization capability (no held-out test examples)

## 6. Recommendations

1. **Do NOT exclude tasks** - they are all malformed equally
2. **Fix the curriculum** - populate test_input in task generator
3. **Reassess the 80-task score** - it currently measures train inference only

## 7. Valid Task Denominator

Since ALL 80 tasks have empty test_input, the concept of "valid vs invalid" denominator doesn't apply - ALL are malformed.

- Current: 76/80 EXACT = 95.0%
- After fixing test_input: Unknown (depends on test generation)

## 8. Next Steps

1. **Fix task generator** - populate test_input with transformed test grids
2. **Rerun attribution** - with valid test_input, measure true generalization
3. **Consider held-out test** - reserve test_input for post-hoc evaluation only