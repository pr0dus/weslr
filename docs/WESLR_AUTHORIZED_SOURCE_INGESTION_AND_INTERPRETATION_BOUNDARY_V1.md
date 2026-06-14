# WESLR Authorized Source Ingestion And Interpretation Boundary V1

## 1. Boundary definition
**Name:** `authorized_source_ingestion_interpretation_boundary_v1`

A governed source-ingestion door that allows WESLR to read authorized sources only when source class, purpose, retention, evidence role, review requirement, and blocked claims are explicitly defined first.

## 2. Core principle
Unauthorized ingestion is forbidden.
Authorized ingestion is allowed only through this boundary.

WESLR does not ingest sources to produce final answers directly.
WESLR ingests sources to create governed interpretation/evidence/artifact packets that remain review-bound until validated.

## 3. Allowed source entry types
Future ingestion requests may support:
- public/open URL
- public/open PDF
- public/open dataset reference
- public/open GitHub repository reference
- official standard/reference
- official agency/government source
- vendor documentation
- public research paper
- public university/lab artifact
- user-uploaded file
- owner-pasted text
- local file explicitly authorized by owner
- selected metadata-locator result

## 4. Blocked source entry types by default
Blocked unless explicitly authorized and scoped:
- private data without explicit owner authorization
- `.weslr`
- hidden prompts
- private logs
- private emails/messages unless explicitly authorized
- personal medical/legal/financial data unless explicit scoped authorization exists
- paid/closed/copyright-restricted full text unless allowed by license/access
- unknown-source license state
- scraped sites that forbid access
- credentials/secrets/tokens
- private GitHub repos unless owner explicitly authorizes
- any source requiring deception, bypass, or credential misuse

## 5. Source classification
Every ingestion request must classify source as one of:
- `official_standard`
- `official_government_or_agency_data`
- `official_vendor_documentation`
- `public_research_paper`
- `public_dataset`
- `github_repository`
- `public_lab_or_university_artifact`
- `public_benchmark_or_test_suite`
- `public_news_or_report`
- `forum_or_social_discussion`
- `owner_uploaded_file`
- `owner_pasted_text`
- `private_owner_authorized_source`
- `unknown_source_class`
- `blocked_source_class`

## 6. Authorization packet
Before ingestion, WESLR must build an authorization packet containing:
- `ingestion_request_id`
- `requested_by`
- `source_ref`
- `source_class`
- `source_access_level`
- `license_access_posture`
- `privacy_posture`
- `ingestion_purpose`
- `artifact_target`
- `evidence_role_target`
- `raw_retention_allowed`
- `derived_metadata_allowed`
- `quoted_excerpt_allowed`
- `max_excerpt_policy`
- `owner_authorization_required`
- `owner_authorization_present`
- `operator_review_required`
- `expert_review_required`
- `blocked_claims`
- `denied_authority_flags`
- `abort_conditions`
- `next_safe_step`
- `final_judgment`

## 7. Ingestion purposes
Allowed purposes:
- `evidence_candidate_extraction`
- `source_metadata_extraction`
- `claim_boundary_mapping`
- `disconfirmation_mapping`
- `method_limit_extraction`
- `implementation_reference_mapping`
- `known_science_replay`
- `pattern_attribution_support`
- `artifact_context_support`
- `source_selection_validation`
- `contradiction_or_counterevidence_check`

Forbidden purposes:
- direct final answer production
- public claim generation
- proof/discovery confirmation
- accepted evidence creation without review
- accepted candidate creation without review
- autonomous web crawling
- private memory mutation
- runtime action execution
- ontology auto-application

## 8. Ingestion stages
Safe pipeline:
- Stage 0: source authorization packet
- Stage 1: source access check
- Stage 2: source metadata extraction
- Stage 3: bounded content extraction
- Stage 4: claim/assumption/method extraction
- Stage 5: evidence-role classification
- Stage 6: contradiction/disconfirmation extraction
- Stage 7: MLCF evidence normalization
- Stage 8: pattern-attribution candidate creation
- Stage 9: artifact routing
- Stage 10: owner/operator/expert review
- Stage 11: accepted evidence only in a later separately authorized lane

Ingestion does not automatically produce accepted evidence.

## 9. Retention policy
Supported retention modes:
- `metadata_only_no_content_retention`
- `derived_summary_only`
- `bounded_excerpt_with_citation`
- `full_text_transient_no_retention`
- `full_text_retention_owner_authorized`
- `blocked_retention`

Default:
- `metadata_only_no_content_retention`
- `full_text_transient_no_retention`

Raw retention requires explicit owner authorization.

## 10. Interpretation packet
After authorized ingestion, WESLR should create an interpretation packet with:
- `source_ref`
- `source_class`
- `source_metadata`
- `extracted_claims`
- `extracted_assumptions`
- `method_limits`
- `evidence_role_candidates`
- `counterevidence_or_disconfirmation`
- `source_conflicts`
- `missing_evidence`
- `pattern_attribution_candidates`
- `artifact_route_candidates`
- `blocked_claims`
- `denied_authority_flags`
- `review_requirements`
- `safe_metadata_summary`
- `final_judgment`

## 11. Evidence role classes
Supported roles:
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

