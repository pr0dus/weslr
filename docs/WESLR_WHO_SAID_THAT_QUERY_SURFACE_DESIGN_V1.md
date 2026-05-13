# WESLR Who Said That Query Surface Design V1

## Status

- design_only
- who_said_that_query_surface
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change
- no_runtime_integration
- no_query_implementation
- no_log_reads
- no_log_writes
- no_external_model_calls
- no_queue_writes

## Purpose

Design a future read-only query surface that can answer attribution questions such as:

- “who said that?”
- “what generated that?”
- “was that WESLR?”
- “was an LLM involved?”
- “what triggered it?”
- “why did you say that?”
- “which subsystem produced that voice?”
- “was that ambient, proactive, advisor-assisted, or model-assisted?”

from attribution/provenance records rather than guessing.

## Core trust rule

WESLR must answer from records, not intuition.

If attribution/provenance records are missing, WESLR must say attribution is missing or unknown.
It must not guess, and it must not claim “I said it” unless records support WESLR-owned generation.

## Required record sources

Future query surface may read from:

- `VoiceAttributionLogEvent`
- `VoiceSourceAttributionRecord`
- `OutputProvenanceEnvelope`
- `ProvenanceSourceEntry`
- trace refs
- model/provider metadata when available

This design phase must not implement real reads.

## Query intent categories

Future query categories:

- `who_said_that`
- `what_generated_that`
- `was_llm_involved`
- `what_triggered_that`
- `why_did_you_say_that`
- `which_subsystem_generated_that`
- `was_that_weslr_owned`
- `show_last_voice_attribution`
- `unknown`

## Answer contract

A future answer should include, when known:

- source subsystem
- source module
- generated_by
- trigger
- trigger_type
- whether speech was emitted
- TTS/STT engine
- model provider/name if LLM-assisted
- whether LLM-assisted
- whether advisor-assisted
- whether ambient/proactive was involved
- authority level
- truth class
- confidence
- trace refs or redacted trace count
- whether operator review is required
- whether attribution is missing/partial

## Missing-record answer behavior

If no attribution record exists, WESLR should answer in a bounded way:

“I do not have a provenance record for that utterance. I should not guess who said it. The source is currently unknown, and operator review may be needed.”

Rules:

- no self-ownership claim
- no hidden model/provider claim
- no memory mutation
- no queue write in this phase
- no runtime action
- no truth/soundness authority

## LLM-assisted answer behavior

If attribution says an LLM/model was involved, WESLR should disclose:

- `llm_assisted = true`
- model/provider if recorded
- authority is voice_surface/suggestion unless separately validated
- no hidden LLM authority
- no hidden model/provider involvement
- no claim of independent WESLR understanding unless supported by non-LLM provenance/state

## Ambient/proactive answer behavior

If attribution says ambient/proactive was involved, WESLR should disclose:

- source subsystem
- trigger
- whether it came from observation/rule/model/advisor path
- confidence
- operator-review requirement
- whether it was WESLR-owned or assisted

## “Was that WESLR?” distinction

Safe ownership categories:

- `weslr_owned`
- `weslr_surface_llm_assisted`
- `advisor_assisted`
- `external_model_surface`
- `operator_triggered`
- `unknown_unattributed`

WESLR must not collapse all spoken output into “I said it.”

## Query output style

Future answers should be:

- concise
- record-backed
- provenance-aware
- non-mystical
- transparent about missing data
- explicit about LLM/model involvement
- clear about uncertainty

## Review queue integration

If attribution is missing or weak, future query surface may recommend a review item.

This phase must not write queues.

Potential future findings:

- missing attribution record
- attribution record incomplete
- source subsystem unknown
- LLM-assisted output lacks provider/model
- ambient/proactive trigger missing
- voice source not registered

## Relation to self-use query surface

This “who said that?” surface is a specialized part of future broader self-use queries:

- “what did you notice?”
- “why did you suggest this?”
- “which part of you generated this?”
- “where can this take me?”
- “what should we improve next?”

## Safety boundaries

Forbidden:

- provenance guessing
- claiming “I said it” without record support
- hidden LLM authority
- hidden model/provider involvement
- treating unattributed output as WESLR-owned
- raw spoken text disclosure by default
- memory mutation from query alone
- queue writes in this phase
- log reads/writes in this phase
- runtime/chat/voice wiring in this phase
- self-improvement activation
- answer selection
- truth/soundness authority
- official score claims

## Non-goals

- no implementation in this phase
- no query parser
- no runtime/chat integration
- no voice gateway changes
- no ambient loop changes
- no TTS/STT changes
- no real attribution log reads
- no log writes
- no queue writes
- no registry persistence
- no model/advisor calls
- no daemon/cron/scheduler
- no memory mutation

## Future phases

- APPROVE_WHO_SAID_THAT_QUERY_SURFACE_SCHEMA_ONLY
- APPROVE_WHO_SAID_THAT_QUERY_SURFACE_HELPERS_ONLY
- APPROVE_WHO_SAID_THAT_READ_ONLY_LOG_LOOKUP_DESIGN_ONLY
- APPROVE_VOICE_PROVENANCE_MISSING_REVIEW_QUEUE_MAPPING_ONLY
- APPROVE_AMBIENT_VOICE_PROVENANCE_WIRING_DESIGN_ONLY
- APPROVE_SELF_USE_QUERY_SURFACE_DESIGN_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
