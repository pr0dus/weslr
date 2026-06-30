# WESLR ARC Synthetic 2-Step 40 Pilot Runner V1

## 1. Executive verdict

The design-constrained 2-step pilot runner is now implemented as a **deterministic diagnostic scaffold**.

Observed result on the primary attribution baseline (`toy_task_type_preserved_guardrail`):
- exact: `0`
- partial: `0`
- unsupported: `40`
- failed: `0`

That outcome is acceptable for this lane.
This lane was explicitly scoped to create a reproducible pilot runner and reporting surface, **not** to force a passing 2-step score or change solver inference logic.

### Handoff note

`WESLR_CURRENT_HANDOFF.md` reported verified HEAD `9ed508dbdc7899774c7ca19e932a04c3842f584d`, while the live approved repo state for this lane was:
- branch: `occ-discovery-doctrine-implementation-20260613`
- start HEAD: `f6c97910121ec997c9d5c1fad6c32daaf90fdc90`

Per operator instruction for this lane only, that handoff HEAD was treated as stale and implementation proceeded only on live HEAD `f6c97910`.

## 2. Implemented runner entry points

Implemented module:
- `weslr/arc_style_synthetic_2_step_pilot_runner.py`

Implemented entry points:
- `build_arc_style_synthetic_2_step_pilot_plan_v1()`
- `run_arc_style_synthetic_2_step_40_pilot_diagnostic_v1()`
- `summarize_arc_style_synthetic_2_step_40_pilot_diagnostic_v1()`
- `to_arc_style_synthetic_2_step_pilot_json_safe_v1()`

Implemented focused test file:
- `weslr/tests/test_arc_style_synthetic_2_step_pilot_runner_v1.py`

## 3. 40-task inventory

The deterministic pilot inventory matches the approved design split and pair list.

### Easy 20
1. `remove_background_noise -> extract_largest_object`
2. `remove_background_noise -> recolor_symbol`
3. `extract_largest_object -> recolor_symbol`
4. `move_single_object -> border_frame`
5. `copy_grid -> recolor_symbol`
6. `copy_grid -> border_frame`
7. `fill_region -> recolor_symbol`
8. `fill_region -> line_completion`
9. `complete_symmetry -> recolor_symbol`
10. `object_count_to_pattern -> border_frame`
11. `line_completion -> recolor_symbol`
12. `recolor_symbol -> border_frame`
13. `extract_largest_object -> border_frame`
14. `remove_background_noise -> border_frame`
15. `move_single_object -> recolor_symbol`
16. `complete_symmetry -> border_frame`
17. `copy_grid -> line_completion`
18. `fill_region -> border_frame`
19. `line_completion -> border_frame`
20. `extract_largest_object -> complete_symmetry`

### Medium 10
21. `rotate_object_90 -> recolor_symbol`
22. `reflect_object_horizontal_or_vertical -> move_single_object`
23. `rotate_object_90 -> reflect_object_horizontal_or_vertical`
24. `reflect_object_horizontal_or_vertical -> recolor_symbol`
25. `remove_background_noise -> object_count_to_pattern`
26. `extract_largest_object -> object_count_to_pattern`
27. `complete_symmetry -> line_completion`
28. `move_single_object -> complete_symmetry`
29. `fill_region -> complete_symmetry`
30. `object_count_to_pattern -> recolor_symbol`

### Stress / ambiguity 10
31. `rotate_object_90 -> border_frame`
32. `reflect_object_horizontal_or_vertical -> border_frame`
33. `rotate_object_90 -> move_single_object`
34. `reflect_object_horizontal_or_vertical -> complete_symmetry`
35. `remove_background_noise -> complete_symmetry`
36. `extract_largest_object -> line_completion`
37. `object_count_to_pattern -> line_completion`
38. `fill_region -> object_count_to_pattern`
39. `complete_symmetry -> object_count_to_pattern`
40. `move_single_object -> reflect_object_horizontal_or_vertical`

## 4. Easy / medium / stress breakdown

Configured split:
- easy: `20`
- medium: `10`
- stress: `10`

Observed primary-baseline result by bucket:
- easy: `0 exact / 0 partial / 20 unsupported / 0 failed`
- medium: `0 exact / 0 partial / 10 unsupported / 0 failed`
- stress: `0 exact / 0 partial / 10 unsupported / 0 failed`

## 5. Attribution modes

Implemented modes:
- `full_metadata`
- `toy_task_type_preserved_guardrail`
- `fully_stripped_lower_bound`
- `shuffled_renamed`

Observed result by mode:
- `full_metadata`: `0 exact / 0 partial / 40 unsupported / 0 failed`
- `toy_task_type_preserved_guardrail`: `0 exact / 0 partial / 40 unsupported / 0 failed`
- `fully_stripped_lower_bound`: `0 exact / 0 partial / 40 unsupported / 0 failed`
- `shuffled_renamed`: `0 exact / 0 partial / 40 unsupported / 0 failed`

Interpretation:
- the new runner is stable across attribution modes
- the current bounded solver still does not recover these planned 2-step tasks under any implemented mode
- this is evidence of current compositional limitation, not a runner defect by itself

## 6. 2-step pilot result

Primary reporting baseline:
- `toy_task_type_preserved_guardrail`

