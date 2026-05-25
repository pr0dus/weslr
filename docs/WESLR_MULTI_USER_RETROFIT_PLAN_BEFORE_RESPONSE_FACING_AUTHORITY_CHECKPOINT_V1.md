# WESLR Multi-User Retrofit Plan Before Response-Facing Authority Checkpoint V1

## Status

- Design label: `DESIGN_MULTI_USER_RETROFIT_PLAN_BEFORE_RESPONSE_FACING_AUTHORITY_CHECKPOINT_V1`
- Document path: `docs/WESLR_MULTI_USER_RETROFIT_PLAN_BEFORE_RESPONSE_FACING_AUTHORITY_CHECKPOINT_V1.md`
- Lane status: design-only / retrofit-plan
- Scope: sequencing and boundaries for retrofitting existing runtime-adjacent memory/context/profile/artifact/timeline modules before response-facing authority/claim checkpoint design
- Runtime status: no runtime wiring
- Chat status: no chat/user-facing behavior changes
- Implementation status: no helpers, source files, tests, runners, migrations, database work, auth implementation, browser implementation, provider/model/search/advisor integrations, or `.weslr` IO implemented
- Execution status: no public/browser runtime, no account/session enforcement, no memory/context reads, no candidate response execution, no final answer assembly
- Authority status: no authority grants
- Plan judgment: `multi_user_retrofit_plan_blocks_unscoped_response_authority_ready_for_review`

This document is a retrofit plan, not implementation. It defines the order and boundaries for future implementation lanes that would make existing WESLR runtime-adjacent state safe for future public/browser/multi-user use. It does not authorize public/browser runtime, does not wire response formation, does not generate final answers, does not call providers/search/advisors, and does not make `.weslr` public state usable.

## 1. Purpose And Non-Goals

### 1.1 Purpose

The purpose of this plan is to define a staged retrofit path before WESLR continues to response-facing authority/claim checkpoint design.

The plan exists because the latest implementation audit found that many existing modules are useful local/operator foundations, but are not yet safe as public/browser/multi-user foundations. Response-facing authority design must not assume that memory, context, evidence, artifacts, uploads, logs, caches, profiles, timelines, or conversation state are scoped unless a separate reviewed retrofit lane proves that they are.

### 1.2 Non-Goals

This plan does not:

- implement namespace helpers
- implement authorization helpers
- implement scoped memory/context readers
- implement artifact/upload registries
- implement browser runtime
- implement authentication or accounts
- implement guest/session handling
- implement database migrations
- implement deletion/export/retention controls
- implement leakage tests
- modify `weslr/chat_responder.py`
- wire candidate response formation to runtime
- generate final answers, reply text, previews, or user-facing output
- call providers/models/search/advisors
- read or write live `.weslr` runtime state
- permit global `.weslr` as public shared state
- grant public/browser runtime authority
- grant response-facing authority

## 2. Audit Baseline

This plan carries forward these audit conclusions:

- Metadata/design-only helpers are safe if not runtime-wired.
- Shared Cognitive Gym exploratory case helpers remain safe as metadata-only, helper-only, deterministic, in-memory infrastructure.
- CALIBRATION_LEDGER exploratory helpers remain safe as metadata-only adapters and do not score, judge, certify, or answer.
- Reasoning substrate, context/memory trust and evidence boundary, and candidate response formation substrate remain design-only safe.
- Tenant, memory, timeline, profile, artifact, document, fact, evidence, command-cache, daemon, and voice/browser-adjacent implementations need retrofit before browser/public use.
- Existing local/operator defaults are not proof of multi-user safety.
- Existing access labels, session IDs, entity scopes, tenant path utilities, and timeline IDs are partial foundations only; they do not replace central authorization-before-read.

Baseline audit documents:

