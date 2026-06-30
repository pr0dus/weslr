# WESLR ARC 2-Step 80 Shuffle Invariance Audit — No Repair V1

- **Dispatch**: `AUDIT_ARC_2_STEP_80_SHUFFLE_INVARIANCE_NO_REPAIR_V1`
- **Repo**: `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Branch**: `occ-discovery-doctrine-implementation-20260613`
- **Start HEAD**: `52413673e23a0dab3b801ab5c7cdbc0a254d7886`
- **End HEAD**: (to be committed)
- **Report**: `docs/WESLR_ARC_2_STEP_80_SHUFFLE_INVARIANCE_AUDIT_NO_REPAIR_V1.md`

## 1. Context

After the extract→recolor stable-to-value redesign, the combined 80 invariant is:
- **77 exact / 3 partial / 0 unsupported / 0 failed**
- **represented candidates: 80 / 80**
- **unsupported: 0**
- **accepted stress residual: 1**
- **original 40: 39 / 1 / 0 / 0**

This audit checks whether these results depend on accidental ordering. No repairs attempted.

## 2. Methodology

For each shuffle type, three fixed seeds were used: **0, 1, 7**.

| Shuffle type | Description | Mechanism |
|--------------|-------------|-----------|
| 1. Task order | Reorder task specs and entries before running `_run_pilot_from_plan` | Shuffled `task_specs` list; entries reordered to match |
| 2. Train-pair order | Shuffle `train_pairs` array within each task's packet | In-place shuffle of `train_pairs` list per entry |
| 3. `shuffled_renamed` mode | Built-in mode: reverses train pair order + renames task IDs | Uses `perturb_arc_style_task_metadata_v1` with `reverse_train_pairs=True` |
| 4. Variant order | Shuffle test input variants | **N/A** — each task has exactly 1 test input |
| 5. Candidate/tie order | Shuffle parameter option ordering within candidate generation | **N/A** — would require runner patch; see §5 |

## 3. Results

### 3.1 Task order shuffle (seeds 0, 1, 7)

| Seed | Exact | Partial | Unsupported | Failed | Represented | Same 3 partials? |
|------|-------|---------|-------------|--------|-------------|------------------|
| baseline | 77 | 3 | 0 | 0 | 80 | — |
| 0 | 77 | 3 | 0 | 0 | 80 | **Yes** |
| 1 | 77 | 3 | 0 | 0 | 80 | **Yes** |
| 7 | 77 | 3 | 0 | 0 | 80 | **Yes** |

**Verdict**: `shuffle_invariant` for task order.

### 3.2 Train-pair order shuffle (seeds 0, 1, 7)

| Seed | Exact | Partial | Unsupported | Failed | Represented | Same 3 partials? |
|------|-------|---------|-------------|--------|-------------|------------------|
| baseline | 77 | 3 | 0 | 0 | 80 | — |
| 0 | 77 | 3 | 0 | 0 | 80 | **Yes** |
| 1 | 77 | 3 | 0 | 0 | 80 | **Yes** |
| 7 | 77 | 3 | 0 | 0 | 80 | **Yes** |

**Verdict**: `shuffle_invariant` for train-pair order.

### 3.3 `shuffled_renamed` mode (built-in reverse train pairs)

The runner already includes a `shuffled_renamed` mode that reverses train pair order and appends a suffix to task IDs.

| Mode | Exact | Partial | Unsupported | Failed | Represented | Same 3 partials? |
|------|-------|---------|-------------|--------|-------------|------------------|
| baseline (primary) | 77 | 3 | 0 | 0 | 80 | — |
| `shuffled_renamed` | 77 | 3 | 0 | 0 | 80 | **Yes** |

**Verdict**: `shuffle_invariant` for built-in train-pair reversal.

### 3.4 Variant order shuffle

Each task in the 80-task pilot has exactly 1 test input (`TEST_INPUT_COUNT_V1 = 1`). Therefore, variant order shuffle is a no-op and was not tested.

**Verdict**: `not_applicable` — no variants to shuffle.

### 3.5 Candidate/tie-order sensitivity

The candidate generation and ranking mechanism is deterministic:

- Parameter options are generated from grid values in sorted order
- Ranking is by `(exact_matches, partial_matches)` descending
- Ties are broken by parameter ordering (which is deterministic)
- No stochastic tie-breaker or random sampling is used

Testing tie-order sensitivity would require monkey-patching `_generate_parameter_options` or the ranking function inside the runner, which violates the "no change to ranking mechanics" constraint.

**Verdict**: `not_tested` — would require runner modification. The ranking is structurally deterministic.

## 4. Partial rows under all tested permutations

The same 3 tasks remained partial across all tested shuffles:

1. `pilot_2_step_stress_08_fill_then_count_v1` — `accepted_stress_residual`
2. `pilot_2_step_easy_gen_02_noise_recolor_color_swap_v1` — `task_design_issue`
3. `pilot_2_step_medium_ctx_09_extract_recolor_bg_transfer_v1` — `unknown`

No exact→partial or partial→exact flips were observed.

## 5. Overall verdict

```
shuffle_invariant_under_tested_permutations
```

The combined 80 result (77/3/0/0) is stable under:
- Task order permutation
- Train-pair order permutation
- Built-in train-pair reversal (`shuffled_renamed` mode)

The 3 partial rows are stable under all tested permutations.

## 6. Limitations

- **Candidate/tie-order sensitivity** was not tested. The ranking uses deterministic tie-breaking by parameter ordering. If two candidates have identical exact/partial scores, the first in the generated list wins. This ordering comes from grid values sorted ascending, which is deterministic.
- **No stochastic elements** are present in the current runner. There is no random sampling, temperature, or probabilistic candidate selection.
- **Single test input per task** means variant order is not a meaningful axis.

## 7. Invariant preservation

| Check | Status |
|-------|--------|
| combined_80 unchanged | **Yes** — 77/3/0/0 |
| represented candidates unchanged | **Yes** — 80/80 |
| unsupported unchanged | **Yes** — 0 |
| code unchanged | **Yes** — audit script only, no runner changes |
| task specs unchanged | **Yes** — no task redesign |
| forced categories avoided | **Yes** |
| no repairs attempted | **Yes** |

## 8. Validation

| Check | Result |
|-------|--------|
| `git diff --check` | **PASS** |
| `python weslr/tests/release_gate_v1.py` | **PASS** |
| `./scripts/weslr_release_check.sh` | **PASS** |
| `./scripts/chat_weslr_de_health_check.sh --mode source-repo` | **PASS** |

## 9. Short receipt

| Field | Value |
|-------|-------|
| Start HEAD | `52413673e23a0dab3b801ab5c7cdbc0a254d7886` |
| End HEAD | (to be committed) |
| Report path | `docs/WESLR_ARC_2_STEP_80_SHUFFLE_INVARIANCE_AUDIT_NO_REPAIR_V1.md` |
| Shuffle audit completed | **yes** |
| Tested shuffle types | task order, train-pair order, built-in shuffled_renamed |
| Seeds used | 0, 1, 7 |
| Invariant preserved | **yes** |
| Combined 80 unchanged | **yes** (77/3/0/0) |
| Same 3 partials | **yes** |
| Order sensitivity detected | **no** |
| Code unchanged | **yes** |
| Task specs unchanged | **yes** |
| Validation | **PASS** |
| Push avoided | **yes** |
| Recommended next lane | `DESIGN_WESLR_FIRST_CONTROLLED_REAL_EVIDENCE_DIRECTION_RUN_V1` |
