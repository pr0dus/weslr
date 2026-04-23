# Session JSONL Growth Analysis

## Growth Pattern

**Approximately linear** — each exchange adds one user message object + one or more assistant message objects + tool result objects. No automatic deduplication observed.

## Entry Size Contributors (largest to smallest)

### 1. User Prompts — LARGEST
User messages are the dominant storage cost. Each user turn includes:
- Full bootstrap prompt text (~12,000 chars for the initial startup prompt)
- The full OCC prompt text (~3,000 chars per request)
- All user-submitted content

### 2. Assistant Thinking Blocks
Each assistant message contains a `thinking` block with the model's internal reasoning. For example:
- Line 7: thinking block with session startup analysis (~300-500 chars)
- Multiple thinking blocks per long assistant response

### 3. Tool Calls
Each assistant response that calls tools stores:
- Tool name
- Full tool arguments (JSON)
- Tool call ID

### 4. Tool Results
Each tool result stores:
- Full output of the tool (which can be very large — e.g., `exec` outputs containing directory listings, file contents, etc.)
- Some tool results in this session were very large (directory listings, file reads)

### 5. Usage Metadata
Each assistant message stores `usage` with:
- `input` tokens
- `output` tokens
- `cacheRead` / `cacheWrite`
- `totalTokens`

### 6. Administrative Entries
Session markers: `model_change`, `thinking_level_change`, `model-snapshot` — these are small but add up over time.

## Storage Efficiency

| Entry Type | Storage Efficiency | Notes |
|------------|-------------------|-------|
| User messages | **Low** | Full prompt text repeated in every request |
| Assistant thinking | **Low** | Internal reasoning stored permanently |
| Tool results | **Low** | Full output stored, even for read-only tools |
| Tool arguments | **Medium** | Necessary for replay, but can be verbose |
| Usage metadata | **Medium** | Useful for analytics, adds overhead |
| Administrative entries | **High** | Small, necessary |

## Does Session Size Map to Prompt Pressure?

**Yes, approximately.** The session file is essentially a transcript of everything that happened. Each message pair (user + assistant) adds roughly 2-8KB to the file. With 125 entries in ~17 minutes, that's ~7 exchanges. At this rate, after 1 hour of active use, the session could be 2-4MB.

The session file size directly corresponds to how much context the model sees on each request — it is the primary input for session replay.
