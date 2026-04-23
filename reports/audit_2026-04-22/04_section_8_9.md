## SECTION 8 — COMPATIBILITY AFTER UPDATE

Based on actual inspection, determine whether the recent OpenClaw update likely broke:

**Plugin API compatibility:**
- Status: ⚠️ RISKY
- Evidence: No manifest.json in Infinity plugin; register() has "ASSUMPTION" comment; cannot verify OpenClaw actually calls register() with expected API surface
- Conclusion: Update may have changed plugin API contract or discovery requirements. Infinity's "staged" status suggests it's not fully integrated.

**Plugin discovery path assumptions:**
- Status: ✅ OK
- Evidence: Config explicitly sets `plugins.load.paths: ["/data/data/com.termux/files/home/.openclaw/workspace/plugins"]` — this is unambiguous and likely unchanged
- Conclusion: Path is correct. If plugin isn't discovered, it's due to missing manifest, not path change.

**Manifest schema assumptions:**
- Status: ❓ UNKNOWN
- Evidence: No manifest.json found in Infinity plugin directory. Cannot compare against expected schema because there's no manifest to compare.
- Conclusion: This is a pre-existing gap, not something the update broke. However the update may have introduced a manifest requirement that Infinity never satisfied.

**Register hook behavior:**
- Status: ⚠️ RISKY
- Evidence: `register()` defined but only has a comment assuming OpenClaw will call it. No evidence OpenClaw actually invokes register() in current setup. Cannot verify with `openclaw plugins list` (CLI broken).
- Conclusion: Unclear if update changed register() call pattern. The "ASSUMPTION" comment suggests this was never verified against real OpenClaw behavior.

**Capture/restore wiring:**
- Status: 🔴 BROKEN
- Evidence: storage.js missing — capture() crashes before storing. restore() is pass-through. This is not an update regression — the plugin was never functional.
- Conclusion: Pre-existing broken state, not caused by update. Even if update changed wiring, nothing would work anyway due to missing storage.

**Provider config assumptions:**
- Status: ✅ OK
- Evidence: Ollama config has standard fields: api, apiKey, baseUrl, models array. Format looks like standard provider config. No signs of incompatibility.
- Conclusion: Provider config survived the update intact.

**Context budgeting assumptions:**
- Status: ⚠️ RISKY
- Evidence: No explicit token limits on primary model. Compaction mode "safeguard" is vague — behavior unknown. No visibility into whether update changed context handling.
- Conclusion: Update may have changed context behavior but there's no way to verify without CLI access. "Safeguard" compaction may be new or changed, but can't confirm.

**Summary table:**

| Area | Status | Evidence |
|------|--------|----------|
| Plugin API compatibility | ⚠️ RISKY | No manifest; register() assumption not verified |
| Plugin discovery path | ✅ OK | Path explicitly configured and correct |
| Manifest schema | ❓ UNKNOWN | No manifest exists to assess |
| Register hook behavior | ⚠️ RISKY | Assumed but never verified |
| Capture/restore wiring | 🔴 BROKEN | Pre-existing broken (storage missing) |
| Provider config | ✅ OK | Standard Ollama config format intact |
| Context budgeting | ⚠️ RISKY | Compaction mode vague; token limits absent |

---

## SECTION 9 — BOTTLENECK RANKING

Rank the biggest current bottlenecks from most important to least important for these goals:

### A) Strong Infinity capsule integration

| Rank | Bottleneck | What It Is | Evidence | Impact | Fix Class |
|------|-----------|------------|----------|--------|-----------|
| **#1** | **storage.js missing** | Module that persistence.py would call doesn't exist | `require("./storage")` in index.js — file not found | capture() crashes — no capsule ever created or stored | Plugin file missing — recreate storage.js |
| **#2** | **No manifest.json** | Plugin discovery metadata absent | Directory scan shows no manifest.json | OpenClaw may never discover or load the plugin | Add manifest.json to plugin directory |
| **#3** | **restore() is a no-op** | restore() only returns what it's given, doesn't load from storage | index.js restore() function: `return { restored: true, record }` — pass-through only | Even if capsules were stored, restore wouldn't rehydrate anything | Rewrite restore() to call storage.load() |
| **#4** | **register() assumption not verified** | Comment says "ASSUMPTION" — no proof OpenClaw calls it | index.js line: `// ASSUMPTION: OpenClaw will invoke register(api)` | Plugin may be loaded but its capture/restore hooks never registered with OpenClaw | Verify plugin API call pattern; add logging to confirm |
| **#5** | **INFINITY_CAPSULE_PATH not set** | Environment variable for storage location is empty | `echo $INFINITY_CAPSULE_PATH` returned empty | Even if storage.js existed, no one knows where to store capsules | Add storage path config or env var |

### B) Less need for /new

