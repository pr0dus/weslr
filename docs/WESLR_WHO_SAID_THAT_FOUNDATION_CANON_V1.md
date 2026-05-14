# WESLR Who-Said-That Foundation Canon V1

## Status

- status: `canon_checkpoint`
- scope: `foundation_only`
- `no_runtime_integration`
- `no_chat_routing_live`
- `no_voice_wiring`
- `no_log_writes`
- `no_queue_writes`
- `official_score_claimed = false`

## Purpose

This canon checkpoint records the completed foundation-only “who said that?” stack for WESLR. It canonizes schemas and helper boundaries that can answer attribution questions from explicit records in controlled helper contexts, without claiming live runtime routing or live voice attribution.

## Completed components

The completed foundation-only stack includes:

- `WhoSaidThatQueryIntent`
- `WhoSaidThatAnswer`
- parserless resolver
- read-only log lookup schema/helpers
- runtime query schema/helpers
- chat routing schema/helpers
- dry-run vertical slice helpers

These components define record-based attribution query structures, safe answer shapes, parserless helper behavior, read-only lookup boundaries, runtime-query request/result structures, and chat-routing helper decisions. They do not integrate with live chat responders, voice gateway, ambient loop, TTS/STT, queues, config, memory, models, or advisors.

## Canonized behavior

The foundation supports attribution answers from records only. A valid answer must be grounded in already supplied attribution records/events or explicit helper inputs. Missing attribution returns unknown/unattributed rather than guessing.

The parserless resolver does not implement a general natural-language query parser. It resolves only approved attribution question forms from provided in-memory records/events and helper metadata.

The read-only log lookup schema/helpers define safe lookup and selection boundaries, but this phase does not read a default runtime attribution log and does not read or write `.weslr/voice_source_attribution.jsonl`.

The runtime query and chat routing schema/helpers define future-safe request/result and routing shapes. They are helper boundaries only and are not live runtime or chat responder integrations.

## Safety guarantees

This canon checkpoint requires:

- answers from records only
- missing attribution returns unknown/unattributed
- no provenance guessing
- no unsupported “I said it” ownership
- no hidden LLM/provider authority
- no answer selection/truth/soundness/official score claims
- no runtime integration
- no live chat routing
- no voice wiring
- no real attribution log writes
- no queue writes
- no memory mutation
- no runtime/config/model changes

LLM/model/provider involvement must be disclosed when recorded. A helper may report that an attribution record says a model/provider was involved, but it must not convert advisor/model output into truth or WESLR ownership.

## Limitations

This foundation cannot yet answer live runtime “who said that?” without wiring.

It does not provide:

- live chat routing
- live voice attribution
- real attribution log reads from runtime
- real attribution log writes
- chat responder integration
- voice/ambient integration
- TTS/STT integration
- queue persistence
- model/advisor calls

## Canon boundary

Classification: `canon_checkpoint` for completed foundation/design/schema/helper stack only.

This document does not authorize runtime wiring. Live runtime/chat/voice use requires separate readiness review, policy decisions for attribution log paths, and separately approved implementation phases.