- `docs/WESLR_EXISTING_IMPLEMENTATIONS_MULTI_USER_BOUNDARY_AUDIT_V1.md`
- `docs/WESLR_MULTI_USER_SESSION_TENANT_ISOLATION_BOUNDARY_V1.md`
- `docs/WESLR_MULTI_USER_SESSION_TENANT_ISOLATION_BOUNDARY_REVIEW_V1.md`
- `docs/WESLR_EXISTING_MULTI_USER_SESSION_TENANT_ISOLATION_AUDIT_V1.md`

## 3. Unsafe Wiring Risks To Carry Forward

The following risks must remain blocking conditions for public/browser runtime and response-facing authority design:

1. Global `.weslr` defaults for profile, channel identity, entity memory, fact stores, evidence stores, project registries, timelines, daemon state, eval output, and logs.
2. `tl_default` as shared voice/timeline state.
3. Query-string `user_id` as identity authority.
4. Session-only artifact registry and active artifact pointers.
5. Global artifact files under `continuity/artifacts/` without required owner metadata.
6. Unscoped caches, logs, traces, queues, hints, daemon state, process globals, in-memory bootstrap stores, command sessions, and provider/config caches.
7. Public use of timeline/context readers with default users, default timeline roots, or operator-local state.
8. Final/candidate response formation over unscoped memory/evidence/context/uploads/artifacts.
9. Locale/language preference leakage across users or sessions.
10. Background work that carries only a job ID, session ID, or tenant default without account/session/conversation/workspace scope.

## 4. Retrofit Sequence

Each future lane must be separately approved, implemented, reviewed, and validated. No lane below implies runtime wiring or public release.

### Stage 1 — Namespace Schema Helper

Future lanes:

1. `DESIGN_MULTI_USER_NAMESPACE_SCHEMA_HELPER_V1`
2. `IMPLEMENT_MULTI_USER_NAMESPACE_SCHEMA_HELPER_V1`
3. `REVIEW_MULTI_USER_NAMESPACE_SCHEMA_HELPER_IMPLEMENTATION_V1`

Expected outcome:

- A canonical `namespace_v1` shape with required fields and nullable-field denial rules.
- Required identifiers: `tenant_id`, `account_id`, `user_id`, `guest_id`, `session_id`, `conversation_id`, `workspace_id`, `project_id`, `artifact_id`, `upload_id`, `memory_scope_id`, `locale`, and `language`.
- Stateless/public operations explicitly separated from private state access.
- Tests proving invalid/missing namespace fields block private-state access metadata.

Boundary:

- No memory reads.
- No artifact reads.
- No browser runtime.
- No `chat_responder.py` changes.

### Stage 2 — Central Read Authorization Helper

Future lanes:

1. `DESIGN_CENTRAL_READ_AUTHORIZATION_HELPER_V1`
2. `IMPLEMENT_CENTRAL_READ_AUTHORIZATION_HELPER_V1`
3. `REVIEW_CENTRAL_READ_AUTHORIZATION_HELPER_IMPLEMENTATION_V1`

Expected outcome:

- A central authorization-before-read helper that receives `namespace_v1`, resource kind, resource owner metadata, action, and access policy.
- Deny-by-default behavior for missing tenant/account/guest/session/conversation/workspace/resource scope.
- Explicit distinction between authenticated account, mapped user, guest identity, role, workspace membership, and operator-only governance.
- Tests proving query-string `user_id`, display names, profile claims, channel IDs, and session IDs alone do not authorize reads.

Boundary:

- Does not implement auth provider.
- Does not implement account database.
- Does not wire runtime.

### Stage 3 — Scoped Memory / Context Read Adapter

Future lanes:

1. `DESIGN_SCOPED_MEMORY_CONTEXT_READ_ADAPTER_V1`
2. `IMPLEMENT_SCOPED_MEMORY_CONTEXT_READ_ADAPTER_V1`
3. `REVIEW_SCOPED_MEMORY_CONTEXT_READ_ADAPTER_IMPLEMENTATION_V1`

