# WESLR ARC 2-Step Stress Fill-Then-Count Residual Bound Decision V1

- Dispatch: `DIAGNOSE_AND_DECIDE_BOUND_FOR_ARC_2_STEP_STRESS_FILL_THEN_COUNT_RIGHT_ORDER_RESIDUAL_V1`
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `fa8c0264b6e613aa46c148063482df812ef8224e`
- Previous report: `docs/WESLR_ARC_2_STEP_PARAMETER_CARRYOVER_AND_CONTEXTUAL_INFERENCE_REPAIR_V1.md`

## 1. Executive verdict

The sole remaining partial row is exactly the expected stress residual:
- `pilot_2_step_stress_08_fill_then_count_v1`
- `fill_region -> object_count_to_pattern`
- `stress`
- `toy_task_type_preserved_guardrail`

Observed current state:
- 2-step pilot: `39 exact / 1 partial / 0 unsupported / 0 failed`
- represented candidates: `40 / 40`
- candidate budget cutoff: `0`
- generator ambiguity: `0`
- accidental composition matches: `0`
- single-step canonical unchanged: `114 / 6 / 0 / 0`
- single-step solver suite unchanged: `48 / 0 / 0 / 0`
- fully stripped remains lower-bound only
- leakage boundaries preserved

Decision:
- **repair now:** no
- **accepted stress residual:** yes
- **move-to-80 approved:** yes

Reason:
This residual no longer looks like a narrow bounded parameter-carryover bug. The intended ordered pair is represented, but both the intended-order candidate and the reversed-order candidate remain non-plausible on train. Repairing this row now would likely require a broader semantic change to the fill/count interaction, not a small bounded parameter carryover fix.

## 2. Required row report

- task_id: `pilot_2_step_stress_08_fill_then_count_v1`
- composition_pair: `fill_region -> object_count_to_pattern`
- difficulty_bucket: `stress`
- diagnostic_mode: `toy_task_type_preserved_guardrail`
- packet_status: `partial`
- train_fit_status: `partial_fit`
- selected_candidate_id: `pilot_2_step_stress_08_fill_then_count_v1__toy_task_type_preserved_guardrail:sequence:1`
- selected_primitive_sequence: `[{"primitive_id": "object_count_to_pattern", "parameters": {"background_value": 2, "count": null, "pattern_value": 7, "row_index": 3}}, {"primitive_id": "fill_region", "parameters": {"background_value": 7, "fill_value": 0}}]`
- step_1_primitive_and_parameters: `{"primitive_id": "object_count_to_pattern", "parameters": {"background_value": 2, "count": null, "pattern_value": 7, "row_index": 3}}`
- step_2_primitive_and_parameters: `{"primitive_id": "fill_region", "parameters": {"background_value": 7, "fill_value": 0}}`
- non_exact_reason: `right_primitives_wrong_order`
- composition_failure_category: `right_primitives_wrong_order`
- right_pair_selected: `no`
- order_correct: `no`
- step_1_plausible: `no`
- step_2_plausible: `no`
- final_train_output_fits: `no`
- test_failure_classification: `accepted stress residual`

### Intermediate grid summary

Selected candidate intermediate (`sequence:1`):
```json
{
  "shape": [6, 6],
  "grid": [
    [2, 2, 2, 2, 2, 2],
    [2, 2, 2, 2, 2, 2],
    [2, 2, 2, 2, 2, 2],
    [2, 7, 2, 2, 2, 2],
    [2, 2, 2, 2, 2, 2],
    [2, 2, 2, 2, 2, 2]
  ],
  "comparison_to_expected_intermediate": {
    "exact_match": false,
    "value_mismatch_count": 16
  }
}
```

Expected intermediate (evaluation-side only):
```json
[
  [2, 2, 2, 2, 2, 2],
  [2, 4, 4, 4, 4, 2],
  [2, 4, 4, 4, 4, 2],
  [2, 4, 4, 4, 4, 2],
  [2, 4, 4, 4, 4, 2],
  [2, 2, 2, 2, 2, 2]
]
```

### Final predicted output

Selected candidate final prediction (`sequence:1`):
```json
[
  [2, 2, 2, 2, 2, 2],
  [2, 0, 0, 0, 0, 2],
  [2, 0, 0, 0, 0, 2],
  [2, 0, 0, 0, 0, 2],
  [2, 0, 0, 0, 0, 2],
  [2, 2, 2, 2, 2, 2]
]
```

### Expected output (evaluation-side only)

