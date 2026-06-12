# WESLR Authorized Ingestion Boundary V1

## 1. Purpose
This design defines the strict boundary that must exist before WESLR is ever allowed to ingest, read, fetch, parse, retain, summarize, or convert real source material into evidence-intake packets.

Authorized ingestion is the future controlled process by which WESLR may read or receive source material and convert only allowed metadata/summaries into evidence-intake packets.
It is not:
- autonomous crawling
- open web search
- unrestricted RAG
- raw private data storage
- `.weslr` memory mutation
- runtime behavior
- final-answer generation
- proof/discovery/public claim authority

## 2. Ingestion authorization states
Allowed authorization states:
- `not_authorized`
- `operator_requested_metadata_only`
- `operator_supplied_summary_only`
- `operator_supplied_document_metadata_only`
- `future_private_source_review_required`
- `blocked_sensitive_source`
- `blocked_unknown_source`
- `blocked_cross_user_or_tenant`
- `needs_repair`

These are boundary states, not ingestion permission by themselves.

## 3. Source access modes
Allowed source access modes:
- `no_access`
- `metadata_descriptor_only`
- `owner_supplied_summary`
- `owner_supplied_redacted_excerpt`
- `owner_supplied_document_reference`
- `future_connector_requires_review`
- `blocked`

These describe how a source may be handled if and only if the boundary passes.

## 4. Raw content handling states
Allowed raw content handling states:
- `raw_content_forbidden`
- `raw_content_not_retained`
- `redacted_excerpt_only`
- `summary_only`
- `future_retention_requires_design`
- `blocked`

Raw content is forbidden by default unless future design explicitly allows a narrower handling mode.

## 5. Authorization packet fields
An authorized-ingestion authorization packet should include:
- `ingestion_boundary_id`
- `requested_source_kind`
- `requested_access_mode`
- `authorization_state`
- `source_scope`
- `owner_or_operator_request_status`
- `privacy_sensitivity`
- `safety_sensitivity`
- `cross_user_or_tenant_risk`
- `raw_content_handling`
- `retention_policy`
- `allowed_output_form`
- `evidence_intake_link_allowed`
- `operator_review_required`
- `blocked_reason`
- `required_redactions`
- `forbidden_interpretations`
- `authority_status`
- `safe_metadata`

The packet is an authorization boundary record, not the ingestion itself.

## 6. Allowed output forms
Allowed output forms:
- `no_output`
- `metadata_only`
- `redacted_summary_only`
- `evidence_intake_candidate_only`
- `operator_review_packet_only`
- `blocked`

The allowed output form must be the most restrictive one compatible with the source and request.

## 7. Boundary flow
Before any future ingestion-like behavior, WESLR must pass:
1. source-kind classification
2. source-scope check
3. operator/owner request check
4. privacy sensitivity check
5. safety sensitivity check
6. cross-user/tenant check
7. raw-content-handling check
8. retention-policy check
9. allowed-output-form check
10. evidence-intake-link eligibility check
11. operator-review requirement check

Passing the boundary does not create truth, authority, or a proposed direction.
It only permits a future evidence-intake packet to be built from allowed metadata/summaries.

## 8. Hard blocked cases
The boundary must hard-block:
- hidden prompts
- answer keys
- protected benchmark materials
- private data without authorization
- cross-user or cross-tenant data
- secrets or credentials
- raw `.weslr` state
- raw private memory
- raw project state not explicitly authorized
- unknown source with authority implications
- source requiring legal or contractual review
- source that would create public claim, final-answer, proof, or discovery authority

## 9. Relationship to evidence intake
Authorized ingestion boundary comes before evidence intake.
Passing the boundary does not create truth.
Passing the boundary does not create a proposed direction.
It only allows a future evidence-intake packet to be built from allowed metadata/summaries.

## 10. No-autonomous-ingestion rule
WESLR must not autonomously decide to ingest sources.
Any future ingestion must be owner/operator requested, scoped, logged as metadata, and reviewed according to the boundary.

## 11. Safety boundaries
Forbidden in this design:
- runtime wiring
- actual ingestion implementation
- connector implementation
- provider/model/tool/retrieval/web calls
- `.weslr` IO
- persistence/database writes
- memory/project mutation
- public claim authority
- final-answer authority
- proof/discovery/AGI/public-science claims
- hidden/private/protected data intake
- cross-user leakage

## 12. Future validation requirements
A future helper must fail closed on:
- missing boundary id
- missing source kind
- invalid access mode
- invalid authorization state
- missing source scope
- missing owner/operator request status
- missing privacy/safety sensitivity
- cross-user/tenant risk not assessed
- unsafe raw content handling
- unsafe retention policy
- invalid allowed output form
- evidence intake link allowed without valid authorization
- missing forbidden interpretations
- unsafe authority flags
- public claim authorization
- final-answer authority
- source ingestion authorization without boundary pass
- runtime/provider/tool/web/retrieval implication
- `.weslr` implication
- persistence/database implication
- memory/project mutation implication
- hidden/private/protected markers
- cross-user leakage
- non-JSON-safe output

## 13. Final design statement
Authorized ingestion is a strictly controlled boundary layer for future source handling: it can authorize only bounded metadata/summaries for evidence-intake construction, never raw public truth, discovery, proof, or runtime authority.
