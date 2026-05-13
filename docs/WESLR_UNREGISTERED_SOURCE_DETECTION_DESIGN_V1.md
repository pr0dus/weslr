# WESLR Unregistered Source Detection Design V1

## Status

- design_only
- unregistered_source_detection
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change
- no_runtime_integration
- no_queue_writes
- no_external_model_calls
- no_auto_registration

## Purpose

Design a future local detection pass that identifies WESLR modules or artifacts that appear capable of generating, suggesting, speaking, advising, remembering, routing, reviewing, self-reviewing, self-improving, or acting, but do not have provenance source registry entries.

This design identifies modules without provenance source registry entries so they can be reviewed later. It does not implement scanner behavior, mutate the registry, write queues, or change runtime behavior.

## Inputs

Future detection may inspect:

- in-memory provenance source registry seed
- future persisted registry entries
- Python modules
- docs
- tests
- capability registry
- advisor prompt templates
- queue schemas
- voice/proactive modules
- suggestion/proposal modules
- self-review/self-improvement modules
- output provenance envelopes when available

## Detection signals

Future detection signal types may include:

- module name suggests output production
- module contains functions that generate suggestions
- module contains voice/proactive/ambient behavior
- module contains advisor/review/queue behavior
- module contains memory write behavior
- module contains routing/decision behavior
- module contains self-review/self-improvement behavior
- doc references source but registry lacks entry
- test references source but registry lacks entry
- provenance envelope references unknown source
- seed entry exists but docs/tests are missing or stale

These signals are review signals only. They are not evidence of correctness, truth, soundness, activation readiness, or official score.

## Unknown-source policy

If an unregistered or unknown source is detected:

- mark authority as unknown
- require operator review
- do not guess provenance
- do not auto-register
- do not auto-activate
- do not mutate memory
- do not perform runtime action
- create future local-scan finding or review queue suggestion only after separately approved helper phase

Unknown-source handling must preserve uncertainty. The detector must not convert a guess into a registry entry, queue write, memory mutation, runtime action, or active capability.

## Finding types

Future finding categories:

- `unregistered_source_candidate`
- `missing_source_registry_entry`
- `stale_source_registry_entry`
- `source_without_tests`
- `source_without_docs`
- `unknown_source_in_provenance`
- `unregistered_voice_or_proactive_source`
- `unregistered_self_improvement_source`
- `source_authority_boundary_missing`
- `source_activation_policy_inconsistent`

Findings are local review artifacts only until a separately approved helper or queue-mapping phase exists.

## Review queue integration

Detection findings should later map into advisor-review queue items through existing local-scan and queue mapping helpers.

This phase must not write queues. It does not create queue files, append queue events, update queue status, or call queue writer helpers. Queue integration remains a future mapping design/helper phase with explicit operator approval.

## Self-improvement support

Detection must cover WESLR-self-review-suggested and self-improvement-proposed modules.

Self-improvement modules require registry entry, validation, tests, and operator approval before activation. They must not become active from detection alone. Detection may only identify that a self-review or self-improvement source appears registry-required and needs review.

No self-improvement candidate may bypass the registry lifecycle, validation requirements, tests, authority boundary review, or operator approval.

## LLM Advisor integration

LLM Advisor Mode may later review unregistered-source findings and suggest missing entries/tests.

Advisor output is non-authoritative proposal input only. It cannot auto-register sources, certify provenance, activate modules, select answers, claim truth/soundness, claim official score, write queues, mutate memory, or change runtime behavior.

This design phase makes no model/advisor calls and has no external model calls.

## Institution/client extension

Institution/client modules, local LLMs, on-premise/air-gapped models, industrial adapters, and private workflows must also be detectable as registry-required sources when they can generate/suggest/act.

Private or institution-specific sources should be detected by source-relevant behavior, not by public module assumptions. They must follow the same registry entry, authority boundary, validation, tests, and operator review requirements.

Industrial adapters and private workflows remain design-covered only here. This document does not add TIA/C#/industrial implementation, scanner behavior, registry persistence, runtime wiring, or external calls.

## What detection must not do

- no auto-registration
- no automatic fixes
- no queue writes in this phase
- no runtime/chat/voice wiring
- no model/advisor calls
- no memory mutation
- no daemon/cron/scheduler
- no answer selection
- no truth/soundness authority
- no official score
- no provenance guessing
- no auto-activate behavior
- no registry persistence
- no persistent registry file creation
- no real queue file creation
- no runtime integration
- no behavior change

## Future phases

- APPROVE_UNREGISTERED_SOURCE_DETECTION_SCHEMA_ONLY
- APPROVE_UNREGISTERED_SOURCE_DETECTION_HELPERS_ONLY
- APPROVE_PROVENANCE_SOURCE_REGISTRY_LOCAL_SCAN_HELPERS_ONLY
- APPROVE_SOURCE_REGISTRY_REVIEW_QUEUE_MAPPING_ONLY
- APPROVE_VOICE_SOURCE_ATTRIBUTION_DESIGN_ONLY
- APPROVE_SELF_USE_QUERY_SURFACE_DESIGN_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
