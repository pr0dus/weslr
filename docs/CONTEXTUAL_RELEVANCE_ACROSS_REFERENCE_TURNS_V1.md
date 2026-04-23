# CONTEXTUAL_RELEVANCE_ACROSS_REFERENCE_TURNS_V1.md

**Status:** DESIGN DRAFT — canonical model for reference-turn relevance
**Date:** 2026-04-21
**Authoritative for:** Runtime relevance in artifact lifecycle reference turns

---

## SECTION 1 — FILES CHANGED

| File | Change |
|------|--------|
| `docs/CONTEXTUAL_RELEVANCE_ACROSS_REFERENCE_TURNS_V1.md` | **Created** — this document |

No production code files modified. No schema changes. No behavior changes.

---

## SECTION 2 — COMMANDS RUN

None. This pass is documentation-only.

---

## SECTION 3 — DESIGN SUMMARY

### Section A — Purpose

**Why single-message relevance is insufficient for artifact lifecycle turns:**

Single-message relevance (`query_relevant_interests(text=message)`) scores interests against the literal input string. This works for standalone turns where the message itself contains domain content ("optimize nginx reverse proxy").

In artifact lifecycle turns, the message is deliberately minimal — "improve this", "explain this", "give me another version". The message string has no domain keywords. Single-message scoring returns an empty result even when the active artifact is rich with context ("The photovoltaic efficiency hypothesis should specify...").

This is not a scoring failure. It is the correct behavior of a system that scores what it is given. The design gap is that the **contextual signal** — the meaningful domain content in the resolved artifact — is discarded because it lives in the artifact store, not in the message.

**Why reference turns need contextual relevance design:**

Reference turns have a fundamentally different structure:

```
prior artifact (stored) → reference phrase ("improve this") → new artifact (stored)
```

The reference phrase alone tells WESLR nothing about what domain to score against. The prior artifact's content is the meaningful signal. A relevance system that ignores this signal produces empty results for every reference turn, making `_relevant_interests` useless in exactly the workflow where it matters most.

The design challenge: **how does WESLR surface meaningful relevance in reference turns without changing routing authority, bypassing governance, or creating a second scoring system?**

---

### Section B — Current Reality (Phase 1B)

**What currently happens in Phase 1B:**

```
sat-010: "improve the hypothesis about photovoltaic efficiency"
  → Runtime path: artifact_proposal branch
  → _relevant_interests: [efficiency:4, photovoltaic:4, scientific_analysis:3]  ← scored from MESSAGE
  → Artifact written to store (art-X)
  → Evaluation artifact records: raw interests snapshot

sat-011: "improve this"  [art-X is active]
  → Runtime path: artifact_proposal branch (reference resolution runs)
  → _relevant_interests: []  ← scored from "improve this" (no keywords)
  → New artifact written to store (art-Y)
  → Evaluation artifact records: raw interests empty (correct), resolved artifact content captured separately
  → auto_flags["resolved_artifact_was_enriched"] = True
  → resolved_artifact_interests = [efficiency, photovoltaic, scientific_analysis] ← re-scored from artifact content

sat-012: "explain this"  [art-X is active]
  → Same pattern: raw interests empty, resolved content captured, enriched interests annotated

sat-013: "give me another version"  [art-X is active]
  → Same pattern: raw interests empty, resolved content captured
```

**Three distinct data items are being recorded:**

| Data | Source | What it represents |
|------|--------|-------------------|
| `relevant_interests_snapshot` | Runtime: `query_relevant_interests(text=raw_message)` | Message-level relevance (what the runtime produced) |
| `resolved_artifact_content` | Artifact store: `get_artifact(active_artifact_id)` | The actual artifact content after resolution |
| `resolved_artifact_interests` | Evaluation runner: `query_relevant_interests(text=resolved_content)` | Artifact-context relevance (re-scored from resolved content, annotation only) |

**What is currently missing from the runtime output:**

The runtime response dict contains only `relevant_interests_snapshot` (message-level). The resolved artifact content and its interests are captured by the evaluation runner as annotations — they are NOT visible in the runtime response.

This means: if WESLR or an operator inspects a runtime response for a reference turn, they see empty interests with no indication that meaningful artifact-context relevance exists.

---

### Section C — Relevance Modes

Three canonical modes, each with distinct semantics:

#### Mode 1 — Message Relevance

**What it is:** `query_relevant_interests(text=raw_message, tags=[])`

**When it applies:** All turns. Always computed. Advisory.

**What it represents:** The relevance signal present directly in the user's message string, without any resolution or context enrichment.

**Use case:** Standalone turns where the message contains domain content. Good for routing hints, interest tracking, and evaluation baseline.

**Limitation:** Returns empty for reference phrases by design. Not a failure.

---

#### Mode 2 — Artifact-Context Relevance

