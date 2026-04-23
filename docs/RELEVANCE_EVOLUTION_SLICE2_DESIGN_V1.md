# Relevance Evolution — Slice 2 Design v1

> Status: **DESIGN DRAFT** — doctrine for future implementation, no production code changes
> Extends: INTEREST_RELEVANCE_CANON_V1, LONG_HORIZON_RELEVANCE_DOCTRINE_V1, RELEVANCE_AUTONOMOUS_SUGGESTION_ADDENDUM_V1
> After: V2 Slice 1 (recency-only surfacing removed)

---

## SECTION 1 — WHY V2 SLICE 1 IS NOT ENOUGH

### What V2 Slice 1 solved

Slice 1 removed the recency-only floor. An interest now scores 0 if it has no non-recency signal, even if it was touched 5 minutes ago. This fixes false salience from recency.

### What still needs to be defined

Slice 1 establishes the eligibility/amplification distinction but does not define:
- What other non-recency signals may create eligibility (beyond tag overlap, name match, display_name match, tag-in-text)
- How those signals should be structured, gated, and governed
- How suggestion triggering should work through normal operator interaction channels
- How surfacing remains non-dashboard-dependent and non-invasive
- How cooldown rules prevent suggestion spam without operator dashboard interaction

The current relevance surface only has four eligibility signals. Real-world artifact content is richer than those four signals alone can capture. The doctrine needs to define which additional signals may create eligibility in future, and which signals may only amplify already-eligible interests.

---

## SECTION 2 — FUTURE ELIGIBLE SIGNAL CLASSES

### Defining "eligible signal"

An eligible signal is any condition that, when present, allows an interest to be considered for relevance scoring. Without at least one eligible signal, an interest cannot surface regardless of recency or occurrence count.

### Currently implemented (v1 + Slice 1)

| Signal | Type | Creates eligibility? |
|--------|------|----------------------|
| Tag overlap (query tags vs interest tags) | Direct match | ✅ Yes |
| Normalized name in query text | Direct match | ✅ Yes |
| Display_name in query text | Direct match | ✅ Yes |
| Interest tag in query text | Direct match | ✅ Yes |

### Candidate future eligible signals (not yet implemented)

**Signal A — Tag specificity weighting**
An interest whose tags are highly specific (multi-word, narrow scope) should score higher than one with a single generic tag, even with the same tag overlap count.

Example: "governance_oversight_calibration" (3 specific tags) vs "governance" (1 generic tag)
Both share "governance" tag, but specificity indicates precision. Specificity bonus could create eligibility for multi-tag interests where a single-tag interest would not qualify.

Implementation note: Requires tag specificity scoring function. Must be deterministic and inspectable. Not automatic — operator provides tags with desired specificity.

**Signal B — Gap/score signal presence in artifact**
An artifact with a clear gap_reason field, or a low stability_score, or a limitation field, indicates the artifact contains an explicit area of uncertainty. This signal may create eligibility for interests that relate to uncertainty, governance, or quality — even without tag overlap.

Example: An artifact with "limitation: calibration confidence gap" is highly relevant to a "calibration confidence" interest, even if the text does not contain the exact interest name.

Implementation note: This signal type requires artifact metadata inspection. Must not fetch artifact registry — only use metadata already passed to _derive_relevant_interests().

**Signal C — Occurrence cross-reference (structured signal)**
An interest that has been recorded as relevant to the same artifact-or-similar artifact before (via occurrence history) may indicate a stable relationship. This is not recency — it is structural evidence of persistent relevance.

Implementation note: Requires reading occurrence history. Must be read-only, not write. Occurrence count alone is amplification (see Section 3), but occurrence item_id match with current artifact creates eligibility.

**Signal D — Temporal pattern (not recency)**
An interest whose occurrence pattern shows regular recurrence (not just count) across a time window — e.g., 3 occurrences in 7 days — indicates active ongoing relevance, not just historical accumulation.

Implementation note: Requires occurrence timestamp analysis. Not the same as recency bonus — pattern recognition across multiple occurrences, not a single last_seen timestamp.

