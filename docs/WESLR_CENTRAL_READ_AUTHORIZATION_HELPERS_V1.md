# WESLR Central Read Authorization Helpers V1

## Status

- Lane: `DESIGN_CENTRAL_READ_AUTHORIZATION_HELPERS_V1`
- Lane type: design-only
- Document path: `docs/WESLR_CENTRAL_READ_AUTHORIZATION_HELPERS_V1.md`
- Runtime changes: none
- Implementation changes: none
- Source/test/helper changes: none
- Chat/browser/voice/UI changes: none
- `weslr/chat_responder.py`: untouched
- Future helper target: design target only, not created in this lane
- Direction check: `A — review/context-align this design, then implement narrow metadata-only central read authorization helpers`

This document designs future central read authorization helpers. The future helpers decide whether a scoped read is allowed before any memory, context, evidence, artifact, upload, cache, log, or trace read can happen. This design builds on the implemented namespace/source-scope helpers and grants no runtime, read, chat, browser, provider, database, authentication, or final-answer authority.

## 1. Purpose And Non-Goals

### 1.1 Purpose

The purpose is to define a metadata-only central authorization-before-read layer for future WESLR private/shared state use.

The future helper family should:

- consume validated source-scope metadata from the namespace/source-scope helpers
- compare requester scope and target scope before any private/shared state is touched
- classify whether the requested read is allowed only for metadata/internal shadow use or denied
- fail closed for missing scope, invalid scope, cross-user/cross-tenant access, unsafe public/browser use, unknown policy, or authority escalation
- return JSON-safe authorization decision metadata only
- provide a single decision point that future scoped adapters must enforce before reads

### 1.2 Non-Goals

This design does not authorize or create:

- implementation
- helper/source/test files
- runtime/chat/browser/public authority
- authentication implementation
- account/session/browser middleware
- database migration or database access
- memory/context/evidence/artifact/upload/cache/log/trace reads
- `.weslr` public runtime state
- provider/model/search/advisor calls
- candidate execution
- final-answer generation
- safe final response assembly
- scoring, judging, benchmark, certification, official, public-readiness, product-readiness, proof, open-problem, scientific, Turing/IQ/intelligence, or consciousness claims
- changes to `weslr/chat_responder.py`
- TIA/C#/Siemens bridge changes

The design is authorization metadata only. It does not fetch content, inspect files, call services, authenticate users, query databases, generate replies, or wire runtime behavior.

## 2. Relationship To Current Chain

The current chain separates identity/scope, authorization, read adapters, candidate formation, authority checkpoint, and safe assembly.

1. Namespace/source-scope helpers identify and validate scope metadata.
2. Central read authorization decides whether a scoped read is allowed.
3. Scoped adapters later enforce authorization before touching private/shared state.
4. Candidate response formation must not consume unscoped or unauthorized memory, context, evidence, artifact, upload, cache, log, trace, transcript, profile, timeline, daemon, queue, or runtime state.
5. Response-facing authority/claim checkpoint must reject any candidate that relies on unscoped or unauthorized reads.
6. Safe final response assembly shadow work must consume only approved metadata and must not compensate for missing read authorization.

This design follows:

- `docs/WESLR_IMPLEMENTED_REASONING_CHAIN_GAPS_BEFORE_CHAT_WIRING_AUDIT_V1.md`
- `docs/WESLR_NAMESPACE_SCHEMA_AND_SOURCE_SCOPE_HELPERS_V1.md`
- `docs/WESLR_NAMESPACE_SCHEMA_AND_SOURCE_SCOPE_HELPERS_IMPLEMENTATION_REVIEW_V1.md`
- `docs/WESLR_MULTI_USER_SESSION_TENANT_ISOLATION_BOUNDARY_V1.md`
- `docs/WESLR_MULTI_USER_RETROFIT_PLAN_BEFORE_RESPONSE_FACING_AUTHORITY_CHECKPOINT_V1.md`
- `docs/WESLR_RESPONSE_FACING_AUTHORITY_CLAIM_CHECKPOINT_V1.md`
- `docs/WESLR_SAFE_FINAL_RESPONSE_ASSEMBLY_SHADOW_BOUNDARY_V1.md`

Central read authorization is the missing guard between validated source scope and any future scoped adapter. Source-scope validation is not permission.

## 3. Authorization Record Shape

Future authorization decision records should be metadata-only and JSON-safe:

