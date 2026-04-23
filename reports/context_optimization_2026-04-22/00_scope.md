# OCC Lightweight Context Optimization Pass — Scope

**Date:** 2026-04-22  
**Priority:** RED — reduce context pressure  
**Constraint:** Do NOT touch Infinity in this pass.

---

## Safety Confirmation

- **Working directory:** `/data/data/com.termux/files/home/.openclaw/workspace`
- **Config file to edit:** `/data/data/com.termux/files/home/.openclaw/openclaw.json`
- **Files planned for modification:** `openclaw.json` (Telegram disable only)
- **Infinity touching:** ❌ CONFIRMED — Infinity will NOT be touched
- **CLI/shebang touching:** ❌ CONFIRMED — CLI/shebang will NOT be touched

---

## Pass Mandate

This pass is only for lightweight context optimization:
1. Telegram removal first
2. Ollama/context inspection second
3. No heavy architecture work

---

## What This Pass IS NOT

- Not a redesign of any subsystem
- Not a compaction strategy change
- Not a model migration
- Not a session-memory overhaul
- Not touching Infinity in any way