**Signal E — Operator amplitude annotation (future)**
An interest explicitly annotated by the operator with an amplitude value (0.0 to 1.0) may receive eligibility boost. This is operator-provided signal, not inferred.

Implementation note: Requires new optional field on interest (amplitude). Requires operator command or CLI to set. Cannot be inferred automatically.

### Signal governance requirements

Any new eligible signal must satisfy:
1. **Deterministic**: same inputs always produce same score
2. **Inspectable**: match_reasons must include which signal created eligibility
3. **Operator-visible**: output must show why an interest matched
4. **No autonomous inference without governance**: signals that require WESLR to infer operator intent must go through proposal/approval before becoming eligible
5. **No background writes**: signal computation is read-only

---

## SECTION 3 — SIGNALS THAT MAY AMPLIFY BUT NOT CREATE RELEVANCE

Amplification signals raise the score of an already-eligible interest. They cannot create eligibility on their own.

### Currently implemented

| Signal | Type | Amplifies? |
|--------|------|-----------|
| Recency < 48h (+2) | Amplification | ✅ Yes |
| Recency < 7d (+1) | Amplification | ✅ Yes |
| Occurrence count bonus (min(count/10, 2)) | Amplification | ✅ Yes (but needs guard — see below) |

### Amplification signal that needs guard: occurrence count

**Problem with current implementation:** In v1, occurrence_count bonus is min(count/10, 2). This means an interest with 20 occurrences gets +2 bonus even if it has no tag or text match. Combined with recency, this creates a path where only count + recency produce a score above 0 — which is a recency/count-only creation, now blocked by Slice 1.

After Slice 1, this specific path is already blocked (has_signal gate). But the amplification itself needs an explicit guard: **occurrence count bonus should only apply when has_signal is True** (i.e., when at least one non-recency, non-count signal exists).

**Recommended guard:** In the scoring function, occurrence count bonus should be applied only after has_signal check passes. This ensures count amplification never creates relevance — only amplifies already-eligible interests.

### Future candidate amplification signals

**Signal F — Age-based dampening (not recency)**
Very old interests (created > 1 year ago, no activity in 6 months) may receive a dampening factor unless marked as foundational. This is not recency — it's age-based decay for non-foundational interests.

**Signal G — Specificity amplification**
Multi-tag interests with 3+ tags may receive a slight amplification bonus when they are eligible. This rewards precision without creating eligibility.

---

## SECTION 4 — SUGGESTION TRIGGER MODEL

### Trigger contexts (natural interaction points)

A suggestion is surfaced when the operator is already engaged in a natural WESLR interaction. Suggestions must never be background push notifications or dashboard-only alerts.

**Trigger Context 1 — Artifact review completion**
After an artifact is processed and _derive_relevant_interests() returns results, WESLR may surface: "This relates to your [interest] interest. Should I record an occurrence?"

Condition: _relevant_interests returned non-empty, and the matching interest has not had an occurrence recorded for this artifact in the last 30 days.

**Trigger Context 2 — Interest creation surfacing**
When WESLR processes an artifact that has no matching interests but shows strong internal signals (gap_reason, low confidence, limitation), WESLR may surface: "No tracked interest matches this artifact. Would you like to create one?"

Condition: query_relevant_interests() returns [], AND artifact_meta shows gap_reason or limitation or internal_score < 0.5.

**Trigger Context 3 — Dormancy check**
When the operator asks about interest status or reviews interest list, WESLR may note: "Your [interest] hasn't surfaced in [N] days. Still active?"

Condition: Operator explicitly calls interest list/show, AND some interest has last_seen_at > 30 days ago.

**Trigger Context 4 — Similarity detection**
When the operator reviews their interests and two interests share >80% tag overlap or near-identical names, WESLR may surface: "Your [interest A] and [interest B] have similar tags. Consider merging?"

Condition: Operator calls interest list AND analysis finds duplicate-potential interests.

**Trigger Context 5 — On-demand query**
When the operator asks "what interests do I have?" or "what's relevant to X?", WESLR surfaces the relevance results as information, not as a suggestion to act.

