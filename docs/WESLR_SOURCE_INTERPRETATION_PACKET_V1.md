# WESLR Source Interpretation Packet V1

## 1. Purpose
Define `source_interpretation_packet_v1`: a metadata-first, review-bound packet that records what WESLR extracted from an authorized source, what evidence role it might play, what claims remain blocked, what conflicts/disconfirmations exist, and what next safe artifact or review step is recommended.

This packet is not accepted evidence, not a final answer, and not a public claim.

## 2. Relationship to the authorization boundary
This packet may exist only after a valid source-ingestion authorization packet.

It must require and respect:
- `ingestion_request_id`
- `authorization_packet_ref`
- `source_ref`
- `source_class`
- `retention_mode`
- `review_requirements`
- `blocked_claims`
- `denied_authority_flags`

It must respect the authorization packet’s:
- source class
- access/license/privacy posture
- retention mode
- raw retention permission
- quoted excerpt policy
- owner/operator/expert review requirements
- abort conditions
- denied authority flags

It must not bypass authorization, provenance, retention, or review gates.

## 3. Required packet fields
Minimum required fields:
- `schema_name`
- `schema_version`
- `interpretation_packet_id`
- `ingestion_request_id`
- `authorization_packet_ref`
- `source_ref`
- `source_class`
- `source_access_level`
- `license_access_posture`
- `privacy_posture`
- `retention_mode`
- `source_metadata`
- `interpreted_under_authorization`
- `bounded_content_policy`
- `extracted_claims`
- `extracted_assumptions`
- `method_limits`
- `evidence_role_candidates`
- `counterevidence_or_disconfirmation`
- `source_conflicts`
- `missing_evidence`
- `pattern_attribution_candidates`
- `artifact_route_candidates`
- `mlcf_normalization_hints`
- `oer_or_noop_hints`
- `candidate_preparation_eligibility`
- `review_requirements`
- `blocked_claims`
- `denied_authority_flags`
- `abort_conditions`
- `blocked_labels`
- `safe_metadata_summary`
- `next_safe_step`
- `final_judgment`

## 4. Source metadata
`source_metadata` may include only safe metadata and provenance-friendly details such as:
- title
- authors or organization if available
- publication/source date if available
- source host/domain
- source class
- source access/license/privacy posture
- citation/provenance reference
- locator record reference if sourced from a metadata locator
- content hash or local file hash only if authorized and safe
- retrieval timestamp only in future implementation

Raw content retention is not required.

## 5. Extracted claims
Claims are review-bound only.

Each claim candidate should include:
- `claim_id`
- `claim_text_or_safe_paraphrase`
- `claim_type`
- `source_location_ref`
- `evidence_role_candidate`
- `confidence_posture`
- `required_review`
- `blocked_claims`
- `disconfirmation_need`

The packet must not mark claims as true, accepted evidence, or final answers.

## 6. Assumptions and method limits
Each assumption or method limit should include:
- `id`
- `statement`
- `category`
- `why_it_matters`
- `what_would_break_it`
- `review_required`
- `related_claim_ids`

## 7. Evidence role candidates
Supported candidate roles:
- `primary_evidence_candidate`
- `supporting_evidence_candidate`
- `counterevidence_candidate`
- `disconfirmation_source_candidate`
- `method_limit_source`
- `implementation_reference`
- `historical_context`
- `known_science_replay_reference`
- `source_selection_reference`
- `weak_signal_only`
- `not_evidence`
- `blocked_evidence`

All remain candidate/review-bound.

## 8. Confidence posture
Use only:
- `interpretation_low`
- `interpretation_medium`
- `interpretation_high`
- `interpretation_conflicted`
- `interpretation_unknown`

Interpretation confidence must not be treated as truth confidence.

## 9. Disconfirmation-first structure
The packet must include:
- what would disconfirm the claim
- what would make the source irrelevant
- what alternative explanations exist
- what source class is needed next
- what expert review is needed
- what cannot be claimed yet

## 10. Conflict handling
Supported conflict states:
- `no_known_conflict`
- `internal_source_conflict`
- `conflict_with_other_source`
- `conflict_with_known_science_replay`
- `conflict_requiring_expert_review`
- `conflict_requiring_more_evidence`
- `conflict_requiring_stop_or_block`

Conflicts must never be resolved automatically.

## 11. Pattern attribution candidates
Each pattern attribution candidate should include:
- `source_pattern_id`
- `target_domain_or_experiment`
- `shared_structure`
- `key_differences`
- `possible_mechanism_overlap_posture`
- `disconfirmation_tests`
- `analogy_strength`
- `blocked_claims`
- `next_safe_step`

Same-mechanism claims are blocked unless separately evidenced and reviewed.

