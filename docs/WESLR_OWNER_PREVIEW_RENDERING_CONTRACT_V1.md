# WESLR Owner Preview Rendering Contract V1

## OCC Final Report

1. Handshake result
- PASS
- WESLR root/branch/HEAD matched the expected values.
- OCC workspace root/branch/HEAD matched the expected values.

2. Start HEAD
- `387fffb4aa6cec91dd3d50255b5ffad919235e3f`

3. Files changed
- `docs/WESLR_OWNER_PREVIEW_RENDERING_CONTRACT_V1.md`

4. Source artifacts reviewed
- `docs/WESLR_PROJECT_CHAT_UI_UX_OR_RUNTIME_DRY_RUN_NEXT_LANE_SELECTION_V1.md`
- `docs/WESLR_PRIVATE_PROJECT_CHAT_OWNER_PREVIEW_METADATA_HELPERS_REVISION_REVIEW_V1.md`
- `docs/WESLR_PRIVATE_PROJECT_CHAT_OWNER_PREVIEW_METADATA_HELPERS_REVISION_REPORT_V1.md`
- `docs/WESLR_PRIVATE_PROJECT_CHAT_OWNER_PREVIEW_METADATA_HELPERS_REVIEW_V1.md`
- `docs/WESLR_PRIVATE_PROJECT_CHAT_OWNER_PREVIEW_METADATA_HELPERS_IMPLEMENTATION_REPORT_V1.md`
- `docs/WESLR_PRIVATE_PROJECT_CHAT_OWNER_PREVIEW_BOUNDARY_REVIEW_V1.md`
- `docs/WESLR_PRIVATE_PROJECT_CHAT_OWNER_PREVIEW_BOUNDARY_V1.md`
- `docs/WESLR_CONTROLLED_PROJECT_CHAT_RUNTIME_SHELL_METADATA_HELPERS_REVIEW_V1.md`
- `docs/WESLR_CONTROLLED_PROJECT_CHAT_RUNTIME_SHELL_BOUNDARY_REVIEW_V1.md`

5. Rendering contract summary
- This contract defines how private owner-preview metadata packets may be safely displayed later.
- It is a bridge from metadata helpers to future UI design.
- It is not UI implementation.
- It is not runtime.
- It is not final-answer rendering.
- It is not public readiness.

6. Renderable packet categories
- preview shell decision summary
- blocked summary
- clarification summary
- approval summary
- operator-review summary
- answer-plan candidate summary
- retrieval-request candidate summary
- tool-lane candidate summary
- persistence candidate summary
- observability summary
- dry-run summary
- consumption-plan summary
- validation summary

7. Allowed display fields
- preview status
- readiness label
- user-visible status
- owner-visible summary
- operator-visible summary
- candidate packet type
- selected next metadata step
- blocked authority
- approval requirement
- clarification requirement
- operator-review requirement
- missing evidence flags
- stale/contradiction flags
- privacy flags
- limitations
- validation result
- redaction summary

8. Forbidden display fields
- private mechanism names
- hidden/system prompt
- raw traces
- raw private project data
- raw memory/project payloads
- raw `.weslr` state
- final answer text
- executed retrieval/tool/persistence results
- “I searched / I executed / I saved / I remembered”
- public-ready / certified / conscious / autonomous deployment claims

9. Rendering states/rules
- Rendering states:
  - `render_not_allowed`
  - `render_metadata_only`
  - `render_blocked`
  - `render_clarification_required`
  - `render_approval_required`
  - `render_operator_review_required`
  - `render_candidate_only`
  - `render_invalid`
  - `render_not_public_ready`
- Rendering rules:
  - missing owner/scope blocks rendering
  - invalid packet blocks rendering
  - unsafe wording blocks rendering
  - raw/private data blocks rendering
  - final-answer-like text blocks rendering
  - execution/persistence claims block rendering
  - public-readiness claims block rendering
  - synthetic/example packets are preferred
  - real private packet display requires later approval boundary

10. Owner safety model
- owner-only
- private/local or protected staging only
- no public access
- no tester access unless separately governed
- no cross-user data
- no raw private payload logs
- redaction by default

11. Denied authority
- runtime wiring
- chat responder
- final answer
- retrieval/SearXNG
- tool execution
- persistence/database
- `.weslr` IO
- memory/project mutation
- UI consumption implementation
- public access
- tester access
- private data exposure
- public readiness claim

12. Failure modes
- preview mistaken for live chat
- rendered text looks like final answer
- hidden/private mechanism leakage
- raw private data shown
- execution claim shown
- save/memory claim shown
- public-readiness implication
- UI implements more than contract allows

13. Future implementation validation
- Future rendering helper/UI work must prove:
  - disabled by default
  - owner-only
  - metadata-only
  - no raw private data
  - no runtime calls
  - no final answer text
  - no retrieval/tool/persistence execution
  - no `.weslr`
  - no unsafe wording
  - clear blocked/candidate labels
  - tests for forbidden fields and wording

14. Protected-file status
- Unchanged:
  - `weslr/chat_responder.py`
  - `weslr/main.py`
  - `main.py`
  - `dialogue.py`
  - `chat_ui.py`

15. Validation results
- `git diff --check`: pass
- `git status --short --untracked-files=no`: clean
- `git diff --stat`: clean
- `python3 weslr/tests/release_gate_v1.py`: pass
- `bash scripts/weslr_release_check.sh`: pass

16. Blocking gaps
- None in the contract itself.

17. Non-blocking gaps
- No rendering helper/UI implementation exists yet by design.

18. Final judgment
- `weslr_owner_preview_rendering_contract_design_ready_for_review`

19. Recommended next lane
- `REVIEW_WESLR_OWNER_PREVIEW_RENDERING_CONTRACT_V1`
