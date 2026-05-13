# WESLR Provenance Source Registry Lifecycle Design V1

## Status

- design_only
- source_registry_lifecycle
- self_improvement_aware
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change
- no_runtime_integration
- no_external_model_calls
- no_self_activation

## Purpose

Design a living provenance source registry lifecycle so WESLR can track which subsystem generated, suggested, spoke, advised, remembered, routed, reviewed, self-suggested, or acted.

This phase defines lifecycle rules only. It does not implement registry behavior, create registry files, create scanners, write queues, activate self-improvement, wire runtime/chat/voice/proactive outputs, call external models, mutate memory, or change configuration.

## Core principle

The registry is not a fixed final list.

It is a versioned registration system that future WESLR modules must extend.

Any future WESLR module that can generate, suggest, speak, advise, remember, decide, route, review, self-improve, or act must register a provenance source entry before being considered production-safe.

A source registry entry is not authority by itself. It is an operator-reviewable contract describing what a subsystem is allowed to emit, what it is forbidden to emit, which lifecycle state it occupies, which tests/docs support it, and which approval path made it eligible for production use.

## Self-improvement principle

The registry lifecycle must cover not only human-added modules, but also future WESLR-suggested or WESLR-self-improvement-derived modules.

Any source/module/capability proposed by:

- WESLR itself
- local scan
- advisor review
- self-review
- future approved self-improvement workflow
- operator
- institution/client

must require a provenance source registry entry before it can become production-safe or active.

Hard boundary: Self-suggested or self-improvement-derived modules must not become active automatically. They must remain proposal/input until validated, tested, and operator-approved.

WESLR-self-suggested modules and self-improvement-derived modules therefore enter the same governance lane as any other extension: proposal, review, validation, tests, operator decision, then explicit activation if approved. No self-added capability may bypass registration, provenance envelope compatibility, or operator approval.

## Source entry concept

Future source entries should define:

- `source_id`
- `display_name`
- `module_path`
- `source_type`
- `authority_boundary`
- `allowed_outputs`
- `forbidden_outputs`
- `llm_assisted`
- `advisor_assisted`
- `operator_review_required`
- `introduced_in_commit`
- `last_reviewed_commit`
- `capability_scope`
- `status`
- `owner`
- `related_docs`
- `related_tests`

Self-improvement lifecycle fields:

- `proposed_by`
- `origin_type`
- `approval_status`
- `operator_decision`
- `created_from_proposal_id`
- `created_from_advisor_review_id`
- `created_from_queue_item_id`
- `validation_required`
- `tests_required`
- `activation_allowed`

These fields make the registry a lifecycle artifact, not a static catalog. They preserve where a source came from, why it exists, what reviewed it, and whether activation is explicitly allowed.

## Origin categories

Registry source entries should support these origin categories:

- `operator_added`
- `institution_added`
- `advisor_suggested`
- `local_scan_suggested`
- `weslr_self_review_suggested`
- `self_improvement_proposed`
- `unknown`

Origin records do not confer authority. They explain the source of a proposal or entry so later review can distinguish operator-added modules, institution/client extensions, advisor-suggested modules, local-scan-suggested modules, WESLR-self-review-suggested modules, and self-improvement-proposed modules.

## Approval/status categories

Lifecycle approval statuses:

- `proposed`
- `under_review`
- `approved`
- `rejected`
- `active`
- `deprecated`
- `blocked`
- `unknown`

Registry source status values:

- `active`
- `experimental`
- `deprecated`
- `blocked`
- `unknown`

Approval and activation are separate. A proposal may be approved for implementation but not active. A source may be experimental but not production-safe. `activation_allowed` must remain false until required provenance, validation, tests, and operator approval are present.

## Source types

Source entries should classify source type as one of:

- `chat_surface`
- `voice_surface`
- `ambient_loop`
- `proactive_suggestion`
- `advisor_review`
- `capability_guidance`
- `memory_capture`
- `state_checkpoint`
- `teaching_explanation`
- `operator_cli`
- `external_provider`
- `institution_extension`
- `self_review`
- `self_improvement_candidate`
- `unknown`

Source type helps the provenance envelope and self-use query surfaces explain which part of WESLR generated an output and which safety boundary applies.

## Unknown/unregistered source policy

If an output references an unregistered source:

- mark source as `unknown` or `unregistered`
- authority must be `unknown`
- operator review required
- no truth/soundness authority
- no automatic memory write
- no automatic runtime action
- no automatic activation
- create future review suggestion, not automatic fix

Unknown sources must not be normalized into trusted sources by guessing. If provenance is incomplete, WESLR should say the source is unknown and route the gap into a review/proposal lane when that lane is approved.

## Registration contract

Any future WESLR module that can generate, suggest, speak, advise, remember, decide, route, self-review, self-improve, or act must register a provenance source entry before being considered production-safe.

This applies equally to:

- human-coded modules
- institution/client extensions
- advisor-suggested modules
- local-scan-suggested modules
- WESLR-self-review-suggested modules
- self-improvement-derived modules

The registration contract requires at minimum: source identity, source type, authority boundary, allowed outputs, forbidden outputs, LLM/advisor assistance disclosure, operator-review requirement, related docs/tests, approval status, activation status, and provenance envelope compatibility.

## Self-improvement workflow connection

Future safe self-improvement flow:

