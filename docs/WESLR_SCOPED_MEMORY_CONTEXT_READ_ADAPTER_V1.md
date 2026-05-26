# WESLR Scoped Memory Context Read Adapter V1

## Status

- Lane: `DESIGN_SCOPED_MEMORY_CONTEXT_READ_ADAPTER_V1`
- Lane type: design-only
- Document path: `docs/WESLR_SCOPED_MEMORY_CONTEXT_READ_ADAPTER_V1.md`
- Runtime changes: none
- Implementation changes: none
- Source/test/helper changes: none
- Chat/browser/voice/UI changes: none
- Provider/model/search/advisor calls: none
- `.weslr` IO: none
- Real memory/context reads: none
- Final-answer or user-facing output: none
- Direction check: `A — review/context-align this design, then implement scoped memory/context read adapter helpers`

This document designs a future scoped memory/context read adapter boundary. It does not implement an adapter, perform real reads, touch `.weslr`, wire runtime/chat/browser behavior, query databases, make authentication/session decisions, call providers/search/advisors/models, or generate final/user-facing answers.

## 1. Purpose

The purpose is to design a future adapter that can request scoped memory/context metadata safely before any actual memory or context data is read or exposed.

The future adapter boundary uses:

- source scope as identity/scope metadata validation
- central read authorization as read-decision metadata
- the adapter boundary as the future enforcement point before any actual memory/context read

The adapter exists to ensure memory/context data can never flow into candidate formation, authority checkpoints, safe assembly, runtime, chat, browser, or final-answer paths unless scope is validated, read authorization allows the bounded request, and the future adapter enforces the authorization at the read boundary.

## 2. Non-Goals

This design does not authorize or create:

- implementation
- real memory reads
- context reads
- `.weslr` IO
- database/auth/session implementation
- runtime/chat/browser wiring
- provider/model/search/advisor calls
- final-answer generation
- public/user-facing output
- automatic truth from memory
- cross-user/global memory reads
- helper/source/test implementation files
- cache/log/trace/artifact/upload adapters
- theorem prover/solver runners
- web/search ingestion
- TIA/C#/Siemens bridge changes

Memory/context content remains relevance input only. It is never automatic truth, never evidence by itself, and never a substitute for source/provenance/evidence checks.

Explicit non-goal summary: no implementation, no real memory reads, no context reads, no final-answer generation, no public/user-facing output, no automatic truth from memory, and no cross-user/global memory reads.

## 3. Adapter Layers

A future scoped memory/context read adapter should be organized into these layers.

### 3.1 `read_request_intake`

Accept explicit request metadata only. The intake layer must not read memory/context content. It normalizes the requested read kind, use context, content mode, requester scope, target scope, privacy/provenance/currentness/retention labels, and denied-authority map.

### 3.2 `source_scope_requirement`

Require a validated source scope before any read decision can proceed. Missing, invalid, unscoped, global, query-string, `.weslr`, `tl_default`, process-global, default-timeline, public-browser/private-state, or unsafe scope metadata must fail closed before any adapter read.

### 3.3 `central_read_authorization_requirement`

Require central read authorization metadata before any read envelope can be built. The authorization must be explicit, JSON-safe, same-scope or policy-safe, and false-only for denied-authority fields. Denied, missing, malformed, stale, or authority-expanding authorization blocks the adapter.

### 3.4 `adapter_policy_check`

Check adapter-specific read mode, content mode, privacy label, requested use context, public/browser flag, currentness label, provenance label, and policy label. The adapter must enforce the narrower of source-scope validation, read authorization, and adapter policy.

### 3.5 `redaction/privacy boundary`

Default to no content. Redaction is mandatory before any future content-bearing summary mode. Raw private content, raw context, unrestricted profile dumps, cross-user context, runtime transcripts, provider outputs, and final-answer injections are forbidden.

### 3.6 `metadata-only preview mode`

Permit metadata-only summaries of what would be read, why it is allowed or blocked, and which scope/provenance/currentness labels apply. This mode must keep `content_included: false`.

### 3.7 `read_result_envelope`

Wrap any future result in a JSON-safe envelope with authorization decision metadata, scope summary, provenance summary, currentness summary, redaction status, blocked reasons, observed gaps, next safe steps, and false-only denied authority.

### 3.8 `rejection/result summary`

Return deterministic blocked summaries for denied requests. Rejections must be safe to render internally and must not include raw memory/context content.

### 3.9 `audit trace metadata`

Record metadata only: request id, authorization id/decision label, source-scope summary, adapter policy label, read mode, blocked reasons, and denied authority. Audit trace metadata is not runtime logging authority and must not write `.weslr` or public/browser state in this design.

## 4. Future Public Helper APIs

Future helper API names only:

- `build_scoped_memory_context_read_request_v1`
- `validate_scoped_memory_context_read_request_v1`
- `authorize_scoped_memory_context_read_request_v1`
- `build_scoped_memory_context_read_envelope_v1`
- `validate_scoped_memory_context_read_envelope_v1`
- `summarize_scoped_memory_context_read_adapter_v1`
- `to_scoped_memory_context_read_adapter_json_safe_v1`
- `render_scoped_memory_context_read_adapter_markdown_v1`

These are design targets only. No implementation is created in this lane.

## 5. Request Metadata

Future request metadata should include:

- `schema_version`
- `request_id`
- `read_kind`: one of `memory`, `context`, `continuity_anchor`, `profile_summary`, `evidence_summary`
- `source_scope`
- `requester_scope`
- `target_scope`
- `requested_use_context`
- `requested_content_mode`
- `privacy_label`
- `retention_label`
- `provenance_label`
- `currentness_label`
- `policy_label`
- `authorization_request`
- `denied_authority`

