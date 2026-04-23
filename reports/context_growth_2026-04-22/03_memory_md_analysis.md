# MEMORY.md Analysis

## Size

- **File size:** 17,330 bytes (~17KB)
- **Bootstrap injection:** Truncated 30% in current bootstrap — original is larger
- **Effective context contribution:** ~12KB after truncation

## Static vs. Growing

- **Static** — MEMORY.md does not auto-grow
- It is a manually curated file updated by the agent or user
- Only grows when someone explicitly edits it
- Injected once at bootstrap, not repeatedly

## Load Pattern

- Loaded **once** at session startup (bootstrap)
- Not re-loaded during the session
- Not re-injected on heartbeats

## Context Efficiency Assessment

| Dimension | Rating | Notes |
|-----------|--------|-------|
| Information density | High | User-curated long-term memory |
| Context efficiency | Moderate | 17KB is large but valuable |
| Growth contribution | Low | Static file |
| Bootstrap burden | High | Large single injection at startup |

## Comparison to Session Context

- MEMORY.md at 17KB is smaller than the current active session JSONL (~267KB and growing)
- Session chat history already exceeds MEMORY.md in a moderately long session
- MEMORY.md burden is **fixed and known** — session history grows unbounded

## Verdict

- **Keep as-is** — high value, low growth
- Not the main problem — session history is
- A lighter alternative (e.g., a summary instead of full MEMORY.md) could be considered in a future pass, but only if the operator chooses to restructure
