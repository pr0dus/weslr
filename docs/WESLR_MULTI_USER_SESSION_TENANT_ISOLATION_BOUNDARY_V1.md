# WESLR Multi-User Session Tenant Isolation Boundary V1

## Status

- Design label: `DESIGN_MULTI_USER_SESSION_TENANT_ISOLATION_BOUNDARY_V1`
- Document path: `docs/WESLR_MULTI_USER_SESSION_TENANT_ISOLATION_BOUNDARY_V1.md`
- Lane status: design-only
- Scope: public/browser/international multi-user isolation boundary before any browser/public runtime, response-facing authority expansion, or safe final response assembly
- Runtime status: no runtime wiring
- Chat status: no chat/user-facing behavior changes
- Implementation status: no helpers, source files, tests, runners, migrations, database work, auth implementation, browser implementation, provider/model/search/advisor integrations, or `.weslr` IO implemented
- Execution status: no browser request handling, no public runtime, no account/session enforcement, no memory/context reads, no candidate response execution, no final answer assembly
- Claim status: no product-readiness, public-release, security-compliance, privacy-compliance, benchmark, certification, or official claims
- Authority status: no authority grants

This document defines the design-only boundary that must protect WESLR from cross-user, cross-session, cross-tenant, cross-conversation, cross-artifact, cross-upload, cross-cache, and cross-log leakage before any public/browser/international runtime is allowed. It creates no implementation, modifies no runtime path, executes no helper, calls no provider/model/search/advisor, reads/writes no `.weslr` state, changes no `weslr/chat_responder.py`, creates no final answer, and grants no authority.

## 1. Purpose

This boundary protects WESLR from cross-user/context/memory leakage when WESLR eventually serves many public browser users, guest users, international users, teams, institutions, and workspaces at once.

The purpose is to define what must be true before public/browser runtime may use WESLR state:

- every memory/context/evidence/artifact/upload/log/cache access has an explicit owner/session/tenant scope
- user, session, conversation, tenant, workspace, project, artifact, upload, memory, locale, and language context are separated before candidate response formation
- public/browser requests cannot inherit local operator `.weslr` state, repo-private context, `tl_default`, process-global hints, or session-only artifact pointers
- candidate response formation knows whose context/memory/evidence it is using before ranking, rejecting, or composing anything
- guest sessions are isolated and expire safely
- background work, async tasks, caches, queues, logs, traces, and uploads cannot leak one user's material into another user's response
- central authorization exists before any read, not only before writes
- data export, deletion, retention, privacy, language, and audit boundaries are explicit before public/international users arrive

## 2. Non-Goals

This design does not:

- implement browser runtime
- implement authentication
- implement accounts
- implement database migration
- implement tenant storage
- implement session middleware
- implement request context helpers
- implement authorization guards
- implement scoped memory/context readers
- implement upload/artifact stores
- implement cache or queue changes
- implement deletion/export controls
- implement leakage tests
- implement rate limits or load handling
- implement or modify `weslr/chat_responder.py`
- wire candidate response formation to runtime
- generate final answers, reply text, answer drafts, preview output, or user-facing output
- permit public/browser runtime
- permit `.weslr` public state use
- call providers/models/search/advisors
- grant any answer, runtime, provider, public release, or security authority

It is a boundary and sequencing document only.

## 3. Current Audit Baseline

This design follows:

- `docs/WESLR_EXISTING_MULTI_USER_SESSION_TENANT_ISOLATION_AUDIT_V1.md`

The audit judgment was:

`existing_multi_user_isolation_partial_needs_boundary_design_before_public_runtime`

The audit found partial foundations:

- `weslr/tenant_context.py` provides tenant path utilities and thread-local tenant context.
- `weslr/bootstrap.py` provides bootstrap/timeline identity foundations.
- `weslr/channel_identity.py` and `weslr/user_profile.py` separate profile claims from verification evidence.
- `weslr/entity_memory.py` and `weslr/memory_capture.py` provide entity-scoped memory metadata and conservative capture patterns.
- `weslr/artifact_store.py` provides persistent artifacts and session-keyed active artifact registry.
- `weslr/voice_gateway.py` provides browser/voice WebSocket routing to timelines.
- Some document/fact/frontier/evidence stores use tenant-aware path resolution.
- Governance docs exist for account/tenant/data ownership, public surface readiness, repo hygiene, and timeline continuity.

The audit also found WESLR is not ready for public/international multi-user runtime because it is missing:

