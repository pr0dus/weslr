# ARTIFACT LINEAGE AND GRAPH MODEL V1
**Generated:** 2026-04-22 22:38 GMT+2
**Mode:** STRICT — design only, no code changes, no behavior changes, no routing changes, no scoring changes, no governance changes, no new authority
**Author:** Main agent
**Sources:** ARCHITECTURE_DOCTRINE_ADDENDUM.md (Brick 4), docs/ARTIFACT_TYPES_AND_LIFECYCLE_V1.md, docs/TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md, docs/WESLR_CANONICAL_SELF_MODEL_V1.md

---

## SECTION 1 — PURPOSE

### Why Artifact Lineage Is Required After Types and Lifecycle

ARTIFACT_TYPES_AND_LIFECYCLE_V1 defined what artifacts are (six types) and how they move through states (drafted → surfaced → reviewed → approved/denied → applied/superseded → archived). This answered the question: *what is this artifact and what is its current status?*

But it left unanswered: *where did this artifact come from and what does it connect to?*

Without lineage, artifacts are isolated objects. A Research Artifact cannot be traced to the question that prompted it. An Improvement Proposal cannot reference the Analysis Artifact that identified the gap it addresses. A Comparison Artifact cannot name the two options it compared. A Judgment Artifact cannot identify which artifact it decided.

This matters for four reasons:

**Auditability.** When an Improvement Proposal is approved and executed, the operator should be able to trace the full chain: Analysis Artifact (diagnosis) → Research Artifact (context) → Improvement Proposal (fix). Without lineage, the operator sees only the proposal, not the reasoning chain that produced it.

**Comparison and synthesis.** Future WESLR reasoning should be able to ask: "what is the evidence that this proposal was built on?" or "has this gap been addressed before?" Without lineage, such questions cannot be answered programmatically — only by reading the artifact content, which is fragile.

**Continuity.** When "improve this" resolves to an artifact, the operator should be able to see the lineage chain: "this artifact is generation 3 of the PV Efficiency lineage." Without lineage, the system can only say "this is the current artifact" with no history.

**Governance.** When a Judgment Artifact records a decision on an Improvement Proposal, future inspectors need to know what was decided and why. Without lineage reference to the target artifact, the Judgment Artifact is disconnected from its subject.

### Why Artifacts Must Not Remain Isolated Objects

An artifact without lineage is a document, not a system object. It can be read, but it cannot be queried, compared, or connected to other artifacts programmatically. WESLR's evolution system requires artifacts to be nodes in a traceable graph — not leaves floating in isolation.

Brick 4 established that artifacts are the unit of evolution. If each artifact is an island, the evolution system is just a collection of disconnected documents. Lineage turns the collection into a system.

---

## SECTION 2 — CORE LINEAGE PRINCIPLE

### The Rule

**Every artifact must have a traceable origin.** This does not mean every artifact needs a parent — first-generation artifacts exist at the beginning of a chain and point to an origin event or source instead. But all artifacts must be queryable by origin.

**Artifact state and artifact lineage are descriptive, not authoritative.** They describe what is true about an artifact's history and status, but they do not grant permission to execute, apply, or mutate system behavior.

### First-Generation (Root) Artifacts

A root artifact is one that was created without a parent artifact. It may point to:
- An `origin_event` (e.g., `research_triggered`, `operator_request`, `drift_concern_raised`, `continuity_break_detected`)
- An `origin_source` (e.g., a session event, a user request, a system trigger)

Root artifacts still have a `root_artifact_id` — it is their own ID. They have no `parent_artifact_id`. The `lineage_depth` is 0.

Root artifacts are valid. Not every chain starts from another artifact. A Research Artifact prompted by an operator question is a root artifact — its origin is the operator question, not a prior artifact.

### Derived Artifacts

A derived artifact is one created with a `parent_artifact_id`. It continues a chain. Its `root_artifact_id` is inherited from its parent (or is its own ID if its parent was a root). Its `lineage_depth` = parent's `lineage_depth` + 1.

