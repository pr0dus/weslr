# WESLR Synthetic Speech Test Corpus Helper Implementation Plan V1

## Status

- design_only
- implementation_plan_only
- execution_allowed = false
- no_runtime_integration
- no_microphone_access
- no_audio_generation
- no_audio_processing
- no_raw_audio_storage
- no_public_accuracy_claim
- no_authority_grant
- no_model_calls
- no_provider_calls
- no_weslr_writes
- no_behavior_pack_promotion

## 1. Purpose and scope

**Helper name:** `Synthetic Speech Test Corpus Helper V1`

**Future module suggestion:** `weslr/synthetic_speech_test_corpus.py`

**Future test file suggestion:** `weslr/tests/test_synthetic_speech_test_corpus_v1.py`

This helper will define safe synthetic / provenance-known speech test corpus metadata for future speech-quality evaluation.

It must be:

- metadata-only
- deterministic/pure
- import-safe
- synthetic/provenance-known corpus metadata only
- no audio generation
- no raw audio storage
- no microphone access
- no public accuracy claim
- no authority granted

It must not:

- use private user audio
- use hidden recordings
- use biometric datasets
- use poisoned external media
- use arbitrary social-media audio
- frame itself as a public benchmark
- store raw voice recordings
- call models/providers
- wire runtime behavior
- imply product readiness

Core rule:

> The corpus is provenance metadata, not an audio engine.

## 2. Public helper API plan

### 2.1 `build_synthetic_speech_corpus_packet_v1(...)`

**Purpose:** build a normalized synthetic corpus metadata packet from safe provenance inputs.

**Input shape:**
- named metadata fields only
- source refs, provenance refs, variant refs, scenario refs, and policy flags
- no raw audio
- no audio generation inputs

**Output shape:**
- dict-like corpus packet with required schema fields present
- normalized lists / mappings
- explicit source-class and blocker flags

**Validation behavior:**
- reject missing required fields
- reject unsafe source classes or unsafe field names
- reject any blocker flag set true
- reject missing `synthetic_only`, `provenance_known`, `no_public_benchmark_claim`, `no_authority_granted`, or `safe_metadata`

**Fail-closed behavior:**
- on any invalid or ambiguous input, raise or return a rejected-invalid result rather than coercing unsafe content

**No side effects:**
- no file I/O
- no network I/O
- no subprocess
- no runtime mutation

### 2.2 `validate_synthetic_speech_corpus_packet_v1(packet)`

**Purpose:** validate corpus packet shape, source policy, variant coverage, blockers, and safety boundaries.

**Input shape:**
- one corpus packet object

**Output shape:**
- validation result / boolean-style verdict with diagnostics

**Validation behavior:**
- confirm required fields exist
- confirm field types and allowed values
- confirm all blocker flags are false
- confirm no forbidden corpus source is present

**Fail-closed behavior:**
- unknown or malformed content must fail validation

**No side effects:**
- read-only validation only

### 2.3 `summarize_synthetic_speech_corpus_packet_v1(packet)`

**Purpose:** produce a compact internal summary of the corpus packet.

**Input shape:**
- validated corpus packet

**Output shape:**
- short summary object or dict
- counts / labels / status only

**Validation behavior:**
- summarize only validated packets, or return rejected-invalid

**Fail-closed behavior:**
- if the packet is invalid, the summary must not imply benchmark status, authority, or quality claims

**No side effects:**
- no state changes
- no persistence

### 2.4 `to_synthetic_speech_corpus_json_safe_v1(packet)`

**Purpose:** return a JSON-safe copy of the corpus packet.

**Input shape:**
- corpus packet object

**Output shape:**
- JSON-safe dict / structure with unsafe values removed or rejected

**Validation behavior:**
- preserve only safe scalar/list/map values
- reject unserializable or forbidden content

**Fail-closed behavior:**
- if safe conversion cannot be guaranteed, fail rather than mutating toward unsafe output

**No side effects:**
- must not mutate input

### 2.5 `render_synthetic_speech_corpus_markdown_v1(packet)`

**Purpose:** render an internal human-readable markdown summary.

**Input shape:**
- validated corpus packet

**Output shape:**
- markdown string

**Validation behavior:**
- render only safe metadata and explicit safety status

**Fail-closed behavior:**
- must not invent public claims, benchmark claims, or authority claims

**No side effects:**
- presentation only
- no writes, no network, no runtime actions

## 3. Corpus packet schema

### 3.1 Required fields

- `packet_id`
- `schema_version`
- `source_refs`
- `provenance_refs`
- `corpus_name`
- `corpus_scope`
- `variant_family_refs`
- `scenario_refs`
- `allowed_source_class`
- `forbidden_source_flags`
- `coverage_summary`
- `synthetic_only`
- `provenance_known`
- `review_required`
- `no_private_user_audio`
- `no_hidden_recording`
- `no_biometric_dataset`
- `no_public_benchmark_claim`
- `no_authority_granted`
- `no_public_claim`
- `safe_metadata`

