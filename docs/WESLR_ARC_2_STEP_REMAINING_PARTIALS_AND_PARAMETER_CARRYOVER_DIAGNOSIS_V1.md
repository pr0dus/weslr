# WESLR ARC 2-Step Remaining Partials and Parameter Carryover Diagnosis V1

- Dispatch: `DIAGNOSE_REMAINING_BOUNDED_ARC_2_STEP_PARTIALS_AND_PARAMETER_CARRYOVER_FAILURES_V1`
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `edb0ae6e4f64fc362fa1528ad563b837ed0173cc`
- Previous report: `docs/WESLR_ARC_2_STEP_SEQUENCE_GENERATOR_AND_INTERMEDIATE_EVALUATOR_IMPLEMENTATION_V1.md`

## 1. Executive verdict

Observed non-exact population is exactly the expected residual set: `6 partial + 1 unsupported` in `toy_task_type_preserved_guardrail` and `full_metadata`, with `fully_stripped_lower_bound` intentionally unchanged as a lower-bound diagnostic.

The remaining failures are not budget-driven and not ranking-driven. They are dominated by bounded parameter inference/context transfer gaps:
- `4` rows are primarily `step_1_parameter_inference_failure`
- `2` rows are primarily `step_2_parameter_inference_failure`
- `1` row is `sequence_not_generated` due to a step-2 parameter inference hole during candidate construction
- strict current-runner `parameter_carryover_failure` label appears on `1` row only, but the broader remaining surface is still contextual parameter transfer/inference, not search breadth

No evidence was found for:
- candidate budget cutoff
- ranking choosing the wrong candidate when a better bounded 2-step candidate was already available
- compatibility-matrix rejection of the unsupported row
- replay/scoring/final-answer wiring or any leakage boundary regression

## 2. Non-exact inventory

| task_id | composition_pair | bucket | status | primary root cause | intended pair represented | candidate count | step1 plausible | step2 plausible | marginal gain vs best single-step |
|---|---|---|---|---|---:|---:|---:|---:|---|
| `pilot_2_step_easy_03_extract_then_recolor_v1` | `extract_largest_object -> recolor_symbol` | `easy` | `partial` | `step_2_parameter_inference_failure` | no | 1 | no | yes | positive (19 -> 11) |
| `pilot_2_step_easy_08_fill_then_line_v1` | `fill_region -> line_completion` | `easy` | `partial` | `step_1_parameter_inference_failure` | yes | 2 | no | yes | negative (0 -> 24) |
| `pilot_2_step_easy_10_count_then_border_v1` | `object_count_to_pattern -> border_frame` | `easy` | `partial` | `step_1_parameter_inference_failure` | yes | 2 | no | yes | positive (54 -> 7) |
| `pilot_2_step_easy_18_fill_then_border_v1` | `fill_region -> border_frame` | `easy` | `partial` | `step_1_parameter_inference_failure` | yes | 2 | no | yes | positive (72 -> 24) |
| `pilot_2_step_medium_05_remove_noise_then_count_v1` | `remove_background_noise -> object_count_to_pattern` | `medium` | `unsupported` | `sequence_not_generated` | no | 0 | no | no | flat unsupported |
| `pilot_2_step_medium_09_fill_then_symmetry_v1` | `fill_region -> complete_symmetry` | `medium` | `partial` | `step_1_parameter_inference_failure` | yes | 2 | no | yes | negative (0 -> 24) |
| `pilot_2_step_stress_08_fill_then_count_v1` | `fill_region -> object_count_to_pattern` | `stress` | `partial` | `step_2_parameter_inference_failure` | yes | 2 | no | no | negative (42 -> 70) |

## 3. Aggregate scrutiny measurements

- non-exact rows found: `7`
- partial rows: `6`
- unsupported rows: `1`
- intended pairs represented: `5 / 7`
- strict `parameter_carryover_failure` labels: `1`
- accidental composition matches: `1`
- candidate budget cutoff count: `0`
- generator ambiguity count: `0`
- primary root-cause counts:
  - `step_1_parameter_inference_failure`: `4`
  - `step_2_parameter_inference_failure`: `2`
  - `sequence_not_generated`: `1`

Parameterization-count convention used in this diagnosis: `parameterization count = executable bounded 2-step candidates emitted with concrete parameters`. Under that definition, every represented candidate here is already parameterized, so the per-task parameterization count equals the candidate count.

## 4. Row-level diagnosis

### `pilot_2_step_easy_03_extract_then_recolor_v1`

