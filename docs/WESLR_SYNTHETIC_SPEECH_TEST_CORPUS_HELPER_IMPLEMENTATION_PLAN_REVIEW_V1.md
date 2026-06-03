# WESLR Synthetic Speech Test Corpus Helper Implementation Plan Review V1

## 1. Scope reviewed

Review target:

- `docs/WESLR_SYNTHETIC_SPEECH_TEST_CORPUS_HELPER_IMPLEMENTATION_PLAN_V1.md`

Repository anchor confirmed:

- `/data/data/com.termux/files/home/weslr-pr47-clean`
- branch: `master`
- HEAD: `0b679354d7783478835c80ad2cd8110216ee62e0`

## 2. Overall review

The implementation plan is sufficient for a future pure metadata-only `Synthetic Speech Test Corpus Helper V1`.

It stays within the intended boundary:

- metadata-only
- deterministic / pure
- import-safe
- synthetic / provenance-known corpus metadata only
- no audio generation
- no raw audio storage
- no microphone access
- no public accuracy claim
- no authority granted
- corpus is provenance metadata, not an audio engine

## 3. Public helper API plan

All required future functions are defined and bounded well enough for implementation:

- `build_synthetic_speech_corpus_packet_v1(...)`
- `validate_synthetic_speech_corpus_packet_v1(packet)`
- `summarize_synthetic_speech_corpus_packet_v1(packet)`
- `to_synthetic_speech_corpus_json_safe_v1(packet)`
- `render_synthetic_speech_corpus_markdown_v1(packet)`

For each function, the plan clearly states:

- purpose
- input shape
- output shape
- validation behavior
- fail-closed behavior
- no side effects

Assessment: sufficient.

## 4. Corpus packet schema

The required fields are explicit and complete for the stated boundary:

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

Optional fields are also reasonable:

- `created_at`
- `created_by_ref`
- `related_packet_refs`
- `related_design_refs`
- `notes`

Assessment: sufficient.

## 5. Allowed variant families

The allowed families are appropriate and remain metadata-only:

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

The plan correctly says:

- families are metadata only
- families describe challenge structure, not real audio storage
- families do not imply public benchmark status

Assessment: sufficient.

## 6. Forbidden sources

The boundary is explicit and fail-closed for:

- private user audio
- hidden recordings
- biometric speaker datasets unless separately approved
- proprietary speech datasets without approval
- poisoned external media
- arbitrary social-media audio
- official benchmark/private benchmark data
- raw voice recordings
- public accuracy benchmark framing

Assessment: sufficient.

## 7. Source classification

The source classes are clear and safe:

- `synthetic_weslr_created`
- `operator_written_text_only`
- `provenance_known_fixture`
- `public_open_text_only`
- `unknown_source_blocked`
- `private_audio_blocked`
- `hidden_recording_blocked`
- `biometric_dataset_blocked`
- `poisoned_media_blocked`

The plan also states:

- approved classes only pass
- unknown / blocked classes fail validation
- source class metadata does not become benchmark framing

Assessment: sufficient.

## 8. Relationship to Speech Quality Packet Helper

The separation is preserved:

- corpus helper may reference `speech_quality_packet`
- corpus helper preserves `no_authority_granted`
- corpus helper preserves `no_public_claim`
- corpus helper does not weaken the normalized speaker/auth metadata denylist
- corpus helper does not introduce `speaker_verified`
- corpus helper does not store voice identity/auth/fallback metadata

Assessment: sufficient.

## 9. Relationship to voice auth

The plan keeps voice auth safely fenced:

- may include metadata-only spoof/replay scenarios
- may include fake approval phrase scenarios
- may not enroll speakers
- may not verify speakers
- may not update templates
- may not restore account access
- may not authorize actions

Assessment: sufficient.

## 10. Gap and blocker fields

The blocker set is strong and fail-closed:

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

Assessment: sufficient.

## 11. Future tests

The future test list covers the important boundary cases:

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

Assessment: sufficient.

## 12. Implementation constraints

The future implementation constraints are appropriately narrow:

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

Assessment: sufficient.

## 13. Future latency note

The latency note is safe as written:

- future lane `DESIGN_WESLR_REACTION_TIME_AND_LATENCY_BUDGET_AUDIT_V1`
- latency work comes after the speech helper chain
- latency measurement must not weaken safety, identity, or authority boundaries

Assessment: safe.

## 14. Gap analysis

No blocking gaps found.

Minor non-blocking hardening ideas only:

- If future implementation wants extra symmetry, it could optionally add explicit `has_audio_generation` and `has_speaker_verification` blocker fields, but the current plan already forbids both clearly enough.
- `public_open_text_only` should remain strictly text-only in implementation, but the current wording already supports that boundary.

These are not required repairs.

## 15. Sufficiency assessment

- sufficient_as_synthetic_corpus_helper_plan: yes
- sufficient_as_api_plan: yes
- sufficient_as_schema_plan: yes
- sufficient_as_source_classification_plan: yes
- sufficient_as_forbidden_source_boundary: yes
- sufficient_as_variant_family_plan: yes
- sufficient_as_voice_auth_separation: yes
- sufficient_as_safe_non_runtime_plan: yes
- future_latency_note_safe: yes
- ready_for_helper_implementation: yes

## 16. Final judgment

`synthetic_speech_corpus_helper_implementation_plan_valid_ready_for_implementation`

## 17. Recommended next lane

`IMPLEMENT_WESLR_SYNTHETIC_SPEECH_TEST_CORPUS_HELPER_V1`
