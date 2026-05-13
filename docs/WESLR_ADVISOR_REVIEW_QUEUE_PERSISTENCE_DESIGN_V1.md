# WESLR Advisor Review Queue Persistence Design V1

## Status

- design_only
- persistence_design
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change
- no_queue_writes
- no_external_model_calls

## Purpose

Design future safe persistence for `AdvisorReviewQueueItem` records created from local-scan advisor-review mapping helpers.

This document is design only. It does not implement persistence, write queue files, create database files, create schedulers, call advisors or external models, mutate prompts, activate providers, change runtime/config state, select answers, claim truth/soundness, or claim an official score.

## Persistence Principle

Future persistence must store review suggestions for operator review only. Persisted records are non-authoritative review artifacts. They must not trigger advisor calls, automatic implementation, prompt mutation, provider activation, runtime changes, memory mutation, governance overrides, answer selection, truth/soundness claims, or official score claims.

Persistence should preserve traceability from local signal to `AdvisorReviewQueueItem` to operator decision, while keeping authority at the operator/governance layer.

## Proposed Storage Model

Recommended future model:

- redacted JSONL or JSON queue for advisor review items
- append-only event log for creation events
- separate status/update records for status transitions, or explicit safe status transition events
- no raw benchmark text storage
- no secrets, API keys, or tokens
- no private user data by default
- all records are validated before persistence
- canonical serialization for persisted records
- content hash for tamper-evident audit trails
- provenance fields for source scan/report/finding references
- original suggestion content is never silently modified

A JSONL event-log shape is preferred for creation and update events because it naturally supports append-only audit trails. A compact JSON queue may be acceptable for read-only projections generated from the event log, but the projection must not be treated as the authority if it can be regenerated.

## Suggested Future Path Policy

A safe future location could be:

- `.weslr/advisor_review_queue.jsonl`

This path follows the repository's existing `.weslr/*.jsonl` queue convention, while separating advisor-review persistence from `pending_messages_queue.py` delivery messages and from legacy root-level `review_queue.json` / `export_queue.json` artifact lifecycle queues.

Path policy for any future writer:

- queue root must be fixed and repository-local
- reject absolute user-controlled paths
- reject `..` traversal
- reject symlink escapes
- reject user-controlled filenames
- do not create this file until a later implementation approval

## Existing Queue Pattern Recommended

Existing patterns observed:

- `weslr/pending_messages_queue.py` uses `.weslr/pending_messages.jsonl` and `.weslr/pending_messages_consumed.jsonl`; enqueue appends JSONL records, while consume rewrites pending entries and appends consumed entries.
- `review_queue.json` and `export_queue.json` are legacy root-level JSON arrays used by artifact/governed-cycle documentation and dashboard surfaces.
- `weslr/capability_discovery/review.py` exposes mutable review-status actions through a store/API layer rather than direct queue-file hand edits.

Safest pattern to reuse later: repository-local `.weslr/*.jsonl` with append-only creation events and separate explicit status transition events. Avoid directly mutating legacy `review_queue.json` or `export_queue.json` for advisor-review persistence unless a later operator decision explicitly aligns those surfaces.

## Record Lifecycle

Future records may represent these lifecycle states:

- created
- pending_review
- accepted
- rejected
- deferred
- archived

Creation should append a creation event. Status changes should append status/update events. A reader may project the latest status, but the original creation event remains intact.

## Validation Before Write

Any future writer must validate before persistence:

- `AdvisorReviewQueueItem`
- `AdvisorReviewQueueSafetyFlags`
- redaction policy
- operator approval remains required
- advisor calls remain disabled unless separately approved
- advisor_call_mode remains safe unless separately approved
- no unsafe free-text indicators
- no raw benchmark text
- no secrets, API keys, or tokens
- no private user data by default
- no answer key or official-score content
- no execution or implementation intent

If validation fails, no persistence event is written.

## Read/List Behavior

A future reader may:

- list pending review items
- summarize counts by status, suggestion type, source, and risk level
- load item by id
- return redacted summaries only
- skip or quarantine malformed records without deleting them
- preserve event order for audit review

Read/list behavior must not call models, advisors, runtime APIs, providers, prompt mutation surfaces, or governance override paths.

## Status Update Behavior

A future updater may:

- change review status only through allowed transitions
- record operator decision
- record reviewer identity/role when available
- record timestamp and reason
- preserve audit trail
- never modify original suggestion content silently
- append status/update events rather than overwriting creation events

Allowed transitions should be explicit and conservative, for example:

- created → pending_review
- pending_review → accepted
- pending_review → rejected
- pending_review → deferred
- pending_review → archived
- deferred → pending_review
- accepted → archived
- rejected → archived

No status transition may imply implementation, model invocation, provider activation, prompt mutation, runtime/config changes, memory mutation, answer selection, truth/soundness authority, or official score authority.

## What Persistence Must Not Do

Future persistence must not do any of the following:

- no external model calls
- no advisor calls
- no automatic implementation
- no prompt mutation
- no provider activation
- no runtime/config changes
- no memory mutation
- no governance override
- no answer selection
- no truth/soundness claim
- no official score
- no raw benchmark text storage
- no secrets/API keys/tokens
- no private user data by default
- no queue item self-approval
- no hidden background execution
- no cron/scheduler/daemon creation
- no direct OpenClaw config changes

## Tamper and Audit Policy

Future persistence should protect against queue item tampering by design:

- strict field allowlist
- canonical JSON serialization
- append-only event log
- per-event content hash
- optional chain hash for event order integrity
- explicit created_at / updated_at / operator_decision_at timestamps
- immutable creation records
- status transitions as separate events
- redaction-before-write
- validation errors returned without writing

These mechanisms are design requirements only in this phase.

## Institution/Client Policy

Institutions may choose storage location and policy later. The default recommendation is local-only repository storage under `.weslr/` until an institution-specific policy is approved.

Client deployment policy:

- air-gapped/on-prem deployments can keep the queue local only
- retention policy must be configurable later
- sensitive deployments may require manual export/import only
- multi-tenant deployments must isolate queue storage by institution/client/project
- regulated deployments may require encryption-at-rest and separate operator audit review
- no institution should receive automatic external transmission by default

## Non-Goals

This phase does not implement:

- persistence helpers
- queue file creation
- database creation
- queue readers or writers
- status update helpers
- cron/scheduler/daemon behavior
- advisor/model call flow
- prompt mutation
- provider activation
- runtime/config changes
- memory mutation
- governance override
- automatic implementation
- answer selection
- truth/soundness claim
- official score

## Future Phases

- APPROVE_ADVISOR_REVIEW_QUEUE_PERSISTENCE_SCHEMA_ONLY
- APPROVE_ADVISOR_REVIEW_QUEUE_PERSISTENCE_HELPERS_ONLY
- APPROVE_LOCAL_SCAN_ONLY_ADVISOR_REVIEW_ADAPTER_HELPERS_ONLY
- APPROVE_OPERATOR_APPROVED_ADVISOR_CALL_FLOW_DESIGN_ONLY
- APPROVE_OPENCLAW_CRON_TRIGGER_DESIGN_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
