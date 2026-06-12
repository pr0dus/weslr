# WESLR Real Findings Evidence Intake V1

## 1. Purpose
This design defines how WESLR may later record a real-world/source evidence signal in a safe, metadata-only evidence-intake packet before any proposed-direction packet is considered.

A real findings evidence intake packet is an internal candidate metadata record only.
It is not:
- source ingestion implementation
- live retrieval
- web search
- provider/tool call
- proof
- discovery
- public claim
- final answer
- runtime authority
- persistence authorization

## 2. Packet fields
A real findings evidence intake packet should include:
- `evidence_intake_id`
- `source_scope`
- `source_kind`
- `source_reference_summary`
- `source_access_status`
- `raw_content_retained`
- `evidence_signal_summary`
- `observed_pattern`
- `known_limitations`
- `missing_context`
- `confidence_posture`
- `calibration_axes_to_apply`
- `reverse_trace_reference`
- `proposed_direction_eligibility`
- `disconfirming_signal`
- `operator_review_need`
- `privacy_sensitivity`
- `safety_sensitivity`
- `promotion_blockers`
- `forbidden_interpretations`
- `authority_status`
- `safe_metadata`

The packet must remain metadata-only and JSON-safe.

## 3. Allowed source kinds
Allowed source kinds:
- `public_open_source`
- `owner_supplied_document`
- `owner_supplied_observation`
- `synthetic_example`
- `known_science_replay`
- `internal_project_artifact`
- `blocked_private_source`
- `unknown_source`

These are source classification labels, not authorization.

## 4. Allowed access statuses
Allowed access statuses:
- `not_accessed`
- `metadata_only`
- `owner_supplied_summary`
- `future_access_requires_review`
- `blocked`
- `needs_repair`

These describe access posture, not source permission by themselves.

## 5. Allowed confidence postures
Allowed confidence postures:
- `unassessed`
- `weak_signal`
- `moderate_signal`
- `strong_signal_requires_pressure_test`
- `conflicting_signal`
- `insufficient_context`
- `blocked_by_safety`

These describe evidence posture only.

## 6. Proposed-direction eligibility
Allowed proposed-direction eligibility values:
- `not_eligible`
- `eligible_for_candidate_direction`
- `eligible_after_probe`
- `eligible_after_pressure_test`
- `operator_review_required`
- `blocked_by_safety`
- `needs_repair`

Eligibility is a separate metadata result, not an authorization.

## 7. Intake flow
A real evidence signal must pass through:
1. source scope check
2. privacy/safety sensitivity check
3. raw-content-retention check
4. confidence posture check
5. disconfirming signal requirement
6. calibration axes selection
7. operator review need check
8. proposed-direction eligibility check

This design records the checks; it does not perform real ingestion.

## 8. Relationship to calibrated proposed directions
Evidence intake does not create proposed directions directly.
It only determines whether a future proposed-direction packet may be built.
The proposed-direction layer remains separate and downstream.

## 9. No-raw-retention rule
By default, raw source content must not be retained.
Only summaries/metadata are allowed unless a future source-scope/read-authorization design explicitly permits retention.

## 10. Safety boundaries
Forbidden in this design:
- runtime wiring
- actual source ingestion
- provider/model/tool/retrieval/web calls
- `.weslr` IO
- persistence/database writes
- memory/project mutation
- public claim authority
- final-answer authority
- benchmark/proof/AGI/public-science/discovery claims
- hidden/private/protected data intake
- cross-user leakage

## 11. Authority status
The packet must explicitly encode a fail-closed authority posture.
Expected authority status keys include:
- runtime authorization: false
- source ingestion authorization: false
- public claim authorization: false
- final-answer authority: false
- provider/model/tool/retrieval/web implication: false
- `.weslr` implication: false
- persistence/database implication: false
- memory/project mutation implication: false
- hidden/private/protected marker implication: false
- automatic discovery authority: false

## 12. Future validation requirements
A future helper must fail closed on:
- missing evidence intake id
- missing source scope
- missing source kind
- invalid source kind
- invalid access status
- raw content retained true without explicit authorization
- missing evidence signal summary
- missing known limitations
- missing missing-context field
- invalid confidence posture
- missing disconfirming signal
- missing calibration axes
- invalid proposed-direction eligibility
- unsafe authority flags
- public claim authorization
- final-answer authority
- provider/model/tool/retrieval/web implication
- source ingestion authorization
- runtime authorization
- `.weslr` implication
- `.weslr` read/write implication
- `.weslr` persistence/state implication
- persistence/database implication
- memory/project mutation implication
- hidden/private/protected markers
- non-JSON-safe output

## 13. Evidence posture
Supporting evidence should be summarized, not inflated.
Missing context and disconfirming signals must remain visible.
No field should be interpreted as proof of correctness.

## 14. Relationship to the calibration chain
This intake layer is the upstream metadata gate for later candidate-direction work.
It sits before calibrated proposed directions and can supply only bounded evidence posture, not proposal authority.

## 15. Final design statement
WESLR real findings evidence intake is a metadata-only, fail-closed evidence posture layer: useful for later candidate-direction decisions, but never for raw ingestion, public truth, discovery, proof, or final authority.
