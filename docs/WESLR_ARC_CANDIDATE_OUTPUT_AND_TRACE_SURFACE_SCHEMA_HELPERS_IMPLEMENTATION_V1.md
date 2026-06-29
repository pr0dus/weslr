# WESLR ARC CANDIDATE OUTPUT AND TRACE SURFACE SCHEMA HELPERS IMPLEMENTATION V1

## 1. Executive verdict
`arc_candidate_output_and_trace_surface_schema_helpers_implemented_but_needs_review`

## 2. Design reference
Implemented from:
- `docs/WESLR_ARC_CANDIDATE_OUTPUT_AND_TRACE_SURFACE_FOR_REAL_SCORING_DESIGN_V1.md`

Scope kept intentionally narrow:
- schema/helper module only
- no live replay scoring wiring
- no generator deservedness change
- no assembler deservedness change
- no runtime/emitter work

## 3. Candidate output surface helpers
Added `weslr/arc_candidate_output_trace_surface.py` with:
- `build_candidate_output_surface(...)`
- `normalize_grid_int_matrix(...)`
- `validate_json_safe_candidate_output_surface(...)`
- `derive_candidate_output_comparability(...)`
- `derive_unscorable_reason(...)`
- `compare_normalized_grid_int_matrices(...)`

Implemented concepts:
- `present`
- `output_type`
- `normalized_output`
- `raw_output_reference`
- `output_provenance`
- `serialization_status`
- `comparable_to_expected`
- `incomparable_reason_code`
- `schema_version`

First implementation normalization:
- rectangular nested integer lists only
- deterministic canonicalization only
- no expected-answer access
- no fuzzy matching

## 4. Core trace surface helpers
Added:
- `build_candidate_trace_surface(...)`

Implemented fields:
- `construction_mode`
- `construction_trace_complete`
- `forced_uniqueness_trace_present`
- `train_evidence_grounded`
- `missing_required_trace_fields`
- `unresolved_rivals`
- `candidate_trace_provenance`
- `trace_schema_version`
- `candidate_output_surface_present`
- `candidate_output_surface_type`

## 5. Composed trace surface helpers
Added:
- `build_composed_trace_surface(...)`

Implemented fields:
- `ordered_component_list`
- `component_execution_order`
- `component_records`
- `intermediate_outputs_after_each_component`
- `component_support_map`
- `component_only_support`
- `whole_composition_support`
- `interaction_assumptions`
- `alternative_order_surfaces`
- `alternative_subset_surfaces`
- `partial_transform_surfaces`
- `full_composition_alternatives`
- `sufficient_for_alternative_enumeration`
- `trace_schema_version`

This lane defines and validates shape only.
It does not emit live composed component traces yet.

## 6. MDL trace surface helpers
Added:
- `build_mdl_trace_surface(...)`

Implemented fields:
- `accepted_grammar_id`
- `accepted_grammar_record`
- `grammar_output_surface`
- `grammar_train_support_evidence`
- `simplicity_primary_evidence`
- `negative_evidence_present`
- `competing_grammar_records`
- `train_forced_grammar`
- `compact_but_not_forced`
- `sufficient_for_competing_grammar_diagnosis`
- `trace_schema_version`

This lane defines and validates shape only.
It does not emit live grammar outputs yet.

## 7. Scoring helper contracts
Implemented helper-only scoring contracts:
- comparability check without reading expected answer values
- unscorable-reason derivation
- deterministic exact equality for normalized integer grids

Explicitly not implemented in this lane:
- live replay scoring wiring
- expected-answer loading
- candidate selection
- fuzzy comparison
- RNG/hash scoring

## 8. Boundary/leakage helpers
Added:
- `FORBIDDEN_UPSTREAM_SCORING_FIELDS`
- `detect_forbidden_upstream_scoring_fields(...)`

Covered forbidden fields:
- `synthetic_expected_answer_for_scoring_only`
- `expected_output`
- `expected_answer`
- `post_ledger_scoring_status`
- `post_ledger_scoring_result`
- `deserved_exact_result`
- `deserved_but_wrong_result`
- `scoring_result`
- `scoring_label`

## 9. Tests added
Added focused suite:
- `weslr/tests/test_arc_candidate_output_trace_surface_v1.py`

Coverage includes:
- missing/unscorable default candidate output surface
- deterministic integer-grid normalization
- non-rectangular rejection
- non-integer rejection
- non-JSON-safe rejection
- descriptor-only non-comparability
- exact normalized grid comparison
- missing/expected-missing/ambiguous unscorable reason codes
- JSON-safe core/composed/MDL trace surfaces
- component-only vs whole-composition support separation
- simplicity-primary vs train-forced separation
- forbidden scoring-field detection
- no RNG/hash/random use
- no replay runtime wiring import/call
- no input mutation

## 10. Safety boundaries
Confirmed:
- local only
- schema/helper implementation only
- no push
- no public ARC/Kaggle data
- no hidden test output use
- no expected-answer use during generation or deservedness
- no generator deservedness repair
- no assembler deservedness repair
- no live replay scoring wiring
- no full V5 replay
- no emitter implementation
- no runtime solver wiring
- no ChatResponder changes
- no final-answer emission
- no learned scorer implementation
- no `.weslr`
- no external calls
- protected files unchanged

## 11. Recommended next safe local follow-up
`IMPLEMENT_ARC_CANDIDATE_OUTPUT_AND_TRACE_SURFACE_REPLAY_PRESERVATION_V1`

Why:
- schema/helper contracts now exist
- next safe step is preserving these surfaces through replay artifacts before enabling real live scoring
