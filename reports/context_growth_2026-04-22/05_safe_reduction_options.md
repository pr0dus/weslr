# Safe Reduction Options

## Options Considered

### Option 1: Disable session-memory hook
- **Change:** `hooks.internal.entries.session-memory.enabled: false`
- **Why safe:** Reduces heartbeat-triggered context re-injection; small files involved
- **Why not chosen:** The duplication is speculative — needs code inspection to confirm actual injection. Disabling without confirming could break continuity features.
- **Risk:** Medium — could break session continuity features

### Option 2: Clear or archive old session files
- **Change:** Delete `.reset.` and `.deleted.` session files in `/agents/main/sessions/`
- **Why safe:** Only deletes old historical data, not active session
- **Why not chosen:** Not a config change; requires file deletion. Not appropriate for this pass (no config edit).
- **Risk:** Low — historical data only

### Option 3: Leave everything as-is
- **Change:** None
- **Why safe:** No disruption to any system
- **Why chosen:** No clearly safe, high-confidence reduction found

---

## Decision: NO CHANGE in this pass

**Rationale:**
1. The primary context growth source is **session chat history** (session JSONL) — not something that can be safely disabled or reduced without breaking conversation continuity
2. `session-memory` hook is **speculatively duplicative** — not confirmed to inject redundant context without code inspection
3. `HEARTBEAT.md` is **empty** — no current burden
4. MEMORY.md is **static and valuable** — reducing it would lose important user context
5. The only aggressive option (clearing session history) is not appropriate for this pass

**All context growth sources found are either:**
- Intentional and necessary (chat history)
- Static (MEMORY.md)
- Empty/minimal (HEARTBEAT.md)
- Speculative (session-memory duplication — needs code inspection)

---

## What Was Left Untouched

- ❌ `hooks.internal.entries.session-memory` — disabled only if duplication confirmed via code inspection
- ❌ HEARTBEAT.md — already empty, no action needed
- ❌ MEMORY.md — high value, static, not the growth driver
- ❌ Session history (JSONL files) — necessary for conversation continuity
- ❌ Any workspace state files
- ❌ Infinity, Telegram, CLI/shebang
