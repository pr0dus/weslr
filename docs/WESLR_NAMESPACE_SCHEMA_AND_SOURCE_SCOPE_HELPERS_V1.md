# WESLR Namespace Schema And Source Scope Helpers V1

## Status

- Lane: `DESIGN_NAMESPACE_SCHEMA_AND_SOURCE_SCOPE_HELPERS_V1`
- Lane type: design-only
- Runtime changes: none
- Implementation changes: none
- Target future helper module: design target only, not created in this lane
- Target future tests: design target only, not created in this lane

This document designs future namespace schema and source-scope helpers. These helpers are intended to provide metadata foundations for identifying whose context, memory, evidence, artifact, upload, cache, trace, log, candidate input, or runtime-adjacent dependency belongs to whom.

## 1. Purpose And Non-Goals

### Purpose

Design a narrow metadata-only helper family that can later represent and validate source scope before any candidate response formation, response-facing authority checkpoint, safe final response assembly shadow work, scoped read adapter, artifact/upload lookup, cache/log/trace use, or public/browser/runtime path depends on contextual material.

The future helper family should make source ownership explicit and machine-checkable through stable metadata fields, JSON-safe records, validation outcomes, and denied-authority flags.

### Non-goals

This lane does not authorize or create:

- runtime/browser/public authority
- authentication implementation
- account creation or login/session infrastructure
- database migration
- memory reads
- context reads
- evidence reads
- artifact/upload/cache/log/trace reads
- `.weslr` public runtime state
- final-answer generation
- candidate response formation helper implementation
- authority checkpoint helper implementation
- safe final response assembly helper implementation
- chat/browser/voice/UI behavior
- provider/model/search/advisor calls
- scoring/judging
- official/product/certification/public-readiness claims
- TIA/C#/Siemens bridge changes

This document is design-only and creates no helper/source/test implementation.

## 2. Relationship To Current Architecture

This design follows and narrows the direction established by:

- `docs/WESLR_MULTI_USER_SESSION_TENANT_ISOLATION_BOUNDARY_V1.md`
- `docs/WESLR_MULTI_USER_RETROFIT_PLAN_BEFORE_RESPONSE_FACING_AUTHORITY_CHECKPOINT_V1.md`
- `docs/WESLR_DIRECTION_REVIEW_AFTER_SAFE_FINAL_RESPONSE_ASSEMBLY_SHADOW_BOUNDARY_V1.md`

It supports future separately authorized work:

- central read authorization helper
- scoped memory/context read adapter
- scoped artifact/upload registry
- authority checkpoint validation
- safe final response assembly shadow helpers
- cache/log/trace scoping
- async request context
- leakage negative tests

Architecture placement:

1. Namespace/source-scope helpers identify and validate scope metadata.
2. Central read authorization decides whether a scoped read is allowed.
3. Scoped adapters enforce read decisions before touching memory/context/evidence/artifacts/uploads/caches/logs/traces.
4. Candidate formation and authority checkpoint helpers may consume only validated, scoped metadata.
5. Safe final response assembly shadow helpers may later consume approved candidate/checkpoint metadata only after scope foundations exist.

## 3. Required Namespace Identifiers

Future metadata records should use these canonical fields where applicable:

- `tenant_id`
- `account_id`
- `user_id`
- `session_id`
- `conversation_id`
- `workspace_id`
- `project_id`
- `artifact_id`
- `upload_id`
- `memory_scope_id`
- `evidence_scope_id`
- `cache_scope_id`
- `trace_scope_id`
- `locale`
- `language`
- `source_kind`
- `source_owner_kind`
- `source_created_at`
- `source_currentness_label`

Field notes:

- `tenant_id` identifies the top-level isolation namespace for hosted/public/multi-user use.
- `account_id` identifies an authenticated account namespace when authentication exists.
- `user_id` identifies a user within a tenant/account model, but does not by itself prove identity.
- `session_id` identifies an interaction/session namespace and is not sufficient alone for owner authority.
- `conversation_id` identifies a conversation/thread namespace and is not sufficient alone for owner authority.
- `workspace_id` and `project_id` identify work/project scope and must not imply user authority by themselves.
- `artifact_id` and `upload_id` identify objects that must inherit owner/source scope.
- `memory_scope_id`, `evidence_scope_id`, `cache_scope_id`, and `trace_scope_id` identify derived stores or slices that must be linked back to owner/source scope.
- `locale` and `language` constrain formatting and interpretation, but are not identity proof.
- `source_kind` identifies the source class, such as memory, context, evidence, artifact, upload, cache, log, trace, transcript, profile, timeline, candidate, synthetic_fixture, or operator_local.
- `source_owner_kind` identifies whether the source is tenant-owned, account-owned, user-owned, session-owned, conversation-owned, workspace-owned, project-owned, artifact-owned, upload-owned, guest-owned, anonymized-aggregate, operator-local, or synthetic.
- `source_created_at` records creation time as metadata, not authority.
- `source_currentness_label` records freshness/currentness status, not truth.