**What it is:** `query_relevant_interests(text=resolved_artifact_content, tags=[])`, applied only when:
- a reference phrase was detected (`_is_artifact_reference_phrase`)
- an active artifact was resolved (`_has_active_artifact == True`)

**When it applies:** Only in reference turns with an active artifact. Advisory. Never bypasses governance.

**What it represents:** The relevance signal present in the artifact that the user is referencing — the domain context that motivated the reference.

**Use case:** Informs WESLR about what domain the user is working in during artifact lifecycle turns. Enables meaningful interest tracking without requiring the user to repeat domain keywords every turn.

**Limitation:** Scores the artifact content, not the user's intent for the new artifact. A user saying "explain this" may not want a governance quality artifact. The interests from the prior artifact are context signal, not directive.

---

#### Mode 3 — Combined Advisory Relevance

**What it is:** A structured metadata annotation on the runtime response, present only in reference turns.

```json
{
  "_relevant_interests": [],           // Mode 1: always present
  "_artifact_context_interests": [],   // Mode 2: present when resolved artifact exists
  "_reference_resolved": true,         // Flag: was reference resolution attempted?
  "_reference_resolved_to": "art-...", // artifact_id of resolved artifact
  "_relevance_mode": "reference-turn" // "message" | "reference-turn" | "combined"
}
```

**When it applies:** In all runtime responses. Advisory fields are `null`/`[]` when not applicable.

**What it represents:** The complete relevance picture for this turn, split by source so consumers can distinguish message-level from artifact-context.

**Use case:** WESLR self-inspection, SatUi operator display, evaluation artifact annotation, interest tracking across artifact lifecycle.

