# WESLR Speech Quality Packet Helper V1 Review

## 1. Scope reviewed

Implementation files reviewed:

- `weslr/speech_quality_packet.py`
- `weslr/tests/test_speech_quality_packet_v1.py`

Repository anchor confirmed:

- `/data/data/com.termux/files/home/weslr-pr47-clean`
- branch: `master`
- HEAD: `737bfc31949bb512835e9fb03a0f96571bf7f082`

Reference docs reviewed:

- `docs/WESLR_SPEECH_QUALITY_PACKET_HELPER_IMPLEMENTATION_PLAN_V1.md`
- `docs/WESLR_SPEECH_QUALITY_PACKET_HELPER_IMPLEMENTATION_PLAN_REVIEW_V1.md`
- `docs/WESLR_SPEECH_QUALITY_HELPER_DECOMPOSITION_V1.md`
- `docs/WESLR_SPEECH_QUALITY_HELPER_DECOMPOSITION_REVIEW_V1.md`

## 2. Overall review

The helper is implemented in the right general shape: pure, metadata-only, import-safe, deterministic, and fail-closed for most of the intended boundary.

However, there is a blocking boundary hole in the unknown-extra-metadata path:

- `speaker_verified` is currently accepted as valid extra metadata
- that means a speaker-verification claim can enter the packet without rejection
- this violates the intended voice-auth boundary and the packet-helper safety boundary

So the implementation is close, but not yet context-aligned enough to be considered ready.

## 3. Public API implementation

Assessment: **confirmed**.

Implemented APIs:

- `build_speech_quality_packet_v1(...)`
- `validate_speech_quality_packet_v1(packet)`
- `summarize_speech_quality_packet_v1(packet)`
- `to_speech_quality_packet_json_safe_v1(packet)`
- `render_speech_quality_packet_markdown_v1(packet)`

They are implemented as local Python helpers with no file I/O, network I/O, subprocess execution, or provider/model calls.

This part is sufficient.

## 4. Schema implementation

Assessment: **mostly confirmed**.

Required fields are implemented and enforced:

- `packet_id`
- `schema_version`
- `source_refs`
- `provenance_refs`
- `corpus_ref`
- `command_set_ref`
- `feature_pipeline_ref`
- `scenario_refs`
- `quality_scope`
- `quality_band_fields`
- `gap_labels`
- `blocker_fields`
- `synthetic_only`
- `review_required`
- `no_authority_granted`
- `no_public_claim`
- `safe_metadata`

Optional fields are handled:

- `created_at`
- `created_by_ref`
- `related_review_refs`
- `related_design_refs`
- `notes`

This part is sufficient.

## 5. Validation behavior

Assessment: **partially confirmed**.

Confirmed behavior:

- `schema_version` must equal `speech_quality_packet_v1`
- `packet_id` must be non-empty
- refs are normalized and validated as safe strings/lists in the builder
- list fields are real lists in the built packet
- mappings use stable string keys
- `synthetic_only` must be true
- `no_authority_granted` must be true
- `no_public_claim` must be true
- `safe_metadata` must be true
- true blocker fields fail validation
- unknown gap labels fail validation
- unknown metric bands fail validation
- unsafe packets are not silently converted into valid packets

Blocking gap:

- `validate_speech_quality_packet_v1` accepts `speaker_verified=True` as unknown extra metadata
- the builder also accepts `speaker_verified=True` and returns a valid packet
- this is a speaker-verification claim surface and should fail closed

This is the main issue.

## 6. Allowed constants

Assessment: **confirmed**.

Allowed bands are present:

- `unknown`
- `not_evaluated`
- `low`
- `medium`
- `high`
- `blocked`
- `requires_review`

Allowed gap labels are present:

- `feature_quality_gap`
- `preprocessing_gap`
- `command_vocabulary_gap`
- `command_confusion_gap`
- `false_positive_gap`
- `false_negative_gap`
- `rejection_gap`
- `calibration_gap`
- `noise_robustness_gap`
- `accent_robustness_gap`
- `multilingual_gap`
- `synthetic_voice_gap`
- `replay_gap`
- `cymatics_interpretability_gap`
- `operator_attention_gap`
- `overfit_risk`
- `unknown_gap`

Blocker flags are present:

