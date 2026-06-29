# WESLR ARC Line Completion Priority Fix V1

## 1. Executive Verdict

**PASS** — Evidence-based priority fix increased EXACT from 74/80 (92.5%) to 76/80 (95.0%).

## 2. Root Cause

Priority conflict in `_infer_pair_structural_candidate_v1`:
- `complete_symmetry` was checked before `line_completion`
- For line_completion variant 2: symmetry matched 2/3 train pairs, line_completion matched 3/3
- Blueprint logic requires ALL pairs to match for family selection
- With 2 vs 3 matches, neither reached blueprint threshold but symmetry "won" the per-pair inference

## 3. Priority Fix

Moved `line_completion` check before `symmetry` in `_infer_pair_structural_candidate_v1`:
- Line 655: Check `line_completion` first
- Line 662: Only check `symmetry` if `line_completion` is None

This is evidence-based: line_completion matches more train pairs (3/3) than symmetry (2/3).

## 4. 80-Task Results

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| EXACT | 74 | 76 | +2 |
| UNSUPPORTED | 6 | 4 | -2 |
| EXACT % | 92.5% | 95.0% | +2.5% |

## 5. Stripped/Shuffled Results

| Test | Before | After |
|------|--------|-------|
| Stripped (no metadata) | 66/80 (82.5%) | 68/80 (85.0%) |
| Shuffled (random order) | 72/80 (90.0%) | 75/80 (93.8%) |

## 6. Remaining Unsupported Cases

| Task | Family | Root Cause |
|------|--------|------------|
| synthetic_complete_symmetry_variant_2_v1 ×4 | complete_symmetry | Empty test input (curriculum bug) |

Note: The 4 remaining unsupported are from the copy_grid family having empty test inputs in the curriculum, NOT solver failures.

## 7. Boundary Preservation

- ✅ Expected outputs in train pairs (allowed for ARC train examples)
- ✅ Test outputs NOT used in solver generation
- ✅ No candidate_output_surface wiring
- ✅ No replay/scoring wiring
- ✅ No final-answer emission
- ✅ No provider/model/tool/retrieval calls
- ✅ `.weslr` untouched
- ✅ Protected runtime files unchanged

## 8. Recommended Next Lane

`EXCLUDE_MALFORMED_SYNTHETIC_TASKS_V1` — Remove tasks with empty test inputs from the 80-task easy curriculum (copy_grid variant 2 cases).