**Limitation:** `_artifact_context_interests` is annotation (re-scored from stored artifact content, not from the runtime's own scoring). It should not be used to modify runtime behavior — only to inform observation and evaluation.

---

### Section D — Reference Turn Cases

#### D.1 — "improve this"

**Input:** "improve this" (with active artifact)  
**Message relevance:** Empty (no keywords)  
**Artifact-context relevance:** Scored from resolved artifact content  
**Combined advisory:** `_relevance_mode = "reference-turn"`, `_artifact_context_interests` populated

**Design question:** Should the artifact-context interests from the prior artifact inform what interests WESLR tracks for this user/session going forward?

**Decision:** Yes — but as advisory annotation only. WESLR can read `_artifact_context_interests` to know that the user has been working on `photovoltaic/efficiency` and update its session-level interest tracking. It may NOT use this to change routing, scoring weights, or governance thresholds.

---

#### D.2 — "explain this"

**Input:** "explain this" (with active artifact)  
**Message relevance:** Empty (no keywords)  
**Artifact-context relevance:** Scored from resolved artifact content  
**Combined advisory:** `_relevance_mode = "reference-turn"`, `_artifact_context_interests` populated

**Special consideration:** "explain this" often means the user wants to understand what the artifact says, not what domain it belongs to. Artifact-context interests inform that the artifact is about `photovoltaic`, but the user's actual question ("what does this say?") is answered by the artifact's content — not by interests.

**Design implication:** In "explain this" turns, `_artifact_context_interests` should be clearly labeled as context signal (what the artifact is about) rather than instructional signal (what the user wants). The evaluation artifact should note this distinction.

---

#### D.3 — "give me another version"

**Input:** "give me another version" (with active artifact)  
**Message relevance:** Empty (no keywords)  
**Artifact-context relevance:** Scored from resolved artifact content  
**Combined advisory:** `_relevance_mode = "reference-turn"`, `_artifact_context_interests` populated

**Special consideration:** This turn should generate a new artifact revision. The artifact-context interests from the prior artifact inform what the new artifact should be about — the same domain, a different formulation.

**Design implication:** `_artifact_context_interests` for this turn tells WESLR which domain interests are in play for the revision. This can inform SatUi operator inspection ("user requested another version of a photovoltaic efficiency artifact") without being a routing directive.

---

#### D.4 — Reference phrase with NO active artifact

**Input:** "improve this" (no active artifact)  
**Message relevance:** Empty (no keywords)  
**Artifact-context relevance:** Not applicable — no artifact resolved  
**Combined advisory:**
```json
{
  "_relevant_interests": [],
  "_artifact_context_interests": null,
  "_reference_resolved": false,
  "_reference_resolved_to": null,
  "_relevance_mode": "reference-no-artifact"
}
```

**WESLR behavior:** Returns safe fallback message: "I don't have a current stored artifact to refer to yet."

**Design implication:** This case is handled correctly today. The combined advisory structure makes it explicit that resolution was attempted (`_reference_resolved = true`) but failed (`_reference_resolved_to = null`), distinguishing it from a turn where no reference was attempted at all.

---

### Section E — Output Model (Future Runtime Metadata)

The canonical runtime response shape for all turns should include:

```json
{
  "message": "...",
  "audience": "...",
  "source": "...",
  "_relevant_interests": [...],           // Mode 1: message-level
  "_reference_metadata": {
    "_reference_resolved": true,           // boolean
    "_reference_resolved_to": "art-...",  // artifact_id or null
    "_reference_phrase_detected": "improve this",  // detected phrase or null
    "_artifact_context_interests": [...],   // Mode 2: re-scored from resolved artifact
    "_relevance_mode": "reference-turn"   // "message" | "reference-turn" | "reference-no-artifact"
  }
}
```

**Field semantics:**

| Field | Type | Present when |
|-------|------|-------------|
| `_relevant_interests` | `list` | Always |
| `_reference_metadata._reference_resolved` | `bool` | Always |
| `_reference_metadata._reference_resolved_to` | `str \| null` | Always |
| `_reference_metadata._reference_phrase_detected` | `str \| null` | When phrase detected |
| `_reference_metadata._artifact_context_interests` | `list \| null` | When artifact resolved |
| `_reference_metadata._relevance_mode` | `str` | Always |

**Key rules:**
- `_relevant_interests` is never suppressed or rewritten based on artifact context
- `_artifact_context_interests` is additive annotation, not a replacement
- Both are advisory — neither has authority over routing or governance
- `_relevance_mode` distinguishes the three cases so consumers can handle each appropriately

---

### Section F — Forbidden Drift

The following are explicitly forbidden in any implementation of this design:

1. **No routing authority for `_artifact_context_interests`.** `_artifact_context_interests` may not influence which routing branch is taken. It is annotation only.

2. **No governance triggers from reference-turn relevance.** A high score in `_artifact_context_interests` may not trigger `ExecutionGate`, change proposal status, or bypass governance thresholds.

3. **No silent score rewriting.** `_relevant_interests` (message-level) may not be silently replaced by `_artifact_context_interests`. The two must coexist and be clearly distinguished.

4. **No hidden relevance.** The distinction between message-level and artifact-context relevance must be visible in the runtime metadata. An operator inspecting a response must be able to tell which interests came from the message and which came from the resolved artifact.

5. **No auto-enrichment of message interests.** Artifact-context interests may not be injected into `_relevant_interests` for non-evaluation purposes (e.g., modifying routing, generating proposals, changing scores).

6. **No interest tracking write-back.** `_artifact_context_interests` may not write to the interest registry or update `occurrence_count`.

7. **No routing path changes.** The routing path taken for a reference turn must remain identical whether or not artifact-context interests are present. The only difference is the advisory metadata annotation.

---

### Section G — Recommended First Implementation

**Smallest safe implementation:** Add `_reference_metadata` as an advisory annotation field to the runtime response in `build_communicator_message_payload()`, without changing routing, scoring, or governance.

**Changes required:**

1. **In `dialogue.py`** — After the reference resolution check, build a `_reference_metadata` dict:
   ```python
   _reference_metadata = {
       "_reference_resolved": bool,
       "_reference_resolved_to": artifact_id or None,
       "_reference_phrase_detected": phrase or None,
       "_artifact_context_interests": enriched_interests or None,
       "_relevance_mode": "message" | "reference-turn" | "reference-no-artifact"
   }
   ```
   Include in the return dict alongside `_relevant_interests`.

2. **No changes to:** scoring logic, routing branches, `ExecutionGate`, `change_proposals`, `self_improvement_proposal`, governance paths, or interest registry.

3. **Preserve existing behavior:** `_relevant_interests` remains the message-level score. `_reference_metadata._artifact_context_interests` is additive annotation only.

**Rationale:** This is the smallest safe step because:
- It is purely additive — existing responses unchanged
- No routing influence — `_reference_metadata` is advisory only
- No scoring changes — `_relevant_interests` unchanged
- No governance changes — annotation doesn't trigger governance
- Enables WESLR self-inspection and SatUi operator display of reference-turn context
- Establishes the canonical metadata structure for future phases

**What NOT to implement first:**
- Changing evaluation runner to use `_artifact_context_interests` instead of `relevant_interests`
- Propagating `_artifact_context_interests` into routing decisions
- Auto-tracking interests based on artifact context
- Phase 1C (multi-turn scenarios) before Phase 1B is stable

---

## SECTION 4 — STOP LINE

**Confirmed:**
- Documentation only ✅
- No production code changes ✅
- No schema changes (design phase) ✅
- No behavior changes ✅
- No routing changes ✅
- No scoring changes ✅
- No governance changes ✅
- New document created: `docs/CONTEXTUAL_RELEVANCE_ACROSS_REFERENCE_TURNS_V1.md` ✅

**Stop after this pass. No code changes. No behavior changes.**

---

*This document defines the canonical model for runtime relevance in artifact lifecycle reference turns. All implementation work must reference this document. The recommended first implementation (adding `_reference_metadata` to the runtime response) should be implemented before Phase 1C.*