- `has_raw_audio`
- `has_microphone_access`
- `has_runtime_voice_event`
- `has_private_user_audio`
- `has_hidden_recording`
- `has_biometric_identity_claim`
- `has_speaker_verification_claim`
- `has_action_authority`
- `has_public_accuracy_claim`
- `has_model_provider_call`
- `has_weslr_write`
- `has_behavior_pack_promotion`

This part is sufficient.

## 7. Forbidden field/security behavior

Assessment: **mostly confirmed**.

Confirmed rejections include:

- raw waveform data
- audio buffers
- microphone handles
- live stream handles
- unredacted transcripts from real users
- provider output payloads
- model output payloads
- hidden runtime event logs
- public benchmark identifiers
- product-readiness claims
- certification claims
- authority-bearing claims

Gap:

- `speaker_verified` is not rejected
- any authority-adjacent extra metadata key in that shape should be blocked

## 8. JSON-safe behavior

Assessment: **confirmed**.

`to_speech_quality_packet_json_safe_v1`:

- returns JSON-safe data
- does not mutate input
- preserves safety flags in the returned structure
- rejects unsafe/unserializable content instead of silently normalizing it into validity

This part is sufficient.

## 9. Summary behavior

Assessment: **confirmed**.

The summary:

- validates first
- reflects invalid status when the packet is invalid
- does not imply authority
- does not imply success when invalid
- does not create public accuracy, benchmark, product-readiness, or certification claims

This part is sufficient.

## 10. Markdown renderer behavior

Assessment: **mostly confirmed**.

The renderer:

- emits internal markdown only
- marks invalid packets clearly
- does not create authority claims
- does not create benchmark/product-readiness/certification claims

The renderer wording is broadly safe, though it should stay careful to avoid future drift into claim-like phrasing.

This part is sufficient for now.

## 11. Test coverage

Assessment: **partial**.

Covered well:

- valid minimal packet
- valid full packet
- missing required field rejected
- wrong schema version rejected
- raw audio field rejected
- microphone/runtime event rejected
- private user audio rejected
- hidden recording rejected
- biometric identity claim rejected
- speaker verification claim rejected
- action authority rejected
- public accuracy claim rejected
- model/provider call rejected
- `.weslr` write blocker rejected
- behavior-pack promotion blocker rejected
- unsafe gap label rejected
- unsafe metric band rejected
- any true blocker rejected
- `synthetic_only=false` rejected
- `no_authority_granted=false` rejected
- `no_public_claim=false` rejected
- `safe_metadata=false` rejected
- JSON-safe copy does not mutate input
- markdown renderer does not create public claim
- summary does not imply authority
- unknown-but-safe metadata field behavior

Missing high-risk boundary case:

- explicit rejection of `speaker_verified`
- ideally also an explicit test for authority-adjacent extra metadata keys that are not currently hint-matched

## 12. Boundary preservation

Assessment: **mostly confirmed**.

The implementation does not introduce:

- microphone access
- audio processing
- raw audio storage
- runtime voice recognition
- voice template storage
- runtime wiring
- model/provider calls
- `.weslr` writes
- behavior-pack promotion
- public accuracy/benchmark/product-readiness claims

But it does introduce a route by which a speaker-verification claim can survive as extra metadata, which is not acceptable for this boundary.

## 13. Gap analysis

Blocking gaps:

- `speaker_verified` is accepted as extra metadata and therefore passes validation/build

Non-blocking gaps:

- extra-metadata key filtering may need a broader authority-adjacent denylist
- renderer phrasing could be kept under continued watch for claim-like wording drift

## 14. Sufficiency assessment

- implemented_required_public_apis: **yes**
- schema_matches_plan: **yes**
- validation_fail_closed: **no**
- blocker_enforcement_sufficient: **no**
- json_safe_behavior_sufficient: **yes**
- summary_behavior_safe: **yes**
- markdown_renderer_safe: **yes**
- tests_sufficient: **no**
- safe_non_runtime_helper: **yes**
- ready_for_context_alignment: **no**

## 15. Final judgment

`speech_quality_packet_helper_v1_needs_repair`

## 16. Recommended next lane

`REPAIR_WESLR_SPEECH_QUALITY_PACKET_HELPER_V1_SPEAKER_VERIFIED_BOUNDARY`
