# Relevance — Autonomous Suggestion Addendum v1

> Status: **DOCTRINE ADDENDUM** — extends INTEREST_RELEVANCE_CANON_V1 and LONG_HORIZON_RELEVANCE_DOCTRINE_V1
> This document defines what WESLR may autonomously observe and proactively suggest about relevance, and what it may not silently do without operator approval.

---

## SECTION 1 — WHY DASHBOARD-ONLY GOVERNANCE IS INSUFFICIENT

### The problem with "operator reviews at console" as the only relevance governance

The current Interest Tracker / Relevance chapter assumes the operator governs relevance through:
- Manual interest creation via CLI
- Manual occurrence tracking via CLI
- Explicit review of `_relevant_interests` metadata when reviewing an artifact

This works for deliberate, console-based workflows. It fails in three realistic WESLR operating contexts:

**Continuous background operation:** WESLR processes artifacts, reviews, and conversations in the background without active operator monitoring. An interest that becomes significant (through repeated relevance to incoming artifacts) will not be noticed unless the operator happens to check the dashboard. Silent buildup of relevance significance — even when correct — goes unobserved.

**Natural language interaction:** When WESLR responds to the operator through text or voice, the operator may ask about or reference relevance topics ("should I be tracking this concern?", "have we had interests related to calibration before?"). WESLR cannot answer these questions purely from operator dashboard interactions — it needs to observe and reason about relevance state and surface observations naturally.

**Pre-decision awareness:** WESLR may detect that a tracked interest is becoming more or less relevant before the operator reviews the next artifact. Waiting for dashboard interaction creates a lag between relevance observation and governance action that could be bridged by proactive suggestion.

### The core principle

WESLR may autonomously observe relevance state and proactively suggest relevance-related observations through normal communication channels. WESLR must not autonomously convert those observations into consequential authority — routing control, state mutation, or decision influence — without operator approval.

The gap between "observes and suggests" and "acts with authority" is the governed approval boundary.

---

## SECTION 2 — AUTONOMOUS OBSERVATION VS GOVERNED CONSEQUENCE

### Three tiers of relevance behavior

**Tier 1 — Autonomous observation (no approval required)**
WESLR may observe relevance state and compute relevance signals without operator input. This is passive monitoring — it generates information but does not act on it or surface it unprompted.

Examples:
- Checking whether an interest has been matched by a new artifact
- Computing whether an interest's occurrence count has crossed a threshold
- Observing that a previously matched interest has stopped matching new artifacts

**Tier 2 — Proactive suggestion (approval recommended but not required for suggestion itself)**
WESLR may surface relevance observations as suggestions through normal communication channels (text response, voice output) when doing so serves the operator naturally. The operator receives the information and chooses whether to act.

Crucially: suggesting is not acting. A suggestion proposes; it does not execute.

Examples:
- "I notice calibration concerns have come up 3 times this week — worth creating an interest?"
- "This artifact relates strongly to your tracked interest in governance oversight."
- "You've created several interests around similar topics — should they be merged?"

**Tier 3 — Consequential action (operator approval required)**
Any behavior that modifies state, changes routing, influences decisions, or exercises authority requires explicit operator approval through the governance surface.

Examples:
- Creating a new interest automatically (forbidden — requires operator command)
- Recording an occurrence without operator input (forbidden — requires explicit trigger)
- Adjusting routing based on relevance signal (forbidden — relevance is advisory only by canon)

### The boundary

```
Observation → [operator reviews suggestion] → [approval or rejection] → Consequential action
```

WESLR may move freely along this chain as long as it does not skip from Observation to Consequential Action without the operator's explicit governance step.

---

## SECTION 3 — ALLOWED AUTONOMOUS RELEVANCE BEHAVIORS

The following behaviors are permitted as autonomous observation, subject to Tier 2 suggestion rules:

| Behavior | Tier | Notes |
|---------|------|-------|
| Observe interest match frequency over time | 1 | Passive monitoring only |
| Observe that an interest has not matched in N days | 1 | Passive monitoring only |
| Observe that a new artifact has potential relevance to tracked interests | 1 | Passive — does not surface until Tier 2 |
| Compute relevance scores against newly processed artifacts | 1 | Passive — results held for potential suggestion |
| Observe that two interests have overlapping tags or similar names | 1 | Passive — flag for potential suggestion |
| Observe that an interest's name or tags are similar to an artifact's content | 1 | Passive |
| Track recurrence patterns (how often an interest matches) | 1 | Passive |

These behaviors do not require approval to implement. They do require that their outputs are held at Tier 1 until the operator naturally triggers a Tier 2 suggestion context.

---

## SECTION 4 — ALLOWED PROACTIVE SUGGESTION BEHAVIORS

The following suggestions may be surfaced proactively when the operator is in a natural communication context with WESLR (not requiring explicit dashboard interaction):

| Suggestion | Trigger condition | Form |
|-----------|------------------|------|
| "Create interest X?" | Strong repeated match to no existing interest | Text/voice suggestion to create |
| "Track occurrence on interest X?" | Strong match with no recent occurrence recorded | Text/voice suggestion to record |
| "Merge interests X and Y?" | Two interests with >80% tag overlap or nearly identical names | Text/voice suggestion to merge |
| "Your tracked interest X is relevant here" | Artifact scores high on existing interest | Text/voice surfacing of _relevant_interests |
| "Interest X has not matched in 30 days" | Dormancy observation | Text/voice note on interest status |
| "Tag overlap: interest X and Y share tags" | Structural similarity observed | Text/voice suggestion to review |

**Suggestion rules:**
- Suggestions must be clearly labeled as suggestions, not commands or decisions
- Suggestions must not include any automatic state mutation
- Suggestions must be reversible and non-consequential if the operator ignores them
- Suggestions must not be repeated on the same topic within a short window (cooldown)

---

## SECTION 5 — FORBIDDEN SILENT CONSEQUENCES

The following are explicitly forbidden as autonomous or silent actions without operator approval:

| Forbidden | Reason |
|-----------|--------|
| Auto-create an interest based on frequency analysis | Write authority belongs to operator; auto-creation violates canonicalization |
| Auto-record an occurrence without explicit operator trigger | Occurrence recording requires deliberate action per canon |
| Modify routing behavior based on relevance signal | Relevance is advisory-only per canon; routing authority must remain explicit |
| Suppress or deprioritize an artifact/response based on relevance signal | Decision authority remains with operator and governance layer |
| Auto-archive or mark an interest as dormant without approval | Temporal state is operator-designated; automatic state changes require governance |
| Inject relevance signals into LLM prompt construction without approval | Prompt injection is a consequential action, not a suggestion |
| Use relevance as a gate for any capability or feature | Relevance eligibility vs amplification requires explicit approval per doctrine |
| Surface relevance observations as facts rather than suggestions | Suggestion framing is required; presenting as fact implies authority |

---

## SECTION 6 — TEXT/VOICE SUGGESTION PATTERNS

The following patterns describe how Tier 2 suggestions should be framed in natural language:

### Interest creation suggestion
```
Pattern: "I've noticed [observation]. Would you like me to track this as an interest?"
Example: "Governance concerns have come up in 4 recent artifacts — would you like me to create a tracked interest?"
Constraints: Use "would you like" not "I am creating"; no auto-creation
```

### Occurrence recording suggestion
```
Pattern: "This relates to your [interest name] interest. Should I record an occurrence?"
Example: "This artifact is strongly related to your 'confidence calibration' interest. Should I record an occurrence?"
Constraints: "Should I" — not "I am recording"
```

### Merge suggestion
```
Pattern: "Your [interest A] and [interest B] have very similar tags. Consider reviewing them?"
Example: "You have two interests with 'governance quality' tags — should they be merged?"
Constraints: "Consider reviewing" not "I have merged them"
```