Derived artifacts are the primary mechanism of evolution. Each step in a chain — Research → Analysis → Improvement Proposal → Applied — is a derived artifact continuing the chain.

### Multi-Parent Artifacts

A multi-parent artifact is one created with multiple `parent_artifact_ids`. This is valid for:
- Comparison Artifacts — derived from two (or more) options being compared
- Synthesis Artifacts — derived from multiple Research or Analysis Artifacts informing one conclusion
- Judgment Artifacts — derived from the artifact being judged (single parent, but may reference comparison inputs)

Multi-parent artifacts do not have a single linear chain. They have a graph structure at their origin. This is intentional: comparison requires two inputs; synthesis requires multiple sources.

For multi-parent artifacts:
- `lineage_depth` = max(parent lineage_depth) + 1
- All parent IDs are recorded
- The artifact is not a direct continuation of any one parent — it is a new node with multiple incoming edges

Multi-parent artifacts must document why multiple parents were necessary. This is recorded in the artifact's `origin_reason` field.

---

## SECTION 3 — GRAPH MODEL

### Structural Overview

The artifact lineage is a directed acyclic graph (DAG) with one constraint: cycles are forbidden. An artifact may reference ancestors (its parents, grandparents, root), but may not reference itself or any artifact that transitively references it.

The direction of edges is from derived artifact → parent artifact (child points to parent). This reflects the direction of derivation.

### Node Definition

A node = an artifact. Every artifact is a node. Node identity is established by `artifact_id`.

### Edge Types

| Edge Type | Meaning | Source Node | Target Node | Required Fields |
|---|---|---|---|---|
| `derived_from` | This artifact was created from the target artifact (direct parent) | Any derived artifact | Its direct parent | `parent_artifact_id`, `derivation_reason` |
| `compares` | This artifact evaluated two or more target artifacts | Comparison Artifact | Option artifacts being compared | `compared_artifact_ids` (list) |
| `judges` | This artifact recorded a governance decision on the target artifact | Judgment Artifact | Target artifact being decided | `target_artifact_id`, `judgment` |
| `refines` | This artifact is a refined version of the target artifact, incorporating feedback | Artifact in `refined` state | Original artifact | `parent_artifact_id`, `refinement_feedback_ref` |
| `analyzes` | This artifact evaluated the target artifact as its subject | Analysis Artifact | Artifact being analyzed | `subject_artifact_id` |
| `proposes_change_for` | This artifact proposes a change addressing the target artifact | Improvement Proposal | Gap/analysis artifact being addressed | `addresses_artifact_id` |
| `continues` | This artifact continues a thread or lineage from the target artifact | Any artifact continuing prior work | Prior artifact in chain | `continues_artifact_id`, `continuation_type` |
| `supersedes` | This artifact replaced the target artifact as the authoritative version | Artifact in `superseded` state | Replaced artifact | `superseded_artifact_id` |

### Edge Cardinality

| Edge Type | Cardinality |
|---|---|
| `derived_from` | 0 (root artifact) or exactly 1 (single-parent) or 2+ (multi-parent) |
| `compares` | 2+ (at least two options) |
| `judges` | 1 (one target per judgment) |
| `refines` | 1 (one parent per refinement) |
| `analyzes` | 1 (one subject per analysis) |
| `proposes_change_for` | 1 (one addressed artifact per proposal) |
| `continues` | 1 (one continued artifact) |
| `supersedes` | 1 (one superseded artifact per replacement) |

### Cycle Prohibition

The graph is a DAG. Cycles are forbidden because they break the meaning of "derived from" (an artifact cannot be its own ancestor). If cycle detection is attempted and a cycle would be created, the artifact creation is invalid and must be rejected.