### 3.2 Optional fields

- `created_at`
- `created_by_ref`
- `related_packet_refs`
- `related_design_refs`
- `notes`

### 3.3 Recommended shape notes

- refs should be safe strings only
- lists should be explicit lists, not comma-delimited strings
- mappings should use stable string keys
- no nested raw-data blobs
- corpus metadata should stay provenance-known and non-public

## 4. Allowed variant families

Allowed synthetic variant families:

- `clear_command`
- `near_neighbor_command`
- `noisy_variant`
- `accent_variant`
- `multilingual_variant`
- `partial_command`
- `background_speech`
- `repeated_command`
- `fake_approval_phrase`
- `unsafe_action_phrase`
- `low_confidence_phrase`
- `replay_scenario_metadata`
- `synthetic_voice_scenario_metadata`
- `cymatics_misleading_display_scenario`
- `prompt_injection_spoken_phrase`
- `unknown_variant`

Rules:
- families are metadata only
- families may describe challenge structure, not real audio storage
- families do not imply public benchmark status

## 5. Forbidden sources

Fail closed for:

- private user audio
- hidden recordings
- biometric speaker datasets unless separately approved
- proprietary speech datasets without approval
- poisoned external media
- arbitrary social-media audio
- official benchmark/private benchmark data
- raw voice recordings
- public accuracy benchmark framing

## 6. Source classification

Define source classes:

- `synthetic_weslr_created`
- `operator_written_text_only`
- `provenance_known_fixture`
- `public_open_text_only`
- `unknown_source_blocked`
- `private_audio_blocked`
- `hidden_recording_blocked`
- `biometric_dataset_blocked`
- `poisoned_media_blocked`

Rules:
- approved classes only
- unknown / blocked classes fail validation
- source class metadata must not become public benchmark framing

## 7. Relationship to Speech Quality Packet Helper

Define:
- corpus helper may reference `speech_quality_packet`
- corpus helper must preserve `no_authority_granted`
- corpus helper must preserve `no_public_claim`
- corpus helper must not weaken the normalized speaker/auth metadata denylist
- corpus helper must not introduce `speaker_verified`
- corpus helper must not store voice identity/auth/fallback metadata

## 8. Relationship to voice auth

Record:
- synthetic corpus may include metadata-only spoof/replay scenarios
- synthetic corpus may include fake approval phrase scenarios
- synthetic corpus may not enroll speakers
- synthetic corpus may not verify speakers
- synthetic corpus may not update templates
- synthetic corpus may not restore account access
- synthetic corpus may not authorize actions

## 9. Gap and blocker fields

Define blocker flags:

- `has_private_user_audio`
- `has_hidden_recording`
- `has_raw_audio`
- `has_biometric_dataset`
- `has_unapproved_proprietary_dataset`
- `has_poisoned_external_media`
- `has_social_media_audio`
- `has_public_benchmark_claim`
- `has_speaker_verification_claim`
- `has_action_authority`
- `has_model_provider_call`
- `has_weslr_write`
- `has_behavior_pack_promotion`

Any true blocker fails validation.

## 10. Future tests to implement later

Design tests for:

- valid minimal synthetic corpus packet
- valid full synthetic corpus packet
- forbidden private audio rejected
- hidden recording rejected
- biometric dataset rejected
- poisoned media rejected
- arbitrary social-media audio rejected
- public benchmark claim rejected
- raw audio field rejected
- speaker verification claim rejected
- action authority rejected
- unknown unsafe source class rejected
- safe public text-only fixture accepted
- JSON-safe copy does not mutate input
- summary does not imply benchmark or authority
- markdown renderer does not create public accuracy claim

## 11. Implementation constraints

Future implementation must be:

- pure Python
- stdlib only unless already present and justified
- deterministic
- import-safe
- no file I/O
- no network I/O
- no subprocess
- no provider/model calls
- no `.weslr` writes
- no runtime wiring
- no hidden state

## 12. Completion criteria

Implementation plan is ready when:

- API is clear
- schema is clear
- source classes are clear
- variant families are clear
- blockers are clear
- tests are clear
- relation to speech quality packet helper is clear
- relation to voice auth is clear
- no runtime/audio/authority behavior is introduced

## 13. Future latency note

After the speech helper chain is complete, WESLR should run a separate design lane for reaction-time and latency budget auditing:

`DESIGN_WESLR_REACTION_TIME_AND_LATENCY_BUDGET_AUDIT_V1`

That future lane should measure response latency without weakening safety, identity, or authority boundaries.

## 14. Final constraint

This plan must remain a future metadata-only support layer.

It must not become a runtime audio generator, a public benchmark surface, a hidden router, or an authority surface.