- mandatory authenticated browser account boundary
- universal tenant/user/session namespace
- central read authorization
- guest isolation
- public upload isolation
- async-safe request scoping
- deletion/export controls
- leakage negative tests
- complete browser/public privacy, retention, language, rate/load, and audit boundaries

The audit found cross-user memory/context leakage risks. Therefore this boundary recommends direction C.

## 4. Required Identity Namespace Model

Public/browser WESLR must not treat identity as a single string. Every request and every state access must carry a scoped namespace model.

### 4.1 Required identifiers

#### `tenant_id`

The top-level data/control boundary.

Rules:

- Required for every public/browser request.
- May identify an individual tenant, team tenant, company tenant, institution tenant, hosted tenant, or self-hosted tenant.
- Must never silently default to local operator `.weslr` or repository global state in public runtime.
- A public guest tenant may exist, but it must be explicit, temporary, isolated, and retention-limited.

#### `account_id` / `user_id`

Label: account_id / user_id

The authenticated account or verified user identity.

Rules:

- Required for authenticated users.
- Must be bound to account/session authentication, not taken from untrusted text or query-string claims.
- `user_id` may represent the human/person timeline; `account_id` represents access identity.
- If both exist, access checks must use the authenticated account and mapped user identity.

#### `session_id`

The active browser/API session.

Rules:

- Required for browser/public requests.
- Session IDs are request/access continuity keys, not sufficient authorization by themselves.
- Session ID must be bound to `tenant_id` and `account_id` or explicit guest identity.
- Session state must expire and must be clearable.

#### `conversation_id`

The current conversation/thread of dialogue.

Rules:

- Required for any transcript, context-window, candidate-response, or turn-continuity material.
- Conversation state must be scoped to tenant/account/session.
- A conversation cannot read another conversation's transcript unless an authorized cross-conversation continuity rule explicitly allows it.

#### `workspace_id` / `project_id`

Label: workspace_id / project_id

The working context inside a tenant.

Rules:

- Required whenever project/workspace memory, uploads, artifacts, evidence, or repo/project context is accessed.
- A tenant can contain many workspaces/projects.
- Workspace membership must be checked before workspace memory/context is read.
- Project IDs must not be inferred from stale memory when access would be expanded.

#### `artifact_id`

The identifier for generated, uploaded, revised, inspected, or referenced artifacts.

Rules:

- Every artifact must have owner metadata: tenant, account/user or role, workspace/project, conversation/session origin, access level, retention policy, and provenance.
- `artifact_id` alone is not sufficient for retrieval.
- Artifact reads require owner-scope authorization.

#### `upload_id`

The identifier for uploaded files/material.

Rules:

- Every upload must have tenant/account/session/conversation/workspace ownership before parsing, indexing, summarizing, or using in candidate formation.
- Uploads from guests must be isolated, expiry-bound, and deleteable.
- Upload content must not become shared memory unless explicit authorization and policy allow it.

#### `memory_scope_id`

The identifier for a memory scope such as person, project, team, institution, tenant, or operator-only governance.

Rules:

- Memory scope must include both semantic scope and access owner scope.
- Example: `memory_scope_id=person:user_123` is insufficient without tenant/account authorization and access-level checks.
- Memory can be relevance input only after scope and authorization are resolved.

#### `locale` / `language` context

Label: locale / language context

The language, locale, region, and formatting context for a user/session/conversation.

Rules:

- Locale/language must be request/session metadata, not inferred as a permanent user truth without confirmation.
- Candidate response formation must know the user's current language context when choosing response style, clarification behavior, date/number formatting, and public/legal/privacy copy.
- Locale/language preferences must be scoped to account/user/tenant and must not leak across users.

### 4.2 Mandatory namespace tuple

Every public/browser state access must conceptually include:

```text
namespace_v1:
  tenant_id: required
  account_id: required for authenticated user, null only for explicit guest scope
  user_id: required when mapped/verified, null only for explicit guest scope
  guest_id: required when account_id/user_id are null
  session_id: required
  conversation_id: required for conversation/context/candidate-response state
  workspace_id: required for workspace/project material
  project_id: required when project-specific state is used
  artifact_id: required for artifact operations
  upload_id: required for upload/material operations
  memory_scope_id: required for memory operations
  locale: required for public/browser rendering defaults
  language: required for public/browser response language defaults
```

Nullable fields must be explicitly justified. Absence of a namespace field must block state access unless the operation is truly stateless and public.

