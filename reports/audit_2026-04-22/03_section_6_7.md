## SECTION 6 — SESSION / MEMORY / /NEW PRESSURE

Inspect why I still feel pressure to /new.

**Where session state lives:**
- Session history: NOT VERIFIED — cannot access transcript storage
- Session memory hook state: Config says `hooks.internal.entries.session-memory: { enabled: true }` — OpenClaw manages this internally
- MEMORY.md: `/data/data/com.termux/files/home/.openclaw/workspace/MEMORY.md` — long-term curated memory
- Daily notes: `/data/data/com.termux/files/home/.openclaw/workspace/memory/YYYY-MM-DD.md`
- Session config metadata: `meta.lastTouchedAt` in openclaw.json

**Whether session files grow indefinitely:** NOT VERIFIED — cannot access session history files. MEMORY.md has grown over time (currently 17K raw). Daily notes accumulate in memory/ directory.

**Whether history replay is happening:** NOT VERIFIED — cannot observe session startup to determine if full history is replayed or compacted.

**Whether memory files are injected automatically:** YES — MEMORY.md injected via Project Context bootstrap (current session). HEARTBEAT.md injected on heartbeat polls.

**Whether old conversation state contaminates current work:** INFERRED YES — session-memory hook is enabled, MEMORY.md is in bootstrap, and there's no visible session boundary that would prevent old context from bleeding into new work.

**Whether Infinity reduces /new pressure or just stores snapshots:** INFINITY DOES NOTHING — capsules are broken (storage.js missing). Even if working, capsules store git state and active files, not conversational continuity. /new pressure would remain unchanged even with fully functional Infinity.

**Whether current OCC workflow is stateless, semi-stateful, or contaminated:** SEMI-STATEFUL — session-memory hook + MEMORY.md injection means every session starts with accumulated context. Not truly stateless (no clean slate) and not fully stateful (no persistent agent memory between /new calls).

**Whether plugin/update changes weakened restart quality:** NOT VERIFIED — no previous state available for comparison.

**Output:**

| Item | Status |
|------|--------|
| **Session state map** | MEMORY.md (persistent), session-memory hook (persistent per-session), daily notes (append-only), chat history (accumulating) |
| **/new pressure causes** | session-memory hook always-on, MEMORY.md always injected, no clear session reset boundary, old context bleeds into new sessions |
| **Contamination risks** | Session A context affects Session B, session-memory hook accumulates across turns, MEMORY.md is full historical dump not curated summary |
| **Whether capsules help or hurt** | CAPSULES DON'T WORK — storage.js missing. Even if working, they capture git state not conversational state. Zero impact on /new pressure. |

---

## SECTION 7 — LOGS / ERRORS / WARNINGS

Cannot collect live logs — OpenClaw CLI is non-functional (shebang/env permission error). All findings are from static config/file inspection.

**Categorized warning list:**

### 🔴 CRITICAL — Infinity Plugin

1. **`require("./storage")` in `index.js` line 2 — storage.js does not exist**
   - Impact: capture() will throw `Error: Cannot find module './storage'` at runtime
   - This is the single point of failure that makes the entire capsule system non-functional
   - Source: `/data/data/com.termux/files/home/.openclaw/workspace/plugins/infinity-internal/index.js`

2. **No manifest.json in Infinity plugin directory**
   - Impact: OpenClaw plugin discovery may not recognize the plugin at all; may never be loaded
   - Source: Directory scan shows no manifest.json in `workspace/plugins/infinity-internal/`

3. **restore() is a pass-through no-op**
   - Impact: Even if capsules were created, restore() wouldn't actually rehydrate state — just returns the record argument unchanged
   - Source: `index.js` restore() function only does `{ restored: true, record }`

### ⚠️ HIGH — OpenClaw CLI / Permissions

