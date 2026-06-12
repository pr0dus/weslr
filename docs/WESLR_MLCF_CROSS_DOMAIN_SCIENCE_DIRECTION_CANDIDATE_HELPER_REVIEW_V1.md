# WESLR MLCF Cross-Domain Science Direction Candidate Helper V1 — Review

## Implementation summary
The helper is a deterministic, metadata-only cross-domain direction builder. It turns multiple owner-supplied domain summaries into a bounded candidate method packet, with a shared structure map, bridge summary, calibration axes, pressure-test prompts, probe suggestions, and fail-closed safety metadata.

It closes the gap from the prior sample: it does more than route a signal; it synthesizes a candidate method description.

## API summary
Reviewed public APIs:
- `allowed_mlcf_cross_domain_candidate_types_v1()`
- `allowed_mlcf_cross_domain_relation_types_v1()`
- `allowed_mlcf_cross_domain_next_steps_v1()`
- `build_mlcf_cross_domain_science_direction_candidate_v1(...)`
- `validate_mlcf_cross_domain_science_direction_candidate_v1(...)`
- `summarize_mlcf_cross_domain_science_direction_candidate_v1(...)`
- `to_mlcf_cross_domain_science_direction_candidate_json_safe_v1(...)`
- `build_initial_mlcf_cross_domain_science_direction_candidate_examples_v1()`

## Canonical example assessment
Reviewed examples:
1. `rf_material_floorplan_sparse_change_map_candidate`
   - produces a rich candidate method summary
   - uses `cross_domain_method_candidate`
   - recommends `architecture_direction_ledger`
   - next safe step: `pressure_test`
2. `weak_analogy_blocked_candidate`
   - correctly blocks superficial mappings
   - routes to `failed_idea_ledger`
   - next safe step: `archive`
3. `cross_domain_probe_needed_candidate`
   - correctly recommends `probe`
   - routes to `idea_candidate_ledger`
   - preserves the gap between suggestion and proof

## RF/material/floor-plan candidate assessment
The RF/material/floor-plan example is the key success case.
It produces the intended candidate method summary:
- `Sparse RF spatial change map constrained by floor-plan topology and calibrated against material/surface scattering assumptions.`

This is materially richer than the prior generic routing result and remains a candidate direction only.

## Weak analogy blocked-candidate assessment
The weak analogy example correctly fails safe:
- relation type includes `weak_or_fake_analogy`
- candidate type is `blocked_cross_domain_candidate`
- summary stays skeptical
- next safe step is `archive`
- disconfirming signal explicitly says the analogy collapses under simplification

## Probe-needed candidate assessment
The probe-needed example correctly identifies insufficient evidence:
- candidate type is `cross_domain_probe_candidate`
- next safe step is `probe`
- includes probe design suggestions and missing evidence

## Calibration-axis assessment
The helper uses implemented calibration axes only.
For the RF/material/floor-plan candidate it includes:
- `topological_structure_preserving_calibration`
- `information_theory_compression_calibration`
- `signal_detection_calibration`
- `causal_counterfactual_calibration`
- `popper_falsification_calibration`

The probe variant adds `bayesian_calibration` appropriately.

## Authority / safety assessment
Reviewed fail-closed coverage includes:
- required candidate fields and domain count
- candidate type, relation type, next safe step, ledger id, calibration axis validation
- unsafe authority flags
- runtime / source ingestion / public claim / final-answer authority
- provider / model / tool / web / retrieval authority
- `.weslr` IO / read / write / persistence
- database writes
- memory / project mutation
- behavior-pack promotion authority
- public science / proof / discovery / AGI / benchmark claims
- cross-user leakage
- hidden/private/protected markers
- non-JSON-safe output handling

Assessment: metadata-only and bounded.

## Validation results
Passed:
- `python3 -m py_compile weslr/mlcf_cross_domain_science_direction_candidate.py weslr/tests/test_mlcf_cross_domain_science_direction_candidate_v1.py`
- `python3 -m pytest weslr/tests/test_mlcf_cross_domain_science_direction_candidate_v1.py` (`51 passed`)
- `git diff --check`
- `python3 weslr/tests/release_gate_v1.py`
- `bash scripts/weslr_release_check.sh`

## Protected-file status
Unchanged:
- `weslr/chat_responder.py`
- `weslr/main.py`
- `main.py`
- `dialogue.py`
- `chat_ui.py`

## Ready for first controlled sample run?
Yes.

## Recommended next lane
`RUN_WESLR_FIRST_MLCF_CROSS_DOMAIN_SCIENCE_DIRECTION_CANDIDATE_SAMPLE_V1`

## Review conclusion
The helper is valid, bounded, metadata-only, and ready for the first controlled cross-domain direction candidate sample run.