### 4.3 Core rule

No memory, context, artifact, upload, cache, trace, log, or candidate response input may be read without explicit owner/session/tenant scope.

This applies to:

- long-term memory
- recent conversation context
- transcript windows
- candidate response inputs
- artifacts
- uploaded files/material
- extracted facts
- evidence packets
- repo/project context
- cache entries
- background task outputs
- queues
- logs and traces
- telemetry summaries
- model/provider/advisor results in any future authorized lane

## 5. Isolation Rules

### 5.1 Per-user memory separation

Rules:

- Personal memory must be keyed by tenant and account/user identity.
- Person-scoped memory cannot be read using only a display name, text claim, query-string `user_id`, session ID, or conversation ID.
- Explicit memory and inferred memory must remain separated.
- Memory access must check access level before the content influences candidate formation.
- Private memory must not be used in public/shared workspace responses unless policy and user authorization permit it.

### 5.2 Per-session context separation

Rules:

- Session context is transient and belongs to `(tenant_id, account_id/user_id or guest_id, session_id)`.
- Session context cannot be used as durable identity proof.
- Session state must expire and must be clearable.
- Session resumption must re-check account/session binding before loading context.
- A session-only registry cannot retrieve artifacts, memory, uploads, or transcripts without owner scope.

### 5.3 Per-conversation transcript separation

Rules:

- Transcripts must be keyed by conversation and owner namespace.
- Conversation A cannot supply hidden context to Conversation B unless an explicit authorized continuity rule selects a scoped summary or artifact.
- Raw transcript reuse must be minimized; summaries need provenance, owner scope, and privacy labels.
- Quoted/untrusted text inside a conversation must remain labeled as untrusted content.

### 5.4 Per-tenant/workspace separation

Rules:

- Tenant is the top-level state boundary.
- Workspace/project is the working boundary inside tenant.
- Cross-tenant reads are denied by default.
- Cross-workspace reads are denied unless role/membership/policy explicitly allows them.
- Tenant-local defaults must not fall back to repository-global state in public runtime.

### 5.5 Guest-user isolation

Rules:

- Guest users receive explicit `guest_id`, `tenant_id`, `session_id`, and `conversation_id` scoped to the guest runtime.
- Guest state must be isolated from authenticated user memory and from other guests.
- Guest uploads and artifacts must have expiry and deletion semantics.
- Guest state cannot be promoted to persistent user memory without explicit account creation and consent.

### 5.6 Upload/material isolation

Rules:

- Uploads must be assigned `upload_id` and owner namespace before parsing.
- Extracted text, embeddings, summaries, facts, and evidence packets inherit upload owner scope.
- Uploads cannot become public evidence or shared workspace memory without explicit policy and consent.
- Upload deletion must delete or tombstone derived indexes/summaries where required by policy.

### 5.7 Artifact isolation

Rules:

- Artifacts require owner namespace metadata at creation.
- `artifact_id` alone cannot authorize retrieval.
- Active artifact pointers must be keyed by tenant/account/session/conversation/workspace, not only by session ID.
- Reference resolution for “this” must never select another user's artifact, a different tenant's artifact, or a workspace artifact outside the user's membership.

### 5.8 Repo/project context separation

Rules:

- Local repo/operator context is not public-user context.
- Public/browser users cannot inherit private repo docs, local `.weslr` state, operator memory, OpenClaw workspace files, or source-level implementation details unless an explicit public-safe surface exposes sanitized content.
- Project context used for a public user must be tied to an authorized workspace/project.

### 5.9 Evidence/provenance separation

Rules:

- Evidence inherits owner and source scope.
- User-provided evidence remains user-provided; it is not global truth.
- Public/external evidence must be labeled separately from private uploads, repo context, memory, and model assumptions.
- Candidate response formation must know which evidence belongs to which tenant/user/session/conversation before ranking.

### 5.10 Browser request scoping

Rules:

- Every browser/API/WebSocket request must create or receive a scoped request context before any stateful read.
- Request context must not be derived from untrusted text or query parameters alone.
- Query-string `user_id` may be routing metadata only after authentication has already established the account/session binding.
- Browser request context must be available to downstream helpers explicitly, not implicitly through unsafe globals.

### 5.11 Cache namespace scoping

Rules:

