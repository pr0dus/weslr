# WESLR ARC 2-Step Sequence Generator and Intermediate Evaluator Design V1

- Dispatch: `DESIGN_BOUNDED_ARC_2_STEP_SEQUENCE_CANDIDATE_GENERATOR_AND_INTERMEDIATE_EVALUATOR_V1`
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `8d38829c1256c7d47ca41a56e24def61cf4fe89f`

## 1. Executive verdict

Design the **smallest safe bounded 2-step mechanism** that can begin solving the fixed internal 40-task 2-step pilot without tuning tasks to pass and without changing final-answer/scoring/benchmark surfaces.

Recommended verdict:
- add a **bounded represented 2-step candidate generator** with maximum sequence length `2`
- add an **explicit intermediate-state evaluator** that checks step-1 plausibility and step-2 plausibility on train pairs only
- keep the mechanism **deterministic, budgeted, train-pair-derived, and diagnostic-first**
- do **not** use expected test outputs
- do **not** change public score/reporting semantics in the first implementation lane

This design is intentionally narrow. It exists to repair the currently missing surface:
- no represented executable 2-step candidate sequence
- sequence search absent
- 2-step executor absent
- intermediate-state evaluation absent

## 2. Current validated starting point

Current validated state:
- single-step canonical: `114 exact / 6 partial / 0 unsupported / 0 failed = 95.0%`
- single-step solver suite: `48 exact / 0 partial`
- 2-step 40 pilot: `0 exact / 0 partial / 40 unsupported / 0 failed`

Current 2-step diagnosis already confirmed:
- no represented executable 2-step candidate sequence
- sequence search absent
- 2-step executor absent
- intermediate-state evaluation absent

Therefore the first safe repair target is not broader search, not task tuning, and not scoring changes.
The first target is simply: **represent and evaluate bounded 2-step candidates safely**.

## 3. Design goal

The mechanism should answer this question cleanly:

> If the current single-step family inference and parameter inference are composed into bounded 2-step candidates, do any of the fixed 40 pilot rows become train-plausible for the right structural reason?

Success in this design lane means:
- represented ordered pairs exist in candidate generation
- train-pair-only parameter flow is defined
- intermediate-state plausibility is observable
- failure categories become more specific than the current all-unsupported surface

Success in this design lane does **not** mean:
- ARC benchmark claims
- public score claims
- ARC-AGI-1/2 coupling
- final-answer readiness
- broad open-ended sequence search

## 4. Bounded 2-step candidate generator design

### 4.1 Scope

The generator should create only:
- single-step candidates already supported today
- bounded 2-step candidates with `max_sequence_length = 2`
- only from a **supported primitive-pair allowlist**

No sequence length greater than `2` is allowed.

### 4.2 Supported primitive pairs only

The first implementation should generate 2-step candidates only when the ordered pair appears in the fixed 40-task pilot composition inventory or in an explicit supported-pair table derived from that inventory.

That means:
- no wildcard primitive chaining
- no arbitrary Cartesian product of all primitives
- no open-ended compositional enumeration

Recommended source of truth:
- a deterministic ordered-pair allowlist aligned with the 40-task pilot design

### 4.3 Deterministic ordering

Candidate generation order should be deterministic and stable across reruns.

Recommended ordering rule:
1. pair allowlist order from the fixed pilot design source
2. within a pair, stable parameter signature ordering
3. single-step before two-step only if existing behavior depends on it; otherwise explicitly group by:
   - represented two-step candidates first for pair-enabled tasks
   - fallback single-step candidates second

Recommended tie-break fields:
- `candidate_role`
- `pair_rank`
- `parameter_signature`
- `primitive_id_sequence`

### 4.4 Strict candidate budget

The design must remain strongly budgeted.

Recommended first implementation budget:
- `MAX_PRIMITIVE_SEQUENCE_DEPTH_V2 = 2`
- `MAX_TWO_STEP_CANDIDATES_PER_TASK_V1 = 8`
- `MAX_TOTAL_CANDIDATES_PER_TASK_V2 = 12`

Budget rationale:
- enough room to represent real 2-step alternatives
- still small enough to stay auditable and deterministic
- avoids silent drift into unconstrained sequence search

Recommended 2-step candidate buckets within the budget:
1. intended-order family-supported pair candidates
2. reversed-order pair candidates when both primitives are individually plausible
3. bounded single-step fallback candidates from the existing surface

### 4.5 Generation recipe

For each task packet:
1. infer single-step family/parameter evidence from train pairs only
2. map that evidence into a bounded ordered-pair candidate set using the supported-pair allowlist
3. build candidate packets whose `primitive_sequence` has exactly two steps:
   - `[{primitive_id: p1, parameters: ...}, {primitive_id: p2, parameters: ...}]`
4. mark provenance fields:
   - `sequence_length`
   - `pair_supported = true|false`
   - `pair_source`
   - `parameter_flow_mode`
   - `uses_train_pairs_only = true`