**Graph relationships define structural connections between artifacts. Artifact state and artifact lineage are descriptive, not authoritative. No edge type, graph connectivity, or lineage depth implies execution authority or permission to act.**

### Graph Direction and Traversal

Edges point from child to parent (derived → parent). To trace ancestry: follow `derived_from` edges backward. To trace descendants: query all artifacts that have a given artifact ID in their `parent_artifact_ids` field.

Forward tracing (descendants) is a query operation, not stored as edges. For any artifact, its descendants are all artifacts that list it as a parent. This is a query-time computation, not a stored directed edge in the reverse direction.

---

## SECTION 4 — REQUIRED LINEAGE FIELDS

### Minimum Canonical Fields

Every artifact must carry the following fields for lineage purposes:

| Field | Type | Required | Description |
|---|---|---|---|
| `artifact_id` | string | Always | Unique identifier; establishment of node identity |
| `artifact_type` | enum | Always | From ARTIFACT_TYPES_AND_LIFECYCLE_V1; enables edge type constraints |
| `artifact_state` | enum | Always | From ARTIFACT_TYPES_AND_LIFECYCLE_V1; state machine |
| `origin_event` | string | Always | What triggered this artifact's creation: `research_triggered`, `operator_request`, `system_diagnostic`, `governance_review`, `comparison_request`, `lineage_continuation`, `unknown` |
| `origin_source` | string | Always | What specifically triggered it: session event, user message hash, system trigger name, etc. |
| `parent_artifact_ids` | list[string] | For derived artifacts | Direct parent artifact IDs; empty for root artifacts |
| `root_artifact_id` | string | Always | ID of the root of this lineage chain; for root artifacts, equals own `artifact_id` |
| `lineage_depth` | int | Always | 0 for root, parent's depth + 1 for derived |
| `graph_edges` | list[object] | Always | List of outgoing edges; each edge: `{edge_type, target_artifact_id, edge_metadata}` |
| `origin_reason` | string | For multi-parent artifacts | Why this artifact required multiple parents; required when `len(parent_artifact_ids) > 1` |
| `generation` | int | Always | Linear generation number within a single-parent chain; same as `lineage_depth` for single-parent chains; for multi-parent, the generation is max(parent generations) + 1 |

### Field Justification

**`origin_event` + `origin_source`:** Root artifacts (no parent) must have a traceable origin. These two fields together provide a canonical answer to "what caused this artifact to be created?" Without them, root artifacts have no machine-readable origin.

**`parent_artifact_ids`:** The fundamental lineage relationship. Single-parent artifacts have exactly one entry. Multi-parent have two or more. Root artifacts have an empty list.

**`root_artifact_id`:** Enables querying "all artifacts in this lineage chain" without traversing the full parent chain. Given any artifact, its root is always known in one field lookup.

**`lineage_depth`:** Enables depth queries without traversal. "Show me only artifacts with depth ≤ 2" is a direct filter, not a graph traversal.

**`graph_edges`:** The canonical encoding of relationships. This field records all outgoing edges from this artifact node. Edge types are constrained by the graph model (Section 3). An artifact without edges is valid — it means the artifact has no outgoing relationships yet.

**`origin_reason`:** Multi-parent artifacts require justification. This prevents accidental multi-parent creation and forces the artifact author to state why the artifact required multiple sources.

### Example: Root Research Artifact

```json
{
  "artifact_id": "art-1777000000001-1",
  "artifact_type": "research",
  "artifact_state": "drafted",
  "origin_event": "operator_request",
  "origin_source": "operator_question_1777000000001",
  "parent_artifact_ids": [],
  "root_artifact_id": "art-1777000000001-1",
  "lineage_depth": 0,
  "generation": 1,
  "graph_edges": []
}
```

### Example: Derived Improvement Proposal