Condition: Operator-initiated query. No suggestion framing needed — this is an information response.

### What is NOT a trigger context

- Background monitoring with no operator interaction
- Dashboard opening (unless operator is already engaged in conversation)
- Scheduled checks without operator context
- Artifact ingestion without subsequent operator interaction

---

## SECTION 5 — TEXT/VOICE SURFACING MODEL

### Surfacing principles

1. **Suggestion framing is required** for any proactive proposal: "Would you like...?", "Consider...", "Should I...?"
2. **Information framing** is required for on-demand responses: "Your interests are...", "This is relevant to..."
3. **No assertion framing** (WESLR must not state relevance as fact of authority): Never "This IS relevant to your interest" — always "This relates to..." or "This may be relevant to..."
4. **No repeated surfacing without operator response** — cooldown applies

### Suggestion sentence patterns

**Interest creation suggestion:**
```
"I've noticed calibration concerns appear in several recent artifacts. 
Would you like to create a tracked interest for this?"
```

**Occurrence recording suggestion:**
```
"This artifact relates to your 'governance quality' interest. 
Should I record an occurrence?"
```

**Merge suggestion:**
```
"Your 'governance quality A' and 'governance quality B' interests 
share similar tags. Consider reviewing them for a potential merge?"
```

**Dormancy note:**
```
"Your 'operator safety constraints' interest hasn't surfaced in 45 days. 
Still something you'd like to track?"
```

**Information response (on-demand):**
```
"Your active interests: governance_quality (3 occurrences), 
confidence_calibration (1 occurrence). Both are relevant to this artifact."
```

### Response boundary

WESLR should surface suggestions as a natural response within the ongoing interaction — not as a separate notification system, not as a standalone message, not as a dashboard alert. The suggestion should feel like a helpful observation in context, not a system interrupt.

---

## SECTION 6 — COOLDOWN / REPETITION RULES

### Cooldown definition

Cooldown prevents the same suggestion from being repeated within a time window. It is tracked per interest per trigger type, not per artifact.

### Cooldown windows by trigger type

| Trigger type | Cooldown window | Notes |
|-------------|-----------------|-------|
| Interest creation suggestion | 24 hours | Per artifact + topic combination |
| Occurrence recording suggestion | 12 hours | Per interest + per artifact |
| Merge suggestion | 4 hours | Per pair of interests |
| Dormancy note | 48 hours | Per interest |
| On-demand query | No cooldown | Operator-initiated — always allowed |

### Cooldown tracking design

Cooldown state should be stored in a lightweight ephemeral structure:
- Not persisted (resets on session restart — acceptable for suggestion cooldown)
- Not written to interests.json (maintains read-only surface of interest_tracker)
- Per-session in-memory tracking OR optional operator-controlled flag file

Example cooldown entry:
```json
{
  "interest_id": "abc123",
  "trigger_type": "occurrence_suggestion",
  "suppress_until": "2026-04-21T12:00:00Z",
  "artifact_id": "artifact-xyz"
}
```

### Cooldown enforcement rule

When a trigger condition is met, the system checks:
1. Is there an active cooldown entry for this interest + trigger_type?
2. If yes, has suppress_until passed?
3. If not passed, suppress the suggestion silently (do not surface, do not log as event)
4. If passed or no entry, proceed with surfacing

### What cooldown does NOT affect

- On-demand operator queries (interest list, show, relevance query)
- Information responses (never subject to cooldown)
- Explicit operator request for suggestions
- Suggestion acceptance/denial responses

---

## SECTION 7 — CANON BOUNDARIES TO PRESERVE

### From INTEREST_RELEVANCE_CANON_V1

| Rule | Must preserve |
|------|--------------|
| Write authority: only interest_tracker.py writes interests.json | ✅ Suggestion system must call interest_tracker functions, not write directly |
| Advisory-only: relevance never influences decisions, routing, wording | ✅ Suggestion surfacing must not change behavior of explain_artifact output |
| Forbidden drift: no silent interest creation | ✅ Suggestion system proposes creation, does not create |
| Forbidden drift: no hidden routing influence | ✅ Suggestion trigger must not gate or reroute anything |
| Integration point list: currently only sim.explain_item() | ✅ New surfacing from suggestion system is NOT a new integration point — it is a text/voice output from existing interaction context |

