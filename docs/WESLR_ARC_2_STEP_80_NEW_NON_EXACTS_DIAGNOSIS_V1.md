# WESLR ARC 2-Step 80 New Non-Exacts Diagnosis V1

- Dispatch: `DIAGNOSE_NEW_80_TASK_NON_EXACTS_WITHOUT_TOUCHING_KNOWN_STRESS_RESIDUAL_V1`
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `5238b6e6176520fbd6681813bcc3803ca46dc911`
- Previous report: `docs/WESLR_ARC_2_STEP_80_PILOT_EXPANSION_WITH_STRESS_RESIDUAL_TRACKING_V1.md`

## 1. Executive verdict

This lane diagnoses only the 4 new non-exacts from the 80-task expansion.
The known stress residual was left untouched.

Diagnosed rows:
1. `pilot_2_step_easy_gen_02_noise_recolor_color_swap_v1`
2. `pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1`
3. `pilot_2_step_easy_gen_10_line_recolor_vertical_v1`
4. `pilot_2_step_medium_ctx_09_extract_recolor_bg_transfer_v1`

High-level judgment:
- `3` rows are narrow repair candidates
- `1` row is a generator/sequence-generation correction candidate
- `0` are accepted new residuals
- `0` show candidate-budget cutoff
- `0` show generator ambiguity

Root-cause distribution used in this diagnosis:
- `step_2_parameter_inference_failure`: `2`
- `parameter_carryover_failure`: `1`
- `sequence_not_generated`: `1`

Known stress residual untouched: yes.

## 2. Per-row diagnosis

### A. `pilot_2_step_easy_gen_02_noise_recolor_color_swap_v1`

- task_id: `pilot_2_step_easy_gen_02_noise_recolor_color_swap_v1`
- composition_pair: `remove_background_noise -> recolor_symbol`
- difficulty_bucket: `easy`
- diagnostic_mode: `toy_task_type_preserved_guardrail`
- packet_status: `partial`
- train_fit_status: `partial_fit`
- selected_candidate_id: `pilot_2_step_easy_gen_02_noise_recolor_color_swap_v1__toy_task_type_preserved_guardrail:sequence:1`
- selected_primitive_sequence: `[{"primitive_id": "recolor_symbol", "parameters": {"background_value": 0, "from_value": 9, "to_value": 2}}, {"primitive_id": "remove_background_noise", "parameters": {"background_value": 0}}]`
- step_1_primitive_and_parameters: `{"primitive_id": "recolor_symbol", "parameters": {"background_value": 0, "from_value": 9, "to_value": 2}}`
- step_2_primitive_and_parameters: `{"primitive_id": "remove_background_noise", "parameters": {"background_value": 0}}`
- intended_pair_represented: `yes`
- order_correct: `no`
- step_1_plausible: `no`
- step_2_plausible: `yes`
- non_exact_reason: `first_step_wrong_second_correct`
- composition_failure_category: `first_step_wrong_second_correct`
- root_cause: `step_2_parameter_inference_failure`

Intermediate grid summary (selected candidate):
```json
{
  "shape": [6, 6],
  "grid": [
    [0, 2, 0, 0, 0, 0],
    [0, 2, 2, 2, 2, 0],
    [0, 2, 2, 2, 2, 0],
    [0, 2, 2, 2, 2, 0],
    [0, 2, 2, 2, 2, 0],
    [0, 0, 0, 0, 0, 0]
  ],
  "comparison_to_expected_intermediate": {
    "exact_match": false,
    "value_mismatch_count": 1
  }
}
```

Final predicted output (selected candidate):
```json
[
  [0, 2, 0, 0, 0, 0],
  [0, 2, 2, 2, 2, 0],
  [0, 2, 2, 2, 2, 0],
  [0, 2, 2, 2, 2, 0],
  [0, 2, 2, 2, 2, 0],
  [0, 0, 0, 0, 0, 0]
]
```

Expected output (evaluation-side only):
```json
[
  [0, 9, 0, 0, 0, 0],
  [0, 2, 2, 2, 2, 0],
  [0, 2, 2, 2, 2, 0],
  [0, 2, 2, 2, 2, 0],
  [0, 2, 2, 2, 2, 0],
  [0, 0, 0, 0, 0, 0]
]
```

Diagnosis:
- the intended ordered pair is generated
- the intended candidate (`sequence:0`) already has the right order and an exact step-1 intermediate on the test case
- the failure is the recolor step choosing `from_value=9 -> to_value=2`, which wrongly recolors the surviving singleton marker that should remain `9`
- this is therefore best treated as a **narrow step-2 recolor inference miss**, not budget, not ambiguity

Decision class:
- `narrow repair candidate`

---

### B. `pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1`

