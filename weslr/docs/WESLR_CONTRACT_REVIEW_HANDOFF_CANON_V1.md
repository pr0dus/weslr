# WESLR Contract Review Handoff Canon V1

**Date:** 2026-05-01
**Canon:** WESLR_CONTRACT_REVIEW_HANDOFF_CANON_V1_DEFINED
**Status:** OPERATOR-ACCEPTED CONSTRAINT

---

## Purpose

This document defines the canonical meaning of signals produced by the contract insufficiency detection and proposal bridge system. It exists to prevent drift: without explicit canon, a future self or operator might reinterpret `proposal_ready=true` or `pending_review` in a way that bypasses human review.

---

## Canonical Meanings

### `proposal_ready = true`

**Means:** The detector's evidence is stable enough — by its own criteria — to present to an operator for review.

**Does NOT mean:**
- Approval to change a contract
- Permission to modify response text
- Implementation authorization
- Production system change
- Operator agreement with the diagnosis

**The signal is a prompt, not a command.**

---

### `contract_proposal_review_log.jsonl`

**Means:** An append-only queue of evidence summaries awaiting operator review.

**Does NOT mean:**
- Production truth
- Approved behavior
- Implementation plan
- `proposal_trace.jsonl` (which is reserved for operator-approved decisions)
- `implementation_plans.json` (which is reserved for fully-specified implementation steps)
- Any change to live system behavior

**It is an inbox, not a verdict.**

---

## Hard Rules (Non-Negotiable)

These rules are enforced by the bridge module and must never be bypassed:

| Rule | Enforcement |
|------|-------------|
| Bridge must never change response contracts | Module has no write path to contracts |
| Bridge must never write to `proposal_trace.jsonl` | Explicitly excluded from bridge's write targets |
| Bridge must never write to `implementation_plans.json` | Explicitly excluded from bridge's write targets |
| Bridge must never auto-approve proposals | `automatic_change=false` on all records, enforced in module |
| Bridge may only summarize evidence | Bridge reads log, writes summary; no contract data modified |
| Operator review is required before any contract change | `proposal_status=pending_review` requires explicit operator action |

---

## Evidence Filtering Rules

The bridge applies these filters before creating a proposal record:

1. **proposal_ready must be true** — evidence must have passed detector stability threshold
2. **stable_across_checks >= 3** — minimum stability required
3. **No PII in evidence strings** — emails, URLs, IPs, phone numbers rejected
4. **No forbidden fields** — `raw_prompt`, `prompt`, `message`, `user_input`, `email`, `phone`, `ip`, `address` rejected
5. **Deduplication** — same `pattern_type + contract + response_path + stable_across_checks` produces one record

---

## What the Proposal Record Is

A `contract_proposal_review_v1` record contains:

```json
{
  "record_type": "contract_proposal_review_v1",
  "proposal_id": "CP-YYYYMMDD-NNN",
  "generated_at": "<ISO timestamp>",
  "pattern_type": "weak_entry_repetition",
  "contract": "conversational_entry",
  "response_path": "fallback_safe",
  "evidence_summary": {
    "occurrence_count": 5,
    "signal_types_seen": [null, null, null, null, null],
    "frame_distribution": {"entry": 5},
    "stable_across_checks": 3,
    "window_size": 50
  },
  "operator_action_requested": "review_contract_outcome",
  "automatic_change": false,
  "proposal_status": "pending_review"
}
```

It is a **structured summary** — not the raw observation data. Raw prompts are never in the log.

---

## What the Proposal Record Is NOT

- Not an implementation plan
- Not a contract modification
- Not a verdict
- Not an instruction to the system
- Not a change to any `_CONTRACT_REPLIES` entry

---

## Operator Decision Required

The only authorized path from `pending_review` to a contract change is:

1. **Operator reads** `contract_proposal_review_log.jsonl`
2. **Operator reviews** evidence summary
3. **Operator makes decision** (approve / reject / defer)
4. **Decision recorded** in a separate decision log (not yet implemented)
5. **If approved** — implementation plan written to `implementation_plans.json` (not yet implemented)
6. **If approved** — contract response changed via explicit operator action (not yet implemented)

No step may be skipped. No step may be combined. No step may be performed by the detector or bridge.

---

## Verdict

```
WESLR_CONTRACT_REVIEW_HANDOFF_CANON_V1_DEFINED
```
