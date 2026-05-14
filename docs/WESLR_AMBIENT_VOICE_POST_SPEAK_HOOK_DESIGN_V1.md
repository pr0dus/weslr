# WESLR Ambient Voice Post-Speak Hook Design V1

Status: `design_only`
Approval token: `APPROVE_AMBIENT_VOICE_POST_SPEAK_HOOK_DESIGN_ONLY`

This document designs the future post-speak provenance hook for confirming whether a planned ambient/proactive/voice utterance was actually emitted successfully, failed, or was blocked. It does not implement hook behavior and does not wire voice gateway, ambient loop, TTS/STT, runtime/chat behavior, queues, config, memory, models, advisors, or speech.

Execution flags:

- `execution_allowed = false`
- `no_runtime_integration`
- `no_voice_wiring`
- `no_log_writes`
- `no_queue_writes`
- `no_model_calls`
- `no_advisor_calls`
- `no_memory_mutation`
- `no_speech_triggered`

## 1. Purpose

After a future TTS/speech attempt, the post-speak hook must confirm whether speech succeeded, failed, or was blocked. The post-speak confirmation exists to close the loop between a pre-speak hook result and the final attribution record used by future “who said that?” lookup.

The post-speak hook must not infer that speech happened. It records explicit success/failure/blocking status from the future speech surface and trace metadata.

## 2. Required inputs

A future approved post-speak hook must receive explicit inputs:

- pre-speak hook result
- utterance ID
- output provenance ID
- attribution record ID
- TTS/STT engine metadata
- speech success/failure flag
- trace refs

The pre-speak hook result determines whether speech was allowed. The utterance ID, output provenance ID, attribution record ID, engine metadata, and trace refs bind the attempt to the attribution stack.

## 3. Required future outputs

A future approved implementation should produce:

- post-speak `AmbientVoiceProvenanceHookRecord`
- post-speak `VoiceAttributionLogEvent`
- confirmation/failure status

The post-speak `AmbientVoiceProvenanceHookRecord` captures the hook decision. The post-speak `VoiceAttributionLogEvent` captures whether speech was emitted and whether it succeeded or failed. Confirmation/failure status must be explicit and auditable.

## 4. Success behavior

Success behavior:

- speech emitted only if pre-speak allowed it
- post-speak confirmation records success and trace refs
- success requires utterance ID, output provenance ID, attribution record ID, TTS/STT engine metadata where available, and trace refs

If pre-speak did not allow speech, the post-speak hook must not create a success confirmation. A success confirmation means the planned utterance was actually emitted and the trace refs connect it to provenance.

## 5. Failure behavior

Failure behavior:

- failed/blocked speech creates failure attribution record
- no “I said it” claim if speech was not emitted
- failure status remains distinguishable from success status
- blocked status remains distinguishable from failed TTS emission

If speech was blocked before emission or failed during emission, future who-said-that answers must not claim the utterance was spoken by WESLR. Failed/blocked records exist for auditability, not ownership claims.

## 6. Missing provenance behavior

When post-speak provenance is missing, incomplete, ambiguous, or unsafe:

- no guessing
- source unknown
- operator review recommended

Missing provenance must not become WESLR ownership. The post-speak hook must preserve uncertainty rather than inventing a source or success state.

## 7. Safety boundaries

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
- no memory mutation from post-speak hook alone
- no queue writes in this phase
- no log writes in this phase
- no model calls in this phase
- no advisor calls in this phase
- no config changes
- no speech triggered in this phase
- no truth/soundness/score claims

This phase must not create `.weslr/voice_source_attribution.jsonl` and must not append to any attribution log.

## 8. Future phases

Allowed next-step decisions are:

- `APPROVE_AMBIENT_VOICE_POST_SPEAK_HOOK_SCHEMA_ONLY`
- `APPROVE_AMBIENT_VOICE_POST_SPEAK_HOOK_HELPERS_ONLY`
- `APPROVE_WHO_SAID_THAT_RUNTIME_QUERY_DESIGN_ONLY`
- `REQUEST_REVISION`
- `REJECT_OR_DEFER`

No future implementation work is authorized by this document alone.
