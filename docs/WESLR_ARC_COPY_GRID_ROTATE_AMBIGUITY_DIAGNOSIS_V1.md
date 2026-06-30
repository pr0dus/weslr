# WESLR ARC Copy-Grid / Rotate Ambiguity Diagnosis V1

- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `d5c651e8e516113503a58051fa9e8e4c9416f6cd`
- Dispatch: `DIAGNOSE_ARC_COPY_GRID_ROTATE_AMBIGUITY_WITHOUT_FIX_V1`
- Scope: diagnosis only; no solver, ranking, or test-logic changes applied

## Baseline
Current truth-aligned canonical baseline at start HEAD:
- canonical 120: `109 exact / 11 partial / 0 unsupported / 0 failed`
- canonical exact %: `90.83333333333333%`
- `copy_grid`: `6 exact / 4 partial`

## Summary finding
`copy_grid` non-exacts are concentrated in **synthetic_copy_grid_variant_2_v1**.
There are **4 canonical non-exact rows**:
1. `full_metadata` / `synthetic_copy_grid_variant_2_v1` / test input `0`
2. `full_metadata` / `synthetic_copy_grid_variant_2_v1` / test input `1`
3. `toy_task_type_preserved_only` / `synthetic_copy_grid_variant_2_v1__toy_task_type_preserved_only` / test input `0`
4. `fully_stripped_train_pairs_plus_test_input_only` / `synthetic_copy_grid_variant_2_v1__fully_stripped` / test input `0`

The root cause has **two layers**:
1. **The synthetic family example is genuinely ambiguous** between concrete `copy` and concrete `rotate_object_90` on its train pairs.
2. The current dry-run candidate generator emits **unsupported abstract aliases** (`rotate`, `reflect`) rather than concrete executable primitives (`rotate_object_90`, `reflect_object_horizontal_or_vertical`). That causes the selected row to become `partial` through validation mismatch instead of becoming exact.

## Row-by-row diagnosis

### Row 1
- mode: `full_metadata`
- task_id: `synthetic_copy_grid_variant_2_v1`
- variant: `1` (task name variant 2)
- test_input_index: `0`
- selected candidate id: `synthetic_copy_grid_variant_2_v1:rotate:0`
- inferred primitive: `rotate`
- train_fit_status: `unsupported`
- packet status: `partial`
- mismatch reason: `validation_mismatch`

#### train_pairs
- `synthetic_copy_grid_variant_2_v1_train_0`
  - input = output =
    `[[2,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]`
- `synthetic_copy_grid_variant_2_v1_train_1`
  - input = output =
    `[[0,0,0,0,0],[0,2,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,5]]`
- `synthetic_copy_grid_variant_2_v1_train_2`
  - input = output =
    `[[0,0,0,0,0],[0,0,0,0,0],[0,0,2,0,0],[0,0,0,0,0],[0,0,0,0,0]]`

#### test_input
`[[0,2,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]`

#### expected output (evaluation-side only)
`[[0,2,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]`

#### primitive evidence on train pairs
- copy fit count: `3/3`
- rotate_object_90 fit count: `3/3`
- reflect horizontal fit count: `1/3`
- reflect vertical fit count: `1/3`
- other emitted dry-run candidates:
  - `rotate` alias: `unsupported`
  - `reflect` alias: `unsupported`

#### primitive evidence on test input (evaluation only)
- copy predicted grid = expected: **yes**
- rotate_object_90 predicted grid = expected: **yes**
- reflect horizontal predicted grid = expected: **no**
- reflect vertical predicted grid = expected: **yes**

#### dry-run emitted candidate packets
- selected primitive sequence: `[{"primitive_id": "rotate", "parameters": {"angle": 90}}]`
- candidate evaluations:
  - `synthetic_copy_grid_variant_2_v1:rotate:0` → primitive `rotate`, `unsupported_candidate=True`, `train_fit_status=unsupported`
  - `synthetic_copy_grid_variant_2_v1:reflect:1` → primitive `reflect`, `unsupported_candidate=True`, `train_fit_status=unsupported`

