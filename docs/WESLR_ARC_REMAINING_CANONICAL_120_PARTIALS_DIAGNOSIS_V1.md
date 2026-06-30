# WESLR ARC Remaining Canonical 120 Partials Diagnosis V1

- Dispatch: `DIAGNOSE_ARC_REMAINING_CANONICAL_120_PARTIALS_AFTER_OBJECT_COUNT_REPAIR_V1`
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `482c0cc2368f81c08a326595e3fa90546f5a52bb`
- Previous report: `docs/WESLR_ARC_OBJECT_COUNT_TO_PATTERN_DYNAMIC_COUNT_REPAIR_V1.md`

## Baseline under diagnosis

- canonical 120: `114 exact / 6 partial / 0 unsupported / 0 failed = 95.0%`
- synthetic solver suite: `48 exact / 0 partial`
- copy_grid: `10 exact / 0 partial`
- object_count_to_pattern: `10 exact / 0 partial`
- rotate_object_90: `7 exact / 3 partial`
- reflect_object_horizontal_or_vertical: `7 exact / 3 partial`

## High-level confirmation

Yes. All remaining canonical partials are exactly these six rows, and all are in:
- mode: `fully_stripped_train_pairs_plus_test_input_only`
- families: `rotate_object_90` and `reflect_object_horizontal_or_vertical`

There are:
- 3 rotate partials
- 3 reflect partials
- 0 remaining partials in any other mode
- 0 remaining partials in any other family

## Common diagnosis pattern

All six rows share the same structural pattern:

1. Train-pair structural inference still recovers the correct concrete family in stripped mode.
   - rotate rows: pair inference recovers `rotate_object_90`
   - reflect rows: pair inference recovers `reflect_object_horizontal_or_vertical`
2. But candidate generation then discards those exact-family inferences because stripped mode changes the task type away from the family-specific label.
3. That leaves `candidate_blueprints = []`.
4. The solver falls back to the unsupported abstract alias candidate:
   - selected primitive becomes `rotate`
   - selected candidate id becomes `...:rotate:0`
   - train_fit_status becomes `unsupported`
5. The synthetic solver suite then builds a fallback attempt grid for the unsupported abstract candidate, producing a mismatching prediction.

So the remaining partials are not caused by generator drift, expected-output drift, or validation artifacts.

## Remaining partial rows

### 1) rotate partial — variant 1
- mode: `fully_stripped_train_pairs_plus_test_input_only`
- task_id: `synthetic_rotate_object_90_variant_1_v1__fully_stripped`
- family: `rotate_object_90`
- variant: `0`
- test_input_index: `0`
- selected candidate id: `synthetic_rotate_object_90_variant_1_v1__fully_stripped:rotate:0`
- inferred primitive: `rotate`
- inferred parameters: `{"angle": 90}`
- train_fit_status: `unsupported`
- mismatch reason: `candidate_generation_gap,validation_mismatch`

Predicted output:
```json
[[0,0,0,0],[3,0,1,0],[0,1,1,1],[0,0,0,0]]
```

Expected output (evaluation-side only):
```json
[[0,0,0,0],[0,1,0,0],[0,1,1,0],[0,1,0,0]]
```

Root cause classification:
- primary: `missing family-specific toy_task_type guardrail`
- secondary symptom: `abstract alias issue`
- not supported by evidence: missing rotation parameter inference / executor limitation / generator ambiguity / validation artifact

Evidence note:
- stripped train-pair inference still recovered concrete `rotate_object_90` with parameters `{"object_value":1,"background_value":0}` on both train pairs
- those exact-family inferences were not promoted into candidate blueprints because stripped mode no longer matched the rotate family task-type allowlist

### 2) rotate partial — variant 2
- mode: `fully_stripped_train_pairs_plus_test_input_only`
- task_id: `synthetic_rotate_object_90_variant_2_v1__fully_stripped`
- family: `rotate_object_90`
- variant: `1`
- test_input_index: `0`
- selected candidate id: `synthetic_rotate_object_90_variant_2_v1__fully_stripped:rotate:0`
- inferred primitive: `rotate`
- inferred parameters: `{"angle": 90}`
- train_fit_status: `unsupported`
- mismatch reason: `candidate_generation_gap,validation_mismatch`

Predicted output:
```json
[[0,0,0,3,0],[0,0,2,0,0],[0,2,2,2,0],[0,0,0,0,0],[0,0,0,0,0]]
```

Expected output (evaluation-side only):
```json
[[0,0,0,0,0],[0,2,0,0,0],[0,2,2,0,0],[0,2,0,0,0],[0,0,0,0,0]]
```

