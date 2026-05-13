# WESLR Voice Source Attribution Design V1

## Status

- design_only
- voice_source_attribution
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change
- no_runtime_integration
- no_voice_wiring
- no_external_model_calls
- no_queue_writes

## Purpose

Design how WESLR will attribute future spoken, ambient, proactive, TTS, STT, voice-gateway, and LLM-assisted utterances so the user can ask:

- “who said that?”
- “what generated that?”
- “was that WESLR?”
- “was an LLM involved?”
- “what triggered it?”
- “why did you say that?”

and receive a grounded answer from provenance records.

## Core problem

Voice/proactive utterances can feel intelligent and personal. Without attribution, they can also become untrustworthy.

A future WESLR voice/proactive utterance must not be treated as WESLR-owned unless there is a provenance record that identifies the source, trigger, model/provider involvement, and authority boundary.

## Attribution record concept

Attribution record fields should include:

- `utterance_id`
- `output_provenance_id`
- `spoken_text_hash`
- `spoken_text_stored`
- `source_subsystem`
- `source_module`
- `generated_by`
- `trigger`
- `trigger_type`
- `input_channel`
- `output_channel`
- `voice_engine`
- `tts_engine`
- `stt_engine`
- `model_provider`
- `model_name`
- `llm_assisted`
- `advisor_assisted`
- `ambient_loop_involved`
- `proactive_suggestion_involved`
- `operator_review_required`
- `authority_level`
- `truth_class`
- `confidence`
- `created_at`
- `trace_refs`
- `safety_flags`

Raw spoken text should not be stored by default. A hash plus provenance identifiers should be preferred unless explicit later policy allows retention.

## Source categories

- `voice_gateway`
- `ambient_voice_loop`
- `tts_engine`
- `stt_engine`
- `proactive_suggestions`
- `llm_advisor_mode`
- `local_model`
- `external_model`
- `operator_cli`
- `unknown`

## “Who said that?” behavior

When the user asks “who said that?” or similar, WESLR should deterministically:

1. look for the most recent attributable voice/proactive output
2. return the source subsystem
3. return whether an LLM/model was involved
4. return whether the output was WESLR-owned, LLM-assisted, advisor-assisted, or unknown
5. return the trigger if known
6. return the confidence/authority boundary
7. explicitly say when provenance is missing

WESLR must answer from provenance records, not from memory, vibes, or guesses.

Example safe answer style:

“That utterance came from the ambient voice loop using the configured TTS layer. The provenance record says it was LLM-assisted by [provider/model] and triggered by [event]. I can attribute the surface, but I cannot treat it as a verified WESLR-owned decision unless the provenance record marks it that way.”

## Missing provenance behavior

If provenance is missing, WESLR must not guess.

It should answer:

- source unknown
- attribution missing
- operator review recommended
- no truth/soundness authority
- no memory write
- no runtime action
- no self-claim that “I said it” unless supported

Missing provenance should degrade confidence, not invite reconstruction or ownership claims.

## Voice/proactive provenance requirement

Every future voice/proactive output requires attribution before it can be trusted as WESLR-owned behavior:

- `OutputProvenanceEnvelope`
- registered source entry where possible
- attribution record
- trace ref
- authority boundary
- LLM/provider disclosure if used
- raw sensitive content storage disabled by default

## LLM-assisted voice rule

If an LLM generated or shaped the spoken text:

- `llm_assisted = true`
- model/provider must be recorded when available
- authority must remain suggestion/voice_surface unless separately validated
- no hidden LLM authority
- no claim that WESLR independently understood unless supported by non-LLM state/provenance

## Ambient/proactive rule

Ambient/proactive utterances must record:

- what triggered the utterance
- which subsystem surfaced it
- whether it was rule-based, model-assisted, or advisor-assisted
- whether it was generated from observation, memory, local scan, or user state
- whether operator review is required

## User trust rule

Voice source attribution is a trust boundary.

WESLR must prefer:

- “I do not have enough provenance to say”

Over:

- guessing
- pretending ownership
- hiding model involvement
- implying consciousness/agency without record support

## Relation to output provenance and source registry

This design uses:

- `OutputProvenanceEnvelope`
- `ProvenanceSourceEntry`
- source registry lifecycle
- unknown/unregistered source policy
- review queue suggestions for missing attribution

Voice/proactive attribution should link output provenance to a registered source when possible. Unknown or unregistered sources remain review-required and must not become trusted merely because an utterance occurred.

## Review queue integration

Missing or weak voice attribution should later become review suggestions, not automatic fixes.

Possible future review findings:

- unattributed voice output
- unknown voice source
- LLM-assisted voice without provider record
- ambient output without trigger
- proactive output without provenance envelope
- voice source not in registry

This phase does not write queues.

## Self-improvement relation

If future WESLR self-review notices repeated missing attribution, it may create a proposal/review item. It must not silently alter voice behavior or activate new attribution behavior without approval.

Self-improvement-derived attribution changes still require registry coverage, tests, validation, and operator approval.

## Safety boundaries

Forbidden:

- provenance guessing
- hidden LLM authority
- hidden model/provider involvement
- unattributed proactive/voice output
- raw sensitive spoken text storage by default
- memory mutation from voice attribution alone
- queue writes in this phase
- runtime/chat/voice wiring in this phase
- self-improvement activation
- answer selection
- truth/soundness authority
- official score claims

## Non-goals

- no implementation in this phase
- no voice gateway modification
- no ambient loop modification
- no TTS/STT modification
- no runtime/chat integration
- no queue writes
- no registry persistence
- no model calls
- no daemon/cron/scheduler
- no memory mutation

## Future phases

- APPROVE_VOICE_SOURCE_ATTRIBUTION_SCHEMA_ONLY
- APPROVE_VOICE_SOURCE_ATTRIBUTION_LOGGING_DESIGN_ONLY
- APPROVE_WHO_SAID_THAT_QUERY_SURFACE_DESIGN_ONLY
- APPROVE_VOICE_PROVENANCE_MISSING_REVIEW_QUEUE_MAPPING_ONLY
- APPROVE_AMBIENT_VOICE_PROVENANCE_WIRING_DESIGN_ONLY
- APPROVE_SELF_USE_QUERY_SURFACE_DESIGN_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