- Every cache key touching user/context/evidence/material must include tenant/account-or-guest/session/conversation/workspace as appropriate.
- Cache reads without tenant/user/session key are denied for public runtime.
- Public/stateless caches must be declared as public and must not include private content.
- Cache eviction must respect retention/deletion policy.

### 5.12 Async/concurrent request safety

Rules:

- Async public runtime must not rely on plain thread-local tenant context alone.
- Future runtime should use explicit request context passing or async-safe context propagation such as `contextvars`.
- Context must be set before state access and cleared after request/task completion.
- JSON/JSONL stores, queues, and index writes need write-lock or transactional discipline before many-user use.

### 5.13 Background task isolation

Rules:

- Background tasks must carry explicit namespace context.
- A background job cannot read memory/artifacts/uploads/logs using only job ID.
- Task outputs must be scoped to the originating tenant/account/workspace/conversation or explicitly anonymized aggregate policy.
- Failure logs must avoid private raw content and must preserve owner scope for audit.

## 6. Leakage Risks To Block

The following are explicitly blocked for public/browser runtime:

1. Global `.weslr` defaults for public runtime.
2. `tl_default` as shared user state.
3. Query-string `user_id` as sufficient identity.
4. Global artifacts without owner scope.
5. Mutable process globals as shared user context.
6. Optional namespace keys for memory/context/artifact/upload/cache/log reads.
7. Incomplete read-time authorization.
8. Session-only artifact registry without user/account/tenant owner.
9. Cache reads without tenant/user/session key.
10. Logs/traces containing private raw content without redaction, owner scope, and retention policy.
11. Profile files or channel bindings loaded from one global user path in public runtime.
12. Entity memory reads that rely only on entity ID and access metadata without account/tenant authorization.
13. Upload-derived facts or summaries used outside the upload owner's scope.
14. Conversation history reused across users without explicit owner continuity and authorization.
15. Background task results delivered or cached without owner namespace.
16. Locale/language preferences from one user applied to another user.
17. Operator/admin/private repo state included in public user candidate response inputs.
18. Cross-user learning from private data without explicit aggregated anonymized policy.

## 7. Public / Browser / International Readiness Requirements

Before public/browser/international runtime, WESLR must have the following reviewed and tested boundaries.

### 7.1 Authenticated account boundary

Required:

- account/session authentication before persistent user memory/context access
- verified mapping from account to user/person timeline
- role and tenant membership lookup
- denial behavior for unauthenticated requests
- separation of profile claims from verified account access

### 7.2 Guest session boundary

Required:

- explicit guest ID
- guest tenant/session/conversation namespace
- no access to authenticated memory
- no access to other guest state
- upload/artifact expiry
- deletion on expiry or user request according to policy
- no promotion to persistent memory without explicit consent

### 7.3 Central authorization check before all reads

Required:

- read authorization for memory, context, artifact, upload, cache, log, trace, evidence, and background task output
- authorization before candidate response formation receives inputs
- deny-by-default when namespace or role is missing
- audit metadata for denied reads without private leakage

### 7.4 Per-user memory/context namespace

Required:

- personal memory namespace
- workspace/project memory namespace
- institution/company tenant memory namespace
- operator-only governance memory namespace
- explicit rules for memory sharing and exclusion
- stale/inferred/private memory labels preserved

### 7.5 Upload ownership and deletion

Required:

- upload owner metadata
- derived content/index ownership
- upload deletion/tombstone behavior
- workspace sharing rules
- sensitive-content handling
- public-demo file upload disabled unless this boundary is implemented

### 7.6 User data export/delete controls

Required:

- export of user/account personal data
- export of tenant/workspace data by authorized owner/admin
- delete or tombstone personal data according to policy
- handle derived summaries, indexes, caches, and logs
- distinguish personal, project, institution, operator-only, and legal-retention data

### 7.7 Retention policy

Required:

- retention labels for memory, transcript, upload, artifact, log, trace, cache, and background task data
- guest retention defaults
- authenticated user retention settings or terms
- workspace/tenant retention policy
- deletion/expiry execution model before public runtime

### 7.8 Locale/language handling

Required:

- request/session locale and language context
- account-level language preferences when authenticated
- guest language handling without permanent inference unless consented
- date/time/number formatting discipline
- privacy/legal copy localizability
- no cross-user preference leakage

### 7.9 Rate/load/concurrency boundaries

Required:

- per-account/guest/session/tenant rate limits
- upload limits
- background task limits
- queue isolation
- cache isolation
- concurrent write safety
- failure isolation so one tenant/user cannot corrupt another's state