Request metadata constraints:

- JSON-safe only
- no raw memory text
- no raw context text
- no raw private material
- no `.weslr` payloads
- no provider/model/search/advisor output
- no final-answer text
- no runtime transcript
- no hidden/protected material
- false-only denied-authority map required

## 6. Read Envelope Metadata

Future read envelope metadata should include:

- `schema_version`
- `request_id`
- `authorization_decision`
- `read_status`
- `read_mode`
- `content_included`: false by default
- `redaction_status`
- `scope_summary`
- `provenance_summary`
- `currentness_summary`
- `blocked_reason_labels`
- `observed_gaps`
- `next_safe_steps`
- `denied_authority`

Envelope constraints:

- `content_included` defaults to false and remains false for metadata-only preview modes
- blocked envelopes must not include content
- summaries must be metadata-only and JSON-safe
- denied authority must be complete and false-only
- envelope rendering is internal review Markdown only, not user-facing output

## 7. Allowed Read Modes

Safe design modes only:

- `metadata_only_preview`: show request/authorization/scope metadata only; `content_included: false`.
- `redacted_summary_candidate`: future bounded candidate summary mode only after adapter implementation/review; raw content remains forbidden.
- `continuity_anchor_metadata`: metadata about a continuity anchor only; no raw memory/context text.
- `evidence_summary_metadata`: metadata about evidence/provenance/currentness only; no automatic truth.
- `blocked_no_read`: fail-closed result; no content read or exposed.

Allowed read modes do not grant runtime, chat, browser, final-answer, provider/search/model/advisor, public output, or cross-user authority.

## 8. Forbidden Read Modes

The future adapter must block:

- `raw_memory_text`
- `raw_private_context`
- `cross_user_context`
- `global_memory`
- `dot_weslr_state`
- `runtime_transcript`
- `browser_public_state`
- `provider_output_ingestion`
- `final_answer_context_injection`
- `unrestricted_profile_dump`

Any synonym, marker, policy label, requested content mode, or next step implying these modes must fail closed.

## 9. Fail-Closed Rules

The future adapter must deny or block when:

- source scope is missing
- source scope is invalid
- read authorization is missing
- read authorization denies the request
- requester/target mismatch exists
- cross-user/cross-tenant risk exists
- guest/anonymous authenticated mismatch exists
- public browser context requests private/operator-local state
- raw private content is requested
- `.weslr`, global, `tl_default`, process-global, or default timeline markers appear
- query-string identity appears
- stale/untrusted source is requested as truth
- final-answer/runtime/chat/provider/search authority is implied
- denied-authority fields are missing or true
- output is not JSON-safe
- source scope validates but authorization is absent or denied
- authorization allows metadata only but the adapter request asks for content
- adapter policy is unknown, contradictory, or broader than read authorization
- evidence/provenance/currentness labels are missing for factual use
- memory/context is requested as automatic truth

Default outcome is `blocked_no_read`.

## 10. Relationship To `source_scope` And `read_authorization`

The separation is strict:

- `source_scope` identifies and validates scope metadata.
- `read_authorization` decides whether a scoped read may proceed.
- The scoped adapter would enforce the authorization at the read boundary.
- Memory/context content remains relevance input only, never automatic truth.
- Evidence/provenance still controls factual authority.

Source-scope validation is not permission. Read authorization is not a read. The scoped adapter is the future enforcement point, but this design does not implement that enforcement.

If source-scope and read-authorization disagree, the adapter must enforce the safest result: deny or metadata-only preview. If either prerequisite is missing, the adapter must return `blocked_no_read`.

## 11. Negative Tests Required For Future Implementation

A future implementation lane must include tests for:

- missing scope
- invalid scope
- missing authorization
- denied authorization
- cross-user mismatch
- cross-tenant mismatch
- public-browser/private-state conflict
- raw/private content request
- `.weslr` marker
- global memory marker
- `tl_default` marker
- process-global/default timeline marker
- query-string identity
- stale/untrusted source-as-truth
- final-answer authority marker
- runtime authority marker
- provider/search authority marker
- denied-authority true field
- denied-authority missing field
- non-JSON-safe metadata
- metadata-only allowed path
- `blocked_no_read` path
- content mode broader than authorization
- evidence/provenance/currentness missing for factual use
- internal Markdown renderer omits raw content
- JSON-safe export rejects unsafe objects

Tests must use synthetic metadata only and must not read `.weslr`, runtime transcripts, real memory, real context, browser state, provider output, databases, uploads, artifacts, logs, traces, or private user content.

## 12. Future Implementation Constraints

A future implementation may only create narrow metadata helper files and tests if separately authorized. It must remain:

- pure in-memory
- deterministic
- import-safe
- JSON-safe
- synthetic-data-tested
- metadata-only by default
- no real reads unless a later adapter-read implementation lane is explicitly authorized
- no `.weslr` IO
- no database/auth/session implementation
- no runtime/chat/browser wiring
- no provider/model/search/advisor calls
- no final-answer/user-facing output
- no authority grants

The future helper must not modify `weslr/chat_responder.py`, `weslr/source_scope.py`, or `weslr/read_authorization.py` unless a separate lane explicitly authorizes that exact file.

## 13. Direction Check

`A — review/context-align this design, then implement scoped memory/context read adapter helpers`

Rationale: this design clearly preserves no real reads, no runtime wiring, and no final-answer authority. It returns the chain from the clean UNKNOWN ENGINE diagnostic branch to the central read authorization / scoped memory-context adapter guard sequence before chat wiring.
