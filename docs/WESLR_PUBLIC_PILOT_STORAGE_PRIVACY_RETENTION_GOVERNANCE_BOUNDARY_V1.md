# WESLR Public Pilot Storage Privacy Retention Governance Boundary V1

## 1. Status

- design-only
- no implementation
- no source/runtime/helper edits
- no data migration
- no raw private data reads/dumps
- no raw JSON reads
- no DB row reads/writes
- no queue processing
- no email sending
- no deployment changes
- no OCW management changes
- no `.weslr` IO
- no provider/model/search/advisor calls
- no runtime/chat/UI/voice changes
- no final-answer generation
- no public launch
- no product/intelligence/Turing/certification claims
- no authority grant

## 2. Purpose

This document defines the governance boundary around WESLR's existing public pilot surfaces. It does not create new pilot surfaces and does not duplicate existing feedback, suggestion, review, queue, logger, website, or OCW/deployment surfaces.

It must govern:

- suggestion storage
- pilot logger storage/display
- public feedback template
- website/public signal metadata
- review queue/advisor queue/review interface
- consolidation promotion path
- continuity storage indicators
- `.weslr` path authority
- OCW/Ubuntu storage-access limits

The purpose is to make public-pilot storage safe enough to design later implementation fixes without reading raw private records, processing queues, exposing private content, or creating runtime/public-launch authority.

## 3. Readiness Basis

- Public pilot readiness is `not_ready_confirmed`.
- The first-30 pilot remains directionally useful but blocked.
- Existing surfaces are not safe for public pilot use until governance and safety fixes exist.
- This boundary precedes implementation fixes.

The reviewed audit found blocker-level risk around consent, privacy, retention, deletion/revocation, queue output, promotion influence, `.weslr` path authority, and OCW/Ubuntu storage access.

## 4. Governance Object

Future object:

`WeslrPublicPilotStoragePrivacyRetentionGovernanceBoundaryV1`

It must be:

- metadata-only
- JSON-safe
- source-scoped
- owner/requester/target scoped
- storage-surface scoped
- consent-gated
- redaction-gated
- retention-gated
- deletion/revocation-aware
- queue-output-limited
- `.weslr`-excluding by default
- OCW-access-limited
- promotion-gated
- fail-closed
- authority-denying by default

It is not an implementation, storage writer, queue processor, database reader, export tool, public launch mechanism, OCW management grant, or runtime/final-answer authority surface.

## 5. Required Fields

`WeslrPublicPilotStoragePrivacyRetentionGovernanceBoundaryV1` requires:

- `schema_version`
- `governance_boundary_id`
- `created_at_label`
- `updated_at_label`
- `freshness_label`
- `surface_scope`
- `storage_scope`
- `owner_scope`
- `requester_scope`
- `target_scope`
- `consent_policy_metadata`
- `privacy_policy_metadata`
- `redaction_policy_metadata`
- `retention_policy_metadata`
- `deletion_policy_metadata`
- `revocation_policy_metadata`
- `queue_output_policy_metadata`
- `promotion_isolation_metadata`
- `ocw_access_policy_metadata`
- `dot_weslr_policy_metadata`
- `public_feedback_policy_metadata`
- `pilot_logger_policy_metadata`
- `suggestion_storage_policy_metadata`
- `review_queue_policy_metadata`
- `validation_status`
- `blocked_reason_labels`
- `next_safe_steps`
- `denied_authority`

All fields are metadata-only. Missing scope, missing policy metadata, missing denied-authority fields, true denied-authority fields, raw/private content, raw JSON/database rows, non-JSON-safe metadata, or authority-bearing claims must fail closed.

## 6. Consent Policy

Future governance must define:

- consent before contact storage
- consent before feedback storage
- consent before suggestion storage
- consent before project-review submission storage
- consent before upstream/public sharing
- consent before testimonial use
- consent before OCW/operator access to pilot data
- consent scope labels
- revocation support
- missing consent blocks public pilot use

Consent must be scoped by owner/requester/target, surface, storage category, submission type, visibility, retention class, operator/OCW access, and intended use. Consent for feedback storage must not imply testimonial use. Consent for local/private review must not imply upstream/public sharing. Consent for metadata capture must not imply raw-content storage.

## 7. Privacy Policy

Future governance must require:

- raw private content excluded by default
- project/private data excluded by default
- contact data minimized
- secrets/customer data blocked
- `.weslr` excluded by default
- logs/traces/caches excluded unless separately governed
- cross-user reuse blocked
- private pilot data not visible to OCW by default
- public testimonials blocked without consent
- raw feedback not used as public claim material

Private pilot data remains private by default even when it is referenced by metadata, queue summaries, review requests, or storage indicators. Public-readiness, product-readiness, intelligence, Turing, certification, testimonial, or endorsement claims must not be inferred from stored feedback.

## 8. Redaction Policy

Future governance must require:

- redaction before operator review
- redaction before upstream/public use
- redaction before reports
- nested redaction, not only top-level stripping
- safe summaries only
- raw JSON/DB rows blocked from reports
- pilot logger CLI/display must be governed before use
- suggestion free text must be redacted/minimized before review