```json
{
  "schema_version": "weslr.central_read_authorization.v1",
  "authorization_id": "read_auth_...",
  "source_scope_summary": {
    "source_scope_id": "scope_...",
    "source_kind": "memory|context|evidence|artifact|upload|cache|log|trace|synthetic_fixture|operator_local",
    "source_owner_kind": "tenant|account|user|guest|session|conversation|workspace|project|artifact|upload|operator_local|synthetic|anonymized_aggregate",
    "validation_status": "valid|invalid|blocked_missing_scope|blocked_unsafe_scope|synthetic_only"
  },
  "requested_read_kind": "memory|context|evidence|artifact|upload|cache|log|trace|transcript|profile|timeline|queue|daemon|background_result|synthetic_fixture",
  "requested_use_context": "candidate_metadata|authority_checkpoint|shadow_validation|safe_assembly_shadow|internal_review|public_browser|runtime_chat|provider_call|final_answer|unknown",
  "requester_scope": {
    "tenant_id": "tenant_...",
    "account_id": "acct_...",
    "user_id": "user_...",
    "guest_id": null,
    "session_id": "sess_...",
    "conversation_id": "conv_...",
    "workspace_id": "workspace_...",
    "project_id": "project_..."
  },
  "target_scope": {
    "tenant_id": "tenant_...",
    "account_id": "acct_...",
    "user_id": "user_...",
    "guest_id": null,
    "session_id": "sess_...",
    "conversation_id": "conv_...",
    "workspace_id": "workspace_...",
    "project_id": "project_...",
    "resource_scope_id": "memory_or_artifact_or_upload_or_cache_or_log_or_trace_scope"
  },
  "owner_scope_match_label": "same_scope|same_tenant_different_user|same_user_different_session|same_user_different_conversation|guest_to_authenticated|authenticated_to_guest|cross_user|cross_tenant|operator_local|synthetic_only|unknown",
  "privacy_label": "public|user_private|tenant_private|operator_private|raw_private|redacted|synthetic|unknown",
  "retention_label": "ephemeral|session|conversation|project|account|tenant|operator_local|unknown",
  "provenance_label": "direct|derived|inferred|uploaded|generated|synthetic|unknown",
  "currentness_label": "current|stale|historical|unknown|synthetic",
  "public_browser_context": false,
  "decision": "allow_metadata_only|allow_read_for_internal_shadow_use|deny_missing_source_scope|deny_scope_mismatch|deny_cross_user_or_cross_tenant|deny_public_browser_context|deny_private_or_raw_content|deny_stale_or_untrusted_source|deny_unsupported_use_context|deny_missing_policy|deny_runtime_authority|deny_provider_or_external_call|deny_final_answer_or_user_output|escalate_for_design_review",
  "decision_reason_labels": ["validated_same_scope", "internal_shadow_only"],
  "blocked_reason_labels": [],
  "required_followup": ["none|request_scope|request_policy|design_review|scoped_adapter_required|external_validation_required"],
  "denied_authority": {
    "grants_runtime_authority": false,
    "permits_public_browser_runtime": false,
    "permits_unscoped_memory_reads": false,
    "permits_cross_user_context": false,
    "permits_provider_calls": false,
    "permits_dot_weslr_public_state": false,
    "permits_final_answer_generation": false,
    "permits_authentication_decisions": false,
    "permits_database_reads": false,
    "permits_memory_reads_without_adapter": false
  }
}
```

Record constraints:

- The decision record is metadata only.
- It must not include raw memory, raw context, raw uploads, raw artifacts, raw logs, raw traces, hidden prompts, private text, provider output, database rows, filesystem paths as authority, or `.weslr` payloads.
- `authorization_id` is an internal metadata identifier, not a capability token.
- `allow_metadata_only` and `allow_read_for_internal_shadow_use` are not runtime/chat/browser permissions.
- Any allow decision remains unenforceable until a future scoped adapter consumes it.

## 4. Decision Outcomes

Future helpers should define these decision outcomes:

- `allow_metadata_only`: source and request metadata can be used as metadata only; no content read is authorized.
- `allow_read_for_internal_shadow_use`: a future scoped adapter may perform a bounded internal shadow read if separately implemented and called; no runtime/user output authority is granted.
- `deny_missing_source_scope`: source scope is absent or not validated.
- `deny_scope_mismatch`: requester and target scope mismatch in a way not allowed by policy.
- `deny_cross_user_or_cross_tenant`: target belongs to another user, guest, account, tenant, workspace, project, conversation, or session without reviewed policy.
- `deny_public_browser_context`: public/browser context requests private/operator-local/local `.weslr`/unsafe shared state.
- `deny_private_or_raw_content`: requested read would expose raw private, hidden, uploaded, artifact, log, trace, memory, or operator-local content.
- `deny_stale_or_untrusted_source`: requested use requires current/trusted evidence but source is stale, inferred, unknown, or insufficient.
- `deny_unsupported_use_context`: requested use context is unknown or unsupported by the source policy.
- `deny_missing_policy`: no explicit policy exists for the source kind, owner kind, requested read kind, or use context.
- `deny_runtime_authority`: request implies runtime/chat/browser/public authority.
- `deny_provider_or_external_call`: request implies provider/model/search/advisor/network/external call authority.
- `deny_final_answer_or_user_output`: request implies final-answer generation, reply text, preview, sendable output, or user-facing output.
- `escalate_for_design_review`: metadata is ambiguous or the policy space is not designed enough for a safe decision.

