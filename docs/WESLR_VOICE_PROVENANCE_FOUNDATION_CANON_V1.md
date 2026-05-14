# WESLR Voice Provenance Foundation Canon V1

## Status

- status: `canon_checkpoint`
- scope: `foundation_only`
- `no_runtime_integration`
- `no_voice_wiring`
- `no_log_writes`
- `no_chat_responder_routing`
- `no_voice_gateway_wiring`
- `no_ambient_loop_wiring`
- `no_queue_writes`
- `no_memory_mutation`
- `no_runtime_config_model_changes`
- `official_score_claimed = false`

## Purpose

This canon checkpoint records the completed foundation-only voice provenance stack for WESLR. It canonizes schemas and helper boundaries that make future voice attribution possible without claiming live runtime behavior.

The foundation exists so future approved systems can attribute spoken, ambient, proactive, TTS/STT, voice-gateway, or LLM-assisted utterances from explicit provenance records rather than memory, style, recency, or guesswork.

## Completed components

The completed foundation-only stack includes:

- `VoiceSourceAttributionRecord`
- `VoiceAttributionLogEvent`
- voice attribution logging helpers
- redacted summaries
- safe missing-attribution behavior
- validation surfaces for attribution and log events
- helper boundaries that keep attribution records separate from runtime speech behavior

These components provide structured records and helper behavior only. They do not activate live attribution, route chat responses, emit speech, write real logs, or change runtime behavior.

## Canonized behavior

The foundation may represent:

- source subsystem or component identity
- trigger metadata
- model/provider involvement when known and recorded
- authority boundary metadata
- output provenance references
- missing or unknown attribution states
- redacted summaries for review-safe inspection

The foundation must preserve uncertainty. If attribution is missing, unknown, unregistered, or unsupported, the safe behavior is to report that attribution is unavailable or requires review. It must not infer ownership from tone, recency, channel, memory, or user expectation.

## Safety guarantees

This canon checkpoint requires:

- no raw spoken text by default
- no hidden LLM/provider authority
- no unsupported “I said it” ownership
- no memory mutation
- no queue writes
- no runtime/config/model changes
- no answer selection/truth/soundness/official score claims
- no runtime voice wiring
- no chat responder routing
- no voice gateway wiring
- no ambient loop wiring
- no real attribution log writes

A future attribution answer may only claim ownership or source identity when supported by explicit records. Unknown, missing, or unsafe attribution remains non-authoritative.

## Limitations

This checkpoint is foundation-only:

- not wired to runtime
- not wired to voice gateway
- not wired to ambient loop
- not wired to TTS/STT
- not writing real logs
- not reading or writing `.weslr/voice_source_attribution.jsonl`
- cannot yet answer live spoken events
- does not implement live “who said that?” behavior
- does not provide chat responder routing
- does not activate advisors or external models

## Non-goals

This canon does not authorize:

- live voice attribution
- live “who said that?” answers
- real attribution log writes
- chat responder routing
- voice gateway wiring
- ambient loop wiring
- queue persistence
- daemon, cron, or scheduler creation
- runtime/config/model mutation
- answer selection, truth, soundness, benchmark, or official score claims

## Canon boundary

Classification: `canon_checkpoint` for completed foundation/design/schema/helper stack only.

This document is not a readiness declaration for live runtime use. Runtime wiring, voice gateway integration, ambient loop integration, log persistence, and live answer surfaces require separate operator approval and separate tests.