```json
{
  "artifact_id": "art-1777000000003-1",
  "artifact_type": "improvement_proposal",
  "artifact_state": "drafted",
  "origin_event": "governance_review",
  "origin_source": "drift_concern_dc-001",
  "parent_artifact_ids": ["art-1777000000002-1"],
  "root_artifact_id": "art-1777000000001-1",
  "lineage_depth": 2,
  "generation": 1,
  "origin_reason": null,
  "graph_edges": [
    {"edge_type": "proposes_change_for", "target_artifact_id": "art-1777000000002-1", "edge_metadata": {"gap_addressed": "context_selection_gap"}},
    {"edge_type": "analyzes", "target_artifact_id": "art-1777000000002-1", "edge_metadata": {}}
  ]
}
```

---

## SECTION 5 — STATE VS AUTHORITY

### The Rule

**Artifact state and artifact lineage are descriptive, not authoritative.**

Artifact state is a recorded status. Artifact lineage is traceability. Neither grants authority. Execution authority exists only through explicit governance mechanisms outside the artifact structure.

This means three things explicitly:

**1. An `approved` artifact does not mean the change may self-apply.**

The `approved` state is a governance decision record. It records that the operator authorized execution. It does not grant WESLR autonomous authority to execute. Execution still requires the ExecutionGate to verify approval state and issue the execution permit.

**2. Graph connectivity does not imply permission.**

If Artifact B `derived_from` Artifact A, this does not mean B has any authority over A, or that B's contents are endorsed by A, or that A must accept B's proposals. The graph is a record of derivation, not a delegation of authority.

**3. A relationship edge does not grant access or execution rights.**

`compares`, `judges`, `analyzes`, `proposes_change_for` — all of these are descriptive relationships. They describe what the artifact did, not what rights the artifact has. An Analysis Artifact that `analyzes` an artifact does so because it was created to do so; the edge is the record, not the authorization.

### What Graph Connectivity Actually Provides

- **Traceability** — given any artifact, you can find its ancestors and descendants
- **Auditability** — the reasoning chain behind any artifact is queryable
- **Context** — an Improvement Proposal's proposal can be contextualized by its source Analysis and Research artifacts
- **Pattern detection** — recurring chains, common patterns, repeated dependencies can be detected

What graph connectivity does NOT provide:
- Execution authority
- Override rights
- Autonomous change capability
- Privilege escalation

---

## SECTION 6 — RELATION TO ARTIFACT TYPES

### Research Artifact

**Lineage pattern:** Root artifacts are common (new research prompted by operator question or system curiosity trigger). Derived Research Artifacts are common (follow-up research building on prior findings).

**Edge types used:** `continues` (Research → Research when continuing investigation), `analyzes` (if Research artifact evaluates prior artifacts as part of its investigation)

**Multi-parent allowed:** Yes — synthesis of multiple prior Research Artifacts into a consolidated finding.

**Key rule:** Research Artifact may reference any artifact type as context, but its outgoing edges should reflect what it actually evaluated, not every artifact it read.

---

### Analysis Artifact

**Lineage pattern:** Typically derived from Research Artifact (research findings surface a gap that warrants diagnosis) or from an event (drift detected, contamination flagged). Often has exactly one parent.

**Edge types used:** `analyzes` (Analysis → the artifact or behavior it is diagnosing), `proposes_change_for` (if Analysis identifies a fixable gap and generates an Improvement Proposal)

**Multi-parent allowed:** Yes — diagnosis informed by multiple Research Artifacts or multiple source events.

**Key rule:** Analysis Artifact should `analyze` the specific artifact or state that prompted it. It should not analyze itself.

---

### Improvement Proposal

**Lineage pattern:** Typically derived from Analysis Artifact (diagnosis establishes the gap; proposal addresses it). May also have Research Artifact parent(s) if research directly motivated the proposal.

**Edge types used:** `proposes_change_for` (Proposal → Analysis Artifact or problem statement it addresses), `analyzes` (Proposal may analyze the gap it addresses), `continues` (if proposal continues a prior proposal in the same chain)

