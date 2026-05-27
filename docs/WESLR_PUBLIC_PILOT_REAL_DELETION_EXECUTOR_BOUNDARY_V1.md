# WESLR Public Pilot Real Deletion Executor Boundary V1

## 1. Purpose

This boundary defines the rules for a future real public-pilot deletion executor. It does **not** authorize implementation, runtime wiring, or real deletion now. It only defines how a later executor must behave if and when it is separately approved.

## 2. Current Status

- implementation commit: `376d1e8`
- review commit: `3f82102`
- current deletion/revocation helpers are metadata-only / synthetic-safe primitives
- public pilot remains not ready
- real deletion executor does not yet exist

## 3. Deletion Executor Definition

A future deletion executor would be responsible for:

- accepting a validated deletion or revocation request
- verifying scope, tenant, and user identity
- applying suppression before deletion
- identifying allowed public-pilot storage categories
- deleting/removing/revoking only explicitly allowed records
- generating JSON-safe receipts
- preserving privacy and audit safety
- failing closed when ambiguous

This boundary does not define implementation mechanics. It only sets the safety contract for a future executor.

## 4. Allowed Future Deletion Targets

Only the following public-pilot scoped categories may be eligible in a later implementation, and only through explicit storage adapters:

- suggestion box public pilot entries
- pilot signal logger entries
- advisor/review queue public-pilot items
- synthetic/public-pilot calibration metadata
- public-pilot scoped artifacts specifically designed as deletable

Exact implementation must later map each category to an explicit storage adapter. No implicit storage discovery is allowed.

## 5. Forbidden Targets

The future executor must not automatically touch:

- `.weslr` runtime state
- unrelated user memory
- unrelated tenants
- process-global state
- query-string `user_id`
- `tl_default`
- backups without a separate backup policy
- exports without a separate export policy
- logs without a separate log retention policy
- runtime/chat/voice/UI behavior
- private raw transcripts unless later storage-specific design explicitly covers them
- source code, git history, or committed docs
- audit records that must be retained in redacted/safe form

## 6. Identity and Scope Validation

All deletion requests must fail closed unless they carry explicit validated namespace/source metadata.

Rules:

- no deletion by query-string `user_id`
- no anonymous deletion
- no guest cross-user deletion
- no tenant inference from process globals
- no broad matching
- no fuzzy identity matching
- no default namespace fallback
- no cross-tenant or cross-user promotion by assumption

Scope must be explicit and validated before any suppression or deletion path is considered.

## 7. Suppression-Before-Deletion Ordering

Required sequence:

1. validate request
2. build suppression marker
3. apply suppression to future processing metadata
4. freeze new processing for that scoped identity/category
5. enumerate eligible storage categories
6. delete/remove/revoke allowed items
7. generate receipt
8. validate receipt
9. return only JSON-safe metadata

If the sequence cannot be preserved, the executor must fail closed.

## 8. Receipt Policy

Receipts must be JSON-safe and must not include:

- raw deleted content
- private text
- full prompts/responses
- secrets
- storage dumps
- cross-user identifiers

Receipts may include:

- request id
- scoped namespace
- deletion category labels
- counts by category if safe
- skipped categories with safe reason labels
- timestamp metadata
- blocked/failed status
- validation labels
- denied authority fields

## 9. Backup / Export / Log Handling

This design does **not** authorize backup deletion, export deletion, or log deletion.

Those must be handled by separate future sub-boundaries:

- backup deletion / expiry boundary
- export revocation boundary
- audit log retention / redaction boundary
- retro-cleanup boundary

Until those exist, backup/export/log targets remain forbidden.

## 10. Failure Behavior

The future executor must fail closed when:

- scope is missing
- tenant is ambiguous
- request is malformed
- storage adapter is unknown
- category is not explicitly allowed
- raw data would need to be exposed
- deletion would cross tenant/user boundary
- receipt cannot be validated
- suppression marker cannot be applied

No fallback deletion path is allowed.

## 11. Validation and Tests Required Before Implementation

Future tests must cover:

- valid scoped deletion request
- revocation request
- malformed request blocked
- query-string user_id blocked
- guest/anonymous blocked
- cross-tenant blocked
- `.weslr` blocked
- `tl_default` blocked
- backup/export/log deletion blocked
- raw receipt leakage blocked
- suppression-before-deletion ordering
- JSON-safe receipt validation
- denied authority fields preserved
- no runtime/chat/UI/voice wiring

## 12. Denied Authority Fields

This boundary grants no authority for:

- real deletion
- public pilot launch
- deployment
- runtime integration
- automatic purge
- legal compliance claims
- GDPR/DSGVO compliance claims
- production readiness
- user-facing deletion UI
- backup deletion
- export deletion
- retro-cleanup

## 13. Future Implementation Sequence

Recommended later lanes:

- `REVIEW_PUBLIC_PILOT_REAL_DELETION_EXECUTOR_BOUNDARY_V1`
- `AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_PUBLIC_PILOT_REAL_DELETION_EXECUTOR_BOUNDARY_REVIEW_V1`
- only then consider `IMPLEMENT_PUBLIC_PILOT_REAL_DELETION_EXECUTOR_HELPERS_V1`

## 14. Decision

This document is a design-only governance boundary. It authorizes no implementation and no deletion.
