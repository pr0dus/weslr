# WESLR Ambient Voice Provenance Wiring Design V1

Status: `design_only`
Approval token: `APPROVE_AMBIENT_VOICE_PROVENANCE_WIRING_DESIGN_ONLY`

This document is a design-only plan for future ambient/proactive/voice output provenance wiring. It does not implement runtime integration, voice wiring, log writing, queue writing, model calls, configuration changes, memory mutation, or chat behavior changes.

Execution flags:

- `execution_allowed = false`
- `no_runtime_integration`
- `no_voice_wiring`
- `no_log_writes`
- `no_queue_writes`
- `no_model_calls`
- `no_external_model_calls`
- `no_memory_mutation`
- `no_truth_soundness_score_claims`
- `official_score_claimed = false`

## 1. Current safe stack

The current safe stack already separates provenance structures from runtime voice behavior:

- `VoiceSourceAttributionRecord` — structured record for who generated or mediated an output, with subsystem/module/provider/model fields where applicable.
- `VoiceAttributionLogEvent` — event wrapper for pre-speak drafts and post-speak confirmation/failure records.
- Logging helpers — append-only helper surface designed for future attribution log events; not activated by this phase.
- Who-said-that query helpers — query intent and answer structures for later user-facing attribution questions.
- Parserless resolver — uses provided in-memory records/events only; it does not parse arbitrary text and does not guess.
- Read-only lookup helpers — load and select attribution log events from explicit paths without creating `.weslr/voice_source_attribution.jsonl`.

## 2. Future wiring points

Future runtime work may wire the attribution stack at these boundaries, but this phase does not wire them:

- voice gateway
- ambient loop
- proactive suggestions
- TTS emission
- STT transcript path
- local response generation
- model-assisted response generation

Each future wiring point must pass an explicit provenance envelope forward instead of relying on implicit caller identity or conversational memory.

## 3. Required future flow

A future approved implementation should follow this flow:

1. Pre-speak attribution draft — create a draft `VoiceAttributionLogEvent` before speech is attempted.
2. Output provenance envelope — attach an output provenance envelope describing source subsystem, module, trigger, channel, model/provider involvement, and trace references.
3. Source registry entry — ensure the source has a known registry entry or mark it unregistered for operator review.
4. TTS attempt — emit via TTS only after provenance metadata is available to the emitting path.
5. Post-speak attribution confirmation/failure — record whether speech was emitted and whether the attempt succeeded or failed.
6. Append-only attribution log — append the final redacted attribution event only in a future approved logging phase.
7. Future who-said-that lookup — answer “who said that?” only from recorded attribution records/log events.

The intended lifecycle is: pre-speak attribution draft → output provenance envelope → source registry entry → TTS attempt → post-speak attribution confirmation/failure → append-only attribution log → future who-said-that lookup.

## 4. Missing attribution rule

When attribution is missing, incomplete, ambiguous, or untrusted:

- no guessing
- no “I said it” claim
- source unknown
- operator review recommended

A who-said-that answer must report missing attribution rather than inventing ownership. Missing records cannot be upgraded into WESLR ownership by tone, style, recency, memory, or assumption.

## 5. LLM/model-assisted rule

For local/model-assisted response generation and any future LLM/model-assisted voice output:

- provider/model recorded when available
- no hidden LLM authority
- no hidden model/provider involvement
- no claim of independent WESLR understanding without non-LLM provenance

If a response is model-assisted, the attribution record must preserve that fact. A model-assisted draft may still be spoken by WESLR surfaces, but the record must not imply independent WESLR understanding unless supported by non-LLM provenance and explicit reviewed source context.

## 6. Safety boundaries for this phase

This phase is documentation and test coverage only. It explicitly forbids:

- runtime integration in this phase
- voice gateway changes
- ambient loop changes
- proactive suggestion runtime changes
- TTS/STT behavior changes
- chat behavior changes
- log writes in this phase
- queue writes in this phase
- model calls in this phase
- advisor calls in this phase
- configuration changes
- memory mutation
- self-improvement activation
- truth/soundness claims
- official score claims
- answer selection from undocumented runtime state

This phase must not create `.weslr/voice_source_attribution.jsonl` and must not append to any attribution log.

## 7. Future phases

Allowed next-step decisions are:

- `APPROVE_AMBIENT_VOICE_PROVENANCE_WIRING_SCHEMA_ONLY`
- `APPROVE_AMBIENT_VOICE_PRE_SPEAK_HOOK_DESIGN_ONLY`
- `APPROVE_AMBIENT_VOICE_POST_SPEAK_HOOK_DESIGN_ONLY`
- `APPROVE_WHO_SAID_THAT_RUNTIME_QUERY_DESIGN_ONLY`
- `REQUEST_REVISION`
- `REJECT_OR_DEFER`

No future implementation work is authorized by this document alone.