---

### Row 2
- mode: `full_metadata`
- task_id: `synthetic_copy_grid_variant_2_v1`
- variant: `1` (task name variant 2)
- test_input_index: `1`
- selected candidate id: `synthetic_copy_grid_variant_2_v1:rotate:0`
- inferred primitive: `rotate`
- train_fit_status: `unsupported`
- packet status: `partial`
- mismatch reason: `validation_mismatch`

#### train_pairs
Same three train pairs as Row 1.

#### test_input
`[[5,0,0,0,0],[0,0,2,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]`

#### expected output (evaluation-side only)
`[[5,0,0,0,0],[0,0,2,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]`

#### primitive evidence on train pairs
- copy fit count: `3/3`
- rotate_object_90 fit count: `3/3`
- reflect horizontal fit count: `1/3`
- reflect vertical fit count: `1/3`
- other emitted dry-run candidates:
  - `rotate` alias: `unsupported`
  - `reflect` alias: `unsupported`

#### primitive evidence on test input (evaluation only)
- copy predicted grid = expected: **yes**
- rotate_object_90 predicted grid = expected: **yes**
- reflect horizontal predicted grid = expected: **no**
- reflect vertical predicted grid = expected: **no**

#### dry-run emitted candidate packets
- selected primitive sequence: `[{"primitive_id": "rotate", "parameters": {"angle": 90}}]`
- candidate evaluations:
  - `synthetic_copy_grid_variant_2_v1:rotate:0` → primitive `rotate`, `unsupported_candidate=True`, `train_fit_status=unsupported`
  - `synthetic_copy_grid_variant_2_v1:reflect:1` → primitive `reflect`, `unsupported_candidate=True`, `train_fit_status=unsupported`

---

### Row 3
- mode: `toy_task_type_preserved_only`
- task_id: `synthetic_copy_grid_variant_2_v1__toy_task_type_preserved_only`
- variant: `1` (task name variant 2)
- test_input_index: `0`
- selected candidate id: `synthetic_copy_grid_variant_2_v1__toy_task_type_preserved_only:rotate:0`
- inferred primitive: `rotate`
- train_fit_status: `unsupported`
- packet status: `partial`
- mismatch reason: `validation_mismatch`

#### train_pairs
Same underlying three train pairs as Row 1.

#### test_input
`[[0,2,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]`

#### expected output (evaluation-side only)
`[[0,2,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]`

#### primitive evidence on train pairs
- copy fit count: `3/3`
- rotate_object_90 fit count: `3/3`
- reflect horizontal fit count: `1/3`
- reflect vertical fit count: `1/3`
- other emitted dry-run candidates:
  - `rotate` alias: `unsupported`
  - `reflect` alias: `unsupported`

#### primitive evidence on test input (evaluation only)
- copy predicted grid = expected: **yes**
- rotate_object_90 predicted grid = expected: **yes**
- reflect horizontal predicted grid = expected: **no**
- reflect vertical predicted grid = expected: **yes**

---

### Row 4
- mode: `fully_stripped_train_pairs_plus_test_input_only`
- task_id: `synthetic_copy_grid_variant_2_v1__fully_stripped`
- variant: `1` (task name variant 2)
- test_input_index: `0`
- selected candidate id: `synthetic_copy_grid_variant_2_v1__fully_stripped:rotate:0`
- inferred primitive: `rotate`
- train_fit_status: `unsupported`
- packet status: `partial`
- mismatch reason: `validation_mismatch`

#### train_pairs
Same underlying three train pairs as Row 1.

#### test_input
`[[0,2,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]`

#### expected output (evaluation-side only)
`[[0,2,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]`