## 4. Source Scope Record Shape

Future helpers should define a metadata-only record shaped like:

```json
{
  "schema": "weslr.source_scope.v1",
  "source_scope_id": "scope_...",
  "tenant_id": "tenant_...",
  "account_id": "acct_...",
  "user_id": "user_...",
  "session_id": "sess_...",
  "conversation_id": "conv_...",
  "workspace_id": "workspace_...",
  "project_id": "project_...",
  "source_kind": "memory|context|evidence|artifact|upload|cache|log|trace|candidate|synthetic_fixture|operator_local",
  "source_ref": "opaque reference label, not raw content",
  "source_owner_kind": "tenant|account|user|session|conversation|workspace|project|artifact|upload|guest|anonymized_aggregate|operator_local|synthetic",
  "allowed_use_contexts": ["candidate_metadata", "authority_checkpoint", "shadow_validation"],
  "retention_label": "ephemeral|session|conversation|project|account|tenant|operator_local|unknown",
  "privacy_label": "public|user_private|tenant_private|operator_private|synthetic|redacted|unknown",
  "currentness_label": "current|stale|historical|unknown|synthetic",
  "provenance_label": "direct|derived|inferred|uploaded|generated|synthetic|unknown",
  "validation_status": "valid|invalid|blocked_missing_scope|blocked_unsafe_scope|synthetic_only",
  "locale": "optional locale label",
  "language": "optional language label",
  "source_created_at": "optional ISO-8601 timestamp label",
  "denied_authority": {
    "grants_runtime_authority": false,
    "permits_public_browser_runtime": false,
    "permits_unscoped_memory_reads": false,
    "permits_cross_user_context": false,
    "permits_provider_calls": false,
    "permits_dot_weslr_public_state": false,
    "permits_final_answer_generation": false,
    "permits_authentication_decisions": false
  }
}
```

Record constraints:

- `source_ref` must be an opaque reference or label, not raw private content.
- The record must be JSON-safe.
- The record must be metadata-only.
- The record must not perform authorization by itself.
- The record must not imply that a read is allowed.
- The record must preserve false denied-authority fields.

## 5. Validation Rules

Future `validate_source_scope_v1` behavior should include these rules:

1. Missing `tenant_id`, `account_id` or `user_id`, `session_id`, or `conversation_id` blocks public/browser use where those scopes are required.
2. Unscoped memory, context, evidence, artifact, upload, cache, log, trace, transcript, profile, timeline, or candidate input blocks candidate response authority.
3. Query-string `user_id` is not identity authority.
4. Display names, profile claims, browser-local labels, and request parameters are not identity authority.
5. Global `.weslr` is invalid as public multi-user scope.
6. `tl_default` is invalid as shared user scope for public/browser/multi-user use.
7. Source scope must be explicit and carried in metadata, not inferred from process globals, thread locals, current working directory, active artifact pointer, active upload pointer, or default timeline.
8. Guest sessions require explicit guest namespace fields and must not silently promote into authenticated user memory.
9. Anonymous or aggregated learning requires an explicit anonymized policy label and must not carry raw user-private content.
10. Locale and language are metadata constraints, not proof of identity or authorization.
11. Private/operator-local source scope must not be marked usable for public/browser response paths.
12. Cross-user source mixing is invalid unless an explicit anonymized aggregate policy is present and raw/private material is absent.
13. Validation must fail closed when required fields are missing, contradictory, unsafe, or unknown for the requested use context.

## 6. Helper API Design Only

Future helper APIs may include:

- `build_source_scope_v1(...)`
  - Constructs a metadata-only source-scope record from explicit fields.
  - Does not read memory/context/evidence/artifacts/uploads/caches/logs/traces.
  - Does not infer scope from globals.