## 12. Artifact route candidates
Supported routes:
- `unexplained_signal_artifact`
- `false_assumption_or_overclaim_artifact`
- `unfinished_work_artifact`
- `experiment_plan_artifact`
- `source_selection_evidence_plan`
- `normalized_evidence_packet`
- `artifact_forward_work_plan`
- `product_or_workflow_artifact`
- `operator_review`
- `expert_review`
- `blocked_state`

## 13. MLCF normalization hints
The packet may suggest:
- source class
- evidence role candidate
- authority posture
- retention posture
- provenance/citation posture
- conflict/disconfirmation markers
- missing evidence
- review requirements

It must not write to MLCF directly.

## 14. OER / no-op hints
The packet may suggest:
- ontology seems sufficient
- ontology seems insufficient
- route to OER no-op
- route to ontology expansion request
- route to operator review
- no ontology action

It must not auto-apply ontology changes.

## 15. Candidate-preparation eligibility
Supported values:
- `candidate_preparation_excluded`
- `candidate_preparation_premature`
- `candidate_preparation_possible_after_review`
- `candidate_preparation_possible_after_evidence_normalization`
- `candidate_preparation_blocked`

The packet must not create candidates directly.

## 16. Denied authority flags
Explicit false flags:
- `accepted_evidence_authority`
- `accepted_candidate_authority`
- `final_answer_authority`
- `public_claim_authority`
- `proof_claim_authority`
- `discovery_truth_claim_authority`
- `product_readiness_claim_authority`
- `runtime_wiring_authority`
- `provider_model_call_authority`
- `source_fetch_authority`
- `source_ingestion_authority`
- `raw_retention_authority`
- `memory_mutation_authority`
- `database_write_authority`
- `weslr_io_authority`
- `ontology_auto_application_authority`
- `self_modification_authority`

Any true denied authority flag must fail validation.

## 17. Retention behavior
The packet may contain only:
- metadata
- safe paraphrases
- bounded excerpts only if authorized
- citation/provenance references

It must not contain:
- raw full text unless explicitly owner-authorized
- private data
- secrets
- `.weslr`
- hidden prompts
- source dumps

## 18. Abort conditions
Abort interpretation packet creation if:
- no valid authorization reference
- source class is blocked
- authorization is missing where required
- retention policy is violated
- raw source content appears when not allowed
- `.weslr` appears
- secrets/credentials appear
- accepted evidence/candidate wording appears
- final-answer wording appears
- proof/discovery/public-science/product-readiness claim appears
- provider/model/runtime authority appears
- source fetch/ingestion authority appears outside authorization
- conflict requires expert review before interpretation
- provenance/citation reference is missing

## 19. Future implementation files and APIs
Proposed files:
- `weslr/source_interpretation_packet.py`
- `weslr/tests/test_source_interpretation_packet_v1.py`

Expected APIs:
- `build_source_interpretation_packet_v1`
- `validate_source_interpretation_packet_v1`
- `summarize_source_interpretation_packet_v1`
- `render_source_interpretation_packet_markdown_v1`
- `to_source_interpretation_packet_json_safe_v1`
- `build_initial_source_interpretation_examples_v1`

## 20. Future examples
Include:
- public research paper interpreted as evidence candidate
- official standard interpreted as authority/context source
- GitHub repo interpreted only as implementation reference
- false-assumption article interpreted for disconfirmation mapping
- pulsar known-science replay reference
- owner-uploaded PDF with no raw retention
- unsafe packet with accepted-discovery wording blocked
- unsafe packet containing `.weslr` blocked
- weak source routed to not-evidence / weak-signal-only

## 21. Validation expectations
Future validator must fail closed on:
- missing required fields
- missing authorization reference
- invalid source class
- invalid retention mode
- raw content without authorization
- `.weslr`
- hidden prompts
- secrets/credentials
- private data without authorization
- accepted evidence/candidate wording
- final-answer wording
- proof/discovery/public-science/product-readiness claims
- true denied authority flags
- missing blocked claims
- missing abort conditions
- missing review requirements
- missing provenance/source ref
- route to candidate-prep without review/evidence normalization
- same-mechanism pattern attribution claim without evidence/review

## 22. Owner / assistant usage model
Safe flow:
1. Owner/assistant provides authorized source or source request.
2. Authorization boundary creates an authorization packet.
3. Interpreter creates this source interpretation packet.
4. Owner/assistant reviews the packet.
5. Only then can later lanes normalize evidence, create artifacts, or plan experiments.

This allows WESLR to ingest and interpret sources through governance without becoming uncontrolled browsing or raw RAG.

## 23. Recommended next lane
`REVIEW_WESLR_SOURCE_INTERPRETATION_PACKET_V1`