### From RELEVANCE_AUTONOMOUS_SUGGESTION_ADDENDUM_V1

| Rule | Must preserve |
|------|--------------|
| Tier 2 suggestion must be clearly labeled as proposal, not command | ✅ All surfacing uses suggestion framing patterns |
| No background notification systems | ✅ Suggestion only surfaces during active operator interaction |
| Suggestion cooldown prevents repetition | ✅ Per Section 6 of this document |
| No auto-recording of occurrences | ✅ Occurrence recording requires operator explicit approval |
| No state mutation without governance approval | ✅ Suggestion acceptance goes through interest_tracker API |

### From LONG_HORIZON_RELEVANCE_DOCTRINE_V1

| Rule | Must preserve |
|------|--------------|
| Recency cannot create relevance by itself | ✅ Already enforced in Slice 1 |
| Count cannot create relevance by itself | ✅ Amplification guard needed (Section 3 of this document) |
| Broad interests must not dominate specific interests | ✅ Tag specificity signal (Signal A) rewards precision |
| Time significance must distinguish active/dormant/foundational/historical | ✅ Dormancy suggestion uses last_seen_at, not auto-state |

---

## SECTION 8 — SAFEST FIRST IMPLEMENTATION AFTER THIS DESIGN

### Recommended first slice: Cooldown tracking system + Occurrence recording suggestion trigger

**Why this is safest:**
1. Uses existing query_relevant_interests() output — no new eligible signal implementation
2. Cooldown tracking is read-only in-memory — no state writes, no interests.json modification
3. Occurrence recording suggestion uses existing interest_tracker.add_occurrence() — correct write authority path
4. Trigger is embedded in existing interaction context (artifact review) — not a new integration point
5. Suggests, does not auto-act — operator retains full control

**What to implement:**
1. `weslr/interest_suggestion_cooldown.py` — ephemeral cooldown tracker with time-window suppression
2. `interest_suggest(artifact_meta, relevance_results)` — function that checks cooldown and returns formatted suggestion text or None
3. Call site: in the interaction context after _derive_relevant_interests() returns non-empty AND operator is engaged (not background)

**What NOT to implement in this slice:**
- No new eligible signal implementation (keep Slice 1 behavior)
- No interest creation suggestion trigger (defer to second slice)
- No tag specificity scoring (defer to third slice)
- No temporal state inference (defer to future canon update)
- No persistence layer for cooldown (session-only is fine)

**Implementation location:**
The surfacing should NOT be in sim.explain_item() — that function already returns structured metadata. Surfacing should occur in the operator interaction layer (text/voice response formatter) after explain_item() results are processed.

---

## SECTION 9 — STOP LINE

**Verified completed:**

- ✅ Design/spec only — no production code changes
- ✅ No implementation started
- ✅ No routing changes
- ✅ No schema changes
- ✅ No new integration points defined
- ✅ docs/RELEVANCE_EVOLUTION_SLICE2_DESIGN_V1.md created and complete
- ✅ Future eligible signal classes defined (5 candidates with governance requirements)
- ✅ Amplification signal guard defined (occurrence count requires has_signal)
- ✅ Suggestion trigger model defined (5 natural interaction contexts)
- ✅ Text/voice surfacing patterns defined with framing rules
- ✅ Cooldown rules defined (per interest, per trigger type, per time window)
- ✅ Canon boundaries preserved (write authority, advisory-only, no auto-creation, no background notification)
- ✅ Safest first implementation identified (cooldown tracker + occurrence suggestion trigger)
- ✅ Subsequent slices identified for future (interest creation trigger, tag specificity signal, age dampening)

**No code implemented in this step.**

---

*This design was produced following V2 Slice 1 implementation and the inspection of existing WESLR suggestion/proposal infrastructure. It defines the evolution path for relevance eligible signals, suggestion triggering, and surfacing while preserving all existing canon boundaries.*