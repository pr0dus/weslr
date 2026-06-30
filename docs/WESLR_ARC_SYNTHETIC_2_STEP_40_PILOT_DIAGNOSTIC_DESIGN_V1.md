# WESLR ARC Synthetic 2-Step 40 Pilot Diagnostic Design V1

## 1. Executive verdict

Design a **40-task pilot diagnostic** for ARC-style 2-step compositions before attempting a 120-payload expansion.

Recommended verdict:
- proceed with a **40-task/payload pilot** first
- keep it **diagnostic-only** at first, not leaderboard-facing
- anchor the pilot on **toy_task_type-preserved** as the primary attribution baseline
- keep **fully stripped** as a lower-bound stress diagnostic, not as the success gate
- do **not** change solver logic, generators, ranking, candidate_output_surface, replay, scoring, or final-answer behavior in this lane

The pilot should be designed to answer one question cleanly:
> Can the current bounded single-step synthetic stack be extended into a controlled 2-step diagnostic without confusing composition failure, generator ambiguity, and stripped-mode attribution collapse?

## Handoff note

`WESLR_CURRENT_HANDOFF.md` reported verified HEAD `9ed508dbdc7899774c7ca19e932a04c3842f584d`, while the live approved repo state for this lane was:
- branch: `occ-discovery-doctrine-implementation-20260613`
- start HEAD: `ba17bc179662466048805eb0a1e90b62ab7a286f`

Per operator instruction for this lane only, the handoff HEAD was treated as stale and design proceeded only on live HEAD `ba17bc17`.

## 2. Why 40-task pilot instead of 120

A 40-task pilot is preferable now because it isolates the new failure surface introduced by **composition**, not raw scale.

Reasons:
- the single-step layer is already strong enough to justify composition work
  - canonical 120: `114 exact / 6 partial / 0 unsupported / 0 failed = 95.0%`
  - synthetic solver suite: `48 exact / 0 partial`
- the remaining 6 partials are already understood and concentrated in **fully stripped lower-bound mode** only
- a 120-scale 2-step rollout would mix too many uncertainties at once:
  - composition order failure
  - one-step shortcut false solutions
  - parameter carryover failure
  - stripped attribution collapse
  - generator ambiguity
- 40 tasks is large enough to expose real composition patterns while still being small enough for:
  - row-by-row manual diagnosis
  - reportable per-pair family coverage
  - careful generator review before implementation drift compounds

Recommended interpretation:
- **40-task pilot** = architecture probe
- **future 120-task 2-step expansion** = only after the pilot shows stable evidence and a useful taxonomy

## 3. Proposed 40-task composition plan

The pilot should use only already-supported primitives:
- `copy_grid`
- `recolor_symbol`
- `move_single_object`
- `fill_region`
- `extract_largest_object`
- `border_frame`
- `complete_symmetry`
- `line_completion`
- `object_count_to_pattern`
- `remove_background_noise`
- `rotate_object_90`
- `reflect_object_horizontal_or_vertical`

### Proposed task inventory

#### Easy 20
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

#### Medium 10
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

#### Stress / ambiguity 10
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

## 4. Easy / medium / stress split

### Easy 20
Purpose:
- validate that composition plumbing works when each step is semantically distinct
- minimize pair-order ambiguity
- minimize overlap with single-step shortcut solutions

Characteristics:
- first step simplifies or normalizes the scene
- second step applies an obvious visual transformation
- output signature should clearly require both steps

### Medium 10
Purpose:
- test compositions where one step is geometric or count-encoding
- require parameter carryover from step 1 into step 2 interpretation
- expose whether current family inference can remain stable under bounded composition

Characteristics:
- geometry plus recolor / move
- denoise or extraction feeding counting
- symmetry feeding completion

### Stress / ambiguity 10
Purpose:
- deliberately probe cases where a shallow single-step or wrong-order explanation may look plausible
- quantify lower-bound ambiguity before scaling beyond the pilot

Characteristics:
- step pairs with shared visual signatures
- opportunities for shortcut false solutions
- higher risk of primitive-order confusion or partial structural overfit

## 5. Primitive-pair coverage table

