# WESLR Voice Source Attribution Logging Design V1

## Status

- design_only
- voice_source_attribution_logging
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change
- no_runtime_integration
- no_voice_wiring
- no_log_writes
- no_external_model_calls
- no_queue_writes

## Purpose

Design how future WESLR voice/proactive attribution records will be created and logged so the system can later answer:

- “who said that?”
- “what generated that?”
- “was an LLM involved?”
- “what triggered it?”
- “why did you say that?”

from attribution/provenance records instead of guessing.

Future voice/proactive outputs must become attributable before they become trusted WESLR-owned behavior. Attribution logging must preserve source, trigger, model/provider involvement, authority boundary, and trace references without storing raw sensitive spoken text by default.

## Current state

- `VoiceSourceAttributionRecord` schema exists.
- `OutputProvenanceEnvelope` schema exists.
- `ProvenanceSourceEntry` schema/seed exists.
- No logging behavior exists yet.
- No voice wiring exists yet.
- No query surface exists yet.

## Logging lifecycle

Future lifecycle:

`voice/proactive output candidate → output provenance envelope → voice attribution record → validation → append-only attribution log → later query surface`

This phase must not implement that lifecycle. It only designs it.

The future lifecycle should require validation before a voice/proactive output is treated as attributable, and should keep the attribution record linked to output provenance, source registry metadata, and trace references.

## Pre-speak vs post-speak attribution

### Pre-speak attribution draft

A future pre-speak attribution draft is created before speaking.

It records:

- intended source
- trigger
- input channel and output channel
- model/provider involvement
- intended authority boundary
- intended truth class and confidence
- trace references available before speech

It must validate before the utterance is considered attributable.

### Post-speak attribution confirmation

A future post-speak attribution confirmation is created after speech/TTS succeeds or fails.

It records:

- whether speech was actually emitted
- whether TTS succeeded, failed, or was skipped
- TTS/STT engine used
- final trace reference
- linked output provenance identifier
- linked voice attribution record identifier

It does not store raw spoken text by default.

## Attribution log concept

The future attribution log should be:

- append-only attribution log
- local by default
- redacted by default
- raw spoken text disabled by default
- hash instead of raw text
- one record per spoken/proactive utterance
- safe for air-gapped/on-prem deployments
- governed by explicit path policy before real writes
- free of hidden model calls
- free of hidden memory writes
- unable to trigger runtime action from logging alone

Suggested future path, design only:

`.weslr/voice_source_attribution.jsonl`

Do not create this file.

No attribution log file is created in this phase. No logging helpers are implemented in this phase.

## Required linked records

Each future logged attribution should link when available:

- `VoiceSourceAttributionRecord`
- `OutputProvenanceEnvelope`
- `ProvenanceSourceEntry`
- trace reference
- model/provider record if LLM-assisted
- advisor review record if advisor-assisted
- review queue item if attribution is missing/weak

## Missing attribution handling

If a future voice/proactive output lacks attribution:

- do not guess
- mark source unknown
- operator review required
- no claim “I said it” without provenance
- no memory mutation
- no runtime action
- create future review suggestion only after a separately approved queue-mapping phase

Missing attribution should lower confidence and authority rather than invite reconstruction, ownership claims, or post-hoc provenance guessing.

## LLM/model disclosure

If an LLM/model contributed to the utterance:

- record `llm_assisted = true`
- record provider/model when available
- authority remains `voice_surface` or suggestion unless separately validated
- no hidden LLM authority
- no hidden model/provider involvement
- no implication that WESLR independently understood unless supported by non-LLM provenance

LLM-assisted voice should not become a system fact merely because it was spoken.

## Ambient/proactive disclosure

If ambient/proactive systems contributed:

- record source subsystem
- record trigger
- record whether it was observation/rule/model/advisor-assisted
- record confidence
- record operator-review requirement
- do not treat as autonomous decision without provenance and approval

Ambient/proactive disclosure must distinguish observation, local rule, model assistance, advisor assistance, and operator action when those distinctions are available.

## “Who said that?” dependency

A future “who said that?” query surface must depend on logged attribution records.

If records are missing, WESLR must say attribution is missing instead of guessing.

The query surface must not answer from memory, vibes, reconstructed intent, or hidden model assumptions.

## Review queue integration

Missing/weak attribution may later create review suggestions for:

- unattributed voice output
- missing provider/model record
- ambient output without trigger
- proactive output without provenance envelope
- voice source not in registry
- repeated attribution failures

This design phase must not write queues.

Review queue mapping requires a separate approved phase before any queue item can be created.

## Institution/client policy

Institution deployments may require:

- local-only attribution log
- air-gapped storage
- admin-controlled retention policy
- redacted export only
- role-restricted access to voice attribution records
- raw spoken text disabled permanently

Client policy should decide storage path, retention period, access control, export format, and whether spoken text hashes are permitted. The default posture remains local, redacted, append-only, and raw-text disabled.

## Safety boundaries

Forbidden:

- raw spoken text storage by default
- provenance guessing
- hidden LLM authority
- hidden model/provider involvement
- unattributed proactive/voice output treated as WESLR-owned
- memory mutation from attribution alone
- queue writes in this phase
- log writes in this phase
- runtime/chat/voice wiring in this phase
- self-improvement activation
- answer selection
- truth/soundness authority
- official score claims

## Non-goals

- no implementation in this phase
- no logging helpers
- no attribution log file
- no voice gateway changes
- no ambient loop changes
- no TTS/STT changes
- no “who said that?” query surface
- no queue writes
- no registry persistence
- no model calls
- no daemon/cron/scheduler
- no memory mutation

## Future phases

- APPROVE_VOICE_SOURCE_ATTRIBUTION_LOG_SCHEMA_ONLY
- APPROVE_VOICE_SOURCE_ATTRIBUTION_LOGGING_HELPERS_ONLY
- APPROVE_WHO_SAID_THAT_QUERY_SURFACE_DESIGN_ONLY
- APPROVE_VOICE_PROVENANCE_MISSING_REVIEW_QUEUE_MAPPING_ONLY
- APPROVE_AMBIENT_VOICE_PROVENANCE_WIRING_DESIGN_ONLY
- APPROVE_SELF_USE_QUERY_SURFACE_DESIGN_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