Default outcome is denial when the policy is unknown, incomplete, contradictory, non-JSON-safe, or authority-expanding.

## 5. Required Inputs

Future authorization must require these explicit inputs:

1. Validated source-scope metadata from the namespace/source-scope helper family.
2. `requested_use_context`.
3. `requested_read_kind`.
4. Requester tenant/account/user-or-guest/session/conversation scope.
5. Target source scope.
6. Public/browser flag or runtime context label.
7. Privacy, provenance, currentness, and retention labels.
8. Owner/scope match label or enough metadata to derive it deterministically.
9. Denied-authority fields present and false.
10. Explicit policy label or policy table input for the requested source kind and use context.

Authorization must not rely on untrusted display names, query-string identity, browser-local labels, session ID alone, current working directory, process globals, thread locals, active artifact pointer, active upload pointer, default timeline, or local operator `.weslr` state.

## 6. Fail-Closed Rules

Future helpers must fail closed when:

1. `source_scope` is missing.
2. `source_scope` is invalid.
3. Requester scope is missing.
4. Target scope is missing.
5. Tenant mismatch exists without explicit reviewed policy.
6. Account/user mismatch exists without explicit reviewed policy.
7. Session/conversation mismatch exists where the resource requires session or conversation confinement.
8. Guest scope attempts authenticated read.
9. Authenticated scope attempts guest-private read without explicit policy.
10. Anonymous or aggregate scope carries raw private content.
11. Query-string `user_id` is used as identity authority.
12. Display name, profile claim, channel label, request parameter, or browser-local label is used as identity authority.
13. Global `.weslr` is used as public scope.
14. `tl_default` is used as public/browser/shared user scope.
15. Process-global, thread-local, current-working-directory, active artifact pointer, active upload pointer, default timeline, or default user inference is used.
16. Resource kind is memory, context, evidence, artifact, upload, cache, log, trace, transcript, profile, timeline, queue, daemon, or background result without explicit source scope.
17. Public/browser context requests private, operator-local, raw, local `.weslr`, or unreviewed shared state.
18. Denied-authority fields are missing.
19. Any denied-authority field is true.
20. Requested use implies runtime/chat/browser/final-answer/provider/search/advisor/external-call/`.weslr` public authority.
21. Authorization policy is unknown, absent, contradictory, or not JSON-safe.
22. Source currentness or provenance is insufficient for the requested use context.
23. Request would create cross-user context, preference, locale, language, upload, artifact, cache, log, trace, queue, or daemon influence.

Fail-closed output should include blocked reason labels and required followup labels. It should not include the private content that caused denial.

## 7. Separation From Source-Scope Helpers

Source-scope validation is not permission. In exact invariant form: source-scope validation is not permission.

Central read authorization is also not a read adapter.

Separation rules:

- Source-scope helpers identify and validate ownership/source metadata.
- Central read authorization decides whether a scoped read may be allowed by policy.
- Authorization decision records do not fetch content.
- Authorization decision records do not perform filesystem, network, provider, database, browser, runtime, or `.weslr` IO.
- Authorization decision records do not authenticate users.
- Authorization decision records do not create sessions.
- Authorization decision records do not generate final answers or candidate prose.
- Scoped adapters later enforce decisions before reads.
- A read without adapter enforcement remains unauthorized even if an authorization metadata record exists.

The future helpers return metadata only: request metadata, validation metadata, decision metadata, safe summaries, JSON-safe copies, and internal review Markdown.

## 8. Relationship To Future Adapters

This design feeds later lanes:

### 8.1 Scoped memory/context read adapter

The future adapter must require an authorization decision before touching memory, context, profile, timeline, transcript, facts, documents, evidence, project registry, conversation state, or continuity snapshots.

### 8.2 Scoped artifact/upload registry

The future registry must require authorization before resolving artifact IDs, upload IDs, active artifact pointers, upload-derived text, summaries, embeddings, facts, or evidence packets.

### 8.3 Cache/log/trace scoping

Future cache/log/trace helpers must require authorization before cache hits, log reads, trace reads, daemon outputs, queue outputs, background results, or debug state can influence candidates.

### 8.4 Async request context

Future async request context must carry tenant/account-or-guest/session/conversation/workspace/source scope into every authorization call without process-global or thread-local fallback.

### 8.5 Leakage negative tests

