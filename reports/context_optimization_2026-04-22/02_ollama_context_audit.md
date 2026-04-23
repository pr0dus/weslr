# Ollama / Model / Context Audit

## Config Table

| Setting | Value | Location |
|---------|-------|----------|
| **Primary model** | `ollama/minimax-m2.7:cloud` | `agents.defaults.model.primary` |
| **Primary context window** | 196,608 tokens | `models.providers.ollama.models[0]` |
| **Primary maxTokens** | 8,192 | `models.providers.ollama.models[0]` |
| **Fallback models** | glm-5.1:cloud (202,752), qwen3-coder-next:cloud (262,144) | `models.providers.ollama.models[]` |
| **Compaction mode** | `safeguard` | `agents.defaults.compaction.mode` |
| **Session-memory hook** | `enabled: true` | `hooks.internal.entries.session-memory` |
| **Ollama host** | `http://127.0.0.1:11434` | `models.providers.ollama.baseUrl` |
| **Provider** | ollama (local) | `provider_config.json` |

## Context Pressure Sources

| Source | Severity | Notes |
|--------|----------|-------|
| MEMORY.md injection | HIGH | 17,166 chars, heavily truncated in bootstrap |
| session-memory hook | HIGH | Injects session context every heartbeat |
| bootstrap files (HEARTBEAT.md, IDENTITY.md, etc.) | MEDIUM | Multiple files injected on every session start |
| continuity/artifacts/ | MEDIUM | 60+ artifact JSON files in continuity/ |
| dashboard_history.json | MEDIUM | 59,609 bytes |
| main.py | LOW | 361,596 bytes — not in context unless loaded |
| messages.json | LOW | 308 bytes |
| entity_graph.json | LOW | 149 bytes |

## Top Likely Causes of "100% Context Feeling"

1. **MEMORY.md at ~17KB injected into every bootstrap** — largest single text chunk
2. **session-memory hook** adds continuous background context on heartbeats
3. **continuity/artifacts/** directory with 60+ files — all potentially scannable
4. **Dashboard/workspace state files** loaded but not obviously needed for OCC

## Model Config Assessment

The `minimax-m2.7:cloud` config is **sensible but potentially wasteful**:
- 196,608 context window is large but appropriate for coding tasks
- 8,192 maxTokens is conservative — could be raised to 16,384 safely
- `safeguard` compaction mode is conservative — correct for this pass
- Model has `reasoning: true` — appropriate for the task

**Assessment:** Model config is reasonable. No urgent changes needed. maxTokens could be slightly higher but not critical.