| Rank | Bottleneck | What It Is | Evidence | Impact | Fix Class |
|------|-----------|------------|----------|--------|-----------|
| **#1** | **session-memory hook always-on** | OpenClaw persists session context across turns with no opt-out | openclaw.json: `hooks.internal.entries.session-memory: { enabled: true }` | Every /new still carries accumulated session state via hook | Config: add conditional trigger or opt-in mode |
| **#2** | **MEMORY.md full injection** | Long-term memory file (17K) injected entirely at bootstrap | MEMORY.md in Project Context — ~12K after truncation | Historical context bleeds into every session regardless of /new | Architecture: curated summary vs raw MEMORY.md injection |
| **#3** | **No clear session reset boundary** | /new clears chat history but session-memory and MEMORY.md persist | No configuration defining what /new should actually reset | Partial reset only — not a true fresh start | Workflow: define explicit /new reset contract |
| **#4** | **Compaction behavior unknown** | "safeguard" mode vague — may not actually reduce context | openclaw.json: `compaction.mode: "safeguard"` — no docs | May be doing nothing or being too aggressive — can't tune | Config: document or investigate safeguard thresholds |

### C) Better long-context coding

| Rank | Bottleneck | What It Is | Evidence | Impact | Fix Class |
|------|-----------|------------|----------|--------|-----------|
| **#1** | **No maxTokens on primary model** | minimax-m2.7:cloud has contextWindow but no output cap | openclaw.json models[0] — no maxTokens field | Model may over-generate, wasting context budget on filler | Config: add `maxTokens: 8192` to primary model |
| **#2** | **Cannot measure actual token usage** | No visibility into prompt/completion token counts | Cannot exec any tool to measure | All optimization is guesswork — may be under or over budget | Tooling: add token counting/logging |
| **#3** | **Context budget shared without isolation** | Session history + MEMORY.md + session-memory + heartbeats compete for same 196K | All present in context simultaneously | No resource management — consumers starve each other | Architecture: separate budget pools or prioritization |
| **#4** | **qwen3-coder-next has 262K context but 8K maxTokens** | Larger model capped at small output | openclaw.json models[1]: contextWindow 262144, maxTokens 8192 | Huge input capacity wasted by output cap | Config: increase maxTokens or use differently |
| **#5** | **No proactive summarization** | Context grows until hitting hard limit, then truncation | No summarization strategy visible in config | Important context may be lost to hard truncation | Architecture: add proactive summarization before limit |

### D) Correct Ollama usage

| Rank | Bottleneck | What It Is | Evidence | Impact | Fix Class |
|------|-----------|------------|----------|--------|-----------|
| **#1** | **Cannot verify Ollama is running** | No way to confirm 127.0.0.1:11434 is reachable and responding | Cannot curl, cannot exec node to HTTP call, cannot check process | Don't know if model calls succeed or silently fail | Tooling: verify Ollama endpoint connectivity |
| **#2** | **OLLAMA_HOST / OLLAMA_BASE_URL not set** | No environment variable override for connection | `echo $OLLAMA_HOST` empty, `echo $OLLAMA_BASE_URL` empty | Single point of failure — no fallback connection method | Config: set env vars or add secondary URL |
| **#3** | **No timeout or retry policy** | Unknown behavior when Ollama is slow or unavailable | No timeout/retry in config | Silent failures or hung requests with no recovery | Config: add timeout and retry settings |
| **#4** | **All models free — cost unknown** | Cost set to 0 for all models — no cost signal | openclaw.json models cost: all zeros | Cannot optimize for cost efficiency if Ollama has metered usage | Config: add cost tracking if applicable |
| **#5** | **No fallback provider** | No secondary provider if Ollama fails | Only Ollama models in config | Complete failure if Ollama goes down | Config: add fallback provider |

### E) Maximum stable context efficiency

| Rank | Bottleneck | What It Is | Evidence | Impact | Fix Class |
|------|-----------|------------|----------|--------|-----------|
| **#1** | **Context consumers not measured** | No token counting — competing consumers (history, memory, hooks) unquantified | Cannot exec any measurement tool | Optimizing blind — don't know what's consuming the budget | Tooling: add per-source token accounting |
| **#2** | **Compaction mode "safeguard" behavior unknown** | Vague name — no documentation of what it actually does | openclaw.json: `compaction.mode: "safeguard"` | May be non-functional or too conservative — can't tune | Config: investigate or replace with explicit strategy |
| **#3** | **No summarization strategy** | Context grows indefinitely until hitting limit | No summarization mentioned in config | Hard truncation loses important context | Architecture: proactive summarization pipeline |
| **#4** | **lightContext not configured for sub-agents** | Spawned sub-agents inherit full session context | No lightContext setting in agents config | Wastes context on agent-to-agent communication | Config: enable lightContext for sub-agent runs |
| **#5** | **MEMORY.md bootstrap truncation** | 17K file → ~12K injected (30% removed at bootstrap) | Project Context shows MEMORY.md truncated | May be discarding important memory content | Architecture: more selective injection or smaller source |