Future leakage tests must prove authorization denies cross-tenant, cross-user, guest/authenticated, conversation, session, artifact, upload, cache, log, trace, `.weslr`, `tl_default`, and default-timeline leakage.

### 8.6 Candidate/checkpoint/assembly helpers

Candidate response formation, response-facing authority checkpoint, and safe final response assembly shadow helpers must treat unauthorized or missing read authorization as a hard block. They must not infer, repair, or bypass authorization.

## 9. Negative Test Design

Future tests should use synthetic metadata only and cover:

1. Missing source scope denied.
2. Invalid source scope denied.
3. Tenant mismatch denied.
4. Account mismatch denied.
5. User mismatch denied.
6. Session mismatch denied where session confinement is required.
7. Conversation mismatch denied where conversation confinement is required.
8. Guest-to-authenticated read denied.
9. Authenticated-to-guest-private read denied.
10. Cross-user memory denied.
11. Cross-tenant artifact denied.
12. Cross-conversation upload denied where conversation confinement is required.
13. Query-string identity denied.
14. Display-name/profile-claim/channel-label identity denied.
15. Global `.weslr` denied.
16. `tl_default` denied.
17. Process-global/default timeline inference denied.
18. Active artifact/upload pointer inference denied.
19. Private/operator-local state denied in `public_browser` context.
20. Raw private content denied for anonymous aggregate.
21. Unknown policy denied.
22. Missing denied-authority field denied.
23. True denied-authority field denied.
24. Final-answer authority denied.
25. Runtime/chat/browser authority denied.
26. Provider/model/search/advisor authority denied.
27. `.weslr` public state authority denied.
28. Valid synthetic same-scope metadata request allowed only as `allow_metadata_only` or `allow_read_for_internal_shadow_use`.
29. No filesystem calls.
30. No network calls.
31. No provider/model/search/advisor calls.
32. No database calls.
33. No runtime/browser/chat calls.
34. No `.weslr` reads or writes.
35. JSON-safe export preserves denied-authority false fields and blocked labels.
36. Internal Markdown rendering omits raw content and states metadata-only posture.

## 10. Denied Authority Fields

Future authorization records must keep these denied-authority fields present and false:

```json
{
  "grants_runtime_authority": false,
  "permits_public_browser_runtime": false,
  "permits_unscoped_memory_reads": false,
  "permits_cross_user_context": false,
  "permits_provider_calls": false,
  "permits_dot_weslr_public_state": false,
  "permits_final_answer_generation": false,
  "permits_authentication_decisions": false,
  "permits_database_reads": false,
  "permits_memory_reads_without_adapter": false
}
```

Validation must fail closed if any field is missing or true. Future implementation must not silently add new authority fields with permissive defaults.

## 11. Future API Design Only

A later separately authorized implementation lane may implement APIs with these names:

- `build_read_authorization_request_v1`
- `validate_read_authorization_request_v1`
- `authorize_scoped_read_v1`
- `require_read_authorization_for_candidate_v1`
- `summarize_read_authorization_v1`
- `to_read_authorization_json_safe_v1`
- `render_read_authorization_markdown_v1`

Design intent:

- `build_read_authorization_request_v1` builds JSON-safe request metadata from explicit arguments.
- `validate_read_authorization_request_v1` validates required fields and denied-authority invariants.
- `authorize_scoped_read_v1` returns a decision record; it does not read content.
- `require_read_authorization_for_candidate_v1` blocks candidate metadata that depends on unauthorized or missing reads.
- `summarize_read_authorization_v1` returns safe metadata summary only.
- `to_read_authorization_json_safe_v1` round-trips through JSON-safe structures.
- `render_read_authorization_markdown_v1` renders internal review Markdown only after validation and without raw content.

No implementation is authorized in this lane.

## 12. Direction Check

Options:

- A — review/context-align this design, then implement narrow metadata-only central read authorization helpers
- B — pause/review architecture before implementation
- C — design scoped memory/context read adapter before implementing central authorization

Direction check: `A`.

Recommendation: choose A only if the design remains metadata-only, does not perform reads, does not grant runtime authority, does not touch source-scope implementation, and is reviewed/context-aligned before implementation.

Reason: namespace/source-scope helpers are already implemented and reviewed. Central read authorization is now the next missing guard before scoped adapters, candidate formation helpers, response-facing checkpoint helpers, safe assembly helpers, or chain-level shadow tests can safely use private/shared state.

## 13. Safety Conclusion

No runtime step is authorized.

No public/browser step is authorized.

No implementation step is authorized.

No memory/context/evidence/artifact/upload/cache/log/trace read is authorized.

No `.weslr` public runtime state is authorized.

No provider/model/search/advisor call is authorized.

No authentication decision or database read is authorized.

No candidate execution, final-answer generation, safe assembly, scoring, judging, official claim, or authority grant is authorized.