Redaction policy must classify raw free text, contact fields, user/session identifiers, project details, customer/industrial details, logs/traces/caches, queue snapshots, and nested dictionaries/lists as unsafe by default. Safe summaries must preserve only minimal evidence labels, counts, storage category labels, risk labels, and next-step labels.

## 9. Retention Policy

Future governance must require:

- retention duration labels
- storage category labels
- default retention limits
- retention enforcement required before public pilot use
- docs-only retention is insufficient
- stale records must not remain indefinitely
- backups/exports require separate governance

Retention metadata must distinguish public feedback, private feedback, suggestions, contact data, project-review submissions, pilot logger events, red-team/intervention events, review queue records, advisor queue records, public-signal metadata, contract-observation metadata, and continuity indicators. Any retained category must have a visible duration label and later enforceable implementation path before public pilot use.

## 10. Deletion / Revocation Policy

Future governance must require:

- deletion request handling
- revocation of consent
- contact removal
- feedback removal
- suggestion removal
- project-review removal
- queue item removal or suppression
- purge/anonymization requirements
- deletion proof/receipt metadata
- no public pilot use until deletion/revocation behavior is designed and later implemented

Deletion and revocation must not depend on reading raw records into reports. Future implementations should support safe lookup, suppression, anonymization, and deletion receipt metadata without exporting private content. Backup/export deletion requires separate reviewed governance.

## 11. Queue / Review Output Policy

Future governance must require:

- queues must not expose private data
- queues must not create public testimonials
- suggestions must not automatically become roadmap
- project reviews must not become official WESLR behavior
- queue outputs must not create upstream submissions
- queue outputs must not influence promotion without review
- queue outputs must not bypass release gates
- queue outputs must not create runtime/final-answer behavior

Queue and review outputs may only become safe metadata summaries until a later implementation lane creates validated controls. Review queue/advisor queue/review interface outputs must preserve operator-review boundaries and deny public launch, public claims, source edits, runtime behavior, final-answer behavior, and official core promotion.

## 12. Promotion Isolation Policy

Future governance must require:

- public feedback cannot directly feed consolidation promotion
- suggestions cannot become promoted behavior without review/operator/release gates
- promotion helpers must be isolated from public pilot storage by default
- no feedback-to-runtime path
- no feedback-to-final-answer path
- no automatic official core promotion

Promotion paths must treat public pilot feedback as untrusted input. Feedback or suggestions may produce only review candidates after consent, redaction, and operator review. Any official-core promotion requires separate reviewed implementation, release gates, and explicit operator authority.

## 13. `.weslr` Path Authority Policy

Future governance must require:

- public pilot flows must not read/write `.weslr`
- advisor queue defaults involving `.weslr` must be blocked for public pilot flows unless separately authorized
- consolidation promotion defaults involving `.weslr` must be blocked for public pilot flows unless separately authorized
- `.weslr` access requires separate reviewed lane

Public pilot governance must fail closed on `.weslr` paths, home-directory `.weslr` paths, implicit defaults that resolve to `.weslr`, path traversal into `.weslr`, or any policy that requires `.weslr` read/write authority.

## 14. OCW / Ubuntu Access Policy

Future governance must require:

- OCW may manage deployment only under operator-approved boundaries
- OCW must not access private pilot/suggestion/review storage by default
- OCW must not export pilot data
- OCW must not process queues
- OCW must not restart/deploy based on private feedback without approval
- OCW actions must be reportable/loggable in future implementation
- OCW remains tool/deployment agent, not WESLR identity
- release gates cannot be bypassed

OCW/Ubuntu management authority must remain separate from pilot data authority. Deployment/service access must not imply private storage access, queue processing, feedback export, release-gate bypass, public launch, or WESLR identity authority.

## 15. Public Feedback / GitHub Template Policy

Future governance must require:

- privacy warning before public issue submission
- no secrets/customer data warning
- no private project data warning
- testimonial consent separate from feedback submission
- public GitHub issue feedback must not imply public endorsement
- public issue feedback must not imply product readiness

Public feedback is public by platform behavior but still requires clear scope. Public issue submission must not silently authorize reuse as marketing, testimonial, roadmap, official WESLR behavior, upstream submission, or product-readiness evidence.

## 16. Suggestion Storage Policy

Future governance must require:

- contact email optional and consent-gated
- free-text fields minimized/redacted
- request/problem/note fields treated as private by default
- deletion/revocation supported
- no public use without consent
- no roadmap/promotion without review

Suggestion records must be private by default. Contact and free-text fields require minimization, redaction, retention limits, deletion/revocation handling, and safe-summary review before any public pilot use.

## 17. Pilot Logger Policy

Future governance must require:

- user/session identifiers minimized or hashed
- arbitrary details treated as private by default
- CLI/display of raw events blocked before governance/fixes
- retention/deletion required
- red-team/intervention/user events treated as sensitive
- no raw display in reports

Pilot logger storage/display is a blocker until governed. Reports may use only safe metadata labels, counts, and risk summaries. Raw events, raw details, raw identifiers, raw intervention records, and raw red-team records must not appear in reports.

