# WORKFLOW_EXECUTION_CONTRACT_v1

## Purpose
Eliminate repo/worktree confusion, dirty-state contamination, and cross-project leaks by enforcing clear work lanes, ownership, preflight, and commit blockers across WESLR core, host/front-door, and external projects.

## Work Lanes
- **WESLR Core Lane**: weslr/ code, weslr_state/, WESLR docs/tests, adapters directly tied to WESLR governance/ingress. Worktree example: workspace_clean_signals or a dedicated clean WESLR worktree.
- **Host/Front-Door Lane**: chat_ui/front-door bridges, host-side launch scripts, identity cache, ingress wiring. Isolated worktree recommended for host changes.
- **External Project Lane (Infinity/TIA/etc.)**: plugins/infinity/, activation assets, any non-WESLR projects. Must not be touched during WESLR-only work.

## File Ownership
- **WESLR Core**: weslr/, weslr_state/, weslr/tests/, WESLR-focused docs in docs/ that describe core contracts (ingress, identity/continuity, role/permission, core resolution).
- **Host/Front-Door**: chat_ui.py, host-side scripts (scripts/start_chat_ui.sh, launch_chat_ui.py), front-door tests (tests/test_chat_ui_identity_cache.py when run from host lane), host-facing docs for ingress/bridge contracts.
- **External (Infinity/TIA)**: plugins/infinity*/ and related assets; not to be staged/committed in WESLR or host lanes.

## Clean-Worktree Rule
- Use clean, project-scoped worktrees for commits. Do not commit from dirty monorepo roots. If another lane has conflicts (e.g., Infinity), create/use a clean WESLR worktree and commit only allowed files there.

## Preflight Check (before coding/commit)
1) `pwd` — confirm expected worktree path.
2) `git branch --show-current` — confirm lane branch (e.g., weslr/canonical-clean-signals for WESLR).
3) `git status --short` — ensure only lane-owned files are touched; no conflicts (no "UU").
4) Touched files review — verify they belong to the current lane.
5) Confirm no unresolved conflicts anywhere in the worktree.
6) If any check fails, stop and switch to a clean worktree or resolve within the correct lane.

## Commit Blockers
- Unresolved conflicts (`git status` shows UU).
- Dirty files from other lanes (e.g., Infinity files when in WESLR lane).
- Unknown or mixed-ownership files staged for commit.
- Unclean worktree used for WESLR commits (dirty host tree, unrelated changes).
- Missing/failed targeted tests for touched areas (run targeted pytest for front-door/WESLR changes).

## Handoff Rule (Core ↔ Host)
- Changes in WESLR core (e.g., exposing decision_snapshot) should be committed in WESLR lane, then consumed by host/front-door via clean pull/worktree. No ad-hoc copying of core into host.
- Host/front-door changes (e.g., identity cache, PYTHONPATH launcher) must stay in host lane; do not commit WESLR core files alongside host changes unless explicitly required and in a clean WESLR worktree.
- Use documented contracts (CORE_RESOLUTION_CONTRACT_v1, IDENTITY_CONTINUITY_BOUNDARY_CONTRACT_v1, ROLE_PERMISSION_CONTRACT_v1) to guide handoff; avoid bespoke path hacks.

## Status
- Contract defined here; no runtime code changes in this doc.
