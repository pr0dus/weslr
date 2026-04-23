# Long-Horizon Relevance Doctrine — v1

> Status: **DESIGN DRAFT** — doctrine and design direction, not implementation
> This document defines why Relevance v1 is insufficient for lifetime continuity and establishes the design direction for Relevance v2.

---

## SECTION 1 — WHY RELEVANCE V1 IS NOT ENOUGH

### What v1 does correctly

Relevance v1 is bounded, explainable, and safe within a bounded context window. Its scoring is structural (tag overlap, name match, text proximity, recency, occurrence count) and fully inspectable. It does not modify behavior, does not influence decisions, and remains advisory-only. This makes it a valid foundation for a limited-scope relevance system.

### Why v1 breaks down over long horizons

**Recency creates false salience.** In v1, any interest created within 48 hours scores at least 2 (recency floor) even with zero actual relevance. Over days or weeks, this means newly created interests always dominate results even if they represent no real significance. Over years, every interest ever created becomes "recent" relative to the lifetime of the system — the recency signal becomes noise.

**Count creates popularity gravity.** An interest with 20 occurrences scores higher than one with 5 occurrences, purely as a function of how many times it was manually recorded. Over a long lifetime, interests that were easiest to record (most frequently touched) would systematically dominate over interests that are most significant but infrequently touched. The scoring rewards frequency, not importance.

**Lexical matching is too literal.** v1 matches on exact normalized names, display name text, and tag overlap. A "governance quality" interest will not match an artifact that talks about "institutional oversight" and "outcome assurance" even if those concepts are deeply related. Over a lifetime, the vocabulary used to describe the same fundamental concern will evolve — a literal matching system will miss meaning that has persisted through language drift.

**Binary recency is too coarse.** v1 applies +2 if last_seen within 48h, +1 if within 7 days, 0 otherwise. This creates sharp cliffs: a 49-hour-old interest scores 2, a 49-hour-old minus one second scores 0. Over years, the distinction between "this was relevant yesterday" and "this was relevant 3 years ago" is lost entirely.

**Dormant interests are invisible.** An interest that was significant for decades, then not touched for years, scores the same as one that was never established. Over a lifetime, foundational knowledge (what the operator cares about fundamentally) and historical knowledge (what was important in past eras) are systematically hidden from relevance results in favor of whatever was touched most recently.

**Broad interests dominate specific ones.** An interest with tag "governance" (extremely broad) will match every artifact that mentions governance in any context. Over a lifetime, broad-tagged interests would suppress narrow but precise interests, rewarding generality over specificity even when specificity is more accurate.

### The core problem

v1 scoring rewards **how recently something was touched** and **how many times it was touched** — not **how deeply significant it is** or **how persistently it represents a real concern**. Over a short horizon (days to weeks), recency and frequency are reasonable proxies for relevance. Over a human lifetime, they become noise.

---

## SECTION 2 — LONG-HORIZON MEMORY REQUIREMENTS

### What relevance must do over years

**Distinguish active from dormant.** An interest that is currently being used or referenced should score differently from one that was established but not touched in years. This is not recency — it is a signal about current relevance versus historical record.

**Distinguish foundational from popular.** An interest that represents a core operator concern (governance values, quality standards, safety constraints) should not be drowned by interests that were simply touched more frequently. Foundational interests may have low occurrence counts but high significance.

**Allow semantic drift.** Over a lifetime, the vocabulary used to describe the same concern will change. "Governance quality" in 2026 might be "institutional oversight" in 2031 and "structural accountability" in 2038. All three refer to the same core concern. Relevance must allow concept continuity even when surface vocabulary changes.

**Protect forgotten knowledge.** An interest that was active in 2027, then not mentioned for 15 years, may still represent a real concern that should resurface when context warrants. The system must not only surface currently-active relevance but also protect knowledge that is dormant but still significant.

**Suppress false salience.** A newly created interest with 20 occurrences in 48 hours should not outrank a foundational interest that has been valid for 10 years. The scoring must penalize newly-hot over persistently-significant.

**Distinguish specificity from generality.** A highly specific interest (e.g., "confidence calibration in measurement artifacts") should score distinctly from a broad interest (e.g., "quality"). Specificity should be rewarded, not penalized.

