# LINEAGE-AWARE ARTIFACT INSPECTION V1
**Document type:** Design Specification  
**Status:** Initial  
**Date:** 2026-04-23  
**Scope:** Operator-facing lineage inspection surface — no graph UI, no code changes

---

## SECTION 1 — PURPOSE

### Why lineage needs a simple inspection surface before graph display

The artifact system now carries lineage fields on all new artifacts (`parent_artifact_ids`, `root_artifact_id`, `generation`). The underlying graph model is documented in doctrine. However, before any graph UI is built, the system needs a minimal, trustworthy way for operators and internal processes to answer basic lineage questions about any artifact.

Graph UI is layered on top of inspection capability. It requires interpretation, traversal logic, and rendering decisions. Those layers introduce complexity and potential for inference beyond the explicit data. The inspection surface must come first because it establishes what is authoritative versus what is derived.

Without a defined inspection model, operators have no safe way to ask "where did this artifact come from?" They must either inspect raw artifact JSON directly (error-prone, inconsistent) or rely on future graph UI (premature for operational decisions).

### Why operators and system need understandable lineage facts first

Operators make decisions based on what they can reason about. A lineage inspection surface that produces a small, well-defined output structure is easier to audit, test, and trust than ad-hoc JSON inspection.

The system also needs an inspection interface that does not expose raw graph complexity. Internal processes that evaluate artifacts should get a consistent, versioned response shape — not a graph traversal result that might vary by depth or direction.

---

## SECTION 2 — CURRENT REALITY

### Lineage fields that now exist on new artifacts

| Field | Type | Description |
|-------|------|-------------|
| `parent_artifact_ids` | `list[str]` | Direct parents; empty if root |
| `root_artifact_id` | `str \| null` | Topmost ancestor; null if lineage unknown |
| `generation` | `int` | Distance from root (0 = root) |

These fields are present on all newly created artifacts. Contract is explicit for roots and derived artifacts.

### Continuity and thread data that also exists

Artifacts may reference thread or session context. This data is stored separately from lineage fields and is consulted but not merged into the lineage model.

### What is not yet implemented

- No inspection helper that reads lineage fields and produces a consistent structured response
- No operator-facing surface (CLI, debug, or operator panel) for lineage questions
- No graph engine for traversal or path queries
- No stored `lineage_status` on artifacts — only raw fields
- No distinction between `legacy_unknown` (old artifact, no fields) and `incomplete` (new artifact, fields present but parent/root missing)

---

## SECTION 3 — CORE INSPECTION QUESTIONS

The system should be able to answer the following questions about any artifact:

**Q1 — Is this artifact root or derived?**  
Read `parent_artifact_ids`. Empty → root. Non-empty → derived.

**Q2 — What is its parent?**  
Return `parent_artifact_ids[0]` if present. Null if none.

**Q3 — What is its root?**  
Return `root_artifact_id`. Null if not set.

**Q4 — What generation is it?**  
Return `generation`. Null if not set.

**Q5 — Does it belong to an active thread?**  
Consult thread/session context. Not a lineage field — separate concern.

**Q6 — Is lineage incomplete or legacy?**  
- `legacy_unknown`: artifact predates lineage fields and carries no `generation` field  
- `incomplete`: new artifact with `generation` field present but `root_artifact_id` is null despite non-empty `parent_artifact_ids`  
- `complete`: has `generation` and `root_artifact_id` populated correctly

---

## SECTION 4 — OUTPUT MODEL

When the inspection surface is queried for an artifact ID, it returns:

```python
@dataclass
class ArtifactLineageInspection:
    artifact_id: str
    lineage_status: Literal["root", "derived", "incomplete", "legacy_unknown"]
    parent_artifact_ids: list[str]        # empty if root
    root_artifact_id: str | None         # null if unknown or incomplete
    generation: int | None                # null if unknown
    thread_ids: list[str]                 # from session/thread context; empty if none
    lineage_complete: bool                # true when status is root|derived and root_artifact_id is set
    notes: str                            # human-readable provenance note
```

### `lineage_status` values

| Value | Meaning |
|-------|---------|
| `root` | `parent_artifact_ids` is empty; `generation == 0` |
| `derived` | `parent_artifact_ids` is non-empty; `root_artifact_id` and `generation` are set |
| `incomplete` | `parent_artifact_ids` non-empty but `root_artifact_id` is null — data gap |
| `legacy_unknown` | Artifact predates lineage fields; no `generation` field present |

### `notes` field guidance

