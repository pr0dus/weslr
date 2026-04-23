# History Structure Analysis

## Is History Compacted or Raw?

**Raw.** The session JSONL contains full, unmodified copies of:
- Every user message (complete text including bootstrap prompts)
- Every assistant response (including thinking blocks)
- Every tool call and tool result
- All usage metadata

**No summarization, no truncation, no checkpoint replacement** — all original content is preserved verbatim.

## Key Observations

### No Summary/Checkpoint Replacement
- Old turns remain fully present
- No evidence of any turn being replaced with a summary
- The session reads as a complete transcript

### Bootstrap Prompt Stored in Every User Message
The session file includes the full bootstrap prompt as the first user message — this is the largest single chunk in the session. This bootstrap prompt contains:
- AGENTS.md content
- SOUL.md content
- IDENTITY.md content
- USER.md content
- TOOLS.md content
- Partial MEMORY.md content
- HEARTBEAT.md content
- Large parts of the OpenClaw system prompt

This means the **same bootstrap context is stored in the session file** alongside the live conversation.

### Session Structure Integrity
The JSONL format stores entries in order with parent-child links. Replay of this session would reproduce the exact conversation flow.

## Replay Cost

If the session is replayed (e.g., after a reset), the model would see:
1. The full bootstrap prompt again
2. All previous conversation turns
3. All tool results
4. All thinking blocks

This is **full replay**, not summary-based. The session history grows unbounded with each exchange.