- task_id: `pilot_2_step_easy_03_extract_then_recolor_v1`
- composition_pair: `extract_largest_object -> recolor_symbol`
- difficulty_bucket: `easy`
- diagnostic_mode: `toy_task_type_preserved_guardrail`
- packet_status: `partial`
- train_fit_status: `partial_fit`
- selected_candidate_id: `pilot_2_step_easy_03_extract_then_recolor_v1__toy_task_type_preserved_guardrail:sequence:1`
- selected_primitive_sequence: `[{"primitive_id": "recolor_symbol", "parameters": {"background_value": 0}}, {"primitive_id": "extract_largest_object", "parameters": {}}]`
- root_cause_classification: `step_2_parameter_inference_failure`
- non_exact_reason: `parameter_carryover_failure`
- composition_failure_category: `parameter_carryover_failure`
- candidate_count: `1`
- parameterization_count: `1`
- intended_pair_represented: `no`
- step_1_parameter_inference: `failure`
- step_2_parameter_inference: `success`
- full_pair_train_fit_result: `partial_fit`
- marginal_gain_vs_best_single_step: `positive (19 -> 11)`
- accidental_composition_match: `yes`
- step_1_primitive_and_parameters: `{"primitive_id": "recolor_symbol", "parameters": {"background_value": 0}, "dynamic_parameter_keys": []}`
- step_2_primitive_and_parameters: `{"primitive_id": "extract_largest_object", "parameters": {}, "dynamic_parameter_keys": ["background_value"]}`
- right_primitive_pair_selected: `no`
- order_correct: `no`
- step_1_plausible: `no`
- step_2_plausible: `yes`
- train_final_output_fit: `no`
- test_output_failed_due_to_parameter_transfer: `no`
- dynamic_or_contextual_parameters_recomputed_correctly: `no (dynamic background parameter varies across train pairs and the intended ordered pair never materializes)`
- diagnosis_note: Intended ordered pair was not generated because step-2 recolor inference failed on the extracted intermediate; the reversed pair accidentally matches the held-out evaluation output while remaining partial on train.
- intermediate_grid_summary:
```json
{
  "shape": [
    6,
    6
  ],
  "grid": [
    [
      0,
      7,
      0,
      0,
      0,
      0
    ],
    [
      0,
      3,
      3,
      3,
      3,
      0
    ],
    [
      0,
      3,
      3,
      3,
      3,
      0
    ],
    [
      0,
      3,
      3,
      3,
      3,
      0
    ],
    [
      0,
      3,
      3,
      3,
      3,
      0
    ],
    [
      7,
      0,
      0,
      0,
      0,
      0
    ]
  ],
  "comparison_to_expected_intermediate": {
    "exact_match": false,
    "value_mismatch_count": 17,
    "mismatch_cells": [
      {
        "row": 1,
        "column": 1,
        "expected": 7,
        "predicted": 3
      },
      {
        "row": 1,
        "column": 2,
        "expected": 7,
        "predicted": 3
      },
      {
        "row": 1,
        "column": 3,
        "expected": 7,
        "predicted": 3
      },
      {
        "row": 1,
        "column": 4,
        "expected": 7,
        "predicted": 3
      },
      {
        "row": 2,
        "column": 1,
        "expected": 7,
        "predicted": 3
      },
      {
        "row": 2,
        "column": 2,
        "expected": 7,
        "predicted": 3
      },
      {
        "row": 2,
        "column": 3,
        "expected": 7,
        "predicted": 3
      },
      {
        "row": 2,
        "column": 4,
        "expected": 7,
        "predicted": 3
      },
      {
        "row": 3,
        "column": 1,
        "expected": 7,
        "predicted": 3
      },
      {
        "row": 3,
        "column": 2,
        "expected": 7,
        "predicted": 3
      },
      {
        "row": 3,
        "column": 3,
        "expected": 7,
        "predicted": 3
      },
      {
        "row": 3,
        "column": 4,
        "expected": 7,
        "predicted": 3
      },
      {
        "row": 4,
        "column": 1,
        "expected": 7,
        "predicted": 3
      },
      {
        "row": 4,
        "column": 2,
        "expected": 7,
        "predicted": 3
      },
      {
        "row": 4,
        "column": 3,
        "expected": 7,
        "predicted": 3
      },
      {
        "row": 4,
        "column": 4,
        "expected": 7,
        "predicted": 3
      },
      {
        "row": 5,
        "column": 0,
        "expected": 0,
        "predicted": 7
      }
    ]
  }
}
```
- final_predicted_output:
```json
[
  [
    0,
    7,
    0,
    0,
    0,
    0
  ],
  [
    0,
    7,
    7,
    7,
    7,
    0
  ],
  [
    0,
    7,
    7,
    7,
    7,
    0
  ],
  [
    0,
    7,
    7,
    7,
    7,
    0
  ],
  [
    0,
    7,
    7,
    7,
    7,
    0
  ],
  [
    0,
    0,
    0,
    0,
    0,
    0
  ]
]
```
- expected_output_evaluation_side_only:
```json
[
  [
    0,
    7,
    0,
    0,
    0,
    0
  ],
  [
    0,
    7,
    7,
    7,
    7,
    0
  ],
  [
    0,
    7,
    7,
    7,
    7,
    0
  ],
  [
    0,
    7,
    7,
    7,
    7,
    0
  ],
  [
    0,
    7,
    7,
    7,
    7,
    0
  ],
  [
    0,
    0,
    0,
    0,
    0,
    0
  ]
]
```

