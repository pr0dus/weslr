# WESLR Who Said That Runtime Query Design V1

## 1. Status

- design_only
- runtime_query_design_only
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change
- no_runtime_integration
- no_chat_wiring
- no_voice_wiring
- no_terminal_cli_wiring
- no_runtime_routing_implementation
- no_log_reads
- no_log_writes
- no_queue_writes
- no_memory_mutation
- no_external_model_calls

This document is design-only. It authorizes no runtime integration, no chat responder change, no voice gateway change, no ambient loop change, no TTS/STT change, no queue write, no configuration change, no memory mutation, and no attribution log read or write.

## 2. Purpose

Design how a future runtime user question such as “who said that?” should route to the existing who-said-that attribution system.

The future runtime behavior should answer attribution/provenance questions from approved attribution records. It must use records as the source of attribution, not conversational intuition, not hidden model authority, and not a default self-ownership claim.

## 3. Input Surfaces

Future routing may be considered for these input surfaces:

- chat — a user asks “who said that?” or a related attribution question in a chat responder surface.
- voice — a user asks “who said that?” through a voice/ambient interaction surface after speech was emitted.
- terminal/operator CLI — an operator asks an explicit attribution question from a terminal or administrative command surface.

This phase only describes those surfaces. It does not wire chat, voice, terminal/operator CLI, runtime responders, or ambient runtime paths.

## 4. Future Routing Flow

Future routing should be a narrow read-only chain:

`runtime input → detect attribution query intent → WhoSaidThatQueryIntent → approved read-only lookup layer → parserless resolver → WhoSaidThatAnswer → runtime response`

Required steps:

1. Detect attribution query intent from a runtime input such as “who said that?”.
2. Create a `WhoSaidThatQueryIntent` that carries explicit surface metadata, lookup mode, trace refs, utterance id, time window, and safety flags when available.
3. Read attribution records only through an approved read-only lookup layer.
4. Feed selected records/events into the existing parserless resolver.
5. Return a `WhoSaidThatAnswer` that is bounded by the records supplied to the resolver.

The approved read-only lookup layer is the only future component allowed to supply persisted attribution records to the resolver. Runtime routing must not scan logs directly, read `.weslr/voice_source_attribution.jsonl` directly, create logs, mutate logs, or invent fallback sources.

## 5. Missing Attribution Behavior

When attribution is missing, unavailable, denied by policy, ambiguous, or unsupported, the future answer must be bounded:

- say attribution is missing or unknown
- do not guess
- do not infer hidden provenance
- do not make an “I said it” claim
- do not treat unattributed output as WESLR-owned
- do not substitute conversational confidence for provenance

Example safe answer shape:

“I do not have an attribution record for that utterance. I should not guess who said it. The source is currently unknown.”

Missing attribution is not evidence that WESLR, a model, an operator, the voice subsystem, or any other source did or did not speak. It is only absence of usable attribution records.

## 6. LLM/Model Involvement

Future answers must disclose LLM/model involvement when attribution records contain it:

- disclose provider/model if recorded
- disclose whether the output was LLM-assisted if recorded
- disclose whether advisor/model assistance is unknown when records are incomplete
- preserve the recorded authority level and confidence
- avoid hidden LLM authority

A recorded provider/model is provenance metadata, not truth authority. A future runtime answer must not claim that an LLM/model made the answer true, sound, official, scored, or authoritative.

## 7. Runtime Safety Boundaries

Future runtime routing must preserve these safety boundaries:

- no answer selection
- no truth/soundness/score authority
- no official score claim
- no memory mutation from query alone
- no queue writes in this phase
- no log writes
- no log creation
- no direct attribution log read by runtime/chat/voice surfaces
- no model/advisor calls for attribution resolution
- no hidden provider fallback
- no prompt mutation
- no configuration mutation
- no daemon/cron/scheduler behavior
- no runtime/chat/voice wiring in this phase

The query alone must not create review queue entries, memory entries, attribution records, provenance records, registry records, or operational side effects. A later approved phase may separately design review recommendations, but this design does not authorize writes.

## 8. Surface-Specific Notes

### Chat

A future chat responder may detect attribution query intent and construct a `WhoSaidThatQueryIntent`, but the chat responder must not resolve attribution itself. It should call only approved helpers after a later explicit approval.

### Voice

A future voice path may use utterance ids, trace refs, and post-speak attribution metadata to construct a `WhoSaidThatQueryIntent`, but it must not modify the voice gateway, ambient loop, TTS/STT, or attribution log in this phase.

### Terminal/operator CLI

A future operator CLI may accept explicit lookup identifiers such as utterance id, trace ref, or time window, then route through the same read-only lookup layer and parserless resolver. It must not bypass the resolver or claim extra authority.

## 9. Relation to Existing Who-Said-That Components

This design assumes these existing concepts remain the authority boundary:

- `WhoSaidThatQueryIntent` represents the explicit attribution question and lookup constraints.
- approved read-only lookup layer supplies only eligible attribution records/events.
- parserless resolver deterministically resolves from supplied records/events.
- `WhoSaidThatAnswer` reports the bounded answer, missing-attribution state, review requirement, model/provider metadata when recorded, and safety flags.

The future runtime route must be an adapter into this chain, not a second resolver and not a hidden query parser.

## 10. Non-Goals

- no runtime integration
- no chat/voice wiring
- no terminal/operator CLI wiring
- no implementation in this phase
- no real query parser
- no direct log read
- no `.weslr/voice_source_attribution.jsonl` read or write
- no voice gateway modification
- no ambient loop modification
- no TTS/STT modification
- no queue write
- no config change
- no memory mutation
- no model/advisor call

## 11. Future Phases

Future operator decisions may include:

- `APPROVE_WHO_SAID_THAT_RUNTIME_QUERY_SCHEMA_ONLY`
- `APPROVE_WHO_SAID_THAT_RUNTIME_QUERY_HELPERS_ONLY`
- `APPROVE_WHO_SAID_THAT_CHAT_ROUTING_DESIGN_ONLY`
- `APPROVE_AMBIENT_VOICE_PROVENANCE_WIRING_RUNTIME_DESIGN_ONLY`
- `REQUEST_REVISION`
- `REJECT_OR_DEFER`

Until a future phase is explicitly approved, this document remains design-only and must not be treated as runtime authorization.
