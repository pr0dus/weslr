# PUBLIC_LEARNING_BOUNDARY_V1.md — WESLR Public Learning Boundary Canon

**Status:** CANONICAL — doctrine document
**Date:** 2026-05-03
**Supersedes:** None (new canonical document)
**Authoritative for:** All WESLR sessions, all fact extraction and storage, all responses that reference stored facts

---

## SECTION 1 — THE BOUNDARY

WESLR may accumulate structured facts from user session summaries. This canon defines what that means — and what it does not mean.

**Stored facts are NOT learning in the sense that matters:**

1. **Facts do not change system behavior.** A stored fact about "robotic arm calibration" does not change how WESLR responds, decides, routes, or acts. Facts are inert records.

2. **Facts do not train models.** WESLR does not fine-tune, distill, or transfer knowledge from fact assertions into model weights or system prompts.

3. **Facts do not create hidden beliefs.** WESLR's response logic is governed by the arbiter, not by accumulated facts.

4. **Facts may be surfaced in responses.** When a user asks "what did we discuss about the robotic arm?", WESLR may present relevant facts as "what we discussed." This is explicit recall, not hidden inference.

---

## SECTION 2 — WHAT FACT STORAGE IS

Fact storage is:

- **Structured recall** — a way to organize what the user said across sessions
- **Append-only** — new facts are added; nothing is overwritten or deleted
- **Queryable** — facts can be retrieved by subject, predicate, or object
- **Operator-visible** — all fact records are in plaintext JSONL files

---

## SECTION 3 — WHAT FACT STORAGE IS NOT

Fact storage is NOT:

- Learning that changes WESLR's decision-making without operator review
- A source of truth — facts reflect what the user summarized, not verified external reality
- An automatic action trigger — facts exist in storage; they do not cause actions
- A training signal — facts are never used to improve any model

---

## SECTION 4 — OPERATOR CLAIM

If an operator asks "did WESLR learn that?", the answer is: WESLR has structured records of what you said. It has not learned in any way that changes its behavior without your review and approval.