- `validate_source_scope_v1(source_scope, *, required_use_context=None, public_browser=False)`
  - Returns validation metadata.
  - Fails closed for missing or unsafe scope.
  - Does not authorize reads.

- `require_source_scope_for_candidate_v1(candidate_metadata)`
  - Checks that candidate-facing metadata carries valid source scope before candidate authority can be considered.
  - Returns blocked metadata if scope is missing or unsafe.
  - Does not form a response.

- `summarize_source_scope_v1(source_scope)`
  - Returns a compact metadata summary for reports/reviews.
  - Does not expose raw private content.

- `to_source_scope_json_safe_v1(source_scope)`
  - Produces JSON-safe metadata.
  - Rejects non-JSON-safe values.

- `render_source_scope_markdown_v1(source_scope)`
  - Renders safe internal Markdown for review/report artifacts only.
  - Not user-facing output.
  - Not final-answer text.

All future APIs must remain pure, deterministic, import-safe, side-effect-free, in-memory, synthetic-testable, no `.weslr` IO, no provider/model/search/advisor calls, no runtime wiring, and no authority grants.

## 7. Negative Test Design

Future tests should prove that the helper family:

- rejects missing `tenant_id`
- rejects missing `account_id`, `user_id`, or `session_id` where required
- rejects missing `conversation_id` where conversation scope is required
- rejects query-string-only identity
- rejects display-name-only or profile-claim-only identity
- rejects global `.weslr` public state
- rejects `tl_default` as shared user scope
- rejects unscoped artifact/upload/cache/log/trace references
- rejects unscoped memory/context/evidence references
- rejects cross-user source mixing
- rejects private/operator-local source scope for public/browser use
- rejects guest-to-authenticated promotion without explicit policy
- rejects anonymous/aggregate records that carry raw/private material
- preserves false denied-authority fields
- produces JSON-safe export only
- remains import-safe with no side effects
- performs no filesystem, network, provider/model/search/advisor, runtime, chat, browser, or `.weslr` calls

## 8. Relationship To Future Central Read Authorization

Namespace/source-scope helpers identify and validate scope metadata.

Central read authorization decides whether a read is allowed.

Both are required before scoped memory/context reads or public/browser runtime.

Ordering:

1. Design namespace schema and source-scope helpers.
2. Review namespace schema and source-scope helper design.
3. Implement narrow pure metadata helpers only if separately authorized.
4. Review implementation.
5. Design central read authorization helpers against the stable source-scope shape.
6. Implement central read authorization only if separately authorized.
7. Only after both exist should scoped memory/context adapters or public/browser paths be considered.

This document does not authorize central read authorization implementation.

## 9. Denied Authority Fields

Future source-scope records and validation outputs must keep these denied authority fields false:

```text
grants_runtime_authority: false
permits_public_browser_runtime: false
permits_unscoped_memory_reads: false
permits_cross_user_context: false
permits_provider_calls: false
permits_dot_weslr_public_state: false
permits_final_answer_generation: false
permits_authentication_decisions: false
```

Any helper, test, report, artifact, or handoff that sets or implies one of these fields true must be rejected unless a separate explicitly authorized and reviewed lane changes the boundary.

## 10. Direction Check

Options:

- A — review/context-align this design, then implement namespace/source-scope helpers
- B — pause/review architecture before implementation
- C — design central read authorization helper before implementing namespace helpers

Recommendation: A, only if the future helper implementation remains narrow, metadata-only, pure, deterministic, import-safe, side-effect-free, synthetic-data-only, no `.weslr` IO, no runtime wiring, no provider/model/search/advisor calls, no auth decisions, no memory reads, no public/browser behavior, no final-answer/assembly helper implementation, and no authority grants.

Rationale: namespace/source-scope helpers are lower-risk than safe assembly helpers and are a prerequisite for central read authorization. Designing central read authorization first would lack a stable scope record. Pausing architecture is safe but less useful now that the direction review identified namespace/source-scope schema as the next lowest-risk substrate.

## 11. Safety Check

This document is design-only. It creates no implementation, no runtime wiring, no public/browser authority, no authentication implementation, no database migration, no memory/context/evidence reads, no `.weslr` public runtime state, no final-answer generation, no candidate/authority/assembly helper implementation, no provider/model/search/advisor calls, no scoring/judging, no official/product/certification claims, and no authority grants.
