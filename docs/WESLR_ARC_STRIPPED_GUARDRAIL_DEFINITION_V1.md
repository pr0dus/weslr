# WESLR ARC Stripped Guardrail Definition V1

- Dispatch: `VERIFY_ARC_STRIPPED_GUARDRAIL_DEFINITION_V1`
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `7081da9f`
- Previous report: `docs/WESLR_ARC_SYNTHETIC_120_DIAGNOSTIC_RUNNER_V1.md`
- Handoff note: `WESLR_CURRENT_HANDOFF.md` still points at stale verified HEAD `9ed508db...`; this verification followed the operator-requested live repo state at `7081da9f`.

## 1. Executive verdict

Yes: `toy_task_type_preserved_only` is the correct **guardrail-preserving stripped mode** for this runner.

Reason:
- it keeps `train_pairs`
- it keeps `test_input`
- it preserves the family-bearing `trace.toy_task_type`
- it strips the richer generator/variant labeling that would otherwise over-inform attribution
- it does **not** introduce expected test output into solver generation

Yes: the current `fully_stripped_train_pairs_plus_test_input_only` cohort should be treated only as a **lower-bound diagnostic**.

Important nuance:
- the current implementation is **not literally raw `train_pairs + test_input` only** after packet reconstruction
- `build_arc_style_grid_task_packet_v1(...)` injects generic packet scaffolding and fallback trace defaults, including `toy_task_type = "synthetic"`
- that generic synthetic fallback is materially weaker than family-preserving `toy_task_type`, so the cohort still functions as a lower-bound stress test
- but its current label is slightly stronger than the literal runtime object it constructs

Judgment:
- architectural interpretation requested by the operator is correct
- `toy_task_type` is a guardrail signal, not expected-output leakage
- fully stripped remains useful, but should not be the main stripped score reported for future reflect-integration work

## 2. Inspection of current runner stripped modes

Inspected file:
- `weslr/arc_style_synthetic_diagnostic_runner.py`

Relevant construction points:
- `_minimal_trace(...)`
- `_rebuild_packet(...)`
- `build_arc_style_synthetic_diagnostic_plan_v1()`
- `_mode_summary(...)`

Observed mode definitions:
- `full_metadata`
  - uses the committed packet as generated
- `toy_task_type_preserved_only`
  - rebuilds the first packet of each family variant through `_rebuild_packet(...)`
  - sets `preserve_toy_task_type=True`
- `fully_stripped_train_pairs_plus_test_input_only`
  - rebuilds the first packet of each family variant through `_rebuild_packet(...)`
  - sets `preserve_toy_task_type=False`
- `shuffled_renamed`
  - perturbs metadata ordering / naming while preserving the family-bearing trace payload

## 3. What `toy_task_type_preserved_only` actually keeps

Confirmed preserved inputs:
- `train_pairs`: kept
- `test_input`: kept
- `trace.toy_task_type`: kept from the original packet

Also present after reconstruction because packet building injects schema-safe packet scaffolding:
- `task_id`
- `task_source`
- `grid_format`
- `palette`
- empty `object_candidates`
- empty `transformation_candidates`
- empty `constraint_candidates`
- empty `candidate_outputs`
- empty `validation_results`
- empty `failure_notes`
- generic/default trace fields such as:
  - `schema_version`
  - `internal_synthetic_only`
  - `toy_task`
  - `task_family`
  - `no_arc_dataset_ingestion`
  - `no_solver_runtime`
  - `no_candidate_search`
  - `no_object_extraction_implementation`
  - `no_primitive_executor`
  - `task_id`
  - `train_pair_count`
  - `palette_id_count`
  - `diagnostic_mode`
  - `synthetic_diagnostic_runner`

Interpretation:
- this mode preserves the **family-bearing guardrail token** (`toy_task_type`) while removing richer generator-side family/variant tagging
- that is the correct architectural stripped mode when the goal is to keep blueprint blocking / guarded family selection intact without carrying more metadata than necessary

## 4. What `toy_task_type_preserved_only` strips

Confirmed stripped from the rebuilt packet:
- packet-level `family_id`: not present
- packet-level `variant_index`: not present
- packet-level `primitive_id`: not present
- packet-level `ground_truth_transform`: not present
- packet-level `generator_metadata`: not present
- original `trace.synthetic_generator_family_id`: removed
- original `trace.synthetic_generator_variant_index`: removed
- original `trace.synthetic_expected_output_hidden`: removed
- optional shuffled `variant_key`: not present

Expected-output path check:
- the rebuilt packet passed into `run_arc_style_bounded_solver_dry_run_v1(...)` does not contain the expected test output
- the runner stores expected grids separately in entry metadata for packet-result validation after dry-run selection
- rerun trace flags remained:
  - `uses_test_output = false`
  - `uses_task_id_for_candidate_selection = false`
  - `uses_notes_for_candidate_selection = false`
  - `lookup_table_detected = false`

Judgment:
- preserving `toy_task_type` here is **not expected-output leakage**

## 5. What `fully_stripped_train_pairs_plus_test_input_only` actually keeps

Confirmed family-specific removals:
- original family-bearing `trace.toy_task_type` is not preserved
- original generator family/variant trace tags are not preserved
- packet-level family/variant/primitive/ground-truth/generator metadata are not preserved