```text
WESLR notices a gap → creates suggestion/proposal → optional LLM advisor review → tests/design created → operator approves → implementation happens → new source registry entry required → provenance envelope uses that source
```

No self-improvement-derived capability may activate without:

- registry entry
- provenance envelope compatibility
- validation
- tests
- operator approval
- rollback/review path

Self-improvement proposals connect to provenance/source registry entries through `created_from_proposal_id`, `created_from_advisor_review_id`, `created_from_queue_item_id`, `origin_type`, `approval_status`, and `activation_allowed`. This prevents self-improvement from creating hidden or unattributed authority.

## Future local-scan support

Future local scan checks should detect:

- module produces outputs but has no source registry entry
- source entry exists but has no tests
- source entry has stale docs
- source entry authority boundary missing
- source entry lacks voice/proactive attribution rules
- source entry added by institution/client but not reviewed
- self-suggested module lacks provenance registration
- self-improvement proposal lacks source lifecycle fields
- source entry activation status is inconsistent with approval status

Local scans should report findings as diagnostics or review suggestions only. They must not create active entries, mutate runtime behavior, write queues without approval, or activate self-improvement-derived sources.

## Review queue integration

Missing/stale/unsafe source registry coverage should become review queue suggestions, not automatic changes.

Examples:

- unregistered output source detected
- self-improvement candidate lacks source entry
- advisor-suggested module lacks tests
- voice/proactive source lacks attribution rule
- institution extension lacks authority boundary

Review queue suggestions should preserve provenance, identify the detection source, carry operator-review requirements, and remain non-authoritative until validated and approved. This design does not write queues.

## LLM Advisor integration

LLM Advisor Mode may review registry coverage and suggest:

- missing entries
- missing tests
- missing authority boundaries
- wording-risk improvements
- source lifecycle problems
- provenance coverage gaps
- self-improvement registration gaps

Hard boundary: LLM advisor output is non-authoritative proposal input only. It cannot become truth, memory, runtime behavior, policy, or active registry state without validation and operator approval.

Advisor suggestions must preserve model/provider provenance when used later. They may inform proposal candidates, tests, docs, or review queue suggestions, but they cannot create registry authority or activate a source.

## Institution/client extension

Institutions and clients may add private source entries for:

- local LLMs
- on-premise models
- air-gapped models
- domain modules
- industrial adapters
- internal tools
- private workflows

These entries remain governed, reviewable, and subject to provenance/approval requirements. Institution/client private modules should be able to remain private while still carrying source IDs, authority boundaries, status, owner, related tests/docs, and activation review data.

## Versioning and lifecycle

Entries should support:

- source schema version
- introduced commit
- last reviewed commit
- related tests
- related docs
- status
- owner
- review cadence

Registry lifecycle must be revisited when:

- WESLR gains a new module
- WESLR gains a new output channel
- WESLR gains new advisor/provider integration
- WESLR gains new memory/governance behavior
- WESLR gains self-review/self-improvement capability
- institution/client adds private module
- provenance diagnostics find unknown sources

Versioning should make source lifecycle review auditable across commits and institutional deployments. A registry entry should be updated or re-reviewed when its source behavior, authority boundary, output channel, ownership, docs, tests, or activation state changes.

## Safety boundaries

Forbid:

- hidden LLM authority
- provenance guessing
- unregistered voice/proactive output
- unregistered self-improvement output
- hidden memory mutation
- hidden queue writes
- hidden runtime actions
- automatic activation
- automatic self-improvement deployment
- answer selection
- truth/soundness authority
- official score claims
- raw sensitive content storage by default

Additional boundaries:

- An unregistered source cannot be production-safe.
- Advisor-suggested entries cannot become active without validation and operator approval.
- Local-scan findings cannot mutate the registry directly.
- Self-review may notice gaps but may not grant itself authority.
- Institution/client extensions remain governed even when private.

## Non-goals

- no implementation in this phase
- no registry file/schema yet
- no runtime integration
- no source scanner implementation
- no queue writes
- no voice/chat wiring
- no model calls
- no self-improvement implementation
- no automatic activation

This document does not create registry files, dataclasses, loaders, scanners, queue writers, daemon loops, runtime routers, chat/voice/proactive integrations, model/advisor calls, OpenClaw config changes, parser/normalizer/solver changes, MCQ/scoring changes, or TIA/C#/industrial changes.

## Future phases

Possible next operator decisions:

- `APPROVE_PROVENANCE_SOURCE_REGISTRY_SCHEMA_ONLY`
- `APPROVE_PROVENANCE_SOURCE_REGISTRY_INITIAL_SEED_ONLY`
- `APPROVE_UNREGISTERED_SOURCE_DETECTION_DESIGN_ONLY`
- `APPROVE_PROVENANCE_SOURCE_REGISTRY_LOCAL_SCAN_HELPERS_ONLY`
- `APPROVE_SELF_IMPROVEMENT_SOURCE_REGISTRATION_DESIGN_ONLY`
- `APPROVE_VOICE_SOURCE_ATTRIBUTION_DESIGN_ONLY`
- `APPROVE_SELF_USE_QUERY_SURFACE_DESIGN_ONLY`
- `REQUEST_REVISION`
- `REJECT_OR_DEFER`

Recommended next move is schema-only design for provenance source registry entries and lifecycle statuses. Do not implement scanners, queue writes, runtime integration, voice/chat wiring, advisor calls, or self-improvement activation yet.
