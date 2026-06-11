# WESLR Reverse Calibration Trace V1

## 1. Purpose
A reverse calibration trace is an internal, metadata-only structure that starts from a known outcome and maps backward to earlier signal phases, expected next steps, and the reason each step is preferred over calibration, archive, or claim.

## 2. Safe use
Reverse calibration may use known historical, scientific, or project outcomes to calibrate internal next-step selection.
It must not claim discovery, proof, intelligence, public science authority, or future predictive certainty.

## 3. Trace fields
A reverse calibration trace uses these fields:
- `trace_id`
- `source_case_id`
- `known_outcome_summary`
- `known_outcome_authority_status`
- `phase_id`
- `phase_signal_summary`
- `expected_forward_next_step`
- `why_this_step`
- `why_not_calibrate`
- `why_not_archive`
- `why_not_claim`
- `disconfirming_signal`
- `required_next_evidence`
- `selector_bridge_comparison`
- `mismatch_if_any`
- `calibration_lesson`
- `forbidden_interpretations`
- `authority_status`
- `safe_metadata`

## 4. Allowed next-step labels
Allowed labels:
- `probe`
- `pressure_test`
- `calibrate`
- `archive`
- `operator_review`
- `blocked_by_safety`
- `watch`
- `not_applicable`
- `needs_repair`

## 5. Canonical pulsar reverse trace
Known outcome:
- pulsars were eventually identified as real astronomical objects

Reverse phases:
- `initial_strange_signal`
  - expected next step: `probe`
  - why not calibrate: signal needs structured observation, not system self-adjustment
  - why not claim: no confirmation yet
- `repeated_precise_signal`
  - expected next step: `pressure_test`
  - why not calibrate: repetition strengthens signal enough to test alternatives
  - why not claim: ordinary explanations still possible
- `ordinary_explanations_weakened`
  - expected next step: `calibrate`
  - why calibrate now: competing explanations and confidence posture need adjustment
  - why not claim: still needs external confirmation
- `external_confirmation`
  - expected next step: `archive` or `operator_review` depending on system policy
  - why not claim automatically: public authority still requires human/external review
- `unsafe_public_claim_attempt`
  - expected next step: `blocked_by_safety`
  - why: live unauthorized claim remains blocked

## 6. Why reverse calibration helps the old failure
Old failure:
- `calibrate: 8`

Reverse calibration improvement:
- teaches why some phases deserve `probe`
- teaches why some deserve `pressure_test`
- teaches why only true posture/confidence issues deserve `calibrate`
- teaches why weak cases may be `watch` or `archive`
- teaches why unsafe public claims must be blocked

## 7. Relationship to the comparative artifact
The comparative artifact proved differentiation exists at the bridge layer.
Reverse calibration explains why each differentiated next step is justified by known-outcome backtracking.

## 8. Relationship to future ingestion
Before real source ingestion, WESLR needs reverse traces so it can map real signals to justified next steps instead of collapsing into calibration or overclaiming.

## 9. Safety boundaries
Forbidden in this design:
- runtime
- source ingestion
- provider/tool/web calls
- `.weslr` IO
- persistence
- memory/project mutation
- public claims
- final-answer authority
- benchmark/score/proof/AGI/public-science claims
- automatic discovery claims

## 10. Future validation requirements
A future helper must fail closed on:
- missing trace id
- missing known outcome
- missing phase id
- invalid next-step label
- missing why-this-step
- missing why-not-claim
- unsafe authority flags
- public claim authorization
- final-answer authority
- provider/model/tool/retrieval/web implication
- `.weslr` implication
- `.weslr` read/write implication
- `.weslr` persistence/state implication
- hidden/private/protected markers
- non-JSON-safe output

## 11. Design outcome
The best outcome is a reverse-trace layer that is strict on authority and permissive on safe internal reasoning signals.
