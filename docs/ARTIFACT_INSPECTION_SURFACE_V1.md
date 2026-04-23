# ARTIFACT_INSPECTION_SURFACE_V1
**Document type:** Design Specification
**Status:** Initial
**Date:** 2026-04-23
**Scope:** Canonical operator-facing artifact inspection surface for SatUi — additive, no redesign

---

## SECTION 1 — FILES CHANGED

```
docs/ARTIFACT_INSPECTION_SURFACE_V1.md  [NEW]
```

---

## SECTION 2 — COMMANDS RUN

```
None — documentation only, no execution
```

---

## SECTION 3 — DESIGN SUMMARY

### Purpose

The artifact inspection surface provides operators and debug workflows with a stable, minimal read view into individual artifacts — without exposing graph internals, authority language, or traversal logic.

It exists because:
1. Operators need a trusted way to inspect a single artifact's core data, lineage classification, and thread membership
2. Debug workflows require a stable contract that won't break as internal graph models evolve
3. The surface must not imply ownership, control, or routing significance — it is informational only

### Current Reality

**What exists today:**

| Layer | Component | Shape |
|---|---|---|
| API | `POST /api/artifact_inspect` | Returns `{artifact, lineage_inspection, continuity}` JSON |
| Backend | `chat_ui.py` handler | Reads `artifact_id` from JSON body, calls `get_artifact()`, runs `inspect_artifact_lineage()` |
| Lineage module | `weslr/lineage_inspector.py` | Returns `ArtifactLineageInspection` dataclass with `.to_dict()` |
| Artifact store | `weslr/artifact_store.py` | `get_artifact()` — read-only, no traversal |
| UI | SatUi collapsible inspect section | Input field + Go button, 8-field structured display |

**What does not exist yet:**
- Multi-artifact batch inspection
- Path/traversal queries (ancestor chain, sibling list)
- Graph visualization or node/edge display
- Artifact content diff or version comparison
- Inspection logging or audit trail
- Operator annotations on artifacts

---

## SECTION 4 — SAFE VISIBLE FIELDS

The following fields are the canonical visible output of the inspection surface. All are surfaced in the SatUi view and available via the API response.

| Field | Source | Meaning |
|---|---|---|
| `type` | `artifact.type` | Artifact classification (e.g., `artifact_revision`) |
| `created_at` | `artifact.created_at` | ISO timestamp of creation |
| `source` | `artifact.source` | Origin system (e.g., `dialogue`) |
| `lineage_status` | `lineage_inspection.lineage_status` | `root` \| `derived` \| `incomplete` \| `legacy_unknown` |
| `generation` | `lineage_inspection.generation` | Distance from root (0 for root), null if unknown |
| `root_artifact_id` | `lineage_inspection.root_artifact_id` | Topmost ancestor ID |
| `notes` | `lineage_inspection.notes` | Human-readable lineage note |
| `in_active_thread` | `continuity.in_active_thread` | Boolean: does this artifact appear in any thread? |
| `thread_ids` | `continuity.thread_ids` | List of thread IDs this artifact belongs to |

These fields are safe because they:
- Describe observable properties of the artifact itself
- Use outcome vocabulary (no graph jargon in visible labels)
- Are stable across internal refactors

---

## SECTION 5 — HIDDEN / INTERNAL FIELDS

The following are explicitly not surfaced in the canonical inspection view. They exist in the internal artifact model but are not exposed to operators via the inspection surface.

| Field | Reason hidden |
|---|---|
| `artifact_id` (in artifact block) | Internal identifier; operators reference artifacts by context in the conversation, not by raw ID. ID shown in SatUi input placeholder only. |
| `parent_artifact_ids` | Raw parent list is graph traversal data, not an operator-level fact. The `lineage_status` classification conveys the same information in outcome vocabulary. |
| `content` | Full artifact content can be large and is not needed for inspection-level review. Separate UI if content inspection is needed. |
| `context` (full object) | Full context block is internal metadata. Field labels and key values may be surfaced in future if operationally needed, but not raw structure. |
| `thread_ids` raw list in full detail | `in_active_thread` boolean is sufficient for operational awareness. Full thread ID list available via API for debug use. |

**Rationale:** The surface shows what matters for operator decisions — what it is, where it came from, whether it is active. It does not expose the graph machinery underneath.

---

## SECTION 6 — RELATION TO LINEAGE AND CONTINUITY

### Lineage Inspection

`lineage_inspection` is the structured output of `inspect_artifact_lineage()` applied to a single artifact. It classifies the artifact into one of four mutually exclusive statuses:

- **root** — no parent; generation 0; self as root
- **derived** — has parents; root_artifact_id set; generation > 0
- **incomplete** — has parents but root_artifact_id is null (data gap, not an artifact type)
- **legacy_unknown** — predates lineage fields; classification is unknown

The `lineage_status` field is the canonical operator-facing fact about an artifact's lineage. It is derived from explicit fields only — no inference beyond the classification rules documented in `weslr/lineage_inspector.py`.

### Continuity

`continuity` provides thread membership signal:
- `in_active_thread`: boolean — true if the artifact appears in any known thread context
- `thread_ids`: list — specific thread IDs

This tells the operator whether the artifact is connected to active conversation threads, not whether it is "correct" or "authoritative." Thread membership is a fact; authority is an operator judgment.