Expected outcome:

- Adapter layer for entity memory, user profile, channel identity, timelines, conversation context, continuity snapshots, project registry, facts, documents, and evidence packets.
- All reads require `namespace_v1` and central read authorization.
- Existing local/operator defaults remain allowed only under explicit local/operator mode, never public/browser mode.
- Tests proving tenant A/user A/conversation A cannot read tenant B/user B/conversation B state.

Boundary:

- No public runtime.
- No response formation wiring.
- No broad source rewrite; exact modules only per implementation lane.

### Stage 4 — Scoped Artifact / Upload Registry

Future lanes:

1. `DESIGN_SCOPED_ARTIFACT_UPLOAD_REGISTRY_V1`
2. `IMPLEMENT_SCOPED_ARTIFACT_UPLOAD_REGISTRY_V1`
3. `REVIEW_SCOPED_ARTIFACT_UPLOAD_REGISTRY_IMPLEMENTATION_V1`

Expected outcome:

- Artifact and upload records include owner metadata: tenant, account/user or guest, session, conversation, workspace/project, access level, retention policy, provenance, and deletion/export state.
- `artifact_id` alone cannot retrieve material.
- Active artifact pointers are keyed by tenant/account-or-guest/session/conversation/workspace, not session alone.
- Upload-derived text, embeddings, summaries, facts, evidence packets, and artifacts inherit upload owner scope.
- Tests proving “this” cannot resolve across users, sessions, tenants, conversations, or unauthorized workspaces.

Boundary:

- No public upload enablement.
- No browser UI changes.
- No final answer use of uploaded material.

### Stage 5 — Cache / Log / Trace Scoping

Future lanes:

1. `DESIGN_CACHE_LOG_TRACE_SCOPING_V1`
2. `IMPLEMENT_CACHE_LOG_TRACE_SCOPING_V1`
3. `REVIEW_CACHE_LOG_TRACE_SCOPING_IMPLEMENTATION_V1`

Expected outcome:

- Every cache, queue, hint store, daemon state, process-global store, eval output, transcript log, trace, and background output has namespace scope or is explicitly local/operator-only.
- Private logs are redacted or owner-scoped before storage.
- Background jobs carry full namespace context and cannot publish cross-user output.
- Tests proving unscoped caches/logs cannot be read in public/browser mode.

Boundary:

- No daemon public activation.
- No provider/model/search/advisor calls.
- No runtime wiring.

### Stage 6 — Async-Safe Request Context

Future lanes:

1. `DESIGN_ASYNC_SAFE_REQUEST_CONTEXT_V1`
2. `IMPLEMENT_ASYNC_SAFE_REQUEST_CONTEXT_V1`
3. `REVIEW_ASYNC_SAFE_REQUEST_CONTEXT_IMPLEMENTATION_V1`

Expected outcome:

- Explicit request context or `contextvars`-based context for async workloads.
- Thread-local tenant context is no longer treated as sufficient for browser/public runtime.
- Entry/exit cleanup rules prevent context bleed across requests.
- JSON/JSONL write-lock discipline and transaction expectations are documented or implemented per store.
- Tests proving concurrent requests cannot share namespace or active pointers.

Boundary:

- No public runtime enablement.
- No WebSocket or chat behavior changes unless separately authorized.

### Stage 7 — Leakage Negative Tests

Future lanes:

1. `DESIGN_MULTI_USER_LEAKAGE_NEGATIVE_TESTS_V1`
2. `IMPLEMENT_MULTI_USER_LEAKAGE_NEGATIVE_TESTS_V1`
3. `REVIEW_MULTI_USER_LEAKAGE_NEGATIVE_TESTS_V1`

Expected outcome:

- Negative tests for memory, profiles, facts, documents, evidence packets, projects, timelines, continuity, artifacts, uploads, active pointers, caches, queues, logs, traces, daemons, and candidate-response inputs.
- Tests explicitly cover tenant A versus tenant B, user A versus user B, conversation A versus conversation B, guest versus authenticated user, and workspace A versus workspace B.

