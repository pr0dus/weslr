# WESLR Ambient Voice Pre-Speak Hook Design V1

Status: `design_only`
Approval token: `APPROVE_AMBIENT_VOICE_PRE_SPEAK_HOOK_DESIGN_ONLY`

This document designs the future pre-speak provenance hook for ambient/proactive/voice outputs. It does not implement hook behavior and does not wire voice gateway, ambient loop, TTS/STT, runtime/chat behavior, queues, config, memory, models, or advisors.

Execution flags:

- `execution_allowed = false`
- `no_runtime_integration`
- `no_voice_wiring`
- `no_log_writes`
- `no_queue_writes`
- `no_model_calls`
- `no_advisor_calls`
- `no_memory_mutation`

## 1. Purpose

Before any future voice/proactive utterance is spoken, the pre-speak hook must create and validate attribution intent. The hook exists so WESLR can later answer “who said that?” from records instead of from memory, style, recency, or guesswork.

The pre-speak attribution step should run before TTS emission and before any future ambient/proactive voice surface commits to speaking. It prepares provenance, verifies that the source can be represented safely, and blocks or marks unknown when provenance cannot be established.

## 2. Required inputs

A future approved pre-speak hook must receive explicit metadata, not infer it from conversational context alone:

- source subsystem
- trigger
- output channel
- intended voice/TTS path
- LLM/model involvement if any
- output provenance envelope reference
- source registry entry reference where available

The source subsystem and trigger identify where the utterance came from. The output channel and intended voice/TTS path identify the planned surface. LLM/model involvement must include provider/model when available. The output provenance envelope reference and source registry entry reference connect the hook to the broader provenance stack.

## 3. Required future outputs

A future approved implementation should produce or validate these records before speech:

- `AmbientVoiceProvenanceHookRecord`
- `VoiceSourceAttributionRecord`
- pre-speak `VoiceAttributionLogEvent`

The `AmbientVoiceProvenanceHookRecord` represents the hook decision. The `VoiceSourceAttributionRecord` represents the source attribution intent. The pre-speak `VoiceAttributionLogEvent` represents a draft event that may later be confirmed or failed by a post-speak hook.

## 4. Blocking rule

Blocking rule: If attribution cannot be created/validated, future speech must either stop or be marked unattributed/unknown.

The hook must not silently proceed as though attribution exists. A missing, invalid, ambiguous, or unsafe attribution draft is a gating condition: stop before speech when policy requires blocking, or allow only an explicitly unattributed/unknown speech path with operator review recommended.

## 5. Missing provenance behavior

When provenance is missing or cannot be validated:

- no guessing
- no “I said it” claim
- source unknown
- operator review recommended

Missing provenance must not become WESLR ownership. The future who-said-that path must report unknown/unattributed rather than inventing a source.

## 6. Safety boundaries

This design phase forbids runtime behavior and side effects:

- no runtime integration in this phase
- no voice wiring in this phase
- no voice gateway changes
- no ambient loop changes
- no TTS/STT behavior changes
- no runtime/chat behavior changes
- no raw spoken text by default
- no hidden LLM authority
- no hidden provider/model authority
- no memory mutation from pre-speak hook alone
- no queue writes in this phase
- no log writes in this phase
- no model calls in this phase
- no advisor calls in this phase
- no config changes
- no truth/soundness/score claims

This phase must not create `.weslr/voice_source_attribution.jsonl` and must not append to any attribution log.

## 7. Future phases

Allowed next-step decisions are:

- `APPROVE_AMBIENT_VOICE_PRE_SPEAK_HOOK_SCHEMA_ONLY`
- `APPROVE_AMBIENT_VOICE_PRE_SPEAK_HOOK_HELPERS_ONLY`
- `APPROVE_AMBIENT_VOICE_POST_SPEAK_HOOK_DESIGN_ONLY`
- `APPROVE_WHO_SAID_THAT_RUNTIME_QUERY_DESIGN_ONLY`
- `REQUEST_REVISION`
- `REJECT_OR_DEFER`

No future implementation work is authorized by this document alone.