- task_id: `pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1`
- composition_pair: `extract_largest_object -> recolor_symbol`
- difficulty_bucket: `easy`
- diagnostic_mode: `toy_task_type_preserved_guardrail`
- packet_status: `partial`
- train_fit_status: `partial_fit`
- selected_candidate_id: `pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1__toy_task_type_preserved_guardrail:sequence:1`
- selected_primitive_sequence: `[{"primitive_id": "recolor_symbol", "parameters": {"background_value": 4}}, {"primitive_id": "extract_largest_object", "parameters": {}}]`
- step_1_primitive_and_parameters: `{"primitive_id": "recolor_symbol", "parameters": {"background_value": 4}}`
- step_2_primitive_and_parameters: `{"primitive_id": "extract_largest_object", "parameters": {}}`
- intended_pair_represented: `yes`
- order_correct: `no`
- step_1_plausible: `no`
- step_2_plausible: `yes`
- non_exact_reason: `parameter_carryover_failure`
- composition_failure_category: `parameter_carryover_failure`
- root_cause: `parameter_carryover_failure`

Intermediate grid summary (selected candidate):
```json
{
  "shape": [7, 7],
  "grid": [
    [0, 7, 0, 0, 0, 0, 0],
    [0, 4, 4, 4, 4, 4, 0],
    [0, 4, 4, 4, 4, 4, 0],
    [0, 4, 4, 4, 4, 4, 0],
    [0, 4, 4, 4, 4, 4, 0],
    [0, 4, 4, 4, 4, 4, 0],
    [7, 0, 0, 0, 0, 0, 0]
  ],
  "comparison_to_expected_intermediate": {
    "exact_match": false,
    "value_mismatch_count": 26
  }
}
```

Final predicted output (selected candidate):
```json
[
  [0, 7, 0, 0, 0, 0, 0],
  [0, 7, 7, 7, 7, 7, 0],
  [0, 7, 7, 7, 7, 7, 0],
  [0, 7, 7, 7, 7, 7, 0],
  [0, 7, 7, 7, 7, 7, 0],
  [0, 7, 7, 7, 7, 7, 0],
  [0, 0, 0, 0, 0, 0, 0]
]
```

Expected output (evaluation-side only):
```json
[
  [0, 7, 0, 0, 0, 0, 0],
  [0, 7, 7, 7, 7, 7, 0],
  [0, 7, 7, 7, 7, 7, 0],
  [0, 7, 7, 7, 7, 7, 0],
  [0, 7, 7, 7, 7, 7, 0],
  [0, 7, 7, 7, 7, 7, 0],
  [0, 0, 0, 0, 0, 0, 0]
]
```

Diagnosis:
- the intended pair is represented
- the intended candidate carries only `background_value=4` for recolor, leaving `from_value/to_value` dynamic but unresolved in the stable selected summary
- the reversed candidate accidentally matches the test output exactly while remaining partial on train
- this is the clearest new **extract/recolor carryover** case and should stay grouped with similar extract/recolor repair work rather than treated as a generic ranking problem

Decision class:
- `narrow repair candidate`

---

### C. `pilot_2_step_easy_gen_10_line_recolor_vertical_v1`

- task_id: `pilot_2_step_easy_gen_10_line_recolor_vertical_v1`
- composition_pair: `line_completion -> recolor_symbol`
- difficulty_bucket: `easy`
- diagnostic_mode: `toy_task_type_preserved_guardrail`
- packet_status: `unsupported`
- train_fit_status: `unsupported`
- selected_candidate_id: `none`
- selected_primitive_sequence: `[]`
- step_1_primitive_and_parameters: `none`
- step_2_primitive_and_parameters: `none`
- intended_pair_represented: `no`
- order_correct: `no`
- step_1_plausible: `no`
- step_2_plausible: `no`
- non_exact_reason: `sequence_not_generated`
- composition_failure_category: `sequence_not_generated`
- root_cause: `sequence_not_generated`

Intermediate grid summary:
- expected test intermediate exists and is a completed vertical line
- no candidate was emitted, so there is no generated intermediate to compare

Expected output (evaluation-side only):
```json
[
  [0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0],
  [0, 3, 3, 3, 3, 3],
  [0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0]
]
```

Unsupported-row answers:
- intended pair generated: `no`
- any executable 2-step candidate generated: `no`
- skipped by compatibility matrix: `no`
- skipped by parameter inference: `yes`
- skipped by budget: `no`
- sequence-generation issue or generator issue: `sequence-generation issue`

Diagnosis:
- line-completion options exist on both train pairs
- recolor options collapse to zero after the step-1 intermediate because the intermediate and final output are the same single-color line, so the current bounded recolor option generator has no `from_value != to_value` move to emit
- this is not ambiguity and not budget cutoff; it is a **no-op second-step sequence-generation hole**

Decision class:
- `generator correction candidate`

---

### D. `pilot_2_step_medium_ctx_09_extract_recolor_bg_transfer_v1`

