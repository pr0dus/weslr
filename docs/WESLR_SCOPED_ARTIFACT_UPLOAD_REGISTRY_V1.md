# WESLR Scoped Artifact Upload Registry V1

## Status

- Lane: `DESIGN_SCOPED_ARTIFACT_UPLOAD_REGISTRY_V1`
- Lane type: design-only
- Design path: `docs/WESLR_SCOPED_ARTIFACT_UPLOAD_REGISTRY_V1.md`
- Runtime changes: none
- Implementation changes: none
- Artifact/upload reads: none
- Upload ingestion: none
- `.weslr` IO: none
- Final-answer authority: none

This document designs a future scoped artifact/upload registry boundary. It records artifact/upload metadata only and defines how future metadata can be registered, scoped, authorized, summarized, and rejected before any artifact/upload content is read or exposed.

## 1. Purpose

The future scoped artifact/upload registry exists to make artifact and upload handling fail closed before content access. The registry records metadata only and enforces:

- source_scope validation
- central read authorization
- artifact/upload ownership scope
- provenance/currentness/privacy labels
- no raw content exposure by default
- no cross-user or global artifact leakage

The registry is not a content reader. It is a boundary where artifact/upload identity, ownership, requester/target scope, policy labels, and read authorization must be present and valid before any later separately authorized content-bearing adapter could be considered.

## 2. Non-goals

This design explicitly does not authorize:

- no implementation
- no artifact file reads
- no upload ingestion
- no filesystem scanning
- no `.weslr` IO
- no database/auth/session implementation
- no runtime/chat/browser wiring
- no provider/model/search/advisor calls
- no final-answer generation
- no public/user-facing output
- no automatic truth from artifacts/uploads
- no cross-user/global artifact reads

## 3. Registry Layers

A future helper implementation should model these layers as metadata transformations only:

1. `artifact_metadata_intake` — accepts explicit artifact metadata labels without reading artifact content.
2. `upload_metadata_intake` — accepts explicit upload metadata labels without ingesting upload bytes, browser state, or runtime transcript data.
3. `source_scope_requirement` — requires a valid source_scope record for the artifact/upload source and intended use.
4. `ownership_scope_validation` — compares owner_scope, requester_scope, and target_scope before access decisions.
5. `central_read_authorization_requirement` — requires central read authorization metadata before any non-blocked registry access result.
6. `registry_policy_check` — validates access mode, policy_label, privacy_label, retention_label, provenance_label, currentness_label, and authorized_use_contexts.
7. `privacy/redaction boundary` — forces content_included to false and exposes only redaction/privacy status labels.
8. `metadata-only preview` — permits bounded metadata summaries only when source scope, ownership, and authorization are valid.
9. `artifact_read_envelope` — creates a metadata envelope for access status, not raw artifact/upload content.
10. `rejection/result summary` — returns blocked reasons, observed gaps, and next safe steps.
11. `audit trace metadata` — records decision labels and metadata-only trace anchors without logs, files, `.weslr`, or runtime reads.

## 4. Future Public Helper APIs

Future helper API names only:

- `build_scoped_artifact_upload_registry_entry_v1`
- `validate_scoped_artifact_upload_registry_entry_v1`
- `authorize_scoped_artifact_upload_access_v1`
- `build_scoped_artifact_upload_access_envelope_v1`
- `validate_scoped_artifact_upload_access_envelope_v1`
- `summarize_scoped_artifact_upload_registry_v1`
- `to_scoped_artifact_upload_registry_json_safe_v1`
- `render_scoped_artifact_upload_registry_markdown_v1`

These names do not authorize implementation in this lane.

## 5. Registry Entry Metadata

A future registry entry should be JSON-safe metadata only and should include:

- `schema_version`
- `registry_entry_id`
- `artifact_or_upload_kind`
- `artifact_id`
- `upload_id`
- `source_scope`
- `owner_scope`
- `requester_scope`
- `target_scope`
- `storage_locator_label`
- `content_included: false` by default
- `content_hash_label`
- `provenance_label`
- `currentness_label`
- `privacy_label`
- `retention_label`
- `policy_label`
- `authorized_use_contexts`
- `denied_authority`

`storage_locator_label` is a label only, not a path to read. `content_hash_label` is metadata only, not proof of truth or permission to retrieve content.

