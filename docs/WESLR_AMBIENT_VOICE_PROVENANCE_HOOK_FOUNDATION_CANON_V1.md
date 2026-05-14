# WESLR Ambient Voice Provenance Hook Foundation Canon V1

## Status

- status: `canon_checkpoint`
- scope: `foundation_only`
- `no_runtime_integration`
- `no_voice_wiring`
- `no_log_writes`
- `no_queue_writes`
- `official_score_claimed = false`

## Purpose

This canon checkpoint records the completed foundation-only ambient voice provenance hook stack for WESLR. It canonizes the design/schema/helper foundation for future pre-speak and post-speak attribution boundaries without claiming live voice gateway, ambient loop, TTS/STT, or runtime capability.

## Completed components

The completed foundation-only stack includes:

- ambient voice provenance wiring design
- ambient voice provenance wiring schema
- pre-speak hook schema/helpers
- post-speak hook schema/helpers
- in-memory validation/result surfaces for future hook boundaries
- safety flags that prevent runtime, voice, log, queue, model, advisor, memory, and config mutation claims

These components define how future approved hook phases should prepare and validate attribution metadata before speech and record success/failure/blocked outcomes after an attempted speech event. They do not wire any live speech system.

## Canonized behavior

The pre-speak hook foundation validates explicit metadata before any future speech surface may proceed. It is designed to block speech when attribution/provenance/trace refs are missing, invalid, or unsafe.

The post-speak hook foundation records success/failure/blocked state in memory for the helper result returned by the function call. This is an in-memory helper result only; it is not persistent memory mutation and it is not an attribution log write.

The provenance wiring foundation defines safe records for future ambient voice hook flow. It does not connect those records to voice gateway, ambient loop, chat responder, TTS/STT, queues, config, memory, models, advisors, or runtime behavior.

## Safety guarantees

This canon checkpoint requires:

- pre-speak blocks speech when attribution/provenance/trace refs are missing
- post-speak records success/failure/blocked state in memory only as helper return data
- no actual speech triggering
- no attribution log writes
- no queue writes
- no model/advisor calls
- no memory mutation
- no runtime/config/model changes
- no voice gateway wiring
- no ambient loop wiring
- no TTS/STT hook execution
- no answer selection/truth/soundness/official score claims
- no live “who said that?” from spoken events

The hook foundation must not create unsupported WESLR ownership claims. If speech was blocked, failed, or not emitted, future consumers must preserve that state and avoid claiming that WESLR said the utterance.

## Limitations

This checkpoint is foundation-only:

- not wired into voice gateway
- not wired into ambient loop
- not wired into TTS/STT
- not wired into chat responder
- not reading or writing `.weslr/voice_source_attribution.jsonl`
- cannot yet produce live attribution records
- cannot answer live spoken-event attribution questions
- does not create real attribution log writes
- does not trigger speech

## Canon boundary

Classification: `canon_checkpoint` for completed foundation/design/schema/helper stack only.

This document does not authorize runtime wiring. Live voice gateway wiring, ambient loop wiring, actual TTS/STT hook execution, attribution log persistence, and live “who said that?” from spoken events require separate operator approval and separate tests.