- root: `"Generated directly; no parent artifact."`
- derived: `"Derived from {parent_artifact_ids[0]}; root is {root_artifact_id}, generation {generation}."`
- incomplete: `"Parent references present but root_artifact_id is unset; lineage incomplete."`
- legacy_unknown: `"Artifact predates lineage fields; parent/root/generation unknown."`

---

## SECTION 5 — SAFE EXPOSURE LEVEL

### Operator-safe

The inspection output is a single artifact's lineage facts in a defined structure. It does not include sibling references, child counts, graph distance, or traversal paths. An operator can read the output and understand where this artifact sits in its lineage without understanding graph mechanics.

### Technical-safe

The inspection surface reads existing artifact data and applies rules. It does not write. It does not mutate lineage fields. It does not attempt to reconstruct missing data — it reports what is present and marks gaps clearly.

### No raw graph complexity yet

Graph UI, path traversal, ancestor/descendant queries, and visual lineage displays are out of scope for this first slice. The inspection surface is the foundation those layers will be built on — not the display itself.

---

## SECTION 6 — FORBIDDEN DRIFT

The following are explicitly ruled out for this design and first implementation:

1. **No turning inspection into authority** — the inspection surface answers questions; it does not make decisions, trigger actions, or modify artifact state based on lineage.

2. **No graph UI in first slice** — no visualization, node rendering, edge drawing, or interactive graph exploration.

3. **No lineage inference beyond explicit fields** — do not infer `root_artifact_id` by traversing parent references at inspection time. If `root_artifact_id` is null and `parent_artifact_ids` is non-empty, report `incomplete`; do not compute the root.

4. **No pretending old artifacts have full lineage** — legacy artifacts (pre-lineage-fields) must be reported as `legacy_unknown`, not quietly assigned a root or generation.

5. **No graph engine** — no traversal library, no edge resolution, no graph persistence. The inspection surface operates on per-artifact field reads only.

6. **No thread/session reconstruction** — `thread_ids` are read from known context if available; the inspection surface does not reconstruct thread membership from message logs or history.

---

## SECTION 7 — RECOMMENDED FIRST IMPLEMENTATION

### Choose the smallest safe first implementation

A single inspection helper module that:
- Takes an artifact dict (or artifact ID + store) as input
- Reads the three lineage fields (`parent_artifact_ids`, `root_artifact_id`, `generation`)
- Reads thread context if available
- Returns an `ArtifactLineageInspection` dataclass instance

**File:** `weslr/lineage_inspector.py` (or equivalent location under the weslr package)

**Responsibilities:**
- Classify lineage status from raw fields
- Build the `notes` string
- Set `lineage_complete` flag
- Handle `legacy_unknown` when `generation` field is absent

**Not responsibilities:**
- Graph traversal
- Persistence
- CLI interface (defer to later iteration)
- Stored artifact mutation

**Location reasoning:** Placed in the weslr package alongside existing modules (entity_graph, etc.) so it is importable by other weslr components. Not in `commands/` since it is not an operator-facing command — that layer comes later.

**Optional follow-on surfaces (deferred):**
- CLI command: `weslr lineage-inspect <artifact-id>` — for debug/operator use
- Internal service wrapper for programmatic use

### Versioning

The inspection output model carries a version field internally (e.g., `output_version: str = "1.0"`). This allows the surface to evolve without breaking callers.

---

## SECTION 8 — STOP LINE

This document is design only.  

**No code has been written.**  
**No behavior has changed.**  
**No commands have been run.**  

This document authorizes no implementation, no deployment, no behavior change, and no authority delegation beyond this design phase.

---

## OUTPUT FORMAT

### SECTION 1 — FILES CHANGED

```
docs/LINEAGE_AWARE_ARTIFACT_INSPECTION_V1.md  [NEW]
```

### SECTION 2 — COMMANDS RUN

```
None — design only, no execution
```

### SECTION 3 — DESIGN SUMMARY

- Lineage inspection surface defined as read-only helper returning `ArtifactLineageInspection` dataclass
- Covers root/derived/incomplete/legacy_unknown classification from explicit fields only
- No graph engine, no traversal, no inference beyond stated rules
- Output model includes version field for forward compatibility
- Placement: `weslr/lineage_inspector.py` (first safe location)
- Deferred: CLI surface, graph UI, traversal engine

### SECTION 4 — RECOMMENDED FIRST IMPLEMENTATION

Single Python module `weslr/lineage_inspector.py`:
- `ArtifactLineageInspection` dataclass
- `inspect_artifact_lineage(artifact: dict) -> ArtifactLineageInspection`
- Classification logic from raw lineage fields only
- No persistence, no graph, no CLI

### SECTION 5 — STOP LINE

Design complete. Document only. No code, no commands, no behavior changes.