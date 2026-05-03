# WESLR_DETERMINISTIC_ANCHOR_AND_PROBABILISTIC_INTERPRETATION_CANON_V1.md

**Status:** CANONICAL — doctrine document
**Date:** 2026-05-03
**Supersedes:** None (new canonical document)
**Authoritative for:** All fact extraction, entity matching, and query resolution in WESLR

---

## SECTION 1 — DETERMINISTIC ANCHOR

All core WESLR operations — timeline appends, fact extraction, arbiter routing — are anchored in deterministic rules. No probabilistic model is required for these operations.

**Deterministic operations (Layer 1):**
- Timeline event append: deterministic record creation
- Fact extraction from session summaries: pattern-based rules (Phase 1)
- Arbiter routing: rule-based turn classification
- Project registry: explicit user commands only

**Probabilistic operations (Layer 2 — low-risk, automated):**
- Optional semantic similarity for entity ID matching (e.g., fuzzy entity suggestion)
- Answer quality scoring
- These are assistants to the deterministic core and do not require operator review.

---

## SECTION 2 — FACT EXTRACTION SPECIFICATION

Fact extraction is **deterministic** — it uses a fixed set of pattern-matching rules to convert session summary text into structured triples (subject, predicate, object).

**Rules for Phase 1 (10 patterns):**

1. `"X discussed Y"` → (user, discussed, Y)
2. `"X said Y about Z"` → (X, said_about, Z) where Y is descriptor
3. `"X worked on Y"` → (user, worked_on, Y)
4. `"X is important for Y"` → (Y, has_importance, X)
5. `"X depends on Y"` → (X, depends_on, Y)
6. `"X is part of Y"` → (X, part_of, Y)
7. `"X uses Y"` → (X, uses, Y)
8. `"X created Y"` → (X, created, Y)
9. `"X tested Y"` → (X, tested, Y)
10. `"X upgraded Y"` → (X, upgraded, Y)

Each pattern produces a triple with:
- `subject`: normalized entity string
- `predicate`: normalized relation string
- `object`: normalized entity string
- `record_type`: "fact_assertion_v1"
- `authority`: "extracted_from_timeline"
- `automatic_action`: false
- `hidden_learning`: false
- `raw_prompt_stored`: false

**Extraction is not inference.** The extractor identifies explicit relationships in summary text. It does not hypothesize or infer beyond what was written.

---

## SECTION 3 — SEMANTIC SIMILARITY (FUTURE)

Semantic similarity for entity matching (e.g., suggesting "robotic_arm" when user types "robotic arm") is a **low-risk probabilistic assistant (Layer 2)** and may be automated without operator review, provided:
- It does not change fact storage or routing decisions
- It is used only as a suggestion/ranking aid
- It does not trigger writes or state changes

This canon will be updated when semantic similarity is formally introduced.