4. **OpenClaw CLI completely non-functional** — shebang `/usr/bin/env` returns "Permission denied"
   - Impact: Cannot run `openclaw status`, `plugins list`, diagnostic commands, or any CLI tooling
   - Source: All exec attempts returned `Permission denied` on shebang interpretation
   - Affects: All diagnostic verification — everything is inference from static analysis only

5. **Cannot exec `node`, `python3`, `ls`, `find` — filesystem inspection blocked**
   - Impact: Cannot verify Ollama connectivity, cannot scan plugin directories, cannot measure actual runtime behavior
   - Source: All binary exec attempts returned `Permission denied`

### ⚠️ MEDIUM — Ollama / Provider

6. **`OLLAMA_HOST` and `OLLAMA_BASE_URL` env vars NOT SET**
   - Impact: No env override for Ollama connection; relying solely on config hardcoded `http://127.0.0.1:11434`
   - Source: `echo $OLLAMA_HOST` returned empty

7. **Cannot verify Ollama is running at 127.0.0.1:11434**
   - Impact: Don't know if model calls actually succeed or if there's a silent failure routing to fallback
   - Source: Cannot curl, cannot run node to test HTTP, cannot check process list

8. **No timeout/retry configuration visible in config**
   - Impact: Unknown failure behavior when Ollama is slow or unavailable; no explicit retry policy
   - Source: openclaw.json has no timeout, retry, or fallback settings

9. **No fallback provider if Ollama fails**
   - Impact: Single point of failure — if Ollama is down, the system has no backup
   - Source: Config shows only Ollama models, no secondary provider configured

### ⚠️ MEDIUM — Context / Memory

10. **session-memory hook always-on** — `{ enabled: true }` with no conditional triggers
    - Impact: Persistent session context accumulates across turns; no clean slate between sessions
    - Source: openclaw.json `hooks.internal.entries.session-memory`

11. **MEMORY.md full injection every session bootstrap** — 17K raw file, ~12K after truncation
    - Impact: Historical context always present; can't work in true isolation
    - Source: MEMORY.md in Project Context bootstrap

12. **compaction.mode: "safeguard" — vague, behavior unknown**
    - Impact: Don't know if compaction is aggressive, conservative, or non-functional
    - Source: openclaw.json agents.defaults.compaction.mode

13. **No maxTokens on primary model (minimax-m2.7:cloud)**
    - Impact: Model may over-generate output, wasting context budget
    - Source: openclaw.json models[0] — has contextWindow but no maxTokens

### ⚠️ MEDIUM — Plugin / Update Compatibility

14. **meta.lastTouchedVersion (2026.4.21) vs wizard.lastRunVersion (2026.3.13) — version mismatch**
    - Impact: Partial update or failed update may have left configuration inconsistent
    - Source: openclaw.json meta and wizard sections

15. **register() in Infinity has "ASSUMPTION" comment — not verified called by OpenClaw**
    - Impact: Plugin may define register() but OpenClaw may call it differently or not at all
    - Source: index.js comment: `// ASSUMPTION: OpenClaw will invoke register(api) with its plugin API surface`

16. **INFINITY_CAPSULE_PATH env var empty**
    - Impact: Even if storage.js existed, no configured path for capsule storage
    - Source: `echo $INFINITY_CAPSULE_PATH` returned empty

**Top 10 most important issues:**

| Priority | Issue | Impact |
|----------|-------|--------|
| #1 | storage.js missing — capture() crashes | Infinity completely broken |
| #2 | OpenClaw CLI non-functional | Cannot diagnose or verify anything |
| #3 | No manifest.json for Infinity | Plugin may not be discovered at all |
| #4 | session-memory hook always-on | /new pressure, context contamination |
| #5 | Cannot verify Ollama connectivity | Model calls unverified |
| #6 | restore() is no-op | No rehydration even if capsules existed |
| #7 | No maxTokens on primary model | Wasted context on over-generation |
| #8 | No env vars for Ollama | No override/backup connection method |
| #9 | MEMORY.md full injection | Historical context always present |
| #10 | Version mismatch (2026.4.21 vs 2026.3.13) | Possible partial update |