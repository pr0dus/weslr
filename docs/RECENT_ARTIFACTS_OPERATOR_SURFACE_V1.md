# RECENT_ARTIFACTS_OPERATOR_SURFACE_V1
**Document type:** Design Specification
**Status:** Initial
**Date:** 2026-04-23
**Scope:** Canonical operator-facing recent artifacts list surface for SatUi — additive, no redesign

---

## SECTION 1 — FILES CHANGED

```
docs/RECENT_ARTIFACTS_OPERATOR_SURFACE_V1.md  [NEW]
```

---

## SECTION 2 — COMMANDS RUN

```
None — documentation only, no execution
```

---

## SECTION 3 — DESIGN SUMMARY

### Purpose

The recent artifacts list gives operators a lightweight, read-only way to browse all known artifacts without requiring an artifact ID or active continuity context. It exists because:

1. Operators need a low-friction way to discover what artifacts exist and their basic properties
2. The inspect-from-bubble and inspect-current-artifact flows both require a known artifact ID or active continuity state — the list fills the gap
3. It provides artifact discovery before inspection, making the two surfaces complementary

### Current Reality

**What exists today:**

| Layer | Component | Shape |
|---|---|---|
| API | `GET /api/artifacts/recent` | Returns `{"artifacts": [{artifact_id, created_at, type, lineage_status}, ...]}` |
| Backend | `chat_ui.py` handler | Calls `list_artifacts(limit=20)`, then per-item `inspect_artifact_lineage()` for status |
| Artifact store | `weslr.artifact_store.list_artifacts()` | Returns compact artifact list, newest first |
| Lineage module | `weslr.lineage_inspector.inspect_artifact_lineage()` | Classifies each artifact into status |
| UI | SatUi collapsible "Show recent artifacts" button | Scrollable list inside existing inspect section |

**What does not exist yet:**
- Filtering or search within the list
- Pagination (beyond 20)
- Sorting options
- Batch inspection (inspect multiple at once)
- Artifact content preview on hover
- Creation of new artifacts through the list
- Deletion or modification through the list
- Timestamps beyond created_at

---

## SECTION 4 — SAFE LIST FIELDS

The following fields are the canonical visible output of the recent artifacts list. Each is shown in the compact list row.

| Field | Source | Meaning |
|---|---|---|
| `artifact_id` | `artifact.artifact_id` | Internal identifier — shown in abbreviated/minimal form in list; full ID used for inspect |
| `created_at` | `artifact.created_at` | ISO timestamp — shown in compact datetime format (YYYY-MM-DD HH:MM) |
| `type` | `artifact.type` | Artifact classification (e.g., `artifact_revision`) |
| `lineage_status` | `inspect_artifact_lineage()` output | `root` \| `derived` \| `incomplete` \| `legacy_unknown` — colored indicator |

These fields are safe because they:
- Describe observable static properties of each artifact
- Are all read from existing artifact metadata
- Can be safely displayed without operator action or interpretation

---

## SECTION 5 — HIDDEN / INTERNAL FIELDS

The following exist in the artifact model but are not displayed in the recent artifacts list.

| Field | Reason hidden |
|---|---|
| `content` | Artifact content can be large and may include intermediate reasoning. Not needed for list-level browsing. |
| `parent_artifact_ids` | Parent list is graph traversal data. `lineage_status` conveys the classification outcome without exposing the field. |
| `root_artifact_id` | Available via inspection. Not needed in the list. |
| `generation` | Available via inspection. `lineage_status` already conveys root vs derived distinction. |
| `context` (full object) | Internal metadata structure. Field labels surfaced only through deliberate display design. |
| `thread_ids` | Available via inspection. Not needed for list browsing. |

---

## SECTION 6 — RELATION TO ARTIFACT INSPECTION AND CONTINUITY

### Relationship to Artifact Inspection Surface

The recent artifacts list and the artifact inspection surface are complementary:

- **List** → answers "what artifacts exist?" with basic properties and status
- **Inspection** → answers "what is this specific artifact's full facts?" with 8 structured fields

The list is the entry point; inspection is the drill-down. Clicking any artifact in the list populates the inspect input and triggers the existing inspect flow — no new inspection logic is introduced.

### Relationship to Continuity

The recent artifacts list is **continuity-agnostic**:
- It shows all known artifacts regardless of thread membership
- It does not filter to only active-thread artifacts
- An artifact's presence in the list does not imply it is the current active artifact
- Thread membership is available through the inspection surface

This separation is intentional: operators may need to inspect an artifact that is not currently active.

### What is not included

- No "current artifact" indicator in the list — the "Inspect current artifact" button handles that separately
- No thread context in the list rows
- No link between list items and active continuity state

---

## SECTION 7 — OPERATOR / DEBUG ROLE

### Who uses this surface

