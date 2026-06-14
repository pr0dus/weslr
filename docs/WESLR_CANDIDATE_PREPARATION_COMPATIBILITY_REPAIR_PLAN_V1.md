# WESLR Candidate Preparation Compatibility Repair Plan V1

## 1. Purpose
Plan the next coding lane to repair candidate-preparation compatibility after the scout, registry, and ontology-expansion route work broadened the upstream metadata chain.

## 2. Current failure summary
The optional neighboring suite `weslr/tests/test_cross_domain_scout_to_mlcf_candidate_preparation_v1.py -q` currently fails because the candidate-preparation path still expects a narrower scout/integration shape than the now-expanded upstream chain provides.

Observed failure labels:
- `invalid_source_scout_packet`
- `invalid_signal_type`
- `unsafe_claim_language_present`

Observed current raw upstream scout/integration shape:
- source scout root `signal_type`: `None`
- source scout validator: `blocked = True`, `blocked_labels = ['invalid_signal_type']`
- integration validator: `blocked = True`, `blocked_labels = ['invalid_source_scout_packet', 'invalid_signal_type', 'unsafe_claim_language_present']`
- selected route on the integration packet: `scout_blocked_by_safety`
- next safe step on the integration packet: `blocked_by_safety`

Exact fields implicated in the current failure chain:
- `source_scout_packet.signal_type` → `None`, causing `invalid_signal_type`
- `route_decisions[0].blocked_authorities` → contains claim-bearing labels such as `discovery_claim_authority` and `proof_claim_authority`
- `metadata_locator_route_payload_preview.blocked_source_content_fields` → contains claim-bearing phrases such as `trusted evidence` and `accepted evidence`

This is currently an upstream compatibility issue, not a candidate-preparation implementation repair in this lane.

## 3. Source artifacts reviewed
- `weslr/cross_domain_scout_to_mlcf_candidate_preparation.py`
- `weslr/tests/test_cross_domain_scout_to_mlcf_candidate_preparation_v1.py`
- `weslr/cross_domain_scout_to_mlcf_integration.py`
- `weslr/cross_domain_open_problem_discovery_scout.py`
- `weslr/unfinished_research_discovery_constants.py`
- `weslr/unfinished_research_discovery_registry.py`
- `weslr/ontology_expansion_request_builder.py`
- `weslr/mlcf_routing_from_live_searxng_metadata_result.py`

## 4. Failure inventory
### Failing suite
- `weslr/tests/test_cross_domain_scout_to_mlcf_candidate_preparation_v1.py -q`

### Representative failures
- `_integration_packet()` asserts integration validity, but the integration packet is blocked.
- `test_valid_integration_packet_builds_ready_for_operator_review_packet`
- `test_source_selection_plan_needed_route_builds_correct_status`
- `test_wrong_route_becomes_excluded_packet`
- `test_no_bridge_refs_produce_needs_repair_status`
- `test_unsafe_claim_source_content_marker_blocks`
- `test_json_safe_conversion_works`
- `test_summary_is_safe_and_does_not_include_claims`
- Multiple denied-authority and raw-content rejection cases depend on `_integration_packet()` and therefore fail early.

### Exact current blocking chain
- `invalid_signal_type` originates from the upstream scout packet’s missing root `signal_type` (`None`).
- `invalid_source_scout_packet` is a downstream integration validation result because the scout packet is already blocked.
- `unsafe_claim_language_present` is triggered by claim-bearing labels/text embedded in the blocked route metadata:
  - `discovery_claim_authority`
  - `proof_claim_authority`
  - `trusted evidence`
  - `accepted evidence`

## 5. Candidate-preparation compatibility boundary
After repair, candidate-preparation should accept only narrow, safe, metadata-only inputs:
- normal candidate routes with disconfirmation-first metadata
- safe metadata candidate routes
- packets with denied authorities all false
- packets with no raw source, no HTML, no snippets, no PDF text, no final-answer text
- packets with no unsafe claim language in candidate-facing summaries
- packets with required disconfirmation fields intact