## 6. Access Envelope Metadata

A future access envelope should be JSON-safe metadata only and should include:

- `schema_version`
- `registry_entry_id`
- `access_request_id`
- `authorization_decision`
- `access_status`
- `access_mode`
- `content_included: false` by default
- `redaction_status`
- `scope_summary`
- `provenance_summary`
- `currentness_summary`
- `blocked_reason_labels`
- `observed_gaps`
- `next_safe_steps`
- `denied_authority`

The envelope must never include raw artifact content, raw upload content, runtime transcripts, browser upload state, provider output, final-answer text, or public/user-facing prose.

## 7. Allowed Access Modes

Safe future access modes only:

- `metadata_only_preview`
- `redacted_summary_candidate`
- `provenance_summary_metadata`
- `continuity_anchor_metadata`
- `blocked_no_access`

All allowed modes remain metadata-only. `redacted_summary_candidate` is a candidate metadata label only and does not imply content access, factual truth, runtime use, or final-answer generation.

## 8. Forbidden Access Modes

Future validation must block:

- `raw_artifact_content`
- `raw_upload_content`
- `cross_user_artifact_access`
- `global_artifact_registry`
- `dot_weslr_artifact_state`
- `runtime_transcript_upload`
- `browser_public_upload_state`
- `provider_output_ingestion`
- `final_answer_artifact_injection`
- `unrestricted_artifact_dump`

## 9. Fail-Closed Rules

A future implementation must deny or block when:

- missing or invalid source_scope
- missing owner/requester/target scope
- missing or denied read authorization
- ownership mismatch
- cross-user/cross-tenant risk
- guest/anonymous authenticated mismatch
- public browser context requests private/operator-local artifact
- raw artifact/upload content requested
- forbidden access mode requested
- `.weslr`/global/`tl_default`/process-global/default timeline markers appear
- query-string identity appears
- stale/untrusted artifact is requested as truth
- final-answer/runtime/chat/provider/search authority is implied
- denied-authority fields are missing or true
- metadata is not JSON-safe

Blocked results should use `blocked_no_access`, preserve `content_included: false`, include blocked_reason_labels, and expose no raw content.

## 10. Relationship To Existing Helpers

- `source_scope` identifies and validates ownership and access scope metadata. It is not permission and not a read.
- `read_authorization` decides whether scoped artifact/upload metadata access may proceed. It is still metadata-only and does not read content.
- The scoped artifact/upload registry enforces authorization at the artifact/upload boundary before any artifact/upload content could be considered by a future separately authorized adapter.
- The scoped memory/context adapter remains separate. Memory/context reads and artifact/upload registry checks must not collapse into one global reader.
- Artifact/upload metadata can support relevance/provenance only, not automatic truth.
- Evidence/provenance still controls factual authority. Artifact/upload presence, upload identity, hash labels, or storage labels do not create truth, answer authority, product readiness, or public-output authority.

## 11. Negative Tests Required For Future Implementation

Future implementation test coverage should include:

- missing/invalid source scope
- missing owner/requester/target scope
- missing/denied authorization
- ownership mismatch
- cross-user/tenant mismatch
- public-browser/private-artifact conflict
- raw artifact/upload content request
- each forbidden access mode
- `.weslr`/global/`tl_default`/process-global marker
- query-string identity
- stale/untrusted artifact-as-truth
- final-answer/runtime/provider/search authority marker
- denied-authority true/missing
- non-JSON-safe metadata
- metadata-only allowed path
- `blocked_no_access` path

Tests should be synthetic metadata only and should not use real artifacts, real uploads, `.weslr`, filesystem/database/auth/browser/session state, provider/model/search/advisor calls, runtime transcripts, or final-answer generation.

## 12. Direction Check

A — review/context-align this design, then implement scoped artifact/upload registry helpers.

Recommendation: A, because this design preserves no raw artifact reads, no upload ingestion, no runtime wiring, and no final-answer authority while closing the scoped artifact/upload registry gap identified before chat wiring.

## Safety Conclusion

This design is metadata-only and boundary-only. It creates no implementation, reads no artifact or upload content, performs no upload ingestion, touches no `.weslr` IO, wires no runtime/chat/browser behavior, calls no provider/model/search/advisor, and grants no final-answer, public-output, cross-user, global registry, or truth authority.
