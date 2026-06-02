# WESLR Document Access Control and PII Scrubbing Boundary V1

## 1. Executive doctrine

Document access is a permission and privacy boundary.
PII scrubbing is a minimization and exposure-control boundary.
Neither grants truth authority.

Core rule: a document being accessible does **not** mean it is safe to cite, safe to store, safe to vectorize, safe to use publicly, or safe to act on.

## 2. Boundary position

```
uploaded file / memory source / retrieved document / artifact / source node
→ access classification
→ privacy sensitivity classification
→ PII detection/scrubbing policy
→ Poison Shield
→ Source Evidence Graph
→ RAG query routing
→ NAIE
→ inline citation / claim grounding
→ final answer assembly later
→ daemon receives compact verdict only
```

This boundary sits before retrieval, grounding, and downstream daemon verdict shaping.

## 3. Access levels

Allowed access levels:
- `owner_private`
- `operator_internal`
- `project_internal`
- `workspace_shared`
- `public_source`
- `public_website_source`
- `third_party_source`
- `unknown_access`
- `access_blocked`

## 4. Privacy sensitivity levels

Allowed privacy sensitivity levels:
- `non_sensitive`
- `low_sensitivity`
- `medium_sensitivity`
- `high_sensitivity`
- `restricted_sensitive`
- `unknown_sensitivity`

## 5. Source use permissions

Allowed use permissions:
- `may_read_metadata`
- `may_read_summary`
- `may_read_content`
- `may_index`
- `may_vectorize`
- `may_quote`
- `may_cite_private`
- `may_cite_public`
- `may_use_for_answer`
- `may_use_for_public_claim`
- `may_use_for_action`
- `blocked`

## 6. PII categories

Allowed PII categories:
- `personal_name`
- `email_address`
- `phone_number`
- `postal_address`
- `precise_location`
- `government_id`
- `financial_data`
- `payment_data`
- `health_data`
- `biometric_data`
- `child_data`
- `employment_data`
- `legal_data`
- `authentication_secret`
- `api_key_or_token`
- `private_message`
- `unknown_pii`

## 7. Scrubbing modes

Allowed scrubbing modes:
- `no_scrub_required`
- `metadata_only`
- `summary_only`
- `redact_direct_identifiers`
- `redact_sensitive_fields`
- `hash_reference_only`
- `block_content_use`
- `block_public_use`
- `owner_review_required`
- `operator_review_required`

## 8. Access control packet shape

