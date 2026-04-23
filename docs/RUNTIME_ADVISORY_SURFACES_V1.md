# RUNTIME_ADVISORY_SURFACES_V1
**Document type:** Design Specification  
**Status:** Initial  
**Date:** 2026-04-23  
**Scope:** Canonical advisory surface model for SatUi — operator-facing display, no code changes

---

## SECTION 1 — FILES CHANGED

```
docs/RUNTIME_ADVISORY_SURFACES_V1.md  [NEW]
```

---

## SECTION 2 — COMMANDS RUN

```
None — design only, no execution
```

---

## SECTION 3 — DESIGN SUMMARY

### What this document defines

A canonical model for all operator-facing advisory panels in SatUi — unified under one structure, one priority ordering, and one language contract.

### What already exists

SatUi renders two independent advisory panels today:

1. **Contamination advisory** — produced by `dialogue.py` → `_contamination_metadata`, shown as a risk-colored panel with type label + reason + expandable signal tags
2. **Lineage advisory** — produced by `dialogue.py` → `_lineage_inspection`, shown as a dot + label + expandable notes panel

Both are advisory (operator sees, operator decides). Both are attached to message bubbles in `chat_ui.py`. Neither has a shared model.

### What the problem is

Each advisory was designed independently. Ordering is effectively implementation-order (whichever `chat_ui.py` renders first). Future advisory types — context-selection, drift, safety, authority — would add without coordination, fragmenting the operator experience.

### Why this is about organization, not redesign

No rendering logic changes. No new advisory types introduced yet. No behavior changes. This document defines the **framework** that existing and future advisories slot into — so ordering, stacking, language, and display rules are semantic, not accidental.

---

## SECTION 4 — CANONICAL ADVISORY TYPES

### Current

| Type | Purpose | Attached to |
|---|---|---|
| `contamination` | Flags when 'this' resolved to an artifact that may not belong in the current context | Artifact reference turns |
| `lineage` | Shows whether the resolved artifact is root, derived, legacy, or has incomplete lineage | Artifact reference turns |

### Reserved for future (near-term)

| Type | Purpose | Status |
|---|---|---|
| `context-selection` | Signals when the operator may want to switch to a different active context/thread | Not yet implemented |
| `drift` | Flags observed response drift, unusual latency, or governance overrides | Not yet implemented |

Each reserved type requires its own design document before activation. This document provides the container; individual designs fill the slots.

---

## SECTION 5 — PRIORITY MODEL

### Why priority ordering matters

On a single message bubble, multiple advisories can be present simultaneously (contamination + lineage, for example). The operator should see the most operationally significant signal first — not whichever was implemented first.

### Priority ranking (highest to lowest)

1. **`contamination`** — Highest priority. Contamination is the only advisory that signals the artifact resolution itself may be wrong. If this is high-risk, everything else is secondary.
2. **`lineage`** — Second priority. Lineage informs whether the artifact is authoritative, derived, or legacy. High-generation or incomplete lineage is operationally significant but less urgent than contamination.
3. **`context-selection`** — Reserved. Lower priority than lineage. Context-switch signals are advisory; the operator has explicit control.
4. **`drift`** — Reserved. Lowest priority among active advisories. Drift is an internal observation signal.

### Rationale

Contamination gets highest priority because it is the only advisory that says the **resolution itself is suspect**. Lineage says what the artifact is; contamination says whether using it is safe. Context-selection and drift are lower priority because they are informational, not resolution-quality signals.

---

## SECTION 6 — STACKING / DISPLAY RULES

### Max visible advisories per message bubble

**Up to 2 visible by default.**  
If both contamination and lineage are present, both render in priority order. If a third advisory type exists (future), it collapses by default regardless of priority.

**Rationale:** More than 2 expanded panels per message creates visual noise and implies the system is unsure rather than informative. Additive visibility should have a ceiling.

### Primary vs secondary display

- **Primary advisory:** The highest-priority advisory that is present. Rendered with its full default display state.
- **Secondary advisory:** Lower-priority advisories present on the same bubble. Rendered in a collapsed state by default (icon + label only; expand on demand).

### When a panel should collapse by default

| Advisory | Default state |
|---|---|
| `contamination` — high risk | Visible (full) |
| `contamination` — medium risk | Collapsed (icon + type label) |
| `contamination` — low risk | Absent (not displayed in first slice) |
| `lineage` — root | Collapsed (dot + label) |
| `lineage` — derived | Collapsed (dot + label) |
| `lineage` — legacy_unknown | Collapsed (dot + label) |
| `lineage` — incomplete | Visible (dot + label + notes) |

### When a panel should not appear at all

- Advisory field is absent from the response dict → no panel rendered
- `risk_level: none` on contamination → no panel rendered (clean resolution needs no advisory)
- Artifact was not resolved (safe path) → no contamination advisory; lineage advisory also absent

---

## SECTION 7 — LANGUAGE / HUMAN FACTOR RULES

### Operator-safe wording

Every advisory label uses the vocabulary of **outcome**, not mechanism:

| Advisory | Say | Don't say |
|---|---|---|
| Contamination — high | "Domain mismatch" or "Topic bleed" | "Cross-domain keyword contamination detected" |
| Contamination — medium | "Possible mismatch" | "Medium-risk contamination_check triggered" |
| Lineage — root | "Root artifact" | "No parent_artifact_ids — generation 0" |
| Lineage — derived | "Based on previous artifact" | "Has parent artifact, lineage complete" |
| Lineage — legacy_unknown | "Older artifact" | "Predates lineage fields, legacy_unknown status" |
| Lineage — incomplete | "Lineage incomplete" | "Parent present but root_artifact_id null" |

