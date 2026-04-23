# Active Session Growth Investigation — Scope

**Date:** 2026-04-22

---

## Context

- `/new` starts at ~10% context → **startup is acceptable**
- The problem is **long-session context growth over time**
- This pass inspects only the **current active session** behavior
- No config changes unless one tiny safe change is overwhelmingly justified

## What This Pass Is NOT

- Not a redesign of the session format
- Not a compaction architecture change
- Not touching Infinity, WESLR, CLI/shebang, Telegram, or model config
- Not implementing new history management
