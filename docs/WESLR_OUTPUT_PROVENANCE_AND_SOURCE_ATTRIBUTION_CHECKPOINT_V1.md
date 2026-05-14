# WESLR Output Provenance and Source Attribution Checkpoint V1

## Status

- status: `canon_checkpoint`
- scope: `foundation_only`
- `no_runtime_integration`
- `no_voice_wiring`
- `no_log_writes`
- `no_queue_writes`
- `no_memory_mutation`
- `no_runtime_config_model_changes`
- `official_score_claimed = false`

## Purpose

This checkpoint records the shared provenance foundation for future self-use, voice attribution, source-registry checks, and review systems.

The foundation connects output provenance and source attribution records so future approved systems can describe where an output came from, what authority boundary applied, what triggered it, and whether model/provider involvement was recorded.

## Completed components

The completed foundation includes:

- `OutputProvenanceEnvelope`
- voice source attribution schema
- voice attribution log schema
- attribution logging helper layer
- source registry dependency
- safe validation boundaries for provenance and attribution records

The `OutputProvenanceEnvelope` provides a shared envelope for output-origin metadata. The voice source attribution schema describes source, trigger, authority, and model/provider involvement for future voice/proactive outputs. The voice attribution log schema provides event structure for future append-only attribution events, but this checkpoint does not authorize real log writes.

## Authority boundary

Provenance records describe source, authority, and trigger. They do not make truth claims by themselves.

A provenance record can say that a source, subsystem, model, provider, advisor, or operator path was recorded as involved. It cannot prove the output is true, sound, correct, benchmark-valid, or officially scored.

Unknown or unregistered source remains operator-review required. Missing source identity must not be converted into WESLR ownership. Unregistered source detection and source registry checks remain safety boundaries, not automatic authority grants.

## LLM/advisor rule

LLM/model involvement must be disclosed when recorded.

Advisor output remains proposal input, not truth. Advisor records, provider records, prompt templates, and review queue suggestions do not become authoritative answers without operator review and the separately approved system boundary that consumes them.

No hidden LLM/provider authority is allowed. No output may be represented as directly WESLR-owned when explicit provenance says a model, provider, advisor, or external subsystem was involved.

## Future users

Future approved users of this foundation may include:

- who-said-that system
- ambient voice hooks
- source registry checks
- review queue suggestions
- self-use provenance reporting
- voice/proactive attribution review tools

Those future users require their own approval if they wire runtime behavior, route chat, emit speech, write logs, write queues, call models/advisors, or mutate config/runtime/memory.

## Safety guarantees

This checkpoint requires:

- no runtime integration
- no voice wiring
- no log writes
- no queue writes
- no memory mutation
- no runtime/config/model changes
- no answer selection/truth/soundness/official score claims
- no unsupported WESLR ownership claims
- no hidden LLM/provider authority
- no raw spoken text by default in attribution records

## Limitations

This is a foundation-only checkpoint. It does not provide live runtime attribution, live “who said that?” answers, chat responder routing, voice gateway wiring, ambient loop wiring, TTS/STT behavior, queue persistence, or real attribution log writes.

It canonizes the record and helper foundation that future approved systems may use.
