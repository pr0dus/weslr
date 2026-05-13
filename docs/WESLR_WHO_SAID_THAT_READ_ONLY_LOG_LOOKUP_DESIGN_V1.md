# WESLR Who Said That Read-Only Log Lookup Design V1

## 1. Title

WESLR Who Said That Read-Only Log Lookup Design V1

## 2. Status

- design_only
- read_only_log_lookup_design
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change
- no_runtime_integration
- no_log_reads
- no_log_writes
- no_external_model_calls
- no_queue_writes

This document is a design boundary only. It authorizes no implementation, no execution path, and no runtime behavior change.

## 3. Purpose

Design how future “who said that?” helpers may read attribution log events safely and feed them into the existing parserless resolver.

The purpose is to define a future read-only attribution log lookup layer that can select explicitly governed attribution records without creating, writing, mutating, or inferring provenance. The lookup layer is only a future input source for the parserless resolver; it is not a parser, not a voice gateway, not a runtime integration, and not an authority system.

## 4. Current Chain

Current in-memory chain:

`provided in-memory records/events → parserless resolver → WhoSaidThatAnswer`

The current implementation accepts already-supplied `VoiceSourceAttributionRecord` and `VoiceAttributionLogEvent` objects or dictionaries, applies deterministic parserless resolver rules, and returns a `WhoSaidThatAnswer`.

## 5. Future Chain

Future read-only lookup chain:

`read-only attribution log lookup → selected VoiceAttributionLogEvent records → parserless resolver → WhoSaidThatAnswer`

The future lookup layer may only provide selected `VoiceAttributionLogEvent` records to the existing parserless resolver helpers. The resolver remains responsible for producing the `WhoSaidThatAnswer`.

## 6. Read-Only Boundary

Future lookup must:

- require explicit path policy before any allowed read path is considered
- read only append-only attribution logs
- never create the log file
- never write to the log file
- never mutate records
- never mutate memory/runtime/config
- never call models
- never guess provenance

The explicit path policy must be operator-governed and narrow. Missing, denied, or unsupported paths must produce no records rather than fallback scanning.

## 7. Lookup Modes

Future lookup modes:

- `most_recent` — select recent eligible log events by timestamp, then feed selected records into the parserless resolver.
- `by_utterance_id` — select log events matching a requested utterance id.
- `by_trace_ref` — select log events matching an explicit trace reference.
- `by_time_window` — select log events in an explicit operator-approved time window.
- `manual_review_only` — return no automatic attribution and preserve the case for later operator review if separately approved.

Every mode must be deterministic, bounded, and read-only. Ambiguity must not be resolved by guessing.

## 8. Missing-Log Behavior

If no log exists, future lookup must:

- return no records
- produce a safe missing-attribution answer through the resolver
- do not create a log file
- do not infer source
- recommend operator review only if later approved

A missing log is not evidence that a source did or did not speak. It is only absence of available attribution records.

## 9. Redaction Policy

Future lookup must not expose:

- raw spoken text
- secrets
- API keys
- tokens
- private user data
- raw benchmark text
- answer keys
- official score data

Diagnostics must be redacted/count-only by default. Any future debug view must preserve hashes, ids, counts, categories, timestamps, and safety flags rather than raw sensitive content.

## 10. Relation to Existing Modules

Future design must use and remain compatible with:

- `VoiceAttributionLogEvent`
- `VoiceSourceAttributionRecord`
- `WhoSaidThatQueryIntent`
- `WhoSaidThatAnswer`
- parserless resolver helpers

The lookup layer is only an input selection layer. It must feed selected log events into the parserless resolver rather than creating a separate attribution authority.

## 11. Safety Boundaries

The future layer forbids:

- log writes
- log creation
- queue writes
- registry persistence
- runtime/chat/voice wiring
- model/advisor calls
- provenance guessing
- unsupported “I said it” claims
- hidden LLM/provider authority
- memory mutation
- self-improvement activation
- answer selection
- truth/soundness authority
- official score claims

The design does not authorize hidden escalation, fallback provider use, advisor review writes, self-use activation, or any side effect outside explicit read-only lookup.

## 12. Non-Goals

- no implementation in this phase
- no log reader helper yet
- no query parser
- no runtime/chat integration
- no voice wiring
- no queue mapping
- no model calls

This phase produces only a design document and design-presence tests.

## 13. Future Phases

Future operator decisions may include:

- `APPROVE_WHO_SAID_THAT_READ_ONLY_LOG_LOOKUP_SCHEMA_ONLY`
- `APPROVE_WHO_SAID_THAT_READ_ONLY_LOG_LOOKUP_HELPERS_ONLY`
- `APPROVE_VOICE_PROVENANCE_MISSING_REVIEW_QUEUE_MAPPING_ONLY`
- `APPROVE_AMBIENT_VOICE_PROVENANCE_WIRING_DESIGN_ONLY`
- `APPROVE_SELF_USE_QUERY_SURFACE_DESIGN_ONLY`
- `REQUEST_REVISION`
- `REJECT_OR_DEFER`

Until one of these is explicitly approved, no log lookup schema, helper, queue mapping, runtime integration, or voice wiring should be implemented.
