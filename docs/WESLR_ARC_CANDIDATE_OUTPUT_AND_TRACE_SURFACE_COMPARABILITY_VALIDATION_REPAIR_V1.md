# WESLR ARC CANDIDATE OUTPUT AND TRACE SURFACE COMPARABILITY VALIDATION REPAIR V1

## 1. Executive verdict
`arc_candidate_output_trace_surface_comparability_validation_repaired_but_needs_review`

## 2. Review finding addressed
Addressed the narrow defect recorded in:
- `docs/WESLR_ARC_CANDIDATE_OUTPUT_AND_TRACE_SURFACE_SCHEMA_HELPERS_IMPLEMENTATION_REVIEW_V1.md`

Prior defect:
- `derive_candidate_output_comparability(...)` could mark a surface comparable when `output_type="grid_int_matrix"` and `normalized_output` was merely non-`None`, even if the payload was malformed but JSON-safe.

Examples previously at risk:
- dicts
- strings
- numbers
- ragged lists
- lists with non-integers
- lists with booleans
- empty lists

## 3. Comparability validation repair
Repaired `derive_candidate_output_comparability(...)` so `comparable_to_expected=true` now requires all of:
- candidate output present
- expected output available flag true
- `serialization_status == "json_safe"`
- `output_type == "grid_int_matrix"`
- `normalized_output` passes strict structural validation through the same grid validation logic used by normalization

Repair behavior:
- malformed JSON-safe `normalized_output` now fail-closes to:
  - `comparable_to_expected=false`
  - `incomparable_reason_code="normalization_failed"`
- ordinary comparability derivation does not raise on malformed payloads
- booleans remain rejected even though Python `bool` subclasses `int`

Implementation note:
- repair adds a narrow internal validator path that reuses `normalize_grid_int_matrix(...)` rather than duplicating divergent shape logic

## 4. Normalization/validation consistency
Confirmed consistency after repair:
- `normalize_grid_int_matrix(...)` remains unchanged in behavior
- no weakening of existing rejection rules
- comparability validation now depends on the same strict structural contract as normalization
- normalization/comparability drift risk is reduced because the repair delegates validation back to the normalization primitive

## 5. Tests added/updated
Updated `weslr/tests/test_arc_candidate_output_trace_surface_v1.py` with focused comparability regression coverage for malformed JSON-safe payloads under `output_type="grid_int_matrix"`:
- dict → not comparable, `normalization_failed`
- string → not comparable, `normalization_failed`
- number → not comparable, `normalization_failed`
- ragged list → not comparable, `normalization_failed`
- list containing non-integer → not comparable, `normalization_failed`
- list containing bool → not comparable, `normalization_failed`
- empty list → not comparable, `normalization_failed`
- valid rectangular nested integer list remains comparable
- expected output unavailable still returns `expected_output_missing`

Existing coverage preserved:
- descriptor-only output remains not comparable
- non-JSON-safe output remains not comparable
- helper does not mutate input payloads
- recursive forbidden scoring-field detection remains covered
- no RNG/hash/random logic covered
- no replay runtime wiring import/call covered
- core trace/composed trace/MDL trace helper coverage retained

## 6. Boundary preservation
Confirmed preserved:
- no expected-answer values are read inside comparability derivation
- no RNG/hash/random logic introduced
- no replay runtime wiring introduced
- no replay preservation added
- no generator output emission added
- no assembler logic changed
- forbidden scoring-field detection remains recursive and unchanged
- core trace, composed trace, and MDL trace helpers were not changed in this lane

## 7. Safety boundaries
Confirmed:
- local only
- narrow helper repair only
- no push
- no public ARC/Kaggle data
- no hidden test output use
- no expected-answer use during generation or deservedness
- no generator deservedness repair
- no assembler deservedness repair
- no live replay scoring wiring
- no replay preservation
- no full V5 replay
- no emitter implementation
- no runtime solver wiring
- no ChatResponder changes
- no final-answer emission
- no learned scorer implementation
- no `.weslr`
- no external calls
- protected files unchanged

## 8. Recommended next safe local follow-up
`REVIEW_ARC_CANDIDATE_OUTPUT_AND_TRACE_SURFACE_COMPARABILITY_VALIDATION_REPAIR_V1`

Reason:
- the repair is narrow and likely correct
- this contract will be consumed by replay preservation
- a brief review lane is still the safer default before downstream dependency expansion
