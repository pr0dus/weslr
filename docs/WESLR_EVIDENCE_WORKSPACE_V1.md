# WESLR_EVIDENCE_WORKSPACE_V1.md — WESLR Evidence and Workspace Boundary Canon

**Status:** CANONICAL — doctrine document
**Date:** 2026-05-03
**Supersedes:** None (new canonical document)
**Authoritative for:** All evidence queries, fact queries, and context building in WESLR sessions

---

## SECTION 1 — TWO DISTINCT KNOWLEDGE LANES

WESLR maintains two distinct knowledge lanes:

**Lane 1 — External Evidence (evidence_chat_bridge):**
- Fetched from external sources (SearXNG web search)
- Presented as "the world says X" — unverified unless marked otherwise
- Used when user asks factual questions about the external world
- Stored in: `evidence_cache/` or similar
- Authority: "external_evidence_unverified" or similar

**Lane 2 — Extracted Facts (fact_assertions.jsonl):**
- Derived from user-authored session summaries
- Presented as "what we discussed" — not as verified external truth
- Used when user asks relational or temporal questions about past discussions
- Stored in: `.weslr/fact_assertions.jsonl` (append-only)
- Authority: "extracted_from_timeline"

---

## SECTION 2 — FACT PRESENTATION RULES

When WESLR surfaces a fact from `fact_assertions.jsonl`, it must present it accurately:

✅ Correct: "Based on our last session, we discussed that the robotic arm calibration was important."
✅ Correct: "According to the timeline, Arthur said the gripper upgrade was a priority."
❌ Incorrect: "The robotic arm calibration is important." (implies fact = truth)

The framing matters. Facts are records of what was said. They are not world-state assertions.

---

## SECTION 3 — EVIDENCE vs FACTS IN ARBITER

When the arbiter routes a query, it must distinguish:

| Query Type | Lane | Selected Layer |
|------------|------|----------------|
| "What's the weather?" | External evidence | evidence |
| "What did we discuss about robotic arm?" | Extracted facts | fact_engine |
| "What's the relationship between X and Y?" | Extracted facts | fact_engine |
| "Tell me about the external topic Z" | External evidence | evidence |

The relational query arbiter (Phase 3) implements this distinction.

---

## SECTION 4 — NO TRUTH CONFERRAL

WESLR must never present an extracted fact as conferring truth on a proposition. The `truth_status` of a fact is always "user_discussed" — not "verified", "confirmed", or "true".

When evidence and facts conflict, WESLR should note both: "We discussed X, but external evidence suggests Y. You decide what to believe."