- task_id: `pilot_2_step_medium_ctx_09_extract_recolor_bg_transfer_v1`
- composition_pair: `extract_largest_object -> recolor_symbol`
- difficulty_bucket: `medium`
- diagnostic_mode: `toy_task_type_preserved_guardrail`
- packet_status: `partial`
- train_fit_status: `partial_fit`
- selected_candidate_id: `pilot_2_step_medium_ctx_09_extract_recolor_bg_transfer_v1__toy_task_type_preserved_guardrail:sequence:1`
- selected_primitive_sequence: `[{"primitive_id": "recolor_symbol", "parameters": {"background_value": 5, "from_value": 8, "to_value": 0}}, {"primitive_id": "extract_largest_object", "parameters": {"background_value": 5}}]`
- step_1_primitive_and_parameters: `{"primitive_id": "recolor_symbol", "parameters": {"background_value": 5, "from_value": 8, "to_value": 0}}`
- step_2_primitive_and_parameters: `{"primitive_id": "extract_largest_object", "parameters": {"background_value": 5}}`
- intended_pair_represented: `yes`
- order_correct: `no`
- step_1_plausible: `no`
- step_2_plausible: `yes`
- non_exact_reason: `first_step_wrong_second_correct`
- composition_failure_category: `first_step_wrong_second_correct`
- root_cause: `step_2_parameter_inference_failure`

Intermediate grid summary (selected candidate):
```json
{
  "shape": [7, 7],
  "grid": [
    [0, 0, 0, 0, 0, 0, 0],
    [0, 5, 5, 5, 5, 5, 0],
    [0, 5, 5, 5, 5, 5, 0],
    [0, 5, 5, 5, 5, 5, 0],
    [0, 5, 5, 5, 5, 5, 0],
    [0, 5, 5, 5, 5, 5, 0],
    [0, 0, 0, 0, 0, 0, 0]
  ],
  "comparison_to_expected_intermediate": {
    "exact_match": false,
    "value_mismatch_count": 1
  }
}
```

Final predicted output (selected candidate):
```json
[
  [0, 0, 0, 0, 0, 0, 0],
  [0, 5, 5, 5, 5, 5, 0],
  [0, 5, 5, 5, 5, 5, 0],
  [0, 5, 5, 5, 5, 5, 0],
  [0, 5, 5, 5, 5, 5, 0],
  [0, 5, 5, 5, 5, 5, 0],
  [0, 0, 0, 0, 0, 0, 0]
]
```

Expected output (evaluation-side only):
```json
[
  [0, 0, 0, 0, 0, 0, 0],
  [0, 5, 5, 5, 5, 5, 0],
  [0, 5, 5, 5, 5, 5, 0],
  [0, 5, 5, 5, 5, 5, 0],
  [0, 5, 5, 5, 5, 5, 0],
  [0, 5, 5, 5, 5, 5, 0],
  [0, 5, 0, 0, 0, 0, 0]
]
```

Diagnosis:
- the intended pair is represented
- the intended candidate (`sequence:0`) is exact on the held-out test surface, but remains partial on train because recolor parameter carryover on one train pair is still off
- the selected reversed-order candidate misses by exactly one cell, which confirms this is narrow and localized
- best classification is **step-2 recolor inference failure** inside the extract/recolor family, not a broad generator issue

Decision class:
- `narrow repair candidate`

## 3. Decision summary

Per-row decisions:
- `pilot_2_step_easy_gen_02_noise_recolor_color_swap_v1` → `narrow repair candidate`
- `pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1` → `narrow repair candidate`
- `pilot_2_step_easy_gen_10_line_recolor_vertical_v1` → `generator correction candidate`
- `pilot_2_step_medium_ctx_09_extract_recolor_bg_transfer_v1` → `narrow repair candidate`

No row in this set should currently be accepted as a residual.

## 4. Next-lane recommendation

Best next move:
- **split into separate narrow lanes**

Why:
1. Three rows cluster cleanly into one family: bounded extract/recolor and noise/recolor carryover/inference.
2. One row is structurally different: `line_completion -> recolor_symbol` unsupported because step 2 becomes a no-op and the current bounded sequence generator emits no recolor option.
3. Keeping these separate will make proof and regression control tighter.

Recommended sequence:
1. `REPAIR_BOUNDED_ARC_2_STEP_EXTRACT_RECOLOR_AND_NOISE_RECOLOR_CARRYOVER_V1`
2. `REPAIR_BOUNDED_ARC_2_STEP_LINE_RECOLOR_NO_OP_SEQUENCE_GENERATION_V1`

## 5. Tracking counts

- new non-exacts diagnosed: `4`
- known stress residual touched: `no`
- candidate budget cutoff count: `0`
- generator ambiguity count: `0`
- narrow repairs recommended: `yes`

## 6. Validation posture

Diagnosis-only lane. Validation target:
- `python weslr/tests/release_gate_v1.py`
- `git diff --check`
- `./scripts/weslr_release_check.sh`
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`
