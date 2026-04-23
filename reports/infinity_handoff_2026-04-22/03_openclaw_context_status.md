# OpenClaw Context Status

## Why Startup Is Fine

A fresh `/new` session starts at ~10% context because:
- Session history is empty (new JSONL file)
- Bootstrap files are truncated at 30%
- MEMORY.md is the largest single injection (~12KB after truncation)

## Why Long Sessions Become Heavy

1. **Raw full replay** — every turn stored verbatim in session JSONL
2. **Thinking blocks stored** — internal reasoning permanently in history
3. **Tool results stored** — large exec outputs, file reads embedded inline
4. **Bootstrap repeated** — system prompt embedded as first user message
5. **No summarization** — compaction (safeguard mode) hasn't triggered yet
6. **Linear growth** — ~2-8KB per exchange, no deduplication

## Why Fresh Session + Handoff Is Safer Than Editing Live Session

- The session JSONL is a running transcript — any manual edit risks JSON corruption
- Compaction triggers automatically when context window is ~80% full
- A fresh session starts at 10% — gives plenty of room to work
- All critical state is preserved in this handoff document, not in the session log

## What Was Already Improved This Session

1. **Telegram disabled** — no plugin + channel routing overhead
2. **maxTokens raised** — 8,192 → 16,384 (conservative, ~8% of context window)
3. **217 MB archived** — 303 inactive session files moved to `_archived_2026-04-22/`
4. **Session-memory** — enabled, appears low-overhead based on file sizes

## Current Context Pressure

- Active session: ~479 KB (and growing)
- Compaction threshold: ~160K tokens (80% of 196K context)
- Current estimated context: ~65K tokens (~33%)
- Safeguard not yet triggered (compactionCount: 0)
