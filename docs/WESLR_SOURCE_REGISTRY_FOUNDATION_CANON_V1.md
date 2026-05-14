# WESLR Source Registry Foundation Canon V1

## Status

- status: `canon_checkpoint`
- scope: `foundation_only`
- `no_runtime_integration`
- `no_registry_persistence`
- `no_queue_writes`
- `official_score_claimed = false`

## Purpose

This canon checkpoint records the completed foundation-only source registry stack for WESLR. It canonizes source identity, authority boundary, lifecycle, and seed definitions without claiming live scanning, runtime enforcement, automatic activation, source registration, registry persistence, or self-improvement activation.

## Completed components

The completed foundation-only stack includes:

- `ProvenanceSourceEntry`
- `ProvenanceSourceSafetyFlags`
- initial source registry seed
- source lifecycle rules
- validation boundaries for source identity and authority metadata
- safety flags that prevent hidden runtime actions, registration, activation, persistence, and score claims

## Source registry purpose

The source registry maps subsystem IDs to authority boundaries.

It supports future and foundation-level use by:

- voice attribution
- who-said-that
- advisor review
- self-review
- future extensions
- provenance source checks
- review of missing or stale source coverage

A registry entry can describe the type of source, ownership boundary, authority level, review state, and safety flags. A registry entry does not make a source true, safe, activated, registered in runtime, or authorized to act.

## Source lifecycle rules

The foundation preserves source lifecycle states so future systems can distinguish seeded, proposed, review-required, blocked, deprecated, or unknown sources. Unknown/unregistered sources require operator review before any authority is granted.

The source lifecycle is descriptive. It does not activate providers, register runtime handlers, mutate config, create queues, write registry files, or perform self-improvement.

## Safety guarantees

This canon checkpoint requires:

- unknown/unregistered sources require operator review
- no provenance guessing
- no automatic activation
- no self-improvement activation
- no automatic source registration
- no runtime registry enforcement
- no live scanning
- no queue writes
- no registry persistence
- no runtime/config/model changes
- no truth/soundness/official score authority

Source registry metadata can support future attribution and review, but it is not itself proof of truth, correctness, soundness, benchmark validity, or official score.

## Limitations

This checkpoint does not provide:

- live scanning
- runtime registry enforcement
- automatic source registration
- automatic activation
- queue writes
- registry persistence
- self-improvement activation
- voice gateway wiring
- ambient loop wiring
- chat responder changes
- TTS/STT behavior
- model/advisor calls

## Canon boundary

Classification: `canon_checkpoint` for completed foundation/design/schema/helper stack only.

Runtime registry enforcement, persistent registry storage, source auto-registration, review queue writes, live scanning, and self-improvement activation require separate operator approval and separate tests.