Primary result:
- exact: `0`
- partial: `0`
- unsupported: `40`
- failed: `0`

Operational reading:
- the scaffold is deterministic
- no execution crashes were introduced
- the solver consistently lands in unsupported territory for this pilot inventory
- the pilot is therefore useful immediately as a reproducible lower bound for future controlled repair work

## 7. Pair-level breakdown

All 40 composition pairs scored:
- `0 exact / 0 partial / 1 unsupported / 0 failed`

Pairs:
- `remove_background_noise -> extract_largest_object`
- `remove_background_noise -> recolor_symbol`
- `extract_largest_object -> recolor_symbol`
- `move_single_object -> border_frame`
- `copy_grid -> recolor_symbol`
- `copy_grid -> border_frame`
- `fill_region -> recolor_symbol`
- `fill_region -> line_completion`
- `complete_symmetry -> recolor_symbol`
- `object_count_to_pattern -> border_frame`
- `line_completion -> recolor_symbol`
- `recolor_symbol -> border_frame`
- `extract_largest_object -> border_frame`
- `remove_background_noise -> border_frame`
- `move_single_object -> recolor_symbol`
- `complete_symmetry -> border_frame`
- `copy_grid -> line_completion`
- `fill_region -> border_frame`
- `line_completion -> border_frame`
- `extract_largest_object -> complete_symmetry`
- `rotate_object_90 -> recolor_symbol`
- `reflect_object_horizontal_or_vertical -> move_single_object`
- `rotate_object_90 -> reflect_object_horizontal_or_vertical`
- `reflect_object_horizontal_or_vertical -> recolor_symbol`
- `remove_background_noise -> object_count_to_pattern`
- `extract_largest_object -> object_count_to_pattern`
- `complete_symmetry -> line_completion`
- `move_single_object -> complete_symmetry`
- `fill_region -> complete_symmetry`
- `object_count_to_pattern -> recolor_symbol`
- `rotate_object_90 -> border_frame`
- `reflect_object_horizontal_or_vertical -> border_frame`
- `rotate_object_90 -> move_single_object`
- `reflect_object_horizontal_or_vertical -> complete_symmetry`
- `remove_background_noise -> complete_symmetry`
- `extract_largest_object -> line_completion`
- `object_count_to_pattern -> line_completion`
- `fill_region -> object_count_to_pattern`
- `complete_symmetry -> object_count_to_pattern`
- `move_single_object -> reflect_object_horizontal_or_vertical`

## 8. Failure taxonomy breakdown

Primary-baseline taxonomy counts:
- `right_primitives_wrong_order`: `0`
- `first_step_correct_second_wrong`: `0`
- `first_step_wrong_second_correct`: `0`
- `one_primitive_missing`: `9`
- `shortcut_single_step_false_solution`: `0`
- `ambiguous_train_evidence`: `9`
- `generator_ambiguity`: `0`
- `parameter_inference_failure`: `22`
- `execution_failure`: `0`

Interpretation:
- the current runner is successfully labeling non-exact rows into the intended diagnostic taxonomy
- most rows land in either `parameter_inference_failure` or lower-bound ambiguity / missing-step buckets
- no runner-side execution failures were observed

## 9. Leakage check

Preserved boundaries:
- train outputs allowed for rule inference: yes
- test output hidden from solver generation: yes
- no expected-output candidate construction: yes
- no answer-key usage: yes

Observed leakage/trace posture:
- `uses_test_output`: `false`
- `uses_task_id_for_candidate_selection`: `false`
- `uses_notes_for_candidate_selection`: `false`
- `lookup_table_detected`: `false`
- `synthetic_only`: `true`

## 10. Boundary preservation

Confirmed preserved in this lane:
- solver inference logic unchanged
- existing single-step diagnostic runner unchanged
- rotate/reflect stripped-mode partials not repaired here
- abstract aliases not normalized here
- candidate_output_surface not wired
- replay/scoring/final-answer behavior not added
- ARC-AGI-2 participation untouched
- `.weslr` untouched
- protected runtime/chat files untouched

## 11. What the result does and does not prove

What it proves:
- the 40-task 2-step pilot inventory now exists in committed deterministic code
- the pilot can be rebuilt and rerun reproducibly
- attribution modes, bucket summaries, pair summaries, row-level fields, and failure taxonomy are now wired
- the current bounded solver has a clean measurable failure surface on this pilot

What it does not prove:
- it does not prove 2-step solver readiness
- it does not prove generator optimality
- it does not prove that all current 2-step failures are solver-only rather than a mix of attribution, primitive sequencing, and abstraction limits
- it does not justify any score claim, ARC benchmark claim, or public capability claim

## 12. Recommended next lane

Recommended next lane:
- `DIAGNOSE_ARC_SYNTHETIC_2_STEP_40_PILOT_UNSUPPORTED_PATTERN_V1`

Recommended focus for that next lane:
- inspect representative unsupported rows by bucket and pair family
- determine whether failure mass is dominated by:
  - missing sequence search depth/use
  - primitive-sequence ranking weakness
  - abstraction mismatch between synthetic composition packets and current solver candidate generation
  - over-strong dependence on known single-step family routing
- keep the current pilot inventory fixed while diagnosing
- do not tune tasks to pass until unsupported-pattern diagnosis is explicit