### `pilot_2_step_easy_08_fill_then_line_v1`

- task_id: `pilot_2_step_easy_08_fill_then_line_v1`
- composition_pair: `fill_region -> line_completion`
- difficulty_bucket: `easy`
- diagnostic_mode: `toy_task_type_preserved_guardrail`
- packet_status: `partial`
- train_fit_status: `partial_fit`
- selected_candidate_id: `pilot_2_step_easy_08_fill_then_line_v1__toy_task_type_preserved_guardrail:sequence:0`
- selected_primitive_sequence: `[{"primitive_id": "fill_region", "parameters": {"background_value": 3, "fill_value": 4}}, {"primitive_id": "line_completion", "parameters": {"axis": "horizontal", "background_value": 3, "line_index": 1, "line_value": 4}}]`
- root_cause_classification: `step_1_parameter_inference_failure`
- non_exact_reason: `first_step_wrong_second_correct`
- composition_failure_category: `first_step_wrong_second_correct`
- candidate_count: `2`
- parameterization_count: `2`
- intended_pair_represented: `yes`
- step_1_parameter_inference: `failure`
- step_2_parameter_inference: `success`
- full_pair_train_fit_result: `partial_fit`
- marginal_gain_vs_best_single_step: `negative (0 -> 24)`
- accidental_composition_match: `no`
- step_1_primitive_and_parameters: `{"primitive_id": "fill_region", "parameters": {"background_value": 3, "fill_value": 4}, "dynamic_parameter_keys": []}`
- step_2_primitive_and_parameters: `{"primitive_id": "line_completion", "parameters": {"axis": "horizontal", "background_value": 3, "line_index": 1, "line_value": 4}, "dynamic_parameter_keys": []}`
- right_primitive_pair_selected: `yes`
- order_correct: `yes`
- step_1_plausible: `no`
- step_2_plausible: `yes`
- train_final_output_fit: `no`
- test_output_failed_due_to_parameter_transfer: `yes`
- dynamic_or_contextual_parameters_recomputed_correctly: `no`
- diagnosis_note: Right pair and right order are present, but step 1 under-fills the interior because the bounded 2-step helper does not carry the single-step border-aware fill parameterization into sequence mode.
- intermediate_grid_summary:
```json
{
  "shape": [
    6,
    6
  ],
  "grid": [
    [
      3,
      3,
      3,
      3,
      3,
      3
    ],
    [
      3,
      0,
      0,
      0,
      0,
      3
    ],
    [
      3,
      0,
      4,
      4,
      0,
      3
    ],
    [
      3,
      0,
      4,
      4,
      0,
      3
    ],
    [
      3,
      0,
      0,
      0,
      0,
      3
    ],
    [
      3,
      3,
      3,
      3,
      3,
      3
    ]
  ],
  "comparison_to_expected_intermediate": {
    "exact_match": false,
    "value_mismatch_count": 12,
    "mismatch_cells": [
      {
        "row": 1,
        "column": 1,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 1,
        "column": 2,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 1,
        "column": 3,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 1,
        "column": 4,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 2,
        "column": 1,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 2,
        "column": 4,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 3,
        "column": 1,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 3,
        "column": 4,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 4,
        "column": 1,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 4,
        "column": 2,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 4,
        "column": 3,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 4,
        "column": 4,
        "expected": 4,
        "predicted": 0
      }
    ]
  }
}
```
- final_predicted_output:
```json
[
  [
    3,
    3,
    3,
    3,
    3,
    3
  ],
  [
    3,
    0,
    0,
    0,
    0,
    3
  ],
  [
    3,
    0,
    4,
    4,
    0,
    3
  ],
  [
    3,
    0,
    4,
    4,
    0,
    3
  ],
  [
    3,
    0,
    0,
    0,
    0,
    3
  ],
  [
    3,
    3,
    3,
    3,
    3,
    3
  ]
]
```
- expected_output_evaluation_side_only:
```json
[
  [
    3,
    3,
    3,
    3,
    3,
    3
  ],
  [
    3,
    4,
    4,
    4,
    4,
    3
  ],
  [
    3,
    4,
    4,
    4,
    4,
    3
  ],
  [
    3,
    4,
    4,
    4,
    4,
    3
  ],
  [
    3,
    4,
    4,
    4,
    4,
    3
  ],
  [
    3,
    3,
    3,
    3,
    3,
    3
  ]
]
```

