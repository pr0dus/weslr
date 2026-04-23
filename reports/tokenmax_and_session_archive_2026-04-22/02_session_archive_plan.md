# Session Archive Plan

## Archive Criteria

Files moved to archive must match:
- `*.reset.*` — session files that were reset (historical)
- `*.deleted.*` — session files explicitly deleted by the system
- `*.bak.*` — old backup files
- `*.checkpoint.*` — checkpoint files

## Files Selected for Archive

| Pattern | Count | Description |
|---------|-------|-------------|
| `*.reset.*` | 282 | Session reset snapshots |
| `*.deleted.*` | 20 | Deleted session snapshots |
| `*.bak.*` | 3 | Old backup files |
| `*.checkpoint.*` | 1 | Checkpoint file |

**Total: 303 files**

## Files Intentionally Left Untouched

| File | Reason |
|------|--------|
| `55a1f787-ce89-4c63-bade-978cd58112fc.jsonl` | Active current session |
| `sessions.json` | Session registry — required |
| `sessions.jsonl.lock` | Lock file for active session |
| `aecbc8fa-82b9-408f-9728-d01053a8b4a0.jsonl` | Recent session (Apr 22) |
| `daf51ffb-f44c-4bb5-b5b5-a62969966ad7.jsonl` | Recent session (Apr 22) |
| Plain `*.jsonl` files (no suffix) | Ambiguous — possibly active |

## Risk Assessment

- **Archive vs delete:** Files are moved, not deleted — fully reversible
- **No active sessions affected:** All clearly old/reset/deleted files
- **sessions.json unchanged:** Session registry still references what it needs
- **Plain jsonl files untouched:** Some recent sessions with no suffix left in place
- **WESLR files untouched:** continuity/, weslr/ directories not touched

## Archive Location

`/data/data/com.termux/files/home/.openclaw/agents/main/sessions/_archived_2026-04-22/`
