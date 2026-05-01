# WESLR_STATE_GROUNDED_DIALOGUE_CANON_V1

**Version:** 1.0  
**Status:** DEFINED  
**Authority:** read_only  
**Created:** 2026-05-01

---

## 1. Purpose

WESLR should answer system and architecture questions from inspectable internal state, not from scripted identity alone. This document establishes the doctrine for state-grounded dialogue — a read-only surface that lets WESLR report what it actually has, what it actually sees, and what requires operator attention, based on real internal files and analysis outputs.

---

## 2. Hard-Coded Self Answers vs. State-Grounded Dialogue

| Dimension | Hard-Coded Self Answers | State-Grounded Dialogue |
|-----------|------------------------|--------------------------|
| Source | Static identity handlers | Live internal files and analysis modules |
| freshness | Fixed at code time | Current at query time |
| coverage | Limited to coded paths | Extensible via new sources |
| authority claim | Scripted | Evidence-grounded |
| uncertainty | Often hidden | Explicitly declared when data missing |

State-grounded dialogue does not replace hard-coded identity responses. It provides a complementary, read-only path for architecture and system-state questions that require current evidence.

---

## 3. Allowed Read-Only Sources

The following sources may be consulted to answer state-grounded questions:

- `weslr/docs/WESLR_IMPLEMENTED_REALITY_INVENTORY_V1.md` — current inventory of what is implemented vs. spec-only
- `weslr/docs/WESLR_ARTIFICIAL_ANALYSIS_INDEX_V1_CHECKPOINT.md` — AAI checkpoint record
- `weslr/docs/WESLR_COMPOSITE_ANALYSIS_STACK_V1_CHECKPOINT.md` — composite analysis checkpoint record
- `weslr/docs/WESLR_COMPOSITE_ANALYSIS_STACK_CANON_V1.md` — composite analysis doctrine
- `weslr/artificial_analysis_index.py` — AAI module, via `build_attention_summary()`
- `weslr/composite_analysis_stack.py` — composite analysis module, via `build_composite_summary()`

All reads are passive. No writes, no state mutation, no side effects.

---

## 4. Forbidden Actions

State-grounded dialogue V1 is strictly **read-only**. The following are never permitted within this scope:

- State or file writes
- JSONL writes
- Proposal approval or rejection
- Contract modification
- Memory writes
- External actions (network, filesystem beyond reads)
- Autonomous repair or self-modification
- Changes to `/chat` behavior
- Ollama integration
- Modification of `_CONTRACT_REPLIES` or response contracts

---

## 5. Relationship to OCC

- **OCC may ask WESLR architecture questions** — WESLR answers from current state via the state-grounded dialogue surface
- **WESLR may answer from current state** — without routing through scripted identity handlers
- **OCC may report issues** — state-grounded dialogue exposes limitations and missing sources honestly
- **Operator remains the approval boundary** — no state-grounded answer implies autonomous authority or automatic change

---

## 6. Relationship to Future Experiments

- All experiments must be declared explicitly, not embedded silently in dialogue behavior
- Learning or adaptation triggered by state-grounded dialogue must be visible and operator-declared
- No silent self-modification — WESLR never rewrites its own state, contracts, or canon based on dialogue interactions

---

## 7. V1 Scope

- Read-only query helper implemented in `weslr/state_grounded_dialogue.py`
- Not wired into `/chat` or any messaging surface yet
- No Ollama integration
- No automatic changes based on answers
- Authority is always `read_only`

Future phases may wire this surface into conversational routing, but that requires a separate implementation spec and operator approval.

---

## 8. Verdict

**WESLR_STATE_GROUNDED_DIALOGUE_CANON_V1_DEFINED**