**Time-scale aware.** Different relevance questions operate at different time scales:
- Immediate: what is relevant right now?
- Recent: what has been significant in the last months?
- Historical: what was significant in past eras?
- Foundational: what has been persistently significant across all time?

---

## SECTION 3 — CORE RELEVANCE LAWS

### Law 1: Recency Cannot Create Relevance By Itself

**Statement:** A signal that something was recently touched or recently created does not constitute evidence that it is relevant. Recency is a condition for relevance consideration, not a component of relevance itself.

**Implication for scoring:** Recency may act as a gate (allow consideration) or as a dampener (suppress very old), but it must not add a positive bonus that inflates scores for recently-touched interests over significantly older ones.

**Contrast with v1:** v1 applies +2 for <48h, +1 for <7d — positive bonuses that increase scores for recency. In v2, recency should reduce suppression for active interests, not add to their scores.

### Law 2: Count/History Cannot Create Relevance By Itself

**Statement:** The number of times an interest was touched or the number of occurrences recorded does not constitute evidence that it is significant. Count reflects activity, not importance.

**Implication for scoring:** Occurrence count may act as a secondary signal (very low count may indicate an untested or newly-established interest), but it must not add a positive bonus that rewards popularity.

**Contrast with v1:** v1 applies min(occurrence_count/10, 2) as a positive bonus. In v2, this should be removed or restructured as a damping factor for very low counts.

### Law 3: Broad Interests Must Not Dominate Specific Interests

**Statement:** An interest with a highly generic tag (e.g., "governance") must not suppress an interest with a more specific tag (e.g., "governance_oversight_quality") when both are genuinely relevant to an artifact.

**Implication for scoring:** Tag specificity should be a factor in scoring — more specific tags earn higher specificity credit. Overlapping tag matches should be weighted by specificity, not just counted.

**Design note:** This requires a tag hierarchy or specificity scoring, not just flat tag lists.

### Law 4: Semantic Broadening Must Remain Governed

**Statement:** Allowing an interest to match conceptually related but lexically different terms is valuable for long-horizon continuity, but it must be operator-controlled and inspectable.

**Implication for scoring:** Semantic matching (where a "governance quality" interest matches an artifact about "institutional accountability") is desirable but must be:
- Explicitly approved per-interest (not automatic)
- Traceable: match reasons must show which semantic bridge was used
- Bounded: semantic broadening must not cause false positives at scale

**Design note:** Semantic matching requires a concept mapping layer, not literal text matching. This is a future extension.

### Law 5: Time Significance Must Distinguish Active vs Dormant vs Foundational vs Historical

**Statement:** Every interest exists in one of four temporal states:
- **Active:** currently being referenced or touched
- **Dormant:** was significant but not touched recently (may resurface)
- **Foundational:** represents a core concern that persists regardless of touch frequency
- **Historical:** was relevant in a past era but is not currently active or foundational

**Implication for scoring:** The temporal state of an interest must affect its scoring profile:
- Active: full scoring weight
- Dormant: reduced but nonzero weight (should not be zero — dormant may resurface)
- Foundational: elevated base weight regardless of recency or count
- Historical: minimal weight unless explicitly queried at historical time scale

**Design note:** Temporal state is not determined by last_seen_at alone — it requires a state field and potentially operator annotation.

---

## SECTION 4 — FAILURE MODES TO PREVENT

### False salience

**What it is:** A newly created or recently touched interest scores higher than a more significant older interest purely due to recency or count bonuses.

**How it manifests:** When onboarding a new artifact, recently created interests (which may be exploratory or tentative) outrank foundational interests that represent the operator's core values.

**How to prevent:** Remove positive recency and count bonuses. Treat recency as a suppression dampener, not a score inflator. Foundational interests must have an explicit boost mechanism that is not based on recency.

### Popularity gravity

**What it is:** Interests that were easiest to record (most frequently touched in daily operations) systematically dominate over interests that are deeply significant but infrequently touched.

**How it manifests:** "Governance quality" (touched 50 times in daily operations) suppresses "operator_safety_constraint" (touched only 5 times but represents a hard safety requirement).

**How to prevent:** Count must not add positive score. Foundational interests need an explicit weight mechanism. Specific interests should score above general interests when both are genuinely relevant.

### Memory pollution

