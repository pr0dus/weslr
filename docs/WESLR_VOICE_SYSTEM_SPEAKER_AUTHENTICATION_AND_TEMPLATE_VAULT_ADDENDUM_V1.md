# WESLR Voice System Speaker Authentication and Template Vault Addendum V1

## Status

- design_only
- addendum_to: `docs/VOICE_SYSTEM_STANDARD_V1.md`
- linked_privacy_boundary: `docs/WESLR_PUBLIC_PILOT_STORAGE_PRIVACY_RETENTION_GOVERNANCE_BOUNDARY_V1.md`
- execution_allowed = false
- no_runtime_integration
- no_voice_wiring
- no_audio_processing
- no_template_storage
- no_registry_writes
- no_model_calls
- no_provider_calls
- no_weslr_writes
- no_behavior_pack_promotion

## 1. Addendum purpose

This addendum extends `VOICE_SYSTEM_STANDARD_V1.md` with a narrow future-facing design for consented monthly voice reauthentication and biometric voice-template vault metadata.

It does **not** replace existing voice provenance or source-attribution documents. Those remain the correct place for “who said that?”, output provenance, pre-speak/post-speak hooks, and attribution logging.

This addendum defines:

- monthly voice reauthentication as a periodic recheck of a previously enrolled speaker
- biometric voice template vault metadata as a governed record of speaker-verification state
- the separation between diarization, verification, identification, and authorization

This addendum is design-only. It does not authorize runtime behavior.

## 2. Terminology separation

- **Speaker diarization**: separates Speaker A / Speaker B / Unknown in a recording or live stream.
- **Speaker change detection**: detects that the active speaker changed.
- **Speaker verification**: compares the current challenge voice to an enrolled voice template.
- **Speaker identification**: claims or predicts which person the voice belongs to.
- **Authorization**: grants permission to act.

Rules:

- diarization is not identity
- verification is not authorization
- identity claim is not action approval
- voice match is not owner/operator approval by itself

## 3. Existing voice standard relationship

`VOICE_SYSTEM_STANDARD_V1.md` already establishes:

- `operator_verified` as the v1 trust posture for authenticated voice sessions
- speaker diarization as out of scope for v1
- future trust levels as additive, not implicit

This addendum defines the future `speaker_verified` path.

It also preserves the existing boundary that provenance and source attribution are metadata-first and non-biometric. Voice source attribution can say what surface or subsystem spoke; it does not by itself prove biometric identity.

## 4. Monthly reauthentication flow

Future monthly reauthentication is a consented refresh cycle, not a passive identity guess.

Future flow:

1. passkey/device authentication first, if available
2. WESLR generates a dynamic 5–6 word phrase
3. the phrase expires quickly and is never reused
4. the phrase is checked for phonetic coverage and pronunciation safety
5. the user speaks the phrase
6. the system evaluates:
   - phrase match
   - sample quality
   - speaker-template match
   - liveness/spoof risk
   - drift status
7. uncertain results require owner/operator review
8. failed results block `speaker_verified` update
9. successful results update metadata/template version only after consent

Monthly refresh updates metadata only; it does not grant authority.

## 5. Dynamic challenge design

Challenge phrases must be:

- unpredictable
- short: 5–6 words
- pronunciation-safe
- language-aware
- phonetically balanced
- non-reusable
- not stored as raw audio by default
- recorded only as a `challenge_ref` metadata pointer

The challenge phrase itself is a verification aid, not an identity claim and not a permission grant.

## 6. Voice template vault

Future voice template vault records are metadata records for speaker verification state.

Suggested record shape:

- `voice_vault_record_id`
- `user_ref`
- `speaker_profile_ref`
- `template_version`
- `encrypted_speaker_embedding_ref`
- `embedding_centroid_summary`
- `embedding_variance_summary`
- `enrollment_quality_band`
- `last_refresh_at`
- `next_refresh_due`
- `drift_summary`
- `drift_status`
- `spoof_replay_risk_band`
- `consent_ref`
- `retention_policy_ref`
- `deletion_supported`
- `revocation_supported`
- `raw_audio_retained`
- `raw_audio_retention_reason`
- `safe_metadata`

Rules:

- raw audio retained is false by default
- embeddings/templates are encrypted
- template export is disabled by default
- template use is limited to speaker-verification metadata
- vault records do not authorize actions

## 7. Enrollment and revocation

Enrollment requires:

- explicit consent
- an enrollment challenge/phrase
- a quality threshold
- a spoof/replay risk check
- owner/operator review

Revocation is supported.
Deletion is supported.
Re-enrollment after revocation requires fresh consent.

No hidden enrollment is allowed.
No passive enrollment from ambient speech is allowed.

## 8. Drift and monthly update

Small drift may be recorded as metadata.

Drift bands:

- `stable`
- `minor_drift`
- `review_required_drift`
- `blocked_drift`

Rules:

- monthly refresh updates template version only if safe
- unexpected drift triggers owner/operator review
- repeated mismatch blocks verification
- drift does not expand authority

## 9. Spoof/replay/synthetic voice protection

The future speaker-auth path must treat the following as blocking risks:

- replay risk
- synthetic voice risk
- TTS/deepfake risk
- hidden audio risk
- background speech risk
- phrase mismatch risk
- command injection risk
- liveness uncertainty
- low-quality sample risk

If any of these risks is material or unresolved, `speaker_verified` must not be granted.

## 10. Consent, privacy, retention, deletion

Biometric voice templates are sensitive data.

Required future policy:

- explicit consent required
- purpose limitation required
- retention policy required
- deletion/revocation required
- no raw audio by default
- no private user audio training
- no hidden recording
- no third-party sharing
- no public biometric claim
- link to the storage/privacy/retention boundary

This addendum does not weaken the privacy boundary; it depends on it.

## 11. Authority boundary

`speaker_verified` may become authentication metadata.

`speaker_verified` does **not** approve actions.

Voice alone cannot authorize:

- deployment
- payment
- device control
- public post
- memory write
- file write
- tool execution
- commit/push

High-confidence voice match still routes through Owner/Operator Workflow and Action Authority where required.

## 12. Packet shape

Future `speaker_auth_packet` shape:

- `speaker_auth_packet_id`
- `user_ref`
- `speaker_label`
- `challenge_ref`
- `phrase_match_status`
- `speaker_match_status`
- `speaker_match_confidence_band`
- `liveness_status`
- `spoof_replay_risk_status`
- `noise_quality_status`
- `drift_status`
- `template_version`
- `vault_record_ref`
- `consent_ref`
- `retention_policy_ref`
- `raw_audio_retained`
- `speaker_verified`
- `identity_claimed`
- `authority_granted`
- `owner_review_required`
- `operator_review_required`
- `action_authority_required`
- `memory_write_allowed`
- `tool_execution_allowed`
- `runtime_authority`
- `public_claim_allowed`
- `safe_metadata`

Rules:

- packet metadata may support future verification flows
- packet metadata does not itself grant authority
- any authority-bearing field must remain false unless separately approved by the relevant authority boundary

## 13. Unknown Engine stress scenarios

Future review scenarios should include:

- replayed monthly phrase
- synthetic cloned voice
- old recording
- background speaker
- child/guest voice
- noisy microphone
- partial phrase
- wrong phrase right speaker
- right phrase wrong speaker
- multilingual pronunciation drift
- illness/hoarse voice drift
- urgent approval phrase after verification
- hidden audio from video
- prompt-injection phrase spoken aloud
- template drift beyond threshold
- revoked user attempts reauth

These scenarios are design-time stress cases only. They do not authorize implementation.

## 14. Integration points

This addendum should be read together with:

- `docs/VOICE_SYSTEM_STANDARD_V1.md`
- `docs/WESLR_VOICE_SOURCE_ATTRIBUTION_DESIGN_V1.md`
- `docs/WESLR_UNKNOWN_ENGINE_SPEECH_SIGNAL_FRICTION_AUDIT_V1.md`
- `docs/WESLR_SPEECH_RECOGNITION_QUALITY_AND_CYMATICS_SIGNAL_OPTIMIZATION_V1.md`
- `docs/WESLR_VOICE_LAYER_ARCHITECTURE.md`
- `docs/WESLR_PUBLIC_PILOT_STORAGE_PRIVACY_RETENTION_GOVERNANCE_BOUNDARY_V1.md`
- the Owner/Operator Workflow boundary docs
- the Action Authority Boundary docs
- the Expectation-Deviation Engine docs

## 15. Safety boundaries

Forbidden:

- hidden recording
- passive enrollment
- raw audio storage by default
- biometric identity claim without consent
- speaker verification claim without enrollment
- voice-only owner/operator approval
- voice-only action authority
- public biometric or accuracy claim
- model/provider calls
- runtime wiring
- `.weslr` writes
- behavior-pack promotion

## 16. Future helper roadmap

Future lanes:

- `Speaker Diarization Metadata Helper V1`
- `Voice Challenge Phrase Generator Helper V1`
- `Speaker Auth Packet Helper V1`
- `Voice Template Vault Metadata Helper V1`
- `Voice Drift and Monthly Refresh Helper V1`
- `Voice Spoof/Replay Risk Helper V1`
- `Voice Consent and Revocation Helper V1`
- `Voice Auth Unknown Engine Stress Review V1`

## 17. Final constraint

This addendum defines a future consented speaker-auth metadata path only.

It must not become a biometric authority surface, an action approval surface, a hidden recording surface, or a runtime voice-auth implementation spec.