## 18. Validation Status Labels

Allowed validation labels:

- `design_only`
- `public_pilot_not_ready`
- `blocked_missing_consent_policy`
- `blocked_missing_privacy_policy`
- `blocked_missing_retention_policy`
- `blocked_missing_deletion_policy`
- `blocked_missing_revocation_policy`
- `blocked_raw_private_content`
- `blocked_raw_json_or_db_rows`
- `blocked_dot_weslr_path`
- `blocked_ocw_storage_access`
- `blocked_queue_output_risk`
- `blocked_promotion_risk`
- `blocked_public_testimonial_risk`
- `ready_for_boundary_review`

A future validator should allow `ready_for_boundary_review` only when required metadata exists, denied authority is complete/false, and no fail-closed condition is present.

## 19. Denied Authority

All values below are required false:

```yaml
permits_source_edits: false
permits_runtime_changes: false
permits_queue_processing: false
permits_database_row_reads: false
permits_database_writes: false
permits_raw_json_reads: false
permits_private_feedback_dump: false
permits_contact_export: false
permits_email_sending: false
permits_upstream_submission: false
permits_public_testimonials: false
permits_ocw_management_changes: false
permits_ocw_storage_access: false
permits_ubuntu_deployment_changes: false
permits_service_restart: false
permits_provider_calls: false
permits_model_calls: false
permits_search_calls: false
permits_advisor_calls: false
permits_dot_weslr_reads: false
permits_dot_weslr_writes: false
permits_final_answer_generation: false
permits_public_launch: false
permits_product_readiness_claims: false
permits_intelligence_claims: false
permits_turing_claims: false
permits_certification_claims: false
```

## 20. Fail-Closed Rules

Future validation must block if:

- consent policy missing
- privacy policy missing
- redaction policy missing
- retention policy missing
- deletion/revocation policy missing
- raw private content included
- raw JSON/DB rows included
- contact export implied
- public testimonial implied without consent
- upstream submission implied without consent
- queue output can influence promotion
- queue output can bypass release gate
- `.weslr` path use implied
- OCW storage access implied
- service restart/deploy implied
- runtime/chat/voice/final-answer behavior implied
- public launch/product/intelligence/Turing/certification claim implied
- denied-authority field missing or true
- non-JSON-safe metadata appears

Fail-closed means no public pilot use, no queue processing, no promotion, no public claim, no OCW storage access, and no implementation authority from the boundary object.

## 21. Future Synthetic Tests Required

Future implementation/review should include synthetic-only tests for:

- valid governance metadata
- missing consent policy
- missing privacy policy
- missing retention policy
- missing deletion policy
- missing revocation policy
- raw private content marker
- raw JSON marker
- DB row marker
- contact export marker
- public testimonial marker
- upstream submission marker
- `.weslr` marker
- OCW storage access marker
- queue promotion influence marker
- release gate bypass marker
- service restart marker
- runtime/final-answer marker
- public launch/product/intelligence/Turing/certification claim marker
- true denied-authority field
- missing denied-authority field
- non-JSON-safe metadata

Synthetic tests must not read raw private/user records, raw JSON records, DB rows, `.weslr`, queues, logs, traces, caches, exports, submissions, or provider/model/search/advisor outputs.

## 22. Relationship To Existing Surfaces

This boundary governs existing surfaces; it does not duplicate them:

- `weslr/suggestion_box.py`
- `weslr/pilot_signal_logger.py`
- `.github/ISSUE_TEMPLATE/feedback_request.yml`
- `weslr/website_signal_integration.py`
- `weslr/public_signal_store.py`
- `weslr/contract_observation.py`
- `weslr/advisor_review_queue_persistence.py`
- `weslr/review_interface.py`
- `weslr/consolidation_promotion.py`
- OCW handoff docs/contracts
- continuity storage indicators

The boundary is a governance layer over existing implementation surfaces. It must not create parallel forms, queues, loggers, storage paths, launch flows, OCW authority, runtime behavior, final-answer behavior, or promotion paths.

## 23. Recommended Later Lanes

After review/context alignment, possible later lanes:

- `IMPLEMENT_PUBLIC_PILOT_STORAGE_PRIVACY_SAFETY_FIXES_V1`
- `QUARANTINE_PUBLIC_PILOT_USER_DATA_STORAGE_SURFACES_V1`
- `REVIEW_PUBLIC_PILOT_OCW_DEPLOYMENT_ACCESS_BOUNDARY_V1`
- `DESIGN_PUBLIC_PILOT_USER_EXPERIENCE_REVIEW_PLAN_V1`

Implementation and quarantine lanes must wait until this boundary is reviewed and aligned unless the operator explicitly authorizes emergency quarantine.

## 24. Decision

`public_pilot_storage_privacy_retention_governance_boundary_design_ready_for_review`

## 25. Next Lane

`REVIEW_PUBLIC_PILOT_STORAGE_PRIVACY_RETENTION_GOVERNANCE_BOUNDARY_V1`