### Relevance surfacing
```
Pattern: "This is relevant to your [interest name] interest."
Example: "This artifact is relevant to your tracked interest in governance oversight."
Constraints: Statement of fact from _relevant_interests metadata — not a suggestion to act
```

### Dormancy note
```
Pattern: "Your [interest name] interest hasn't surfaced recently. Still active?"
Example: "Your 'operator safety constraints' interest hasn't been relevant in 45 days — still something to track?"
Constraints: Question, not statement of abandonment; invites operator to confirm or close
```

### Pattern: Suggestion cooldown

Suggestions on the same topic must not be repeated within:
- 24 hours for interest creation suggestions
- 12 hours for occurrence recording suggestions
- 4 hours for merge/similarity suggestions
- 2 hours for dormancy notes

This prevents suggestion spam and respects operator attention.

---

## SECTION 7 — SAFE FUTURE IMPLEMENTATION DIRECTIONS

### Phase A — Interest suggestion engine (safest first suggestion layer)

**What:** A function that observes artifacts and flags when an artifact has strong matches to no existing interest (high relevance score but no tracked interest covers the topic).

**How it works:**
- After an artifact is processed, query relevance surface against existing interests
- If no interests score above threshold but artifact has strong internal signals (low confidence, gap fields, etc.), flag as "potential new interest candidate"
- Store candidate observations in a suggestion queue (not state, just in-memory or ephemeral log)
- When operator naturally asks a question or reviews an artifact, surface the suggestion via normal channels

**Why safe:** No automatic writes; suggestion is presented, not executed; operator controls when/how suggestion is acted upon.

**Constraints:** Suggestion queue must not persist beyond the session unless explicitly saved by operator request. No background notification system.

### Phase B — Occurrence hint engine

**What:** A function that observes when an artifact strongly matches an existing interest but no occurrence has been recorded for that artifact-id yet.

**How it works:**
- After artifact processing, compare _relevant_interests output against interest's occurrence history
- If a match exists but the item_id is not in the interest's occurrence list, flag as "occurrence hint"
- Surface: "This artifact relates to [interest]. Record an occurrence?"

**Why safe:** Suggestion only; no automatic recording; operator chooses whether to act.

### Phase C — Interest similarity detector

**What:** A function that periodically (operator-triggered only, not background) compares all interests for tag/name overlap and flags potential duplicates.

**Implementation:** Not a background process. Operator explicitly asks "do I have duplicate interests?" or similar — then WESLR runs the comparison and reports.

**Why safe:** Request-response model; no unsolicited suggestions; operator initiates.

### What remains forbidden in all phases

- Auto-creation of interests (Phase A-C)
- Auto-recording of occurrences (Phase A-C)
- Background notification systems (Phase A-C — until explicit approval)
- Integration into routing or decision logic (Phase A-C)
- Prompt injection based on suggestion state (Phase A-C)

---

## SECTION 8 — STOP LINE

**Verified completed:**

- ✅ Doctrine addendum only — no production code changes
- ✅ No routing changes
- ✅ No new integrations
- ✅ No state mutation behavior defined
- ✅ docs/RELEVANCE_AUTONOMOUS_SUGGESTION_ADDENDUM_V1.md created
- ✅ Three tiers (observation → suggestion → governed consequence) defined
- ✅ Allowed autonomous observation behaviors listed
- ✅ Allowed proactive suggestion behaviors listed with trigger conditions and framing patterns
- ✅ Forbidden silent consequences explicitly enumerated
- ✅ Safe future implementation directions (Phase A-C) defined with operator-initiation constraint
- ✅ Suggestion cooldown rules established

**No code implemented in this step.** This addendum extends INTEREST_RELEVANCE_CANON_V1 and LONG_HORIZON_RELEVANCE_DOCTRINE_V1. Implementation of Phase A-C requires future authorized steps.

---

*This addendum was produced following the completion of Interest Tracker / Relevance chapter v1 and the first Relevance v2 slice (recency-only surfacing removed). It defines the safe boundary for autonomous observation and proactive suggestion.*