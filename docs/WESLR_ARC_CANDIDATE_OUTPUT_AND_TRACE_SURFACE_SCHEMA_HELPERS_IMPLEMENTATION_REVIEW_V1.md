# WESLR ARC CANDIDATE OUTPUT AND TRACE SURFACE SCHEMA HELPERS IMPLEMENTATION REVIEW V1

## 1. Executive verdict
`arc_candidate_output_and_trace_surface_schema_helpers_review_needs_repair`

## 2. Review scope
Reviewed only:
- `docs/WESLR_ARC_CANDIDATE_OUTPUT_AND_TRACE_SURFACE_SCHEMA_HELPERS_IMPLEMENTATION_V1.md`
- `docs/WESLR_ARC_CANDIDATE_OUTPUT_AND_TRACE_SURFACE_FOR_REAL_SCORING_DESIGN_V1.md`
- `weslr/arc_candidate_output_trace_surface.py`
- `weslr/tests/test_arc_candidate_output_trace_surface_v1.py`

Out of scope and not changed:
- replay preservation
- live replay scoring wiring
- generator deservedness
- assembler deservedness
- full V5 replay
- emitter/runtime/final-answer behavior

## 3. Candidate output surface helper review
Confirmed implemented fields:
- `present`
- `output_type`
- `normalized_output`
- `raw_output_reference`
- `output_provenance`
- `serialization_status`
- `comparable_to_expected`
- `incomparable_reason_code`
- `schema_version`

Confirmed allowed-value inventories match the design:
- output types match design set exactly
- provenance values match design set exactly
- serialization statuses match design set exactly
- incomparable reason codes match design set exactly

Confirmed safe defaults:
- missing candidate output defaults to `present=false`, `output_type="missing"`, `serialization_status="missing"`, `comparable_to_expected=false`, `incomparable_reason_code="candidate_output_missing"`
- descriptor-only output is rejected from comparability by `derive_candidate_output_comparability(...)`

Review finding:
- the helper does **not fully satisfy** the requirement that invalid output must not become comparable by accident
- current `derive_candidate_output_comparability(...)` checks:
  - `present == True`
  - expected output availability flag only
  - `serialization_status == "json_safe"`
  - `output_type == "grid_int_matrix"`
  - `normalized_output is not None`
- it does **not** validate that `normalized_output` is actually a rectangular nested integer list before setting `comparable_to_expected=true`
- consequence: malformed but JSON-safe structures such as dicts or ragged lists can be marked comparable if passed in under `output_type="grid_int_matrix"`

Conclusion:
- field coverage and enum coverage are valid
- accidental comparability prevention is incomplete and needs narrow repair before replay preservation relies on this contract

## 4. Grid normalization and comparison review
Confirmed:
- `normalize_grid_int_matrix(...)` accepts only non-empty rectangular nested integer lists
- non-rectangular grids fail with `ValueError`
- non-integer cells fail with `ValueError`
- booleans are correctly rejected as integers
- `validate_json_safe_candidate_output_surface(...)` fail-closes non-JSON-safe surfaces to:
  - `serialization_status="non_json_safe_rejected"`
  - `comparable_to_expected=false`
  - `incomparable_reason_code="non_json_safe_output"`
- `compare_normalized_grid_int_matrices(...)` uses exact structural equality only after normalization
- no fuzzy matching
- no heuristic equivalence
- no RNG/random/hash scoring logic
- no expected-answer loading inside normalization or comparison helpers

Review note:
- normalization helper itself is valid
- the comparability helper currently does not require successful normalization before declaring comparability, which is the narrow defect in this lane

Conclusion:
- normalization/comparison primitives are locally sound
- comparability gating around those primitives needs repair

## 5. Core trace surface helper review
Confirmed `build_candidate_trace_surface(...)` implements:
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

Confirmed:
- emitted structure is JSON-safe when JSON-safe inputs are provided
- helper inserts no expected-answer fields
- helper inserts no scoring-result fields
- helper is shape-only and does not pretend to preserve live trace emission already

Conclusion:
- core trace surface helper is valid for this narrow schema lane