### What is not included

- **No lineage chain** — ancestor chain beyond root is not shown. `root_artifact_id` provides the anchor point; full chain is graph data.
- **No child/sibling information** — inspection is single-artifact only. Relationships are graph-level facts, not inspection-level.
- **No contamination data** — contamination metadata is a runtime signal on message resolution, not an artifact property. Artifacts are inspected; contamination is observed on reference turns.

---

## SECTION 7 — OPERATOR / DEBUG ROLE

### Who uses this surface

1. **Operator debugging continuity** — "I said improve this and got the wrong artifact — is it stale, wrong generation, or from the wrong thread?"
2. **Session review** — "This artifact was created in Session A — is it root or derived, and is it still active?"
3. **Debug workflows** — confirm artifact state without opening raw JSON files

### What the surface does NOT do

- It does not make recommendations
- It does not flag "this artifact should be used" or "this artifact is wrong"
- It does not trigger routing, scoring, or governance
- It does not modify artifact state
- It does not imply authority or preference

### Language contract

The surface uses operational vocabulary:
- "root artifact" / "derived artifact" / "lineage incomplete" / "older artifact" — outcome labels
- "yes" / "no" for active thread — binary, unambiguous
- "gen N" for generation — compact, no jargon
- No words like "node", "edge", "parent", "child", "traverse", "graph"

---

## SECTION 8 — FORBIDDEN DRIFT

### F1 — No graph traversal exposure
**Forbidden:** Showing parent chains, ancestor paths, or descendant lists in the canonical surface.  
**Why:** Chain data is graph machinery. Operators need classification, not traversal.

### F2 — No content display in first slice
**Forbidden:** Showing `artifact.content` in the inspection view without a separate deliberate design.  
**Why:** Content can be large and may include intermediate reasoning. A separate content view requires its own display design.

### F3 — No authority implication
**Forbidden:** Wordings like "valid artifact", "correct artifact", "authoritative version" in any visible label.  
**Why:** Artifact authority is an operator judgment, not a system signal. Inspection informs; it does not certify.

### F4 — No inspection → control bridging
**Forbidden:** Connecting any inspection field to routing logic, scoring, or governance action.  
**Why:** The surface is read-only observation. Linking inspection to control converts display into authority.

### F5 — No exposure of raw artifact ID as primary label
**Forbidden:** Displaying the raw `artifact_id` as a prominent visible label in the inspection output.  
**Why:** Internal identifier. Operators reference artifacts by conversation context. ID is available in API but not highlighted in UI.

### F6 — No multi-artifact batch in first slice
**Forbidden:** Adding batch inspection (multiple IDs at once) without a separate design document.  
**Why:** Single-artifact inspection is the stable foundation. Batch requires pagination, error handling, and display decisions that belong in a separate design.

### F7 — No modification through the inspection surface
**Forbidden:** Including any write operation (PUT, PATCH, DELETE on artifacts) in the inspection surface.  
**Why:** Read-only by contract. Modification requires separate authority and governance design.

---

## SECTION 9 — RECOMMENDED FUTURE EXTENSION BOUNDARY

The surface is designed to be extended, not replaced. Extensions that fit within the canonical model:

| Extension | Design needed |
|---|---|
| Content view (see full artifact content) | Separate design doc for content display |
| Multi-artifact batch inspection | Separate design doc for pagination + error handling |
| Inspection audit log | Separate design doc for operator annotation |
| Artifact comparison (diff two) | Separate design doc for comparison UI |
| Lineage chain path display | Separate design doc — requires graph UI decisions |

Extensions that do NOT fit the canonical model (require rethinking):
- Any write operations
- Graph traversal visualization
- Routing/score integration
- Exposure of internal field names as operator labels

---

## SECTION 10 — STOP LINE

**DOCUMENTATION ONLY — NO CODE CHANGES**

This document defines the canonical artifact inspection surface:
- Single-artifact read-only inspection via `POST /api/artifact_inspect`
- 9 safe visible fields: type, created_at, source, lineage_status, generation, root_artifact_id, notes, in_active_thread, thread_ids
- Hidden fields: parent_artifact_ids, content, context structure, raw artifact_id as primary label
- Role: operator/debug informational only — no authority, no control, no routing
- Language contract: outcome vocabulary, no graph jargon
- Forbidden drift: no traversal, no content display, no authority language, no inspection→control bridging, no raw ID exposure, no batch in first slice, no modification
- Extension boundary defined for future design docs

### Document Completeness

| Section | Status |
|---|---|
| 1. Files Changed | ✅ Complete |
| 2. Commands Run | ✅ Complete |
| 3. Design Summary | ✅ Complete |
| 4. Safe Visible Fields | ✅ Complete |
| 5. Hidden/Internal Fields | ✅ Complete |
| 6. Relation to Lineage and Continuity | ✅ Complete |
| 7. Operator/Debug Role | ✅ Complete |
| 8. Forbidden Drift | ✅ Complete |
| 9. Recommended Future Extension Boundary | ✅ Complete |
| 10. Stop Line | ✅ Complete |

---

*ARTIFACT_INSPECTION_SURFACE_V1 — Design Specification*
*Documentation only. No code. No behavior changes.*