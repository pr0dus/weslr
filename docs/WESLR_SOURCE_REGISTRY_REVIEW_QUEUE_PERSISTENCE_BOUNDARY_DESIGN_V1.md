# WESLR Source Registry Review Queue Persistence Boundary Design V1

## Status

- design_only
- persistence_boundary_design
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change
- no_queue_writes
- no_registry_persistence
- no_external_model_calls

## Purpose

Design the future safe boundary for persisting advisor-review queue proposals that originate from unregistered-source detection findings.

This phase defines when source-registry review proposals may later use existing generic advisor-review queue persistence helpers. It does not implement writer behavior, create queue files, persist registry data, scan the repository, or change runtime behavior.

## Current pipeline

Current in-memory chain:

`candidate metadata → UnregisteredSourceFinding → AdvisorReviewQueueItem proposal`

The current chain remains purely in-memory. Mapping helpers may create proposal objects, but they do not write queue files and do not persist registry state.

Future chain, only after separate approval:

`AdvisorReviewQueueItem proposal → validated persistence event → append-only queue storage`

The future chain requires a separately approved writer phase and must pass through validation, path policy, redaction, and operator-review gates.

## Boundary principle

Source-registry review proposals must remain in-memory until a separate writer phase is approved. Persistence must never be automatic.

A proposal object is not a queue write. A detection finding is not a registry entry. A mapped queue proposal is not approval, activation, persistence, or execution.

## Preconditions before future persistence

A future writer phase must require:

- valid `UnregisteredSourceFinding`
- valid `AdvisorReviewQueueItem`
- valid `AdvisorQueuePersistenceEvent`
- explicit path policy
- append-only storage
- redaction before write
- operator-review required
- advisor calls disabled
- no runtime/config/memory mutation
- no automatic activation
- no self-improvement activation

The writer boundary must reject unsafe flags, invalid queue items, invalid persistence events, unapproved paths, missing redaction, and any attempt to combine persistence with activation or runtime changes.

## Allowed future persistence mode

When separately approved, persistence may only create append-only review events such as:

- queue item created
- status update requested
- operator decision recorded

These events are records for review workflow only. They must not approve themselves, modify registry entries, activate sources, or invoke advisors.

## What must never happen automatically

- source auto-registration
- source activation
- self-improvement activation
- prompt mutation
- provider activation
- runtime/config mutation
- memory mutation
- advisor/model call
- queue self-approval
- truth/soundness/score claim

## Dry-run first

Future implementation should first support dry-run/no-write diagnostics:

- show what would be persisted
- validate all objects
- produce redacted summary
- write nothing

Dry-run output should be count-based and redacted. It should identify validation errors and unsafe boundaries before any queue file writer exists.

## Test path policy

Future tests may use temp paths only.

Real `.weslr/advisor_review_queue.jsonl` must not be created unless a later explicit real-write phase is approved.

Tests for boundary behavior should verify no real queue file is created, no persistent registry file is created, and no runtime/config/model side effects occur.

## Institution/client policy

Institution deployments may:

- require local-only queue persistence
- require admin approval before status changes
- restrict source-registry review writes by role
- require air-gapped/on-prem storage
- require manual export/import

Institution/client deployments may also require stricter retention, redaction, audit, and role-based write policies before any queue persistence is enabled.

## LLM Advisor relation

Advisor may later review persisted suggestions only after operator-approved advisor call flow. Persistence itself must not call advisors.

Persisting a queue proposal does not grant advisor authority. Advisor output remains non-authoritative proposal input and must not select answers, claim truth/soundness, claim official score, or mutate runtime behavior.

## Non-goals

- no implementation in this phase
- no writer helpers
- no queue file creation
- no scanner automation
- no registry persistence
- no runtime/chat/voice wiring
- no model/advisor calls
- no memory mutation
- no source activation
- no self-improvement activation
- no answer selection
- no truth/soundness authority
- no official score

## Future phases

- APPROVE_SOURCE_REGISTRY_REVIEW_QUEUE_PERSISTENCE_DRY_RUN_HELPERS_ONLY
- APPROVE_SOURCE_REGISTRY_REVIEW_QUEUE_PERSISTENCE_TEMP_PATH_HELPERS_ONLY
- APPROVE_SOURCE_REGISTRY_REVIEW_QUEUE_REAL_WRITE_POLICY_DESIGN_ONLY
- APPROVE_PROVENANCE_SOURCE_REGISTRY_LOCAL_SCAN_HELPERS_ONLY
- APPROVE_VOICE_SOURCE_ATTRIBUTION_DESIGN_ONLY
- APPROVE_SELF_USE_QUERY_SURFACE_DESIGN_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