Boundary:

- Tests do not authorize public runtime.
- Tests do not call providers/models/search/advisors.

### Stage 8 — Guest / Session Boundary

Future lanes:

1. `DESIGN_GUEST_SESSION_BOUNDARY_V1`
2. `IMPLEMENT_GUEST_SESSION_BOUNDARY_V1`
3. `REVIEW_GUEST_SESSION_BOUNDARY_IMPLEMENTATION_V1`

Expected outcome:

- Explicit guest IDs and guest namespace rules.
- Isolated guest tenant/session/conversation state.
- Expiry, deletion, and no-promotion-without-consent rules.
- Guest material cannot become authenticated memory without account creation and explicit consent.

Boundary:

- No account/auth implementation unless that lane explicitly allows it.
- No public browser activation.

### Stage 9 — Account / Auth Boundary

Future lanes:

1. `DESIGN_ACCOUNT_AUTH_BOUNDARY_V1`
2. `IMPLEMENT_ACCOUNT_AUTH_BOUNDARY_V1`
3. `REVIEW_ACCOUNT_AUTH_BOUNDARY_IMPLEMENTATION_V1`

Expected outcome:

- Authenticated account/session binding.
- Account-to-user mapping rules.
- Workspace/project membership rules.
- Role/operator authority separation.
- Explicit rejection of query-string identity, display-name identity, profile-claim identity, channel-only identity, and session-only identity as read authority.

Boundary:

- Auth implementation does not automatically enable public response formation.
- Public runtime requires later reviewed integration lane.

### Stage 10 — Deletion / Export / Retention Controls

Future lanes:

1. `DESIGN_DELETION_EXPORT_RETENTION_CONTROLS_V1`
2. `IMPLEMENT_DELETION_EXPORT_RETENTION_CONTROLS_V1`
3. `REVIEW_DELETION_EXPORT_RETENTION_CONTROLS_IMPLEMENTATION_V1`

Expected outcome:

- Export/delete/tombstone/expiry controls for profiles, memories, uploads, artifacts, facts, documents, evidence, timelines, logs, traces, caches, and background outputs.
- Retention policy is enforced, not just stored as metadata.
- Deletion propagates to derived artifacts/facts/evidence where required.

Boundary:

- No legal/compliance certification claims.
- No public release claim.

## 5. Module Impact Table

| Category / path family | Future treatment | Label |
|---|---|---|
| Metadata-only helpers | Preserve as helper-only; no owner namespace required unless connected to real user material | `no_change_if_helper_only` |
| Cognitive Gym helpers | Keep metadata-only; add namespace only at runtime caller/persistence boundary | `no_change_if_helper_only` |
| CALIBRATION_LEDGER helpers | Keep metadata-only; require scope before user-specific calibration persistence or learning | `no_change_if_helper_only` |
| Reasoning substrate docs/helpers | Carry namespace and read-authorization assumptions as prerequisites | `must_require_scope_before_runtime` |
| `weslr/tenant_context.py` | Replace optional/legacy fallback for public mode with mandatory namespace/request context rules | `must_require_scope_before_runtime` |
| Memory/context/profile modules | Route all reads through scoped adapter and central read authorization | `must_require_authorization_before_read` |
| Timeline/default-reader paths | Block `tl_default`, default users, and operator timeline roots in public mode | `blocked_for_public_browser_until_retrofitted` |
| Artifact/session registry | Add owner metadata and replace session-only active pointers | `must_require_authorization_before_read` |
| Upload/material handling | Add upload owner scope and derived-material inheritance rules before parsing/indexing | `must_require_authorization_before_read` |
| Voice/browser/runtime-adjacent paths | Stay blocked for public browser until auth, request context, timeline, logs, and guest/session boundaries are reviewed | `blocked_for_public_browser_until_retrofitted` |
| Ranked/response formation shadow helpers | Remain safe as synthetic/shadow helpers; reject candidates with missing source scope if later connected | `must_require_scope_before_runtime` |
| Command caches / process globals / daemons | Scope or mark local/operator-only; add negative leakage tests | `needs_negative_leakage_tests` |
| `weslr/security.py` and token/session helpers | Follow-up audit needed before treating as account/auth boundary | `inconclusive_requires_followup_audit` |

