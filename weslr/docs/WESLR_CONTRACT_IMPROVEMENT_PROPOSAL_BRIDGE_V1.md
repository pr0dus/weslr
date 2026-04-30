# WESLR CONTRACT IMPROVEMENT PROPOSAL BRIDGE V1

**Version:** 1.0
**Status:** SPEC ONLY — no runtime effect
**Date:** 2026-04-30

---

## Section 1 — Purpose

Convert a stable insufficiency pattern (from the Insufficiency Detector) into a reviewable operator proposal — without making automatic changes, without LLM inference, and without modifying production behavior.

This bridge is the **last gate before human review**. It converts stable detection evidence into a form the operator can understand and act on. It does not change behavior itself.

---

## Section 2 — Input

**Source:** `weslr/contract_insufficiency_log.jsonl` — evidence records where `proposal_ready = true`

**Trigger:** A record in the insufficiency log where:
- `proposal_ready = true`
- `stable_across_checks >= 3`
- `insufficiency_confirmed = true`

---

## Section 3 — What It Produces

The bridge reads `proposal_ready` evidence and produces an **operator-facing summary** — appended to a review log.

**Output:** `weslr/contract_proposal_review_log.jsonl`

```json
{
  "record_type": "contract_proposal_review_v1",
  "proposal_id": "CP-YYYYMMDD-NNN",
  "generated_at": "2026-04-30T20:00:00Z",
  "pattern_type": "weak_entry_repetition",
  "contract": "conversational_entry",
  "response_path": "fallback_safe",
  "evidence_summary": {
    "occurrence_count": 4,
    "signal_types_seen": ["S4", null, "S4"],
    "frame_distribution": {"entry": 3, "unknown": 1},
    "stable_across_checks": 3,
    "window_size": 50
  },
  "operator_action_requested": "review_contract_outcome",
  "automatic_change": false,
  "proposal_status": "pending_review"
}
```

---

## Section 4 — What It Does NOT Do

| Forbidden | Why |
|-----------|-----|
| No automatic behavior change | All changes require operator approval |
| No LLM inference | Proposal is deterministic summary of evidence |
| No proposal auto-submission to governance | Operator reviews first |
| No write to production state | Review log is separate from production truth |
| No modification of `_CONTRACT_REPLIES` | Contract changes are operator-authorized only |

---

## Section 5 — Operator Review Flow

```
stable insufficiency detected (proposal_ready = true)
    ↓
Bridge generates proposal_summary → contract_proposal_review_log.jsonl
    ↓
Operator reviews proposal_summary manually
    ↓
Operator decides: approve / reject / defer
    ↓
If approved → operator authorizes change via governance surface
    ↓
Change applied → new contract deployed via normal release
```

**No automatic triggers.** The proposal sits in `contract_proposal_review_log.jsonl` until the operator acts on it.

---

## Section 6 — Constraints

| # | Constraint |
|---|------------|
| PB1 | Proposal is read-only from detector evidence, not LLM-generated |
| PB2 | No automatic write to governance or proposal systems |
| PB3 | No behavior modification from proposal |
| PB4 | Operator review required before any contract change |
| PB5 | Proposal log append-only, not production truth |
| PB6 | No PII in proposal records |

---

## Section 7 — Verdict

```
WESLR_CONTRACT_IMPROVEMENT_PROPOSAL_BRIDGE_V1_SPEC_DEFINED
```

Spec version 1.0 — no runtime effect. Converts stable insufficiency evidence into operator-reviewable proposals. No automatic changes.

---

*Spec version 1.0 — gates controlled user exposure*