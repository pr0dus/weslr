# WESLR ARC 2-Step Extract→Recolor Accepted Contract Still Partial — Diagnosis V1

- **Dispatch**: `DIAGNOSE_ACCEPTED_EXTRACT_RECOLOR_CONTRACT_STILL_PARTIAL_V1`
- **Repo**: `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Branch**: `occ-discovery-doctrine-implementation-20260613`
- **Start HEAD**: `489f17363907197520792f3ddf59b0e0e70b6a36`
- **End HEAD**: `489f17363907197520792f3ddf59b0e0e70b6a36` (no code change — diagnosis only)
- **Report**: `docs/WESLR_ARC_2_STEP_EXTRACT_RECOLOR_ACCEPTED_CONTRACT_STILL_PARTIAL_DIAGNOSIS_V1.md`

## 1. Executive verdict

The accepted extract→recolor memory contract does **not** improve the target row because **the contract is diagnostic-only; it is never wired into candidate generation or execution.**

The lane `IMPLEMENT_EXTRACT_RECOLOR_MEMORY_CONTRACT_TO_VALUE_INFERENCE_WITH_TRAIN_PAIR_PASSAGE_V1` added `to_value` inference, delta computation, and contract status to `_build_carryover_trace`. That trace is returned as metadata in `carryover_trace`. However, `_build_carryover_trace` is called **after** candidate generation (`_best_sequence_pair_fit`), not before. The inferred `to_value` is therefore never passed into `_primitive_parameter_options` for `recolor_symbol` during candidate search.

Consequence:
- Candidate 0 still sees `recolor_symbol` parameters generated as `{"background_value": 4}` with `from_value` and `to_value` as `dynamic_parameter_keys`.
- The candidate is partial because the best found `recolor_symbol` parameters happen to match train_0 but not train_1.
- No exact candidate exists in the generated candidate set.
- The accepted contract trace is present in metadata but never consumed by execution.

## 2. Current target row status

- **task_id**: `pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1`
- **packet_status**: `partial`
- **composition_failure_category**: `parameter_carryover_failure`
- **sequence_visibility_reason**: `standard_generated`
- **expected_exact_match**: `false`
- **step1_plausible**: `false`
- **step2_plausible**: `true`
- **selected_candidate_id**: `sequence:1` (wrong order: `recolor_symbol` → `extract_largest_object`)
- **best correct-order candidate (sequence:0)**: `partial`, mismatch 48, `final_exact: false`

## 3. Candidate analysis

### Candidate 0 (correct order: extract → recolor)
```json
{
  "primitive_pair": ["extract_largest_object", "recolor_symbol"],
  "packet_status": "partial",
  "final_exact": false,
  "total_mismatch": 48,
  "train_fit_status": "partial_fit",
  "selected_primitive_sequence": [
    {"primitive_id": "extract_largest_object", "parameters": {"background_value": 4}},
    {"primitive_id": "recolor_symbol", "parameters": {"background_value": 4}}
  ],
  "stable_sequence": [
    {"primitive_id": "extract_largest_object", "stable_parameters": {"background_value": 4}, "dynamic_parameter_keys": []},
    {"primitive_id": "recolor_symbol", "stable_parameters": {"background_value": 4}, "dynamic_parameter_keys": ["from_value", "to_value"]}
  ]
}
```

**Observation**: `recolor_symbol` parameters contain **only** `background_value`. `from_value` and `to_value` are not present in the selected parameters for this candidate. They are listed in `dynamic_parameter_keys`, meaning the generator could not resolve them as stable.

### Candidate 1 (wrong order: recolor → extract)
```json
{
  "primitive_pair": ["recolor_symbol", "extract_largest_object"],
  "packet_status": "partial",
  "final_exact": false,
  "total_mismatch": 23,
  "train_fit_status": "partial_fit"
}
```

This candidate ranks better (lower mismatch) but is still partial and wrong-order.

## 4. Execution consumption of inferred values — **NO**

The `_build_carryover_trace` function (line 776+) receives:
- `step1_exports` (after step 1 execution)
- `step2_parameters` (already selected by `_best_single_step_fit`)
- `current_grid` (intermediate grid after step 1)

It **reads** `to_value` from `step2_parameters` and reports `contract_status = "accepted"` if `to_value` is present. But `_build_carryover_trace` is called **after** candidate selection. It does not feed back into candidate generation.

The contract acceptance logic:
```python
if to_value is not None:
    contract_status = "accepted"
    rejection_reason = None
```

This checks whether the **already-selected** candidate happened to have a `to_value`. It does not cause the candidate to have a `to_value`.

## 5. Why `from_value` and `to_value` are missing from execution

In `_primitive_parameter_options` for `recolor_symbol`:
```python
if primitive_id == "recolor_symbol":
    options = []
    source_values = current_values or target_values
    destination_values = target_values or current_values
    for from_value in source_values[:4]:
        for to_value in destination_values[:4]:
            if from_value == to_value:
                continue
            options.append({"from_value": from_value, "to_value": to_value, "background_value": background_value})
    return _dedupe_parameter_options(options)[:12]