5. never use test output during generation

### 4.6 What must not happen

The 2-step generator must not:
- construct sequences from expected test outputs
- use task ids or notes to special-case individual tasks
- create unbounded pair search over all primitives
- inject benchmark-facing logic
- bypass the existing bounded single-step safety posture

## 5. Intermediate-state evaluator design

### 5.1 Core evaluation loop

For each train pair and each 2-step candidate:
1. execute primitive 1 on the train input grid
2. obtain an intermediate grid
3. execute primitive 2 on that intermediate grid
4. compare the final produced grid to the train output grid
5. separately record whether step 1 and step 2 are individually plausible

### 5.2 What “individually plausible” means

The first implementation should remain bounded and diagnostic.
It does not need hidden ground-truth intermediate labels.

Recommended operational definition:
- **step-1 plausible** if primitive 1 produces an intermediate grid that permits at least one supported primitive-2 completion hypothesis consistent with the observed train output under train-pair-only inference
- **step-2 plausible** if primitive 2, when run from the produced intermediate grid with train-derived parameters, reduces the mismatch to the observed train output in the expected direction or reaches exact train fit

For synthetic internal pilot rows where the designed primitive pair is known at evaluation time, a diagnostic-only internal field may compare against the known synthetic intermediate for taxonomy labeling, but:
- this must be marked **evaluation-side only**
- this must not influence candidate generation
- this must not influence final answer behavior
- this must not be used outside the internal synthetic diagnostic surface

### 5.3 Required recorded fields

Each evaluated 2-step row should record at minimum:
- `selected_primitive_sequence`
- `sequence_generated`
- `sequence_executable`
- `step1_execution_status`
- `step2_execution_status`
- `step1_plausible`
- `step2_plausible`
- `intermediate_grid_available`
- `intermediate_evaluation_mode`
- `final_train_fit_status`
- `parameter_flow_trace`
- `failure_taxonomy_v2`

### 5.4 Canonical safe interpretation

This intermediate evaluator is diagnostic-first.
It exists to tell the difference between:
- missing sequence generation
- wrong order
- correct first step / wrong second step
- wrong first step / correct second step
- parameter carryover failure
- executor failure after a represented sequence exists

## 6. Parameter flow rules

### 6.1 Allowed source of parameters

All parameters must be inferred from:
- train pairs only
- train inputs only
- train outputs only where existing bounded inference already allows train-output-based rule inference

Blocked:
- any parameter derived from test output
- any parameter derived from evaluation-only expected outputs

### 6.2 Stable vs dynamic parameters

Define each parameter as either:
- **stable**: inferred once from train evidence and preserved unchanged across train/test execution
- **dynamic**: recomputed from the current execution input grid at the step where it is needed

Recommended initial split:

Stable examples:
- recolor `from_value` / `to_value` when constant across train pairs
- reflect `axis` when consistently inferred
- border/frame `thickness` when stable
- fill/border symbolic values when stable

Dynamic examples:
- object location dependent movement targets
- count-derived pattern counts
- extracted-object bounding boxes
- background-dominance derived values when the step-1 output changes the visible scene

### 6.3 Parameter flow contract

For a 2-step candidate, record per step:
- `parameter_origin = stable_train_inference | dynamic_recomputed_from_current_input | mixed`
- `parameter_values`
- `parameter_stability_confidence`

Recommended flow rule:
1. infer all stable parameters from train pairs first
2. execute step 1
3. recompute only explicitly dynamic parameters for step 2 from the **current intermediate grid**
4. preserve stable step-2 parameters unchanged
5. never recompute any parameter from expected test output

### 6.4 Failure handling for parameters

If step 2 needs a dynamic parameter but recomputation fails deterministically, classify as:
- `parameter_carryover_failure`

If execution proceeds with represented sequence and parameters but produced grids still mismatch for structural reasons, classify as:
- `intermediate_execution_failure`

## 7. Failure taxonomy v2

The first implementation should extend the current taxonomy with explicit 2-step sequence-aware labels.

Required labels:
- `right_primitives_wrong_order`
- `first_step_correct_second_wrong`
- `first_step_wrong_second_correct`
- `one_primitive_missing`
- `parameter_carryover_failure`
- `intermediate_execution_failure`
- `sequence_not_generated`

Recommended interpretation:
- `right_primitives_wrong_order`
  - both primitives are represented and plausible, but reversed order fits better than intended order
- `first_step_correct_second_wrong`
  - step 1 is plausible or exact at the intermediate level, but step 2 fails to complete correctly
- `first_step_wrong_second_correct`
  - step 2 family seems correct given a hypothetical intended intermediate, but actual step 1 output does not reach that state
- `one_primitive_missing`
  - existing single-step candidate explains only one stage of the transformation
