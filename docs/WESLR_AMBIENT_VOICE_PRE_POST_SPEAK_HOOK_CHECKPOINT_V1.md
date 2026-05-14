# WESLR Ambient Voice Pre/Post Speak Hook Checkpoint V1

## Status

- status: `canon_checkpoint`
- scope: `pre_post_hook_foundation`
- `no_runtime_integration`
- `no_voice_wiring`
- `no_log_writes`
- `no_queue_writes`
- `official_score_claimed = false`

## Purpose

This checkpoint records the completed foundation for WESLR ambient voice pre-speak and post-speak hook helpers. The checkpoint is in-memory only and documents helper boundaries, not live runtime behavior.

## Pre-speak behavior

The pre-speak foundation:

- accepts explicit metadata
- validates attribution/provenance/trace refs
- allows speech only when attribution is valid
- otherwise blocks or marks unattributed/unknown
- preserves missing attribution as a safety state rather than guessing
- avoids unsupported “I said it” ownership claims

Pre-speak blocks missing attribution/provenance/trace refs. It must not infer provenance from conversational context, tone, timing, style, chat metadata alone, or user expectation.

## Post-speak behavior

The post-speak foundation:

- confirms success only when speech was attempted and trace refs exist
- records failure/blocked state
- records success/failure/blocked state in the in-memory helper result
- forbids ownership claim when speech was not emitted
- preserves failed or blocked speech as non-emitted output

Post-speak confirmation does not prove truth, soundness, correctness, or official score. It only records the emission state supplied to the helper boundary.

## Relation to who-said-that

A future live attribution log can later feed the who-said-that lookup/resolver stack.

That future path requires separate approval for runtime wiring, attribution log write policy, default-path policy, retention/privacy boundaries, and live lookup behavior. This checkpoint only establishes the pre/post hook foundation that could later produce safe attribution records for that stack.

## Limitations

This checkpoint is limited to foundation behavior:

- in-memory only
- no log writes
- no attribution log writes
- no runtime wiring
- no voice gateway wiring
- no ambient loop wiring
- no TTS/STT hook execution
- no chat responder integration
- no queue writes
- no model/advisor calls
- no memory mutation
- no runtime/config/model changes
- no live “who said that?” from spoken events
- no answer selection/truth/soundness/official score claims

## Checkpoint boundary

Classification: `canon_checkpoint` for `pre_post_hook_foundation` only.

The checkpoint does not authorize live voice capability. It records that the foundation can validate explicit pre-speak metadata and record explicit post-speak emission state in helper return data, while preserving blocked/unknown/unattributed outcomes safely.