Future packet fields:
- `document_access_packet_id`
- `source_id`
- `source_type`
- `source_name`
- `source_scope`
- `access_level`
- `privacy_sensitivity`
- `detected_pii_categories`
- `scrubbing_mode`
- `allowed_uses`
- `blocked_uses`
- `raw_content_allowed`
- `summary_allowed`
- `indexing_allowed`
- `vectorization_allowed`
- `private_citation_allowed`
- `public_citation_allowed`
- `answer_use_allowed`
- `public_claim_use_allowed`
- `action_use_allowed`
- `owner_review_required`
- `operator_review_required`
- `deletion_required_on_request`
- `export_required_on_request`
- `retention_policy_ref`
- `source_evidence_graph_allowed`
- `rag_routing_allowed`
- `daemon_packet_allowed`
- `recommended_next_gate`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `proof_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 9. Raw content rules

- Raw private content should not cross helper/daemon boundaries.
- Raw private content should not be placed into daemon packets.
- Raw private content should not be used in public citations.
- Raw private content should not be stored in Source Evidence Graph unless explicitly policy-approved later.
- Summaries should be preferred when possible.
- Hash/reference-only mode should be available.
- Secrets/tokens must be blocked, not summarized.

## 10. Vectorization / indexing rules

- No vectorization before explicit access and privacy policy.
- No private data in vector store without retention/deletion/export policy.
- Chunking must preserve source access metadata.
- Chunking must preserve privacy sensitivity metadata.
- Cross-user isolation is mandatory.
- Deletion/export implications must be tracked.
- Public-source indexing is not automatically safe for public claims.

## 11. Citation rules

- Private source may support private answer only if access allowed.
- Private source may not be cited publicly unless public citation allowed.
- Access-restricted evidence must become citation-blocked.
- PII-sensitive evidence must use summary/redaction if allowed.
- Poisoned content cannot support citations.
- Unsupported or blocked evidence must remain visible as blocked metadata.

## 12. RAG relationship

RAG routing must consult this boundary before retrieval.

RAG routing may receive:
- access allowed / blocked
- summary-only required
- vectorization blocked
- public citation blocked
- privacy sensitivity
- PII category summary
- recommended next gate

RAG routing must not receive:
- raw private content unless explicitly authorized
- secrets/tokens
- hidden prompts
- unrelated cross-user content

## 13. Source Evidence Graph relationship

Source Evidence Graph may store:
- source metadata
- access status
- privacy sensitivity
- claim status
- redacted summaries
- blocked-use reasons

Source Evidence Graph must not store:
- raw private documents by default
- secrets/tokens
- private raw logs
- unapproved vector chunks

## 14. Inline citation / grounding relationship

Claim grounding must use:
- private citation allowed
- public citation allowed
- source freshness
- poison status
- access restrictions
- PII scrubbing status

Grounding must block:
- access-forbidden citations
- public citations from private sources
- citations exposing secrets/PII
- public claims based on private evidence

## 15. Daemon relationship

Daemon may receive only compact verdicts:
- access_allowed
- access_blocked
- privacy_blocked
- summary_only
- public_use_blocked
- operator_review_required

Daemon must not receive:
- raw document text
- raw private memory
- PII details beyond compact category/status
- secrets/tokens
- source chunks
- vector payloads

## 16. Document-to-action relationship

Document-to-action remains blocked.

Document content cannot authorize:
- tool execution
- code changes
- emails/messages
- calendar changes
- device control
- public claim publication

Future action requires:
- Tool-Use Executor Boundary
- Action Authority Boundary
- Owner Operator Workflow Engine

## 17. GDPR / legal posture

This design supports privacy and data-minimization thinking, but does not claim legal compliance.

Must not claim:
- GDPR certification
- legal sufficiency
- security certification
- production readiness

Should preserve:
- deletion request implications
- export request implications
- retention policy references
- consent/authorization tracking
- cross-user isolation

## 18. Initial examples

1. Public source may be summarized and cited publicly.
2. Owner-private document may support private answer but not public citation.
3. Access-restricted document blocks RAG retrieval.
4. Document with email/phone requires direct identifier redaction.
5. Document with API key blocks content use.
6. Child data requires restricted-sensitive handling.
7. Health/legal data requires owner/operator review.
8. Uploaded project file may enter Source Evidence Graph as summary-only.
9. Private evidence blocks public website claim.
10. Daemon receives only access_blocked compact verdict.

## 19. Future helper design

Recommended future helper:
`weslr/document_access_pii_boundary.py`

Future APIs:
- `build_document_access_packet_v1(...)`
- `classify_document_access_v1(...)`
- `classify_pii_sensitivity_v1(...)`
- `select_scrubbing_mode_v1(...)`
- `validate_document_access_packet_v1(packet)`
- `summarize_document_access_packet_v1(packet)`
- `to_document_access_json_safe_v1(value)`
- `build_initial_document_access_examples_v1()`

## 20. Future implementation strategy

1. metadata-only packet builder
2. synthetic examples
3. validation helper
4. PII category classifier from explicit metadata only
5. scrubbing mode selector
6. Source Evidence Graph integration
7. RAG routing integration
8. inline citation grounding integration
9. deletion/export/retention policy integration later
10. real content scrubbing much later with owner approval

## 21. Boundaries and non-claims

This design does not implement access control.
It does not inspect documents.
It does not scrub real content.
It does not vectorize files.
It does not implement RAG.
It does not retrieve documents.
It does not call models/providers.
It does not write memory.
It does not write `.weslr`.
It does not authorize public claims.
It does not authorize document-to-action.
It does not claim GDPR compliance, legal sufficiency, security certification, public readiness, or production readiness.

## 22. Recommended next lane

Recommended:
`IMPLEMENT_WESLR_DOCUMENT_ACCESS_CONTROL_AND_PII_SCRUBBING_BOUNDARY_V1`

Then:
`IMPLEMENT_WESLR_RAG_QUERY_ROUTING_AND_RETRIEVAL_BOUNDARY_V1`

Preserve:
`IMPLEMENT_WESLR_INLINE_CITATION_AND_CLAIM_GROUNDING_LAYER_V1`

## 23. Final judgment

`document_access_pii_boundary_design_ready_for_metadata_helper_implementation`