### 7.10 Audit logging without private leakage

Required:

- audit logs contain scoped metadata, not private raw content by default
- redaction rules for messages, uploads, artifacts, memory, provider outputs, and errors
- owner scope on log entries
- retention and deletion policy for logs
- operator/admin access boundary for logs

### 7.11 Leakage negative tests

Required before public/browser use:

- tenant A cannot read tenant B memory/context/artifacts/uploads/logs
- user A cannot read user B private memory
- guest A cannot read guest B state
- session A cannot retrieve session B active artifact without user/tenant authorization
- conversation A cannot influence conversation B unless authorized continuity is explicitly selected
- cache key misses cannot fall back to global private state
- `tl_default` is not used for public users
- query-string `user_id` alone does not authorize access
- unscoped `.weslr` path access is blocked in public runtime
- logs/traces do not include private raw content by default

### 7.12 Admin/operator access boundary

Required:

- operator, admin, owner, support, and member roles separated
- support/operator access is explicit, temporary where appropriate, and audited
- admin is not automatically operator
- operator is not automatically data owner
- public users cannot see operator panels or internal governance memory

### 7.13 No cross-user learning without explicit aggregated anonymized policy

Required:

- private user data cannot train, tune, cache, summarize, or bias other users' responses by default
- aggregated learning requires explicit policy, anonymization, privacy review, opt-out/consent where required, and leakage tests
- individual user memory cannot become public product memory silently

## 8. Relationship To Cognition Substrate

This boundary sits underneath the response/cognition substrate. It is a prerequisite for any response-facing layer in public/browser runtime.

### 8.1 Relationship to context/memory trust and evidence boundary

The context/memory trust and evidence boundary decides how sources are labeled, trusted, marked stale/conflicted/private, and preserved as evidence metadata.

This isolation boundary decides whether those sources may be read at all for the current tenant/account/session/conversation/workspace.

Order:

1. Resolve request namespace and authorization.
2. Read only scoped/authorized context, memory, uploads, artifacts, and evidence.
3. Label trust, provenance, freshness, privacy, and conflict metadata.
4. Pass bounded metadata forward.

### 8.2 Relationship to candidate response formation substrate

Candidate response formation must know whose context/memory/evidence it is using before ranking or composing anything.

Candidate records must include owner-scope metadata for:

- memory used
- memory excluded
- evidence used
- uploads/material used
- artifact references
- conversation history
- locale/language context
- authority constraints

Candidate formation cannot rank a direct-answer candidate over a clarification/boundary/evidence-needed candidate if owner scope is missing or authorization is unresolved.

### 8.3 Relationship to response-facing authority/claim checkpoint

The response-facing authority/claim checkpoint should reject any candidate that:

- lacks owner/session/tenant scope
- uses unscoped memory/context/artifacts/uploads
- uses private data in the wrong channel
- implies public/final/official certainty without allowed evidence
- crosses tenant/user/session/conversation boundaries
- depends on `tl_default`, global `.weslr`, query-string identity, or unscoped caches

### 8.4 Relationship to safe final response assembly

Safe final response assembly may only assemble text from candidates whose scoped inputs have passed:

1. namespace resolution
2. read authorization
3. context/memory/evidence trust labeling
4. candidate boundary checks
5. response-facing authority/claim checkpoint

Final assembly must never be the first layer that discovers owner scope is missing.

## 9. Safe Future Implementation Shape

This section defines a future sequence only. It does not implement anything.

### Phase 1 — Namespace schema helpers

Future helper lane:

`IMPLEMENT_NAMESPACE_SCHEMA_HELPERS_V1`

Expected scope:

- immutable request namespace record shape
- required/nullable field validation
- guest namespace shape
- tenant/account/session/conversation/workspace/artifact/upload/memory-scope identifiers
- JSON-safe metadata summaries

Blocked:

- no runtime wiring
- no auth implementation
- no database migration
- no `.weslr` public state

### Phase 2 — Authorization guard helpers

Future helper lane:

`IMPLEMENT_AUTHORIZATION_GUARD_HELPERS_V1`

Expected scope:

- deterministic guard records
- deny-by-default decision metadata
- scope mismatch labels
- role/membership decision shape
- redacted denial summaries

Blocked:

- no real account provider
- no browser middleware
- no provider/model/search/advisor calls

### Phase 3 — Scoped memory/context read helpers

Future helper lane:

