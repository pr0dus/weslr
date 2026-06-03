# WESLR Synthetic Speech Test Corpus Helper V1 — Review

Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
Branch: `master`
Start HEAD: `60cde2b9d26edaadd0eeeaebf09eb86742e212d2`

## Reviewed files
- `weslr/synthetic_speech_test_corpus.py`
- `weslr/tests/test_synthetic_speech_test_corpus_v1.py`

## Public API check
Confirmed present:
- `build_synthetic_speech_corpus_packet_v1(...)`
- `validate_synthetic_speech_corpus_packet_v1(packet)`
- `summarize_synthetic_speech_corpus_packet_v1(packet)`
- `to_synthetic_speech_corpus_json_safe_v1(packet)`
- `render_synthetic_speech_corpus_markdown_v1(packet)`

These are import-safe, deterministic, stdlib-only, and have no file/network/subprocess/model/runtime wiring.

## Validation run
- `python3 -m py_compile weslr/synthetic_speech_test_corpus.py weslr/tests/test_synthetic_speech_test_corpus_v1.py` ✅
- `python3 -m pytest -q weslr/tests/test_synthetic_speech_test_corpus_v1.py` ✅ (`78` collected)
- `python3 weslr/tests/release_gate_v1.py` ✅
- `bash scripts/weslr_release_check.sh` ✅
- `git diff --check` ✅
- protected-file diff checks ✅
  - `weslr/chat_responder.py` unchanged
  - `weslr/main.py` unchanged
  - `dialogue.py` unchanged
  - `chat_ui.py` unchanged

## What looks correct
- Required schema fields are enforced.
- Allowed source classes are constrained and blocked classes fail.
- Unknown source classes fail closed.
- Required and recommended blocker flags are present in the helper surface.
- `speakerVerified` / `voiceVerified` / `identityVerified` / `accountAccessRestored` / `approvedByVoice` camelCase extras are rejected.
- `to_synthetic_speech_corpus_json_safe_v1` does not mutate input in the happy path.
- Summary and markdown rendering stay internal and do not add public benchmark/authority language.
- Tests cover the main accepted/rejected paths and the safety boundary is mostly preserved.

## Blocking gaps
1. **List-field type boundary is too permissive**
   - `_normalize_string_list(...)` accepts dict inputs for list fields by using their values.
   - This violates the requirement that list fields be real lists, not mappings or coerced structures.
   - I confirmed this with a direct probe: `source_refs={'a': 'fixture:text-only-1'}` was accepted.

2. **Text-only / audio-ref boundary is too permissive**
   - `public_open_text_only` does not fully reject audio-like source material.
   - URL-like refs such as `https://example.com/clip.mp3` and `file:///tmp/clip.wav` were accepted in source/provenance refs.
   - This weakens the strict text-only boundary requested for `public_open_text_only`.

## Non-blocking gaps
- Focused tests do not explicitly cover the dict-as-list rejection case.
- Focused tests do not explicitly cover URL/file-extension audio refs in the `public_open_text_only` lane.

## Sufficiency assessment
- implemented_required_public_apis: yes
- schema_matches_plan: yes
- source_class_validation_sufficient: yes
- public_open_text_only_boundary_sufficient: no
- forbidden_source_rejection_sufficient: no
- blocker_enforcement_sufficient: yes
- normalized_speaker_auth_denylist_preserved: yes
- json_safe_behavior_sufficient: yes
- summary_behavior_safe: yes
- markdown_renderer_safe: yes
- tests_sufficient: no
- safe_non_runtime_helper: yes
- ready_for_context_alignment: no

## Final judgment
`synthetic_speech_corpus_helper_v1_needs_repair`

## Recommended next lane
`AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_SYNTHETIC_SPEECH_CORPUS_HELPER_V1_REVIEW`
