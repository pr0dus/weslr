# WESLR ARC Object-Count-to-Pattern Remaining Partial Diagnosis V1

- Dispatch: `DIAGNOSE_ARC_OBJECT_COUNT_TO_PATTERN_REMAINING_PARTIAL_V1`
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `16351d950bbb1c5251c35f62f96eb8cc9ee3f874`
- Previous report: `docs/WESLR_ARC_COPY_GRID_VARIANT_2_GENERATOR_DISAMBIGUATION_V1.md`

## Handoff note

`WESLR_CURRENT_HANDOFF.md` reported verified HEAD `9ed508dbdc7899774c7ca19e932a04c3842f584d`, but the live repo HEAD for this approved lane was `16351d950bbb1c5251c35f62f96eb8cc9ee3f874`.

Per operator instruction for this lane only, the handoff HEAD was treated as stale and diagnosis proceeded only on live HEAD `16351d95`.

## Baseline under diagnosis

- canonical 120: `113 exact / 7 partial / 0 unsupported / 0 failed`
- copy_grid: `10 exact / 0 partial`
- object_count_to_pattern: `9 exact / 1 partial`
- rotate_object_90: `7 exact / 3 partial`
- reflect: `7 exact / 3 partial`

## Remaining non-exact object_count_to_pattern row

- mode: `full_metadata`
- task_id: `synthetic_object_count_to_pattern_variant_2_v1`
- variant: `1` (task name variant 2)
- test_input_index: `1`
- selected candidate id: `synthetic_object_count_to_pattern_variant_2_v1:object_count_to_pattern:0`
- inferred primitive: `object_count_to_pattern`
- inferred parameters:
  - `count=3`
  - `pattern_value=5`
  - `row_index=2`
  - `background_value=0`
- train_fit_status: `fit`
- packet status: `partial`
- mismatch reason: `validation_mismatch`
- failure reason detail: `attempt_grid_did_not_match_expected_output`

## Evidence

### Train pairs

All three train pairs are identical and encode a 3-object count:

```json
[
  {
    "input_grid": [[2,0,0,0,0],[0,2,0,0,0],[0,0,2,0,0],[0,0,0,0,0],[0,0,0,0,0]],
    "output_grid": [[0,0,0,0,0],[0,0,0,0,0],[5,5,5,0,0],[0,0,0,0,0],[0,0,0,0,0]]
  },
  {
    "input_grid": [[2,0,0,0,0],[0,2,0,0,0],[0,0,2,0,0],[0,0,0,0,0],[0,0,0,0,0]],
    "output_grid": [[0,0,0,0,0],[0,0,0,0,0],[5,5,5,0,0],[0,0,0,0,0],[0,0,0,0,0]]
  },
  {
    "input_grid": [[2,0,0,0,0],[0,2,0,0,0],[0,0,2,0,0],[0,0,0,0,0],[0,0,0,0,0]],
    "output_grid": [[0,0,0,0,0],[0,0,0,0,0],[5,5,5,0,0],[0,0,0,0,0],[0,0,0,0,0]]
  }
]
```

### Test input

```json
[[2,0,0,0,0],[0,2,0,0,0],[0,0,2,0,0],[0,0,0,2,0],[0,0,0,0,0]]
```

### Expected output (evaluation-side only)

```json
[[0,0,0,0,0],[0,0,0,0,0],[5,5,5,5,0],[0,0,0,0,0],[0,0,0,0,0]]
```

### Predicted output from selected candidate

```json
[[0,0,0,0,0],[0,0,0,0,0],[5,5,5,0,0],[0,0,0,0,0],[0,0,0,0,0]]
```

## What happened

The selected candidate is the semantically correct family and it fits train exactly, but it carries a fixed inferred parameter `count=3` from train evidence.

That fixed count is then applied to test input index 1, which actually contains 4 counted objects.

So:
- train-side inference succeeds
- candidate selection remains stable and sensible
- primitive family is correct
- execution uses the provided fixed parameter and therefore emits only three `5` cells instead of four
- validation correctly marks the packet partial

## Root-cause classification

Primary root cause: **parameter inference bug**

Why this classification fits best:
- **not a generator bug**: the generator intentionally varies test count from 3 to 4 for this variant, and the expected output matches that stated family semantics
- **not an expected-output generation bug**: the expected output is consistent with counting 4 non-background objects in the test input
- **not a primitive execution bug**: the primitive executor can already produce the correct output if `count` is left dynamic / recomputed from the test input instead of hard-coded to 3
- **not a candidate selection bug**: the selected candidate is the correct family and outranks the fallback copy candidate for good reasons
- **not a validation artifact**: validation is correctly detecting a real output mismatch

## Narrow-fix judgment

A narrow fix is **justified**.

## Recommended fix type

Recommended fix type: **parameter inference correction**

Most likely correct repair shape:
- stop freezing `count` to the train-only value for this family when the intended transformation is input-count-driven, or
- infer/encode this family in a way that recomputes count from the current test input at execution time rather than binding it to the train example count

## Why not the other fix types

- generator correction: not recommended for this lane’s follow-up, because the current generator is doing useful work by exposing the train-constant-count assumption
- primitive executor correction: not needed; the executor already supports dynamic counting behavior
- validation correction: not needed; validation caught a real mismatch
- no fix / document ambiguity: not appropriate; this is not ambiguous behavior, it is a concrete parameterization error

## Canonical impact if left unfixed

If unchanged, this leaves exactly one `object_count_to_pattern` partial in canonical 120:
- family total remains `9 exact / 1 partial`
- canonical total remains `113 exact / 7 partial / 0 unsupported / 0 failed`

## Files added in this diagnosis lane

- `docs/WESLR_ARC_OBJECT_COUNT_TO_PATTERN_REMAINING_PARTIAL_DIAGNOSIS_V1.md`

## Validation requested for this diagnosis lane

- `python weslr/tests/release_gate_v1.py`
- `git diff --check`
- `./scripts/weslr_release_check.sh`
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`

These validations passed for the report-only commit in this lane.