### `pilot_2_step_easy_10_count_then_border_v1`

- task_id: `pilot_2_step_easy_10_count_then_border_v1`
- composition_pair: `object_count_to_pattern -> border_frame`
- difficulty_bucket: `easy`
- diagnostic_mode: `toy_task_type_preserved_guardrail`
- packet_status: `partial`
- train_fit_status: `partial_fit`
- selected_candidate_id: `pilot_2_step_easy_10_count_then_border_v1__toy_task_type_preserved_guardrail:sequence:0`
- selected_primitive_sequence: `[{"primitive_id": "object_count_to_pattern", "parameters": {"background_value": 0, "count": null, "pattern_value": 8, "row_index": 0}}, {"primitive_id": "border_frame", "parameters": {"frame_value": 8}}]`
- root_cause_classification: `step_1_parameter_inference_failure`
- non_exact_reason: `first_step_wrong_second_correct`
- composition_failure_category: `first_step_wrong_second_correct`
- candidate_count: `2`
- parameterization_count: `2`
- intended_pair_represented: `yes`
- step_1_parameter_inference: `failure`
- step_2_parameter_inference: `success`
- full_pair_train_fit_result: `partial_fit`
- marginal_gain_vs_best_single_step: `positive (54 -> 7)`
- accidental_composition_match: `no`
- step_1_primitive_and_parameters: `{"primitive_id": "object_count_to_pattern", "parameters": {"background_value": 0, "count": null, "pattern_value": 8, "row_index": 0}, "dynamic_parameter_keys": []}`
- step_2_primitive_and_parameters: `{"primitive_id": "border_frame", "parameters": {"frame_value": 8}, "dynamic_parameter_keys": []}`
- right_primitive_pair_selected: `yes`
- order_correct: `yes`
- step_1_plausible: `no`
- step_2_plausible: `yes`
- train_final_output_fit: `no`
- test_output_failed_due_to_parameter_transfer: `yes`
- dynamic_or_contextual_parameters_recomputed_correctly: `no`
- diagnosis_note: Right pair and right order are present, but step 1 anchors the count pattern to row 0 instead of the contextual middle row; border framing is then correct on the wrong intermediate.
- intermediate_grid_summary:
```json
{
  "shape": [
    6,
    6
  ],
  "grid": [
    [
      0,
      8,
      8,
      8,
      0,
      0
    ],
    [
      0,
      0,
      0,
      0,
      0,
      0
    ],
    [
      0,
      0,
      0,
      0,
      0,
      0
    ],
    [
      0,
      0,
      0,
      0,
      0,
      0
    ],
    [
      0,
      0,
      0,
      0,
      0,
      0
    ],
    [
      0,
      0,
      0,
      0,
      0,
      0
    ]
  ],
  "comparison_to_expected_intermediate": {
    "exact_match": false,
    "value_mismatch_count": 6,
    "mismatch_cells": [
      {
        "row": 0,
        "column": 1,
        "expected": 0,
        "predicted": 8
      },
      {
        "row": 0,
        "column": 2,
        "expected": 0,
        "predicted": 8
      },
      {
        "row": 0,
        "column": 3,
        "expected": 0,
        "predicted": 8
      },
      {
        "row": 3,
        "column": 1,
        "expected": 7,
        "predicted": 0
      },
      {
        "row": 3,
        "column": 2,
        "expected": 7,
        "predicted": 0
      },
      {
        "row": 3,
        "column": 3,
        "expected": 7,
        "predicted": 0
      }
    ]
  }
}
```
- final_predicted_output:
```json
[
  [
    8,
    8,
    8,
    8,
    8,
    8
  ],
  [
    8,
    0,
    0,
    0,
    0,
    8
  ],
  [
    8,
    0,
    0,
    0,
    0,
    8
  ],
  [
    8,
    0,
    0,
    0,
    0,
    8
  ],
  [
    8,
    0,
    0,
    0,
    0,
    8
  ],
  [
    8,
    8,
    8,
    8,
    8,
    8
  ]
]
```
- expected_output_evaluation_side_only:
```json
[
  [
    8,
    8,
    8,
    8,
    8,
    8
  ],
  [
    8,
    0,
    0,
    0,
    0,
    8
  ],
  [
    8,
    0,
    0,
    0,
    0,
    8
  ],
  [
    8,
    7,
    7,
    7,
    0,
    8
  ],
  [
    8,
    0,
    0,
    0,
    0,
    8
  ],
  [
    8,
    8,
    8,
    8,
    8,
    8
  ]
]
```

