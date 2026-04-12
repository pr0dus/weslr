# RECOVERY_STARTUP_STATUS_CHECKLIST_v1

Purpose: Provide a single canonical checklist to safely recover runtime state and operator awareness after interruptions/resets.

## Checklist
- **Branch/Worktree**: Confirm worktree path and branch (e.g., weslr/canonical-clean-signals) via `pwd`, `git branch --show-current`.
- **Active Phases**: Verify Phases 1–5 active and checkpointed (see PHASES_1_TO_5_ACTIVATION_SUMMARY_v1.md).
- **Canonical Path**: Ensure canonical conversational path uses route_request (thin client or approved service), not CLI speak or legacy UI.
- **Checkpoint Commits**: Note last stable checkpoint hashes for phases (1–5) and current HEAD.
- **Deferred Surfaces**: Browser/UI deferred; thin client/service is canonical; legacy/CLI speak non-default.
- **Open Items / Queued Suggestions**: Review suggestion orchestration outputs (existing follow-ups, new gaps) and pending approvals.
- **Runtime Safety Flags / Toggles**: Confirm governance gate on; Decision Layer rollback toggle state; acquisition proposals set to proposal-only; background analysis paused/active as intended.
- **Last Known Stable Checkpoint**: Record HEAD and phase checkpoint hashes for quick rollback/restart.

## Usage
Run this checklist at startup/resume or after interruptions before executing new work.