#### primitive evidence on train pairs
- copy fit count: `3/3`
- rotate_object_90 fit count: `3/3`
- reflect horizontal fit count: `1/3`
- reflect vertical fit count: `1/3`
- other emitted dry-run candidates:
  - `rotate` alias: `unsupported`
  - `reflect` alias: `unsupported`

#### primitive evidence on test input (evaluation only)
- copy predicted grid = expected: **yes**
- rotate_object_90 predicted grid = expected: **yes**
- reflect horizontal predicted grid = expected: **no**
- reflect vertical predicted grid = expected: **yes**

## Answers to the diagnosis questions

### 1. Is this a true ambiguous task?
**Yes.**
At the concrete executable level, `synthetic_copy_grid_variant_2_v1` is genuinely ambiguous between:
- `copy`
- `rotate_object_90`

Both fit all three train pairs (`3/3`) and both match the expected output on the observed non-exact rows.

### 2. Is copy_grid the intended synthetic family?
**Yes.**
The generator family is explicitly `copy_grid`, and the hidden expected outputs are plain copies of the test inputs.

### 3. Is rotate a coincidental train-pair match?
**Yes.**
`rotate_object_90` matches because the chosen train examples are rotation-stable for the concrete object placements used in variant 2. That makes rotate a coincidental full-train fit, not evidence that the family was intended to be rotate-first.

### 4. Is the current selected candidate wrong, or is expected generation ambiguous?
**Both, but in different ways.**

- **Expected generation** is family-intended (`copy_grid`) but **not family-disambiguating**. The examples allow a concrete `rotate_object_90` explanation.
- The **current selected candidate is also wrong operationally** because the dry-run emits unsupported abstract aliases:
  - `rotate` instead of concrete `rotate_object_90`
  - `reflect` instead of concrete `reflect_object_horizontal_or_vertical`

So the row becomes partial not because concrete rotate fails, but because the emitted candidate packet is unsupported in the bounded synthetic solver path.

### 5. What exact local fix would be justified, if any?
A future fix would be justified, but **not in this diagnosis lane**.

The narrowest justified local fix depends on the intended policy:

#### If the goal is to preserve synthetic family identity (`copy_grid` should stay copy-like)
Use a **family guardrail fix**:
- when the synthetic family is `copy_grid`, do not let an abstract rotate alias win or stand in for the family;
- emit or prefer a concrete `copy` candidate in that family before abstract rotate/reflect aliases.

#### If the goal is to make the synthetic task intrinsically unambiguous
Use a **generator correction**:
- change `synthetic_copy_grid_variant_2_v1` so at least one train pair or one test input breaks the accidental `rotate_object_90` equivalence.

#### If the goal is only to remove the false partial without changing family semantics
Use a **candidate normalization / family guardrail style fix**:
- normalize abstract `rotate` → concrete `rotate_object_90` and abstract `reflect` → concrete reflect primitive before suite evaluation.
- This would likely make these rows exact, but it would not solve the underlying copy-vs-rotate ambiguity.

## Future-fix classification
Primary recommendation:
- **family guardrail fix**

Secondary viable recommendation if the synthetic family itself should be made unique:
- **generator correction**

Not recommended as the primary fix:
- pure **candidate ranking fix** alone, because it would hide the deeper fact that variant 2 is genuinely ambiguous at the concrete executable level
- **validation correction**, because the evaluation-side expected outputs are internally consistent with the generator’s copy intent
- **no fix, document ambiguity**, unless the team explicitly accepts family-level ambiguity inside the synthetic suite

## Final diagnosis judgment
- `copy_grid` canonical non-exact rows found: **4**
- canonical 120 changed during this diagnosis: **no**
- Root cause:
  1. variant 2 is a real copy-vs-rotate concrete ambiguity
  2. the selected dry-run candidate is an unsupported abstract `rotate` alias, so the suite records a partial mismatch instead of an exact match
- Most justified future fix type: **family guardrail fix**
- Secondary longer-term cleanup: **generator correction** for `synthetic_copy_grid_variant_2_v1`
