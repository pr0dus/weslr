# WESLR ARC-Style Grid Solver Adapter Design V1

## Status
Design only. No implementation, no runtime solver, no ARC dataset ingestion, no score claims.

## Purpose
Define the missing adapter layer between WESLR’s existing solver-like engines and ARC-style grid tasks.

This adapter is not the solver core. It is the structured boundary that:
- represents grid tasks safely,
- extracts object/pattern candidates,
- generates bounded candidate rules/programs,
- validates against train pairs,
- ranks candidates,
- records failures,
- and supports replay/calibration.

## Existing WESLR substrate to reuse
Strongest existing helper surfaces:
- `weslr/raw_signal_cartographer.py`
- `weslr/neurosymbolic_algorithmic_inference_engine.py`
- `weslr/rule_pressure_engine.py`
- `weslr/dialectic_generator_loop.py`
- `weslr/nonlinear_inspiration_resonance_engine.py`
- `weslr/candidate_response_formation.py`
- `weslr/response_fit_self_check.py`
- `weslr/perspicuity_scorer.py`
- `weslr/friction_replay_harness.py`
- `weslr/forecast_calibration_bridge.py`
- `weslr/minimal_recursive_research_loop_dry_run_executor.py`
- recursive research loop scenario helpers
- `weslr/level3_answer_improvement_loop.py` for explanation/reporting only

## 1) ARC-style task packet schema

### Core packet fields
- `task_id`
- `task_source`
- `train_pairs`
- `test_input`
- `grid_format`
- `palette`
- `object_candidates`
- `transformation_candidates`
- `constraint_candidates`
- `candidate_outputs`
- `validation_results`
- `failure_notes`
- `trace`

### Train pair shape
- `train_pairs[] = {input_grid, output_grid, pair_id, notes}`

### Grid metadata
- `width`
- `height`
- `cell_values`
- `palette_ids`
- `has_background`
- `background_color`
- `invalid_cells`

### Candidate result shape
- `candidate_id`
- `candidate_type`
- `primitive_sequence`
- `train_fit_status`
- `partial_fit_metadata`
- `unsupported_assumptions`
- `rejection_reasons`
- `confidence_metadata`
- `calibration_metadata`

## 2) Grid representation boundary

### Allowed grid format
- JSON-safe 2D array of integers or short symbolic strings
- Rectangular only after normalization
- Explicit dimensions required
- Background color explicit or inferable only with trace

### Invalid input handling
- Non-rectangular grids: reject or normalize with failure note
- Mixed cell types: reject
- Empty grid: reject
- Oversized grid: cap or reject based on adapter policy
- Unknown symbols: preserve as symbols, do not coerce silently

### Representation rule
- No hidden benchmark content in docs or trace
- No answer-key leakage
- No direct object memory across tasks unless explicitly traced as calibration state

## 3) Object extraction boundary

Extract candidate structures using existing signal/object helpers and adapter-local metadata:
- connected components
- color groups
- bounding boxes
- repeated shapes
- symmetry candidates
- background candidates
- holes / borders / lines / regions
- relative positions and adjacency

Output should stay candidate-based, not authoritative.

## 4) Transformation primitive registry design

Safe primitive categories:
- copy
- move
- rotate
- reflect
- crop
- extend
- recolor
- count
- fill
- erase background
- complete symmetry
- extract object
- combine objects
- resize / scale
- border / frame operations

Registry rule:
- every primitive must declare required inputs, allowed assumptions, and failure mode labels
- primitives may compose, but only with bounded depth
- no uncontrolled recursion
- deterministic ordering only

## 5) Candidate rule/program packet

Each candidate should carry:
- `candidate_id`
- `primitive_sequence`
- `required_constraints`
- `train_pair_fit_status`
- `unsupported_assumptions`
- `rejection_reasons`
- `confidence_metadata`
- `calibration_metadata`
- `trace_refs`

Candidate types can include:
- direct copy/move/transform candidate
- object-relation candidate
- symmetry completion candidate
- count/paint candidate
- rule-composition candidate
- fallback/unknown candidate

## 6) Train-pair validator

Validator responsibilities:
- apply candidate to each train input
- compare to train output exactly
- record partial-match metadata
- localize failure to object extraction / color mapping / transform sequence / output formatting
- return explicit pass/fail plus trace