### `pilot_2_step_easy_18_fill_then_border_v1`

- task_id: `pilot_2_step_easy_18_fill_then_border_v1`
- composition_pair: `fill_region -> border_frame`
- difficulty_bucket: `easy`
- diagnostic_mode: `toy_task_type_preserved_guardrail`
- packet_status: `partial`
- train_fit_status: `partial_fit`
- selected_candidate_id: `pilot_2_step_easy_18_fill_then_border_v1__toy_task_type_preserved_guardrail:sequence:0`
- selected_primitive_sequence: `[{"primitive_id": "fill_region", "parameters": {"background_value": 2, "fill_value": 4}}, {"primitive_id": "border_frame", "parameters": {"frame_value": 8}}]`
- root_cause_classification: `step_1_parameter_inference_failure`
- non_exact_reason: `first_step_wrong_second_correct`
- composition_failure_category: `first_step_wrong_second_correct`
- candidate_count: `2`
- parameterization_count: `2`
- intended_pair_represented: `yes`
- step_1_parameter_inference: `failure`
- step_2_parameter_inference: `success`
- full_pair_train_fit_result: `partial_fit`
- marginal_gain_vs_best_single_step: `positive (72 -> 24)`
- accidental_composition_match: `no`
- step_1_primitive_and_parameters: `{"primitive_id": "fill_region", "parameters": {"background_value": 2, "fill_value": 4}, "dynamic_parameter_keys": []}`
- step_2_primitive_and_parameters: `{"primitive_id": "border_frame", "parameters": {"frame_value": 8}, "dynamic_parameter_keys": []}`
- right_primitive_pair_selected: `yes`
- order_correct: `yes`
- step_1_plausible: `no`
- step_2_plausible: `yes`
- train_final_output_fit: `no`
- test_output_failed_due_to_parameter_transfer: `yes`
- dynamic_or_contextual_parameters_recomputed_correctly: `no`
- diagnosis_note: Right pair and right order are present, but fill-region again lacks the border-aware contextual parameterization, so border-frame only wraps an under-filled intermediate.
- intermediate_grid_summary:
```json
{
  "shape": [
    6,
    6
  ],
  "grid": [
    [
      2,
      2,
      2,
      2,
      2,
      2
    ],
    [
      2,
      0,
      0,
      0,
      0,
      2
    ],
    [
      2,
      0,
      4,
      4,
      0,
      2
    ],
    [
      2,
      0,
      4,
      4,
      0,
      2
    ],
    [
      2,
      0,
      0,
      0,
      0,
      2
    ],
    [
      2,
      2,
      2,
      2,
      2,
      2
    ]
  ],
  "comparison_to_expected_intermediate": {
    "exact_match": false,
    "value_mismatch_count": 12,
    "mismatch_cells": [
      {
        "row": 1,
        "column": 1,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 1,
        "column": 2,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 1,
        "column": 3,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 1,
        "column": 4,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 2,
        "column": 1,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 2,
        "column": 4,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 3,
        "column": 1,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 3,
        "column": 4,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 4,
        "column": 1,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 4,
        "column": 2,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 4,
        "column": 3,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 4,
        "column": 4,
        "expected": 4,
        "predicted": 0
      }
    ]
  }
}
```
- final_predicted_output:
```json
[
  [
    8,
    8,
    8,
    8,
    8,
    8
  ],
  [
    8,
    0,
    0,
    0,
    0,
    8
  ],
  [
    8,
    0,
    4,
    4,
    0,
    8
  ],
  [
    8,
    0,
    4,
    4,
    0,
    8
  ],
  [
    8,
    0,
    0,
    0,
    0,
    8
  ],
  [
    8,
    8,
    8,
    8,
    8,
    8
  ]
]
```
- expected_output_evaluation_side_only:
```json
[
  [
    8,
    8,
    8,
    8,
    8,
    8
  ],
  [
    8,
    4,
    4,
    4,
    4,
    8
  ],
  [
    8,
    4,
    4,
    4,
    4,
    8
  ],
  [
    8,
    4,
    4,
    4,
    4,
    8
  ],
  [
    8,
    4,
    4,
    4,
    4,
    8
  ],
  [
    8,
    8,
    8,
    8,
    8,
    8
  ]
]
```

