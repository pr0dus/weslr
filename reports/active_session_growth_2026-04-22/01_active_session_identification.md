# Active Session Identification

## Active Session File

| Property | Value |
|----------|-------|
| **Path** | `/data/data/com.termux/files/home/.openclaw/agents/main/sessions/55a1f787-ce89-4c63-bade-978cd58112fc.jsonl` |
| **Size** | 479,483 bytes (~479 KB) |
| **Lines** | 125 JSON objects |
| **Format** | JSONL (newline-delimited JSON) |
| **Session ID** | `55a1f787-ce89-4c63-bade-978cd58112fc` |
| **Session Key** | `agent:main:main` |
| **Channel** | `webchat` |
| **Type** | Direct chat |
| **Started** | 2026-04-22T16:15:47 UTC |

## Registry Reference

- `sessions.json` references this file as `sessionFile` under `agent:main:main` key
- `sessions.json` also contains `skillsSnapshot` with full skills list (large block)
- `sessions.json` is separate from the session JSONL itself

## Session Structure (v3)

The file contains these entry types:
- `{"type":"session"}` — session metadata (1 entry)
- `{"type":"model_change"}` — model change markers
- `{"type":"thinking_level_change"}` — thinking level changes
- `{"type":"custom", "customType":"model-snapshot"}` — model snapshot records
- `{"type":"message"}` — user, assistant, and tool result messages

## How Entries Are Stored

Each entry is a single JSON object on one line. Every user message, assistant response, tool call, and tool result is stored as its own JSON object with full parent-child linkage via `id` and `parentId` fields.

## Is This File Growing?

Yes. It started at 267KB (when first inspected) and grew to 479KB during this session — a 79% increase in ~17 minutes of active use. Growth is approximately linear per exchange.
