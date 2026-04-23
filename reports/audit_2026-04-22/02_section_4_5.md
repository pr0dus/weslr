## SECTION 4 — PROVIDER / MODEL / OLLAMA REALITY

**Active provider:** `ollama` (from config.primary model: `ollama/minimax-m2.7:cloud`)

**Provider config (from openclaw.json):**
```json
{
  "api": "ollama",
  "apiKey": "ollama-local",
  "baseUrl": "http://127.0.0.1:11434",
  "models": [
    {
      "id": "minimax-m2.7:cloud",
      "contextWindow": 196608,
      "name": "minimax-m2.7:cloud",
      "reasoning": true,
      "input": ["text"],
      "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 }
    },
    {
      "id": "qwen3-coder-next:cloud",
      "contextWindow": 262144,
      "name": "qwen3-coder-next:cloud",
      "reasoning": false,
      "maxTokens": 8192,
      "input": ["text"],
      "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 }
    }
  ]
}
```

**All configured models:**
| Model | Context Window | Reasoning | Cost |
|-------|---------------|-----------|------|
| `minimax-m2.7:cloud` | 196,608 | YES | FREE (0/0) |
| `qwen3-coder-next:cloud` | 262,144 | NO | FREE (0/0) |
| `glm-5.1:cloud` | 202,752 | YES | FREE |

**Environment variables:**
```
OLLAMA_HOST         = NOT SET (empty)
OLLAMA_BASE_URL     = NOT SET (empty)
INFINITY_CAPSULE_PATH = NOT SET (empty)
```

**Ollama host URL:** `http://127.0.0.1:11434` (hardcoded in config baseUrl)

**Active model:** `ollama/minimax-m2.7:cloud` (primary in agents.defaults)

**Fallback chain:** Config shows `mode: "merge"` for models — not a strict fallback chain

**Silent fallbacks:** NOT VERIFIED — cannot observe actual HTTP traffic or Ollama logs

**Timeout/retry/token settings:** NOT VISIBLE in config — no explicit timeout, retry, or token limit settings found in openclaw.json

**Context-related settings found:**
- `compaction.mode: "safeguard"` in agents.defaults — some safeguard compaction exists
- `maxTokens: 8192` only set for `qwen3-coder-next:cloud`, NOT for `minimax-m2.7:cloud`
- `contextWindow: 196608` on minimax-m2.7 model — this is the model-declared window

**Ollama connectivity evidence:** CANNOT VERIFY — `openclaw status` fails, `curl` not tested, cannot run node/python

**Whether actual calls go to Ollama:** NOT VERIFIED — no exec possible to observe traffic

**Model fitness for coding + long context:**
- `minimax-m2.7:cloud` — 196K context, reasoning enabled — reasonably suited
- `qwen3-coder-next:cloud` — 262K context, no reasoning, `maxTokens: 8192` — could be better for coding
- All models are free (cost: 0) — no billing risk

### Provider routing reality:
- Single Ollama provider with 3 models (minimax-m2.7:cloud, glm-5.1:cloud, qwen3-coder-next:cloud)
- Active model is minimax-m2.7:cloud (primary)
- Models mode is "merge" — not a fallback chain, all available simultaneously
- No secondary provider configured as fallback
- baseUrl is hardcoded to http://127.0.0.1:11434

### Active model chain:
```
agents.defaults.model.primary = "ollama/minimax-m2.7:cloud"
→ resolves to models[0] in ollama provider
→ contextWindow: 196608, reasoning: true, maxTokens: NOT SET
```

### Actual Ollama connectivity evidence:
CANNOT VERIFY — all exec blocked. Inference only:
- Config has correct baseUrl format
- apiKey is set to "ollama-local" (placeholder, not a real key)
- No timeout or retry — unknown failure behavior

### Silent fallback or misrouting warning:
NOT VERIFIED — cannot observe HTTP traffic. Cannot confirm if requests actually reach Ollama.

---

## SECTION 5 — CONTEXT WINDOW REALITY

| Layer | Value | Source |
|-------|-------|--------|
| **Configured max** | 196,608 (minimax-m2.7) | `openclaw.json` → models[0].contextWindow |
| **Model theoretical max** | 262,144 (qwen3-coder-next) | `openclaw.json` → models[1].contextWindow |
| **Provider enforced** | UNKNOWN | Cannot verify Ollama server-side limits |
| **Effective practical** | UNKNOWN | Cannot measure actual delivery |

**Memory budget competitors (identified):**
1. `hooks.internal.entries.session-memory: { enabled: true }` — session memory auto-injected on every session
2. `COMPACTION` mode `safeguard` — some form of context compaction exists but details unknown
3. `MEMORY.md` + `memory/*.md` — injected via Project Context bootstrap (current session gets all of MEMORY.md truncated at ~12K chars)
4. Active chat history — full message history in context window
5. `HEARTBEAT.md` — injected on heartbeats

**Infinity capsule impact on context:** NOT APPLICABLE — capsules are not working (storage missing)

**Slash-command / session logs inflation:** NOT VERIFIED — cannot observe history size

**Summarization/truncation/compression:** `compaction.mode: "safeguard"` exists but specifics unknown

**Session memory injection:** YES — `session-memory` hook is enabled and will inject memory into context

**OpenClaw update context changes:** NOT VERIFIED — last touched version is `2026.4.21`, previous unknown

**Current context usage vs max:** NOT VERIFIED — cannot measure token count in current session

**Main context waste sources (inferred, not verified):**
1. Full MEMORY.md injection (17K file → ~12K injected) on every session bootstrap
2. Session history accumulating across turns
3. `session-memory` hook adding memory layer on top of history
4. Heartbeat polling injecting additional context

| Metric | Value | Notes |
|--------|-------|-------|
| **Configured maximum** | 196,608 tokens | minimax-m2.7:cloud contextWindow |
| **Model theoretical maximum** | 262,144 tokens | qwen3-coder-next:cloud, larger model |
| **Effective practical maximum** | UNKNOWN | Cannot measure actual usage |
| **Main context waste sources** | session-memory hook, MEMORY.md full injection, no visible compaction metrics, no token counting | All historical context re-injected every session |

**Top 5 opportunities to improve usable context without losing continuity:**
1. Add explicit `maxTokens: 8192` to `minimax-m2.7:cloud` — prevents over-generation waste, current model has 196K input but no output cap
2. Disable or make opt-in the `session-memory` hook — it duplicates MEMORY.md and history, creating triple injection of same context
3. Implement lightContext for sub-agent sessions — spawned sub-agents inherit full session context unnecessarily; `lightContext: true` flag would reduce this
4. Add token usage monitoring — no visibility into actual token counts means all optimization is guesswork; add logging/metrics for prompt tokens, completion tokens, total session tokens
5. Separate compaction strategy from safeguard mode — "safeguard" is vague; investigate actual compaction thresholds and tune or replace with explicit strategy