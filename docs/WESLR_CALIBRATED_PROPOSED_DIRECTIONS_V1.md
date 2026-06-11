# WESLR Calibrated Proposed Directions V1

## 1. Purpose
This design defines how WESLR may form internal proposed directions after calibration without claiming findings, discovery, proof, public truth, final-answer authority, or ingestion authorization.

A calibrated proposed direction is an internal, metadata-only candidate next research/work direction produced after passing through:
- differentiated next-step selection
- reverse calibration trace
- theoretical calibration axes
- capability suppression boundary

It is an internal candidate only, not a finding, discovery, proof, public claim, final answer, or authority-bearing result.

## 2. Proposed direction packet fields
A calibrated proposed direction packet should include:
- `direction_id`
- `source_signal_summary`
- `source_scope`
- `proposed_direction_summary`
- `why_this_direction`
- `calibration_axes_used`
- `reverse_trace_reference`
- `expected_next_step`
- `supporting_evidence_summary`
- `missing_evidence`
- `disconfirming_signal`
- `risk_of_overclaim`
- `risk_of_underexploration`
- `operator_review_need`
- `promotion_blockers`
- `forbidden_interpretations`
- `authority_status`
- `safe_metadata`

The packet is metadata-only and must remain JSON-safe.

## 3. Allowed direction statuses
Allowed statuses:
- `candidate_direction`
- `needs_probe`
- `needs_pressure_test`
- `needs_calibration`
- `needs_evidence`
- `watch`
- `archive`
- `operator_review_required`
- `blocked_by_safety`
- `needs_repair`

These are internal direction statuses, not public labels or truth claims.

## 4. Distinction from findings and claims
A calibrated proposed direction is only an internal candidate.
It is not:
- a finding
- a discovery
- a proof
- a public claim
- a final answer
- an authority-bearing result

Those are not authorized by this design.

## 5. How prior artifacts feed the direction
This design uses prior artifacts as internal calibration context:
- the comparative artifact proves WESLR can differentiate steps
- the reverse trace explains why a step is justified
- the theoretical axes explain which failure mode is being calibrated
- the capability suppression audit prevents safety from suppressing safe cognition

## 6. Pre-ingestion boundary
This design may define the direction packet shape.
It does not authorize real source ingestion.

Future ingestion must be separately designed and reviewed.

## 7. Safety boundaries
Forbidden in this design:
- runtime wiring
- source ingestion
- provider/model/tool/web/retrieval calls
- `.weslr` IO
- persistence
- memory/project mutation
- public claims
- final-answer authority
- benchmark/score/proof/AGI/public-science claims
- automatic discovery claims

## 8. Authority status
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

## 9. Expected internal use
The packet may be used to:
- compare candidate directions
- preserve the reason a direction was proposed
- show what evidence is missing
- show what would falsify or weaken the direction
- decide whether the next step is probe, pressure test, calibration, watch, archive, or operator review

It may not be used to claim truth or completion.

## 10. Promotion blockers
Promotion blockers should capture what prevents a direction from being upgraded, including:
- missing evidence
- disconfirming signals
- weak source scope
- unresolved safety risk
- unsafe authority pressure
- overclaim risk
- underexploration risk
- operator review need

## 11. Forbidden interpretations
The packet must explicitly refuse these interpretations:
- “this is proven”
- “this is discovered”
- “this is public truth”
- “this is a final answer”
- “this authorizes ingestion”
- “this authorizes runtime”
- “this authorizes provider/tool/web use”
- “this authorizes `.weslr` access”

## 12. Relationship to the calibration stack
This design sits after:
- differentiated next-step selection
- reverse calibration
- theoretical calibration axes
- capability suppression audit

It is a downstream candidate-direction layer, not a replacement for those layers.

## 13. Future validation requirements
A future helper must fail closed on:
- missing direction id
- missing source signal summary
- missing proposed direction summary
- missing calibration axes
- missing expected next step
- invalid direction status
- missing disconfirming signal
- missing forbidden interpretations
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

## 14. Non-goals
- not a runtime system
- not a source ingestion system
- not a search system
- not a scoring system
- not a proof system
- not a discovery system
- not a public claim system
- not a final-answer system
- not an authority escalator

## 15. Design outcome
The best outcome is a direction packet that is useful for internal calibration and proposed next-step planning while staying strictly internal, metadata-only, and fail-closed.

## 16. Recommended downstream behavior
When valid, a future helper may classify a packet into one of the allowed statuses and surface the next step as an internal candidate.
When unsafe, it must block or return needs_repair/operator_review_required.

## 17. Evidence posture
Supporting evidence should be summarized, not inflated.
Missing evidence and disconfirming signals must remain visible.
No field should be interpreted as a proof of correctness.

## 18. Final design statement
WESLR calibrated proposed directions are internal candidate directions only: useful for guidance, calibration, and operator review, but never for public truth, discovery, proof, or final authority.
