# WESLR ARC CANDIDATE OUTPUT AND TRACE SURFACE REPLAY PRESERVATION V1

## 1. Executive verdict
`arc_candidate_output_trace_surface_replay_preservation_implemented`

## 2. Scope
Implemented a narrow local helper lane for replay preservation of candidate output and trace surface data only.

Implemented files:
- `weslr/arc_candidate_output_trace_surface.py`
- `weslr/tests/test_arc_candidate_output_trace_surface_v1.py`
- `weslr/tests/release_gate_v1.py`

Out of scope and not added:
- live replay scoring
- expected-answer comparison
- runtime execution
- emitter/final-answer behavior
- generator deservedness changes
- assembler deservedness changes
- provider/model calls
- retrieval/tool execution
- `.weslr` IO
- persistence/export/public behavior

## 3. Replay-preservation helpers added
Added helper-only preservation functions:
- `strip_forbidden_upstream_scoring_fields(...)`
- `preserve_candidate_output_surface_for_replay(...)`
- `preserve_candidate_trace_surface_for_replay(...)`
- `preserve_composed_trace_surface_for_replay(...)`
- `preserve_mdl_trace_surface_for_replay(...)`
- `build_replay_preserved_surface_bundle(...)`

Added explicit allowed-key inventories for preserved packet shapes:
- `CANDIDATE_OUTPUT_SURFACE_KEYS`
- `CANDIDATE_TRACE_SURFACE_KEYS`
- `COMPOSED_TRACE_SURFACE_KEYS`
- `MDL_TRACE_SURFACE_KEYS`

## 4. Preservation behavior
Candidate output replay preservation now:
- strips forbidden upstream scoring/expected fields recursively
- rebuilds the candidate output surface from allowed schema fields only
- re-runs the repaired comparability gate instead of trusting inbound `comparable_to_expected`
- preserves valid rectangular nested integer grids without scoring
- fail-closes malformed JSON-safe normalized outputs to non-comparable
- preserves descriptor-only and non-JSON-safe outputs as non-comparable
- preserves expected-output-unavailable state as non-comparable

Trace replay preservation now:
- rebuilds core trace packets from allowed fields only
- rebuilds composed trace packets from allowed fields only
- rebuilds MDL trace packets from allowed fields only
- strips forbidden scoring/expected fields recursively from nested payloads before preservation

Replay provenance packet added:
- `candidate_output_surface_source: candidate_output_surface`
- `expected_output_load_stage: not_loaded_for_replay_preservation`
- `expected_output_loaded_after_ledger_decision: false`

This lane does not score, compare, or load expected-answer values.

## 5. Boundary preservation
Confirmed preserved:
- no live replay scoring wiring
- no expected-answer value loading
- no expected-answer copying into preserved bundle
- no generator output emission wiring
- no assembler logic changes
- no runtime/emitter/final-answer/chat behavior
- no provider/model/tool/retrieval calls
- no `.weslr`
- no external calls
- no protected runtime/chat file changes

## 6. Tests added/updated
Expanded focused test coverage to prove:
- replay preservation records only allowed candidate-output/trace-surface metadata
- comparable valid grids are preserved without scoring
- malformed JSON-safe structures are not preserved as comparable replay outputs
- bool cells remain rejected
- expected-answer values are not copied into preserved replay packets
- no live replay scoring wiring exists
- no runtime/emitter/final-answer/chat behavior is introduced
- no provider/model/tool/retrieval calls are introduced
- input payloads are not mutated
- recursive forbidden-field stripping remains intact

## 7. Validation summary
Validated with:
- `python3 -m py_compile weslr/arc_candidate_output_trace_surface.py`
- `python3 -m pytest weslr/tests/test_arc_candidate_output_trace_surface_v1.py`
- `python3 weslr/tests/release_gate_v1.py`
- `git diff --check`
- `bash scripts/weslr_release_check.sh`
- `bash scripts/chat_weslr_de_health_check.sh --mode source-repo`

## 8. Recommended next safe local follow-up
`REVIEW_ARC_CANDIDATE_OUTPUT_AND_TRACE_SURFACE_REPLAY_PRESERVATION_V1`

Reason:
- helper-only replay preservation is now implemented
- the contract should be reviewed before any downstream replay scoring lane consumes it