It should remain narrow and should not become a general post-integration promotion surface.

## 6. Non-goals
Candidate-preparation must continue to reject:
- ontology-insufficient signals
- extraordinary/fringe signals without explicit confirmation
- unsafe claim language
- final-answer text
- proof / public-science / discovery-as-truth claims
- accepted evidence
- accepted candidate
- proposal action authority
- source-ingestion authority
- provider/runtime authority
- raw source / snippet / HTML / PDF content

## 7. Ontology-insufficient handling plan
Candidate-preparation should continue to treat ontology-insufficient inputs as not eligible for candidate-prep.

Planned blocked labels for that path:
- `ontology_expansion_request_not_candidate_preparation_eligible`
- `operator_review_required`
- `sufficient_power_false`

Ontology-expansion request packets should remain upstream review / expansion artifacts, not candidate-prep artifacts.

## 8. Expanded signal compatibility plan
The compatibility repair should not make all registry signals candidate-eligible.

Likely candidate-prep-eligible after disconfirmation checks:
- normal candidate signals
- unfinished-work signals
- dormant-direction signals
- cross-domain transfer signals
- technology-blocked signals
- measurement / benchmark-gap signals

Review-only or not candidate-prep:
- ontology-insufficient
- extraordinary/fringe without explicit confirmation
- future-workforce / job-transformation
- language / protocol
- artifact proposal
- disconfirmation-required alone

Blocked / operator-token-gated:
- extraordinary/fringe
- future-workforce / job-transformation
- language / protocol

## 9. Source-scout packet normalization plan
Plan to normalize the expanded scout packet into the candidate-preparation expected shape without weakening validation:
- preserve source ids / locator ids
- preserve domain families and signal families
- preserve evidence roles
- preserve source classes
- preserve disconfirmation fields
- preserve safe metadata summary
- preserve denied authority flags
- preserve blocked labels

Normalization should be narrow, deterministic, and metadata-only.

## 10. Unsafe-claim language repair plan
Keep forbidden wording checks strict, but avoid false positives from safe metadata labels or documentation text.

Do not remove forbidden-word checks.
Do not weaken public-claim safety.
Use field-aware scanning if needed:
- candidate-facing summaries
- free-text narrative fields
- route preview text
- avoid treating enum labels as claims unless the label itself is a dangerous assertion

## 11. Test plan
Next coding lane should add or repair tests for:
- the current failing raw upstream scout example
- ontology-insufficient rejection
- extraordinary/fringe rejection unless token confirmed
- future-workforce review-only posture
- language/protocol review-only posture
- artifact-proposal review-only posture
- safe normal candidate signal accepted only with disconfirmation fields
- unsafe claim language rejected
- raw content rejected
- denied-authority true rejected
- candidate-prep route not broadened
- JSON-safe deterministic output
- metadata-only summary

## 12. Risk assessment
Key risks:
- over-broadening candidate-prep eligibility
- weakening unsafe-claim filters
- accidentally treating ontology-expansion requests as candidate-ready
- accepting future-work / language / fringe inputs too early
- breaking existing tests
- protected-file contamination

## 13. Protected-file requirements
Do not modify:
- `weslr/chat_responder.py`
- `main.py`
- `dialogue.py`
- `chat_ui.py`
- `weslr/main.py` if present

## 14. Validation plan
For the next coding lane:
- `python3 -m pytest weslr/tests/test_cross_domain_scout_to_mlcf_candidate_preparation_v1.py -q`
- `python3 -m py_compile` on the touched helper/test files
- `git diff --check`
- `python3 weslr/tests/release_gate_v1.py`
- `bash scripts/weslr_release_check.sh`

## 15. Recommended implementation lane
`IMPLEMENT_WESLR_CANDIDATE_PREPARATION_COMPATIBILITY_REPAIR_V1`

## 16. Final judgment
This planning lane is valid and ready for implementation planning handoff.
