# WESLR Who Said That Chat Routing Integration Design V1

## 1. Status

- design_only
- chat_routing_integration_design_only
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change
- no_runtime_integration
- no_chat_responder_changes
- no_runtime_chat_behavior_change
- no_voice_wiring
- no_log_reads
- no_log_writes
- no_queue_writes
- no_memory_mutation
- no_model_calls

This document is design-only. It authorizes no runtime integration, no chat responder changes, no runtime/chat behavior change, no voice gateway change, no ambient loop change, no TTS/STT change, no queue write, no config change, no memory mutation, no attribution log read/write, and no model/advisor call.

## 2. Purpose

Design how a future chat integration may connect the who-said-that chat routing helpers to runtime chat without implementing the integration yet.

The goal is a narrow future path where chat/runtime input can detect a clear attribution question, route it into the existing record-backed attribution chain, and otherwise fall through to normal chat behavior.

## 3. Current Stack

The current stack is composed of separate design/schema/helper layers:

- chat routing helpers — classify explicit chat metadata and produce safe in-memory routing decisions.
- runtime query helpers — build and validate runtime query request/result objects without runtime side effects.
- read-only lookup helpers — select attribution records through approved read-only lookup boundaries.
- parserless resolver — resolves from explicitly supplied attribution records/events without parsing or guessing.
- attribution answer schemas — represent bounded attribution answers, including missing-attribution state and safety flags.

The integration design must preserve this stack order. Chat integration should be only an adapter into the existing who-said-that path, not a second resolver and not a hidden parser.

## 4. Future Integration Point

Future chat/runtime input should first detect attribution intent before normal conversational handling:

1. Receive chat/runtime input metadata.
2. Classify explicit metadata through chat routing helpers.
3. If clear attribution intent is detected, create a runtime query request through runtime query helpers.
4. Use only the approved read-only lookup helpers to obtain eligible attribution/provenance records.
5. Resolve via the parserless resolver and attribution answer schemas.
6. Return a bounded attribution response.
7. If the input is not a clear attribution query, fallthrough to normal chat.

Clear attribution intent means a recognized phrase family, a supported attribution intent, and sufficient confidence. It does not mean the integration may guess provenance, scan logs directly, or call a model.

## 5. Fallthrough to Normal Chat

If chat routing helpers return `unknown`, low confidence, or `should_route = false`, the future integration should fall through to normal chat.

Fallthrough must not create attribution records, write queues, mutate memory, read logs, write logs, or alter the original chat responder behavior. It is simply a no-route decision.

## 6. Missing Attribution Behavior

If the who-said-that path is selected but attribution is unavailable, denied by policy, ambiguous, or incomplete, the future response must remain bounded:

- no guessing
- say attribution missing/unknown
- no “I said it” claim
- no hidden ownership claim
- no substitution of chat confidence for provenance

Safe response shape:

“I do not have an attribution record for that. I should not guess who said it. The source is currently unknown.”

Missing attribution is only absence of usable provenance records. It is not evidence that WESLR, an LLM, an operator, runtime chat, voice, or any subsystem did or did not produce the prior output.

## 7. Safety Boundaries

This phase forbids:

- runtime integration in this phase
- chat responder changes
- runtime/chat behavior changes
- voice gateway, ambient loop, TTS/STT changes
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

The future integration must not create side effects from an attribution query alone. Any later write path, review path, runtime wiring, or operator-visible action requires separate approval.

## 8. Non-Goals

- no implementation in this phase
- no chat routing integration helpers yet
- no dry-run runtime path
- no runtime/chat wiring
- no chat responder modification
- no voice routing
- no log lookup expansion
- no queue writes
- no memory mutation
- no model/advisor calls

## 9. Future Phases

Future operator decisions may include:

- `APPROVE_WHO_SAID_THAT_CHAT_ROUTING_INTEGRATION_HELPERS_ONLY`
- `APPROVE_WHO_SAID_THAT_CHAT_ROUTING_DRY_RUN_ONLY`
- `APPROVE_WHO_SAID_THAT_CHAT_ROUTING_RUNTIME_WIRING_DESIGN_ONLY`
- `APPROVE_WHO_SAID_THAT_VOICE_ROUTING_DESIGN_ONLY`
- `REQUEST_REVISION`
- `REJECT_OR_DEFER`

Until a future phase is explicitly approved, this document remains design-only and must not be treated as authorization for runtime/chat/voice wiring.
