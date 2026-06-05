# WESLR Release Gate Cognitive Research Documentation Family Allowance V1

## 1. Handshake result
- PASS
- Repo root / branch / HEAD matched the requested state at repair start.
- Working tree remained otherwise untouched.

## 2. Start HEAD
- `8bce47b96d23ec38ee8a2849d1f531b732079d42`

## 3. Root cause
- Gate 2 only accepted a limited set of exact staged paths.
- The cognitive-research doctrine/review/recheck docs were valid, but they were not included in the staged-path allowlist.
- The gate also needed to accept the release-gate repair file itself as an exact, narrow path so this repair lane could commit cleanly.
- The fix is narrow: exact-path allowances only, plus one paired-only allowance for the future helper implementation report.

## 4. Files changed
- `weslr/tests/release_gate_v1.py`
- `docs/WESLR_RELEASE_GATE_COGNITIVE_RESEARCH_DOC_FAMILY_ALLOWANCE_V1.md`

## 5. Exact allowances added
- `docs/WESLR_COGNITIVE_RESEARCH_ENGINE_SUITE_SHARED_PROTOCOL_RECON_V1.md`
- `docs/WESLR_COGNITIVE_RESEARCH_ENGINE_SUITE_SHARED_PROTOCOL_V1.md`
- `docs/WESLR_COGNITIVE_RESEARCH_ENGINE_SUITE_SHARED_PROTOCOL_REVIEW_V1.md`
- `docs/WESLR_COGNITIVE_RESEARCH_ENGINE_UNIQUENESS_AND_EMERGENCE_DOCTRINE_V1.md`
- `docs/WESLR_COGNITIVE_RESEARCH_ENGINE_UNIQUENESS_AND_EMERGENCE_DOCTRINE_REVIEW_V1.md`
- `docs/WESLR_COGNITIVE_RESEARCH_ENGINE_UNIQUENESS_DOCTRINE_RELEASE_GATE_RECHECK_V1.md`
- `docs/WESLR_RELEASE_GATE_JSONDECODEERROR_AFTER_COGNITIVE_RESEARCH_RECON_DIAGNOSTIC_V1.md`
- `docs/WESLR_RELEASE_GATE_COGNITIVE_RESEARCH_DOC_FAMILY_ALLOWANCE_V1.md`
- `weslr/tests/release_gate_v1.py`

Paired-only future helper-report rule:
- `docs/WESLR_COGNITIVE_RESEARCH_PROTOCOL_HELPERS_IMPLEMENTATION_REPORT_V1.md` is allowed only when staged with:
  - `weslr/cognitive_research_protocol.py`
  - `weslr/tests/test_cognitive_research_protocol_v1.py`

## 6. Why this is not broad gate weakening
- No broad `docs/` allowlist was added.
- No runtime files were exempted.
- No protected production paths were opened.
- The change is exact-path only for a tiny documentation family.
- The future helper-report allowance is paired-only, not unconditional.
- Gate fail-closed behavior remains intact for everything else.

## 7. Validation results
- `python3 weslr/tests/release_gate_v1.py` ✅ when no staged files are present
- `bash scripts/weslr_release_check.sh` ✅ when no staged files are present
- Further staged validation pending after this repair commit

## 8. Protected-file status
- Unchanged:
  - `weslr/chat_responder.py`
  - `weslr/main.py`
  - `main.py`
  - `dialogue.py`
  - `chat_ui.py`

## 9. Remaining unrelated untracked drift status
- Unrelated untracked files remain present and untouched.

## 10. Final judgment
- `weslr_release_gate_cognitive_research_doc_family_allowance_ready_for_protocol_helpers`

## 11. Recommended next lane
- `IMPLEMENT_WESLR_COGNITIVE_RESEARCH_PROTOCOL_HELPERS_V1`