**What it is:** Over a lifetime, the relevance result becomes cluttered with low-signal interests that were created or touched recently, obscuring the signal from high-value interests.

**How it manifests:** The top 3 relevance results for a deeply important artifact include recently-touched but tangential interests, pushing foundational interests to positions 4-7.

**How to prevent:** Strong dampening for non-foundational, non-active interests when they compete with foundational ones. Explicit operator designation of foundational interests.

### Resurfacing noise

**What it is:** Dormant but potentially significant interests resurface with artificially inflated scores due to recency bonuses applied when they are re-touched.

**How it manifests:** A 5-year-dormant interest is re-touched once, immediately gets +2 recency bonus, and re-enters the top results despite having been dormant.

**How to prevent:** Recency bonus should apply only to interests that were recently active AND have a meaningful baseline score. Single re-touch should not immediately elevate a dormant interest.

### Forgotten but foundational knowledge

**What it is:** Interests that represent genuinely important operator values but have not been touched for years become invisible in relevance results.

**How it manifests:** An operator who has a deep commitment to "transparent_handoff_outcomes" but has not referenced it in 3 years gets no relevance signal when reviewing an artifact about handoff quality.

**How to prevent:** Temporal state must distinguish dormant from inactive. Foundational interests must retain elevated base weight regardless of last_seen_at. An explicit "foundational" status (operator-designated) must override dormancy.

### Broad-tag domination

**What it is:** An interest tagged with a very generic term ("governance", "quality", "system") outscores a more specific interest in every match because the generic tag is always present.

**How it manifests:** "Governance" interest always scores higher than "governance_oversight_in_calibration_workflows" for any artifact that mentions governance, regardless of whether the specific interest is more accurate.

**How to prevent:** Tag specificity scoring must penalize generic tags. An interest with 3 highly specific tags should score above one with 1 very generic tag for the same artifact.

---

## SECTION 5 — RELEVANCE V2 DESIGN DIRECTIONS

### Candidate signal classes

**Semantic signals (future):**
- Concept-level matching (not lexical)
- Interest concept graph (relates interests by shared concerns)
- Operator-provided synonym mappings

**Temporal signals:**
- last_seen_at → suppression dampener (not score bonus)
- created_at → age signal (very old may indicate foundational or historical)
- temporal_state field (active/dormant/foundational/historical) → state-based weight
- recurrence pattern (how regularly is this interest touched?)

**Structural signals:**
- tag specificity (more specific tags earn higher specificity credit)
- occurrence_count dampener (low count may indicate untested; high count does not reward popularity)
- name specificity (normalized name length as a specificity proxy)

**Amplitude signals:**
- interest_amplitude (how strongly does this interest represent a real concern? — operator-provided, not derived)
- relevance_origin (who created this interest: operator vs weslr proposal vs system inference)

### Required gating logic

**Minimum signal threshold:** An interest must have at least one non-recency, non-count signal to appear in results. A score built entirely from recency bonus (with no tag/text match) should be rejected before returning results.

**Maximum recency weight:** Recency bonus must be capped as a percentage of total score, not as an absolute additive. For example: recency contribution may not exceed 20% of total score.

**Specificity floor:** An interest with only very generic tags (single-word, highly common) must not appear above an interest with more specific tags when both have valid matches.

**Foundational override:** An interest explicitly marked as "foundational" by the operator retains minimum base weight regardless of dormancy.

### Possible multi-timescale design

**Timescale layers (query-time parameter):**

| Layer | Time horizon | Scoring profile |
|-------|-------------|-----------------|
| immediate | now → 30 days | Strong recency weight, active only |
| recent | 30 days → 1 year | Moderate recency weight, active + recent dormant |
| persistent | 1 year → lifetime | Low recency weight, foundational + persistent dormant |
| historical | any past era | Low amplitude, historical-state interests only |

**Query interface:**
```
query_relevant_interests(text, tags, top_n=3, timescale="recent")
```

Default timescale: "recent" (current behavior, backward compatible).

### Relevance eligibility vs relevance amplification

**Eligibility:** An interest must pass minimum thresholds (at least one non-recency signal, temporal state not "historical" without explicit query) to be considered at all.

**Amplification:** An interest that passes eligibility may be amplified based on:
- temporal state (foundational +0.5, active +0.2)
- specificity (highly specific tags +0.3)
- operator amplitude (if provided, +0 to +1.0)