## 6. Before Response-Facing Authority Checkpoint

Response-facing authority design may safely assume only the following:

- No public/browser runtime permission exists.
- No unscoped memory/context/evidence/artifact/upload/log/cache read is authorized.
- Candidate response formation must remain blocked from unscoped reads.
- Authority checkpoint must reject candidates whose source scope is missing, unauthenticated, unverified, stale, private-for-wrong-recipient, or unauthorized.
- Metadata-only helpers remain safe only while they do not read private runtime state or produce final user-facing text.
- Any response-facing candidate that depends on memory, context, evidence, uploaded material, artifacts, or timeline state must include source scope and read-authorization status as metadata.
- Missing namespace is not a soft warning; it is a blocking condition for private-state influence.

The response-facing authority/claim checkpoint can therefore proceed only as a design lane that carries retrofit constraints forward. It must not claim that the retrofit is implemented.

## 7. Safe Implementation Boundaries For Future Lanes

Future implementation lanes must:

- touch only exact modules named in that lane
- include namespace/read-authorization tests
- include leakage-negative tests
- avoid broad runtime wiring
- keep `weslr/chat_responder.py` untouched unless a later explicitly authorized runtime lane names it
- never use query-string `user_id` as identity authority
- never use global `.weslr` as public shared state
- never treat `session_id`, `artifact_id`, `timeline_id`, display name, profile claim, or channel ID alone as authorization
- preserve local/operator compatibility behind explicit local/operator mode, not public/browser mode
- keep provider/model/search/advisor integrations out unless explicitly authorized by the lane
- keep public/browser runtime disabled until all required boundary reviews pass

## 8. Direction Check

Direction check: `A — after this plan review/context alignment, continue response-facing authority checkpoint design carrying retrofit constraints`

Rationale: this plan clearly blocks unscoped response authority. The response-facing authority checkpoint can remain abstract but useful if it treats namespace and read authorization as mandatory upstream preconditions and rejects candidates whose source scope is missing. Namespace schema implementation is still required before runtime use, but it is not required before a design-only authority checkpoint.

Recommended next lane:

`REVIEW_MULTI_USER_RETROFIT_PLAN_BEFORE_RESPONSE_FACING_AUTHORITY_CHECKPOINT_V1`

After review and context alignment, continue to:

`DESIGN_RESPONSE_FACING_AUTHORITY_CLAIM_CHECKPOINT_V1`

## 9. Denied Authority Fields

- grants_runtime_authority: false
- permits_public_browser_runtime: false
- permits_unscoped_memory_reads: false
- permits_unscoped_context_reads: false
- permits_unscoped_evidence_reads: false
- permits_unscoped_artifact_reads: false
- permits_unscoped_upload_reads: false
- permits_query_string_user_id_authority: false
- permits_tl_default_public_state: false
- permits_global_dot_weslr_public_state: false
- permits_candidate_response_runtime_wiring: false
- permits_final_answer_generation: false
- permits_provider_calls: false
- permits_model_calls: false
- permits_search_calls: false
- permits_advisor_calls: false
- permits_chat_responder_changes: false
- permits_public_release_claims: false

## 10. Safety Check

This plan creates no implementation, changes no runtime behavior, changes no chat/user-facing behavior, reads/writes no live `.weslr` runtime state, calls no providers/models/search/advisors, does not edit `weslr/chat_responder.py`, creates no final answer, and grants no authority.
