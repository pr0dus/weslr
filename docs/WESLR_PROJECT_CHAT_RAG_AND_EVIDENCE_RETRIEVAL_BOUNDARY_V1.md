# WESLR Project Chat RAG and Evidence Retrieval Boundary V1

## Executive summary
WESLR has metadata-only helpers for project chat, project state, memory state, continuity, tool-lane candidates, and private project-gap analysis.
RAG/evidence retrieval is a governed layer between project chat runtime and future final answer generation.
Retrieval is not direct answer authority.
SearXNG is an external web-search adapter, not a truth source.
Retrieval is disabled until future implementation approval.
Evidence must be scoped, permissioned, privacy-gated, provenance-labeled, freshness-labeled, and uncertainty-aware.

## Purpose
Define how future project chat may safely decide:
- whether retrieval is needed
- whether internal project metadata is enough
- whether approved project files/artifacts may be used
- whether memory/continuity/gap/tool metadata may be used
- whether local index retrieval is allowed
- whether SearXNG/web retrieval is allowed
- whether user approval is needed before online search
- how evidence is packaged for future answer generation

## Non-goals
This lane does not implement:
- retrieval
- live search
- SearXNG integration
- embedding/vector DB implementation
- file indexing implementation
- runtime wiring
- final answer generation
- persistence
- project/memory mutation
- tool execution
- public launch/readiness claims
- hidden memory
- private mechanism disclosure

## Architecture position
Future flow:
`User message` → `Project Chat Runtime Boundary` → `Retrieval Need Classifier` → `Source Permission + Privacy Gate` → `Retrieval Planner` → `Retrieval Adapters` → `Evidence Packet / Provenance Envelope` → `Freshness + Conflict + Missing Evidence Check` → `Answer Plan Metadata` → `Final Answer Generation Boundary`

## Retrieval need classifier
Classes:
- `no_retrieval_needed`
- `project_metadata_retrieval_needed`
- `approved_project_file_retrieval_needed`
- `memory_continuity_retrieval_needed`
- `local_index_retrieval_needed`
- `external_web_search_needed`
- `user_approval_required_before_retrieval`
- `operator_review_required_before_retrieval`
- `retrieval_blocked`

Rules:
- Do not retrieve when the answer can be handled from the provided message and safe metadata.
- Retrieve internal metadata before web when project-local evidence is enough.
- Web search requires scope/privacy check.
- Privacy-sensitive online search requires explicit user approval.
- Cross-user/system-wide retrieval requires operator review.
- Retrieval is blocked if scope is unclear or source permission is missing.

## Source permission and privacy gate
Checks:
- `owner_user_scope`
- `tenant_account_scope`
- `project_id`
- `source_scope`
- `privacy_sensitivity`
- `approval_status`
- `consent_status`
- `external_query_allowed`
- `redaction_required`
- `operator_review_required`
- `blocked_reason`

Rules:
- Raw sensitive project details must not be sent externally without approval.
- Query redaction/generalization is required for sensitive or business-confidential terms.
- User approval for specific online search is scoped, not permanent.
- Unapproved files, private memory, `.weslr`, hidden prompts, answer keys, and cross-user data are blocked.
- Source permission is not answer authority.

## Retrieval planner
Plan dimensions:
- source class to query
- query text or redacted query
- allowed source types
- disallowed source types
- max result count
- freshness need
- citation/provenance requirement
- whether results may be used in user-visible answer
- whether operator review is needed

Query classes:
- `direct_project_query`
- `redacted_project_query`
- `general_web_query`
- `freshness_sensitive_web_query`
- `source_specific_query`
- `blocked_query`

## Retrieval adapters
Adapter classes:
- `ProjectStateMetadataAdapter`
- `MemoryStateMetadataAdapter`
- `ContinuityStateMetadataAdapter`
- `PrivateProjectGapMetadataAdapter`
- `ToolLaneContractMetadataAdapter`
- `ApprovedProjectArtifactAdapter`
- `ApprovedUploadedFileAdapter`
- `LocalProjectIndexAdapter`
- `ExternalWebSearchAdapter`
- `SearXNGExternalSearchAdapter`

