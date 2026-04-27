# ADR-0003: Append-Only State Logs

**Status:** Accepted
**Date:** 2026-04-27
**Deciders:** pr0dus (operator)

---

## Context

WESLR needs to persist system state — proposals created, decisions made, plans formed, diagnostic records, handler registry modifications. The natural approach is to read and write state files, updating them as state changes.

However, mutable state files have problems:
- No audit trail — overwriting loses the history of what was decided and when
- Race conditions — concurrent writes can corrupt state
- Recovery gap — if the system crashes mid-write, state can be left inconsistent
- No reconstruction — current state can be reasoned about but past states are lost

The system is append-only by design, but the implementation details need to be explicit.

---

## Decision

**All state-changing events are written to append-only JSONL logs. Records are never modified or deleted after being written.**

Specific rules:

1. **No line modification** — once a JSONL record is written, it is never changed. No updating, no patching, no in-place edits.

2. **No line deletion** — records are not removed from JSONL files. The only way to "remove" a record is to ignore it at read time via limit or filter, but the line remains in the file.

3. **No truncation** — JSONL files grow indefinitely. Load functions use limit parameters to read only the last N lines. No automatic rotation or cleanup.

4. **Schema enforcement on write** — before any record is appended, write-side validators confirm the record meets the schema contract. Malformed records are rejected before they reach the file.

5. **Line-level error isolation on read** — load functions iterate over lines and catch `JSONDecodeError` per line, skipping malformed lines rather than crashing the entire load.

6. **Provenance is mandatory** — every record type must include a timestamp and a type field. These enable reconstruction of the event sequence from the log.

7. **Separate trace and plan files** — proposal_trace.jsonl and implementation_plans.jsonl are separate files. This enables independent truncation and prevents cross-contamination of record types.

---

## Consequences

**Positive:**
- Complete audit trail — every event is preserved in sequence
- Crash-safe writes — appending is safe even if the system crashes mid-write
- Reconstruction possible — any past state can be reconstructed by reading from the beginning
- No race conditions — append is inherently safe for concurrent writers
- Clean recovery — system restarts with full history of what happened before the crash

**Negative:**
- File size grows indefinitely — load functions must use limits to avoid reading the full history every time; no automatic cleanup
- Malformed historical data remains — if a bug writes a malformed record, it stays in the file; write-side validation prevents new malformed writes but doesn't fix old ones
- Limited queryability — JSONL is not queryable by field without loading and filtering; for large histories this is slow

**Neutral:**
- Records from previous sessions are preserved — this is a feature for institutional continuity
- The limit parameter on load functions controls how much history is read — small limits are efficient but miss older records

---

## Alternatives Considered

**Alternative 1: SQL database**
Use a SQLite or PostgreSQL database with transactions for state. Risk: introduces a database dependency that must be maintained. WESLR's current model uses file-based JSONL specifically to avoid database complexity. Also, SQL databases are mutable by default and require additional configuration to achieve append-only semantics.

**Alternative 2: Git-style event store**
Implement a proper event store with versioned snapshots. Risk: event stores are operationally complex and require infrastructure beyond what WESLR currently has. The JSONL approach is simpler and achieves the same append-only guarantees for WESLR's current scale.

**Alternative 3: Rolling window with compaction**
Keep the last N records and periodically compact the file by rewriting only recent records. Risk: compaction involves rewriting, which contradicts the append-only guarantee. If compaction runs concurrently with writes, there is a race condition. The rolling window approach is appropriate for very large files but adds unnecessary complexity at WESLR's current scale.

---

## Reversal Conditions

If at some future point WESLR grows to a scale where JSONL files become unwieldy (>10,000 records), consider:
1. Adding a periodic compaction that snapshots to a separate history file while keeping the active window small
2. This requires a separate ADR before implementation
3. The append-only rule still applies to the active window

The write-side schema enforcement and read-side error isolation from this ADR remain in force regardless of any future compaction approach.

---

*ADR-0003 — Append-Only State Logs — Accepted 2026-04-27*