- `parameter_carryover_failure`
  - a represented sequence exists, but stable/dynamic parameter flow breaks across steps
- `intermediate_execution_failure`
  - represented sequence executes with bounded parameters, yet the intermediate or final produced grids remain structurally wrong
- `sequence_not_generated`
  - no represented executable 2-step candidate entered evaluation for the row

Recommended compatibility rule:
- keep old taxonomy labels available for comparison in synthetic diagnostics where useful
- expose the new taxonomy as the primary 2-step diagnostic classification only after represented sequences exist

## 8. Safety and leakage boundaries

Preserve all current safety boundaries.

Allowed:
- train-pair-only rule inference
- train-pair-only parameter inference
- execution of represented candidate sequences against train inputs for diagnostics

Blocked:
- no answer-key construction
- no expected-test-output usage in candidate generation or parameter inference
- no score claims
- no ARC benchmark coupling
- no ARC-AGI-1 or ARC-AGI-2 participation changes
- no task-specific special casing
- no candidate_output_surface / replay / scoring / final-answer wiring in the first lane

Evaluation-side-only diagnostic allowance for synthetic internal rows:
- optional known intermediate comparison may be used only to label diagnostic categories
- never to create candidates
- never to rank benchmark-facing outputs
- never to influence final answer behavior

## 9. Smallest first implementation lane

Recommended first implementation lane:
- `IMPLEMENT_BOUNDED_ARC_2_STEP_SEQUENCE_CANDIDATE_GENERATOR_AND_INTERMEDIATE_EVALUATOR_V1`

### 9.1 Exact files likely touched

Primary likely code files:
- `weslr/arc_style_grid_solver_dry_run.py`
- `weslr/arc_style_synthetic_2_step_pilot_runner.py`

Primary likely tests:
- `weslr/tests/test_arc_style_grid_solver_dry_run_v1.py`
- `weslr/tests/test_arc_style_synthetic_2_step_pilot_runner_v1.py`

Primary likely docs:
- `docs/WESLR_ARC_2_STEP_SEQUENCE_GENERATOR_AND_INTERMEDIATE_EVALUATOR_IMPLEMENTATION_V1.md`

Possible release-gate exact-path allowance only if needed for new doc path:
- `weslr/tests/release_gate_v1.py`

### 9.2 Minimum test coverage required

Required focused tests:
1. represented 2-step candidate packet generation exists for supported ordered pairs
2. candidate generation stays deterministic across reruns
3. candidate budget is enforced exactly
4. step-1 execution produces intermediate grid deterministically
5. step-2 execution consumes intermediate grid, not original train input
6. stable parameters remain preserved across steps
7. dynamic parameters recompute only from current intermediate input
8. no test-output-derived parameter flow
9. taxonomy emits:
   - `sequence_not_generated`
   - `one_primitive_missing`
   - `first_step_correct_second_wrong`
   - `parameter_carryover_failure`
10. current single-step canonical behavior is not regressed outside the targeted 2-step pilot surface

### 9.3 Expected first-result range

Expected safe first-result range on the fixed 40-task pilot:
- lower bound acceptable: still `0 exact`, but with represented sequences and more specific taxonomy replacing blanket unsupported causes
- realistic first-success band: a **small non-zero number** of train-plausible or exact pilot rows, likely concentrated in easier pairs such as:
  - `move_single_object -> border_frame`
  - `fill_region -> line_completion`
  - `copy_grid -> recolor_symbol`
- unacceptable result:
  - sudden broad gains accompanied by evidence of leakage, task tuning, or benchmark-coupled logic

### 9.4 Rollback criteria

Rollback or stop the implementation lane immediately if any of the following appear:
- candidate generation uses expected test outputs directly or indirectly
- task-specific pair special-casing appears
- candidate budget expands beyond the declared bound without explicit design update
- single-step canonical baseline regresses materially
- scoring/final-answer/reporting surfaces change unintentionally
- represented 2-step sequences cannot be explained from train-pair-only evidence

## 10. Why this is the minimum safe mechanism

This is the minimum safe mechanism because it adds only what the diagnosis proved missing:
1. represented ordered 2-step candidates
2. bounded two-step execution against train pairs
3. explicit intermediate-state observability
4. stable/dynamic parameter flow rules
5. more specific sequence-aware failure taxonomy

It does **not** require:
- open-ended search
- benchmark wiring
- broader abstraction repair
- alias normalization
- final-answer generation
- public score claims

## 11. Recommended closure judgment

Design judgment:
- bounded 2-step candidate generation is now specified
- intermediate-state evaluation is now specified
- parameter-flow rules are now specified
- leakage boundaries remain preserved
- the next implementation lane can be scoped narrowly and audited against this design

Recommended next lane after this design:
- `IMPLEMENT_BOUNDED_ARC_2_STEP_SEQUENCE_CANDIDATE_GENERATOR_AND_INTERMEDIATE_EVALUATOR_V1`