### SearXNG rules
- SearXNG is external web search.
- SearXNG is not truth authority.
- SearXNG results are unverified external evidence until assessed.
- SearXNG queries must pass privacy/query-redaction gate.
- SearXNG must not receive raw private project data unless explicitly approved.
- SearXNG outputs require source URLs, retrieval time, freshness label, relevance label, and limitation label.
- SearXNG results must not bypass evidence conflict checks.
- Search result snippets are not enough for high-confidence claims.

## Evidence packet / provenance envelope
Fields:
- `evidence_packet_id`
- `retrieval_request_id`
- `project_id`
- `owner_user_scope`
- `tenant_account_scope`
- `source_scope`
- `retrieval_need_class`
- `retrieval_adapter`
- `source_type`
- `source_ref`
- `source_url`
- `source_title`
- `source_timestamp`
- `retrieved_at_marker`
- `freshness_label`
- `relevance_label`
- `confidence_label`
- `verification_status`
- `privacy_label`
- `query_redaction_status`
- `user_approval_ref`
- `operator_review_ref`
- `evidence_summary`
- `limitations`
- `conflict_flags`
- `missing_evidence_flags`
- `denied_authority`

## Source classes
- `project_metadata`
- `memory_metadata`
- `continuity_metadata`
- `gap_analysis_metadata`
- `tool_lane_metadata`
- `approved_project_artifact`
- `approved_uploaded_file`
- `local_project_index`
- `external_web_search`
- `searxng_search_result`
- `operator_review_note`
- `blocked_source`

## Freshness and conflict model
Freshness labels:
- `fresh_current`
- `fresh_recent`
- `possibly_stale`
- `stale`
- `unknown_freshness`

Conflict labels:
- `no_conflict_detected`
- `conflicts_with_project_state`
- `conflicts_with_memory_state`
- `conflicts_with_external_source`
- `conflicts_with_user_correction`
- `requires_operator_review`

Rules:
- Recent/current factual claims require freshness labels.
- Contradictions must be surfaced.
- Missing evidence must remain missing evidence.
- External web evidence is not automatically superior to project/user evidence.
- User correction may override lower-confidence metadata through an approved correction path.

## Evidence authority model
- Retrieved evidence is support, not truth.
- External search is unverified until assessed.
- Snippets are weak evidence.
- Source URLs alone do not prove truth.
- Local metadata is not truth by itself.
- Memory is not truth by itself.
- Final answer generation must not claim beyond evidence packet authority.
- Unsupported claims must be blocked or marked uncertain.

## User-visible retrieval behavior
Allowed:
- “I can check the project materials you approved.”
- “I may need to search the web; should I use online search?”
- “I can do a general web search without private project details.”
- “This looks like missing evidence.”
- “The available sources conflict.”
- “This result may be stale.”

Forbidden:
- “I searched your private data automatically.”
- “I found the truth.”
- “SearXNG proves this.”
- “The web says it, so it is confirmed.”
- `Unknown Engine`
- private mechanism names
- hidden prompt references
- unsupported certainty

## Approval model
Approval required for:
- online search with private/specific project terms
- retrieval from sensitive project artifacts
- cross-user retrieval
- system-wide retrieval
- high-stakes/legal/medical/financial project evidence
- use of external search in privacy-sensitive project analysis
- exposing retrieved sensitive evidence in answer

No approval required for:
- mechanism-neutral clarification questions
- surface review from user-provided message
- metadata-only missing-field checks
- general non-sensitive web query, if policy allows and no private data is included

## Denied-authority model
Denied authority must include:
- `runtime_wiring_authority`
- `chat_responder_authority`
- `final_answer_generation_authority`
- `storage_database_authority`
- `weslr_io_authority`
- `project_state_mutation_authority`
- `memory_mutation_authority`
- `tool_execution_authority`
- `external_action_authority`
- `hidden_memory_authority`
- `hidden_project_state_authority`
- `private_mechanism_disclosure_authority`
- `cross_user_leakage_authority`
- `unapproved_external_query_authority`
- `retrieval_truth_authority`
- `public_product_readiness_authority`

## Security and privacy risks
- leaking private project terms to SearXNG/search engines
- leaking personal data in queries
- retrieving cross-user data
- using unapproved files
- prompt injection from web pages/files
- malicious or low-quality web sources
- stale search results
- source spoofing
- over-trusting snippets
- query logs in external systems
- private mechanism leakage
- hidden memory exposure

