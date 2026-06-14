# WESLR Ontology Expansion Protocol V1

## 1. Purpose
WESLR must detect when the current discovery ontology is not powerful enough for a domain, signal, theory, language, artifact, fringe-edge idea, or cross-domain pattern, and then stop short of weak classification, silent archival, overclaiming, auto-expansion, or self-modification.

When the ontology is insufficient, WESLR should mark the case as `ontology_insufficient_for_domain` and emit a governed ontology expansion request packet for operator review.

## 2. Owner intent
This protocol exists to preserve open-closed discovery:
- closed for production routing
- open for governed expansion requests
- never automatic
- never self-authorized
- never public-claim generating

The owner/operator decides whether to expand the ontology.

## 3. Relationship to discovery doctrine
This protocol extends the discovery doctrine, not the production routing surface.
It sits upstream of candidate-preparation and downstream of ontology insufficiency detection.

It does not replace disconfirmation-first rules, source-selection evidence plans, MLCF routing, cross-domain scout logic, or candidate-preparation eligibility.
It feeds them only when a later, separately authorized lane approves the expansion.

## 4. Open-closed architecture
The protocol is open-closed:
- closed production enums and validators remain closed at runtime
- governed expansion requests are open to review and future implementation lanes
- registry-only changes may be allowed where already supported
- code changes are required for new enums, routes, validators, and safety gates

## 5. Ontology-insufficient trigger
Trigger when WESLR cannot safely map a packet to an existing category and the ontology is not powerful enough.

Canonical trigger outputs:
- `ontology_insufficient_for_domain`
- `ontology_insufficient_signal`
- `safe_metadata_summary.sufficient_power: false`

Blocked alternatives:
- forcing a weak existing category
- silently archiving the locator
- overclaiming discovery
- auto-adding ontology entries
- auto-promoting to candidate/evidence/answer

## 6. Expansion request packet schema
The expansion request packet is JSON-safe and must include:
- `expansion_request_id`
- `source_locator_ids`
- `triggering_signal_summary`
- `why_current_ontology_failed`
- `current_signal_type_attempted`
- `current_route_attempted`
- `sufficient_power: false`
- `recommended_expansion_actions`
- `operator_review_required`
- `operator_confirmation_token_required`
- `rollback_plan`
- `blocked_authorities`
- `forbidden_claims`
- `safe_next_step`

Optional but recommended:
- `domain_family_hint`
- `confidence_notes`
- `disconfirming_evidence_map`
- `registry_delta_preview`
- `code_change_required`

## 7. Ten expansion recommendation types

### 7.1 `expansion_enlarge_signal_ontology`
Use when a real signal exists, but current signal families are too narrow.
Inputs: locator evidence, attempted signal type, domain hints.  
Outputs: new/expanded signal family proposal, validation notes, rollback notes.  
Workflow: operator reviews signal boundary first.  
Validation: no weak-category forcing, no candidate promotion.  
Rollback: restore prior signal enum and tests.  
Blocked claims: discovery proof, universal coverage.

### 7.2 `expansion_add_new_domain_family`
Use when the signal is valid but the domain family is missing.  
Inputs: domain hint, locator summary, routing trace.  
Outputs: domain family proposal and registry delta preview.  
Workflow: operator confirms domain fit.  
Validation: domain family must not imply new truth claims.  
Rollback: revert registry snapshot.  
Blocked claims: full domain mastery, product-readiness.

### 7.3 `expansion_add_new_source_class`
Use when source type is unrecognized but structurally relevant.  
Inputs: source descriptor, access pattern, source role hint.  
Outputs: source-class proposal and allow/deny impact.  
Workflow: review source trust posture.  
Validation: no source ingestion by default.  
Rollback: restore prior source-class set.  
Blocked claims: source endorsement, ingestion approval.

### 7.4 `expansion_add_new_evidence_role`
Use when evidence is real but current roles are insufficient.  
Inputs: evidence summary, disconfirmation posture, role gap.  
Outputs: evidence-role proposal and blocked-authority map.  
Workflow: operator reviews disconfirmation-first fit.  
Validation: no accepted evidence implied.  
Rollback: revert evidence-role enum.  
Blocked claims: accepted evidence, proof.

### 7.5 `expansion_add_new_disconfirmation_class`
Use when the current disconfirmation model cannot represent the failure mode.  
Inputs: failure description, risk notes, claim posture.  
Outputs: new disconfirmation class and test hooks.  
Workflow: operator reviews safety implications.  
Validation: disconfirmation-first remains mandatory.  
Rollback: remove class and restore validator expectations.  
Blocked claims: claim validation bypass.

### 7.6 `expansion_add_new_route`
Use when routing itself needs a new governed path.  
Inputs: route gap, packet trace, blocked path.  
Outputs: route proposal, eligibility rules, validator changes.  
Workflow: operator reviews route semantics.  
Validation: new route must not bypass candidate gating.  
Rollback: restore prior route enum and tests.  
Blocked claims: auto-acceptance, hidden bypass.

### 7.7 `expansion_add_new_artifact_type`
Use when the ontology needs a new artifact label.  
Inputs: artifact description, lifecycle stage, retention rules.  
Outputs: artifact type proposal and metadata contract.  
Workflow: operator reviews retention and privacy.  
Validation: artifact type cannot imply acceptance.  
Rollback: restore prior artifact enum.  
Blocked claims: evidence ownership, canonical authority.

### 7.8 `expansion_add_new_language_protocol_pattern`
Use for new language, teaching, protocol, translation, or concept-formation patterns.  
Inputs: language/protocol marker, domain translation hypothesis, concept-map candidate, learning-sequence candidate.  
Outputs: protocol-pattern proposal, teaching artifact candidate, blocked-claim list.  
Workflow: operator reviews for universality risk.  
Validation: no universal-language claim, no WESLR-generates-language claim.  
Rollback: revert pattern registry and tests.  
Blocked claims: universal language, linguistic supremacy.

