# Context Growth Investigation — Scope

**Date:** 2026-04-22  
**Key Fact:** `/new` starts at ~10% context — startup is acceptable  
**Focus:** Growth over time, not startup weight

---

## Scope Statement

- `/new` starts around 10% context → startup weight is NOT the main problem
- Problem is **context accumulation during ongoing use**
- This pass identifies growth sources only — no redesign
- Infinity is out of scope (do not touch)
- Telegram already disabled (do not touch again)

---

## What This Investigation Is NOT

- Not a redesign of the session-memory system
- Not a MEMORY.md rewrite
- Not a compaction strategy change
- Not touching Infinity, Telegram, CLI/shebang
