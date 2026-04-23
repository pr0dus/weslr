# Scope — Minimal Tokenmax + Session Archive Pass

**Date:** 2026-04-22

---

## Scope Boundaries

- **WESLR continuity files:** OUT OF SCOPE — not touched
- **Infinity:** OUT OF SCOPE — not touched
- **CLI/shebang:** OUT OF SCOPE — not touched
- **Memory/session architecture redesign:** OUT OF SCOPE — not touched

---

## This Pass Covers Only

1. **Tokenmax increase** — conservative raise on primary model maxTokens
2. **Session archive** — move clearly inactive OpenClaw session files to archive folder

---

## Archive Criteria

Archived files (moved, not deleted):
- All `*.reset.*` files — old session resets
- All `*.deleted.*` files — deleted sessions
- All `*.bak.*` files — old backups
- All `*.checkpoint.*` files — checkpoint files

NOT moved (left active):
- Plain `*.jsonl` files without reset/deleted/bak suffix
- `sessions.json` — session registry
- `sessions/` folder itself
- `sessions.jsonl.lock` — lock file