Root cause classification:
- primary: `missing family-specific toy_task_type guardrail`
- secondary symptom: `abstract alias issue`
- not supported by evidence: missing rotation parameter inference / executor limitation / generator ambiguity / validation artifact

Evidence note:
- stripped train-pair inference still recovered concrete `rotate_object_90` with parameters `{"object_value":2,"background_value":0}` on all three train pairs
- the family evidence was dropped before candidate blueprint generation

### 3) rotate partial — variant 3
- mode: `fully_stripped_train_pairs_plus_test_input_only`
- task_id: `synthetic_rotate_object_90_variant_3_v1__fully_stripped`
- family: `rotate_object_90`
- variant: `2`
- test_input_index: `0`
- selected candidate id: `synthetic_rotate_object_90_variant_3_v1__fully_stripped:rotate:0`
- inferred primitive: `rotate`
- inferred parameters: `{"angle": 90}`
- train_fit_status: `unsupported`
- mismatch reason: `candidate_generation_gap,validation_mismatch`

Predicted output:
```json
[[0,0,0,0],[0,0,0,0],[0,0,3,0],[0,3,3,3],[0,0,0,0],[3,0,0,0]]
```

Expected output (evaluation-side only):
```json
[[0,0,0,0],[0,0,0,0],[0,3,0,0],[0,3,3,0],[0,3,0,0],[0,0,0,0]]
```

Root cause classification:
- primary: `missing family-specific toy_task_type guardrail`
- secondary symptom: `abstract alias issue`
- not supported by evidence: missing rotation parameter inference / executor limitation / generator ambiguity / validation artifact

Evidence note:
- stripped train-pair inference still recovered concrete `rotate_object_90` with parameters `{"object_value":3,"background_value":0}` on both train pairs
- candidate generation again collapsed to the unsupported abstract alias path

### 4) reflect partial — variant 1
- mode: `fully_stripped_train_pairs_plus_test_input_only`
- task_id: `synthetic_reflect_object_horizontal_or_vertical_variant_1_v1__fully_stripped`
- family: `reflect_object_horizontal_or_vertical`
- variant: `0`
- test_input_index: `0`
- selected candidate id: `synthetic_reflect_object_horizontal_or_vertical_variant_1_v1__fully_stripped:rotate:0`
- inferred primitive: `rotate`
- inferred parameters: `{"angle": 90}`
- train_fit_status: `unsupported`
- mismatch reason: `candidate_generation_gap,validation_mismatch`

Predicted output:
```json
[[0,0,0,0],[3,0,1,0],[0,0,1,1],[0,0,0,0]]
```

Expected output (evaluation-side only):
```json
[[0,0,0,0],[0,0,1,0],[0,1,1,0],[0,0,0,0]]
```

Root cause classification:
- primary: `missing family-specific toy_task_type guardrail`
- secondary symptom: `abstract alias issue`
- explicitly not supported by evidence: missing axis inference
- also not supported: executor limitation / generator ambiguity / validation artifact

Evidence note:
- stripped train-pair inference recovered reflect with `{"axis":"horizontal","object_value":1,"background_value":0}` on both train pairs
- axis inference is already present and correct
- exact reflect evidence was dropped before candidate blueprint generation

### 5) reflect partial — variant 2
- mode: `fully_stripped_train_pairs_plus_test_input_only`
- task_id: `synthetic_reflect_object_horizontal_or_vertical_variant_2_v1__fully_stripped`
- family: `reflect_object_horizontal_or_vertical`
- variant: `1`
- test_input_index: `0`
- selected candidate id: `synthetic_reflect_object_horizontal_or_vertical_variant_2_v1__fully_stripped:rotate:0`
- inferred primitive: `rotate`
- inferred parameters: `{"angle": 90}`
- train_fit_status: `unsupported`
- mismatch reason: `candidate_generation_gap,validation_mismatch`

Predicted output:
```json
[[0,0,0,3,0],[0,0,2,0,0],[0,0,2,2,0],[0,0,0,0,0],[0,0,0,0,0]]
```

Expected output (evaluation-side only):
```json
[[0,0,0,0,0],[0,0,2,2,0],[0,0,2,0,0],[0,0,0,0,0],[0,0,0,0,0]]
```

Root cause classification:
- primary: `missing family-specific toy_task_type guardrail`
- secondary symptom: `abstract alias issue`
- explicitly not supported by evidence: missing axis inference
- also not supported: executor limitation / generator ambiguity / validation artifact