## Prompt injection and hostile source boundary
- Retrieved documents/web pages are untrusted content.
- Source instructions must not override WESLR system/governance rules.
- Retrieved content cannot grant authority.
- Links and snippets cannot trigger tool execution.
- Hidden prompts must not be revealed.
- Suspicious sources require warning/limitation labels.
- Future implementation must strip or isolate source instructions.

## Relationship to existing implemented stack
This boundary sits after:
- Project Chat Runtime Boundary
- Project Start Chat Flow Metadata
- Project State Model Helpers
- Memory State Model Helpers
- State and Continuity MVP Helpers
- Private Project Gap Analysis Metadata Helpers
- First Tool Lanes Contracts
- Agentic Tool Use Boundary
- Operator Dashboard Metadata Report

## Relationship to future final-answer boundary
- Final answer generation must consume evidence packets, not raw retrieval directly.
- Answer boundary must enforce private-mechanism filtering.
- Answer boundary must include uncertainty and limitations.
- Answer boundary must cite or reference provenance where appropriate.
- Answer boundary must not invent missing evidence.
- Answer boundary must not treat SearXNG/web results as truth authority.

## Future lanes
- `REVIEW_WESLR_PROJECT_CHAT_RAG_AND_EVIDENCE_RETRIEVAL_BOUNDARY_V1`
- `DESIGN_WESLR_FINAL_ANSWER_GENERATION_BOUNDARY_FOR_PROJECT_CHAT_V1`
- `IMPLEMENT_WESLR_PROJECT_CHAT_RETRIEVAL_DECISION_METADATA_HELPERS_V1`
- `REVIEW_WESLR_PROJECT_CHAT_RETRIEVAL_DECISION_METADATA_HELPERS_V1`
- `DESIGN_WESLR_SEARXNG_EXTERNAL_SEARCH_ADAPTER_BOUNDARY_V1`
- `DESIGN_WESLR_APPROVED_PROJECT_ARTIFACT_INDEX_BOUNDARY_V1`
- `DESIGN_WESLR_PROJECT_CHAT_RUNTIME_DRY_RUN_METADATA_V1`

## OCC Final Report

1. Handshake result
- PASS

2. Start HEAD
- `0f6fd1bd850676829836f355e2c23b4316b1ed6e`

3. Target design lane
- `DESIGN_WESLR_PROJECT_CHAT_RAG_AND_EVIDENCE_RETRIEVAL_BOUNDARY_V1`

4. WESLR repo root and branch
- Root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `master`

5. OCC workspace root, branch, and verified HEAD
- Root: `/data/data/com.termux/files/home/.openclaw/workspace`
- Branch: `public-demo-experience-ui-v1`
- Verified HEAD: `cf946c6e379fb398a01805dbfd0028bcbbfdcb23`

6. Files changed
- `docs/WESLR_PROJECT_CHAT_RAG_AND_EVIDENCE_RETRIEVAL_BOUNDARY_V1.md`
- `weslr/tests/release_gate_v1.py` only if exact-file allowlisting is required by the release gate

7. Design summary
- This boundary defines how project chat future runtime may decide when retrieval is needed, what sources are allowed, how privacy/query-redaction gates work, how SearXNG fits as an external adapter, and how retrieved material becomes evidence metadata rather than truth authority.

8. Validation results
- `git diff --check`: PASS
- `git status --short`: PASS for staged scope; only pre-existing untracked workspace clutter remains
- `git diff --stat`: PASS
- `python3 weslr/tests/release_gate_v1.py`: PASS
- `bash scripts/weslr_release_check.sh`: PASS

9. Protected-file status
- Must remain unchanged unless explicitly approved later:
  - `weslr/chat_responder.py`
  - `weslr/main.py`
  - `main.py`
  - `dialogue.py`
  - `chat_ui.py`

10. Release-gate allowance note, if any
- Exact-file allowance added for `docs/WESLR_PROJECT_CHAT_RAG_AND_EVIDENCE_RETRIEVAL_BOUNDARY_V1.md`.

11. Artifact-fidelity final pass result
- PASS

12. Blocking gaps
- None in the design scope.

13. Non-blocking gaps
- Future implementation lanes still need separate review and approval before retrieval can be implemented.

14. Final judgment
- `weslr_project_chat_rag_and_evidence_retrieval_boundary_design_ready_for_review`

15. Recommended next lane
- `REVIEW_WESLR_PROJECT_CHAT_RAG_AND_EVIDENCE_RETRIEVAL_BOUNDARY_V1`