**Separation rationale:** Eligibility determines whether an interest is considered. Amplification determines how strongly it scores. This separation prevents recency from creating eligibility in v2.

---

## SECTION 6 — SAFE MIGRATION FROM V1

### What remains canonical from v1

- **Interest schema (interests.json):** The core data model remains valid. New fields (temporal_state, amplitude, is_foundational) may be added as optional extensions.
- **Write authority:** Only interest_tracker.py may write to interests.json — this does not change.
- **Advisory-only contract:** Relevance output must never influence decisions, routing, wording, or confidence — this does not change.
- **No automatic writes:** No autonomous interest creation or occurrence creation — this does not change.
- **Canonicalization document:** docs/INTEREST_RELEVANCE_CANON_V1.md remains authoritative for write rules, integration rules, and forbidden drift. V2 must comply with v1 until v1 is explicitly superseded.

### What can change in v2

- **Scoring function:** _score_interest() may be restructured to remove positive recency/count bonuses
- **Relevance eligibility threshold:** query_relevant_interests() may require minimum signal threshold
- **Return shape:** match_reasons structure may be extended to include specificity and amplitude signals
- **Query parameters:** query_relevant_interests() may accept new parameters (timescale, amplitude_filter) with backward-compatible defaults

### What must remain advisory-only unless later approved

- **Temporal state assignment:** Automatic inference of temporal_state (active/dormant/foundational/historical) requires operator approval before implementation.
- **Semantic matching:** Concept-level matching (not lexical) requires explicit approval as it may create unexpected matches.
- **Amplitude scoring:** Operator-provided amplitude values require a write mechanism and governance approval.
- **New integration points:** Any additional integration points beyond sim.explain_item() require canonicalization doc update.

---

## SECTION 7 — RECOMMENDED FIRST CODE CHANGE LATER

### The single safest highest-value v2 implementation slice

**Change:** Remove the positive recency bonus and replace it with a non-recency signal requirement.

**What this means:**
1. In `relevance_surface._score_interest()`, after computing the score from tag/text/specificity signals, check: if the score consists entirely of recency bonus (i.e., no tag match, no name match, no display_name match, no tag-in-text match), then return score=0 for this interest.
2. The recency bonus itself may be reduced to a dampening factor (e.g., +0 instead of +2), or retained as a neutral signal without positive score impact.

**Why this is the safest slice:**
- It affects only the scoring function in relevance_surface.py
- It changes the behavior of edge cases (empty-match, governance-safety scenarios) but not the behavior of valid matches
- It is backward-compatible: interests with real tag/text matches still score correctly
- It directly addresses the primary bottleneck identified by the cognitive evaluation suite (recency floor of 2 for non-matching interests)
- It does not require new schema, new fields, or new integration points
- It preserves the advisory-only contract — no behavior change to callers

**What it does not include (deliberately omitted from this slice):**
- No temporal_state field (kept for future)
- No tag specificity scoring (kept for future)
- No amplitude signals (kept for future)
- No multi-timescale query parameter (kept for future)
- No changes to integration points

**Approximate location:** `weslr/relevance_surface.py`, `_score_interest()` function — the `return score, reasons` at the end of the scoring function.

---

## SECTION 8 — STOP LINE

**Verified completed:**

- ✅ Doctrine/design document only — no code changes
- ✅ No production scoring changes
- ✅ No routing changes
- ✅ No new integrations
- ✅ No hidden behavior changes
- ✅ docs/LONG_HORIZON_RELEVANCE_DOCTRINE_V1.md created
- ✅ Five core relevance laws defined
- ✅ Six failure modes identified
- ✅ V2 design directions specified with signal classes, gating logic, multi-timescale concept
- ✅ Safe migration path from v1 documented
- ✅ Recommended first implementation slice identified (recency signal requirement) without implementation

**Next authorized step:** Implement the recommended first v2 slice (recency signal requirement) when approved, or proceed to any allowed future extension from docs/INTEREST_RELEVANCE_CANON_V1.md Section 9.

---

*This doctrine was produced following the Interest Tracker / Relevance chapter completion (2026-04-20) and the cognitive evaluation suite run. It defines the design direction for long-horizon relevance without prescribing implementation.*