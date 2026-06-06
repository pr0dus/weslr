# WESLR Private Local Project Chat Smoke Test V1 — Run Result

## OCC Run Report

1. Run result
- PASS

2. Repo state
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `master`
- Start HEAD: `92eebb3`

3. Run target
- `Small matrix of 3 synthetic cases: success + missing approval + public mode blocked`

4. Files used
- `weslr/private_local_project_chat_smoke_test.py`
- `docs/WESLR_PRIVATE_LOCAL_PROJECT_CHAT_SMOKE_TEST_RUN_TARGET_SELECTION_V1.md`

5. Cases executed
- Owner-approved successful dry-run case
- Missing-owner-approval blocked case
- Public-mode blocked case

6. Results
- Success case returned an internal metadata-only result packet.
- Missing owner approval blocked.
- Public mode blocked.
- No answer delivery occurred.
- No provider/model/search/tool call occurred.
- No live retrieval occurred.
- No persistence or `.weslr` IO occurred.
- Blocked labels and provenance were preserved.
- Inputs remained synthetic only.

7. Validation
- Smoke-test matrix executed in-process via `run_private_local_project_chat_smoke_test_v1(...)`.
- Success case: `blocked=false`, `smoke_test_status=private_local_smoke_test_valid_metadata_only`
- Missing-owner-approval case: `blocked=true`, `blocked_labels` included `missing_owner_approval_metadata`
- Public-mode case: `blocked=true`, `blocked_labels` included `public_user_facing_mode_requested_must_be_false`
- `python3 -m pytest weslr/tests/test_private_local_project_chat_smoke_test_v1.py -q` — PASS
- `python3 -m pytest weslr/tests/test_private_local_project_chat_entrypoint_v1.py -q` — PASS
- `python3 -m pytest weslr/tests/test_controlled_private_project_chat_runtime_wiring_v1.py -q` — PASS
- `python3 -m pytest weslr/tests/test_workflow_integrity_red_zone_v1.py -q` — PASS
- `git diff --check` — PASS
- `git status --short` — reviewed
- `git status --short --untracked-files=all` — reviewed
- `git status --short --untracked-files=no` — reviewed
- `python3 weslr/tests/release_gate_v1.py` — PASS
- `bash scripts/weslr_release_check.sh` — PASS

8. Final judgment
- `weslr_private_local_project_chat_smoke_test_run_completed_ready_for_review`

9. Recommended next lane
- `REVIEW_WESLR_PRIVATE_LOCAL_PROJECT_CHAT_SMOKE_TEST_RUN_V1`

10. Commit message
- `WESLR: run private local project chat smoke test v1`