Validation outputs:
- exact match
- partial match
- mismatch category
- unsupported candidate
- ambiguous fit

## 7) Candidate search loop

Search order:
1. simple primitives
2. single-object transforms
3. multi-object transforms
4. composed candidates
5. bounded fallback hypotheses

Rules:
- deterministic ordering
- bounded depth
- no randomness unless explicitly approved later
- stop on confidence threshold or search budget
- preserve rejected hypotheses and reasons

## 8) Existing engine integration map

### `raw_signal_cartographer`
Role: grid/object/signal extraction
- Use for segmentation, recurring symbol detection, symmetry hints, and signal hypothesis capture.
- Best when raw task examples need structural inspection.

### `neurosymbolic_algorithmic_inference_engine`
Role: candidate rules/programs
- Use for structured inference packets, constraint application, candidate derivation, and rejection.
- Strongest candidate-program substrate.

### `rule_pressure_engine`
Role: constraint pressure and correction
- Use for testing candidate assumptions against train outputs and for correction packets.

### `dialectic_generator_loop`
Role: competing hypotheses / counter-hypotheses
- Use for seed candidates, counter-signals, and probe turns.

### `nonlinear_inspiration_resonance_engine`
Role: unusual operator transfer
- Use for structural transfer, transformation search, and operator bridging.

### `response_fit_self_check`
Role: candidate fit status
- Use for candidate fit labels, rejection/revision metadata, and self-check summaries.

### `perspicuity_scorer`
Role: candidate ranking / clarity / report quality
- Use for prioritization and explanation quality, not truth.

### `friction_replay_harness`
Role: failed task replay / regression
- Use for replaying failed tasks, preserving failure categories, and regression control.

### `forecast_calibration_bridge`
Role: confidence and calibration ledger
- Use for measured confidence, calibration records, and outcome tracking.

### `minimal_recursive_research_loop_dry_run_executor`
Role: loop scaffold / dry-run orchestration
- Use only as a dry-run orchestrator, not as a solver runtime.

### `level3_answer_improvement_loop`
Role: explanation/reporting only
- Not part of solving. May summarize traces and explain candidate selections.

## 9) Failure ledger design

Track repeatable failure categories:
- failed primitive
- failed object extraction
- failed color mapping
- overfit rule
- underfit rule
- ambiguity
- unsupported candidate
- missed transformation family
- repeated failure category

Each failure entry should include:
- `task_id`
- `candidate_id`
- `failure_category`
- `localization`
- `notes`
- `replay_ref`

## 10) No-leakage and benchmark boundary

Rules:
- public tasks only until explicitly approved
- no hidden/private benchmark ingestion
- no answer-key leakage
- no official score claims
- no training on evaluation data
- no protected benchmark content in docs unless allowed
- no ARC competition submission adapter until measured local proof exists

## 11) Evaluation harness plan

### Phase A: internal toy tasks
- use synthetic or hand-authored toy grid tasks only
- validate schema and trace packets

### Phase B: primitive registry helpers
- object extraction helpers
- primitive candidate helpers
- train-pair validator

### Phase C: bounded solver dry run
- candidate generation using existing engines
- exact-match / partial-match scoring
- no uncontrolled search

### Phase D: public ARC-style sample tasks
- public sample tasks only
- exact output scoring
- per-task trace packet
- per-engine contribution packet
- failure replay packet

### Phase E: competition adapter
- only after measured local proof
- no public competition claims until separately authorized

## 12) Future implementation sequence

### Phase 1
- schema helpers only
- toy task examples only
- no official ARC data ingestion

### Phase 2
- primitive registry helpers
- object extraction helpers
- train-pair validator

### Phase 3
- candidate generation with existing engines
- bounded solver dry run

### Phase 4
- public ARC-style dataset adapter
- benchmark harness

### Phase 5
- competition submission adapter, only after measured local proof

## 13) Recommendation
Best next lane:
- design adapter boundary first,
- then implement a thin ARC-style adapter over existing helpers,
- then add toy-task harnesses before any public sample task work.

## Final read
WESLR already has a substantial competition-reasoning substrate for extraction, hypothesis generation, constraint pressure, ranking, replay, and calibration. What is missing is the task-native ARC/grid adapter and validator layer, not a new reasoning core.
