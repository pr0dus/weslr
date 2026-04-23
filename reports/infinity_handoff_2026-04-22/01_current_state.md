# Current OpenClaw State

## Model Configuration

| Setting | Value |
|---------|-------|
| **Primary model** | `ollama/minimax-m2.7:cloud` |
| **Context window** | 196,608 tokens |
| **maxTokens** | 16,384 (raised from 8,192 in this session) |
| **Reasoning** | Enabled |
| **Compaction mode** | `safeguard` |

## Telegram

- **Status:** Disabled (`channels.telegram.enabled: false`, `plugins.entries.telegram.enabled: false`)
- Bot token preserved in config for potential re-enablement
- No Telegram files deleted

## Session Files

- **Archived:** 303 inactive session files moved to `_archived_2026-04-22/` (~217 MB)
- **Active:** Current session `55a1f787-ce89-4c63-bade-978cd58112fc.jsonl` (~479 KB, 125 entries, raw full replay)
- **compactionCount:** 0 — safeguard has not triggered yet

## Active Workspace Context

- **Workspace path:** `/data/data/com.termux/files/home/.openclaw/workspace`
- **Gateway:** Running locally on port 18789, loopback bind
- **Plugin allowlist:** `telegram, infinity-internal, ollama, github-copilot, openai, browser, memory-core`
- **Enabled plugins:** `infinity-internal` (enabled: true), `ollama`, `github-copilot`, `openai`, `browser`

## Gateway Auth

- Token mode enabled: `7eac90ac8a1566a7856c0660025fa5765ce62587a53b6ed7`
- Tailscale: OFF
