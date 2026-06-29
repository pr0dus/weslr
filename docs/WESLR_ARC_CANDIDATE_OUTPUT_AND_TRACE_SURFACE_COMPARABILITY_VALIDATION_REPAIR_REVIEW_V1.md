# WESLR ARC CANDIDATE OUTPUT AND TRACE SURFACE COMPARABILITY VALIDATION REPAIR REVIEW V1

## 1. Executive verdict
`arc_candidate_output_trace_surface_comparability_validation_repair_review_valid`

## 2. Review scope
Reviewed only:
- `docs/WESLR_ARC_CANDIDATE_OUTPUT_AND_TRACE_SURFACE_COMPARABILITY_VALIDATION_REPAIR_V1.md`
- `docs/WESLR_ARC_CANDIDATE_OUTPUT_AND_TRACE_SURFACE_SCHEMA_HELPERS_IMPLEMENTATION_REVIEW_V1.md`
- `weslr/arc_candidate_output_trace_surface.py`
- `weslr/tests/test_arc_candidate_output_trace_surface_v1.py`

Out of scope and unchanged:
- replay preservation
- live replay scoring wiring
- generator deservedness
- assembler deservedness
- full V5 replay
- emitter/runtime/final-answer behavior

## 3. Comparability structural validation review
Confirmed `derive_candidate_output_comparability(...)` can set `comparable_to_expected=true` only when:
- candidate output is present
- expected output available flag is true
- `serialization_status == "json_safe"`
- `output_type == "grid_int_matrix"`
- `normalized_output` passes strict structural validation as a non-empty rectangular nested integer grid
- booleans are rejected through the shared grid validator

Confirmed malformed JSON-safe structures fail closed without ordinary derivation crashes:
- dict → `comparable_to_expected=false`, `incomparable_reason_code="normalization_failed"`
- string → `comparable_to_expected=false`, `incomparable_reason_code="normalization_failed"`
- number → `comparable_to_expected=false`, `incomparable_reason_code="normalization_failed"`
- ragged list → `comparable_to_expected=false`, `incomparable_reason_code="normalization_failed"`
- non-integer cells → `comparable_to_expected=false`, `incomparable_reason_code="normalization_failed"`
- bool cells → `comparable_to_expected=false`, `incomparable_reason_code="normalization_failed"`
- empty list → `comparable_to_expected=false`, `incomparable_reason_code="normalization_failed"`

Confirmed valid rectangular nested integer grids still become comparable with:
- `comparable_to_expected=true`
- `incomparable_reason_code="none"`

Conclusion:
- the narrow defect identified in the prior helper review is repaired

## 4. Normalization/validation consistency review
Confirmed:
- `normalize_grid_int_matrix(...)` behavior was not weakened
- comparability validation reuses the same strict normalization logic through `_validate_comparable_grid_int_matrix(...)`
- normalization and comparability now share one structural contract instead of drifting
- valid rectangular nested integer grid comparability is preserved

Conclusion:
- normalization/validation consistency is valid for this helper contract

## 5. Boundary preservation review
Confirmed:
- no expected-answer values are read in comparability derivation
- no RNG/hash/random logic was introduced
- no replay runtime wiring was introduced
- no replay preservation was added
- no generator output emission was added
- no assembler logic was changed
- forbidden scoring-field detection remains recursive
- core trace, composed trace, and MDL trace helpers were not regressed or modified in this lane

Conclusion:
- helper boundary preservation is valid

## 6. Test adequacy review
Confirmed tests now cover:
- malformed JSON-safe dict blocked
- malformed JSON-safe string blocked
- malformed JSON-safe number blocked
- ragged list blocked
- non-integer cells blocked
- bool cells blocked
- empty list blocked
- valid rectangular integer grid preserved
- expected output unavailable still returns `expected_output_missing`
- descriptor-only output remains not comparable
- non-JSON-safe output remains not comparable
- helper does not mutate input payloads
- no RNG/hash/random logic
- no replay runtime wiring import/call

Also preserved:
- recursive forbidden scoring-field detection coverage
- core trace/composed trace/MDL trace JSON-safe shape coverage

Conclusion:
- test adequacy is valid for the repaired narrow contract

## 7. Safety boundary review
Confirmed:
- narrow helper repair only
- no live replay scoring wiring
- no replay preservation
- no generator deservedness change
- no assembler deservedness change
- no full V5 replay
- no runtime/emitter/final-answer behavior
- no `.weslr`
- no external calls
- protected files unchanged

## 8. Recommended next safe local follow-up
`IMPLEMENT_ARC_CANDIDATE_OUTPUT_AND_TRACE_SURFACE_REPLAY_PRESERVATION_V1`

Reason:
- the comparability gate now fail-closes correctly
- malformed JSON-safe candidate output shapes are blocked
- the helper contract is now suitable for the next local replay-preservation lane