**Multi-parent allowed:** Rare — proposals typically address one identified gap. Multi-parent proposals require explicit `origin_reason`.

**Key rule:** An Improvement Proposal's `parent_artifact_ids` should trace back through the Analysis Artifact(s) that motivated it. This chain is the audit trail: *why was this change proposed? Because the Analysis Artifact identified gap X.*

---

### Comparison Artifact

**Lineage pattern:** Multi-parent by design — derives from the two (or more) options being compared. The options being compared may themselves be any artifact type that produces a comparable output.

**Edge types used:** `compares` (Comparison → each option artifact), `judges` (if a Judgment Artifact follows from the comparison to record the decision)

**Multi-parent:** Required — a Comparison Artifact without multiple parents is structurally invalid.

**Key rule:** The `compared_artifact_ids` in the `compares` edge must include all options considered, not just the "winner." A Comparison Artifact that selects Option A as winner must still record Option B as a compared artifact.

---

### Judgment Artifact

**Lineage pattern:** Derived from the artifact it judges (single parent). May also reference a Comparison Artifact as context if a comparison preceded the judgment.

**Edge types used:** `judges` (Judgment → target artifact), `compares` (if judgment was informed by comparison; reference to the comparison artifact in `graph_edges`)

**Multi-parent allowed:** Yes — judgment informed by comparison and by the target artifact.

**Key rule:** Judgment Artifact does not "approve" a proposal by existing — it records the decision. Approval state is stored in `artifact_state` (`approved`/`denied`). The Judgment Artifact is the permanent record; the state is the governance flag.

---

### Continuity Artifact

**Lineage pattern:** Usually root artifacts — created to record current state rather than derive from prior work. May have `continues` edge to prior Continuity Artifact if it is updating a prior snapshot.

**Edge types used:** `continues` (Continuity → prior Continuity Artifact being updated), `supersedes` (if replacing a prior Continuity Artifact)

**Multi-parent allowed:** No — Continuity Artifacts describe single continuity state snapshots.

**Key rule:** Continuity Artifacts are the most stable artifacts. They record what was true at a point in time, not what should change. They do not enter governance.

---

## SECTION 7 — RELATION TO CONTINUITY

### Thread Integration

Artifacts are linked to threads via `thread_id` (from ARTIFACT_TYPES_AND_LIFECYCLE_V1). The thread is a sequence of artifacts. Lineage and thread are orthogonal:
- **Lineage** answers: what is this artifact derived from and what does it influence?
- **Thread** answers: what is the sequence of work items in this work context?

A given artifact may be in a thread (it was worked on in a specific work context) and also have lineage (it derived from prior artifacts). These are independent dimensions.

When an artifact is created in the context of an active thread, `thread_id` should be set. When an artifact is created from a question that has no thread, `thread_id` may be absent.

### Active Continuity Object Integration

The active continuity object (per TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md) may reference an artifact as its current focus. The lineage of that artifact tells the operator:
- Which generation of the artifact is current (via `lineage_depth` and `generation`)
- What the prior versions were (via `parent_artifact_ids` chain)
- Whether the artifact was derived from a contamination event (via `origin_event` = `continuity_break_detected` or `contamination_flagged`)

This allows SatUi to show not just "this is the current artifact" but "this is generation 3 of a lineage that started when a contamination event was detected in Session B."

### Timeline Persistence

Artifact lifecycle events (from ARTIFACT_TYPES_AND_LIFECYCLE_V1) are written to the timeline event log. Lineage extends this:
- `artifact.lineage_created` — when a derived artifact is created with parent references
- `artifact.graph_edge_added` — when an additional edge is added to an existing artifact (edge amendments are allowed but must be logged)

The timeline log entry for a lineage event includes:
- `artifact_id`
- `lineage_depth`
- `parent_artifact_ids`
- `origin_event`

This enables querying the lineage state at any point in time by reading the timeline log up to that timestamp.