## 12. Relationship to Search Weighing Governor
The governor decides whether ingestion is worth requesting.

The ingestion boundary decides whether ingestion is allowed.

The interpretation packet returns to:
- MLCF
- pattern attribution governor
- unexplained signal artifact helper
- artifact forward plan helper
- OER/no-op logic
- candidate-prep only if later route permits

## 13. Relationship to MLCF
MLCF remains the authority/evidence accounting layer.

Ingested material must not bypass MLCF.

MLCF should receive:
- source class
- evidence role candidate
- retention mode
- blocked claims
- denied authority flags
- review requirements
- provenance references
- conflicts/disconfirmation markers

## 14. Relationship to artifacts
Authorized ingestion may support:
- unexplained signal artifact
- false-assumption / overclaim artifact
- unfinished work artifact
- experiment plan artifact
- source-selection evidence plan
- normalized evidence packet
- artifact forward work plan
- product/workflow artifact

It must not directly create:
- accepted discovery
- final answer
- product-ready claim
- autonomous action

## 15. API implications
Possible future private WESLR endpoints:
- `GET /health`
- `GET /capabilities`
- `POST /ingestion/authorize`
- `POST /ingestion/interpret`
- `POST /evidence/normalize`
- `POST /governor/weigh`
- `POST /artifact/build`
- `POST /review/packet`

Boundary:
- API may return governed packets only.
- It must not expose `.weslr`, raw private memory, raw source dumps, credentials, or final-answer authority.
- Public exposure is forbidden unless separately designed and approved.

## 16. Owner / ChatGPT usage model
Safe workflow:
1. Owner/ChatGPT defines the question or source.
2. WESLR builds authorization packet.
3. Owner approves if required.
4. WESLR ingests under boundary.
5. WESLR returns interpretation/evidence/artifact packet.
6. Owner/ChatGPT reviews and challenges the packet.
7. WESLR only advances after review.

This allows WESLR to be used by both human and assistant without bypassing governance.

## 17. Denied authority flags
Explicit false flags:
- `unauthorized_source_ingestion_authority`
- `autonomous_crawling_authority`
- `accepted_evidence_authority`
- `accepted_candidate_authority`
- `final_answer_authority`
- `public_claim_authority`
- `proof_claim_authority`
- `discovery_truth_claim_authority`
- `product_readiness_claim_authority`
- `runtime_wiring_authority`
- `provider_model_call_authority`
- `memory_mutation_authority`
- `database_write_authority`
- `weslr_io_authority`
- `ontology_auto_application_authority`
- `self_modification_authority`

## 18. Abort conditions
Abort ingestion if:
- source class unknown and owner approval missing
- license/access is unclear
- private data appears without authorization
- source requires credentials not approved
- request tries to ingest `.weslr`
- request asks for final answer
- request asks for accepted evidence/candidate
- request asks for proof/discovery/public claim
- request asks for raw retention without authorization
- source exceeds configured size/excerpt limit
- source contains secrets/credentials
- source is unsafe or legally restricted
- source cannot be cited/provenanced
- source conflicts require expert review before use

## 19. Future implementation sequence
Proposed files:
- `weslr/source_ingestion_authorization_boundary.py`
- `weslr/tests/test_source_ingestion_authorization_boundary_v1.py`
- `weslr/source_interpretation_packet.py`
- `weslr/tests/test_source_interpretation_packet_v1.py`

Future APIs:
- `build_source_ingestion_authorization_packet_v1`
- `validate_source_ingestion_authorization_packet_v1`
- `summarize_source_ingestion_authorization_packet_v1`
- `render_source_ingestion_authorization_markdown_v1`
- `to_source_ingestion_authorization_json_safe_v1`
- `build_source_interpretation_packet_v1`
- `validate_source_interpretation_packet_v1`
- `summarize_source_interpretation_packet_v1`
- `render_source_interpretation_markdown_v1`
- `to_source_interpretation_json_safe_v1`
- `build_initial_source_ingestion_examples_v1`

## 20. Examples
- public official standard ingestion request
- public research paper interpretation request
- GitHub repo implementation-reference request
- owner-uploaded PDF with no raw retention
- false-assumption article used only for disconfirmation mapping
- pulsar known-science replay reference
- unsafe private `.weslr` ingestion request blocked
- unsafe final-answer request blocked
- unsafe accepted-discovery request blocked

## 21. Validation expectations
Future validators must fail closed on:
- missing required fields
- owner authorization missing when required
- unknown/private/blocked source without approval
- `.weslr`
- hidden prompt/private memory content
- raw retention without authorization
- true denied authority flags
- accepted evidence/candidate wording
- proof/discovery/public-science/product-readiness claim
- final-answer authority
- autonomous crawling
- runtime/provider/model authority
- ontology auto-application/self-modification authority
- missing blocked claims
- missing provenance/source ref
- missing review requirement
- missing abort conditions

## 22. Recommended next lane
`REVIEW_WESLR_AUTHORIZED_SOURCE_INGESTION_AND_INTERPRETATION_BOUNDARY_V1`

## 23. Final judgment
`authorized_source_ingestion_interpretation_boundary_design_ready_for_review`