### `pilot_2_step_medium_05_remove_noise_then_count_v1`

- task_id: `pilot_2_step_medium_05_remove_noise_then_count_v1`
- composition_pair: `remove_background_noise -> object_count_to_pattern`
- difficulty_bucket: `medium`
- diagnostic_mode: `toy_task_type_preserved_guardrail`
- packet_status: `unsupported`
- train_fit_status: `unsupported`
- selected_candidate_id: `none`
- selected_primitive_sequence: `[]`
- root_cause_classification: `sequence_not_generated`
- non_exact_reason: `sequence_not_generated`
- composition_failure_category: `sequence_not_generated`
- candidate_count: `0`
- parameterization_count: `0`
- intended_pair_represented: `no`
- step_1_parameter_inference: `failure`
- step_2_parameter_inference: `failure during candidate construction`
- full_pair_train_fit_result: `unsupported`
- marginal_gain_vs_best_single_step: `flat unsupported`
- accidental_composition_match: `no`
- step_1_primitive_and_parameters: `none`
- step_2_primitive_and_parameters: `none`
- right_primitive_pair_selected: `no`
- order_correct: `no`
- step_1_plausible: `no`
- step_2_plausible: `no`
- train_final_output_fit: `no`
- test_output_failed_due_to_parameter_transfer: `not_applicable`
- dynamic_or_contextual_parameters_recomputed_correctly: `no (step-2 options collapse to zero on one train pair)`
- diagnosis_note: Sequence construction reaches the intended pair, but object_count_to_pattern has zero bounded parameter options on one train pair after noise removal, so no executable 2-step candidate is emitted.
- intermediate_grid_summary: `none`
- final_predicted_output:
```json
null
```
- expected_output_evaluation_side_only:
```json
[
  [
    0,
    0,
    0,
    0,
    0,
    0
  ],
  [
    0,
    0,
    0,
    0,
    0,
    0
  ],
  [
    0,
    0,
    0,
    0,
    0,
    0
  ],
  [
    0,
    5,
    0,
    0,
    0,
    0
  ],
  [
    0,
    0,
    0,
    0,
    0,
    0
  ],
  [
    0,
    0,
    0,
    0,
    0,
    0
  ]
]
```
- unsupported_row_specific_answers:
  - intended ordered pair generated: `no`
  - any executable 2-step candidate generated: `no`
  - skipped by compatibility matrix: `no`
  - skipped by parameter inference: `yes`
  - skipped by budget: `no`
  - generator issue or sequence-generation issue: `sequence-generation issue caused by step-2 parameter inference hole`

### `pilot_2_step_medium_09_fill_then_symmetry_v1`

