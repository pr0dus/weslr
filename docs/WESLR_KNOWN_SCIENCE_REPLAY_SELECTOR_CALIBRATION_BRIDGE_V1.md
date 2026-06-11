# WESLR Known-Science Replay Selector Calibration Bridge V1

## 1. Purpose
This bridge compares:
- known-science replay expected internal next-step progression
against
- scenario-sensitive next-step selector outputs

It exists only to produce calibration metadata.

It is not:
- runtime execution
- selector replacement
- selector promotion
- a score
- a benchmark
- proof of scientific reasoning
- proof of intelligence
- proof of AGI
- public science output
- final-answer authority

## 2. Bridge role
The bridge is a metadata comparison layer between:
- Known-Science Replay Helpers V1
- Scenario-Sensitive Next-Step Selector V1
- Human-Readable Findings Digest V1
- Forecast Calibration Bridge V1

It should help answer:
- Did the selector choose the expected internal next step?
- If not, was the difference safe, useful, or concerning?
- Is the mismatch due to metadata quality, safety pressure, or simple case/step misalignment?

## 3. Bridge input fields
A future bridge packet should carry only safe metadata fields such as:
- `bridge_id`
- `source_replay_case_id`
- `source_known_outcome`
- `source_case_domain`
- `replay_phase_id`
- `replay_phase_summary`
- `expected_internal_next_step`
- `selector_input_metadata`
- `selector_selected_next_step`
- `selector_selection_reason`
- `alignment_status`
- `alignment_notes`
- `mismatch_type`
- `calibration_observation`
- `recommended_followup`
- `forbidden_interpretations`
- `authority_status`
- `safe_metadata`

## 4. Alignment status model
Allowed alignment statuses:
- `aligned`
- `partially_aligned`
- `mismatch`
- `blocked_by_safety`
- `not_applicable`
- `needs_repair`

### Suggested meaning
- `aligned`: selector choice matches the expected replay step.
- `partially_aligned`: directionally sensible but not exact.
- `mismatch`: selector chose a different safe step than expected.
- `blocked_by_safety`: selector correctly refused unsafe pressure.
- `not_applicable`: no meaningful comparison exists for this phase.
- `needs_repair`: the metadata is invalid or incomplete.

## 5. Mismatch type model
Allowed mismatch types:
- `none`
- `over_cautious`
- `under_cautious`
- `premature_calibration`
- `premature_archive`
- `missed_pressure_test`
- `missed_probe`
- `unsafe_public_claim_pressure`
- `invalid_metadata`
- `unknown_case`

### Suggested meaning
- `none`: no mismatch.
- `over_cautious`: selector delayed progress too much.
- `under_cautious`: selector moved too quickly.
- `premature_calibration`: selector calibrated before the signal warranted it.
- `premature_archive`: selector archived too early.
- `missed_pressure_test`: selector failed to challenge ordinary explanations.
- `missed_probe`: selector failed to open with a cautious probe.
- `unsafe_public_claim_pressure`: selector failed to block unsafe public-claim pressure.
- `invalid_metadata`: input packet was malformed or incomplete.
- `unknown_case`: the case/phase family was not recognized.

## 6. Calibration observations
Bridge observations should be phrased as metadata-only findings such as:
- selector correctly chose `probe` for ambiguous interesting signal
- selector correctly chose `pressure_test` when ordinary explanations must be challenged
- selector correctly chose `calibrate` only after repeatability / measurement refinement mattered
- selector overused `calibrate`
- selector archived too early
- selector failed to block unsafe public claim pressure
- selector returned `needs_repair` for invalid metadata

## 7. Canonical bridge example
### `pulsar_discovery_selector_calibration_bridge`

This canonical bridge should compare the pulsar replay phases against selector outputs.

#### Phases
- `initial_strange_signal`
  - expected: `probe`
- `repeated_precise_signal`
  - expected: `pressure_test`
- `ordinary_explanations_weakened`
  - expected: `calibrate`
- `unsafe_public_claim_attempt`
  - expected: `operator_review` or `blocked`

#### What to observe
- whether the selector stays cautious at the first ambiguity
- whether it pressure-tests ordinary explanations before exotic ones
- whether it calibrates only once repeatability matters
- whether it blocks unsafe public-claim pressure

#### Safe bridge interpretation
- Good alignment is evidence of selector sensitivity, not scientific discovery.
- A mismatch is useful only as calibration feedback.
- The bridge must not infer public authority from a good result.

## 8. Optional future bridge cases
### `continental_drift_selector_calibration_bridge`
- Why it matters: tests gradual-evidence reasoning and resistance to early dismissal.
- Likely expected tensions: `probe` vs `pressure_test`, then `calibrate` as evidence accumulates.
- Useful mismatch to detect: premature archive or over-cautious stagnation.

### `penicillin_contamination_selector_calibration_bridge`
- Why it matters: tests anomaly recognition without romanticizing contamination.
- Likely expected tensions: `probe` vs `calibrate` after the anomaly becomes informative.
- Useful mismatch to detect: dismissing useful anomalies as noise too quickly.

### `cosmic_microwave_background_selector_calibration_bridge`
- Why it matters: tests persistent-background interpretation and careful external comparison.
- Likely expected tensions: `probe`, `pressure_test`, and later `archive` once the signal is understood.
- Useful mismatch to detect: premature cosmology language or premature archive.

### `helicobacter_pylori_selector_calibration_bridge`
- Why it matters: tests conflict between established explanation and later-supported hypothesis.
- Likely expected tensions: `pressure_test` against the old explanation, then `calibrate` as repeat evidence accumulates.
- Useful mismatch to detect: missed pressure-testing or overconfident early resolution.

## 9. Component relationship summary
The bridge should consume metadata from:
- Known-Science Replay Helpers V1
- Scenario-Sensitive Next-Step Selector V1
- Human-Readable Findings Digest V1
- Forecast Calibration Bridge V1

The bridge must not:
- run the recursive research executor
- execute the selector in runtime
- update Suggestion Store
- promote behavior packs
- change answer formation
- modify ChatResponder
- generate public output
- call providers/models/tools/retrieval/web
- read/write `.weslr`
- persist to databases
- mutate memory/project state

## 10. Safety boundaries
Forbidden in this design:
- runtime wiring
- selector execution as runtime behavior
- public claim generation
- benchmark/score/certification language
- discovery/proof/breakthrough/AGI/sentience/consciousness claims
- final-answer authority
- hidden/private/protected data use
- memory/project mutation
- behavior-pack promotion
- `.weslr` IO
- persistence/database writes
- protected-file edits

## 11. Future implementation validation requirements
A future bridge helper must fail closed on:
- missing bridge id
- missing replay case id
- missing expected next step
- missing selector-selected next step
- invalid alignment status
- invalid mismatch type
- missing forbidden interpretations
- missing authority status
- missing safe metadata
- public claim authorization
- runtime action authorization
- storage write authorization
- memory mutation authorization
- project mutation authorization
- behavior promotion authorization
- final-answer authority
- provider/model/tool/retrieval implication
- `.weslr` implication
- hidden/private/protected data markers
- forbidden discovery/proof/breakthrough/AGI/sentience/consciousness claim language
- non-JSON-safe output

## 12. Non-goals
- not a benchmark
- not a score
- not proof of scientific reasoning
- not proof of intelligence
- not proof of AGI
- not a discovery engine
- not runtime integration
- not selector replacement
- not automatic self-improvement
- not behavior-pack promotion

## 13. Status
Design-only bridge specification for later review.
