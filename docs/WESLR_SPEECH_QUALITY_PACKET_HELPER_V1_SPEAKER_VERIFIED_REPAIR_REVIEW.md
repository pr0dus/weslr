# WESLR Speech Quality Packet Helper V1 Speaker Verified Repair Review

## 1. Scope reviewed

Implementation files reviewed:
- `weslr/speech_quality_packet.py`
- `weslr/tests/test_speech_quality_packet_v1.py`

Repository anchor confirmed:
- `/data/data/com.termux/files/home/weslr-pr47-clean`
- branch: `master`
- HEAD: `436bdedb21a4f5569baa32df7c0aa6e90bdf422e`

Reference doc reviewed:
- `docs/WESLR_SPEECH_QUALITY_PACKET_HELPER_V1_REVIEW.md`

## 2. Overall review

The repair is narrow and the main boundary hole is improved: top-level `speaker_verified`, nested `speaker_verified`, JSON-safe conversion of invalid packets, and authority-adjacent phrasing are now handled fail-closed in the reviewed paths.

However, the denylist is still too narrow for normalized variants. `speakerVerified` and `speakerverified` are still accepted as extra metadata in a valid packet, so the speaker-verification claim surface is not fully closed yet.

## 3. Repair scope

Assessment: confirmed.

- only `weslr/speech_quality_packet.py` and `weslr/tests/test_speech_quality_packet_v1.py` changed in the repair
- no runtime/audio/speaker-verification behavior was introduced
- protected files were untouched

## 4. `speaker_verified` rejection

Assessment: mostly confirmed.

Confirmed rejection paths:
- top-level `speaker_verified`
- nested `speaker_verified`
- JSON-safe conversion of invalid `speaker_verified` packets
- summary/markdown mark such packets invalid

Diagnostics are reasonably aligned:
- unsafe extra metadata field
- authority-adjacent metadata not allowed
- validation fails closed

Remaining hole:
- compact normalized variants such as `speakerVerified` and `speakerverified` are still accepted

## 5. Authority-adjacent denylist

Assessment: not sufficient.

The explicit denylist covers many listed forms, but it does not catch all normalized variants. In particular:
- `speakerVerified` → accepted
- `speakerverified` → accepted
- `speaker-verified` → rejected

So the denylist is still too narrow if the intent is to fail closed on all obvious speaker-verification claim variants.

## 6. Safe unknown metadata preservation

Assessment: confirmed with caveat.

- unknown-but-safe metadata still passes
- safe metadata is JSON-safe
- safe metadata is not treated as authority-bearing when it avoids the denylist

Caveat:
- the current safe-metadata path still needs broader normalization coverage so that unsafe claim variants do not slip through as “safe” unknown metadata

## 7. Validation behavior

Assessment: partially restored.

Confirmed:
- validation fails closed for `speaker_verified`
- builder does not return a valid packet containing top-level `speaker_verified`
- JSON-safe conversion does not sanitize invalid `speaker_verified` packets into validity
- summary/markdown mark invalid packets as invalid

Not yet sufficient:
- validation still allows compact normalized variants of the same claim surface
- invalid speaker-verification packets should not be possible to express via simple camelCase/concatenated key variants

## 8. Regression preservation

Assessment: mostly preserved.

Still confirmed in review:
- valid minimal packet passes
- valid full packet passes
- true blockers still fail
- raw audio / microphone / runtime voice / private audio / hidden recording still fail
- biometric identity claim still fails
- action authority still fails
- public accuracy claim still fails
- model/provider call still fails
- `.weslr` write blocker still fails
- behavior-pack promotion blocker still fails
- `synthetic_only=false` still fails
- `no_authority_granted=false` still fails
- `no_public_claim=false` still fails
- `safe_metadata=false` still fails

Boundary hole remains:
- `speakerVerified` / `speakerverified` can still be accepted

## 9. Test coverage

Assessment: partial.

Covered:
- top-level `speaker_verified` rejected
- nested `speaker_verified` rejected
- authority-adjacent metadata keys rejected
- JSON-safe copy rejects invalid `speaker_verified` packets
- summary/render mark speaker-verification packets invalid
- safe unknown metadata still accepted

Coverage gap:
- no explicit test for camelCase or compact normalized variants like `speakerVerified` or `speakerverified`

Test count note:
- current file has 24 test functions, but `pytest --collect-only` reports 67 collected cases
- that looks like consolidation/parameterization rather than a raw collapse in collected coverage
- still, the missing normalized-variant case is real

## 10. Boundary preservation

Assessment: mostly confirmed.

No introduction of:
- microphone access
- audio processing
- raw audio storage
- runtime voice recognition
- speaker verification implementation
- voice template storage
- runtime wiring
- model/provider calls
- `.weslr` writes
- behavior-pack promotion
- public accuracy/benchmark/product-readiness claims
- authority grant

But the claim boundary is still not fully closed because normalized speaker-verification variants can still survive as extra metadata.

## 11. Gap analysis

Blocking gap:
- denylist is too narrow for normalized speaker-verification variants (`speakerVerified`, `speakerverified`)

Non-blocking gaps:
- safe-metadata key filtering could use stronger normalization
- renderer wording should stay under watch for future claim drift

## 12. Sufficiency assessment

- repair_closes_speaker_verified_gap: **no**
- authority_adjacent_denylist_sufficient: **no**
- validation_fail_closed_restored: **yes** for `speaker_verified`, **no** overall
- blocker_enforcement_sufficient: **no**
- safe_unknown_metadata_preserved: **yes**
- json_safe_behavior_safe_after_repair: **yes**
- summary_renderer_safe_after_repair: **yes**
- tests_sufficient_after_repair: **no**
- safe_non_runtime_helper_preserved: **yes**
- ready_for_context_alignment: **no**

## 13. Final judgment

`speech_quality_packet_speaker_verified_repair_needs_more_work`

## 14. Recommended next lane

`REPAIR_WESLR_SPEECH_QUALITY_PACKET_HELPER_V1_SPEAKER_VERIFIED_BOUNDARY`