### Future Cross-Session Reference Resolution

When "improve this" resolves to an artifact in a future session, the lineage graph tells WESLR:
1. This artifact is the current generation in its lineage (via `lineage_depth` and `supersedes` edge)
2. Prior generations exist and can be retrieved for comparison (via `parent_artifact_ids`)
3. If this artifact's origin was a contamination event, the contamination metadata is available on the artifact

This makes the lineage graph the authoritative answer to "what is the full history of this artifact chain?"

---

## SECTION 8 — FORBIDDEN DRIFT

### F1 — Artifact Mutation Without Lineage Update

An artifact that has been placed in `surfaced` or later state must not be modified. Modification requires creating a new artifact with a `parent_artifact_id` reference to the original, transitioning the original to `superseded`. This rule is absolute. No exceptions for "minor fixes" or "typo corrections" — even small changes create a new artifact with lineage link.

### F2 — Comparison Without Persistent References

A Comparison Artifact must reference the artifacts it compared via `compares` edges. Transient in-memory comparisons that produce text but no persistent reference are not valid Comparison Artifacts. The comparison must be recorded, not just described in the response.

### F3 — Derived Artifacts With No Parent Trace

An artifact created in response to another artifact (Analysis responding to Research; Proposal responding to Analysis; Comparison responding to options) must have a `parent_artifact_id`. The only exception is root artifacts created from `origin_event` without a prior artifact. If an artifact clearly derives from another artifact but has no `parent_artifact_id`, this is a structural error and the artifact is non-compliant.

### F4 — Lineage Graph Used as Execution Authority

No edge type in the graph model grants execution rights. In particular:
- `proposes_change_for` does not authorize the proposed change
- `analyzes` does not endorse the analyzed artifact
- `judges` is the record of judgment, not the judgment itself
- `supersedes` does not grant the superseding artifact automatic authority over the superseded one

Any system that interprets graph connectivity as authority has violated this rule and must be corrected.

### F5 — Silent Rewriting of Root/Parent Relationships

After an artifact is created and placed in `surfaced` state, its `parent_artifact_ids` and `root_artifact_id` fields are immutable. These fields define the artifact's identity in the graph. Changing them after surfacing destroys the graph's integrity. Correction requires creating a new artifact with correct lineage.

### F6 — Multi-Parent Artifacts Without Justification

An artifact with more than one `parent_artifact_id` must have a non-empty `origin_reason` field explaining why multiple parents were necessary. Artifacts with multiple parents and no `origin_reason` are non-compliant.

### F7 — Cycle Creation

An artifact whose creation would create a cycle in the lineage graph (artifact A is its own ancestor via parent chain) must be rejected at creation time. This is a structural validation, not a style preference.

### F8 — No Implicit Authority from State or Lineage

Artifact state and artifact lineage must never be used to infer execution authority. All execution must pass through explicit governance pathways. Specifically:
- `"approved"` state does not mean the change may self-apply — execution still requires ExecutionGate verification
- Strong lineage, many parents, or deep chains never justify execution without approval
- Graph connectivity (edge types, connectivity patterns, lineage depth) never triggers or authorizes execution
- Using graph position or edge presence as an execution trigger violates this invariant

---

## SECTION 9 — RECOMMENDED FIRST IMPLEMENTATION

### Decision: Add Canonical Lineage Fields to New Artifacts, Leave Existing Artifacts Unchanged

**Rationale:** The smallest safe structural step is to define the canonical fields and require them for all new artifact creation, while accepting that existing artifacts (which lack these fields) are valid backward-compatible artifacts.

This is the correct first step because:
1. **Additive only** — existing artifacts remain valid; no migration required
2. **Bounded** — just adding fields to the artifact schema when any new artifact is created
3. **Enables future graph queries** — as new artifacts accumulate, the graph becomes queryable
4. **Does not require graph infrastructure** — no graph database, no edge store, just fields in the artifact JSON
5. **Backward compatible** — existing artifact-generating code continues to work; new code emits the fields