- task_id: `pilot_2_step_medium_09_fill_then_symmetry_v1`
- composition_pair: `fill_region -> complete_symmetry`
- difficulty_bucket: `medium`
- diagnostic_mode: `toy_task_type_preserved_guardrail`
- packet_status: `partial`
- train_fit_status: `partial_fit`
- selected_candidate_id: `pilot_2_step_medium_09_fill_then_symmetry_v1__toy_task_type_preserved_guardrail:sequence:0`
- selected_primitive_sequence: `[{"primitive_id": "fill_region", "parameters": {"background_value": 2, "fill_value": 4}}, {"primitive_id": "complete_symmetry", "parameters": {"axes": ["horizontal", "vertical"], "background_value": 2}}]`
- root_cause_classification: `step_1_parameter_inference_failure`
- non_exact_reason: `first_step_wrong_second_correct`
- composition_failure_category: `first_step_wrong_second_correct`
- candidate_count: `2`
- parameterization_count: `2`
- intended_pair_represented: `yes`
- step_1_parameter_inference: `failure`
- step_2_parameter_inference: `success`
- full_pair_train_fit_result: `partial_fit`
- marginal_gain_vs_best_single_step: `negative (0 -> 24)`
- accidental_composition_match: `no`
- step_1_primitive_and_parameters: `{"primitive_id": "fill_region", "parameters": {"background_value": 2, "fill_value": 4}, "dynamic_parameter_keys": []}`
- step_2_primitive_and_parameters: `{"primitive_id": "complete_symmetry", "parameters": {"axes": ["horizontal", "vertical"], "background_value": 2}, "dynamic_parameter_keys": []}`
- right_primitive_pair_selected: `yes`
- order_correct: `yes`
- step_1_plausible: `no`
- step_2_plausible: `yes`
- train_final_output_fit: `no`
- test_output_failed_due_to_parameter_transfer: `yes`
- dynamic_or_contextual_parameters_recomputed_correctly: `no`
- diagnosis_note: Right pair and right order are present, but fill-region under-fills first; symmetry can complete the oracle intermediate, not the generated one.
- intermediate_grid_summary:
```json
{
  "shape": [
    6,
    6
  ],
  "grid": [
    [
      2,
      2,
      2,
      2,
      2,
      2
    ],
    [
      2,
      0,
      0,
      0,
      0,
      2
    ],
    [
      2,
      0,
      4,
      4,
      0,
      2
    ],
    [
      2,
      0,
      4,
      4,
      0,
      2
    ],
    [
      2,
      0,
      0,
      0,
      0,
      2
    ],
    [
      2,
      2,
      2,
      2,
      2,
      2
    ]
  ],
  "comparison_to_expected_intermediate": {
    "exact_match": false,
    "value_mismatch_count": 12,
    "mismatch_cells": [
      {
        "row": 1,
        "column": 1,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 1,
        "column": 2,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 1,
        "column": 3,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 1,
        "column": 4,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 2,
        "column": 1,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 2,
        "column": 4,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 3,
        "column": 1,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 3,
        "column": 4,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 4,
        "column": 1,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 4,
        "column": 2,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 4,
        "column": 3,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 4,
        "column": 4,
        "expected": 4,
        "predicted": 0
      }
    ]
  }
}
```
- final_predicted_output:
```json
[
  [
    2,
    2,
    2,
    2,
    2,
    2
  ],
  [
    2,
    0,
    0,
    0,
    0,
    2
  ],
  [
    2,
    0,
    4,
    4,
    0,
    2
  ],
  [
    2,
    0,
    4,
    4,
    0,
    2
  ],
  [
    2,
    0,
    0,
    0,
    0,
    2
  ],
  [
    2,
    2,
    2,
    2,
    2,
    2
  ]
]
```
- expected_output_evaluation_side_only:
```json
[
  [
    2,
    2,
    2,
    2,
    2,
    2
  ],
  [
    2,
    4,
    4,
    4,
    4,
    2
  ],
  [
    2,
    4,
    4,
    4,
    4,
    2
  ],
  [
    2,
    4,
    4,
    4,
    4,
    2
  ],
  [
    2,
    4,
    4,
    4,
    4,
    2
  ],
  [
    2,
    2,
    2,
    2,
    2,
    2
  ]
]
```

### `pilot_2_step_stress_08_fill_then_count_v1`