```json
[
  [0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0],
  [0, 7, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0]
]
```

## 3. What the evidence says

### 3.1 Intended-order candidate is present, but still bad

The intended ordered pair candidate exists:
- candidate id: `...:sequence:0`
- primitive pair: `fill_region -> object_count_to_pattern`

But it remains strongly non-plausible:
- step 1 parameters: `fill_region(background_value=2, fill_value=0)`
- step 2 parameters: `object_count_to_pattern(background_value=2, count=null, pattern_value=7, row_index=3)`
- step 1 exact on train: `false` for both train pairs
- step 2 exact from oracle intermediate: `false` for both train pairs
- total mismatch: `70`

This matters: the intended pair is not being blocked by search, budget, or emission. It is already present and still bad.

### 3.2 Reversed-order candidate wins only because it is less wrong

The selected candidate is the reversed pair:
- candidate id: `...:sequence:1`
- primitive pair: `object_count_to_pattern -> fill_region`
- total mismatch: `42`

It wins because:
- `42 < 70`
- ranking itself is behaving consistently with the existing bounded mismatch rule
- no evidence shows a hidden better intended-order candidate being suppressed

### 3.3 Both step families remain semantically off

For the intended pair:
- `fill_region` fills the interior with `0` instead of the expected `4`
- `object_count_to_pattern` then keeps border/background semantics that preserve `2` around the entire frame

For the reversed pair:
- `object_count_to_pattern` first creates a count mark, but still preserves the `2` frame semantics
- `fill_region(background_value=7, fill_value=0)` then wipes the row marker instead of producing the expected zero grid with a single `7`

That means the residual is not just a row-index miss or a carryover miss. The primitive semantics themselves do not align cleanly with this stress composition under current bounded definitions.

## 4. Decision requirements

### 4.1 Residual classification

Best classification:
- `accepted stress-bound case`

Not supported by current evidence:
- `true parameter carryover bug` — no; carryover/search issues were already repaired elsewhere, and the intended pair is present here
- `step-1 fill_region contextual inference bug` — not narrowly; step 1 is wrong, but fixing it now likely means changing fill semantics, not just parameter carryover
- `step-2 object_count_to_pattern contextual inference bug` — not narrowly; step 2 is also non-plausible even from the oracle intermediate in prior evaluation and still co-fails here
- `generator ambiguity` — no; both bounded candidates are deterministic and explicit
- `validation artifact` — no evidence

### 4.2 What repair would require

A meaningful repair would most likely require:
- `broader semantic model of fill/count interaction`

It does **not** look like it primarily requires:
- `narrow parameter inference improvement`
- `generator correction`
- `candidate ranking/budget change`

Why:
- the intended ordered pair already exists
- candidate budget is already sufficient for this pair
- ranking selects the lower-mismatch candidate consistently
- both candidate orders remain non-plausible, which points to primitive semantics under this stress interaction, not a simple bounded parameter miss

### 4.3 Decision

Decision:
- `repair now`: **no**
- `accept as known stress residual and move to 80`: **yes**

## 5. Move-to-80 gate

Current state is sufficient to proceed to the 80-task expansion because all of the following hold:
- `39 / 40 exact`
- `1 / 40 partial diagnosed`
- `0 unsupported`
- `40 / 40 represented candidates`
- no leakage
- no single-step regression
- fully stripped still lower-bound

Judgment:
- **move-to-80 approved: yes**

## 6. Why stopping here is the right bound

Stopping here is evidence-literate because:
1. The broad bounded 2-step mechanism is already working on `39 / 40`.
2. The last residual is isolated to one stress composition.
3. The residual is diagnosed, represented, deterministic, and non-ambiguous.
4. A further repair now would likely broaden primitive semantics rather than just tighten bounded carryover.
5. That broader semantic change is better judged in the next expansion context than forced into the 40-task closure lane.

## 7. Boundaries preserved

Confirmed unchanged:
- candidate budget/ranking unchanged
- no generator ambiguity introduced
- no leakage boundary regression
- no single-step regression
- no fully-stripped policy change
- no solver/generator/runner logic change in this lane

## 8. Validation posture

This is a diagnosis/decision-only lane. Validation target:
- `python weslr/tests/release_gate_v1.py`
- `git diff --check`
- `./scripts/weslr_release_check.sh`
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`

## 9. Recommended next lane

`EXPAND_BOUNDED_ARC_2_STEP_PILOT_FROM_40_TO_80_WITH_STRESS_RESIDUAL_TRACKING_V1`