But the current mode does **not** literally keep only raw `train_pairs` and raw `test_input`.

Observed reconstruction artifacts added by `build_arc_style_grid_task_packet_v1(...)`:
- `grid_format`
- `palette`
- empty candidate/constraint/validation lists
- generic trace defaults
- fallback `trace.toy_task_type = "synthetic"`
- derived packet metadata such as `train_pair_count` and `palette_id_count`

Interpretation:
- this cohort is better described as:
  - **family-specific toy-task-type stripped, generic packet scaffolding retained**
- because the remaining `toy_task_type` is only the generic fallback value `synthetic`, it does not preserve the family guardrail needed for blueprint blocking
- this is why it should be treated as a **lower-bound stress test only**

## 6. Rerun results

Rerun entry point:
- `weslr.arc_style_synthetic_diagnostic_runner.run_arc_style_synthetic_120_diagnostic_runner_v1`

Observed rerun:

| Mode | Packets | Exact | Partial | Unsupported | Failed | Exact % |
|---|---:|---:|---:|---:|---:|---:|
| full metadata | 48 | 41 | 3 | 4 | 0 | 85.4% |
| toy_task_type preserved only | 36 | 32 | 1 | 3 | 0 | 88.9% |
| fully stripped train_pairs + test_input only | 36 | 29 | 4 | 3 | 0 | 80.6% |
| shuffled / renamed | 36 | 32 | 1 | 3 | 0 | 88.9% |

Observed dependency summary:
- `original_full_metadata_exact = 41`
- `toy_task_type_preserved_only_exact = 32`
- `fully_stripped_exact = 29`
- `dependency_still_present = true`

## 7. Did toy_task_type-preserved still equal shuffled?

Yes.

Rerun result:
- `toy_task_type_preserved_only = 32 / 36 exact`
- `shuffled_renamed = 32 / 36 exact`

Interpretation:
- metadata ordering / renaming perturbation did not degrade the guardrail-preserving stripped cohort relative to the prior 120-runner report
- the meaningful drop remains between family-preserving `toy_task_type` and family-agnostic fully stripped reconstruction

## 8. Guardrail classification

`toy_task_type` should be classified as a **guardrail signal** for this lane.

Why:
- it constrains family/blueprint blocking posture
- it does not reveal expected test output
- it does not inject a solved candidate grid
- it does not wire candidate replay or scoring
- it is weaker than full generator metadata because it preserves only the family-bearing synthetic task type, not the richer variant/generator trace surface

This means:
- `toy_task_type_preserved_only` is the correct main stripped score for future reflect-boundary reasoning
- `fully_stripped_train_pairs_plus_test_input_only` remains valuable as a harsher lower-bound stress test, but should not be treated as the architectural guardrail baseline

## 9. Expected-output leakage and forbidden behavior check

Observed from rerun result flags:
- `uses_test_output = false`
- `uses_task_id_for_candidate_selection = false`
- `uses_notes_for_candidate_selection = false`
- `lookup_table_detected = false`

Observed leakage flags:
- `synthetic_only = true`
- `uses_kaggle_data = false`
- `uses_arc_public_data = false`
- `uses_hidden_private_data = false`
- `uses_solution_file = false`
- `uses_answer_key = false`
- `uses_test_output_for_candidate_generation = false`
- `official_score_claim = false`

No forbidden behavior was added or observed:
- no reflect integration
- no copy-grid repair
- no rotate repair
- no candidate_output_surface wiring
- no replay/scoring/final-answer behavior
- no `.weslr` access
- no protected runtime/chat file edits

## 10. Validation

Files changed in this lane:
- `docs/WESLR_ARC_STRIPPED_GUARDRAIL_DEFINITION_V1.md`
- `weslr/tests/release_gate_v1.py` (exact-path allowance for this report only)

Validation commands:
- `python3 -m py_compile weslr/tests/release_gate_v1.py`
- `pytest -q weslr/tests/test_arc_style_synthetic_diagnostic_runner_v1.py`
- `python3 weslr/tests/release_gate_v1.py`
- `git diff --check`
- `bash scripts/weslr_release_check.sh`
- `bash scripts/chat_weslr_de_health_check.sh --mode source-repo`

Validation result:
- `python3 -m py_compile weslr/tests/release_gate_v1.py`: **PASS**
- `pytest -q weslr/tests/test_arc_style_synthetic_diagnostic_runner_v1.py`: **PASS**
- `python3 weslr/tests/release_gate_v1.py`: **PASS**
- `git diff --check`: **PASS**
- `bash scripts/weslr_release_check.sh`: **PASS**
- `bash scripts/chat_weslr_de_health_check.sh --mode source-repo`: **PASS** (with expected optional non-runtime-host WARN probes)

## 11. Recommended next lane

Recommended next lane:
- `DESIGN_ARC_REFLECT_GUARDRAIL_PRESERVING_INTEGRATION_BOUNDARY_V1`

Reason:
- the stripped-mode interpretation is now verified
- future reflect integration should treat `toy_task_type_preserved_only` as the primary stripped guardrail baseline
- fully stripped should remain a lower-bound stress diagnostic only
- no solver repair work was mixed into this verification lane