### No raw IDs by default

Advisory panels must not expose internal artifact IDs, session IDs, or graph node references. If diagnostic detail requires an ID, it goes in the expandable section and is labeled as internal detail.

### No graph jargon in first slices

Words like "node", "edge", "traverse", "parent_artifact_ids", "root_artifact_id" do not appear in the primary label or reason text. They may appear in the expandable diagnostic section if needed for debugging.

### No debug-style clutter

Signal tag lists (`#message_domain_mismatch #artifact_context_present`) belong only in expandable sections, not in the primary label or reason. Keep the visible text to 1-2 lines maximum for the primary panel.

---

## SECTION 8 — FORBIDDEN DRIFT

### F1 — No advisory overload
**Forbidden:** Rendering more than 2 expanded advisories per message bubble without explicit operator action to expand a third.  
**Why:** Overloaded panels signal system uncertainty rather than providing clear guidance. Ceiling enforces legibility.

### F2 — No mixing advisories with authority/control
**Forbidden:** Advisory panels that contain buttons, toggles, or confirmation prompts.  
**Why:** Advisories inform; they do not gate. Authority and control surfaces are separate UI layers.

### F3 — No implementation-order deciding semantics
**Forbidden:** Ordering advisories by which was implemented first, or by code insertion order in `chat_ui.py`.  
**Why:** Ordering must be semantic (priority-based). Implementation order is arbitrary and changes with code evolution.

### F4 — No exposing raw internals by default
**Forbidden:** Showing artifact IDs, session IDs, field names, or graph references in the primary visible label or reason.  
**Why:** Primary display text is for operator reading. Internal identifiers are for debugging and require explicit expand to see.

### F5 — No new advisory types without design documents
**Forbidden:** Activating a new advisory type (context-selection, drift, etc.) without a documented design specifying its purpose, display model, priority rank, and language contract.  
**Why:** The framework prevents fragmentation. Each new advisory type needs its own design doc that slots into this model.

### F6 — No advisory ordering that buries contamination
**Forbidden:** Placing any advisory higher than contamination in the render order.  
**Why:** Contamination is the highest-priority signal. It cannot be visually buried below lower-priority advisories.

### F7 — No color as sole status conveyor
**Forbidden:** Relying on color (red/amber/green) as the only indicator of advisory severity.  
**Why:** Color supplements text. Operators who are color-blind or viewing in highambient light must be able to understand the advisory from text alone.

---

## SECTION 9 — RECOMMENDED FIRST IMPLEMENTATION

### Smallest safe organizational change

**Add an advisory priority registry in `chat_ui.py`** — a defined constant ordering advisories by priority (contamination before lineage), so render order is semantic not accidental. No new advisory types. No behavior changes.

**File:** `chat_ui.py` (modified)

**Change:** Before rendering, sort advisory panels by priority constant:

```python
ADVISORY_PRIORITY = {
    "contamination": 0,   # highest
    "lineage": 1,
    # future: "context-selection": 2,
    # future: "drift": 3,
}

def sort_advisories(advisory_list):
    return sorted(advisory_list, key=lambda a: ADVISORY_PRIORITY.get(a.get("type"), 99))
```

**What this achieves:**
- Render order is now semantic, not implementation-order
- The framework is in place for adding future advisories by priority
- No new panels, no behavior changes, no new authority
- Operator sees the same panels in a better order

**What this does NOT implement in first slice:**
- Stacking/ceiling rules (up to 2 visible advisories) — deferred
- Context-selection advisory — requires own design doc
- Drift advisory — requires own design doc
- Collapse-by-default differentiation — deferred

### Rationale for smallest first

Reordering is the lowest-risk change that establishes the priority framework. It does not change what panels exist, what they say, or when they appear. It only changes the visual order — which matters because contamination (highest priority) must be visible first.

---

## SECTION 10 — STOP LINE

**DOCUMENTATION ONLY — NO CODE CHANGES**

This document defines the canonical runtime advisory surface model for SatUi:
- Advisory types: contamination (current), lineage (current), context-selection (reserved), drift (reserved)
- Priority ranking: contamination > lineage > context-selection > drift
- Stacking rules: max 2 visible by default, primary vs secondary collapse model
- Language contract: outcome vocabulary, no IDs, no graph jargon, no debug clutter
- Forbidden drift: no overload, no authority mixing, no implementation-order semantics, no raw internals, no new advisories without design docs, no burying contamination, no color-only status
- First implementation: priority registry constant in `chat_ui.py` for semantic ordering

### Document Completeness

| Section | Status |
|---|---|
| 1. Files Changed | ✅ Complete |
| 2. Commands Run | ✅ Complete |
| 3. Design Summary | ✅ Complete |
| 4. Canonical Advisory Types | ✅ Complete |
| 5. Priority Model | ✅ Complete |
| 6. Stacking / Display Rules | ✅ Complete |
| 7. Language / Human Factor Rules | ✅ Complete |
| 8. Forbidden Drift | ✅ Complete |
| 9. Recommended First Implementation | ✅ Complete |
| 10. Stop Line | ✅ Complete |

---

*RUNTIME_ADVISORY_SURFACES_V1 — Design Specification*
*Design only. No code. No routing changes. No scoring changes. No governance changes.*