`IMPLEMENT_SCOPED_MEMORY_CONTEXT_READ_HELPERS_V1`

Expected scope:

- safe read interface shape
- owner-scope precondition checks
- private/stale/inferred/conflicted exclusion metadata
- context/memory trust boundary interop

Blocked:

- no runtime chat wiring
- no public memory reads
- no unscoped `.weslr` access

### Phase 4 — Upload/artifact ownership helpers

Future helper lane:

`IMPLEMENT_UPLOAD_ARTIFACT_OWNERSHIP_HELPERS_V1`

Expected scope:

- artifact owner metadata validation
- upload owner metadata validation
- active artifact pointer namespace design
- deletion/tombstone metadata shape
- safe “this” reference preconditions

Blocked:

- no upload runtime
- no artifact store migration without review
- no user-facing behavior

### Phase 5 — Leakage negative tests

Future helper/test lane:

`IMPLEMENT_MULTI_USER_ISOLATION_NEGATIVE_TESTS_V1`

Expected scope:

- tenant A/B read-denial tests
- user A/B private memory tests
- guest A/B isolation tests
- conversation A/B contamination tests
- session-only artifact registry denial tests
- unscoped cache denial tests
- `tl_default` public-runtime block tests
- query-string identity rejection tests
- log redaction tests

Blocked:

- no public runtime claim until tests pass
- no browser integration before tests pass

### Phase 6 — Browser integration only after helper tests pass

Future runtime lane only after prior review:

`DESIGN_PUBLIC_BROWSER_RUNTIME_INTEGRATION_AFTER_ISOLATION_TESTS_V1`

Requirements before any implementation:

- namespace schema helpers reviewed
- authorization guard helpers reviewed
- scoped read helpers reviewed
- upload/artifact owner helpers reviewed
- leakage negative tests passing
- public surface hardening reviewed
- operator/admin boundary reviewed
- data export/delete/retention design reviewed

## 10. Denied Authority Fields

```yaml
grants_runtime_authority: false
permits_public_browser_runtime: false
permits_cross_user_memory: false
permits_unscoped_memory_reads: false
permits_unscoped_artifact_reads: false
permits_provider_calls: false
permits_dot_weslr_public_state: false
permits_final_answer_generation: false
```

Additional denied authority:

```yaml
permits_auth_implementation: false
permits_database_migration: false
permits_browser_implementation: false
permits_chat_responder_changes: false
permits_voice_gateway_changes: false
permits_ui_changes: false
permits_upload_runtime: false
permits_background_task_runtime: false
permits_cache_runtime_changes: false
permits_log_runtime_changes: false
permits_model_calls: false
permits_search_calls: false
permits_advisor_calls: false
permits_scoring_or_judging: false
permits_public_release_claim: false
```

## 11. Direction Check

Options:

A — proceed next with response-facing authority/claim checkpoint design
B — pause/review public-browser architecture direction
C — review this multi-user boundary first, then context alignment, then continue architecture

Recommended direction:

`C — review this multi-user boundary first, then context alignment, then continue architecture`

Rationale:

The audit found cross-user memory/context leakage risk. Candidate response formation, response-facing authority, and safe final assembly all depend on scoped, authorized inputs. Therefore the multi-user boundary should be reviewed first, then OCC/WESLR context should be aligned around it, and only then should architecture continue toward response-facing authority/claim checkpoint design or public/browser runtime design.

## 12. Review Checklist For This Boundary

A future review should confirm:

- the namespace model covers tenant/account/user/session/conversation/workspace/project/artifact/upload/memory/locale/language
- nullable fields are deny-by-default
- global `.weslr`, `tl_default`, query-string identity, session-only artifact lookup, unscoped caches, raw private logs, and mutable process-global context are blocked for public runtime
- candidate response formation is explicitly downstream of namespace and authorization checks
- public/browser readiness requirements include auth, guest isolation, central read authorization, upload ownership/deletion, export/delete controls, retention, locale/language, rate/load/concurrency, audit logging, leakage tests, admin/operator boundary, and no cross-user learning without policy
- future implementation sequence begins with helper schemas/guards/tests before browser integration
- denied authority fields remain false

## 13. Safety Check

This design does not implement behavior, does not edit `weslr/chat_responder.py`, does not inspect or modify live `.weslr` runtime state, does not call providers/models/search/advisors, does not wire runtime, does not add helpers, does not create tests, does not modify browser/voice/UI files, and does not change chat/user-facing behavior.