| Pair | Bucket | Count | Why included |
|---|---:|---:|---|
| remove_background_noise -> extract_largest_object | Easy | 1 | canonical denoise-then-isolate chain |
| remove_background_noise -> recolor_symbol | Easy | 1 | cleanup then symbol transform |
| extract_largest_object -> recolor_symbol | Easy | 1 | isolate then recolor |
| move_single_object -> border_frame | Easy | 1 | spatial move then global frame |
| copy_grid -> recolor_symbol | Easy | 1 | baseline composition sanity check |
| copy_grid -> border_frame | Easy | 1 | baseline + global wrapper |
| fill_region -> recolor_symbol | Easy | 1 | region fill then value change |
| fill_region -> line_completion | Easy | 1 | fill-to-line interaction |
| complete_symmetry -> recolor_symbol | Easy | 1 | symmetry then recolor |
| object_count_to_pattern -> border_frame | Easy | 1 | count encoding then wrapper |
| line_completion -> recolor_symbol | Easy | 1 | line then recolor |
| recolor_symbol -> border_frame | Easy | 1 | value transform then wrapper |
| extract_largest_object -> border_frame | Easy | 1 | isolate then frame |
| remove_background_noise -> border_frame | Easy | 1 | cleanup then frame |
| move_single_object -> recolor_symbol | Easy | 1 | object motion then value change |
| complete_symmetry -> border_frame | Easy | 1 | complete then frame |
| copy_grid -> line_completion | Easy | 1 | baseline then completion |
| fill_region -> border_frame | Easy | 1 | region transform then frame |
| line_completion -> border_frame | Easy | 1 | completion then wrapper |
| extract_largest_object -> complete_symmetry | Easy | 1 | isolate then complete |
| rotate_object_90 -> recolor_symbol | Medium | 1 | geometry then value transform |
| reflect_object_horizontal_or_vertical -> move_single_object | Medium | 1 | geometry then translation |
| rotate_object_90 -> reflect_object_horizontal_or_vertical | Medium | 1 | 2-step geometry chain |
| reflect_object_horizontal_or_vertical -> recolor_symbol | Medium | 1 | reflect then recolor |
| remove_background_noise -> object_count_to_pattern | Medium | 1 | cleanup feeding count encoding |
| extract_largest_object -> object_count_to_pattern | Medium | 1 | isolate feeding count encoding |
| complete_symmetry -> line_completion | Medium | 1 | completed structure feeding completion rule |
| move_single_object -> complete_symmetry | Medium | 1 | motion before symmetry closure |
| fill_region -> complete_symmetry | Medium | 1 | region fill before mirror completion |
| object_count_to_pattern -> recolor_symbol | Medium | 1 | count pattern then recolor |
| rotate_object_90 -> border_frame | Stress | 1 | geometry vs wrapper shortcut risk |
| reflect_object_horizontal_or_vertical -> border_frame | Stress | 1 | geometry vs wrapper shortcut risk |
| rotate_object_90 -> move_single_object | Stress | 1 | order-sensitive geometry/translation |
| reflect_object_horizontal_or_vertical -> complete_symmetry | Stress | 1 | reflect vs symmetry ambiguity |
| remove_background_noise -> complete_symmetry | Stress | 1 | cleanup can look shortcut-able |
| extract_largest_object -> line_completion | Stress | 1 | isolate vs direct line shortcut risk |
| object_count_to_pattern -> line_completion | Stress | 1 | count encoding vs line shortcut risk |
| fill_region -> object_count_to_pattern | Stress | 1 | region fill can perturb count signal |
| complete_symmetry -> object_count_to_pattern | Stress | 1 | symmetry can change count semantics |
| move_single_object -> reflect_object_horizontal_or_vertical | Stress | 1 | order-sensitive geometry chain |

Coverage properties:
- all 40 tasks use only already-supported primitives
- all listed exemplar compositions from the dispatch are included
- geometric, symbolic, regional, denoising, counting, and framing families are all exercised
- rotate/reflect appear, but are concentrated more heavily in medium/stress where they belong

## 6. Failure taxonomy

The pilot runner should classify each evaluated payload with both an **outcome class** and a **composition diagnosis class**.

### Outcome class
- `exact`
- `partial`
- `unsupported`
- `failed`

### Composition diagnosis class
- `right_primitives_wrong_order`
- `first_step_correct_second_wrong`
- `first_step_wrong_second_correct`
- `one_primitive_missing`
- `shortcut_single_step_false_solution`
- `ambiguous_train_evidence`
- `generator_ambiguity`
- `parameter_inference_failure`
- `execution_failure`

### Practical interpretation
- `right_primitives_wrong_order`: both primitives appear plausibly relevant, but the sequence is reversed
- `first_step_correct_second_wrong`: intermediate state looks correct, final transform diverges
- `first_step_wrong_second_correct`: second primitive could fit if the first had produced the intended intermediate surface
- `one_primitive_missing`: a single-step explanation captures only one stage of the task
- `shortcut_single_step_false_solution`: solver finds a plausible one-step explanation that bypasses the intended composition
- `ambiguous_train_evidence`: train examples do not force a unique 2-step hypothesis
- `generator_ambiguity`: the generator itself emits data that supports multiple intended interpretations
- `parameter_inference_failure`: correct primitive family is found but one or more parameters are wrong or frozen incorrectly
- `execution_failure`: intended primitive sequence is present but executor output is wrong