Evidence note:
- stripped train-pair inference recovered reflect with `{"axis":"vertical","object_value":2,"background_value":0}` on all three train pairs
- axis inference is present and correct
- the failure is not “unknown axis”; it is “known axis but discarded family evidence”

### 6) reflect partial — variant 3
- mode: `fully_stripped_train_pairs_plus_test_input_only`
- task_id: `synthetic_reflect_object_horizontal_or_vertical_variant_3_v1__fully_stripped`
- family: `reflect_object_horizontal_or_vertical`
- variant: `2`
- test_input_index: `0`
- selected candidate id: `synthetic_reflect_object_horizontal_or_vertical_variant_3_v1__fully_stripped:rotate:0`
- inferred primitive: `rotate`
- inferred parameters: `{"angle": 90}`
- train_fit_status: `unsupported`
- mismatch reason: `candidate_generation_gap,validation_mismatch`

Predicted output:
```json
[[0,0,0,0],[0,0,0,0],[0,0,3,0],[0,0,3,3],[0,0,0,0],[3,0,0,0]]
```

Expected output (evaluation-side only):
```json
[[0,0,0,0],[0,0,0,0],[0,0,3,0],[0,3,3,0],[0,0,0,0],[0,0,0,0]]
```

Root cause classification:
- primary: `missing family-specific toy_task_type guardrail`
- secondary symptom: `abstract alias issue`
- explicitly not supported by evidence: missing axis inference
- also not supported: executor limitation / generator ambiguity / validation artifact

Evidence note:
- stripped train-pair inference recovered reflect with `{"axis":"horizontal","object_value":3,"background_value":0}` on both train pairs
- axis inference is already correct before candidate generation drops the family

## Required confirmation answers

### Are all remaining partials in the specified mode/families?
Yes.

All remaining partials are in:
- `fully_stripped_train_pairs_plus_test_input_only`
- `rotate_object_90`
- `reflect_object_horizontal_or_vertical`

No remaining partials exist outside that intersection.

### Root-cause mapping against the requested categories

Best-fit classification for all 6 rows:
- **primary:** `missing family-specific toy_task_type guardrail`
- **secondary symptom:** `abstract alias issue`

Not supported by evidence here:
- `missing axis inference` — no; reflect rows already infer the correct axis
- `missing rotation parameter inference` — no; rotate rows already infer concrete object/background rotation parameters during pair inference
- `executor limitation` — no; concrete family executors already work in non-stripped modes and in full synthetic suite
- `generator ambiguity` — no; train-pair family evidence is exact and stable
- `validation artifact` — no; validation correctly marks a real mismatch between fallback-attempt grid and expected grid

## Is a fix justified?

A fix is **technically justified** if the explicit goal is to improve the fully stripped lower-bound mode.

However, there is also a reasonable argument to leave these as lower-bound stress-test partials because:
- the synthetic solver suite itself is already `48 exact / 0 partial`
- all remaining misses are concentrated in the most adversarial stripped mode
- the concrete family evidence is already present; the misses are about what the stripped policy chooses to keep valid for candidate generation

So the decision is strategic rather than evidentiary.

## Recommended next lane

Recommended next lane from the provided options:
- **`leave fully stripped as lower-bound only and move to harder 2-step tasks`**

Why this is the best fit among the provided choices:
- `repair stripped rotate parameter inference` is not the real issue; the rotate parameters are already recovered in pair inference
- `repair stripped reflect axis inference` is not the real issue; the reflect axis is already recovered in pair inference
- `normalize abstract aliases` would clean up the visible fallback symptom but would not by itself restore the dropped exact-family candidate blueprints
- therefore the cleanest recommendation, given the current menu, is to treat fully stripped mode as a deliberate lower-bound stress surface and move on

If a future lane does target these 6 partials, the true repair should be framed more precisely as:
- restore bounded promotion of concrete rotate/reflect family evidence in stripped mode without reintroducing task-id or toy-task-type shortcuts

## Canonical status if no further repair is applied

Canonical 120 remains unchanged at:
- `114 exact / 6 partial / 0 unsupported / 0 failed`

That equals `95.0%` exact on canonical 120.

## Files added in this diagnosis lane

- `docs/WESLR_ARC_REMAINING_CANONICAL_120_PARTIALS_DIAGNOSIS_V1.md`

## Validation requested for this diagnosis lane

- `python weslr/tests/release_gate_v1.py`
- `git diff --check`
- `./scripts/weslr_release_check.sh`
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`

These validations passed for the report-only commit in this lane.