### 7.9 `expansion_add_new_operator_review_category`
Use when a new operator confirmation token or review category is necessary.  
Inputs: missing review posture, safety rationale, confirmation semantics.  
Outputs: new token/category proposal and review UX notes.  
Workflow: operator explicitly confirms the new category.  
Validation: token must be exact-match and case-sensitive.  
Rollback: remove token and restore old confirmation rules.  
Blocked claims: implicit approval, silent operator consent.

### 7.10 `expansion_create_new_discovery_lens_design_lane`
Use when the whole discovery lens needs a new governed design lane.  
Inputs: cross-domain gap, chain summary, future implementation rationale.  
Outputs: new design lane proposal and implementation sequencing.  
Workflow: operator decides whether to open a lane.  
Validation: no auto-implementation, no public claim.  
Rollback: close lane proposal and restore previous design scope.  
Blocked claims: readiness, deployment, completion.

## 8. Registry-update vs code-change distinction

### Registry update allowed for
- domain families
- source-class keyword hints
- signal-family detection cues
- open-access/paywalled domain hints
- query templates
- artifact-type labels where already supported

### Code change required for
- new route enum
- new signal type enum
- new evidence role enum
- new disconfirming-evidence class enum
- new operator-review token
- new validator behavior
- new safety gate
- new candidate-preparation eligibility path

## 9. Operator workflow
The operator can:
- accept expansion request
- reject expansion request
- defer expansion request
- merge with existing domain family
- request stronger disconfirmation
- request second true run
- request new discovery-lens design lane

The operator cannot:
- auto-promote accepted evidence
- auto-promote accepted candidate
- bypass disconfirmation-first rules
- bypass extraordinary-claim quarantine
- bypass source-selection/evidence plan
- create public claims from expansion requests

Required operator confirmation tokens must be exact and case-sensitive.

## 10. Rollback path
Every expansion must include:
- prior enum/registry snapshot
- changed fields
- affected helper modules
- affected tests
- blocked old behavior
- rollback command or revert commit
- post-rollback validation
- no-memory-mutation confirmation
- no `.weslr` IO confirmation

Rollback must restore the previous routing surface and validator behavior before any new expansion is re-attempted.

## 11. Second true-run interaction
After implementation, the second true run should:
- use a non-WiFi domain
- test ontology-insufficient detection
- test expansion request creation
- test no auto-application
- test operator-review packet creation
- test disconfirmation-first fields
- test no public claim / no accepted evidence

## 12. Integration with discovery layers
This protocol must integrate with:
- fringe-edge science layer
- time-revisit layer
- domain-convergence layer
- future-work/job-transformation layer
- language/protocol discovery layer
- artifact proposal layer
- disconfirmation-first layer
- source-selection evidence plan
- MLCF routing
- cross-domain scout
- candidate-preparation helper

## 13. Extraordinary-claim handling
If expansion is triggered by fringe or extraordinary claims, require:
- `extraordinary_claim_signal` or `fringe_edge_science_signal`
- thermodynamics / energy-conservation checks where relevant
- independent replication requirement
- fraud/scam-risk check
- safety/legal check
- `EXTRAORDINARY_CLAIM_REVIEW_CONFIRMED`
- no candidate-preparation route unless separately authorized after disconfirmation

## 14. Language/protocol expansion handling
If expansion is triggered by new language/protocol patterns, require:
- language/protocol candidate marker
- domain translation hypothesis
- user-teaching artifact candidate
- concept-map candidate
- learning-sequence candidate
- no universal-language claim
- no WESLR-generates-language claim
- operator review token

## 15. Future-work/job-transformation handling
If expansion is triggered by work/job transformation, require:
- `future_workforce_impact_hypothesis`
- no market hype
- uncertainty labels
- social/economic disconfirmation
- regulatory constraints
- operator review

## 16. Disconfirmation-first requirements
Every expansion request must preserve disconfirmation-first rules:
- unknown signals do not silently archive
- unknown signals do not become candidates
- route eligibility remains explicit
- evidence acceptance stays blocked until later authorization
- expansion requests never become final answers

## 17. Blocked routes and forbidden claims
Blocked routes:
- direct candidate promotion from expansion request
- accepted-evidence creation
- final-answer generation
- public-proof claims
- runtime auto-modification
- `.weslr` persistence actions

Forbidden claims:
- discovery proof
- universal language
- product readiness
- AGI/sentience/consciousness claims
- accepted evidence or accepted candidate claims
- automatic ontology sufficiency claims

## 18. Validation plan
Future tests should cover:
- valid expansion request packet
- unknown signal does not silently archive
- unknown signal does not become candidate-preparation
- operator token required
- registry-only expansion path
- code-change-required expansion path
- rollback packet shape
- extraordinary-claim expansion quarantined
- language/protocol expansion blocked from universal claims
- future-work expansion blocked from market hype
- no `.weslr` IO
- no runtime/chat/UI/voice edits
- no public claim
- JSON-safe serialization

## 19. Future implementation plan
Implementation should proceed in a separate lane after review:
1. add protocol schema helpers
2. add ontology-insufficient detection hooks
3. add expansion request packet builder
4. add operator token handling
5. add registry/code-change separation tests
6. add rollback metadata helpers
7. add focused second-true-run tests
8. review before any broader routing changes

## 20. Next recommended lane
`REVIEW_WESLR_ONTOLOGY_EXPANSION_PROTOCOL_V1`

## 21. Final judgment
`ontology_expansion_protocol_design_ready_for_review`