1. **Discovery** — "What artifacts have been created? What are they?"
2. **Debug continuity** — "The active artifact seems wrong — let me check what else exists"
3. **Inspection entry point** — find an artifact, then inspect it
4. **Session review** — see artifact creation timeline without opening thread history

### What the surface does NOT do

- It does not make recommendations about which artifact to use
- It does not filter or rank artifacts by relevance
- It does not modify artifact state
- It does not trigger routing or scoring
- It does not imply authority or correctness

### Language contract

The list uses minimal operational vocabulary:
- Artifact ID — shown as-is, not abbreviated beyond display
- `created_at` — compact ISO datetime
- `type` — raw type string from artifact model
- `lineage_status` — colored indicator: blue=root, green=derived, amber=incomplete/legacy_unknown
- No words like "node", "edge", "parent", "child", "traverse"

---

## SECTION 8 — FORBIDDEN DRIFT

### F1 — No content in list rows
**Forbidden:** Displaying `artifact.content` or partial content preview in the list rows.  
**Why:** Content can be large and may expose intermediate reasoning. Inspection is the appropriate surface for content review.

### F2 — No modification through the list
**Forbidden:** Adding write operations (delete, update, archive) triggered from list items.  
**Why:** Read-only by contract. Modification requires separate authority and governance design.

### F3 — No pagination in first slice
**Forbidden:** Adding pagination controls, page numbers, or offset-based navigation without a separate design document.  
**Why:** The 20-item default is a safety ceiling. Pagination requires display and UX decisions.

### F4 — No search/filter without design doc
**Forbidden:** Adding text search, type filter, or status filter to the list without a separate design document.  
**Why:** Filtering requires display decisions (filter UI, active filter state, clear filter action) that belong in a separate design.

### F5 — No batch inspection
**Forbidden:** Selecting multiple artifacts from the list for simultaneous inspection.  
**Why:** Batch operations require multi-select UI, result handling, and display decisions. Single-select inspection is the established contract.

### F6 — No current-artifact highlight in list
**Forbidden:** Auto-highlighting or marking the currently active artifact within the list.  
**Why:** Active artifact is already accessible via "Inspect current artifact" button. Mixing the two concepts would blur the list's discovery role.

### F7 — No sorting controls
**Forbidden:** Adding sort options (by date, type, lineage status) without a separate design document.  
**Why:** List is currently newest-first. Sort controls add UI complexity and state that requires deliberate design.

---

## SECTION 9 — FUTURE EXTENSION BOUNDARY

Extensions that fit within the canonical model:

| Extension | Design needed |
|---|---|
| Text search within artifact IDs | Separate design doc — requires filter UI and clear-search action |
| Type filter dropdown | Separate design doc — requires filter state management |
| Artifact content preview on hover | Separate design doc — requires hover state, content truncation, display contract |
| Pagination beyond 20 | Separate design doc — requires page controls, offset management |
| Artifact creation from list | Separate design doc — requires write authority and creation form |

Extensions that do NOT fit the canonical model (require rethinking):
- Any write operations through the list
- Graph traversal or parent/child chain display
- Batch multi-select inspection
- Sorting controls
- Current-artifact highlighting within the list

---

## SECTION 10 — STOP LINE

**DOCUMENTATION ONLY — NO CODE CHANGES**

This document defines the canonical recent artifacts operator surface:
- Read-only list of up to 20 most recent artifacts, newest first
- Safe visible fields: artifact_id, created_at, type, lineage_status (colored)
- Hidden fields: content, parent_artifact_ids, root_artifact_id, generation, context, thread_ids
- Role: artifact discovery entry point — complements but does not replace "Inspect current artifact"
- Relationship to inspection: list is entry point, inspection is drill-down; clicking an item triggers existing inspect flow
- Relationship to continuity: list is continuity-agnostic; no filtering by active thread
- Forbidden drift: no content display, no modification, no pagination, no search/filter, no batch inspection, no current-artifact highlight, no sort controls
- Extension boundary defined: search, filter, pagination, content preview, creation each require separate design docs

### Document Completeness

| Section | Status |
|---|---|
| 1. Files Changed | ✅ Complete |
| 2. Commands Run | ✅ Complete |
| 3. Design Summary | ✅ Complete |
| 4. Safe List Fields | ✅ Complete |
| 5. Hidden/Internal Fields | ✅ Complete |
| 6. Relation to Artifact Inspection and Continuity | ✅ Complete |
| 7. Operator/Debug Role | ✅ Complete |
| 8. Forbidden Drift | ✅ Complete |
| 9. Future Extension Boundary | ✅ Complete |
| 10. Stop Line | ✅ Complete |

---

*RECENT_ARTIFACTS_OPERATOR_SURFACE_V1 — Design Specification*
*Documentation only. No code. No behavior changes.*