```

This generates parameter options using **grid cell values**, not using `step1_exports`. The `_build_carryover_trace` function's diagnostic metadata about `from_value`/`to_value` is never returned to `_primitive_parameter_options`.

## 6. Pair-level evidence

Train pair 0:
- `step1_exact`: true
- `step2_exact_from_oracle_intermediate`: true
- `final_exact`: true

Train pair 1:
- `step1_exact`: false
- `step2_exact_from_oracle_intermediate`: true
- `final_exact`: false
- `final_mismatch_count`: 23

Interpretation:
- Step 1 (extract) fails on train pair 1 (the extracted object has a different value).
- Step 2 (recolor) would be exact if given the correct intermediate.
- But because step 1 fails, the overall candidate is partial.
- Even when step 1 succeeds (train pair 0), the `recolor_symbol` parameters are not explicitly `from_value`/`to_value` — they rely on grid-value matching which happens to work.

## 7. Precise blocker classification

| Question | Answer |
|----------|--------|
| Is inferred `to_value` present in diagnostic trace? | **Yes** — `carryover_trace.to_value_resolution = "stable_train_inference"`, `contract_status = "accepted"` |
| Is inferred `to_value` passed into candidate execution? | **No** — trace is post-selection metadata only |
| Is `from_value` correctly passed into recolor execution? | **No** — not present in selected candidate parameters |
| Are resolved values applied to intermediate grid `E`? | **No** — execution uses `_apply_primitive` with the already-selected params |
| Does selected candidate use repaired contract path? | **No** — candidate was generated before trace exists |
| Is candidate exact but losing ranking? | **No** — no exact candidate exists in generated set |
| Is candidate itself still partial? | **Yes** — both candidates are partial |
| Remaining failure cause | **Import resolution not wired into candidate generation** (parameter option generation does not consume carryover metadata) |

## 8. What the accepted contract lane actually did

The lane added:
1. `to_value` inference from already-selected `step2_parameters`
2. Delta computation between intermediate and final grid
3. Contract status (`accepted`/`rejected`) in trace metadata
4. `introduced_values`, `removed_or_replaced_values`, `conclusive_delta`

What it did **not** do:
1. Pass inferred `from_value`/`to_value` back into `_primitive_parameter_options`
2. Add `extracted_object_value` → `from_value` mapping in parameter generation
3. Consume `carryover_trace` during candidate ranking
4. Change candidate budget or ranking

Therefore the lane is correctly scoped as a **diagnostic/trace** implementation, not a behavioral repair. The target row remains partial because the contract information is observed, not applied.

## 9. Recommended next implementation lane

`IMPLEMENT_EXTRACT_RECOLOR_CARRYOVER_INTO_PARAMETER_GENERATION_V1`

Scope:
- Modify `_primitive_parameter_options` for `recolor_symbol` to accept optional `carryover_hints` dict
- When preceded by `extract_largest_object`, use `extracted_object_value` from `step1_exports` as a `from_value` candidate
- When `to_value` can be inferred from train-pair delta or task spec, inject it into options
- Ensure `recolor_symbol` parameter options include `{"from_value": <inferred>, "to_value": <inferred>, "background_value": <inferred>}`
- Keep candidate budget unchanged (max 12 options)
- Keep ranking unchanged (still by mismatch count)
- No test output usage
- No task-id shortcuts
- Preserve all existing invariants

Expected outcome:
- Target row moves from `partial` to `exact`
- Combined 80 becomes `77 exact / 3 partial / 0 unsupported / 0 failed`
- Original 40 unchanged
- All leakage boundaries preserved

## 10. Invariants preserved during diagnosis

- original 40: `39 exact / 1 partial / 0 unsupported / 0 failed` — **preserved**
- combined 80: `76 exact / 4 partial / 0 unsupported / 0 failed` — **preserved**
- represented candidates: `80 / 80` — **preserved**
- unsupported: `0` — **preserved**
- accepted stress residual: `1` — **preserved**
- no code changes made — **preserved**
- git status clean — **yes**

## 11. Validation

- `python -m pytest weslr/tests/test_arc_style_synthetic_2_step_pilot_runner_v1.py::test_80_task_expansion_preserves_original_40_and_tracks_residuals -xvs` → **PASS**
- `python weslr/tests/release_gate_v1.py` → **PASS**
- `git diff --check` → **clean**
- `./scripts/weslr_release_check.sh` → **PASS**
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo` → **PASS**

## 12. Short receipt

| Field | Value |
|-------|-------|
| Start HEAD | `489f17363907197520792f3ddf59b0e0e70b6a36` |
| End HEAD | `489f17363907197520792f3ddf59b0e0e70b6a36` |
| Commit | no commit (diagnosis only) |
| Report path | `docs/WESLR_ARC_2_STEP_EXTRACT_RECOLOR_ACCEPTED_CONTRACT_STILL_PARTIAL_DIAGNOSIS_V1.md` |
| Accepted contract consumed by execution | **no** |
| Exact candidate exists | **no** |
| Ranking blocks exact candidate | **no** (no exact candidate generated) |
| Precise blocker classification | **import resolution not wired into parameter generation** — `_primitive_parameter_options` for `recolor_symbol` does not consume `carryover_trace` or `step1_exports` metadata |
| Target row unchanged | **yes** (expected — no behavioral changes made) |
| 80 continuity preserved | **yes** |
| Validation | **PASS** |
| Push avoided | **yes** |
| Recommended next lane | `IMPLEMENT_EXTRACT_RECOLOR_CARRYOVER_INTO_PARAMETER_GENERATION_V1` |