## 7. Attribution modes

The pilot should evaluate each task under four attribution modes:

1. `full_metadata`
   - complete task packet
   - strongest attribution surface
   - should be the primary design/debug baseline

2. `toy_task_type-preserved guardrail mode`
   - metadata reduced, but task-family guardrail preserved
   - should remain the main operational comparison baseline

3. `fully_stripped lower-bound mode`
   - train pairs + test input only
   - no family/task-type hint preservation
   - explicitly lower-bound diagnostic only, not primary success gate

4. `shuffled/renamed mode`
   - metadata field reorder / rename perturbation
   - checks robustness against shallow metadata over-coupling

### Interpretation rule
- success should be judged primarily by `full_metadata` and `toy_task_type-preserved`
- `fully_stripped` should be used to measure lower-bound compositional recoverability only
- `shuffled/renamed` should detect fragile metadata coupling

## 8. Leakage boundaries

The 2-step pilot must preserve the same leakage posture as the current single-step synthetic diagnostics.

Allowed:
- train outputs may be used for bounded rule inference
- train outputs may support family/parameter inference

Blocked:
- test output hidden from solver generation
- no expected-output candidate construction
- no answer-key usage
- no candidate creation from evaluation-only expected outputs
- no final-answer or score claims
- no ARC-AGI-2 submission coupling

### Leakage contract wording
- `uses_train_output_for_transformation_inference = true` is allowed
- `uses_test_output = false` must remain invariant
- evaluation-side expected outputs must only be used for post-hoc packet scoring / diagnostic labeling

## 9. Runner design proposal

The pilot runner should be diagnostic-first and shaped similarly to the current canonical synthetic runner.

### Proposed artifacts
- `build_arc_style_synthetic_2_step_pilot_plan_v1()`
- `run_arc_style_synthetic_2_step_40_pilot_diagnostic_v1()`
- `summarize_arc_style_synthetic_2_step_40_pilot_diagnostic_v1()`
- JSON-safe export helper
- focused failure-ledger builder for composition categories

### Proposed data model
Each evaluation row should include:
- `diagnostic_mode`
- `task_id`
- `source_task_id`
- `composition_pair`
- `difficulty_bucket`
- `test_input_index`
- `selected_candidate_id`
- `selected_primitive_sequence`
- `train_fit_status`
- `packet_status`
- `non_exact_reason`
- `composition_failure_category`
- `expected_exact_match`
- leakage flags

### Proposed gating philosophy
- 40 tasks total, 1 payload each in the pilot
- diagnostic rows should be manually reviewable
- no public score claims
- no competition framing
- baseline report should emphasize pair-level and bucket-level breakdown, not only one headline exact rate

### Recommended first implementation shape
Implement in two phases later:
1. **design-constrained generator/plan layer only**
2. **runner + evaluation layer**

Do not implement solver changes in the same lane as the first pilot scaffolding.

## 10. Risks

### Main risks
1. **Single-step shortcut contamination**
   - some 2-step tasks may admit plausible one-step false solutions
2. **Generator ambiguity**
   - compositions may accidentally support multiple valid intended orders
3. **Attribution collapse in stripped mode**
   - already visible in rotate/reflect single-step lower-bound rows
4. **Intermediate-state invisibility**
   - without explicit intermediate-state diagnostics, it may be hard to tell whether step 1 or step 2 failed
5. **Pair imbalance**
   - too many easy wrapper tasks could overstate composition readiness
6. **Geometric over-concentration**
   - rotate/reflect pairs can dominate observed failure taxonomy if not bounded carefully

### Risk posture recommendation
- treat the pilot as an **evidence-gathering diagnostic**, not as proof of 2-step runtime readiness
- require row-level post-run review before any 120-scale 2-step expansion

## 11. Recommended implementation lane

Recommended next lane:
- `DESIGN_CONSTRAINED_IMPLEMENT_ARC_SYNTHETIC_2_STEP_40_PILOT_PLAN_AND_RUNNER_V1`

Recommended scope of that next lane:
- implement plan/build/report plumbing for the 40-task pilot
- generate only the designed composition inventory
- add runner summaries and failure taxonomy wiring
- keep solver logic unchanged
- keep candidate_output_surface/replay/scoring/final-answer behavior blocked
- keep fully stripped as lower-bound only

Recommended non-goals for that next lane:
- no rotate/reflect stripped-mode repair
- no abstract alias normalization
- no ARC-AGI-2 participation changes
- no public-score framing

## Validation

Requested validation for this design lane:
- `python weslr/tests/release_gate_v1.py`
- `git diff --check`
- `./scripts/weslr_release_check.sh`
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`

These validations passed for the report-only commit in this lane.