## 6. Composed trace surface helper review
Confirmed `build_composed_trace_surface(...)` implements:
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

Confirmed:
- `component_only_support` and `whole_composition_support` remain separate booleans
- helper shape is sufficient for later preservation wiring
- helper does not claim live composed traces are already emitted; it only builds packets

Conclusion:
- composed trace surface helper is valid for later replay-preservation use

## 7. MDL trace surface helper review
Confirmed `build_mdl_trace_surface(...)` implements:
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

Confirmed:
- `simplicity_primary_evidence` remains separate from `train_forced_grammar`
- `compact_but_not_forced` is not collapsed into `train_forced_grammar`
- helper does not claim live grammar outputs are already emitted

Conclusion:
- MDL trace surface helper is valid for this narrow schema lane

## 8. Scoring helper contract review
Confirmed:
- comparability can be checked from candidate-side surface metadata plus an `expected_output_available` flag, without reading expected-answer values
- exact comparison takes already-provided candidate and expected grids only
- helpers do not load expected answers themselves
- helper module does not influence generation
- helper module does not influence assembler deservedness
- no live replay scoring wiring was added

Critical review note:
- the contract is not yet fully safe because comparability can become true without proving the supposed normalized grid is structurally valid
- replay preservation should not consume this contract as-is if comparability booleans are meant to be trusted downstream

Conclusion:
- helper-only scoring boundaries are preserved
- comparability validation contract needs narrow repair first

## 9. Boundary/leakage helper review
Confirmed forbidden scoring-field inventory includes:
- `synthetic_expected_answer_for_scoring_only`
- `expected_output`
- `expected_answer`
- `post_ledger_scoring_status`
- `post_ledger_scoring_result`
- `deserved_exact_result`
- `deserved_but_wrong_result`
- `scoring_result`
- `scoring_label`

Confirmed behavior:
- `detect_forbidden_upstream_scoring_fields(...)` walks nested dict/list payloads recursively
- nested forbidden fields are detected, not just shallow keys
- helper does not mutate input payloads

Conclusion:
- boundary/leakage helper is valid for nested payload detection in this lane

## 10. Test adequacy review
Confirmed the 21 focused tests cover:
- missing/unscorable default candidate output surface
- deterministic integer-grid normalization
- non-rectangular rejection
- non-integer rejection
- non-JSON-safe rejection
- descriptor-only non-comparability
- exact normalized grid comparison
- missing/expected-missing/ambiguous unscorable reasons
- JSON-safe core/composed/MDL trace surfaces
- component-only vs whole-composition separation
- simplicity-primary vs train-forced separation
- forbidden scoring-field detection
- no RNG/hash/random use
- no replay runtime wiring import/call
- no input mutation

Test adequacy finding:
- tests are **too shallow** for the accidental-comparability boundary
- missing focused test coverage for malformed but JSON-safe `normalized_output` under `output_type="grid_int_matrix"`
- missing focused assertion that comparability must remain false unless normalization succeeds or the normalized structure is revalidated

Recommended narrow repair lane:
- `REPAIR_ARC_CANDIDATE_OUTPUT_AND_TRACE_SURFACE_COMPARABILITY_VALIDATION_V1`

Conclusion:
- current tests are good for broad shape coverage
- they are not sufficient to certify the comparability-safety contract needed before replay preservation

## 11. Safety boundary review
Confirmed:
- schema/helper implementation only
- no live replay scoring wiring
- no generator deservedness change
- no assembler deservedness change
- no full V5 replay
- no runtime/emitter/final-answer behavior
- no `.weslr`
- no external calls
- protected files unchanged in this review lane

## 12. Recommended next safe local follow-up
`REPAIR_ARC_CANDIDATE_OUTPUT_AND_TRACE_SURFACE_COMPARABILITY_VALIDATION_V1`

Why this should come before replay preservation:
- downstream replay preservation should not freeze or trust a `comparable_to_expected=true` surface that may not actually be a valid normalized integer grid
- repair should be narrow:
  - require structural grid validation before comparability can become true
  - add focused tests for malformed JSON-safe candidate outputs
  - keep replay wiring out of scope
