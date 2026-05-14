# WESLR Who Said That Chat Routing Design V1

## 1. Status

- design_only
- chat_routing_design_only
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change
- no_runtime_integration
- no_chat_routing_implementation
- no_chat_responder_change
- no_voice_wiring
- no_log_reads
- no_log_writes
- no_queue_writes
- no_memory_mutation
- no_model_calls

This document is design-only. It authorizes no runtime routing, no chat routing implementation, no chat responder modification, no voice gateway change, no ambient loop change, no TTS/STT change, no queue write, no config change, no memory mutation, no attribution log read/write, and no model/advisor call.

## 2. Purpose

Design how future chat questions like “who said that?” route to attribution/provenance answers from the existing record-backed who-said-that runtime query helpers.

The future chat route should answer attribution questions from approved provenance records. It must not answer from conversational intuition, hidden LLM authority, runtime guesses, or default self-ownership claims.

## 3. Supported Query Phrases

Future chat intent detection may recognize narrow attribution phrases such as:

- “who said that?”
- “what generated that?”
- “was that WESLR?”
- “was an LLM involved?”
- “what triggered that?”
- “why did you say that?”

This design does not implement a parser. Phrase recognition in a later approved phase should be narrow, deterministic, and limited to attribution intent detection.

## 4. Future Routing Flow

Future chat routing should follow this bounded chain:

`chat input → detect attribution intent → WhoSaidThatRuntimeQueryRequest → approved read-only lookup layer → parserless resolver → WhoSaidThatRuntimeQueryResult → chat response`

Required future steps:

1. Detect attribution intent from a chat question such as “who said that?”.
2. Create a `WhoSaidThatRuntimeQueryRequest` using explicit metadata only, with no raw text storage and query text hash only.
3. Use an approved read-only lookup layer to obtain eligible attribution/provenance records.
4. Resolve via the existing parserless resolver and record-backed who-said-that helpers.
5. Return a `WhoSaidThatRuntimeQueryResult` that preserves the attribution answer id, missing-attribution state, review requirement, and safety posture.

The chat layer must be only a future adapter into the existing attribution chain. It must not become a second resolver, a hidden query parser, a log scanner, or an attribution authority.

## 5. Missing Attribution Behavior

If attribution is missing, unavailable, denied, ambiguous, or unsupported, the future chat answer must remain bounded:

- say attribution is missing/unknown
- do not guess
- do not infer hidden provenance
- make no “I said it” claim
- do not treat unattributed output as WESLR-owned
- do not substitute chat confidence for provenance

Safe answer shape:

“I do not have an attribution record for that. I should not guess who said it. The source is currently unknown.”

Missing attribution is only absence of usable attribution records. It is not evidence that WESLR, an LLM, an operator, voice runtime, or any subsystem did or did not produce the prior output.

## 6. LLM/Model Disclosure

Future chat answers must disclose LLM/model involvement only if recorded in attribution/provenance records:

- disclose provider/model only if recorded
- disclose LLM assistance only if recorded
- disclose unknown provider/model state when records are incomplete
- preserve recorded confidence and operator-review posture
- no hidden LLM authority

A provider/model name is provenance metadata, not truth authority. The chat response must not claim model involvement makes an attribution answer true, sound, official, scored, or authoritative.

## 7. Safety Boundaries

This phase forbids:

- runtime routing in this phase
- chat routing implementation in this phase
- chat responder modification
- voice gateway, ambient loop, or TTS/STT changes
- log reads/writes in this phase
- direct `.weslr/voice_source_attribution.jsonl` access
- queue writes
- memory mutation
- model calls
- advisor calls
- answer selection
- truth/soundness/score claims
- official score claims
- prompt/config mutation
- daemon/cron/scheduler behavior

The query alone must not create memory records, queue records, attribution records, provenance records, registry records, or operational side effects.

## 8. Future Integration Notes

A later chat-routing helper phase may define an in-memory intent object for chat metadata, but it must still route through `WhoSaidThatRuntimeQueryRequest` and `WhoSaidThatRuntimeQueryResult`.

A later integration design may specify where chat responders call the helpers, but must separately prove no raw text persistence, no hidden provider calls, no direct log access, and no ownership claim without records.

## 9. Non-Goals

- no implementation in this phase
- no chat routing implementation
- no runtime integration
- no query parser
- no chat responder changes
- no voice routing
- no log lookup implementation
- no log reads or writes
- no queue writes
- no memory mutation
- no model/advisor calls

## 10. Future Phases

Future operator decisions may include:

- `APPROVE_WHO_SAID_THAT_CHAT_ROUTING_SCHEMA_ONLY`
- `APPROVE_WHO_SAID_THAT_CHAT_ROUTING_HELPERS_ONLY`
- `APPROVE_WHO_SAID_THAT_CHAT_ROUTING_INTEGRATION_DESIGN_ONLY`
- `APPROVE_WHO_SAID_THAT_VOICE_ROUTING_DESIGN_ONLY`
- `REQUEST_REVISION`
- `REJECT_OR_DEFER`

Until a future phase is explicitly approved, this document remains design-only and must not be treated as authorization for runtime/chat/voice wiring.