### Fields to Add

For all new artifacts created after this design is canonized:
- `root_artifact_id` (string) — always populated
- `parent_artifact_ids` (list[string]) — empty for root, 1+ for derived
- `lineage_depth` (int) — always populated
- `generation` (int) — always populated
- `origin_event` (string) — always populated
- `origin_source` (string) — always populated
- `graph_edges` (list[object]) — always populated, empty list if no edges yet
- `origin_reason` (string) — required when `len(parent_artifact_ids) > 1`

### What NOT to Implement First

- **Graph store or graph database** — fields are stored in the artifact JSON itself; no separate graph store needed yet
- **Graph querying engine** — traversal can be done by reading artifact records; no special query language needed yet
- **Edge validation at creation** — first pass allows edge field to be populated manually; structural validation can be added as a second pass
- **Retroactive lineage for existing artifacts** — backward compatibility is preserved; existing artifacts are valid without lineage fields
- **Visualization** — lineage graph display in SatUi can be added after the fields exist in new artifacts

### Implementation Order

1. Define canonical field names (this document ✅)
2. Instrument `dialogue.py` artifact creation with all lineage fields — `origin_event`, `origin_source`, `parent_artifact_ids`, `root_artifact_id`, `lineage_depth`, `generation`, `graph_edges`
3. Instrument `self_improvement_proposal.py` with lineage fields — derive from the observation that triggered the proposal
4. Instrument `cross_session_artifact_eval.py` with lineage fields — eval artifacts as Analysis type with lineage
5. Verify fields are populated for new artifacts by inspecting artifact records

---

## SECTION 10 — FUTURE EXTENSIONS

The following are acknowledged as natural extensions but are **not designed here**:

**Graph querying:** After artifacts accumulate lineage fields, query operations become possible: "find all descendants of artifact X", "find all artifacts with lineage_depth > 3", "find all artifacts that compare options A and B". These require a query layer but do not require changing the field definitions.

**Synthesis artifacts:** A future artifact type that combines multiple Research Artifacts into a consolidated finding, with explicit multi-parent lineage and `origin_reason`. Not designed here — the type taxonomy already allows it; the specific synthesis logic is a later slice.

**Lineage-aware SatUi displays:** Showing the full lineage chain for an artifact (root → ... → current) as a navigable graph in SatUi. Not designed here — requires UI work that should follow the field implementation, not precede it.

**Multi-artifact research chains:** A series of Research Artifacts that build on each other, where each derives from the prior, creating a traceable research trajectory. The lineage model supports this; the specific chain-creation trigger logic is deferred.

**Automated cycle detection:** A validation layer that rejects artifact creation if it would create a cycle in the lineage graph. Not a first implementation item — can be added as a second pass after manual lineage population is working.

---

## SECTION 11 — STOP LINE

- Documentation only ✅
- No code changes ✅
- No behavior changes ✅
- No routing changes ✅
- No scoring changes ✅
- No governance changes ✅
- No new authority ✅
- Additive only ✅

**Files changed:**
- `docs/ARTIFACT_LINEAGE_AND_GRAPH_MODEL_V1.md` — created (this document)

**Relation to existing doctrine:**
- ARCHITECTURE_DOCTRINE_ADDENDUM.md → lineage is the structural implementation of Brick 4's "traceable evolution" requirement
- docs/ARTIFACT_TYPES_AND_LIFECYCLE_V1.md → lineage extends artifact definition with ancestry; edge types constrained by artifact type
- docs/TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md → lineage integrates with thread and active continuity object
- docs/WESLR_CANONICAL_SELF_MODEL_V1.md → lineage provides the traceable history needed for the 7-parallel-lane consolidation target

---

*ARTIFACT_LINEAGE_AND_GRAPH_MODEL_V1 — Design Specification*
*Design only. No code. No behavior changes.*