- task_id: `pilot_2_step_stress_08_fill_then_count_v1`
- composition_pair: `fill_region -> object_count_to_pattern`
- difficulty_bucket: `stress`
- diagnostic_mode: `toy_task_type_preserved_guardrail`
- packet_status: `partial`
- train_fit_status: `partial_fit`
- selected_candidate_id: `pilot_2_step_stress_08_fill_then_count_v1__toy_task_type_preserved_guardrail:sequence:0`
- selected_primitive_sequence: `[{"primitive_id": "fill_region", "parameters": {"background_value": 2, "fill_value": 0}}, {"primitive_id": "object_count_to_pattern", "parameters": {"background_value": 2, "count": null, "pattern_value": 0, "row_index": 0}}]`
- root_cause_classification: `step_2_parameter_inference_failure`
- non_exact_reason: `none`
- composition_failure_category: `none`
- candidate_count: `2`
- parameterization_count: `2`
- intended_pair_represented: `yes`
- step_1_parameter_inference: `failure`
- step_2_parameter_inference: `failure`
- full_pair_train_fit_result: `partial_fit`
- marginal_gain_vs_best_single_step: `negative (42 -> 70)`
- accidental_composition_match: `no`
- step_1_primitive_and_parameters: `{"primitive_id": "fill_region", "parameters": {"background_value": 2, "fill_value": 0}, "dynamic_parameter_keys": []}`
- step_2_primitive_and_parameters: `{"primitive_id": "object_count_to_pattern", "parameters": {"background_value": 2, "count": null, "pattern_value": 0, "row_index": 0}, "dynamic_parameter_keys": []}`
- right_primitive_pair_selected: `yes`
- order_correct: `yes`
- step_1_plausible: `no`
- step_2_plausible: `no`
- train_final_output_fit: `no`
- test_output_failed_due_to_parameter_transfer: `yes`
- dynamic_or_contextual_parameters_recomputed_correctly: `no`
- diagnosis_note: Both steps are wrong in the selected candidate. Fill-region collapses the interior to 0 and object_count_to_pattern also fails even against the oracle intermediate, so this is the clearest remaining step-2 contextual inference miss.
- intermediate_grid_summary:
```json
{
  "shape": [
    6,
    6
  ],
  "grid": [
    [
      2,
      2,
      2,
      2,
      2,
      2
    ],
    [
      2,
      0,
      0,
      0,
      0,
      2
    ],
    [
      2,
      0,
      0,
      0,
      0,
      2
    ],
    [
      2,
      0,
      0,
      0,
      0,
      2
    ],
    [
      2,
      0,
      0,
      0,
      0,
      2
    ],
    [
      2,
      2,
      2,
      2,
      2,
      2
    ]
  ],
  "comparison_to_expected_intermediate": {
    "exact_match": false,
    "value_mismatch_count": 16,
    "mismatch_cells": [
      {
        "row": 1,
        "column": 1,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 1,
        "column": 2,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 1,
        "column": 3,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 1,
        "column": 4,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 2,
        "column": 1,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 2,
        "column": 2,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 2,
        "column": 3,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 2,
        "column": 4,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 3,
        "column": 1,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 3,
        "column": 2,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 3,
        "column": 3,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 3,
        "column": 4,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 4,
        "column": 1,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 4,
        "column": 2,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 4,
        "column": 3,
        "expected": 4,
        "predicted": 0
      },
      {
        "row": 4,
        "column": 4,
        "expected": 4,
        "predicted": 0
      }
    ]
  }
}
```
- final_predicted_output:
```json
[
  [
    2,
    0,
    2,
    2,
    2,
    2
  ],
  [
    2,
    2,
    2,
    2,
    2,
    2
  ],
  [
    2,
    2,
    2,
    2,
    2,
    2
  ],
  [
    2,
    2,
    2,
    2,
    2,
    2
  ],
  [
    2,
    2,
    2,
    2,
    2,
    2
  ],
  [
    2,
    2,
    2,
    2,
    2,
    2
  ]
]
```
- expected_output_evaluation_side_only:
```json
[
  [
    0,
    0,
    0,
    0,
    0,
    0
  ],
  [
    0,
    0,
    0,
    0,
    0,
    0
  ],
  [
    0,
    0,
    0,
    0,
    0,
    0
  ],
  [
    0,
    7,
    0,
    0,
    0,
    0
  ],
  [
    0,
    0,
    0,
    0,
    0,
    0
  ],
  [
    0,
    0,
    0,
    0,
    0,
    0
  ]
]
```

## 5. Unsupported-row diagnosis

The sole unsupported row is `pilot_2_step_medium_05_remove_noise_then_count_v1`.

Observed cause chain:
- packet trace still preserves the intended supported pair `remove_background_noise -> object_count_to_pattern`
- step 1 (`remove_background_noise`) does produce bounded options and a best fit on both train pairs
- step 2 (`object_count_to_pattern`) produces zero bounded parameter options on one train pair after the noise-removal intermediate
- sequence generation therefore aborts before emitting any executable candidate
- this is not a compatibility-matrix skip and not a budget skip
- recommended interpretation: `sequence_not_generated` with a step-2 contextual parameter inference hole inside the sequence generator

## 6. Candidate-budget and ranking findings

- candidate budget cutoff count: `0`
- no row showed evidence that a better bounded 2-step candidate already existed but lost to ranking
- where two candidates were present, the selected candidate was the lower-mismatch candidate or tied for lowest mismatch
- the problem is candidate quality / parameterization, not search ordering

## 7. Recommended next implementation

Recommended next implementation: `parameter carryover repair`.

Why this is the best next move among the offered options:
- the dominant residual surface is contextual parameter transfer/inference, not search breadth
- `4` rows fail because step 1 is the right family but loses contextual parameters in sequence mode
- `2` more rows fail because step 2 lacks enough contextual parameter inference once the intermediate changes
- the unsupported row is also a contextual parameter inference failure during sequence construction
- there is no evidence that raising budget or changing ranking is the next leverage point

Practical sequencing note:
- if the next lane must stay narrow, repair step-1 contextual carryover for `fill_region` / `object_count_to_pattern` first, then revisit step-2 contextual inference for `recolor_symbol` and `object_count_to_pattern` on generated intermediates

## 8. Validation posture

This lane is diagnosis-only. No solver/generator/runner logic was changed. Validation target remains:
- `python weslr/tests/release_gate_v1.py`
- `git diff --check`
- `./scripts/weslr_release_check.sh`
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`
